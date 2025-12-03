# Data Model: ML Quality & Lifecycle Improvements

**Feature**: 001-ml-quality-lifecycle  
**Phase**: 1 - Design  
**Date**: 2025-12-03

## Overview

This document defines the data entities, relationships, and validation rules for the ML Quality & Lifecycle Improvements feature.

---

## Entity Definitions

### 1. ModelConfig

**Purpose**: Centralized configuration for all ML models in the enrichment pipeline.

```python
@dataclass
class ModelConfig:
    """Configuration for an ML model with version tracking."""
    
    # Required fields
    model_id: str              # e.g., "skills_extractor"
    version: str               # e.g., "v4.0-unified-config-enhanced"
    model_type: str            # "skills_extraction" | "embeddings" | "clustering" | "section_classification"
    
    # Metadata
    created_at: datetime       # When config was created
    updated_at: datetime       # Last modification time
    
    # Optional training info
    training_data_version: Optional[str] = None   # Version of training data used
    training_date: Optional[datetime] = None      # When model was trained
    
    # Performance tracking
    performance_metrics: Optional[Dict[str, float]] = None  # Latest eval metrics
    
    # Runtime config
    config_overrides: Optional[Dict[str, Any]] = None       # YAML override values
    is_active: bool = True                                  # Whether this version is active
```

**Validation Rules**:
- `model_id` must match pattern: `^[a-z_]+$` (lowercase with underscores)
- `version` must match pattern: `^v\d+\.\d+(-[a-z0-9-]+)?$`
- `model_type` must be one of allowed enrichment types
- `created_at` must be <= `updated_at`

**Relationships**:
- Referenced by `JobEnrichment.enrichment_version`
- Referenced by `EvaluationResult.model_id`

---

### 2. SkillAlias

**Purpose**: Maps skill aliases to canonical skill names for normalization.

```python
@dataclass
class SkillAlias:
    """Mapping from skill alias to canonical name."""
    
    # Required fields
    alias_id: str              # UUID
    alias_text: str            # e.g., "K8s", "GCP", "JS"
    canonical_name: str        # e.g., "Kubernetes", "Google Cloud Platform"
    
    # Classification
    skill_category: str        # Category of the canonical skill
    
    # Metadata
    source: str                # "manual" | "user_feedback" | "auto_detected"
    confidence: float          # 0.0-1.0, how confident we are in this mapping
    created_at: datetime
    created_by: Optional[str]  # User who added (if manual)
    
    # Status
    is_active: bool = True     # Can be deactivated without deletion
```

**Validation Rules**:
- `alias_text` must be non-empty, max 50 characters
- `canonical_name` must be non-empty, max 100 characters
- `skill_category` must be valid category from lexicon
- `confidence` must be between 0.0 and 1.0
- `alias_text` must be unique (case-insensitive)

**BigQuery Schema**:
```sql
CREATE TABLE IF NOT EXISTS `brightdata_jobs.skill_aliases` (
    alias_id STRING NOT NULL,
    alias_text STRING NOT NULL,
    canonical_name STRING NOT NULL,
    skill_category STRING NOT NULL,
    source STRING,
    confidence FLOAT64,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    created_by STRING,
    is_active BOOL DEFAULT TRUE
);
```

---

### 3. ExtractedSkill (Extended)

**Purpose**: Represents a skill extracted from a job posting with enhanced metadata.

```python
@dataclass
class ExtractedSkill:
    """Skill identified from a job posting with extraction details."""
    
    # Identifiers
    skill_id: str              # UUID
    job_posting_id: str        # Reference to job_postings
    enrichment_id: str         # Reference to job_enrichments
    
    # Skill information
    skill_name: str            # Canonical skill name
    skill_category: str        # Category (programming_languages, etc.)
    
    # Confidence and provenance
    confidence_score: float    # Final computed confidence (0.0-1.0)
    source_strategies: List[str]  # Which strategies found this skill
    
    # Section relevance (Phase 2)
    section_relevance_score: Optional[float] = None  # 0.0-1.0
    extracted_from_section: Optional[str] = None     # Section name if identified
    
    # Context
    context_snippet: Optional[str] = None  # Surrounding text
    position_in_text: Optional[int] = None # Character offset
    
    # Timestamps
    created_at: datetime
```

**Validation Rules**:
- `confidence_score` must be between 0.0 and 1.0
- `source_strategies` must contain at least one valid strategy name
- `skill_name` must be non-empty
- If `section_relevance_score` provided, must be between 0.0 and 1.0

**BigQuery Schema Extension**:
```sql
ALTER TABLE `brightdata_jobs.job_skills`
ADD COLUMN IF NOT EXISTS source_strategies ARRAY<STRING>,
ADD COLUMN IF NOT EXISTS section_relevance_score FLOAT64,
ADD COLUMN IF NOT EXISTS extracted_from_section STRING,
ADD COLUMN IF NOT EXISTS position_in_text INT64,
ADD COLUMN IF NOT EXISTS enrichment_version STRING;
```

