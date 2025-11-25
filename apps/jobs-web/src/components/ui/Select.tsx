import { Listbox, ListboxButton, ListboxOptions, ListboxOption, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { Check, ChevronDown } from 'lucide-react';

export type SelectVariant = 'default' | 'filled';
export type SelectSize = 'sm' | 'md' | 'lg';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  variant?: SelectVariant;
  size?: SelectSize;
  label?: string;
  error?: string;
  helperText?: string;
  placeholder?: string;
  fullWidth?: boolean;
  disabled?: boolean;
  className?: string;
}

const variantStyles: Record<SelectVariant, string> = {
  default: 'border border-gray-300 rounded-lg bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500',
  filled: 'border-0 bg-gray-100 rounded-lg focus:bg-white focus:ring-2 focus:ring-blue-500',
};

const sizeStyles: Record<SelectSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-5 py-3 text-lg',
};

export const Select = ({
  options,
  value,
  onChange,
  variant = 'default',
  size = 'md',
  label,
  error,
  helperText,
  placeholder = 'Select...',
  fullWidth = false,
  disabled = false,
  className = '',
}: SelectProps) => {
  const baseStyles = 'transition-all focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed';
  const errorStyles = error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : '';
  
  const selectedOption = options.find(opt => opt.value === value);
  
  return (
    <div className={fullWidth ? 'w-full' : ''}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      
      <Listbox value={value} onChange={onChange} disabled={disabled}>
        <div className="relative">
          <ListboxButton
            className={`
              ${baseStyles}
              ${variantStyles[variant]}
              ${sizeStyles[size]}
              ${errorStyles}
              ${fullWidth ? 'w-full' : ''}
              ${className}
              relative text-left pr-10
            `.trim().replace(/\s+/g, ' ')}
          >
            <span className={selectedOption ? 'block truncate' : 'block truncate text-gray-400'}>
              {selectedOption ? selectedOption.label : placeholder}
            </span>
            <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
              <ChevronDown className="h-4 w-4 text-gray-400" aria-hidden="true" />
            </span>
          </ListboxButton>
          
          <Transition
            as={Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <ListboxOptions className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
              {options.map((option) => (
                <ListboxOption
                  key={option.value}
                  value={option.value}
                  disabled={option.disabled}
                  className={({ active, selected }) =>
                    `relative cursor-pointer select-none py-2 pl-10 pr-4 ${
                      active ? 'bg-blue-100 text-blue-900' : 'text-gray-900'
                    } ${option.disabled ? 'opacity-50 cursor-not-allowed' : ''}`
                  }
                >
                  {({ selected }) => (
                    <>
                      <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                        {option.label}
                      </span>
                      {selected && (
                        <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-blue-600">
                          <Check className="h-4 w-4" aria-hidden="true" />
                        </span>
                      )}
                    </>
                  )}
                </ListboxOption>
              ))}
            </ListboxOptions>
          </Transition>
        </div>
      </Listbox>
      
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
      
      {!error && helperText && (
        <p className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
};

Select.displayName = 'Select';
