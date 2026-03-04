#!/usr/bin/env bash

set -e

INTERVAL=60
NETWORK=home_lab
KILL_SWITCH="scripts/chaos.stop"

# containers ktoré nechceš rozbíjať
PROTECTED=(
  "npm"
  "portainer"
)

log() {
  echo "[CHAOS] $1"
}

check_kill_switch() {
  if [ -f "$KILL_SWITCH" ]; then
    log "Kill switch detected. Exiting."
    exit 0
  fi
}

random_container() {
  docker ps --format "{{.Names}}" | grep -v -E "$(IFS="|"; echo "${PROTECTED[*]}")" | shuf -n 1
}

restart_container() {
  c=$(random_container)
  log "Restarting $c"
  docker restart "$c"
}

kill_container() {
  c=$(random_container)
  log "Killing $c"
  docker kill "$c"
}

cpu_throttle() {
  c=$(random_container)
  log "CPU limiting $c"
  docker update --cpus=0.2 "$c"
}

network_disconnect() {
  c=$(random_container)
  log "Disconnecting $c from $NETWORK"
  docker network disconnect "$NETWORK" "$c" || true
}

restore_network() {
  c=$(random_container)
  log "Reconnecting $c to $NETWORK"
  docker network connect "$NETWORK" "$c" || true
}

CHAOS_FUNCS=(
  restart_container
  kill_container
  cpu_throttle
  network_disconnect
)

log "Chaos started"

while true; do

  check_kill_switch

  action=${CHAOS_FUNCS[$RANDOM % ${#CHAOS_FUNCS[@]}]}

  $action

  sleep $INTERVAL

done