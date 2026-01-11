"""
LangGraph State Schema
"""
from typing import TypedDict, List, Optional, Dict, Any
from enum import Enum


class Difficulty(str, Enum):
    """요리 난이도"""
    EASY = "쉬움"
    MEDIUM = "보통"
    HARD = "어려움"


class UserPersona(str, Enum):
    """사용자 페르소나"""
    BEGINNER = "beginner"  # 초보자
    EXPERT = "expert"  # 숙련가


class GraphState(TypedDict):
    """LangGraph 상태 스키마"""
    
    # 입력 데이터
    user_input: str  # 원본 입력 텍스트
    ingredients: List[str]  # 정규화된 재료 리스트
    ingredient_categories: Dict[str, str]  # 재료별 카테고리
    
    # 필터 조건 (선택적)
    difficulty: Optional[Difficulty]
    max_cooking_time: Optional[int]  # 분 단위
    dietary_preferences: Optional[List[str]]  # 채식, 할랄 등
    serving_size: Optional[int]  # 인분 수 (기본값: 레시피 원본 인분 수)
    category: Optional[str]  # 카테고리 (메인요리, 후식, 반찬, 국/찌개 등)
    
    # 레시피 데이터
    recipes: List[Dict[str, Any]]  # 검색된 레시피 리스트
    # 각 레시피: {
    #   "id": str,
    #   "name": str,
    #   "ingredients": List[str],
    #   "match_score": float,
    #   "difficulty": str,
    #   "cooking_time": int,
    #   "steps": List[str]
    # }
    
    search_source: Optional[str]  # 검색 소스 (tavily, crawler, llm)
    selected_recipe: Optional[Dict[str, Any]]  # 선택된 레시피
    user_choice: Optional[int]  # 사용자가 선택한 레시피 인덱스
    
    # 분석 결과
    nutrition_info: Optional[Dict[str, Any]]  # 영양 정보
    optimized_steps: Optional[List[Dict[str, Any]]]  # 최적화된 요리 단계
    
    # 재료 확인
    required_ingredients: List[str]  # 레시피에 필요한 재료
    missing_ingredients: List[str]  # 부족한 재료
    shopping_list: Optional[List[Dict[str, Any]]]  # 쇼핑 리스트
    substitution_suggestions: Optional[List[Dict[str, Any]]]  # 대체 재료 제안
    
    # 최종 출력
    final_output: Optional[Dict[str, Any]]  # 최종 결과
    
    # 에러 처리
    error: Optional[str]
    retry_count: int
    
    # Self-Correction Loop 관련
    match_rate: Optional[float]  # 재료 매칭률 (0.0 ~ 1.0)
    correction_iteration: int  # 수정 반복 횟수
    matched_ingredients: List[str]  # 매칭된 재료
    substitution_guidances: Optional[List[Dict[str, Any]]]  # 대체 재료 사용 시 가이드 메시지
    
    # Deep Research 관련 필드
    source_comparison: Optional[Dict[str, Any]]  # 소스 비교 결과 (크롤링 vs Tavily vs LLM)
    quality_score: Optional[float]  # 레시피 품질 점수 (0.0 ~ 1.0)
    validation_iteration: int  # 검증 반복 횟수
    crawler_recipes: Optional[List[Dict[str, Any]]]  # 크롤링 결과
    tavily_recipes: Optional[List[Dict[str, Any]]]  # Tavily 검색 결과
    llm_recipes: Optional[List[Dict[str, Any]]]  # LLM 생성 결과
    
    # 페르소나 및 지능형 매칭 관련 필드
    matching_score: Optional[float]  # 지능형 매칭 점수 (0.0 ~ 100.0)
    user_persona: Optional[UserPersona]  # 사용자 페르소나 (초보자/숙련가)
    storage_tips: Optional[List[Dict[str, Any]]]  # 재료 보관 팁 및 활용 팁
    
    # Explainability 관련 필드
    selection_reasoning: Optional[str]  # 레시피 선택 이유 설명
    rejection_reasons: Optional[List[Dict[str, str]]]  # 탈락 레시피와 탈락 이유
    
    # Research Hypothesis 관련 필드
    research_hypothesis: Optional[str]  # 연구 가설 (예: "재료 매칭률 ≥ 80%")
    hypothesis_validation_result: Optional[Dict[str, Any]]  # 가설 검증 결과
    
    # Confidence Score 관련 필드
    confidence_score: Optional[float]  # 최종 신뢰도 (0.0 ~ 1.0)
    confidence_breakdown: Optional[Dict[str, float]]  # 신뢰도 세부 점수
    
    # Alternative Recipe Branch 관련 필드
    alternative_recipes: Optional[List[Dict[str, Any]]]  # 대안 레시피 리스트 (상위 2-3개)
    alternative_analysis: Optional[str]  # 최종 레시피와 대안의 차이 분석
    
    # Human-in-the-loop Feedback 관련 필드
    user_feedback: Optional[Dict[str, Any]]  # 사용자 피드백 데이터
    feedback_score: Optional[int]  # 피드백 점수 (1-5)
    
    # 초보자 모드 전용 필드
    menu_name: Optional[str]  # 메뉴 이름 (예: "김치찌개")
    original_recipe: Optional[Dict[str, Any]]  # 크롤링한 원본 레시피 데이터
    structured_recipe: Optional[Dict[str, Any]]  # 구조화된 레시피 데이터
    extracted_ingredients: Optional[List[str]]  # 추출된 재료 리스트
    extracted_categories: Optional[Dict[str, str]]  # 재료별 카테고리 매핑
    ingredients_checklist: Optional[Dict[str, Any]]  # 프론트엔드용 재료 체크리스트
    grouped_ingredients: Optional[Dict[str, List[str]]]  # 카테고리별 그룹화된 재료
    estimated_match_rate: Optional[float]  # 예상 매칭률
    waiting_for_user_selection: Optional[bool]  # 사용자 입력 대기 중인지
    user_selected_ingredients: Optional[List[str]]  # 사용자가 선택한 재료 리스트
    interrupt_reason: Optional[str]  # interrupt 이유
    category_analysis: Optional[Dict[str, Any]]  # 카테고리별 분석 결과
    adapted_recipe_steps: Optional[List[Dict[str, Any]]]  # 대체재료 반영된 조리법
    adapted_ingredients: Optional[List[str]]  # 대체재료 반영된 재료 리스트
    substitution_mapping: Optional[Dict[str, str]]  # 부족 재료 → 대체재료 매핑
    substitution_details: Optional[Dict[str, Dict[str, Any]]]  # 대체재료 상세 정보
    optimized_recipe_steps: Optional[List[Dict[str, Any]]]  # 페르소나 최적화된 조리법



