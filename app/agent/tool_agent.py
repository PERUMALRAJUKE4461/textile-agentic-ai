import json
import logging
import re
from collections.abc import Mapping
from typing import Any

from openai import OpenAI

from app.config import load_settings
from tools.machine_tools import get_machine_status
from tools.maintenance_tools import get_maintenance_history
from tools.research_tools import web_research
from tools.diagnostic_tools import diagnose_machine
from tools.root_cause_tools import root_cause_analysis


LOGGER = logging.getLogger(__name__)
client: OpenAI | None = None


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_machine_status",
            "description": (
                "Get the latest telemetry and operating status "
                "of a textile loom."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "loom_id": {
                        "type": "string",
                        "description": "Loom ID such as L001.",
                    }
                },
                "required": ["loom_id"],
            },
        },
    },
        {
        "type": "function",
        "function": {
            "name": "get_maintenance_history",
            "description": (
                "Get previous maintenance records and recurring "
                "issues for a textile loom."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "loom_id": {
                        "type": "string",
                        "description": "Loom ID such as L001.",
                    }
                },
                "required": ["loom_id"],
            },
        },
    },
        {
        "type": "function",
        "function": {
            "name": "web_research",
            "description": (
                "Search the web for reliable technical information "
                "about textile machines, loom faults, maintenance, "
                "production problems, and possible causes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "A focused technical search query."
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
    "type": "function",
    "function": {
        "name": "diagnose_machine",
        "description": (
            "Analyze a textile loom's telemetry and identify "
            "possible machine or process problems."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "loom_id": {
                    "type": "string",
                    "description": "Loom ID such as L001.",
                }
            },
            "required": ["loom_id"],
        },
    },
},
    {
        "type": "function",
        "function": {
            "name": "root_cause_analysis",
            "description": (
                "Correlate current telemetry, maintenance history, diagnostic "
                "findings, and targeted technical web research into ranked "
                "root causes with evidence-based confidence scores and "
                "prioritized technician actions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "loom_id": {
                        "type": "string",
                        "description": "Loom ID such as L001.",
                    }
                },
                "required": ["loom_id"],
            },
        },
    },
]


def _invalid_arguments(tool_name: str, message: str) -> dict[str, object]:
    return {
        "success": False,
        "error_code": "invalid_tool_arguments",
        "tool": tool_name,
        "error": message,
    }


def _required_string(
    tool_name: str, arguments: Mapping[str, Any], name: str
) -> str | dict[str, object]:
    value = arguments.get(name)
    if not isinstance(value, str) or not value.strip():
        return _invalid_arguments(
            tool_name, f"Argument {name!r} must be a non-empty string."
        )
    return value.strip()


def execute_tool(
    tool_name: str, arguments: Mapping[str, Any] | None
) -> dict[str, object]:
    """Execute a tool and convert argument or runtime failures to a result."""

    if not isinstance(arguments, Mapping):
        return _invalid_arguments(tool_name, "Tool arguments must be a JSON object.")

    LOGGER.debug("Dispatching tool %s", tool_name)
    try:
        if tool_name == "get_machine_status":
            loom_id = _required_string(tool_name, arguments, "loom_id")
            return (
                loom_id
                if isinstance(loom_id, dict)
                else get_machine_status(loom_id)
            )

        if tool_name == "get_maintenance_history":
            loom_id = _required_string(tool_name, arguments, "loom_id")
            return (
                loom_id
                if isinstance(loom_id, dict)
                else get_maintenance_history(loom_id)
            )

        if tool_name == "web_research":
            query = _required_string(tool_name, arguments, "query")
            return query if isinstance(query, dict) else web_research(query)

        if tool_name == "diagnose_machine":
            loom_id = _required_string(tool_name, arguments, "loom_id")
            return (
                loom_id
                if isinstance(loom_id, dict)
                else diagnose_machine(loom_id)
            )

        if tool_name == "root_cause_analysis":
            loom_id = _required_string(tool_name, arguments, "loom_id")
            return (
                loom_id
                if isinstance(loom_id, dict)
                else root_cause_analysis(loom_id)
            )
    except Exception as error:
        LOGGER.error("Tool execution failed for %s: %s", tool_name, error)
        return {
            "success": False,
            "error_code": "tool_execution_error",
            "tool": tool_name,
            "error": "The tool failed while processing the request.",
        }

    return {
        "success": False,
        "error_code": "unknown_tool",
        "error": f"Unknown tool: {tool_name}",
    }


