"""HealthService gRPC implementation."""

import json
from pathlib import Path

from sqlalchemy import text

from app.db import async_session
from app.services.partner_service import get_mqtt_client

from gen import lifeos_pb2, lifeos_pb2_grpc

_BUILD_INFO_PATH = Path(__file__).resolve().parent.parent.parent / "build-info.json"


def _build_info_ci() -> tuple[str, str, str]:
    """(ci_run_number, ci_run_id, ci_run_url) from build-info.json; empty strings if missing."""
    try:
        raw = _BUILD_INFO_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError, TypeError):
        return ("", "", "")
    n = data.get("ciRunNumber")
    num = str(n) if n is not None else ""
    rid = data.get("ciRunId") or ""
    if not isinstance(rid, str):
        rid = str(rid)
    url = data.get("ciRunUrl") or ""
    if not isinstance(url, str):
        url = str(url)
    return (num, rid, url)


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

        ci_num, ci_id, ci_url = _build_info_ci()

        return lifeos_pb2.HealthResponse(
            status=overall,
            db=db_status,
            mqtt=mqtt_status,
            ci_run_number=ci_num,
            ci_run_id=ci_id,
            ci_run_url=ci_url,
        )
