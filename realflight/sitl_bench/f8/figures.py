"""F8 figures and checks (read-only on the data).

  python figures.py <pkl_dir> <out_dir>

Figure 1 (f8_b6b_prearm.png): the B6b run 1 pre-arm runaway (wbench2_hoverB_20261012_114206, F 43-63 s):
  EKF3 VE (both cores) against the true East velocity; XKF5.NI with the flow-gate line; the OF rows (quality) and
  the rangefinder; events.
Figure 2 (f8_b10b_second_fs.png): the B10b second EKF failsafe (wbench2_hoverC_20261012_114843, F 115-146 s):
  true x against the textured-mat edge (x = -10 m), RFND, XKF4 HORIZ_POS_REL, OF rows, events.
Checks printed: the implied flow range on the ground (VE / (FIX/1000)) against HAGL - FLOW_POS_Z; the VE ramp slope
against g*sin(EKF roll) with the vehicle level (IMU AccY ~ 0).
"""
import csv
import os
import pickle
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

WB = os.path.expanduser("~/thesis_data/wbench")


def ser(d, k, f, c=None):
    r = [x for x in d.get(k, []) if c is None or x.get("C") == c]
    return np.array([x["TimeUS"] * 1e-6 for x in r]), np.array([x[f] for x in r], dtype=float)


def truth(sess, off):
    rows = {}
    for r in csv.DictReader(open(os.path.join(WB, sess, "forwarder.csv"))):
        if r["mode"] == "normal" and r["body"].endswith("#1") and r["dest"] == "1":
            rows[r["t_mocap"]] = (float(r["t_mocap"]) - off, float(r["x"]), float(r["y"]), float(r["z"]))
    return np.array(sorted(rows.values()))


def offset(sess, pairs):
    return float(np.median([w - f for w, f in pairs]))


def events(d, t0, t1):
    out = []
    for x in d.get("MSG", []):
        t = x["TimeUS"] * 1e-6
        if t0 <= t <= t1:
            out.append((t, x["Message"]))
    for x in d.get("ARM", []):
        t = x["TimeUS"] * 1e-6
        if t0 <= t <= t1:
            out.append((t, "ARM" if x["ArmState"] else "DISARM"))
    return out


def vlines(ax, ev, keys):
    for t, m in ev:
        for k, lab in keys:
            if k in m:
                ax.axvline(t, color="0.5", lw=0.8, ls="--")
                ax.text(t, ax.get_ylim()[1], lab, rotation=90, va="top", ha="right", fontsize=7, color="0.3")


def fig_b6b(pdir, out):
    sess = "wbench2_hoverB_20261012_114206"
    d = pickle.load(open(os.path.join(pdir, sess + "__00000027.pkl"), "rb"))
    # W-F pairs from the analysis timeline (03_B6b_right_body.txt): MODE LAND 44.883 <-> 1791765778.193,
    # EV ARMED 56.431 <-> 1791765790.110
    off = offset(sess, [(1791765778.193, 44.883), (1791765790.110, 56.431)])
    T = truth(sess, off)
    t0, t1 = 43.0, 63.0
    m = (T[:, 0] > t0 - 1) & (T[:, 0] < t1 + 1)
    Tm = T[m]
    # true East velocity, 0.2 s central difference; blank the carry teleport (|v| > 5 m/s)
    tv = Tm[:, 0]
    ve = np.gradient(Tm[:, 1], tv)
    ve[np.abs(ve) > 5] = np.nan
    fig, ax = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
    for c, col in ((0, "C0"), (1, "C1")):
        t, v = ser(d, "XKF1", "VE", c)
        ax[0].plot(t, v, col, label=f"EKF3 VE core {c}")
    ax[0].plot(tv, ve, "k", lw=1, label="true East velocity (Gazebo)")
    ax[0].set_ylabel("East velocity (m/s)")
    ax[0].legend(fontsize=8, loc="upper left")
    t, ni = ser(d, "XKF5", "NI")
    ax[1].plot(t, ni, "C3")
    ax[1].axhline(100, color="k", lw=0.8)
    ax[1].text(t0 + 0.2, 105, "gate (test ratio 1)", fontsize=8)
    ax[1].set_ylabel("XKF5.NI (100 x test ratio)")
    t, q = ser(d, "OF", "Qual")
    ax[2].plot(t, q, "C2.", ms=2)
    ax[2].set_ylabel("OF quality (rows = flow received)")
    t, r = ser(d, "RFND", "Dist")
    ax[3].plot(t, r, "C4")
    t, h = ser(d, "XKF5", "HAGL")
    ax[3].plot(t, h, "C5", label="XKF5.HAGL (EKF height of body origin)")
    ax[3].plot(t, h - 0.25, "C5", ls=":", label="HAGL - FLOW_POS_Z (flow range on the ground)")
    ax[3].axhline(0, color="k", lw=0.5)
    ax[3].set_ylabel("RFND / height (m)")
    ax[3].legend(fontsize=8)
    ax[3].set_xlim(t0, t1)
    ax[3].set_xlabel("FC time F (s)")
    ev = events(d, t0, t1)
    ev.append((49.93, "touchdown"))
    ev.append((1791765785.676 - off, "carry"))
    for a in ax:
        vlines(a, ev, [("touchdown", "touchdown"), ("DISARM", "disarm"), ("carry", "carry"), ("ARM", "arm"),
                       ("EKF Failsafe", "EKF FS")])
    fig.suptitle("F8: B6b run 1, EKF3 East-velocity runaway on the ground before arming")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "f8_b6b_prearm.png"), dpi=110)

    # checks
    t5, fix = ser(d, "XKF5", "FIX")
    _, hagl = ser(d, "XKF5", "HAGL")
    tk, vek = ser(d, "XKF1", "VE", 0)
    print("implied flow range on the ground (VE / FIX), B6b, core 0:")
    for ts in (50.2, 51.0, 52.0, 53.0, 53.5):
        i = np.searchsorted(t5, ts)
        v = np.interp(t5[i], tk, vek)
        print(f"  F {t5[i]:.2f}: VE {v:.3f}  FIX/1000 {fix[i] / 1000:.3f}  -> range {v / (fix[i] / 1000):+.4f} m;"
              f"  HAGL - 0.25 = {hagl[i] - 0.25:+.3f} m")
    m = (tk > 50.5) & (tk < 58.4)
    slope = np.polyfit(tk[m], vek[m], 1)[0]
    _, roll = ser(d, "XKF1", "Roll", 0)
    ti, accy = ser(d, "IMU", "AccY")
    mi = (ti > 50.5) & (ti < 56.0)
    print(f"VE ramp slope 50.5-58.4 s: {slope:.3f} m/s^2; EKF roll mean {roll[m].mean():.2f} deg -> "
          f"g*sin(roll) = {9.81 * np.sin(np.radians(roll[m].mean())):.3f} m/s^2; IMU AccY mean "
          f"{accy[mi].mean():+.4f} m/s^2 (level => true roll ~0)")


