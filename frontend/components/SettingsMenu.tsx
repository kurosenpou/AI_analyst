'use client';

import React from 'react';
import { useSettings } from '../contexts/SettingsContext';

const SettingsMenu: React.FC = () => {
  const { fontSize, setFontSize, isSettingsOpen, setIsSettingsOpen } = useSettings();

  if (!isSettingsOpen) return null;

  return (
    <>
      {/* 背景遮罩 */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={() => setIsSettingsOpen(false)}
      />
      
      {/* 設置菜單 */}
      <div className="fixed left-4 top-1/2 transform -translate-y-1/2 z-50 bg-black border-2 border-green-400 font-mono text-green-400">
        <div className="w-80">
          {/* 標題欄 */}
          <div className="bg-green-400 text-black px-3 py-1 font-bold text-center">
            ╔══════════════════════════════════════╗
          </div>
          <div className="bg-green-400 text-black px-3 py-0 font-bold text-center">
            ║            SYSTEM SETTINGS           ║
          </div>
          <div className="bg-green-400 text-black px-3 py-1 font-bold text-center">
            ╚══════════════════════════════════════╝
          </div>
          
          {/* 設置內容 */}
          <div className="p-4 space-y-4">
            <div className="text-green-300 text-xs mb-3">
              *** DISPLAY CONFIGURATION ***
            </div>
            
            {/* 字體大小設置 */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-cyan-400">FONT SIZE:</span>
                <span className="text-yellow-400 font-bold">{fontSize}px</span>
              </div>
              
              <div className="space-y-2">
                <input
                  type="range"
                  min="10"
                  max="24"
                  value={fontSize}
                  onChange={(e) => setFontSize(parseInt(e.target.value))}
                  className="w-full h-2 bg-green-900 rounded-lg appearance-none cursor-pointer slider"
                  style={{
                    background: `linear-gradient(to right, #22c55e 0%, #22c55e ${((fontSize - 10) / 14) * 100}%, #166534 ${((fontSize - 10) / 14) * 100}%, #166534 100%)`
                  }}
                />
                <div className="flex justify-between text-xs text-green-300">
                  <span>10px</span>
                  <span>17px</span>
                  <span>24px</span>
                </div>
              </div>
              
              {/* 預覽文字 */}
              <div className="border border-green-400 p-2 mt-3">
                <div className="text-green-300 text-xs mb-1">» PREVIEW:</div>
                <div 
                  className="text-green-400"
                  style={{ fontSize: `${fontSize}px` }}
                >
                  [SAMPLE] AI ANALYST BBS TERMINAL
                </div>
                <div 
                  className="text-cyan-400 text-xs mt-1"
                  style={{ fontSize: `${fontSize * 0.8}px` }}
                >
                  &gt; System ready for data analysis...
                </div>
              </div>
            </div>
            
            {/* 快捷鍵提示 */}
            <div className="border-t border-green-400 pt-3 mt-4">
              <div className="text-green-300 text-xs mb-2">
                *** KEYBOARD SHORTCUTS ***
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-cyan-400">[CTRL+,]</span>
                  <span className="text-green-400">Open Settings</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-cyan-400">[ESC]</span>
                  <span className="text-green-400">Close Menu</span>
                </div>
              </div>
            </div>
            
            {/* 關閉按鈕 */}
            <div className="text-center pt-3">
              <button
                onClick={() => setIsSettingsOpen(false)}
                className="bg-green-400 text-black px-6 py-1 font-bold hover:bg-green-300 border-2 border-green-400 text-xs"
              >
                [ESC] CLOSE SETTINGS
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default SettingsMenu;