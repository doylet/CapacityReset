"""
Extraction strategies for skills.

Implements Strategy pattern for different skill extraction methods.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .config import SkillsConfig
from .filters import SkillFilter
from .scorer import SkillScorer
from .normalizer import TextNormalizer


class ExtractionStrategy(ABC):
    """Abstract base class for skill extraction strategies."""
    
    @abstractmethod
    def extract(self, doc, text: str, source_field: str) -> List[Dict[str, Any]]:
        """
        Extract skills from text using specific strategy.
        
        Args:
            doc: spaCy document
            text: Source text
            source_field: Field identifier (e.g., 'job_summary', 'job_description_responsibilities')
            
        Returns:
            List of skill dictionaries
        """
        pass


class LexiconExtractor(ExtractionStrategy):
    """Extracts skills by matching against a curated lexicon."""
    
    def __init__(
        self,
        phrase_matcher,
        normalizer: TextNormalizer,
        scorer: SkillScorer,
        config: SkillsConfig
    ):
        """
        Initialize lexicon extractor.
        
        Args:
            phrase_matcher: spaCy PhraseMatcher with loaded lexicon
            normalizer: Text normalizer instance
            scorer: Skill scorer instance
            config: Configuration
        """
        self.phrase_matcher = phrase_matcher
        self.normalizer = normalizer
        self.scorer = scorer
        self.config = config
    
    def extract(self, doc, text: str, source_field: str) -> List[Dict[str, Any]]:
        """Extract skills that match the skills lexicon."""
        skills = []
        matches = self.phrase_matcher(doc)
        
        for match_id, start, end in matches:
            # Get the matched span
            span = doc[start:end]
            category = doc.vocab.strings[match_id]
            skill_text = span.text
            
            # Normalize and clean the skill text
            normalized_skill = self.normalizer.normalize_skill_text(skill_text, span)
            if not normalized_skill:
                continue
            
            # Extract context
            context = self.scorer.extract_context(text, skill_text)
            
            # Calculate confidence (lexicon match has full weight)
            confidence = self.scorer.calculate_confidence(text, skill_text, context)
            confidence *= self.config.extraction_weights.lexicon_match
            
            skills.append({
                'skill_name': normalized_skill,
                'skill_category': category,
                'source_field': source_field,
                'confidence_score': confidence,
                'context_snippet': context,
                'extraction_method': 'lexicon_match'
            })
        
        return skills


class NERExtractor(ExtractionStrategy):
    """Extracts skills from Named Entity Recognition."""
    
    def __init__(
        self,
        normalizer: TextNormalizer,
        scorer: SkillScorer,
        skill_filter: SkillFilter,
        config: SkillsConfig
    ):
        """
        Initialize NER extractor.
        
        Args:
            normalizer: Text normalizer instance
            scorer: Skill scorer instance
            skill_filter: Skill filter instance
            config: Configuration
        """
        self.normalizer = normalizer
        self.scorer = scorer
        self.skill_filter = skill_filter
        self.config = config
    
    def extract(self, doc, text: str, source_field: str) -> List[Dict[str, Any]]:
        """Extract skills from named entities (PRODUCT, ORG, SKILL-like)."""
        skills = []
        
        # Look for entities that might be skills/tools/technologies
        for ent in doc.ents:
            # Focus on PRODUCT, ORG entities that are likely tools/tech
            if ent.label_ in ['PRODUCT', 'ORG', 'GPE']:
                skill_text = ent.text
                
                # Filter out obviously non-skill entities
                if self.skill_filter.is_likely_skill(skill_text):
                    # Normalize and clean
                    normalized_skill = self.normalizer.normalize_skill_text(skill_text, ent)
                    if not normalized_skill:
                        continue
                    
                    context = self.scorer.extract_context(text, skill_text)
                    confidence = self.scorer.calculate_confidence(text, skill_text, context)
                    confidence *= self.config.extraction_weights.ner
                    
                    skills.append({
                        'skill_name': normalized_skill,
                        'skill_category': 'technical_skills',
                        'source_field': source_field,
                        'confidence_score': confidence,
                        'context_snippet': context,
                        'extraction_method': 'ner'
                    })
        
        return skills


class NounChunkExtractor(ExtractionStrategy):
    """Extracts skill-like noun chunks."""
    
    def __init__(
        self,
        normalizer: TextNormalizer,
        scorer: SkillScorer,
        skill_filter: SkillFilter,
        config: SkillsConfig
    ):
        """
        Initialize noun chunk extractor.
        
        Args:
            normalizer: Text normalizer instance
            scorer: Skill scorer instance
            skill_filter: Skill filter instance
            config: Configuration
        """
        self.normalizer = normalizer
        self.scorer = scorer
        self.skill_filter = skill_filter
        self.config = config
    
    def extract(self, doc, text: str, source_field: str) -> List[Dict[str, Any]]:
        """Extract skill-like noun chunks (e.g., 'project management', 'data analysis')."""
        skills = []
        
        for chunk in doc.noun_chunks:
            # Look for chunks with skill-like patterns
            if self.skill_filter.is_skill_chunk(chunk):
                skill_text = chunk.text
                
                # Normalize and clean
                normalized_skill = self.normalizer.normalize_skill_text(skill_text, chunk)
                if not normalized_skill:
                    continue
                
                context = self.scorer.extract_context(text, skill_text)
                confidence = self.scorer.calculate_confidence(text, skill_text, context)
                confidence *= self.config.extraction_weights.noun_chunk
                
                # Categorize based on verbs
                category = self._categorize_chunk(chunk)
                
                skills.append({
                    'skill_name': normalized_skill,
                    'skill_category': category,
                    'source_field': source_field,
                    'confidence_score': confidence,
                    'context_snippet': context,
                    'extraction_method': 'noun_chunk'
                })
        
        return skills
    
    def _categorize_chunk(self, chunk) -> str:
        """Categorize a noun chunk based on its lemmas."""
        text = chunk.text.lower()
        
        if any(word in text for word in ['manage', 'lead', 'direct', 'coordinate']):
            return 'managing_directing'
        elif any(word in text for word in ['plan', 'strategy', 'design']):
            return 'planning'
        elif any(word in text for word in ['research', 'analyse', 'analyze', 'investigate']):
            return 'researching_analysing'
        elif any(word in text for word in ['communicate', 'present', 'write', 'speak']):
            return 'communicating'
        elif any(word in text for word in ['technical', 'program', 'engineer', 'build']):
            return 'technical_skills'
        elif any(word in text for word in ['sell', 'market', 'promote']):
            return 'selling_marketing'
        else:
            return 'general_skills'
