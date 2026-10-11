#!/bin/bash
# One Replay run (one heavy step): run_one.sh <outdir> <replay-binary> <log.bin> [ENV=VAL ...]
# Replay writes ukf_shadow.csv / ukf_inputs.csv (+ ukf_geometry.csv / ukf_derot.csv in the new build) into <outdir>.
# Its own replayed dataflash (logs/) is deleted afterwards. The input log is only read.
set -e
OUT=$1; BIN=$2; LOG=$3; shift 3
mkdir -p "$OUT"
cd "$OUT"
md5sum "$BIN" > binary.md5
echo "$@" > env.txt
env "$@" timeout 1800 "$BIN" "$LOG" > replay.log 2>&1 || echo "replay rc=$?" >> replay.log
rm -rf logs
wc -l ukf_shadow.csv ukf_inputs.csv | tr '\n' ' '; echo
