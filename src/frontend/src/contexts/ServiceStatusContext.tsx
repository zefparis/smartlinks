import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { toast } from 'sonner';
import adminApi from '@/lib/api';

type ServiceName = 'router' | 'autopilot' | 'probes';

type ServiceStatus = {
  [key in ServiceName]: boolean;
};

type ServiceLogs = {
  [key in ServiceName]: string[];
};

type ServiceContextType = {
  status: ServiceStatus;
  logs: ServiceLogs;
  startService: (service: ServiceName) => Promise<void>;
  stopService: (service: ServiceName) => Promise<void>;
  getLogs: (service: ServiceName) => string[];
  refreshStatus: () => Promise<void>;
};

const ServiceStatusContext = createContext<ServiceContextType | undefined>(undefined);

export function ServiceStatusProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<ServiceStatus>({
    router: false,
    autopilot: false,
    probes: false,
  });

  const [logs, setLogs] = useState<ServiceLogs>({
    router: [],
    autopilot: [],
    probes: [],
  });

  const refreshStatus = async () => {
    try {
      const healthRes = await adminApi.getHealth();
      
      setStatus({
        router: healthRes?.router ?? false,
        autopilot: healthRes?.autopilot ?? false,
        probes: false, // Not available in health check
      });
    } catch (error) {
      console.error('Failed to refresh service status:', error);
      toast.error('Failed to refresh service status');
    }
  };

  const startService = async (service: ServiceName) => {
    try {
      await adminApi.startService(service);
      await refreshStatus();
      toast.success(`${service} started successfully`);
    } catch (error) {
      console.error(`Failed to start ${service}:`, error);
      toast.error(`Failed to start ${service}`);
    }
  };

  const stopService = async (service: ServiceName) => {
    try {
      await adminApi.stopService(service);
      await refreshStatus();
      toast.success(`${service} stopped successfully`);
    } catch (error) {
      console.error(`Failed to stop ${service}:`, error);
      toast.error(`Failed to stop ${service}`);
    }
  };

  const getLogs = (service: ServiceName): string[] => {
    return logs[service] || [];
  };

  // Initial load
  useEffect(() => {
    refreshStatus();
    
    // Set up polling
    const interval = setInterval(refreshStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <ServiceStatusContext.Provider
      value={{
        status,
        logs,
        startService,
        stopService,
        getLogs,
        refreshStatus,
      }}
    >
      {children}
    </ServiceStatusContext.Provider>
  );
}

export function useServiceStatus() {
  const context = useContext(ServiceStatusContext);
  if (context === undefined) {
    throw new Error('useServiceStatus must be used within a ServiceStatusProvider');
  }
  return context;
}
