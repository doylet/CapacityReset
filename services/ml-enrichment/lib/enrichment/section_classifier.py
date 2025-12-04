"""
Section Classifier Module

Classifies job posting sections for skills relevance.
Uses rule-based classification with support for future ML enhancement.
"""

import logging
import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

from ..domain.entities import SectionClassification

logger = logging.getLogger(__name__)


@dataclass
class ClassifiedSection:
    """Result of section classification."""
    text: str
    header: Optional[str]
    index: int
    is_relevant: bool
    probability: float
    detected_keywords: List[str]


class SectionClassifier:
    """
    Classifies job posting sections for skills relevance.
    
    Uses rule-based classification based on:
    - Section headers (if present)
    - Keyword indicators
    - Section position and structure
    """
    
    VERSION = "v1.0-rule-based"
    
    # Section headers that strongly indicate skills relevance
    RELEVANT_HEADERS = {
        'requirements', 'qualifications', 'skills', 'technical requirements',
        'required qualifications', 'preferred qualifications', 'must have',
        'required skills', 'technical skills', 'what you need',
        'what we are looking for', 'what you will need', 'key requirements',
        'minimum requirements', 'job requirements', 'experience needed',
        'experience required', 'essential skills', 'desired skills',
        'core competencies', 'you will need', 'ideal candidate'
    }
    
    # Section headers that indicate non-relevance
    NON_RELEVANT_HEADERS = {
        'benefits', 'compensation', 'salary', 'perks', 'about us',
        'company culture', 'our mission', 'equal opportunity', 'diversity',
        'how to apply', 'application process', 'contact', 'location',
        'about the company', 'our values', 'why join us', 'work environment',
        'what we offer', 'our benefits', 'eeo statement', 'legal'
    }
    
    # Keywords that indicate skills relevance
    SKILL_INDICATOR_KEYWORDS = {
        'experience with', 'proficient in', 'knowledge of', 'expertise in',
        'skilled in', 'familiar with', 'understanding of', 'ability to',
        'strong background', 'hands-on experience', 'proven track record',
        'years of experience', 'proficiency in', 'competency in',
        'working knowledge', 'deep understanding', 'technical expertise'
    }
    
    # Technology patterns that indicate skills sections
    TECH_PATTERNS = [
        r'\b(?:python|java|javascript|typescript|c\+\+|c#|go|rust|ruby|php|scala|kotlin)\b',
        r'\b(?:aws|azure|gcp|docker|kubernetes|terraform|jenkins)\b',
        r'\b(?:react|vue|angular|node\.?js|django|flask|spring)\b',
        r'\b(?:sql|nosql|postgresql|mysql|mongodb|redis)\b',
        r'\b(?:machine learning|deep learning|ai|ml|data science)\b'
    ]
    
    def __init__(self):
        """Initialize the section classifier."""
        self.classification_method = "rule_based"
        
        # Compile regex patterns
        self._tech_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.TECH_PATTERNS
        ]
        
        # Normalize header sets for comparison
        self._relevant_headers = {h.lower() for h in self.RELEVANT_HEADERS}
        self._non_relevant_headers = {h.lower() for h in self.NON_RELEVANT_HEADERS}
    
    def get_version(self) -> str:
        """Get classifier version."""
        return self.VERSION
    
    def classify_sections(
        self,
        text: str,
        job_posting_id: Optional[str] = None
    ) -> List[SectionClassification]:
        """
        Classify all sections in a job posting.
        
        Args:
            text: Full job posting text
            job_posting_id: Optional job posting ID
            
        Returns:
            List of SectionClassification for each section
        """
        # Split into sections
        sections = self._split_into_sections(text)
        
        classifications = []
        for idx, (header, content) in enumerate(sections):
            result = self._classify_section(header, content, idx)
            
            classification = SectionClassification(
                job_posting_id=job_posting_id,
                section_text=content,
                section_header=header,
                section_index=idx,
                is_skills_relevant=result.is_relevant,
                relevance_probability=result.probability,
                classifier_version=self.VERSION,
                classification_method=self.classification_method,
                detected_keywords=result.detected_keywords
            )
            
            classifications.append(classification)
        
        return classifications
    
    def get_relevant_text(
        self,
        text: str,
        min_probability: float = 0.5
    ) -> str:
        """
        Extract only skills-relevant sections from text.
        
        Args:
            text: Full job posting text
            min_probability: Minimum relevance probability
            
        Returns:
            Concatenated relevant sections
        """
        classifications = self.classify_sections(text)
        
        relevant_sections = [
            c.section_text for c in classifications
            if c.is_skills_relevant and c.relevance_probability >= min_probability
        ]
        
        return "\n\n".join(relevant_sections) if relevant_sections else text
    
    def _split_into_sections(self, text: str) -> List[Tuple[Optional[str], str]]:
        """
        Split text into sections based on headers and structure.
        
        Returns:
            List of (header, content) tuples
        """
        sections = []
        
        # Try to split by common section patterns
        # Look for patterns like "Requirements:", "## Skills", etc.
        section_pattern = re.compile(
            r'^(?:#+\s*)?([A-Z][A-Za-z\s&-]+?)(?:[:.\n])',
            re.MULTILINE
        )
        
        matches = list(section_pattern.finditer(text))
        
        if not matches:
            # No clear sections, treat as single section
            return [(None, text.strip())]
        
        for i, match in enumerate(matches):
            header = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            
            if content:  # Only include non-empty sections
                sections.append((header, content))
        
        # Add any text before the first header
        if matches and matches[0].start() > 0:
            pre_content = text[:matches[0].start()].strip()
            if pre_content:
                sections.insert(0, (None, pre_content))
        
        return sections if sections else [(None, text.strip())]
    
    def _classify_section(
        self,
        header: Optional[str],
        content: str,
        index: int
    ) -> ClassifiedSection:
        """
        Classify a single section.
        
        Args:
            header: Section header if available
            content: Section content
            index: Section index in document
            
        Returns:
            ClassifiedSection result
        """
        detected_keywords = []
        scores = []
        
        # Score based on header
        if header:
            header_lower = header.lower()
            
            if self._matches_header_set(header_lower, self._relevant_headers):
                scores.append(0.9)
                detected_keywords.append(f"header:{header}")
            elif self._matches_header_set(header_lower, self._non_relevant_headers):
                scores.append(0.1)
            else:
                scores.append(0.5)  # Neutral
        
        # Score based on skill indicator keywords
        content_lower = content.lower()
        keyword_count = 0
        for keyword in self.SKILL_INDICATOR_KEYWORDS:
            if keyword in content_lower:
                keyword_count += 1
                detected_keywords.append(keyword)
        
        if keyword_count > 0:
            scores.append(min(0.5 + keyword_count * 0.1, 0.9))
        
        # Score based on technology patterns
        tech_matches = []
        for pattern in self._tech_patterns:
            matches = pattern.findall(content)
            tech_matches.extend(matches)
        
        if tech_matches:
            # More tech terms = higher likelihood of skills section
            tech_score = min(0.5 + len(tech_matches) * 0.05, 0.95)
            scores.append(tech_score)
            detected_keywords.extend(list(set(m.lower() for m in tech_matches))[:5])
        
        # Score based on section structure
        # Bullet points often indicate requirements/skills
        bullet_count = len(re.findall(r'^[\s]*[-•*]\s', content, re.MULTILINE))
        if bullet_count > 2:
            scores.append(0.7)
        
        # Calculate final probability
        if scores:
            probability = sum(scores) / len(scores)
        else:
            probability = 0.5
        
        is_relevant = probability >= 0.5
        
        return ClassifiedSection(
            text=content,
            header=header,
            index=index,
            is_relevant=is_relevant,
            probability=probability,
            detected_keywords=detected_keywords
        )
    
    def _matches_header_set(self, header: str, header_set: Set[str]) -> bool:
        """Check if header matches any in the set (partial matching)."""
        for h in header_set:
            if h in header or header in h:
                return True
        return False


def get_section_classifier() -> SectionClassifier:
    """Get singleton section classifier instance."""
    global _classifier_instance
    if '_classifier_instance' not in globals():
        _classifier_instance = SectionClassifier()
    return _classifier_instance


# Alias methods for test compatibility
SectionClassifier.detect_sections = lambda self, text: [
    {'header': result.section_header, 'text': result.section_text, 'is_relevant': result.is_skills_relevant, 'probability': result.relevance_probability}
    for result in self.classify_sections(text or "")
]

SectionClassifier.get_relevance_score = lambda self, section_header: (
    0.9 if any(h in (section_header or "").lower() for h in self._relevant_headers) else
    0.1 if any(h in (section_header or "").lower() for h in self._non_relevant_headers) else
    0.5
)
