#!/usr/bin/env python
# encoding=utf8

import logging
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from db.models import AgentTrading, Rule
from end_points.common.const.consts import RuleType, Trade

logger = logging.getLogger(__name__)

_DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
)


@dataclass(frozen=True)
class TradingAgentSignal:
    run_id: str
    stock_code: str
    trading_date: datetime
    trading_type: str
    created_at: datetime
    updated_at: datetime
    agent_id: str | None
    agent_url: str | None
    agent_name: str | None
    agent_description: str | None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _default_source_db_path() -> Path:
    return _repo_root() / ".runtime" / "database" / "trading_agent_runs.db"


def _default_runs_dir() -> Path:
    return _repo_root() / ".runtime" / "runs"


def _parse_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if value is None:
        return datetime.now()

    text = str(value).strip()
    if not text:
        return datetime.now()

    normalized = text.replace("T", " ")
    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        logger.warning("Could not parse datetime value: %s", value)
        return datetime.now()


def _normalize_stock_code(stock_code) -> str:
    value = str(stock_code or "").strip()
    return value.split(".")[0] if "." in value else value


def _map_trading_type(action) -> str:
    if str(action or "").strip().lower() == Trade.buy:
        return Trade.indicating
    return Trade.not_indicating


def _extract_agent_id(agent_url: str | None) -> str | None:
    if not agent_url:
        return None
    match = re.search(r"/agents/([^/]+)/a2a/?$", str(agent_url).strip())
    if match:
        return match.group(1)
    return None


def _default_agent_name(agent_id: str | None) -> str:
    return f"trading_agent_{agent_id}" if agent_id else "trading_agent_auto"


def _default_agent_description(agent_id: str | None) -> str:
    if agent_id:
        return f"Auto-created remote agent rule for trading agent {agent_id}"
    return "Auto-created remote agent rule from trading_agent runtime data"


def ensure_rule_agent_ids(db) -> int:
    updated = 0
    remote_rules = db.session.query(Rule).filter(Rule.type == RuleType.remote_agent).all()
    for rule in remote_rules:
        if rule.agent_id:
            continue
        agent_id = _extract_agent_id(rule.info)
        if not agent_id:
            continue
        existing = db.session.query(Rule).filter(Rule.agent_id == agent_id).first()
        if existing and existing.id != rule.id:
            logger.warning(
                "Cannot backfill agent_id=%s for rule_id=%s because it is already used by rule_id=%s",
                agent_id,
                rule.id,
                existing.id,
            )
            continue
        rule.agent_id = agent_id
        updated += 1

    if updated:
        db.session.commit()
        logger.info("Backfilled agent_id for %s remote_agent rules", updated)
    return updated


def _load_run_summary_index(runs_dir: Path) -> dict[str, dict]:
    if not runs_dir.exists():
        return {}

    summaries: dict[str, dict] = {}
    for summary_path in sorted(runs_dir.glob("*/summary.json")):
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        run_id = payload.get("trading_run_id")
        if not run_id:
            continue

        agent_url = payload.get("agent_url")
        agent_id = payload.get("agent_id") or _extract_agent_id(agent_url)
        summaries[str(run_id)] = {
            "agent_url": agent_url,
            "agent_id": str(agent_id) if agent_id is not None else None,
            "agent_name": payload.get("agent_name") or _default_agent_name(agent_id),
            "agent_description": payload.get("agent_description") or _default_agent_description(agent_id),
        }
    return summaries


