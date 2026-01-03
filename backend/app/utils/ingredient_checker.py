"""
재료 비교 유틸리티 함수 (LangGraph 독립적)
"""
import re
import logging
from typing import List, Dict, Any, Tuple
from app.utils.ingredient_map import IngredientNormalizer, check_ingredient_substitution_with_llm
from app.config import settings

logger = logging.getLogger(__name__)


def normalize_for_matching(ingredient: str) -> str:
    """매칭용 정규화: 수량 제거 후 재료명만 추출"""
    if not ingredient:
        return ""
    # 수량 패턴 제거 (예: "200g", "1대", "2컵")
    name_only = re.sub(r'\s*\d+\.?\d*\s*[가-힣a-zA-Z]*\s*$', '', str(ingredient)).strip()
    name_only = re.sub(r'\s+\d+\.?\d*\s*[가-힣a-zA-Z]*\s*', ' ', name_only).strip()
    return name_only


def check_ingredients_simple(
    required_ingredients: List[str],
    user_ingredients: List[str],
    recipe_name: str = ""
) -> Dict[str, Any]:
    """
    재료 비교 (간단한 버전, LangGraph State 불필요)
    
    Args:
        required_ingredients: 레시피에 필요한 재료 목록
        user_ingredients: 사용자가 보유한 재료 목록
        recipe_name: 레시피 이름 (선택적, LLM 매칭용)
    
    Returns:
        {
            "matched_ingredients": List[str],
            "missing_ingredients": List[str],
            "match_rate": float,
            "substitution_guidances": List[Dict] (선택적)
        }
    """
    matched_ingredients = []
    missing_ingredients = []
    substitution_guidances = []
    
    # 요리 도구 목록
    from app.services.recipe_crawler import COOKING_TOOLS
    
    for required_ing in required_ingredients:
        is_matched = False
        required_ing_name = normalize_for_matching(required_ing)
        
        # 요리 도구 제외
        if any(tool in required_ing_name for tool in COOKING_TOOLS):
            continue
        
        # 물 제외
        if required_ing_name in ["물", "water"]:
            continue
        
        # 1순위: 정규화 매칭
        for user_ing in user_ingredients:
            user_ing_name = normalize_for_matching(user_ing)
            
            if IngredientNormalizer.can_substitute(user_ing_name, required_ing_name):
                is_matched = True
                guidance = IngredientNormalizer.get_substitution_guidance(user_ing_name, required_ing_name)
                if guidance:
                    substitution_guidances.append({
                        "user_ingredient": user_ing,
                        "required_ingredient": required_ing,
                        "guidance": guidance
                    })
                break
        
        # 2순위: LLM 매칭 (정규화 매칭 실패 시)
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
                    substitution_guidances.append({
                        "user_ingredient": user_ing,
                        "required_ingredient": required_ing,
                        "guidance": llm_result.get("reason", "")
                    })
                    break
        
        # 매칭 결과 분류
        if is_matched:
            matched_ingredients.append(required_ing)
        else:
            missing_ingredients.append(required_ing)
    
    # 매칭률 계산
    match_rate = len(matched_ingredients) / len(required_ingredients) if required_ingredients else 0.0
    
    return {
        "matched_ingredients": matched_ingredients,
        "missing_ingredients": missing_ingredients,
        "match_rate": match_rate,
        "substitution_guidances": substitution_guidances if substitution_guidances else None
    }

