"""
Recipe API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.models.state import GraphState, Difficulty
from app.graph.graph import recipe_graph

router = APIRouter()


def create_initial_state(
    user_input: str,
    difficulty: Optional[Difficulty] = None,
    max_cooking_time: Optional[int] = None,
    dietary_preferences: Optional[List[str]] = None,
    serving_size: Optional[int] = None,
    user_persona: Optional[str] = None,
    category: Optional[str] = None
) -> GraphState:
    """
    GraphState 초기 상태 생성 헬퍼 함수
    """
    return {
        "user_input": user_input,
        "ingredients": [],
        "ingredient_categories": {},
        "difficulty": difficulty,
        "max_cooking_time": max_cooking_time,
        "dietary_preferences": dietary_preferences,
        "serving_size": serving_size if serving_size is not None else 1,  # 기본값 1인분
        "recipes": [],
        "search_source": None,
        "selected_recipe": None,
        "user_choice": None,
        "nutrition_info": None,
        "optimized_steps": None,
        "required_ingredients": [],
        "missing_ingredients": [],
        "shopping_list": None,
        "substitution_suggestions": None,
        "final_output": None,
        "error": None,
        "retry_count": 0,
        "match_rate": None,
        "correction_iteration": 0,
        "matched_ingredients": [],
        "substitution_guidances": None,
        # Deep Research 필드
        "source_comparison": None,
        "quality_score": None,
        "validation_iteration": 0,
        "crawler_recipes": None,
        "tavily_recipes": None,
        "llm_recipes": None,
        # 페르소나 및 지능형 매칭 관련 필드
        "matching_score": None,
        "user_persona": user_persona,
        "storage_tips": None,
        "category": category,
    }


class RecipeRequest(BaseModel):
    """레시피 추천 요청"""
    ingredients: str  # 콤마로 구분된 재료 목록
    difficulty: Optional[Difficulty] = None
    max_cooking_time: Optional[int] = None
    dietary_preferences: Optional[List[str]] = None
    serving_size: Optional[int] = None  # 인분 수 (기본값: 레시피 원본)
    category: Optional[str] = None  # 카테고리 (메인요리, 후식, 반찬, 국/찌개 등)


class RecipeResponse(BaseModel):
    """레시피 추천 응답"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/recommend", response_model=RecipeResponse)
