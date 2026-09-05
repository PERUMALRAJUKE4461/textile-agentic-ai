"""Machine telemetry endpoints."""

from fastapi import APIRouter

from app.api.models import MachineStatus
from app.api.routes.common import tool_result
from tools.machine_tools import get_machine_status


router = APIRouter(prefix="/api/machines", tags=["machines"])


@router.get("/{loom_id}", response_model=MachineStatus)
def machine_status(loom_id: str) -> dict[str, object]:
    """Return current telemetry for a loom."""
    return tool_result(lambda: get_machine_status(loom_id))