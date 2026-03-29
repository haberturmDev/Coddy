# Token Tracking & Usage Exposure — Prompt

## Instructions for LLM (Claude / Sonnet / similar)

You are a senior backend engineer working on an AI agent/orchestrator system built with Hexagonal Architecture (Ports & Adapters).

The system already supports:
- session-based chat
- SQLite persistence
- LLM integration via an abstract LLMClient

Your task is to implement token tracking and expose token usage in API responses.

---

## Goal

Extend the system so that for each request we can:

1. Track total input tokens (`prompt_tokens`)
2. Track output tokens (`completion_tokens`)
3. Track combined total (`total_tokens`) as reported by the provider
4. Return this information in the API response
5. Keep architecture clean and extensible

---

## Core Token Logic

- `prompt_tokens` → returned by LLM API (entire input: history + new message)
- `completion_tokens` → returned by LLM API (assistant response)
- `total_tokens` → as returned by the provider (typically prompt + completion)

---

## Architecture Requirements

Follow existing architecture strictly:

- Domain layer remains clean (no infrastructure details)
- Application layer orchestrates logic
- Infrastructure layer handles LLM + storage

---

## Required Changes

### 1. Chat flow update

In `ChatUseCase`: call the LLM, read usage from `LLMResponse`, attach usage to the result returned to the HTTP layer.

---

### 2. API response

Extend response schema to include:

```json
{
  "response": "...",
  "session_id": "...",
  "usage": {
    "prompt_tokens": 120,
    "completion_tokens": 40,
    "total_tokens": 160
  }
}
```

---

### 3. LLM client

Ensure `LLMClient` returns structured response:

- `content` (text)
- usage fields: `prompt_tokens`, `completion_tokens`, `total_tokens`

Do NOT leak raw API response outside infrastructure.

---

## Documentation updates

### ARCHITECTURE.md

Add or maintain a **Token management** section describing `LLMResponse`, per-request `usage` in API responses, and that counts reflect the provider’s reporting for that call.

### GETTING_STARTED.md

Update the response JSON example to include the `usage` block (three fields as above).

---

## Constraints

- Do NOT break hexagonal architecture
- Do NOT introduce heavy dependencies
- Keep logic explicit and simple
- Do NOT rewrite unrelated code

---

## Extensibility

Design so it can later support:

- token limits enforcement
- automatic summarization
- model routing based on token count

---

## Expected outcome

- Token usage visible per request
- Clean integration into existing architecture
- Updated documentation
