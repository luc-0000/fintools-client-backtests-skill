# Agents And MCP Spec

## Source Anchors

- Source: end_points/get_rule/operations/agent_utils.py
- Source: local_agents/tauric_mcp/main.py
- Source: local_agents/quant_agent_vlm/main.py
- Source: local_agents/fingenius/main.py
- Source: mcp_servers/combo_mcp_servers/trading_agent_tools_mcp.py
- Source: mcp_servers/news_mcp_servers/news_tools_mcp.py
- Source: mcp_servers/tech_mcp_servers/tech_tools_mcp.py
- Source: remote_agents_a2a/trading_agent_server.py
- Source: remote_agents_a2a/trading_agent_client.py

## Agent Categories

### Local Agent Rules

Configured by `Rule.info = <python module path or module.function>`.

Observed local agent implementations:

- `local_agents.tauric_mcp.main.tauric_main`
- `local_agents.quant_agent_vlm.main.qa_main`
- `local_agents.fingenius.main.fingenius_main`

Contract:

- input: normalized stock code without exchange suffix
- output: truthy/falsey value interpreted as buy signal

### Remote Agent Rules

Configured by `Rule.type = remote_agent` and `Rule.info = <base_url>`.

Contract:

- client calls remote A2A service
- returned bool maps to `indicating` or `not_indicating`

## MCP Tool Bundles

### Trading Agent Tools

- exposes market and fundamentals retrieval
- internally chooses stock-market handling via `StockUtils`
- currently A-share-centric even when comments suggest broader coverage

### News Tools

- wraps Google News and related utilities
- supplies news items and formatted reports for agent reasoning

### Tech Tools

- exposes technical-analysis helpers and trendline computations
- used by `quant_agent_vlm`

## Tauric MCP Architecture

- loads trading and news MCP tools asynchronously
- builds `TradingAgentsGraph`
- propagates one stock/date through multi-agent reasoning
- includes config, model adapters, graph setup, memory, risk debate, and researcher/manager roles

## Quant Agent VLM Architecture

- fetches technical MCP tools
- collects recent historical bars
- runs graph-based analysis agents:
  - trend
  - pattern
  - indicator
  - final decision
- outputs boolean LONG/non-LONG decision

## FinGenius Architecture

- larger internal framework with:
  - research environment
  - battle/debate environment
  - MCP-backed agents
  - report generation
  - optimization traces under `apo/`
- many files appear framework-like rather than part of the stable backend API contract
- treat it as an embedded agent subsystem with unstable internal boundaries

## A2A Server Surface

- server publishes a generic agent card on `http://localhost:9999/`
- streaming is declared as supported
- executor implementation is `StreamingAgentExecutor`

## Replication Requirements

To reimplement the agent plane, preserve:

- local dynamic import by module path
- remote bool-returning call path
- MCP tool segregation by concern: trading/news/technical
- normalization into `AgentTrading` as the sole downstream contract used by simulators
