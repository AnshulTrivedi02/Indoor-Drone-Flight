#!/bin/bash
# One Replay run (one heavy step): run_one_keep.sh <outdir> <replay-binary> <log.bin> [ENV=VAL ...]
# As r1ukf/run_one.sh, but the replayed dataflash (logs/) is KEPT (the XUKO / FMT checks read it). Input only read.
set -e
OUT=$1; BIN=$2; LOG=$3; shift 3
mkdir -p "$OUT"
cd "$OUT"
md5sum "$BIN" > binary.md5
echo "$@" > env.txt
env "$@" timeout 1800 "$BIN" "$LOG" > replay.log 2>&1 || echo "replay rc=$?" >> replay.log
ls -la logs > logs_ls.txt 2>&1 || true
wc -l ukf_shadow.csv ukf_inputs.csv | tr '\n' ' '; echo
