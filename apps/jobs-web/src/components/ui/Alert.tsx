import { Description } from '@headlessui/react';
import { forwardRef } from 'react';
import { AlertCircle, CheckCircle, Info, XCircle, X } from 'lucide-react';

export type AlertVariant = 'info' | 'success' | 'warning' | 'error';

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
  title?: string;
  closable?: boolean;
  onClose?: () => void;
  icon?: React.ReactNode;
}

const variantStyles: Record<AlertVariant, { container: string; icon: string }> = {
  info: {
    container: 'bg-blue-50 border-blue-200 text-blue-800',
    icon: 'text-blue-600',
  },
  success: {
    container: 'bg-green-50 border-green-200 text-green-800',
    icon: 'text-green-600',
  },
  warning: {
    container: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    icon: 'text-yellow-600',
  },
  error: {
    container: 'bg-red-50 border-red-200 text-red-800',
    icon: 'text-red-600',
  },
};

const defaultIcons: Record<AlertVariant, React.ReactNode> = {
  info: <Info className="w-5 h-5" />,
  success: <CheckCircle className="w-5 h-5" />,
  warning: <AlertCircle className="w-5 h-5" />,
  error: <XCircle className="w-5 h-5" />,
};

export const Alert = forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      variant = 'info',
      title,
      closable = false,
      onClose,
      icon,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    const styles = variantStyles[variant];
    const displayIcon = icon !== undefined ? icon : defaultIcons[variant];
    
    return (
      <div
        ref={ref}
        className={`
          relative flex gap-3 p-4 border rounded-lg
          ${styles.container}
          ${className}
        `.trim().replace(/\s+/g, ' ')}
        role="alert"
        {...props}
      >
        {displayIcon && (
          <div className={`flex-shrink-0 ${styles.icon}`}>
            {displayIcon}
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          {title && (
            <h5 className="font-semibold mb-1">{title}</h5>
          )}
          <Description className="text-sm">{children}</Description>
        </div>
        
        {closable && (
          <button
            type="button"
            onClick={onClose}
            className="flex-shrink-0 ml-auto hover:opacity-70 transition-opacity"
            aria-label="Close alert"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }
);

Alert.displayName = 'Alert';
