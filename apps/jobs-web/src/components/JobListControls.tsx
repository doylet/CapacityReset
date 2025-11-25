'use client';

import { Grid, List, SortAsc, SortDesc } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
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
            <Select
              value={sortField}
              onChange={(value) => handleSortFieldChange(value as SortField)}
              options={[
                { value: 'date', label: 'Date Posted' },
                { value: 'title', label: 'Job Title' },
                { value: 'skills', label: 'Skills Count' },
                { value: 'company', label: 'Company' }
              ]}
            />
            
            <Button
              onClick={() => onSortChange(sortField, sortOrder === 'asc' ? 'desc' : 'asc')}
              variant="ghost"
              size="sm"
              title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
            >
              {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
            </Button>
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-1 border border-gray-300 rounded-md p-0.5">
            <Button
              onClick={() => onViewModeChange('list')}
              variant={viewMode === 'list' ? 'primary' : 'ghost'}
              size="sm"
              title="List View"
              className="!p-1.5"
            >
              <List className="w-4 h-4" />
            </Button>
            <Button
              onClick={() => onViewModeChange('grid')}
              variant={viewMode === 'grid' ? 'primary' : 'ghost'}
              size="sm"
              title="Grid View"
              className="!p-1.5"
            >
              <Grid className="w-4 h-4" />
            </Button>
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
