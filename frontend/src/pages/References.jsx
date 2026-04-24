import { trialsAPI } from '../lib/api'
import { useQuery } from '@tanstack/react-query'

export default function References() {
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const { data: docs = [], isLoading: loading } = useQuery({
    queryKey: ['references'],
    queryFn: () => trialsAPI.getReferences().then(res => res.data.documents || []),
  })

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 animate-slide-up">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Knowledge Base References</h1>
        <p className="text-gray-400 text-sm mt-1">Medical documents used by the AI assistant</p>
      </div>
      
      {loading ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center animate-pulse-soft">
          <p className="text-gray-400">Loading documents...</p>
        </div>
      ) : docs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {docs.map((doc, idx) => (
            <a key={idx} href={`${API_BASE}${doc.download_url}`} target="_blank" rel="noopener noreferrer" className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm hover:border-teal-200 hover:shadow-md transition-all flex items-center gap-4 group">
              <div className="w-12 h-12 bg-rose-50 text-rose-500 rounded-xl flex items-center justify-center text-xl group-hover:bg-rose-100 transition-colors">
                📄
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold text-gray-700 text-sm truncate">{doc.name}</h3>
                <p className="text-xs text-gray-400">{(doc.size_bytes / 1024 / 1024).toFixed(2)} MB • PDF Document</p>
              </div>
            </a>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
          <p className="text-gray-400">No reference documents found.</p>
        </div>
      )}
    </div>
  )
}
