'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// 支持的語言類型
export type Language = 'zh-CN' | 'zh-TW' | 'en' | 'ja';

// 語言選項配置
export const LANGUAGE_OPTIONS = [
  { code: 'zh-CN' as Language, name: '简体中文', flag: '🇨🇳' },
  { code: 'zh-TW' as Language, name: '繁體中文', flag: '🇹🇼' },
  { code: 'en' as Language, name: 'English', flag: '🇺🇸' },
  { code: 'ja' as Language, name: '日本語', flag: '🇯🇵' }
];

// 翻譯數據類型
interface TranslationData {
  [key: string]: any;
}

// 語言上下文類型
interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, fallback?: string) => string;
  isLoading: boolean;
}

// 創建語言上下文
const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// 語言提供者組件
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>('zh-TW');
  const [translations, setTranslations] = useState<TranslationData>({});
  const [isLoading, setIsLoading] = useState(true);

  // 從 localStorage 加載保存的語言設置
  useEffect(() => {
    const savedLanguage = localStorage.getItem('preferred-language') as Language;
    if (savedLanguage && LANGUAGE_OPTIONS.some(opt => opt.code === savedLanguage)) {
      setLanguageState(savedLanguage);
    }
  }, []);

  // 加載翻譯文件
  useEffect(() => {
    const loadTranslations = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`/locales/${language}.json`);
        if (response.ok) {
          const data = await response.json();
          setTranslations(data);
        } else {
          console.warn(`Failed to load translations for ${language}`);
          // 如果加載失敗，嘗試加載默認語言（繁體中文）
          if (language !== 'zh-TW') {
            const fallbackResponse = await fetch('/locales/zh-TW.json');
            if (fallbackResponse.ok) {
              const fallbackData = await fallbackResponse.json();
              setTranslations(fallbackData);
            }
          }
        }
      } catch (error) {
        console.error('Error loading translations:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadTranslations();
  }, [language]);

  // 設置語言並保存到 localStorage
  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('preferred-language', lang);
  };

  // 翻譯函數
  const t = (key: string, fallback?: string): string => {
    const keys = key.split('.');
    let value = translations;
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        // 如果找不到翻譯，返回 fallback 或 key
        return fallback || key;
      }
    }
    
    return typeof value === 'string' ? value : (fallback || key);
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, isLoading }}>
      {children}
    </LanguageContext.Provider>
  );
}

// 使用語言上下文的 Hook
export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}

// 語言切換組件
export function LanguageSelector() {
  const { language, setLanguage } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);

  const currentLanguage = LANGUAGE_OPTIONS.find(opt => opt.code === language);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-green-400 text-black px-3 py-1 font-bold hover:bg-green-300 border border-green-400 text-xs flex items-center space-x-1"
        title="Language / 語言 / 言語"
      >
        <span>{currentLanguage?.flag}</span>
        <span>{currentLanguage?.name}</span>
        <span className="text-xs">{isOpen ? '▲' : '▼'}</span>
      </button>
      
      {isOpen && (
        <div className="absolute top-full right-0 mt-1 bg-black border border-green-400 z-50 min-w-[120px]">
          {LANGUAGE_OPTIONS.map((option) => (
            <button
              key={option.code}
              onClick={() => {
                setLanguage(option.code);
                setIsOpen(false);
              }}
              className={`w-full text-left px-3 py-2 text-xs hover:bg-green-400 hover:text-black flex items-center space-x-2 ${
                language === option.code ? 'bg-green-400 text-black' : 'text-green-400'
              }`}
            >
              <span>{option.flag}</span>
              <span>{option.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}