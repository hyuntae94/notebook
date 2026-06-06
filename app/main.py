"""Application entrypoint and FastAPI app factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import health, items
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure a FastAPI application.

    Using a factory (rather than a module-level singleton) keeps construction
    explicit and lets tests build isolated apps with custom settings.
    """
    settings = settings or get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(items.router, prefix="/items", tags=["items"])

    return app


# Module-level instance used by `uvicorn app.main:app`.
app = create_app()
