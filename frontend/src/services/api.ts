import axios from 'axios'
import type { Recipe, RecipeResponse } from '../types/recipe'

// 로컬 ?�경?��? 배포 ?�경?��? ?�동 감�?
const getApiBaseUrl = (): string => {
  // ?�경 변?��? 명시?�으�??�정?�어 ?�으�??�선 ?�용
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  
  // 개발 ?�경?�거??localhost??경우
  if (import.meta.env.DEV || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000'
  }
  
  // 배포 ?�경 (기본�?
  return 'https://airecipeguide-production.up.railway.app'
}

const API_BASE_URL = getApiBaseUrl()

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface RecipeRequest {
  ingredients: string
  difficulty?: string | null
  max_cooking_time?: number | null
  dietary_preferences?: string[] | null
  serving_size?: number | null
  category?: string | null
  user_persona?: string | null
}

// RecipeResponse??types/recipe.ts?�서 import

export const recommendRecipe = async (request: RecipeRequest): Promise<RecipeResponse> => {
  const response = await apiClient.post<RecipeResponse>('/api/v1/recipes/recommend', request)
  return response.data
}

export const selectRecipe = async (recipeIndex: number, ingredients: string, userPersona?: string, recipeId?: string, recipeName?: string, recipeData?: Recipe/*, servingSize?: number*/): Promise<RecipeResponse> => {
  const params = new URLSearchParams({
    recipe_index: recipeIndex.toString(),
    ingredients: ingredients
  })
  if (userPersona) {
    params.append('user_persona', userPersona)
  }
  if (recipeId) {
    params.append('recipe_id', recipeId)
  }
  if (recipeName) {
    params.append('recipe_name', recipeName)
  }
  if (recipeData) {
    params.append('recipe_data', JSON.stringify(recipeData))
  }
  // if (servingSize) {
  //   params.append('serving_size', servingSize.toString())
  // }
  const response = await apiClient.post<RecipeResponse>(
    `/api/v1/recipes/select?${params.toString()}`
  )
  return response.data
}

export const getRecipeByMenu = async (menuName: string, ingredients: string): Promise<RecipeResponse> => {
  const params = new URLSearchParams({
    menu_name: menuName,
    ingredients: ingredients
  })
  const response = await apiClient.post<RecipeResponse>(
    `/api/v1/recipes/by-menu?${params.toString()}`
  )
  return response.data
}

// 초보??모드: 메뉴 검??(Phase 1)
export interface MenuSearchRequest {
  menu_name: string
}

export interface UpdateRequest {
  thread_id: string
  selected_ingredients: string[]
  menu_name?: string  // 메뉴 이름 (상태 복원용, Optional)
}

export const searchMenuForBeginner = async (request: MenuSearchRequest): Promise<RecipeResponse> => {
  const response = await apiClient.post<RecipeResponse>('/api/v1/recipes/search', request)
  return response.data
}

// 초보??모드: ?�료 ?�택 ?�데?�트 (Phase 2-4)
export const updateIngredientSelection = async (request: UpdateRequest): Promise<RecipeResponse> => {
  const response = await apiClient.post<RecipeResponse>('/api/v1/recipes/update', request)
  return response.data
}