#!/bin/bash
# Decompress scratch COPIES of the packed bags (read-only on the trial directories).
SC=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/pw
set -e
for b in fwdplainc_tex_r1 fwdplainc_trans_r1 fwdc_tex_r1 fwdplainc_tex_r2 fwdplainc_tex_r3 fwdplainc_trans_r2 fwdplainc_trans_r3 fwdplainc_blank_r1; do
  d=$SC/bags/$b; mkdir -p $d
  cp ~/thesis_data/trials/$b/bag/metadata.yaml $d/
  [ -s $d/bag_0.db3 ] || zstd -d -q -T2 ~/thesis_data/trials/$b/bag/bag_0.db3.zst -o $d/bag_0.db3
  echo "$b $(stat -c %s $d/bag_0.db3)"
done
echo UNPACKED
