"use client";

import { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Radar } from "react-chartjs-2";

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

// 模拟数据
const mockData = {
  labels: ["威胁识别", "风险评估", "缓解措施", "安全考虑", "完整性"],
  datasets: [
    {
      label: "GPT-4",
      data: [90, 85, 88, 89, 85],
      backgroundColor: "rgba(106, 216, 196, 0.2)",
      borderColor: "rgba(106, 216, 196, 1)",
      borderWidth: 1,
    },
    {
      label: "Claude 3",
      data: [86, 89, 82, 87, 84],
      backgroundColor: "rgba(255, 137, 150, 0.2)",
      borderColor: "rgba(255, 137, 150, 1)",
      borderWidth: 1,
    },
    {
      label: "Gemini",
      data: [82, 79, 81, 78, 80],
      backgroundColor: "rgba(157, 108, 207, 0.2)",
      borderColor: "rgba(157, 108, 207, 1)",
      borderWidth: 1,
    },
  ],
};

const options = {
  responsive: true,
  plugins: {
    legend: {
      position: "top" as const,
    },
    title: {
      display: true,
      text: "详细性能指标",
    },
    tooltip: {
      callbacks: {
        label: function(context: any) {
          return `${context.dataset.label}: ${context.raw}`;
        }
      }
    }
  },
  scales: {
    r: {
      beginAtZero: true,
      max: 100,
      ticks: {
        stepSize: 20,
      },
    },
  },
};

export default function PerformanceRadarChart() {
  const [chartData, setChartData] = useState(mockData);

  // 这里可以添加实际数据获取逻辑
  useEffect(() => {
    // 模拟数据加载
    const timer = setTimeout(() => {
      setChartData(mockData);
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-4">
      <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">性能雷达图</h2>
      <div className="h-80">
        <Radar data={chartData} options={options} />
      </div>
    </div>
  );
} 