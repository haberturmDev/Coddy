# Coddy — Architecture Reference

## Purpose
Foundation for an AI agent/orchestrator system. Currently: HTTP → LLM → response.
Designed to grow into: agent loops, RAG, memory, tool calling, sessions.

## Stack
- Python 3.9+, FastAPI, httpx, Pydantic v2
- LLM: Groq (swappable)
- Persistence: SQLite via SQLAlchemy 2.x (declarative ORM; `create_all` at startup — no migration runner yet)

## Pattern: Hexagonal (Ports & Adapters)
Dependencies always point inward: `api` → `application` → `domain` ← `infrastructure`

## Structure
```
main.py                          # DI wiring + app startup (engine, create_all, adapters)
api/
  schemas/chat.py                # Pydantic request/response models
  routes/chat.py                 # POST /chat — thin HTTP handler
application/
  use_cases/chat_use_case.py     # Orchestration logic (no I/O)
domain/
  ports/llm_client.py            # LLMClient ABC — the port
  ports/session_store.py         # SessionStore ABC — conversation persistence
  models/conversation.py         # Message, Role, Conversation dataclasses
infrastructure/
  llm/groq_client.py             # GroqClient — the adapter
  memory/in_memory_session_store.py  # InMemorySessionStore — dev/tests; no DB
  sqlite/
    engine.py                    # create_sqlite_engine — shared Engine factory
    models.py                    # SQLAlchemy Base + table mappings (sessions, messages)
    sqlite_session_store.py      # SQLiteSessionStore — SessionStore adapter
```

## Databases & SQL — project rules
- **Boundary:** `domain` and `application` must not import SQLAlchemy, drivers, or SQL strings. Persistence is only through **ports** (`SessionStore`, etc.) implemented under `infrastructure/`.
- **Where SQL lives:** table definitions, queries, and `Session` / connection usage stay inside the adapter package (e.g. `infrastructure/sqlite/`). Do not pass ORM models or `Engine` into use cases.
- **Engine lifecycle:** create **one** `Engine` at startup in `main.py` (or a dedicated bootstrap module), pass it into adapters. Avoid creating engines per request or per repository call.
- **API style:** prefer SQLAlchemy 2.0 patterns (`select()`, `Session` as context manager, `Mapped` / `mapped_column`). No legacy `Query` API in new code.
- **Domain types at the edge:** adapters translate between DB rows and domain models (`Conversation`, `Message`, …) inside `infrastructure`; use cases work only with domain types and ports.
- **Schema changes:** today we rely on `create_all` for bootstrapping. When migrations are introduced (e.g. Alembic), they belong next to the DB package and run from startup or a release step — document that choice when it lands.

## Key Rules
- **Never** import infrastructure into domain or application.
- Routes only call use cases, never infrastructure directly.
- Swap provider: implement `LLMClient`, replace existing client (for ex `GroqClient()`) in `main.py` lifespan.
- Swap session storage: implement `SessionStore`, replace the store in `main.py` lifespan (e.g. `SQLiteSessionStore(engine)` or `InMemorySessionStore()` for tests).

## Extension Points
| Feature | Where |
|---|---|
| Sessions / history | `SessionStore` + `ChatUseCase.execute(session_id=...)` |
| RAG | Retrieval step inside `ChatUseCase.execute` |
| Tool calling | Tool-dispatch loop inside `ChatUseCase.execute` |
| New LLM provider | New class in `infrastructure/llm/`, swap in `main.py` |
| New endpoint | New schema in `api/schemas/`, route in `api/routes/` |
| Another database | New engine factory + adapter package under `infrastructure/`, same ports |

## Endpoint
`POST /chat` — `{"message": "...", "session_id": "<optional>"}` → `{"response": "...", "session_id": "..."}`
