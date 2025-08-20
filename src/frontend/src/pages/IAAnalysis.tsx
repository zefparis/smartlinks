import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  CpuChipIcon,
  EyeIcon,
  PlayIcon
} from '@heroicons/react/24/outline';

interface AnalysisResult {
  id: string;
  timestamp: string;
  type: 'performance' | 'security' | 'optimization' | 'anomaly';
  status: 'completed' | 'running' | 'failed';
  score: number;
  title: string;
  description: string;
  recommendations: string[];
  metrics: {
    cpu: number;
    memory: number;
    traffic: number;
    errors: number;
  };
}

export default function IAAnalysisPage() {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([
    {
      id: '1',
      timestamp: '2025-01-20T01:30:00Z',
      type: 'performance',
      status: 'completed',
      score: 92,
      title: 'Analyse de Performance Système',
      description: 'Évaluation complète des performances du système SmartLinks',
      recommendations: [
        'Optimiser les requêtes de base de données',
        'Augmenter le cache Redis',
        'Réduire la latence des API externes'
      ],
      metrics: { cpu: 45, memory: 67, traffic: 89, errors: 2 }
    },
    {
      id: '2',
      timestamp: '2025-01-20T01:15:00Z',
      type: 'anomaly',
      status: 'completed',
      score: 78,
      title: 'Détection d\'Anomalies',
      description: 'Identification des comportements anormaux dans le trafic',
      recommendations: [
        'Surveiller les pics de trafic inhabituels',
        'Vérifier les sources de trafic suspectes',
        'Renforcer la sécurité des endpoints'
      ],
      metrics: { cpu: 32, memory: 54, traffic: 156, errors: 8 }
    },
    {
      id: '3',
      timestamp: '2025-01-20T01:00:00Z',
      type: 'optimization',
      status: 'running',
      score: 0,
      title: 'Optimisation Automatique',
      description: 'Optimisation en cours des algorithmes de conversion',
      recommendations: [],
      metrics: { cpu: 78, memory: 45, traffic: 67, errors: 1 }
    }
  ]);

  const [isRunningAnalysis, setIsRunningAnalysis] = useState(false);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'performance':
        return <ChartBarIcon className="h-5 w-5" />;
      case 'security':
        return <ExclamationTriangleIcon className="h-5 w-5" />;
      case 'optimization':
        return <CpuChipIcon className="h-5 w-5" />;
      case 'anomaly':
        return <EyeIcon className="h-5 w-5" />;
      default:
        return <ChartBarIcon className="h-5 w-5" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'performance':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'security':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      case 'optimization':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'anomaly':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 dark:text-green-400';
      case 'running':
        return 'text-blue-600 dark:text-blue-400';
      case 'failed':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const runNewAnalysis = async () => {
    setIsRunningAnalysis(true);
    // Simulate analysis
    setTimeout(() => {
      const newAnalysis: AnalysisResult = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        type: 'performance',
        status: 'completed',
        score: Math.floor(Math.random() * 20) + 80,
        title: 'Nouvelle Analyse Système',
        description: 'Analyse complète du système effectuée',
        recommendations: [
          'Système fonctionnel',
          'Performances optimales',
          'Aucune action requise'
        ],
        metrics: {
          cpu: Math.floor(Math.random() * 50) + 30,
          memory: Math.floor(Math.random() * 40) + 40,
          traffic: Math.floor(Math.random() * 100) + 50,
          errors: Math.floor(Math.random() * 5)
        }
      };
      setAnalyses(prev => [newAnalysis, ...prev]);
      setIsRunningAnalysis(false);
    }, 3000);
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
              <div className="p-3 bg-gradient-to-r from-green-500 to-blue-600 rounded-2xl shadow-lg">
                <ChartBarIcon className="h-8 w-8 text-white" />
              </div>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent mb-2">
              Analyse Système IA
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Analyses approfondies et recommandations intelligentes pour optimiser votre système
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-8 flex justify-center">
          <button
            onClick={runNewAnalysis}
            disabled={isRunningAnalysis}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
          >
            {isRunningAnalysis ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                <span>Analyse en cours...</span>
              </>
            ) : (
              <>
                <PlayIcon className="h-5 w-5" />
                <span>Lancer une nouvelle analyse</span>
              </>
            )}
          </button>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <CheckCircleIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Analyses Complétées</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {analyses.filter(a => a.status === 'completed').length}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <ClockIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">En Cours</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {analyses.filter(a => a.status === 'running').length}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                <ChartBarIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Score Moyen</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {Math.round(analyses.filter(a => a.score > 0).reduce((acc, a) => acc + a.score, 0) / analyses.filter(a => a.score > 0).length) || 0}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
                <ExclamationTriangleIcon className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Recommandations</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {analyses.reduce((acc, a) => acc + a.recommendations.length, 0)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Analysis Results */}
        <div className="space-y-6">
          {analyses.map((analysis) => (
            <div key={analysis.id} className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${getTypeColor(analysis.type)}`}>
                      {getTypeIcon(analysis.type)}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {analysis.title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {new Date(analysis.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    {analysis.score > 0 && (
                      <div className="text-right">
                        <div className="text-2xl font-bold text-gray-900 dark:text-white">
                          {analysis.score}
                        </div>
                        <div className="text-xs text-gray-500">Score</div>
                      </div>
                    )}
                    <span className={`font-medium ${getStatusColor(analysis.status)} capitalize`}>
                      {analysis.status === 'running' && (
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent inline-block mr-2"></div>
                      )}
                      {analysis.status}
                    </span>
                  </div>
                </div>
                
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  {analysis.description}
                </p>
                
                {/* Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="text-lg font-semibold text-gray-900 dark:text-white">
                      {analysis.metrics.cpu}%
                    </div>
                    <div className="text-xs text-gray-500">CPU</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="text-lg font-semibold text-gray-900 dark:text-white">
                      {analysis.metrics.memory}%
                    </div>
                    <div className="text-xs text-gray-500">Mémoire</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="text-lg font-semibold text-gray-900 dark:text-white">
                      {analysis.metrics.traffic}
                    </div>
                    <div className="text-xs text-gray-500">Trafic</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="text-lg font-semibold text-gray-900 dark:text-white">
                      {analysis.metrics.errors}
                    </div>
                    <div className="text-xs text-gray-500">Erreurs</div>
                  </div>
                </div>
                
                {/* Recommendations */}
                {analysis.recommendations.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                      Recommandations:
                    </h4>
                    <ul className="space-y-2">
                      {analysis.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm text-gray-600 dark:text-gray-400">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
