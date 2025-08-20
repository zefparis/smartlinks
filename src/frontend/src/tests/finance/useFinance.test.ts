import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useFinanceDashboard,
  usePayments,
  usePayouts,
  useReconciliation,
  useFees,
  useRefundPayment,
  useExecutePayout,
  useCreatePayment
} from '@/hooks/useFinance';
import { financeService } from '@/services/finance';

jest.mock('@/services/finance');

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useFinance hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useFinanceDashboard', () => {
    it('fetches dashboard data successfully', async () => {
      const mockData = {
        kpis: {
          total_revenue: 100000,
          pending_payments: 5000,
          success_rate: 98.5,
          active_customers: 250
        },
        revenue_trend: [],
        provider_distribution: []
      };

      (financeService.getDashboard as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useFinanceDashboard(), {
        wrapper: createWrapper()
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
        expect(result.current.data).toEqual(mockData);
      });

      expect(financeService.getDashboard).toHaveBeenCalled();
    });

    it('handles dashboard fetch error', async () => {
      const error = new Error('Dashboard fetch failed');
      (financeService.getDashboard as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useFinanceDashboard(), {
        wrapper: createWrapper()
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
        expect(result.current.error).toEqual(error);
      });
    });
  });

  describe('usePayments', () => {
    it('fetches payments with filters', async () => {
      const mockPayments = [
        { id: 'pay_1', amount: 1000, status: 'captured' },
        { id: 'pay_2', amount: 2000, status: 'pending' }
      ];

      (financeService.getPayments as jest.Mock).mockResolvedValue(mockPayments);

      const filters = {
        status: 'captured',
        provider: 'stripe_cards',
        start_date: '2024-01-01',
        end_date: '2024-01-31'
      };

      const { result } = renderHook(() => usePayments(filters), {
        wrapper: createWrapper()
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
        expect(result.current.data).toEqual(mockPayments);
      });

      expect(financeService.getPayments).toHaveBeenCalledWith(filters);
    });
  });

  describe('useRefundPayment', () => {
    it('processes refund successfully', async () => {
      const mockRefund = { id: 'refund_1', status: 'completed' };
      (financeService.refundPayment as jest.Mock).mockResolvedValue(mockRefund);

      const { result } = renderHook(() => useRefundPayment(), {
        wrapper: createWrapper()
      });

      const refundData = {
        payment_id: 'pay_1',
        amount: 500,
        reason: 'Customer request'
      };

      result.current.mutate(refundData);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
        expect(result.current.data).toEqual(mockRefund);
      });

      expect(financeService.refundPayment).toHaveBeenCalledWith(
        'pay_1',
        { amount: 500, reason: 'Customer request' }
      );
    });

    it('handles refund error', async () => {
      const error = new Error('Refund failed');
      (financeService.refundPayment as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useRefundPayment(), {
        wrapper: createWrapper()
      });

      result.current.mutate({
        payment_id: 'pay_1',
        amount: 500
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
        expect(result.current.error).toEqual(error);
      });
    });
  });

  describe('useExecutePayout', () => {
    it('executes payout successfully', async () => {
      const mockPayout = { id: 'payout_1', status: 'processing' };
      (financeService.executePayout as jest.Mock).mockResolvedValue(mockPayout);

      const { result } = renderHook(() => useExecutePayout(), {
        wrapper: createWrapper()
      });

      result.current.mutate('payout_1');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
        expect(result.current.data).toEqual(mockPayout);
      });

      expect(financeService.executePayout).toHaveBeenCalledWith('payout_1');
    });
  });

  describe('useCreatePayment', () => {
    it('creates payment successfully', async () => {
      const mockPayment = {
        id: 'pay_new',
        status: 'pending',
        checkout_url: 'https://checkout.stripe.com/...'
      };
      (financeService.createPayment as jest.Mock).mockResolvedValue(mockPayment);

      const { result } = renderHook(() => useCreatePayment(), {
        wrapper: createWrapper()
      });

      const paymentData = {
        amount: 10000,
        currency: 'USD',
        provider: 'stripe_cards',
        customer_email: 'customer@example.com'
      };

      result.current.mutate(paymentData);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
        expect(result.current.data).toEqual(mockPayment);
      });

      expect(financeService.createPayment).toHaveBeenCalledWith(paymentData);
    });
  });

  describe('useFees', () => {
    it('fetches fee data with date range', async () => {
      const mockFees = {
        total_fees: 5000,
        average_rate: 2.9,
        by_provider: [
          { provider: 'stripe_cards', total: 3000, rate: 2.9 },
          { provider: 'paypal', total: 2000, rate: 3.49 }
        ]
      };

      (financeService.getFees as jest.Mock).mockResolvedValue(mockFees);

      const { result } = renderHook(
        () => useFees('2024-01-01', '2024-01-31'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
        expect(result.current.data).toEqual(mockFees);
      });

      expect(financeService.getFees).toHaveBeenCalledWith({
        start_date: '2024-01-01',
        end_date: '2024-01-31'
      });
    });
  });

  describe('useReconciliation', () => {
    it('fetches reconciliation reports', async () => {
      const mockReports = [
        {
          id: 'rec_1',
          provider: 'stripe_cards',
          match_rate: 98.5,
          matched_count: 197,
          unmatched_count: 3,
          total_amount: 50000
        }
      ];

      (financeService.getReconciliation as jest.Mock).mockResolvedValue(mockReports);

      const { result } = renderHook(() => useReconciliation(), {
        wrapper: createWrapper()
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
        expect(result.current.data).toEqual(mockReports);
      });

      expect(financeService.getReconciliation).toHaveBeenCalled();
    });
  });
});
