/**
 * Finance Hooks
 * Custom React hooks for finance data fetching and state management
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { financeService } from '../services/finance';
import type {
  FinanceDashboard,
  Balance,
  Payment,
  Payout,
  ReconciliationReport,
  Fee,
  Alert,
  CreatePaymentRequest,
  RefundRequest,
  CheckoutSession,
} from '../services/finance';

// Dashboard Hook
export function useFinanceDashboard(refreshInterval = 30000) {
  return useQuery<FinanceDashboard>({
    queryKey: ['finance', 'dashboard'],
    queryFn: () => financeService.getDashboard(),
    refetchInterval: refreshInterval,
    staleTime: 10000,
  });
}

// Balances Hook
export function useBalances() {
  return useQuery<Balance[]>({
    queryKey: ['finance', 'balances'],
    queryFn: () => financeService.getBalances(),
    staleTime: 30000,
  });
}

// Recent Payments Hook with filters
export function useRecentPayments(params?: {
  limit?: number;
  offset?: number;
  status?: string;
  provider?: string;
  from_date?: string;
  to_date?: string;
  min_amount?: number;
  max_amount?: number;
  search?: string;
}) {
  return useQuery({
    queryKey: ['finance', 'payments', params],
    queryFn: () => financeService.getRecentPayments(params),
    staleTime: 5000,
  });
}

// Payment Details Hook
export function usePaymentDetails(paymentId: string | null) {
  return useQuery<Payment>({
    queryKey: ['finance', 'payment', paymentId],
    queryFn: () => financeService.getPaymentDetails(paymentId!),
    enabled: !!paymentId,
  });
}

// Create Payment Hook
export function useCreatePayment() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreatePaymentRequest) => financeService.createPayment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'payments'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'dashboard'] });
    },
  });
}

// Capture Payment Hook
export function useCapturePayment() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ provider, paymentId }: { provider: string; paymentId: string }) =>
      financeService.capturePayment(provider, paymentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'payments'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'dashboard'] });
    },
  });
}

// Refund Payment Hook
export function useRefundPayment() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({
      provider,
      paymentId,
      data,
    }: {
      provider: string;
      paymentId: string;
      data: RefundRequest;
    }) => financeService.refundPayment(provider, paymentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'payments'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'balances'] });
    },
  });
}

// Payouts Hook
export function usePayouts(params?: {
  status?: string;
  provider?: string;
  from_date?: string;
  to_date?: string;
}) {
  return useQuery<Payout[]>({
    queryKey: ['finance', 'payouts', params],
    queryFn: () => financeService.getPayouts(params),
    staleTime: 10000,
  });
}

// Schedule Payout Hook
export function useSchedulePayout() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ provider, currency }: { provider: string; currency: string }) =>
      financeService.schedulePayout(provider, currency),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'payouts'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'dashboard'] });
    },
  });
}

// Execute Payout Hook
export function useExecutePayout() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (payoutId: string) => financeService.executePayout(payoutId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'payouts'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'balances'] });
    },
  });
}

// Mark Payout Paid Hook
export function useMarkPayoutPaid() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ payoutId, externalRef }: { payoutId: string; externalRef: string }) =>
      financeService.markPayoutPaid(payoutId, externalRef),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'payouts'] });
    },
  });
}

// Single Reconciliation Report Hook
export function useReconciliationReport(provider: string, date?: string) {
  return useQuery<ReconciliationReport>({
    queryKey: ['finance', 'reconciliation', provider, date],
    queryFn: () => financeService.getReconciliation(provider, date),
    staleTime: 60000,
  });
}

// Run Daily Reconciliation Hook
export function useRunDailyReconciliation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => financeService.runDailyReconciliation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'reconciliation'] });
    },
  });
}

// Fees Hook
export function useFees(params?: {
  provider?: string;
  from_date?: string;
  to_date?: string;
}) {
  return useQuery<Fee[]>({
    queryKey: ['finance', 'fees', params],
    queryFn: () => financeService.getFees(params),
    staleTime: 30000,
  });
}

// Alerts Hook
export function useFinanceAlerts(refreshInterval = 10000) {
  return useQuery<Alert[]>({
    queryKey: ['finance', 'alerts'],
    queryFn: () => financeService.getAlerts(),
    refetchInterval: refreshInterval,
    staleTime: 5000,
  });
}

// Export Hooks
export function useExportPaymentsCSV() {
  return useMutation({
    mutationFn: (params: any) => financeService.exportPaymentsCSV(params),
    onSuccess: (blob: Blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `payments-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}

export function useExportReconciliationCSV() {
  return useMutation({
    mutationFn: ({ provider, date }: { provider: string; date: string }) =>
      financeService.exportReconciliationCSV(provider, date),
    onSuccess: (blob: Blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reconciliation-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}

// Checkout Hook with real-time status
export function useCheckout() {
  return useMutation({
    mutationFn: (data: CreatePaymentRequest) => financeService.createPayment(data),
  });
}

// Checkout Status Polling Hook
export function useCheckoutStatus(sessionId: string | null, enabled: boolean) {
  return useQuery<CheckoutSession>({
    queryKey: ['finance', 'checkout', 'status', sessionId],
    queryFn: () => financeService.getCheckoutStatus(sessionId!),
    enabled: !!sessionId && enabled,
    refetchInterval: 2500, // Poll every 2.5 seconds
    staleTime: 0,
    gcTime: 300000, // 5 minutes
    retry: false,
  });
}

// Alias exports for convenience
export const usePayments = useRecentPayments;
export const useAlerts = useFinanceAlerts;
export const useDashboard = useFinanceDashboard;
export const useReconciliation = () => {
  // Get all reconciliation reports
  return useQuery({
    queryKey: ['finance', 'reconciliation', 'all'],
    queryFn: async () => {
      // Fetch reports for common providers
      const providers = ['stripe_cards', 'paypal'];
      const reports = await Promise.all(
        providers.map(provider => 
          financeService.getReconciliation(provider).catch(() => null)
        )
      );
      return reports.filter(Boolean);
    },
    staleTime: 60000,
  });
};

// User payment history hook
export function useUserPaymentHistory(userId?: string, email?: string) {
  return useQuery({
    queryKey: ['finance', 'user-payments', userId, email],
    queryFn: () => {
      // Use the getRecentPayments with search filter
      const search = email || userId;
      return financeService.getRecentPayments({ search, limit: 100 });
    },
    enabled: !!(userId || email),
    staleTime: 30000,
  });
}
