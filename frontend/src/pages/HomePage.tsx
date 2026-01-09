import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { recommendRecipe, getRecipeByMenu } from '../services/api'
import { useAppSelector } from '../store/hooks'
import IngredientInput from '../components/IngredientInput'
import IngredientCheckboxPanel from '../components/IngredientCheckboxPanel'
import PersonaSelector from '../components/PersonaSelector'

const HomePage = () => {
  const navigate = useNavigate()
  const selectedTags = useAppSelector((state) => state.ingredients.selectedIngredients)
  
  const [menuName, setMenuName] = useState('')
  const [loading, setLoading] = useState(false)
  const [menuLoading, setMenuLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [userPersona, setUserPersona] = useState<'beginner' | 'expert'>('beginner')

  // 초기화
  const handleReset = () => {
    setError(null)
  }

  // 재료 문자열 생성 (API 전송용)
  const getIngredientsString = () => {
    return selectedTags.join(', ')
  }

  // 재료가 있는지 확인
  const hasIngredients = selectedTags.length > 0

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!hasIngredients) return

    setLoading(true)
    setError(null)

    try {
      const response = await recommendRecipe({
        ingredients: getIngredientsString(),
        difficulty: null,
        max_cooking_time: null,
        dietary_preferences: null,
        category: null,
        user_persona: userPersona,
      })

      if (response.success && response.data) {
        // 레시피 결과 페이지로 이동 (state로 데이터 전달)
        // setTimeout을 사용하여 React 상태 업데이트 후 라우팅 실행
        const data = response.data
        setLoading(false) // 로딩 상태 해제
        setTimeout(() => {
          navigate('/recipes', { 
            state: { 
              recipes: data.recipes || [],
              searchSource: data.search_source_label || data.search_source || null,
              userPersona: userPersona
            } 
          })
        }, 100) // 100ms 지연으로 React 상태 업데이트 완료 대기
      } else {
        setError(response.error || '레시피를 찾을 수 없습니다.')
        setLoading(false)
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '오류가 발생했습니다.'
      setError(errorMessage)
      setLoading(false)
    }
  }


  // 메뉴 이름으로 레시피 검색
  const handleMenuSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!menuName.trim() || !hasIngredients) return

    setMenuLoading(true)
    setError(null)

    try {
      const response = await getRecipeByMenu(menuName.trim(), getIngredientsString())

      if (response.success && response.data) {
        // 레시피 목록 페이지로 이동 (여러 레시피 선택 가능)
        // setTimeout을 사용하여 React 상태 업데이트 후 라우팅 실행
        const data = response.data
        setMenuLoading(false) // 로딩 상태 해제
        setTimeout(() => {
          navigate('/recipes', {
            state: {
              recipes: data.recipes || [],
              menuName: menuName.trim()  // 메뉴 이름도 함께 전달
            }
          })
        }, 100) // 100ms 지연으로 React 상태 업데이트 완료 대기
      } else {
        setError(response.error || '레시피를 찾을 수 없습니다.')
        setMenuLoading(false)
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '오류가 발생했습니다.'
      setError(errorMessage)
      setMenuLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* 제목 섹션 */}
      <div className="text-center mb-12 animate-fade-in">
        <h2 className="text-4xl font-bold bg-gradient-to-r from-orange-600 to-pink-600 bg-clip-text text-transparent mb-4">
          레시피 찾기
        </h2>
        <p className="text-gray-600 text-lg">
          메뉴 이름이나 재료를 입력하면 레시피를 찾아드립니다
        </p>
      </div>

      {/* 메뉴 이름 검색 섹션 */}
      <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 animate-fade-in border border-gray-100">
        <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <span className="text-2xl">🔍</span>
          메뉴 이름으로 검색
        </h3>
        <form onSubmit={handleMenuSearch} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              메뉴 이름 (예: 파스타, 김치찌개, 된장찌개)
            </label>
            <input
              type="text"
              value={menuName}
              onChange={(e) => setMenuName(e.target.value)}
              placeholder="메뉴 이름을 입력하세요"
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-orange-400 focus:ring-2 focus:ring-orange-200 outline-none text-gray-700"
            />
          </div>
          <p className="text-sm text-gray-500">
            💡 보유 재료를 먼저 입력한 후 메뉴 이름을 검색하면 부족한 재료를 알려드립니다
          </p>
          <button
            type="submit"
            disabled={menuLoading || !menuName.trim() || !hasIngredients}
            className="w-full bg-gradient-to-r from-blue-500 to-indigo-500 text-white py-3 px-6 rounded-xl hover:from-blue-600 hover:to-indigo-600 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg font-semibold text-lg"
          >
            {menuLoading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin">⏳</span>
                검색 중...
              </span>
            ) : (
              '메뉴 검색하기 🔍'
            )}
          </button>
        </form>
      </div>

      {/* 구분선 */}
      <div className="flex items-center my-8">
        <div className="flex-1 border-t border-gray-300"></div>
        <span className="px-4 text-gray-500 font-medium">또는</span>
        <div className="flex-1 border-t border-gray-300"></div>
      </div>

      {/* 재료 기반 검색 섹션 */}
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-gray-800 mb-2 flex items-center justify-center gap-2">
          <span className="text-2xl">🥬</span>
          재료로 레시피 추천받기
        </h3>
        <p className="text-gray-600">
          보유한 재료를 입력하면 맞는 레시피를 추천해드립니다
        </p>
      </div>

      {/* 재료 입력 폼 */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl p-8 mb-8 animate-fade-in border border-gray-100">
        {/* 재료 입력 영역 */}
        <IngredientInput onReset={handleReset} />
        <IngredientCheckboxPanel />

        {/* 페르소나 선택 */}
        <PersonaSelector value={userPersona} onChange={setUserPersona} />

        {error && (
          <div className="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-200 text-red-700 px-5 py-4 rounded-xl mb-6 shadow-md animate-slide-in flex items-center gap-2">
            <span className="text-xl">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !hasIngredients}
          className="w-full bg-gradient-to-r from-orange-500 to-pink-500 text-white py-4 px-6 rounded-xl hover:from-orange-600 hover:to-pink-600 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg font-semibold text-lg"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⏳</span>
              레시피 검색 중...
            </span>
          ) : (
            '레시피 찾기 ✨'
          )}
        </button>
      </form>
    </div>
  )
}

export default HomePage


