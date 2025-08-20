import * as React from 'react';

// Lightweight shadcn-like tooltip without external deps (fallback)
// API: <TooltipProvider><Tooltip><TooltipTrigger asChild>...</TooltipTrigger><TooltipContent>...</TooltipContent></Tooltip></TooltipProvider>

const TooltipContext = React.createContext<{ open: boolean; setOpen: (v: boolean) => void } | null>(null);

export function TooltipProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

export function Tooltip({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false);
  return <TooltipContext.Provider value={{ open, setOpen }}>{children}</TooltipContext.Provider>;
}

export function TooltipTrigger({ asChild = false, children }: { asChild?: boolean; children: React.ReactNode }) {
  const ctx = React.useContext(TooltipContext);
  if (!ctx) return <>{children}</>;
  const props = {
    onMouseEnter: () => ctx.setOpen(true),
    onMouseLeave: () => ctx.setOpen(false),
    onFocus: () => ctx.setOpen(true),
    onBlur: () => ctx.setOpen(false),
  } as any;
  if (asChild && React.isValidElement(children)) return React.cloneElement(children as any, props);
  return (
    <button {...props} className="bg-transparent">
      {children}
    </button>
  );
}

export function TooltipContent({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  const ctx = React.useContext(TooltipContext);
  if (!ctx) return null;
  return ctx.open ? (
    <div className={`z-50 -mt-1 select-none rounded-md border bg-white px-2 py-1 text-xs text-gray-700 shadow ${className}`}>
      {children}
    </div>
  ) : null;
}
