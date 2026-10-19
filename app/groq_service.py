"""
Groq-powered chat layer for POST /chat.

Uses Groq's OpenAI-compatible chat completions API with manual tool
calling: we hand Groq a JSON schema describing each tools.py function,
Groq decides which one (if any) to call and with what arguments, we
execute it locally in Python, then send the result back to Groq for a
natural-language summary.

Falls back to the deterministic rule-based agent (agent.run_agent) if:
  - GROQ_API_KEY isn't set in the environment or .env
  - the Groq call raises for any reason (network, quota, bad response,
    auth failure, token-limit, etc.)

This means /chat keeps working with zero external dependency when no API
key is configured, or when Groq is temporarily unavailable -- Groq only
upgrades the experience, it is never a hard requirement.
"""

import os
import json
import logging
from typing import Optional, Dict, Any

from . import tools
from . import agent as rule_based_agent
from app.config import GROQ_MODEL_NAME, BASE_DIR

logger = logging.getLogger("customer_segmentation.groq_service")

_MAX_TOOL_RESULT_CHARS = 4000

SYSTEM_INSTRUCTION = (
    "You are a retail banking analytics assistant for a customer "
    "segmentation tool. Use the available tools to answer questions about "
    "customer segmentation, feature engineering, data preprocessing, "
    "EDA, customer segments, personas, retention risk, and individual "
    "customers. Always call a tool to get real numbers rather than "
    "guessing or estimating."
)

_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "explainability_tool",
            "description": (
                "Explain why a specific customer was assigned to their "
                "cluster, comparing their attributes (income, balance, "
                "credit score, transactions, investment, digital score) "
                "against the cluster average."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "The numeric ID of the customer to explain.",
                    },
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_segment",
            "description": (
                "Look up which cluster/segment a specific customer belongs "
                "to and their basic segment info."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "The numeric ID of the customer to look up.",
                    },
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retention_tool",
            "description": (
                "Analyze customer engagement and recommend customer retention, "
                "cross-selling, premium upgrades, investment opportunities, "
                "loan eligibility, and next-best banking actions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster": {
                        "type": "integer",
                        "description": (
                            "Optional cluster number to filter retention "
                            "results to. Omit to get all clusters."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "eda_tool",
            "description": (
                "Get exploratory data analysis / summary statistics, "
                "optionally filtered to a single cluster. If no cluster is "
                "given, returns stats across all clusters."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster": {
                        "type": "integer",
                        "description": (
                            "Optional cluster number to filter EDA results "
                            "to. Omit to get all clusters."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "segmentation_tool",
            "description": (
                "Summarize customer segments identified by K-Means clustering. "
                "Return personas, customer counts, business characteristics, "
                "average financial metrics, business value, and recommended "
                "banking products for each segment."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "feature_engineering_tool",
            "description": (
                "Explain the feature engineering and preprocessing pipeline "
                "used before K-Means customer segmentation."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
]

_TOOL_FN_MAP = {
    "explainability_tool": tools.explainability_tool,
    "get_customer_segment": tools.get_customer_segment,
    "retention_tool": tools.retention_tool,
    "eda_tool": tools.eda_tool,
    "segmentation_tool": tools.segmentation_tool,
    "feature_engineering_tool": tools.feature_engineering_tool,
}


def get_groq_api_key() -> str:
    """Dynamically reads GROQ_API_KEY from environment."""
    return os.getenv("GROQ_API_KEY", "").strip()


def get_groq_client():
    """Dynamically initializes and returns a Groq client if key is set."""
    key = get_groq_api_key()
    if not key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=key)
    except Exception as e:
        logger.warning("Could not initialize Groq client: %s", e)
        return None


def is_groq_configured() -> bool:
    return bool(get_groq_api_key())


def test_and_set_groq_key(new_key: str) -> Dict[str, Any]:
    """
    Validates a Groq API key against Groq's API and persists it to .env.
    """
    key = new_key.strip()
    if not key:
        return {"success": False, "message": "API key cannot be empty."}

    try:
        from groq import Groq
        test_client = Groq(api_key=key)
        # Test call to verify validity
        test_client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=3,
        )
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg or "Invalid API Key" in err_msg:
            return {"success": False, "message": "Invalid Groq API Key. Please verify key from console.groq.com/keys."}
        return {"success": False, "message": f"Groq verification failed: {err_msg}"}

    # Update runtime environment
    os.environ["GROQ_API_KEY"] = key

    # Persist in .env
    try:
        env_file = BASE_DIR / ".env"
        existing_lines = []
        if env_file.exists():
            existing_lines = env_file.read_text(encoding="utf-8").splitlines()
        
        filtered = [l for l in existing_lines if not l.startswith("GROQ_API_KEY=")]
        filtered.append(f"GROQ_API_KEY={key}")
        env_file.write_text("\n".join(filtered) + "\n", encoding="utf-8")
    except Exception as e:
        logger.warning("Could not write key to .env file: %s", e)

    return {"success": True, "message": f"Groq API key activated successfully for model {GROQ_MODEL_NAME}."}


def clear_groq_key() -> Dict[str, Any]:
    """Removes the Groq API key and reverts to rule-based agent."""
    os.environ["GROQ_API_KEY"] = ""
    try:
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            existing_lines = env_file.read_text(encoding="utf-8").splitlines()
            filtered = [l for l in existing_lines if not l.startswith("GROQ_API_KEY=")]
            env_file.write_text("\n".join(filtered) + "\n", encoding="utf-8")
    except Exception as e:
        logger.warning("Could not clear key from .env file: %s", e)

    return {"success": True, "message": "Groq API key cleared. Reverted to local analytical agent."}


def _serialize_tool_result(raw_result) -> str:
    """
    Turns a tool's raw return value into a JSON string capped at _MAX_TOOL_RESULT_CHARS.
    """
    if raw_result is None:
        return "null"

    full = json.dumps(raw_result)
    if len(full) <= _MAX_TOOL_RESULT_CHARS:
        return full

    return full[:_MAX_TOOL_RESULT_CHARS] + "... (truncated for length)"


def _run_groq_turn(client, query: str) -> dict:
    """
    Sends the query to Groq with manual tool calling enabled.
    """
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": query},
    ]

    first_response = client.chat.completions.create(
        model=GROQ_MODEL_NAME,
        messages=messages,
        tools=_TOOL_SCHEMAS,
        tool_choice="auto",
    )

    choice = first_response.choices[0]
    tool_calls = choice.message.tool_calls

    if not tool_calls:
        return {
            "response": choice.message.content,
            "execution_plan": [f"Groq ({GROQ_MODEL_NAME}) answered directly"],
            "results": {},
        }

    call = tool_calls[0]
    tool_name = call.function.name
    try:
        tool_args = json.loads(call.function.arguments)
    except (json.JSONDecodeError, TypeError):
        tool_args = {}

    raw_result = None
    if tool_name in _TOOL_FN_MAP:
        try:
            raw_result = _TOOL_FN_MAP[tool_name](**tool_args)
        except Exception as e:
            raw_result = {"error": str(e)}

    # Send tool result back to Groq for natural language summarization
    messages.append(choice.message)
    messages.append(
        {
            "role": "tool",
            "tool_call_id": call.id,
            "content": _serialize_tool_result(raw_result),
        }
    )

    second_response = client.chat.completions.create(
        model=GROQ_MODEL_NAME,
        messages=messages,
    )

    summary_text = second_response.choices[0].message.content

    return {
        "response": summary_text,
        "execution_plan": [
            f"Groq LLM parsed query",
            f"Executed tool: {tool_name}",
            f"Groq ({GROQ_MODEL_NAME}) synthesized analytical summary",
        ],
        "results": raw_result if isinstance(raw_result, (dict, list)) else {},
    }


def generate_chat_response(query: str) -> dict:
    """
    Main entrypoint for POST /chat.
    Tries Groq LLM first if configured, falls back to deterministic rule-based agent.
    """
    client = get_groq_client()
    if client is not None:
        try:
            return _run_groq_turn(client, query)
        except Exception as e:
            logger.warning("Groq inference call failed: %s; falling back to rule-based agent", e)
            fallback_result = rule_based_agent.run_agent(query)
            formatted = rule_based_agent.to_chat_response(fallback_result)
            formatted["execution_plan"] = [
                f"Groq API call encountered an issue: {e}",
                "Synthesized answer using local analytical agent",
            ] + formatted["execution_plan"]
            return formatted

    # Local deterministic rule-based agent
    fallback_result = rule_based_agent.run_agent(query)
    formatted = rule_based_agent.to_chat_response(fallback_result)
    formatted["execution_plan"] = [
        "Local analytical agent (Add Groq API key to activate LLaMA 3.1 LLM)"
    ] + formatted["execution_plan"]
    return formatted