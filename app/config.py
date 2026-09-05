"""Application configuration loaded from environment variables.

The diagnostic limits below are prototype defaults for this project. They are
not universal operating limits and should eventually be replaced with
OEM- and machine-specific configuration.
"""

from dataclasses import dataclass
import logging
import os
from pathlib import Path

from dotenv import load_dotenv


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    """Runtime settings for data tools, diagnostics, and API clients."""

    openrouter_api_key: str | None
    openrouter_model: str
    openrouter_base_url: str
    tavily_api_key: str | None
    telemetry_file: str
    maintenance_file: str
    cors_origins: tuple[str, ...]
    research_max_results: int
    request_timeout_seconds: float
    max_agent_rounds: int
    rpm_minimum: float
    temperature_maximum: float
    vibration_maximum: float
    motor_current_maximum: float
    warp_tension_minimum: float
    warp_tension_maximum: float
    weft_tension_minimum: float
    weft_tension_maximum: float
    efficiency_minimum: float
    defect_rate_maximum: float


def _optional_secret(environ: dict[str, str], name: str) -> str | None:
    value = environ.get(name, "").strip()
    return value or None


def _float_setting(environ: dict[str, str], name: str, default: float) -> float:
    value = environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        return float(value)
    except ValueError:
        LOGGER.warning("Invalid numeric setting %s; using default", name)
        return default


def _int_setting(environ: dict[str, str], name: str, default: int) -> int:
    value = environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except ValueError:
        LOGGER.warning("Invalid integer setting %s; using default", name)
        return default


def load_settings(environ: dict[str, str] | None = None) -> Settings:
    """Load settings without exposing or logging secret values."""
    load_dotenv()
    values = dict(os.environ if environ is None else environ)

    cors_origins = tuple(
        origin.strip()
        for origin in values.get(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origin.strip()
    )

    return Settings(
        openrouter_api_key=_optional_secret(values, "OPENROUTER_API_KEY"),
        openrouter_model=values.get(
            "OPENROUTER_MODEL", "deepseek/deepseek-v4-flash-0731"
        ).strip(),
        openrouter_base_url=values.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).strip(),
        tavily_api_key=_optional_secret(values, "TAVILY_API_KEY"),
        telemetry_file=values.get(
            "TELEMETRY_FILE", str(PROJECT_ROOT / "data" / "loom_telemetry.csv")
        ),
        maintenance_file=values.get(
            "MAINTENANCE_FILE", str(PROJECT_ROOT / "data" / "maintenance_history.csv")
        ),
        cors_origins=cors_origins,
        research_max_results=_int_setting(values, "RESEARCH_MAX_RESULTS", 5),
        request_timeout_seconds=_float_setting(values, "REQUEST_TIMEOUT_SECONDS", 30.0),
        max_agent_rounds=_int_setting(values, "MAX_AGENT_ROUNDS", 8),
        rpm_minimum=_float_setting(values, "RPM_MINIMUM", 600.0),
        temperature_maximum=_float_setting(values, "TEMPERATURE_MAXIMUM", 65.0),
        vibration_maximum=_float_setting(values, "VIBRATION_MAXIMUM", 3.0),
        motor_current_maximum=_float_setting(values, "MOTOR_CURRENT_MAXIMUM", 15.0),
        warp_tension_minimum=_float_setting(values, "WARP_TENSION_MINIMUM", 25.0),
        warp_tension_maximum=_float_setting(values, "WARP_TENSION_MAXIMUM", 35.0),
        weft_tension_minimum=_float_setting(values, "WEFT_TENSION_MINIMUM", 20.0),
        weft_tension_maximum=_float_setting(values, "WEFT_TENSION_MAXIMUM", 30.0),
        efficiency_minimum=_float_setting(values, "EFFICIENCY_MINIMUM", 85.0),
        defect_rate_maximum=_float_setting(values, "DEFECT_RATE_MAXIMUM", 2.0),
    )