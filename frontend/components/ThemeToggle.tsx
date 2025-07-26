'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

interface ThemeToggleProps {
  className?: string
}

export default function ThemeToggle({ className = '' }: ThemeToggleProps) {
  const [isDark, setIsDark] = useState(true)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // 从localStorage读取主题设置
    const savedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    
    if (savedTheme) {
      setIsDark(savedTheme === 'dark')
      document.documentElement.setAttribute('data-theme', savedTheme)
    } else {
      setIsDark(prefersDark)
      document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
    }
  }, [])

  const toggleTheme = () => {
    const newTheme = isDark ? 'light' : 'dark'
    setIsDark(!isDark)
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('theme', newTheme)
  }

  if (!mounted) {
    return (
      <div className={`theme-toggle-skeleton ${className}`}>
        <div className="toggle-button skeleton" />
      </div>
    )
  }

  return (
    <div className={`theme-toggle ${className}`}>
      <button
        onClick={toggleTheme}
        className="toggle-button"
        aria-label={`切换到${isDark ? '亮色' : '暗色'}主题`}
        title={`切换到${isDark ? '亮色' : '暗色'}主题`}
      >
        <motion.div
          className="toggle-track"
          animate={{
            backgroundColor: isDark ? '#30363d' : '#e2e8f0'
          }}
          transition={{ duration: 0.2 }}
        >
          <motion.div
            className="toggle-thumb"
            animate={{
              x: isDark ? 0 : 20,
              backgroundColor: isDark ? '#0d1117' : '#ffffff'
            }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
          >
            <motion.div
              className="toggle-icon"
              animate={{ rotate: isDark ? 0 : 180 }}
              transition={{ duration: 0.2 }}
            >
              {isDark ? (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"
                    fill="currentColor"
                  />
                </svg>
              ) : (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="5" fill="currentColor" />
                  <line x1="12" y1="1" x2="12" y2="3" stroke="currentColor" strokeWidth="2" />
                  <line x1="12" y1="21" x2="12" y2="23" stroke="currentColor" strokeWidth="2" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" stroke="currentColor" strokeWidth="2" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" stroke="currentColor" strokeWidth="2" />
                  <line x1="1" y1="12" x2="3" y2="12" stroke="currentColor" strokeWidth="2" />
                  <line x1="21" y1="12" x2="23" y2="12" stroke="currentColor" strokeWidth="2" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" stroke="currentColor" strokeWidth="2" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" stroke="currentColor" strokeWidth="2" />
                </svg>
              )}
            </motion.div>
          </motion.div>
        </motion.div>
        
        <span className="toggle-label">
          {isDark ? '暗色' : '亮色'}
        </span>
      </button>

      <style jsx>{`
        .theme-toggle {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
        }

        .theme-toggle-skeleton {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
        }

        .toggle-button {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          background: none;
          border: none;
          cursor: pointer;
          padding: var(--spacing-xs);
          border-radius: var(--border-radius-lg);
          transition: var(--transition-colors);
          color: var(--color-text-secondary);
        }

        .toggle-button:hover {
          background-color: var(--color-bg-tertiary);
          color: var(--color-text-primary);
        }

        .toggle-button:focus-visible {
          outline: 2px solid var(--color-primary);
          outline-offset: 2px;
        }

        .toggle-track {
          position: relative;
          width: 40px;
          height: 20px;
          border-radius: var(--border-radius-full);
          display: flex;
          align-items: center;
          padding: 2px;
        }

        .toggle-thumb {
          width: 16px;
          height: 16px;
          border-radius: var(--border-radius-full);
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: var(--shadow-sm);
        }

        .toggle-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--color-text-secondary);
        }

        .toggle-label {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-medium);
          user-select: none;
        }

        .skeleton {
          background: linear-gradient(
            90deg,
            var(--color-bg-tertiary) 25%,
            var(--color-bg-quaternary) 50%,
            var(--color-bg-tertiary) 75%
          );
          background-size: 200% 100%;
          animation: loading 1.5s infinite;
          width: 40px;
          height: 20px;
          border-radius: var(--border-radius-full);
        }

        @keyframes loading {
          0% {
            background-position: 200% 0;
          }
          100% {
            background-position: -200% 0;
          }
        }

        @media (max-width: 768px) {
          .toggle-label {
            display: none;
          }
        }
      `}</style>
    </div>
  )
}