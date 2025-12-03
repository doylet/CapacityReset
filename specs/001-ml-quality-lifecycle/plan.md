# Implementation Plan: ML Quality & Lifecycle Improvements

**Branch**: `001-ml-quality-lifecycle` | **Date**: 2025-12-03 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-ml-quality-lifecycle/spec.md`

## Summary

This feature implements comprehensive ML model lifecycle improvements for the job enrichment system, including:

1. **Model Version Management** (P1) - Standardized model identifiers and enrichment version tracking
2. **Enhanced Skills Extraction** (P1) - Multi-strategy extraction with alias resolution and confidence scoring
3. **Stable Job Clustering** (P2) - Cluster version tracking with run identifiers
4. **ML Performance Monitoring** (P2) - Evaluation metrics (precision, recall, F1) with CI/CD integration
5. **Section-Aware Extraction** (P3) - Section classification for improved skill relevance

The implementation builds upon the existing `services/ml-enrichment` service, extending the `UnifiedSkillsExtractor` pattern and `job_enrichments` polymorphic tracking table.

## Technical Context

**Language/Version**: Python 3.11 (backend services)  
**Primary Dependencies**: 
- FastAPI (API layer) - existing
- spaCy 3.x (NLP/skills extraction) - existing
- scikit-learn (clustering, evaluation) - existing
- google-cloud-bigquery (data warehouse) - existing
- sentence-transformers (semantic extraction) - existing optional dependency

**Storage**: 
- Google BigQuery (`brightdata_jobs` dataset)
- Google Cloud Storage (model artifacts, evaluation datasets)

**Testing**: 
- Contract tests (repository interfaces)
- Integration tests (use cases)
- Evaluation scripts with labeled test data

**Target Platform**: Google Cloud Run (serverless containers)  
**Project Type**: Monorepo with microservices (`services/ml-enrichment`)  
**Performance Goals**: 
- <500ms API response time
- <5s ML enrichment per job
- <2 min evaluation for 100 samples

**Constraints**: 
- Serverless (no VMs)
- Managed services only
- Stateless services

**Scale/Scope**: ~1000 jobs/day scraped, 100+ enrichments/day

## Constitution Check

*GATE: All checks must pass before implementation. Re-check after Phase 1 design.*

### Required Checks

1. **Hexagonal Architecture (Principle I)**
   - [x] Does feature separate domain, application, and adapter layers?
     - Domain: `ModelConfig`, `SkillAlias`, `EvaluationResult` entities
     - Application: Enrichment orchestration use cases
     - Adapters: BigQuery storage implementations
   - [x] Are repository interfaces (ports) defined in domain/?
     - Extends existing `SkillsStorage` interface pattern
   - [x] Do adapters implement domain interfaces without domain depending on infrastructure?
     - BigQuery adapters implement storage interfaces

2. **Monorepo Service Separation (Principle II)**
   - [x] Does feature belong in existing service or require new service?
     - Extends existing `services/ml-enrichment` service
   - [x] No new service required - enhances existing ML enrichment capabilities
   - [x] Are service boundaries clear (no cross-service imports)?
     - All changes contained within `ml-enrichment`

3. **Cloud-Native, Serverless First (Principle III)**
   - [x] Does feature use Cloud Run/Functions (not VMs)?
     - Existing Cloud Run deployment
   - [x] Does it use managed services (BigQuery, GCS, Vertex AI)?
     - BigQuery for tracking, GCS for model artifacts
   - [x] Is service stateless (all state in BigQuery/GCS)?
     - Model configs and evaluation results stored in BigQuery

4. **Polymorphic Enrichment Tracking (Principle IV)** *(ML feature)*
   - [x] Does feature add new enrichment type to job_enrichments table?
     - New `model_evaluation` type for evaluation results
   - [x] Does it track enrichment_version for model iteration?
     - FR-003 requires `enrichment_version` in all records
   - [x] Is processing idempotent (checks existing enrichments)?
     - Existing pattern maintained

5. **Lazy-Loading ML Models (Principle V)** *(ML feature)*
   - [x] Are ML models loaded lazily (not at import time)?
     - Follows existing `get_skills_extractor()` pattern
   - [x] Is loading wrapped in `get_*()` singleton pattern?
     - New extractors follow established pattern

6. **Human-in-the-Loop ML Reinforcement (Principle VI)** *(user-facing ML)*
   - [x] Can users provide feedback on ML outputs?
     - FR-011: Section classifier training from annotation tool exports
   - [x] Does feedback flow back to lexicon/training data?
     - Annotation exports → section classifier retraining

7. **Infrastructure as Code & GitOps (Principle VII)**
   - [x] Is infrastructure defined in code (cloudbuild.yaml, SQL scripts)?
     - Schema changes in `sql/` directory
   - [x] Are migrations idempotent?
     - CREATE TABLE IF NOT EXISTS pattern
   - [x] Are environment variables documented?
     - In service README

8. **Code Clarity & Maintainability (Principle VIII)**
   - [x] No HEREDOCs in codebase
   - [x] SQL in separate `.sql` files or triple-quoted strings
   - [x] Configuration in Python dataclasses (UnifiedSkillsConfig pattern)

## Project Structure

### Documentation (this feature)

```text
specs/001-ml-quality-lifecycle/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Technical research findings
├── data-model.md        # Phase 1: Entity definitions and relationships
├── quickstart.md        # Phase 1: Developer setup guide
├── contracts/           # Phase 1: API contracts
│   ├── skills-extraction.yaml    # Skills extraction API
│   ├── model-config.yaml         # Model configuration API
│   └── evaluation.yaml           # Evaluation API
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code (repository root)

