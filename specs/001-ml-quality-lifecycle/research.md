# Research: ML Quality & Lifecycle Improvements

**Feature**: 001-ml-quality-lifecycle  
**Phase**: 0 - Research  
**Date**: 2025-12-03

## Overview

This document captures technical research findings and decisions for the ML Quality & Lifecycle Improvements feature. All NEEDS CLARIFICATION items from the Technical Context have been resolved.

---

## 1. Model Version Identifier Format

### Decision
Use format: `{model_type}_v{major}.{minor}[-{suffix}]`

### Examples
- `skills_extractor_v4.0-unified-config-enhanced`
- `skills_extractor_v4.0-unified-config-legacy`
- `job_clusterer_v1.0-kmeans-tfidf`
- `embeddings_generator_v1.0-vertex-ai`
- `section_classifier_v1.0-bert`

### Rationale
- **Semantic versioning** enables clear upgrade paths (major = breaking, minor = features)
- **Suffix** distinguishes operational modes (enhanced/legacy) and algorithms (kmeans/dbscan)
- **Consistent with existing** `UnifiedSkillsConfig.version` pattern: `"v4.0-unified-config"`

### Alternatives Considered
1. **UUID-based** - Rejected: Not human-readable, hard to compare
2. **Timestamp-based** - Rejected: Doesn't convey compatibility information
3. **Git commit hash** - Rejected: Requires git context, not deployment-independent

---

## 2. Model Configuration Storage

### Decision
Store model configuration in **Python dataclasses** with optional **YAML override files**.

### Implementation
```python
# lib/config/model_config.py
@dataclass
class ModelConfig:
    model_id: str
    version: str
    created_at: datetime
    training_data_version: Optional[str] = None
    performance_metrics: Optional[Dict[str, float]] = None
    config_overrides: Optional[Dict[str, Any]] = None
```

### Configuration Files
```
services/ml-enrichment/config/
├── model_versions.yaml      # Version registry
└── skill_aliases.yaml       # Alias mappings
```

### Rationale
- **Dataclasses** provide type safety and IDE support
- **YAML files** enable runtime configuration without code changes
- **Follows existing pattern** in `UnifiedSkillsConfig` 
- **No HEREDOCs** - Constitution Principle VIII compliance

### Alternatives Considered
1. **BigQuery table for config** - Rejected: Adds latency, config rarely changes
2. **Environment variables** - Rejected: Hard to manage complex structures
3. **Firestore** - Rejected: Constitution prefers BigQuery for state

---

## 3. Enrichment Version Tracking Schema

### Decision
Extend `job_enrichments` table with explicit version columns.

### Schema Extension
```sql
ALTER TABLE `brightdata_jobs.job_enrichments`
ADD COLUMN IF NOT EXISTS model_id STRING,
ADD COLUMN IF NOT EXISTS model_version STRING,
ADD COLUMN IF NOT EXISTS enrichment_version STRING;
```

### Migration Strategy
- **Backward compatible**: New columns are nullable
- **Legacy tagging**: Existing rows get `enrichment_version = 'legacy'`
- **Idempotent script**: Uses `IF NOT EXISTS` pattern

### Rationale
- **Minimal schema change** - adds columns, doesn't break existing queries
- **Queryable** - enables filtering by version directly in SQL
- **Audit trail** - preserves original enrichment metadata

### Alternatives Considered
1. **Separate version table** - Rejected: Adds JOIN complexity
2. **JSON metadata column** - Rejected: Hard to query/filter
3. **New enrichment table** - Rejected: Breaks existing consumers

---

## 4. Skill Alias Resolution Strategy

### Decision
Use **configurable YAML mapping** with **runtime alias lookup**.

### Alias Format
```yaml
# config/skill_aliases.yaml
aliases:
  - alias: "K8s"
    canonical: "Kubernetes"
    category: "devops_tools"
  - alias: "GCP"
    canonical: "Google Cloud Platform"
    category: "cloud_platforms"
  - alias: "AWS"
    canonical: "Amazon Web Services"
    category: "cloud_platforms"
  - alias: "JS"
    canonical: "JavaScript"
    category: "programming_languages"
  - alias: "TS"
    canonical: "TypeScript"
    category: "programming_languages"
```

