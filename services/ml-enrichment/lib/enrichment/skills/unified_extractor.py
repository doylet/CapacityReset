"""
Unified skills extractor with automatic enhanced/original fallback.

This consolidates both the original and enhanced extractors into a single implementation
that automatically uses enhanced ML features when available, falling back gracefully.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import logging
from dataclasses import dataclass

# Try to import enhanced ML dependencies
try:
    from sentence_transformers import SentenceTransformer
    import torch
    import re
    ENHANCED_DEPENDENCIES_AVAILABLE = True
except ImportError:
    ENHANCED_DEPENDENCIES_AVAILABLE = False

from .unified_config import UnifiedSkillsConfig
from .normalizer import TextNormalizer
from .filters import SkillFilter, SectionFilter
from .scorer import SkillScorer
from .storage import SkillsStorage, BigQuerySkillsStorage
from .utils import get_nlp, get_phrase_matcher


@dataclass
class SkillMatch:
    """Represents a matched skill with metadata."""
    text: str
    category: str
    confidence: float
    extraction_method: str
    context: str
    start_char: int
    end_char: int
    normalized: str


class UnifiedSkillsExtractor:
    """
    Unified skills extractor that automatically uses enhanced features when available.
    
    This combines the functionality of both the original and enhanced extractors,
    providing seamless fallback when advanced ML dependencies are not available.
    """
    
    def __init__(
        self,
        config: Optional[UnifiedSkillsConfig] = None,
        storage: Optional[SkillsStorage] = None,
        enable_semantic: bool = True,
        enable_patterns: bool = True
    ):
        """Initialize unified extractor with optional advanced features."""
        
        # Configuration
        self.config = config or UnifiedSkillsConfig()
        
        # Check if enhanced features are available and requested
        self.enhanced_mode = (
            ENHANCED_DEPENDENCIES_AVAILABLE 
            and self.config.enhanced_mode 
            and (enable_semantic or enable_patterns)
        )
        
        # Update config based on available features
        if not self.enhanced_mode and self.config.fallback_to_original:
            self.config.enhanced_mode = False
            logging.info("Enhanced ML features not available, falling back to original extraction")
        
        # NLP components
        self.nlp = get_nlp()
        self.phrase_matcher = get_phrase_matcher(self.nlp, self.config)
        
        # Core components
        self.normalizer = TextNormalizer(self.nlp)
        self.skill_filter = SkillFilter(self.config)
        self.section_filter = SectionFilter(self.config)
        self.scorer = SkillScorer(self.config)
        
        # Initialize BigQuery storage with proper parameters
        if storage is None:
            import os
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "sylvan-replica-478802-p4")
            dataset_id = os.getenv("BIGQUERY_DATASET", "brightdata_jobs")
            self.storage = BigQuerySkillsStorage(project_id, dataset_id)
        else:
            self.storage = storage
        
        # Enhanced ML components (if available)
        self.semantic_model = None
        self.enable_semantic = enable_semantic and self.enhanced_mode
        self.enable_patterns = enable_patterns and self.enhanced_mode
        
        if self.enhanced_mode:
            self._initialize_enhanced_features()
        
        # Skills lexicon
        self.skills_lexicon = self.config.get_skills_lexicon()
        self._build_skill_sets()
        
        logging.info(f"Initialized UnifiedSkillsExtractor v{self.config.version} "
                    f"(enhanced_mode={self.enhanced_mode}, semantic={self.enable_semantic}, "
                    f"patterns={self.enable_patterns})")
    
    def _initialize_enhanced_features(self):
        """Initialize enhanced ML components if available."""
        if not ENHANCED_DEPENDENCIES_AVAILABLE:
            return
        
        try:
            if self.enable_semantic:
                # Initialize sentence transformer for semantic similarity
                model_name = self.config.ml_config.sentence_transformer_model
                self.semantic_model = SentenceTransformer(model_name)
                logging.info(f"Loaded semantic model: {model_name}")
        except Exception as e:
            logging.warning(f"Failed to load semantic model: {e}")
            self.enable_semantic = False
    
    def _build_skill_sets(self):
        """Build skill sets for efficient lookup."""
        self.all_skills = set()
        self.skills_by_category = {}
        
        for category, skills in self.skills_lexicon.items():
            normalized_skills = [self.normalizer.normalize_skill(skill) for skill in skills]
            self.skills_by_category[category] = set(normalized_skills)
            self.all_skills.update(normalized_skills)
    
    def extract_skills(
        self,
        job_summary: str,
        job_description: str,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract skills using unified approach with enhanced features when available.
        
        Returns:
            Dict with skills, metadata, and extraction statistics
        """
        
        # Combine and normalize text
        combined_text = f"{job_summary} {job_description}"
        normalized_text = self.normalizer.normalize_text(combined_text)
        
        # Filter to relevant sections
        relevant_text = self.section_filter.extract_relevant_sections(normalized_text)
        
        # Extract skills using multiple strategies
        skill_matches = []
        
        # 1. Enhanced lexicon matching
        lexicon_matches = self._extract_lexicon_skills(relevant_text)
        skill_matches.extend(lexicon_matches)
        
        # 2. Semantic similarity (if enhanced mode)
        if self.enable_semantic:
            semantic_matches = self._extract_semantic_skills(relevant_text)
            skill_matches.extend(semantic_matches)
        
        # 3. Pattern-based extraction (if enhanced mode)
        if self.enable_patterns:
            pattern_matches = self._extract_pattern_skills(relevant_text)
            skill_matches.extend(pattern_matches)
        
        # 4. NER extraction (fallback)
        ner_matches = self._extract_ner_skills(relevant_text)
        skill_matches.extend(ner_matches)
        
        # 5. Noun chunk extraction (fallback)
        chunk_matches = self._extract_noun_chunk_skills(relevant_text)
        skill_matches.extend(chunk_matches)
        
        # Deduplicate and filter
        filtered_matches = self._deduplicate_and_filter(skill_matches)
        
        # Score and rank skills
        scored_skills = self._score_skills(filtered_matches, relevant_text)
        
        # Apply confidence threshold
        threshold = self.config.get_confidence_threshold()
        final_skills = [skill for skill in scored_skills if skill['confidence'] >= threshold]
        
        # Group by category and limit per category if enhanced mode
        if self.enhanced_mode:
            final_skills = self._limit_skills_per_category(final_skills)
        
        return {
            'skills': final_skills,
            'extraction_metadata': {
                'total_matches': len(skill_matches),
                'filtered_matches': len(filtered_matches),
                'final_skills': len(final_skills),
                'enhanced_mode': self.enhanced_mode,
                'semantic_enabled': self.enable_semantic,
                'patterns_enabled': self.enable_patterns,
                'confidence_threshold': threshold,
                'extractor_version': self.config.version
            }
        }
    
    def _extract_lexicon_skills(self, text: str) -> List[SkillMatch]:
        """Extract skills using lexicon matching."""
        matches = []
        doc = self.nlp(text)
        
        for category, skills in self.skills_by_category.items():
            for skill in skills:
                # Simple substring matching
                skill_lower = skill.lower()
                text_lower = text.lower()
                
                start = 0
                while True:
                    pos = text_lower.find(skill_lower, start)
                    if pos == -1:
                        break
                    
                    # Extract context
                    context_start = max(0, pos - self.config.context_window)
                    context_end = min(len(text), pos + len(skill) + self.config.context_window)
                    context = text[context_start:context_end].strip()
                    
                    matches.append(SkillMatch(
                        text=skill,
                        category=category,
                        confidence=self.config.extraction_weights.enhanced_lexicon if self.enhanced_mode 
                                 else self.config.extraction_weights.original_lexicon,
                        extraction_method='lexicon',
                        context=context,
                        start_char=pos,
                        end_char=pos + len(skill),
                        normalized=skill
                    ))
                    
                    start = pos + 1
        
        return matches
    
    def _extract_semantic_skills(self, text: str) -> List[SkillMatch]:
        """Extract skills using semantic similarity (enhanced mode only)."""
        if not self.enable_semantic or not self.semantic_model:
            return []
        
        matches = []
        threshold = self.config.ml_config.semantic_similarity_threshold
        
        try:
            # Get embeddings for text chunks
            doc = self.nlp(text)
            sentences = [sent.text for sent in doc.sents if len(sent.text.strip()) > 20]
            
            if not sentences:
                return matches
            
            # Get embeddings for sentences and all skills
            sentence_embeddings = self.semantic_model.encode(sentences)
            all_skills_list = list(self.all_skills)
            skill_embeddings = self.semantic_model.encode(all_skills_list)
            
            # Compute similarities
            import torch.nn.functional as F
            similarities = F.cosine_similarity(
                torch.tensor(sentence_embeddings).unsqueeze(1),
                torch.tensor(skill_embeddings).unsqueeze(0),
                dim=2
            )
            
            # Find high-similarity matches
            for i, sentence in enumerate(sentences):
                for j, skill in enumerate(all_skills_list):
                    similarity = similarities[i][j].item()
                    
                    if similarity >= threshold:
                        # Find which category this skill belongs to
                        category = None
                        for cat, cat_skills in self.skills_by_category.items():
                            if skill in cat_skills:
                                category = cat
                                break
                        
                        if category:
                            matches.append(SkillMatch(
                                text=skill,
                                category=category,
                                confidence=self.config.extraction_weights.semantic_similarity * similarity,
                                extraction_method='semantic',
                                context=sentence,
                                start_char=0,  # Approximate
                                end_char=len(skill),
                                normalized=skill
                            ))
        
        except Exception as e:
            logging.warning(f"Semantic extraction failed: {e}")
        
        return matches
    
    def _extract_pattern_skills(self, text: str) -> List[SkillMatch]:
        """Extract skills using regex patterns (enhanced mode only)."""
        if not self.enable_patterns:
            return []
        
        matches = []
        
        try:
            for pattern_type, patterns in self.config.tech_patterns.items():
                for pattern_str in patterns:
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    
                    for match in pattern.finditer(text):
                        skill_text = match.group(0).strip()
                        
                        if len(skill_text) >= self.config.filter_config.min_skill_length:
                            # Determine category based on pattern type
                            category = self._get_category_from_pattern(pattern_type, skill_text)
                            
                            # Extract context
                            context_start = max(0, match.start() - self.config.context_window)
                            context_end = min(len(text), match.end() + self.config.context_window)
                            context = text[context_start:context_end].strip()
                            
                            matches.append(SkillMatch(
                                text=skill_text,
                                category=category,
                                confidence=self.config.extraction_weights.pattern_based,
                                extraction_method='pattern',
                                context=context,
                                start_char=match.start(),
                                end_char=match.end(),
                                normalized=self.normalizer.normalize_skill(skill_text)
                            ))
        
        except Exception as e:
            logging.warning(f"Pattern extraction failed: {e}")
        
        return matches
    
    def _extract_ner_skills(self, text: str) -> List[SkillMatch]:
        """Extract skills using Named Entity Recognition."""
        matches = []
        
        try:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT", "EVENT"] and len(ent.text.strip()) >= 3:
                    normalized = self.normalizer.normalize_skill(ent.text)
                    
                    # Try to categorize
                    category = self._categorize_skill(normalized)
                    if category:
                        matches.append(SkillMatch(
                            text=ent.text.strip(),
                            category=category,
                            confidence=self.config.extraction_weights.ner,
                            extraction_method='ner',
                            context=ent.sent.text if ent.sent else ent.text,
                            start_char=ent.start_char,
                            end_char=ent.end_char,
                            normalized=normalized
                        ))
        
        except Exception as e:
            logging.warning(f"NER extraction failed: {e}")
        
        return matches
    
    def _extract_noun_chunk_skills(self, text: str) -> List[SkillMatch]:
        """Extract skills from noun chunks."""
        matches = []
        
        try:
            doc = self.nlp(text)
            
            for chunk in doc.noun_chunks:
                chunk_text = chunk.text.strip()
                word_count = len(chunk_text.split())
                
                if (self.config.filter_config.min_chunk_words <= word_count <= 
                    self.config.filter_config.max_chunk_words):
                    
                    normalized = self.normalizer.normalize_skill(chunk_text)
                    
                    # Try to categorize
                    category = self._categorize_skill(normalized)
                    if category:
                        matches.append(SkillMatch(
                            text=chunk_text,
                            category=category,
                            confidence=self.config.extraction_weights.noun_chunk,
                            extraction_method='noun_chunk',
                            context=chunk.sent.text if chunk.sent else chunk_text,
                            start_char=chunk.start_char,
                            end_char=chunk.end_char,
                            normalized=normalized
                        ))
        
        except Exception as e:
            logging.warning(f"Noun chunk extraction failed: {e}")
        
        return matches
    
    def _categorize_skill(self, skill: str) -> Optional[str]:
        """Try to categorize a skill based on known lexicons."""
        skill_lower = skill.lower()
        
        for category, skills in self.skills_by_category.items():
            if skill_lower in skills:
                return category
        
        return None
    
    def _get_category_from_pattern(self, pattern_type: str, skill_text: str) -> str:
        """Get category based on pattern type."""
        if pattern_type == 'versions':
            return 'programming_languages'
        elif pattern_type == 'frameworks':
            return 'web_frameworks'
        elif pattern_type == 'certifications':
            return 'devops_tools'
        else:
            return 'technical_skills'
    
    def _deduplicate_and_filter(self, matches: List[SkillMatch]) -> List[SkillMatch]:
        """Remove duplicates and apply basic filtering."""
        if not matches:
            return []
        
        # Filter by basic criteria
        filtered = []
        for match in matches:
            if (self.skill_filter.is_valid_skill(match.text) and 
                match.text.lower() not in self.config.noise_words):
                filtered.append(match)
        
        # Deduplicate by normalized text, keeping highest confidence
        seen = {}
        for match in filtered:
            key = match.normalized.lower()
            if key not in seen or match.confidence > seen[key].confidence:
                seen[key] = match
        
        return list(seen.values())
    
    def _score_skills(self, matches: List[SkillMatch], text: str) -> List[Dict[str, Any]]:
        """Score skills using advanced or basic scoring."""
        scored_skills = []
        
        for match in matches:
            if self.enhanced_mode and self.config.ml_config.use_ml_confidence_scoring:
                # Use enhanced ML scoring
                confidence = self._calculate_ml_confidence(match, text)
            else:
                # Use basic scoring
                confidence = self._calculate_basic_confidence(match, text)
            
            scored_skills.append({
                'text': match.text,
                'category': match.category,
                'confidence': confidence,
                'extraction_method': match.extraction_method,
                'context': match.context[:self.config.max_context_length]
            })
        
        return sorted(scored_skills, key=lambda x: x['confidence'], reverse=True)
    
    def _calculate_ml_confidence(self, match: SkillMatch, text: str) -> float:
        """Calculate confidence using ML-based ensemble scoring."""
        weights = self.config.ml_config.ensemble_weights
        scores = {}
        
        # Extraction method score
        scores['extraction_method'] = match.confidence
        
        # Context strength (check for strong indicators)
        context_lower = match.context.lower()
        context_strength = 0.5
        for indicator in self.config.skill_context_indicators['strong_indicators']:
            if indicator in context_lower:
                context_strength = 1.0
                break
        for indicator in self.config.skill_context_indicators['medium_indicators']:
            if indicator in context_lower:
                context_strength = max(context_strength, 0.7)
        scores['context_strength'] = context_strength
        
        # Frequency (how often the skill appears)
        frequency = text.lower().count(match.normalized.lower())
        scores['frequency'] = min(0.5 + frequency * 0.1, 1.0)
        
        # Category relevance
        scores['category_relevance'] = self.config.get_category_weight(match.category)
        
        # Position importance (skills mentioned early are often more important)
        position_ratio = match.start_char / max(len(text), 1)
        scores['position_importance'] = 1.0 - position_ratio * 0.3  # Earlier = higher score
        
        # Text quality (longer contexts are often more reliable)
        scores['text_quality'] = min(len(match.context) / 100, 1.0)
        
        # Skill specificity (longer, more specific skills are often better)
        scores['skill_specificity'] = min(len(match.text) / 20, 1.0)
        
        # Calculate weighted ensemble score
        final_score = sum(weights[feature] * score for feature, score in scores.items())
        return min(max(final_score, 0.0), 1.0)
    
    def _calculate_basic_confidence(self, match: SkillMatch, text: str) -> float:
        """Calculate confidence using basic scoring."""
        base_confidence = match.confidence
        
        # Frequency bonus
        frequency = text.lower().count(match.normalized.lower())
        frequency_bonus = min(frequency * 0.1, 0.3)
        
        # Context bonus
        context_lower = match.context.lower()
        context_bonus = 0.0
        for indicator in self.config.strong_indicators:
            if indicator in context_lower:
                context_bonus = 0.2
                break
        for indicator in self.config.medium_indicators:
            if indicator in context_lower:
                context_bonus = max(context_bonus, 0.1)
        
        return min(base_confidence + frequency_bonus + context_bonus, 1.0)
    
    def _limit_skills_per_category(self, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Limit number of skills per category (enhanced mode only)."""
        if not self.enhanced_mode:
            return skills
        
        category_counts = {}
        limited_skills = []
        max_per_category = self.config.ml_config.max_skills_per_category
        
        for skill in skills:
            category = skill['category']
            count = category_counts.get(category, 0)
            
            if count < max_per_category:
                limited_skills.append(skill)
                category_counts[category] = count + 1
        
        return limited_skills
    
    def get_version(self) -> str:
        """Get extractor version."""
        mode_suffix = "-enhanced" if self.enhanced_mode else "-legacy"
        return f"{self.config.version}{mode_suffix}"
    
    def save_skills(self, job_id: str, skills_data: Dict[str, Any]) -> bool:
        """Save extracted skills to storage."""
        try:
            return self.storage.save_skills(job_id, skills_data)
        except Exception as e:
            logging.error(f"Failed to save skills for job {job_id}: {e}")
            return False


# Aliases for backward compatibility
SkillsExtractor = UnifiedSkillsExtractor  # Original name  
EnhancedSkillsExtractor = UnifiedSkillsExtractor  # Enhanced name