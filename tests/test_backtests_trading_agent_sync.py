import sqlite3
from pathlib import Path
import sys
import tempfile
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


SKILL_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = SKILL_ROOT / "backtests" / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from db.models import AgentTrading, Base, Rule
from end_points.common.utils.trading_agent_sync import (
    ensure_trading_agent_source_schema,
    sync_trading_agent_into_backtests,
)
from end_points.config.db_init import DatabaseWrapper


class BacktestsTradingAgentSyncTests(unittest.TestCase):
    def _build_db(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        session = scoped_session(sessionmaker(bind=engine))
        return DatabaseWrapper(session, engine=engine), session

    def _write_source_db(self, path: Path):
        conn = sqlite3.connect(path)
        conn.execute(
            """
            CREATE TABLE trading_agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                stock_code TEXT NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                raw_result TEXT,
                mode TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO trading_agent_runs
            (run_id, stock_code, action, created_at, updated_at, raw_result, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("run-old", "600519", "buy", "2026-03-21 09:00:00", "2026-03-21 09:00:00", "buy", "streaming"),
                ("run-new", "600519", "sell", "2026-03-21 15:00:00", "2026-03-21 15:00:00", "sell", "polling"),
                ("run-hold", "000001", "hold", "2026-03-21 10:00:00", "2026-03-21 10:00:00", "hold", "polling"),
            ],
        )
        conn.commit()
        conn.close()

    def _write_summary(self, runs_dir: Path, run_name: str, trading_run_id: str, agent_url: str):
        run_dir = runs_dir / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "summary.json").write_text(
            (
                "{"
                f"\"agent_type\": \"trading\", "
                f"\"agent_url\": \"{agent_url}\", "
                f"\"trading_run_id\": \"{trading_run_id}\""
                "}"
            ),
            encoding="utf-8",
        )

    def test_sync_auto_creates_rule_and_appends_latest_daily_rows(self):
        with tempfile.TemporaryDirectory(prefix="backtests-sync-") as tmpdir:
            tmp_path = Path(tmpdir)
            source_db_path = tmp_path / "trading_agent_runs.db"
            runs_dir = tmp_path / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)

            self._write_source_db(source_db_path)
            self._write_summary(runs_dir, "run-1", "run-old", "https://example.com/api/v1/agents/105/a2a/")
            self._write_summary(runs_dir, "run-2", "run-new", "https://example.com/api/v1/agents/105/a2a/")
            self._write_summary(runs_dir, "run-3", "run-hold", "https://example.com/api/v1/agents/106/a2a/")

            db, session = self._build_db()
            try:
                result = sync_trading_agent_into_backtests(db, source_db_path=source_db_path, runs_dir=runs_dir)

                self.assertEqual(result["read_rows"], 2)
                self.assertEqual(result["inserted"], 2)
                self.assertEqual(result["updated"], 0)

                rules = session.query(Rule).order_by(Rule.agent_id.asc()).all()
                self.assertEqual([rule.agent_id for rule in rules], ["105", "106"])
                self.assertEqual([rule.type for rule in rules], ["remote_agent", "remote_agent"])
                self.assertEqual(
                    [rule.info for rule in rules],
                    [
                        "https://example.com/api/v1/agents/105/a2a/",
                        "https://example.com/api/v1/agents/106/a2a/",
                    ],
                )

                tradings = session.query(AgentTrading).order_by(AgentTrading.rule_id.asc(), AgentTrading.stock.asc()).all()
                self.assertEqual(len(tradings), 2)
                self.assertEqual(
                    {(trading.rule_id, trading.stock, trading.trading_type) for trading in tradings},
                    {
                        (rules[0].id, "600519", "not_indicating"),
                        (rules[1].id, "000001", "not_indicating"),
                    },
                )
            finally:
                session.remove()

    def test_source_schema_migration_adds_agent_columns_and_backfills(self):
        with tempfile.TemporaryDirectory(prefix="backtests-source-migration-") as tmpdir:
            tmp_path = Path(tmpdir)
            source_db_path = tmp_path / "trading_agent_runs.db"
            runs_dir = tmp_path / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)

            self._write_source_db(source_db_path)
            self._write_summary(runs_dir, "run-1", "run-old", "https://example.com/api/v1/agents/105/a2a/")

            result = ensure_trading_agent_source_schema(source_db_path, runs_dir=runs_dir)

            self.assertEqual(result["columns_added"], 2)
            conn = sqlite3.connect(source_db_path)
            try:
                columns = conn.execute("pragma table_info(trading_agent_runs)").fetchall()
                self.assertIn("agent_id", [column[1] for column in columns])
                self.assertIn("agent_name", [column[1] for column in columns])
                row = conn.execute(
                    "select run_id, agent_id, agent_name from trading_agent_runs where run_id = 'run-old'"
                ).fetchone()
                self.assertEqual(row, ("run-old", "105", "trading_agent_105"))
            finally:
                conn.close()

    def test_sync_reuses_existing_rule_by_agent_id(self):
        with tempfile.TemporaryDirectory(prefix="backtests-sync-existing-") as tmpdir:
            tmp_path = Path(tmpdir)
            source_db_path = tmp_path / "trading_agent_runs.db"
            runs_dir = tmp_path / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)

            self._write_source_db(source_db_path)
            self._write_summary(runs_dir, "run-1", "run-old", "https://example.com/api/v1/agents/105/a2a/")
            self._write_summary(runs_dir, "run-2", "run-new", "https://example.com/api/v1/agents/105/a2a/")
            self._write_summary(runs_dir, "run-3", "run-hold", "https://example.com/api/v1/agents/106/a2a/")

            db, session = self._build_db()
            try:
                session.add(
                    Rule(
                        name="manual_105",
                        type="remote_agent",
                        info="https://example.com/api/v1/agents/105/a2a/",
                        description="manual",
                        agent_id="105",
                    )
                )
                session.commit()

                result = sync_trading_agent_into_backtests(db, source_db_path=source_db_path, runs_dir=runs_dir)

                self.assertEqual(result["inserted"], 2)
                self.assertEqual(session.query(Rule).filter(Rule.agent_id == "105").count(), 1)
                self.assertEqual(session.query(Rule).count(), 2)
            finally:
                session.remove()

if __name__ == "__main__":
    unittest.main()
