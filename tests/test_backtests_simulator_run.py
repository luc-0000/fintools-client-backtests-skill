from datetime import datetime
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


SKILL_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = SKILL_ROOT / "backtests" / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from db.models import AgentTrading, Base, Rule, SimTrading, Simulator, SimulatorConfig, Stock
from end_points.config.db_init import DatabaseWrapper
from end_points.common.const.consts import RuleType
from end_points.get_rule.operations.agent_utils import run_sim_agent
from end_points.get_simulator.operations.get_simulator_utils import align_indicator_dates_to_market_dates


class BacktestsSimulatorRunTests(unittest.TestCase):
    def _build_db(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        session = scoped_session(sessionmaker(bind=engine))
        return DatabaseWrapper(session, engine=engine), session

    def test_align_indicator_dates_to_market_dates_moves_weekend_signal_to_next_trading_day(self):
        stock_data = pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-03-20", "2026-03-23", "2026-03-24"]),
                "open": [10.0, 10.2, 10.4],
                "close": [10.1, 10.3, 10.5],
            }
        )

        aligned = align_indicator_dates_to_market_dates(stock_data, [pd.Timestamp("2026-03-21")])

        self.assertEqual(aligned, [pd.Timestamp("2026-03-23")])

    def test_run_sim_agent_writes_simulator_trading_for_weekend_signal(self):
        db, session = self._build_db()
        try:
            session.add(
                Rule(
                    id=3006,
                    name="remote_69",
                    type=RuleType.remote_agent,
                    info="https://example.com/api/v1/agents/69/a2a/",
                    description="",
                    agent_id="69",
                )
            )
            session.add(Stock(code="600519", name="Kweichow Moutai", se="sh"))
            session.add(
                Simulator(
                    id=4,
                    rule_id=3006,
                    start_date=datetime(2026, 1, 1),
                    init_money=100000,
                    current_money=100000,
                    current_shares="[]",
                    status="running",
                )
            )
            session.add(SimulatorConfig(id=1, profit_threshold=0, stop_loss=5, max_holding_days=5))
            session.add(
                AgentTrading(
                    rule_id=3006,
                    stock="600519",
                    trading_date=datetime(2026, 3, 21),
                    trading_type="indicating",
                )
            )
            session.commit()

            stock_data = pd.DataFrame(
                {
                    "date": pd.to_datetime(["2026-03-20", "2026-03-23", "2026-03-24", "2026-03-25"]),
                    "open": [10.0, 10.1, 10.2, 10.3],
                    "high": [10.1, 10.2, 10.3, 10.4],
                    "low": [9.9, 10.0, 10.1, 10.2],
                    "close": [10.0, 10.1, 10.2, 10.3],
                    "volume": [1, 1, 1, 1],
                    "turnover": [1, 1, 1, 1],
                    "turnover_rate": [1, 1, 1, 1],
                    "shake_rate": [1, 1, 1, 1],
                    "change_rate": [1, 1, 1, 1],
                    "change_amount": [1, 1, 1, 1],
                }
            )

            with patch(
                "end_points.get_simulator.operations.get_simulator_utils.stockDataFrameFromTushare",
                return_value=stock_data,
            ):
                run_sim_agent(db, 4)

            sim_trades = (
                session.query(SimTrading)
                .filter(SimTrading.sim_id == 4)
                .order_by(SimTrading.trading_date.asc(), SimTrading.id.asc())
                .all()
            )
            self.assertGreaterEqual(len(sim_trades), 2)
            self.assertEqual(sim_trades[0].trading_type, "indicating")
            self.assertEqual(sim_trades[0].trading_date.date().isoformat(), "2026-03-23")
            self.assertEqual(sim_trades[1].trading_type, "buy")
            self.assertEqual(sim_trades[1].trading_date.date().isoformat(), "2026-03-24")
        finally:
            session.remove()
