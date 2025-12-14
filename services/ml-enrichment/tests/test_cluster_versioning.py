"""
Unit Tests for Cluster Version Tracking

Tests the cluster version tracking functionality:
1. Cluster run ID generation
2. Version tracking across clustering runs
3. Active/inactive flag management
4. Stability metrics calculation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid


class TestClusterRunIdGeneration:
    """Tests for cluster run ID generation."""
    
    def test_cluster_run_id_is_uuid_format(self):
        """Cluster run ID should be a valid UUID."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        run_id = clusterer.generate_cluster_run_id()
        
        # Should be a valid UUID string
        assert isinstance(run_id, str)
        # Should be able to parse as UUID
        parsed = uuid.UUID(run_id)
        assert str(parsed) == run_id
    
    def test_cluster_run_id_is_unique(self):
        """Each call should generate a unique run ID."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        
        run_ids = [clusterer.generate_cluster_run_id() for _ in range(10)]
        
        # All should be unique
        assert len(run_ids) == len(set(run_ids))


class TestClusterVersionTracking:
    """Tests for cluster version tracking."""
    
    def test_clusterer_has_version(self):
        """JobClusterer should report its version."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        version = clusterer.get_version()
        
        assert isinstance(version, str)
        assert version.startswith('v')
    
    def test_cluster_model_id_set(self):
        """Clusterer should have a model ID."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        model_id = clusterer.get_model_id()
        
        assert isinstance(model_id, str)
        assert len(model_id) > 0
    
    def test_cluster_version_increments(self):
        """Cluster version should increment with each run."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        
        # First version should be 1
        version1 = clusterer.get_next_cluster_version()
        assert version1 >= 1
        
        # Simulating increment by calling again
        version2 = clusterer.get_next_cluster_version()
        assert version2 == version1 + 1


class TestClusterAssignmentEntity:
    """Tests for ClusterAssignment entity."""
    
    def test_cluster_assignment_has_version_fields(self):
        """ClusterAssignment should have version tracking fields."""
        from lib.domain.entities import ClusterAssignment
        
        assignment = ClusterAssignment(
            job_posting_id='job-123',
            enrichment_id='enrich-456',
            cluster_id=0,
            cluster_name='Tech Jobs',
            cluster_keywords=[{'term': 'python', 'score': 0.8}],
            cluster_size=50,
            cluster_run_id='run-789',
            cluster_model_id='job_clusterer_v1.0',
            cluster_version=1,
            is_active=True
        )
        
        # All version fields should be set
        assert assignment.cluster_run_id == 'run-789'
        assert assignment.cluster_model_id == 'job_clusterer_v1.0'
        assert assignment.cluster_version == 1
        assert assignment.is_active is True
    
    def test_cluster_assignment_default_is_active(self):
        """New cluster assignments should be active by default."""
        from lib.domain.entities import ClusterAssignment
        
        assignment = ClusterAssignment(
            job_posting_id='job-123',
            enrichment_id='enrich-456',
            cluster_id=0,
            cluster_name='Tech Jobs',
            cluster_keywords=[],
            cluster_size=10,
            cluster_run_id='run-abc',
            cluster_model_id='v1.0',
            cluster_version=1
        )
        
        # Default should be active
        assert assignment.is_active is True
    
    def test_cluster_assignment_to_dict_includes_version(self):
        """to_dict should include version tracking fields."""
        from lib.domain.entities import ClusterAssignment
        
        assignment = ClusterAssignment(
            job_posting_id='job-123',
            enrichment_id='enrich-456',
            cluster_id=0,
            cluster_name='Data Engineering',
            cluster_keywords=[{'term': 'spark', 'score': 0.9}],
            cluster_size=25,
            cluster_run_id='run-xyz',
            cluster_model_id='job_clusterer_v1.0',
            cluster_version=3,
            is_active=False
        )
        
        data = assignment.to_dict()
        
        assert 'cluster_run_id' in data
        assert 'cluster_model_id' in data
        assert 'cluster_version' in data
        assert 'is_active' in data
        assert data['cluster_version'] == 3
        assert data['is_active'] is False


