# Capability Matrix

This matrix records the currently implemented capability surface of the skill.

Status values:

- `implemented`: confirmed in current code
- `covered`: has explicit automated coverage today
- `gap`: implemented but not adequately protected by current tests

## Capability Inventory

| ID | Capability | Status | Primary Evidence | Current Coverage |
|---|---|---|---|---|
| CAP-001 | Wrapper CLI requires `--agent-type`, `--mode`, `--stock-code`, `--agent-url` | implemented | `scripts/run_agent_client.py` `ensure_required()` | covered |
| CAP-001A | Public skill downloader CLI requires `--skill-id` as the top-level target for public skill archive downloads | implemented | `scripts/download_skill.py` `parse_args()` | covered |
| CAP-002 | Only `streaming` and `polling` are accepted mode names | implemented | `scripts/run_agent_client.py` `normalize_mode()` | covered |
| CAP-003 | Supported combinations are `trading/deep_research` x `streaming/polling` | implemented | `run_inside_env()` dispatch branches | partially covered |
| CAP-004 | Unsupported agent/mode combinations fail explicitly instead of silently remapping | implemented | `run_inside_env()` final `fail(...)` branch | gap |
| CAP-005 | Skill validates bundled layout by requiring `agents_client/` and `requirements.txt` | implemented | `validate_skill_layout()` | covered |
| CAP-006 | Skill remains runnable after being copied out of the original parent repo | implemented | skill-root-relative imports and files | covered |
| CAP-007 | `--work-dir` is treated as parent directory, not direct run directory | implemented | `ensure_work_dir()` + `create_run_dir()` | gap |
| CAP-008 | Default parent directory is `skill_root/.runtime/runs` when `--work-dir` is not provided | implemented | `default_runs_parent_dir()` and `ensure_work_dir()` | covered |
| CAP-009 | Streaming probe uses the same default parent directory under `skill_root/.runtime/runs` | implemented | `scripts/stream_probe.py` `default_parent_dir()` | covered |
| CAP-010 | Each execution creates a unique run directory named `fintools-agent-client-run-*` | implemented | `create_run_dir()` | covered |
| CAP-011 | Name collisions in the same second are resolved with `-002`, `-003`, ... | implemented | `create_run_dir()` | covered |
| CAP-012 | Access token resolution order is CLI, env, cached parent token | implemented | `resolve_access_token()` | partially covered |
| CAP-013 | Access token is cached into parent directory for later runs | implemented | `save_access_token()` from `resolve_access_token()` | partially covered |
| CAP-014 | Runtime selection prefers current Python 3.10+, then discovered Python 3.10+, then conda | implemented | `find_python_runtime()` | gap |
| CAP-015 | Skill runtime lives under `skill_root/.runtime/env` instead of the run parent directory | implemented | `local_runtime_dir()` and `ensure_local_runtime()` | covered |
| CAP-016 | Local runtime auto-installs or auto-updates when the environment is missing or `requirements.txt` changed | implemented | `ensure_local_runtime()`, `create_local_runtime()`, `update_local_runtime()` | partially covered |
| CAP-017 | Child execution is re-execed with unbuffered Python output | implemented | `main()` child args + env | covered |
| CAP-018 | Child execution exports runtime metadata via `FINTOOLS_RUNTIME_*` env vars | implemented | `main()` child env | partially covered |
| CAP-019 | `run.log` is created in the run directory and mirrors stdout/stderr | implemented | `TeeStream` + `run_inside_env()` | gap |
| CAP-020 | `summary.json` is always written with stable top-level fields | implemented | `write_summary()` + `run_inside_env()` | partially covered |
| CAP-021 | `summary.json` includes `report_path`, `log_path`, `run_dir`, runtime metadata, success, and error | implemented | `run_inside_env()` summary payload | partially covered |
| CAP-021A | `summary.json` includes `skill_id` and `public_base_url` for public skill archive downloads | implemented | `scripts/download_skill.py` `run_inside_env()` summary payload | covered |
| CAP-022 | Streaming `trading` path is dispatched through `agents_client.streaming.trading_agent_client_stream` | implemented | `run_streaming_trading()` | covered indirectly |
| CAP-023 | Streaming `deep_research` path is dispatched through `agents_client.streaming.dr_agent_client_stream` | implemented | `run_streaming_deep_research()` | gap |
| CAP-024 | Polling `trading` path is dispatched through `agents_client.db_polling.trading_agent_client_db` | implemented | `run_polling_trading()` | partially covered |
| CAP-025 | Polling `deep_research` path is dispatched through `agents_client.db_polling.dr_agent_client_db` | implemented | `run_polling_deep_research()` | covered |
| CAP-026 | Polling runs pass `<run-dir>/downloaded_reports` as report output directory | implemented | `run_inside_env()` polling branches | covered for trading, partial overall |
| CAP-027 | Streaming success attempts to discover latest file under `<run-dir>/downloaded_reports` | implemented | `find_downloaded_report()` + streaming branches | covered |
| CAP-028 | Polling success propagates `downloaded_file` into `summary.json` as `report_path` | implemented | polling branches in `run_inside_env()` | covered |
| CAP-029 | Parent directory is never auto-deleted by the wrapper | implemented | directory lifecycle in `main()`/`run_inside_env()` | gap |
| CAP-030 | Final user-visible result emits `[result]` lines for summary path, report path, log path, run dir, success | implemented | `announce_result()` calls in `run_inside_env()` | gap |
| CAP-031 | Polling client can resume an existing task via `task_id` | implemented | `recover_task()` and `run_stock_agent_client()` | gap |
| CAP-032 | Polling client downloads final reports after completed status | implemented | `print_report_download_result()` | partially covered |
| CAP-033 | Report downloading handles 404 and 410 responses without raising uncaught errors | implemented | `ReportDownloader.download_zip()` | gap |
| CAP-034 | Streaming probe output is kept under `<parent-dir>/probe/` | implemented | `scripts/stream_probe.py` helpers | partially covered |
| CAP-035 | Public skill archive downloads are written under `<run-dir>/downloaded_skills/` | implemented | `scripts/download_skill.py` `download_public_skill()` | covered |
| CAP-036 | Public skill archive downloads do not require access token resolution | implemented | `scripts/download_skill.py` `main()` + `run_inside_env()` | covered |
| CAP-037 | Public skill archive download URLs are built from `--public-base-url` plus `/skills/{repo_id}/download` | implemented | `scripts/download_skill.py` `public_skill_download_url()` | covered |

## Current Test Gap Priorities

The following capabilities are part of the baseline but are not yet well protected by tests and should be added next:

- `CAP-004` unsupported combination failure path
- `CAP-007` explicit proof that `--work-dir` remains the parent directory and a child run dir is created beneath it
- `CAP-014` runtime selection precedence across current interpreter, discovered interpreter, and conda
- `CAP-016` automatic install/update behavior for the local runtime
- `CAP-019` `run.log` tee behavior
- `CAP-029` parent directory preservation
- `CAP-030` final result output contract
- `CAP-031` task recovery branches for `completed`, `failed`, `not found`, and polling continuation
- `CAP-033` report downloader behavior for 404 and 410
- `CAP-035` and `CAP-037` error handling for public skill download failures

## Notes On Coverage Labels

- `covered` means the current tests assert the capability directly.
- `partially covered` means only one branch or one observable outcome is asserted today.
- `gap` means the capability is implemented now but a future refactor could break it without a direct failing test.
