"""
BigQuery Cluster Repository Adapter

Implements cluster assignment storage with version tracking support.
Follows the existing repository pattern in the codebase.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from google.cloud import bigquery

from ...domain.entities import ClusterAssignment


class BigQueryClusterRepository:
    """
    BigQuery adapter for job cluster assignments.
    
    Provides CRUD operations for cluster assignments with version tracking.
    """
    
    def __init__(
        self,
        project_id: str = "sylvan-replica-478802-p4",
        dataset_id: str = "brightdata_jobs"
    ):
        """
        Initialize the repository.
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset name
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.full_dataset_id = f"{project_id}.{dataset_id}"
        self.table_id = f"{self.full_dataset_id}.job_clusters"
        self.client = bigquery.Client()
    
    def save(self, assignment: ClusterAssignment) -> str:
        """
        Save a cluster assignment with version tracking.
        
        Args:
            assignment: ClusterAssignment entity to save
            
        Returns:
            The cluster_assignment_id
        """
        row = {
            'cluster_assignment_id': assignment.cluster_assignment_id,
            'job_posting_id': assignment.job_posting_id,
            'enrichment_id': assignment.enrichment_id,
            'cluster_id': assignment.cluster_id,
            'cluster_name': assignment.cluster_name,
            'cluster_keywords': json.dumps(assignment.cluster_keywords),
            'cluster_size': assignment.cluster_size,
            'cluster_run_id': assignment.cluster_run_id,
            'cluster_model_id': assignment.cluster_model_id,
            'cluster_version': assignment.cluster_version,
            'is_active': assignment.is_active,
            'created_at': assignment.created_at.isoformat()
        }
        
        errors = self.client.insert_rows_json(self.table_id, [row])
        
        if errors:
            raise Exception(f"Failed to save cluster assignment: {errors}")
        
        return assignment.cluster_assignment_id
    
    def save_batch(self, assignments: List[ClusterAssignment]) -> int:
        """
        Save multiple cluster assignments in batch.
        
        Args:
            assignments: List of ClusterAssignment entities
            
        Returns:
            Number of assignments saved
        """
        if not assignments:
            return 0
        
        rows = []
        for assignment in assignments:
            rows.append({
                'cluster_assignment_id': assignment.cluster_assignment_id,
                'job_posting_id': assignment.job_posting_id,
                'enrichment_id': assignment.enrichment_id,
                'cluster_id': assignment.cluster_id,
                'cluster_name': assignment.cluster_name,
                'cluster_keywords': json.dumps(assignment.cluster_keywords),
                'cluster_size': assignment.cluster_size,
                'cluster_run_id': assignment.cluster_run_id,
                'cluster_model_id': assignment.cluster_model_id,
                'cluster_version': assignment.cluster_version,
                'is_active': assignment.is_active,
                'created_at': assignment.created_at.isoformat()
            })
        
        errors = self.client.insert_rows_json(self.table_id, rows)
        
        if errors:
            raise Exception(f"Failed to save cluster assignments: {errors}")
        
        return len(assignments)
    
    def find_by_run_id(
        self,
        cluster_run_id: str,
        active_only: bool = False
    ) -> List[ClusterAssignment]:
        """
        Find all assignments for a cluster run.
        
        Args:
            cluster_run_id: The cluster run ID
            active_only: If True, only return active assignments
            
        Returns:
            List of ClusterAssignment entities
        """
        active_filter = "AND is_active = TRUE" if active_only else ""
        
        query = f"""
        SELECT *
        FROM `{self.table_id}`
        WHERE cluster_run_id = '{cluster_run_id}'
            {active_filter}
        ORDER BY cluster_id, job_posting_id
        """
        
        results = self.client.query(query).result()
        
        return [self._row_to_entity(row) for row in results]
    
    def find_active_by_job(self, job_posting_id: str) -> Optional[ClusterAssignment]:
        """
        Find the active cluster assignment for a job.
        
        Args:
            job_posting_id: Job posting ID
            
        Returns:
            ClusterAssignment or None
        """
        query = f"""
        SELECT *
        FROM `{self.table_id}`
        WHERE job_posting_id = '{job_posting_id}'
            AND is_active = TRUE
        LIMIT 1
        """
        
        results = list(self.client.query(query).result())
        
        if not results:
            return None
        
        return self._row_to_entity(results[0])
    
    def find_history_by_job(
        self,
        job_posting_id: str,
        limit: int = 10
    ) -> List[ClusterAssignment]:
        """
        Find cluster assignment history for a job.
        
        Args:
            job_posting_id: Job posting ID
            limit: Maximum results
            
        Returns:
            List of ClusterAssignment entities (newest first)
        """
        query = f"""
        SELECT *
        FROM `{self.table_id}`
        WHERE job_posting_id = '{job_posting_id}'
        ORDER BY cluster_version DESC
        LIMIT {limit}
        """
        
        results = self.client.query(query).result()
        
        return [self._row_to_entity(row) for row in results]
    
    def deactivate_by_run_id(self, cluster_run_id: str) -> int:
        """
        Deactivate all assignments for a run.
        
        Args:
            cluster_run_id: Run ID to deactivate
            
        Returns:
            Number of assignments deactivated
        """
        query = f"""
        UPDATE `{self.table_id}`
        SET is_active = FALSE
        WHERE cluster_run_id = '{cluster_run_id}'
            AND is_active = TRUE
        """
        
        job = self.client.query(query)
        job.result()
        
        return job.num_dml_affected_rows or 0
    
    def deactivate_all_active(self) -> int:
        """
        Deactivate all active assignments.
        
        Returns:
            Number of assignments deactivated
        """
        query = f"""
        UPDATE `{self.table_id}`
        SET is_active = FALSE
        WHERE is_active = TRUE
        """
        
        job = self.client.query(query)
        job.result()
        
        return job.num_dml_affected_rows or 0
    
    def list_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List cluster runs with summary information.
        
        Args:
            limit: Maximum runs to return
            
        Returns:
            List of run summaries
        """
        query = f"""
        SELECT 
            cluster_run_id,
            cluster_model_id,
            MIN(created_at) AS run_start,
            MAX(created_at) AS run_end,
            COUNT(DISTINCT job_posting_id) AS jobs_clustered,
            COUNT(DISTINCT cluster_id) AS clusters_created,
            COUNTIF(is_active) AS active_assignments
        FROM `{self.table_id}`
        GROUP BY cluster_run_id, cluster_model_id
        ORDER BY run_start DESC
        LIMIT {limit}
        """
        
        results = self.client.query(query).result()
        
        return [
            {
                'cluster_run_id': row['cluster_run_id'],
                'cluster_model_id': row['cluster_model_id'],
                'run_start': row['run_start'],
                'run_end': row['run_end'],
                'jobs_clustered': row['jobs_clustered'],
                'clusters_created': row['clusters_created'],
                'active_assignments': row['active_assignments']
            }
            for row in results
        ]
    
    def calculate_stability(
        self,
        old_run_id: str,
        new_run_id: str
    ) -> Dict[str, Any]:
        """
        Calculate stability metrics between two runs.
        
        Args:
            old_run_id: Previous run ID
            new_run_id: New run ID
            
        Returns:
            Stability metrics
        """
        query = f"""
        WITH comparison AS (
            SELECT 
                CASE 
                    WHEN old.cluster_id IS NULL THEN 'new'
                    WHEN new.cluster_id IS NULL THEN 'removed'
                    WHEN old.cluster_id = new.cluster_id THEN 'stable'
                    ELSE 'changed'
                END AS status
            FROM (
                SELECT job_posting_id, cluster_id
                FROM `{self.table_id}`
                WHERE cluster_run_id = '{old_run_id}'
            ) old
            FULL OUTER JOIN (
                SELECT job_posting_id, cluster_id
                FROM `{self.table_id}`
                WHERE cluster_run_id = '{new_run_id}'
            ) new
            ON old.job_posting_id = new.job_posting_id
        )
        SELECT 
            status,
            COUNT(*) AS count
        FROM comparison
        GROUP BY status
        """
        
        results = self.client.query(query).result()
        
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
    
    def _row_to_entity(self, row) -> ClusterAssignment:
        """Convert BigQuery row to ClusterAssignment entity."""
        keywords = row.get('cluster_keywords', '[]')
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords)
            except json.JSONDecodeError:
                keywords = []
        
        return ClusterAssignment(
            cluster_assignment_id=row['cluster_assignment_id'],
            job_posting_id=row['job_posting_id'],
            enrichment_id=row.get('enrichment_id'),
            cluster_id=row['cluster_id'],
            cluster_name=row['cluster_name'],
            cluster_keywords=keywords,
            cluster_size=row.get('cluster_size', 0),
            cluster_run_id=row.get('cluster_run_id', str(uuid.uuid4())),
            cluster_model_id=row.get('cluster_model_id', 'v1.0-kmeans-tfidf'),
            cluster_version=row.get('cluster_version', 1),
            is_active=row.get('is_active', True),
            created_at=row['created_at'] if isinstance(row['created_at'], datetime)
                       else datetime.fromisoformat(str(row['created_at']))
        )
