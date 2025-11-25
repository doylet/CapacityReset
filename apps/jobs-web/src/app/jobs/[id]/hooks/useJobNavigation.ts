import { useEffect, useState } from 'react';

interface JobNavigation {
  previousJobId: string | null;
  nextJobId: string | null;
  loading: boolean;
}

export function useJobNavigation(currentJobId: string, apiUrl: string): JobNavigation {
  const [previousJobId, setPreviousJobId] = useState<string | null>(null);
  const [nextJobId, setNextJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchJobList = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${apiUrl}/jobs`);
        const jobs = await response.json();
        
        const currentIndex = jobs.findIndex((job: any) => job.job_posting_id === currentJobId);
        
        if (currentIndex !== -1) {
          setPreviousJobId(currentIndex > 0 ? jobs[currentIndex - 1].job_posting_id : null);
          setNextJobId(currentIndex < jobs.length - 1 ? jobs[currentIndex + 1].job_posting_id : null);
        }
      } catch (error) {
        console.error('Error fetching job navigation:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchJobList();
  }, [currentJobId, apiUrl]);

  return { previousJobId, nextJobId, loading };
}
