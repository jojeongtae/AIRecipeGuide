"""
Phase 1: phase1 노드 함수들
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
from app.database import SessionLocal
from app.services.db_service import (
    get_cached_search,
    save_search_cache,
    save_recipe
)
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
from app.graph.nodes.search_module import _generate_recipes_with_llm, _search_recipes_with_tavily, _parse_tavily_results_with_llm
from app.graph.nodes.filter_module import filter_recipes, _has_main_ingredient_in_recipe
from app.graph.nodes.selection_module import select_recipe, compare_and_select_source
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

def input_ingredients(state: GraphState) -> Dict[str, Any]:
    """
    노드 1: 재료 입력 처리
    사용자 입력을 받아 정규화된 재료 리스트로 변환
    """
    user_input = state.get("user_input", "")
    ingredients = []
    for part in user_input.replace("，", ",").split(","):
        ing = part.strip()
        if ing:
            ingredients.append(ing)
    
    return {
        **state,
        "ingredients": ingredients,
        "user_input": user_input
    }




def analyze_ingredients(state: GraphState) -> Dict[str, Any]:
    """
    노드 2: 재료 분석 및 정규화
    - 재료명 정규화 (동의어 처리) - IngredientNormalizer 사용
    - 카테고리 분류
    """
    ingredients = state.get("ingredients", [])
    
    normalized_ingredients = []
    ingredient_categories = {}
    
    for ingredient in ingredients:
        # IngredientNormalizer를 사용한 정규화
        normalized = IngredientNormalizer.normalize(ingredient)
        # 괄호 제거 등 추가 정규화
        normalized = _normalize_ingredient_name(normalized)
        normalized_ingredients.append(normalized)
        
        # 카테고리 분류
        if normalized in ["계란", "달걀"]:
            ingredient_categories[normalized] = "단백질"
        elif normalized in ["토마토", "양파", "당근", "대파", "파"]:
            ingredient_categories[normalized] = "채소"
        elif normalized in ["밥", "쌀"]:
            ingredient_categories[normalized] = "주식"
        else:
            ingredient_categories[normalized] = "기타"
    
    # 페르소나가 없으면 기본값으로 초보자 설정
    user_persona = state.get("user_persona")
    if not user_persona:
        user_persona = UserPersona.BEGINNER
    
    return {
        **state,
        "ingredients": normalized_ingredients,
        "ingredient_categories": ingredient_categories,
        "user_persona": user_persona
    }



def _get_recipe_image_url(recipe_name: str) -> str:
    """레시피 이름으로 Unsplash에서 음식 이미지 URL 가져오기"""
    try:
        import urllib.parse
        # Unsplash Source API (무료, API 키 불필요)
        query = urllib.parse.quote(f"{recipe_name} food korean")
        return f"https://source.unsplash.com/400x300/?{query}"
    except Exception:
        return ""



# _generate_recipes_with_llm는 search_module.py에서 import됨

def _get_default_recipes(ingredients: List[str]) -> List[Dict[str, Any]]:
    """기본 레시피 반환 (LLM 사용 불가 시)"""
    ingredients_set = set(ing.lower() for ing in ingredients)
    
    default_recipes = [
        {
            "id": "1",
            "name": "계란볶음밥",
            "ingredients": ["계란", "밥", "양파", "대파", "식용유", "소금", "후추"],
            "cooking_time": 15,
            "difficulty": "초보환영",
            "level": "초보환영",
            "steps": [
                "계란을 그릇에 풀어 소금과 후추로 간을 합니다",
                "팬에 식용유를 두르고 계란을 스크램블합니다",
                "양파와 대파를 넣고 볶습니다",
                "밥을 넣고 함께 볶아 완성합니다"
            ],
            "match_score": 0.0,
            "image": _get_recipe_image_url("계란볶음밥"),  # 이미지 추가
            "serving_size": 2,  # 기본값 2인분
        },
        {
            "id": "2",
            "name": "김치볶음밥",
            "ingredients": ["밥", "김치", "계란", "대파", "식용유", "참기름"],
            "cooking_time": 20,
            "difficulty": "초보환영",
            "level": "초보환영",
            "steps": [
                "김치를 잘게 썹니다",
                "팬에 식용유를 두르고 김치를 볶습니다",
                "밥을 넣고 함께 볶습니다",
                "계란을 풀어 넣고 볶아 완성합니다",
                "대파와 참기름을 넣어 마무리합니다"
            ],
            "match_score": 0.0,
            "image": _get_recipe_image_url("김치볶음밥"),  # 이미지 추가
            "serving_size": 2,  # 기본값 2인분
        },
    ]
    
    # 보유 재료와 매칭되는 레시피만 필터링
    matched_recipes = []
    for recipe in default_recipes:
        recipe_ingredients = [ing.lower() for ing in recipe["ingredients"]]
        if any(ing in ingredients_set for ing in recipe_ingredients):
            matched_recipes.append(recipe)
    
    return matched_recipes if matched_recipes else default_recipes



def _categorize_ingredient(ingredient: str) -> str:
    """
    재료를 카테고리로 분류 (메인 재료, 부재료, 양념)
    
    Returns:
        "main" (메인 재료), "side" (부재료), "seasoning" (양념)
    """
    normalized = _normalize_ingredient_name(ingredient).lower()
    
    # 메인 재료 (50점)
    main_keywords = {
        # 고기류
        "돼지고기", "돼지", "삼겹살", "목살", "앞다리", "뒷다리", "갈비", "갈비살",
        "소고기", "소", "한우", "쇠고기", "등심", "안심", "갈비살", "불고기",
        "닭고기", "닭", "치킨", "닭가슴살", "닭다리", "닭날개", "닭봉",
        "햄", "베이컨", "소시지", "스팸",
        # 생선류
        "고등어", "연어", "참치", "삼치", "꽁치", "멸치", "오징어", "문어", "새우", "게", "조개",
        "전복", "소라", "바지락", "홍합",
        # 계란
        "계란", "달걀", "계란후라이", "스크램블",
        # 두부
        "두부", "연두부", "부침두부",
        # 해조류
        "김", "미역", "다시마", "톳",
    }
    
    # 양념류 (20점)
    seasoning_keywords = {
        "소금", "후추", "설탕", "식초", "간장", "된장", "고춧가루", "고추장",
        "마늘", "생강", "파", "대파", "쪽파", "양파", "고추", "청양고추",
        "참기름", "들기름", "식용유", "올리브오일", "버터", "마요네즈",
        "물엿", "올리고당", "매실청", "꿀",
        "다진마늘", "다진생강", "다진파",
    }
    
    # 메인 재료 확인
    for keyword in main_keywords:
        if keyword in normalized or normalized in keyword:
            return "main"
    
    # 양념 확인
    for keyword in seasoning_keywords:
        if keyword in normalized or normalized in keyword:
            return "seasoning"
    
    # 나머지는 부재료 (30점)
    return "side"



def _identify_main_ingredient(ingredients: List[str]) -> str:
    """재료 목록에서 메인 재료 식별 (고기, 생선, 계란 등) - 우선순위: 고기 > 생선 > 계란 > 두부"""
    # 메인 재료 키워드 (우선순위 순)
    # 1순위: 고기류
    meat_keywords = [
        "돼지고기", "돼지", "삼겹살", "목살", "앞다리", "뒷다리", "갈비", "갈비살",
        "소고기", "소", "한우", "쇠고기", "등심", "안심", "불고기",
        "닭고기", "닭", "치킨", "닭가슴살", "닭다리", "닭날개",
        "햄", "베이컨", "소시지", "스팸",
    ]
    # 2순위: 생선류
    seafood_keywords = [
        "고등어", "연어", "참치", "삼치", "꽁치", "멸치", "오징어", "문어", "새우", "게", "조개",
    ]
    # 3순위: 계란
    egg_keywords = [
        "계란", "달걀", "계란후라이", "스크램블",
    ]
    # 4순위: 두부
    tofu_keywords = [
        "두부", "연두부", "부침두부",
    ]
    
    # 우선순위별로 키워드 목록을 순서대로 체크
    keyword_groups = [
        (meat_keywords, 1),
        (seafood_keywords, 2),
        (egg_keywords, 3),
        (tofu_keywords, 4),
    ]
    
    # 정규화된 재료명으로 메인 재료 찾기
    normalized_ingredients = [_normalize_ingredient_name(ing) for ing in ingredients]
    
    # 모든 재료를 스캔하여 가장 높은 우선순위(낮은 숫자)의 재료 찾기
    best_priority = 999
    best_ingredient = None
    
    for ingredient_idx, ingredient in enumerate(normalized_ingredients):
        for keywords, priority in keyword_groups:
            for keyword in keywords:
                if keyword in ingredient.lower() or ingredient.lower() in keyword:
                    # 더 높은 우선순위(낮은 숫자)를 찾았으면 업데이트
                    if priority < best_priority:
                        best_priority = priority
                        best_ingredient = ingredients[ingredient_idx]
                        break
            if best_priority == priority:  # 이미 최고 우선순위를 찾았으면 다음 그룹 체크 불필요
                break
    
    if best_ingredient:
        return best_ingredient
    
    # 메인 재료를 찾지 못하면 첫 번째 재료를 메인으로 사용
    return ingredients[0] if ingredients else ""






# _parse_tavily_results_with_llm는 search_module.py에서 import됨

def search_recipes(state: GraphState) -> Dict[str, Any]:
    """
    노드 3: 레시피 검색 (다중 소스 수집)
    크롤링, Tavily, LLM 결과를 각각 수집하여 compare_and_select_source로 전달
    """
    ingredients = state.get("ingredients", [])
    filters = state.get("filters", {})
    pre_selected_recipe = state.get("pre_selected_recipe")
    
    # 캐시 조회 시도 (DB 연결 실패 시 기존 로직으로 폴백)
    try:
        db = SessionLocal()
        cached_result = get_cached_search(db, ingredients, filters)
        db.close()
        
        if cached_result and cached_result.get("cached"):
            logger.info("캐시에서 검색 결과 조회 성공")
            # 캐시된 recipe_ids를 사용하여 레시피 정보를 가져와야 하지만,
            # 현재는 캐시에 recipe_ids만 저장되어 있으므로 compare_and_select_source에서 처리
            # 여기서는 캐시 히트를 표시만 하고 기존 로직 계속 진행
            # (실제로는 recipe_ids를 가져와서 레시피를 조회해야 하지만, 
            #  현재 구조상 compare_and_select_source에서 처리하는 것이 더 적합)
            state["cache_hit"] = True
            state["cached_recipe_ids"] = cached_result.get("recipe_ids", [])
            state["cached_match_scores"] = cached_result.get("match_scores", {})
    except Exception as e:
        logger.warning(f"캐시 조회 실패, 기존 로직으로 진행: {e}")
        state["cache_hit"] = False
    
    crawler_recipes = []
    tavily_recipes = []
    llm_recipes = []
    
    # 1순위: 만개의레시피 크롤링 시도
    # 육류(닭고기, 소고기, 돼지고기, 베이컨 등)를 우선적으로 필터링하여 검색
    meat_keywords = ["닭고기", "닭", "치킨", "닭가슴살", "닭다리", "닭날개", "닭봉",
                     "소고기", "소", "한우", "쇠고기", "등심", "안심", "갈비살", "불고기",
                     "돼지고기", "돼지", "삼겹살", "목살", "앞다리", "뒷다리", "갈비", "갈비살",
                     "오리고기", "오리",
                     "베이컨", "햄", "소시지", "스팸"]
    
    # 해산물 키워드 (육류 다음 우선순위)
    seafood_keywords = ["고등어", "연어", "참치", "삼치", "꽁치", "멸치", "오징어", "문어", "새우", "게", "조개",
                        "전복", "소라", "바지락", "홍합", "굴"]
    
    meat_ingredients = []
    seafood_ingredients = []
    other_main_ingredients = []
    
    for ing in ingredients:
        normalized = _normalize_ingredient_name(ing).lower()
        category = _categorize_ingredient(ing)
        
        # 육류 우선 필터링
        is_meat = False
        for meat_keyword in meat_keywords:
            if meat_keyword in normalized or normalized in meat_keyword:
                meat_ingredients.append(ing)
                is_meat = True
                break
        
        # 해산물 필터링 (육류 다음 우선순위)
        is_seafood = False
        if not is_meat:
            for seafood_keyword in seafood_keywords:
                if seafood_keyword in normalized or normalized in seafood_keyword:
                    seafood_ingredients.append(ing)
                    is_seafood = True
                    break
        
        # 육류/해산물이 아닌 메인 재료
        if not is_meat and not is_seafood and category == "main":
            other_main_ingredients.append(ing)
    
    # 검색 전략: 여러 재료를 조합해서 검색하여 더 다양한 결과 얻기
    if meat_ingredients:
        # 육류가 있으면 육류 + 해산물/다른 메인 재료 조합 (최대 3개까지)
        combined_others = seafood_ingredients + other_main_ingredients
        if combined_others:
            # 육류 1개 + 해산물/다른 메인 재료 2개까지 조합
            search_ingredients = meat_ingredients[:1] + combined_others[:2]
            logger.info(f"육류 + 메인 재료 조합 검색: {len(search_ingredients)}개 재료 ({meat_ingredients[:1]} + {combined_others[:2]})")
        else:
            search_ingredients = meat_ingredients
            logger.info(f"육류 우선 필터링: {len(meat_ingredients)}개 육류 재료로 검색")
    elif seafood_ingredients:
        # 해산물이 있으면 해산물 + 다른 메인 재료 조합 (최대 3개까지)
        if other_main_ingredients:
            search_ingredients = seafood_ingredients[:1] + other_main_ingredients[:2]
            logger.info(f"해산물 + 메인 재료 조합 검색: {len(search_ingredients)}개 재료 ({seafood_ingredients[:1]} + {other_main_ingredients[:2]})")
        else:
            search_ingredients = seafood_ingredients
            logger.info(f"해산물 우선 필터링: {len(seafood_ingredients)}개 해산물 재료로 검색")
    elif other_main_ingredients:
        # 메인 재료가 여러 개면 최대 3개까지 조합
        search_ingredients = other_main_ingredients[:3]
        logger.info(f"메인 재료 조합 검색: {len(search_ingredients)}개 ({search_ingredients})")
    else:
        # 메인 재료가 없으면 전체 재료 중 상위 5개 사용
        search_ingredients = ingredients[:5]
        logger.info(f"전체 재료 상위 {len(search_ingredients)}개로 검색: {search_ingredients}")
    
    # 메인 재료 목록 (필터링용)
    main_ingredients = meat_ingredients + seafood_ingredients + other_main_ingredients
    
    try:
        from app.services.recipe_crawler import search_recipes_by_ingredients, RecipeCrawlerError
        # 검색은 조합된 재료를 사용하지만, 매칭 계산은 전체 재료 사용
        # 더 많은 결과를 얻기 위해 max_results를 늘림
        crawler_recipes = search_recipes_by_ingredients(search_ingredients, max_results=20, user_ingredients=ingredients)
        
        # 검색 결과 필터링: 메인 재료가 실제로 포함된 레시피만 선택 (더 엄격하게)
        if main_ingredients and crawler_recipes:
            filtered_crawler_recipes = []
            for recipe in crawler_recipes:
                recipe_ingredients = recipe.get("ingredients", [])
                recipe_ingredients_normalized = [_normalize_ingredient_name(ing).lower() for ing in recipe_ingredients]
                
                # 메인 재료 중 하나라도 레시피에 포함되어 있는지 확인 (더 엄격하게)
                # "닭고기"를 검색했는데 "닭똥집"만 나오는 경우 제외
                from app.utils.ingredient_map import IngredientNormalizer
                has_main = False
                for main_ing in main_ingredients:
                    main_normalized = _normalize_ingredient_name(main_ing).lower()
                    for recipe_ing in recipe_ingredients_normalized:
                        # 정확한 매칭 또는 동의어 매칭만 허용
                        if IngredientNormalizer.can_substitute(main_normalized, recipe_ing):
                            has_main = True
                            break
                        # 부분 일치도 허용하되, 너무 짧은 키워드(2글자 이하)는 제외
                        elif len(main_normalized) > 2 and (main_normalized in recipe_ing or recipe_ing in main_normalized):
                            # "닭똥집" 같은 특수 케이스 제외 (닭고기 != 닭똥집)
                            if "똥집" not in recipe_ing and "모래집" not in recipe_ing:
                                has_main = True
                                break
                    if has_main:
                        break
                
                if has_main:
                    filtered_crawler_recipes.append(recipe)
            
            crawler_recipes = filtered_crawler_recipes
            logger.info(f"메인 재료 필터링 후: {len(crawler_recipes)}개 레시피")
        
        if crawler_recipes:
            logger.info(f"✅ 크롤링으로 {len(crawler_recipes)}개 레시피 찾음")
        else:
            logger.info("크롤링 결과 없음")
    except (RecipeCrawlerError, ImportError) as e:
        logger.warning(f"크롤링 실패: {e}")
    
    # 2순위: Tavily 검색 (크롤링 결과가 없을 때만 사용)
    # 크롤링 결과가 있으면 크롤링을 우선 사용하므로 Tavily는 사용하지 않음
    should_use_tavily = False
    if not crawler_recipes:
        # 크롤링 결과가 없을 때만 Tavily 사용
        should_use_tavily = True
        logger.info("크롤링 결과가 없어 Tavily 검색 시도")
    
    if should_use_tavily and settings.TAVILY_API_KEY:
        tavily_recipes = _search_recipes_with_tavily(ingredients)
        if tavily_recipes:
            logger.info(f"✅ Tavily Search API로 {len(tavily_recipes)}개 레시피 검색 성공")
    
    # 3순위: LLM 생성 (크롤링과 Tavily 결과가 모두 없거나 부족할 때)
    # 크롤링 결과가 있지만 매칭 점수가 모두 0이거나, 결과가 없을 때 LLM 생성
    has_valid_crawler = crawler_recipes and any(r.get("match_score", 0) > 0 for r in crawler_recipes)
    has_valid_tavily = tavily_recipes and any(r.get("match_score", 0) > 0 for r in tavily_recipes)
    
    if not has_valid_crawler and not has_valid_tavily:
        llm_recipes = _generate_recipes_with_llm(ingredients)
        if llm_recipes:
            logger.info(f"LLM으로 {len(llm_recipes)}개 레시피 생성")
    
    # pre_selected_recipe가 있으면 크롤러 결과에 맨 앞에 추가 (사용자가 선택한 레시피 보존)
    if pre_selected_recipe:
        # 중복 제거: 이미 크롤러 결과에 있는지 확인
        pre_url = pre_selected_recipe.get("url") or pre_selected_recipe.get("source_url")
        pre_name = pre_selected_recipe.get("name", "")
        is_duplicate = False
        
        for recipe in crawler_recipes:
            recipe_url = recipe.get("url") or recipe.get("source_url")
            recipe_name = recipe.get("name", "")
            if (pre_url and recipe_url == pre_url) or (pre_name and recipe_name == pre_name):
                is_duplicate = True
                break
        
        if not is_duplicate:
            crawler_recipes.insert(0, pre_selected_recipe)
            logger.info(f"pre_selected_recipe를 크롤러 결과 맨 앞에 추가: {pre_name}")
    
    # 각 소스의 결과를 별도로 저장 (compare_and_select_source에서 처리)
    return {
        **state,
        "crawler_recipes": crawler_recipes,
        "tavily_recipes": tavily_recipes,
        "llm_recipes": llm_recipes,
        "recipes": []  # compare_and_select_source에서 채워짐
    }



def _classify_recipe_category(recipe_name: str, ingredients: List[str]) -> str:
    """
    레시피 이름과 재료를 기반으로 카테고리 분류
    """
    name_lower = recipe_name.lower()
    
    # 후식 키워드
    dessert_keywords = ["탕후루", "케이크", "쿠키", "푸딩", "마카롱", "마시멜로우", "젤리", "캔디", "사탕", "초콜릿", "아이스크림", "빙수", "팥빙수", "과자", "떡", "한과", "후식", "디저트"]
    if any(keyword in name_lower for keyword in dessert_keywords):
        return "후식"
    
    # 국/찌개 키워드
    soup_keywords = ["국", "찌개", "탕", "전골", "해장국", "미역국", "콩나물국", "된장찌개", "김치찌개", "부대찌개"]
    if any(keyword in name_lower for keyword in soup_keywords):
        return "국/찌개"
    
    # 면/밥 키워드 (메인요리로 분류)
    # 면/밥은 보통 메인요리이므로 메인요리로 분류
    # rice_noodle_keywords = ["볶음밥", "비빔밥", "죽", "리조또", "파스타", "라면", "국수", "우동", "냉면", "쫄면", "떡볶이", "짜장면", "짬뽕"]
    # if any(keyword in name_lower for keyword in rice_noodle_keywords):
    #     return "면/밥"
    
    # 음료 키워드
    drink_keywords = ["주스", "스무디", "라떼", "에이드", "티", "차", "쥬스", "음료", "드링크"]
    if any(keyword in name_lower for keyword in drink_keywords):
        return "음료"
    
    # 반찬 키워드 (명확한 반찬만 반찬으로 분류)
    # "볶음"은 너무 일반적이므로 제외하고, 명확한 반찬 키워드만 사용
    side_keywords = ["나물", "어묵볶음", "무침", "부침", "전", "튀김", "김치", "절임", "장아찌", "반찬"]
    # 볶음밥, 비빔밥 등은 메인요리
    if "볶음밥" in name_lower or "비빔밥" in name_lower:
        return "메인요리"
    if any(keyword in name_lower for keyword in side_keywords):
        return "반찬"
    
    # 기본값은 메인요리
    return "메인요리"



def _has_main_ingredient_in_recipe(user_ingredients: List[str], recipe_ingredients: List[str]) -> bool:
    """
    사용자가 입력한 메인 재료(육류, 해산물, 밥, 면 등)가 레시피에 있는지 확인
    """
    from app.utils.ingredient_map import IngredientNormalizer
    
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



# filter_recipes는 filter_module.py에서 import됨
# 아래 함수는 제거됨 - filter_module.py를 참조하세요

def select_recipe(state: GraphState) -> Dict[str, Any]:
    """
    노드 5: 레시피 선택
    단일 레시피면 자동 선택, 여러 개면 상위 3개 추천
    """
    recipes = state.get("recipes", [])
    user_choice = state.get("user_choice")
    selected_recipe_id = state.get("selected_recipe_id")
    selected_recipe_name = state.get("selected_recipe_name")
    pre_selected_recipe = state.get("pre_selected_recipe")
    
    if len(recipes) == 0:
        logger.warning("레시피 목록이 비어있습니다.")
        return {"error": "레시피를 찾을 수 없습니다."}
    
    if len(recipes) == 1:
        logger.info(f"단일 레시피 자동 선택: {recipes[0].get('name', 'Unknown')}")
        return {"selected_recipe": recipes[0]}
    
    # 1순위: recipe_id로 정확히 매칭
    if selected_recipe_id:
        for recipe in recipes:
            recipe_id = recipe.get("id")
            if recipe_id and str(recipe_id) == str(selected_recipe_id):
                logger.info(f"레시피 ID로 정확히 매칭: {recipe.get('name', 'Unknown')} (ID: {selected_recipe_id})")
                return {"selected_recipe": recipe}
        logger.warning(f"레시피 ID로 매칭 실패: {selected_recipe_id}")
    
    # 2순위: recipe_name으로 정확히 매칭
    if selected_recipe_name:
        for recipe in recipes:
            recipe_name = recipe.get("name", "")
            if recipe_name == selected_recipe_name:
                logger.info(f"레시피 이름으로 정확히 매칭: {recipe_name}")
                return {"selected_recipe": recipe}
        logger.warning(f"레시피 이름으로 매칭 실패: {selected_recipe_name}")
    
    # 3순위: pre_selected_recipe와 이름/URL로 매칭
    if pre_selected_recipe:
        pre_name = pre_selected_recipe.get("name", "")
        pre_url = pre_selected_recipe.get("url") or pre_selected_recipe.get("source_url")
        for recipe in recipes:
            recipe_name = recipe.get("name", "")
            recipe_url = recipe.get("url") or recipe.get("source_url")
            if recipe_name == pre_name or (pre_url and recipe_url == pre_url):
                logger.info(f"pre_selected_recipe로 매칭: {recipe_name}")
                return {"selected_recipe": recipe}
        # 매칭 실패 시 pre_selected_recipe를 그대로 사용
        logger.warning(f"pre_selected_recipe로 매칭 실패, pre_selected_recipe를 그대로 사용: {pre_name}")
        return {"selected_recipe": pre_selected_recipe}
    
    # 4순위: user_choice 인덱스로 매칭 (하위 호환성)
    if user_choice is not None:
        # user_choice가 유효한 범위인지 확인
        if 0 <= user_choice < len(recipes):
            selected = recipes[user_choice]
            logger.info(f"사용자 선택 레시피 (인덱스 {user_choice}): {selected.get('name', 'Unknown')}")
            return {"selected_recipe": selected}
        else:
            logger.warning(f"유효하지 않은 레시피 인덱스: {user_choice} (총 {len(recipes)}개 레시피)")
            # 인덱스가 범위를 벗어나면 첫 번째 레시피 선택
            return {"selected_recipe": recipes[0]}
    
    # 여러 개인 경우 상위 10개 반환 (사용자 선택 대기)
    logger.info(f"레시피 {len(recipes)}개 중 상위 10개 반환")
    return {"recipes": recipes[:10]}






def compare_and_select_source(state: GraphState) -> Dict[str, Any]:
    """
    Phase 1: 다중 소스 수집 및 교차 검증
    크롤링 vs Tavily vs LLM 결과 비교 및 최적 소스 선택
    """
    crawler_recipes = state.get("crawler_recipes", [])
    tavily_recipes = state.get("tavily_recipes", [])
    llm_recipes = state.get("llm_recipes", [])
    ingredients = state.get("ingredients", [])
    
    source_scores = {}
    all_recipes = []
    
    # 크롤링 결과 평가 (지능형 매칭 점수 사용)
    if crawler_recipes:
        crawler_scores = []
        for recipe in crawler_recipes:
            recipe_ingredients = recipe.get("ingredients", [])
            # 지능형 매칭 점수 계산
            match_score = calculate_intelligent_matching_score(ingredients, recipe_ingredients)
            recipe["match_score"] = match_score
            crawler_scores.append(match_score)
        
        if crawler_scores:
            avg_score = sum(crawler_scores) / len(crawler_scores)
            source_scores["crawler"] = {
                "avg_match_score": avg_score,
                "recipe_count": len(crawler_recipes),
                "recipes": crawler_recipes
            }
            all_recipes.extend(crawler_recipes)
    
    # Tavily 결과 평가 (지능형 매칭 점수 사용)
    if tavily_recipes:
        tavily_scores = []
        for recipe in tavily_recipes:
            recipe_ingredients = recipe.get("ingredients", [])
            # 지능형 매칭 점수 계산
            match_score = calculate_intelligent_matching_score(ingredients, recipe_ingredients)
            recipe["match_score"] = match_score
            tavily_scores.append(match_score)
        
        if tavily_scores:
            avg_score = sum(tavily_scores) / len(tavily_scores)
            source_scores["tavily"] = {
                "avg_match_score": avg_score,
                "recipe_count": len(tavily_recipes),
                "recipes": tavily_recipes
            }
            all_recipes.extend(tavily_recipes)
    
    # LLM 결과 평가 (지능형 매칭 점수 사용)
    if llm_recipes:
        llm_scores = []
        for recipe in llm_recipes:
            recipe_ingredients = recipe.get("ingredients", [])
            # 지능형 매칭 점수 계산
            match_score = calculate_intelligent_matching_score(ingredients, recipe_ingredients)
            recipe["match_score"] = match_score
            llm_scores.append(match_score)
        
        if llm_scores:
            avg_score = sum(llm_scores) / len(llm_scores)
            source_scores["llm"] = {
                "avg_match_score": avg_score,
                "recipe_count": len(llm_recipes),
                "recipes": llm_recipes
            }
            all_recipes.extend(llm_recipes)
    
    # 최적 소스 선택 (크롤링 우선, 크롤링 결과가 있으면 항상 크롤링 선택)
    best_source = None
    best_score = 0.0
    selected_recipes = []
    
    # 1순위: 크롤링 결과가 있으면 항상 크롤링 우선 (점수와 관계없이 선택)
    if "crawler" in source_scores:
        crawler_data = source_scores["crawler"]
        crawler_score = crawler_data["avg_match_score"]
        best_source = "crawler"
        best_score = crawler_score
        selected_recipes = crawler_data["recipes"]
        logger.info(f"✅ 크롤링 결과 우선 선택: 평균 매칭 점수 {crawler_score:.1f}점, 레시피 {len(selected_recipes)}개")
    
    # 크롤링 결과가 없을 때만 다른 소스 중 최고 점수 선택
    if not selected_recipes:
        logger.info("크롤링 결과가 없어 다른 소스 검토 중...")
        for source, data in source_scores.items():
            score = data["avg_match_score"]
            if score > best_score:
                best_score = score
                best_source = source
                selected_recipes = data["recipes"]
                logger.info(f"{source} 소스 선택: 평균 매칭 점수 {score:.1f}점, 레시피 {len(selected_recipes)}개")
    
    # 최적 소스가 없으면 모든 레시피를 합쳐서 상위 레시피 선택
    if not selected_recipes and all_recipes:
        # 매칭 점수순 정렬
        all_recipes.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        selected_recipes = all_recipes[:10]
        best_source = "mixed"
    
    logger.info(f"소스 선택 전 - selected_recipes: {len(selected_recipes)}, all_recipes: {len(all_recipes)}")
    
    # 매칭 점수 임계값으로 필터링 (너무 낮은 매칭도는 제외)
    filtered_recipes = [r for r in selected_recipes if r.get("match_score", 0) >= settings.MATCH_SCORE_THRESHOLD]
    logger.info(f"매칭 점수 필터링 ({settings.MATCH_SCORE_THRESHOLD}점 이상) 후: {len(filtered_recipes)}개")
    
    # 필터링된 레시피가 없으면 매칭 점수순으로 상위 레시피 선택 (최소한 결과는 제공)
    if not filtered_recipes and selected_recipes:
        # 매칭 점수순 정렬
        sorted_recipes = sorted(selected_recipes, key=lambda x: x.get("match_score", 0), reverse=True)
        filtered_recipes = sorted_recipes[:10]  # 최소 10개는 제공
        logger.warning(f"매칭 점수 {settings.MATCH_SCORE_THRESHOLD}점 이상 레시피가 없어 상위 10개 반환: {len(filtered_recipes)}개")
    
    # 여전히 레시피가 없으면 LLM 생성 시도
    if not filtered_recipes:
        logger.warning("모든 소스에서 레시피를 찾지 못함. LLM 생성 시도...")
        try:
            llm_recipes_new = _generate_recipes_with_llm(ingredients)
            if llm_recipes_new:
                # LLM 결과의 지능형 매칭 점수 계산
                for recipe in llm_recipes_new:
                    recipe_ingredients = recipe.get("ingredients", [])
                    match_score = calculate_intelligent_matching_score(ingredients, recipe_ingredients)
                    recipe["match_score"] = match_score
                
                filtered_recipes = llm_recipes_new[:5]
                best_source = "llm"
                logger.info(f"LLM으로 {len(filtered_recipes)}개 레시피 생성 완료")
            else:
                logger.error("LLM 레시피 생성 실패")
        except Exception as e:
            logger.error(f"LLM 레시피 생성 중 오류: {e}")
    
    selected_recipes = filtered_recipes
    logger.info(f"최종 반환할 레시피 수: {len(selected_recipes)}")
    
    # 소스 비교 결과 저장
    source_comparison = {
        "sources": source_scores,
        "selected_source": best_source,
        "selected_score": best_score
    }
    
    logger.info(f"소스 비교 완료: 선택된 소스={best_source}, 레시피 수={len(selected_recipes)}, 평균 매칭률={best_score:.1%}")
    
    if not selected_recipes:
        logger.error(f"최종 레시피가 없습니다. 크롤링={len(crawler_recipes)}, Tavily={len(tavily_recipes)}, LLM={len(llm_recipes)}")
    
    # 선택된 레시피들의 평균 지능형 매칭 점수 계산 및 저장
    if selected_recipes:
        avg_matching_score = sum(r.get("match_score", 0) for r in selected_recipes) / len(selected_recipes)
        logger.info(f"평균 지능형 매칭 점수: {avg_matching_score:.1f}")
    else:
        avg_matching_score = 0.0
    
    # 캐시 저장 시도 (DB 연결 실패 시 무시하고 계속 진행)
    try:
        db = SessionLocal()
        ingredients = state.get("ingredients", [])
        filters = state.get("filters", {})
        
        logger.info(f"DB 저장 시작: 레시피 {len(selected_recipes)}개, 재료: {ingredients}")
        
        # 레시피들을 DB에 저장하고 ID 수집
        recipe_ids = []
        match_scores = {}
        
        for recipe in selected_recipes:
            # 레시피 저장
            recipe_id = save_recipe(db, recipe)
            if recipe_id:
                recipe_ids.append(recipe_id)
                match_scores[str(recipe_id)] = recipe.get("match_score", 0)
                logger.info(f"레시피 저장 성공: {recipe.get('name', 'Unknown')} (ID: {recipe_id})")
            else:
                logger.warning(f"레시피 저장 실패: {recipe.get('name', 'Unknown')}")
        
        # 캐시 저장
        if recipe_ids:
            cache_saved = save_search_cache(
                db=db,
                ingredients=ingredients,
                recipe_ids=recipe_ids,
                match_scores=match_scores,
                filters=filters,
                cache_days=7
            )
            if cache_saved:
                logger.info(f"검색 결과 캐시 저장 완료: {len(recipe_ids)}개 레시피")
            else:
                logger.warning(f"검색 캐시 저장 실패")
        else:
            logger.warning(f"저장할 레시피 ID가 없어서 캐시 저장 안 함")
        
        db.close()
    except Exception as e:
        logger.error(f"캐시 저장 실패 (기존 로직 계속 진행): {e}", exc_info=True)
    
    return {
        **state,
        "recipes": selected_recipes,
        "search_source": best_source,
        "source_comparison": source_comparison,
        "matching_score": avg_matching_score  # state에 matching_score 저장
    }



def explain_recipe_selection(state: GraphState) -> Dict[str, Any]:
    """
    Explainability 노드: 소스 선택 이유 설명
    compare_and_select_source 이후에 실행 (레시피 선택 이전이므로 소스 선택 이유만 설명)
    """
    source_comparison = state.get("source_comparison", {})
    search_source = state.get("search_source", "unknown")
    recipes = state.get("recipes", [])
    
    # 소스 선택 이유 생성
    reasons = []
    reasons.append(f"선택된 검색 소스: {search_source}")
    
    if source_comparison:
        selected_source = source_comparison.get("selected_source")
        selected_score = source_comparison.get("selected_score", 0)
        sources = source_comparison.get("sources", {})
        
        if selected_source:
            reasons.append(f"선택 근거: {selected_source} 소스의 평균 매칭 점수 {selected_score:.1f}점")
            
            # 다른 소스와 비교
            for source_name, source_data in sources.items():
                if source_name != selected_source:
                    other_score = source_data.get("avg_match_score", 0)
                    other_count = source_data.get("recipe_count", 0)
                    reasons.append(f"  - {source_name}: 평균 {other_score:.1f}점 ({other_count}개 레시피)")
    
    if recipes:
        reasons.append(f"총 {len(recipes)}개 레시피 후보 검색 완료")
    
    selection_reasoning = "\n".join(reasons)
    
    # 탈락 소스 분석 (레시피 선택 전이므로 소스 레벨 분석)
    rejection_reasons = []
    if source_comparison:
        selected_source = source_comparison.get("selected_source")
        sources = source_comparison.get("sources", {})
        
        for source_name, source_data in sources.items():
            if source_name != selected_source:
                other_score = source_data.get("avg_match_score", 0)
                selected_score = source_comparison.get("selected_score", 0)
                rejection_reasons.append({
                    "recipe_name": f"{source_name} 소스",
                    "reason": f"평균 매칭 점수 낮음 ({other_score:.1f}점 < {selected_score:.1f}점)"
                })
    
    logger.info(f"소스 선택 설명 생성: 선택 이유 {len(reasons)}개, 탈락 소스 {len(rejection_reasons)}개")
    
    return {
        **state,
        "selection_reasoning": selection_reasoning,
        "rejection_reasons": rejection_reasons if rejection_reasons else None
    }



def formulate_hypothesis(state: GraphState) -> Dict[str, Any]:
    """
    Research Hypothesis 노드: 레시피 선택에 대한 가설 수립
    select_recipe 이후, analyze_nutrition 이전에 실행
    """
    selected_recipe = state.get("selected_recipe")
    user_ingredients = state.get("ingredients", [])
    match_rate = state.get("match_rate", 0.0)
    matching_score = state.get("matching_score", 0.0)
    difficulty = state.get("difficulty")
    max_cooking_time = state.get("max_cooking_time")
    
    if not selected_recipe:
        return state
    
    # 가설 구성 요소
    hypothesis_parts = []
    
    # 재료 매칭률 가설
    if match_rate is not None:
        if match_rate >= 0.8:
            hypothesis_parts.append(f"재료 매칭률 ≥ 80% (실제: {match_rate:.1%})")
        else:
            hypothesis_parts.append(f"재료 매칭률 {match_rate:.1%} (대체 재료 고려 필요)")
    
    # 매칭 점수 가설
    if matching_score is not None:
        if matching_score >= 50:
            hypothesis_parts.append(f"지능형 매칭 점수 ≥ 50점 (실제: {matching_score:.1f}점)")
        else:
            hypothesis_parts.append(f"지능형 매칭 점수 {matching_score:.1f}점 (보통 수준)")
    
    # 조리 시간 가설
    recipe_cooking_time = selected_recipe.get("cooking_time", 0)
    if max_cooking_time:
        if recipe_cooking_time <= max_cooking_time:
            hypothesis_parts.append(f"조리 시간 ≤ 사용자 제한 ({recipe_cooking_time}분 ≤ {max_cooking_time}분)")
        else:
            hypothesis_parts.append(f"조리 시간 초과 가능성 ({recipe_cooking_time}분 > {max_cooking_time}분)")
    
    # 난이도 가설
    recipe_difficulty = selected_recipe.get("difficulty") or selected_recipe.get("level", "")
    if difficulty:
        hypothesis_parts.append(f"난이도 조건 충족: {recipe_difficulty}")
    else:
        hypothesis_parts.append(f"난이도: {recipe_difficulty} (초보자 가능 여부 검토)")
    
    research_hypothesis = " | ".join(hypothesis_parts)
    
    # 가설 검증 결과 초기화 (나중에 검증 노드에서 채움)
    hypothesis_validation_result = {
        "hypothesis": research_hypothesis,
        "validated": False,
        "validation_details": {}
    }
    
    logger.info(f"연구 가설 수립: {research_hypothesis}")
    
    return {
        **state,
        "research_hypothesis": research_hypothesis,
        "hypothesis_validation_result": hypothesis_validation_result
    }



def analyze_alternatives(state: GraphState) -> Dict[str, Any]:
    """
    Alternative Recipe Branch 분석 노드
    select_recipe 이후에 실행하여 대안 분석 생성
    선택된 레시피를 제외한 상위 2-3개를 대안으로 보존
    """
    selected_recipe = state.get("selected_recipe")
    recipes = state.get("recipes", [])
    
    if not selected_recipe:
        return state
    
    selected_id = selected_recipe.get("id") or selected_recipe.get("name", "")
    selected_name = selected_recipe.get("name", "알 수 없음")
    selected_match_score = selected_recipe.get("match_score", 0)
    
    # 선택된 레시피를 제외한 상위 2-3개 추출
    alternative_candidates = []
    for recipe in recipes:
        recipe_id = recipe.get("id") or recipe.get("name", "")
        if recipe_id != selected_id:
            alternative_candidates.append(recipe)
    
    # 매칭 점수순 정렬
    alternative_candidates.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    alternative_recipes = alternative_candidates[:3]  # 상위 3개
    
    # 대안 분석 생성
    if alternative_recipes:
        analysis_parts = []
        analysis_parts.append(f"선택된 레시피: {selected_name} (매칭 점수: {selected_match_score:.1f}점)")
        analysis_parts.append(f"\n대안 레시피 {len(alternative_recipes)}개:")
        
        for i, alt_recipe in enumerate(alternative_recipes, 1):
            alt_name = alt_recipe.get("name", "알 수 없음")
            alt_score = alt_recipe.get("match_score", 0)
            score_diff = selected_match_score - alt_score
            alt_cooking_time = alt_recipe.get("cooking_time", "N/A")
            alt_difficulty = alt_recipe.get("difficulty") or alt_recipe.get("level", "N/A")
            analysis_parts.append(f"{i}. {alt_name} (매칭 점수: {alt_score:.1f}점, 차이: -{score_diff:.1f}점, 조리시간: {alt_cooking_time}분, 난이도: {alt_difficulty})")
        
        alternative_analysis = "\n".join(analysis_parts)
    else:
        alternative_analysis = "대안 레시피가 없습니다."
    
    logger.info(f"대안 레시피 분석: 선택된 레시피 1개, 대안 {len(alternative_recipes)}개")
    
    return {
        **state,
        "alternative_recipes": alternative_recipes if alternative_recipes else None,
        "alternative_analysis": alternative_analysis
    }


# ==================== 초보자 모드 노드들 ====================

def search_menu_recipe(state: GraphState) -> Dict[str, Any]:
    """
    Phase 1-1: 메뉴 검색 노드 (초보자 모드)
    
    입력: 메뉴 이름 (예: "김치찌개")
    동작:
    - 만개의레시피 크롤링
    - 인기순 정렬 (조회수/좋아요 기준)
    - 상위 1개 또는 상위 3개 중 최고 인기 레시피 선택
    출력: 원본 레시피 데이터
    """
    from app.services.recipe_crawler import search_recipes_by_name
    
    menu_name = state.get("user_input", "").strip()
    if not menu_name:
        return {"error": "메뉴 이름이 입력되지 않았습니다."}
    
    logger.info(f"메뉴 검색 시작: {menu_name}")
    
    try:
        # 만개의레시피에서 메뉴 이름으로 검색 (최대 3개)
        recipes = search_recipes_by_name(menu_name, max_results=3)
        
        if not recipes:
            logger.warning(f"메뉴 '{menu_name}'에 대한 레시피를 찾을 수 없습니다.")
            return {"error": f"'{menu_name}'에 대한 레시피를 찾을 수 없습니다."}
        
        # 인기도 점수 계산 및 정렬
        # view_count와 like_count가 없으면 name_similarity를 사용
        for recipe in recipes:
            view_count = recipe.get("view_count", 0)
            like_count = recipe.get("like_count", 0)
            name_similarity = recipe.get("name_similarity", 0.0)
            
            # 인기도 점수 계산 (조회수 70%, 좋아요 30%)
            # view_count가 없으면 name_similarity 기반으로 추정
            if view_count == 0 and like_count == 0:
                popularity_score = name_similarity * 1000  # 추정 점수
            else:
                popularity_score = (view_count * 0.7) + (like_count * 100 * 0.3)
            
            recipe["popularity_score"] = popularity_score
        
        # 인기도 점수 순으로 정렬
        recipes.sort(key=lambda x: x.get("popularity_score", 0), reverse=True)
        
        # 상위 1개 선택
        top_recipe = recipes[0]
        
        logger.info(f"메뉴 검색 완료: {menu_name} -> {top_recipe.get('name', 'Unknown')} (인기도 점수: {top_recipe.get('popularity_score', 0):.1f})")
        
        return {
            **state,
            "menu_name": menu_name,
            "original_recipe": top_recipe,
            "recipes": recipes  # 후보 레시피들도 보관 (필요시 사용)
        }
    
    except Exception as e:
        logger.error(f"메뉴 검색 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": f"메뉴 검색 중 오류가 발생했습니다: {str(e)}"}


def extract_recipe_data(state: GraphState) -> Dict[str, Any]:
    """
    Phase 1-2: 레시피 데이터 추출 노드 (초보자 모드)
    
    입력: 크롤링한 레시피 데이터 (original_recipe)
    동작:
    - 재료 리스트 추출 (정규화)
    - 조리 순서 추출
    - 메타데이터 추출 (출처, 인기도, 조리시간, 난이도 등)
    출력: 구조화된 레시피 데이터
    """
    original_recipe = state.get("original_recipe")
    if not original_recipe:
        return {"error": "크롤링한 레시피 데이터가 없습니다."}
    
    logger.info(f"레시피 데이터 추출 시작: {original_recipe.get('name', 'Unknown')}")
    
    try:
        # 재료 추출 및 정규화
        raw_ingredients = original_recipe.get("ingredients", [])
        logger.info(f"원본 재료 추출: {len(raw_ingredients)}개")
        logger.info(f"원본 재료 목록: {raw_ingredients}")  # 전체 재료 목록 로깅
        normalized_ingredients = []
        ingredient_categories = {}
        seen_normalized = set()  # 정규화된 재료명 중복 제거용
        
        for ing in raw_ingredients:
            if not ing or not ing.strip():
                continue
            
            # 수량 정보를 포함한 원본 재료명을 그대로 사용
            # 정규화 없이 원본 그대로 사용 (수량 정보 보존)
            # 부분 일치 로직 때문에 '파스타면200g' -> '대파' 같은 잘못된 매핑 방지
            cleaned_ing = ing.strip()
            
            if cleaned_ing:
                # 중복 제거: 원본 재료명 기준 (수량 포함)
                if cleaned_ing not in seen_normalized:
                    normalized_ingredients.append(cleaned_ing)
                    seen_normalized.add(cleaned_ing)
                    # 카테고리 분류 (수량 제거한 재료명으로)
                    ing_name_only = re.sub(r'\s*\d+\.?\d*\s*[가-힣a-zA-Z]*\s*$', '', cleaned_ing).strip()
                    ing_name_only = re.sub(r'^\s*\d+\.?\d*\s*[가-힣a-zA-Z]*\s+', '', ing_name_only).strip()
                    if not ing_name_only:
                        ing_name_only = cleaned_ing
                    # 수량 제거한 재료명으로만 정규화 (카테고리 분류용)
                    normalized_for_category = IngredientNormalizer.normalize(ing_name_only)
                    category = categorize_ingredient(normalized_for_category)
                    ingredient_categories[cleaned_ing] = category
                else:
                    logger.debug(f"재료 중복 제거: '{ing}'")
        
        logger.info(f"정규화된 재료: {normalized_ingredients} (중복 제거 후 {len(normalized_ingredients)}개)")  # 정규화된 재료 목록 로깅
        
        # 조리 순서 추출
        cooking_steps = original_recipe.get("steps", [])
        
        # 메타데이터 추출
        structured_recipe = {
            "name": original_recipe.get("name", "레시피"),
            "source": "만개의레시피",
            "source_url": original_recipe.get("url", ""),
            "recipe_id": original_recipe.get("id", ""),
            "view_count": original_recipe.get("view_count", 0),
            "like_count": original_recipe.get("like_count", 0),
            "popularity_score": original_recipe.get("popularity_score", 0.0),
            "cooking_time": original_recipe.get("cooking_time", 30),
            "difficulty": original_recipe.get("difficulty", "보통"),
            "serving_size": original_recipe.get("serving_size", 2),
            "image": original_recipe.get("image", ""),
            "ingredients": normalized_ingredients,
            "steps": cooking_steps,
        }
        
        # 인기도 표시 문자열 생성
        view_count = structured_recipe.get("view_count", 0)
        like_count = structured_recipe.get("like_count", 0)
        popularity_display = ""
        if view_count > 0 or like_count > 0:
            view_str = f"{view_count:,}회" if view_count < 10000 else f"{view_count // 10000}만회"
            popularity_display = f"🔥 조회수 {view_str}, 좋아요 {like_count}개"
        else:
            popularity_display = "🔥 인기 레시피"
        
        structured_recipe["popularity_display"] = popularity_display
        
        logger.info(f"레시피 데이터 추출 완료: {structured_recipe['name']}, 재료 {len(normalized_ingredients)}개, 단계 {len(cooking_steps)}개")
        
        return {
            **state,
            "structured_recipe": structured_recipe,
            "extracted_ingredients": normalized_ingredients,
            "extracted_categories": ingredient_categories,
            "required_ingredients": normalized_ingredients  # 필요 재료로 설정
        }
    
    except Exception as e:
        logger.error(f"레시피 데이터 추출 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": f"레시피 데이터 추출 중 오류가 발생했습니다: {str(e)}"}


def present_ingredients_to_user(state: GraphState) -> Dict[str, Any]:
    """
    Phase 1-3: 재료 리스트 제시 노드 (초보자 모드)
    
    입력: 추출한 재료 리스트
    동작:
    - 재료 리스트를 체크박스 형태로 정리
    - 카테고리 분류 (메인재료, 부재료, 양념)
    - 일반적으로 집에 있는 재료 자동 체크 (물, 식용유, 소금 등)
    - 매칭률 예상 표시 준비
    출력: 프론트엔드에 표시할 재료 리스트 (가이드 포함)
    """
    structured_recipe = state.get("structured_recipe")
    extracted_ingredients = state.get("extracted_ingredients", [])
    extracted_categories = state.get("extracted_categories", {})
    
    if not extracted_ingredients:
        return {"error": "추출된 재료 리스트가 없습니다."}
    
    logger.info(f"재료 리스트 제시 준비: {len(extracted_ingredients)}개 재료")
    
    try:
        # 카테고리별로 그룹화
        grouped = {
            "main": [],
            "side": [],
            "seasoning": [],
            "other": []
        }
        
        # 일반적으로 집에 있는 재료 목록 (자동 체크용)
        common_ingredients = {
            "물", "식용유", "소금", "후추", "설탕", "참기름", "마늘", "대파", 
            "간장", "된장", "고춧가루", "양파"
        }
        
        checklist_items = []
        auto_checked_count = 0
        seen_ingredients = set()  # 중복 제거용
        
        for ing in extracted_ingredients:
            # 재료 이름 정규화 (중복 확인용)
            normalized_ing = ing.strip()
            normalized_lower = normalized_ing.lower()
            
            # 중복 제거: 이미 본 재료면 건너뛰기
            if normalized_ing in seen_ingredients:
                logger.debug(f"중복 재료 제거: {normalized_ing}")
                continue
            
            seen_ingredients.add(normalized_ing)
            
            category = extracted_categories.get(ing, "other")
            if category not in grouped:
                category = "other"
            
            # 일반 재료인지 확인 (정규화된 이름 기준)
            # 반전: 일반 재료는 체크 해제 (있는 재료), 나머지는 체크 (없는 재료)
            is_common = any(common in normalized_lower for common in common_ingredients)
            is_checked = not is_common  # 일반 재료가 아니면 체크 (없는 재료)
            
            if is_common:
                auto_checked_count += 1  # 일반 재료는 자동으로 체크 해제되므로 카운트
            
            checklist_items.append({
                "name": ing,
                "category": category,
                "checked": is_checked
            })
            
            grouped[category].append(ing)
        
        # 예상 매칭률 계산 (자동 체크된 재료 기준)
        estimated_match_rate = auto_checked_count / len(extracted_ingredients) if extracted_ingredients else 0.0
        
        # 프론트엔드용 체크리스트 구조
        ingredients_checklist = {
            "items": checklist_items,
            "summary": {
                "total": len(extracted_ingredients),
                "auto_checked": auto_checked_count,
                "estimated_match_rate": estimated_match_rate,
                "match_rate_display": f"예상 매칭률: {estimated_match_rate * 100:.0f}%"
            }
        }
        
        logger.info(f"재료 리스트 제시 준비 완료: 총 {len(extracted_ingredients)}개, 자동 체크 {auto_checked_count}개, 예상 매칭률 {estimated_match_rate * 100:.0f}%")
        
        return {
            **state,
            "ingredients_checklist": ingredients_checklist,
            "grouped_ingredients": grouped,
            "estimated_match_rate": estimated_match_rate,
            "waiting_for_user_selection": True,
            "interrupt_reason": "waiting_for_ingredient_selection"
        }
    
    except Exception as e:
        logger.error(f"재료 리스트 제시 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": f"재료 리스트 제시 중 오류가 발생했습니다: {str(e)}"}

