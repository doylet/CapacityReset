# Quickstart: AI Brand Roadmap Integration

**Created**: December 4, 2024  
**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data Model**: [data-model.md](./data-model.md)  
**Phase**: 1 - Design & Contracts (30-90 days)

## Overview

This guide enables developers to integrate AI Brand Roadmap functionality into the existing CapacityReset platform. The feature extends the ml-enrichment service with brand analysis and cross-surface content generation capabilities.

## Prerequisites

- Existing ml-enrichment service running
- BigQuery access with table creation permissions
- Vertex AI enabled with Gemini access
- GCS bucket for document storage
- Python 3.11+ development environment

## Quick Setup (10 minutes)

### 1. Database Schema Setup

Create brand-related BigQuery tables:

```bash
# From repository root
cd services/ml-enrichment
python scripts/create_brand_tables.py
```

**SQL Files**: Use schemas from `data-model.md` or the following files:
- `sql/brand_representations_schema.sql`
- `sql/professional_themes_schema.sql` 
- `sql/professional_surfaces_schema.sql`
- `sql/content_generations_schema.sql`
- `sql/brand_learning_events_schema.sql`

### 2. Install Dependencies

Add to `services/ml-enrichment/requirements.txt`:

```txt
# Brand analysis dependencies
google-generativeai==0.3.0  # Vertex AI Gemini
pypdf2==3.0.1              # PDF document parsing
python-docx==0.8.11        # DOCX document parsing
sentence-transformers==2.2.2  # Semantic similarity
```

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Add to service environment variables:

```bash
# Vertex AI configuration
export VERTEX_AI_PROJECT_ID="your-project-id"
export VERTEX_AI_LOCATION="us-central1"
export BRAND_ANALYSIS_MODEL="gemini-pro"

# GCS configuration  
export BRAND_DOCUMENTS_BUCKET="capacity-reset-brand-docs"

# Performance tuning
export BRAND_GENERATION_TIMEOUT_SECONDS="30"
export BRAND_ANALYSIS_CACHE_TTL_HOURS="24"
```

### 4. Code Integration

**Domain Layer** - Add to `services/ml-enrichment/domain/entities.py`:

```python
@dataclass
class BrandRepresentation:
    brand_id: str
    user_id: str
    source_document_url: str
    professional_themes: List[Dict]
    voice_characteristics: Dict
    narrative_arc: Dict
    confidence_scores: Dict
    linkedin_profile_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: int = 1

@dataclass  
class ContentGeneration:
    generation_id: str
    brand_id: str
    surface_id: str
    content_text: str
    generation_timestamp: datetime
    generation_version: int = 1
    consistency_score: Optional[float] = None
    user_satisfaction_rating: Optional[int] = None
    edit_count: int = 0
    word_count: int = 0
    status: str = 'draft'
```

**Repository Interfaces** - Add to `services/ml-enrichment/domain/repositories.py`:

```python
class BrandRepository(ABC):
    @abstractmethod
    async def save_brand_representation(self, brand: BrandRepresentation) -> str:
        pass
    
    @abstractmethod  
    async def get_brand_by_user(self, user_id: str) -> Optional[BrandRepresentation]:
        pass

class ContentGenerationRepository(ABC):
    @abstractmethod
    async def save_generation(self, generation: ContentGeneration) -> str:
        pass
    
    @abstractmethod
    async def get_generations_by_brand(self, brand_id: str) -> List[ContentGeneration]:
        pass
```

## Development Workflow

### 1. Brand Analysis Development

**Create Brand Analyzer** - `services/ml-enrichment/lib/brand_analyzer.py`:

```python
import spacy
from google.cloud import aiplatform

class BrandAnalyzer:
    def __init__(self):
        self._nlp_model = None
        self._llm_client = None
    
    def get_nlp_model(self):
        if self._nlp_model is None:
            self._nlp_model = spacy.load("en_core_web_lg")
        return self._nlp_model
    
    def get_llm_client(self):
        if self._llm_client is None:
            aiplatform.init(project=os.getenv('VERTEX_AI_PROJECT_ID'))
            self._llm_client = aiplatform.gapic.PredictionServiceClient()
        return self._llm_client
    
    async def analyze_document(self, document_text: str, linkedin_data: Optional[str] = None) -> BrandRepresentation:
        """Extract brand representation from professional document"""
        # Implementation details...
        pass
```

### 2. Content Generation Development

**Create Content Generator** - `services/ml-enrichment/lib/content_generator.py`:

```python
from typing import List, Dict
from domain.entities import BrandRepresentation, ContentGeneration

class ContentGenerator:
    def __init__(self):
        self._generation_templates = self._load_templates()
    
    async def generate_cross_surface_content(
        self, 
        brand: BrandRepresentation, 
        surface_types: List[str]
    ) -> List[ContentGeneration]:
        """Generate consistent content across multiple surfaces"""
        generations = []
        
        for surface_type in surface_types:
            content = await self._generate_surface_content(brand, surface_type)
            generations.append(content)
        
        # Validate consistency across surfaces
        self._validate_consistency(generations)
        
        return generations
    
    def _load_templates(self) -> Dict[str, str]:
        """Load surface-specific generation templates"""
        return {
            'cv_summary': "Professional summary template...",
            'linkedin_summary': "LinkedIn summary template...", 
            'portfolio_intro': "Portfolio introduction template..."
        }
```

### 3. API Integration

**Extend Jobs API** - Add to `api/jobs-api/api/routes.py`:

