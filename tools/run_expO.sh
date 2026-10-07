#!/usr/bin/env bash
# Experiment O flights (METHODOLOGY "Experiment O: pre-registration"): 3 repeats, nothing else on the machine.
set -u
cd "$(dirname "$0")/.."
EO=$(grep -Ev '^\s*(#|$)' o_gnss.parm | awk '{printf "%s%s=%s", (NR>1?",":""), $1, $2}')
mkdir -p batches/expO
for rep in ${REPS:-1 2 3}; do
  name="O_r${rep}${SUFFIX:-}"; conf="batches/expO/${name}.conf"
  echo "outdoor_indoor  0.5  2.0  60  ${name}" > "$conf"
  LOOPBACK_ONLY=1 GZ_IP=127.0.0.1 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST OUTBACK=15,1.5,50,0.5,20 \
    EXTRA_PARM_FILES="$HOME/thesis_ws/o_gnss.parm" EXPECT_OVERRIDE="$EO" \
    ./run_resumable_batch.sh "$conf" "expO_${name}" || { echo "expO: ${name} FAILED - stopping"; exit 1; }
done
echo "expO: all 3 flights complete"
