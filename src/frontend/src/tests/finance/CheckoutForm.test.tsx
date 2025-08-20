import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CheckoutForm } from '@/components/finance/CheckoutForm';
import { financeService } from '@/services/finance';
import '@testing-library/jest-dom';

jest.mock('@/services/finance');

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false }
  },
});

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('CheckoutForm', () => {
  const mockOnSuccess = jest.fn();
  const mockOnError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders checkout form with provider selection', () => {
    renderWithProviders(
      <CheckoutForm
        amount={9999}
        currency="USD"
        description="Test Product"
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('$99.99')).toBeInTheDocument();
    expect(screen.getByLabelText(/Stripe/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/PayPal/i)).toBeInTheDocument();
  });

  test('validates email input', async () => {
    renderWithProviders(
      <CheckoutForm
        amount={9999}
        currency="USD"
        description="Test Product"
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    const emailInput = screen.getByLabelText(/Email/i);
    const submitButton = screen.getByRole('button', { name: /Pay/i });

    // Try to submit without email
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Email is required/i)).toBeInTheDocument();
    });

    // Enter invalid email
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Invalid email/i)).toBeInTheDocument();
    });
  });

  test('processes Stripe payment successfully', async () => {
    const mockSession = {
      id: 'cs_test_123',
      status: 'complete',
      payment_status: 'paid'
    };

    (financeService.createPayment as jest.Mock).mockResolvedValue(mockSession);
    (financeService.getPaymentStatus as jest.Mock).mockResolvedValue({
      status: 'captured'
    });

    renderWithProviders(
      <CheckoutForm
        amount={9999}
        currency="USD"
        description="Test Product"
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    const emailInput = screen.getByLabelText(/Email/i);
    const nameInput = screen.getByLabelText(/Name/i);
    const stripeRadio = screen.getByLabelText(/Stripe/i);
    const submitButton = screen.getByRole('button', { name: /Pay/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.click(stripeRadio);
    
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(financeService.createPayment).toHaveBeenCalledWith({
        amount: 9999,
        currency: 'USD',
        provider: 'stripe_cards',
        customer_email: 'test@example.com',
        customer_name: 'John Doe',
        description: 'Test Product'
      });
    });

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalledWith(mockSession);
    });
  });

  test('handles payment error', async () => {
    const error = new Error('Payment failed');
    (financeService.createPayment as jest.Mock).mockRejectedValue(error);

    renderWithProviders(
      <CheckoutForm
        amount={9999}
        currency="USD"
        description="Test Product"
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    const emailInput = screen.getByLabelText(/Email/i);
    const submitButton = screen.getByRole('button', { name: /Pay/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(error);
      expect(screen.getByText(/Payment failed/i)).toBeInTheDocument();
    });
  });

  test('displays loading state during payment processing', async () => {
    (financeService.createPayment as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 1000))
    );

    renderWithProviders(
      <CheckoutForm
        amount={9999}
        currency="USD"
        description="Test Product"
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    const emailInput = screen.getByLabelText(/Email/i);
    const submitButton = screen.getByRole('button', { name: /Pay/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);

    expect(screen.getByText(/Processing/i)).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  test('switches between payment providers', () => {
    renderWithProviders(
      <CheckoutForm
        amount={9999}
        currency="USD"
        description="Test Product"
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    const stripeRadio = screen.getByLabelText(/Stripe/i);
    const paypalRadio = screen.getByLabelText(/PayPal/i);

    // Initially Stripe should be selected
    expect(stripeRadio).toBeChecked();
    expect(paypalRadio).not.toBeChecked();

    // Switch to PayPal
    fireEvent.click(paypalRadio);
    expect(stripeRadio).not.toBeChecked();
    expect(paypalRadio).toBeChecked();
  });
});
