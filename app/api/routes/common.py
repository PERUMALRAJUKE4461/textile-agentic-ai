"""Shared HTTP error translation for tool results."""

import logging
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException


LOGGER = logging.getLogger(__name__)


def tool_result(call: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Run a local tool and translate its stable error envelope to HTTP."""
    try:
        result = call()
    except Exception:
        LOGGER.exception("Unhandled exception while serving a tool request")
        raise HTTPException(
            status_code=500,
            detail="The requested tool failed unexpectedly.",
        ) from None

    if not isinstance(result, dict):
        LOGGER.error("Tool returned a non-object result")
        raise HTTPException(status_code=500, detail="The tool returned an invalid response.")

    if result.get("success", False):
        return result

    error_code = result.get("error_code", "tool_execution_error")
    status_code = {
        "invalid_loom_id": 400,
        "invalid_research_query": 400,
        "invalid_tool_arguments": 400,
        "loom_not_found": 404,
        "maintenance_not_found": 404,
        "missing_tavily_api_key": 503,
        "research_timeout": 503,
        "research_api_error": 503,
        "empty_research_results": 503,
    }.get(error_code, 500)
    raise HTTPException(
        status_code=status_code,
        detail=result.get("error") or result.get("message") or "The tool request failed.",
    )


def agent_result(response: str) -> str:
    """Translate the existing agent's graceful error string to HTTP."""
    if not isinstance(response, str) or not response:
        raise HTTPException(status_code=500, detail="The agent returned an invalid response.")
    if response.startswith("Agent unavailable:"):
        raise HTTPException(status_code=503, detail=response)
    return response