"""
Enhanced Skills Extractor with modern ML techniques.

This is a drop-in replacement for the original SkillsExtractor with:
- 400+ modern tech skills
- Semantic similarity matching
- Pattern-based extraction
- ML confidence scoring
- Better deduplication
"""

import json
import logging
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict, Counter

from .enhanced_config import EnhancedSkillsConfig
from .enhanced_extractors import (
    EnhancedLexiconExtractor, 
    PatternBasedExtractor, 
    SemanticExtractor,
    MLBasedConfidenceScorer
)
from .storage import SkillsStorage, BigQuerySkillsStorage
from .utils import get_nlp, get_enhanced_phrase_matcher


class EnhancedSkillsExtractor:
    """
    Enhanced skills extractor with modern ML capabilities.
    
    Features:
    - Comprehensive tech skills lexicon (400+ skills)
    - Semantic similarity matching using sentence transformers
    - Pattern-based extraction for frameworks/versions
    - Advanced ML confidence scoring
    - Intelligent deduplication
    """
    
    def __init__(
        self,
        config: Optional[EnhancedSkillsConfig] = None,
        storage: Optional[SkillsStorage] = None,
        enable_semantic: bool = True,
        enable_patterns: bool = True
    ):
        """
        Initialize enhanced skills extractor.
        
        Args:
            config: Enhanced configuration
            storage: Storage backend
            enable_semantic: Enable semantic similarity extraction
            enable_patterns: Enable pattern-based extraction
        """
        self.config = config or EnhancedSkillsConfig()
        self.storage = storage or BigQuerySkillsStorage(
            project_id=self.config.project_id,
            dataset_id=self.config.dataset_id
        )
        
        # Initialize NLP components
        self.nlp = get_nlp()
        self.phrase_matcher = get_enhanced_phrase_matcher(self.nlp, self.config)
        
        # Initialize extractors
        self.extractors = []
        
        # Always include enhanced lexicon extractor
        self.lexicon_extractor = EnhancedLexiconExtractor(
            phrase_matcher=self.phrase_matcher,
            normalizer=None,  # Will be initialized if needed
            scorer=None,      # Will be initialized if needed
            config=self.config
        )
        self.extractors.append(self.lexicon_extractor)
        
        # Add pattern-based extractor
        if enable_patterns and self.config.ml_config.use_pattern_extraction:
            self.pattern_extractor = PatternBasedExtractor(self.config)
            self.extractors.append(self.pattern_extractor)
        
        # Add semantic extractor
        if enable_semantic and self.config.ml_config.use_semantic_extraction:
            try:
                self.semantic_extractor = SemanticExtractor(
                    config=self.config,
                    model_name=self.config.ml_config.sentence_transformer_model
                )
                self.extractors.append(self.semantic_extractor)
            except ImportError:
                logging.warning("Semantic extraction disabled: sentence-transformers not available")
        
        # Initialize ML confidence scorer
        self.ml_scorer = MLBasedConfidenceScorer(self.config)
        
        logging.info(f"Enhanced Skills Extractor v{self.config.version} initialized with {len(self.extractors)} extractors")
    
    def get_version(self) -> str:
        """Return extractor version."""
        return self.config.version
    
    def extract_skills(
        self, 
        job_summary: str = "", 
        job_description: str = "",
        min_confidence: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract skills from job summary and description.
        
        Args:
            job_summary: Job summary text
            job_description: Full job description
            min_confidence: Minimum confidence threshold (uses config default if None)
            
        Returns:
            List of skill dictionaries with enhanced fields
        """
        all_skills = []
        min_conf = min_confidence or self.config.confidence_threshold
        
        # Combine texts for processing
        texts = {
            'job_summary': job_summary or "",
            'job_description': job_description or ""
        }
        
        for source_field, text in texts.items():
            if not text.strip():
                continue
                
            # Process with spaCy
            doc = self.nlp(text)
            
            # Run all extractors
            for extractor in self.extractors:
                try:
                    skills = extractor.extract(doc, text, source_field)
                    all_skills.extend(skills)
                except Exception as e:
                    logging.warning(f"Extractor {type(extractor).__name__} failed: {e}")
        
        # Post-process skills
        processed_skills = self._post_process_skills(all_skills, min_conf)
        
        logging.info(f"Extracted {len(processed_skills)} skills from {len(all_skills)} candidates")
        return processed_skills
    
    def _post_process_skills(
        self, 
        skills: List[Dict[str, Any]], 
        min_confidence: float
    ) -> List[Dict[str, Any]]:
        """
        Post-process extracted skills with ML scoring and deduplication.
        
        Args:
            skills: Raw extracted skills
            min_confidence: Minimum confidence threshold
            
        Returns:
            Processed and filtered skills
        """
        # Re-score with ML confidence scoring
        if self.config.ml_config.use_ml_confidence_scoring:
            for skill in skills:
                enhanced_confidence = self.ml_scorer.calculate_advanced_confidence(
                    text=skill.get('source_text', ''),
                    skill=skill['skill_name'],
                    context=skill.get('context_snippet', ''),
                    category=skill.get('skill_category', ''),
                    extraction_method=skill.get('extraction_method', ''),
                    additional_features=skill.get('features', {})
                )
                
                # Combine with original confidence
                original_conf = skill.get('confidence_score', 0.5)
                skill['confidence_score'] = (enhanced_confidence + original_conf) / 2
        
        # Apply category weights
        for skill in skills:
            category = skill.get('skill_category', '')
            category_weight = self.config.get_category_weight(category)
            skill['confidence_score'] *= category_weight
        
        # Filter by confidence
        filtered_skills = [
            skill for skill in skills 
            if skill['confidence_score'] >= min_confidence
        ]
        
        # Deduplicate skills
        deduplicated_skills = self._intelligent_deduplication(filtered_skills)
        
        # Limit skills per category
        limited_skills = self._limit_skills_per_category(deduplicated_skills)
        
        # Sort by confidence
        limited_skills.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return limited_skills
    
    def _intelligent_deduplication(
        self, 
        skills: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Intelligent deduplication using similarity and confidence.
        """
        # Group by normalized skill name
        skill_groups = defaultdict(list)
        
        for skill in skills:
            # Normalize skill name for grouping
            normalized_name = self._normalize_for_dedup(skill['skill_name'])
            skill_groups[normalized_name].append(skill)
        
        deduplicated = []
        
        for group in skill_groups.values():
            if len(group) == 1:
                deduplicated.extend(group)
            else:
                # Keep the highest confidence skill from the group
                best_skill = max(group, key=lambda x: x['confidence_score'])
                
                # Merge context from all skills in group
                all_contexts = [s.get('context_snippet', '') for s in group]
                best_skill['context_snippet'] = ' | '.join(filter(None, all_contexts))[:200]
                
                # Add metadata about deduplication
                best_skill['dedupe_count'] = len(group)
                best_skill['alternative_names'] = list(set(s['skill_name'] for s in group))
                
                deduplicated.append(best_skill)
        
        return deduplicated
    
    def _normalize_for_dedup(self, skill_name: str) -> str:
        """Normalize skill name for deduplication."""
        # Convert to lowercase and remove common variations
        normalized = skill_name.lower().strip()
        
        # Handle common variations
        variations = {
            'javascript': ['js', 'java script'],
            'typescript': ['ts', 'type script'],
            'postgresql': ['postgres', 'psql'],
            'kubernetes': ['k8s', 'kube'],
            'docker': ['containerization'],
            'amazon web services': ['aws'],
            'google cloud platform': ['gcp', 'google cloud'],
            'microsoft azure': ['azure']
        }
        
        # Check if skill matches any variation
        for standard, variants in variations.items():
            if normalized in variants or normalized == standard:
                return standard
        
        # Handle framework patterns (e.g., "react.js" -> "react")
        if normalized.endswith('.js'):
            normalized = normalized[:-3]
        elif normalized.endswith(' framework'):
            normalized = normalized[:-10]
        
        return normalized
    
    def _limit_skills_per_category(
        self, 
        skills: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Limit number of skills per category to prevent spam.
        """
        category_counts = defaultdict(int)
        limited_skills = []
        
        # Sort by confidence to prioritize best skills
        sorted_skills = sorted(skills, key=lambda x: x['confidence_score'], reverse=True)
        
        max_per_category = self.config.ml_config.max_skills_per_category
        
        for skill in sorted_skills:
            category = skill.get('skill_category', 'uncategorized')
            
            if category_counts[category] < max_per_category:
                limited_skills.append(skill)
                category_counts[category] += 1
            else:
                # Skip if category is full, unless it's very high confidence
                if skill['confidence_score'] > 0.9:
                    limited_skills.append(skill)
                    # Mark as overflow
                    skill['category_overflow'] = True
        
        return limited_skills
    
    def store_skills(
        self,
        job_posting_id: str,
        enrichment_id: str,
        skills: List[Dict[str, Any]]
    ) -> None:
        """
        Store skills using the configured storage backend.
        
        Args:
            job_posting_id: Job posting identifier
            enrichment_id: Enrichment tracking identifier
            skills: List of extracted skills
        """
        if not skills:
            logging.warning(f"No skills to store for job {job_posting_id}")
            return
        
        # Add metadata to skills before storing
        enriched_skills = []
        for skill in skills:
            enriched_skill = {
                'skill_name': skill['skill_name'],
                'skill_category': skill.get('skill_category', 'uncategorized'),
                'confidence_score': skill['confidence_score'],
                'source_field': skill.get('source_field', 'unknown'),
                'context_snippet': skill.get('context_snippet', ''),
                'extraction_method': skill.get('extraction_method', 'enhanced'),
                
                # Enhanced metadata
                'extractor_version': self.config.version,
                'category_weight': self.config.get_category_weight(skill.get('skill_category', '')),
                'is_high_priority': self.config.is_high_priority_category(skill.get('skill_category', '')),
            }
            
            # Add optional enhanced fields if present
            for field in ['dedupe_count', 'alternative_names', 'similarity_score', 'category_overflow']:
                if field in skill:
                    enriched_skill[field] = skill[field]
            
            enriched_skills.append(enriched_skill)
        
        # Store using the storage backend
        self.storage.store_skills(job_posting_id, enrichment_id, enriched_skills)
        
        logging.info(f"Stored {len(enriched_skills)} skills for job {job_posting_id}")
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get statistics about the extraction process."""
        return {
            'version': self.config.version,
            'extractors_count': len(self.extractors),
            'extractors': [type(e).__name__ for e in self.extractors],
            'lexicon_size': sum(len(skills) for skills in self.config.enhanced_skills_lexicon.values()),
            'categories': list(self.config.enhanced_skills_lexicon.keys()),
            'semantic_enabled': hasattr(self, 'semantic_extractor'),
            'patterns_enabled': hasattr(self, 'pattern_extractor'),
            'ml_scoring_enabled': self.config.ml_config.use_ml_confidence_scoring
        }