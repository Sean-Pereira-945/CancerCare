import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function DietAdherenceChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-50/50 rounded-2xl border border-dashed border-gray-200 p-12 text-center">
        <div className="text-3xl mb-2">🍽️</div>
        <p className="text-sm text-gray-400">No diet adherence data available for this period</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 10, fill: '#94a3b8' }} 
            axisLine={false} 
            tickLine={false}
            tickFormatter={(str) => {
              // Parse 'YYYY-MM-DD' directly to avoid timezone shift
              const [year, month, day] = str.split('-').map(Number);
              const date = new Date(year, month - 1, day);
              return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
            }}
          />
          <YAxis 
            domain={[0, 100]} 
            tick={{ fontSize: 10, fill: '#94a3b8' }} 
            axisLine={false} 
            tickLine={false}
            tickFormatter={(val) => `${val}%`}
          />
          <Tooltip 
            cursor={{ fill: '#f8fafc' }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const str = payload[0].payload.date;
                const [year, month, day] = str.split('-').map(Number);
                const date = new Date(year, month - 1, day);
                return (
                  <div className="bg-white border border-gray-100 shadow-xl rounded-xl p-3">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">
                      {date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
                    </p>
                    <p className="text-lg font-bold text-emerald-600">{payload[0].value}% Adherence</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="rate" radius={[6, 6, 0, 0]} barSize={24}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.rate >= 80 ? '#10b981' : entry.rate >= 50 ? '#f59e0b' : '#ef4444'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
