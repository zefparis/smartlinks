// src/App.tsx
import { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ServiceStatusProvider } from './contexts/ServiceStatusContext';
import AppLayout from './components/layout/AppLayout';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Clicks from './pages/Clicks';
import History from './pages/History';
import Settings from './pages/Settings';
import AssistantPage from './pages/Assistant';
import IAAlgorithmsPage from './pages/IAAlgorithms';
import IAModelPage from './pages/IAModel';
import IAAnalysisPage from './pages/IAAnalysis';
import IAStatusPage from './pages/IAStatus';
import { 
  FinanceLayout,
  DashboardPage as FinanceDashboardPage,
  PaymentsPage,
  PayoutsPage,
  ReconciliationPage,
  FeesPage,
  UserHistoryPage,
  CheckoutPage
} from './pages/Finance';
import { ScraperPage } from './pages/ScraperPage';

// Create QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ServiceStatusProvider>
        <AppLayout isLoading={isLoading}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/clicks" element={<Clicks />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/assistant" element={<AssistantPage />} />
            <Route path="/ia/algorithms" element={<IAAlgorithmsPage />} />
            <Route path="/ia/model" element={<IAModelPage />} />
            <Route path="/ia/analysis" element={<IAAnalysisPage />} />
            <Route path="/ia/status" element={<IAStatusPage />} />
            <Route path="/tools/scraper" element={<ScraperPage />} />
            <Route path="/dashboard/finance" element={<FinanceLayout />}>
              <Route index element={<FinanceDashboardPage />} />
              <Route path="payments" element={<PaymentsPage />} />
              <Route path="payouts" element={<PayoutsPage />} />
              <Route path="reconciliation" element={<ReconciliationPage />} />
              <Route path="fees" element={<FeesPage />} />
              <Route path="user-history" element={<UserHistoryPage />} />
              <Route path="checkout" element={<CheckoutPage />} />
            </Route>
          </Routes>
        </AppLayout>
      </ServiceStatusProvider>
    </QueryClientProvider>
  );
}