### Implementation Pattern
```python
class AliasExtractionStrategy:
    def __init__(self, alias_config_path: str):
        self.aliases = load_yaml(alias_config_path)
        self._build_lookup_index()
    
    def resolve(self, skill_text: str) -> Optional[str]:
        return self.alias_lookup.get(skill_text.lower())
```

### Rationale
- **Maintainable** - Non-technical users can update YAML
- **Fast** - O(1) lookup after initial index build
- **Extensible** - Easy to add new aliases without code changes
- **Follows existing pattern** - Similar to `UnifiedSkillsConfig` lexicons

### Alternatives Considered
1. **BigQuery lookup table** - Rejected: Adds latency per extraction
2. **Hardcoded in Python** - Rejected: Requires deploy for changes
3. **ML-based alias detection** - Rejected: Overkill for known mappings

---

## 5. Confidence Score Calculation

### Decision
Use **weighted ensemble scoring** with multiple signals.

### Scoring Components
| Signal | Weight | Description |
|--------|--------|-------------|
| extraction_method | 0.25 | Base confidence from extraction strategy |
| context_strength | 0.20 | Presence of "required", "experience with", etc. |
| frequency | 0.15 | How often skill appears in text |
| category_relevance | 0.15 | Weight based on skill category |
| position_importance | 0.10 | Earlier mentions weighted higher |
| text_quality | 0.10 | Context length indicates reliability |
| skill_specificity | 0.05 | Longer skill names more specific |

### Formula
```python
final_score = sum(weight * score for signal, weight in weights.items())
confidence = min(max(final_score, 0.0), 1.0)
```

### Rationale
- **Already implemented** in `UnifiedSkillsExtractor._calculate_ml_confidence()`
- **Configurable** via `MLConfig.ensemble_weights`
- **Explainable** - each component contributes measurably

### Alternatives Considered
1. **Neural network scorer** - Rejected: Adds cold start latency
2. **Simple average** - Rejected: Doesn't weight important signals
3. **Rule-based thresholds** - Rejected: Less nuanced

---

## 6. Section Classification Approach

### Decision
Use **rule-based section detection** initially, with **ML classifier** as enhancement.

### Phase 1: Rule-Based (Immediate)
```python
RELEVANT_SECTIONS = [
    'responsibilities', 'requirements', 'qualifications',
    'skills', 'experience', 'technical requirements'
]
EXCLUDED_SECTIONS = [
    'benefits', 'compensation', 'about us', 'company culture'
]
```

### Phase 2: ML Classifier (After Annotation Data)
- Train on annotation tool exports
- Binary classification: skills-relevant vs not
- Model: Fine-tuned BERT or simple logistic regression

### Rationale
- **Already partially implemented** in `SectionFilter` class
- **Incremental approach** - rule-based works now, ML improves later
- **Constitution VI** - Human-in-the-loop via annotation tool

### Alternatives Considered
1. **ML-only from start** - Rejected: No training data yet
2. **No section filtering** - Rejected: Reduces precision
3. **Third-party API** - Rejected: Adds latency and cost

---

## 7. Cluster Version Tracking

### Decision
Extend `job_clusters` table with **run identifier** and **version fields**.

### Schema Extension
```sql
ALTER TABLE `brightdata_jobs.job_clusters`
ADD COLUMN IF NOT EXISTS cluster_run_id STRING,
ADD COLUMN IF NOT EXISTS cluster_model_id STRING,
ADD COLUMN IF NOT EXISTS cluster_version INT64 DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_active BOOL DEFAULT TRUE;
```

### Version Management
- `cluster_run_id`: UUID for each clustering execution
- `cluster_version`: Monotonically increasing per job
- `is_active`: Only latest version is active

### Rationale
- **Enables historical comparison** - track cluster stability
- **Soft delete** - old versions retained for analysis
- **Query performance** - `is_active` index for common queries

### Alternatives Considered
1. **Overwrite clusters each run** - Rejected: Loses history
2. **Separate history table** - Rejected: Adds JOIN complexity
3. **Version in enrichment_id only** - Rejected: Hard to query

---

## 8. Evaluation Metrics Implementation

### Decision
Use **scikit-learn metrics** with **custom per-category breakdown**.

