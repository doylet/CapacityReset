"""
BigQuery Evaluation Repository Adapter

Implements the EvaluationResultRepository interface for BigQuery storage.
"""

import json
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from google.cloud import bigquery

from ...domain.repositories import EvaluationResultRepository
from ...domain.entities import EvaluationResult

logger = logging.getLogger(__name__)


class BigQueryEvaluationRepository(EvaluationResultRepository):
    """
    BigQuery implementation of EvaluationResultRepository.
    
    Stores evaluation results in BigQuery for historical tracking.
    """
    
    def __init__(
        self,
        project_id: str = "sylvan-replica-478802-p4",
        dataset_id: str = "brightdata_jobs",
        table_name: str = "evaluation_results"
    ):
        """
        Initialize the BigQuery adapter.
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            table_name: Table name for evaluation results
        """
        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_name = table_name
        self.full_table_id = f"{project_id}.{dataset_id}.{table_name}"
    
    def save(self, result: EvaluationResult) -> None:
        """Save an evaluation result to BigQuery."""
        row = {
            'evaluation_id': result.evaluation_id,
            'model_id': result.model_id,
            'model_version': result.model_version,
            'dataset_version': result.dataset_version,
            'dataset_path': result.dataset_path,
            'sample_count': result.sample_count,
            'overall_precision': result.overall_precision,
            'overall_recall': result.overall_recall,
            'overall_f1': result.overall_f1,
            'overall_accuracy': result.overall_accuracy,
            'category_metrics': json.dumps(result.category_metrics) if result.category_metrics else None,
            'evaluation_date': result.evaluation_date.isoformat(),
            'execution_time_seconds': result.execution_time_seconds,
            'is_ci_run': result.is_ci_run,
            'ci_build_id': result.ci_build_id,
            'ci_pipeline_name': result.ci_pipeline_name,
            'threshold_f1': result.threshold_f1,
            'threshold_passed': result.threshold_passed,
            'notes': result.notes,
            'environment': result.environment,
            'gcp_project': result.gcp_project,
            'created_at': result.created_at.isoformat()
        }
        
        errors = self.client.insert_rows_json(self.full_table_id, [row])
        
        if errors:
            logger.error(f"Failed to save evaluation result: {errors}")
            raise Exception(f"Failed to save evaluation result: {errors}")
        
        logger.info(f"Saved evaluation result: {result.evaluation_id} for {result.model_id}")
    
    def find_by_id(self, evaluation_id: str) -> Optional[EvaluationResult]:
        """Find an evaluation result by ID."""
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        WHERE evaluation_id = @evaluation_id
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("evaluation_id", "STRING", evaluation_id)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        
        for row in results:
            return self._row_to_result(row)
        
        return None
    
    def find_by_model(
        self,
        model_id: str,
        model_version: Optional[str] = None,
        limit: int = 10
    ) -> List[EvaluationResult]:
        """Find evaluation results for a model."""
        if model_version:
            query = f"""
            SELECT *
            FROM `{self.full_table_id}`
            WHERE model_id = @model_id
                AND model_version = @model_version
            ORDER BY evaluation_date DESC
            LIMIT @limit
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("model_id", "STRING", model_id),
                    bigquery.ScalarQueryParameter("model_version", "STRING", model_version),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
        else:
            query = f"""
            SELECT *
            FROM `{self.full_table_id}`
            WHERE model_id = @model_id
            ORDER BY evaluation_date DESC
            LIMIT @limit
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("model_id", "STRING", model_id),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
        
        results = self.client.query(query, job_config=job_config).result()
        return [self._row_to_result(row) for row in results]
    
    def find_latest(self, model_id: str) -> Optional[EvaluationResult]:
        """Find the most recent evaluation for a model."""
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        WHERE model_id = @model_id
        ORDER BY evaluation_date DESC
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("model_id", "STRING", model_id)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        
        for row in results:
            return self._row_to_result(row)
        
        return None
    
    def find_by_date_range(
        self,
        model_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[EvaluationResult]:
        """Find evaluations within a date range."""
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        WHERE model_id = @model_id
            AND evaluation_date >= @start_date
            AND evaluation_date <= @end_date
        ORDER BY evaluation_date DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("model_id", "STRING", model_id),
                bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
                bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [self._row_to_result(row) for row in results]
    
    def find_ci_runs(
        self,
        model_id: Optional[str] = None,
        limit: int = 50
    ) -> List[EvaluationResult]:
        """Find CI pipeline evaluation runs."""
        if model_id:
            query = f"""
            SELECT *
            FROM `{self.full_table_id}`
            WHERE is_ci_run = TRUE
                AND model_id = @model_id
            ORDER BY evaluation_date DESC
            LIMIT @limit
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("model_id", "STRING", model_id),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
        else:
            query = f"""
            SELECT *
            FROM `{self.full_table_id}`
            WHERE is_ci_run = TRUE
            ORDER BY evaluation_date DESC
            LIMIT @limit
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
        
        results = self.client.query(query, job_config=job_config).result()
        return [self._row_to_result(row) for row in results]
    
    def get_metric_trends(
        self,
        model_id: str,
        metric: str = 'f1',
        days: int = 30
    ) -> List[Dict]:
        """Get metric trends over time."""
        metric_column = f"overall_{metric}"
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = f"""
        SELECT
            DATE(evaluation_date) as date,
            AVG({metric_column}) as avg_value,
            MAX({metric_column}) as max_value,
            MIN({metric_column}) as min_value,
            COUNT(*) as eval_count,
            model_version
        FROM `{self.full_table_id}`
        WHERE model_id = @model_id
            AND evaluation_date >= @start_date
        GROUP BY DATE(evaluation_date), model_version
        ORDER BY date DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("model_id", "STRING", model_id),
                bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]
    
    def compare_versions(
        self,
        model_id: str,
        version_a: str,
        version_b: str
    ) -> Optional[Dict]:
        """Compare evaluation results between two versions."""
        query = f"""
        WITH version_stats AS (
            SELECT
                model_version,
                AVG(overall_precision) as avg_precision,
                AVG(overall_recall) as avg_recall,
                AVG(overall_f1) as avg_f1,
                COUNT(*) as eval_count
            FROM `{self.full_table_id}`
            WHERE model_id = @model_id
                AND model_version IN (@version_a, @version_b)
            GROUP BY model_version
        )
        SELECT * FROM version_stats
        ORDER BY model_version
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("model_id", "STRING", model_id),
                bigquery.ScalarQueryParameter("version_a", "STRING", version_a),
                bigquery.ScalarQueryParameter("version_b", "STRING", version_b)
            ]
        )
        
        results = list(self.client.query(query, job_config=job_config).result())
        
        if len(results) < 2:
            return None
        
        stats_a = dict(results[0]) if results[0]['model_version'] == version_a else dict(results[1])
        stats_b = dict(results[1]) if results[1]['model_version'] == version_b else dict(results[0])
        
        return {
            'version_a': version_a,
            'version_b': version_b,
            'version_a_stats': stats_a,
            'version_b_stats': stats_b,
            'precision_diff': stats_b['avg_precision'] - stats_a['avg_precision'],
            'recall_diff': stats_b['avg_recall'] - stats_a['avg_recall'],
            'f1_diff': stats_b['avg_f1'] - stats_a['avg_f1']
        }
    
    def get_category_breakdown(
        self,
        evaluation_id: str
    ) -> Dict[str, Dict[str, float]]:
        """Get per-category metrics for an evaluation."""
        result = self.find_by_id(evaluation_id)
        if result:
            return result.category_metrics
        return {}
    
    def delete(self, evaluation_id: str) -> bool:
        """Delete an evaluation result."""
        query = f"""
        DELETE FROM `{self.full_table_id}`
        WHERE evaluation_id = @evaluation_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("evaluation_id", "STRING", evaluation_id)
            ]
        )
        
        result = self.client.query(query, job_config=job_config).result()
        return result.num_dml_affected_rows > 0 if hasattr(result, 'num_dml_affected_rows') else True
    
    def get_recent_results(
        self,
        model_id: Optional[str] = None,
        limit: int = 10
    ) -> List[EvaluationResult]:
        """
        Get recent evaluation results.
        
        Args:
            model_id: Optional model ID to filter by
            limit: Maximum number of results
            
        Returns:
            List of EvaluationResult entities
        """
        if model_id:
            return self.find_by_model(model_id=model_id, limit=limit)
        
        query = f"""
        SELECT *
        FROM `{self.full_table_id}`
        ORDER BY evaluation_date DESC
        LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )
        
        try:
            results = self.client.query(query, job_config=job_config).result()
            return [self._row_to_result(row) for row in results]
        except Exception as e:
            logger.warning(f"Could not fetch recent results: {e}")
            return []
    
    def _row_to_result(self, row) -> EvaluationResult:
        """Convert a BigQuery row to an EvaluationResult entity."""
        category_metrics = {}
        if row.get('category_metrics'):
            try:
                category_metrics = json.loads(row['category_metrics'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        return EvaluationResult(
            evaluation_id=row['evaluation_id'],
            model_id=row['model_id'],
            model_version=row['model_version'],
            dataset_version=row['dataset_version'],
            dataset_path=row.get('dataset_path'),
            sample_count=row['sample_count'],
            overall_precision=row['overall_precision'],
            overall_recall=row['overall_recall'],
            overall_f1=row['overall_f1'],
            overall_accuracy=row.get('overall_accuracy'),
            category_metrics=category_metrics,
            evaluation_date=row['evaluation_date'] if isinstance(row['evaluation_date'], datetime) else datetime.fromisoformat(str(row['evaluation_date'])),
            execution_time_seconds=row.get('execution_time_seconds', 0.0),
            is_ci_run=row.get('is_ci_run', False),
            ci_build_id=row.get('ci_build_id'),
            ci_pipeline_name=row.get('ci_pipeline_name'),
            threshold_f1=row.get('threshold_f1'),
            threshold_passed=row.get('threshold_passed'),
            notes=row.get('notes'),
            environment=row.get('environment', 'production'),
            gcp_project=row.get('gcp_project'),
            created_at=row['created_at'] if isinstance(row.get('created_at'), datetime) else datetime.utcnow()
        )
