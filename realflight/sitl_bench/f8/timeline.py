"""F8 investigation: print a binned EKF3/flow/range timeline (core 0 by default) over an FC-clock window.

Usage: python timeline.py <dump.pkl> <t0_s> <t1_s> [bin_s] [core]
Columns: XKF1 VN VE PN PE PD; XKF4 SS flags (decoded, see nav_filter_status in AP_Nav_Common.h) and test ratios;
XKF5 NI FIX FIY HAGL rng; OF Qual flowX flowY bodyX bodyY (rad/s); RFND Dist.
"""
import pickle
import sys

import numpy as np

SS_BITS = ["att", "hvel", "vvel", "hposrel", "hposabs", "vposabs", "terr", "constpos", "predhrel", "predhabs",
           "takeoffdet", "takeoff", "touchdown", "gpsg", "badacc", "gpsglitch", "gpsqual", "init", "rejflow", "rejrng"]


def ss_str(ss):
    ss = int(ss)
    return ",".join(n for i, n in enumerate(SS_BITS) if ss >> i & 1)


def rows(d, k, c=None):
    r = d.get(k, [])
    if c is not None:
        r = [x for x in r if x.get("C") == c]
    t = np.array([x["TimeUS"] for x in r]) * 1e-6
    return t, r


def main(p, t0, t1, b=0.5, core=0):
    d = pickle.load(open(p, "rb"))
    t1k, k1 = rows(d, "XKF1", core)
    t4k, k4 = rows(d, "XKF4", core)
    t5k, k5 = rows(d, "XKF5", core)
    tof, of = rows(d, "OF")
    trf, rf = rows(d, "RFND")
    ev = []
    for k in ("MODE", "EV", "MSG", "ERR", "ARM", "ORGN"):
        for x in d.get(k, []):
            ts = x["TimeUS"] * 1e-6
            if t0 <= ts <= t1:
                ev.append((ts, k, {kk: v for kk, v in x.items() if kk not in ("mavpackettype", "TimeUS")}))
    ev.sort(key=lambda e: e[0])
    ei = 0
    t = t0
    while t < t1:
        while ei < len(ev) and ev[ei][0] < t + b:
            print(f"      >> {ev[ei][0]:8.3f} {ev[ei][1]} {ev[ei][2]}")
            ei += 1

        def last(tt, rr):
            i = np.searchsorted(tt, t + b) - 1
            return rr[i] if i >= 0 else None

        def mean(tt, rr, f):
            m = (tt >= t) & (tt < t + b)
            return np.mean([rr[i][f] for i in np.nonzero(m)[0]]) if m.any() else np.nan

        a = last(t1k, k1)
        s = last(t4k, k4)
        f5 = last(t5k, k5)
        print(f"{t:7.2f} V {a['VN']:6.2f} {a['VE']:6.2f} {a['VD']:5.2f} P {a['PN']:6.2f} {a['PE']:6.2f} {a['PD']:5.2f} "
              f"| SV {s['SV']:.2f} SP {s['SP']:.2f} SH {s['SH']:.2f} FS {s['FS']} TS {s['TS']} [{ss_str(s['SS'])}] "
              f"| NI {f5['NI'] if f5 else -1:4.0f} FIX {mean(t5k, k5, 'FIX'):7.3f} FIY {mean(t5k, k5, 'FIY'):7.3f} "
              f"HAGL {f5['HAGL'] if f5 else -1:5.2f} rng {f5['rng'] if f5 else -1:5.2f} "
              f"| OF q {mean(tof, of, 'Qual'):5.0f} fx {mean(tof, of, 'flowX'):6.3f} fy {mean(tof, of, 'flowY'):6.3f} "
              f"bx {mean(tof, of, 'bodyX'):6.3f} by {mean(tof, of, 'bodyY'):6.3f} n {int(((tof>=t)&(tof<t+b)).sum())} "
              f"| R {mean(trf, rf, 'Dist'):5.3f}")
        t += b


if __name__ == "__main__":
    a = sys.argv
    main(a[1], float(a[2]), float(a[3]), float(a[4]) if len(a) > 4 else 0.5, int(a[5]) if len(a) > 5 else 0)
