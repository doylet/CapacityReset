"""
LLM Prompt Templates for Brand Analysis

Stores versioned prompts for consistent LLM analysis.
Follows Constitution Principle VIII - no HEREDOCs, using triple-quoted strings.
"""

from typing import Dict, Any


class PromptTemplates:
    """
    Centralized prompt templates for brand analysis.
    
    Supports versioning for A/B testing and prompt improvement.
    """
    
    @staticmethod
    def get_theme_extraction_prompt(version: str = "v1") -> str:
        """
        Get prompt template for professional theme extraction.
        
        Args:
            version: Template version (v1, v2, etc.)
            
        Returns:
            Formatted prompt template string
        """
        if version == "v1":
            return """
Analyze this professional document and extract 3-5 key themes that represent the person's professional identity and expertise.

For each theme, provide:
1. Theme name (2-4 words, professional terminology)
2. Confidence score (0.0-1.0 based on evidence strength)
3. Evidence quotes (2-3 specific examples from the text)
4. Brief reasoning (why this theme was identified)

Focus on:
- Professional capabilities and skills
- Leadership and collaboration patterns  
- Industry expertise and domain knowledge
- Career progression indicators
- Unique value propositions

Document content:
{document_content}

Return response as valid JSON:
{
    "themes": [
        {
            "name": "strategic leadership",
            "confidence": 0.95,
            "evidence": ["led cross-functional team of 12", "drove strategic initiatives resulting in 40% growth"],
            "reasoning": "Multiple examples of leading teams and strategic decision-making"
        }
    ]
}
"""
        else:
            raise ValueError(f"Unknown theme extraction prompt version: {version}")
            
    @staticmethod
    def get_voice_analysis_prompt(version: str = "v1") -> str:
        """
        Get prompt template for voice and communication style analysis.
        
        Args:
            version: Template version
            
        Returns:
            Formatted prompt template string
        """
        if version == "v1":
            return """
Analyze the writing style and voice characteristics of this professional document.

Assess these dimensions:
1. Tone: overall emotional character (professional, analytical, creative, approachable)
2. Formality: language formality level (0.0=casual/conversational, 1.0=formal/academic)
3. Energy: communication energy level (0.0=calm/measured, 1.0=dynamic/enthusiastic)
4. Communication style: approach to conveying information (data-driven, storytelling, collaborative, direct)
5. Vocabulary complexity: language sophistication (accessible, business, technical, academic)

Provide evidence quotes that demonstrate each characteristic.

Document content:
{document_content}

Return as valid JSON:
{
    "tone": "professional",
    "formality": 0.8,
    "energy": 0.6,
    "communication_style": ["data-driven", "results-oriented"],
    "vocabulary_complexity": "business technical",
    "evidence_quotes": ["achieved 40% improvement in system efficiency", "collaborated with stakeholders to define requirements"],
    "confidence_score": 0.92
}
"""
        else:
            raise ValueError(f"Unknown voice analysis prompt version: {version}")
            
    @staticmethod  
    def get_narrative_analysis_prompt(version: str = "v1") -> str:
        """
        Get prompt template for career narrative arc analysis.
        
        Args:
            version: Template version
            
        Returns:
            Formatted prompt template string
        """
        if version == "v1":
            return """
Analyze the career narrative and professional progression shown in this document.

Identify:
1. Progression pattern: overall career trajectory
   - technical_to_leadership: evolved from IC to management
   - specialist_expert: deepened expertise in domain
   - cross_domain: moved between different areas
   - entrepreneurial: built/founded things
   
2. Value proposition: core professional value
   - innovation_driver: creates new solutions
   - problem_solver: tackles complex challenges
   - strategic_thinker: sees big picture
   - execution_expert: delivers results
   - relationship_builder: connects and influences
   
3. Future positioning: likely next career steps
   - senior_technical_lead: technical leadership
   - strategic_advisor: consultative role
   - domain_expert: specialized authority
   - general_manager: broad business leadership
   
4. Timeline evidence: specific examples showing progression

Document content:
{document_content}

Return as valid JSON:
{
    "progression_pattern": "technical_to_leadership",
    "value_proposition": "innovation_driver",
    "future_positioning": "senior_technical_lead", 
    "timeline_evidence": [
        {"period": "2020-2023", "role": "Senior Engineer", "growth": "Led architecture decisions and mentored junior developers"}
    ],
    "confidence_score": 0.88,
    "supporting_narrative": "Shows clear progression from individual contributor to technical leadership with consistent innovation focus..."
}
"""
        else:
            raise ValueError(f"Unknown narrative analysis prompt version: {version}")
            
    @staticmethod
    def format_prompt(template: str, **kwargs) -> str:
        """
        Format prompt template with provided variables.
        
        Args:
            template: Prompt template string
            **kwargs: Variables to substitute
            
        Returns:
            Formatted prompt string
        """
        return template.format(**kwargs)
        
    @staticmethod
    def get_available_versions() -> Dict[str, list]:
        """
        Get all available prompt template versions.
        
        Returns:
            Dict mapping prompt types to available versions
        """
        return {
            "theme_extraction": ["v1"],
            "voice_analysis": ["v1"],
            "narrative_analysis": ["v1"]
        }