# ML Enrichment Service

Enriches LinkedIn job postings with ML-powered features:

## Features

1. **Skills Extraction** (v4.0 - Enhanced)
   - Extracts technologies, tools, frameworks, and soft skills
   - Uses spaCy NLP with pattern matching and lexicon-based extraction
   - **Alias Resolution**: Handles common abbreviations (K8s → Kubernetes, GCP → Google Cloud Platform)
   - **Multi-strategy extraction**: Lexicon, pattern, NER, and noun-chunk extraction
   - Categorizes skills: programming_languages, web_frameworks, databases, cloud_platforms, devops_tools, etc.
   - **Enhanced confidence scoring**: Weighted ensemble with context and frequency analysis
   - **Section-aware extraction**: Prioritizes skills from relevant sections (Requirements, Skills, etc.)
   - Tracks extraction version for re-enrichment workflows

2. **Vector Embeddings**
   - Generates semantic embeddings for job descriptions
   - Uses Vertex AI `text-embedding-004` model (768 dimensions)
   - Intelligent chunking by sections (responsibilities, requirements, etc.)
   - Enables semantic search and job matching

3. **Job Clustering** (v1.0)
   - Clusters jobs by similarity using K-means on embeddings
   - Extracts defining keywords using TF-IDF
   - **Version tracking**: Tracks cluster assignments across runs
   - **Stability metrics**: Measures how stable cluster assignments are over time
   - Supports cluster evolution analysis

4. **Section Classification**
   - Classifies job posting sections for skills relevance
   - Rule-based classification with keyword detection
   - Supports future ML model training from annotations

5. **ML Performance Monitoring**
   - Evaluates extraction quality against labeled datasets
   - Calculates precision, recall, F1 metrics
   - Per-category metric breakdown
   - CI/CD integration with threshold gating

## Architecture

### Polymorphic Enrichment Tracking
- **job_enrichments**: Tracks all enrichment types with versioning
- **job_skills**: Stores extracted skills with metadata
- **job_embeddings**: Stores vector embeddings with chunks
- **job_clusters**: Stores cluster assignments with version tracking
- **evaluation_results**: Stores model evaluation metrics

### Version Tracking
- All enrichments include `enrichment_version` for re-processing
- `model_id` and `model_version` track specific model variants
- Query jobs needing re-enrichment with new model versions

### Loose Coupling
- `job_postings` table remains independent
- Enrichments reference jobs via `job_posting_id`
- Easy to reprocess with new models using `enrichment_version`

## API Endpoints

### Main Enrichment Endpoint
POST https://ml-enrichment-{hash}.a.run.app

#### Request Body
```json
{
  "enrichment_types": ["skills_extraction", "embeddings", "clustering"],
  "batch_size": 50,
  "n_clusters": 10,
  "clustering_method": "kmeans"
}
```

#### Response
```json
{
  "status": "success",
  "skills_extraction": {
    "processed": 10,
    "failed": 0,
    "total_skills": 45,
    "extractor_version": "v4.0-unified-config-enhanced",
    "alias_resolution": {
      "total_lookups": 150,
      "successful_resolutions": 12,
      "resolution_rate": 0.08
    }
  },
  "embeddings": {
    "processed": 10,
    "failed": 0,
    "total_embeddings": 30,
    "generator_version": "v1.0-text-embedding-004"
  },
  "clustering": {
    "total_jobs": 100,
    "clusters_created": 10,
    "method": "kmeans",
    "cluster_run_id": "abc-123-def",
    "cluster_version": 5,
    "stability": 0.85
  },
  "execution_time_seconds": 12.5
}
```

### Evaluation Endpoint
POST /evaluate

#### Request Body
```json
{
  "dataset_path": "gs://bucket/path/to/data.jsonl",
  "sample_limit": 100,
  "categories": ["programming_languages", "cloud_platforms"]
}
```

#### Response
```json
{
  "status": "success",
  "evaluation": {
    "model_id": "skills_extractor",
    "model_version": "v4.0-enhanced",
    "overall_precision": 0.85,
    "overall_recall": 0.90,
    "overall_f1": 0.87,
    "sample_count": 100
  }
}
```

