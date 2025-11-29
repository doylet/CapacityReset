'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Tag, X, Check, AlertCircle } from 'lucide-react';

export type AnnotationLabel = 
  | 'SKILLS_SECTION'
  | 'RESPONSIBILITIES'
  | 'QUALIFICATIONS'
  | 'REQUIREMENTS'
  | 'EXPERIENCE'
  | 'NICE_TO_HAVE'
  | 'COMPANY_INFO'
  | 'BENEFITS'
  | 'SALARY'
  | 'OTHER';

interface Annotation {
  annotation_id: string;
  section_text: string;
  start_index: number;
  end_index: number;
  label: AnnotationLabel;
  contains_skills: boolean;
  notes?: string;
}

interface SectionAnnotatorProps {
  jobId: string;
  jobDescription: string;
  apiUrl: string;
  annotatorId?: string;
}

const LABEL_CONFIGS: Record<AnnotationLabel, { label: string; color: string; description: string }> = {
  SKILLS_SECTION: { label: 'Skills', color: 'bg-blue-100 text-blue-800 border-blue-300', description: 'Technical or soft skills required' },
  RESPONSIBILITIES: { label: 'Responsibilities', color: 'bg-purple-100 text-purple-800 border-purple-300', description: 'Job duties and responsibilities' },
  QUALIFICATIONS: { label: 'Qualifications', color: 'bg-green-100 text-green-800 border-green-300', description: 'Education and certifications' },
  REQUIREMENTS: { label: 'Requirements', color: 'bg-orange-100 text-orange-800 border-orange-300', description: 'Must-have requirements' },
  EXPERIENCE: { label: 'Experience', color: 'bg-yellow-100 text-yellow-800 border-yellow-300', description: 'Years of experience required' },
  NICE_TO_HAVE: { label: 'Nice to Have', color: 'bg-teal-100 text-teal-800 border-teal-300', description: 'Preferred but not required' },
  COMPANY_INFO: { label: 'Company Info', color: 'bg-indigo-100 text-indigo-800 border-indigo-300', description: 'About the company' },
  BENEFITS: { label: 'Benefits', color: 'bg-pink-100 text-pink-800 border-pink-300', description: 'Perks and benefits' },
  SALARY: { label: 'Salary', color: 'bg-red-100 text-red-800 border-red-300', description: 'Compensation information' },
  OTHER: { label: 'Other', color: 'bg-gray-100 text-gray-800 border-gray-300', description: 'Other relevant information' },
};

