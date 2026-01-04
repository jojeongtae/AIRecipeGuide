import { useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { selectRecipe } from '../services/api'

const RecipeResultsPage = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { recipes = [], searchSource = null, menuName = null } = (location.state as any) || {}
  
  const [loading, setLoading] = useState(false)
  const [loadingStage, setLoadingStage] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  const handleSelectRecipe = async (index: number) => {
    if (!recipes[index]) return

    // 메뉴 이름 기반 검색 결과인 경우 레시피 정보를 직접 전달
    if (menuName) {
      const selectedRecipe = recipes[index]
      // 레시피 상세 페이지 형식으로 변환
      navigate('/recipe', { 
        state: { 
          recipeData: {
            recipe: selectedRecipe
          },
          searchSource: searchSource
        } 
      })
      return
    }

    // 재료 기반 검색 결과인 경우 기존 로직 사용
    setLoading(true)
    setError(null)
    setLoadingStage('레시피 검색 중...')

    // 단계별 로딩 메시지
    const stageTimer = setTimeout(() => {
      setLoadingStage('요리 순서 정렬 중...')
    }, 3000)

    const stageTimer2 = setTimeout(() => {
      setLoadingStage('대체재료 생각 중...')
    }, 6000)

    try {
      const selectedRecipe = recipes[index]
      const ingredientsString = selectedRecipe.ingredients?.join(', ') || ''
      const response = await selectRecipe(
        index,
        ingredientsString,
        2
      )

      clearTimeout(stageTimer)
      clearTimeout(stageTimer2)

      if (response.success && response.data) {
        // 레시피 상세 페이지로 이동
        navigate('/recipe', { 
          state: { 
            recipeData: response.data,
            searchSource: searchSource
          } 
        })
      } else {
        setError(response.error || '레시피를 불러올 수 없습니다.')
        setLoadingStage('')
      }
    } catch (err: any) {
      clearTimeout(stageTimer)
      clearTimeout(stageTimer2)
      setError(err.message || '오류가 발생했습니다.')
      setLoadingStage('')
    } finally {
      setLoading(false)
    }
  }

  if (recipes.length === 0) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="text-6xl mb-4">🔍</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">레시피를 찾을 수 없습니다</h2>
          <p className="text-gray-600 mb-6">다른 재료로 다시 검색해보세요.</p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-gradient-to-r from-orange-500 to-pink-500 text-white rounded-xl hover:from-orange-600 hover:to-pink-600 transition-all font-semibold"
          >
            다시 검색하기
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-4xl font-bold bg-gradient-to-r from-orange-600 to-pink-600 bg-clip-text text-transparent flex items-center gap-3 mb-2">
            <span className="text-4xl">🍽️</span>
            {menuName ? `"${menuName}" 검색 결과` : '추천 레시피'} ({recipes.length}개)
          </h2>
          {menuName && (
            <p className="text-gray-600 text-sm mt-1">
              검색어: <span className="font-medium">{menuName}</span>
            </p>
          )}
          {searchSource && (
            <p className="text-gray-600 text-sm mt-1">
              출처: <span className="font-medium">{searchSource}</span>
            </p>
          )}
        </div>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 text-gray-700 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors font-medium"
        >
          ← 다시 검색
        </button>
      </div>

      {error && (
        <div className="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-200 text-red-700 px-5 py-4 rounded-xl mb-6 shadow-md animate-slide-in flex items-center gap-2">
          <span className="text-xl">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {loading && loadingStage && (
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 animate-fade-in border border-gray-100">
          <div className="flex items-center justify-center gap-3 py-8">
            <span className="animate-spin text-3xl">⏳</span>
            <span className="text-xl font-semibold text-gray-700">{loadingStage}</span>
          </div>
        </div>
      )}

      {/* 레시피 리스트 */}
      <div className="space-y-4">
        {recipes.map((recipe: any, index: number) => (
          <div
            key={recipe.id || index}
            className="bg-white border-2 border-gray-200 rounded-xl p-5 hover:border-orange-300 hover:shadow-lg cursor-pointer transition-all transform hover:scale-[1.02] animate-slide-in"
            style={{ animationDelay: `${index * 0.1}s` }}
            onClick={() => handleSelectRecipe(index)}
          >
            <div className="flex gap-4">
              {/* 레시피 이미지 */}
              <div className="flex-shrink-0 w-32 h-32 rounded-lg overflow-hidden bg-gray-200">
                {recipe.image ? (
                  <img
                    src={recipe.image}
                    alt={recipe.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement
                      target.style.display = 'none'
                      if (target.parentElement) {
                        target.parentElement.innerHTML = '<div class="w-full h-full flex items-center justify-center text-4xl">🍽️</div>'
                      }
                    }}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-orange-100 to-pink-100">
                    🍽️
                  </div>
                )}
              </div>
              
              {/* 레시피 정보 */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <span className="text-2xl">👨‍🍳</span>
                    {recipe.name}
                  </h3>
                  {recipe.category && (
                    <span className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-xs font-medium">
                      {recipe.category}
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-3 text-sm mb-3">
                  <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-medium">
                    난이도: {recipe.level || recipe.difficulty || 'N/A'}
                  </span>
                  <span className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full font-medium">
                    ⏱️ {recipe.cooking_time}분
                  </span>
                  {(recipe.match_score || recipe.match_rate !== undefined) && (
                    <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium">
                      매칭도: {(() => {
                        const rate = recipe.match_rate ?? recipe.match_score ?? 0;
                        // match_rate가 1보다 크면 이미 퍼센트 값이므로 그대로 사용, 아니면 100 곱함
                        return Math.round(rate > 1 ? rate : rate * 100);
                      })()}%
                    </span>
                  )}
                </div>
                {recipe.missing_ingredients && recipe.missing_ingredients.length > 0 && (
                  <div className="text-sm text-orange-700 bg-orange-50 px-3 py-2 rounded-lg">
                    📋 추가 필요: <span className="font-semibold">
                      {recipe.missing_ingredients
                        .map((ing: string) => ing.replace(/\s*\d+[\/\.]?\d*\s*[가-힣a-zA-Z]*\s*$/, '').trim())
                        .filter((ing: string) => ing.length > 0)
                        .join(', ')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default RecipeResultsPage

