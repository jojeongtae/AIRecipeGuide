"""
Recipe API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.models.state import GraphState, Difficulty, UserPersona
from app.graph.graph import recipe_graph
from app.utils.logger import get_logger

logger = get_logger(__name__)

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
    user_persona: Optional[str] = None  # 사용자 페르소나 (beginner/expert)


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
    from app.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info(f"레시피 추천 요청: 재료={request.ingredients}, 페르소나={request.user_persona}")
    
    try:
        # user_persona 처리
        user_persona_enum = None
        if request.user_persona:
            try:
                user_persona_enum = UserPersona(request.user_persona)
            except ValueError:
                user_persona_enum = UserPersona.BEGINNER  # 기본값
        
        initial_state = create_initial_state(
            user_input=request.ingredients,
            difficulty=request.difficulty,
            max_cooking_time=request.max_cooking_time,
            dietary_preferences=request.dietary_preferences,
            serving_size=request.serving_size,
            category=request.category,
            user_persona=user_persona_enum
        )
        
        from app.graph.nodes import input_ingredients, analyze_ingredients, search_recipes, compare_and_select_source, filter_recipes
        
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
    user_persona: Optional[str] = Query(None, description="사용자 페르소나 (beginner/expert)"),
    recipe_id: Optional[str] = Query(None, description="선택한 레시피 ID (정확한 매칭용)"),
    recipe_name: Optional[str] = Query(None, description="선택한 레시피 이름 (정확한 매칭용)"),
    recipe_data: Optional[str] = Query(None, description="선택한 레시피 전체 정보 (JSON 문자열)"),
):
    """
    여러 레시피 중 하나 선택
    """
    try:
        # user_persona 처리
        user_persona_enum = None
        if user_persona:
            try:
                user_persona_enum = UserPersona(user_persona)
            except ValueError:
                user_persona_enum = UserPersona.BEGINNER  # 기본값
        
        initial_state = create_initial_state(
            user_input=ingredients,
            serving_size=serving_size,
            user_persona=user_persona_enum
        )
        initial_state["user_choice"] = recipe_index
        logger.info(f"레시피 선택 요청: index={recipe_index}, recipe_id={recipe_id}, recipe_name={recipe_name}")
        
        # 선택한 레시피를 정확히 식별하기 위한 정보 추가
        if recipe_id:
            initial_state["selected_recipe_id"] = recipe_id
        if recipe_name:
            initial_state["selected_recipe_name"] = recipe_name
        # 선택한 레시피 전체 정보 저장 (재검색 결과에 없을 때 사용)
        if recipe_data:
            try:
                import json
                selected_recipe_data = json.loads(recipe_data)
                initial_state["pre_selected_recipe"] = selected_recipe_data
                logger.info(f"선택한 레시피 정보 저장: {selected_recipe_data.get('name', 'Unknown')}")
            except Exception as e:
                logger.warning(f"레시피 데이터 파싱 실패: {e}")
        
        logger.info("레시피 상세정보 생성 시작...")
        result = recipe_graph.invoke(initial_state)
        
        if result.get("error"):
            logger.error(f"레시피 처리 중 오류: {result.get('error')}")
            return RecipeResponse(
                success=False,
                error=result.get("error", "레시피 처리 중 오류가 발생했습니다.")
            )
        
        if not result.get("final_output"):
            logger.warning("레시피 정보를 생성할 수 없습니다.")
            return RecipeResponse(
                success=False,
                error="레시피 정보를 생성할 수 없습니다."
            )
        
        final_output = result.get("final_output", {})
        recipe_name = final_output.get("recipe", {}).get("name") if isinstance(final_output.get("recipe"), dict) else "Unknown"
        logger.info(f"레시피 상세정보 생성 완료: {recipe_name}")
        
        # 레시피 상세정보 DB 저장 시도
        try:
            from app.database import SessionLocal
            from app.services.db_service import save_recipe
            
            recipe_data = final_output.get("recipe", {})
            if recipe_data:
                db = SessionLocal()
                # 상세정보 포함하여 저장 (영양정보, 최적화된 조리단계 등)
                recipe_data_to_save = recipe_data.copy()
                # final_output에서 추가 정보 가져오기
                if final_output.get("nutrition"):
                    recipe_data_to_save["nutrition_info"] = final_output.get("nutrition")
                if final_output.get("cooking_steps"):
                    recipe_data_to_save["steps"] = final_output.get("cooking_steps")
                
                recipe_id = save_recipe(db, recipe_data_to_save)
                if recipe_id:
                    logger.info(f"레시피 상세정보 DB 저장 완료: {recipe_id} ({recipe_name})")
                else:
                    logger.warning(f"레시피 상세정보 DB 저장 실패: {recipe_name}")
                db.close()
        except Exception as e:
            logger.warning(f"레시피 상세정보 DB 저장 중 오류 (기존 로직 계속 진행): {e}")
        
        return RecipeResponse(
            success=True,
            data=final_output
        )
        
    except Exception as e:
        import traceback
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
        
        # 이름 일치도 점수 추가 (이미 search_recipes_by_name에서 계산됨)
        # 추가로 매칭률 기반 정렬도 고려
        
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
        
        # 최종 정렬: 이름 일치도 우선 (이미 search_recipes_by_name에서 계산됨), 그 다음 매칭률
        # name_similarity가 이미 계산되어 있으므로 이를 우선 사용
        recipes_with_match_rate.sort(
            key=lambda x: (
                x.get("name_similarity", 0.0),  # 이름 일치도 (내림차순)
                x.get("match_rate", 0.0)  # 재료 매칭률 (내림차순)
            ),
            reverse=True
        )
        
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
        logger.error(f"메뉴 기반 레시피 검색 오류: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"레시피 검색 중 오류가 발생했습니다: {str(e)}")

