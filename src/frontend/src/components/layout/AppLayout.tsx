// src/components/layout/AppLayout.tsx
import { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';

type AppLayoutProps = {
  children: React.ReactNode;
  isLoading?: boolean;
};

export default function AppLayout({ children, isLoading = false }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-700">
        <div className="h-16 w-16 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-700">
      <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="lg:pl-64">
        <Header setSidebarOpen={setSidebarOpen} />
        <main className="py-8 px-4 sm:px-6 lg:px-8 text-gray-800 dark:text-gray-100">
          {children}
        </main>
      </div>
    </div>
  );
}
