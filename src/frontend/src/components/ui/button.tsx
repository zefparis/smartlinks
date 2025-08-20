import * as React from 'react';
import { cn } from '@/lib/utils';

const variantStyles = {
  default: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
  destructive: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  outline: 'border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700',
  secondary: 'bg-gray-800 text-white hover:bg-gray-700 focus:ring-gray-500',
  ghost: 'bg-transparent text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700',
  link: 'bg-transparent text-blue-600 dark:text-blue-400 underline-offset-4 hover:underline',
};

const sizeStyles = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-11 px-5 text-base',
};

export function buttonVariants({
  variant = 'default',
  size = 'md',
  className = ''
}: {
  variant?: keyof typeof variantStyles;
  size?: keyof typeof sizeStyles;
  className?: string;
} = {}) {
  const base = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none';
  return cn(base, variantStyles[variant], sizeStyles[size], className);
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variantStyles;
  size?: keyof typeof sizeStyles;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => (
    <button ref={ref} className={buttonVariants({ variant, size, className })} {...props} />
  )
);
Button.displayName = 'Button';
