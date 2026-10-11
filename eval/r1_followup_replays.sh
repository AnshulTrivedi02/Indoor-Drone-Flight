#!/bin/bash
# R1 follow-up (docs/handovers/2026-10-10_r1_converter.md): the two LIGHT single replays the R1 stage could not run
# because BUILD_LOCK was held for hours. Run each under the lock protocol, from the thesis_ws checkout that holds R1:
#
#   python3 src/estimators/fgo_cpp/tools/heavy.py "R1 default-unchanged replay" -- bash eval/r1_followup_replays.sh default <scratch>
#   python3 src/estimators/fgo_cpp/tools/heavy.py "R1 events-mode smoke"       -- bash eval/r1_followup_replays.sh smoke   <scratch>
#
# default: ONE default (bag-mode) FGO replay of cl_a_tex_half with args "0.25 2" (as batches/fgo_half_pred.jobs), bag
#          decompressed to <scratch> (the stored bag_0.db3.zst is read only, never modified), outputs to <scratch>;
#          fgo_traj.tum is byte-compared with the stored ~/thesis_data/trials/cl_a_tex_half/fgo/fgo_traj.tum (final
#          re-run, 2026-10-10 02:05). If it DIFFERS, re-run with the base commit 3a2c3a8's fgo_replay/fgo_core/
#          factors/measurement_models before concluding (stored output vs code drift).
# smoke:   the events mode on the first 90 s (FC clock) of the same flight's dataflash (not a result; plumbing only).
set -eu
MODE=$1; S=$2
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
T=cl_a_tex_half; D=$HOME/thesis_data/trials/$T
mkdir -p "$S"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
if [ "$MODE" = default ]; then
  mkdir -p "$S/bags/$T"
  [ -f "$S/bags/$T/bag_0.db3" ] || nice -n 19 zstd -d -q "$D/bag/bag_0.db3.zst" -o "$S/bags/$T/bag_0.db3"
  cp "$D/bag/metadata.yaml" "$S/bags/$T/"
  grep -q "$(sha256sum "$S/bags/$T/bag_0.db3" | cut -c1-64)" "$D/bag/PACKED.txt" || { echo "decompressed bag sha256 mismatch"; exit 1; }
  FGO_BAG_ROOT=$S/bags FGO_OUT_ROOT=$S/replay_default nice -n 19 $HOME/venv-fgo/bin/python src/estimators/fgo/fgo_replay.py $T 0.25 2 \
    > "$S/replay_default.log" 2>&1
  for f in fgo_traj.tum ground_truth.tum bgz_series.txt; do
    cmp -s "$S/replay_default/$T/fgo/$f" "$D/fgo/$f" && echo "IDENTICAL $f" || echo "DIFFERS $f"
  done | tee -a "$S/replay_default.log"
  rm -f "$S/bags/$T/bag_0.db3"
elif [ "$MODE" = smoke ]; then
  nice -n 19 $HOME/venv-fgo/bin/python eval/bin2fgo.py "$D/ardupilot.bin" -o "$S/conv/${T}_smoke.npz" \
    --flow-delay-ms 16 --range-delay-ms 40 --truth sim2 --t-end 90 > "$S/conv_smoke.log"
  FGO_EVENTS=$S/conv/${T}_smoke.npz FGO_OUT_ROOT=$S/replay_events nice -n 19 $HOME/venv-fgo/bin/python \
    src/estimators/fgo/fgo_replay.py $T 0.25 2 > "$S/replay_events.log" 2>&1
  tail -12 "$S/replay_events.log"
else
  echo "mode: default | smoke"; exit 2
fi
