"""
Enhanced configuration with modern ML parameters.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional


# Comprehensive tech skills lexicon (400+ modern skills)
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

# Modern job-specific keywords that indicate skill requirements
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

# Patterns for extracting version numbers and specific technologies
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
class AdvancedMLConfig:
    """Configuration for advanced ML features."""
    
    # Semantic similarity settings
    use_semantic_extraction: bool = True
    semantic_similarity_threshold: float = 0.7
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    
    # Pattern extraction settings
    use_pattern_extraction: bool = True
    pattern_confidence_boost: float = 0.1
    
    # Confidence scoring
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
class EnhancedExtractionWeights:
    """Enhanced weights for different extraction methods."""
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


@dataclass
class EnhancedSkillsConfig:
    """
    Enhanced configuration with modern ML capabilities.
    
    This extends the original configuration with advanced features
    for better skill extraction and confidence scoring.
    """
    
    # Version identifier
    version: str = "v3.0-enhanced-ml-extraction"
    
    # BigQuery configuration
    project_id: str = "sylvan-replica-478802-p4"
    dataset_id: str = "brightdata_jobs"
    
    # Enhanced lexicons
    enhanced_skills_lexicon: Dict[str, List[str]] = field(default_factory=lambda: ENHANCED_SKILLS_LEXICON)
    skill_context_indicators: Dict[str, Set[str]] = field(default_factory=lambda: {
        k: set(v) for k, v in SKILL_CONTEXT_INDICATORS.items()
    })
    tech_patterns: Dict[str, List[str]] = field(default_factory=lambda: TECH_PATTERNS)
    
    # Advanced ML configuration
    ml_config: AdvancedMLConfig = field(default_factory=AdvancedMLConfig)
    
    # Enhanced weights
    extraction_weights: EnhancedExtractionWeights = field(default_factory=EnhancedExtractionWeights)
    category_weights: CategoryWeights = field(default_factory=CategoryWeights)
    
    # Context extraction
    context_window: int = 60  # Increased for better context
    max_context_length: int = 200
    
    # Filtering configuration
    min_skill_length: int = 2
    max_skill_length: int = 40
    confidence_threshold: float = 0.6
    
    # Section filtering (improved)
    relevant_sections: List[str] = field(default_factory=lambda: [
        'responsibilities', 'requirements', 'qualifications', 'skills',
        'experience', 'technical requirements', 'must have', 'nice to have',
        'what you will do', 'what we are looking for', 'about you',
        'key responsibilities', 'role overview', 'technical skills',
        'required skills', 'preferred skills', 'core competencies',
        'technologies used', 'tech stack', 'tools and technologies'
    ])
    
    excluded_sections: List[str] = field(default_factory=lambda: [
        'benefits', 'compensation', 'salary', 'perks', 'about us',
        'company culture', 'our mission', 'equal opportunity', 'diversity',
        'how to apply', 'application process', 'contact us', 'location'
    ])
    
    # Noise filtering
    noise_words: Set[str] = field(default_factory=lambda: {
        'new york', 'san francisco', 'los angeles', 'london', 'berlin',
        'remote', 'hybrid', 'full time', 'part time', 'contract',
        'competitive salary', 'health insurance', 'work life balance',
        'team player', 'fast paced', 'dynamic environment', 'startup',
        'unicorn', 'scale up', 'growth company', 'innovative', 'cutting edge'
    })
    
    # Skill prioritization
    high_priority_categories: Set[str] = field(default_factory=lambda: {
        'programming_languages', 'web_frameworks', 'cloud_platforms',
        'machine_learning', 'devops_tools', 'databases'
    })
    
    @property
    def full_dataset_id(self) -> str:
        """Return fully qualified dataset ID."""
        return f"{self.project_id}.{self.dataset_id}"
    
    def get_category_weight(self, category: str) -> float:
        """Get weight for a specific category."""
        return getattr(self.category_weights, category, 0.5)
    
    def is_high_priority_category(self, category: str) -> bool:
        """Check if category is high priority."""
        return category in self.high_priority_categories