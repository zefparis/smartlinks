import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import axios from 'axios';

// Error types for better error handling
export const ApiErrorType = {
  NETWORK: 'NETWORK_ERROR',
  TIMEOUT: 'TIMEOUT_ERROR',
  ABORTED: 'ABORTED_ERROR',
  NOT_FOUND: 'NOT_FOUND',
  FORBIDDEN: 'FORBIDDEN',
  SERVER: 'SERVER_ERROR',
  UNAUTHORIZED: 'UNAUTHORIZED',
  VALIDATION: 'VALIDATION_ERROR',
  UNKNOWN: 'UNKNOWN_ERROR',
};

// Create axios instance with default config
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
  timeout: 10000, // 10 seconds
});

// Request interceptor for auth token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    if (axios.isCancel(error)) {
      return Promise.reject({ type: ApiErrorType.ABORTED, message: 'Request cancelled' });
    }

    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        return Promise.reject({ type: ApiErrorType.TIMEOUT, message: 'Request timed out' });
      }
      return Promise.reject({ type: ApiErrorType.NETWORK, message: 'Network error' });
    }

    const { status, data } = error.response;
    const errorMap = {
      400: { type: ApiErrorType.VALIDATION, message: data?.message || 'Invalid request' },
      401: { type: ApiErrorType.UNAUTHORIZED, message: 'Session expired' },
      403: { type: ApiErrorType.FORBIDDEN, message: 'Access denied' },
      404: { type: ApiErrorType.NOT_FOUND, message: 'Resource not found' },
      500: { type: ApiErrorType.SERVER, message: 'Server error' },
    };

    const errorInfo = errorMap[status] || { 
      type: ApiErrorType.UNKNOWN, 
      message: data?.message || 'An error occurred' 
    };

    return Promise.reject({
      ...errorInfo,
      status,
      data: data,
    });
  }
);

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const activeRequests = useRef(new Map());

  // Clean up requests on unmount
  useEffect(() => {
    return () => {
      activeRequests.current.forEach((cancel, id) => {
        cancel(`Request ${id} was cancelled`);
      });
      activeRequests.current.clear();
    };
  }, []);

  const request = useCallback(async (method, url, data = null, config = {}) => {
    const source = axios.CancelToken.source();
    const requestId = Date.now();
    
    // Add to active requests
    activeRequests.current.set(requestId, source.cancel);
    
    setLoading(true);
    setError(null);

    try {
      const response = await api({
        method,
        url,
        data,
        cancelToken: source.token,
        ...config,
      });
      
      return response.data;
    } catch (error) {
      if (error.type !== ApiErrorType.ABORTED) {
        setError(error);
      }
      throw error;
    } finally {
      activeRequests.current.delete(requestId);
      setLoading(activeRequests.current.size > 0);
    }
  }, []);

  const get = useMemo(() => (url, data, config) => request('get', url, data, config), [request]);
  const post = useMemo(() => (url, data, config) => request('post', url, data, config), [request]);
  const put = useMemo(() => (url, data, config) => request('put', url, data, config), [request]);
  const del = useMemo(() => (url, data, config) => request('delete', url, data, config), [request]);

  return {
    get,
    post,
    put,
    delete: del,
    loading,
    error,
    cancelAll: () => {
      activeRequests.current.forEach(cancel => cancel('All requests cancelled'));
      activeRequests.current.clear();
    },
  };
};

export default useApi;
