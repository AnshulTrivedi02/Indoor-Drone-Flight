#!/bin/sh
# Model audit (DIAGNOSTIC): copy EKF3's generated covariance-prediction block verbatim and build the harness.
set -e
OUT=${1:?out dir}
SRC=$HOME/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_core.cpp
sed -n '1196,1748p' "$SRC" > "$OUT/ekf3_gen.inc"
head -1 "$OUT/ekf3_gen.inc" | grep -q 'intermediate calculations'
g++ -O2 -std=c++17 -I"$OUT" -o "$OUT/ekf3_cov_harness" "$(dirname "$0")/ekf3_cov_harness.cpp"
