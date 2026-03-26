import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = SKILL_ROOT / "backtests" / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from end_points.get_rule.rule_schema import RuleCreateArgs


class BacktestsRuleCreateTests(unittest.TestCase):
    def test_rule_create_args_allows_blank_description(self):
        args = RuleCreateArgs(
            name="remote_agent_105",
            type="remote_agent",
            description="",
            info="https://example.com/api/v1/agents/105/a2a/",
            agent_id="105",
        )
        self.assertIsNone(args.description)


if __name__ == "__main__":
    unittest.main()
