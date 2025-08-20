/**
 * ReconciliationTable Component
 * Displays reconciliation status and mismatches
 */

import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Download, RefreshCw, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';
import type { ReconciliationReport } from '../../services/finance';

interface ReconciliationTableProps {
  reports: ReconciliationReport[];
  loading?: boolean;
  onExport: (provider: string, date: string) => void;
  onForceReconciliation: () => void;
}

export function ReconciliationTable({
  reports,
  loading,
  onExport,
  onForceReconciliation,
}: ReconciliationTableProps) {
  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount / 100);
  };

  const getMatchRateColor = (rate: number) => {
    if (rate >= 95) return 'text-green-600';
    if (rate >= 85) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getMatchRateIcon = (rate: number) => {
    if (rate >= 95) return <CheckCircle className="h-4 w-4 text-green-600" />;
    if (rate >= 85) return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    return <XCircle className="h-4 w-4 text-red-600" />;
  };

  const totalMatched = reports.reduce((sum, r) => sum + r.matched_amount, 0);
  const totalMissing = reports.reduce((sum, r) => sum + r.missing_amount, 0);
  const totalMismatched = reports.reduce((sum, r) => sum + r.mismatched_amount, 0);
  const totalAmount = totalMatched + totalMissing + totalMismatched;
  const overallMatchRate = totalAmount > 0 ? (totalMatched / totalAmount) * 100 : 0;

  return (
    <div className="space-y-8">
      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card className="shadow-2xl rounded-2xl border-0 bg-card">
          <CardHeader className="pb-2 bg-background/80 rounded-t-2xl">
            <CardTitle className="text-base font-bold text-foreground">Taux de correspondance global</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <span className={`text-3xl font-extrabold ${getMatchRateColor(overallMatchRate)}`}>{overallMatchRate.toFixed(1)}%</span>
              {getMatchRateIcon(overallMatchRate)}
            </div>
            <Progress value={overallMatchRate} className="mt-2 h-2 rounded-full transition-all duration-300" />
          </CardContent>
        </Card>
        <Card className="shadow-2xl rounded-2xl border-0 bg-card">
          <CardHeader className="pb-2 bg-background/80 rounded-t-2xl">
            <CardTitle className="text-base font-bold text-green-600 dark:text-green-400">Appariés</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-extrabold text-green-600 dark:text-green-400">
              {reports.reduce((sum, r) => sum + r.matched_count, 0)}
            </div>
            <p className="text-xs text-muted-foreground">transactions appariées</p>
          </CardContent>
        </Card>
        <Card className="shadow-2xl rounded-2xl border-0 bg-card">
          <CardHeader className="pb-2 bg-background/80 rounded-t-2xl">
            <CardTitle className="text-base font-bold text-yellow-600 dark:text-yellow-400">Manquants</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-extrabold text-yellow-600 dark:text-yellow-400">
              {reports.reduce((sum, r) => sum + r.missing_count, 0)}
            </div>
            <p className="text-xs text-muted-foreground">transactions non trouvées</p>
          </CardContent>
        </Card>
        <Card className="shadow-2xl rounded-2xl border-0 bg-card">
          <CardHeader className="pb-2 bg-background/80 rounded-t-2xl">
            <CardTitle className="text-base font-bold text-red-600 dark:text-red-400">Écarts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-extrabold text-red-600 dark:text-red-400">
              {reports.reduce((sum, r) => sum + r.mismatched_count, 0)}
            </div>
            <p className="text-xs text-muted-foreground">écarts de montant</p>
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex justify-end">
        <Button onClick={onForceReconciliation} variant="default" className="font-semibold transition-all">
          <RefreshCw className="mr-2 h-4 w-4" />
          Lancer la réconciliation
        </Button>
      </div>

      {/* Table */}
      <div className="rounded-2xl shadow-xl overflow-hidden border border-muted bg-card">
        <Table>
          <TableHeader className="bg-muted/70">
            <TableRow>
              <TableHead className="text-base font-semibold text-muted-foreground">Prestataire</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground">Date</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground">Taux</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground">Appariés</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground">Manquants</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground">Écarts</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground">Montant non réconcilié</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reports.map((report) => {
              const unreconciled = report.missing_amount + report.mismatched_amount;
              return (
                <TableRow
                  key={`${report.provider}-${report.date}`}
                  className="transition-colors hover:bg-accent/50 focus-within:bg-accent/70"
                >
                  <TableCell className="font-medium capitalize">
                    {report.provider.replace('_', ' ')}
                  </TableCell>
                  <TableCell>{format(new Date(report.date), 'dd/MM/yyyy')}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className={`font-semibold ${getMatchRateColor(report.match_rate)}`}>{report.match_rate.toFixed(1)}%</span>
                      {getMatchRateIcon(report.match_rate)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="font-bold text-green-600 dark:text-green-400">{report.matched_count}</span>
                    <span className="text-muted-foreground ml-1">
                      ({formatAmount(report.matched_amount, report.currency)})
                    </span>
                  </TableCell>
                  <TableCell className="text-yellow-600 dark:text-yellow-400">
                    {report.missing_count}
                    <span className="text-muted-foreground ml-1">
                      ({formatAmount(report.missing_amount, report.currency)})
                    </span>
                  </TableCell>
                  <TableCell className="text-red-600 dark:text-red-400">
                    {report.mismatched_count}
                    <span className="text-muted-foreground ml-1">
                      ({formatAmount(report.mismatched_amount, report.currency)})
                    </span>
                  </TableCell>
                  <TableCell className={unreconciled > 0 ? 'text-red-600 font-semibold dark:text-red-400' : ''}>
                    {formatAmount(unreconciled, report.currency)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="rounded-full hover:bg-accent/60 focus:bg-accent/80 transition-all"
                      onClick={() => onExport(report.provider, report.date)}
                      title="Exporter"
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
            {reports.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-muted-foreground">
                  Aucun rapport de réconciliation disponible
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
