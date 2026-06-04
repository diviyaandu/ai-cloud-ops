Here's the full flow from user input to displayed answer:

---

**1. User types a message** in the AI Copilot panel and hits send.

**2. `AgentPanel` (frontend)** packages the message + conversation history into a JSON body and POSTs to `http://127.0.0.1:8000/agent`.

**3. `api/agent.py`** receives the request. If `force_agent` was set, it prepends a routing hint to the message (e.g. "Run a security audit. " + original message). Then calls `run_agent(message, history)` from `agents/graph.py`.

**4. `agents/graph.py`** creates the initial `AgentState` — a TypedDict holding the message, history, intent, and placeholders for the response. It passes this into the compiled LangGraph graph, which starts at the `route` node.

**5. `route_node` → `agents/router.py`** makes **Groq call #1** (`temperature=0.1`, `max_tokens=128`). The system prompt lists the 4 intent categories with examples. The model returns a JSON object like `{"intent": "operational", "confidence": 0.97, "reasoning": "..."}`. The router strips any markdown fences, parses the JSON, validates the intent value, increments the Groq call counter in `state/store.py`, and writes intent + confidence + reasoning back into `AgentState`.

**6. `route_to_agent()`** reads `state["intent"]` and returns the name of the next node. LangGraph's conditional edge dispatches to one of: `operational_agent`, `security_agent`, `finops_agent`, or `general_agent`.

**7. The specialist agent node runs.** Using operational as the example:

- `operational_node` calls `operational.run(message, history)`
- It calls `mcp_call("get_all_metrics")` — an HTTP request to the MCP server on port 8001
- The MCP server executes `tools/prometheus.py` against Prometheus and returns live metrics JSON
- The agent builds a prompt: system prompt (SRE persona) + last 6 history turns + the metrics JSON + the user's question
- **Groq call #2** (`temperature=0.3`, `max_tokens=512`) generates a natural language answer
- Groq call counter incremented again in `store.py`
- Returns `{agent, agent_label, answer, metrics_snapshot, overall_status}`

For **security**: same pattern but `mcp_call("run_full_audit")` → `tools/security_checks.py` (psutil, local system).
For **finops**: `mcp_call("get_full_cost_report")` + `mcp_call("get_full_resource_report")` → Azure Cost Management + Resource Graph.
For **general**: no tool call, just a direct Groq call inside `general_node` itself.

**8. The agent writes** `agent_response` and `final_answer` into `AgentState` and the node exits to `END`.

**9. `run_agent()` in `graph.py`** extracts the final state and returns a flat dict: `answer`, `agent`, `agent_label`, `intent`, `intent_confidence`, `intent_reasoning`, `overall_status`, `data`.

**10. `api/agent.py`** wraps this in `AgentResponse` (Pydantic model) and returns it as JSON with HTTP 200.

**11. `AgentPanel` (frontend)** receives the response, appends the assistant message to the conversation history with the `agent_label` shown as a badge, and renders the answer text.

---

**Where things live:**

| Concern              | Location                                                                                                  |
| -------------------- | --------------------------------------------------------------------------------------------------------- |
| Conversation history | Frontend React state in `AgentPanel` — sent on every request, never stored server-side                    |
| Groq call count      | `state/store.py` — in-memory global, reset on server restart                                              |
| Analysis cache       | `state/store.py` — used by `/analyze` route, not the agent                                                |
| Prompt construction  | `agents/router.py` (routing prompt), each specialist agent file (task prompt)                             |
| LLM calls            | Router: `router.py`. Specialists: `operational.py`, `security.py`, `finops.py`, `graph.py` (general node) |
| Tool calls           | MCP server on port 8001 via `mcp_server/client.py` → `tools/`                                             |
| Error handling       | `mcp_call()` try/catch in each agent; HTTP 500 in `api/agent.py`; JSON parse fallback in `router.py`      |

**Frontend-only:** `AgentPanel`, message rendering, history state, the POST call itself.
**Backend-only:** `graph.py`, `router.py`, all agent files, `store.py`, MCP server, all `tools/` modules.
**Bridge:** `api/agent.py` — the single HTTP boundary between them.

# AI Cloud Ops — Full Workflow & Handoff

## What This Is

A full-stack AI-powered Azure cloud operations dashboard. It lets you monitor your Azure subscription, chat with AI agents that pull live cloud data, and run on-demand infrastructure analysis — all in one UI.

---

## Tech Stack

| Layer               | Technology                             |
| ------------------- | -------------------------------------- |
| Frontend            | Next.js · Tailwind · Recharts          |
| Backend             | FastAPI (port 8000)                    |
| MCP Tool Server     | FastAPI (port 8001)                    |
| AI Model            | Groq · `llama-3.1-8b-instant`          |
| Agent Orchestration | LangGraph                              |
| Cloud Data          | Azure Resource Graph + Cost Management |

---

## Architecture Overview

```
Browser (Next.js)
    │
    ├── GET /cloud-resources  ──→ Azure Resource Graph (live inventory)
    ├── GET /stats            ──→ Groq call counter
    ├── GET /analyze          ──→ AI cloud analysis (on demand)
    └── POST /agent           ──→ Multi-agent AI system
                                        │
                              LangGraph orchestration
                                        │
                          ┌─────────────┴─────────────┐
                      Router Agent (Groq)         classifies intent
                          │
              ┌───────────┼───────────┬───────────┐
         Operational   Security    FinOps      General
           Agent        Agent      Agent       Agent
              │            │          │
         mcp_call()   mcp_call()  mcp_call()
              │
         MCP Server (port 8001)
              │
         tools/registry.py
              │
    ┌─────────┴──────────┐
    Azure Resource Graph  Azure Cost Management
```

---

## How a User Query Flows (Step by Step)

**1. User types a message** in the AI Copilot panel → `POST /agent`

**2. `api/agent.py`** receives `{ message, history, force_agent }` and calls `run_agent()`

**3. LangGraph** (`agents/graph.py`) initializes `AgentState` and enters the `route` node

**4. Router** (`agents/router.py`) makes **Groq call #1** with `temperature=0.1` — model returns:

```json
{ "intent": "operational", "confidence": 0.97, "reasoning": "..." }
```

Intent is validated and written to state. Rules:

- Resource health / status / what's running → `operational`
- Costs / spend / billing → `finops`
- Ports / SSH / audit → `security`
- Everything else → `general`

**5. Graph dispatches** to the correct agent node based on intent

**6. Specialist agent runs** — example using Operational:

- Calls `mcp_call("get_resource_inventory")` and `mcp_call("get_unhealthy_resources")` via HTTP to port 8001
- MCP server executes `tools/azure_resource_graph.py` against the Azure Resource Graph REST API
- Tool result (live JSON) is injected into the prompt
- **Groq call #2** (`temperature=0.3`, `max_tokens=512`) generates a natural language answer

**7. Response** flows back through LangGraph state → `AgentResponse` → frontend

Each query = **2 Groq calls** (1 router + 1 specialist), tracked in `state/store.py` and exposed via `GET /stats`.

---

## The Four Agents

| Agent       | Triggered by                                  | Data source                            | Tools used                                          |
| ----------- | --------------------------------------------- | -------------------------------------- | --------------------------------------------------- |
| Operational | Resource health, what's running, infra status | Azure Resource Graph                   | `get_resource_inventory`, `get_unhealthy_resources` |
| FinOps      | Costs, spend, budgets, billing                | Azure Cost Management + Resource Graph | `get_full_cost_report`, `get_full_resource_report`  |
| Security    | Ports, SSH, audit, vulnerabilities            | Local system (psutil)                  | `run_full_audit`                                    |
| General     | Greetings, off-topic                          | None                                   | Direct Groq call                                    |

---

## Frontend Structure

```
page.tsx (app shell)
├── Topbar        — live clock, resource count, Groq call counter, Azure status
├── Sidebar       — navigation between 4 views
└── Views
    ├── Overview  — resource inventory cards + CloudIntelligence panel + alerts
    ├── AI Copilot — full multi-agent chat (AgentPanel)
    ├── Analysis  — on-demand AI cloud analysis (AnalysisPanel → GET /analyze)
    └── Alerts    — AlertsPanel
```

**Key frontend hooks:**

- `useCloudResources()` — polls `GET /cloud-resources` every 30s for live Azure inventory
- `useGroqStats()` — polls `GET /stats` every 5s for Groq call count

---

## Azure Setup

- **Subscription:** `SUB-KEY`
- **Resource Group:** `rg-finops-prod`
- **Auth:** Service Principal with Reader role (env vars: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`)
- **Known resources:** 2× Cognitive Services (eastus, eastus2), 1× Storage Account (eastus)
- **Limitations:** Student account — Cost Management API restricted, Resource Graph fully working

---

## Running the Project

```bash
# Terminal 1 — main backend
cd backend
python -m uvicorn main:app --port 8000 --reload

# Terminal 2 — MCP tool server
cd backend
python -m uvicorn mcp_server.server:app --port 8001 --reload

# Terminal 3 — frontend
cd frontend
npm run dev
```

---

## Current State

| Feature                               | Status                                    |
| ------------------------------------- | ----------------------------------------- |
| Azure Resource Graph (live inventory) | ✅ Working                                |
| Cloud resource dashboard cards        | ✅ Working                                |
| CloudIntelligence panel with filters  | ✅ Working                                |
| Multi-agent system (all 4 agents)     | ✅ Working                                |
| Groq call counter (live)              | ✅ Working                                |
| On-demand cloud analysis              | ✅ Working                                |
| Router intent classification          | ✅ Fixed (resource queries → operational) |
| Azure Cost Management                 | ⚠️ Restricted (student account)           |
| Security agent                        | ⚠️ Monitors local system, not Azure       |

---

## Suggested Next Steps

1. Add VM power state to resource inventory (Azure Monitor query)
2. Wire Security agent to Azure Security Center instead of local psutil
3. Add `CognitiveServices` as top-level key in `/cloud-resources` response (backend already supports it via `RESOURCE_TYPE_MAP`)
4. Log Analytics / App Insights integration
5. Deploy backend + frontend to Azure (App Service or Container Apps)
