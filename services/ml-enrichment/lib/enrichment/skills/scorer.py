"""
Confidence scoring for extracted skills.
"""

from .config import SkillsConfig


class SkillScorer:
    """Calculates confidence scores for extracted skills."""
    
    def __init__(self, config: SkillsConfig):
        """
        Initialize scorer with configuration.
        
        Args:
            config: Skills extraction configuration
        """
        self.config = config
    
    def calculate_confidence(self, text: str, skill: str, context: str) -> float:
        """
        Calculate confidence score based on context and frequency.
        
        Args:
            text: Full text where skill was found
            skill: The skill name
            context: Context snippet around the skill
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        text_lower = text.lower()
        skill_lower = skill.lower()
        context_lower = context.lower()
        
        weights = self.config.confidence_weights
        
        # Base confidence
        confidence = weights.base_score
        
        # Boost for frequency
        mentions = text_lower.count(skill_lower)
        frequency_boost = min(
            mentions * weights.frequency_boost_per_mention,
            weights.max_frequency_boost
        )
        confidence += frequency_boost
        
        # Boost for context indicators
        for indicator in self.config.strong_indicators:
            if indicator in context_lower:
                confidence += weights.strong_indicator_boost
                break
        
        for indicator in self.config.medium_indicators:
            if indicator in context_lower:
                confidence += weights.medium_indicator_boost
                break
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def extract_context(self, text: str, keyword: str) -> str:
        """
        Extract surrounding context for a keyword.
        
        Args:
            text: Full text
            keyword: Keyword to find context for
            
        Returns:
            Context snippet with ellipsis markers
        """
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        pos = text_lower.find(keyword_lower)
        if pos == -1:
            return ""
        
        window = self.config.context_window
        start = max(0, pos - window)
        end = min(len(text), pos + len(keyword) + window)
        
        context = text[start:end]
        
        # Add ellipsis markers
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        
        return context.strip()
