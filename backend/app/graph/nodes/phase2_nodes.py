"""
Phase 2: phase2 노드 함수들
"""

"""
LangGraph Node Functions
"""
import json
import re
import logging
import requests
from typing import Dict, Any, List, Optional, Tuple
from app.models.state import GraphState, UserPersona
from app.config import settings
from app.utils.ingredient_map import IngredientNormalizer, check_ingredient_substitution_with_llm
from app.constants import (
    SUBSTITUTION_RULES,
    CATEGORY_SUBSTITUTIONS,
    CATEGORY_BLACKLIST_KEYWORDS,
    MAIN_INGREDIENT_WEIGHT,
    SIDE_INGREDIENT_WEIGHT,
    SEASONING_INGREDIENT_WEIGHT,
    CONFIDENCE_MATCH_RATE_WEIGHT,
    CONFIDENCE_MATCHING_SCORE_WEIGHT,
    CONFIDENCE_QUALITY_SCORE_WEIGHT,
    CONFIDENCE_NUTRITION_BONUS,
    DEFAULT_SERVING_SIZE,
    DEFAULT_COOKING_TIME,
    DEFAULT_DIFFICULTY
)
from app.graph.utils.llm_helpers import call_openai_api, extract_json_from_response
from app.graph.utils.ingredient_utils import (
    normalize_ingredient_name,
    parse_ingredient_quantity,
    categorize_ingredient,
    identify_main_ingredient,
    calculate_intelligent_matching_score
)
from app.graph.utils.recipe_utils import (
    adjust_ingredient_quantity,
    classify_recipe_category,
    get_recipe_image_url
)

logger = logging.getLogger(__name__)

# 하위 호환성을 위한 별칭 (기존 코드에서 _로 시작하는 함수 사용)
_normalize_ingredient_name = normalize_ingredient_name
_parse_ingredient_quantity = parse_ingredient_quantity
_adjust_ingredient_quantity = adjust_ingredient_quantity
_categorize_ingredient = categorize_ingredient
_identify_main_ingredient = identify_main_ingredient
_classify_recipe_category = classify_recipe_category
_get_recipe_image_url = get_recipe_image_url
_extract_json_from_response = extract_json_from_response
_call_openai_api = call_openai_api


# 상수 및 헬퍼 함수는 위에서 import됨
# _normalize_ingredient_name은 위에서 alias로 이미 설정됨 (중복 정의 삭제됨)

def _suggest_substitutions_with_llm(ingredient: str, category: Optional[str]) -> List[Dict[str, Any]]:
    """LLM을 사용하여 재료 대체제 제안"""
    if not settings.OPENAI_API_KEY:
        return []
    
    try:
        category_text = category or "정보 없음"
        prompt = f"""다음 재료를 대신할 수 있는 한국 요리용 대체 재료를 JSON 형식으로 3개 이내로 제안해주세요.

부족한 재료: {ingredient}
재료 카테고리: {category_text}

각 제안에는 대체 재료 이름(ingredient), 간단한 이유(reason), 0~1 사이의 confidence 값을 포함해주세요.
응답은 다음 JSON 형식의 리스트만 반환하세요:
[
  {{"ingredient": "대체재", "reason": "설명", "confidence": 0.8}}
]
"""
        # OpenAI API 호출 (헤더 최소화로 헤더 불일치 문제 해결)
        messages = [
            {"role": "system", "content": "당신은 한국 요리 전문가입니다. 현실적이고 이용하기 쉬운 대체 재료를 제안하세요."},
            {"role": "user", "content": prompt}
        ]
        content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.5)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        data = json.loads(content)
        suggestions = []
        for entry in data:
            suggestions.append({
                "ingredient": entry.get("ingredient"),
                "reason": entry.get("reason", ""),
                "confidence": float(max(0.0, min(1.0, entry.get("confidence", 0.5)))),
                "source": "llm",
            })
        return suggestions
    except Exception as e:
        logger.error(f"LLM 대체재 제안 실패: {e}")
        return []



