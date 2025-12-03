# Feature Specification: ML Quality & Lifecycle Improvements

**Feature Branch**: `001-ml-quality-lifecycle`  
**Created**: 2025-12-03  
**Status**: Draft  
**Input**: Comprehensive spec for ML Quality & Lifecycle improvements including model versioning, skills extraction enhancements, clustering stability, and metrics evaluation

## User Scenarios & Testing *(mandatory)*

### User Story 1 - ML Model Version Management (Priority: P1)

As a data scientist or ML engineer, I need to track which version of the ML model was used to process each job posting, so that I can understand the provenance of enrichment data, re-process jobs when models are updated, and roll back to previous versions if quality degrades.

**Why this priority**: Without version tracking, there's no way to know which jobs need re-enrichment when models improve, no ability to debug quality issues, and no way to compare model performance over time. This is foundational for all other ML lifecycle improvements.

**Independent Test**: Can be fully tested by deploying a new model version and verifying that (1) new enrichments are tagged with the new version, (2) the system can identify jobs processed by older versions, and (3) the correct version identifier is visible in all enrichment records.

**Acceptance Scenarios**:

1. **Given** a job posting is enriched, **When** the enrichment is stored, **Then** the enrichment record includes a model identifier (e.g., "skills_extractor_v1.2")
2. **Given** a new model version is deployed, **When** querying for jobs needing re-enrichment, **Then** the system returns jobs processed by older model versions
3. **Given** multiple model versions exist in the system, **When** viewing an enrichment record, **Then** the exact model version used is clearly displayed

---

### User Story 2 - Enhanced Skills Extraction Accuracy (Priority: P1)

As a job seeker or recruiter using the platform, I need the skills extraction to be more accurate and comprehensive, so that job-skill matching is reliable and I don't miss relevant opportunities or candidates due to extraction errors.

**Why this priority**: Skills extraction quality directly impacts the core value proposition of the platform. Poor extraction leads to poor matching, which affects user trust and engagement.

**Independent Test**: Can be fully tested by running extraction on a curated test set of job postings and measuring precision/recall metrics against ground truth labels.

**Acceptance Scenarios**:

1. **Given** a job posting contains skill aliases (e.g., "K8s", "GCP"), **When** skills are extracted, **Then** the canonical skill names are identified (e.g., "Kubernetes", "Google Cloud Platform")
2. **Given** a job posting has multiple sections, **When** skills are extracted, **Then** skills from relevant sections (requirements, qualifications) are weighted higher than skills from company description sections
3. **Given** skills are extracted, **When** viewing the results, **Then** each skill includes a confidence score and the extraction strategies that contributed to its identification

---

### User Story 3 - Stable Job Clustering Over Time (Priority: P2)

As a product manager or data analyst, I need job clustering to be stable and versioned over time, so that I can track trends, compare cluster assignments across different time periods, and ensure consistent job categorization.

**Why this priority**: Clustering stability is important for analytics and trend reporting, but has less immediate user impact than skills extraction accuracy.

**Independent Test**: Can be fully tested by running clustering on a fixed dataset, then running it again on the same dataset plus new jobs, and verifying that existing job cluster assignments can be tracked and compared.

**Acceptance Scenarios**:

1. **Given** a clustering job runs, **When** clusters are stored, **Then** each cluster assignment includes a cluster run identifier and model version
2. **Given** multiple clustering runs have occurred, **When** querying job clusters, **Then** the system can filter to show only the latest/active cluster version
3. **Given** a new clustering run completes, **When** comparing to previous runs, **Then** the system provides metrics on cluster stability (e.g., how many jobs changed clusters)

---

### User Story 4 - ML Performance Monitoring and Evaluation (Priority: P2)

As a data scientist or ML engineer, I need to evaluate ML model performance against labeled test data and track metrics over time, so that I can detect regressions, measure improvements, and make data-driven decisions about model updates.

**Why this priority**: Without evaluation capabilities, there's no objective way to know if models are improving or degrading. This enables continuous improvement of the ML system.

**Independent Test**: Can be fully tested by providing a labeled evaluation dataset and verifying that the system produces accuracy, precision, recall, and F1 metrics per skill category.

**Acceptance Scenarios**:

1. **Given** a labeled evaluation dataset exists, **When** running model evaluation, **Then** the system reports precision, recall, and F1 scores for skills extraction
2. **Given** evaluation runs over time, **When** comparing results, **Then** the system shows metric trends across model versions
3. **Given** a new model version is proposed, **When** evaluation runs in CI/CD, **Then** the pipeline can gate deployment based on metric thresholds

---

### User Story 5 - Section-Aware Skills Extraction (Priority: P3)

As a job seeker, I need skills extraction to focus on the most relevant sections of job postings, so that I see accurate skills rather than noise from company descriptions or benefits sections.

**Why this priority**: Section-aware extraction improves precision but requires training data from the annotation tool. It's an enhancement on top of the core extraction improvements.

**Independent Test**: Can be fully tested by comparing extraction results on jobs with clear section headers before and after section classification is enabled.

**Acceptance Scenarios**:

1. **Given** a job posting has identifiable sections, **When** skills extraction runs, **Then** each section is classified as skills-relevant or not
2. **Given** section classification is enabled, **When** skills from irrelevant sections appear, **Then** they have lower confidence scores or are filtered out
3. **Given** a section classifier model exists, **When** new annotations are collected, **Then** the classifier can be retrained with improved accuracy

---

### Edge Cases

- What happens when a job posting has no identifiable sections or headers?
  - The system extracts skills from the full text with standard confidence weighting
- How does the system handle when a model version file is missing or corrupted?
  - The system falls back to the last known good version and logs a warning
