"""Small HTTP surface for Google OAuth: callback redirect + token exchange (PKCE + client_secret)."""

from __future__ import annotations

import json
import logging
import os
from urllib.parse import urlencode

import aiohttp
from aiohttp import web

logger = logging.getLogger("lifeos.oauth")

DEFAULT_BIND = "127.0.0.1"
DEFAULT_PORT = 8090


def _cors_headers() -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400",
    }


async def _google_callback(request: web.Request) -> web.StreamResponse:
    q = request.rel_url.query
    params: dict[str, str] = {}
    if q.get("code"):
        params["code"] = q["code"]
    if q.get("state"):
        params["state"] = q["state"]
    if q.get("error"):
        params["error"] = q["error"]
    if q.get("error_description"):
        params["error_description"] = q["error_description"]
    scheme = os.getenv("OAUTH_APP_SCHEME", "lifeos").strip().rstrip(":/")
    target = f"{scheme}://oauth?{urlencode(params)}"
    raise web.HTTPFound(location=target)


async def _oauth_exchange(request: web.Request) -> web.StreamResponse:
    if request.method == "OPTIONS":
        return web.Response(status=204, headers=_cors_headers())

    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "invalid_json", "error_description": "Body must be JSON"},
            status=400,
            headers=_cors_headers(),
        )

    code = body.get("code")
    code_verifier = body.get("code_verifier")
    redirect_uri = body.get("redirect_uri")
    if not code or not code_verifier or not redirect_uri:
        return web.json_response(
            {
                "error": "invalid_request",
                "error_description": "code, code_verifier, and redirect_uri are required",
            },
            status=400,
            headers=_cors_headers(),
        )

    client_id = (os.getenv("GOOGLE_OAUTH_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID") or "").strip()
    client_secret = (
        os.getenv("GOOGLE_OAUTH_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET") or ""
    ).strip()
    if not client_id or not client_secret:
        logger.error("Google OAuth: GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET not set")
        return web.json_response(
            {"error": "server_error", "error_description": "OAuth is not configured on the server"},
            status=503,
            headers=_cors_headers(),
        )

    form = {
        "code": str(code),
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": str(redirect_uri),
        "grant_type": "authorization_code",
        "code_verifier": str(code_verifier),
    }

    token_url = "https://oauth2.googleapis.com/token"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=form) as resp:
                text = await resp.text()
                http_status = resp.status
                try:
                    data = json.loads(text) if text else {}
                except Exception:
                    data = {"error": "invalid_response", "detail": text[:500]}
    except aiohttp.ClientError as e:
        logger.exception("Token request failed: %s", e)
        return web.json_response(
            {"error": "network_error", "error_description": "Could not reach Google token endpoint"},
            status=502,
            headers=_cors_headers(),
        )

    if isinstance(data, dict) and http_status == 200:
        return web.json_response(data, headers=_cors_headers())

    status = 400 if 400 <= http_status < 500 else http_status if http_status >= 400 else 400
    if not isinstance(data, dict):
        return web.json_response(
            {"error": "token_exchange_failed", "detail": str(data)[:500]},
            status=status,
            headers=_cors_headers(),
        )
    return web.json_response(data, status=status, headers=_cors_headers())


async def start_oauth_http() -> web.AppRunner:
    bind = os.getenv("OAUTH_HTTP_BIND", DEFAULT_BIND).strip() or DEFAULT_BIND
    port = int(os.getenv("OAUTH_HTTP_PORT", str(DEFAULT_PORT)) or DEFAULT_PORT)

    app = web.Application()
    app.router.add_get("/oauth/google/callback", _google_callback)
    app.router.add_route("OPTIONS", "/oauth/exchange", _oauth_exchange)
    app.router.add_post("/oauth/exchange", _oauth_exchange)

    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, bind, port)
    await site.start()
    logger.info("OAuth HTTP listening on http://%s:%s", bind, port)
    return runner


async def stop_oauth_http(runner: web.AppRunner) -> None:
    await runner.cleanup()
