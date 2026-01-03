"""
레시피 관련 헬퍼 함수들
"""
from typing import List, Optional, Dict, Any
import re

from app.graph.utils.ingredient_utils import normalize_ingredient_name, parse_ingredient_quantity


def adjust_ingredient_quantity(ingredient: str, original_servings: int, target_servings: int) -> str:
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
    
    name, quantity, unit = parse_ingredient_quantity(ingredient)
    
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


def classify_recipe_category(recipe_name: str, ingredients: List[str]) -> str:
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
    
    # 음료 키워드
    drink_keywords = ["주스", "스무디", "라떼", "에이드", "티", "차", "쥬스", "음료", "드링크"]
    if any(keyword in name_lower for keyword in drink_keywords):
        return "음료"
    
    # 반찬 키워드 (명확한 반찬만 반찬으로 분류)
    side_keywords = ["나물", "어묵볶음", "무침", "부침", "전", "튀김", "김치", "절임", "장아찌", "반찬"]
    # 볶음밥, 비빔밥 등은 메인요리
    if "볶음밥" in name_lower or "비빔밥" in name_lower:
        return "메인요리"
    if any(keyword in name_lower for keyword in side_keywords):
        return "반찬"
    
    # 기본값은 메인요리
    return "메인요리"


def get_recipe_image_url(recipe_name: str) -> str:
    """레시피 이름으로 Unsplash에서 음식 이미지 URL 가져오기"""
    try:
        import urllib.parse
        # Unsplash Source API (무료, API 키 불필요)
        query = urllib.parse.quote(f"{recipe_name} food korean")
        return f"https://source.unsplash.com/400x300/?{query}"
    except Exception:
        return ""

