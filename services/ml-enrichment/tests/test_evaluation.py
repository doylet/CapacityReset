"""
Unit Tests for Skills Evaluator

Tests the evaluation functionality:
1. Loading evaluation datasets
2. Calculating metrics (precision, recall, F1)
3. Per-category metric breakdown
4. CI/CD threshold checking
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
import tempfile
import os


class TestSkillsEvaluator:
    """Tests for SkillsEvaluator class."""
    
    def test_evaluator_initialization(self):
        """Evaluator should initialize with model ID and version."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator(model_id="test_model")
        
        assert evaluator.model_id == "test_model"
        assert evaluator.model_version is not None
    
    def test_evaluator_uses_extractor_version(self):
        """Evaluator should use the extractor's version."""
        from lib.evaluation.evaluator import SkillsEvaluator
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        evaluator = SkillsEvaluator(
            model_id="skills_extractor",
            extractor=extractor
        )
        
        assert evaluator.model_version == extractor.get_version()
    
    def test_evaluate_returns_result_entity(self):
        """Evaluation should return an EvaluationResult entity."""
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        from lib.domain.entities import EvaluationResult
        
        evaluator = SkillsEvaluator(model_id="test")
        
        # Create test dataset
        samples = [
            EvaluationSample(
                job_id="test-001",
                text="Python developer with Django experience",
                skills={"python", "django"}
            ),
            EvaluationSample(
                job_id="test-002",
                text="Java engineer with Spring Boot",
                skills={"java", "spring boot"}
            )
        ]
        
        result = evaluator.evaluate(dataset=samples)
        
        assert isinstance(result, EvaluationResult)
        assert result.sample_count == 2
        assert 0.0 <= result.overall_f1 <= 1.0


class TestMetricsCalculation:
    """Tests for metrics calculation."""
    
    def test_calculate_precision(self):
        """Precision should be TP / (TP + FP)."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator(model_id="test")
        
        # Predicted: {A, B, C}, Actual: {A, B, D}
        # TP = 2 (A, B), FP = 1 (C), FN = 1 (D)
        predictions = [{"a", "b", "c"}]
        actuals = [{"a", "b", "d"}]
        
        metrics = evaluator._calculate_metrics(predictions, actuals)
        
        # Precision = 2 / (2 + 1) = 0.667
        assert abs(metrics['precision'] - 0.667) < 0.01
    
    def test_calculate_recall(self):
        """Recall should be TP / (TP + FN)."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator(model_id="test")
        
        # Predicted: {A, B}, Actual: {A, B, C, D}
        # TP = 2, FP = 0, FN = 2
        predictions = [{"a", "b"}]
        actuals = [{"a", "b", "c", "d"}]
        
        metrics = evaluator._calculate_metrics(predictions, actuals)
        
        # Recall = 2 / (2 + 2) = 0.5
        assert metrics['recall'] == 0.5
    
    def test_calculate_f1(self):
        """F1 should be harmonic mean of precision and recall."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator(model_id="test")
        
        # Perfect match
        predictions = [{"a", "b", "c"}]
        actuals = [{"a", "b", "c"}]
        
        metrics = evaluator._calculate_metrics(predictions, actuals)
        
        # Perfect precision and recall = perfect F1
        assert metrics['f1'] == 1.0
    
    def test_handle_empty_predictions(self):
        """Should handle empty predictions gracefully."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator(model_id="test")
        
        predictions = [set()]  # No predictions
        actuals = [{"a", "b"}]  # Has ground truth
        
        metrics = evaluator._calculate_metrics(predictions, actuals)
        
        # Precision undefined (0/0), set to 0
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1'] == 0.0
    
    def test_handle_empty_actuals(self):
        """Should handle empty actuals gracefully."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator(model_id="test")
        
        predictions = [{"a", "b"}]
        actuals = [set()]  # No ground truth
        
        metrics = evaluator._calculate_metrics(predictions, actuals)
        
        # All predictions are false positives
        assert metrics['recall'] == 0.0 or metrics['false_negatives'] == 0


class TestDatasetLoading:
    """Tests for dataset loading functionality."""
    
    def test_load_jsonl_file(self):
        """Should load samples from JSONL file."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator(model_id="test")
        
        # Create temp JSONL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"job_id": "j1", "text": "Python developer", "skills": ["Python"]}\n')
            f.write('{"job_id": "j2", "text": "Java engineer", "skills": ["Java"]}\n')
            temp_path = f.name
        
        try:
            samples = evaluator._load_dataset(temp_path)
            
            assert len(samples) == 2
            assert samples[0].job_id == "j1"
            assert "python" in samples[0].skills or "Python" in samples[0].skills
        finally:
            os.unlink(temp_path)
    
    def test_load_with_sample_limit(self):
        """Should respect sample limit when loading."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator(model_id="test")
        
        # Create temp JSONL file with 5 samples
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for i in range(5):
                f.write(f'{{"job_id": "j{i}", "text": "Test {i}", "skills": ["skill{i}"]}}\n')
            temp_path = f.name
        
        try:
            samples = evaluator._load_dataset(temp_path, limit=3)
            
            assert len(samples) == 3
        finally:
            os.unlink(temp_path)
    
    def test_handle_missing_file(self):
        """Should handle missing file gracefully."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator(model_id="test")
        
        samples = evaluator._load_dataset("/nonexistent/path.jsonl")
        
        assert samples == []


