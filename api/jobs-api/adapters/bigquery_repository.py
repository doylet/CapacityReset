"""
BigQuery Adapter - Persistence implementation (Hexagon Adapter)

Implements repository ports using BigQuery as the data source.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from google.cloud import bigquery
from domain.entities import Job, Skill, Cluster, SkillLexiconEntry, SkillType
from domain.repositories import JobRepository, SkillRepository, ClusterRepository, SkillLexiconRepository


PROJECT_ID = "sylvan-replica-478802-p4"
DATASET_ID = f"{PROJECT_ID}.brightdata_jobs"


class BigQueryJobRepository(JobRepository):
    """BigQuery implementation of JobRepository."""
    
    def __init__(self):
        self.client = bigquery.Client()
    
    async def list_jobs(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Job]:
        """List jobs with filters."""
        where_clauses = []
        
        if filters:
            if 'date_from' in filters:
                where_clauses.append(f"jp.job_posted_date >= '{filters['date_from']}'")
            if 'date_to' in filters:
                where_clauses.append(f"jp.job_posted_date <= '{filters['date_to']}'")
            if 'location' in filters:
                where_clauses.append(f"LOWER(jp.job_location) LIKE LOWER('%{filters['location']}%')")
            if 'cluster_id' in filters:
                where_clauses.append(f"jc.cluster_id = {filters['cluster_id']}")
            if 'skill_name' in filters:
                where_clauses.append(f"LOWER(js.skill_name) LIKE LOWER('%{filters['skill_name']}%')")
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        query = f"""
        WITH job_skill_counts AS (
            SELECT 
                job_posting_id,
                COUNT(*) as skills_count
            FROM `{DATASET_ID}.job_skills`
            GROUP BY job_posting_id
        )
        SELECT DISTINCT
            jp.job_posting_id,
            jp.job_title,
            jp.company_name,
            jp.job_location,
            jp.job_summary,
            jp.job_description_formatted,
            jp.job_posted_date,
            COALESCE(jsc.skills_count, 0) as skills_count
        FROM `{DATASET_ID}.job_postings` jp
        LEFT JOIN `{DATASET_ID}.job_clusters` jc ON jp.job_posting_id = jc.job_posting_id
        LEFT JOIN `{DATASET_ID}.job_skills` js ON jp.job_posting_id = js.job_posting_id
        LEFT JOIN job_skill_counts jsc ON jp.job_posting_id = jsc.job_posting_id
        {where_sql}
        ORDER BY jp.job_posted_date DESC
        LIMIT {limit}
        OFFSET {offset}
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        jobs = []
        for row in results:
            job = Job(
                job_posting_id=row['job_posting_id'],
                job_title=row['job_title'],
                company_name=row['company_name'],
                job_location=row['job_location'],
                job_summary=row['job_summary'],
                job_description_formatted=row['job_description_formatted'],
                job_posted_date=row['job_posted_date'],
                skills_count=row['skills_count']
            )
            jobs.append(job)
        
        return jobs
    
    async def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Get single job by ID."""
        query = f"""
        WITH job_skill_counts AS (
            SELECT 
                job_posting_id,
                COUNT(*) as skills_count
            FROM `{DATASET_ID}.job_skills`
            GROUP BY job_posting_id
        )
        SELECT
            jp.job_posting_id,
            jp.job_title,
            jp.company_name,
            jp.job_location,
            jp.job_summary,
            jp.job_description_formatted,
            jp.job_posted_date,
            COALESCE(jsc.skills_count, 0) as skills_count
        FROM `{DATASET_ID}.job_postings` jp
        LEFT JOIN job_skill_counts jsc ON jp.job_posting_id = jsc.job_posting_id
        WHERE jp.job_posting_id = '{job_id}'
        """
        
        query_job = self.client.query(query)
        results = list(query_job.result())
        
        if not results:
            return None
        
        row = results[0]
        return Job(
            job_posting_id=row['job_posting_id'],
            job_title=row['job_title'],
            company_name=row['company_name'],
            job_location=row['job_location'],
            job_summary=row['job_summary'],
            job_description_formatted=row['job_description_formatted'],
            job_posted_date=row['job_posted_date'],
            skills_count=row['skills_count']
        )
    
    async def get_jobs_by_ids(self, job_ids: List[str]) -> List[Job]:
        """Get multiple jobs for report generation."""
        ids_str = "', '".join(job_ids)
        query = f"""
        WITH job_skill_counts AS (
            SELECT 
                job_posting_id,
                COUNT(*) as skills_count
            FROM `{DATASET_ID}.job_skills`
            GROUP BY job_posting_id
        )
        SELECT
            jp.job_posting_id,
            jp.job_title,
            jp.company_name,
            jp.job_location,
            jp.job_summary,
            jp.job_description_formatted,
            jp.job_posted_date,
            COALESCE(jsc.skills_count, 0) as skills_count
        FROM `{DATASET_ID}.job_postings` jp
        LEFT JOIN job_skill_counts jsc ON jp.job_posting_id = jsc.job_posting_id
        WHERE jp.job_posting_id IN ('{ids_str}')
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        jobs = []
        for row in results:
            job = Job(
                job_posting_id=row['job_posting_id'],
                job_title=row['job_title'],
                company_name=row['company_name'],
                job_location=row['job_location'],
                job_summary=row['job_summary'],
                job_description_formatted=row['job_description_formatted'],
                job_posted_date=row['job_posted_date'],
                skills_count=row['skills_count']
            )
            jobs.append(job)
        
        return jobs


