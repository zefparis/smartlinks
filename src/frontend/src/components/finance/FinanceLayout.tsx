/**
 * FinanceLayout Component
 * Layout wrapper for all finance pages with sub-navigation
 */

import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { Card } from '../ui/card';
import { Tabs, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  LayoutDashboard,
  CreditCard, 
  ArrowUpRight, 
  FileCheck, 
  Calculator,
  History,
  ShoppingCart
} from 'lucide-react';

const financeRoutes = [
  {
    path: '/dashboard/finance',
    label: 'Overview',
    icon: LayoutDashboard,
    exact: true
  },
  {
    path: '/dashboard/finance/payments',
    label: 'Payments',
    icon: CreditCard,
  },
  {
    path: '/dashboard/finance/payouts',
    label: 'Payouts',
    icon: ArrowUpRight,
  },
  {
    path: '/dashboard/finance/reconciliation',
    label: 'Reconciliation',
    icon: FileCheck,
  },
  {
    path: '/dashboard/finance/fees',
    label: 'Fees',
    icon: Calculator,
  },
  {
    path: '/dashboard/finance/user-history',
    label: 'User History',
    icon: History,
  },
  {
    path: '/dashboard/finance/checkout',
    label: 'Checkout',
    icon: ShoppingCart,
  },
];

export function FinanceLayout() {
  const location = useLocation();
  
  // Determine active tab based on current path
  const currentPath = location.pathname;
  const activeTab = financeRoutes.find(route => 
    route.exact ? route.path === currentPath : currentPath.startsWith(route.path)
  )?.path || '/dashboard/finance';

  return (
    <div className="flex flex-col gap-6">
      {/* Finance Section Header */}
      <div className="flex flex-col gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Finance</h1>
          <p className="text-muted-foreground">
            Manage payments, payouts, reconciliation and financial analytics
          </p>
        </div>

        {/* Sub-navigation Tabs */}
        <div className="border-b">
          <nav className="flex gap-6">
            {financeRoutes.map((route) => {
              const Icon = route.icon;
              const isActive = route.exact 
                ? currentPath === route.path 
                : currentPath.startsWith(route.path) && route.path !== '/dashboard/finance';
              
              return (
                <NavLink
                  key={route.path}
                  to={route.path}
                  className={({ isActive: linkActive }) => `
                    flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 transition-colors
                    ${linkActive || isActive
                      ? 'border-primary text-foreground' 
                      : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
                    }
                  `}
                >
                  <Icon className="h-4 w-4" />
                  {route.label}
                </NavLink>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Page Content */}
      <div className="flex-1">
        <Outlet />
      </div>
    </div>
  );
}
