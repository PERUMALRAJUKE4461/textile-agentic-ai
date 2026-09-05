"""Technical web research endpoints."""

from fastapi import APIRouter

from app.api.models import ResearchRequest, ResearchResponse
from app.api.routes.common import tool_result
from tools.research_tools import web_research


router = APIRouter(prefix="/api", tags=["research"])


@router.post("/research", response_model=ResearchResponse)
def research(request: ResearchRequest) -> dict[str, object]:
    """Search for general technical information using the existing tool."""
    return tool_result(lambda: web_research(request.query))