import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { FinanceDashboard } from '@/components/finance/FinanceDashboard';
import { financeService } from '@/services/finance';
import '@testing-library/jest-dom';

// Mock the finance service
jest.mock('@/services/finance');

const mockDashboardData = {
  kpis: {
    total_revenue: 150000,
    pending_payments: 12000,
    success_rate: 95.5,
    active_customers: 342
  },
  revenue_trend: [
    { date: '2024-01-01', amount: 10000 },
    { date: '2024-01-02', amount: 12000 },
    { date: '2024-01-03', amount: 15000 }
  ],
  provider_distribution: [
    { provider: 'stripe_cards', amount: 100000, count: 200 },
    { provider: 'paypal', amount: 50000, count: 142 }
  ]
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('FinanceDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (financeService.getDashboard as jest.Mock).mockResolvedValue(mockDashboardData);
    (financeService.getAlerts as jest.Mock).mockResolvedValue([]);
  });

  test('renders dashboard with KPI cards', async () => {
    renderWithProviders(<FinanceDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Total Revenue')).toBeInTheDocument();
      expect(screen.getByText('$1,500.00')).toBeInTheDocument();
      expect(screen.getByText('Pending Payments')).toBeInTheDocument();
      expect(screen.getByText('$120.00')).toBeInTheDocument();
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
      expect(screen.getByText('95.5%')).toBeInTheDocument();
      expect(screen.getByText('Active Customers')).toBeInTheDocument();
      expect(screen.getByText('342')).toBeInTheDocument();
    });
  });

  test('displays revenue trend chart', async () => {
    renderWithProviders(<FinanceDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Revenue Trend')).toBeInTheDocument();
    });
  });

  test('shows provider distribution', async () => {
    renderWithProviders(<FinanceDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Payment Providers')).toBeInTheDocument();
    });
  });

  test('displays loading state initially', () => {
    (financeService.getDashboard as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    renderWithProviders(<FinanceDashboard />);
    
    expect(screen.getAllByTestId('skeleton')).toHaveLength(4);
  });

  test('handles error state gracefully', async () => {
    (financeService.getDashboard as jest.Mock).mockRejectedValue(
      new Error('Failed to fetch dashboard data')
    );

    renderWithProviders(<FinanceDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load dashboard/i)).toBeInTheDocument();
    });
  });

  test('renders tabs for different sections', async () => {
    renderWithProviders(<FinanceDashboard />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Payments/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Payouts/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Reconciliation/i })).toBeInTheDocument();
    });
  });
});
