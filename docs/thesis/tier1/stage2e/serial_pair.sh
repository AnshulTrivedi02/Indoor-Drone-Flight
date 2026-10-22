#!/bin/bash
# Serial 0% runtime pair on T_A_r2 (user ruling R3, 2026-10-22): arm (a) as-is (extra, timing-only), then arm (b)
# control e3b_T_A_r2_0 (registered). Run inside ONE heavy.py call with nothing else running. Then cmp the arm (a)
# .tum files against the stored Experiment 3 output (read-only).
set -u; S=/home/makerspace/thesis_data/tier1/stage2e
A=/home/makerspace/thesis_data/tier1/T_A_r2/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7
E=/home/makerspace/thesis_data/trials/T_A_r2/lc_fgo_lc_t245
if [ -e "$A" ]; then echo "PAIR REFUSED: $A exists" >> $S/par_timing.tsv; exit 2; fi
case "$(realpath -m "$A")" in /home/makerspace/thesis_data/trials/*) echo "PAIR REFUSED: under trials" >> $S/par_timing.tsv; exit 2;; esac
bash $S/one_job.sh e3a_T_A_r2_0; rca=$?
for f in live.tum hindsight.tum; do
  if cmp -s "$A/$f" "$E/$f"; then r=IDENTICAL; else r=DIFFERENT; fi
  echo -e "e3a_T_A_r2_0 vs trials/T_A_r2/lc_fgo_lc_t245\t$f\t$r\t$(date -Iseconds)" >> $S/pair_cmp.txt
done
[ $rca -ne 0 ] && { echo "PAIRDONE rc=$rca (arm a)" >> $S/par_timing.tsv; exit $rca; }
bash $S/one_job.sh e3b_T_A_r2_0; rc=$?
echo "PAIRDONE rc=$rc" >> $S/par_timing.tsv; exit $rc
