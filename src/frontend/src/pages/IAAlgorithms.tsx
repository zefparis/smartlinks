import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  CpuChipIcon,
  PlayIcon,
  PauseIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { SettingsModal } from '@/components/autopilot/SettingsModal';
import autopilotAPI, { Algorithm as APIAlgorithm } from '@/api/autopilot';

interface Algorithm {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'error';
  description: string;
  lastRun?: string;
  performance?: number;
  category: string;
}

export default function IAAlgorithms() {
  const navigate = useNavigate();
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<Algorithm | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [algorithms, setAlgorithms] = useState<Algorithm[]>([
    {
      id: 'traffic_optimizer',
      name: 'Traffic Optimizer',
      status: 'active',
      description: 'Optimise automatiquement le trafic et les conversions',
      lastRun: '2025-01-20T01:30:00Z',
      performance: 95,
      category: 'Optimisation'
    },
    {
      id: 'anomaly_detector',
      name: 'Anomaly Detector',
      status: 'active',
      description: 'Détecte les anomalies dans les métriques système',
      lastRun: '2025-01-20T01:25:00Z',
      performance: 88,
      category: 'Surveillance'
    },
    {
      id: 'budget_arbitrage',
      name: 'Budget Arbitrage',
      status: 'active',
      description: 'Gère automatiquement la répartition du budget',
      lastRun: '2025-01-20T01:20:00Z',
      performance: 92,
      category: 'Finance'
    },
    {
      id: 'predictive_alerting',
      name: 'Predictive Alerting',
      status: 'active',
      description: 'Prédictions et alertes intelligentes',
      lastRun: '2025-01-20T01:15:00Z',
      performance: 87,
      category: 'Prédiction'
    },
    {
      id: 'self_healing',
      name: 'Self Healing',
      status: 'error',
      description: 'Auto-réparation des problèmes système',
      lastRun: '2025-01-20T00:45:00Z',
      performance: 0,
      category: 'Maintenance'
    }
  ]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'inactive':
        return <PauseIcon className="h-5 w-5 text-yellow-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <CpuChipIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'inactive':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const toggleAlgorithm = (id: string) => {
    setAlgorithms(prev => prev.map(algo => 
      algo.id === id 
        ? { ...algo, status: algo.status === 'active' ? 'inactive' : 'active' }
        : algo
    ));
  };

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
              <div className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl shadow-lg">
                <CpuChipIcon className="h-8 w-8 text-white" />
              </div>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
              Gestion des Algorithmes IA
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Contrôlez et configurez les algorithmes autonomes qui gèrent votre système SmartLinks
            </p>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <CheckCircleIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Actifs</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {algorithms.filter(a => a.status === 'active').length}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg">
                <PauseIcon className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Inactifs</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {algorithms.filter(a => a.status === 'inactive').length}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-lg">
                <ExclamationTriangleIcon className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Erreurs</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {algorithms.filter(a => a.status === 'error').length}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <ChartBarIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Performance Moy.</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {Math.round(algorithms.reduce((acc, a) => acc + (a.performance || 0), 0) / algorithms.length)}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Algorithms List */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Algorithmes Disponibles
            </h2>
          </div>
          
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {algorithms.map((algorithm) => (
              <div key={algorithm.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                      <CpuChipIcon className="h-6 w-6 text-gray-600 dark:text-gray-400" />
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                          {algorithm.name}
                        </h3>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(algorithm.status)}`}>
                          {getStatusIcon(algorithm.status)}
                          <span className="ml-1 capitalize">{algorithm.status}</span>
                        </span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                          {algorithm.category}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {algorithm.description}
                      </p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                        {algorithm.lastRun && (
                          <span>
                            Dernière exécution: {new Date(algorithm.lastRun).toLocaleString()}
                          </span>
                        )}
                        {algorithm.performance !== undefined && (
                          <span>
                            Performance: {algorithm.performance}%
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleAlgorithm(algorithm.id)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                        algorithm.status === 'active'
                          ? 'bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/20 dark:text-red-400'
                          : 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/20 dark:text-green-400'
                      }`}
                    >
                      {algorithm.status === 'active' ? (
                        <>
                          <PauseIcon className="h-4 w-4 inline mr-1" />
                          Arrêter
                        </>
                      ) : (
                        <>
                          <PlayIcon className="h-4 w-4 inline mr-1" />
                          Démarrer
                        </>
                      )}
                    </button>
                    
                    <button 
                      onClick={() => {
                        setSelectedAlgorithm(algorithm);
                        setIsSettingsOpen(true);
                      }}
                      className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                    >
                      <Cog6ToothIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Settings Modal */}
      {selectedAlgorithm && (
        <SettingsModal
          algorithm={{
            id: selectedAlgorithm.id,
            name: selectedAlgorithm.name,
            description: selectedAlgorithm.description,
            status: selectedAlgorithm.status,
            last_run: selectedAlgorithm.lastRun || '',
            performance: { actions_taken: 0, improvement: `${selectedAlgorithm.performance}%` }
          }}
          isOpen={isSettingsOpen}
          onClose={() => {
            setIsSettingsOpen(false);
            setSelectedAlgorithm(null);
          }}
        />
      )}
    </div>
  );
}
