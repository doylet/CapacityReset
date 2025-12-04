# Research: AI Brand Roadmap

**Created**: December 4, 2024  
**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)  
**Phase**: 0 - Research & Architecture (0-30 days)

## Research Objectives

This research phase resolves critical clarifications needed before design can proceed and establishes the technical foundation for the AI Brand Roadmap feature.

## Requirements Clarifications

### Q1: User Personas for Phase 1
**Question**: Should Phase 1 focus exclusively on job seekers, or should it support multiple professional personas?

**Research Needed**: Market analysis, user value assessment, development complexity

**Recommendation**: **Job seekers only in Phase 1**

**Decision**: Focus exclusively on job seekers in Phase 1 implementation
**Rationale**: 
- Provides clear, focused use case with well-defined success criteria
- Job seekers have the highest urgency and clearest value proposition for professional branding
- Enables faster development and validation with a specific user segment
- Career transition use cases overlap significantly with job seeker workflows
- Future phases can extend to entrepreneurs, freelancers, and executives with proven foundation

**Alternatives considered**:
- Multiple personas from start: Rejected due to complexity and unclear prioritization
- Job seekers + executives: Rejected as executives have different branding needs requiring separate research

### Q2: Input Surface Requirements  
**Question**: What input sources must be supported for brand analysis?

**Research Needed**: Brand analysis quality assessment, user onboarding friction, technical complexity

**Recommendation**: **CV required + optional LinkedIn profile**

**Decision**: CV/resume required, LinkedIn profile optional for enhanced analysis
**Rationale**:
- CV/resume provides core professional history and achievements essential for brand analysis  
- LinkedIn profiles add social proof and voice examples but aren't universal among job seekers
- Graceful degradation allows quality brand analysis from CV alone while improving with LinkedIn data
- Reduces onboarding friction compared to requiring multiple sources
- Technical complexity manageable with existing document processing capabilities

**Alternatives considered**:
- CV only: Rejected as LinkedIn provides valuable voice and positioning insights
- CV + LinkedIn required: Rejected due to onboarding friction and LinkedIn access complexity  

### Q3: Minimum Output Surfaces
**Question**: How many professional surfaces must be generated for "one-click branding"?

**Research Needed**: User value assessment, generation consistency challenges, technical feasibility

**Recommendation**: **3 surfaces minimum (CV summary + LinkedIn summary + portfolio introduction)**

**Decision**: Generate 3 core surfaces - CV professional summary, LinkedIn summary, and portfolio/website introduction
**Rationale**:
- Three surfaces provide comprehensive coverage of primary professional touchpoints
- Demonstrates clear value over manual content creation (saves 2-3 hours of writing)
- Sufficient variety to validate cross-surface consistency capabilities
- Technical complexity manageable within 30-second generation requirement
- Covers job application pipeline: CV for applications, LinkedIn for networking, portfolio for showcasing

**Alternatives considered**:
- 2 surfaces (CV + LinkedIn): Rejected as insufficient to demonstrate full branding value
- 4+ surfaces: Rejected due to generation time constraints and diminishing returns

## Technology Research

### Brand Analysis Architecture

**Decision**: Document analysis pipeline using spaCy + Vertex AI LLM combination
**Rationale**: 
- spaCy provides efficient document parsing and entity extraction
- Vertex AI LLM (Gemini) offers sophisticated semantic analysis for themes and voice characteristics
- Combination enables both structured data extraction and nuanced professional identity modeling
- Fits existing ml-enrichment service ML model lazy-loading pattern

**Implementation Pattern**:
```python
# Lazy-loaded brand analyzer
def get_brand_analyzer():
    global _brand_analyzer
    if _brand_analyzer is None:
        _brand_analyzer = BrandAnalyzer(
            nlp_model=get_spacy_model(),
            llm_client=get_vertex_ai_client()
        )
    return _brand_analyzer
```

### Content Generation Strategy

**Decision**: Template-guided LLM generation with consistency validation  
**Rationale**:
- Surface-specific templates ensure appropriate tone and structure for each platform
- LLM generation provides natural language quality and personalization
- Cross-surface consistency validation prevents messaging conflicts
- Performance optimized through template constraints and parallel generation

**Generation Flow**:
1. Brand representation → surface templates
2. Parallel LLM generation for each surface  
3. Consistency validation across outputs
4. Refinement if consistency scores below threshold

### Learning Architecture

**Decision**: Event-sourced feedback system feeding brand representation updates
**Rationale**:
- Captures all user interactions (edits, regenerations, preferences) as events
- Enables replay and analysis of user learning patterns
- Feeds back to brand representation refinement
- Supports A/B testing of different generation approaches

**Event Types**:
- Content edits (surface, edit type, original/modified text)
- Regeneration requests (surface, feedback reason)
- Brand overview modifications (field, original/new value)
- Preference settings (tone, style, emphasis areas)

### Performance Optimization Strategy

**Decision**: Cached brand representations with incremental generation
**Rationale**:
- Brand analysis (expensive) cached after initial processing
- Content generation (fast) performed on-demand
- Incremental updates to brand representation avoid full reanalysis
- Parallel surface generation reduces total time

**Performance Targets**:
- Brand analysis: <5 minutes (one-time per user)
- Content generation: <30 seconds (cross-surface)
- Brand updates: <10 seconds (incremental)

## Architecture Patterns

### Domain Integration

**Decision**: Extend existing ml-enrichment service with new domain entities
**Rationale**:
- Brand analysis is fundamentally an ML enrichment of professional documents
- Leverages existing infrastructure (BigQuery, Vertex AI, Cloud Run)
- Follows established patterns for model versioning and lazy loading
- Maintains service boundaries while adding related functionality

### Data Model Foundation

**Core Entities**:
- `BrandRepresentation`: Professional identity model (themes, voice, narrative)
- `ContentGeneration`: Generated content with metadata and feedback  
- `BrandLearningEvent`: User interaction tracking for improvement
- `ProfessionalTheme`: Extracted concepts building brand foundation

### API Integration

**Decision**: Extend jobs-api with brand management endpoints
**Rationale**:
- Brand functionality logically extends job-related user workflows
- Leverages existing authentication and user management
- Maintains API consistency and documentation patterns
- Enables integration with existing job application features

## Implementation Risks & Mitigations

**Risk**: LLM generation consistency across surfaces
**Mitigation**: Consistency validation pipeline with automatic retry for low-scoring outputs

**Risk**: Brand analysis quality for minimal CV content  
**Mitigation**: Graceful degradation with user prompts for additional context

**Risk**: 30-second generation time constraint
**Mitigation**: Parallel generation, cached representations, optimized prompts

**Risk**: User feedback integration complexity
**Mitigation**: Event-sourced design with incremental learning implementation

## Success Validation Strategy

- **Brand Analysis Quality**: Human evaluation of theme extraction accuracy (>85%)
- **Generation Consistency**: Automated semantic similarity scoring (>90%)  
- **Performance**: Automated testing of generation times (<30s target)
- **User Satisfaction**: A/B testing of brand quality vs. manual creation

## Next Phase Readiness

✅ **All NEEDS CLARIFICATION markers resolved**  
✅ **Technology stack decisions made**  
✅ **Architecture patterns established**  
✅ **Performance strategy defined**

**Ready for Phase 1**: Design & Contracts