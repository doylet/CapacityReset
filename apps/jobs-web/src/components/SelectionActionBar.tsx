'use client';

import { Button } from '@/components/ui/Button';
import { FileText } from 'lucide-react';

interface SelectionActionBarProps {
  selectedCount: number;
  onGenerateReport: () => void;
}

export default function SelectionActionBar({ selectedCount, onGenerateReport }: SelectionActionBarProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-center justify-between">
      <span className="text-sm font-medium text-blue-900">
        {selectedCount} job(s) selected
      </span>
      <Button
        onClick={onGenerateReport}
        variant="primary"
        size="sm"
        leftIcon={<FileText className="w-4 h-4" />}
      >
        Generate ML Report
      </Button>
    </div>
  );
}
