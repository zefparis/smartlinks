import axios, { AxiosInstance, AxiosResponse } from 'axios';

import { format, subDays } from 'date-fns';
import { toast } from 'sonner';

// Helper type for unwrapping Axios responses
type UnwrapAxiosResponse<T> = T extends Promise<AxiosResponse<infer D>> ? Promise<D> : T;

async function unwrapResponse<T>(promise: Promise<AxiosResponse<T>>): Promise<T> {
  const response = await promise;
  return response.data;
}

const api: AxiosInstance = axios.create({
  baseURL: '/',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for API calls
api.interceptors.request.use(
  (config) => {
    // You can add auth tokens here if needed
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error?.response?.data?.message || error?.message || 'Unknown error';
    toast.error(`API Error: ${message}`);
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export interface HealthCheckResponse {
  router: boolean;
  autopilot: boolean;
  ts: string;
}

export type ServiceLevel = 'active' | 'warning' | 'down';
export interface SystemStatusResponse {
  router: ServiceLevel;
  autopilot: ServiceLevel;
  probes: ServiceLevel;
  ts: string;
}

export interface MetricsResponse {
  clicks_total: number;
  last_click_id: string | null;
  last_click_time: string | null;
  segments: Array<{
    segment: string;
    count: number;
    avg_risk: number;
  }>;
}

export interface StatsResponse {
  clicks_total: number;
  fraud_suspects: number;
  approved: number;
  fraud_rate: number;
  approval_rate: number;
}

export interface RecentClick {
  id: string;
  created_at: string;
  user: string;
  segment: string;
  risk: number;
  offer_id: string | null;
}

// Types supplémentaires
export interface ClickHistory {
  date: string;
  clicks: number;
  conversions: number;
  revenue: number;
}

export interface TrafficStats {
  date: string;
  clicks: number;
  conversions: number;
  revenue: number;
}

export interface DeviceStats {
  device: string;
  count: number; // Mapped from backend 'clicks' field
  conversion_rate: number;
  clicks?: number; // Backend field
  conversions?: number; // Backend field
  revenue?: number; // Backend field
}

export interface CountryStats {
  country: string;
  clicks: number;
  conversions: number;
  revenue: number;
}

export interface DiscoveryResponse {
  opportunities: Array<{
    segment: string;
    reason: string;
  }>;
  alerts: Array<{
    issue: string;
    details: string;
  }>;
  projections: {
    clicks_next_7_days: number;
    expected_revenue: number;
  };
}

interface ApiClient {
  getHealth: () => Promise<HealthCheckResponse>;
  getMetrics: () => Promise<MetricsResponse>;
  getStats: () => Promise<StatsResponse>;
  getRecentClicks: (limit?: number, days?: number, device?: string, country?: string) => Promise<RecentClick[]>;
  getClickHistory: (days?: number, segmentId?: string, device?: string, country?: string) => Promise<ClickHistory[]>;
  getDeviceStats: (segmentId?: string, timeRange?: string) => Promise<DeviceStats[]>;
  getCountryStats: (days?: number, limit?: number) => Promise<CountryStats[]>;
  seedDatabase: () => Promise<any>;
  updatePayouts: () => Promise<any>;
  flushDatabase: () => Promise<any>;
  getConfig: () => Promise<any>;
  updateConfig: (config: any) => Promise<any>;
  getSettings: () => Promise<any>;
  updateGeneralSetting: (key: string, value: any) => Promise<any>;
  updateOfferSetting: (offerId: string, key: string, value: any) => Promise<any>;
  exportSettings: () => Promise<any>;
  startService: (service: string) => Promise<any>;
  stopService: (service: string) => Promise<any>;
  getServiceStatus: () => Promise<any>;
  getServiceLogs: (service: string) => Promise<string>;
  getSystemStatus: () => Promise<SystemStatusResponse>;
  askAssistant: (question: string) => Promise<{ answer: string }>;
  askDG: (question: string, insights?: any) => Promise<{ answer: string }>;
  askDiscovery: (days?: number) => Promise<DiscoveryResponse>;
  iaStatus: () => Promise<any>;
  iaAsk: (question: string, context?: any) => Promise<any>;
}

const apiClient: ApiClient = {
  // Health
  getHealth: () => unwrapResponse(api.get<HealthCheckResponse>('/api/health')),
  
  // Metrics
  getMetrics: () => unwrapResponse(api.get<MetricsResponse>('/api/metrics')),
  
  // Stats
  getStats: () => unwrapResponse(api.get<StatsResponse>('/api/stats')),
  
  // Clicks
  getRecentClicks: (limit: number = 50, days?: number, device?: string, country?: string) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (days) params.append('days', days.toString());
    if (device) params.append('device', device);
    if (country) params.append('country', country);
    
    return unwrapResponse(api.get<RecentClick[]>(`/api/clicks/recent?${params.toString()}`));
  },
  
  // Analytics - Fixed to handle backend response wrappers
  getDeviceStats: async (days: number = 30, limit: number = 10) => {
    try {
      const response = await unwrapResponse(api.get(`/api/analytics/devices?days=${days}&limit=${limit}`));
      console.log('DEBUG getDeviceStats response:', response);
      
      // Backend returns {devices: [...], total_clicks: ..., ...}
      // Normalize to array format expected by frontend
      const devices = response?.devices ?? response ?? [];
      
      // Ensure devices is always an array
      if (!Array.isArray(devices)) {
        console.warn('getDeviceStats: devices is not an array, returning empty array');
        return [];
      }
      
      // Map backend 'clicks' field to frontend 'count' field
      return devices.map((device: any) => ({
        device: device?.device || 'unknown',
        count: device?.clicks || 0, // Map clicks -> count
        conversion_rate: device?.conversion_rate || 0,
        clicks: device?.clicks || 0,
        conversions: device?.conversions || 0,
        revenue: device?.revenue || 0
      }));
    } catch (error) {
      console.error('getDeviceStats error:', error);
      return [];
    }
  },
  
  getCountryStats: async (days: number = 30, limit: number = 10) => {
    try {
      const response = await unwrapResponse(api.get(`/api/analytics/countries?days=${days}&limit=${limit}`));
      console.log('DEBUG getCountryStats response:', response);
      
      // Backend returns {countries: [...]} - normalize to array
      const countries = response?.countries ?? response ?? [];
      
      // Ensure countries is always an array
      if (!Array.isArray(countries)) {
        console.warn('getCountryStats: countries is not an array, returning empty array');
        return [];
      }
      
      return countries.map((country: any) => ({
        country: country?.country || 'Unknown',
        clicks: country?.clicks || 0,
        conversions: country?.conversions || 0,
        revenue: country?.revenue || 0,
        conversion_rate: country?.conversion_rate || 0
      }));
    } catch (error) {
      console.error('getCountryStats error:', error);
      return [];
    }
  },
  
  getClickHistory: async (days: number = 30, segmentId?: string, device?: string, country?: string) => {
    try {
      const params = new URLSearchParams();
      params.append('days', days.toString());
      if (segmentId) params.append('segment_id', segmentId);
      if (device) params.append('device', device);
      if (country) params.append('country', country);
      
      const response = await unwrapResponse(api.get(`/api/analytics/clicks/history?${params.toString()}`));
      console.log('DEBUG getClickHistory response:', response);
      
      // Backend returns {history: [...], total_clicks: ...} - normalize to array
      const history = response?.history ?? response ?? [];
      
      // Ensure history is always an array
      if (!Array.isArray(history)) {
        console.warn('getClickHistory: history is not an array, returning empty array');
        return [];
      }
      
      return history.map((entry: any) => ({
        date: entry?.date || new Date().toISOString().split('T')[0],
        clicks: entry?.clicks || 0,
        conversions: entry?.conversions || 0,
        revenue: entry?.revenue || 0
      }));
    } catch (error) {
      console.error('getClickHistory error:', error);
      return [];
    }
  },
  
  // Admin Actions
  seedDatabase: () => unwrapResponse(api.post('/api/admin/seed')),
  updatePayouts: () => unwrapResponse(api.post('/api/admin/payouts')),
  flushDatabase: () => unwrapResponse(api.post('/api/admin/flush')),
  
  // Configuration
  getConfig: () => unwrapResponse(api.get('/api/config')),
  updateConfig: (config: any) => unwrapResponse(api.put('/api/config', config)),
  
  // Settings - Added missing endpoints
  getSettings: () => unwrapResponse(api.get('/api/settings')),
  updateGeneralSetting: (key: string, value: any) => 
    unwrapResponse(api.put('/api/settings/general', { key, value })),
  updateOfferSetting: (offerId: string, key: string, value: any) => 
    unwrapResponse(api.put(`/api/settings/offer/${offerId}`, { key, value })),
  exportSettings: () => unwrapResponse(api.get('/api/settings/export')),
  
  // Service control
  startService: (service: string) => unwrapResponse(api.post(`/api/services/${service}/start`)),
  stopService: (service: string) => unwrapResponse(api.post(`/api/services/${service}/stop`)),
  getServiceStatus: () => unwrapResponse(api.get('/api/services/status')),
  getServiceLogs: (service: string) => unwrapResponse(api.get(`/api/services/${service}/logs`)),

  // System status (dashboard)
  getSystemStatus: () => unwrapResponse(api.get<SystemStatusResponse>('/api/status')),
  
  // AI Assistant
  askAssistant: (question: string) =>
    unwrapResponse(api.post<{ answer: string }>('/api/assistant/ask', { question })),
    
  // CEO Assistant (DG AI)
  askDG: (prompt: string) =>
    unwrapResponse(api.post('/api/ai/dg', { prompt })),
  
  // AI Discovery
  askDiscovery: (days: number = 30) => 
    unwrapResponse(api.post<DiscoveryResponse>('/api/ai/discovery', { days })),
  
  // IA Supervisor - Unified API
  iaStatus: () => unwrapResponse(api.get('/api/ia/status')),
  iaAsk: (question: string, context?: any) => 
    unwrapResponse(api.post('/api/ia/ask', { question, context }))
};

export default apiClient;
