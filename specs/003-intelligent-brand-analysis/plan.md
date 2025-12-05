# Implementation Plan: Intelligent Brand Analysis with LLM Integration

**Branch**: `003-intelligent-brand-analysis` | **Date**: December 4, 2025 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-intelligent-brand-analysis/spec.md`

## Summary

Replace deterministic keyword-based brand analysis with Vertex AI Gemini integration to provide nuanced professional theme extraction, voice characteristic analysis, and contextual content generation. Maintains existing API surface while enhancing analysis depth and personalization.

## Technical Context

**Language/Version**: Python 3.11 (backend services), TypeScript 5.x (frontend)  
**Primary Dependencies**: FastAPI (API), Next.js (frontend), Vertex AI Gemini (LLM), BigQuery (storage)  
**Storage**: Google BigQuery (brand data), Google Cloud Storage (document storage)  
**Testing**: Contract tests (repository interfaces), integration tests (LLM mocking)  
**Target Platform**: Google Cloud Run (existing ml-enrichment service extension)  
**Project Type**: Monorepo enhancement - extends existing brand analysis functionality  
**Performance Goals**: <30s brand analysis including LLM, <500ms API response for cached results  
**Constraints**: Vertex AI API rate limits, token costs, fallback to keyword analysis required  
**Scale/Scope**: ~50 brand analyses/day, 3x LLM calls per analysis (themes, voice, narrative)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Required Checks**:

1. **Hexagonal Architecture (Principle I)**
   - ✅ Does feature separate domain, application, and adapter layers?
     - *Extends existing brand domain entities with LLM analysis capabilities*
   - ✅ Are repository interfaces (ports) defined in domain/?
     - *Uses existing BrandRepository and ContentGenerationRepository interfaces*
   - ✅ Do adapters implement domain interfaces without domain depending on infrastructure?
     - *New VertexAIAnalysisAdapter implements analysis interfaces in adapters/ layer, domain remains infrastructure-independent*

2. **Monorepo Service Separation (Principle II)**
   - ✅ Does feature belong in existing service or require new service?
     - *Extends existing ml-enrichment service - natural fit for AI-powered analysis*
   - ✅ If new service: Does it have independent cloudbuild.yaml and Dockerfile?
     - *N/A - uses existing ml-enrichment service infrastructure*
   - ✅ Are service boundaries clear (no cross-service imports)?
     - *Interfaces with jobs-api via existing brand API endpoints*

3. **Cloud-Native, Serverless First (Principle III)**
   - ✅ Does feature use Cloud Run/Functions (not VMs)?
     - *Runs within existing ml-enrichment Cloud Run service*
   - ✅ Does it use managed services (BigQuery, GCS, Vertex AI)?
     - *Uses Vertex AI Gemini, existing BigQuery brand tables, GCS for documents*
   - ✅ Is service stateless (all state in BigQuery/GCS)?
     - *LLM analysis results stored in BigQuery, prompts cached in memory*

4. **Polymorphic Enrichment Tracking (Principle IV)**
   - ✅ Does feature add new enrichment type to job_enrichments table?
     - *Uses existing brand_representations table with analysis_type field for LLM vs keyword tracking*
   - ✅ Does it track enrichment_version for model iteration?
     - *Adds llm_model_version field to brand_representations for Gemini model tracking*
   - ✅ Is processing idempotent (checks existing enrichments)?
     - *Checks existing analysis before LLM calls, implements caching*

5. **Lazy-Loading ML Models (Principle V)**
   - ✅ Are ML models loaded lazily (not at import time)?
     - *Vertex AI client initialized on first use via get_vertex_client() pattern*
   - ✅ Is loading wrapped in `get_*()` singleton pattern?
     - *get_vertex_client() and get_gemini_model() functions with lazy initialization*

6. **Human-in-the-Loop ML Reinforcement (Principle VI)**
   - ✅ Can users provide feedback on ML outputs?
     - *Extends existing brand feedback system to capture LLM analysis quality ratings*
   - ✅ Does feedback flow back to lexicon/training data?
     - *Feedback stored in brand_learning_events for future prompt engineering*

7. **Infrastructure as Code & GitOps (Principle VII)**
   - ✅ Is infrastructure defined in code (cloudbuild.yaml, SQL scripts)?
     - *Uses existing ml-enrichment cloudbuild.yaml, extends brand schema with migration script*
   - ✅ Are migrations idempotent?
     - *Schema migration adds columns with IF NOT EXISTS, updates are MERGE statements*
   - ✅ Are environment variables documented?
     - *VERTEX_AI_PROJECT_ID, VERTEX_AI_LOCATION, GEMINI_MODEL_NAME documented in service README*

8. **Code Clarity & Maintainability (Principle VIII)**
   - ✅ No HEREDOCs or forbidden string construction patterns?
     - *LLM prompts stored in separate prompt files or triple-quoted Python strings*
   - ✅ SQL queries in separate files or proper string formatting?
     - *Analysis queries use existing BigQuery adapter pattern with triple-quoted strings*

## Project Structure

### Documentation (this feature)

```text
specs/003-intelligent-brand-analysis/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (enhanced areas)

