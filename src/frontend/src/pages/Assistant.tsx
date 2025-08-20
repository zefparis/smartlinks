import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  SparklesIcon, 
  CpuChipIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import IASupervisorWidget from '@/components/ia-supervisor/IASupervisorWidgetV2';

// Composant de la page de l'assistant IA moderne
export default function AssistantPage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simuler un temps de chargement
    const timer = setTimeout(() => setIsLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="h-16 w-16 animate-spin rounded-full border-4 border-gradient-to-r from-blue-500 to-purple-600 border-t-transparent mx-auto"></div>
            <SparklesIcon className="h-8 w-8 text-blue-500 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
          </div>
          <p className="mt-4 text-lg font-medium text-gray-600 dark:text-gray-300">
            Initialisation de l'Assistant IA...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header moderne */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button
              onClick={() => navigate(-1)}
              className="mr-4 flex items-center px-3 py-2 rounded-lg text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:text-indigo-300 dark:hover:bg-indigo-900/20 transition-all duration-200"
            >
              <ArrowLeftIcon className="mr-2 h-5 w-5" />
              Retour
            </button>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-4">
              <div className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl shadow-lg">
                <SparklesIcon className="h-8 w-8 text-white" />
              </div>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
              Assistant IA SmartLinks
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Votre assistant intelligent pour l'optimisation, l'analyse et la gestion autonome de votre système
            </p>
          </div>
        </div>

        {/* Statistiques rapides */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <button
            onClick={() => navigate('/ia/status')}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg hover:scale-105 transition-all duration-200 text-left"
          >
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <CheckCircleIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Statut IA</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">En ligne</p>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => navigate('/ia/algorithms')}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg hover:scale-105 transition-all duration-200 text-left"
          >
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <CpuChipIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Algorithmes</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">10 actifs</p>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => navigate('/ia/model')}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg hover:scale-105 transition-all duration-200 text-left"
          >
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                <ChartBarIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Modèle IA</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">GPT-4o</p>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => navigate('/ia/analysis')}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg hover:scale-105 transition-all duration-200 text-left"
          >
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
                <ClockIcon className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Dernière analyse</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">Maintenant</p>
              </div>
            </div>
          </button>
        </div>

        {/* Widget IA principal */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <IASupervisorWidget />
        </div>
        
        {/* Fonctionnalités disponibles */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="text-center">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-xl w-fit mx-auto mb-4">
                <ChartBarIcon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Analyse Système
              </h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                Analyse complète des performances et détection d'anomalies en temps réel
              </p>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="text-center">
              <div className="p-3 bg-green-100 dark:bg-green-900/20 rounded-xl w-fit mx-auto mb-4">
                <CheckCircleIcon className="h-8 w-8 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Auto-Correction
              </h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                Résolution automatique des problèmes détectés avec validation intelligente
              </p>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="text-center">
              <div className="p-3 bg-purple-100 dark:bg-purple-900/20 rounded-xl w-fit mx-auto mb-4">
                <SparklesIcon className="h-8 w-8 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Optimisation IA
              </h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                Recommandations intelligentes pour améliorer les performances du système
              </p>
            </div>
          </div>
        </div>
        
        <div className="mt-8 text-center">
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            🚀 Assistant IA alimenté par GPT-4o • Algorithmes autonomes • Analyse en temps réel
          </p>
        </div>
      </div>
    </div>
  );
}
