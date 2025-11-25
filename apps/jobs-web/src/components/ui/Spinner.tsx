import { forwardRef } from 'react';

export type SpinnerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type SpinnerVariant = 'primary' | 'secondary' | 'white';

export interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: SpinnerSize;
  variant?: SpinnerVariant;
  label?: string;
}

const sizeStyles: Record<SpinnerSize, string> = {
  xs: 'w-3 h-3 border-2',
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-3',
  xl: 'w-12 h-12 border-4',
};

const variantStyles: Record<SpinnerVariant, string> = {
  primary: 'border-blue-600 border-t-transparent',
  secondary: 'border-gray-600 border-t-transparent',
  white: 'border-white border-t-transparent',
};

export const Spinner = forwardRef<HTMLDivElement, SpinnerProps>(
  (
    {
      size = 'md',
      variant = 'primary',
      label,
      className = '',
      ...props
    },
    ref
  ) => {
    return (
      <div ref={ref} className={`inline-flex items-center gap-2 ${className}`} {...props}>
        <div
          className={`
            animate-spin rounded-full
            ${sizeStyles[size]}
            ${variantStyles[variant]}
          `.trim().replace(/\s+/g, ' ')}
          role="status"
          aria-label={label || 'Loading'}
        >
          <span className="sr-only">{label || 'Loading...'}</span>
        </div>
        {label && <span className="text-sm text-gray-600">{label}</span>}
      </div>
    );
  }
);

Spinner.displayName = 'Spinner';
