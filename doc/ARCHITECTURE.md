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
  models/conversation.py         # Message, Role, Conversation dataclasses
infrastructure/
  llm/groq_client.py             # GroqClient — the adapter
```

## Key Rules
- **Never** import infrastructure into domain or application.
- Routes only call use cases, never infrastructure directly.
- Swap provider: implement `LLMClient`, replace existing client (for ex `GroqClient()`) in `main.py` lifespan.

## Extension Points
| Feature | Where |
|---|---|
| Sessions / history | Pass persisted `Conversation` into `ChatUseCase.execute` |
| RAG | Retrieval step inside `ChatUseCase.execute` |
| Tool calling | Tool-dispatch loop inside `ChatUseCase.execute` |
| New LLM provider | New class in `infrastructure/llm/`, swap in `main.py` |
| New endpoint | New schema in `api/schemas/`, route in `api/routes/` |

## Endpoint
`POST /chat` — `{"message": "..."}` → `{"response": "..."}`
