/**
 * CheckoutPage
 * Page complète pour le checkout multi-provider (Stripe, PayPal)
 * Route : /finance/checkout
 */

import { CheckoutForm } from "./CheckoutForm";
import { Card, CardHeader, CardTitle, CardDescription } from "../ui/card";

export function CheckoutPage() {
  // Simu : Montant, devise, description. (à remplacer par vrai panier/contexte si besoin)
  const amount = 1999; // 19,99 €
  const currency = "EUR";
  const description = "Abonnement SmartLinks Pro (1 mois)";

  // Actions à la fin du paiement
  const handleSuccess = (session: any) => {
    // Redirige, affiche un toast, ou recharge la page selon tes UX standards
    window.location.href = "/finance/payments"; // Ex : va sur l’historique des paiements
  };

  const handleCancel = () => {
    window.location.href = "/finance";
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl flex flex-col gap-8">
        <Card className="shadow-2xl rounded-2xl border-0 bg-card transition-shadow duration-200">
          <CardHeader className="bg-background/90 rounded-t-2xl px-8 pt-8 pb-4">
            <CardTitle className="text-xl font-bold text-foreground">Paiement sécurisé</CardTitle>
            <CardDescription className="text-base text-muted-foreground">
              Finalise ton achat SmartLinks en choisissant ta méthode de paiement.
            </CardDescription>
          </CardHeader>
          <CheckoutForm
            amount={amount}
            currency={currency}
            description={description}
            onSuccess={handleSuccess}
            onCancel={handleCancel}
          />
        </Card>
      </div>
    </div>
  );
}
