declare module '@radix-ui/react-tooltip' {
  import * as React from 'react';
  export const Provider: React.FC<{ delayDuration?: number; children?: React.ReactNode }>;
  export const Root: React.FC<{ children?: React.ReactNode }>;
  export const Trigger: React.ForwardRefExoticComponent<any>;
  export const Content: React.ForwardRefExoticComponent<any>;
  export const Arrow: React.FC<any>;
}
