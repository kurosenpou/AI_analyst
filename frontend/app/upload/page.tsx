'use client'

import { useState, useEffect } from 'react'
import { uploadFile, generateBusinessReport } from '../../lib/api'

interface ProcessingStep {
  id: number
  name: string
  status: 'pending' | 'running' | 'complete' | 'error'
  message?: string
}

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [reportType, setReportType] = useState<string>('business_plan')
  const [requirements, setRequirements] = useState<string>('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [steps, setSteps] = useState<ProcessingStep[]>([
    { id: 1, name: '上傳文件', status: 'pending' },
    { id: 2, name: '解析數據', status: 'pending' },
    { id: 3, name: '生成報告', status: 'pending' },
    { id: 4, name: '完成', status: 'pending' }
  ])
  const [report, setReport] = useState<string>('')
  const [showReport, setShowReport] = useState(false)
  const [terminalOutput, setTerminalOutput] = useState<string[]>([
    '$ AI Business Agent Terminal v1.0.0',
    '$ 歡迎使用 AI 商業報告生成器',
    '$ 請上傳您的業務數據文件'
  ])

  const addTerminalLine = (line: string) => {
    setTerminalOutput(prev => [...prev, line])
  }

  const updateStep = (stepId: number, status: ProcessingStep['status'], message?: string) => {
    setSteps(prev => prev.map(step => 
      step.id === stepId ? { ...step, status, message } : step
    ))
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      addTerminalLine(`> 已選擇文件: ${selectedFile.name}`)
      addTerminalLine(`> 文件大小: ${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`)
      
      const fileType = selectedFile.name.split('.').pop()?.toLowerCase()
      if (['csv', 'pdf', 'xlsx', 'xls'].includes(fileType || '')) {
        addTerminalLine(`> 文件格式檢查: ✓ ${fileType?.toUpperCase()}`)
      } else {
        addTerminalLine(`> 文件格式檢查: ⚠ 不支持的格式`)
      }
    }
  }

  const handleSubmit = async () => {
    if (!file) {
      addTerminalLine('> 錯誤: 請先選擇文件')
      return
    }

    setIsProcessing(true)
    addTerminalLine('> 開始處理...')
    addTerminalLine(`> 報告類型: ${getReportTypeName(reportType)}`)
    
    if (requirements.trim()) {
      addTerminalLine(`> 特殊要求: ${requirements}`)
    }

    try {
      // Step 1: Upload file
      updateStep(1, 'running')
      addTerminalLine('> [1/4] 正在上傳文件...')
      
      const uploadResponse = await uploadFile(file)
      updateStep(1, 'complete', '文件上傳成功')
      addTerminalLine('> [1/4] ✓ 文件上傳完成')

      // Step 2: Parse data
      updateStep(2, 'running')
      addTerminalLine('> [2/4] 正在解析數據...')
      
      // Simulate parsing delay
      await new Promise(resolve => setTimeout(resolve, 2000))
      updateStep(2, 'complete', '數據解析完成')
      addTerminalLine('> [2/4] ✓ 數據解析完成')

      // Step 3: Generate report
      updateStep(3, 'running')
      addTerminalLine('> [3/4] 正在生成報告...')
      addTerminalLine('> 使用 GPT-4 模型進行分析...')
      
      const reportResponse = await generateBusinessReport(
        uploadResponse.data.file_id,
        reportType as 'business_plan' | 'market_report' | 'investment_summary',
        requirements || undefined
      )
      
      updateStep(3, 'complete', '報告生成完成')
      addTerminalLine('> [3/4] ✓ 報告生成完成')
      
      // Step 4: Complete
      updateStep(4, 'complete', '所有任務完成')
      addTerminalLine('> [4/4] ✓ 所有任務完成')
      addTerminalLine('> 報告已準備就緒')
      
      setReport(reportResponse.data.content)
      
    } catch (error: any) {
      const currentStep = steps.find(s => s.status === 'running')?.id || 1
      updateStep(currentStep, 'error', error.message)
      addTerminalLine(`> ✗ 錯誤: ${error.message}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const getReportTypeName = (type: string) => {
    switch (type) {
      case 'business_plan': return '商業計劃書'
      case 'market_report': return '市場分析報告'
      case 'investment_summary': return '投資建議書'
      default: return type
    }
  }

  const getStepStatusIcon = (status: ProcessingStep['status']) => {
    switch (status) {
      case 'complete': return '✓'
      case 'running': return '⟲'
      case 'error': return '✗'
      default: return '○'
    }
  }

  const getStepStatusClass = (status: ProcessingStep['status']) => {
    switch (status) {
      case 'complete': return 'terminal-success'
      case 'running': return 'terminal-info'
      case 'error': return 'terminal-error'
      default: return ''
    }
  }

  return (
    <div className="terminal-container">
      <div className="terminal-header">
        AI Business Agent - 文件上傳與報告生成
      </div>

      <div style={{ height: 'calc(100vh - 60px)', display: 'flex' }}>
        {/* Left Panel - Controls */}
        <div style={{ 
          width: '40%', 
          padding: '20px', 
          borderRight: '1px solid #333',
          overflowY: 'auto'
        }}>
          <div className="terminal-output terminal-info">
            {'>'} 配置選項
          </div>

          {/* File Upload */}
          <div style={{ marginBottom: '20px' }}>
            <div className="terminal-output">
              文件選擇:
            </div>
            <input
              type="file"
              accept=".csv,.pdf,.xlsx,.xls"
              onChange={handleFileChange}
              style={{
                width: '100%',
                padding: '8px',
                background: '#1e1e1e',
                border: '1px solid #444',
                color: '#ffffff',
                borderRadius: '4px',
                fontFamily: 'Consolas, Monaco, monospace'
              }}
            />
          </div>

          {/* Report Type */}
          <div style={{ marginBottom: '20px' }}>
            <div className="terminal-output">
              報告類型:
            </div>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                background: '#1e1e1e',
                border: '1px solid #444',
                color: '#ffffff',
                borderRadius: '4px',
                fontFamily: 'Consolas, Monaco, monospace'
              }}
            >
              <option value="business_plan">商業計劃書</option>
              <option value="market_report">市場分析報告</option>
              <option value="investment_summary">投資建議書</option>
            </select>
          </div>

          {/* Requirements */}
          <div style={{ marginBottom: '20px' }}>
            <div className="terminal-output">
              特殊要求 (可選):
            </div>
            <textarea
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder="請描述您對報告的特殊要求..."
              rows={4}
              style={{
                width: '100%',
                padding: '8px',
                background: '#1e1e1e',
                border: '1px solid #444',
                color: '#ffffff',
                borderRadius: '4px',
                fontFamily: 'Consolas, Monaco, monospace',
                resize: 'vertical'
              }}
            />
          </div>

          {/* Generate Button */}
          <button
            onClick={handleSubmit}
            disabled={!file || isProcessing}
            style={{
              width: '100%',
              padding: '12px',
              background: file && !isProcessing ? '#4fc3f7' : '#666',
              color: '#000',
              border: 'none',
              borderRadius: '4px',
              fontFamily: 'Consolas, Monaco, monospace',
              fontWeight: 'bold',
              cursor: file && !isProcessing ? 'pointer' : 'not-allowed'
            }}
          >
            {isProcessing ? '處理中...' : '生成報告'}
          </button>

          {/* Processing Steps */}
          {(isProcessing || steps.some(s => s.status === 'complete')) && (
            <div style={{ marginTop: '20px' }}>
              <div className="terminal-output terminal-info">
                {'>'} 處理進度
              </div>
              {steps.map((step) => (
                <div 
                  key={step.id} 
                  className={`terminal-output ${getStepStatusClass(step.status)}`}
                >
                  {getStepStatusIcon(step.status)} [{step.id}/4] {step.name}
                  {step.message && (
                    <div style={{ marginLeft: '20px', fontSize: '12px' }}>
                      {step.message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* View Report Button */}
          {report && (
            <button
              onClick={() => setShowReport(true)}
              style={{
                width: '100%',
                padding: '12px',
                background: '#4caf50',
                color: '#000',
                border: 'none',
                borderRadius: '4px',
                fontFamily: 'Consolas, Monaco, monospace',
                fontWeight: 'bold',
                cursor: 'pointer',
                marginTop: '10px'
              }}
            >
              查看生成的報告
            </button>
          )}
        </div>

        {/* Right Panel - Terminal Output */}
        <div style={{ 
          width: '60%', 
          padding: '20px',
          overflowY: 'auto'
        }}>
          <div className="terminal-output terminal-info">
            {'>'} 系統日誌
          </div>
          {terminalOutput.map((line, index) => (
            <div key={index} className="terminal-output">
              {line}
            </div>
          ))}
        </div>
      </div>

      {/* Report Modal */}
      {showReport && (
        <div className="modal-overlay" onClick={() => setShowReport(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button 
              className="modal-close"
              onClick={() => setShowReport(false)}
            >
              ×
            </button>
            <h2 style={{ color: '#4fc3f7', marginBottom: '20px' }}>
              {getReportTypeName(reportType)}
            </h2>
            <div className="report-content">
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                {report}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
