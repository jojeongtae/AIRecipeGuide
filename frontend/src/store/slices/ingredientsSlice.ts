import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface IngredientsState {
  selectedIngredients: string[]
}

const initialState: IngredientsState = {
  selectedIngredients: [],
}

const ingredientsSlice = createSlice({
  name: 'ingredients',
  initialState,
  reducers: {
    // 재료 추가
    addIngredient: (state, action: PayloadAction<string>) => {
      const ingredient = action.payload.trim()
      if (ingredient && !state.selectedIngredients.includes(ingredient)) {
        state.selectedIngredients.push(ingredient)
      }
    },
    // 재료 제거
    removeIngredient: (state, action: PayloadAction<string>) => {
      state.selectedIngredients = state.selectedIngredients.filter(
        (ing) => ing !== action.payload
      )
    },
    // 재료 목록 초기화
    clearIngredients: (state) => {
      state.selectedIngredients = []
    },
    // 재료 목록 설정 (배치 업데이트용)
    setIngredients: (state, action: PayloadAction<string[]>) => {
      state.selectedIngredients = action.payload
    },
  },
})

export const { addIngredient, removeIngredient, clearIngredients, setIngredients } =
  ingredientsSlice.actions

export default ingredientsSlice.reducer


