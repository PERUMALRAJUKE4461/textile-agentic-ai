"""Root-cause analysis endpoints."""

from fastapi import APIRouter

from app.api.models import RootCauseResponse
from app.api.routes.common import tool_result
from tools.root_cause_tools import root_cause_analysis


router = APIRouter(prefix="/api/machines", tags=["root cause"])


@router.get("/{loom_id}/root-cause", response_model=RootCauseResponse)
def root_cause(loom_id: str) -> dict[str, object]:
    """Return the existing structured root-cause analysis for a loom."""
    return tool_result(lambda: root_cause_analysis(loom_id))