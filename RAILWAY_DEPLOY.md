# Railway 배포 가이드

## 1. Railway에서 PostgreSQL 서비스 추가

### 방법 1: Railway 대시보드에서 추가
1. Railway 프로젝트 대시보드로 이동
2. **"New"** 버튼 클릭 → **"Database"** 선택 → **"Add PostgreSQL"** 선택
3. PostgreSQL 서비스가 자동으로 생성되고 `DATABASE_URL` 환경 변수가 자동 설정됨

### 방법 2: Railway CLI 사용
```bash
railway add postgresql
```

## 2. 환경 변수 설정

Railway 대시보드에서 다음 환경 변수들을 설정하세요:

### 필수 환경 변수
- `DATABASE_URL`: PostgreSQL 서비스 추가 시 자동 설정됨 (수동 설정 불필요)
- `OPENAI_API_KEY`: OpenAI API 키
- `TAVILY_API_KEY`: Tavily Search API 키 (선택사항)
- `FRONTEND_URL`: 프론트엔드 배포 URL (예: `https://your-frontend.railway.app`)

### 선택 환경 변수
- `ENVIRONMENT`: `production` (기본값: `development`)
- `LOG_LEVEL`: `INFO` (기본값: `INFO`)

## 3. Alembic 마이그레이션 실행

Railway에서 배포 후 자동으로 마이그레이션을 실행하도록 설정:

### 방법 1: Railway의 Start Command에 마이그레이션 포함

Railway 프로젝트 설정에서 **Custom Start Command**를 다음과 같이 변경:

**기존 설정:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**변경할 설정:**
```bash
cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**또는 Railway가 backend 디렉토리를 루트로 인식하는 경우:**
```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

> **중요**: 
> - `8000` → `$PORT`로 변경 (Railway가 자동으로 포트 할당)
> - `alembic upgrade head &&`를 앞에 추가하여 마이그레이션 자동 실행
> - 프로젝트 루트에서 실행하는 경우 `cd backend &&` 추가 필요

### 방법 2: Railway CLI로 수동 실행

배포 후 Railway CLI로 접속하여 마이그레이션 실행:

```bash
railway run alembic upgrade head
```

### 방법 3: Railway Scripts 사용

`railway.json` 파일 생성 (프로젝트 루트에):

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## 4. 배포 확인

1. Railway 대시보드에서 서비스 로그 확인
2. 마이그레이션이 성공적으로 실행되었는지 확인:
   ```
   INFO  [alembic.runtime.migration] Running upgrade -> xxxxx, create tables
   ```
3. API 엔드포인트 테스트:
   ```bash
   curl https://your-backend.railway.app/api/v1/recipes/recommend
   ```

## 5. 문제 해결

### DATABASE_URL이 인식되지 않는 경우
- Railway 대시보드에서 PostgreSQL 서비스가 추가되었는지 확인
- 환경 변수 탭에서 `DATABASE_URL`이 설정되어 있는지 확인
- 서비스 재시작

### 마이그레이션 실패 시
- Railway CLI로 직접 접속하여 실행:
  ```bash
  railway run alembic upgrade head
  ```
- 로그 확인:
  ```bash
  railway logs
  ```

### 연결 오류 시
- `DATABASE_URL` 형식 확인 (postgresql://로 시작해야 함)
- PostgreSQL 서비스가 실행 중인지 확인
- 방화벽 설정 확인

## 참고사항

- Railway는 `DATABASE_URL` 환경 변수를 자동으로 제공합니다
- 코드는 `DATABASE_URL`이 있으면 우선 사용하고, 없으면 개별 환경 변수로 구성합니다
- 로컬 개발 시에는 `.env` 파일에 개별 환경 변수를 설정하세요

