# AI Cloud Ops — Handoff

## Project

Full-stack AI-powered Azure cloud operations dashboard.

## Directory Structure

```
ai-cloud-ops/
├── frontend/
│   ├── app/
│   │   └── page.tsx
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── CloudIntelligence.tsx
│   │   │   ├── InsightCards.tsx
│   │   │   ├── AlertsPanel.tsx
│   │   │   ├── AnalysisPanel.tsx
│   │   │   └── ActionsPanel.tsx          ← NEW
│   │   └── chat/
│   │       └── AgentPanel.tsx
│   ├── hooks/
│   │   └── useCloudResources.ts
│   ├── styles/
│   │   ├── global.css
│   │   ├── layout.css
│   │   ├── cards.css
│   │   ├── dashboard.css
│   │   ├── filters.css
│   │   ├── chat.css
│   │   ├── alerts.css
│   │   ├── analysis.css
│   │   └── ic.css
│   └── types/
│       └── cloud.ts
└── backend/
    ├── main.py
    ├── agents/
    │   ├── graph.py
    │   ├── router.py
    │   ├── operational.py
    │   ├── security.py
    │   ├── finops.py
    │   ├── actions.py                    ← NEW
    │   └── tool_selector.py              ← NEW
    ├── api/
    │   └── agent.py
    ├── routes/
    │   ├── cloud_resources.py
    │   ├── cloud_summary.py
    │   ├── cloud_tags.py
    │   ├── analysis.py
    │   ├── chat.py
    │   ├── metrics.py
    │   └── actions.py                    ← NEW
    ├── tools/
    │   ├── registry.py
    │   ├── azure_resource_graph.py
    │   ├── azure_cost.py
    │   ├── azure_log_analytics.py
    │   ├── azure_advisor.py
    │   └── azure_write.py                ← NEW
    ├── mcp_server/
    │   ├── server.py
    │   └── client.py
    ├── state/
    │   ├── store.py
    │   └── action_store.py               ← NEW
    └── terraform/
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        ├── resource_group.tf
        └── terraform.tfvars.example
```

## Tech Stack

- **Frontend**: Next.js, TypeScript, Tailwind, Recharts, modular CSS
- **Backend**: FastAPI (port 8000), MCP server (port 8001)
- **AI**: Groq (`llama-3.1-8b-instant`), LangGraph
- **Azure**: Resource Graph, Cost Management, Log Analytics (`law-finopsai-dev`, `rg-finopsai-dev`), Azure Advisor
- **Auth**: Service Principal with Contributor role (scoped to both RGs)

## Azure Subscription

- Subscription: `d91323a4-7619-4450-8e88-c17d3cd3df5e`
- Resource groups: `rg-finops-prod`, `rg-finopsai-dev`
- Student account — Cost Management API partially restricted
- 24 resources across eastus/eastus2/Korea Central

## Environment Variables

```env
AZURE_SUBSCRIPTION_ID=d91323a4-7619-4450-8e88-c17d3cd3df5e
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=bb8accbd-2957-41ab-a7ce-5e253b829c7e
AZURE_CLIENT_SECRET=<your-secret>
AZURE_ALLOWED_RGS=rg-finops-prod,rg-finopsai-dev
AZURE_LOG_ANALYTICS_WORKSPACE_ID=<your-workspace-id>
GROQ_API_KEY=<your-groq-key>
GROQ_MODEL=llama-3.1-8b-instant
```

## Current Feature Status

| Feature                                                  | Status     |
| -------------------------------------------------------- | ---------- |
| Azure Resource Graph (live inventory)                    | ✅ Working |
| Dynamic resource cards (fully data-driven)               | ✅ Working |
| CloudIntelligence panel (dynamic charts)                 | ✅ Working |
| Multi-agent system (Operational/Security/FinOps/General) | ✅ Working |
| Router intent classification                             | ✅ Working |
| Log Analytics integration                                | ✅ Working |
| Azure Advisor integration                                | ✅ Working |
| InsightCards (predicted spend, health, security, logs)   | ✅ Working |
| Terraform IaC skeleton                                   | ✅ Created |
| Tag filtering (backend + frontend)                       | ✅ Working |
| Groq call counter                                        | ✅ Working |
| Write-back action tools                                  | ✅ Working |
| Action approval queue (backend)                          | ✅ Working |
| Actions REST endpoints                                   | ✅ Working |
| ActionsPanel UI (Approve/Reject)                         | ✅ Working |
| Agent auto-proposes tagging actions                      | ✅ Working |
| Dynamic tool selection per agent query                   | ✅ Working |
| SP upgraded to Contributor on both RGs                   | ✅ Done    |
| Debug/noise logging removed                              | ✅ Done    |

