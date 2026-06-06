# HANDOFF.md

> 다음 에이전트를 위한 인수인계 문서. **이 파일만 읽어도** 이어서 작업할 수 있도록 정리했다.
> 작성 시점: 2026-06-06

---

## 0. 한 줄 요약

`fast_back`(FastAPI items CRUD 서비스)의 **계획 명세서 `PLAN_SPEC.md`를 작성 완료**했다.
아직 **코드 구현은 시작하지 않았다.** 다음 단계는 `PLAN_SPEC.md`의 "단계 1: DB 영속화"부터.

---

## 1. 이번 세션에서 한 일

사용자 요청: "PLAN_SPEC.md를 설명하고 상세하게 작성해줘. 단, 질문하고 허락한 것만."

### 진행 흐름
1. 레포 탐색 → `PLAN_SPEC.md`는 **존재하지 않았음**(신규 생성 대상).
2. 사용자에게 4지선다 질문 → 아래 답변 확정.
3. 실제 소스 전부 읽고 현황 파악.
4. `PLAN_SPEC.md` 작성.
5. 사용자가 추가 정보 제공(서버=Render, DB=Supabase) → 문서에 반영.

### 사용자가 확정한 결정 (질문 응답)
- **문서 목적**: 현황(As-Is) + 로드맵(To-Be) 둘 다.
- **로드맵 범위**: DB 영속화 + 인증/인가.
- **언어/분량**: 한국어 · 상세.
- **추가 지시(자유 입력)**: 서버는 **Render**, DB는 **Supabase**.

---

## 2. ✅ 성공한 것 (완료)

- **`PLAN_SPEC.md` 생성 완료** (`/Users/hyunkim/Desktop/fast_back/PLAN_SPEC.md`).
  - 1. 개요 (Render/Supabase 스택 표 포함)
  - 2. 현황(As-Is) — 실제 소스 기준: 디렉터리, 요청 흐름, 앱 팩토리, 라우트 표,
    `ItemRepository`(인메모리 한계), 모델 3분할, 설정, 테스트 픽스처, 컨벤션
  - 3. 로드맵 — 단계 1(DB/Supabase), 단계 2(인증/인가), 단계 3(Render 배포)
  - 4. 가드레일 / 5. 작업 순서 / 6. 미해결 질문
- Supabase = 관리형 Postgres로 확정 반영(연결 문자열 pooler 6543 vs direct 5432,
  SSL 필수, PgBouncer+asyncpg 주의, Alembic은 direct로 실행 등).
- Render 배포 단계 추가(`$PORT` 사용, Build/Start 커맨드, 환경변수, `/health` 헬스체크).

---

## 3. ❌ 아직 안 한 것 / 실패한 것

- **코드 구현 전혀 없음.** 문서 작업만 했다. app/ 소스는 손대지 않았다.
- DB 연동(SQLAlchemy/Alembic) 미착수.
- 인증/인가(JWT 등) 미착수.
- Render 배포 설정(`render.yaml` 등) 미작성.
- (실패라기보다) 아래 결정들이 **미확정**이라 구현을 시작하지 못함 — 4번 참고.

---

## 4. ⚠️ 다음 에이전트가 먼저 확정해야 할 결정 (BLOCKER)

`PLAN_SPEC.md`의 6번 섹션과 동일. 구현 착수 전 사용자에게 물어볼 것:

1. **단계 1 — 동기 vs 비동기 SQLAlchemy?**
   async로 가면 핸들러가 `async def`로 바뀌어, "저장소 인터페이스 보존" 원칙의
   명시적 예외가 된다. (현재 핸들러는 전부 동기)
2. **단계 1 — 인메모리 `ItemRepository`를 테스트용으로 남길지 제거할지?**
3. **단계 2 — 인증 방식: JWT / API Key / 둘 다?**
4. **단계 2 — 사용자 가입을 공개 엔드포인트로 둘지?**
5. **단계 2 — items의 어떤 동작을 인증 필수로 할지(읽기 공개 여부)?**
6. **단계 3 — 마이그레이션을 Render pre-deploy로 자동화할지 수동 실행할지?**
7. **단계 3 — Render 플랜(Free vs 유료, 콜드 스타트 허용 여부)?**

---

## 5. 다음 단계 (권장 작업 순서)

1. 위 BLOCKER 중 최소 **#1(동기/비동기)** 와 **#3(인증 방식)** 을 사용자에게 확정받는다.
2. `PLAN_SPEC.md` "단계 1: DB 영속화" 착수:
   - `database_url` 설정 추가(`app/core/config.py`) + `.env.example` 갱신.
   - `app/core/db.py`(engine, sessionmaker) 신설.
   - ORM 모델 추가, `ItemRepository`를 DB 구현으로 교체(메서드 시그니처 보존).
   - Alembic 초기화 + items 테이블 마이그레이션.
   - `tests/conftest.py` 격리 전략을 트랜잭션 롤백 또는 임시 DB로 전환.
3. 각 변경 후 `pytest`, `ruff check .` 통과 확인.

---

## 6. 프로젝트 핵심 사실 (배경 지식)

- **스택**: Python 3.11+, FastAPI, Pydantic v2, pydantic-settings, pytest, ruff.
- **아키텍처**: 앱 팩토리(`app/main.py:create_app`) → 라우트(`app/api/routes/`) →
  서비스(`app/services/`) → 모델(`app/models/`). DI(`Depends`) 중심.
- **현재 저장소**: `app/services/items.py`의 `ItemRepository` = 인메모리 전역 싱글턴
  (`_repository`). 멀티프로세스 비안전, 재시작 시 소실 → **DB 대체용 임시물**.
- **엔드포인트**: `GET /health`, `GET/POST /items`, `GET/PATCH/DELETE /items/{id}`.
- **모델 3분할**: `ItemCreate`(입력) / `ItemUpdate`(부분수정, 전부 optional) /
  `Item`(응답, `id` 포함). 신규 리소스도 이 패턴 유지.
- **가드레일**(반드시 지킬 것): 핸들러 얇게, 저장소 인터페이스 보존,
  DI로 주입(전역 직접참조 금지), 스키마 3분할, 설정은 `get_settings()` 경유,
  `.env.example` 동기화.
- **테스트 주의**: `conftest.py`의 `client` 픽스처는 단일 repo 인스턴스를 클로저로
  잡아야 함(`lambda: repo`). 요청마다 새로 만들면 상태 유실.
- **린트**: `B008`은 의도적으로 무시(FastAPI `Depends()`/`Query()` 관용) — "고치지" 말 것.

### 명령어 (CLAUDE.md 발췌)
```bash
source .venv/bin/activate        # 또는 ./.venv/bin/ 프리픽스
uvicorn app.main:app --reload    # 개발 서버 http://127.0.0.1:8000, docs /docs
pytest                           # 테스트
ruff check . && ruff format .    # 린트/포맷
```

---

## 7. 참고 파일

- `PLAN_SPEC.md` — 전체 계획(현황 + 로드맵). **메인 참조 문서.**
- `CLAUDE.md` — 프로젝트 규약/명령어/아키텍처 설명.
- `README.md` — 프로젝트 소개.
- `app/` — 실제 소스. `.env.example` — 설정 키 목록.
