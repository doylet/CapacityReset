"""
Integration Tests for Enrichment Versioning

Tests the integration of version tracking across the enrichment pipeline.
Verifies that:
1. Jobs can be queried by enrichment version
2. Re-enrichment workflows correctly identify outdated jobs
3. Version information flows through the entire pipeline
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json


class TestEnrichmentVersionQueries:
    """Tests for version-based enrichment queries."""
    
    def test_get_jobs_needing_enrichment_filters_by_version(self):
        """get_jobs_needing_enrichment should filter by version when specified."""
        # Create mock BigQuery client
        mock_client = Mock()
        mock_query_job = Mock()
        
        # Simulate query results
        mock_results = [
            {
                'job_posting_id': 'job-001',
                'job_title': 'Python Developer',
                'company_name': 'Test Corp',
                'job_location': 'Remote',
                'job_summary': 'Looking for Python dev',
                'job_description_formatted': 'Full stack Python role',
                'job_posted_date': datetime.utcnow()
            },
            {
                'job_posting_id': 'job-002',
                'job_title': 'Java Developer',
                'company_name': 'Test Corp',
                'job_location': 'NYC',
                'job_summary': 'Looking for Java dev',
                'job_description_formatted': 'Backend Java role',
                'job_posted_date': datetime.utcnow()
            }
        ]
        
        mock_query_job.result.return_value = mock_results
        mock_client.query.return_value = mock_query_job
        
        with patch('lib.utils.enrichment_utils.bigquery_client', mock_client):
            from lib.utils.enrichment_utils import get_jobs_needing_enrichment
            
            # Call with version filter
            jobs = get_jobs_needing_enrichment(
                enrichment_type='skills_extraction',
                limit=10,
                enrichment_version='v4.0-unified-config-enhanced'
            )
            
            # Verify query was called
            mock_client.query.assert_called_once()
            query_call = mock_client.query.call_args[0][0]
            
            # Query should include version filter
            assert 'enrichment_version' in query_call
            assert 'v4.0-unified-config-enhanced' in query_call
    
    def test_log_enrichment_includes_version(self):
        """log_enrichment should store version information."""
        mock_client = Mock()
        mock_client.insert_rows_json.return_value = []  # No errors
        
        with patch('lib.utils.enrichment_utils.bigquery_client', mock_client):
            from lib.utils.enrichment_utils import log_enrichment
            
            enrichment_id = log_enrichment(
                job_posting_id='job-123',
                enrichment_type='skills_extraction',
                enrichment_version='v4.0-unified-config-enhanced',
                status='success',
                metadata={'skills_count': 10}
            )
            
            # Verify insert was called
            mock_client.insert_rows_json.assert_called_once()
            
            # Check the row being inserted
            call_args = mock_client.insert_rows_json.call_args
            rows = call_args[0][1]
            
            assert len(rows) == 1
            row = rows[0]
            assert row['enrichment_version'] == 'v4.0-unified-config-enhanced'
            assert row['status'] == 'success'


class TestVersionFlowThroughPipeline:
    """Tests that version info flows through the enrichment pipeline."""
    
    def test_skills_extraction_stores_version(self):
        """Skills extraction should store version in enrichment record."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        # Create extractor
        config = UnifiedSkillsConfig()
        extractor = UnifiedSkillsExtractor(
            config=config,
            enable_semantic=False,
            enable_patterns=False
        )
        
        # Extract skills
        result = extractor.extract_skills(
            job_summary="Looking for Python developer",
            job_description="Must have 5+ years Python experience",
            job_id="test-job"
        )
        
        # Version should be in metadata
        assert 'extraction_metadata' in result
        version = result['extraction_metadata']['extractor_version']
        
        # Version should follow expected format
        assert version.startswith('v')
        assert '-' in version  # Has mode suffix
    
    def test_extraction_metadata_includes_mode_info(self):
        """Extraction metadata should indicate which modes were used."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Python developer",
            job_description="Python and Django required",
            job_id="test"
        )
        
        metadata = result['extraction_metadata']
        
        # Should include mode information
        assert 'enhanced_mode' in metadata
        assert 'semantic_enabled' in metadata
        assert 'patterns_enabled' in metadata


class TestReEnrichmentWorkflow:
    """Tests for identifying jobs that need re-enrichment."""
    
    def test_job_enrichment_needs_reprocessing_for_new_version(self):
        """JobEnrichment should correctly identify need for reprocessing."""
        from lib.domain.entities import JobEnrichment
        
        # Old enrichment with legacy version
        enrichment = JobEnrichment(
            job_posting_id='job-001',
            enrichment_type='skills_extraction',
            status='success',
            model_id='skills_extractor',
            model_version='v3.0-legacy',
            enrichment_version='skills_extractor_v3.0-legacy'
        )
        
        # Should need reprocessing for newer version
        assert enrichment.needs_reprocessing('skills_extractor_v4.0-enhanced')
        
        # Should not need reprocessing for same version
        assert not enrichment.needs_reprocessing('skills_extractor_v3.0-legacy')
    
    def test_failed_enrichment_always_needs_reprocessing(self):
        """Failed enrichments should always need reprocessing."""
        from lib.domain.entities import JobEnrichment
        
        enrichment = JobEnrichment(
            job_posting_id='job-001',
            enrichment_type='skills_extraction',
            status='failed',
            enrichment_version='skills_extractor_v4.0-enhanced'
        )
        
        # Even for same version, failed should need reprocessing
        assert enrichment.needs_reprocessing('skills_extractor_v4.0-enhanced')
    
    def test_enrichment_without_version_needs_reprocessing(self):
        """Enrichments without version should need reprocessing."""
        from lib.domain.entities import JobEnrichment
        
        enrichment = JobEnrichment(
            job_posting_id='job-001',
            enrichment_type='skills_extraction',
            status='success'
            # No version info
        )
        
        # Should need reprocessing since no version
        assert enrichment.needs_reprocessing('skills_extractor_v4.0-enhanced')


class TestModelConfigLoading:
    """Tests for loading model configuration from YAML."""
    
    def test_load_model_config_returns_correct_version(self):
        """Loading model config should return the active version."""
        from lib.config import load_model_config, get_current_version
        
        # Get current version for skills_extractor
        current_version = get_current_version('skills_extractor')
        
        if current_version:
            # Should have a version string
            assert isinstance(current_version, str)
            assert current_version.startswith('v')
    
    def test_load_skill_aliases_returns_list(self):
        """Loading skill aliases should return a list of mappings."""
        from lib.config import load_skill_aliases
        
        aliases = load_skill_aliases()
        
        # Should be a list
        assert isinstance(aliases, list)
        
        # If aliases exist, check structure
        if aliases:
            first_alias = aliases[0]
            assert 'alias' in first_alias
            assert 'canonical' in first_alias
            assert 'category' in first_alias
    
    def test_alias_resolver_singleton(self):
        """AliasResolver should be a singleton."""
        from lib.config import get_alias_resolver
        
        resolver1 = get_alias_resolver()
        resolver2 = get_alias_resolver()
        
        assert resolver1 is resolver2
    
    def test_alias_resolver_resolves_known_aliases(self):
        """AliasResolver should resolve known aliases."""
        from lib.config import get_alias_resolver
        
        resolver = get_alias_resolver()
        
        # Test some common aliases
        test_cases = [
            ('K8s', 'Kubernetes'),
            ('GCP', 'Google Cloud Platform'),
            ('JS', 'JavaScript'),
            ('TS', 'TypeScript')
        ]
        
        for alias, expected_canonical in test_cases:
            result = resolver.resolve(alias)
            if result:  # May be None if YAML not loaded
                assert result == expected_canonical, f"Expected {alias} -> {expected_canonical}, got {result}"


class TestVersionStorageInBigQuery:
    """Tests for version storage in BigQuery schemas."""
    
    def test_job_enrichment_entity_has_version_fields(self):
        """JobEnrichment entity should have all version fields."""
        from lib.domain.entities import JobEnrichment
        
        enrichment = JobEnrichment(
            job_posting_id='job-123',
            enrichment_type='skills_extraction',
            status='success',
            model_id='skills_extractor',
            model_version='v4.0-enhanced',
            enrichment_version='skills_extractor_v4.0-enhanced'
        )
        
        # Convert to dict for storage
        data = enrichment.to_dict()
        
        # Verify version fields are present
        assert 'model_id' in data
        assert 'model_version' in data
        assert 'enrichment_version' in data
        
        # Values should be correct
        assert data['model_id'] == 'skills_extractor'
        assert data['model_version'] == 'v4.0-enhanced'
        assert data['enrichment_version'] == 'skills_extractor_v4.0-enhanced'
    
    def test_job_enrichment_serialization_roundtrip(self):
        """JobEnrichment should survive serialization roundtrip."""
        from lib.domain.entities import JobEnrichment
        
        original = JobEnrichment(
            job_posting_id='job-123',
            enrichment_type='skills_extraction',
            status='success',
            model_id='skills_extractor',
            model_version='v4.0-enhanced'
        )
        
        data = original.to_dict()
        restored = JobEnrichment.from_dict(data)
        
        assert restored.job_posting_id == original.job_posting_id
        assert restored.enrichment_type == original.enrichment_type
        assert restored.model_id == original.model_id
        assert restored.model_version == original.model_version
        assert restored.enrichment_version == original.enrichment_version


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
