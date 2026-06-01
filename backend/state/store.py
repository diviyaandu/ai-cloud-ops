"""
Centralised mutable state.

All modules import from here so state is never scattered
across multiple files or duplicated as globals.
"""
import asyncio

# ── Metrics cache ──────────────────────────────────────────
metrics_cache: dict       = {}
metrics_lock:  asyncio.Lock = asyncio.Lock()
last_collected: float      = 0.0

# ── Analysis cache ─────────────────────────────────────────
last_analysis:          str   = ""
last_analysis_time:     float = 0.0
last_analysis_snapshot: dict  = {}

# ── Telemetry ──────────────────────────────────────────────
groq_call_count: int = 0

def increment_groq_calls() -> int:
    global groq_call_count
    groq_call_count += 1
    return groq_call_count