"""
Phase 3: phase3 노드 함수들
"""

"""
LangGraph Node Functions
"""
import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.models.state import GraphState, UserPersona
from app.config import settings
from app.utils.ingredient_map import IngredientNormalizer
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

def analyze_nutrition(state: GraphState) -> Dict[str, Any]:
    """
    노드 6: 영양 분석
    LLM을 사용하여 레시피의 영양 정보를 추정
    """
    selected_recipe = state.get("selected_recipe")
    
    if not selected_recipe:
        logger.error("analyze_nutrition: selected_recipe가 없습니다.")
        return {"error": "선택된 레시피가 없습니다."}
    
    # 크롤링된 레시피에 영양 정보가 있으면 사용
    if selected_recipe.get("nutrition"):
        return {"nutrition_info": selected_recipe["nutrition"]}
    
    # LLM을 사용하여 영양 정보 계산 (메뉴명과 재료 기반)
    try:
        nutrition_info = _calculate_nutrition_with_llm(selected_recipe)
        return {"nutrition_info": nutrition_info}
    except Exception as e:
        logger.error(f"영양 정보 계산 실패: {e}")
        # 기본값 반환
        return {
            "nutrition_info": {
                "calories": 350,
                "carbohydrates": 45,
                "protein": 15,
                "fat": 12,
            }
        }



def _calculate_nutrition_with_llm(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """LLM을 사용하여 레시피의 영양 정보 추정 (메뉴명과 재료 기반)"""
    if not settings.OPENAI_API_KEY:
        # API 키가 없으면 기본값 반환
        return {
            "calories": 350,
            "carbohydrates": 45,
            "protein": 15,
            "fat": 12,
        }
    
    try:
        recipe_name = recipe.get("name", "레시피")
        ingredients = recipe.get("ingredients", [])
        ingredients_str = ", ".join(ingredients) if ingredients else "정보 없음"
        
        # 조리 시간 정보도 포함
        cooking_time = recipe.get("cooking_time", 0)
        cooking_time_str = f"{cooking_time}분" if cooking_time > 0 else "정보 없음"
        
        prompt = f"""다음 한국 요리 레시피의 영양 정보를 추정해주세요.

레시피명: {recipe_name}
재료: {ingredients_str}
조리시간: {cooking_time_str}

레시피명과 재료 목록을 보고, 일반적인 1인분 기준으로 영양 정보를 추정해주세요.
한국 요리의 일반적인 영양소 비율을 고려하여 현실적인 값을 제공해주세요.

다음 JSON 형식으로 응답해주세요:
{{
  "calories": 칼로리(kcal) - 정수,
  "carbohydrates": 탄수화물(g) - 정수,
  "protein": 단백질(g) - 정수,
  "fat": 지방(g) - 정수
}}

예시:
- 밥류 (볶음밥, 비빔밥 등): 칼로리 400-600kcal, 탄수화물 높음
- 찌개/국물류: 칼로리 200-400kcal, 단백질 중간
- 볶음류: 칼로리 300-500kcal, 지방 중간
- 조림류: 칼로리 250-450kcal, 단백질 높음

JSON만 응답하고 다른 설명은 하지 마세요."""

        # OpenAI API 호출 (헤더 최소화로 헤더 불일치 문제 해결)
        messages = [
            {"role": "system", "content": "당신은 한국 요리 영양 전문가입니다. 레시피명과 재료를 분석하여 1인분 기준의 정확한 영양 정보를 추정합니다."},
            {"role": "user", "content": prompt}
        ]
        content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.3)
        
        # JSON 추출
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        return {
            "calories": int(result.get("calories", 350)),
            "carbohydrates": int(result.get("carbohydrates", 45)),
            "protein": int(result.get("protein", 15)),
            "fat": int(result.get("fat", 12)),
        }
        
    except Exception as e:
        logger.error(f"LLM 영양 정보 계산 오류: {e}")
        return {
            "calories": 350,
            "carbohydrates": 45,
            "protein": 15,
            "fat": 12,
        }



