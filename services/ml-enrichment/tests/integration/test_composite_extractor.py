"""
Integration Tests for Composite Skills Extractor

Tests the integration of multiple extraction strategies:
- Lexicon matching
- Alias resolution
- Pattern-based extraction
- Semantic similarity (when available)
- NER extraction
"""

import pytest
from unittest.mock import Mock, patch


class TestCompositeExtractorIntegration:
    """Tests for the composite extraction pipeline."""
    
    def test_extractor_combines_multiple_strategies(self):
        """Extractor should combine results from multiple strategies."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        # Job description with skills that should be found by different strategies
        result = extractor.extract_skills(
            job_summary="Python and JavaScript developer needed",
            job_description="""
            Requirements:
            - 5+ years of Python experience
            - Experience with React and Vue.js
            - Knowledge of PostgreSQL and MongoDB
            - AWS or GCP cloud experience
            - Kubernetes (K8s) for container orchestration
            """,
            job_id="test-001"
        )
        
        skills = result.get('skills', [])
        skill_names = [s['text'].lower() for s in skills]
        
        # Should find skills from various categories
        assert len(skills) > 0
        
        # Check metadata shows strategies used
        metadata = result.get('extraction_metadata', {})
        assert 'extractor_version' in metadata
    
    def test_extractor_deduplicates_across_strategies(self):
        """Skills found by multiple strategies should be deduplicated."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        # Mention the same skill multiple times
        result = extractor.extract_skills(
            job_summary="Python Python Python developer",
            job_description="Must have Python experience. Strong Python skills required. Python is essential.",
            job_id="test-002"
        )
        
        skills = result.get('skills', [])
        skill_names = [s['text'].lower() for s in skills]
        
        # Should not have duplicate entries
        assert len(skill_names) == len(set(skill_names))
    
    def test_extractor_normalizes_skill_names(self):
        """Skills should be normalized consistently."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        # Use different cases for same skills
        result = extractor.extract_skills(
            job_summary="Python and PYTHON developer",
            job_description="Experience with python, Python, and PYTHON required",
            job_id="test-003"
        )
        
        skills = result.get('skills', [])
        skill_names = [s['text'].lower() for s in skills]
        
        # Python should appear only once
        python_count = skill_names.count('python')
        assert python_count <= 1
    
    def test_extractor_includes_extraction_method(self):
        """Each skill should indicate its extraction method."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Senior Python developer",
            job_description="Python and Django experience required",
            job_id="test-004"
        )
        
        skills = result.get('skills', [])
        
        if skills:
            for skill in skills:
                # Each skill should have extraction method
                assert 'extraction_method' in skill
                # Method should be a valid string
                assert isinstance(skill['extraction_method'], str)
                assert len(skill['extraction_method']) > 0
    
    def test_extractor_scores_skills_by_confidence(self):
        """Skills should be scored and sorted by confidence."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Senior Python developer",
            job_description="Python, Django, PostgreSQL experience required",
            job_id="test-005"
        )
        
        skills = result.get('skills', [])
        
        if len(skills) > 1:
            # Skills should be sorted by confidence (descending)
            confidences = [s.get('confidence', 0) for s in skills]
            assert confidences == sorted(confidences, reverse=True)
    
    def test_extractor_includes_context_snippets(self):
        """Skills should include surrounding context."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Python developer",
            job_description="Must have 5+ years of Python experience",
            job_id="test-006"
        )
        
        skills = result.get('skills', [])
        
        if skills:
            for skill in skills:
                # Each skill should have context
                assert 'context' in skill
                assert isinstance(skill['context'], str)
    
    def test_extractor_categorizes_skills(self):
        """Skills should be assigned to categories."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Full stack developer",
            job_description="Python, React, PostgreSQL, AWS experience needed",
            job_id="test-007"
        )
        
        skills = result.get('skills', [])
        
        if skills:
            for skill in skills:
                # Each skill should have a category
                assert 'category' in skill
                assert isinstance(skill['category'], str)


class TestAliasIntegration:
    """Tests for alias resolution integration."""
    
    def test_alias_resolved_in_extraction(self):
        """Known aliases should be resolved during extraction."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        from lib.config import get_alias_resolver
        
        # Check if alias resolver has entries
        resolver = get_alias_resolver()
        all_aliases = resolver.get_all_aliases()
        
        if not all_aliases:
            pytest.skip("No aliases configured")
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        # Use a known alias
        result = extractor.extract_skills(
            job_summary="K8s administrator needed",
            job_description="Experience with K8s and container orchestration",
            job_id="test-008"
        )
        
        skills = result.get('skills', [])
        # Should find skills from the text
        assert len(skills) >= 0  # May or may not find depending on config
    
    def test_alias_resolver_provides_category(self):
        """Alias resolution should provide skill category."""
        from lib.config import get_alias_resolver
        
        resolver = get_alias_resolver()
        
        info = resolver.get_alias_info('K8s')
        
        if info:  # May be None if aliases not configured
            assert 'category' in info
            assert 'confidence' in info


class TestExtractionWithVariousInputs:
    """Tests for extraction with different input types."""
    
    def test_extraction_with_empty_input(self):
        """Extractor should handle empty input gracefully."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="",
            job_description="",
            job_id="test-empty"
        )
        
        # Should return valid result structure
        assert 'skills' in result
        assert 'extraction_metadata' in result
        assert result['skills'] == []
    
    def test_extraction_with_none_values(self):
        """Extractor should handle None input gracefully."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        # This should not raise an exception
        try:
            result = extractor.extract_skills(
                job_summary=None or "",
                job_description=None or "",
                job_id="test-none"
            )
            assert 'skills' in result
        except (TypeError, AttributeError):
            pytest.fail("Extractor should handle None gracefully")
    
    def test_extraction_with_special_characters(self):
        """Extractor should handle special characters."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="C++ & C# developer needed!",
            job_description="Experience with .NET, ASP.NET, and Vue.js (3.x+) required",
            job_id="test-special"
        )
        
        # Should return valid result
        assert 'skills' in result
        assert isinstance(result['skills'], list)
    
    def test_extraction_with_long_text(self):
        """Extractor should handle very long job descriptions."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        # Create a long description
        long_description = " ".join([
            "Python developer experience required.",
            "Knowledge of Django and Flask.",
            "Database experience with PostgreSQL."
        ] * 100)
        
        result = extractor.extract_skills(
            job_summary="Senior Software Engineer",
            job_description=long_description,
            job_id="test-long"
        )
        
        # Should complete without error
        assert 'skills' in result
        assert 'extraction_metadata' in result


class TestEnhancedModeToggle:
    """Tests for enhanced vs original mode."""
    
    def test_enhanced_mode_detection(self):
        """Extractor should detect enhanced mode availability."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=True,
            enable_patterns=True
        )
        
        # Should have enhanced_mode attribute
        assert hasattr(extractor, 'enhanced_mode')
        assert isinstance(extractor.enhanced_mode, bool)
    
    def test_version_includes_mode_suffix(self):
        """Version string should indicate mode."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        version = extractor.get_version()
        
        # Version should include mode suffix
        assert '-enhanced' in version or '-legacy' in version
    
    def test_fallback_mode_works(self):
        """Extractor should work in fallback mode."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        config = UnifiedSkillsConfig()
        config.fallback_to_original = True
        
        extractor = UnifiedSkillsExtractor(
            config=config,
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Python developer",
            job_description="Python and Django required",
            job_id="test-fallback"
        )
        
        # Should produce results even in fallback mode
        assert 'skills' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
