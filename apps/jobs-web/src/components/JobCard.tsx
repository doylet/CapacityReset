'use client';

import Link from 'next/link';
import { Calendar, MapPin, Tag } from 'lucide-react';
import { format } from 'date-fns';

interface Cluster {
  cluster_id: number;
  cluster_name: string;
  cluster_keywords: string[];
  cluster_size: number;
}

interface Job {
  job_posting_id: string;
  job_title: string;
  company_name: string;
  job_location: string;
  job_summary: string;
  job_posted_date: string;
  skills_count?: number;
  cluster?: Cluster;
}

interface JobCardProps {
  job: Job;
  isSelected: boolean;
  onToggleSelection: (jobId: string) => void;
}

export default function JobCard({ job, isSelected, onToggleSelection }: JobCardProps) {
  return (
    <div
      className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-6 ${
        isSelected ? 'ring-2 ring-blue-500' : ''
      }`}
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
            <Link href={`/jobs/${job.job_posting_id}`}>
              <h3 className="text-lg font-semibold text-gray-900 hover:text-blue-600 cursor-pointer">
                {job.job_title}
              </h3>
            </Link>
            <p className="text-sm text-gray-600 mt-1">{job.company_name}</p>
            
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
