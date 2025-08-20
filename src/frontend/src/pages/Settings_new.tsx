import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { 
  ArrowPathIcon, 
  TrashIcon, 
  ArrowDownTrayIcon, 
  CheckCircleIcon,
  StopIcon,
  ExclamationTriangleIcon,
  PlayIcon
} from '@heroicons/react/24/outline';
import api from '@/lib/api';
import { cn } from '@/lib/utils';
import { classes } from '@/lib/design-system';

export default function Settings() {
  const [loading, setLoading] = useState({
    flush: false,
    resync: false,
    updatePayouts: false,
    save: false,
  });
  const [config, setConfig] = useState<any>(null);
  const [formData, setFormData] = useState<any>({});
  const [isFlushModalVisible, setIsFlushModalVisible] = useState(false);
  const [isResyncModalVisible, setIsResyncModalVisible] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [serviceStatus, setServiceStatus] = useState<Record<string, boolean>>({});
  const [logs, setLogs] = useState<Record<string, string>>({});
  const [expandedService, setExpandedService] = useState<string | null>(null);

  useEffect(() => {
    fetchConfig();
    fetchServiceStatus();
  }, []);

  const fetchConfig = async () => {
    try {
      // First try the main settings endpoint
      const data = await api.getSettings();
      
      // If data exists, use it
      if (data) {
        console.log('Settings loaded:', data);
        const safeConfig = {
          app_name: data?.app_name ?? 'SmartLinks Autopilot',
          version: data?.version ?? '1.0.0',
          timezone: data?.timezone ?? 'UTC',
          currency: data?.currency ?? 'EUR',
          default_cap_day: data?.default_cap_day ?? 1000,
          fraud_threshold: data?.fraud_threshold ?? 0.8,
          auto_approval: data?.auto_approval ?? true,
          email_notifications: data?.email_notifications ?? true,
          slack_notifications: data?.slack_notifications ?? false,
          max_daily_budget: data?.max_daily_budget ?? 5000.0,
          min_payout_threshold: data?.min_payout_threshold ?? 10.0,
          ...data
        };
        
        setConfig(safeConfig);
        setFormData(safeConfig);
        return;
      }
    } catch (error) {
      console.warn('Settings endpoint not available, trying config endpoint');
    }

    // Fallback to config endpoint
    try {
      const safeConfigData = await api.getConfig();
      
      const safeConfig = {
        app_name: safeConfigData?.app_name ?? 'SmartLinks Autopilot',
        version: safeConfigData?.version ?? '1.0.0',
        timezone: safeConfigData?.timezone ?? 'UTC',
        currency: safeConfigData?.currency ?? 'EUR',
        default_cap_day: safeConfigData?.default_cap_day ?? 1000,
        fraud_threshold: safeConfigData?.fraud_threshold ?? 0.8,
        auto_approval: safeConfigData?.auto_approval ?? true,
        email_notifications: safeConfigData?.email_notifications ?? true,
        slack_notifications: safeConfigData?.slack_notifications ?? false,
        max_daily_budget: safeConfigData?.max_daily_budget ?? 5000.0,
        min_payout_threshold: safeConfigData?.min_payout_threshold ?? 10.0,
        ...safeConfigData
      };
      
      setConfig(safeConfig);
      setFormData(safeConfig);
    } catch (error) {
      console.error('Error fetching config:', error);
      toast.error('Failed to load configuration');
      
      // Set fallback config on error
      const fallbackConfig = {
        app_name: 'SmartLinks Autopilot',
        version: '1.0.0',
        timezone: 'UTC',
        currency: 'EUR',
        default_cap_day: 1000,
        fraud_threshold: 0.8,
        auto_approval: true,
        email_notifications: true,
        slack_notifications: false,
        max_daily_budget: 5000.0,
        min_payout_threshold: 10.0
      };
      
      setConfig(fallbackConfig);
      setFormData(fallbackConfig);
    } finally {
      setLoading(prev => ({ ...prev, save: false }));
    }
  };

  const fetchServiceStatus = async () => {
    try {
      const status = await api.getServiceStatus();
      setServiceStatus(status ?? {});
    } catch (error) {
      console.error('Failed to fetch service status:', error);
      setServiceStatus({});
    }
  };

  const fetchLogs = async (service: string) => {
    try {
      const logsData = await api.getServiceLogs(service);
      const logsText = logsData?.data ?? 'No logs available';
      setLogs(prev => ({
        ...prev,
        [service]: logsText
      }));
    } catch (error) {
      console.error(`Failed to fetch logs for ${service}:`, error);
      setLogs(prev => ({
        ...prev,
        [service]: 'Failed to load logs'
      }));
    }
  };

  const handleFlushDatabase = async () => {
    if (confirmText !== 'FLUSH') {
      toast.error('Please type FLUSH to confirm');
      return;
    }
    
    try {
      setLoading(prev => ({ ...prev, flush: true }));
      await api.flushDatabase();
      toast.success('Database flushed successfully');
      setIsFlushModalVisible(false);
      setConfirmText('');
    } catch (error) {
      toast.error('Failed to flush database');
      console.error('Flush error:', error);
    } finally {
      setLoading(prev => ({ ...prev, flush: false }));
    }
  };

  const handleResyncData = async () => {
    if (confirmText !== 'RESYNC') {
      toast.error('Please type RESYNC to confirm');
      return;
    }
    
    try {
      setLoading(prev => ({ ...prev, resync: true }));
      await api.seedDatabase();
      toast.success('Data resynchronization started');
      setIsResyncModalVisible(false);
      setConfirmText('');
    } catch (error) {
      toast.error('Failed to start data resynchronization');
      console.error('Resync error:', error);
    } finally {
      setLoading(prev => ({ ...prev, resync: false }));
    }
  };

  const handleUpdatePayouts = async () => {
    try {
      setLoading(prev => ({ ...prev, updatePayouts: true }));
      await api.updatePayouts();
      toast.success('Payouts updated successfully');
    } catch (error) {
      toast.error('Failed to update payouts');
      console.error('Payouts error:', error);
    } finally {
      setLoading(prev => ({ ...prev, updatePayouts: false }));
    }
  };

  const handleSaveConfig = async (values: any) => {
    setLoading(prev => ({ ...prev, save: true }));
    try {
      // Validate values before saving
      const safeValues = {
        ...values,
        default_cap_day: Number(values?.default_cap_day ?? 1000),
        fraud_threshold: Number(values?.fraud_threshold ?? 0.8),
        max_daily_budget: Number(values?.max_daily_budget ?? 5000.0),
        min_payout_threshold: Number(values?.min_payout_threshold ?? 10.0)
      };
      
      await api.updateConfig(safeValues);
      toast.success('Configuration saved successfully');
      setConfig(safeValues);
    } catch (error) {
      console.error('Error saving config:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to save configuration';
      toast.error(errorMessage);
    } finally {
      setLoading(prev => ({ ...prev, save: false }));
    }
  };

  const toggleService = async (service: string, start: boolean) => {
    try {
      if (start) {
        await api.startService(service);
      } else {
        await api.stopService(service);
      }
      toast.success(`Service ${service} ${start ? 'started' : 'stopped'} successfully`);
      fetchServiceStatus();
      if (logs[service]) {
        fetchLogs(service);
      }
    } catch (error) {
      toast.error(`Failed to ${start ? 'start' : 'stop'} service ${service}`);
      console.error('Service toggle error:', error);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSaveConfig(formData);
  };

  const toggleServiceLogs = (service: string) => {
    if (expandedService === service) {
      setExpandedService(null);
    } else {
      setExpandedService(service);
      if (!logs[service]) {
        fetchLogs(service);
      }
    }
  };

  if (!config) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <Skeleton className="h-12 w-12 rounded-full mx-auto" />
          <Skeleton className="h-4 w-32 mx-auto" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Manage your application configuration and services
        </p>
      </div>
      
      <Tabs defaultValue="general" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="danger">Danger Zone</TabsTrigger>
        </TabsList>
        
        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Application Settings</CardTitle>
              <CardDescription>Configure your SmartLinks application settings</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleFormSubmit} className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="app_name">Application Name</Label>
                    <Input
                      id="app_name"
                      value={formData.app_name || ''}
                      onChange={(e) => handleInputChange('app_name', e.target.value)}
                      className={cn(classes.input.base)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="version">Version</Label>
                    <Input
                      id="version"
                      value={formData.version || ''}
                      disabled
                      className={cn(classes.input.base, "bg-gray-50 dark:bg-gray-900")}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="timezone">Timezone</Label>
                    <Input
                      id="timezone"
                      value={formData.timezone || ''}
                      onChange={(e) => handleInputChange('timezone', e.target.value)}
                      className={cn(classes.input.base)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="currency">Currency</Label>
                    <Input
                      id="currency"
                      value={formData.currency || ''}
                      onChange={(e) => handleInputChange('currency', e.target.value)}
                      className={cn(classes.input.base)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="default_cap_day">Default Daily Cap</Label>
                    <Input
                      id="default_cap_day"
                      type="number"
                      value={formData.default_cap_day || ''}
                      onChange={(e) => handleInputChange('default_cap_day', e.target.value)}
                      className={cn(classes.input.base)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="fraud_threshold">Fraud Threshold</Label>
                    <Input
                      id="fraud_threshold"
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      value={formData.fraud_threshold || ''}
                      onChange={(e) => handleInputChange('fraud_threshold', e.target.value)}
                      className={cn(classes.input.base)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="max_daily_budget">Max Daily Budget</Label>
                    <Input
                      id="max_daily_budget"
                      type="number"
                      step="0.01"
                      value={formData.max_daily_budget || ''}
                      onChange={(e) => handleInputChange('max_daily_budget', e.target.value)}
                      className={cn(classes.input.base)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="min_payout_threshold">Min Payout Threshold</Label>
                    <Input
                      id="min_payout_threshold"
                      type="number"
                      step="0.01"
                      value={formData.min_payout_threshold || ''}
                      onChange={(e) => handleInputChange('min_payout_threshold', e.target.value)}
                      className={cn(classes.input.base)}
                    />
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="auto_approval">Auto Approval</Label>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Automatically approve valid transactions
                      </p>
                    </div>
                    <Switch
                      id="auto_approval"
                      checked={formData.auto_approval || false}
                      onCheckedChange={(checked) => handleInputChange('auto_approval', checked)}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="email_notifications">Email Notifications</Label>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Receive email alerts for important events
                      </p>
                    </div>
                    <Switch
                      id="email_notifications"
                      checked={formData.email_notifications || false}
                      onCheckedChange={(checked) => handleInputChange('email_notifications', checked)}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="slack_notifications">Slack Notifications</Label>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Send notifications to Slack workspace
                      </p>
                    </div>
                    <Switch
                      id="slack_notifications"
                      checked={formData.slack_notifications || false}
                      onCheckedChange={(checked) => handleInputChange('slack_notifications', checked)}
                    />
                  </div>
                </div>
                
                <div className="flex justify-end">
                  <Button 
                    type="submit"
                    disabled={loading.save}
                    className={cn(classes.button.base, classes.button.variants.primary, classes.button.sizes.md)}
                  >
                    {loading.save ? (
                      <ArrowPathIcon className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <CheckCircleIcon className="mr-2 h-4 w-4" />
                    )}
                    Save Settings
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="services" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Service Management</CardTitle>
              <CardDescription>Monitor and control application services</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(serviceStatus || {}).map(([service, isRunning]) => (
                <Card key={service} className={cn(classes.card.base)}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={cn(
                          "h-3 w-3 rounded-full",
                          isRunning ? "bg-green-500" : "bg-red-500"
                        )} />
                        <CardTitle className="text-lg">{service}</CardTitle>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => toggleServiceLogs(service)}
                        >
                          <ArrowDownTrayIcon className="h-4 w-4" />
                        </Button>
                        {isRunning ? (
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => toggleService(service, false)}
                          >
                            <StopIcon className="mr-2 h-4 w-4" />
                            Stop
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="default"
                            onClick={() => toggleService(service, true)}
                          >
                            <PlayIcon className="mr-2 h-4 w-4" />
                            Start
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  {expandedService === service && (
                    <CardContent>
                      <div className="bg-gray-900 dark:bg-gray-950 rounded-md p-4">
                        <pre className="text-xs text-gray-300 overflow-x-auto">
                          {logs[service] || 'Loading logs...'}
                        </pre>
                      </div>
                    </CardContent>
                  )}
                </Card>
              ))}
              
              {Object.keys(serviceStatus).length === 0 && (
                <Alert>
                  <ExclamationTriangleIcon className="h-4 w-4" />
                  <AlertTitle>No Services</AlertTitle>
                  <AlertDescription>
                    No services are currently configured or available.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="danger" className="space-y-4">
          <Alert>
            <ExclamationTriangleIcon className="h-4 w-4" />
            <AlertTitle>Warning</AlertTitle>
            <AlertDescription>
              These actions are destructive and cannot be undone. Please proceed with caution.
            </AlertDescription>
          </Alert>
          
          <Card>
            <CardHeader>
              <CardTitle>Flush Database</CardTitle>
              <CardDescription>
                Remove all data from the database. This action cannot be undone.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                variant="destructive"
                onClick={() => setIsFlushModalVisible(true)}
                disabled={loading.flush}
              >
                <TrashIcon className="mr-2 h-4 w-4" />
                Flush Database
              </Button>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Resync Data</CardTitle>
              <CardDescription>
                Resynchronize all data from external sources. This may take several minutes.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                variant="outline"
                onClick={() => setIsResyncModalVisible(true)}
                disabled={loading.resync}
              >
                <ArrowPathIcon className="mr-2 h-4 w-4" />
                Resync Data
              </Button>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Update Payouts</CardTitle>
              <CardDescription>
                Recalculate and update all payout information.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                variant="outline"
                onClick={handleUpdatePayouts}
                disabled={loading.updatePayouts}
              >
                {loading.updatePayouts ? (
                  <ArrowPathIcon className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <ArrowPathIcon className="mr-2 h-4 w-4" />
                )}
                Update Payouts
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      
      {/* Flush Database Modal */}
      <Dialog open={isFlushModalVisible} onOpenChange={setIsFlushModalVisible}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Database Flush</DialogTitle>
            <DialogDescription>
              This will permanently delete all data in the database. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <Alert>
              <ExclamationTriangleIcon className="h-4 w-4" />
              <AlertTitle>Danger</AlertTitle>
              <AlertDescription>
                Type <strong>FLUSH</strong> below to confirm this action.
              </AlertDescription>
            </Alert>
            <div className="space-y-2">
              <Label htmlFor="confirm-flush">Confirmation</Label>
              <Input
                id="confirm-flush"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder="Type FLUSH to confirm"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsFlushModalVisible(false);
                setConfirmText('');
              }}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleFlushDatabase}
              disabled={loading.flush || confirmText !== 'FLUSH'}
            >
              {loading.flush ? (
                <ArrowPathIcon className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <TrashIcon className="mr-2 h-4 w-4" />
              )}
              Flush Database
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Resync Data Modal */}
      <Dialog open={isResyncModalVisible} onOpenChange={setIsResyncModalVisible}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Data Resynchronization</DialogTitle>
            <DialogDescription>
              This will resynchronize all data from external sources. This process may take several minutes.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <Alert>
              <ExclamationTriangleIcon className="h-4 w-4" />
              <AlertTitle>Caution</AlertTitle>
              <AlertDescription>
                Type <strong>RESYNC</strong> below to confirm this action.
              </AlertDescription>
            </Alert>
            <div className="space-y-2">
              <Label htmlFor="confirm-resync">Confirmation</Label>
              <Input
                id="confirm-resync"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder="Type RESYNC to confirm"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsResyncModalVisible(false);
                setConfirmText('');
              }}
            >
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={handleResyncData}
              disabled={loading.resync || confirmText !== 'RESYNC'}
            >
              {loading.resync ? (
                <ArrowPathIcon className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <ArrowPathIcon className="mr-2 h-4 w-4" />
              )}
              Start Resync
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
