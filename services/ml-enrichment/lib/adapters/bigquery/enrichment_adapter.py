"""
BigQuery Enrichment Repository Adapter

Implements enrichment tracking storage with version tracking support.
Follows the existing repository pattern in the codebase.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from google.cloud import bigquery

from ...domain.entities import JobEnrichment


class BigQueryEnrichmentRepository:
    """
    BigQuery adapter for job enrichment tracking.
    
    Provides CRUD operations for enrichments with version tracking support.
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
        self.table_id = f"{self.full_dataset_id}.job_enrichments"
        self.client = bigquery.Client()
    
    def save(self, enrichment: JobEnrichment) -> str:
        """
        Save an enrichment record with version tracking.
        
        Args:
            enrichment: JobEnrichment entity to save
            
        Returns:
            The enrichment_id
        """
        row = {
            'enrichment_id': enrichment.enrichment_id,
            'job_posting_id': enrichment.job_posting_id,
            'enrichment_type': enrichment.enrichment_type,
            'status': enrichment.status,
            'model_id': enrichment.model_id,
            'model_version': enrichment.model_version,
            'enrichment_version': enrichment.enrichment_version,
            'created_at': enrichment.created_at.isoformat(),
            'updated_at': enrichment.updated_at.isoformat(),
            'metadata': json.dumps(enrichment.metadata) if enrichment.metadata else None,
            'error_message': enrichment.error_message,
            'processing_time_ms': enrichment.processing_time_ms,
            'retry_count': enrichment.retry_count
        }
        
        errors = self.client.insert_rows_json(self.table_id, [row])
        
        if errors:
            raise Exception(f"Failed to save enrichment: {errors}")
        
        return enrichment.enrichment_id
    
    def save_with_version(
        self,
        job_posting_id: str,
        enrichment_type: str,
        status: str,
        model_id: str,
        model_version: str,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> str:
        """
        Save enrichment record with explicit version tracking.
        
        Convenience method that creates and saves a JobEnrichment with version info.
        
        Args:
            job_posting_id: Reference to job
            enrichment_type: Type of enrichment
            status: Enrichment status
            model_id: Model identifier
            model_version: Model version string
            metadata: Optional enrichment metadata
            error_message: Error details if failed
            processing_time_ms: Processing time
            
        Returns:
            The enrichment_id
        """
        enrichment = JobEnrichment(
            job_posting_id=job_posting_id,
            enrichment_type=enrichment_type,
            status=status,
            model_id=model_id,
            model_version=model_version,
            metadata=metadata,
            error_message=error_message,
            processing_time_ms=processing_time_ms
        )
        
        return self.save(enrichment)
    
    def find_by_job_and_type(
        self,
        job_posting_id: str,
        enrichment_type: str,
        version: Optional[str] = None
    ) -> Optional[JobEnrichment]:
        """
        Find enrichment by job ID and type.
        
        Args:
            job_posting_id: Job posting ID
            enrichment_type: Type of enrichment
            version: Optional version filter
            
        Returns:
            JobEnrichment or None
        """
        version_filter = f"AND enrichment_version = '{version}'" if version else ""
        
        query = f"""
        SELECT *
        FROM `{self.table_id}`
        WHERE job_posting_id = '{job_posting_id}'
            AND enrichment_type = '{enrichment_type}'
            {version_filter}
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        results = list(self.client.query(query).result())
        
        if not results:
            return None
        
        row = results[0]
        return self._row_to_entity(row)
    
    def find_by_version(
        self,
        enrichment_type: str,
        version: str,
        status: str = 'success',
        limit: int = 100
    ) -> List[JobEnrichment]:
        """
        Find all enrichments for a specific version.
        
        Args:
            enrichment_type: Type of enrichment
            version: Version to filter by
            status: Status filter
            limit: Maximum results
            
        Returns:
            List of JobEnrichment entities
        """
        query = f"""
        SELECT *
        FROM `{self.table_id}`
        WHERE enrichment_type = '{enrichment_type}'
            AND enrichment_version = '{version}'
            AND status = '{status}'
        ORDER BY created_at DESC
        LIMIT {limit}
        """
        
        results = self.client.query(query).result()
        
        return [self._row_to_entity(row) for row in results]
    
    def count_by_version(self, enrichment_type: str) -> Dict[str, int]:
        """
        Count enrichments grouped by version.
        
        Args:
            enrichment_type: Type of enrichment
            
        Returns:
            Dictionary of version -> count
        """
        query = f"""
        SELECT 
            COALESCE(enrichment_version, 'legacy') AS version,
            COUNT(*) AS count
        FROM `{self.table_id}`
        WHERE enrichment_type = '{enrichment_type}'
            AND status = 'success'
        GROUP BY enrichment_version
        ORDER BY count DESC
        """
        
        results = self.client.query(query).result()
        
        return {row['version']: row['count'] for row in results}
    
    def update_status(
        self,
        enrichment_id: str,
        status: str,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update enrichment status.
        
        Args:
            enrichment_id: ID of enrichment to update
            status: New status
            error_message: Error message if failed
            metadata: Updated metadata
            
        Returns:
            True if updated successfully
        """
        updates = [f"status = '{status}'", f"updated_at = '{datetime.utcnow().isoformat()}'"]
        
        if error_message:
            updates.append(f"error_message = '{error_message}'")
        
        if metadata:
            updates.append(f"metadata = '{json.dumps(metadata)}'")
        
        query = f"""
        UPDATE `{self.table_id}`
        SET {', '.join(updates)}
        WHERE enrichment_id = '{enrichment_id}'
        """
        
        try:
            self.client.query(query).result()
            return True
        except Exception:
            return False
    
    def get_outdated_enrichments(
        self,
        enrichment_type: str,
        current_version: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find enrichments with outdated versions.
        
        Args:
            enrichment_type: Type of enrichment
            current_version: The current/target version
            limit: Maximum results
            
        Returns:
            List of outdated enrichment info
        """
        query = f"""
        SELECT 
            job_posting_id,
            enrichment_id,
            enrichment_version AS old_version,
            '{current_version}' AS target_version,
            created_at AS enriched_at
        FROM `{self.table_id}`
        WHERE enrichment_type = '{enrichment_type}'
            AND status = 'success'
            AND (enrichment_version != '{current_version}' OR enrichment_version IS NULL)
        ORDER BY created_at ASC
        LIMIT {limit}
        """
        
        results = self.client.query(query).result()
        
        return [
            {
                'job_posting_id': row['job_posting_id'],
                'enrichment_id': row['enrichment_id'],
                'old_version': row['old_version'],
                'target_version': row['target_version'],
                'enriched_at': row['enriched_at']
            }
            for row in results
        ]
    
    def _row_to_entity(self, row) -> JobEnrichment:
        """Convert BigQuery row to JobEnrichment entity."""
        metadata = row.get('metadata')
        if metadata and isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = None
        
        return JobEnrichment(
            enrichment_id=row['enrichment_id'],
            job_posting_id=row['job_posting_id'],
            enrichment_type=row['enrichment_type'],
            status=row['status'],
            model_id=row.get('model_id'),
            model_version=row.get('model_version'),
            enrichment_version=row.get('enrichment_version'),
            created_at=row['created_at'] if isinstance(row['created_at'], datetime) 
                       else datetime.fromisoformat(str(row['created_at'])),
            updated_at=row['updated_at'] if isinstance(row['updated_at'], datetime)
                       else datetime.fromisoformat(str(row['updated_at'])),
            metadata=metadata,
            error_message=row.get('error_message'),
            processing_time_ms=row.get('processing_time_ms'),
            retry_count=row.get('retry_count', 0)
        )
