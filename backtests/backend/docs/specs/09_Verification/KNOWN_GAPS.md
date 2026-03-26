# Known Gaps And Ambiguities

## 1. `Rule.info` Is Polymorphic

The same DB column carries incompatible payload shapes:

- JSON for some rule types
- Python import path for local agents
- base URL for remote agents

Any reimplementation should either preserve this overload for compatibility or migrate with explicit versioned schema handling.

## 2. Config Surface Is Not Fully Centralized

The main server config is explicit, but agent/provider credentials are distributed across subsystems and `.env` usage.

## 3. Internal Agent Framework Boundaries Are Uneven

`local_agents/fingenius` contains framework code, tools, prompts, reports, optimization traces, and utilities in one subtree. Stable runtime contracts are less clear than in the HTTP layer.

## 4. File-Backed Simulator Logs

Simulator reads/writes HTML log files from the code tree. This is observable behavior but a fragile persistence mechanism.

## 5. Legacy Migration Residue

The codebase contains comments and compatibility shims from earlier Flask/model-based behavior. Some comments describe removed subsystems, which means source comments are not always authoritative.

## 6. Security/Operational Debt Visible In Source

- plaintext credentials in `service.conf`
- `exec()`-based config loading
- globally shared mutable runtime state

These do not block replication, but they should be treated as explicit design debt rather than accidental omissions.
