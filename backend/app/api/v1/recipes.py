"""
Recipe API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.models.state import GraphState, Difficulty, UserPersona
from app.graph.graph import beginner_mode_graph
# recipe_graph는 추후 숙련가 모드 구현 시 사용 예정
# from app.graph.graph import recipe_graph
import uuid
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
    category: Optional[str] = None,
    menu_name: Optional[str] = None,
    user_selected_ingredients: Optional[List[str]] = None
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
        # 초보자 모드 전용 필드
        "menu_name": menu_name,
        "original_recipe": None,
        "structured_recipe": None,
        "extracted_ingredients": None,
        "extracted_categories": None,
        "ingredients_checklist": None,
        "grouped_ingredients": None,
        "estimated_match_rate": None,
        "waiting_for_user_selection": False,
        "user_selected_ingredients": user_selected_ingredients or [],
        "interrupt_reason": None,
        "category_analysis": None,
        "adapted_recipe_steps": None,
        "adapted_ingredients": None,
        "substitution_mapping": None,
        "substitution_details": None,
        "optimized_recipe_steps": None,
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


# ============================================================================
# 추후 숙련가 모드 구현 시 사용 예정 코드
# ============================================================================

# @router.post("/recommend", response_model=RecipeResponse)
# async def recommend_recipe(request: RecipeRequest):
#     """
#     재료 기반 레시피 추천 (숙련가 모드용)
#     """
#     from app.utils.logger import get_logger
#     logger = get_logger(__name__)
#     logger.info(f"레시피 추천 요청: 재료={request.ingredients}, 페르소나={request.user_persona}")
#     
#     try:
#         # user_persona 처리
#         user_persona_enum = None
#         if request.user_persona:
#             try:
#                 user_persona_enum = UserPersona(request.user_persona)
#             except ValueError:
#                 user_persona_enum = UserPersona.BEGINNER  # 기본값
#         
#         initial_state = create_initial_state(
#             user_input=request.ingredients,
#             difficulty=request.difficulty,
#             max_cooking_time=request.max_cooking_time,
#             dietary_preferences=request.dietary_preferences,
#             serving_size=request.serving_size,
#             category=request.category,
#             user_persona=user_persona_enum
#         )
#         
#         from app.graph.nodes import input_ingredients, analyze_ingredients, search_recipes, compare_and_select_source, filter_recipes
#         
#         state = input_ingredients(initial_state)
#         logger.info(f"입력 재료: {state.get('ingredients', [])}")
#         
#         state = analyze_ingredients(state)
#         logger.info(f"분석된 재료: {state.get('ingredients', [])}")
#         
#         state = search_recipes(state)
#         logger.info(f"검색 결과 - 크롤링: {len(state.get('crawler_recipes', []))}, Tavily: {len(state.get('tavily_recipes', []))}, LLM: {len(state.get('llm_recipes', []))}")
#         
#         state = compare_and_select_source(state)
#         logger.info(f"소스 선택 후 레시피 수: {len(state.get('recipes', []))}")
#         
#         # 카테고리 필터링 적용
#         state = filter_recipes(state)
#         recipes = state.get("recipes", [])
#         logger.info(f"카테고리 필터링 후 레시피 수: {len(recipes)}, 카테고리: {initial_state.get('category')}")
#         
#         if not recipes or len(recipes) == 0:
#             logger.warning("레시피를 찾을 수 없습니다.")
#             return RecipeResponse(
#                 success=False,
#                 error="입력하신 재료로 만들 수 있는 레시피를 찾을 수 없습니다."
#             )
#         
#         search_source = state.get("search_source", "unknown")
#         logger.info(f"선택된 소스: {search_source}, 레시피 수: {len(recipes)}")
#         
#         return RecipeResponse(
#             success=True,
#             data={
#                 "recipes": recipes,
#                 "search_source": search_source,
#                 "search_source_label": {
#                     "tavily": "🌐 실시간 웹 검색 (Tavily)",
#                     "crawler": "📋 만개의레시피 크롤링",
#                     "llm": "🤖 AI 레시피 생성",
#                     "mixed": "🔀 혼합 소스"
#                 }.get(search_source, "알 수 없음")
#             }
#         )
#         
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/select", response_model=RecipeResponse)
# async def select_recipe(
#     recipe_index: int = Query(..., description="선택한 레시피 인덱스"),
#     ingredients: str = Query(..., description="재료 목록 (쉼표로 구분)"),
#     serving_size: Optional[int] = Query(None, description="인분 수"),
#     user_persona: Optional[str] = Query(None, description="사용자 페르소나 (beginner/expert)"),
#     recipe_id: Optional[str] = Query(None, description="선택한 레시피 ID (정확한 매칭용)"),
#     recipe_name: Optional[str] = Query(None, description="선택한 레시피 이름 (정확한 매칭용)"),
#     recipe_data: Optional[str] = Query(None, description="선택한 레시피 전체 정보 (JSON 문자열)"),
# ):
#     """
#     여러 레시피 중 하나 선택 (숙련가 모드용)
#     """
#     try:
#         # user_persona 처리
#         user_persona_enum = None
#         if user_persona:
#             try:
#                 user_persona_enum = UserPersona(user_persona)
#             except ValueError:
#                 user_persona_enum = UserPersona.BEGINNER  # 기본값
#         
#         initial_state = create_initial_state(
#             user_input=ingredients,
#             serving_size=serving_size,
#             user_persona=user_persona_enum
#         )
#         initial_state["user_choice"] = recipe_index
#         logger.info(f"레시피 선택 요청: index={recipe_index}, recipe_id={recipe_id}, recipe_name={recipe_name}")
#         
#         # 선택한 레시피를 정확히 식별하기 위한 정보 추가
#         if recipe_id:
#             initial_state["selected_recipe_id"] = recipe_id
#         if recipe_name:
#             initial_state["selected_recipe_name"] = recipe_name
#         # 선택한 레시피 전체 정보 저장 (재검색 결과에 없을 때 사용)
#         if recipe_data:
#             try:
#                 import json
#                 selected_recipe_data = json.loads(recipe_data)
#                 initial_state["pre_selected_recipe"] = selected_recipe_data
#                 logger.info(f"선택한 레시피 정보 저장: {selected_recipe_data.get('name', 'Unknown')}")
#             except Exception as e:
#                 logger.warning(f"레시피 데이터 파싱 실패: {e}")
#         
#         logger.info("레시피 상세정보 생성 시작...")
#         # from app.graph.graph import recipe_graph  # 추후 숙련가 모드 구현 시 주석 해제
#         # result = recipe_graph.invoke(initial_state)
#         #
#         # if result.get("error"):
#         #     logger.error(f"레시피 처리 중 오류: {result.get('error')}")
#         #     return RecipeResponse(
#         #         success=False,
#         #         error=result.get("error", "레시피 처리 중 오류가 발생했습니다.")
#         #     )
#         #
#         # if not result.get("final_output"):
#         #     logger.warning("레시피 정보를 생성할 수 없습니다.")
#         #     return RecipeResponse(
#         #         success=False,
#         #         error="레시피 정보를 생성할 수 없습니다."
#         #     )
#         #
#         # final_output = result.get("final_output", {})
#         # recipe_name = final_output.get("recipe", {}).get("name") if isinstance(final_output.get("recipe"), dict) else "Unknown"
#         # logger.info(f"레시피 상세정보 생성 완료: {recipe_name}")
#         #
#         # # 레시피 상세정보 DB 저장 시도
#         # try:
#         #     from app.database import SessionLocal
#         #     from app.services.db_service import save_recipe
#         #
#         #     recipe_data = final_output.get("recipe", {})
#         #     if recipe_data:
#         #         db = SessionLocal()
#         #         # 상세정보 포함하여 저장 (영양정보, 최적화된 조리단계 등)
#         #         recipe_data_to_save = recipe_data.copy()
#         #         # final_output에서 추가 정보 가져오기
#         #         if final_output.get("nutrition"):
#         #             recipe_data_to_save["nutrition_info"] = final_output.get("nutrition")
#         #         if final_output.get("cooking_steps"):
#         #             recipe_data_to_save["steps"] = final_output.get("cooking_steps")
#         #
#         #         recipe_id = save_recipe(db, recipe_data_to_save)
#         #         if recipe_id:
#         #             logger.info(f"레시피 상세정보 DB 저장 완료: {recipe_id} ({recipe_name})")
#         #         else:
#         #             logger.warning(f"레시피 상세정보 DB 저장 실패: {recipe_name}")
#         #         db.close()
#         # except Exception as e:
#         #     logger.warning(f"레시피 상세정보 DB 저장 중 오류 (기존 로직 계속 진행): {e}")
#         #
#         # return RecipeResponse(
#         #     success=True,
#         #     data=final_output
#         # )
#         
#     except Exception as e:
#         import traceback
#         logger.error(f"레시피 선택 오류: {e}")
#         logger.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail=f"레시피 선택 중 오류가 발생했습니다: {str(e)}")


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


