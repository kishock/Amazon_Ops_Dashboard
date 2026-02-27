# Amazon Ops Dashboard

Amazon Selling Partner API(SP-API) Sandbox 데이터를 수집/저장/조회하기 위한 FastAPI 기반 백엔드 프로젝트입니다.

현재 구현은 **주문(Orders) ETL 파이프라인**에 초점이 맞춰져 있으며, Inventory/Logs는 확장 가능한 스텁 형태로 포함되어 있습니다.

## 1) 프로젝트 개요

이 프로젝트의 목적은 다음과 같습니다.

- SP-API Sandbox에서 주문 데이터를 조회
- 조회한 주문 데이터를 PostgreSQL에 업서트(upsert)
- 신규 주문 발생 시 Slack Webhook 알림 발송
- API 엔드포인트로 주문/상태 정보를 조회
- 향후 inventory, logs, scheduler 기능으로 확장 가능한 구조 제공

핵심 기술 스택:

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- psycopg (PostgreSQL 드라이버)
- Uvicorn
- Docker / Docker Compose

## 2) 폴더 구조

```text
Amazon_Ops_Dashboard/
  app/
    api/
      routes_dashboard.py      # /dashboard/health
      routes_orders.py         # /orders, /orders/sync-sandbox
      routes_inventory.py      # inventory 스텁 엔드포인트
      routes_logs.py           # logs 스텁 엔드포인트
    core/
      config.py                # 환경변수 기반 설정(Settings)
    db/
      session.py               # SQLAlchemy engine/session/Base
      models.py                # ORM 모델(Order)
      crud.py                  # DB CRUD + upsert 로직
    services/
      spapi_client.py          # Amazon LWA 토큰 + Sandbox Orders API 호출
      etl_orders.py            # 주문 ETL 오케스트레이션
      slack_notifier.py        # Slack Webhook 알림 전송
      etl_inventory.py         # inventory ETL 스텁
    workers/
      scheduler.py             # 배치 실행 진입점(단건 실행 함수)
    main.py                    # FastAPI 앱 생성 및 라우터 등록
  Dockerfile
  docker-compose.yml
  requirements.txt
  .env.example
  sandbox_lwa_token_test.py    # LWA 토큰 점검용 보조 스크립트
```

## 3) 구성(컴포넌트 설명)

### 3.1 API 레이어 (`app/api`)

- `routes_dashboard.py`
  - `GET /dashboard/health`
  - DB에 `SELECT 1`을 실행해 연결 상태를 확인
- `routes_orders.py`
  - `GET /orders/`: DB에 저장된 주문 목록 반환
  - `POST /orders/sync-sandbox`: 주문 ETL 실행 트리거
  - 설정/외부 API 오류를 의미 있는 HTTP 상태코드로 변환
- `routes_inventory.py`, `routes_logs.py`
  - 현재 빈 목록을 반환하는 스텁

### 3.2 서비스 레이어 (`app/services`)

- `spapi_client.py`
  - LWA access token 발급
  - Sandbox Orders API 호출
  - 필수 자격 증명(`SPAPI_CLIENT_ID`, `SPAPI_CLIENT_SECRET`, `SPAPI_REFRESH_TOKEN`) 검증
- `etl_orders.py`
  - SP-API에서 주문 목록 가져오기
  - 주문별 upsert 수행
  - `DEMO_MODE=true`일 때 synthetic 주문 1건 추가 생성
  - 신규(`amazon_order_id` 기준) 주문만 Slack 알림 발송
  - 트랜잭션 commit/rollback 처리
- `slack_notifier.py`
  - Slack Incoming Webhook으로 신규 주문 알림 전송
  - 알림 실패 시 ETL은 계속 진행

### 3.3 데이터 레이어 (`app/db`)

- `session.py`
  - SQLAlchemy `engine`, `SessionLocal`, `Base`, `get_db()` 정의
- `models.py`
  - `orders` 테이블에 대한 `Order` ORM 모델 정의
- `crud.py`
  - SP-API datetime 문자열 파싱
  - `upsert_order()`로 `amazon_order_id` 기준 업서트
  - 신규 생성 여부를 함께 반환해 중복 알림 방지에 사용
  - `list_orders()` 조회

### 3.4 워커 레이어 (`app/workers`)

- `scheduler.py`
  - 향후 주기 실행 작업을 위한 위치
  - 현재는 `run_orders_sync_once()` 단건 실행 함수 제공

### 3.5 앱 엔트리포인트 (`app/main.py`)

