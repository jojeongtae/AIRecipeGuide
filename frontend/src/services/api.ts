import axios from 'axios'
import type { Recipe, RecipeResponse } from '../types/recipe'

// 로컬 환경인지 배포 환경인지 자동 감지
const getApiBaseUrl = (): string => {
  // 환경 변수가 명시적으로 설정되어 있으면 우선 사용
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  
  // 개발 환경이거나 localhost인 경우
  if (import.meta.env.DEV || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:5000'
  }
  
  // 배포 환경 (기본값)
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

// RecipeResponse는 types/recipe.ts에서 import

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

