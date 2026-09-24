#!/usr/bin/env bash
# Evaluate one recorded trial set end to end, exactly as Phase 2 was evaluated.
#
# Usage: eval/run_set_eval.sh <tag> TRIAL [TRIAL...]
#
# Steps (each output goes to eval/results/*_<tag>.json, logs to
# ~/thesis_data/batches/eval_<tag>/):
#   1. eval/imu_gap_check.py --write   IMU-gap rule verdict per bag (ok / trim / unusable)
#   2. UKF (venv-evo) + FGO (venv-fgo, window 0.25 s) replays, 4 at a time, for every bag
#      that is not "unusable" (the replays apply the trim themselves)
#   3. eval/input_timing.py, eval/flow_quality.py
#   4. eval/three_way_eval.py: all estimators on replayable bags; EKF3 only on unusable
#      bags, whose cruise window comes from eval/extract_gt_tum.py
#   5. merged evo JSON, then eval/phase2_score.py with the pre-registered bands
# Run it only when no trial is flying: the replays load the CPU, which is the confound
# the Phase 1 checks measure.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
[ $# -ge 2 ] || { echo "Usage: $0 <tag> TRIAL [TRIAL...]" >&2; exit 1; }
TAG="$1"; shift; TRIALS=("$@")
LOGD="$HOME/thesis_data/batches/eval_$TAG"; mkdir -p "$LOGD"
TD="$HOME/thesis_data/trials"; RES=eval/results
EVO="$HOME/venv-evo/bin/python"; FGO="$HOME/venv-fgo/bin/python"; AP="$HOME/venv-ardupilot/bin/python"

echo "[1/5] IMU-gap rule"
"$EVO" eval/imu_gap_check.py "${TRIALS[@]}" --write > "$LOGD/imu_gaps.jsonl" || exit 1
declare -a OK=() BAD=()
for t in "${TRIALS[@]}"; do
    v=$(python3 -c "import json;print(json.load(open('$TD/$t/imu_gaps.json'))['verdict'])")
    echo "  $t: $v"
    if [ "$v" = unusable ]; then BAD+=("$t"); else OK+=("$t"); fi
done

echo "[2/5] replays (${#OK[@]} bags)"
: > "$LOGD/jobs.txt"
for t in "${OK[@]}"; do
    echo "$EVO src/estimators/ukf_replay.py $t > $LOGD/ukf_$t.log 2>&1; echo rc=\$? >> $LOGD/ukf_$t.log" >> "$LOGD/jobs.txt"
    echo "$FGO src/estimators/fgo/fgo_replay.py $t 0.25 > $LOGD/fgo_$t.log 2>&1; echo rc=\$? >> $LOGD/fgo_$t.log" >> "$LOGD/jobs.txt"
done
[ "${#OK[@]}" -gt 0 ] && xargs -P 4 -I{} bash -c '{}' < "$LOGD/jobs.txt"
if grep -L "rc=0" "$LOGD"/ukf_*.log "$LOGD"/fgo_*.log 2>/dev/null | grep -q .; then
    echo "ERROR: a replay failed:"; grep -L "rc=0" "$LOGD"/ukf_*.log "$LOGD"/fgo_*.log; exit 1
fi

echo "[3/5] input timing, flow quality"
"$EVO" eval/input_timing.py "${TRIALS[@]}" --json "$RES/input_timing_$TAG.json" > "$LOGD/input_timing.txt" 2>&1 || exit 1
"$EVO" eval/flow_quality.py "${TRIALS[@]}" --json "$RES/flow_quality_$TAG.json" > "$LOGD/flow_quality.txt" 2>&1 || exit 1

echo "[4/5] three-way evaluation"
parts=()
if [ "${#OK[@]}" -gt 0 ]; then
    "$AP" eval/three_way_eval.py "${OK[@]}" --json "$LOGD/evo_ok.json" > "$LOGD/three_way_ok.txt" 2>&1 || exit 1
    parts+=("$LOGD/evo_ok.json")
fi
for t in "${BAD[@]}"; do
    "$EVO" eval/extract_gt_tum.py "$t" > /dev/null || exit 1
    "$AP" eval/three_way_eval.py "$t" --only EKF3 --json "$LOGD/evo_$t.json" > "$LOGD/three_way_$t.txt" 2>&1 || exit 1
    parts+=("$LOGD/evo_$t.json")
done
python3 - "$RES/${TAG}_evo.json" "${parts[@]}" <<'PYEOF' || exit 1
import json, sys
out = None
for p in sys.argv[2:]:
    d = json.load(open(p))
    if out is None:
        out = d
    else:
        assert d["window_def"] == out["window_def"], "window definitions differ"
        out["trials"].update(d["trials"])
json.dump(out, open(sys.argv[1], "w"), indent=1)
PYEOF

echo "[5/5] score"
python3 eval/phase2_score.py --trials "$(IFS=,; echo "${TRIALS[*]},")" \
    --timing "input_timing_$TAG.json" --flow "flow_quality_$TAG.json" --evo "${TAG}_evo.json" \
    --json "$RES/${TAG}_score.json" | tee "$LOGD/score.txt"