- FastAPI 앱 생성
- `/dashboard`, `/orders`, `/inventory`, `/logs` 라우터 등록
- startup 이벤트에서 `Base.metadata.create_all()` 실행 (테이블 자동 생성)

## 4) 아키텍처

데이터 흐름은 다음과 같습니다.

1. 클라이언트가 `POST /orders/sync-sandbox` 호출
2. API 레이어가 `run_orders_etl()` 실행
3. ETL이 `SPAPIClient`를 통해 LWA 토큰 발급 후 주문 데이터 조회
4. ETL이 `crud.upsert_order()`로 DB에 업서트
5. 신규 주문만 Slack 알림 발송
6. 커밋 후 `{fetched, upserted, demo_generated}` 결과 반환

```text
[Client]
   |
   v
[FastAPI Router: /orders/sync-sandbox]
   |
   v
[ETL Service: run_orders_etl]
   |                    \
   |                     -> [SPAPIClient] -> Amazon LWA + SP-API Sandbox
   v
[CRUD Upsert]
   |
   +--> [Slack Webhook] (신규 주문만)
   |
   v
[PostgreSQL orders 테이블]
```

레이어 분리 원칙:

- API: HTTP 입출력/의존성 주입
- Services: 외부 연동/비즈니스 흐름
- DB: 영속성/쿼리 처리
- Workers: 배치/스케줄 실행 진입점

## 5) 환경 변수

`.env.example`를 기준으로 `.env` 파일을 생성해 사용합니다.

```env
# App
APP_NAME=Amazon Ops Dashboard
ENVIRONMENT=local
DEMO_MODE=false

# PostgreSQL
DATABASE_URL=
DB_HOST=localhost
DB_PORT=5432
DB_USER=
DB_PASSWORD=
DB_NAME=

# LWA / SP-API Sandbox
SPAPI_CLIENT_ID=
SPAPI_CLIENT_SECRET=
SPAPI_REFRESH_TOKEN=
SPAPI_SANDBOX_ENDPOINT=https://sandbox.sellingpartnerapi-na.amazon.com
SPAPI_MARKETPLACE_ID=ATVPDKIKX0DER

# Slack Incoming Webhook
SLACK_WEBHOOK_URL=
```

주의:

- `POST /orders/sync-sandbox`를 실제로 사용하려면 SP-API 관련 3개 자격 증명이 반드시 필요합니다.
- `docker-compose.yml`은 `env_file: .env`를 사용하므로 `.env` 파일이 없으면 실행 실패할 수 있습니다.
- `DATABASE_URL`이 설정되면 `DB_HOST/PORT/USER/PASSWORD/NAME`보다 우선 적용됩니다.
- Supabase 같은 외부 PostgreSQL은 `DATABASE_URL` 사용을 권장합니다.
- `DEMO_MODE=true`일 때는 샌드박스 응답 처리 후 synthetic 주문 1건을 추가로 생성합니다.

### 5.1 Sandbox 정적 응답 제약과 DEMO_MODE

SP-API Sandbox Orders는 패턴 매칭 기반의 정적 테스트 케이스를 반환하므로, 동일 케이스 호출 시 신규 주문이 계속 생성되지 않습니다.

이 제약 때문에 데모 시나리오를 위해 `DEMO_MODE`를 제공합니다.

- `DEMO_MODE=false` (기본값)
  - 샌드박스 원본 주문만 upsert
- `DEMO_MODE=true`
  - 샌드박스 주문 upsert 이후 synthetic 주문(테스트/데모를 위해 인위적으로 만든 가짜 주문) 1건 생성
  - 생성 규칙:
    - `amazon_order_id`: `DEMO-<UTC timestamp>`
    - `order_status`: `Pending`
  - synthetic 주문도 동일한 파이프라인을 사용:
    - upsert (`amazon_order_id` 유니크 기준)
    - 신규 주문 이벤트 처리
    - Slack 알림 발송
  - 즉, static sandbox 제약이 있어도 신규 주문 -> DB -> 알림까지 라이브 데모 가능

## 6) 실행 방법

## 6.1 로컬 실행 (Windows PowerShell)

1. 가상환경 생성 및 활성화

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. 패키지 설치

```powershell
pip install -r requirements.txt
```

3. 환경 파일 준비

```powershell
Copy-Item .env.example .env
# 필요 시 .env 값 수정
```

4. API 실행

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. 접속 확인

