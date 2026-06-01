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

- **Subscription:** `d91323a4-7619-4450-8e88-c17d3cd3df5e`
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

Next step:
Implement three enhancements across the existing codebase: \*\*(1) integrate Terraform as the Infrastructure-as-Code layer for Azure resource provisioning, with a structure that supports future AI-generated Terraform workflows and allows correlation between Terraform-managed and discovered resources; (2) introduce a standardized Azure tagging strategy (Project, Environment, Owner, Application) and ensure tags are included in resource discovery, normalized in backend responses, and automatically applied to Terraform-created resources; and (3) add frontend resource filtering based on these tags, including dynamic filter values, multi-filter support, active filter display, clear-filter functionality, and any required backend API support for tag-based filtering. Preserve all existing functionality and follow the current project architecture and coding patterns.
