'use client';

import { useEffect, useState, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import PageHeader from '@/components/PageHeader';
import JobFilters from '@/components/JobFilters';
import SelectionActionBar from '@/components/SelectionActionBar';
import JobCard from '@/components/JobCard';
import JobGridCard from '@/components/JobGridCard';
import JobListControls, { SortField, SortOrder, ViewMode } from '@/components/JobListControls';
import Pagination from '@/components/Pagination';
import { Job, Cluster, JobFilters as JobFiltersType } from '@/types';
import { Spinner } from '@/components/ui';

function JobListContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isInitialized, setIsInitialized] = useState(false);

  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<JobFiltersType>({
    location: '',
    skill_name: '',
    cluster_id: '',
  });
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [selectedJobs, setSelectedJobs] = useState<Set<string>>(new Set());
  const [favoriteJobs, setFavoriteJobs] = useState<Set<string>>(new Set());
  const [hiddenJobs, setHiddenJobs] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [sortField, setSortField] = useState<SortField>('date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

  // Initialize state from URL query params
  useEffect(() => {
    const location = searchParams.get('location') || '';
    const skill = searchParams.get('skill') || '';
    const cluster = searchParams.get('cluster') || '';
    const sort = searchParams.get('sort') as SortField || 'date';
    const order = searchParams.get('order') as SortOrder || 'desc';
    const view = searchParams.get('view') as ViewMode || null;
    const page = parseInt(searchParams.get('page') || '1', 10);

    setFilters({ location, skill_name: skill, cluster_id: cluster });
    setSortField(sort);
    setSortOrder(order);
    setCurrentPage(page);
    
    // Only override viewMode from URL if no localStorage preference exists
    const savedViewMode = localStorage.getItem('viewMode');
    if (view && !savedViewMode) {
      setViewMode(view);
    }

    setIsInitialized(true);
  }, []);

  // Update URL when state changes
  useEffect(() => {
    if (!isInitialized) return;

    const params = new URLSearchParams();
    if (filters.location) params.set('location', filters.location);
    if (filters.skill_name) params.set('skill', filters.skill_name);
    if (filters.cluster_id) params.set('cluster', filters.cluster_id);
    if (sortField !== 'date') params.set('sort', sortField);
    if (sortOrder !== 'desc') params.set('order', sortOrder);
    if (viewMode !== 'list') params.set('view', viewMode);
    if (currentPage !== 1) params.set('page', currentPage.toString());

    const queryString = params.toString();
    const newUrl = queryString ? `/?${queryString}` : '/';
    router.replace(newUrl, { scroll: false });
  }, [filters, sortField, sortOrder, viewMode, currentPage, isInitialized, router]);

  // Load preferences from localStorage
  useEffect(() => {
    const savedFavorites = localStorage.getItem('favoriteJobs');
    const savedHidden = localStorage.getItem('hiddenJobs');
    const savedViewMode = localStorage.getItem('viewMode');
    
    if (savedFavorites) setFavoriteJobs(new Set(JSON.parse(savedFavorites)));
    if (savedHidden) setHiddenJobs(new Set(JSON.parse(savedHidden)));
    if (savedViewMode) setViewMode(savedViewMode as ViewMode);
  }, []);

  // Save preferences to localStorage
  useEffect(() => {
    localStorage.setItem('favoriteJobs', JSON.stringify(Array.from(favoriteJobs)));
  }, [favoriteJobs]);

  useEffect(() => {
    localStorage.setItem('hiddenJobs', JSON.stringify(Array.from(hiddenJobs)));
  }, [hiddenJobs]);

  useEffect(() => {
    localStorage.setItem('viewMode', viewMode);
  }, [viewMode]);

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

  const fetchJobs = useCallback(async () => {
    // Only show loading spinner on initial fetch (when jobs is empty)
    if (jobs.length === 0) {
      setLoading(true);
    }
    
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
  }, [filters, jobs.length]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1); // Reset to page 1 when filters change
  };

  const handleClearFilters = () => {
    setFilters({ location: '', skill_name: '', cluster_id: '' });
    setCurrentPage(1); // Reset to page 1 when clearing filters
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

  const toggleFavorite = (jobId: string) => {
    setFavoriteJobs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(jobId)) {
        newSet.delete(jobId);
      } else {
        newSet.add(jobId);
      }
      return newSet;
    });
  };

  const toggleHidden = (jobId: string) => {
    setHiddenJobs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(jobId)) {
        newSet.delete(jobId);
      } else {
        newSet.add(jobId);
      }
      return newSet;
    });
  };

  const handleSortChange = (field: SortField, order: SortOrder) => {
    setSortField(field);
    setSortOrder(order);
    setCurrentPage(1);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Sort and filter jobs
  const getSortedAndFilteredJobs = () => {
    let filtered = [...jobs];

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortField) {
        case 'date':
          comparison = new Date(a.job_posted_date).getTime() - new Date(b.job_posted_date).getTime();
          break;
        case 'title':
          comparison = a.job_title.localeCompare(b.job_title);
          break;
        case 'skills':
          comparison = (a.skills_count || 0) - (b.skills_count || 0);
          break;
        case 'company':
          comparison = a.company_name.localeCompare(b.company_name);
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    // Prioritize favorites, then regular, then hidden
    filtered.sort((a, b) => {
      const aFavorite = favoriteJobs.has(a.job_posting_id);
      const bFavorite = favoriteJobs.has(b.job_posting_id);
      const aHidden = hiddenJobs.has(a.job_posting_id);
      const bHidden = hiddenJobs.has(b.job_posting_id);

      if (aFavorite && !bFavorite) return -1;
      if (!aFavorite && bFavorite) return 1;
      if (aHidden && !bHidden) return 1;
      if (!aHidden && bHidden) return -1;
      return 0;
    });

    return filtered;
  };

  const sortedJobs = getSortedAndFilteredJobs();
  const paginatedJobs = sortedJobs.slice((currentPage - 1) * pageSize, currentPage * pageSize);

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
          onClearFilters={handleClearFilters}
        />

        <JobListControls
          viewMode={viewMode}
          sortField={sortField}
          sortOrder={sortOrder}
          totalJobs={sortedJobs.length}
          currentPage={currentPage}
          pageSize={pageSize}
          onViewModeChange={setViewMode}
          onSortChange={handleSortChange}
          onPageChange={handlePageChange}
        />

        <SelectionActionBar
          selectedCount={selectedJobs.size}
          onGenerateReport={generateReport}
        />

        {loading ? (
          <div className="text-center py-12">
            <Spinner size="lg" label="Loading jobs..." />
          </div>
        ) : (
          <>
            {sortedJobs.length === 0 ? (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <p className="text-gray-500">No jobs found. Try adjusting your filters.</p>
              </div>
            ) : viewMode === 'grid' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {paginatedJobs.map(job => (
                  <JobGridCard
                    key={job.job_posting_id}
                    job={job}
                    isSelected={selectedJobs.has(job.job_posting_id)}
                    isFavorite={favoriteJobs.has(job.job_posting_id)}
                    isHidden={hiddenJobs.has(job.job_posting_id)}
                    onToggleSelection={toggleJobSelection}
                    onToggleFavorite={toggleFavorite}
                    onToggleHidden={toggleHidden}
                  />
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {paginatedJobs.map(job => (
                  <JobCard
                    key={job.job_posting_id}
                    job={job}
                    isSelected={selectedJobs.has(job.job_posting_id)}
                    isFavorite={favoriteJobs.has(job.job_posting_id)}
                    isHidden={hiddenJobs.has(job.job_posting_id)}
                    onToggleSelection={toggleJobSelection}
                    onToggleFavorite={toggleFavorite}
                    onToggleHidden={toggleHidden}
                  />
                ))}
              </div>
            )}

            {/* Bottom Pagination */}
            {!loading && sortedJobs.length > 0 && (
              <div className="mt-8 flex justify-center">
                <Pagination
                  currentPage={currentPage}
                  totalJobs={sortedJobs.length}
                  pageSize={pageSize}
                  onPageChange={handlePageChange}
                />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    }>
      <JobListContent />
    </Suspense>
  );
}
