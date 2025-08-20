import { useState, useCallback, useRef, useEffect } from 'react';
import axios from 'axios';

// Cache configuration
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// Request cache
const requestCache = new Map();

// Create axios instance with default config
const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
const api = axios.create({
  baseURL: apiUrl,
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
  },
  withCredentials: true,
  timeout: 30000, // 30 seconds
});

// Add request interceptor for auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If the error is 401 and we haven't tried to refresh the token yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const response = await axios.post(`${originalRequest.baseURL}/api/auth/refresh`, {}, {
          withCredentials: true
        });
        
        const { access_token } = response.data;
        localStorage.setItem('authToken', access_token);
        
        // Update the authorization header
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        
        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh fails, redirect to login
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

/**
 * Custom hook for making API requests with retry and cache
 * @returns {Object} API methods and loading/error states
 */
export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const activeRequests = useRef(new Set());

  // Cancel all pending requests on unmount
  useEffect(() => {
    return () => {
      activeRequests.current.forEach(cancel => cancel());
      activeRequests.current.clear();
    };
  }, []);

  // Generate cache key from request config
  const getCacheKey = (method, url, data) => {
    return `${method}:${url}:${JSON.stringify(data || {})}`;
  };

  // Handle API request with retry logic
  const request = useCallback(async (method, url, data = null, config = {}) => {
    const cacheKey = getCacheKey(method, url, data);
    const source = axios.CancelToken.source();
    activeRequests.current.add(source.cancel);

    // Check cache first if it's a GET request
    if (method.toLowerCase() === 'get' && requestCache.has(cacheKey)) {
      const { data: cachedData, timestamp } = requestCache.get(cacheKey);
      if (Date.now() - timestamp < CACHE_TTL) {
        activeRequests.current.delete(source.cancel);
        return cachedData;
      }
      // Remove expired cache
      requestCache.delete(cacheKey);
    }

    let retryCount = 0;
    const makeRequest = async () => {
      while (retryCount < MAX_RETRIES) {
        try {
          setLoading(true);
          setError(null);

          const response = await api({
            method,
            url,
            data,
            cancelToken: source.token,
            ...config,
          });

          // Cache successful GET responses
          if (method.toLowerCase() === 'get') {
            requestCache.set(cacheKey, {
              data: response.data,
              timestamp: Date.now(),
            });
          }

          return response.data;
        } catch (err) {
          retryCount++;
          
          // Don't retry on 4xx errors (except 401 which is handled by interceptor)
          if (err.response?.status >= 400 && err.response?.status < 500 && err.response?.status !== 429) {
            throw err;
          }
          
          // Don't retry if request was canceled
          if (axios.isCancel(err)) {
            throw err;
          }
          
          // If we've exhausted retries, throw the error
          if (retryCount >= MAX_RETRIES) {
            throw err;
          }
          
          // Exponential backoff
          const delay = RETRY_DELAY * Math.pow(2, retryCount - 1);
          await new Promise(resolve => setTimeout(resolve, delay));
        } finally {
          if (retryCount >= MAX_RETRIES || !activeRequests.current.has(source.cancel)) {
            setLoading(false);
          }
        }
      }
    };

    try {
      return await makeRequest();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'An error occurred';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      activeRequests.current.delete(source.cancel);
    }
  }, []);

  // Clear specific cache entry
  const clearCache = useCallback((method, url, data) => {
    const cacheKey = getCacheKey(method, url, data);
    requestCache.delete(cacheKey);
  }, []);

  // Clear all cache
  const clearAllCache = useCallback(() => {
    requestCache.clear();
  }, []);

  // GET request with caching
  const get = useCallback(
    (url, config = {}) => request('get', url, null, config),
    [request]
  );

  // POST request with cache invalidation
  const post = useCallback(
    (url, data = {}, config = {}) => {
      // Clear any cached GET requests that might be affected by this POST
      clearCache('get', url, null);
      return request('post', url, data, config);
    },
    [request, clearCache]
  );

  // PUT request with cache invalidation
  const put = useCallback(
    (url, data = {}, config = {}) => {
      clearCache('get', url, null);
      return request('put', url, data, config);
    },
    [request, clearCache]
  );

  // DELETE request with cache invalidation
  const del = useCallback(
    (url, config = {}) => {
      clearCache('get', url, null);
      return request('delete', url, null, config);
    },
    [request, clearCache]
  );

  return {
    loading,
    error,
    get,
    post,
    put,
    delete: del,
    clearCache,
    clearAllCache,
  };
};

