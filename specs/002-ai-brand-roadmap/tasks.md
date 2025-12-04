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

- [X] T001 Create BigQuery schema files per data-model.md in sql/ directory
- [X] T002 [P] Add brand dependencies to services/ml-enrichment/requirements.txt
- [ ] T003 [P] Configure Vertex AI environment variables in services/ml-enrichment/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create brand_representations table schema in sql/brand_representations_schema.sql
- [X] T005 [P] Create professional_themes table schema in sql/professional_themes_schema.sql  
- [X] T006 [P] Create professional_surfaces table schema in sql/professional_surfaces_schema.sql
- [X] T007 [P] Create content_generations table schema in sql/content_generations_schema.sql
- [X] T008 [P] Create brand_learning_events table schema in sql/brand_learning_events_schema.sql
- [X] T009 [P] Create brand_theme_associations table schema in sql/brand_theme_associations_schema.sql
- [X] T010 [P] Extend domain entities in api/jobs-api/domain/entities.py with BrandRepresentation, ContentGeneration, BrandLearningEvent
- [X] T011 [P] Define brand repository interfaces in api/jobs-api/domain/repositories.py with BrandRepository, ContentGenerationRepository, LearningRepository
- [ ] T012 Implement BigQuery brand adapters in services/ml-enrichment/adapters/bigquery_repository.py
- [X] T013 Create idempotent BigQuery table creation script in services/ml-enrichment/scripts/create_brand_tables.py
- [X] T014 [P] Initialize professional surfaces data in sql/professional_surfaces_data.sql (cv_summary, linkedin_summary, portfolio_intro)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Professional Brand Discovery (Priority: P1) 🎯 MVP

**Goal**: Job seeker uploads CV and receives comprehensive brand overview with themes, voice characteristics, and narrative arc

**Independent Test**: Upload CV → generate brand overview → validate themes and voice characteristics extracted

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create BrandAnalyzer class in services/ml-enrichment/lib/brand_analyzer.py
- [ ] T016 [P] [US1] Create document parser utilities in services/ml-enrichment/lib/document_parser.py
- [ ] T017 [US1] Implement brand analysis use case in services/ml-enrichment/application/use_cases.py
- [X] T018 [US1] Add document upload endpoint in api/jobs-api/api/routes.py for /brand/analysis
- [X] T019 [US1] Implement brand overview retrieval endpoint in api/jobs-api/api/routes.py for /brand/overview/{brand_id}
- [X] T020 [US1] Add brand analysis request/response models in api/jobs-api/api/schemas.py
- [ ] T021 [US1] Create GCS document upload utility in services/ml-enrichment/lib/document_storage.py
- [ ] T022 [US1] Add lazy-loading function get_brand_analyzer() in services/ml-enrichment/main.py
- [X] T023 [US1] Implement brand overview update endpoint in api/jobs-api/api/routes.py for PATCH /brand/overview/{brand_id}
- [X] T024 [US1] Create brand management UI page in apps/jobs-web/src/app/brand/page.tsx
- [X] T025 [P] [US1] Create BrandAnalyzer component in apps/jobs-web/src/components/brand/BrandAnalyzer.tsx
- [X] T026 [P] [US1] Create BrandOverview component in apps/jobs-web/src/components/brand/BrandOverview.tsx

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
- [X] T031 [US2] Add content generation endpoint in api/jobs-api/api/routes.py for POST /brand/{brand_id}/generate
- [X] T032 [US2] Add generated content retrieval endpoint in api/jobs-api/api/routes.py for GET /brand/{brand_id}/content
- [X] T033 [US2] Create content generation request/response models in api/jobs-api/api/schemas.py
- [ ] T034 [US2] Add lazy-loading function get_content_generator() in services/ml-enrichment/main.py
- [X] T035 [US2] Implement content regeneration endpoint in api/jobs-api/api/routes.py for POST /brand/{brand_id}/content/{generation_id}/regenerate
- [X] T036 [P] [US2] Create ContentGenerator component in apps/jobs-web/src/components/brand/ContentGenerator.tsx
- [X] T037 [P] [US2] Create GeneratedContent component in apps/jobs-web/src/components/brand/GeneratedContent.tsx
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
- [X] T042 [US3] Add feedback submission endpoint in api/jobs-api/api/routes.py for POST /brand/{brand_id}/feedback
- [X] T043 [US3] Create feedback request models in api/jobs-api/api/schemas.py
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
- [X] T052 [P] Create professional surfaces management API in api/jobs-api/api/routes.py for GET /brand/surfaces
- [ ] T053 [P] Add brand analytics dashboard components in apps/jobs-web/src/components/brand/analytics/
- [ ] T054 Run quickstart.md validation and integration testing
- [ ] T055 [P] Update API documentation with brand endpoints in api/jobs-api/docs/
- [ ] T056 [P] Performance optimization for sub-30-second generation requirement

