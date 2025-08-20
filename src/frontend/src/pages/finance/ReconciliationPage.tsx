/**
 * Reconciliation Page
 * View and manage payment reconciliation
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { ReconciliationTable } from '../../components/finance/ReconciliationTable';
import { useReconciliation, useExportReconciliationCSV } from '../../hooks/useFinance';

export function ReconciliationPage() {
  const { data, isLoading } = useReconciliation();
  const exportMutation = useExportReconciliationCSV();

  const handleExport = (provider: string, date: string) => {
    exportMutation.mutate({ provider, date });
  };

  const handleForceReconciliation = () => {
    // Force reconciliation process
    console.log('Running reconciliation...');
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Reconciliation</h1>
        <p className="text-muted-foreground">
          Monitor transaction matching and identify discrepancies
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Reconciliation Reports</CardTitle>
          <CardDescription>
            Track reconciliation status across all payment providers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ReconciliationTable
            reports={data || []}
            loading={isLoading}
            onExport={handleExport}
            onForceReconciliation={handleForceReconciliation}
          />
        </CardContent>
      </Card>
    </div>
  );
}
