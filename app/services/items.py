"""Business logic for items, backed by a simple in-memory store.

This is intentionally a stand-in for a real database layer. Swap
``ItemRepository`` for one backed by SQLAlchemy/an async driver when you
introduce persistence — the route handlers depend on the interface, not the
storage.
"""

from itertools import count

from app.models.item import Item, ItemCreate, ItemUpdate


class ItemRepository:
    """In-memory CRUD store for items.

    A single instance is shared across requests via the ``get_item_repository``
    dependency. Not safe for multi-process deployments — it exists so the API
    is runnable end-to-end without external infrastructure.
    """

    def __init__(self) -> None:
        self._items: dict[int, Item] = {}
        self._ids = count(1)

    def list(self) -> list[Item]:
        return list(self._items.values())

    def get(self, item_id: int) -> Item | None:
        return self._items.get(item_id)

    def create(self, data: ItemCreate) -> Item:
        item = Item(id=next(self._ids), **data.model_dump())
        self._items[item.id] = item
        return item

    def update(self, item_id: int, data: ItemUpdate) -> Item | None:
        existing = self._items.get(item_id)
        if existing is None:
            return None
        updated = existing.model_copy(update=data.model_dump(exclude_unset=True))
        self._items[item_id] = updated
        return updated

    def delete(self, item_id: int) -> bool:
        return self._items.pop(item_id, None) is not None


_repository = ItemRepository()


def get_item_repository() -> ItemRepository:
    """FastAPI dependency returning the shared repository.

    Override in tests with ``app.dependency_overrides`` to inject a fresh,
    isolated store per test.
    """
    return _repository
