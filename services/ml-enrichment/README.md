# ML Enrichment Service

Enriches LinkedIn job postings with ML-powered features:

## Features

1. **Skills Extraction**
   - Extracts technologies, tools, frameworks, and soft skills
   - Uses spaCy NLP with pattern matching
   - Categorizes skills: programming_language, framework, database, cloud, tool, data_science, soft_skill
   - Confidence scoring based on mention frequency

2. **Vector Embeddings**
   - Generates semantic embeddings for job descriptions
   - Uses Vertex AI `text-embedding-004` model (768 dimensions)
   - Intelligent chunking by sections (responsibilities, requirements, etc.)
   - Enables semantic search and job matching

## Architecture

### Polymorphic Enrichment Tracking
- **job_enrichments**: Tracks all enrichment types with versioning
- **job_skills**: Stores extracted skills with metadata
- **job_embeddings**: Stores vector embeddings with chunks

### Loose Coupling
- `job_postings` table remains independent
- Enrichments reference jobs via `job_posting_id`
- Easy to reprocess with new models using `enrichment_version`

## API

### Endpoint
POST https://ml-enrichment-{hash}.a.run.app

### Request Body
```json
{
  "enrichment_types": ["skills_extraction", "embeddings"],
  "batch_size": 50
}
```

### Response
```json
{
  "status": "success",
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
  "execution_time_seconds": 12.5
}
```

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
