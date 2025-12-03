"""
SkillAliasRepository Interface

Defines the port for skill alias storage operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from ..entities import SkillAlias


class SkillAliasRepository(ABC):
    """
    Abstract interface for skill alias storage.
    
    This is a port in the hexagonal architecture - implementations
    (adapters) provide concrete storage mechanisms.
    """
    
    @abstractmethod
    def save(self, alias: SkillAlias) -> None:
        """
        Save a skill alias.
        
        Args:
            alias: The SkillAlias to save
        """
        pass
    
    @abstractmethod
    def save_batch(self, aliases: List[SkillAlias]) -> int:
        """
        Save multiple skill aliases in a batch.
        
        Args:
            aliases: List of SkillAlias objects to save
            
        Returns:
            Number of successfully saved aliases
        """
        pass
    
    @abstractmethod
    def find_by_alias_text(self, alias_text: str) -> Optional[SkillAlias]:
        """
        Find a skill alias by its alias text.
        
        Args:
            alias_text: The alias text to search for
            
        Returns:
            SkillAlias if found, None otherwise
        """
        pass
    
    @abstractmethod
    def find_by_canonical_name(self, canonical_name: str) -> List[SkillAlias]:
        """
        Find all aliases that map to a canonical name.
        
        Args:
            canonical_name: The canonical skill name
            
        Returns:
            List of SkillAlias objects
        """
        pass
    
    @abstractmethod
    def find_by_category(self, category: str) -> List[SkillAlias]:
        """
        Find all aliases in a category.
        
        Args:
            category: The skill category
            
        Returns:
            List of SkillAlias objects
        """
        pass
    
    @abstractmethod
    def find_all_active(self) -> List[SkillAlias]:
        """
        Find all active aliases.
        
        Returns:
            List of active SkillAlias objects
        """
        pass
    
    @abstractmethod
    def get_alias_mapping(self) -> Dict[str, str]:
        """
        Get a dictionary mapping all aliases to canonical names.
        
        Returns:
            Dictionary with alias_text (lowercase) as key, canonical_name as value
        """
        pass
    
    @abstractmethod
    def update(self, alias: SkillAlias) -> None:
        """
        Update an existing skill alias.
        
        Args:
            alias: The SkillAlias to update
        """
        pass
    
    @abstractmethod
    def deactivate(self, alias_id: str) -> None:
        """
        Deactivate a skill alias.
        
        Args:
            alias_id: The ID of the alias to deactivate
        """
        pass
    
    @abstractmethod
    def record_usage(self, alias_text: str) -> None:
        """
        Record that an alias was used for resolution.
        
        Args:
            alias_text: The alias text that was used
        """
        pass
    
    @abstractmethod
    def get_usage_stats(self, limit: int = 100) -> List[Dict]:
        """
        Get usage statistics for aliases.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of dictionaries with usage statistics
        """
        pass
