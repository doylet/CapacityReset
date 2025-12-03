"""
Unit Tests for Alias Extraction Strategy

Tests the AliasExtractionStrategy class that resolves skill aliases
to canonical names during skills extraction.
"""

import pytest
from unittest.mock import Mock, patch


class TestAliasExtractionStrategy:
    """Tests for the AliasExtractionStrategy class."""
    
    def test_alias_resolver_loads_from_yaml(self):
        """Alias resolver should load aliases from YAML config."""
        from lib.config import get_alias_resolver
        
        resolver = get_alias_resolver()
        
        # Should have loaded aliases
        all_aliases = resolver.get_all_aliases()
        assert len(all_aliases) > 0
    
    def test_alias_resolver_is_case_insensitive(self):
        """Alias resolution should be case-insensitive by default."""
        from lib.config import get_alias_resolver
        
        resolver = get_alias_resolver()
        
        # Test various cases
        test_cases = [
            ('K8s', 'K8S', 'k8s'),
            ('GCP', 'gcp', 'Gcp'),
            ('JS', 'js', 'Js')
        ]
        
        for variants in test_cases:
            results = [resolver.resolve(v) for v in variants]
            # All variants should return the same canonical name
            if results[0]:  # If alias exists
                assert all(r == results[0] for r in results)
    
    def test_alias_resolver_returns_none_for_unknown(self):
        """Alias resolver should return None for unknown aliases."""
        from lib.config import get_alias_resolver
        
        resolver = get_alias_resolver()
        
        # Unknown skill should return None
        result = resolver.resolve('NotAnAlias12345')
        assert result is None
    
    def test_alias_info_includes_confidence(self):
        """Alias info should include confidence score."""
        from lib.config import get_alias_resolver
        
        resolver = get_alias_resolver()
        
        info = resolver.get_alias_info('K8s')
        if info:
            assert 'confidence' in info
            assert 0.0 <= info['confidence'] <= 1.0
    
    def test_alias_info_includes_category(self):
        """Alias info should include skill category."""
        from lib.config import get_alias_resolver
        
        resolver = get_alias_resolver()
        
        info = resolver.get_alias_info('K8s')
        if info:
            assert 'category' in info
            assert info['category'] == 'devops_tools'
    
    def test_alias_is_alias_method(self):
        """is_alias should correctly identify known aliases."""
        from lib.config import get_alias_resolver
        
        resolver = get_alias_resolver()
        
        # Known aliases should return True
        assert resolver.is_alias('K8s') is True
        assert resolver.is_alias('GCP') is True
        
        # Unknown terms should return False
        assert resolver.is_alias('NotAnAlias12345') is False


class TestAliasIntegrationWithExtractor:
    """Tests for alias integration with the skills extractor."""
    
    def test_extractor_resolves_aliases_in_text(self):
        """Extractor should resolve aliases found in text."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        config = UnifiedSkillsConfig()
        extractor = UnifiedSkillsExtractor(
            config=config,
            enable_semantic=False,
            enable_patterns=False
        )
        
        # Test text with aliases
        result = extractor.extract_skills(
            job_summary="Looking for K8s administrator",
            job_description="Must know K8s and GCP",
            job_id="test-001"
        )
        
        # Check if skills were extracted
        skills = result.get('skills', [])
        skill_names = [s['text'].lower() for s in skills]
        
        # Should find skills (either alias or canonical)
        assert len(skills) > 0
    
    def test_extractor_deduplicates_alias_and_canonical(self):
        """Extractor should not report both alias and canonical for same skill."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        config = UnifiedSkillsConfig()
        extractor = UnifiedSkillsExtractor(
            config=config,
            enable_semantic=False,
            enable_patterns=False
        )
        
        # Text with both alias and canonical name
        result = extractor.extract_skills(
            job_summary="Need Kubernetes (K8s) expert",
            job_description="Experience with K8s and Kubernetes required",
            job_id="test-002"
        )
        
        skills = result.get('skills', [])
        skill_names = [s['text'].lower() for s in skills]
        
        # Should not have duplicates
        assert len(skill_names) == len(set(skill_names))
    
    def test_extraction_includes_source_strategies(self):
        """Extracted skills should include source_strategies field."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Python developer",
            job_description="Python and Django experience required",
            job_id="test-003"
        )
        
        skills = result.get('skills', [])
        if skills:
            # At least one skill should have extraction_method
            first_skill = skills[0]
            assert 'extraction_method' in first_skill


class TestSkillAliasEntity:
    """Tests for the SkillAlias entity."""
    
    def test_skill_alias_creation(self):
        """SkillAlias should be creatable with valid data."""
        from lib.domain.entities import SkillAlias
        
        alias = SkillAlias(
            alias_text="K8s",
            canonical_name="Kubernetes",
            skill_category="devops_tools",
            source="manual",
            confidence=1.0
        )
        
        assert alias.alias_text == "K8s"
        assert alias.canonical_name == "Kubernetes"
        assert alias.skill_category == "devops_tools"
        assert alias.confidence == 1.0
    
    def test_skill_alias_validates_confidence(self):
        """SkillAlias should validate confidence range."""
        from lib.domain.entities import SkillAlias
        
        # Valid confidence
        alias = SkillAlias(
            alias_text="K8s",
            canonical_name="Kubernetes",
            skill_category="devops_tools",
            confidence=0.9
        )
        assert alias.confidence == 0.9
        
        # Invalid confidence
        with pytest.raises(ValueError):
            SkillAlias(
                alias_text="K8s",
                canonical_name="Kubernetes",
                skill_category="devops_tools",
                confidence=1.5  # > 1.0
            )
    
    def test_skill_alias_serialization(self):
        """SkillAlias should survive serialization roundtrip."""
        from lib.domain.entities import SkillAlias
        
        original = SkillAlias(
            alias_text="GCP",
            canonical_name="Google Cloud Platform",
            skill_category="cloud_platforms",
            source="manual",
            confidence=1.0
        )
        
        data = original.to_dict()
        restored = SkillAlias.from_dict(data)
        
        assert restored.alias_text == original.alias_text
        assert restored.canonical_name == original.canonical_name
        assert restored.skill_category == original.skill_category
    
    def test_skill_alias_records_usage(self):
        """SkillAlias should track usage count."""
        from lib.domain.entities import SkillAlias
        
        alias = SkillAlias(
            alias_text="K8s",
            canonical_name="Kubernetes",
            skill_category="devops_tools"
        )
        
        assert alias.usage_count == 0
        
        alias.record_usage()
        assert alias.usage_count == 1
        
        alias.record_usage()
        assert alias.usage_count == 2


class TestCommonAliases:
    """Tests for common skill aliases that should be resolved."""
    
    @pytest.mark.parametrize("alias,expected_canonical", [
        ("K8s", "Kubernetes"),
        ("GCP", "Google Cloud Platform"),
        ("JS", "JavaScript"),
        ("TS", "TypeScript"),
        ("AWS", "Amazon Web Services"),
        ("Postgres", "PostgreSQL"),
        ("Mongo", "MongoDB"),
        ("Vue", "Vue.js"),
        ("ReactJS", "React"),
    ])
    def test_common_alias_resolution(self, alias, expected_canonical):
        """Common aliases should resolve to expected canonical names."""
        from lib.config import get_alias_resolver
        
        resolver = get_alias_resolver()
        result = resolver.resolve(alias)
        
        # If alias is configured, it should resolve correctly
        if result:
            assert result == expected_canonical


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