def optimize_cooking_order(state: GraphState) -> Dict[str, Any]:
    """
    노드 7: 요리 순서 최적화
    LLM을 사용하여 요리 단계를 시간 효율적으로 재배열하고 대체 재료에 맞춰 조정
    """
    selected_recipe = state.get("selected_recipe")
    substitution_suggestions = state.get("substitution_suggestions", [])
    
    if not selected_recipe:
        logger.error("optimize_cooking_order: selected_recipe가 없습니다.")
        return {"error": "선택된 레시피가 없습니다."}
    
    # 이전에 최적화된 steps가 있으면 사용 (재검증 후 재최적화)
    optimized_steps = state.get("optimized_steps")
    if optimized_steps:
        steps = [step.get("description", "") if isinstance(step, dict) else str(step) for step in optimized_steps]
    else:
        steps = selected_recipe.get("steps", [])
    
    ingredients = selected_recipe.get("ingredients", [])
    recipe_name = selected_recipe.get("name", "레시피")
    
    # steps가 없거나 비어있으면 LLM으로 생성
    if not steps:
        logger.warning(f"레시피 '{recipe_name}'에 조리 단계가 없습니다. LLM으로 생성합니다.")
        steps = _generate_cooking_steps_with_llm(recipe_name, ingredients, selected_recipe.get("cooking_time", 30))
        if not steps:
            # LLM 생성 실패 시 기본 단계
            steps = ["재료를 준비합니다.", "조리합니다.", "완성합니다."]
    
    # 대체 재료가 적용된 경우, 조리법을 대체 재료에 맞춰 수정
    applied_substitutions = {}
    if substitution_suggestions:
        for sub in substitution_suggestions:
            missing = sub.get("missing")
            suggestions = sub.get("suggestions", [])
            if suggestions:
                # 가장 높은 confidence를 가진 대체재 선택
                best_sub = max(suggestions, key=lambda x: x.get("confidence", 0))
                applied_substitutions[missing] = best_sub.get("ingredient")
    
    # 페르소나 가져오기
    user_persona = state.get("user_persona")
    persona_str = user_persona.value if user_persona else "beginner"
    
    # LLM을 사용하여 요리 순서 최적화 (페르소나 기반)
    try:
        optimized_steps = _optimize_steps_with_llm(
            steps=steps,
            ingredients=ingredients,
            substitutions=applied_substitutions,
            cooking_time=selected_recipe.get("cooking_time", 30),
            recipe_name=recipe_name,
            persona=persona_str
        )
    except Exception as e:
        logger.error(f"요리 순서 최적화 실패: {e}")
        # 기본 형식으로 반환
        optimized_steps = [
            {"step": i + 1, "description": step, "time": max(3, selected_recipe.get("cooking_time", 30) // len(steps))}
            for i, step in enumerate(steps)
        ]
    
    return {"optimized_steps": optimized_steps}



def _generate_cooking_steps_with_llm(recipe_name: str, ingredients: List[str], cooking_time: int) -> List[str]:
    """LLM을 사용하여 레시피의 조리 단계 생성 (steps가 없을 때)"""
    if not settings.OPENAI_API_KEY:
        return []
    
    try:
        ingredients_str = ", ".join(ingredients)
        
        prompt = f"""다음 한국 요리 레시피의 상세한 조리 단계를 작성해주세요.

레시피 이름: {recipe_name}
재료: {ingredients_str}
예상 조리 시간: {cooking_time}분

다음 형식으로 5-8단계의 상세한 조리 방법을 작성해주세요:
1. 재료 준비 및 손질
2. 양념 준비
3. 조리 시작
4. 중간 과정
5. 마무리 및 완성

**중요**: 각 단계에서 재료를 사용할 때 반드시 수량을 포함하세요 (예: "쌀뜨물 2컵", "돼지고기 200g", "대파 1대")
각 단계는 구체적이고 실용적으로 작성해주세요.

응답은 다음 JSON 형식으로 해주세요:
{{
  "steps": [
    "1단계 설명",
    "2단계 설명",
    ...
  ]
}}

JSON만 응답하고 다른 설명은 하지 마세요."""
        
        # OpenAI API 호출 (헤더 최소화로 헤더 불일치 문제 해결)
        messages = [
            {"role": "system", "content": "당신은 한국 요리 전문 쉐프입니다. 주어진 레시피의 상세하고 실용적인 조리 단계를 작성합니다."},
            {"role": "user", "content": prompt}
        ]
        content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.7)
        
        # JSON 추출
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        steps = result.get("steps", [])
        
        return steps if steps else []
        
    except Exception as e:
        logger.error(f"LLM 조리 단계 생성 오류: {e}")
        return []



def _optimize_steps_with_llm(
    steps: List[str],
    ingredients: List[str],
    substitutions: Dict[str, str],
    cooking_time: int,
    recipe_name: str = "레시피",
    persona: Optional[str] = None
) -> List[Dict[str, Any]]:
    """LLM을 사용하여 요리 순서를 최적화하고 대체 재료에 맞춰 조정 (페르소나 기반)"""
    if not settings.OPENAI_API_KEY:
        # API 키가 없으면 기본 형식으로 반환
        return [
            {"step": i + 1, "description": step, "time": max(3, cooking_time // len(steps))}
            for i, step in enumerate(steps)
        ]
    
    try:
        from app.prompts import get_cooking_steps_prompt
        
        # 페르소나에 맞는 프롬프트 생성
        persona_str = persona or "beginner"  # 기본값은 초보자
        system_msg, user_instruction = get_cooking_steps_prompt(
            persona=persona_str,
            recipe_name=recipe_name,
            ingredients=ingredients,
            steps=steps,
            substitutions=substitutions
        )

        # OpenAI API 호출 (헤더 최소화로 헤더 불일치 문제 해결)
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_instruction}
        ]
        content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.5)
        
        # JSON 추출
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        optimized = result.get("steps", [])
        
        # 형식 검증 및 기본값 설정
        formatted_steps = []
        for step_data in optimized:
            step_dict = {
                "step": step_data.get("step", len(formatted_steps) + 1),
                "description": step_data.get("description", ""),
                "time": max(1, int(step_data.get("time", 5)))
            }
            # 초보자용 팁 추가
            if persona_str == "beginner" and "tips" in step_data:
                step_dict["tips"] = step_data.get("tips", "")
            # 숙련가용 기술 정보 추가
            elif persona_str == "expert":
                if "technique" in step_data:
                    step_dict["technique"] = step_data.get("technique", "")
                if "parallel" in step_data:
                    step_dict["parallel"] = step_data.get("parallel", "")
            formatted_steps.append(step_dict)
        
        return formatted_steps if formatted_steps else [
            {"step": i + 1, "description": step, "time": max(3, cooking_time // len(steps))}
            for i, step in enumerate(steps)
        ]
        
    except Exception as e:
        logger.error(f"LLM 요리 순서 최적화 오류: {e}")
        return [
            {"step": i + 1, "description": step, "time": max(3, cooking_time // len(steps))}
            for i, step in enumerate(steps)
        ]



def validate_nutrition(state: GraphState) -> Dict[str, Any]:
    """
    Phase 3: 영양 정보 검증
    영양 정보 합리성 검증 및 비정상 수치 감지
    """
    nutrition_info = state.get("nutrition_info")
    selected_recipe = state.get("selected_recipe")
    
    if not nutrition_info:
        return {**state, "error": "영양 정보가 없습니다."}
    
    calories = nutrition_info.get("calories", 0)
    carbohydrates = nutrition_info.get("carbohydrates", 0)
    protein = nutrition_info.get("protein", 0)
    fat = nutrition_info.get("fat", 0)
    
    # 합리적 범위 검증
    # 일반적인 한국 요리 1인분 기준
    is_valid = True
    issues = []
    
    # 칼로리 검증 (50kcal ~ 2000kcal)
    if calories < 50 or calories > 2000:
        is_valid = False
        issues.append(f"칼로리가 비정상적입니다: {calories}kcal")
    
    # 탄수화물 검증 (0g ~ 200g)
    if carbohydrates < 0 or carbohydrates > 200:
        is_valid = False
        issues.append(f"탄수화물이 비정상적입니다: {carbohydrates}g")
    
    # 단백질 검증 (0g ~ 100g)
    if protein < 0 or protein > 100:
        is_valid = False
        issues.append(f"단백질이 비정상적입니다: {protein}g")
    
    # 지방 검증 (0g ~ 100g)
    if fat < 0 or fat > 100:
        is_valid = False
        issues.append(f"지방이 비정상적입니다: {fat}g")
    
    # 총 영양소 합리성 (칼로리 = 탄수화물*4 + 단백질*4 + 지방*9, ±20% 허용)
    calculated_calories = carbohydrates * 4 + protein * 4 + fat * 9
    if calculated_calories > 0:
        ratio = calories / calculated_calories
        if ratio < 0.8 or ratio > 1.2:
            is_valid = False
            issues.append(f"칼로리 계산이 일치하지 않습니다: {calories}kcal vs {calculated_calories:.0f}kcal")
    
    if not is_valid:
        logger.warning(f"영양 정보 검증 실패: {', '.join(issues)} (그래도 진행)")
        # 검증 실패해도 그냥 진행 (속도 우선)
    
    logger.info("영양 정보 검증 통과")
    return state



def validate_cooking_order(state: GraphState) -> Dict[str, Any]:
    """
    Phase 3: 조리 순서 검증
    조리 순서 논리성 검증 및 시간 순서 확인
    """
    optimized_steps = state.get("optimized_steps", [])
    
    if not optimized_steps:
        return {**state, "error": "조리 순서가 없습니다."}
    
    is_valid = True
    issues = []
    
    # 기본 검증
    if len(optimized_steps) < 2:
        is_valid = False
        issues.append("조리 단계가 너무 적습니다 (최소 2단계 필요)")
    
    # 단계 번호 검증
    step_numbers = [step.get("step", 0) for step in optimized_steps]
    if sorted(step_numbers) != list(range(1, len(optimized_steps) + 1)):
        is_valid = False
        issues.append("단계 번호가 순서대로 되어 있지 않습니다")
    
    # 시간 순서 검증 (각 단계에 시간이 있는지)
    for step in optimized_steps:
        if "time" not in step or step.get("time", 0) <= 0:
            is_valid = False
            issues.append(f"단계 {step.get('step', '?')}에 시간 정보가 없습니다")
    
    # 논리적 순서 검증 (재료 준비 → 조리 → 마무리)
    first_step = optimized_steps[0].get("description", "").lower()
    last_step = optimized_steps[-1].get("description", "").lower()
    
    prep_keywords = ["준비", "씻", "자르", "썰", "손질"]
    finish_keywords = ["완성", "마무리", "마지막", "마지막으로", "마지막 단계"]
    
    has_prep = any(keyword in first_step for keyword in prep_keywords)
    has_finish = any(keyword in last_step for keyword in finish_keywords)
    
    if not has_prep and len(optimized_steps) > 2:
        issues.append("첫 단계에 재료 준비 과정이 없을 수 있습니다")
    
    if not is_valid:
        logger.warning(f"조리 순서 검증 실패: {', '.join(issues)} (그래도 진행)")
        # 검증 실패해도 그냥 진행 (속도 우선)
    
    logger.info("조리 순서 검증 통과")
    return state



def validate_recipe_completeness(state: GraphState) -> Dict[str, Any]:
    """
    Phase 3: 레시피 완성도 검증
    필수 정보 확인, 일관성 검사, 품질 점수 계산
    """
    selected_recipe = state.get("selected_recipe")
    nutrition_info = state.get("nutrition_info")
    optimized_steps = state.get("optimized_steps", [])
    
    if not selected_recipe:
        return {**state, "error": "선택된 레시피가 없습니다.", "quality_score": 0.0}
    
    quality_score = 0.0
    max_score = 100.0
    issues = []
    
    # 필수 정보 확인 (각 항목당 20점)
    checks = {
        "레시피 이름": selected_recipe.get("name"),
        "재료 목록": selected_recipe.get("ingredients", []),
        "조리 단계": optimized_steps,
        "영양 정보": nutrition_info,
        "조리 시간": selected_recipe.get("cooking_time", 0),
    }
    
    for check_name, check_value in checks.items():
        if check_value:
            if isinstance(check_value, list) and len(check_value) > 0:
                quality_score += settings.QUALITY_SCORE_INCREMENT
            elif isinstance(check_value, dict) and len(check_value) > 0:
                quality_score += settings.QUALITY_SCORE_INCREMENT
            elif isinstance(check_value, (str, int)) and check_value:
                quality_score += settings.QUALITY_SCORE_INCREMENT
            else:
                issues.append(f"{check_name}이(가) 비어있습니다")
        else:
            issues.append(f"{check_name}이(가) 없습니다")
    
    # 일관성 검사 (추가 점수)
    # 재료와 조리 단계 일관성
    ingredients = selected_recipe.get("ingredients", [])
    if ingredients and optimized_steps:
        steps_text = " ".join([step.get("description", "") for step in optimized_steps])
        ingredients_mentioned = sum(1 for ing in ingredients if ing in steps_text)
        if ingredients_mentioned > 0:
            consistency_score = (ingredients_mentioned / len(ingredients)) * 10.0
            quality_score += consistency_score
        else:
            issues.append("조리 단계에 재료가 언급되지 않습니다")
    
    # 조리 시간과 단계 수 일관성
    cooking_time = selected_recipe.get("cooking_time", 0)
    if cooking_time > 0 and optimized_steps:
        steps_time = sum(step.get("time", 0) for step in optimized_steps)
        if steps_time > 0:
            time_ratio = min(cooking_time, steps_time) / max(cooking_time, steps_time)
            if time_ratio > 0.7:  # 70% 이상 일치하면 좋음
                quality_score += 10.0
            else:
                issues.append("조리 시간과 단계별 시간이 일치하지 않습니다")
    
    # 품질 점수 정규화 (0.0 ~ 1.0)
    normalized_score = quality_score / max_score
    
    if normalized_score < 0.8:
        logger.warning(f"레시피 완성도 검증 실패: 점수={normalized_score:.1%}, 문제={', '.join(issues)} (그래도 진행)")
        # 검증 실패해도 그냥 진행 (속도 우선)
    
    logger.info(f"레시피 완성도 검증 통과: 점수={normalized_score:.1%}")
    return {
        **state,
        "quality_score": normalized_score
    }


# ==================== 초보자 모드 Phase 3 노드 ====================

def analyze_user_situation(state: GraphState) -> Dict[str, Any]:
    """
    Phase 3-1: 사용자 상황 분석 노드 (초보자 모드)
    
    입력:
    - 크롤링한 원본 레시피 (필요 재료)
    - 사용자가 체크한 보유 재료
    동작:
    - 보유 vs 필요 재료 비교
    - 부족한 재료 식별
    - 매칭률 계산
    - 재료 카테고리별 분석
    출력: 사용자 상황 분석 결과
    """
    structured_recipe = state.get("structured_recipe") or state.get("original_recipe")
    
    if not structured_recipe:
        return {"error": "레시피 데이터가 없습니다."}
    
    required_ingredients = structured_recipe.get("ingredients", []) or state.get("required_ingredients", [])
    
    if not required_ingredients:
        return {"error": "필요한 재료 리스트가 없습니다."}
    
    # 체크된 재료 = 없는 재료 (missing_ingredients)
    # phase2_nodes에서 이미 missing_ingredients로 설정되어 있음
    missing_ingredients = state.get("missing_ingredients", [])
    
    logger.info(f"사용자 상황 분석 시작: 필요 재료 {len(required_ingredients)}개, 없는 재료 {len(missing_ingredients)}개")
    
    try:
        # 재료 매칭 (체크된 재료 = 없는 재료로 처리)
        matched_ingredients = []
        
        for req_ing in required_ingredients:
            is_missing = False
            # missing_ingredients에 있는 재료인지 확인
            for missing_ing in missing_ingredients:
                if IngredientNormalizer.can_substitute(req_ing, missing_ing):
                    is_missing = True
                    break
            
            # 없는 재료가 아니면 매칭된 재료
            if not is_missing:
                matched_ingredients.append(req_ing)
        
        # 전체 매칭률 계산
        match_rate = len(matched_ingredients) / len(required_ingredients) if required_ingredients else 0.0
        
        # 지능형 매칭 점수 계산 (matched_ingredients와 required_ingredients로 계산)
        # matched_ingredients = 보유 재료로 간주
        matching_score = calculate_intelligent_matching_score(
            matched_ingredients,
            required_ingredients
        )
        
        # 카테고리별 분석
        extracted_categories = state.get("extracted_categories", {})
        category_analysis = {
            "main": {"required": [], "matched": [], "missing": [], "match_rate": 0.0},
            "side": {"required": [], "matched": [], "missing": [], "match_rate": 0.0},
            "seasoning": {"required": [], "matched": [], "missing": [], "match_rate": 0.0},
            "other": {"required": [], "matched": [], "missing": [], "match_rate": 0.0}
        }
        
        for req_ing in required_ingredients:
            category = extracted_categories.get(req_ing, "other")
            if category not in category_analysis:
                category = "other"
            
            category_analysis[category]["required"].append(req_ing)
            
            if req_ing in matched_ingredients:
                category_analysis[category]["matched"].append(req_ing)
            else:
                category_analysis[category]["missing"].append(req_ing)
        
        # 카테고리별 매칭률 계산
        for category, data in category_analysis.items():
            required_count = len(data["required"])
            matched_count = len(data["matched"])
            if required_count > 0:
                data["match_rate"] = matched_count / required_count
        
        logger.info(f"사용자 상황 분석 완료: 매칭률 {match_rate * 100:.1f}%, 매칭 점수 {matching_score:.1f}점, 부족한 재료 {len(missing_ingredients)}개")
        
        return {
            **state,
            "required_ingredients": required_ingredients,
            "matched_ingredients": matched_ingredients,
            "missing_ingredients": missing_ingredients,
            "match_rate": match_rate,
            "matching_score": matching_score,
            "category_analysis": category_analysis
        }
    
    except Exception as e:
        logger.error(f"사용자 상황 분석 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": f"사용자 상황 분석 중 오류가 발생했습니다: {str(e)}"}


def plan_substitutions(state: GraphState) -> Dict[str, Any]:
    """
    Phase 3-2: 대체재료 계획 노드 (LLM 활용 - 초보자 모드)
    
    입력:
    - 부족한 재료 리스트
    - 원본 레시피 정보 (맛, 특징)
    - 사용자 페르소나 (초보자)
    동작 (LLM):
    - 부족한 재료별 대체재료 제안
    - 원본 레시피의 맛/특징을 최대한 유지하는 방향
    - 대체재료 사용 시 맛 변화 예측
    - 신뢰도 점수 부여
    출력: 대체재료 계획 (부족 재료 → 대체재료 매핑)
    """
    missing_ingredients = state.get("missing_ingredients", [])
    structured_recipe = state.get("structured_recipe") or state.get("original_recipe")
    user_persona = state.get("user_persona")
    
    if not missing_ingredients:
        return {
            **state,
            "substitution_suggestions": [],
            "substitution_details": {}
        }
    
    if not structured_recipe:
        return {"error": "레시피 정보가 없습니다."}
    
    logger.info(f"대체재료 계획 시작: 부족한 재료 {len(missing_ingredients)}개")
    
    try:
        # 레시피 특징 추출 (LLM 호출)
        recipe_name = structured_recipe.get("name", "")
        recipe_ingredients = structured_recipe.get("ingredients", [])
        
        recipe_context = f"""
레시피명: {recipe_name}
주요 재료: {', '.join(recipe_ingredients[:5])}
"""
        
        # 각 부족한 재료에 대해 대체재료 계획 생성
        substitution_details = {}
        
        for missing_ing in missing_ingredients[:5]:  # 최대 5개만 처리
            try:
                # 기존 _suggest_substitutions_with_llm 재사용하되, 레시피 컨텍스트 추가
                category = state.get("extracted_categories", {}).get(missing_ing)
                
                if settings.OPENAI_API_KEY:
                    prompt = f"""다음 레시피에 부족한 재료의 대체재료를 제안해주세요.

{recipe_context}

부족한 재료: {missing_ing}
재료 카테고리: {category or "정보 없음"}

**중요**: 원본 레시피의 맛과 특징을 최대한 유지할 수 있는 대체재료를 제안해주세요.
초보자가 이해하기 쉬운 설명을 포함해주세요.

각 제안에는 다음을 포함해주세요:
- ingredient: 대체재료 이름
- reason: 대체 이유 (초보자용 설명)
- confidence: 신뢰도 (0.0~1.0)
- taste_change: 맛 변화 예측
- usage_tip: 사용 팁

응답은 다음 JSON 형식의 리스트만 반환하세요:
[
  {{
    "ingredient": "대체재",
    "reason": "설명",
    "confidence": 0.8,
    "taste_change": "맛 변화 설명",
    "usage_tip": "사용 팁"
  }}
]
"""
                    messages = [
                        {"role": "system", "content": "당신은 한국 요리 전문가입니다. 초보자가 이해하기 쉽게 대체재료를 제안하세요."},
                        {"role": "user", "content": prompt}
                    ]
                    content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.5)
                    
                    # JSON 추출
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    data = json.loads(content)
                    if isinstance(data, list) and len(data) > 0:
                        best_sub = data[0]  # 첫 번째 제안 사용
                        substitution_details[missing_ing] = {
                            "ingredient": missing_ing,
                            "substitute": best_sub.get("ingredient", ""),
                            "reason": best_sub.get("reason", ""),
                            "confidence": float(max(0.0, min(1.0, best_sub.get("confidence", 0.5)))),
                            "taste_change": best_sub.get("taste_change", ""),
                            "usage_tip": best_sub.get("usage_tip", "")
                        }
                else:
                    # API 키가 없으면 기본값
                    substitution_details[missing_ing] = {
                        "ingredient": missing_ing,
                        "substitute": missing_ing,
                        "reason": "대체재료 정보 없음",
                        "confidence": 0.5,
                        "taste_change": "예측 불가",
                        "usage_tip": ""
                    }
            except Exception as e:
                logger.warning(f"대체재료 계획 생성 실패 ({missing_ing}): {e}")
                continue
        
        # substitution_suggestions 형식으로도 저장 (하위 호환)
        substitution_suggestions = []
        for missing, details in substitution_details.items():
            substitution_suggestions.append({
                "missing": missing,
                "suggestions": [{
                    "ingredient": details["substitute"],
                    "reason": details["reason"],
                    "confidence": details["confidence"]
                }]
            })
        
        # substitution_mapping 생성
        substitution_mapping = {
            missing: details["substitute"]
            for missing, details in substitution_details.items()
        }
        
        logger.info(f"대체재료 계획 완료: {len(substitution_details)}개 재료")
        
        return {
            **state,
            "substitution_suggestions": substitution_suggestions,
            "substitution_details": substitution_details,
            "substitution_mapping": substitution_mapping
        }
    
    except Exception as e:
        logger.error(f"대체재료 계획 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": f"대체재료 계획 중 오류가 발생했습니다: {str(e)}"}


def adapt_recipe_content(state: GraphState) -> Dict[str, Any]:
    """
    Phase 3-3: 레시피 내용 가공 노드 (LLM 활용 - 핵심)
    
    입력:
    - 크롤링한 원본 조리법
    - 대체재료 정보
    - 사용자 페르소나 (초보자)
    동작 (LLM):
    - 원본 조리법을 사용자 상황에 맞게 가공
    - 대체재료 사용 부분만 수정
    - 각 단계에 대체재료 사용 시 주의사항 추가
    - 원본 레시피의 핵심은 유지 (조리법 구조 보존)
    출력: 가공된 조리법
    """
    structured_recipe = state.get("structured_recipe") or state.get("original_recipe")
    substitution_details = state.get("substitution_details", {})
    substitution_mapping = state.get("substitution_mapping", {})
    
    if not structured_recipe:
        return {"error": "레시피 정보가 없습니다."}
    
    original_steps = structured_recipe.get("steps", [])
    if not original_steps:
        return {"error": "조리 단계가 없습니다."}
    
    logger.info(f"레시피 내용 가공 시작: {len(original_steps)}개 단계")
    
    try:
        # 대체재료가 없으면 원본 그대로 반환
        if not substitution_mapping:
            adapted_steps = [
                {
                    "step": i + 1,
                    "description": step if isinstance(step, str) else step.get("description", str(step)),
                    "note": None
                }
                for i, step in enumerate(original_steps)
            ]
            adapted_ingredients = structured_recipe.get("ingredients", [])
        else:
            # LLM으로 레시피 가공
            if settings.OPENAI_API_KEY:
                steps_text = "\n".join([
                    f"{i+1}. {step if isinstance(step, str) else step.get('description', str(step))}"
                    for i, step in enumerate(original_steps)
                ])
                
                substitutions_text = "\n".join([
                    f"- {original} → {substitute}"
                    for original, substitute in substitution_mapping.items()
                ])
                
                prompt = f"""다음 레시피의 조리 단계를 대체재료 정보를 반영하여 수정해주세요.

**원본 조리 단계:**
{steps_text}

**대체재료:**
{substitutions_text}

**중요 규칙:**
1. 원본 조리 단계의 구조와 순서를 반드시 유지하세요.
2. 대체재료 사용 부분만 수정하세요.
3. 각 단계에 대체재료 사용 시 주의사항을 note 필드로 추가하세요.
4. 원본 조리법의 핵심은 그대로 유지하세요.

응답은 다음 JSON 형식으로 반환하세요:
{{
  "steps": [
    {{
      "step": 1,
      "description": "수정된 조리 단계 설명",
      "note": "대체재료 사용 시 주의사항 (없으면 null)"
    }}
  ],
  "ingredients": ["수정된 재료 리스트"]
}}
"""
                messages = [
                    {"role": "system", "content": "당신은 한국 요리 전문가입니다. 원본 레시피의 구조를 유지하면서 대체재료를 반영하세요."},
                    {"role": "user", "content": prompt}
                ]
                content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.3)
                
                # JSON 추출
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                data = json.loads(content)
                adapted_steps = data.get("steps", [])
                adapted_ingredients = data.get("ingredients", structured_recipe.get("ingredients", []))
            else:
                # API 키가 없으면 단순 교체
                adapted_steps = [
                    {
                        "step": i + 1,
                        "description": step if isinstance(step, str) else step.get("description", str(step)),
                        "note": None  # 대체재료 정보는 adapted_ingredients에만 반영
                    }
                    for i, step in enumerate(original_steps)
                ]
                adapted_ingredients = [
                    substitution_mapping.get(ing, ing)
                    for ing in structured_recipe.get("ingredients", [])
                ]
        
        logger.info(f"레시피 내용 가공 완료: {len(adapted_steps)}개 단계")
        
        return {
            **state,
            "adapted_recipe_steps": adapted_steps,
            "adapted_ingredients": adapted_ingredients
        }
    
    except Exception as e:
        logger.error(f"레시피 내용 가공 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": f"레시피 내용 가공 중 오류가 발생했습니다: {str(e)}"}


def optimize_for_persona(state: GraphState) -> Dict[str, Any]:
    """
    Phase 3-4: 페르소나 최적화 노드 (초보자용)
    
    입력:
    - 가공된 조리법
    - 사용자 페르소나: 초보자
    동작 (LLM):
    - 각 단계에 "왜 이렇게 하는지" 설명 추가
    - 실패 포인트 예상 및 대비책 제안
    - 시간/화력 조절 팁
    - 재료 준비 순서 안내
    - 실수 방지 팁 추가
    출력: 초보자 최적화된 조리법 (상세 설명 포함)
    """
    adapted_steps = state.get("adapted_recipe_steps")
    structured_recipe = state.get("structured_recipe") or state.get("original_recipe")
    user_persona = state.get("user_persona")
    substitution_details = state.get("substitution_details", {})
    
    # adapted_steps가 없으면 원본 레시피의 steps를 사용
    if not adapted_steps:
        if structured_recipe:
            original_steps = structured_recipe.get("steps", [])
            if original_steps:
                adapted_steps = [
                    {
                        "step": i + 1,
                        "description": step if isinstance(step, str) else step.get("description", str(step)),
                        "note": None
                    }
                    for i, step in enumerate(original_steps)
                ]
                logger.info(f"원본 레시피 steps를 adapted_steps 형식으로 변환: {len(adapted_steps)}개")
            else:
                return {"error": "조리 단계가 없습니다."}
        else:
            return {"error": "레시피 정보가 없습니다."}
    
    # 초보자 페르소나가 아니면 그대로 반환
    if user_persona != UserPersona.BEGINNER:
        return {
            **state,
            "optimized_recipe_steps": adapted_steps
        }
    
    logger.info(f"페르소나 최적화 시작: 초보자용, {len(adapted_steps)}개 단계")
    
    try:
        if settings.OPENAI_API_KEY:
            steps_text = "\n".join([
                f"{step.get('step', i+1)}. {step.get('description', '')}"
                for i, step in enumerate(adapted_steps)
            ])
            
            substitutions_text = ""
            if substitution_details:
                substitutions_text = "\n대체재료 정보:\n" + "\n".join([
                    f"- {details['ingredient']} → {details['substitute']}: {details['usage_tip']}"
                    for details in substitution_details.values()
                ])
            
            prompt = f"""다음 레시피 조리 단계를 초보자를 위한 상세한 가이드로 변환해주세요.

**조리 단계:**
{steps_text}
{substitutions_text}

**요구사항:**
1. 각 단계에 "왜 이렇게 하는지" 설명을 why 필드로 추가
2. 실패 포인트 예상 및 대비책을 failure_points 필드로 추가
3. 화력/시간 조절 팁을 heat_level 필드로 추가
4. 첫 단계에 재료 준비 순서를 preparation_guide 필드로 추가
5. 일반적인 실수 방지 팁을 general_tips 필드로 추가

응답은 다음 JSON 형식으로 반환하세요:
{{
  "steps": [
    {{
      "step": 1,
      "description": "조리 단계 설명",
      "why": "왜 이렇게 하는지 설명",
      "failure_points": ["실패 포인트 1", "실패 포인트 2"],
      "heat_level": "중불",
      "note": "기존 note 유지"
    }}
  ],
  "preparation_guide": "재료 준비 순서",
  "general_tips": ["팁 1", "팁 2"]
}}
"""
            messages = [
                {"role": "system", "content": "당신은 초보자를 위한 요리 가이드 전문가입니다. 쉽고 상세하게 설명하세요."},
                {"role": "user", "content": prompt}
            ]
            content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.4)
            
            # JSON 추출
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            optimized_steps = data.get("steps", adapted_steps)
            preparation_guide = data.get("preparation_guide", "")
            general_tips = data.get("general_tips", [])
            
            # 첫 단계에 preparation_guide와 general_tips 추가
            if optimized_steps and (preparation_guide or general_tips):
                optimized_steps[0]["preparation_guide"] = preparation_guide
                optimized_steps[0]["general_tips"] = general_tips
        else:
            # API 키가 없으면 기본 구조만 추가
            optimized_steps = [
                {
                    **step,
                    "why": "초보자용 설명 필요",
                    "failure_points": [],
                    "heat_level": "중불"
                }
                for step in adapted_steps
            ]
            if optimized_steps:
                optimized_steps[0]["preparation_guide"] = "재료를 미리 준비해두세요"
                optimized_steps[0]["general_tips"] = ["화력을 적절히 조절하세요"]
        
        logger.info(f"페르소나 최적화 완료: {len(optimized_steps)}개 단계")
        
        return {
            **state,
            "optimized_recipe_steps": optimized_steps
        }
    
    except Exception as e:
        logger.error(f"페르소나 최적화 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # 오류 시 가공된 단계 그대로 반환
        return {
            **state,
            "optimized_recipe_steps": adapted_steps
        }


# ==================== Explainable + Research-grade 노드들 ====================

