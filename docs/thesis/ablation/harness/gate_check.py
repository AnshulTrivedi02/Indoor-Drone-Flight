"""Identity gate (pre-registration §9; user edit 2026-10-24): r0 fgo_traj.tum byte-identical to the stored
~/thesis_data/trials/<t>/fgo_<arm>/fgo_traj.tum on 12/12 bags. Exit 0 iff 12/12. Other files reported, not gated."""
import filecmp, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rungs import *
res, ok = {}, 0
for arm in ("heading", "baseline"):
    for t in BAGS:
        new = os.path.join(A, RUNGS["r0"][0], t, f"fgo_{arm}"); old = os.path.join(TR, t, f"fgo_{arm}")
        e = {}
        for f in ("fgo_traj.tum", "ground_truth.tum", "bgz_series.txt", "fwd_stats.json"):
            a, b = os.path.join(new, f), os.path.join(old, f)
            e[f] = (os.path.exists(a) and os.path.exists(b) and filecmp.cmp(a, b, shallow=False))
        res[f"{t}.{arm}"] = e; ok += e["fgo_traj.tum"]
        print(f"{t:18} {arm:9} " + " ".join(f"{k}={'IDENTICAL' if v else 'DIFFERENT'}" for k, v in e.items()))
v = "PASS" if ok == 12 else "FAIL"
print(f"[gate] fgo_traj.tum byte-identical {ok}/12: {v}")
json.dump({"gate": "r0 byte identity of fgo_traj.tum vs stored", "checked_local": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "n_identical": ok, "n": 12, "verdict": v, "files": res}, open(f"{A}/gate.json", "w"), indent=1)
sys.exit(0 if ok == 12 else 1)
