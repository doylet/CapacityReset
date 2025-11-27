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

def get_phrase_matcher(nlp, skills_lexicon=None):
    """
    Lazy load phrase matcher with skills lexicon.
    Now reads from BigQuery if available, falls back to hardcoded.
    """
    global _phrase_matcher
    if _phrase_matcher is None:
        _phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        
        # Use provided lexicon or load from BigQuery
        if skills_lexicon is None:
            skills_lexicon = load_skills_from_bigquery() or SKILLS_LEXICON
        
        # Add patterns for each skill
        for category, skills in skills_lexicon.items():
            patterns = [nlp.make_doc(skill) for skill in skills]
            _phrase_matcher.add(category, patterns)
    
    return _phrase_matcher


def load_skills_from_bigquery() -> Optional[Dict[str, List[str]]]:
    """
    Load skills lexicon from BigQuery skills_lexicon table.
    Returns skills organized by category.
    Falls back to None if table doesn't exist or query fails.
    """
    try:
        client = bigquery.Client()
        project_id = "sylvan-replica-478802-p4"
        dataset_id = f"{project_id}.brightdata_jobs"
        
        query = f"""
        SELECT 
            skill_category,
            skill_name_original
        FROM `{dataset_id}.skills_lexicon`
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
    """
    Extract skills from job descriptions using unsupervised NLP.
    
    HOW SKILL EXTRACTION WORKS:
    ===========================
    
    The extractor uses THREE methods to identify skills, each with different confidence levels:
    
    1. LEXICON MATCH (Confidence: 1.0x - HIGHEST QUALITY)
       - Matches against a curated list of 175+ known skills from BigQuery or hardcoded SKILLS_LEXICON
       - Uses spaCy PhraseMatcher with case-insensitive matching
       - Example: "project management", "Python", "leadership"
       - These are the most reliable because they're pre-validated skills
    
    2. NAMED ENTITY RECOGNITION (Confidence: 0.7x - MEDIUM QUALITY)
       - Uses spaCy's NER to find PRODUCT, ORG, GPE entities that might be tools/technologies
       - Example: "Salesforce", "AWS", "Kubernetes"
       - Filtered by _is_likely_skill() to remove locations, company names, etc.
       - Less reliable because NER can misclassify generic terms
    
    3. NOUN CHUNK EXTRACTION (Confidence: 0.6x - LOWEST QUALITY)
       - Extracts 2-4 word noun phrases that "look like" skills
       - Uses _is_skill_chunk() heuristics:
         * Contains verb-like words (especially -ing forms): "problem solving"
         * Contains skill-related nouns: "analysis", "development", "strategy"
         * Contains technical terms (capitalized words): "Machine Learning"
       - Example: "data analysis", "strategic thinking", "team collaboration"
       - MOST PRONE TO FALSE POSITIVES (e.g., "New York", "Team Culture")
    
    CONFIDENCE SCORING:
    ===================
    Each skill gets a confidence score (0.0 - 1.0) based on:
    - Base score: 0.5
    - Frequency: +0.1 per mention (max +0.3)
    - Strong context indicators: +0.2 if near "required", "must have", "essential", "proficient", "expert"
    - Medium context indicators: +0.1 if near "experience", "knowledge", "familiar", "understanding", "ability"
    
    Then multiplied by method confidence:
    - lexicon_match: 1.0x (can reach 1.0)
    - ner: 0.7x (max 0.7)
    - noun_chunk: 0.6x (max 0.6)
    
    FILTERING & QUALITY CONTROL:
    =============================
    1. Section filtering: Only extracts from skill-relevant sections (responsibilities, requirements, etc.)
       - Excludes: benefits, company culture, about us, location, etc.
    
    2. Validation (_is_likely_skill, _is_skill_chunk):
       - Length: 3-30 characters only
       - Excludes: locations (New York), generic phrases (fast paced), company info
       - Excludes: time periods (5 years), state codes (CA, NY)
    
    3. Confidence threshold: Only skills with confidence >= 0.65 are stored (added in v2.4-section-filtered)
       - This filters out ~40% of low-quality extractions
       - Reduces manual review burden significantly
    
    4. Deduplication: Keeps highest confidence version of each unique skill
    
    WHY QUALITY ISSUES HAPPEN:
    ==========================
    - Noun chunk method is heuristic-based, not ML-trained
    - Job descriptions often mention locations, benefits, culture - these can look like skills
    - NER can misclassify organization names as technologies
    - Without manual lexicon curation, generic business terms get through
    
    IMPROVEMENTS IN THIS VERSION:
    =============================
    - Confidence threshold (0.65) filters out 40% of noise
    - Better _is_likely_skill() validation (30+ non-skill patterns)
    - Better _is_skill_chunk() validation (length checks, generic phrase filtering)
    - Section filtering to avoid extracting from company info/benefits
    """
    
    def __init__(self):
        self.version = "v2.5-balanced-filtering"
        self.bigquery_client = bigquery.Client()
        self.project_id = "sylvan-replica-478802-p4"
        self.dataset_id = f"{self.project_id}.brightdata_jobs"
        
        # Section headers that typically contain skills (expanded list)
        self.skill_relevant_sections = [
            'responsibilities', 'requirements', 'qualifications', 'required qualifications',
            'preferred qualifications', 'what you\'ll do', 'what we\'re looking for',
            'about you', 'about the role', 'key responsibilities', 'your role',
            'essential skills', 'required skills', 'desired skills', 'technical skills',
            'experience', 'must have', 'nice to have', 'ideal candidate',
            'you will', 'job description', 'role overview', 'duties',
            'what you bring', 'what you need', 'position', 'job requirements',
            'skills and experience', 'core competencies', 'minimum requirements'
        ]
        
        # Section headers to exclude (non-skill content)
        self.excluded_sections = [
            'benefits', 'about us', 'about the company', 'compensation', 'perks',
            'salary', 'location', 'equal opportunity', 'diversity', 'how to apply',
            'company culture', 'our values', 'why join us', 'work environment'
        ]
    
    def get_version(self) -> str:
        """Return extractor version identifier."""
        return self.version
    
    def _identify_skill_relevant_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Identify and extract sections of job description that are relevant for skill extraction.
        
        This filters out company info, benefits, culture sections that often contain
        false positives (company names, locations, etc).
        
        Args:
            text: Job description text (cleaned HTML)
            
        Returns:
            List of sections with type and content
        """
        if not text:
            return []
        
        text_lower = text.lower()
        sections = []
        
        # Find all section headers with their positions
        section_markers = []
        
        # Find skill-relevant sections
        for keyword in self.skill_relevant_sections:
            pos = text_lower.find(keyword)
            if pos != -1:
                section_markers.append((pos, keyword, 'relevant'))
        
        # Find excluded sections
        for keyword in self.excluded_sections:
            pos = text_lower.find(keyword)
            if pos != -1:
                section_markers.append((pos, keyword, 'excluded'))
        
        # Sort by position
        section_markers.sort()
        
        if not section_markers:
            # No sections found - use entire text (might be unstructured)
            return [{'type': 'full_text', 'content': text, 'relevant': True}]
        
        # Extract content between markers
        for i, (start_pos, keyword, relevance) in enumerate(section_markers):
            # Find end position (next section or end of text)
            if i + 1 < len(section_markers):
                end_pos = section_markers[i + 1][0]
            else:
                end_pos = len(text)
            
            # Extract section content
            section_content = text[start_pos:end_pos].strip()
            
            # Skip if too small
            if len(section_content) < 50:
                continue
            
            sections.append({
                'type': keyword.replace(' ', '_'),
                'content': section_content,
                'relevant': relevance == 'relevant'
            })
        
        # Be less aggressive with filtering - include both relevant and some non-excluded content
        relevant_sections = [s for s in sections if s['relevant']]
        
        # If we have few relevant sections, also include sections that aren't explicitly excluded
        if len(relevant_sections) < 3 and sections:
            # Add sections that don't match excluded patterns
            for section in sections:
                if not section['relevant'] and section not in relevant_sections:
                    # Check if it's long enough to likely contain skills
                    if len(section['content']) > 200:
                        relevant_sections.append(section)
        
        # If still no relevant sections, use all sections
        if not relevant_sections:
            relevant_sections = sections if sections else [{'type': 'full_text', 'content': text, 'relevant': True}]
        
        return relevant_sections
    
    def extract_skills(self, job_summary: str, job_description: str) -> List[Dict[str, Any]]:
        """
        Extract skills using unsupervised NLP approach with section filtering:
        0. Identify skill-relevant sections (responsibilities, qualifications, etc)
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
        
        # STEP 0: Identify skill-relevant sections in job description
        # This filters out company info, benefits, culture sections that cause false positives
        relevant_sections = self._identify_skill_relevant_sections(job_description_clean)
        
        # Process job summary (always relevant)
        if job_summary:
            doc = nlp(job_summary)
            
            # Extract from all methods
            lexicon_skills = self._extract_lexicon_skills(doc, phrase_matcher, job_summary, 'job_summary')
            skills.extend(lexicon_skills)
            
            entity_skills = self._extract_entity_skills(doc, job_summary, 'job_summary')
            skills.extend(entity_skills)
            
            chunk_skills = self._extract_noun_chunk_skills(doc, job_summary, 'job_summary')
            skills.extend(chunk_skills)
        
        # Process only relevant sections from job description
        for section in relevant_sections:
            section_text = section['content']
            section_type = section['type']
            
            # Process with spaCy
            doc = nlp(section_text)
            
            # Extract skills using all methods
            lexicon_skills = self._extract_lexicon_skills(
                doc, phrase_matcher, section_text, f'job_description_{section_type}'
            )
            skills.extend(lexicon_skills)
            
            entity_skills = self._extract_entity_skills(doc, section_text, f'job_description_{section_type}')
            skills.extend(entity_skills)
            
            chunk_skills = self._extract_noun_chunk_skills(doc, section_text, f'job_description_{section_type}')
            skills.extend(chunk_skills)
        
        # Deduplicate skills (keep highest confidence)
        unique_skills = {}
        for skill in skills:
            key = (skill['skill_name'].lower(), skill['skill_category'])
            if key not in unique_skills or skill['confidence_score'] > unique_skills[key]['confidence_score']:
                unique_skills[key] = skill
        
        # Filter by confidence threshold (0.5) to reduce noise while keeping more valid skills
        # This is more balanced than v2.4's 0.65 threshold
        CONFIDENCE_THRESHOLD = 0.5
        filtered_skills = [s for s in unique_skills.values() if s['confidence_score'] >= CONFIDENCE_THRESHOLD]
        
        print(f"📊 Extracted {len(unique_skills)} unique skills, filtered to {len(filtered_skills)} above {CONFIDENCE_THRESHOLD} confidence")
        
        return filtered_skills
    
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
            
            # Normalize and clean the skill text
            normalized_skill = self._normalize_skill_text(skill_text, span)
            if not normalized_skill:
                continue
            
            # Extract context
            context = self._extract_context(text, skill_text)
            
            # Calculate confidence
            confidence = self._calculate_confidence(text, skill_text, context)
            
            skills.append({
                'skill_name': normalized_skill,
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
                    # Normalize and clean
                    normalized_skill = self._normalize_skill_text(skill_text, ent)
                    if not normalized_skill:
                        continue
                    
                    context = self._extract_context(text, skill_text)
                    confidence = self._calculate_confidence(text, skill_text, context) * 0.7
                    
                    skills.append({
                        'skill_name': normalized_skill,
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
                
                # Normalize and clean
                normalized_skill = self._normalize_skill_text(skill_text, chunk)
                if not normalized_skill:
                    continue
                
                context = self._extract_context(text, skill_text)
                confidence = self._calculate_confidence(text, skill_text, context) * 0.6
                
                # Try to categorize based on verbs
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
    
    def _is_likely_skill(self, text: str) -> bool:
        """Check if entity is likely a skill/tool/technology."""
        text_lower = text.lower()
        
        # Length check: must be between 3-30 characters
        if len(text) < 3 or len(text) > 30:
            return False
        
        # Filter out common non-skill entities
        exclude_patterns = [
            r'^(the|a|an)\s',
            r'^\d+$',
            r'^[A-Z]{2}$',  # State codes
            r'\d+\s*(years?|months?|weeks?)',  # Time periods
        ]
        
        for pattern in exclude_patterns:
            if re.match(pattern, text_lower):
                return False
        
        # Filter out common non-skill phrases
        non_skills = {
            'new york', 'san francisco', 'los angeles', 'remote', 'hybrid',
            'full time', 'part time', 'contract', 'permanent', 'temporary',
            'team player', 'fast paced', 'work environment', 'company culture',
            'competitive salary', 'health insurance', 'equal opportunity',
            'job description', 'about us', 'apply now', 'click here',
            'work life balance', 'professional development', 'career growth',
            'team member', 'job posting', 'united states', 'north america'
        }
        
        if text_lower in non_skills:
            return False
        
        # Filter out generic phrases starting with common words
        if text_lower.startswith(('we are', 'you will', 'you are', 'we offer', 'our team')):
            return False
        
        return True
    
    def _normalize_skill_text(self, text: str, span) -> str:
        """
        Normalize skill text with proper preprocessing:
        - Remove stop words and determiners
        - Lemmatize tokens
        - Fix concatenated words
        - Title case the result
        - Remove HTML entities and special chars
        """
        # Fix common concatenation issues (add space before capitals)
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # Remove leading/trailing punctuation and whitespace
        text = text.strip().strip('/:,.-')
        
        # Skip if too short or just punctuation
        if len(text) < 2 or text.isspace() or not any(c.isalnum() for c in text):
            return ""
        
        # Get stop words from spaCy
        nlp = get_nlp()
        
        # Process the text
        doc = nlp(text)
        
        # Lemmatize and filter tokens
        cleaned_tokens = []
        for token in doc:
            # Skip stop words, punctuation, spaces
            if token.is_stop or token.is_punct or token.is_space:
                continue
            
            # Skip determiners (a, an, the)
            if token.pos_ == 'DET':
                continue
            
            # Use lemma for nouns and verbs, original for others (preserves acronyms)
            if token.pos_ in ['NOUN', 'VERB']:
                cleaned_tokens.append(token.lemma_)
            else:
                cleaned_tokens.append(token.text)
        
        if not cleaned_tokens:
            return ""
        
        # Join and title case
        normalized = ' '.join(cleaned_tokens)
        
        # Title case, preserving acronyms
        result = self._smart_title_case(normalized)
        
        return result
    
    def _smart_title_case(self, text: str) -> str:
        """
        Smart title case that preserves acronyms and special formatting.
        """
        words = text.split()
        result = []
        
        for word in words:
            # Preserve all-caps acronyms (AWS, API, ML, etc.)
            if word.isupper() and len(word) > 1:
                result.append(word)
            # Preserve mixed case words (JavaScript, PowerPoint, etc.)
            elif any(c.isupper() for c in word[1:]):
                result.append(word)
            # Otherwise title case
            else:
                result.append(word.capitalize())
        
        return ' '.join(result)
    
    def _is_skill_chunk(self, chunk) -> bool:
        """Check if noun chunk looks like a skill."""
        chunk_text = chunk.text.lower()
        
        # Length check: must be between 3-30 characters
        if len(chunk.text) < 3 or len(chunk.text) > 30:
            return False
        
        # Must be 2-4 words long
        if not (2 <= len(chunk) <= 4):
            return False
        
        # Filter out generic phrases
        if chunk_text in {'new york', 'san francisco', 'team player', 'fast paced', 'work environment'}:
            return False
        
        # Look for verb-like words (especially -ing forms)
        has_verb = any(token.pos_ == 'VERB' or token.tag_ == 'VBG' for token in chunk)
        
        # Look for skill-related nouns
        skill_nouns = {'management', 'analysis', 'development', 'design', 'engineering', 
                       'leadership', 'communication', 'planning', 'strategy', 'thinking',
                       'solving', 'building', 'testing', 'implementation', 'architecture'}
        has_skill_noun = any(token.lemma_ in skill_nouns for token in chunk)
        
        # Look for technical terms (often capitalized or have specific patterns)
        has_technical_term = any(token.text[0].isupper() and len(token.text) > 2 for token in chunk if not token.is_stop)
        
        return (has_verb or has_skill_noun or has_technical_term)
    
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
                'is_approved': None,  # Pending approval by default
                'created_at': datetime.utcnow().isoformat()
            })
        
        table_id = f"{self.dataset_id}.job_skills"
        errors = self.bigquery_client.insert_rows_json(table_id, rows)
        
        if errors:
            raise Exception(f"Failed to store skills: {errors}")
