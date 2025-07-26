'use client';

import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';

// 報告類型定義
interface Report {
  id: string;
  name: string;
  type: 'analysis' | 'debate' | 'summary';
  size: string;
  createdAt: string;
  status: 'ready' | 'generating' | 'error';
}

// 報告下載中心組件
export default function ReportDownloadCenter() {
  const { t } = useLanguage();
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  // 模擬加載報告列表
  useEffect(() => {
    const loadReports = async () => {
      setIsLoading(true);
      try {
        // 模擬 API 調用
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 模擬報告數據
        const mockReports: Report[] = [
          {
            id: '1',
            name: 'Data_Analysis_Report_2025.pdf',
            type: 'analysis',
            size: '2.3 MB',
            createdAt: '2025-01-25 14:30',
            status: 'ready'
          },
          {
            id: '2',
            name: 'AI_Debate_Summary_v1.docx',
            type: 'debate',
            size: '1.8 MB',
            createdAt: '2025-01-25 13:45',
            status: 'ready'
          },
          {
            id: '3',
            name: 'Executive_Summary_Q1.pdf',
            type: 'summary',
            size: '0.9 MB',
            createdAt: '2025-01-25 12:15',
            status: 'generating'
          }
        ];
        
        setReports(mockReports);
      } catch (error) {
        console.error('Error loading reports:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadReports();
  }, []);

  // 處理報告下載
  const handleDownload = async (report: Report) => {
    if (report.status !== 'ready') return;
    
    setDownloadingId(report.id);
    try {
      // 模擬下載過程
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // 這裡可以添加實際的下載邏輯
      console.log('Downloading report:', report.name);
      
      // 創建模擬下載
      const link = document.createElement('a');
      link.href = '#'; // 實際應用中這裡應該是報告的 URL
      link.download = report.name;
      link.click();
      
    } catch (error) {
      console.error('Download error:', error);
      alert(t('reportDownload.downloadError'));
    } finally {
      setDownloadingId(null);
    }
  };

  // 獲取報告類型圖標
  const getReportIcon = (type: Report['type']) => {
    switch (type) {
      case 'analysis': return '📊';
      case 'debate': return '💬';
      case 'summary': return '📋';
      default: return '📄';
    }
  };

  // 獲取狀態圖標和文本
  const getStatusDisplay = (status: Report['status']) => {
    switch (status) {
      case 'ready': return { icon: '✅', text: t('common.operational'), color: 'text-green-400' };
      case 'generating': return { icon: '⏳', text: t('reportDownload.generating'), color: 'text-yellow-400' };
      case 'error': return { icon: '❌', text: t('common.offline'), color: 'text-red-400' };
      default: return { icon: '❓', text: 'Unknown', color: 'text-gray-400' };
    }
  };

  return (
    <div className="p-2 bg-black text-green-400 font-mono text-sm h-full">
      <div className="border border-green-400 h-full flex flex-col">
        {/* 標題欄 */}
        <div className="bg-green-400 text-black px-2 py-1 text-center font-bold flex-shrink-0">
          ╔══════════════════════════════════════╗
        </div>
        <div className="bg-green-400 text-black px-2 py-0 text-center font-bold flex-shrink-0">
          ║      {t('reportDownload.title')}     ║
        </div>
        <div className="bg-green-400 text-black px-2 py-1 text-center font-bold flex-shrink-0">
          ╚══════════════════════════════════════╝
        </div>
        
        {/* 狀態信息 */}
        <div className="p-3 border-b border-green-400 flex-shrink-0">
          <div className="text-green-300 text-xs mb-2">
            *** {t('reportDownload.availableReports').toUpperCase()} ***
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-cyan-400">» {t('common.status')}:</span>
            <span className="text-yellow-400 font-bold">
              {isLoading ? t('common.loading') : `${reports.length} REPORTS`}
            </span>
          </div>
        </div>
        
        {/* 報告列表 */}
        <div className="flex-1 overflow-y-auto min-h-0">
          {isLoading ? (
            <div className="p-4 text-center">
              <div className="text-yellow-400 text-xs mb-2">⏳ {t('common.loading')}</div>
              <div className="text-green-300 text-xs">» SCANNING REPORT DATABASE...</div>
            </div>
          ) : reports.length === 0 ? (
            <div className="p-4 text-center">
              <div className="text-gray-400 text-xs mb-2">📭 {t('reportDownload.noReports')}</div>
              <div className="text-green-300 text-xs">» GENERATE REPORTS TO SEE THEM HERE</div>
            </div>
          ) : (
            <div className="p-2 space-y-2">
              {reports.map((report) => {
                const status = getStatusDisplay(report.status);
                const isDownloading = downloadingId === report.id;
                
                return (
                  <div key={report.id} className="border border-green-400 p-2">
                    <div className="flex items-start justify-between mb-1">
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <span className="text-lg">{getReportIcon(report.type)}</span>
                        <div className="flex-1 min-w-0">
                          <div className="text-cyan-400 text-xs font-bold truncate" title={report.name}>
                            {report.name}
                          </div>
                          <div className="text-green-300 text-xs">
                            {report.size} | {report.createdAt}
                          </div>
                        </div>
                      </div>
                      <div className={`text-xs ${status.color} flex items-center space-x-1`}>
                        <span>{status.icon}</span>
                        <span>{status.text}</span>
                      </div>
                    </div>
                    
                    <div className="flex space-x-2 mt-2">
                      <button
                        onClick={() => handleDownload(report)}
                        disabled={report.status !== 'ready' || isDownloading}
                        className={`flex-1 px-2 py-1 text-xs font-bold border ${
                          report.status !== 'ready' || isDownloading
                            ? 'bg-gray-600 text-gray-400 border-gray-600 cursor-not-allowed'
                            : 'bg-blue-600 text-white border-blue-600 hover:bg-blue-500'
                        }`}
                      >
                        {isDownloading ? '⬇️ ' + t('common.loading') : '📥 ' + t('reportDownload.downloadReport')}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
        
        {/* 底部信息 */}
        <div className="p-2 border-t border-green-400 flex-shrink-0">
          <div className="text-green-300 text-xs text-center">
            » F2: {t('common.download')} | F5: REFRESH | CTRL+R: RELOAD
          </div>
        </div>
      </div>
    </div>
  );
}