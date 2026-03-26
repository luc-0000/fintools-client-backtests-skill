# Backend Spec Index

This spec bundle documents the `backend/` codebase as an implementation-grade reference for replication and migration.

## Scope

- Included: `manage.py`, `service.conf`, `pyproject.toml`, `db/`, `end_points/`, `data_processing/`, `mcp_servers/`, `local_agents/`, `remote_agents_a2a/`, `personal_agents/`, `scripts/`
- Excluded by design: `backups/`, `__pycache__/`, generated report/output folders, `pomltrace/`, images used only as artifacts, and other runtime byproducts

## Documents

- [00_Overview/PROJECT.md](./00_Overview/PROJECT.md)
- [00_Overview/ARCHITECTURE.md](./00_Overview/ARCHITECTURE.md)
- [01_Configuration/ENVIRONMENT.md](./01_Configuration/ENVIRONMENT.md)
- [02_Data/ENTITIES.md](./02_Data/ENTITIES.md)
- [03_API/ENDPOINTS.md](./03_API/ENDPOINTS.md)
- [04_Business_Logic/WORKFLOWS.md](./04_Business_Logic/WORKFLOWS.md)
- [05_Agents/AGENTS_AND_MCP.md](./05_Agents/AGENTS_AND_MCP.md)
- [06_Operations/MAINTENANCE.md](./06_Operations/MAINTENANCE.md)
- [08_Testing/TEST_SPECS.md](./08_Testing/TEST_SPECS.md)
- [09_Verification/COVERAGE_REPORT.md](./09_Verification/COVERAGE_REPORT.md)
- [09_Verification/KNOWN_GAPS.md](./09_Verification/KNOWN_GAPS.md)

## Reading Order

1. Start with `PROJECT.md` and `ARCHITECTURE.md`.
2. Read `ENVIRONMENT.md` and `ENTITIES.md` before reproducing runtime behavior.
3. Use `ENDPOINTS.md` and `WORKFLOWS.md` to reimplement the HTTP and trading logic.
4. Use `AGENTS_AND_MCP.md` for the LLM-agent and tool topology.
5. Use `COVERAGE_REPORT.md` and `KNOWN_GAPS.md` before claiming replication completeness.
