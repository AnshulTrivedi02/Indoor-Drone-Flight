#!/usr/bin/env bash
# Experiment T flights (pre-registered: METHODOLOGY "Experiment T: pre-registration"). 12 single-trial resumable batches,
# interleaved A1 B1 C1 D1 A2 ... D3, each with its own TAG_IDS (the batch runner has no per-trial environment).
# Re-running resumes (completed batches are skipped by run_resumable_batch.sh). Stops at the first failed batch.
set -u
cd "$(dirname "$0")/.."
declare -A IDS=([A]=all [B]=0,1,2,3 [C]=0,2 [D]=0)
EO=$(grep -Ev '^\s*(#|$)' tags_extnav.parm | awk '{printf "%s%s=%s", (NR>1?",":""), $1, $2}')
for rep in 1 2 3; do
  for c in A B C D; do
    name="T_${c}_r${rep}"; conf="batches/expT/${name}.conf"
    echo "room_tags  0.5  2.0  60  ${name}" > "$conf"
    LOOPBACK_ONLY=1 GZ_IP=127.0.0.1 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST TAG_BRIDGE=1 TAG_IDS="${IDS[$c]}" TAG_SIGMA_POS=0.05 \
      LAPS=5,6,0.5 EXTRA_PARM_FILES="$HOME/thesis_ws/tags_extnav.parm" EXPECT_OVERRIDE="$EO" \
      ./run_resumable_batch.sh "$conf" "expT_${name}" || { echo "expT: batch ${name} FAILED - stopping"; exit 1; }
  done
done
echo "expT: all 12 flights complete"
