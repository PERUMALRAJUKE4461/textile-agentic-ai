"""Maintenance history endpoints."""

from fastapi import APIRouter

from app.api.models import MaintenanceHistory
from app.api.routes.common import tool_result
from tools.maintenance_tools import get_maintenance_history


router = APIRouter(prefix="/api/machines", tags=["maintenance"])


@router.get("/{loom_id}/maintenance", response_model=MaintenanceHistory)
def maintenance_history(loom_id: str) -> dict[str, object]:
    """Return maintenance history for a loom."""
    return tool_result(lambda: get_maintenance_history(loom_id))