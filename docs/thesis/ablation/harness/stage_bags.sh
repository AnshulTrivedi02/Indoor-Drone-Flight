#!/bin/bash
# Stage decompressed COPIES of the 6 packed input bags (read-only source ~/thesis_data/trials/<t>/bag/) into
# ~/thesis_data/ablation/bags/<t>/ for FGO_BAG_ROOT (decisions_log D43). sha256 checked against PACKED.txt.
set -eu
B=/home/makerspace/thesis_data/ablation/bags; TD=/home/makerspace/thesis_data/trials
for t in fwdc_tex_r1 fwdc_tex_r2 fwdc_tex_r3 fwdplainc_tex_r1 fwdplainc_tex_r2 fwdplainc_tex_r3; do
  mkdir -p $B/$t
  if [ ! -f $B/$t/VERIFIED ]; then
    cp $TD/$t/bag/metadata.yaml $B/$t/metadata.yaml
    zstd -q -d -c $TD/$t/bag/bag_0.db3.zst > $B/$t/bag_0.db3.part
    want=$(awk '/^sha256/{print $2}' $TD/$t/bag/PACKED.txt); got=$(sha256sum $B/$t/bag_0.db3.part | cut -d' ' -f1)
    [ "$want" = "$got" ] || { echo "SHA MISMATCH $t"; exit 2; }
    mv $B/$t/bag_0.db3.part $B/$t/bag_0.db3; echo "$got $(date -Iseconds)" > $B/$t/VERIFIED
  fi
  echo "$t $(cat $B/$t/VERIFIED)"
done
