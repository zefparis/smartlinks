import React from 'react';

export type StatusLevel = 'active' | 'warning' | 'down';

const COLORS: Record<StatusLevel, string> = {
  active: 'bg-green-500',
  warning: 'bg-amber-500',
  down: 'bg-red-500',
};

export default function StatusIndicator({ status, label, className = '' }: { status: StatusLevel; label?: string; className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className={`inline-block w-3 h-3 rounded-full ${COLORS[status]}`} aria-label={status} />
      {label && <span className="text-sm text-gray-700">{label}</span>}
    </div>
  );
}
