# PLAN_SPEC.md

> `fast_back` 프로젝트의 **계획 명세서(Plan Specification)**.
> 이 문서는 두 가지를 담는다.
>
> 1. **현황(As-Is)** — 지금 코드베이스가 어떻게 구성되어 있고 무엇을 하는지.
> 2. **로드맵(To-Be)** — 앞으로 추가할 핵심 기능(DB 영속화, 인증/인가)의 구현 계획.
>
> 코드를 작성하기 *전에* 의사결정을 정리해 두는 설계 문서이며, 구현이 진행되면
> 해당 섹션을 갱신한다.

---

## 1. 개요

| 항목 | 내용 |
| --- | --- |
| 프로젝트명 | `fast_back` |
| 종류 | FastAPI 기반 소규모 REST API 서비스 |
| 현재 도메인 | 단일 리소스 `Item`의 CRUD |
| 저장소 | 인메모리(프로세스 전역 싱글턴) — DB 대체용 임시 구현 |
| 런타임 | Python 3.11+, FastAPI, Pydantic v2, pydantic-settings |
| 테스트 | pytest + httpx(TestClient) |
| 린트/포맷 | ruff |
| 배포 대상 (예정) | **Render** (웹 서비스 호스팅) |
| DB (예정) | **Supabase** (관리형 Postgres) |

### 목적

FastAPI의 표준 레이어드 아키텍처(앱 팩토리 → 라우트 → 서비스 → 모델)를
**확장 가능한 형태로** 보여주는 베이스라인이다. 현재는 인메모리 저장소로
엔드투엔드 동작하지만, 인터페이스를 유지한 채 실제 DB와 인증을 얹는 것을
전제로 설계되어 있다.

---

## 2. 현황 (As-Is)

### 2.1 디렉터리 구조

```
app/
  main.py              # 앱 팩토리 create_app() + 모듈 레벨 app
  core/
    config.py          # Settings (pydantic-settings), get_settings() 캐시
  api/
    routes/
      health.py        # GET /health
      items.py         # /items CRUD 핸들러
  services/
    items.py           # ItemRepository (인메모리) + get_item_repository 의존성
  models/
    item.py            # Item / ItemCreate / ItemUpdate 스키마
tests/
  conftest.py          # client 픽스처 (저장소 격리)
  test_health.py
  test_items.py
```

### 2.2 요청 흐름

```
HTTP 요청
  → app/main.py (create_app: CORS, 라우터 등록)
    → app/api/routes/*  (얇은 핸들러: 검증 + 404 매핑)
      → app/services/*  (비즈니스 로직 + 저장)
        ↘ app/models/*  (경계에서 pydantic 검증)
```

핵심 원칙은 **의존성 주입(DI)** 이다. 핸들러는 `Depends(...)`로 협력 객체를
받고, 테스트는 전역 상태를 직접 건드리지 않고 `dependency_overrides`로
주입을 교체한다.

### 2.3 앱 팩토리 — `app/main.py`

- `create_app(settings=None)`가 앱을 생성·구성한다(CORS 미들웨어, 라우터 등록).
- 모듈 레벨 `app = create_app()`는 `uvicorn app.main:app` 용도.
- 테스트는 `create_app()`을 호출해 **격리된 인스턴스**를 얻는다.
- 새 라우트 모듈 추가 지점: 여기서 `import` 후 `app.include_router(...)`.

| 라우터 | prefix | 태그 |
| --- | --- | --- |
| `health.router` | (루트) | health |
| `items.router` | `/items` | items |

### 2.4 라우트 — `app/api/routes/`

핸들러는 의도적으로 얇다: pydantic 모델로 검증하고, 서비스에 위임하고,
"없음"을 `HTTPException(404)`로 매핑한다.

| 메서드 | 경로 | 동작 | 성공 코드 |
| --- | --- | --- | --- |
| GET | `/health` | 헬스 체크 `{"status": "ok"}` | 200 |
| GET | `/items` | 전체 목록 | 200 |
| POST | `/items` | 생성 | 201 |
| GET | `/items/{item_id}` | 단건 조회 | 200 (없으면 404) |
| PATCH | `/items/{item_id}` | 부분 수정 | 200 (없으면 404) |
| DELETE | `/items/{item_id}` | 삭제 | 204 (없으면 404) |

