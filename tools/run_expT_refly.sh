#!/usr/bin/env bash
# Experiment T: re-fly of the flights the standing IMU-gap rule (eval/imu_gap_check.py) marked unusable, unchanged
# configuration (a correction, not tuning). Cause: replays were run concurrently with the flights (CPU load -> IMU
# bridge irregularities). Run with NOTHING else on the machine. Old dirs are kept as <name>_IMUGAP.
set -u
cd "$(dirname "$0")/.."
declare -A IDS=([A]=all [B]=0,1,2,3 [C]=0,2 [D]=0)
EO=$(grep -Ev '^\s*(#|$)' tags_extnav.parm | awk '{printf "%s%s=%s", (NR>1?",":""), $1, $2}')
for name in "$@"; do
  c=${name:2:1}; conf="batches/expT/${name}_refly.conf"
  [ -d "$HOME/thesis_data/trials/$name" ] && [ ! -d "$HOME/thesis_data/trials/${name}_IMUGAP" ] && mv "$HOME/thesis_data/trials/$name" "$HOME/thesis_data/trials/${name}_IMUGAP"
  echo "room_tags  0.5  2.0  60  ${name}" > "$conf"
  LOOPBACK_ONLY=1 GZ_IP=127.0.0.1 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST TAG_BRIDGE=1 TAG_IDS="${IDS[$c]}" TAG_SIGMA_POS=0.05 \
    LAPS=5,6,0.5 EXTRA_PARM_FILES="$HOME/thesis_ws/tags_extnav.parm" EXPECT_OVERRIDE="$EO" \
    ./run_resumable_batch.sh "$conf" "expT_refly_${name}" || { echo "expT refly: ${name} FAILED - stopping"; exit 1; }
done
echo "expT refly: done"
