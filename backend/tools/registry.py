"""
tools/registry.py

Central tool registry — the MCP tool bus.
Each agent imports from here rather than directly from tool modules.
Keeps the tool surface explicit and testable.
"""

from tools.prometheus import (
    get_cpu_usage,
    get_memory_usage,
    get_disk_usage,
    get_http_error_rate,
    get_network_io,
    get_system_load,
    get_all_metrics,
)

from tools.security_checks import (
    check_open_ports,
    check_failed_ssh_logins,
    check_suspicious_processes,
    check_root_equivalent_users,
    check_world_writable_files,
    run_full_audit,
)

from tools.azure_cost import (
    get_monthly_spend,
    get_daily_spend,
    get_cost_by_resource_group,
    get_budget_status,
    get_cost_anomalies,
    get_full_cost_report,
)

# Tool registry: maps tool name (used in LangGraph) → callable
TOOL_REGISTRY: dict = {
    # Operational / Prometheus
    "get_cpu_usage":        get_cpu_usage,
    "get_memory_usage":     get_memory_usage,
    "get_disk_usage":       get_disk_usage,
    "get_http_error_rate":  get_http_error_rate,
    "get_network_io":       get_network_io,
    "get_system_load":      get_system_load,
    "get_all_metrics":      get_all_metrics,
    # Security
    "check_open_ports":              check_open_ports,
    "check_failed_ssh_logins":       check_failed_ssh_logins,
    "check_suspicious_processes":    check_suspicious_processes,
    "check_root_equivalent_users":   check_root_equivalent_users,
    "check_world_writable_files":    check_world_writable_files,
    "run_full_audit":                run_full_audit,
    # FinOps
    "get_monthly_spend":             get_monthly_spend,
    "get_daily_spend":               get_daily_spend,
    "get_cost_by_resource_group":    get_cost_by_resource_group,
    "get_budget_status":             get_budget_status,
    "get_cost_anomalies":            get_cost_anomalies,
    "get_full_cost_report":          get_full_cost_report,
}


async def call_tool(name: str, **kwargs) -> dict:
    """Call a registered tool by name. Raises KeyError if not found."""
    if name not in TOOL_REGISTRY:
        raise KeyError(f"Unknown tool: {name!r}. Available: {list(TOOL_REGISTRY)}")
    return await TOOL_REGISTRY[name](**kwargs)