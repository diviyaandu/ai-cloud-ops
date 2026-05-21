"""
api/agent.py

POST /agent — the new multi-agent endpoint.
Drop this router into your existing main.py alongside /chat, /metrics, /analyze.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.graph import run_agent

router = APIRouter()


class AgentRequest(BaseModel):
    message: str
    history: list[dict] = []  # [{"role": "user"|"assistant", "content": str}]
    # Optionally force a specific agent (bypass routing):
    force_agent: str | None = None  # "operational" | "security" | "finops" | None


class AgentResponse(BaseModel):
    answer: str
    agent: str           # which sub-agent handled it
    agent_label: str     # emoji + readable label e.g. "⚙️ Operational Agent"
    intent: str          # routing classification
    intent_confidence: float
    intent_reasoning: str
    overall_status: str  # "ok" | "warning" | "critical" | "unknown"
    data: dict           # raw agent payload (metrics snapshot, audit results, etc.)


@router.post("/agent", response_model=AgentResponse)
async def agent_endpoint(req: AgentRequest):
    """
    Multi-agent endpoint. Routes the user's message to the correct specialist agent:
    - Operational Agent  → live Prometheus metrics
    - Security Agent     → live security audit (ports, SSH, processes)
    - FinOps Agent       → Azure cost data (mocked until credentials set)
    - General Agent      → catch-all for off-topic messages

    Pass `history` as a list of prior turns for multi-turn context.
    Pass `force_agent` to skip routing and hit a specific agent directly.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    # If caller wants to bypass routing
    if req.force_agent:
        message_with_hint = req.message
        # Inject a routing hint via message prefix so the router picks the right agent
        intent_hints = {
            "operational": "What are the current system metrics? ",
            "security":    "Run a security audit. ",
            "finops":      "What are the Azure costs? ",
        }
        hint = intent_hints.get(req.force_agent, "")
        message_with_hint = hint + req.message if hint else req.message
    else:
        message_with_hint = req.message

    try:
        result = await run_agent(message_with_hint, req.history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    return AgentResponse(**result)