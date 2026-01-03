"""
Application Constants
매직 넘버, 상수, 설정값 등을 정의
"""
from typing import Dict, List, Any


# ==================== 재료 대체 규칙 ====================

SUBSTITUTION_RULES: Dict[str, List[Dict[str, Any]]] = {
    "돼지고기": [
        {"ingredient": "닭고기", "reason": "비슷한 단백질류 조리법", "confidence": 0.85},
        {"ingredient": "소고기", "reason": "양념과 조리법이 유사", "confidence": 0.75},
    ],
    "소고기": [
        {"ingredient": "돼지고기", "reason": "볶음/구이에 동일하게 활용 가능", "confidence": 0.8},
        {"ingredient": "양고기", "reason": "풍미가 비슷한 적색육", "confidence": 0.6},
    ],
    "닭고기": [
        {"ingredient": "칠면조", "reason": "단백질과 식감이 유사", "confidence": 0.7},
        {"ingredient": "돼지고기", "reason": "조림/볶음에 대체 가능", "confidence": 0.65},
    ],
    "대파": [
        {"ingredient": "쪽파", "reason": "향과 식감이 유사", "confidence": 0.9},
        {"ingredient": "양파", "reason": "향미를 비슷하게 낼 수 있음", "confidence": 0.6},
    ],
    "양파": [
        {"ingredient": "대파", "reason": "기본 향을 비슷하게 낼 수 있음", "confidence": 0.6},
        {"ingredient": "샬롯", "reason": "향과 단맛이 비슷", "confidence": 0.7},
    ],
    "참기름": [
        {"ingredient": "들기름", "reason": "고소한 풍미 대체", "confidence": 0.85},
        {"ingredient": "올리브오일", "reason": "기름기 보완용", "confidence": 0.4},
    ],
}

CATEGORY_SUBSTITUTIONS: Dict[str, List[Dict[str, Any]]] = {
    "단백질": [
        {"ingredient": "두부", "reason": "식물성 단백질 대체", "confidence": 0.55},
        {"ingredient": "버섯", "reason": "식감과 감칠맛 보완", "confidence": 0.45},
    ],
    "채소": [
        {"ingredient": "양파", "reason": "기본 향과 단맛 제공", "confidence": 0.5},
        {"ingredient": "파프리카", "reason": "식감과 색감 보완", "confidence": 0.4},
    ],
    "주식": [
        {"ingredient": "면", "reason": "탄수화물 대체", "confidence": 0.45},
        {"ingredient": "감자", "reason": "전분질 대체", "confidence": 0.4},
    ],
}

# ==================== 카테고리 블랙리스트 ====================

CATEGORY_BLACKLIST_KEYWORDS: List[str] = [
    '탕후루', '에이드', '차', '티', '주스', '쥬스', '스무디', '라떼', 
    '디저트', '간식', '케이크', '쿠키', '푸딩', '마카롱', '마시멜로우', 
    '젤리', '캔디', '사탕', '초콜릿', '아이스크림', '빙수', '팥빙수', 
    '과자', '한과', '후식', '음료', '드링크'
]

# ==================== 매칭 점수 가중치 ====================

# 메인 재료 매칭 점수 가중치
MAIN_INGREDIENT_WEIGHT: float = 50.0
# 부재료 매칭 점수 가중치
SIDE_INGREDIENT_WEIGHT: float = 30.0
# 양념 매칭 점수 가중치
SEASONING_INGREDIENT_WEIGHT: float = 20.0

# ==================== 신뢰도 계산 가중치 ====================

# 신뢰도 계산 시 가중치
CONFIDENCE_MATCH_RATE_WEIGHT: float = 0.4
CONFIDENCE_MATCHING_SCORE_WEIGHT: float = 0.3
CONFIDENCE_QUALITY_SCORE_WEIGHT: float = 0.3
CONFIDENCE_NUTRITION_BONUS: float = 0.1

# ==================== 기본값 ====================

# 기본 서빙 사이즈
DEFAULT_SERVING_SIZE: int = 2
# 기본 조리 시간 (분)
DEFAULT_COOKING_TIME: int = 30
# 기본 난이도
DEFAULT_DIFFICULTY: str = "보통"

# ==================== 검증 임계값 ====================

# 영양 정보 검증 범위
NUTRITION_CALORIES_MIN: int = 50
NUTRITION_CALORIES_MAX: int = 2000
NUTRITION_CARBOHYDRATES_MAX: int = 200
NUTRITION_PROTEIN_MAX: int = 100
NUTRITION_FAT_MAX: int = 100
NUTRITION_CALCULATION_TOLERANCE: float = 0.2  # ±20% 허용

# 조리 순서 검증
MIN_COOKING_STEPS: int = 2
MIN_STEP_DESCRIPTION_LENGTH: int = 10

# 품질 점수
QUALITY_SCORE_MAX: float = 100.0
MIN_CONSISTENCY_SCORE: float = 0.7  # 70% 이상 일치하면 좋음

