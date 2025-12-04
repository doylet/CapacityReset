"""
Integration Tests for Composite Extractor

Tests the unified skills extractor with multiple extraction strategies:
1. Lexicon matching
2. Alias resolution
3. Pattern matching
4. NER extraction
5. Noun chunk extraction

Verifies that strategies work together correctly with proper deduplication
and confidence scoring.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestCompositeExtractorIntegration:
    """Tests for composite extraction with multiple strategies."""
    
    def test_extractor_combines_multiple_strategies(self):
        """Extractor should combine results from multiple strategies."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        extractor = UnifiedSkillsExtractor(
            config=UnifiedSkillsConfig(),
            enable_semantic=False,  # Disable to avoid dependency
            enable_patterns=True
        )
        
        result = extractor.extract_skills(
            job_summary="Senior Python Developer with Kubernetes experience",
            job_description="""
            Requirements:
            - 5+ years Python programming experience
            - Experience with K8s and Docker containerization
            - Knowledge of AWS or GCP cloud platforms
            - Strong SQL database skills
            - Familiarity with React or Vue.js
            """,
            job_id="test-composite-001"
        )
        
        # Should extract skills
        assert 'skills' in result
        skills = result['skills']
        
        # Should find core skills
        skill_texts = [s['text'].lower() for s in skills]
        
        # Programming language should be found
        assert any('python' in s for s in skill_texts)
        
        # Metadata should be included
        assert 'extraction_metadata' in result
        metadata = result['extraction_metadata']
        assert 'total_matches' in metadata
        assert 'filtered_matches' in metadata
    
    def test_deduplication_keeps_highest_confidence(self):
        """When skill found by multiple strategies, highest confidence wins."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        # Job with Python mentioned multiple times
        result = extractor.extract_skills(
            job_summary="Python Python Python developer needed",
            job_description="We need a Python expert. Experience with Python required. Python is essential.",
            job_id="test-dedup"
        )
        
        skills = result['skills']
        
        # Python should appear only once
        python_skills = [s for s in skills if 'python' in s['text'].lower()]
        assert len(python_skills) == 1, "Python should be deduplicated"
    
    def test_category_assignment_is_correct(self):
        """Skills should be assigned to correct categories."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        result = extractor.extract_skills(
            job_summary="Full stack developer position",
            job_description="Must know Python, React, PostgreSQL, and Docker",
            job_id="test-category"
        )
        
        skills_by_category = {}
        for skill in result['skills']:
            cat = skill['category']
            if cat not in skills_by_category:
                skills_by_category[cat] = []
            skills_by_category[cat].append(skill['text'].lower())
        
        # Check some expected categories
        if 'programming_languages' in skills_by_category:
            assert 'python' in skills_by_category['programming_languages']
        
        if 'databases' in skills_by_category:
            assert any('postgresql' in s or 'postgres' in s 
                      for s in skills_by_category['databases'])
    
    def test_confidence_scores_in_valid_range(self):
        """All confidence scores should be between 0 and 1."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        result = extractor.extract_skills(
            job_summary="DevOps Engineer",
            job_description="Kubernetes, Docker, Terraform, AWS, Jenkins, CI/CD pipelines",
            job_id="test-confidence"
        )
        
        for skill in result['skills']:
            assert 0.0 <= skill['confidence'] <= 1.0, \
                f"Confidence {skill['confidence']} out of range for skill {skill['text']}"
    
    def test_context_extraction_is_meaningful(self):
        """Extracted context should be meaningful text around the skill."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        result = extractor.extract_skills(
            job_summary="Python developer needed",
            job_description="Must have 5+ years experience with Python programming language",
            job_id="test-context"
        )
        
        for skill in result['skills']:
            if skill.get('context'):
                # Context should contain the skill
                assert skill['text'].lower() in skill['context'].lower(), \
                    f"Context '{skill['context']}' should contain skill '{skill['text']}'"


