

// 챗봇
export interface ChatRequest {
  question: string
}

export const chatWithRecipeBot = async (request: ChatRequest): Promise<RecipeResponse> => {
  const response = await apiClient.post<RecipeResponse>('/api/v1/recipes/chat', request)
  return response.data
}

