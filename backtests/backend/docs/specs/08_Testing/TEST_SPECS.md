# Test Specifications

## API Tests

### Pool CRUD

- Create pool with valid name -> returns `SUCCESS` and new ID
- Create duplicate/invalid payload -> returns failure response
- Delete pool -> pool row removed and stock count side effects remain consistent

### Rule CRUD

- Create local agent rule with module path in `info`
- Create remote agent rule with URL in `info`
- Delete rule with attached pools, simulators, and trading rows -> all manual cleanup paths execute

### Simulator Config

- Update config row `id=1`
- Read config immediately -> values match persisted thresholds

## Rule Execution Tests

### Local Agent Import

- Valid module path resolves callable and runs
- Invalid module path returns structured error

### Remote Agent Execution

- Remote bool `true` -> `AgentTrading.trading_type = indicating`
- Remote bool `false` -> `AgentTrading.trading_type = not_indicating`
- Remote error -> no crash; stock run returns failure payload

### Trading Upsert

- Two concurrent writes for same `(rule_id, stock, date)` yield one row with final trade type

## Simulator Tests

### Signal To Trade Conversion

- indicate at `t`, buy allowed at `t+1`, profit exit before `max_holding_days`
- indicate at `t`, limit-up next day -> `fail_to_buy`
- bought position, limit-down day before max window -> `fail_to_sell`
- bought position, stop loss hit -> sell
- bought position, no threshold hit -> forced sell on last holding day

### Capital Logic

- insufficient cash or lot-size affordability -> `not_sufficient_to_buy`
- successful multi-stock replay updates cash, holdings, and assets consistently

### Metrics

- closing profitable and losing trades updates:
  - `cum_earn`
  - `avg_earn`
  - `earning_rate`
  - `earning_info`
  - `sharpe`
  - `max_drawback`

## Integration Tests

- Rule -> AgentTrading -> Simulator full chain
- Pool membership with suffix stock code joins correctly to base `stock.code`
- Bind-key DB session reads from configured alternate engines

## Manual Verification Cases

- `/health` reflects DB initialized state
- `/api/v1/get_simulator/simulator/{id}` returns readable HTML log stream after run
- MCP-backed local agents can run with required environment credentials present
