"""
mcp_server/server.py

Lightweight MCP-style HTTP server.

WHY THIS EXISTS — the architectural shift:
  Before: Agent → import tools.registry → call_tool() [in-process, same memory space]
  After:  Agent → HTTP POST /execute     → MCP server → call_tool() [network boundary]

The network boundary is the key change. It means:
  - Tools can run in a separate process or container from agents
  - Any HTTP client (agent, curl, another service) can invoke any tool
  - Tools become independently deployable and scalable
  - This is the same pattern the MCP spec uses — a server exposing tools over a
    transport (HTTP here, stdio in the official SDK)

This is intentionally minimal:
  - No auth (add API key header when you need it)
  - No websockets (not needed for request/response tools)
  - No streaming (add if tools ever produce incremental output)
  - No MCP SDK dependency (we implement the same contract, lighter)

Run standalone:
    cd backend/
    uvicorn mcp_server.server:app --port 8001 --reload

Or mount into main FastAPI app:
    from mcp_server.server import app as mcp_app
    main_app.mount("/mcp", mcp_app)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Reuse the existing registry — no reimplementation needed.
# TOOL_REGISTRY and call_tool() are preserved exactly as-is.
from tools.registry import TOOL_REGISTRY, call_tool

app = FastAPI(
    title="MCP Tool Server",
    description="Exposes the tool registry over HTTP in an MCP-style interface",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Request / Response models ──────────────────────────────────────────────────

class ExecuteRequest(BaseModel):
    tool: str
    params: dict = {}


class ExecuteResponse(BaseModel):
    tool: str
    result: dict
    ok: bool = True


class ErrorResponse(BaseModel):
    tool: str
    error: str
    ok: bool = False


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/tools")
async def list_tools() -> dict:
    """
    Return all tool names registered in the tool registry.

    Agents call this at startup (or on demand) to discover what tools
    are available — the same discovery pattern used in the MCP spec.
    """
    return {
        "tools": list(TOOL_REGISTRY.keys()),
        "count": len(TOOL_REGISTRY),
    }


@app.post("/execute")
async def execute_tool(req: ExecuteRequest) -> dict:
    """
    Execute a registered tool by name with optional params.

    This is the single entrypoint for all tool execution.
    Agents no longer import or await tools directly — they POST here.

    Flow:
        Agent → POST /execute {"tool": "get_all_metrics", "params": {}}
                    ↓
              call_tool() from tools/registry.py   ← unchanged
                    ↓
              tool function (prometheus.py etc.)   ← unchanged
                    ↓
              JSON result → HTTP response → Agent

    The tools/registry.py and every tool file are completely unchanged.
    We are only adding a network boundary on top of what already exists.
    """
    if req.tool not in TOOL_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Tool '{req.tool}' not found",
                "available_tools": list(TOOL_REGISTRY.keys()),
            },
        )

    try:
        result = await call_tool(req.tool, **req.params)
    except TypeError as e:
        # Wrong params passed for this tool
        raise HTTPException(
            status_code=422,
            detail={"error": f"Invalid params for tool '{req.tool}': {e}"},
        )
    except Exception as e:
        # Tool itself raised — return structured error, don't crash the server
        raise HTTPException(
            status_code=500,
            detail={"error": f"Tool '{req.tool}' failed: {e}"},
        )

    return {
        "tool": req.tool,
        "result": result,
        "ok": True,
    }


@app.get("/health")
async def health() -> dict:
    """Simple liveness check."""
    return {"status": "ok", "tools_registered": len(TOOL_REGISTRY)}