def check_ingredients(state: GraphState) -> Dict[str, Any]:
    """
    노드 8: 재료 확인 (Self-Correction Loop 지원)
    레시피에 필요한 재료와 보유 재료 비교, 매칭률 계산
    수량 정보는 무시하고 재료명만으로 매칭
    """
    selected_recipe = state.get("selected_recipe")
    user_ingredients = state.get("ingredients", [])
    correction_iteration = state.get("correction_iteration", 0)
    
    if not selected_recipe:
        return {"error": "선택된 레시피가 없습니다."}
    
    required_ingredients = selected_recipe.get("ingredients", [])
    
    # 매칭용 정규화 함수 (수량 제거)
    def normalize_for_matching(ingredient: str) -> str:
        """매칭용 정규화: 수량 제거 후 재료명만 추출"""
        if not ingredient:
            return ""
        # 수량 패턴 제거 (예: "200g", "1대", "2컵")
        name_only = re.sub(r'\s*\d+\.?\d*\s*[가-힣a-zA-Z]*\s*$', '', str(ingredient)).strip()
        name_only = re.sub(r'\s+\d+\.?\d*\s*[가-힣a-zA-Z]*\s*', ' ', name_only).strip()
        return name_only
    
    # 새로운 정규화 시스템 사용 (IngredientNormalizer)
    # 상위 개념과 하위 개념을 모두 고려한 유연한 매칭
    matched_ingredients = []
    missing_ingredients = []
    substitution_guidances = []  # 대체 재료 사용 시 가이드
    
    recipe_name = selected_recipe.get("name", "")
    
    for required_ing in required_ingredients:
        is_matched = False
        matched_user_ing = None
        
        # 수량 제거 후 재료명만 추출
        required_ing_name = normalize_for_matching(required_ing)
        
        # 요리 도구 제외 (식기류 필터링)
        from app.services.recipe_crawler import COOKING_TOOLS
        if any(tool in required_ing_name for tool in COOKING_TOOLS):
            logger.debug(f"요리 도구 제외: {required_ing_name}")
            continue
        
        # 물 제외 (한국에서는 항상 사용 가능)
        if required_ing_name in ["물", "water"]:
            logger.debug(f"물 제외 (항상 사용 가능): {required_ing_name}")
            continue
        
        # 1순위: 정확 일치 또는 표준화된 정규화 매칭
        for user_ing in user_ingredients:
            # 수량 제거 후 재료명만 추출
            user_ing_name = normalize_for_matching(user_ing)
            
            if IngredientNormalizer.can_substitute(user_ing_name, required_ing_name):
                is_matched = True
                matched_user_ing = user_ing
                # 가이드 메시지 확인
                guidance = IngredientNormalizer.get_substitution_guidance(user_ing_name, required_ing_name)
                if guidance:
                    substitution_guidances.append({
                        "user_ingredient": user_ing,
                        "required_ingredient": required_ing,
                        "guidance": guidance
                    })
                break
        
        # 2순위: LLM 기반 스마트 매칭 (정규화 매칭 실패 시)
        if not is_matched and settings.OPENAI_API_KEY:
            for user_ing in user_ingredients:
                user_ing_name = normalize_for_matching(user_ing)
                llm_result = check_ingredient_substitution_with_llm(
                    user_ingredient=user_ing_name,
                    required_ingredient=required_ing_name,
                    recipe_name=recipe_name,
                    api_key=settings.OPENAI_API_KEY
                )
                if llm_result.get("can_substitute", False):
                    is_matched = True
                    matched_user_ing = user_ing
                    substitution_guidances.append({
                        "user_ingredient": user_ing,
                        "required_ingredient": required_ing,
                        "guidance": llm_result.get("reason", "")
                    })
                    logger.info(f"LLM 매칭: '{user_ing_name}' -> '{required_ing_name}' (이유: {llm_result.get('reason', '')})")
                    break
        
        # 매칭 결과 분류
        if is_matched:
            matched_ingredients.append(required_ing)
        else:
            missing_ingredients.append(required_ing)
    
    # 매칭률 계산
    match_rate = len(matched_ingredients) / len(required_ingredients) if required_ingredients else 0.0
    
    # 지능형 매칭 점수 계산 (가중치 기반)
    matching_score = calculate_intelligent_matching_score(user_ingredients, required_ingredients)
    
    # 이전 매칭률 저장 (self-correction loop 개선용)
    previous_match_rate = state.get("match_rate", 0.0)
    
    logger.info(f"재료 매칭 완료: 매칭 {len(matched_ingredients)}/{len(required_ingredients)}, 매칭률 {match_rate:.1%}, 대체 가이드 {len(substitution_guidances)}개")
    
    return {
        "required_ingredients": required_ingredients,
        "matched_ingredients": matched_ingredients,
        "missing_ingredients": missing_ingredients,  # 대체 가능한 재료는 여기서 제외됨
        "match_rate": match_rate,
        "previous_match_rate": previous_match_rate,  # 이전 매칭률 저장
        "matching_score": matching_score,
        "correction_iteration": correction_iteration,
        "substitution_guidances": substitution_guidances if substitution_guidances else None  # 대체 가이드 추가
    }



