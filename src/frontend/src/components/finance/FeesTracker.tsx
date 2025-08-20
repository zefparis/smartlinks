/**
 * FeesTracker Component
 * Displays and analyzes payment processing fees
 */

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Button } from '../ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Progress } from '../ui/progress';
import { Download, TrendingUp, TrendingDown } from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { format } from 'date-fns';
import { useFees } from '../../hooks/useFinance';

export function FeesTracker() {
  const [timeRange, setTimeRange] = useState('7d');
  const [provider, setProvider] = useState('all');
  
  const { data: feesData, isLoading } = useFees({
    timeRange,
    provider: provider === 'all' ? undefined : provider,
  });

  const formatCurrency = (amount: number, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount / 100);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const calculateSavings = () => {
    if (!feesData) return 0;
    const avgRate = feesData.total_fees / feesData.total_volume;
    const industryAvg = 0.029; // 2.9% industry average
    return Math.max(0, (industryAvg - avgRate) * feesData.total_volume);
  };

  const savings = calculateSavings();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Fees Analysis</h2>
          <p className="text-muted-foreground">
            Track processing fees and optimize costs
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="1y">Last year</SelectItem>
            </SelectContent>
          </Select>
          <Select value={provider} onValueChange={setProvider}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Providers</SelectItem>
              <SelectItem value="stripe_cards">Stripe</SelectItem>
              <SelectItem value="paypal">PayPal</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Fees</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {feesData ? formatCurrency(feesData.total_fees) : '$0'}
            </div>
            <p className="text-xs text-muted-foreground">
              {timeRange === '7d' ? 'This week' : 
               timeRange === '30d' ? 'This month' :
               timeRange === '90d' ? 'This quarter' : 'This year'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Average Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {feesData ? formatPercent(feesData.average_rate * 100) : '0%'}
            </div>
            <div className="flex items-center text-xs">
              {feesData && feesData.rate_trend < 0 ? (
                <>
                  <TrendingDown className="mr-1 h-3 w-3 text-green-600" />
                  <span className="text-green-600">
                    {Math.abs(feesData.rate_trend).toFixed(1)}% lower
                  </span>
                </>
              ) : feesData && feesData.rate_trend > 0 ? (
                <>
                  <TrendingUp className="mr-1 h-3 w-3 text-red-600" />
                  <span className="text-red-600">
                    {feesData.rate_trend.toFixed(1)}% higher
                  </span>
                </>
              ) : (
                <span className="text-muted-foreground">No change</span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {feesData ? formatCurrency(feesData.total_volume) : '$0'}
            </div>
            <p className="text-xs text-muted-foreground">
              {feesData?.transaction_count || 0} transactions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Estimated Savings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(savings)}
            </div>
            <p className="text-xs text-muted-foreground">
              vs industry average (2.9%)
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="breakdown">Breakdown</TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Fees Trend</CardTitle>
              <CardDescription>Daily fees and effective rate over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height="300">
                <LineChart data={feesData?.daily_fees || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                  />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip 
                    labelFormatter={(value) => format(new Date(value), 'MMM dd, yyyy')}
                    formatter={(value: any, name: string) => 
                      name === 'fees' ? formatCurrency(value) : formatPercent(value)
                    }
                  />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="fees"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name="Fees"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="rate"
                    stroke="#10b981"
                    strokeWidth={2}
                    name="Rate (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Breakdown Tab */}
        <TabsContent value="breakdown" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Fee Breakdown by Provider</CardTitle>
              <CardDescription>Compare fees across payment providers</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ResponsiveContainer width="100%" height="200">
                <BarChart data={feesData?.provider_breakdown || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="provider" />
                  <YAxis />
                  <Tooltip formatter={(value: any) => formatCurrency(value)} />
                  <Bar dataKey="fees" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Provider</TableHead>
                    <TableHead>Volume</TableHead>
                    <TableHead>Fees</TableHead>
                    <TableHead>Rate</TableHead>
                    <TableHead>Transactions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {feesData?.provider_breakdown?.map((provider) => (
                    <TableRow key={provider.provider}>
                      <TableCell className="font-medium capitalize">
                        {provider.provider.replace('_', ' ')}
                      </TableCell>
                      <TableCell>{formatCurrency(provider.volume)}</TableCell>
                      <TableCell>{formatCurrency(provider.fees)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span>{formatPercent(provider.rate * 100)}</span>
                          <Progress
                            value={provider.rate * 100 * 20} // Scale to 0-100 (5% max)
                            className="w-16 h-2"
                          />
                        </div>
                      </TableCell>
                      <TableCell>{provider.transaction_count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Comparison Tab */}
        <TabsContent value="comparison" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Rate Comparison</CardTitle>
              <CardDescription>Your rates vs industry standards</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {feesData?.provider_breakdown?.map((provider) => {
                  const industryRates: Record<string, number> = {
                    stripe_cards: 0.029,
                    paypal: 0.034,
                  };
                  const industryRate = industryRates[provider.provider] || 0.03;
                  const difference = provider.rate - industryRate;
                  const isLower = difference < 0;
                  
                  return (
                    <div key={provider.provider} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-medium capitalize">
                          {provider.provider.replace('_', ' ')}
                        </span>
                        <span className={isLower ? 'text-green-600' : 'text-red-600'}>
                          {isLower ? '▼' : '▲'} {formatPercent(Math.abs(difference) * 100)}
                        </span>
                      </div>
                      <div className="flex gap-2 text-sm">
                        <div className="flex-1">
                          <div className="flex justify-between mb-1">
                            <span>Your Rate</span>
                            <span>{formatPercent(provider.rate * 100)}</span>
                          </div>
                          <Progress value={provider.rate * 1000} className="h-2" />
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between mb-1">
                            <span>Industry Avg</span>
                            <span>{formatPercent(industryRate * 100)}</span>
                          </div>
                          <Progress 
                            value={industryRate * 1000} 
                            className="h-2 bg-gray-200"
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
