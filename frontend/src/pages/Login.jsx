import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../lib/api'
import { useAuth } from '../hooks/useAuth'
import toast from 'react-hot-toast'

export default function Login() {
  const [isRegister, setIsRegister] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', password: '', cancer_type: '', role: 'patient' })
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (isRegister) {
        const { data } = await authAPI.register(form)
        login(data.access_token, { name: form.name, email: form.email, cancer_type: form.cancer_type, role: form.role })
        toast.success('Account created! Welcome to CancerCare AI.')
      } else {
        const { data } = await authAPI.login({ email: form.email, password: form.password })
        login(data.access_token, data.user)
        toast.success('Welcome back!')
      }
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const update = (field, value) => setForm(prev => ({ ...prev, [field]: value }))

  return (
    <div className="min-h-screen flex">
      {/* Left Panel — Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-teal-600 via-teal-700 to-teal-900 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(255,255,255,0.1),transparent_50%)]" />
        <div className="relative z-10 flex flex-col justify-center px-16">
          <div className="w-16 h-16 rounded-2xl bg-white/10 backdrop-blur flex items-center justify-center mb-8 shadow-xl">
            <span className="text-3xl">🎗️</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
            Your AI-Powered<br />Health Companion
          </h1>
          <p className="text-teal-100 text-lg leading-relaxed max-w-md">
            CancerCare AI helps you manage your health journey with personalized insights, diet plans, symptom tracking, and compassionate support.
          </p>
          <div className="mt-12 space-y-4">
            {[
              { icon: '💬', text: 'AI Chatbot trained on medical knowledge' },
              { icon: '📋', text: 'Upload & analyze medical reports' },
              { icon: '🥗', text: 'Personalized diet recommendations' },
              { icon: '📊', text: 'Track symptoms & visualize trends' },
            ].map((feature, i) => (
              <div key={i} className="flex items-center gap-3 text-teal-100">
                <span className="text-lg">{feature.icon}</span>
                <span className="text-sm">{feature.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel — Form */}
      <div className="flex-1 flex items-center justify-center p-6 bg-gray-50">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center mx-auto mb-3 shadow-lg shadow-teal-500/20">
              <span className="text-2xl">🎗️</span>
            </div>
            <h1 className="text-2xl font-bold gradient-text">CancerCare AI</h1>
          </div>

          <div className="bg-white rounded-2xl shadow-xl shadow-gray-200/50 p-8 border border-gray-100">
            <h2 className="text-2xl font-bold text-gray-800 mb-1">
              {isRegister ? 'Create Account' : 'Welcome Back'}
            </h2>
            <p className="text-sm text-gray-400 mb-6">
              {isRegister ? 'Join CancerCare AI for personalized support' : 'Sign in to continue your health journey'}
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              {isRegister && (
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Full Name</label>
                  <input
                    type="text" required value={form.name}
                    onChange={e => update('name', e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
                    placeholder="John Doe"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5">Email Address</label>
                <input
                  type="email" required value={form.email}
                  onChange={e => update('email', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5">Password</label>
                <input
                  type="password" required value={form.password}
                  onChange={e => update('password', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
                  placeholder="••••••••"
                />
              </div>

              {isRegister && (
                <>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1.5">Cancer Type</label>
                    <select
                      value={form.cancer_type}
                      onChange={e => update('cancer_type', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 bg-white"
                    >
                      <option value="">Select type (optional)</option>
                      <option value="breast">Breast Cancer</option>
                      <option value="lung">Lung Cancer</option>
                      <option value="colorectal">Colorectal Cancer</option>
                      <option value="prostate">Prostate Cancer</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1.5">I am a</label>
                    <div className="flex gap-3">
                      {['patient', 'caregiver'].map(role => (
                        <button
                          key={role} type="button"
                          onClick={() => update('role', role)}
                          className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ${
                            form.role === role
                              ? 'bg-teal-50 text-teal-700 border-2 border-teal-500'
                              : 'bg-gray-50 text-gray-500 border-2 border-transparent hover:bg-gray-100'
                          }`}
                        >
                          {role === 'patient' ? '🧑 Patient' : '🤝 Caregiver'}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}

              <button
                type="submit" disabled={loading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-600 to-teal-500 text-white text-sm font-semibold hover:from-teal-700 hover:to-teal-600 transition-all duration-200 shadow-lg shadow-teal-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? '...' : isRegister ? 'Create Account' : 'Sign In'}
              </button>
            </form>

            <div className="mt-5 text-center">
              <button
                onClick={() => setIsRegister(!isRegister)}
                className="text-sm text-teal-600 hover:text-teal-700 font-medium"
              >
                {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Register"}
              </button>
            </div>
          </div>

          <p className="text-xs text-gray-400 text-center mt-4 px-4">
            By continuing, you acknowledge that CancerCare AI is an educational tool and not a substitute for professional medical advice.
          </p>
        </div>
      </div>
    </div>
  )
}
