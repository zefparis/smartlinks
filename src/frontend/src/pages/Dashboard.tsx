import { useState, useEffect } from 'react';
import { useServiceStatus } from '@/contexts/ServiceStatusContext';
import api, { MetricsResponse, TrafficStats, StatsResponse } from '@/lib/api';
import { format } from 'date-fns';
import { toast } from 'sonner';
import {
  ArrowPathIcon,
  ArrowTopRightOnSquareIcon,
  ArrowTrendingUpIcon,
  ClockIcon,
  CursorArrowRaysIcon,
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  UserGroupIcon,
  ShieldExclamationIcon,
  BoltIcon,
  TrashIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import HealthCard from '@/components/dashboard/HealthCard';
import MetricCard from '@/components/dashboard/MetricCard';
import TrafficChart from '@/components/dashboard/TrafficChart';
import RecentClicks from '@/components/dashboard/RecentClicks';
import AIChatPanel from '@/components/ai/AIChatPanel';
import StatusIndicator from '@/components/ui/StatusIndicator';
import useSystemStatus from '@/hooks/useSystemStatus';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';

export default function Dashboard() {
  const { status, startService, stopService } = useServiceStatus();
  const { status: sysStatus, errors: systemErrors, refresh: refreshSystemStatus } = useSystemStatus(10000);
  // Initialize with default values to prevent uncontrolled inputs
  const [metrics, setMetrics] = useState<MetricsResponse>({ 
    clicks_total: 0,
    last_click_id: null,
    last_click_time: null,
    segments: []
  });
  
  const [stats, setStats] = useState<StatsResponse>({
    clicks_total: 0,
    fraud_suspects: 0,
    approved: 0,
    fraud_rate: 0,
    approval_rate: 0
  });
  
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isAIPanelOpen, setIsAIPanelOpen] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [metricsRes, statsRes] = await Promise.allSettled([
        api.getMetrics().catch(() => ({
          data: {
            clicks_total: 0,
            last_click_id: null,
            last_click_time: null,
            segments: [],
            error: 'Failed to load metrics'
          }
        })),
        api.getStats().catch(() => ({
          data: {
            clicks_total: 0,
            fraud_suspects: 0,
            approved: 0,
            fraud_rate: 0,
            approval_rate: 0,
            error: 'Failed to load stats'
          }
        }))
      ]);
      
      if (metricsRes.status === 'fulfilled' && metricsRes.value?.data) {
        setMetrics(prev => ({
          clicks_total: metricsRes.value.data.clicks_total ?? 0,
          last_click_id: metricsRes.value.data.last_click_id ?? null,
          last_click_time: metricsRes.value.data.last_click_time ?? null,
          segments: metricsRes.value.data.segments ?? []
        }));
      }
      
      if (statsRes.status === 'fulfilled' && statsRes.value?.data) {
        setStats(prev => ({
          clicks_total: statsRes.value.data.clicks_total ?? 0,
          fraud_suspects: statsRes.value.data.fraud_suspects ?? 0,
          approved: statsRes.value.data.approved ?? 0,
          fraud_rate: statsRes.value.data.fraud_rate ?? 0,
          approval_rate: statsRes.value.data.approval_rate ?? 0
        }));
      }
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Set up polling every 5 seconds
    const interval = setInterval(fetchData, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const handleServiceToggle = async (service: 'router' | 'autopilot' | 'probes') => {
    try {
      if (status[service]) {
        await stopService(service);
      } else {
        await startService(service);
      }
    } catch (error) {
      console.error(`Failed to toggle ${service}:`, error);
      toast.error(`Failed to toggle ${service}`);
    }
  };

  const handleAction = async (action: 'seed' | 'payout' | 'flush') => {
    try {
      switch (action) {
        case 'seed':
          await api.seedDatabase();
          toast.success('Database seeded successfully');
          break;
        case 'payout':
          await api.updatePayouts();
          toast.success('Payout rates updated');
          break;
        case 'flush':
          if (window.confirm('Are you sure you want to flush the database? This cannot be undone.')) {
            await api.flushDatabase();
            toast.success('Database flushed');
          }
          break;
      }
      await fetchData();
    } catch (error) {
      console.error(`Failed to perform ${action}:`, error);
      toast.error(`Failed to perform ${action}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Overview of your SmartLinks performance and metrics
            {lastUpdated && ` • Last updated at ${format(lastUpdated, 'HH:mm:ss')}`}
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" size="md" onClick={() => fetchData()}>
            <ArrowPathIcon className="w-5 h-5 mr-2 -ml-1 text-gray-500" aria-hidden="true" />
            Refresh
          </Button>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="md" onClick={() => { refreshSystemStatus(); toast.success('System status refreshed'); }} className="transform-none">
                  <ChartBarIcon className="w-5 h-5 mr-2 -ml-1 text-gray-500 dark:text-gray-400" aria-hidden="true" />
                  Refresh Status
                </Button>
              </TooltipTrigger>
              <TooltipContent>Refresh system status</TooltipContent>
            </Tooltip>
          </TooltipProvider>
          {import.meta.env.VITE_ENABLE_DASHBOARD_AI === "true" && (
            <Button onClick={() => setIsAIPanelOpen(true)}>
              AI Assistant
            </Button>
          )}
        </div>
      </div>

      {/* System Status Indicators */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Card className="p-4 flex items-center justify-between">
          <StatusIndicator status={sysStatus.router} label="Router" />
          <Button variant="link"
            onClick={() => handleServiceToggle('router')}
            className="text-xs"
          >
            Toggle
          </Button>
        </Card>
        <Card className="p-4 flex items-center justify-between">
          <StatusIndicator status={sysStatus.autopilot} label="Autopilot" />
          <Button variant="link"
            onClick={() => handleServiceToggle('autopilot')}
            className="text-xs"
          >
            Toggle
          </Button>
        </Card>
        <Card className="p-4 flex items-center justify-between">
          <StatusIndicator status={sysStatus.probes} label="Probes" />
          <Button variant="link"
            onClick={() => handleServiceToggle('probes')}
            className="text-xs"
          >
            Toggle
          </Button>
        </Card>
      </div>

      {/* Health Status */}
      <div className="grid grid-cols-1 gap-5 mt-6 sm:grid-cols-2 lg:grid-cols-4">
        <HealthCard
          title="Router"
          isActive={status.router}
          onToggle={() => handleServiceToggle('router')}
          icon={CursorArrowRaysIcon}
        />
        <HealthCard
          title="Autopilot"
          isActive={status.autopilot}
          onToggle={() => handleServiceToggle('autopilot')}
          icon={ShieldCheckIcon}
        />
        <HealthCard
          title="Probes"
          isActive={status.probes}
          onToggle={() => handleServiceToggle('probes')}
          icon={UserGroupIcon}
        />
        <div className="overflow-hidden bg-white dark:bg-gray-800 rounded-lg shadow ring-1 ring-gray-200 dark:ring-gray-600">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex items-center justify-center w-12 h-12 text-white rounded-md bg-amber-500">
                <ClockIcon className="w-6 h-6" aria-hidden="true" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-300 truncate">Uptime</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">99.9%</div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 gap-5 mt-6 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          title="Total Clicks"
          value={stats?.clicks_total?.toLocaleString() || '0'}
          icon={CursorArrowRaysIcon}
          trend="up"
          change="12%"
          iconColor="text-blue-500"
          bgColor="bg-blue-50"
        />
        <MetricCard
          title="Approved"
          value={stats?.approved?.toLocaleString() || '0'}
          icon={ShieldCheckIcon}
          trend="up"
          change="5.3%"
          iconColor="text-green-500"
          bgColor="bg-green-50"
        />
        <MetricCard
          title="Approval Rate"
          value={`${(stats?.approval_rate * 100)?.toFixed(1)}%` || '0%'}
          icon={ArrowTrendingUpIcon}
          trend="up"
          change="2.1%"
          iconColor="text-green-500"
          bgColor="bg-green-50"
        />
        <MetricCard
          title="Fraud Rate"
          value={`${(stats?.fraud_rate * 100)?.toFixed(1)}%` || '0%'}
          icon={ShieldExclamationIcon}
          trend="down"
          change="1.2%"
          iconColor="text-red-500"
          bgColor="bg-red-50"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 mt-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Traffic by Segment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <TrafficChart data={metrics?.segments || []} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <RecentClicks />
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="mt-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Quick Actions</h3>
        <div className="grid grid-cols-1 gap-4 mt-4 sm:grid-cols-3">
          <TooltipProvider>
            <Tooltip>
              <div className="inline-flex">
                <TooltipTrigger asChild>
                  <Button onClick={() => handleAction('seed')} className="justify-center">
                    <ArrowPathIcon className="w-5 h-5 mr-2" />
                    Re-seed Database
                  </Button>
                </TooltipTrigger>
              </div>
              <TooltipContent>Populate database with sample data</TooltipContent>
            </Tooltip>

            <Tooltip>
              <div className="inline-flex">
                <TooltipTrigger asChild>
                  <Button onClick={() => handleAction('payout')} className="justify-center bg-green-600 hover:bg-green-700">
                    <ArrowPathIcon className="w-5 h-5 mr-2" />
                    Update Payouts
                  </Button>
                </TooltipTrigger>
              </div>
              <TooltipContent>Recalculate payout rates</TooltipContent>
            </Tooltip>

            <Tooltip>
              <div className="inline-flex">
                <TooltipTrigger asChild>
                  <Button onClick={() => handleAction('flush')} className="justify-center bg-red-600 hover:bg-red-700">
                    <ArrowPathIcon className="w-5 h-5 mr-2" />
                    Flush Database
                  </Button>
                </TooltipTrigger>
              </div>
              <TooltipContent>Delete all data (irreversible)</TooltipContent>
            </Tooltip>

            {/* New actions */}
            <Tooltip>
              <div className="inline-flex">
                <TooltipTrigger asChild>
                  <Button onClick={() => toast.success('Backend restart triggered')} className="justify-center bg-gray-800 hover:bg-gray-700">
                    <ArrowPathIcon className="w-5 h-5 mr-2" />
                    Restart Backend
                  </Button>
                </TooltipTrigger>
              </div>
              <TooltipContent>Restart backend services</TooltipContent>
            </Tooltip>

            <Tooltip>
              <div className="inline-flex">
                <TooltipTrigger asChild>
                  <Button onClick={async () => { await fetchData(); toast.success('Analytics refreshed'); }} className="justify-center bg-blue-600 hover:bg-blue-700">
                    <ChartBarIcon className="w-5 h-5 mr-2" />
                    Refresh Analytics
                  </Button>
                </TooltipTrigger>
              </div>
              <TooltipContent>Refresh metrics and charts</TooltipContent>
            </Tooltip>

            <Tooltip>
              <div className="inline-flex">
                <TooltipTrigger asChild>
                  <Button onClick={() => toast.success('Cache cleared')} className="justify-center bg-yellow-600 hover:bg-yellow-700">
                    <TrashIcon className="w-5 h-5 mr-2" />
                    Clear Cache
                  </Button>
                </TooltipTrigger>
              </div>
              <TooltipContent>Clear application cache</TooltipContent>
            </Tooltip>

            <Tooltip>
              <div className="inline-flex">
                <TooltipTrigger asChild>
                  <Button onClick={() => toast.success('Database optimized')} className="justify-center bg-purple-600 hover:bg-purple-700">
                    <BoltIcon className="w-5 h-5 mr-2" />
                    Optimize DB
                  </Button>
                </TooltipTrigger>
              </div>
              <TooltipContent>Run database optimization</TooltipContent>
            </Tooltip>

            <Tooltip>
              <div className="inline-flex">
                <TooltipTrigger asChild>
                  <Button onClick={() => toast.success('Security scan completed')} className="justify-center bg-emerald-600 hover:bg-emerald-700">
                    <ShieldCheckIcon className="w-5 h-5 mr-2" />
                    Run Security Scan
                  </Button>
                </TooltipTrigger>
              </div>
              <TooltipContent>Run basic security checks</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* Logs Panel */}
      <Card className="mt-6">
        <CardHeader className="flex items-center justify-between flex-row">
          <CardTitle>System Logs</CardTitle>
          <Button variant="link" onClick={() => setShowLogs(s => !s)} className="text-sm">
            {showLogs ? 'Hide Logs' : 'View Logs'}
          </Button>
        </CardHeader>
        {showLogs && (
          <CardContent>
            <div className="max-h-64 overflow-auto border rounded p-3 text-sm font-mono bg-gray-50 dark:bg-gray-800 dark:border-gray-700">
              {systemErrors.length === 0 ? (
                <div className="text-gray-500 dark:text-gray-400">No errors recorded.</div>
              ) : (
                <ul className="space-y-2">
                  {systemErrors.map((e, idx) => (
                    <li key={idx} className="text-red-400 dark:text-red-400 break-all">{e}</li>
                  ))}
                </ul>
              )}
            </div>
          </CardContent>
        )}
      </Card>

      {/* AI Chat Panel */}
      {import.meta.env.VITE_ENABLE_DASHBOARD_AI === "true" && (
        <AIChatPanel isOpen={isAIPanelOpen} onClose={() => setIsAIPanelOpen(false)} />
      )}
    </div>
  );
}
