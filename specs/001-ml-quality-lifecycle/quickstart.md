# Quickstart: ML Quality & Lifecycle Improvements

**Feature**: 001-ml-quality-lifecycle  
**Phase**: 1 - Design  
**Date**: 2025-12-03

## Overview

This guide helps developers get started with the ML Quality & Lifecycle Improvements feature. It covers local development setup, running the enhanced skills extraction, and working with model versioning.

---

## Prerequisites

### Required Software
- Python 3.11+
- Docker (for local BigQuery emulation or testing)
- Google Cloud SDK (for production deployment)

### Google Cloud Access
- Access to `sylvan-replica-478802-p4` project
- BigQuery read/write permissions on `brightdata_jobs` dataset
- GCS access for model artifacts (if using semantic extraction)

---

## Local Development Setup

### 1. Clone and Navigate

```bash
cd services/ml-enrichment
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

# For enhanced mode (semantic extraction)
pip install sentence-transformers torch
```

### 4. Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 5. Set Environment Variables

```bash
export GOOGLE_CLOUD_PROJECT="sylvan-replica-478802-p4"
export BIGQUERY_DATASET="brightdata_jobs"

# For local testing without GCP
export USE_LOCAL_MODE=true
```

---

## Running Skills Extraction

### Basic Extraction (Local Testing)

```python
from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig

# Initialize extractor
config = UnifiedSkillsConfig()
extractor = UnifiedSkillsExtractor(
    config=config,
    enable_semantic=False,  # Disable for faster local testing
    enable_patterns=True
)

# Extract skills from text
result = extractor.extract_skills(
    job_summary="Senior Python Developer with Kubernetes experience",
    job_description="""
    Requirements:
    - 5+ years Python experience
    - Experience with K8s and Docker
    - Knowledge of AWS or GCP
    - Strong SQL skills
    """,
    job_id="test-job-001"
)

# View results
print(f"Extracted {len(result['skills'])} skills:")
for skill in result['skills']:
    print(f"  - {skill['text']} ({skill['category']}): {skill['confidence']:.2f}")
print(f"\nExtractor version: {extractor.get_version()}")
```

### Expected Output

```
Extracted 6 skills:
  - Python (programming_languages): 0.92
  - Kubernetes (devops_tools): 0.88
  - Docker (devops_tools): 0.85
  - AWS (cloud_platforms): 0.82
  - GCP (cloud_platforms): 0.80
  - SQL (databases): 0.78

Extractor version: v4.0-unified-config-enhanced
```

---

## Working with Skill Aliases

### Using Alias Resolution

Aliases like "K8s", "GCP", "JS" are automatically resolved:

```python
# The text contains "K8s" and "GCP"
result = extractor.extract_skills(
    job_summary="K8s admin needed",
    job_description="Must know GCP and JS",
    job_id="test-002"
)

# Output will show canonical names
# "K8s" → "Kubernetes"
# "GCP" → "Google Cloud Platform"
# "JS" → "JavaScript"
```

### Adding Custom Aliases

Edit `config/skill_aliases.yaml`:

```yaml
aliases:
  # Add new alias
  - alias: "ML"
    canonical: "Machine Learning"
    category: "machine_learning"
    
  - alias: "DL"
    canonical: "Deep Learning"
    category: "machine_learning"
```

---

## Model Version Tracking

### Checking Current Version

```python
from lib.enrichment.skills import UnifiedSkillsExtractor

extractor = UnifiedSkillsExtractor()
print(f"Version: {extractor.get_version()}")
# Output: v4.0-unified-config-enhanced
```

### Querying Enrichments by Version

```sql
-- Find jobs enriched with specific version
SELECT job_posting_id, created_at
FROM `brightdata_jobs.job_enrichments`
WHERE enrichment_type = 'skills_extraction'
  AND enrichment_version = 'v4.0-unified-config-enhanced'
ORDER BY created_at DESC
LIMIT 100;

-- Find jobs needing re-enrichment
SELECT jp.job_posting_id, jp.job_title
FROM `brightdata_jobs.job_postings` jp
LEFT JOIN `brightdata_jobs.job_enrichments` je
  ON jp.job_posting_id = je.job_posting_id
  AND je.enrichment_type = 'skills_extraction'
  AND je.enrichment_version = 'v4.0-unified-config-enhanced'
WHERE je.enrichment_id IS NULL
LIMIT 100;
```

