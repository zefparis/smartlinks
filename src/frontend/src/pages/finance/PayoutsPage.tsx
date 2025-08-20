/**
 * Payouts Page
 * Manage and execute payouts
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { PayoutsTable } from '../../components/finance/PayoutsTable';
import { usePayouts, useExecutePayout } from '../../hooks/useFinance';

export function PayoutsPage() {
  const { data, isLoading } = usePayouts();
  const executePayout = useExecutePayout();

  const handleExecute = (payout: any) => {
    executePayout.mutate(payout.payout_id);
  };

  const handleMarkPaid = (payout: any) => {
    // Mark payout as paid manually
    console.log('Mark as paid:', payout);
  };

  const handleCancel = (payout: any) => {
    // Cancel payout
    console.log('Cancel payout:', payout);
  };

  const handleViewDetails = (payout: any) => {
    // View payout details
    console.log('View details:', payout);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Payouts</h1>
        <p className="text-muted-foreground">
          Manage payouts to payment providers
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Payout Management</CardTitle>
          <CardDescription>
            Execute and track payouts with real-time status updates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PayoutsTable
            payouts={data || []}
            loading={isLoading}
            onExecute={handleExecute}
            onMarkPaid={handleMarkPaid}
            onCancel={handleCancel}
            onViewDetails={handleViewDetails}
          />
        </CardContent>
      </Card>
    </div>
  );
}
