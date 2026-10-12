#!/bin/bash
# XUKO FMT (2026-10-12): re-check on the INSTALLED binaries (~/ardupilot_ukf build, ukf-jitter-fix = xuko-fmt 0a214d29d3):
# the 5-log CSV byte-identity against be7c4d18 (one heavy step per Replay), then UKF_Equiv on the stored tapes.
D=/home/makerspace/thesis_ws/.claude/worktrees/agent-a60b4a326e4fb1d35/eval/diag
bash $D/xuko_fmt/driver.sh /home/makerspace/ardupilot_ukf/build/sitl/tool/Replay inst
python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py --wait-s 3600 "xuko-fmt UKF_Equiv installed check" -- bash $D/port_merge_u4/equiv_inst.sh /home/makerspace/ardupilot_ukf/build/sitl/examples/UKF_Equiv xukoinst
echo RECHECK_DONE
