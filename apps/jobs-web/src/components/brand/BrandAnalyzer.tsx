'use client';

import { useState, useRef } from 'react';
import { Upload, FileText, Loader2, CheckCircle } from 'lucide-react';
import { BrandAnalysisResponse } from '@/types/brand';

interface BrandAnalyzerProps {
  onBrandCreated: (brandId: string, brand: BrandAnalysisResponse) => void;
}

export default function BrandAnalyzer({ onBrandCreated }: BrandAnalyzerProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError('Please select a file to analyze');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('document', selectedFile);
      if (linkedinUrl) {
        formData.append('linkedin_profile_url', linkedinUrl);
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/brand/analysis`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to analyze document');
      }

      const result: BrandAnalysisResponse = await response.json();
      onBrandCreated(result.brand_id, result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Discover Your Professional Brand
        </h2>
        <p className="text-gray-600 mb-6">
          Upload your CV or resume to analyze your professional identity and create 
          consistent branded content across multiple platforms.
        </p>

        {/* File Upload Area */}
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : selectedFile
              ? 'border-green-500 bg-green-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            onChange={handleFileSelect}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          
          {selectedFile ? (
            <div className="flex flex-col items-center">
              <CheckCircle className="w-12 h-12 text-green-500 mb-3" />
              <p className="text-green-700 font-medium">{selectedFile.name}</p>
              <p className="text-sm text-gray-500 mt-1">
                Click or drag to replace
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <Upload className="w-12 h-12 text-gray-400 mb-3" />
              <p className="text-gray-700 font-medium">
                Drop your CV/resume here
              </p>
              <p className="text-sm text-gray-500 mt-1">
                or click to browse (PDF, DOC, DOCX, TXT)
              </p>
            </div>
          )}
        </div>

        {/* LinkedIn URL (Optional) */}
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            LinkedIn Profile URL (Optional)
          </label>
          <input
            type="url"
            value={linkedinUrl}
            onChange={(e) => setLinkedinUrl(e.target.value)}
            placeholder="https://linkedin.com/in/yourprofile"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Adding your LinkedIn profile enhances brand analysis with voice and positioning insights
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Analyze Button */}
        <button
          onClick={handleAnalyze}
          disabled={!selectedFile || isAnalyzing}
          className={`mt-6 w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
            !selectedFile || isAnalyzing
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isAnalyzing ? (
            <span className="flex items-center justify-center">
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Analyzing Your Professional Brand...
            </span>
          ) : (
            <span className="flex items-center justify-center">
              <FileText className="w-5 h-5 mr-2" />
              Analyze My Brand
            </span>
          )}
        </button>

        {/* Info Box */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-medium text-gray-900 mb-2">
            What we'll extract:
          </h3>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Professional themes and core strengths</li>
            <li>• Voice characteristics and communication style</li>
            <li>• Career narrative and value proposition</li>
            <li>• Key achievements and differentiators</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
