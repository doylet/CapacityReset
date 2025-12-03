"""
Model Configuration Module

Centralized configuration for all ML models in the enrichment pipeline.
Supports model version tracking, configuration management, and performance metrics.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """
    Configuration for an ML model with version tracking.
    
    Version format: v{major}.{minor}[-{suffix}]
    Examples:
        - skills_extractor_v4.0-unified-config-enhanced
        - job_clusterer_v1.0-kmeans-tfidf
        - embeddings_generator_v1.0-vertex-ai
    """
    
    # Required fields
    model_id: str              # e.g., "skills_extractor"
    version: str               # e.g., "v4.0-unified-config-enhanced"
    model_type: str            # "skills_extraction" | "embeddings" | "clustering" | "section_classification"
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    description: str = ""
    
    # Optional training info
    training_data_version: Optional[str] = None
    training_date: Optional[datetime] = None
    
    # Performance tracking
    performance_metrics: Optional[Dict[str, float]] = None
    
    # Runtime config
    config_overrides: Optional[Dict[str, Any]] = None
    is_active: bool = True
    
    # Validation patterns
    MODEL_ID_PATTERN = re.compile(r'^[a-z_]+$')
    VERSION_PATTERN = re.compile(r'^v\d+\.\d+(-[a-z0-9-]+)?$')
    VALID_MODEL_TYPES = {
        'skills_extraction',
        'embeddings',
        'clustering',
        'section_classification'
    }
    
    def __post_init__(self):
        """Validate model configuration after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate all fields."""
        # Validate model_id
        if not self.MODEL_ID_PATTERN.match(self.model_id):
            raise ValueError(
                f"Invalid model_id '{self.model_id}'. "
                f"Must match pattern: lowercase with underscores only"
            )
        
        # Validate version
        if not self.VERSION_PATTERN.match(self.version):
            raise ValueError(
                f"Invalid version '{self.version}'. "
                f"Must match pattern: v{{major}}.{{minor}}[-{{suffix}}]"
            )
        
        # Validate model_type
        if self.model_type not in self.VALID_MODEL_TYPES:
            raise ValueError(
                f"Invalid model_type '{self.model_type}'. "
                f"Must be one of: {self.VALID_MODEL_TYPES}"
            )
        
        # Validate timestamps
        if self.created_at > self.updated_at:
            raise ValueError("created_at must be <= updated_at")
        
        # Validate performance metrics if provided
        if self.performance_metrics:
            for key, value in self.performance_metrics.items():
                if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                    raise ValueError(
                        f"Performance metric '{key}' must be a float between 0.0 and 1.0"
                    )
    
    def get_full_version_id(self) -> str:
        """Get full version identifier including model_id."""
        return f"{self.model_id}_{self.version}"
    
    def update_performance_metrics(self, metrics: Dict[str, float]):
        """Update performance metrics and timestamp."""
        if self.performance_metrics is None:
            self.performance_metrics = {}
        self.performance_metrics.update(metrics)
        self.updated_at = datetime.utcnow()
        logger.info(f"Updated performance metrics for {self.model_id}: {metrics}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'model_id': self.model_id,
            'version': self.version,
            'model_type': self.model_type,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'description': self.description,
            'training_data_version': self.training_data_version,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'performance_metrics': self.performance_metrics,
            'config_overrides': self.config_overrides,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """Create from dictionary."""
        return cls(
            model_id=data['model_id'],
            version=data['version'],
            model_type=data['model_type'],
            created_at=datetime.fromisoformat(data.get('created_at', datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.utcnow().isoformat())),
            description=data.get('description', ''),
            training_data_version=data.get('training_data_version'),
            training_date=datetime.fromisoformat(data['training_date']) if data.get('training_date') else None,
            performance_metrics=data.get('performance_metrics'),
            config_overrides=data.get('config_overrides'),
            is_active=data.get('is_active', True)
        )


@dataclass
class ModelVersionInfo:
    """Information about a specific model version."""
    version: str
    is_active: bool
    created_at: datetime
    description: str = ""
    performance_metrics: Optional[Dict[str, float]] = None
    config: Optional[Dict[str, Any]] = None


# Singleton instances for model configs
_model_configs: Dict[str, ModelConfig] = {}


def get_model_config(model_id: str) -> Optional[ModelConfig]:
    """
    Get model configuration by ID.
    
    Implements singleton pattern for lazy loading.
    
    Args:
        model_id: The model identifier (e.g., "skills_extractor")
        
    Returns:
        ModelConfig or None if not found
    """
    global _model_configs
    
    if model_id not in _model_configs:
        # Try to load from YAML configuration
        from . import load_model_config
        config = load_model_config(model_id)
        if config:
            _model_configs[model_id] = config
    
    return _model_configs.get(model_id)


def register_model_config(config: ModelConfig):
    """
    Register a model configuration.
    
    Args:
        config: The ModelConfig to register
    """
    global _model_configs
    _model_configs[config.model_id] = config
    logger.info(f"Registered model config: {config.model_id} v{config.version}")


def list_registered_models() -> List[str]:
    """List all registered model IDs."""
    return list(_model_configs.keys())


def clear_model_configs():
    """Clear all registered model configs (for testing)."""
    global _model_configs
    _model_configs = {}
