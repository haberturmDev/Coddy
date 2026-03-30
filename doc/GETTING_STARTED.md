# Getting Started

## Prerequisites
- Python 3.9+
- A [Groq API key](https://console.groq.com)

## Setup

```bash
# 1. Install dependencies
python3 -m pip install -r requirements.txt

# 2. Create your .env file
cp .env.example .env
# Open .env and set: GROQ_API_KEY=your_key_here

# 3. Start the server
python3 -m uvicorn main:app --reload
```

Server runs at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`

## Send a message

Omit `session_id` to start a new chat; the server returns a `session_id` you can send on the next request to continue the same conversation.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

Response:
```json
{
  "response": "Hi! How can I help you?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "usage": {
    "prompt_tokens": 42,
    "completion_tokens": 10,
    "total_tokens": 52
  }
}
```

Follow-up in the same session (replace the id with the one you received):

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What did I just say?", "session_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

## Swap the LLM provider
1. Create a new class in `infrastructure/llm/` that extends `LLMClient`.
2. Replace `GroqClient()` with your new class in `main.py` lifespan.

## Enable conversation summarization

Pass `memory_config` **once** when starting or continuing a session. The config is stored in the session — all future turns in that session automatically apply summarization without you needing to send `memory_config` again.

### Step 1 — enable summarization on the first (or any) turn

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, let'\''s start a long conversation.",
    "memory_config": {
      "strategies": { "summarization": true },
      "params": {
        "summarization": {
          "last_n_messages": 10,
          "model": "llama-3.1-8b-instant"
        }
      }
    }
  }'
```

Take the `session_id` from the response.

### Step 2 — all follow-up turns apply summarization automatically

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Continue our chat.", "session_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

No `memory_config` needed — the session remembers it. Once the history grows beyond `last_n_messages`, older turns are compressed into a summary automatically.

### Override or disable for a session

Send a new `memory_config` on any turn to replace the stored config. To disable summarization:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Stop summarizing.",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "memory_config": { "strategies": { "summarization": false } }
  }'
```

### Defaults (all fields optional)

| Field | Default |
|---|---|
| `strategies.summarization` | `false` |
| `params.summarization.last_n_messages` | `10` |
| `params.summarization.model` | `"llama-3.1-8b-instant"` |

> **Existing SQLite databases** need a one-time migration before this feature works across restarts:
> ```sql
> ALTER TABLE sessions ADD COLUMN summary TEXT;
> ALTER TABLE sessions ADD COLUMN memory_config_json TEXT;
> ```
> Alternatively, delete the `coddy.db` file and let the server recreate it on next startup.
