# Data Model Spec

## Source Anchors

- Source: db/models.py
- Source: end_points/common/const/consts.py

## Core Tables

### `stock`

- PK: `code`
- Purpose: canonical stock master
- Fields: `name`, `se`, `type`, `index_code`, timestamps
- Used by: stock listing, rule stock joins, simulator display labels

### `pool`

- PK: `id`
- Purpose: named stock collections
- Fields: `name`, `stocks`, `latest_date`, timestamps
- Invariant: `stocks` is denormalized and should be kept in sync with `pool_stock`

### `pool_stock`

- PK: `id`
- Purpose: membership relation between stocks and pools
- Fields: `stock_code`, `pool_id`, timestamps
- Note: `stock_code` may include exchange suffix; downstream logic often strips it before joining to `stock.code`

### `rule`

- PK: `id`
- Purpose: executable trading rule definition
- Fields: `name`, `type`, `info`, `description`, timestamps
- Important overload:
  - `type` classifies execution mode
  - `info` may hold JSON, a local module path, or a remote agent URL

### `rule_pool`

- PK: `id`
- Purpose: attaches rules to pools
- Fields: `rule_id`, `pool_id`, timestamps

### `stock_rule_earn`

- PK: `id`
- Purpose: per-stock, per-rule precomputed earning/signal summary
- Fields: `stock_code`, `rule_id`, `earn`, `avg_earn`, `earning_rate`, `trading_times`, `status`, `indicating_date`, `updated_at`

### `pool_rule_earn`

- PK: `id`
- Purpose: aggregated performance per `(pool_id, rule_id)`
- Fields: `pool_id`, `rule_id`, earning metrics, `updated_at`

### `simulator`

- PK: `id`
- Purpose: replay state for one rule on one stock or one stock universe
- Fields:
  - identity: `stock_code`, `rule_id`, `start_date`, `status`
  - capital: `init_money`, `current_money`, `current_shares`
  - metrics: `cum_earn`, `avg_earn`, `earning_rate`, `trading_times`, `indicating_date`
  - serialized analytics: `earning_info`
  - timestamps

### `simulator_trading`

- PK: `id`
- Purpose: event log for simulator replay
- Fields: `sim_id`, `stock`, `trading_date`, `trading_type`, `trading_amount`, timestamps

### `simulator_config`

- PK: `id`
- Purpose: global sell-condition config
- Fields:
  - `profit_threshold`
  - `stop_loss`
  - `max_holding_days`
- Implicit singleton behavior: code queries row `id == 1`

### `agent_trading`

- PK: `id`
- Unique key: `(rule_id, stock, trading_date)`
- Purpose: normalized output of agent decisions
- Fields: `rule_id`, `stock`, `trading_date`, `trading_type`, `trading_amount`, timestamps
- Role in architecture: handoff contract between agent execution and simulator replay

## Secondary Tables Still Present

- `stock_index`
- `updating_stock`
- `stocks_in_pool`

These support market-data update flows and are not the primary API contract, but they remain part of runtime behavior.

## Data Invariants

- `AgentTrading.stock` is stored without exchange suffix when possible.
- Deleting a rule cascades manually in code:
  - detach `rule_pool`
  - delete `agent_trading`
  - clear earning summaries
  - delete associated simulators
- Deleting a simulator also deletes:
  - `simulator_trading`
  - its HTML log file

## Serialized Fields

- `Simulator.current_shares`: JSON string
- `Simulator.earning_info`: JSON string with keys such as `earns`, `sell_dates`, `bought_dates`, `earn_rates_after`, `cum_earns_after`, `avg_earns_after`, `assets`
- `Rule.info`: structurally polymorphic string payload

Any strict-schema reimplementation should normalize these into typed objects while keeping wire compatibility at the boundaries.
