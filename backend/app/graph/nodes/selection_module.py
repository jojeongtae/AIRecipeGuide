"""
레시피 선택 관련 함수 모듈
레시피 선택 로직 분리
"""
import logging
from typing import Dict, Any, List
from app.models.state import GraphState
from app.config import settings
from app.database import SessionLocal
from app.services.db_service import save_recipe, save_search_cache
from app.graph.utils.ingredient_utils import calculate_intelligent_matching_score
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
    
    # 소스 선택 전략
    best_source = "unknown"
    selected_recipes = []
    
    if source_scores:
        # 크롤링 결과가 있으면 우선 선택 (신뢰도 높음)
        if "crawler" in source_scores:
            crawler_data = source_scores["crawler"]
            avg_score = crawler_data["avg_match_score"]
            if avg_score >= settings.CRAWLER_PRIORITY_THRESHOLD:
                best_source = "crawler"
                selected_recipes = crawler_data["recipes"]
                logger.info(f"✅ 크롤링 결과 우선 선택: 평균 매칭 점수 {avg_score:.1f}점, 레시피 {len(selected_recipes)}개")
            else:
                # 크롤링 점수가 낮으면 다른 소스와 비교
                best_source = max(source_scores.items(), key=lambda x: x[1]["avg_match_score"])[0]
                selected_recipes = source_scores[best_source]["recipes"]
        else:
            # 크롤링 결과가 없으면 가장 높은 점수의 소스 선택
            best_source = max(source_scores.items(), key=lambda x: x[1]["avg_match_score"])[0]
            selected_recipes = source_scores[best_source]["recipes"]
    
    # 매칭 점수 임계값으로 필터링 (너무 낮은 매칭도는 제외)
    filtered_recipes = [r for r in selected_recipes if r.get("match_score", 0) >= settings.MATCH_SCORE_THRESHOLD]
    logger.info(f"매칭 점수 필터링 ({settings.MATCH_SCORE_THRESHOLD}점 이상) 후: {len(filtered_recipes)}개")
    
    # 필터링된 레시피가 없으면 매칭 점수순으로 상위 레시피 선택 (최소한 결과는 제공)
    if not filtered_recipes and selected_recipes:
        sorted_recipes = sorted(selected_recipes, key=lambda x: x.get("match_score", 0), reverse=True)
        filtered_recipes = sorted_recipes[:10]  # 최소 10개는 제공
        logger.warning(f"매칭 점수 {settings.MATCH_SCORE_THRESHOLD}점 이상 레시피가 없어 상위 10개 반환: {len(filtered_recipes)}개")
    
    if not filtered_recipes:
        # 모든 소스에서 결과가 없으면 LLM 생성 시도
        if settings.OPENAI_API_KEY:
            from app.graph.nodes.search_module import _generate_recipes_with_llm
            llm_recipes_new = _generate_recipes_with_llm(ingredients)
            if llm_recipes_new:
                # 매칭 점수 계산
                for recipe in llm_recipes_new:
                    recipe_ingredients = recipe.get("ingredients", [])
                    match_score = calculate_intelligent_matching_score(ingredients, recipe_ingredients)
                    recipe["match_score"] = match_score
                filtered_recipes = llm_recipes_new[:5]
                best_source = "llm"
                logger.info(f"LLM으로 {len(filtered_recipes)}개 레시피 생성 완료")
    
    selected_recipes = filtered_recipes
    
    # DB 저장 시도
    try:
        db = SessionLocal()
        logger.info(f"DB 저장 시작: 레시피 {len(selected_recipes)}개, 재료: {ingredients}")
        
        for recipe in selected_recipes:
            try:
                recipe_id = save_recipe(db, recipe)
                if recipe_id:
                    logger.info(f"레시피 저장 성공: {recipe.get('name', 'Unknown')} (ID: {recipe_id})")
            except Exception as e:
                logger.warning(f"레시피 저장 실패: {recipe.get('name', 'Unknown')}, 오류: {e}")
        
        # 검색 캐시 저장
        try:
            cache_id = save_search_cache(db, ingredients, selected_recipes)
            if cache_id:
                logger.info(f"검색 결과 캐시 저장 완료: {len(selected_recipes)}개 레시피")
        except Exception as e:
            logger.warning(f"검색 캐시 저장 실패: {e}")
        
        db.close()
    except Exception as e:
        logger.warning(f"DB 저장 중 오류 발생 (계속 진행): {e}")
    
    # 소스 비교 정보 생성
    source_comparison = {
        "selected_source": best_source,
        "selected_score": source_scores.get(best_source, {}).get("avg_match_score", 0) if best_source != "unknown" else 0,
        "sources": source_scores
    }
    
    # 평균 매칭 점수 계산
    if selected_recipes:
        avg_matching_score = sum(r.get("match_score", 0) for r in selected_recipes) / len(selected_recipes)
    else:
        avg_matching_score = 0.0
    
    logger.info(f"소스 선택 전 - selected_recipes: {len(selected_recipes)}, all_recipes: {len(all_recipes)}")
    logger.info(f"매칭 점수 필터링 ({settings.MATCH_SCORE_THRESHOLD}점 이상) 후: {len(selected_recipes)}개")
    logger.info(f"최종 반환할 레시피 수: {len(selected_recipes)}")
    logger.info(f"소스 비교 완료: 선택된 소스={best_source}, 레시피 수={len(selected_recipes)}, 평균 매칭률={avg_matching_score*100:.1f}%")
    logger.info(f"평균 지능형 매칭 점수: {avg_matching_score:.1f}")
    
    return {
        **state,
        "recipes": selected_recipes,
        "search_source": best_source,
        "source_comparison": source_comparison,
        "matching_score": avg_matching_score  # state에 matching_score 저장
    }

