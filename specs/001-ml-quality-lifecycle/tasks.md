# Tasks: ML Quality & Lifecycle Improvements

**Input**: Design documents from `/specs/001-ml-quality-lifecycle/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: Tests are included per existing test patterns in `services/ml-enrichment/tests/`. The architecture uses hexagonal/ports & adapters with contract tests for repository interfaces.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md structure:
- **Service code**: `services/ml-enrichment/lib/`
- **Config files**: `services/ml-enrichment/config/`
- **SQL schemas**: `sql/`
- **Tests**: `services/ml-enrichment/tests/`
- **Scripts**: `services/ml-enrichment/scripts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, configuration structure, and model version foundation

- [X] T001 Create config directory structure at services/ml-enrichment/config/
- [X] T002 [P] Create model_versions.yaml configuration file at services/ml-enrichment/config/model_versions.yaml
- [X] T003 [P] Create skill_aliases.yaml configuration file at services/ml-enrichment/config/skill_aliases.yaml
- [X] T004 [P] Create ModelConfig dataclass in services/ml-enrichment/lib/config/model_config.py
- [X] T005 Add YAML configuration loading utility in services/ml-enrichment/lib/config/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Schema Extensions

- [X] T006 Create job_enrichments_v2_schema.sql with enrichment_version fields at sql/job_enrichments_v2_schema.sql
- [X] T007 [P] Create skill_aliases_schema.sql BigQuery table definition at sql/skill_aliases_schema.sql
- [X] T008 [P] Create evaluation_results_schema.sql BigQuery table definition at sql/evaluation_results_schema.sql
- [X] T009 [P] Create section_classifications_schema.sql BigQuery table definition at sql/section_classifications_schema.sql
- [X] T010 Create migration script for existing enrichments (legacy version tagging) at sql/migrations/001_add_version_fields.sql

### Domain Entities

- [X] T011 [P] Implement SkillAlias entity dataclass in services/ml-enrichment/lib/domain/entities/skill_alias.py
- [X] T012 [P] Implement ExtractedSkill entity dataclass (extended) in services/ml-enrichment/lib/domain/entities/extracted_skill.py
- [X] T013 [P] Implement SectionClassification entity dataclass in services/ml-enrichment/lib/domain/entities/section_classification.py
- [X] T014 [P] Implement ClusterAssignment entity dataclass (extended) in services/ml-enrichment/lib/domain/entities/cluster_assignment.py
- [X] T015 [P] Implement EvaluationResult entity dataclass in services/ml-enrichment/lib/domain/entities/evaluation_result.py
- [X] T016 Implement JobEnrichment entity dataclass (extended with version fields) in services/ml-enrichment/lib/domain/entities/job_enrichment.py
- [X] T017 Create domain entities __init__.py exporting all entities at services/ml-enrichment/lib/domain/entities/__init__.py

### Repository Interfaces (Ports)

- [X] T018 [P] Define SkillAliasRepository interface in services/ml-enrichment/lib/domain/repositories/skill_alias_repository.py
- [X] T019 [P] Define EvaluationResultRepository interface in services/ml-enrichment/lib/domain/repositories/evaluation_repository.py
- [X] T020 [P] Define SectionClassificationRepository interface in services/ml-enrichment/lib/domain/repositories/section_classification_repository.py
- [X] T021 Update domain repositories __init__.py at services/ml-enrichment/lib/domain/repositories/__init__.py

### BigQuery Adapters (Implementations)

- [X] T022 [P] Implement BigQuerySkillAliasRepository in services/ml-enrichment/lib/adapters/bigquery/skill_alias_adapter.py
- [X] T023 [P] Implement BigQueryEvaluationRepository in services/ml-enrichment/lib/adapters/bigquery/evaluation_adapter.py
- [X] T024 [P] Implement BigQuerySectionClassificationRepository in services/ml-enrichment/lib/adapters/bigquery/section_classification_adapter.py
- [X] T025 Update BigQuery adapters __init__.py at services/ml-enrichment/lib/adapters/bigquery/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - ML Model Version Management (Priority: P1) 🎯 MVP

**Goal**: Track which version of the ML model was used to process each job posting, enabling re-enrichment when models are updated and rollback if quality degrades.

**Independent Test**: Deploy a new model version and verify that (1) new enrichments are tagged with the new version, (2) the system can identify jobs processed by older versions, and (3) the correct version identifier is visible in all enrichment records.

### Tests for User Story 1

- [X] T026 [P] [US1] Contract test for model version tracking in services/ml-enrichment/tests/contract/test_model_version_tracking.py
- [X] T027 [P] [US1] Integration test for enrichment version queries in services/ml-enrichment/tests/integration/test_enrichment_versioning.py

