#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="daily420-bot"
APP_DIR="/opt/daily420_bot"
DEFAULT_BRANCH="main"

resolve_branch() {
  check_repo
  local branch=""
  branch="$(runuser -u daily420 -- bash -lc "cd '${APP_DIR}' && git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||'")" || true
  if [[ -n "${branch}" ]]; then
    echo "${branch}"
    return
  fi

  branch="$(runuser -u daily420 -- bash -lc "cd '${APP_DIR}' && git rev-parse --abbrev-ref HEAD 2>/dev/null")" || true
  if [[ -n "${branch}" ]]; then
    echo "${branch}"
    return
  fi

  echo "${DEFAULT_BRANCH}"
}

usage() {
  cat <<'EOF'
Usage: daily420-bot <command> [args]

Commands:
  status                Show systemd status
  start                 Start bot service
  stop                  Stop bot service
  restart               Restart bot service
  logs [N]              Show last N log lines (default: 200)
  follow                Follow live logs
  update [branch]       Safe update (git pull --ff-only + deps + restart)
  update-force [branch] Force update (reset to origin/branch + clean + deps + restart)
  menu                  Interactive menu
  help                  Show this help
EOF
}

need_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "[ERROR] Run as root: sudo daily420-bot $*" >&2
    exit 1
  fi
}

check_app_dir() {
  if [[ ! -d "${APP_DIR}" ]]; then
    echo "[ERROR] App dir not found: ${APP_DIR}" >&2
    exit 1
  fi
}

check_repo() {
  check_app_dir
  if [[ ! -d "${APP_DIR}/.git" ]]; then
    echo "[ERROR] ${APP_DIR} is not a git repository" >&2
    exit 1
  fi
}

run_as_service_user() {
  local cmd="$1"
  runuser -u daily420 -- bash -lc "cd '${APP_DIR}' && ${cmd}"
}

install_deps() {
  if [[ ! -x "${APP_DIR}/.venv/bin/python" ]]; then
    run_as_service_user "python3 -m venv .venv"
  fi
  run_as_service_user ".venv/bin/python -m pip install --upgrade pip"
  run_as_service_user ".venv/bin/python -m pip install -r requirements.txt"
}

do_update() {
  local branch="$1"
  need_root "update"
  check_repo
  echo "[INFO] Updating from branch: ${branch}"
  run_as_service_user "git checkout '${branch}'"
  run_as_service_user "git pull --ff-only origin '${branch}'"
  install_deps
  systemctl restart "${SERVICE_NAME}"
  echo "[OK] Updated and restarted ${SERVICE_NAME}"
}

do_update_force() {
  local branch="$1"
  need_root "update-force"
  check_repo

  echo "[WARN] This will discard ALL local changes in ${APP_DIR}."
  read -r -p "Type FORCE to continue: " answer
  if [[ "${answer}" != "FORCE" ]]; then
    echo "[INFO] Canceled"
    exit 0
  fi

  echo "[INFO] Force updating from origin/${branch}"
  run_as_service_user "git fetch --all --prune"
  run_as_service_user "git checkout '${branch}'"
  run_as_service_user "git reset --hard 'origin/${branch}'"
  run_as_service_user "git clean -fd"
  install_deps
  systemctl restart "${SERVICE_NAME}"
  echo "[OK] Force-updated and restarted ${SERVICE_NAME}"
}

show_menu() {
  while true; do
    echo
    echo "==== Daily420 Bot Manager ===="
    echo "1) Status"
    echo "2) Start"
    echo "3) Stop"
    echo "4) Restart"
    echo "5) Logs (last 200)"
    echo "6) Follow logs"
    echo "7) Update (safe, current/default branch)"
    echo "8) Update FORCE (current/default branch)"
    echo "9) Exit"
    read -r -p "Select: " choice

    case "${choice}" in
      1) systemctl status "${SERVICE_NAME}" --no-pager || true ;;
      2) need_root "start"; systemctl start "${SERVICE_NAME}" ;;
      3) need_root "stop"; systemctl stop "${SERVICE_NAME}" ;;
      4) need_root "restart"; systemctl restart "${SERVICE_NAME}" ;;
      5) journalctl -u "${SERVICE_NAME}" -n 200 --no-pager ;;
      6) journalctl -u "${SERVICE_NAME}" -f ;;
      7) do_update "$(resolve_branch)" ;;
      8) do_update_force "$(resolve_branch)" ;;
      9) break ;;
      *) echo "Unknown option" ;;
    esac
  done
}

cmd="${1:-help}"
case "${cmd}" in
  status)
    systemctl status "${SERVICE_NAME}" --no-pager || true
    ;;
  start)
    need_root "start"
    systemctl start "${SERVICE_NAME}"
    ;;
  stop)
    need_root "stop"
    systemctl stop "${SERVICE_NAME}"
    ;;
  restart)
    need_root "restart"
    systemctl restart "${SERVICE_NAME}"
    ;;
  logs)
    lines="${2:-200}"
    journalctl -u "${SERVICE_NAME}" -n "${lines}" --no-pager
    ;;
  follow)
    journalctl -u "${SERVICE_NAME}" -f
    ;;
  update)
    branch="${2:-$(resolve_branch)}"
    do_update "${branch}"
    ;;
  update-force)
    branch="${2:-$(resolve_branch)}"
    do_update_force "${branch}"
    ;;
  menu)
    show_menu
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    usage
    exit 1
    ;;
esac
