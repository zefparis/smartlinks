/**
 * KPICard Component
 * Displays key performance indicators for finance dashboard
 */

import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Skeleton } from '../ui/skeleton';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../../lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    label: string;
  };
  icon?: React.ReactNode;
  loading?: boolean;
  className?: string;
}

export function KPICard({ title, value, subtitle, trend, icon, loading, className }: KPICardProps) {
  if (loading) {
    return (
      <Card className={className}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-4" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-32 mb-1" />
          <Skeleton className="h-3 w-20" />
        </CardContent>
      </Card>
    );
  }

  const TrendIcon = trend ? (
    trend.value > 0 ? TrendingUp : 
    trend.value < 0 ? TrendingDown : 
    Minus
  ) : null;

  const trendColor = trend ? (
    trend.value > 0 ? 'text-green-600' : 
    trend.value < 0 ? 'text-red-600' : 
    'text-gray-600'
  ) : '';

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
        {trend && TrendIcon && (
          <div className={cn('flex items-center gap-1 mt-2', trendColor)}>
            <TrendIcon className="h-3 w-3" />
            <span className="text-xs font-medium">
              {Math.abs(trend.value)}% {trend.label}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
