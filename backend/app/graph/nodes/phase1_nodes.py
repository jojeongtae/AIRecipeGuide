"""
Phase 1: phase1 노드 함수들
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



def _normalize_ingredient_name(name: str) -> str:
    """재료명 정규화 (괄호 제거, 공백 정리)"""
    if not name:
        return ""
    normalized = re.sub(r'\([^)]*\)', '', name).strip()
    normalized = ' '.join(normalized.split())
    return normalized



def _extract_json_from_response(content: str) -> str:
    """LLM 응답에서 JSON 추출"""
    if "```json" in content:
        return content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        return content.split("```")[1].split("```")[0].strip()
    return content.strip()



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



def _generate_recipes_with_llm(ingredients: List[str]) -> List[Dict[str, Any]]:
    """LLM을 사용하여 재료 기반 레시피 생성"""
    if not settings.OPENAI_API_KEY:
        # API 키가 없으면 기본 레시피 반환
        return _get_default_recipes(ingredients)
    
    try:
        ingredients_str = ", ".join(ingredients)
        prompt = f"""다음 재료를 사용하여 만들 수 있는 한국 요리 레시피 3개를 추천해주세요.

보유한 재료: {ingredients_str}

각 레시피에 대해 다음 정보를 JSON 형식으로 제공해주세요:
1. 레시피 이름 (name)
2. 필요한 재료 목록 (ingredients) - 보유한 재료와 추가로 필요한 재료 포함
3. 조리 시간 (cooking_time) - 분 단위
4. 난이도 (difficulty) - "초보환영", "보통", "어려움" 중 하나
5. 요리 순서 (steps) - 단계별 설명

응답은 반드시 다음 JSON 형식으로 해주세요:
{{
  "recipes": [
    {{
      "name": "레시피 이름",
      "ingredients": ["재료1", "재료2", ...],
      "cooking_time": 30,
      "difficulty": "보통",
      "steps": ["1단계 설명", "2단계 설명", ...]
    }}
  ]
}}

