"""
LangGraph Node Functions
Phase별로 분리된 노드 함수들
"""
# Phase별 모듈에서 모든 노드 함수 import
from .phase1_nodes import (
    input_ingredients,
    analyze_ingredients,
    search_recipes,
    compare_and_select_source,
    explain_recipe_selection,
    filter_recipes,
    select_recipe,
    analyze_alternatives,
    formulate_hypothesis,
)

from .phase2_nodes import (
    check_ingredients,
    web_search_substitutions,
    suggest_substitutions,
    modify_recipe_with_substitutions,
)

from .phase3_nodes import (
    analyze_nutrition,
    validate_nutrition,
    optimize_cooking_order,
    validate_cooking_order,
    validate_recipe_completeness,
)

from .phase4_nodes import (
    generate_shopping_list,
    calculate_confidence_score,
    generate_output,
    collect_user_feedback,
    generate_storage_tips,
    # 초보자 모드 Phase 4
    generate_final_output,
)

# 초보자 모드 Phase 1-3 노드 import
from .phase1_nodes import (
    search_menu_recipe,
    extract_recipe_data,
    present_ingredients_to_user,
)

from .phase2_nodes import (
    wait_for_ingredient_selection,
)

from .phase3_nodes import (
    analyze_user_situation,
    plan_substitutions,
    adapt_recipe_content,
    optimize_for_persona,
)

__all__ = [
    # Phase 1
    "input_ingredients",
    "analyze_ingredients",
    "search_recipes",
    "compare_and_select_source",
    "explain_recipe_selection",
    "filter_recipes",
    "select_recipe",
    "analyze_alternatives",
    "formulate_hypothesis",
    # Phase 2
    "check_ingredients",
    "web_search_substitutions",
    "suggest_substitutions",
    "modify_recipe_with_substitutions",
    # Phase 3
    "analyze_nutrition",
    "validate_nutrition",
    "optimize_cooking_order",
    "validate_cooking_order",
    "validate_recipe_completeness",
    # Phase 4
    "generate_shopping_list",
    "calculate_confidence_score",
    "generate_output",
    "collect_user_feedback",
    "generate_storage_tips",
    # 초보자 모드 노드들
    "search_menu_recipe",
    "extract_recipe_data",
    "present_ingredients_to_user",
    "wait_for_ingredient_selection",
    "analyze_user_situation",
    "plan_substitutions",
    "adapt_recipe_content",
    "optimize_for_persona",
    "generate_final_output",
]
