# Environment And Configuration

## Source Anchors

- Source: service.conf
- Source: ../../config.json
- Source: end_points/init_global.py
- Source: end_points/config/db_init.py
- Source: local_agents/tauric_mcp/default_config.py

## Boot Config Contract

`manage.py` reads `CFG_PATH` from the process environment. If unset, it loads `./service.conf`.

`init_global()` then merges `service.conf` with the root-level database config file referenced by `DATABASE_CONFIG` (default `../../config.json`).

`load_config_file()` treats `.conf` files as Python source and executes them with `exec()`. For `.json` files it uses JSON parsing.

## Required Config Keys

| Key | Purpose | Default Behavior |
| --- | --- | --- |
| `VERSION_FILE` | Build/version text file path | falls back to `./version` in init logic |
| `LISTEN` | server bind host | `0.0.0.0` |
| `PORT` | server bind port | `8888` |
| `DEBUG` | uvicorn reload toggle | `False` unless config enables it |
| `DATABASE_CONFIG` | path to root DB config file | `../../config.json` |
| `database.backend` | selected backend | `sqlite` |
| `database.common.auto_bootstrap` | whether to seed/init on startup | `true` |
| `database.common.seed_dir` | seed json directory | checked-in backup json path |
| `database.sqlite.path` | SQLite database path | `.runtime/database/backtests.sqlite3` |
| `database.mysql.host` | MySQL host | `localhost` |
| `database.mysql.port` | MySQL port | `3306` |
| `database.mysql.user` | MySQL username | `root` |
| `database.mysql.password` | MySQL password | empty string |
| `database.mysql.database` | MySQL primary schema | `fintools_backtest` |
| `database.mysql.binds` | bind-key to schema map | fixed object in `config.json` |

## Database Binding Model

Bind keys from `end_points/common/const/consts.py`:

- `cn_stocks`
- `cn_stocks_m`
- `cn_stocks_in_pool`

Replication requirement:

- when `database.backend=sqlite`, one SQLite engine for the repo-local database file and all bind keys map to it
- when `database.backend=mysql`, one primary MySQL engine plus bind-key engines built from `database.mysql.binds`

## Global Runtime State

`global_var` stores:

- `version`
- `db`
- `db_engine`
- `db_session`
- `db_engines`
- `db_binds`

This is shared mutable process state. Reimplementations should either preserve it for compatibility or replace it with explicit dependency injection across all routes and services.

## Agent-Side Environment

Agent modules call `load_dotenv()`. The codebase implies environment-based credentials for:

- LLM providers
- Tushare and other market/news APIs
- optional MCP and storage backends

Exact env var names are not centralized in one file and must be recovered per adapter/module during a deeper hardening pass.

## Risks To Preserve Or Eliminate Explicitly

- database backend switching is config-driven from the root `config.json`.
- config file execution via `exec()` is code execution by design.
- several agent systems rely on side-loaded `.env` rather than typed config.