export default function SectionAnnotator({ jobId, jobDescription, apiUrl, annotatorId = 'user-1' }: SectionAnnotatorProps) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [selectedText, setSelectedText] = useState('');
  const [selectionIndices, setSelectionIndices] = useState<{ start: number; end: number } | null>(null);
  const [showLabelModal, setShowLabelModal] = useState(false);
  const [selectedLabel, setSelectedLabel] = useState<AnnotationLabel | null>(null);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch existing annotations
  useEffect(() => {
    fetchAnnotations();
  }, [jobId]);

  const fetchAnnotations = async () => {
    try {
      const response = await fetch(`${apiUrl}/jobs/${jobId}/annotations`);
      if (response.ok) {
        const data = await response.json();
        setAnnotations(data);
      }
    } catch (err) {
      console.error('Failed to fetch annotations:', err);
    }
  };

  const handleTextSelection = () => {
    const selection = window.getSelection();
    const text = selection?.toString().trim();
    
    if (!text || text.length < 10) {
      return;
    }

    // Get selection indices relative to job description
    const range = selection?.getRangeAt(0);
    if (!range) return;

    const preSelectionRange = range.cloneRange();
    const container = document.getElementById('annotation-text');
    if (!container) return;

    preSelectionRange.selectNodeContents(container);
    preSelectionRange.setEnd(range.startContainer, range.startOffset);
    const start = preSelectionRange.toString().length;
    const end = start + text.length;

    setSelectedText(text);
    setSelectionIndices({ start, end });
    setShowLabelModal(true);
    setError(null);
  };

  const createAnnotation = async () => {
    if (!selectedLabel || !selectionIndices) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/annotations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_posting_id: jobId,
          section_text: selectedText,
          start_index: selectionIndices.start,
          end_index: selectionIndices.end,
          label: selectedLabel,
          annotator_id: annotatorId,
          notes: notes || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create annotation');
      }

      const newAnnotation = await response.json();
      setAnnotations([...annotations, newAnnotation]);
      resetModal();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create annotation');
    } finally {
      setLoading(false);
    }
  };

  const deleteAnnotation = async (annotationId: string) => {
    try {
      const response = await fetch(`${apiUrl}/annotations/${annotationId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setAnnotations(annotations.filter(a => a.annotation_id !== annotationId));
      }
    } catch (err) {
      console.error('Failed to delete annotation:', err);
    }
  };

  const resetModal = () => {
    setShowLabelModal(false);
    setSelectedText('');
    setSelectionIndices(null);
    setSelectedLabel(null);
    setNotes('');
    window.getSelection()?.removeAllRanges();
  };

  // Render job description with annotation highlights
  const renderHighlightedText = () => {
    if (annotations.length === 0) {
      return <div className="whitespace-pre-wrap">{jobDescription}</div>;
    }

    // Sort annotations by start index
    const sortedAnnotations = [...annotations].sort((a, b) => a.start_index - b.start_index);
    const segments: JSX.Element[] = [];
    let lastIndex = 0;

    sortedAnnotations.forEach((annotation, idx) => {
      // Add text before annotation
      if (annotation.start_index > lastIndex) {
        segments.push(
          <span key={`text-${idx}`}>
            {jobDescription.slice(lastIndex, annotation.start_index)}
          </span>
        );
      }

      // Add highlighted annotation
      const config = LABEL_CONFIGS[annotation.label];
      segments.push(
        <span
          key={`annotation-${annotation.annotation_id}`}
          className={`${config.color} border-b-2 cursor-pointer relative group`}
          title={`${config.label}${annotation.notes ? `: ${annotation.notes}` : ''}`}
        >
          {annotation.section_text}
          <button
            onClick={() => deleteAnnotation(annotation.annotation_id)}
            className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 bg-red-500 text-white rounded-full p-1 text-xs transition-opacity"
          >
            <X className="w-3 h-3" />
          </button>
        </span>
      );

      lastIndex = annotation.end_index;
    });

    // Add remaining text
    if (lastIndex < jobDescription.length) {
      segments.push(
        <span key="text-end">{jobDescription.slice(lastIndex)}</span>
      );
    }

    return <div className="whitespace-pre-wrap">{segments}</div>;
  };

  return (
    <div className="space-y-4">
      {/* Annotation Stats */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Tag className="w-5 h-5 text-gray-500" />
          <h3 className="text-lg font-semibold text-gray-900">
            Section Annotations ({annotations.length})
          </h3>
        </div>
        <Badge variant="secondary">
          {annotations.filter(a => a.contains_skills).length} with skills
        </Badge>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          <strong>How to annotate:</strong> Select any text in the job description below and choose a label to mark different sections for ML training.
        </p>
      </div>

      {/* Annotatable Text */}
      <div
        id="annotation-text"
        className="bg-white border border-gray-200 rounded-lg p-6 cursor-text"
        onMouseUp={handleTextSelection}
      >
        {renderHighlightedText()}
      </div>

      {/* Label Selection Modal */}
      {showLabelModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Label Section</h3>
                <button onClick={resetModal} className="text-gray-400 hover:text-gray-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Selected Text Preview */}
              <div className="bg-gray-50 border border-gray-200 rounded p-3 mb-4">
                <p className="text-sm text-gray-600 mb-1">Selected text:</p>
                <p className="text-sm text-gray-900 italic">"{selectedText.slice(0, 100)}{selectedText.length > 100 ? '...' : ''}"</p>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded p-3 mb-4 flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-900">{error}</p>
                </div>
              )}

              {/* Label Selection Grid */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                {(Object.entries(LABEL_CONFIGS) as [AnnotationLabel, typeof LABEL_CONFIGS[AnnotationLabel]][]).map(([key, config]) => (
                  <button
                    key={key}
                    onClick={() => setSelectedLabel(key)}
                    className={`text-left p-3 border-2 rounded-lg transition-all ${
                      selectedLabel === key
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className={`inline-block px-2 py-1 rounded text-xs font-medium mb-1 ${config.color}`}>
                      {config.label}
                    </div>
                    <p className="text-xs text-gray-600">{config.description}</p>
                  </button>
                ))}
              </div>

              {/* Notes (Optional) */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notes (optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add any additional context or notes..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                />
              </div>

              {/* Actions */}
              <div className="flex gap-3 justify-end">
                <Button variant="outline" onClick={resetModal}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={createAnnotation}
                  disabled={!selectedLabel || loading}
                  leftIcon={loading ? undefined : <Check className="w-4 h-4" />}
                >
                  {loading ? 'Creating...' : 'Create Annotation'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
