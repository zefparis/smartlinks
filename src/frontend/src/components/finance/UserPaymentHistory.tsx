/**
 * UserPaymentHistory Component
 * Shows payment history for a specific user
 */

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { StatusBadge } from './StatusBadge';
import { Download, Search, Eye, Receipt, Calendar } from 'lucide-react';
import { format } from 'date-fns';
import { usePayments } from '../../hooks/useFinance';
import type { Payment } from '../../services/finance';

interface UserPaymentHistoryProps {
  userId?: string;
  userEmail?: string;
}

export function UserPaymentHistory({ userId, userEmail }: UserPaymentHistoryProps) {
  const [searchTerm, setSearchTerm] = useState(userEmail || '');
  const [currentUserId, setCurrentUserId] = useState(userId);
  const [timeRange, setTimeRange] = useState<'all' | '30d' | '90d' | '1y'>('all');

  const { data, isLoading } = usePayments({
    user_id: currentUserId,
    search: searchTerm,
    // Add time range filter based on selection
    from_date: timeRange !== 'all' ? getDateFromRange(timeRange) : undefined,
  });

  function getDateFromRange(range: string): string {
    const now = new Date();
    switch (range) {
      case '30d':
        now.setDate(now.getDate() - 30);
        break;
      case '90d':
        now.setDate(now.getDate() - 90);
        break;
      case '1y':
        now.setFullYear(now.getFullYear() - 1);
        break;
    }
    return now.toISOString().split('T')[0];
  }

  const handleSearch = () => {
    // In a real app, this would search for user by email/ID
    console.log('Searching for user:', searchTerm);
  };

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount / 100);
  };

  const calculateStats = (payments: Payment[]) => {
    const total = payments.reduce((sum, p) => sum + p.amount, 0);
    const successful = payments.filter(p => p.status === 'captured');
    const failed = payments.filter(p => p.status === 'failed');
    const refunded = payments.filter(p => p.status === 'refunded');
    
    return {
      total,
      count: payments.length,
      successful: successful.length,
      failed: failed.length,
      refunded: refunded.length,
      avgAmount: payments.length > 0 ? total / payments.length : 0,
      totalRefunded: refunded.reduce((sum, p) => sum + p.amount, 0),
    };
  };

  const payments = data?.payments || [];
  const stats = calculateStats(payments);

  const downloadReceipt = (payment: Payment) => {
    // Generate and download receipt
    console.log('Downloading receipt for:', payment.payment_id);
  };

  const viewDetails = (payment: Payment) => {
    // Open payment details modal
    console.log('Viewing details for:', payment.payment_id);
  };

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <Card>
        <CardHeader>
          <CardTitle>User Payment History</CardTitle>
          <CardDescription>
            Search and view payment history for a specific user
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Enter user email or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-9"
              />
            </div>
            <Button onClick={handleSearch}>Search</Button>
          </div>
        </CardContent>
      </Card>

      {/* User Stats */}
      {payments.length > 0 && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Spent</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatAmount(stats.total, 'USD')}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.count} payments
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Average Payment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatAmount(stats.avgAmount, 'USD')}
              </div>
              <p className="text-xs text-muted-foreground">
                per transaction
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.count > 0 
                  ? ((stats.successful / stats.count) * 100).toFixed(1) 
                  : 0}%
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.failed} failed
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Refunded</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatAmount(stats.totalRefunded, 'USD')}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.refunded} refunds
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Payment History */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Payment Transactions</CardTitle>
              <CardDescription>
                {payments.length > 0 
                  ? `Showing ${payments.length} transactions`
                  : 'No transactions found'}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Tabs value={timeRange} onValueChange={(v) => setTimeRange(v as any)}>
                <TabsList>
                  <TabsTrigger value="all">All Time</TabsTrigger>
                  <TabsTrigger value="30d">30 Days</TabsTrigger>
                  <TabsTrigger value="90d">90 Days</TabsTrigger>
                  <TabsTrigger value="1y">1 Year</TabsTrigger>
                </TabsList>
              </Tabs>
              {payments.length > 0 && (
                <Button variant="outline" size="sm">
                  <Download className="mr-2 h-4 w-4" />
                  Export
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Payment ID</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Method</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {payments.map((payment) => (
                <TableRow key={payment.payment_id}>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3 text-muted-foreground" />
                      <span>{format(new Date(payment.date), 'MMM dd, yyyy')}</span>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {payment.payment_id.slice(0, 8)}...
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
                  <TableCell className="max-w-[200px] truncate">
                    {payment.description || '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => viewDetails(payment)}
                        title="View Details"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      {payment.status === 'captured' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => downloadReceipt(payment)}
                          title="Download Receipt"
                        >
                          <Receipt className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {payments.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground">
                    {searchTerm 
                      ? 'No payments found for this user'
                      : 'Enter a user email or ID to view payment history'}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
