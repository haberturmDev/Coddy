from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # loads .env if present; no-op in prod when vars are injected

from infrastructure.logging_config import configure_logging

configure_logging()

from fastapi import FastAPI

from api.middleware.http_logging import HTTPLoggingMiddleware
from api.routes.chat import router as chat_router
from application.use_cases.chat_use_case import ChatUseCase
from infrastructure.llm.groq_client import GroqClient
from infrastructure.sqlite.engine import create_sqlite_engine
from infrastructure.sqlite.models import Base
from infrastructure.sqlite.sqlite_session_store import SQLiteSessionStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Wire dependencies once at startup.
    # To swap providers: replace GroqClient with OpenAIClient / AnthropicClient.
    llm = GroqClient()
    engine = create_sqlite_engine()
    Base.metadata.create_all(engine)
    session_store = SQLiteSessionStore(engine)
    app.state.chat_use_case = ChatUseCase(llm=llm, session_store=session_store)
    yield
    # Cleanup hooks go here (close DB pools, flush caches, etc.)


app = FastAPI(
    title="Coddy AI Orchestrator",
    description="Clean-architecture foundation for an AI agent system.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(HTTPLoggingMiddleware)
app.include_router(chat_router)
