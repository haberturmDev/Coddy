You are a senior backend engineer working on an AI agent/orchestrator system.

The project already follows clean Hexagonal Architecture (Ports & Adapters).

Architecture reference:
- Session persistence is abstracted via SessionStore interface
- Current implementation uses in-memory storage
- You must replace or extend it with a persistent SQLite-based implementation

Follow the existing architecture strictly. Do NOT break layering rules.

---

## Goal

Replace in-memory session storage with persistent SQLite storage so that:

1. Conversation history is stored in SQLite
2. After server restart, sessions and messages are restored
3. If the same session_id is used, the conversation continues seamlessly
4. Behavior remains identical from API perspective

---

## Architectural Constraints (CRITICAL)

Follow these rules strictly:

- Domain layer defines SessionStore interface
- Infrastructure layer implements it
- Application layer depends only on the interface
- API layer must not access database directly

You must:
- Implement a new SQLite-based SessionStore in infrastructure layer
- Plug it via dependency injection (main.py)

DO NOT modify domain abstractions unless absolutely necessary.

---

## Storage Design

Design a simple, clean relational schema.

You need at least:

1. Sessions table
   - session_id (primary key)
   - created_at (optional)

2. Messages table
   - id (primary key)
   - session_id (foreign key)
   - role (system/user/assistant)
   - content (text)
   - created_at (ordering)

Ensure:
- Messages are always retrieved in correct chronological order
- Each session is isolated

---

## Behavior Requirements

### On new message:

1. If session_id is not provided:
   - create a new session
   - initialize with system message

2. If session_id exists:
   - load full message history from SQLite

3. Append user message to storage

4. Send full history to LLM

5. Store assistant response in SQLite

6. Return response + session_id

---

### On server restart:

- All sessions must remain available
- History must be loaded from SQLite automatically
- No data loss

---

## Python + SQLite Best Practices (IMPORTANT)

Follow modern Python practices:

- Use a lightweight ORM or query layer:
  - Prefer SQLAlchemy (2.0 style) or a minimal abstraction
  - Avoid raw SQL scattered across code

- Use a repository-like pattern inside infrastructure layer

- Use connection/session management properly:
  - Do NOT open new connections per function call blindly
  - Use a shared engine

- Ensure thread safety (FastAPI context)

- Keep DB logic isolated in infrastructure only

---

## Interface Mapping

Your SQLite implementation must fully conform to SessionStore interface:

Typical operations:

- create_session(session_id)
- get_messages(session_id)
- append_message(session_id, message)
- session_exists(session_id)

---

## Migration Strategy

- Do NOT remove InMemorySessionStore
- Add new implementation: SQLiteSessionStore
- Switch implementation via dependency injection

---

## Extensibility (VERY IMPORTANT)

Design must allow future:

- switching SQLite → Postgres
- adding message metadata
- adding summarization
- partial loading of history (windowing)

Avoid hardcoded assumptions.

---

## Constraints

- Keep implementation simple and explicit
- No overengineering
- No heavy frameworks beyond necessary DB layer
- Do NOT rewrite unrelated code
- Respect existing architecture strictly

---

## Expected Outcome

- Persistent session storage using SQLite
- Clean infrastructure implementation
- No changes required in API or use case logic
- System behaves identically but survives restarts