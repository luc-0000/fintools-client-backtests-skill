# HTTP API Spec

## Source Anchors

- Source: end_points/config/routes.py
- Source: end_points/get_pool/get_pool_routes.py
- Source: end_points/get_stock/get_stock_routes.py
- Source: end_points/get_rule/get_rule_routes.py
- Source: end_points/get_simulator/get_simulator_routes.py

## Base Behavior

- API prefix: `/api/v1`
- Standard success shape: usually `{ "code": "SUCCESS", "data": ... }`
- Error behavior:
  - route-level exceptions become `HTTPException(500, detail=...)`
  - uncaught app exceptions become `{code:"FAILURE", message:"Internal server error", detail:"..."}` with status 500

## Root Endpoints

### `GET /`

- Returns service identity, version, docs path, and running status

### `GET /health`

- Returns health plus coarse DB connectivity flag from `global_var['db']`

## Pool API

### `GET /api/v1/get_pool/pool_list`

- List all pools

### `POST /api/v1/get_pool/pool_list`

- Create pool
- Input: pool name payload

### `GET /api/v1/get_pool/pool/{pool_id}`

- Get pool by ID

### `PUT /api/v1/get_pool/pool/{pool_id}`

- Update pool

### `DELETE /api/v1/get_pool/pool/{pool_id}`

- Delete pool

## Stock API

### `GET /api/v1/get_stock/stock_list`

- Query params:
  - `page >= 1`
  - `page_size 1..1000`
  - optional `pool_id`, `stock_code`, `stock_name`

### `POST /api/v1/get_stock/stock_list`

- Add stock to pool

### `GET /api/v1/get_stock/stock/{stock_code}`

- Query params:
  - `page`
  - `page_size 1..50000`
  - `bind_key` default `cn_stocks`
- Returns historical/market detail for a stock

### `DELETE /api/v1/get_stock/stock/{stock_code}`

- Remove stock from pool

### `GET /api/v1/get_stock/stock/{stock_code}/rules`

- Returns rules related to a stock

## Rule API

### `GET /api/v1/get_rule/rule_list`

- Query params:
  - `bind_key`
  - optional `rule_id`, `pool_id`, `stock_code`, `stock_id`, `status`, `rule_type`
- Returns rule rows enriched with:
  - `pools`
  - aggregated `stocks` count

### `POST /api/v1/get_rule/rule_list`

- Create rule
- Defaults `type` to `agent`

### `GET /api/v1/get_rule/rule/{rule_id}`

- Reads via list/filter fallback, not a dedicated single-record query

### `PUT /api/v1/get_rule/rule/{rule_id}`

- Updates name/description/info and legacy info-subfields when info is JSON

### `DELETE /api/v1/get_rule/rule/{rule_id}`

- Manual cleanup flow, not DB-level cascade

### `GET /api/v1/get_rule/rule/{rule_id}/pools`

- If `rule_id` is non-numeric or `NaN`, code coerces to `0` meaning "all rules"

### `POST /api/v1/get_rule/rule/{rule_id}/pools`

- Bulk add pools to rule

### `DELETE /api/v1/get_rule/rule/{rule_id}/pools`

- Remove one pool from rule

### `GET /api/v1/get_rule/rule/{rule_id}/stocks`

- Returns stocks implied by rule-pool bindings

### `GET /api/v1/get_rule/rule/{rule_id}/params`

- Currently returns empty `items`

### `POST /api/v1/get_rule/rule/run/{rule_id}`

- Executes the agent rule over all stocks in its pools

### `GET /api/v1/get_rule/rule/{rule_id}/trading`

- Paged `AgentTrading` list

## Simulator API

### `GET /api/v1/get_simulator/simulator_list`

- Optional filters: `status`, `rule_type`
- Returns enriched performance metrics including sharpe/max_drawback when data exists

### `POST /api/v1/get_simulator/simulator_list`

- Create simulator

### `GET /api/v1/get_simulator/simulator/{sim_id}`

- Returns HTML log contents, not simulator row data

### `PUT /api/v1/get_simulator/simulator/{sim_id}/run`

- Replays simulator from `AgentTrading`

### `DELETE /api/v1/get_simulator/simulator/{sim_id}`

- Deletes DB row, trading rows, and HTML log file

### `GET /api/v1/get_simulator/simulator/{sim_id}/trading`

- Returns paginated `SimTrading` plus distinct stock list

### `GET /api/v1/get_simulator/simulator/{sim_id}/params`

- Returns expanded `earning_info` with normalized growth-rate series

### `GET /api/v1/get_simulator/config`

- Reads global simulator thresholds

### `PUT /api/v1/get_simulator/config`

- Updates global simulator thresholds

## Non-Registered Internal API Surfaces

- `get_earn` functions compute aggregate returns but are not exposed by current route registration
- `agent_streaming.py` exposes streaming helpers, but their route wiring is not visible in the inspected route file and should be treated as internal until confirmed
