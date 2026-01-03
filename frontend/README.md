# Recipe Recommendation System - Frontend

레시피 추천 시스템 프론트엔드 (React + TypeScript + Vite + Tailwind CSS)

## 🚀 시작하기

### 1. 의존성 설치

```bash
npm install
```

### 2. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 http://localhost:3000 접속

### 3. 빌드

```bash
npm run build
```

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── components/
│   │   └── RecipeRecommendation.tsx  # 메인 레시피 추천 컴포넌트
│   ├── services/
│   │   └── api.ts                    # API 클라이언트
│   ├── types/
│   │   └── recipe.ts                 # TypeScript 타입 정의
│   ├── App.tsx                       # 메인 앱 컴포넌트
│   ├── main.tsx                      # 진입점
│   └── index.css                     # 전역 스타일
├── package.json
├── vite.config.ts                    # Vite 설정
├── tailwind.config.js                # Tailwind CSS 설정
└── tsconfig.json                     # TypeScript 설정
```

## 🎨 기술 스택

- **React 18**: UI 라이브러리
- **TypeScript**: 타입 안정성
- **Vite**: 빌드 도구 및 개발 서버
- **Tailwind CSS**: 유틸리티 기반 CSS 프레임워크
- **Axios**: HTTP 클라이언트

## 🔧 주요 기능

### 레시피 추천
- 재료 입력 (쉼표로 구분)
- 레시피 검색 및 추천
- 여러 레시피 중 선택
- 레시피 상세 정보 표시

### UI 구성
- 반응형 디자인
- 로딩 상태 표시
- 에러 처리
- 레시피 상세 정보 (재료, 영양 정보, 요리 순서)
- 쇼핑 리스트 표시

## 🌐 API 연동

백엔드 API와 연동:
- `POST /api/v1/recipes/recommend`: 레시피 추천
- `POST /api/v1/recipes/select`: 레시피 선택

API Base URL은 `vite.config.ts`의 proxy 설정 또는 환경 변수로 관리됩니다.

## 📝 환경 변수

`.env` 파일 생성 (선택):

```env
VITE_API_BASE_URL=http://localhost:5000
```

## 🎯 다음 단계

- [ ] 상태 관리 라이브러리 추가 (React Query 등)
- [ ] 레시피 필터링 UI (난이도, 조리 시간)
- [ ] 레시피 즐겨찾기 기능
- [ ] 반응형 디자인 개선
- [ ] 애니메이션 추가