### Quick CI/CD Evaluation
POST /evaluate/quick

#### Request Body
```json
{
  "dataset_path": "gs://bucket/path/to/data.jsonl",
  "threshold": 0.75,
  "sample_limit": 50,
  "ci_build_id": "build-12345"
}
```

#### Response
```json
{
  "status": "success",
  "passed": true,
  "evaluation": {
    "overall_f1": 0.82,
    "threshold": 0.75,
    "threshold_passed": true
  }
}
```
Exit codes: 200 (passed), 417 (failed threshold), 500 (error)

### Historical Results
GET /evaluate/results?model_id=skills_extractor&limit=10

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| GCP_PROJECT | GCP project ID | sylvan-replica-478802-p4 |
| BIGQUERY_DATASET | BigQuery dataset name | brightdata_jobs |
| LOG_LEVEL | Logging level | INFO |
| ENABLE_SEMANTIC | Enable semantic extraction | false |
| ENABLE_PATTERNS | Enable pattern extraction | true |

## Deployment

```bash
# Deploy via Cloud Build trigger
gcloud builds triggers run ml-enrichment-trigger

# Or manual deploy
cd services/ml-enrichment
gcloud builds submit --config cloudbuild.yaml
```

## Querying Enrichments

### Find jobs needing enrichment
```sql
SELECT jp.job_posting_id, jp.job_title
FROM `brightdata_jobs.job_postings` jp
LEFT JOIN `brightdata_jobs.job_enrichments` je
  ON jp.job_posting_id = je.job_posting_id
  AND je.enrichment_type = 'skills_extraction'
  AND je.status = 'success'
  AND je.enrichment_version = 'v4.0-unified-config'
WHERE je.enrichment_id IS NULL
LIMIT 100
```

### Get skills for a job
```sql
SELECT skill_name, skill_category, confidence_score
FROM `brightdata_jobs.job_skills`
WHERE job_posting_id = 'your-job-id'
ORDER BY confidence_score DESC
```

### Get active cluster assignments
```sql
SELECT 
  cluster_id,
  cluster_name,
  COUNT(*) as job_count
FROM `brightdata_jobs.job_clusters`
WHERE is_active = TRUE
GROUP BY cluster_id, cluster_name
ORDER BY job_count DESC
```

### Check cluster stability
```sql
SELECT 
  cluster_run_id,
  cluster_version,
  COUNT(*) as total_jobs
FROM `brightdata_jobs.job_clusters`
GROUP BY cluster_run_id, cluster_version
ORDER BY cluster_version DESC
LIMIT 5
```

### Semantic search
```sql
SELECT 
  jp.job_posting_id,
  jp.job_title,
  jp.company_name,
  VECTOR_SEARCH(
    je.embedding,
    (SELECT embedding FROM `brightdata_jobs.job_embeddings` WHERE job_posting_id = 'reference-job-id' LIMIT 1)
  ) AS similarity_score
FROM `brightdata_jobs.job_postings` jp
JOIN `brightdata_jobs.job_embeddings` je
  ON jp.job_posting_id = je.job_posting_id
WHERE je.chunk_type = 'full_description'
ORDER BY similarity_score DESC
LIMIT 10
```

## Dependencies

- `functions-framework`: HTTP endpoint
- `google-cloud-bigquery`: Data storage
- `google-cloud-aiplatform`: Vertex AI embeddings
- `google-cloud-logging`: Logging
- `spacy`: NLP for skills extraction
- `scikit-learn`: Clustering and TF-IDF
- `pyyaml`: Configuration loading

## Configuration

Configuration files are in the `config/` directory:

- `model_versions.yaml`: Model version registry
- `skill_aliases.yaml`: Skill alias mappings (K8s → Kubernetes, etc.)

## Testing

```bash
# Run unit tests
cd services/ml-enrichment
python -m pytest tests/ -v

# Run integration tests
python -m pytest tests/integration/ -v

# Run evaluation
python -m lib.evaluation.evaluator --dataset data/eval.jsonl --threshold 0.75
```
