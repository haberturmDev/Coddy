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

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

Response:
```json
{"response": "Hi! How can I help you?"}
```

## Swap the LLM provider
1. Create a new class in `infrastructure/llm/` that extends `LLMClient`.
2. Replace `GroqClient()` with your new class in `main.py` lifespan.
