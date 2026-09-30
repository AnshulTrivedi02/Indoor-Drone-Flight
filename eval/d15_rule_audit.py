#!/usr/bin/env python3
"""D15 per-bag audit: did the ground-proximity rule fire in every UKF/FGO replay of the re-run?
Parses the "[ground-proximity]" line of each replay log under ~/thesis_data/batches/{eval_*,d15_*}.
FLAGS: no line (the rule was not in the code that ran); take-off never detected; arm time missing;
0 flows replaced (expected only where no valid flow reaches the estimator before take-off, e.g. blank).
Usage: python3 eval/d15_rule_audit.py [--since ISO] [--json OUT]"""
import argparse, glob, json, os, re
ap = argparse.ArgumentParser(); ap.add_argument("--since", default="2026-09-30T13:18"); ap.add_argument("--json"); a = ap.parse_args()
import datetime as dt
since = dt.datetime.fromisoformat(a.since).timestamp()
B = os.path.expanduser("~/thesis_data/batches")
pat = re.compile(r"\[ground-proximity\] flows replaced (\d+); take-off detected (\w+) at t (\S+); arm t (\S+)")
rows, flags = [], []
logs = glob.glob(f"{B}/eval_*/*.log") + glob.glob(f"{B}/d15_*/logs/*.log")
for p in sorted(logs):
    if os.path.getmtime(p) < since:
        continue
    base = os.path.basename(p)
    if not re.match(r"(ukf|fgo)", base, re.I) and "5b" not in p:
        continue
    txt = open(p, errors="replace").read()
    ms = pat.findall(txt)
    name = os.path.relpath(p, B)
    if not ms:
        flags.append((name, "NO RULE LINE")); continue
    for n, tk, tt, ta in ms:
        r = {"log": name, "n_replaced": int(n), "takeoff": tk == "True", "t_takeoff": None if tt == "None" else float(tt),
             "t_arm": None if ta == "None" else float(ta)}
        rows.append(r)
        if r["t_arm"] is None: flags.append((name, "ARM TIME MISSING"))
        if not r["takeoff"]: flags.append((name, "TAKE-OFF NEVER DETECTED"))
        if r["n_replaced"] == 0: flags.append((name, "0 REPLACED"))
print(f"{len(rows)} replay records")
for r in rows:
    print(f"  {r['log']:60s} replaced {r['n_replaced']:5d}  take-off {r['t_takeoff']}  arm {r['t_arm']}")
print("FLAGS:" if flags else "no flags")
for f in flags:
    print("  ", *f)
if a.json:
    json.dump({"rows": rows, "flags": flags}, open(a.json, "w"), indent=1)
