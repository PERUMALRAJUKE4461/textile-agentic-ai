"""Machine diagnosis endpoints."""

from fastapi import APIRouter

from app.api.models import Diagnosis
from app.api.routes.common import tool_result
from tools.diagnostic_tools import diagnose_machine


router = APIRouter(prefix="/api/machines", tags=["diagnosis"])


@router.get("/{loom_id}/diagnosis", response_model=Diagnosis)
def diagnosis(loom_id: str) -> dict[str, object]:
    """Run the existing diagnostic tool for a loom."""
    return tool_result(lambda: diagnose_machine(loom_id))