- Swagger UI: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/dashboard/health`

## 6.2 Docker Compose 실행

1. `.env` 생성

```powershell
Copy-Item .env.example .env
```

2. 컨테이너 실행

```powershell
docker compose up --build
```

3. 접속

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

4. 종료

```powershell
docker compose down
```

볼륨까지 정리하려면:

```powershell
docker compose down -v
```

## 7) 주요 API 엔드포인트

- `GET /dashboard/health`
  - DB 연결 상태 확인
- `GET /orders/`
  - 저장된 주문 목록 조회
- `POST /orders/sync-sandbox`
  - SP-API Sandbox 주문 동기화 실행
  - 신규 주문은 Slack 알림도 함께 발송
- `GET /inventory/`
  - 스텁 (빈 배열)
- `GET /logs/`
  - 스텁 (빈 배열)

예시:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/orders/sync-sandbox
Invoke-RestMethod -Method Get -Uri http://localhost:8000/orders/
```

## 8) 데이터 모델 (orders)

`orders` 테이블 주요 컬럼:

- `id`: PK
- `amazon_order_id`: Amazon 주문 ID (유니크)
- `order_status`: 주문 상태
- `purchase_date`: 주문 생성 시각
- `last_update_date`: 마지막 갱신 시각
- `raw_payload`: 원본 JSON 페이로드
- `synced_at`: 동기화 시각

업서트 키는 `amazon_order_id`입니다.

간단 ERD:

```text
+---------------------------+
|          orders           |
+---------------------------+
| id (PK, int)              |
| amazon_order_id (unique)  |
| order_status              |
| purchase_date (timestamptz) |
| last_update_date (timestamptz) |
| raw_payload (json)        |
| synced_at (timestamptz)   |
+---------------------------+
```

## 9) 현재 상태와 확장 포인트

현재 구현 상태:

- 주문 ETL: 구현 완료
- Inventory ETL: 스텁
- Logs API: 스텁
- 스케줄러: 단건 실행 함수만 존재
- 테스트 코드: 별도 미구현

권장 다음 단계:

1. `tests/` 추가 (API, CRUD, ETL 단위/통합 테스트)
2. Alembic 마이그레이션 도입 (`create_all` 의존 축소)
3. 스케줄러(예: APScheduler/Celery) 기반 주기 동기화
4. inventory/logs 기능 실구현
5. 예외 처리/로깅 표준화 및 관측성(메트릭) 추가

## 10) API 응답 샘플(JSON)

### 10.1 `GET /dashboard/health`

```json
{
  "status": "ok",
  "db": "connected"
}
```

### 10.2 `GET /orders/`

```json
{
  "orders": [
    {
      "id": 12,
      "amazon_order_id": "902-3159896-1390916",
      "order_status": "Shipped",
      "purchase_date": "2026-02-26T09:12:44+00:00",
      "last_update_date": "2026-02-26T10:02:11+00:00",
      "synced_at": "2026-02-27T01:20:33+00:00"
    }
  ]
}
```

### 10.3 `POST /orders/sync-sandbox`

```json
{
  "fetched": 5,
  "upserted": 6,
  "demo_generated": 1
}
```

### 10.4 `GET /inventory/` (현재 스텁)

```json
{
  "inventory": []
}
```

### 10.5 `GET /logs/` (현재 스텁)

```json
{
  "logs": []
}
```

## 11) 트러블슈팅

- `ModuleNotFoundError` 발생 시:
  - 가상환경 활성화 여부 확인
  - `pip install -r requirements.txt` 재실행

- `DB 연결 실패` 시:
  - 외부 DB를 쓰면 `.env`의 `DATABASE_URL` 우선 확인
  - `.env`의 DB_HOST/PORT/USER/PASSWORD/DB_NAME 확인
  - Docker 사용 시 `api` 컨테이너에서는 `DB_HOST=db`여야 함
  - 비밀번호에 특수문자가 있으면 URL 인코딩 필요

- `Missing SP-API credentials` 에러 시:
  - `.env`에 `SPAPI_CLIENT_ID`, `SPAPI_CLIENT_SECRET`, `SPAPI_REFRESH_TOKEN` 입력

- `sync-sandbox`가 `503`을 반환할 때:
  - SP-API 자격 증명이 누락되었는지 확인

- `sync-sandbox`가 `502`를 반환할 때:
  - Amazon LWA/SP-API 응답 상태와 네트워크 연결 확인

- `sync-sandbox`가 빈 결과를 반환할 때:
  - Sandbox 테스트 케이스/Marketplace ID/권한 설정 확인
