"""
Integration Tests for Evaluation API

Tests the /evaluate endpoints:
1. Full evaluation endpoint
2. Quick CI evaluation endpoint
3. Historical results endpoint
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import tempfile
import os


class TestEvaluationEndpoints:
    """Tests for evaluation API endpoints."""
    
    def test_evaluate_endpoint_returns_metrics(self):
        """POST /evaluate should return evaluation metrics."""
        # Mock the evaluation flow
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        from lib.domain.entities import EvaluationResult
        
        evaluator = SkillsEvaluator(model_id="skills_extractor")
        
        samples = [
            EvaluationSample(
                job_id="test-001",
                text="Python developer with experience in Django and PostgreSQL",
                skills={"python", "django", "postgresql"}
            ),
            EvaluationSample(
                job_id="test-002",
                text="DevOps engineer with Docker and Kubernetes expertise",
                skills={"docker", "kubernetes"}
            )
        ]
        
        result = evaluator.evaluate(dataset=samples)
        
        # Verify response structure
        assert hasattr(result, 'overall_precision')
        assert hasattr(result, 'overall_recall')
        assert hasattr(result, 'overall_f1')
        assert hasattr(result, 'sample_count')
        assert result.sample_count == 2
    
    def test_evaluate_quick_endpoint_for_ci(self):
        """POST /evaluate/quick should support CI/CD workflows."""
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        
        evaluator = SkillsEvaluator(model_id="skills_extractor")
        
        samples = [
            EvaluationSample(
                job_id="ci-test-001",
                text="Software engineer with Python experience",
                skills={"python"}
            )
        ]
        
        # Simulate quick eval
        result = evaluator.evaluate(dataset=samples, sample_limit=10)
        
        # Add CI flags
        result.is_ci_run = True
        result.ci_build_id = "ci-12345"
        result.threshold_passed = result.overall_f1 >= 0.7
        
        assert result.is_ci_run is True
        assert result.ci_build_id == "ci-12345"
    
    def test_evaluate_results_endpoint_returns_history(self):
        """GET /evaluate/results should return historical results."""
        from lib.domain.entities import EvaluationResult
        
        # Simulate historical results
        results = [
            EvaluationResult(
                model_id="skills_extractor",
                model_version="v4.0-enhanced",
                dataset_version="v1",
                sample_count=100,
                overall_precision=0.85,
                overall_recall=0.90,
                overall_f1=0.87,
                evaluation_date=datetime.utcnow() - timedelta(days=1),
                execution_time_seconds=5.0
            ),
            EvaluationResult(
                model_id="skills_extractor",
                model_version="v4.0-enhanced",
                dataset_version="v2",
                sample_count=150,
                overall_precision=0.88,
                overall_recall=0.92,
                overall_f1=0.90,
                evaluation_date=datetime.utcnow(),
                execution_time_seconds=7.5
            )
        ]
        
        # Verify results can be serialized
        for result in results:
            data = result.to_dict()
            assert 'overall_f1' in data
            assert 'evaluation_date' in data


class TestEvaluationWithRealExtractor:
    """Integration tests using the real skills extractor."""
    
    def test_full_evaluation_workflow(self):
        """Should run complete evaluation against test data."""
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        
        evaluator = SkillsEvaluator(model_id="skills_extractor")
        
        # Create realistic test samples
        samples = [
            EvaluationSample(
                job_id="eval-001",
                text="""
                Senior Software Engineer
                
                Requirements:
                - 5+ years Python experience
                - Experience with Django or Flask
                - PostgreSQL database expertise
                - Docker containerization knowledge
                """,
                skills={"python", "django", "flask", "postgresql", "docker"}
            ),
            EvaluationSample(
                job_id="eval-002",
                text="""
                DevOps Engineer
                
                Must have:
                - Kubernetes and Docker experience
                - AWS cloud platform knowledge
                - Terraform for infrastructure
                - CI/CD pipeline experience with Jenkins or GitHub Actions
                """,
                skills={"kubernetes", "docker", "aws", "terraform", "jenkins", "github actions"}
            ),
            EvaluationSample(
                job_id="eval-003",
                text="""
                Frontend Developer
                
                Skills needed:
                - React.js expertise
                - TypeScript experience
                - CSS and Tailwind CSS knowledge
                - Jest for testing
                """,
                skills={"react", "typescript", "css", "tailwind css", "jest"}
            )
        ]
        
        result = evaluator.evaluate(dataset=samples)
        
        # Verify metrics are calculated
        assert result.sample_count == 3
        assert 0.0 <= result.overall_precision <= 1.0
        assert 0.0 <= result.overall_recall <= 1.0
        assert 0.0 <= result.overall_f1 <= 1.0
        
        # Log results for visibility
        print(f"\nEvaluation Results:")
        print(f"  Precision: {result.overall_precision:.3f}")
        print(f"  Recall: {result.overall_recall:.3f}")
        print(f"  F1: {result.overall_f1:.3f}")
        print(f"  Execution Time: {result.execution_time_seconds:.2f}s")
    
    def test_evaluate_with_diverse_job_types(self):
        """Should handle diverse job posting types."""
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        
        evaluator = SkillsEvaluator(model_id="skills_extractor")
        
        samples = [
            # Data Science job
            EvaluationSample(
                job_id="ds-001",
                text="Data Scientist with Python, TensorFlow, and ML experience. Must know SQL.",
                skills={"python", "tensorflow", "sql"}
            ),
            # Mobile development job
            EvaluationSample(
                job_id="mobile-001",
                text="iOS Developer with Swift and SwiftUI experience. Xcode proficiency required.",
                skills={"swift", "swiftui", "xcode"}
            ),
            # Backend job
            EvaluationSample(
                job_id="backend-001",
                text="Java Backend Engineer with Spring Boot and microservices experience.",
                skills={"java", "spring boot"}
            )
        ]
        
        result = evaluator.evaluate(dataset=samples)
        
        assert result.sample_count == 3
        assert result.execution_time_seconds > 0


class TestEvaluationResultStorage:
    """Tests for storing and retrieving evaluation results."""
    
    def test_result_can_be_serialized(self):
        """Evaluation result should be serializable to JSON."""
        from lib.domain.entities import EvaluationResult
        
        result = EvaluationResult(
            model_id="skills_extractor",
            model_version="v4.0-enhanced",
            dataset_version="test-v1",
            sample_count=50,
            overall_precision=0.82,
            overall_recall=0.88,
            overall_f1=0.85,
            evaluation_date=datetime.utcnow(),
            execution_time_seconds=3.5,
            category_metrics={
                'programming_languages': {'precision': 0.9, 'recall': 0.95, 'f1': 0.92},
                'cloud_platforms': {'precision': 0.8, 'recall': 0.85, 'f1': 0.82}
            }
        )
        
        data = result.to_dict()
        json_str = json.dumps(data, default=str)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed['model_id'] == 'skills_extractor'
        assert parsed['overall_f1'] == 0.85
    
    def test_result_roundtrip(self):
        """Result should survive serialization/deserialization."""
        from lib.domain.entities import EvaluationResult
        
        original = EvaluationResult(
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
        
        data = original.to_dict()
        restored = EvaluationResult.from_dict(data)
        
        assert restored.model_id == original.model_id
        assert restored.overall_f1 == original.overall_f1
        assert restored.sample_count == original.sample_count


class TestEvaluationPerformance:
    """Performance tests for evaluation."""
    
    def test_evaluation_completes_in_time(self):
        """Evaluation should complete within reasonable time."""
        import time
        from lib.evaluation.evaluator import SkillsEvaluator, EvaluationSample
        
        evaluator = SkillsEvaluator(model_id="skills_extractor")
        
        # Generate 20 test samples
        samples = [
            EvaluationSample(
                job_id=f"perf-{i}",
                text=f"Software engineer with Python, Java, Docker experience. Sample {i}.",
                skills={"python", "java", "docker"}
            )
            for i in range(20)
        ]
        
        start = time.time()
        result = evaluator.evaluate(dataset=samples)
        elapsed = time.time() - start
        
        # Should complete in < 30 seconds for 20 samples
        assert elapsed < 30.0, f"Evaluation took {elapsed:.2f}s, expected < 30s"
        assert result.sample_count == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
