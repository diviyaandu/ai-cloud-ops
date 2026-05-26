"""
agents/security.py

Security Agent — runs a live security audit and interprets findings.
All checks use Python stdlib + psutil; no external APIs required.
"""

import json
import os
from typing import Any

from groq import Groq
from mcp_server.client import mcp_call

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_client: Groq | None = None


def _groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


SYSTEM_PROMPT = """Security auditor AI. Given audit JSON, respond in 3 paragraphs max.
Lead with worst finding. For each issue: what it is, why it matters, what to do.
Use CRITICAL/WARNING/OK labels. If clean, say so briefly."""


async def run(user_message: str, history: list[dict] | None = None) -> dict[str, Any]:
    """
    Run a full security audit and generate a security-focused response.

    Returns:
        {
            "agent": "security",
            "answer": str,
            "audit_results": dict,
            "overall_status": str,
        }
    """
    import asyncio

    # 1. Run all security checks via MCP server
    try:
        audit = await mcp_call("run_full_audit")
    except Exception as e:
        audit = {"error": str(e), "overall_status": "unknown"}

    overall_status = audit.get("overall_status", "unknown")

    # Only status + one-line summary per check — no lists, no raw data
    trimmed = {"overall_status": audit.get("overall_status")}
    for key, val in audit.items():
        if isinstance(val, dict) and key != "overall_status":
            trimmed[key] = {
                "status":  val.get("status", "unknown"),
                "summary": val.get("summary", ""),
            }
    audit_summary = json.dumps(trimmed)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"AUDIT:\n{audit_summary}\n\nQ: {user_message}"},
    ]

    # 3. Call Groq
    loop = asyncio.get_event_loop()

    def _call():
        response = _groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=600,
        )
        return response.choices[0].message.content

    answer = await loop.run_in_executor(None, _call)

    return {
        "agent": "security",
        "agent_label": "🔒 Security Agent",
        "answer": answer,
        "audit_results": audit,
        "overall_status": overall_status,
    }