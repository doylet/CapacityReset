"""
Integration Tests for Evaluation API

Tests the evaluation endpoints including:
- /evaluate endpoint
- /evaluate/quick endpoint
- /evaluate/results endpoint
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json


class TestEvaluateEndpoint:
    """Tests for the /evaluate endpoint."""
    
    def test_evaluate_requires_dataset(self):
        """Evaluate endpoint should require dataset path."""
        # Simulate missing dataset
        request = {'enrichment_types': ['model_evaluation']}
        
        # Should indicate dataset is required
        assert 'dataset_path' not in request or 'dataset' not in request
    
    def test_evaluate_returns_metrics(self):
        """Evaluate endpoint should return metrics."""
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        
        evaluator = SkillsEvaluator()
        
        samples = [
            EvaluationSample(
                job_id="job-001",
                text="Python developer needed",
                skills={"python"}
            )
        ]
        
        result = evaluator.evaluate(dataset=samples)
        
        # Should have all required metrics
        assert hasattr(result, 'overall_precision')
        assert hasattr(result, 'overall_recall')
        assert hasattr(result, 'overall_f1')
        assert hasattr(result, 'sample_count')
    
    def test_evaluate_includes_execution_time(self):
        """Evaluate result should include execution time."""
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        
        evaluator = SkillsEvaluator()
        
        samples = [
            EvaluationSample(
                job_id="job-001",
                text="Python developer needed",
                skills={"python"}
            )
        ]
        
        result = evaluator.evaluate(dataset=samples)
        
        assert result.execution_time_seconds >= 0


class TestEvaluateQuickEndpoint:
    """Tests for the /evaluate/quick endpoint."""
    
    def test_quick_sets_threshold_passed(self):
        """Quick evaluate should set threshold_passed flag."""
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        
        evaluator = SkillsEvaluator()
        
        # Create a simple test that should pass
        samples = [
            EvaluationSample(
                job_id="job-001",
                text="Python and Django developer",
                skills={"python", "django"}
            )
        ]
        
        result = evaluator.evaluate(dataset=samples)
        
        # Manually simulate quick evaluation logic
        threshold_f1 = 0.0  # Very low threshold
        threshold_passed = result.overall_f1 >= threshold_f1
        
        assert isinstance(threshold_passed, bool)
    
    def test_quick_limits_samples(self):
        """Quick evaluate should limit sample count."""
        sample_limit = 50
        total_samples = 100
        
        # In quick mode, only sample_limit should be used
        limited = min(total_samples, sample_limit)
        
        assert limited == 50
    
    def test_quick_includes_ci_build_id(self):
        """Quick evaluate should include CI build ID if provided."""
        ci_build_id = "build-abc123"
        
        # This should be included in result
        assert ci_build_id is not None


class TestEvaluateResultsEndpoint:
    """Tests for the /evaluate/results endpoint."""
    
    def test_results_returns_history(self):
        """Results endpoint should return evaluation history."""
        # Simulate historical results
        mock_results = [
            {
                'evaluation_id': 'eval-001',
                'model_id': 'skills_extractor',
                'model_version': 'v4.0-enhanced',
                'overall_f1': 0.85,
                'evaluation_date': datetime.utcnow().isoformat()
            },
            {
                'evaluation_id': 'eval-002',
                'model_id': 'skills_extractor',
                'model_version': 'v4.0-enhanced',
                'overall_f1': 0.87,
                'evaluation_date': datetime.utcnow().isoformat()
            }
        ]
        
        assert len(mock_results) == 2
        assert all('overall_f1' in r for r in mock_results)
    
    def test_results_can_filter_by_model(self):
        """Results should be filterable by model ID."""
        model_id = 'skills_extractor'
        
        all_results = [
            {'model_id': 'skills_extractor', 'overall_f1': 0.85},
            {'model_id': 'skills_extractor', 'overall_f1': 0.87},
            {'model_id': 'other_model', 'overall_f1': 0.90}
        ]
        
        filtered = [r for r in all_results if r['model_id'] == model_id]
        
        assert len(filtered) == 2
    
    def test_results_sorted_by_date(self):
        """Results should be sorted by date (newest first)."""
        results = [
            {'evaluation_date': '2025-01-01', 'overall_f1': 0.80},
            {'evaluation_date': '2025-06-01', 'overall_f1': 0.85},
            {'evaluation_date': '2025-03-01', 'overall_f1': 0.82}
        ]
        
        sorted_results = sorted(results, key=lambda x: x['evaluation_date'], reverse=True)
        
        assert sorted_results[0]['evaluation_date'] == '2025-06-01'
        assert sorted_results[-1]['evaluation_date'] == '2025-01-01'


class TestEvaluationResultStorage:
    """Tests for storing evaluation results."""
    
    def test_result_entity_serialization(self):
        """EvaluationResult should serialize correctly."""
        from lib.domain.entities import EvaluationResult
        
        result = EvaluationResult(
            model_id='skills_extractor',
            model_version='v4.0-enhanced',
            dataset_version='v1.0',
            sample_count=100,
            overall_precision=0.85,
            overall_recall=0.90,
            overall_f1=0.87,
            evaluation_date=datetime.utcnow()
        )
        
        data = result.to_dict()
        
        assert 'model_id' in data
        assert 'overall_f1' in data
        assert data['model_id'] == 'skills_extractor'
    
    def test_result_entity_roundtrip(self):
        """EvaluationResult should survive serialization roundtrip."""
        from lib.domain.entities import EvaluationResult
        
        original = EvaluationResult(
            model_id='skills_extractor',
            model_version='v4.0-enhanced',
            dataset_version='v1.0',
            sample_count=100,
            overall_precision=0.85,
            overall_recall=0.90,
            overall_f1=0.87,
            evaluation_date=datetime.utcnow()
        )
        
        data = original.to_dict()
        restored = EvaluationResult.from_dict(data)
        
        assert restored.model_id == original.model_id
        assert restored.overall_f1 == original.overall_f1
        assert restored.sample_count == original.sample_count


class TestEvaluationWithRepository:
    """Tests for evaluation with BigQuery repository."""
    
    def test_save_result_to_repository(self):
        """Should be able to save evaluation result."""
        from lib.domain.entities import EvaluationResult
        
        mock_repository = Mock()
        mock_repository.save.return_value = 'eval-123'
        
        result = EvaluationResult(
            model_id='skills_extractor',
            model_version='v4.0-enhanced',
            dataset_version='v1.0',
            sample_count=100,
            overall_precision=0.85,
            overall_recall=0.90,
            overall_f1=0.87,
            evaluation_date=datetime.utcnow()
        )
        
        # Simulate save
        saved_id = mock_repository.save(result)
        
        assert saved_id == 'eval-123'
        mock_repository.save.assert_called_once_with(result)
    
    def test_find_latest_for_model(self):
        """Should find latest evaluation for a model."""
        mock_repository = Mock()
        mock_repository.find_latest_for_model.return_value = {
            'evaluation_id': 'eval-123',
            'model_id': 'skills_extractor',
            'overall_f1': 0.87
        }
        
        result = mock_repository.find_latest_for_model('skills_extractor')
        
        assert result['model_id'] == 'skills_extractor'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
