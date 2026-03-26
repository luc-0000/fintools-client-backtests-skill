import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


SKILL_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = SKILL_ROOT / "backtests" / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from db.models import Base, Rule, Simulator
from end_points.config.db_init import DatabaseWrapper
from end_points.get_simulator.operations.get_simulator_opts import addSimulator, deleteSimulator


class BacktestsSimulatorCreateTests(unittest.TestCase):
    def _build_db(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        session = scoped_session(sessionmaker(bind=engine))
        return DatabaseWrapper(session, engine=engine), session

    def test_add_simulator_creates_log_directory_and_record(self):
        db, session = self._build_db()
        try:
            rule = Rule(
                name="remote_105",
                type="remote_agent",
                info="https://example.com/api/v1/agents/105/a2a/",
                description="test",
                agent_id="105",
            )
            session.add(rule)
            session.commit()

            with tempfile.TemporaryDirectory(prefix="sim-log-dir-") as tmpdir:
                with patch(
                    "end_points.get_simulator.operations.get_simulator_utils._sim_log_dir",
                    return_value=tmpdir,
                ):
                    result = addSimulator(
                        db,
                        {"rule_id": rule.id, "start_date": date(2026, 1, 2), "init_money": 100000},
                    )

                    self.assertEqual(result["code"], "SUCCESS")
                    sim_id = result["data"]
                    sim = session.query(Simulator).filter(Simulator.id == sim_id).first()
                    self.assertIsNotNone(sim)
                    self.assertEqual(sim.rule_id, rule.id)
                    self.assertEqual(sim.start_date.date().isoformat(), "2026-01-02")

                    log_path = Path(tmpdir) / f"{sim_id}.html"
                    self.assertTrue(log_path.exists())
                    self.assertIn("Sim", log_path.read_text(encoding="utf-8"))

                    delete_result = deleteSimulator(db, sim_id)
                    self.assertEqual(delete_result["code"], "SUCCESS")
        finally:
            session.remove()


if __name__ == "__main__":
    unittest.main()
