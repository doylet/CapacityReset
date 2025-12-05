# ML Enrichment Service

Enriches LinkedIn job postings with ML-powered features:

## Features

1. **Skills Extraction**
   - Extracts technologies, tools, frameworks, and soft skills
   - Uses spaCy NLP with pattern matching and lexicon-based extraction
   - Alias resolution (e.g., K8s → Kubernetes, GCP → Google Cloud Platform)
   - Enhanced confidence scoring with weighted ensemble
   - Categorizes skills: programming_languages, web_frameworks, cloud_platforms, databases, devops_tools, machine_learning, soft_skills
   - Version tracking for model updates

2. **Vector Embeddings**
   - Generates semantic embeddings for job descriptions
   - Uses Vertex AI `text-embedding-004` model (768 dimensions)
   - Intelligent chunking by sections (responsibilities, requirements, etc.)
   - Enables semantic search and job matching

3. **Job Clustering** (New)
   - Clusters similar jobs using K-means or DBSCAN
   - TF-IDF keyword extraction per cluster
   - Cluster version tracking for stability analysis
   - Enables trend analysis and career path discovery

4. **Section Classification** (New)
   - Classifies job posting sections for skills relevance
   - Prioritizes skills from Requirements/Skills sections
   - Rule-based with ML-ready architecture
   - Improves extraction precision

5. **Model Evaluation** (New)
   - Evaluates extraction accuracy against labeled datasets
   - Computes precision, recall, F1 metrics
   - Per-category performance breakdown
   - CI/CD integration with threshold gating

## Architecture

### Polymorphic Enrichment Tracking
- **job_enrichments**: Tracks all enrichment types with versioning
- **job_skills**: Stores extracted skills with metadata
- **job_embeddings**: Stores vector embeddings with chunks
- **job_clusters**: Stores cluster assignments with version tracking

### Version Tracking
- All enrichments include model version
- Supports re-enrichment workflows for model updates
- Version-based queries for analysis

### Loose Coupling
- `job_postings` table remains independent
- Enrichments reference jobs via `job_posting_id`
- Easy to reprocess with new models using `enrichment_version`

## API Endpoints

### Main Enrichment
POST /enrich
```json
{
  "enrichment_types": ["skills_extraction", "embeddings", "clustering"],
  "batch_size": 50,
  "n_clusters": 10,
  "clustering_method": "kmeans"
}
```

Response:
```json
{
  "status": "success",
  "skills_extraction": {
    "processed": 10,
    "failed": 0,
    "total_skills": 45,
    "extractor_version": "v4.0-unified-config-enhanced",
    "alias_resolution": {
      "aliases_loaded": 50,
      "resolver_available": true
    }
  },
  "embeddings": {
    "processed": 10,
    "failed": 0,
    "total_embeddings": 30
  },
  "clustering": {
    "total_jobs": 100,
    "clusters_created": 10,
    "cluster_model_id": "v1.0-kmeans-tfidf",
    "cluster_run_id": "uuid"
  },
  "execution_time_seconds": 12.5
}
```

### Evaluation Endpoints

POST /evaluate
```json
{
  "dataset_path": "gs://bucket/evaluation_data.jsonl",
  "sample_limit": 100,
  "categories": ["programming_languages", "web_frameworks"]
}
```

POST /evaluate_quick (for CI/CD)
```json
{
  "dataset_path": "gs://bucket/eval_small.jsonl",
  "threshold_f1": 0.7,
  "sample_limit": 50,
  "ci_build_id": "build-123"
}
```

GET /evaluate_results
```json
{
  "model_id": "skills_extractor",
  "limit": 20
}
```

### Section Classification

POST /classify_sections
```json
{
  "job_posting_id": "job-123",
  "text": "Full job posting text..."
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_ID` | GCP project ID | sylvan-replica-478802-p4 |
| `DATASET_ID` | BigQuery dataset | brightdata_jobs |
| `LOG_LEVEL` | Logging level | INFO |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account key path | (optional) |

## Deployment

```bash
# Deploy via Cloud Build trigger
gcloud builds triggers run ml-enrichment-trigger

# Or manual deploy
cd services/ml-enrichment
gcloud builds submit --config cloudbuild.yaml
```

## Querying Enrichments

### Find jobs needing enrichment for a version
```sql
SELECT jp.job_posting_id, jp.job_title
FROM `brightdata_jobs.job_postings` jp
LEFT JOIN `brightdata_jobs.job_enrichments` je
  ON jp.job_posting_id = je.job_posting_id
  AND je.enrichment_type = 'skills_extraction'
  AND je.status = 'success'
  AND je.enrichment_version = 'v4.0-unified-config-enhanced'
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

### Cluster stability analysis
```sql
SELECT 
  cluster_run_id,
  cluster_model_id,
  COUNT(DISTINCT job_posting_id) AS jobs_clustered,
  COUNT(DISTINCT cluster_id) AS clusters_created
FROM `brightdata_jobs.job_clusters`
WHERE is_active = TRUE
GROUP BY cluster_run_id, cluster_model_id
ORDER BY MAX(created_at) DESC
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
- `scikit-learn`: Clustering algorithms
- `sentence-transformers`: Semantic similarity (optional)
- `torch`: Enhanced ML features (optional)

## Environment Variables

### Core Configuration
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `BIGQUERY_DATASET`: BigQuery dataset for job data
- `GCS_BUCKET`: Google Cloud Storage bucket for ML artifacts
- `MODEL_VERSION`: Current ML model version (for enrichment tracking)

### LLM Integration (Feature 003)
- `VERTEX_AI_PROJECT_ID`: GCP project ID for Vertex AI (defaults to GOOGLE_CLOUD_PROJECT)
- `VERTEX_AI_LOCATION`: Vertex AI location/region (e.g., 'us-central1')
- `GEMINI_MODEL_NAME`: Gemini model variant ('gemini-flash', 'gemini-pro')
- `LLM_CACHE_TTL`: Cache TTL for LLM responses in seconds (default: 3600)
- `LLM_MAX_RETRIES`: Maximum retry attempts for LLM API calls (default: 3)

## Testing

```bash
# Run all tests
cd services/ml-enrichment
python -m pytest tests/ -v

# Run specific test category
python -m pytest tests/test_alias_extraction.py -v
python -m pytest tests/test_evaluation.py -v
python -m pytest tests/integration/ -v
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run locally
functions-framework --target=enrich --debug
```
