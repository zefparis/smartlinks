/**
 * StatusBadge Component
 * Displays colored badges for various payment/payout statuses
 */

import { Badge } from '../ui/badge';
import { cn } from '../../lib/utils';

export type PaymentStatus = 'pending' | 'captured' | 'failed' | 'refunded' | 'disputed';
export type PayoutStatus = 'proposed' | 'paid' | 'failed' | 'cancelled';

interface StatusBadgeProps {
  status: PaymentStatus | PayoutStatus | string;
  className?: string;
}

const statusConfig: Record<string, { label: string; className: string }> = {
  // Payment statuses
  pending: {
    label: 'Pending',
    className: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  },
  captured: {
    label: 'Captured',
    className: 'bg-green-100 text-green-800 border-green-300',
  },
  failed: {
    label: 'Failed',
    className: 'bg-red-100 text-red-800 border-red-300',
  },
  refunded: {
    label: 'Refunded',
    className: 'bg-purple-100 text-purple-800 border-purple-300',
  },
  disputed: {
    label: 'Disputed',
    className: 'bg-orange-100 text-orange-800 border-orange-300',
  },
  // Payout statuses
  proposed: {
    label: 'Proposed',
    className: 'bg-blue-100 text-blue-800 border-blue-300',
  },
  paid: {
    label: 'Paid',
    className: 'bg-green-100 text-green-800 border-green-300',
  },
  cancelled: {
    label: 'Cancelled',
    className: 'bg-gray-100 text-gray-800 border-gray-300',
  },
  // Generic
  success: {
    label: 'Success',
    className: 'bg-green-100 text-green-800 border-green-300',
  },
  error: {
    label: 'Error',
    className: 'bg-red-100 text-red-800 border-red-300',
  },
  warning: {
    label: 'Warning',
    className: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  },
  info: {
    label: 'Info',
    className: 'bg-blue-100 text-blue-800 border-blue-300',
  },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status.toLowerCase()] || {
    label: status,
    className: 'bg-gray-100 text-gray-800 border-gray-300',
  };

  return (
    <Badge className={cn(config.className, 'font-medium', className)} variant="outline">
      {config.label}
    </Badge>
  );
}
