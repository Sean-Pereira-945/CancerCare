import { useEffect, useState } from 'react'
import { symptomsAPI } from '../lib/api'
import { useAuth } from '../hooks/useAuth'
import SymptomChart from '../components/SymptomChart'
import MedicalDisclaimer from '../components/MedicalDisclaimer'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const { user } = useAuth()
  const [data, setData] = useState([])
  const [days, setDays] = useState(14)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    symptomsAPI.getTrends(days)
      .then(res => setData(res.data.trends))
      .catch(() => setData([]))
      .finally(() => setLoading(false))
  }, [days])

  const quickActions = [
    { path: '/chat', icon: '💬', label: 'AI Chat', desc: 'Ask health questions', color: 'from-teal-500 to-teal-600' },
    { path: '/symptoms', icon: '🩺', label: 'Log Symptoms', desc: 'Track how you feel', color: 'from-blue-500 to-blue-600' },
    { path: '/diet', icon: '🥗', label: 'Diet Plan', desc: 'Get meal suggestions', color: 'from-emerald-500 to-emerald-600' },
    { path: '/reports', icon: '📋', label: 'Upload Report', desc: 'Analyze your labs', color: 'from-purple-500 to-purple-600' },
  ]

  // Calculate summary stats from trend data
  const latestLog = data.length > 0 ? data[data.length - 1] : null
  const avgMood = data.length > 0 ? (data.reduce((sum, d) => sum + (d.mood || 0), 0) / data.length).toFixed(1) : '--'
  const avgPain = data.length > 0 ? (data.reduce((sum, d) => sum + (d.pain || 0), 0) / data.length).toFixed(1) : '--'

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Greeting */}
      <div className="animate-slide-up">
        <h1 className="text-3xl font-bold text-gray-800">
          Welcome back, <span className="gradient-text">{user?.name?.split(' ')[0] || 'there'}</span> 👋
        </h1>
        <p className="text-gray-400 text-sm mt-1">Here's an overview of your health journey</p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 animate-slide-up" style={{ animationDelay: '100ms' }}>
        {quickActions.map(action => (
          <Link
            key={action.path}
            to={action.path}
            className="group bg-white rounded-2xl border border-gray-100 p-5 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300"
          >
            <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center text-lg shadow-md mb-3 group-hover:scale-110 transition-transform duration-300`}>
              {action.icon}
            </div>
            <h3 className="text-sm font-semibold text-gray-700">{action.label}</h3>
            <p className="text-xs text-gray-400 mt-0.5">{action.desc}</p>
          </Link>
        ))}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 animate-slide-up" style={{ animationDelay: '200ms' }}>
        <div className="bg-white rounded-2xl border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-lg bg-green-50 flex items-center justify-center text-lg">😊</div>
            <span className="text-xs text-gray-400 font-medium">Avg. Mood ({days}d)</span>
          </div>
          <p className="text-2xl font-bold text-gray-800">{avgMood}<span className="text-sm text-gray-400 font-normal">/10</span></p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-lg bg-amber-50 flex items-center justify-center text-lg">⚡</div>
            <span className="text-xs text-gray-400 font-medium">Avg. Pain ({days}d)</span>
          </div>
          <p className="text-2xl font-bold text-gray-800">{avgPain}<span className="text-sm text-gray-400 font-normal">/10</span></p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center text-lg">📝</div>
            <span className="text-xs text-gray-400 font-medium">Logs Recorded</span>
          </div>
          <p className="text-2xl font-bold text-gray-800">{data.length}</p>
        </div>
      </div>

      {/* Chart */}
      <div className="animate-slide-up" style={{ animationDelay: '300ms' }}>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-700">Symptom Trends</h2>
          <div className="flex gap-1.5">
            {[7, 14, 30].map(d => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                  days === d
                    ? 'bg-teal-600 text-white shadow-md shadow-teal-500/20'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>
        {loading ? (
          <div className="bg-white rounded-2xl border border-gray-100 p-16 text-center">
            <div className="animate-pulse-soft text-gray-400 text-sm">Loading chart data...</div>
          </div>
        ) : (
          <SymptomChart data={data} />
        )}
      </div>

      {/* Disclaimer */}
      <MedicalDisclaimer />
    </div>
  )
}
