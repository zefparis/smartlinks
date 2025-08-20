/**
 * RefundModal Component
 * Modal for processing payment refunds
 */

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '../ui/alert';
import type { Payment } from '../../services/finance';

interface RefundModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  payment: Payment | null;
  onRefund: (amount?: number, reason?: string) => void;
  loading?: boolean;
}

export function RefundModal({ open, onOpenChange, payment, onRefund, loading }: RefundModalProps) {
  const [refundType, setRefundType] = useState<'full' | 'partial'>('full');
  const [partialAmount, setPartialAmount] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');

  if (!payment) return null;

  const handleSubmit = () => {
    setError('');
    
    if (refundType === 'partial') {
      const amount = parseFloat(partialAmount);
      if (isNaN(amount) || amount <= 0) {
        setError('Please enter a valid amount');
        return;
      }
      if (amount * 100 > payment.amount) {
        setError('Refund amount cannot exceed payment amount');
        return;
      }
      onRefund(Math.round(amount * 100), reason);
    } else {
      onRefund(undefined, reason);
    }
  };

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount / 100);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Process Refund</DialogTitle>
          <DialogDescription>
            Refund payment {payment.payment_id.slice(0, 8)}...
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Payment Info */}
          <div className="rounded-lg bg-muted p-3 space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Original Amount:</span>
              <span className="font-medium">
                {formatAmount(payment.amount, payment.currency)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Provider:</span>
              <span className="font-medium capitalize">
                {payment.provider.replace('_', ' ')}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Date:</span>
              <span className="font-medium">
                {new Date(payment.date).toLocaleDateString()}
              </span>
            </div>
          </div>

          {/* Refund Type */}
          <div className="space-y-3">
            <Label>Refund Type</Label>
            <RadioGroup value={refundType} onValueChange={(v) => setRefundType(v as 'full' | 'partial')}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="full" id="full" />
                <Label htmlFor="full" className="font-normal">
                  Full Refund ({formatAmount(payment.amount, payment.currency)})
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="partial" id="partial" />
                <Label htmlFor="partial" className="font-normal">
                  Partial Refund
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Partial Amount */}
          {refundType === 'partial' && (
            <div className="space-y-2">
              <Label htmlFor="amount">Refund Amount</Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                  {payment.currency.toUpperCase()}
                </span>
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  min="0.01"
                  max={payment.amount / 100}
                  value={partialAmount}
                  onChange={(e) => setPartialAmount(e.target.value)}
                  className="pl-14"
                  placeholder="0.00"
                />
              </div>
            </div>
          )}

          {/* Reason */}
          <div className="space-y-2">
            <Label htmlFor="reason">Reason for Refund (Optional)</Label>
            <Textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Enter reason for refund..."
              rows={3}
            />
          </div>

          {/* Error */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Warning */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              This action cannot be undone. The refund will be processed immediately.
            </AlertDescription>
          </Alert>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? 'Processing...' : 'Process Refund'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
