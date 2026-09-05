"""Advanced AI analysis endpoints."""

from fastapi import APIRouter

from app.api.models import AdvancedAnalysisResponse
from app.api.routes.common import tool_result
from tools.advanced_analysis_tools import advanced_machine_analysis


router = APIRouter(prefix="/api/machines", tags=["advanced AI"])


@router.get("/{loom_id}/advanced-analysis", response_model=AdvancedAnalysisResponse)
def advanced_analysis(loom_id: str) -> dict[str, object]:
    """Return explainable anomalies, trends, risks, forecasts, and RCA."""
    return tool_result(lambda: advanced_machine_analysis(loom_id))