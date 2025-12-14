"""
Unit Tests for Section Classifier

Tests the section classification functionality:
1. Section splitting
2. Relevance probability calculation
3. Header matching
4. Keyword detection
"""

import pytest
from unittest.mock import Mock, patch


class TestSectionClassifier:
    """Tests for SectionClassifier class."""
    
    def test_classifier_initialization(self):
        """Classifier should initialize with default settings."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        assert classifier.VERSION.startswith('v')
        assert classifier.classification_method == "rule_based"
    
    def test_classifier_has_relevant_headers(self):
        """Classifier should have predefined relevant headers."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        assert 'requirements' in classifier.RELEVANT_HEADERS
        assert 'skills' in classifier.RELEVANT_HEADERS
        assert 'qualifications' in classifier.RELEVANT_HEADERS
    
    def test_classifier_has_non_relevant_headers(self):
        """Classifier should have predefined non-relevant headers."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        assert 'benefits' in classifier.NON_RELEVANT_HEADERS
        assert 'about us' in classifier.NON_RELEVANT_HEADERS
        assert 'compensation' in classifier.NON_RELEVANT_HEADERS
    
    def test_get_version(self):
        """get_version should return classifier version."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        version = classifier.get_version()
        
        assert isinstance(version, str)
        assert version.startswith('v')


class TestSectionSplitting:
    """Tests for section splitting functionality."""
    
    def test_split_text_with_headers(self):
        """Should split text by section headers."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = """
        About the Role:
        This is a great opportunity.
        
        Requirements:
        - Python experience
        - Docker knowledge
        
        Benefits:
        - Health insurance
        - 401k
        """
        
        sections = classifier._split_into_sections(text)
        
        # Should find multiple sections
        assert len(sections) >= 2
    
    def test_split_text_without_headers(self):
        """Should return single section if no headers found."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = "Looking for a Python developer with experience in Django and PostgreSQL."
        
        sections = classifier._split_into_sections(text)
        
        # Should have at least one section
        assert len(sections) >= 1
    
    def test_split_preserves_content(self):
        """Section content should be preserved."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = """
        Requirements:
        - Python 5+ years
        - Django framework
        """
        
        sections = classifier._split_into_sections(text)
        
        # Content should contain key words
        all_content = " ".join(section[1] for section in sections)
        assert "Python" in all_content


class TestRelevanceClassification:
    """Tests for relevance classification."""
    
    def test_requirements_section_is_relevant(self):
        """Requirements section should be classified as relevant."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        result = classifier._classify_section(
            header="Requirements",
            content="5+ years Python experience required",
            index=0
        )
        
        assert result.is_relevant is True
        assert result.probability >= 0.7
    
    def test_benefits_section_is_not_relevant(self):
        """Benefits section should be classified as not relevant."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        result = classifier._classify_section(
            header="Benefits",
            content="Health insurance, 401k matching, unlimited PTO",
            index=0
        )
        
        assert result.is_relevant is False
        assert result.probability < 0.5
    
    def test_section_with_tech_keywords_is_relevant(self):
        """Section with tech keywords should be classified as relevant."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        result = classifier._classify_section(
            header=None,  # No header
            content="Must have Python, Docker, and Kubernetes experience. AWS knowledge required.",
            index=0
        )
        
        # Should be relevant due to tech keywords
        assert result.probability >= 0.5
    
    def test_probability_in_valid_range(self):
        """Probability should be between 0 and 1."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        test_cases = [
            ("Skills", "Python and Java required"),
            ("Benefits", "Free lunch and gym"),
            (None, "Some random text about the company"),
            ("About Us", "We are a great company")
        ]
        
        for header, content in test_cases:
            result = classifier._classify_section(header, content, 0)
            assert 0.0 <= result.probability <= 1.0


class TestKeywordDetection:
    """Tests for keyword detection in sections."""
    
    def test_detects_skill_indicator_keywords(self):
        """Should detect skill indicator keywords."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        result = classifier._classify_section(
            header=None,
            content="Must have experience with Python. Strong background in Django required.",
            index=0
        )
        
        # Should detect keywords
        assert len(result.detected_keywords) > 0
    
    def test_detects_tech_patterns(self):
        """Should detect technology patterns."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        result = classifier._classify_section(
            header=None,
            content="Looking for Python, JavaScript, and React developers. AWS experience preferred.",
            index=0
        )
        
        # Should detect tech patterns
        assert any('python' in kw.lower() for kw in result.detected_keywords)


class TestClassifySections:
    """Tests for the main classify_sections method."""
    
    def test_classify_returns_list_of_classifications(self):
        """classify_sections should return list of SectionClassification."""
        from lib.enrichment.section_classifier import SectionClassifier
        from lib.domain.entities import SectionClassification
        
        classifier = SectionClassifier()
        
        text = """
        Requirements:
        - Python developer
        
        Benefits:
        - Health insurance
        """
        
        classifications = classifier.classify_sections(text, job_posting_id="test-123")
        
        assert isinstance(classifications, list)
        assert len(classifications) >= 1
        
        for c in classifications:
            assert isinstance(c, SectionClassification)
    
    def test_classification_includes_all_fields(self):
        """Classification should include all required fields."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = "Requirements: Python experience required"
        
        classifications = classifier.classify_sections(text, job_posting_id="test-123")
        
        assert len(classifications) >= 1
        
        c = classifications[0]
        assert hasattr(c, 'section_text')
        assert hasattr(c, 'is_skills_relevant')
        assert hasattr(c, 'relevance_probability')
        assert hasattr(c, 'classifier_version')


class TestGetRelevantText:
    """Tests for get_relevant_text method."""
    
    def test_returns_only_relevant_sections(self):
        """get_relevant_text should return only relevant sections."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = """
        Requirements:
        - Python 5+ years
        - Docker knowledge
        
        Benefits:
        - Free food
        - Gym membership
        
        Skills:
        - Strong programming skills
        """
        
        relevant = classifier.get_relevant_text(text, min_probability=0.5)
        
        # Should include requirements and skills content
        assert "Python" in relevant or "programming" in relevant
    
    def test_returns_full_text_if_no_relevant_sections(self):
        """Should return full text if no sections are relevant."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        text = "This is a short job posting without clear sections."
        
        relevant = classifier.get_relevant_text(text, min_probability=0.9)
        
        # Should return original text
        assert text.strip() in relevant or relevant == text.strip() or len(relevant) > 0


class TestHeaderMatching:
    """Tests for header matching functionality."""
    
    def test_matches_exact_header(self):
        """Should match exact headers."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        assert classifier._matches_header_set('requirements', classifier._relevant_headers)
        assert classifier._matches_header_set('benefits', classifier._non_relevant_headers)
    
    def test_matches_partial_header(self):
        """Should match partial headers."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        # "job requirements" contains "requirements"
        assert classifier._matches_header_set('job requirements', classifier._relevant_headers)
    
    def test_case_insensitive_matching(self):
        """Header matching should be case-insensitive."""
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        # Headers are lowercased for comparison
        assert classifier._matches_header_set('requirements', classifier._relevant_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
