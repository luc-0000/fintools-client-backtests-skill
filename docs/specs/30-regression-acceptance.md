# Regression Acceptance

This document defines the minimum acceptance bar for future changes. A refactor is not acceptable if it drops any baseline capability below.

## Capability Preservation Rules

Future changes must continue to satisfy all of the following:

1. The skill remains self-contained and runnable from its own copied directory when bundled files are present.
2. The wrapper continues to support both `trading` and `deep_research`.
3. The wrapper continues to support both `streaming` and `polling`.
4. The wrapper continues to support public skill archive downloads via `--skill-id`.
5. The wrapper continues to create a distinct run directory under a parent directory.
6. The wrapper continues to reuse cached tokens from the parent directory for agent execution.
7. The wrapper continues to prepare or reuse a skill-local Python runtime under `.runtime/env`.
8. The wrapper continues to write `summary.json` and `run.log` into the run directory.
9. The wrapper continues to surface the final `report_path` when one is available.
10. The wrapper continues to retain the current run directory and the parent directory after execution.
11. Unsupported or invalid inputs continue to fail explicitly rather than silently changing behavior.

## Required Manual Review Questions

Any change touching the wrapper or client dispatch code should be reviewed against these questions:

- Does the change alter the accepted CLI inputs or mode names?
- Does the change remove or rename one of the four supported agent/mode combinations?
- Does the change remove or alter public skill archive download behavior?
- Does the change change where tokens, logs, summaries, or reports are written?
- Does the change break copied-skill execution outside the original source repo?
- Does the change weaken local runtime reuse or automatic runtime update behavior?
- Does the change change whether run artifacts are retained after execution?
- Does the change stop exposing `report_path` or `run.log` to the caller?

If any answer is yes, the specs and tests must be updated in the same change.

## Required Automated Checks To Reach

The repository should maintain executable checks for these behaviors:

- CLI validation and mode normalization
- parent directory selection and run directory creation
- token cache precedence and persistence
- runtime selection precedence and local runtime reuse
- supported dispatch paths for all four combinations
- public skill archive download path and output directory
- `summary.json` field contract
- `run.log` tee behavior
- run directory retention
- report downloader error handling
- polling task recovery branches

## Current Highest-Risk Regression Areas

The current codebase is most exposed to accidental regression in these areas because tests are incomplete:

- runtime discovery and local runtime preparation
- directory lifecycle
- log tee behavior
- unsupported-combination failure behavior
- polling recovery branches
- report downloader failure handling

## Suggested Next Test Additions

Add tests in roughly this order:

1. invalid combination and invalid runtime selection branches
2. run directory retention and parent preservation
3. `run.log` tee behavior and final `[result]` lines
4. polling recovery matrix
5. `ReportDownloader.download_zip()` success, 404, and 410 handling
6. stream probe default path and log retention behavior

## Completion Standard For Future Refactors

A future refactor that touches this subsystem should not be considered complete until:

1. the baseline docs remain true,
2. any intentional contract changes are documented,
3. the affected regression checks pass,
4. newly introduced uncovered behavior is either tested or explicitly listed as a remaining gap.
