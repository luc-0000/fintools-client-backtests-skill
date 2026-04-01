# Dual-Write Architecture and Idempotency in Backtests

## Context
When triggering the LLM trading agent via the `backtests` UI (`agent_streaming.py`), the system executes a classic "Dual-Write" (双写) operation designed as an idempotent safety net:

1. **SSOT Ledger Write**: The underlying driver (`run_agent_client.py`) natively catches the exact action (e.g. `{"action": "sell"}`) returned by the remote LLM, forces it to lowercase to prevent SQLite constraint failures (`action.lower()`), and explicitly INSERTs it into `.runtime/database/trading_agent_runs.db`. This is the single source of truth (SSOT) which ensures that even headless cron jobs will silently record their runs cleanly.
2. **Explicit UI View Write**: Back in the UI layer (`agent_streaming.py`), after the stream completes, the code calls `update_rule_trading(...)` using the exact `rule_id` that triggered the request.

## Why keep both?
Is it a duplication? Yes, technically. The `update_rule_trading` directly inserts/updates the `AgentTrading` view. Following that, we ALSO invoke `sync_trading_agent_into_backtests(...)`, which sweeps the SSOT ledger, matches `agent_url` to `rule_id`, and repeats the update to `AgentTrading`.

We intentionally preserved this dual-write "awkwardness" to eliminate a critical race-condition/mapping-miss:
- If a user configures two different UI rules (Rule A and Rule B) to point to the exact same Remote Agent URL.
- The user clicks Run on Rule B.
- The SSOT logs the URL execution.
- If we solely relied on the `sync` crawler, it would use `.first()` filtering by URL and improperly assign Rule B's data to Rule A!
- By retaining the explicit `update_rule_trading` locally, Rule B gets its guaranteed instant update.

Both mechanisms are strictly *idempotent* (uses MERGE internally on duplicate entries), meaning running both back-to-back incurs zero data duplication anomalies while covering all edge cases.

## Action Items
No new code changes to the database mapping scripts are needed. Regressions covering this architecture should focus on ensuring `run_agent_client.py` respects the dictionary type hints returned from `run_stock_agent_client`.
