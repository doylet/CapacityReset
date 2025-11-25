import { Input as HeadlessInput } from '@headlessui/react';
import { forwardRef } from 'react';

export type InputVariant = 'default' | 'filled' | 'flushed';
export type InputSize = 'sm' | 'md' | 'lg';

export interface InputProps extends Omit<React.ComponentPropsWithoutRef<'input'>, 'size'> {
  variant?: InputVariant;
  inputSize?: InputSize;
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

const variantStyles: Record<InputVariant, string> = {
  default: 'border border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-500',
  filled: 'border-0 bg-gray-100 rounded-lg focus:bg-white focus:ring-2 focus:ring-blue-500',
  flushed: 'border-0 border-b-2 border-gray-300 rounded-none focus:border-blue-500',
};

const sizeStyles: Record<InputSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-5 py-3 text-lg',
};

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      variant = 'default',
      inputSize = 'md',
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className = '',
      disabled,
      type = 'text',
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
        
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {leftIcon}
            </div>
          )}
          
          <HeadlessInput
            as="input"
            type={type}
            ref={ref}
            disabled={disabled}
            className={`
              ${baseStyles}
              ${variantStyles[variant]}
              ${sizeStyles[inputSize]}
              ${errorStyles}
              ${leftIcon ? 'pl-10' : ''}
              ${rightIcon ? 'pr-10' : ''}
              ${fullWidth ? 'w-full' : ''}
              ${className}
            `.trim().replace(/\s+/g, ' ')}
            {...props}
          />
          
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
              {rightIcon}
            </div>
          )}
        </div>
        
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

Input.displayName = 'Input';
