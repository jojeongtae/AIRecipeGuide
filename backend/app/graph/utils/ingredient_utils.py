"""
재료 관련 헬퍼 함수들
"""
import re
from typing import List, Optional, Tuple

from app.utils.ingredient_map import IngredientNormalizer
from app.constants import (
    MAIN_INGREDIENT_WEIGHT,
    SIDE_INGREDIENT_WEIGHT,
    SEASONING_INGREDIENT_WEIGHT
)


def normalize_ingredient_name(name: str) -> str:
    """재료명 정규화 (괄호 제거, 공백 정리)"""
    if not name:
        return ""
    normalized = re.sub(r'\([^)]*\)', '', name).strip()
    normalized = ' '.join(normalized.split())
    return normalized


def parse_ingredient_quantity(ingredient: str) -> Tuple[str, Optional[float], Optional[str]]:
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


def categorize_ingredient(ingredient: str) -> str:
    """
    재료를 카테고리로 분류 (메인 재료, 부재료, 양념)
    
    Returns:
        "main" (메인 재료), "side" (부재료), "seasoning" (양념)
    """
    normalized = normalize_ingredient_name(ingredient).lower()
    
    # 메인 재료 (50점)
    main_keywords = {
        # 고기류
        "돼지고기", "돼지", "삼겹살", "목살", "앞다리", "뒷다리", "갈비", "갈비살",
        "소고기", "소", "한우", "쇠고기", "등심", "안심", "갈비살", "불고기",
        "닭고기", "닭", "치킨", "닭가슴살", "닭다리", "닭날개", "닭봉",
        "오리고기", "오리",
        "햄", "베이컨", "소시지", "스팸",
        # 생선류
        "고등어", "연어", "참치", "삼치", "꽁치", "멸치", "오징어", "문어", "새우", "게", "조개",
        "전복", "소라", "바지락", "홍합", "굴",
        # 계란
        "계란", "달걀", "계란후라이", "스크램블",
        # 두부
        "두부", "연두부", "부침두부",
        # 해조류
        "김", "미역", "다시마", "톳",
        # 곡물/면류
        "밥", "라면", "스파게티", "파스타", "떡", "만두피", "국수", "소면", "우동면", "우동",
        # 유제품
        "우유", "치즈", "생크림", "요구르트",
        # 기타 메인 재료
        "콩", "견과류", "건조과일", "김치",
    }
    
    # 양념류 (20점)
    seasoning_keywords = {
        "소금", "후추", "설탕", "식초", "간장", "된장", "고춧가루", "고추장", "쌈장",
        "마늘", "생강", "파", "대파", "쪽파", "양파", "고추", "청양고추",
        "참기름", "들기름", "식용유", "올리브오일", "버터", "마요네즈",
        "물엿", "올리고당", "매실청", "꿀",
        "다진마늘", "다진생강", "다진파",
        # 양념 추가
        "케첩", "머스타드", "레몬즙", "라임즙",
        # 조미료 추가
        "맛술", "청주", "와인", "카레가루", "커리파우더",
        # 향신료 추가
        "고수", "바질", "로즈마리", "타임", "오레가노", "파프리카파우더", 
        "칠리파우더", "카이엔페퍼", "커민", "코리앤더",
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


def identify_main_ingredient(ingredients: List[str]) -> str:
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
    normalized_ingredients = [normalize_ingredient_name(ing) for ing in ingredients]
    
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


def calculate_intelligent_matching_score(
    user_ingredients: List[str],
    recipe_ingredients: List[str]
) -> float:
    """
    지능형 매칭 점수 계산 (0.0 ~ 100.0)
    
    가중치 구조:
    - 메인 재료 일치: 최대 50점
    - 나머지 재료 일치: 최대 50점 (부재료 30점 + 양념 20점)
    
    Args:
        user_ingredients: 사용자가 보유한 재료 리스트
        recipe_ingredients: 레시피에 필요한 재료 리스트
    
    Returns:
        매칭 점수 (0.0 ~ 100.0)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    user_ingredients_normalized = [normalize_ingredient_name(ing) for ing in user_ingredients]
    recipe_ingredients_normalized = [normalize_ingredient_name(ing) for ing in recipe_ingredients]
    
    # 각 카테고리별 매칭 계산
    main_matched = 0
    main_total = 0
    side_matched = 0
    side_total = 0
    seasoning_matched = 0
    seasoning_total = 0
    
    for recipe_ing in recipe_ingredients_normalized:
        category = categorize_ingredient(recipe_ing)
        
        # 사용자 재료와 매칭 확인 (동의어 처리 포함)
        matched = False
        for user_ing in user_ingredients_normalized:
            if IngredientNormalizer.can_substitute(user_ing, recipe_ing):
                matched = True
                break
            # 문자열 포함 체크 (fallback)
            if not matched and (user_ing in recipe_ing or recipe_ing in user_ing):
                matched = True
                break
        
        # 카테고리별 카운트
        if category == "main":
            main_total += 1
            if matched:
                main_matched += 1
        elif category == "seasoning":
            seasoning_total += 1
            if matched:
                seasoning_matched += 1
        else:  # side
            side_total += 1
            if matched:
                side_matched += 1
    
    # 가중치 적용하여 점수 계산
    main_score = (main_matched / main_total * MAIN_INGREDIENT_WEIGHT) if main_total > 0 else 0
    side_score = (side_matched / side_total * SIDE_INGREDIENT_WEIGHT) if side_total > 0 else 0
    seasoning_score = (seasoning_matched / seasoning_total * SEASONING_INGREDIENT_WEIGHT) if seasoning_total > 0 else 0
    remaining_score = side_score + seasoning_score  # 나머지 합계 (최대 50점)
    
    total_score = main_score + remaining_score
    
    logger.info(f"매칭 점수 계산: 메인({main_matched}/{main_total})={main_score:.1f}, "
                f"부재료({side_matched}/{side_total})={side_score:.1f}, "
                f"양념({seasoning_matched}/{seasoning_total})={seasoning_score:.1f}, "
                f"나머지합계={remaining_score:.1f}, 총점={total_score:.1f}")
    
    return total_score

