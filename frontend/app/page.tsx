'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { Upload, Wifi, WifiOff, Circle, Square } from 'lucide-react';

// 文件上傳組件
const FileUploadArea = () => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    setUploadedFiles(prev => [...prev, ...files]);
    toast.success(`已上傳 ${files.length} 個文件`);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setUploadedFiles(prev => [...prev, ...files]);
    toast.success(`已上傳 ${files.length} 個文件`);
  };

  return (
    <div className="h-full p-4">
      <motion.div
        className={`h-full border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-colors ${
          isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <Upload className="w-12 h-12 text-gray-400 mb-4" />
        <p className="text-gray-600 text-center">
          點擊或拖拽文件至此處上傳
        </p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileSelect}
        />
      </motion.div>
      
      {uploadedFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          <h3 className="text-sm font-medium text-gray-700">已上傳文件:</h3>
          {uploadedFiles.map((file, index) => (
            <div key={index} className="text-xs text-gray-600 truncate">
              {file.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// LLM辯論聊天室組件
const DebateChatRoom = () => {
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
      const speakers = ['GPT-4', 'Claude-3', '裁判'];
      const contents = [
        '我認為這個數據分析結果顯示了明顯的趨勢...',
        '但是我們需要考慮到樣本偏差的問題...',
        '雙方觀點都有道理，讓我們深入分析...',
        '從統計學角度來看...',
        '這個結論需要更多證據支持...'
      ];
      
      const newMessage = {
        id: Date.now().toString(),
        speaker: speakers[Math.floor(Math.random() * speakers.length)],
        content: contents[Math.floor(Math.random() * contents.length)],
        timestamp: new Date(),
        type: Math.random() > 0.7 ? 'judge' : 'debate' as 'debate' | 'judge' | 'system'
      };
      
      setMessages(prev => [...prev.slice(-20), newMessage]);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="h-full p-4 flex flex-col">
      <h3 className="text-lg font-medium text-gray-800 mb-4">LLM辯論實況</h3>
      <div className="flex-1 min-h-0 overflow-y-auto space-y-3 max-h-96">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`p-3 rounded-lg ${
                message.type === 'judge' 
                  ? 'bg-yellow-50 border-l-4 border-yellow-400'
                  : 'bg-gray-50 border-l-4 border-blue-400'
              }`}
            >
              <div className="flex justify-between items-start mb-1">
                <span className={`font-medium text-sm ${
                  message.type === 'judge' ? 'text-yellow-700' : 'text-blue-700'
                }`}>
                  {message.speaker}
                </span>
                <span className="text-xs text-gray-500">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <p className="text-sm text-gray-700">{message.content}</p>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={chatEndRef} />
      </div>
    </div>
  );
};

// LLM連接狀態組件
const LLMConnectionStatus = () => {
  const [llmStatus, setLlmStatus] = useState({
    'GPT-4': { connected: true, role: 'debater1' },
    'Claude-3': { connected: true, role: 'debater2' },
    'Gemini': { connected: false, role: 'judge' }
  });

  useEffect(() => {
    // 模擬連接狀態變化
    const interval = setInterval(() => {
      setLlmStatus(prev => {
        const models = Object.keys(prev);
        const randomModel = models[Math.floor(Math.random() * models.length)];
        return {
          ...prev,
          [randomModel]: {
            ...prev[randomModel as keyof typeof prev],
            connected: Math.random() > 0.3
          }
        };
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getRoleIcon = (role: string) => {
    if (role === 'judge') return <Circle className="w-3 h-3 text-green-500 fill-current" />;
    if (role === 'debater1') return <Square className="w-3 h-3 text-red-500 fill-current" />;
    if (role === 'debater2') return <Square className="w-3 h-3 text-blue-500 fill-current" />;
    return null;
  };

  return (
    <div className="h-full p-4">
      <h3 className="text-lg font-medium text-gray-800 mb-4">LLM狀態</h3>
      <div className="grid grid-cols-2 gap-4">
        {Object.entries(llmStatus).map(([model, status], index) => (
          <motion.div
            key={model}
            className={`p-4 rounded-lg border-2 transition-colors ${
              status.connected ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'
            } ${index === 2 ? 'col-span-2' : ''}`}
            whileHover={{ scale: 1.05 }}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-gray-800">{model}</span>
              {status.connected ? (
                <Wifi className="w-4 h-4 text-green-500" />
              ) : (
                <WifiOff className="w-4 h-4 text-red-500" />
              )}
            </div>
            <div className="flex items-center space-x-2">
              {getRoleIcon(status.role)}
              <span className="text-sm text-gray-600">
                {status.role === 'judge' ? '裁判' : 
                 status.role === 'debater1' ? '辯方A' : '辯方B'}
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// 實時監控組件
const RealTimeMonitoring = () => {
  const [metrics, setMetrics] = useState({
    activeDebates: 1,
    totalRequests: 0,
    avgResponseTime: 0,
    systemLoad: 0
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        activeDebates: Math.floor(Math.random() * 3) + 1,
        totalRequests: prev.totalRequests + Math.floor(Math.random() * 5),
        avgResponseTime: Math.floor(Math.random() * 1000) + 500,
        systemLoad: Math.floor(Math.random() * 100)
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-full p-4">
      <h3 className="text-lg font-medium text-gray-800 mb-4">實時監控</h3>
      <div className="space-y-4">
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="text-sm text-gray-600">活躍辯論</div>
          <div className="text-2xl font-bold text-blue-600">{metrics.activeDebates}</div>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="text-sm text-gray-600">總請求數</div>
          <div className="text-2xl font-bold text-green-600">{metrics.totalRequests}</div>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="text-sm text-gray-600">平均響應時間</div>
          <div className="text-2xl font-bold text-orange-600">{metrics.avgResponseTime}ms</div>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="text-sm text-gray-600">系統負載</div>
          <div className="text-2xl font-bold text-purple-600">{metrics.systemLoad}%</div>
        </div>
      </div>
    </div>
  );
};

// 主頁面組件
export default function MinimalistHomePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* 頂部標題 */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 px-6 shadow-lg">
        <h1 className="text-2xl font-bold text-center">AI董事會（alpha測試版）</h1>
      </div>
      
      {/* 主要內容區域 */}
      <div className="h-[calc(100vh-4rem)] grid grid-cols-2 gap-1">
        {/* 左側區域 */}
        <div className="grid grid-rows-2 gap-1">
          {/* 左上：文件上傳 */}
          <div className="bg-white border border-gray-200">
            <FileUploadArea />
          </div>
          
          {/* 左下：LLM辯論聊天室 */}
          <div className="bg-white border border-gray-200">
            <DebateChatRoom />
          </div>
        </div>
        
        {/* 右側區域 */}
        <div className="grid grid-rows-2 gap-1">
          {/* 右上：LLM連接狀態 */}
          <div className="bg-white border border-gray-200">
            <LLMConnectionStatus />
          </div>
          
          {/* 右下：實時監控 */}
          <div className="bg-white border border-gray-200">
            <RealTimeMonitoring />
          </div>
        </div>
      </div>
    </div>
  );
}
