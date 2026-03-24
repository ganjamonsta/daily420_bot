#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/daily420_bot"
SERVICE_NAME="daily420-bot"
SERVICE_USER="${SERVICE_USER:-${SUDO_USER:-daily420}}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "[ERROR] Run as root: sudo bash deploy/install_debian12.sh"
  exit 1
fi

if [[ ! -f "${PROJECT_ROOT}/bot.py" ]]; then
  echo "[ERROR] bot.py not found in ${PROJECT_ROOT}. Run this script from cloned repository."
  exit 1
fi

echo "[1/8] Installing system packages..."
apt-get update
apt-get install -y python3 python3-venv python3-pip git ca-certificates rsync

echo "[2/8] Preparing service user..."
if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  useradd --system --create-home --shell /usr/sbin/nologin "${SERVICE_USER}"
fi

echo "[3/8] Ensuring app dir at ${APP_DIR}..."
mkdir -p "${APP_DIR}"
if [[ "${PROJECT_ROOT}" != "${APP_DIR}" ]]; then
  echo "[INFO] Syncing repository files to ${APP_DIR}"
  rsync -a --delete --exclude '.venv' --exclude '__pycache__' --exclude '.git' "${PROJECT_ROOT}/" "${APP_DIR}/"
  if [[ -d "${PROJECT_ROOT}/.git" ]]; then
    echo "[INFO] Preserving git metadata"
    rsync -a --delete "${PROJECT_ROOT}/.git/" "${APP_DIR}/.git/"
  fi
fi

chown -R "${SERVICE_USER}:${SERVICE_USER}" "${APP_DIR}"

echo "[4/8] Preparing environment file..."
if [[ ! -f "${APP_DIR}/.env" && -f "${APP_DIR}/.env.example" ]]; then
  cp "${APP_DIR}/.env.example" "${APP_DIR}/.env"
  chown "${SERVICE_USER}:${SERVICE_USER}" "${APP_DIR}/.env"
fi

echo "[5/8] Creating virtual environment and installing dependencies..."
runuser -u "${SERVICE_USER}" -- bash -lc "cd '${APP_DIR}' && python3 -m venv .venv"
runuser -u "${SERVICE_USER}" -- bash -lc "cd '${APP_DIR}' && .venv/bin/python -m pip install --upgrade pip"
runuser -u "${SERVICE_USER}" -- bash -lc "cd '${APP_DIR}' && .venv/bin/python -m pip install -r requirements.txt"

echo "[6/8] Installing systemd service..."
install -m 0644 "${APP_DIR}/deploy/${SERVICE_NAME}.service" "/etc/systemd/system/${SERVICE_NAME}.service"
sed -i "s/^User=.*/User=${SERVICE_USER}/" "/etc/systemd/system/${SERVICE_NAME}.service"
sed -i "s/^Group=.*/Group=${SERVICE_USER}/" "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"

echo "[7/8] Installing bot manager CLI..."
install -m 0755 "${APP_DIR}/deploy/botctl.sh" /usr/local/bin/daily420-bot

echo "[8/8] Starting service (if BOT_TOKEN configured)..."
if grep -Eq '^BOT_TOKEN=YOUR_BOT_TOKEN_HERE$|^BOT_TOKEN=$' "${APP_DIR}/.env"; then
  echo "[WARN] BOT_TOKEN is not configured in ${APP_DIR}/.env"
  echo "[INFO] Edit file and set token, then run:"
  echo "       sudo systemctl restart ${SERVICE_NAME}"
else
  systemctl restart "${SERVICE_NAME}"
  sleep 1
  systemctl --no-pager --full status "${SERVICE_NAME}" || true
fi

echo
echo "[DONE] Deployment bootstrap completed."
echo "Service user: ${SERVICE_USER}"
echo "Useful commands:"
echo "  sudo daily420-bot status"
echo "  sudo daily420-bot logs 200"
echo "  sudo daily420-bot follow"
echo "  sudo daily420-bot restart"
echo "  sudo daily420-bot update"
echo "  sudo daily420-bot update-force"
