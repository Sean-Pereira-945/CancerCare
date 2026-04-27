import { caregiverAPI } from '../lib/api'
import { useAuth } from '../hooks/useAuth'
import MedicalDisclaimer from '../components/MedicalDisclaimer'
import toast from 'react-hot-toast'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
export default function Caregiver() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const [mealForm, setMealForm] = useState({ 
    type: 'lunch', 
    adhered: true, 
    date: new Date().toISOString().split('T')[0] 
  })

  const { data: summary, isLoading: loading } = useQuery({
    queryKey: ['caregiver', 'summary'],
    queryFn: () => caregiverAPI.getSummary().then(res => res.data),
    enabled: user?.role === 'caregiver',
  })

  const linkMutation = useMutation({
    mutationFn: (email) => caregiverAPI.link(email),
    onSuccess: (res) => {
      toast.success(`Linked to ${res.data.patient_name}!`)
      queryClient.invalidateQueries({ queryKey: ['caregiver', 'summary'] })
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Failed to link')
    },
  })

  const logMedicationMutation = useMutation({
    mutationFn: (medId) => caregiverAPI.logMedication(medId),
    onSuccess: () => {
      toast.success('Medication logged!')
      queryClient.invalidateQueries({ queryKey: ['caregiver', 'summary'] })
    },
    onError: () => {
      toast.error('Failed to log medication')
    },
  })

  const logMealMutation = useMutation({
    mutationFn: (data) => caregiverAPI.logMeal(data),
    onSuccess: () => {
      toast.success('Meal logged!')
      queryClient.invalidateQueries({ queryKey: ['caregiver', 'summary'] })
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Failed to log meal')
    },
  })

  const linkPatient = (e) => {
    e.preventDefault()
    if (!email.trim()) return
    linkMutation.mutate(email)
  }

  const handleLogMedication = (medId) => {
    logMedicationMutation.mutate(medId)
  }

  const handleLogMeal = (e) => {
    e.preventDefault()
    // Use the selected date at noon to avoid timezone edge cases
    const selectedDate = new Date(`${mealForm.date}T12:00:00`)
    logMealMutation.mutate({
      date: selectedDate.toISOString(),
      meal_type: mealForm.type,
      adhered_to_plan: mealForm.adhered
    })
  }

  const linking = linkMutation.isPending
  const loggingMeal = logMealMutation.isPending

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
          {/* Caregiver & Patient Profiles */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Caregiver Info */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Caregiver Profile</h2>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center text-white text-lg font-bold">
                  {summary.caregiver?.name?.[0]?.toUpperCase() || 'C'}
                </div>
                <div>
                  <p className="font-semibold text-gray-700">{summary.caregiver?.name || user?.name}</p>
                  <p className="text-sm text-gray-400">{summary.caregiver?.email || user?.email}</p>
                </div>
              </div>
            </div>

            {/* Patient Info */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Linked Patient</h2>
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
          </div>

          {/* Medications & Reminders */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Medications & Reminders</h2>
            {summary.medications?.length > 0 ? (
              <div className="space-y-3">
                {summary.medications.map((med, i) => (
                  <div key={i} className="flex flex-col gap-2 p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className="flex items-center gap-3">
                      <span className="text-lg">💊</span>
                      <div>
                        <p className="text-sm font-medium text-gray-700">{med.name} <span className="text-xs text-gray-400 font-normal ml-1">({med.dosage})</span></p>
                        <p className="text-xs text-teal-600 font-medium">{med.frequency} {med.times?.length > 0 ? `• ${med.times.join(', ')}` : ''}</p>
                      </div>
                      <div className="ml-auto flex items-center gap-2">
                        {med.active && !med.taken_today && (
                          <button onClick={() => handleLogMedication(med.id)} className="text-xs px-3 py-1 bg-teal-600 text-white rounded-lg hover:bg-teal-700">
                            Mark Taken
                          </button>
                        )}
                        {med.taken_today && (
                          <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-lg border border-green-100 flex items-center gap-1">
                            ✓ Taken Today
                          </span>
                        )}
                        <span className={`text-xs px-2 py-0.5 rounded-full ${med.active ? 'bg-green-50 text-green-600' : 'bg-gray-200 text-gray-500'}`}>
                          {med.active ? 'Active' : 'Paused'}
                        </span>
                      </div>
                    </div>
                    {med.notes && (
                      <div className="ml-9 mt-1 text-xs text-amber-700 bg-amber-50 px-3 py-2 rounded-lg border border-amber-100">
                        <span className="font-semibold">Instruction:</span> {med.notes}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No medications recorded</p>
            )}
          </div>

          {/* Symptom Trends */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Symptom Trends (Last 7 Logs)</h2>
            {summary.symptom_trends?.length > 0 ? (
              <div className="space-y-2">
                {summary.symptom_trends.map((log, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100 text-xs">
                    <div className="flex flex-col">
                      <span className="font-semibold text-gray-700">{new Date(log.date).toLocaleDateString()}</span>
                      <span className="text-gray-400">Mood: {log.mood}/10</span>
                    </div>
                    <div className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <span className="text-amber-600 font-bold">{log.pain}</span>
                        <span className="text-[10px] text-gray-400">Pain</span>
                      </div>
                      <div className="flex flex-col items-center">
                        <span className="text-blue-600 font-bold">{log.fatigue}</span>
                        <span className="text-[10px] text-gray-400">Fatigue</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No symptom logs recorded yet</p>
            )}
          </div>

          {/* Medical Reports */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Clinical Reports</h2>
            {summary.reports?.length > 0 ? (
              <div className="space-y-3">
                {summary.reports.map((report, i) => (
                  <div key={i} className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-bold text-gray-700">{report.filename}</p>
                      <span className="text-[10px] text-gray-400">{new Date(report.uploaded_at).toLocaleDateString()}</span>
                    </div>
                    {report.extracted_fields?.summary && (
                      <div className="text-xs text-teal-800 bg-teal-50/50 p-3 rounded-lg border border-teal-100/50 leading-relaxed">
                        <span className="font-bold">AI Summary:</span> {report.extracted_fields.summary}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No medical reports uploaded by patient</p>
            )}
          </div>

          {/* Diet Instructions & Adherence */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Dietary Instructions & Adherence</h2>
            
            {summary.diet_instructions?.guidelines && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
                <div className="bg-green-50 rounded-xl p-4 border border-green-100">
                  <h3 className="text-xs font-bold text-green-800 uppercase tracking-wider mb-2">Recommended (Emphasize)</h3>
                  <ul className="text-sm text-green-700 list-disc pl-4 space-y-1">
                    {summary.diet_instructions.guidelines.emphasize?.map((item, idx) => (
                      <li key={idx} className="capitalize">{item}</li>
                    ))}
                  </ul>
                </div>
                <div className="bg-red-50 rounded-xl p-4 border border-red-100">
                  <h3 className="text-xs font-bold text-red-800 uppercase tracking-wider mb-2">Avoid / Limit</h3>
                  <ul className="text-sm text-red-700 list-disc pl-4 space-y-1">
                    {summary.diet_instructions.guidelines.avoid?.map((item, idx) => (
                      <li key={idx} className="capitalize">{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {summary.diet_instructions?.full_plan && (
              <div className="mb-6">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">7-Day Meal Schedule</h3>
                <div className="space-y-3">
                  {summary.diet_instructions.full_plan.slice(0, 3).map((day, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                      <p className="text-[10px] font-bold text-teal-600 mb-1">DAY {day.day}</p>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                        <div><span className="font-semibold">B:</span> {day.breakfast}</div>
                        <div><span className="font-semibold">L:</span> {day.lunch}</div>
                        <div><span className="font-semibold">D:</span> {day.dinner}</div>
                      </div>
                    </div>
                  ))}
                  <p className="text-[10px] text-gray-400 italic text-center">... showing first 3 days of plan ...</p>
                </div>
              </div>
            )}

            <div className="flex items-center gap-4 pt-4 border-t border-gray-50">
              <div className="text-3xl font-bold text-teal-600">{summary.diet_adherence?.rate || 0}%</div>
              <div className="flex-1">
                <p className="text-xs font-medium text-gray-600 mb-1">Diet Plan Adherence</p>
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-teal-500 to-teal-400 rounded-full transition-all duration-500"
                    style={{ width: `${summary.diet_adherence?.rate || 0}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1">{summary.diet_adherence?.total || 0} meals logged by patient</p>
              </div>
            </div>

            {/* Meal Logging Form */}
            <form onSubmit={handleLogMeal} className="mt-5 p-4 bg-gray-50 rounded-xl border border-gray-100 flex flex-wrap items-center gap-3">
              <span className="text-sm font-semibold text-gray-700">Log Meal:</span>
              <input 
                type="date" 
                value={mealForm.date} 
                onChange={e => setMealForm({...mealForm, date: e.target.value})}
                className="text-sm border-gray-200 rounded-lg px-3 py-1.5 focus:ring-teal-500/20 focus:border-teal-500"
              />
              <select value={mealForm.type} onChange={e => setMealForm({...mealForm, type: e.target.value})} className="text-sm border-gray-200 rounded-lg px-3 py-1.5 focus:ring-teal-500/20 focus:border-teal-500">
                <option value="breakfast">Breakfast</option>
                <option value="lunch">Lunch</option>
                <option value="dinner">Dinner</option>
                <option value="snack">Snack</option>
              </select>
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input type="checkbox" checked={mealForm.adhered} onChange={e => setMealForm({...mealForm, adhered: e.target.checked})} className="rounded text-teal-600 focus:ring-teal-500/20" />
                Followed Diet
              </label>
              <button type="submit" disabled={loggingMeal} className="ml-auto px-4 py-1.5 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700 disabled:opacity-50">
                {loggingMeal ? '...' : 'Log'}
              </button>
            </form>
          </div>
        </div>
      ) : null}

      <MedicalDisclaimer />
    </div>
  )
}
