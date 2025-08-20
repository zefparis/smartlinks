import { useEffect, useRef, useState, useCallback } from 'react';
import api from '@/lib/api';
import { toast } from 'sonner';

export type ServiceLevel = 'active' | 'warning' | 'down';

export type SystemStatus = {
  router: ServiceLevel;
  autopilot: ServiceLevel;
  probes: ServiceLevel;
};

type RawStatus = Partial<Record<keyof SystemStatus, ServiceLevel | boolean | string | null | undefined>>;

const normalizeLevel = (v: unknown, fallback: ServiceLevel = 'down'): ServiceLevel => {
  // supporte boolean, string, null/undefined
  if (typeof v === 'boolean') return v ? 'active' : 'down';
  if (typeof v === 'string') {
    const x = v.toLowerCase();
    if (x === 'active' || x === 'warning' || x === 'down') return x;
    if (x === 'ok' || x === 'healthy' || x === 'up') return 'active';
    if (x === 'degraded') return 'warning';
    if (x === 'fail' || x === 'error' || x === 'offline') return 'down';
  }
  return fallback;
};

export default function useSystemStatus(pollMs: number = 10000) {
  const [status, setStatus] = useState<SystemStatus>({
    router: 'down',
    autopilot: 'down',
    probes: 'warning',
  });
  const [errors, setErrors] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  // évite race conditions (on ignore les réponses obsolètes)
  const seqRef = useRef(0);
  // anti-spam toast
  const toastShownRef = useRef(false);

  const fetchStatus = useCallback(async () => {
    const seq = ++seqRef.current;
    try {
      setIsLoading(true);
      const data: RawStatus = await api.getSystemStatus() || {};

      // normalisation robuste
      const next: SystemStatus = {
        router: normalizeLevel(data.router, 'down'),
        autopilot: normalizeLevel(data.autopilot, 'down'),
        probes: normalizeLevel(data.probes, 'warning'),
      };

      // ignore si une réponse plus récente a déjà été appliquée
      if (seq !== seqRef.current) return;

      setStatus(next);
      setLastUpdated(Date.now());
      setIsLoading(false);
      toastShownRef.current = false; // reset anti-spam si ça remarche
    } catch (e: any) {
      // ignore si réponse plus récente
      if (seq !== seqRef.current) return;

      setIsLoading(false);
      setErrors(prev => [
        `${new Date().toISOString()} - ${(e?.message || 'system status failed')}`,
        ...prev,
      ].slice(0, 200));

      // on dégrade sans casser probes si elle venait d’une autre source
      setStatus(prev => ({
        ...prev,
        router: 'down',
        autopilot: 'down',
      }));

      if (!toastShownRef.current) {
        toast.error('System status check failed');
        toastShownRef.current = true; // une fois par cycle de panne
      }
    }
  }, []);

  useEffect(() => {
    // premier fetch
    fetchStatus();

    // polling + pause quand l'onglet est caché
    let interval: number | undefined;

    const start = () => {
      // évite double interval
      if (interval) clearInterval(interval);
      interval = window.setInterval(fetchStatus, pollMs);
    };

    const stop = () => {
      if (interval) {
        clearInterval(interval);
        interval = undefined;
      }
    };

    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        fetchStatus(); // refresh immédiat
        start();
      } else {
        stop();
      }
    };

    // initialisation
    if (document.visibilityState === 'visible') start();

    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      stop();
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [fetchStatus, pollMs]);

  // expose un refresh manuel (idempotent)
  const refresh = useCallback(() => fetchStatus(), [fetchStatus]);

  return { status, errors, isLoading, lastUpdated, refresh };
}
