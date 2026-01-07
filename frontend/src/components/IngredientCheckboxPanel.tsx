import { useState } from 'react'
import ingredientsData from '../data/ingredients.json'
import { useAppSelector, useAppDispatch } from '../store/hooks'
import { addIngredient, removeIngredient } from '../store/slices/ingredientsSlice'

const IngredientCheckboxPanel = () => {
  const dispatch = useAppDispatch()
  const selectedTags = useAppSelector((state) => state.ingredients.selectedIngredients)
  const [showCheckboxPanel, setShowCheckboxPanel] = useState(false)

  const handleCheckboxToggle = (item: string) => {
    if (selectedTags.includes(item)) {
      dispatch(removeIngredient(item))
    } else {
      dispatch(addIngredient(item))
    }
  }

  return (
    <>
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
    </>
  )
}

export default IngredientCheckboxPanel

