"""CRUD routes for the Item resource.

Demonstrates the project's standard pattern: thin handlers that validate via
pydantic models and delegate to a service obtained through Depends().
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.item import Item, ItemCreate, ItemUpdate
from app.services.items import ItemRepository, get_item_repository

router = APIRouter()


@router.get("", response_model=list[Item])
def list_items(repo: ItemRepository = Depends(get_item_repository)) -> list[Item]:
    return repo.list()


@router.post("", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ItemCreate,
    repo: ItemRepository = Depends(get_item_repository),
) -> Item:
    return repo.create(payload)


@router.get("/{item_id}", response_model=Item)
def get_item(
    item_id: int,
    repo: ItemRepository = Depends(get_item_repository),
) -> Item:
    item = repo.get(item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.patch("/{item_id}", response_model=Item)
def update_item(
    item_id: int,
    payload: ItemUpdate,
    repo: ItemRepository = Depends(get_item_repository),
) -> Item:
    item = repo.update(item_id, payload)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    repo: ItemRepository = Depends(get_item_repository),
) -> None:
    if not repo.delete(item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")
