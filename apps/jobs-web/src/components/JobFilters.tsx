'use client';

import { Search, Filter, MapPin, Tag } from 'lucide-react';

interface Cluster {
  cluster_id: number;
  cluster_name: string;
  cluster_keywords: string[];
  cluster_size: number;
}

interface JobFiltersProps {
  filters: {
    location: string;
    skill_name: string;
    cluster_id: string;
  };
  clusters: Cluster[];
  onFilterChange: (key: string, value: string) => void;
  onApplyFilters: () => void;
  onClearFilters: () => void;
}

export default function JobFilters({
  filters,
  clusters,
  onFilterChange,
  onApplyFilters,
  onClearFilters,
}: JobFiltersProps) {
  return (
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
            onChange={(e) => onFilterChange('location', e.target.value)}
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
            onChange={(e) => onFilterChange('skill_name', e.target.value)}
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
            onChange={(e) => onFilterChange('cluster_id', e.target.value)}
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
          onClick={onApplyFilters}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Apply Filters
        </button>
        <button
          onClick={onClearFilters}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
