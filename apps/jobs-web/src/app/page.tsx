'use client';

import { useEffect, useState } from 'react';
import PageHeader from '@/components/PageHeader';
import JobFilters from '@/components/JobFilters';
import SelectionActionBar from '@/components/SelectionActionBar';
import JobCard from '@/components/JobCard';
import { Job, Cluster, JobFilters as JobFiltersType } from '@/types';

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<JobFiltersType>({
    location: '',
    skill_name: '',
    cluster_id: '',
  });
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [selectedJobs, setSelectedJobs] = useState<Set<string>>(new Set());

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

  useEffect(() => {
    fetchClusters();
    fetchJobs();
  }, []);

  const fetchClusters = async () => {
    try {
      const response = await fetch(`${API_URL}/clusters`);
      const data = await response.json();
      setClusters(data);
    } catch (error) {
      console.error('Error fetching clusters:', error);
    }
  };

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.location) params.append('location', filters.location);
      if (filters.skill_name) params.append('skill_name', filters.skill_name);
      if (filters.cluster_id) params.append('cluster_id', filters.cluster_id);
      
      const response = await fetch(`${API_URL}/jobs?${params.toString()}`);
      const data = await response.json();
      setJobs(data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleClearFilters = () => {
    setFilters({ location: '', skill_name: '', cluster_id: '' });
    fetchJobs();
  };

  const toggleJobSelection = (jobId: string) => {
    setSelectedJobs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(jobId)) {
        newSet.delete(jobId);
      } else {
        newSet.add(jobId);
      }
      return newSet;
    });
  };

  const generateReport = async () => {
    if (selectedJobs.size === 0) {
      alert('Please select at least one job');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/jobs/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_ids: Array.from(selectedJobs) }),
      });
      const report = await response.json();
      
      // Display report in modal or new page
      alert(JSON.stringify(report, null, 2));
    } catch (error) {
      console.error('Error generating report:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <JobFilters
          filters={filters}
          clusters={clusters}
          onFilterChange={handleFilterChange}
          onApplyFilters={fetchJobs}
          onClearFilters={handleClearFilters}
        />

        <SelectionActionBar
          selectedCount={selectedJobs.size}
          onGenerateReport={generateReport}
        />

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            <p className="mt-2 text-gray-600">Loading jobs...</p>
          </div>
        ) : (
          <div className="space-y-4">
            {jobs.length === 0 ? (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <p className="text-gray-500">No jobs found. Try adjusting your filters.</p>
              </div>
            ) : (
              jobs.map(job => (
                <JobCard
                  key={job.job_posting_id}
                  job={job}
                  isSelected={selectedJobs.has(job.job_posting_id)}
                  onToggleSelection={toggleJobSelection}
                />
              ))
            )}
          </div>
        )}
      </main>
    </div>
  );
}
