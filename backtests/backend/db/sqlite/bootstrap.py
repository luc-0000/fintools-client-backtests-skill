#!/usr/bin/env python
# encoding=utf8
"""Bootstrap backtests database from the checked-in JSON backup."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from db.models import (
    AgentTrading,
    Base,
    Pool,
    PoolRuleEarn,
    PoolStock,
    Rule,
    RulePool,
    SimTrading,
    Simulator,
    SimulatorConfig,
    Stock,
    StockIndex,
    StockRuleEarn,
    StocksInPool,
    UpdatingStock,
)

SEED_TABLES = [
    ("stock", Stock),
    ("stock_index", StockIndex),
    ("updating_stock", UpdatingStock),
    ("stocks_in_pool", StocksInPool),
    ("pool", Pool),
    ("pool_stock", PoolStock),
    ("rule", Rule),
    ("rule_pool", RulePool),
    ("stock_rule_earn", StockRuleEarn),
    ("pool_rule_earn", PoolRuleEarn),
    ("simulator", Simulator),
    ("simulator_trading", SimTrading),
    ("simulator_config", SimulatorConfig),
    ("agent_trading", AgentTrading),
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_sqlite_path() -> Path:
    return _repo_root() / ".runtime" / "database" / "backtests.sqlite3"


def default_seed_dir() -> Path:
    return _repo_root() / "backtests" / "backend" / "backups" / "backup_20260207_201912" / "json_export"


def _parse_value(value: Any):
    if value in ("", None):
        return None
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return value
    return value


def _normalize_record(model, raw_record: dict[str, Any]) -> dict[str, Any]:
    normalized = {}
    for column in model.__table__.columns:
        if column.name not in raw_record:
            continue
        normalized[column.name] = _parse_value(raw_record[column.name])
    return normalized


def seed_database(engine, seed_dir: Path | None = None) -> bool:
    seed_dir = seed_dir or default_seed_dir()
    if not seed_dir.exists():
        return False

    inspector = inspect(engine)
    if "stock" not in inspector.get_table_names():
        return False

    with Session(engine) as session:
        if session.query(Stock).first() is not None:
            return False

        for table_name, model in SEED_TABLES:
            seed_file = seed_dir / f"{table_name}.json"
            if not seed_file.exists():
                continue

            with seed_file.open("r", encoding="utf-8") as f:
                records = json.load(f)

            if not records:
                continue

            session.bulk_insert_mappings(
                model,
                [_normalize_record(model, record) for record in records],
            )

        session.commit()
        return True


def ensure_schema_compatibility(engine) -> None:
    inspector = inspect(engine)
    if "rule" not in inspector.get_table_names():
        return

    rule_columns = {column["name"] for column in inspector.get_columns("rule")}
    with engine.begin() as connection:
        if "agent_id" not in rule_columns:
            connection.execute(text("ALTER TABLE rule ADD COLUMN agent_id VARCHAR(255)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_rule_agent_id ON rule(agent_id) WHERE agent_id IS NOT NULL"))


def ensure_database(engine, seed_dir: Path | None = None, bootstrap: bool = True) -> bool:
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility(engine)
    if not bootstrap:
        return False
    return seed_database(engine, seed_dir=seed_dir)


def ensure_sqlite_database(engine, seed_dir: Path | None = None) -> bool:
    return ensure_database(engine, seed_dir=seed_dir)
