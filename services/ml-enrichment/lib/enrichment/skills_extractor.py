"""
Skills Extractor Module

Extracts skills, technologies, tools, and certifications from job postings
using spaCy NLP and pattern matching.
"""

import spacy
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.cloud import bigquery

# Don't load model at module level - lazy load instead
_nlp = None

def get_nlp():
    """Lazy load spaCy model."""
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp

# Technology keywords and categories
TECH_KEYWORDS = {
    'programming_language': [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
        'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html', 'css'
    ],
    'framework': [
        'react', 'angular', 'vue', 'django', 'flask', 'spring', 'node.js', 'express',
        'fastapi', 'rails', 'laravel', '.net', 'asp.net', 'next.js', 'nuxt', 'svelte'
    ],
    'database': [
        'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb',
        'cassandra', 'oracle', 'sql server', 'sqlite', 'neo4j', 'bigquery'
    ],
    'cloud': [
        'aws', 'azure', 'gcp', 'google cloud', 'amazon web services', 'kubernetes',
        'docker', 'terraform', 'cloudformation', 'cloud run', 'lambda', 'ec2', 's3'
    ],
    'tool': [
        'git', 'github', 'gitlab', 'jira', 'confluence', 'jenkins', 'circleci',
        'travis ci', 'ansible', 'puppet', 'chef', 'grafana', 'prometheus', 'datadog'
    ],
    'data_science': [
        'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
        'spark', 'hadoop', 'airflow', 'dbt', 'tableau', 'power bi', 'looker'
    ],
    'soft_skill': [
        'leadership', 'communication', 'problem solving', 'teamwork', 'agile',
        'scrum', 'project management', 'stakeholder management', 'mentoring'
    ]
}


class SkillsExtractor:
    """Extract skills from job descriptions using NLP and pattern matching."""
    
    def __init__(self):
        self.version = "v1.0-spacy-en_core_web_sm"
        self.bigquery_client = bigquery.Client()
        self.project_id = "sylvan-replica-478802-p4"
        self.dataset_id = f"{self.project_id}.brightdata_jobs"
    
    def get_version(self) -> str:
        """Return extractor version identifier."""
        return self.version
    
    def extract_skills(self, job_summary: str, job_description: str) -> List[Dict[str, Any]]:
        """
        Extract skills from job text.
        
        Args:
            job_summary: Brief job summary
            job_description: Full job description
            
        Returns:
            List of skill dictionaries with name, category, confidence, context
        """
        skills = []
        
        # Combine texts for analysis
        texts = {
            'job_summary': job_summary or '',
            'job_description_formatted': job_description or ''
        }
        
        for source_field, text in texts.items():
            if not text:
                continue
            
            # Convert to lowercase for matching
            text_lower = text.lower()
            
            # Process with spaCy
            nlp = get_nlp()
            doc = nlp(text)
            
            # Extract skills by category
            for category, keywords in TECH_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        # Find context snippet
                        context = self._extract_context(text, keyword)
                        
                        # Calculate confidence based on mentions
                        mentions = text_lower.count(keyword)
                        confidence = min(0.5 + (mentions * 0.1), 1.0)
                        
                        skills.append({
                            'skill_name': keyword.title(),
                            'skill_category': category,
                            'source_field': source_field,
                            'confidence_score': confidence,
                            'context_snippet': context
                        })
        
        # Deduplicate skills (keep highest confidence)
        unique_skills = {}
        for skill in skills:
            key = (skill['skill_name'].lower(), skill['skill_category'])
            if key not in unique_skills or skill['confidence_score'] > unique_skills[key]['confidence_score']:
                unique_skills[key] = skill
        
        return list(unique_skills.values())
    
    def _extract_context(self, text: str, keyword: str, window: int = 50) -> str:
        """Extract surrounding context for a keyword."""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        pos = text_lower.find(keyword_lower)
        if pos == -1:
            return ""
        
        start = max(0, pos - window)
        end = min(len(text), pos + len(keyword) + window)
        
        context = text[start:end]
        
        # Clean up
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        
        return context.strip()
    
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
                'created_at': datetime.utcnow().isoformat()
            })
        
        table_id = f"{self.dataset_id}.job_skills"
        errors = self.bigquery_client.insert_rows_json(table_id, rows)
        
        if errors:
            raise Exception(f"Failed to store skills: {errors}")
