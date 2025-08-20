import React, { useEffect, useMemo, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import api from '@/lib/api';
import { ClickHistory, DeviceStats, CountryStats } from '@/lib/api';
import { useTheme } from '@/contexts/ThemeContext';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export default function Analytics() {
  const { theme } = useTheme();
  const [trafficData, setTrafficData] = useState<ClickHistory[]>([]);
  const [deviceData, setDeviceData] = useState<DeviceStats[]>([]);
  const [countryData, setCountryData] = useState<CountryStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const colors = useMemo(() => {
    const isDark = theme === 'dark';
    return {
      axis: isDark ? '#e5e7eb' : '#111827',
      grid: isDark ? '#374151' : '#e5e7eb',
      text: isDark ? '#e5e7eb' : '#111827',
      subtext: isDark ? '#9ca3af' : '#6b7280',
    };
  }, [theme]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const [trafficRes, deviceRes, countryRes] = await Promise.all([
          api.getClickHistory(30),
          api.getDeviceStats(),
          api.getCountryStats(),
        ]);

        // Debug raw responses
        console.log('DEBUG traffic:', trafficRes);
        console.log('DEBUG devices:', deviceRes);
        console.log('DEBUG countries:', countryRes);

        // Robust data handling with nullish coalescing
        setTrafficData(trafficRes ?? []);
        setDeviceData(deviceRes ?? []);
        setCountryData(countryRes ?? []);
        
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load analytics data';
        setError(errorMessage);
        console.error('Analytics error:', err);
        
        // Set fallback empty data on error
        setTrafficData([]);
        setDeviceData([]);
        setCountryData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading analytics data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center p-6 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
          <div className="text-red-600 dark:text-red-400 mb-2">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">Analytics Error</h3>
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Analytics Dashboard</h1>
      
      {/* Traffic Over Time */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow ring-1 ring-gray-200 dark:ring-gray-600 p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Traffic Over Time (Last 30 Days)</h2>
        <div className="h-80 mt-4">
          {trafficData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400">No data available</div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trafficData ?? []}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                <XAxis 
                  dataKey="date" 
                  stroke={colors.axis}
                  tick={{ fill: colors.text }}
                />
                <YAxis stroke={colors.axis} tick={{ fill: colors.text }} />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
                    border: `1px solid ${colors.grid}`,
                    borderRadius: '8px',
                    color: colors.text
                  }}
                />
                <Legend wrapperStyle={{ color: colors.text }} />
                <Bar dataKey="clicks" fill="#3b82f6" name="Clicks" />
                <Bar dataKey="conversions" fill="#10b981" name="Conversions" />
              </BarChart>
            </ResponsiveContainer>
          )}
          {(!trafficData || trafficData.length === 0) && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-gray-800/50 rounded">
              <p className="text-gray-500 dark:text-gray-400">No traffic data available</p>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Device Distribution */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow ring-1 ring-gray-200 dark:ring-gray-600 p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Traffic by Device</h2>
          <div className="h-80 mt-4">
            {deviceData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={deviceData ?? []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ device, count, percent }) => `${device ?? 'Unknown'}: ${count ?? 0} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {(deviceData ?? []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
                      border: `1px solid ${colors.grid}`,
                      borderRadius: '8px',
                      color: colors.text
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
            {(!deviceData || deviceData.length === 0) && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-gray-800/50 rounded">
                <p className="text-gray-500 dark:text-gray-400">No device data available</p>
              </div>
            )}
          </div>
        </div>

        {/* Country Distribution */}
        <div className="bg-white dark:bg-gray-900 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Traffic by Country</h2>
          <div className="space-y-2">
            {(countryData ?? []).length > 0 ? (
              (countryData ?? []).slice(0, 10).map((country, index) => (
                <div key={country?.country ?? `country-${index}`} className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className={colors.text}>{country?.country ?? 'Unknown'}</span>
                  <span className={colors.subtext}>{country?.clicks ?? 0} clicks</span>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center py-8">
                <p className="text-gray-500 dark:text-gray-400">No country data available</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Card component for consistent styling
const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div className={`bg-white dark:bg-gray-800 rounded-lg shadow ring-1 ring-gray-200 dark:ring-gray-600 p-4 ${className}`}>
    {children}
  </div>
);
