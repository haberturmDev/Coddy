You are a senior backend engineer working on an AI agent platform.

Your task is to extend an existing backend service by implementing chat functionality with session-based conversation history stored in memory.

## Goal

Implement a chat system that allows a user to have a multi-turn conversation within a single session.

The system must:
1. Accept a user message
2. Associate it with a session
3. Maintain conversation history in memory for that session
4. Send the full conversation history to the LLM on each request
5. Return the assistant's response
6. Append the assistant's response to the session history

---

## Core Concept

The LLM is stateless.

This means:
- It does NOT remember previous messages
- The full conversation history must be sent on every request

You must explicitly manage this history.

---

## Session Behavior

- Each conversation is identified by a session_id
- If no session_id is provided, create a new session
- Each session maintains its own independent message history
- History must persist for the lifetime of the application (in memory only for now)

---

## Message Model

Each message in history must have:
- role: "system" | "user" | "assistant"
- content: string

At minimum:
- Initialize each session with a system message
- Append user messages and assistant responses in order

---

## Flow per Request

For each incoming user message:

1. Resolve or create session
2. Retrieve session history
3. Append new user message to history
4. Send entire history to LLM provider
5. Receive assistant response
6. Append assistant response to history
7. Return response to user along with session_id

---

## Architecture Requirements

Follow clean architecture principles:

- Do NOT mix HTTP layer with business logic
- Session management must be separated from LLM logic
- LLM interaction must go through an abstraction (already exists in the project)
- Architecture doc @file:ARCHITECTURE.md

You should introduce or extend:
- a session manager / memory store (in-memory for now)
- application-level service that coordinates chat flow

---

## Constraints

- Store everything in memory (no database yet)
- Keep implementation simple and explicit
- Do NOT introduce external frameworks or heavy abstractions
- Do NOT rewrite unrelated parts of the codebase

---

## Extensibility (Important)

Design the solution so it can be easily extended later with:
- persistent storage (database instead of memory)
- context window trimming
- summarization of long conversations
- multi-agent workflows

---

## Expected Outcome

A working chat system where:
- multiple independent sessions are supported
- each session maintains its own conversation history
- the LLM receives full context on each request
- the system is cleanly structured and ready for future extensions