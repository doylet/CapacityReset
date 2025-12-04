"""
Unified configuration for skills extraction with backward compatibility.

This consolidates both the original and enhanced configurations,
providing graceful fallback when enhanced ML features are not available.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional


# Enhanced tech skills lexicon (400+ modern skills)
ENHANCED_SKILLS_LEXICON = {
    'programming_languages': [
        'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'go', 'rust',
        'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'dart', 'elixir',
        'clojure', 'haskell', 'f#', 'lua', 'julia', 'nim', 'zig', 'crystal',
        'assembly', 'cobol', 'fortran', 'perl', 'groovy', 'erlang'
    ],
    'web_frameworks': [
        'react', 'vue.js', 'angular', 'svelte', 'next.js', 'nuxt.js', 'gatsby',
        'express.js', 'fastify', 'nestjs', 'django', 'flask', 'fastapi',
        'spring boot', 'asp.net core', 'laravel', 'symfony', 'rails', 'sinatra',
        'phoenix', 'gin', 'fiber', 'actix-web', 'axum', 'warp'
    ],
    'cloud_platforms': [
        'aws', 'azure', 'google cloud', 'gcp', 'alibaba cloud', 'digitalocean',
        'heroku', 'vercel', 'netlify', 'cloudflare', 'firebase', 'supabase',
        'railway', 'fly.io', 'render', 'planetscale', 'neon', 'upstash'
    ],
    'devops_tools': [
        'docker', 'kubernetes', 'helm', 'terraform', 'ansible', 'jenkins',
        'github actions', 'gitlab ci', 'circleci', 'travis ci', 'prometheus',
        'grafana', 'datadog', 'new relic', 'elk stack', 'fluentd', 'consul',
        'vault', 'nomad', 'nginx', 'apache', 'haproxy', 'istio', 'linkerd'
    ],
    'databases': [
        'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
        'dynamodb', 'neo4j', 'influxdb', 'clickhouse', 'snowflake', 'bigquery',
        'redshift', 'supabase', 'planetscale', 'cockroachdb', 'timescaledb',
        'sqlite', 'oracle', 'sql server', 'mariadb', 'couchdb', 'rethinkdb'
    ],
    'machine_learning': [
        'tensorflow', 'pytorch', 'scikit-learn', 'keras', 'hugging face',
        'transformers', 'bert', 'gpt', 'llama', 'stable diffusion', 'opencv',
        'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly', 'jupyter',
        'mlflow', 'kubeflow', 'weights & biases', 'tensorboard', 'dvc',
        'apache spark', 'hadoop', 'kafka', 'airflow', 'dbt', 'ray'
    ],
    'mobile_development': [
        'react native', 'flutter', 'ionic', 'xamarin', 'swift ui', 'jetpack compose',
        'android studio', 'xcode', 'expo', 'cordova', 'capacitor', 'nativescript'
    ],
    'frontend_tools': [
        'html', 'css', 'sass', 'scss', 'tailwind css', 'bootstrap', 'material-ui',
        'chakra ui', 'ant design', 'webpack', 'vite', 'rollup', 'parcel',
        'babel', 'typescript', 'eslint', 'prettier', 'jest', 'cypress'
    ],
    'testing_frameworks': [
        'jest', 'mocha', 'chai', 'cypress', 'playwright', 'selenium', 'puppeteer',
        'pytest', 'unittest', 'testng', 'junit', 'rspec', 'karma', 'enzyme',
        'react testing library', 'vue test utils', 'postman', 'k6', 'jmeter'
    ],
    'design_tools': [
        'figma', 'sketch', 'adobe xd', 'framer', 'principle', 'invision',
        'zeplin', 'abstract', 'photoshop', 'illustrator', 'after effects'
    ],
    'blockchain': [
        'solidity', 'ethereum', 'bitcoin', 'web3.js', 'ethers.js', 'truffle',
        'hardhat', 'metamask', 'ipfs', 'polygon', 'chainlink', 'opensea'
    ],
    'soft_skills': [
        'leadership', 'communication', 'teamwork', 'problem solving',
        'critical thinking', 'creativity', 'adaptability', 'time management',
        'project management', 'mentoring', 'public speaking', 'negotiation'
    ]
}

# Original skills lexicon (175 general skills) for backward compatibility
ORIGINAL_SKILLS_LEXICON = {
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

# Advanced skill context indicators
SKILL_CONTEXT_INDICATORS = {
    'strong_indicators': {
        'experience with', 'proficient in', 'expertise in', 'skilled in',
        'advanced knowledge', 'mastery of', 'expert level', 'deep understanding',
        'hands-on experience', 'proven experience', 'extensive experience',
        'working knowledge', 'solid understanding', 'strong background'
    },
    'medium_indicators': {
        'familiar with', 'knowledge of', 'understanding of', 'exposure to',
        'basic knowledge', 'some experience', 'awareness of', 'introduction to',
        'fundamentals of', 'basics of', 'beginner level', 'entry level'
    },
    'requirement_indicators': {
        'required', 'must have', 'essential', 'mandatory', 'necessary',
        'needed', 'critical', 'vital', 'key requirement', 'prerequisite'
    },
    'preference_indicators': {
        'preferred', 'nice to have', 'bonus', 'plus', 'advantageous',
        'desirable', 'ideal', 'would be great', 'additional', 'extra'
    }
}

# Technology patterns for extraction
TECH_PATTERNS = {
    'versions': [
        r'\\b(?:python|node|java|php|ruby|go|rust)\\s+(?:v?\\d+\\.\\d+(?:\\.\\d+)?)\\b',
        r'\\b(?:react|vue|angular|django|spring)\\s+(?:v?\\d+\\.\\d+(?:\\.\\d+)?)\\b',
        r'\\b(?:aws|azure|gcp)\\s+(?:v?\\d+\\.\\d+(?:\\.\\d+)?)\\b'
    ],
    'frameworks': [
        r'\\b\\w+\\.js\\b', r'\\b\\w+\\.py\\b', r'\\b\\w+-\\w+\\b',
        r'\\bspring\\s+\\w+\\b', r'\\b\\w+\\s+framework\\b'
    ],
    'certifications': [
        r'\\b(?:aws|azure|google cloud|gcp)\\s+certified\\b',
        r'\\bcertified\\s+(?:kubernetes|docker|terraform)\\b',
        r'\\b\\w+\\s+certification\\b'
    ]
}


@dataclass
class MLConfig:
    """Configuration for advanced ML features."""
    
    # Semantic similarity settings
    use_semantic_extraction: bool = True
    semantic_similarity_threshold: float = 0.7
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    
    # Pattern extraction settings
    use_pattern_extraction: bool = True
    pattern_confidence_boost: float = 0.1
    
    # Confidence scoring with ML features
    use_ml_confidence_scoring: bool = True
    ensemble_weights: Dict[str, float] = field(default_factory=lambda: {
        'extraction_method': 0.25,
        'context_strength': 0.20,
        'frequency': 0.15,
        'category_relevance': 0.15,
        'position_importance': 0.10,
        'text_quality': 0.10,
        'skill_specificity': 0.05
    })
    
    # Filtering improvements
    min_confidence_threshold: float = 0.6
    max_skills_per_category: int = 15
    dedupe_similarity_threshold: float = 0.85


@dataclass
class ExtractionWeights:
    """Weights for different extraction methods."""
    enhanced_lexicon: float = 1.0
    semantic_similarity: float = 0.9
    pattern_based: float = 0.8
    original_lexicon: float = 0.7
    ner: float = 0.6
    noun_chunk: float = 0.5


@dataclass
class CategoryWeights:
    """Weights for different skill categories."""
    programming_languages: float = 1.0
    web_frameworks: float = 0.95
    cloud_platforms: float = 0.95
    machine_learning: float = 0.9
    devops_tools: float = 0.9
    databases: float = 0.85
    mobile_development: float = 0.8
    frontend_tools: float = 0.8
    testing_frameworks: float = 0.75
    design_tools: float = 0.7
    blockchain: float = 0.8
    soft_skills: float = 0.6
    # Legacy categories (for backward compatibility)
    technical_skills: float = 0.9
    communicating: float = 0.6
    creative_skills: float = 0.6
    developing_people: float = 0.6
    financial_skills: float = 0.7
    interpersonal_skills: float = 0.6
    managing_directing: float = 0.7
    organising: float = 0.6
    planning: float = 0.7
    researching_analysing: float = 0.8
    selling_marketing: float = 0.6


@dataclass
class FilterConfig:
    """Configuration for skill filtering."""
    min_skill_length: int = 2
    max_skill_length: int = 40
    min_chunk_words: int = 2
    max_chunk_words: int = 4
    min_section_length: int = 50
    fallback_section_length: int = 200
    confidence_threshold: float = 0.6


@dataclass
class UnifiedSkillsConfig:
    """
    Unified configuration that supports both original and enhanced extraction.
    
    This configuration automatically adapts based on available dependencies,
    providing enhanced features when possible while maintaining backward compatibility.
    """
    
    # Version identifier
    version: str = "v4.0-unified-config"
    
    # BigQuery configuration
    project_id: str = "sylvan-replica-478802-p4"
    dataset_id: str = "brightdata_jobs"
    
    # Alias configuration path (for external alias resolution)
    alias_config_path: Optional[str] = None
    
    # Mode selection (auto-detected based on available dependencies)
    enhanced_mode: bool = True
    fallback_to_original: bool = True
    
    # Skills lexicons (enhanced is preferred, original as fallback)
    enhanced_skills_lexicon: Dict[str, List[str]] = field(default_factory=lambda: ENHANCED_SKILLS_LEXICON)
    original_skills_lexicon: Dict[str, List[str]] = field(default_factory=lambda: ORIGINAL_SKILLS_LEXICON)
    
    # Context indicators for advanced extraction
    skill_context_indicators: Dict[str, Set[str]] = field(default_factory=lambda: {
        k: set(v) for k, v in SKILL_CONTEXT_INDICATORS.items()
    })
    tech_patterns: Dict[str, List[str]] = field(default_factory=lambda: TECH_PATTERNS)
    
    # Advanced ML configuration
    ml_config: MLConfig = field(default_factory=MLConfig)
    
    # Extraction and scoring weights
    extraction_weights: ExtractionWeights = field(default_factory=ExtractionWeights)
    category_weights: CategoryWeights = field(default_factory=CategoryWeights)
    
    # Filtering configuration
    filter_config: FilterConfig = field(default_factory=FilterConfig)
    
    # Context extraction
    context_window: int = 60
    max_context_length: int = 200
    
    # Section filtering (comprehensive list)
    relevant_sections: List[str] = field(default_factory=lambda: [
        'responsibilities', 'requirements', 'qualifications', 'required qualifications',
        'preferred qualifications', 'skills', 'experience', 'technical requirements',
        'must have', 'nice to have', 'what you will do', 'what we are looking for',
        'about you', 'key responsibilities', 'role overview', 'technical skills',
        'required skills', 'preferred skills', 'core competencies',
        'technologies used', 'tech stack', 'tools and technologies',
        'what you\'ll do', 'what we\'re looking for', 'about the role',
        'your role', 'essential skills', 'desired skills', 'ideal candidate',
        'you will', 'job description', 'duties', 'what you bring',
        'what you need', 'position', 'job requirements', 'skills and experience',
        'minimum requirements'
    ])
    
    excluded_sections: List[str] = field(default_factory=lambda: [
        'benefits', 'compensation', 'salary', 'perks', 'about us',
        'company culture', 'our mission', 'equal opportunity', 'diversity',
        'how to apply', 'application process', 'contact us', 'location',
        'about the company', 'our values', 'why join us', 'work environment'
    ])
    
    # Noise filtering (comprehensive)
    noise_words: Set[str] = field(default_factory=lambda: {
        'new york', 'san francisco', 'los angeles', 'london', 'berlin',
        'remote', 'hybrid', 'full time', 'part time', 'contract', 'permanent',
        'temporary', 'competitive salary', 'health insurance', 'work life balance',
        'team player', 'fast paced', 'dynamic environment', 'startup',
        'unicorn', 'scale up', 'growth company', 'innovative', 'cutting edge',
        'job description', 'about us', 'apply now', 'click here',
        'professional development', 'career growth', 'team member',
        'job posting', 'united states', 'north america'
    })
    
    # Context indicators (legacy support)
    strong_indicators: Set[str] = field(default_factory=lambda: {
        'required', 'must have', 'essential', 'proficient', 'expert',
        'experience with', 'expertise in', 'skilled in', 'advanced knowledge'
    })
    
    medium_indicators: Set[str] = field(default_factory=lambda: {
        'experience', 'knowledge', 'familiar', 'understanding', 'ability',
        'exposure to', 'basic knowledge', 'some experience'
    })
    
    # Skill prioritization
    high_priority_categories: Set[str] = field(default_factory=lambda: {
        'programming_languages', 'web_frameworks', 'cloud_platforms',
        'machine_learning', 'devops_tools', 'databases', 'technical_skills'
    })
    
    @property
    def full_dataset_id(self) -> str:
        """Return fully qualified dataset ID."""
        return f"{self.project_id}.{self.dataset_id}"
    
    def get_skills_lexicon(self) -> Dict[str, List[str]]:
        """Get the appropriate skills lexicon based on mode."""
        if self.enhanced_mode:
            return self.enhanced_skills_lexicon
        return self.original_skills_lexicon
    
    def get_category_weight(self, category: str) -> float:
        """Get weight for a specific category."""
        return getattr(self.category_weights, category, 0.5)
    
    def is_high_priority_category(self, category: str) -> bool:
        """Check if category is high priority."""
        return category in self.high_priority_categories
    
    def get_confidence_threshold(self) -> float:
        """Get the appropriate confidence threshold."""
        if self.enhanced_mode:
            return self.ml_config.min_confidence_threshold
        return self.filter_config.confidence_threshold


# Aliases for backward compatibility
SkillsConfig = UnifiedSkillsConfig  # Original name
EnhancedSkillsConfig = UnifiedSkillsConfig  # Enhanced name