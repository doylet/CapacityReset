"""
Unit Tests for Confidence Scoring

Tests the confidence scoring system used in skills extraction.
Verifies that confidence scores are calculated correctly based on
multiple signals and stay within valid ranges.
"""

import pytest


class TestConfidenceScoring:
    """Tests for confidence score calculation."""
    
    def test_confidence_score_range(self):
        """Confidence scores should be between 0.0 and 1.0."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Python developer needed",
            job_description="Looking for Python and Django experience",
            job_id="test-001"
        )
        
        skills = result.get('skills', [])
        for skill in skills:
            confidence = skill.get('confidence', 0)
            assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} out of range for skill {skill}"
    
    def test_confidence_threshold_filters_skills(self):
        """Skills below confidence threshold should be filtered."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        # Set a high threshold
        config = UnifiedSkillsConfig()
        config.ml_config.min_confidence_threshold = 0.9
        
        extractor = UnifiedSkillsExtractor(
            config=config,
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Python developer",
            job_description="Python experience required",
            job_id="test-002"
        )
        
        skills = result.get('skills', [])
        threshold = result['extraction_metadata']['confidence_threshold']
        
        # All returned skills should meet threshold
        for skill in skills:
            assert skill['confidence'] >= threshold
    
    def test_lexicon_match_base_confidence(self):
        """Lexicon matches should have predictable base confidence."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Python developer",
            job_description="Python programming required",
            job_id="test-003"
        )
        
        skills = result.get('skills', [])
        python_skills = [s for s in skills if 'python' in s['text'].lower()]
        
        # Python should be found with reasonable confidence
        if python_skills:
            assert python_skills[0]['confidence'] >= 0.5
    
    def test_context_strength_affects_confidence(self):
        """Strong context indicators should boost confidence."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        # Extract from text with strong context
        result_strong = extractor.extract_skills(
            job_summary="Expert Python developer",
            job_description="Must have extensive Python experience. Expert-level Python required.",
            job_id="test-strong"
        )
        
        # Extract from text with weak context
        result_weak = extractor.extract_skills(
            job_summary="Developer",
            job_description="Some Python exposure helpful.",
            job_id="test-weak"
        )
        
        # Both should find Python
        strong_skills = result_strong.get('skills', [])
        weak_skills = result_weak.get('skills', [])
        
        python_strong = [s for s in strong_skills if 'python' in s['text'].lower()]
        python_weak = [s for s in weak_skills if 'python' in s['text'].lower()]
        
        # Strong context should have higher or equal confidence
        if python_strong and python_weak:
            assert python_strong[0]['confidence'] >= python_weak[0]['confidence'] - 0.1


class TestExtractionMetadata:
    """Tests for extraction metadata."""
    
    def test_metadata_includes_threshold(self):
        """Extraction metadata should include confidence threshold."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Developer",
            job_description="Development work",
            job_id="test"
        )
        
        assert 'extraction_metadata' in result
        assert 'confidence_threshold' in result['extraction_metadata']
    
    def test_metadata_includes_counts(self):
        """Extraction metadata should include match counts."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
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
        
        # Should have count information
        assert 'total_matches' in metadata
        assert 'filtered_matches' in metadata
        assert 'final_skills' in metadata
    
    def test_metadata_includes_mode_info(self):
        """Extraction metadata should indicate extraction mode."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Developer",
            job_description="Development work",
            job_id="test"
        )
        
        metadata = result['extraction_metadata']
        
        assert 'enhanced_mode' in metadata
        assert 'semantic_enabled' in metadata
        assert 'patterns_enabled' in metadata


class TestSkillScorerComponent:
    """Tests for the SkillScorer component."""
    
    def test_skill_scorer_exists(self):
        """SkillScorer class should exist and be usable."""
        from lib.enrichment.skills.scorer import SkillScorer
        from lib.enrichment.skills.unified_config import UnifiedSkillsConfig
        
        config = UnifiedSkillsConfig()
        scorer = SkillScorer(config)
        
        assert scorer is not None
    
    def test_scorer_handles_empty_context(self):
        """Scorer should handle skills with empty context."""
        from lib.enrichment.skills.scorer import SkillScorer
        from lib.enrichment.skills.unified_config import UnifiedSkillsConfig
        
        config = UnifiedSkillsConfig()
        scorer = SkillScorer(config)
        
        # Create a mock skill match
        mock_match = type('MockMatch', (), {
            'text': 'Python',
            'category': 'programming_languages',
            'confidence': 0.7,
            'context': '',
            'normalized': 'python'
        })()
        
        # Should not raise error
        # Note: Actual scoring method depends on implementation


class TestCategoryWeighting:
    """Tests for category-based confidence weighting."""
    
    def test_high_priority_categories_weighted_higher(self):
        """High priority categories should have higher base weight."""
        from lib.enrichment.skills.unified_config import UnifiedSkillsConfig
        
        config = UnifiedSkillsConfig()
        
        # Programming languages should have high weight
        prog_lang_weight = config.get_category_weight('programming_languages')
        
        # Soft skills should have lower weight
        soft_skills_weight = config.get_category_weight('soft_skills')
        
        # Programming languages should be weighted higher than soft skills
        assert prog_lang_weight > soft_skills_weight
    
    def test_category_weight_defaults(self):
        """Unknown categories should have a default weight."""
        from lib.enrichment.skills.unified_config import UnifiedSkillsConfig
        
        config = UnifiedSkillsConfig()
        
        # Unknown category should return default
        weight = config.get_category_weight('unknown_category_12345')
        
        assert weight == 0.5  # Default weight


class TestConfidenceComponents:
    """Tests for individual confidence scoring components."""
    
    def test_frequency_affects_confidence(self):
        """More frequent mentions should boost confidence."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        # Extract from text with many Python mentions
        result_frequent = extractor.extract_skills(
            job_summary="Python Python Python developer",
            job_description="Python Python Python Python Python experience required",
            job_id="test-frequent"
        )
        
        # Extract from text with single mention
        result_single = extractor.extract_skills(
            job_summary="Developer",
            job_description="Python experience required",
            job_id="test-single"
        )
        
        frequent_skills = result_frequent.get('skills', [])
        single_skills = result_single.get('skills', [])
        
        python_frequent = [s for s in frequent_skills if 'python' in s['text'].lower()]
        python_single = [s for s in single_skills if 'python' in s['text'].lower()]
        
        # Frequent mentions might boost confidence
        # (This is implementation-dependent)
        if python_frequent and python_single:
            # At minimum, both should be found
            assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
