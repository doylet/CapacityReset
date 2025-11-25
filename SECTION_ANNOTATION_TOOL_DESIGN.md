# Section Annotation Tool - Architectural Design

## Overview

A developer tool for annotating sections of job postings to create training data for ML models that detect skill-relevant content. This tool enables developers to select and label sections of job descriptions, which will be used to train models to automatically identify high-quality skill extraction zones.

## Business Requirements

1. **Section Selection**: Developers can highlight/select arbitrary sections of job posting text
2. **Section Labeling**: Each section can be labeled with a category (e.g., "skills_section", "responsibilities", "qualifications")
3. **Training Data Collection**: Annotations are stored as training data for ML model improvement
4. **Production Enabled**: Tool is accessible in production with appropriate access controls
5. **Independent of Jobs-Web**: Can function standalone without breaking existing job posting UI

## Architectural Principles

Following **Hexagonal Architecture (Ports & Adapters)**:

```
┌─────────────────────────────────────────────────┐
│              Domain Layer                        │
│  (Pure business logic, no dependencies)          │
│                                                  │
│  - SectionAnnotation (entity)                   │
│  - AnnotationLabel (enum)                       │
│  - SectionAnnotationRepository (port)           │
└─────────────────────────────────────────────────┘
                        ↑
                        │
┌─────────────────────────────────────────────────┐
│           Application Layer                      │
│  (Use cases orchestrating domain)                │
│                                                  │
│  - CreateAnnotationUseCase                      │
│  - ListAnnotationsUseCase                       │
│  - GetAnnotationsByJobUseCase                   │
│  - DeleteAnnotationUseCase                      │
│  - ExportTrainingDataUseCase                    │
└─────────────────────────────────────────────────┘
                        ↑
                        │
┌─────────────────────────────────────────────────┐
│            Adapters Layer                        │
│  (Infrastructure implementations)                │
│                                                  │
│  - BigQueryAnnotationRepository (persistence)   │
│  - FastAPI REST endpoints                       │
│  - React UI components                          │
└─────────────────────────────────────────────────┘
```

## 1. Domain Layer (Core Business Logic)

### 1.1 Domain Entities

**File**: `api/jobs-api/domain/entities.py`

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class AnnotationLabel(str, Enum):
    """Categories for annotated sections."""
    SKILLS_SECTION = "skills_section"          # Explicit skills list
    RESPONSIBILITIES = "responsibilities"      # Role duties (contains skills)
    QUALIFICATIONS = "qualifications"          # Required/preferred qualifications
    REQUIREMENTS = "requirements"              # Technical requirements
    EXPERIENCE = "experience"                  # Experience requirements
    NICE_TO_HAVE = "nice_to_have"             # Optional skills
    COMPANY_INFO = "company_info"              # About company (exclude from extraction)
    BENEFITS = "benefits"                      # Benefits section (exclude)
    LOCATION = "location"                      # Location info (exclude)
    OTHER = "other"                           # Uncategorized

