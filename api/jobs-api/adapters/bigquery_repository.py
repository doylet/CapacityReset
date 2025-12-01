"""
BigQuery Adapter - Persistence implementation (Hexagon Adapter)

Implements repository ports using BigQuery as the data source.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from google.cloud import bigquery
from domain.entities import Job, Skill, Cluster, SkillLexiconEntry, SkillType, SectionAnnotation, AnnotationLabel
from domain.repositories import JobRepository, SkillRepository, ClusterRepository, SkillLexiconRepository, SectionAnnotationRepository


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
            jp.company_url,
            jp.company_logo,
            jp.job_location,
            jp.job_summary,
            jp.job_description_formatted,
            jp.job_posted_date,
            jp.url as job_url,
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
                company_url=row.get('company_url'),
                company_logo=row.get('company_logo'),
                job_location=row['job_location'],
                job_summary=row['job_summary'],
                job_description_formatted=row['job_description_formatted'],
                job_posted_date=row['job_posted_date'],
                job_url=row.get('job_url'),
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
            jp.company_url,
            jp.company_logo,
            jp.job_location,
            jp.job_summary,
            jp.job_description_formatted,
            jp.job_posted_date,
            jp.url as job_url,
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
            company_url=row.get('company_url'),
            company_logo=row.get('company_logo'),
            job_location=row['job_location'],
            job_summary=row['job_summary'],
            job_description_formatted=row['job_description_formatted'],
            job_posted_date=row['job_posted_date'],
            job_url=row.get('job_url'),
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
            jp.company_url,
            jp.company_logo,
            jp.job_location,
            jp.job_summary,
            jp.job_description_formatted,
            jp.job_posted_date,
            jp.url as job_url,
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
                company_url=row.get('company_url'),
                company_logo=row.get('company_logo'),
                job_location=row['job_location'],
                job_summary=row['job_summary'],
                job_description_formatted=row['job_description_formatted'],
                job_posted_date=row['job_posted_date'],
                job_url=row.get('job_url'),
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
            is_approved,
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
                is_approved=row.get('is_approved'),
                skill_type='general',  # Default skill type since it's not in DB schema yet
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
        import uuid
        enrichment_id = str(uuid.uuid4())
        
        # First create an enrichment record
        enrichment_query = f"""
        INSERT INTO `{DATASET_ID}.job_enrichments` (
            enrichment_id,
            job_posting_id,
            enrichment_type,
            enrichment_version,
            created_at,
            status,
            metadata
        ) VALUES (
            '{enrichment_id}',
            '{job_id}',
            'user_skill_addition',
            'manual_v1',
            CURRENT_TIMESTAMP(),
            'success',
            JSON_OBJECT('user_added', true, 'skill_name', '{skill.skill_name}')
        )
        """
        self.client.query(enrichment_query).result()
        
        # Then add the skill record
        skill_query = f"""
        INSERT INTO `{DATASET_ID}.job_skills` (
            skill_id,
            job_posting_id,
            enrichment_id,
            skill_name,
            skill_category,
            source_field,
            confidence_score,
            context_snippet,
            is_approved,
            created_at
        ) VALUES (
            '{skill.skill_id}',
            '{skill.job_posting_id}',
            '{enrichment_id}',
            '{skill.skill_name}',
            '{skill.skill_category}',
            'user_defined',
            {skill.confidence_score},
            '{skill.context_snippet.replace("'", "''")}',
            TRUE,
            CURRENT_TIMESTAMP()
        )
        """
        self.client.query(skill_query).result()
        
        # Set is_approved to True since user-defined skills are automatically approved
        skill.is_approved = True
        return skill
    
    async def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill."""
        query = f"""
        DELETE FROM `{DATASET_ID}.job_skills`
        WHERE skill_id = '{skill_id}'
        """
        self.client.query(query).result()
        return True
    
    async def approve_skill(self, skill_id: str) -> Skill:
        """Approve a suggested skill (sets is_approved=True)."""
        # Update skill to approved
        update_query = f"""
        UPDATE `{DATASET_ID}.job_skills`
        SET is_approved = TRUE
        WHERE skill_id = '{skill_id}'
        """
        self.client.query(update_query).result()
        
        # Fetch updated skill
        select_query = f"""
        SELECT
            skill_id,
            job_posting_id,
            skill_name,
            skill_category,
            confidence_score,
            context_snippet,
            'lexicon_match' as extraction_method,
            is_approved,
            created_at
        FROM `{DATASET_ID}.job_skills`
        WHERE skill_id = '{skill_id}'
        """
        result = list(self.client.query(select_query).result())
        
        if not result:
            raise ValueError(f"Skill {skill_id} not found")
        
        row = result[0]
        return Skill(
            skill_id=row['skill_id'],
            job_posting_id=row['job_posting_id'],
            skill_name=row['skill_name'],
            skill_category=row['skill_category'],
            confidence_score=row['confidence_score'],
            context_snippet=row['context_snippet'],
            extraction_method=row['extraction_method'],
            is_approved=row.get('is_approved'),
            skill_type='general',  # Default skill type since it's not in DB schema yet
            created_at=row['created_at']
        )
    
    async def reject_skill(self, skill_id: str) -> bool:
        """Reject a suggested skill (deletes it)."""
        return await self.delete_skill(skill_id)


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
        cluster_keywords = row['cluster_keywords']
        if isinstance(cluster_keywords, str):
            cluster_keywords = json.loads(cluster_keywords)
        return Cluster(
            cluster_id=row['cluster_id'],
            cluster_name=row['cluster_name'],
            cluster_keywords=cluster_keywords,
            cluster_size=row['cluster_size']
        )
    
    async def list_all_clusters(self) -> List[Cluster]:
        """Get all clusters."""
        query = f"""
        WITH unique_clusters AS (
            SELECT
                cluster_id,
                ANY_VALUE(cluster_name) as cluster_name,
                ANY_VALUE(cluster_keywords) as cluster_keywords,
                ANY_VALUE(cluster_size) as cluster_size
            FROM `{DATASET_ID}.job_clusters`
            GROUP BY cluster_id
        )
        SELECT
            cluster_id,
            cluster_name,
            cluster_keywords,
            cluster_size
        FROM unique_clusters
        ORDER BY cluster_size DESC
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        clusters = []
        for row in results:
            cluster_keywords = row['cluster_keywords']
            if isinstance(cluster_keywords, str):
                cluster_keywords = json.loads(cluster_keywords)
            cluster = Cluster(
                cluster_id=row['cluster_id'],
                cluster_name=row['cluster_name'],
                cluster_keywords=cluster_keywords,
                cluster_size=row['cluster_size']
            )
            clusters.append(cluster)
        
        return clusters


class InMemorySkillLexiconRepository(SkillLexiconRepository):
    """In-memory lexicon repository (DEPRECATED - use BigQuerySkillLexiconRepository)."""
    
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


class BigQuerySkillLexiconRepository(SkillLexiconRepository):
    """BigQuery-backed persistent skills lexicon."""
    
    def __init__(self):
        self.client = bigquery.Client()
    
    def _normalize_skill_name(self, name: str) -> str:
        """Normalize skill name for matching."""
        return name.lower().strip()
    
    async def get_lexicon(self) -> List[SkillLexiconEntry]:
        """Get all lexicon entries."""
        query = f"""
        SELECT
            skill_id,
            skill_name,
            skill_name_original,
            skill_category,
            skill_type,
            source,
            usage_count,
            confidence_sum,
            user_corrections,
            aliases,
            first_seen,
            last_updated,
            created_by_user_id
        FROM `{DATASET_ID}.skills_lexicon`
        ORDER BY usage_count DESC, skill_name
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        entries = []
        for row in results:
            entry = SkillLexiconEntry(
                skill_name=row['skill_name'],
                skill_category=row['skill_category'],
                skill_type=SkillType(row['skill_type']) if row['skill_type'] else SkillType.GENERAL,
                added_by_user=row['source'] == 'USER_ADDED',
                usage_count=row['usage_count'],
                created_at=row['first_seen']
            )
            entries.append(entry)
        
        return entries
    
    async def add_to_lexicon(self, entry: SkillLexiconEntry) -> SkillLexiconEntry:
        """Add new skill to lexicon or update if exists."""
        import uuid
        from datetime import datetime
        
        normalized_name = self._normalize_skill_name(entry.skill_name)
        
        # Check if skill already exists
        check_query = f"""
        SELECT skill_id, usage_count, confidence_sum, user_corrections
        FROM `{DATASET_ID}.skills_lexicon`
        WHERE skill_name = '{normalized_name}'
        LIMIT 1
        """
        
        check_job = self.client.query(check_query)
        existing = list(check_job.result())
        
        if existing:
            # Update existing skill
            row = existing[0]
            update_query = f"""
            UPDATE `{DATASET_ID}.skills_lexicon`
            SET 
                usage_count = usage_count + 1,
                user_corrections = user_corrections + 1,
                last_updated = CURRENT_TIMESTAMP()
            WHERE skill_name = '{normalized_name}'
            """
            self.client.query(update_query).result()
        else:
            # Insert new skill
            now = datetime.utcnow().isoformat()
            insert_data = [{
                "skill_id": str(uuid.uuid4()),
                "skill_name": normalized_name,
                "skill_name_original": entry.skill_name,
                "skill_category": entry.skill_category,
                "skill_type": entry.skill_type.value if hasattr(entry.skill_type, 'value') else (entry.skill_type or "GENERAL"),
                "source": "USER_ADDED" if entry.added_by_user else "ML_EXTRACTED",
                "usage_count": 1,
                "confidence_sum": 1.0,
                "user_corrections": 1 if entry.added_by_user else 0,
                "aliases": [],
                "first_seen": now,
                "last_updated": now,
                "created_by_user_id": None
            }]
            
            errors = self.client.insert_rows_json(
                f"{DATASET_ID}.skills_lexicon",
                insert_data
            )
            
            if errors:
                raise Exception(f"Failed to insert skill: {errors}")
        
        return entry
    
    async def update_lexicon_entry(self, entry: SkillLexiconEntry) -> SkillLexiconEntry:
        """Update existing lexicon entry."""
        normalized_name = self._normalize_skill_name(entry.skill_name)
        
        update_query = f"""
        UPDATE `{DATASET_ID}.skills_lexicon`
        SET 
            skill_category = '{entry.skill_category}',
            skill_type = '{entry.skill_type.value if entry.skill_type else "GENERAL"}',
            last_updated = CURRENT_TIMESTAMP()
        WHERE skill_name = '{normalized_name}'
        """
        
        self.client.query(update_query).result()
        return entry
    
    async def get_lexicon_by_category(self, category: str) -> List[SkillLexiconEntry]:
        """Get lexicon entries for a specific category."""
        query = f"""
        SELECT
            skill_name,
            skill_name_original,
            skill_category,
            skill_type,
            source,
            usage_count,
            first_seen
        FROM `{DATASET_ID}.skills_lexicon`
        WHERE skill_category = '{category}'
        ORDER BY usage_count DESC, skill_name
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        entries = []
        for row in results:
            entry = SkillLexiconEntry(
                skill_name=row['skill_name'],
                skill_category=row['skill_category'],
                skill_type=SkillType(row['skill_type']) if row['skill_type'] else SkillType.GENERAL,
                added_by_user=row['source'] == 'USER_ADDED',
                usage_count=row['usage_count'],
                created_at=row['first_seen']
            )
            entries.append(entry)
        
        return entries
    
    async def search_skills(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search skills by name (for autocomplete)."""
        normalized_query = self._normalize_skill_name(query)
        
        search_query = f"""
        SELECT
            skill_id,
            skill_name,
            skill_name_original,
            skill_category,
            usage_count
        FROM `{DATASET_ID}.skills_lexicon`
        WHERE skill_name LIKE '%{normalized_query}%'
        ORDER BY usage_count DESC, skill_name
        LIMIT {limit}
        """
        
        query_job = self.client.query(search_query)
        results = query_job.result()
        
        skills = []
        for row in results:
            skills.append({
                "skill_id": row['skill_id'],
                "skill_name": row['skill_name_original'],
                "skill_category": row['skill_category'],
                "usage_count": row['usage_count']
            })
        
        return skills
    
    async def get_categories_with_counts(self) -> List[Dict[str, Any]]:
        """Get all skill categories with skill counts."""
        query = f"""
        SELECT
            skill_category,
            COUNT(*) as skill_count
        FROM `{DATASET_ID}.skills_lexicon`
        GROUP BY skill_category
        ORDER BY skill_category
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        categories = []
        for row in results:
            # Convert snake_case to Title Case
            display_name = row['skill_category'].replace('_', ' ').title()
            categories.append({
                "category": row['skill_category'],
                "display_name": display_name,
                "skill_count": row['skill_count']
            })
        
        return categories


class BigQuerySectionAnnotationRepository(SectionAnnotationRepository):
    """BigQuery implementation of SectionAnnotationRepository."""
    
    def __init__(self):
        self.client = bigquery.Client()
    
    async def create_annotation(self, annotation: SectionAnnotation) -> SectionAnnotation:
        """Store annotation in BigQuery."""
        query = f"""
        INSERT INTO `{DATASET_ID}.job_section_annotations` (
            annotation_id,
            job_posting_id,
            section_text,
            section_start_index,
            section_end_index,
            label,
            contains_skills,
            annotator_id,
            notes,
            created_at
        ) VALUES (
            @annotation_id,
            @job_posting_id,
            @section_text,
            @section_start_index,
            @section_end_index,
            @label,
            @contains_skills,
            @annotator_id,
            @notes,
            CURRENT_TIMESTAMP()
        )
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("annotation_id", "STRING", annotation.annotation_id),
                bigquery.ScalarQueryParameter("job_posting_id", "STRING", annotation.job_posting_id),
                bigquery.ScalarQueryParameter("section_text", "STRING", annotation.section_text),
                bigquery.ScalarQueryParameter("section_start_index", "INT64", annotation.section_start_index),
                bigquery.ScalarQueryParameter("section_end_index", "INT64", annotation.section_end_index),
                bigquery.ScalarQueryParameter("label", "STRING", annotation.label.value),
                bigquery.ScalarQueryParameter("contains_skills", "BOOL", annotation.contains_skills),
                bigquery.ScalarQueryParameter("annotator_id", "STRING", annotation.annotator_id),
                bigquery.ScalarQueryParameter("notes", "STRING", annotation.notes),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()  # Wait for completion
        
        return annotation
    
    async def get_annotation_by_id(self, annotation_id: str) -> Optional[SectionAnnotation]:
        """Get a single annotation by ID."""
        query = f"""
        SELECT
            annotation_id,
            job_posting_id,
            section_text,
            section_start_index,
            section_end_index,
            label,
            contains_skills,
            annotator_id,
            notes,
            created_at
        FROM `{DATASET_ID}.job_section_annotations`
        WHERE annotation_id = @annotation_id
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("annotation_id", "STRING", annotation_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        for row in results:
            return SectionAnnotation(
                annotation_id=row.annotation_id,
                job_posting_id=row.job_posting_id,
                section_text=row.section_text,
                section_start_index=row.section_start_index,
                section_end_index=row.section_end_index,
                label=AnnotationLabel(row.label),
                contains_skills=row.contains_skills,
                annotator_id=row.annotator_id,
                notes=row.notes,
                created_at=row.created_at
            )
        
        return None
    
    async def list_annotations(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[SectionAnnotation]:
        """List all annotations with pagination."""
        query = f"""
        SELECT
            annotation_id,
            job_posting_id,
            section_text,
            section_start_index,
            section_end_index,
            label,
            contains_skills,
            annotator_id,
            notes,
            created_at
        FROM `{DATASET_ID}.job_section_annotations`
        ORDER BY created_at DESC
        LIMIT {limit}
        OFFSET {offset}
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        annotations = []
        for row in results:
            annotations.append(
                SectionAnnotation(
                    annotation_id=row.annotation_id,
                    job_posting_id=row.job_posting_id,
                    section_text=row.section_text,
                    section_start_index=row.section_start_index,
                    section_end_index=row.section_end_index,
                    label=AnnotationLabel(row.label),
                    contains_skills=row.contains_skills,
                    annotator_id=row.annotator_id,
                    notes=row.notes,
                    created_at=row.created_at
                )
            )
        
        return annotations
    
    async def get_annotations_for_job(self, job_id: str) -> List[SectionAnnotation]:
        """Get all annotations for a specific job."""
        query = f"""
        SELECT
            annotation_id,
            job_posting_id,
            section_text,
            section_start_index,
            section_end_index,
            label,
            contains_skills,
            annotator_id,
            notes,
            created_at
        FROM `{DATASET_ID}.job_section_annotations`
        WHERE job_posting_id = @job_id
        ORDER BY created_at DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("job_id", "STRING", job_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        annotations = []
        for row in results:
            annotations.append(
                SectionAnnotation(
                    annotation_id=row.annotation_id,
                    job_posting_id=row.job_posting_id,
                    section_text=row.section_text,
                    section_start_index=row.section_start_index,
                    section_end_index=row.section_end_index,
                    label=AnnotationLabel(row.label),
                    contains_skills=row.contains_skills,
                    annotator_id=row.annotator_id,
                    notes=row.notes,
                    created_at=row.created_at
                )
            )
        
        return annotations
    
    async def delete_annotation(self, annotation_id: str) -> bool:
        """Delete an annotation."""
        query = f"""
        DELETE FROM `{DATASET_ID}.job_section_annotations`
        WHERE annotation_id = @annotation_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("annotation_id", "STRING", annotation_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()
        
        return True  # BigQuery doesn't return affected rows easily
    
    async def export_training_data(self) -> List[Dict[str, Any]]:
        """Export all annotations as training data format."""
        query = f"""
        SELECT
            job_posting_id as job_id,
            section_text as text,
            label,
            contains_skills as should_extract_skills,
            section_start_index as start_index,
            section_end_index as end_index,
            annotator_id,
            notes,
            created_at
        FROM `{DATASET_ID}.job_section_annotations`
        ORDER BY created_at DESC
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        training_data = []
        for row in results:
            training_data.append({
                'job_id': row.job_id,
                'text': row.text,
                'label': row.label,
                'should_extract_skills': row.should_extract_skills,
                'start_index': row.start_index,
                'end_index': row.end_index,
                'annotator_id': row.annotator_id,
                'notes': row.notes,
                'created_at': row.created_at.isoformat() if row.created_at else None
            })
        
        return training_data
