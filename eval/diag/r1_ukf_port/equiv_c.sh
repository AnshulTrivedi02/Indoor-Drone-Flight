#!/bin/bash
# (c) UKF_Equiv, old (installed, abb0357d0f, md5 537e0dcd; read-only use) vs new (scratch build), on the existing
# event tapes of the 2026-10-09 jitter-fix stage (copied, not modified). Output: byte comparison of every output file.
set -e
R=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/r1ukf/c
J=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix
OLD=/home/makerspace/ardupilot_ukf/build/sitl/examples/UKF_Equiv
NEW=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/apukf/build/sitl/examples/UKF_Equiv
mkdir -p $R; cd $R
cp $J/cfi60_A.bin $J/cfi60_C.bin $J/cfi10_B.bin $J/s2/dsn_tex_r2.bin $J/s2/dsn_tex_r2.qdiag $J/ua/h_s1_r1.bin $J/ua/h_s1_r1.qdiag .
md5sum $OLD $NEW
for V in old new; do
  B=$OLD; [ $V = new ] && B=$NEW
  for c in cfi60_A cfi60_C cfi10_B; do
    UKF_EQ_IN=$c.bin UKF_EQ_OUT=${c}_$V.state UKF_EQ_PDIAG=${c}_$V.pdiag $B | tail -1
  done
  UKF_EQ_IN=dsn_tex_r2.bin UKF_EQ_OUT=dsn_tex_r2_$V.state $B | tail -1
  UKF_EQ_QDIAG=dsn_tex_r2.qdiag UKF_EQ_IN=dsn_tex_r2.bin UKF_EQ_OUT=dsn_tex_r2_q_$V.state $B | tail -1
  UKF_EQ_IN=h_s1_r1.bin UKF_EQ_OUT=h_s1_r1_$V.state $B | tail -1
  UKF_EQ_QDIAG=h_s1_r1.qdiag UKF_EQ_IN=h_s1_r1.bin UKF_EQ_OUT=h_s1_r1_q_$V.state $B | tail -1
done
for f in cfi60_A cfi60_C cfi10_B; do
  cmp ${f}_old.state ${f}_new.state && echo "$f state IDENTICAL"
  cmp ${f}_old.pdiag ${f}_new.pdiag && echo "$f pdiag IDENTICAL"
done
for f in dsn_tex_r2 dsn_tex_r2_q h_s1_r1 h_s1_r1_q; do
  cmp ${f}_old.state ${f}_new.state && echo "$f state IDENTICAL"
done
cmp dsn_tex_r2_new.state $J/s2/dsn_tex_r2_port.bin && echo "dsn_tex_r2 new == stored 2026-10-09 port output"
cmp h_s1_r1_new.state $J/ua/h_s1_r1_port.bin && echo "h_s1_r1 new == stored 2026-10-09 port output"
echo EQUIV_DONE
