"""
Text normalization utilities for skills extraction.
"""

import re
import html
from html.parser import HTMLParser
from typing import Any


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


class TextNormalizer:
    """Handles text normalization and cleaning for skill extraction."""
    
    def __init__(self, nlp):
        """
        Initialize normalizer with spaCy model.
        
        Args:
            nlp: Loaded spaCy model instance
        """
        self.nlp = nlp
    
    @staticmethod
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
    
    def normalize_skill_text(self, text: str, span: Any) -> str:
        """
        Normalize skill text with proper preprocessing:
        - Remove stop words and determiners
        - Lemmatize tokens
        - Fix concatenated words
        - Title case the result
        - Remove HTML entities and special chars
        
        Args:
            text: Raw skill text
            span: spaCy span object for additional context
            
        Returns:
            Normalized skill text or empty string if invalid
        """
        # Fix common concatenation issues (add space before capitals)
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # Remove leading/trailing punctuation and whitespace
        text = text.strip().strip('/:,.-')
        
        # Skip if too short or just punctuation
        if len(text) < 2 or text.isspace() or not any(c.isalnum() for c in text):
            return ""
        
        # Process the text
        doc = self.nlp(text)
        
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
        result = self.smart_title_case(normalized)
        
        return result
    
    @staticmethod
    def smart_title_case(text: str) -> str:
        """
        Smart title case that preserves acronyms and special formatting.
        
        Args:
            text: Text to title case
            
        Returns:
            Title-cased text with acronyms preserved
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

    def normalize_skill(self, skill_text: str) -> str:
        """
        Simple skill normalization for basic string inputs.
        
        This is a simpler version of normalize_skill_text for cases where
        we don't have a spaCy span object.
        
        Args:
            skill_text: Raw skill text string
            
        Returns:
            Normalized skill text
        """
        if not skill_text or not isinstance(skill_text, str):
            return ""
            
        # Basic cleaning
        skill_text = skill_text.strip()
        if len(skill_text) < 2:
            return ""
            
        # Fix common concatenation issues (add space before capitals)
        skill_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', skill_text)
        
        # Remove leading/trailing punctuation and whitespace
        skill_text = skill_text.strip().strip('/:,.-')
        
        # Process with spaCy
        doc = self.nlp(skill_text)
        
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
            return skill_text.strip()  # Return original if no tokens left
        
        # Join and title case
        normalized = ' '.join(cleaned_tokens)
        result = self.smart_title_case(normalized)
        
        return result
