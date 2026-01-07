"""
필터링 관련 함수 모듈
레시피 필터링 로직 분리
"""
import logging
from typing import Dict, Any, List
from app.models.state import GraphState
from app.constants import CATEGORY_BLACKLIST_KEYWORDS
from app.graph.utils.ingredient_utils import normalize_ingredient_name, categorize_ingredient
from app.graph.utils.recipe_utils import classify_recipe_category
from app.utils.ingredient_map import IngredientNormalizer
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 하위 호환성을 위한 별칭
_normalize_ingredient_name = normalize_ingredient_name
_categorize_ingredient = categorize_ingredient
_classify_recipe_category = classify_recipe_category


def _has_main_ingredient_in_recipe(user_ingredients: List[str], recipe_ingredients: List[str]) -> bool:
    """
    사용자가 입력한 메인 재료(육류, 해산물, 밥, 면 등)가 레시피에 있는지 확인
    """
    # 메인 재료 키워드 (단백질, 주재료)
    main_ingredient_keywords = [
        # 고기류
        '돼지고기', '소고기', '닭고기', '햄', '베이컨', '소시지', '스팸',
        # 해산물
        '생선', '고등어', '연어', '참치', '오징어', '문어', '새우', '게', '조개',
        # 주재료
        '밥', '라면', '면', '국수', '스파게티', '파스타',
        # 계란
        '계란', '달걀',
        # 두부
        '두부', '콩'
    ]
    
    # 사용자 재료 중 메인 재료 찾기
    user_main_ingredients = []
    for user_ing in user_ingredients:
        user_ing_normalized = _normalize_ingredient_name(user_ing).lower()
        for keyword in main_ingredient_keywords:
            if keyword in user_ing_normalized or user_ing_normalized in keyword:
                user_main_ingredients.append(user_ing)
                break
    
    # 메인 재료가 없으면 체크하지 않음 (양념만 있는 경우 등)
    if not user_main_ingredients:
        return True
    
    # 레시피 재료 중 메인 재료 매칭 확인
    for user_main in user_main_ingredients:
        user_main_normalized = _normalize_ingredient_name(user_main)
        for recipe_ing in recipe_ingredients:
            recipe_ing_normalized = _normalize_ingredient_name(recipe_ing)
            if IngredientNormalizer.can_substitute(user_main_normalized, recipe_ing_normalized):
                return True
    
    return False


