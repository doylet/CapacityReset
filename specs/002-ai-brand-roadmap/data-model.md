# Data Model: AI Brand Roadmap

**Created**: December 4, 2024  
**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)  
**Phase**: 1 - Design & Contracts (30-90 days)

## Core Entities

### Brand Representation
**Purpose**: Central professional identity model containing extracted themes, voice characteristics, and narrative structure

**Attributes**:
- `brand_id` (UUID): Unique identifier
- `user_id` (UUID): Owner reference  
- `source_document_url` (STRING): GCS path to uploaded CV/resume
- `linkedin_profile_url` (STRING, NULLABLE): Optional LinkedIn profile data
- `professional_themes` (JSON): Array of extracted career themes and strengths
- `voice_characteristics` (JSON): Tone, style, and communication patterns
- `narrative_arc` (JSON): Career story structure and key messages
- `confidence_scores` (JSON): Analysis confidence by theme/characteristic
- `created_at` (TIMESTAMP): Initial analysis timestamp
- `updated_at` (TIMESTAMP): Last modification time
- `version` (INTEGER): Brand representation version for evolution tracking

**Relationships**:
- One-to-many with Content Generations
- One-to-many with Brand Learning Events
- Many-to-many with Professional Themes

**Validation Rules**:
- Must have at least one source document
- Professional themes array must contain 1-10 themes
- Voice characteristics must include tone, formality, and energy levels
- Narrative arc must include career focus and value proposition

### Professional Theme
**Purpose**: Individual extracted concepts representing career focus, expertise areas, or value propositions

**Attributes**:
- `theme_id` (UUID): Unique identifier
- `theme_name` (STRING): Human-readable theme label
- `theme_category` (STRING): Category (skill, industry, role, value)
- `description` (TEXT): Detailed theme explanation
- `keywords` (ARRAY<STRING>): Associated terms and phrases
- `confidence_score` (FLOAT): Extraction confidence (0.0-1.0)
- `source_evidence` (TEXT): Document text supporting this theme
- `created_at` (TIMESTAMP): Theme extraction time

**Relationships**:
- Many-to-many with Brand Representations
- One-to-many with Brand Learning Events (theme-specific feedback)

### Professional Surface  
**Purpose**: Target platform or document type with specific formatting and tone requirements

**Attributes**:
- `surface_id` (UUID): Unique identifier
- `surface_type` (STRING): Platform type (cv_summary, linkedin_summary, portfolio_intro)
- `surface_name` (STRING): Display name
- `content_requirements` (JSON): Character limits, tone guidelines, structure rules
- `template_structure` (TEXT): Generation template with placeholders
- `validation_rules` (JSON): Content validation criteria
- `active` (BOOLEAN): Whether surface is available for generation

**Relationships**:
- One-to-many with Content Generations
- Referenced by Brand Learning Events

### Content Generation
**Purpose**: Individual piece of branded content with metadata, version tracking, and feedback history

**Attributes**:
- `generation_id` (UUID): Unique identifier
- `brand_id` (UUID): Source brand representation
- `surface_id` (UUID): Target surface reference
- `content_text` (TEXT): Generated content
- `generation_timestamp` (TIMESTAMP): Creation time
- `generation_version` (INTEGER): Version number for regenerations
- `generation_prompt` (TEXT): LLM prompt used for generation
- `consistency_score` (FLOAT): Cross-surface consistency rating
- `user_satisfaction_rating` (INTEGER, NULLABLE): User feedback score (1-5)
- `edit_count` (INTEGER): Number of user modifications
- `word_count` (INTEGER): Content length
- `status` (STRING): active, draft, archived

**Relationships**:
- Many-to-one with Brand Representation
- Many-to-one with Professional Surface  
- One-to-many with Brand Learning Events

**State Transitions**:
- draft → active (user approval)
- active → archived (regeneration)
- archived → active (user restoration)

### Brand Learning Event
**Purpose**: Captured user interaction for continuous improvement of brand analysis and generation

