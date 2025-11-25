"""
Dependency Injection - FastAPI dependencies

Provides repository and use case instances to route handlers.
"""

from functools import lru_cache

from adapters.bigquery_repository import (
    BigQueryJobRepository,
    BigQuerySkillRepository,
    BigQueryClusterRepository,
    BigQuerySkillLexiconRepository,
    BigQuerySectionAnnotationRepository
)
from application.use_cases import (
    ListJobsUseCase,
    GetJobDetailUseCase,
    UpdateSkillUseCase,
    AddSkillToJobUseCase,
    GenerateJobsReportUseCase,
    ReinforceLexiconUseCase,
    CreateAnnotationUseCase,
    GetAnnotationsByJobUseCase,
    ListAnnotationsUseCase,
    DeleteAnnotationUseCase,
    ExportTrainingDataUseCase
)
from domain.repositories import (
    JobRepository,
    SkillRepository,
    ClusterRepository,
    SkillLexiconRepository,
    SectionAnnotationRepository
)


# === Repository Singletons ===

@lru_cache()
def get_job_repo() -> JobRepository:
    """Get job repository singleton."""
    return BigQueryJobRepository()


@lru_cache()
def get_skill_repo() -> SkillRepository:
    """Get skill repository singleton."""
    return BigQuerySkillRepository()


@lru_cache()
def get_cluster_repo() -> ClusterRepository:
    """Get cluster repository singleton."""
    return BigQueryClusterRepository()


@lru_cache()
def get_lexicon_repo() -> SkillLexiconRepository:
    """Get lexicon repository singleton."""
    return BigQuerySkillLexiconRepository()


@lru_cache()
def get_annotation_repo() -> SectionAnnotationRepository:
    """Get annotation repository singleton."""
    return BigQuerySectionAnnotationRepository()


# === Use Case Factories ===

def get_list_jobs_uc() -> ListJobsUseCase:
    """Get ListJobsUseCase with dependencies."""
    return ListJobsUseCase(get_job_repo(), get_cluster_repo())


def get_job_detail_uc() -> GetJobDetailUseCase:
    """Get GetJobDetailUseCase with dependencies."""
    return GetJobDetailUseCase(get_job_repo(), get_skill_repo(), get_cluster_repo())


def get_update_skill_uc() -> UpdateSkillUseCase:
    """Get UpdateSkillUseCase with dependencies."""
    return UpdateSkillUseCase(get_skill_repo())


def get_add_skill_uc() -> AddSkillToJobUseCase:
    """Get AddSkillToJobUseCase with dependencies."""
    return AddSkillToJobUseCase(get_skill_repo(), get_lexicon_repo())


def get_generate_report_uc() -> GenerateJobsReportUseCase:
    """Get GenerateJobsReportUseCase with dependencies."""
    return GenerateJobsReportUseCase(get_job_repo())


def get_reinforce_lexicon_uc() -> ReinforceLexiconUseCase:
    """Get ReinforceLexiconUseCase with dependencies."""
    return ReinforceLexiconUseCase(get_lexicon_repo())


# === Annotation Use Case Factories ===

def get_create_annotation_uc() -> CreateAnnotationUseCase:
    """Get CreateAnnotationUseCase with dependencies."""
    return CreateAnnotationUseCase(get_annotation_repo(), get_job_repo())


def get_annotations_by_job_uc() -> GetAnnotationsByJobUseCase:
    """Get GetAnnotationsByJobUseCase with dependencies."""
    return GetAnnotationsByJobUseCase(get_annotation_repo())


def get_list_annotations_uc() -> ListAnnotationsUseCase:
    """Get ListAnnotationsUseCase with dependencies."""
    return ListAnnotationsUseCase(get_annotation_repo())


def get_delete_annotation_uc() -> DeleteAnnotationUseCase:
    """Get DeleteAnnotationUseCase with dependencies."""
    return DeleteAnnotationUseCase(get_annotation_repo())


def get_export_training_data_uc() -> ExportTrainingDataUseCase:
    """Get ExportTrainingDataUseCase with dependencies."""
    return ExportTrainingDataUseCase(get_annotation_repo())
