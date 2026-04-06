import { useState } from 'react'
import { trialsAPI } from '../lib/api'
import MedicalDisclaimer from '../components/MedicalDisclaimer'
import toast from 'react-hot-toast'

export default function ClinicalTrials() {
  const [query, setQuery] = useState('')
  const [trials, setTrials] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const search = async (e) => {
    e?.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setSearched(true)
    try {
      const { data } = await trialsAPI.searchTrials(query)
      setTrials(data.trials || [])
      setTotal(data.total || 0)
    } catch {
      toast.error('Failed to search trials')
    } finally {
      setLoading(false)
    }
  }

  const quickSearches = ['breast', 'lung', 'colorectal', 'prostate', 'leukemia', 'melanoma']

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="animate-slide-up">
        <h1 className="text-2xl font-bold text-gray-800">Clinical Trials</h1>
        <p className="text-gray-400 text-sm mt-1">Search recruiting clinical trials from ClinicalTrials.gov</p>
      </div>

      {/* Search */}
      <form onSubmit={search} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 animate-slide-up" style={{ animationDelay: '100ms' }}>
        <div className="flex gap-2">
          <input
            value={query} onChange={e => setQuery(e.target.value)}
            placeholder="Search by cancer type, treatment, or keyword..."
            className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
          <button type="submit" disabled={loading}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-teal-500 text-white text-sm font-medium hover:from-teal-700 hover:to-teal-600 transition-all shadow-md shadow-teal-500/20 disabled:opacity-50">
            {loading ? 'Searching...' : '🔬 Search'}
          </button>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {quickSearches.map(q => (
            <button key={q} type="button"
              onClick={() => { setQuery(q); }}
              className="px-3 py-1.5 bg-gray-50 hover:bg-teal-50 text-gray-500 hover:text-teal-600 text-xs rounded-lg transition-colors capitalize">
              {q}
            </button>
          ))}
        </div>
      </form>

      {/* Results */}
      {searched && (
        <div className="animate-fade-in">
          <p className="text-sm text-gray-400 mb-4">
            {loading ? 'Searching...' : `Found ${total} trials · Showing ${trials.length} results`}
          </p>

          {trials.length === 0 && !loading ? (
            <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
              <div className="text-4xl mb-3">🔍</div>
              <p className="text-gray-400 text-sm">No trials found. Try a different search term.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {trials.map((trial, i) => (
                <div key={trial.id || i} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 hover:shadow-md transition-all">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-mono text-teal-600 bg-teal-50 px-2 py-0.5 rounded">
                          {trial.id}
                        </span>
                        {trial.phase && (
                          <span className="text-xs text-purple-600 bg-purple-50 px-2 py-0.5 rounded">
                            {Array.isArray(trial.phase) ? trial.phase.join(', ') : trial.phase}
                          </span>
                        )}
                      </div>
                      <h3 className="text-sm font-semibold text-gray-700 mt-1">{trial.title}</h3>
                      {trial.summary && (
                        <p className="text-xs text-gray-400 mt-2 leading-relaxed">{trial.summary}</p>
                      )}
                    </div>
                    <a
                      href={`https://clinicaltrials.gov/study/${trial.id}`}
                      target="_blank" rel="noopener noreferrer"
                      className="px-3 py-1.5 bg-teal-50 text-teal-600 text-xs font-medium rounded-lg hover:bg-teal-100 transition-colors flex-shrink-0"
                    >
                      View ↗
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <MedicalDisclaimer />
    </div>
  )
}
