# SmartLinks Finance Module Documentation

## Overview
The SmartLinks Finance Module is a comprehensive frontend solution for managing payments, payouts, reconciliation, and financial analytics. Built with React, TypeScript, and shadcn/ui components, it provides a production-ready interface for financial operations.

## Architecture

### Directory Structure
```
src/
├── components/
│   └── finance/
│       ├── AlertBanner.tsx        # Finance alerts display
│       ├── CheckoutForm.tsx       # Multi-provider checkout UI
│       ├── FeesTracker.tsx        # Fee analysis and tracking
│       ├── FinanceDashboard.tsx   # Main dashboard with KPIs
│       ├── KPICard.tsx            # Key metric display cards
│       ├── PaymentsTable.tsx      # Payment transactions table
│       ├── PayoutsTable.tsx       # Payout management table
│       ├── ReconciliationTable.tsx # Reconciliation reports
│       ├── RefundModal.tsx        # Refund processing dialog
│       ├── StatusBadge.tsx        # Status indicator badges
│       └── UserPaymentHistory.tsx # User payment history view
├── pages/
│   ├── Finance.tsx                # Main finance layout
│   └── finance/
│       ├── CheckoutPage.tsx       # Checkout demo page
│       ├── DashboardPage.tsx      # Finance dashboard
│       ├── FeesPage.tsx           # Fees tracking page
│       ├── PaymentsPage.tsx       # Payments management
│       ├── PayoutsPage.tsx        # Payouts management
│       ├── ReconciliationPage.tsx # Reconciliation view
│       └── UserHistoryPage.tsx    # User history search
├── hooks/
│   └── useFinance.ts              # Finance data hooks
└── services/
    └── finance.ts                 # Finance API service

```

## Components

### Core Components

#### FinanceDashboard
Main dashboard component displaying:
- KPI cards (total revenue, pending payments, success rate, active customers)
- Revenue trend chart
- Provider distribution pie chart
- Finance alerts
- Tabbed interface for payments, payouts, and reconciliation

#### PaymentsTable
Features:
- Search by transaction ID, customer, or reference
- Status filtering (pending, captured, failed, refunded)
- Provider filtering (Stripe, PayPal)
- Date range selection
- CSV export functionality
- Refund action buttons
- Pagination support

#### PayoutsTable
Capabilities:
- Status-based filtering
- Overdue payout alerts
- Execute, mark paid, and cancel actions
- Provider and date filtering
- Amount and count display

#### ReconciliationTable
Displays:
- Match rates with progress bars
- Transaction counts (matched, unmatched, pending)
- Amount totals
- CSV export per report
- Color-coded status indicators

#### CheckoutForm
Multi-provider checkout supporting:
- Stripe card payments
- PayPal payments
- Customer information collection
- Real-time payment status polling
- Success/failure feedback

### UI Components

#### StatusBadge
Displays colored badges for payment/payout statuses:
- **Pending**: Yellow
- **Captured/Paid**: Green
- **Failed**: Red
- **Refunded**: Purple
- **Cancelled**: Gray

#### KPICard
Shows key metrics with:
- Title and value
- Optional trend indicators
- Loading skeleton states
- Icon support

#### RefundModal
Handles refund processing with:
- Full/partial refund options
- Amount validation
- Optional reason input
- Confirmation dialog

## Hooks

### Data Fetching Hooks
- `useFinanceDashboard()` - Dashboard metrics and charts
- `usePayments()` - Payment transactions with filters
- `usePayouts()` - Payout management data
- `useReconciliation()` - Reconciliation reports
- `useFees()` - Fee tracking data
- `useFinanceAlerts()` - Real-time alerts
- `useUserPaymentHistory()` - User-specific payments

### Mutation Hooks
- `useCreatePayment()` - Initiate new payments
- `useRefundPayment()` - Process refunds
- `useExecutePayout()` - Execute scheduled payouts
- `useExportPaymentsCSV()` - Export payment data
- `useExportReconciliationCSV()` - Export reconciliation reports

## API Integration

