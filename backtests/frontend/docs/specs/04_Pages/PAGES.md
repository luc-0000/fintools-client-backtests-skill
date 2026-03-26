# Pages

## Source Anchors

- Source: src/router/index.tsx
- Source: src/layouts/ProLayout.tsx
- Source: src/pages/Pools/index.tsx
- Source: src/pages/Pools/Detail.tsx
- Source: src/pages/Rules/index.tsx
- Source: src/pages/Rules/Detail.tsx
- Source: src/pages/Simulators/index.tsx
- Source: src/pages/Simulators/Detail.tsx
- Source: src/pages/AgentLog/index.tsx

## Route Map

- `/` -> redirect to `/rule`
- `/pool`
- `/pool/:id`
- `/rule`
- `/rule/:id`
- `/simulator`
- `/simulator/:id`
- `/agent-log/:ruleId`
- `/agent-log/:ruleId/:stockCode`

## Page Catalog

### Pools Index

- Title: `Pools`
- Layout:
  - page title
  - two tabs: `Pools`, `Stocks`
- Main content:
  - pool management list
  - stock management list

### Pool Detail

- Title:
  - route-provided pool name uppercased, else fallback `Pool {id}`
- Main content:
  - member stock table
  - add stock modal
  - delete confirmation modal

### Rules Index

- Title: `Rules`
- Header action:
  - `Agent Schema`
- Main content:
  - tabs: `Local Agents`, `Remote Agents`
- Auxiliary content:
  - informational schema modal

### Rule Detail

- Title combines rule ID and uppercase rule name
- Tabs:
  - `Pools`
  - `Stocks`
  - `Indicating`
- Content modes:
  - pool performance management
  - stock performance browsing
  - agent trading records

### Simulators Index

- Title: `Simulators`
- Header actions:
  - `Config`
  - `Trading Mechanism`
- Main content:
  - global config summary strip
  - tabs for local and remote agents

### Simulator Detail

- Title: `Simulator {id} - {ruleName}`
- Subtitle: `Rule ID: {ruleId}`
- Tabs:
  - `Logs`
  - `Earns`
  - `Trading`
- Special content:
  - backend HTML log output
  - ECharts performance graphs
  - trading event table with stock filter

### Agent Log

- Standalone monitor view outside the admin shell
- Two modes:
  - whole rule execution
  - single stock execution
- Main content:
  - progress tags
  - live log console
  - close button

## Shared Page Traits

- Admin-console information density
- Desktop-first layouts
- Low ornamentation
- Table-first information architecture
