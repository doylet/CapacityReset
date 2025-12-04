"""
Unit Tests for SkillsEvaluator

Tests the skills evaluator functionality including:
- Dataset loading
- Metrics calculation
- Per-category breakdown
- CI/CD integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
import tempfile
import os


class TestSkillsEvaluatorInit:
    """Tests for SkillsEvaluator initialization."""
    
    def test_evaluator_creates_with_defaults(self):
        """Evaluator should initialize with default settings."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator()
        
        assert evaluator.model_id == "skills_extractor"
        assert evaluator.extractor is not None
        assert evaluator.model_version is not None
    
    def test_evaluator_accepts_custom_model_id(self):
        """Evaluator should accept custom model ID."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator(model_id="custom_extractor")
        
        assert evaluator.model_id == "custom_extractor"
    
    def test_evaluator_accepts_custom_extractor(self):
        """Evaluator should accept custom extractor."""
        from lib.evaluation.evaluator import SkillsEvaluator
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        custom_extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        evaluator = SkillsEvaluator(
            extractor=custom_extractor
        )
        
        assert evaluator.extractor is custom_extractor


class TestDatasetLoading:
    """Tests for evaluation dataset loading."""
    
    def test_load_from_local_jsonl(self):
        """Should load samples from local JSONL file."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        # Create temp JSONL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(json.dumps({"job_id": "job-001", "text": "Python developer needed", "skills": ["Python"]}) + "\n")
            f.write(json.dumps({"job_id": "job-002", "text": "React engineer wanted", "skills": ["React", "JavaScript"]}) + "\n")
            temp_path = f.name
        
        try:
            evaluator = SkillsEvaluator()
            samples = evaluator._load_from_local(temp_path)
            
            assert len(samples) == 2
            assert samples[0].job_id == "job-001"
            assert "Python" in samples[0].skills
            assert samples[1].job_id == "job-002"
            assert "React" in samples[1].skills
        finally:
            os.unlink(temp_path)
    
    def test_load_with_limit(self):
        """Should respect sample limit."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for i in range(10):
                f.write(json.dumps({"job_id": f"job-{i}", "text": f"Job {i}", "skills": ["Python"]}) + "\n")
            temp_path = f.name
        
        try:
            evaluator = SkillsEvaluator()
            samples = evaluator._load_from_local(temp_path, limit=5)
            
            assert len(samples) == 5
        finally:
            os.unlink(temp_path)
    
    def test_load_handles_missing_file(self):
        """Should handle missing file gracefully."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator()
        samples = evaluator._load_from_local("/nonexistent/path.jsonl")
        
        assert samples == []


class TestMetricsCalculation:
    """Tests for evaluation metrics calculation."""
    
    def test_calculate_perfect_metrics(self):
        """Perfect predictions should yield 1.0 metrics."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator()
        
        predictions = [
            {"python", "django"},
            {"react", "javascript"}
        ]
        actuals = [
            {"python", "django"},
            {"react", "javascript"}
        ]
        
        metrics = evaluator._calculate_metrics(predictions, actuals)
        
        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['f1'] == 1.0
    
    def test_calculate_zero_metrics(self):
        """Completely wrong predictions should yield 0.0 metrics."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator()
        
        predictions = [
            {"java", "spring"},
            {"angular", "typescript"}
        ]
        actuals = [
            {"python", "django"},
            {"react", "javascript"}
        ]
        
        metrics = evaluator._calculate_metrics(predictions, actuals)
        
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1'] == 0.0
    
    def test_calculate_partial_metrics(self):
        """Partial matches should yield intermediate metrics."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator()
        
        predictions = [
            {"python", "django", "extra"},  # 2 correct, 1 extra
        ]
        actuals = [
            {"python", "django", "flask"},  # 3 skills, 2 found
        ]
        
        metrics = evaluator._calculate_metrics(predictions, actuals)
        
        # TP=2, FP=1, FN=1
        # Precision = 2/3 ≈ 0.67
        # Recall = 2/3 ≈ 0.67
        assert 0.6 <= metrics['precision'] <= 0.7
        assert 0.6 <= metrics['recall'] <= 0.7
    
    def test_calculate_handles_empty(self):
        """Should handle empty sets gracefully."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator()
        
        predictions = [set(), set()]
        actuals = [set(), set()]
        
        metrics = evaluator._calculate_metrics(predictions, actuals)
        
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1'] == 0.0


class TestEvaluationRun:
    """Tests for running full evaluation."""
    
    def test_evaluate_returns_result(self):
        """Evaluation should return EvaluationResult."""
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        from lib.domain.entities import EvaluationResult
        
        evaluator = SkillsEvaluator()
        
        # Provide inline dataset
        samples = [
            EvaluationSample(
                job_id="job-001",
                text="Looking for Python developer with Django experience",
                skills={"python", "django"}
            ),
            EvaluationSample(
                job_id="job-002",
                text="React and JavaScript engineer needed",
                skills={"react", "javascript"}
            )
        ]
        
        result = evaluator.evaluate(dataset=samples)
        
        assert isinstance(result, EvaluationResult)
        assert result.sample_count == 2
        assert 0.0 <= result.overall_precision <= 1.0
        assert 0.0 <= result.overall_recall <= 1.0
        assert 0.0 <= result.overall_f1 <= 1.0
    
    def test_evaluate_quick_sets_ci_fields(self):
        """Quick evaluation should set CI-specific fields."""
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        
        evaluator = SkillsEvaluator()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(json.dumps({"job_id": "job-001", "text": "Python developer", "skills": ["Python"]}) + "\n")
            temp_path = f.name
        
        try:
            result = evaluator.evaluate_quick(
                dataset_path=temp_path,
                threshold_f1=0.5,
                sample_limit=10,
                ci_build_id="build-123"
            )
            
            assert result.is_ci_run is True
            assert result.ci_build_id == "build-123"
            assert result.threshold_passed is not None
        finally:
            os.unlink(temp_path)


class TestDatasetVersion:
    """Tests for dataset version extraction."""
    
    def test_extract_version_from_filename(self):
        """Should extract version from filename."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator()
        
        version = evaluator._get_dataset_version("/path/to/dataset_v1.2.jsonl")
        
        # Should extract version part
        assert "1.2" in version or "dataset_v1.2" in version
    
    def test_generate_inline_version(self):
        """Should generate version for inline data."""
        from lib.evaluation.evaluator import SkillsEvaluator
        
        evaluator = SkillsEvaluator()
        
        version = evaluator._get_dataset_version(None)
        
        assert version.startswith("inline-")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
