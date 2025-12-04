-- Initial Professional Surfaces Data
-- Seed data for the three core surfaces: CV summary, LinkedIn summary, and portfolio introduction

INSERT INTO `professional_surfaces` (
  surface_id,
  surface_type,
  surface_name,
  content_requirements,
  template_structure,
  validation_rules,
  active
) VALUES
(
  'surf-cv-summary-001',
  'cv_summary',
  'CV Professional Summary',
  JSON '{"min_length": 100, "max_length": 300, "tone_guidelines": ["professional", "achievement-focused"], "structure_requirements": ["opening_statement", "key_achievements", "value_proposition"]}',
  'A results-driven {career_focus} with {experience_years} years of experience in {industry}. Known for {key_strength_1} and {key_strength_2}. Demonstrated ability to {key_achievement}. Seeking to leverage expertise in {target_role}.',
  JSON '{"required_elements": ["career_focus", "experience_indication", "value_statement"], "forbidden_phrases": ["I am", "My name is"]}',
  TRUE
),
(
  'surf-linkedin-summary-001',
  'linkedin_summary',
  'LinkedIn Summary',
  JSON '{"min_length": 150, "max_length": 500, "tone_guidelines": ["conversational", "professional", "authentic"], "structure_requirements": ["hook", "story", "expertise", "call_to_action"]}',
  '{hook_statement}\n\n{career_story}\n\nI specialize in {expertise_areas} and am passionate about {passion_statement}.\n\n{key_achievements}\n\n{call_to_action}',
  JSON '{"required_elements": ["personal_hook", "expertise_areas", "call_to_action"], "forbidden_phrases": [], "encourages_first_person": true}',
  TRUE
),
(
  'surf-portfolio-intro-001',
  'portfolio_intro',
  'Portfolio Introduction',
  JSON '{"min_length": 100, "max_length": 250, "tone_guidelines": ["creative", "professional", "engaging"], "structure_requirements": ["introduction", "expertise", "value_statement"]}',
  'Hello, I am {professional_title}. {expertise_statement} {unique_value_proposition} Explore my work to see {portfolio_preview}.',
  JSON '{"required_elements": ["professional_identity", "expertise_overview", "portfolio_invitation"], "forbidden_phrases": []}',
  TRUE
);
