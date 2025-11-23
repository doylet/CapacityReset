# ML Enrichment Service Architecture

## Overview

The ML Enrichment Service provides machine learning capabilities for LinkedIn job postings, including skills extraction, vector embeddings, and job clustering.

## Architecture Principles

1. **Loose Coupling**: Job postings remain independent; enrichments tracked separately in `job_enrichments` table
2. **Polymorphic Design**: One enrichment tracking table supports multiple enrichment types
3. **Separation of Concerns**: Code organized into distinct layers (API, Processing, Data Access, ML Models)
4. **Lazy Loading**: ML models loaded on-demand to optimize cold start performance

## Code Structure

```
services/ml-enrichment/
├── main.py                          # HTTP endpoint & routing (160 lines)
├── lib/
│   ├── utils/
│   │   ├── __init__.py
│   │   └── enrichment_utils.py      # Data access layer (queries, logging, clients)
│   ├── processors/
│   │   ├── __init__.py
│   │   └── enrichment_processors.py # Business logic layer (orchestration, error handling)
│   └── enrichment/
│       ├── __init__.py
│       ├── skills_extractor.py      # Skills extraction with spaCy NLP
│       ├── embeddings_generator.py  # Vector embeddings with Vertex AI
│       └── job_clusterer.py         # Job clustering with K-means/DBSCAN
├── requirements.txt
└── cloudbuild.yaml
```

## Layer Responsibilities

### 1. API Layer (`main.py`)
- **Purpose**: HTTP request handling and routing
- **Responsibilities**:
  - Parse incoming requests
  - Lazy-load ML modules (skills extractor, embeddings generator, clusterer)
  - Route to appropriate processors
  - Return JSON responses
- **Key Functions**:
  - `main(request)`: HTTP Cloud Function entry point
  - `get_skills_extractor()`: Lazy loader for skills extraction
  - `get_embeddings_generator()`: Lazy loader for embeddings
  - `get_job_clusterer()`: Lazy loader for clustering

### 2. Data Access Layer (`lib/utils/enrichment_utils.py`)
- **Purpose**: Database queries and logging
- **Responsibilities**:
  - Query jobs needing enrichment
  - Log enrichment attempts to `job_enrichments` table
  - Provide logger access
  - Initialize BigQuery and Cloud Logging clients
- **Key Functions**:
  - `get_jobs_needing_enrichment(enrichment_type, limit)`: Query unenriched jobs
  - `log_enrichment(job_posting_id, enrichment_type, ...)`: Record enrichment status
  - `get_logger()`: Access Cloud Logging logger

### 3. Business Logic Layer (`lib/processors/enrichment_processors.py`)
- **Purpose**: Orchestrate enrichment workflows
- **Responsibilities**:
  - Process batches of jobs
  - Handle errors gracefully
  - Coordinate between data access and ML modules
  - Track statistics (processed, failed, totals)
- **Key Functions**:
  - `process_skills_extraction(jobs, extractor)`: Extract skills from job descriptions
  - `process_embeddings(jobs, generator)`: Generate vector embeddings
  - `process_clustering(n_clusters, method, clusterer)`: Cluster jobs by similarity

### 4. ML Module Layer (`lib/enrichment/`)
- **Purpose**: Machine learning implementations
- **Responsibilities**:
  - Load and manage ML models
  - Extract features from text
  - Generate embeddings
  - Cluster jobs
  - Store results in BigQuery tables
- **Modules**:
  - `SkillsExtractor`: spaCy NLP + TF-IDF for skill identification
  - `EmbeddingsGenerator`: Vertex AI text-embedding-004 for semantic vectors
  - `JobClusterer`: K-means/DBSCAN clustering with keyword extraction

## Data Flow

```
HTTP Request
    ↓
main.py (parse request)
    ↓
enrichment_utils.get_jobs_needing_enrichment()
    ↓
enrichment_processors.process_*() ← ML Module (lazy loaded)
    ↓
enrichment_utils.log_enrichment()
    ↓
ML Module.store_*() → BigQuery
    ↓
main.py (return response)
```

## Database Schema

### job_enrichments (Polymorphic Tracker)
- `enrichment_id` (UUID, primary key)
- `job_posting_id` (foreign key to job_postings)
- `enrichment_type` (skills_extraction, embeddings, job_clustering)
- `enrichment_version` (model version identifier)
- `status` (success, failed, partial)
- `metadata` (JSON, type-specific details)
- `error_message` (string, if failed)
- `created_at` (timestamp)

### job_skills
- `skill_id` (UUID, primary key)
- `job_posting_id` (foreign key)
- `enrichment_id` (foreign key to job_enrichments)
- `skill_name` (string)
- `skill_category` (programming_language, framework, database, cloud, tool, data_science, soft_skill)
- `confidence_score` (float, 0.0-1.0)
- `context_snippet` (text)
- `created_at` (timestamp)

### job_embeddings
- `embedding_id` (UUID, primary key)
- `job_posting_id` (foreign key)
- `enrichment_id` (foreign key to job_enrichments)
- `chunk_id` (integer)
- `chunk_type` (section name: overview, responsibilities, requirements, benefits, full_text)
- `content` (text)
- `embedding` (ARRAY<FLOAT64>[768])
- `model_version` (text-embedding-004)
- `created_at` (timestamp)