def _error_response(message: str) -> str:
    return f"Agent unavailable: {message}"


def _investigation_loom_id(
    user_query: str, history_messages: list[dict[str, str]]
) -> str | None:
    """Find a loom ID for a machine-specific investigation or follow-up."""
    investigation_terms = re.compile(
        r"\b(check|investigat\w*|diagnos\w*|status|condition|fault|problem|"
        r"issue|production|maintenance|machine|loom|why)\b",
        re.IGNORECASE,
    )
    if not investigation_terms.search(user_query):
        return None

    current_match = re.search(r"\bL\d+\b", user_query, re.IGNORECASE)
    if current_match:
        return current_match.group(0).upper()

    for item in reversed(history_messages):
        history_match = re.search(r"\bL\d+\b", item["content"], re.IGNORECASE)
        if history_match:
            return history_match.group(0).upper()
    return None


def _collect_investigation_evidence(loom_id: str) -> dict[str, dict[str, object]]:
    """Run four distinct machine tools before composing an investigation."""
    tool_arguments = {"loom_id": loom_id}
    evidence: dict[str, dict[str, object]] = {}
    for tool_name in (
        "get_machine_status",
        "get_maintenance_history",
        "diagnose_machine",
        "root_cause_analysis",
    ):
        result = execute_tool(tool_name, tool_arguments)
        evidence[tool_name] = result
    return evidence


