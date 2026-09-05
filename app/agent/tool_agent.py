import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools.machine_tools import get_machine_status
from tools.maintenance_tools import get_maintenance_history
from tools.research_tools import web_research

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


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
]


def execute_tool(tool_name, arguments):
    """Execute an available tool."""

    if tool_name == "get_machine_status":
        return get_machine_status(arguments["loom_id"])

    if tool_name == "get_maintenance_history":
        return get_maintenance_history(arguments["loom_id"])

    if tool_name == "web_research":
        return web_research(arguments["query"])
    return {
        "success": False,
        "error": f"Unknown tool: {tool_name}",
    }


def run_agent(user_query: str):

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
        {
            "role": "user",
            "content": user_query,
        },
    ]

    while True:

        response = client.chat.completions.create(
            model=os.getenv("OPENROUTER_MODEL"),
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        # No tool call → agent has finished reasoning
        if not assistant_message.tool_calls:

            return assistant_message.content

        # Add the assistant's tool request to conversation
        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            arguments = json.loads(
                tool_call.function.arguments
            )

            print(f"\n[TOOL CALL] {tool_name}")
            print(f"[ARGUMENTS] {arguments}")

            result = execute_tool(
                tool_name,
                arguments,
            )

            print("[TOOL RESULT]")
            print(json.dumps(result, indent=2))

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )