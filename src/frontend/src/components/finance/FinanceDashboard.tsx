/**
 * FinanceDashboard Component
 * Main finance dashboard with KPIs, charts, and quick actions
 */

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Button } from '../ui/button';
import { KPICard } from './KPICard';
import { AlertBanner } from './AlertBanner';
import { PaymentsTable } from './PaymentsTable';
import { PayoutsTable } from './PayoutsTable';
import { ReconciliationTable } from './ReconciliationTable';
import { RefundModal } from './RefundModal';
import {
  DollarSign,
  CreditCard,
  TrendingUp,
  AlertCircle,
  Download,
  RefreshCw,
  Plus,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  useDashboard,
  usePayments,
  usePayouts,
  useReconciliation,
  useAlerts,
  useRefundPayment,
  useExportPaymentsCSV,
  useExecutePayout,
} from '../../hooks/useFinance';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'];

export function FinanceDashboard() {
  const [selectedPayment, setSelectedPayment] = useState<any>(null);
  const [refundModalOpen, setRefundModalOpen] = useState(false);
  const [paymentFilters, setPaymentFilters] = useState({
    status: undefined,
    provider: undefined,
    from_date: undefined,
    to_date: undefined,
    search: undefined,
  });

  // Fetch data
  const { data: dashboard, isLoading: dashboardLoading } = useDashboard();
  const { data: payments, isLoading: paymentsLoading } = usePayments(paymentFilters);
  const { data: payouts, isLoading: payoutsLoading } = usePayouts();
  const { data: reconciliation, isLoading: reconciliationLoading } = useReconciliation();
  const { data: alerts } = useAlerts();

  // Mutations
  const refundMutation = useRefundPayment();
  const exportMutation = useExportPaymentsCSV();
  const executePayout = useExecutePayout();

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

  const handleExportPayments = () => {
    exportMutation.mutate(paymentFilters);
  };

  const formatCurrency = (amount: number, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount / 100);
  };

  // Calculate trends
  const calculateTrend = (current: number, previous: number) => {
    if (previous === 0) return 0;
    return ((current - previous) / previous) * 100;
  };

  const volumeTrend = dashboard
    ? calculateTrend(dashboard.volume_today, dashboard.volume_yesterday)
    : 0;

  const successTrend = dashboard
    ? calculateTrend(dashboard.success_rate, 85) // Compare to 85% baseline
    : 0;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Finance Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor payments, payouts, and financial health
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            New Payout
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {alerts && alerts.length > 0 && (
        <AlertBanner alerts={alerts} onDismiss={(id) => console.log('Dismiss alert', id)} />
      )}

      {/* KPIs */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Balance"
          value={dashboard ? formatCurrency(dashboard.total_balance) : '$0'}
          subtitle="Across all providers"
          icon={<DollarSign className="h-4 w-4" />}
          loading={dashboardLoading}
        />
        <KPICard
          title="Today's Volume"
          value={dashboard ? formatCurrency(dashboard.volume_today) : '$0'}
          subtitle={`${dashboard?.transactions_today || 0} transactions`}
          trend={{
            value: volumeTrend,
            label: 'vs yesterday',
          }}
          icon={<CreditCard className="h-4 w-4" />}
          loading={dashboardLoading}
        />
        <KPICard
          title="Success Rate"
          value={dashboard ? `${dashboard.success_rate.toFixed(1)}%` : '0%'}
          subtitle="Last 7 days"
          trend={{
            value: successTrend,
            label: 'vs baseline',
          }}
          icon={<TrendingUp className="h-4 w-4" />}
          loading={dashboardLoading}
        />
        <KPICard
          title="Pending Payouts"
          value={dashboard ? formatCurrency(dashboard.pending_payouts) : '$0'}
          subtitle={`${dashboard?.pending_payout_count || 0} payouts`}
          icon={<AlertCircle className="h-4 w-4" />}
          loading={dashboardLoading}
        />
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Revenue Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue Trend</CardTitle>
            <CardDescription>Daily revenue over the last 7 days</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height="200">
              <LineChart data={dashboard?.revenue_trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value: any) => formatCurrency(value)} />
                <Line
                  type="monotone"
                  dataKey="amount"
                  stroke="#3b82f6"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Provider Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Provider Distribution</CardTitle>
            <CardDescription>Volume by payment provider</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height="200">
              <PieChart>
                <Pie
                  data={dashboard?.provider_distribution || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {(dashboard?.provider_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="payments" className="space-y-4">
        <TabsList>
          <TabsTrigger value="payments">Payments</TabsTrigger>
          <TabsTrigger value="payouts">Payouts</TabsTrigger>
          <TabsTrigger value="reconciliation">Reconciliation</TabsTrigger>
        </TabsList>

        <TabsContent value="payments" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Payments</CardTitle>
              <CardDescription>
                View and manage payment transactions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PaymentsTable
                payments={payments?.payments || []}
                total={payments?.total || 0}
                loading={paymentsLoading}
                onViewDetails={(payment) => console.log('View', payment)}
                onRefund={(payment) => {
                  setSelectedPayment(payment);
                  setRefundModalOpen(true);
                }}
                onExport={handleExportPayments}
                onFiltersChange={setPaymentFilters}
                currentFilters={paymentFilters}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payouts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Payout Management</CardTitle>
              <CardDescription>
                Track and execute payouts to providers
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PayoutsTable
                payouts={payouts || []}
                loading={payoutsLoading}
                onExecute={(payout) => executePayout.mutate(payout.payout_id)}
                onMarkPaid={(payout) => console.log('Mark paid', payout)}
                onCancel={(payout) => console.log('Cancel', payout)}
                onViewDetails={(payout) => console.log('View', payout)}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reconciliation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Reconciliation Status</CardTitle>
              <CardDescription>
                Monitor transaction matching and discrepancies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ReconciliationTable
                reports={reconciliation || []}
                loading={reconciliationLoading}
                onExport={(provider, date) => console.log('Export', provider, date)}
                onForceReconciliation={() => console.log('Force reconciliation')}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Refund Modal */}
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