JSON만 응답하고 다른 설명은 하지 마세요."""

        # OpenAI API 호출 (헤더 최소화로 헤더 불일치 문제 해결)
        messages = [
            {"role": "system", "content": "당신은 한국 요리 전문가입니다. 주어진 재료로 만들 수 있는 맛있는 레시피를 추천해주세요."},
            {"role": "user", "content": prompt}
        ]
        content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.7)
        content = _extract_json_from_response(content)
        result = json.loads(content)
        recipes = result.get("recipes", [])
        
        # 레시피 형식 변환
        formatted_recipes = []
        for i, recipe in enumerate(recipes, 1):
            recipe_name = recipe.get("name", "레시피")
            # 레시피 이름으로 이미지 URL 생성
            recipe_image = _get_recipe_image_url(recipe_name)
            
            formatted_recipe = {
                "id": f"llm_{i}",
                "name": recipe_name,
                "ingredients": recipe.get("ingredients", []),
                "cooking_time": recipe.get("cooking_time", 30),
                "difficulty": recipe.get("difficulty", "보통"),
                "level": recipe.get("difficulty", "보통"),
                "steps": recipe.get("steps", []),
                "match_score": 0.0,  # 나중에 계산
                "image": recipe_image,  # 이미지 추가
                "serving_size": 2,  # 기본값 2인분
            }
            formatted_recipes.append(formatted_recipe)
        
        return formatted_recipes
        
    except ImportError:
        return _get_default_recipes(ingredients)
    except Exception as e:
        logger.error(f"LLM 레시피 생성 오류: {e}")
        return _get_default_recipes(ingredients)



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



def _search_recipes_with_tavily(ingredients: List[str]) -> List[Dict[str, Any]]:
    """Tavily Search API를 사용하여 실시간 레시피 검색 (메인 재료 기반)"""
    if not settings.TAVILY_API_KEY:
        logger.info("Tavily API 키가 설정되지 않아 Tavily 검색을 건너뜁니다.")
        return []
    
    try:
        from tavily import TavilyClient
        
        # 메인 재료 식별
        main_ingredient = _identify_main_ingredient(ingredients)
        other_ingredients = [ing for ing in ingredients if ing != main_ingredient]
        
        logger.info(f"Tavily Search API 사용: 메인 재료={main_ingredient}, 전체 재료={ingredients}")
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        
        # 메인 재료 기반 검색 쿼리 생성
        if other_ingredients:
            # 메인 재료 + 서브 재료 조합
            query = f"{main_ingredient} {', '.join(other_ingredients[:2])} 레시피 한국 요리"
        else:
            # 메인 재료만
            query = f"{main_ingredient} 레시피 한국 요리"
        
        # Tavily 검색 실행
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=10,
            include_answer=True,
            include_raw_content=True
        )
        
        recipes = []
        results = response.get("results", [])
        logger.info(f"Tavily 검색 결과: {len(results)}개 웹 페이지 발견")
        
        # 검색 결과를 LLM으로 분석하여 레시피 추출
        if results and settings.OPENAI_API_KEY:
            recipes = _parse_tavily_results_with_llm(results, ingredients)
            logger.info(f"Tavily 검색으로 {len(recipes)}개 레시피 추출 완료")
        else:
            logger.warning("Tavily 검색 결과가 없거나 OpenAI API 키가 설정되지 않았습니다.")
        
        return recipes
        
    except ImportError:
        logger.warning("tavily-python 패키지가 설치되지 않았습니다.")
        return []
    except Exception as e:
        logger.error(f"Tavily Search API 오류: {e}")
        return []



def _parse_tavily_results_with_llm(search_results: List[Dict], ingredients: List[str]) -> List[Dict[str, Any]]:
    """LLM을 사용하여 Tavily 검색 결과를 레시피 형식으로 파싱"""
    if not settings.OPENAI_API_KEY:
        return []
    
    try:
        # 검색 결과 요약 및 이미지 추출
        results_summary = []
        result_images = []  # 각 결과의 이미지 URL 저장
        
        for i, result in enumerate(search_results[:5], 1):  # 상위 5개만 사용
            title = result.get("title", "")
            content = result.get("content", "")[:500]  # 처음 500자만
            url = result.get("url", "")
            
            # 이미지 URL 추출 (여러 소스 시도)
            image_url = ""
            if "images" in result and result["images"]:
                image_url = result["images"][0]  # 첫 번째 이미지 사용
            elif "image" in result:
                image_url = result["image"]
            
            result_images.append(image_url)
            results_summary.append(f"{i}. {title}\n{content}\nURL: {url}")
        
        results_text = "\n\n".join(results_summary)
        ingredients_str = ", ".join(ingredients)
        
        prompt = f"""다음은 웹 검색 결과입니다. 이 결과에서 사용자가 보유한 재료({ingredients_str})로 만들 수 있는 한국 요리 레시피를 추출해주세요.

검색 결과:
{results_text}

**중요**: 각 레시피에 대해 반드시 다음 정보를 모두 포함하여 JSON 형식으로 제공해주세요:
1. 레시피 이름 (name)
2. 필요한 재료 목록 (ingredients) - 보유한 재료와 추가로 필요한 재료 포함
3. 조리 시간 (cooking_time) - 분 단위
4. 난이도 (difficulty) - "초보환영", "보통", "어려움" 중 하나
5. 요리 순서 (steps) - **반드시 5-8단계의 상세한 조리 과정을 배열로 제공**

요리 순서(steps)는 다음 형식으로 작성해주세요:
- 각 단계는 구체적이고 실용적으로 작성
- 재료 준비 → 양념/소스 준비 → 조리 시작 → 중간 과정 → 마무리 순서로 구성
- 최소 5단계 이상 필수

응답은 반드시 다음 JSON 형식으로 해주세요:
{{
  "recipes": [
    {{
      "name": "레시피 이름",
      "ingredients": ["재료1", "재료2", ...],
      "cooking_time": 30,
      "difficulty": "보통",
      "steps": ["1단계: 재료를 준비하고 손질합니다", "2단계: 양념을 만듭니다", "3단계: 팬에 기름을 두르고 볶습니다", "4단계: 중간 과정", "5단계: 완성합니다"]
    }}
  ]
}}

**steps 필드는 반드시 5개 이상의 단계를 포함해야 합니다. 빈 배열이나 단계가 적은 경우는 절대 안 됩니다.**

