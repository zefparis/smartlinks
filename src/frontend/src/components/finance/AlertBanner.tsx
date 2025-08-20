/**
 * AlertBanner Component
 * Displays finance-related alerts and warnings
 */

import { AlertTriangle, Info, XCircle, X } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';
import type { Alert as AlertType } from '../../services/finance';

interface AlertBannerProps {
  alerts: AlertType[];
  onDismiss?: (alertId: string) => void;
  className?: string;
}

const alertIcons = {
  info: Info,
  warning: AlertTriangle,
  error: XCircle,
};

const alertStyles = {
  info: 'border-blue-200 bg-blue-50 text-blue-900',
  warning: 'border-yellow-200 bg-yellow-50 text-yellow-900',
  error: 'border-red-200 bg-red-50 text-red-900',
};

export function AlertBanner({ alerts, onDismiss, className }: AlertBannerProps) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className={cn('space-y-2', className)}>
      {alerts.map((alert) => {
        const Icon = alertIcons[alert.severity];
        const style = alertStyles[alert.severity];
        
        return (
          <Alert key={alert.id} className={cn('relative', style)}>
            <Icon className="h-4 w-4" />
            <AlertTitle className="pr-8">
              {alert.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </AlertTitle>
            <AlertDescription>{alert.message}</AlertDescription>
            {onDismiss && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-2 top-2 h-6 w-6"
                onClick={() => onDismiss(alert.id)}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </Alert>
        );
      })}
    </div>
  );
}
