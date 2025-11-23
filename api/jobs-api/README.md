# Jobs API

FastAPI backend implementing hexagonal architecture for job skills management and ML enrichment.

## Architecture

```
domain/
  entities.py       # Core business objects (Job, Skill, Cluster)
  repositories.py   # Repository ports (interfaces)
  
application/
  use_cases.py      # Business logic orchestration
  
adapters/
  bigquery_repository.py  # BigQuery persistence adapter
  
main.py             # FastAPI REST adapter (HTTP endpoints)
```

## Features

- List jobs with filtering (date, location, cluster, skill)
- Get job details with extracted skills
- Update skill metadata (skill_type: general/specialised/transferrable)
- Add user-defined skills (reinforcement to ML lexicon)
- Generate ML reports for multiple jobs
- View and manage skills lexicon

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload --port 8080

# API docs at http://localhost:8080/docs
```

## Endpoints

```
GET  /jobs                  List jobs with filters
GET  /jobs/{id}             Get job detail
PUT  /jobs/{id}/skills/{id} Update skill type
POST /jobs/{id}/skills      Add skill (reinforcement)
POST /jobs/report           Generate ML report
GET  /lexicon               View skills lexicon
POST /lexicon               Add to lexicon
GET  /clusters              List all clusters
```

## Deployment

```bash
# Build and deploy to Cloud Run
gcloud builds submit --config cloudbuild.yaml
```

## Environment

- Python 3.11
- FastAPI + Uvicorn
- BigQuery client
- Cloud Run (512Mi, 300s timeout)
