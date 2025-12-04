"""
BigQuery Enrichment Adapter

Implements the enrichment repository interface for BigQuery storage.
Handles version-tracked enrichment operations.
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from google.cloud import bigquery

from ...domain.entities import JobEnrichment


logger = logging.getLogger(__name__)


class BigQueryEnrichmentRepository:
    """
    BigQuery implementation of enrichment storage.
    
    Handles CRUD operations for job_enrichments table with version tracking.
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
        self.table_id = f"{project_id}.{dataset_id}.job_enrichments"
        self.client = bigquery.Client()
    
    def create(
        self,
        job_posting_id: str,
        enrichment_type: str,
        model_id: str,
        model_version: str,
        status: str = "pending",
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> JobEnrichment:
        """
        Create a new enrichment record with version tracking.
        
        Args:
            job_posting_id: Reference to job posting
            enrichment_type: Type of enrichment (skills_extraction, embeddings, etc.)
            model_id: Model identifier (e.g., 'skills_extractor')
            model_version: Full model version string
            status: Initial status (pending, processing, success, failed)
            metadata: Optional additional metadata
            error_message: Error message if failed
            
        Returns:
            Created JobEnrichment entity
        """
        enrichment_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Create enrichment_version as denormalized field
        enrichment_version = f"{model_id}_{model_version}" if model_id and model_version else model_version
        
        enrichment = JobEnrichment(
            enrichment_id=enrichment_id,
            job_posting_id=job_posting_id,
            enrichment_type=enrichment_type,
            status=status,
            model_id=model_id,
            model_version=model_version,
            enrichment_version=enrichment_version,
            metadata=metadata,
            error_message=error_message,
            created_at=now,
            updated_at=now
        )
        
        row = {
            'enrichment_id': enrichment.enrichment_id,
            'job_posting_id': enrichment.job_posting_id,
            'enrichment_type': enrichment.enrichment_type,
            'status': enrichment.status,
            'model_id': enrichment.model_id,
            'model_version': enrichment.model_version,
            'enrichment_version': enrichment.enrichment_version,
            'metadata': json.dumps(enrichment.metadata) if enrichment.metadata else None,
            'error_message': enrichment.error_message,
            'created_at': enrichment.created_at.isoformat(),
            'updated_at': enrichment.updated_at.isoformat()
        }
        
        errors = self.client.insert_rows_json(self.table_id, [row])
        
        if errors:
            logger.error(f"Failed to insert enrichment: {errors}")
            raise Exception(f"Failed to insert enrichment: {errors}")
        
        logger.info(
            f"Created enrichment {enrichment_id} for job {job_posting_id} "
            f"(type={enrichment_type}, version={enrichment_version})"
        )
        
        return enrichment
    
    def update_status(
        self,
        enrichment_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update enrichment status.
        
        Args:
            enrichment_id: Enrichment to update
            status: New status
            metadata: Optional metadata to merge
            error_message: Error message if failed
            
        Returns:
            True if update succeeded
        """
        metadata_clause = ""
        if metadata:
            metadata_json = json.dumps(metadata).replace("'", "\\'")
            metadata_clause = f", metadata = '{metadata_json}'"
        
        error_clause = ""
        if error_message:
            error_message_escaped = error_message.replace("'", "\\'")
            error_clause = f", error_message = '{error_message_escaped}'"
        
        query = f"""
        UPDATE `{self.table_id}`
        SET status = '{status}',
            updated_at = CURRENT_TIMESTAMP()
            {metadata_clause}
            {error_clause}
        WHERE enrichment_id = '{enrichment_id}'
        """
        
        try:
            query_job = self.client.query(query)
            query_job.result()
            logger.info(f"Updated enrichment {enrichment_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update enrichment {enrichment_id}: {e}")
            return False
    
    def get_by_job_and_type(
        self,
        job_posting_id: str,
        enrichment_type: str,
        version: Optional[str] = None
    ) -> Optional[JobEnrichment]:
        """
        Get enrichment for a specific job and type.
        
        Args:
            job_posting_id: Job posting ID
            enrichment_type: Type of enrichment
            version: Optional specific version to match
            
        Returns:
            JobEnrichment if found, None otherwise
        """
        version_filter = f"AND enrichment_version = '{version}'" if version else ""
        
        query = f"""
        SELECT *
        FROM `{self.table_id}`
        WHERE job_posting_id = '{job_posting_id}'
            AND enrichment_type = '{enrichment_type}'
            AND status = 'success'
            {version_filter}
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        try:
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            if results:
                row = results[0]
                return self._row_to_entity(row)
            return None
        except Exception as e:
            logger.error(f"Failed to query enrichment: {e}")
            return None
    
    def get_jobs_by_version(
        self,
        enrichment_type: str,
        version: str,
        status: str = "success",
        limit: int = 1000
    ) -> List[str]:
        """
        Get all job IDs enriched with a specific version.
        
        Args:
            enrichment_type: Type of enrichment
            version: Version to filter by
            status: Enrichment status
            limit: Maximum results
            
        Returns:
            List of job_posting_ids
        """
        query = f"""
        SELECT DISTINCT job_posting_id
        FROM `{self.table_id}`
        WHERE enrichment_type = '{enrichment_type}'
            AND enrichment_version = '{version}'
            AND status = '{status}'
        LIMIT {limit}
        """
        
        try:
            query_job = self.client.query(query)
            return [row['job_posting_id'] for row in query_job.result()]
        except Exception as e:
            logger.error(f"Failed to query jobs by version: {e}")
            return []
    
    def _row_to_entity(self, row) -> JobEnrichment:
        """Convert BigQuery row to JobEnrichment entity."""
        metadata = None
        if row.get('metadata'):
            try:
                metadata = json.loads(row['metadata'])
            except json.JSONDecodeError:
                metadata = row['metadata']
        
        return JobEnrichment(
            enrichment_id=row['enrichment_id'],
            job_posting_id=row['job_posting_id'],
            enrichment_type=row['enrichment_type'],
            status=row['status'],
            model_id=row.get('model_id'),
            model_version=row.get('model_version'),
            enrichment_version=row.get('enrichment_version'),
            metadata=metadata,
            error_message=row.get('error_message'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )
