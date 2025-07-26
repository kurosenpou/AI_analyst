'use client'

import { useState, useCallback, useRef } from 'react'
import { uploadFile } from '../lib/api'

interface FileWithPreview {
  file: File
  id: string
  preview?: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
}

interface EnhancedFileUploadProps {
  onFilesUploaded: (files: FileWithPreview[]) => void
  onError: (error: string) => void
  maxFiles?: number
  maxSize?: number // in MB
  acceptedTypes?: string[]
  disabled?: boolean
  className?: string
  theme?: 'light' | 'dark' | 'auto'
}

export default function EnhancedFileUpload({
  onFilesUploaded,
  onError,
  maxFiles = 5,
  maxSize = 10,
  acceptedTypes = ['csv', 'pdf', 'xlsx', 'xls'],
  disabled = false,
  className = '',
  theme = 'auto'
}: EnhancedFileUploadProps) {
  const [files, setFiles] = useState<FileWithPreview[]>([])
  const [dragActive, setDragActive] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxSize * 1024 * 1024) {
      return `文件大小超過 ${maxSize}MB 限制`
    }

    // Check file type
    const extension = file.name.split('.').pop()?.toLowerCase()
    if (!extension || !acceptedTypes.includes(extension)) {
      return `不支持的文件格式。支持的格式：${acceptedTypes.join(', ')}`
    }

    return null
  }

  const generatePreview = (file: File): Promise<string | undefined> => {
    return new Promise((resolve) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = (e) => resolve(e.target?.result as string)
        reader.readAsDataURL(file)
      } else {
        resolve(undefined)
      }
    })
  }

  const addFiles = useCallback(async (newFiles: File[]) => {
    if (files.length + newFiles.length > maxFiles) {
      onError(`最多只能上傳 ${maxFiles} 個文件`)
      return
    }

    const validatedFiles: FileWithPreview[] = []

    for (const file of newFiles) {
      const error = validateFile(file)
      if (error) {
        onError(`${file.name}: ${error}`)
        continue
      }

      const preview = await generatePreview(file)
      validatedFiles.push({
        file,
        id: `${Date.now()}-${Math.random()}`,
        preview,
        status: 'pending',
        progress: 0
      })
    }

    setFiles(prev => [...prev, ...validatedFiles])
  }, [files.length, maxFiles, onError])

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }

  const uploadFiles = async () => {
    if (files.length === 0) {
      onError('請先選擇文件')
      return
    }

    setIsUploading(true)
    const updatedFiles = [...files]

    try {
      for (let i = 0; i < updatedFiles.length; i++) {
        const fileData = updatedFiles[i]
        if (fileData.status !== 'pending') continue

        // Update status to uploading
        updatedFiles[i] = { ...fileData, status: 'uploading', progress: 0 }
        setFiles([...updatedFiles])

        try {
          // Simulate progress updates
          const progressInterval = setInterval(() => {
            updatedFiles[i] = { 
              ...updatedFiles[i], 
              progress: Math.min(updatedFiles[i].progress + 10, 90) 
            }
            setFiles([...updatedFiles])
          }, 200)

          const response = await uploadFile(fileData.file)
          
          clearInterval(progressInterval)
          updatedFiles[i] = { 
            ...updatedFiles[i], 
            status: 'success', 
            progress: 100 
          }
          setFiles([...updatedFiles])

        } catch (error: any) {
          updatedFiles[i] = { 
            ...updatedFiles[i], 
            status: 'error', 
            progress: 0,
            error: error.message || '上傳失敗'
          }
          setFiles([...updatedFiles])
        }
      }

      onFilesUploaded(updatedFiles.filter(f => f.status === 'success'))
    } finally {
      setIsUploading(false)
    }
  }

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(true)
  }, [])

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    addFiles(droppedFiles)
  }, [addFiles])

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      addFiles(selectedFiles)
    }
  }

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase()
    switch (extension) {
      case 'pdf': return '📄'
      case 'csv': return '📊'
      case 'xlsx':
      case 'xls': return '📈'
      default: return '📁'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'var(--color-success)'
      case 'error': return 'var(--color-error)'
      case 'uploading': return 'var(--color-info)'
      default: return 'var(--color-text-secondary)'
    }
  }

  return (
    <div className={`enhanced-file-upload ${className} theme-${theme} ${disabled ? 'disabled' : ''}`}>
      {/* Drop Zone */}
      <div 
        className={`upload-zone ${dragActive ? 'active' : ''}`}
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <div className="upload-content">
          <div className="upload-icon">📁</div>
          <div className="upload-text">
            <div className="upload-primary">拖拽文件到此處或點擊選擇</div>
            <div className="upload-secondary">
              支持 {acceptedTypes.join(', ')} 格式，最大 {maxSize}MB
            </div>
            <div className="upload-limit">
              最多 {maxFiles} 個文件，已選擇 {files.length} 個
            </div>
          </div>
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={acceptedTypes.map(type => `.${type}`).join(',')}
        onChange={handleFileInput}
        style={{ display: 'none' }}
      />

      {/* File List */}
      {files.length > 0 && (
        <div className="file-list">
          <div className="file-list-header">
            <span>已選擇的文件 ({files.length})</span>
            <button 
              className="clear-all-btn"
              onClick={() => setFiles([])}
              disabled={isUploading || disabled}
            >
              清空全部
            </button>
          </div>
          
          {files.map((fileData) => (
            <div key={fileData.id} className="file-item">
              <div className="file-info">
                <span className="file-icon">{getFileIcon(fileData.file.name)}</span>
                <div className="file-details">
                  <div className="file-name">{fileData.file.name}</div>
                  <div className="file-size">
                    {(fileData.file.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                </div>
              </div>
              
              <div className="file-status">
                {fileData.status === 'uploading' && (
                  <div className="file-progress">
                    <div 
                      className="progress-bar-mini"
                      style={{ width: `${fileData.progress}%` }}
                    />
                    <span className="progress-text">{fileData.progress}%</span>
                  </div>
                )}
                
                {fileData.status === 'success' && (
                  <span className="status-icon success">✓</span>
                )}
                
                {fileData.status === 'error' && (
                  <span className="status-icon error" title={fileData.error}>✗</span>
                )}
                
                {fileData.status === 'pending' && (
                  <button 
                    className="remove-btn"
                    onClick={() => removeFile(fileData.id)}
                    disabled={isUploading || disabled}
                  >
                    ✗
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Button */}
      {files.length > 0 && (
        <div className="upload-actions">
          <button 
            className="upload-btn"
            onClick={uploadFiles}
            disabled={isUploading || files.every(f => f.status !== 'pending') || disabled}
          >
            {isUploading ? '上傳中...' : '開始上傳'}
          </button>
        </div>
      )}

      <style jsx>{`
        .enhanced-file-upload {
          width: 100%;
          margin: var(--spacing-lg) 0;
          --color-primary: #00d4aa;
          --color-primary-hover: #00b894;
          --color-error: #e74c3c;
          --color-success: #27ae60;
          --color-info: #3498db;
          --transition-fast: 0.15s ease;
          --transition-normal: 0.3s ease;
          --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
          --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
          --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
          --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
        }

        /* Light Theme */
        .enhanced-file-upload.theme-light,
        .enhanced-file-upload.theme-auto {
          --color-bg-primary: #ffffff;
          --color-bg-secondary: #f8f9fa;
          --color-bg-tertiary: #e9ecef;
          --color-bg-quaternary: #dee2e6;
          --color-text-primary: #212529;
          --color-text-secondary: #6c757d;
          --color-text-tertiary: #adb5bd;
          --color-text-muted: #868e96;
          --color-border: #dee2e6;
          --color-accent-primary: var(--color-primary);
          --color-primary-alpha: rgba(0, 212, 170, 0.1);
          --border-radius-sm: 4px;
          --border-radius-md: 8px;
          --border-radius-lg: 12px;
          --spacing-xs: 4px;
          --spacing-sm: 8px;
          --spacing-md: 16px;
          --spacing-lg: 24px;
          --spacing-xl: 32px;
          --spacing-2xl: 48px;
          --spacing-3xl: 64px;
          --font-size-xs: 12px;
          --font-size-sm: 14px;
          --font-size-base: 16px;
          --font-size-lg: 18px;
          --font-weight-medium: 500;
          --font-weight-semibold: 600;
          --font-weight-bold: 700;
        }

        /* Dark Theme */
        .enhanced-file-upload.theme-dark {
          --color-bg-primary: #1a1a1a;
          --color-bg-secondary: #2d2d2d;
          --color-bg-tertiary: #404040;
          --color-bg-quaternary: #525252;
          --color-text-primary: #ffffff;
          --color-text-secondary: #d1d5db;
          --color-text-tertiary: #9ca3af;
          --color-text-muted: #6b7280;
          --color-border: #404040;
          --color-accent-primary: var(--color-primary);
          --color-primary-alpha: rgba(0, 212, 170, 0.15);
          --border-radius-sm: 4px;
          --border-radius-md: 8px;
          --border-radius-lg: 12px;
          --spacing-xs: 4px;
          --spacing-sm: 8px;
          --spacing-md: 16px;
          --spacing-lg: 24px;
          --spacing-xl: 32px;
          --spacing-2xl: 48px;
          --spacing-3xl: 64px;
          --font-size-xs: 12px;
          --font-size-sm: 14px;
          --font-size-base: 16px;
          --font-size-lg: 18px;
          --font-weight-medium: 500;
          --font-weight-semibold: 600;
          --font-weight-bold: 700;
        }

        /* Auto theme - uses system preference */
        @media (prefers-color-scheme: dark) {
          .enhanced-file-upload.theme-auto {
            --color-bg-primary: #1a1a1a;
            --color-bg-secondary: #2d2d2d;
            --color-bg-tertiary: #404040;
            --color-bg-quaternary: #525252;
            --color-text-primary: #ffffff;
            --color-text-secondary: #d1d5db;
            --color-text-tertiary: #9ca3af;
            --color-text-muted: #6b7280;
            --color-border: #404040;
            --color-primary-alpha: rgba(0, 212, 170, 0.15);
          }
        }

        .enhanced-file-upload.disabled {
          opacity: 0.6;
          pointer-events: none;
        }

        .upload-zone {
          border: 2px dashed var(--color-border);
          border-radius: var(--border-radius-lg);
          padding: var(--spacing-2xl);
          text-align: center;
          cursor: pointer;
          transition: all var(--transition-normal);
          background: var(--color-bg-secondary);
          position: relative;
          overflow: hidden;
        }

        .upload-zone:hover:not(.enhanced-file-upload.disabled *),
        .upload-zone.active {
          border-color: var(--color-accent-primary);
          background: var(--color-primary-alpha);
          transform: translateY(-2px);
          box-shadow: var(--shadow-lg);
        }

        .enhanced-file-upload.disabled .upload-zone {
          cursor: not-allowed;
          background: var(--color-bg-quaternary);
        }

        .upload-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--spacing-md);
        }

        .upload-icon {
          font-size: 48px;
          opacity: 0.7;
        }

        .upload-text {
          color: var(--color-text-primary);
        }

        .upload-primary {
          font-size: var(--font-size-base);
          font-weight: 600;
          margin-bottom: var(--spacing-xs);
        }

        .upload-secondary {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
          margin-bottom: var(--spacing-xs);
        }

        .upload-limit {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .file-list {
          margin-top: var(--spacing-lg);
          border: 1px solid var(--color-bg-tertiary);
          border-radius: var(--border-radius-md);
          background: var(--color-bg-secondary);
        }

        .file-list-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-md);
          border-bottom: 1px solid var(--color-bg-tertiary);
          font-weight: 600;
        }

        .clear-all-btn {
          background: var(--color-error);
          color: white;
          border: none;
          padding: var(--spacing-xs) var(--spacing-sm);
          border-radius: var(--border-radius-sm);
          cursor: pointer;
          font-size: var(--font-size-xs);
          transition: all var(--transition-fast);
        }

        .clear-all-btn:hover:not(:disabled) {
          background: #d32f2f;
        }

        .clear-all-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .file-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-md);
          border-bottom: 1px solid var(--color-bg-tertiary);
        }

        .file-item:last-child {
          border-bottom: none;
        }

        .file-info {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
        }

        .file-icon {
          font-size: 24px;
        }

        .file-details {
          display: flex;
          flex-direction: column;
        }

        .file-name {
          font-weight: 500;
          color: var(--color-text-primary);
        }

        .file-size {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .file-status {
          display: flex;
          align-items: center;
        }

        .file-progress {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
        }

        .progress-bar-mini {
          width: 60px;
          height: 4px;
          background: var(--color-accent-primary);
          border-radius: 2px;
          transition: width var(--transition-fast);
        }

        .progress-text {
          font-size: var(--font-size-xs);
          color: var(--color-text-secondary);
          min-width: 30px;
        }

        .status-icon {
          font-size: 18px;
          font-weight: bold;
        }

        .status-icon.success {
          color: var(--color-success);
        }

        .status-icon.error {
          color: var(--color-error);
        }

        .remove-btn {
          background: var(--color-error);
          color: white;
          border: none;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          cursor: pointer;
          font-size: 12px;
          transition: all var(--transition-fast);
        }

        .remove-btn:hover:not(:disabled) {
          background: #d32f2f;
          transform: scale(1.1);
        }

        .upload-actions {
          margin-top: var(--spacing-lg);
          text-align: center;
        }

        .upload-btn {
          background: var(--color-accent-primary);
          color: var(--color-bg-primary);
          border: none;
          padding: var(--spacing-md) var(--spacing-xl);
          border-radius: var(--border-radius-md);
          cursor: pointer;
          font-size: var(--font-size-base);
          font-weight: 600;
          transition: all var(--transition-fast);
        }

        .upload-btn:hover:not(:disabled) {
          background: #00b894;
          transform: translateY(-2px);
          box-shadow: var(--shadow-md);
        }

        .upload-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }

        /* Enhanced Responsive Design */
        @media (max-width: 1024px) {
          .enhanced-file-upload {
            margin: var(--spacing-md) 0;
          }
          
          .upload-zone {
            padding: var(--spacing-xl);
          }
        }

        @media (max-width: 768px) {
          .upload-zone {
            padding: var(--spacing-lg);
          }
          
          .upload-icon {
            font-size: 36px;
          }
          
          .upload-primary {
            font-size: var(--font-size-base);
          }
          
          .upload-secondary {
            font-size: var(--font-size-xs);
          }
          
          .file-item {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--spacing-sm);
            padding: var(--spacing-sm);
          }
          
          .file-status {
            align-self: flex-end;
            width: 100%;
            justify-content: flex-end;
          }
          
          .file-list {
            padding: var(--spacing-md);
          }
          
          .file-list-header {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--spacing-sm);
          }
        }

        @media (max-width: 480px) {
          .upload-zone {
            padding: var(--spacing-md);
          }
          
          .upload-icon {
            font-size: 32px;
          }
          
          .upload-primary {
            font-size: var(--font-size-sm);
          }
          
          .upload-secondary,
          .upload-limit {
            font-size: var(--font-size-xs);
          }
          
          .file-name {
            font-size: var(--font-size-xs);
            word-break: break-word;
          }
          
          .file-size {
            font-size: 10px;
          }
          
          .file-icon {
            font-size: 20px;
          }
          
          .upload-btn {
            padding: var(--spacing-sm) var(--spacing-lg);
            font-size: var(--font-size-sm);
          }
        }

        @media (max-width: 320px) {
          .upload-zone {
            padding: var(--spacing-sm);
          }
          
          .upload-content {
            gap: var(--spacing-sm);
          }
          
          .file-item {
            padding: var(--spacing-xs);
          }
        }
      `}</style>
    </div>
  )
}