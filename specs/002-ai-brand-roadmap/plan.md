# Implementation Plan: AI Brand Roadmap – From Task-Level ML to One-Click Professional Branding

**Branch**: `002-ai-brand-roadmap` | **Date**: December 4, 2024 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-ai-brand-roadmap/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature transforms CapacityReset from disconnected ML tasks into an identity-aware AI engine that creates coherent professional brands across multiple surfaces. The system will analyze professional documents to extract brand themes and voice characteristics, generate cross-surface content (LinkedIn, CV, portfolio) with consistent messaging, and learn from user feedback to improve future generations. Key requirements include brand representation persistence, sub-30-second generation times, and <10% editing requirements for 80% of users.

## Technical Context

**Language/Version**: Python 3.11 (brand analysis/generation services), TypeScript 5.x (frontend branding UI)  
**Primary Dependencies**: FastAPI (brand API), Next.js (brand management UI), Vertex AI (LLM for brand analysis/generation), spaCy (document analysis)  
**Storage**: Google BigQuery (brand representations, generated content, learning events), Google Cloud Storage (uploaded documents)  
**Testing**: Contract tests (brand repository interfaces), integration tests (brand analysis use cases)  
**Target Platform**: Google Cloud Run (brand services), Cloud Functions (document processing events)  
**Project Type**: New brand-focused service in monorepo extending existing ML enrichment architecture  
**Performance Goals**: <10min brand discovery, <30s cross-surface generation, <500ms brand overview retrieval  
**Constraints**: Job seekers only in Phase 1; CV required with optional LinkedIn; 3 output surfaces minimum  
**Scale/Scope**: Primary user persona: job seekers; Input: CV required + LinkedIn optional; Output: 3 surfaces (CV summary, LinkedIn summary, portfolio introduction)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Required Checks**:

1. **Hexagonal Architecture (Principle I)**
   - [x] Does feature separate domain, application, and adapter layers?
     - *Brand entities in domain/, brand use cases in application/, BigQuery adapters for persistence*
   - [x] Are repository interfaces (ports) defined in domain/?
     - *BrandRepository, ContentGenerationRepository, LearningEventRepository interfaces*
   - [x] Do adapters implement domain interfaces without domain depending on infrastructure?
     - *BigQuery adapters implement domain repository interfaces*

2. **Monorepo Service Separation (Principle II)**
   - [x] Does feature belong in existing service or require new service?
     - *Extends existing ml-enrichment service with new brand capabilities*
   - [x] If new service: Does it have independent cloudbuild.yaml and Dockerfile?
     - *Uses existing ml-enrichment service infrastructure*
   - [x] Are service boundaries clear (no cross-service imports)?
     - *Brand functionality contained within ml-enrichment service boundaries*

3. **Cloud-Native, Serverless First (Principle III)**
   - [x] Does feature use Cloud Run/Functions (not VMs)?
     - *Extends existing Cloud Run ml-enrichment service*
   - [x] Does it use managed services (BigQuery, GCS, Vertex AI)?
     - *BigQuery for brand persistence, GCS for documents, Vertex AI for LLM generation*
   - [x] Is service stateless (all state in BigQuery/GCS)?
     - *All brand representations and generated content persisted in BigQuery*

4. **Polymorphic Enrichment Tracking (Principle IV)** *(if ML feature)*
   - [x] Does feature add new enrichment type to job_enrichments table?
     - *New enrichment_type: 'brand_analysis' for document brand extraction*
   - [x] Does it track enrichment_version for model iteration?
     - *Brand analysis models versioned for continuous improvement*
   - [x] Is processing idempotent (checks existing enrichments)?
     - *Checks for existing brand representations before reprocessing*

5. **Lazy-Loading ML Models (Principle V)** *(if ML feature)*
   - [x] Are ML models loaded lazily (not at import time)?
     - *Brand analysis and generation models loaded on-demand*
   - [x] Is loading wrapped in `get_*()` singleton pattern?
     - *get_brand_analyzer(), get_content_generator() functions*