def _is_valid_ingredient(ingredient: str) -> bool:
    """
    재료가 실제 재료인지 검증 (조리 방법/도구가 아닌지 확인)
    """
    if not ingredient or len(ingredient.strip()) < 2:
        return False
    
    ingredient_lower = ingredient.lower().strip()
    
    # 조리 방법 키워드 필터링
    cooking_methods = [
        '다지기', '볶기', '끓이기', '굽기', '튀기기', '찌기', '삶기', '데치기',
        '절이기', '무치기', '비빔', '볶음', '구이', '찜', '조림', '튀김',
        '손으로', '기계로', '가공기', '프로세서'
    ]
    
    # 조리 도구 키워드 필터링
    cooking_tools = [
        '도마', '조리용나이프', '요리나이프', '가위', '유리볼', '요리스푼',
        '냄비', '프라이팬', '팬', '볼', '그릇', '접시', '칼', '나이프',
        '에어프라이어', '오븐', '전자레인지', '믹서', '블렌더'
    ]
    
    # 동사 형태 필터링 (예: "손으로 다지기", "기계로 다지기")
    action_patterns = [
        r'.*다지기$', r'.*자르기$', r'.*썰기$', r'.*볶기$', r'.*끓이기$',
        r'.*굽기$', r'.*튀기기$', r'.*찌기$', r'.*삶기$', r'.*데치기$'
    ]
    
    # 조리 방법/도구 키워드가 포함되어 있으면 재료가 아님
    for method in cooking_methods:
        if method in ingredient_lower:
            return False
    
    for tool in cooking_tools:
        if tool in ingredient_lower:
            return False
    
    # 동사 패턴 매칭
    import re
    for pattern in action_patterns:
        if re.match(pattern, ingredient_lower):
            return False
    
    # 너무 짧거나 의미없는 텍스트 제외
    if len(ingredient_lower) < 2:
        return False
    
    return True