def ensure_trading_agent_source_schema(source_db_path: Path, runs_dir: Path | None = None) -> dict[str, int]:
    source_db_path = Path(source_db_path)
    if runs_dir is not None:
        runs_dir = Path(runs_dir)
    if not source_db_path.exists():
        return {"columns_added": 0, "rows_backfilled": 0}

    summary_index = _load_run_summary_index(runs_dir or _default_runs_dir())
    conn = sqlite3.connect(str(source_db_path))
    try:
        conn.row_factory = sqlite3.Row
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(trading_agent_runs)").fetchall()}
        columns_added = 0
        if "agent_id" not in columns:
            conn.execute("ALTER TABLE trading_agent_runs ADD COLUMN agent_id TEXT")
            columns_added += 1
        if "agent_name" not in columns:
            conn.execute("ALTER TABLE trading_agent_runs ADD COLUMN agent_name TEXT")
            columns_added += 1

        rows_backfilled = 0
        rows = conn.execute("SELECT id, run_id, agent_id, agent_name FROM trading_agent_runs ORDER BY id ASC").fetchall()
        for row in rows:
            summary = summary_index.get(str(row["run_id"] or "").strip(), {})
            agent_id = row["agent_id"] or summary.get("agent_id")
            agent_name = row["agent_name"] or summary.get("agent_name") or _default_agent_name(agent_id)
            if not agent_id and not row["agent_id"] and not row["agent_name"]:
                continue
            if row["agent_id"] == agent_id and row["agent_name"] == agent_name:
                continue
            conn.execute(
                "UPDATE trading_agent_runs SET agent_id = ?, agent_name = ? WHERE id = ?",
                (agent_id, agent_name, row["id"]),
            )
            rows_backfilled += 1

        conn.commit()
        return {"columns_added": columns_added, "rows_backfilled": rows_backfilled}
    finally:
        conn.close()


