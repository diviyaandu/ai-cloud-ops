"""
mcp_server/client.py

Thin async HTTP client for the MCP tool server.

WHY A SHARED CLIENT:
  Every agent that switches from direct call_tool() to HTTP needs the same
  boilerplate: build the URL, POST JSON, handle errors, parse the result.
  Centralising it here means agents stay clean — one import, one function call.

  In-process (old):
      result = await call_tool("get_all_metrics")

  Via MCP server (new):
      result = await mcp_call("get_all_metrics")

  The call site is nearly identical. The difference is that the tool now
  executes on the other side of a network socket — making it independently
  deployable, observable (logs at the server), and callable by anything.
"""

import os
import httpx
from typing import Any

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001")

# Timeout: most tools are fast (psutil, Prometheus queries).
# Security audit (run_full_audit) scans the filesystem — give it more time.
DEFAULT_TIMEOUT = 30.0


async def mcp_call(tool: str, params: dict | None = None, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """
    Call a tool on the MCP server and return its result dict.

    Args:
        tool:    Tool name as registered in TOOL_REGISTRY
        params:  Optional keyword args forwarded to the tool function
        timeout: HTTP timeout in seconds (default 30s)

    Returns:
        The tool's result dict (same shape as direct call_tool() returns)

    Raises:
        RuntimeError: if the server returns an error or is unreachable
    """
    payload = {"tool": tool, "params": params or {}}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{MCP_SERVER_URL}/execute", json=payload)
    except httpx.ConnectError:
        raise RuntimeError(
            f"MCP server unreachable at {MCP_SERVER_URL}. "
            "Start it with: uvicorn mcp_server.server:app --port 8001"
        )
    except httpx.TimeoutException:
        raise RuntimeError(f"MCP server timed out executing tool '{tool}' after {timeout}s")

    if response.status_code == 404:
        detail = response.json().get("detail", {})
        raise KeyError(f"Tool '{tool}' not registered on MCP server. {detail}")

    if not response.is_success:
        detail = response.json().get("detail", response.text)
        raise RuntimeError(f"MCP server error for tool '{tool}': {detail}")

    body = response.json()
    return body["result"]


async def mcp_list_tools() -> list[str]:
    """Fetch the list of available tool names from the MCP server."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MCP_SERVER_URL}/tools")
            response.raise_for_status()
            return response.json()["tools"]
    except Exception as e:
        raise RuntimeError(f"Could not fetch tool list from MCP server: {e}")