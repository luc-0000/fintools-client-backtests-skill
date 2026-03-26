# Fintools Client Skill Baseline

## Purpose

This document freezes the capability baseline that is already implemented in this repository as of 2026-03-19.

The goal is not to describe desired future behavior. The goal is to record current implemented behavior so later refactors do not silently remove completed capabilities.

## In Scope

This baseline covers the current bundled skill implementation centered on:

- `scripts/run_agent_client.py`
- `scripts/download_skill.py`
- `agents_client/streaming/`
- `agents_client/db_polling/`
- `agents_client/utils.py`
- `scripts/stream_probe.py`

## Protected Boundary

The `agents_client/` directory is a protected upstream boundary for this repository's first baseline.

- Do not modify files under `agents_client/` by default.
- Wrapper-level changes should be made in `scripts/`, `docs/`, and `tests/` whenever practical.
- If a future change intentionally modifies `agents_client/`, that decision should be explicit and documented as an upstream-behavior change rather than a wrapper-only change.

It also uses the following as supporting contract references, but code remains the source of truth:

- `SKILL.md`
- `references/runtime-contract.md`
- `tests/test_run_agent_client.py`
- `tests/test_download_skill.py`

## Baseline Rule

Any future change in this repository must preserve every capability listed in:

- `docs/specs/10-capability-matrix.md`
- `docs/specs/20-runtime-contract.md`
- `docs/specs/30-regression-acceptance.md`

If a change intentionally removes or alters a baseline capability, the change is incomplete until:

1. the affected spec is explicitly updated,
2. the removal or change is called out in review,
3. the regression acceptance criteria are updated,
4. the automated checks are updated to match the new intended baseline.

## Current Product Boundary

The repository currently implements a bundled Fintools client skill that:

- runs `trading` and `deep_research` agent clients,
- supports `streaming` and `polling` execution modes,
- downloads public skill archives through `/api/v1/public/skills/{repo_id}/download`,
- chooses or prepares a reusable Python runtime,
- creates a parent run directory and a unique run subdirectory,
- caches and reuses `FINTOOLS_ACCESS_TOKEN`,
- mirrors run output into `run.log`,
- writes a machine-readable `summary.json`,
- downloads reports into `downloaded_reports/` when available,
- downloads skill archives into `downloaded_skills/` when requested,
- remains runnable after being copied outside the original parent repository, as long as the bundled files remain present.

## Non-Goals For This Baseline

The following are intentionally not claimed as frozen behavior yet:

- exact CLI text formatting outside the documented status/result prefixes,
- exact report file names returned by remote services,
- remote server-side semantics outside the wrapper's local handling,
- full correctness of streaming/polling network flows against a live server,
- complete test coverage of all listed capabilities.

## Evidence Standard

A capability may be listed in the baseline when it is supported by at least one of:

- direct implementation in the current code,
- current runtime contract documented in-repo and aligned with the implementation,
- observable local output structure produced by the wrapper,
- existing automated tests.

Existing tests are supporting evidence only. They are not the sole authority for whether a capability is part of the baseline.

## Change Control Guidance

For future work in this repository:

- use these specs as the capability inventory before editing the wrapper,
- add or update tests when a baseline capability is currently under-tested,
- do not merge behavior changes that make the capability matrix less true,
- prefer changing implementation details behind the same external contract.
