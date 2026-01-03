"""
Phase 4: phase4 노드 함수들
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

def _parse_ingredient_quantity(ingredient: str) -> Tuple[str, Optional[float], Optional[str]]:
    """
    재료 문자열에서 이름과 수량을 파싱
    예: "돼지고기 200g" -> ("돼지고기", 200.0, "g")
    예: "대파 1대" -> ("대파", 1.0, "대")
    예: "돼지고기" -> ("돼지고기", None, None)
    
    Returns:
        (재료명, 수량값, 단위)
    """
    if not ingredient:
        return ("", None, None)
    
    # 숫자와 단위 패턴 찾기 (예: "200g", "1대", "2컵", "300ml")
    quantity_pattern = r'(\d+\.?\d*)\s*([가-힣a-zA-Z]+)'
    match = re.search(quantity_pattern, ingredient)
    
    if match:
        quantity_value = float(match.group(1))
        unit = match.group(2)
        # 재료명 추출 (수량 부분 제거)
        name = re.sub(quantity_pattern, '', ingredient).strip()
        # 앞뒤 공백 정리
        name = ' '.join(name.split())
        return (name, quantity_value, unit)
    else:
        # 수량이 없으면 전체를 재료명으로
        return (ingredient.strip(), None, None)



def _adjust_ingredient_quantity(ingredient: str, original_servings: int, target_servings: int) -> str:
    """
    인분 수에 맞게 재료 수량 조정
    예: "돼지고기 200g", 2인분 -> 4인분 -> "돼지고기 400g"
    예: "대파 1대", 2인분 -> 3인분 -> "대파 1.5대"
    
    Args:
        ingredient: 재료 문자열 (예: "돼지고기 200g")
        original_servings: 원본 인분 수
        target_servings: 목표 인분 수
    
    Returns:
        조정된 재료 문자열
    """
    if original_servings <= 0 or target_servings <= 0:
        return ingredient
    
    if original_servings == target_servings:
        return ingredient
    
    name, quantity, unit = _parse_ingredient_quantity(ingredient)
    
    if quantity is None or unit is None:
        # 수량 정보가 없으면 그대로 반환
        return ingredient
    
    # 비례 계산
    ratio = target_servings / original_servings
    adjusted_quantity = quantity * ratio
    
    # 소수점 처리 (0.5 단위로 반올림)
    if adjusted_quantity < 1:
        adjusted_quantity = round(adjusted_quantity, 1)
    else:
        adjusted_quantity = round(adjusted_quantity)
    
    # 단위별 소수점 표시 여부 결정
    if unit in ["대", "개", "장", "줄기", "송이"]:
        # 개수 단위는 소수점 표시
        if adjusted_quantity == int(adjusted_quantity):
            return f"{name} {int(adjusted_quantity)}{unit}"
        else:
            return f"{name} {adjusted_quantity}{unit}"
    else:
        # 무게/부피 단위는 소수점 표시
        if adjusted_quantity == int(adjusted_quantity):
            return f"{name} {int(adjusted_quantity)}{unit}"
        else:
            return f"{name} {adjusted_quantity}{unit}"



def generate_shopping_list(state: GraphState) -> Dict[str, Any]:
    """
    노드 10: 쇼핑 리스트 생성
    부족한 재료를 쇼핑 리스트로 정리 (레시피의 수량 정보 포함)
    """
    missing_ingredients = state.get("missing_ingredients", [])
    ingredient_categories = state.get("ingredient_categories", {})
    selected_recipe = state.get("selected_recipe", {})
    recipe_ingredients = selected_recipe.get("ingredients", [])
    
    # 매칭용 정규화 함수 (수량 제거)
    def normalize_for_matching(ingredient: str) -> str:
        """매칭용 정규화: 수량 제거 후 재료명만 추출"""
        if not ingredient:
            return ""
        name_only = re.sub(r'\s*\d+\.?\d*\s*[가-힣a-zA-Z]*\s*$', '', str(ingredient)).strip()
        name_only = re.sub(r'\s+\d+\.?\d*\s*[가-힣a-zA-Z]*\s*', ' ', name_only).strip()
        return name_only
    
    # 요리 도구 제외
    from app.services.recipe_crawler import COOKING_TOOLS
    filtered_missing = [
        ing for ing in missing_ingredients 
        if not any(tool in normalize_for_matching(ing) for tool in COOKING_TOOLS)
    ]
    
    shopping_list = []
    for missing in filtered_missing:
        # 레시피에서 해당 재료의 수량 정보 찾기
        missing_name = normalize_for_matching(missing)
        recipe_ing = None
        
        for ing in recipe_ingredients:
            ing_name = normalize_for_matching(ing)
            if IngredientNormalizer.can_substitute(ing_name, missing_name):
                recipe_ing = ing
                break
        
        # 수량 정보 추출
        if recipe_ing:
            # 수량이 포함된 문자열에서 수량 부분 추출
            quantity_match = re.search(r'(\d+\.?\d*)\s*([가-힣a-zA-Z]+)', recipe_ing)
            if quantity_match:
                quantity_value = quantity_match.group(1)
                unit = quantity_match.group(2)
                display = f"{missing_name} {quantity_value}{unit}"
                quantity = f"{quantity_value}{unit}"
            else:
                display = missing
                quantity = None
        else:
            display = missing
            quantity = None
        
        shopping_list.append({
            "ingredient": missing,  # 매칭용 이름
            "display": display,  # 표시용 (수량 포함)
            "category": ingredient_categories.get(missing, "기타"),
            "quantity": quantity  # 수량 정보
        })
    
    # 카테고리별 그룹화
    shopping_list.sort(key=lambda x: x["category"])
    
    return {"shopping_list": shopping_list}



def generate_output(state: GraphState) -> Dict[str, Any]:
    """
    노드 11: 최종 결과 생성
    모든 정보를 통합하여 최종 출력 생성
    """
    selected_recipe = state.get("selected_recipe")
    
    if not selected_recipe:
        logger.error("generate_output: selected_recipe가 없습니다.")
        return {"error": "선택된 레시피가 없습니다."}
    
    nutrition_info = state.get("nutrition_info")
    optimized_steps = state.get("optimized_steps")
    shopping_list = state.get("shopping_list")
    substitutions = state.get("substitution_suggestions")
    substitution_guidances = state.get("substitution_guidances")  # 대체 재료 가이드
    serving_size = state.get("serving_size")
    
    # selected_recipe에 image 필드가 있는지 확인하고 포함
    recipe_data = selected_recipe.copy()
    if "image" not in recipe_data:
        recipe_data["image"] = ""
    
    # optimized_steps가 없으면 원본 steps 사용
    if not optimized_steps:
        original_steps = selected_recipe.get("steps", [])
        if original_steps:
            # 원본 steps를 optimized_steps 형식으로 변환
            optimized_steps = [
                {
                    "step": i + 1,
                    "description": step if isinstance(step, str) else step.get("description", str(step)),
                    "time": max(3, selected_recipe.get("cooking_time", 30) // len(original_steps))
                }
                for i, step in enumerate(original_steps)
            ]
            logger.info(f"optimized_steps가 없어서 원본 steps {len(original_steps)}개를 사용")
        else:
            logger.warning("원본 steps도 없습니다. 기본 steps 생성")
            optimized_steps = [
                {"step": 1, "description": "재료를 준비합니다.", "time": 5},
                {"step": 2, "description": "조리합니다.", "time": 10},
                {"step": 3, "description": "완성합니다.", "time": 5}
            ]
    
    # 인분 수 조정 (항상 1인분으로 고정)
    original_servings = recipe_data.get("serving_size", 2)  # 레시피 원본 인분수
    target_servings = 1  # 항상 1인분으로 고정
    
    if target_servings != original_servings and target_servings > 0:
        # 재료 수량 조정
        adjusted_ingredients = [
            _adjust_ingredient_quantity(ing, original_servings, target_servings)
            for ing in recipe_data.get("ingredients", [])
        ]
        recipe_data["ingredients"] = adjusted_ingredients
        logger.info(f"인분 수 조정: {original_servings}인분 -> {target_servings}인분 (표시 제거)")
    
    # serving_size 필드 제거 (표시하지 않음, 항상 1인분 기준)
    if "serving_size" in recipe_data:
        del recipe_data["serving_size"]
    
    # 재료 보관 팁 포함
    storage_tips = state.get("storage_tips")
    
    # Explainability 관련 정보
    selection_reasoning = state.get("selection_reasoning")
    rejection_reasons = state.get("rejection_reasons")
    research_hypothesis = state.get("research_hypothesis")
    alternative_analysis = state.get("alternative_analysis")
    
    # Confidence Score
    confidence_score = state.get("confidence_score", 0.0)
    confidence_breakdown = state.get("confidence_breakdown")
    confidence_warning = None
    if confidence_score < 0.6:
        confidence_warning = f"이 레시피의 신뢰도가 낮습니다 ({confidence_score:.1%}). 재료 매칭이나 레시피 품질을 확인해주세요."
    elif confidence_score < 0.8:
        confidence_warning = f"이 레시피의 신뢰도가 보통입니다 ({confidence_score:.1%}). 추가 확인을 권장합니다."
    
    final_output = {
        "recipe": recipe_data,
        "nutrition": nutrition_info,
        "cooking_steps": optimized_steps,  # 반드시 steps 포함
        "shopping_list": shopping_list if shopping_list else None,
        "substitutions": substitutions if substitutions else None,
        "substitution_guidances": substitution_guidances if substitution_guidances else None,  # 대체 재료 가이드 추가
        "storage_tips": storage_tips if storage_tips else None,  # 재료 보관 팁 추가
        # Explainability 정보 추가
        "selection_reasoning": selection_reasoning,
        "rejection_reasons": rejection_reasons,
        "research_hypothesis": research_hypothesis,
        "alternative_analysis": alternative_analysis,
        # Confidence Score 추가
        "confidence_score": confidence_score,
        "confidence_breakdown": confidence_breakdown,
        "confidence_warning": confidence_warning,
    }
    
    logger.info(f"최종 출력 생성 완료: {recipe_data.get('name', 'Unknown')}, steps: {len(optimized_steps)}개, 신뢰도: {confidence_score:.1%}")
    return {"final_output": final_output}


# ==================== Deep Research 노드들 ====================


def generate_storage_tips(state: GraphState) -> Dict[str, Any]:
    """
    재료 관리 지능화 노드
    보관 팁 및 활용 팁 제공 (LLM 호출 최소화를 위해 스킵)
    """
    # LLM 호출 최소화: 빈 배열 반환
    return {**state, "storage_tips": []}



def calculate_confidence_score(state: GraphState) -> Dict[str, Any]:
    """
    Confidence Score 계산 노드
    nutrition, quality, matching 점수를 종합하여 최종 신뢰도 계산
    """
    match_rate = state.get("match_rate", 0.0)
    matching_score = state.get("matching_score", 0.0)
    quality_score = state.get("quality_score", 0.0)
    nutrition_info = state.get("nutrition_info")
    
    # 세부 점수 계산 (0.0 ~ 1.0)
    breakdown = {}
    
    # 1. 매칭률 점수 (가중치: 0.4)
    match_rate_score = float(match_rate) if match_rate else 0.0
    breakdown["match_rate"] = match_rate_score
    
    # 2. 지능형 매칭 점수 (가중치: 0.3) - 0-100 스케일을 0-1로 변환
    matching_score_normalized = (matching_score / 100.0) if matching_score else 0.0
    breakdown["matching_score"] = matching_score_normalized
    
    # 3. 품질 점수 (가중치: 0.3)
    quality_score_normalized = float(quality_score) if quality_score else 0.5
    breakdown["quality_score"] = quality_score_normalized
    
    # 영양 정보 유무 보너스 (+0.1)
    nutrition_bonus = 0.1 if nutrition_info else 0.0
    breakdown["nutrition_bonus"] = nutrition_bonus
    
    # 최종 신뢰도 계산 (가중 평균)
    confidence_score = (
        breakdown["match_rate"] * 0.4 +
        breakdown["matching_score"] * 0.3 +
        breakdown["quality_score"] * 0.3 +
        nutrition_bonus
    )
    
    # 0.0 ~ 1.0 범위로 클리핑
    confidence_score = max(0.0, min(1.0, confidence_score))
    
    logger.info(f"신뢰도 계산: 최종={confidence_score:.2f}, 세부={breakdown}")
    
    return {
        **state,
        "confidence_score": confidence_score,
        "confidence_breakdown": breakdown
    }



def collect_user_feedback(state: GraphState) -> Dict[str, Any]:
    """
    Human-in-the-loop Feedback 수집 노드
    generate_output 이후에 실행 (실제 피드백 수집 로직은 TODO)
    """
    # TODO: 실제 사용자 피드백 수집 로직 구현
    # - API 엔드포인트에서 피드백 데이터 수신
    # - 다음 추천 시 가중치 조정에 활용
    
    # 현재는 상태만 초기화
    user_feedback = None
    feedback_score = None
    
    logger.info("사용자 피드백 수집 노드 실행 (TODO: 실제 수집 로직 구현)")
    
    return {
        **state,
        "user_feedback": user_feedback,
        "feedback_score": feedback_score
    }



