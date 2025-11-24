'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Calendar, MapPin, Tag, Edit2, Plus, Save, X, ExternalLink } from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';

interface Skill {
  skill_id: string;
  skill_name: string;
  skill_category: string;
  confidence_score: number;
  context_snippet: string;
  extraction_method: string;
  skill_type?: 'GENERAL' | 'SPECIALISED' | 'TRANSFERRABLE';
}

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

interface EditingSkill {
  skill_id: string;
  skill_type: 'GENERAL' | 'SPECIALISED' | 'TRANSFERRABLE';
}

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;

  const [job, setJob] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingSkill, setEditingSkill] = useState<EditingSkill | null>(null);
  const [showAddSkill, setShowAddSkill] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const [newSkill, setNewSkill] = useState({
    skill_name: '',
    skill_category: 'technical_skills',
    skill_type: 'GENERAL' as 'GENERAL' | 'SPECIALISED' | 'TRANSFERRABLE',
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

  useEffect(() => {
    fetchJobDetail();
  }, [jobId]);

  const fetchJobDetail = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/jobs/${jobId}`);
      const data = await response.json();
      setJob(data);
    } catch (error) {
      console.error('Error fetching job detail:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTextSelection = () => {
    const selection = window.getSelection();
    const text = selection?.toString().trim();
    if (text && text.length > 2) {
      setSelectedText(text);
      setNewSkill(prev => ({ ...prev, skill_name: text }));
      setShowAddSkill(true);
    }
  };

  const updateSkillType = async (skillId: string, skillType: 'GENERAL' | 'SPECIALISED' | 'TRANSFERRABLE') => {
    try {
      await fetch(`${API_URL}/jobs/${jobId}/skills/${skillId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_type: skillType }),
      });
      
      // Refresh job data
      fetchJobDetail();
      setEditingSkill(null);
    } catch (error) {
      console.error('Error updating skill:', error);
    }
  };

  const addSkillToJob = async () => {
    if (!newSkill.skill_name) return;

    try {
      await fetch(`${API_URL}/jobs/${jobId}/skills`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          skill_name: newSkill.skill_name,
          skill_category: newSkill.skill_category,
          context_snippet: selectedText,
          skill_type: newSkill.skill_type,
        }),
      });

      // Refresh and reset
      fetchJobDetail();
      setShowAddSkill(false);
      setNewSkill({
        skill_name: '',
        skill_category: 'technical_skills',
        skill_type: 'GENERAL',
      });
      setSelectedText('');
    } catch (error) {
      console.error('Error adding skill:', error);
    }
  };

  const normalizeWhitespace = (text: string): string => {
    return text
      // Replace multiple spaces with single space
      .replace(/ {2,}/g, ' ')
      // Replace multiple newlines with double newline (paragraph break)
      .replace(/\n{3,}/g, '\n\n')
      // Remove trailing/leading whitespace from each line
      .split('\n')
      .map(line => line.trim())
      .join('\n')
      .trim();
  };

  const highlightSkillsInText = (text: string) => {
    if (!job?.skills || job.skills.length === 0) return normalizeWhitespace(text);

    let highlightedText = normalizeWhitespace(text);
    const skillsToHighlight = [...job.skills].sort((a, b) => 
      b.skill_name.length - a.skill_name.length
    );

    skillsToHighlight.forEach(skill => {
      const regex = new RegExp(`\\b${skill.skill_name}\\b`, 'gi');
      const skillTypeClass = skill.skill_type ? skill.skill_type.toLowerCase() : '';
      highlightedText = highlightedText.replace(
        regex,
        `<span class="skill-highlight ${skillTypeClass}" data-skill-id="${skill.skill_id}" title="${skill.skill_category} (${skill.confidence_score.toFixed(2)})">${skill.skill_name}</span>`
      );
    });

    return highlightedText;
  };

  const getSkillsByCategory = () => {
    if (!job?.skills) return {};
    return job.skills.reduce((acc, skill) => {
      if (!acc[skill.skill_category]) {
        acc[skill.skill_category] = [];
      }
      acc[skill.skill_category].push(skill);
      return acc;
    }, {} as Record<string, Skill[]>);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Job not found</p>
          <Link href="/" className="text-blue-600 hover:text-blue-800">
            Back to Jobs
          </Link>
        </div>
      </div>
    );
  }

  const skillsByCategory = getSkillsByCategory();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link href="/" className="inline-flex items-center text-sm text-gray-600 hover:text-blue-700 mb-4">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Jobs
          </Link>
          
          <div className="flex items-start gap-4">
            {/* Company Logo */}
            {job.company_logo && (
              <img 
                src={job.company_logo} 
                alt={`${job.company_name} logo`}
                className="h-16 w-16 object-contain flex-shrink-0"
              />
            )}
            
            <div className="flex-1">
              {/* Job Title */}
              <h1 className="text-2xl font-semibold text-gray-900 mb-1">{job.job_title}</h1>
              
              {/* Company Name */}
              {job.company_url ? (
                <a 
                  href={job.company_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-base text-gray-900 hover:text-blue-700 hover:underline inline-block mb-2"
                >
                  {job.company_name}
                </a>
              ) : (
                <p className="text-base text-gray-900 mb-2">{job.company_name}</p>
              )}
              
              {/* Job Metadata */}
              <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {job.job_location}
                </span>
                <span className="text-gray-400">·</span>
                <span>{formatDistanceToNow(new Date(job.job_posted_date), { addSuffix: true })}</span>
              </div>
              
              {/* View Original Link */}
              {job.job_url && (
                <a 
                  href={job.job_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-blue-700 bg-white border border-blue-700 rounded-full hover:bg-blue-50 transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  View Original Job Posting
                </a>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Job Info */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {job.job_location}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {format(new Date(job.job_posted_date), 'MMMM d, yyyy')}
                </span>
              </div>

              {job.cluster && (
                <div className="mb-4">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                    {job.cluster.cluster_name}
                  </span>
                </div>
              )}
            </div>

            {/* Job Description with Highlighted Skills */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Job Description</h2>
                <button
                  onClick={() => setShowAddSkill(true)}
                  className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4" />
                  Add Skill
                </button>
              </div>
              
              <div className="text-gray-700 leading-relaxed">
                <p className="text-sm text-gray-500 mb-4 italic">
                  Select text to add as a new skill, or click highlighted skills to edit
                </p>
                <div
                  onMouseUp={handleTextSelection}
                  dangerouslySetInnerHTML={{ __html: highlightSkillsInText(job.job_description_formatted) }}
                  className="whitespace-pre-wrap"
                />
              </div>
            </div>
          </div>

          {/* Sidebar - Skills */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Tag className="w-5 h-5" />
                Extracted Skills ({job.skills.length})
              </h2>

              <div className="space-y-4">
                {Object.entries(skillsByCategory).map(([category, skills]) => (
                  <div key={category}>
                    <h3 className="text-sm font-medium text-gray-700 mb-2 capitalize">
                      {category.replace(/_/g, ' ')}
                    </h3>
                    <div className="space-y-2">
                      {skills.map(skill => (
                        <div
                          key={skill.skill_id}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">{skill.skill_name}</p>
                            <p className="text-xs text-gray-500">
                              Confidence: {(skill.confidence_score * 100).toFixed(0)}%
                              {skill.skill_type && ` • ${skill.skill_type}`}
                            </p>
                          </div>
                          <button
                            onClick={() => setEditingSkill({ skill_id: skill.skill_id, skill_type: skill.skill_type || 'GENERAL' })}
                            className="ml-2 p-1 text-gray-400 hover:text-gray-600"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Edit Skill Modal */}
      {editingSkill && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Edit Skill Type</h3>
            <div className="space-y-3">
              {(['GENERAL', 'SPECIALISED', 'TRANSFERRABLE'] as const).map(type => (
                <label key={type} className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="skill_type"
                    value={type}
                    checked={editingSkill.skill_type === type}
                    onChange={(e) => setEditingSkill({ ...editingSkill, skill_type: e.target.value as any })}
                    className="h-4 w-4 text-blue-600"
                  />
                  <span className="text-sm font-medium text-gray-900">{type}</span>
                </label>
              ))}
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => updateSkillType(editingSkill.skill_id, editingSkill.skill_type)}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save
              </button>
              <button
                onClick={() => setEditingSkill(null)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Skill Modal */}
      {showAddSkill && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Skill</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Skill Name</label>
                <input
                  type="text"
                  value={newSkill.skill_name}
                  onChange={(e) => setNewSkill({ ...newSkill, skill_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Python"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                <select
                  value={newSkill.skill_category}
                  onChange={(e) => setNewSkill({ ...newSkill, skill_category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="technical_skills">Technical Skills</option>
                  <option value="communicating">Communicating</option>
                  <option value="creative_skills">Creative Skills</option>
                  <option value="developing_people">Developing People</option>
                  <option value="financial_skills">Financial Skills</option>
                  <option value="interpersonal_skills">Interpersonal Skills</option>
                  <option value="managing_directing">Managing & Directing</option>
                  <option value="organising">Organising</option>
                  <option value="planning">Planning</option>
                  <option value="researching_analysing">Researching & Analysing</option>
                  <option value="selling_marketing">Selling & Marketing</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Skill Type</label>
                <div className="space-y-2">
                  {(['GENERAL', 'SPECIALISED', 'TRANSFERRABLE'] as const).map(type => (
                    <label key={type} className="flex items-center gap-3 p-2 border rounded cursor-pointer hover:bg-gray-50">
                      <input
                        type="radio"
                        name="new_skill_type"
                        value={type}
                        checked={newSkill.skill_type === type}
                        onChange={(e) => setNewSkill({ ...newSkill, skill_type: e.target.value as any })}
                        className="h-4 w-4 text-blue-600"
                      />
                      <span className="text-sm text-gray-900">{type}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={addSkillToJob}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center justify-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Skill
              </button>
              <button
                onClick={() => {
                  setShowAddSkill(false);
                  setSelectedText('');
                }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
