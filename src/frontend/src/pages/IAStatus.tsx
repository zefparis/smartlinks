import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CpuChipIcon,
  ServerIcon,
  WifiIcon,
  BoltIcon
} from '@heroicons/react/24/outline';

interface SystemStatus {
  component: string;
  status: 'online' | 'offline' | 'warning' | 'error';
  uptime: string;
  lastCheck: string;
  details: string;
}

export default function IAStatusPage() {
  const navigate = useNavigate();
  const [systemStatus, setSystemStatus] = useState<SystemStatus[]>([
    {
      component: 'IA Supervisor',
      status: 'online',
      uptime: '99.9%',
      lastCheck: '2025-01-20T01:30:00Z',
      details: 'Fonctionnel avec 10 algorithmes actifs'
    },
    {
      component: 'OpenAI GPT-4o',
      status: 'online',
      uptime: '98.5%',
      lastCheck: '2025-01-20T01:29:45Z',
      details: 'Connecté et opérationnel'
    },
    {
      component: 'Base de données',
      status: 'online',
      uptime: '100%',
      lastCheck: '2025-01-20T01:30:15Z',
      details: 'SQLite - Performances optimales'
    },
    {
      component: 'API Backend',
      status: 'online',
      uptime: '99.8%',
      lastCheck: '2025-01-20T01:30:20Z',
      details: 'FastAPI sur port 8000'
    },
    {
      component: 'Frontend React',
      status: 'online',
      uptime: '100%',
      lastCheck: '2025-01-20T01:30:25Z',
      details: 'Vite dev server sur port 5173'
    },
    {
      component: 'Algorithmes Auto',
      status: 'warning',
      uptime: '95.2%',
      lastCheck: '2025-01-20T01:25:00Z',
      details: '9/10 algorithmes actifs - Self Healing en erreur'
    }
  ]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'offline':
        return <ServerIcon className="h-5 w-5 text-gray-500" />;
      default:
        return <CpuChipIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      case 'offline':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const overallStatus = systemStatus.every(s => s.status === 'online') ? 'optimal' : 
                       systemStatus.some(s => s.status === 'error' || s.status === 'offline') ? 'critical' : 'warning';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button
              onClick={() => navigate('/assistant')}
              className="mr-4 flex items-center px-3 py-2 rounded-lg text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:text-indigo-300 dark:hover:bg-indigo-900/20 transition-all duration-200"
            >
              <ArrowLeftIcon className="mr-2 h-5 w-5" />
              Retour à l'Assistant
            </button>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-4">
              <div className={`p-3 rounded-2xl shadow-lg ${
                overallStatus === 'optimal' ? 'bg-gradient-to-r from-green-500 to-blue-600' :
                overallStatus === 'warning' ? 'bg-gradient-to-r from-yellow-500 to-orange-600' :
                'bg-gradient-to-r from-red-500 to-pink-600'
              }`}>
                <ServerIcon className="h-8 w-8 text-white" />
              </div>
            </div>
            <h1 className={`text-4xl font-bold bg-clip-text text-transparent mb-2 ${
              overallStatus === 'optimal' ? 'bg-gradient-to-r from-green-600 to-blue-600' :
              overallStatus === 'warning' ? 'bg-gradient-to-r from-yellow-600 to-orange-600' :
              'bg-gradient-to-r from-red-600 to-pink-600'
            }`}>
              Statut Système IA
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Surveillance en temps réel de tous les composants de votre système SmartLinks
            </p>
          </div>
        </div>

        {/* Overall Status */}
        <div className={`mb-8 p-6 rounded-2xl shadow-lg ${
          overallStatus === 'optimal' ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' :
          overallStatus === 'warning' ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800' :
          'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`p-3 rounded-xl ${
                overallStatus === 'optimal' ? 'bg-green-100 dark:bg-green-900/40' :
                overallStatus === 'warning' ? 'bg-yellow-100 dark:bg-yellow-900/40' :
                'bg-red-100 dark:bg-red-900/40'
              }`}>
                {overallStatus === 'optimal' ? (
                  <CheckCircleIcon className="h-8 w-8 text-green-600 dark:text-green-400" />
                ) : overallStatus === 'warning' ? (
                  <ExclamationTriangleIcon className="h-8 w-8 text-yellow-600 dark:text-yellow-400" />
                ) : (
                  <ExclamationTriangleIcon className="h-8 w-8 text-red-600 dark:text-red-400" />
                )}
              </div>
              <div>
                <h2 className={`text-2xl font-bold ${
                  overallStatus === 'optimal' ? 'text-green-800 dark:text-green-300' :
                  overallStatus === 'warning' ? 'text-yellow-800 dark:text-yellow-300' :
                  'text-red-800 dark:text-red-300'
                }`}>
                  Système {overallStatus === 'optimal' ? 'Optimal' : overallStatus === 'warning' ? 'Attention' : 'Critique'}
                </h2>
                <p className={`${
                  overallStatus === 'optimal' ? 'text-green-700 dark:text-green-400' :
                  overallStatus === 'warning' ? 'text-yellow-700 dark:text-yellow-400' :
                  'text-red-700 dark:text-red-400'
                }`}>
                  {overallStatus === 'optimal' ? 'Tous les composants fonctionnent correctement' :
                   overallStatus === 'warning' ? 'Certains composants nécessitent attention' :
                   'Des composants critiques sont en panne'}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className={`text-3xl font-bold ${
                overallStatus === 'optimal' ? 'text-green-600 dark:text-green-400' :
                overallStatus === 'warning' ? 'text-yellow-600 dark:text-yellow-400' :
                'text-red-600 dark:text-red-400'
              }`}>
                {systemStatus.filter(s => s.status === 'online').length}/{systemStatus.length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Composants actifs</div>
            </div>
          </div>
        </div>

        {/* System Components */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Composants Système
            </h2>
          </div>
          
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {systemStatus.map((component, index) => (
              <div key={index} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                      {component.component.includes('IA') ? (
                        <BoltIcon className="h-6 w-6 text-gray-600 dark:text-gray-400" />
                      ) : component.component.includes('API') ? (
                        <ServerIcon className="h-6 w-6 text-gray-600 dark:text-gray-400" />
                      ) : component.component.includes('Frontend') ? (
                        <WifiIcon className="h-6 w-6 text-gray-600 dark:text-gray-400" />
                      ) : (
                        <CpuChipIcon className="h-6 w-6 text-gray-600 dark:text-gray-400" />
                      )}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                          {component.component}
                        </h3>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(component.status)}`}>
                          {getStatusIcon(component.status)}
                          <span className="ml-1 capitalize">{component.status}</span>
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {component.details}
                      </p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                        <span>
                          Uptime: {component.uptime}
                        </span>
                        <span>
                          Dernière vérification: {new Date(component.lastCheck).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      component.status === 'online' ? 'bg-green-400' :
                      component.status === 'warning' ? 'bg-yellow-400' :
                      component.status === 'error' ? 'bg-red-400' : 'bg-gray-400'
                    } ${component.status === 'online' ? 'animate-pulse' : ''}`}></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <button
            onClick={() => navigate('/ia/algorithms')}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-all duration-200 text-left"
          >
            <div className="flex items-center space-x-3">
              <CpuChipIcon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Gérer les Algorithmes</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Configurer les algorithmes IA</p>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => navigate('/ia/model')}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-all duration-200 text-left"
          >
            <div className="flex items-center space-x-3">
              <BoltIcon className="h-8 w-8 text-purple-600 dark:text-purple-400" />
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Configuration Modèle</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Paramètres GPT-4o</p>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => navigate('/ia/analysis')}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-all duration-200 text-left"
          >
            <div className="flex items-center space-x-3">
              <ClockIcon className="h-8 w-8 text-green-600 dark:text-green-400" />
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Analyses Système</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Rapports détaillés</p>
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
