'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface SettingsContextType {
  fontSize: number;
  setFontSize: (size: number) => void;
  isSettingsOpen: boolean;
  setIsSettingsOpen: (open: boolean) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

interface SettingsProviderProps {
  children: ReactNode;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [fontSize, setFontSize] = useState(14); // 默認字體大小
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // 從 localStorage 加載設置
  useEffect(() => {
    const savedFontSize = localStorage.getItem('bbs-font-size');
    if (savedFontSize) {
      setFontSize(parseInt(savedFontSize, 10));
    }
  }, []);

  // 保存字體大小到 localStorage
  const handleSetFontSize = (size: number) => {
    setFontSize(size);
    localStorage.setItem('bbs-font-size', size.toString());
    
    // 動態更新 CSS 變量
    document.documentElement.style.setProperty('--bbs-font-size', `${size}px`);
  };

  // 初始化 CSS 變量
  useEffect(() => {
    document.documentElement.style.setProperty('--bbs-font-size', `${fontSize}px`);
  }, [fontSize]);

  const value = {
    fontSize,
    setFontSize: handleSetFontSize,
    isSettingsOpen,
    setIsSettingsOpen,
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};