**Attributes**:
- `event_id` (UUID): Unique identifier
- `brand_id` (UUID): Associated brand representation
- `event_type` (STRING): edit, regeneration, preference_change, rating
- `event_timestamp` (TIMESTAMP): Interaction time
- `surface_id` (UUID, NULLABLE): Related surface if applicable  
- `theme_id` (UUID, NULLABLE): Related theme if applicable
- `event_data` (JSON): Type-specific data (edits, feedback, preferences)
- `user_feedback` (TEXT, NULLABLE): Optional user explanation
- `processed` (BOOLEAN): Whether event has been integrated into learning

**Event Type Schemas**:
```json
// edit event_data
{
  "original_text": "...",
  "modified_text": "...",
  "edit_type": "addition|deletion|modification",
  "edit_category": "tone|content|structure"
}

// regeneration event_data  
{
  "reason": "tone|accuracy|length|style",
  "feedback": "user explanation",
  "previous_generation_id": "uuid"
}

// preference_change event_data
{
  "preference_type": "tone|formality|emphasis",
  "old_value": "...",
  "new_value": "..."
}
```

**Relationships**:
- Many-to-one with Brand Representation
- Many-to-one with Professional Surface (optional)
- Many-to-one with Professional Theme (optional)
- Many-to-one with Content Generation (optional)

## Database Schema (BigQuery)

```sql
-- Brand Representations
CREATE TABLE IF NOT EXISTS `brand_representations` (
  brand_id STRING NOT NULL,
  user_id STRING NOT NULL,
  source_document_url STRING NOT NULL,
  linkedin_profile_url STRING,
  professional_themes JSON NOT NULL,
  voice_characteristics JSON NOT NULL,  
  narrative_arc JSON NOT NULL,
  confidence_scores JSON NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  version INTEGER NOT NULL DEFAULT 1
) 
PARTITION BY DATE(created_at)
CLUSTER BY user_id;

-- Professional Themes  
CREATE TABLE IF NOT EXISTS `professional_themes` (
  theme_id STRING NOT NULL,
  theme_name STRING NOT NULL,
  theme_category STRING NOT NULL,
  description TEXT NOT NULL,
  keywords ARRAY<STRING> NOT NULL,
  confidence_score FLOAT64 NOT NULL,
  source_evidence TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY theme_category;

-- Professional Surfaces
CREATE TABLE IF NOT EXISTS `professional_surfaces` (
  surface_id STRING NOT NULL,
  surface_type STRING NOT NULL,
  surface_name STRING NOT NULL,
  content_requirements JSON NOT NULL,
  template_structure TEXT NOT NULL,
  validation_rules JSON NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE
)
CLUSTER BY surface_type;

-- Content Generations
CREATE TABLE IF NOT EXISTS `content_generations` (
  generation_id STRING NOT NULL,
  brand_id STRING NOT NULL,
  surface_id STRING NOT NULL,
  content_text TEXT NOT NULL,
  generation_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  generation_version INTEGER NOT NULL DEFAULT 1,
  generation_prompt TEXT NOT NULL,
  consistency_score FLOAT64,
  user_satisfaction_rating INTEGER,
  edit_count INTEGER NOT NULL DEFAULT 0,
  word_count INTEGER NOT NULL,
  status STRING NOT NULL DEFAULT 'draft'
)
PARTITION BY DATE(generation_timestamp)  
CLUSTER BY brand_id, surface_id;

-- Brand Learning Events
CREATE TABLE IF NOT EXISTS `brand_learning_events` (
  event_id STRING NOT NULL,
  brand_id STRING NOT NULL,
  event_type STRING NOT NULL,
  event_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  surface_id STRING,
  theme_id STRING,
  event_data JSON NOT NULL,
  user_feedback TEXT,
  processed BOOLEAN NOT NULL DEFAULT FALSE
)
PARTITION BY DATE(event_timestamp)
CLUSTER BY brand_id, event_type;

-- Brand-Theme Associations (Many-to-Many)
CREATE TABLE IF NOT EXISTS `brand_theme_associations` (
  brand_id STRING NOT NULL,
  theme_id STRING NOT NULL,
  relevance_score FLOAT64 NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY brand_id;
```

