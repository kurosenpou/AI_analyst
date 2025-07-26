'use client';

import { useState, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import { SettingsProvider, useSettings } from '../contexts/SettingsContext';
import { LanguageProvider, useLanguage, LanguageSelector } from '../contexts/LanguageContext';
import SettingsMenu from '../components/SettingsMenu';
import MultiInputArea from '../components/MultiInputArea';
import ReportDownloadCenter from '../components/ReportDownloadCenter';

// 文件上傳組件 - BBS風格（支持多語言）
const FileUploadArea = () => {
  const { t } = useLanguage();
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setUploadedFiles(prev => [...prev, ...files]);
    toast.success(`[${t('common.upload').toUpperCase()}] ${files.length} files added to queue`);
  };

  const handleUpload = async () => {
    if (uploadedFiles.length === 0) return;
    
    setIsUploading(true);
    try {
      // 模擬上傳過程
      await new Promise(resolve => setTimeout(resolve, 2000));
      toast.success(t('fileUpload.uploadSuccess'));
      setUploadedFiles([]);
    } catch (error) {
      toast.error(t('fileUpload.uploadError'));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="h-full p-2 bg-black text-green-400 font-mono text-sm">
      <div className="border border-green-400 h-full flex flex-col">
        <div className="bg-green-400 text-black px-2 py-1 font-bold flex-shrink-0">
          ╔═══════════════════════════════════════╗
        </div>
        <div className="bg-green-400 text-black px-2 py-0 font-bold text-center flex-shrink-0">
          ║        {t('fileUpload.title')}        ║
        </div>
        <div className="bg-green-400 text-black px-2 py-1 font-bold flex-shrink-0">
          ╚═══════════════════════════════════════╝
        </div>
        
        <div className="p-4 flex flex-col flex-1 min-h-0">
          <div className="text-center mb-4 flex-shrink-0">
            <pre className="text-xs leading-tight">
{`    ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
   █                                     █
   █  [F] ${t('fileUpload.selectFile').toUpperCase().padEnd(29)} █
   █                                     █
   █  ${t('fileUpload.supportedFormats')}: .csv, .txt, .json      █
   █  ${t('fileUpload.maxSize')}: 10MB                █
    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀`}
            </pre>
          </div>
          
          <div className="text-center mb-4 flex-shrink-0 space-y-2">
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="bg-green-400 text-black px-4 py-1 font-bold hover:bg-green-300 border-2 border-green-400 block mx-auto"
              disabled={isUploading}
            >
              📁 {t('fileUpload.selectFile')}
            </button>
            
            {uploadedFiles.length > 0 && (
              <button 
                onClick={handleUpload}
                disabled={isUploading}
                className={`px-4 py-1 font-bold border-2 block mx-auto ${
                  isUploading 
                    ? 'bg-yellow-400 text-black border-yellow-400' 
                    : 'bg-blue-600 text-white border-blue-600 hover:bg-blue-500'
                }`}
              >
                {isUploading ? '⏳ ' + t('fileUpload.uploading') : '📤 ' + t('common.upload')}
              </button>
            )}
            
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".csv,.txt,.json,.xlsx,.xls"
              className="hidden"
              onChange={handleFileSelect}
            />
          </div>
          
          {uploadedFiles.length > 0 && (
            <div className="flex-1 overflow-y-auto min-h-0">
              <div className="border border-green-400 p-2">
                <div className="text-green-300 mb-2 text-xs">
                  » UPLOAD QUEUE [{uploadedFiles.length}]:
                </div>
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="text-xs mb-1 flex justify-between items-center">
                    <span>
                      [{String(index + 1).padStart(2, '0')}] {file.name.substring(0, 25)}{file.name.length > 25 ? '...' : ''}
                    </span>
                    <span className="text-cyan-400">
                      {(file.size / 1024 / 1024).toFixed(2)}MB
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// LLM辯論聊天室組件 - BBS風格（支持多語言）
const DebateChatRoom = () => {
  const { t } = useLanguage();
  const [messages, setMessages] = useState<Array<{
    id: string;
    speaker: string;
    content: string;
    timestamp: Date;
    type: 'debate' | 'judge' | 'system';
  }>>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 模擬實時消息
    const interval = setInterval(() => {
      const speakers = ['GPT-4', 'CLAUDE3', 'JUDGE_AI'];
      const contents = [
        'ANALYZING DATA PATTERNS... TREND DETECTED',
        'SAMPLE BIAS DETECTED. RECALCULATING...',
        'BOTH ARGUMENTS VALID. PROCESSING SYNTHESIS...',
        'STATISTICAL SIGNIFICANCE: 95.7% CONFIDENCE',
        'INSUFFICIENT EVIDENCE. REQUESTING MORE DATA...'
      ];
      
      const newMessage = {
        id: Date.now().toString(),
        speaker: speakers[Math.floor(Math.random() * speakers.length)],
        content: contents[Math.floor(Math.random() * contents.length)],
        timestamp: new Date(),
        type: Math.random() > 0.7 ? 'judge' : 'debate' as 'debate' | 'judge' | 'system'
      };
      
      setMessages(prev => [...prev.slice(-15), newMessage]);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour12: false }).substring(0, 5);
  };

  return (
    <div className="h-full p-2 bg-black text-green-400 font-mono text-sm">
      <div className="border border-green-400 h-full flex flex-col">
        <div className="bg-green-400 text-black px-2 py-1 font-bold text-center">
          ╔══════════════════════════════════════════════════════════════╗
        </div>
        <div className="bg-green-400 text-black px-2 py-0 font-bold text-center">
          ║              {t('debateChat.title')}              ║
        </div>
        <div className="bg-green-400 text-black px-2 py-1 font-bold text-center">
          ╚══════════════════════════════════════════════════════════════╝
        </div>
        
        <div className="flex-1 overflow-y-auto p-2 space-y-1 min-h-0">
          <div className="text-green-300 text-xs mb-2">
            *** {t('debateChat.title').toUpperCase()} ACTIVE ***
          </div>
          
          {messages.map((message) => {
            const userColor = message.type === 'judge' ? 'text-yellow-400' : 
                            message.speaker === 'GPT-4' ? 'text-cyan-400' : 'text-magenta-400';
            const prefix = message.type === 'judge' ? '[JUDGE]' : '[DEBATER]';
            
            return (
              <div key={message.id} className="text-xs leading-relaxed">
                <div className="flex items-start space-x-1">
                  <span className="text-green-300">[{formatTime(message.timestamp)}]</span>
                  <span className={userColor}>{prefix}</span>
                  <span className={userColor + ' font-bold'}>&lt;{message.speaker}&gt;</span>
                </div>
                <div className="ml-16 text-green-400 break-words">
                  {message.content}
                </div>
              </div>
            );
          })}
          
          <div ref={chatEndRef} />
        </div>
        
        <div className="border-t border-green-400 p-2">
          <div className="text-xs text-green-300">
            » {t('common.online')}: 3 | {t('debateChat.title')}: {messages.length} | {t('common.status')}: {t('common.operational').toUpperCase()}
          </div>
        </div>
      </div>
    </div>
  );
};

// LLM連接狀態組件 - BBS風格（支持多語言）
const LLMConnectionStatus = () => {
  const { t } = useLanguage();
  const [connections, setConnections] = useState([
    { name: 'GPT-4', status: 'connected', latency: 45, role: 'DEBATER_A' },
    { name: 'CLAUDE3', status: 'connected', latency: 52, role: 'DEBATER_B' },
    { name: 'GEMINI', status: 'disconnected', latency: 0, role: 'JUDGE' },
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setConnections(prev => prev.map(conn => ({
        ...conn,
        status: Math.random() > 0.1 ? 'connected' : 'disconnected',
        latency: conn.status === 'connected' ? Math.floor(Math.random() * 100) + 20 : 0
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-2 bg-black text-green-400 font-mono text-sm h-full">
      <div className="border border-green-400 h-full flex flex-col">
        <div className="bg-green-400 text-black px-2 py-1 text-center font-bold flex-shrink-0">
          ┌─────────────────────────────────────┐
        </div>
        <div className="bg-green-400 text-black px-2 py-0 text-center font-bold flex-shrink-0">
          │         SYSTEM STATUS MONITOR       │
        </div>
        <div className="bg-green-400 text-black px-2 py-1 text-center font-bold flex-shrink-0">
          └─────────────────────────────────────┘
        </div>
        
        <div className="p-3 space-y-2 flex-1 overflow-y-auto min-h-0">
          <div className="text-green-300 text-xs mb-3">
            *** AI NODES CONNECTION STATUS ***
          </div>
          
          {connections.map((conn) => {
            const statusSymbol = conn.status === 'connected' ? '●' : '○';
            const statusColor = conn.status === 'connected' ? 'text-green-400' : 'text-red-400';
            const statusText = conn.status === 'connected' ? 'ONLINE' : 'OFFLINE';
            
            return (
              <div key={conn.name} className="text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={statusColor + ' text-lg'}>{statusSymbol}</span>
                    <span className="text-cyan-400 font-bold">{conn.name}</span>
                    <span className="text-yellow-400">[{conn.role}]</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className={statusColor + ' font-bold'}>[{statusText}]</span>
                    {conn.status === 'connected' && (
                      <span className="text-yellow-400">{conn.latency}ms</span>
                    )}
                  </div>
                </div>
                <div className="ml-6 text-green-300 text-xs">
                  {conn.status === 'connected' 
                    ? `└─ READY FOR PROCESSING` 
                    : `└─ CONNECTION LOST`
                  }
                </div>
              </div>
            );
          })}
          
          <div className="border-t border-green-400 mt-4 pt-2">
            <div className="text-xs text-green-300" suppressHydrationWarning>
              » UPTIME: {new Date().toLocaleTimeString('en-US', { hour12: false })}
            </div>
            <div className="text-xs text-green-300">
              » ACTIVE NODES: {connections.filter(c => c.status === 'connected').length}/{connections.length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// 實時監控組件 - BBS風格（支持多語言）
const RealTimeMonitoring = () => {
  const { t } = useLanguage();
  const [metrics, setMetrics] = useState({
    cpuUsage: 45,
    memoryUsage: 67,
    activeConnections: 12,
    messagesPerSecond: 3.2,
    networkTraffic: 1024,
    diskUsage: 34
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics({
        cpuUsage: Math.floor(Math.random() * 100),
        memoryUsage: Math.floor(Math.random() * 100),
        activeConnections: Math.floor(Math.random() * 20) + 5,
        messagesPerSecond: parseFloat((Math.random() * 10).toFixed(1)),
        networkTraffic: Math.floor(Math.random() * 2048) + 512,
        diskUsage: Math.floor(Math.random() * 100)
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const getBarGraph = (value: number, maxWidth: number = 20) => {
    const filled = Math.floor((value / 100) * maxWidth);
    const empty = maxWidth - filled;
    return '█'.repeat(filled) + '░'.repeat(empty);
  };

  return (
    <div className="p-2 bg-black text-green-400 font-mono text-sm h-full">
      <div className="border border-green-400 h-full flex flex-col">
        <div className="bg-green-400 text-black px-2 py-1 text-center font-bold flex-shrink-0">
          ╔══════════════════════════════════════╗
        </div>
        <div className="bg-green-400 text-black px-2 py-0 text-center font-bold flex-shrink-0">
          ║         {t('monitoring.title')} v2.1          ║
        </div>
        <div className="bg-green-400 text-black px-2 py-1 text-center font-bold flex-shrink-0">
          ╚══════════════════════════════════════╝
        </div>
        
        <div className="p-3 space-y-3 flex-1 overflow-y-auto min-h-0">
          <div className="text-green-300 text-xs mb-3">
            *** {t('monitoring.realTimeMetrics').toUpperCase()} ***
          </div>
          
          <div className="space-y-2">
            <div className="text-xs">
              <div className="flex justify-between items-center">
                <span className="text-cyan-400">{t('monitoring.cpuUsage').toUpperCase()}:</span>
                <span className="text-yellow-400 font-bold">{metrics.cpuUsage}%</span>
              </div>
              <div className="text-green-400 text-xs mt-1">
                [{getBarGraph(metrics.cpuUsage)}]
              </div>
            </div>
            
            <div className="text-xs">
              <div className="flex justify-between items-center">
                <span className="text-cyan-400">{t('monitoring.memory').toUpperCase()}:</span>
                <span className="text-yellow-400 font-bold">{metrics.memoryUsage}%</span>
              </div>
              <div className="text-green-400 text-xs mt-1">
                [{getBarGraph(metrics.memoryUsage)}]
              </div>
            </div>
            
            <div className="text-xs">
              <div className="flex justify-between items-center">
                <span className="text-cyan-400">{t('monitoring.diskIO').toUpperCase()}:</span>
                <span className="text-yellow-400 font-bold">{metrics.diskUsage}%</span>
              </div>
              <div className="text-green-400 text-xs mt-1">
                [{getBarGraph(metrics.diskUsage)}]
              </div>
            </div>
          </div>
          
          <div className="border-t border-green-400 pt-2 space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-green-300">{t('monitoring.connections').toUpperCase()}:</span>
              <span className="text-white font-bold">{metrics.activeConnections}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-green-300">{t('monitoring.msgPerSec').toUpperCase()}:</span>
              <span className="text-white font-bold">{metrics.messagesPerSecond}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-green-300">{t('monitoring.networkTraffic').toUpperCase()}:</span>
              <span className="text-white font-bold">{metrics.networkTraffic}KB/s</span>
            </div>
          </div>
          
          <div className="border-t border-green-400 pt-2">
            <div className="text-xs text-green-300" suppressHydrationWarning>
              » LAST UPDATE: {new Date().toLocaleTimeString('en-US', { hour12: false })}
            </div>
            <div className="text-xs text-green-300">
              » {t('common.status').toUpperCase()}: {t('common.operational').toUpperCase()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// 內部主頁面組件 - 使用設置上下文（支持多語言）
function HomePage() {
  const [currentTime, setCurrentTime] = useState<Date | null>(null);
  const [isClient, setIsClient] = useState(false);
  const { setIsSettingsOpen, fontSize } = useSettings();
  const { t } = useLanguage();

  useEffect(() => {
    setIsClient(true);
    setCurrentTime(new Date());
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 鍵盤快捷鍵支持
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl+, 打開設置
      if (event.ctrlKey && event.key === ',') {
        event.preventDefault();
        setIsSettingsOpen(true);
      }
      // ESC 關閉設置
      if (event.key === 'Escape') {
        setIsSettingsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [setIsSettingsOpen]);

  return (
    <div className="h-screen bg-black text-green-400 font-mono bbs-interface overflow-hidden" style={{ fontSize: `${fontSize}px` }}>
      {/* 設置按鈕 */}
      <button
        onClick={() => setIsSettingsOpen(true)}
        className="fixed top-4 left-4 z-30 bg-green-400 text-black px-2 py-1 font-bold hover:bg-green-300 border border-green-400 text-xs"
        title="Settings (Ctrl+,)"
      >
        [⚙] {t('common.settings').toUpperCase()}
      </button>
      
      {/* 語言選擇器 */}
      <div className="fixed top-4 right-4 z-30">
        <LanguageSelector />
      </div>
      
      {/* 設置菜單 */}
      <SettingsMenu />
      
      {/* BBS 標題區域 */}
      <div className="border-b-2 border-green-400 p-4">
        <div className="text-center">
          <div className="text-green-400 text-sm mb-2">
            ╔══════════════════════════════════════════════════════════════════════════════╗
          </div>
          <div className="text-green-400 text-sm">
            ║                                                                              ║
          </div>
          <div className="text-yellow-400 text-lg font-bold">
            ║                        {t('header.title')} v3.14                        ║
          </div>
          <div className="text-cyan-400 text-sm">
            ║                    {t('header.subtitle')}                     ║
          </div>
          <div className="text-green-400 text-sm">
            ║                                                                              ║
          </div>
          <div className="text-green-400 text-sm mb-2">
            ╚══════════════════════════════════════════════════════════════════════════════╝
          </div>
          <div className="text-green-300 text-xs">
            » {t('common.systemTime').toUpperCase()}: {isClient && currentTime ? currentTime.toLocaleString('en-US', { hour12: false }) : t('common.loading').toUpperCase()} | {t('common.online').toUpperCase()}: 42 | {t('common.status').toUpperCase()}: {t('common.operational').toUpperCase()}
          </div>
        </div>
      </div>

      {/* 主要內容區域 */}
      <div className="px-4 pb-4 h-[calc(100vh-220px)] overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full overflow-hidden">
          {/* 左側：文件上傳/下載區域 + 輸入區域 */}
          <div className="lg:col-span-1 h-full flex flex-col space-y-4 overflow-hidden">
            {/* 上方：文件上傳和報告下載 */}
            <div className="flex-1 min-h-0 overflow-hidden">
              <div className="grid grid-cols-2 gap-2 h-full">
                {/* 左側：文件上傳 */}
                <div className="overflow-hidden">
                  <FileUploadArea />
                </div>
                {/* 右側：報告下載 */}
                <div className="overflow-hidden">
                  <ReportDownloadCenter />
                </div>
              </div>
            </div>
            {/* 下方：多功能輸入區域 */}
            <div className="flex-shrink-0 h-48">
              <MultiInputArea />
            </div>
          </div>

          {/* 中間：辯論聊天室 */}
          <div className="lg:col-span-1 h-full overflow-hidden">
            <DebateChatRoom />
          </div>

          {/* 右側：狀態監控 */}
          <div className="lg:col-span-1 h-full flex flex-col space-y-4 overflow-hidden">
            <div className="flex-1 min-h-0 overflow-hidden">
              <LLMConnectionStatus />
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">
              <RealTimeMonitoring />
            </div>
          </div>
        </div>
      </div>
      
      {/* 底部狀態欄 */}
      <div className="fixed bottom-0 left-0 right-0 bg-green-400 text-black p-1">
        <div className="flex justify-between text-xs font-bold">
          <span>» F1-{t('footer.help').toUpperCase()} | F2-{t('footer.upload').toUpperCase()} | F3-{t('footer.chat').toUpperCase()} | F4-{t('footer.status').toUpperCase()} | CTRL+,-{t('common.settings').toUpperCase()} | F10-{t('footer.exit').toUpperCase()}</span>
          <span>» {t('footer.connectedTo').toUpperCase()}: AI-ANALYST-BBS.NET | {t('footer.font').toUpperCase()}: {fontSize}px</span>
        </div>
      </div>
    </div>
  );
}

// 主頁面組件 - 包裝設置和語言提供者
export default function MinimalistHomePage() {
  return (
    <SettingsProvider>
      <LanguageProvider>
        <HomePage />
      </LanguageProvider>
    </SettingsProvider>
  );
}
