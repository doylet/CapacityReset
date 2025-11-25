'use client';

import Link from 'next/link';
import { MapPin, Calendar, Briefcase, Star, EyeOff, Tag } from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import { Job, Cluster } from '@/types';
import ViewOriginalJobLink from './ViewOriginalJobLink';

interface JobCardProps {
  job: Job;
  isSelected: boolean;
  isFavorite: boolean;
  isHidden: boolean;
  onToggleSelection: (jobId: string) => void;
  onToggleFavorite: (jobId: string) => void;
  onToggleHidden: (jobId: string) => void;
}

export default function JobCard({
  job,
  isSelected,
  isFavorite,
  isHidden,
  onToggleSelection,
  onToggleFavorite,
  onToggleHidden,
}: JobCardProps) {
  return (
    <div
      className={`bg-white border border-gray-200 rounded-lg hover:shadow-lg transition-all duration-200 ${
        isSelected ? 'ring-2 ring-blue-600 border-blue-600' : ''
      } ${isHidden ? 'opacity-50' : ''}`}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelection(job.job_posting_id)}
            className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          
          {/* Company Logo */}
          {job.company_logo && (
            <img 
              src={job.company_logo} 
              alt={`${job.company_name} logo`}
              className="h-14 w-14 object-contain mt-1"
            />
          )}
          
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <Link href={`/jobs/${job.job_posting_id}`}>
                  <h3 className="text-base font-semibold text-blue-700 hover:underline cursor-pointer line-clamp-2">
                    {job.job_title}
                  </h3>
                </Link>
                
                {/* Company Name */}
                {job.company_url ? (
                  <a 
                    href={job.company_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-sm text-gray-900 hover:text-blue-700 hover:underline mt-0.5 inline-block"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {job.company_name}
                  </a>
                ) : (
                  <p className="text-sm text-gray-900 mt-0.5">{job.company_name}</p>
                )}
                
                {/* Location and Date */}
                <div className="flex items-center gap-1 mt-1 text-sm text-gray-600">
                  <span>{job.job_location}</span>
                  <span className="text-gray-400">·</span>
                  <span>{formatDistanceToNow(new Date(job.job_posted_date), { addSuffix: true })}</span>
                  {job.skills_count && (
                    <>
                      <span className="text-gray-400">·</span>
                      <span>{job.skills_count} skills</span>
                    </>
                  )}
                </div>
              </div>
              
              {/* Action buttons */}
              <div className="flex items-center gap-1">
                {job.job_url && (
                  <ViewOriginalJobLink 
                    href={job.job_url} 
                    variant="link" 
                  />
                )}
                <button
                  onClick={() => onToggleFavorite(job.job_posting_id)}
                  className={`p-2 rounded-full hover:bg-gray-100 transition-colors ${
                    isFavorite ? 'text-yellow-600' : 'text-gray-500'
                  }`}
                  title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
                >
                  <Star className={`w-5 h-5 ${isFavorite ? 'fill-current' : ''}`} />
                </button>
                <button
                  onClick={() => onToggleHidden(job.job_posting_id)}
                  className={`p-2 rounded-full hover:bg-gray-100 transition-colors ${
                    isHidden ? 'text-gray-700' : 'text-gray-500'
                  }`}
                  title={isHidden ? 'Show job' : 'Hide job'}
                >
                  <EyeOff className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Job Summary */}
            <p className="text-sm text-gray-700 mt-2 line-clamp-2">
              {job.job_summary}
            </p>

            {/* Cluster Badge */}
            {job.cluster && (
              <div className="mt-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                  {job.cluster.cluster_name}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