def suggest_substitutions(state: GraphState) -> Dict[str, Any]:
    """
    노드 9: 재료 대체 제안 (Self-Correction Loop 지원)
    부족한 재료에 대한 대체재 목록 생성 및 레시피 수정
    """
    missing_ingredients = state.get("missing_ingredients", [])
    matched_ingredients = state.get("matched_ingredients", [])
    user_ingredients = state.get("ingredients", [])
    ingredient_categories = state.get("ingredient_categories", {})
    selected_recipe = state.get("selected_recipe")
    correction_iteration = state.get("correction_iteration", 0)
    
    # 재료가 아닌 것들 필터링
    missing_ingredients = [ing for ing in missing_ingredients if _is_valid_ingredient(ing)]
    
    if not missing_ingredients:
        return {**state, "substitution_suggestions": []}
    
    # 매칭용 정규화 함수
    def normalize_for_matching(ingredient: str) -> str:
        """매칭용 정규화: 수량 제거 후 재료명만 추출"""
        if not ingredient:
            return ""
        name_only = re.sub(r'\s*\d+\.?\d*\s*[가-힣a-zA-Z]*\s*$', '', str(ingredient)).strip()
        name_only = re.sub(r'\s+\d+\.?\d*\s*[가-힣a-zA-Z]*\s*', ' ', name_only).strip()
        return name_only
    
    # 사용자가 이미 보유한 재료 목록 (정규화된 이름)
    user_ingredients_normalized = {normalize_for_matching(ing) for ing in user_ingredients}
    matched_ingredients_normalized = {normalize_for_matching(ing) for ing in matched_ingredients}
    
    suggestions: List[Dict[str, Any]] = []
    
    for missing in missing_ingredients:
        normalized = _normalize_ingredient_name(missing)
        category = ingredient_categories.get(normalized) or ingredient_categories.get(missing)
        
        rule_candidates = SUBSTITUTION_RULES.get(normalized) or SUBSTITUTION_RULES.get(missing)
        if not rule_candidates and category and category in CATEGORY_SUBSTITUTIONS:
            rule_candidates = CATEGORY_SUBSTITUTIONS[category]
        
        formatted_candidates: List[Dict[str, Any]] = []
        if rule_candidates:
            formatted_candidates = [
                {
                    "ingredient": candidate["ingredient"],
                    "reason": candidate.get("reason", ""),
                    "confidence": float(candidate.get("confidence", 0.5)),
                    "source": "rule",
                }
                for candidate in rule_candidates
            ]
        else:
            formatted_candidates = _suggest_substitutions_with_llm(normalized or missing, category)
        
        # 사용자가 이미 보유한 재료는 대체재에서 제외 + 재료가 아닌 것 필터링
        filtered_candidates = []
        for candidate in formatted_candidates:
            candidate_ingredient = candidate.get("ingredient", "")
            # 재료가 아닌 것 필터링
            if not _is_valid_ingredient(candidate_ingredient):
                continue
            
            candidate_name = normalize_for_matching(candidate_ingredient)
            # 사용자가 이미 보유한 재료이거나, 매칭된 재료와 동일하면 제외
            if candidate_name not in user_ingredients_normalized and candidate_name not in matched_ingredients_normalized:
                filtered_candidates.append(candidate)
        
        if filtered_candidates:
            suggestions.append({
                "missing": missing,
                "normalized": normalized or missing,
                "suggestions": filtered_candidates[:3],
            })
    
    # 대체재가 제안되면 레시피의 재료 목록을 업데이트 (Self-Correction)
    # **중요**: steps를 반드시 보존해야 함
    if suggestions and selected_recipe:
        updated_recipe = selected_recipe.copy()
        
        # 모든 필드를 명시적으로 보존
        original_steps = updated_recipe.get("steps", [])
        original_cooking_time = updated_recipe.get("cooking_time", 30)
        original_difficulty = updated_recipe.get("difficulty", "보통")
        original_name = updated_recipe.get("name", "레시피")
        original_image = updated_recipe.get("image", "")
        original_serving_size = updated_recipe.get("serving_size", 2)
        
        updated_ingredients = updated_recipe.get("ingredients", []).copy()
        
        # 가장 높은 confidence를 가진 대체재로 교체
        for sub in suggestions:
            missing = sub.get("missing")
            best_sub = max(sub.get("suggestions", []), key=lambda x: x.get("confidence", 0))
            substitute = best_sub.get("ingredient")
            
            # 재료 목록에서 부족한 재료를 대체재로 교체
            for i, ing in enumerate(updated_ingredients):
                if ing == missing or _normalize_ingredient_name(ing) == _normalize_ingredient_name(missing):
                    updated_ingredients[i] = substitute
                    break
        
        # 모든 필드를 보존하면서 재료만 업데이트
        updated_recipe["ingredients"] = updated_ingredients
        updated_recipe["steps"] = original_steps  # steps 반드시 보존
        updated_recipe["cooking_time"] = original_cooking_time
        updated_recipe["difficulty"] = original_difficulty
        updated_recipe["level"] = original_difficulty
        updated_recipe["name"] = original_name
        updated_recipe["image"] = original_image
        updated_recipe["serving_size"] = original_serving_size
        updated_recipe["substitutions_applied"] = True
        
        logger.info(f"suggest_substitutions: {len(original_steps)}개 steps 보존")
        
        return {
            **state,
            "substitution_suggestions": suggestions,
            "selected_recipe": updated_recipe,
            "correction_iteration": correction_iteration + 1
        }
    
    return {**state, "substitution_suggestions": suggestions, "correction_iteration": correction_iteration + 1}



