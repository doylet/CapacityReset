import { Transition } from '@headlessui/react';
import Link from 'next/link';
import { ArrowLeft, MapPin } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import ViewOriginalJobLink from '@/components/ViewOriginalJobLink';

interface JobHeaderProps {
  job: {
    company_logo?: string | null;
    company_name: string;
    company_url?: string | null;
    job_title: string;
    job_url?: string | null;
    job_location: string;
    job_posted_date: string;
  };
  previousJobId?: string | null;
  nextJobId?: string | null;
}

export default function JobHeader({ job }: JobHeaderProps) {
  return (
    <Transition
      show={true}
      appear={true}
      enter="transition-all duration-500"
      enterFrom="opacity-0 -translate-y-4"
      enterTo="opacity-100 translate-y-0"
    >
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <Link 
              href="/" 
              className="inline-flex items-center text-sm text-gray-600 hover:text-blue-700 transition-colors group"
            >
              <ArrowLeft className="w-4 h-4 mr-1 group-hover:-translate-x-1 transition-transform" />
              Back to Jobs
            </Link>
          </div>
          
          <div className="flex items-start gap-4">
            {/* Company Logo */}
            {job.company_logo && (
              <Transition
                show={true}
                appear={true}
                enter="transition-all duration-500 delay-100"
                enterFrom="opacity-0 scale-75"
                enterTo="opacity-100 scale-100"
              >
                <img 
                  src={job.company_logo} 
                  alt={`${job.company_name} logo`}
                  className="h-16 w-16 object-contain flex-shrink-0 rounded-lg"
                />
              </Transition>
            )}
            
            <div className="flex-1">
              {/* Job Title and External Link */}
              <div className="flex items-start justify-between gap-4 mb-1">
                <h1 className="text-2xl font-semibold text-gray-900">{job.job_title}</h1>
                
                {/* View Original Link */}
                {job.job_url && (
                  <ViewOriginalJobLink href={job.job_url} />
                )}
              </div>
              
              {/* Company Name */}
              {job.company_url ? (
                <a 
                  href={job.company_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-base text-gray-900 hover:text-blue-700 hover:underline inline-block mb-2 transition-colors"
                >
                  {job.company_name}
                </a>
              ) : (
                <p className="text-base text-gray-900 mb-2">{job.company_name}</p>
              )}
              
              {/* Job Metadata */}
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {job.job_location}
                </span>
                <span className="text-gray-400">·</span>
                <span>{formatDistanceToNow(new Date(job.job_posted_date), { addSuffix: true })}</span>
              </div>
            </div>
          </div>
        </div>
      </header>
    </Transition>
  );
}
