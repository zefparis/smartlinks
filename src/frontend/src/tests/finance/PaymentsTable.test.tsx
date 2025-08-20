import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PaymentsTable } from '@/components/finance/PaymentsTable';
import '@testing-library/jest-dom';

const mockPayments = [
  {
    id: 'pay_1',
    amount: 10000,
    currency: 'USD',
    status: 'captured',
    provider: 'stripe_cards',
    customer_email: 'user1@example.com',
    created_at: '2024-01-15T10:00:00Z',
    reference: 'REF-001'
  },
  {
    id: 'pay_2',
    amount: 5000,
    currency: 'USD',
    status: 'pending',
    provider: 'paypal',
    customer_email: 'user2@example.com',
    created_at: '2024-01-15T11:00:00Z',
    reference: 'REF-002'
  },
  {
    id: 'pay_3',
    amount: 15000,
    currency: 'USD',
    status: 'failed',
    provider: 'stripe_cards',
    customer_email: 'user3@example.com',
    created_at: '2024-01-15T12:00:00Z',
    reference: 'REF-003'
  }
];

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('PaymentsTable', () => {
  const mockOnRefund = jest.fn();
  const mockOnExport = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders payment table with data', () => {
    renderWithProviders(
      <PaymentsTable
        payments={mockPayments}
        onRefund={mockOnRefund}
        onExport={mockOnExport}
      />
    );

    expect(screen.getByText('pay_1')).toBeInTheDocument();
    expect(screen.getByText('user1@example.com')).toBeInTheDocument();
    expect(screen.getByText('$100.00')).toBeInTheDocument();
    expect(screen.getByText('Captured')).toBeInTheDocument();
  });

  test('filters payments by search term', () => {
    renderWithProviders(
      <PaymentsTable
        payments={mockPayments}
        onRefund={mockOnRefund}
        onExport={mockOnExport}
      />
    );

    const searchInput = screen.getByPlaceholderText(/Search/i);
    fireEvent.change(searchInput, { target: { value: 'REF-002' } });

    expect(screen.queryByText('pay_1')).not.toBeInTheDocument();
    expect(screen.getByText('pay_2')).toBeInTheDocument();
    expect(screen.queryByText('pay_3')).not.toBeInTheDocument();
  });

  test('filters payments by status', () => {
    renderWithProviders(
      <PaymentsTable
        payments={mockPayments}
        onRefund={mockOnRefund}
        onExport={mockOnExport}
      />
    );

    const statusFilter = screen.getByRole('combobox', { name: /Status/i });
    fireEvent.change(statusFilter, { target: { value: 'captured' } });

    expect(screen.getByText('pay_1')).toBeInTheDocument();
    expect(screen.queryByText('pay_2')).not.toBeInTheDocument();
    expect(screen.queryByText('pay_3')).not.toBeInTheDocument();
  });

  test('filters payments by provider', () => {
    renderWithProviders(
      <PaymentsTable
        payments={mockPayments}
        onRefund={mockOnRefund}
        onExport={mockOnExport}
      />
    );

    const providerFilter = screen.getByRole('combobox', { name: /Provider/i });
    fireEvent.change(providerFilter, { target: { value: 'paypal' } });

    expect(screen.queryByText('pay_1')).not.toBeInTheDocument();
    expect(screen.getByText('pay_2')).toBeInTheDocument();
    expect(screen.queryByText('pay_3')).not.toBeInTheDocument();
  });

  test('calls onRefund when refund button is clicked', () => {
    renderWithProviders(
      <PaymentsTable
        payments={mockPayments}
        onRefund={mockOnRefund}
        onExport={mockOnExport}
      />
    );

    const refundButtons = screen.getAllByText('Refund');
    fireEvent.click(refundButtons[0]);

    expect(mockOnRefund).toHaveBeenCalledWith(mockPayments[0]);
  });

  test('calls onExport when export button is clicked', () => {
    renderWithProviders(
      <PaymentsTable
        payments={mockPayments}
        onRefund={mockOnRefund}
        onExport={mockOnExport}
      />
    );

    const exportButton = screen.getByText(/Export/i);
    fireEvent.click(exportButton);

    expect(mockOnExport).toHaveBeenCalled();
  });

  test('displays empty state when no payments', () => {
    renderWithProviders(
      <PaymentsTable
        payments={[]}
        onRefund={mockOnRefund}
        onExport={mockOnExport}
      />
    );

    expect(screen.getByText(/No payments found/i)).toBeInTheDocument();
  });

  test('disables refund button for non-captured payments', () => {
    renderWithProviders(
      <PaymentsTable
        payments={mockPayments}
        onRefund={mockOnRefund}
        onExport={mockOnExport}
      />
    );

    const refundButtons = screen.getAllByRole('button', { name: /Refund/i });
    
    // First payment is captured - should be enabled
    expect(refundButtons[0]).not.toBeDisabled();
    
    // Second payment is pending - should be disabled
    expect(refundButtons[1]).toBeDisabled();
    
    // Third payment is failed - should be disabled
    expect(refundButtons[2]).toBeDisabled();
  });

  test('sorts payments by date', () => {
    renderWithProviders(
      <PaymentsTable
        payments={mockPayments}
        onRefund={mockOnRefund}
        onExport={mockOnExport}
      />
    );

    const dateHeader = screen.getByText('Date');
    fireEvent.click(dateHeader);

    const paymentIds = screen.getAllByTestId('payment-id').map(el => el.textContent);
    expect(paymentIds[0]).toBe('pay_3');
    expect(paymentIds[1]).toBe('pay_2');
    expect(paymentIds[2]).toBe('pay_1');
  });
});