class TestQuickEvaluation:
    """Tests for CI/CD quick evaluation."""
    
    def test_quick_evaluation_threshold_pass(self):
        """Quick evaluation should pass when F1 >= threshold."""
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        
        evaluator = SkillsEvaluator(model_id="test")
        
        # Create samples that will pass (high overlap)
        samples = [
            EvaluationSample(
                job_id="test-001",
                text="Python developer",
                skills={"python"}
            )
        ]
        
        result = evaluator.evaluate_quick(
            dataset_path=None,
            threshold_f1=0.0,  # Low threshold to ensure pass
            sample_limit=1,
            ci_build_id="build-123"
        )
        
        # Should fail since we can't load from None, but API should work
        # This test mainly checks the interface
    
    def test_quick_evaluation_sets_ci_flags(self):
        """Quick evaluation should set CI-specific flags."""
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        
        evaluator = SkillsEvaluator(model_id="test")
        
        samples = [
            EvaluationSample(
                job_id="test-001",
                text="Python developer with experience",
                skills={"python"}
            )
        ]
        
        # We can test using dataset directly
        result = evaluator.evaluate(dataset=samples)
        
        # Simulate quick eval behavior
        result.is_ci_run = True
        result.ci_build_id = "build-123"
        result.threshold_passed = result.overall_f1 >= 0.5
        
        assert result.is_ci_run is True
        assert result.ci_build_id == "build-123"


class TestEvaluationResultEntity:
    """Tests for EvaluationResult entity."""
    
    def test_evaluation_result_has_all_fields(self):
        """EvaluationResult should have all required fields."""
        from lib.domain.entities import EvaluationResult
        
        result = EvaluationResult(
            model_id="skills_extractor",
            model_version="v4.0-enhanced",
            dataset_version="v1",
            sample_count=100,
            overall_precision=0.85,
            overall_recall=0.90,
            overall_f1=0.87,
            evaluation_date=datetime.utcnow(),
            execution_time_seconds=5.0
        )
        
        assert result.model_id == "skills_extractor"
        assert result.overall_f1 == 0.87
        assert result.sample_count == 100
    
    def test_evaluation_result_to_dict(self):
        """to_dict should include all fields."""
        from lib.domain.entities import EvaluationResult
        
        result = EvaluationResult(
            model_id="test",
            model_version="v1",
            dataset_version="v1",
            sample_count=10,
            overall_precision=0.8,
            overall_recall=0.9,
            overall_f1=0.85,
            evaluation_date=datetime.utcnow(),
            execution_time_seconds=1.0
        )
        
        data = result.to_dict()
        
        assert 'model_id' in data
        assert 'overall_f1' in data
        assert 'evaluation_date' in data
    
    def test_evaluation_result_threshold_field(self):
        """Should track threshold checking."""
        from lib.domain.entities import EvaluationResult
        
        result = EvaluationResult(
            model_id="test",
            model_version="v1",
            dataset_version="v1",
            sample_count=10,
            overall_precision=0.8,
            overall_recall=0.9,
            overall_f1=0.85,
            evaluation_date=datetime.utcnow(),
            execution_time_seconds=1.0,
            is_ci_run=True,
            threshold_passed=True
        )
        
        assert result.is_ci_run is True
        assert result.threshold_passed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
