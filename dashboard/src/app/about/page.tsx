"use client";

import Image from "next/image";
import MainLayout from "@/components/layout/MainLayout";

export default function AboutPage() {
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">关于 TM-Bench</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            威胁建模基准测试项目的背景和目标
          </p>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
              <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">项目概述</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                TM-Bench（威胁建模基准测试）是一个全面评估大型语言模型（LLM）在威胁建模任务中表现的项目。本项目旨在提供一个标准化的基准测试框架，帮助研究人员和从业者理解不同模型在识别、分析和缓解安全威胁方面的能力。
              </p>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                在软件安全领域，威胁建模是一个关键过程，它涉及识别潜在的威胁和漏洞，评估它们的风险，并制定适当的缓解策略。随着人工智能技术的发展，LLMs显示出在辅助安全分析方面的巨大潜力，但不同模型的性能存在显著差异。
              </p>
              <p className="text-gray-600 dark:text-gray-400">
                我们的基准测试考虑了多种复杂度的威胁建模场景，从简单的Web应用程序到复杂的分布式系统，为各种模型提供了全面的评估。通过这些指标，我们希望推动人工智能安全分析工具的进步，并促进更安全的软件开发实践。
              </p>
            </div>
            <div className="flex justify-center items-center">
              <div className="relative w-full h-72">
                <Image
                  src="https://picsum.photos/id/0/400/300"
                  alt="威胁建模概念图"
                  fill
                  className="object-cover rounded-lg"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">我们的团队</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex flex-col items-center">
              <div className="relative w-32 h-32 mb-4">
                <Image
                  src="https://picsum.photos/id/1005/300/300"
                  alt="团队成员照片"
                  fill
                  className="object-cover rounded-full"
                />
              </div>
              <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200">张教授</h3>
              <p className="text-gray-600 dark:text-gray-400">首席研究员</p>
            </div>
            <div className="flex flex-col items-center">
              <div className="relative w-32 h-32 mb-4">
                <Image
                  src="https://picsum.photos/id/1006/300/300"
                  alt="团队成员照片"
                  fill
                  className="object-cover rounded-full"
                />
              </div>
              <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200">李博士</h3>
              <p className="text-gray-600 dark:text-gray-400">安全专家</p>
            </div>
            <div className="flex flex-col items-center">
              <div className="relative w-32 h-32 mb-4">
                <Image
                  src="https://picsum.photos/id/1012/300/300"
                  alt="团队成员照片"
                  fill
                  className="object-cover rounded-full"
                />
              </div>
              <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200">王工程师</h3>
              <p className="text-gray-600 dark:text-gray-400">AI研究员</p>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
} 