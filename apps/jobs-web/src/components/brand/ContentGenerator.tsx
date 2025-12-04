'use client';

import { useState } from 'react';
import { Wand2, Loader2, FileText, Linkedin, Globe } from 'lucide-react';
import { BrandOverview, GeneratedContent, SurfaceType, ContentGenerationResponse } from '@/types/brand';

interface ContentGeneratorProps {
  brandId: string;
  brand: BrandOverview;
  onContentGenerated: (content: GeneratedContent[]) => void;
}

interface SurfaceOption {
  type: SurfaceType;
  name: string;
  description: string;
  icon: React.ReactNode;
}

const SURFACE_OPTIONS: SurfaceOption[] = [
  {
    type: 'cv_summary',
    name: 'CV Professional Summary',
    description: 'A concise, achievement-focused professional summary for your resume',
    icon: <FileText className="w-5 h-5" />,
  },
  {
    type: 'linkedin_summary',
    name: 'LinkedIn Summary',
    description: 'An engaging, authentic summary for your LinkedIn profile',
    icon: <Linkedin className="w-5 h-5" />,
  },
  {
    type: 'portfolio_intro',
    name: 'Portfolio Introduction',
    description: 'A creative introduction for your portfolio or personal website',
    icon: <Globe className="w-5 h-5" />,
  },
];

export default function ContentGenerator({ brandId, brand, onContentGenerated }: ContentGeneratorProps) {
  const [selectedSurfaces, setSelectedSurfaces] = useState<SurfaceType[]>([
    'cv_summary',
    'linkedin_summary',
    'portfolio_intro',
  ]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [targetLength, setTargetLength] = useState<'concise' | 'standard' | 'detailed'>('standard');

  const toggleSurface = (surface: SurfaceType) => {
    setSelectedSurfaces((prev) =>
      prev.includes(surface)
        ? prev.filter((s) => s !== surface)
        : [...prev, surface]
    );
  };

  const handleGenerate = async () => {
    if (selectedSurfaces.length === 0) {
      setError('Please select at least one surface to generate content for');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/brand/${brandId}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          surface_types: selectedSurfaces,
          generation_preferences: {
            emphasis_themes: [],
            target_length: targetLength,
            include_achievements: true,
          },
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate content');
      }

      const result: ContentGenerationResponse = await response.json();
      onContentGenerated(result.generated_content);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 flex items-center mb-4">
        <Wand2 className="w-6 h-6 mr-2 text-blue-600" />
        Generate Branded Content
      </h2>
      <p className="text-gray-600 mb-6">
        Create consistent, professional content across multiple platforms using your established brand.
      </p>

      {/* Surface Selection */}
      <div className="space-y-3 mb-6">
        <label className="block text-sm font-medium text-gray-700">
          Select surfaces to generate
        </label>
        {SURFACE_OPTIONS.map((surface) => (
          <label
            key={surface.type}
            className={`flex items-start p-4 border rounded-lg cursor-pointer transition-colors ${
              selectedSurfaces.includes(surface.type)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:bg-gray-50'
            }`}
          >
            <input
              type="checkbox"
              checked={selectedSurfaces.includes(surface.type)}
              onChange={() => toggleSurface(surface.type)}
              className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <div className="ml-3 flex-1">
              <div className="flex items-center">
                <span className="text-gray-400 mr-2">{surface.icon}</span>
                <span className="font-medium text-gray-900">{surface.name}</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">{surface.description}</p>
            </div>
          </label>
        ))}
      </div>

      {/* Length Preference */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Content Length
        </label>
        <div className="flex gap-3">
          {(['concise', 'standard', 'detailed'] as const).map((length) => (
            <button
              key={length}
              onClick={() => setTargetLength(length)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                targetLength === length
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {length.charAt(0).toUpperCase() + length.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={selectedSurfaces.length === 0 || isGenerating}
        className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
          selectedSurfaces.length === 0 || isGenerating
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700'
        }`}
      >
        {isGenerating ? (
          <span className="flex items-center justify-center">
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            Generating Content...
          </span>
        ) : (
          <span className="flex items-center justify-center">
            <Wand2 className="w-5 h-5 mr-2" />
            Generate {selectedSurfaces.length} Surface{selectedSurfaces.length !== 1 ? 's' : ''}
          </span>
        )}
      </button>

      {/* Performance Note */}
      <p className="mt-4 text-xs text-center text-gray-500">
        Content generation typically completes in under 30 seconds
      </p>
    </div>
  );
}