class BigQuerySkillRepository(SkillRepository):
    """BigQuery implementation of SkillRepository."""
    
    def __init__(self):
        self.client = bigquery.Client()
    
    async def get_skills_for_job(self, job_id: str) -> List[Skill]:
        """Get all skills for a job."""
        query = f"""
        SELECT
            skill_id,
            job_posting_id,
            skill_name,
            skill_category,
            confidence_score,
            context_snippet,
            'lexicon_match' as extraction_method,
            created_at
        FROM `{DATASET_ID}.job_skills`
        WHERE job_posting_id = '{job_id}'
        ORDER BY confidence_score DESC
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        skills = []
        for row in results:
            skill = Skill(
                skill_id=row['skill_id'],
                job_posting_id=row['job_posting_id'],
                skill_name=row['skill_name'],
                skill_category=row['skill_category'],
                confidence_score=row['confidence_score'],
                context_snippet=row['context_snippet'],
                extraction_method=row['extraction_method'],
                created_at=row['created_at']
            )
            skills.append(skill)
        
        return skills
    
    async def update_skill(self, skill: Skill) -> Skill:
        """Update skill metadata."""
        # TODO: Implement skill metadata updates
        # For now, return skill as-is
        return skill
    
    async def add_skill_to_job(self, job_id: str, skill: Skill) -> Skill:
        """Add user-defined skill to job."""
        # TODO: Insert into job_skills table
        return skill
    
    async def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill."""
        # TODO: Implement deletion
        return True


class BigQueryClusterRepository(ClusterRepository):
    """BigQuery implementation of ClusterRepository."""
    
    def __init__(self):
        self.client = bigquery.Client()
    
    async def get_cluster_for_job(self, job_id: str) -> Optional[Cluster]:
        """Get cluster for a job."""
        query = f"""
        SELECT
            cluster_id,
            cluster_name,
            cluster_keywords,
            cluster_size
        FROM `{DATASET_ID}.job_clusters`
        WHERE job_posting_id = '{job_id}'
        LIMIT 1
        """
        
        query_job = self.client.query(query)
        results = list(query_job.result())
        
        if not results:
            return None
        
        row = results[0]
        return Cluster(
            cluster_id=row['cluster_id'],
            cluster_name=row['cluster_name'],
            cluster_keywords=row['cluster_keywords'],  # Already JSON
            cluster_size=row['cluster_size']
        )
    
    async def list_all_clusters(self) -> List[Cluster]:
        """Get all clusters."""
        query = f"""
        SELECT
            cluster_id,
            ANY_VALUE(cluster_name) as cluster_name,
            ANY_VALUE(cluster_keywords) as cluster_keywords,
            ANY_VALUE(cluster_size) as cluster_size
        FROM `{DATASET_ID}.job_clusters`
        GROUP BY cluster_id
        ORDER BY ANY_VALUE(cluster_size) DESC
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        clusters = []
        for row in results:
            cluster = Cluster(
                cluster_id=row['cluster_id'],
                cluster_name=row['cluster_name'],
                cluster_keywords=row['cluster_keywords'],
                cluster_size=row['cluster_size']
            )
            clusters.append(cluster)
        
        return clusters


class InMemorySkillLexiconRepository(SkillLexiconRepository):
    """In-memory lexicon repository (TODO: persist to BigQuery or file)."""
    
    def __init__(self):
        self.lexicon: Dict[str, SkillLexiconEntry] = {}
    
    async def get_lexicon(self) -> List[SkillLexiconEntry]:
        """Get all lexicon entries."""
        return list(self.lexicon.values())
    
    async def add_to_lexicon(self, entry: SkillLexiconEntry) -> SkillLexiconEntry:
        """Add entry to lexicon."""
        self.lexicon[entry.skill_name.lower()] = entry
        return entry
    
    async def update_lexicon_entry(self, entry: SkillLexiconEntry) -> SkillLexiconEntry:
        """Update lexicon entry."""
        self.lexicon[entry.skill_name.lower()] = entry
        return entry
    
    async def get_lexicon_by_category(self, category: str) -> List[SkillLexiconEntry]:
        """Get lexicon by category."""
        return [e for e in self.lexicon.values() if e.skill_category == category]