### 2.5 서비스/저장소 — `app/services/items.py`

- `ItemRepository`: `dict[int, Item]` + `itertools.count(1)` 기반 인메모리 CRUD.
- `_repository`는 **프로세스 전역 싱글턴**, `get_item_repository()` 의존성으로 공유.
- 명시적 한계: **멀티프로세스 비안전**, 재시작 시 데이터 소실. DB 대체용 임시물.
- 교체 전략: 동일한 메서드 시그니처(`list/get/create/update/delete`)를 유지한
  영속화 구현으로 갈아끼우면 핸들러는 변경 불필요.

### 2.6 모델 — `app/models/item.py`

세 가지 형태를 의도별로 분리한다.

| 스키마 | 용도 | 특징 |
| --- | --- | --- |
| `ItemBase` | 공통 필드 | `name`(1–100), `description`(≤500, optional), `price`(≥0) |
| `ItemCreate` | 생성 입력 | `ItemBase` 그대로, `id` 없음 |
| `ItemUpdate` | 부분 수정 | 모든 필드 optional, `model_dump(exclude_unset=True)`로 적용 |
| `Item` | 읽기 응답 | 서버 할당 `id: int` 포함 |

### 2.7 설정 — `app/core/config.py`

- `Settings`(pydantic-settings): 환경변수 + `.env`에서 로드.
- `get_settings()`는 `@lru_cache`로 프로세스당 1회 파싱. **항상 의존성으로 접근**.
- 현재 키: `app_name`, `environment`, `debug`, `cors_origins`.

### 2.8 테스트 — `tests/`

- `conftest.py`의 `client` 픽스처: `create_app()` + 테스트당 **새 `ItemRepository`**.
- 핵심 주의: 람다가 단일 인스턴스를 클로저로 잡아야 함
  (`lambda: repo`). 요청마다 `ItemRepository()`를 새로 만들면 한 테스트 안에서
  상태가 유실된다.

### 2.9 컨벤션

- 전역 대신 DI. 테스트 시 provider를 `dependency_overrides`로 교체.
- `B008`은 의도적으로 무시(`pyproject.toml`) — FastAPI의 `Depends()`/`Query()` 관용.

---

## 3. 로드맵 (To-Be)

> 우선순위 순. 각 단계는 **인터페이스 보존**과 **테스트 우선**을 지킨다.
> 각 단계의 기술 선택지는 *제안*이며, 착수 전 확정한다.

### 단계 0. 사전 준비 (공통)

- [ ] `requirements.txt`에 신규 런타임 의존성 추가 시 버전 핀 정책 정리.
- [ ] `app/core/config.py`에 신규 설정 키 추가 시 `.env.example` 동기 갱신.
- [ ] 마이그레이션/시드 절차를 README와 본 문서에 반영.

---

### 단계 1. DB 영속화

**목표**: 인메모리 `ItemRepository`를 실제 DB 기반 구현으로 교체하되,
**라우트 핸들러는 그대로** 둔다.

#### 기술 선택 (확정: Supabase = 관리형 Postgres)

| 항목 | 선택 | 비고 |
| --- | --- | --- |
| DB | **Supabase (Postgres)** | dev/prod 모두 Postgres로 통일 |
| ORM | SQLAlchemy 2.x (async) | FastAPI 정합성 ↑ |
| 드라이버 | `asyncpg` (async) / `psycopg` (sync) | 단계 1의 동기·비동기 결정에 따름 |
| 마이그레이션 | Alembic | 스키마 진화 추적 |

> Supabase는 Postgres 호스팅 + 풀러(PgBouncer)를 제공한다. 앱에서는
> Supabase가 발급하는 **Connection String**(URI)을 그대로 사용한다.
> ORM만 쓸 경우 supabase-py SDK는 불필요하며, 순수 Postgres 접속으로 충분하다.

#### Supabase 연결 주의사항

- **연결 문자열 종류**: Supabase는 *Direct connection*(5432)과
  *Connection pooler*(6543, PgBouncer)를 제공한다. Render 같은 서버리스/
  컨테이너 환경에서는 **pooler(transaction mode)** 사용을 권장.
- **드라이버 URL 형식 예시**
  - async: `postgresql+asyncpg://<user>:<pw>@<host>:6543/postgres`
  - sync: `postgresql+psycopg://<user>:<pw>@<host>:5432/postgres`
