'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface ProgressStep {
  id: string
  title: string
  description: string
  status: 'pending' | 'running' | 'completed' | 'error'
  progress?: number
  startTime?: Date
  endTime?: Date
  error?: string
  duration?: number
}

interface EnhancedProgressProps {
  steps: ProgressStep[]
  currentStep?: string
  overallProgress: number
  isRunning: boolean
  onCancel?: () => void
  showTimeEstimate?: boolean
  showDetailedSteps?: boolean
  theme?: 'light' | 'dark' | 'auto'
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'minimal' | 'detailed'
  className?: string
}

export default function EnhancedProgress({
  steps,
  currentStep,
  overallProgress,
  isRunning,
  onCancel,
  showTimeEstimate = true,
  showDetailedSteps = true,
  theme = 'auto',
  size = 'md',
  variant = 'default',
  className = ''
}: EnhancedProgressProps) {
  const [elapsedTime, setElapsedTime] = useState(0)
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<number | null>(null)
  const [animatedProgress, setAnimatedProgress] = useState(0)
  const [stepsCollapsed, setStepsCollapsed] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedProgress(overallProgress)
    }, 100)
    return () => clearTimeout(timer)
  }, [overallProgress])

  useEffect(() => {
    let interval: NodeJS.Timeout
    
    if (isRunning) {
      const startTime = Date.now()
      interval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000)
        setElapsedTime(elapsed)
        
        // Calculate estimated time remaining
        if (overallProgress > 0 && overallProgress < 100) {
          const totalEstimated = (elapsed / overallProgress) * 100
          const remaining = Math.max(0, totalEstimated - elapsed)
          setEstimatedTimeRemaining(Math.floor(remaining))
        }
      }, 1000)
    } else {
      setEstimatedTimeRemaining(null)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isRunning, overallProgress])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getStepIcon = (status: string, index: number) => {
    switch (status) {
      case 'completed':
        return (
          <motion.svg 
            width="20" 
            height="20" 
            viewBox="0 0 24 24" 
            fill="none"
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
          >
            <path 
              d="M20 6L9 17l-5-5" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
          </motion.svg>
        )
      case 'error':
        return (
          <motion.svg 
            width="20" 
            height="20" 
            viewBox="0 0 24 24" 
            fill="none"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </motion.svg>
        )
      case 'running':
        return (
          <motion.div
            className="loading-spinner"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <circle 
                cx="12" 
                cy="12" 
                r="10" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeDasharray="60" 
                strokeDashoffset="20"
              />
            </svg>
          </motion.div>
        )
      default:
        return (
          <motion.div 
            className="step-number"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.2, delay: index * 0.05 }}
          >
            {index + 1}
          </motion.div>
        )
    }
  }

  const getStepStatusClass = (status: string) => {
    switch (status) {
      case 'completed': return 'step-completed'
      case 'error': return 'step-error'
      case 'running': return 'step-running'
      default: return 'step-pending'
    }
  }

  const completedSteps = steps.filter(step => step.status === 'completed').length
  const totalSteps = steps.length
  const currentStepData = steps.find(step => step.id === currentStep)

  return (
    <div className={`enhanced-progress theme-${theme} size-${size} variant-${variant} ${className}`}>
      {/* Progress Header */}
      <motion.div 
        className="progress-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="progress-info">
          <h3 className="progress-title">處理進度</h3>
          <div className="progress-stats">
            <span className="step-counter">{completedSteps}/{totalSteps} 步驟完成</span>
            <span className="progress-percentage">{Math.round(animatedProgress)}%</span>
          </div>
          {showTimeEstimate && (
            <div className="progress-timeline">
              <span className="elapsed-time">已用時: {formatTime(elapsedTime)}</span>
              {estimatedTimeRemaining !== null && (
                <span className="remaining-time">預計剩餘: {formatTime(estimatedTimeRemaining)}</span>
              )}
            </div>
          )}
        </div>
        
        {onCancel && isRunning && (
          <motion.button 
            className="cancel-btn"
            onClick={onCancel}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            取消
          </motion.button>
        )}
      </motion.div>

      {/* Overall Progress Bar */}
      <div className="progress-bar-container">
        <motion.div
          className="progress-bar"
          initial={{ width: 0 }}
          animate={{ width: `${animatedProgress}%` }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
        >
          <div className="progress-bar-glow" />
        </motion.div>
        <div className="progress-bar-background" />
      </div>

      {/* Current Step Highlight */}
      {currentStepData && (
        <motion.div 
          className="current-step"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="current-step-header">
            <motion.span 
              className="current-step-icon"
              animate={{ 
                scale: [1, 1.1, 1],
                opacity: [1, 0.7, 1]
              }}
              transition={{ 
                duration: 2, 
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              {getStepIcon(currentStepData.status, 0)}
            </motion.span>
            <div className="current-step-info">
              <div className="current-step-title">{currentStepData.title}</div>
              <div className="current-step-description">{currentStepData.description}</div>
            </div>
          </div>
          
          {currentStepData.progress !== undefined && currentStepData.status === 'running' && (
            <motion.div 
              className="current-step-progress"
              initial={{ opacity: 0, scaleX: 0 }}
              animate={{ opacity: 1, scaleX: 1 }}
              transition={{ duration: 0.3 }}
              style={{ originX: 0 }}
            >
              <div className="mini-progress-bar">
                <motion.div
                  className="mini-progress-fill"
                  initial={{ width: 0 }}
                  animate={{ width: `${currentStepData.progress}%` }}
                  transition={{ duration: 0.5, ease: 'easeInOut' }}
                >
                  <div className="mini-progress-glow" />
                </motion.div>
              </div>
              <span className="mini-progress-text">{currentStepData.progress}%</span>
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Detailed Steps */}
      {showDetailedSteps && (
        <div className="steps-list">
          <div className="steps-header">
            <h4>詳細步驟</h4>
            <motion.button 
              className="toggle-steps"
              onClick={() => setStepsCollapsed(!stepsCollapsed)}
              animate={{ rotate: stepsCollapsed ? -90 : 0 }}
              transition={{ duration: 0.2 }}
            >
              ▼
            </motion.button>
          </div>
          
          <AnimatePresence>
            {!stepsCollapsed && (
              <motion.div 
                className="steps-content"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                {steps.map((step, index) => (
                  <motion.div 
                    key={step.id}
                    className={`step-item ${getStepStatusClass(step.status)} ${step.id === currentStep ? 'current' : ''}`}
                    initial={{ opacity: 0, x: -30 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ 
                      duration: 0.3, 
                      delay: index * 0.1,
                      ease: 'easeOut'
                    }}
                    layout
                  >
                    <div className="step-indicator">
                      <motion.div
                        className="step-icon"
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        {getStepIcon(step.status, index)}
                      </motion.div>
                      
                      {index < steps.length - 1 && (
                        <div className="step-connector">
                          <motion.div
                            className="connector-line"
                            initial={{ scaleY: 0 }}
                            animate={{ 
                              scaleY: step.status === 'completed' ? 1 : 0
                            }}
                            transition={{ duration: 0.4, delay: 0.2 }}
                            style={{ originY: 0 }}
                          />
                        </div>
                      )}
                    </div>
                    
                    <div className="step-content">
                      <div className="step-header">
                        <div className="step-title">{step.title}</div>
                        <div className="step-meta">
                          {step.status === 'running' && step.progress !== undefined && (
                            <motion.span 
                              className="step-progress"
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ duration: 0.3 }}
                            >
                              {step.progress}%
                            </motion.span>
                          )}
                          {step.status === 'completed' && step.endTime && step.startTime && (
                            <span className="step-duration">
                              {formatTime(Math.floor((step.endTime.getTime() - step.startTime.getTime()) / 1000))}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="step-description">{step.description}</div>
                      
                      {step.error && (
                        <motion.div 
                          className="step-error"
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ duration: 0.3 }}
                        >
                          <span className="error-icon">⚠</span>
                          {step.error}
                        </motion.div>
                      )}
                      
                      {(step.startTime || step.endTime) && (
                        <div className="step-timing">
                          {step.startTime && (
                            <span>開始: {step.startTime.toLocaleTimeString()}</span>
                          )}
                          {step.endTime && (
                            <span>完成: {step.endTime.toLocaleTimeString()}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      <style jsx>{`
        .enhanced-progress {
          width: 100%;
          max-width: 700px;
          margin: 0 auto;
          --color-primary: #00d4aa;
          --color-secondary: #00b894;
          --color-success: #27ae60;
          --color-error: #e74c3c;
          --color-warning: #f39c12;
          --color-info: #3498db;
          --transition-fast: 0.15s ease;
          --transition-normal: 0.3s ease;
          --transition-slow: 0.5s ease;
          --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
          --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
          --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
          --glow-primary: 0 0 20px rgba(0, 212, 170, 0.3);
        }

        /* Theme Variables */
        .enhanced-progress.theme-light,
        .enhanced-progress.theme-auto {
          --color-bg-primary: #ffffff;
          --color-bg-secondary: #f8f9fa;
          --color-bg-tertiary: #e9ecef;
          --color-bg-quaternary: #dee2e6;
          --color-text-primary: #212529;
          --color-text-secondary: #6c757d;
          --color-text-tertiary: #adb5bd;
          --color-border: #dee2e6;
          --color-primary-alpha: rgba(0, 212, 170, 0.1);
        }

        .enhanced-progress.theme-dark {
          --color-bg-primary: #1a1a1a;
          --color-bg-secondary: #2d2d2d;
          --color-bg-tertiary: #404040;
          --color-bg-quaternary: #525252;
          --color-text-primary: #ffffff;
          --color-text-secondary: #d1d5db;
          --color-text-tertiary: #9ca3af;
          --color-border: #404040;
          --color-primary-alpha: rgba(0, 212, 170, 0.15);
        }

        @media (prefers-color-scheme: dark) {
          .enhanced-progress.theme-auto {
            --color-bg-primary: #1a1a1a;
            --color-bg-secondary: #2d2d2d;
            --color-bg-tertiary: #404040;
            --color-bg-quaternary: #525252;
            --color-text-primary: #ffffff;
            --color-text-secondary: #d1d5db;
            --color-text-tertiary: #9ca3af;
            --color-border: #404040;
            --color-primary-alpha: rgba(0, 212, 170, 0.15);
          }
        }

        /* Size Variants */
        .enhanced-progress.size-sm {
          --spacing-xs: 4px;
          --spacing-sm: 8px;
          --spacing-md: 12px;
          --spacing-lg: 16px;
          --spacing-xl: 20px;
          --font-size-xs: 10px;
          --font-size-sm: 12px;
          --font-size-base: 14px;
          --font-size-lg: 16px;
          --icon-size: 16px;
          --step-icon-size: 32px;
        }

        .enhanced-progress.size-md {
          --spacing-xs: 6px;
          --spacing-sm: 12px;
          --spacing-md: 16px;
          --spacing-lg: 24px;
          --spacing-xl: 32px;
          --font-size-xs: 12px;
          --font-size-sm: 14px;
          --font-size-base: 16px;
          --font-size-lg: 18px;
          --icon-size: 20px;
          --step-icon-size: 40px;
        }

        .enhanced-progress.size-lg {
          --spacing-xs: 8px;
          --spacing-sm: 16px;
          --spacing-md: 24px;
          --spacing-lg: 32px;
          --spacing-xl: 48px;
          --font-size-xs: 14px;
          --font-size-sm: 16px;
          --font-size-base: 18px;
          --font-size-lg: 20px;
          --icon-size: 24px;
          --step-icon-size: 48px;
        }

        /* Base Styles */
        .enhanced-progress {
          padding: var(--spacing-lg);
          background-color: var(--color-bg-secondary);
          border-radius: 12px;
          border: 1px solid var(--color-border);
          box-shadow: var(--shadow-sm);
        }

        .progress-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: var(--spacing-lg);
        }

        .progress-info {
          flex: 1;
        }

        .progress-title {
          font-size: var(--font-size-lg);
          font-weight: 600;
          color: var(--color-text-primary);
          margin: 0 0 var(--spacing-xs) 0;
        }

        .progress-stats {
          display: flex;
          gap: var(--spacing-md);
          font-size: var(--font-size-sm);
          margin-bottom: var(--spacing-xs);
        }

        .step-counter {
          color: var(--color-text-secondary);
        }

        .progress-percentage {
          color: var(--color-primary);
          font-weight: 700;
        }

        .progress-timeline {
          display: flex;
          gap: var(--spacing-md);
          font-size: var(--font-size-xs);
          color: var(--color-text-secondary);
        }

        .cancel-btn {
          background: var(--color-error);
          color: white;
          border: none;
          padding: var(--spacing-xs) var(--spacing-md);
          border-radius: 6px;
          cursor: pointer;
          font-size: var(--font-size-sm);
          font-weight: 500;
          transition: var(--transition-normal);
          box-shadow: var(--shadow-sm);
        }

        .cancel-btn:hover {
          background: #d32f2f;
          box-shadow: var(--shadow-md);
        }

        .progress-bar-container {
          position: relative;
          width: 100%;
          height: 12px;
          margin-bottom: var(--spacing-lg);
        }

        .progress-bar-background {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-color: var(--color-bg-tertiary);
          border-radius: 6px;
        }

        .progress-bar {
          position: relative;
          height: 100%;
          background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
          border-radius: 6px;
          overflow: hidden;
          box-shadow: var(--glow-primary);
        }

        .progress-bar-glow {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.4),
            transparent
          );
          animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }

        .current-step {
          background: var(--color-primary-alpha);
          border: 1px solid var(--color-primary);
          border-radius: 8px;
          padding: var(--spacing-md);
          margin-bottom: var(--spacing-lg);
        }

        .current-step-header {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
          margin-bottom: var(--spacing-sm);
        }

        .current-step-icon {
          font-size: 20px;
          color: var(--color-primary);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .current-step-info {
          flex: 1;
        }

        .current-step-title {
          font-weight: 600;
          color: var(--color-text-primary);
          margin-bottom: var(--spacing-xs);
        }

        .current-step-description {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
        }

        .current-step-progress {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
        }

        .mini-progress-bar {
          flex: 1;
          height: 6px;
          background: var(--color-bg-tertiary);
          border-radius: 3px;
          overflow: hidden;
          position: relative;
        }

        .mini-progress-fill {
          height: 100%;
          background: var(--color-primary);
          border-radius: 3px;
          position: relative;
          overflow: hidden;
        }

        .mini-progress-glow {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.5),
            transparent
          );
          animation: shimmer 1.5s infinite;
        }

        .mini-progress-text {
          font-size: var(--font-size-xs);
          color: var(--color-text-secondary);
          min-width: 30px;
          font-weight: 500;
        }

        .steps-list {
          border-top: 1px solid var(--color-border);
          padding-top: var(--spacing-lg);
        }

        .steps-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--spacing-md);
        }

        .steps-header h4 {
          margin: 0;
          color: var(--color-text-primary);
          font-size: var(--font-size-base);
          font-weight: 600;
        }

        .toggle-steps {
          background: none;
          border: none;
          color: var(--color-text-secondary);
          cursor: pointer;
          font-size: var(--font-size-sm);
          transition: var(--transition-normal);
          padding: var(--spacing-xs);
          border-radius: 4px;
        }

        .toggle-steps:hover {
          background: var(--color-bg-tertiary);
          color: var(--color-text-primary);
        }

        .steps-content {
          overflow: hidden;
        }

        .step-item {
          display: flex;
          gap: var(--spacing-md);
          margin-bottom: var(--spacing-md);
          position: relative;
        }

        .step-item.current {
          background: var(--color-primary-alpha);
          border-radius: 8px;
          padding: var(--spacing-sm);
          margin: var(--spacing-sm) 0;
        }

        .step-indicator {
          display: flex;
          flex-direction: column;
          align-items: center;
          position: relative;
          flex-shrink: 0;
        }

        .step-icon {
          width: var(--step-icon-size);
          height: var(--step-icon-size);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: var(--font-size-sm);
          transition: var(--transition-normal);
          z-index: 2;
          position: relative;
        }

        .step-number {
          font-size: var(--font-size-sm);
          font-weight: 600;
        }

        .step-connector {
          position: absolute;
          top: var(--step-icon-size);
          left: 50%;
          transform: translateX(-50%);
          width: 2px;
          height: calc(100% + var(--spacing-md));
          background-color: var(--color-bg-tertiary);
          z-index: 1;
        }

        .connector-line {
          width: 100%;
          height: 100%;
          background: linear-gradient(180deg, var(--color-primary), var(--color-secondary));
          border-radius: 1px;
        }

        .step-content {
          flex: 1;
          padding-top: var(--spacing-xs);
          min-width: 0;
        }

        .step-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--spacing-xs);
        }

        .step-title {
          font-size: var(--font-size-base);
          font-weight: 600;
          color: var(--color-text-primary);
          flex: 1;
          min-width: 0;
        }

        .step-meta {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          flex-shrink: 0;
        }

        .step-progress,
        .step-duration {
          font-size: var(--font-size-sm);
          font-weight: 500;
          color: var(--color-primary);
        }

        .step-description {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
          margin-bottom: var(--spacing-xs);
          line-height: 1.5;
        }

        .step-error {
          display: flex;
          align-items: center;
          gap: var(--spacing-xs);
          color: var(--color-error);
          font-size: var(--font-size-sm);
          background: rgba(231, 76, 60, 0.1);
          padding: var(--spacing-xs) var(--spacing-sm);
          border-radius: 6px;
          margin-top: var(--spacing-xs);
          border-left: 3px solid var(--color-error);
        }

        .error-icon {
          font-size: 14px;
        }

        .step-timing {
          display: flex;
          gap: var(--spacing-md);
          font-size: var(--font-size-xs);
          color: var(--color-text-tertiary);
          margin-top: var(--spacing-xs);
        }

        /* Status-specific styles */
        .step-item.step-completed .step-icon {
          background-color: var(--color-success);
          color: white;
          box-shadow: 0 0 0 3px rgba(39, 174, 96, 0.2);
        }

        .step-item.step-completed .step-title {
          color: var(--color-success);
        }

        .step-item.step-error .step-icon {
          background-color: var(--color-error);
          color: white;
          box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.2);
        }

        .step-item.step-error .step-title {
          color: var(--color-error);
        }

        .step-item.step-running .step-icon {
          background-color: var(--color-primary);
          color: white;
          box-shadow: 0 0 0 3px var(--color-primary-alpha), var(--glow-primary);
          animation: pulse 2s infinite;
        }

        .step-item.step-running .step-title {
          color: var(--color-primary);
          font-weight: 700;
        }

        .step-item.step-pending .step-icon {
          background-color: var(--color-bg-tertiary);
          color: var(--color-text-secondary);
          border: 2px solid var(--color-border);
        }

        .step-item.step-pending .step-title {
          color: var(--color-text-secondary);
        }

        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }

        /* Variant Styles */
        .enhanced-progress.variant-minimal {
          padding: var(--spacing-md);
          background: transparent;
          border: none;
          box-shadow: none;
        }

        .enhanced-progress.variant-minimal .progress-header {
          margin-bottom: var(--spacing-md);
        }

        .enhanced-progress.variant-detailed .step-description {
          background-color: var(--color-bg-primary);
          padding: var(--spacing-sm);
          border-radius: 6px;
          border-left: 3px solid var(--color-primary);
        }

        /* Responsive Design */
        @media (max-width: 768px) {
          .enhanced-progress {
            padding: var(--spacing-md);
          }

          .progress-header {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--spacing-sm);
          }

          .progress-stats {
            flex-direction: column;
            gap: var(--spacing-xs);
          }

          .progress-timeline {
            flex-direction: column;
            gap: var(--spacing-xs);
          }

          .current-step-header {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--spacing-sm);
          }

          .step-item {
            gap: var(--spacing-sm);
          }

          .step-header {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--spacing-xs);
          }
        }

        @media (max-width: 480px) {
          .enhanced-progress {
            padding: var(--spacing-sm);
          }

          .progress-title {
            font-size: var(--font-size-base);
          }

          .step-icon {
            width: 32px;
            height: 32px;
          }

          .step-title {
            font-size: var(--font-size-sm);
          }

          .step-description {
            font-size: var(--font-size-xs);
          }
        }
      `}</style>
    </div>
  )
}