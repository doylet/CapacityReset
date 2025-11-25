import { useMemo } from 'react';
import { Skill } from '@/types/skills';

const normalizeWhitespace = (text: string): string => {
  if (!text) return '';
  
  // If it's HTML content (contains tags), clean up HTML whitespace
  if (text.includes('<') && text.includes('>')) {
    return text
      // Remove excessive whitespace between HTML tags
      .replace(/>\s+</g, '><')
      // Remove empty paragraphs and divs
      .replace(/<(p|div|br)[^>]*>\s*<\/(p|div)>/gi, '')
      // Normalize whitespace within text nodes
      .replace(/\s{2,}/g, ' ')
      .trim();
  }
  
  // For plain text, aggressive whitespace normalization
  return text
    // Replace multiple spaces/tabs with single space
    .replace(/[ \t]{2,}/g, ' ')
    // Replace 3+ newlines with just 1 (paragraph break)
    .replace(/\n{3,}/g, '\n')
    // Remove spaces before newlines
    .replace(/ +\n/g, '\n')
    // Remove spaces after newlines
    .replace(/\n +/g, '\n')
    // Remove trailing/leading whitespace from each line
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0) // Remove empty lines
    .join('\n')
    .trim();
};

export function useSkillHighlighting(
  skills: Skill[] | undefined,
  description: string | undefined
): string {
  return useMemo(() => {
    if (!skills || skills.length === 0 || !description) {
      return normalizeWhitespace(description || '');
    }

    const text = description;
    const isHTML = text.includes('<') && text.includes('>');
    let highlightedText = isHTML ? text : normalizeWhitespace(text);
    
    // Highlight all skills (both approved and pending suggestions)
    // Only exclude explicitly rejected ones (is_approved === false)
    const skillsToHighlight = skills.filter(skill => skill.is_approved !== false);
    
    // Sort skills by length (longest first) to avoid partial matches
    const sortedSkills = [...skillsToHighlight].sort((a, b) => 
      b.skill_name.length - a.skill_name.length
    );

    // Build a single regex pattern for all skills (more efficient than looping)
    skillsToHighlight.forEach(skill => {
      const escapedSkill = skill.skill_name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      
      if (isHTML) {
        const regex = new RegExp(`(?<!<[^>]*)\\b${escapedSkill}\\b(?![^<]*>)`, 'gi');
        const skillTypeClass = skill.skill_type ? skill.skill_type.toLowerCase() : '';
        highlightedText = highlightedText.replace(
          regex,
          `<span class="skill-highlight ${skillTypeClass}" data-skill-id="${skill.skill_id}" title="${skill.skill_category} (${skill.confidence_score.toFixed(2)})">${skill.skill_name}</span>`
        );
      } else {
        const regex = new RegExp(`\\b${escapedSkill}\\b`, 'gi');
        const skillTypeClass = skill.skill_type ? skill.skill_type.toLowerCase() : '';
        highlightedText = highlightedText.replace(
          regex,
          `<span class="skill-highlight ${skillTypeClass}" data-skill-id="${skill.skill_id}" title="${skill.skill_category} (${skill.confidence_score.toFixed(2)})">${skill.skill_name}</span>`
        );
      }
    });

    return highlightedText;
  }, [skills, description]);
}