/**
 * Custom hook for IASupervisor API with enhanced error handling and caching
 * @returns {Object} IASupervisor API methods
 */
export const useIASupervisor = () => {
  const { get, post, error, loading } = useApi();
  const [status, setStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [logs, setLogs] = useState([]);
  const [algorithms, setAlgorithms] = useState([]);

  // Ask a question to the AI Supervisor
  const askQuestion = useCallback(async (question, context = {}) => {
    try {
      const response = await post('/api/ia/ask', { question, context });
      // Update logs with the new question and response
      setLogs(prev => [
        ...prev,
        { type: 'question', content: question, timestamp: new Date().toISOString() },
        { type: 'response', content: response.response, timestamp: new Date().toISOString() }
      ].slice(-100)); // Keep only last 100 entries
      return response;
    } catch (err) {
      console.error('Error asking question:', err);
      throw err;
    }
  }, [post]);

  // Analyze system status
  const analyzeSystem = useCallback(async () => {
    try {
      const result = await post('/api/ia/analyze');
      // Update status with latest analysis
      setStatus(prev => ({
        ...prev,
        lastAnalysisTime: new Date().toISOString(),
        analysisResults: result
      }));
      return result;
    } catch (err) {
      console.error('Error analyzing system:', err);
      throw err;
    }
  }, [post]);

  // Fix detected issues
  const fixIssues = useCallback(async () => {
    try {
      const result = await post('/api/ia/fix');
      // Refresh status after fixing issues
      await fetchStatus();
      return result;
    } catch (err) {
      console.error('Error fixing issues:', err);
      throw err;
    }
  }, [post]);

  // Change operation mode
  const switchMode = useCallback(async (mode) => {
    try {
      await post('/api/ia/switch-mode', { mode });
      // Update local status with new mode
      setStatus(prev => ({
        ...prev,
        mode
      }));
    } catch (err) {
      console.error('Error switching mode:', err);
      throw err;
    }
  }, [post]);

  // Get current status
  const fetchStatus = useCallback(async () => {
    try {
      const statusData = await get('/api/ia/status');
      setStatus(statusData);
      return statusData;
    } catch (err) {
      console.error('Error fetching status:', err);
      throw err;
    }
  }, [get]);

  // List available algorithms
  const fetchAlgorithms = useCallback(async () => {
    try {
      const algorithmsData = await get('/api/ia/algorithms');
      setAlgorithms(algorithmsData);
      return algorithmsData;
    } catch (err) {
      console.error('Error fetching algorithms:', err);
      throw err;
    }
  }, [get]);

  // Get interaction logs
  const fetchLogs = useCallback(async (limit = 100) => {
    try {
      const logsData = await get(`/api/ia/logs?limit=${limit}`);
      setLogs(logsData);
      return logsData;
    } catch (err) {
      console.error('Error fetching logs:', err);
      throw err;
    }
  }, [get]);

  // Simulate traffic
  const simulateTraffic = useCallback(async (params = {}) => {
    try {
      return await post('/api/ia/simulate', params);
    } catch (err) {
      console.error('Error simulating traffic:', err);
      throw err;
    }
  }, [post]);

  // Initial data loading
  useEffect(() => {
    fetchStatus();
    fetchAlgorithms();
    fetchLogs();
  }, [fetchStatus, fetchAlgorithms, fetchLogs]);

  return {
    // State
    status,
    alerts,
    logs,
    algorithms,
    loading,
    error,
    
    // Actions
    askQuestion,
    analyzeSystem,
    fixIssues,
    switchMode,
    fetchStatus,
    fetchAlgorithms,
    fetchLogs,
    simulateTraffic,
  };
};

export default useApi;
