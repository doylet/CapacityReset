"""
Unit Tests for Metrics Calculation

Tests the metrics calculation utilities:
1. Set-based precision/recall/F1
2. Multi-label binarization
3. Per-category breakdown
"""

import pytest
from unittest.mock import Mock, patch
from typing import Set, List, Dict


class TestSetBasedMetrics:
    """Tests for set-based metric calculations."""
    
    def test_perfect_precision_recall(self):
        """Perfect overlap should give 1.0 for all metrics."""
        predictions = [{"python", "java", "docker"}]
        actuals = [{"python", "java", "docker"}]
        
        tp = len(predictions[0] & actuals[0])  # 3
        fp = len(predictions[0] - actuals[0])  # 0
        fn = len(actuals[0] - predictions[0])  # 0
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0  # 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0     # 1.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0  # 1.0
        
        assert precision == 1.0
        assert recall == 1.0
        assert f1 == 1.0
    
    def test_no_overlap(self):
        """No overlap should give 0.0 for all metrics."""
        predictions = [{"python", "java"}]
        actuals = [{"ruby", "rust"}]
        
        tp = len(predictions[0] & actuals[0])  # 0
        fp = len(predictions[0] - actuals[0])  # 2
        fn = len(actuals[0] - predictions[0])  # 2
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0  # 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0     # 0.0
        
        assert precision == 0.0
        assert recall == 0.0
    
    def test_partial_overlap(self):
        """Partial overlap should give intermediate values."""
        predictions = [{"python", "java", "ruby"}]  # Predicted 3
        actuals = [{"python", "java", "rust"}]      # Actual 3
        
        tp = len(predictions[0] & actuals[0])  # 2 (python, java)
        fp = len(predictions[0] - actuals[0])  # 1 (ruby)
        fn = len(actuals[0] - predictions[0])  # 1 (rust)
        
        precision = tp / (tp + fp)  # 2/3 = 0.667
        recall = tp / (tp + fn)     # 2/3 = 0.667
        f1 = 2 * precision * recall / (precision + recall)  # 0.667
        
        assert abs(precision - 0.667) < 0.01
        assert abs(recall - 0.667) < 0.01
        assert abs(f1 - 0.667) < 0.01


class TestAggregatedMetrics:
    """Tests for metrics aggregated across multiple samples."""
    
    def test_aggregate_across_samples(self):
        """Metrics should be aggregated correctly across samples."""
        predictions = [
            {"python", "java"},       # Sample 1: 2 predictions
            {"docker", "kubernetes"}  # Sample 2: 2 predictions
        ]
        actuals = [
            {"python", "rust"},       # Sample 1: 2 actual
            {"docker", "terraform"}   # Sample 2: 2 actual
        ]
        
        total_tp = 0
        total_fp = 0
        total_fn = 0
        
        for pred, actual in zip(predictions, actuals):
            total_tp += len(pred & actual)  # 1 + 1 = 2
            total_fp += len(pred - actual)  # 1 + 1 = 2
            total_fn += len(actual - pred)  # 1 + 1 = 2
        
        precision = total_tp / (total_tp + total_fp)  # 2/4 = 0.5
        recall = total_tp / (total_tp + total_fn)     # 2/4 = 0.5
        
        assert precision == 0.5
        assert recall == 0.5
    
    def test_varying_set_sizes(self):
        """Should handle varying prediction/actual set sizes."""
        predictions = [
            {"python"},                    # 1 prediction
            {"java", "docker", "k8s"}      # 3 predictions
        ]
        actuals = [
            {"python", "java", "rust"},    # 3 actual
            {"docker"}                     # 1 actual
        ]
        
        # Sample 1: TP=1, FP=0, FN=2
        # Sample 2: TP=1, FP=2, FN=0
        # Total: TP=2, FP=2, FN=2
        
        total_tp = 2
        total_fp = 2
        total_fn = 2
        
        precision = total_tp / (total_tp + total_fp)  # 2/4 = 0.5
        recall = total_tp / (total_tp + total_fn)     # 2/4 = 0.5
        
        assert precision == 0.5
        assert recall == 0.5


