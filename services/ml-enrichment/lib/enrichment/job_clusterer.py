"""
Job Clustering Module

Clusters jobs by similarity using existing embeddings and extracts
high-impact keywords/terms that define each cluster.

Extended with cluster version tracking for stability analysis.
"""

import uuid
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from google.cloud import bigquery
from sklearn.cluster import KMeans, DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import numpy as np


logger = logging.getLogger(__name__)


class JobClusterer:
    """Cluster jobs and extract defining keywords with version tracking."""
    
    MODEL_ID = "job_clusterer"
    
    def __init__(self):
        self.version = "v1.0-kmeans-tfidf"
        self.bigquery_client = bigquery.Client()
        self.project_id = "sylvan-replica-478802-p4"
        self.dataset_id = f"{self.project_id}.brightdata_jobs"
        self.n_clusters = 10  # Configurable number of clusters
        self._cluster_version_counter = 0
        
    def get_version(self) -> str:
        """Return clusterer version identifier."""
        return self.version
    
    def get_model_id(self) -> str:
        """Return the model identifier."""
        return self.MODEL_ID
    
    def generate_cluster_run_id(self) -> str:
        """Generate a unique run ID for this clustering execution."""
        return str(uuid.uuid4())
    
    def get_next_cluster_version(self) -> int:
        """Get the next cluster version number."""
        self._cluster_version_counter += 1
        return self._cluster_version_counter
    
    def get_current_cluster_version(self) -> int:
        """Get the current cluster version from database."""
        query = f"""
        SELECT MAX(cluster_version) as max_version
        FROM `{self.dataset_id}.job_clusters`
        WHERE is_active = TRUE
        """
        
        try:
            query_job = self.bigquery_client.query(query)
            results = list(query_job.result())
            if results and results[0]['max_version']:
                return int(results[0]['max_version'])
            return 0
        except Exception as e:
            logger.warning(f"Could not fetch current cluster version: {e}")
            return 0
    
    def calculate_cluster_stability(
        self,
        previous_assignments: Dict[str, int],
        current_assignments: Dict[str, int]
    ) -> Optional[float]:
        """
        Calculate cluster stability between two runs.
        
        Args:
            previous_assignments: Dict mapping job_id -> cluster_id from previous run
            current_assignments: Dict mapping job_id -> cluster_id from current run
            
        Returns:
            Stability score between 0.0 and 1.0, or None if no previous data
        """
        if not previous_assignments:
            return None
        
        # Only compare jobs that exist in both runs
        common_jobs = set(previous_assignments.keys()) & set(current_assignments.keys())
        
        if not common_jobs:
            return None
        
        # Count jobs that stayed in the same cluster
        stable_count = sum(
            1 for job_id in common_jobs
            if previous_assignments[job_id] == current_assignments[job_id]
        )
        
        stability = stable_count / len(common_jobs)
        return round(stability, 4)
    
    def generate_stability_report(
        self,
        previous_assignments: Dict[str, int],
        current_assignments: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Generate a detailed stability report between two clustering runs.
        
        Args:
            previous_assignments: Previous cluster assignments
            current_assignments: Current cluster assignments
            
        Returns:
            Dictionary with stability metrics and migration details
        """
        common_jobs = set(previous_assignments.keys()) & set(current_assignments.keys())
        
        jobs_unchanged = 0
        jobs_changed = 0
        migrations = {}
        
        for job_id in common_jobs:
            old_cluster = previous_assignments[job_id]
            new_cluster = current_assignments[job_id]
            
            if old_cluster == new_cluster:
                jobs_unchanged += 1
            else:
                jobs_changed += 1
                migration_key = (old_cluster, new_cluster)
                migrations[migration_key] = migrations.get(migration_key, 0) + 1
        
        overall_stability = self.calculate_cluster_stability(
            previous_assignments, current_assignments
        )
        
        return {
            'overall_stability': overall_stability or 0.0,
            'jobs_unchanged': jobs_unchanged,
            'jobs_changed': jobs_changed,
            'total_compared': len(common_jobs),
            'new_jobs': len(set(current_assignments.keys()) - set(previous_assignments.keys())),
            'removed_jobs': len(set(previous_assignments.keys()) - set(current_assignments.keys())),
            'migrations': migrations
        }
    
    def get_previous_cluster_assignments(self, run_id: Optional[str] = None) -> Dict[str, int]:
        """
        Get previous cluster assignments from the database.
        
        Args:
            run_id: Optional specific run ID to fetch, otherwise gets latest active
            
        Returns:
            Dictionary mapping job_id to cluster_id
        """
        if run_id:
            query = f"""
            SELECT job_posting_id, cluster_id
            FROM `{self.dataset_id}.job_clusters`
            WHERE cluster_run_id = '{run_id}'
            """
        else:
            query = f"""
            SELECT job_posting_id, cluster_id
            FROM `{self.dataset_id}.job_clusters`
            WHERE is_active = TRUE
            """
        
        try:
            query_job = self.bigquery_client.query(query)
            results = query_job.result()
            return {row['job_posting_id']: row['cluster_id'] for row in results}
        except Exception as e:
            logger.warning(f"Could not fetch previous assignments: {e}")
            return {}
    
    def deactivate_previous_assignments(self):
        """Mark all current active cluster assignments as inactive."""
        query = f"""
        UPDATE `{self.dataset_id}.job_clusters`
        SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP()
        WHERE is_active = TRUE
        """
        
        try:
            query_job = self.bigquery_client.query(query)
            query_job.result()
            logger.info("Deactivated previous cluster assignments")
        except Exception as e:
            logger.error(f"Failed to deactivate previous assignments: {e}")
            raise
    
    def cluster_jobs(
        self,
        method: str = "kmeans",
        n_clusters: int = 10,
        min_jobs_per_cluster: int = 3,
        track_version: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Cluster all jobs with embeddings and extract keywords.
        
        Args:
            method: Clustering method ('kmeans' or 'dbscan')
            n_clusters: Number of clusters for kmeans
            min_jobs_per_cluster: Minimum jobs per cluster for dbscan
            track_version: Whether to include version tracking info
            
        Returns:
            List of cluster assignments with keywords and version info
        """
        # Generate run ID for this clustering execution
        cluster_run_id = self.generate_cluster_run_id()
        cluster_version = self.get_current_cluster_version() + 1
        
        logger.info(f"Starting clustering run {cluster_run_id}, version {cluster_version}")
        
        # Fetch job embeddings
        jobs_data = self._fetch_job_embeddings()
        
        if len(jobs_data) < n_clusters:
            raise ValueError(f"Not enough jobs ({len(jobs_data)}) for {n_clusters} clusters")
        
        # Get previous assignments for stability calculation
        previous_assignments = self.get_previous_cluster_assignments()
        
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
        
        # Build current assignments for stability calculation
        current_assignments = {job['job_posting_id']: job['cluster_id'] for job in jobs_data}
        
        # Calculate stability
        stability = self.calculate_cluster_stability(previous_assignments, current_assignments)
        if stability is not None:
            logger.info(f"Cluster stability: {stability:.2%}")
        
        # Prepare results with version info
        results = []
        for job in jobs_data:
            cluster_id = job['cluster_id']
            result = {
                'job_posting_id': job['job_posting_id'],
                'cluster_id': cluster_id,
                'cluster_name': cluster_keywords[cluster_id]['name'],
                'cluster_keywords': cluster_keywords[cluster_id]['keywords'],
                'cluster_size': cluster_keywords[cluster_id]['size'],
                'job_title': job['job_title'],
                'company_name': job['company_name']
            }
            
            if track_version:
                result.update({
                    'cluster_run_id': cluster_run_id,
                    'cluster_model_id': f"{self.MODEL_ID}_{self.version}",
                    'cluster_version': cluster_version,
                    'is_active': True
                })
            
            results.append(result)
        
        # Store metadata about this run
        if track_version and results:
            results[0]['run_metadata'] = {
                'stability': stability,
                'previous_run_jobs': len(previous_assignments),
                'current_run_jobs': len(current_assignments)
            }
        
        return results
    
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
    
    def store_clusters(
        self,
        cluster_results: List[Dict[str, Any]],
        enrichment_id: str,
        deactivate_previous: bool = True
    ):
        """
        Store cluster assignments in BigQuery with version tracking.
        
        Args:
            cluster_results: List of cluster assignments (with version info)
            enrichment_id: Reference to job_enrichments
            deactivate_previous: Whether to deactivate previous assignments first
        """
        if not cluster_results:
            return
        
        # Deactivate previous assignments if requested
        if deactivate_previous:
            try:
                self.deactivate_previous_assignments()
            except Exception as e:
                logger.warning(f"Could not deactivate previous assignments: {e}")
        
        rows = []
        for result in cluster_results:
            row = {
                'cluster_assignment_id': str(uuid.uuid4()),
                'job_posting_id': result['job_posting_id'],
                'enrichment_id': enrichment_id,
                'cluster_id': result['cluster_id'],
                'cluster_name': result['cluster_name'],
                'cluster_keywords': json.dumps(result['cluster_keywords']),
                'cluster_size': result['cluster_size'],
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Add version tracking fields if present
            if 'cluster_run_id' in result:
                row['cluster_run_id'] = result['cluster_run_id']
            if 'cluster_model_id' in result:
                row['cluster_model_id'] = result['cluster_model_id']
            if 'cluster_version' in result:
                row['cluster_version'] = result['cluster_version']
            if 'is_active' in result:
                row['is_active'] = result['is_active']
            else:
                row['is_active'] = True  # Default to active
            
            rows.append(row)
        
        table_id = f"{self.dataset_id}.job_clusters"
        errors = self.bigquery_client.insert_rows_json(table_id, rows)
        
        if errors:
            raise Exception(f"Failed to store clusters: {errors}")
        
        logger.info(f"Stored {len(rows)} cluster assignments")
