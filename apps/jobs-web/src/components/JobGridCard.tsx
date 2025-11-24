'use client';

import Link from 'next/link';
import { Calendar, MapPin, Tag, Star, EyeOff } from 'lucide-react';
import { format } from 'date-fns';
import { Job } from '@/types';

interface JobGridCardProps {
  job: Job;
  isSelected: boolean;
  isFavorite: boolean;
  isHidden: boolean;
  onToggleSelection: (jobId: string) => void;
  onToggleFavorite: (jobId: string) => void;
  onToggleHidden: (jobId: string) => void;
}

export default function JobGridCard({
  job,
  isSelected,
  isFavorite,
  isHidden,
  onToggleSelection,
  onToggleFavorite,
  onToggleHidden,
}: JobGridCardProps) {
  return (
    <div
      className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-4 ${
        isSelected ? 'ring-2 ring-blue-500' : ''
      } ${isHidden ? 'opacity-50' : ''}`}
    >
      {/* Header with checkbox and actions */}
      <div className="flex items-start justify-between mb-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onToggleSelection(job.job_posting_id)}
          className="mt-0.5 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        
        <div className="flex items-center gap-1">
          <button
            onClick={() => onToggleFavorite(job.job_posting_id)}
            className={`p-1 rounded hover:bg-gray-100 ${
              isFavorite ? 'text-yellow-500' : 'text-gray-400'
            }`}
            title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
          >
            <Star className={`w-4 h-4 ${isFavorite ? 'fill-current' : ''}`} />
          </button>
          <button
            onClick={() => onToggleHidden(job.job_posting_id)}
            className={`p-1 rounded hover:bg-gray-100 ${
              isHidden ? 'text-gray-600' : 'text-gray-400'
            }`}
            title={isHidden ? 'Show job' : 'Hide job'}
          >
            <EyeOff className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Job Info */}
      <Link href={`/jobs/${job.job_posting_id}`}>
        <h3 className="text-base font-semibold text-gray-900 hover:text-blue-600 cursor-pointer mb-1 line-clamp-2">
          {job.job_title}
        </h3>
      </Link>
      
      <div className="flex items-center gap-2 mb-2">
        {job.company_logo && (
          <img 
            src={job.company_logo} 
            alt={`${job.company_name} logo`} 
            className="h-4 w-4 object-contain"
          />
        )}
        {job.company_url ? (
          <a
            href={job.company_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:text-blue-800 hover:underline line-clamp-1"
            onClick={(e) => e.stopPropagation()}
          >
            {job.company_name}
          </a>
        ) : (
          <p className="text-sm text-gray-600 line-clamp-1">{job.company_name}</p>
        )}
      </div>

      <div className="flex flex-col gap-1.5 text-xs text-gray-500 mb-3">
        <span className="flex items-center gap-1">
          <MapPin className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">{job.job_location}</span>
        </span>
        <span className="flex items-center gap-1">
          <Calendar className="w-3 h-3 flex-shrink-0" />
          {format(new Date(job.job_posted_date), 'MMM d, yyyy')}
        </span>
        {(job.skills_count ?? 0) > 0 && (
          <span className="flex items-center gap-1">
            <Tag className="w-3 h-3 flex-shrink-0" />
            {job.skills_count} skills
          </span>
        )}
      </div>

      <p className="text-sm text-gray-700 line-clamp-3 mb-3">
        {job.job_summary}
      </p>

      {job.cluster && (
        <div>
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            {job.cluster.cluster_name}
          </span>
        </div>
      )}
    </div>
  );
}
