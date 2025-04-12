"use client";

import { useState } from "react";

interface Tab {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: Tab[];
  defaultTabId?: string;
  onChange?: (tabId: string) => void;
  className?: string;
}

export default function Tabs({ tabs, defaultTabId, onChange, className = "" }: TabsProps) {
  const [activeTabId, setActiveTabId] = useState(defaultTabId || tabs[0]?.id);

  const handleTabClick = (tabId: string) => {
    setActiveTabId(tabId);
    if (onChange) {
      onChange(tabId);
    }
  };

  return (
    <div className={`border-b border-gray-200 dark:border-gray-800 ${className}`}>
      <div className="flex space-x-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleTabClick(tab.id)}
            className={`py-2 px-1 font-medium text-sm border-b-2 transition-colors ${
              activeTabId === tab.id
                ? "border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            }`}
            aria-current={activeTabId === tab.id ? "page" : undefined}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
} 