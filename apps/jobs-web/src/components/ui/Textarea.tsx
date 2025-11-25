import { Textarea as HeadlessTextarea } from '@headlessui/react';
import { forwardRef } from 'react';

export type TextareaVariant = 'default' | 'filled';
export type TextareaSize = 'sm' | 'md' | 'lg';

export interface TextareaProps extends React.ComponentPropsWithoutRef<typeof HeadlessTextarea> {
  variant?: TextareaVariant;
  textareaSize?: TextareaSize;
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
  resize?: 'none' | 'vertical' | 'horizontal' | 'both';
}

const variantStyles: Record<TextareaVariant, string> = {
  default: 'border border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-500',
  filled: 'border-0 bg-gray-100 rounded-lg focus:bg-white focus:ring-2 focus:ring-blue-500',
};

const sizeStyles: Record<TextareaSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-5 py-3 text-lg',
};

const resizeStyles: Record<string, string> = {
  none: 'resize-none',
  vertical: 'resize-y',
  horizontal: 'resize-x',
  both: 'resize',
};

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      variant = 'default',
      textareaSize = 'md',
      label,
      error,
      helperText,
      fullWidth = false,
      resize = 'vertical',
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles = 'transition-all focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed';
    const errorStyles = error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : '';
    
    return (
      <div className={fullWidth ? 'w-full' : ''}>
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        
        <HeadlessTextarea
          ref={ref}
          disabled={disabled}
          className={`
            ${baseStyles}
            ${variantStyles[variant]}
            ${sizeStyles[textareaSize]}
            ${resizeStyles[resize]}
            ${errorStyles}
            ${fullWidth ? 'w-full' : ''}
            ${className}
          `.trim().replace(/\s+/g, ' ')}
          {...props}
        />
        
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
        
        {!error && helperText && (
          <p className="mt-1 text-sm text-gray-500">{helperText}</p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
