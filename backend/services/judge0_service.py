import asyncio
import base64
from dataclasses import dataclass
from typing import Optional

import httpx

from core.config import settings


LANGUAGE_IDS = {
    "python": 71,
    "java": 62,
    "cpp": 54,
    "javascript": 63,
}

RUNNING_STATUS_IDS = {1, 2}
COMPILE_ERROR_STATUS_IDS = {6}
TIME_LIMIT_STATUS_IDS = {5}


class Judge0Unavailable(Exception):
    pass


@dataclass
class Judge0Result:
    status_id: int
    status_description: str
    stdout: str = ""
    stderr: str = ""
    compile_output: str = ""
    time: Optional[float] = None
    memory: Optional[int] = None
    message: str = ""

    @property
    def raw_status(self):
        if self.status_id == 3:
            return "Finished"
        if self.status_id in COMPILE_ERROR_STATUS_IDS:
            return "Compile Error"
        if self.status_id in TIME_LIMIT_STATUS_IDS:
            return "Time Limit Exceeded"
        if self.status_id == 4:
            return "Wrong Answer"
        if self.status_id >= 7:
            return "Runtime Error"
        return self.status_description or "Judge Error"


def trim_output(value: Optional[str]) -> str:
    if not value:
        return ""
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def truncate_text(value: Optional[str], limit: Optional[int] = None) -> str:
    if not value:
        return ""
    limit = limit or settings.CODE_OUTPUT_LIMIT
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...[truncated]"


def decode_judge0_text(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return base64.b64decode(value).decode("utf-8", errors="replace")
    except Exception:
        return value


class Judge0Service:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.JUDGE0_BASE_URL).rstrip("/")
        self.timeout = settings.JUDGE0_TIMEOUT_SECONDS
        self.poll_interval = settings.JUDGE0_POLL_INTERVAL_SECONDS
        self.max_poll_attempts = settings.JUDGE0_MAX_POLL_ATTEMPTS

    async def run_code(self, language: str, source_code: str, stdin: str) -> Judge0Result:
        language_id = LANGUAGE_IDS.get(language)
        if not language_id:
            raise ValueError("Unsupported language")

        payload = {
            "language_id": language_id,
            "source_code": source_code,
            "stdin": stdin,
            "cpu_time_limit": 2,
            "wall_time_limit": 6,
            "memory_limit": 128000,
            "max_processes_and_or_threads": 64,
            "enable_network": False,
        }
        if language in {"cpp", "java"}:
            payload.update(
                {
                    "cpu_time_limit": 4,
                    "wall_time_limit": 12,
                    "memory_limit": 256000,
                }
            )

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                create_resp = await client.post("/submissions", params={"base64_encoded": "false", "wait": "false"}, json=payload)
                create_resp.raise_for_status()
                token = create_resp.json().get("token")
                if not token:
                    raise Judge0Unavailable("Judge0 did not return a submission token.")

                fields = "stdout,stderr,compile_output,message,status,time,memory"
                for _ in range(self.max_poll_attempts):
                    result_resp = await client.get(
                        f"/submissions/{token}",
                        params={"base64_encoded": "true", "fields": fields},
                    )
                    result_resp.raise_for_status()
                    data = result_resp.json()
                    status = data.get("status") or {}
                    status_id = int(status.get("id") or 0)
                    if status_id not in RUNNING_STATUS_IDS:
                        return Judge0Result(
                            status_id=status_id,
                            status_description=status.get("description") or "Unknown",
                            stdout=truncate_text(decode_judge0_text(data.get("stdout"))),
                            stderr=truncate_text(decode_judge0_text(data.get("stderr"))),
                            compile_output=truncate_text(decode_judge0_text(data.get("compile_output"))),
                            message=truncate_text(decode_judge0_text(data.get("message"))),
                            time=float(data["time"]) if data.get("time") not in (None, "") else None,
                            memory=int(data["memory"]) if data.get("memory") not in (None, "") else None,
                        )
                    await asyncio.sleep(self.poll_interval)

        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
            raise Judge0Unavailable(f"Judge0 service is unavailable: {exc}") from exc

        return Judge0Result(
            status_id=5,
            status_description="Time Limit Exceeded",
            message="Judge0 polling timed out.",
        )


judge0_service = Judge0Service()