- What happens when clustering runs on a dataset with very few jobs?
  - The system uses a minimum cluster size threshold and may produce fewer clusters than requested
- How does the system handle skill aliases that map to multiple canonical skills?
  - The system uses context and confidence scoring to select the most likely canonical skill
- What happens when evaluation data has insufficient labels for certain categories?
  - The system reports metrics only for categories with sufficient samples and flags gaps

## Requirements *(mandatory)*

### Functional Requirements

**Phase 0 - Foundations**

- **FR-001**: System MUST use a standardized model identifier format for all ML models (e.g., `skills_extractor_v{major}.{minor}`)
- **FR-002**: System MUST store model configuration in a centralized location that can be read by all enrichment services
- **FR-003**: System MUST include `enrichment_version` in all enrichment records that matches the model identifier

**Phase 1 - Skills Extraction Improvements**

- **FR-004**: System MUST support multiple extraction strategies (rule-based, alias/synonym, and optionally embedding-based) that run in sequence
- **FR-005**: System MUST merge results from multiple extraction strategies, deduplicating by canonical skill name
- **FR-006**: System MUST maintain a configurable mapping of skill aliases to canonical names (e.g., "K8s" → "Kubernetes")
- **FR-007**: System MUST compute per-skill confidence scores based on extraction strategy, frequency, and section presence
- **FR-008**: System MUST record which extraction strategies contributed to each skill identification

**Phase 2 - Section Classification**

- **FR-009**: System MUST support a section classifier that identifies skills-relevant sections of job postings
- **FR-010**: System MUST integrate section classification with skills extraction to weight or filter skills by section relevance
- **FR-011**: System MUST support training the section classifier from annotated data exported via the annotation tool API

**Phase 3 - Clustering Lifecycle**

- **FR-012**: System MUST include `cluster_run_id` and `cluster_model_id` in all cluster assignment records
- **FR-013**: System MUST support a `cluster_version` field to identify the active/current cluster assignments
- **FR-014**: System MUST support running clustering as a periodic batch job over a configurable time window of jobs

**Phase 4 - Metrics and Evaluation**

- **FR-015**: System MUST provide evaluation functionality that computes precision, recall, and F1 for skills extraction against labeled test data
- **FR-016**: System MUST produce evaluation results in a consistent format that can be stored and compared over time
- **FR-017**: System MUST support running a quick evaluation check that can be integrated into CI/CD pipelines

**Architecture Alignment**:
- Feature involves ML models: All new extraction strategies (composite extractor, alias extractor) follow the existing `ExtractionStrategy` pattern and use lazy-loading (Principle V)
- Feature involves user feedback: Section classifier training uses data from annotation tool, completing the feedback loop from user annotations to model improvement (Principle VI)
- Feature fits in monorepo structure: All changes are within `services/ml-enrichment` with new config files and evaluation scripts (Principle II)

### Key Entities

- **ModelConfig**: Represents configuration for ML models
  - Key attributes: model_id, version, created_at, training_data_version, performance_metrics
  - Relationships: Referenced by enrichments and evaluation results

- **SkillAlias**: Represents a mapping from skill alias to canonical skill
  - Key attributes: alias_text, canonical_skill_name, skill_category
  - Relationships: Used by alias extraction strategy

- **ExtractedSkill**: Represents a skill identified from a job posting (extends existing job_skills)
  - Key attributes: skill_name, skill_category, confidence_score, source_strategies, section_relevance_score
  - Relationships: Belongs to job posting, references enrichment

- **SectionClassification**: Represents classification of a job posting section
  - Key attributes: section_text, is_skills_relevant, relevance_probability
  - Relationships: Belongs to job posting, used by section-aware extraction

- **ClusterAssignment**: Represents a job's cluster assignment (extends existing job_clusters)
  - Key attributes: cluster_id, cluster_run_id, cluster_model_id, cluster_version
  - Relationships: Belongs to job posting, belongs to cluster run

- **EvaluationResult**: Represents results from model evaluation
  - Key attributes: model_id, evaluation_date, metrics (precision, recall, F1), dataset_version, category_breakdown
  - Relationships: References model version, stored for historical comparison

## Assumptions

The following reasonable defaults and assumptions have been made:

1. **Storage**: Cloud storage (GCS buckets) is available for model artifacts and training data exports
2. **Evaluation Data Format**: Evaluation datasets follow JSONL format with job posting text and labeled skills/sections
3. **Confidence Thresholds**: Default confidence threshold for displaying skills is 0.5 (configurable)
4. **Clustering Window**: Default clustering window is 6 months of job postings (configurable)
5. **Active Cluster Version**: The most recent cluster_version is considered active by default
6. **Backward Compatibility**: Existing job enrichments without version information are treated as version "legacy"
7. **CI Evaluation Dataset**: A small held-out evaluation dataset (10-50 samples) is sufficient for CI gate checks

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All enrichment records include model version identifiers, enabling 100% of jobs to be filtered by enrichment version
- **SC-002**: Skills extraction F1 score improves by at least 10% compared to baseline (measured on held-out test set)
- **SC-003**: Alias resolution correctly maps 95% of common skill aliases to canonical names (tested against curated alias list)
- **SC-004**: Section classifier achieves at least 85% accuracy in identifying skills-relevant sections
- **SC-005**: Cluster assignments include version tracking, enabling historical comparison across 100% of clustering runs
- **SC-006**: Evaluation script produces metrics within 2 minutes for a test set of 100 samples
- **SC-007**: CI pipeline can run evaluation check within 5 minutes and gate deployment on performance thresholds
- **SC-008**: No regression in enrichment processing time (less than 10% increase per job)
