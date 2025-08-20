/**
 * PayoutsTable Component
 * Manages payouts with actions for execution and tracking
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
import { StatusBadge } from './StatusBadge';
import { Play, Check, X, Eye, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { Alert, AlertDescription } from '../ui/alert';
import type { Payout } from '../../services/finance';

interface PayoutsTableProps {
  payouts: Payout[];
  loading?: boolean;
  onExecute: (payout: Payout) => void;
  onMarkPaid: (payout: Payout) => void;
  onCancel: (payout: Payout) => void;
  onViewDetails: (payout: Payout) => void;
}

export function PayoutsTable({
  payouts,
  loading,
  onExecute,
  onMarkPaid,
  onCancel,
  onViewDetails,
}: PayoutsTableProps) {
  const [filters, setFilters] = useState({
    status: 'all',
    provider: 'all',
  });

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount / 100);
  };

  const filteredPayouts = payouts.filter((payout) => {
    if (filters.status !== 'all' && payout.status !== filters.status) return false;
    if (filters.provider !== 'all' && payout.provider !== filters.provider) return false;
    return true;
  });

  const pendingPayouts = payouts.filter(p => p.status === 'proposed');
  const overduePayouts = pendingPayouts.filter(p => {
    const daysOld = (Date.now() - new Date(p.date).getTime()) / (1000 * 60 * 60 * 24);
    return daysOld > 7;
  });

  return (
    <div className="space-y-6">
      {/* Alerts */}
      {overduePayouts.length > 0 && (
        <Alert variant="destructive" className="rounded-xl shadow-md">
          <AlertCircle className="h-5 w-5" />
          <AlertDescription className="font-semibold">
            {overduePayouts.length} paiements en attente dépassent 7 jours
          </AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <Select
          value={filters.status}
          onValueChange={(value) => setFilters({ ...filters, status: value })}
        >
          <SelectTrigger className="w-full sm:w-[180px] bg-background border-muted rounded-lg focus:ring-2 focus:ring-primary transition-all">
            <SelectValue placeholder="Filtrer par statut" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous statuts</SelectItem>
            <SelectItem value="proposed">Proposé</SelectItem>
            <SelectItem value="paid">Payé</SelectItem>
            <SelectItem value="failed">Échoué</SelectItem>
            <SelectItem value="cancelled">Annulé</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={filters.provider}
          onValueChange={(value) => setFilters({ ...filters, provider: value })}
        >
          <SelectTrigger className="w-full sm:w-[180px] bg-background border-muted rounded-lg focus:ring-2 focus:ring-primary transition-all">
            <SelectValue placeholder="Filtrer par prestataire" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous prestataires</SelectItem>
            <SelectItem value="stripe_cards">Stripe</SelectItem>
            <SelectItem value="paypal">PayPal</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-2xl shadow-xl overflow-hidden border border-muted bg-card">
        <Table>
          <TableHeader className="bg-muted/70">
            <TableRow>
              <TableHead className="text-base font-semibold text-muted-foreground">Date</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground">Montant</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground">Prestataire</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground">Moyen</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground">Statut</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground">Référence</TableHead>
              <TableHead className="text-base font-semibold text-muted-foreground text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredPayouts.map((payout) => {
              const daysOld = (Date.now() - new Date(payout.date).getTime()) / (1000 * 60 * 60 * 24);
              const isOverdue = payout.status === 'proposed' && daysOld > 7;
              
              return (
                <TableRow
                  key={payout.payout_id}
                  className={
                    `transition-colors ${isOverdue ? 'bg-red-50 dark:bg-red-900/40' : 'hover:bg-accent/50 focus-within:bg-accent/70'} `
                  }
                >
                  <TableCell>
                    {format(new Date(payout.date), 'dd/MM/yyyy')}
                    {isOverdue && (
                      <span className="ml-2 text-xs text-red-600 font-semibold">
                        ({Math.floor(daysOld)}j)
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="font-bold text-lg text-foreground">
                    {formatAmount(payout.amount, payout.currency)}
                  </TableCell>
                  <TableCell className="capitalize">
                    {payout.provider.replace('_', ' ')}
                  </TableCell>
                  <TableCell className="uppercase">
                    {payout.method}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={payout.status} />
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {payout.external_ref || '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      {payout.status === 'proposed' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="rounded-full hover:bg-primary/10 focus:bg-primary/20 transition-all"
                            onClick={() => onExecute(payout)}
                            title="Exécuter le paiement"
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="rounded-full hover:bg-green-100 focus:bg-green-200 dark:hover:bg-green-900/30 dark:focus:bg-green-900/50 transition-all"
                            onClick={() => onMarkPaid(payout)}
                            title="Marquer comme payé"
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="rounded-full hover:bg-red-100 focus:bg-red-200 dark:hover:bg-red-900/30 dark:focus:bg-red-900/50 transition-all"
                            onClick={() => onCancel(payout)}
                            title="Annuler"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="rounded-full hover:bg-accent/60 focus:bg-accent/80 transition-all"
                        onClick={() => onViewDetails(payout)}
                        title="Voir détails"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
            {filteredPayouts.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground">
                  Aucun paiement trouvé
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
