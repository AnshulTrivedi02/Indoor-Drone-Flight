# Flight-lock helpers (source this file). Ruling 2026-10-08: locks are created ATOMICALLY with an owner ID and only
# their owner removes them. BUILD_LOCK (coding agents, tools/heavy.py) and FLIGHT_LOCK (flights) exclude each other.
#   flight_lock_acquire "<what>" [cap_s]  : waits while BUILD_LOCK exists (cap, default 3600 s); then creates FLIGHT_LOCK
#                                           with noclobber (fails if it exists); exports FLIGHT_LOCK_TOKEN
#   flight_lock_release                   : removes FLIGHT_LOCK only if it holds our token
FLIGHT_LOCK_FILE="$HOME/thesis_data/FLIGHT_LOCK"; BUILD_LOCK_FILE="$HOME/thesis_data/BUILD_LOCK"
flight_lock_acquire() {
    local what="$1" cap="${2:-3600}" t0=$SECONDS
    while [ -e "$BUILD_LOCK_FILE" ] && [ $((SECONDS - t0)) -lt "$cap" ]; do sleep 20; done
    [ -e "$BUILD_LOCK_FILE" ] && { echo "flight_lock: BUILD_LOCK held > ${cap} s: $(cat "$BUILD_LOCK_FILE")" >&2; return 1; }
    FLIGHT_LOCK_TOKEN="pid $$ token $RANDOM$RANDOM $(date -Is) : $what"
    if ! ( set -o noclobber; echo "$FLIGHT_LOCK_TOKEN" > "$FLIGHT_LOCK_FILE" ) 2>/dev/null; then
        echo "flight_lock: FLIGHT_LOCK already held: $(cat "$FLIGHT_LOCK_FILE" 2>/dev/null)" >&2; return 1
    fi
    export FLIGHT_LOCK_TOKEN
    sleep 5                                   # a BUILD_LOCK created in the same instant wins: back off
    if [ -e "$BUILD_LOCK_FILE" ]; then flight_lock_release; echo "flight_lock: BUILD_LOCK raced; released" >&2; return 1; fi
}
flight_lock_release() {
    [ -n "${FLIGHT_LOCK_TOKEN:-}" ] && [ -f "$FLIGHT_LOCK_FILE" ] && [ "$(cat "$FLIGHT_LOCK_FILE")" = "$FLIGHT_LOCK_TOKEN" ] && rm -f "$FLIGHT_LOCK_FILE"
    return 0
}