---

## Phase 7: Constitutional Compliance & Template Management

**Purpose**: Ensure code clarity principles and template-based content generation following Constitution Principle VIII

- [ ] T057 [P] Create generation templates directory in services/ml-enrichment/templates/brand/ following file-based approach
- [ ] T058 [P] Create CV summary template in services/ml-enrichment/templates/brand/cv_summary.jinja2
- [ ] T059 [P] Create LinkedIn summary template in services/ml-enrichment/templates/brand/linkedin_summary.jinja2
- [ ] T060 [P] Create portfolio introduction template in services/ml-enrichment/templates/brand/portfolio_intro.jinja2
- [ ] T061 Implement template loader utility in services/ml-enrichment/lib/template_loader.py (no HEREDOCs per Constitution VIII)
- [ ] T062 Create SQL query files in sql/queries/brand/ directory for brand-related database operations
- [ ] T063 [P] Verify no HEREDOC patterns in brand-related code (Constitution VIII compliance audit)
- [ ] T064 [P] Update content_generator.py to use file-based templates instead of inline strings

---

## Phase 8: Edge Case Handling

**Purpose**: Handle edge cases identified in spec.md for robust production behavior

### Insufficient Content Handling (Edge Case 1)

- [ ] T065 [US1] Implement minimum content validator in services/ml-enrichment/lib/content_validator.py
- [ ] T066 [US1] Add graceful degradation prompts for sparse CVs in services/ml-enrichment/lib/brand_analyzer.py
- [ ] T067 [US1] Create user prompt flow for additional context when CV lacks sufficient content in apps/jobs-web/src/components/brand/ContentPrompt.tsx

### Career Transition Handling (Edge Case 2)

- [ ] T068 [US1] Implement multi-identity detection in services/ml-enrichment/lib/identity_detector.py
- [ ] T069 [US1] Add career transition narrative support to brand representation model
- [ ] T070 [US1] Create career transition UI component in apps/jobs-web/src/components/brand/CareerTransition.tsx

### Edit Contradiction Handling (Edge Case 3)

- [ ] T071 [US3] Implement brand coherence validator in services/ml-enrichment/lib/coherence_validator.py
- [ ] T072 [US3] Add contradiction detection for user edits vs. established brand
- [ ] T073 [US3] Create edit conflict resolution UI in apps/jobs-web/src/components/brand/EditConflict.tsx

### Context Divergence Handling (Edge Case 4)

- [ ] T074 [US2] Implement surface context analyzer in services/ml-enrichment/lib/context_analyzer.py
- [ ] T075 [US2] Add cross-context consistency maintenance logic to content generator
- [ ] T076 [US2] Create context adaptation preview in apps/jobs-web/src/components/brand/ContextPreview.tsx

### Similar Background Handling (Edge Case 5)

- [ ] T077 [US1] Implement unique differentiator extraction in services/ml-enrichment/lib/differentiator_extractor.py
- [ ] T078 [US1] Add differentiation scoring to brand analysis output

---

## Phase 9: Success Criteria Measurement & Validation

**Purpose**: Implement measurement infrastructure to validate all success criteria from spec.md

### SC-001: Brand Discovery Time (<10 minutes)

- [ ] T079 [P] Implement brand discovery timing tracker in services/ml-enrichment/lib/metrics/discovery_timer.py
- [ ] T080 [P] Add discovery time logging to brand analysis use case
- [ ] T081 [P] Create discovery time dashboard widget in apps/jobs-web/src/components/brand/analytics/DiscoveryTime.tsx

### SC-002: Edit Requirement (<10% editing for 80% users)

- [ ] T082 [P] Implement edit percentage calculator in services/ml-enrichment/lib/metrics/edit_tracker.py
- [ ] T083 [P] Add word count comparison between generated and final content
- [ ] T084 [P] Create edit frequency analytics in apps/jobs-web/src/components/brand/analytics/EditMetrics.tsx

### SC-003: Cross-Surface Consistency (90% semantic similarity)

