import { Checkbox as HeadlessCheckbox, Description, Label } from '@headlessui/react';
import { Check } from 'lucide-react';

export type CheckboxSize = 'sm' | 'md' | 'lg';
export type CheckboxVariant = 'primary' | 'success' | 'danger';

export interface CheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  size?: CheckboxSize;
  variant?: CheckboxVariant;
  disabled?: boolean;
  indeterminate?: boolean;
  className?: string;
}

const sizeStyles: Record<CheckboxSize, { box: string; icon: string }> = {
  sm: {
    box: 'h-4 w-4',
    icon: 'w-3 h-3',
  },
  md: {
    box: 'h-5 w-5',
    icon: 'w-4 h-4',
  },
  lg: {
    box: 'h-6 w-6',
    icon: 'w-5 h-5',
  },
};

const variantStyles: Record<CheckboxVariant, string> = {
  primary: 'bg-blue-600 border-blue-600',
  success: 'bg-green-600 border-green-600',
  danger: 'bg-red-600 border-red-600',
};

export const Checkbox = ({
  checked,
  onChange,
  label,
  description,
  size = 'md',
  variant = 'primary',
  disabled = false,
  indeterminate = false,
  className = '',
}: CheckboxProps) => {
  const sizes = sizeStyles[size];
  
  return (
    <div className={`flex items-start gap-3 ${className}`}>
      <HeadlessCheckbox
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        className={`
          ${sizes.box}
          flex items-center justify-center rounded border-2 
          transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
          disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer
          ${checked || indeterminate ? variantStyles[variant] : 'border-gray-300 bg-white'}
        `.trim().replace(/\s+/g, ' ')}
      >
        {(checked || indeterminate) && (
          <Check className={`${sizes.icon} text-white stroke-[3]`} />
        )}
      </HeadlessCheckbox>
      
      {(label || description) && (
        <div className="flex-1">
          {label && (
            <Label className="block text-sm font-medium text-gray-900 cursor-pointer">
              {label}
            </Label>
          )}
          {description && (
            <Description className="text-sm text-gray-500">
              {description}
            </Description>
          )}
        </div>
      )}
    </div>
  );
};

Checkbox.displayName = 'Checkbox';
