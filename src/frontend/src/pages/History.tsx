import React, { useEffect, useState } from 'react';
import { format } from 'date-fns';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DatePickerWithRange } from '@/components/ui/date-range-picker';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow, TableFooter } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import dayjs, { Dayjs } from 'dayjs';
import api, { ClickHistory } from '@/lib/api';
import { useTheme } from '@/contexts/ThemeContext';
import { cn } from '@/lib/utils';
import { classes } from '@/lib/design-system';

export default function History() {
  const { theme } = useTheme();
  const [historyData, setHistoryData] = useState<ClickHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'7days' | '30days' | '90days' | 'custom'>('30days');
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([dayjs().subtract(29, 'day'), dayjs()]);
  const [groupBy, setGroupBy] = useState<'day' | 'week' | 'month'>('day');
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);

  const colors = {
    axis: theme === 'dark' ? '#e5e7eb' : '#111827',
    grid: theme === 'dark' ? '#374151' : '#e5e7eb',
    text: theme === 'dark' ? '#e5e7eb' : '#111827',
  };

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const [startDate, endDate] = dateRange;
      const days = endDate.diff(startDate, 'day') + 1;
      const response = await api.getClickHistory(days);
      setHistoryData(response || []);
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [timeRange, dateRange, groupBy]);

  const handleTimeRangeChange = (value: string) => {
    const timeValue = value as '7days' | '30days' | '90days' | 'custom';
    setTimeRange(timeValue);
    const today = dayjs();
    switch (timeValue) {
      case '7days':
        setDateRange([today.subtract(6, 'day'), today]);
        break;
      case '30days':
        setDateRange([today.subtract(29, 'day'), today]);
        break;
      case '90days':
        setDateRange([today.subtract(89, 'day'), today]);
        break;
      default:
        break;
    }
  };

  const handleGroupByChange = (value: string) => {
    if (value === 'day' || value === 'week' || value === 'month') {
      setGroupBy(value);
    }
  };

  const handleDateRangeChange = (range: { from: Date | undefined; to: Date | undefined }) => {
    if (range.from && range.to) {
      setTimeRange('custom');
      setDateRange([dayjs(range.from), dayjs(range.to)]);
    }
  };

  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedData = React.useMemo(() => {
    if (!sortConfig) return historyData;
    
    return [...historyData].sort((a, b) => {
      let aValue: any;
      let bValue: any;
      
      switch (sortConfig.key) {
        case 'date':
          aValue = new Date(a.date).getTime();
          bValue = new Date(b.date).getTime();
          break;
        case 'clicks':
          aValue = a.clicks;
          bValue = b.clicks;
          break;
        case 'conversions':
          aValue = a.conversions;
          bValue = b.conversions;
          break;
        case 'conversionRate':
          aValue = a.clicks > 0 ? a.conversions / a.clicks : 0;
          bValue = b.clicks > 0 ? b.conversions / b.clicks : 0;
          break;
        case 'revenue':
          aValue = a.revenue;
          bValue = b.revenue;
          break;
        case 'rpc':
          aValue = a.clicks > 0 ? a.revenue / a.clicks : 0;
          bValue = b.clicks > 0 ? b.revenue / b.clicks : 0;
          break;
        default:
          return 0;
      }
      
      if (sortConfig.direction === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  }, [historyData, sortConfig]);

  // Calculate totals
  const totals = React.useMemo(() => {
    return sortedData.reduce(
      (acc, curr) => ({
        totalClicks: acc.totalClicks + curr.clicks,
        totalConversions: acc.totalConversions + curr.conversions,
        totalRevenue: acc.totalRevenue + curr.revenue,
      }),
      { totalClicks: 0, totalConversions: 0, totalRevenue: 0 }
    );
  }, [sortedData]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Click History</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Track your click performance over time
          </p>
        </div>
        
        <div className="flex flex-wrap gap-3">
          <Select value={timeRange} onValueChange={handleTimeRangeChange}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Select time range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7days">Last 7 days</SelectItem>
              <SelectItem value="30days">Last 30 days</SelectItem>
              <SelectItem value="90days">Last 90 days</SelectItem>
              <SelectItem value="custom">Custom Range</SelectItem>
            </SelectContent>
          </Select>
          
          {timeRange === 'custom' && (
            <DatePickerWithRange
              date={{
                from: dateRange[0].toDate(),
                to: dateRange[1].toDate()
              }}
              onDateChange={handleDateRangeChange}
            />
          )}
          
          <Select value={groupBy} onValueChange={handleGroupByChange}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Group by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">By Day</SelectItem>
              <SelectItem value="week">By Week</SelectItem>
              <SelectItem value="month">By Month</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <Card className={cn(classes.card.base)}>
        <CardHeader>
          <CardTitle>Performance Trends</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-80 w-full" />
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={historyData}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fill: colors.axis }} 
                    stroke={colors.grid} 
                    tickFormatter={(date) => 
                      format(new Date(date), groupBy === 'month' ? 'MMM yyyy' : 'MMM d')
                    } 
                  />
                  <YAxis yAxisId="left" orientation="left" stroke={colors.axis} />
                  <YAxis yAxisId="right" orientation="right" stroke={colors.axis} />
                  <Tooltip 
                    contentStyle={{ 
                      background: theme === 'dark' ? '#111827' : '#ffffff', 
                      color: colors.text, 
                      border: '1px solid ' + colors.grid,
                      borderRadius: '8px'
                    }} 
                    labelFormatter={(label) => format(new Date(label), 'PPP')}
                  />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="clicks"
                    name="Clicks"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.3}
                  />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="conversions"
                    name="Conversions"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.3}
                  />
                  <Area
                    yAxisId="right"
                    type="monotone"
                    dataKey="revenue"
                    name="Revenue"
                    stroke="#f59e0b"
                    fill="#f59e0b"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className={cn(classes.card.base)}>
        <CardHeader>
          <CardTitle>Detailed History</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-64 w-full" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                      onClick={() => handleSort('date')}
                    >
                      Date
                      {sortConfig?.key === 'date' && (
                        <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 text-right"
                      onClick={() => handleSort('clicks')}
                    >
                      Clicks
                      {sortConfig?.key === 'clicks' && (
                        <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 text-right"
                      onClick={() => handleSort('conversions')}
                    >
                      Conversions
                      {sortConfig?.key === 'conversions' && (
                        <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 text-right"
                      onClick={() => handleSort('conversionRate')}
                    >
                      Conversion Rate
                      {sortConfig?.key === 'conversionRate' && (
                        <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 text-right"
                      onClick={() => handleSort('revenue')}
                    >
                      Revenue
                      {sortConfig?.key === 'revenue' && (
                        <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 text-right"
                      onClick={() => handleSort('rpc')}
                    >
                      RPC
                      {sortConfig?.key === 'rpc' && (
                        <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedData.map((row) => (
                    <TableRow key={row.date}>
                      <TableCell>{format(new Date(row.date), 'MMM d, yyyy')}</TableCell>
                      <TableCell className="text-right font-medium">{row.clicks.toLocaleString()}</TableCell>
                      <TableCell className="text-right">{row.conversions.toLocaleString()}</TableCell>
                      <TableCell className="text-right">
                        {row.clicks > 0 ? `${((row.conversions / row.clicks) * 100).toFixed(1)}%` : '0%'}
                      </TableCell>
                      <TableCell className="text-right">${row.revenue.toFixed(2)}</TableCell>
                      <TableCell className="text-right">
                        ${(row.clicks > 0 ? row.revenue / row.clicks : 0).toFixed(4)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
                {sortedData.length > 0 && (
                  <TableFooter>
                    <TableRow>
                      <TableCell className="font-semibold">Total</TableCell>
                      <TableCell className="text-right font-semibold">
                        {totals.totalClicks.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {totals.totalConversions.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {totals.totalClicks ? `${((totals.totalConversions / totals.totalClicks) * 100).toFixed(2)}%` : '0%'}
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        ${totals.totalRevenue.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        ${totals.totalClicks ? (totals.totalRevenue / totals.totalClicks).toFixed(4) : '0.0000'}
                      </TableCell>
                    </TableRow>
                  </TableFooter>
                )}
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
