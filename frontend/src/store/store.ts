import { configureStore } from '@reduxjs/toolkit'
import { persistStore, persistReducer } from 'redux-persist'
import storage from 'redux-persist/lib/storage' // localStorage 사용
import ingredientsReducer from './slices/ingredientsSlice'

// Persist 설정
const ingredientsPersistConfig = {
  key: 'ingredients',
  storage,
  whitelist: ['selectedIngredients'], // persist할 필드만 지정
}

// Persisted reducer 생성
const persistedIngredientsReducer = persistReducer(
  ingredientsPersistConfig,
  ingredientsReducer
)

// Store 설정
export const store = configureStore({
  reducer: {
    ingredients: persistedIngredientsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // redux-persist의 액션 타입은 무시
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
})

export const persistor = persistStore(store)

// TypeScript 타입 추론을 위한 타입 export
export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch


