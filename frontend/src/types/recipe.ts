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
  level?: string  // 난이도 (difficulty와 동일, 하위 호환성)
  match_rate?: number  // 매칭률 (0.0~1.0 또는 0~100)
  missing_ingredients?: string[]  // 부족한 재료 목록
  popularity_display?: string  // 인기도 표시 (예: "🔥 조회수 1만회")
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

export interface BeginnerFinalOutput {
  recipe_name: string
  source_info?: {
    source: string
    source_url?: string
    popularity_display?: string
  }
  metadata?: {
    cooking_time?: number
    difficulty?: string
    serving_size?: number
    image?: string
  }
  ingredients?: string[]
  cooking_steps?: Array<{
    step?: number
    description: string
    [key: string]: any
  }>
  substitutions?: {
    has_substitutions: boolean
    substitution_list?: Array<{
      original: string
      substitute: string
      reason?: string
      taste_change?: string
      usage_tip?: string
    }>
    summary?: string
  }
  matching_info?: {
    match_rate?: number
    matching_score?: number
    category_analysis?: any
  }
  persona?: string
  preparation_guide?: string
  general_tips?: string[]
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
    // 초보자 모드 최종 출력
    final_output?: BeginnerFinalOutput
    // 초보자 모드 Phase 1 응답
    thread_id?: string
    menu_name?: string
    ingredients_checklist?: {
      items?: Array<{ name: string; category: string; checked: boolean }>
      summary?: {
        total: number
        auto_checked: number
        estimated_match_rate: number
        match_rate_display?: string
      }
    }
    estimated_match_rate?: number
    waiting_for_selection?: boolean
    recipe_info?: {
      name?: string
      cooking_time?: number
      difficulty?: string
      serving_size?: number
      image?: string
      popularity_display?: string
    }
  }
  error?: string
}