### Endpoints
```typescript
// Payments
GET    /api/finance/payments
POST   /api/finance/payments
GET    /api/finance/payments/:id
POST   /api/finance/payments/:id/refund
GET    /api/finance/payments/export

// Payouts
GET    /api/finance/payouts
POST   /api/finance/payouts
POST   /api/finance/payouts/:id/execute
POST   /api/finance/payouts/:id/mark-paid

// Reconciliation
GET    /api/finance/reconciliation
POST   /api/finance/reconciliation/run
GET    /api/finance/reconciliation/export

// Dashboard & Analytics
GET    /api/finance/dashboard
GET    /api/finance/balances
GET    /api/finance/fees
GET    /api/finance/alerts
```

## Features

### Payment Management
- View all payment transactions
- Filter by status, provider, date range
- Search by ID, customer, reference
- Process full/partial refunds
- Export transaction data to CSV

### Payout Management
- Schedule and execute payouts
- Track payout status
- Handle overdue payouts
- Manual marking as paid
- Provider-specific payout handling

### Reconciliation
- Automated daily reconciliation
- Match rate tracking
- Discrepancy identification
- Detailed reconciliation reports
- Export reconciliation data

### Fee Tracking
- Processing fee analysis
- Provider fee comparison
- Time-based fee trends
- Industry rate benchmarks
- Fee optimization insights

### Multi-Provider Support
- **Stripe**: Card payments, refunds, payouts
- **PayPal**: Express checkout, refunds
- Extensible architecture for additional providers

## Usage Examples

### Basic Dashboard Implementation
```tsx
import { FinanceDashboard } from '@/components/finance/FinanceDashboard';

function FinancePage() {
  return <FinanceDashboard />;
}
```

### Payment Processing with Refunds
```tsx
import { usePayments, useRefundPayment } from '@/hooks/useFinance';
import { PaymentsTable } from '@/components/finance/PaymentsTable';

function PaymentsManager() {
  const { data: payments } = usePayments();
  const refundMutation = useRefundPayment();

  const handleRefund = (paymentId: string, amount: number) => {
    refundMutation.mutate({
      payment_id: paymentId,
      amount,
      reason: 'Customer request'
    });
  };

  return (
    <PaymentsTable
      payments={payments}
      onRefund={handleRefund}
    />
  );
}
```

### Checkout Integration
```tsx
import { CheckoutForm } from '@/components/finance/CheckoutForm';

function CheckoutPage() {
  return (
    <CheckoutForm
      amount={9999} // in cents
      currency="USD"
      description="Premium Subscription"
      onSuccess={(session) => {
        console.log('Payment successful:', session);
      }}
    />
  );
}
```

## Testing

### Component Testing
```bash
npm run test:components
```

Tests cover:
- Component rendering
- User interactions
- Data fetching
- Error handling
- Accessibility

### Integration Testing
```bash
npm run test:integration
```

Validates:
- API communication
- State management
- Route navigation
- Multi-provider flows

## Performance Optimizations

### Data Fetching
- React Query caching with stale times
- Optimistic updates for mutations
- Background refetching for real-time data
- Pagination for large datasets

### UI Rendering
- Skeleton loading states
- Virtual scrolling for large tables
- Memoized expensive computations
- Code splitting by route

## Security Considerations

### Payment Security
- No sensitive card data stored client-side
- Secure redirect flows for payment providers
- CSRF protection on mutations
- Input validation and sanitization

### Access Control
- Role-based component visibility
- Protected routes for finance pages
- Audit logging for financial actions
- Session-based authentication

## Configuration

### Environment Variables
```env
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLIC_KEY=pk_test_...
VITE_PAYPAL_CLIENT_ID=...
```

### Provider Configuration
```typescript
const providers = {
  stripe_cards: {
    name: 'Stripe',
    icon: CreditCard,
    color: 'purple'
  },
  paypal: {
    name: 'PayPal',
    icon: Wallet,
    color: 'blue'
  }
};
```

## Deployment

### Build Process
```bash
# Install dependencies
npm install

# Run tests
npm test

# Build for production
npm run build

# Preview production build
npm run preview
```

### Production Checklist
- [ ] Environment variables configured
- [ ] API endpoints accessible
- [ ] Payment provider keys set
- [ ] SSL certificates valid
- [ ] Error monitoring enabled
- [ ] Analytics tracking setup
- [ ] Backup procedures in place

## Support

For issues or questions:
- Check the [API Documentation](./API_REFERENCE.md)
- Review [Common Issues](./TROUBLESHOOTING.md)
- Contact the development team

## License
Copyright © 2024 SmartLinks. All rights reserved.
