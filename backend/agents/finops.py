"""
agents/finops.py

FinOps Agent — analyses Azure cloud costs and provides spend insights.
Currently uses mocked data. When Azure credentials are ready:
  - Set USE_REAL_AZURE = True in tools/azure_cost.py
  - No changes needed here.
"""

import json
import os
from typing import Any

from groq import Groq
from tools.registry import get_full_cost_report

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_client: Groq | None = None


def _groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are an expert FinOps engineer specialising in Azure cloud cost optimisation.
You have been given a full cost report for an Azure subscription. Answer the user's question
based on the cost data.

Guidelines:
- Lead with the most actionable finding (overspend, anomaly, or biggest cost driver)
- Always reference specific dollar amounts from the data
- Suggest concrete cost-saving actions where relevant
- Note if data is from a mock/demo environment
- Be concise — 3 paragraphs maximum
- Format currency as $X,XXX.XX
"""


async def run(user_message: str, history: list[dict] | None = None) -> dict[str, Any]:
    """
    Fetch cost data and generate a FinOps-focused response.

    Returns:
        {
            "agent": "finops",
            "answer": str,
            "cost_report": dict,
            "overall_status": str,
        }
    """
    import asyncio

    # 1. Fetch cost data (mock or real depending on USE_REAL_AZURE flag)
    try:
        cost_report = await get_full_cost_report()
    except Exception as e:
        cost_report = {"error": str(e), "mode": "error"}

    # Derive overall status from budget + anomalies
    budget = cost_report.get("budget_status", {})
    anomalies = cost_report.get("anomalies", {})
    statuses = [budget.get("status", "ok"), anomalies.get("status", "ok")]
    if "critical" in statuses:
        overall_status = "critical"
    elif "warning" in statuses:
        overall_status = "warning"
    else:
        overall_status = "ok"

    # 2. Build prompt
    cost_summary = json.dumps(cost_report, indent=2)
    mode_note = "(NOTE: this is MOCK data — set USE_REAL_AZURE=True in tools/azure_cost.py for live data)" \
        if cost_report.get("mode") == "mock" else ""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        messages.extend(history[-6:])

    messages.append({
        "role": "user",
        "content": (
            f"AZURE COST REPORT {mode_note}:\n```json\n{cost_summary}\n```\n\n"
            f"USER QUESTION: {user_message}"
        ),
    })

    # 3. Call Groq
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
        "agent": "finops",
        "agent_label": "💰 FinOps Agent",
        "answer": answer,
        "cost_report": cost_report,
        "overall_status": overall_status,
        "data_mode": cost_report.get("mode", "unknown"),
    }