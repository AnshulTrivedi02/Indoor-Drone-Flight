#!/usr/bin/env python3
"""D27 (b): old (eval/results_preD27/) vs new (eval/results/) for every regenerated result. Every numeric or string
leaf is compared by its path. A path is a UKF path if any key on it contains "ukf" (any case); every change on a
NON-UKF path is FLAGGED (EKF3 and FGO numbers must be unchanged: their replays were not re-run). Writes a Markdown
table of the changed UKF leaves and the flags.
Usage: python3 eval/d27_compare.py [--md docs/thesis/d27_old_vs_new.md] [--json eval/results/d27_old_vs_new.json]"""
import argparse, glob, json, math, os
ap = argparse.ArgumentParser(); ap.add_argument("--md", default="docs/thesis/d27_old_vs_new.md")
ap.add_argument("--json", default="eval/results/d27_old_vs_new.json"); a = ap.parse_args()
def leaves(x, p=()):
    if isinstance(x, dict):
        for k, v in x.items(): yield from leaves(v, p + (str(k),))
    elif isinstance(x, list):
        for i, v in enumerate(x): yield from leaves(v, p + (str(i),))
    else:
        yield p, x
def same(u, v):
    if isinstance(u, float) and isinstance(v, float):
        return (math.isnan(u) and math.isnan(v)) or u == v
    return u == v
out = {}; md = ["# D27: old vs new (offline UKF process noise aligned)", ""]
for old_p in sorted(glob.glob("eval/results_preD27/*.json")):
    name = os.path.basename(old_p)[:-5]; new_p = f"eval/results/{name}.json"
    O = dict(leaves(json.load(open(old_p)))); N = dict(leaves(json.load(open(new_p))))
    ch, flags = [], []
    for k in sorted(set(O) | set(N), key=lambda k: "/".join(k)):
        u, v = O.get(k, "<absent>"), N.get(k, "<absent>")
        if same(u, v):
            continue
        is_ukf = any("ukf" in s.lower() for s in k)
        (ch if is_ukf else flags).append(("/".join(k), u, v))
    out[name] = {"ukf_changes": len(ch), "non_ukf_changes": len(flags), "changes": ch, "flags": flags}
    md += [f"## {name}: {len(ch)} UKF leaves changed; {len(flags)} NON-UKF leaves changed" + (" — FLAG" if flags else ""), ""]
    if ch:
        md += ["| path | old | new |", "|---|---|---|"] + [f"| `{k}` | {u} | {v} |" for k, u, v in ch[:400]] + [""]
    if flags:
        md += ["**Non-UKF changes:**", "", "| path | old | new |", "|---|---|---|"] + [f"| `{k}` | {u} | {v} |" for k, u, v in flags[:200]] + [""]
os.makedirs(os.path.dirname(a.md), exist_ok=True)
open(a.md, "w").write("\n".join(md) + "\n"); json.dump(out, open(a.json, "w"), indent=1, default=str)
for n, r in out.items():
    print(f"{n:28s} UKF changed {r['ukf_changes']:5d}   NON-UKF changed {r['non_ukf_changes']:4d}" + ("   <-- FLAG" if r["non_ukf_changes"] else ""))
