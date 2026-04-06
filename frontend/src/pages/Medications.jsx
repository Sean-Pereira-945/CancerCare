import { useState, useEffect } from 'react'
import { medsAPI } from '../lib/api'
import MedicalDisclaimer from '../components/MedicalDisclaimer'
import toast from 'react-hot-toast'

export default function Medications() {
  const [medications, setMedications] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    name: '', dosage: '', frequency: '', times: [], notes: ''
  })

  useEffect(() => {
    loadMeds()
  }, [])

  const loadMeds = async () => {
    try {
      const { data } = await medsAPI.list()
      setMedications(data.medications || [])
    } catch {}
    setLoading(false)
  }

  const update = (field, value) => setForm(prev => ({ ...prev, [field]: value }))

  const handleAdd = async (e) => {
    e.preventDefault()
    try {
      await medsAPI.add(form)
      toast.success('Medication added!')
      setShowForm(false)
      setForm({ name: '', dosage: '', frequency: '', times: [], notes: '' })
      loadMeds()
    } catch {
      toast.error('Failed to add medication')
    }
  }

  const toggleActive = async (id, active) => {
    try {
      await medsAPI.update(id, { active: !active })
      toast.success(active ? 'Medication deactivated' : 'Medication reactivated')
      loadMeds()
    } catch {
      toast.error('Failed to update')
    }
  }

  const deleteMed = async (id) => {
    try {
      await medsAPI.delete(id)
      toast.success('Medication removed')
      loadMeds()
    } catch {
      toast.error('Failed to delete')
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between animate-slide-up">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Medications</h1>
          <p className="text-gray-400 text-sm mt-1">Track your medications and dosages</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-teal-500 text-white text-sm font-medium hover:from-teal-700 hover:to-teal-600 transition-all shadow-md shadow-teal-500/20"
        >
          {showForm ? 'Cancel' : '+ Add Medication'}
        </button>
      </div>

      {/* Add Form */}
      {showForm && (
        <form onSubmit={handleAdd} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4 animate-fade-in">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Medication Name *</label>
              <input required value={form.name} onChange={e => update('name', e.target.value)}
                placeholder="e.g., Tamoxifen"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Dosage</label>
              <input value={form.dosage} onChange={e => update('dosage', e.target.value)}
                placeholder="e.g., 20mg"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Frequency</label>
              <select value={form.frequency} onChange={e => update('frequency', e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 bg-white">
                <option value="">Select frequency</option>
                <option value="once daily">Once Daily</option>
                <option value="twice daily">Twice Daily</option>
                <option value="three times daily">Three Times Daily</option>
                <option value="weekly">Weekly</option>
                <option value="as needed">As Needed</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Notes</label>
              <input value={form.notes} onChange={e => update('notes', e.target.value)}
                placeholder="e.g., Take with food"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
            </div>
          </div>
          <button type="submit"
            className="px-6 py-2.5 rounded-xl bg-teal-600 text-white text-sm font-medium hover:bg-teal-700 transition-colors">
            Add Medication
          </button>
        </form>
      )}

      {/* Medications List */}
      <div className="space-y-3 animate-slide-up" style={{ animationDelay: '100ms' }}>
        {loading ? (
          <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
            <p className="text-gray-400 text-sm">Loading medications...</p>
          </div>
        ) : medications.length === 0 ? (
          <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
            <div className="text-4xl mb-3">💊</div>
            <p className="text-gray-400 text-sm">No medications added yet</p>
          </div>
        ) : (
          medications.map(med => (
            <div key={med.id} className={`bg-white rounded-2xl border border-gray-100 p-5 flex items-center gap-4 hover:shadow-md transition-all ${!med.active ? 'opacity-50' : ''}`}>
              <div className={`w-11 h-11 rounded-xl flex items-center justify-center text-lg ${med.active ? 'bg-teal-50' : 'bg-gray-100'}`}>
                💊
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-gray-700">{med.name}</h3>
                  {!med.active && <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">Inactive</span>}
                </div>
                <p className="text-xs text-gray-400 mt-0.5">
                  {[med.dosage, med.frequency].filter(Boolean).join(' · ') || 'No details'}
                </p>
                {med.notes && <p className="text-xs text-gray-400 italic mt-0.5">{med.notes}</p>}
              </div>
              <div className="flex gap-2">
                <button onClick={() => toggleActive(med.id, med.active)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    med.active ? 'bg-amber-50 text-amber-600 hover:bg-amber-100' : 'bg-green-50 text-green-600 hover:bg-green-100'
                  }`}>
                  {med.active ? 'Pause' : 'Resume'}
                </button>
                <button onClick={() => deleteMed(med.id)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-50 text-red-500 hover:bg-red-100 transition-colors">
                  Remove
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <MedicalDisclaimer />
    </div>
  )
}
