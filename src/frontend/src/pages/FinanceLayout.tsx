/**
 * Finance Page
 * Main finance module page with navigation
 */

import { Outlet, Link, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  LayoutDashboard,
  CreditCard,
  ArrowUpRight,
  FileText,
  Calculator,
  History,
  ShoppingCart,
} from 'lucide-react';

const navigation = [
  {
    name: 'Dashboard',
    href: '/finance',
    icon: LayoutDashboard,
    exact: true,
  },
  {
    name: 'Payments',
    href: '/finance/payments',
    icon: CreditCard,
  },
  {
    name: 'Payouts',
    href: '/finance/payouts',
    icon: ArrowUpRight,
  },
  {
    name: 'Reconciliation',
    href: '/finance/reconciliation',
    icon: FileText,
  },
  {
    name: 'Fees',
    href: '/finance/fees',
    icon: Calculator,
  },
  {
    name: 'User History',
    href: '/finance/user-history',
    icon: History,
  },
  {
    name: 'Checkout Demo',
    href: '/finance/checkout',
    icon: ShoppingCart,
  },
];

export function FinanceLayout() {
  const location = useLocation();

  const isActive = (href: string, exact = false) => {
    if (exact) {
      return location.pathname === href;
    }
    return location.pathname.startsWith(href);
  };

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div className="w-64 border-r bg-background">
        <div className="p-6">
          <h2 className="text-lg font-semibold">Finance</h2>
        </div>
        <nav className="space-y-1 px-3">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href, item.exact);
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  active
                    ? 'bg-accent text-accent-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <Outlet />
      </div>
    </div>
  );
}
