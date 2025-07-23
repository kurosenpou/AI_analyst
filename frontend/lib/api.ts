/**
 * API client for communicating with the FastAPI backend
 */

import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message)
    
    // Handle common error cases
    if (error.response?.status === 404) {
      throw new Error('Resource not found')
    } else if (error.response?.status === 500) {
      throw new Error('Server error. Please try again later.')
    } else if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail)
    } else {
      throw new Error(error.message || 'An unexpected error occurred')
    }
  }
)

// File upload API
export const uploadFile = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post('/api/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response
}

// Get file status
export const getFileStatus = async (fileId: string) => {
  const response = await apiClient.get(`/api/upload/${fileId}/status`)
  return response
}

// Delete uploaded file
export const deleteFile = async (fileId: string) => {
  const response = await apiClient.delete(`/api/upload/${fileId}`)
  return response
}

// Generate business report
export const generateBusinessReport = async (fileId: string, reportType: string, additionalContext?: string) => {
  const response = await apiClient.post('/api/generate/business-report', {
    file_id: fileId,
    report_type: reportType,
    additional_context: additionalContext || null,
  })

  return response
}

// Quick data analysis
export const getQuickAnalysis = async (fileId: string) => {
  const response = await apiClient.post('/api/generate/quick-analysis', {
    file_id: fileId,
  })

  return response
}

// Get generated report
export const getReport = async (reportId: string) => {
  const response = await apiClient.get(`/api/generate/${reportId}`)
  return response
}

// Download report
export const downloadReport = async (reportId: string, format: string = 'markdown') => {
  const response = await apiClient.get(`/api/generate/${reportId}/download`, {
    params: { format },
    responseType: 'blob', // Important for file downloads
  })

  // Create download link
  const blob = new Blob([response.data], { 
    type: format === 'markdown' ? 'text/markdown' : 'text/plain' 
  })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `report_${reportId}.${format === 'markdown' ? 'md' : 'txt'}`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)

  return response
}

// Health check
export const healthCheck = async () => {
  const response = await apiClient.get('/health')
  return response
}

// Utility function to format error messages
export const formatApiError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail
  } else if (error.message) {
    return error.message
  } else {
    return 'An unexpected error occurred'
  }
}

// Utility function to check if backend is available
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    await healthCheck()
    return true
  } catch (error) {
    console.error('Backend health check failed:', error)
    return false
  }
}

export default apiClient
