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
    // Debug logging
    console.log('useSkillHighlighting called with:', {
      skillsCount: skills?.length || 0,
      descriptionLength: description?.length || 0,
      skills: skills?.map(s => ({ name: s.skill_name, approved: s.is_approved })),
    });

    if (!skills || skills.length === 0 || !description) {
      return normalizeWhitespace(description || '');
    }

    const text = description;
    const isHTML = text.includes('<') && text.includes('>');
    let highlightedText = isHTML ? text : normalizeWhitespace(text);
    
    // Highlight all skills (both approved and pending suggestions)
    // Only exclude explicitly rejected ones (is_approved === false)
    const skillsToHighlight = skills.filter(skill => skill.is_approved !== false);
    
    console.log('Skills to highlight:', skillsToHighlight.length, 'out of', skills.length);
    
    // Sort skills by length (longest first) to avoid partial matches
    const sortedSkills = [...skillsToHighlight].sort((a, b) => 
      b.skill_name.length - a.skill_name.length
    );

    // Process skills in sorted order to avoid partial matches
    sortedSkills.forEach(skill => {
      const escapedSkill = skill.skill_name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      
      if (isHTML) {
        const regex = new RegExp(`(?<!<[^>]*)\\b${escapedSkill}\\b(?![^<]*>)`, 'gi');
        const skillTypeClass = skill.skill_type ? skill.skill_type.toLowerCase() : '';
        const beforeReplace = highlightedText;
        highlightedText = highlightedText.replace(
          regex,
          `<span class="skill-highlight ${skillTypeClass}" data-skill-id="${skill.skill_id}" title="${skill.skill_category} (${skill.confidence_score.toFixed(2)})">${skill.skill_name}</span>`
        );
        
        if (beforeReplace !== highlightedText) {
          console.log(`Highlighted "${skill.skill_name}" in HTML content`);
        }
      } else {
        const regex = new RegExp(`\\b${escapedSkill}\\b`, 'gi');
        const skillTypeClass = skill.skill_type ? skill.skill_type.toLowerCase() : '';
        const beforeReplace = highlightedText;
        highlightedText = highlightedText.replace(
          regex,
          `<span class="skill-highlight ${skillTypeClass}" data-skill-id="${skill.skill_id}" title="${skill.skill_category} (${skill.confidence_score.toFixed(2)})">${skill.skill_name}</span>`
        );
        
        if (beforeReplace !== highlightedText) {
          console.log(`Highlighted "${skill.skill_name}" in plain text content`);
        }
      }
    });

    return highlightedText;
  }, [skills, description]);
}
