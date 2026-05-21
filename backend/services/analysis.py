import time

import state.store as store
from config.settings import ANALYSIS_COOLDOWN
from services.metrics import get_system_metrics, build_metrics_summary, metrics_changed_significantly
from services.groq_client import call_groq

_SYSTEM = "You are an expert Site Reliability Engineer. Be concise and operational."

_PROMPT_TEMPLATE = """\
Current system state:
{summary}

Provide a concise operational report:
1. Overall system status (one sentence)
2. Primary concern (if any)
3. Recommended action
Be direct and metric-specific.\
"""


async def get_analysis(force: bool = False) -> dict:
    """
    Returns cached analysis when possible.
    Calls Groq only when force=True, or cooldown elapsed AND metrics shifted.
    """
    data = await get_system_metrics()
    now  = time.monotonic()

    cooldown_ok = (now - store.last_analysis_time) >= ANALYSIS_COOLDOWN
    changed     = metrics_changed_significantly(data)
    should_call = force or (cooldown_ok and changed)

    if should_call:
        summary = build_metrics_summary(data)
        store.last_analysis = call_groq(
            system=_SYSTEM,
            messages=[{"role": "user", "content": _PROMPT_TEMPLATE.format(summary=summary)}],
            max_tokens=220,
            temperature=0.3,
        )
        store.last_analysis_time     = now
        store.last_analysis_snapshot = {k: data[k] for k in ("cpu", "memory", "disk")}

    return {
        **data,
        "analysis":             store.last_analysis or "Click 'Analyze' to generate AI analysis.",
        "analysis_fresh":       should_call,
        "groq_calls_total":     store.groq_call_count,
        "next_auto_in_seconds": max(0, int(ANALYSIS_COOLDOWN - (now - store.last_analysis_time))),
    }