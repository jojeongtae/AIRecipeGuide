
interface PersonaSelectorProps {
  value: 'beginner' | 'expert'
  onChange: (persona: 'beginner' | 'expert') => void
  variant?: 'default' | 'compact'
}

const PersonaSelector = ({ value, onChange, variant = 'default' }: PersonaSelectorProps) => {
  if (variant === 'compact') {
    return (
      <div className="mb-4 flex items-center justify-center gap-4">
        <div className="flex items-center gap-2 bg-white rounded-xl p-2 border-2 border-gray-200 shadow-sm">
          <button
            type="button"
            onClick={() => onChange('beginner')}
            className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${
              value === 'beginner'
                ? 'bg-orange-100 border-2 border-orange-400 shadow-md'
                : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
            }`}
          >
            <span className="text-2xl">🌱</span>
            <div className="flex flex-col items-start">
              <span className={`font-semibold ${value === 'beginner' ? 'text-orange-700' : 'text-gray-700'}`}>
                초보자
              </span>
              <span className={`text-xs text-center ${value === 'beginner' ? 'text-orange-600' : 'text-gray-500'}`}>
                상세 설명
              </span>
            </div>
          </button>
          <button
            type="button"
            onClick={() => onChange('expert')}
            className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${
              value === 'expert'
                ? 'bg-purple-100 border-2 border-purple-400 shadow-md'
                : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
            }`}
          >
            <span className="text-2xl">🔥</span>
            <div className="flex flex-col items-start">
              <span className={`font-semibold ${value === 'expert' ? 'text-purple-700' : 'text-gray-700'}`}>
                숙련가
              </span>
              <span className={`text-xs text-center ${value === 'expert' ? 'text-purple-600' : 'text-gray-500'}`}>
                간단 요약
              </span>
            </div>
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="mb-6">
      <label className="block text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
        <span className="text-2xl">👤</span>
        나의 요리 실력
      </label>
      <div className="grid grid-cols-2 gap-4">
        <button
          type="button"
          onClick={() => onChange('beginner')}
          className={`p-4 rounded-xl border-2 transition-all ${
            value === 'beginner'
              ? 'border-orange-500 bg-orange-50 shadow-md'
              : 'border-gray-200 bg-white hover:border-orange-200 hover:bg-orange-50'
          }`}
        >
          <div className="flex flex-col items-center gap-2">
            <span className="text-3xl">🌱</span>
            <span className={`font-semibold ${value === 'beginner' ? 'text-orange-700' : 'text-gray-700'}`}>
              초보자
            </span>
            <span className={`text-xs text-center ${value === 'beginner' ? 'text-orange-600' : 'text-gray-500'}`}>
              용어 설명, 단계별 가이드
            </span>
          </div>
        </button>
        <button
          type="button"
          onClick={() => onChange('expert')}
          className={`p-4 rounded-xl border-2 transition-all ${
            value === 'expert'
              ? 'border-purple-500 bg-purple-50 shadow-md'
              : 'border-gray-200 bg-white hover:border-purple-200 hover:bg-purple-50'
          }`}
        >
          <div className="flex flex-col items-center gap-2">
            <span className="text-3xl">🔥</span>
            <span className={`font-semibold ${value === 'expert' ? 'text-purple-700' : 'text-gray-700'}`}>
              숙련가
            </span>
            <span className={`text-xs text-center ${value === 'expert' ? 'text-purple-600' : 'text-gray-500'}`}>
              효율적 조리법, 고급 기법
            </span>
          </div>
        </button>
      </div>
    </div>
  )
}

export default PersonaSelector

