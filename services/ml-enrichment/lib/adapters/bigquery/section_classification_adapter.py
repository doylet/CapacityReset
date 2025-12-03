"""
BigQuery Section Classification Repository Adapter

Implements the SectionClassificationRepository interface for BigQuery storage.
"""

import json
import logging
from typing import List, Optional, Dict
from datetime import datetime
from google.cloud import bigquery

from ...domain.repositories import SectionClassificationRepository
from ...domain.entities import SectionClassification

logger = logging.getLogger(__name__)


class BigQuerySectionClassificationRepository(SectionClassificationRepository):
    """
    BigQuery implementation of SectionClassificationRepository.
    
    Stores section classifications in BigQuery for analysis and training.
    """
    
    def __init__(
        self,
        project_id: str = "sylvan-replica-478802-p4",
        dataset_id: str = "brightdata_jobs",
        table_name: str = "section_classifications"
    ):
        """
        Initialize the BigQuery adapter.
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            table_name: Table name for section classifications
        """
        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_name = table_name
        self.full_table_id = f"{project_id}.{dataset_id}.{table_name}"
    
    def save(self, classification: SectionClassification) -> None:
        """Save a section classification to BigQuery."""
        row = self._classification_to_row(classification)
        
        errors = self.client.insert_rows_json(self.full_table_id, [row])
        
        if errors:
            logger.error(f"Failed to save classification: {errors}")
            raise Exception(f"Failed to save classification: {errors}")
        
        logger.debug(f"Saved classification for job {classification.job_posting_id}")
    
    def save_batch(self, classifications: List[SectionClassification]) -> int:
        """Save multiple section classifications in a batch."""
        if not classifications:
            return 0
        
        rows = [self._classification_to_row(c) for c in classifications]
        
        errors = self.client.insert_rows_json(self.full_table_id, rows)
        
        if errors:
            logger.error(f"Failed to save batch of classifications: {errors}")
            return len(classifications) - len(errors)
        
        logger.info(f"Saved {len(classifications)} classifications")
        return len(classifications)
    
    def find_by_job(self, job_posting_id: str) -> List[SectionClassification]:
        """Find all classifications for a job posting."""
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        WHERE job_posting_id = @job_posting_id
        ORDER BY section_index
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("job_posting_id", "STRING", job_posting_id)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [self._row_to_classification(row) for row in results]
    
    def find_relevant_sections(
        self,
        job_posting_id: str,
        min_probability: float = 0.5
    ) -> List[SectionClassification]:
        """Find skills-relevant sections for a job posting."""
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        WHERE job_posting_id = @job_posting_id
            AND is_skills_relevant = TRUE
            AND relevance_probability >= @min_probability
        ORDER BY section_index
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("job_posting_id", "STRING", job_posting_id),
                bigquery.ScalarQueryParameter("min_probability", "FLOAT64", min_probability)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [self._row_to_classification(row) for row in results]
    
    def find_by_classifier_version(
        self,
        classifier_version: str,
        limit: int = 100
    ) -> List[SectionClassification]:
        """Find classifications by classifier version."""
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        WHERE classifier_version = @classifier_version
        ORDER BY created_at DESC
        LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("classifier_version", "STRING", classifier_version),
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [self._row_to_classification(row) for row in results]
    
    def get_training_data(
        self,
        limit: int = 1000
    ) -> List[SectionClassification]:
        """Get labeled classifications for training."""
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        WHERE human_label IS NOT NULL
        ORDER BY labeled_at DESC
        LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [self._row_to_classification(row) for row in results]
    
    def add_human_label(
        self,
        classification_id: str,
        is_relevant: bool,
        labeled_by: str
    ) -> None:
        """Add a human label to a classification."""
        query = f"""
        UPDATE `{self.full_table_id}`
        SET
            human_label = @is_relevant,
            labeled_by = @labeled_by,
            labeled_at = CURRENT_TIMESTAMP()
        WHERE classification_id = @classification_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("classification_id", "STRING", classification_id),
                bigquery.ScalarQueryParameter("is_relevant", "BOOL", is_relevant),
                bigquery.ScalarQueryParameter("labeled_by", "STRING", labeled_by)
            ]
        )
        
        self.client.query(query, job_config=job_config).result()
        logger.debug(f"Added human label to classification: {classification_id}")
    
    def get_classifier_stats(
        self,
        classifier_version: Optional[str] = None
    ) -> List[Dict]:
        """Get classification statistics."""
        if classifier_version:
            query = f"""
            SELECT
                classifier_version,
                classification_method,
                COUNT(*) AS total_classifications,
                COUNTIF(is_skills_relevant) AS relevant_count,
                COUNTIF(NOT is_skills_relevant) AS not_relevant_count,
                AVG(relevance_probability) AS avg_probability,
                MIN(created_at) AS first_classification,
                MAX(created_at) AS last_classification
            FROM `{self.full_table_id}`
            WHERE classifier_version = @classifier_version
            GROUP BY classifier_version, classification_method
            ORDER BY last_classification DESC
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("classifier_version", "STRING", classifier_version)
                ]
            )
        else:
            query = f"""
            SELECT
                classifier_version,
                classification_method,
                COUNT(*) AS total_classifications,
                COUNTIF(is_skills_relevant) AS relevant_count,
                COUNTIF(NOT is_skills_relevant) AS not_relevant_count,
                AVG(relevance_probability) AS avg_probability,
                MIN(created_at) AS first_classification,
                MAX(created_at) AS last_classification
            FROM `{self.full_table_id}`
            GROUP BY classifier_version, classification_method
            ORDER BY last_classification DESC
            """
            job_config = bigquery.QueryJobConfig()
        
        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]
    
    def get_header_patterns(self, min_count: int = 10) -> List[Dict]:
        """Get section header patterns with relevance rates."""
        query = f"""
        SELECT
            LOWER(section_header) AS section_header_normalized,
            COUNT(*) AS occurrence_count,
            COUNTIF(is_skills_relevant) AS relevant_count,
            COUNTIF(NOT is_skills_relevant) AS not_relevant_count,
            AVG(CAST(is_skills_relevant AS INT64)) AS relevance_rate
        FROM `{self.full_table_id}`
        WHERE section_header IS NOT NULL
        GROUP BY LOWER(section_header)
        HAVING COUNT(*) >= @min_count
        ORDER BY occurrence_count DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("min_count", "INT64", min_count)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]
    
    def get_accuracy_metrics(
        self,
        classifier_version: str
    ) -> Optional[Dict]:
        """Get accuracy metrics for a classifier version."""
        query = f"""
        WITH labeled_data AS (
            SELECT
                is_skills_relevant AS predicted,
                human_label AS actual
            FROM `{self.full_table_id}`
            WHERE classifier_version = @classifier_version
                AND human_label IS NOT NULL
        )
        SELECT
            COUNT(*) AS total_samples,
            SUM(CASE WHEN predicted = actual THEN 1 ELSE 0 END) AS correct,
            SUM(CASE WHEN predicted = TRUE AND actual = TRUE THEN 1 ELSE 0 END) AS true_positives,
            SUM(CASE WHEN predicted = TRUE AND actual = FALSE THEN 1 ELSE 0 END) AS false_positives,
            SUM(CASE WHEN predicted = FALSE AND actual = TRUE THEN 1 ELSE 0 END) AS false_negatives,
            SUM(CASE WHEN predicted = FALSE AND actual = FALSE THEN 1 ELSE 0 END) AS true_negatives
        FROM labeled_data
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("classifier_version", "STRING", classifier_version)
            ]
        )
        
        results = list(self.client.query(query, job_config=job_config).result())
        
        if not results or results[0]['total_samples'] == 0:
            return None
        
        row = results[0]
        total = row['total_samples']
        tp = row['true_positives'] or 0
        fp = row['false_positives'] or 0
        fn = row['false_negatives'] or 0
        tn = row['true_negatives'] or 0
        
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'total_samples': total,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'confusion_matrix': {
                'true_positives': tp,
                'false_positives': fp,
                'false_negatives': fn,
                'true_negatives': tn
            }
        }
    
    def delete_by_job(self, job_posting_id: str) -> int:
        """Delete all classifications for a job posting."""
        query = f"""
        DELETE FROM `{self.full_table_id}`
        WHERE job_posting_id = @job_posting_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("job_posting_id", "STRING", job_posting_id)
            ]
        )
        
        result = self.client.query(query, job_config=job_config).result()
        deleted = result.num_dml_affected_rows if hasattr(result, 'num_dml_affected_rows') else 0
        logger.info(f"Deleted {deleted} classifications for job {job_posting_id}")
        return deleted
    
    def _classification_to_row(self, classification: SectionClassification) -> Dict:
        """Convert a SectionClassification to a BigQuery row."""
        return {
            'classification_id': classification.classification_id,
            'job_posting_id': classification.job_posting_id,
            'section_text': classification.section_text,
            'section_header': classification.section_header,
            'section_index': classification.section_index,
            'is_skills_relevant': classification.is_skills_relevant,
            'relevance_probability': classification.relevance_probability,
            'classifier_version': classification.classifier_version,
            'classification_method': classification.classification_method,
            'section_word_count': classification.section_word_count,
            'section_char_count': classification.section_char_count,
            'detected_keywords': classification.detected_keywords,
            'created_at': classification.created_at.isoformat(),
            'human_label': classification.human_label,
            'labeled_by': classification.labeled_by,
            'labeled_at': classification.labeled_at.isoformat() if classification.labeled_at else None
        }
    
    def _row_to_classification(self, row) -> SectionClassification:
        """Convert a BigQuery row to a SectionClassification entity."""
        return SectionClassification(
            classification_id=row['classification_id'],
            job_posting_id=row.get('job_posting_id'),
            section_text=row['section_text'],
            section_header=row.get('section_header'),
            section_index=row.get('section_index', 0),
            is_skills_relevant=row['is_skills_relevant'],
            relevance_probability=row['relevance_probability'],
            classifier_version=row['classifier_version'],
            classification_method=row['classification_method'],
            section_word_count=row.get('section_word_count'),
            section_char_count=row.get('section_char_count'),
            detected_keywords=list(row.get('detected_keywords', [])) if row.get('detected_keywords') else [],
            created_at=row['created_at'] if isinstance(row['created_at'], datetime) else datetime.fromisoformat(str(row['created_at'])),
            human_label=row.get('human_label'),
            labeled_by=row.get('labeled_by'),
            labeled_at=row['labeled_at'] if row.get('labeled_at') else None
        )
