<!--
Sync Impact Report - Constitution Amendment
Version: 1.0.0 → 2.0.0 (MAJOR)
Date: 2025-11-30
Rationale: Initial constitution creation based on comprehensive project audit

Modified Principles:
- All principles: Newly defined based on existing patterns

Added Sections:
- Core Principles (7 principles)
- Technology Stack Standards
- Development Workflow
- Governance

Removed Sections:
- None (new constitution)

Templates Requiring Updates:
✅ plan-template.md - Updated constitution check references
✅ spec-template.md - Aligned with architecture principles
✅ tasks-template.md - Aligned with testing and deployment principles

Follow-up TODOs:
- None
-->

# CapacityReset Constitution

## Core Principles

### I. Hexagonal Architecture (Ports & Adapters)

**Domain Layer First**: All business logic resides in domain entities and repositories (ports). Domain MUST NOT depend on infrastructure.

**Adapter Pattern**: External dependencies (BigQuery, Vertex AI, GCS) are accessed through adapters implementing domain repository interfaces.

**Use Case Orchestration**: Application layer (use_cases.py) orchestrates domain logic and coordinates between repositories. No business rules in use cases - only workflow orchestration.

**Independence**: Domain can be tested without infrastructure. Swap adapters for testing or different storage backends.

**Rationale**: Enables testability, maintainability, and evolution of infrastructure without affecting business logic. Proven pattern for cloud-native microservices.

### II. Monorepo Service Separation

**Service Isolation**: Each microservice lives in `services/`, `api/`, or `apps/` with self-contained dependencies, Dockerfiles, and Cloud Build configurations.

**Independent Deployment**: Services deploy independently via Cloud Build triggers. No shared deployment pipeline.

**Clear Boundaries**:
- `services/linkedin-scraper`: BrightData API orchestration
- `services/brightdata-etl`: GCS to BigQuery transformation
- `services/ml-enrichment`: ML-powered job enrichment (skills, embeddings, clustering)
- `api/jobs-api`: REST API implementing hexagonal architecture
- `apps/jobs-web`: Next.js frontend

**Shared Assets**: SQL schemas (`sql/`), documentation, and project-wide configuration at repository root.

**Rationale**: Maintains service autonomy while avoiding multi-repo complexity for a small team. Enables parallel development and independent scaling.

### III. Cloud-Native, Serverless First

**Serverless Deployment**: Services run on Cloud Run or Cloud Functions. No VM management.

**Managed Services**: Prefer managed GCP services: BigQuery (data warehouse), GCS (object storage), Vertex AI (ML), Cloud Logging, Cloud Scheduler.

**Event-Driven Orchestration**: Cloud Scheduler triggers services via HTTP. Services coordinate through BigQuery state tables (e.g., `scraper_execution_logs`, `job_enrichments`).

**Stateless Services**: No persistent local state. All state in BigQuery or GCS.

**Rationale**: Reduces operational overhead, enables auto-scaling, and aligns with GCP best practices for cost efficiency.

### IV. Polymorphic Enrichment Tracking

**Unified Enrichment Table**: `job_enrichments` tracks all enrichment types (skills_extraction, embeddings, clustering) with polymorphic design (enrichment_type, enrichment_version, status, metadata).

**Loose Coupling**: `job_postings` table remains independent. Enrichments reference jobs via foreign key but can be added/removed without schema changes.

**Versioning**: Every enrichment records `enrichment_version` enabling model iteration and reprocessing with new versions.

**Idempotency**: Services check enrichment status before processing. Already-enriched jobs are skipped unless version changes.

**Rationale**: Allows ML model evolution without breaking existing data. Supports experimental enrichment types and A/B testing of models.

### V. Lazy-Loading ML Models

**On-Demand Loading**: ML models (spaCy NLP, Vertex AI embeddings) loaded lazily on first use, not at import time.

**Cold Start Optimization**: Reduces Cloud Run cold start from 3-5s to ~500ms by deferring model loading until needed.

**Memory Efficiency**: Services only load required models based on requested enrichment types.

**Implementation**: Global singletons with `get_*()` functions check `if _model is None` before loading.

**Rationale**: Critical for serverless environments with cold starts. Improves user experience and reduces costs.

### VI. Human-in-the-Loop ML Reinforcement

**User Feedback Loop**: Users can approve/reject ML-extracted skills. Approved skills reinforce `skills_lexicon` table for future extractions.

**Manual Skill Addition**: Users can add skills not detected by ML. These feed back to lexicon with `added_by_user=True` flag.

