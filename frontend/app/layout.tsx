import './globals.css'
import { Toaster } from 'react-hot-toast'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <head>
        <title>AI董事會（alpha測試版）</title>
        <meta name="description" content="AI董事會智能分析平台" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="min-h-screen">
        {children}
        
        {/* Toast Notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
          }}
        />
      </body>
    </html>
  )
}
