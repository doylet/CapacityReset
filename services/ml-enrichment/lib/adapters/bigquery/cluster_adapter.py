"""
BigQuery Cluster Adapter

Implements the cluster repository interface for BigQuery storage.
Handles version-tracked cluster assignment operations.
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from google.cloud import bigquery

from ...domain.entities import ClusterAssignment


logger = logging.getLogger(__name__)


class BigQueryClusterRepository:
    """
    BigQuery implementation of cluster storage.
    
    Handles CRUD operations for job_clusters table with version tracking.
    """
    
    def __init__(
        self,
        project_id: str = "sylvan-replica-478802-p4",
        dataset_id: str = "brightdata_jobs"
    ):
        """
        Initialize repository.
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset name
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = f"{project_id}.{dataset_id}.job_clusters"
        self.client = bigquery.Client()
    
    def save_assignments(
        self,
        assignments: List[ClusterAssignment],
        deactivate_previous: bool = True
    ) -> int:
        """
        Save cluster assignments with version tracking.
        
        Args:
            assignments: List of ClusterAssignment entities
            deactivate_previous: Whether to deactivate previous assignments first
            
        Returns:
            Number of assignments saved
        """
        if not assignments:
            return 0
        
        # Deactivate previous assignments if requested
        if deactivate_previous:
            self.deactivate_all()
        
        rows = []
        for assignment in assignments:
            row = assignment.to_dict()
            # Convert keywords to JSON string if needed
            if isinstance(row.get('cluster_keywords'), list):
                row['cluster_keywords'] = json.dumps(row['cluster_keywords'])
            rows.append(row)
        
        errors = self.client.insert_rows_json(self.table_id, rows)
        
        if errors:
            logger.error(f"Failed to insert cluster assignments: {errors}")
            raise Exception(f"Failed to insert cluster assignments: {errors}")
        
        logger.info(f"Saved {len(rows)} cluster assignments")
        return len(rows)
    
    def deactivate_all(self):
        """Mark all current active cluster assignments as inactive."""
        query = f"""
        UPDATE `{self.table_id}`
        SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP()
        WHERE is_active = TRUE
        """
        
        try:
            query_job = self.client.query(query)
            query_job.result()
            logger.info("Deactivated all previous cluster assignments")
        except Exception as e:
            logger.warning(f"Could not deactivate previous assignments: {e}")
    
    def deactivate_by_run_id(self, run_id: str):
        """Mark assignments from a specific run as inactive."""
        query = f"""
        UPDATE `{self.table_id}`
        SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP()
        WHERE cluster_run_id = '{run_id}'
        """
        
        try:
            query_job = self.client.query(query)
            query_job.result()
            logger.info(f"Deactivated assignments for run {run_id}")
        except Exception as e:
            logger.error(f"Failed to deactivate assignments for run {run_id}: {e}")
            raise
    
    def get_active_assignments(self, limit: int = 10000) -> List[ClusterAssignment]:
        """Get all currently active cluster assignments."""
        query = f"""
        SELECT *
        FROM `{self.table_id}`
        WHERE is_active = TRUE
        LIMIT {limit}
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return [self._row_to_entity(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to fetch active assignments: {e}")
            return []
    
    def get_assignments_by_run(self, run_id: str) -> List[ClusterAssignment]:
        """Get all cluster assignments for a specific run."""
        query = f"""
        SELECT *
        FROM `{self.table_id}`
        WHERE cluster_run_id = '{run_id}'
        ORDER BY cluster_id, job_posting_id
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return [self._row_to_entity(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to fetch assignments for run {run_id}: {e}")
            return []
    
    def get_assignment_for_job(
        self,
        job_posting_id: str,
        active_only: bool = True
    ) -> Optional[ClusterAssignment]:
        """Get cluster assignment for a specific job."""
        active_filter = "AND is_active = TRUE" if active_only else ""
        
        query = f"""
        SELECT *
        FROM `{self.table_id}`
        WHERE job_posting_id = '{job_posting_id}'
            {active_filter}
        ORDER BY cluster_version DESC
        LIMIT 1
        """
        
        try:
            query_job = self.client.query(query)
            results = list(query_job.result())
            if results:
                return self._row_to_entity(results[0])
            return None
        except Exception as e:
            logger.error(f"Failed to fetch assignment for job {job_posting_id}: {e}")
            return None
    
    def get_job_cluster_history(
        self,
        job_posting_id: str
    ) -> List[ClusterAssignment]:
        """Get full cluster history for a job across all runs."""
        query = f"""
        SELECT *
        FROM `{self.table_id}`
        WHERE job_posting_id = '{job_posting_id}'
        ORDER BY cluster_version DESC
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return [self._row_to_entity(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to fetch cluster history for {job_posting_id}: {e}")
            return []
    
    def get_run_statistics(self, run_id: str) -> Dict[str, Any]:
        """Get statistics for a specific clustering run."""
        query = f"""
        SELECT 
            cluster_run_id,
            cluster_model_id,
            cluster_version,
            COUNT(DISTINCT job_posting_id) as total_jobs,
            COUNT(DISTINCT cluster_id) as num_clusters,
            MIN(created_at) as run_timestamp
        FROM `{self.table_id}`
        WHERE cluster_run_id = '{run_id}'
        GROUP BY cluster_run_id, cluster_model_id, cluster_version
        """
        
        try:
            query_job = self.client.query(query)
            results = list(query_job.result())
            if results:
                row = results[0]
                return {
                    'cluster_run_id': row['cluster_run_id'],
                    'cluster_model_id': row['cluster_model_id'],
                    'cluster_version': row['cluster_version'],
                    'total_jobs': row['total_jobs'],
                    'num_clusters': row['num_clusters'],
                    'run_timestamp': row['run_timestamp']
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to fetch run statistics for {run_id}: {e}")
            return {}
    
    def list_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent clustering runs."""
        query = f"""
        SELECT 
            cluster_run_id,
            cluster_model_id,
            cluster_version,
            COUNT(DISTINCT job_posting_id) as total_jobs,
            COUNT(DISTINCT cluster_id) as num_clusters,
            MIN(created_at) as run_timestamp,
            MAX(CASE WHEN is_active THEN 1 ELSE 0 END) as is_current
        FROM `{self.table_id}`
        GROUP BY cluster_run_id, cluster_model_id, cluster_version
        ORDER BY cluster_version DESC
        LIMIT {limit}
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return [
                {
                    'cluster_run_id': row['cluster_run_id'],
                    'cluster_model_id': row['cluster_model_id'],
                    'cluster_version': row['cluster_version'],
                    'total_jobs': row['total_jobs'],
                    'num_clusters': row['num_clusters'],
                    'run_timestamp': row['run_timestamp'],
                    'is_current': bool(row['is_current'])
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Failed to list runs: {e}")
            return []
    
    def _row_to_entity(self, row) -> ClusterAssignment:
        """Convert BigQuery row to ClusterAssignment entity."""
        keywords = row.get('cluster_keywords')
        if keywords and isinstance(keywords, str):
            try:
                keywords = json.loads(keywords)
            except json.JSONDecodeError:
                keywords = []
        
        return ClusterAssignment(
            cluster_assignment_id=row.get('cluster_assignment_id', str(uuid.uuid4())),
            job_posting_id=row.get('job_posting_id'),
            enrichment_id=row.get('enrichment_id'),
            cluster_id=row['cluster_id'],
            cluster_name=row['cluster_name'],
            cluster_keywords=keywords or [],
            cluster_size=row.get('cluster_size', 0),
            cluster_run_id=row.get('cluster_run_id', ''),
            cluster_model_id=row.get('cluster_model_id', ''),
            cluster_version=row.get('cluster_version', 1),
            is_active=row.get('is_active', False),
            created_at=row.get('created_at') if row.get('created_at') else datetime.utcnow()
        )
