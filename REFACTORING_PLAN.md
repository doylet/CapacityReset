# Repository Refactoring Plan

## Current Structure
```
CapacityReset/
├── main.py                          # Cloud Run service entry point
├── lib/
│   ├── clients/
│   │   ├── brightdata_client.py
│   │   └── bigquery_client.py
│   └── gcloud_env_client.py
├── Dockerfile
├── cloudbuild.yaml
└── requirements.txt
```

## Proposed Monorepo Structure
```
CapacityReset/
├── services/
│   ├── linkedin-scraper/           # Cloud Run service
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── cloudbuild.yaml
│   │   └── lib/
│   │       ├── clients/
│   │       │   ├── brightdata_client.py
│   │       │   └── bigquery_client.py
│   │       └── gcloud_env_client.py
│   │
│   └── brightdata-etl/             # Future: ETL Cloud Function/Run
│       ├── main.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── cloudbuild.yaml
│
├── shared/                          # Shared utilities across services
│   ├── __init__.py
│   ├── bigquery_utils.py           # Common BigQuery operations
│   └── gcloud_config.py            # Shared GCP configuration
│
├── sql/                             # SQL scripts and schemas
│   ├── schemas/
│   │   ├── scrape_requests.sql
│   │   └── job_postings.sql
│   └── transforms/
│       └── brightdata_transform_upsert.sql
│
├── docs/                            # Documentation
│   ├── architecture.md
│   └── deployment.md
│
└── README.md
```

## Migration Strategy (Minimal Breaking Changes)

### Phase 1: Reorganize (No Breaking Changes)
1. Create `services/linkedin-scraper/` directory
2. Move current files into it:
   - `main.py` → `services/linkedin-scraper/main.py`
   - `lib/` → `services/linkedin-scraper/lib/`
   - `Dockerfile` → `services/linkedin-scraper/Dockerfile`
   - `requirements.txt` → `services/linkedin-scraper/requirements.txt`
   - `cloudbuild.yaml` → `services/linkedin-scraper/cloudbuild.yaml`
3. Create `sql/` directory and move BigQuery files
4. Update Cloud Build trigger to point to new path

### Phase 2: Extract Shared Code
1. Create `shared/` directory
2. Move common utilities that will be reused:
   - `gcloud_env_client.py` → `shared/gcloud_config.py`
   - BigQuery helpers → `shared/bigquery_utils.py`
3. Update imports in linkedin-scraper service

### Phase 3: Add New Services
1. Create `services/brightdata-etl/` for transformation pipeline
2. Each service is self-contained with its own:
   - Dependencies (requirements.txt)
   - Build configuration (cloudbuild.yaml)
   - Dockerfile
3. Services can import from `shared/` for common utilities

## Benefits of This Approach

✅ **Minimal Breaking Changes**: 
   - Update Cloud Build trigger path once
   - No changes to deployed service behavior
   - Imports remain mostly the same

✅ **Clear Boundaries**:
   - Each service is independent
   - Easy to understand what each component does
   - Can deploy services separately

✅ **Shared Code**:
   - Common utilities in one place
   - No code duplication
   - Easier maintenance

✅ **Single Repo**:
   - One git history
   - Easier to manage dependencies
   - Simpler CI/CD
   - Better for small teams

## Alternative: Separate Repos (More Breaking Changes)

If you later decide you need separate repos:
```
doylet/capacityreset-linkedin-scraper
doylet/capacityreset-brightdata-etl
doylet/capacityreset-shared-utils    # Shared as a package
```

**Downsides**:
- More complex dependency management
- Need to version and publish shared package
- Multiple CI/CD pipelines
- Cross-repo changes are harder

## Recommendation

Start with **monorepo** structure. It's simpler, requires minimal changes, and you can always split into separate repos later if needed. For your use case (2-3 services, single team), a monorepo is the pragmatic choice.

## Implementation Steps

1. Create new directory structure
2. Move files (use `git mv` to preserve history)
3. Update Cloud Build trigger:
   - Change `includedFiles` to `services/linkedin-scraper/**`
   - Update `dir` in cloudbuild.yaml steps
4. Test deployment
5. Update documentation

**Estimated time**: 30 minutes
**Risk**: Low (all changes are organizational)