### job_clusters
- `cluster_assignment_id` (UUID, primary key)
- `job_posting_id` (foreign key)
- `enrichment_id` (foreign key to job_enrichments)
- `cluster_id` (integer)
- `cluster_name` (string, generated from keywords)
- `cluster_keywords` (JSON array of {keyword, score})
- `cluster_size` (integer)
- `created_at` (timestamp)

## API Reference

### Endpoint
```
POST https://ml-enrichment-e3b7ctuuxa-ts.a.run.app
```

### Request Body
```json
{
  "enrichment_types": ["skills_extraction", "embeddings", "clustering"],
  "batch_size": 50,
  "n_clusters": 10,
  "clustering_method": "kmeans"
}
```

### Response
```json
{
  "status": "success",
  "execution_time_seconds": 12.5,
  "skills_extraction": {
    "processed": 10,
    "failed": 0,
    "total_skills": 45
  },
  "embeddings": {
    "processed": 10,
    "failed": 0,
    "total_embeddings": 30
  },
  "clustering": {
    "total_jobs": 64,
    "clusters_created": 8,
    "method": "kmeans"
  }
}
```

## Deployment

### Cloud Run Configuration
- **Region**: australia-southeast1
- **Memory**: 1GB (for ML models)
- **CPU**: 1
- **Timeout**: 300s
- **Concurrency**: 1 (for model consistency)

### Automation
- **Scheduler**: `ml-enrichment-scheduler`
- **Frequency**: Daily at 4:15am Sydney time
- **Payload**: `{"enrichment_types": ["skills_extraction", "embeddings"], "batch_size": 100}`

### Build & Deploy
```bash
# Trigger automatic deployment
git push origin main

# Check build status
gcloud builds list --limit=1

# View logs
gcloud builds log <BUILD_ID> --stream

# Manual deploy (if needed)
cd services/ml-enrichment
gcloud builds submit --config cloudbuild.yaml
```

## Performance

### Cold Start
- **Without lazy loading**: ~3-5 seconds (all models load at import)
- **With lazy loading**: ~500ms (models load on first use)

### Processing Speed
- **Skills extraction**: ~1 second per job
- **Embeddings generation**: ~1.5 seconds per job
- **Clustering**: ~4-5 seconds for 37 jobs

### Memory Usage
- **Base service**: ~200MB
- **With spaCy loaded**: ~400MB
- **With Vertex AI loaded**: ~600MB
- **All models loaded**: ~800MB
- **Configured limit**: 1GB (20% headroom)

## Best Practices

### Code Organization
1. Keep `main.py` focused on HTTP routing only
2. Put data access in `lib/utils/`
3. Put business logic in `lib/processors/`
4. Put ML implementations in `lib/enrichment/`

### Error Handling
1. Always log enrichment attempts (success or failure)
2. Use try-except blocks in processors
3. Store error messages in `job_enrichments.error_message`
4. Return partial success (some jobs may fail in a batch)

### Testing
1. Test with small batches first (`batch_size: 2`)
2. Check Cloud Logging for detailed execution logs
3. Query BigQuery tables to verify data storage
4. Monitor memory usage with Cloud Run metrics

### Extending
To add a new enrichment type:

1. **Create ML module**: `lib/enrichment/new_enricher.py`
   - Implement extraction/generation logic
   - Include lazy loading for models
   - Store results in new BigQuery table

2. **Add processor**: Update `lib/processors/enrichment_processors.py`
   - Add `process_new_enrichment(jobs, enricher)` function
   - Include error handling and statistics tracking

3. **Add lazy loader**: Update `main.py`
   - Add global `_new_enricher = None`
   - Add `get_new_enricher()` function

4. **Update main handler**: In `main.py` function
   - Add new enrichment type to request parsing
   - Add processing logic with `if 'new_enrichment' in enrichment_types`

5. **Create table**: Add script in `scripts/`
   - Define schema
   - Create table in BigQuery

6. **Add queries**: Create `queries/new_enrichment_queries.sql`
   - Add example queries for analysis

## Monitoring

### Cloud Logging Queries
```
# View all enrichment logs
resource.type="cloud_run_revision"
resource.labels.service_name="ml-enrichment"

# Filter by enrichment type
jsonPayload.message=~"Skills extraction"
jsonPayload.message=~"Embeddings generation"
jsonPayload.message=~"Job clustering"

# View errors only
severity="ERROR"
```

### BigQuery Queries
See `queries/example_queries.sql` for:
- Skills distribution analysis
- Top skills by category
- Jobs missing enrichments
- Embedding coverage statistics
- Cluster analysis and keywords

## References

- **Skills Extraction**: spaCy NLP library, TF-IDF scoring
- **Vector Embeddings**: Vertex AI text-embedding-004 (768 dimensions)
- **Job Clustering**: scikit-learn K-means and DBSCAN
- **Storage**: Google Cloud BigQuery
- **Logging**: Google Cloud Logging
- **Deployment**: Google Cloud Run, Cloud Build
