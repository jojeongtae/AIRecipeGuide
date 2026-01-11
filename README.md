# 레시피 추천 시스템

메뉴 이름으로 레시피를 검색하고, 없는 재료를 체크하면 대체재료를 제안하는 AI 기반 웹 애플리케이션입니다.  
LangGraph를 활용하여 구현한 AI Agent 서비스로, 초보자도 쉽게 요리할 수 있도록 상세한 가이드를 제공합니다.

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

이런 사람들을 실제로 주변에서 많이 보면서, **"만들고 싶은 메뉴를 검색하면 없는 재료만 체크하면 대체재료를 제안해주는 서비스"**가 있으면 좋겠다고 생각했습니다.

- 메뉴 이름으로 검색하면 인기 레시피의 재료 리스트 자동 생성
- 없는 재료만 체크하면 AI가 대체재료 제안
- 초보자도 따라할 수 있는 상세한 조리 과정 제공
- 각 단계별 설명과 실패 방지 팁 포함

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

### 1. 페르소나별 레시피 추천 모드

#### 🟢 초보자 모드 (메뉴 이름 검색)
- **메뉴 이름 검색**: 만들고 싶은 메뉴를 검색 (예: "김치찌개")
- **자동 재료 리스트 생성**: 인기 레시피 기준으로 재료 리스트 자동 생성
- **체크박스 방식**: 없는 재료만 체크 (일반 재료는 자동 체크 해제)
- **자동 대체재 제안**: 없는 재료에 대한 대체재 자동 제안
- **상세한 조리 가이드**: 초보자용 상세 설명, 실패 방지 팁 제공

#### 🔵 숙련가 모드 (재료 기반 검색) - 예정
- **재료 입력**: 보유한 재료를 빠르게 입력
- **여러 레시피 비교**: 매칭률, 조리시간, 난이도 비교
- **효율 최적화**: 시간 단축 팁, 병렬 처리 가능 단계 표시


### 3. 지능형 재료 매칭 시스템
- **재료 정규화**: 동의어 및 계층 구조 기반 재료 매칭
  - 예: "목살" ↔ "돼지고기", "후추" ↔ "후춧가루", "신김치" ↔ "김치"
- **LLM 기반 스마트 매칭**: 복잡한 대체 가능 여부 판단


### 5. Human-in-the-Loop 패턴 (초보자 모드)
- **LangGraph 1.0 Interrupt**: 사용자 재료 선택 대기
- **Checkpointer**: 상태 저장 및 복원
- **점진적 가공**: 원본 레시피 → 상황 분석 → 대체재료 계획 → 조리법 가공 → 페르소나 최적화

### 6. 페르소나 기반 맞춤형 출력
- **초보자 모드**: 요리 용어 설명, 실수 방지 가이드, "왜 이렇게 하는지" 설명

### 7. 재료 관리 지능
- **보관 팁**: 냉장/냉동 보관법, 유통기한 정보
- **활용 팁**: 재료 기반 관련 메뉴 추천
- **대체 재료 가이드**: 부족한 재료의 대체 가능 여부 안내


## 🛠 기술 스택

### Backend
- **FastAPI**: RESTful API 프레임워크
- **LangGraph**: 워크플로우 오케스트레이션
- **OpenAI GPT-4**: 레시피 생성, 최적화, 검증
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
│   │   │   │   ├── phase1_nodes.py     # Phase 1: 크롤링 기반 데이터 수집
│   │   │   │   ├── phase2_nodes.py     # Phase 2: Human-in-the-Loop
│   │   │   │   ├── phase3_nodes.py     # Phase 3: AI 기반 가공
│   │   │   │   └── phase4_nodes.py     # Phase 4: 결과 생성 및 제공
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
CORS_ORIGINS=["http://localhost:3000"]
```

4. **서버 실행**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

### Frontend 설정

1. **의존성 설치**
```bash
cd frontend
npm install
```

2. **환경 변수 설정** (로컬 환경에서 실행 시)
로컬 환경에서 백엔드 API를 사용하려면 환경 변수를 설정해야 합니다.

`frontend` 디렉토리에 `.env` 파일을 생성하고 다음 내용을 추가:
```env
VITE_API_BASE_URL=http://localhost:5000
```

또는 `frontend/src/services/api.ts` 파일의 `API_BASE_URL` 기본값을 직접 수정:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
```