### Implementation for User Story 1

- [X] T028 [US1] Implement get_version() method in UnifiedSkillsExtractor at services/ml-enrichment/lib/enrichment/skills/unified_extractor.py
- [X] T029 [US1] Implement get_model_config() singleton loader in services/ml-enrichment/lib/config/model_config.py
- [X] T030 [US1] Add enrichment_version field to enrichment storage in services/ml-enrichment/lib/utils/enrichment_utils.py
- [X] T031 [US1] Implement version-based job query function in services/ml-enrichment/lib/utils/enrichment_utils.py
- [X] T032 [US1] Add version tracking to job_enrichments insert operations in services/ml-enrichment/lib/adapters/bigquery/enrichment_adapter.py
- [X] T033 [US1] Create query for jobs needing re-enrichment in services/ml-enrichment/queries/version_queries.sql
- [X] T034 [US1] Update main.py to include version in enrichment response at services/ml-enrichment/main.py
- [X] T035 [US1] Add logging for version tracking operations in services/ml-enrichment/lib/config/model_config.py

**Checkpoint**: User Story 1 should be fully functional - enrichments include version identifiers (SC-001)

---

## Phase 4: User Story 2 - Enhanced Skills Extraction Accuracy (Priority: P1)

**Goal**: Improve skills extraction accuracy through alias resolution, multi-strategy extraction, and confidence scoring.

**Independent Test**: Run extraction on a curated test set of job postings and measure precision/recall metrics against ground truth labels.

### Tests for User Story 2

- [X] T036 [P] [US2] Unit test for AliasExtractionStrategy in services/ml-enrichment/tests/test_alias_extraction.py
- [X] T037 [P] [US2] Integration test for composite extractor in services/ml-enrichment/tests/integration/test_composite_extractor.py
- [X] T038 [P] [US2] Test for confidence scoring in services/ml-enrichment/tests/test_confidence_scoring.py

### Implementation for User Story 2

- [X] T039 [P] [US2] Implement AliasExtractionStrategy class in services/ml-enrichment/lib/config/__init__.py (AliasResolver)
- [X] T040 [US2] Implement alias lookup index builder in services/ml-enrichment/lib/config/__init__.py
- [X] T041 [US2] Extend UnifiedSkillsConfig with alias_config_path in services/ml-enrichment/lib/enrichment/skills/unified_config.py
- [X] T042 [US2] Integrate AliasExtractionStrategy into composite extractor in services/ml-enrichment/lib/enrichment/skills/unified_extractor.py
- [X] T043 [US2] Implement strategy result merging with deduplication in services/ml-enrichment/lib/enrichment/skills/unified_extractor.py
- [X] T044 [US2] Add source_strategies field to skill output in services/ml-enrichment/lib/enrichment/skills/unified_extractor.py
- [X] T045 [US2] Implement enhanced confidence scoring using weighted ensemble in services/ml-enrichment/lib/enrichment/skills/unified_extractor.py
- [X] T046 [US2] Populate skill_aliases.yaml with initial common aliases in services/ml-enrichment/config/skill_aliases.yaml
- [X] T047 [US2] Add alias resolution statistics to extraction response in services/ml-enrichment/main.py

**Checkpoint**: User Story 2 should be fully functional - alias resolution works (SC-003), confidence scores included

---

## Phase 5: User Story 3 - Stable Job Clustering Over Time (Priority: P2)

**Goal**: Implement cluster version tracking to enable historical comparison and trend analysis.

**Independent Test**: Run clustering on a fixed dataset, then run it again on the same dataset plus new jobs, and verify that existing job cluster assignments can be tracked and compared.

### Tests for User Story 3

- [ ] T048 [P] [US3] Unit test for cluster version tracking in services/ml-enrichment/tests/test_cluster_versioning.py
- [ ] T049 [P] [US3] Integration test for cluster stability metrics in services/ml-enrichment/tests/integration/test_cluster_stability.py

### Implementation for User Story 3

- [ ] T050 [US3] Extend JobClusterer with cluster_run_id generation in services/ml-enrichment/lib/enrichment/job_clusterer.py
- [ ] T051 [US3] Add cluster_model_id and cluster_version fields to clustering output in services/ml-enrichment/lib/enrichment/job_clusterer.py
- [ ] T052 [US3] Implement is_active flag management for cluster assignments in services/ml-enrichment/lib/enrichment/job_clusterer.py
- [ ] T053 [US3] Add cluster version filtering queries in services/ml-enrichment/queries/clustering_queries.sql
- [ ] T054 [US3] Implement cluster stability metrics calculation in services/ml-enrichment/lib/enrichment/job_clusterer.py
- [ ] T055 [US3] Add cluster_run_id to clustering response in services/ml-enrichment/main.py
- [ ] T056 [US3] Update BigQuery adapter for cluster version storage in services/ml-enrichment/lib/adapters/bigquery/cluster_adapter.py

