import { useEffect, useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import api from '@/lib/api';
import { RecentClick } from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

type SafeClick = RecentClick & {
  slug?: string;
  geo?: string;
  status?: string;
  revenue?: number;
};

export default function RecentClicks() {
  const [clicks, setClicks] = useState<SafeClick[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecentClicks = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await api.getRecentClicks(10);

        const safeClicks: SafeClick[] = Array.isArray(response)
          ? response.map(click => ({
              ...click,
              slug: '',
              geo: 'Unknown',
              status: 'pending',
              revenue: 0
            }))
          : [];

        setClicks(safeClicks);
      } catch (err) {
        console.error('Failed to fetch recent clicks:', err);
        setError('Failed to load recent clicks');
        setClicks([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecentClicks();
    const interval = setInterval(fetchRecentClicks, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusVariant = (status?: string): "default" | "secondary" | "destructive" | "outline" => {
    switch ((status || '').toLowerCase()) {
      case 'converted':
        return 'default';
      case 'pending':
        return 'secondary';
      case 'failed':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getRiskVariant = (risk: number): "default" | "secondary" | "destructive" | "outline" => {
    if (risk > 70) return 'destructive';
    if (risk > 30) return 'secondary';
    return 'default';
  };

  const formatRevenue = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatSegment = (segment?: string) => {
    const [country = '', device = ''] = (segment || '').split(':');
    return (
      <span>
        <span className="font-medium">{country.toUpperCase() || '??'}</span>
        {device && <span className="text-gray-500">:{device}</span>}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (clicks.length === 0) {
    return (
      <Alert>
        <AlertDescription className="text-center">
          No recent clicks found
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Time</TableHead>
            <TableHead>User</TableHead>
            <TableHead>Segment</TableHead>
            <TableHead>Risk</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Revenue</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {clicks.map(click => (
            <TableRow key={click.id}>
              <TableCell className="text-sm text-gray-900 dark:text-gray-100">
                {formatDistanceToNow(new Date(click.created_at), { addSuffix: true })}
              </TableCell>
              <TableCell className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {click.user || 'Anonymous'}
              </TableCell>
              <TableCell className="text-sm text-gray-900 dark:text-gray-100">
                {click.segment ? formatSegment(click.segment) : 'N/A'}
              </TableCell>
              <TableCell>
                <Badge variant={getRiskVariant(click.risk || 0)}>
                  {click.risk || 0}%
                </Badge>
              </TableCell>
              <TableCell>
                <Badge variant={getStatusVariant(click.status)}>
                  {click.status || 'unknown'}
                </Badge>
              </TableCell>
              <TableCell className="text-sm text-gray-500 dark:text-gray-400">
                {formatRevenue(click.revenue || 0)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
