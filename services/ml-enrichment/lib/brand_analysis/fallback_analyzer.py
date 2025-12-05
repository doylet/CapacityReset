"""
Fallback Analyzer for Keyword-Based Brand Analysis

Provides deterministic analysis when LLM is unavailable.
Maintains service reliability per constitution principles.
"""

import re
import logging
from typing import List, Dict, Any
from collections import Counter

from ...domain.entities import LLMThemeResult, LLMVoiceCharacteristics, LLMNarrativeArc


class FallbackAnalyzer:
    """
    Keyword-based fallback analyzer for brand analysis.
    
    Provides basic analysis using pattern matching and heuristics
    when Vertex AI LLM is unavailable.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Professional theme keywords
        self.theme_patterns = {
            "leadership": [
                "led", "managed", "coordinated", "directed", "supervised", 
                "mentored", "guided", "oversaw", "spearheaded", "orchestrated"
            ],
            "technical_expertise": [
                "developed", "implemented", "designed", "built", "programmed",
                "engineered", "architected", "optimized", "automated", "debugged"
            ],
            "strategic_thinking": [
                "strategy", "strategic", "planning", "roadmap", "vision",
                "initiative", "transformation", "innovation", "growth", "scaling"
            ],
            "collaboration": [
                "collaborated", "partnered", "worked with", "cross-functional",
                "stakeholders", "team", "communication", "facilitated"
            ],
            "problem_solving": [
                "solved", "resolved", "troubleshooted", "analyzed", "investigated",
                "identified", "diagnosed", "improved", "enhanced", "fixed"
            ],
            "results_driven": [
                "achieved", "delivered", "exceeded", "increased", "improved",
                "reduced", "saved", "generated", "performance", "metrics"
            ]
        }
        
        # Voice analysis patterns
        self.formality_indicators = {
            "high": ["furthermore", "accordingly", "subsequently", "aforementioned"],
            "medium": ["however", "therefore", "additionally", "specifically"],
            "low": ["really", "pretty", "quite", "very", "super"]
        }
        
        self.energy_indicators = {
            "high": ["excited", "passionate", "thrilled", "enthusiastic", "dynamic"],
            "medium": ["interested", "engaged", "focused", "committed"],
            "low": ["steady", "consistent", "reliable", "methodical"]
        }
        
    def analyze_themes(self, content: str) -> List[LLMThemeResult]:
        """
        Extract professional themes using keyword matching.
        
        Args:
            content: Document text content
            
        Returns:
            List of identified themes with confidence scores
        """
        content_lower = content.lower()
        themes = []
        
        for theme_name, keywords in self.theme_patterns.items():
            matches = []
            match_count = 0
            
            for keyword in keywords:
                if keyword in content_lower:
                    matches.append(keyword)
                    # Count multiple occurrences
                    match_count += len(re.findall(rf'\b{re.escape(keyword)}\w*', content_lower))
                    
            if matches:
                # Calculate confidence based on keyword diversity and frequency
                diversity_score = len(matches) / len(keywords)  # 0.0-1.0
                frequency_score = min(match_count / 10, 1.0)   # Cap at 1.0
                confidence = (diversity_score * 0.6 + frequency_score * 0.4) * 0.8  # Max 0.8 for keyword analysis
                
                if confidence > 0.2:  # Threshold for inclusion
                    theme = LLMThemeResult(
                        theme_name=theme_name.replace("_", " "),
                        confidence=round(confidence, 2),
                        evidence=matches[:3],  # Top 3 matching keywords
                        context="keyword_analysis",
                        reasoning=f"Found {len(matches)} relevant keywords with {match_count} total matches"
                    )
                    themes.append(theme)
                    
        # Sort by confidence and return top themes
        themes.sort(key=lambda x: x.confidence, reverse=True)
        return themes[:5]  # Max 5 themes
        
    def analyze_voice_characteristics(self, content: str) -> LLMVoiceCharacteristics:
        """
        Analyze voice characteristics using keyword patterns.
        
        Args:
            content: Document text content
            
        Returns:
            Voice characteristics with basic analysis
        """
        content_lower = content.lower()
        
        # Analyze formality
        formality_score = self._calculate_formality(content_lower)
        
        # Analyze energy
        energy_score = self._calculate_energy(content_lower)
        
        # Determine tone based on patterns
        tone = self._determine_tone(content_lower)
        
        # Identify communication style
        communication_style = self._identify_communication_style(content_lower)
        
        # Assess vocabulary complexity
        vocabulary_complexity = self._assess_vocabulary_complexity(content)
        
        # Find evidence quotes (sentences with strong indicators)
        evidence_quotes = self._extract_evidence_quotes(content, communication_style)
        
        return LLMVoiceCharacteristics(
            tone=tone,
            formality=formality_score,
            energy=energy_score,
            communication_style=communication_style,
            vocabulary_complexity=vocabulary_complexity,
            evidence_quotes=evidence_quotes[:3],
            confidence_score=0.6  # Fixed confidence for keyword analysis
        )
        
    def analyze_narrative_arc(self, content: str) -> LLMNarrativeArc:
        """
        Analyze career narrative using basic pattern matching.
        
        Args:
            content: Document text content
            
        Returns:
            Basic narrative arc analysis
        """
        content_lower = content.lower()
        
        # Determine progression pattern
        progression_pattern = self._determine_progression_pattern(content_lower)
        
        # Identify value proposition
        value_proposition = self._identify_value_proposition(content_lower)
        
        # Predict future positioning
        future_positioning = self._predict_future_positioning(content_lower, progression_pattern)
        
        return LLMNarrativeArc(
            progression_pattern=progression_pattern,
            value_proposition=value_proposition,
            future_positioning=future_positioning,
            timeline_evidence=[],  # Limited timeline extraction in fallback
            confidence_score=0.5,  # Lower confidence for keyword analysis
            supporting_narrative="Basic keyword-based career progression analysis"
        )
        
    def _calculate_formality(self, content: str) -> float:
        """Calculate formality score based on language patterns."""
        high_formal = sum(1 for indicator in self.formality_indicators["high"] if indicator in content)
        medium_formal = sum(1 for indicator in self.formality_indicators["medium"] if indicator in content) 
        low_formal = sum(1 for indicator in self.formality_indicators["low"] if indicator in content)
        
        if high_formal > 0 or medium_formal > 2:
            return 0.8
        elif low_formal > 2:
            return 0.3
        else:
            return 0.6  # Default professional
            
    def _calculate_energy(self, content: str) -> float:
        """Calculate energy score based on language patterns."""
        high_energy = sum(1 for indicator in self.energy_indicators["high"] if indicator in content)
        medium_energy = sum(1 for indicator in self.energy_indicators["medium"] if indicator in content)
        low_energy = sum(1 for indicator in self.energy_indicators["low"] if indicator in content)
        
        if high_energy > 0:
            return 0.8
        elif medium_energy > 1:
            return 0.6
        else:
            return 0.4  # Default calm
            
    def _determine_tone(self, content: str) -> str:
        """Determine overall tone based on content analysis."""
        if any(word in content for word in ["passionate", "excited", "love", "enjoy"]):
            return "enthusiastic"
        elif any(word in content for word in ["data", "analysis", "metrics", "research"]):
            return "analytical"
        elif any(word in content for word in ["creative", "innovative", "design", "artistic"]):
            return "creative"
        else:
            return "professional"
            
    def _identify_communication_style(self, content: str) -> List[str]:
        """Identify communication style tags."""
        styles = []
        
        if any(word in content for word in ["data", "metrics", "analysis", "results", "performance"]):
            styles.append("data-driven")
            
        if any(word in content for word in ["team", "collaboration", "partnership", "stakeholders"]):
            styles.append("collaborative")
            
        if any(word in content for word in ["achieved", "delivered", "exceeded", "improved"]):
            styles.append("results-oriented")
            
        return styles[:3] if styles else ["professional"]
        
    def _assess_vocabulary_complexity(self, content: str) -> str:
        """Assess vocabulary complexity level."""
        technical_terms = len(re.findall(r'\b\w{10,}\b', content))  # Long technical words
        total_words = len(content.split())
        
        if total_words > 0:
            complexity_ratio = technical_terms / total_words
            if complexity_ratio > 0.1:
                return "technical professional"
            elif complexity_ratio > 0.05:
                return "business professional"
            else:
                return "accessible professional"
        return "professional"
        
    def _extract_evidence_quotes(self, content: str, communication_style: List[str]) -> List[str]:
        """Extract sentences that demonstrate communication style."""
        sentences = re.split(r'[.!?]+', content)
        evidence = []
        
        for sentence in sentences[:20]:  # Check first 20 sentences
            sentence = sentence.strip()
            if len(sentence) > 20:  # Meaningful length
                # Look for sentences with style indicators
                if any(style_word in sentence.lower() for style in communication_style 
                       for style_word in style.split("-")):
                    evidence.append(sentence)
                    
        return evidence
        
    def _determine_progression_pattern(self, content: str) -> str:
        """Determine career progression pattern."""
        if any(word in content for word in ["founded", "startup", "entrepreneur"]):
            return "entrepreneurial"
        elif any(word in content for word in ["led", "managed", "director", "manager"]):
            return "technical_to_leadership"
        elif any(word in content for word in ["expert", "specialist", "advanced", "deep"]):
            return "specialist_expert"
        else:
            return "general_professional"
            
    def _identify_value_proposition(self, content: str) -> str:
        """Identify core value proposition."""
        if any(word in content for word in ["innovation", "created", "developed", "new"]):
            return "innovation_driver"
        elif any(word in content for word in ["solved", "resolved", "fixed", "improved"]):
            return "problem_solver"
        elif any(word in content for word in ["strategy", "planning", "vision"]):
            return "strategic_thinker"
        else:
            return "experienced_professional"
            
    def _predict_future_positioning(self, content: str, progression_pattern: str) -> str:
        """Predict future career positioning."""
        if progression_pattern == "technical_to_leadership":
            return "senior_technical_lead"
        elif progression_pattern == "specialist_expert":
            return "domain_expert"
        elif progression_pattern == "entrepreneurial":
            return "strategic_advisor"
        else:
            return "continued_growth"