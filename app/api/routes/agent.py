"""Existing agent endpoint."""

from fastapi import APIRouter, HTTPException

from app.api.models import (
    AgentRequest,
    AgentResponse,
    ConversationHistoryResponse,
)
from app.api.routes.common import agent_result
from app.agent.memory import get_conversation_history, save_conversation_turn
from app.agent.tool_agent import run_agent


router = APIRouter(prefix="/api", tags=["agent"])


@router.post("/agent", response_model=AgentResponse)
def agent(request: AgentRequest) -> AgentResponse:
    """Run the tool-using agent with persistent history when a session is supplied."""
    history = (
        get_conversation_history(request.session_id)
        if request.session_id
        else request.conversation_history
    )
    response = agent_result(run_agent(request.question, history))
    if request.session_id:
        save_conversation_turn(request.session_id, request.question, response)
    return AgentResponse(response=response)


@router.get("/agent/{session_id}/history", response_model=ConversationHistoryResponse)
def conversation_history(session_id: str) -> ConversationHistoryResponse:
    """Load persisted messages so a returning browser can restore its chat."""
    try:
        messages = get_conversation_history(session_id, limit=200)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return ConversationHistoryResponse(session_id=session_id, messages=messages)