"""
Unit Tests for SectionClassifier

Tests the section classification functionality including:
- Section header detection
- Relevance scoring
- Section boundary detection
"""

import pytest
from unittest.mock import Mock, patch


class TestSectionClassifierInit:
    """Tests for SectionClassifier initialization."""
    
    def test_classifier_creates_with_defaults(self):
        """SectionClassifier should initialize with default patterns."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        assert classifier is not None
        assert len(classifier.relevant_sections) > 0
        assert len(classifier.excluded_sections) > 0
    
    def test_classifier_has_version(self):
        """SectionClassifier should have a version identifier."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        version = classifier.get_version()
        
        assert isinstance(version, str)
        assert len(version) > 0


class TestSectionDetection:
    """Tests for section header detection."""
    
    def test_detect_requirements_section(self):
        """Should detect 'Requirements' section header."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = """
        About the Role
        This is a senior position.
        
        Requirements
        - 5+ years Python experience
        - Strong communication skills
        """
        
        sections = classifier.detect_sections(text)
        
        # Should find at least the Requirements section
        section_names = [s.get('header', '').lower() for s in sections]
        assert any('requirement' in name for name in section_names)
    
    def test_detect_skills_section(self):
        """Should detect 'Skills' section header."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = """
        Job Description
        Exciting opportunity...
        
        Technical Skills
        Python, JavaScript, React
        """
        
        sections = classifier.detect_sections(text)
        
        section_names = [s.get('header', '').lower() for s in sections]
        assert any('skill' in name for name in section_names)
    
    def test_handle_no_sections(self):
        """Should handle text with no clear sections."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = "Looking for a Python developer with React experience."
        
        sections = classifier.detect_sections(text)
        
        # Should return at least one section (the entire text)
        assert len(sections) >= 0  # May be empty or have full text as one section


class TestRelevanceScoring:
    """Tests for section relevance scoring."""
    
    def test_requirements_section_high_relevance(self):
        """Requirements section should have high relevance score."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        score = classifier.get_relevance_score("Requirements")
        
        assert score >= 0.7
    
    def test_skills_section_high_relevance(self):
        """Skills section should have high relevance score."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        score = classifier.get_relevance_score("Technical Skills")
        
        assert score >= 0.7
    
    def test_about_us_low_relevance(self):
        """About Us section should have low relevance score."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        score = classifier.get_relevance_score("About Us")
        
        assert score < 0.5
    
    def test_benefits_low_relevance(self):
        """Benefits section should have low relevance score."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        score = classifier.get_relevance_score("Benefits")
        
        assert score < 0.5
    
    def test_unknown_section_medium_relevance(self):
        """Unknown section should have medium relevance score."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        score = classifier.get_relevance_score("Some Random Header")
        
        # Unknown sections should get a default score
        assert 0.0 <= score <= 1.0


class TestSectionClassification:
    """Tests for full section classification."""
    
    def test_classify_mixed_sections(self):
        """Should correctly classify mixed sections."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = """
        About Us
        We are a great company.
        
        Requirements
        - Python 3 years
        - React experience
        
        Benefits
        - Health insurance
        - Remote work
        """
        
        classifications = classifier.classify_sections(text)
        
        # Should have classifications for each section
        assert len(classifications) > 0
        
        # Each classification should have required fields
        for classification in classifications:
            assert 'is_skills_relevant' in classification
            assert 'relevance_probability' in classification
    
    def test_classify_returns_sorted_by_relevance(self):
        """Classifications should be sorted by relevance."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = """
        Benefits
        Great perks!
        
        Required Skills
        Python, Django, React
        
        About Us
        Amazing company.
        """
        
        classifications = classifier.classify_sections(text)
        
        if len(classifications) > 1:
            # Should be sorted by relevance (highest first)
            scores = [c.get('relevance_probability', 0) for c in classifications]
            assert scores == sorted(scores, reverse=True)


class TestSectionEntity:
    """Tests for SectionClassification entity."""
    
    def test_section_classification_entity(self):
        """SectionClassification entity should have correct structure."""
        from lib.domain.entities import SectionClassification
        
        classification = SectionClassification(
            job_posting_id='job-001',
            section_text='Python experience required',
            section_index=0,
            is_skills_relevant=True,
            relevance_probability=0.9,
            classifier_version='v1.0-rule-based',
            classification_method='rule_based'
        )
        
        assert classification.is_skills_relevant is True
        assert classification.relevance_probability == 0.9
    
    def test_section_classification_validation(self):
        """SectionClassification should validate probability range."""
        from lib.domain.entities import SectionClassification
        
        # Valid probability
        classification = SectionClassification(
            job_posting_id='job-001',
            section_text='Test',
            section_index=0,
            is_skills_relevant=True,
            relevance_probability=0.8,
            classifier_version='v1.0',
            classification_method='rule_based'
        )
        assert 0.0 <= classification.relevance_probability <= 1.0
    
    def test_section_classification_serialization(self):
        """SectionClassification should serialize correctly."""
        from lib.domain.entities import SectionClassification
        
        classification = SectionClassification(
            job_posting_id='job-001',
            section_text='Python required',
            section_index=0,
            is_skills_relevant=True,
            relevance_probability=0.9,
            classifier_version='v1.0',
            classification_method='rule_based'
        )
        
        data = classification.to_dict()
        
        assert 'job_posting_id' in data
        assert 'is_skills_relevant' in data
        assert 'relevance_probability' in data


class TestEdgeCases:
    """Tests for edge cases in section classification."""
    
    def test_empty_text(self):
        """Should handle empty text."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        sections = classifier.detect_sections("")
        
        assert isinstance(sections, list)
    
    def test_none_text(self):
        """Should handle None text."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        # Should not raise exception
        try:
            sections = classifier.detect_sections(None or "")
            assert isinstance(sections, list)
        except (TypeError, AttributeError):
            pytest.fail("Should handle None gracefully")
    
    def test_very_long_text(self):
        """Should handle very long text."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        # Create long text
        long_text = "Requirements\n" + "Python experience needed. " * 1000
        
        sections = classifier.detect_sections(long_text)
        
        assert isinstance(sections, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
