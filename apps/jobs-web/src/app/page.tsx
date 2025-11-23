'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Search, Filter, Calendar, MapPin, Tag } from 'lucide-react';
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

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
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

  const handleApplyFilters = () => {
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
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Jobs Skills Explorer</h1>
          <p className="text-sm text-gray-600 mt-1">View and edit job skills with ML enrichment</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <MapPin className="w-4 h-4 inline mr-1" />
                Location
              </label>
              <input
                type="text"
                placeholder="e.g., Sydney"
                value={filters.location}
                onChange={(e) => handleFilterChange('location', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Search className="w-4 h-4 inline mr-1" />
                Skill Name
              </label>
              <input
                type="text"
                placeholder="e.g., Python"
                value={filters.skill_name}
                onChange={(e) => handleFilterChange('skill_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Tag className="w-4 h-4 inline mr-1" />
                Cluster
              </label>
              <select
                value={filters.cluster_id}
                onChange={(e) => handleFilterChange('cluster_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Clusters</option>
                {clusters.map(cluster => (
                  <option key={cluster.cluster_id} value={cluster.cluster_id}>
                    {cluster.cluster_name} ({cluster.cluster_size})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 flex gap-3">
            <button
              onClick={handleApplyFilters}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Apply Filters
            </button>
            <button
              onClick={() => {
                setFilters({ location: '', skill_name: '', cluster_id: '' });
                fetchJobs();
              }}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Action Bar */}
        {selectedJobs.size > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-center justify-between">
            <span className="text-sm font-medium text-blue-900">
              {selectedJobs.size} job(s) selected
            </span>
            <button
              onClick={generateReport}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
            >
              Generate ML Report
            </button>
          </div>
        )}

        {/* Jobs List */}
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
                <div
                  key={job.job_posting_id}
                  className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-6 ${
                    selectedJobs.has(job.job_posting_id) ? 'ring-2 ring-blue-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <input
                        type="checkbox"
                        checked={selectedJobs.has(job.job_posting_id)}
                        onChange={() => toggleJobSelection(job.job_posting_id)}
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
              ))
            )}
          </div>
        )}
      </main>
    </div>
  );
}
