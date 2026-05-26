"""
agents/operational.py

Operational Agent — answers questions about system health using real Prometheus data.

ARCHITECTURE CHANGE:
  Before: metrics = await get_all_metrics()          [direct in-process call]
  After:  metrics = await mcp_call("get_all_metrics") [HTTP → MCP server → tool]

  The agent no longer imports or executes tool functions directly.
  It sends an HTTP request to the MCP server, which owns tool execution.
  The tool result comes back as JSON over the wire — identical shape to before.

  Why this matters:
    - The MCP server can be scaled, restarted, or swapped independently
    - Tool execution is now observable at the network layer (logs, traces)
    - Any future agent (or external client) can call the same tool the same way
    - agents/ has zero direct dependency on tools/ module code
"""

import json
import os
from typing import Any

from groq import Groq
from mcp_server.client import mcp_call  # ← replaces: from tools.registry import get_all_metrics

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_client: Groq | None = None


def _groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) AI assistant.
You have been given live system metrics from Prometheus. Answer the user's question
concisely and precisely. Focus on actionable insights. If something looks wrong, say
what it is and what to do about it. Use plain language — no jargon unless the user
clearly knows what they're doing.

Metric status levels: ok = healthy, warning = investigate, critical = act now.

Format your response in 2–3 short paragraphs maximum. Lead with the most important finding.
"""


async def run(user_message: str, history: list[dict] | None = None) -> dict[str, Any]:
    """
    Fetch live metrics via MCP server and generate an SRE-focused response.

    Returns:
        {
            "agent": "operational",
            "answer": str,
            "metrics_snapshot": dict,
            "overall_status": str,
        }
    """
    import asyncio

    # 1. Fetch live Prometheus data through the MCP server.
    #
    #    OLD: metrics = await get_all_metrics()
    #    NEW: metrics = await mcp_call("get_all_metrics")
    #
    #    The result dict is identical — only the execution path changed.
    #    If the MCP server is down, mcp_call() raises RuntimeError and we
    #    catch it below, same as before.
    try:
        metrics = await mcp_call("get_all_metrics")
    except Exception as e:
        metrics = {"error": str(e), "overall_status": "unknown"}

    overall_status = metrics.get("overall_status", "unknown")

    # 2. Build the prompt (unchanged)
    metrics_summary = json.dumps(metrics, indent=2)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        messages.extend(history[-6:])

    messages.append({
        "role": "user",
        "content": (
            f"LIVE METRICS (from Prometheus):\n```json\n{metrics_summary}\n```\n\n"
            f"USER QUESTION: {user_message}"
        ),
    })

    # 3. Call Groq (unchanged)
    loop = asyncio.get_event_loop()

    def _call():
        response = _groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=512,
        )
        return response.choices[0].message.content

    answer = await loop.run_in_executor(None, _call)

    return {
        "agent": "operational",
        "agent_label": "⚙️ Operational Agent",
        "answer": answer,
        "metrics_snapshot": metrics,
        "overall_status": overall_status,
    }