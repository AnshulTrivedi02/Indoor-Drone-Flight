#!/usr/bin/env bash
# Evaluate a recorded trial's EKF pose estimate against ground truth using evo.
#
# Usage: ./evaluate_trial.sh <trial_name>
#
# Runs evo_ape and evo_rpe (translation-part ATE/RPE) plus an evo_traj
# comparison, reading directly from the trial's ROS2 bag via evo's bag2
# reader (the pure-Python rosbags library — no ROS install needed for this
# step, and no manual TUM conversion). Both /ground_truth/pose and
# /ekf/pose are plain geometry_msgs/PoseStamped, already in the same
# frame (ENU/FLU) — see CLAUDE.md, "EKF State Estimate — Stage B" for the
# NED->ENU / FRD->FLU transform applied by ekf_bridge.py.
#
# Output: ~/thesis_data/trials/<trial_name>/evo/
#   ape_plot.pdf, ape_results.zip   — absolute pose error (ATE)
#   rpe_plot.pdf, rpe_results.zip   — relative pose error (RPE)
#   traj_plot.pdf                  — trajectory comparison (position/orientation/speed vs time)

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <trial_name>" >&2
    exit 1
fi

TRIAL_NAME="$1"
TRIAL_DIR="$HOME/thesis_data/trials/$TRIAL_NAME"
BAG_DIR="$TRIAL_DIR/bag"
OUT_DIR="$TRIAL_DIR/evo"

if [ ! -d "$BAG_DIR" ]; then
    echo "ERROR: Bag not found: $BAG_DIR" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"

set +u
source "$HOME/venv-evo/bin/activate"
set -u

echo "Evaluating trial '$TRIAL_NAME' -> $OUT_DIR"
echo ""

echo "--- evo_ape (absolute pose error / ATE) ---"
evo_ape bag2 "$BAG_DIR" /ground_truth/pose /ekf/pose \
    -a --no_warnings \
    --save_plot "$OUT_DIR/ape_plot.pdf" \
    --save_results "$OUT_DIR/ape_results.zip"

echo ""
echo "--- evo_rpe (relative pose error / RPE) ---"
evo_rpe bag2 "$BAG_DIR" /ground_truth/pose /ekf/pose \
    -a --no_warnings \
    --save_plot "$OUT_DIR/rpe_plot.pdf" \
    --save_results "$OUT_DIR/rpe_results.zip"

echo ""
echo "--- evo_traj (trajectory comparison) ---"
evo_traj bag2 "$BAG_DIR" /ground_truth/pose /ekf/pose \
    --ref=/ground_truth/pose \
    -a --plot_mode=xy --no_warnings \
    --save_plot "$OUT_DIR/traj_plot.pdf"

echo ""
echo "Evaluation complete. Results in $OUT_DIR"
