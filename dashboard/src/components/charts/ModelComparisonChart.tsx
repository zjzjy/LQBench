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
  labels: ["GPT-4", "Claude 3", "Llama 3", "Mistral", "Gemini"],
  datasets: [
    {
      label: "总体得分",
      data: [87, 85, 76, 72, 80],
      backgroundColor: "#3498db",
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
      text: "模型性能比较",
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
  },
  onClick: (event: any, elements: any) => {
    if (elements.length > 0) {
      const index = elements[0].index;
      console.log("点击了:", mockData.labels[index]);
    }
  },
};

export default function ModelComparisonChart() {
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
      <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">模型比较</h2>
      <div className="h-80">
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
} 