def filter_recipes(state: GraphState) -> Dict[str, Any]:
    """
    노드 4: 레시피 필터링
    난이도, 조리 시간, 카테고리, 블랙리스트 키워드, 매칭 점수 등으로 필터링
    """
    recipes = state.get("recipes", [])
    user_choice = state.get("user_choice")
    user_ingredients = state.get("ingredients", [])
    difficulty = state.get("difficulty")
    max_cooking_time = state.get("max_cooking_time")
    category = state.get("category")
    selected_recipe = state.get("selected_recipe")
    
    # 사용자가 직접 선택한 레시피가 있으면 우선 처리
    if user_choice is not None and 0 <= user_choice < len(recipes):
        selected_recipe = recipes[user_choice]
        logger.info(f"사용자 선택 레시피 보존: {selected_recipe.get('name', 'Unknown')} (인덱스 {user_choice})")
    
    filtered_recipes = []
    
    # 1단계: 블랙리스트 키워드 필터링 및 조리 방법 체크
    for recipe in recipes:
        recipe_name = recipe.get("name", "").lower()
        
        # 블랙리스트 키워드 체크
        if any(keyword in recipe_name for keyword in CATEGORY_BLACKLIST_KEYWORDS):
            logger.info(f"블랙리스트 키워드로 제외: {recipe.get('name')}")
            continue
        
        # 조리 방법이 없는 레시피 제외 (레시피가 아닌 항목 필터링)
        steps = recipe.get("steps", [])
        if not steps or len(steps) == 0:
            logger.info(f"조리 방법 없음으로 제외: {recipe.get('name')}")
            continue
        
        filtered_recipes.append(recipe)
    
    logger.info(f"블랙리스트 필터링 후: {len(filtered_recipes)}개")
    
    # 2단계: 메인 재료 체크 (더욱 완화 - 매칭 점수 40점 이상이면 통과)
    if user_ingredients:
        main_ingredient_filtered = []
        for recipe in filtered_recipes:
            recipe_ingredients = recipe.get("ingredients", [])
            match_score = recipe.get("match_score", 0)
            # 메인 재료가 있거나, 매칭 점수가 40점 이상이면 통과 (더 완화)
            if _has_main_ingredient_in_recipe(user_ingredients, recipe_ingredients) or match_score >= 40.0:
                main_ingredient_filtered.append(recipe)
            else:
                logger.info(f"메인 재료 없음으로 제외: {recipe.get('name')} (매칭점수: {match_score:.1f})")
        filtered_recipes = main_ingredient_filtered
        logger.info(f"메인 재료 체크 후: {len(filtered_recipes)}개")
    
    # 3단계: 매칭 점수 필터링 (40점 미만 제외) - 이미 compare_and_select_source에서 필터링되었으므로 스킵
    # filtered_recipes는 이미 40점 이상만 포함되어 있음
    logger.info(f"매칭 점수 필터링 후: {len(filtered_recipes)}개 (이미 필터링됨)")
    
    # 4단계: 카테고리 필터링 및 분류 (선택적 - 카테고리 불일치해도 매칭 점수가 높으면 우선순위만 낮춤)
    if category:
        categorized_matched = []
        categorized_unmatched = []
        
        for recipe in filtered_recipes:
            recipe_name = recipe.get("name", "")
            recipe_category = _classify_recipe_category(recipe_name, recipe.get("ingredients", []))
            recipe["category"] = recipe_category
            
            match_score = recipe.get("match_score", 0)
            
            if recipe_category == category:
                categorized_matched.append(recipe)
                logger.info(f"레시피 '{recipe.get('name')}' 카테고리 분류: {recipe_category}")
            else:
                # 카테고리 불일치해도 매칭 점수가 높으면 포함 (우선순위만 낮춤)
                if match_score >= 50.0:
                    categorized_unmatched.append(recipe)
                    logger.info(f"카테고리 불일치지만 높은 매칭 점수로 포함: '{recipe.get('name')}' (분류: {recipe_category}, 요청: {category}, 점수: {match_score:.1f})")
                else:
                    logger.info(f"제외 카테고리로 제외: '{recipe.get('name')}' (분류: {recipe_category}, 요청: {category})")
        
        filtered_recipes = categorized_matched + categorized_unmatched
        logger.info(f"카테고리 필터링 후: {len(filtered_recipes)}개 (일치: {len(categorized_matched)}개, 불일치 포함: {len(categorized_unmatched)}개)")
    else:
        # 카테고리 필터가 없어도 각 레시피에 카테고리 추가
        for recipe in filtered_recipes:
            recipe_name = recipe.get("name", "")
            recipe_category = _classify_recipe_category(recipe_name, recipe.get("ingredients", []))
            recipe["category"] = recipe_category
    
    # 5단계: 제목 매칭 우선순위 (사용자 입력과 레시피 이름 유사도)
    if user_ingredients:
        # 메인 재료가 레시피 이름에 포함된 경우 우선순위 상승
        title_matched = []
        title_unmatched = []
        
        for recipe in filtered_recipes:
            recipe_name = recipe.get("name", "").lower()
            has_title_match = any(
                _normalize_ingredient_name(ing).lower() in recipe_name 
                for ing in user_ingredients
            )
            
            if has_title_match:
                title_matched.append(recipe)
            else:
                title_unmatched.append(recipe)
        
        filtered_recipes = title_matched + title_unmatched
    
    # 6단계: 난이도 필터링
    if difficulty:
        filtered_recipes = [r for r in filtered_recipes if r.get("difficulty") == difficulty.value]
    
    # 7단계: 조리 시간 필터링
    if max_cooking_time:
        filtered_recipes = [r for r in filtered_recipes if r.get("cooking_time", 0) <= max_cooking_time]
    
    # 선택된 레시피가 있으면 맨 앞에 배치
    if selected_recipe:
        # 선택된 레시피를 필터링된 리스트에서 제거 (중복 방지)
        filtered_recipes = [r for r in filtered_recipes if r.get("name") != selected_recipe.get("name") or r.get("url") != selected_recipe.get("url")]
        filtered_recipes.insert(0, selected_recipe)
        logger.info(f"사용자 선택 레시피를 리스트 맨 앞에 배치: {selected_recipe.get('name', 'Unknown')}")
    
    logger.info(f"필터링 완료: {len(recipes)}개 -> {len(filtered_recipes)}개")
    
    return {
        **state,
        "recipes": filtered_recipes
    }

