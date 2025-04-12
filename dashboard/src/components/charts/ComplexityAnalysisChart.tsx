"use client";

import { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// 模拟数据
const mockData = {
  labels: ["简单", "中等", "复杂", "非常复杂"],
  datasets: [
    {
      label: "GPT-4",
      data: [92, 88, 83, 75],
      backgroundColor: "#6ad8c4",
    },
    {
      label: "Claude 3",
      data: [90, 87, 81, 72],
      backgroundColor: "#ff8996",
    },
    {
      label: "Llama 3",
      data: [86, 80, 73, 64],
      backgroundColor: "#f7b731",
    },
    {
      label: "Gemini",
      data: [89, 85, 78, 68],
      backgroundColor: "#9d6ccf",
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
      text: "不同复杂度下的性能",
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      max: 100,
      title: {
        display: true,
        text: "得分",
      },
    },
    x: {
      title: {
        display: true,
        text: "复杂度级别",
      },
    },
  },
};

export default function ComplexityAnalysisChart() {
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
      <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">复杂度分析</h2>
      <div className="h-80">
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
} 