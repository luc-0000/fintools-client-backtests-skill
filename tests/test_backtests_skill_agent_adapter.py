import asyncio
from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


SKILL_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = SKILL_ROOT / "backtests" / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from db.models import AgentTrading, Base, Pool, PoolStock, Rule, RulePool
from end_points.config.db_init import DatabaseWrapper
from end_points.get_rule.operations.agent_streaming import stream_single_stock_execution
from end_points.get_rule.operations.agent_utils import run_agent_for_stock
from end_points.get_rule.operations.skill_agent_adapter import _resolve_token, stream_trading_agent_via_skill


class BacktestsSkillAgentAdapterTests(unittest.TestCase):
    def _build_db(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        session = scoped_session(sessionmaker(bind=engine))
        return DatabaseWrapper(session, engine=engine), session

    def test_run_agent_for_stock_uses_skill_adapter_result(self):
        db, session = self._build_db()
        try:
            rule = Rule(
                name="remote_105",
                type="remote_agent",
                info="https://example.com/api/v1/agents/105/a2a/",
                description="",
                agent_id="105",
            )
            session.add(rule)
            session.commit()

            with patch(
                "end_points.get_rule.operations.agent_utils.execute_agent_with_skill_adapter",
                new=AsyncMock(return_value={"result": {"action": "buy"}}),
            ):
                result = run_agent_for_stock(db, rule.id, "600519")

            self.assertTrue(result["success"])
            self.assertEqual(result["action"], "buy")
            trading = session.query(AgentTrading).filter(AgentTrading.rule_id == rule.id).one()
            self.assertEqual(trading.stock, "600519")
            self.assertEqual(trading.trading_type, "indicating")
        finally:
            session.remove()

    def test_stream_single_stock_execution_uses_skill_adapter(self):
        db, session = self._build_db()
        try:
            rule = Rule(
                name="remote_106",
                type="remote_agent",
                info="https://example.com/api/v1/agents/106/a2a/",
                description="",
                agent_id="106",
            )
            session.add(rule)
            session.commit()

            async def run_stream():
                items = []
                async for item in stream_single_stock_execution(db, rule.id, "000001"):
                    items.append(item)
                return items

            async def fake_stream(*_args, **_kwargs):
                yield {"type": "streaming_text", "message": "report line"}
                yield {"type": "result", "result": {"result": {"action": "hold"}}}

            with patch(
                "end_points.get_rule.operations.agent_streaming.stream_trading_agent_via_skill",
                new=fake_stream,
            ):
                logs = asyncio.run(run_stream())

            self.assertTrue(any("Using skill agent execution flow" in item.get("message", "") for item in logs))
            self.assertTrue(any(item.get("type") == "remote_result" for item in logs))
            trading = session.query(AgentTrading).filter(AgentTrading.rule_id == rule.id).one()
            self.assertEqual(trading.stock, "000001")
            self.assertEqual(trading.trading_type, "not_indicating")
        finally:
            session.remove()

    def test_stream_trading_agent_via_skill_yields_lines_incrementally(self):
        async def fake_run_streaming_trading(stock_code, agent_url, token):
            print("line one")
            await asyncio.sleep(0)
            print("line two")
            await asyncio.sleep(0)
            return {"result": {"action": "buy"}}

        async def collect():
            items = []
            async for item in stream_trading_agent_via_skill("600519", "https://example.com/a2a/"):
                items.append(item)
            return items

        with patch(
            "end_points.get_rule.operations.skill_agent_adapter._resolve_token",
            return_value="cached-real-token",
        ), patch(
            "end_points.get_rule.operations.skill_agent_adapter.run_streaming_trading",
            new=fake_run_streaming_trading,
        ):
            items = asyncio.run(collect())

        self.assertEqual(
            [item["message"] for item in items if item["type"] == "streaming_text"],
            ["line one", "line two"],
        )
        self.assertEqual(items[-1]["type"], "result")
        self.assertEqual(items[-1]["result"]["result"]["action"], "buy")

    def test_stream_single_stock_execution_streams_report_before_final_result(self):
        db, session = self._build_db()
        try:
            rule = Rule(
                name="remote_107",
                type="remote_agent",
                info="https://example.com/api/v1/agents/107/a2a/",
                description="",
                agent_id="107",
            )
            session.add(rule)
            session.commit()

            async def fake_stream(*_args, **_kwargs):
                yield {"type": "streaming_text", "message": "report line 1"}
                yield {"type": "streaming_text", "message": "report line 2"}
                yield {"type": "result", "result": {"result": {"action": "hold"}}}

            async def run_stream():
                items = []
                async for item in stream_single_stock_execution(db, rule.id, "000001"):
                    items.append(item)
                return items

            with patch(
                "end_points.get_rule.operations.agent_streaming.stream_trading_agent_via_skill",
                new=fake_stream,
            ):
                logs = asyncio.run(run_stream())

            event_types = [item["type"] for item in logs]
            self.assertIn("streaming_text", event_types)
            self.assertIn("remote_result", event_types)
            self.assertLess(event_types.index("streaming_text"), event_types.index("remote_result"))
            self.assertEqual(
                [item["message"] for item in logs if item["type"] == "streaming_text"],
                ["report line 1", "report line 2"],
            )
        finally:
            session.remove()

    def test_resolve_token_uses_skill_cache_instead_of_environment(self):
        with patch(
            "end_points.get_rule.operations.skill_agent_adapter.default_runs_parent_dir",
            return_value=Path("/tmp/fintools-runs"),
        ), patch(
            "end_points.get_rule.operations.skill_agent_adapter.load_cached_access_token",
            return_value="cached-real-token",
        ), patch(
            "end_points.get_rule.operations.skill_agent_adapter.token_file_path",
            return_value=Path("/tmp/fintools-runs/.fintools_access_token"),
        ), patch.dict("os.environ", {"FINTOOLS_ACCESS_TOKEN": "env-token"}, clear=False):
            self.assertEqual(_resolve_token(), "cached-real-token")

    def test_resolve_token_rejects_placeholder_cached_token(self):
        with patch(
            "end_points.get_rule.operations.skill_agent_adapter.default_runs_parent_dir",
            return_value=Path("/tmp/fintools-runs"),
        ), patch(
            "end_points.get_rule.operations.skill_agent_adapter.load_cached_access_token",
            return_value="your-fintools-access-token",
        ), patch(
            "end_points.get_rule.operations.skill_agent_adapter.token_file_path",
            return_value=Path("/tmp/fintools-runs/.fintools_access_token"),
        ):
            with self.assertRaisesRegex(RuntimeError, "Invalid FINTOOLS access token cache"):
                _resolve_token()