def web_search_substitutions(state: GraphState) -> Dict[str, Any]:
    """
    Phase 2: 재료 부족 시 웹 검색
    Tavily로 대체재 검색 및 정보 수집
    """
    missing_ingredients = state.get("missing_ingredients", [])
    
    # 재료가 아닌 것들 필터링
    missing_ingredients = [ing for ing in missing_ingredients if _is_valid_ingredient(ing)]
    
    if not missing_ingredients or not settings.TAVILY_API_KEY:
        return {**state, "substitution_suggestions": []}
    
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        
        substitution_suggestions = []
        
        for missing in missing_ingredients[:3]:  # 최대 3개만 검색
            query = f"{missing} 대체재 대신 사용할 수 있는 재료 한국 요리"
            
            try:
                response = client.search(
                    query=query,
                    search_depth="basic",
                    max_results=5,
                    include_answer=True
                )
                
                results = response.get("results", [])
                if results and settings.OPENAI_API_KEY:
                    # LLM으로 검색 결과 분석
                    suggestions = _parse_substitution_search_with_llm(results, missing)
                    # 재료가 아닌 것 필터링
                    filtered_suggestions = [s for s in suggestions if _is_valid_ingredient(s.get("ingredient", ""))]
                    if filtered_suggestions:
                        substitution_suggestions.append({
                            "missing": missing,
                            "normalized": _normalize_ingredient_name(missing),
                            "suggestions": filtered_suggestions,
                            "source": "tavily"
                        })
            except Exception as e:
                logger.error(f"Tavily 대체재 검색 실패 ({missing}): {e}")
                continue
        
        logger.info(f"웹 검색으로 {len(substitution_suggestions)}개 대체재 제안 완료")
        return {**state, "substitution_suggestions": substitution_suggestions}
        
    except ImportError:
        logger.warning("tavily-python 패키지가 설치되지 않았습니다.")
        return {**state, "substitution_suggestions": []}
    except Exception as e:
        logger.error(f"웹 검색 대체재 오류: {e}")
        return {**state, "substitution_suggestions": []}



def _parse_substitution_search_with_llm(search_results: List[Dict], missing_ingredient: str) -> List[Dict[str, Any]]:
    """LLM을 사용하여 대체재 검색 결과 파싱"""
    if not settings.OPENAI_API_KEY:
        return []
    
    try:
        results_summary = []
        for result in search_results[:3]:
            title = result.get("title", "")
            content = result.get("content", "")[:300]
            results_summary.append(f"{title}\n{content}")
        
        results_text = "\n\n".join(results_summary)
        
        prompt = f"""다음은 "{missing_ingredient}"의 대체재에 대한 웹 검색 결과입니다.
        
검색 결과:
{results_text}

이 결과에서 "{missing_ingredient}"를 대신할 수 있는 한국 요리용 재료를 3개 이내로 추출해주세요.
각 제안에는 재료 이름(ingredient), 간단한 이유(reason), 0~1 사이의 confidence 값을 포함해주세요.

응답은 다음 JSON 형식의 리스트만 반환하세요:
[
  {{"ingredient": "대체재", "reason": "설명", "confidence": 0.8}}
]

JSON만 응답하고 다른 설명은 하지 마세요."""
        
        # OpenAI API 호출 (헤더 최소화로 헤더 불일치 문제 해결)
        messages = [
            {"role": "system", "content": "당신은 한국 요리 전문가입니다. 웹 검색 결과에서 현실적이고 이용하기 쉬운 대체 재료를 추출합니다."},
            {"role": "user", "content": prompt}
        ]
        content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.5)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        data = json.loads(content)
        suggestions = []
        for entry in data:
            ingredient = entry.get("ingredient", "")
            # 재료가 아닌 것 필터링
            if not _is_valid_ingredient(ingredient):
                continue
            suggestions.append({
                "ingredient": ingredient,
                "reason": entry.get("reason", ""),
                "confidence": float(max(0.0, min(1.0, entry.get("confidence", 0.5)))),
                "source": "tavily_llm",
            })
        return suggestions
    except Exception as e:
        logger.error(f"LLM 대체재 파싱 오류: {e}")
        return []



