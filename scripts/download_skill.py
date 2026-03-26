#!/usr/bin/env python3
"""Download a public Fintools skill archive into a managed run directory."""

import argparse
import asyncio
from email.message import Message
import json
import os
from pathlib import Path
import sys
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REQUIREMENTS_FILE = SKILL_ROOT / "requirements.txt"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_agent_client import (
    LOG_NAME,
    SUMMARY_NAME,
    TeeStream,
    announce_result,
    announce_status,
    create_run_dir,
    ensure_local_runtime,
    ensure_work_dir,
    fail,
    log_file_path,
    print_runtime_banner,
)


DEFAULT_PUBLIC_BASE_URL = "http://8.153.13.5:8000/api/v1/public"
SKILL_DOWNLOADS_DIRNAME = "downloaded_skills"


def validate_download_layout():
    missing = []
    if not REQUIREMENTS_FILE.is_file():
        missing.append("requirements.txt")
    if missing:
        fail(
            "The skill download bundle is incomplete. Missing required bundled files under {0}: {1}".format(
                SKILL_ROOT, ", ".join(missing)
            )
        )


validate_download_layout()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download a public Fintools skill archive into a managed run directory."
    )
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--public-base-url", default=DEFAULT_PUBLIC_BASE_URL)
    parser.add_argument("--work-dir")
    parser.add_argument("--_in-env", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_work-dir-auto-created", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def skill_downloads_dir(work_dir):
    path = Path(work_dir) / SKILL_DOWNLOADS_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def public_skill_download_url(skill_id, public_base_url):
    base = (public_base_url or DEFAULT_PUBLIC_BASE_URL).rstrip("/")
    encoded_skill_id = urllib_parse.quote(str(skill_id).strip(), safe="")
    return "{0}/skills/{1}/download".format(base, encoded_skill_id)


def extract_archive_filename(content_disposition, skill_id):
    message = Message()
    message["content-disposition"] = content_disposition or ""
    filename = message.get_filename()
    if filename:
        filename = Path(filename).name
        if filename:
            return filename
    return "skill-{0}.zip".format(skill_id)


def download_public_skill(skill_id, public_base_url, output_dir):
    output_path = skill_downloads_dir(output_dir)
    url = public_skill_download_url(skill_id, public_base_url)
    announce_status("正在下载 public skill: {0}".format(skill_id))
    announce_status("Public skill URL: {0}".format(url))
    request = urllib_request.Request(url, method="GET")
    try:
        with urllib_request.urlopen(request) as response:
            content = response.read()
            content_disposition = response.headers.get("content-disposition", "")
            filename = extract_archive_filename(content_disposition, skill_id)
            file_path = output_path / filename
            file_path.write_bytes(content)
            announce_result("Downloaded skill archive: {0}".format(file_path))
            return str(file_path.resolve())
    except urllib_error.HTTPError as exc:
        fail("Failed to download public skill {0}: HTTP {1}".format(skill_id, exc.code))
    except urllib_error.URLError as exc:
        fail("Failed to download public skill {0}: {1}".format(skill_id, exc.reason))


def write_summary(work_dir, payload):
    summary_path = Path(work_dir) / SUMMARY_NAME
    summary_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return summary_path


async def run_inside_env(args):
    work_dir = Path(args.work_dir).resolve()
    run_log = log_file_path(work_dir)
    parent_auto_created = args._work_dir_auto_created

    announce_status("正在准备当前 run 目录")
    os.chdir(str(work_dir))

    report_path = None
    error = None
    success = False
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    with run_log.open("a", encoding="utf-8") as log_handle:
        tee_stdout = TeeStream(original_stdout, log_handle)
        tee_stderr = TeeStream(original_stderr, log_handle)
        sys.stdout = tee_stdout
        sys.stderr = tee_stderr
        try:
            announce_status("当前日志文件: {0}".format(run_log))
            report_path = download_public_skill(args.skill_id, args.public_base_url, work_dir)
            success = True
        except SystemExit:
            raise
        except Exception as exc:
            error = str(exc)
        finally:
            tee_stdout.flush()
            tee_stderr.flush()
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    summary = {
        "skill_id": args.skill_id,
        "public_base_url": args.public_base_url,
        "runtime_type": os.environ.get("FINTOOLS_RUNTIME_TYPE", "unknown"),
        "runtime_detail": os.environ.get("FINTOOLS_RUNTIME_DETAIL", "unknown"),
        "runtime_env_dir": os.environ.get("FINTOOLS_RUNTIME_ENV_DIR", "unknown"),
        "work_dir": str(work_dir),
        "parent_dir_source": "auto-created" if parent_auto_created else "user-provided",
        "run_dir": str(work_dir),
        "log_path": str(run_log),
        "report_path": report_path,
        "success": bool(success),
        "error": error,
    }
    announce_status("正在写入 summary.json")
    summary_path = write_summary(work_dir, summary)
    announce_result("Summary written to: {0}".format(summary_path))
    announce_result("Report path: {0}".format(report_path or "none"))
    announce_result("Run log: {0}".format(run_log))
    announce_result("Run directory: {0}".format(work_dir))
    announce_result("Run success: {0}".format("yes" if success else "no"))
    if error:
        announce_result("Run error: {0}".format(error))

    if success:
        return 0
    return 1


def main():
    announce_status("正在解析运行参数")
    args = parse_args()

    if args._in_env:
        return asyncio.run(run_inside_env(args))

    announce_status("正在准备主目录")
    parent_dir, parent_auto_created = ensure_work_dir(args.work_dir)
    announce_status("正在创建本次 run 目录")
    work_dir = create_run_dir(parent_dir, "skill", args.skill_id, "download")
    announce_status("正在准备 skill 本地运行环境")
    env_python, runtime_metadata = ensure_local_runtime()
    print_runtime_banner(parent_dir, work_dir, parent_auto_created, runtime_metadata)

    child_env = os.environ.copy()
    child_env["FINTOOLS_RUNTIME_TYPE"] = runtime_metadata["runtime_type"]
    child_env["FINTOOLS_RUNTIME_DETAIL"] = runtime_metadata["runtime_detail"]
    child_env["FINTOOLS_RUNTIME_ENV_DIR"] = runtime_metadata["runtime_env_dir"]
    child_env["PYTHONUNBUFFERED"] = "1"

    child_args = [
        env_python,
        "-u",
        str(Path(__file__).resolve()),
        "--skill-id",
        str(args.skill_id),
        "--public-base-url",
        args.public_base_url,
        "--work-dir",
        str(work_dir),
        "--_in-env",
    ]
    if parent_auto_created:
        child_args.append("--_work-dir-auto-created")
    announce_result("Runtime env: {0}".format(runtime_metadata["runtime_env_dir"]))
    announce_status("正在启动子进程执行 public skill 下载")
    completed = os.spawnve(os.P_WAIT, env_python, child_args, child_env)
    return completed


if __name__ == "__main__":
    raise SystemExit(main())
