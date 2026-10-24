"""Write order.txt and one job script per run. Refuses if any job script or output dir already exists non-empty."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rungs import *
LOCK = "$(date -d '2026-11-04T23:59:00+11:00' +%s)"
js = jobs()
open(f"{A}/order.txt", "w").write("\n".join(js) + "\n")
for j in js:
    if j == "GATE":
        continue
    r, t, arm, d = parse(j)
    folder, W, cap, _, env = RUNGS[r]
    root = f"{A}/{folder}"
    assert d.startswith(A + "/") and not d.startswith(TR), d
    assert d == os.path.join(root, t, "fgo_" + arm + (f"_{env['F_TAG']}" if env else "")), d
    if os.path.isdir(d) and os.listdir(d):
        sys.exit(f"REFUSE: {d} exists and is non-empty")
    envs = " ".join(f"{k}={v}" for k, v in env.items())
    p = f"{A}/jobs/{j}.sh"
    open(p, "w").write(f"""#!/bin/bash
# ablation job {j} (pre-registration §3). Output: {d}
LOCK={LOCK}; NOW=$(date +%s); REM=$((LOCK-NOW))
if [ $REM -le 0 ]; then echo "[job] past the lock: NOT RUN"; exit 99; fi
TO=$(( REM < 172800 ? REM : 172800 ))
D={d}
if [ -d "$D" ] && [ -n "$(ls -A "$D")" ]; then echo "[job] REFUSE: $D non-empty"; exit 98; fi
cd /home/makerspace/thesis_ws || exit 97
export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 FGO_OUT_ROOT={root} {envs}
echo "[job] {j} start $(date -Iseconds) timeout ${{TO}}s OMP=$OMP_NUM_THREADS OPENBLAS=$OPENBLAS_NUM_THREADS nice=$(nice) FGO_OUT_ROOT=$FGO_OUT_ROOT F_TAG=${{F_TAG:-}} F_ROBUST=${{F_ROBUST:-}}"
exec timeout $TO /home/makerspace/venv-fgo/bin/python src/estimators/fgo/fgo_replay.py {t} {W} {cap} {arm}
""")
    os.chmod(p, 0o755)
print(len(js), "entries;", len([j for j in js if j != "GATE"]), "jobs")
