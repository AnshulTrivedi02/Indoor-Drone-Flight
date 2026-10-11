#!/bin/bash
# board-h743 (2a): (iii) UKF_Equiv byte-identity, new build vs the installed binary and the stored 2026-10-09 port outputs. One heavy.py step.
H=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
O=$H/h7/ident
# (iii) UKF_Equiv
J=$H/jfix; E=$O/equiv; mkdir -p $E; cd $E
OLD=/home/makerspace/ardupilot_ukf/build/sitl/examples/UKF_Equiv
NEWE=$H/aph7/build/sitl/examples/UKF_Equiv
cp $J/cfi60_A.bin $J/cfi60_C.bin $J/cfi10_B.bin $J/s2/dsn_tex_r2.bin $J/s2/dsn_tex_r2.qdiag $J/ua/h_s1_r1.bin $J/ua/h_s1_r1.qdiag .
md5sum $OLD $NEWE
for V in old new; do
  B=$OLD; [ $V = new ] && B=$NEWE
  for c in cfi60_A cfi60_C cfi10_B; do UKF_EQ_IN=$c.bin UKF_EQ_OUT=${c}_$V.state UKF_EQ_PDIAG=${c}_$V.pdiag $B | tail -1; done
  UKF_EQ_IN=dsn_tex_r2.bin UKF_EQ_OUT=dsn_tex_r2_$V.state $B | tail -1
  UKF_EQ_QDIAG=dsn_tex_r2.qdiag UKF_EQ_IN=dsn_tex_r2.bin UKF_EQ_OUT=dsn_tex_r2_q_$V.state $B | tail -1
  UKF_EQ_IN=h_s1_r1.bin UKF_EQ_OUT=h_s1_r1_$V.state $B | tail -1
  UKF_EQ_QDIAG=h_s1_r1.qdiag UKF_EQ_IN=h_s1_r1.bin UKF_EQ_OUT=h_s1_r1_q_$V.state $B | tail -1
done
for f in cfi60_A cfi60_C cfi10_B; do
  cmp ${f}_old.state ${f}_new.state && echo "equiv $f state IDENTICAL (new vs installed)"
  cmp ${f}_old.pdiag ${f}_new.pdiag && echo "equiv $f pdiag IDENTICAL (new vs installed)"
done
for f in dsn_tex_r2 dsn_tex_r2_q h_s1_r1 h_s1_r1_q; do
  cmp ${f}_old.state ${f}_new.state && echo "equiv $f state IDENTICAL (new vs installed)"
done
cmp dsn_tex_r2_new.state $J/s2/dsn_tex_r2_port.bin && echo "equiv dsn_tex_r2 new == stored 2026-10-09 port output"
cmp h_s1_r1_new.state $J/ua/h_s1_r1_port.bin && echo "equiv h_s1_r1 new == stored 2026-10-09 port output"
rm -f *.bin.tmp
echo IDENTITY_DONE
