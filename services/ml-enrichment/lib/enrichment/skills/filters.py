"""
Filtering logic for skills extraction.
"""

import re
from typing import List, Dict
from .config import SkillsConfig


class SkillFilter:
    """Filters to determine if text is likely a skill."""
    
    def __init__(self, config: SkillsConfig):
        """
        Initialize filter with configuration.
        
        Args:
            config: Skills extraction configuration
        """
        self.config = config
    
    def is_likely_skill(self, text: str) -> bool:
        """
        Check if entity is likely a skill/tool/technology.
        
        Args:
            text: Text to evaluate
            
        Returns:
            True if likely a skill, False otherwise
        """
        text_lower = text.lower()
        
        # Length check
        if len(text) < self.config.filter_config.min_skill_length or \
           len(text) > self.config.filter_config.max_skill_length:
            return False
        
        # Filter out common non-skill patterns
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
        if text_lower in self.config.non_skill_phrases:
            return False
        
        # Filter out generic phrases starting with common words
        if text_lower.startswith(('we are', 'you will', 'you are', 'we offer', 'our team')):
            return False
        
        return True
    
    def is_skill_chunk(self, chunk) -> bool:
        """
        Check if noun chunk looks like a skill.
        
        Args:
            chunk: spaCy noun chunk
            
        Returns:
            True if looks like a skill, False otherwise
        """
        chunk_text = chunk.text.lower()
        
        # Length check
        if len(chunk.text) < self.config.filter_config.min_skill_length or \
           len(chunk.text) > self.config.filter_config.max_skill_length:
            return False
        
        # Must be 2-4 words long
        if not (self.config.filter_config.min_chunk_words <= len(chunk) <= self.config.filter_config.max_chunk_words):
            return False
        
        # Filter out generic phrases
        if chunk_text in {'new york', 'san francisco', 'team player', 'fast paced', 'work environment'}:
            return False
        
        # Look for verb-like words (especially -ing forms)
        has_verb = any(token.pos_ == 'VERB' or token.tag_ == 'VBG' for token in chunk)
        
        # Look for skill-related nouns
        has_skill_noun = any(token.lemma_ in self.config.skill_nouns for token in chunk)
        
        # Look for technical terms (often capitalized or have specific patterns)
        has_technical_term = any(
            token.text[0].isupper() and len(token.text) > 2 
            for token in chunk if not token.is_stop
        )
        
        return (has_verb or has_skill_noun or has_technical_term)


class SectionFilter:
    """Filters job description sections to identify skill-relevant content."""
    
    def __init__(self, config: SkillsConfig):
        """
        Initialize section filter with configuration.
        
        Args:
            config: Skills extraction configuration
        """
        self.config = config
    
    def identify_skill_relevant_sections(self, text: str) -> List[Dict[str, str]]:
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
        for keyword in self.config.skill_relevant_sections:
            pos = text_lower.find(keyword)
            if pos != -1:
                section_markers.append((pos, keyword, 'relevant'))
        
        # Find excluded sections
        for keyword in self.config.excluded_sections:
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
            if len(section_content) < self.config.filter_config.min_section_length:
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
                    if len(section['content']) > self.config.filter_config.fallback_section_length:
                        relevant_sections.append(section)
        
        # If still no relevant sections, use all sections
        if not relevant_sections:
            relevant_sections = sections if sections else [{'type': 'full_text', 'content': text, 'relevant': True}]
        
        return relevant_sections