## Agent Architecture

Each user query = 3 Groq calls (router + tool selector + specialist):

- **Router** → classifies into operational / security / finops / general
- **Tool Selector** → picks 1-4 relevant tools dynamically per query
- **Operational** → allowed tools: `get_resource_inventory`, `get_unhealthy_resources`, `get_resource_group_summary`, `get_log_summary`, `get_recent_errors`, `get_failed_operations`, `get_resource_health_logs`, `get_full_resource_report`
- **Security** → allowed tools: `get_untagged_resources`, `get_recently_modified_resources`, `get_unhealthy_resources`, `get_advisor_security_recommendations`, `get_advisor_reliability_recommendations`, `get_resource_health_logs`, `get_failed_operations`, `get_full_resource_report`
- **FinOps** → allowed tools: `get_monthly_spend`, `get_daily_spend`, `get_cost_by_resource_group`, `get_budget_status`, `get_cost_anomalies`, `get_full_cost_report`, `get_advisor_cost_recommendations`, `get_untagged_resources`, `get_full_resource_report`
- **General** → direct Groq call, no tools

All tool calls go via MCP server (port 8001) → `tools/registry.py` → Azure APIs.

## Write-back + Approval Gate

### How It Works

1. Agent detects actionable finding (e.g. untagged resources)
2. Agent calls `propose_action()` → action enters queue with status `pending`
3. Actions panel in UI shows pending queue
4. Human clicks Approve → action executes against Azure
5. Human clicks Reject → action marked rejected, nothing touches Azure

### Action Types

| Action              | Params                                                |
| ------------------- | ----------------------------------------------------- |
| `apply_tags`        | `resource_id`, `tags` (dict)                          |
| `stop_vm`           | `resource_group`, `vm_name`                           |
| `start_vm`          | `resource_group`, `vm_name`                           |
| `scale_app_service` | `resource_group`, `plan_name`, `sku_name`, `capacity` |
| `delete_resource`   | `resource_id`                                         |

### Guardrails

- All write actions check resource group against `ALLOWED_RGS` env var
- SP Contributor role scoped to `rg-finops-prod` and `rg-finopsai-dev` only
- No action executes without explicit UI approval
- `delete_resource` and `stop_vm` blocked outside allowed RGs

### REST Endpoints

```
POST   /actions                    queue an action
GET    /actions                    list all actions
POST   /actions/{id}/approve       approve and execute
POST   /actions/{id}/reject        reject without executing
```

### Action Statuses

```
pending → approved → executed
                  → failed
       → rejected
```

## Known Issues / Next Up

1. **Untagged resource `id` field** — KQL in `_real_untagged_resources()` now includes `id`, but verify actions are being queued after a FinOps query. If still empty, some resource types may not return `id` from Resource Graph.

2. **security.py dynamic tool selection** — implemented but not fully tested yet.

3. **Action store is in-memory** — restarts clear the queue. Consider persisting to SQLite or Redis if needed.

4. **No write tools registered in MCP registry** — `azure_write.py` functions are called directly from `routes/actions.py`, not via MCP. If you want agents to propose actions via tool calls in future, register them in `tools/registry.py` with a `propose_` prefix.

5. **Possible next features**:
   - Email/Teams notification on action proposal
   - Action history log (persist executed/rejected actions)
   - Bulk approve
   - Azure Policy integration for automated tagging enforcement

## Running The Project

```bash
# Terminal 1
cd backend && python -m uvicorn main:app --port 8000 --reload

# Terminal 2
cd backend && python -m uvicorn mcp_server.server:app --port 8001 --reload

# Terminal 3
cd frontend && npm run dev
```

## Testing via PowerShell

```powershell
# Queue an action manually
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/actions" `
  -ContentType "application/json" `
  -Body '{"action_type":"apply_tags","params":{"resource_id":"<resource-id>","tags":{"env":"dev"}},"proposed_by":"agent"}'

# List actions
Invoke-RestMethod -Uri "http://localhost:8000/actions"

# Approve
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/actions/<id>/approve"

# Reject
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/actions/<id>/reject"

# Get real resource IDs
az resource list --resource-group rg-finopsai-dev --query "[].id" -o tsv
```

## Preferences

- Responses under 150 words unless more detail requested
- Exact file paths and diffs over prose
- Code changes only, no descriptions unless asked
- Testing via PowerShell `Invoke-RestMethod`
