import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from '@heroicons/react/20/solid';

type Trend = 'up' | 'down' | 'neutral';

type MetricCardProps = {
  title: string;
  value: string | number;
  icon: React.ElementType;
  trend: Trend;
  change: string;
  iconColor: string;
  bgColor: string;
};

export default function MetricCard({
  title,
  value,
  icon: Icon,
  trend,
  change,
  iconColor,
  bgColor,
}: MetricCardProps) {
  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-600';
    if (trend === 'down') return 'text-red-600';
    return 'text-gray-500';
  };

  const getTrendIcon = () => {
    if (trend === 'up') return <ArrowUpIcon className="w-4 h-4 text-green-500" />;
    if (trend === 'down') return <ArrowDownIcon className="w-4 h-4 text-red-500" />;
    return <MinusIcon className="w-4 h-4 text-gray-500" />;
  };

  return (
    <div className="overflow-hidden bg-white dark:bg-gray-800 rounded-lg shadow ring-1 ring-gray-200 dark:ring-gray-600">
      <div className="p-5">
        <div className="flex items-center">
          <div className={`p-3 rounded-md ${bgColor}`}>
            <Icon className={`w-6 h-6 ${iconColor}`} aria-hidden="true" />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-300 truncate">{title}</dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{value}</div>
                <div className={`ml-2 flex items-center text-sm font-semibold ${getTrendColor()}`}>
                  {getTrendIcon()}
                  <span className="sr-only">
                    {trend === 'up' ? 'Increased' : trend === 'down' ? 'Decreased' : 'No change'} by
                  </span>
                  {change}
                </div>
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}
