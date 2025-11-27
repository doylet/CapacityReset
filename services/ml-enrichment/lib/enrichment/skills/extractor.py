"""
Main skills extractor orchestrator.

Coordinates all extraction strategies, filtering, scoring, and storage.
"""

from typing import List, Dict, Any, Optional
from .config import SkillsConfig
from .normalizer import TextNormalizer
from .filters import SkillFilter, SectionFilter
from .scorer import SkillScorer
from .extractors import LexiconExtractor, NERExtractor, NounChunkExtractor, ExtractionStrategy
from .storage import SkillsStorage, BigQuerySkillsStorage
from .utils import get_nlp, get_phrase_matcher


class SkillsExtractor:
    """
    Orchestrates skills extraction using multiple strategies.
    
    Uses dependency injection for all components, making it easy to:
    - Test with mock implementations
    - Swap out extraction strategies
    - Tune configuration parameters
    - Use different storage backends
    """
    
    def __init__(
        self,
        config: Optional[SkillsConfig] = None,
        storage: Optional[SkillsStorage] = None,
        extractors: Optional[List[ExtractionStrategy]] = None
    ):
        """
        Initialize skills extractor with dependencies.
        
        Args:
            config: Configuration (uses defaults if None)
            storage: Storage backend (uses BigQuery if None)
            extractors: List of extraction strategies (uses all default if None)
        """
        # Configuration
        self.config = config or SkillsConfig()
        
        # NLP components
        self.nlp = get_nlp()
        self.phrase_matcher = get_phrase_matcher(self.nlp, self.config)
        
        # Initialize component dependencies
        self.normalizer = TextNormalizer(self.nlp)
        self.skill_filter = SkillFilter(self.config)
        self.section_filter = SectionFilter(self.config)
        self.scorer = SkillScorer(self.config)
        
        # Storage
        self.storage = storage or BigQuerySkillsStorage(
            self.config.project_id,
            self.config.dataset_id
        )
        
        # Extraction strategies
        if extractors is None:
            self.extractors = [
                LexiconExtractor(self.phrase_matcher, self.normalizer, self.scorer, self.config),
                NERExtractor(self.normalizer, self.scorer, self.skill_filter, self.config),
                NounChunkExtractor(self.normalizer, self.scorer, self.skill_filter, self.config)
            ]
        else:
            self.extractors = extractors
    
    def get_version(self) -> str:
        """Return extractor version identifier."""
        return self.config.version
    
    def extract_skills(self, job_summary: str, job_description: str) -> List[Dict[str, Any]]:
        """
        Extract skills using all configured extraction strategies.
        
        Args:
            job_summary: Brief job summary
            job_description: Full job description (may contain HTML)
            
        Returns:
            List of skill dictionaries with name, category, confidence, context
        """
        skills = []
        
        # Strip HTML from job description before processing
        job_description_clean = self.normalizer.strip_html(job_description) if job_description else ''
        
        # Identify skill-relevant sections in job description
        relevant_sections = self.section_filter.identify_skill_relevant_sections(job_description_clean)
        
        # Process job summary (always relevant)
        if job_summary:
            doc = self.nlp(job_summary)
            
            # Apply all extraction strategies
            for extractor in self.extractors:
                extracted = extractor.extract(doc, job_summary, 'job_summary')
                skills.extend(extracted)
        
        # Process only relevant sections from job description
        for section in relevant_sections:
            section_text = section['content']
            section_type = section['type']
            
            # Process with spaCy
            doc = self.nlp(section_text)
            
            # Apply all extraction strategies
            for extractor in self.extractors:
                extracted = extractor.extract(
                    doc, 
                    section_text, 
                    f'job_description_{section_type}'
                )
                skills.extend(extracted)
        
        # Deduplicate skills (keep highest confidence)
        unique_skills = {}
        for skill in skills:
            key = (skill['skill_name'].lower(), skill['skill_category'])
            if key not in unique_skills or skill['confidence_score'] > unique_skills[key]['confidence_score']:
                unique_skills[key] = skill
        
        # Filter by confidence threshold
        filtered_skills = [
            s for s in unique_skills.values() 
            if s['confidence_score'] >= self.config.filter_config.confidence_threshold
        ]
        
        print(f"📊 Extracted {len(unique_skills)} unique skills, "
              f"filtered to {len(filtered_skills)} above "
              f"{self.config.filter_config.confidence_threshold} confidence")
        
        return filtered_skills
    
    def store_skills(self, job_posting_id: str, enrichment_id: str, skills: List[Dict[str, Any]]):
        """
        Store extracted skills using configured storage backend.
        
        Args:
            job_posting_id: Job reference
            enrichment_id: Enrichment tracking reference
            skills: List of extracted skills
        """
        self.storage.store_skills(job_posting_id, enrichment_id, skills)
