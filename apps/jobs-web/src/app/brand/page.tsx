'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Sparkles } from 'lucide-react';
import BrandAnalyzer from '@/components/brand/BrandAnalyzer';
import BrandOverviewDisplay from '@/components/brand/BrandOverview';
import ContentGenerator from '@/components/brand/ContentGenerator';
import GeneratedContentDisplay from '@/components/brand/GeneratedContent';
import { BrandAnalysisResponse, BrandOverview, GeneratedContent, SurfaceType } from '@/types/brand';

type PageStep = 'analyze' | 'overview' | 'generate' | 'content';

export default function BrandPage() {
  const [currentStep, setCurrentStep] = useState<PageStep>('analyze');
  const [brandId, setBrandId] = useState<string | null>(null);
  const [brandOverview, setBrandOverview] = useState<BrandOverview | null>(null);
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent[]>([]);

  const handleBrandCreated = (id: string, response: BrandAnalysisResponse) => {
    setBrandId(id);
    setBrandOverview(response.brand_overview);
    setCurrentStep('overview');
  };

  const handleContentGenerated = (content: GeneratedContent[]) => {
    setGeneratedContent(content);
    setCurrentStep('content');
  };

  const handleRegenerate = async (generationId: string, surfaceType: SurfaceType) => {
    // In a full implementation, this would call the regenerate API
    console.log('Regenerating', generationId, surfaceType);
  };

  const handleRate = async (generationId: string, rating: number) => {
    if (!brandId) return;
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await fetch(`${apiUrl}/brand/${brandId}/rating?rating=${rating}&generation_id=${generationId}`, {
        method: 'POST',
      });
    } catch (err) {
      console.error('Failed to submit rating', err);
    }
  };

  const renderStepIndicator = () => {
    const steps = [
      { key: 'analyze', label: 'Analyze' },
      { key: 'overview', label: 'Review Brand' },
      { key: 'generate', label: 'Generate' },
      { key: 'content', label: 'Content' },
    ];

    const currentIndex = steps.findIndex((s) => s.key === currentStep);

    return (
      <div className="flex items-center justify-center mb-8">
        {steps.map((step, index) => (
          <div key={step.key} className="flex items-center">
            <div
              className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                index <= currentIndex
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {index + 1}
            </div>
            <span
              className={`ml-2 text-sm ${
                index <= currentIndex ? 'text-gray-900 font-medium' : 'text-gray-500'
              }`}
            >
              {step.label}
            </span>
            {index < steps.length - 1 && (
              <div
                className={`w-16 h-0.5 mx-4 ${
                  index < currentIndex ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Link
                href="/"
                className="flex items-center text-gray-600 hover:text-gray-900 mr-6"
              >
                <ArrowLeft className="w-5 h-5 mr-1" />
                Back
              </Link>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <Sparkles className="w-7 h-7 mr-2 text-blue-600" />
                AI Brand Roadmap
              </h1>
            </div>
            {brandId && currentStep !== 'analyze' && (
              <button
                onClick={() => {
                  setBrandId(null);
                  setBrandOverview(null);
                  setGeneratedContent([]);
                  setCurrentStep('analyze');
                }}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Start Over
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {renderStepIndicator()}

        {/* Step: Analyze */}
        {currentStep === 'analyze' && (
          <BrandAnalyzer onBrandCreated={handleBrandCreated} />
        )}

        {/* Step: Overview */}
        {currentStep === 'overview' && brandOverview && (
          <div className="space-y-6">
            <BrandOverviewDisplay brand={brandOverview} />
            <div className="flex justify-center gap-4">
              <button
                onClick={() => setCurrentStep('analyze')}
                className="px-6 py-3 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Re-analyze
              </button>
              <button
                onClick={() => setCurrentStep('generate')}
                className="px-6 py-3 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Continue to Content Generation
              </button>
            </div>
          </div>
        )}

        {/* Step: Generate */}
        {currentStep === 'generate' && brandId && brandOverview && (
          <div className="grid lg:grid-cols-2 gap-8">
            <div>
              <ContentGenerator
                brandId={brandId}
                brand={brandOverview}
                onContentGenerated={handleContentGenerated}
              />
            </div>
            <div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Brand Summary
                </h3>
                <div className="space-y-4">
                  <div>
                    <span className="text-sm text-gray-500">Career Focus</span>
                    <p className="font-medium text-gray-900">
                      {brandOverview.narrative_arc.career_focus}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Value Proposition</span>
                    <p className="font-medium text-gray-900">
                      {brandOverview.narrative_arc.value_proposition}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Top Themes</span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {brandOverview.professional_themes.slice(0, 3).map((theme) => (
                        <span
                          key={theme.theme_id}
                          className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded-full"
                        >
                          {theme.theme_name}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step: Content */}
        {currentStep === 'content' && brandId && (
          <div className="space-y-6">
            <GeneratedContentDisplay
              content={generatedContent}
              brandId={brandId}
              onRegenerate={handleRegenerate}
              onRate={handleRate}
            />
            <div className="flex justify-center gap-4">
              <button
                onClick={() => setCurrentStep('generate')}
                className="px-6 py-3 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Generate More
              </button>
              <button
                onClick={() => setCurrentStep('overview')}
                className="px-6 py-3 text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
              >
                Edit Brand
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            AI Brand Roadmap – From Task-Level ML to One-Click Professional Branding
          </p>
        </div>
      </footer>
    </div>
  );
}
