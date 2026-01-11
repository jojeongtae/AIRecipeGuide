import { useState } from 'react';
import { SearchBar } from '../components/SearchBar';
import { RecipeDetail } from '../components/RecipeDetail';
import { IngredientChecklist, IngredientItem } from '../components/IngredientChecklist';
import { Recipe as RecipeCardType } from '../components/RecipeCard';
import { ChefHat, Sparkles, MessageCircle, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { searchMenuForBeginner, updateIngredientSelection, chatWithRecipeBot } from '../services/api';
import type { Recipe } from '../types/recipe';

// types/recipe.ts의 Recipe를 RecipeCardType으로 변환
const convertRecipeToCardType = (recipe: Recipe): RecipeCardType => {
  return {
    id: recipe.id,
    name: recipe.name,
    title: recipe.name,
    image: recipe.image,
    cooking_time: recipe.cooking_time,
    cookTime: `${recipe.cooking_time}분`,
    servings: recipe.serving_size,
    difficulty: recipe.difficulty || recipe.level || '보통',
    category: recipe.category,
    ingredients: recipe.ingredients,
    steps: recipe.steps.map((step, idx) => ({
      step: idx + 1,
      description: step
    })),
    match_rate: recipe.match_rate,
  };
};

export default function BeginnerModePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRecipe, setSelectedRecipe] = useState<RecipeCardType | null>(null);
  const [isChatBotOpen, setIsChatBotOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 챗봇 상태
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'bot'; content: string }>>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  
  // Phase 1: 메뉴 검색 결과
  const [searchResult, setSearchResult] = useState<{
    menuName: string;
    recipes: Recipe[];
    topRecipe?: Recipe;
  } | null>(null);
  
  // Phase 2: 재료 체크리스트
  const [ingredientChecklist, setIngredientChecklist] = useState<IngredientItem[]>([]);
  const [selectedIngredients, setSelectedIngredients] = useState<string[]>([]);
  const [estimatedMatchRate, setEstimatedMatchRate] = useState<number>(0);
  const [threadId, setThreadId] = useState<string | null>(null);

  // 메뉴 검색
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    setSearchResult(null);
    setIngredientChecklist([]);
    setSelectedIngredients([]);

    try {
      // 초보자 모드 API 호출: Phase 1 (메뉴 검색 → 재료 체크리스트)
      const response = await searchMenuForBeginner({ menu_name: searchQuery.trim() });
      
      if (response.success && response.data) {
        const data = response.data;
        const threadIdValue = data.thread_id;
        const menuName = data.menu_name || searchQuery.trim();
        const checklistData = data.ingredients_checklist || {};
        const matchRate = data.estimated_match_rate || checklistData.summary?.estimated_match_rate || 0;
        
        // 재료 체크리스트를 IngredientItem 배열로 변환
        const allIngredients: IngredientItem[] = [];
        let autoChecked: string[] = [];
        
        // 백엔드 응답 형식: ingredients_checklist.items 배열
        const items = checklistData.items || [];
        items.forEach((item: { name: string; category: string; checked: boolean }) => {
          const category: IngredientItem['category'] = 
            (item.category === 'main' || item.category === 'side' || item.category === 'seasoning' || item.category === 'other')
              ? item.category 
              : 'other';
          
          allIngredients.push({
            name: item.name,
            category,
            checked: item.checked || false
          });
          
          if (item.checked) {
            autoChecked.push(item.name);
          }
        });
        
        setThreadId(threadIdValue || null);
        
        // 레시피 정보가 있으면 표시용으로 저장
        const recipeInfo = data.recipe_info;
        setSearchResult({
          menuName,
          recipes: recipeInfo ? [{
            id: '1',
            name: recipeInfo.name || menuName,
            ingredients: [],
            match_score: 0,
            difficulty: recipeInfo.difficulty || '보통',
            cooking_time: recipeInfo.cooking_time || 30,
            steps: [],
            image: recipeInfo.image,
            popularity_display: recipeInfo.popularity_display
          } as Recipe] : [],
          topRecipe: recipeInfo ? {
            id: '1',
            name: recipeInfo.name || menuName,
            ingredients: [],
            match_score: 0,
            difficulty: recipeInfo.difficulty || '보통',
            cooking_time: recipeInfo.cooking_time || 30,
            steps: [],
            image: recipeInfo.image,
            popularity_display: recipeInfo.popularity_display
          } as Recipe : undefined
        });
        setIngredientChecklist(allIngredients);
        setSelectedIngredients(autoChecked);
        setEstimatedMatchRate(matchRate);
      } else {
        setError(response.error || '레시피를 찾을 수 없습니다. 다른 메뉴 이름으로 검색해보세요.');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '검색 중 오류가 발생했습니다.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 재료 선택 변경 (selected = 없는 재료 목록)
  const handleIngredientChange = (selected: string[]) => {
    setSelectedIngredients(selected);
    if (ingredientChecklist.length > 0) {
      // 매칭률 계산: 체크되지 않은 재료 = 있는 재료
      const matchRate = (ingredientChecklist.length - selected.length) / ingredientChecklist.length;
      setEstimatedMatchRate(matchRate);
    }
  };

  // 재료 선택 완료 후 최종 레시피 요청
  // selectedIngredients = 없는 재료 목록 (체크된 재료)
  const handleConfirmIngredients = async () => {
    if (!threadId || !searchResult) return;

    setLoading(true);
    setError(null);

    try {
      // 초보자 모드 API 호출: Phase 2-4 (재료 선택 → 최종 레시피 생성)
      const response = await updateIngredientSelection({
        thread_id: threadId,
        selected_ingredients: selectedIngredients,
        menu_name: searchResult.menuName
      });

      if (response.success && response.data) {
        console.log('레시피 생성 응답:', response.data); // 디버깅용
        let recipeCard: RecipeCardType;
        
        // final_output이 있으면 사용 (초보자 모드 최종 출력)
        if (response.data.final_output) {
          console.log('final_output:', response.data.final_output); // 디버깅용
          const finalOutput = response.data.final_output;
          recipeCard = {
            id: '1',
            name: finalOutput.recipe_name || searchResult.menuName,
            title: finalOutput.recipe_name || searchResult.menuName,
            image: finalOutput.metadata?.image,
            cooking_time: finalOutput.metadata?.cooking_time || 30,
            cookTime: finalOutput.metadata?.cooking_time ? `${finalOutput.metadata.cooking_time}분` : undefined,
            servings: finalOutput.metadata?.serving_size || 2,
            difficulty: finalOutput.metadata?.difficulty || '보통',
            ingredients: finalOutput.ingredients || selectedIngredients,
            steps: (finalOutput.cooking_steps || []).map((step: any) => ({
              step: step.step || 0,
              description: typeof step === 'string' ? step : step.description || ''
            })),
            popularity_display: finalOutput.source_info?.popularity_display,
            substitutions: finalOutput.substitutions,
          };
        } else if (response.data.recipe) {
          // 기존 레시피 응답 형식 사용 (fallback)
          recipeCard = convertRecipeToCardType(response.data.recipe);
        } else {
          setError('레시피 데이터를 받지 못했습니다.');
          return;
        }
        
        setSelectedRecipe(recipeCard);
      } else {
        setError(response.error || '레시피를 생성할 수 없습니다.');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '레시피 생성 중 오류가 발생했습니다.';
      setError(errorMessage);
      console.error('레시피 생성 오류:', err);
    } finally {
      setLoading(false);
    }
  };

  // 추천 검색어
  const suggestedKeywords = ['김치찌개', '파스타', '샐러드', '티라미수', '미역국', '스테이크'];

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 via-pink-50 to-yellow-50">
      {/* Main Content */}
      <main className="max-w-md mx-auto px-4 flex flex-col items-center justify-center min-h-screen py-8">
        {/* Logo & Title */}
        {!searchResult && (
          <div className="w-full text-center mb-12">
            <div className="flex items-center justify-center gap-3 mb-4">
              <ChefHat className="w-12 h-12 text-orange-500" />
            </div>
            <h1 className="text-4xl mb-3">레시피 검색</h1>
            <p className="text-gray-500 text-lg">
              원하는 요리를 검색해보세요
            </p>
          </div>
        )}

        {/* Search Bar */}
        <div className="w-full mb-4">
          <SearchBar 
            value={searchQuery} 
            onChange={setSearchQuery}
            onSearch={handleSearch}
            placeholder="레시피를 검색하세요... (예: 김치찌개)"
          />
        </div>
        
        {/* Tip: 정확한 레시피 이름 유도 */}
        {!searchResult && (
          <div className="w-full mb-8 px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              💡 <strong>Tip:</strong> 메뉴 이름을 구체적으로 입력하시면 더 정확한 레시피를 찾을 수 있습니다
            </p>
            <p className="text-xs text-blue-600 mt-1">
              예: "까르보나라", "스팸김치찌개", "돼지고기김치찌개"
            </p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4"></div>
            <p className="text-gray-600">검색 중...</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="w-full bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Phase 1: 검색 결과 및 재료 체크리스트 */}
        {searchResult && !selectedRecipe && (
          <div className="w-full space-y-6">
            {/* 검색 결과 정보 */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-xl font-semibold mb-2">{searchResult.menuName}</h2>
              {searchResult.topRecipe?.popularity_display && (
                <p className="text-sm text-orange-600 font-medium mb-2">
                  {searchResult.topRecipe.popularity_display}
                </p>
              )}
              <p className="text-sm text-gray-600">
                인기 레시피를 찾았습니다! 보유한 재료를 체크해주세요.
              </p>
            </div>

            {/* 재료 체크리스트 */}
            {ingredientChecklist.length > 0 && (
              <IngredientChecklist
                ingredients={ingredientChecklist}
                onChange={handleIngredientChange}
                estimatedMatchRate={estimatedMatchRate}
              />
            )}

            {/* 확인 버튼 */}
            <Button
              onClick={handleConfirmIngredients}
              disabled={loading}
              className="w-full bg-orange-500 hover:bg-orange-600 text-white py-3 text-lg font-semibold"
            >
              {loading ? '처리 중...' : '레시피 생성하기'}
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </div>
        )}

        {/* 추천 검색어 */}
        {!searchResult && !loading && (
          <>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
              <Sparkles className="w-4 h-4 text-orange-400" />
              <span>AI가 레시피를 추천해드립니다</span>
            </div>
            <div className="mt-8 text-center w-full">
              <p className="text-sm text-gray-400 mb-3">추천 검색어</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {suggestedKeywords.map((keyword) => (
                  <button
                    key={keyword}
                    onClick={() => {
                      setSearchQuery(keyword);
                      setTimeout(() => handleSearch(), 100);
                    }}
                    className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm hover:border-orange-300 hover:bg-orange-50 transition-colors"
                  >
                    {keyword}
                  </button>
                ))}
              </div>
            </div>
          </>
        )}
      </main>

      {/* Recipe Detail Modal */}
      {selectedRecipe && (
        <RecipeDetail
          recipe={selectedRecipe}
          onClose={() => {
            setSelectedRecipe(null);
            setSearchResult(null);
            setSearchQuery('');
          }}
        />
      )}

      {/* ChatBot Floating Button */}
      {!isChatBotOpen && (
        <Button
          onClick={() => setIsChatBotOpen(true)}
          size="icon"
          className="fixed bottom-4 right-4 w-14 h-14 rounded-full shadow-lg bg-orange-500 hover:bg-orange-600 z-50"
        >
          <MessageCircle className="w-6 h-6" />
        </Button>
      )}

      {/* ChatBot Modal */}
      {isChatBotOpen && (
        <div className="fixed bottom-20 right-4 w-80 h-96 bg-white rounded-lg shadow-2xl z-50 border border-gray-200 flex flex-col">
          <div className="p-4 border-b flex items-center justify-between">
            <h3 className="font-semibold">레시피 AI 챗봇</h3>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsChatBotOpen(false)}
              className="h-6 w-6"
            >
              ✕
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.length === 0 && (
              <div className="text-center text-gray-500 text-sm py-8">
                요리 관련 질문을 해주세요!
                <br />
                예: "나는 집에 소금이 없는데 어떻게해?"
              </div>
            )}
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-3 py-2 ${
                    msg.role === 'user'
                      ? 'bg-orange-500 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-3 py-2">
                  <div className="text-sm text-gray-500">답변 생성 중...</div>
                </div>
              </div>
            )}
          </div>
          <div className="p-4 border-t">
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (!chatInput.trim() || chatLoading) return;

                const userQuestion = chatInput.trim();
                setChatInput('');
                setChatMessages((prev) => [...prev, { role: 'user', content: userQuestion }]);
                setChatLoading(true);

                try {
                  const response = await chatWithRecipeBot({ 
                    question: userQuestion,
                    menu_name: searchResult?.menuName || undefined
                  });
                  if (response.success && response.data?.answer) {
                    setChatMessages((prev) => [
                      ...prev,
                      { role: 'bot', content: response.data!.answer! },
                    ]);
                  } else {
                    setChatMessages((prev) => [
                      ...prev,
                      { role: 'bot', content: response.error || '답변을 생성할 수 없습니다.' },
                    ]);
                  }
                } catch (err: any) {
                  setChatMessages((prev) => [
                    ...prev,
                    { role: 'bot', content: err.message || '오류가 발생했습니다.' },
                  ]);
                } finally {
                  setChatLoading(false);
                }
              }}
              className="flex gap-2"
            >
              <Input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="질문을 입력하세요..."
                className="flex-1"
                disabled={chatLoading}
              />
              <Button type="submit" disabled={chatLoading || !chatInput.trim()}>
                전송
              </Button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
