"""
DB 확인 스크립트
레시피 데이터가 정상적으로 저장되었는지 확인
"""
import sys
import os

# backend 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.db import Recipe, RecipeSearchCache, UserSearchHistory, IngredientMatchingCache
from sqlalchemy import func

def check_database():
    """DB에 저장된 데이터 확인"""
    try:
        db = SessionLocal()
        
        print("=" * 60)
        print("DB 데이터 확인")
        print("=" * 60)
        
        # 1. 레시피 테이블
        recipe_count = db.query(func.count(Recipe.id)).scalar()
        print(f"\n📋 레시피 테이블 (recipes):")
        print(f"   총 레시피 수: {recipe_count}")
        
        if recipe_count > 0:
            recent_recipes = db.query(Recipe).order_by(Recipe.created_at.desc()).limit(5).all()
            print(f"\n   최근 저장된 레시피 (최대 5개):")
            for recipe in recent_recipes:
                print(f"   - {recipe.name} (ID: {recipe.id}, 소스: {recipe.source_type}, 생성일: {recipe.created_at})")
        
        # 2. 검색 캐시 테이블
        cache_count = db.query(func.count(RecipeSearchCache.id)).scalar()
        print(f"\n💾 검색 캐시 테이블 (recipe_search_cache):")
        print(f"   총 캐시 수: {cache_count}")
        
        if cache_count > 0:
            recent_caches = db.query(RecipeSearchCache).order_by(RecipeSearchCache.search_timestamp.desc()).limit(5).all()
            print(f"\n   최근 검색 캐시 (최대 5개):")
            for cache in recent_caches:
                print(f"   - 재료: {', '.join(cache.ingredients[:3])}... (레시피 {len(cache.recipe_ids)}개, 조회수: {cache.hit_count}, 생성일: {cache.search_timestamp})")
        
        # 3. 사용자 검색 히스토리 테이블
        history_count = db.query(func.count(UserSearchHistory.id)).scalar()
        print(f"\n📜 검색 히스토리 테이블 (user_search_history):")
        print(f"   총 히스토리 수: {history_count}")
        
        # 4. 재료 매칭 캐시 테이블
        matching_count = db.query(func.count(IngredientMatchingCache.id)).scalar()
        print(f"\n🔗 재료 매칭 캐시 테이블 (ingredient_matching_cache):")
        print(f"   총 매칭 캐시 수: {matching_count}")
        
        print("\n" + "=" * 60)
        print("확인 완료")
        print("=" * 60)
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()