> **참고**: 배포 환경에서는 환경 변수 `VITE_API_BASE_URL`이 자동으로 설정되므로 별도 수정이 필요 없습니다.

3. **개발 서버 실행**
```bash
npm run dev
```

프론트엔드는 기본적으로 `http://localhost:3000`에서 실행됩니다.

> **참고**: `vite.config.ts`에 프록시 설정이 되어 있어, 환경 변수를 설정하지 않아도 로컬 개발 시 백엔드 API (`http://localhost:5000`)로 자동 프록시됩니다. 다만 배포 환경에서 사용하려면 환경 변수 설정이 필요합니다.

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

### LangGraph 워크플로우 (초보자 모드)

레시피 추천 프로세스는 다음 노드들로 구성됩니다 (Phase별 분리):

**Phase 1: 크롤링 기반 데이터 수집 (AI 없음)**
1. **search_menu_recipe**: 메뉴 이름으로 레시피 검색 (만개의레시피 크롤링)
2. **extract_recipe_data**: 레시피 데이터 추출 (재료, 조리순서, 메타데이터)
3. **present_ingredients_to_user**: 재료 체크리스트 생성 및 제시
   - 일반 재료 (물, 식용유, 소금 등)는 자동 체크 해제
   - 나머지 재료는 체크 (없는 재료로 가정)
   - **[INTERRUPT]**: 사용자 재료 선택 대기

**Phase 2: Human-in-the-Loop (인간 개입)**
4. **wait_for_ingredient_selection**: 재료 선택 대기
   - 체크된 재료 = 없는 재료 (missing_ingredients)
   - 사용자가 "레시피 생성하기" 클릭 시 재개

**Phase 3: AI 기반 가공 (LLM 활용)**
5. **analyze_user_situation**: 사용자 상황 분석 (필요 재료 vs 없는 재료)
6. **plan_substitutions**: 대체재료 계획 (LLM) - 부족한 재료에 대한 대체재 제안
7. **adapt_recipe_content**: 레시피 내용 가공 (LLM) - 대체재료에 맞게 조리법 수정
8. **optimize_for_persona**: 페르소나별 최적화 (LLM) - 초보자용 상세 설명 추가

**Phase 4: 결과 생성 및 제공**
9. **generate_final_output**: 최종 출력 생성
   - 대체재료 정보 포함
   - 원본 출처 정보 포함
   - 페르소나별 최적화된 레시피

## 🎬 동작 예시

### 예시: 초보자 모드 - 메뉴 이름 검색

**사용자 입력**: 메뉴 이름 "김치찌개"

**시스템 동작 과정**:
1. **Phase 1**: 만개의레시피에서 "김치찌개" 검색 및 크롤링
2. **재료 추출**: 인기 레시피 기준으로 재료 리스트 자동 생성
   - 일반 재료 (물, 식용유, 소금 등): 자동 체크 해제
   - 나머지 재료: 체크 (없는 재료로 가정)
3. **[INTERRUPT]**: 사용자가 없는 재료 체크 (예: "김치", "고춧가루")
4. **Phase 2**: 재료 선택 완료 → 다음 단계 진행
5. **Phase 3**: AI 가공
   - 대체재료 제안: "김치" → "신김치", "고춧가루" → "고추장"
   - 레시피 내용 수정: 대체재료에 맞게 조리법 수정
   - 초보자용 최적화: 상세 설명, 실패 방지 팁 추가
6. **Phase 4**: 최종 레시피 출력

**결과**:
- 추천 레시피: "김치찌개" (대체재료 적용)
- 대체재료 정보: "김치 → 신김치", "고춧가루 → 고추장"
- 초보자용 상세 가이드: 각 단계별 설명, 주의사항 포함

### 실제 사용 방법