def modify_recipe_with_substitutions(state: GraphState) -> Dict[str, Any]:
    """
    Phase 2: 대체재로 레시피 수정
    대체재로 재료 교체, 수량 재계산, 조리법 조정
    **중요**: steps를 반드시 보존해야 함
    """
    selected_recipe = state.get("selected_recipe")
    substitution_suggestions = state.get("substitution_suggestions", [])
    
    if not selected_recipe or not substitution_suggestions:
        return state
    
    # 레시피의 모든 필드를 보존하면서 수정
    updated_recipe = selected_recipe.copy()
    
    # steps를 명시적으로 보존
    original_steps = updated_recipe.get("steps", [])
    original_cooking_time = updated_recipe.get("cooking_time", 30)
    original_difficulty = updated_recipe.get("difficulty", "보통")
    original_name = updated_recipe.get("name", "레시피")
    original_image = updated_recipe.get("image", "")
    original_serving_size = updated_recipe.get("serving_size", 2)
    
    updated_ingredients = updated_recipe.get("ingredients", []).copy()
    applied_substitutions = {}
    
    # 가장 높은 confidence를 가진 대체재로 교체
    for sub in substitution_suggestions:
        missing = sub.get("missing")
        suggestions = sub.get("suggestions", [])
        if suggestions:
            best_sub = max(suggestions, key=lambda x: x.get("confidence", 0))
            substitute = best_sub.get("ingredient")
            applied_substitutions[missing] = substitute
            
            # 재료 목록에서 부족한 재료를 대체재로 교체
            for i, ing in enumerate(updated_ingredients):
                if ing == missing or _normalize_ingredient_name(ing) == _normalize_ingredient_name(missing):
                    updated_ingredients[i] = substitute
                    break
    
    # 모든 필드를 보존하면서 재료만 업데이트
    updated_recipe["ingredients"] = updated_ingredients
    updated_recipe["steps"] = original_steps  # steps 반드시 보존
    updated_recipe["cooking_time"] = original_cooking_time
    updated_recipe["difficulty"] = original_difficulty
    updated_recipe["level"] = original_difficulty
    updated_recipe["name"] = original_name
    updated_recipe["image"] = original_image
    updated_recipe["serving_size"] = original_serving_size
    updated_recipe["substitutions_applied"] = True
    updated_recipe["applied_substitutions"] = applied_substitutions
    
    logger.info(f"레시피 수정 완료: {len(applied_substitutions)}개 재료 대체, steps 보존: {len(original_steps)}개")
    
    return {
        **state,
        "selected_recipe": updated_recipe,
        "correction_iteration": state.get("correction_iteration", 0) + 1
    }


# ==================== 초보자 모드 Phase 2 노드 ====================

def wait_for_ingredient_selection(state: GraphState) -> Dict[str, Any]:
    """
    Phase 2: Human-in-the-Loop - 재료 선택 대기 노드 (초보자 모드)
    
    상태: 그래프 중단 (interrupt) 후 재개
    동작: 사용자가 없는 재료 체크 완료까지 대기
    입력: 사용자가 체크한 재료 리스트 (user_selected_ingredients = 없는 재료)
    재개: update 호출로 다음 단계 진행
    """
    user_selected_ingredients = state.get("user_selected_ingredients", [])
    
    if user_selected_ingredients is None:
        # 아직 사용자 입력이 없으면 interrupt 상태 유지
        return {
            **state,
            "waiting_for_user_selection": True,
            "interrupt_reason": "waiting_for_ingredient_selection"
        }
    
    # 체크된 재료 = 없는 재료 (missing_ingredients)로 설정
    missing_ingredients = user_selected_ingredients
    
    logger.info(f"재료 선택 완료: {len(missing_ingredients)}개 없는 재료 선택됨")
    
    # interrupt 해제 및 다음 단계로 진행
    return {
        **state,
        "missing_ingredients": missing_ingredients,
        "user_selected_ingredients": [],  # 빈 리스트로 설정 (보유 재료는 계산으로 처리)
        "waiting_for_user_selection": False,
        "interrupt_reason": None
    }


# ==================== 재료 관리 지능화 노드 ====================

