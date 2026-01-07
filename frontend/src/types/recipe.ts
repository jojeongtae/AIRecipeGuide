export interface Recipe {
  id: string
  name: string
  ingredients: string[]
  match_score: number
  difficulty: string
  cooking_time: number
  steps: string[]
  image?: string  // 레시피 이미지 URL
  serving_size?: number  // 인분 수
  category?: string  // 카테고리 (메인요리, 후식, 반찬, 국/찌개 등)
}

export interface NutritionInfo {
  calories: number
  carbohydrates: number
  protein: number
  fat: number
  fiber?: number
}

export interface CookingStep {
  step: number
  description: string
  time?: number
}

export interface ShoppingListItem {
  ingredient: string
  display?: string  // 표시용 (수량 포함, 예: "돼지고기 200g")
  category: string
  quantity?: string  // 수량 정보 (예: "200g")
}

export interface SubstitutionOption {
  ingredient: string
  reason?: string
  confidence?: number
  source?: string
}

export interface SubstitutionSuggestion {
  missing: string
  normalized?: string
  suggestions: SubstitutionOption[]
}

export interface RecipeResponse {
  success: boolean
  data?: {
    recipe?: Recipe
    recipes?: Recipe[]
    nutrition?: NutritionInfo
    cooking_steps?: CookingStep[]
    shopping_list?: ShoppingListItem[]
    substitutions?: SubstitutionSuggestion[]
    search_source?: string // 검색 소스 (tavily, crawler, llm, mixed)
    search_source_label?: string // 검색 소스 라벨 (표시용)
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
    matched_ingredients?: string[]
    missing_ingredients?: string[]
  }
  error?: string
}





