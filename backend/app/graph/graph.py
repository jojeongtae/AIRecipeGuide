"""
LangGraph Workflow Graph - Deep Research 형 워크플로우
"""
from langgraph.graph import StateGraph, END
from app.models.state import GraphState
from app.graph.nodes import (
    input_ingredients,
    analyze_ingredients,
    search_recipes,
    filter_recipes,
    select_recipe,
    analyze_nutrition,
    optimize_cooking_order,
    check_ingredients,
    suggest_substitutions,
    generate_shopping_list,
    # generate_storage_tips,  # LLM 호출 최소화를 위해 제거
    generate_output,
    # Deep Research 노드들
    compare_and_select_source,
    web_search_substitutions,
    modify_recipe_with_substitutions,
    validate_nutrition,
    validate_cooking_order,
    validate_recipe_completeness,
    # Explainable + Research-grade 노드들
    explain_recipe_selection,
    formulate_hypothesis,
    calculate_confidence_score,
    analyze_alternatives,
    collect_user_feedback,
)


def should_wait_for_user_selection(state: GraphState) -> str:
    """레시피 개수에 따른 분기"""
    recipes = state.get("recipes", [])
    user_choice = state.get("user_choice")
    
    if len(recipes) == 0:
        return "end"
    elif len(recipes) == 1:
        return "auto_select"
    elif user_choice is not None:
        return "auto_select"
    else:
        return "wait_for_selection"


def check_ingredients_availability(state: GraphState) -> str:
    """재료 충분 여부에 따른 분기 (Self-Correction Loop) + 지능형 매칭 점수 기반 분기"""
    missing = state.get("missing_ingredients", [])
    match_rate = state.get("match_rate", 0.0)
    matching_score = state.get("matching_score", 0.0)
    correction_iteration = state.get("correction_iteration")
    
    # correction_iteration이 None이면 0으로 설정
    if correction_iteration is None:
        correction_iteration = 0
    
    # 재료가 부족하면 항상 대체재료 제안 시도
    if len(missing) > 0:
        if correction_iteration >= 3:
            return "generate_shopping_list"
        return "web_search_substitutions"
    
    # 재료가 모두 있으면 바로 쇼핑 리스트 생성
    return "generate_shopping_list"


def should_search_substitutions(state: GraphState) -> str:
    """재료 부족 시 대체재료 제안 필요 여부 결정"""
    missing = state.get("missing_ingredients", [])
    
    # 재료가 부족하면 항상 대체재료 제안 (web_search_substitutions에서 이미 웹 검색 완료)
    if len(missing) > 0:
        return "web_search"  # suggest_substitutions로 연결
    else:
        return "analyze_nutrition"


def should_retry_modification(state: GraphState) -> str:
    """레시피 수정 재시도 여부 결정 (최대 3회)"""
    correction_iteration = state.get("correction_iteration", 0)
    
    if correction_iteration >= 3:
        return "generate_shopping_list"
    
    return "check_ingredients"


def should_retry_validation(state: GraphState) -> str:
    """검증 실패 시 재시도 여부 결정"""
    validation_iteration = state.get("validation_iteration", 0)
    
    if validation_iteration >= 1:
        return "generate_output"  # 최대 1회 재시도 후 그냥 진행 (완화)
    
    return "retry_validation"


def should_retry_nutrition(state: GraphState) -> str:
    """영양 정보 검증 실패 시 재분석 여부 결정 - 검증 완화"""
    # 검증 실패해도 그냥 진행 (속도 우선)
    return "optimize_cooking_order"


def should_retry_cooking_order(state: GraphState) -> str:
    """조리 순서 검증 실패 시 재최적화 여부 결정 - 검증 완화"""
    # 검증 실패해도 그냥 진행 (속도 우선)
    return "validate_recipe_completeness"