## Repository Interfaces

### Brand Repository
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities import BrandRepresentation, ProfessionalTheme

class BrandRepository(ABC):
    @abstractmethod
    async def save_brand_representation(self, brand: BrandRepresentation) -> str:
        """Store brand representation, return brand_id"""
        pass
    
    @abstractmethod  
    async def get_brand_by_user(self, user_id: str) -> Optional[BrandRepresentation]:
        """Retrieve user's current brand representation"""
        pass
    
    @abstractmethod
    async def update_brand_themes(self, brand_id: str, themes: List[ProfessionalTheme]) -> bool:
        """Update themes for existing brand"""
        pass
    
    @abstractmethod
    async def get_brand_history(self, brand_id: str) -> List[BrandRepresentation]:
        """Retrieve brand evolution history"""
        pass
```

### Content Generation Repository
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities import ContentGeneration, ProfessionalSurface

class ContentGenerationRepository(ABC):
    @abstractmethod
    async def save_generation(self, generation: ContentGeneration) -> str:
        """Store generated content, return generation_id"""
        pass
    
    @abstractmethod
    async def get_generations_by_brand(self, brand_id: str) -> List[ContentGeneration]:
        """Retrieve all content for a brand"""
        pass
    
    @abstractmethod  
    async def get_active_generation(self, brand_id: str, surface_id: str) -> Optional[ContentGeneration]:
        """Get current active content for surface"""
        pass
    
    @abstractmethod
    async def archive_generation(self, generation_id: str) -> bool:
        """Archive old generation when regenerating"""
        pass
```

### Learning Repository
```python
from abc import ABC, abstractmethod
from typing import List
from domain.entities import BrandLearningEvent

class LearningRepository(ABC):
    @abstractmethod
    async def save_learning_event(self, event: BrandLearningEvent) -> str:
        """Store user interaction event"""
        pass
    
    @abstractmethod
    async def get_unprocessed_events(self, brand_id: str) -> List[BrandLearningEvent]:
        """Retrieve events needing integration"""
        pass
    
    @abstractmethod
    async def mark_event_processed(self, event_id: str) -> bool:
        """Mark event as integrated into learning"""
        pass
    
    @abstractmethod  
    async def get_learning_patterns(self, brand_id: str) -> dict:
        """Analyze user patterns for improvement"""
        pass
```

## Data Flow

### Brand Analysis Flow
1. User uploads CV → GCS storage
2. Document analysis extracts themes, voice, narrative 
3. BrandRepresentation created with confidence scores
4. Professional themes extracted and associated
5. Brand overview presented for user review

### Content Generation Flow  
1. User requests cross-surface generation
2. BrandRepresentation retrieved with themes
3. Parallel generation for each surface using templates
4. Consistency validation across surfaces
5. ContentGeneration records created
6. Generated content presented for review

### Learning Flow
1. User edits content or provides feedback
2. BrandLearningEvent captured with interaction details  
3. Events processed to identify patterns
4. Brand representation updated based on patterns
5. Future generations improved using learned preferences

## Validation & Constraints

### Data Quality
- All brand representations must have valid confidence scores (0.0-1.0)
- Content generations must pass surface-specific validation rules
- Learning events must contain valid JSON schemas for event_data
- Theme keywords must be non-empty and relevant

### Performance Constraints  
- Brand analysis results cached for 24 hours
- Content generation uses template-guided prompts for speed
- Learning events processed in batches every hour
- Cross-surface consistency validation runs in parallel

### Business Rules
- Users can only have one active brand representation
- Regenerated content archives previous versions
- Theme associations require minimum confidence threshold (0.3)
- Learning events older than 90 days are archived