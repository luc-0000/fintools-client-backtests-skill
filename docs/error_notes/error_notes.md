# Error Notes

## 2026-03-19

### 1. Agent-only boundary was written too narrowly

- Symptom: the skill started telling the host that it could only call agents and could not download skills.
- Root cause: wrapper/docs were mistakenly narrowed to an agent-only contract.
- Fix: restore dual capability at the repository level, then split entrypoints so agent execution stays in `scripts/run_agent_client.py` and skill downloads move to `scripts/download_skill.py`.

### 2. Agent and skill download responsibilities were mixed in one script

- Symptom: `run_agent_client.py` name and contract no longer matched the combined behavior.
- Root cause: skill download logic was added directly into the agent runner.
- Fix: move public skill archive download into `scripts/download_skill.py`, keep `run_agent_client.py` agent-only, and split tests/docs accordingly.

### 3. Layout validation was too broad for the download entrypoint

- Symptom: download flow reused a layout check that required `agents_client/`, even though downloading a public skill does not depend on it.
- Root cause: `validate_skill_layout()` represented agent runtime needs, not shared bundle needs.
- Fix: rename the agent-side check to `validate_agent_layout()` and add `validate_download_layout()` in `scripts/download_skill.py` that only requires `requirements.txt`.

### 4. Download filename parsing was incorrect

- Symptom: downloaded archive names could include raw `Content-Disposition` header fragments instead of a clean filename.
- Root cause: filename parsing used manual string splitting on `filename=` and did not properly handle standard header forms such as `filename*=` or more complex parameter layouts.
- Fix: parse `Content-Disposition` via `email.message.Message.get_filename()` and fall back to `skill-<id>.zip` only when no usable filename is provided.

### 5. Download path expectation vs. actual path

- Observation: a run was written under `/private/tmp/...`.
- Verified behavior: `scripts/download_skill.py` still defaults to `skill_root/.runtime/runs/` when `--work-dir` is not provided, because it uses `ensure_work_dir(args.work_dir)`.
- Interpretation: the `/private/tmp/...` path is consistent with an explicit or host-provided `--work-dir`, not with a broken default path implementation.

## 2026-03-23

### 1. Create Agent failed because backend allowed blank description at schema layer but not at DB layer

- Symptom: the Agents page `Create` action appeared to do nothing, and direct backend `POST /api/v1/get_rule/rule_list` returned `{"code":"FAILURE","id":"2209","errMsg":"2209"}`.
- Root cause: `RuleCreateArgs` normalized blank `description` to `None`, but `rule.description` in SQLite is `NOT NULL`, so insert failed with `sqlite3.IntegrityError: NOT NULL constraint failed: rule.description`.
- Fix: in `backtests/backend/end_points/get_rule/operations/get_rule_opts.py`, normalize missing `description` to `''` before insert. Frontend-side blank descriptions are still allowed.
- Verification:
  - direct backend create request to `127.0.0.1:8888` succeeded after the fix
  - proxied create request through `127.0.0.1:8000/api/v1/...` also succeeded

### 2. Create Simulator previously failed because initial log writing broke the whole creation flow

- Symptom: simulator creation returned failure even when payload itself was otherwise valid.
- Root cause:
  - simulator creation path wrote an initial HTML log file under `end_points/get_simulator/operations/sim_logs/`
  - log helpers did not ensure the directory existed
  - `write_sim_log()` / `read_sim_log()` closed `file` unconditionally in `finally`, which caused secondary errors when open failed
  - simulator creation treated this log-writing problem as a full creation failure
- Fix:
  - make simulator log helpers create the log directory automatically
  - guard `file.close()` behind `file is not None`
  - keep log errors from aborting simulator creation
- Verification:
  - direct backend create request to `127.0.0.1:8888/api/v1/get_simulator/simulator_list` succeeded
  - proxied create request through `127.0.0.1:8000/api/v1/get_simulator/simulator_list` also succeeded

### 3. Preferred triage order for frontend actions that "do nothing"

- Rule adopted: do not start with browser-side guessing.
- Correct order:
  - first test the backend endpoint directly with a minimal real payload
  - if backend fails, inspect backend traceback/logs and fix that first
  - only after backend passes, test the frontend-to-backend API path through the frontend proxy
  - only after both API layers pass, investigate browser click/submit behavior

### 4. Backtests remote-agent execution must not fall back to `.env` or environment token lookup

- Symptom: `backtests` remote agent execution still failed with `401 Unauthorized` when fetching `/.well-known/agent-card.json`, even after the execution path was switched to the shared skill adapter.
- Root cause:
  - `backtests` adapter reused `scripts/run_agent_client.py::resolve_access_token()`
  - that helper intentionally supports `CLI -> environment variable -> cached token file`
  - for `backtests`, this was too broad: it allowed accidental fallback to non-runtime sources and made placeholder values easy to leak into execution
  - the cached token file at `.runtime/runs/.fintools_access_token` contained the example value `your-fintools-access-token`
- Fix:
  - keep `agents_client/` unchanged
  - narrow token resolution only in `backtests` adapter
  - allow only:
    - explicit token passed into the adapter
    - or the skill-cached token file `.runtime/runs/.fintools_access_token`
  - reject placeholder/example token values early with a clear local error instead of letting the request reach the remote agent and fail as `401`
- Verification:
  - direct adapter call now raises `Invalid FINTOOLS access token cache ...`
  - real backend SSE execution now emits the same local error immediately and no longer reaches remote `agent-card.json` lookup with a placeholder token

### 5. Simulator could finish with no `simulator_trading` rows even when `agent_trading` had signals

- Symptom: running simulator such as `simulator 4` returned without useful trading output, and `simulator_trading` stayed empty even though the linked `remote_agent` already had signal rows in `agent_trading`.
- Root cause:
  - `trading_agent_runs -> agent_trading` sync used the runtime execution date directly
  - recent synced signal dates such as `2026-03-21` were Saturdays, not market dates
  - simulator matching logic required exact date matches against market data, so weekend signals were silently skipped
  - in addition, simulator trade records were being inserted with ISO datetime strings like `2026-03-23T00:00:00`, which SQLite `DateTime` columns reject
- Fix:
  - in `backtests/backend/end_points/get_simulator/operations/get_simulator_utils.py`, align non-trading signal dates to the next available market date before generating simulator trades
  - normalize string / pandas timestamp trade dates to real Python `datetime` objects before inserting `simulator_trading`
- Verification:
  - regression test `tests/test_backtests_simulator_run.py` now covers:
    - weekend signal date -> next trading day alignment
    - `run_sim_agent()` producing `simulator_trading` rows from a weekend signal
  - related suite passes:
    - `tests.test_backtests_simulator_run`
    - `tests.test_backtests_simulator_create`

### 6. Current network can still block real Tushare-backed simulator runs

- Observation: under the current network, real `runSimulator()` may still fail while fetching行情数据 from Tushare.
- Verified behavior:
  - one real `simulator 4` run hit `requests.exceptions.ReadTimeout` against `api.waditu.com`
  - after that timeout, `stockDataFrameFromTushare()` returned data without the expected OHLC columns, which then caused follow-on simulator failure
- Interpretation:
  - this is an upstream network/data-source issue in the current environment, not the local simulator date-alignment / SQLite insert bug above
  - the local simulator bug was fixed independently and covered by regression tests
