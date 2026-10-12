"""F8: raw (unbinned) rows over a short FC-clock window: XKF1 (both cores), XKF2 accel bias, XKF3 innovations,
XKF4 test ratios, XKF5, OF, RFND and IMU accel/gyro, merged in time order.

Usage: python fine.py <dump.pkl> <t0_s> <t1_s> [types, comma-separated]
"""
import pickle
import sys

FIELDS = {
    "XKF1": ["C", "Roll", "Pitch", "Yaw", "VN", "VE", "VD", "PN", "PE", "PD", "GX", "GY", "GZ"],
    "XKF2": ["C", "AX", "AY", "AZ"],
    "XKF3": ["C", "IVN", "IVE", "IVD", "IPN", "IPE", "IPD"],
    "XKF4": ["C", "SV", "SP", "SH", "FS", "TS", "SS", "PI"],
    "XKF5": ["NI", "FIX", "FIY", "HAGL", "offset", "rng", "eVel"],
    "OF": ["Qual", "flowX", "flowY", "bodyX", "bodyY"],
    "RFND": ["Dist", "Stat"],
    "IMU": ["I", "AccX", "AccY", "AccZ", "GyrX", "GyrY", "GyrZ"],
    "ATT": ["Roll", "Pitch", "Yaw", "DesRoll", "DesPitch"],
    "RCOU": ["C1", "C2", "C3", "C4"],
}


def main(p, t0, t1, types=None):
    d = pickle.load(open(p, "rb"))
    types = types or list(FIELDS)
    out = []
    for k in types:
        for x in d.get(k, []):
            t = x["TimeUS"] * 1e-6
            if t0 <= t <= t1:
                fl = FIELDS.get(k) or [f for f in x if f not in ("mavpackettype", "TimeUS")]
                out.append((t, k, " ".join(f"{f}={x[f]:.4g}" if isinstance(x[f], float) else f"{f}={x[f]}"
                                            for f in fl if f in x)))
    for k in ("MODE", "EV", "MSG", "ERR"):
        for x in d.get(k, []):
            t = x["TimeUS"] * 1e-6
            if t0 <= t <= t1:
                out.append((t, k, str({kk: v for kk, v in x.items() if kk not in ("mavpackettype", "TimeUS")})))
    out.sort(key=lambda e: e[0])
    for t, k, s in out:
        print(f"{t:9.3f} {k:5s} {s}")


if __name__ == "__main__":
    a = sys.argv
    main(a[1], float(a[2]), float(a[3]), a[4].split(",") if len(a) > 4 else None)
