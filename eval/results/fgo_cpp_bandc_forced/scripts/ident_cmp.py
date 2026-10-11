"""Switch-OFF byte-identity (ruling 2026-10-11 item 1): compare every output of the switch-OFF build (out/<tag>/) with
the 2d build's outputs (node 28636bf9 / replay 0981e455; d18/dump). Wall-clock timing is excluded: *.step_ns.i64,
*.stdout, the step-time fields of *.info.json, and column 4 (step_ns) of L1.live.f64 (t_k, valid, sent, t_us, step_ns,
arrival index). Usage: ident_cmp.py <new_dir> <ref_dump_dir>"""
import json, os, sys
import numpy as np

new, ref = sys.argv[1], sys.argv[2]
ok = True
for f in sorted(os.listdir(new)):
    if f.endswith((".step_ns.i64", ".stdout")):
        continue
    a, b = os.path.join(new, f), os.path.join(ref, f)
    if not os.path.exists(b):
        print(f"MISSING-REF {f}"); ok = False; continue
    if f.endswith(".info.json"):
        ja, jb = json.load(open(a)), json.load(open(b))
        keys = sorted(set(ja) | set(jb))
        timing = [k for k in keys if k == "batch_s" or "step" in k]   # batch_s = wall-clock batch duration
        diff = [k for k in keys if k not in timing and ja.get(k) != jb.get(k)]
        print(f"{'IDENTICAL' if not diff else 'DIFFER'} {f} (non-timing keys; timing keys excluded: {timing})"
              + (f" differ: {diff}" if diff else ""))
        ok &= not diff
        continue
    if f == "L1.live.f64":
        x, y = np.fromfile(a).reshape(-1, 6), np.fromfile(b).reshape(-1, 6)
        same = x.shape == y.shape and np.array_equal(np.delete(x, 4, 1), np.delete(y, 4, 1))
        print(f"{'IDENTICAL' if same else 'DIFFER'} {f} (all columns except step_ns; rows {len(x)})")
        ok &= same
        continue
    same = open(a, "rb").read() == open(b, "rb").read()
    print(f"{'IDENTICAL' if same else 'DIFFER'} {f} ({os.path.getsize(a)} B)")
    ok &= same
print("ALL BYTE-IDENTICAL" if ok else "NOT ALL IDENTICAL")
sys.exit(0 if ok else 1)