# ==================== 초보자 모드 API 엔드포인트 ====================

class MenuSearchRequest(BaseModel):
    """메뉴 검색 요청 (초보자 모드)"""
    menu_name: str  # 메뉴 이름


class UpdateRequest(BaseModel):
    """재료 선택 업데이트 요청 (초보자 모드)"""
    thread_id: str  # 그래프 실행 thread_id
    selected_ingredients: List[str]  # 사용자가 선택한 재료 리스트
    menu_name: Optional[str] = None  # 메뉴 이름 (상태 복원용)


class ChatRequest(BaseModel):
    """챗봇 질문 요청"""
    question: str  # 사용자 질문
    menu_name: Optional[str] = None  # 현재 만들고 있는 메뉴 이름 (컨텍스트용)


@router.post("/search", response_model=RecipeResponse)
async def search_menu_for_beginner(request: MenuSearchRequest):
    """
    초보자 모드: 메뉴 검색 및 재료 체크리스트 반환
    
    Phase 1 실행 (search_menu_recipe → extract_recipe_data → present_ingredients_to_user)
    interrupt 후 재료 체크리스트 반환
    """
    try:
        menu_name = request.menu_name.strip()
        if not menu_name:
            return RecipeResponse(
                success=False,
                error="메뉴 이름을 입력해주세요."
            )
        
        logger.info(f"초보자 모드 메뉴 검색: {menu_name}")
        
        # 초기 상태 생성
        initial_state = create_initial_state(
            user_input=menu_name,
            user_persona=UserPersona.BEGINNER,
            menu_name=menu_name
        )
        
        # thread_id 생성 (checkpointer와 연동)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        # beginner_mode_graph 실행 (interrupt까지)
        try:
            # 그래프 실행 - interrupt까지 실행 (wait_for_ingredient_selection에서 END)
            result = beginner_mode_graph.invoke(initial_state, config=config)
            
            # 상태가 checkpointer에 저장되었는지 확인
            saved_state = beginner_mode_graph.get_state(config)
            if not saved_state or not saved_state.values:
                logger.warning(f"그래프 실행 후 상태가 저장되지 않았습니다. thread_id: {thread_id}")
                # 상태가 없어도 결과는 반환 (결과에 필요한 정보가 있으면)
            
        except Exception as e:
            logger.error(f"그래프 실행 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return RecipeResponse(success=False, error=f"레시피 검색 중 오류가 발생했습니다: {str(e)}")
        
        # 재료 체크리스트 및 레시피 기본 정보 반환
        ingredients_checklist = result.get("ingredients_checklist", {})
        estimated_match_rate = result.get("estimated_match_rate", 0.0)
        menu_name_result = result.get("menu_name", menu_name)
        structured_recipe = result.get("structured_recipe", {})
        original_recipe = result.get("original_recipe", {})
        
        # 레시피 기본 정보 구성 (프론트엔드 표시용)
        recipe_info = None
        if structured_recipe:
            recipe_info = {
                "name": structured_recipe.get("name", menu_name_result),
                "cooking_time": structured_recipe.get("cooking_time"),
                "difficulty": structured_recipe.get("difficulty"),
                "serving_size": structured_recipe.get("serving_size"),
                "image": structured_recipe.get("image") or original_recipe.get("image"),
                "popularity_display": original_recipe.get("popularity_display") or structured_recipe.get("popularity_display")
            }
        
        logger.info(f"메뉴 검색 완료: {menu_name_result}, 재료 체크리스트 준비 완료, thread_id: {thread_id}")
        
        return RecipeResponse(
            success=True,
            data={
                "thread_id": thread_id,
                "menu_name": menu_name_result,
                "ingredients_checklist": ingredients_checklist,
                "estimated_match_rate": estimated_match_rate,
                "waiting_for_selection": True,
                "recipe_info": recipe_info  # 레시피 기본 정보 추가
            }
        )
    
    except Exception as e:
        import traceback
        logger.error(f"메뉴 검색 오류: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"메뉴 검색 중 오류가 발생했습니다: {str(e)}")


@router.post("/update", response_model=RecipeResponse)
async def update_ingredient_selection(request: UpdateRequest):
    """
    초보자 모드: 재료 선택 업데이트 및 최종 레시피 생성
    
    Phase 2-4 실행 (wait_for_ingredient_selection → analyze_user_situation → ... → generate_final_output)
    """
    try:
        thread_id = request.thread_id
        selected_ingredients = request.selected_ingredients
        
        # selected_ingredients = 없는 재료 목록 (체크된 재료)
        # 빈 리스트도 허용 (모든 재료가 있는 경우)
        
        logger.info(f"재료 선택 업데이트: thread_id={thread_id}, 없는 재료 {len(selected_ingredients)}개")
        
        # checkpointer에서 상태 복원
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # 저장된 상태 확인
            saved_state = beginner_mode_graph.get_state(config)
            
            logger.info(f"상태 조회 결과: saved_state={saved_state}, values 존재: {saved_state.values if saved_state else None}")
            
            # 상태가 없을 때 menu_name으로 Phase 1 재실행 (상태 복원)
            if not saved_state or not saved_state.values:
                logger.warning(f"저장된 상태를 찾을 수 없습니다. thread_id: {thread_id}. menu_name으로 Phase 1 재실행")
                
                if not request.menu_name:
                    return RecipeResponse(
                        success=False,
                        error=f"저장된 상태를 찾을 수 없습니다. thread_id: {thread_id}. 메뉴를 다시 검색해주세요."
                    )
                
                # Phase 1 재실행하여 상태 복원
                from app.graph.nodes import search_menu_recipe, extract_recipe_data, present_ingredients_to_user
                
                initial_state = create_initial_state(
                    user_input=request.menu_name,
                    user_persona=UserPersona.BEGINNER,
                    menu_name=request.menu_name
                )
                
                state = search_menu_recipe(initial_state)
                if state.get("error"):
                    return RecipeResponse(success=False, error=state["error"])
                
                state = extract_recipe_data(state)
                if state.get("error"):
                    return RecipeResponse(success=False, error=state["error"])
                
                state = present_ingredients_to_user(state)
                if state.get("error"):
                    return RecipeResponse(success=False, error=state["error"])
                
                current_state = state
                logger.info(f"Phase 1 재실행 완료. menu_name: {request.menu_name}")
            else:
                logger.info(f"상태 확인 완료. thread_id: {thread_id}, 상태 키 수: {len(saved_state.values) if saved_state.values else 0}")
                # 현재 상태 가져오기
                current_state = saved_state.values.copy()
            
            # 사용자 선택한 재료로 상태 업데이트
            current_state["user_selected_ingredients"] = selected_ingredients
            current_state["waiting_for_user_selection"] = False  # 재료 선택 완료
            
            # Phase 2-4 노드들을 직접 호출 (LangGraph의 update() 메서드는 존재하지 않음)
            from app.graph.nodes import (
                wait_for_ingredient_selection,
                analyze_user_situation,
                plan_substitutions,
                adapt_recipe_content,
                optimize_for_persona,
                generate_final_output
            )
            
            # Phase 2: 재료 선택 완료 처리
            state = wait_for_ingredient_selection(current_state)
            
            # Phase 3: 사용자 상황 분석 및 가공
            state = analyze_user_situation(state)
            if state.get("error"):
                return RecipeResponse(success=False, error=state["error"])
            
            # 대체재료가 필요한 경우에만 plan_substitutions 실행
            missing_ingredients = state.get("missing_ingredients", [])
            if missing_ingredients:
                state = plan_substitutions(state)
                if state.get("error"):
                    return RecipeResponse(success=False, error=state["error"])
            
            # adapt_recipe_content는 항상 실행
            state = adapt_recipe_content(state)
            if state.get("error"):
                return RecipeResponse(success=False, error=state["error"])
            
            state = optimize_for_persona(state)
            if state.get("error"):
                return RecipeResponse(success=False, error=state["error"])
            
            # Phase 4: 최종 출력 생성
            state = generate_final_output(state)
            if state.get("error"):
                return RecipeResponse(success=False, error=state["error"])
            
            final_output = state.get("final_output")
            if not final_output:
                return RecipeResponse(
                    success=False,
                    error="최종 레시피를 생성할 수 없습니다."
                )
            
            logger.info(f"최종 레시피 생성 완료: {final_output.get('recipe_name', 'Unknown')}")
            
            return RecipeResponse(
                success=True,
                data={
                    "final_output": final_output
                }
            )
        except Exception as inner_e:
            logger.error(f"그래프 업데이트 중 오류: {inner_e}")
            import traceback
            logger.error(traceback.format_exc())
            return RecipeResponse(
                success=False,
                error=f"레시피 생성 중 오류가 발생했습니다: {str(inner_e)}"
            )
    
    except Exception as e:
        import traceback
        logger.error(f"재료 선택 업데이트 오류: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"재료 선택 업데이트 중 오류가 발생했습니다: {str(e)}")


@router.post("/chat", response_model=RecipeResponse)
async def chat_with_recipe_bot(request: ChatRequest):
    """
    요리 챗봇: 요리 관련 질문에 답변
    
    요리 관련 질문만 받도록 필터링하고, 대체재료, 조리법 등 요리 관련 질문에 답변
    예시: "나는 집에 소금이 없는데 어떻게해?"
    """
    try:
        question = request.question.strip()
        if not question:
            return RecipeResponse(
                success=False,
                error="질문을 입력해주세요."
            )
        
        logger.info(f"챗봇 질문: {question}")
        
        # LLM 호출을 위한 import
        from app.graph.utils.llm_helpers import call_openai_api
        from app.config import settings
        
        if not settings.OPENAI_API_KEY:
            return RecipeResponse(
                success=False,
                error="OpenAI API 키가 설정되지 않았습니다."
            )
        
        # 1단계: 요리 관련 질문인지 필터링
        filter_messages = [
            {
                "role": "system",
                "content": "당신은 요리 관련 질문을 판단하는 분류기입니다. 사용자의 질문이 요리, 재료, 조리법, 레시피, 대체재료 등 요리 관련 내용인지 판단하세요. 요리 관련이면 'yes', 그 외면 'no'로만 답변하세요."
            },
            {
                "role": "user",
                "content": f"다음 질문이 요리 관련 질문인가요? (요리, 재료, 조리법, 레시피, 대체재료 등)\n\n질문: {question}\n\n답변: (yes 또는 no만)"
            }
        ]
        
        try:
            filter_response = call_openai_api(
                messages=filter_messages,
                model="gpt-4o-mini",
                temperature=0.3
            )
            
            # 필터링 결과 확인
            is_cooking_related = "yes" in filter_response.lower().strip()
            
            if not is_cooking_related:
                return RecipeResponse(
                    success=False,
                    error="요리 관련 질문만 답변 가능합니다. 요리, 재료, 조리법, 레시피에 관한 질문을 해주세요."
                )
        except Exception as e:
            logger.error(f"필터링 오류: {e}")
            # 필터링 실패 시 그냥 진행 (오류 방지)
            pass
        
        # 2단계: 요리 관련 질문에 답변 생성
        # 현재 만들고 있는 메뉴 정보를 컨텍스트로 추가
        context_text = ""
        if request.menu_name:
            context_text = f"\n\n현재 사용자가 '{request.menu_name}'를 만들고 있습니다. 사용자의 질문이 이 메뉴와 관련된 것으로 이해하고 답변해주세요. 예를 들어, '{request.menu_name}을 만드는 과정에서 재료가 없으시군요' 같은 식으로 자연스럽게 언급하세요."
        
        answer_messages = [
            {
                "role": "system",
                "content": f"""당신은 친절한 요리 챗봇입니다. 사용자의 요리 관련 질문에 대해 실용적이고 도움이 되는 답변을 제공하세요.

특히 다음 상황에서 도움을 제공하세요:
- 재료가 없을 때 대체재료 제안 (예: "소금이 없으면 간장이나 멸치 액젓으로 대체 가능합니다")
- 조리법 궁금증 해결
- 요리 중 발생하는 문제 해결
- 레시피 관련 질문{context_text}

답변은 간결하고 실용적으로, 한국 요리에 맞게 작성하세요."""
            },
            {
                "role": "user",
                "content": question
            }
        ]
        
        try:
            answer = call_openai_api(
                messages=answer_messages,
                model="gpt-4o-mini",
                temperature=0.7
            )
            
            logger.info(f"챗봇 답변 생성 완료: {len(answer)}자")
            
            return RecipeResponse(
                success=True,
                data={
                    "answer": answer,
                    "question": question
                }
            )
        except Exception as e:
            logger.error(f"답변 생성 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return RecipeResponse(
                success=False,
                error=f"답변 생성 중 오류가 발생했습니다: {str(e)}"
            )
    
    except Exception as e:
        import traceback
        logger.error(f"챗봇 오류: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"챗봇 처리 중 오류가 발생했습니다: {str(e)}")
