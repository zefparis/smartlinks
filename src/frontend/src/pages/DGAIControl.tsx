/**
 * DG AI Control page for global RCP management
 */

import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, Activity, Settings, Plus, Eye, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { classes } from '@/lib/design-system';

interface RCPPolicy {
  id: string;
  name: string;
  scope: 'global' | 'algorithm' | 'segment';
  mode: 'monitor' | 'enforce';
  enabled: boolean;
  authority_required: string;
  created_at: string;
  updated_at: string;
}

interface RCPEvaluation {
  id: string;
  policy_id: string;
  algo_key: string;
  result: 'allowed' | 'modified' | 'blocked' | 'mixed';
  created_at: string;
  stats: {
    actions_allowed: number;
    actions_modified: number;
    actions_blocked: number;
    risk_cost: number;
  };
}

export function DGAIControl() {
  const [activeTab, setActiveTab] = useState('policies');
  const [policies, setPolicies] = useState<RCPPolicy[]>([]);
  const [evaluations, setEvaluations] = useState<RCPEvaluation[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'policies') {
        // Mock data - would fetch from API
        setPolicies([
          {
            id: 'global-safety-001',
            name: 'Global Safety Guards',
            scope: 'global',
            mode: 'enforce',
            enabled: true,
            authority_required: 'dg_ai',
            created_at: '2024-01-15T10:00:00Z',
            updated_at: '2024-01-15T10:00:00Z'
          },
          {
            id: 'traffic-limits-001',
            name: 'Traffic Optimizer Limits',
            scope: 'algorithm',
            mode: 'monitor',
            enabled: true,
            authority_required: 'admin',
            created_at: '2024-01-14T15:30:00Z',
            updated_at: '2024-01-14T15:30:00Z'
          }
        ]);
      } else if (activeTab === 'evaluations') {
        // Mock data - would fetch from API
        setEvaluations([
          {
            id: 'eval-001',
            policy_id: 'global-safety-001',
            algo_key: 'traffic_optimizer',
            result: 'modified',
            created_at: '2024-01-15T14:30:00Z',
            stats: {
              actions_allowed: 3,
              actions_modified: 2,
              actions_blocked: 1,
              risk_cost: 2.5
            }
          }
        ]);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePolicy = () => {
    // Would open policy creation modal
    console.log('Create new policy');
  };

  const handleDeletePolicy = (policyId: string) => {
    // Would delete policy after confirmation
    console.log('Delete policy:', policyId);
  };

  const getScopeVariant = (scope: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (scope) {
      case 'global': return 'destructive';
      case 'algorithm': return 'default';
      case 'segment': return 'secondary';
      default: return 'outline';
    }
  };

  const getModeVariant = (mode: string): "default" | "secondary" | "destructive" | "outline" => {
    return mode === 'enforce' ? 'destructive' : 'secondary';
  };

  const getResultVariant = (result: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (result) {
      case 'allowed': return 'default';
      case 'modified': return 'secondary';
      case 'blocked': return 'destructive';
      case 'mixed': return 'outline';
      default: return 'outline';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Shield className="w-8 h-8 text-blue-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">DG AI Control</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Gestion globale des politiques de contrôle runtime (RCP)
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className={cn(classes.card.base)}>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Politiques actives</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">12</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(classes.card.base)}>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <Activity className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Évaluations (24h)</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">247</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(classes.card.base)}>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Actions bloquées</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">8</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(classes.card.base)}>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                <Settings className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Coût risque (€)</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">156.7</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Card className={cn(classes.card.base)}>
        <CardContent className="p-0">
          <Tabs defaultValue="policies" className="w-full">
            <TabsList className="w-full justify-start rounded-none border-b">
              <TabsTrigger value="policies">Politiques RCP</TabsTrigger>
              <TabsTrigger value="evaluations">Évaluations</TabsTrigger>
              <TabsTrigger value="analytics">Analytiques</TabsTrigger>
            </TabsList>

            {loading ? (
              <div className="p-6 space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-32 w-full" />
              </div>
            ) : (
              <>
                <TabsContent value="policies" className="p-6 mt-0">
                  <div>
                    <div className="flex justify-between items-center mb-6">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Politiques RCP</h3>
                      <Button
                        onClick={handleCreatePolicy}
                        className={cn(classes.button.base, classes.button.variants.primary)}
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Nouvelle politique
                      </Button>
                    </div>

                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Politique</TableHead>
                            <TableHead>Portée</TableHead>
                            <TableHead>Mode</TableHead>
                            <TableHead>Statut</TableHead>
                            <TableHead>Autorité requise</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {policies.map((policy) => (
                            <TableRow key={policy.id}>
                              <TableCell>
                                <div>
                                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{policy.name}</div>
                                  <div className="text-sm text-gray-500 dark:text-gray-400">{policy.id}</div>
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant={getScopeVariant(policy.scope)}>
                                  {policy.scope}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <Badge variant={getModeVariant(policy.mode)}>
                                  {policy.mode}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <Badge variant={policy.enabled ? 'default' : 'outline'}>
                                  {policy.enabled ? 'Activé' : 'Désactivé'}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-sm text-gray-500 dark:text-gray-400">
                                {policy.authority_required}
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex justify-end gap-2">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="p-1"
                                  >
                                    <Eye className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="p-1 hover:text-red-600"
                                    onClick={() => handleDeletePolicy(policy.id)}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="evaluations" className="p-6 mt-0">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-6">Historique des évaluations</h3>
                    
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Politique</TableHead>
                            <TableHead>Algorithme</TableHead>
                            <TableHead>Résultat</TableHead>
                            <TableHead>Actions</TableHead>
                            <TableHead>Coût risque</TableHead>
                            <TableHead>Date</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {evaluations.map((evaluation) => (
                            <TableRow key={evaluation.id}>
                              <TableCell className="text-sm text-gray-900 dark:text-gray-100">
                                {evaluation.policy_id}
                              </TableCell>
                              <TableCell className="text-sm text-gray-900 dark:text-gray-100">
                                {evaluation.algo_key}
                              </TableCell>
                              <TableCell>
                                <Badge variant={getResultVariant(evaluation.result)}>
                                  {evaluation.result}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-sm text-gray-500 dark:text-gray-400">
                                <div className="text-xs space-y-1">
                                  <div>✅ {evaluation.stats.actions_allowed} autorisées</div>
                                  <div>🔧 {evaluation.stats.actions_modified} modifiées</div>
                                  <div>🚫 {evaluation.stats.actions_blocked} bloquées</div>
                                </div>
                              </TableCell>
                              <TableCell className="text-sm text-gray-900 dark:text-gray-100 font-medium">
                                €{evaluation.stats.risk_cost.toFixed(2)}
                              </TableCell>
                              <TableCell className="text-sm text-gray-500 dark:text-gray-400">
                                {new Date(evaluation.created_at).toLocaleString('fr-FR')}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="analytics" className="p-6 mt-0">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-6">Analytiques RCP</h3>
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <p className="font-medium">📊 Tableau de bord analytique en cours de développement...</p>
                        <p className="text-sm mt-1">
                          Incluera des graphiques de tendances, métriques de performance, et alertes.
                        </p>
                      </AlertDescription>
                    </Alert>
                  </div>
                </TabsContent>
              </>
            )}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
