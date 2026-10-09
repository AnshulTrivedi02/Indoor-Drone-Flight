#!/usr/bin/env python3
"""Final consolidated re-run: merge the regenerated blank-behaviour outputs into eval/results/blank_behaviour.json.
eval/d27_regen.sh replaced ONLY the ukf* fields (the FGO was unchanged then). In the final re-run both the UKF and the FGO
change, so every ukf* AND fgo* field is replaced; every other field (EKF3 flags, flow counts, windows, loss times) must be
IDENTICAL to the snapshot, else exit 1 (the EKF3-unchanged rule). Trials present only in the old file are kept as they
were and listed.
Usage: final_rerun_merge_bb.py OLD_JSON NEW_PLAIN_JSON NEW_ARMS_JSON OUT_JSON"""
import json, sys

old_p, plain_p, arms_p, out_p = sys.argv[1:5]
old = json.load(open(old_p)); new = {**json.load(open(plain_p))}
for t, d in json.load(open(arms_p)).items():
    new.setdefault(t, {}).update(d)
out = json.loads(json.dumps(old)); bad = []
for t, d in new.items():
    if t not in out:
        bad.append(f"trial {t} not in the snapshot"); continue
    for k, v in d.items():
        if k.startswith(("ukf", "fgo")):
            out[t][k] = v
        elif json.dumps(v, sort_keys=True) != json.dumps(old[t].get(k), sort_keys=True):
            bad.append(f"NON-UKF/FGO FIELD DIFFERS: {t}.{k}")
for t in sorted(set(old) - set(new)):
    print(f"kept from the snapshot (not regenerated): {t}")
for b in bad:
    print(b)
if bad:
    sys.exit(1)
json.dump(out, open(out_p, "w"), indent=1)
print(f"merged {len(new)} trials; all non-UKF/FGO fields identical")
