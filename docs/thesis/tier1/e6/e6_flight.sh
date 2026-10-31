#!/usr/bin/env bash
# E6 flight: e6_flight.sh <trial name> <HPROFILE json>. The T_A configuration (tools/run_expT_refly.sh) minus LAPS, plus
# HPROFILE; batch state under ~/thesis_data/tier1/e6/batches (guard-safe, D90); FLIGHT_LOCK via tools/flight_lock.sh,
# never inside heavy.py (D81). docs/thesis/tier1/e6_preregistration.md §3.1, §8.
set -u
NAME="$1"; PROF="$2"
E=/home/makerspace/thesis_data/tier1/e6; mkdir -p $E/flights $E/batches
[ -f "$PROF" ] || { echo "no profile $PROF" >&2; exit 1; }
case "$NAME" in T_*) echo "refusing a T_ name (guard glob)" >&2; exit 1;; esac
[ -e "$HOME/thesis_data/trials/$NAME" ] && { echo "trial $NAME exists; new flights get new names" >&2; exit 1; }
source /home/makerspace/thesis_ws/tools/flight_lock.sh
flight_lock_acquire "E6 flight $NAME" 7200 || exit 1
trap flight_lock_release EXIT
cd /home/makerspace/thesis_ws
EO=$(grep -Ev '^\s*(#|$)' tags_extnav.parm | awk '{printf "%s%s=%s", (NR>1?",":""), $1, $2}')
conf="$E/flights/${NAME}.conf"; echo "room_tags  0.5  2.0  60  ${NAME}" > "$conf"
LOOPBACK_ONLY=1 GZ_IP=127.0.0.1 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST TAG_BRIDGE=1 TAG_IDS=all TAG_SIGMA_POS=0.05 \
  HPROFILE="$PROF" EXTRA_PARM_FILES="$HOME/thesis_ws/tags_extnav.parm" EXPECT_OVERRIDE="$EO" \
  BATCHES_DIR="$E/batches" ./run_resumable_batch.sh "$conf" "$NAME"
rc=$?
echo "exit $rc" > "$E/flights/${NAME}.done"
exit $rc
