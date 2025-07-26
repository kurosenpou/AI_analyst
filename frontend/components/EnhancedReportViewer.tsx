'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'react-hot-toast'

interface ReportSection {
  id: string
  title: string
  content: string
  level: number
}

interface EnhancedReportViewerProps {
  title: string
  content: string
  isOpen: boolean
  onClose: () => void
  onExport?: (format: 'pdf' | 'docx' | 'txt') => void
  showTableOfContents?: boolean
  allowSearch?: boolean
  theme?: 'light' | 'dark' | 'auto'
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'compact' | 'detailed'
  className?: string
}

export default function EnhancedReportViewer({
  title,
  content,
  isOpen,
  onClose,
  onExport,
  showTableOfContents = true,
  allowSearch = true,
  theme = 'auto',
  size = 'md',
  variant = 'default',
  className = ''
}: EnhancedReportViewerProps) {
  const [sections, setSections] = useState<ReportSection[]>([])
  const [activeSection, setActiveSection] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [searchResults, setSearchResults] = useState<number[]>([])
  const [currentSearchIndex, setCurrentSearchIndex] = useState(0)
  const [showTOC, setShowTOC] = useState(true)
  const [fontSize, setFontSize] = useState(16)
  const contentRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Parse content into sections
  useEffect(() => {
    if (!content) return

    const lines = content.split('\n')
    const parsedSections: ReportSection[] = []
    let currentSection: ReportSection | null = null
    let sectionContent: string[] = []

    lines.forEach((line, index) => {
      const trimmedLine = line.trim()
      
      // Check if line is a heading (starts with #)
      const headingMatch = trimmedLine.match(/^(#{1,6})\s+(.+)$/)
      
      if (headingMatch) {
        // Save previous section
        if (currentSection) {
          currentSection.content = sectionContent.join('\n')
          parsedSections.push(currentSection)
        }
        
        // Start new section
        const level = headingMatch[1].length
        const sectionTitle = headingMatch[2]
        currentSection = {
          id: `section-${index}`,
          title: sectionTitle,
          content: '',
          level
        }
        sectionContent = []
      } else {
        sectionContent.push(line)
      }
    })

    // Add last section
    if (currentSection) {
      currentSection.content = sectionContent.join('\n')
      parsedSections.push(currentSection)
    }

    setSections(parsedSections)
    if (parsedSections.length > 0) {
      setActiveSection(parsedSections[0].id)
    }
  }, [content])

  // Search functionality
  useEffect(() => {
    if (!searchTerm || !contentRef.current) {
      setSearchResults([])
      setCurrentSearchIndex(0)
      return
    }

    const contentElement = contentRef.current
    const textContent = contentElement.textContent || ''
    const regex = new RegExp(searchTerm, 'gi')
    const matches = [...textContent.matchAll(regex)]
    
    setSearchResults(matches.map(match => match.index || 0))
    setCurrentSearchIndex(0)
  }, [searchTerm])

  // Highlight search results
  const highlightSearchTerm = (text: string) => {
    if (!searchTerm) return text
    
    const regex = new RegExp(`(${searchTerm})`, 'gi')
    return text.replace(regex, '<mark class="search-highlight">$1</mark>')
  }

  // Navigate to section
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setActiveSection(sectionId)
    }
  }

  // Search navigation
  const navigateSearch = (direction: 'next' | 'prev') => {
    if (searchResults.length === 0) return
    
    let newIndex = currentSearchIndex
    if (direction === 'next') {
      newIndex = (currentSearchIndex + 1) % searchResults.length
    } else {
      newIndex = currentSearchIndex === 0 ? searchResults.length - 1 : currentSearchIndex - 1
    }
    
    setCurrentSearchIndex(newIndex)
    
    // Scroll to search result (simplified)
    if (contentRef.current) {
      const searchElements = contentRef.current.querySelectorAll('.search-highlight')
      if (searchElements[newIndex]) {
        searchElements[newIndex].scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }
  }

  // Export functionality
  const handleExport = (format: 'pdf' | 'docx' | 'txt') => {
    if (onExport) {
      onExport(format)
    } else {
      // Fallback: download as text file
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${title}.${format === 'txt' ? 'txt' : format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return
      
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'f':
            e.preventDefault()
            searchInputRef.current?.focus()
            break
          case '=':
          case '+':
            e.preventDefault()
            setFontSize(prev => Math.min(prev + 2, 24))
            break
          case '-':
            e.preventDefault()
            setFontSize(prev => Math.max(prev - 2, 12))
            break
          case '0':
            e.preventDefault()
            setFontSize(16)
            break
        }
      }
      
      if (e.key === 'Escape') {
        onClose()
      }
      
      if (searchTerm && searchResults.length > 0) {
        if (e.key === 'F3' || (e.ctrlKey && e.key === 'g')) {
          e.preventDefault()
          navigateSearch(e.shiftKey ? 'prev' : 'next')
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, searchTerm, searchResults.length, currentSearchIndex])

  if (!isOpen) return null

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div 
          className={`enhanced-report-viewer ${theme} ${size} ${variant} ${className}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <motion.div 
            className="report-overlay" 
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
          
          <motion.div 
            className="report-container"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
        {/* Header */}
        <motion.div 
          className="report-header"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <div className="header-left">
            <motion.h2 
              className="report-title"
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.2 }}
            >
              {title}
            </motion.h2>
            <motion.div 
              className="header-controls"
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.3 }}
            >
              {showTableOfContents && (
                <motion.button 
                  className={`toc-toggle ${showTOC ? 'active' : ''}`}
                  onClick={() => setShowTOC(!showTOC)}
                  title="切換目錄"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  animate={{ 
                    backgroundColor: showTOC ? 'var(--color-accent-primary)' : 'var(--color-bg-tertiary)'
                  }}
                  transition={{ duration: 0.2 }}
                >
                  📋
                </motion.button>
              )}
              
              <motion.div 
                className="font-size-controls"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.3, delay: 0.4 }}
              >
                <motion.button 
                  onClick={() => setFontSize(prev => Math.max(prev - 2, 12))}
                  title="縮小字體 (Ctrl+-)"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  A-
                </motion.button>
                <motion.span 
                  className="font-size-display"
                  key={fontSize}
                  initial={{ scale: 1.2 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.2 }}
                >
                  {fontSize}px
                </motion.span>
                <motion.button 
                  onClick={() => setFontSize(prev => Math.min(prev + 2, 24))}
                  title="放大字體 (Ctrl++)"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  A+
                </motion.button>
              </motion.div>
            </motion.div>
          </div>
          
          <motion.div 
            className="header-right"
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            {allowSearch && (
              <motion.div 
                className="search-container"
                whileHover={{ scale: 1.02 }}
                whileFocus={{ scale: 1.02 }}
              >
                <motion.input
                  ref={searchInputRef}
                  type="text"
                  placeholder="搜索內容... (Ctrl+F)"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="search-input"
                  whileFocus={{ borderColor: 'var(--color-accent-primary)' }}
                />
                <AnimatePresence>
                  {searchResults.length > 0 && (
                    <motion.div 
                      className="search-navigation"
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 10 }}
                      transition={{ duration: 0.2 }}
                    >
                      <motion.span 
                        className="search-count"
                        key={`${currentSearchIndex}-${searchResults.length}`}
                        initial={{ scale: 1.1 }}
                        animate={{ scale: 1 }}
                        transition={{ duration: 0.2 }}
                      >
                        {currentSearchIndex + 1}/{searchResults.length}
                      </motion.span>
                      <motion.button 
                        onClick={() => navigateSearch('prev')}
                        title="上一個 (Shift+F3)"
                        whileHover={{ scale: 1.1, backgroundColor: 'var(--color-accent-primary)' }}
                        whileTap={{ scale: 0.9 }}
                      >
                        ↑
                      </motion.button>
                      <motion.button 
                        onClick={() => navigateSearch('next')}
                        title="下一個 (F3)"
                        whileHover={{ scale: 1.1, backgroundColor: 'var(--color-accent-primary)' }}
                        whileTap={{ scale: 0.9 }}
                      >
                        ↓
                      </motion.button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}
            
            {onExport && (
              <motion.div 
                className="export-controls"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.3, delay: 0.3 }}
              >
                <motion.button 
                  className="export-btn"
                  onClick={() => handleExport('pdf')}
                  title="導出為PDF"
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                >
                  📄 PDF
                </motion.button>
                <motion.button 
                  className="export-btn"
                  onClick={() => handleExport('docx')}
                  title="導出為Word"
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                >
                  📝 Word
                </motion.button>
                <motion.button 
                  className="export-btn"
                  onClick={() => handleExport('txt')}
                  title="導出為文本"
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                >
                  📋 Text
                </motion.button>
              </motion.div>
            )}
            
            <motion.button 
              className="close-btn" 
              onClick={onClose} 
              title="關閉 (Esc)"
              whileHover={{ scale: 1.1, rotate: 90 }}
              whileTap={{ scale: 0.9 }}
              transition={{ duration: 0.2 }}
            >
              ✕
            </motion.button>
          </motion.div>
        </motion.div>

        {/* Content Area */}
        <motion.div 
          className="report-body"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
        >
          {/* Table of Contents */}
          <AnimatePresence>
            {showTableOfContents && showTOC && sections.length > 0 && (
              <motion.div 
                className="table-of-contents"
                initial={{ x: -300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -300, opacity: 0 }}
                transition={{ 
                  type: "spring", 
                  stiffness: 300, 
                  damping: 30,
                  duration: 0.4 
                }}
              >
                <motion.h3
                  initial={{ y: -10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ duration: 0.3, delay: 0.1 }}
                >
                  目錄
                </motion.h3>
                <motion.nav 
                  className="toc-nav"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: 0.2 }}
                >
                  {sections.map((section, index) => (
                    <motion.button
                      key={section.id}
                      className={`toc-item level-${section.level} ${
                        activeSection === section.id ? 'active' : ''
                      }`}
                      onClick={() => scrollToSection(section.id)}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ 
                        duration: 0.3, 
                        delay: 0.1 + index * 0.05 
                      }}
                      whileHover={{ 
                        x: 5, 
                        backgroundColor: 'var(--color-bg-tertiary)',
                        transition: { duration: 0.2 }
                      }}
                      whileTap={{ scale: 0.98 }}
                    >
                      {section.title}
                    </motion.button>
                  ))}
                </motion.nav>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Report Content */}
          <motion.div 
            ref={contentRef}
            className="report-content"
            style={{ fontSize: `${fontSize}px` }}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.4 }}
            layout
          >
            {sections.length > 0 ? (
              sections.map((section, index) => (
                <motion.div 
                  key={section.id} 
                  id={section.id} 
                  className="content-section"
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ 
                    duration: 0.5, 
                    delay: 0.1 + index * 0.1 
                  }}
                >
                  <motion.h3 
                    className={`section-heading level-${section.level}`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: 0.2 + index * 0.1 }}
                  >
                    {section.title}
                  </motion.h3>
                  <motion.div 
                    className="section-content"
                    dangerouslySetInnerHTML={{
                      __html: highlightSearchTerm(section.content)
                        .replace(/\n/g, '<br>')
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
                    key={fontSize}
                    animate={{ fontSize: `${fontSize}px` }}
                  />
                </motion.div>
              ))
            ) : (
              <motion.div 
                className="raw-content"
                dangerouslySetInnerHTML={{
                  __html: highlightSearchTerm(content)
                    .replace(/\n/g, '<br>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                key={fontSize}
                animate={{ fontSize: `${fontSize}px` }}
              />
            )}
          </motion.div>
        </motion.div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// Add CSS-in-JS styles component
function ReportViewerStyles() {
  return (
    <style jsx>{`
        .enhanced-report-viewer {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 1000;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: var(--spacing-lg);
        }

        .enhanced-report-viewer.dark {
          --color-bg-primary: #1a1a1a;
          --color-bg-secondary: #2d2d2d;
          --color-bg-tertiary: #404040;
          --color-text-primary: #ffffff;
          --color-text-secondary: #cccccc;
          --color-text-muted: #999999;
        }

        .enhanced-report-viewer.light {
          --color-bg-primary: #ffffff;
          --color-bg-secondary: #f8f9fa;
          --color-bg-tertiary: #e9ecef;
          --color-text-primary: #212529;
          --color-text-secondary: #495057;
          --color-text-muted: #6c757d;
        }

        .enhanced-report-viewer.sm .report-container {
          max-width: 800px;
          height: 80vh;
        }

        .enhanced-report-viewer.lg .report-container {
          max-width: 1400px;
          height: 95vh;
        }

        .enhanced-report-viewer.compact .report-header {
          padding: var(--spacing-md);
        }

        .enhanced-report-viewer.compact .report-content {
          padding: var(--spacing-md);
        }

        .report-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          backdrop-filter: blur(4px);
        }

        .report-container {
          position: relative;
          width: 100%;
          max-width: 1200px;
          height: 90vh;
          background: var(--color-bg-primary);
          border-radius: var(--border-radius-lg);
          box-shadow: var(--shadow-xl);
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .report-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-lg);
          border-bottom: 1px solid var(--color-bg-tertiary);
          background: var(--color-bg-secondary);
          flex-shrink: 0;
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: var(--spacing-lg);
          flex: 1;
        }

        .report-title {
          margin: 0;
          color: var(--color-text-primary);
          font-size: var(--font-size-xl);
          font-weight: 600;
        }

        .header-controls {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
        }

        .toc-toggle {
          background: var(--color-bg-tertiary);
          border: 1px solid var(--color-bg-tertiary);
          color: var(--color-text-secondary);
          padding: var(--spacing-xs) var(--spacing-sm);
          border-radius: var(--border-radius-sm);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .toc-toggle.active,
        .toc-toggle:hover {
          background: var(--color-accent-primary);
          color: var(--color-bg-primary);
          border-color: var(--color-accent-primary);
        }

        .font-size-controls {
          display: flex;
          align-items: center;
          gap: var(--spacing-xs);
          background: var(--color-bg-tertiary);
          border-radius: var(--border-radius-sm);
          padding: var(--spacing-xs);
        }

        .font-size-controls button {
          background: none;
          border: none;
          color: var(--color-text-secondary);
          padding: var(--spacing-xs);
          cursor: pointer;
          border-radius: var(--border-radius-xs);
          transition: all var(--transition-fast);
        }

        .font-size-controls button:hover {
          background: var(--color-accent-primary);
          color: var(--color-bg-primary);
        }

        .font-size-display {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          min-width: 30px;
          text-align: center;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
        }

        .search-container {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          background: var(--color-bg-primary);
          border: 1px solid var(--color-bg-tertiary);
          border-radius: var(--border-radius-md);
          padding: var(--spacing-xs);
        }

        .search-input {
          background: none;
          border: none;
          color: var(--color-text-primary);
          padding: var(--spacing-xs) var(--spacing-sm);
          font-size: var(--font-size-sm);
          width: 200px;
          outline: none;
        }

        .search-input::placeholder {
          color: var(--color-text-muted);
        }

        .search-navigation {
          display: flex;
          align-items: center;
          gap: var(--spacing-xs);
        }

        .search-count {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .search-navigation button {
          background: none;
          border: none;
          color: var(--color-text-secondary);
          padding: var(--spacing-xs);
          cursor: pointer;
          border-radius: var(--border-radius-xs);
          transition: all var(--transition-fast);
        }

        .search-navigation button:hover {
          background: var(--color-accent-primary);
          color: var(--color-bg-primary);
        }

        .export-controls {
          display: flex;
          gap: var(--spacing-xs);
        }

        .export-btn {
          background: var(--color-accent-primary);
          color: var(--color-bg-primary);
          border: none;
          padding: var(--spacing-xs) var(--spacing-sm);
          border-radius: var(--border-radius-sm);
          cursor: pointer;
          font-size: var(--font-size-xs);
          transition: all var(--transition-fast);
        }

        .export-btn:hover {
          background: #00b894;
          transform: translateY(-1px);
        }

        .close-btn {
          background: var(--color-error);
          color: white;
          border: none;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          cursor: pointer;
          font-size: var(--font-size-base);
          transition: all var(--transition-fast);
        }

        .close-btn:hover {
          background: #d32f2f;
          transform: scale(1.1);
        }

        .report-body {
          display: flex;
          flex: 1;
          overflow: hidden;
        }

        .table-of-contents {
          width: 300px;
          background: var(--color-bg-secondary);
          border-right: 1px solid var(--color-bg-tertiary);
          padding: var(--spacing-lg);
          overflow-y: auto;
          flex-shrink: 0;
        }

        .table-of-contents h3 {
          margin: 0 0 var(--spacing-md) 0;
          color: var(--color-text-primary);
          font-size: var(--font-size-base);
        }

        .toc-nav {
          display: flex;
          flex-direction: column;
        }

        .toc-item {
          background: none;
          border: none;
          color: var(--color-text-secondary);
          padding: var(--spacing-xs) var(--spacing-sm);
          text-align: left;
          cursor: pointer;
          border-radius: var(--border-radius-sm);
          margin-bottom: var(--spacing-xs);
          transition: all var(--transition-fast);
          font-size: var(--font-size-sm);
        }

        .toc-item.level-1 {
          font-weight: 600;
          padding-left: var(--spacing-sm);
        }

        .toc-item.level-2 {
          padding-left: var(--spacing-lg);
        }

        .toc-item.level-3 {
          padding-left: var(--spacing-xl);
        }

        .toc-item:hover,
        .toc-item.active {
          background: var(--color-accent-primary);
          color: var(--color-bg-primary);
        }

        .report-content {
          flex: 1;
          padding: var(--spacing-lg);
          overflow-y: auto;
          line-height: 1.6;
        }

        .content-section {
          margin-bottom: var(--spacing-xl);
        }

        .section-heading {
          color: var(--color-text-primary);
          margin: 0 0 var(--spacing-md) 0;
          padding-bottom: var(--spacing-sm);
          border-bottom: 1px solid var(--color-bg-tertiary);
        }

        .section-heading.level-1 {
          font-size: var(--font-size-xl);
          font-weight: 700;
        }

        .section-heading.level-2 {
          font-size: var(--font-size-lg);
          font-weight: 600;
        }

        .section-heading.level-3 {
          font-size: var(--font-size-base);
          font-weight: 500;
        }

        .section-content,
        .raw-content {
          color: var(--color-text-primary);
          white-space: pre-wrap;
        }

        :global(.search-highlight) {
          background: var(--color-warning);
          color: var(--color-bg-primary);
          padding: 1px 2px;
          border-radius: 2px;
          font-weight: 600;
        }

        @media (max-width: 768px) {
          .enhanced-report-viewer {
            padding: var(--spacing-sm);
          }
          
          .report-container {
            height: 95vh;
          }
          
          .report-header {
            flex-direction: column;
            gap: var(--spacing-md);
            padding: var(--spacing-md);
          }
          
          .header-left,
          .header-right {
            width: 100%;
            justify-content: space-between;
          }
          
          .search-input {
            width: 150px;
          }
          
          .table-of-contents {
            width: 250px;
          }
          
          .report-content {
            padding: var(--spacing-md);
          }
        }
      `}</style>
  )
}