'use client';

import { Grid, List, SortAsc, SortDesc } from 'lucide-react';
import Pagination from './Pagination';

export type SortField = 'date' | 'title' | 'skills' | 'company';
export type SortOrder = 'asc' | 'desc';
export type ViewMode = 'list' | 'grid';

interface JobListControlsProps {
  viewMode: ViewMode;
  sortField: SortField;
  sortOrder: SortOrder;
  totalJobs: number;
  currentPage: number;
  pageSize: number;
  onViewModeChange: (mode: ViewMode) => void;
  onSortChange: (field: SortField, order: SortOrder) => void;
  onPageChange: (page: number) => void;
}

export default function JobListControls({
  viewMode,
  sortField,
  sortOrder,
  totalJobs,
  currentPage,
  pageSize,
  onViewModeChange,
  onSortChange,
  onPageChange,
}: JobListControlsProps) {
  const handleSortFieldChange = (field: SortField) => {
    if (field === sortField) {
      // Toggle order if same field
      onSortChange(field, sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // Default to desc for new field
      onSortChange(field, 'desc');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        {/* Left: Sort and View Controls */}
        <div className="flex items-center gap-4 flex-wrap">
          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Sort by:</label>
            <select
              value={sortField}
              onChange={(e) => handleSortFieldChange(e.target.value as SortField)}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="date">Date Posted</option>
              <option value="title">Job Title</option>
              <option value="skills">Skills Count</option>
              <option value="company">Company</option>
            </select>
            
            <button
              onClick={() => onSortChange(sortField, sortOrder === 'asc' ? 'desc' : 'asc')}
              className="p-1.5 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
              title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
            >
              {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
            </button>
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-1 border border-gray-300 rounded-md p-0.5">
            <button
              onClick={() => onViewModeChange('list')}
              className={`p-1.5 rounded ${
                viewMode === 'list'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
              title="List View"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => onViewModeChange('grid')}
              className={`p-1.5 rounded ${
                viewMode === 'grid'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
              title="Grid View"
            >
              <Grid className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Right: Pagination */}
        <Pagination
          currentPage={currentPage}
          totalJobs={totalJobs}
          pageSize={pageSize}
          onPageChange={onPageChange}
        />
      </div>
    </div>
  );
}
