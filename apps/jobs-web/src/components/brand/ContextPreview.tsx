'use client';

import { useState, useEffect, useMemo } from 'react';
import { SurfaceType, BrandOverview, ProfessionalSurface, GeneratedContent } from '@/types/brand';
import { 
  Eye, 
  Settings, 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  RefreshCw, 
  Maximize2, 
  Minimize2,
  Target,
  BarChart3,
  Zap,
  Shield,
  Layers
} from 'lucide-react';

interface ContextAnalysis {
  surface_type: string;
  context_score: number;
  adaptation_recommendations: string[];
  divergence_points: string[];
  consistency_risks: string[];
  optimization_opportunities: string[];
  confidence_level: number;
}

interface CrossSurfaceContextMap {
  surface_contexts: Record<string, ContextAnalysis>;
  shared_themes: string[];
  divergent_aspects: Array<{
    aspect: string;
    description: string;
    affected_surfaces: string[];
    severity: string;
  }>;
  consistency_score: number;
  adaptation_strategy: Record<string, any>;
  resolution_recommendations: string[];
}

interface ContextPreviewProps {
  brand: BrandOverview;
  surfaces: ProfessionalSurface[];
  selectedSurfaces: SurfaceType[];
  existingContent?: GeneratedContent[];
  onContextUpdate?: (contextMap: CrossSurfaceContextMap) => void;
  onSurfaceOptimization?: (surfaceType: SurfaceType, optimizations: string[]) => void;
  isLoading?: boolean;
  className?: string;
}

const SURFACE_NAMES: Record<SurfaceType, string> = {
  cv_summary: 'CV Professional Summary',
  linkedin_summary: 'LinkedIn Summary',
  portfolio_intro: 'Portfolio Introduction',
};

const SURFACE_COLORS: Record<SurfaceType, string> = {
  cv_summary: 'border-blue-200 bg-blue-50',
  linkedin_summary: 'border-blue-600 bg-blue-100',
  portfolio_intro: 'border-purple-200 bg-purple-50',
};

const SEVERITY_COLORS = {
  low: 'text-green-600 bg-green-100',
  medium: 'text-orange-600 bg-orange-100',
  high: 'text-red-600 bg-red-100',
};

