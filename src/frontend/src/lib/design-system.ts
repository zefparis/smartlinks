/**
 * SmartLinks Design System
 * Unified design tokens and utilities for consistent UI
 */

export const colors = {
  // Primary palette
  primary: {
    50: 'rgb(239 246 255)',
    100: 'rgb(219 234 254)',
    200: 'rgb(191 219 254)',
    300: 'rgb(147 197 253)',
    400: 'rgb(96 165 250)',
    500: 'rgb(59 130 246)',
    600: 'rgb(37 99 235)',
    700: 'rgb(29 78 216)',
    800: 'rgb(30 64 175)',
    900: 'rgb(30 58 138)',
    950: 'rgb(23 37 84)',
  },
  
  // Status colors
  status: {
    success: 'rgb(34 197 94)',
    warning: 'rgb(251 146 60)',
    error: 'rgb(239 68 68)',
    info: 'rgb(59 130 246)',
  },
  
  // Semantic colors for light/dark mode
  semantic: {
    background: {
      light: 'rgb(255 255 255)',
      dark: 'rgb(17 24 39)',
    },
    surface: {
      light: 'rgb(249 250 251)',
      dark: 'rgb(31 41 55)',
    },
    border: {
      light: 'rgb(229 231 235)',
      dark: 'rgb(55 65 81)',
    },
    text: {
      primary: {
        light: 'rgb(17 24 39)',
        dark: 'rgb(243 244 246)',
      },
      secondary: {
        light: 'rgb(107 114 128)',
        dark: 'rgb(156 163 175)',
      },
    },
  },
};

export const spacing = {
  xs: '0.5rem',   // 8px
  sm: '0.75rem',  // 12px
  md: '1rem',     // 16px
  lg: '1.5rem',   // 24px
  xl: '2rem',     // 32px
  '2xl': '3rem',  // 48px
  '3xl': '4rem',  // 64px
};

export const borderRadius = {
  sm: '0.25rem',  // 4px
  md: '0.375rem', // 6px
  lg: '0.5rem',   // 8px
  xl: '0.75rem',  // 12px
  '2xl': '1rem',  // 16px
  full: '9999px',
};

export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
};

export const typography = {
  fontFamily: {
    sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    mono: '"JetBrains Mono", "SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
  },
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem',// 30px
    '4xl': '2.25rem', // 36px
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};

export const animations = {
  duration: {
    fast: '150ms',
    base: '200ms',
    slow: '300ms',
    slower: '500ms',
  },
  easing: {
    ease: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
};

// Utility classes for consistent styling
export const classes = {
  // Card styles
  card: {
    base: 'bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700',
    hover: 'hover:shadow-md transition-shadow duration-200',
    padding: 'p-4 sm:p-6',
  },
  
  // Button styles
  button: {
    base: 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
    sizes: {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-sm',
      lg: 'px-6 py-3 text-base',
    },
    variants: {
      primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
      secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600',
      outline: 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-transparent dark:text-gray-300 dark:hover:bg-gray-800',
      danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
      success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500',
    },
  },
  
  // Input styles
  input: {
    base: 'block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
    error: 'border-red-300 focus:border-red-500 focus:ring-red-500',
  },
  
  // Table styles
  table: {
    container: 'overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg',
    header: 'bg-gray-50 dark:bg-gray-800',
    headerCell: 'px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider',
    body: 'bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700',
    cell: 'px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100',
  },
  
  // Modal styles
  modal: {
    overlay: 'fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 transition-opacity',
    container: 'fixed inset-0 z-50 overflow-y-auto',
    content: 'relative bg-white dark:bg-gray-800 rounded-lg shadow-xl',
    header: 'px-6 py-4 border-b border-gray-200 dark:border-gray-700',
    body: 'px-6 py-4',
    footer: 'px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3',
  },
  
  // Badge styles
  badge: {
    base: 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
    variants: {
      success: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      info: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      neutral: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
    },
  },
  
  // Layout styles
  layout: {
    container: 'mx-auto max-w-7xl px-4 sm:px-6 lg:px-8',
    section: 'py-6 sm:py-8',
    grid: {
      cols2: 'grid grid-cols-1 gap-4 sm:grid-cols-2',
      cols3: 'grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3',
      cols4: 'grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4',
    },
  },
};

// Helper function to combine classes
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

// Theme-aware color getter
export function getThemeColor(
  colorPath: string,
  isDark: boolean
): string {
  const paths = colorPath.split('.');
  let value: any = colors;
  
  for (const path of paths) {
    value = value[path];
    if (!value) return '';
  }
  
  if (typeof value === 'object' && ('light' in value || 'dark' in value)) {
    return isDark ? value.dark : value.light;
  }
  
  return value;
}
