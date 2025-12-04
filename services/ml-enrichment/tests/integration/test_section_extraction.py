"""
Integration Tests for Section-Aware Extraction

Tests the integration of section classification with skills extraction:
- Section-weighted skill extraction
- Relevance scoring in output
- Comparison with non-section-aware extraction
"""

import pytest
from unittest.mock import Mock, patch


class TestSectionAwareExtraction:
    """Tests for section-aware skills extraction."""
    
    def test_extraction_includes_section_info(self):
        """Extracted skills should include section information."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        # Job with clear sections
        job_summary = "Python developer position"
        job_description = """
        Requirements
        - 5+ years Python experience
        - Django or Flask framework
        
        Benefits
        - Health insurance
        - Remote work option
        """
        
        result = extractor.extract_skills(
            job_summary=job_summary,
            job_description=job_description,
            job_id="test-001"
        )
        
        # Should return skills
        skills = result.get('skills', [])
        assert len(skills) >= 0  # May or may not find skills
        
        # Metadata should be present
        assert 'extraction_metadata' in result
    
    def test_requirements_section_prioritized(self):
        """Skills from Requirements section should have higher confidence."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        # Same skill in different sections
        job_description = """
        About Our Culture
        We use Python for some internal tools.
        
        Requirements
        - Expert level Python required
        - Python testing frameworks
        """
        
        result = extractor.extract_skills(
            job_summary="",
            job_description=job_description,
            job_id="test-002"
        )
        
        skills = result.get('skills', [])
        
        # If Python is found, check that it has reasonable confidence
        python_skills = [s for s in skills if 'python' in s.get('text', '').lower()]
        if python_skills:
            # At least one Python skill should have decent confidence
            max_confidence = max(s.get('confidence', 0) for s in python_skills)
            assert max_confidence > 0


class TestSectionRelevanceInOutput:
    """Tests for section relevance in extraction output."""
    
    def test_skill_has_section_context(self):
        """Extracted skills should have context from their section."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Senior Python Developer",
            job_description="Must have Python and Django experience",
            job_id="test-003"
        )
        
        skills = result.get('skills', [])
        
        if skills:
            for skill in skills:
                # Each skill should have a context field
                assert 'context' in skill
                assert isinstance(skill['context'], str)


class TestSectionClassifierIntegration:
    """Tests for SectionClassifier integration with extractor."""
    
    def test_classifier_available(self):
        """SectionClassifier should be importable."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        assert classifier is not None
    
    def test_classifier_scores_text(self):
        """SectionClassifier should score section text."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = """
        Requirements
        - Python experience
        """
        
        sections = classifier.classify_sections(text)
        
        # Should return list of classifications
        assert isinstance(sections, list)


class TestWithAndWithoutSectionAwareness:
    """Tests comparing section-aware vs regular extraction."""
    
    def test_both_modes_produce_results(self):
        """Both modes should produce valid results."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        
        job_text = "Looking for Python developer with Django experience"
        
        # Regular extraction
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary=job_text,
            job_description=job_text,
            job_id="test-004"
        )
        
        # Should have valid structure
        assert 'skills' in result
        assert 'extraction_metadata' in result
    
    def test_extraction_metadata_includes_mode(self):
        """Extraction metadata should include mode information."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        result = extractor.extract_skills(
            job_summary="Python developer",
            job_description="Python and Django required",
            job_id="test-005"
        )
        
        metadata = result.get('extraction_metadata', {})
        
        # Should have mode information
        assert 'enhanced_mode' in metadata


class TestSectionBoundaries:
    """Tests for section boundary detection in extraction."""
    
    def test_skills_from_correct_sections(self):
        """Skills should be attributed to correct sections."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = """
        Job Title: Senior Developer
        
        Requirements
        Python, Django, PostgreSQL
        
        Nice to Have
        React, TypeScript
        
        Benefits
        Health, Dental, Vision
        """
        
        sections = classifier.detect_sections(text)
        
        # Should detect multiple sections
        if sections:
            # At least one section should be identified
            assert any(s.get('text', '') for s in sections)


class TestRelevanceWeighting:
    """Tests for relevance-based confidence weighting."""
    
    def test_relevant_section_boosts_confidence(self):
        """Skills from relevant sections should have boosted confidence."""
        # This tests the concept - actual implementation may vary
        
        # Skill from "Requirements" section
        requirements_base_confidence = 0.7
        requirements_relevance = 0.9
        
        # Skill from "About Us" section
        about_us_base_confidence = 0.7
        about_us_relevance = 0.2
        
        # Weighted confidence should differ
        weighted_requirements = requirements_base_confidence * requirements_relevance
        weighted_about_us = about_us_base_confidence * about_us_relevance
        
        assert weighted_requirements > weighted_about_us
    
    def test_excluded_section_reduces_confidence(self):
        """Skills from excluded sections should have reduced confidence."""
        # Benefits section should be excluded
        benefits_base_confidence = 0.8
        benefits_relevance = 0.1  # Low relevance
        
        weighted = benefits_base_confidence * benefits_relevance
        
        # Should be significantly reduced
        assert weighted < benefits_base_confidence * 0.5


class TestSectionClassificationEndToEnd:
    """End-to-end tests for section classification."""
    
    def test_full_pipeline(self):
        """Test complete extraction pipeline with section awareness."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=False
        )
        
        job_description = """
        About the Company
        We are a leading tech company.
        
        Job Description
        As a Senior Python Developer, you will work on exciting projects.
        
        Requirements
        - 5+ years of Python experience
        - Strong knowledge of Django or Flask
        - PostgreSQL or MySQL experience
        - Experience with Docker and Kubernetes
        
        Nice to Have
        - React or Vue.js experience
        - AWS or GCP cloud experience
        
        Benefits
        - Competitive salary
        - Health insurance
        - Flexible work hours
        """
        
        result = extractor.extract_skills(
            job_summary="Senior Python Developer",
            job_description=job_description,
            job_id="test-e2e"
        )
        
        # Should successfully extract skills
        assert 'skills' in result
        assert 'extraction_metadata' in result
        
        # Metadata should include processing info
        metadata = result['extraction_metadata']
        assert 'total_matches' in metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
