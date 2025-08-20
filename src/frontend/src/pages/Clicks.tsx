import React, { useEffect, useState } from 'react';
import { format } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { MagnifyingGlassIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import api from '@/lib/api';
import { cn } from '@/lib/utils';
import { classes } from '@/lib/design-system';


// Define the ClickRecord type based on the backend response
type ClickRecord = {
  id: number;
  timestamp: string;
  country: string;
  device: string;
  // Additional fields we'll add for display
  status: string;
  revenue: number;
  segment?: string;
  risk?: number;
};

const statusColors: Record<string, string> = {
  approved: 'green',
  pending: 'blue',
  rejected: 'red',
  fraud: 'volcano',
};

const EmptyState = () => (
  <div className="text-center py-12">
    <ExclamationTriangleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
    <div className="text-gray-500 dark:text-gray-400 text-lg font-medium">No clicks found</div>
    <p className="text-gray-400 dark:text-gray-500 mt-2">Try adjusting your search or check back later</p>
  </div>
);

export default function Clicks() {
  const [clicks, setClicks] = useState<ClickRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [filters, setFilters] = useState({
    status: '',
    search: '',
  });

  const fetchClicks = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Call the API with pagination
      const response = await api.getRecentClicks(pageSize);
      
      // Ensure we always have an array, even if the response is malformed
      const clicksData = Array.isArray(response) ? response : [];
      
      // Transform the API response to match our ClickRecord type
      const formattedClicks: ClickRecord[] = clicksData.map(click => ({
        id: click.id || 0,
        timestamp: click.timestamp || new Date().toISOString(),
        country: click.country || 'Unknown',
        device: click.device || 'desktop',
        status: 'approved', // Default status
        revenue: Math.random() * 100, // Simulated revenue
        segment: click.segment || 'organic',
        risk: Math.floor(Math.random() * 100) // Simulated risk score
      }));
      
      setClicks(formattedClicks);
    } catch (error) {
      console.error('Error fetching clicks:', error);
      setError('Failed to load clicks. Please try again later.');
      setClicks([]); // Ensure clicks is always an array
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClicks();
  }, [pageSize]);

  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const handleStatusFilter = (status: string) => {
    setFilters({ ...filters, status });
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({ ...filters, search: e.target.value });
  };

  const filteredData = React.useMemo(() => {
    let filtered = clicks.filter((click) => {
      const matchesStatus = !filters.status || click.status === filters.status;
      const matchesSearch = !filters.search || 
        Object.values(click).some(
          (val) => 
            val && 
            val.toString().toLowerCase().includes(filters.search.toLowerCase())
        );
      return matchesStatus && matchesSearch;
    });

    // Sort data if sorting is configured
    if (sortConfig) {
      filtered = [...filtered].sort((a, b) => {
        let aValue: any = a[sortConfig.key as keyof ClickRecord];
        let bValue: any = b[sortConfig.key as keyof ClickRecord];
        
        if (sortConfig.key === 'timestamp') {
          aValue = new Date(aValue).getTime();
          bValue = new Date(bValue).getTime();
        }
        
        if (sortConfig.direction === 'asc') {
          return aValue > bValue ? 1 : -1;
        } else {
          return aValue < bValue ? 1 : -1;
        }
      });
    }

    return filtered;
  }, [clicks, filters, sortConfig]);

  // Pagination
  const paginatedData = React.useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return filteredData.slice(start, end);
  }, [filteredData, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredData.length / pageSize);

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch(status.toLowerCase()) {
      case 'approved': return 'default';
      case 'pending': return 'secondary';
      case 'rejected': return 'destructive';
      case 'fraud': return 'destructive';
      default: return 'outline';
    }
  };

  const getRiskBadgeVariant = (risk: number): "default" | "secondary" | "destructive" => {
    if (risk > 70) return 'destructive';
    if (risk > 30) return 'secondary';
    return 'default';
  };

  // Show error state if there was an error
  if (error) {
    return (
      <div className="p-6">
        <Card className={cn(classes.card.base)}>
          <CardContent className="text-center py-12">
            <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <div className="text-red-500 text-lg font-medium mb-4">{error}</div>
            <Button 
              onClick={() => fetchClicks()}
              className={cn(classes.button.base, classes.button.variants.primary)}
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Recent Clicks</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Monitor and analyze your click activity in real-time
        </p>
      </div>
      
      <Card className={cn(classes.card.base)}>
        <CardHeader>
          <CardTitle>Click Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search clicks..."
                value={filters.search || ''}
                onChange={handleSearch}
                className={cn(classes.input.base, "pl-10")}
              />
            </div>
            <div className="w-full md:w-48">
              <Select
                value={filters.status || 'all'}
                onValueChange={handleStatusFilter}
              >
                <SelectTrigger className={cn(classes.input.base)}>
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="fraud">Fraud</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Select
              value={pageSize.toString()}
              onValueChange={(value) => setPageSize(Number(value))}
            >
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="20">20</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-64 w-full" />
            </div>
          ) : !loading && clicks.length === 0 ? (
            <EmptyState />
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead 
                        className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 w-20"
                        onClick={() => handleSort('id')}
                      >
                        ID
                        {sortConfig?.key === 'id' && (
                          <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </TableHead>
                      <TableHead 
                        className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                        onClick={() => handleSort('timestamp')}
                      >
                        Timestamp
                        {sortConfig?.key === 'timestamp' && (
                          <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </TableHead>
                      <TableHead 
                        className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                        onClick={() => handleSort('country')}
                      >
                        Country
                        {sortConfig?.key === 'country' && (
                          <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </TableHead>
                      <TableHead 
                        className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                        onClick={() => handleSort('device')}
                      >
                        Device
                        {sortConfig?.key === 'device' && (
                          <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </TableHead>
                      <TableHead 
                        className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                        onClick={() => handleSort('status')}
                      >
                        Status
                        {sortConfig?.key === 'status' && (
                          <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </TableHead>
                      <TableHead 
                        className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                        onClick={() => handleSort('risk')}
                      >
                        Risk
                        {sortConfig?.key === 'risk' && (
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
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedData.map((click) => (
                      <TableRow key={click.id}>
                        <TableCell className="font-medium">{click.id}</TableCell>
                        <TableCell>{format(new Date(click.timestamp), 'PPpp')}</TableCell>
                        <TableCell>
                          <span className="flex items-center">
                            <span className={`fi fi-${click.country.toLowerCase()} mr-2`}></span>
                            {click.country}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="flex items-center">
                            {click.device.toLowerCase() === 'mobile' && '📱'}
                            {click.device.toLowerCase() === 'desktop' && '💻'}
                            {click.device.toLowerCase() === 'tablet' && '📱'}
                            <span className="ml-2">{click.device.charAt(0).toUpperCase() + click.device.slice(1)}</span>
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusBadgeVariant(click.status)}>
                            {click.status.charAt(0).toUpperCase() + click.status.slice(1)}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getRiskBadgeVariant(click.risk || 0)}>
                            {click.risk || 0}%
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          ${click.revenue.toFixed(2)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              
              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, filteredData.length)} of {filteredData.length} results
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </Button>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let pageNum;
                        if (totalPages <= 5) {
                          pageNum = i + 1;
                        } else if (currentPage <= 3) {
                          pageNum = i + 1;
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + i;
                        } else {
                          pageNum = currentPage - 2 + i;
                        }
                        return (
                          <Button
                            key={pageNum}
                            variant={currentPage === pageNum ? "default" : "outline"}
                            size="sm"
                            onClick={() => setCurrentPage(pageNum)}
                          >
                            {pageNum}
                          </Button>
                        );
                      })}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
