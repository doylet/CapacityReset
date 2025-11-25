/**
 * Shared skill types - centralized type definitions
 * 
 * Note: These should match the backend SkillType enum
 * Backend: api/jobs-api/domain/entities.py::SkillType
 */

export type SkillType = 'General' | 'Specialised' | 'Transferrable';

export const SKILL_TYPES: readonly SkillType[] = ['General', 'Specialised', 'Transferrable'] as const;

export interface Skill {
  skill_id: string;
  skill_name: string;
  skill_category: string;
  confidence_score: number;
  context_snippet: string;
  extraction_method: string;
  approval_status?: 'pending' | 'approved' | 'rejected';
  skill_type?: SkillType;
  is_approved?: boolean | null;
}

/**
 * Utility to validate if a string is a valid SkillType
 */
export function isValidSkillType(value: string): value is SkillType {
  return SKILL_TYPES.includes(value as SkillType);
}

/**
 * Convert backend skill type format to frontend format
 * Backend uses lowercase: "general", "specialised", "transferrable"
 * Frontend uses capitalized: "General", "Specialised", "Transferrable"
 */
export function normalizeSkillType(backendType: string): SkillType {
  const normalized = backendType.charAt(0).toUpperCase() + backendType.slice(1).toLowerCase();
  return isValidSkillType(normalized) ? normalized : 'General';
}