```python
from fastapi import UploadFile, File

@app.post("/brand/analysis", response_model=BrandAnalysisResponse)
async def analyze_brand(
    document: UploadFile = File(...),
    linkedin_profile_url: Optional[str] = None
):
    # Document upload to GCS
    document_url = await upload_document_to_gcs(document)
    
    # Brand analysis
    brand_analyzer = get_brand_analyzer()
    brand_rep = await brand_analyzer.analyze_document(document_url, linkedin_profile_url)
    
    # Persistence
    brand_repo = get_brand_repository()
    brand_id = await brand_repo.save_brand_representation(brand_rep)
    
    return BrandAnalysisResponse(brand_id=brand_id, brand_overview=brand_rep)

@app.post("/brand/{brand_id}/generate", response_model=ContentGenerationResponse)
async def generate_content(
    brand_id: str, 
    request: ContentGenerationRequest
):
    # Retrieve brand
    brand_repo = get_brand_repository()
    brand = await brand_repo.get_brand_by_id(brand_id)
    
    # Generate content
    content_generator = get_content_generator()
    generations = await content_generator.generate_cross_surface_content(
        brand, request.surface_types
    )
    
    # Persistence
    content_repo = get_content_generation_repository()
    for generation in generations:
        await content_repo.save_generation(generation)
    
    return ContentGenerationResponse(generations=generations)
```

### 4. Frontend Integration

**Brand Management UI** - Create `apps/jobs-web/src/app/brand/page.tsx`:

```typescript
'use client'

import { useState } from 'react'
import { BrandAnalyzer } from '@/components/brand/BrandAnalyzer'
import { ContentGenerator } from '@/components/brand/ContentGenerator'

export default function BrandPage() {
  const [brandId, setBrandId] = useState<string | null>(null)
  
  return (
    <div className="brand-management">
      <h1>AI Brand Roadmap</h1>
      
      {!brandId ? (
        <BrandAnalyzer onBrandCreated={setBrandId} />
      ) : (
        <ContentGenerator brandId={brandId} />
      )}
    </div>
  )
}
```

## Testing Strategy

### 1. Contract Testing

Test repository interfaces with in-memory implementations:

```python
# tests/test_brand_repository.py
import pytest
from domain.repositories import BrandRepository
from adapters.memory_brand_repository import InMemoryBrandRepository

@pytest.fixture
def brand_repo() -> BrandRepository:
    return InMemoryBrandRepository()

async def test_save_and_retrieve_brand(brand_repo):
    # Test brand representation persistence
    brand = BrandRepresentation(...)
    brand_id = await brand_repo.save_brand_representation(brand)
    
    retrieved = await brand_repo.get_brand_by_id(brand_id)
    assert retrieved.brand_id == brand_id
```

### 2. Integration Testing  

Test use cases with test BigQuery datasets:

```python
# tests/test_brand_analysis.py
import pytest
from application.use_cases import BrandAnalysisUseCase

@pytest.mark.integration
async def test_brand_analysis_workflow():
    use_case = BrandAnalysisUseCase(
        brand_repo=get_test_brand_repository(),
        document_processor=get_test_document_processor()
    )
    
    # Test complete workflow
    document_path = "test_cv.pdf"
    brand_id = await use_case.analyze_document(document_path)
    
    assert brand_id is not None
```

### 3. Performance Testing

Validate generation time requirements:

```python
# tests/test_performance.py
import time
import pytest

@pytest.mark.performance
async def test_content_generation_performance():
    start_time = time.time()
    
    # Generate content for 3 surfaces
    generations = await content_generator.generate_cross_surface_content(
        brand, ['cv_summary', 'linkedin_summary', 'portfolio_intro']
    )
    
    elapsed_time = time.time() - start_time
    assert elapsed_time < 30.0  # 30-second requirement
```

## Deployment

### 1. Cloud Build Updates

No changes needed - uses existing `services/ml-enrichment/cloudbuild.yaml`.

### 2. Environment Variables

Update Cloud Run service environment:

```bash
gcloud run services update ml-enrichment \
  --set-env-vars VERTEX_AI_PROJECT_ID=your-project-id,BRAND_DOCUMENTS_BUCKET=capacity-reset-brand-docs
```

### 3. BigQuery Permissions

Ensure service account has BigQuery admin permissions for new tables.

## Monitoring & Observability

### Performance Metrics

- Brand analysis completion time (<5 minutes)
- Content generation time (<30 seconds) 
- Cross-surface consistency scores (>90%)
- User satisfaction ratings

### Error Tracking

- Document parsing failures
- LLM generation timeouts
- Consistency validation failures
- User feedback processing errors

### Logging

```python
import logging
from google.cloud import logging as cloud_logging

# Structured logging for brand events
logger = logging.getLogger(__name__)

await logger.info(
    "Brand analysis completed",
    extra={
        'brand_id': brand_id,
        'analysis_time_ms': elapsed_time,
        'confidence_score': confidence_score,
        'themes_count': len(themes)
    }
)
```

## Next Steps

1. **Phase 0 Validation**: Complete research and requirements clarification
2. **Phase 1 Implementation**: Build core brand analysis and generation services
3. **Phase 2 Learning**: Integrate feedback loops and continuous improvement
4. **Production Deployment**: Full feature rollout with monitoring

## Support & Documentation

- **API Documentation**: [brand-api.yaml](./contracts/brand-api.yaml)
- **Data Model**: [data-model.md](./data-model.md)
- **Architecture**: [plan.md](./plan.md)
- **Research**: [research.md](./research.md)