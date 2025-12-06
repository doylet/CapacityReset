'use client';

import { useState, useRef, useEffect } from 'react';
import { GeneratedContent, SurfaceType, ProfessionalSurface } from '@/types/brand';
import { 
  Copy, 
  Check, 
  RefreshCw, 
  Edit3, 
  Save, 
  X, 
  FileText, 
  Linkedin, 
  Globe, 
  Star,
  AlertCircle,
  Clock,
  CheckCircle2,
  MoreHorizontal,
  Download,
  Share2,
  Eye
} from 'lucide-react';

interface ContentSurfaceProps {
  content: GeneratedContent;
  surface: ProfessionalSurface;
  brandId: string;
  isLoading?: boolean;
  onRegenerate?: (generationId: string, feedback?: string) => Promise<void>;
  onEdit?: (generationId: string, updatedContent: string) => Promise<void>;
  onRate?: (generationId: string, rating: number) => void;
  onCopy?: (content: string, surfaceType: SurfaceType) => void;
  onPreview?: (content: string, surfaceType: SurfaceType) => void;
  className?: string;
}

const SURFACE_ICONS: Record<string, React.ReactNode> = {
  cv_summary: <FileText className="w-5 h-5" />,
  linkedin_summary: <Linkedin className="w-5 h-5" />,
  portfolio_intro: <Globe className="w-5 h-5" />,
};

const SURFACE_COLORS: Record<string, string> = {
  cv_summary: 'border-blue-200 bg-blue-50',
  linkedin_summary: 'border-blue-600 bg-blue-100',
  portfolio_intro: 'border-purple-200 bg-purple-50',
};

const SURFACE_ACCENT_COLORS: Record<string, string> = {
  cv_summary: 'text-blue-700',
  linkedin_summary: 'text-blue-800',
  portfolio_intro: 'text-purple-700',
};