#### 초보자 모드
1. 배포 URL 접속: [https://disciplined-youthfulness-production-6532.up.railway.app/](https://disciplined-youthfulness-production-6532.up.railway.app/)
2. 메뉴 이름 검색: 만들고 싶은 메뉴 이름 입력 (예: "김치찌개")
3. 재료 체크: 없는 재료만 체크 (일반 재료는 자동 체크 해제)
4. 레시피 생성: "레시피 생성하기" 클릭
5. 최종 레시피 확인: 대체재료 정보 및 상세 가이드 포함

## 🔌 API 엔드포인트

### 초보자 모드 API

#### POST `/api/v1/recipes/search`

메뉴 이름 검색 및 재료 체크리스트 반환

**Request Body:**
```json
{
  "menu_name": "김치찌개"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "thread_id": "uuid-string",
    "menu_name": "김치찌개",
    "ingredients_checklist": {
      "items": [
        {
          "name": "파스타면200g",
          "category": "main",
          "checked": true
        },
        {
          "name": "소금",
          "category": "seasoning",
          "checked": false
        }
      ],
      "summary": {
        "total": 8,
        "auto_checked": 3,
        "estimated_match_rate": 0.625
      }
    },
    "estimated_match_rate": 0.625,
    "waiting_for_selection": true,
    "recipe_info": {
      "name": "김치찌개",
      "cooking_time": 30,
      "difficulty": "보통",
      "serving_size": 2,
      "image": "...",
      "popularity_display": "🔥 조회수 15만회"
    }
  }
}
```

#### POST `/api/v1/recipes/update`

재료 선택 업데이트 및 최종 레시피 생성

**Request Body:**
```json
{
  "thread_id": "uuid-string",
  "menu_name": "김치찌개",
  "selected_ingredients": ["김치", "고춧가루"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "final_output": {
      "recipe_name": "김치찌개",
      "source_info": {
        "source": "만개의레시피",
        "popularity_display": "🔥 조회수 15만회"
      },
      "metadata": {
        "cooking_time": 30,
        "difficulty": "보통",
        "serving_size": 2,
        "image": "..."
      },
      "ingredients": [...],
      "cooking_steps": [...],
      "substitutions": {
        "has_substitutions": true,
        "substitution_list": [
          {
            "original": "김치",
            "substitute": "신김치",
            "reason": "...",
            "taste_change": "..."
          }
        ],
        "summary": "다음 재료를 대체했습니다: 김치 → 신김치, 고춧가루 → 고추장"
      }
    }
  }
}
```



## 📝 주요 개선 사항

### 최근 업데이트

1. **초보자 모드 구현**
   - 메뉴 이름 기반 레시피 검색 및 크롤링
   - Human-in-the-Loop 패턴 구현 (LangGraph Interrupt)
   - 대체재료 제안 및 레시피 가공
   - 초보자용 상세 가이드 생성

2. **재료 매칭 시스템 고도화**
   - 재료 정규화 모듈 분리 (`utils/ingredient_map.py`)
   - LLM 기반 스마트 매칭 기능 추가
   - 상위 개념-하위 개념 매칭 지원

3. **필터링 개선**
   - 식기류 자동 필터링 (계량컵, 대접 등)
   - 재료 이름 노이즈 필터링 (500원, 크기, 두께 등)

4. **페르소나 기반 출력**
   - 초보자 모드 맞춤형 조리 가이드
   - 재료 보관 및 활용 팁 제공

5. **UI/UX 개편**
   - 체크박스 기반 직관적인 재료 선택 인터페이스
   - 단계별 가이드 제공 (검색 → 재료 체크 → 레시피 생성)
   - 간결한 레이아웃으로 사용자 부담 최소화



## 향후 예정

1. **숙련가 모드 구현**
   - 재료 기반 검색 (빠른 입력)
   - 여러 레시피 비교 및 선택
   - 효율 최적화 (시간 단축 팁, 병렬 처리 가능 단계)
   - 원본 중심 최소한의 가공

2. **챗봇 기능**
   - 레시피 생성 후 대체재료 질문
   - LangGraph의 interrupt를 활용한 챗봇 단계
   - 레시피 컨텍스트 유지
   - 대화 히스토리 관리

3. **로직 변경 (예정)**
   - 기존 재료 리스트 보여주는 컴포넌트랑 챗봇 컴포넌트랑 교체 예정
   - 현: 사용자 검색 -> 재료 리스트 -> 레시피 제공
   예정: 사용자 검색 -> 레시피 제공
   부족한 재료는 챗봇을 통해 가이드라인 제공 예정
   