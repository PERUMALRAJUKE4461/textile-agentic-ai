"""Pydantic request and response models for the backend API."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MachineStatus(BaseModel):
    """Current telemetry for a loom."""

    success: bool
    loom_id: str
    loom_type: str
    timestamp: str
    rpm: float
    temperature: float
    vibration: float
    motor_current: float
    warp_tension: float
    weft_tension: float
    humidity: float
    production_rate: float
    efficiency: float
    defect_rate: float
    machine_status: str
    fault_type: str


class MaintenanceRecord(BaseModel):
    """One maintenance event stored for a loom."""

    date: str
    loom_id: str
    loom_type: str
    issue: str
    action_taken: str
    technician: str
    downtime_hours: str


class MaintenanceHistory(BaseModel):
    """Maintenance history response."""

    success: bool
    loom_id: str
    record_count: int
    records: list[MaintenanceRecord]


class Diagnosis(BaseModel):
    """Diagnostic findings for a loom."""

    loom_id: str
    machine_status: str
    fault_type: str
    issues: list[str]
    diagnosis: str


class ResearchRequest(BaseModel):
    """Request body for technical web research."""

    query: str = Field(min_length=1, max_length=500)


class ResearchResult(BaseModel):
    """One web research result."""

    title: str = ""
    url: str = ""
    content: str = ""
    score: float = 0


class ResearchResponse(BaseModel):
    """Technical research response."""

    success: bool
    query: str
    result_count: int
    results: list[ResearchResult]
    error_code: str | None = None
    error: str | None = None


class AgentRequest(BaseModel):
    """Question submitted to the existing agent."""

    question: str = Field(min_length=1, max_length=4000)
    conversation_history: list[dict[str, str]] = Field(default_factory=list, max_length=40)


class AgentResponse(BaseModel):
    """Final natural-language agent response."""

    response: str


class RootCauseResponse(BaseModel):
    """Structured Phase 2 root-cause analysis."""

    model_config = ConfigDict(extra="allow")

    success: bool
    loom_id: str
    analysis_type: str
    root_causes: list[dict[str, Any]]
    summary: str


class AdvancedAnalysisResponse(BaseModel):
    """Combined Phase 6 analysis response."""

    model_config = ConfigDict(extra="allow")

    success: bool
    loom_id: str
    current_telemetry: dict[str, Any]
    historical_record_count: int
    diagnostic: dict[str, Any]
    maintenance_history: dict[str, Any]
    anomaly_detection: dict[str, Any]
    trend_analysis: dict[str, Any]
    predictive_maintenance: dict[str, Any]
    production_forecast: dict[str, Any]
    failure_risk: dict[str, Any]
    root_cause_analysis: dict[str, Any]
    limitations: list[str]
    explainability: str