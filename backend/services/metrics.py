import asyncio
import time

import psutil

import state.store as store
from config.settings import (
    METRICS_CACHE_TTL,
    CPU_WARN, CPU_CRIT,
    MEM_WARN, MEM_CRIT,
    DISK_WARN, DISK_CRIT,
    CHANGE_THRESHOLD,
)


async def get_system_metrics() -> dict:
    """
    Collect CPU / memory / disk at most once per METRICS_CACHE_TTL seconds.
    Uses run_in_executor so psutil never blocks the event loop.
    """
    async with store.metrics_lock:
        now = time.monotonic()
        if now - store.last_collected < METRICS_CACHE_TTL and store.metrics_cache:
            return store.metrics_cache.copy()

        loop = asyncio.get_running_loop()
        cpu, memory, disk = await asyncio.gather(
            loop.run_in_executor(None, lambda: psutil.cpu_percent(interval=None)),
            loop.run_in_executor(None, lambda: psutil.virtual_memory().percent),
            loop.run_in_executor(None, lambda: psutil.disk_usage("/").percent),
        )

        alerts   = _build_alerts(cpu, memory, disk)
        severity = _classify_severity(cpu, memory, disk)

        result = {
            "cpu":      round(cpu,    1),
            "memory":   round(memory, 1),
            "disk":     round(disk,   1),
            "alerts":   alerts,
            "severity": severity,
        }

        store.metrics_cache.clear()
        store.metrics_cache.update(result)
        store.last_collected = now
        return result


def build_metrics_summary(data: dict) -> str:
    alerts_str = data["alerts"] if data["alerts"] else "none"
    return (
        f"CPU: {data['cpu']}%  |  Memory: {data['memory']}%  |  "
        f"Disk: {data['disk']}%  |  Severity: {data['severity']}\n"
        f"Active alerts: {alerts_str}"
    )


def metrics_changed_significantly(new: dict) -> bool:
    """True if any metric shifted >= CHANGE_THRESHOLD since last analysis."""
    if not store.last_analysis_snapshot:
        return True
    return any(
        abs(new.get(k, 0) - store.last_analysis_snapshot.get(k, 0)) >= CHANGE_THRESHOLD
        for k in ("cpu", "memory", "disk")
    )


# ── Helpers ────────────────────────────────────────────────

def _build_alerts(cpu: float, memory: float, disk: float) -> list[str]:
    alerts = []
    if cpu > CPU_CRIT:
        alerts.append(f"[HIGH] CPU at {cpu}% — exceeds {CPU_CRIT}% threshold")
    elif cpu > CPU_WARN:
        alerts.append(f"[WARN] CPU at {cpu}% — approaching limit")

    if memory > MEM_CRIT:
        alerts.append(f"[HIGH] Memory at {memory}% — exceeds {MEM_CRIT}% threshold")
    elif memory > MEM_WARN:
        alerts.append(f"[WARN] Memory at {memory}% — approaching limit")

    if disk > DISK_CRIT:
        alerts.append(f"[HIGH] Disk at {disk}% — critically full")
    elif disk > DISK_WARN:
        alerts.append(f"[WARN] Disk at {disk}% — getting full")
    return alerts


def _classify_severity(cpu: float, memory: float, disk: float) -> str:
    if cpu > CPU_CRIT or memory > MEM_CRIT:
        return "High"
    if cpu > CPU_WARN or memory > MEM_WARN or disk > DISK_WARN:
        return "Medium"
    return "Low"