async def recommend_recipe(request: RecipeRequest):
    """
    재료 기반 레시피 추천
    """
    try:
        initial_state = create_initial_state(
            user_input=request.ingredients,
            difficulty=request.difficulty,
            max_cooking_time=request.max_cooking_time,
            dietary_preferences=request.dietary_preferences,
            serving_size=request.serving_size,
            category=request.category
        )
        
        from app.graph.nodes import input_ingredients, analyze_ingredients, search_recipes, compare_and_select_source, filter_recipes
        
        import logging
        logger = logging.getLogger(__name__)
        
        state = input_ingredients(initial_state)
        logger.info(f"입력 재료: {state.get('ingredients', [])}")
        
        state = analyze_ingredients(state)
        logger.info(f"분석된 재료: {state.get('ingredients', [])}")
        
        state = search_recipes(state)
        logger.info(f"검색 결과 - 크롤링: {len(state.get('crawler_recipes', []))}, Tavily: {len(state.get('tavily_recipes', []))}, LLM: {len(state.get('llm_recipes', []))}")
        
        state = compare_and_select_source(state)
        logger.info(f"소스 선택 후 레시피 수: {len(state.get('recipes', []))}")
        
        # 카테고리 필터링 적용
        state = filter_recipes(state)
        recipes = state.get("recipes", [])
        logger.info(f"카테고리 필터링 후 레시피 수: {len(recipes)}, 카테고리: {initial_state.get('category')}")
        
        if not recipes or len(recipes) == 0:
            logger.warning("레시피를 찾을 수 없습니다.")
            return RecipeResponse(
                success=False,
                error="입력하신 재료로 만들 수 있는 레시피를 찾을 수 없습니다."
            )
        
        search_source = state.get("search_source", "unknown")
        logger.info(f"선택된 소스: {search_source}, 레시피 수: {len(recipes)}")
        
        return RecipeResponse(
            success=True,
            data={
                "recipes": recipes,
                "search_source": search_source,
                "search_source_label": {
                    "tavily": "🌐 실시간 웹 검색 (Tavily)",
                    "crawler": "📋 만개의레시피 크롤링",
                    "llm": "🤖 AI 레시피 생성",
                    "mixed": "🔀 혼합 소스"
                }.get(search_source, "알 수 없음")
            }
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/select", response_model=RecipeResponse)
async def select_recipe(
    recipe_index: int = Query(..., description="선택한 레시피 인덱스"),
    ingredients: str = Query(..., description="재료 목록 (쉼표로 구분)"),
    serving_size: Optional[int] = Query(None, description="인분 수"),
):
    """
    여러 레시피 중 하나 선택
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        initial_state = create_initial_state(
            user_input=ingredients,
            serving_size=serving_size
        )
        initial_state["user_choice"] = recipe_index
        
        result = recipe_graph.invoke(initial_state)
        
        if result.get("error"):
            return RecipeResponse(
                success=False,
                error=result.get("error", "레시피 처리 중 오류가 발생했습니다.")
            )
        
        if not result.get("final_output"):
            return RecipeResponse(
                success=False,
                error="레시피 정보를 생성할 수 없습니다."
            )
        
        return RecipeResponse(
            success=True,
            data=result.get("final_output")
        )
        
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"레시피 선택 오류: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"레시피 선택 중 오류가 발생했습니다: {str(e)}")


@router.post("/by-menu", response_model=RecipeResponse)
async def get_recipe_by_menu(
    menu_name: str = Query(..., description="메뉴 이름 (예: 파스타, 김치찌개)"),
    ingredients: str = Query(..., description="보유 재료 목록 (쉼표로 구분)"),
    serving_size: Optional[int] = Query(None, description="인분 수"),
):
    """
    메뉴 이름 기반 레시피 검색 + 재료 확인
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # 재료 목록 파싱
        user_ingredients_list = [ing.strip() for ing in ingredients.split(",") if ing.strip()]
        
        # 메뉴 이름으로 레시피 검색
        from app.services.recipe_crawler import search_recipes_by_name
        from app.utils.ingredient_checker import check_ingredients_simple
        
        recipes = search_recipes_by_name(
            menu_name=menu_name,
            max_results=3,  # 성능 최적화: 3개로 제한
            user_ingredients=user_ingredients_list
        )
        
        if not recipes:
            return RecipeResponse(
                success=False,
                error=f"'{menu_name}' 레시피를 찾을 수 없습니다."
            )
        
        # 모든 레시피에 매칭률 계산 및 추가 (병렬 처리)
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def calculate_match_rate(recipe):
            """레시피 매칭률 계산 (별도 함수로 분리)"""
            recipe_copy = recipe.copy()
            
            # serving_size 필드 제거 (항상 1인분 기준, 표시하지 않음)
            if "serving_size" in recipe_copy:
                del recipe_copy["serving_size"]
            
            # 재료 비교하여 매칭률 계산
            ingredient_check_result = check_ingredients_simple(
                required_ingredients=recipe_copy.get("ingredients", []),
                user_ingredients=user_ingredients_list,
                recipe_name=recipe_copy.get("name", "")
            )
            
            # 매칭률 정보 추가
            recipe_copy["match_rate"] = ingredient_check_result["match_rate"]
            recipe_copy["matched_ingredients"] = ingredient_check_result["matched_ingredients"]
            recipe_copy["missing_ingredients"] = ingredient_check_result["missing_ingredients"]
            
            return recipe_copy
        
        # 병렬 처리로 매칭률 계산 (성능 최적화)
        recipes_with_match_rate = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_recipe = {
                executor.submit(calculate_match_rate, recipe): recipe
                for recipe in recipes
            }
            
            for future in as_completed(future_to_recipe):
                try:
                    recipe_with_match = future.result()
                    recipes_with_match_rate.append(recipe_with_match)
                except Exception as e:
                    logger.error(f"매칭률 계산 오류: {e}")
                    continue
            recipe_copy = recipe.copy()
            
            # serving_size 필드 제거 (항상 1인분 기준, 표시하지 않음)
            if "serving_size" in recipe_copy:
                del recipe_copy["serving_size"]
            
            # 재료 비교하여 매칭률 계산
            ingredient_check_result = check_ingredients_simple(
                required_ingredients=recipe_copy.get("ingredients", []),
                user_ingredients=user_ingredients_list,
                recipe_name=recipe_copy.get("name", "")
            )
            
            # 매칭률 정보 추가
            recipe_copy["match_rate"] = ingredient_check_result["match_rate"]
            recipe_copy["matched_ingredients"] = ingredient_check_result["matched_ingredients"]
            recipe_copy["missing_ingredients"] = ingredient_check_result["missing_ingredients"]
            
            recipes_with_match_rate.append(recipe_copy)
        
        # 정렬: 레시피 이름에 메뉴 이름이 포함된 것을 우선, 그 다음 매칭률 순
        def sort_key(recipe):
            name = recipe.get("name", "").lower()
            menu_lower = menu_name.lower()
            name_match = 1 if menu_lower in name else 0  # 이름에 메뉴명 포함되면 1, 아니면 0
            match_rate = recipe.get("match_rate", 0.0)
            return (name_match, match_rate)  # 튜플 정렬: 첫 번째 요소 우선, 같으면 두 번째 요소
        recipes_with_match_rate.sort(key=sort_key, reverse=True)
        
        # 응답 데이터 구성 (레시피 목록 반환)
        result_data = {
            "recipes": recipes_with_match_rate
        }
        
        return RecipeResponse(
            success=True,
            data=result_data
        )
        
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"메뉴 기반 레시피 검색 오류: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"레시피 검색 중 오류가 발생했습니다: {str(e)}")