export default function ContentSurface({
  content,
  surface,
  brandId,
  isLoading = false,
  onRegenerate,
  onEdit,
  onRate,
  onCopy,
  onPreview,
  className = '',
}: ContentSurfaceProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(content.content_text);
  const [isCopied, setIsCopied] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [showActionsMenu, setShowActionsMenu] = useState(false);
  const [userRating, setUserRating] = useState(content.user_satisfaction_rating || 0);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [isEditing, editedContent]);

  // Click outside to close menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowActionsMenu(false);
      }
    };

    if (showActionsMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showActionsMenu]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content.content_text);
      setIsCopied(true);
      onCopy?.(content.content_text, content.surface_type);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy content:', error);
    }
  };

  const handleStartEdit = () => {
    setIsEditing(true);
    setEditedContent(content.content_text);
    setShowActionsMenu(false);
  };

  const handleSaveEdit = async () => {
    if (!editedContent.trim() || editedContent === content.content_text) {
      setIsEditing(false);
      return;
    }

    setIsSaving(true);
    try {
      await onEdit?.(content.generation_id, editedContent);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save edit:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedContent(content.content_text);
  };

  const handleRegenerate = async (withFeedback: boolean = false) => {
    setIsRegenerating(true);
    setShowActionsMenu(false);
    
    try {
      const feedbackText = withFeedback ? feedback : undefined;
      await onRegenerate?.(content.generation_id, feedbackText);
      setFeedback('');
      setShowFeedback(false);
    } catch (error) {
      console.error('Failed to regenerate content:', error);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleRate = (rating: number) => {
    setUserRating(rating);
    onRate?.(content.generation_id, rating);
  };

  const handlePreview = () => {
    onPreview?.(content.content_text, content.surface_type);
    setShowActionsMenu(false);
  };

  const getContentStatusIndicator = () => {
    if (content.status === 'active') {
      return (
        <div className="flex items-center gap-1 text-green-600 text-xs">
          <CheckCircle2 className="w-3 h-3" />
          Active
        </div>
      );
    } else if (content.status === 'draft') {
      return (
        <div className="flex items-center gap-1 text-orange-600 text-xs">
          <Clock className="w-3 h-3" />
          Draft
        </div>
      );
    }
    return null;
  };

  const getWordCountStatus = () => {
    const requirements = surface.content_requirements;
    const wordCount = content.word_count;
    
    if (requirements.min_length && wordCount < requirements.min_length) {
      return { status: 'warning', message: `${wordCount} words (min: ${requirements.min_length})` };
    } else if (requirements.max_length && wordCount > requirements.max_length) {
      return { status: 'error', message: `${wordCount} words (max: ${requirements.max_length})` };
    } else {
      return { status: 'success', message: `${wordCount} words` };
    }
  };

  const wordCountStatus = getWordCountStatus();
  const surfaceColor = SURFACE_COLORS[content.surface_type] || 'border-gray-200 bg-gray-50';
  const accentColor = SURFACE_ACCENT_COLORS[content.surface_type] || 'text-gray-700';

  return (
    <div className={`border rounded-lg p-6 ${surfaceColor} ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-white border ${accentColor}`}>
            {SURFACE_ICONS[content.surface_type] || <FileText className="w-5 h-5" />}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{surface.surface_name}</h3>
            <div className="flex items-center gap-3 text-sm text-gray-500">
              <span>Generated {new Date(content.generation_timestamp).toLocaleDateString()}</span>
              {getContentStatusIndicator()}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Word count indicator */}
          <div className={`text-xs px-2 py-1 rounded-full ${
            wordCountStatus.status === 'error' ? 'bg-red-100 text-red-700' :
            wordCountStatus.status === 'warning' ? 'bg-orange-100 text-orange-700' :
            'bg-green-100 text-green-700'
          }`}>
            {wordCountStatus.message}
          </div>

          {/* Actions menu */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setShowActionsMenu(!showActionsMenu)}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-white rounded-lg transition-colors"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>

            {showActionsMenu && (
              <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                <div className="p-1">
                  <button
                    onClick={handleCopy}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                  >
                    <Copy className="w-4 h-4" />
                    Copy Content
                  </button>
                  <button
                    onClick={handleStartEdit}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                  >
                    <Edit3 className="w-4 h-4" />
                    Edit Content
                  </button>
                  <button
                    onClick={handlePreview}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                  >
                    <Eye className="w-4 h-4" />
                    Preview
                  </button>
                  <div className="h-px bg-gray-200 my-1" />
                  <button
                    onClick={() => handleRegenerate(false)}
                    disabled={isRegenerating}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 ${isRegenerating ? 'animate-spin' : ''}`} />
                    Regenerate
                  </button>
                  <button
                    onClick={() => setShowFeedback(true)}
                    disabled={isRegenerating}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md disabled:opacity-50"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Regenerate with Feedback
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="space-y-4">
        {isEditing ? (
          <div className="space-y-3">
            <textarea
              ref={textareaRef}
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              className="w-full p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your content here..."
              style={{ minHeight: '120px' }}
            />
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={handleSaveEdit}
                  disabled={isSaving || !editedContent.trim()}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSaving ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  <X className="w-4 h-4" />
                  Cancel
                </button>
              </div>
              <div className="text-sm text-gray-500">
                {editedContent.split(' ').filter(word => word.length > 0).length} words
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg p-4 border">
            <pre className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed font-sans">
              {content.content_text}
            </pre>
          </div>
        )}

        {/* Quality Indicators */}
        {content.consistency_score && (
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-1">
              <AlertCircle className="w-4 h-4" />
              <span>Consistency Score: {(content.consistency_score * 100).toFixed(1)}%</span>
            </div>
          </div>
        )}

        {/* Rating */}
        {!isEditing && (
          <div className="flex items-center justify-between pt-3 border-t border-gray-200">
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600">Rate this content:</span>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => handleRate(star)}
                    className={`p-1 transition-colors ${
                      star <= userRating ? 'text-yellow-400' : 'text-gray-300 hover:text-yellow-300'
                    }`}
                  >
                    <Star className="w-4 h-4" fill={star <= userRating ? 'currentColor' : 'none'} />
                  </button>
                ))}
              </div>
            </div>

            {isCopied && (
              <div className="flex items-center gap-1 text-green-600 text-sm">
                <Check className="w-4 h-4" />
                Copied!
              </div>
            )}
          </div>
        )}
      </div>

      {/* Feedback Modal */}
      {showFeedback && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Regeneration Feedback
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Share what you'd like to improve in the regenerated content:
            </p>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="e.g., Make it more technical, focus on leadership experience, use a more casual tone..."
              className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
            />
            <div className="flex items-center gap-3 mt-4">
              <button
                onClick={() => handleRegenerate(true)}
                disabled={isRegenerating}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isRegenerating ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                {isRegenerating ? 'Regenerating...' : 'Regenerate'}
              </button>
              <button
                onClick={() => setShowFeedback(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading Overlay */}
      {(isLoading || isRegenerating) && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
          <div className="flex items-center gap-3 text-gray-600">
            <RefreshCw className="w-5 h-5 animate-spin" />
            <span>{isRegenerating ? 'Regenerating content...' : 'Loading...'}</span>
          </div>
        </div>
      )}
    </div>
  );
}