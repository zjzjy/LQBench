"use client";

import { useState } from "react";
import Image from "next/image";
import MainLayout from "@/components/layout/MainLayout";
import ModelComparisonChart from "@/components/charts/ModelComparisonChart";
import PerformanceRadarChart from "@/components/charts/PerformanceRadarChart";
import ComplexityAnalysisChart from "@/components/charts/ComplexityAnalysisChart";
import Tabs from "@/components/ui/Tabs";

export default function Dashboard() {
  const [activeViewTab, setActiveViewTab] = useState("overview");
  const [activeModelTab, setActiveModelTab] = useState("top");

  const viewTabs = [
    { id: "overview", label: "概览" },
    { id: "leaderboard", label: "排行榜" },
  ];

  const modelTabs = [
    { id: "top", label: "顶级模型" },
    { id: "custom", label: "自定义选择" },
  ];

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">仪表盘</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            探索威胁建模基准测试结果和模型性能
          </p>
        </div>

        <div className="mb-6">
          <Tabs 
            tabs={viewTabs} 
            defaultTabId="overview" 
            onChange={setActiveViewTab} 
          />
        </div>

        {activeViewTab === "overview" ? (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <ModelComparisonChart />
              <PerformanceRadarChart />
            </div>
            
            <div className="mb-6">
              <Tabs 
                tabs={modelTabs} 
                defaultTabId="top" 
                onChange={setActiveModelTab}
              />
            </div>

            <div className="mb-6">
              <ComplexityAnalysisChart />
            </div>
          </>
        ) : (
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">排行榜</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">排名</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">模型</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">总分</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">威胁识别</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">风险评估</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">完整性</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">1</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">GPT-4</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">87</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">90</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">85</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">85</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">2</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">Claude 3</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">85</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">86</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">89</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">84</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">3</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">Gemini</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">80</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">82</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">79</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">80</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
