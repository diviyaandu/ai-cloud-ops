"""
tools/prometheus.py

Queries your live Prometheus instance for operational metrics.
Prometheus is expected at PROMETHEUS_URL (default: http://localhost:9090).
"""

import os
import httpx
from datetime import datetime, timedelta
from typing import Any

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")


# ── Low-level helpers ──────────────────────────────────────────────────────────

async def _query(promql: str) -> dict[str, Any]:
    """Instant PromQL query → raw Prometheus JSON."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
        )
        r.raise_for_status()
        return r.json()


async def _query_range(promql: str, hours: int = 1) -> dict[str, Any]:
    """Range PromQL query over the last N hours, 60s step."""
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={
                "query": promql,
                "start": start.isoformat() + "Z",
                "end": end.isoformat() + "Z",
                "step": "60s",
            },
        )
        r.raise_for_status()
        return r.json()


def _scalar(result: dict) -> float | None:
    """Extract first scalar value from an instant query result."""
    try:
        return float(result["data"]["result"][0]["value"][1])
    except (IndexError, KeyError, ValueError):
        return None


# ── Public tool functions (called by Operational Agent) ───────────────────────

async def get_cpu_usage() -> dict[str, Any]:
    """Average CPU usage across all nodes, 5-minute window (%)."""
    result = await _query(
        '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
    )
    value = _scalar(result)
    return {
        "metric": "cpu_usage_percent",
        "value": round(value, 2) if value is not None else None,
        "unit": "%",
        "status": _threshold(value, warn=70, crit=90),
        "description": "Average CPU utilisation across all nodes (5m avg)",
    }


async def get_memory_usage() -> dict[str, Any]:
    """Memory utilisation percentage."""
    result = await _query(
        "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
    )
    value = _scalar(result)
    return {
        "metric": "memory_usage_percent",
        "value": round(value, 2) if value is not None else None,
        "unit": "%",
        "status": _threshold(value, warn=75, crit=90),
        "description": "Memory utilisation across all nodes",
    }


async def get_disk_usage() -> dict[str, Any]:
    """Root filesystem utilisation percentage."""
    result = await _query(
        'sum(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100'
    )
    value = _scalar(result)
    return {
        "metric": "disk_usage_percent",
        "value": round(value, 2) if value is not None else None,
        "unit": "%",
        "status": _threshold(value, warn=80, crit=95),
        "description": "Root filesystem utilisation",
    }


async def get_http_error_rate() -> dict[str, Any]:
    """HTTP 5xx error rate (requests/sec) over last 5 minutes."""
    result = await _query(
        'sum(rate(http_requests_total{status=~"5.."}[5m])) or vector(0)'
    )
    value = _scalar(result)
    return {
        "metric": "http_error_rate_rps",
        "value": round(value, 4) if value is not None else None,
        "unit": "req/s",
        "status": _threshold(value, warn=0.1, crit=1.0),
        "description": "HTTP 5xx error rate (5m window)",
    }


async def get_network_io() -> dict[str, Any]:
    """Network receive + transmit throughput (bytes/sec)."""
    rx = await _query("sum(rate(node_network_receive_bytes_total[5m]))")
    tx = await _query("sum(rate(node_network_transmit_bytes_total[5m]))")
    rx_val = _scalar(rx)
    tx_val = _scalar(tx)
    return {
        "metric": "network_io",
        "receive_bytes_per_sec": round(rx_val, 2) if rx_val is not None else None,
        "transmit_bytes_per_sec": round(tx_val, 2) if tx_val is not None else None,
        "unit": "bytes/s",
        "status": "ok",
        "description": "Network I/O throughput across all interfaces",
    }


async def get_system_load() -> dict[str, Any]:
    """1-minute and 15-minute load averages."""
    load1 = await _query("node_load1")
    load15 = await _query("node_load15")
    cpu_count_result = await _query("count(node_cpu_seconds_total{mode='idle'})")
    l1 = _scalar(load1)
    l15 = _scalar(load15)
    cpus = _scalar(cpu_count_result) or 1
    # Normalised load: load / cpu_count — warn at 0.7, crit at 1.0
    normalised = (l1 / cpus) * 100 if l1 is not None else None
    return {
        "metric": "system_load",
        "load_1m": round(l1, 2) if l1 is not None else None,
        "load_15m": round(l15, 2) if l15 is not None else None,
        "cpu_count": int(cpus),
        "status": _threshold(normalised, warn=70, crit=100),
        "description": "System load averages (1m / 15m)",
    }


async def get_all_metrics() -> dict[str, Any]:
    """Fetch all operational metrics in one call. Used by the Operational Agent."""
    import asyncio
    cpu, mem, disk, http_err, net, load = await asyncio.gather(
        get_cpu_usage(),
        get_memory_usage(),
        get_disk_usage(),
        get_http_error_rate(),
        get_network_io(),
        get_system_load(),
        return_exceptions=True,
    )
    results = {}
    for label, val in [
        ("cpu", cpu), ("memory", mem), ("disk", disk),
        ("http_errors", http_err), ("network", net), ("load", load),
    ]:
        if isinstance(val, Exception):
            results[label] = {"error": str(val)}
        else:
            results[label] = val

    # Derive an overall health status
    statuses = [v.get("status") for v in results.values() if isinstance(v, dict) and "status" in v]
    if "critical" in statuses:
        overall = "critical"
    elif "warning" in statuses:
        overall = "warning"
    else:
        overall = "ok"

    results["overall_status"] = overall
    return results


# ── Internal helper ────────────────────────────────────────────────────────────

def _threshold(value: float | None, warn: float, crit: float) -> str:
    if value is None:
        return "unknown"
    if value >= crit:
        return "critical"
    if value >= warn:
        return "warning"
    return "ok"