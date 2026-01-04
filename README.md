# 레시피 추천 시스템

보유한 재료를 기반으로 맞춤형 레시피를 추천하는 AI 기반 웹 애플리케이션입니다.  
LangGraph를 활용하여 구현한 AI Agent 서비스로, 실제 냉장고에 있는 재료만으로 요리할 수 있는 레시피를 추천합니다.

## 🌐 배포 URL

**실제 동작하는 서비스**: [https://disciplined-youthfulness-production-6532.up.railway.app/](https://disciplined-youthfulness-production-6532.up.railway.app/)

위 링크를 클릭하여 바로 서비스를 체험해보실 수 있습니다.

## 🎯 프로젝트 배경 (왜 만들었는가?)

### 문제 상황

현재 많은 사람들이 다음과 같은 이유로 배달음식을 주문하고 있습니다:

1. **자취를 하는데 요리를 할 줄 몰라서 배달음식만 시켜먹는 사람들**
   - 요리 경험이 없어 어떻게 시작해야 할지 모름
   - 레시피를 찾아도 어려워 보이거나 재료가 복잡함
   - 결과적으로 배달음식에 의존하게 됨

2. **요리를 할 줄 알지만 레시피를 몰라서 요리하기를 귀찮아서 배달 시켜먹는 사람**
   - 요리 자체는 할 수 있지만 매번 레시피를 찾는 것이 번거로움
   - 집에 있는 재료로 뭘 만들 수 있을지 모르겠음
   - 결국 편의를 위해 배달음식을 선택

### 해결책

이런 사람들을 실제로 주변에서 많이 보면서, **"냉장고에 있는 재료만으로 쉽게 만들 수 있는 레시피를 추천해주는 서비스"**가 있으면 좋겠다고 생각했습니다.

- 냉장고 재료만 입력하면 바로 추천
- 부족한 재료는 대체 재료 제안
- 초보자도 따라할 수 있는 상세한 조리 과정 제공
- 페르소나 기반 맞춤형 가이드 (초보자/숙련가)

이를 통해 **요리 진입장벽을 낮추고**, **더 많은 사람들이 집에서 요리를 즐길 수 있도록** 하는 것이 이 프로젝트의 목표입니다.

## 🛠 개발 방법론 (어떻게 만들었는가?)

### 기본 개발 방식

이 프로젝트는 기본적으로 **Cursor 에디터를 활용한 바이브 코딩**으로 작업을 진행하였습니다.

- Cursor의 AI 어시스턴트를 활용한 빠른 프로토타이핑
- 실시간 코드 생성 및 수정
- 반복적인 테스트와 개선

### 상세 로직 구현

디테일이 필요한 로직의 경우에는 다음 과정을 거쳤습니다:

1. **별도 연구 및 학습**
   - 해당 기술/알고리즘에 대한 자료를 따로 조사하고 학습
   - 관련 코드 예제 및 공식 문서 참고
   - 베스트 프랙티스 확인

2. **명확한 프롬프트 작성**
   - 조사한 내용을 바탕으로 Cursor Agent에게 프롬프트를 **더 명확하게** 전달
   - 구체적인 요구사항과 예상 동작 방식 명시
   - 에지 케이스 및 제약사항 설명

3. **반복적 개선**
   - 구현된 코드를 실제 환경에서 테스트
   - 사용자 시나리오 기반 검증
   - 점진적 리팩토링을 통한 코드 품질 향상

이런 방식으로, 기본적인 기능은 빠르게 프로토타이핑하고, 복잡한 로직은 신중하게 연구한 후 구현함으로써 **개발 속도와 코드 품질의 균형**을 맞췄습니다.

## 📋 목차

- [프로젝트 배경](#-프로젝트-배경-왜-만들었는가)
- [개발 방법론](#-개발-방법론-어떻게-만들었는가)
- [배포 URL](#-배포-url)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [프로젝트 구조](#-프로젝트-구조)
- [설치 및 실행](#-설치-및-실행)
- [주요 기능 상세](#-주요-기능-상세)
- [동작 예시](#-동작-예시)
- [API 엔드포인트](#-api-엔드포인트)
- [주요 개선 사항](#-주요-개선-사항)

## 🎯 주요 기능

### 1. 다중 소스 레시피 검색
- **만개의레시피 크롤링**: 한국 요리 레시피 데이터베이스에서 검색
- **Tavily 웹 검색**: 실시간 웹에서 레시피 정보 수집
- **LLM 생성**: 검색 결과가 없을 경우 AI가 레시피 생성

### 2. 지능형 재료 매칭 시스템
- **재료 정규화**: 동의어 및 계층 구조 기반 재료 매칭
  - 예: "목살" ↔ "돼지고기", "후추" ↔ "후춧가루", "신김치" ↔ "김치"
- **가중치 기반 매칭 점수**: 메인 재료(50점), 부재료(30점), 양념(20점)
- **LLM 기반 스마트 매칭**: 복잡한 대체 가능 여부 판단

### 3. Deep Research 워크플로우
- **Phase 1**: 다중 소스 수집 및 교차 검증
- **Phase 2**: 레시피 선택 및 재료 검증
- **Phase 3**: 레시피 품질 검증 및 최적화
- **Phase 4**: 최종 출력 생성

### 4. 페르소나 기반 맞춤형 출력
- **초보자 모드**: 요리 용어 설명, 실수 방지 가이드, 설거지 최소화 팁
- **숙련가 모드**: 효율적인 조리 순서, 상세한 조리 기법 (열 조절, 타이밍)

### 5. 재료 관리 지능
- **보관 팁**: 냉장/냉동 보관법, 유통기한 정보
- **활용 팁**: 재료 기반 관련 메뉴 추천
- **대체 재료 가이드**: 부족한 재료의 대체 가능 여부 안내

### 6. 쇼핑 리스트 필터링
- 보유한 재료의 상위 개념이나 유사어가 레시피에 있으면 구매 목록에서 자동 제외
- 식기류 및 불필요한 항목 자동 필터링

## 🛠 기술 스택

### Backend
- **FastAPI**: RESTful API 프레임워크
- **LangGraph**: 워크플로우 오케스트레이션
- **OpenAI GPT-4**: 레시피 생성, 최적화, 검증
- **Tavily API**: 실시간 웹 검색
- **BeautifulSoup**: 웹 크롤링 (만개의레시피)
- **httpx**: HTTP 클라이언트
- **Pydantic**: 데이터 검증

### Frontend
- **React 18**: UI 라이브러리
- **TypeScript**: 타입 안정성
- **Vite**: 빌드 도구
- **Tailwind CSS**: 스타일링
- **Axios**: HTTP 클라이언트

## 📁 프로젝트 구조

```
sideproject/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── recipes.py          # API 엔드포인트
│   │   ├── graph/
│   │   │   ├── graph.py                # LangGraph 워크플로우 정의
│   │   │   ├── nodes/                  # 워크플로우 노드 구현 (Phase별 분리)
│   │   │   │   ├── __init__.py         # 노드 함수 export
│   │   │   │   ├── phase1_nodes.py     # Phase 1: 다중 소스 수집 및 교차 검증
│   │   │   │   ├── phase2_nodes.py     # Phase 2: 레시피 선택 및 재료 검증
│   │   │   │   ├── phase3_nodes.py     # Phase 3: 레시피 품질 검증 및 최적화
│   │   │   │   └── phase4_nodes.py     # Phase 4: 최종 출력 생성
│   │   ├── models/
│   │   │   └── state.py                # GraphState 스키마
│   │   ├── services/
│   │   │   └── recipe_crawler.py       # 만개의레시피 크롤링
│   │   ├── utils/
│   │   │   └── ingredient_map.py       # 재료 정규화 및 매칭
│   │   ├── prompts.py                  # 페르소나별 프롬프트
│   │   ├── config.py                   # 설정 관리
│   │   └── main.py                     # FastAPI 앱
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── RecipeRecommendation.tsx  # 메인 UI 컴포넌트
│   │   ├── services/
│   │   │   └── api.ts                   # API 클라이언트
│   │   ├── types/
│   │   │   └── recipe.ts                # TypeScript 타입 정의
│   │   └── App.tsx
│   ├── package.json
│   └── README.md
│
└── README.md
```

## 🚀 설치 및 실행

### Backend 설정

1. **가상환경 생성 및 활성화**
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

2. **의존성 설치**
```bash
pip install -r requirements.txt
```

3. **환경 변수 설정**
`.env` 파일을 생성하고 다음 변수들을 설정:
```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:5173"]
```

4. **서버 실행**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

서버는 기본적으로 `http://localhost:8000`에서 실행됩니다.

### Frontend 설정

1. **의존성 설치**
```bash
cd frontend
npm install
```

2. **개발 서버 실행**
```bash
npm run dev
```

## 📖 주요 기능 상세

### 재료 정규화 시스템

`backend/app/utils/ingredient_map.py`에 정의된 `IngredientNormalizer` 클래스는 다음과 같은 재료 매핑을 지원합니다:

- **후추 계열**: 후추, 후춧가루, 후추가루, 통후추
- **돼지고기 계열**: 돼지고기, 목살, 삼겹살, 앞다리살, 뒷다리살, 돼지갈비, 돼지고기안심 등
- **소고기 계열**: 소고기, 소고기안심, 소등심, 소갈비, 불고기 등
- **닭고기 계열**: 닭고기, 닭가슴살, 닭다리, 닭날개, 닭봉
- **김치 계열**: 김치, 신김치, 새김치, 배추김치, 묵은지
- **간장 계열**: 간장, 진간장, 국간장, 양조간장
- **설탕 계열**: 설탕, 백설탕, 흑설탕, 황설탕
- **물엿 계열**: 물엿, 올리고당, 조청

### LangGraph 워크플로우

레시피 추천 프로세스는 다음 노드들로 구성됩니다 (Phase별 분리):

**Phase 1: 다중 소스 수집 및 교차 검증**
1. **input_ingredients**: 사용자 입력 재료 처리
2. **analyze_ingredients**: 사용자 입력 재료 분석 및 정규화
3. **search_recipes**: 다중 소스에서 레시피 검색 (크롤링, Tavily, LLM)
4. **compare_and_select_source**: 소스 비교 및 최적 소스 선택
5. **explain_recipe_selection**: 소스 선택 이유 설명
6. **filter_recipes**: 레시피 필터링 (난이도, 시간, 카테고리 등)
7. **select_recipe**: 레시피 선택
8. **analyze_alternatives**: 대안 레시피 분석
9. **formulate_hypothesis**: 레시피 선택 가설 수립

**Phase 2: 레시피 선택 및 재료 검증**
10. **check_ingredients**: 보유 재료와 레시피 재료 매칭
11. **web_search_substitutions**: 부족한 재료 대체 재료 검색
12. **suggest_substitutions**: 대체 재료 제안
13. **modify_recipe_with_substitutions**: 레시피에 대체 재료 적용

**Phase 3: 레시피 품질 검증 및 최적화**
14. **analyze_nutrition**: 영양 정보 분석
15. **validate_nutrition**: 영양 정보 검증
16. **optimize_cooking_order**: 페르소나 기반 조리 순서 최적화
17. **validate_cooking_order**: 조리 순서 검증
18. **validate_recipe_completeness**: 레시피 완성도 검증

**Phase 4: 최종 출력 생성**
19. **generate_shopping_list**: 쇼핑 리스트 생성
20. **calculate_confidence_score**: 신뢰도 점수 계산
21. **generate_output**: 최종 결과 생성
22. **collect_user_feedback**: 사용자 피드백 수집
23. **generate_storage_tips**: 재료 보관 및 활용 팁 생성

### 매칭 점수 필터링

매칭 점수가 20점 미만인 레시피는 자동으로 필터링됩니다.

## 🎬 동작 예시

### 예시 1: 기본 레시피 추천

**입력 재료**: `["돼지고기", "김치", "대파"]`

**시스템 동작 과정**:
1. **Phase 1**: 다중 소스에서 레시피 검색 (크롤링, Tavily, LLM)
2. **Phase 2**: 재료 매칭 확인 → 부족한 재료 있으면 대체재 검색 및 제안
3. **Phase 3**: 영양 정보 분석 및 검증, 조리 순서 최적화 및 검증 (Deep Research 재귀 루프)
4. **Phase 4**: 쇼핑 리스트 생성 및 최종 결과 출력

**결과**:
- 추천 레시피: "돼지고기 김치찌개"
- 페르소나별 맞춤형 조리 가이드 제공

### 예시 2: 재료 부족 시 대체재 제안

**입력 재료**: `["닭가슴살", "양파"]` (부족: "마요네즈")

**시스템 동작 과정**:
1. 재료 매칭 확인 → "마요네즈" 부족
2. **Self-Correction Loop**: 웹 검색으로 대체재 찾기 (최대 3회 재시도)
3. 대체재 제안: "마요네즈" → "그릭요거트" 또는 "플레인요거트"
4. 레시피 자동 수정 후 재검증
5. 최종 결과 출력

**결과**:
- 추천 레시피: "닭가슴살 샐러드" (대체재 적용)
- 대체재 가이드: "마요네즈 대신 그릭요거트 사용 가능"
- 매칭률 개선 추적 (이전 매칭률 vs 현재 매칭률)

### 예시 3: Deep Research 재검증 프로세스

**영양 정보 검증**:
- 검증 실패 시 → `analyze_nutrition`으로 재분석 (최대 2회)
- 칼로리 계산 일치성, 합리적 범위 검증

**조리 순서 검증**:
- 검증 실패 시 → `optimize_cooking_order`로 재최적화 (최대 2회)
- 논리적 순서, 시간 일관성 검증

**신뢰도 점수 계산**:
- 매칭률, 품질 점수, 영양 정보 정확도를 종합하여 최종 신뢰도 산출

### 실제 사용 방법

1. 배포 URL 접속: [https://disciplined-youthfulness-production-6532.up.railway.app/](https://disciplined-youthfulness-production-6532.up.railway.app/)
2. 재료 입력: 냉장고에 있는 재료를 입력
3. 옵션 선택 (선택사항):
   - 난이도: 쉬움/보통/어려움
   - 최대 조리 시간
   - 인분 수
   - 페르소나: 초보자/숙련가
4. 레시피 추천 받기: AI가 Deep Research 프로세스를 통해 최적의 레시피 추천
5. 레시피 선택 및 상세 정보 확인

## 🔌 API 엔드포인트

### POST `/api/v1/recipes/recommend`

레시피 추천 요청

**Request Body:**
```json
{
  "ingredients": ["돼지고기", "김치", "대파"],
  "difficulty": "보통",
  "max_cooking_time": 60,
  "serving_size": 2,
  "user_persona": "beginner"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "recipes": [
      {
        "id": "...",
        "name": "돼지고기 김치찌개",
        "ingredients": [...],
        "match_score": 85.0,
        "difficulty": "보통",
        "cooking_time": 30,
        "image": "...",
        "url": "..."
      }
    ]
  }
}
```

### POST `/api/v1/recipes/select`

레시피 선택 및 상세 정보 생성

**Request Body:**
```json
{
  "recipe_index": 0,
  "ingredients": ["돼지고기", "김치", "대파"],
  "serving_size": 2,
  "user_persona": "beginner"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "recipe": {...},
    "nutrition": {...},
    "cooking_steps": [...],
    "shopping_list": [...],
    "substitutions": [...],
    "substitution_guidances": [...],
    "storage_tips": [...]
  }
}
```


## 📝 주요 개선 사항

### 최근 업데이트

1. **코드 구조 리팩토링**
   - **nodes.py Phase별 분리**: 2624줄의 단일 파일을 4개의 phase별 파일로 분리
     - `phase1_nodes.py`: 다중 소스 수집 및 교차 검증 노드 (21개 함수)
     - `phase2_nodes.py`: 레시피 선택 및 재료 검증 노드 (7개 함수)
     - `phase3_nodes.py`: 레시피 품질 검증 및 최적화 노드 (8개 함수)
     - `phase4_nodes.py`: 최종 출력 생성 노드 (7개 함수)
   - 각 phase 파일에 필요한 의존성 함수(private 함수 포함) 자동 포함
   - 코드 가독성 및 유지보수성 향상
   - 기존 API 인터페이스 호환성 유지 (`from app.graph.nodes import ...`)

2. **재료 매칭 시스템 고도화**
   - 재료 정규화 모듈 분리 (`utils/ingredient_map.py`)
   - LLM 기반 스마트 매칭 기능 추가
   - 상위 개념-하위 개념 매칭 지원

3. **필터링 개선**
   - 식기류 자동 필터링 (계량컵, 대접 등)
   - 매칭 점수 20점 이상만 표시
   - 쇼핑 리스트에서 대체 가능 재료 자동 제외

4. **페르소나 기반 출력**
   - 초보자/숙련가 모드별 맞춤형 조리 가이드
   - 재료 보관 및 활용 팁 제공

5. **Deep Research 워크플로우** ✅
   - **재귀적 재검증 루프**: 검증 실패 시 자동으로 재분석/재최적화
     - Phase 2 (재료 검증): 최대 3회 재시도
     - Phase 3 (영양 정보 검증): 최대 2회 재시도
     - Phase 3 (조리 순서 검증): 최대 2회 재시도
   - **다중 소스 교차 검증**: 크롤링, Tavily, LLM 결과 비교 분석
   - **자기 교정 (Self-Correction)**: 매칭률 개선 추적 및 재시도
   - **신뢰도 점수 계산**: 다차원적 검증 결과를 종합한 신뢰도 산출
   - 재귀 한도 설정 (50회)으로 무한 루프 방지

## 🤝 기여

이슈 및 개선 제안은 언제나 환영합니다!

## 향후 예정

1. **DB 연결**
   - 레시피 데이터베이스 구축 및 연동
   - 사용자 검색 히스토리 저장
   - 레시피 캐싱을 통한 성능 향상

2. **응답 속도 최적화**
   - 레시피 검색 및 매칭 로직 성능 개선
   - LLM 호출 최소화 및 캐싱 전략 수립
   - 병렬 처리 최적화

3. **다양한 레시피 추천**
   - 검색 시 매칭도가 비슷한 경우 다양한 레시피 보여주기
   - 사용자에게 더 많은 선택권 제공
   - 매칭도 기반 다양성 확보
