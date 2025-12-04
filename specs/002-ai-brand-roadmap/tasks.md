# Tasks: AI Brand Roadmap – From Task-Level ML to One-Click Professional Branding

**Input**: Design documents from `/specs/002-ai-brand-roadmap/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL per CapacityReset constitution. The hexagonal architecture provides testability through contract tests of repository interfaces.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for AI Brand Roadmap

- [ ] T001 Create BigQuery schema files per data-model.md in sql/ directory
- [ ] T002 [P] Add brand dependencies to services/ml-enrichment/requirements.txt
- [ ] T003 [P] Configure Vertex AI environment variables in services/ml-enrichment/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create brand_representations table schema in sql/brand_representations_schema.sql
- [ ] T005 [P] Create professional_themes table schema in sql/professional_themes_schema.sql  
- [ ] T006 [P] Create professional_surfaces table schema in sql/professional_surfaces_schema.sql
- [ ] T007 [P] Create content_generations table schema in sql/content_generations_schema.sql
- [ ] T008 [P] Create brand_learning_events table schema in sql/brand_learning_events_schema.sql
- [ ] T009 [P] Create brand_theme_associations table schema in sql/brand_theme_associations_schema.sql
- [ ] T010 [P] Extend domain entities in services/ml-enrichment/domain/entities.py with BrandRepresentation, ContentGeneration, BrandLearningEvent
- [ ] T011 [P] Define brand repository interfaces in services/ml-enrichment/domain/repositories.py with BrandRepository, ContentGenerationRepository, LearningRepository
- [ ] T012 Implement BigQuery brand adapters in services/ml-enrichment/adapters/bigquery_repository.py
- [ ] T013 Create idempotent BigQuery table creation script in services/ml-enrichment/scripts/create_brand_tables.py
- [ ] T014 [P] Initialize professional surfaces data in sql/professional_surfaces_data.sql (cv_summary, linkedin_summary, portfolio_intro)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Professional Brand Discovery (Priority: P1) 🎯 MVP

**Goal**: Job seeker uploads CV and receives comprehensive brand overview with themes, voice characteristics, and narrative arc

**Independent Test**: Upload CV → generate brand overview → validate themes and voice characteristics extracted

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create BrandAnalyzer class in services/ml-enrichment/lib/brand_analyzer.py
- [ ] T016 [P] [US1] Create document parser utilities in services/ml-enrichment/lib/document_parser.py
- [ ] T017 [US1] Implement brand analysis use case in services/ml-enrichment/application/use_cases.py
- [ ] T018 [US1] Add document upload endpoint in api/jobs-api/api/routes.py for /brand/analysis
- [ ] T019 [US1] Implement brand overview retrieval endpoint in api/jobs-api/api/routes.py for /brand/overview/{brand_id}
- [ ] T020 [US1] Add brand analysis request/response models in api/jobs-api/api/schemas.py
- [ ] T021 [US1] Create GCS document upload utility in services/ml-enrichment/lib/document_storage.py
- [ ] T022 [US1] Add lazy-loading function get_brand_analyzer() in services/ml-enrichment/main.py
- [ ] T023 [US1] Implement brand overview update endpoint in api/jobs-api/api/routes.py for PATCH /brand/overview/{brand_id}
- [ ] T024 [US1] Create brand management UI page in apps/jobs-web/src/app/brand/page.tsx
- [ ] T025 [P] [US1] Create BrandAnalyzer component in apps/jobs-web/src/components/brand/BrandAnalyzer.tsx
- [ ] T026 [P] [US1] Create BrandOverview component in apps/jobs-web/src/components/brand/BrandOverview.tsx

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - One-Click Cross-Surface Generation (Priority: P2)

**Goal**: User with brand overview generates consistent content across CV summary, LinkedIn summary, and portfolio introduction in <30 seconds

**Independent Test**: Use existing brand overview → request cross-surface generation → validate 3 surfaces generated with consistent messaging

### Implementation for User Story 2

- [ ] T027 [P] [US2] Create ContentGenerator class in services/ml-enrichment/lib/content_generator.py
- [ ] T028 [P] [US2] Create generation templates in services/ml-enrichment/lib/generation_templates.py
- [ ] T029 [P] [US2] Create consistency validator in services/ml-enrichment/lib/consistency_validator.py
- [ ] T030 [US2] Implement content generation use case in services/ml-enrichment/application/use_cases.py
- [ ] T031 [US2] Add content generation endpoint in api/jobs-api/api/routes.py for POST /brand/{brand_id}/generate
- [ ] T032 [US2] Add generated content retrieval endpoint in api/jobs-api/api/routes.py for GET /brand/{brand_id}/content
- [ ] T033 [US2] Create content generation request/response models in api/jobs-api/api/schemas.py
- [ ] T034 [US2] Add lazy-loading function get_content_generator() in services/ml-enrichment/main.py
- [ ] T035 [US2] Implement content regeneration endpoint in api/jobs-api/api/routes.py for POST /brand/{brand_id}/content/{generation_id}/regenerate
- [ ] T036 [P] [US2] Create ContentGenerator component in apps/jobs-web/src/components/brand/ContentGenerator.tsx
- [ ] T037 [P] [US2] Create GeneratedContent component in apps/jobs-web/src/components/brand/GeneratedContent.tsx
- [ ] T038 [P] [US2] Create ContentSurface component in apps/jobs-web/src/components/brand/ContentSurface.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Brand Learning and Refinement (Priority: P3)

**Goal**: System learns from user edits, regeneration requests, and feedback to improve future content generation

**Independent Test**: Make content edits → request regeneration → validate subsequent generations incorporate learned preferences

### Implementation for User Story 3

- [ ] T039 [P] [US3] Create BrandLearningEngine class in services/ml-enrichment/lib/brand_learning_engine.py
- [ ] T040 [P] [US3] Create feedback processor in services/ml-enrichment/lib/feedback_processor.py
- [ ] T041 [US3] Implement learning integration use case in services/ml-enrichment/application/use_cases.py
- [ ] T042 [US3] Add feedback submission endpoint in api/jobs-api/api/routes.py for POST /brand/{brand_id}/feedback
- [ ] T043 [US3] Create feedback request models in api/jobs-api/api/schemas.py
- [ ] T044 [US3] Implement learning event processing job in services/ml-enrichment/scripts/process_learning_events.py
- [ ] T045 [US3] Add brand representation update logic based on learning events in services/ml-enrichment/lib/brand_updater.py
- [ ] T046 [P] [US3] Create FeedbackCapture component in apps/jobs-web/src/components/brand/FeedbackCapture.tsx
- [ ] T047 [P] [US3] Create EditTracker component in apps/jobs-web/src/components/brand/EditTracker.tsx
- [ ] T048 [US3] Integrate learning feedback into content generation workflow

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T049 [P] Add performance monitoring for brand analysis and generation times in services/ml-enrichment/lib/performance_monitor.py
- [ ] T050 [P] Implement caching strategy for brand representations in services/ml-enrichment/lib/brand_cache.py
- [ ] T051 [P] Add comprehensive error handling and logging across all brand endpoints
- [ ] T052 [P] Create professional surfaces management API in api/jobs-api/api/routes.py for GET /brand/surfaces
- [ ] T053 [P] Add brand analytics dashboard components in apps/jobs-web/src/components/brand/analytics/
- [ ] T054 Run quickstart.md validation and integration testing
- [ ] T055 [P] Update API documentation with brand endpoints in api/jobs-api/docs/
- [ ] T056 [P] Performance optimization for sub-30-second generation requirement

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires brand representations from US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances US1/US2 but independently testable

### Within Each User Story

- Models and utilities before services
- Services before endpoints  
- Backend endpoints before frontend components
- Core implementation before UI integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Backend and frontend components marked [P] within each story can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch foundational components together:
Task: "Create professional_themes table schema in sql/professional_themes_schema.sql"
Task: "Create professional_surfaces table schema in sql/professional_surfaces_schema.sql" 
Task: "Extend domain entities with brand entities"

# Launch backend components for User Story 1 together:
Task: "Create BrandAnalyzer class in services/ml-enrichment/lib/brand_analyzer.py"
Task: "Create document parser utilities in services/ml-enrichment/lib/document_parser.py"

# Launch frontend components for User Story 1 together:
Task: "Create BrandAnalyzer component in apps/jobs-web/src/components/brand/BrandAnalyzer.tsx"
Task: "Create BrandOverview component in apps/jobs-web/src/components/brand/BrandOverview.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (CV upload → brand overview)
5. Deploy/demo basic brand discovery capability

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (Basic brand discovery)
3. Add User Story 2 → Test independently → Deploy/Demo (One-click cross-surface generation)
4. Add User Story 3 → Test independently → Deploy/Demo (Learning and refinement)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Brand Discovery)
   - Developer B: User Story 2 (Content Generation)
   - Developer C: User Story 3 (Learning System)
3. Stories complete and integrate independently

---

## Success Validation

**After User Story 1 (MVP)**:
- [ ] CV upload generates brand overview in <10 minutes
- [ ] Brand themes and voice characteristics accurately extracted
- [ ] User can edit and update brand overview

**After User Story 2**:
- [ ] Cross-surface generation completes in <30 seconds
- [ ] Content maintains 90% consistency across surfaces
- [ ] Generated content requires <10% editing

**After User Story 3**:
- [ ] User feedback captured and processed
- [ ] Subsequent generations show learning improvements
- [ ] Edit frequency reduces by 25% after 3 feedback sessions

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability  
- Each user story should be independently completable and testable
- Focus on MVP delivery with User Story 1 first
- Validate each checkpoint before proceeding
- Performance targets: <10min brand analysis, <30s generation, 90% consistency