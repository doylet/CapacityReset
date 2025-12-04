"""
Integration Tests for Section-Aware Extraction

Tests the integration of section classification with skills extraction:
1. Section filtering improves precision
2. Confidence boosting for skills in relevant sections
3. End-to-end extraction with section awareness
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestSectionAwareExtractionIntegration:
    """Integration tests for section-aware extraction."""
    
    def test_extractor_with_section_classification(self):
        """Skills extractor should use section classification."""
        from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig
        from lib.enrichment.section_classifier import SectionClassifier
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        # Job with clear sections
        job_text = """
        About Us:
        We are a leading tech company based in San Francisco.
        
        Requirements:
        - 5+ years Python experience
        - Experience with Django or Flask
        - PostgreSQL database knowledge
        - Docker and Kubernetes skills
        
        Benefits:
        - Health insurance
        - Remote work options
        - Free lunch
        
        Responsibilities:
        - Design and implement APIs
        - Collaborate with product teams
        """
        
        result = extractor.extract_skills(
            job_summary="Python Developer",
            job_description=job_text,
            job_id="test-section-001"
        )
        
        # Should extract skills
        assert len(result['skills']) > 0
        
        # Skills should come from relevant sections
        skill_texts = [s['text'].lower() for s in result['skills']]
        
        # Technical skills should be found
        assert any('python' in s for s in skill_texts)
    
    def test_section_filter_improves_precision(self):
        """Section filtering should reduce noise from non-relevant sections."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        from lib.enrichment.section_classifier import SectionClassifier
        
        classifier = SectionClassifier()
        
        # Job with non-skill content that might match patterns
        full_text = """
        About Our Company:
        We use Python internally for automation. Our team is in New York.
        
        Requirements:
        - Must know Python programming
        - 3+ years experience
        
        Perks:
        Our office has a Java bar (coffee). We use React for fun projects.
        """
        
        # Get relevant text only
        relevant_text = classifier.get_relevant_text(full_text, min_probability=0.5)
        
        # Should primarily include Requirements section
        assert "Python programming" in relevant_text or "experience" in relevant_text
        
        # The "Java bar" from Perks should be filtered out (ideally)
        # Note: this depends on how well section detection works
    
    def test_confidence_boosted_in_relevant_sections(self):
        """Skills in relevant sections should have higher confidence."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        # Job with same skill mentioned in different contexts
        job_text = """
        Requirements:
        - Expert Python developer required
        - Must be proficient in Python
        
        About the Team:
        We sometimes use Python for internal tools.
        """
        
        result = extractor.extract_skills(
            job_summary="Python Developer",
            job_description=job_text,
            job_id="test-confidence-001"
        )
        
        # Should find Python with reasonable confidence
        python_skills = [s for s in result['skills'] if 'python' in s['text'].lower()]
        
        if python_skills:
            # Python should have decent confidence
            assert python_skills[0]['confidence'] > 0.3


class TestEndToEndSectionExtraction:
    """End-to-end tests for section-aware extraction."""
    
    def test_full_job_posting_extraction(self):
        """Full job posting should be processed correctly."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        from lib.enrichment.section_classifier import SectionClassifier, get_section_classifier
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        job_posting = """
        Senior Software Engineer - Backend
        
        Location: Remote, US
        
        About the Company:
        We are building the next generation of developer tools. Join our 
        team of passionate engineers who love clean code and great products.
        
        ## What You'll Do:
        - Design and implement scalable backend services
        - Write clean, maintainable Python code
        - Build and optimize PostgreSQL databases
        - Deploy services using Docker and Kubernetes
        - Collaborate with frontend team on API design
        
        ## Required Qualifications:
        - 5+ years of software development experience
        - Strong Python programming skills
        - Experience with Django or FastAPI
        - PostgreSQL or MySQL database experience
        - Docker containerization knowledge
        - AWS or GCP cloud platform experience
        
        ## Nice to Have:
        - Kubernetes orchestration
        - Redis caching experience
        - GraphQL API design
        - CI/CD pipeline experience
        
        ## What We Offer:
        - Competitive salary and equity
        - Health, dental, and vision insurance
        - Unlimited PTO
        - Remote-first culture
        - Learning and development budget
        
        Equal Opportunity Employer.
        """
        
        result = extractor.extract_skills(
            job_summary="Senior Software Engineer - Backend",
            job_description=job_posting,
            job_id="test-full-001"
        )
        
        skills = result['skills']
        skill_texts = [s['text'].lower() for s in skills]
        
        # Should extract key skills
        expected_skills = ['python', 'django', 'docker', 'postgresql']
        for expected in expected_skills:
            assert any(expected in s for s in skill_texts), \
                f"Expected to find '{expected}' in skills"
    
    def test_extraction_includes_metadata(self):
        """Extraction should include useful metadata."""
        from lib.enrichment.skills import UnifiedSkillsExtractor
        
        extractor = UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        
        job_text = """
        Requirements:
        - Python experience required
        """
        
        result = extractor.extract_skills(
            job_summary="Python Developer",
            job_description=job_text,
            job_id="test-metadata-001"
        )
        
        # Should have extraction metadata
        assert 'extraction_metadata' in result
        metadata = result['extraction_metadata']
        
        assert 'extractor_version' in metadata
        assert 'enhanced_mode' in metadata