---

### 4. SectionClassification

**Purpose**: Classification result for a section of a job posting.

```python
@dataclass
class SectionClassification:
    """Classification of a job posting section for skills relevance."""
    
    # Identifiers
    classification_id: str     # UUID
    job_posting_id: str        # Reference to job_postings
    
    # Section details
    section_text: str          # The section content
    section_header: Optional[str]  # Header if identifiable
    section_index: int         # Order in document
    
    # Classification result
    is_skills_relevant: bool   # Binary classification
    relevance_probability: float  # Confidence (0.0-1.0)
    
    # Model info
    classifier_version: str    # Version of classifier used
    classification_method: str # "rule_based" | "ml_model"
    
    # Timestamps
    created_at: datetime
```

**Validation Rules**:
- `section_text` must be non-empty
- `relevance_probability` must be between 0.0 and 1.0
- `section_index` must be >= 0
- `classification_method` must be valid method name

**BigQuery Schema**:
```sql
CREATE TABLE IF NOT EXISTS `brightdata_jobs.section_classifications` (
    classification_id STRING NOT NULL,
    job_posting_id STRING NOT NULL,
    section_text STRING NOT NULL,
    section_header STRING,
    section_index INT64 NOT NULL,
    is_skills_relevant BOOL NOT NULL,
    relevance_probability FLOAT64 NOT NULL,
    classifier_version STRING NOT NULL,
    classification_method STRING NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

---

### 5. ClusterAssignment (Extended)

**Purpose**: Job cluster assignment with version tracking for stability analysis.

```python
@dataclass
class ClusterAssignment:
    """Assignment of a job to a cluster with version tracking."""
    
    # Identifiers
    cluster_assignment_id: str  # UUID
    job_posting_id: str         # Reference to job_postings
    enrichment_id: str          # Reference to job_enrichments
    
    # Cluster info
    cluster_id: int             # Cluster number within run
    cluster_name: str           # Human-readable name
    cluster_keywords: List[Dict[str, Any]]  # Top keywords with scores
    cluster_size: int           # Total jobs in this cluster
    
    # Version tracking (NEW)
    cluster_run_id: str         # UUID for this clustering execution
    cluster_model_id: str       # Model version used
    cluster_version: int        # Incrementing version per job
    is_active: bool             # Whether this is the current assignment
    
    # Timestamps
    created_at: datetime
```

**Validation Rules**:
- `cluster_id` must be >= 0
- `cluster_version` must be >= 1
- `cluster_keywords` must be valid JSON array
- Only one assignment per job should have `is_active = True`

**BigQuery Schema Extension**:
```sql
ALTER TABLE `brightdata_jobs.job_clusters`
ADD COLUMN IF NOT EXISTS cluster_run_id STRING,
ADD COLUMN IF NOT EXISTS cluster_model_id STRING,
ADD COLUMN IF NOT EXISTS cluster_version INT64 DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_active BOOL DEFAULT TRUE;
```

---

### 6. EvaluationResult

**Purpose**: Stores results from ML model evaluation runs.

```python
@dataclass
class EvaluationResult:
    """Results from evaluating an ML model against labeled data."""
    
    # Identifiers
    evaluation_id: str         # UUID
    model_id: str              # Which model was evaluated
    model_version: str         # Specific version evaluated
    
    # Dataset info
    dataset_version: str       # Version of evaluation dataset
    dataset_path: str          # GCS path to dataset
    sample_count: int          # Number of samples evaluated
    
    # Overall metrics
    overall_precision: float   # Macro precision
    overall_recall: float      # Macro recall
    overall_f1: float          # Macro F1 score
    
    # Per-category breakdown
    category_metrics: Dict[str, Dict[str, float]]
    # Example: {"programming_languages": {"precision": 0.85, "recall": 0.90, "f1": 0.87, "support": 50}}
    
    # Execution info
    evaluation_date: datetime
    execution_time_seconds: float
    
    # CI/CD info
    is_ci_run: bool = False    # Whether this was a CI pipeline run
    ci_build_id: Optional[str] = None
    threshold_passed: Optional[bool] = None  # Did it meet threshold?
