import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { recommendRecipe, getRecipeByMenu } from '../services/api'
import ingredientsData from '../data/ingredients.json'
import { useAppSelector, useAppDispatch } from '../store/hooks'
import { addIngredient, removeIngredient, clearIngredients } from '../store/slices/ingredientsSlice'

const HomePage = () => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const selectedTags = useAppSelector((state) => state.ingredients.selectedIngredients)
  
  const [inputValue, setInputValue] = useState('')
  const [menuName, setMenuName] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [showCheckboxPanel, setShowCheckboxPanel] = useState(false)
  const [loading, setLoading] = useState(false)
  const [menuLoading, setMenuLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [userPersona, setUserPersona] = useState<'beginner' | 'expert'>('beginner')
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
      if (suggestions.length > 0) {
        addTag(suggestions[0])
      } else {
        addTag(inputValue.trim())
      }
    } else if (e.key === 'Backspace' && !inputValue && selectedTags.length > 0) {
      removeTag(selectedTags[selectedTags.length - 1])
    }
  }

  // 초기화
  const handleReset = () => {
    dispatch(clearIngredients())
    setInputValue('')
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
        navigate('/recipes', { 
          state: { 
            recipes: response.data.recipes || [],
            searchSource: response.data.search_source_label || response.data.search_source || null,
            userPersona: userPersona
          } 
        })
      } else {
        setError(response.error || '레시피를 찾을 수 없습니다.')
      }
    } catch (err: any) {
      setError(err.message || '오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  // 체크박스 토글
  const handleCheckboxToggle = (item: string) => {
    if (selectedTags.includes(item)) {
      removeTag(item)
    } else {
      addTag(item)
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
        navigate('/recipes', {
          state: {
            recipes: response.data.recipes || [],
            menuName: menuName.trim()  // 메뉴 이름도 함께 전달
          }
        })
      } else {
        setError(response.error || '레시피를 찾을 수 없습니다.')
      }
    } catch (err: any) {
      setError(err.message || '오류가 발생했습니다.')
    } finally {
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
                        ? 'bg-purple-100 text-purple-700 border border-purple-200' 
                        : 'bg-orange-100 text-orange-700 border border-orange-200'
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

        {/* 페르소나 선택 */}
        <div className="mb-6">
          <label className="block text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span className="text-2xl">👤</span>
            나의 요리 실력
          </label>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setUserPersona('beginner')}
              className={`p-4 rounded-xl border-2 transition-all ${
                userPersona === 'beginner'
                  ? 'border-orange-500 bg-orange-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-orange-200 hover:bg-orange-50'
              }`}
            >
              <div className="flex flex-col items-center gap-2">
                <span className="text-3xl">🌱</span>
                <span className={`font-semibold ${userPersona === 'beginner' ? 'text-orange-700' : 'text-gray-700'}`}>
                  초보자
                </span>
                <span className={`text-xs text-center ${userPersona === 'beginner' ? 'text-orange-600' : 'text-gray-500'}`}>
                  용어 설명, 단계별 가이드
                </span>
              </div>
            </button>
            <button
              type="button"
              onClick={() => setUserPersona('expert')}
              className={`p-4 rounded-xl border-2 transition-all ${
                userPersona === 'expert'
                  ? 'border-purple-500 bg-purple-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-purple-200 hover:bg-purple-50'
              }`}
            >
              <div className="flex flex-col items-center gap-2">
                <span className="text-3xl">🔥</span>
                <span className={`font-semibold ${userPersona === 'expert' ? 'text-purple-700' : 'text-gray-700'}`}>
                  숙련가
                </span>
                <span className={`text-xs text-center ${userPersona === 'expert' ? 'text-purple-600' : 'text-gray-500'}`}>
                  효율적 조리법, 고급 기법
                </span>
              </div>
            </button>
          </div>
        </div>

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


