# Patterns

## Source Anchors

- Source: src/pages/Pools/index.tsx
- Source: src/pages/Rules/index.tsx
- Source: src/pages/Rules/Detail.tsx
- Source: src/pages/Simulators/index.tsx
- Source: src/pages/Simulators/Detail.tsx
- Source: src/pages/AgentLog/index.tsx

## Navigation Pattern

- Top-level navigation is section-based through ProLayout.
- Section internals often use `Tabs`.
- Detail exploration uses route transitions from table cells.
- Long-running execution logs open in a separate dedicated page.

## Page Skeleton Pattern

- Default shell:
  - outer page padding `20px`
  - title row
  - optional right-side action
  - tabs or one main grid

## Search / Filter Pattern

- Filtering is light and tactical:
  - searchable selects
  - pool selectors
  - stock selectors embedded in table search forms
- There is no broad faceted filter panel or persistent filter bar pattern.

## Table / Pagination Pattern

- `ProTable` is the dominant presentation primitive.
- Common page sizes:
  - `50` for management lists
  - `100` for simulator trading details
- Sorting is applied on dates and numeric performance columns.

## CRUD Pattern

- Create:
  - toolbar primary button
  - modal form
- Edit:
  - row action opens modal with current values
- Delete:
  - short confirmation modal with plain warning text

## Execution Pattern

- Rule execution:
  - run action opens log route in a new window
  - progress is also visible inline in rule list
- Simulator execution:
  - run action remains inside row and uses a small spinner

## State Pattern

- Loading:
  - section-wide `Spin`
  - inline `Loading...` text when needed
- Empty:
  - plain text fallback, not rich empty states
- Error:
  - Antd `message.error`
  - no custom exception screens

## Content Pattern

- Copy is short, direct, and ops-oriented.
- Labels are mostly English even though locale is Chinese.
- UI emphasizes admin task completion rather than narrative guidance.