**Section Annotations**: Users annotate job description sections (responsibilities, qualifications, etc.) to train future section classifiers.

**Confidence Scoring**: ML extractions include confidence scores. User feedback improves model calibration over time.

**Rationale**: Enables continuous model improvement without expensive retraining pipelines. Users naturally improve system as they use it.

### VII. Infrastructure as Code & GitOps

**Cloud Build Triggers**: Each service has `cloudbuild.yaml` defining build, test, and deploy steps. Triggers on git push to main.

**BigQuery Schema Management**: SQL schema definitions in `sql/` directory. Scripts in `services/*/scripts/` for table creation and migrations.

**Environment Configuration**: GCP project and environment variables defined in service code and Cloud Build substitutions. No manual console configuration.

**Idempotent Migrations**: Scripts check for table existence before creation. MERGE statements for upserts.

**Rationale**: Ensures reproducibility, auditability, and disaster recovery. All infrastructure changes tracked in git.

## Technology Stack Standards

**Languages**:
- Backend Services: Python 3.11
- Frontend: TypeScript 5.x + Next.js 14

**Frameworks**:
- API: FastAPI (hexagonal architecture)
- Frontend: Next.js (App Router), React, Tailwind CSS
- ML: spaCy 3.x, scikit-learn, Vertex AI SDK

**Data & Storage**:
- Data Warehouse: Google BigQuery
- Object Storage: Google Cloud Storage
- State Tracking: BigQuery tables (not Firestore/Cloud SQL)

**Deployment**:
- Container Registry: Artifact Registry
- Compute: Cloud Run (backend), Cloud Functions (event handlers)
- CI/CD: Cloud Build with service-specific triggers
- Scheduling: Cloud Scheduler

**Observability**:
- Logging: Cloud Logging (structured JSON)
- Errors: Logged with context to BigQuery or Cloud Logging
- Execution Tracking: Dedicated BigQuery tables (e.g., `etl_execution_logs`, `scraper_execution_logs`)

## Development Workflow

**Feature Development**:
1. Create feature branch from main
2. Implement following hexagonal architecture (domain → application → adapters)
3. Test locally with `uvicorn` (APIs) or `npm run dev` (frontend)
4. Commit and push to trigger Cloud Build preview deploy
5. Merge to main triggers production deploy

**Database Changes**:
1. Write SQL schema in `sql/` or `services/*/scripts/`
2. Create idempotent migration script
3. Run script manually via `python scripts/script_name.py`
4. Document schema changes in service README

**ML Model Updates**:
1. Increment `enrichment_version` in code
2. Deploy new version via Cloud Build
3. Existing enrichments preserved (version-tagged)
4. Reprocess subset of jobs to validate new model

**Testing Strategy**:
- **Contract Tests**: Validate repository interfaces (domain/repositories.py)
- **Integration Tests**: Test use cases with in-memory or test BigQuery datasets
- **Manual Testing**: Use Cloud Run URLs with sample requests before production
- **No Unit Tests Required**: Architecture itself provides testability through ports/adapters

**Code Review**:
- Architecture compliance: Does it follow hexagonal architecture?
- Service isolation: No cross-service imports except through APIs
- Idempotency: Can operations safely retry?
- Observability: Are errors logged with context?

## Governance

**Constitution Authority**: This document supersedes all prior practices and ad-hoc decisions. All architecture decisions MUST align with these principles.

**Amendment Process**:
1. Propose amendment with rationale in GitHub issue or PR
2. Discuss impact on existing services
3. Update constitution version following semantic versioning:
   - **MAJOR**: Backward incompatible governance/principle removals or redefinitions
   - **MINOR**: New principle/section added or materially expanded guidance
   - **PATCH**: Clarifications, wording, typo fixes, non-semantic refinements
4. Update affected templates and documentation
5. Communicate changes to team
6. Merge to main

**Compliance Verification**:
- All PRs MUST include architecture justification if introducing new patterns
- Code reviews MUST verify principle adherence
- Complexity justifications required for deviations (see plan-template.md)

**Versioning Policy**:
- Track all service versions in cloudbuild.yaml or package.json
- ML enrichment versions tracked in `job_enrichments.enrichment_version`
- Breaking API changes require new endpoint version (e.g., `/v2/jobs`)

**Review Cadence**: Constitution reviewed quarterly or when major architectural decisions arise.

**Version**: 2.0.0 | **Ratified**: 2025-11-30 | **Last Amended**: 2025-11-30
