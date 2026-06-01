import time
import json

import state.store as store
from services.groq_client import call_groq
from tools.azure_resource_graph import get_resource_inventory, get_unhealthy_resources

ANALYSIS_COOLDOWN = 60  # seconds

_SYSTEM = "You are an expert Azure Cloud Operations engineer. Be concise and actionable."

_PROMPT_TEMPLATE = """\
Current Azure resource inventory:
{summary}

Provide a concise cloud operations report:
1. Overall infrastructure status (one sentence)
2. Primary concern or risk (if any)
3. Recommended action
Be direct and specific to the resources shown.\
"""


async def get_analysis(force: bool = False) -> dict:
    now = time.monotonic()
    cooldown_ok = (now - store.last_analysis_time) >= ANALYSIS_COOLDOWN
    should_call = force or cooldown_ok

    if should_call:
        try:
            inventory = await get_resource_inventory()
            unhealthy = await get_unhealthy_resources()
        except Exception as e:
            inventory = {"error": str(e)}
            unhealthy = {}

        summary = json.dumps({
            "inventory": inventory,
            "unhealthy": unhealthy,
        }, indent=2)

        store.last_analysis = call_groq(
            system=_SYSTEM,
            messages=[{"role": "user", "content": _PROMPT_TEMPLATE.format(summary=summary)}],
            max_tokens=220,
            temperature=0.3,
        )
        store.last_analysis_time = now

    return {
        "analysis": store.last_analysis or "Click ▶ ANALYZE to run cloud infrastructure analysis.",
        "analysis_fresh": should_call,
        "groq_calls_total": store.groq_call_count,
    }