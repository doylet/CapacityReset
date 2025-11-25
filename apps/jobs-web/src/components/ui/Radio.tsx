import { RadioGroup, Radio as HeadlessRadio, Label, Description } from '@headlessui/react';

export type RadioSize = 'sm' | 'md' | 'lg';
export type RadioVariant = 'primary' | 'success' | 'danger';

export interface RadioOption {
  value: string;
  label: string;
  description?: string;
  disabled?: boolean;
}

export interface RadioGroupProps {
  value: string;
  onChange: (value: string) => void;
  options: RadioOption[];
  label?: string;
  size?: RadioSize;
  variant?: RadioVariant;
  orientation?: 'vertical' | 'horizontal';
  disabled?: boolean;
  className?: string;
}

const sizeStyles: Record<RadioSize, { radio: string; dot: string }> = {
  sm: {
    radio: 'h-4 w-4',
    dot: 'h-2 w-2',
  },
  md: {
    radio: 'h-5 w-5',
    dot: 'h-2.5 w-2.5',
  },
  lg: {
    radio: 'h-6 w-6',
    dot: 'h-3 w-3',
  },
};

const variantStyles: Record<RadioVariant, string> = {
  primary: 'border-blue-600',
  success: 'border-green-600',
  danger: 'border-red-600',
};

const variantDotStyles: Record<RadioVariant, string> = {
  primary: 'bg-blue-600',
  success: 'bg-green-600',
  danger: 'bg-red-600',
};

export const Radio = ({
  value,
  onChange,
  options,
  label,
  size = 'md',
  variant = 'primary',
  orientation = 'vertical',
  disabled = false,
  className = '',
}: RadioGroupProps) => {
  const sizes = sizeStyles[size];
  
  return (
    <RadioGroup value={value} onChange={onChange} disabled={disabled} className={className}>
      {label && <Label className="block text-sm font-medium text-gray-900 mb-3">{label}</Label>}
      
      <div className={`${orientation === 'vertical' ? 'space-y-3' : 'flex flex-wrap gap-4'}`}>
        {options.map((option) => (
          <HeadlessRadio
            key={option.value}
            value={option.value}
            disabled={option.disabled}
            className="group flex items-start gap-3 cursor-pointer"
          >
            {({ checked }) => (
              <>
                <div
                  className={`
                    ${sizes.radio}
                    flex items-center justify-center rounded-full border-2 
                    transition-colors
                    group-focus:ring-2 group-focus:ring-offset-2 group-focus:ring-blue-500
                    ${option.disabled ? 'opacity-50 cursor-not-allowed' : ''}
                    ${checked ? variantStyles[variant] : 'border-gray-300'}
                  `.trim().replace(/\s+/g, ' ')}
                >
                  {checked && (
                    <div className={`${sizes.dot} rounded-full ${variantDotStyles[variant]}`} />
                  )}
                </div>
                
                <div className="flex-1">
                  <Label className="block text-sm font-medium text-gray-900 cursor-pointer">
                    {option.label}
                  </Label>
                  {option.description && (
                    <Description className="text-sm text-gray-500">
                      {option.description}
                    </Description>
                  )}
                </div>
              </>
            )}
          </HeadlessRadio>
        ))}
      </div>
    </RadioGroup>
  );
};

Radio.displayName = 'Radio';