### Metrics Calculated
- Precision (per-category and overall)
- Recall (per-category and overall)
- F1 Score (per-category and overall)
- Support (sample count per category)

### Implementation
```python
from sklearn.metrics import precision_recall_fscore_support

def evaluate_skills(predicted: List[Set[str]], 
                    actual: List[Set[str]]) -> Dict[str, float]:
    # Convert to multi-label binary format
    # Calculate per-category metrics
    # Return structured results
```

### Storage Schema
```sql
CREATE TABLE evaluation_results (
    evaluation_id STRING,
    model_id STRING,
    evaluation_date TIMESTAMP,
    dataset_version STRING,
    overall_precision FLOAT64,
    overall_recall FLOAT64,
    overall_f1 FLOAT64,
    category_metrics JSON,
    sample_count INT64
);
```

### Rationale
- **Standard metrics** - widely understood
- **Category breakdown** - identifies weak areas
- **scikit-learn** - already in dependencies

### Alternatives Considered
1. **Custom metric implementation** - Rejected: Reinventing wheel
2. **MLflow tracking** - Rejected: Adds infrastructure
3. **Simple accuracy only** - Rejected: Insufficient for multi-label

---

## 9. CI/CD Evaluation Integration

### Decision
Create **lightweight evaluation script** that runs in CI pipeline.

### Implementation
```python
# scripts/evaluate_ci.py
def main():
    # Load test dataset from GCS
    test_data = load_test_data('gs://bucket/eval_data.jsonl')
    
    # Run extraction
    extractor = get_skills_extractor()
    predictions = [extractor.extract_skills(d['text']) for d in test_data]
    
    # Calculate metrics
    metrics = evaluate_skills(predictions, [d['labels'] for d in test_data])
    
    # Check thresholds
    if metrics['f1'] < THRESHOLD:
        sys.exit(1)  # Fail build
```

### Cloud Build Integration
```yaml
steps:
  - name: 'python:3.11'
    entrypoint: 'python'
    args: ['scripts/evaluate_ci.py']
    env:
      - 'EVAL_THRESHOLD=0.7'
```

### Rationale
- **Fast execution** - small test set (10-50 samples)
- **Gate deployment** - fail build on regression
- **No new infrastructure** - runs in existing Cloud Build

### Alternatives Considered
1. **Full evaluation in CI** - Rejected: Too slow
2. **Manual evaluation only** - Rejected: Regressions slip through
3. **Separate evaluation service** - Rejected: Overkill

---

## 10. Performance Budget

### Decision
Maintain **<10% processing time increase** per job (SC-008).

### Current Baseline
- Skills extraction: ~2-3 seconds per job
- Embeddings: ~1-2 seconds per job
- Clustering: N/A (batch only)

### New Feature Overhead
| Feature | Estimated Overhead | Mitigation |
|---------|-------------------|------------|
| Alias resolution | <50ms | Pre-built O(1) hash lookup index at startup |
| Confidence scoring | <100ms | Already implemented in enhanced mode |
| Section classification | <200ms | Rule-based regex pre-compiled at startup; ML classifier deferred |
| Version tracking | <10ms | Simple string field additions |

### Total Expected: <360ms additional (~10-15% increase)

**Note**: Estimates assume warm container (no cold start). Cold starts add ~500ms due to lazy model loading (Constitution Principle V). Section classification overhead is based on pre-compiled regex patterns matching ~15 relevant sections and ~10 excluded sections per job text.

### Rationale
- **Lazy loading** prevents cold start regression
- **Most features already exist** in enhanced mode
- **Acceptable tradeoff** for quality improvements

---

## Summary of Decisions

| Topic | Decision |
|-------|----------|
| Version format | `{model_type}_v{major}.{minor}[-{suffix}]` |
| Config storage | Python dataclasses + YAML files |
| Schema extension | Add columns to existing tables |
| Alias resolution | YAML config with runtime lookup |
| Confidence scoring | Weighted ensemble (7 signals) |
| Section classification | Rule-based now, ML later |
| Cluster versioning | Run ID + version counter + active flag |
| Evaluation metrics | scikit-learn precision/recall/F1 |
| CI integration | Lightweight script with threshold check |
| Performance | <10% overhead target |

---

## Open Questions (None)

All technical decisions have been made. Implementation can proceed to Phase 1.
