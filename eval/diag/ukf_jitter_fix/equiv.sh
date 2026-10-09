#!/bin/bash
# UKF jitter fix: (1) C++ free-inertial; (2) step-2 dsn_tex_r2 E1-E5; (3) tier A H_s1_r1 UA1-UA5 (+ D27 diagnostic).
# Fixed Python core = this worktree; fixed port = the scratch worktree build. Nothing under ~/thesis_data is written.
set -e
J=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix
WT=/home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4
EQ=$J/apukf/build/sitl/examples/UKF_Equiv
PY=/home/makerspace/venv-evo/bin/python3
md5sum $EQ
# (1) C++ free inertial
cd $J
for c in 60_A 60_C 10_B; do
  UKF_EQ_IN=cfi$c.bin UKF_EQ_OUT=cfi${c}_state.bin UKF_EQ_PDIAG=cfi$c.pdiag $EQ | tail -1
done
# (2) step 2, dsn_tex_r2, under a FAKE HOME holding REAL files only (no symlinks)
FH=$J/home
T=/home/makerspace/thesis_data/trials/dsn_tex_r2
mkdir -p $FH/thesis_data/trials/dsn_tex_r2/bag $FH/thesis_ws/src/optical_flow_interfaces/msg $J/s2
cp $WT/src/optical_flow_interfaces/msg/OpticalFlow.msg $FH/thesis_ws/src/optical_flow_interfaces/msg/
cp $T/bag/metadata.yaml $FH/thesis_data/trials/dsn_tex_r2/bag/
[ -e $FH/thesis_data/trials/dsn_tex_r2/bag/bag_0.db3 ] || zstd -q -d $T/bag/bag_0.db3.zst -o $FH/thesis_data/trials/dsn_tex_r2/bag/bag_0.db3
cp $T/imu_gaps.json $FH/thesis_data/trials/dsn_tex_r2/
cd $WT
HOME=$FH $PY eval/ukf_event_export.py dsn_tex_r2 $J/s2/dsn_tex_r2 > $J/s2/export.log 2>&1
tail -3 $J/s2/export.log
cd $J/s2
UKF_EQ_IN=dsn_tex_r2.bin UKF_EQ_OUT=dsn_tex_r2_port.bin $EQ | tail -1
cd $WT
HOME=$FH $PY eval/ukf_equivalence.py $J/s2/dsn_tex_r2 --log tex --json $J/s2/equiv_dsn_tex_r2.json > $J/s2/equiv.log 2>&1 || true
cat $J/s2/equiv.log
rm -f $FH/thesis_data/trials/dsn_tex_r2/bag/bag_0.db3
# (3) tier A, H_s1_r1
mkdir -p $J/ua
cd $WT
ROOM_TAG_SIGMA_POS=0.02 $PY eval/ukf_tag_event_export.py H_s1_r1 $J/ua/h_s1_r1 > $J/ua/export.log 2>&1
tail -3 $J/ua/export.log
cd $J/ua
UKF_EQ_IN=h_s1_r1.bin UKF_EQ_OUT=h_s1_r1_port.bin $EQ | tail -1
cp h_s1_r1.npz h_s1_r1_d27.npz
UKF_EQ_QDIAG=h_s1_r1.qdiag UKF_EQ_IN=h_s1_r1.bin UKF_EQ_OUT=h_s1_r1_d27_port.bin $EQ | tail -2
cd $WT
$PY eval/ukf_tag_equivalence.py $J/ua/h_s1_r1 --json $J/ua/tierA.json > $J/ua/tierA.log 2>&1 || true
$PY eval/ukf_tag_equivalence.py $J/ua/h_s1_r1_d27 --json $J/ua/tierA_d27.json > $J/ua/tierA_d27.log 2>&1 || true
cat $J/ua/tierA.log $J/ua/tierA_d27.log
# remove the symlinks the tier-A export made in its scratch trial dir
rm -f $J/ua/h_s1_r1_trial/bag $J/ua/h_s1_r1_trial/imu_gaps.json
echo DONE
