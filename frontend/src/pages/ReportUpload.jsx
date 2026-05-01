import { useState } from 'react'
import { reportsAPI } from '../lib/api'
import MedicalDisclaimer from '../components/MedicalDisclaimer'
import toast from 'react-hot-toast'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export default function ReportUpload() {
  const queryClient = useQueryClient()
  const [file, setFile] = useState(null)

  const { data: reports = [], isLoading: loading } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportsAPI.getReports().then(res => res.data.reports || []),
  })

  const uploadMutation = useMutation({
    mutationFn: (file) => reportsAPI.uploadReport(file),
    onSuccess: () => {
      toast.success('Report uploaded and indexed!')
      setFile(null)
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Upload failed')
    },
  })

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file) return toast.error('Select a PDF file first')
    uploadMutation.mutate(file)
  }

  const uploading = uploadMutation.isPending

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="animate-slide-up">
        <h1 className="text-2xl font-bold text-gray-800">Medical Report Upload</h1>
        <p className="text-gray-400 text-sm mt-1">Upload PDF reports for AI analysis — findings are used by the chatbot</p>
      </div>

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 animate-slide-up" style={{ animationDelay: '100ms' }}>
        <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center hover:border-teal-400 transition-colors">
          <div className="text-4xl mb-3">📄</div>
          <p className="text-sm text-gray-500 mb-3">
            {file ? file.name : 'Drag & drop or click to select a PDF report'}
          </p>
          <input
            type="file"
            accept=".pdf"
            onChange={e => setFile(e.target.files?.[0] || null)}
            className="hidden"
            id="report-upload"
          />
          <label
            htmlFor="report-upload"
            className="inline-block px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm rounded-xl cursor-pointer transition-colors"
          >
            Choose PDF File
          </label>
          <p className="text-xs text-gray-400 mt-2">Max 10MB · PDF only</p>
        </div>

        <button
          type="submit" disabled={uploading || !file}
          className="mt-4 px-8 py-3 rounded-xl bg-gradient-to-r from-teal-600 to-teal-500 text-white text-sm font-semibold hover:from-teal-700 hover:to-teal-600 transition-all shadow-lg shadow-teal-500/20 disabled:opacity-50"
        >
          {uploading ? 'Analyzing...' : '📋 Upload & Analyze'}
        </button>
      </form>

      {/* Extracted Information Section - Only show if data exists */}
      {uploadMutation.data && (uploadMutation.data.extracted?.summary || uploadMutation.data.extracted?.overall_signal || Object.keys(uploadMutation.data.extracted || {}).filter(k => k !== 'summary' && k !== 'recovery_status' && k !== 'key_metrics' && k !== 'overall_signal' && k !== 'signal_evidence' && k !== 'table_highlights' && k !== 'table_excerpt').length > 0) && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 animate-fade-in">
          {/* Risk Assessment */}
          {uploadMutation.data.risk_assessment && !uploadMutation.data.risk_assessment.error && (
            <div className="mb-6 p-4 bg-teal-50 rounded-2xl border border-teal-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-teal-800">Initial Risk Assessment</h3>
                <p className="text-xs text-teal-600">Based on extracted clinical markers</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-teal-700">{uploadMutation.data.risk_assessment.risk_score}%</div>
                <div className="text-xs font-bold text-teal-500 uppercase tracking-wider">{uploadMutation.data.risk_assessment.risk_level} Risk</div>
              </div>
            </div>
          )}

          <h2 className="text-lg font-semibold text-gray-700 mb-4">Extracted Information</h2>
          
          {/* AI Analysis Summary */}
          {uploadMutation.data.extracted?.summary && (
            <div className="mb-6 space-y-3">
              <div className="bg-teal-50/50 rounded-2xl p-5 border border-teal-100/50">
                <span className="text-[10px] font-bold text-teal-600 uppercase tracking-widest">AI Insight: Recovery Status</span>
                <p className="text-lg font-bold text-teal-800 mt-1">{uploadMutation.data.extracted.recovery_status}</p>
                <div className="mt-4 pt-4 border-t border-teal-100">
                  <span className="text-[10px] font-bold text-teal-600 uppercase tracking-widest">Clinical Summary</span>
                  <p className="text-sm text-teal-900 leading-relaxed mt-2">{uploadMutation.data.extracted.summary}</p>
                </div>
              </div>
            </div>
          )}

          {uploadMutation.data.extracted?.overall_signal && (
            <div className="mb-6 bg-white rounded-2xl border border-teal-100 p-5">
              <span className="text-[10px] font-bold text-teal-600 uppercase tracking-widest">Overall Signal</span>
              <p className="text-lg font-bold text-teal-800 mt-1">{uploadMutation.data.extracted.overall_signal}</p>
              {Array.isArray(uploadMutation.data.extracted.signal_evidence) && uploadMutation.data.extracted.signal_evidence.length > 0 && (
                <ul className="mt-3 text-sm text-teal-900 space-y-1 list-disc ml-5">
                  {uploadMutation.data.extracted.signal_evidence.slice(0, 6).map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {Array.isArray(uploadMutation.data.extracted?.table_highlights) && uploadMutation.data.extracted.table_highlights.length > 0 && (
            <div className="mb-6 bg-gray-50 rounded-2xl border border-gray-100 p-5">
              <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Table Highlights</span>
              <ul className="mt-3 text-sm text-gray-700 space-y-1 list-disc ml-5">
                {uploadMutation.data.extracted.table_highlights.slice(0, 6).map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {uploadMutation.data.extracted && Object.keys(uploadMutation.data.extracted).filter(k => k !== 'summary' && k !== 'recovery_status' && k !== 'key_metrics' && k !== 'overall_signal' && k !== 'signal_evidence' && k !== 'table_highlights' && k !== 'table_excerpt').length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {Object.entries(uploadMutation.data.extracted)
                .filter(([key]) => key !== 'summary' && key !== 'recovery_status' && key !== 'key_metrics' && key !== 'overall_signal' && key !== 'signal_evidence' && key !== 'table_highlights' && key !== 'table_excerpt')
                .map(([key, value]) => (
                <div key={key} className="bg-gray-50 rounded-xl p-3">
                  <span className="text-xs text-gray-400 font-medium capitalize">{key.replace('_', ' ')}</span>
                  <p className="text-sm text-gray-700 font-medium mt-0.5">
                    {Array.isArray(value) ? value.join(', ') : value}
                  </p>
                </div>
              ))}
            </div>
          )}
          <p className="text-xs text-teal-600 mt-4 flex items-center gap-1">
            ✅ Report indexed — you can now ask the chatbot questions about this report
          </p>
        </div>
      )}

      {/* Past Reports */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 animate-slide-up" style={{ animationDelay: '200ms' }}>
        <h2 className="text-lg font-semibold text-gray-700 mb-4">Your Reports</h2>
        {loading ? (
          <p className="text-sm text-gray-400">Loading...</p>
        ) : reports.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-2">📂</div>
            <p className="text-sm text-gray-400">No reports uploaded yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((report, i) => {
              const classification = report.extracted_fields?.signal_classification
              const dateLabel = report.uploaded_at ? new Date(report.uploaded_at).toLocaleDateString() : 'Unknown date'
              const pagesLabel = report.page_count ? `${report.page_count} pages` : null
              const metaLabel = pagesLabel ? `${dateLabel} · ${pagesLabel}` : dateLabel

              return (
                <div key={i} className="flex items-start gap-4 p-4 bg-gray-50 rounded-xl hover:bg-teal-50 transition-colors">
                  <div className="w-10 h-10 rounded-lg bg-teal-100 flex items-center justify-center text-teal-600 text-lg">📋</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">{report.filename}</p>
                    <p className="text-xs text-gray-400 mt-1">{metaLabel}</p>
                    <p className="text-xs text-gray-400 mt-1">Signal derived from report analysis</p>
                  </div>
                  {report.extracted_fields && Object.keys(report.extracted_fields).filter(k => k !== 'summary' && k !== 'recovery_status' && k !== 'key_metrics').length > 0 && (
                    <span className="text-xs text-teal-600 bg-teal-50 px-2.5 py-1 rounded-full">
                      {Object.keys(report.extracted_fields).filter(k => k !== 'summary' && k !== 'recovery_status' && k !== 'key_metrics').length} markers
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      <MedicalDisclaimer />
    </div>
  )
}
