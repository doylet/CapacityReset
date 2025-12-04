'use client';

import { useState, useEffect } from 'react';
import { Search, Filter, MapPin, Tag } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';

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
  onClearFilters: () => void;
}

export default function JobFilters({
  filters,
  clusters,
  onFilterChange,
  onClearFilters,
}: JobFiltersProps) {
  // Local state for debounced inputs
  const [localLocation, setLocalLocation] = useState(filters.location);
  const [localSkill, setLocalSkill] = useState(filters.skill_name);

  // Sync local state with props when cleared externally
  useEffect(() => {
    setLocalLocation(filters.location);
    setLocalSkill(filters.skill_name);
  }, [filters.location, filters.skill_name]);

  // Debounce location filter
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localLocation !== filters.location) {
        onFilterChange('location', localLocation);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [localLocation]);

  // Debounce skill filter
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localSkill !== filters.skill_name) {
        onFilterChange('skill_name', localSkill);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [localSkill]);

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-5 h-5 text-gray-600" />
        <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-1">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <MapPin className="w-4 h-4 inline mr-1" />
            Location
          </label>
          <Input
            placeholder="e.g., Sydney"
            value={localLocation}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLocalLocation(e.target.value)}
            leftIcon={<MapPin className="w-4 h-4" />}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Search className="w-4 h-4 inline mr-1" />
            Skill Name
          </label>
          <Input
            placeholder="e.g., Python"
            value={localSkill}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLocalSkill(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Tag className="w-4 h-4 inline mr-1" />
            Cluster
          </label>
          <Select
            value={filters.cluster_id}
            onChange={(value) => onFilterChange('cluster_id', value)}
            options={[
              { value: '', label: 'All Clusters' },
              ...clusters.map(cluster => ({
                value: cluster.cluster_id.toString(),
                label: `${cluster.cluster_name} (${cluster.cluster_size})`
              }))
            ]}
          />
        </div>
      </div>

      {(filters.location || filters.skill_name || filters.cluster_id) && (
        <div className="mt-4">
          <Button
            onClick={onClearFilters}
            variant="secondary"
            size="sm"
          >
            Clear Filters
          </Button>
        </div>
      )}
    </div>
  );
}