@dataclass
class SectionAnnotation:
    """Developer annotation of a job posting section."""
    annotation_id: str
    job_posting_id: str
    section_text: str              # The actual text selected
    section_start_index: int       # Character position in full text
    section_end_index: int         # Character position in full text
    label: AnnotationLabel         # Category of this section
    contains_skills: bool          # Whether ML should extract from this
    annotator_id: str             # Developer who created annotation
    notes: Optional[str] = None    # Optional notes about annotation
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate annotation data."""
        if self.section_end_index <= self.section_start_index:
            raise ValueError("End index must be greater than start index")
        if not self.section_text.strip():
            raise ValueError("Section text cannot be empty")
        if len(self.section_text) < 10:
            raise ValueError("Section must be at least 10 characters")
```

### 1.2 Repository Port

**File**: `api/jobs-api/domain/repositories.py`

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities import SectionAnnotation

class SectionAnnotationRepository(ABC):
    """Port for section annotation data access."""
    
    @abstractmethod
    async def create_annotation(self, annotation: SectionAnnotation) -> SectionAnnotation:
        """Store a new section annotation."""
        pass
    
    @abstractmethod
    async def get_annotation_by_id(self, annotation_id: str) -> Optional[SectionAnnotation]:
        """Get a single annotation."""
        pass
    
    @abstractmethod
    async def list_annotations(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[SectionAnnotation]:
        """List all annotations with pagination."""
        pass
    
    @abstractmethod
    async def get_annotations_for_job(self, job_id: str) -> List[SectionAnnotation]:
        """Get all annotations for a specific job."""
        pass
    
    @abstractmethod
    async def delete_annotation(self, annotation_id: str) -> bool:
        """Delete an annotation."""
        pass
    
    @abstractmethod
    async def export_training_data(self) -> List[dict]:
        """Export all annotations as training data format."""
        pass
```

## 2. Application Layer (Use Cases)

**File**: `api/jobs-api/application/use_cases.py`

```python
from typing import List, Optional, Dict, Any
from domain.entities import SectionAnnotation, AnnotationLabel
from domain.repositories import SectionAnnotationRepository, JobRepository
import uuid

class CreateAnnotationUseCase:
    """Use case: Create a new section annotation."""
    
    def __init__(
        self,
        annotation_repo: SectionAnnotationRepository,
        job_repo: JobRepository
    ):
        self.annotation_repo = annotation_repo
        self.job_repo = job_repo
    
    async def execute(
        self,
        job_id: str,
        section_text: str,
        section_start_index: int,
        section_end_index: int,
        label: AnnotationLabel,
        annotator_id: str,
        notes: Optional[str] = None
    ) -> SectionAnnotation:
        """Create and store a new annotation."""
        
        # Validate job exists
        job = await self.job_repo.get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Determine if this section should be used for skill extraction
        contains_skills = label in [
            AnnotationLabel.SKILLS_SECTION,
            AnnotationLabel.RESPONSIBILITIES,
            AnnotationLabel.QUALIFICATIONS,
            AnnotationLabel.REQUIREMENTS,
            AnnotationLabel.EXPERIENCE,
            AnnotationLabel.NICE_TO_HAVE
        ]
        
        # Create annotation
        annotation = SectionAnnotation(
            annotation_id=str(uuid.uuid4()),
            job_posting_id=job_id,
            section_text=section_text,
            section_start_index=section_start_index,
            section_end_index=section_end_index,
            label=label,
            contains_skills=contains_skills,
            annotator_id=annotator_id,
            notes=notes
        )
        
        return await self.annotation_repo.create_annotation(annotation)


class GetAnnotationsByJobUseCase:
    """Use case: Get all annotations for a job."""
    
    def __init__(self, annotation_repo: SectionAnnotationRepository):
        self.annotation_repo = annotation_repo
    
    async def execute(self, job_id: str) -> List[SectionAnnotation]:
        """Get all annotations for a specific job posting."""
        return await self.annotation_repo.get_annotations_for_job(job_id)


class DeleteAnnotationUseCase:
    """Use case: Delete an annotation."""
    
    def __init__(self, annotation_repo: SectionAnnotationRepository):
        self.annotation_repo = annotation_repo
    
    async def execute(self, annotation_id: str) -> bool:
        """Delete an annotation by ID."""
        return await self.annotation_repo.delete_annotation(annotation_id)


class ExportTrainingDataUseCase:
    """Use case: Export annotations as ML training data."""
    
    def __init__(self, annotation_repo: SectionAnnotationRepository):
        self.annotation_repo = annotation_repo
    
    async def execute(self) -> Dict[str, Any]:
        """
        Export all annotations in ML training format.
        
        Returns:
            {
                'format': 'section_classification_v1',
                'total_annotations': int,
                'annotations': [
                    {
                        'job_id': str,
                        'text': str,
                        'label': str,
                        'should_extract_skills': bool,
                        'start_index': int,
                        'end_index': int
                    }
                ]
            }
        """
        annotations = await self.annotation_repo.export_training_data()
        
        return {
            'format': 'section_classification_v1',
            'total_annotations': len(annotations),
            'annotations': annotations,
            'label_distribution': self._calculate_label_distribution(annotations)
        }
    
    def _calculate_label_distribution(self, annotations: List[dict]) -> Dict[str, int]:
        """Calculate how many annotations per label."""
        distribution = {}
        for ann in annotations:
            label = ann['label']
            distribution[label] = distribution.get(label, 0) + 1
        return distribution
```

## 3. Adapters Layer (Infrastructure)

### 3.1 Persistence Adapter (BigQuery)

**File**: `api/jobs-api/adapters/bigquery_repository.py`

```python
# Add to existing BigQueryRepository class:

class BigQueryRepository(JobRepository, SkillRepository, ..., SectionAnnotationRepository):
    
    # ... existing methods ...
    
    # Section Annotation Methods
    
    async def create_annotation(self, annotation: SectionAnnotation) -> SectionAnnotation:
        """Store annotation in BigQuery."""
        query = """
        INSERT INTO `{project}.{dataset}.job_section_annotations` (
            annotation_id,
            job_posting_id,
            section_text,
            section_start_index,
            section_end_index,
            label,
            contains_skills,
            annotator_id,
            notes,
            created_at
        ) VALUES (
            @annotation_id,
            @job_posting_id,
            @section_text,
            @section_start_index,
            @section_end_index,
            @label,
            @contains_skills,
            @annotator_id,
            @notes,
            CURRENT_TIMESTAMP()
        )
        """.format(
            project=self.project_id,
            dataset=self.dataset_id
        )
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("annotation_id", "STRING", annotation.annotation_id),
                bigquery.ScalarQueryParameter("job_posting_id", "STRING", annotation.job_posting_id),
                bigquery.ScalarQueryParameter("section_text", "STRING", annotation.section_text),
                bigquery.ScalarQueryParameter("section_start_index", "INT64", annotation.section_start_index),
                bigquery.ScalarQueryParameter("section_end_index", "INT64", annotation.section_end_index),
                bigquery.ScalarQueryParameter("label", "STRING", annotation.label.value),
                bigquery.ScalarQueryParameter("contains_skills", "BOOL", annotation.contains_skills),
                bigquery.ScalarQueryParameter("annotator_id", "STRING", annotation.annotator_id),
                bigquery.ScalarQueryParameter("notes", "STRING", annotation.notes),
            ]
        )
        
        await self.client.query(query, job_config=job_config).result()
        return annotation
    
    async def get_annotations_for_job(self, job_id: str) -> List[SectionAnnotation]:
        """Get all annotations for a job."""
        query = """
        SELECT
            annotation_id,
            job_posting_id,
            section_text,
            section_start_index,
            section_end_index,
            label,
            contains_skills,
            annotator_id,
            notes,
            created_at
        FROM `{project}.{dataset}.job_section_annotations`
        WHERE job_posting_id = @job_id
        ORDER BY created_at DESC
        """.format(
            project=self.project_id,
            dataset=self.dataset_id
        )
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("job_id", "STRING", job_id)
            ]
        )
        
        results = await self.client.query(query, job_config=job_config).result()
        
        annotations = []
        for row in results:
            annotations.append(
                SectionAnnotation(
                    annotation_id=row.annotation_id,
                    job_posting_id=row.job_posting_id,
                    section_text=row.section_text,
                    section_start_index=row.section_start_index,
                    section_end_index=row.section_end_index,
                    label=AnnotationLabel(row.label),
                    contains_skills=row.contains_skills,
                    annotator_id=row.annotator_id,
                    notes=row.notes,
                    created_at=row.created_at
                )
            )
        
        return annotations
    
    # ... additional annotation repository methods ...
```

### 3.2 REST API Adapter (FastAPI)

**File**: `api/jobs-api/api/routes.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from domain.entities import AnnotationLabel

router = APIRouter()

# Request/Response Models
class CreateAnnotationRequest(BaseModel):
    job_id: str
    section_text: str
    section_start_index: int
    section_end_index: int
    label: AnnotationLabel
    annotator_id: str
    notes: Optional[str] = None

class AnnotationResponse(BaseModel):
    annotation_id: str
    job_posting_id: str
    section_text: str
    section_start_index: int
    section_end_index: int
    label: str
    contains_skills: bool
    annotator_id: str
    notes: Optional[str]
    created_at: str

# Endpoints
@router.post("/annotations", response_model=AnnotationResponse)
async def create_annotation(
    request: CreateAnnotationRequest,
    use_case: CreateAnnotationUseCase = Depends(get_create_annotation_use_case)
):
    """Create a new section annotation."""
    try:
        annotation = await use_case.execute(
            job_id=request.job_id,
            section_text=request.section_text,
            section_start_index=request.section_start_index,
            section_end_index=request.section_end_index,
            label=request.label,
            annotator_id=request.annotator_id,
            notes=request.notes
        )
        
        return AnnotationResponse(
            annotation_id=annotation.annotation_id,
            job_posting_id=annotation.job_posting_id,
            section_text=annotation.section_text,
            section_start_index=annotation.section_start_index,
            section_end_index=annotation.section_end_index,
            label=annotation.label.value,
            contains_skills=annotation.contains_skills,
            annotator_id=annotation.annotator_id,
            notes=annotation.notes,
            created_at=annotation.created_at.isoformat() if annotation.created_at else ""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/jobs/{job_id}/annotations", response_model=List[AnnotationResponse])
async def get_job_annotations(
    job_id: str,
    use_case: GetAnnotationsByJobUseCase = Depends(get_annotations_by_job_use_case)
):
    """Get all annotations for a specific job."""
    annotations = await use_case.execute(job_id)
    
    return [
        AnnotationResponse(
            annotation_id=ann.annotation_id,
            job_posting_id=ann.job_posting_id,
            section_text=ann.section_text,
            section_start_index=ann.section_start_index,
            section_end_index=ann.section_end_index,
            label=ann.label.value,
            contains_skills=ann.contains_skills,
            annotator_id=ann.annotator_id,
            notes=ann.notes,
            created_at=ann.created_at.isoformat() if ann.created_at else ""
        )
        for ann in annotations
    ]

@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    use_case: DeleteAnnotationUseCase = Depends(get_delete_annotation_use_case)
):
    """Delete an annotation."""
    success = await use_case.execute(annotation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return {"status": "deleted"}

@router.get("/annotations/export")
async def export_training_data(
    use_case: ExportTrainingDataUseCase = Depends(get_export_training_data_use_case)
):
    """Export all annotations as ML training data."""
    return await use_case.execute()
```

### 3.3 Database Schema (BigQuery)

**File**: `api/jobs-api/schema/job_section_annotations.sql`

```sql
CREATE TABLE `{project}.{dataset}.job_section_annotations` (
  annotation_id STRING NOT NULL,
  job_posting_id STRING NOT NULL,
  section_text STRING NOT NULL,
  section_start_index INT64 NOT NULL,
  section_end_index INT64 NOT NULL,
  label STRING NOT NULL,
  contains_skills BOOL NOT NULL,
  annotator_id STRING NOT NULL,
  notes STRING,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  
  -- Metadata
  _partition_date DATE NOT NULL DEFAULT CURRENT_DATE()
)
PARTITION BY _partition_date
OPTIONS(
  description="Section annotations for ML training data",
  require_partition_filter=false
);

-- Indexes for performance
CREATE INDEX idx_job_posting 
ON `{project}.{dataset}.job_section_annotations`(job_posting_id);

CREATE INDEX idx_label 
ON `{project}.{dataset}.job_section_annotations`(label);

CREATE INDEX idx_created_at 
ON `{project}.{dataset}.job_section_annotations`(created_at DESC);
```

## 4. Frontend (React UI)

### 4.1 Section Selection Component

**File**: `apps/jobs-web/src/components/SectionAnnotator/SectionAnnotator.tsx`

```typescript
import React, { useState, useCallback } from 'react';
import { AnnotationLabel } from '@/types/annotations';

interface SectionAnnotatorProps {
  jobId: string;
  jobDescription: string;
  existingAnnotations: Annotation[];
  onAnnotate: (annotation: CreateAnnotationRequest) => Promise<void>;
}

export const SectionAnnotator: React.FC<SectionAnnotatorProps> = ({
  jobId,
  jobDescription,
  existingAnnotations,
  onAnnotate
}) => {
  const [selectedText, setSelectedText] = useState('');
  const [selectionRange, setSelectionRange] = useState<{start: number, end: number} | null>(null);
  const [showLabelModal, setShowLabelModal] = useState(false);
  
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return;
    
    const text = selection.toString().trim();
    if (text.length < 10) return; // Minimum section length
    
    const range = selection.getRangeAt(0);
    const startIndex = range.startOffset;
    const endIndex = range.endOffset;
    
    setSelectedText(text);
    setSelectionRange({ start: startIndex, end: endIndex });
    setShowLabelModal(true);
  }, []);
  
  const handleLabelSelection = async (label: AnnotationLabel, notes?: string) => {
    if (!selectionRange) return;
    
    await onAnnotate({
      job_id: jobId,
      section_text: selectedText,
      section_start_index: selectionRange.start,
      section_end_index: selectionRange.end,
      label,
      annotator_id: 'developer', // TODO: Get from auth context
      notes
    });
    
    setShowLabelModal(false);
    setSelectedText('');
    setSelectionRange(null);
  };
  
  return (
    <div className="section-annotator">
      {/* Overlay showing existing annotations */}
      <div 
        className="annotatable-text"
        onMouseUp={handleTextSelection}
      >
        {renderTextWithAnnotations(jobDescription, existingAnnotations)}
      </div>
      
      {/* Label Selection Modal */}
      {showLabelModal && (
        <LabelModal
          selectedText={selectedText}
          onSelectLabel={handleLabelSelection}
          onCancel={() => setShowLabelModal(false)}
        />
      )}
    </div>
  );
};
```

### 4.2 Feature Flag Integration

**File**: `apps/jobs-web/src/app/jobs/[id]/page.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { SectionAnnotator } from '@/components/SectionAnnotator';

export default function JobDetailPage({ params }: { params: { id: string } }) {
  const [annotationMode, setAnnotationMode] = useState(false);
  
  // Feature flag check
  useEffect(() => {
    const isDeveloper = process.env.NEXT_PUBLIC_ENABLE_ANNOTATIONS === 'true';
    setAnnotationMode(isDeveloper);
  }, []);
  
  return (
    <div>
      {/* Existing job detail UI */}
      <JobHeader job={job} />
      
      {/* Toggle for annotation mode (developer only) */}
      {annotationMode && (
        <div className="developer-tools">
          <button onClick={() => setAnnotationMode(!annotationMode)}>
            Toggle Annotation Mode
          </button>
        </div>
      )}
      
      {/* Conditionally render annotator or regular description */}
      {annotationMode ? (
        <SectionAnnotator
          jobId={params.id}
          jobDescription={job.job_description_formatted}
          existingAnnotations={annotations}
          onAnnotate={handleCreateAnnotation}
        />
      ) : (
        <JobDescription highlightedDescription={highlightedDescription} />
      )}
    </div>
  );
}
```

## 5. Deployment Strategy

### 5.1 Independent Deployment

- **Backend**: Deploy annotation endpoints to existing `api/jobs-api` service
- **Frontend**: Feature-flagged component in `apps/jobs-web`
- **Database**: Create `job_section_annotations` table in existing BigQuery dataset

### 5.2 Feature Flags

```bash
# Environment variable for enabling annotation mode
NEXT_PUBLIC_ENABLE_ANNOTATIONS=true  # Only for developers
```

### 5.3 Access Control

- Initially: Environment variable based (developer mode)
- Future: Role-based access control (RBAC) with user authentication

## 6. Integration with ML Enrichment Service

### 6.1 Training Data Export

The ML enrichment service can fetch training data:

```python
# services/ml-enrichment/lib/training/section_detector.py

async def fetch_training_data():
    """Fetch annotations from API for model training."""
    response = requests.get(f"{API_URL}/annotations/export")
    data = response.json()
    
    return data['annotations']

async def train_section_classifier():
    """Train a classifier to detect skill-relevant sections."""
    annotations = await fetch_training_data()
    
    # Train model (e.g., using sklearn, spaCy, or transformers)
    # Input: section_text
    # Output: label (whether to extract skills)
    
    model = train_bert_classifier(annotations)
    save_model(model, "section_classifier_v1")
```

### 6.2 Using Trained Model in Skills Extractor

```python
# services/ml-enrichment/lib/enrichment/skills_extractor.py

class SkillsExtractor:
    def __init__(self):
        self.section_detector = load_section_detector_model()
    
    def extract_skills(self, job_text: str) -> List[Skill]:
        # Detect sections first
        sections = self.section_detector.detect_sections(job_text)
        
        # Filter to skill-relevant sections only
        skill_sections = [s for s in sections if s.should_extract_skills]
        
        # Extract skills only from relevant sections
        skills = []
        for section in skill_sections:
            section_skills = self._extract_from_text(section.text)
            skills.extend(section_skills)
        
        return skills
```

## 7. Implementation Phases

### Phase 1: Backend Foundation (Week 1)
- [ ] Add domain entities (SectionAnnotation, AnnotationLabel)
- [ ] Add repository port (SectionAnnotationRepository)
- [ ] Create use cases (Create, List, Delete, Export)
- [ ] Create BigQuery table
- [ ] Implement BigQuery adapter

### Phase 2: API Layer (Week 1)
- [ ] Add FastAPI endpoints
- [ ] Add request/response models
- [ ] Wire up dependency injection
- [ ] Test endpoints with Postman/curl

### Phase 3: Frontend UI (Week 2)
- [ ] Create SectionAnnotator component
- [ ] Implement text selection UI
- [ ] Create label selection modal
- [ ] Add annotation overlay visualization
- [ ] Integrate with existing job detail page

### Phase 4: Feature Flag & Access Control (Week 2)
- [ ] Add environment variable feature flag
- [ ] Add UI toggle for annotation mode
- [ ] Test in production with flag disabled
- [ ] Enable for developers only

### Phase 5: ML Integration (Week 3)
- [ ] Create training data export utility
- [ ] Build section detection model
- [ ] Integrate model into skills extractor
- [ ] A/B test extraction quality

## 8. Testing Strategy

### Unit Tests
- Domain entity validation
- Use case logic
- Repository adapter methods

### Integration Tests
- API endpoints with real BigQuery
- Full annotation workflow

### E2E Tests
- Frontend text selection
- Annotation creation and display
- Training data export

## 9. Success Metrics

1. **Annotation Coverage**: At least 100 job postings annotated
2. **Label Distribution**: Balanced representation across all labels
3. **ML Model Accuracy**: >85% accuracy in section detection
4. **Extraction Quality**: 20% improvement in skill extraction precision

## 10. Future Enhancements

1. **Annotation Review**: Peer review workflow for quality control
2. **Bulk Import**: Import annotations from external sources
3. **Active Learning**: ML suggests sections for annotation
4. **Analytics Dashboard**: Visualize annotation statistics
5. **Multi-user Collaboration**: Real-time collaborative annotation

---

## Architecture Compliance Checklist

✅ **Hexagonal Architecture**
- Domain entities are pure Python classes (no infrastructure dependencies)
- Repository interfaces defined as abstract ports
- Use cases orchestrate domain logic
- Adapters implement infrastructure (BigQuery, FastAPI, React)

✅ **Independence**
- Can deploy annotation endpoints without breaking existing API
- Frontend feature-flagged to avoid breaking jobs-web
- Database table isolated (no foreign key constraints to existing tables)

✅ **Complementary**
- Extends existing jobs-api architecture
- Reuses existing BigQuery infrastructure
- Integrates with ML enrichment service for training

✅ **Clean Implementation**
- Single responsibility principle (one use case per operation)
- Dependency inversion (domain doesn't depend on adapters)
- Open/closed principle (easy to add new annotation types)