- [ ] T085 [P] Implement semantic similarity scorer in services/ml-enrichment/lib/metrics/consistency_scorer.py
- [ ] T086 [P] Add automated consistency validation to content generation pipeline
- [ ] T087 [P] Create consistency score display in apps/jobs-web/src/components/brand/analytics/ConsistencyScore.tsx

### SC-004: Generation Time (<30 seconds)

- [ ] T088 [P] Implement generation timing tracker in services/ml-enrichment/lib/metrics/generation_timer.py
- [ ] T089 [P] Add timing metrics to one-click generation use case
- [ ] T090 [P] Create performance monitoring for generation latency in apps/jobs-web/src/components/brand/analytics/GenerationPerformance.tsx

### SC-005: Single Session Completion (85% success rate)

- [ ] T091 [P] Implement session completion tracker in services/ml-enrichment/lib/metrics/session_tracker.py
- [ ] T092 [P] Add session state persistence for workflow tracking
- [ ] T093 [P] Create session completion analytics in apps/jobs-web/src/components/brand/analytics/SessionMetrics.tsx

### SC-006: User Satisfaction (>4.0/5.0 rating)

- [ ] T094 [P] Implement satisfaction rating capture in api/jobs-api/api/routes.py for POST /brand/{brand_id}/rating
- [ ] T095 [P] Create rating UI component in apps/jobs-web/src/components/brand/SatisfactionRating.tsx
- [ ] T096 [P] Add satisfaction analytics dashboard in apps/jobs-web/src/components/brand/analytics/SatisfactionScore.tsx

### SC-007: Learning Improvement (25% edit reduction after 3 sessions)

- [ ] T097 [P] Implement learning progress tracker in services/ml-enrichment/lib/metrics/learning_tracker.py
- [ ] T098 [P] Add session-over-session edit comparison analytics
- [ ] T099 [P] Create learning improvement visualization in apps/jobs-web/src/components/brand/analytics/LearningProgress.tsx

### SC-008: Onboarding Time (<15 minutes to first content)

- [ ] T100 [P] Implement end-to-end onboarding timer in services/ml-enrichment/lib/metrics/onboarding_timer.py
- [ ] T101 [P] Add onboarding milestone tracking (account creation → first branded content)
- [ ] T102 [P] Create onboarding funnel analytics in apps/jobs-web/src/components/brand/analytics/OnboardingFunnel.tsx

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Constitutional Compliance (Phase 7)**: Can run in parallel with Phase 6 - no blocking dependencies
- **Edge Case Handling (Phase 8)**: Depends on User Stories (Phase 3-5) - extends story functionality
- **Success Criteria Measurement (Phase 9)**: Depends on User Stories and Polish phases - adds measurement layer

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
- [ ] CV upload generates brand overview in <10 minutes (SC-001: T079-T081)
- [ ] Brand themes and voice characteristics accurately extracted
- [ ] User can edit and update brand overview

**After User Story 2**:
- [ ] Cross-surface generation completes in <30 seconds (SC-004: T088-T090)
- [ ] Content maintains 90% consistency across surfaces (SC-003: T085-T087)
- [ ] Generated content requires <10% editing (SC-002: T082-T084)

**After User Story 3**:
- [ ] User feedback captured and processed
- [ ] Subsequent generations show learning improvements (SC-007: T097-T099)
- [ ] Edit frequency reduces by 25% after 3 feedback sessions

**Cross-Cutting Validations**:
- [ ] 85% single-session completion rate (SC-005: T091-T093)
- [ ] User satisfaction exceeds 4.0/5.0 rating (SC-006: T094-T096)
- [ ] End-to-end onboarding under 15 minutes (SC-008: T100-T102)

---

## Success Criteria to Task Mapping

| Success Criteria | Description | Validation Tasks |
|-----------------|-------------|------------------|
| SC-001 | Brand discovery <10 minutes | T079, T080, T081 |
| SC-002 | <10% editing for 80% users | T082, T083, T084 |
| SC-003 | 90% cross-surface consistency | T085, T086, T087 |
| SC-004 | Generation <30 seconds | T088, T089, T090 |
| SC-005 | 85% single-session completion | T091, T092, T093 |
| SC-006 | User satisfaction >4.0/5.0 | T094, T095, T096 |
| SC-007 | 25% edit reduction after 3 sessions | T097, T098, T099 |
| SC-008 | Onboarding <15 minutes | T100, T101, T102 |

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability  
- Each user story should be independently completable and testable
- Focus on MVP delivery with User Story 1 first
- Validate each checkpoint before proceeding
- Performance targets: <10min brand analysis, <30s generation, 90% consistency