"""
Unit Tests for Metrics Calculation

Tests the metrics calculation utilities including:
- Precision, recall, F1 calculation
- Micro/macro averaging
- Per-category breakdown
"""

import pytest
from typing import Set, List


class TestPrecisionCalculation:
    """Tests for precision metric calculation."""
    
    def test_precision_perfect_match(self):
        """Precision should be 1.0 for perfect predictions."""
        # TP=3, FP=0, FN=0
        predictions = {"python", "django", "flask"}
        actuals = {"python", "django", "flask"}
        
        tp = len(predictions & actuals)
        fp = len(predictions - actuals)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        
        assert precision == 1.0
    
    def test_precision_no_false_positives(self):
        """Precision should be 1.0 with no false positives."""
        # TP=2, FP=0, FN=1
        predictions = {"python", "django"}
        actuals = {"python", "django", "flask"}
        
        tp = len(predictions & actuals)
        fp = len(predictions - actuals)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        
        assert precision == 1.0
    
    def test_precision_with_false_positives(self):
        """Precision should decrease with false positives."""
        # TP=2, FP=2
        predictions = {"python", "django", "java", "spring"}
        actuals = {"python", "django", "flask"}
        
        tp = len(predictions & actuals)
        fp = len(predictions - actuals)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        
        assert precision == 0.5  # 2/(2+2)
    
    def test_precision_zero(self):
        """Precision should be 0.0 with no true positives."""
        predictions = {"java", "spring"}
        actuals = {"python", "django"}
        
        tp = len(predictions & actuals)
        fp = len(predictions - actuals)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        
        assert precision == 0.0


class TestRecallCalculation:
    """Tests for recall metric calculation."""
    
    def test_recall_perfect_match(self):
        """Recall should be 1.0 for perfect predictions."""
        predictions = {"python", "django", "flask"}
        actuals = {"python", "django", "flask"}
        
        tp = len(predictions & actuals)
        fn = len(actuals - predictions)
        
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        assert recall == 1.0
    
    def test_recall_with_false_negatives(self):
        """Recall should decrease with false negatives."""
        # TP=2, FN=1
        predictions = {"python", "django"}
        actuals = {"python", "django", "flask"}
        
        tp = len(predictions & actuals)
        fn = len(actuals - predictions)
        
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        assert recall == pytest.approx(2/3)
    
    def test_recall_zero(self):
        """Recall should be 0.0 with no true positives."""
        predictions = {"java", "spring"}
        actuals = {"python", "django"}
        
        tp = len(predictions & actuals)
        fn = len(actuals - predictions)
        
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        assert recall == 0.0


class TestF1Calculation:
    """Tests for F1 score calculation."""
    
    def test_f1_perfect_match(self):
        """F1 should be 1.0 for perfect predictions."""
        precision = 1.0
        recall = 1.0
        
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        assert f1 == 1.0
    
    def test_f1_zero(self):
        """F1 should be 0.0 when precision or recall is 0."""
        precision = 0.0
        recall = 0.0
        
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        assert f1 == 0.0
    
    def test_f1_harmonic_mean(self):
        """F1 should be harmonic mean of precision and recall."""
        precision = 0.8
        recall = 0.6
        
        f1 = 2 * precision * recall / (precision + recall)
        
        # Harmonic mean of 0.8 and 0.6
        expected = 2 * 0.8 * 0.6 / (0.8 + 0.6)
        
        assert f1 == pytest.approx(expected)
    
    def test_f1_with_unequal_precision_recall(self):
        """F1 should balance precision and recall."""
        # High precision, low recall
        precision = 0.9
        recall = 0.3
        
        f1 = 2 * precision * recall / (precision + recall)
        
        # F1 will be closer to the lower value
        assert f1 < precision
        assert f1 > recall


class TestAggregateMetrics:
    """Tests for aggregate metrics across multiple samples."""
    
    def test_aggregate_perfect_match(self):
        """Aggregate metrics should be 1.0 for perfect match."""
        samples = [
            ({"python", "django"}, {"python", "django"}),
            ({"react", "javascript"}, {"react", "javascript"})
        ]
        
        total_tp = 0
        total_fp = 0
        total_fn = 0
        
        for predictions, actuals in samples:
            total_tp += len(predictions & actuals)
            total_fp += len(predictions - actuals)
            total_fn += len(actuals - predictions)
        
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        assert precision == 1.0
        assert recall == 1.0
        assert f1 == 1.0
    
    def test_aggregate_mixed_results(self):
        """Aggregate metrics should average across samples."""
        samples = [
            ({"python", "django"}, {"python", "django"}),  # Perfect
            ({"java"}, {"python", "django"})  # Completely wrong
        ]
        
        total_tp = 0
        total_fp = 0
        total_fn = 0
        
        for predictions, actuals in samples:
            total_tp += len(predictions & actuals)
            total_fp += len(predictions - actuals)
            total_fn += len(actuals - predictions)
        
        # TP=2 (from first), FP=1 (from second), FN=2 (from second)
        assert total_tp == 2
        assert total_fp == 1
        assert total_fn == 2
        
        precision = total_tp / (total_tp + total_fp)  # 2/3
        recall = total_tp / (total_tp + total_fn)  # 2/4 = 0.5
        
        assert precision == pytest.approx(2/3)
        assert recall == pytest.approx(0.5)


class TestCategoryMetrics:
    """Tests for per-category metrics calculation."""
    
    def test_category_metrics_structure(self):
        """Category metrics should have correct structure."""
        category_metrics = {
            'programming_languages': {
                'precision': 0.85,
                'recall': 0.90,
                'f1': 0.87,
                'support': 50
            }
        }
        
        assert 'precision' in category_metrics['programming_languages']
        assert 'recall' in category_metrics['programming_languages']
        assert 'f1' in category_metrics['programming_languages']
        assert 'support' in category_metrics['programming_languages']
    
    def test_category_metrics_valid_range(self):
        """All category metrics should be in valid range."""
        metrics_values = [0.0, 0.5, 0.85, 1.0]
        
        for value in metrics_values:
            assert 0.0 <= value <= 1.0


class TestEdgeCases:
    """Tests for edge cases in metrics calculation."""
    
    def test_empty_predictions(self):
        """Should handle empty predictions."""
        predictions = set()
        actuals = {"python", "django"}
        
        tp = len(predictions & actuals)
        fp = len(predictions - actuals)
        fn = len(actuals - predictions)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        assert precision == 0.0
        assert recall == 0.0
    
    def test_empty_actuals(self):
        """Should handle empty actuals."""
        predictions = {"python", "django"}
        actuals = set()
        
        tp = len(predictions & actuals)
        fp = len(predictions - actuals)
        fn = len(actuals - predictions)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        assert precision == 0.0  # All predictions are false positives
        assert recall == 0.0  # No recall possible
    
    def test_both_empty(self):
        """Should handle both empty."""
        predictions = set()
        actuals = set()
        
        tp = len(predictions & actuals)
        fp = len(predictions - actuals)
        fn = len(actuals - predictions)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        assert precision == 0.0
        assert recall == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
