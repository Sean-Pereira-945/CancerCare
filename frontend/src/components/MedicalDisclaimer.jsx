export default function MedicalDisclaimer() {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-700 leading-relaxed">
      <div className="flex items-start gap-2">
        <svg className="w-4 h-4 mt-0.5 flex-shrink-0 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <p>
          <strong>Medical Disclaimer:</strong> CancerCare AI is an educational tool providing general health information. It does NOT constitute medical advice, diagnosis, or treatment recommendations. Always consult your oncologist or healthcare provider before making any decisions about your care.
        </p>
      </div>
    </div>
  )
}