def load_latest_daily_signals(source_db_path: Path, runs_dir: Path | None = None) -> list[TradingAgentSignal]:
    if not source_db_path.exists():
        logger.info("Trading agent source database not found, skip sync: %s", source_db_path)
        return []

    ensure_trading_agent_source_schema(source_db_path, runs_dir=runs_dir)

    query = """
        SELECT id, run_id, stock_code, action, created_at, updated_at, agent_id, agent_name
        FROM trading_agent_runs
        ORDER BY stock_code ASC, created_at ASC, updated_at ASC, id ASC
    """

    conn = None
    try:
        conn = sqlite3.connect(str(source_db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query).fetchall()
    except sqlite3.Error as exc:
        logger.warning("Failed to read trading agent database %s: %s", source_db_path, exc)
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    summary_index = _load_run_summary_index(runs_dir or _default_runs_dir())
    latest_by_day: dict[tuple[str, str, datetime.date], TradingAgentSignal] = {}
    for row in rows:
        created_at = _parse_datetime(row["created_at"])
        updated_at = _parse_datetime(row["updated_at"]) if row["updated_at"] else created_at
        stock_code = _normalize_stock_code(row["stock_code"])
        if not stock_code:
            continue
        run_id = str(row["run_id"] or "").strip()
        summary = summary_index.get(run_id, {})
        agent_url = summary.get("agent_url")
        agent_id = row["agent_id"] or summary.get("agent_id")

        signal = TradingAgentSignal(
            run_id=run_id,
            stock_code=stock_code,
            trading_date=datetime.combine(created_at.date(), datetime.min.time()),
            trading_type=_map_trading_type(row["action"]),
            created_at=created_at,
            updated_at=updated_at,
            agent_id=agent_id,
            agent_url=agent_url,
            agent_name=row["agent_name"] or summary.get("agent_name") or _default_agent_name(agent_id),
            agent_description=summary.get("agent_description") or _default_agent_description(agent_id),
        )
        agent_key = signal.agent_id or signal.agent_url or "unknown_agent"
        latest_by_day[(agent_key, signal.stock_code, signal.trading_date.date())] = signal

    return list(latest_by_day.values())


def _build_unique_rule_name(db, preferred_name: str, agent_id: str | None) -> str:
    candidate = (preferred_name or "").strip() or _default_agent_name(agent_id)
    existing = db.session.query(Rule).filter(Rule.name == candidate).first()
    if not existing:
        return candidate

    suffix = agent_id or "auto"
    candidate = f"{candidate}_{suffix}"
    existing = db.session.query(Rule).filter(Rule.name == candidate).first()
    if not existing:
        return candidate

    counter = 2
    while True:
        retry = f"{candidate}_{counter}"
        existing = db.session.query(Rule).filter(Rule.name == retry).first()
        if not existing:
            return retry
        counter += 1


def _find_or_create_rule_for_signal(db, signal: TradingAgentSignal) -> Rule:
    rule = None
    if signal.agent_id:
        rule = (
            db.session.query(Rule)
            .filter(Rule.type == RuleType.remote_agent)
            .filter(Rule.agent_id == signal.agent_id)
            .first()
        )

    if rule is None and signal.agent_url:
        rule = (
            db.session.query(Rule)
            .filter(Rule.type == RuleType.remote_agent)
            .filter(Rule.info == signal.agent_url)
            .first()
        )

    if rule is None:
        remote_rules = (
            db.session.query(Rule)
            .filter(Rule.type == RuleType.remote_agent)
            .order_by(Rule.id.asc())
            .all()
        )
        if not signal.agent_id and not signal.agent_url and remote_rules:
            if len(remote_rules) > 1:
                logger.warning(
                    "Signal %s has no agent metadata, falling back to first remote_agent rule_id=%s",
                    signal.run_id,
                    remote_rules[0].id,
                )
            return remote_rules[0]

    if rule is None:
        rule = Rule(
            name=_build_unique_rule_name(db, signal.agent_name, signal.agent_id),
            type=RuleType.remote_agent,
            info=signal.agent_url or "",
            description=(signal.agent_description or _default_agent_description(signal.agent_id))[:255],
            agent_id=signal.agent_id,
        )
        db.session.add(rule)
        db.session.flush()
        logger.info("Auto-created remote_agent rule id=%s agent_id=%s info=%s", rule.id, rule.agent_id, rule.info)
        return rule

    changed = False
    if signal.agent_id and not rule.agent_id:
        rule.agent_id = signal.agent_id
        changed = True
    if signal.agent_url and rule.info != signal.agent_url:
        rule.info = signal.agent_url
        changed = True
    if signal.agent_name and rule.name != signal.agent_name and not rule.name.startswith("trading_agent_"):
        pass
    if signal.agent_description and (not rule.description or rule.description == "test"):
        rule.description = signal.agent_description[:255]
        changed = True
    if changed:
        db.session.flush()
    return rule


def sync_trading_agent_into_backtests(
    db,
    source_db_path: Path | None = None,
    runs_dir: Path | None = None,
) -> dict:
    source_db_path = source_db_path or _default_source_db_path()
    runs_dir = runs_dir or _default_runs_dir()
    ensure_rule_agent_ids(db)
    signals = load_latest_daily_signals(source_db_path, runs_dir=runs_dir)
    if not signals:
        return {
            "source_db_path": str(source_db_path),
            "runs_dir": str(runs_dir),
            "target_rule_ids": [],
            "read_rows": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
        }

    inserted = 0
    updated = 0
    skipped = 0
    target_rule_ids: set[int] = set()
    for signal in signals:
        rule = _find_or_create_rule_for_signal(db, signal)
        target_rule_ids.add(rule.id)
        existing = (
            db.session.query(AgentTrading)
            .filter(AgentTrading.rule_id == rule.id)
            .filter(AgentTrading.stock == signal.stock_code)
            .filter(AgentTrading.trading_date == signal.trading_date)
            .first()
        )

        if existing:
            changed = False
            if existing.trading_type != signal.trading_type:
                existing.trading_type = signal.trading_type
                changed = True
            if existing.updated_at != signal.updated_at:
                existing.updated_at = signal.updated_at
                changed = True
            if changed:
                updated += 1
            else:
                skipped += 1
            continue

        db.session.add(
            AgentTrading(
                rule_id=rule.id,
                stock=signal.stock_code,
                trading_date=signal.trading_date,
                trading_type=signal.trading_type,
                trading_amount=0,
                created_at=signal.created_at,
                updated_at=signal.updated_at,
            )
        )
        inserted += 1

    db.session.commit()

    result = {
        "source_db_path": str(source_db_path),
        "runs_dir": str(runs_dir),
        "target_rule_ids": sorted(target_rule_ids),
        "read_rows": len(signals),
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
    }
    logger.info("Trading agent sync completed: %s", result)
    return result
