# Backend Project Spec

## Identity

- Project root: `backend/`
- Runtime style: FastAPI application with SQLAlchemy-backed CRUD/services, plus local and remote trading agents
- Entry command: `python manage.py`
- HTTP server: Uvicorn hosting `end_points.main:app`
- Primary problem domain: stock pools, rules, rule-to-stock signaling, simulator replay, and agent-based trading decisions

## Source Anchors

- Source: manage.py
- Source: end_points/main.py
- Source: end_points/config/routes.py
- Source: pyproject.toml

## What Exists

- HTTP API modules:
  - `end_points/get_pool`
  - `end_points/get_stock`
  - `end_points/get_rule`
  - `end_points/get_simulator`
- Shared runtime:
  - `end_points/init_global.py`
  - `end_points/config/db_init.py`
  - `end_points/config/global_var.py`
  - `end_points/common/`
- Persistence:
  - `db/models.py`
  - `../../config.json`
- Data ingestion:
  - `data_processing/data_provider/*`
  - `data_processing/update_stocks/*`
- Agent/tool subsystems:
  - `local_agents/*`
  - `mcp_servers/*`
  - `remote_agents_a2a/*`
  - `personal_agents/*`
- Maintenance scripts:
  - `scripts/create_tables.py`
  - `scripts/export_database.py`
  - `scripts/import_data.py`
  - `scripts/init_db.sh`

## Technology Stack

- Python >= 3.11
- FastAPI + Uvicorn
- SQLAlchemy + SQLite
- Pydantic request/response schemas
- Tushare / Akshare / Mairui for market data
- LangChain / LangGraph / FastMCP / A2A-related libraries for agent execution

## Replication Intent

To replicate this backend, an implementation must preserve:

- The HTTP resource model for pools, stocks, rules, and simulators
- The multi-database session wrapper and bind-key access pattern
- The agent rule execution model:
  - `rule.info` holds either a local module path or a remote agent base URL
  - agent runs emit `AgentTrading` rows
  - simulators derive replay/trading metrics from `AgentTrading`
- The simulator sell logic:
  - profit threshold
  - stop loss
  - max holding days
- The MCP tool layer that feeds local agents with market, technical, and news context

## Explicit Non-Goals In This Spec Bundle

- It does not preserve runtime dumps in `backups/`
- It does not treat generated report folders as source of truth
- It does not document every experimental file under `local_agents/fingenius` as stable API; those are captured as internal implementation surfaces with noted uncertainty
