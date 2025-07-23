import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'AI Business Agent - Generate Business Reports',
  description: 'Upload your business data and generate AI-powered business reports, market analysis, and investment summaries',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        <div className="min-h-screen flex flex-col">
          {/* Header */}
          <header className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                <div className="flex items-center">
                  <h1 className="text-xl font-bold text-gray-900">
                    AI Business Agent
                  </h1>
                </div>
                <nav className="flex space-x-4">
                  <a href="/" className="text-gray-600 hover:text-gray-900 transition-colors">
                    Home
                  </a>
                  <a href="/upload" className="text-gray-600 hover:text-gray-900 transition-colors">
                    Upload
                  </a>
                </nav>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1">
            {children}
          </main>

          {/* Footer */}
          <footer className="bg-white border-t mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <p className="text-center text-sm text-gray-500">
                © 2025 AI Business Agent MVP. Powered by GPT-4 for intelligent business insights.
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
