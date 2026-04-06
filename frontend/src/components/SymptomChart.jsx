import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const symptomColors = {
  fatigue: '#ef4444',
  mood: '#10b981',
  pain: '#f59e0b',
  nausea: '#8b5cf6',
  appetite: '#3b82f6',
  sleep_hours: '#06b6d4',
}

export default function SymptomChart({ data, selectedSymptoms = ['fatigue', 'mood', 'pain', 'nausea'] }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
        <div className="text-4xl mb-3">📊</div>
        <p className="text-gray-400 text-sm">No symptom data yet. Start logging to see trends.</p>
      </div>
    )
  }

  // Format dates for display
  const chartData = data.map(entry => ({
    ...entry,
    date: entry.date || new Date(entry.logged_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }))

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
      <h3 className="font-semibold text-gray-700 mb-4">Symptom Trends</h3>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} />
          <YAxis domain={[0, 10]} tick={{ fontSize: 11, fill: '#94a3b8' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255,255,255,0.95)',
              border: '1px solid #e2e8f0',
              borderRadius: '12px',
              boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
              fontSize: '12px'
            }}
          />
          <Legend wrapperStyle={{ fontSize: '12px' }} />
          {selectedSymptoms.map(symptom => (
            <Line
              key={symptom}
              type="monotone"
              dataKey={symptom}
              stroke={symptomColors[symptom] || '#6b7280'}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
