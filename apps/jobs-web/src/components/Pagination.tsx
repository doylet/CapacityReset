'use client';

import { Button } from '@/components/ui/Button';

interface PaginationProps {
  currentPage: number;
  totalJobs: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({
  currentPage,
  totalJobs,
  pageSize,
  onPageChange,
}: PaginationProps) {
  if (totalJobs === 0) return null;

  const totalPages = Math.ceil(totalJobs / pageSize);
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalJobs);

  return (
    <div className="flex items-center gap-4">
      <span className="text-sm text-gray-600">
        Showing {startItem}-{endItem} of {totalJobs}
      </span>
      
      <div className="flex items-center gap-1">
        <Button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          variant="outline"
          size="sm"
        >
          Previous
        </Button>
        
        <div className="flex items-center gap-1">
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            let pageNum;
            if (totalPages <= 5) {
              pageNum = i + 1;
            } else if (currentPage <= 3) {
              pageNum = i + 1;
            } else if (currentPage >= totalPages - 2) {
              pageNum = totalPages - 4 + i;
            } else {
              pageNum = currentPage - 2 + i;
            }
            
            return (
              <Button
                key={pageNum}
                onClick={() => onPageChange(pageNum)}
                variant={currentPage === pageNum ? 'primary' : 'outline'}
                size="sm"
              >
                {pageNum}
              </Button>
            );
          })}
        </div>
        
        <Button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          variant="outline"
          size="sm"
        >
          Next
        </Button>
      </div>
    </div>
  );
}