```text
services/ml-enrichment/           # Enhanced ML service
├── adapters/
│   └── vertex_ai_adapter.py    # NEW: Vertex AI client adapter
├── lib/
│   ├── brand_analysis/          # NEW: LLM-powered analysis
│   │   ├── __init__.py
│   │   ├── vertex_analyzer.py   # Vertex AI Gemini integration
│   │   ├── prompt_templates.py  # LLM prompts for analysis tasks
│   │   ├── fallback_analyzer.py # Existing keyword-based backup
│   │   └── analysis_orchestrator.py # Coordinates LLM + fallback
│   └── utils/
│       └── llm_cache.py         # NEW: Response caching utility
└── scripts/
    └── migrate_brand_schema.py   # NEW: Add LLM tracking columns

api/jobs-api/                    # Enhanced API endpoints
├── domain/
│   ├── entities.py             # Enhanced with LLM metadata
│   └── repositories.py         # Enhanced interfaces
├── application/
│   └── use_cases.py            # Enhanced brand analysis orchestration
└── adapters/
    └── ml_enrichment_client.py # Enhanced to use new analysis types

sql/                             # Database enhancements
├── brand_representations_v2_schema.sql  # NEW: LLM tracking columns
└── llm_analysis_cache_schema.sql        # NEW: Response caching table
```

**Structure Decision**: Enhances existing ml-enrichment service rather than creating new service. LLM integration is a natural extension of current brand analysis capabilities. Maintains service isolation while leveraging existing infrastructure.

## Phase Breakdown

### Phase 0: Research & Requirements Clarification (Days 1-3)

**Objective**: Resolve specification ambiguities and validate technical approach

**Research Tasks**:
1. **LLM Model Selection** - Compare Gemini Pro vs Flash for brand analysis use cases (cost, latency, quality)
2. **Prompt Engineering Strategy** - Research effective prompts for theme extraction, voice analysis, narrative building
3. **API Rate Limiting** - Document Vertex AI quotas, pricing, and retry strategies
4. **Fallback Strategy** - Define graceful degradation when LLM unavailable
5. **Caching Architecture** - Design cache invalidation and storage strategy for LLM responses
6. **Multi-language Support** - Clarify English-only vs multi-language requirements

**Deliverables**:
- `research.md` with technical decisions and rationale
- LLM model comparison analysis
- Prompt templates and engineering guidelines
- Performance benchmarks and cost projections

### Phase 1: Design & Contracts (Days 4-10)

**Objective**: Define data models, API contracts, and integration interfaces

**Design Tasks**:
1. **Data Model Enhancement** - Extend brand schema with LLM metadata and caching
2. **Domain Entity Updates** - Add LLM analysis results to brand entities
3. **API Contract Refinement** - Update OpenAPI spec with enhanced response fields
4. **Integration Interfaces** - Define Vertex AI adapter contracts
5. **Error Handling Design** - Specify fallback flows and error responses
6. **Performance Monitoring** - Define metrics for LLM integration health

**Deliverables**:
- `data-model.md` with enhanced BigQuery schema
- `contracts/` with updated API specifications
- `quickstart.md` for LLM integration development
- Database migration scripts

### Phase 2: Implementation Planning (Days 11-15)

**Objective**: Break down development into parallel, testable tasks

**Planning Tasks**:
1. **Task Decomposition** - Independent development tracks for backend/frontend
2. **Testing Strategy** - Unit tests with LLM mocking, integration tests
3. **Deployment Strategy** - Gradual rollout with feature flags
4. **Monitoring & Alerting** - LLM API health, cost tracking, fallback usage
5. **Documentation** - Developer guides and troubleshooting

**Deliverables**:
- `tasks.md` with 30-40 implementation tasks
- Testing framework for LLM integration
- Deployment and rollback procedures
- Monitoring and alerting specifications

## Risk Assessment

**High Risk**:
- **Vertex AI API Availability** - External dependency could cause service degradation
  - *Mitigation*: Robust fallback to keyword analysis, health checks, circuit breaker pattern
- **LLM Response Quality** - Inconsistent or inappropriate theme extraction
  - *Mitigation*: Confidence thresholds, human feedback loops, A/B testing vs existing approach
- **Cost Escalation** - Unexpected token usage from complex documents
  - *Mitigation*: Document size limits, token budgeting, cost monitoring alerts

**Medium Risk**:
- **Response Time Degradation** - LLM calls extend analysis beyond 30s target
  - *Mitigation*: Async processing option, response caching, timeout configurations
- **Prompt Engineering Complexity** - Difficulty achieving consistent, high-quality outputs
  - *Mitigation*: Iterative prompt development, validation datasets, feedback integration

**Low Risk**:
- **Schema Migration Complexity** - Adding LLM columns to existing brand tables
  - *Mitigation*: Idempotent migration scripts, backward compatibility preservation

## Success Metrics

**Technical Metrics**:
- LLM API success rate >95%
- Fallback activation rate <10% 
- Analysis completion time <30s (P95)
- Cache hit rate >40% for similar documents

**Quality Metrics**:
- User satisfaction with theme relevance >90%
- Generated content preference vs current approach >70%
- Confidence score accuracy (calibration) within ±10%

**Business Metrics**:
- Reduced "generic content" feedback by 60%
- Increased brand analysis completion rate by 20%
- User engagement with generated content up 40%

## Dependencies

**External Dependencies**:
- Vertex AI Gemini API availability and pricing
- Google Cloud Authentication for service accounts
- Existing brand analysis infrastructure (Phase 002 implementation)

**Internal Dependencies**:
- BigQuery schema migrations deployed
- Updated ml-enrichment service with enhanced requirements
- Frontend components updated to display enhanced analysis results

**Critical Path**:
1. Research & prompt engineering (blocks all implementation)
2. Schema migrations (blocks backend development)
3. Vertex AI adapter implementation (blocks LLM integration)
4. Fallback strategy implementation (blocks production deployment)

## Complexity Tracking

> **No Constitutional Violations Detected**

All requirements align with established architecture principles. Feature extends existing service boundaries appropriately and maintains hexagonal architecture separation. LLM integration follows established lazy-loading patterns for external services.