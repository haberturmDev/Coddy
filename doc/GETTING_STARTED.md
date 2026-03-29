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
