import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "download_skill.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("download_skill", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DownloadPublicSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_public_skill_download_url(self):
        url = self.module.public_skill_download_url("102", "http://example.com/api/v1/public/")
        self.assertEqual(url, "http://example.com/api/v1/public/skills/102/download")

    def test_extract_archive_filename_uses_content_disposition_filename(self):
        filename = self.module.extract_archive_filename(
            'attachment; filename="new-skill-create11777-main.zip"',
            "102",
        )
        self.assertEqual(filename, "new-skill-create11777-main.zip")

    def test_extract_archive_filename_supports_filename_star(self):
        filename = self.module.extract_archive_filename(
            "attachment; filename*=UTF-8''new-skill-create11777-main.zip",
            "102",
        )
        self.assertEqual(filename, "new-skill-create11777-main.zip")

    def test_validate_download_layout_does_not_require_agents_client(self):
        with mock.patch.object(self.module, "REQUIREMENTS_FILE", Path("/tmp/real-req.txt")):
            with mock.patch.object(Path, "is_file", return_value=True):
                self.module.validate_download_layout()

    def test_validate_download_layout_fails_when_requirements_missing(self):
        with mock.patch.object(self.module, "REQUIREMENTS_FILE", Path("/tmp/missing-req.txt")):
            with mock.patch.object(Path, "is_file", return_value=False):
                with self.assertRaises(SystemExit):
                    self.module.validate_download_layout()

    def test_main_uses_skill_run_dir(self):
        with tempfile.TemporaryDirectory(prefix="fintools-skill-parent-") as tmpdir:
            parent_dir = Path(tmpdir)
            run_dir = parent_dir / "fintools-agent-client-run-skill-102-download-20260312-120000"
            args = type(
                "Args",
                (),
                {
                    "skill_id": "102",
                    "public_base_url": "http://example.com/api/v1/public",
                    "work_dir": str(parent_dir),
                    "_in_env": False,
                    "_work_dir_auto_created": False,
                },
            )()

            with mock.patch.object(self.module, "parse_args", return_value=args), \
                 mock.patch.object(self.module, "ensure_work_dir", return_value=(parent_dir, False)), \
                 mock.patch.object(self.module, "create_run_dir", return_value=run_dir) as mock_create_run_dir, \
                 mock.patch.object(self.module, "ensure_local_runtime", return_value=("/tmp/fake-python", {"runtime_type": "venv", "runtime_detail": "current:/usr/bin/python3", "runtime_env_dir": "/tmp/fake-env"})), \
                 mock.patch.object(self.module, "print_runtime_banner"), \
                 mock.patch.object(self.module.os, "spawnve", return_value=0) as mock_spawnve:
                result = self.module.main()

            self.assertEqual(result, 0)
            mock_create_run_dir.assert_called_once_with(parent_dir, "skill", "102", "download")
            child_args = mock_spawnve.call_args.args[2]
            self.assertIn("--skill-id", child_args)
            self.assertNotIn("--agent-type", child_args)

    def test_run_inside_env_downloads_public_skill_archive(self):
        with tempfile.TemporaryDirectory(prefix="fintools-skill-run-") as tmpdir:
            work_dir = Path(tmpdir)
            args = type(
                "Args",
                (),
                {
                    "skill_id": "102",
                    "public_base_url": "http://example.com/api/v1/public",
                    "work_dir": str(work_dir),
                    "_in_env": True,
                    "_work_dir_auto_created": False,
                },
            )()

            class FakeResponse:
                def __init__(self):
                    self.headers = {"content-disposition": 'attachment; filename="skill-102.zip"'}

                def read(self):
                    return b"zip-bytes"

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return None

            with mock.patch.object(self.module.urllib_request, "urlopen", return_value=FakeResponse()):
                result = self.module.asyncio.run(self.module.run_inside_env(args))

            self.assertEqual(result, 0)
            downloaded = work_dir / "downloaded_skills" / "skill-102.zip"
            self.assertTrue(downloaded.is_file())
            summary = json.loads((work_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["skill_id"], "102")
            self.assertEqual(Path(summary["report_path"]).resolve(), downloaded.resolve())
