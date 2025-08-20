/**
 * Payments Page
 * Dedicated page for payments management
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { PaymentsTable } from '../../components/finance/PaymentsTable';
import { RefundModal } from '../../components/finance/RefundModal';
import { usePayments, useRefundPayment, useExportPaymentsCSV } from '../../hooks/useFinance';
import type { Payment } from '../../services/finance';

export function PaymentsPage() {
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [refundModalOpen, setRefundModalOpen] = useState(false);
  const [filters, setFilters] = useState({
    status: undefined,
    provider: undefined,
    from_date: undefined,
    to_date: undefined,
    search: undefined,
  });

  const { data, isLoading } = usePayments(filters);
  const refundMutation = useRefundPayment();
  const exportMutation = useExportPaymentsCSV();

  const handleRefund = (amount?: number, reason?: string) => {
    if (selectedPayment) {
      refundMutation.mutate(
        {
          payment_id: selectedPayment.payment_id,
          amount,
          reason,
        },
        {
          onSuccess: () => {
            setRefundModalOpen(false);
            setSelectedPayment(null);
          },
        }
      );
    }
  };

  const handleExport = () => {
    exportMutation.mutate(filters);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Payments</h1>
        <p className="text-muted-foreground">
          Manage and track all payment transactions
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Payment Transactions</CardTitle>
          <CardDescription>
            View, filter, and manage payment records
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PaymentsTable
            payments={data?.payments || []}
            total={data?.total || 0}
            loading={isLoading}
            onViewDetails={(payment) => console.log('View details', payment)}
            onRefund={(payment) => {
              setSelectedPayment(payment);
              setRefundModalOpen(true);
            }}
            onExport={handleExport}
            onFiltersChange={setFilters}
            currentFilters={filters}
          />
        </CardContent>
      </Card>

      <RefundModal
        open={refundModalOpen}
        onOpenChange={setRefundModalOpen}
        payment={selectedPayment}
        onRefund={handleRefund}
        loading={refundMutation.isPending}
      />
    </div>
  );
}
