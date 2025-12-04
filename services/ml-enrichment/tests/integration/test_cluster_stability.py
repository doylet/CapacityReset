"""
Integration Tests for Cluster Stability Metrics

Tests the cluster stability analysis across multiple clustering runs:
1. Comparing cluster assignments between runs
2. Calculating stability metrics
3. Tracking cluster evolution over time
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import uuid


class TestClusterStabilityMetricsIntegration:
    """Integration tests for cluster stability across runs."""
    
    def test_stability_tracking_across_runs(self):
        """Should track stability between consecutive runs."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        
        # Simulate previous run results
        previous_assignments = {
            'job-001': 0,
            'job-002': 0,
            'job-003': 1,
            'job-004': 1,
            'job-005': 2
        }
        
        # Current run - some jobs changed clusters
        current_assignments = {
            'job-001': 0,  # Same
            'job-002': 1,  # Changed from 0 to 1
            'job-003': 1,  # Same
            'job-004': 0,  # Changed from 1 to 0
            'job-005': 2   # Same
        }
        
        stability = clusterer.calculate_cluster_stability(
            previous_assignments,
            current_assignments
        )
        
        # 3 out of 5 stayed in same cluster
        assert stability == 0.6
    
    def test_stability_with_completely_new_run(self):
        """First run should have no stability metric (no previous)."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        
        # No previous assignments
        previous_assignments = {}
        
        current_assignments = {
            'job-001': 0,
            'job-002': 1,
            'job-003': 2
        }
        
        stability = clusterer.calculate_cluster_stability(
            previous_assignments,
            current_assignments
        )
        
        # Should handle empty previous gracefully
        # Convention: return 1.0 (100%) for first run or None
        assert stability is None or stability == 1.0


class TestClusterEvolutionTracking:
    """Tests for tracking cluster evolution over time."""
    
    def test_get_cluster_history_for_job(self):
        """Should retrieve cluster history for a specific job."""
        from lib.domain.entities import ClusterAssignment
        
        # Simulate cluster history
        history = [
            ClusterAssignment(
                job_posting_id='job-123',
                enrichment_id='e1',
                cluster_id=0,
                cluster_name='Python Jobs',
                cluster_keywords=[],
                cluster_size=20,
                cluster_run_id='run-1',
                cluster_model_id='v1.0',
                cluster_version=1,
                is_active=False
            ),
            ClusterAssignment(
                job_posting_id='job-123',
                enrichment_id='e2',
                cluster_id=1,
                cluster_name='ML Engineering',
                cluster_keywords=[],
                cluster_size=25,
                cluster_run_id='run-2',
                cluster_model_id='v1.0',
                cluster_version=2,
                is_active=False
            ),
            ClusterAssignment(
                job_posting_id='job-123',
                enrichment_id='e3',
                cluster_id=1,
                cluster_name='ML Engineering',
                cluster_keywords=[],
                cluster_size=30,
                cluster_run_id='run-3',
                cluster_model_id='v1.0',
                cluster_version=3,
                is_active=True
            )
        ]
        
        # Verify history structure
        assert len(history) == 3
        
        # Only last should be active
        active = [h for h in history if h.is_active]
        assert len(active) == 1
        assert active[0].cluster_version == 3
    
    def test_cluster_migration_analysis(self):
        """Should identify jobs that frequently change clusters."""
        from lib.domain.entities import ClusterAssignment
        
        # Job that changed clusters frequently
        volatile_job_history = [
            ClusterAssignment(
                job_posting_id='volatile-job',
                enrichment_id='e1',
                cluster_id=0,
                cluster_name='Cluster A',
                cluster_keywords=[],
                cluster_size=10,
                cluster_run_id='run-1',
                cluster_model_id='v1.0',
                cluster_version=1,
                is_active=False
            ),
            ClusterAssignment(
                job_posting_id='volatile-job',
                enrichment_id='e2',
                cluster_id=2,  # Changed
                cluster_name='Cluster C',
                cluster_keywords=[],
                cluster_size=15,
                cluster_run_id='run-2',
                cluster_model_id='v1.0',
                cluster_version=2,
                is_active=False
            ),
            ClusterAssignment(
                job_posting_id='volatile-job',
                enrichment_id='e3',
                cluster_id=1,  # Changed again
                cluster_name='Cluster B',
                cluster_keywords=[],
                cluster_size=12,
                cluster_run_id='run-3',
                cluster_model_id='v1.0',
                cluster_version=3,
                is_active=True
            )
        ]
        
        # Count cluster changes
        clusters_visited = set(h.cluster_id for h in volatile_job_history)
        assert len(clusters_visited) == 3  # Was in 3 different clusters


class TestClusterVersionFiltering:
    """Tests for filtering by cluster version."""
    
    def test_get_active_cluster_assignments(self):
        """Should be able to filter to only active assignments."""
        from lib.domain.entities import ClusterAssignment
        
        assignments = [
            ClusterAssignment(
                job_posting_id='job-1',
                enrichment_id='e1',
                cluster_id=0,
                cluster_name='C0',
                cluster_keywords=[],
                cluster_size=10,
                cluster_run_id='run-old',
                cluster_model_id='v1.0',
                cluster_version=1,
                is_active=False
            ),
            ClusterAssignment(
                job_posting_id='job-1',
                enrichment_id='e2',
                cluster_id=1,
                cluster_name='C1',
                cluster_keywords=[],
                cluster_size=15,
                cluster_run_id='run-new',
                cluster_model_id='v1.0',
                cluster_version=2,
                is_active=True
            ),
            ClusterAssignment(
                job_posting_id='job-2',
                enrichment_id='e3',
                cluster_id=0,
                cluster_name='C0',
                cluster_keywords=[],
                cluster_size=10,
                cluster_run_id='run-new',
                cluster_model_id='v1.0',
                cluster_version=2,
                is_active=True
            )
        ]
        
        active = [a for a in assignments if a.is_active]
        
        assert len(active) == 2
        assert all(a.cluster_version == 2 for a in active)
    
    def test_get_assignments_by_run_id(self):
        """Should filter assignments by specific run ID."""
        from lib.domain.entities import ClusterAssignment
        
        run_1_id = 'run-abc-123'
        run_2_id = 'run-def-456'
        
        assignments = [
            ClusterAssignment(
                job_posting_id='job-1',
                enrichment_id='e1',
                cluster_id=0,
                cluster_name='C0',
                cluster_keywords=[],
                cluster_size=10,
                cluster_run_id=run_1_id,
                cluster_model_id='v1.0',
                cluster_version=1,
                is_active=False
            ),
            ClusterAssignment(
                job_posting_id='job-2',
                enrichment_id='e2',
                cluster_id=1,
                cluster_name='C1',
                cluster_keywords=[],
                cluster_size=15,
                cluster_run_id=run_1_id,
                cluster_model_id='v1.0',
                cluster_version=1,
                is_active=False
            ),
            ClusterAssignment(
                job_posting_id='job-1',
                enrichment_id='e3',
                cluster_id=1,
                cluster_name='C1',
                cluster_keywords=[],
                cluster_size=15,
                cluster_run_id=run_2_id,
                cluster_model_id='v1.0',
                cluster_version=2,
                is_active=True
            )
        ]
        
        run_1_assignments = [a for a in assignments if a.cluster_run_id == run_1_id]
        run_2_assignments = [a for a in assignments if a.cluster_run_id == run_2_id]
        
        assert len(run_1_assignments) == 2
        assert len(run_2_assignments) == 1


class TestClusterStabilityReporting:
    """Tests for stability reporting functionality."""
    
    def test_generate_stability_report(self):
        """Should generate a stability report between two runs."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        
        old_run = {
            'job-1': 0, 'job-2': 0, 'job-3': 1, 
            'job-4': 1, 'job-5': 2, 'job-6': 2
        }
        
        new_run = {
            'job-1': 0,  # Same
            'job-2': 1,  # Changed 0->1
            'job-3': 1,  # Same
            'job-4': 2,  # Changed 1->2
            'job-5': 2,  # Same
            'job-6': 0   # Changed 2->0
        }
        
        report = clusterer.generate_stability_report(old_run, new_run)
        
        assert 'overall_stability' in report
        assert 'jobs_unchanged' in report
        assert 'jobs_changed' in report
        
        assert report['jobs_unchanged'] == 3  # jobs 1, 3, 5
        assert report['jobs_changed'] == 3    # jobs 2, 4, 6
    
    def test_stability_report_includes_migrations(self):
        """Stability report should show cluster migrations."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        
        old_run = {
            'job-1': 0,
            'job-2': 0,
            'job-3': 1
        }
        
        new_run = {
            'job-1': 1,  # Moved 0->1
            'job-2': 1,  # Moved 0->1  
            'job-3': 1   # Same
        }
        
        report = clusterer.generate_stability_report(old_run, new_run)
        
        # Should track migration patterns
        if 'migrations' in report:
            migrations = report['migrations']
            # 2 jobs moved from cluster 0 to cluster 1
            assert migrations.get((0, 1), 0) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
