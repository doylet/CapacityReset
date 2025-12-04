'use client';

import { useState } from 'react';
import { GeneratedContent, SurfaceType } from '@/types/brand';
import { Copy, Check, RefreshCw, FileText, Linkedin, Globe, Star } from 'lucide-react';

interface GeneratedContentDisplayProps {
  content: GeneratedContent[];
  brandId: string;
  onRegenerate?: (generationId: string, surfaceType: SurfaceType) => void;
  onRate?: (generationId: string, rating: number) => void;
}

const SURFACE_ICONS: Record<SurfaceType, React.ReactNode> = {
  cv_summary: <FileText className="w-5 h-5" />,
  linkedin_summary: <Linkedin className="w-5 h-5" />,
  portfolio_intro: <Globe className="w-5 h-5" />,
};

const SURFACE_NAMES: Record<SurfaceType, string> = {
  cv_summary: 'CV Professional Summary',
  linkedin_summary: 'LinkedIn Summary',
  portfolio_intro: 'Portfolio Introduction',
};

export default function GeneratedContentDisplay({
  content,
  brandId,
  onRegenerate,
  onRate,
}: GeneratedContentDisplayProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [ratings, setRatings] = useState<Record<string, number>>({});

  const handleCopy = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleRate = (generationId: string, rating: number) => {
    setRatings((prev) => ({ ...prev, [generationId]: rating }));
    onRate?.(generationId, rating);
  };

  if (content.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-500">No content generated yet. Use the generator above to create branded content.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Generated Content</h2>
      
      {content.map((item) => (
        <div key={item.generation_id} className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Header */}
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <span className="text-blue-600 mr-2">
                  {SURFACE_ICONS[item.surface_type]}
                </span>
                <h3 className="font-medium text-gray-900">
                  {item.surface_name || SURFACE_NAMES[item.surface_type]}
                </h3>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-500">
                  {item.word_count} words
                </span>
                {item.consistency_score && (
                  <span className="text-sm text-green-600">
                    {Math.round(item.consistency_score * 100)}% consistent
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            <div className="prose max-w-none">
              <p className="text-gray-800 whitespace-pre-wrap">{item.content_text}</p>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              {/* Rating */}
              <div className="flex items-center gap-1">
                <span className="text-sm text-gray-500 mr-2">Rate this:</span>
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => handleRate(item.generation_id, star)}
                    className={`p-1 transition-colors ${
                      (ratings[item.generation_id] || item.user_satisfaction_rating || 0) >= star
                        ? 'text-yellow-500'
                        : 'text-gray-300 hover:text-yellow-400'
                    }`}
                  >
                    <Star
                      className="w-5 h-5"
                      fill={
                        (ratings[item.generation_id] || item.user_satisfaction_rating || 0) >= star
                          ? 'currentColor'
                          : 'none'
                      }
                    />
                  </button>
                ))}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleCopy(item.content_text, item.generation_id)}
                  className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {copiedId === item.generation_id ? (
                    <>
                      <Check className="w-4 h-4 text-green-500" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      Copy
                    </>
                  )}
                </button>
                {onRegenerate && (
                  <button
                    onClick={() => onRegenerate(item.generation_id, item.surface_type)}
                    className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Regenerate
                  </button>
                )}
              </div>
            </div>

            {/* Meta info */}
            <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
              <span>Version {item.generation_version}</span>
              <span>•</span>
              <span>Generated {new Date(item.generation_timestamp).toLocaleString()}</span>
              {item.edit_count > 0 && (
                <>
                  <span>•</span>
                  <span>{item.edit_count} edits</span>
                </>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
