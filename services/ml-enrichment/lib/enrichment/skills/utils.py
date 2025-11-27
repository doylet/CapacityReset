"""
Utilities for loading spaCy model and skills lexicon.
"""

import spacy
from typing import Optional, Dict, List
from spacy.matcher import PhraseMatcher
from google.cloud import bigquery
from .config import SkillsConfig

# Global caches for lazy loading
_nlp = None
_phrase_matcher = None


def get_nlp():
    """
    Lazy load spaCy model.
    
    Returns:
        Loaded spaCy model
    """
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


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
