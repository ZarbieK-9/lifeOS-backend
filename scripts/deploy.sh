#!/usr/bin/env bash
# Run on the server after the backend repo is updated (git reset --hard).
# Repo root = this backend project (not a monorepo).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BUILD_VERSION=$(git rev-parse --short HEAD)
BUILD_COMMIT=$(git rev-parse HEAD)
BUILD_BRANCH=$(git rev-parse --abbrev-ref HEAD)
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
printf '{"version":"%s","commit":"%s","branch":"%s","buildTime":"%s"}\n' \
  "$BUILD_VERSION" "$BUILD_COMMIT" "$BUILD_BRANCH" "$BUILD_TIME" >build-info.json
if [ -n "${GITHUB_RUN_NUMBER:-}" ] && [ -n "${GITHUB_RUN_ID:-}" ] && [ -n "${GITHUB_REPOSITORY:-}" ]; then
  export _LIFEOS_GH_RN="$GITHUB_RUN_NUMBER" _LIFEOS_GH_RID="$GITHUB_RUN_ID" _LIFEOS_GH_REPO="$GITHUB_REPOSITORY"
  python3 <<'PY'
import json
import os
from pathlib import Path

p = Path("build-info.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["ciRunNumber"] = int(os.environ["_LIFEOS_GH_RN"])
d["ciRunId"] = os.environ["_LIFEOS_GH_RID"]
d["ciRunUrl"] = (
    f"https://github.com/{os.environ['_LIFEOS_GH_REPO']}/actions/runs/{os.environ['_LIFEOS_GH_RID']}"
)
p.write_text(json.dumps(d, separators=(",", ":")) + "\n", encoding="utf-8")
PY
  unset _LIFEOS_GH_RN _LIFEOS_GH_RID _LIFEOS_GH_REPO
fi
echo "Build version: $BUILD_VERSION ($BUILD_COMMIT) on $BUILD_BRANCH at $BUILD_TIME"

[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
chmod +x generate.sh
export PATH="$PWD/.venv/bin:$PATH"
./generate.sh
set -a
if [ -f .env ]; then
  # shellcheck disable=SC1091
  . ./.env
fi
set +a
.venv/bin/alembic upgrade head
sudo systemctl restart pm2-zarbie.service
