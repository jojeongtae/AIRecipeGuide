"""
한국 요리 재료 유의어 및 계층 구조 정의
재료 정규화 및 유연한 매칭을 위한 맵핑
"""
from typing import Dict, List, Set, Optional, Any


class IngredientNormalizer:
    """재료 정규화 및 유의어 매칭 클래스"""
    
    # 재료 계층 구조 (상위 개념 -> 하위 개념 리스트)
    INGREDIENT_HIERARCHY: Dict[str, List[str]] = {
        # 후추 관련 (상위: 후추 -> 하위: 후춧가루, 통후추)
        "후추": ["후춧가루", "후추가루", "통후추", "후추"],
        # 고추 관련
        "고추": ["고춧가루", "고추가루", "청양고추", "홍고추", "꽈리고추"],
        # 돼지고기 관련
        "돼지고기": [
            "목살", "삼겹살", "앞다리살", "앞다리", "뒷다리살", "뒷다리",
            "갈비", "갈비살", "돼지갈비", "돼지갈비살",
            "돼지고기안심", "돼지안심", "돼지고기장조림용",
            "제육용", "제육볶음용", "돼지고기"
        ],
        # 소고기 관련
        "소고기": [
            "소고기안심", "소안심", "소등심", "소갈비",
            "소불고기", "불고기", "한우"
        ],
        # 닭고기 관련
        "닭고기": ["닭가슴살", "닭다리", "닭날개", "닭봉", "치킨"],
        # 마늘 관련
        "마늘": ["다진마늘", "다진 마늘", "통마늘", "마늘가루"],
        # 생강 관련
        "생강": ["다진생강", "다진 생강", "통생강", "생강가루"],
        # 대파 관련
        "대파": ["다진파", "다진 파", "파", "쪽파"],
        # 계란 관련
        "계란": ["달걀", "에그", "통계란", "삶은계란"],
        # 김치 관련
        "김치": ["신김치", "새김치", "배추김치", "묵은지"],
        # 간장 관련
        "간장": ["진간장", "국간장", "양조간장"],
        # 설탕 관련
        "설탕": ["백설탕", "흑설탕", "황설탕"],
        # 물엿 관련
        "물엿": ["올리고당", "조청"],
    }
    
    # 역 매핑 생성 (하위 개념 -> 상위 개념)
    INGREDIENT_TO_STANDARD: Dict[str, str] = {}
    for standard, variants in INGREDIENT_HIERARCHY.items():
        INGREDIENT_TO_STANDARD[standard] = standard
        for variant in variants:
            INGREDIENT_TO_STANDARD[variant] = standard
    
    @classmethod
    def normalize(cls, ingredient: str) -> str:
        """
        재료를 표준어로 정규화
        예: "목살" -> "돼지고기", "후춧가루" -> "후추"
        """
        # 공백 제거 (앞뒤 공백, 중간 공백도 정리)
        normalized = ' '.join(ingredient.strip().split())
        
        # 정확히 일치하는 경우
        if normalized in cls.INGREDIENT_TO_STANDARD:
            return cls.INGREDIENT_TO_STANDARD[normalized]
        
        # 부분 일치 확인 (예: "돼지고기장조림용" -> "돼지고기")
        for variant, standard in cls.INGREDIENT_TO_STANDARD.items():
            if variant in normalized or normalized in variant:
                return standard
        
        # 매칭되지 않으면 원본 반환
        return normalized
    
    @classmethod
    def can_substitute(cls, user_ingredient: str, required_ingredient: str) -> bool:
        """
        사용자 재료가 요구 재료를 대체할 수 있는지 확인
        - 상위 개념이 하위 개념을 대체할 수 있음 (예: "돼지고기" -> "목살")
        - 같은 계층에 속하면 대체 가능 (예: "후추" <-> "후춧가루")
        """
        user_normalized = cls.normalize(user_ingredient)
        required_normalized = cls.normalize(required_ingredient)
        
        # 같은 표준어로 정규화되면 대체 가능
        if user_normalized == required_normalized:
            return True
        
        # 사용자 재료가 요구 재료의 상위 개념인지 확인
        if required_normalized in cls.INGREDIENT_HIERARCHY:
            variants = cls.INGREDIENT_HIERARCHY[required_normalized]
            if user_normalized in variants or user_ingredient in variants:
                return True
        
        # 요구 재료가 사용자 재료의 상위 개념인지 확인
        if user_normalized in cls.INGREDIENT_HIERARCHY:
            variants = cls.INGREDIENT_HIERARCHY[user_normalized]
            if required_normalized in variants or required_ingredient in variants:
                return True
        
        return False
    
    @classmethod
    def get_substitution_guidance(cls, user_ingredient: str, required_ingredient: str) -> Optional[str]:
        """
        대체 재료 사용 시 가이드 메시지 생성
        부위나 형태가 중요할 경우 안내 메시지 반환
        """
        user_normalized = cls.normalize(user_ingredient)
        required_normalized = cls.normalize(required_ingredient)
        
        # 같은 계층이지만 형태가 다른 경우
        if user_normalized == required_normalized and user_ingredient != required_ingredient:
            # 부위명이 다른 경우 (예: 목살 vs 삼겹살)
            if user_normalized in ["돼지고기", "소고기", "닭고기"]:
                return f"{user_ingredient}으로 {required_ingredient}을 대체할 수 있지만, 식감은 다를 수 있습니다."
            # 형태가 다른 경우 (예: 통후추 vs 후춧가루)
            elif "통" in required_ingredient and "가루" in user_ingredient:
                return f"{user_ingredient}으로 {required_ingredient}을 대체할 수 있습니다."
            elif "가루" in required_ingredient and "통" in user_ingredient:
                return f"{user_ingredient}으로 {required_ingredient}을 대체할 수 있습니다."
        
        return None


