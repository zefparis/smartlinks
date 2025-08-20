/**
 * CheckoutForm Component
 * Multi-provider checkout UI with real-time status
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Separator } from '../ui/separator';
import { Alert, AlertDescription } from '../ui/alert';
import { Progress } from '../ui/progress';
import { StatusBadge } from './StatusBadge';
import {
  CreditCard,
  Building,
  Wallet,
  Shield,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { useCheckout, useCheckoutStatus } from '../../hooks/useFinance';
import type { CreatePaymentRequest } from '../../services/finance';
import type { CheckoutSession } from '../../services/finance';

interface CheckoutFormProps {
  amount: number;
  currency?: string;
  description?: string;
  onSuccess?: (session: CheckoutSession) => void;
  onCancel?: () => void;
}

export function CheckoutForm({
  amount,
  currency = 'USD',
  description = 'Payment',
  onSuccess,
  onCancel,
}: CheckoutFormProps) {
  const [provider, setProvider] = useState<'stripe_cards' | 'paypal'>('stripe_cards');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pollingEnabled, setPollingEnabled] = useState(false);

  const checkout = useCheckout();
    const { data: status, error: statusError } = useCheckoutStatus(sessionId, pollingEnabled);

  useEffect(() => {
    if (status?.status === 'completed' && onSuccess) {
      setPollingEnabled(false);
      onSuccess(status);
    } else if (status?.status === 'failed' || status?.status === 'cancelled') {
      setPollingEnabled(false);
    }
  }, [status, onSuccess]);

  useEffect(() => {
    if (status?.status === 'completed' && onSuccess) {
      setPollingEnabled(false);
      onSuccess(status);
    }
  }, [status, onSuccess]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const payload: CreatePaymentRequest = {
      amount,
      currency,
      provider,
      meta: {
        customer_email: email,
        customer_name: name,
        description,
        success_url: window.location.href,
        cancel_url: window.location.href,
      },
    };

    checkout.mutate(payload, {
      onSuccess: (data: { payment_id: string; provider: string; session: any; status: string }) => {
        // Extract session_id from the session object or use payment_id as fallback
        const sessionId = data.session?.session_id || data.payment_id;
        setSessionId(sessionId);
        setPollingEnabled(true);
        
        // Check if there's a checkout URL in the session
        const checkoutUrl = data.session?.checkout_url;
        if (checkoutUrl) {
          window.location.href = checkoutUrl;
        }
      },
    });
  };

  const formatAmount = (amt: number, curr: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: curr,
    }).format(amt / 100);
  };

  const getStatusIcon = (st?: string) => {
    switch (st) {
      case 'pending':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-600" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'cancelled':
        return <AlertCircle className="h-5 w-5 text-yellow-600" />;
      default:
        return null;
    }
  };

  const getProgressValue = () => {
    switch (status?.status) {
      case 'pending':
        return 50;
      case 'completed':
        return 100;
      case 'failed':
      case 'cancelled':
        return 0;
      default:
        return 0;
    }
  };

  return (
    <Card className="w-full max-w-xl shadow-2xl rounded-2xl bg-card border-0 transition-shadow duration-200">
      <CardHeader className="bg-background/80 rounded-t-2xl px-8 pt-8 pb-4">
        <CardTitle className="text-xl font-bold text-foreground">Paiement sécurisé</CardTitle>
        <CardDescription className="text-base text-muted-foreground">
          Finalise ton achat de <span className="font-semibold text-foreground">{formatAmount(amount, currency)}</span>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-8 p-8">
        {/* Amount Summary */}
        <div className="rounded-xl bg-muted/70 p-6 flex flex-col gap-1 shadow-inner">
          <div className="flex justify-between items-center">
            <span className="text-base text-muted-foreground">Montant total</span>
            <span className="text-2xl font-bold text-foreground">{formatAmount(amount, currency)}</span>
          </div>
          {description && (
            <p className="mt-2 text-sm text-muted-foreground">{description}</p>
          )}
        </div>

        {/* Status Display */}
        {sessionId && status && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Statut du paiement</span>
              <StatusBadge status={status.status} />
            </div>
            <Progress value={getProgressValue()} className="h-2 rounded-full transition-all duration-300" />
            {status.status === 'pending' && (
              <Alert className="bg-blue-50 border-blue-200 text-blue-900 dark:bg-blue-900/40 dark:border-blue-700 dark:text-blue-100">
                <Loader2 className="h-4 w-4 animate-spin" />
                <AlertDescription>
                  Paiement en attente. Merci de finaliser dans la fenêtre ouverte.
                </AlertDescription>
              </Alert>
            )}
            {status.status === 'completed' && (
              <Alert className="bg-green-50 border-green-200 text-green-900 dark:bg-green-900/40 dark:border-green-700 dark:text-green-100">
                <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-300" />
                <AlertDescription>
                  Paiement réussi ! Transaction ID : {status.payment_id}
                </AlertDescription>
              </Alert>
            )}
            {status.status === 'failed' && (
              <Alert variant="destructive">
                <XCircle className="h-4 w-4" />
                <AlertDescription>
                  Paiement échoué. Merci de réessayer ou d'utiliser un autre moyen.
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {/* Checkout Form */}
        {!sessionId && (
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Payment Provider Selection */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">Méthode de paiement</Label>
              <RadioGroup value={provider} onValueChange={(v: 'stripe_cards' | 'paypal') => setProvider(v)} className="flex flex-col gap-4">
                <div className="flex items-center gap-3 rounded-xl border bg-background p-4 hover:bg-accent/60 transition-colors cursor-pointer focus-within:ring-2 focus-within:ring-primary">
                  <RadioGroupItem value="stripe_cards" id="stripe" />
                  <Label htmlFor="stripe" className="flex-1 cursor-pointer">
                    <div className="flex items-center gap-3">
                      <CreditCard className="h-5 w-5" />
                      <div>
                        <p className="font-medium text-foreground">Carte bancaire</p>
                        <p className="text-sm text-muted-foreground">Stripe • Visa, Mastercard, etc.</p>
                      </div>
                    </div>
                  </Label>
                </div>
                <div className="flex items-center gap-3 rounded-xl border bg-background p-4 hover:bg-accent/60 transition-colors cursor-pointer focus-within:ring-2 focus-within:ring-primary">
                  <RadioGroupItem value="paypal" id="paypal" />
                  <Label htmlFor="paypal" className="flex-1 cursor-pointer">
                    <div className="flex items-center gap-3">
                      <Wallet className="h-5 w-5" />
                      <div>
                        <p className="font-medium text-foreground">PayPal</p>
                        <p className="text-sm text-muted-foreground">Compte PayPal ou paiement invité</p>
                      </div>
                    </div>
                  </Label>
                </div>
              </RadioGroup>
            </div>

            <Separator />

            {/* Customer Information */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="font-semibold">Adresse email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="john@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="rounded-lg px-4 py-2 bg-background focus:ring-2 focus:ring-primary transition-all placeholder:text-muted-foreground"
                  aria-label="Adresse email"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="name" className="font-semibold">Nom complet</Label>
                <Input
                  id="name"
                  type="text"
                  autoComplete="name"
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="rounded-lg px-4 py-2 bg-background focus:ring-2 focus:ring-primary transition-all placeholder:text-muted-foreground"
                  aria-label="Nom complet"
                />
              </div>
            </div>

            {/* Security Notice */}
            <Alert className="bg-muted/80 border-0 shadow-none">
              <Shield className="h-4 w-4" />
              <AlertDescription>
                Tes informations de paiement sont chiffrées et sécurisées. Nous ne stockons jamais tes données bancaires.
              </AlertDescription>
            </Alert>

            {/* Actions */}
            <div className="flex flex-col md:flex-row gap-4 mt-2">
              {onCancel && (
                <Button type="button" variant="outline" onClick={onCancel} className="flex-1 transition-all">
                  Annuler
                </Button>
              )}
              <Button
                type="submit"
                className="flex-1 font-semibold text-lg transition-all"
                disabled={checkout.isPending || !email || !name}
                variant="default"
              >
                {checkout.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Paiement en cours...
                  </>
                ) : (
                  <>
                    <Shield className="mr-2 h-4 w-4" />
                    Payer {formatAmount(amount, currency)}
                  </>
                )}
              </Button>
            </div>
          </form>
        )}

        {/* Success Actions */}
        {status?.status === 'completed' && (
          <div className="flex flex-col md:flex-row gap-4">
            <Button variant="outline" className="flex-1" onClick={() => window.print()}>
              Imprimer le reçu
            </Button>
            <Button className="flex-1" onClick={() => onSuccess?.(status)}>
              Continuer
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
