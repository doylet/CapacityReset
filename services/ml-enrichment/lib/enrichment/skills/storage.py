"""
Storage interfaces and implementations for extracted skills.
"""

import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
from google.cloud import bigquery


class SkillsStorage(ABC):
    """Abstract interface for skills storage."""
    
    @abstractmethod
    def store_skills(self, job_posting_id: str, enrichment_id: str, skills: List[Dict[str, Any]]):
        """
        Store extracted skills.
        
        Args:
            job_posting_id: Job reference
            enrichment_id: Enrichment tracking reference
            skills: List of extracted skills
        """
        pass


class BigQuerySkillsStorage(SkillsStorage):
    """BigQuery implementation of skills storage."""
    
    def __init__(self, project_id: str, dataset_id: str):
        """
        Initialize storage with BigQuery configuration.
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
        """
        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.full_dataset_id = f"{project_id}.{dataset_id}"
    
    def store_skills(self, job_posting_id: str, enrichment_id: str, skills: List[Dict[str, Any]]):
        """
        Store extracted skills in BigQuery.
        
        Args:
            job_posting_id: Job reference
            enrichment_id: Enrichment tracking reference
            skills: List of extracted skills
        """
        if not skills:
            return
        
        rows = []
        for skill in skills:
            rows.append({
                'skill_id': str(uuid.uuid4()),
                'job_posting_id': job_posting_id,
                'enrichment_id': enrichment_id,
                'skill_name': skill['skill_name'],
                'skill_category': skill['skill_category'],
                'source_field': skill['source_field'],
                'confidence_score': skill['confidence_score'],
                'context_snippet': skill['context_snippet'],
                'is_approved': None,  # Pending approval by default
                'created_at': datetime.utcnow().isoformat()
            })
        
        table_id = f"{self.full_dataset_id}.job_skills"
        errors = self.client.insert_rows_json(table_id, rows)
        
        if errors:
            raise Exception(f"Failed to store skills: {errors}")


class InMemorySkillsStorage(SkillsStorage):
    """In-memory storage for testing purposes."""
    
    def __init__(self):
        """Initialize in-memory storage."""
        self.skills = []
    
    def store_skills(self, job_posting_id: str, enrichment_id: str, skills: List[Dict[str, Any]]):
        """
        Store extracted skills in memory.
        
        Args:
            job_posting_id: Job reference
            enrichment_id: Enrichment tracking reference
            skills: List of extracted skills
        """
        for skill in skills:
            self.skills.append({
                'job_posting_id': job_posting_id,
                'enrichment_id': enrichment_id,
                **skill
            })
    
    def get_all_skills(self) -> List[Dict[str, Any]]:
        """Return all stored skills."""
        return self.skills
    
    def clear(self):
        """Clear all stored skills."""
        self.skills = []