# LLM 호출 결과 캐싱 (메모리 기반)
_llm_cache: Dict[str, Dict[str, Any]] = {}

# LLM 기반 스마트 매칭 함수
def check_ingredient_substitution_with_llm(
    user_ingredient: str,
    required_ingredient: str,
    recipe_name: str = "",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    LLM을 사용하여 재료 대체 가능 여부 확인 (캐싱 지원)
    
    Args:
        user_ingredient: 사용자가 가진 재료
        required_ingredient: 레시피에 필요한 재료
        recipe_name: 레시피 이름 (선택적)
        api_key: OpenAI API 키 (선택적, 없으면 None 반환)
    
    Returns:
        {"can_substitute": bool, "reason": str}
    """
    if not api_key:
        return {"can_substitute": False, "reason": "API key not available"}
    
    # 캐시 키 생성 (recipe_name은 제외하여 재사용성 향상)
    cache_key = f"{user_ingredient.lower().strip()}|{required_ingredient.lower().strip()}"
    if cache_key in _llm_cache:
        return _llm_cache[cache_key]
    
    try:
        import requests
        
        prompt = f"""레시피에 필요한 재료와 사용자가 가진 재료를 비교하여 대체 가능 여부를 판단해주세요.

레시피 이름: {recipe_name if recipe_name else "일반 요리"}
필요한 재료: {required_ingredient}
사용자가 가진 재료: {user_ingredient}

질문: 사용자가 가진 '{user_ingredient}'로 레시피에 필요한 '{required_ingredient}'를 대체할 수 있나요?

다음을 고려해주세요:
1. 한국 요리에서 일반적으로 사용되는 재료 대체 관행
2. 부위명과 일반명의 관계 (예: 목살 -> 돼지고기)
3. 형태 차이 (예: 후추 -> 후춧가루, 통마늘 -> 마늘)
4. 식감이나 맛에 큰 영향을 주지 않는 경우 대체 가능

응답은 다음 JSON 형식으로 해주세요:
{{
  "can_substitute": true/false,
  "reason": "대체 가능/불가능한 이유 (한국어로 간단히)"
}}

JSON만 응답하고 다른 설명은 하지 마세요."""
        
        # OpenAI API 호출 (헤더 최소화로 헤더 불일치 문제 해결)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "당신은 한국 요리 전문가입니다. 재료 대체 가능 여부를 정확하게 판단합니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        
        # JSON 추출
        import json
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        llm_result = {
            "can_substitute": result.get("can_substitute", False),
            "reason": result.get("reason", "")
        }
        # 캐시에 저장
        _llm_cache[cache_key] = llm_result
        return llm_result
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"LLM 재료 대체 확인 오류: {e}")
        error_result = {"can_substitute": False, "reason": f"오류: {str(e)}"}
        # 오류도 캐시에 저장하여 재시도 방지
        _llm_cache[cache_key] = error_result
        return error_result