**Checkpoint**: User Story 3 should be fully functional - cluster assignments include version tracking (SC-005)

---

## Phase 6: User Story 4 - ML Performance Monitoring and Evaluation (Priority: P2)

**Goal**: Evaluate ML model performance against labeled test data and track metrics over time.

**Independent Test**: Provide a labeled evaluation dataset and verify that the system produces accuracy, precision, recall, and F1 metrics per skill category.

### Tests for User Story 4

- [ ] T057 [P] [US4] Unit test for SkillsEvaluator in services/ml-enrichment/tests/test_evaluation.py
- [ ] T058 [P] [US4] Test for metrics calculation in services/ml-enrichment/tests/test_metrics.py
- [ ] T059 [P] [US4] Integration test for evaluation API in services/ml-enrichment/tests/integration/test_evaluation_api.py

### Implementation for User Story 4

- [X] T060 [P] [US4] Implement metrics calculation module in services/ml-enrichment/lib/evaluation/evaluator.py
- [X] T061 [US4] Implement SkillsEvaluator class in services/ml-enrichment/lib/evaluation/evaluator.py
- [X] T062 [US4] Implement evaluation dataset loader (JSONL format) in services/ml-enrichment/lib/evaluation/evaluator.py
- [X] T063 [US4] Implement per-category metrics breakdown in services/ml-enrichment/lib/evaluation/evaluator.py
- [ ] T064 [US4] Add evaluation result storage via BigQueryEvaluationRepository in services/ml-enrichment/lib/evaluation/evaluator.py
- [X] T065 [US4] Create evaluate_ci.py CI/CD script in services/ml-enrichment/scripts/evaluate_ci.py
- [X] T066 [US4] Add threshold checking and exit code logic to evaluate_ci.py in services/ml-enrichment/scripts/evaluate_ci.py
- [ ] T067 [US4] Add evaluation queries to retrieve historical results in services/ml-enrichment/queries/evaluation_queries.sql
- [ ] T068 [US4] Add /evaluate endpoint to main.py at services/ml-enrichment/main.py
- [ ] T069 [US4] Add /evaluate/quick endpoint for CI in services/ml-enrichment/main.py
- [ ] T070 [US4] Add /evaluate/results endpoint for historical data in services/ml-enrichment/main.py
- [ ] T071 [US4] Update cloudbuild.yaml to include evaluation step (optional) in services/ml-enrichment/cloudbuild.yaml

**Checkpoint**: User Story 4 should be fully functional - evaluation produces metrics (SC-006, SC-007)

---

## Phase 7: User Story 5 - Section-Aware Skills Extraction (Priority: P3)

**Goal**: Improve extraction precision by classifying job posting sections and weighting skills from relevant sections higher.

**Independent Test**: Compare extraction results on jobs with clear section headers before and after section classification is enabled.

### Tests for User Story 5

- [ ] T072 [P] [US5] Unit test for SectionClassifier in services/ml-enrichment/tests/test_section_classifier.py
- [ ] T073 [P] [US5] Integration test for section-aware extraction in services/ml-enrichment/tests/integration/test_section_extraction.py

### Implementation for User Story 5

- [X] T074 [US5] Implement rule-based SectionClassifier in services/ml-enrichment/lib/enrichment/section_classifier.py
- [X] T075 [US5] Define RELEVANT_SECTIONS and EXCLUDED_SECTIONS patterns in services/ml-enrichment/lib/enrichment/section_classifier.py
- [ ] T076 [US5] Add section_relevance_score to ExtractedSkill output in services/ml-enrichment/lib/enrichment/skills/unified_extractor.py
- [ ] T077 [US5] Integrate SectionClassifier with UnifiedSkillsExtractor in services/ml-enrichment/lib/enrichment/skills/unified_extractor.py
- [ ] T078 [US5] Implement confidence weighting based on section relevance in services/ml-enrichment/lib/enrichment/skills/unified_extractor.py
- [X] T079 [US5] Add section classification storage in services/ml-enrichment/lib/adapters/bigquery/section_classification_adapter.py
- [ ] T080 [US5] Add section_classification to enrichment_types in main.py at services/ml-enrichment/main.py
- [ ] T081 [US5] Create placeholder for ML classifier training from annotation exports in services/ml-enrichment/lib/enrichment/skills/section_classifier.py

