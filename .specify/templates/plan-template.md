# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

**Language/Version**: Python 3.11 (backend services), TypeScript 5.x (frontend)  
**Primary Dependencies**: FastAPI (API), Next.js (frontend), spaCy/Vertex AI (ML)  
**Storage**: Google BigQuery (data warehouse), Google Cloud Storage (object storage)  
**Testing**: Contract tests (repository interfaces), integration tests (use cases)  
**Target Platform**: Google Cloud Run (serverless containers), Cloud Functions (event handlers)  
**Project Type**: Monorepo with microservices (services/, api/, apps/)  
**Performance Goals**: <500ms API response time, <5s ML enrichment per job  
**Constraints**: Serverless (no VMs), managed services only, stateless services  
**Scale/Scope**: ~1000 jobs/day scraped, 100+ enrichments/day

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Required Checks**:

1. **Hexagonal Architecture (Principle I)**
   - [ ] Does feature separate domain, application, and adapter layers?
   - [ ] Are repository interfaces (ports) defined in domain/?
   - [ ] Do adapters implement domain interfaces without domain depending on infrastructure?

2. **Monorepo Service Separation (Principle II)**
   - [ ] Does feature belong in existing service or require new service?
   - [ ] If new service: Does it have independent cloudbuild.yaml and Dockerfile?
   - [ ] Are service boundaries clear (no cross-service imports)?

3. **Cloud-Native, Serverless First (Principle III)**
   - [ ] Does feature use Cloud Run/Functions (not VMs)?
   - [ ] Does it use managed services (BigQuery, GCS, Vertex AI)?
   - [ ] Is service stateless (all state in BigQuery/GCS)?

4. **Polymorphic Enrichment Tracking (Principle IV)** *(if ML feature)*
   - [ ] Does feature add new enrichment type to job_enrichments table?
   - [ ] Does it track enrichment_version for model iteration?
   - [ ] Is processing idempotent (checks existing enrichments)?

5. **Lazy-Loading ML Models (Principle V)** *(if ML feature)*
   - [ ] Are ML models loaded lazily (not at import time)?
   - [ ] Is loading wrapped in `get_*()` singleton pattern?

6. **Human-in-the-Loop ML Reinforcement (Principle VI)** *(if user-facing ML)*
   - [ ] Can users provide feedback on ML outputs?
   - [ ] Does feedback flow back to lexicon/training data?

7. **Infrastructure as Code & GitOps (Principle VII)**
   - [ ] Is infrastructure defined in code (cloudbuild.yaml, SQL scripts)?
   - [ ] Are migrations idempotent?
   - [ ] Are environment variables documented?

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# CapacityReset Monorepo Structure

services/                # Backend microservices (Cloud Run/Functions)
├── linkedin-scraper/    # BrightData API orchestration
├── brightdata-etl/      # GCS to BigQuery transformation
└── ml-enrichment/       # ML enrichment (skills, embeddings, clustering)

api/                     # REST APIs (Cloud Run)
└── jobs-api/           # FastAPI with hexagonal architecture
    ├── domain/         # Entities + repository ports
    ├── application/    # Use cases (orchestration)
    ├── adapters/       # Repository implementations (BigQuery)
    └── api/            # FastAPI routes

apps/                    # Frontend applications
└── jobs-web/           # Next.js web app

sql/                     # Shared BigQuery schemas
├── bigquery_job_postings_schema.sql
├── bigquery_transform_upsert.sql
└── brightdata_request_queries_schema.sql

# Each service/api/app contains:
├── cloudbuild.yaml     # Cloud Build configuration
├── Dockerfile          # Container definition
├── requirements.txt    # Python dependencies (or package.json)
├── main.py             # Service entry point
└── README.md           # Service documentation
```

**Structure Decision**: This project uses a monorepo with service isolation (Principle II). Each service deploys independently via Cloud Build triggers. Shared SQL schemas live in `sql/` at repository root.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
