import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useState } from 'react'

const navItems = [
  { path: '/chat', label: 'AI Chat', icon: '💬' },
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/symptoms', label: 'Symptoms', icon: '🩺' },
  { path: '/diet', label: 'Diet Plan', icon: '🥗' },
  { path: '/reports', label: 'Reports', icon: '📋' },
  { path: '/medications', label: 'Medications', icon: '💊' },
  { path: '/trials', label: 'Clinical Trials', icon: '🔬' },
  { path: '/caregiver', label: 'Caregiver', icon: '🤝' },
]

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth()
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)

  if (!isAuthenticated) return null

  return (
    <>
      {/* Desktop Sidebar */}
      <nav className="hidden lg:flex flex-col w-64 bg-white border-r border-gray-100 h-screen fixed left-0 top-0 z-40">
        {/* Logo */}
        <div className="p-5 border-b border-gray-50">
          <Link to="/dashboard" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <span className="text-white text-lg">🎗️</span>
            </div>
            <div>
              <h1 className="text-lg font-bold gradient-text">CancerCare</h1>
              <p className="text-[10px] text-gray-400 -mt-0.5 tracking-wide">AI Health Platform</p>
            </div>
          </Link>
        </div>

        {/* Nav Items */}
        <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navItems.map(item => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-teal-50 text-teal-700 shadow-sm'
                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                }`}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </Link>
            )
          })}
        </div>

        {/* User Section */}
        <div className="p-4 border-t border-gray-50">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center text-white text-sm font-bold shadow">
              {user?.name?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-700 truncate">{user?.name || 'User'}</p>
              <p className="text-xs text-gray-400 truncate">{user?.cancer_type || 'Patient'}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full px-3 py-2 text-xs text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors duration-200"
          >
            Sign Out
          </button>
        </div>
      </nav>

      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-100">
        <div className="flex items-center justify-between px-4 py-3">
          <Link to="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center">
              <span className="text-white text-sm">🎗️</span>
            </div>
            <span className="font-bold text-sm gradient-text">CancerCare AI</span>
          </Link>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {mobileOpen
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              }
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileOpen && (
          <div className="bg-white border-t border-gray-100 px-3 py-3 space-y-1 animate-fade-in">
            {navItems.map(item => {
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm ${
                    isActive ? 'bg-teal-50 text-teal-700 font-medium' : 'text-gray-500'
                  }`}
                >
                  <span>{item.icon}</span>
                  {item.label}
                </Link>
              )
            })}
            <button
              onClick={() => { logout(); setMobileOpen(false) }}
              className="w-full text-left px-3 py-2.5 text-sm text-red-500 hover:bg-red-50 rounded-xl"
            >
              Sign Out
            </button>
          </div>
        )}
      </div>
    </>
  )
}
