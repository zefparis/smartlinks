import { Chart } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
  ChartOptions,
} from 'chart.js';
import { useEffect, useMemo, useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

type TrafficData = {
  segment: string | null | undefined;
  count: number;
  avg_risk: number; // accepte 0..1 ou 0..100
}[];

export default function TrafficChart({ data }: { data: TrafficData }) {
  const { theme } = useTheme();

  // On type le state en 'bar' pour matcher <Chart type="bar">,
  // et on cast lors du render pour supporter le dataset 'line'.
  const [chartData, setChartData] = useState<ChartData<'bar' | 'line'>>({
    labels: [],
    datasets: [],
  });

  useEffect(() => {
    if (!Array.isArray(data) || data.length === 0) {
      // reset pour éviter l'affichage d'anciens points
      setChartData({ labels: [], datasets: [] });
      return;
    }

    // tri par count décroissant
    const topSegments = [...data].sort((a, b) => b.count - a.count).slice(0, 5);

    const labels = topSegments.map((item) => {
      const seg = (item.segment || '').toString();
      const [country = '', device = ''] = seg.split(':');
      const devLabel = device ? device.charAt(0).toUpperCase() + device.slice(1) : '';
      return `${country.toUpperCase()} ${devLabel}`.trim();
    });

    const counts = topSegments.map((item) => Number(item.count) || 0);

    // normalisation risk: si >1, on assume 0..100 → /100
    const riskScores01 = topSegments.map((item) => {
      const v = Number(item.avg_risk) || 0;
      return v > 1 ? v / 100 : v; // bornage en [0,1]
    });

    setChartData({
      labels,
      datasets: [
        {
          type: 'bar',
          label: 'Clicks',
          data: counts,
          backgroundColor: 'rgba(79, 70, 229, 0.8)',
          borderColor: 'rgba(79, 70, 229, 1)',
          borderWidth: 1,
          yAxisID: 'y',
          barPercentage: 0.7,
          categoryPercentage: 0.8,
        } as const,
        {
          type: 'line',
          label: 'Avg. Risk Score',
          data: riskScores01,
          backgroundColor: 'rgba(220, 38, 38, 0.8)',
          borderColor: 'rgba(220, 38, 38, 1)',
          borderWidth: 2,
          yAxisID: 'y1',
          tension: 0.3,
          pointRadius: 4,
          pointHoverRadius: 6,
        } as const,
      ],
    });
  }, [data]);

  const options = useMemo<ChartOptions<'bar' | 'line'>>(() => {
    const isDark = theme === 'dark';
    const axisColor = isDark ? 'rgba(229, 231, 235, 0.8)' : 'rgba(17, 24, 39, 0.8)';
    const gridColor = isDark ? 'rgba(55, 65, 81, 0.4)' : 'rgba(229, 231, 235, 0.7)';
    const titleColor = isDark ? '#e5e7eb' : '#111827';

    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: {
          grid: { display: false },
          ticks: { maxRotation: 45, minRotation: 45, color: axisColor },
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: { display: true, text: 'Number of Clicks', color: titleColor },
          grid: { drawOnChartArea: true, color: gridColor },
          ticks: { color: axisColor },
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: { display: true, text: 'Avg. Risk Score', color: titleColor },
          grid: { drawOnChartArea: false, color: gridColor },
          min: 0,
          max: 1, // on bosse en 0..1 après normalisation
          ticks: {
            stepSize: 0.2,
            callback: (v) => {
              const n = typeof v === 'string' ? Number(v) : Number(v);
              return Number.isFinite(n) ? n.toFixed(1) : v;
            },
            color: axisColor,
          },
        },
      },
      plugins: {
        legend: { position: 'top', labels: { color: axisColor } },
        tooltip: {
          titleColor: titleColor,
          bodyColor: axisColor,
          callbacks: {
            label: (ctx) => {
              const label = ctx.dataset.label || '';
              const raw = Number(ctx.raw);
              if (label === 'Avg. Risk Score') {
                return `${label}: ${Number.isFinite(raw) ? raw.toFixed(2) : ctx.raw}`;
              }
              return `${label}: ${Number.isFinite(raw) ? raw.toLocaleString() : ctx.raw}`;
            },
          },
        },
      },
    };
  }, [theme]);

  return (
    <div className="w-full h-full">
      {Array.isArray(data) && data.length > 0 ? (
        // cast pour matcher le generic 'bar' du composant Chart tout en gardant le mixed dataset
        <Chart type="bar" data={chartData as unknown as ChartData<'bar'>} options={options} />
      ) : (
        <div className="flex items-center justify-center h-full text-gray-500">No data available</div>
      )}
    </div>
  );
}
