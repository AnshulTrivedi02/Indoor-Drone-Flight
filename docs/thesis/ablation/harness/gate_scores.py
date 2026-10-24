"""Gate part 2 (pre-registration §9): the r0 scores must equal the stored phase4 values exactly. Runs the read-only
scorer (docs/thesis/ablation/score_ablation.py) for r0 both arms, writing scores/r0_<arm>.json. Exit 0 iff 12/12."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rungs import *
REPO = "/home/makerspace/thesis_ws"
st = {ds: json.load(open(f"{REPO}/eval/results/phase4_{ds}_arms.json")) for ds in ("fwdc", "fwdplainc")}
ok = 0
for arm in ("heading", "baseline"):
    js = f"{A}/scores/r0_{arm}.json"
    assert not os.path.exists(js), js
    subprocess.run(["/home/makerspace/venv-ardupilot/bin/python", f"{REPO}/docs/thesis/ablation/score_ablation.py",
                    "--root", f"{A}/{RUNGS['r0'][0]}", "--sub", f"fgo_{arm}", "--json", js] + BAGS, check=True,
                   capture_output=True)
    sc = json.load(open(js))["trials"]
    for t in BAGS:
        a = sc[t]["ate_a_cruise_m"]; b = st[t.split("_")[0]][t][f"FGO_{arm}"]["evo"]["ate_a_cruise"]["+0.00"]
        ok += a == b
        print(f"{t:18} {arm:9} scored {a} stored {b} {'EQUAL' if a == b else 'DIFFERENT'}")
print(f"[gate-scores] {ok}/12 equal: {'PASS' if ok == 12 else 'FAIL'}")
sys.exit(0 if ok == 12 else 1)
