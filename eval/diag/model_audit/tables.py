"""Model audit (2026-10-09), DIAGNOSTIC: markdown tables from free_inertial.py outputs (variance ratios, flag > 2x).
Usage: python3 tables.py FI60.json FI10.json"""
import sys, json
fi60, fi10 = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
Q = [("tilt", "tilt σ (rad)"), ("yaw", "yaw σ (rad)"), ("vh", "horiz. vel σ (m/s)"), ("vz", "vert. vel σ (m/s)"),
     ("ph", "horiz. pos σ (m)"), ("pz", "vert. pos σ (m)"), ("bg", "gyro-bias σ (rad/s)"), ("ba", "accel-bias σ (m/s²)")]


def table(case, ref, ests, times, src, refcase=None):
    r = src["cases"][case]
    print(f"\n#### case {case}, reference `{ref}`\n")
    print("| t (s) | quantity | expected | " + " | ".join(ests) + " |")
    print("|---|---|---|" + "---|" * len(ests))
    for t in times:
        for q, lab in Q:
            e = src["cases"][refcase or case][ref][t][q]
            cells = []
            for est in ests:
                v = r[est][t][q]; vr = (v / e) ** 2
                flag = " **FLAG**" if (vr > 2.0 or vr < 0.5) else ""
                cells.append(f"{v:.4g} (×{vr:.2f}){flag}")
            print(f"| {t} | {lab} | {e:.4g} | " + " | ".join(cells) + " |")


table("A", "analytic_tv", ["ekf3", "ukf_offline", "ukf_port", "fgo", "ukf_offline_nojitter", "ukf_port_nojitter"],
      ["10", "60"], fi60)
table("B", "analytic", ["ekf3", "ukf_offline", "ukf_port", "fgo"], ["1", "10"], fi10)
table("C", "analytic_tv", ["ekf3", "ukf_offline", "ukf_port", "fgo"], ["10", "60"], fi60, refcase="A")
