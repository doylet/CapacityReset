// Brand-related types for AI Brand Roadmap feature

export type ThemeCategory = 'skill' | 'industry' | 'role' | 'value_proposition' | 'achievement';
export type VoiceTone = 'professional' | 'conversational' | 'authoritative' | 'creative' | 'analytical';
export type FormalityLevel = 'casual' | 'business_casual' | 'formal' | 'highly_formal';
export type EnergyLevel = 'reserved' | 'balanced' | 'enthusiastic' | 'dynamic';
export type SurfaceType = 'cv_summary' | 'linkedin_summary' | 'portfolio_intro';
export type ContentStatus = 'draft' | 'active' | 'archived';

export interface ProfessionalTheme {
  theme_id: string;
  theme_name: string;
  theme_category: ThemeCategory;
  description?: string;
  keywords: string[];
  confidence_score: number;
  source_evidence?: string;
}

export interface VoiceCharacteristics {
  tone: VoiceTone;
  formality_level: FormalityLevel;
  energy_level: EnergyLevel;
  communication_style: string[];
  vocabulary_complexity: string;
}

export interface NarrativeArc {
  career_focus: string;
  value_proposition: string;
  career_progression?: string;
  key_achievements: string[];
  future_goals?: string;
}

export interface BrandOverview {
  brand_id: string;
  professional_themes: ProfessionalTheme[];
  voice_characteristics: VoiceCharacteristics;
  narrative_arc: NarrativeArc;
  confidence_scores: Record<string, number>;
  created_at?: string;
  updated_at?: string;
}

export interface AnalysisMetadata {
  document_type?: string;
  word_count?: number;
  confidence_score?: number;
  processing_time_ms?: number;
}

export interface BrandAnalysisResponse {
  brand_id: string;
  analysis_status: string;
  brand_overview: BrandOverview;
  analysis_metadata?: AnalysisMetadata;
}

export interface GeneratedContent {
  generation_id: string;
  surface_type: SurfaceType;
  surface_name?: string;
  content_text: string;
  generation_timestamp: string;
  generation_version: number;
  word_count: number;
  consistency_score?: number;
  edit_count: number;
  user_satisfaction_rating?: number;
  status: ContentStatus;
}

export interface GenerationMetadata {
  generation_time_ms?: number;
  consistency_score?: number;
  surfaces_count: number;
}

export interface ContentGenerationResponse {
  generation_id: string;
  brand_id: string;
  generated_content: GeneratedContent[];
  generation_metadata?: GenerationMetadata;
}

export interface ProfessionalSurface {
  surface_id: string;
  surface_type: string;
  surface_name: string;
  content_requirements: {
    min_length?: number;
    max_length?: number;
    tone_guidelines: string[];
    structure_requirements: string[];
  };
  template_structure?: string;
  active: boolean;
}

export interface GenerationPreferences {
  emphasis_themes: string[];
  target_length: 'concise' | 'standard' | 'detailed';
  include_achievements: boolean;
}

export interface ContentGenerationRequest {
  surface_types: SurfaceType[];
  generation_preferences?: GenerationPreferences;
}