JSON만 응답하고 다른 설명은 하지 마세요."""

        # OpenAI API 호출 (헤더 최소화로 헤더 불일치 문제 해결)
        messages = [
            {"role": "system", "content": "당신은 한국 요리 전문가입니다. 웹 검색 결과에서 주어진 재료로 만들 수 있는 맛있는 레시피를 추출해주세요."},
            {"role": "user", "content": prompt}
        ]
        content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.7)
        
        # JSON 추출
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        recipes = result.get("recipes", [])
        
        # 레시피 형식 변환
        formatted_recipes = []
        for i, recipe in enumerate(recipes, 1):
            steps = recipe.get("steps", [])
            recipe_name = recipe.get("name", "레시피")
            
            # steps가 없거나 비어있으면 레시피 이름과 재료로부터 생성
            if not steps or len(steps) == 0:
                logger.warning(f"Tavily 레시피 '{recipe_name}'에 steps가 없습니다. LLM으로 생성합니다.")
                steps = _generate_cooking_steps_with_llm(
                    recipe_name,
                    recipe.get("ingredients", []),
                    recipe.get("cooking_time", 30)
                )
                if not steps:
                    # LLM 생성 실패 시 기본 단계
                    steps = [
                        "재료를 준비하고 손질합니다.",
                        "양념이나 소스를 만듭니다.",
                        "팬이나 냄비에 기름을 두르고 가열합니다.",
                        "재료를 넣고 조리합니다.",
                        "완성합니다."
                    ]
            
            formatted_recipe = {
                "id": str(i),
                "name": recipe_name,
                "ingredients": recipe.get("ingredients", []),
                "cooking_time": recipe.get("cooking_time", 30),
                "difficulty": recipe.get("difficulty", "보통"),
                "level": recipe.get("difficulty", "보통"),
                "steps": steps,
                "match_score": 0.0,  # 나중에 계산
            }
            formatted_recipes.append(formatted_recipe)
        
        logger.info(f"Tavily 레시피 {len(formatted_recipes)}개 파싱 완료 (모두 steps 포함)")
        return formatted_recipes
        
    except Exception as e:
        logger.error(f"LLM 레시피 파싱 오류: {e}")
        return []



def search_recipes(state: GraphState) -> Dict[str, Any]:
    """
    노드 3: 레시피 검색 (다중 소스 수집)
    크롤링, Tavily, LLM 결과를 각각 수집하여 compare_and_select_source로 전달
    """
    ingredients = state.get("ingredients", [])
    
    crawler_recipes = []
    tavily_recipes = []
    llm_recipes = []
    
    # 1순위: 만개의레시피 크롤링 시도
    # 육류(닭고기, 소고기, 돼지고기)를 우선적으로 필터링하여 검색
    meat_keywords = ["닭고기", "닭", "치킨", "닭가슴살", "닭다리", "닭날개", "닭봉",
                     "소고기", "소", "한우", "쇠고기", "등심", "안심", "갈비살", "불고기",
                     "돼지고기", "돼지", "삼겹살", "목살", "앞다리", "뒷다리", "갈비", "갈비살"]
    
    meat_ingredients = []
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
        
        # 육류가 아닌 메인 재료
        if not is_meat and category == "main":
            other_main_ingredients.append(ing)
    
    # 육류가 있으면 육류만 검색, 없으면 다른 메인 재료 검색, 그것도 없으면 전체 재료 검색
    if meat_ingredients:
        search_ingredients = meat_ingredients
        logger.info(f"육류 우선 필터링: {len(meat_ingredients)}개 육류 재료로 검색")
    elif other_main_ingredients:
        search_ingredients = other_main_ingredients
        logger.info(f"다른 메인 재료로 검색: {len(other_main_ingredients)}개")
    else:
        search_ingredients = ingredients
        logger.info(f"전체 재료로 검색: {len(ingredients)}개")
    
    # 메인 재료 목록 (필터링용)
    main_ingredients = meat_ingredients + other_main_ingredients
    
    try:
        from app.services.recipe_crawler import search_recipes_by_ingredients, RecipeCrawlerError
        # 검색은 메인 재료만 사용하지만, 매칭 계산은 전체 재료 사용
        crawler_recipes = search_recipes_by_ingredients(search_ingredients, max_results=10, user_ingredients=ingredients)
        
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



def filter_recipes(state: GraphState) -> Dict[str, Any]:
    """
    노드 4: 레시피 필터링
    난이도, 조리 시간, 카테고리, 블랙리스트 키워드, 매칭 점수 등으로 필터링
    """
    recipes = state.get("recipes", [])
    difficulty = state.get("difficulty")
    max_cooking_time = state.get("max_cooking_time")
    category = state.get("category")
    user_ingredients = state.get("ingredients", [])
    user_choice = state.get("user_choice")
    
    # 사용자가 선택한 레시피를 미리 보존
    selected_recipe = None
    if user_choice is not None and 0 <= user_choice < len(recipes):
        selected_recipe = recipes[user_choice]
        logger.info(f"사용자 선택 레시피 보존: {selected_recipe.get('name', 'Unknown')} (인덱스 {user_choice})")
    
    filtered_recipes = []
    
    # 1단계: 블랙리스트 키워드 필터링
    for recipe in recipes:
        recipe_name = recipe.get("name", "").lower()
        
        # 블랙리스트 키워드 체크
        if any(keyword in recipe_name for keyword in CATEGORY_BLACKLIST_KEYWORDS):
            logger.info(f"블랙리스트 키워드로 제외: {recipe.get('name')}")
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
        # 메인요리를 선택했을 때 절대 포함하지 않을 카테고리
        exclude_categories = []
        if category == "메인요리":
            exclude_categories = ["후식", "음료"]
        elif category == "반찬":
            exclude_categories = ["후식", "음료"]
        elif category == "국/찌개":
            exclude_categories = ["후식", "음료"]
        
        categorized_matched = []
        categorized_unmatched = []
        for recipe in filtered_recipes:
            recipe_category = recipe.get("category")
            if not recipe_category:
                recipe_category = _classify_recipe_category(
                    recipe.get("name", ""),
                    recipe.get("ingredients", [])
                )
                recipe["category"] = recipe_category
                logger.info(f"레시피 '{recipe.get('name')}' 카테고리 분류: {recipe_category}")
            
            # 제외 카테고리는 절대 포함하지 않음
            if recipe_category in exclude_categories:
                logger.info(f"제외 카테고리로 제외: '{recipe.get('name')}' (분류: {recipe_category}, 요청: {category})")
                continue
            
            if recipe_category == category:
                categorized_matched.append(recipe)
            else:
                match_score = recipe.get("match_score", 0)
                # 카테고리가 다르더라도 매칭 점수가 40점 이상이면 포함 (우선순위만 낮춤) - 더 완화
                if match_score >= 40.0:
                    categorized_unmatched.append(recipe)
                    logger.info(f"카테고리 불일치지만 높은 매칭 점수로 포함: '{recipe.get('name')}' (분류: {recipe_category}, 요청: {category}, 점수: {match_score:.1f})")
                else:
                    logger.info(f"카테고리 불일치로 제외: '{recipe.get('name')}' (분류: {recipe_category}, 요청: {category}, 점수: {match_score:.1f})")
        
        # 카테고리 일치 레시피를 먼저, 그 다음 높은 점수의 불일치 레시피
        filtered_recipes = categorized_matched + categorized_unmatched
        logger.info(f"카테고리 필터링 후: {len(filtered_recipes)}개 (일치: {len(categorized_matched)}개, 불일치 포함: {len(categorized_unmatched)}개)")
    else:
        # 카테고리 필터가 없어도 각 레시피에 카테고리 추가
        for recipe in filtered_recipes:
            if not recipe.get("category"):
                recipe["category"] = _classify_recipe_category(
                    recipe.get("name", ""),
                    recipe.get("ingredients", [])
                )
    
    # 5단계: 제목 일관성 체크 - 메인 재료가 제목에 포함된 레시피를 우선순위 상단에 배치
    if user_ingredients:
        main_ingredient = _identify_main_ingredient(user_ingredients)
        if main_ingredient:
            main_ingredient_normalized = _normalize_ingredient_name(main_ingredient).lower()
            
            # 제목에 메인 재료가 포함된 레시피와 그렇지 않은 레시피 분리
            title_matched = []
            title_unmatched = []
            
            for recipe in filtered_recipes:
                recipe_name_lower = recipe.get("name", "").lower()
                if main_ingredient_normalized in recipe_name_lower:
                    title_matched.append(recipe)
                else:
                    title_unmatched.append(recipe)
            
            # 제목에 메인 재료가 포함된 레시피를 앞에 배치
            filtered_recipes = title_matched + title_unmatched
    
    # 6단계: 난이도 필터링
    if difficulty:
        filtered_recipes = [r for r in filtered_recipes if r.get("difficulty") == difficulty.value]
    
    # 7단계: 조리 시간 필터링
    if max_cooking_time:
        filtered_recipes = [r for r in filtered_recipes if r.get("cooking_time", 0) <= max_cooking_time]
    
    # 8단계: 사용자가 선택한 레시피 보존 및 우선순위 배치
    if selected_recipe is not None:
        # 선택된 레시피를 필터링된 리스트에서 제거 (중복 방지)
        filtered_recipes = [r for r in filtered_recipes if r.get("name") != selected_recipe.get("name") or r.get("url") != selected_recipe.get("url")]
        # 선택된 레시피를 리스트 맨 앞에 배치
        filtered_recipes.insert(0, selected_recipe)
        logger.info(f"사용자 선택 레시피를 리스트 맨 앞에 배치: {selected_recipe.get('name', 'Unknown')}")
    
    logger.info(f"필터링 완료: {len(recipes)}개 -> {len(filtered_recipes)}개")
    
    # state의 다른 필드들(특히 search_source)을 유지
    return {
        **state,
        "recipes": filtered_recipes
    }



def select_recipe(state: GraphState) -> Dict[str, Any]:
    """
    노드 5: 레시피 선택
    단일 레시피면 자동 선택, 여러 개면 상위 3개 추천
    """
    recipes = state.get("recipes", [])
    user_choice = state.get("user_choice")
    
    if len(recipes) == 0:
        logger.warning("레시피 목록이 비어있습니다.")
        return {"error": "레시피를 찾을 수 없습니다."}
    
    if len(recipes) == 1:
        logger.info(f"단일 레시피 자동 선택: {recipes[0].get('name', 'Unknown')}")
        return {"selected_recipe": recipes[0]}
    
    if user_choice is not None:
        selected_recipe_id = state.get("selected_recipe_id")
        selected_recipe_name = state.get("selected_recipe_name")
        
        # 레시피 ID 또는 이름으로 먼저 찾기 (정확한 매칭)
        selected = None
        if selected_recipe_id or selected_recipe_name:
            for recipe in recipes:
                recipe_id = recipe.get("id", "")
                recipe_name = recipe.get("name", "")
                
                # ID 매칭 우선
                if selected_recipe_id and recipe_id == selected_recipe_id:
                    selected = recipe
                    logger.info(f"레시피 ID로 매칭: {recipe_name} (ID: {recipe_id})")
                    break
                # 이름 매칭
                elif selected_recipe_name and recipe_name == selected_recipe_name:
                    selected = recipe
                    logger.info(f"레시피 이름으로 매칭: {recipe_name}")
                    break
        
        # ID/이름 매칭 실패 시 인덱스로 선택
        if not selected:
            if 0 <= user_choice < len(recipes):
                selected = recipes[user_choice]
                logger.info(f"사용자 선택 레시피 (인덱스 {user_choice}): {selected.get('name', 'Unknown')}")
            else:
                logger.warning(f"유효하지 않은 레시피 인덱스: {user_choice} (총 {len(recipes)}개 레시피)")
                # 인덱스가 범위를 벗어나면 첫 번째 레시피 선택
                selected = recipes[0] if recipes else None
        
        if selected:
            return {"selected_recipe": selected}
        else:
            logger.error("선택할 레시피를 찾을 수 없습니다.")
            return {"error": "선택할 레시피를 찾을 수 없습니다."}
    
    # 여러 개인 경우 상위 10개 반환 (사용자 선택 대기)
    logger.info(f"레시피 {len(recipes)}개 중 상위 10개 반환")
    return {"recipes": recipes[:10]}



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
    
    # 레시피 이름 기준 중복 제거 (같은 이름의 레시피는 매칭 점수가 높은 것 하나만 남기기)
    unique_recipes = {}
    for recipe in filtered_recipes:
        recipe_name = recipe.get("name", "").strip()
        if not recipe_name:
            continue
        
        # 레시피 이름 정규화 (공백, 특수문자 정리)
        normalized_name = recipe_name.lower().strip()
        
        if normalized_name not in unique_recipes:
            unique_recipes[normalized_name] = recipe
        else:
            # 이미 존재하면 매칭 점수가 높은 것을 선택
            existing_score = unique_recipes[normalized_name].get("match_score", 0)
            current_score = recipe.get("match_score", 0)
            if current_score > existing_score:
                unique_recipes[normalized_name] = recipe
    
    selected_recipes = list(unique_recipes.values())
    logger.info(f"레시피 이름 중복 제거 후: {len(filtered_recipes)}개 -> {len(selected_recipes)}개")
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


