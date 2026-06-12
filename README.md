# AI Cloud Ops

An AI-powered Azure cloud operations dashboard. Ask natural language questions about your Azure infrastructure — the system routes your query to the right specialist agent, pulls live data from Azure, and returns actionable insights. Write-back actions (tagging, scaling, stop/start) go through a human-approval gate before touching Azure.

---

## Features

- **Multi-agent AI** — Operational, Security, FinOps, and General agents powered by Groq (`llama-3.1-8b-instant`)
- **Live Azure data** — Resource Graph, Log Analytics, Azure Advisor, Cost Management
- **Dynamic tool selection** — LLM picks the right tools per query, no hardcoded routing
- **Write-back with approval gate** — agents propose actions; humans approve or reject in the UI
- **Resource investigations** — ask about a specific named resource and get full details
- **Session-based credentials** — connect with SP credentials at runtime via the UI modal
- **Tag filtering** — filter inventory by Azure tags
- **Auto-refresh** — polls Azure data on a configurable interval; manual refresh button available

---

## Tech Stack

| Layer    | Technology                                                              |
| -------- | ----------------------------------------------------------------------- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind v4, Recharts                 |
| Backend  | FastAPI, Python, LangGraph                                              |
| AI       | Groq API (`llama-3.1-8b-instant`)                                       |
| Tool bus | MCP server (port 8001)                                                  |
| Azure    | Resource Graph, Log Analytics, Advisor, Cost Management, Container Apps |

---

## Prerequisites

- Node.js 18+
- Python 3.11+
- Azure Service Principal with Contributor role on target resource groups
- Groq API key

---

## Setup

### 1. Clone

```bash
git clone https://github.com/your-org/ai-cloud-ops.git
cd ai-cloud-ops
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in values
```

`.env`:

```env
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>
AZURE_ALLOWED_RGS=rg-finops-prod,rg-finopsai-dev
AZURE_LOG_ANALYTICS_WORKSPACE_ID=<your-workspace-guid>
GROQ_API_KEY=<your-groq-key>
GROQ_MODEL=llama-3.1-8b-instant
AZURE_SESSION_TTL_SECONDS=3600
```

### 3. Frontend

```bash
cd frontend
npm install
```

---

## Running

```bash
# Terminal 1 — FastAPI backend
cd backend && python -m uvicorn main:app --port 8000 --reload

# Terminal 2 — MCP tool server
cd backend && python -m uvicorn mcp_server.server:app --port 8001 --reload

# Terminal 3 — Next.js frontend
cd frontend && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Docker

```bash
docker-compose up --build
```

---

## Agent Architecture

Each chat message triggers 3 Groq calls:

```
User message
  → Router         (classify: operational / security / finops / general)
  → Tool Selector  (pick 1–4 tools relevant to the query)
  → Specialist     (call tools, generate answer)
```

| Agent       | Focus                                          |
| ----------- | ---------------------------------------------- |
| Operational | Resource health, inventory, logs, failed ops   |
| Security    | Untagged resources, governance, recent changes |
| FinOps      | Costs, budget, anomalies, Advisor savings      |
| General     | Freeform Azure questions                       |

---

## Write-back Actions

Agents can propose actions. Nothing executes until a human approves in the UI.

| Action                | Description                                     |
| --------------------- | ----------------------------------------------- |
| `apply_tags`          | Tag a resource                                  |
| `stop_container_app`  | Scale Container App replicas to 0               |
| `start_container_app` | Scale Container App replicas to 1+              |
| `stop_vm`             | Deallocate a VM                                 |
| `start_vm`            | Start a VM                                      |
| `scale_app_service`   | Change App Service plan SKU/capacity            |
| `delete_resource`     | Delete a resource (blocked outside allowed RGs) |

### REST API

```
POST   /actions                  queue an action
GET    /actions                  list all actions
POST   /actions/{id}/approve     approve and execute
POST   /actions/{id}/reject      reject
```

---

## Session Credentials

Connect a Service Principal at runtime without restarting the backend:

```bash
curl -X POST http://localhost:8000/session/connect \
  -H "Content-Type: application/json" \
  -d '{"subscription_id":"...","tenant_id":"...","client_id":"...","client_secret":"..."}'

curl http://localhost:8000/session/status
curl -X POST http://localhost:8000/session/disconnect
```

Sessions are in-memory and expire after `AZURE_SESSION_TTL_SECONDS` (default 1 hour).

---

## Project Structure

```
ai-cloud-ops/
├── frontend/
│   ├── app/page.tsx
│   ├── components/
│   │   ├── layout/        # Topbar, Sidebar, AzureConnection modal
│   │   ├── dashboard/     # InsightCards, AlertsPanel, ActionsPanel, CloudIntelligence
│   │   ├── chat/          # AgentPanel
│   │   └── views/         # OverviewView, AgentView, AlertsView, ActionsView
│   ├── hooks/             # useCloudResources, useCloudSummary, useAgent
│   ├── services/api.ts
│   └── styles/
└── backend/
    ├── agents/            # router, tool_selector, operational, security, finops
    ├── tools/             # azure_resource_graph, azure_cost, azure_log_analytics,
    │                      # azure_advisor, azure_write
    ├── routes/            # cloud_resources, cloud_summary, actions, session, chat
    ├── mcp_server/        # MCP tool bus (port 8001)
    ├── state/             # action_store (in-memory), session_store
    └── main.py
```

---

## Known Limitations

- Action queue is in-memory — cleared on backend restart
- Cost Management API is partially restricted on Azure student accounts
- No user authentication — SP credentials are shared across all sessions
