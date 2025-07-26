'use client';

import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useSettings } from '../contexts/SettingsContext';
import { LanguageSelector } from '../contexts/LanguageContext';
import MultiInputArea from '../components/MultiInputArea';

import { Upload, Download, MessageSquare, Activity, Settings, Moon, Sun, Monitor, Globe } from 'lucide-react';

// 極簡文件上傳組件
const MinimalFileUpload = () => {
  const { t } = useLanguage();
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles(prev => [...prev, ...droppedFiles]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...selectedFiles]);
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    // Simulate upload
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsUploading(false);
    setFiles([]);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <Upload className="w-4 h-4" />
        <span className="text-sm font-medium">{t('upload.title')}</span>
      </div>
      
      <div
        className={`flex-1 border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 ${
          isDragging 
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-950 scale-[1.02]' 
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
        }`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <input
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
        />
        <label htmlFor="file-upload" className="cursor-pointer">
          <div className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors">
            <Upload className="w-8 h-8 mx-auto mb-2" />
            <p className="text-sm">{t('upload.dragDrop')}</p>
          </div>
        </label>
        
        {files.length > 0 && (
          <div className="mt-4 space-y-2 animate-fade-in">
            {files.map((file, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-300">
                <span className="truncate">{file.name}</span>
                <button
                  onClick={() => setFiles(files.filter((_, i) => i !== index))}
                  className="text-red-500 hover:text-red-700 ml-2"
                >
                  ×
                </button>
              </div>
            ))}
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="mt-3 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-2 px-4 rounded-lg transition-all duration-200 font-medium hover:shadow-md disabled:cursor-not-allowed"
            >
              {isUploading ? t('upload.uploading') : t('upload.uploadBtn')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// 極簡聊天組件
const MinimalChat = () => {
  const { t } = useLanguage();
  const [messages] = useState([
    { id: 1, text: 'AI分析已開始...', type: 'system', user: 'AI Analyst', time: '14:30' },
    { id: 2, text: '正在處理數據...', type: 'ai', user: 'Expert A', time: '14:32' },
  ]);

  const getAvatarColor = (type: string) => {
    switch (type) {
      case 'system': return 'bg-blue-100 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400';
      case 'ai': return 'bg-green-100 text-green-600 dark:bg-green-900/20 dark:text-green-400';
      default: return 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <MessageSquare className="w-4 h-4" />
        <span className="text-sm font-medium">{t('debateChat.title')}</span>
        <div className="ml-auto">
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
            {t('debateChat.activeSession')}
          </span>
        </div>
      </div>
      
      <div className="flex-1 bg-gray-50 dark:bg-gray-800 rounded-lg p-4 overflow-y-auto">
        <div className="space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className="flex items-start gap-3 group">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${getAvatarColor(msg.type)}`}>
                {msg.user.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{msg.user}</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">{msg.time}</span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 leading-relaxed">{msg.text}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// 極簡狀態監控
const MinimalStatus = () => {
  const { t } = useLanguage();
  const [status, setStatus] = useState({
    cpu: 45,
    memory: 67,
    connections: 3,
    uptime: '2h 15m'
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setStatus(prev => ({
        ...prev,
        cpu: Math.floor(Math.random() * 30) + 30,
        memory: Math.floor(Math.random() * 20) + 50,
        connections: Math.floor(Math.random() * 5) + 5
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (value: number) => {
    if (value < 50) return 'text-green-600 dark:text-green-400';
    if (value < 80) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <Monitor className="w-4 h-4" />
        <span className="text-sm font-medium">{t('monitoring.title')}</span>
        <div className="ml-auto">
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
            {t('common.operational')}
          </span>
        </div>
      </div>
      
      <div className="space-y-4">
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className={`text-xl font-bold transition-colors ${getStatusColor(status.cpu)}`}>{status.cpu}%</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">CPU</div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-2">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-500 ${
                    status.cpu < 50 ? 'bg-green-500' : status.cpu < 80 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${status.cpu}%` }}
                ></div>
              </div>
            </div>
            <div className="text-center">
              <div className={`text-xl font-bold transition-colors ${getStatusColor(status.memory)}`}>{status.memory}%</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('monitoring.memory')}</div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-2">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-500 ${
                    status.memory < 50 ? 'bg-green-500' : status.memory < 80 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${status.memory}%` }}
                ></div>
              </div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-blue-600 dark:text-blue-400">{status.connections}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('monitoring.connections')}</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-gray-900 dark:text-white">{status.uptime}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('common.uptime')}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// 主題切換按鈕
const ThemeToggle = () => {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const theme = localStorage.getItem('theme');
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const shouldBeDark = theme === 'dark' || (!theme && systemDark);
    
    setIsDark(shouldBeDark);
    document.documentElement.classList.toggle('dark', shouldBeDark);
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark', newTheme);
  };

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-200 group"
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-gray-600 dark:text-gray-300 group-hover:text-yellow-500 transition-colors" />
      ) : (
        <Moon className="w-5 h-5 text-gray-600 dark:text-gray-300 group-hover:text-blue-500 transition-colors" />
      )}
    </button>
  );
};

// 極簡主頁面
function MinimalHomePage() {
  const { t } = useLanguage();
  const { setIsSettingsOpen } = useSettings();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors duration-300">
      {/* 頂部導航 */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4 sticky top-0 z-50 backdrop-blur-sm bg-white/95 dark:bg-gray-900/95">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center shadow-sm">
              <span className="text-white font-bold text-sm">AI</span>
            </div>
            <h1 className="text-xl font-semibold">{t('header.title')}</h1>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
              <Globe className="w-5 h-5 text-gray-600 dark:text-gray-300" />
            </div>
            <LanguageSelector />
            <ThemeToggle />
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title={t('common.settings')}
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* 主要內容 - 2x2 四窗口佈局 */}
      <main className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 gap-6 h-[calc(100vh-140px)]">
            {/* 左上：上傳文件/下載報告窗口 */}
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="h-full flex flex-col">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <Upload className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">{t('upload.title')} / {t('download.title')}</h3>
                </div>
                <div className="flex-1 grid grid-cols-2 gap-4">
                  {/* 上傳區域 */}
                  <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4 text-center hover:border-blue-500 transition-colors">
                    <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-600 dark:text-gray-400">{t('upload.dragDrop')}</p>
                  </div>
                  {/* 下載區域 */}
                  <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 text-center">
                    <Download className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-600 dark:text-gray-400">{t('download.noReports')}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* 右上：AI模型鏈接狀況及當前角色 */}
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="h-full flex flex-col">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <Monitor className="w-5 h-5 text-green-600 dark:text-green-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">{t('llm.title')}</h3>
                </div>
                <div className="flex-1 space-y-3">
                  <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-sm font-medium">OpenAI GPT-4</span>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
                      {t('llm.connected')}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-sm font-medium">Claude 3</span>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
                      {t('llm.connected')}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-sm font-medium">Gemini Pro</span>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full mr-1"></div>
                      {t('llm.testing')}
                    </span>
                  </div>
                  <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <p className="text-sm font-medium text-blue-800 dark:text-blue-400">{t('llm.currentRole')}: {t('llm.moderator')}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* 左下：用戶聊天輸入框 */}
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="h-full flex flex-col">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <MessageSquare className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">{t('input.title')}</h3>
                </div>
                <div className="flex-1 flex flex-col">
                  <textarea
                    className="flex-1 p-4 border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                    placeholder={t('input.placeholder')}
                  />
                  <div className="flex justify-end mt-4">
                    <button className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium">
                      {t('input.submit')}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* 右下：AI辯論訊息實時廣播 */}
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="h-full flex flex-col">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
                    <Activity className="w-5 h-5 text-red-600 dark:text-red-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">{t('debate.title')}</h3>
                </div>
                <div className="flex-1 overflow-y-auto space-y-3">
                  <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-blue-600 dark:text-blue-400">GPT-4</span>
                      <span className="text-xs text-gray-500">14:23</span>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{t('debate.sampleMessage1')}</p>
                  </div>
                  <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-green-600 dark:text-green-400">Claude</span>
                      <span className="text-xs text-gray-500">14:24</span>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{t('debate.sampleMessage2')}</p>
                  </div>
                  <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-yellow-600 dark:text-yellow-400">Gemini</span>
                      <span className="text-xs text-gray-500">14:25</span>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{t('debate.sampleMessage3')}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 mt-16">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
            <span>© 2024 AI Analyst. {t('common.status')}: {t('common.operational')}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default MinimalHomePage;