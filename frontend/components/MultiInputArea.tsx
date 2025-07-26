'use client';

import React, { useState } from 'react';
import { useLanguage } from '../contexts/LanguageContext';

// 輸入模式類型
type InputMode = 'debate-prep' | 'report-review';

// 多功能輸入區域組件
export default function MultiInputArea() {
  const { t } = useLanguage();
  const [mode, setMode] = useState<InputMode>('debate-prep');
  const [inputText, setInputText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 處理模式切換
  const handleModeSwitch = () => {
    setMode(mode === 'debate-prep' ? 'report-review' : 'debate-prep');
    setInputText(''); // 切換模式時清空輸入
  };

  // 處理提交
  const handleSubmit = async () => {
    if (!inputText.trim()) return;
    
    setIsSubmitting(true);
    try {
      // 這裡可以添加實際的提交邏輯
      console.log(`Submitting ${mode}:`, inputText);
      
      // 模擬 API 調用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 提交成功後清空輸入
      setInputText('');
      
      // 可以添加成功提示
      alert(mode === 'debate-prep' ? '辯論需求已提交！' : '點評已提交！');
    } catch (error) {
      console.error('Submit error:', error);
      alert('提交失敗，請重試');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 處理清空
  const handleClear = () => {
    setInputText('');
  };

  // 獲取當前模式的標題和佔位符
  const getModeConfig = () => {
    if (mode === 'debate-prep') {
      return {
        title: t('inputArea.modeDebatePrep'),
        placeholder: t('inputArea.placeholder.debatePrep'),
        icon: '🎯'
      };
    } else {
      return {
        title: t('inputArea.modeReportReview'),
        placeholder: t('inputArea.placeholder.reportReview'),
        icon: '📝'
      };
    }
  };

  const modeConfig = getModeConfig();

  return (
    <div className="p-2 bg-black text-green-400 font-mono text-sm h-full">
      <div className="border border-green-400 h-full flex flex-col">
        {/* 標題欄 */}
        <div className="bg-green-400 text-black px-2 py-1 text-center font-bold flex-shrink-0">
          ╔══════════════════════════════════════╗
        </div>
        <div className="bg-green-400 text-black px-2 py-0 text-center font-bold flex-shrink-0">
          ║        {t('inputArea.title')}        ║
        </div>
        <div className="bg-green-400 text-black px-2 py-1 text-center font-bold flex-shrink-0">
          ╚══════════════════════════════════════╝
        </div>
        
        {/* 模式切換區域 */}
        <div className="p-3 border-b border-green-400 flex-shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className="text-cyan-400 text-xs">» {t('common.status')}:</span>
              <span className="text-yellow-400 font-bold text-xs">
                {modeConfig.icon} {modeConfig.title}
              </span>
            </div>
            <button
              onClick={handleModeSwitch}
              className="bg-cyan-400 text-black px-2 py-1 text-xs font-bold hover:bg-cyan-300 border border-cyan-400"
              title={t('inputArea.switchMode')}
            >
              [{t('inputArea.switchMode')}]
            </button>
          </div>
          
          {/* 模式指示器 */}
          <div className="flex space-x-1 text-xs">
            <div className={`px-2 py-1 border ${
              mode === 'debate-prep' 
                ? 'bg-green-400 text-black border-green-400' 
                : 'text-green-400 border-green-400'
            }`}>
              🎯 {t('inputArea.modeDebatePrep')}
            </div>
            <div className={`px-2 py-1 border ${
              mode === 'report-review' 
                ? 'bg-green-400 text-black border-green-400' 
                : 'text-green-400 border-green-400'
            }`}>
              📝 {t('inputArea.modeReportReview')}
            </div>
          </div>
        </div>
        
        {/* 輸入區域 */}
        <div className="p-3 flex-1 flex flex-col min-h-0">
          <div className="text-green-300 text-xs mb-2">
            *** {modeConfig.title.toUpperCase()} ***
          </div>
          
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={modeConfig.placeholder}
            className="flex-1 bg-black text-green-400 border border-green-400 p-2 text-xs font-mono resize-none focus:outline-none focus:border-cyan-400 min-h-0"
            disabled={isSubmitting}
          />
          
          {/* 字符計數 */}
          <div className="text-green-300 text-xs mt-1 text-right">
            » {t('common.loading').replace('...', '')}: {inputText.length} chars
          </div>
        </div>
        
        {/* 操作按鈕區域 */}
        <div className="p-3 border-t border-green-400 flex-shrink-0">
          <div className="flex space-x-2">
            <button
              onClick={handleSubmit}
              disabled={!inputText.trim() || isSubmitting}
              className={`flex-1 px-3 py-2 text-xs font-bold border ${
                !inputText.trim() || isSubmitting
                  ? 'bg-gray-600 text-gray-400 border-gray-600 cursor-not-allowed'
                  : 'bg-green-400 text-black border-green-400 hover:bg-green-300'
              }`}
            >
              {isSubmitting ? '⏳ ' + t('common.loading') : '📤 ' + t('inputArea.submit')}
            </button>
            
            <button
              onClick={handleClear}
              disabled={!inputText || isSubmitting}
              className={`px-3 py-2 text-xs font-bold border ${
                !inputText || isSubmitting
                  ? 'bg-gray-600 text-gray-400 border-gray-600 cursor-not-allowed'
                  : 'bg-red-600 text-white border-red-600 hover:bg-red-500'
              }`}
              title={t('inputArea.clear')}
            >
              🗑️ {t('inputArea.clear')}
            </button>
          </div>
          
          {/* 快捷鍵提示 */}
          <div className="text-green-300 text-xs mt-2 text-center">
            » CTRL+ENTER: {t('inputArea.submit')} | ESC: {t('inputArea.clear')} | TAB: {t('inputArea.switchMode')}
          </div>
        </div>
      </div>
    </div>
  );
}