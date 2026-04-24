import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Chatbot from './pages/Chatbot'
import SymptomTracker from './pages/SymptomTracker'
import DietPlan from './pages/DietPlan'
import ReportUpload from './pages/ReportUpload'
import Medications from './pages/Medications'
import ClinicalTrials from './pages/ClinicalTrials'
import References from './pages/References'
import Caregiver from './pages/Caregiver'

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center mx-auto mb-3 animate-pulse-soft">
          <span className="text-xl">🎗️</span>
        </div>
        <p className="text-sm text-gray-400">Loading CancerCare AI...</p>
      </div>
    </div>
  )
  return isAuthenticated ? children : <Navigate to="/login" />
}

function AppLayout() {
  return (
    <div className="flex">
      <Navbar />
      <main className="flex-1 lg:ml-64 min-h-screen pt-14 lg:pt-0">
        <Routes>
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/chat" element={<ProtectedRoute><Chatbot /></ProtectedRoute>} />
          <Route path="/symptoms" element={<ProtectedRoute><SymptomTracker /></ProtectedRoute>} />
          <Route path="/diet" element={<ProtectedRoute><DietPlan /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><ReportUpload /></ProtectedRoute>} />
          <Route path="/medications" element={<ProtectedRoute><Medications /></ProtectedRoute>} />
          <Route path="/trials" element={<ProtectedRoute><ClinicalTrials /></ProtectedRoute>} />
          <Route path="/references" element={<ProtectedRoute><References /></ProtectedRoute>} />
          <Route path="/caregiver" element={<ProtectedRoute><Caregiver /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </main>
    </div>
  )
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

function AppRoutes() {
  const navigate = useNavigate()

  useEffect(() => {
    const handleUnauthorized = () => {
      navigate('/login')
    }
    window.addEventListener('auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [navigate])

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: '#fff',
            color: '#374151',
            borderRadius: '12px',
            fontSize: '13px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            border: '1px solid #f3f4f6',
          },
        }}
      />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={<AppLayout />} />
      </Routes>
    </>
  )
}
