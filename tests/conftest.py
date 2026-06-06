"""Shared pytest fixtures.

The ``client`` fixture builds a fresh app and overrides the item repository
with a brand-new in-memory store, so tests never share state.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.items import ItemRepository, get_item_repository


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    repo = ItemRepository()  # one fresh store shared across the test's requests
    app.dependency_overrides[get_item_repository] = lambda: repo
    return TestClient(app)
