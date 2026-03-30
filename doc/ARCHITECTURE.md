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
  schemas/chat.py                # Pydantic request/response models (incl. MemoryConfigSchema)
  routes/chat.py                 # POST /chat — thin HTTP handler
application/
  use_cases/chat_use_case.py     # Orchestration logic (no I/O)
  memory/
    memory_config.py             # MemoryConfig, MemoryStrategies, SummarizationParams dataclasses
    memory_manager.py            # MemoryManager — central extension point for memory strategies
    summarization_service.py     # SummarizationService — compresses old messages via LLMClient
domain/
  ports/llm_client.py            # LLMClient ABC — the port (supports optional model override)
  ports/session_store.py         # SessionStore ABC — conversation persistence
  models/conversation.py         # Message, Role, Conversation dataclasses (incl. summary field)
infrastructure/
  llm/groq_client.py             # GroqClient — the adapter
  memory/in_memory_session_store.py  # InMemorySessionStore — dev/tests; no DB
  sqlite/
    engine.py                    # create_sqlite_engine — shared Engine factory
    models.py                    # SQLAlchemy Base + table mappings (sessions w/ summary, messages)
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
| New memory strategy | Add method in `MemoryManager`, dispatch from `build_context` |

## Endpoint
`POST /chat` — `{"message": "...", "session_id": "<optional>", "memory_config": {...}}` → `{"response": "...", "session_id": "...", "usage": { ... }}`

## Token management
- The LLM port returns structured usage (`LLMResponse`: prompt, completion, and total token counts from the provider).
- The API exposes a `usage` object on every chat response: `prompt_tokens`, `completion_tokens`, and `total_tokens` (full prompt + reply for that request, as reported by the provider).

## Memory system

The memory system lives entirely in `application/memory/` and is controlled via the optional `memory_config` request field.

### Components

- **`MemoryConfig`** — dataclass carrying strategy flags and per-strategy parameters; deserialized from the `memory_config` JSON field in the request.
- **`MemoryManager`** — the single extension seam for all memory strategies. `build_context(conversation, current_message, config)` returns `(llm_messages, new_summary)`. Adding a new strategy means adding a private method here and dispatching it from `build_context` — `ChatUseCase` never changes.
- **`SummarizationService`** — calls `LLMClient.generate()` with a dedicated compression prompt and a (possibly different) model to produce a concise summary of old messages.

### Config resolution — sticky-session behavior

`memory_config` is **session-scoped**, not per-request. Once set, it is serialized as JSON and stored in the `sessions` table under `memory_config_json`. On every subsequent turn the stored config is loaded automatically, so you only need to send `memory_config` once per session.

Resolution order per request:

1. `memory_config` present in the request → use it and **overwrite** the stored session config
2. `memory_config` absent, but a config is stored for the session → use the stored config
3. Neither exists → no memory strategy; full history is sent to the LLM (original behaviour)

### Summarization flow

```
history = [msg_1 ... msg_M]   (all messages for the session, excluding current)
old_messages    = history[:-N]   (summarized if non-empty)
recent_messages = history[-N:]

LLM context sent:
  [SYSTEM: system_prompt]
  [SYSTEM: "Previous conversation summary:\n{summary}"]  ← only if summary exists
  [recent_messages]
  [USER: current_message]
```

`N` defaults to `10`. If `len(history) <= N` no summarization call is made but an existing stored summary is still forwarded.

### Request schema

```json
{
  "message": "Hello!",
  "session_id": "optional-uuid",
  "memory_config": {
    "strategies": { "summarization": true },
    "params": {
      "summarization": {
        "last_n_messages": 10,
        "model": "llama-3.1-8b-instant"
      }
    }
  }
}
```

All fields inside `memory_config` are optional and fall back to their defaults. Omit `memory_config` entirely on follow-up turns — the session remembers it.

### Summary and config persistence

The `sessions` table carries two new nullable text columns:

| Column | Purpose |
|---|---|
| `summary` | Latest compressed summary of old messages |
| `memory_config_json` | JSON-serialized `MemoryConfig` stored for the session |

Both are loaded into the `Conversation` domain object on `get_or_create` and written back on `save`. Messages are never deleted — the summary logically replaces old messages in the LLM context only.

> **Existing databases:** run the following once, or delete `coddy.db` to let `create_all` recreate the schema:
> ```sql
> ALTER TABLE sessions ADD COLUMN summary TEXT;
> ALTER TABLE sessions ADD COLUMN memory_config_json TEXT;
> ```

