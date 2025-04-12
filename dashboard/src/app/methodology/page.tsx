"use client";

import Image from "next/image";
import MainLayout from "@/components/layout/MainLayout";

export default function MethodologyPage() {
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">评测方法论</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            我们如何评估大型语言模型的威胁建模能力
          </p>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">评估框架</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            我们的评估框架是基于以下核心原则设计的：
          </p>
          <ul className="list-disc pl-6 mb-4 text-gray-600 dark:text-gray-400 space-y-2">
            <li><span className="font-medium">全面性</span>：测试覆盖威胁建模的所有关键方面，包括威胁识别、风险评估、缓解措施和文档。</li>
            <li><span className="font-medium">现实性</span>：使用来自真实世界的案例研究和架构，反映实际应用场景。</li>
            <li><span className="font-medium">复杂度梯度</span>：包含从简单到复杂的各种场景，以测试模型的能力边界。</li>
            <li><span className="font-medium">可重复性</span>：确保结果可以被其他研究人员复现和验证。</li>
          </ul>
          <div className="relative w-full h-64 my-6 rounded-lg overflow-hidden">
            <Image
              src="https://picsum.photos/id/180/800/400"
              alt="评估框架图"
              fill
              className="object-cover"
            />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">评估指标</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium mb-2 text-gray-800 dark:text-gray-200">威胁识别能力</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                模型识别潜在威胁的完整性和准确性。包括：
              </p>
              <ul className="list-disc pl-6 text-gray-600 dark:text-gray-400">
                <li>威胁覆盖范围</li>
                <li>威胁分类准确性</li>
                <li>边缘案例处理</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-medium mb-2 text-gray-800 dark:text-gray-200">风险评估质量</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                模型评估威胁严重性和优先级的能力。包括：
              </p>
              <ul className="list-disc pl-6 text-gray-600 dark:text-gray-400">
                <li>严重性评估准确性</li>
                <li>概率估计合理性</li>
                <li>影响分析深度</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-medium mb-2 text-gray-800 dark:text-gray-200">缓解措施推荐</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                模型提出实用且有效缓解策略的能力。包括：
              </p>
              <ul className="list-disc pl-6 text-gray-600 dark:text-gray-400">
                <li>缓解策略有效性</li>
                <li>实施可行性</li>
                <li>推荐的具体程度</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-medium mb-2 text-gray-800 dark:text-gray-200">完整性与一致性</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                威胁模型的整体质量和连贯性。包括：
              </p>
              <ul className="list-disc pl-6 text-gray-600 dark:text-gray-400">
                <li>文档完整性</li>
                <li>内部一致性</li>
                <li>假设的清晰度</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">评分系统</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            每个模型在每个场景中的表现都根据上述指标进行评分，总分为100分。评分由安全专家团队根据预定义的标准进行。我们使用以下评分级别：
          </p>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">分数范围</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">评级</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">描述</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">90-100</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">卓越</td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">全面的威胁识别和风险评估，具有高度实用的缓解策略</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">80-89</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">优秀</td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">良好的威胁覆盖和评估，可行的缓解措施，少量遗漏</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">70-79</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">良好</td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">基本威胁识别，合理的风险评估，基本缓解措施</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">60-69</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">及格</td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">部分威胁识别，有限的风险评估，简单的缓解措施</td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">0-59</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">不及格</td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">明显缺失关键威胁，评估不准确，缓解措施无效或缺失</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </MainLayout>
  );
} 