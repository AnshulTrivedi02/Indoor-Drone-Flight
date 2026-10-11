#!/bin/bash
# 2026-10-12: the INSTALLED UKF_Equiv (built from ukf-jitter-fix = rung1-geometry 16535f9a29) on the stored 2026-10-09
# tapes (copies in r1ukf/c); every output must equal the stored outputs of the old installed build (537e0dcd, *_old).
# Usage: equiv_inst.sh [<UKF_Equiv binary>] [<tag>]   (default: the installed binary, tag inst)
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
C=$S/r1ukf/c
B=${1:-/home/makerspace/ardupilot_ukf/build/sitl/examples/UKF_Equiv}
V=${2:-inst}
O=$S/s12/equiv_$V
mkdir -p $O; cd $O
md5sum $B
for c in cfi60_A cfi60_C cfi10_B; do
  UKF_EQ_IN=$C/$c.bin UKF_EQ_OUT=${c}_$V.state UKF_EQ_PDIAG=${c}_$V.pdiag $B | tail -1
done
UKF_EQ_IN=$C/dsn_tex_r2.bin UKF_EQ_OUT=dsn_tex_r2_$V.state $B | tail -1
UKF_EQ_QDIAG=$C/dsn_tex_r2.qdiag UKF_EQ_IN=$C/dsn_tex_r2.bin UKF_EQ_OUT=dsn_tex_r2_q_$V.state $B | tail -1
UKF_EQ_IN=$C/h_s1_r1.bin UKF_EQ_OUT=h_s1_r1_$V.state $B | tail -1
UKF_EQ_QDIAG=$C/h_s1_r1.qdiag UKF_EQ_IN=$C/h_s1_r1.bin UKF_EQ_OUT=h_s1_r1_q_$V.state $B | tail -1
for f in cfi60_A cfi60_C cfi10_B; do
  cmp -s $C/${f}_old.state ${f}_$V.state && echo "RESULT $f state IDENTICAL" || echo "RESULT $f state DIFFERS"
  cmp -s $C/${f}_old.pdiag ${f}_$V.pdiag && echo "RESULT $f pdiag IDENTICAL" || echo "RESULT $f pdiag DIFFERS"
done
for f in dsn_tex_r2 dsn_tex_r2_q h_s1_r1 h_s1_r1_q; do
  cmp -s $C/${f}_old.state ${f}_$V.state && echo "RESULT $f state IDENTICAL" || echo "RESULT $f state DIFFERS"
done
echo EQUIV_DONE