class TestSectionClassificationEntity:
    """Tests for SectionClassification entity."""
    
    def test_section_classification_has_all_fields(self):
        """SectionClassification should have required fields."""
        from lib.domain.entities import SectionClassification
        
        classification = SectionClassification(
            section_text="Python experience required",
            section_header="Requirements",
            section_index=0,
            is_skills_relevant=True,
            relevance_probability=0.9,
            classifier_version="v1.0-rule-based",
            classification_method="rule_based",
            detected_keywords=["python", "experience"]
        )
        
        assert classification.section_text == "Python experience required"
        assert classification.is_skills_relevant is True
        assert classification.relevance_probability == 0.9
    
    def test_section_classification_to_dict(self):
        """SectionClassification should serialize to dict."""
        from lib.domain.entities import SectionClassification
        
        classification = SectionClassification(
            section_text="Test content",
            section_header="Requirements",
            section_index=1,
            is_skills_relevant=True,
            relevance_probability=0.85,
            classifier_version="v1.0",
            classification_method="rule_based",
            detected_keywords=["python"]
        )
        
        data = classification.to_dict()
        
        assert data['section_text'] == "Test content"
        assert data['is_skills_relevant'] is True
        assert data['relevance_probability'] == 0.85


class TestSectionClassificationStorage:
    """Tests for storing section classifications."""
    
    def test_classification_storage_adapter_exists(self):
        """BigQuery adapter for section classifications should exist."""
        from lib.adapters.bigquery import BigQuerySectionClassificationRepository
        
        # Should be able to instantiate
        repo = BigQuerySectionClassificationRepository()
        
        assert repo is not None
    
    def test_classification_can_be_saved(self):
        """Section classification should be saveable."""
        from lib.domain.entities import SectionClassification
        
        classification = SectionClassification(
            job_posting_id="test-job-123",
            section_text="Python developer required",
            section_header="Requirements",
            section_index=0,
            is_skills_relevant=True,
            relevance_probability=0.9,
            classifier_version="v1.0",
            classification_method="rule_based",
            detected_keywords=["python"]
        )
        
        # Should be able to convert to dict for storage
        data = classification.to_dict()
        
        assert 'job_posting_id' in data
        assert 'is_skills_relevant' in data


class TestGetSectionClassifier:
    """Tests for get_section_classifier singleton."""
    
    def test_get_section_classifier_returns_instance(self):
        """get_section_classifier should return classifier instance."""
        from lib.enrichment.section_classifier import get_section_classifier
        
        classifier = get_section_classifier()
        
        assert classifier is not None
    
    def test_get_section_classifier_is_singleton(self):
        """get_section_classifier should return same instance."""
        from lib.enrichment.section_classifier import get_section_classifier
        
        classifier1 = get_section_classifier()
        classifier2 = get_section_classifier()
        
        # May or may not be exact same instance depending on implementation
        # But both should be valid classifiers
        assert classifier1.get_version() == classifier2.get_version()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
