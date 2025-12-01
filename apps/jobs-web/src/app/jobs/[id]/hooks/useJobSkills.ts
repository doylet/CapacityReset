import { useState, useEffect } from 'react';
import { Skill, SkillType } from '@/types/skills';

interface Cluster {
  cluster_id: number;
  cluster_name: string;
  cluster_keywords: string[];
  cluster_size: number;
}

interface JobDetail {
  job_posting_id: string;
  job_title: string;
  company_name: string;
  company_url?: string | null;
  company_logo?: string | null;
  job_location: string;
  job_summary: string;
  job_posted_date: string;
  job_url?: string | null;
  job_description_formatted: string;
  skills: Skill[];
  cluster?: Cluster;
}

interface SkillCategory {
  category: string;
  display_name: string;
  skill_count: number;
}

export function useJobSkills(jobId: string, apiUrl: string, initialJob?: JobDetail | null) {
  const [job, setJob] = useState<JobDetail | null>(initialJob || null);
  const [loading, setLoading] = useState(!initialJob);
  const [skillCategories, setSkillCategories] = useState<SkillCategory[]>([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);

  const fetchJobDetail = async () => {
    if (!initialJob) {
      setLoading(true);
    }
    try {
      const response = await fetch(`${apiUrl}/jobs/${jobId}`);
      const data = await response.json();
      setJob(data);
    } catch (error) {
      console.error('Error fetching job detail:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSkillCategories = async () => {
    setCategoriesLoading(true);
    try {
      const response = await fetch(`${apiUrl}/skills/categories`);
      const data = await response.json();
      setSkillCategories(data.categories || []);
    } catch (error) {
      console.error('Error fetching skill categories:', error);
      // Fallback to default categories if API fails
      setSkillCategories([
        { category: 'technical_skills', display_name: 'Technical Skills', skill_count: 0 },
        { category: 'communicating', display_name: 'Communicating', skill_count: 0 },
        { category: 'creative_skills', display_name: 'Creative Skills', skill_count: 0 },
      ]);
    } finally {
      setCategoriesLoading(false);
    }
  };

  useEffect(() => {
    if (!initialJob) {
      fetchJobDetail();
    }
    fetchSkillCategories();
  }, [jobId, initialJob]);

  const updateSkillType = async (skillId: string, skillType: SkillType) => {
    try {
      await fetch(`${apiUrl}/jobs/${jobId}/skills/${skillId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_type: skillType }),
      });
      
      await fetchJobDetail();
    } catch (error) {
      console.error('Error updating skill:', error);
    }
  };

  const addSkillToJob = async (
    skillName: string,
    skillCategory: string,
    skillType: SkillType,
    contextSnippet: string
  ) => {
    if (!skillName) return;

    try {
      await fetch(`${apiUrl}/jobs/${jobId}/skills`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          skill_name: skillName,
          skill_category: skillCategory,
          context_snippet: contextSnippet,
          skill_type: skillType,
        }),
      });

      await fetchJobDetail();
    } catch (error) {
      console.error('Error adding skill:', error);
    }
  };

  const approveSkill = async (skillId: string) => {
    try {
      await fetch(`${apiUrl}/jobs/${jobId}/skills/${skillId}/approve`, {
        method: 'POST',
      });
      
      await fetchJobDetail();
      
      // Debug logging to check if approval was successful
      if (process.env.NODE_ENV === 'development') {
        console.log(`Approved skill ${skillId}, refetching job details...`);
      }
    } catch (error) {
      console.error('Error approving skill:', error);
    }
  };

  const rejectSkill = async (skillId: string) => {
    try {
      await fetch(`${apiUrl}/jobs/${jobId}/skills/${skillId}/reject`, {
        method: 'POST',
      });
      
      await fetchJobDetail();
    } catch (error) {
      console.error('Error rejecting skill:', error);
    }
  };

  const unapproveSkill = async (skillId: string) => {
    try {
      await fetch(`${apiUrl}/jobs/${jobId}/skills/${skillId}/unapprove`, {
        method: 'POST',
      });
      
      await fetchJobDetail();
      
      // Debug logging to check if unapproval was successful
      if (process.env.NODE_ENV === 'development') {
        console.log(`Unapproved skill ${skillId}, refetching job details...`);
      }
    } catch (error) {
      console.error('Error unapproving skill:', error);
    }
  };

  const getSkillsByCategory = () => {
    if (!job?.skills) return {};
    // Show only approved skills in the categorized view
    const approvedSkills = job.skills.filter(skill => skill.is_approved === true);
    
    return approvedSkills.reduce((acc, skill) => {
      if (!acc[skill.skill_category]) {
        acc[skill.skill_category] = [];
      }
      acc[skill.skill_category].push(skill);
      return acc;
    }, {} as Record<string, Skill[]>);
  };

  return {
    job,
    loading,
    skillCategories,
    categoriesLoading,
    updateSkillType,
    addSkillToJob,
    approveSkill,
    rejectSkill,
    unapproveSkill,
    getSkillsByCategory,
  };
}