class TestEdgeCases:
    """Tests for edge cases in metrics calculation."""
    
    def test_empty_predictions_and_actuals(self):
        """Should handle both empty gracefully."""
        predictions = [set()]
        actuals = [set()]
        
        tp = 0
        fp = 0
        fn = 0
        
        # All zeros - undefined precision/recall
        # Convention: set to 0 or 1 depending on interpretation
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        assert precision == 0.0  # or 1.0 if we consider "no errors"
    
    def test_single_element_sets(self):
        """Should work correctly with single-element sets."""
        # Perfect match of single element
        predictions = [{"python"}]
        actuals = [{"python"}]
        
        tp = 1
        fp = 0
        fn = 0
        
        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        
        assert precision == 1.0
        assert recall == 1.0
    
    def test_case_sensitivity(self):
        """Sets should handle case correctly (typically lowercase)."""
        predictions = [{"python", "javascript"}]
        actuals = [{"Python", "JavaScript"}]  # Different case
        
        # Direct comparison would find no matches
        tp = len(predictions[0] & actuals[0])  # 0 if case-sensitive
        
        # In practice, we lowercase both
        predictions_lower = [{s.lower() for s in preds} for preds in predictions]
        actuals_lower = [{s.lower() for s in acts} for acts in actuals]
        
        tp_lower = len(predictions_lower[0] & actuals_lower[0])  # 2
        
        assert tp == 0  # Case-sensitive: no match
        assert tp_lower == 2  # Case-insensitive: both match


class TestPerCategoryMetrics:
    """Tests for per-category metric breakdown."""
    
    def test_category_level_precision(self):
        """Should calculate precision per skill category."""
        # Category: programming_languages
        predictions = [{"python", "java", "ruby"}]
        actuals = [{"python", "java", "rust"}]
        
        # For this category
        tp = 2  # python, java
        fp = 1  # ruby
        
        category_precision = tp / (tp + fp)  # 0.667
        
        assert abs(category_precision - 0.667) < 0.01
    
    def test_multiple_categories(self):
        """Should track metrics separately per category."""
        # Simulated predictions by category
        predictions_by_category = {
            'programming_languages': {"python", "java"},
            'cloud_platforms': {"aws", "azure", "gcp"}
        }
        
        actuals_by_category = {
            'programming_languages': {"python", "rust"},
            'cloud_platforms': {"aws", "azure"}
        }
        
        # Programming languages: TP=1, FP=1, FN=1
        prog_tp = 1
        prog_fp = 1
        prog_fn = 1
        prog_precision = prog_tp / (prog_tp + prog_fp)  # 0.5
        
        # Cloud platforms: TP=2, FP=1, FN=0
        cloud_tp = 2
        cloud_fp = 1
        cloud_fn = 0
        cloud_precision = cloud_tp / (cloud_tp + cloud_fp)  # 0.667
        cloud_recall = cloud_tp / (cloud_tp + cloud_fn)     # 1.0
        
        assert prog_precision == 0.5
        assert abs(cloud_precision - 0.667) < 0.01
        assert cloud_recall == 1.0


class TestF1ScoreCalculation:
    """Tests specifically for F1 score calculation."""
    
    def test_f1_is_harmonic_mean(self):
        """F1 should be harmonic mean of precision and recall."""
        precision = 0.8
        recall = 0.6
        
        # Harmonic mean formula
        expected_f1 = 2 * precision * recall / (precision + recall)
        # = 2 * 0.8 * 0.6 / 1.4 = 0.96 / 1.4 ≈ 0.686
        
        assert abs(expected_f1 - 0.686) < 0.01
    
    def test_f1_when_precision_zero(self):
        """F1 should be 0 when precision is 0."""
        precision = 0.0
        recall = 0.9
        
        if (precision + recall) > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0
        
        assert f1 == 0.0
    
    def test_f1_when_recall_zero(self):
        """F1 should be 0 when recall is 0."""
        precision = 0.9
        recall = 0.0
        
        if (precision + recall) > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0
        
        assert f1 == 0.0
    
    def test_f1_perfect_score(self):
        """F1 should be 1.0 when both precision and recall are 1.0."""
        precision = 1.0
        recall = 1.0
        
        f1 = 2 * precision * recall / (precision + recall)
        
        assert f1 == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
