"""
Job Clustering Module

Clusters jobs by similarity using existing embeddings and extracts
high-impact keywords/terms that define each cluster.

Supports version tracking for cluster stability analysis.
"""

import uuid
import json
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from google.cloud import bigquery
from sklearn.cluster import KMeans, DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import numpy as np


class JobClusterer:
    """
    Cluster jobs and extract defining keywords with version tracking.
    
    Supports:
    - K-means and DBSCAN clustering algorithms
    - TF-IDF keyword extraction per cluster
    - Version tracking via cluster_run_id and cluster_version
    - Cluster stability analysis between runs
    - Deactivation of previous assignments on re-clustering
    
    Each clustering run generates a unique cluster_run_id that enables:
    - Tracking cluster assignments over time
    - Comparing stability between runs
    - Historical analysis of cluster evolution
    """
    
    def __init__(self):
        self.version = "v1.0-kmeans-tfidf"
        self.bigquery_client = bigquery.Client()
        self.project_id = "sylvan-replica-478802-p4"
        self.dataset_id = f"{self.project_id}.brightdata_jobs"
        self.n_clusters = 10  # Configurable number of clusters
        self._current_run_id: Optional[str] = None
        
    def get_version(self) -> str:
        """Return clusterer version identifier."""
        return self.version
    
    def generate_cluster_run_id(self) -> str:
        """Generate a unique cluster run ID for tracking."""
        return str(uuid.uuid4())
    
    def cluster_jobs(
        self,
        method: str = "kmeans",
        n_clusters: int = 10,
        min_jobs_per_cluster: int = 3,
        deactivate_previous: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Cluster all jobs with embeddings and extract keywords.
        
        Args:
            method: Clustering method ('kmeans' or 'dbscan')
            n_clusters: Number of clusters for kmeans
            min_jobs_per_cluster: Minimum jobs per cluster for dbscan
            deactivate_previous: Whether to deactivate previous cluster assignments
            
        Returns:
            List of cluster assignments with keywords and version tracking
        """
        # Generate run ID for this clustering execution
        self._current_run_id = self.generate_cluster_run_id()
        
        # Deactivate previous cluster assignments if requested
        if deactivate_previous:
            self._deactivate_previous_assignments()
        
        # Fetch job embeddings
        jobs_data = self._fetch_job_embeddings()
        
        if len(jobs_data) < n_clusters:
            raise ValueError(f"Not enough jobs ({len(jobs_data)}) for {n_clusters} clusters")
        
        # Get current cluster versions for each job
        job_versions = self._get_current_cluster_versions([j['job_posting_id'] for j in jobs_data])
        
        # Extract embeddings matrix and job info
        embeddings_matrix = np.array([job['embedding'] for job in jobs_data])
        
        # Perform clustering
        if method == "kmeans":
            cluster_labels = self._kmeans_clustering(embeddings_matrix, n_clusters)
        elif method == "dbscan":
            cluster_labels = self._dbscan_clustering(embeddings_matrix)
        else:
            raise ValueError(f"Unknown clustering method: {method}")
        
        # Assign clusters to jobs
        for idx, job in enumerate(jobs_data):
            job['cluster_id'] = int(cluster_labels[idx])
        
        # Extract keywords for each cluster
        cluster_keywords = self._extract_cluster_keywords(jobs_data)
        
        # Prepare results with version tracking
        results = []
        for job in jobs_data:
            cluster_id = job['cluster_id']
            job_id = job['job_posting_id']
            
            # Increment version for this job
            current_version = job_versions.get(job_id, 0)
            new_version = current_version + 1
            
            results.append({
                'job_posting_id': job_id,
                'cluster_id': cluster_id,
                'cluster_name': cluster_keywords[cluster_id]['name'],
                'cluster_keywords': cluster_keywords[cluster_id]['keywords'],
                'cluster_size': cluster_keywords[cluster_id]['size'],
                'job_title': job['job_title'],
                'company_name': job['company_name'],
                # Version tracking fields
                'cluster_run_id': self._current_run_id,
                'cluster_model_id': self.version,
                'cluster_version': new_version,
                'is_active': True
            })
        
        return results
    
    def _deactivate_previous_assignments(self) -> int:
        """
        Deactivate all previous cluster assignments.
        
        Returns:
            Number of assignments deactivated
        """
        query = f"""
        UPDATE `{self.dataset_id}.job_clusters`
        SET is_active = FALSE
        WHERE is_active = TRUE
        """
        
        try:
            job = self.bigquery_client.query(query)
            job.result()
            return job.num_dml_affected_rows or 0
        except Exception:
            # Table may not exist yet or have the column
            return 0
    
    def _get_current_cluster_versions(self, job_ids: List[str]) -> Dict[str, int]:
        """
        Get the current cluster version for each job.
        
        Args:
            job_ids: List of job IDs to check
            
        Returns:
            Dictionary of job_id -> current_version
        """
        if not job_ids:
            return {}
        
        # Build job ID list for query
        job_ids_str = ", ".join([f"'{jid}'" for jid in job_ids])
        
        query = f"""
        SELECT 
            job_posting_id,
            MAX(cluster_version) as max_version
        FROM `{self.dataset_id}.job_clusters`
        WHERE job_posting_id IN ({job_ids_str})
        GROUP BY job_posting_id
        """
        
        try:
            results = self.bigquery_client.query(query).result()
            return {row['job_posting_id']: row['max_version'] for row in results}
        except Exception:
            # Table may not exist yet
            return {}
    
    def calculate_stability_metrics(
        self,
        old_run_id: str,
        new_run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate cluster stability metrics between two runs.
        
        Args:
            old_run_id: Previous cluster run ID
            new_run_id: Current cluster run ID (defaults to current)
            
        Returns:
            Stability metrics including percentage of stable assignments
        """
        new_run_id = new_run_id or self._current_run_id
        
        if not new_run_id:
            raise ValueError("No current run ID available")
        
        query = f"""
        WITH old_clusters AS (
            SELECT job_posting_id, cluster_id
            FROM `{self.dataset_id}.job_clusters`
            WHERE cluster_run_id = '{old_run_id}'
        ),
        new_clusters AS (
            SELECT job_posting_id, cluster_id
            FROM `{self.dataset_id}.job_clusters`
            WHERE cluster_run_id = '{new_run_id}'
        ),
        comparison AS (
            SELECT 
                COALESCE(o.job_posting_id, n.job_posting_id) AS job_posting_id,
                o.cluster_id AS old_cluster,
                n.cluster_id AS new_cluster,
                CASE 
                    WHEN o.cluster_id IS NULL THEN 'new'
                    WHEN n.cluster_id IS NULL THEN 'removed'
                    WHEN o.cluster_id = n.cluster_id THEN 'stable'
                    ELSE 'changed'
                END AS status
            FROM old_clusters o
            FULL OUTER JOIN new_clusters n
                ON o.job_posting_id = n.job_posting_id
        )
        SELECT 
            status,
            COUNT(*) AS count
        FROM comparison
        GROUP BY status
        """
        
        try:
            results = self.bigquery_client.query(query).result()
            
            metrics = {'stable': 0, 'changed': 0, 'new': 0, 'removed': 0}
            for row in results:
                metrics[row['status']] = row['count']
            
            total_common = metrics['stable'] + metrics['changed']
            stability_index = metrics['stable'] / total_common if total_common > 0 else 0
            
            return {
                'old_run_id': old_run_id,
                'new_run_id': new_run_id,
                'stable_jobs': metrics['stable'],
                'changed_jobs': metrics['changed'],
                'new_jobs': metrics['new'],
                'removed_jobs': metrics['removed'],
                'stability_index': stability_index
            }
        except Exception as e:
            return {
                'old_run_id': old_run_id,
                'new_run_id': new_run_id,
                'error': str(e)
            }
    
    def get_current_run_id(self) -> Optional[str]:
        """Get the current cluster run ID."""
        return self._current_run_id
    
    def _fetch_job_embeddings(self) -> List[Dict[str, Any]]:
        """Fetch job embeddings from BigQuery."""
        query = f"""
        SELECT 
            je.job_posting_id,
            je.embedding,
            jp.job_title,
            jp.company_name,
            jp.job_summary,
            jp.job_description_formatted
        FROM `{self.dataset_id}.job_embeddings` je
        JOIN `{self.dataset_id}.job_postings` jp
            ON je.job_posting_id = jp.job_posting_id
        WHERE je.chunk_type = 'full_description'
        ORDER BY je.created_at DESC
        """
        
        query_job = self.bigquery_client.query(query)
        results = query_job.result()
        
        jobs = []
        for row in results:
            jobs.append({
                'job_posting_id': row['job_posting_id'],
                'embedding': list(row['embedding']),
                'job_title': row['job_title'],
                'company_name': row['company_name'],
                'job_summary': row['job_summary'],
                'job_description_formatted': row['job_description_formatted']
            })
        
        return jobs
    
    def _kmeans_clustering(self, embeddings: np.ndarray, n_clusters: int) -> np.ndarray:
        """Perform K-means clustering."""
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
            max_iter=300
        )
        cluster_labels = kmeans.fit_predict(embeddings)
        return cluster_labels
    
    def _dbscan_clustering(self, embeddings: np.ndarray) -> np.ndarray:
        """Perform DBSCAN clustering."""
        dbscan = DBSCAN(
            eps=0.5,
            min_samples=3,
            metric='cosine'
        )
        cluster_labels = dbscan.fit_predict(embeddings)
        return cluster_labels
    
    def _extract_cluster_keywords(
        self,
        jobs_data: List[Dict[str, Any]],
        top_n_keywords: int = 10
    ) -> Dict[int, Dict[str, Any]]:
        """
        Extract defining keywords for each cluster using TF-IDF.
        
        Args:
            jobs_data: List of jobs with cluster assignments
            top_n_keywords: Number of top keywords to extract per cluster
            
        Returns:
            Dictionary mapping cluster_id to keywords and metadata
        """
        # Group jobs by cluster
        clusters = {}
        for job in jobs_data:
            cluster_id = job['cluster_id']
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            
            # Combine title and summary for keyword extraction
            text = f"{job['job_title']} {job['job_summary']}"
            clusters[cluster_id].append({
                'text': text,
                'job_title': job['job_title']
            })
        
        # Extract keywords for each cluster
        cluster_keywords = {}
        
        for cluster_id, cluster_jobs in clusters.items():
            # Combine all text in cluster
            cluster_texts = [job['text'] for job in cluster_jobs]
            
            # Extract TF-IDF keywords
            tfidf = TfidfVectorizer(
                max_features=50,
                stop_words='english',
                ngram_range=(1, 2),  # Unigrams and bigrams
                min_df=1,
                max_df=0.8
            )
            
            try:
                tfidf_matrix = tfidf.fit_transform(cluster_texts)
                feature_names = tfidf.get_feature_names_out()
                
                # Get average TF-IDF scores across cluster
                avg_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
                top_indices = avg_scores.argsort()[-top_n_keywords:][::-1]
                
                keywords = [
                    {
                        'term': feature_names[idx],
                        'score': float(avg_scores[idx])
                    }
                    for idx in top_indices
                ]
                
                # Generate cluster name from top keywords
                cluster_name = self._generate_cluster_name(keywords[:3])
                
            except Exception as e:
                # Fallback if TF-IDF fails
                keywords = []
                cluster_name = f"Cluster {cluster_id}"
            
            # Get most common job titles in cluster
            title_counter = Counter([job['job_title'] for job in cluster_jobs])
            common_titles = [title for title, _ in title_counter.most_common(3)]
            
            cluster_keywords[cluster_id] = {
                'name': cluster_name,
                'keywords': keywords,
                'size': len(cluster_jobs),
                'common_titles': common_titles
            }
        
        return cluster_keywords
    
    def _generate_cluster_name(self, top_keywords: List[Dict[str, Any]]) -> str:
        """Generate human-readable cluster name from keywords."""
        if not top_keywords:
            return "General Jobs"
        
        # Take top 2-3 keywords and create name
        terms = [kw['term'].title() for kw in top_keywords[:2]]
        return " / ".join(terms)
    
    def store_clusters(self, cluster_results: List[Dict[str, Any]], enrichment_id: str):
        """
        Store cluster assignments in BigQuery with version tracking.
        
        Args:
            cluster_results: List of cluster assignments with version fields
            enrichment_id: Reference to job_enrichments
        """
        if not cluster_results:
            return
        
        rows = []
        for result in cluster_results:
            rows.append({
                'cluster_assignment_id': str(uuid.uuid4()),
                'job_posting_id': result['job_posting_id'],
                'enrichment_id': enrichment_id,
                'cluster_id': result['cluster_id'],
                'cluster_name': result['cluster_name'],
                'cluster_keywords': json.dumps(result['cluster_keywords']),
                'cluster_size': result['cluster_size'],
                # Version tracking fields
                'cluster_run_id': result.get('cluster_run_id', self._current_run_id),
                'cluster_model_id': result.get('cluster_model_id', self.version),
                'cluster_version': result.get('cluster_version', 1),
                'is_active': result.get('is_active', True),
                'created_at': datetime.utcnow().isoformat()
            })
        
        table_id = f"{self.dataset_id}.job_clusters"
        errors = self.bigquery_client.insert_rows_json(table_id, rows)
        
        if errors:
            raise Exception(f"Failed to store clusters: {errors}")
