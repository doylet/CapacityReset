import { Button } from '@/components/ui/Button';
import { ExternalLink } from 'lucide-react';

interface ViewOriginalJobLinkProps {
  href: string;
  variant?: 'button' | 'link';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function ViewOriginalJobLink({ 
  href, 
  variant = 'button',
  size = 'sm',
  className = ''
}: ViewOriginalJobLinkProps) {
  if (variant === 'link') {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className={`inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 hover:underline ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        <ExternalLink className="w-4 h-4" />
        View Original
      </a>
    );
  }

  return (
    <Button
      as="a"
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      variant="outline"
      size={size}
      leftIcon={<ExternalLink className="w-4 h-4" />}
      className={className}
    >
      View Original Posting
    </Button>
  );
}
