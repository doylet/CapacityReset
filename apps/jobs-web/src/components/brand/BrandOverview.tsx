'use client';

import { BrandOverview, ProfessionalTheme } from '@/types/brand';
import { User, Mic, BookOpen, Award, TrendingUp } from 'lucide-react';

interface BrandOverviewDisplayProps {
  brand: BrandOverview;
  onEdit?: () => void;
}

export default function BrandOverviewDisplay({ brand, onEdit }: BrandOverviewDisplayProps) {
  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      skill: 'bg-blue-100 text-blue-800',
      industry: 'bg-green-100 text-green-800',
      role: 'bg-purple-100 text-purple-800',
      value_proposition: 'bg-orange-100 text-orange-800',
      achievement: 'bg-yellow-100 text-yellow-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <User className="w-6 h-6 mr-2 text-blue-600" />
              Your Professional Brand
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Analysis completed • Last updated {brand.updated_at ? new Date(brand.updated_at).toLocaleDateString() : 'recently'}
            </p>
          </div>
          {onEdit && (
            <button
              onClick={onEdit}
              className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              Edit Brand
            </button>
          )}
        </div>

        {/* Confidence Scores */}
        <div className="mt-4 grid grid-cols-4 gap-4">
          {Object.entries(brand.confidence_scores).map(([key, score]) => (
            <div key={key} className="text-center">
              <div className={`text-lg font-bold ${getConfidenceColor(score)}`}>
                {Math.round(score * 100)}%
              </div>
              <div className="text-xs text-gray-500 capitalize">{key}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Professional Themes */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-medium text-gray-900 flex items-center mb-4">
          <Award className="w-5 h-5 mr-2 text-blue-600" />
          Professional Themes
        </h3>
        <div className="grid gap-4">
          {brand.professional_themes.map((theme) => (
            <div key={theme.theme_id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900">{theme.theme_name}</span>
                <span className={`px-2 py-1 text-xs rounded-full ${getCategoryColor(theme.theme_category)}`}>
                  {theme.theme_category.replace('_', ' ')}
                </span>
              </div>
              {theme.description && (
                <p className="text-sm text-gray-600 mb-2">{theme.description}</p>
              )}
              <div className="flex flex-wrap gap-2">
                {theme.keywords.map((keyword, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
              <div className="mt-2 flex items-center">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${theme.confidence_score * 100}%` }}
                  />
                </div>
                <span className="ml-2 text-xs text-gray-500">
                  {Math.round(theme.confidence_score * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Voice Characteristics */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-medium text-gray-900 flex items-center mb-4">
          <Mic className="w-5 h-5 mr-2 text-blue-600" />
          Voice Characteristics
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-500">Tone</span>
            <p className="font-medium text-gray-900 capitalize">{brand.voice_characteristics.tone}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Formality</span>
            <p className="font-medium text-gray-900 capitalize">
              {brand.voice_characteristics.formality_level.replace('_', ' ')}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Energy Level</span>
            <p className="font-medium text-gray-900 capitalize">{brand.voice_characteristics.energy_level}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Vocabulary</span>
            <p className="font-medium text-gray-900 capitalize">{brand.voice_characteristics.vocabulary_complexity}</p>
          </div>
        </div>
        {brand.voice_characteristics.communication_style.length > 0 && (
          <div className="mt-4">
            <span className="text-sm text-gray-500">Communication Style</span>
            <div className="flex flex-wrap gap-2 mt-1">
              {brand.voice_characteristics.communication_style.map((style, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded-full"
                >
                  {style.replace('_', ' ')}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Narrative Arc */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-medium text-gray-900 flex items-center mb-4">
          <BookOpen className="w-5 h-5 mr-2 text-blue-600" />
          Career Narrative
        </h3>
        <div className="space-y-4">
          <div>
            <span className="text-sm text-gray-500">Career Focus</span>
            <p className="font-medium text-gray-900">{brand.narrative_arc.career_focus}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Value Proposition</span>
            <p className="font-medium text-gray-900">{brand.narrative_arc.value_proposition}</p>
          </div>
          {brand.narrative_arc.career_progression && (
            <div>
              <span className="text-sm text-gray-500">Career Progression</span>
              <p className="font-medium text-gray-900">{brand.narrative_arc.career_progression}</p>
            </div>
          )}
          {brand.narrative_arc.key_achievements.length > 0 && (
            <div>
              <span className="text-sm text-gray-500">Key Achievements</span>
              <ul className="mt-1 space-y-1">
                {brand.narrative_arc.key_achievements.map((achievement, idx) => (
                  <li key={idx} className="flex items-start">
                    <TrendingUp className="w-4 h-4 mr-2 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-900">{achievement}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {brand.narrative_arc.future_goals && (
            <div>
              <span className="text-sm text-gray-500">Future Goals</span>
              <p className="font-medium text-gray-900">{brand.narrative_arc.future_goals}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
