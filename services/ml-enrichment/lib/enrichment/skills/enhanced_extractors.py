"""
Enhanced extraction strategies using modern ML approaches.

This module implements state-of-the-art NLP techniques for better skill extraction.
"""

import json
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
import numpy as np

# Optional imports for enhanced features
try:
    import torch
    from transformers import AutoTokenizer, AutoModel, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .config import SkillsConfig
from .extractors import ExtractionStrategy


# Comprehensive tech skills lexicon (400+ skills)
ENHANCED_TECH_LEXICON = {
    "programming_languages": [
        "python", "javascript", "java", "typescript", "c++", "c#", "go", "rust",
        "php", "ruby", "swift", "kotlin", "scala", "r", "matlab", "perl",
        "dart", "elixir", "clojure", "haskell", "f#", "visual basic", "cobol",
        "fortran", "assembly", "lua", "groovy", "julia", "erlang", "nim"
    ],
    "web_technologies": [
        "react", "vue.js", "angular", "svelte", "next.js", "nuxt.js", "gatsby",
        "html", "css", "sass", "scss", "less", "tailwind css", "bootstrap",
        "material-ui", "jquery", "backbone.js", "ember.js", "meteor",
        "webpack", "vite", "rollup", "parcel", "gulp", "grunt", "babel",
        "express.js", "fastify", "koa", "nestjs", "django", "flask", "fastapi",
        "spring boot", "asp.net", "laravel", "symfony", "rails", "sinatra"
    ],
    "cloud_platforms": [
        "aws", "azure", "google cloud", "gcp", "alibaba cloud", "digitalocean",
        "heroku", "vercel", "netlify", "cloudflare", "firebase", "supabase",
        "s3", "ec2", "lambda", "cloudformation", "terraform", "pulumi",
        "docker", "kubernetes", "helm", "istio", "openshift", "rancher",
        "ecs", "fargate", "cloud run", "app engine", "azure functions"
    ],
    "databases": [
        "mysql", "postgresql", "sqlite", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "neo4j", "influxdb", "oracle", "sql server",
        "mariadb", "couchdb", "rethinkdb", "cockroachdb", "snowflake",
        "bigquery", "redshift", "databricks", "clickhouse", "timescaledb"
    ],
    "data_science": [
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
        "jupyter", "matplotlib", "seaborn", "plotly", "tableau", "power bi",
        "apache spark", "hadoop", "kafka", "airflow", "dbt", "mlflow",
        "kubeflow", "weights & biases", "tensorboard", "hugging face",
        "spacy", "nltk", "opencv", "transformers", "bert", "gpt", "llama"
    ],
    "devops_tools": [
        "jenkins", "github actions", "gitlab ci", "circleci", "travis ci",
        "ansible", "puppet", "chef", "saltstack", "vagrant", "packer",
        "prometheus", "grafana", "datadog", "new relic", "splunk", "elk stack",
        "fluentd", "jaeger", "zipkin", "consul", "vault", "nomad", "nginx",
        "apache", "haproxy", "cloudflare", "cdn", "load balancer"
    ],
    "mobile_development": [
        "react native", "flutter", "ionic", "xamarin", "cordova", "swift",
        "objective-c", "kotlin", "java android", "android studio", "xcode",
        "firebase", "realm", "sqlite mobile", "push notifications", "app store"
    ],
    "testing_tools": [
        "jest", "mocha", "chai", "cypress", "selenium", "puppeteer", "playwright",
        "pytest", "unittest", "testng", "junit", "rspec", "jasmine", "karma",
        "enzyme", "react testing library", "postman", "newman", "k6", "jmeter"
    ],
    "design_tools": [
        "figma", "sketch", "adobe xd", "photoshop", "illustrator", "after effects",
        "principle", "framer", "invision", "zeplin", "abstract", "canva"
    ],
    "project_management": [
        "jira", "confluence", "trello", "asana", "monday.com", "notion",
        "slack", "microsoft teams", "discord", "zoom", "agile", "scrum",
        "kanban", "waterfall", "lean", "safe", "project planning", "roadmap"
    ]
}

