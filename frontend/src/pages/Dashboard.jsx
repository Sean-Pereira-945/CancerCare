import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import SymptomChart from '../components/SymptomChart'
import DietAdherenceChart from '../components/DietAdherenceChart'
import MedicalDisclaimer from '../components/MedicalDisclaimer'
import { Link } from 'react-router-dom'
import { dietAPI, symptomsAPI } from '../lib/api'
import {
  ChatBubbleLeftRightIcon,
  HeartIcon,
  SparklesIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline'
import { useQuery } from '@tanstack/react-query'

export default function Dashboard() {
  const { user } = useAuth()
  const [days, setDays] = useState(14)

  const { data: trendsData, isLoading: loadingSymptoms, refetch: refetchSymptoms } = useQuery({
    queryKey: ['symptoms', 'trends', days],
    queryFn: () => symptomsAPI.getTrends(days).then(res => res.data.trends),
  })

  const { data: adherenceData, isLoading: loadingDiet, refetch: refetchDiet } = useQuery({
    queryKey: ['diet', 'trends', days],
    queryFn: () => dietAPI.getAdherenceTrends(days).then(res => res.data),
    refetchInterval: 10000, // Auto-update every 10 seconds
  })

  const data = trendsData || []
  const dietTrends = adherenceData || []

  const quickActions = [
    { path: '/chat', icon: ChatBubbleLeftRightIcon, label: 'AI Chat', desc: 'Ask care-related questions', color: 'bg-teal-50 text-teal-700 border-teal-100' },
    { path: '/symptoms', icon: HeartIcon, label: 'Log Symptoms', desc: 'Track daily health changes', color: 'bg-blue-50 text-blue-700 border-blue-100' },
    { path: '/diet', icon: SparklesIcon, label: 'Diet Plan', desc: 'Generate personalized guidance', color: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
    { path: '/reports', icon: DocumentTextIcon, label: 'Upload Report', desc: 'Summarize clinical documents', color: 'bg-violet-50 text-violet-700 border-violet-100' },
  ]

  // Calculate summary stats from trend data
  const avgMood = data.length > 0 ? (data.reduce((sum, d) => sum + (d.mood || 0), 0) / data.length).toFixed(1) : '--'
  const avgPain = data.length > 0 ? (data.reduce((sum, d) => sum + (d.pain || 0), 0) / data.length).toFixed(1) : '--'

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Greeting */}
      <div className="animate-slide-up">
        <h1 className="text-3xl font-bold text-gray-800">
          Welcome back, <span className="text-teal-700">{user?.name?.split(' ')[0] || 'there'}</span>
        </h1>
        <p className="text-gray-400 text-sm mt-1">Here's an overview of your health journey</p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 animate-slide-up" style={{ animationDelay: '100ms' }}>
        {quickActions.map(action => (
          <Link
            key={action.path}
            to={action.path}
            className="group surface-card surface-card-hover p-5"
          >
            <div className={`w-11 h-11 rounded-xl border ${action.color} flex items-center justify-center mb-3 transition-transform duration-300`}>
              <action.icon className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-semibold text-gray-700">{action.label}</h3>
            <p className="text-xs text-gray-400 mt-0.5">{action.desc}</p>
          </Link>
        ))}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 animate-slide-up" style={{ animationDelay: '200ms' }}>
        <div className="surface-card p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-lg bg-green-50 flex items-center justify-center text-lg">😊</div>
            <span className="text-xs text-gray-400 font-medium">Avg. Mood ({days}d)</span>
          </div>
          <p className="text-2xl font-bold text-gray-800">{avgMood}<span className="text-sm text-gray-400 font-normal">/10</span></p>
        </div>
        <div className="surface-card p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-lg bg-amber-50 flex items-center justify-center text-lg">⚡</div>
            <span className="text-xs text-gray-400 font-medium">Avg. Pain ({days}d)</span>
          </div>
          <p className="text-2xl font-bold text-gray-800">{avgPain}<span className="text-sm text-gray-400 font-normal">/10</span></p>
        </div>
        <div className="surface-card p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center text-lg">🥗</div>
            <span className="text-xs text-gray-400 font-medium">Diet Adherence</span>
          </div>
          <p className="text-2xl font-bold text-gray-800">{dietTrends.length > 0 ? dietTrends[dietTrends.length - 1].rate : 0}<span className="text-sm text-gray-400 font-normal">%</span></p>
        </div>
      </div>

      {/* Recent Caregiver Updates */}
      {dietTrends.length > 0 && (
        <div className="animate-slide-up" style={{ animationDelay: '250ms' }}>
          <div className="bg-teal-50 border border-teal-100 rounded-2xl p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-sm">🤝</div>
            <div className="flex-1">
              <h3 className="text-sm font-bold text-teal-800">Latest Caregiver Update</h3>
              <p className="text-xs text-teal-700">Your caregiver recently logged your {days}d adherence trends.</p>
            </div>
            <div className="text-right">
              <span className="text-[10px] font-bold text-teal-600 uppercase tracking-widest">Status</span>
              <p className="text-xs font-bold text-teal-800">Synced</p>
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="animate-slide-up" style={{ animationDelay: '300ms' }}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-700">Symptom Trends</h2>
            <button onClick={() => refetchSymptoms()} className="p-1 hover:bg-gray-100 rounded-full transition-colors text-gray-400" title="Refresh data">
              <SparklesIcon className="w-4 h-4" />
            </button>
          </div>
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
        {loadingSymptoms ? (
          <div className="bg-white rounded-2xl border border-gray-100 p-16 text-center">
            <div className="animate-pulse-soft text-gray-400 text-sm">Loading chart data...</div>
          </div>
        ) : (
          <SymptomChart data={data} />
        )}
      </div>

      {/* Diet Adherence Chart */}
      <div className="animate-slide-up" style={{ animationDelay: '400ms' }}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-700">Diet Adherence</h2>
            <button onClick={() => refetchDiet()} className="p-1 hover:bg-gray-100 rounded-full transition-colors text-gray-400" title="Refresh data">
              <SparklesIcon className="w-4 h-4" />
            </button>
          </div>
          <span className="text-xs text-gray-400 italic">Updated by your caregiver</span>
        </div>
        {loadingDiet ? (
          <div className="bg-white rounded-2xl border border-gray-100 p-16 text-center">
            <div className="animate-pulse-soft text-gray-400 text-sm">Loading adherence data...</div>
          </div>
        ) : (
          <DietAdherenceChart data={dietTrends} />
        )}
      </div>

      {/* Disclaimer */}
      <MedicalDisclaimer />
    </div>
  )
}
