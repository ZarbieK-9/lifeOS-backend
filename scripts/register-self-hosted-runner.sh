#!/usr/bin/env bash
# Run ON THE SERVER (once) to install a GitHub Actions self-hosted runner for lifeOS-backend.
#
# 1. In browser: https://github.com/ZarbieK-9/lifeOS-backend/settings/actions/runners/new
#    Choose Linux x64, copy the token from the "./config.sh ... --token XXXXX" line.
# 2. On server:
#    export GITHUB_ACTIONS_RUNNER_TOKEN='paste-token-here'
#    bash register-self-hosted-runner.sh
#
# Optional: after `gh auth login` on the server, you can instead run:
#    TOKEN=$(gh api repos/ZarbieK-9/lifeOS-backend/actions/runners/registration-token -X POST -q .token)
#    GITHUB_ACTIONS_RUNNER_TOKEN="$TOKEN" bash register-self-hosted-runner.sh
#
# After configure: keep runner up with `./run.sh` or install service:
#    cd ~/actions-runner-lifeos && sudo ./svc.sh install && sudo ./svc.sh start

set -euo pipefail

TOKEN="${GITHUB_ACTIONS_RUNNER_TOKEN:-${1:-}}"
if [[ -z "${TOKEN}" ]]; then
  echo "Set GITHUB_ACTIONS_RUNNER_TOKEN or pass token as first argument."
  echo "Get a fresh token: Repo → Settings → Actions → Runners → New self-hosted runner"
  exit 1
fi

# Match existing pocketbridge runner version on your machine when possible.
RUNNER_VERSION="${RUNNER_VERSION:-2.333.0}"
RUNNER_DIR="${RUNNER_DIR:-${HOME}/actions-runner-lifeos}"
REPO_URL="${REPO_URL:-https://github.com/ZarbieK-9/lifeOS-backend}"
RUNNER_NAME="${RUNNER_NAME:-lifeos-backend-runner}"

mkdir -p "${RUNNER_DIR}"
cd "${RUNNER_DIR}"

if [[ ! -f config.sh ]]; then
  echo "Downloading actions-runner v${RUNNER_VERSION}..."
  curl -sL "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" | tar xz
fi

echo "Configuring runner (unattended)..."
./config.sh --url "${REPO_URL}" --token "${TOKEN}" --name "${RUNNER_NAME}" --unattended --replace

echo ""
echo "Done. Start the listener:"
echo "  cd ${RUNNER_DIR} && ./run.sh"
echo "Or install as systemd service (survives reboot):"
echo "  cd ${RUNNER_DIR} && sudo ./svc.sh install && sudo ./svc.sh start"
