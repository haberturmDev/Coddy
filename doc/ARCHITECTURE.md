# Coddy — Architecture Reference

## Purpose
Foundation for an AI agent/orchestrator system. Currently: HTTP → LLM → response.
Designed to grow into: agent loops, RAG, memory, tool calling, sessions.

## Stack
- Python 3.9+, FastAPI, httpx, Pydantic v2
- LLM: Groq (swappable)

## Pattern: Hexagonal (Ports & Adapters)
Dependencies always point inward: `api` → `application` → `domain` ← `infrastructure`

## Structure
```
main.py                          # DI wiring + app startup
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
  memory/in_memory_session_store.py  # InMemorySessionStore — session adapter
```

## Key Rules
- **Never** import infrastructure into domain or application.
- Routes only call use cases, never infrastructure directly.
- Swap provider: implement `LLMClient`, replace existing client (for ex `GroqClient()`) in `main.py` lifespan.
- Swap session storage: implement `SessionStore`, replace `InMemorySessionStore()` in `main.py` lifespan.

## Extension Points
| Feature | Where |
|---|---|
| Sessions / history | `SessionStore` + `ChatUseCase.execute(session_id=...)` |
| RAG | Retrieval step inside `ChatUseCase.execute` |
| Tool calling | Tool-dispatch loop inside `ChatUseCase.execute` |
| New LLM provider | New class in `infrastructure/llm/`, swap in `main.py` |
| New endpoint | New schema in `api/schemas/`, route in `api/routes/` |

## Endpoint
`POST /chat` — `{"message": "...", "session_id": "<optional>"}` → `{"response": "...", "session_id": "..."}`
