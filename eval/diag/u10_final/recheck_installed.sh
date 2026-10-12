#!/bin/bash
# U10 rule 2: re-check on the INSTALLED binaries (~/ardupilot_ukf build, ukf-jitter-fix = replay-rukx f30f6ffa2f):
# the 5-log Replay (CSV byte-identity against e82c050b), the log checks, replay_gate + scorer, UKF_Equiv.
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
D=/home/makerspace/thesis_ws/.claude/worktrees/agent-a5e6fd9bcc14a040c/eval/diag/u10_final
bash $D/driver.sh /home/makerspace/ardupilot_ukf/build/sitl/tool/Replay inst
bash $D/check_all.sh inst
bash $D/score_all.sh inst
python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py --wait-s 3600 "U10 rule-2 UKF_Equiv installed check" -- bash $S/s12/equiv_inst.sh /home/makerspace/ardupilot_ukf/build/sitl/examples/UKF_Equiv u10inst | grep RESULT
echo RECHECK_DONE
