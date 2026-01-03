import { useState, useEffect, useRef } from 'react'
import { recommendRecipe, selectRecipe } from '../services/api'
import type { RecipeResponse } from '../types/recipe'
import ingredientsData from '../data/ingredients.json'
import { useAppSelector, useAppDispatch } from '../store/hooks'
import { addIngredient, removeIngredient, clearIngredients } from '../store/slices/ingredientsSlice'

const RecipeRecommendation = () => {
  const dispatch = useAppDispatch()
  const selectedTags = useAppSelector((state) => state.ingredients.selectedIngredients)
  
  const [inputValue, setInputValue] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [showCheckboxPanel, setShowCheckboxPanel] = useState(false)
  const [loading, setLoading] = useState(false)
  const [loadingStage, setLoadingStage] = useState<string>('')
  const [result, setResult] = useState<RecipeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [recipeOptions, setRecipeOptions] = useState<any[]>([])
  const [searchSource, setSearchSource] = useState<string | null>(null)
  const [servingSize, setServingSize] = useState<number>(2)
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // 전체 재료 목록 생성
  const allIngredients = [
    ...ingredientsData.baseIngredients.flatMap(cat => cat.items),
    ...ingredientsData.sauces.flatMap(cat => cat.items)
  ]

  // 자동완성 필터링
  useEffect(() => {
    if (inputValue.trim()) {
      const filtered = allIngredients.filter(item =>
        item.includes(inputValue.trim()) && !selectedTags.includes(item)
      ).slice(0, 8)
      setSuggestions(filtered)
      setShowSuggestions(filtered.length > 0)
    } else {
      setSuggestions([])
      setShowSuggestions(false)
    }
  }, [inputValue, selectedTags])

  // 외부 클릭 시 자동완성 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // 태그 추가
  const addTag = (tag: string) => {
    if (tag.trim() && !selectedTags.includes(tag.trim())) {
      dispatch(addIngredient(tag.trim()))
      setInputValue('')
      setShowSuggestions(false)
    }
  }

  // 태그 제거
  const removeTag = (tag: string) => {
    dispatch(removeIngredient(tag))
  }

  // 입력 필드 처리
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value)
  }

  // Enter 키 처리
  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault()
      // 자동완성 첫 번째 항목이 있으면 추가, 없으면 입력값 그대로 추가
      if (suggestions.length > 0) {
        addTag(suggestions[0])
      } else {
        addTag(inputValue.trim())
      }
    } else if (e.key === 'Backspace' && !inputValue && selectedTags.length > 0) {
      // 백스페이스로 마지막 태그 제거
      removeTag(selectedTags[selectedTags.length - 1])
    }
  }

  // 초기화
  const handleReset = () => {
    dispatch(clearIngredients())
    setInputValue('')
    setResult(null)
    setRecipeOptions([])
    setError(null)
    setSearchSource(null)
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
    setResult(null)
    setRecipeOptions([])

    try {
      const response = await recommendRecipe({
        ingredients: getIngredientsString(),
        difficulty: null,
        max_cooking_time: null,
        dietary_preferences: null,
        category: null,
      })

      if (response.success && response.data) {
        setSearchSource(response.data.search_source_label || response.data.search_source || null)
        // recipes 배열이 있으면 리스트로 표시
        if (response.data.recipes && Array.isArray(response.data.recipes) && response.data.recipes.length > 0) {
          setRecipeOptions(response.data.recipes)
        } else {
          setError(response.error || '레시피를 찾을 수 없습니다.')
        }
      } else {
        setError(response.error || '레시피를 찾을 수 없습니다.')
      }
    } catch (err: any) {
      setError(err.message || '오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectRecipe = async (index: number) => {
    setLoading(true)
    setError(null)
    setLoadingStage('레시피 검색 중...')

    // 단계별 로딩 메시지 표시를 위한 타이머
    const stageTimer = setTimeout(() => {
      setLoadingStage('요리 순서 정렬 중...')
    }, 3000) // 3초 후

    const substitutionTimer = setTimeout(() => {
      setLoadingStage('대체재료 생각 중...')
    }, 6000) // 6초 후

    try {
      const response = await selectRecipe(index, getIngredientsString(), servingSize)
      
      // 타이머 정리
      clearTimeout(stageTimer)
      clearTimeout(substitutionTimer)
      
      if (response.success && response.data) {
        setResult(response.data)
        setRecipeOptions([])
        setLoadingStage('')
        // 레시피의 기본 인분 수로 servingSize 업데이트
        if (response.data.recipe?.serving_size) {
          setServingSize(response.data.recipe.serving_size)
        }
      } else {
        setError(response.error || '레시피를 불러올 수 없습니다.')
        setLoadingStage('')
      }
    } catch (err: any) {
      clearTimeout(stageTimer)
      clearTimeout(substitutionTimer)
      setError(err.message || '오류가 발생했습니다.')
      setLoadingStage('')
    } finally {
      setLoading(false)
    }
  }

  const handleServingSizeChange = async (newSize: number) => {
    if (newSize < 1 || newSize > 20) return
    setServingSize(newSize)
    
    // 레시피가 선택된 상태에서 인분 수 변경 시 재요청
    if (result?.recipe && recipeOptions.length === 0) {
      // 현재 선택된 레시피의 인덱스를 찾아서 다시 요청
      // 이 경우는 이미 상세 화면이므로, serving_size만 업데이트하여 재요청
      setLoading(true)
      setLoadingStage('인분 수 조정 중...')
      try {
        // 원래 선택했던 레시피 인덱스를 찾기 어려우므로, 
        // 현재 result의 recipe 정보를 기반으로 serving_size만 업데이트
        // recipes가 없으면 전체 검색이 실행되지만, 이미 상세 화면이므로 0번 인덱스 사용
        const response = await selectRecipe(0, getIngredientsString(), newSize)
        if (response.success && response.data) {
          setResult(response.data)
        }
      } catch (err: any) {
        setError(err.message || '인분 수 조정 중 오류가 발생했습니다.')
      } finally {
        setLoading(false)
        setLoadingStage('')
      }
    }
  }

  // 체크박스에서 재료 선택
  const handleCheckboxToggle = (item: string) => {
    if (selectedTags.includes(item)) {
      removeTag(item)
    } else {
      addTag(item)
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl p-8 mb-8 animate-fade-in border border-gray-100">
        {/* 재료 입력 영역 */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <label className="block text-lg font-bold text-gray-800 flex items-center gap-2">
              <span className="text-2xl">🥬</span>
              재료를 입력하세요
            </label>
            {hasIngredients && (
              <button
                type="button"
                onClick={handleReset}
                className="text-sm text-gray-600 hover:text-gray-800 px-3 py-1 rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-1"
              >
                <span>🔄</span>
                초기화
              </button>
            )}
          </div>

          {/* 태그 입력 필드 */}
          <div className="relative mb-4">
            <div className="flex flex-wrap gap-2 p-3 min-h-[60px] border-2 border-gray-200 rounded-xl focus-within:border-orange-400 focus-within:ring-2 focus-within:ring-orange-200 transition-all bg-white">
              {selectedTags.map((tag: string) => {
                const isSauce = ingredientsData.sauces.some(cat => cat.items.includes(tag))
                return (
                  <span
                    key={tag}
                    className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium ${
                      isSauce 
                        ? 'bg-purple-100 text-purple-700' 
                        : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => removeTag(tag)}
                      className="hover:opacity-70 focus:outline-none text-lg leading-none"
                    >
                      ×
                    </button>
                  </span>
                )
              })}
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleInputKeyDown}
                onFocus={() => inputValue.trim() && setShowSuggestions(true)}
                placeholder={selectedTags.length === 0 ? "재료를 입력하세요 (Enter로 추가)" : ""}
                className="flex-1 min-w-[200px] outline-none text-gray-700 placeholder-gray-400"
              />
            </div>

            {/* 자동완성 드롭다운 */}
            {showSuggestions && suggestions.length > 0 && (
              <div
                ref={suggestionsRef}
                className="absolute z-10 w-full mt-1 bg-white border-2 border-gray-200 rounded-xl shadow-lg max-h-60 overflow-y-auto"
              >
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => addTag(suggestion)}
                    className="w-full text-left px-4 py-2 hover:bg-orange-50 transition-colors flex items-center gap-2"
                  >
                    <span className="text-orange-500">+</span>
                    <span className="text-gray-700">{suggestion}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 재료 목록에서 선택 버튼 */}
          <div className="mb-4">
            <button
              type="button"
              onClick={() => setShowCheckboxPanel(!showCheckboxPanel)}
              className="text-sm text-gray-600 hover:text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-2"
            >
              <span>{showCheckboxPanel ? '▼' : '▶'}</span>
              재료 목록에서 선택
            </button>
          </div>

          {/* 접을 수 있는 체크박스 패널 */}
          {showCheckboxPanel && (
            <div className="grid md:grid-cols-2 gap-6 mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200">
              {/* 좌측: 일반 재료 */}
              <div>
                <h3 className="text-md font-bold text-gray-800 mb-3 flex items-center gap-2">
                  <span className="text-lg">🥘</span>
                  일반 재료
                </h3>
                <div className="max-h-64 overflow-y-auto space-y-3">
                  {ingredientsData.baseIngredients.map((category) => (
                    <div key={category.category} className="mb-3">
                      <h4 className="text-xs font-semibold text-gray-600 mb-2">
                        {category.category}
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {category.items.map((item) => (
                          <label
                            key={item}
                            className="flex items-center gap-1.5 cursor-pointer hover:bg-white px-2 py-1 rounded transition-colors"
                          >
                            <input
                              type="checkbox"
                              checked={selectedTags.includes(item)}
                              onChange={() => handleCheckboxToggle(item)}
                              className="w-3.5 h-3.5 text-orange-500 border-gray-300 rounded focus:ring-orange-400"
                            />
                            <span className="text-xs text-gray-700">{item}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 우측: 소스/양념 */}
              <div>
                <h3 className="text-md font-bold text-gray-800 mb-3 flex items-center gap-2">
                  <span className="text-lg">🧂</span>
                  소스/양념
                </h3>
                <div className="max-h-64 overflow-y-auto space-y-3">
                  {ingredientsData.sauces.map((category) => (
                    <div key={category.category} className="mb-3">
                      <h4 className="text-xs font-semibold text-gray-600 mb-2">
                        {category.category}
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {category.items.map((item) => (
                          <label
                            key={item}
                            className="flex items-center gap-1.5 cursor-pointer hover:bg-white px-2 py-1 rounded transition-colors"
                          >
                            <input
                              type="checkbox"
                              checked={selectedTags.includes(item)}
                              onChange={() => handleCheckboxToggle(item)}
                              className="w-3.5 h-3.5 text-purple-500 border-gray-300 rounded focus:ring-purple-400"
                            />
                            <span className="text-xs text-gray-700">{item}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={loading || !hasIngredients}
          className="w-full bg-gradient-to-r from-orange-500 to-pink-500 text-white py-3 px-6 rounded-xl hover:from-orange-600 hover:to-pink-600 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg font-semibold text-lg"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⏳</span>
              검색 중...
            </span>
          ) : (
            '레시피 추천받기 ✨'
          )}
        </button>
      </form>

      {error && (
        <div className="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-200 text-red-700 px-5 py-4 rounded-xl mb-6 shadow-md animate-slide-in flex items-center gap-2">
          <span className="text-xl">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {recipeOptions.length > 0 && (
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 animate-fade-in border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-pink-600 bg-clip-text text-transparent flex items-center gap-2">
              <span className="text-3xl">🍽️</span>
              추천 레시피 ({recipeOptions.length}개)
            </h2>
            {searchSource && (
              <span className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full font-medium">
                {searchSource}
              </span>
            )}
          </div>
          <div className="space-y-4">
            {recipeOptions.map((recipe, index) => (
              <div
                key={recipe.id || index}
                className="border-2 border-gray-200 rounded-xl p-5 hover:border-orange-300 hover:shadow-lg cursor-pointer transition-all transform hover:scale-[1.02] bg-gradient-to-br from-white to-gray-50 animate-slide-in overflow-hidden"
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
                          // 이미지 로드 실패 시 플레이스홀더 표시
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
                      {(recipe as any).category && (
                        <span className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-xs font-medium">
                          {(recipe as any).category}
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
                      <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium">
                        매칭도: {Math.round(recipe.match_score || 0)}%
                      </span>
                    </div>
                    {recipe.missing_ingredients && recipe.missing_ingredients.length > 0 && (
                      <div className="text-sm text-orange-700 bg-orange-50 px-3 py-2 rounded-lg mb-2">
                        📋 추가 필요: <span className="font-semibold">
                          {recipe.missing_ingredients
                            .map((ing: string) => {
                              // 수량 정보 제거 (예: "양파 1/4개" → "양파")
                              return ing.replace(/\s*\d+[\/\.]?\d*\s*[가-힣a-zA-Z]*\s*$/, '').trim()
                            })
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
      )}

      {loading && loadingStage && (
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 animate-fade-in border border-gray-100">
          <div className="flex items-center justify-center gap-3 py-8">
            <span className="animate-spin text-3xl">⏳</span>
            <span className="text-xl font-semibold text-gray-700">{loadingStage}</span>
          </div>
        </div>
      )}

      {result && (
        <div className="bg-white rounded-2xl shadow-xl p-8 animate-fade-in border border-gray-100">
          {result.recipe && (
            <>
              <div className="mb-6 pb-6 border-b-2 border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <h2 className="text-4xl font-bold bg-gradient-to-r from-orange-600 to-pink-600 bg-clip-text text-transparent flex items-center gap-3">
                      <span className="text-4xl">🍲</span>
                      {result.recipe.name}
                    </h2>
                    {(result.recipe as any).category && (
                      <span className="bg-indigo-100 text-indigo-700 px-4 py-2 rounded-full text-sm font-medium">
                        {(result.recipe as any).category}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {/* 인분 수 조정 */}
                    <div className="flex items-center gap-2 bg-orange-50 px-3 py-2 rounded-lg border border-orange-200">
                      <span className="text-sm font-medium text-gray-700">인분:</span>
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => handleServingSizeChange(servingSize - 1)}
                          disabled={servingSize <= 1}
                          className="w-7 h-7 rounded-full bg-white border border-orange-300 text-orange-600 font-bold hover:bg-orange-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          −
                        </button>
                        <span className="w-10 text-center font-semibold text-gray-800">{servingSize}</span>
                        <button
                          type="button"
                          onClick={() => handleServingSizeChange(servingSize + 1)}
                          disabled={servingSize >= 20}
                          className="w-7 h-7 rounded-full bg-white border border-orange-300 text-orange-600 font-bold hover:bg-orange-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          +
                        </button>
                      </div>
                    </div>
                    {searchSource && (
                      <span className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full font-medium">
                        {searchSource}
                      </span>
                    )}
                  </div>
                </div>
                {/* 레시피 대표 이미지 */}
                {(result.recipe as any).image && (
                  <div className="w-full h-64 rounded-xl overflow-hidden bg-gray-200 mb-4">
                    <img
                      src={(result.recipe as any).image}
                      alt={result.recipe.name}
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
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-5 border-2 border-blue-100">
                  <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <span className="text-2xl">🥘</span>
                    필요한 재료
                  </h3>
                  <div className="space-y-4">
                    {(result as any).matched_ingredients && (result as any).matched_ingredients.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-2">
                          <span>✅</span> 보유 재료
                        </h4>
                        <ul className="space-y-2">
                          {(result as any).matched_ingredients.map((ing: string, idx: number) => (
                            <li key={idx} className="flex items-center gap-2 text-gray-700 bg-green-50 px-3 py-2 rounded-lg shadow-sm border border-green-200">
                              <span className="text-green-600">✓</span>
                              <span>{ing}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {(result as any).missing_ingredients && (result as any).missing_ingredients.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-orange-700 mb-2 flex items-center gap-2">
                          <span>📋</span> 추가 필요
                        </h4>
                        <ul className="space-y-2">
                          {(result as any).missing_ingredients.map((ing: string, idx: number) => (
                            <li key={idx} className="flex items-center gap-2 text-gray-700 bg-orange-50 px-3 py-2 rounded-lg shadow-sm border border-orange-200">
                              <span className="text-orange-500">•</span>
                              <span>{ing}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {(!(result as any).matched_ingredients && !(result as any).missing_ingredients) && (
                      <ul className="space-y-2">
                        {result.recipe.ingredients?.map((ing, idx) => (
                          <li key={idx} className="flex items-center gap-2 text-gray-700 bg-white px-3 py-2 rounded-lg shadow-sm">
                            <span className="text-orange-500">•</span>
                            <span>{ing}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>

                {result.nutrition && (
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-5 border-2 border-purple-100">
                    <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                      <span className="text-2xl">📊</span>
                      영양 정보
                    </h3>
                    <div className="space-y-3">
                      <div className="bg-white px-4 py-2 rounded-lg shadow-sm">
                        <span className="font-semibold text-orange-600">칼로리:</span> <span className="text-gray-700">{result.nutrition.calories}kcal</span>
                      </div>
                      <div className="bg-white px-4 py-2 rounded-lg shadow-sm">
                        <span className="font-semibold text-blue-600">탄수화물:</span> <span className="text-gray-700">{result.nutrition.carbohydrates}g</span>
                      </div>
                      <div className="bg-white px-4 py-2 rounded-lg shadow-sm">
                        <span className="font-semibold text-green-600">단백질:</span> <span className="text-gray-700">{result.nutrition.protein}g</span>
                      </div>
                      <div className="bg-white px-4 py-2 rounded-lg shadow-sm">
                        <span className="font-semibold text-pink-600">지방:</span> <span className="text-gray-700">{result.nutrition.fat}g</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {result.cooking_steps && (
                <div className="mb-8 bg-gradient-to-br from-yellow-50 to-orange-50 rounded-xl p-6 border-2 border-yellow-100">
                  <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <span className="text-2xl">👨‍🍳</span>
                    요리 순서
                  </h3>
                  <ol className="space-y-3">
                    {result.cooking_steps.map((step: any, idx: number) => (
                      <li key={idx} className="flex gap-3 bg-white px-4 py-3 rounded-lg shadow-sm">
                        <span className="flex-shrink-0 w-8 h-8 bg-gradient-to-r from-orange-500 to-pink-500 text-white rounded-full flex items-center justify-center font-bold">
                          {idx + 1}
                        </span>
                        <span className="text-gray-700 pt-0.5">{step.description || step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {result.shopping_list && result.shopping_list.length > 0 && (
                <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-200 rounded-xl p-6 shadow-md">
                  <h3 className="text-2xl font-bold text-yellow-800 mb-4 flex items-center gap-2">
                    <span className="text-2xl">🛒</span>
                    쇼핑 리스트
                  </h3>
                  <ul className="space-y-2">
                    {result.shopping_list.map((item: any, idx: number) => (
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

              {result.substitutions && result.substitutions.length > 0 && (
                <div className="mt-8 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 rounded-xl p-6 shadow-md">
                  <h3 className="text-2xl font-bold text-green-800 mb-4 flex items-center gap-2">
                    <span className="text-2xl">🔄</span>
                    대체 재료 제안
                  </h3>
                  <div className="space-y-4">
                    {result.substitutions.map((item, idx) => (
                      <div key={`${item.missing}-${idx}`} className="bg-white rounded-xl p-4 shadow-sm border border-green-100">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                            <span className="text-green-500">부족 재료</span>
                            <span>{item.missing}</span>
                          </div>
                        </div>
                        <ul className="space-y-3">
                          {item.suggestions.map((suggestion, sIdx) => (
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
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default RecipeRecommendation
