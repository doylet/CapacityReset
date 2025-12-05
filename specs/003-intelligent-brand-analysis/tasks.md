# Tasks: Intelligent Brand Analysis with LLM Integration

**Input**: Design documents from `/specs/003-intelligent-brand-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL per CapacityReset constitution - not included unless explicitly requested in the feature specification. The architecture itself (hexagonal/ports & adapters) provides testability through contract tests of repository interfaces.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create enhanced ml-enrichment service structure for LLM integration
- [ ] T002 [P] Update services/ml-enrichment/requirements.txt with Vertex AI SDK dependencies
- [ ] T003 [P] Configure environment variables for Vertex AI in services/ml-enrichment/README.md
- [ ] T004 [P] Update services/ml-enrichment/cloudbuild.yaml with enhanced environment configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create brand schema migration in sql/brand_representations_v2_schema.sql
- [X] T006 Create LLM cache schema in sql/llm_analysis_cache_schema.sql  
- [X] T007 [P] Implement enhanced Brand domain entities in api/jobs-api/domain/entities.py
- [X] T008 [P] Update BrandRepository interface in api/jobs-api/domain/repositories.py
- [X] T009 Create Vertex AI adapter in services/ml-enrichment/lib/adapters/vertex_ai_adapter.py
- [X] T010 Create LLM cache utility in services/ml-enrichment/lib/brand_analysis/llm_cache_utility.py
- [X] T010b Create API call tracking utility in services/ml-enrichment/lib/utils/api_call_tracker.py
- [X] T011 Create brand analysis orchestrator in services/ml-enrichment/lib/brand_analysis/analysis_orchestrator.py
- [X] T012 [P] Create prompt templates in services/ml-enrichment/lib/brand_analysis/prompt_templates.py
- [X] T013 [P] Create fallback analyzer in services/ml-enrichment/lib/brand_analysis/fallback_analyzer.py
- [X] T014 Execute schema migrations using scripts/migrate_brand_schema.py
- [X] T015 Create brand feedback collection system in api/jobs-api/api/routes.py

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Nuanced Theme Extraction (Priority: P1) 🎯 MVP

**Goal**: Replace keyword-based theme extraction with LLM-powered analysis that understands context, tone, and implicit messaging

**Independent Test**: Upload CV, verify themes are contextually relevant with confidence explanations and evidence citations

### Implementation for User Story 1

- [ ] T016 [P] [US1] Create LLMThemeResult entity in api/jobs-api/domain/entities.py
- [ ] T017 [P] [US1] Create ThemeExtractionPrompt in services/ml-enrichment/lib/brand_analysis/prompt_templates.py
- [ ] T018 [US1] Implement theme extraction logic in services/ml-enrichment/lib/brand_analysis/vertex_analyzer.py
- [ ] T018b [US1] Implement narrative arc analysis logic in services/ml-enrichment/lib/brand_analysis/vertex_analyzer.py
- [ ] T019 [US1] Update theme extraction in brand analysis use case in api/jobs-api/application/use_cases.py
- [ ] T020 [US1] Enhanced theme display in brand analysis API response in api/jobs-api/api/routes.py
- [ ] T021 [US1] Add theme extraction error handling and fallback logic in analysis_orchestrator.py
- [ ] T022 [US1] Add theme analysis caching in llm_cache.py
- [ ] T023 [US1] Update frontend components to display enhanced themes in apps/jobs-web/src/components/

**Checkpoint**: At this point, User Story 1 should be fully functional with LLM-powered theme extraction

---

## Phase 4: User Story 2 - Dynamic Voice Characteristic Analysis (Priority: P2)

**Goal**: Capture communication style, energy level, and personality traits from professional documents for personalized content

**Independent Test**: Compare CV writing styles and verify system identifies appropriate voice characteristics with supporting quotes

### Implementation for User Story 2

- [ ] T024 [P] [US2] Create VoiceCharacteristics entity in api/jobs-api/domain/entities.py
- [ ] T025 [P] [US2] Create VoiceAnalysisPrompt in services/ml-enrichment/lib/brand_analysis/prompt_templates.py
- [ ] T026 [US2] Implement voice analysis logic in services/ml-enrichment/lib/brand_analysis/vertex_analyzer.py
- [ ] T027 [US2] Update voice analysis in brand analysis use case in api/jobs-api/application/use_cases.py
- [ ] T028 [US2] Enhanced voice characteristics in API response in api/jobs-api/api/routes.py
- [ ] T029 [US2] Add voice analysis error handling and confidence thresholds in analysis_orchestrator.py
- [ ] T030 [US2] Add voice analysis caching in llm_cache.py
- [ ] T031 [US2] Update frontend to display voice characteristics in apps/jobs-web/src/components/

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Contextual Content Generation (Priority: P3)

**Goal**: Generate platform-specific content that maintains authentic voice while adapting for different contexts

**Independent Test**: Generate content for multiple platforms and verify consistency in voice/themes with appropriate adaptation

### Implementation for User Story 3

- [ ] T032 [P] [US3] Create ContentGenerationRequest entity in api/jobs-api/domain/entities.py
- [ ] T033 [P] [US3] Create ContentGenerationPrompt in services/ml-enrichment/lib/brand_analysis/prompt_templates.py
- [ ] T034 [US3] Implement content generation logic in services/ml-enrichment/lib/brand_analysis/vertex_analyzer.py
- [ ] T035 [US3] Create content generation use case in api/jobs-api/application/use_cases.py
- [ ] T036 [US3] Add content generation API endpoint in api/jobs-api/api/routes.py
- [ ] T037 [US3] Add content generation caching and rate limiting in llm_cache.py
- [ ] T038 [US3] Add platform context validation in analysis_orchestrator.py
- [ ] T039 [US3] Create content generation UI in apps/jobs-web/src/components/

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Add comprehensive logging for LLM interactions in services/ml-enrichment/lib/brand_analysis/vertex_analyzer.py
- [ ] T041 [P] Implement circuit breaker pattern for Vertex AI failures in adapters/vertex_ai_adapter.py
- [ ] T042 [P] Add cost monitoring and token usage tracking in adapters/vertex_ai_adapter.py
- [ ] T043 [P] Create LLM health check endpoints in services/ml-enrichment/main.py
- [ ] T044 [P] Update API documentation with enhanced brand analysis in api/jobs-api/api/schemas.py
- [ ] T045 [P] Add performance monitoring for LLM response times in analysis_orchestrator.py
- [ ] T046 Update project documentation with LLM integration details in specs/003-intelligent-brand-analysis/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 but may reference shared analysis infrastructure
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses results from US1 and US2 but should be independently testable

### Within Each User Story

- Domain entities before services
- Prompt templates before analysis logic  
- Core implementation before API integration
- Backend implementation before frontend updates
- Error handling and caching after core functionality
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Entity creation and prompt template creation within each story can run in parallel
- Frontend and error handling tasks can run in parallel after core functionality

---

## Parallel Example: User Story 1

```bash
# Launch entity and prompt creation for User Story 1 together:
Task: "Create LLMThemeResult entity in api/jobs-api/domain/entities.py"
Task: "Create ThemeExtractionPrompt in services/ml-enrichment/lib/brand_analysis/prompt_templates.py"

