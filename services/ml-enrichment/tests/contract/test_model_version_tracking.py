"""
Contract Tests for Model Version Tracking

Tests the contracts for model version management in the ML enrichment service.
Ensures that:
1. All enrichments include version identifiers
2. Version format follows the standard pattern
3. Model configs can be loaded and validated
"""

import pytest
from datetime import datetime
import re


class TestModelConfigContract:
    """Tests for ModelConfig entity contract."""
    
    def test_model_config_version_pattern(self):
        """Version must follow pattern: v{major}.{minor}[-{suffix}]."""
        from lib.config.model_config import ModelConfig
        
        # Valid versions
        valid_versions = [
            "v1.0",
            "v4.0-unified-config-enhanced",
            "v4.0-unified-config-legacy",
            "v1.0-kmeans-tfidf",
            "v2.5-beta",
            "v10.20-alpha-test"
        ]
        
        for version in valid_versions:
            config = ModelConfig(
                model_id="test_model",
                version=version,
                model_type="skills_extraction"
            )
            assert config.version == version
    
    def test_model_config_invalid_version_rejected(self):
        """Invalid version formats should be rejected."""
        from lib.config.model_config import ModelConfig
        
        invalid_versions = [
            "1.0",              # Missing 'v' prefix
            "v1",               # Missing minor version
            "version1.0",       # Wrong prefix
            "v1.0_something",   # Underscore instead of hyphen
            "v1.0-UPPERCASE"    # Uppercase in suffix
        ]
        
        for version in invalid_versions:
            with pytest.raises(ValueError):
                ModelConfig(
                    model_id="test_model",
                    version=version,
                    model_type="skills_extraction"
                )
    
    def test_model_config_model_id_pattern(self):
        """Model ID must be lowercase with underscores only."""
        from lib.config.model_config import ModelConfig
        
        # Valid model IDs
        valid_ids = [
            "skills_extractor",
            "job_clusterer",
            "embeddings_generator",
            "section_classifier"
        ]
        
        for model_id in valid_ids:
            config = ModelConfig(
                model_id=model_id,
                version="v1.0",
                model_type="skills_extraction"
            )
            assert config.model_id == model_id
    
    def test_model_config_invalid_model_id_rejected(self):
        """Invalid model IDs should be rejected."""
        from lib.config.model_config import ModelConfig
        
        invalid_ids = [
            "SkillsExtractor",   # Uppercase
            "skills-extractor",  # Hyphen
            "skills.extractor",  # Dot
            "skills extractor",  # Space
            "123_model"          # Starts with number
        ]
        
        for model_id in invalid_ids:
            with pytest.raises(ValueError):
                ModelConfig(
                    model_id=model_id,
                    version="v1.0",
                    model_type="skills_extraction"
                )
    
    def test_model_config_valid_model_types(self):
        """Model type must be one of the allowed types."""
        from lib.config.model_config import ModelConfig
        
        valid_types = [
            "skills_extraction",
            "embeddings",
            "clustering",
            "section_classification"
        ]
        
        for model_type in valid_types:
            config = ModelConfig(
                model_id="test_model",
                version="v1.0",
                model_type=model_type
            )
            assert config.model_type == model_type
    
    def test_model_config_invalid_model_type_rejected(self):
        """Invalid model types should be rejected."""
        from lib.config.model_config import ModelConfig
        
        with pytest.raises(ValueError):
            ModelConfig(
                model_id="test_model",
                version="v1.0",
                model_type="invalid_type"
            )
    
    def test_model_config_get_full_version_id(self):
        """Full version ID should combine model_id and version."""
        from lib.config.model_config import ModelConfig
        
        config = ModelConfig(
            model_id="skills_extractor",
            version="v4.0-unified-config-enhanced",
            model_type="skills_extraction"
        )
        
        assert config.get_full_version_id() == "skills_extractor_v4.0-unified-config-enhanced"
    
    def test_model_config_performance_metrics_validation(self):
        """Performance metrics must be between 0.0 and 1.0."""
        from lib.config.model_config import ModelConfig
        
        # Valid metrics
        config = ModelConfig(
            model_id="test_model",
            version="v1.0",
            model_type="skills_extraction",
            performance_metrics={"precision": 0.85, "recall": 0.90, "f1": 0.87}
        )
        assert config.performance_metrics["precision"] == 0.85
        
        # Invalid metrics
        with pytest.raises(ValueError):
            ModelConfig(
                model_id="test_model",
                version="v1.0",
                model_type="skills_extraction",
                performance_metrics={"precision": 1.5}  # > 1.0
            )
    
    def test_model_config_to_dict_roundtrip(self):
        """ModelConfig should survive serialization/deserialization."""
        from lib.config.model_config import ModelConfig
        
        original = ModelConfig(
            model_id="skills_extractor",
            version="v4.0-enhanced",
            model_type="skills_extraction",
            description="Test model",
            performance_metrics={"f1": 0.85}
        )
        
        data = original.to_dict()
        restored = ModelConfig.from_dict(data)
        
        assert restored.model_id == original.model_id
        assert restored.version == original.version
        assert restored.model_type == original.model_type
        assert restored.performance_metrics == original.performance_metrics


