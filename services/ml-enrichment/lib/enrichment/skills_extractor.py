"""
Skills Extractor Module

Extracts skills from job postings using unsupervised NLP approach:
- Named Entity Recognition (NER) with spaCy
- Phrase matching against a skills lexicon (175 general skills)
- Context-aware confidence scoring

No hardcoded supervised keywords - discovers skills from job text.
"""

import spacy
import uuid
import json
import re
import html
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from google.cloud import bigquery
from spacy.matcher import PhraseMatcher
from html.parser import HTMLParser

# Don't load model at module level - lazy load instead
_nlp = None
_phrase_matcher = None


class HTMLStripper(HTMLParser):
    """Simple HTML tag stripper."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ''.join(self.text)


def strip_html(html_text: str) -> str:
    """
    Strip HTML tags from text, keeping only the content.
    Also decodes HTML entities like &lt; &gt; &amp; etc.
    
    Args:
        html_text: HTML-formatted text
        
    Returns:
        Plain text with HTML tags removed and entities decoded
    """
    if not html_text:
        return ""
    
    # Use HTMLParser to strip tags
    stripper = HTMLStripper()
    try:
        stripper.feed(html_text)
        text = stripper.get_text()
    except Exception:
        # Fallback to regex if parser fails
        text = re.sub(r'<[^>]+>', ' ', html_text)
    
    # Decode HTML entities (&lt; &gt; &amp; &nbsp; etc.)
    text = html.unescape(text)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def get_nlp():
    """Lazy load spaCy model."""
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp

def get_phrase_matcher(nlp):
    """Lazy load phrase matcher with skills lexicon."""
    global _phrase_matcher
    if _phrase_matcher is None:
        _phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        
        # Load skills lexicon from embedded data
        skills_lexicon = SKILLS_LEXICON
        
        # Add patterns for each skill
        for category, skills in skills_lexicon.items():
            patterns = [nlp.make_doc(skill) for skill in skills]
            _phrase_matcher.add(category, patterns)
    
    return _phrase_matcher

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


class SkillsExtractor:
    """Extract skills from job descriptions using unsupervised NLP."""
    
    def __init__(self):
        self.version = "v2.2-unsupervised-ner-lexicon-entities-decoded"
        self.bigquery_client = bigquery.Client()
        self.project_id = "sylvan-replica-478802-p4"
        self.dataset_id = f"{self.project_id}.brightdata_jobs"
    
    def get_version(self) -> str:
        """Return extractor version identifier."""
        return self.version
    
    def extract_skills(self, job_summary: str, job_description: str) -> List[Dict[str, Any]]:
        """
        Extract skills using unsupervised NLP approach:
        1. Use spaCy NER to identify entities (organizations, products, skills)
        2. Use phrase matcher against skills lexicon (175 general skills)
        3. Extract noun chunks that look skill-like
        4. Calculate confidence based on context, frequency, and source
        
        Args:
            job_summary: Brief job summary
            job_description: Full job description
            
        Returns:
            List of skill dictionaries with name, category, confidence, context
        """
        nlp = get_nlp()
        phrase_matcher = get_phrase_matcher(nlp)
        
        skills = []
        
        # Strip HTML from job description before processing
        job_description_clean = strip_html(job_description) if job_description else ''
        
        # Combine texts for analysis
        texts = {
            'job_summary': job_summary or '',
            'job_description_formatted': job_description_clean
        }
        
        for source_field, text in texts.items():
            if not text:
                continue
            
            # Process with spaCy
            doc = nlp(text)
            
            # 1. Extract skills from lexicon using phrase matcher
            lexicon_skills = self._extract_lexicon_skills(doc, phrase_matcher, text, source_field)
            skills.extend(lexicon_skills)
            
            # 2. Extract named entities (PRODUCT, ORG, SKILL)
            entity_skills = self._extract_entity_skills(doc, text, source_field)
            skills.extend(entity_skills)
            
            # 3. Extract skill-like noun chunks (verbs + -ing forms)
            chunk_skills = self._extract_noun_chunk_skills(doc, text, source_field)
            skills.extend(chunk_skills)
        
        # Deduplicate skills (keep highest confidence)
        unique_skills = {}
        for skill in skills:
            key = (skill['skill_name'].lower(), skill['skill_category'])
            if key not in unique_skills or skill['confidence_score'] > unique_skills[key]['confidence_score']:
                unique_skills[key] = skill
        
        return list(unique_skills.values())
    
    def _extract_lexicon_skills(
        self, doc, phrase_matcher, text: str, source_field: str
    ) -> List[Dict[str, Any]]:
        """Extract skills that match the skills lexicon."""
        skills = []
        matches = phrase_matcher(doc)
        
        for match_id, start, end in matches:
            # Get the matched span
            span = doc[start:end]
            category = doc.vocab.strings[match_id]
            skill_text = span.text
            
            # Extract context
            context = self._extract_context(text, skill_text)
            
            # Calculate confidence
            confidence = self._calculate_confidence(text, skill_text, context)
            
            skills.append({
                'skill_name': skill_text.title(),
                'skill_category': category,
                'source_field': source_field,
                'confidence_score': confidence,
                'context_snippet': context,
                'extraction_method': 'lexicon_match'
            })
        
        return skills
    
    def _extract_entity_skills(
        self, doc, text: str, source_field: str
    ) -> List[Dict[str, Any]]:
        """Extract skills from named entities (PRODUCT, ORG, SKILL-like)."""
        skills = []
        
        # Look for entities that might be skills/tools/technologies
        for ent in doc.ents:
            # Focus on PRODUCT, ORG entities that are likely tools/tech
            if ent.label_ in ['PRODUCT', 'ORG', 'GPE']:
                skill_text = ent.text
                
                # Filter out obviously non-skill entities
                if self._is_likely_skill(skill_text):
                    context = self._extract_context(text, skill_text)
                    confidence = self._calculate_confidence(text, skill_text, context) * 0.7
                    
                    skills.append({
                        'skill_name': skill_text.title(),
                        'skill_category': 'technical_skills',
                        'source_field': source_field,
                        'confidence_score': confidence,
                        'context_snippet': context,
                        'extraction_method': 'ner'
                    })
        
        return skills
    
    def _extract_noun_chunk_skills(
        self, doc, text: str, source_field: str
    ) -> List[Dict[str, Any]]:
        """Extract skill-like noun chunks (e.g., 'project management', 'data analysis')."""
        skills = []
        
        for chunk in doc.noun_chunks:
            # Look for chunks with skill-like patterns
            if self._is_skill_chunk(chunk):
                skill_text = chunk.text
                context = self._extract_context(text, skill_text)
                confidence = self._calculate_confidence(text, skill_text, context) * 0.6
                
                # Try to categorize based on verbs
                category = self._categorize_chunk(chunk)
                
                skills.append({
                    'skill_name': skill_text.title(),
                    'skill_category': category,
                    'source_field': source_field,
                    'confidence_score': confidence,
                    'context_snippet': context,
                    'extraction_method': 'noun_chunk'
                })
        
        return skills
    
    def _is_likely_skill(self, text: str) -> bool:
        """Check if entity is likely a skill/tool/technology."""
        text_lower = text.lower()
        
        # Filter out common non-skill entities
        exclude_patterns = [
            r'^(the|a|an)\s',
            r'^\d+$',
            r'^[A-Z]{2}$',
        ]
        
        for pattern in exclude_patterns:
            if re.match(pattern, text_lower):
                return False
        
        return len(text) > 2
    
    def _is_skill_chunk(self, chunk) -> bool:
        """Check if noun chunk looks like a skill."""
        # Look for verb-like words (especially -ing forms)
        has_verb = any(token.pos_ == 'VERB' or token.tag_ == 'VBG' for token in chunk)
        
        # Look for skill-related nouns
        skill_nouns = {'management', 'analysis', 'development', 'design', 'engineering', 
                       'leadership', 'communication', 'planning', 'strategy'}
        has_skill_noun = any(token.lemma_ in skill_nouns for token in chunk)
        
        # Must be 2-4 words long
        is_reasonable_length = 2 <= len(chunk) <= 4
        
        return (has_verb or has_skill_noun) and is_reasonable_length
    
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
    
    def _calculate_confidence(self, text: str, skill: str, context: str) -> float:
        """Calculate confidence score based on context and frequency."""
        text_lower = text.lower()
        skill_lower = skill.lower()
        context_lower = context.lower()
        
        # Base confidence
        confidence = 0.5
        
        # Boost for frequency
        mentions = text_lower.count(skill_lower)
        confidence += min(mentions * 0.1, 0.3)
        
        # Boost for context indicators
        strong_indicators = ['required', 'must have', 'essential', 'proficient', 'expert']
        medium_indicators = ['experience', 'knowledge', 'familiar', 'understanding', 'ability']
        
        for indicator in strong_indicators:
            if indicator in context_lower:
                confidence += 0.2
                break
        
        for indicator in medium_indicators:
            if indicator in context_lower:
                confidence += 0.1
                break
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _extract_context(self, text: str, keyword: str, window: int = 50) -> str:
        """Extract surrounding context for a keyword."""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        pos = text_lower.find(keyword_lower)
        if pos == -1:
            return ""
        
        start = max(0, pos - window)
        end = min(len(text), pos + len(keyword) + window)
        
        context = text[start:end]
        
        # Clean up
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        
        return context.strip()
    
    def store_skills(self, job_posting_id: str, enrichment_id: str, skills: List[Dict[str, Any]]):
        """
        Store extracted skills in BigQuery.
        
        Args:
            job_posting_id: Job reference
            enrichment_id: Enrichment tracking reference
            skills: List of extracted skills
        """
        if not skills:
            return
        
        rows = []
        for skill in skills:
            rows.append({
                'skill_id': str(uuid.uuid4()),
                'job_posting_id': job_posting_id,
                'enrichment_id': enrichment_id,
                'skill_name': skill['skill_name'],
                'skill_category': skill['skill_category'],
                'source_field': skill['source_field'],
                'confidence_score': skill['confidence_score'],
                'context_snippet': skill['context_snippet'],
                'created_at': datetime.utcnow().isoformat()
            })
        
        table_id = f"{self.dataset_id}.job_skills"
        errors = self.bigquery_client.insert_rows_json(table_id, rows)
        
        if errors:
            raise Exception(f"Failed to store skills: {errors}")
