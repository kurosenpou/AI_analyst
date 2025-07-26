'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ThemeToggle from './ThemeToggle'

interface NavItem {
  label: string
  href: string
  icon?: React.ReactNode
}

interface ResponsiveNavbarProps {
  title?: string
  items?: NavItem[]
  className?: string
}

const defaultItems: NavItem[] = [
  {
    label: '首页',
    href: '/',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" strokeWidth="2" fill="none" />
        <polyline points="9,22 9,12 15,12 15,22" stroke="currentColor" strokeWidth="2" fill="none" />
      </svg>
    )
  },
  {
    label: '分析报告',
    href: '/reports',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" strokeWidth="2" fill="none" />
        <polyline points="14,2 14,8 20,8" stroke="currentColor" strokeWidth="2" fill="none" />
        <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" strokeWidth="2" />
        <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" strokeWidth="2" />
        <polyline points="10,9 9,9 8,9" stroke="currentColor" strokeWidth="2" fill="none" />
      </svg>
    )
  },
  {
    label: '历史记录',
    href: '/history',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" />
        <polyline points="12,6 12,12 16,14" stroke="currentColor" strokeWidth="2" fill="none" />
      </svg>
    )
  }
]

export default function ResponsiveNavbar({ 
  title = 'AI 数据分析师', 
  items = defaultItems, 
  className = '' 
}: ResponsiveNavbarProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const toggleMenu = () => {
    setIsOpen(!isOpen)
  }

  const closeMenu = () => {
    setIsOpen(false)
  }

  return (
    <>
      <motion.nav
        className={`responsive-navbar ${scrolled ? 'scrolled' : ''} ${className}`}
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="navbar-container">
          {/* Logo/Title */}
          <div className="navbar-brand">
            <motion.h1
              className="brand-title"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {title}
            </motion.h1>
          </div>

          {/* Desktop Navigation */}
          <div className="navbar-nav desktop-nav">
            {items.map((item, index) => (
              <motion.a
                key={item.href}
                href={item.href}
                className="nav-link"
                whileHover={{ y: -2 }}
                whileTap={{ y: 0 }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                {item.icon && <span className="nav-icon">{item.icon}</span>}
                <span className="nav-label">{item.label}</span>
              </motion.a>
            ))}
          </div>

          {/* Right Section */}
          <div className="navbar-actions">
            <ThemeToggle className="desktop-theme-toggle" />
            
            {/* Mobile Menu Button */}
            <button
              className="mobile-menu-button"
              onClick={toggleMenu}
              aria-label="切换菜单"
              aria-expanded={isOpen}
            >
              <motion.div
                className="hamburger"
                animate={isOpen ? 'open' : 'closed'}
              >
                <motion.span
                  className="hamburger-line"
                  variants={{
                    closed: { rotate: 0, y: 0 },
                    open: { rotate: 45, y: 6 }
                  }}
                />
                <motion.span
                  className="hamburger-line"
                  variants={{
                    closed: { opacity: 1 },
                    open: { opacity: 0 }
                  }}
                />
                <motion.span
                  className="hamburger-line"
                  variants={{
                    closed: { rotate: 0, y: 0 },
                    open: { rotate: -45, y: -6 }
                  }}
                />
              </motion.div>
            </button>
          </div>
        </div>
      </motion.nav>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              className="mobile-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={closeMenu}
            />
            
            <motion.div
              className="mobile-menu"
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'tween', duration: 0.3 }}
            >
              <div className="mobile-menu-header">
                <h2 className="mobile-menu-title">{title}</h2>
                <button
                  className="mobile-close-button"
                  onClick={closeMenu}
                  aria-label="关闭菜单"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" strokeWidth="2" />
                    <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" strokeWidth="2" />
                  </svg>
                </button>
              </div>
              
              <div className="mobile-menu-content">
                <div className="mobile-nav">
                  {items.map((item, index) => (
                    <motion.a
                      key={item.href}
                      href={item.href}
                      className="mobile-nav-link"
                      onClick={closeMenu}
                      initial={{ opacity: 0, x: 50 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      whileHover={{ x: 10 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {item.icon && <span className="mobile-nav-icon">{item.icon}</span>}
                      <span className="mobile-nav-label">{item.label}</span>
                    </motion.a>
                  ))}
                </div>
                
                <div className="mobile-menu-footer">
                  <ThemeToggle />
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <style jsx>{`
        .responsive-navbar {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: var(--z-navbar);
          background-color: var(--color-bg-primary);
          border-bottom: 1px solid var(--color-border);
          transition: var(--transition-all);
          backdrop-filter: blur(10px);
        }

        .responsive-navbar.scrolled {
          background-color: var(--color-bg-primary-alpha);
          box-shadow: var(--shadow-lg);
        }

        .navbar-container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 var(--spacing-lg);
          display: flex;
          align-items: center;
          justify-content: space-between;
          height: 64px;
        }

        .navbar-brand {
          flex-shrink: 0;
        }

        .brand-title {
          font-size: var(--font-size-xl);
          font-weight: var(--font-weight-bold);
          color: var(--color-primary);
          margin: 0;
          cursor: pointer;
        }

        .navbar-nav {
          display: flex;
          align-items: center;
          gap: var(--spacing-lg);
        }

        .desktop-nav {
          display: none;
        }

        .nav-link {
          display: flex;
          align-items: center;
          gap: var(--spacing-xs);
          padding: var(--spacing-sm) var(--spacing-md);
          border-radius: var(--border-radius-md);
          text-decoration: none;
          color: var(--color-text-secondary);
          font-weight: var(--font-weight-medium);
          transition: var(--transition-colors);
        }

        .nav-link:hover {
          color: var(--color-primary);
          background-color: var(--color-bg-tertiary);
        }

        .nav-icon {
          display: flex;
          align-items: center;
          color: inherit;
        }

        .nav-label {
          font-size: var(--font-size-sm);
        }

        .navbar-actions {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
        }

        .desktop-theme-toggle {
          display: none;
        }

        .mobile-menu-button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          height: 40px;
          background: none;
          border: none;
          border-radius: var(--border-radius-md);
          cursor: pointer;
          color: var(--color-text-secondary);
          transition: var(--transition-colors);
        }

        .mobile-menu-button:hover {
          background-color: var(--color-bg-tertiary);
          color: var(--color-text-primary);
        }

        .hamburger {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .hamburger-line {
          width: 20px;
          height: 2px;
          background-color: currentColor;
          border-radius: 1px;
        }

        .mobile-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: var(--color-overlay);
          z-index: var(--z-overlay);
        }

        .mobile-menu {
          position: fixed;
          top: 0;
          right: 0;
          bottom: 0;
          width: 280px;
          max-width: 80vw;
          background-color: var(--color-bg-primary);
          border-left: 1px solid var(--color-border);
          z-index: var(--z-modal);
          display: flex;
          flex-direction: column;
        }

        .mobile-menu-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--spacing-lg);
          border-bottom: 1px solid var(--color-border);
        }

        .mobile-menu-title {
          font-size: var(--font-size-lg);
          font-weight: var(--font-weight-bold);
          color: var(--color-primary);
          margin: 0;
        }

        .mobile-close-button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          background: none;
          border: none;
          border-radius: var(--border-radius-md);
          cursor: pointer;
          color: var(--color-text-secondary);
          transition: var(--transition-colors);
        }

        .mobile-close-button:hover {
          background-color: var(--color-bg-tertiary);
          color: var(--color-text-primary);
        }

        .mobile-menu-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          padding: var(--spacing-lg);
        }

        .mobile-nav {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-xs);
        }

        .mobile-nav-link {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
          padding: var(--spacing-md);
          border-radius: var(--border-radius-md);
          text-decoration: none;
          color: var(--color-text-secondary);
          font-weight: var(--font-weight-medium);
          transition: var(--transition-colors);
        }

        .mobile-nav-link:hover {
          color: var(--color-primary);
          background-color: var(--color-bg-tertiary);
        }

        .mobile-nav-icon {
          display: flex;
          align-items: center;
          color: inherit;
        }

        .mobile-nav-label {
          font-size: var(--font-size-base);
        }

        .mobile-menu-footer {
          padding-top: var(--spacing-lg);
          border-top: 1px solid var(--color-border);
        }

        /* Desktop Styles */
        @media (min-width: 768px) {
          .desktop-nav {
            display: flex;
          }

          .desktop-theme-toggle {
            display: flex;
          }

          .mobile-menu-button {
            display: none;
          }

          .navbar-container {
            padding: 0 var(--spacing-xl);
          }
        }

        /* Large Desktop */
        @media (min-width: 1024px) {
          .navbar-container {
            padding: 0 var(--spacing-2xl);
          }

          .navbar-nav {
            gap: var(--spacing-xl);
          }
        }
      `}</style>
    </>
  )
}