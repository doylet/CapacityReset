'use client';

import { useState } from 'react';
import { BrandOverview, ProfessionalTheme } from '@/types/brand';
import { User, Mic, BookOpen, Award, TrendingUp, ChevronDown, ChevronUp, Quote, Lightbulb } from 'lucide-react';

interface BrandOverviewDisplayProps {
  brand: BrandOverview;
  onEdit?: () => void;
}

interface ThemeCardProps {
  theme: ProfessionalTheme;
  getCategoryColor: (category: string) => string;
}

function ThemeCard({ theme, getCategoryColor }: ThemeCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-gray-900">{theme.theme_name}</span>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 text-xs rounded-full ${getCategoryColor(theme.theme_category)}`}>
            {theme.theme_category.replace('_', ' ')}
          </span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
            aria-label={isExpanded ? "Collapse details" : "Expand details"}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
          </button>
        </div>
      </div>
      
      {theme.description && (
        <p className="text-sm text-gray-600 mb-2">{theme.description}</p>
      )}
      
      {/* Keywords */}
      <div className="flex flex-wrap gap-2 mb-3">
        {theme.keywords.map((keyword, idx) => (
          <span
            key={idx}
            className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
          >
            {keyword}
          </span>
        ))}
      </div>
      
      {/* Confidence Score */}
      <div className="flex items-center">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${theme.confidence_score * 100}%` }}
          />
        </div>
        <span className="ml-2 text-xs text-gray-500 whitespace-nowrap">
          {Math.round(theme.confidence_score * 100)}% confidence
        </span>
      </div>
      
      {/* Expanded Details - LLM Reasoning and Evidence */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
          {/* LLM Reasoning */}
          {theme.reasoning && (
            <div className="flex items-start gap-2">
              <Lightbulb className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Why this theme?
                </span>
                <p className="text-sm text-gray-700 mt-1">{theme.reasoning}</p>
              </div>
            </div>
          )}
          
          {/* Source Evidence */}
          {theme.source_evidence && (
            <div className="flex items-start gap-2">
              <Quote className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Evidence
                </span>
                <p className="text-sm text-gray-700 mt-1 italic">{theme.source_evidence}</p>
              </div>
            </div>
          )}
          
          {/* Evidence Quotes (if available) */}
          {theme.evidence_quotes && theme.evidence_quotes.length > 0 && (
            <div className="flex items-start gap-2">
              <Quote className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Supporting Quotes
                </span>
                <ul className="mt-1 space-y-1">
                  {theme.evidence_quotes.map((quote, idx) => (
                    <li key={idx} className="text-sm text-gray-700 pl-3 border-l-2 border-green-200">
                      "{quote}"
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
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

      {/* Professional Themes - Enhanced Display */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <Award className="w-5 h-5 mr-2 text-blue-600" />
            Professional Themes
          </h3>
          <span className="text-sm text-gray-500">
            {brand.professional_themes.length} themes identified
          </span>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Click on a theme to see the reasoning and evidence behind each identification.
        </p>
        <div className="grid gap-4">
          {brand.professional_themes.map((theme) => (
            <ThemeCard 
              key={theme.theme_id} 
              theme={theme} 
              getCategoryColor={getCategoryColor} 
            />
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
