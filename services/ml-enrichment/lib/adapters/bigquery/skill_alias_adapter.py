"""
BigQuery Skill Alias Repository Adapter

Implements the SkillAliasRepository interface for BigQuery storage.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
from google.cloud import bigquery

from ...domain.repositories import SkillAliasRepository
from ...domain.entities import SkillAlias

logger = logging.getLogger(__name__)


class BigQuerySkillAliasRepository(SkillAliasRepository):
    """
    BigQuery implementation of SkillAliasRepository.
    
    Stores skill aliases in BigQuery for persistence and querying.
    """
    
    def __init__(
        self,
        project_id: str = "sylvan-replica-478802-p4",
        dataset_id: str = "brightdata_jobs",
        table_name: str = "skill_aliases"
    ):
        """
        Initialize the BigQuery adapter.
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            table_name: Table name for skill aliases
        """
        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_name = table_name
        self.full_table_id = f"{project_id}.{dataset_id}.{table_name}"
    
    def save(self, alias: SkillAlias) -> None:
        """Save a skill alias to BigQuery."""
        row = {
            'alias_id': alias.alias_id,
            'alias_text': alias.alias_text,
            'canonical_name': alias.canonical_name,
            'skill_category': alias.skill_category,
            'source': alias.source,
            'confidence': alias.confidence,
            'created_at': alias.created_at.isoformat(),
            'created_by': alias.created_by,
            'is_active': alias.is_active,
            'usage_count': alias.usage_count,
            'last_used_at': alias.last_used_at.isoformat() if alias.last_used_at else None
        }
        
        errors = self.client.insert_rows_json(self.full_table_id, [row])
        
        if errors:
            logger.error(f"Failed to save alias: {errors}")
            raise Exception(f"Failed to save alias: {errors}")
        
        logger.debug(f"Saved alias: {alias.alias_text} -> {alias.canonical_name}")
    
    def save_batch(self, aliases: List[SkillAlias]) -> int:
        """Save multiple skill aliases in a batch."""
        if not aliases:
            return 0
        
        rows = []
        for alias in aliases:
            rows.append({
                'alias_id': alias.alias_id,
                'alias_text': alias.alias_text,
                'canonical_name': alias.canonical_name,
                'skill_category': alias.skill_category,
                'source': alias.source,
                'confidence': alias.confidence,
                'created_at': alias.created_at.isoformat(),
                'created_by': alias.created_by,
                'is_active': alias.is_active,
                'usage_count': alias.usage_count,
                'last_used_at': alias.last_used_at.isoformat() if alias.last_used_at else None
            })
        
        errors = self.client.insert_rows_json(self.full_table_id, rows)
        
        if errors:
            logger.error(f"Failed to save batch of aliases: {errors}")
            return len(aliases) - len(errors)
        
        logger.info(f"Saved {len(aliases)} aliases")
        return len(aliases)
    
    def find_by_alias_text(self, alias_text: str) -> Optional[SkillAlias]:
        """Find a skill alias by its alias text."""
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        WHERE LOWER(alias_text) = LOWER(@alias_text)
            AND is_active = TRUE
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("alias_text", "STRING", alias_text)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        
        for row in results:
            return self._row_to_alias(row)
        
        return None
    
    def find_by_canonical_name(self, canonical_name: str) -> List[SkillAlias]:
        """Find all aliases that map to a canonical name."""
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        WHERE canonical_name = @canonical_name
            AND is_active = TRUE
        ORDER BY confidence DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("canonical_name", "STRING", canonical_name)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [self._row_to_alias(row) for row in results]
    
    def find_by_category(self, category: str) -> List[SkillAlias]:
        """Find all aliases in a category."""
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        WHERE skill_category = @category
            AND is_active = TRUE
        ORDER BY canonical_name, confidence DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("category", "STRING", category)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [self._row_to_alias(row) for row in results]
    
    def find_all_active(self) -> List[SkillAlias]:
        """Find all active aliases."""
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        WHERE is_active = TRUE
        ORDER BY skill_category, canonical_name
        """
        
        results = self.client.query(query).result()
        return [self._row_to_alias(row) for row in results]
    
    def get_alias_mapping(self) -> Dict[str, str]:
        """Get a dictionary mapping all aliases to canonical names."""
        query = f"""
        SELECT LOWER(alias_text) as alias_lower, canonical_name
        FROM `{self.full_table_id}`
        WHERE is_active = TRUE
        """
        
        results = self.client.query(query).result()
        return {row['alias_lower']: row['canonical_name'] for row in results}
    
    def update(self, alias: SkillAlias) -> None:
        """Update an existing skill alias."""
        query = f"""
        UPDATE `{self.full_table_id}`
        SET
            canonical_name = @canonical_name,
            skill_category = @skill_category,
            confidence = @confidence,
            is_active = @is_active,
            usage_count = @usage_count,
            last_used_at = @last_used_at
        WHERE alias_id = @alias_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("alias_id", "STRING", alias.alias_id),
                bigquery.ScalarQueryParameter("canonical_name", "STRING", alias.canonical_name),
                bigquery.ScalarQueryParameter("skill_category", "STRING", alias.skill_category),
                bigquery.ScalarQueryParameter("confidence", "FLOAT64", alias.confidence),
                bigquery.ScalarQueryParameter("is_active", "BOOL", alias.is_active),
                bigquery.ScalarQueryParameter("usage_count", "INT64", alias.usage_count),
                bigquery.ScalarQueryParameter(
                    "last_used_at", "TIMESTAMP",
                    alias.last_used_at.isoformat() if alias.last_used_at else None
                )
            ]
        )
        
        self.client.query(query, job_config=job_config).result()
        logger.debug(f"Updated alias: {alias.alias_text}")
    
    def deactivate(self, alias_id: str) -> None:
        """Deactivate a skill alias."""
        query = f"""
        UPDATE `{self.full_table_id}`
        SET is_active = FALSE
        WHERE alias_id = @alias_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("alias_id", "STRING", alias_id)
            ]
        )
        
        self.client.query(query, job_config=job_config).result()
        logger.debug(f"Deactivated alias: {alias_id}")
    
    def record_usage(self, alias_text: str) -> None:
        """Record that an alias was used for resolution."""
        query = f"""
        UPDATE `{self.full_table_id}`
        SET
            usage_count = usage_count + 1,
            last_used_at = CURRENT_TIMESTAMP()
        WHERE LOWER(alias_text) = LOWER(@alias_text)
            AND is_active = TRUE
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("alias_text", "STRING", alias_text)
            ]
        )
        
        self.client.query(query, job_config=job_config).result()
    
    def get_usage_stats(self, limit: int = 100) -> List[Dict]:
        """Get usage statistics for aliases."""
        query = f"""
        SELECT
            alias_text,
            canonical_name,
            skill_category,
            usage_count,
            last_used_at,
            confidence
        FROM `{self.full_table_id}`
        WHERE is_active = TRUE
        ORDER BY usage_count DESC
        LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]
    
    def _row_to_alias(self, row) -> SkillAlias:
        """Convert a BigQuery row to a SkillAlias entity."""
        return SkillAlias(
            alias_id=row['alias_id'],
            alias_text=row['alias_text'],
            canonical_name=row['canonical_name'],
            skill_category=row['skill_category'],
            source=row.get('source', 'manual'),
            confidence=row.get('confidence', 1.0),
            created_at=row['created_at'] if isinstance(row['created_at'], datetime) else datetime.fromisoformat(str(row['created_at'])),
            created_by=row.get('created_by'),
            is_active=row.get('is_active', True),
            usage_count=row.get('usage_count', 0),
            last_used_at=row['last_used_at'] if row.get('last_used_at') else None
        )
