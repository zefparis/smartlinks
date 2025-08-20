/**
 * Client Portal - Espace client/affilié self-service complet
 * Dashboard, stats, paiements, settings pour les clients
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  DollarSign, 
  TrendingUp, 
  Users, 
  Calendar,
  Download,
  Settings,
  CreditCard,
  FileText,
  Bell,
  Eye,
  ExternalLink
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

interface ClientStats {
  total_earnings: number;
  pending_payout: number;
  clicks_count: number;
  conversion_rate: number;
  current_tier: string;
  next_tier_progress: number;
}

interface PayoutMethod {
  id: string;
  type: 'stripe' | 'paypal' | 'bank_transfer';
  details: any;
  is_default: boolean;
  status: 'active' | 'pending' | 'disabled';
}

interface RecentPayout {
  id: string;
  amount: number;
  date: string;
  status: string;
  method: string;
}

interface EarningsHistory {
  date: string;
  earnings: number;
  clicks: number;
}

export function ClientPortal() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState<ClientStats | null>(null);
  const [payoutMethods, setPayoutMethods] = useState<PayoutMethod[]>([]);
  const [recentPayouts, setRecentPayouts] = useState<RecentPayout[]>([]);
  const [earningsHistory, setEarningsHistory] = useState<EarningsHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadClientData();
  }, []);

  const loadClientData = async () => {
    try {
      setLoading(true);
      // Simuler le chargement des données client
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setStats({
        total_earnings: 2847.50,
        pending_payout: 347.20,
        clicks_count: 15420,
        conversion_rate: 3.2,
        current_tier: 'Gold',
        next_tier_progress: 67
      });

      setPayoutMethods([
        {
          id: '1',
          type: 'stripe',
          details: { last4: '4242', brand: 'Visa' },
          is_default: true,
          status: 'active'
        },
        {
          id: '2',
          type: 'paypal',
          details: { email: 'client@example.com' },
          is_default: false,
          status: 'active'
        }
      ]);

      setRecentPayouts([
        { id: '1', amount: 250.00, date: '2025-01-15', status: 'completed', method: 'Stripe' },
        { id: '2', amount: 180.50, date: '2025-01-08', status: 'completed', method: 'PayPal' },
        { id: '3', amount: 320.75, date: '2025-01-01', status: 'processing', method: 'Stripe' }
      ]);

      setEarningsHistory([
        { date: '2025-01-01', earnings: 45.20, clicks: 1200 },
        { date: '2025-01-02', earnings: 67.80, clicks: 1450 },
        { date: '2025-01-03', earnings: 52.30, clicks: 1180 },
        { date: '2025-01-04', earnings: 78.90, clicks: 1680 },
        { date: '2025-01-05', earnings: 91.20, clicks: 1920 },
        { date: '2025-01-06', earnings: 84.50, clicks: 1750 },
        { date: '2025-01-07', earnings: 103.40, clicks: 2100 }
      ]);

    } catch (error) {
      console.error('Error loading client data:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Gains Totaux</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_earnings.toFixed(2)} €</div>
            <p className="text-xs text-muted-foreground">
              +12.5% par rapport au mois dernier
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Paiement Pending</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.pending_payout.toFixed(2)} €</div>
            <p className="text-xs text-muted-foreground">
              Prochain paiement le 25/01
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Clics Total</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.clicks_count.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              +8.2% cette semaine
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Taux Conversion</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.conversion_rate}%</div>
            <p className="text-xs text-muted-foreground">
              Moyenne industrie: 2.8%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tier Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Statut Affilié
            <Badge variant="secondary">{stats?.current_tier}</Badge>
          </CardTitle>
          <CardDescription>
            Progression vers le niveau Platinum
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progression</span>
              <span>{stats?.next_tier_progress}%</span>
            </div>
            <Progress value={stats?.next_tier_progress} className="h-2" />
            <p className="text-xs text-muted-foreground">
              Plus que 850€ de gains pour atteindre le niveau Platinum (+15% de commission)
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Évolution des Gains</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={earningsHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(date) => format(new Date(date), 'dd/MM')} />
                <YAxis />
                <Tooltip 
                  labelFormatter={(date) => format(new Date(date), 'dd MMMM yyyy', { locale: fr })}
                  formatter={(value: number) => [`${value.toFixed(2)} €`, 'Gains']}
                />
                <Line type="monotone" dataKey="earnings" stroke="#3b82f6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Clics par Jour</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={earningsHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(date) => format(new Date(date), 'dd/MM')} />
                <YAxis />
                <Tooltip 
                  labelFormatter={(date) => format(new Date(date), 'dd MMMM yyyy', { locale: fr })}
                  formatter={(value: number) => [value.toLocaleString(), 'Clics']}
                />
                <Bar dataKey="clicks" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderPayments = () => (
    <div className="space-y-6">
      {/* Payout Methods */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Méthodes de Paiement
            <Button size="sm">
              <CreditCard className="h-4 w-4 mr-2" />
              Ajouter
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {payoutMethods.map((method) => (
              <div key={method.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <CreditCard className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">
                      {method.type === 'stripe' ? 'Carte Bancaire' : 
                       method.type === 'paypal' ? 'PayPal' : 'Virement'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {method.type === 'stripe' ? `**** ${method.details.last4}` : method.details.email}
                    </p>
                  </div>
                  {method.is_default && (
                    <Badge variant="secondary">Par défaut</Badge>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={method.status === 'active' ? 'default' : 'secondary'}>
                    {method.status === 'active' ? 'Actif' : 'Inactif'}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    <Settings className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Payouts */}
      <Card>
        <CardHeader>
          <CardTitle>Historique des Paiements</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentPayouts.map((payout: any) => (
              <div key={payout.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                    <DollarSign className="h-4 w-4 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <p className="font-medium">{payout.amount.toFixed(2)} €</p>
                    <p className="text-sm text-muted-foreground">
                      {format(new Date(payout.date), 'dd MMMM yyyy', { locale: fr })} • {payout.method}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={payout.status === 'completed' ? 'default' : 'secondary'}>
                    {payout.status === 'completed' ? 'Terminé' : 'En cours'}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderReports = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Rapports et Exports</CardTitle>
          <CardDescription>
            Téléchargez vos rapports de performance et documents fiscaux
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline" className="h-20 flex-col">
              <FileText className="h-6 w-6 mb-2" />
              Rapport Mensuel
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <Download className="h-6 w-6 mb-2" />
              Export CSV
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <FileText className="h-6 w-6 mb-2" />
              Factures
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <FileText className="h-6 w-6 mb-2" />
              Justificatifs
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Paramètres du Compte</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Notifications Email</p>
                <p className="text-sm text-muted-foreground">Recevoir les notifications par email</p>
              </div>
              <Button variant="outline" size="sm">Configurer</Button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Seuil de Paiement</p>
                <p className="text-sm text-muted-foreground">Montant minimum pour déclencher un paiement</p>
              </div>
              <Button variant="outline" size="sm">50€</Button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Fréquence des Paiements</p>
                <p className="text-sm text-muted-foreground">À quelle fréquence recevoir les paiements</p>
              </div>
              <Button variant="outline" size="sm">Hebdomadaire</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Liens d'Affiliation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm font-medium mb-2">Votre lien principal:</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 p-2 bg-background rounded text-sm">
                  https://smartlinks.com/ref/ABC123
                </code>
                <Button size="sm" variant="outline">Copier</Button>
              </div>
            </div>
            <Button className="w-full">
              <ExternalLink className="h-4 w-4 mr-2" />
              Générer Nouveau Lien
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Espace Client</h1>
              <p className="text-muted-foreground">Gérez vos gains et paramètres d'affiliation</p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Bell className="h-4 w-4 mr-2" />
                Notifications
              </Button>
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Support
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="payments">Paiements</TabsTrigger>
            <TabsTrigger value="reports">Rapports</TabsTrigger>
            <TabsTrigger value="settings">Paramètres</TabsTrigger>
          </TabsList>

          <div className="mt-6">
            <TabsContent value="dashboard">
              {renderDashboard()}
            </TabsContent>
            <TabsContent value="payments">
              {renderPayments()}
            </TabsContent>
            <TabsContent value="reports">
              {renderReports()}
            </TabsContent>
            <TabsContent value="settings">
              {renderSettings()}
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