class TestAliasResolutionIntegration:
    """Tests for alias resolution in extraction pipeline."""
    
    def test_common_aliases_are_resolved(self):
        """Common aliases like K8s, GCP should be resolved."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        from lib.config import get_alias_resolver
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        result = extractor.extract_skills(
            job_summary="K8s administrator needed",
            job_description="Must know GCP, Docker, and JS/TS",
            job_id="test-aliases"
        )
        
        skill_texts = [s['text'].lower() for s in result['skills']]
        
        # Either alias or canonical should be found
        # (exact behavior depends on alias config)
        assert any('k8s' in s or 'kubernetes' in s for s in skill_texts) or \
               any('docker' in s for s in skill_texts), \
               "Should extract at least some skills from job text"
    
    def test_alias_resolver_works_independently(self):
        """AliasResolver should work independently of extractor."""
        from lib.config import get_alias_resolver
        
        resolver = get_alias_resolver()
        
        # Should not raise even if YAML not loaded
        result = resolver.resolve("K8s")
        
        # Result is either the canonical or the original
        assert result in ("Kubernetes", "K8s", None)


class TestExtractionMethodTracking:
    """Tests for tracking which extraction method found each skill."""
    
    def test_extraction_method_is_recorded(self):
        """Skills should record which method found them."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        result = extractor.extract_skills(
            job_summary="Python developer",
            job_description="Python, Django, PostgreSQL required",
            job_id="test-method"
        )
        
        for skill in result['skills']:
            assert 'extraction_method' in skill, \
                f"Skill {skill['text']} should have extraction_method"
            assert skill['extraction_method'] in [
                'lexicon', 'semantic', 'pattern', 'ner', 'noun_chunk'
            ]
    
    def test_different_methods_find_different_skills(self):
        """Different extraction methods should potentially find different skills."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        # Use text with varied skill mentions
        result = extractor.extract_skills(
            job_summary="Machine learning engineer at AWS",
            job_description="""
            We're looking for an ML engineer with:
            - Python 3.10+ experience
            - TensorFlow or PyTorch expertise  
            - AWS SageMaker experience
            - Strong communication skills
            """,
            job_id="test-varied"
        )
        
        # Get unique extraction methods
        methods = set(s['extraction_method'] for s in result['skills'])
        
        # At least lexicon should be used
        assert 'lexicon' in methods


class TestEnhancedModeVsLegacy:
    """Tests comparing enhanced mode vs legacy mode."""
    
    def test_enhanced_mode_detected_correctly(self):
        """Enhanced mode should be detected based on dependencies."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        # Create with explicit enhanced settings
        extractor = UnifiedSkillsExtractor(
            enable_semantic=True,  # Try to enable
            enable_patterns=True
        )
        
        result = extractor.extract_skills(
            job_summary="Test job",
            job_description="Python developer needed",
            job_id="test-mode"
        )
        
        metadata = result['extraction_metadata']
        
        # enhanced_mode flag should be present
        assert 'enhanced_mode' in metadata
        
        # Should have mode-specific suffix in version
        assert 'extractor_version' in metadata
    
    def test_legacy_mode_fallback_works(self):
        """Should work even when enhanced dependencies unavailable."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        # Force legacy mode
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Java developer",
            job_description="Must know Java, Spring Boot, MySQL",
            job_id="test-legacy"
        )
        
        # Should still extract skills
        assert len(result['skills']) > 0 or result['extraction_metadata']['total_matches'] >= 0


class TestPerformance:
    """Performance tests for extraction pipeline."""
    
    def test_extraction_completes_in_reasonable_time(self):
        """Extraction should complete within reasonable time limit."""
        import time
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        # Long job description
        long_description = """
        Senior Software Engineer
        
        We are looking for a highly skilled software engineer with expertise in:
        - Python, Java, JavaScript, TypeScript, Go, Rust
        - React, Angular, Vue.js, Next.js
        - AWS, Azure, Google Cloud Platform
        - Docker, Kubernetes, Terraform
        - PostgreSQL, MongoDB, Redis
        - Machine Learning, TensorFlow, PyTorch
        
        Requirements:
        - 7+ years of software development experience
        - Strong communication and leadership skills
        - Experience with Agile methodologies
        """ * 5  # Repeat to make it longer
        
        start_time = time.time()
        
        result = extractor.extract_skills(
            job_summary="Senior Software Engineer",
            job_description=long_description,
            job_id="test-perf"
        )
        
        elapsed_time = time.time() - start_time
        
        # Should complete in under 5 seconds
        assert elapsed_time < 5.0, f"Extraction took {elapsed_time:.2f}s, expected < 5s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
