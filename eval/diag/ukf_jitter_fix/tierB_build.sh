#!/bin/sh
# Rebuild Replay from the COMMITTED ukf-jitter-fix (abb0357d0f) in a fresh scratch worktree.
set -e
J=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix
git -C /home/makerspace/ardupilot_ukf worktree add --detach $J/apukf ukf-jitter-fix
git -C $J/apukf log --oneline -1
sh $J/copymods.sh
cd $J/apukf
./waf configure --board sitl --no-submodule-update
./waf replay
./waf build --target examples/UKF_Equiv
md5sum build/sitl/tool/Replay build/sitl/examples/UKF_Equiv
# functional check of the committed UKF_Equiv against the tested one (free-inertial case A diag(P), byte compare)
cd $J
UKF_EQ_IN=cfi60_A.bin UKF_EQ_OUT=cfi60_A_commit_state.bin UKF_EQ_PDIAG=cfi60_A_commit.pdiag $J/apukf/build/sitl/examples/UKF_Equiv | tail -1
cmp cfi60_A.pdiag cfi60_A_commit.pdiag && echo "PDIAG byte-identical (committed build == tested build)"
cmp cfi60_A_state.bin cfi60_A_commit_state.bin && echo "STATE byte-identical"