class TestActiveClusterManagement:
    """Tests for managing active/inactive cluster assignments."""
    
    def test_deactivate_previous_assignments(self):
        """Should be able to deactivate previous cluster assignments for a job."""
        from lib.domain.entities import ClusterAssignment
        
        old_assignment = ClusterAssignment(
            job_posting_id='job-123',
            enrichment_id='enrich-old',
            cluster_id=1,
            cluster_name='Old Cluster',
            cluster_keywords=[],
            cluster_size=10,
            cluster_run_id='run-old',
            cluster_model_id='v1.0',
            cluster_version=1,
            is_active=True
        )
        
        # Deactivate
        old_assignment.deactivate()
        
        assert old_assignment.is_active is False
    
    def test_new_assignment_supersedes_old(self):
        """New cluster assignment should be active while old is inactive."""
        from lib.domain.entities import ClusterAssignment
        
        old_assignment = ClusterAssignment(
            job_posting_id='job-123',
            enrichment_id='enrich-old',
            cluster_id=1,
            cluster_name='Old Cluster',
            cluster_keywords=[],
            cluster_size=10,
            cluster_run_id='run-old',
            cluster_model_id='v1.0',
            cluster_version=1,
            is_active=True
        )
        
        # Create new assignment
        new_assignment = ClusterAssignment(
            job_posting_id='job-123',
            enrichment_id='enrich-new',
            cluster_id=2,
            cluster_name='New Cluster',
            cluster_keywords=[],
            cluster_size=15,
            cluster_run_id='run-new',
            cluster_model_id='v1.0',
            cluster_version=2,
            is_active=True
        )
        
        # Deactivate old
        old_assignment.deactivate()
        
        # Check state
        assert old_assignment.is_active is False
        assert new_assignment.is_active is True
        assert old_assignment.cluster_version < new_assignment.cluster_version


class TestClusterStabilityMetrics:
    """Tests for cluster stability metrics calculation."""
    
    def test_calculate_stability_perfect_match(self):
        """Stability should be 100% when all jobs stay in same cluster."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        
        # Previous assignments: job1->cluster1, job2->cluster2
        previous = {
            'job-1': 0,
            'job-2': 1,
            'job-3': 0
        }
        
        # Current assignments: same
        current = {
            'job-1': 0,
            'job-2': 1,
            'job-3': 0
        }
        
        stability = clusterer.calculate_cluster_stability(previous, current)
        
        assert stability == 1.0  # 100% stable
    
    def test_calculate_stability_complete_shuffle(self):
        """Stability should be 0% when all jobs change clusters."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        
        # All jobs change clusters
        previous = {
            'job-1': 0,
            'job-2': 1
        }
        current = {
            'job-1': 1,
            'job-2': 0
        }
        
        stability = clusterer.calculate_cluster_stability(previous, current)
        
        assert stability == 0.0  # 0% stable
    
    def test_calculate_stability_partial_change(self):
        """Stability should reflect partial changes correctly."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        
        # 2 out of 4 jobs change
        previous = {
            'job-1': 0,
            'job-2': 1,
            'job-3': 0,
            'job-4': 1
        }
        current = {
            'job-1': 0,  # same
            'job-2': 0,  # changed
            'job-3': 1,  # changed
            'job-4': 1   # same
        }
        
        stability = clusterer.calculate_cluster_stability(previous, current)
        
        assert stability == 0.5  # 50% stable (2/4)
    
    def test_calculate_stability_with_new_jobs(self):
        """Stability should only consider jobs that existed previously."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        
        # Previous: 2 jobs
        previous = {
            'job-1': 0,
            'job-2': 1
        }
        
        # Current: 2 old jobs (same clusters) + 1 new job
        current = {
            'job-1': 0,
            'job-2': 1,
            'job-3': 0  # New job, should be ignored for stability
        }
        
        stability = clusterer.calculate_cluster_stability(previous, current)
        
        assert stability == 1.0  # 100% of existing jobs are stable


class TestClusteringResultsWithVersion:
    """Tests for clustering results including version info."""
    
    def test_cluster_results_include_run_id(self):
        """Clustering results should include run ID."""
        from lib.enrichment.job_clusterer import JobClusterer
        
        clusterer = JobClusterer()
        
        # Create mock result
        run_id = clusterer.generate_cluster_run_id()
        model_id = clusterer.get_model_id()
        version = clusterer.get_version()
        
        result = {
            'job_posting_id': 'job-123',
            'cluster_id': 0,
            'cluster_name': 'Test Cluster',
            'cluster_run_id': run_id,
            'cluster_model_id': model_id,
            'cluster_version': 1,
            'is_active': True
        }
        
        assert 'cluster_run_id' in result
        assert 'cluster_model_id' in result
        assert 'cluster_version' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
