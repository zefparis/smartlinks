/**
 * Finance API Service
 * Handles all finance-related API calls
 */

import apiClient from '../lib/api';

export interface Balance {
  currency: string;
  provider: string;
  amount: number;
  available: number;
  pending: number;
}

export interface Payment {
  payment_id: string;
  user_id?: string;
  date: string;
  amount: number;
  currency: string;
  provider: string;
  status: 'pending' | 'captured' | 'failed' | 'refunded' | 'disputed';
  metadata?: Record<string, any>;
  provider_payment_id?: string;
  fees?: number;
  net_amount?: number;
}

export interface Payout {
  payout_id: string;
  date: string;
  amount: number;
  currency: string;
  method: 'sepa' | 'withdrawal' | 'manual';
  status: 'proposed' | 'paid' | 'failed' | 'cancelled';
  external_ref?: string;
  provider: string;
  metadata?: Record<string, any>;
}

export interface ReconciliationReport {
  provider: string;
  date: string;
  matched_count: number;
  matched_amount: number;
  missing_count: number;
  missing_amount: number;
  mismatched_count: number;
  mismatched_amount: number;
  match_rate: number;
  currency: string;
}

export interface Fee {
  provider: string;
  total_amount: number;
  percentage_of_revenue: number;
  count: number;
  period: string;
  currency: string;
}

export interface FinanceDashboard {
  total_balance: { [currency: string]: number };
  revenue_gross: { [currency: string]: number };
  revenue_net: { [currency: string]: number };
  total_fees: { [currency: string]: number };
  refunds: { count: number; amount: { [currency: string]: number } };
  disputes: { count: number; amount: { [currency: string]: number } };
  last_payout?: Payout;
  pending_payouts: number;
  alerts: Alert[];
}

export interface Alert {
  id: string;
  type: 'dispute' | 'payout_failed' | 'low_balance' | 'reconciliation_mismatch';
  severity: 'info' | 'warning' | 'error';
  message: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface CreatePaymentRequest {
  amount: number;
  currency: string;
  provider: string;
  meta?: Record<string, any>;
}

export interface RefundRequest {
  amount?: number;
  reason?: string;
}

export interface CheckoutSession {
  session_id: string;
  status: 'pending' | 'completed' | 'failed' | 'cancelled';
  payment_id?: string;
  checkout_url?: string;
  expires_at: string;
}

class FinanceService {
  async getDashboard(): Promise<FinanceDashboard> {
    const response = await apiClient.get<FinanceDashboard>('/finance/dashboard');
    return response.data;
  }

  async getBalances(): Promise<Balance[]> {
    const response = await apiClient.get<Balance[]>('/payments/balances');
    return response.data;
  }

  async getRecentPayments(params?: {
    limit?: number;
    offset?: number;
    status?: string;
    provider?: string;
    from_date?: string;
    to_date?: string;
    min_amount?: number;
    max_amount?: number;
    search?: string;
  }): Promise<{ payments: Payment[]; total: number }> {
    const response = await apiClient.get('/payments/recent', { params });
    return response.data;
  }

  async getPaymentDetails(paymentId: string): Promise<Payment> {
    const response = await apiClient.get<Payment>(`/payments/${paymentId}`);
    return response.data;
  }

  async createPayment(data: CreatePaymentRequest): Promise<{
    payment_id: string;
    provider: string;
    session: any;
    status: string;
  }> {
    const response = await apiClient.post('/payments/create', data);
    return response.data;
  }

  async capturePayment(provider: string, paymentId: string): Promise<Payment> {
    const response = await apiClient.post(`/payments/capture/${provider}/${paymentId}`, {});
    return response.data;
  }

  async refundPayment(provider: string, paymentId: string, data: RefundRequest): Promise<{
    status: string;
    amount: number;
    currency: string;
    provider_refund_id: string;
    reason?: string;
  }> {
    const response = await apiClient.post(`/payments/refund/${provider}/${paymentId}`, data);
    return response.data;
  }

  async getPayouts(params?: {
    status?: string;
    provider?: string;
    from_date?: string;
    to_date?: string;
  }): Promise<Payout[]> {
    const response = await apiClient.get<Payout[]>('/finance/payouts', { params });
    return response.data;
  }

  async schedulePayout(provider: string, currency: string): Promise<Payout> {
    const response = await apiClient.post('/finance/payouts/schedule', {
      provider,
      currency,
    });
    return response.data;
  }

  async executePayout(payoutId: string): Promise<Payout> {
    const response = await apiClient.post(`/finance/payouts/${payoutId}/execute`, {});
    return response.data;
  }

  async markPayoutPaid(payoutId: string, externalRef: string): Promise<Payout> {
    const response = await apiClient.post(`/finance/payouts/${payoutId}/mark-paid`, {
      external_ref: externalRef,
    });
    return response.data;
  }

  async getReconciliation(provider: string, date?: string): Promise<ReconciliationReport> {
    const response = await apiClient.get<ReconciliationReport>(
      `/finance/reconciliation/${provider}`,
      { params: { date } }
    );
    return response.data;
  }

  async runDailyReconciliation(): Promise<{ message: string }> {
    const response = await apiClient.post('/finance/reconciliation/daily', {});
    return response.data;
  }

  async getFees(params?: {
    provider?: string;
    from_date?: string;
    to_date?: string;
  }): Promise<Fee[]> {
    const response = await apiClient.get<Fee[]>('/finance/fees', { params });
    return response.data;
  }

  async exportPaymentsCSV(params: any): Promise<Blob> {
    const response = await apiClient.get('/payments/export/csv', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }

  async exportReconciliationCSV(provider: string, date: string): Promise<Blob> {
    const response = await apiClient.get(`/finance/reconciliation/${provider}/export`, {
      params: { date },
      responseType: 'blob',
    });
    return response.data;
  }

  async getAlerts(): Promise<Alert[]> {
    const response = await apiClient.get<Alert[]>('/ia/alerts', {
      params: { type: 'finance' },
    });
    return response.data;
  }

  async getCheckoutStatus(sessionId: string): Promise<CheckoutSession> {
    const response = await apiClient.get<CheckoutSession>(`/payments/checkout/status/${sessionId}`);
    return response.data;
  }
}

export const financeService = new FinanceService();
