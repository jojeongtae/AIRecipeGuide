import axios from 'axios'
import type { Recipe, NutritionInfo, CookingStep, ShoppingListItem, SubstitutionSuggestion } from '../types/recipe'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://airecipeguide-production.up.railway.app'

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
}

export interface RecipeResponse {
  success: boolean
  data?: {
    recipes?: Recipe[]
    recipe?: Recipe
    nutrition?: NutritionInfo
    cooking_steps?: CookingStep[]
    shopping_list?: ShoppingListItem[]
    substitutions?: SubstitutionSuggestion[]
    search_source?: string
    search_source_label?: string
    substitution_guidances?: Array<{
      user_ingredient: string
      required_ingredient: string
      guidance: string
    }>
    storage_tips?: Array<{
      ingredient: string
      storage_tips: string[]
      utilization_tips?: string[]
    }>
  }
  error?: string
}

export const recommendRecipe = async (request: RecipeRequest): Promise<RecipeResponse> => {
  const response = await apiClient.post<RecipeResponse>('/api/v1/recipes/recommend', request)
  return response.data
}

export const selectRecipe = async (recipeIndex: number, ingredients: string/*, servingSize?: number*/): Promise<RecipeResponse> => {
  const params = new URLSearchParams({
    recipe_index: recipeIndex.toString(),
    ingredients: ingredients
  })
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

