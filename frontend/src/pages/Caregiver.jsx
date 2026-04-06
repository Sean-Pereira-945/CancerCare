import { useState, useEffect } from 'react'
import { caregiverAPI } from '../lib/api'
import { useAuth } from '../hooks/useAuth'
import MedicalDisclaimer from '../components/MedicalDisclaimer'
import toast from 'react-hot-toast'

export default function Caregiver() {
  const { user } = useAuth()
  const [email, setEmail] = useState('')
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [linking, setLinking] = useState(false)

  useEffect(() => {
    if (user?.role === 'caregiver') {
      setLoading(true)
      caregiverAPI.getSummary()
        .then(res => setSummary(res.data))
        .catch(() => {})
        .finally(() => setLoading(false))
    }
  }, [user])

  const linkPatient = async (e) => {
    e.preventDefault()
    if (!email.trim()) return
    setLinking(true)
    try {
      const { data } = await caregiverAPI.link(email)
      toast.success(`Linked to ${data.patient_name}!`)
      // Refresh summary
      const s = await caregiverAPI.getSummary()
      setSummary(s.data)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to link')
    } finally {
      setLinking(false)
    }
  }

  if (user?.role !== 'caregiver') {
    return (
      <div className="p-6 max-w-2xl mx-auto space-y-6">
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center animate-slide-up">
          <div className="text-5xl mb-4">🤝</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Caregiver Portal</h1>
          <p className="text-gray-400 text-sm max-w-md mx-auto">
            This section is for caregivers. To access it, register as a caregiver and link to a patient's account to view their health summary.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div className="animate-slide-up">
        <h1 className="text-2xl font-bold text-gray-800">Caregiver Portal</h1>
        <p className="text-gray-400 text-sm mt-1">Monitor your patient's health journey</p>
      </div>

      {/* Link Patient */}
      <form onSubmit={linkPatient} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 animate-slide-up" style={{ animationDelay: '100ms' }}>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Link to Patient</h2>
        <div className="flex gap-2">
          <input value={email} onChange={e => setEmail(e.target.value)}
            placeholder="Enter patient's email address"
            type="email"
            className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
          <button type="submit" disabled={linking}
            className="px-5 py-2.5 rounded-xl bg-teal-600 text-white text-sm font-medium hover:bg-teal-700 transition-colors disabled:opacity-50">
            {linking ? '...' : 'Link'}
          </button>
        </div>
      </form>

      {/* Patient Summary */}
      {loading ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center animate-pulse-soft">
          <p className="text-gray-400 text-sm">Loading patient data...</p>
        </div>
      ) : summary?.error ? (
        <div className="bg-amber-50 border border-amber-200 text-amber-700 p-4 rounded-2xl text-sm">
          {summary.error}
        </div>
      ) : summary?.patient ? (
        <div className="space-y-4 animate-fade-in">
          {/* Patient Info */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Patient Information</h2>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center text-white text-lg font-bold">
                {summary.patient.name?.[0]?.toUpperCase()}
              </div>
              <div>
                <p className="font-semibold text-gray-700">{summary.patient.name}</p>
                <p className="text-sm text-gray-400 capitalize">{summary.patient.cancer_type} cancer</p>
              </div>
            </div>
          </div>

          {/* Medications */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Current Medications</h2>
            {summary.medications?.length > 0 ? (
              <div className="space-y-2">
                {summary.medications.map((med, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                    <span className="text-lg">💊</span>
                    <div>
                      <p className="text-sm font-medium text-gray-700">{med.name}</p>
                      <p className="text-xs text-gray-400">{med.dosage}</p>
                    </div>
                    <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${med.active ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                      {med.active ? 'Active' : 'Paused'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No medications recorded</p>
            )}
          </div>

          {/* Diet Adherence */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Diet Adherence</h2>
            <div className="flex items-center gap-4">
              <div className="text-3xl font-bold text-teal-600">{summary.diet_adherence?.rate || 0}%</div>
              <div className="flex-1">
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-teal-500 to-teal-400 rounded-full transition-all duration-500"
                    style={{ width: `${summary.diet_adherence?.rate || 0}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1">{summary.diet_adherence?.total || 0} meals logged</p>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <MedicalDisclaimer />
    </div>
  )
}
