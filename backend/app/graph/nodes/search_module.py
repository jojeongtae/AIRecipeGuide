"""
검색 관련 함수 모듈
크롤링, Tavily, LLM 검색 로직 분리
"""
import json
import logging
from typing import Dict, Any, List, Optional
from app.config import settings
from app.graph.utils.llm_helpers import call_openai_api, extract_json_from_response
from app.graph.utils.ingredient_utils import normalize_ingredient_name, categorize_ingredient
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 하위 호환성을 위한 별칭
_normalize_ingredient_name = normalize_ingredient_name
_categorize_ingredient = categorize_ingredient
_extract_json_from_response = extract_json_from_response
_call_openai_api = call_openai_api


def _generate_recipes_with_llm(ingredients: List[str]) -> List[Dict[str, Any]]:
    """
    LLM을 사용하여 레시피 생성
    """
    if not settings.OPENAI_API_KEY:
        return []
    
    try:
        ingredients_str = ", ".join(ingredients)
        
        prompt = f"""다음 재료로 만들 수 있는 한국 요리 레시피를 3개 추천해주세요.

재료: {ingredients_str}

각 레시피는 다음 정보를 포함해야 합니다:
- 레시피 이름
- 필요한 재료 목록 (주어진 재료 + 추가 필요한 재료)
- 예상 조리 시간 (분)
- 난이도 (쉬움/보통/어려움)
- 상세한 조리 단계 (5단계 이상)

응답은 다음 JSON 형식으로 해주세요:
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

        messages = [
            {"role": "system", "content": "당신은 한국 요리 전문가입니다. 주어진 재료로 만들 수 있는 맛있는 레시피를 추천해주세요."},
            {"role": "user", "content": prompt}
        ]
        content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.7)
        
        # JSON 추출
        json_content = _extract_json_from_response(content)
        result = json.loads(json_content)
        recipes = result.get("recipes", [])
        
        # 레시피 형식 변환
        formatted_recipes = []
        for i, recipe in enumerate(recipes, 1):
            steps = recipe.get("steps", [])
            if not steps or len(steps) == 0:
                # steps가 없으면 기본 단계 생성
                steps = [
                    "재료를 준비하고 손질합니다.",
                    "양념이나 소스를 만듭니다.",
                    "팬이나 냄비에 기름을 두르고 가열합니다.",
                    "재료를 넣고 조리합니다.",
                    "완성합니다."
                ]
            
            formatted_recipe = {
                "id": str(i),
                "name": recipe.get("name", "레시피"),
                "ingredients": recipe.get("ingredients", []),
                "cooking_time": recipe.get("cooking_time", 30),
                "difficulty": recipe.get("difficulty", "보통"),
                "level": recipe.get("difficulty", "보통"),
                "steps": steps,
                "match_score": 0.0,
            }
            formatted_recipes.append(formatted_recipe)
        
        return formatted_recipes
        
    except Exception as e:
        logger.error(f"LLM 레시피 생성 오류: {e}")
        return []


def _search_recipes_with_tavily(ingredients: List[str]) -> List[Dict[str, Any]]:
    """
    Tavily Search API를 사용하여 레시피 검색
    """
    if not settings.TAVILY_API_KEY:
        logger.info("Tavily API 키가 설정되지 않아 Tavily 검색을 건너뜁니다.")
        return []
    
    try:
        from tavily import TavilyClient
        
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        
        # 메인 재료 추출 (첫 번째 재료 사용)
        main_ingredient = ingredients[0] if ingredients else ""
        logger.info(f"Tavily Search API 사용: 메인 재료={main_ingredient}, 전체 재료={ingredients}")
        
        # 검색 쿼리 생성
        search_query = f"{main_ingredient} 레시피"
        if len(ingredients) > 1:
            search_query += f" {' '.join(ingredients[1:3])}"  # 최대 3개 재료만 사용
        
        # Tavily 검색 실행
        response = client.search(
            query=search_query,
            search_depth="advanced",
            max_results=5,
            include_answer=False,
            include_raw_content=False,
            include_images=False
        )
        
        results = response.get("results", [])
        logger.info(f"Tavily 검색 결과: {len(results)}개 웹 페이지 발견")
        
        if results and settings.OPENAI_API_KEY:
            # LLM을 사용하여 검색 결과에서 레시피 추출
            recipes = _parse_tavily_results_with_llm(results, ingredients)
            if recipes:
                logger.info(f"Tavily 검색으로 {len(recipes)}개 레시피 추출 완료")
                return recipes
            else:
                logger.warning("Tavily 검색 결과가 없거나 OpenAI API 키가 설정되지 않았습니다.")
        else:
            logger.warning("Tavily 검색 결과가 없거나 OpenAI API 키가 설정되지 않았습니다.")
        
        return []
        
    except ImportError:
        logger.warning("tavily-python 패키지가 설치되지 않았습니다.")
        return []
    except Exception as e:
        logger.error(f"Tavily Search API 오류: {e}")
        return []


def _parse_tavily_results_with_llm(search_results: List[Dict], ingredients: List[str]) -> List[Dict[str, Any]]:
    """
    Tavily 검색 결과를 LLM으로 파싱하여 레시피 추출
    """
    if not settings.OPENAI_API_KEY:
        return []
    
    try:
        # 검색 결과 요약
        search_content = []
        for i, result in enumerate(search_results[:5], 1):  # 최대 5개 결과만 사용
            title = result.get("title", "")
            content = result.get("content", "")[:500]  # 내용은 500자로 제한
            search_content.append(f"{i}. {title}\n{content}")
        
        search_text = "\n\n".join(search_content)
        ingredients_str = ", ".join(ingredients)
        
        prompt = f"""다음 웹 검색 결과에서 주어진 재료로 만들 수 있는 한국 요리 레시피를 추출해주세요.