- **SSL 필수**: Supabase는 SSL 연결을 요구 → 드라이버 옵션에 `sslmode=require`
  또는 asyncpg `ssl` 설정 반영.
- **PgBouncer + asyncpg 주의**: transaction-mode pooler에서는 prepared
  statement 캐시를 꺼야 한다(`prepared_statement_cache_size=0` 등).
- **마이그레이션 실행 경로**: Alembic은 pooler가 아닌 **Direct connection(5432)**
  으로 돌리는 편이 안전(DDL/세션 일관성).

#### 작업 항목

- [ ] 설정 추가: `database_url`(Supabase 연결 문자열, `.env`로만 주입).
- [ ] 엔진/세션 팩토리 모듈 신설: `app/core/db.py` (async engine, `sessionmaker`).
- [ ] ORM 모델 정의: `app/models/` 또는 `app/db/` 에 `ItemTable`(테이블) 추가.
      - pydantic 스키마(`Item*`)와 ORM 모델은 분리 유지. 변환 계층 둠.
- [ ] `ItemRepository`를 DB 구현으로 교체:
      - 동일 메서드 시그니처 유지 (`list/get/create/update/delete`).
      - 단, async 전환 시 핸들러도 `async def`로 변경되고 `await` 필요 →
        **이 부분은 인터페이스 변경**이므로 사전 합의 필요(아래 ⚠️ 참고).
- [ ] 의존성 교체: `get_item_repository`가 요청 스코프 세션을 받아 저장소 생성.
- [ ] Alembic 초기화 + 최초 마이그레이션(items 테이블).
- [ ] 테스트: `conftest.py`의 격리 전략을 **트랜잭션 롤백** 또는
      **테스트별 임시 SQLite**로 전환.

#### ⚠️ 결정 필요 포인트

- **동기 vs 비동기**: async로 가면 핸들러 시그니처가 바뀐다(`async def` + `await`).
  현재 핸들러는 동기. async를 택할지, 동기 SQLAlchemy로 핸들러를 보존할지 확정.
- **인메모리 구현 유지 여부**: 테스트/로컬 빠른 실행용으로 인메모리 구현을
  남겨 둘지(저장소 인터페이스를 추상화), 완전히 제거할지.

---

### 단계 2. 인증 / 인가

**목표**: 보호된 엔드포인트에 인증을 추가하고, 필요 시 권한(인가) 분기.

#### 기술 선택지 (제안)

| 항목 | 1안 (권장) | 2안 |
| --- | --- | --- |
| 방식 | JWT (OAuth2 Password Bearer) | API Key 헤더 |
| 해싱 | `passlib[bcrypt]` | — (API Key는 해싱 저장) |
| 토큰 | `python-jose` 또는 `pyjwt` | — |

> 권장 근거: JWT + OAuth2PasswordBearer는 FastAPI가 1급으로 지원하고
> Swagger UI에서 바로 인증 테스트가 된다. 서비스 간 호출만이면 API Key가 단순.

#### 작업 항목

- [ ] 설정 추가: `secret_key`, `access_token_expire_minutes`, `algorithm`.
      - `secret_key`는 `.env`로만 주입, 저장소에 커밋 금지. `.env.example`엔 플레이스홀더.
- [ ] (JWT 택 시) `User` 도메인 추가:
      - 모델: `UserCreate`(평문 비밀번호 입력) / `User`(응답, 비밀번호 제외).
      - 저장소: `UserRepository` (단계 1의 DB 위에 구축).
- [ ] 보안 유틸: 비밀번호 해싱/검증, JWT 발급/디코드 → `app/core/security.py`.
- [ ] 인증 라우트: `POST /auth/token` (로그인 → 토큰 발급).
- [ ] 의존성: `get_current_user`(토큰 검증) → 보호 엔드포인트에 `Depends`.
- [ ] 인가(선택): 역할/스코프 필드 추가 후 의존성에서 권한 검사.
- [ ] 보호 적용 범위 결정: 어떤 `items` 동작을 인증 필수로 할지
      (예: 읽기는 공개, 쓰기는 인증).
- [ ] 테스트: 인증 헤더가 있는/없는 케이스, 만료 토큰, 권한 부족(403) 케이스.

#### ⚠️ 결정 필요 포인트

