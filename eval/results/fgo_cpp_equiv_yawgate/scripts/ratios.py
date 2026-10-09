"""Yaw (and tilt) VARIANCE ratios FGO / EKF3, FGO / UKF (offline, port), FGO / analytic at each checkpoint, from the
free-inertial JSONs (values there are 1-sigma; ratios here are of variances). Usage: ratios.py fi10.json fi60.json"""
import json, sys

def row(c, name, t, q):
    r = c.get(name)
    if r is None:
        return None
    e = r.get(str(int(t)))
    return None if e is None else e[q]

for f in sys.argv[1:]:
    d = json.load(open(f))
    for case, c in d["cases"].items():
        ts = sorted(int(k) for k in c["ekf3"])
        for q in ("yaw", "tilt"):
            for t in ts:
                fg = row(c, "fgo", t, q)
                out = []
                for ref in ("ekf3", "ukf_offline", "ukf_port", "analytic", "fgo_chain"):
                    v = row(c, ref, t, q)
                    out.append(f"/{ref} {fg**2 / v**2:.4f}" if (fg and v) else f"/{ref} -")
                ug = row(c, "fgo_ungated", t, q); e3 = row(c, "ekf3", t, q)
                ugs = f"  [ungated/ekf3 {ug**2 / e3**2:.4f}]" if ug else ""
                print(f"{f.split('/')[-1]:9s} case {case} {q:4s} t={t:5.0f}  fgo var " + "  ".join(out) + ugs)
