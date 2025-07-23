'use client'

import { useState, useEffect, useRef } from 'react'
import { uploadFile, generateBusinessReport } from '../lib/api'

interface TerminalLine {
  id: number
  content: string
  type: 'normal' | 'success' | 'error' | 'warning' | 'info' | 'prompt'
}

export default function HomePage() {
  const [lines, setLines] = useState<TerminalLine[]>([
    { id: 0, content: '請將需要分析的文件拖拽進畫面中', type: 'info' }
  ])
  const [currentInput, setCurrentInput] = useState('')
  const [isWaitingForInput, setIsWaitingForInput] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [reportModalOpen, setReportModalOpen] = useState(false)
  const [generatedReport, setGeneratedReport] = useState('')
  const [uploadedFile, setUploadedFile] = useState<any>(null)
  const [progress, setProgress] = useState(0)
  const [currentModel, setCurrentModel] = useState('GPT-4')
  
  const inputRef = useRef<HTMLInputElement>(null)
  const terminalRef = useRef<HTMLDivElement>(null)

  const addLine = (content: string, type: TerminalLine['type'] = 'normal') => {
    setLines(prev => [...prev, { id: Date.now(), content, type }])
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length === 0) return

    const file = files[0]
    addLine(`> 檢測到文件: ${file.name}`, 'success')
    addLine('> 對即將生成的報告，是否有特殊的要求？（按回車跳過）', 'prompt')
    
    setUploadedFile(file)
    setIsWaitingForInput(true)
    
    // Focus input for user to type
    setTimeout(() => {
      inputRef.current?.focus()
    }, 100)
  }

  const handleInputSubmit = async (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && isWaitingForInput) {
      e.preventDefault()
      
      const userRequirement = currentInput.trim()
      if (userRequirement) {
        addLine(`> ${userRequirement}`, 'normal')
        addLine('> 已記錄您的要求', 'success')
      } else {
        addLine('> 跳過特殊要求', 'info')
      }
      
      setCurrentInput('')
      setIsWaitingForInput(false)
      
      // Start processing
      await startProcessing(userRequirement)
    }
  }

  const startProcessing = async (userRequirement: string) => {
    setIsProcessing(true)
    
    try {
      addLine(`> 開始處理...`, 'info')
      addLine(`> 使用模型: ${currentModel}`, 'info')
      
      // Upload file
      setProgress(25)
      addLine('> [1/4] 正在上傳文件...', 'info')
      const uploadResponse = await uploadFile(uploadedFile)
      
      setProgress(50)
      addLine('> [2/4] 正在解析數據...', 'info')
      await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate processing
      
      setProgress(75)
      addLine('> [3/4] 正在生成報告...', 'info')
      const reportResponse = await generateBusinessReport(
        uploadResponse.data.file_id,
        'business_plan',
        userRequirement || undefined
      )
      
      setProgress(100)
      addLine('> [4/4] 報告生成完成！', 'success')
      addLine('> ✓ 工作完成', 'success')
      addLine('> 提示: 點擊左上角菜單按鈕查看生成的報告', 'info')
      
      setGeneratedReport(reportResponse.data.content)
      
    } catch (error: any) {
      addLine(`> ✗ 錯誤: ${error.message}`, 'error')
    } finally {
      setIsProcessing(false)
      setProgress(0)
    }
  }

  const getLineClass = (type: TerminalLine['type']) => {
    switch (type) {
      case 'success': return 'terminal-success'
      case 'error': return 'terminal-error'
      case 'warning': return 'terminal-warning'
      case 'info': return 'terminal-info'
      case 'prompt': return 'terminal-info'
      default: return ''
    }
  }

  // Auto scroll to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [lines])

  return (
    <>
      {/* Sidebar Toggle */}
      <button 
        className="sidebar-toggle"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        ☰ 菜單
      </button>

      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-content">
          <div className="sidebar-section">
            <div className="sidebar-title">報告管理</div>
            <div 
              className="sidebar-item"
              onClick={() => {
                if (generatedReport) {
                  setReportModalOpen(true)
                  setSidebarOpen(false)
                } else {
                  alert('尚未生成報告')
                }
              }}
            >
              查看最新報告
            </div>
            <div className="sidebar-item" onClick={() => window.location.reload()}>
              重新開始
            </div>
          </div>
          
          <div className="sidebar-section">
            <div className="sidebar-title">設置</div>
            <div className="sidebar-item">
              模型: {currentModel}
            </div>
            <div className="sidebar-item">
              版本: v1.0.0
            </div>
          </div>
          
          <div className="sidebar-section">
            <div className="sidebar-title">幫助</div>
            <div className="sidebar-item">
              支持的格式: CSV, PDF, Excel
            </div>
            <div className="sidebar-item">
              最大文件大小: 10MB
            </div>
          </div>
        </div>
      </div>

      {/* Main Terminal */}
      <div 
        className="terminal-container"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="terminal-header">
          AI Business Agent MVP - Terminal Interface
        </div>
        
        <div ref={terminalRef} style={{ height: 'calc(100vh - 120px)', overflowY: 'auto' }}>
          {lines.map((line) => (
            <div key={line.id} className={`terminal-output ${getLineClass(line.type)}`}>
              {line.content}
            </div>
          ))}
          
          {isWaitingForInput && (
            <div className="terminal-output">
              <span className="terminal-prompt">$ </span>
              <input
                ref={inputRef}
                type="text"
                className="terminal-input"
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onKeyDown={handleInputSubmit}
                placeholder="輸入您的要求或按回車跳過..."
              />
              <span className="terminal-cursor">_</span>
            </div>
          )}
          
          {isProcessing && progress > 0 && (
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="terminal-output terminal-info">
                進度: {progress}%
              </div>
            </div>
          )}
        </div>

        {/* Drop zone overlay */}
        {dragActive && (
          <div className="drop-zone active">
            <div style={{ 
              position: 'absolute', 
              top: '50%', 
              left: '50%', 
              transform: 'translate(-50%, -50%)',
              color: '#4caf50',
              fontSize: '18px',
              textAlign: 'center'
            }}>
              <div>松開以上傳文件</div>
              <div style={{ marginTop: '10px', fontSize: '14px' }}>
                支持 CSV, PDF, Excel 格式
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Report Modal */}
      {reportModalOpen && (
        <div className="modal-overlay" onClick={() => setReportModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button 
              className="modal-close"
              onClick={() => setReportModalOpen(false)}
            >
              ×
            </button>
            <h2 style={{ color: '#4fc3f7', marginBottom: '20px' }}>生成的報告</h2>
            <div className="report-content">
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                {generatedReport}
              </pre>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