- **방식 확정**: JWT vs API Key (혹은 둘 다).
- **사용자 등록 흐름 범위**: 가입 엔드포인트를 공개할지, 시드/관리자만 생성할지.
- **보호 대상 엔드포인트**: 전체 인증 vs 쓰기만 인증.

---

### 단계 3. 배포 (Render)

**목표**: `fast_back`을 Render 웹 서비스로 배포하고, Supabase DB와 연결.

#### 작업 항목

- [ ] **Start 커맨드**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
      (Render는 `$PORT` 환경변수로 포트를 주입 → 하드코딩 금지).
- [ ] **Build 커맨드**: `pip install -r requirements.txt`.
- [ ] **환경변수**(Render 대시보드 또는 `render.yaml`):
      - `DATABASE_URL` → Supabase 연결 문자열(pooler).
      - `SECRET_KEY`, `ENVIRONMENT=production`, `DEBUG=false`,
        `CORS_ORIGINS`(실제 프런트 도메인으로 제한).
- [ ] **CORS 좁히기**: 현재 기본값 `["*"]` → 운영에서는 허용 출처 명시.
- [ ] **마이그레이션 실행 시점**: 배포 시 Alembic 마이그레이션을 어떻게 돌릴지 결정
      (Render의 *pre-deploy command* 또는 수동 1회 실행).
- [ ] **헬스 체크**: Render Health Check Path를 `/health`로 설정.
- [ ] (선택) `render.yaml`(Infrastructure as Code)로 서비스 정의를 레포에 커밋.
- [ ] (선택) GitHub 연동 자동 배포(main push → deploy).

#### ⚠️ 결정 필요 포인트

- Render 플랜(Free/Starter): Free는 유휴 시 슬립 → 콜드 스타트 존재.
- 마이그레이션 자동화 여부(pre-deploy hook vs 수동).

---

## 4. 아키텍처 가드레일 (변경 시 유지할 것)

1. **핸들러는 얇게**: 검증 + 위임 + 404 매핑까지만. 로직은 서비스로.
2. **저장소 인터페이스 보존**: 구현을 바꿔도 메서드 시그니처는 유지.
   (단계 1의 async 전환은 명시적 예외 — 사전 합의 필요)
3. **DI로 모든 협력 객체 주입**: 전역 직접 참조 금지. 테스트 seam 유지.
4. **스키마 3분할 유지**: 신규 리소스도 `*Create` / `*Update` / 읽기 형태 분리.
5. **설정은 `get_settings()` 경유**: `Settings()` 직접 생성 금지, 테스트는 override.
6. **`.env.example` 동기화**: 설정 키 추가 시 즉시 갱신.

---

## 5. 작업 순서 요약

```
[단계 0] 사전 준비
   └─ 의존성/설정/문서 정책 정리
[단계 1] DB 영속화
   ├─ 동기/비동기 결정 ⚠️
   ├─ db.py + ORM 모델 + Alembic
   ├─ ItemRepository 교체 (인터페이스 보존)
   └─ 테스트 격리 전략 전환
[단계 2] 인증/인가
   ├─ 방식 결정 (JWT/API Key) ⚠️
   ├─ User 도메인 + security.py
   ├─ /auth/token + get_current_user
   └─ 보호 범위 결정 + 테스트
[단계 3] 배포 (Render + Supabase)
   ├─ Start/Build 커맨드 + $PORT
   ├─ 환경변수(DATABASE_URL, SECRET_KEY, CORS) 설정
   ├─ 마이그레이션 실행 경로 결정 ⚠️
   └─ /health 헬스체크 + (선택) render.yaml
```

---

## 6. 미해결 질문 (착수 전 확정)

- [ ] 단계 1: 동기 SQLAlchemy로 핸들러 시그니처를 보존할지, async로 갈지?
- [ ] 단계 1: 인메모리 구현을 테스트용으로 남길지 제거할지?
- [ ] 단계 2: 인증 방식 — JWT / API Key / 둘 다?
- [ ] 단계 2: 사용자 가입을 공개 엔드포인트로 둘지?
- [ ] 단계 2: items의 어떤 동작을 인증 필수로 할지(읽기 공개 여부)?
- [ ] 단계 3: 마이그레이션을 Render pre-deploy로 자동화할지 수동 실행할지?
- [ ] 단계 3: Render 플랜(Free vs 유료) — 콜드 스타트 허용 여부?
```
