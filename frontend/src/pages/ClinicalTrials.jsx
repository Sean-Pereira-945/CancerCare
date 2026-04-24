import { trialsAPI } from '../lib/api'
import { useAuth } from '../hooks/useAuth'
import { useQuery } from '@tanstack/react-query'

export default function ClinicalTrials() {
  const { user } = useAuth()

  const { data: trials = [], isLoading: loading } = useQuery({
    queryKey: ['trials', user?.cancer_type],
    queryFn: () => trialsAPI.searchTrials(user.cancer_type).then(res => res.data.trials || []),
    enabled: !!user?.cancer_type,
  })

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 animate-slide-up">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Clinical Trials</h1>
        <p className="text-gray-400 text-sm mt-1">Live recruiting trials for {user?.cancer_type || 'your'} cancer</p>
      </div>
      
      {loading ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center animate-pulse-soft">
          <p className="text-gray-400">Searching ClinicalTrials.gov...</p>
        </div>
      ) : trials.length > 0 ? (
        <div className="space-y-4">
          {trials.map(trial => (
            <div key={trial.id} className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-gray-800 text-lg">{trial.title}</h3>
                <span className="text-xs bg-teal-50 text-teal-700 px-2 py-1 rounded-full font-medium whitespace-nowrap">
                  {trial.status}
                </span>
              </div>
              <p className="text-sm text-gray-500 mb-4">{trial.summary}</p>
              <div className="flex gap-4 text-xs text-gray-400 font-medium">
                <span>Phase: {trial.phase?.join(', ') || 'N/A'}</span>
                <span>NCT ID: {trial.id}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
          <p className="text-gray-400">No recruiting trials found at this time.</p>
        </div>
      )}
    </div>
  )
}
