"""Existing agent endpoint."""

from fastapi import APIRouter

from app.api.models import AgentRequest, AgentResponse
from app.api.routes.common import agent_result
from app.agent.tool_agent import run_agent


router = APIRouter(prefix="/api", tags=["agent"])


@router.post("/agent", response_model=AgentResponse)
def agent(request: AgentRequest) -> AgentResponse:
    """Run the existing CLI agent and return its final response."""
    return AgentResponse(response=agent_result(run_agent(request.question)))