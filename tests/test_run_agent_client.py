from datetime import datetime
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "run_agent_client.py"
)
STREAM_PROBE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "stream_probe.py"
)
DB_CLIENT_PATH = (
    Path(__file__).resolve().parents[1] / "agents_client" / "db_polling" / "db_client.py"
)
UTILS_PATH = (
    Path(__file__).resolve().parents[1] / "agents_client" / "utils.py"
)


def build_dependency_stubs():
    httpx_module = types.ModuleType("httpx")
    httpx_module.Timeout = lambda *args, **kwargs: ("timeout", args, kwargs)
    httpx_module.AsyncClient = object

    class HTTPStatusError(Exception):
        def __init__(self, *args, response=None, **kwargs):
            super().__init__(*args)
            self.response = response

    httpx_module.HTTPStatusError = HTTPStatusError

    dotenv_module = types.ModuleType("dotenv")
    dotenv_module.load_dotenv = lambda *_args, **_kwargs: None

    a2a_module = types.ModuleType("a2a")
    a2a_client_module = types.ModuleType("a2a.client")
    a2a_types_module = types.ModuleType("a2a.types")

    class DummyA2ACardResolver:
        def __init__(self, *args, **kwargs):
            pass

        async def get_agent_card(self):
            return {}

    class DummyA2AClient:
        def __init__(self, *args, **kwargs):
            pass

        async def send_message_streaming(self, _req):
            if False:
                yield None

    class DummyMessageSendParams:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummySendStreamingMessageRequest:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    a2a_client_module.A2ACardResolver = DummyA2ACardResolver
    a2a_client_module.A2AClient = DummyA2AClient
    a2a_types_module.MessageSendParams = DummyMessageSendParams
    a2a_types_module.SendStreamingMessageRequest = DummySendStreamingMessageRequest

    return {
        "httpx": httpx_module,
        "dotenv": dotenv_module,
        "a2a": a2a_module,
        "a2a.client": a2a_client_module,
        "a2a.types": a2a_types_module,
    }


