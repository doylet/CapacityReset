import { Switch as HeadlessSwitch, Description, Label } from '@headlessui/react';

export type SwitchSize = 'sm' | 'md' | 'lg';
export type SwitchVariant = 'primary' | 'success' | 'danger';

export interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  size?: SwitchSize;
  variant?: SwitchVariant;
  disabled?: boolean;
  className?: string;
}

const sizeStyles: Record<SwitchSize, { switch: string; toggle: string }> = {
  sm: {
    switch: 'h-5 w-9',
    toggle: 'h-4 w-4',
  },
  md: {
    switch: 'h-6 w-11',
    toggle: 'h-5 w-5',
  },
  lg: {
    switch: 'h-7 w-14',
    toggle: 'h-6 w-6',
  },
};

const variantStyles: Record<SwitchVariant, string> = {
  primary: 'bg-blue-600',
  success: 'bg-green-600',
  danger: 'bg-red-600',
};

export const Switch = ({
  checked,
  onChange,
  label,
  description,
  size = 'md',
  variant = 'primary',
  disabled = false,
  className = '',
}: SwitchProps) => {
  const sizes = sizeStyles[size];
  
  return (
    <div className={`flex items-start gap-3 ${className}`}>
      <HeadlessSwitch
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        className={`
          ${sizes.switch}
          relative inline-flex items-center rounded-full
          transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
          disabled:opacity-50 disabled:cursor-not-allowed
          ${checked ? variantStyles[variant] : 'bg-gray-200'}
        `.trim().replace(/\s+/g, ' ')}
      >
        <span className="sr-only">{label || 'Toggle'}</span>
        <span
          className={`
            ${sizes.toggle}
            inline-block transform rounded-full bg-white shadow-lg ring-0 
            transition-transform
            ${checked ? (size === 'sm' ? 'translate-x-4' : size === 'md' ? 'translate-x-5' : 'translate-x-7') : 'translate-x-1'}
          `.trim().replace(/\s+/g, ' ')}
        />
      </HeadlessSwitch>
      
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

Switch.displayName = 'Switch';
