"""Liveness / readiness endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return service status. Used by load balancers and uptime checks."""
    return {"status": "ok"}
