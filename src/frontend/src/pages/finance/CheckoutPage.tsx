/**
 * Checkout Page
 * Demo page for testing checkout flow
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { CheckoutForm } from '../../components/finance/CheckoutForm';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { CheckCircle } from 'lucide-react';

export function CheckoutPage() {
  const [amount, setAmount] = useState(99.99);
  const [description, setDescription] = useState('Test Payment');
  const [showCheckout, setShowCheckout] = useState(false);
  const [successSession, setSuccessSession] = useState<any>(null);

  const handleSuccess = (session: any) => {
    setSuccessSession(session);
    setShowCheckout(false);
  };

  const handleStartCheckout = () => {
    setShowCheckout(true);
    setSuccessSession(null);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Checkout Demo</h1>
        <p className="text-muted-foreground">
          Test the multi-provider checkout flow
        </p>
      </div>

      {!showCheckout && !successSession && (
        <Card className="max-w-lg">
          <CardHeader>
            <CardTitle>Configure Test Payment</CardTitle>
            <CardDescription>
              Set up a test payment to process through the checkout flow
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="amount">Amount (USD)</Label>
              <Input
                id="amount"
                type="number"
                step="0.01"
                min="0.50"
                value={amount}
                onChange={(e) => setAmount(parseFloat(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Payment description..."
              />
            </div>
            <Button onClick={handleStartCheckout} className="w-full">
              Start Checkout
            </Button>
          </CardContent>
        </Card>
      )}

      {showCheckout && (
        <div className="flex justify-center">
          <CheckoutForm
            amount={Math.round(amount * 100)} // Convert to cents
            currency="USD"
            description={description}
            onSuccess={handleSuccess}
            onCancel={() => setShowCheckout(false)}
          />
        </div>
      )}

      {successSession && (
        <Card className="max-w-lg border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-800">
              <CheckCircle className="h-5 w-5" />
              Payment Successful!
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Session ID:</span>
                <span className="font-mono">{successSession.session_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Payment ID:</span>
                <span className="font-mono">{successSession.payment_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status:</span>
                <span className="font-medium capitalize">{successSession.status}</span>
              </div>
            </div>
            <Button 
              onClick={() => {
                setSuccessSession(null);
                setShowCheckout(false);
              }}
              className="mt-4 w-full"
              variant="outline"
            >
              Start New Payment
            </Button>
          </CardContent>
        </Card>
      )}

      <Alert>
        <AlertDescription>
          This is a demo environment. Use test card numbers like 4242 4242 4242 4242 for Stripe.
        </AlertDescription>
      </Alert>
    </div>
  );
}