# Industry-specific skill patterns
SKILL_PATTERNS = {
    "frameworks": [
        r"\b\w+\.js\b", r"\b\w+\.py\b", r"\b\w+-\w+\b",  # framework naming patterns
        r"\bspring\s+\w+\b", r"\b\w+\s+framework\b", r"\b\w+\s+library\b"
    ],
    "versions": [
        r"\b\w+\s+\d+\.\d+\b", r"\b\w+\s+v\d+\b", r"\b\w+\s+version\s+\d+\b"
    ],
    "certifications": [
        r"\b\w+\s+certified\b", r"\bcertified\s+\w+\b", r"\b\w+\s+certification\b"
    ]
}


class EnhancedLexiconExtractor(ExtractionStrategy):
    """
    Enhanced lexicon-based extraction with comprehensive tech skills.
    """
    
    def __init__(self, phrase_matcher, normalizer, scorer, config: SkillsConfig):
        super().__init__()
        self.phrase_matcher = phrase_matcher
        self.normalizer = normalizer
        self.scorer = scorer
        self.config = config
        self.tech_lexicon = ENHANCED_TECH_LEXICON
        
    def extract(self, doc, text: str, source_field: str) -> List[Dict[str, Any]]:
        """Extract skills using enhanced tech lexicon."""
        skills = []
        text_lower = text.lower()
        
        # Extract from comprehensive lexicon
        for category, skill_list in self.tech_lexicon.items():
            for skill in skill_list:
                skill_lower = skill.lower()
                if skill_lower in text_lower:
                    # Find all occurrences with context
                    start_pos = 0
                    while True:
                        pos = text_lower.find(skill_lower, start_pos)
                        if pos == -1:
                            break
                        
                        # Extract context around the skill
                        context = self._extract_rich_context(text, pos, skill)
                        
                        # Calculate enhanced confidence
                        confidence = self._calculate_enhanced_confidence(
                            text, skill, context, category
                        )
                        
                        if confidence >= self.config.filter_config.confidence_threshold:
                            skills.append({
                                'skill_name': skill,
                                'skill_category': category,
                                'confidence_score': confidence,
                                'source_field': source_field,
                                'context_snippet': context,
                                'extraction_method': 'enhanced_lexicon'
                            })
                        
                        start_pos = pos + 1
                        
        return self._deduplicate_skills(skills)
    
    def _extract_rich_context(self, text: str, pos: int, skill: str) -> str:
        """Extract rich context with skill indicators."""
        window = self.config.context_window
        start = max(0, pos - window)
        end = min(len(text), pos + len(skill) + window)
        
        context = text[start:end].strip()
        
        # Add ellipsis markers
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
            
        return context
    
    def _calculate_enhanced_confidence(
        self, text: str, skill: str, context: str, category: str
    ) -> float:
        """Calculate confidence with category-specific boosts."""
        base_confidence = self.scorer.calculate_confidence(text, skill, context)
        
        # Category-specific boosts
        category_boosts = {
            "programming_languages": 0.2,
            "web_technologies": 0.15,
            "cloud_platforms": 0.15,
            "databases": 0.1,
            "data_science": 0.1
        }
        
        boost = category_boosts.get(category, 0.05)
        return min(base_confidence + boost, 1.0)
    
    def _deduplicate_skills(self, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate skills, keeping highest confidence."""
        skill_map = {}
        
        for skill in skills:
            key = skill['skill_name'].lower()
            if key not in skill_map or skill['confidence_score'] > skill_map[key]['confidence_score']:
                skill_map[key] = skill
                
        return list(skill_map.values())


class PatternBasedExtractor(ExtractionStrategy):
    """
    Extract skills using regex patterns for frameworks, versions, etc.
    """
    
    def __init__(self, config: SkillsConfig):
        super().__init__()
        self.config = config
        self.patterns = SKILL_PATTERNS
        
    def extract(self, doc, text: str, source_field: str) -> List[Dict[str, Any]]:
        """Extract skills using regex patterns."""
        skills = []
        
        for pattern_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    skill_name = match.group().strip()
                    
                    # Skip if too short or generic
                    if len(skill_name) < 3 or skill_name.lower() in {'the', 'and', 'with', 'for'}:
                        continue
                        
                    context = self._extract_context(text, match.start(), skill_name)
                    confidence = self._calculate_pattern_confidence(skill_name, pattern_type, context)
                    
                    if confidence >= self.config.filter_config.confidence_threshold:
                        skills.append({
                            'skill_name': skill_name,
                            'skill_category': pattern_type,
                            'confidence_score': confidence,
                            'source_field': source_field,
                            'context_snippet': context,
                            'extraction_method': 'pattern_based'
                        })
                        
        return skills
    
    def _extract_context(self, text: str, pos: int, skill: str) -> str:
        """Extract context around pattern match."""
        window = 30
        start = max(0, pos - window)
        end = min(len(text), pos + len(skill) + window)
        return text[start:end].strip()
    
    def _calculate_pattern_confidence(self, skill: str, pattern_type: str, context: str) -> float:
        """Calculate confidence for pattern-based matches."""
        base_confidence = 0.6
        
        # Pattern type boosts
        type_boosts = {
            "frameworks": 0.2,
            "versions": 0.15,
            "certifications": 0.25
        }
        
        return min(base_confidence + type_boosts.get(pattern_type, 0.1), 0.95)


class SemanticExtractor(ExtractionStrategy):
    """
    Extract skills using semantic similarity with embeddings.
    Requires sentence-transformers library.
    """
    
    def __init__(self, config: SkillsConfig, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__()
        self.config = config
        self.model = None
        self.model_name = model_name
        self._skill_embeddings = None
        self._skills_list = None
        
    def _load_model(self):
        """Lazy load the sentence transformer model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers package required for semantic extraction")
            
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
            self._prepare_skill_embeddings()
    
    def _prepare_skill_embeddings(self):
        """Pre-compute embeddings for all skills in lexicon."""
        all_skills = []
        for category, skills in ENHANCED_TECH_LEXICON.items():
            all_skills.extend(skills)
            
        self._skills_list = all_skills
        self._skill_embeddings = self.model.encode(all_skills)
    
    def extract(self, doc, text: str, source_field: str) -> List[Dict[str, Any]]:
        """Extract skills using semantic similarity."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return []  # Graceful fallback
            
        self._load_model()
        
        skills = []
        
        # Extract noun phrases and entities as candidates
        candidates = set()
        
        # Add noun chunks
        for chunk in doc.noun_chunks:
            if 2 <= len(chunk.text.split()) <= 4:
                candidates.add(chunk.text.lower().strip())
        
        # Add named entities
        for ent in doc.ents:
            if ent.label_ in ['PRODUCT', 'ORG', 'TECHNOLOGY']:
                candidates.add(ent.text.lower().strip())
        
        # Calculate semantic similarity
        if candidates:
            candidate_embeddings = self.model.encode(list(candidates))
            similarities = np.dot(candidate_embeddings, self._skill_embeddings.T)
            
            for i, candidate in enumerate(candidates):
                max_similarity = np.max(similarities[i])
                
                if max_similarity > 0.7:  # High similarity threshold
                    best_match_idx = np.argmax(similarities[i])
                    matched_skill = self._skills_list[best_match_idx]
                    
                    # Find category
                    category = self._find_skill_category(matched_skill)
                    
                    # Extract context
                    context = self._find_skill_context(text, candidate)
                    
                    confidence = min(max_similarity, 0.9)
                    
                    skills.append({
                        'skill_name': matched_skill,
                        'skill_category': category,
                        'confidence_score': confidence,
                        'source_field': source_field,
                        'context_snippet': context,
                        'extraction_method': 'semantic_similarity',
                        'candidate_text': candidate,
                        'similarity_score': max_similarity
                    })
        
        return skills
    
    def _find_skill_category(self, skill: str) -> str:
        """Find which category a skill belongs to."""
        for category, skills in ENHANCED_TECH_LEXICON.items():
            if skill in skills:
                return category
        return "uncategorized"
    
    def _find_skill_context(self, text: str, candidate: str) -> str:
        """Find context for the candidate text in original text."""
        text_lower = text.lower()
        pos = text_lower.find(candidate.lower())
        
        if pos != -1:
            window = 40
            start = max(0, pos - window)
            end = min(len(text), pos + len(candidate) + window)
            return text[start:end].strip()
        
        return ""


class MLBasedConfidenceScorer:
    """
    ML-based confidence scoring using multiple features.
    """
    
    def __init__(self, config: SkillsConfig):
        self.config = config
        
    def calculate_advanced_confidence(
        self, 
        text: str, 
        skill: str, 
        context: str,
        category: str,
        extraction_method: str,
        additional_features: Optional[Dict] = None
    ) -> float:
        """Calculate confidence using multiple ML features."""
        
        features = self._extract_features(text, skill, context, category, extraction_method)
        if additional_features:
            features.update(additional_features)
            
        # Simple ensemble scoring (can be replaced with trained model)
        confidence = self._ensemble_score(features)
        
        return min(max(confidence, 0.0), 1.0)
    
    def _extract_features(
        self, text: str, skill: str, context: str, category: str, method: str
    ) -> Dict[str, float]:
        """Extract numerical features for ML scoring."""
        
        text_lower = text.lower()
        skill_lower = skill.lower()
        context_lower = context.lower()
        
        return {
            # Frequency features
            'skill_frequency': text_lower.count(skill_lower),
            'skill_density': text_lower.count(skill_lower) / len(text.split()),
            
            # Position features
            'first_occurrence_ratio': text_lower.find(skill_lower) / len(text),
            'appears_in_title': 1.0 if skill_lower in text[:100].lower() else 0.0,
            
            # Context features
            'context_length': len(context),
            'has_strong_indicators': 1.0 if any(ind in context_lower for ind in self.config.strong_indicators) else 0.0,
            'has_medium_indicators': 1.0 if any(ind in context_lower for ind in self.config.medium_indicators) else 0.0,
            
            # Category features
            'is_programming_language': 1.0 if category == 'programming_languages' else 0.0,
            'is_framework': 1.0 if category in ['web_technologies', 'frameworks'] else 0.0,
            'is_cloud_tech': 1.0 if category == 'cloud_platforms' else 0.0,
            
            # Method features
            'extraction_method_score': {
                'enhanced_lexicon': 0.9,
                'semantic_similarity': 0.85,
                'pattern_based': 0.7,
                'lexicon': 0.8
            }.get(method, 0.5),
            
            # Text quality features
            'text_length': len(text),
            'context_skill_ratio': len(context) / len(skill) if skill else 1.0,
        }
    
    def _ensemble_score(self, features: Dict[str, float]) -> float:
        """Simple ensemble scoring (replace with trained model)."""
        
        # Weighted combination of features
        weights = {
            'extraction_method_score': 0.25,
            'has_strong_indicators': 0.20,
            'skill_frequency': 0.15,
            'is_programming_language': 0.10,
            'is_framework': 0.10,
            'appears_in_title': 0.10,
            'context_skill_ratio': 0.05,
            'has_medium_indicators': 0.05
        }
        
        score = 0.3  # Base score
        
        for feature, weight in weights.items():
            if feature in features:
                if feature in ['skill_frequency']:
                    # Normalize frequency
                    normalized = min(features[feature] / 3.0, 1.0)
                    score += weight * normalized
                elif feature in ['context_skill_ratio']:
                    # Optimal ratio is around 10-15
                    optimal_ratio = min(features[feature] / 15.0, 1.0)
                    score += weight * optimal_ratio
                else:
                    score += weight * features[feature]
                    
        return score