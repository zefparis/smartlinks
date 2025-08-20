import { useState, useEffect, useCallback, useRef } from 'react';
import { useApi, ApiErrorType } from './useApiV2';

// Module-level one-time init promise and data cache to survive StrictMode double-mount
let __iaInitPromise = null;
let __iaInitData = null; // { available, status, alerts, logs }

const useIASupervisor = () => {
  const { get, post, error: apiError } = useApi();
  const [isAvailable, setIsAvailable] = useState(true);
  const [status, setStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [logs, setLogs] = useState([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const mountedRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Check if IA service is available
  const checkAvailability = useCallback(async () => {
    try {
      const status = await get('/api/ia/status');
      setIsAvailable(true);
      setStatus(status);
      return true;
    } catch (error) {
      if (error.type === ApiErrorType.NOT_FOUND) {
        setIsAvailable(false);
        return false;
      }
      throw error;
    }
  }, [get]);

  // Internal: fetch initial data once (no state updates here)
  const fetchInitial = useCallback(async () => {
    try {
      const statusRes = await get('/api/ia/status').catch(() => null);
      const available = !!statusRes;

      let alertsRes = [];
      let logsRes = [];
      if (available) {
        [alertsRes, logsRes] = await Promise.all([
          get('/api/ia/alerts').catch(() => []),
          get('/api/ia/logs').catch(() => []),
        ]);
      }

      const data = {
        available,
        status: statusRes || null,
        alerts: Array.isArray(alertsRes) ? alertsRes : [],
        logs: Array.isArray(logsRes) ? logsRes : [],
      };
      __iaInitData = data;
      return data;
    } catch (error) {
      console.error('Failed to initialize IA Supervisor:', error);
      const data = { available: false, status: null, alerts: [], logs: [] };
      __iaInitData = data;
      return data;
    }
  }, [get]);

  // Apply cached/init data to component state (guarded by mountedRef)
  const applyInitData = useCallback((data) => {
    if (!mountedRef.current) return;
    setIsAvailable(!!data.available);
    setStatus(data.status || null);
    setAlerts(Array.isArray(data.alerts) ? data.alerts : []);
    setLogs(Array.isArray(data.logs) ? data.logs : []);
  }, []);

  // Public: initialize once per app lifecycle
  const initialize = useCallback(async () => {
    if (__iaInitPromise) {
      const data = await __iaInitPromise;
      applyInitData(data);
      setIsInitialized(true);
      return data.available;
    }

    __iaInitPromise = fetchInitial();
    const data = await __iaInitPromise;
    applyInitData(data);
    setIsInitialized(true);
    return data.available;
  }, [applyInitData, fetchInitial]);

  // Ask a question to the IA
  const askQuestion = useCallback(async (question) => {
    try {
      const response = await post('/api/ia/ask', { question });
      // Backend may return {answer} (assistant_router) or {response} (IA Supervisor)
      return response?.answer ?? response?.response ?? null;
    } catch (error) {
      if (error.type === ApiErrorType.NOT_FOUND) {
        setIsAvailable(false);
        throw new Error('IA service is not available');
      }
      throw error;
    }
  }, [post]);

  // Analyze system status
  const analyzeSystem = useCallback(async () => {
    try {
      // Backend exposes GET /api/ia/analyze returning AnalyzeResponse
      const result = await get('/api/ia/analyze');
      // Prefer AI analysis section; fallback to full result
      return result?.ai_analysis ?? result ?? null;
    } catch (error) {
      if (error.type === ApiErrorType.NOT_FOUND) {
        setIsAvailable(false);
        throw new Error('Analysis service is not available');
      }
      throw error;
    }
  }, [get]);

  // Initialize on mount (StrictMode-safe)
  useEffect(() => {
    initialize();
  }, [initialize]);

  return {
    // State
    isAvailable,
    status,
    alerts,
    logs,
    loading: !isInitialized,
    error: apiError,
    
    // Methods
    askQuestion,
    analyzeSystem,
    checkAvailability,
    // Force a full refresh regardless of init (always refetch)
    refresh: useCallback(async () => {
      const data = await fetchInitial();
      applyInitData(data);
      return data.available;
    }, [fetchInitial, applyInitData]),
  };
};

export default useIASupervisor;
