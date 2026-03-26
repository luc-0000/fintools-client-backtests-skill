# Runtime Contract Baseline

This document records the current runtime contract implemented by the agent wrapper `scripts/run_agent_client.py`. It is narrower than a product spec and should be treated as a compatibility contract for future refactors.

## Bundled Layout Contract

The skill currently depends on these files existing inside the copied skill directory itself:

- `agents_client/`
- `requirements.txt`
- `scripts/run_agent_client.py`

The wrapper resolves paths relative to `SKILL_ROOT`, not relative to an external parent repository.

If `agents_client/` or `requirements.txt` is missing, startup must fail clearly before the run proceeds.

## Input Contract

The top-level agent wrapper currently requires:

- `--agent-type`
- `--mode`
- `--stock-code`
- `--agent-url`

Optional inputs currently supported:

- `--access-token`
- `--work-dir`
- `--task-id`

Internal-only wrapper flags:

- `--_in-env`
- `--_work-dir-auto-created`

Accepted mode values are currently:

- `streaming`
- `polling`

## Supported Execution Matrix

Current code supports all four combinations below:

| Agent Type | Mode | Local Dispatch |
|---|---|---|
| `trading` | `streaming` | `agents_client.streaming.trading_agent_client_stream.run_trading_agent` |
| `deep_research` | `streaming` | `agents_client.streaming.dr_agent_client_stream.run_dr_agent` |
| `trading` | `polling` | `agents_client.db_polling.trading_agent_client_db.main` |
| `deep_research` | `polling` | `agents_client.db_polling.dr_agent_client_db.main` |

## Parent And Run Directory Contract

When the caller provides `--work-dir`, that path is treated as the parent directory for runs.

When the caller does not provide `--work-dir`:

- use `skill_root/.runtime/runs`

Each execution creates a child run directory under the parent directory:

- name format: `fintools-agent-client-run-<agent_type>-<stock_code>-<mode>-<timestamp>`
- collision behavior: append `-002`, `-003`, and so on

The wrapper must not directly reuse the parent directory as the run directory.

## Token Contract

Token resolution order is currently used for agent execution only:

1. `--access-token`
2. `FINTOOLS_ACCESS_TOKEN` environment variable
3. `<parent-dir>/.fintools_access_token`

When a token is obtained from CLI or environment and a parent directory is known, the wrapper writes it back to:

- `<parent-dir>/.fintools_access_token`

The token cache file is intended for reuse across later runs under the same parent directory.

## Runtime Selection Contract

Current runtime selection behavior:

1. prefer the current interpreter when it is Python 3.10+
2. otherwise try `python3.13`, `python3.12`, `python3.11`, `python3.10`, `python3`
3. otherwise fall back to `conda`
4. otherwise fail

The persistent runtime lives under:

- `skill_root/.runtime/env/`

Current runtime metadata lives under:

- `skill_root/.runtime/install-state.json`

When the local runtime is missing, the wrapper creates it automatically before running the child process.

When `requirements.txt` changed since the last successful installation, the wrapper updates the same local runtime automatically before running the child process.

Child execution currently receives:

- `FINTOOLS_ACCESS_TOKEN`
- `FINTOOLS_RUNTIME_TYPE`
- `FINTOOLS_RUNTIME_DETAIL`
- `FINTOOLS_RUNTIME_ENV_DIR`
- `PYTHONUNBUFFERED=1`

## Output Contract

The run directory currently contains or may contain:

- `summary.json`
- `run.log`
- `downloaded_reports/`

`downloaded_reports/` is created before the run logic dispatches.

For polling runs, `<run-dir>/downloaded_reports` is passed to the polling client as `report_output_dir`.

For streaming runs, the wrapper currently looks for the most recently modified file under `<run-dir>/downloaded_reports` after a successful streaming call.

## Summary File Contract

`summary.json` currently includes at least these fields:

- `agent_type`
- `mode`
- `stock_code`
- `agent_url`
- `runtime_type`
- `runtime_detail`
- `runtime_env_dir`
- `work_dir`
- `parent_dir_source`
- `run_dir`
- `log_path`
- `report_path`
- `success`
- `error`

`report_path` may be `null` when no report was downloaded or discovered.

## Logging Contract

The wrapper currently mirrors stdout and stderr into `<run-dir>/run.log` while still printing to the active terminal.

The wrapper also emits status/result markers intended for host integration:

- status prefix: `[status] `
- result prefix: `[result] `

## Directory Retention Contract

The parent directory is not automatically removed by the wrapper.

The current run directory is retained after execution so `summary.json`, `run.log`, and downloaded reports remain inspectable.