---

## Running Evaluation

### Local Evaluation

```python
from lib.evaluation.evaluator import SkillsEvaluator

# Initialize evaluator
evaluator = SkillsEvaluator(model_id="skills_extractor")

# Run evaluation on test data
results = evaluator.evaluate(
    dataset_path="gs://ml-enrichment-data/eval/test_v1.jsonl",
    sample_limit=100
)

# View results
print(f"Overall F1: {results['overall_f1']:.3f}")
print(f"Precision: {results['overall_precision']:.3f}")
print(f"Recall: {results['overall_recall']:.3f}")

# Per-category breakdown
for category, metrics in results['category_metrics'].items():
    print(f"\n{category}:")
    print(f"  F1: {metrics['f1']:.3f}")
    print(f"  Support: {metrics['support']}")
```

### CI Pipeline Evaluation

```bash
# Run quick evaluation with threshold
python scripts/evaluate_ci.py --threshold 0.75

# Expected output on success:
# ✓ Evaluation passed: F1=0.83 (threshold=0.75)

# Expected output on failure:
# ✗ Evaluation failed: F1=0.72 < threshold=0.75
# Exit code: 1
```

---

## Testing

### Run Unit Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_alias_extraction.py -v

# With coverage
pytest tests/ --cov=lib --cov-report=html
```

### Test Data Format

Evaluation data follows JSONL format:

```json
{"job_id": "test-001", "text": "Python developer needed...", "skills": ["Python", "Django", "PostgreSQL"]}
{"job_id": "test-002", "text": "DevOps engineer with K8s...", "skills": ["Kubernetes", "Docker", "AWS"]}
```

---

## Deployment

### Local Testing with Cloud Run

```bash
# Build container
docker build -t ml-enrichment .

# Run locally
docker run -p 8080:8080 \
  -e GOOGLE_CLOUD_PROJECT=sylvan-replica-478802-p4 \
  ml-enrichment

# Test endpoint
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"enrichment_types": ["skills_extraction"], "batch_size": 10}'
```

### Deploy to Cloud Run

```bash
# Via Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Or direct deploy
gcloud run deploy ml-enrichment \
  --source . \
  --region us-central1 \
  --memory 2Gi \
  --timeout 300s
```

---

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `sylvan-replica-478802-p4` |
| `BIGQUERY_DATASET` | BigQuery dataset | `brightdata_jobs` |
| `USE_LOCAL_MODE` | Skip BigQuery ops | `false` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `ENABLE_SEMANTIC` | Enable semantic extraction | `true` |
| `CONFIDENCE_THRESHOLD` | Min confidence for skills | `0.6` |

### Configuration Files

```
services/ml-enrichment/
├── config/
│   ├── model_versions.yaml    # Model version registry
│   └── skill_aliases.yaml     # Alias mappings
└── lib/enrichment/skills/
    └── unified_config.py      # Python config dataclass
```

---

## Troubleshooting

### Common Issues

**1. "Enhanced ML features not available"**
```
Solution: Install optional dependencies
pip install sentence-transformers torch
```

**2. "Failed to load spaCy model"**
```
Solution: Download the model
python -m spacy download en_core_web_sm
```

**3. "BigQuery permission denied"**
```
Solution: Check GCP authentication
gcloud auth application-default login
```

**4. "Cold start too slow"**
```
Solution: Increase memory allocation
gcloud run services update ml-enrichment --memory 4Gi
```

### Getting Help

- Check logs: `gcloud logging read "resource.type=cloud_run_revision"`
- Contact ML team: ml-enrichment@company.com
- Documentation: See `services/ml-enrichment/README.md`

---

## Next Steps

1. **Explore the API**: See `contracts/` for full OpenAPI specs
2. **Review data model**: See `data-model.md` for entity definitions
3. **Understand architecture**: See `services/ml-enrichment/ARCHITECTURE.md`
4. **Run evaluation**: Create test data and run `evaluate_ci.py`
