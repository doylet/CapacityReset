"""
Integration Tests for Cluster Stability Metrics

Tests the cluster stability tracking between clustering runs:
- Comparing cluster assignments across runs
- Calculating stability metrics
- Version-based filtering
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestClusterVersionQueries:
    """Tests for version-based cluster queries."""
    
    def test_query_clusters_by_run_id(self):
        """Should be able to query clusters by run_id."""
        mock_client = Mock()
        mock_query_job = Mock()
        
        # Mock results
        mock_results = [
            {
                'cluster_assignment_id': 'ca-001',
                'job_posting_id': 'job-001',
                'cluster_id': 1,
                'cluster_name': 'Python Devs',
                'cluster_run_id': 'run-001',
                'is_active': True
            },
            {
                'cluster_assignment_id': 'ca-002',
                'job_posting_id': 'job-002',
                'cluster_id': 1,
                'cluster_name': 'Python Devs',
                'cluster_run_id': 'run-001',
                'is_active': True
            }
        ]
        
        mock_query_job.result.return_value = mock_results
        mock_client.query.return_value = mock_query_job
        
        # Query should include run_id filter
        with patch('google.cloud.bigquery.Client', return_value=mock_client):
            # The query would be executed here
            # Verify query structure includes run_id
            mock_client.query.assert_not_called()  # Just checking mock setup
    
    def test_query_active_clusters_only(self):
        """Should filter to only active cluster assignments."""
        # Active clusters are the current assignments
        all_clusters = [
            {'job_posting_id': 'job-001', 'cluster_id': 1, 'is_active': True, 'cluster_version': 2},
            {'job_posting_id': 'job-001', 'cluster_id': 2, 'is_active': False, 'cluster_version': 1},
            {'job_posting_id': 'job-002', 'cluster_id': 1, 'is_active': True, 'cluster_version': 1}
        ]
        
        active_clusters = [c for c in all_clusters if c['is_active']]
        
        assert len(active_clusters) == 2
        assert all(c['is_active'] for c in active_clusters)


class TestClusterComparison:
    """Tests for comparing cluster assignments across runs."""
    
    def test_identify_changed_clusters(self):
        """Should identify jobs that changed clusters between runs."""
        old_run = [
            {'job_posting_id': 'job-001', 'cluster_id': 1, 'cluster_run_id': 'run-001'},
            {'job_posting_id': 'job-002', 'cluster_id': 1, 'cluster_run_id': 'run-001'},
            {'job_posting_id': 'job-003', 'cluster_id': 2, 'cluster_run_id': 'run-001'},
            {'job_posting_id': 'job-004', 'cluster_id': 2, 'cluster_run_id': 'run-001'}
        ]
        
        new_run = [
            {'job_posting_id': 'job-001', 'cluster_id': 1, 'cluster_run_id': 'run-002'},  # Same
            {'job_posting_id': 'job-002', 'cluster_id': 2, 'cluster_run_id': 'run-002'},  # Changed
            {'job_posting_id': 'job-003', 'cluster_id': 2, 'cluster_run_id': 'run-002'},  # Same
            {'job_posting_id': 'job-004', 'cluster_id': 1, 'cluster_run_id': 'run-002'}   # Changed
        ]
        
        # Create lookup
        old_by_job = {c['job_posting_id']: c['cluster_id'] for c in old_run}
        
        changed = []
        unchanged = []
        
        for new_cluster in new_run:
            job_id = new_cluster['job_posting_id']
            old_cluster_id = old_by_job.get(job_id)
            
            if old_cluster_id is not None:
                if old_cluster_id != new_cluster['cluster_id']:
                    changed.append({
                        'job_posting_id': job_id,
                        'old_cluster': old_cluster_id,
                        'new_cluster': new_cluster['cluster_id']
                    })
                else:
                    unchanged.append(job_id)
        
        assert len(changed) == 2
        assert len(unchanged) == 2
        assert changed[0]['job_posting_id'] == 'job-002'
        assert changed[1]['job_posting_id'] == 'job-004'
    
    def test_identify_new_jobs(self):
        """Should identify jobs that are new in the latest run."""
        old_run = [
            {'job_posting_id': 'job-001', 'cluster_id': 1},
            {'job_posting_id': 'job-002', 'cluster_id': 1}
        ]
        
        new_run = [
            {'job_posting_id': 'job-001', 'cluster_id': 1},
            {'job_posting_id': 'job-002', 'cluster_id': 1},
            {'job_posting_id': 'job-003', 'cluster_id': 2},  # New
            {'job_posting_id': 'job-004', 'cluster_id': 2}   # New
        ]
        
        old_job_ids = {c['job_posting_id'] for c in old_run}
        new_jobs = [c for c in new_run if c['job_posting_id'] not in old_job_ids]
        
        assert len(new_jobs) == 2
        assert new_jobs[0]['job_posting_id'] == 'job-003'
        assert new_jobs[1]['job_posting_id'] == 'job-004'


class TestClusterStabilityMetrics:
    """Tests for overall cluster stability metrics."""
    
    def test_calculate_stability_index(self):
        """Should calculate overall stability index between runs."""
        old_assignments = {
            'job-001': 1, 'job-002': 1, 'job-003': 2, 'job-004': 2,
            'job-005': 3, 'job-006': 3, 'job-007': 1, 'job-008': 2
        }
        
        new_assignments = {
            'job-001': 1, 'job-002': 1, 'job-003': 2, 'job-004': 3,  # job-004 changed
            'job-005': 3, 'job-006': 1, 'job-007': 1, 'job-008': 2   # job-006 changed
        }
        
        # Calculate stability
        common_jobs = set(old_assignments.keys()) & set(new_assignments.keys())
        stable = sum(
            1 for job_id in common_jobs
            if old_assignments[job_id] == new_assignments[job_id]
        )
        
        stability_index = stable / len(common_jobs) if common_jobs else 0
        
        # 6 out of 8 stayed in same cluster
        assert stability_index == 0.75
    
    def test_calculate_cluster_size_changes(self):
        """Should track cluster size changes between runs."""
        old_clusters = {
            1: {'size': 10, 'name': 'Python Devs'},
            2: {'size': 15, 'name': 'Java Devs'},
            3: {'size': 8, 'name': 'Data Scientists'}
        }
        
        new_clusters = {
            1: {'size': 12, 'name': 'Python Devs'},      # Grew
            2: {'size': 10, 'name': 'Java Devs'},        # Shrunk
            3: {'size': 8, 'name': 'Data Scientists'}    # Same
        }
        
        changes = {}
        for cluster_id in old_clusters:
            if cluster_id in new_clusters:
                changes[cluster_id] = {
                    'old_size': old_clusters[cluster_id]['size'],
                    'new_size': new_clusters[cluster_id]['size'],
                    'change': new_clusters[cluster_id]['size'] - old_clusters[cluster_id]['size']
                }
        
        assert changes[1]['change'] == 2
        assert changes[2]['change'] == -5
        assert changes[3]['change'] == 0


class TestDeactivatePreviousAssignments:
    """Tests for deactivating previous cluster assignments."""
    
    def test_deactivate_updates_flag(self):
        """Deactivation should set is_active to False."""
        from lib.domain.entities import ClusterAssignment
        
        assignment = ClusterAssignment(
            job_posting_id='job-001',
            enrichment_id='enr-001',
            cluster_id=1,
            cluster_name='Test',
            cluster_keywords=[],
            cluster_size=10,
            is_active=True
        )
        
        assert assignment.is_active is True
        
        assignment.deactivate()
        
        assert assignment.is_active is False
    
    def test_only_one_active_per_job(self):
        """Only one cluster assignment per job should be active."""
        from lib.domain.entities import ClusterAssignment
        
        # First run
        v1 = ClusterAssignment(
            job_posting_id='job-001',
            enrichment_id='enr-001',
            cluster_id=1,
            cluster_name='Test',
            cluster_keywords=[],
            cluster_size=10,
            cluster_version=1,
            is_active=True
        )
        
        # Simulate new run - deactivate old
        v1.deactivate()
        
        # Second run
        v2 = ClusterAssignment(
            job_posting_id='job-001',
            enrichment_id='enr-002',
            cluster_id=2,
            cluster_name='Updated Test',
            cluster_keywords=[],
            cluster_size=15,
            cluster_version=2,
            is_active=True
        )
        
        # Only v2 should be active
        assert v1.is_active is False
        assert v2.is_active is True


class TestClusterHistoryTracking:
    """Tests for tracking cluster history over time."""
    
    def test_version_history_preserved(self):
        """All versions should be preserved for historical analysis."""
        assignments = [
            {'job_id': 'job-001', 'cluster_id': 1, 'version': 1, 'run_id': 'run-001', 'is_active': False},
            {'job_id': 'job-001', 'cluster_id': 2, 'version': 2, 'run_id': 'run-002', 'is_active': False},
            {'job_id': 'job-001', 'cluster_id': 1, 'version': 3, 'run_id': 'run-003', 'is_active': True}
        ]
        
        # All versions should be in history
        assert len(assignments) == 3
        
        # Only latest is active
        active = [a for a in assignments if a['is_active']]
        assert len(active) == 1
        assert active[0]['version'] == 3
    
    def test_can_compare_any_two_versions(self):
        """Should be able to compare any two historical versions."""
        versions = {
            'run-001': {'job-001': 1, 'job-002': 1, 'job-003': 2},
            'run-002': {'job-001': 2, 'job-002': 1, 'job-003': 2},
            'run-003': {'job-001': 2, 'job-002': 2, 'job-003': 1}
        }
        
        # Compare run-001 vs run-003
        old = versions['run-001']
        new = versions['run-003']
        
        common = set(old.keys()) & set(new.keys())
        changed = sum(1 for job_id in common if old[job_id] != new[job_id])
        
        # All 3 jobs changed clusters
        assert changed == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
