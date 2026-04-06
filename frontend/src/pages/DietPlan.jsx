import { useState } from 'react'
import { dietAPI } from '../lib/api'
import { useAuth } from '../hooks/useAuth'
import DietCard from '../components/DietCard'
import MedicalDisclaimer from '../components/MedicalDisclaimer'
import toast from 'react-hot-toast'

export default function DietPlan() {
  const { user } = useAuth()
  const [form, setForm] = useState({
    cancer_type: user?.cancer_type || '',
    stage: '',
    fatigue: 5,
    nausea: 3,
    appetite: 'moderate',
    restrictions: 'none'
  })
  const [plan, setPlan] = useState(null)
  const [guidelines, setGuidelines] = useState(null)
  const [loading, setLoading] = useState(false)

  const update = (field, value) => setForm(prev => ({ ...prev, [field]: value }))

  const generatePlan = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await dietAPI.generatePlan(form)
      setPlan(data.plan)
      setGuidelines(data.guidelines)
      toast.success('Diet plan generated!')
    } catch {
      toast.error('Failed to generate plan. Check your API keys.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="animate-slide-up">
        <h1 className="text-2xl font-bold text-gray-800">Diet Plan Generator</h1>
        <p className="text-gray-400 text-sm mt-1">AI-powered personalized meal plans based on your condition</p>
      </div>

      {/* Form */}
      <form onSubmit={generatePlan} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 animate-slide-up" style={{ animationDelay: '100ms' }}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Cancer Type</label>
            <select value={form.cancer_type} onChange={e => update('cancer_type', e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 bg-white">
              <option value="">Select type</option>
              <option value="breast">Breast</option>
              <option value="lung">Lung</option>
              <option value="colorectal">Colorectal</option>
              <option value="prostate">Prostate</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Treatment Stage</label>
            <input value={form.stage} onChange={e => update('stage', e.target.value)}
              placeholder="e.g., Stage II, Post-surgery"
              className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Appetite</label>
            <select value={form.appetite} onChange={e => update('appetite', e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 bg-white">
              <option value="poor">Poor</option>
              <option value="moderate">Moderate</option>
              <option value="good">Good</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Fatigue ({form.fatigue}/10)</label>
            <input type="range" min="1" max="10" value={form.fatigue}
              onChange={e => update('fatigue', parseInt(e.target.value))}
              className="w-full accent-teal-600" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Nausea ({form.nausea}/10)</label>
            <input type="range" min="1" max="10" value={form.nausea}
              onChange={e => update('nausea', parseInt(e.target.value))}
              className="w-full accent-teal-600" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Dietary Restrictions</label>
            <input value={form.restrictions} onChange={e => update('restrictions', e.target.value)}
              placeholder="e.g., vegetarian, gluten-free"
              className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
          </div>
        </div>

        <button type="submit" disabled={loading}
          className="mt-5 px-8 py-3 rounded-xl bg-gradient-to-r from-teal-600 to-teal-500 text-white text-sm font-semibold hover:from-teal-700 hover:to-teal-600 transition-all shadow-lg shadow-teal-500/20 disabled:opacity-50">
          {loading ? 'Generating with AI...' : '🥗 Generate 7-Day Plan'}
        </button>
      </form>

      {/* Guidelines */}
      {guidelines && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-fade-in">
          <div className="bg-green-50 border border-green-200 rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-green-700 mb-2">✅ Emphasize</h3>
            <ul className="space-y-1">
              {guidelines.emphasize.map((item, i) => (
                <li key={i} className="text-sm text-green-600 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-green-400 rounded-full" />{item}
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-red-700 mb-2">❌ Avoid</h3>
            <ul className="space-y-1">
              {guidelines.avoid.map((item, i) => (
                <li key={i} className="text-sm text-red-600 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-red-400 rounded-full" />{item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Meal Plan */}
      {plan && Object.keys(plan).length > 0 && !plan.error && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 animate-fade-in">
          {Object.entries(plan).map(([day, meals]) => (
            <DietCard key={day} day={day} meals={meals} />
          ))}
        </div>
      )}

      {plan?.error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl text-sm">
          ⚠️ {plan.error}
        </div>
      )}

      <MedicalDisclaimer />
    </div>
  )
}
