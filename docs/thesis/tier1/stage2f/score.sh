#!/bin/bash
# Stage 2f: score every completed E4 run (after the last job only; reads bags). Never overwrites a score file.
set -u
S=/home/makerspace/thesis_data/tier1/stage2f; cd /home/makerspace/thesis_ws
for j in $(cat $S/order.txt); do
  grep -qP "^$j\t.*\tcompleted\$" $S/timing.tsv || { echo "$j not completed: not scored"; continue; }
  t=$(echo $j | sed -E 's/^e4_(T_[A-D]_r[0-9])_.*/\1/'); rest=${j#e4_${t}_}
  out=docs/thesis/tier1/scores/E4_${t}_${rest}.json
  [ -e $out ] && { echo "$j already scored"; continue; }
  ~/venv-tags/bin/python eval/tag_score.py $t --in-root ~/thesis_data/tier1 --fgo-subdir room_fgo_${rest} --json $out > $S/score_logs/E4_${t}_${rest}.log 2>&1
  echo "$j rc=$?"
done
