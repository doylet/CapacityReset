"""
Configuration Module

Provides YAML configuration loading utilities and centralized access
to model configurations, skill aliases, and other runtime settings.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import YAML - it should be in requirements but handle gracefully
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.warning("PyYAML not available. YAML configuration loading disabled.")

# Configuration directory path
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def load_yaml_file(filename: str) -> Optional[Dict[str, Any]]:
    """
    Load a YAML configuration file.
    
    Args:
        filename: Name of the YAML file (e.g., "model_versions.yaml")
        
    Returns:
        Dictionary with YAML contents or None if not found/error
    """
    if not YAML_AVAILABLE:
        logger.error("Cannot load YAML file: PyYAML not installed")
        return None
    
    filepath = CONFIG_DIR / filename
    
    if not filepath.exists():
        logger.warning(f"Configuration file not found: {filepath}")
        return None
    
    try:
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
            logger.debug(f"Loaded configuration from {filepath}")
            return data
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading configuration file {filepath}: {e}")
        return None


def load_model_versions() -> Dict[str, Any]:
    """
    Load model version registry from YAML.
    
    Returns:
        Dictionary with model configurations
    """
    data = load_yaml_file("model_versions.yaml")
    return data.get("models", {}) if data else {}


def load_skill_aliases() -> List[Dict[str, Any]]:
    """
    Load skill aliases from YAML.
    
    Returns:
        List of alias mappings
    """
    data = load_yaml_file("skill_aliases.yaml")
    return data.get("aliases", []) if data else []


def load_alias_config() -> Dict[str, Any]:
    """
    Load alias configuration settings.
    
    Returns:
        Dictionary with alias configuration
    """
    data = load_yaml_file("skill_aliases.yaml")
    return data.get("config", {}) if data else {}


def load_model_config(model_id: str) -> Optional['ModelConfig']:
    """
    Load a specific model configuration from YAML.
    
    Args:
        model_id: The model identifier (e.g., "skills_extractor")
        
    Returns:
        ModelConfig instance or None if not found
    """
    from .model_config import ModelConfig
    
    models = load_model_versions()
    model_data = models.get(model_id)
    
    if not model_data:
        logger.warning(f"Model configuration not found for: {model_id}")
        return None
    
    # Find active version
    active_version = None
    for version_info in model_data.get("versions", []):
        if version_info.get("is_active", False):
            active_version = version_info
            break
    
    if not active_version:
        logger.warning(f"No active version found for model: {model_id}")
        return None
    
    # Parse created_at timestamp
    created_at = datetime.utcnow()
    if active_version.get("created_at"):
        try:
            timestamp_str = active_version["created_at"]
            # Handle 'Z' suffix for UTC timezone
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]  # Remove 'Z'
            created_at = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            pass
    
    try:
        return ModelConfig(
            model_id=model_data.get("model_id", model_id),
            version=active_version["version"],
            model_type=model_data.get("model_type", "skills_extraction"),
            created_at=created_at,
            updated_at=created_at,
            description=active_version.get("description", ""),
            performance_metrics=active_version.get("performance_metrics"),
            config_overrides=active_version.get("config"),
            is_active=True
        )
    except Exception as e:
        logger.error(f"Error creating ModelConfig for {model_id}: {e}")
        return None


def get_current_version(model_id: str) -> Optional[str]:
    """
    Get the current active version for a model.
    
    Args:
        model_id: The model identifier
        
    Returns:
        Version string or None
    """
    models = load_model_versions()
    model_data = models.get(model_id)
    
    if model_data:
        return model_data.get("current_version")
    return None


def get_legacy_version() -> str:
    """
    Get the legacy version identifier for enrichments without version tracking.
    
    Returns:
        Legacy version string (default: "legacy")
    """
    data = load_yaml_file("model_versions.yaml")
    return data.get("legacy_version", "legacy") if data else "legacy"


def get_default_config(key: str, default: Any = None) -> Any:
    """
    Get a default configuration value.
    
    Args:
        key: Configuration key
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    data = load_yaml_file("model_versions.yaml")
    if data:
        return data.get("defaults", {}).get(key, default)
    return default


