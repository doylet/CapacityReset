"""
Configuration for skills extraction.

Centralized configuration with parameterized ML capabilities.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set


# Skills Lexicon - 175 general skills across 11 categories
# Source: User-provided skills CSV (unsupervised reference)
SKILLS_LEXICON = {
    'communicating': [
        'corresponding', 'editing', 'facilitating', 'interviewing', 'listening',
        'negotiating', 'persuading', 'presenting', 'public speaking', 'reporting',
        'translating', 'writing'
    ],
    'creative_skills': [
        'composing', 'conceiving', 'conceptualising', 'creating', 'devising',
        'designing', 'drawing', 'illustrating', 'innovating', 'painting',
        'performing', 'photographing', 'sculpting', 'styling'
    ],
    'developing_people': [
        'advising', 'assessing performance', 'coaching', 'collaborating', 'building teams',
        'consulting', 'counselling', 'demonstrating', 'facilitating', 'group dynamics',
        'instructing', 'mediating', 'motivating', 'teaching'
    ],
    'financial_skills': [
        'analysing', 'appraising', 'estimating', 'assessing', 'auditing',
        'budgeting', 'calculating', 'costing', 'evaluating', 'forecasting',
        'investing'
    ],
    'interpersonal_skills': [
        'advising skills', 'facilitating', 'formulating', 'group participation', 'working autonomously',
        'influencing', 'leading', 'liaising', 'motivating', 'negotiating skills',
        'networking', 'relationship building', 'teamwork', 'trust building'
    ],
    'managing_directing': [
        'appraising', 'approving', 'coaching', 'coordinating', 'delegating',
        'developing others', 'executing', 'facilitating', 'formulating', 'influencing',
        'interviewing', 'hiring', 'leading meetings', 'making decisions', 'managing',
        'managing projects', 'mentoring', 'planning', 'team building'
    ],
    'organising': [
        'general administration', 'quality control', 'time management', 'filing', 'categorising',
        'classifying', 'compiling', 'coordinating', 'distributing', 'documenting',
        'expediting', 'implementing', 'maintaining', 'monitoring', 'office management',
        'planning', 'scheduling', 'systematising'
    ],
    'planning': [
        'analysing', 'conceptualising', 'designing', 'developing policy', 'developing strategy',
        'establishing goals', 'identifying problems', 'strategic thinking'
    ],
    'researching_analysing': [
        'assessing', 'calculating', 'classifying', 'critiquing', 'developing',
        'diagnosing', 'evaluating', 'examining', 'experimenting', 'extracting',
        'interpreting', 'interrogating', 'investigating', 'measuring', 'organising',
        'researching', 'reviewing', 'solving problems', 'summarising', 'surveying',
        'synthesising', 'testing', 'troubleshooting'
    ],
    'selling_marketing': [
        'advertising', 'analysing markets', 'building rapport', 'building relationships', 'delivering',
        'demonstrating', 'developing', 'editing', 'identifying', 'influencing',
        'marketing', 'merchandising', 'promoting', 'prospecting', 'publicising',
        'sales', 'selling', 'servicing', 'social media', 'writing copy'
    ],
    'technical_skills': [
        'assembling', 'building', 'calibrating', 'configuring', 'constructing',
        'designing', 'developing', 'diagnosing', 'engineering', 'fabricating',
        'installing', 'maintaining', 'manufacturing', 'operating', 'programming',
        'repairing', 'setting up', 'technical writing', 'testing', 'training',
        'troubleshooting', 'upgrading', 'using technology'
    ]
}


@dataclass
class ExtractionWeights:
    """Weights for different extraction methods."""
    lexicon_match: float = 1.0
    ner: float = 0.7
    noun_chunk: float = 0.6


@dataclass
class ConfidenceWeights:
    """Weights for confidence scoring."""
    base_score: float = 0.5
    frequency_boost_per_mention: float = 0.1
    max_frequency_boost: float = 0.3
    strong_indicator_boost: float = 0.2
    medium_indicator_boost: float = 0.1


@dataclass
class FilterConfig:
    """Configuration for skill filtering."""
    min_skill_length: int = 3
    max_skill_length: int = 30
    min_chunk_words: int = 2
    max_chunk_words: int = 4
    min_section_length: int = 50
    fallback_section_length: int = 200
    confidence_threshold: float = 0.5


@dataclass
class SkillsConfig:
    """
    Complete configuration for skills extraction.
    
    This centralizes all parameters to make the ML pipeline configurable
    and easier to tune/experiment with.
    """
    
    # Version identifier
    version: str = "v2.5-balanced-filtering"
    
    # BigQuery configuration
    project_id: str = "sylvan-replica-478802-p4"
    dataset_id: str = "brightdata_jobs"
    
    # Skills lexicon (can be overridden with BigQuery data)
    skills_lexicon: Dict[str, List[str]] = field(default_factory=lambda: SKILLS_LEXICON)
    
    # Section keywords for filtering
    skill_relevant_sections: List[str] = field(default_factory=lambda: [
        'responsibilities', 'requirements', 'qualifications', 'required qualifications',
        'preferred qualifications', 'what you\'ll do', 'what we\'re looking for',
        'about you', 'about the role', 'key responsibilities', 'your role',
        'essential skills', 'required skills', 'desired skills', 'technical skills',
        'experience', 'must have', 'nice to have', 'ideal candidate',
        'you will', 'job description', 'role overview', 'duties',
        'what you bring', 'what you need', 'position', 'job requirements',
        'skills and experience', 'core competencies', 'minimum requirements'
    ])
    
    excluded_sections: List[str] = field(default_factory=lambda: [
        'benefits', 'about us', 'about the company', 'compensation', 'perks',
        'salary', 'location', 'equal opportunity', 'diversity', 'how to apply',
        'company culture', 'our values', 'why join us', 'work environment'
    ])
    
    # Filtering configuration
    filter_config: FilterConfig = field(default_factory=FilterConfig)
    
    # Extraction weights
    extraction_weights: ExtractionWeights = field(default_factory=ExtractionWeights)
    
    # Confidence scoring weights
    confidence_weights: ConfidenceWeights = field(default_factory=ConfidenceWeights)
    
    # Context extraction window
    context_window: int = 50
    
    # Strong context indicators
    strong_indicators: Set[str] = field(default_factory=lambda: {
        'required', 'must have', 'essential', 'proficient', 'expert'
    })
    
    # Medium context indicators
    medium_indicators: Set[str] = field(default_factory=lambda: {
        'experience', 'knowledge', 'familiar', 'understanding', 'ability'
    })
    
    # Non-skill phrases to filter out
    non_skill_phrases: Set[str] = field(default_factory=lambda: {
        'new york', 'san francisco', 'los angeles', 'remote', 'hybrid',
        'full time', 'part time', 'contract', 'permanent', 'temporary',
        'team player', 'fast paced', 'work environment', 'company culture',
        'competitive salary', 'health insurance', 'equal opportunity',
        'job description', 'about us', 'apply now', 'click here',
        'work life balance', 'professional development', 'career growth',
        'team member', 'job posting', 'united states', 'north america'
    })
    
    # Skill-related nouns for chunk detection
    skill_nouns: Set[str] = field(default_factory=lambda: {
        'management', 'analysis', 'development', 'design', 'engineering',
        'leadership', 'communication', 'planning', 'strategy', 'thinking',
        'solving', 'building', 'testing', 'implementation', 'architecture'
    })
    
    @property
    def full_dataset_id(self) -> str:
        """Return fully qualified dataset ID."""
        return f"{self.project_id}.{self.dataset_id}"
