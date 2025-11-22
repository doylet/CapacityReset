# Separate Cloud Build & Images Strategy

## Problem
Monorepo with multiple services needs:
- Separate Docker images per service
- Separate Cloud Build triggers
- Only build/deploy when specific service changes

## Solution: Service-Specific Builds

### Directory Structure
```
CapacityReset/
├── services/
│   ├── linkedin-scraper/
│   │   ├── cloudbuild.yaml         # ← Service-specific build
│   │   ├── Dockerfile
│   │   └── ...
│   └── brightdata-etl/
│       ├── cloudbuild.yaml         # ← Service-specific build
│       ├── Dockerfile
│       └── ...
```

### Each Service Gets:

**1. Own Cloud Build Trigger**
```
Trigger: linkedin-scraper-trigger
- Included files: services/linkedin-scraper/**
- Cloud Build config: services/linkedin-scraper/cloudbuild.yaml
- Branch: main
```

**2. Own Docker Image**
```
Image: australia-southeast1-docker.pkg.dev/PROJECT/cloud-run-source-deploy/linkedin-scraper
Tags: 
  - :$COMMIT_SHA
  - :latest
```

**3. Own Cloud Run Service**
```
Service: linkedin-scraper
Image: .../linkedin-scraper:$COMMIT_SHA
```

## Implementation

### 1. Service-Specific cloudbuild.yaml

**services/linkedin-scraper/cloudbuild.yaml**:
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '--no-cache'
      - '-t'
      - 'australia-southeast1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/linkedin-scraper:$COMMIT_SHA'
      - '-t'
      - 'australia-southeast1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/linkedin-scraper:latest'
      - '.'
    dir: 'services/linkedin-scraper'  # ← Build from service directory

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - 'australia-southeast1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/linkedin-scraper'

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'linkedin-scraper'
      - '--image'
      - 'australia-southeast1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/linkedin-scraper:$COMMIT_SHA'
      - '--region'
      - 'australia-southeast1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'

images:
  - 'australia-southeast1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/linkedin-scraper'
```

**services/brightdata-etl/cloudbuild.yaml**:
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '--no-cache'
      - '-t'
      - 'australia-southeast1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/brightdata-etl:$COMMIT_SHA'
      - '-t'
      - 'australia-southeast1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/brightdata-etl:latest'
      - '.'
    dir: 'services/brightdata-etl'  # ← Different service directory

  # ... same pattern but with brightdata-etl names
```

### 2. Update Cloud Build Trigger

**Current trigger** references root cloudbuild.yaml.

**Update it** to:
```bash
gcloud builds triggers update d431faf0-8fe4-47ba-bfa5-0adcdf8de7c1 \
  --build-config=services/linkedin-scraper/cloudbuild.yaml \
  --included-files='services/linkedin-scraper/**'
```

This means:
- ✅ Only triggers when `services/linkedin-scraper/` files change
- ✅ Uses service-specific build config
- ✅ Builds only that service's image

### 3. Create Additional Triggers

For each new service:
```bash
gcloud builds triggers create github \
  --name=brightdata-etl-trigger \
  --repo-name=CapacityReset \
  --repo-owner=doylet \
  --branch-pattern=main \
  --build-config=services/brightdata-etl/cloudbuild.yaml \
  --included-files='services/brightdata-etl/**'
```

### 4. Shared Code Handling

If you change `shared/` code, you may want ALL services to rebuild:

**Option A: Add shared/ to included-files**
```bash
--included-files='services/linkedin-scraper/**,shared/**'
```

**Option B: Manual trigger**
- Push changes, manually trigger all service builds

**Option C: Root build file** (more complex)
- Root cloudbuild.yaml that builds all services when shared/ changes

## Result

Each service is **completely independent**:

| Service | Trigger | Image | Cloud Run Service |
|---------|---------|-------|-------------------|
| LinkedIn Scraper | `linkedin-scraper-trigger` | `.../linkedin-scraper:SHA` | `linkedin-scraper` |
| BrightData ETL | `brightdata-etl-trigger` | `.../brightdata-etl:SHA` | `brightdata-etl` |

Changes to `services/linkedin-scraper/` only rebuild/deploy that service.
Changes to `services/brightdata-etl/` only rebuild/deploy that service.

## Migration Steps

1. **Create service directory**:
   ```bash
   mkdir -p services/linkedin-scraper
   git mv main.py lib Dockerfile requirements.txt cloudbuild.yaml services/linkedin-scraper/
   ```

2. **Update image names in cloudbuild.yaml**:
   - Change `capacityreset/post-linkedin-jobs-brightdata-webscraper` → `linkedin-scraper`
   - Add `dir: 'services/linkedin-scraper'` to docker build step

3. **Update trigger**:
   ```bash
   gcloud builds triggers update d431faf0-8fe4-47ba-bfa5-0adcdf8de7c1 \
     --build-config=services/linkedin-scraper/cloudbuild.yaml \
     --included-files='services/linkedin-scraper/**'
   ```

4. **Rename Cloud Run service** (optional, or keep old name):
   ```bash
   # Deploy to new service name
   gcloud run deploy linkedin-scraper --image=... --region=australia-southeast1
   
   # Update Cloud Scheduler to point to new service
   # Delete old service when ready
   ```

5. **Test deployment**

6. **Repeat for new services**

This keeps everything clean and separated while staying in one repo.
