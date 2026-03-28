# AI Orchestrator Starter Prompt

You are a senior backend engineer designing a production-ready foundation for an AI agent system.

## Goal
Build a simple service that:
1. Accepts a user request via HTTP
2. Sends it to an LLM (via API, currently Groq)
3. Receives the response
4. Returns it to the user

---

## Critical Requirements

### 1. Architecture (VERY IMPORTANT)
Use clean, extensible architecture (Hexagonal / Ports & Adapters style).

Structure must clearly separate:

- API layer (HTTP)
- Application layer (use cases)
- Domain layer (interfaces / abstractions)
- Infrastructure layer (LLM provider implementation)

I want to be able to:
- easily swap Groq → OpenAI / Anthropic
- later add:
  - agent loop
  - RAG
  - memory
  - tool calling

DO NOT create a monolithic file.

---

### 2. LLM Abstraction

Define an interface like:

```python
class LLMClient:
    def generate(self, prompt: str) -> str:
        pass
```

Then implement:

```python
class GroqClient(LLMClient):
    ...
```

The system must depend on the interface, not the implementation.

---

### 3. Tech Stack

Use:
- Python 3.11+
- FastAPI
- httpx (or similar) for API calls

Keep it simple but production-oriented.

---

### 4. API Design

Implement endpoint:

POST /chat

Request:
```json
{
  "message": "Hello"
}
```

Response:
```json
{
  "response": "Hi!"
}
```

---

### 5. Groq Integration

Use Groq API:
https://console.groq.com/docs/overview

- Read API key from environment variable
- Use a modern model (e.g. llama3 or mixtral depending on availability)
- Keep implementation clean and isolated

---

### 6. Extensibility Hooks

Prepare code so that later I can add:
- conversation/session support
- message history
- summarization
- tools

You don't need to implement these, but structure must allow it.

---

### 7. Code Quality

- Use type hints
- Clear folder structure
- No unnecessary complexity
- No overengineering
- Add brief comments where needed

---

### 8. Output Format

Provide:

1. Folder structure
2. Full code for all files
3. Instructions to run (pip install + run server)
4. Example curl request

---

### 9. Important Constraints

- Do NOT use heavy frameworks like LangChain
- Do NOT hide logic behind abstractions I can't control
- Keep everything explicit and readable

---

### 10. Development Constraint (IMPORTANT)

Do NOT rewrite entire files when modifying code in future iterations.
Only modify necessary parts.

---

## Expected Outcome

The result should be a clean foundation for building a full AI orchestrator later.

