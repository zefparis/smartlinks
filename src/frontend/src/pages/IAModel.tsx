import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  SparklesIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  ClockIcon,
  CpuChipIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface ModelConfig {
  name: string;
  version: string;
  status: 'active' | 'inactive' | 'error';
  temperature: number;
  maxTokens: number;
  timeout: number;
  apiCalls: number;
  successRate: number;
  avgResponseTime: number;
}

export default function IAModelPage() {
  const navigate = useNavigate();
  const [config, setConfig] = useState<ModelConfig>({
    name: 'GPT-4o',
    version: '2024-08-06',
    status: 'active',
    temperature: 0.7,
    maxTokens: 1000,
    timeout: 30,
    apiCalls: 1247,
    successRate: 98.5,
    avgResponseTime: 2.3
  });

  const [isEditing, setIsEditing] = useState(false);
  const [tempConfig, setTempConfig] = useState(config);

  const handleSave = () => {
    setConfig(tempConfig);
    setIsEditing(false);
    // TODO: Save to backend
  };

  const handleCancel = () => {
    setTempConfig(config);
    setIsEditing(false);
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
              <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-600 rounded-2xl shadow-lg">
                <SparklesIcon className="h-8 w-8 text-white" />
              </div>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
              Configuration Modèle IA
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Gérez les paramètres et performances de votre modèle d'intelligence artificielle
            </p>
          </div>
        </div>

        {/* Model Status */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <SparklesIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Modèle</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">{config.name}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <ChartBarIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Taux de succès</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">{config.successRate}%</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                <CpuChipIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Appels API</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">{config.apiCalls.toLocaleString()}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
                <ClockIcon className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Temps moyen</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">{config.avgResponseTime}s</p>
              </div>
            </div>
          </div>
        </div>

        {/* Configuration Panel */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Paramètres du Modèle
            </h2>
            <div className="flex space-x-2">
              {isEditing ? (
                <>
                  <button
                    onClick={handleCancel}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 rounded-lg transition-colors"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={handleSave}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                  >
                    Sauvegarder
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400 dark:hover:bg-blue-900/40 rounded-lg transition-colors flex items-center"
                >
                  <Cog6ToothIcon className="h-4 w-4 mr-2" />
                  Modifier
                </button>
              )}
            </div>
          </div>
          
          <div className="p-6 space-y-6">
            {/* Model Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Nom du Modèle
                </label>
                <input
                  type="text"
                  value={isEditing ? tempConfig.name : config.name}
                  onChange={(e) => isEditing && setTempConfig({...tempConfig, name: e.target.value})}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:bg-gray-50 dark:disabled:bg-gray-800 disabled:text-gray-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Version
                </label>
                <input
                  type="text"
                  value={isEditing ? tempConfig.version : config.version}
                  onChange={(e) => isEditing && setTempConfig({...tempConfig, version: e.target.value})}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:bg-gray-50 dark:disabled:bg-gray-800 disabled:text-gray-500"
                />
              </div>
            </div>

            {/* Parameters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Température ({isEditing ? tempConfig.temperature : config.temperature})
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={isEditing ? tempConfig.temperature : config.temperature}
                  onChange={(e) => isEditing && setTempConfig({...tempConfig, temperature: parseFloat(e.target.value)})}
                  disabled={!isEditing}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Précis (0)</span>
                  <span>Créatif (2)</span>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Tokens Maximum
                </label>
                <input
                  type="number"
                  value={isEditing ? tempConfig.maxTokens : config.maxTokens}
                  onChange={(e) => isEditing && setTempConfig({...tempConfig, maxTokens: parseInt(e.target.value)})}
                  disabled={!isEditing}
                  min="100"
                  max="4000"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:bg-gray-50 dark:disabled:bg-gray-800 disabled:text-gray-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Timeout (secondes)
                </label>
                <input
                  type="number"
                  value={isEditing ? tempConfig.timeout : config.timeout}
                  onChange={(e) => isEditing && setTempConfig({...tempConfig, timeout: parseInt(e.target.value)})}
                  disabled={!isEditing}
                  min="5"
                  max="120"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:bg-gray-50 dark:disabled:bg-gray-800 disabled:text-gray-500"
                />
              </div>
            </div>

            {/* Status Indicator */}
            <div className="flex items-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex-shrink-0">
                <SparklesIcon className="h-5 w-5 text-green-400" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800 dark:text-green-400">
                  Modèle IA opérationnel
                </p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Le modèle {config.name} fonctionne correctement avec un taux de succès de {config.successRate}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Métriques de Performance
            </h2>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                  {config.apiCalls.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Requêtes traitées aujourd'hui
                </div>
              </div>
              
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 dark:text-green-400 mb-2">
                  {config.successRate}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Taux de succès global
                </div>
              </div>
              
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                  {config.avgResponseTime}s
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Temps de réponse moyen
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
