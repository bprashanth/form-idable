#!/usr/bin/env bash
# The ONLY sanctioned way to start a GPU container on this host.
#
# Why this exists (see ../../CLAUDE.md "Before launching any local training /
# inference job"): the GB10 shares 121 GB between CPU and GPU. An uncapped
# `--gpus all` container hard-freezes the box — GPU memory is charged to no
# process, the OOM killer never fires, and the kernel livelocks in reclaim.
# No panic, no logs, hard reset. It happened twice on 2026-07-31 because these
# rules were not followed.
#
# This wrapper enforces:
#   * a hard cgroup memory cap, so an over-allocation gets OOM-killed
#     (survivable) instead of freezing the host (not survivable)
#   * --shm-size 8g (not 24/32g)
#   * a `free -g` preflight requiring >40 GB available
#   * a reboot check — if the box rebooted recently, a job probably froze it,
#     so refuse to auto-relaunch without an explicit override
#
# Usage:
#   ./gpu_run.sh <name> <mem_gb> -- <docker args...>
# Example:
#   ./gpu_run.sh train2b 60 -- -v /models:/models --entrypoint bash img -c "..."
#
# NEVER add `-d` yourself and never wrap this in `setsid nohup` after a crash:
# re-arming detached is what turned one freeze into a reboot loop. Run it in
# the foreground of a background Bash tool call and watch the logs.
set -euo pipefail

NAME=${1:?usage: gpu_run.sh <name> <mem_gb> -- <docker args...>}
MEM=${2:?need memory cap in GB}
shift 2
[[ "${1:-}" == "--" ]] && shift

MIN_FREE=${MIN_FREE_GB:-40}
AVAIL=$(free -g | awk 'NR==2{print $7}')
if (( AVAIL < MIN_FREE )); then
  echo "REFUSING: only ${AVAIL} GB available, need >${MIN_FREE} GB." >&2
  echo "Stop other GPU consumers first (docker ps; systemctl status ds4-ssd)." >&2
  exit 1
fi

# If the host rebooted in the last 30 min, a previous job probably froze it.
BOOT_MIN=$(awk '{print int($1/60)}' /proc/uptime)
if (( BOOT_MIN < 30 )) && [[ "${FORCE_AFTER_REBOOT:-0}" != "1" ]]; then
  echo "REFUSING: host booted ${BOOT_MIN} min ago — a previous job may have" >&2
  echo "frozen it. Investigate (last -x reboot), then re-run with" >&2
  echo "FORCE_AFTER_REBOOT=1 if you are sure." >&2
  exit 1
fi

if (( MEM > AVAIL - 20 )); then
  echo "REFUSING: cap ${MEM}g leaves <20 GB headroom (avail ${AVAIL}g)." >&2
  exit 1
fi

docker rm -f "$NAME" >/dev/null 2>&1 || true
echo "launching $NAME  cap=${MEM}g  avail=${AVAIL}g  shm=8g"
exec docker run --rm --name "$NAME" --gpus all \
  --memory "${MEM}g" --memory-swap "${MEM}g" --shm-size 8g \
  "$@"