export default function ContextPreview({
  brand,
  surfaces,
  selectedSurfaces,
  existingContent = [],
  onContextUpdate,
  onSurfaceOptimization,
  isLoading = false,
  className = '',
}: ContextPreviewProps) {
  const [contextMap, setContextMap] = useState<CrossSurfaceContextMap | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedSurfacePreview, setSelectedSurfacePreview] = useState<SurfaceType | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [previewMode, setPreviewMode] = useState<'overview' | 'detailed'>('overview');

  // Filter surfaces to only those selected
  const filteredSurfaces = useMemo(() => 
    surfaces.filter(surface => 
      selectedSurfaces.includes(surface.surface_type as SurfaceType)
    ),
    [surfaces, selectedSurfaces]
  );

  // Analyze context when surfaces or brand change
  useEffect(() => {
    if (filteredSurfaces.length > 0 && brand) {
      analyzeContext();
    }
  }, [filteredSurfaces, brand]);

  const analyzeContext = async () => {
    setIsAnalyzing(true);
    
    try {
      // Simulate context analysis - in production would call API
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const mockContextMap: CrossSurfaceContextMap = {
        surface_contexts: Object.fromEntries(
          filteredSurfaces.map(surface => [
            surface.surface_type,
            {
              surface_type: surface.surface_type,
              context_score: 0.75 + Math.random() * 0.2,
              adaptation_recommendations: getAdaptationRecommendations(surface.surface_type as SurfaceType, brand),
              divergence_points: getDivergencePoints(surface.surface_type as SurfaceType),
              consistency_risks: getConsistencyRisks(surface.surface_type as SurfaceType),
              optimization_opportunities: getOptimizationOpportunities(surface.surface_type as SurfaceType),
              confidence_level: 0.8 + Math.random() * 0.15,
            }
          ])
        ),
        shared_themes: brand.professional_themes.slice(0, 3).map(theme => theme.theme_name),
        divergent_aspects: getDivergentAspects(filteredSurfaces),
        consistency_score: 0.82 + Math.random() * 0.15,
        adaptation_strategy: {
          primary_approach: 'theme_consistency_first',
          shared_theme_emphasis: brand.professional_themes.slice(0, 3).map(theme => theme.theme_name),
          consistency_checkpoints: ['voice_characteristics_alignment', 'core_theme_representation']
        },
        resolution_recommendations: getResolutionRecommendations(filteredSurfaces)
      };
      
      setContextMap(mockContextMap);
      onContextUpdate?.(mockContextMap);
      
    } catch (error) {
      console.error('Context analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSurfaceOptimization = (surfaceType: SurfaceType) => {
    const surfaceContext = contextMap?.surface_contexts[surfaceType];
    if (surfaceContext) {
      onSurfaceOptimization?.(surfaceType, surfaceContext.optimization_opportunities);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 0.8) return <CheckCircle2 className="w-4 h-4 text-green-600" />;
    if (score >= 0.6) return <AlertTriangle className="w-4 h-4 text-orange-600" />;
    return <AlertTriangle className="w-4 h-4 text-red-600" />;
  };

  if (isLoading || isAnalyzing) {
    return (
      <div className={`border rounded-lg p-6 bg-gray-50 ${className}`}>
        <div className="flex items-center justify-center space-y-4">
          <div className="text-center">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600 mb-2" />
            <p className="text-gray-600">Analyzing context requirements...</p>
            <p className="text-sm text-gray-500 mt-1">
              Evaluating cross-surface consistency and optimization opportunities
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!contextMap) {
    return (
      <div className={`border rounded-lg p-6 bg-gray-50 ${className}`}>
        <div className="text-center">
          <Settings className="w-6 h-6 mx-auto text-gray-400 mb-2" />
          <p className="text-gray-600">Context analysis not available</p>
          <button
            onClick={analyzeContext}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Analyze Context
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`border rounded-lg bg-white ${className}`}>
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Eye className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Context Adaptation Preview</h3>
              <p className="text-sm text-gray-600">
                Cross-surface consistency and optimization analysis
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-600">Consistency Score:</span>
              <div className={`flex items-center gap-1 font-semibold ${getScoreColor(contextMap.consistency_score)}`}>
                {getScoreIcon(contextMap.consistency_score)}
                {(contextMap.consistency_score * 100).toFixed(1)}%
              </div>
            </div>
            
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </div>
        </div>
        
        {/* Mode Toggle */}
        <div className="flex items-center gap-2 mt-3">
          <button
            onClick={() => setPreviewMode('overview')}
            className={`px-3 py-1 text-sm rounded-lg transition-colors ${
              previewMode === 'overview' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setPreviewMode('detailed')}
            className={`px-3 py-1 text-sm rounded-lg transition-colors ${
              previewMode === 'detailed' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Detailed Analysis
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {previewMode === 'overview' ? (
          <OverviewMode 
            contextMap={contextMap}
            filteredSurfaces={filteredSurfaces}
            onSurfaceOptimization={handleSurfaceOptimization}
            isExpanded={isExpanded}
          />
        ) : (
          <DetailedMode 
            contextMap={contextMap}
            filteredSurfaces={filteredSurfaces}
            selectedSurface={selectedSurfacePreview}
            onSurfaceSelect={setSelectedSurfacePreview}
            onSurfaceOptimization={handleSurfaceOptimization}
            isExpanded={isExpanded}
          />
        )}
      </div>
    </div>
  );
}

// Overview Mode Component
function OverviewMode({ 
  contextMap, 
  filteredSurfaces, 
  onSurfaceOptimization, 
  isExpanded 
}: {
  contextMap: CrossSurfaceContextMap;
  filteredSurfaces: ProfessionalSurface[];
  onSurfaceOptimization: (surfaceType: SurfaceType) => void;
  isExpanded: boolean;
}) {
  return (
    <div className="space-y-4">
      {/* Shared Themes */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <Layers className="w-4 h-4 text-green-600" />
          <h4 className="font-medium text-green-800">Shared Brand Themes</h4>
        </div>
        <div className="flex flex-wrap gap-2">
          {contextMap.shared_themes.map((theme, index) => (
            <span key={index} className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm">
              {theme}
            </span>
          ))}
        </div>
      </div>

      {/* Surface Context Scores */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {filteredSurfaces.map((surface) => {
          const context = contextMap.surface_contexts[surface.surface_type];
          const surfaceType = surface.surface_type as SurfaceType;
          
          return (
            <div key={surface.surface_id} className={`border rounded-lg p-4 ${SURFACE_COLORS[surfaceType]}`}>
              <div className="flex items-center justify-between mb-2">
                <h5 className="font-medium text-gray-900">{SURFACE_NAMES[surfaceType]}</h5>
                <div className={`flex items-center gap-1 text-sm font-semibold ${getScoreColor(context.context_score)}`}>
                  {getScoreIcon(context.context_score)}
                  {(context.context_score * 100).toFixed(0)}%
                </div>
              </div>
              
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-600">Adaptations needed:</span>
                  <span className="ml-1 font-medium">{context.adaptation_recommendations.length}</span>
                </div>
                
                <div>
                  <span className="text-gray-600">Optimization opportunities:</span>
                  <span className="ml-1 font-medium">{context.optimization_opportunities.length}</span>
                </div>
                
                {context.optimization_opportunities.length > 0 && (
                  <button
                    onClick={() => onSurfaceOptimization(surfaceType)}
                    className="w-full mt-2 px-3 py-1 bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors text-sm"
                  >
                    <Zap className="w-3 h-3 inline mr-1" />
                    Optimize Surface
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Divergent Aspects */}
      {isExpanded && contextMap.divergent_aspects.length > 0 && (
        <div className="border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-orange-600" />
            <h4 className="font-medium text-gray-900">Context Divergences</h4>
          </div>
          
          <div className="space-y-3">
            {contextMap.divergent_aspects.map((aspect, index) => (
              <div key={index} className="border-l-4 border-orange-200 pl-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-gray-900">{aspect.aspect.replace('_', ' ')}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${SEVERITY_COLORS[aspect.severity as keyof typeof SEVERITY_COLORS]}`}>
                    {aspect.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{aspect.description}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Affects: {aspect.affected_surfaces.join(', ')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Resolution Recommendations */}
      {isExpanded && contextMap.resolution_recommendations.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-blue-600" />
            <h4 className="font-medium text-blue-800">Resolution Recommendations</h4>
          </div>
          
          <ul className="space-y-1 text-sm">
            {contextMap.resolution_recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
                <span className="text-blue-700">{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// Detailed Mode Component
function DetailedMode({ 
  contextMap, 
  filteredSurfaces, 
  selectedSurface, 
  onSurfaceSelect, 
  onSurfaceOptimization,
  isExpanded 
}: {
  contextMap: CrossSurfaceContextMap;
  filteredSurfaces: ProfessionalSurface[];
  selectedSurface: SurfaceType | null;
  onSurfaceSelect: (surface: SurfaceType | null) => void;
  onSurfaceOptimization: (surfaceType: SurfaceType) => void;
  isExpanded: boolean;
}) {
  return (
    <div className="space-y-4">
      {/* Surface Selector */}
      <div className="flex flex-wrap gap-2">
        {filteredSurfaces.map((surface) => {
          const surfaceType = surface.surface_type as SurfaceType;
          const isSelected = selectedSurface === surfaceType;
          const context = contextMap.surface_contexts[surfaceType];
          
          return (
            <button
              key={surface.surface_id}
              onClick={() => onSurfaceSelect(isSelected ? null : surfaceType)}
              className={`px-4 py-2 rounded-lg border transition-colors ${
                isSelected 
                  ? 'border-blue-500 bg-blue-100 text-blue-700' 
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <span>{SURFACE_NAMES[surfaceType]}</span>
                <div className={`flex items-center gap-1 text-xs ${getScoreColor(context.context_score)}`}>
                  {getScoreIcon(context.context_score)}
                  {(context.context_score * 100).toFixed(0)}%
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Detailed Surface Analysis */}
      {selectedSurface && (
        <SurfaceDetailedAnalysis 
          surface={filteredSurfaces.find(s => s.surface_type === selectedSurface)!}
          context={contextMap.surface_contexts[selectedSurface]}
          onOptimize={() => onSurfaceOptimization(selectedSurface)}
        />
      )}

      {/* Cross-Surface Analysis */}
      {!selectedSurface && (
        <div className="space-y-4">
          <div className="text-center text-gray-500 py-8">
            <BarChart3 className="w-8 h-8 mx-auto mb-2" />
            <p>Select a surface above to view detailed analysis</p>
          </div>
        </div>
      )}
    </div>
  );
}

// Surface Detailed Analysis Component
function SurfaceDetailedAnalysis({ 
  surface, 
  context, 
  onOptimize 
}: {
  surface: ProfessionalSurface;
  context: ContextAnalysis;
  onOptimize: () => void;
}) {
  const surfaceType = surface.surface_type as SurfaceType;
  
  return (
    <div className={`border rounded-lg p-4 ${SURFACE_COLORS[surfaceType]}`}>
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-gray-900">{SURFACE_NAMES[surfaceType]} Analysis</h4>
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-1 text-sm font-semibold ${getScoreColor(context.context_score)}`}>
            {getScoreIcon(context.context_score)}
            Context Score: {(context.context_score * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">
            Confidence: {(context.confidence_level * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Adaptations */}
        <div className="bg-white rounded-lg p-3 border">
          <h5 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
            <Settings className="w-4 h-4 text-gray-600" />
            Required Adaptations
          </h5>
          {context.adaptation_recommendations.length > 0 ? (
            <ul className="space-y-1 text-sm">
              {context.adaptation_recommendations.map((rec, index) => (
                <li key={index} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 flex-shrink-0" />
                  <span className="text-gray-700">{rec}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 italic">No adaptations required</p>
          )}
        </div>

        {/* Opportunities */}
        <div className="bg-white rounded-lg p-3 border">
          <h5 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
            <Zap className="w-4 h-4 text-green-600" />
            Optimization Opportunities
          </h5>
          {context.optimization_opportunities.length > 0 ? (
            <ul className="space-y-1 text-sm">
              {context.optimization_opportunities.map((opp, index) => (
                <li key={index} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                  <span className="text-gray-700">{opp}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 italic">No optimization opportunities identified</p>
          )}
        </div>

        {/* Consistency Risks */}
        <div className="bg-white rounded-lg p-3 border">
          <h5 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
            <Shield className="w-4 h-4 text-orange-600" />
            Consistency Risks
          </h5>
          {context.consistency_risks.length > 0 ? (
            <ul className="space-y-1 text-sm">
              {context.consistency_risks.map((risk, index) => (
                <li key={index} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 bg-orange-500 rounded-full mt-2 flex-shrink-0" />
                  <span className="text-gray-700">{risk}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 italic">No consistency risks identified</p>
          )}
        </div>

        {/* Divergence Points */}
        <div className="bg-white rounded-lg p-3 border">
          <h5 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
            <Info className="w-4 h-4 text-blue-600" />
            Context Divergences
          </h5>
          {context.divergence_points.length > 0 ? (
            <ul className="space-y-1 text-sm">
              {context.divergence_points.map((point, index) => (
                <li key={index} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                  <span className="text-gray-700">{point}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 italic">No significant divergences</p>
          )}
        </div>
      </div>

      {/* Optimize Button */}
      {context.optimization_opportunities.length > 0 && (
        <button
          onClick={onOptimize}
          className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
        >
          <Zap className="w-4 h-4" />
          Apply Optimizations
        </button>
      )}
    </div>
  );
}

// Helper functions for mock data
function getAdaptationRecommendations(surfaceType: SurfaceType, brand: BrandOverview): string[] {
  const baseRecommendations = {
    cv_summary: [
      'Emphasize quantifiable achievements',
      'Use professional third-person tone',
      'Integrate industry-specific keywords'
    ],
    linkedin_summary: [
      'Adopt conversational first-person narrative',
      'Include call-to-action for networking',
      'Balance personal and professional elements'
    ],
    portfolio_intro: [
      'Showcase creative vision and unique approach',
      'Include portfolio preview elements',
      'Emphasize client value proposition'
    ]
  };

  return baseRecommendations[surfaceType] || [];
}

function getDivergencePoints(surfaceType: SurfaceType): string[] {
  return [
    'Tone formality varies from brand baseline',
    'Content length exceeds optimal range'
  ];
}

function getConsistencyRisks(surfaceType: SurfaceType): string[] {
  return [
    'Platform-specific adaptations may dilute core brand message',
    'Surface audience expectations may conflict with brand voice'
  ];
}

function getOptimizationOpportunities(surfaceType: SurfaceType): string[] {
  const opportunities = {
    cv_summary: [
      'Leverage strong technical themes for ATS optimization',
      'Incorporate industry leadership keywords'
    ],
    linkedin_summary: [
      'Enhance networking appeal with thought leadership elements',
      'Optimize for LinkedIn algorithm with engagement hooks'
    ],
    portfolio_intro: [
      'Align content with visual portfolio themes',
      'Strengthen client value proposition messaging'
    ]
  };

  return opportunities[surfaceType] || [];
}

function getDivergentAspects(surfaces: ProfessionalSurface[]): Array<{
  aspect: string;
  description: string;
  affected_surfaces: string[];
  severity: string;
}> {
  return [
    {
      aspect: 'tone_formality',
      description: 'Varying formality levels across surfaces may create inconsistent brand perception',
      affected_surfaces: surfaces.map(s => s.surface_type),
      severity: 'medium'
    }
  ];
}

function getResolutionRecommendations(surfaces: ProfessionalSurface[]): string[] {
  return [
    'Establish consistent voice characteristics across all surfaces',
    'Maintain core value proposition in all content variations',
    'Balance surface-specific optimizations with brand coherence'
  ];
}

function getScoreColor(score: number): string {
  if (score >= 0.8) return 'text-green-600';
  if (score >= 0.6) return 'text-orange-600';
  return 'text-red-600';
}

function getScoreIcon(score: number): JSX.Element {
  if (score >= 0.8) return <CheckCircle2 className="w-4 h-4 text-green-600" />;
  if (score >= 0.6) return <AlertTriangle className="w-4 h-4 text-orange-600" />;
  return <AlertTriangle className="w-4 h-4 text-red-600" />;
}