def load_module():
    spec = importlib.util.spec_from_file_location("run_agent_client", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with mock.patch.dict(sys.modules, build_dependency_stubs(), clear=False):
        spec.loader.exec_module(module)
    return module


def load_stream_probe_module():
    spec = importlib.util.spec_from_file_location("stream_probe", STREAM_PROBE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_db_client_module():
    skill_root = DB_CLIENT_PATH.parents[2]
    if str(skill_root) not in sys.path:
        sys.path.insert(0, str(skill_root))
    spec = importlib.util.spec_from_file_location("db_client", DB_CLIENT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with mock.patch.dict(sys.modules, build_dependency_stubs(), clear=False):
        spec.loader.exec_module(module)
    return module


def load_utils_module():
    skill_root = UTILS_PATH.parents[1]
    if str(skill_root) not in sys.path:
        sys.path.insert(0, str(skill_root))
    spec = importlib.util.spec_from_file_location("agents_client.utils", UTILS_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with mock.patch.dict(sys.modules, build_dependency_stubs(), clear=False):
        spec.loader.exec_module(module)
    return module


class RunAgentClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.stream_probe = load_stream_probe_module()
        cls.db_client = load_db_client_module()
        cls.utils = load_utils_module()

    def test_normalize_mode_accepts_streaming(self):
        self.assertEqual(self.module.normalize_mode("streaming"), "streaming")

    def test_normalize_mode_accepts_polling(self):
        self.assertEqual(self.module.normalize_mode("polling"), "polling")

    def test_normalize_mode_rejects_old_internal_name(self):
        with self.assertRaises(SystemExit):
            self.module.normalize_mode("recoverable_polling")

    def test_skill_root_contains_bundled_runtime_files(self):
        self.assertTrue(self.module.AGENTS_CLIENT_DIR.is_dir())
        self.assertTrue(self.module.REQUIREMENTS_FILE.is_file())

    def test_validate_agent_layout_fails_cleanly_when_bundled_files_missing(self):
        with mock.patch.object(self.module, "AGENTS_CLIENT_DIR", Path("/tmp/missing-agents-client")), \
             mock.patch.object(self.module, "REQUIREMENTS_FILE", Path("/tmp/missing-requirements.txt")):
            with self.assertRaises(SystemExit):
                self.module.validate_agent_layout()

    def test_standalone_skill_copy_imports_without_parent_repo(self):
        skill_root = MODULE_PATH.parents[1]
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-standalone-") as tmpdir:
            copied_root = Path(tmpdir) / "fintools-agent-client"
            shutil.copytree(skill_root, copied_root)
            copied_module_path = copied_root / "scripts" / "run_agent_client.py"
            spec = importlib.util.spec_from_file_location("standalone_run_agent_client", copied_module_path)
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)

            self.assertEqual(module.SKILL_ROOT.resolve(), copied_root.resolve())
            self.assertTrue(module.AGENTS_CLIENT_DIR.is_dir())
            self.assertTrue(module.REQUIREMENTS_FILE.is_file())

    def test_token_file_path(self):
        self.assertEqual(
            self.module.token_file_path("/tmp/example-parent"),
            Path("/tmp/example-parent/.fintools_access_token"),
        )

    def test_save_and_load_cached_access_token(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-token-") as tmpdir:
            self.module.save_access_token(tmpdir, "secret-token")
            self.assertEqual(self.module.load_cached_access_token(tmpdir), "secret-token")

    def test_resolve_access_token_uses_cache(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-token-") as tmpdir:
            self.module.save_access_token(tmpdir, "cached-token")
            args = type("Args", (), {"access_token": None})()
            with mock.patch.dict(self.module.os.environ, {}, clear=True):
                self.assertEqual(self.module.resolve_access_token(args, tmpdir), "cached-token")

    def test_ensure_required_rejects_missing_agent_url(self):
        args = type(
            "Args",
            (),
            {
                "agent_type": "trading",
                "mode": "streaming",
                "stock_code": "600519",
                "agent_url": None,
            },
        )()
        with self.assertRaises(SystemExit):
            self.module.ensure_required(args)

    def test_auto_work_dir_prefix_contains_skill_name(self):
        work_dir, auto_created = self.module.ensure_work_dir(None)
        self.assertTrue(auto_created)
        self.assertEqual(Path(work_dir).name, "runs")
        self.assertEqual(Path(work_dir).parent, self.module.SKILL_ROOT / ".runtime")

    def test_default_runs_parent_dir_is_under_skill_runtime_directory(self):
        runs_dir = self.module.default_runs_parent_dir()
        self.assertEqual(runs_dir, self.module.SKILL_ROOT / ".runtime" / "runs")

    def test_stream_probe_uses_same_default_parent_dir(self):
        parent_dir = self.stream_probe.ensure_parent_dir(None)
        self.assertEqual(parent_dir, self.stream_probe.SKILL_ROOT / ".runtime" / "runs")

    def test_stream_probe_keeps_output_under_probe_directory(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-parent-") as tmpdir:
            probe_dir = self.stream_probe.ensure_probe_dir(tmpdir)
            self.assertEqual(probe_dir, Path(tmpdir) / "probe")

    def test_safe_name_fragment(self):
        self.assertEqual(self.module.safe_name_fragment("Deep Research"), "deepresearch")
        self.assertEqual(self.module.safe_name_fragment("600519"), "600519")
        self.assertEqual(self.module.safe_name_fragment("streaming"), "streaming")

    def test_create_run_dir_under_parent(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-parent-") as tmpdir:
            run_dir = self.module.create_run_dir(tmpdir, "trading", "600519", "streaming")
            self.assertEqual(Path(run_dir).parent, Path(tmpdir))
            self.assertRegex(
                Path(run_dir).name,
                r"^fintools-agent-client-run-trading-600519-streaming-\d{8}-\d{6}$",
            )

    def test_create_run_dir_adds_sequence_when_timestamp_collides(self):
        fixed_now = datetime(2026, 3, 12, 12, 0, 0)
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-parent-") as tmpdir, \
             mock.patch.object(self.module, "datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            mock_datetime.strftime = datetime.strftime
            first_run = self.module.create_run_dir(tmpdir, "trading", "600519", "streaming")
            second_run = self.module.create_run_dir(tmpdir, "trading", "600519", "streaming")

            self.assertEqual(Path(first_run).name, "fintools-agent-client-run-trading-600519-streaming-20260312-120000")
            self.assertEqual(Path(second_run).name, "fintools-agent-client-run-trading-600519-streaming-20260312-120000-002")

    def test_local_runtime_dir_is_under_skill_runtime_directory(self):
        runtime_dir = self.module.local_runtime_dir()
        self.assertEqual(runtime_dir, self.module.SKILL_ROOT / ".runtime" / "env")

    def test_runtime_python_path_points_into_local_env(self):
        python_path = self.module.runtime_python_path("/tmp/example-env")
        self.assertEqual(python_path, Path("/tmp/example-env/bin/python"))

    def test_write_and_load_install_state_round_trip(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-runtime-") as tmpdir:
            state_path = Path(tmpdir) / "install-state.json"
            payload = {"requirements_hash": "abc123", "python_version": "3.11.9"}
            with mock.patch.object(self.module, "install_state_path", return_value=state_path):
                self.module.write_install_state(payload)
                loaded = self.module.load_install_state()

        self.assertEqual(loaded, payload)

    def test_log_file_path(self):
        self.assertEqual(
            self.module.log_file_path("/tmp/example-run"),
            Path("/tmp/example-run/run.log"),
        )

    def test_announce_helpers_use_expected_prefixes(self):
        with mock.patch("builtins.print") as mock_print:
            self.module.announce_status("正在安装依赖")
            self.module.announce_result("Report path: /tmp/example.zip")

        self.assertEqual(mock_print.call_args_list[0].args[0], "[status] 正在安装依赖")
        self.assertEqual(mock_print.call_args_list[1].args[0], "[result] Report path: /tmp/example.zip")

    def test_build_reexec_args_preserves_polling_mode(self):
        args = type(
            "Args",
            (),
            {
                "agent_type": "trading",
                "mode": "polling",
                "stock_code": "600519",
                "agent_url": "http://example.com/a2a/",
                "access_token": None,
                "task_id": None,
            },
        )()
        argv = self.module.build_reexec_args(args, Path("/tmp/work"), auto_created=True)
        self.assertIn("polling", argv)
        self.assertNotIn("recoverable_polling", argv)

    def test_main_uses_unbuffered_child_process(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-test-") as tmpdir:
            with mock.patch.object(self.module, "parse_args") as mock_parse_args, \
                 mock.patch.object(self.module, "resolve_access_token", return_value="token"), \
                 mock.patch.object(self.module, "ensure_work_dir", return_value=(Path(tmpdir), True)), \
                 mock.patch.object(self.module, "create_run_dir", return_value=Path(tmpdir) / "fintools-agent-client-run-trading-600519-streaming-20260312-120000"), \
                 mock.patch.object(self.module, "ensure_local_runtime", return_value=("/tmp/fake-python", {"runtime_type": "venv", "runtime_detail": "current:/usr/bin/python3", "runtime_env_dir": str(self.module.SKILL_ROOT / '.runtime' / 'env')})), \
                 mock.patch.object(self.module, "print_runtime_banner"), \
                 mock.patch.object(self.module.subprocess, "run") as mock_subprocess_run:
                mock_parse_args.return_value = type(
                    "Args",
                    (),
                    {
                        "agent_type": "trading",
                        "mode": "streaming",
                        "stock_code": "600519",
                        "agent_url": "http://example.com/a2a/",
                        "access_token": None,
                        "work_dir": None,
                        "task_id": None,
                        "_in_env": False,
                        "_work_dir_auto_created": False,
                    },
                )()
                mock_subprocess_run.return_value = type("Completed", (), {"returncode": 0})()

                result = self.module.main()

                self.assertEqual(result, 0)
                called_args = mock_subprocess_run.call_args.kwargs["env"]
                called_cmd = mock_subprocess_run.call_args.args[0]
                self.assertEqual(called_args["PYTHONUNBUFFERED"], "1")
                self.assertEqual(called_args["FINTOOLS_RUNTIME_ENV_DIR"], str(self.module.SKILL_ROOT / ".runtime" / "env"))
                self.assertEqual(called_cmd[1], "-u")

    def test_main_treats_work_dir_as_parent_and_creates_child_run_dir(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-parent-") as tmpdir:
            parent_dir = Path(tmpdir)
            run_dir = parent_dir / "fintools-agent-client-run-trading-600519-streaming-20260312-120000"
            args = type(
                "Args",
                (),
                {
                    "agent_type": "trading",
                    "mode": "streaming",
                    "stock_code": "600519",
                    "agent_url": "http://example.com/a2a/",
                    "access_token": None,
                    "work_dir": str(parent_dir),
                    "task_id": None,
                    "_in_env": False,
                    "_work_dir_auto_created": False,
                },
            )()

            with mock.patch.object(self.module, "parse_args", return_value=args), \
                 mock.patch.object(self.module, "resolve_access_token", return_value="token"), \
                 mock.patch.object(self.module, "ensure_work_dir", return_value=(parent_dir, False)) as mock_ensure_work_dir, \
                 mock.patch.object(self.module, "create_run_dir", return_value=run_dir) as mock_create_run_dir, \
                 mock.patch.object(self.module, "ensure_local_runtime", return_value=("/tmp/fake-python", {"runtime_type": "venv", "runtime_detail": "current:/usr/bin/python3", "runtime_env_dir": str(self.module.SKILL_ROOT / '.runtime' / 'env')})), \
                 mock.patch.object(self.module, "print_runtime_banner"), \
                 mock.patch.object(self.module.subprocess, "run", return_value=type("Completed", (), {"returncode": 0})()) as mock_subprocess_run:
                result = self.module.main()

            self.assertEqual(result, 0)
            mock_ensure_work_dir.assert_called_once_with(str(parent_dir))
            mock_create_run_dir.assert_called_once_with(parent_dir, "trading", "600519", "streaming")
            child_args = mock_subprocess_run.call_args.args[0]
            self.assertIn("--work-dir", child_args)
            self.assertEqual(child_args[child_args.index("--work-dir") + 1], str(run_dir))

    def test_ensure_local_runtime_reuses_existing_env_when_hash_matches(self):
        runtime = {"type": "venv", "detail": "current:/usr/bin/python3", "python": "/usr/bin/python3"}
        install_state = {"requirements_hash": "abc123"}

        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-runtime-") as tmpdir:
            env_dir = Path(tmpdir)
            python_path = env_dir / "bin" / "python"
            python_path.parent.mkdir(parents=True, exist_ok=True)
            python_path.write_text("", encoding="utf-8")

            with mock.patch.object(self.module, "find_python_runtime", return_value=runtime), \
                 mock.patch.object(self.module, "local_runtime_dir", return_value=env_dir), \
                 mock.patch.object(self.module, "runtime_python_path", return_value=python_path), \
                 mock.patch.object(self.module, "requirements_fingerprint", return_value="abc123"), \
                 mock.patch.object(self.module, "load_install_state", return_value=install_state), \
                 mock.patch.object(self.module, "version_for", return_value=(3, 11, 9)), \
                 mock.patch.object(self.module, "write_install_state") as mock_write_state, \
                 mock.patch.object(self.module, "announce_status") as mock_announce_status, \
                 mock.patch.object(self.module, "update_local_runtime") as mock_update_runtime:
                env_python, metadata = self.module.ensure_local_runtime()

        self.assertEqual(env_python, str(python_path))
        self.assertEqual(metadata["runtime_env_dir"], str(env_dir))
        mock_update_runtime.assert_not_called()
        mock_write_state.assert_called_once()
        self.assertTrue(any("直接复用" in call.args[0] for call in mock_announce_status.call_args_list))

    def test_ensure_local_runtime_updates_env_when_requirements_change(self):
        runtime = {"type": "venv", "detail": "current:/usr/bin/python3", "python": "/usr/bin/python3"}
        install_state = {"requirements_hash": "oldhash"}

        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-runtime-") as tmpdir:
            env_dir = Path(tmpdir)
            python_path = env_dir / "bin" / "python"
            python_path.parent.mkdir(parents=True, exist_ok=True)
            python_path.write_text("", encoding="utf-8")

            with mock.patch.object(self.module, "find_python_runtime", return_value=runtime), \
                 mock.patch.object(self.module, "local_runtime_dir", return_value=env_dir), \
                 mock.patch.object(self.module, "runtime_python_path", return_value=python_path), \
                 mock.patch.object(self.module, "requirements_fingerprint", return_value="newhash"), \
                 mock.patch.object(self.module, "load_install_state", return_value=install_state), \
                 mock.patch.object(self.module, "version_for", return_value=(3, 11, 9)), \
                 mock.patch.object(self.module, "write_install_state") as mock_write_state, \
                 mock.patch.object(self.module, "announce_status") as mock_announce_status, \
                 mock.patch.object(self.module, "update_local_runtime") as mock_update_runtime:
                env_python, metadata = self.module.ensure_local_runtime()

        self.assertEqual(env_python, str(python_path))
        self.assertEqual(metadata["requirements_hash"], "newhash")
        mock_update_runtime.assert_called_once_with(python_path, "本地运行环境更新")
        mock_write_state.assert_called_once()
        self.assertTrue(any("正在更新本地运行环境" in call.args[0] for call in mock_announce_status.call_args_list))

    def test_run_inside_env_rejects_unsupported_agent_and_mode_combination(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-run-") as tmpdir:
            work_dir = Path(tmpdir)
            args = type(
                "Args",
                (),
                {
                    "agent_type": "unsupported_agent",
                    "mode": "streaming",
                    "stock_code": "600519",
                    "agent_url": "http://example.com/a2a/",
                    "access_token": None,
                    "work_dir": str(work_dir),
                    "task_id": None,
                    "_in_env": True,
                    "_work_dir_auto_created": False,
                },
            )()

            with mock.patch.object(self.module, "resolve_access_token", return_value="token"):
                with self.assertRaises(SystemExit):
                    self.module.asyncio.run(self.module.run_inside_env(args))

    def test_run_inside_env_uses_streaming_client_success_without_wrapper_download(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-run-") as tmpdir:
            work_dir = Path(tmpdir)

            args = type(
                "Args",
                (),
                {
                    "agent_type": "trading",
                    "mode": "streaming",
                    "stock_code": "600519",
                    "agent_url": "http://example.com/a2a/",
                    "access_token": None,
                    "work_dir": str(work_dir),
                    "task_id": None,
                    "_in_env": True,
                    "_work_dir_auto_created": False,
                },
            )()

            with mock.patch.object(self.module, "resolve_access_token", return_value="token"), \
                 mock.patch.object(self.module, "run_streaming_trading", new=mock.AsyncMock(return_value=True)):
                result = self.module.asyncio.run(self.module.run_inside_env(args))

            self.assertEqual(result, 0)
            summary = json.loads((work_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertTrue(summary["success"])
            self.assertIsNone(summary["report_path"])
            self.assertIsNone(summary["error"])

    def test_run_inside_env_records_streaming_report_path_from_run_directory(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-run-") as tmpdir:
            work_dir = Path(tmpdir)
            reports_dir = work_dir / "downloaded_reports"

            args = type(
                "Args",
                (),
                {
                    "agent_type": "trading",
                    "mode": "streaming",
                    "stock_code": "600519",
                    "agent_url": "http://example.com/a2a/",
                    "access_token": None,
                    "work_dir": str(work_dir),
                    "task_id": None,
                    "_in_env": True,
                    "_work_dir_auto_created": False,
                },
            )()

            async def fake_run_streaming(*_args, **_kwargs):
                reports_dir.mkdir(parents=True, exist_ok=True)
                report_path = reports_dir / "report.zip"
                report_path.write_text("zip-placeholder", encoding="utf-8")
                return True

            with mock.patch.object(self.module, "resolve_access_token", return_value="token"), \
                 mock.patch.object(self.module, "run_streaming_trading", new=mock.AsyncMock(side_effect=fake_run_streaming)):
                result = self.module.asyncio.run(self.module.run_inside_env(args))

            self.assertEqual(result, 0)
            summary = json.loads((work_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(summary["report_path"]).resolve(), (reports_dir / "report.zip").resolve())

    def test_run_inside_env_writes_run_log_and_result_lines(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-run-") as tmpdir:
            work_dir = Path(tmpdir)
            reports_dir = work_dir / "downloaded_reports"

            args = type(
                "Args",
                (),
                {
                    "agent_type": "trading",
                    "mode": "streaming",
                    "stock_code": "600519",
                    "agent_url": "http://example.com/a2a/",
                    "access_token": None,
                    "work_dir": str(work_dir),
                    "task_id": None,
                    "_in_env": True,
                    "_work_dir_auto_created": False,
                },
            )()

            async def fake_run_streaming(*_args, **_kwargs):
                reports_dir.mkdir(parents=True, exist_ok=True)
                (reports_dir / "report.zip").write_text("zip-placeholder", encoding="utf-8")
                print("stream body line")
                print("stream err line", file=sys.stderr)
                return True

            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            with mock.patch.object(self.module, "resolve_access_token", return_value="token"), \
                 mock.patch.object(self.module, "run_streaming_trading", new=mock.AsyncMock(side_effect=fake_run_streaming)), \
                 mock.patch("sys.stdout", stdout_buffer), \
                 mock.patch("sys.stderr", stderr_buffer):
                result = self.module.asyncio.run(self.module.run_inside_env(args))

            self.assertEqual(result, 0)
            log_text = (work_dir / "run.log").read_text(encoding="utf-8")
            self.assertIn("stream body line", log_text)
            self.assertIn("stream err line", log_text)

            stdout_text = stdout_buffer.getvalue()
            self.assertIn("[result] Summary written to:", stdout_text)
            self.assertIn("[result] Report path:", stdout_text)
            self.assertIn("[result] Run log:", stdout_text)
            self.assertIn("[result] Run directory:", stdout_text)
            self.assertIn("[result] Run success: yes", stdout_text)

    def test_run_inside_env_uses_deep_research_polling_client(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-run-") as tmpdir:
            work_dir = Path(tmpdir)

            args = type(
                "Args",
                (),
                {
                    "agent_type": "deep_research",
                    "mode": "polling",
                    "stock_code": "600519",
                    "agent_url": "http://example.com/a2a/",
                    "access_token": None,
                    "work_dir": str(work_dir),
                    "task_id": "task-123",
                    "_in_env": True,
                    "_work_dir_auto_created": False,
                },
            )()

            polling_result = {
                "status": "completed",
                "downloaded_file": str(work_dir / "downloaded_reports" / "report.md"),
                "error": None,
            }

            with mock.patch.object(self.module, "resolve_access_token", return_value="token"), \
                 mock.patch.object(self.module, "run_polling_deep_research", new=mock.AsyncMock(return_value=polling_result)):
                result = self.module.asyncio.run(self.module.run_inside_env(args))

            self.assertEqual(result, 0)
            summary = json.loads((work_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertTrue(summary["success"])
            self.assertEqual(summary["report_path"], polling_result["downloaded_file"])
            self.assertIsNone(summary["error"])

    def test_run_inside_env_passes_run_reports_dir_to_polling_client(self):
        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-run-") as tmpdir:
            work_dir = Path(tmpdir)

            args = type(
                "Args",
                (),
                {
                    "agent_type": "trading",
                    "mode": "polling",
                    "stock_code": "600519",
                    "agent_url": "http://example.com/a2a/",
                    "access_token": None,
                    "work_dir": str(work_dir),
                    "task_id": "task-456",
                    "_in_env": True,
                    "_work_dir_auto_created": False,
                },
            )()

            polling_result = {
                "status": "completed",
                "downloaded_file": str(work_dir / "downloaded_reports" / "report.zip"),
                "error": None,
            }

            with mock.patch.object(self.module, "resolve_access_token", return_value="token"), \
                 mock.patch.object(
                     self.module,
                     "run_polling_trading",
                     new=mock.AsyncMock(return_value=polling_result),
                 ) as mock_run_polling_trading:
                result = self.module.asyncio.run(self.module.run_inside_env(args))

            self.assertEqual(result, 0)
            self.assertEqual(
                Path(mock_run_polling_trading.await_args.kwargs["report_output_dir"]).resolve(),
                (work_dir / "downloaded_reports").resolve(),
            )

    def test_run_stock_agent_client_records_downloaded_file(self):
        client = mock.Mock()
        client.download_reports_zip = mock.AsyncMock(return_value="/tmp/example/report.zip")

        with mock.patch.object(
            self.db_client,
            "recover_task",
            new=mock.AsyncMock(return_value={"status": "completed"}),
        ):
            result = self.module.asyncio.run(
                self.db_client.run_stock_agent_client(
                    lambda **kwargs: client,
                    "Trading Agent Client",
                    "http://example.com/a2a/",
                    "600519",
                    "token",
                    task_id="task-789",
                    report_output_dir="/tmp/example",
                )
            )

        self.assertEqual(result["downloaded_file"], "/tmp/example/report.zip")
        client.download_reports_zip.assert_awaited_once_with("/tmp/example")

    def test_recover_task_returns_not_found_error_for_404(self):
        client = mock.Mock()
        client.get_task_status = mock.AsyncMock(side_effect=Exception("404 not found"))

        result = self.module.asyncio.run(self.db_client.recover_task(client, "task-404"))

        self.assertEqual(result["status"], "error")
        self.assertIn("Task not found", result["error"])

    def test_recover_task_returns_completed_task_without_waiting(self):
        client = mock.Mock()
        client.get_task_status = mock.AsyncMock(return_value={"status": "completed", "result": "done"})
        client.wait_for_task = mock.AsyncMock()

        result = self.module.asyncio.run(self.db_client.recover_task(client, "task-done"))

        self.assertEqual(result["status"], "completed")
        client.wait_for_task.assert_not_called()

    def test_recover_task_polls_when_task_still_running(self):
        client = mock.Mock()
        client.get_task_status = mock.AsyncMock(return_value={"status": "running"})
        client.wait_for_task = mock.AsyncMock(return_value={"status": "completed"})

        result = self.module.asyncio.run(self.db_client.recover_task(client, "task-running"))

        self.assertEqual(result["status"], "completed")
        client.wait_for_task.assert_awaited_once_with("task-running")

    def test_report_downloader_returns_none_for_404(self):
        downloader = self.utils.ReportDownloader("http://example.com", a2a_token="token")
        response = mock.Mock(status_code=404)
        response.headers = {}

        async_client = mock.AsyncMock()
        async_client.get = mock.AsyncMock(return_value=response)
        async_client.__aenter__.return_value = async_client
        async_client.__aexit__.return_value = None

        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-reports-") as tmpdir, \
             mock.patch.object(self.utils.httpx, "AsyncClient", return_value=async_client):
            result = self.module.asyncio.run(downloader.download_zip(tmpdir))

        self.assertIsNone(result)

    def test_report_downloader_returns_none_for_410(self):
        downloader = self.utils.ReportDownloader("http://example.com", a2a_token="token")
        response = mock.Mock(status_code=410)
        response.headers = {}

        async_client = mock.AsyncMock()
        async_client.get = mock.AsyncMock(return_value=response)
        async_client.__aenter__.return_value = async_client
        async_client.__aexit__.return_value = None

        with tempfile.TemporaryDirectory(prefix="fintools-agent-client-reports-") as tmpdir, \
             mock.patch.object(self.utils.httpx, "AsyncClient", return_value=async_client):
            result = self.module.asyncio.run(downloader.download_zip(tmpdir))

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
