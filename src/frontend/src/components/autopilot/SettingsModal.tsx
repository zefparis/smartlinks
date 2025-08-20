/**
 * Simple settings modal for algorithm configuration
 */

import React, { useState, useEffect } from 'react';
import { X, Save, RotateCcw } from 'lucide-react';
import autopilotAPI, { Algorithm, AlgorithmSettings, AIPolicy } from '@/api/autopilot';
import { Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription } from '@/components/ui/dialog';

interface SettingsModalProps {
  algorithm: Algorithm;
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsModal({ algorithm, isOpen, onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState('common');
  const [settings, setSettings] = useState<AlgorithmSettings | null>(null);
  const [policy, setPolicy] = useState<AIPolicy | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && algorithm) {
      loadSettings();
    }
  }, [isOpen, algorithm]);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const [settingsData, policyData] = await Promise.all([
        autopilotAPI.getSettings(algorithm.key),
        autopilotAPI.getPolicy(algorithm.key)
      ]);
      setSettings(settingsData);
      setPolicy(policyData);
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings || !policy) return;
    
    setLoading(true);
    try {
      await Promise.all([
        autopilotAPI.updateSettings(algorithm.key, settings.settings),
        autopilotAPI.updatePolicy(algorithm.key, policy)
      ]);
      console.log('Settings saved successfully');
      onClose();
    } catch (error) {
      console.error('Error saving settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    loadSettings();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="shadow-2xl rounded-2xl max-w-4xl w-full max-h-[90vh] p-0 bg-background border-none dark:bg-background/90 backdrop-blur-md">
        <DialogHeader className="p-6 pb-2 border-b bg-background/80 rounded-t-2xl">
          <DialogTitle className="text-2xl font-bold text-foreground">
            Configuration - {algorithm.name}
          </DialogTitle>
          <DialogDescription className="text-base text-muted-foreground">
            Configurez les paramètres et les politiques IA
          </DialogDescription>
        </DialogHeader>

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex space-x-8 px-6">
            {['common', 'advanced', 'ai-policy', 'rcp', 'preview'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                  activeTab === tab
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                {tab === 'common' && 'Commun'}
                {tab === 'advanced' && 'Avancé'}
                {tab === 'ai-policy' && 'Politique IA'}
                {tab === 'rcp' && 'Contrôles RCP'}
                {tab === 'preview' && 'Aperçu'}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <>
              {activeTab === 'common' && (
                <div className="space-y-6">
                  <div className="bg-muted p-4 rounded-lg">
                    <h3 className="font-medium text-foreground mb-4">Paramètres communs</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Activé
                        </label>
                        <input
                          type="checkbox"
                          checked={settings?.settings?.enabled || false}
                          onChange={(e) => setSettings(prev => prev ? {...prev, settings: {...prev.settings, enabled: e.target.checked}} : null)}
                          className="h-4 w-4 text-primary focus:ring-primary border-muted rounded"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Fréquence d'exécution (minutes)
                        </label>
                        <input
                          type="number"
                          value={settings?.settings?.execution_frequency || 60}
                          onChange={(e) => setSettings(prev => prev ? {...prev, settings: {...prev.settings, execution_frequency: parseInt(e.target.value)}} : null)}
                          className="w-full px-3 py-2 border border-muted rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'advanced' && (
                <div className="space-y-6">
                  <div className="bg-muted p-4 rounded-lg">
                    <h3 className="font-medium text-foreground mb-4">Paramètres avancés</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Configuration JSON
                        </label>
                        <textarea
                          value={JSON.stringify(settings?.settings || {}, null, 2)}
                          onChange={(e) => {
                            try {
                              const parsed = JSON.parse(e.target.value);
                              setSettings(prev => prev ? {...prev, settings: parsed} : null);
                            } catch (error) {
                              // Invalid JSON, ignore
                            }
                          }}
                          rows={10}
                          className="w-full px-3 py-2 border border-muted rounded-md focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'ai-policy' && (
                <div className="space-y-6">
                  <div className="bg-muted p-4 rounded-lg">
                    <h3 className="font-medium text-foreground mb-4">Politique IA</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Niveau d'autorité
                        </label>
                        <select
                          value={policy?.authority || 'advisory'}
                          onChange={(e) => setPolicy(prev => prev ? {...prev, authority: e.target.value as any} : null)}
                          className="w-full px-3 py-2 border border-muted rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                          <option value="advisory">Consultatif</option>
                          <option value="safe_apply">Application sécurisée</option>
                          <option value="full_control">Contrôle total</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Budget de risque quotidien (€)
                        </label>
                        <input
                          type="number"
                          value={policy?.risk_budget_daily || 1000}
                          onChange={(e) => setPolicy(prev => prev ? {...prev, risk_budget_daily: parseFloat(e.target.value)} : null)}
                          className="w-full px-3 py-2 border border-muted rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'rcp' && (
                <div className="space-y-6">
                  <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg dark:bg-yellow-900/20 dark:border-yellow-800">
                    <h3 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">Runtime Control Policies</h3>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300">
                      Les politiques RCP permettent de contrôler automatiquement les actions de l'algorithme en temps réel.
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Guards Section */}
                    <div className="bg-red-50 p-4 rounded-lg border border-red-200 dark:bg-red-900/20 dark:border-red-800">
                      <h4 className="font-medium text-red-800 dark:text-red-200 mb-3">🛡️ Guards (Gardes)</h4>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-foreground mb-1">
                            CVR minimum (%)
                          </label>
                          <input
                            type="number"
                            step="0.01"
                            placeholder="ex: 0.03"
                            className="w-full px-3 py-2 border border-muted rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-foreground mb-1">
                            Taux d'erreur maximum (%)
                          </label>
                          <input
                            type="number"
                            step="0.01"
                            placeholder="ex: 0.05"
                            className="w-full px-3 py-2 border border-muted rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Limits Section */}
                    <div className="bg-orange-50 p-4 rounded-lg border border-orange-200 dark:bg-orange-900/20 dark:border-orange-800">
                      <h4 className="font-medium text-orange-800 dark:text-orange-200 mb-3">⚡ Limits (Limites)</h4>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-foreground mb-1">
                            Actions par heure
                          </label>
                          <input
                            type="number"
                            placeholder="ex: 10"
                            className="w-full px-3 py-2 border border-muted rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-foreground mb-1">
                            Risque maximum par action
                          </label>
                          <input
                            type="number"
                            step="0.1"
                            placeholder="ex: 5.0"
                            className="w-full px-3 py-2 border border-muted rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Gates Section */}
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 dark:bg-blue-900/20 dark:border-blue-800">
                      <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-3">🚪 Gates (Portes)</h4>
                      <div className="space-y-3">
                        <div>
                          <label className="flex items-center space-x-2">
                            <input type="checkbox" className="rounded border-muted" />
                            <span className="text-sm text-foreground">Activer uniquement en heures de bureau</span>
                          </label>
                        </div>
                        <div>
                          <label className="flex items-center space-x-2">
                            <input type="checkbox" className="rounded border-muted" />
                            <span className="text-sm text-foreground">Suspendre si volume de trafic faible</span>
                          </label>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-foreground mb-1">
                            Géolocalisation autorisée
                          </label>
                          <select className="w-full px-3 py-2 border border-muted rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary">
                            <option value="">Toutes</option>
                            <option value="US">États-Unis</option>
                            <option value="EU">Europe</option>
                            <option value="FR">France</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Mutations Section */}
                    <div className="bg-green-50 p-4 rounded-lg border border-green-200 dark:bg-green-900/20 dark:border-green-800">
                      <h4 className="font-medium text-green-800 dark:text-green-200 mb-3">🔧 Mutations</h4>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-foreground mb-1">
                            Réduction automatique des poids (%)
                          </label>
                          <input
                            type="number"
                            step="1"
                            placeholder="ex: 20"
                            className="w-full px-3 py-2 border border-muted rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                          />
                        </div>
                        <div>
                          <label className="flex items-center space-x-2">
                            <input type="checkbox" className="rounded border-muted" />
                            <span className="text-sm text-foreground">Limiter les changements delta</span>
                          </label>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-foreground mb-1">
                            Delta maximum (%)
                          </label>
                          <input
                            type="number"
                            step="1"
                            placeholder="ex: 15"
                            className="w-full px-3 py-2 border border-muted rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Preview and Audit */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-purple-50 p-4 rounded-lg border border-purple-200 dark:bg-purple-900/20 dark:border-purple-800">
                      <h4 className="font-medium text-purple-800 dark:text-purple-200 mb-3">🔍 Aperçu RCP</h4>
                      <button className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm transition-colors">
                        Simuler les politiques RCP
                      </button>
                      <p className="text-xs text-purple-600 dark:text-purple-200 mt-2">
                        Testez vos règles sans les appliquer
                      </p>
                    </div>

                    <div className="bg-muted p-4 rounded-lg border border-muted-foreground/20">
                      <h4 className="font-medium text-foreground mb-3">📊 Audit RCP</h4>
                      <button className="w-full px-4 py-2 bg-muted-foreground text-background rounded-md hover:bg-foreground/80 text-sm transition-colors">
                        Voir l'historique des évaluations
                      </button>
                      <p className="text-xs text-muted-foreground mt-2">
                        Consultez les actions bloquées/modifiées
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'preview' && (
                <div className="space-y-6">
                  <div className="bg-blue-50 p-4 rounded-lg dark:bg-blue-900/20">
                    <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-4">Aperçu des actions</h3>
                    <p className="text-blue-700 dark:text-blue-200">
                      Fonctionnalité d'aperçu en cours de développement...
                    </p>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <DialogFooter className="flex items-center justify-between p-6 border-t bg-muted rounded-b-2xl">
          <button
            onClick={handleReset}
            disabled={loading}
            className="flex items-center px-4 py-2 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Réinitialiser
          </button>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              Annuler
            </button>
            <button
              onClick={handleSave}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-primary text-background rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4 mr-2" />
              Sauvegarder
            </button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
