export default function DietCard({ day, meals }) {
  if (!meals) return null

  const mealTypes = [
    { key: 'breakfast', label: 'Breakfast', icon: '🌅' },
    { key: 'snack_am', label: 'Morning Snack', icon: '🍎' },
    { key: 'lunch', label: 'Lunch', icon: '☀️' },
    { key: 'snack_pm', label: 'Afternoon Snack', icon: '🥜' },
    { key: 'dinner', label: 'Dinner', icon: '🌙' },
  ]

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-300">
      <div className="bg-gradient-to-r from-teal-600 to-teal-500 px-5 py-3">
        <h3 className="text-white font-semibold capitalize">{day.replace('_', ' ')}</h3>
      </div>
      <div className="p-4 space-y-3">
        {mealTypes.map(({ key, label, icon }) => {
          const meal = meals[key]
          if (!meal) return null
          return (
            <div key={key} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl hover:bg-teal-50 transition-colors duration-200">
              <span className="text-lg">{icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-teal-600 uppercase tracking-wide">{label}</span>
                  {meal.calories && (
                    <span className="text-xs text-gray-400">{meal.calories} cal</span>
                  )}
                </div>
                <p className="text-sm text-gray-700 mt-0.5">{meal.meal || meal.name || JSON.stringify(meal)}</p>
                {meal.notes && (
                  <p className="text-xs text-gray-400 mt-1 italic">{meal.notes}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
