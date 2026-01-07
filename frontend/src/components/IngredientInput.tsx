import { useState, useEffect, useRef } from 'react'
import ingredientsData from '../data/ingredients.json'
import { useAppSelector, useAppDispatch } from '../store/hooks'
import { addIngredient, removeIngredient, clearIngredients } from '../store/slices/ingredientsSlice'

interface IngredientInputProps {
  placeholder?: string
  showResetButton?: boolean
  onReset?: () => void
}

const IngredientInput = ({ 
  placeholder = "재료를 입력하세요 (Enter로 추가)",
  showResetButton = true,
  onReset
}: IngredientInputProps) => {
  const dispatch = useAppDispatch()
  const selectedTags = useAppSelector((state) => state.ingredients.selectedIngredients)
  
  const [inputValue, setInputValue] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // 전체 재료 목록 생성 (메모이제이션 필요시 useMemo 사용)
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
  }, [inputValue, selectedTags, allIngredients])

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

  const handleReset = () => {
    dispatch(clearIngredients())
    setInputValue('')
    if (onReset) {
      onReset()
    }
  }

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <label className="block text-lg font-bold text-gray-800 flex items-center gap-2">
          <span className="text-2xl">🥬</span>
          재료를 입력하세요
        </label>
        {showResetButton && selectedTags.length > 0 && (
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
            placeholder={selectedTags.length === 0 ? placeholder : ""}
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
    </div>
  )
}

export default IngredientInput