class TestJobEnrichmentVersionContract:
    """Tests for JobEnrichment entity version tracking contract."""
    
    def test_enrichment_includes_version_fields(self):
        """JobEnrichment must include version tracking fields."""
        from lib.domain.entities import JobEnrichment
        
        enrichment = JobEnrichment(
            job_posting_id="test-job-123",
            enrichment_type="skills_extraction",
            status="success"
        )
        
        # Version fields should exist
        assert hasattr(enrichment, 'model_id')
        assert hasattr(enrichment, 'model_version')
        assert hasattr(enrichment, 'enrichment_version')
    
    def test_enrichment_version_auto_computed(self):
        """Enrichment version should be auto-computed when model info is set."""
        from lib.domain.entities import JobEnrichment
        
        enrichment = JobEnrichment(
            job_posting_id="test-job-123",
            enrichment_type="skills_extraction",
            status="success",
            model_id="skills_extractor",
            model_version="v4.0-enhanced"
        )
        
        assert enrichment.enrichment_version == "skills_extractor_v4.0-enhanced"
    
    def test_enrichment_set_version_method(self):
        """set_version should update all version fields."""
        from lib.domain.entities import JobEnrichment
        
        enrichment = JobEnrichment(
            job_posting_id="test-job-123",
            enrichment_type="skills_extraction",
            status="pending"
        )
        
        enrichment.set_version("skills_extractor", "v4.0-enhanced")
        
        assert enrichment.model_id == "skills_extractor"
        assert enrichment.model_version == "v4.0-enhanced"
        assert enrichment.enrichment_version == "skills_extractor_v4.0-enhanced"
    
    def test_enrichment_needs_reprocessing_check(self):
        """needs_reprocessing should correctly identify outdated enrichments."""
        from lib.domain.entities import JobEnrichment
        
        enrichment = JobEnrichment(
            job_posting_id="test-job-123",
            enrichment_type="skills_extraction",
            status="success",
            enrichment_version="skills_extractor_v3.0-legacy"
        )
        
        # Should need reprocessing for newer version
        assert enrichment.needs_reprocessing("skills_extractor_v4.0-enhanced") is True
        
        # Should not need reprocessing for same version
        assert enrichment.needs_reprocessing("skills_extractor_v3.0-legacy") is False
    
    def test_enrichment_valid_types(self):
        """Enrichment type must be one of the allowed types."""
        from lib.domain.entities import JobEnrichment
        
        valid_types = [
            "skills_extraction",
            "embeddings",
            "clustering",
            "section_classification"
        ]
        
        for enrichment_type in valid_types:
            enrichment = JobEnrichment(
                job_posting_id="test-job-123",
                enrichment_type=enrichment_type,
                status="pending"
            )
            assert enrichment.enrichment_type == enrichment_type
    
    def test_enrichment_valid_statuses(self):
        """Enrichment status must be one of the allowed values."""
        from lib.domain.entities import JobEnrichment
        
        valid_statuses = ["pending", "processing", "success", "failed"]
        
        for status in valid_statuses:
            enrichment = JobEnrichment(
                job_posting_id="test-job-123",
                enrichment_type="skills_extraction",
                status=status
            )
            assert enrichment.status == status


class TestExtractorVersionContract:
    """Tests for skills extractor version reporting contract."""
    
    def test_extractor_has_get_version_method(self):
        """UnifiedSkillsExtractor must have get_version method."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor()
        
        assert hasattr(extractor, 'get_version')
        version = extractor.get_version()
        assert isinstance(version, str)
        assert len(version) > 0
    
    def test_extractor_version_includes_mode_suffix(self):
        """Extractor version should indicate enhanced or legacy mode."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor()
        version = extractor.get_version()
        
        # Version should end with -enhanced or -legacy
        assert version.endswith("-enhanced") or version.endswith("-legacy")
    
    def test_extraction_result_includes_version(self):
        """Extraction results should include extractor version in metadata."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(enable_semantic=False, enable_patterns=False)
        
        result = extractor.extract_skills(
            job_summary="Python developer needed",
            job_description="Looking for Python expertise",
            job_id="test-001"
        )
        
        assert 'extraction_metadata' in result
        assert 'extractor_version' in result['extraction_metadata']
        assert result['extraction_metadata']['extractor_version'] == extractor.get_version()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