**Checkpoint**: User Story 5 should be fully functional - section classification improves extraction (SC-004)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T082 [P] Update services/ml-enrichment/README.md with new features documentation
- [ ] T083 [P] Add environment variable documentation to README
- [ ] T084 [P] Update quickstart.md with new usage examples at specs/001-ml-quality-lifecycle/quickstart.md
- [ ] T085 Code cleanup and consolidate imports across modules
- [ ] T086 Performance optimization: ensure <10% processing time increase (SC-008)
- [ ] T087 [P] Add comprehensive logging for debugging and monitoring
- [ ] T088 Security review: validate no sensitive data in logs
- [ ] T089 Run quickstart.md validation - verify all code examples work
- [ ] T090 Validate all BigQuery schemas are idempotent (IF NOT EXISTS pattern)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 - can proceed in parallel (if staffed)
  - US3 and US4 are both P2 - can proceed after P1 stories or in parallel with them
  - US5 is P3 - can proceed after P2 stories or in parallel
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational - No dependencies on other stories
- **User Story 4 (P2)**: Can start after Foundational - Uses entities from US1 for version tracking in results
- **User Story 5 (P3)**: Can start after Foundational - Integrates with US2 extraction pipeline

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Entities/models before services
- Services before adapters
- Core implementation before API endpoints
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, user stories can start based on priority
- All tests for a user story marked [P] can run in parallel
- All entity implementations marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task: T036 "Unit test for AliasExtractionStrategy in services/ml-enrichment/tests/test_alias_extraction.py"
Task: T037 "Integration test for composite extractor in services/ml-enrichment/tests/integration/test_composite_extractor.py"
Task: T038 "Test for confidence scoring in services/ml-enrichment/tests/test_confidence_scoring.py"

# Then implement:
Task: T039 "Implement AliasExtractionStrategy class" (can start immediately)
```

---

## Parallel Example: Foundational Phase

```bash
# All schema tasks in parallel:
Task: T007 "Create skill_aliases_schema.sql"
Task: T008 "Create evaluation_results_schema.sql"
Task: T009 "Create section_classifications_schema.sql"

# All entity tasks in parallel:
Task: T011 "Implement SkillAlias entity"
Task: T012 "Implement ExtractedSkill entity"
Task: T013 "Implement SectionClassification entity"
Task: T014 "Implement ClusterAssignment entity"
Task: T015 "Implement EvaluationResult entity"

# All repository interfaces in parallel:
Task: T018 "Define SkillAliasRepository interface"
Task: T019 "Define EvaluationResultRepository interface"
Task: T020 "Define SectionClassificationRepository interface"

# All adapter implementations in parallel:
Task: T022 "Implement BigQuerySkillAliasRepository"
Task: T023 "Implement BigQueryEvaluationRepository"
Task: T024 "Implement BigQuerySectionClassificationRepository"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Model Version Management)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready - all enrichments now have version tracking (SC-001)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (SC-002, SC-003)
4. Add User Story 3 → Test independently → Deploy/Demo (SC-005)
5. Add User Story 4 → Test independently → Deploy/Demo (SC-006, SC-007)
6. Add User Story 5 → Test independently → Deploy/Demo (SC-004)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1 - version tracking)
   - Developer B: User Story 2 (P1 - skills extraction)
3. After P1 stories:
   - Developer A: User Story 3 (P2 - clustering)
   - Developer B: User Story 4 (P2 - evaluation)
4. Finally:
   - Developer A or B: User Story 5 (P3 - section classification)
5. Stories complete and integrate independently

---

## Summary

| Phase | Tasks | Parallel Tasks | Stories |
|-------|-------|----------------|---------|
| Phase 1: Setup | 5 | 3 | - |
| Phase 2: Foundational | 20 | 14 | - |
| Phase 3: User Story 1 | 10 | 2 | US1 (P1) |
| Phase 4: User Story 2 | 12 | 4 | US2 (P1) |
| Phase 5: User Story 3 | 9 | 2 | US3 (P2) |
| Phase 6: User Story 4 | 15 | 4 | US4 (P2) |
| Phase 7: User Story 5 | 10 | 2 | US5 (P3) |
| Phase 8: Polish | 9 | 4 | - |
| **Total** | **90** | **35** | **5** |

### MVP Scope (Recommended)

- **Phase 1 + 2 + 3**: 35 tasks for User Story 1 (Model Version Management)
- Delivers: 100% of enrichments have version identifiers (SC-001)
- Foundation: Ready for all remaining stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
