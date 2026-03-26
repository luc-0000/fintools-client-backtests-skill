# Operations And Maintenance

## Source Anchors

- Source: scripts/create_tables.py
- Source: scripts/export_database.py
- Source: scripts/import_data.py
- Source: scripts/init_db.sh
- Source: data_processing/update_stocks/download_mydata.py
- Source: data_processing/update_stocks/update_all_stocks_list.py
- Source: data_processing/update_stocks/remove_staled_stocks.py

## Schema Bootstrap

- `scripts/create_tables.py` creates SQLAlchemy-declared tables
- `scripts/init_db.sh` is the shell bootstrap entry for DB initialization

## Data Import/Export

- `scripts/export_database.py`
  - reads DB config
  - exports SQL dump and per-table JSON
- `scripts/import_data.py`
  - imports data back into the runtime schema

These scripts define the repo's intended backup/restore path, separate from the checked-in `backups/` directory.

## Market Data Update Flows

### Update Stock Universe

- `update_all_stocks_list.py`
- refreshes the stock master list

### Download Historical Data

- `download_mydata.py`
- pulls data for stocks and indices
- creates missing stock tables dynamically via helper utilities

### Remove Stale Stocks

- `remove_staled_stocks.py`
- removes outdated stock membership/data artifacts

## Operational Outputs

The code writes runtime artifacts to:

- simulator HTML logs
- local agent reports
- optimization traces
- exported DB snapshots

Repository hygiene requirement for future tasks:

- keep these as runtime outputs, not canonical source inputs
- do not treat generated traces as permanent examples unless intentionally documented
