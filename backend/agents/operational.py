"""
agents/operational.py

Operational Agent — answers questions about Azure resource health and inventory.
Pulls live data from Azure Resource Graph via the MCP server.
"""

import json
import os
import asyncio
from typing import Any

from groq import Groq
from agents.tool_selector import select_tools
from agents.actions import propose_action
from mcp_server.client import mcp_call
import state.store as store

ALLOWED_TOOLS = [
    "get_resource_inventory", "get_unhealthy_resources",
    "get_resource_group_summary", "get_log_summary",
    "get_recent_errors", "get_failed_operations",
    "get_resource_health_logs", "get_full_resource_report",
    "get_resource_details",
]

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_client: Groq | None = None


def _groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are an expert Azure cloud operations engineer.
You have been given live data from Azure Resource Graph about the user's subscription.
Answer the user's question concisely and precisely based on this data.

Guidelines:
- Lead with the most important finding (unhealthy resources, recent changes, or inventory summary)
- Reference specific resource names, types, and regions where relevant
- If resources are unhealthy or recently modified, highlight them
- Suggest concrete next steps where relevant
- Be concise — 3 paragraphs maximum
- Status levels: ok = healthy, warning = investigate, critical = act now
- If the user asked to start or stop a VM, confirm the action has been queued for approval — do not say you cannot do it
"""


async def run(user_message: str, history: list[dict] | None = None) -> dict[str, Any]:
    # 1. Select tools dynamically
    tools = await select_tools(user_message, allowed=ALLOWED_TOOLS)

    # 2. Extract resource name/group hints from the query
    import re
    rg_match   = re.search(r'rg[-\w]+', user_message, re.IGNORECASE)
    name_match = re.search(r'([a-z][a-z0-9\-]{2,40})', user_message, re.IGNORECASE)
    hinted_rg   = rg_match.group(0).lower()   if rg_match   else ""
    hinted_name = name_match.group(1).lower()  if name_match else ""

    # 3. Call selected tools in parallel
    async def _call(tool_name: str):
        if tool_name == "get_resource_details":
            from tools.azure_resource_graph import get_resource_details
            return await get_resource_details(
                resource_name=hinted_name, resource_group=hinted_rg
            )
        return await mcp_call(tool_name)

    results = await asyncio.gather(
        *[_call(t) for t in tools], return_exceptions=True
    )
    tool_data = {
        t: (r if not isinstance(r, Exception) else {"error": str(r)})
        for t, r in zip(tools, results)
    }

    overall_status = "ok"
    for v in tool_data.values():
        s = v.get("status", "ok")
        if s == "critical":
            overall_status = "critical"
        elif s == "warning" and overall_status != "critical":
            overall_status = "warning"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-2:])

    tool_json = json.dumps(tool_data, indent=2)
    if len(tool_json) > 3000:
        tool_json = tool_json[:3000] + "\n... (truncated)"

    messages.append({
        "role": "user",
        "content": (
            f"AZURE DATA:\n```json\n{tool_json}\n```\n\n"
            f"USER QUESTION: {user_message}"
        ),
    })

    loop = asyncio.get_event_loop()

    def _call():
        response = _groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=512,
        )
        store.increment_groq_calls()
        return response.choices[0].message.content

    answer = await loop.run_in_executor(None, _call)

    # Propose start/stop actions if user intent detected
    import re as _re
    proposed_actions = []
    msg_lower = user_message.lower()
    is_stop  = bool(_re.search(r"stop|shutdown|deallocate", msg_lower))
    is_start = bool(_re.search(r"start|power.?on", msg_lower))
    is_container_app = bool(_re.search(r'\bca-\w+|container.?app\b', msg_lower))

    if (is_stop or is_start) and hinted_name and hinted_rg:
        if is_container_app or hinted_name.startswith("ca-"):
            action_type = "stop_container_app" if is_stop else "start_container_app"
            params = {"resource_group": hinted_rg, "app_name": hinted_name}
        else:
            action_type = "stop_vm" if is_stop else "start_vm"
            params = {"resource_group": hinted_rg, "vm_name": hinted_name}
        proposed_actions.append(propose_action(action_type, params, proposed_by="operational-agent"))

    return {
        "agent": "operational",
        "agent_label": "⚙️ Operational Agent",
        "answer": answer,
        "tool_data": tool_data,
        "overall_status": overall_status,
        "proposed_actions": proposed_actions,
    }