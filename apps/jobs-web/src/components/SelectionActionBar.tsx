'use client';

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
      <button
        onClick={onGenerateReport}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
      >
        Generate ML Report
      </button>
    </div>
  );
}