재료: {ingredients_str}

검색 결과:
{search_text}

각 레시피는 다음 정보를 포함해야 합니다:
- 레시피 이름
- 필요한 재료 목록
- 예상 조리 시간 (분)
- 난이도 (쉬움/보통/어려움)
- 상세한 조리 단계 (5단계 이상, 반드시 포함)

응답은 다음 JSON 형식으로 해주세요:
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

        # OpenAI API 호출
        messages = [
            {"role": "system", "content": "당신은 한국 요리 전문가입니다. 웹 검색 결과에서 주어진 재료로 만들 수 있는 맛있는 레시피를 추출해주세요."},
            {"role": "user", "content": prompt}
        ]
        content = _call_openai_api(messages=messages, model="gpt-4o-mini", temperature=0.7)
        
        # JSON 추출
        json_content = _extract_json_from_response(content)
        result = json.loads(json_content)
        recipes = result.get("recipes", [])
        
        # 레시피 형식 변환
        formatted_recipes = []
        for i, recipe in enumerate(recipes, 1):
            steps = recipe.get("steps", [])
            recipe_name = recipe.get("name", "레시피")
            
            # steps가 없거나 비어있으면 기본 단계 생성
            if not steps or len(steps) == 0:
                logger.warning(f"Tavily 레시피 '{recipe_name}'에 steps가 없습니다. 기본 단계를 생성합니다.")
                # 기본 단계 생성 (LLM 호출 최소화)
                steps = [
                    "재료를 준비하고 손질합니다.",
                    "양념이나 소스를 만듭니다.",
                    "팬이나 냄비에 기름을 두르고 가열합니다.",
                    "재료를 넣고 조리합니다.",
                    "완성합니다."
                ]
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
                "match_score": 0.0,
            }
            formatted_recipes.append(formatted_recipe)
        
        logger.info(f"Tavily 레시피 {len(formatted_recipes)}개 파싱 완료 (모두 steps 포함)")
        return formatted_recipes
        
    except Exception as e:
        logger.error(f"LLM 레시피 파싱 오류: {e}")
        return []

