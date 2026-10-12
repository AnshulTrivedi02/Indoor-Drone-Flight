"""F8/F2 link check: attitude demand, throttle and EKF3 velocity while armed on the ground in LAND.

Usage: python f2_check.py <dump.pkl> <t0> <t1>
"""
import pickle
import sys

import numpy as np


def main(p, t0, t1):
    d = pickle.load(open(p, "rb"))

    def idx(k, core=None):
        return {round(x["TimeUS"] * 1e-6, 1): x for x in d.get(k, [])
                if t0 < x["TimeUS"] * 1e-6 < t1 and (core is None or x.get("C") == core)}

    att, ct, k1 = idx("ATT"), idx("CTUN"), idx("XKF1", 0)
    for t in sorted(att):
        if int(round(t * 10)) % 5:
            continue
        a, c, k = att[t], ct.get(t, {}), k1.get(t, {})
        print(f"{t:7.1f} DesR {a['DesRoll']:6.1f} R {a['Roll']:6.1f} DesP {a['DesPitch']:6.1f} P {a['Pitch']:6.1f} "
              f"ThO {c.get('ThO', np.nan):.3f} | EKF VN {k.get('VN', np.nan):6.2f} VE {k.get('VE', np.nan):6.2f}")
    for kk in ("MODE", "EV", "MSG", "ERR", "ARM"):
        for x in d.get(kk, []):
            if t0 < x["TimeUS"] * 1e-6 < t1:
                print("   >>", round(x["TimeUS"] * 1e-6, 2), kk,
                      {a: b for a, b in x.items() if a not in ("mavpackettype", "TimeUS")})


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
