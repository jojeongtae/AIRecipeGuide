import axios from 'axios'
import type { Recipe, RecipeResponse } from '../types/recipe'

// ë¡œì»¬ ?˜ê²½?¸ì? ë°°í¬ ?˜ê²½?¸ì? ?ë™ ê°ì?
const getApiBaseUrl = (): string => {
  // ?˜ê²½ ë³€?˜ê? ëª…ì‹œ?ìœ¼ë¡??¤ì •?˜ì–´ ?ˆìœ¼ë©??°ì„  ?¬ìš©
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  
  // ê°œë°œ ?˜ê²½?´ê±°??localhost??ê²½ìš°
  if (import.meta.env.DEV || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000'
  }
  
  // ë°°í¬ ?˜ê²½ (ê¸°ë³¸ê°?
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

// RecipeResponse??types/recipe.ts?ì„œ import

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

// ì´ˆë³´??ëª¨ë“œ: ë©”ë‰´ ê²€??(Phase 1)
export interface MenuSearchRequest {
  menu_name: string
}

export interface UpdateRequest {
  thread_id: string
  selected_ingredients: string[]
}

export const searchMenuForBeginner = async (request: MenuSearchRequest): Promise<RecipeResponse> => {
  const response = await apiClient.post<RecipeResponse>('/api/v1/recipes/search', request)
  return response.data
}

// ì´ˆë³´??ëª¨ë“œ: ?¬ë£Œ ? íƒ ?…ë°?´íŠ¸ (Phase 2-4)
export const updateIngredientSelection = async (request: UpdateRequest): Promise<RecipeResponse> => {
  const response = await apiClient.post<RecipeResponse>('/api/v1/recipes/update', request)
  return response.data
}
