# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

The repo uses a local venv at `.venv` and pip (no uv/poetry). Activate it, or prefix commands with `./.venv/bin/`.

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Run the dev server (auto-reload) at http://127.0.0.1:8000, docs at /docs
uvicorn app.main:app --reload

# Tests
pytest                          # all tests
pytest tests/test_items.py      # one file
pytest tests/test_items.py::test_delete_item   # one test
pytest -k "update"              # by name pattern

# Lint / format
ruff check .
ruff format .
```

Runtime deps live in `requirements.txt`; dev-only deps (pytest, httpx, ruff) in `requirements-dev.txt`, which includes the runtime set.

## Architecture

A small FastAPI service organized in layers. Request flow:
`app/main.py` (app factory) → `app/api/routes/*` (handlers) → `app/services/*` (logic/storage), with `app/models/*` (pydantic schemas) used for validation at the boundary.

- **App factory** — `app/main.py:create_app()` builds and configures the app (CORS, router registration). A module-level `app = create_app()` exists for `uvicorn app.main:app`. Tests call `create_app()` to get isolated instances. Add new route modules by importing them and calling `app.include_router(...)` here.

- **Routes** — `app/api/routes/`. Handlers are thin: validate via pydantic models, obtain collaborators through `Depends(...)`, delegate to a service, and map "not found" to `HTTPException(404)`. `health.py` is registered at the root; `items.py` is mounted under the `/items` prefix in `create_app`.

- **Services** — `app/services/`. Business logic and storage. `items.py` holds an in-memory `ItemRepository` (a process-global singleton returned by the `get_item_repository` dependency). **This is a deliberate stand-in for a database** and is not multi-process safe. Replace it with a persistence-backed implementation; keep the same method surface so handlers don't change.

- **Models** — `app/models/`. Pydantic v2 schemas split by intent: `*Create` (client input), `*Update` (all-optional partial update applied with `model_dump(exclude_unset=True)`), and the base read shape with server-assigned fields like `id`. Keep these three shapes distinct when adding resources.

- **Config** — `app/core/config.py`. `Settings` (pydantic-settings) reads env vars and an optional `.env`. Always access via the cached `get_settings()` dependency rather than constructing `Settings()` directly; override it in tests through `dependency_overrides`.

## Conventions

- **Dependency injection over globals.** Routes receive services/settings via `Depends`. This is also the seam for testing — override providers in `dependency_overrides`, never reach into module state.
- **Test isolation.** `tests/conftest.py` provides a `client` fixture that overrides `get_item_repository` with one fresh `ItemRepository` per test (the lambda must close over a single instance, not construct a new one per request — otherwise state is lost between calls within a test). Add similar overrides for any new stateful service.
- **B008 is ignored on purpose** (`pyproject.toml`) — FastAPI's `Depends()`/`Query()` idiom intentionally calls functions in argument defaults. Don't "fix" those call sites.
