/**
 * PaymentsTable Component
 * Displays payments with filtering, sorting, and actions
 */

import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Skeleton } from '../ui/skeleton';
import { StatusBadge } from './StatusBadge';
import { Eye, RefreshCw, Download, Search, Filter } from 'lucide-react';
import { format } from 'date-fns';
import type { Payment } from '../../services/finance';

interface PaymentsTableProps {
  payments: Payment[];
  total: number;
  loading?: boolean;
  onViewDetails: (payment: Payment) => void;
  onRefund: (payment: Payment) => void;
  onExport: () => void;
  onFiltersChange: (filters: any) => void;
  currentFilters: any;
}

export function PaymentsTable({
  payments,
  total,
  loading,
  onViewDetails,
  onRefund,
  onExport,
  onFiltersChange,
  currentFilters,
}: PaymentsTableProps) {
  const [searchTerm, setSearchTerm] = useState(currentFilters.search || '');
  const [showFilters, setShowFilters] = useState(false);

  const handleSearch = () => {
    onFiltersChange({ ...currentFilters, search: searchTerm });
  };

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount / 100);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters Bar */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-1 gap-2">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search payments..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="pl-9"
            />
          </div>
          <Button variant="outline" onClick={handleSearch}>
            Search
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4" />
          </Button>
        </div>
        <Button variant="outline" onClick={onExport}>
          <Download className="mr-2 h-4 w-4" />
          Export CSV
        </Button>
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="grid gap-4 rounded-lg border p-4 md:grid-cols-4">
          <Select
            value={currentFilters.status || 'all'}
            onValueChange={(value) =>
              onFiltersChange({ ...currentFilters, status: value === 'all' ? undefined : value })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="captured">Captured</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="refunded">Refunded</SelectItem>
              <SelectItem value="disputed">Disputed</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={currentFilters.provider || 'all'}
            onValueChange={(value) =>
              onFiltersChange({ ...currentFilters, provider: value === 'all' ? undefined : value })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Provider" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Providers</SelectItem>
              <SelectItem value="stripe_cards">Stripe</SelectItem>
              <SelectItem value="paypal">PayPal</SelectItem>
            </SelectContent>
          </Select>

          <Input
            type="date"
            placeholder="From Date"
            value={currentFilters.from_date || ''}
            onChange={(e) =>
              onFiltersChange({ ...currentFilters, from_date: e.target.value })
            }
          />

          <Input
            type="date"
            placeholder="To Date"
            value={currentFilters.to_date || ''}
            onChange={(e) =>
              onFiltersChange({ ...currentFilters, to_date: e.target.value })
            }
          />
        </div>
      )}

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Payment ID</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Provider</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Fees</TableHead>
              <TableHead>Net</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {payments.map((payment) => (
              <TableRow key={payment.payment_id}>
                <TableCell className="font-mono text-sm">
                  {payment.payment_id.slice(0, 8)}...
                </TableCell>
                <TableCell>
                  {format(new Date(payment.date), 'MMM dd, yyyy HH:mm')}
                </TableCell>
                <TableCell className="font-medium">
                  {formatAmount(payment.amount, payment.currency)}
                </TableCell>
                <TableCell className="capitalize">
                  {payment.provider.replace('_', ' ')}
                </TableCell>
                <TableCell>
                  <StatusBadge status={payment.status} />
                </TableCell>
                <TableCell>
                  {payment.fees
                    ? formatAmount(payment.fees, payment.currency)
                    : '-'}
                </TableCell>
                <TableCell>
                  {payment.net_amount
                    ? formatAmount(payment.net_amount, payment.currency)
                    : '-'}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewDetails(payment)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    {payment.status === 'captured' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onRefund(payment)}
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {payments.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-muted-foreground">
                  No payments found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Info */}
      <div className="text-sm text-muted-foreground">
        Showing {payments.length} of {total} payments
      </div>
    </div>
  );
}
