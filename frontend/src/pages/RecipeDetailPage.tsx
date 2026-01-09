import { useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import type { CookingStep, ShoppingListItem, RecipeResponse, SubstitutionSuggestion } from '../types/recipe'
// import { selectRecipe } from '../services/api' // 주석처리 (1인분 고정)

const RecipeDetailPage = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { recipeData, searchSource } = (location.state as { recipeData?: RecipeResponse; searchSource?: string }) || {}
  
  // const [servingSize, setServingSize] = useState<number>(2)
  const [loading] = useState(false)
  const [loadingStage] = useState<string>('')
  const [loadingProgress] = useState<number>(0)
  const [error] = useState<string | null>(null)
  const [recipe] = useState(recipeData?.data?.recipe || null)
  const [fullData] = useState<RecipeResponse['data'] | null>(recipeData?.data || null)

  useEffect(() => {
    if (!recipeData) {
      navigate('/')
    }
    // 디버깅: 대체재료 데이터 확인
    if (fullData) {
      console.log('fullData:', fullData)
      console.log('substitutions:', fullData.substitutions)
      console.log('missing_ingredients:', fullData.missing_ingredients)
    }
  }, [recipeData, navigate, fullData])

  // const handleServingSizeChange = async (newSize: number) => {
  //   if (newSize < 1 || newSize > 20 || newSize === servingSize) return

  //   setServingSize(newSize)
  //   setLoading(true)
  //   setLoadingStage('인분 수 조정 중...')
  //   setLoadingProgress(50)
  //   setError(null)

  //   try {
  //     const ingredientsString = recipe?.ingredients?.join(', ') || ''
  //     const response = await selectRecipe(
  //       0, // 이미 선택된 레시피이므로 인덱스는 중요하지 않음
  //       ingredientsString,
  //       newSize
  //     )

  //     if (response.success && response.data) {
  //       setLoadingProgress(100)
  //       setFullData(response.data)
  //       setRecipe(response.data.recipe)
  //     } else {
  //       setError(response.error || '인분 수 조정에 실패했습니다.')
  //       setLoadingProgress(0)
  //     }
  //   } catch (err: any) {
  //     setError(err.message || '오류가 발생했습니다.')
  //     setLoadingProgress(0)
  //   } finally {
  //     setLoading(false)
  //     setLoadingStage('')
  //   }
  // }

  if (!recipe) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">레시피를 불러올 수 없습니다</h2>
          <button
            onClick={() => navigate('/')}
            className="mt-4 px-6 py-3 bg-gradient-to-r from-orange-500 to-pink-500 text-white rounded-xl hover:from-orange-600 hover:to-pink-600 transition-all font-semibold"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <button
          onClick={() => navigate(-1)}
          className="px-4 py-2 text-gray-700 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors font-medium"
        >
          ← 뒤로가기
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
          <div className="flex flex-col items-center justify-center gap-4 py-6">
            <div className="flex items-center gap-3">
              <span className="animate-spin text-3xl">⏳</span>
              <span className="text-xl font-semibold text-gray-700">{loadingStage}</span>
            </div>
            {/* 진행률 게이지 바 */}
            <div className="w-full max-w-md">
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-orange-500 to-pink-500 h-3 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${loadingProgress}%` }}
                ></div>
              </div>
              <div className="text-center mt-2 text-sm text-gray-500">
                {loadingProgress}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 레시피 상세 */}
      <div className="bg-white rounded-2xl shadow-xl p-4 sm:p-6 md:p-8 animate-fade-in border border-gray-100">
        <div className="mb-4 sm:mb-6 pb-4 sm:pb-6 border-b-2 border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4 mb-4">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 flex-1">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold bg-gradient-to-r from-orange-600 to-pink-600 bg-clip-text text-transparent flex items-center gap-2 sm:gap-3 break-words">
                <span className="text-2xl sm:text-3xl md:text-4xl">🍲</span>
                <span>{recipe.name}</span>
              </h2>
              {recipe.category && (
                <span className="bg-indigo-100 text-indigo-700 px-3 sm:px-4 py-1 sm:py-2 rounded-full text-xs sm:text-sm font-medium self-start sm:self-auto">
                  {recipe.category}
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              {/* 인분 수 조정 - 주석처리 (1인분 고정) */}
              {/* <div className="flex items-center gap-2 bg-orange-50 px-3 py-2 rounded-lg border border-orange-200">
                <span className="text-sm font-medium text-gray-700">인분:</span>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => handleServingSizeChange(servingSize - 1)}
                    disabled={servingSize <= 1 || loading}
                    className="w-7 h-7 rounded-full bg-white border border-orange-300 text-orange-600 font-bold hover:bg-orange-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    −
                  </button>
                  <span className="w-10 text-center font-semibold text-gray-800">{servingSize}</span>
                  <button
                    type="button"
                    onClick={() => handleServingSizeChange(servingSize + 1)}
                    disabled={servingSize >= 20 || loading}
                    className="w-7 h-7 rounded-full bg-white border border-orange-300 text-orange-600 font-bold hover:bg-orange-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    +
                  </button>
                </div>
              </div> */}
              {searchSource && (
                <span className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full font-medium">
                  {searchSource}
                </span>
              )}
            </div>
          </div>
          
          {/* 레시피 대표 이미지 */}
          {recipe.image && (
            <div className="w-full h-48 sm:h-56 md:h-64 rounded-xl overflow-hidden bg-gray-200 mb-4">
              <img
                src={recipe.image}
                alt={recipe.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  const target = e.target as HTMLImageElement
                  target.style.display = 'none'
                  if (target.parentElement) {
                    target.parentElement.innerHTML = '<div class="w-full h-full flex items-center justify-center text-6xl bg-gradient-to-br from-orange-100 to-pink-100">🍽️</div>'
                  }
                }}
              />
            </div>
          )}
        </div>
        
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {/* 필요한 재료 */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-5 border-2 border-blue-100">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="text-2xl">🥘</span>
              필요한 재료
            </h3>
            <div className="space-y-4">
              {fullData?.matched_ingredients && fullData.matched_ingredients.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-2">
                    <span>✅</span> 보유 재료
                  </h4>
                  <ul className="space-y-2">
                    {fullData.matched_ingredients.map((ing: string, idx: number) => (
                      <li key={idx} className="flex items-center gap-2 text-gray-700 bg-green-50 px-3 py-2 rounded-lg shadow-sm border border-green-200">
                        <span className="text-green-600">✓</span>
                        <span>{ing}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {fullData?.missing_ingredients && fullData.missing_ingredients.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-orange-700 mb-2 flex items-center gap-2">
                    <span>📋</span> 추가 필요
                  </h4>
                  <ul className="space-y-2">
                    {fullData.missing_ingredients.map((ing: string, idx: number) => (
                      <li key={idx} className="flex items-center gap-2 text-gray-700 bg-orange-50 px-3 py-2 rounded-lg shadow-sm border border-orange-200">
                        <span className="text-orange-500">•</span>
                        <span>{ing}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {(!fullData?.matched_ingredients && !fullData?.missing_ingredients) && (
                <ul className="space-y-2">
                  {recipe.ingredients?.map((ing: string, idx: number) => (
                    <li key={idx} className="flex items-center gap-2 text-gray-700 bg-white px-3 py-2 rounded-lg shadow-sm">
                      <span className="text-orange-500">•</span>
                      <span>{ing}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* 영양 정보 */}
          {fullData?.nutrition && (
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-5 border-2 border-purple-100">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <span className="text-2xl">📊</span>
                영양 정보
              </h3>
              <div className="space-y-3">
                <div className="bg-white px-4 py-2 rounded-lg shadow-sm">
                  <span className="font-semibold text-orange-600">칼로리:</span> <span className="text-gray-700">{fullData.nutrition.calories}kcal</span>
                </div>
                <div className="bg-white px-4 py-2 rounded-lg shadow-sm">
                  <span className="font-semibold text-blue-600">탄수화물:</span> <span className="text-gray-700">{fullData.nutrition.carbohydrates}g</span>
                </div>
                <div className="bg-white px-4 py-2 rounded-lg shadow-sm">
                  <span className="font-semibold text-green-600">단백질:</span> <span className="text-gray-700">{fullData.nutrition.protein}g</span>
                </div>
                <div className="bg-white px-4 py-2 rounded-lg shadow-sm">
                  <span className="font-semibold text-pink-600">지방:</span> <span className="text-gray-700">{fullData.nutrition.fat}g</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 요리 순서 */}
        {(fullData?.cooking_steps || recipe?.steps) && (
          <div className="mb-6 sm:mb-8 bg-gradient-to-br from-yellow-50 to-orange-50 rounded-xl p-4 sm:p-6 border-2 border-yellow-100">
            <h3 className="text-xl sm:text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="text-2xl">👨‍🍳</span>
              요리 순서
            </h3>
            <ol className="space-y-3">
              {(fullData?.cooking_steps || recipe?.steps || []).map((step: CookingStep | string, idx: number) => {
                const stepDescription = typeof step === 'string' ? step : step.description || step.step?.toString() || ''
                return (
                  <li key={idx} className="flex gap-3 bg-white px-4 py-3 rounded-lg shadow-sm">
                    <span className="flex-shrink-0 w-8 h-8 bg-gradient-to-r from-orange-500 to-pink-500 text-white rounded-full flex items-center justify-center font-bold">
                      {idx + 1}
                    </span>
                    <span className="text-gray-700 pt-0.5">{stepDescription}</span>
                  </li>
                )
              })}
            </ol>
          </div>
        )}

        {/* 대체 재료 제안 */}
        {fullData?.substitutions && fullData.substitutions.length > 0 && (
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 rounded-xl p-6 shadow-md mb-8">
            <h3 className="text-2xl font-bold text-green-800 mb-4 flex items-center gap-2">
              <span className="text-2xl">🔄</span>
              대체 재료 제안
            </h3>
            <div className="space-y-4">
              {fullData.substitutions.map((item: SubstitutionSuggestion, idx: number) => (
                <div key={`${item.missing}-${idx}`} className="bg-white rounded-xl p-4 shadow-sm border border-green-100">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                      <span className="text-green-500">부족 재료</span>
                      <span>{item.missing}</span>
                    </div>
                  </div>
                  <ul className="space-y-3">
                    {item.suggestions.map((suggestion, sIdx: number) => (
                      <li key={`${suggestion.ingredient}-${sIdx}`} className="border border-green-100 rounded-lg p-3 bg-green-50/50">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-gray-800">{suggestion.ingredient}</span>
                          {typeof suggestion.confidence === 'number' && (
                            <span className="text-sm text-green-600">
                              신뢰도 {Math.round(suggestion.confidence * 100)}%
                            </span>
                          )}
                        </div>
                        {suggestion.reason && (
                          <p className="text-sm text-gray-600">{suggestion.reason}</p>
                        )}
                        {suggestion.source && (
                          <p className="text-xs text-gray-400 mt-1">
                            출처: {suggestion.source === 'rule' ? '규칙 기반' : 'LLM'}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 쇼핑 리스트 */}
        {fullData?.shopping_list && fullData.shopping_list.length > 0 && (
          <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-200 rounded-xl p-6 shadow-md">
            <h3 className="text-2xl font-bold text-yellow-800 mb-4 flex items-center gap-2">
              <span className="text-2xl">🛒</span>
              쇼핑 리스트
            </h3>
            <ul className="space-y-2">
              {fullData.shopping_list?.map((item: ShoppingListItem, idx: number) => (
                <li key={idx} className="bg-white px-4 py-2 rounded-lg shadow-sm text-yellow-800">
                  <span className="font-semibold">{item.display || item.ingredient}</span>
                  {item.quantity && (
                    <span className="text-yellow-700 ml-2 font-medium">{item.quantity}</span>
                  )}
                  <span className="text-yellow-600 ml-2">({item.category})</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

export default RecipeDetailPage

