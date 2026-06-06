# fast_back

A FastAPI backend service.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000. Interactive docs are at
http://127.0.0.1:8000/docs (Swagger UI) and `/redoc`.

## Endpoints

| Method | Path           | Description            |
| ------ | -------------- | ---------------------- |
| GET    | `/health`      | Liveness check         |
| GET    | `/items`       | List items             |
| POST   | `/items`       | Create an item         |
| GET    | `/items/{id}`  | Fetch one item         |
| PATCH  | `/items/{id}`  | Partially update item  |
| DELETE | `/items/{id}`  | Delete an item         |

## Development

```bash
pytest          # run tests
ruff check .    # lint
ruff format .   # format
```

Configuration is read from environment variables / a `.env` file — see
`.env.example`.

## Notes

The `items` resource uses an in-memory store (`app/services/items.py`) as a
stand-in for a database. Replace `ItemRepository` with a persistence-backed
implementation when you add a datastore; route handlers depend on the
repository interface, not the storage.

## testing