def run_agent(
    user_query: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    """Run the OpenRouter tool-calling loop with graceful failure handling."""

    if not isinstance(user_query, str) or not user_query.strip():
        return _error_response("a non-empty user query is required.")

    current_settings = load_settings()
    if not current_settings.openrouter_api_key:
        return _error_response("OPENROUTER_API_KEY is not configured.")
    if not current_settings.openrouter_model:
        return _error_response("OPENROUTER_MODEL is not configured.")

    try:
        active_client = client or OpenAI(
            base_url=getattr(
                current_settings, "openrouter_base_url", "https://openrouter.ai/api/v1"
            ),
            api_key=current_settings.openrouter_api_key,
            timeout=getattr(current_settings, "request_timeout_seconds", 30.0),
        )
    except Exception as error:
        LOGGER.error("Unable to configure OpenRouter client: %s", error)
        return _error_response(
            "the OpenRouter client could not be configured. Check the API URL and settings."
        )

    history_messages = []
    for item in conversation_history or []:
        if item.get("role") in {"user", "assistant"} and item.get("content"):
            history_messages.append(
                {"role": item["role"], "content": item["content"]}
            )

    investigation_loom_id = _investigation_loom_id(user_query, history_messages)
    investigation_evidence = (
        _collect_investigation_evidence(investigation_loom_id)
        if investigation_loom_id
        else {}
    )

    messages = [
        {
            "role": "system",
                "content": (
                    "You are a textile manufacturing AI agent. "
                    "Investigate machine conditions using the available tools. "
            
                    "Do not invent machine measurements or maintenance records. "
            
                    "Use machine telemetry for current conditions. "
            
                    "Use maintenance history to identify recurring problems. "
            
                    "Use web research when external technical knowledge is needed. "
                    "Use the conversation history to resolve references such as it, "
                    "this machine, the loom, the issue, and the technician. If a "
                    "loom is already known from the conversation, do not ask for its "
                    "ID again. Answer the user's specific question first and do not "
                    "repeat a full investigation when a concise follow-up answer is "
                    "appropriate. Prioritize technician actions when asked what to "
                    "check. Use tools when current machine-specific evidence is "
                    "needed, but use sufficient conversation evidence directly when "
                    "it already answers the question. "
                    "The latest conversation messages are persistent memory; use "
                    "them to resolve follow-ups and never claim to remember details "
                    "that are absent from them. For a loom investigation, use the "
                    "provided machine status, maintenance history, diagnostics, and "
                    "root-cause evidence before answering. These four tools have "
                    "already been executed for the identified loom. Do not repeat "
                    "those same lookups unless the user requests a fresh check. "
                    "Use root-cause evidence and its targeted research to prepare "
                    "the final report. "
                    "The root-cause confidence score is evidence-based, not a "
                    "scientifically validated probability. "
            
                    "Treat machine telemetry and maintenance records as "
                    "machine-specific facts. "
            
                    "Treat web research as general technical reference "
                    "information. "
            
                    "Never present a value obtained from web research as the "
                    "actual measurement of the machine. "
            
                    "Clearly distinguish between: "
                    "1. Observed facts, "
                    "2. Web references, "
                    "3. Inferences, and "
                    "4. Recommendations. "
            
                    "Clearly distinguish observed facts from inferences and "
                    "recommendations. "
            
                    "Do not present web information as machine-specific facts. "
            
                    "After gathering sufficient evidence, provide a clear "
                    "diagnosis and recommended next steps."
                ),
            
        },
        *(
            [
                {
                    "role": "system",
                    "content": (
                        "Pre-collected machine investigation evidence (tool output):\n"
                        + json.dumps(investigation_evidence, default=str)
                    ),
                }
            ]
            if investigation_evidence
            else []
        ),
        *history_messages,
        {
            "role": "user",
            "content": user_query,
        },
    ]

    for _ in range(current_settings.max_agent_rounds):
        try:
            response = active_client.chat.completions.create(
                model=current_settings.openrouter_model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            assistant_message = response.choices[0].message
        except TimeoutError:
            LOGGER.error("OpenRouter request timed out")
            return _error_response("the OpenRouter request timed out.")
        except Exception as error:
            if "timeout" in type(error).__name__.lower() or "timeout" in str(error).lower():
                LOGGER.error("OpenRouter request timed out")
                return _error_response("the OpenRouter request timed out.")
            LOGGER.error("OpenRouter request failed: %s", error)
            return _error_response(
                "the OpenRouter request failed. Check the API key, model, and network."
            )

        if not assistant_message.tool_calls:
            return assistant_message.content or _error_response(
                "OpenRouter returned an empty response."
            )

        messages.append(assistant_message)
        for tool_call in assistant_message.tool_calls:
            try:
                tool_name = tool_call.function.name
                raw_arguments = tool_call.function.arguments
                arguments = json.loads(raw_arguments)
                if not isinstance(arguments, dict):
                    result = _invalid_arguments(
                        tool_name, "Tool arguments must decode to a JSON object."
                    )
                else:
                    result = execute_tool(tool_name, arguments)
            except (json.JSONDecodeError, TypeError):
                tool_name = getattr(
                    getattr(tool_call, "function", None), "name", "unknown"
                )
                LOGGER.warning("Malformed JSON arguments for tool %s", tool_name)
                result = _invalid_arguments(
                    tool_name, "Tool arguments were not valid JSON."
                )
            except Exception as error:
                LOGGER.exception("Malformed tool call: %s", error)
                result = {
                    "success": False,
                    "error_code": "malformed_tool_call",
                    "error": "The model returned an invalid tool call.",
                }

            LOGGER.info("Tool call completed: %s", tool_name)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": getattr(tool_call, "id", "unknown"),
                    "content": json.dumps(result, default=str),
                }
            )

    LOGGER.error("Agent reached the maximum tool-call rounds")
    return _error_response("the investigation exceeded the maximum tool-call rounds.")