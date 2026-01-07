"""
Database service layer for caching and data persistence
"""
import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.db import (
    Recipe,
    RecipeSearchCache,
    UserSearchHistory,
    IngredientMatchingCache
)

logger = logging.getLogger(__name__)


def _generate_ingredient_hash(ingredients: List[str]) -> str:
    """재료 리스트를 해시로 변환"""
    # 정렬하여 같은 재료 조합이 같은 해시를 가지도록 함
    sorted_ingredients = sorted([ing.lower().strip() for ing in ingredients])
    ingredient_str = "|".join(sorted_ingredients)
    return hashlib.sha256(ingredient_str.encode()).hexdigest()


def get_cached_search(
    db: Session,
    ingredients: List[str],
    filters: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    캐시된 검색 결과 조회
    
    Args:
        db: DB 세션
        ingredients: 재료 리스트
        filters: 필터 딕셔너리 (선택사항)
    
    Returns:
        캐시된 결과가 있으면 딕셔너리, 없으면 None
    """
    try:
        ingredient_hash = _generate_ingredient_hash(ingredients)
        
        # 만료되지 않은 캐시 조회
        cache = db.query(RecipeSearchCache).filter(
            and_(
                RecipeSearchCache.ingredient_hash == ingredient_hash,
                RecipeSearchCache.expires_at > datetime.utcnow()
            )
        ).first()
        
        if cache:
            # hit_count 증가
            cache.hit_count = (cache.hit_count or 0) + 1
            db.commit()
            
            logger.info(f"캐시 히트: {ingredient_hash[:8]}... (hit_count: {cache.hit_count})")
            
            return {
                "recipe_ids": cache.recipe_ids,
                "match_scores": cache.match_scores or {},
                "filters": cache.filters or {},
                "cached": True
            }
        
        return None
    except Exception as e:
        logger.error(f"캐시 조회 중 오류: {e}", exc_info=True)
        return None


def save_search_cache(
    db: Session,
    ingredients: List[str],
    recipe_ids: List[uuid.UUID],
    match_scores: Optional[Dict[str, float]] = None,
    filters: Optional[Dict[str, Any]] = None,
    cache_days: int = 7
) -> bool:
    """
    검색 결과를 캐시에 저장
    
    Args:
        db: DB 세션
        ingredients: 재료 리스트
        recipe_ids: 레시피 ID 리스트
        match_scores: 레시피별 매칭 점수 딕셔너리 (선택사항)
        filters: 필터 딕셔너리 (선택사항)
        cache_days: 캐시 유효 기간 (일)
    
    Returns:
        저장 성공 여부
    """
    try:
        ingredient_hash = _generate_ingredient_hash(ingredients)
        expires_at = datetime.utcnow() + timedelta(days=cache_days)
        
        # 기존 캐시가 있으면 업데이트, 없으면 생성
        cache = db.query(RecipeSearchCache).filter(
            RecipeSearchCache.ingredient_hash == ingredient_hash
        ).first()
        
        if cache:
            cache.recipe_ids = recipe_ids
            cache.match_scores = match_scores
            cache.filters = filters
            cache.expires_at = expires_at
            cache.search_timestamp = datetime.utcnow()
        else:
            cache = RecipeSearchCache(
                id=uuid.uuid4(),
                ingredient_hash=ingredient_hash,
                ingredients=ingredients,
                recipe_ids=recipe_ids,
                match_scores=match_scores,
                filters=filters,
                expires_at=expires_at,
                hit_count=0
            )
            db.add(cache)
        
        db.commit()
        logger.info(f"검색 캐시 저장 완료: {ingredient_hash[:8]}... (레시피 {len(recipe_ids)}개)")
        return True
    except Exception as e:
        logger.error(f"캐시 저장 중 오류: {e}", exc_info=True)
        db.rollback()
        return False


def save_recipe(db: Session, recipe_data: Dict[str, Any]) -> Optional[uuid.UUID]:
    """
    레시피를 DB에 저장
    
    Args:
        db: DB 세션
        recipe_data: 레시피 데이터 딕셔너리
    
    Returns:
        저장된 레시피 ID, 실패 시 None
    """
    try:
        # 기존 레시피가 있으면 업데이트, 없으면 생성
        recipe_id_raw = recipe_data.get("id")
        source_url = recipe_data.get("url") or recipe_data.get("source_url")
        
        recipe = None
        recipe_id_uuid = None
        
        # UUID 형식인지 확인
        if recipe_id_raw:
            if isinstance(recipe_id_raw, str):
                # UUID 형식인지 확인 (예: "550e8400-e29b-41d4-a716-446655440000")
                # UUID 형식: 8-4-4-4-12 하이픈 포함
                if len(recipe_id_raw) == 36 and recipe_id_raw.count('-') == 4:
                    try:
                        recipe_id_uuid = uuid.UUID(recipe_id_raw)
                        recipe = db.query(Recipe).filter(Recipe.id == recipe_id_uuid).first()
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"UUID 변환 실패 (UUID 형식이지만 유효하지 않음): {recipe_id_raw}, 오류: {e}")
                        recipe_id_uuid = None
                else:
                    # UUID 형식이 아님 (크롤러 ID 등 숫자 문자열)
                    logger.debug(f"UUID 형식이 아님 (크롤러 ID일 가능성): {recipe_id_raw}")
                    recipe_id_uuid = None
            elif isinstance(recipe_id_raw, uuid.UUID):
                recipe_id_uuid = recipe_id_raw
                recipe = db.query(Recipe).filter(Recipe.id == recipe_id_uuid).first()
        
        # UUID가 아니고 source_url로도 못 찾았으면 source_url로 다시 시도
        if not recipe and source_url:
            recipe = db.query(Recipe).filter(Recipe.source_url == source_url).first()
        
        if recipe:
            # 업데이트
            for key, value in recipe_data.items():
                if hasattr(recipe, key) and key != "id":
                    setattr(recipe, key, value)
        else:
            # 새로 생성 (UUID 형식이 아니면 새 UUID 생성)
            new_recipe_id = recipe_id_uuid if recipe_id_uuid else uuid.uuid4()
            recipe = Recipe(
                id=new_recipe_id,
                name=recipe_data.get("name", ""),
                source_type=recipe_data.get("source_type", "unknown"),
                source_url=source_url or recipe_data.get("source_url"),
                ingredients=recipe_data.get("ingredients", []),
                steps=recipe_data.get("steps", []),
                cooking_time=recipe_data.get("cooking_time"),
                difficulty=recipe_data.get("difficulty"),
                category=recipe_data.get("category"),
                serving_size=recipe_data.get("serving_size"),
                image_url=recipe_data.get("image_url") or recipe_data.get("image"),
                nutrition_info=recipe_data.get("nutrition_info"),
                tags=recipe_data.get("tags"),
                quality_score=recipe_data.get("quality_score"),
                validation_passed=recipe_data.get("validation_passed"),
                nutrition_accuracy=recipe_data.get("nutrition_accuracy"),
                step_completeness=recipe_data.get("step_completeness"),
                view_count=recipe_data.get("view_count", 0),
                select_count=recipe_data.get("select_count", 0),
                avg_match_score=recipe_data.get("avg_match_score") or recipe_data.get("match_score"),
                avg_rating=recipe_data.get("avg_rating")
            )
            db.add(recipe)
        
        db.commit()
        logger.info(f"레시피 저장 완료: {recipe.id} ({recipe.name})")
        return recipe.id
    except Exception as e:
        logger.error(f"레시피 저장 중 오류: {e}", exc_info=True)
        db.rollback()
        return None


def get_ingredient_matching(
    db: Session,
    user_ingredient: str,
    recipe_ingredient: str
) -> Optional[Dict[str, Any]]:
    """
    재료 매칭 캐시 조회
    
    Args:
        db: DB 세션
        user_ingredient: 사용자 재료
        recipe_ingredient: 레시피 재료
    
    Returns:
        캐시된 매칭 결과, 없으면 None
    """
    try:
        cache = db.query(IngredientMatchingCache).filter(
            and_(
                IngredientMatchingCache.user_ingredient == user_ingredient.lower().strip(),
                IngredientMatchingCache.recipe_ingredient == recipe_ingredient.lower().strip()
            )
        ).first()
        
        if cache:
            # hit_count 증가
            cache.hit_count = (cache.hit_count or 0) + 1
            db.commit()
            
            return {
                "match_result": cache.match_result,
                "substitution_possible": cache.substitution_possible,
                "llm_reason": cache.llm_reason,
                "cached": True
            }
        
        return None
    except Exception as e:
        logger.error(f"재료 매칭 캐시 조회 중 오류: {e}", exc_info=True)
        return None


def save_ingredient_matching(
    db: Session,
    user_ingredient: str,
    recipe_ingredient: str,
    match_result: Dict[str, Any],
    substitution_possible: Optional[bool] = None,
    llm_reason: Optional[str] = None
) -> bool:
    """
    재료 매칭 결과를 캐시에 저장
    
    Args:
        db: DB 세션
        user_ingredient: 사용자 재료
        recipe_ingredient: 레시피 재료
        match_result: 매칭 결과 딕셔너리
        substitution_possible: 대체 가능 여부 (선택사항)
        llm_reason: LLM 이유 (선택사항)
    
    Returns:
        저장 성공 여부
    """
    try:
        user_ing = user_ingredient.lower().strip()
        recipe_ing = recipe_ingredient.lower().strip()
        
        # 기존 캐시가 있으면 업데이트, 없으면 생성
        cache = db.query(IngredientMatchingCache).filter(
            and_(
                IngredientMatchingCache.user_ingredient == user_ing,
                IngredientMatchingCache.recipe_ingredient == recipe_ing
            )
        ).first()
        
        if cache:
            cache.match_result = match_result
            cache.substitution_possible = substitution_possible
            cache.llm_reason = llm_reason
        else:
            cache = IngredientMatchingCache(
                id=uuid.uuid4(),
                user_ingredient=user_ing,
                recipe_ingredient=recipe_ing,
                match_result=match_result,
                substitution_possible=substitution_possible,
                llm_reason=llm_reason,
                hit_count=0
            )
            db.add(cache)
        
        db.commit()
        logger.debug(f"재료 매칭 캐시 저장: {user_ing} <-> {recipe_ing}")
        return True
    except Exception as e:
        logger.error(f"재료 매칭 캐시 저장 중 오류: {e}", exc_info=True)
        db.rollback()
        return False


def save_search_history(
    db: Session,
    ingredients: List[str],
    filters: Optional[Dict[str, Any]] = None,
    persona: Optional[str] = None,
    selected_recipe_id: Optional[uuid.UUID] = None,
    match_score: Optional[float] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> bool:
    """
    사용자 검색 히스토리 저장
    
    Args:
        db: DB 세션
        ingredients: 재료 리스트
        filters: 필터 딕셔너리 (선택사항)
        persona: 페르소나 (선택사항)
        selected_recipe_id: 선택된 레시피 ID (선택사항)
        match_score: 매칭 점수 (선택사항)
        user_id: 사용자 ID (선택사항)
        session_id: 세션 ID (선택사항)
    
    Returns:
        저장 성공 여부
    """
    try:
        history = UserSearchHistory(
            id=uuid.uuid4(),
            user_id=user_id,
            session_id=session_id,
            ingredients=ingredients,
            filters=filters,
            persona=persona,
            selected_recipe_id=selected_recipe_id,
            match_score=match_score
        )
        db.add(history)
        db.commit()
        logger.debug(f"검색 히스토리 저장 완료: {len(ingredients)}개 재료")
        return True
    except Exception as e:
        logger.error(f"검색 히스토리 저장 중 오류: {e}", exc_info=True)
        db.rollback()
        return False

