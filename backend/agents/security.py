"""
agents/security.py

Security Agent — runs a live security audit and interprets findings.
All checks use Python stdlib + psutil; no external APIs required.
"""

import json
import os
from typing import Any

from groq import Groq
from tools.registry import run_full_audit

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_client: Groq | None = None


def _groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are an expert security engineer and cloud security auditor.
You have been given a live security audit of a Linux server. Answer the user's question
based on the audit findings.

Guidelines:
- Lead with the most serious finding (if any)
- For each issue, explain: WHAT it is, WHY it matters, WHAT to do
- Use severity language: CRITICAL / WARNING / OK
- Be concise — 3–4 short paragraphs maximum
- If everything looks clean, say so clearly and briefly
- Don't pad the response with generic security advice unless directly relevant
"""


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

    # 1. Run all security checks concurrently
    try:
        audit = await run_full_audit()
    except Exception as e:
        audit = {"error": str(e), "overall_status": "unknown"}

    overall_status = audit.get("overall_status", "unknown")

    # 2. Build prompt
    audit_summary = json.dumps(audit, indent=2)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        messages.extend(history[-6:])

    messages.append({
        "role": "user",
        "content": (
            f"LIVE SECURITY AUDIT RESULTS:\n```json\n{audit_summary}\n```\n\n"
            f"USER QUESTION: {user_message}"
        ),
    })

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