'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, AlertCircle, Loader2 } from 'lucide-react'

interface FileUploadProps {
  onFileUpload: (file: File) => Promise<void>
  isUploading: boolean
  error: string | null
}

const FileUploadComponent: React.FC<FileUploadProps> = ({
  onFileUpload,
  isUploading,
  error
}) => {
  const [dragActive, setDragActive] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles[0])
    }
  }, [onFileUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: false,
    disabled: isUploading
  })

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`upload-zone ${isDragActive ? 'active' : ''} ${
          isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
        }`}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center">
          {isUploading ? (
            <>
              <Loader2 className="w-12 h-12 text-primary-600 animate-spin mb-4" />
              <p className="text-lg font-medium text-primary-600 mb-2">
                Uploading and processing file...
              </p>
              <p className="text-sm text-gray-500">
                Please wait while we analyze your data
              </p>
            </>
          ) : (
            <>
              <Upload className="w-12 h-12 text-gray-400 mb-4" />
              <p className="text-lg font-medium text-gray-700 mb-2">
                {isDragActive
                  ? 'Drop your file here'
                  : 'Drag & drop your file here, or click to browse'}
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Supports CSV, PDF, Excel files up to 10MB
              </p>
              
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <File className="w-4 h-4" />
                <span>CSV, PDF, XLSX, XLS</span>
              </div>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-4 bg-error-50 border border-error-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error-600 flex-shrink-0" />
            <div>
              <h3 className="font-medium text-error-800">Upload Failed</h3>
              <p className="text-error-600 text-sm">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Upload Tips */}
      <div className="mt-6 bg-blue-50 rounded-lg p-4">
        <h4 className="font-medium text-blue-800 mb-2">Upload Tips:</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• For best results, include column headers in CSV files</li>
          <li>• PDF files should contain text (not just images)</li>
          <li>• Excel files: all sheets will be analyzed</li>
          <li>• Financial data, customer data, and market data work best</li>
        </ul>
      </div>
    </div>
  )
}

export default FileUploadComponent
