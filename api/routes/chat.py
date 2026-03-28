from fastapi import APIRouter, HTTPException, Request
from api.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    """Single-turn chat endpoint.

    The ChatUseCase is attached to app.state during startup (see main.py),
    which keeps routes free of infrastructure concerns.
    """
    use_case = request.app.state.chat_use_case
    try:
        reply, session_id = await use_case.execute(
            body.message, session_id=body.session_id
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(response=reply, session_id=session_id)