```

**Validation Rules**:
- All metric values must be between 0.0 and 1.0
- `sample_count` must be > 0
- `execution_time_seconds` must be >= 0
- `category_metrics` must have valid category names

**BigQuery Schema**:
```sql
CREATE TABLE IF NOT EXISTS `brightdata_jobs.evaluation_results` (
    evaluation_id STRING NOT NULL,
    model_id STRING NOT NULL,
    model_version STRING NOT NULL,
    dataset_version STRING NOT NULL,
    dataset_path STRING,
    sample_count INT64 NOT NULL,
    overall_precision FLOAT64 NOT NULL,
    overall_recall FLOAT64 NOT NULL,
    overall_f1 FLOAT64 NOT NULL,
    category_metrics JSON,
    evaluation_date TIMESTAMP NOT NULL,
    execution_time_seconds FLOAT64,
    is_ci_run BOOL DEFAULT FALSE,
    ci_build_id STRING,
    threshold_passed BOOL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

---

### 7. JobEnrichment (Extended)

**Purpose**: Extended enrichment tracking with version fields.

```python
@dataclass
class JobEnrichment:
    """Tracks enrichment status with version information."""
    
    # Existing fields
    enrichment_id: str         # UUID
    job_posting_id: str        # Reference to job_postings
    enrichment_type: str       # skills_extraction | embeddings | clustering | section_classification
    status: str                # pending | processing | success | failed
    
    # NEW: Version tracking
    model_id: str              # Model identifier
    model_version: str         # Full version string
    enrichment_version: str    # Denormalized for query performance
    
    # Existing fields
    metadata: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
```

**BigQuery Schema Extension**:
```sql
ALTER TABLE `brightdata_jobs.job_enrichments`
ADD COLUMN IF NOT EXISTS model_id STRING,
ADD COLUMN IF NOT EXISTS model_version STRING,
ADD COLUMN IF NOT EXISTS enrichment_version STRING;

-- Migration for existing records
UPDATE `brightdata_jobs.job_enrichments`
SET enrichment_version = 'legacy'
WHERE enrichment_version IS NULL;
```

---

## Entity Relationships

```
┌─────────────────┐      ┌──────────────────┐
│  job_postings   │──────│  job_enrichments │
└─────────────────┘      └──────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐      ┌──────────────────┐
│   job_skills    │      │   job_clusters   │
│  (ExtractedSkill)│      │(ClusterAssignment)
└─────────────────┘      └──────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐      ┌──────────────────┐
│  skill_aliases  │      │evaluation_results│
└─────────────────┘      └──────────────────┘
                               │
                               │
                               ▼
                       ┌──────────────────┐
                       │   model_config   │
                       │    (runtime)     │
                       └──────────────────┘
```

---

## State Transitions

### Enrichment Status
```
pending → processing → success
                   └─→ failed → pending (retry)
```

### Cluster Version
```
New clustering run:
  1. Create new cluster_run_id
  2. Set new assignments with cluster_version = max(existing) + 1
  3. Set is_active = TRUE for new, FALSE for old
```

### Evaluation Flow
```
1. Load model version
2. Run evaluation on test set
3. Store results with model_version
4. Compare to threshold
5. Update model_config.performance_metrics
```

---

## Indexes and Query Optimization

### Recommended Indexes

```sql
-- job_enrichments: Query by version
CREATE INDEX IF NOT EXISTS idx_enrichments_version 
ON `brightdata_jobs.job_enrichments` (enrichment_version, enrichment_type);

-- job_skills: Query by job and confidence
CREATE INDEX IF NOT EXISTS idx_skills_job_confidence
ON `brightdata_jobs.job_skills` (job_posting_id, confidence_score DESC);

-- job_clusters: Query active clusters
CREATE INDEX IF NOT EXISTS idx_clusters_active
ON `brightdata_jobs.job_clusters` (is_active, cluster_run_id);

-- evaluation_results: Query by model and date
CREATE INDEX IF NOT EXISTS idx_eval_model_date
ON `brightdata_jobs.evaluation_results` (model_id, evaluation_date DESC);
```

### Common Query Patterns

```sql
-- Find jobs needing re-enrichment (new model version)
SELECT job_posting_id
FROM `brightdata_jobs.job_postings` jp
LEFT JOIN `brightdata_jobs.job_enrichments` je
  ON jp.job_posting_id = je.job_posting_id
  AND je.enrichment_type = 'skills_extraction'
  AND je.enrichment_version = @current_version
WHERE je.enrichment_id IS NULL;

-- Get latest evaluation for a model
SELECT *
FROM `brightdata_jobs.evaluation_results`
WHERE model_id = @model_id
ORDER BY evaluation_date DESC
LIMIT 1;

-- Get cluster stability (jobs that changed clusters)
SELECT 
  old.job_posting_id,
  old.cluster_name AS old_cluster,
  new.cluster_name AS new_cluster
FROM `brightdata_jobs.job_clusters` old
JOIN `brightdata_jobs.job_clusters` new
  ON old.job_posting_id = new.job_posting_id
WHERE old.cluster_run_id = @old_run_id
  AND new.cluster_run_id = @new_run_id
  AND old.cluster_id != new.cluster_id;
```

---

## Data Validation Rules Summary

| Entity | Field | Rule |
|--------|-------|------|
| ModelConfig | version | `^v\d+\.\d+(-[a-z0-9-]+)?$` |
| SkillAlias | alias_text | Unique, max 50 chars |
| ExtractedSkill | confidence_score | 0.0 - 1.0 |
| SectionClassification | relevance_probability | 0.0 - 1.0 |
| ClusterAssignment | is_active | Only one TRUE per job |
| EvaluationResult | overall_f1 | 0.0 - 1.0 |
| JobEnrichment | enrichment_version | Non-null after migration |
