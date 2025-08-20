import { Switch } from '@headlessui/react';
import { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';

interface HealthCardProps {
  title: string;
  isActive: boolean;
  onToggle: (next: boolean) => Promise<void>; // ⬅️ aligne l'API
  icon: React.ElementType;
  className?: string;
  description?: string;
  loading?: boolean;
}

export default function HealthCard({
  title,
  isActive,
  onToggle,
  icon: Icon,
  className = '',
  description = '',
  loading = false,
}: HealthCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [localStatus, setLocalStatus] = useState<boolean>(!!isActive);
  const lastStableRef = useRef<boolean>(!!isActive); // pour revert exact

  useEffect(() => {
    setLocalStatus(isActive);
    lastStableRef.current = isActive;
  }, [isActive]);

  const handleToggle = async (nextChecked: boolean) => {
    if (loading || isLoading) return;
    setIsLoading(true);

    // optimistic update → à partir de la valeur passée par Switch
    setLocalStatus(nextChecked);

    try {
      await onToggle(nextChecked); // le parent sait quoi faire (start/stop)
      lastStableRef.current = nextChecked; // on valide le nouvel état stable
    } catch (error) {
      console.error(`Failed to toggle ${title}:`, error);
      toast.error(`Failed to toggle ${title}`);
      // revert strict sur le dernier état stable connu
      setLocalStatus(lastStableRef.current);
    } finally {
      setIsLoading(false);
    }
  };

  const isActuallyLoading = loading || isLoading;
  const bgColor = localStatus ? 'bg-green-100' : 'bg-red-100';
  const textColor = localStatus ? 'text-green-600' : 'text-red-600';
  const switchBgColor = localStatus ? 'bg-green-600' : 'bg-gray-200';
  const focusRingColor = localStatus ? 'focus:ring-green-500' : 'focus:ring-red-500';

  return (
    <div className={`overflow-hidden bg-white dark:bg-gray-800 rounded-lg shadow ring-1 ring-gray-200 dark:ring-gray-600 ${className}`}>
      <div className="p-5">
        <div className="flex items-center">
          <div className={`flex items-center justify-center w-12 h-12 rounded-md ${bgColor} ${isActuallyLoading ? 'opacity-50' : ''}`}>
            {isActuallyLoading ? (
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 dark:border-gray-300" />
            ) : (
              <Icon className={`w-6 h-6 ${textColor}`} aria-hidden="true" />
            )}
          </div>

          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-300 truncate">{title}</dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                  {localStatus ? 'Active' : 'Inactive'}
                </div>
                {description && (
                  <span className="ml-2 text-sm text-gray-500 dark:text-gray-300">
                    {description}
                  </span>
                )}
              </dd>
            </dl>
          </div>

          <div className="ml-5 flex-shrink-0">
            <Switch
              checked={!!localStatus}
              onChange={handleToggle}            // ⬅️ reçoit (next:boolean)
              disabled={isActuallyLoading}
              className={`${switchBgColor} relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 ${focusRingColor} focus:ring-offset-2 ${isActuallyLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span className="sr-only">Toggle {title}</span>
              <span
                aria-hidden="true"
                className={`${localStatus ? 'translate-x-5' : 'translate-x-0'} pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
              />
            </Switch>
          </div>
        </div>
      </div>
    </div>
  );
}