```text
services/ml-enrichment/
├── main.py                      # Service entry point (extend)
├── lib/
│   ├── enrichment/
│   │   ├── skills/
│   │   │   ├── unified_extractor.py    # Extend with alias extraction
│   │   │   ├── unified_config.py       # Extend with alias mappings
│   │   │   ├── alias_extractor.py      # NEW: Alias resolution strategy
│   │   │   └── section_classifier.py   # NEW: Section relevance classifier
│   │   ├── job_clusterer.py            # Extend with version tracking
│   │   └── embeddings_generator.py     # No changes needed
│   ├── config/
│   │   └── model_config.py             # NEW: Centralized model config
│   ├── evaluation/
│   │   ├── evaluator.py                # NEW: Skills evaluation
│   │   └── metrics.py                  # NEW: Metric calculations
│   └── utils/
│       └── enrichment_utils.py         # Extend with version queries
├── queries/
│   ├── clustering_queries.sql          # Add version filtering
│   └── evaluation_queries.sql          # NEW: Evaluation result queries
├── config/
│   ├── model_versions.yaml             # NEW: Model version registry
│   └── skill_aliases.yaml              # NEW: Alias mappings
├── scripts/
│   └── evaluate_ci.py                  # NEW: CI evaluation script
└── tests/
    ├── test_alias_extraction.py        # NEW: Alias tests
    └── test_evaluation.py              # NEW: Evaluation tests

sql/
├── bigquery_job_postings_schema.sql    # Existing
├── job_enrichments_v2_schema.sql       # NEW: Extended with version fields
├── evaluation_results_schema.sql       # NEW: Evaluation tracking
└── skill_aliases_schema.sql            # NEW: Alias lookup table
```

## Complexity Tracking

> **No violations requiring justification** - Feature aligns with all Constitution principles.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Implementation Phases

### Phase 0 - Foundations (FR-001 to FR-003)

**Deliverables**:
1. Model identifier format: `{model_type}_v{major}.{minor}[-{suffix}]`
   - Example: `skills_extractor_v4.0-unified-config-enhanced`
2. Centralized `model_config.py` with version registry
3. Extended `job_enrichments` table with `enrichment_version` field
4. Migration script for existing enrichments (legacy version tagging)

**Success Metrics**:
- SC-001: 100% of new enrichments include version identifiers

### Phase 1 - Skills Extraction Improvements (FR-004 to FR-008)

**Deliverables**:
1. `AliasExtractionStrategy` class implementing alias resolution
2. `skill_aliases.yaml` configuration with common mappings
3. Composite extractor running strategies in sequence
4. Extended skill output with `source_strategies` and `confidence_score`

**Success Metrics**:
- SC-002: 10% F1 improvement (measured via evaluation)
- SC-003: 95% alias resolution accuracy

### Phase 2 - Section Classification (FR-009 to FR-011)

**Deliverables**:
1. `SectionClassifier` class with relevance scoring
2. Integration with skills extraction pipeline
3. Training data export endpoint from annotation tool

**Success Metrics**:
- SC-004: 85% section classification accuracy

### Phase 3 - Clustering Lifecycle (FR-012 to FR-014)

**Deliverables**:
1. Extended `job_clusters` table with `cluster_run_id`, `cluster_model_id`, `cluster_version`
2. Stability metrics calculation between runs
3. Periodic batch job configuration

**Success Metrics**:
- SC-005: 100% of clusters have version tracking

### Phase 4 - Metrics and Evaluation (FR-015 to FR-017)

**Deliverables**:
1. `SkillsEvaluator` class with precision/recall/F1 calculation
2. `evaluation_results` BigQuery table
3. `evaluate_ci.py` script for CI/CD integration

**Success Metrics**:
- SC-006: <2 min evaluation for 100 samples
- SC-007: <5 min CI pipeline evaluation
- SC-008: <10% processing time increase

## Dependencies

### External Dependencies (existing)
- `spacy>=3.0.0` - NLP processing
- `scikit-learn>=1.0.0` - Clustering, evaluation metrics
- `google-cloud-bigquery>=3.0.0` - Data storage
- `sentence-transformers>=2.0.0` - Semantic extraction (optional)
- `pyyaml>=6.0` - Configuration files

### No New Dependencies Required
All functionality can be implemented with existing libraries.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Alias mapping incomplete | Medium | Medium | Start with curated list, enable user additions via lexicon |
| Section classifier accuracy below target | Medium | Low | Fall back to full-text extraction if <70% accuracy |
| Evaluation data insufficient | Low | Medium | Use synthetic data generation for initial testing |
| Cold start regression | Low | High | Monitor Cloud Run metrics, lazy-load new models |

## Next Steps

1. **Phase 0 Research** → Complete `research.md` with technical decisions
2. **Phase 1 Design** → Generate `data-model.md` with entity schemas
3. **Phase 1 Contracts** → Generate API contracts in `contracts/`
4. **Phase 1 Quickstart** → Create developer setup guide