# After core implementation:
Task: "Add theme analysis caching in llm_cache.py"
Task: "Update frontend components to display enhanced themes"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 - Theme Extraction
4. **STOP and VALIDATE**: Test theme extraction independently with real CVs
5. Deploy/demo enhanced theme analysis capability

### Incremental Delivery

1. Complete Setup + Foundational → LLM infrastructure ready
2. Add User Story 1 → Test theme extraction independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test voice analysis independently → Deploy/Demo
4. Add User Story 3 → Test content generation independently → Deploy/Demo
5. Each story adds value without breaking previous functionality

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Theme Extraction)
   - Developer B: User Story 2 (Voice Analysis)  
   - Developer C: User Story 3 (Content Generation)
3. Stories complete and integrate independently

---

## Technical Context

**Service Enhancement**: Extends existing ml-enrichment service with LLM capabilities
**API Integration**: Enhances existing jobs-api brand analysis endpoints
**Fallback Strategy**: Graceful degradation to keyword analysis when LLM unavailable
**Caching Strategy**: Reduces API costs through intelligent response caching
**Monitoring**: Comprehensive tracking of LLM performance, costs, and quality

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability  
- Each user story should be independently completable and testable
- LLM integration maintains existing API surface while enhancing analysis depth
- Fallback to keyword analysis ensures service reliability
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Focus on MVP (User Story 1) for initial value delivery