def create_recipe_graph():
    """
    Deep Research 형 레시피 추천 그래프 생성
    
    Phase 1: 다중 소스 수집 및 교차 검증
    Phase 2: 레시피 선택 및 재료 검증
    Phase 3: 레시피 품질 검증 및 최적화
    Phase 4: 출력 생성
    """
    workflow = StateGraph(GraphState)
    
    # Phase 1: 다중 소스 수집 및 교차 검증
    workflow.add_node("input_ingredients", input_ingredients)
    workflow.add_node("analyze_ingredients", analyze_ingredients)
    workflow.add_node("search_recipes", search_recipes)
    workflow.add_node("compare_and_select_source", compare_and_select_source)
    workflow.add_node("explain_recipe_selection", explain_recipe_selection)  # Explainability 추가
    workflow.add_node("filter_recipes", filter_recipes)
    workflow.add_node("select_recipe", select_recipe)
    workflow.add_node("analyze_alternatives", analyze_alternatives)  # Alternative 분석 추가
    workflow.add_node("formulate_hypothesis", formulate_hypothesis)  # Research Hypothesis 추가
    
    # Phase 2: 레시피 선택 및 재료 검증
    workflow.add_node("check_ingredients", check_ingredients)
    workflow.add_node("web_search_substitutions", web_search_substitutions)
    workflow.add_node("suggest_substitutions", suggest_substitutions)
    workflow.add_node("modify_recipe_with_substitutions", modify_recipe_with_substitutions)
    
    # Phase 3: 레시피 품질 검증 및 최적화
    workflow.add_node("analyze_nutrition", analyze_nutrition)
    workflow.add_node("validate_nutrition", validate_nutrition)
    workflow.add_node("optimize_cooking_order", optimize_cooking_order)
    workflow.add_node("validate_cooking_order", validate_cooking_order)
    workflow.add_node("validate_recipe_completeness", validate_recipe_completeness)
    
    # Phase 4: 출력 생성
    workflow.add_node("generate_shopping_list", generate_shopping_list)
    # generate_storage_tips는 LLM 호출 최소화를 위해 제거
    workflow.add_node("calculate_confidence_score", calculate_confidence_score)  # Confidence Score 추가
    workflow.add_node("generate_output", generate_output)
    workflow.add_node("collect_user_feedback", collect_user_feedback)  # Feedback 루프 추가
    
    # 워크플로우 구성
    workflow.set_entry_point("input_ingredients")
    
    # Phase 1: 다중 소스 수집 및 교차 검증
    workflow.add_edge("input_ingredients", "analyze_ingredients")
    workflow.add_edge("analyze_ingredients", "search_recipes")
    workflow.add_edge("search_recipes", "compare_and_select_source")
    workflow.add_edge("compare_and_select_source", "explain_recipe_selection")  # Explainability 노드 추가
    workflow.add_edge("explain_recipe_selection", "filter_recipes")
    workflow.add_edge("filter_recipes", "select_recipe")
    workflow.add_edge("select_recipe", "analyze_alternatives")  # Alternative 분석 추가
    
    # 레시피 선택 분기 (analyze_alternatives 이후)
    workflow.add_conditional_edges(
        "analyze_alternatives",
        should_wait_for_user_selection,
        {
            "auto_select": "formulate_hypothesis",  # Hypothesis 노드 추가
            "wait_for_selection": END,
            "end": END
        }
    )
    
    # formulate_hypothesis 이후 check_ingredients로 연결
    workflow.add_edge("formulate_hypothesis", "check_ingredients")
    
    # Phase 2: 재료 검증 및 대체재 검색
    workflow.add_conditional_edges(
        "check_ingredients",
        check_ingredients_availability,
        {
            "analyze_nutrition": "analyze_nutrition",
            "web_search_substitutions": "web_search_substitutions",
            "generate_shopping_list": "generate_shopping_list"
        }
    )
    
    # 웹 검색 대체재 분기
    workflow.add_conditional_edges(
        "web_search_substitutions",
        should_search_substitutions,
        {
            "web_search": "suggest_substitutions",
            "analyze_nutrition": "analyze_nutrition"
        }
    )
    
    # 대체재 제안 후 레시피 수정
    workflow.add_edge("suggest_substitutions", "modify_recipe_with_substitutions")
    
    # 레시피 수정 후 재검증
    workflow.add_conditional_edges(
        "modify_recipe_with_substitutions",
        should_retry_modification,
        {
            "check_ingredients": "check_ingredients",
            "generate_shopping_list": "generate_shopping_list"
        }
    )
    
    # Phase 3: 레시피 품질 검증 및 최적화
    workflow.add_edge("analyze_nutrition", "validate_nutrition")
    
    # 영양 정보 검증 분기
    workflow.add_conditional_edges(
        "validate_nutrition",
        should_retry_nutrition,
        {
            "analyze_nutrition": "analyze_nutrition",
            "optimize_cooking_order": "optimize_cooking_order"
        }
    )
    
    workflow.add_edge("optimize_cooking_order", "validate_cooking_order")
    
    # 조리 순서 검증 분기
    workflow.add_conditional_edges(
        "validate_cooking_order",
        should_retry_cooking_order,
        {
            "optimize_cooking_order": "optimize_cooking_order",
            "validate_recipe_completeness": "validate_recipe_completeness"
        }
    )
    
    # 레시피 완성도 검증 후 출력 생성 (storage_tips 스킵하여 LLM 호출 최소화)
    workflow.add_edge("validate_recipe_completeness", "calculate_confidence_score")  # Confidence 계산 추가
    workflow.add_edge("calculate_confidence_score", "generate_output")
    
    # Phase 4: 출력 생성 (storage_tips 스킵)
    workflow.add_edge("generate_shopping_list", "calculate_confidence_score")  # Confidence 계산 추가
    workflow.add_edge("generate_output", "collect_user_feedback")  # Feedback 노드 추가
    workflow.add_edge("collect_user_feedback", END)
    
    # Recursion limit 설정 (무한 루프 방지)
    return workflow.compile(checkpointer=None).with_config({"recursion_limit": 50})


recipe_graph = create_recipe_graph()

