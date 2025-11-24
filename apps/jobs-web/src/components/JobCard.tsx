'use client';

import Link from 'next/link';
import { MapPin, Calendar, Briefcase } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Job, Cluster } from '@/types';

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
      className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-6 ${
        isSelected ? 'ring-2 ring-blue-500' : ''
      } ${isHidden ? 'opacity-50' : ''}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4 flex-1">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelection(job.job_posting_id)}
            className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          
          <div className="flex-1">
            <div className="flex items-start justify-between">
              <Link href={`/jobs/${job.job_posting_id}`}>
                <h3 className="text-lg font-semibold text-gray-900 hover:text-blue-600 cursor-pointer">
                  {job.job_title}
                </h3>
              </Link>
              
              <div className="flex items-center gap-2 ml-4">
                <button
                  onClick={() => onToggleFavorite(job.job_posting_id)}
                  className={`p-1.5 rounded hover:bg-gray-100 ${
                    isFavorite ? 'text-yellow-500' : 'text-gray-400'
                  }`}
                  title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
                >
                  <Star className={`w-5 h-5 ${isFavorite ? 'fill-current' : ''}`} />
                </button>
                <button
                  onClick={() => onToggleHidden(job.job_posting_id)}
                  className={`p-1.5 rounded hover:bg-gray-100 ${
                    isHidden ? 'text-gray-600' : 'text-gray-400'
                  }`}
                  title={isHidden ? 'Show job' : 'Hide job'}
                >
                  <EyeOff className="w-5 h-5" />
                </button>
              </div>
            </div>
            <div className="flex items-center gap-3 mt-1">
              {job.company_logo && (
                <img 
                  src={job.company_logo} 
                  alt={`${job.company_name} logo`}
                  className="h-6 w-6 object-contain"
                />
              )}
              {job.company_url ? (
                <a 
                  href={job.company_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  {job.company_name}
                </a>
              ) : (
                <p className="text-sm text-gray-600">{job.company_name}</p>
              )}
            </div>
            
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {job.job_location}
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {format(new Date(job.job_posted_date), 'MMM d, yyyy')}
              </span>
              {job.skills_count && (
                <span className="flex items-center gap-1">
                  <Tag className="w-4 h-4" />
                  {job.skills_count} skills
                </span>
              )}
            </div>

            <p className="text-sm text-gray-700 mt-3 line-clamp-2">
              {job.job_summary}
            </p>

            {job.cluster && (
              <div className="mt-3">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
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
