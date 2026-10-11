#!/usr/bin/env python3
"""(a) byte-identity table, old vs each new variant, plus the size of any difference in ukf_shadow.csv."""
import filecmp, json, os, sys
import numpy as np
R = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/r1ukf/a"
out = {}
for L in ["dsn_tex_r1", "fwdplainc_tex_r1", "cl_a_tex_half", "cl_ukf_b_tex_r1_half_v2", "H_s2v2_r1"]:
    o = os.path.join(R, L, "old")
    out[L] = {}
    for V in ["new", "geomsitl", "derotrofh", "both"]:
        n = os.path.join(R, L, V)
        row = {}
        for f in ["ukf_shadow.csv", "ukf_inputs.csv"]:
            row[f] = filecmp.cmp(os.path.join(o, f), os.path.join(n, f), shallow=False)
        if not row["ukf_shadow.csv"]:
            a = np.genfromtxt(os.path.join(o, "ukf_shadow.csv"), delimiter=",", names=True)
            b = np.genfromtxt(os.path.join(n, "ukf_shadow.csv"), delimiter=",", names=True)
            same_t = bool(np.array_equal(a["TimeUS"], b["TimeUS"]))
            d3 = np.sqrt((a["PN"] - b["PN"]) ** 2 + (a["PE"] - b["PE"]) ** 2 + (a["PD"] - b["PD"]) ** 2)
            dy = (a["Yaw"] - b["Yaw"] + 180) % 360 - 180
            cols = [c for c in a.dtype.names if not np.array_equal(a[c], b[c])]
            first = int(np.argmax(np.any(np.stack([a[c] != b[c] for c in cols], 1), 1)))
            row["shadow_diff"] = {"same_TimeUS": same_t, "cols_differing": cols,
                                  "first_diff_t_s": float(a["TimeUS"][first] / 1e6),
                                  "pos3d_max_m": float(d3.max()), "pos3d_final_m": float(d3[-1]),
                                  "yaw_max_deg": float(abs(dy).max()),
                                  "acc_counts_old_new": [[int(a[c][-1]), int(b[c][-1])] for c in ("FXa", "FYa", "Ra")]}
        g = os.path.join(n, "ukf_geometry.csv")
        row["geometry"] = open(g).read().strip().splitlines() if os.path.exists(g) else None
        d = os.path.join(n, "ukf_derot.csv")
        if os.path.exists(d):
            lines = open(d).read().splitlines()
            rules = [l.split(",")[2] for l in lines if l.startswith("F,")]
            row["derot_rule_counts"] = {"as_delivered": rules.count("0"), "own_bias_swap": rules.count("1")}
            row["derot_other_lines"] = [l for l in lines if not l.startswith("F,")][:5]
            sw = np.array([[float(x) for x in l.split(",")[3:9]] for l in lines if l.startswith("F,") and l.split(",")[2] == "1"])
            if len(sw):
                dd = sw[:, :2] - sw[:, 3:5]
                row["swap_bias_diff_xy_rad_s"] = {"rms": float(np.sqrt((dd ** 2).mean())), "max": float(abs(dd).max())}
        out[L][V] = row
print(json.dumps(out, indent=1))
json.dump(out, open(os.path.join(R, "..", "a_compare.json"), "w"), indent=1)