def fig_b10b(pdir, out):
    sess = "wbench2_hoverC_20261012_114843"
    d = pickle.load(open(os.path.join(pdir, sess + "__00000028.pkl"), "rb"))
    # W-F pairs from 03_B10b.txt: MODE LAND (GCS) 110.243 <-> 1791766242.244; FAILSAFE_GCS 96.591 <-> 228.500
    off = offset(sess, [(1791766242.244, 110.243), (1791766228.500, 96.591)])
    T = truth(sess, off)
    t0, t1 = 114.0, 147.0
    fig, ax = plt.subplots(4, 1, figsize=(10, 9), sharex=True)
    m = (T[:, 0] > t0) & (T[:, 0] < t1)
    ax[0].plot(T[m, 0], T[m, 1], "k", label="true x (East)")
    ax[0].plot(T[m, 0], T[m, 2], "0.5", label="true y (North)")
    ax[0].axhline(-10, color="C3", lw=1)
    ax[0].text(t0 + 0.3, -9.6, "textured-mat edge x = -10 m (the only ground geometry)", fontsize=8, color="C3")
    ax[0].set_ylabel("position (m)")
    ax[0].legend(fontsize=8)
    t, r = ser(d, "RFND", "Dist")
    ax[1].plot(t, r, "C4")
    ax[1].set_ylabel("RFND Dist (m)")
    t, ss = ser(d, "XKF4", "SS", 0)
    ax[2].step(t, (ss.astype(int) >> 3) & 1, "C0", where="post", label="HORIZ_POS_REL")
    ax[2].step(t, ((ss.astype(int) >> 6) & 1) + 0.03, "C1", where="post", label="TERRAIN_ALT (gndOffsetValid)")
    ax[2].set_ylabel("XKF4 core 0 flags")
    ax[2].legend(fontsize=8)
    t, q = ser(d, "OF", "Qual")
    ax[3].plot(t, q, "C2.", ms=2)
    ax[3].set_ylabel("OF quality")
    ax[3].set_xlabel("FC time F (s)")
    ax[3].set_xlim(t0, t1)
    ev = events(d, t0, t1)
    for a in ax:
        vlines(a, ev, [("EKF Failsafe", "EKF FS"), ("Cleared", "FS cleared"), ("started relative", "flow back"),
                       ("stopped aiding", "stopped aiding"), ("DISARM", "disarm")])
    fig.suptitle("B10b: the second EKF failsafe follows the rangefinder loss at the mat edge")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "f8_b10b_second_fs.png"), dpi=110)
    i = np.argmax(T[m, 1] < -10)
    print(f"B10b: true x crosses -10 m at F {T[m][i, 0]:.2f}")
    tz = t[0]
    tr, rr = ser(d, "RFND", "Dist")
    j = np.argmax((tr > 130) & (rr < 0.01))
    print(f"B10b: first RFND Dist = 0 at F {tr[j]:.2f}")


if __name__ == "__main__":
    os.makedirs(sys.argv[2], exist_ok=True)
    fig_b6b(sys.argv[1], sys.argv[2])
    fig_b10b(sys.argv[1], sys.argv[2])
