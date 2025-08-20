import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
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
  const [config, setConfig] = useState<any>({});
  const [formData, setFormData] = useState<any>({});
  const [isFlushModalVisible, setIsFlushModalVisible] = useState(false);
  const [isResyncModalVisible, setIsResyncModalVisible] = useState(false);
  const [confirmText, setConfirmText] = useState<string>('');
  const [serviceStatus, setServiceStatus] = useState<any>({});
  const [logs, setLogs] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchConfig();
    fetchServiceStatus();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(prev => ({ ...prev, save: true }));
      
      // Try new settings endpoint first, fallback to config
      try {
        const response = await api.getSettings();
        const data = response;
        
        setConfig(data || {});
        setFormData(data || {});
      } catch (error) {
        console.debug('Settings endpoint not available, trying config endpoint');
        try {
          const configResponse = await api.getConfig();
          const configData = configResponse;
          
          setConfig(configData || {});
          setFormData(configData || {});
        } catch (configError) {
          console.error('Failed to load settings:', configError);
          toast.error('Failed to load settings');
        } 
        return;
      }
      
      // Response is already the data we need
      const safeConfigData = config && typeof config === 'object' ? config : {};
      
      // Ensure we always have a valid config structure
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
      const response = await api.getServiceStatus();
      setServiceStatus(response);
    } catch (error) {
      console.error('Error fetching service status:', error);
      // Set fallback status
      setServiceStatus({
        analytics: false,
        database: false,
        ai_supervisor: false
      });
    }
  };

  const fetchLogs = async (service: string) => {
    try {
      const response = await api.getServiceLogs(service);
      setLogs(prev => ({ ...prev, [service]: response }));
    } catch (error) {
      console.error(`Failed to fetch logs for ${service}:`, error);
      setLogs(prev => ({
        ...prev,
        [service]: 'Failed to load logs'
      }));
    }
  };

  const handleFlushDatabase = async () => {
    try {
      setLoading(prev => ({ ...prev, flush: true }));
      await api.flushDatabase();
      toast.success('Database flushed successfully');
      setIsFlushModalVisible(false);
    } catch (error) {
      toast.error('Failed to flush database');
      console.error('Flush error:', error);
    } finally {
      setLoading(prev => ({ ...prev, flush: false }));
    }
  };

  const handleResyncData = async () => {
    try {
      setLoading(prev => ({ ...prev, resync: true }));
      await api.seedDatabase();
      toast.success('Data resync initiated');
      setIsResyncModalVisible(false);
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
      toast.success('Settings saved successfully');
      fetchConfig();
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
      await fetchServiceStatus();
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

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSaveConfig(formData);
  };

  return (
    <div className="container mx-auto py-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage your application configuration and services</p>
      </div>
      
      <Tabs defaultValue="general" className="space-y-6">
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
                      <p className="text-sm text-gray-500 dark:text-gray-400">Automatically approve valid transactions</p>
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
                      <p className="text-sm text-gray-500 dark:text-gray-400">Receive email alerts for important events</p>
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
                      <p className="text-sm text-gray-500 dark:text-gray-400">Send notifications to Slack workspace</p>
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
        
        <TabsContent value="services">
          <Card>
            <CardHeader>
              <CardTitle>Service Management</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(serviceStatus || {}).map(([service, isRunning]) => (
                  <Card key={service} className="mb-4">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <span className="capitalize font-medium">{service?.replace(/_/g, ' ') || 'Unknown'} Service</span>
                          <span className={`ml-2 inline-block w-3 h-3 rounded-full ${isRunning ? 'bg-green-500' : 'bg-red-500'}`}></span>
                        </div>
                        <div className="space-x-2">
                          <Button 
                            variant={isRunning ? 'destructive' : 'default'}
                            onClick={() => toggleService(service, !isRunning)}
                            disabled={loading.save}
                          >
                            {isRunning ? (
                              <><StopIcon className="mr-2 h-4 w-4" /> Stop</>
                            ) : (
                              <><PlayIcon className="mr-2 h-4 w-4" /> Start</>
                            )}
                          </Button>
                          <Button 
                            variant="outline"
                            onClick={() => fetchLogs(service)}
                          >
                            <ArrowPathIcon className="mr-2 h-4 w-4" />
                            View Logs
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="m-0">Status: <span className={isRunning ? 'text-green-500' : 'text-red-500'}>
                            {isRunning ? 'Running' : 'Stopped'}
                          </span></p>
                          <p className="m-0 text-gray-500 text-sm">Last updated: {new Date().toLocaleString()}</p>
                        </div>
                      </div>
                      
                      {logs[service] && (
                        <div className="mt-4 p-2 bg-black text-green-400 font-mono text-sm rounded overflow-auto h-40">
                          <pre className="m-0">{logs[service]}</pre>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="danger">
          <Card className="border-red-200">
            <CardHeader>
              <CardTitle className="text-red-600">Danger Zone</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <Alert variant="destructive">
                  <ExclamationTriangleIcon className="h-4 w-4" />
                  <AlertTitle>Warning</AlertTitle>
                  <AlertDescription>
                    These actions are irreversible. Proceed with caution.
                  </AlertDescription>
                </Alert>
                
                <Card className="border-red-100">
                  <CardHeader>
                    <CardTitle>Flush Database</CardTitle>
                    <CardDescription>
                      This will permanently delete all data in the database. This action cannot be undone.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Dialog>
                      <DialogTrigger>
                        <Button variant="destructive" disabled={loading.flush}>
                          {loading.flush ? (
                            <ArrowPathIcon className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <TrashIcon className="mr-2 h-4 w-4" />
                          )}
                          Flush Database
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Confirm Database Flush</DialogTitle>
                          <DialogDescription>
                            You are about to permanently delete all data in the database.
                          </DialogDescription>
                        </DialogHeader>
                        <Alert variant="destructive">
                          <ExclamationTriangleIcon className="h-4 w-4" />
                          <AlertTitle>Warning: This action cannot be undone!</AlertTitle>
                          <AlertDescription>
                            Type <strong>DELETE</strong> to confirm:
                          </AlertDescription>
                        </Alert>
                        <Input 
                          placeholder="Type DELETE to confirm" 
                          value={confirmText}
                          onChange={(e) => setConfirmText(e.target.value)}
                          className="mt-2" 
                        />
                        <DialogFooter>
                          <Button 
                            variant="destructive" 
                            onClick={handleFlushDatabase}
                            disabled={confirmText !== 'DELETE'}
                          >
                            Yes, Flush Database
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </CardContent>
                </Card>
                
                <Card className="border-yellow-100">
                  <CardHeader>
                    <CardTitle>Resync Data</CardTitle>
                    <CardDescription>
                      Force resynchronization of all data from external sources. This may take some time.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Dialog>
                      <DialogTrigger>
                        <Button variant="outline" disabled={loading.resync}>
                          {loading.resync ? (
                            <ArrowPathIcon className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <ArrowDownTrayIcon className="mr-2 h-4 w-4" />
                          )}
                          Resync Data
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Confirm Data Resync</DialogTitle>
                          <DialogDescription>
                            This will start a full resynchronization of all data from external sources.
                            This process may take several minutes to complete.
                          </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                          <Button onClick={handleResyncData}>
                            Start Resync
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </CardContent>
                </Card>
                
                <Card className="border-blue-100">
                  <CardHeader>
                    <CardTitle>Update Payouts</CardTitle>
                    <CardDescription>
                      Update all payout rates from the latest configuration. This will affect future conversions.
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
                        <ArrowDownTrayIcon className="mr-2 h-4 w-4" />
                      )}
                      Update Payouts
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
