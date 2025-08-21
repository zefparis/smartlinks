/** 
 * Dynamic Scraper Factory for SmartLinks Autopilot
 * Supports execution of any Python scraper from external_scrapers directory
 */

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import apiClient from '@/lib/api';
import { toast } from 'sonner';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, Play, Download, RefreshCw, Info, Search, Eye, CheckCircle } from 'lucide-react';

interface ScraperInfo {
  name: string;
  description?: string;
  entry_point: string;
  requirements: string[];
  params_schema: any;
  status: string;
}

interface ScrapedOffer {
  title?: string;
  url?: string;
  description?: string;
  payout?: number | string;
  category?: string;
  company?: string;
  location?: string;
  date?: string;
  original_data?: any;
  source?: string;
}

interface DiscoveredSource {
  id: number;
  url: string;
  title: string;
  description?: string;
  source_type: string;
  confidence_score: number;
  status: string;
  offers_count: number;
  discovered_at: string;
}

interface DiscoveredOffer {
  id: number;
  title: string;
  url?: string;
  source_url: string;
  payout?: string;
  description?: string;
  category?: string;
  vertical?: string;
  geo?: string;
  network?: string;
  confidence_score: number;
  discovered_at: string;
}

export function ScraperPage() {
  const [scrapers, setScrapers] = useState<ScraperInfo[]>([]);
  const [selectedScraper, setSelectedScraper] = useState<string>('');
  const [scraperParams, setScraperParams] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [scrapedOffers, setScrapedOffers] = useState<ScrapedOffer[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [executionTime, setExecutionTime] = useState<number | null>(null);
  const [health, setHealth] = useState<any>(null);
  const [showLogs, setShowLogs] = useState(false);
  
  // Discovery Scraper state
  const [discoveryStatus, setDiscoveryStatus] = useState<any>(null);
  const [isDiscoveryRunning, setIsDiscoveryRunning] = useState(false);
  const [discoveredSources, setDiscoveredSources] = useState<DiscoveredSource[]>([]);
  const [discoveredOffers, setDiscoveredOffers] = useState<DiscoveredOffer[]>([]);
  const [discoveryLogs, setDiscoveryLogs] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'manual' | 'discovery'>('manual');

  // Load scrapers on component mount
  const loadScrapers = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.listScrapers();
      setScrapers(response.scrapers || []);
      toast.success(`Découvert ${response.count} scrapers`);
    } catch (error: any) {
      console.error('Error loading scrapers:', error);
      toast.error(`Erreur lors du chargement des scrapers: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Load health status
  const loadHealth = async () => {
    try {
      const healthData = await apiClient.scraperHealth();
      setHealth(healthData);
      if (!healthData.ok) {
        toast.warning('Certaines dépendances sont manquantes');
      }
    } catch (error) {
      console.error('Health check failed:', error);
    }
  };

  // Execute selected scraper
  const executeScraper = async () => {
    if (!selectedScraper) {
      toast.error('Veuillez sélectionner un scraper');
      return;
    }

    setIsExecuting(true);
    setLogs([`Démarrage du scraper: ${selectedScraper}...`]);
    setScrapedOffers([]);
    setExecutionTime(null);

    try {
      const response = await apiClient.runScraper(selectedScraper, scraperParams);
      
      setLogs(prev => [...prev, ...response.logs || []]);
      setScrapedOffers(response.offers || []);
      setExecutionTime(response.execution_time || null);
      
      if (response.success) {
        toast.success(`Scraper terminé avec succès! ${response.count} offres trouvées`);
      } else {
        toast.error(`Échec du scraper: ${response.message}`);
      }
    } catch (error: any) {
      const errorMsg = error?.response?.data?.detail || error?.message || 'Erreur inconnue';
      setLogs(prev => [...prev, `ERREUR: ${errorMsg}`]);
      toast.error(`Erreur d'exécution: ${errorMsg}`);
    } finally {
      setIsExecuting(false);
    }
  };

  // Import single offer
  const importOffer = async (offer: ScrapedOffer) => {
    try {
      const response = await apiClient.importOffer(offer);
      if (response.success) {
        toast.success(`Offre importée: ${offer.title || 'Sans titre'}`);
      } else {
        toast.error(`Échec import: ${response.message}`);
      }
    } catch (error: any) {
      const errorMsg = error?.response?.data?.detail || error?.message || 'Erreur inconnue';
      toast.error(`Erreur import: ${errorMsg}`);
    }
  };

  // Discovery Scraper functions
  const loadDiscoveryStatus = async () => {
    try {
      const status = await apiClient.getDiscoveryStatus();
      setDiscoveryStatus(status);
      setIsDiscoveryRunning(status.is_running);
      setDiscoveryLogs(status.logs || []);
    } catch (error: any) {
      console.error('Error loading discovery status:', error);
    }
  };

  const startDiscovery = async () => {
    try {
      setIsDiscoveryRunning(true);
      toast.info('Lancement de l\'exploration autonome...');
      
      const result = await apiClient.startDiscovery();
      
      if (result.success) {
        toast.success(`Exploration terminée! ${result.sources_found} sources et ${result.offers_found} offres trouvées`);
        setDiscoveryLogs(result.logs || []);
        
        // Reload findings
        await loadDiscoveryFindings();
      } else {
        toast.error(`Échec de l'exploration: ${result.message}`);
      }
    } catch (error: any) {
      const errorMsg = error?.response?.data?.detail || error?.message || 'Erreur inconnue';
      toast.error(`Erreur d'exploration: ${errorMsg}`);
    } finally {
      setIsDiscoveryRunning(false);
    }
  };

  const loadDiscoveryFindings = async () => {
    try {
      const findings = await apiClient.getDiscoveryFindings();
      setDiscoveredSources(findings.sources || []);
      setDiscoveredOffers(findings.offers || []);
    } catch (error: any) {
      console.error('Error loading discovery findings:', error);
    }
  };

  const importDiscoveredOffer = async (offerId: number) => {
    try {
      const response = await apiClient.importDiscoveredOffer(offerId);
      if (response.success) {
        toast.success('Offre découverte importée avec succès!');
        // Remove from discovered offers list
        setDiscoveredOffers(prev => prev.filter(offer => offer.id !== offerId));
      } else {
        toast.error(`Échec import: ${response.message}`);
      }
    } catch (error: any) {
      const errorMsg = error?.response?.data?.detail || error?.message || 'Erreur inconnue';
      toast.error(`Erreur import: ${errorMsg}`);
    }
  };

  // Handle parameter changes
  const updateParam = (key: string, value: any) => {
    setScraperParams(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Get current scraper info
  const currentScraper = scrapers.find(s => s.name === selectedScraper);

  // Render parameter inputs based on schema
  const renderParamInputs = () => {
    if (!currentScraper?.params_schema?.properties) {
      return (
        <div className="space-y-4">
          <div>
            <Label htmlFor="pages">Pages à scraper</Label>
            <Input
              id="pages"
              type="number"
              min="1"
              max="10"
              value={scraperParams.pages || 1}
              onChange={(e) => updateParam('pages', parseInt(e.target.value) || 1)}
            />
          </div>
          <div>
            <Label htmlFor="keywords">Mots-clés (optionnel)</Label>
            <Input
              id="keywords"
              value={scraperParams.keywords || ''}
              onChange={(e) => updateParam('keywords', e.target.value)}
              placeholder="Ex: javascript, python..."
            />
          </div>
        </div>
      );
    }

    const properties = currentScraper.params_schema.properties;
    return (
      <div className="space-y-4">
        {Object.entries(properties).map(([key, schema]: [string, any]) => (
          <div key={key}>
            <Label htmlFor={key}>
              {schema.description || key}
              {schema.default !== undefined && (
                <span className="text-sm text-gray-500 ml-2">
                  (défaut: {String(schema.default)})
                </span>
              )}
            </Label>
            {schema.type === 'integer' || schema.type === 'number' ? (
              <Input
                id={key}
                type="number"
                min={schema.minimum}
                max={schema.maximum}
                value={scraperParams[key] || schema.default || ''}
                onChange={(e) => updateParam(key, schema.type === 'integer' ? 
                  parseInt(e.target.value) || schema.default : 
                  parseFloat(e.target.value) || schema.default
                )}
              />
            ) : schema.type === 'boolean' ? (
              <Select
                value={String(scraperParams[key] || schema.default || false)}
                onValueChange={(value) => updateParam(key, value === 'true')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Oui</SelectItem>
                  <SelectItem value="false">Non</SelectItem>
                </SelectContent>
              </Select>
            ) : (
              <Input
                id={key}
                value={scraperParams[key] || schema.default || ''}
                onChange={(e) => updateParam(key, e.target.value)}
                placeholder={schema.description}
              />
            )}
          </div>
        ))}
      </div>
    );
  };

  useEffect(() => {
    loadScrapers();
    loadHealth();
    loadDiscoveryStatus();
    loadDiscoveryFindings();
  }, []);

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100">
          Scraper Factory
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          Exécutez des scrapers manuels ou lancez l'exploration autonome - Aucun droit admin requis
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('manual')}
          className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'manual'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
          }`}
        >
          <Play className="h-4 w-4 inline mr-2" />
          Scrapers Manuels
        </button>
        <button
          onClick={() => setActiveTab('discovery')}
          className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'discovery'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
          }`}
        >
          <Search className="h-4 w-4 inline mr-2" />
          Exploration Autonome
        </button>
      </div>

      {/* Health Status */}
      {health && !health.ok && (
        <Alert variant="destructive">
          <AlertTitle>Dépendances manquantes</AlertTitle>
          <AlertDescription>
            {health.message}
            {health.versions && (
              <div className="mt-2 text-xs">
                Versions: {JSON.stringify(health.versions, null, 2)}
              </div>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Manual Scrapers Tab */}
      {activeTab === 'manual' && (
        <>
          {/* Scraper Selection */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <CardTitle className="flex items-center gap-2">
              <Play className="h-5 w-5" />
              Sélection du Scraper
            </CardTitle>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadScrapers}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              Actualiser
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="ml-2">Chargement des scrapers...</span>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="scraper-select">Scraper disponible</Label>
                  <Select value={selectedScraper} onValueChange={setSelectedScraper}>
                    <SelectTrigger id="scraper-select">
                      <SelectValue placeholder="Choisissez un scraper..." />
                    </SelectTrigger>
                    <SelectContent>
                      {scrapers.map((scraper) => (
                        <SelectItem key={scraper.name} value={scraper.name}>
                          <div className="flex items-center gap-2">
                            <span>{scraper.name}</span>
                            <Badge 
                              variant={scraper.status === 'available' ? 'default' : 
                                     scraper.status === 'missing_deps' ? 'destructive' : 'secondary'}
                              className="text-xs"
                            >
                              {scraper.status}
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {currentScraper && (
                  <div className="space-y-2">
                    <Label>Informations</Label>
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md text-sm">
                      <div className="font-medium">{currentScraper.name}</div>
                      {currentScraper.description && (
                        <div className="text-gray-600 dark:text-gray-400 mt-1">
                          {currentScraper.description}
                        </div>
                      )}
                      <div className="text-xs text-gray-500 mt-2">
                        Entry point: {currentScraper.entry_point}
                      </div>
                      {currentScraper.requirements.length > 0 && (
                        <div className="text-xs text-gray-500 mt-1">
                          Dépendances: {currentScraper.requirements.slice(0, 3).join(', ')}
                          {currentScraper.requirements.length > 3 && '...'}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Parameters */}
              {selectedScraper && (
                <div className="space-y-4 pt-4 border-t">
                  <Label className="text-base font-medium">Paramètres du scraper</Label>
                  {renderParamInputs()}
                </div>
              )}

              {/* Execute Button */}
              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <Button 
                  onClick={executeScraper}
                  disabled={!selectedScraper || isExecuting || (currentScraper?.status === 'error')}
                  className="flex items-center gap-2"
                >
                  {isExecuting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  {isExecuting ? 'Exécution en cours...' : 'Lancer le scraping'}
                </Button>
                
                {logs.length > 0 && (
                  <Button 
                    variant="outline" 
                    onClick={() => setShowLogs(!showLogs)}
                    className="flex items-center gap-2"
                  >
                    <Info className="h-4 w-4" />
                    {showLogs ? 'Masquer' : 'Afficher'} les logs
                  </Button>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Execution Progress */}
      {isExecuting && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              Exécution en cours
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Progress value={undefined} className="w-full" />
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              Scraper: {selectedScraper} - Veuillez patienter...
            </p>
          </CardContent>
        </Card>
      )}

      {/* Logs */}
      {logs.length > 0 && showLogs && (
        <Card>
          <CardHeader>
            <CardTitle>Logs d'exécution</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={logs.join('\n')}
              readOnly
              className="h-40 font-mono text-xs"
              placeholder="Les logs d'exécution apparaîtront ici..."
            />
            {executionTime && (
              <p className="text-sm text-gray-500 mt-2">
                Temps d'exécution: {executionTime.toFixed(2)}s
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {scrapedOffers.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <CardTitle className="flex items-center gap-2">
                <Download className="h-5 w-5" />
                Résultats ({scrapedOffers.length} offres)
              </CardTitle>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    scrapedOffers.forEach(offer => importOffer(offer));
                  }}
                  className="flex items-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Importer tout
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Titre</TableHead>
                    <TableHead>URL</TableHead>
                    <TableHead>Payout</TableHead>
                    <TableHead>Catégorie</TableHead>
                    <TableHead>Entreprise</TableHead>
                    <TableHead>Localisation</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scrapedOffers.map((offer, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium max-w-xs">
                        <div className="truncate" title={offer.title}>
                          {offer.title || 'Sans titre'}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-xs">
                        {offer.url ? (
                          <a 
                            href={offer.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 truncate block"
                            title={offer.url}
                          >
                            {offer.url.length > 30 ? `${offer.url.substring(0, 30)}...` : offer.url}
                          </a>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>
                        {offer.payout ? (
                          typeof offer.payout === 'number' ? 
                            `$${offer.payout.toFixed(2)}` : 
                            String(offer.payout)
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        {offer.category ? (
                          <Badge variant="secondary">{offer.category}</Badge>
                        ) : '-'}
                      </TableCell>
                      <TableCell>{offer.company || '-'}</TableCell>
                      <TableCell>{offer.location || '-'}</TableCell>
                      <TableCell>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => importOffer(offer)}
                          className="flex items-center gap-1"
                        >
                          <Download className="h-3 w-3" />
                          Importer
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

          {/* No scrapers found */}
          {!isLoading && scrapers.length === 0 && (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400">
                  Aucun scraper trouvé dans le dossier external_scrapers/
                </p>
                <p className="text-sm text-gray-400 mt-2">
                  Ajoutez des scrapers Python dans /external_scrapers/ pour les voir apparaître ici
                </p>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Discovery Scraper Tab */}
      {activeTab === 'discovery' && (
        <>
          {/* Discovery Control Panel */}
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5" />
                  Exploration Autonome
                </CardTitle>
                <Button 
                  onClick={startDiscovery}
                  disabled={isDiscoveryRunning}
                  className="flex items-center gap-2"
                >
                  {isDiscoveryRunning ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                  {isDiscoveryRunning ? 'Exploration en cours...' : 'Lancer l\'exploration'}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                  🤖 Exploration Automatique
                </h3>
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  Le bot va scanner Google, Bing et DuckDuckGo pour découvrir de nouvelles sources d'affiliation,
                  analyser automatiquement les patterns d'offres et extraire les données pertinentes.
                </p>
              </div>

              {/* Discovery Status */}
              {discoveryStatus && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                    <div className="text-sm text-gray-500 dark:text-gray-400">État</div>
                    <div className="font-medium">
                      {isDiscoveryRunning ? (
                        <span className="text-orange-600">En cours</span>
                      ) : (
                        <span className="text-green-600">Prêt</span>
                      )}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Sources trouvées</div>
                    <div className="font-medium">{discoveredSources.length}</div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Offres découvertes</div>
                    <div className="font-medium">{discoveredOffers.length}</div>
                  </div>
                </div>
              )}

              {/* Discovery Logs */}
              {discoveryLogs.length > 0 && (
                <div>
                  <Label className="text-base font-medium">Logs d'exploration</Label>
                  <Textarea
                    value={discoveryLogs.join('\n')}
                    readOnly
                    className="h-32 font-mono text-xs mt-2"
                    placeholder="Les logs d'exploration apparaîtront ici..."
                  />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Discovered Sources */}
          {discoveredSources.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  Sources Découvertes ({discoveredSources.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Source</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Offres</TableHead>
                        <TableHead>Statut</TableHead>
                        <TableHead>Découverte</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {discoveredSources.map((source) => (
                        <TableRow key={source.id}>
                          <TableCell>
                            <div className="max-w-xs">
                              <div className="font-medium truncate" title={source.title}>
                                {source.title}
                              </div>
                              <a 
                                href={source.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-xs text-blue-600 hover:text-blue-800 truncate block"
                                title={source.url}
                              >
                                {source.url.length > 40 ? `${source.url.substring(0, 40)}...` : source.url}
                              </a>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{source.source_type}</Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div className="w-16 bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-blue-600 h-2 rounded-full" 
                                  style={{ width: `${source.confidence_score * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-xs">{(source.confidence_score * 100).toFixed(0)}%</span>
                            </div>
                          </TableCell>
                          <TableCell>{source.offers_count}</TableCell>
                          <TableCell>
                            <Badge 
                              variant={source.status === 'scraped' ? 'default' : 
                                     source.status === 'failed' ? 'destructive' : 'secondary'}
                            >
                              {source.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs text-gray-500">
                            {new Date(source.discovered_at).toLocaleDateString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Discovered Offers */}
          {discoveredOffers.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <CardTitle className="flex items-center gap-2">
                    <Download className="h-5 w-5" />
                    Offres Découvertes ({discoveredOffers.length})
                  </CardTitle>
                  <div className="text-sm text-gray-500">
                    Triées par score de confiance
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Titre</TableHead>
                        <TableHead>Source</TableHead>
                        <TableHead>Payout</TableHead>
                        <TableHead>Catégorie</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {discoveredOffers.map((offer) => (
                        <TableRow key={offer.id}>
                          <TableCell className="font-medium max-w-xs">
                            <div className="truncate" title={offer.title}>
                              {offer.title}
                            </div>
                            {offer.description && (
                              <div className="text-xs text-gray-500 truncate mt-1" title={offer.description}>
                                {offer.description.substring(0, 60)}...
                              </div>
                            )}
                          </TableCell>
                          <TableCell className="max-w-xs">
                            <a 
                              href={offer.source_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 truncate block text-xs"
                              title={offer.source_url}
                            >
                              {new URL(offer.source_url).hostname}
                            </a>
                          </TableCell>
                          <TableCell>
                            {offer.payout ? (
                              <span className="font-medium">${offer.payout}</span>
                            ) : '-'}
                          </TableCell>
                          <TableCell>
                            {offer.category ? (
                              <Badge variant="secondary">{offer.category}</Badge>
                            ) : offer.vertical ? (
                              <Badge variant="outline">{offer.vertical}</Badge>
                            ) : '-'}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div className="w-12 bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-green-600 h-2 rounded-full" 
                                  style={{ width: `${offer.confidence_score * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-xs">{(offer.confidence_score * 100).toFixed(0)}%</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => importDiscoveredOffer(offer.id)}
                              className="flex items-center gap-1"
                            >
                              <CheckCircle className="h-3 w-3" />
                              Importer
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* No discoveries yet */}
          {!isDiscoveryRunning && discoveredSources.length === 0 && discoveredOffers.length === 0 && (
            <Card>
              <CardContent className="text-center py-8">
                <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  Aucune exploration lancée
                </p>
                <p className="text-sm text-gray-400 mt-2">
                  Cliquez sur "Lancer l'exploration" pour découvrir automatiquement de nouvelles sources d'affiliation
                </p>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
