import asyncio
import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.run_agent_client import (
    default_runs_parent_dir,
    load_cached_access_token,
    run_streaming_trading,
    token_file_path,
)


PLACEHOLDER_TOKEN_MARKERS = (
    "your-token",
    "your-secret",
    "your-fintools",
    "placeholder",
)


def _is_placeholder_token(token: str | None) -> bool:
    if not token:
        return False
    normalized = token.strip().lower()
    return any(marker in normalized for marker in PLACEHOLDER_TOKEN_MARKERS)


def _resolve_token(access_token: str | None = None) -> str:
    if access_token:
        if _is_placeholder_token(access_token):
            raise RuntimeError("Invalid FINTOOLS access token: explicit placeholder token was provided.")
        return access_token

    parent_dir = default_runs_parent_dir()
    token = load_cached_access_token(parent_dir)
    token_path = token_file_path(parent_dir)
    if not token:
        raise RuntimeError(
            "Missing FINTOOLS access token cache. Run the skill client once to create {0}.".format(token_path)
        )
    if _is_placeholder_token(token):
        raise RuntimeError(
            "Invalid FINTOOLS access token cache at {0}. Replace the placeholder token with a real cached token.".format(
                token_path
            )
        )
    return token


class _StreamingQueueWriter:
    def __init__(self, queue: asyncio.Queue):
        self._queue = queue
        self._buffer = ""

    def write(self, text):
        if not text:
            return
        self._buffer += str(text)
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip("\r")
            if line.strip():
                self._queue.put_nowait({"type": "streaming_text", "message": line})

    def flush(self):
        return

    def close(self):
        if self._buffer.strip():
            self._queue.put_nowait({"type": "streaming_text", "message": self._buffer.rstrip("\r")})
        self._buffer = ""


async def execute_trading_agent_via_skill(
    stock_code: str,
    agent_url: str,
    access_token: str | None = None,
    log_buffer: io.StringIO | None = None,
):
    token = _resolve_token(access_token)
    clean_stock_code = stock_code.split(".")[0] if "." in stock_code else stock_code

    if log_buffer is None:
        return await run_streaming_trading(clean_stock_code, agent_url, token)

    with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
        return await run_streaming_trading(clean_stock_code, agent_url, token)


async def stream_trading_agent_via_skill(
    stock_code: str,
    agent_url: str,
    access_token: str | None = None,
):
    token = _resolve_token(access_token)
    clean_stock_code = stock_code.split(".")[0] if "." in stock_code else stock_code
    queue: asyncio.Queue = asyncio.Queue()

    async def _runner():
        writer = _StreamingQueueWriter(queue)
        try:
            with redirect_stdout(writer), redirect_stderr(writer):
                result = await run_streaming_trading(clean_stock_code, agent_url, token)
            writer.close()
            await queue.put({"type": "result", "result": result})
        except Exception as exc:
            writer.close()
            await queue.put({"type": "error", "error": exc})

    task = asyncio.create_task(_runner())
    try:
        while True:
            item = await queue.get()
            if item["type"] == "error":
                raise item["error"]
            yield item
            if item["type"] == "result":
                break
    finally:
        await task


def run_trading_agent_via_skill(
    stock_code: str,
    agent_url: str,
    access_token: str | None = None,
    log_buffer: io.StringIO | None = None,
):
    return asyncio.run(
        execute_trading_agent_via_skill(
            stock_code=stock_code,
            agent_url=agent_url,
            access_token=access_token,
            log_buffer=log_buffer,
        )
    )


def extract_trading_action(result) -> str | None:
    if not isinstance(result, dict):
        return None

    payload = result.get("result")
    if isinstance(payload, dict):
        action = payload.get("action")
        if isinstance(action, str):
            normalized = action.strip().lower()
            if normalized in {"buy", "sell", "hold"}:
                return normalized

    return None
