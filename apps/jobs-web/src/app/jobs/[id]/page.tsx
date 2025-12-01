'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import JobHeader from './components/JobHeader';
import JobDescription from './components/JobDescription';
import SkillsList from './components/SkillsList';
import SkillModal from './components/SkillModal';
// import SectionAnnotator from './components/SectionAnnotator';
import { useJobSkills } from './hooks/useJobSkills';
import { useSkillHighlighting } from './hooks/useSkillHighlighting';
import { useJobNavigation } from './hooks/useJobNavigation';
import { SkillType } from '@/types/skills';
import { Spinner } from '@/components/ui';

interface EditingSkill {
  skill_id: string;
  skill_type: SkillType;
}

type ModalMode = 'add' | 'edit' | null;

export default function JobDetailPage() {
  const params = useParams();
  const jobId = params.id as string;

  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [editingSkill, setEditingSkill] = useState<EditingSkill | null>(null);
  const [selectedText, setSelectedText] = useState('');
  const [newSkill, setNewSkill] = useState({
    skill_name: '',
    skill_category: 'technical_skills',
    skill_type: 'General' as SkillType,
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

  const {
    job,
    loading,
    skillCategories,
    categoriesLoading,
    updateSkillType,
    addSkillToJob,
    approveSkill,
    rejectSkill,
    getSkillsByCategory,
  } = useJobSkills(jobId, API_URL);

  const highlightedDescription = useSkillHighlighting(
    job?.skills,
    job?.job_description_formatted
  );

  const { previousJobId, nextJobId } = useJobNavigation(jobId, API_URL);

  const handleTextSelection = () => {
    const selection = window.getSelection();
    const text = selection?.toString().trim();
    if (text && text.length > 2) {
      setSelectedText(text);
      setNewSkill({ ...newSkill, skill_name: text });
      setModalMode('add');
    }
  };

  const handleBatchApprove = async (skillIds: string[]) => {
    try {
      await Promise.all(skillIds.map(skillId => approveSkill(skillId)));
    } catch (error) {
      console.error('Batch approve failed:', error);
    }
  };

  const handleBatchReject = async (skillIds: string[]) => {
    try {
      await Promise.all(skillIds.map(skillId => rejectSkill(skillId)));
    } catch (error) {
      console.error('Batch reject failed:', error);
    }
  };

  const handleAddSkill = async () => {
    await addSkillToJob(
      newSkill.skill_name,
      newSkill.skill_category,
      newSkill.skill_type,
      selectedText
    );
    
    setModalMode(null);
    setNewSkill({
      skill_name: '',
      skill_category: 'technical_skills',
      skill_type: 'General',
    });
    setSelectedText('');
  };

  const handleUpdateSkillType = async () => {
    if (!editingSkill) return;
    await updateSkillType(editingSkill.skill_id, editingSkill.skill_type);
    setEditingSkill(null);
    setModalMode(null);
  };

  const handleEditSkill = (skillId: string, skillType: SkillType) => {
    setEditingSkill({ skill_id: skillId, skill_type: skillType });
    setModalMode('edit');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Spinner size="xl" />
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
  const suggestedSkills = job?.skills.filter(s => s.is_approved !== true) || [];
  const approvedSkillsCount = job?.skills.filter(s => s.is_approved === true).length || 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <JobHeader job={job} previousJobId={previousJobId} nextJobId={nextJobId} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <JobDescription
            highlightedDescription={highlightedDescription}
            onTextSelection={handleTextSelection}
            clusterName={job.cluster?.cluster_name}
            previousJobId={previousJobId} 
            nextJobId={nextJobId}
          />

          {/* Sidebar - Skills */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-6">
              <SkillsList
                mode="suggested"
                skills={suggestedSkills}
                onApprove={approveSkill}
                onReject={rejectSkill}
                onBatchApprove={handleBatchApprove}
                onBatchReject={handleBatchReject}
              />
              
              <SkillsList
                mode="approved"
                skillsByCategory={skillsByCategory}
                totalCount={approvedSkillsCount}
                onEditSkill={handleEditSkill}
                onAddSkill={() => setModalMode('add')}
              />
            </div>
          </div>
        </div>

        {/* Section Annotations - TODO: Enable after testing */}
        {/* <div className="mt-8">
          <SectionAnnotator
            jobId={jobId}
            jobDescription={job.job_description}
            apiUrl={API_URL}
          />
        </div> */}
      </main>

      {modalMode === 'edit' && editingSkill && (
        <SkillModal
          isOpen={true}
          mode="edit"
          skillType={editingSkill.skill_type}
          onSkillTypeChange={(type) => setEditingSkill({ ...editingSkill, skill_type: type })}
          onSubmit={handleUpdateSkillType}
          onCancel={() => {
            setEditingSkill(null);
            setModalMode(null);
          }}
        />
      )}

      {modalMode === 'add' && (
        <SkillModal
          isOpen={true}
          mode="add"
          skillName={newSkill.skill_name}
          skillCategory={newSkill.skill_category}
          skillType={newSkill.skill_type}
          skillCategories={skillCategories}
          categoriesLoading={categoriesLoading}
          onSkillNameChange={(name) => setNewSkill({ ...newSkill, skill_name: name })}
          onSkillCategoryChange={(category) => setNewSkill({ ...newSkill, skill_category: category })}
          onSkillTypeChange={(type) => setNewSkill({ ...newSkill, skill_type: type })}
          onSubmit={handleAddSkill}
          onCancel={() => {
            setModalMode(null);
            setSelectedText('');
          }}
        />
      )}
    </div>
  );
}