class AliasResolver:
    """
    Resolves skill aliases to canonical names.
    
    Uses O(1) hash lookup after initial index build at startup.
    Tracks resolution statistics for monitoring and debugging.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize alias resolver (only once due to singleton)."""
        if self._initialized:
            return
        
        self._initialized = True
        self._alias_index: Dict[str, Dict[str, Any]] = {}
        self._config = load_alias_config()
        self._build_index()
        self._reset_stats()
    
    def _reset_stats(self):
        """Reset resolution statistics."""
        self._stats = {
            'total_lookups': 0,
            'successful_resolutions': 0,
            'failed_resolutions': 0,
            'resolutions_by_category': {}
        }
    
    def _build_index(self):
        """Build alias lookup index for O(1) access."""
        aliases = load_skill_aliases()
        case_sensitive = self._config.get("case_sensitive", False)
        
        for alias_entry in aliases:
            alias_text = alias_entry.get("alias", "")
            if not alias_text:
                continue
            
            key = alias_text if case_sensitive else alias_text.lower()
            
            # Store the mapping with all metadata
            self._alias_index[key] = {
                "canonical": alias_entry.get("canonical", alias_text),
                "category": alias_entry.get("category", "technical_skills"),
                "confidence": alias_entry.get("confidence", 1.0),
                "source": alias_entry.get("source", "manual")
            }
        
        logger.info(f"Built alias index with {len(self._alias_index)} entries")
    
    def resolve(self, skill_text: str) -> Optional[str]:
        """
        Resolve a skill alias to its canonical name.
        
        Args:
            skill_text: The skill text to resolve
            
        Returns:
            Canonical name or None if not an alias
        """
        if not skill_text:
            return None
        
        self._stats['total_lookups'] += 1
        
        case_sensitive = self._config.get("case_sensitive", False)
        key = skill_text if case_sensitive else skill_text.lower()
        
        entry = self._alias_index.get(key)
        if entry:
            self._stats['successful_resolutions'] += 1
            category = entry.get('category', 'unknown')
            self._stats['resolutions_by_category'][category] = \
                self._stats['resolutions_by_category'].get(category, 0) + 1
            return entry.get("canonical")
        
        self._stats['failed_resolutions'] += 1
        return None
    
    def get_alias_info(self, skill_text: str) -> Optional[Dict[str, Any]]:
        """
        Get full alias information including confidence and category.
        
        Args:
            skill_text: The skill text to look up
            
        Returns:
            Dictionary with alias info or None
        """
        if not skill_text:
            return None
        
        case_sensitive = self._config.get("case_sensitive", False)
        key = skill_text if case_sensitive else skill_text.lower()
        
        return self._alias_index.get(key)
    
    def is_alias(self, skill_text: str) -> bool:
        """Check if text is a known alias."""
        if not skill_text:
            return False
        
        case_sensitive = self._config.get("case_sensitive", False)
        key = skill_text if case_sensitive else skill_text.lower()
        
        return key in self._alias_index
    
    def get_all_aliases(self) -> Dict[str, str]:
        """Get all alias to canonical mappings."""
        return {
            alias: info["canonical"]
            for alias, info in self._alias_index.items()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get resolution statistics.
        
        Returns:
            Dictionary with resolution statistics
        """
        stats = self._stats.copy()
        stats['total_aliases_loaded'] = len(self._alias_index)
        if stats['total_lookups'] > 0:
            stats['resolution_rate'] = round(
                stats['successful_resolutions'] / stats['total_lookups'], 4
            )
        else:
            stats['resolution_rate'] = 0.0
        return stats
    
    def reset_stats(self):
        """Reset resolution statistics (for testing or batch processing)."""
        self._reset_stats()
    
    def reload(self):
        """Reload aliases from YAML (for runtime updates)."""
        self._alias_index = {}
        self._config = load_alias_config()
        self._build_index()
        self._reset_stats()
        logger.info("Reloaded alias index")


def get_alias_resolver() -> AliasResolver:
    """Get the singleton alias resolver instance."""
    return AliasResolver()


# Export commonly used items
from .model_config import (
    ModelConfig,
    ModelVersionInfo,
    get_model_config,
    register_model_config,
    list_registered_models,
    clear_model_configs
)

__all__ = [
    # YAML loading
    'load_yaml_file',
    'load_model_versions',
    'load_skill_aliases',
    'load_alias_config',
    'load_model_config',
    'get_current_version',
    'get_legacy_version',
    'get_default_config',
    
    # Model config
    'ModelConfig',
    'ModelVersionInfo',
    'get_model_config',
    'register_model_config',
    'list_registered_models',
    'clear_model_configs',
    
    # Alias resolution
    'AliasResolver',
    'get_alias_resolver',
]
