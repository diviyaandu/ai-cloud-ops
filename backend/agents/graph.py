"""
agents/graph.py

LangGraph orchestration graph.

Flow:
  User message
      │
  [route] ← Routing Agent (classifies intent)
      │
      ├─ operational → [operational_agent] ─┐
      ├─ security    → [security_agent]    ─┤→ [format_response] → Output
      ├─ finops      → [finops_agent]      ─┘
      └─ general     → [general_agent]    ──┘

State travels through the graph; each node reads/writes AgentState.
"""

from __future__ import annotations

import os
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from agents.router import classify_intent
from agents import operational, security, finops
from groq import Groq

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


# ── State schema ───────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    user_message: str
    history: list[dict]           # conversation history [{"role":..,"content":..}]
    intent: str                   # routing classification
    intent_confidence: float
    intent_reasoning: str
    agent_response: dict          # populated by whichever sub-agent runs
    final_answer: str             # extracted plain-text answer


# ── Node functions ─────────────────────────────────────────────────────────────

async def route_node(state: AgentState) -> AgentState:
    """Classify intent and write routing decision to state."""
    classification = await classify_intent(state["user_message"])
    return {
        **state,
        "intent": classification["intent"],
        "intent_confidence": classification.get("confidence", 1.0),
        "intent_reasoning": classification.get("reasoning", ""),
    }


async def operational_node(state: AgentState) -> AgentState:
    response = await operational.run(state["user_message"], state.get("history"))
    return {**state, "agent_response": response, "final_answer": response["answer"]}


async def security_node(state: AgentState) -> AgentState:
    response = await security.run(state["user_message"], state.get("history"))
    return {**state, "agent_response": response, "final_answer": response["answer"]}


async def finops_node(state: AgentState) -> AgentState:
    response = await finops.run(state["user_message"], state.get("history"))
    return {**state, "agent_response": response, "final_answer": response["answer"]}


async def general_node(state: AgentState) -> AgentState:
    """Handle general / off-topic messages directly with Groq."""
    import asyncio

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful cloud operations AI assistant. "
                "Answer concisely and helpfully. If the user asks about "
                "specific system metrics or security, let them know they can "
                "ask directly and you'll pull live data."
            ),
        }
    ]
    if state.get("history"):
        messages.extend(state["history"][-6:])
    messages.append({"role": "user", "content": state["user_message"]})

    loop = asyncio.get_event_loop()

    def _call():
        r = client.chat.completions.create(
            model=GROQ_MODEL, messages=messages, temperature=0.5, max_tokens=300
        )
        return r.choices[0].message.content

    answer = await loop.run_in_executor(None, _call)

    return {
        **state,
        "agent_response": {
            "agent": "general",
            "agent_label": "🤖 General Assistant",
            "answer": answer,
            "overall_status": "ok",
        },
        "final_answer": answer,
    }


# ── Routing function (edge condition) ─────────────────────────────────────────

def route_to_agent(state: AgentState) -> str:
    """Return the name of the next node based on classified intent."""
    intent_map = {
        "operational": "operational_agent",
        "security":    "security_agent",
        "finops":      "finops_agent",
        "general":     "general_agent",
    }
    return intent_map.get(state["intent"], "general_agent")


# ── Build the graph ────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("route",             route_node)
    graph.add_node("operational_agent", operational_node)
    graph.add_node("security_agent",    security_node)
    graph.add_node("finops_agent",      finops_node)
    graph.add_node("general_agent",     general_node)

    # Entry
    graph.set_entry_point("route")

    # Conditional dispatch from route → correct agent
    graph.add_conditional_edges(
        "route",
        route_to_agent,
        {
            "operational_agent": "operational_agent",
            "security_agent":    "security_agent",
            "finops_agent":      "finops_agent",
            "general_agent":     "general_agent",
        },
    )

    # All agents → END
    for node in ["operational_agent", "security_agent", "finops_agent", "general_agent"]:
        graph.add_edge(node, END)

    return graph.compile()


# Singleton compiled graph — import this in api/agent.py
compiled_graph = build_graph()


# ── Public entry point ─────────────────────────────────────────────────────────

async def run_agent(user_message: str, history: list[dict] | None = None) -> dict[str, Any]:
    """
    Main entry point. Takes a user message + optional history.
    Returns the full agent state including which agent responded.
    """
    initial_state: AgentState = {
        "user_message": user_message,
        "history": history or [],
        "intent": "",
        "intent_confidence": 0.0,
        "intent_reasoning": "",
        "agent_response": {},
        "final_answer": "",
    }

    final_state = await compiled_graph.ainvoke(initial_state)

    return {
        "answer": final_state["final_answer"],
        "agent": final_state["agent_response"].get("agent", "unknown"),
        "agent_label": final_state["agent_response"].get("agent_label", ""),
        "intent": final_state["intent"],
        "intent_confidence": final_state["intent_confidence"],
        "intent_reasoning": final_state["intent_reasoning"],
        "overall_status": final_state["agent_response"].get("overall_status", "ok"),
        "data": final_state["agent_response"],
    }