6. **Human-in-the-Loop ML Reinforcement (Principle VI)** *(if user-facing ML)*
   - [x] Can users provide feedback on ML outputs?
     - *Users edit brand overviews and generated content with feedback tracking*
   - [x] Does feedback flow back to lexicon/training data?
     - *Brand learning events feed back to improve future brand analysis and generation*

7. **Infrastructure as Code & GitOps (Principle VII)**
   - [x] Is infrastructure defined in code (cloudbuild.yaml, SQL scripts)?
     - *Uses existing ml-enrichment cloudbuild.yaml, new BigQuery schemas in sql/*
   - [x] Are migrations idempotent?
     - *New brand-related tables created with IF NOT EXISTS*
   - [x] Are environment variables documented?
     - *Vertex AI and brand service configuration documented*

**GATE STATUS: ✅ PASS** - All constitutional principles satisfied with extensions to existing ml-enrichment service.

## Constitution Check (Post-Design Re-evaluation)

*Re-checked after Phase 1 design completion - December 4, 2024*

**Design Validation Results**:

1. **Hexagonal Architecture (Principle I)** - ✅ **CONFIRMED**
   - Brand domain entities clearly separated (BrandRepresentation, ContentGeneration, BrandLearningEvent)
   - Repository interfaces defined in domain layer (BrandRepository, ContentGenerationRepository, LearningRepository)  
   - BigQuery adapters implement interfaces without domain dependencies
   - Brand analysis and generation services properly layered

2. **Monorepo Service Separation (Principle II)** - ✅ **CONFIRMED**
   - Brand functionality properly contained within ml-enrichment service boundaries
   - Reuses existing CloudBuild configuration and infrastructure
   - Clear separation from jobs-api (brand management endpoints) and jobs-web (brand UI)
   - No cross-service dependencies introduced

3. **Cloud-Native, Serverless First (Principle III)** - ✅ **CONFIRMED**  
   - Extends existing Cloud Run ml-enrichment service
   - Uses managed Vertex AI for LLM generation
   - All state persisted in BigQuery (brand representations) and GCS (documents)
   - Maintains stateless service pattern

4. **Polymorphic Enrichment Tracking (Principle IV)** - ✅ **CONFIRMED**
   - New enrichment_type: 'brand_analysis' added to existing enrichment tracking
   - Brand analysis models versioned consistently with existing ML patterns
   - Idempotent processing checks for existing brand representations
   - Fits established enrichment architecture

5. **Lazy-Loading ML Models (Principle V)** - ✅ **CONFIRMED**
   - Brand analyzer and content generator implement lazy loading patterns
   - get_brand_analyzer(), get_content_generator() singleton functions defined
   - Consistent with existing spaCy and Vertex AI loading patterns in ml-enrichment

6. **Human-in-the-Loop ML Reinforcement (Principle VI)** - ✅ **CONFIRMED**
   - Comprehensive feedback system through BrandLearningEvent entity
   - User edits, regenerations, and preferences captured and processed  
   - Learning loop feeds back to brand representation refinement
   - Consistent with existing skills lexicon feedback patterns

7. **Infrastructure as Code & GitOps (Principle VII)** - ✅ **CONFIRMED**
   - BigQuery schemas defined in sql/ directory following existing patterns
   - Reuses existing ml-enrichment cloudbuild.yaml and deployment
   - Environment variables documented and follow established naming
   - Migration scripts follow idempotent patterns

**FINAL GATE STATUS: ✅ PASS** - Design maintains constitutional compliance throughout all phases.

## Project Structure

### Documentation (this feature)

```text
specs/002-ai-brand-roadmap/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# AI Brand Roadmap extends existing CapacityReset structure

services/
├── ml-enrichment/       # EXTENDED: Brand analysis and generation capabilities
    ├── domain/
    │   ├── entities.py      # EXTENDED: Brand representation, professional themes
    │   └── repositories.py  # EXTENDED: Brand repository interfaces
    ├── application/
    │   └── use_cases.py     # EXTENDED: Brand analysis and generation use cases
    ├── adapters/
    │   └── bigquery_repository.py  # EXTENDED: Brand persistence adapters
    └── lib/
        ├── brand_analyzer.py    # NEW: Document analysis for brand extraction
        └── content_generator.py # NEW: Cross-surface content generation

api/
└── jobs-api/           # EXTENDED: Brand management endpoints
    ├── domain/         # EXTENDED: Brand entities + repository ports
    ├── application/    # EXTENDED: Brand use cases
    ├── adapters/       # EXTENDED: Brand repository implementations
    └── api/
        └── routes.py   # EXTENDED: Brand discovery and generation endpoints

apps/
└── jobs-web/           # EXTENDED: Brand management UI
    └── src/
        ├── app/
        │   └── brand/  # NEW: Brand discovery and management pages
        └── components/
            └── brand/  # NEW: Brand UI components

sql/                     # EXTENDED: Brand-related schemas
├── brand_representations_schema.sql     # NEW: Brand identity storage
├── content_generations_schema.sql       # NEW: Generated content tracking
├── brand_learning_events_schema.sql     # NEW: User feedback capture
└── professional_themes_schema.sql       # NEW: Extracted themes and patterns

# Each service maintains existing structure:
├── cloudbuild.yaml     # Cloud Build configuration
├── Dockerfile          # Container definition
├── requirements.txt    # Python dependencies
├── main.py             # Service entry point
└── README.md           # Service documentation
```

**Structure Decision**: This feature extends the existing ml-enrichment service with brand capabilities, following Principle II (Service Separation). Brand functionality integrates with existing ML infrastructure while maintaining clear domain boundaries.

## Phase 0: Research & Architecture (0-30 days)

**Prerequisites**: Constitution Check passed ✅

**Research Objectives**:
1. **Clarify Requirements**: Resolve NEEDS CLARIFICATION markers
   - User personas: job seekers only vs. multiple professional personas  
   - Input surfaces: CV only vs. CV + LinkedIn + others
   - Output surfaces: minimum count for "one-click branding" experience
2. **Brand Analysis Technology**: Research document analysis for professional identity extraction
3. **Content Generation Strategy**: Evaluate LLM approaches for cross-surface consistency
4. **Learning Architecture**: Design feedback loop for continuous improvement
5. **Performance Optimization**: Strategy for sub-30-second generation times

**Deliverables**:
- `research.md`: Technology decisions, architecture patterns, performance strategies
- All NEEDS CLARIFICATION markers resolved with specific requirements

## Phase 1: Core Design & Contracts (30-90 days)  

**Prerequisites**: Phase 0 complete, research.md finalized

**Design Objectives**:
1. **Data Model**: Brand representation, content generation, learning events schemas
2. **API Contracts**: Brand discovery, content generation, feedback endpoints
3. **Integration Strategy**: Extension points within existing ml-enrichment service
4. **User Flows**: Brand intake, overview review, one-click generation, refinement

**Deliverables**:
- `data-model.md`: Brand entities, relationships, BigQuery schemas
- `contracts/`: OpenAPI specifications for brand endpoints
- `quickstart.md`: Developer guide for brand feature integration
- Updated agent context with brand technology stack

## Phase 2: Implementation Roadmap (90-180 days)

**Prerequisites**: Phase 1 complete, design validated

**Implementation Strategy**:
- **Month 1**: Brand analysis service (document → brand representation)
- **Month 2**: Content generation service (brand → cross-surface content)  
- **Month 3**: Learning loop integration (feedback → brand improvement)

**Success Validation**:
- SC-001: <10min brand discovery time
- SC-002: <10% content editing requirement  
- SC-004: <30s cross-surface generation
- SC-005: 85% single-session completion rate

**Note**: Phase 2 implementation details will be generated by `/speckit.tasks` command after Phase 1 completion.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**Status**: No constitutional violations identified. All principles satisfied through extension of existing ml-enrichment service architecture.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Next Steps

1. **Execute Phase 0**: Run research workflows to resolve NEEDS CLARIFICATION requirements
2. **Generate Research**: Create `research.md` with technology decisions and architecture patterns
3. **Phase 1 Readiness**: Proceed to design phase after all clarifications resolved
4. **Implementation Planning**: Use `/speckit.tasks` after Phase 1 completion for detailed implementation roadmap
