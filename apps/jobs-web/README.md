# Jobs Web Application

Next.js frontend for viewing and editing job skills with ML enrichment.

## Features

- Browse jobs with advanced filtering (location, skills, clusters, dates)
- Multi-select jobs for ML report generation
- View job details with highlighted skills
- Edit skill metadata (general/specialised/transferrable)
- Select text in job descriptions to add new skills
- Skills feed back to ML model lexicon (reinforcement learning)

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://localhost:8080  # API endpoint
```

## Architecture

Hexagonal architecture:
- UI Layer: Next.js components (presentation)
- API Client: Axios calls to FastAPI backend
- Domain Logic: Lives in api/jobs-api (FastAPI)
- Data: BigQuery via adapters

## Deployment

```bash
# Build and deploy to Cloud Run
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_API_URL=https://jobs-api-e3b7ctuuxa-ts.a.run.app
```

## Key Components

- `app/page.tsx` - Jobs list with filters and multi-select
- `app/jobs/[id]/page.tsx` - Job detail with skill highlighting and editing
- `app/globals.css` - Skill highlighting styles (color-coded by type)
