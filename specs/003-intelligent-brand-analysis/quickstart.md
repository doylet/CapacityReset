# Intelligent Brand Analysis - Quickstart Guide

This guide provides step-by-step instructions for integrating the LLM-powered brand analysis feature into CapacityReset.

## Overview

The Intelligent Brand Analysis feature uses Vertex AI Gemini to:
- Extract professional themes with evidence citations
- Analyze voice and communication characteristics
- Build career narrative arcs
- Generate platform-specific content (CV, LinkedIn, Portfolio)

## Prerequisites

1. **Google Cloud Project** with Vertex AI API enabled
2. **Service Account** with `roles/aiplatform.user` permission
3. **BigQuery Dataset** for caching LLM responses

## Environment Configuration

Set the following environment variables in your deployment:

```bash
# Required
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_AI_PROJECT_ID=your-project-id  # Falls back to GOOGLE_CLOUD_PROJECT
VERTEX_AI_LOCATION=us-central1         # Or your preferred region

# Optional (with defaults)
GEMINI_MODEL_NAME=gemini-flash         # Model variant
LLM_CACHE_TTL=3600                     # Cache TTL in seconds (1 hour)
LLM_MAX_RETRIES=3                      # Max retry attempts
```

## API Endpoints

### Analyze Document

Upload a CV/resume for brand analysis:

```bash
curl -X POST "https://your-api/brand/analysis" \
  -F "document=@resume.pdf" \
  -F "linkedin_profile_url=https://linkedin.com/in/username"
```

Response:
```json
{
  "brand_id": "uuid",
  "analysis_status": "completed",
  "brand_overview": {
    "professional_themes": [
      {
        "theme_name": "Technical Leadership",
        "confidence_score": 0.92,
        "reasoning": "Multiple evidence of team leadership..."
      }
    ],
    "voice_characteristics": {
      "tone": "professional",
      "formality_level": "formal",
      "energy_level": "balanced"
    },
    "narrative_arc": {
      "career_focus": "...",
      "value_proposition": "..."
    }
  }
}
```

### Generate Content

Generate platform-specific content:

```bash
curl -X POST "https://your-api/brand/{brand_id}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "surface_types": ["cv_summary", "linkedin_summary"],
    "generation_preferences": {
      "target_length": "standard"
    }
  }'
```

### Health Check

Check LLM integration status:

```bash
curl "https://your-api/health"
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "vertex_ai": {"status": "available", "model": "gemini-flash"},
    "bigquery": {"status": "available"}
  },
  "llm_integration": {
    "status": "ready",
    "fallback_enabled": true
  }
}
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│   Frontend      │────▶│   Jobs API       │────▶│  ML Enrichment │
│  (React/Next)   │     │  (FastAPI)       │     │  (Cloud Run)   │
└─────────────────┘     └──────────────────┘     └────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌──────────────┐       ┌───────────────┐
                        │   BigQuery   │       │  Vertex AI    │
                        │   (Cache)    │       │   Gemini      │
                        └──────────────┘       └───────────────┘
```

## Fallback Behavior

The system includes automatic fallback when LLM is unavailable:

1. **Theme Extraction**: Falls back to keyword-based pattern matching
2. **Voice Analysis**: Falls back to heuristic-based analysis
3. **Content Generation**: Falls back to template-based generation

Fallback is indicated in the response metadata:
```json
{
  "analysis_metadata": {
    "fallback_used": true,
    "fallback_reason": "Vertex AI timeout"
  }
}
```

## Caching

LLM responses are cached in BigQuery to reduce costs:

- **Theme Analysis**: 48 hours TTL
- **Voice Analysis**: 72 hours TTL
- **Narrative Analysis**: 168 hours (1 week) TTL

Cache can be invalidated via the API or by content changes.

## Cost Monitoring

Token usage and cost estimates are tracked automatically:

- View session costs via the API call tracker
- Alerts when cost thresholds are exceeded
- Per-operation cost breakdown available

## Troubleshooting

### Vertex AI Not Available

Check:
1. `VERTEX_AI_PROJECT_ID` is set correctly
2. Service account has required permissions
3. Vertex AI API is enabled in the project

### Low Confidence Scores

- Ensure document content is clean text (not scanned PDF)
- Minimum recommended document length: 200 words
- Documents with clear professional structure work best

### Slow Response Times

- First request may be slow due to cold start
- Consider enabling response caching
- Check Vertex AI region for latency optimization

## Development

Run locally with mock LLM:

```bash
cd services/ml-enrichment
pip install -r requirements.txt
export USE_MOCK_LLM=true
functions-framework --target=health --debug
```

Run tests:

```bash
pytest tests/test_brand_analysis.py -v
```
