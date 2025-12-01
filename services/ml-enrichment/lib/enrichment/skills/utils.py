"""
Utilities for loading spaCy model and skills lexicon with enhanced features.
"""

import spacy
from typing import Optional, Dict, List, Union
from spacy.matcher import PhraseMatcher
from google.cloud import bigquery
from .config import SkillsConfig

# Import enhanced config if available
try:
    from .enhanced_config import EnhancedSkillsConfig
    ENHANCED_AVAILABLE = True
except ImportError:
    EnhancedSkillsConfig = None
    ENHANCED_AVAILABLE = False

# Global caches for lazy loading
_nlp = None
_phrase_matcher = None
_enhanced_phrase_matcher = None


def get_nlp():
    """
    Lazy load spaCy model.
    
    Returns:
        Loaded spaCy model
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback to basic model if specific model not found
            try:
                _nlp = spacy.load("en")
            except OSError:
                # Last resort - create blank model
                _nlp = spacy.blank("en")
                print("Warning: Using blank spaCy model. Install 'en_core_web_sm' for better performance.")
    return _nlp


def get_enhanced_phrase_matcher(nlp, config: Union[SkillsConfig, 'EnhancedSkillsConfig']):
    """
    Create enhanced phrase matcher with comprehensive tech skills.
    
    Args:
        nlp: spaCy model instance
        config: Configuration (enhanced or regular)
        
    Returns:
        Configured PhraseMatcher with enhanced skills
    """
    global _enhanced_phrase_matcher
    
    if _enhanced_phrase_matcher is None:
        _enhanced_phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        
        # Determine which lexicon to use
        if hasattr(config, 'enhanced_skills_lexicon') and config.enhanced_skills_lexicon:
            lexicon = config.enhanced_skills_lexicon
            print(f"✅ Using enhanced skills lexicon with {sum(len(v) for v in lexicon.values())} skills")
        else:
            # Fall back to regular lexicon
            lexicon = getattr(config, 'skills_lexicon', {})
            print(f"⚠️  Falling back to regular lexicon with {sum(len(v) for v in lexicon.values())} skills")
        
        # Add patterns for each category
        for category, skills in lexicon.items():
            if skills:  # Only add non-empty categories
                try:
                    patterns = [nlp.make_doc(skill) for skill in skills]
                    _enhanced_phrase_matcher.add(category, patterns)
                except Exception as e:
                    print(f"Warning: Failed to add category {category}: {e}")
    
    return _enhanced_phrase_matcher


def load_skills_from_bigquery(config: SkillsConfig) -> Optional[Dict[str, List[str]]]:
    """
    Load skills lexicon from BigQuery skills_lexicon table.
    Returns skills organized by category.
    Falls back to None if table doesn't exist or query fails.
    
    Args:
        config: Configuration with BigQuery settings
        
    Returns:
        Skills dictionary or None on failure
    """
    try:
        client = bigquery.Client()
        
        query = f"""
        SELECT 
            skill_category,
            skill_name_original
        FROM `{config.full_dataset_id}.skills_lexicon`
        ORDER BY skill_category, usage_count DESC
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        # Organize by category
        lexicon_dict = {}
        for row in results:
            category = row['skill_category']
            skill = row['skill_name_original']
            
            if category not in lexicon_dict:
                lexicon_dict[category] = []
            lexicon_dict[category].append(skill)
        
        print(f"✅ Loaded {sum(len(v) for v in lexicon_dict.values())} skills from BigQuery lexicon")
        return lexicon_dict
        
    except Exception as e:
        print(f"⚠️  Could not load skills from BigQuery: {e}")
        print(f"   Falling back to hardcoded SKILLS_LEXICON")
        return None


def get_phrase_matcher(nlp, config: SkillsConfig, skills_lexicon: Optional[Dict[str, List[str]]] = None):
    """
    Lazy load phrase matcher with skills lexicon.
    Now reads from BigQuery if available, falls back to hardcoded.
    
    Args:
        nlp: spaCy model instance
        config: Configuration
        skills_lexicon: Optional pre-loaded skills lexicon
        
    Returns:
        Configured PhraseMatcher
    """
    global _phrase_matcher
    if _phrase_matcher is None:
        _phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        
        # Use provided lexicon or load from BigQuery or use config default
        if skills_lexicon is None:
            skills_lexicon = load_skills_from_bigquery(config) or config.skills_lexicon
        
        # Add patterns for each skill
        for category, skills in skills_lexicon.items():
            patterns = [nlp.make_doc(skill) for skill in skills]
            _phrase_matcher.add(category, patterns)
    
    return _phrase_matcher
