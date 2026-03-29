"""HealthService gRPC implementation."""

import json
import subprocess
from pathlib import Path

from sqlalchemy import text

from app.db import async_session
from app.services.partner_service import get_mqtt_client

from gen import lifeos_pb2, lifeos_pb2_grpc

_BUILD_INFO_PATH = Path(__file__).resolve().parent.parent.parent / "build-info.json"
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _str_field(data: dict, key: str) -> str:
    v = data.get(key)
    if v is None:
        return ""
    return v if isinstance(v, str) else str(v)


def _load_build_info() -> dict:
    try:
        raw = _BUILD_INFO_PATH.read_text(encoding="utf-8")
        return json.loads(raw)
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def _git_fallback_version_commit() -> tuple[str, str]:
    """(short, full) from git when build-info.json is missing."""
    try:
        full = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=_REPO_ROOT,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            .decode()
            .strip()
        )
        short = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=_REPO_ROOT,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            .decode()
            .strip()
        )
        return (short, full)
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return ("", "")


def _build_metadata() -> tuple[str, str, str, str, str, str]:
    """ci_run_number, ci_run_id, ci_run_url, version, git_commit, build_time."""
    data = _load_build_info()
    if not data:
        short, full = _git_fallback_version_commit()
        return ("", "", "", short, full, "")

    n = data.get("ciRunNumber")
    ci_num = str(n) if n is not None else ""
    ci_id = _str_field(data, "ciRunId")
    ci_url = _str_field(data, "ciRunUrl")
    version = _str_field(data, "version")
    commit = _str_field(data, "commit")
    build_time = _str_field(data, "buildTime")
    if not version and not commit:
        short, full = _git_fallback_version_commit()
        version = version or short
        commit = commit or full
    return (ci_num, ci_id, ci_url, version, commit, build_time)


class HealthServicer(lifeos_pb2_grpc.HealthServiceServicer):
    async def Check(self, request, context):
        # Check database
        db_status = "ok"
        try:
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"error: {e}"

        # Check MQTT
        mqtt_status = "ok"
        mqtt = get_mqtt_client()
        if mqtt is None:
            mqtt_status = "disconnected"
        elif not mqtt.is_connected():
            mqtt_status = "disconnected"

        overall = "ok" if db_status == "ok" else "degraded"

        ci_num, ci_id, ci_url, version, git_commit, build_time = _build_metadata()

        return lifeos_pb2.HealthResponse(
            status=overall,
            db=db_status,
            mqtt=mqtt_status,
            ci_run_number=ci_num,
            ci_run_id=ci_id,
            ci_run_url=ci_url,
            version=version,
            git_commit=git_commit,
            build_time=build_time,
        )
