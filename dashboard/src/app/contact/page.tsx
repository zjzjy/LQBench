"use client";

import { useState } from "react";
import { Send, Mail, GitHub, Twitter } from "lucide-react";
import MainLayout from "@/components/layout/MainLayout";

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // 模拟表单提交
    setTimeout(() => {
      setIsSubmitting(false);
      setIsSubmitted(true);
      setFormData({
        name: "",
        email: "",
        subject: "",
        message: "",
      });
    }, 1500);
  };

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">联系我们</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            有问题或建议？请随时与我们联系
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="col-span-2">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">发送消息</h2>
              
              {isSubmitted ? (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-4">
                  <p className="text-green-800 dark:text-green-400">感谢您的消息！我们会尽快回复您。</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit}>
                  <div className="mb-4">
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      您的姓名
                    </label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      required
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
                    />
                  </div>
                  <div className="mb-4">
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      电子邮箱
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
                    />
                  </div>
                  <div className="mb-4">
                    <label htmlFor="subject" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      主题
                    </label>
                    <select
                      id="subject"
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      required
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
                    >
                      <option value="">请选择...</option>
                      <option value="general">一般询问</option>
                      <option value="bug">问题报告</option>
                      <option value="suggestion">建议</option>
                      <option value="collaboration">合作机会</option>
                    </select>
                  </div>
                  <div className="mb-4">
                    <label htmlFor="message" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      消息
                    </label>
                    <textarea
                      id="message"
                      name="message"
                      rows={5}
                      value={formData.message}
                      onChange={handleChange}
                      required
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex items-center justify-center w-full md:w-auto bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? (
                      <span>提交中...</span>
                    ) : (
                      <>
                        <Send size={18} className="mr-2" />
                        <span>发送消息</span>
                      </>
                    )}
                  </button>
                </form>
              )}
            </div>
          </div>
          
          <div>
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">联系方式</h2>
              <div className="space-y-4">
                <div className="flex items-start">
                  <Mail className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 mr-3" />
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">电子邮件</h3>
                    <p className="text-gray-600 dark:text-gray-400">contact@tmbench.org</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <GitHub className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 mr-3" />
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">GitHub</h3>
                    <a 
                      href="https://github.com/tmbench/benchmark" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      github.com/tmbench
                    </a>
                  </div>
                </div>
                <div className="flex items-start">
                  <Twitter className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 mr-3" />
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">Twitter</h3>
                    <a 
                      href="https://twitter.com/tmbench" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      @tmbench
                    </a>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">办公时间</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                周一至周五: 9:00 - 17:00
              </p>
              <p className="text-gray-600 dark:text-gray-400">
                周末: 休息
              </p>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
} 