import { useState } from 'react'
import { symptomsAPI } from '../lib/api'
import MedicalDisclaimer from '../components/MedicalDisclaimer'
import toast from 'react-hot-toast'

export default function SymptomTracker() {
  const today = new Date().toISOString().split('T')[0]
  const [form, setForm] = useState({
    date: today,
    fatigue: 5,
    nausea: 3,
    pain: 3,
    appetite: 5,
    mood: 5,
    sleep_hours: 7,
    journal_text: ''
  })
  const [loading, setLoading] = useState(false)
  const [alert, setAlert] = useState(null)

  const update = (field, value) => setForm(prev => ({ ...prev, [field]: value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await symptomsAPI.logSymptoms(form)
      toast.success('Symptoms logged successfully!')
      if (data.alert) setAlert(data.alert)
    } catch {
      toast.error('Failed to log symptoms')
    } finally {
      setLoading(false)
    }
  }

  const sliders = [
    { key: 'fatigue', label: 'Fatigue Level', emoji: '😴', color: 'bg-red-500', max: 10 },
    { key: 'nausea', label: 'Nausea Level', emoji: '🤢', color: 'bg-purple-500', max: 10 },
    { key: 'pain', label: 'Pain Level', emoji: '😣', color: 'bg-amber-500', max: 10 },
    { key: 'appetite', label: 'Appetite', emoji: '🍽️', color: 'bg-blue-500', max: 10 },
    { key: 'mood', label: 'Mood', emoji: '😊', color: 'bg-green-500', max: 10 },
  ]

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div className="animate-slide-up">
        <h1 className="text-2xl font-bold text-gray-800">Symptom Tracker</h1>
        <p className="text-gray-400 text-sm mt-1">Log how you're feeling today</p>
      </div>

      {alert && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 p-4 rounded-2xl text-sm animate-fade-in">
          💙 {alert}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-6 animate-slide-up" style={{ animationDelay: '100ms' }}>
        {/* Date */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Date</label>
          <input
            type="date" value={form.date}
            onChange={e => update('date', e.target.value)}
            className="px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
        </div>

        {/* Symptom Sliders */}
        {sliders.map(({ key, label, emoji, color, max }) => (
          <div key={key}>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <span>{emoji}</span> {label}
              </label>
              <span className={`text-xs font-bold px-2.5 py-1 rounded-full text-white ${color}`}>
                {form[key]}/{max}
              </span>
            </div>
            <input
              type="range" min="1" max={max} value={form[key]}
              onChange={e => update(key, parseInt(e.target.value))}
              className="w-full h-2 rounded-full appearance-none cursor-pointer accent-teal-600"
              style={{
                background: `linear-gradient(to right, #0d9488 0%, #0d9488 ${(form[key] / max) * 100}%, #e2e8f0 ${(form[key] / max) * 100}%, #e2e8f0 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-gray-300 mt-1">
              <span>Low</span><span>High</span>
            </div>
          </div>
        ))}

        {/* Sleep */}
        <div>
          <label className="text-sm font-medium text-gray-600 flex items-center gap-2 mb-2">
            <span>💤</span> Hours of Sleep
          </label>
          <input
            type="number" min="0" max="24" step="0.5"
            value={form.sleep_hours}
            onChange={e => update('sleep_hours', parseFloat(e.target.value))}
            className="w-24 px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
        </div>

        {/* Journal */}
        <div>
          <label className="text-sm font-medium text-gray-600 flex items-center gap-2 mb-2">
            <span>📝</span> How are you feeling? (Journal)
          </label>
          <textarea
            rows={3} value={form.journal_text}
            onChange={e => update('journal_text', e.target.value)}
            className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 resize-none"
            placeholder="Write a few words about your day... This helps us analyze your mood."
          />
          <p className="text-xs text-gray-400 mt-1">Your entry will be analyzed for mood patterns using AI.</p>
        </div>

        <button
          type="submit" disabled={loading}
          className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-600 to-teal-500 text-white text-sm font-semibold hover:from-teal-700 hover:to-teal-600 transition-all shadow-lg shadow-teal-500/20 disabled:opacity-50"
        >
          {loading ? 'Saving...' : 'Log Symptoms'}
        </button>
      </form>

      <MedicalDisclaimer />
    </div>
  )
}
