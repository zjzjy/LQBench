"use client";

import { useState } from "react";
import Link from "next/link";
import { Home, Info, BookOpen, Mail, ChevronLeft, ChevronRight } from "lucide-react";

interface NavItemProps {
  href: string;
  icon: React.ReactNode;
  label: string;
  isCollapsed: boolean;
}

const NavItem = ({ href, icon, label, isCollapsed }: NavItemProps) => {
  return (
    <Link 
      href={href} 
      className="flex items-center p-3 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
    >
      <div className="text-gray-700 dark:text-gray-300">
        {icon}
      </div>
      {!isCollapsed && (
        <span className="ml-3 text-gray-700 dark:text-gray-300">{label}</span>
      )}
    </Link>
  );
};

export default function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className={`${isCollapsed ? 'w-16' : 'w-64'} h-screen bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-300 fixed top-0 left-0 z-30`}>
      <div className="p-4 flex justify-between items-center">
        {!isCollapsed && (
          <Link href="/" className="text-xl font-bold text-blue-600 dark:text-blue-400">
            TM-Bench
          </Link>
        )}
        <button 
          onClick={toggleSidebar}
          className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>
      <nav className="mt-6 px-2">
        <NavItem 
          href="/" 
          icon={<Home size={20} />} 
          label="Dashboard" 
          isCollapsed={isCollapsed} 
        />
        <NavItem 
          href="/about" 
          icon={<Info size={20} />} 
          label="About" 
          isCollapsed={isCollapsed} 
        />
        <NavItem 
          href="/methodology" 
          icon={<BookOpen size={20} />} 
          label="Methodology" 
          isCollapsed={isCollapsed} 
        />
        <NavItem 
          href="/contact" 
          icon={<Mail size={20} />} 
          label="Contact" 
          isCollapsed={isCollapsed} 
        />
      </nav>
    </div>
  );
} 