"""
만개의레시피 크롤링 모듈
"""
from typing import List, Dict, Any, Optional
import re
import time
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from bs4 import BeautifulSoup

# 요리 도구 목록 (재료 필터링용)
COOKING_TOOLS = [
    '도마', '조리용나이프', '요리나이프', '가위', '유리볼', '요리스푼', '냄비', '프라이팬', 
    '후라이팬', '볼', '접시', '그릇', '국자', '숟가락', '젓가락', '키친타올', 
    '키친타월', '행주', '계량컵', '대접', '컵', '스푼', '궁중팬', '채반', '체',
    '웍', '웍팬', '냄비', '솥', '전골팬', '오븐팬', '쿠키팬', '유리용기', '밀폐용기'
]

# 노이즈 키워드 (재료 필터링용)
NOISE_KEYWORDS = [
    '구매', 'ingredients', '계량법', '안내', '재료', '조리도구', '인덱스', 
    'ingredient', '약간', '적당량', '기준', '생략', 'optional', '선택'
]


class RecipeCrawlerError(Exception):
    """레시피 크롤링 오류"""
    pass


def search_recipes_by_ingredients(ingredients: List[str], max_results: int = 10, user_ingredients: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    만개의레시피에서 재료 기반 레시피 검색
    
    Args:
        ingredients: 검색할 재료 목록 (메인 재료만)
        max_results: 최대 결과 개수
        user_ingredients: 사용자가 보유한 전체 재료 목록 (매칭 계산용, None이면 ingredients 사용)
    
    Returns:
        레시피 정보 리스트
    """
    if not ingredients:
        return []
    
    # 매칭 계산용 재료 목록 (전체 재료)
    match_ingredients = user_ingredients if user_ingredients else ingredients
    
    # 재료를 검색어로 변환
    search_query = " ".join(ingredients)
    
    try:
        # 만개의레시피 검색 URL
        search_url = f"https://www.10000recipe.com/recipe/list.html?q={quote_plus(search_query)}"
        
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = client.get(search_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 레시피 목록 추출
            recipe_items = soup.find_all('div', class_='common_sp_thumb')[:max_results]
            
            # 병렬 처리로 레시피 상세 정보 가져오기
            recipes = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                # 모든 레시피 파싱 작업을 스레드 풀에 제출
                future_to_item = {
                    executor.submit(_parse_recipe_item, item, match_ingredients): item
                    for item in recipe_items
                }
                
                # 완료된 작업부터 결과 수집
                for future in as_completed(future_to_item):
                    try:
                        recipe = future.result()
                        if recipe:
                            recipes.append(recipe)
                    except Exception as e:
                        # 개별 레시피 파싱 실패해도 계속 진행
                        continue
            
            return recipes
            
    except httpx.HTTPError as e:
        raise RecipeCrawlerError(f"레시피 검색 실패: {e}") from e
    except Exception as e:
        raise RecipeCrawlerError(f"크롤링 오류: {e}") from e


def _calculate_name_similarity(menu_name: str, recipe_name: str) -> float:
    """
    메뉴 이름과 레시피 이름의 유사도 계산 (0.0 ~ 1.0)
    """
    menu_name_lower = menu_name.lower().strip()
    recipe_name_lower = recipe_name.lower().strip()
    
    # 완전 일치
    if menu_name_lower == recipe_name_lower:
        return 1.0
    
    # 포함 관계 확인
    if menu_name_lower in recipe_name_lower:
        # 메뉴 이름이 레시피 이름에 포함되는 경우
        ratio = len(menu_name_lower) / len(recipe_name_lower)
        return 0.8 + (ratio * 0.2)  # 0.8 ~ 1.0
    
    if recipe_name_lower in menu_name_lower:
        # 레시피 이름이 메뉴 이름에 포함되는 경우 (부분 일치)
        ratio = len(recipe_name_lower) / len(menu_name_lower)
        return 0.6 + (ratio * 0.2)  # 0.6 ~ 0.8
    
    # 단어 단위 매칭
    menu_words = set(menu_name_lower.split())
    recipe_words = set(recipe_name_lower.split())
    
    if menu_words and recipe_words:
        common_words = menu_words & recipe_words
        if common_words:
            # 공통 단어 비율
            similarity = len(common_words) / max(len(menu_words), len(recipe_words))
            return min(0.5, similarity)  # 최대 0.5
    
    # 유사도 없음
    return 0.0


def search_recipes_by_name(menu_name: str, max_results: int = 5, user_ingredients: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    메뉴 이름으로 레시피 검색 (이름 일치도 우선 정렬)
    
    Args:
        menu_name: 검색할 메뉴 이름 (예: "파스타", "김치찌개")
        max_results: 최대 결과 개수
        user_ingredients: 사용자가 보유한 전체 재료 목록 (매칭 계산용)
    
    Returns:
        레시피 정보 리스트 (이름 일치도 높은 순으로 정렬)
    """
    # 기존 함수 재사용 (메뉴 이름을 검색어로 사용)
    recipes = search_recipes_by_ingredients([menu_name], max_results=max_results * 2, user_ingredients=user_ingredients)
    
    # 각 레시피에 이름 일치도 점수 추가
    for recipe in recipes:
        recipe_name = recipe.get("name", "")
        name_similarity = _calculate_name_similarity(menu_name, recipe_name)
        recipe["name_similarity"] = name_similarity
    
    # 이름 일치도가 높은 순으로 정렬 (내림차순)
    recipes.sort(key=lambda x: x.get("name_similarity", 0.0), reverse=True)
    
    # 상위 max_results개만 반환
    return recipes[:max_results]


def _parse_recipe_item(item, user_ingredients: List[str]) -> Optional[Dict[str, Any]]:
    """레시피 아이템 파싱"""
    try:
        # 레시피 링크 추출
        link_elem = item.find('a', class_='common_sp_link')
        if not link_elem:
            return None
        
        recipe_url = link_elem.get('href', '')
        if not recipe_url.startswith('http'):
            recipe_url = f"https://www.10000recipe.com{recipe_url}"
        
        # 레시피 이름 추출 (여러 방법 시도)
        recipe_name = None
        
        # 방법 1: common_sp_caption_tit 클래스
        name_elem = item.find('h4', class_='common_sp_caption_tit')
        if name_elem:
            recipe_name = name_elem.get_text(strip=True)
        
        # 방법 2: common_sp_caption 클래스 내부
        if not recipe_name:
            caption_elem = item.find('div', class_='common_sp_caption')
            if caption_elem:
                name_elem = caption_elem.find(['h3', 'h4', 'h5', 'a', 'span'])
                if name_elem:
                    recipe_name = name_elem.get_text(strip=True)
        
        # 방법 3: 링크 내부의 텍스트
        if not recipe_name:
            link_elem = item.find('a', class_='common_sp_link')
            if link_elem:
                # 링크 내부의 모든 텍스트 추출
                link_text = link_elem.get_text(strip=True)
                if link_text and len(link_text) > 2:
                    recipe_name = link_text
        
        # 방법 4: 링크의 title 속성
        if not recipe_name:
            link_elem = item.find('a')
            if link_elem:
                recipe_name = link_elem.get('title', '')
        
        # 방법 5: 이미지 alt 속성
        if not recipe_name:
            img_elem = item.find('img')
            if img_elem:
                recipe_name = img_elem.get('alt', '')
        
        # 방법 6: URL에서 추출 (마지막 수단)
        if not recipe_name or recipe_name == "레시피":
            # URL에서 레시피 ID 추출 후 상세 페이지에서 가져오기
            recipe_id = recipe_url.split('/')[-1] if recipe_url else ""
            if recipe_id:
                recipe_name = f"레시피 {recipe_id}"
            else:
                recipe_name = "레시피"
        
        # 레시피 목록에서 이미지 미리 추출 시도
        list_image = ""
        img_elem = item.find('img')
        if img_elem:
            list_image = img_elem.get('src', '') or img_elem.get('data-src', '')
            if list_image:
                if list_image.startswith('//'):
                    list_image = 'https:' + list_image
                elif list_image.startswith('/'):
                    list_image = 'https://www.10000recipe.com' + list_image
        
        # 레시피 상세 정보 가져오기
        recipe_detail = _fetch_recipe_detail(recipe_url)
        
        if not recipe_detail:
            return None
        
        # 상세 페이지에서 레시피 이름 다시 확인 (더 정확할 수 있음)
        if recipe_detail.get("name") and recipe_detail["name"] != "레시피":
            recipe_name = recipe_detail["name"]
        
        # 재료 매칭 점수 계산
        recipe_ingredients = recipe_detail.get("ingredients", [])
        matched_ingredients, missing_ingredients = _calculate_ingredient_match(
            user_ingredients, recipe_ingredients
        )
        
        match_score = len(matched_ingredients) / len(recipe_ingredients) if recipe_ingredients else 0.0
        
        # 이미지 우선순위: 상세 페이지 > 목록 페이지
        final_image = recipe_detail.get("image", "") or list_image
        
        return {
            "id": recipe_url.split('/')[-1] if recipe_url else "",
            "name": recipe_name,
            "url": recipe_url,
            "ingredients": recipe_ingredients,
            "matched_ingredients": matched_ingredients,
            "missing_ingredients": missing_ingredients,
            "match_score": match_score,
            "cooking_time": recipe_detail.get("cooking_time", 0),
            "difficulty": recipe_detail.get("difficulty", "보통"),
            "level": recipe_detail.get("difficulty", "보통"),
            "steps": recipe_detail.get("steps", []),
            "image": final_image,
            "serving_size": recipe_detail.get("serving_size", 2),  # 기본값 2인분
        }
    except Exception:
        return None


def _fetch_recipe_detail(recipe_url: str) -> Optional[Dict[str, Any]]:
    """레시피 상세 정보 가져오기"""
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = client.get(recipe_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 레시피 이름 추출 (상세 페이지에서)
            recipe_name = None
            name_elem = soup.find('div', class_='view2_summary_info')
            if name_elem:
                h3_elem = name_elem.find('h3')
                if h3_elem:
                    recipe_name = h3_elem.get_text(strip=True)
            
            if not recipe_name:
                name_elem = soup.find('h3', class_=re.compile(r'.*tit.*|.*name.*', re.I))
                if name_elem:
                    recipe_name = name_elem.get_text(strip=True)
            
            if not recipe_name:
                title_elem = soup.find('title')
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    # "레시피명 | 만개의레시피" 형식에서 레시피명 추출
                    recipe_name = title_text.split('|')[0].strip() if '|' in title_text else title_text
            
            # 재료 추출 (여러 방법 시도)
            ingredients = []
            
            def clean_ingredient_name(name: str) -> str:
                """재료명 정리 함수"""
                if not name:
                    return ""
                # 끝에 있는 기호 제거 (., /, ~, 등)
                name = re.sub(r'[\.\/\~\~]+$', '', name).strip()
                # 앞뒤 공백 제거
                name = name.strip()
                
                # 불필요한 텍스트 제거 (생략가능, 구매 등)
                name = re.sub(r'\s*생략\s*가능\s*', '', name, flags=re.IGNORECASE)
                name = re.sub(r'\s*생략\s*', '', name, flags=re.IGNORECASE)
                name = re.sub(r'\s*optional\s*', '', name, flags=re.IGNORECASE)
                name = re.sub(r'\s*선택\s*', '', name, flags=re.IGNORECASE)
                name = re.sub(r'\s*구매\s*', '', name, flags=re.IGNORECASE)
                
                return name.strip()
            
            def normalize_ingredient(name: str) -> str:
                """재료명 정규화 (중복 제거용) - 수량 표현 제거 및 핵심 재료명 추출"""
                if not name:
                    return ""
                # 수량 표현 제거 (조금, 약간, 적당량 등)
                # 재료명 앞이나 뒤에 붙어있는 수량 표현 제거
                name = re.sub(r'^조금\s*', '', name, flags=re.IGNORECASE)
                name = re.sub(r'\s*조금$', '', name, flags=re.IGNORECASE)
                name = re.sub(r'^약간\s*', '', name, flags=re.IGNORECASE)
                name = re.sub(r'\s*약간$', '', name, flags=re.IGNORECASE)
                name = re.sub(r'^적당량\s*', '', name, flags=re.IGNORECASE)
                name = re.sub(r'\s*적당량$', '', name, flags=re.IGNORECASE)
                # 숫자로 시작하는 수량 패턴 제거
                name = re.sub(r'^\d+[가-힣a-zA-Z]*\s*', '', name)
                name = re.sub(r'\s*\d+[가-힣a-zA-Z]*$', '', name)
                
                # 핵심 재료명 추출 (설명성 텍스트 제거)
                # 예: "닭고기 정육뼈를 발라 살만 있는 닭고기" -> "닭고기"
                # 예: "뼈를 발라 살만 있는 닭고기" -> "닭고기"
                # 일반적인 재료명 패턴 (고기, 채소, 양념 등)
                core_ingredient_patterns = [
                    r'([가-힣]+고기)',  # 돼지고기, 닭고기, 소고기 등
                    r'([가-힣]+채소)',  # 양배추, 배추 등
                    r'([가-힣]+나물)',  # 콩나물, 숙주나물 등
                    r'([가-힣]+유)',    # 참기름, 올리브유 등
                    r'([가-힣]+가루)',  # 고춧가루, 설탕가루 등
                    r'([가-힣]+장)',    # 간장, 된장 등
                    r'([가-힣]+)',      # 일반 재료명 (마지막)
                ]
                
                for pattern in core_ingredient_patterns:
                    match = re.search(pattern, name)
                    if match:
                        core_name = match.group(1)
                        # 너무 짧은 단어 제외 (1글자)
                        if len(core_name) > 1:
                            name = core_name
                            break
                
                # 끝 기호 제거 후 소문자로 변환
                cleaned = clean_ingredient_name(name).lower()
                return cleaned
            
            # 방법 1: ready_ingre_list 클래스
            ingredient_sections = soup.find_all('div', class_='ready_ingre_list')
            for section in ingredient_sections:
                items = section.find_all('li')
                for item in items:
                        ing_text = item.get_text(strip=True)
                        if ing_text:
                            # "또는", "or"로 시작하는 항목 제외 (이전 항목의 일부)
                            ing_text_lower = ing_text.lower().strip()
                            if ing_text_lower.startswith(('또는', 'or ')):
                                continue
                            
                            # 수량 정보 보존 (원본 텍스트 유지)
                            ing_display = clean_ingredient_name(ing_text)
                            # 매칭용 재료명 추출 (수량 제거)
                            ing_name = re.sub(r'\d+[가-힣a-zA-Z]*\s*', '', ing_text).strip()
                            ing_name = clean_ingredient_name(ing_name)
                            if ing_name:
                                # 중복 체크 (재료명 기준)
                                normalized = normalize_ingredient(ing_name)
                                # "조금", "약간"만 있는 경우 제외
                                if not normalized or normalized in ['조금', '약간', '적당량']:
                                    continue
                                existing_normalized = [normalize_ingredient(re.sub(r'\d+[가-힣a-zA-Z]*\s*', '', ing).strip()) for ing in ingredients]
                                if normalized not in existing_normalized:
                                    # 노이즈 제거 (대소문자 구분 없이)
                                    ing_name_lower = ing_name.lower()
                                    
                                    # 요리 도구 제외 (부분 문자열 체크)
                                    if any(tool in ing_name for tool in COOKING_TOOLS):
                                        continue
                                    
                                    # 노이즈 키워드 제외
                                    if not any(noise in ing_name_lower for noise in NOISE_KEYWORDS) and len(ing_name) > 1:
                                        # 수량 정보 포함하여 저장
                                        ingredients.append(ing_display)
            
            # 방법 2: 다른 클래스명 시도
            if not ingredients:
                ingredient_divs = soup.find_all('div', class_=re.compile(r'.*ingre.*', re.I))
                for div in ingredient_divs:
                    items = div.find_all(['li', 'span', 'div'])
                    for item in items:
                        ing_text = item.get_text(strip=True)
                        if ing_text and len(ing_text) < 50:  # 너무 긴 텍스트 제외
                            # "또는", "or"로 시작하는 항목 제외 (이전 항목의 일부)
                            ing_text_lower = ing_text.lower().strip()
                            if ing_text_lower.startswith(('또는', 'or ')):
                                continue
                            
                            # 수량 정보 보존 (원본 텍스트 유지)
                            ing_display = clean_ingredient_name(ing_text)
                            # 매칭용 재료명 추출 (수량 제거)
                            ing_name = re.sub(r'\d+[가-힣a-zA-Z]*\s*', '', ing_text).strip()
                            ing_name = clean_ingredient_name(ing_name)
                            if ing_name:
                                # 중복 체크 (재료명 기준)
                                normalized = normalize_ingredient(ing_name)
                                # "조금", "약간"만 있는 경우 제외
                                if not normalized or normalized in ['조금', '약간', '적당량']:
                                    continue
                                existing_normalized = [normalize_ingredient(re.sub(r'\d+[가-힣a-zA-Z]*\s*', '', ing).strip()) for ing in ingredients]
                                if normalized not in existing_normalized:
                                        # 노이즈 제거 (대소문자 구분 없이)
                                        ing_name_lower = ing_name.lower()
                                        
                                        # 요리 도구 제외 (부분 문자열 체크)
                                        if any(tool in ing_name for tool in COOKING_TOOLS):
                                            continue
                                        
                                        # 노이즈 키워드 제외
                                        if not any(noise in ing_name_lower for noise in NOISE_KEYWORDS):
                                            if len(ing_name) > 1:
                                                # 수량 정보 포함하여 저장
                                                ingredients.append(ing_display)
            
            # 방법 3: 테이블 형식
            if not ingredients:
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        for cell in cells:
                            text = cell.get_text(strip=True)
                            if text and len(text) < 30:
                                # "또는", "or"로 시작하는 항목 제외 (이전 항목의 일부)
                                text_lower = text.lower().strip()
                                if text_lower.startswith(('또는', 'or ')):
                                    continue
                                
                                # 수량 정보 보존 (원본 텍스트 유지)
                                ing_display = clean_ingredient_name(text)
                                # 매칭용 재료명 추출 (수량 제거)
                                ing_name = re.sub(r'\d+[가-힣a-zA-Z]*\s*', '', text).strip()
                                ing_name = clean_ingredient_name(ing_name)
                                if ing_name:
                                    # 중복 체크 (재료명 기준)
                                    normalized = normalize_ingredient(ing_name)
                                    # "조금", "약간"만 있는 경우 제외
                                    if not normalized or normalized in ['조금', '약간', '적당량']:
                                        continue
                                    existing_normalized = [normalize_ingredient(re.sub(r'\d+[가-힣a-zA-Z]*\s*', '', ing).strip()) for ing in ingredients]
                                    if normalized not in existing_normalized:
                                        # 노이즈 제거 (대소문자 구분 없이)
                                        ing_name_lower = ing_name.lower()
                                        
                                        # 요리 도구 제외 (부분 문자열 체크)
                                        if any(tool in ing_name for tool in COOKING_TOOLS):
                                            continue
                                        
                                        # 노이즈 키워드 제외
                                        if not any(noise in ing_name_lower for noise in NOISE_KEYWORDS) and len(ing_name) > 1:
                                            # 수량 정보 포함하여 저장
                                            ingredients.append(ing_display)
            
            # 최종 중복 제거 및 정리 (재료명 기준으로 중복 제거)
            final_ingredients = []
            seen_normalized = set()
            for ing in ingredients:
                # 재료명만 추출하여 중복 체크
                ing_name_only = re.sub(r'\d+[가-힣a-zA-Z]*\s*', '', ing).strip()
                normalized = normalize_ingredient(ing_name_only)
                if normalized and normalized not in seen_normalized and len(normalized) > 1:
                    final_ingredients.append(ing)
                    seen_normalized.add(normalized)
            
            ingredients = final_ingredients
            
            # 조리 순서 추출 (여러 방법 시도)
            steps = []
            
            # 방법 1: view_step_cont 클래스 직접 찾기 (가장 정확 - 각 단계별로 분리됨)
            step_cont_items = soup.find_all('div', class_='view_step_cont')
            if step_cont_items:
                for step_cont in step_cont_items:
                    # step_cont 내부의 텍스트만 추출
                    step_text = step_cont.get_text(separator=' ', strip=True)
                    
                    # 노이즈 제거
                    if step_text and len(step_text) > 10:
                        # 불필요한 텍스트 제거
                        step_text = re.sub(r'조리순서Steps?', '', step_text, flags=re.I)
                        step_text = re.sub(r'원본보기', '', step_text)
                        step_text = re.sub(r'관련 상품.*', '', step_text)
                        step_text = re.sub(r'레시피 작성자.*', '', step_text)
                        step_text = re.sub(r'About the writer.*', '', step_text, flags=re.I)
                        step_text = re.sub(r'#\w+', '', step_text)  # 해시태그 제거
                        step_text = re.sub(r'\.\.\.+', '', step_text)  # 연속된 점 제거
                        step_text = re.sub(r'\s+', ' ', step_text)  # 여러 공백을 하나로
                        step_text = step_text.strip()
                        if step_text and len(step_text) > 5:
                            steps.append(step_text)
            
            # 방법 2: view_step 클래스에서 각 단계 추출
            if not steps:
                step_items = soup.find_all('div', class_='view_step')
                for step in step_items:
                    # view_step_cont 내부의 텍스트만 추출
                    step_cont = step.find('div', class_='view_step_cont')
                    if step_cont:
                        step_text = step_cont.get_text(separator=' ', strip=True)
                    else:
                        step_text = step.get_text(separator=' ', strip=True)
                    
                    # 노이즈 제거
                    if step_text and len(step_text) > 10:
                        step_text = re.sub(r'조리순서Steps?', '', step_text, flags=re.I)
                        step_text = re.sub(r'원본보기', '', step_text)
                        step_text = re.sub(r'관련 상품.*', '', step_text)
                        step_text = re.sub(r'레시피 작성자.*', '', step_text)
                        step_text = re.sub(r'About the writer.*', '', step_text, flags=re.I)
                        step_text = re.sub(r'#\w+', '', step_text)
                        step_text = re.sub(r'\.\.\.+', '', step_text)
                        step_text = re.sub(r'\s+', ' ', step_text)
                        step_text = step_text.strip()
                        if step_text and len(step_text) > 5:
                            steps.append(step_text)
            
            # 방법 3: step_num과 step_txt 조합
            if not steps:
                step_nums = soup.find_all('div', class_='step_num')
                for step_num in step_nums:
                    step_txt = step_num.find_next_sibling('div', class_='step_txt')
                    if step_txt:
                        step_text = step_txt.get_text(strip=True)
                        if step_text and len(step_text) > 10:
                            steps.append(step_text)
            
            # 방법 4: 다른 클래스명 시도
            if not steps:
                step_divs = soup.find_all('div', class_=re.compile(r'.*step.*', re.I))
                for step_div in step_divs:
                    step_text = step_div.get_text(strip=True)
                    if step_text and len(step_text) > 10:
                        # 노이즈 제거
                        step_text = re.sub(r'조리순서Steps?', '', step_text, flags=re.I)
                        step_text = re.sub(r'원본보기', '', step_text)
                        step_text = step_text.strip()
                        if step_text:
                            steps.append(step_text)
            
            # 방법 5: 번호가 있는 리스트
            if not steps:
                ol_items = soup.find_all('ol')
                for ol in ol_items:
                    li_items = ol.find_all('li')
                    for li in li_items:
                        step_text = li.get_text(strip=True)
                        if step_text and len(step_text) > 10:
                            steps.append(step_text)
            
            # 중복 제거 및 정리
            unique_steps = []
            seen = set()
            for step in steps:
                step_clean = step.strip()
                if step_clean and step_clean not in seen and len(step_clean) > 10:
                    # 너무 짧거나 의미없는 텍스트 제외
                    skip_patterns = ['관련 상품', '레시피 작성자', 'About the writer', '원본보기', 
                                   '맛보장 레시피', '더보기', '레시피 작성자', 'http://', 'https://',
                                   '#돼지고기', '#김치', '#찌개', '#조림', '#찜']
                    if not any(skip in step_clean for skip in skip_patterns):
                        # URL 제거
                        step_clean = re.sub(r'https?://[^\s]+', '', step_clean)
                        step_clean = re.sub(r'www\.[^\s]+', '', step_clean)
                        step_clean = step_clean.strip()
                        if step_clean and len(step_clean) > 10:
                            unique_steps.append(step_clean)
                            seen.add(step_clean)
            
            steps = unique_steps
            
            # 조리 시간 추출
            cooking_time = 0
            time_elem = soup.find('span', class_='view2_summary_info2')
            if time_elem:
                time_text = time_elem.get_text(strip=True)
                # "30분" 형식에서 숫자 추출
                time_match = re.search(r'(\d+)', time_text)
                if time_match:
                    cooking_time = int(time_match.group(1))
            
            # 만개의레시피에는 영양정보가 없으므로 LLM으로 계산 (나중에 analyze_nutrition 노드에서 처리)
            
            # 이미지 추출 (여러 방법 시도)
            image = ""
            
            # 방법 1: ready_ingre_img 클래스 (재료 이미지)
            img_elem = soup.find('img', class_='ready_ingre_img')
            if img_elem:
                image = img_elem.get('src', '')
            
            # 방법 2: 레시피 대표 이미지 (view_pic 클래스)
            if not image:
                view_pic = soup.find('div', class_='view_pic')
                if view_pic:
                    img_elem = view_pic.find('img')
                    if img_elem:
                        image = img_elem.get('src', '') or img_elem.get('data-src', '')
            
            # 방법 3: og:image 메타 태그
            if not image:
                og_image = soup.find('meta', property='og:image')
                if og_image:
                    image = og_image.get('content', '')
            
            # 방법 4: 일반적인 레시피 이미지 클래스
            if not image:
                img_elem = soup.find('img', class_=re.compile(r'.*recipe.*|.*food.*|.*dish.*', re.I))
                if img_elem:
                    image = img_elem.get('src', '') or img_elem.get('data-src', '')
            
            # 방법 5: 첫 번째 큰 이미지 (일반적으로 레시피 이미지)
            if not image:
                all_imgs = soup.find_all('img')
                for img in all_imgs:
                    src = img.get('src', '') or img.get('data-src', '')
                    # 작은 아이콘이나 로고 제외
                    if src and ('recipe' in src.lower() or 'food' in src.lower() or 'dish' in src.lower()):
                        # 상대 경로를 절대 경로로 변환
                        if src.startswith('//'):
                            image = 'https:' + src
                        elif src.startswith('/'):
                            image = 'https://www.10000recipe.com' + src
                        else:
                            image = src
                        break
            
            # 이미지 URL 정규화
            if image:
                if image.startswith('//'):
                    image = 'https:' + image
                elif image.startswith('/'):
                    image = 'https://www.10000recipe.com' + image
                elif not image.startswith('http'):
                    image = 'https://www.10000recipe.com' + image
            
            return {
                "name": recipe_name or "레시피",
                "ingredients": ingredients,
                "steps": steps,
                "cooking_time": cooking_time,
                "difficulty": "보통",  # 만개의레시피에서 난이도 정보가 명확하지 않음
                "image": image,
                "serving_size": 2,  # 기본값 2인분
            }
    except Exception:
        return None


def _calculate_ingredient_match(
    user_ingredients: List[str], 
    recipe_ingredients: List[str]
) -> tuple[List[str], List[str]]:
    """재료 매칭 계산 (IngredientNormalizer 사용)"""
    from app.utils.ingredient_map import IngredientNormalizer
    
    matched = []
    missing = []
    
    for recipe_ing in recipe_ingredients:
        found = False
        recipe_ing_normalized = recipe_ing.lower().strip()
        
        for user_ing in user_ingredients:
            user_ing_normalized = user_ing.lower().strip()
            
            # IngredientNormalizer를 사용한 동의어 매칭
            if IngredientNormalizer.can_substitute(user_ing_normalized, recipe_ing_normalized):
                matched.append(recipe_ing)
                found = True
                break
            
            # 부분 일치 확인 (fallback)
            if not found and (user_ing_normalized in recipe_ing_normalized or recipe_ing_normalized in user_ing_normalized):
                matched.append(recipe_ing)
                found = True
                break
        
        if not found:
            missing.append(recipe_ing)
    
    return matched, missing

