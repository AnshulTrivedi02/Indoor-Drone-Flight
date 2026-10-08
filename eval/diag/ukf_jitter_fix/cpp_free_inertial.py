"""UKF jitter correction (2026-10-09), DIAGNOSTIC: free-inertial covariance growth through the C++ PORT itself.

The model audit's "ukf_port" column was the Python core at the port's 12.5 ms cadence, not the C++. This drives the
port's own NavUKF::predict (and yaw_pseudo for case C) through ~/ardupilot_ukf examples/UKF_Equiv, on exactly the
12.5 ms IMU bins, initial state and initial covariances of eval/diag/model_audit/free_inertial.py, converted to
NED/FRD as eval/ukf_event_export.py does. UKF_Equiv's diagnostic option UKF_EQ_PDIAG dumps diag(P) after every event.

  export: python3 cpp_free_inertial.py export WIN.npz T_TOTAL CASE OUT_PREFIX     -> OUT_PREFIX.bin, OUT_PREFIX.meta.npz
  score:  python3 cpp_free_inertial.py score OUT_PREFIX FI.json CASE REF            (FI.json = free_inertial.py output)
The metrics (tilt, yaw, horizontal/vertical velocity and position, rate-form bias sigma) use only diagonal elements,
which the ENU->NED map permutes and sign-flips, so they are frame-invariant.
"""
import json, math, os, struct, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src", "estimators"))
import ukf_core as U

DTR = 0.0125
S_ATT, S_V, S_P = 1e-5, 1e-2, 1e-2
S_BG_A, S_BA_A = 1e-6, math.sqrt(5e-9) / DTR
S_BG_B, S_BA_B = 0.043633, 0.2
CHK = [1.0, 2.0, 5.0, 10.0, 30.0, 60.0]

T = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1.0]])      # ENU -> NED
F = np.diag([1.0, -1.0, -1.0])                           # FLU <-> FRD
J = np.zeros((15, 15))
J[0:3, 0:3] = T; J[3:6, 3:6] = T
J[6, 6] = 1; J[7, 7] = -1; J[8, 8] = -1
J[9:12, 9:12] = F; J[12:15, 12:15] = F


def to_ned(x):
    y = J @ x
    y[8] = (math.pi / 2 - x[8] + math.pi) % (2 * math.pi) - math.pi
    return y


def export(win, t_total, case, out):
    d = np.load(win)
    t, acc, gyro = d["t"], d["acc"], d["gyro"]
    period = float(d["period_ms"]) / 1e3
    t = t[t <= t[0] + t_total + 1e-9]; n = len(t); acc = acc[:n]; gyro = gyro[:n]
    dts = np.r_[period, np.diff(t)]
    T0 = t[0] - period
    cum_t = np.r_[T0, t]
    cum_g = np.vstack([np.zeros(3), np.cumsum(gyro * dts[:, None], axis=0)])
    cum_a = np.vstack([np.zeros(3), np.cumsum(acc * dts[:, None], axis=0)])
    edges = np.arange(T0, t[-1] + 1e-12, DTR)
    cum_at = lambda e, c: np.array([np.interp(e, cum_t, c[:, k]) for k in range(3)]).T
    G_e, A_e = cum_at(edges, cum_g), cum_at(edges, cum_a)
    bin_da, bin_dv = np.diff(G_e, axis=0), np.diff(A_e, axis=0)
    bin_t = edges[1:] - T0
    am = acc.mean(0)
    s_bg, s_ba = (S_BG_B, S_BA_B) if case == "B" else (S_BG_A, S_BA_A)
    x, _ = U.init_state(am, 2.0, dt=DTR)
    P = np.diag([S_P**2] * 3 + [S_V**2] * 3 + [S_ATT**2] * 3 + [(s_bg * DTR) ** 2] * 3 + [(s_ba * DTR) ** 2] * 3)
    p = U.make_params(dt=DTR)
    ev, et = [], []
    tc = 0.0
    for k in range(len(bin_t)):
        ev.append((0, list(F @ bin_da[k]) + list(F @ bin_dv[k]) + [DTR])); et.append(bin_t[k])
        if case == "C" and bin_t[k] - tc >= p["YAW_DT"]:
            ev.append((3, [0.0] * 7)); et.append(bin_t[k]); tc = bin_t[k]
    with open(out + ".bin", "wb") as f:
        f.write(b"UKFEV001")
        f.write(struct.pack("<15d", *to_ned(x))); f.write(struct.pack("<225d", *(J @ P @ J.T).ravel()))
        f.write(struct.pack("<Q", len(ev)))
        for typ, inp in ev:
            f.write(struct.pack("<b7d", typ, *inp))
    np.savez(out + ".meta.npz", et=np.array(et), typ=np.array([e[0] for e in ev]))
    print(f"exported {len(ev)} events ({sum(1 for e in ev if e[0] == 0)} predicts), case {case}, {t_total} s -> {out}.bin")


def score(prefix, fi_json, case, ref):
    m = np.load(prefix + ".meta.npz")
    et, typ = m["et"], m["typ"]
    Pd = np.fromfile(prefix + ".pdiag", dtype="<f8").reshape(-1, 15)
    assert len(Pd) == len(et), (len(Pd), len(et))
    keep = np.r_[et[1:] != et[:-1], True]          # the state after the LAST event of each 12.5 ms step
    rows = {}
    for c in CHK:
        if c > et[-1] + 0.1:
            continue
        idx = np.where(keep)[0]
        k = idx[int(np.argmin(np.abs(et[idx] - c)))]
        p = Pd[k]
        rows[f"{c:g}"] = dict(t=float(et[k]), tilt=math.sqrt((p[6] + p[7]) / 2), yaw=math.sqrt(p[8]),
                              vh=math.sqrt((p[3] + p[4]) / 2), vz=math.sqrt(p[5]), ph=math.sqrt((p[0] + p[1]) / 2),
                              pz=math.sqrt(p[2]), bg=math.sqrt((p[9] + p[10] + p[11]) / 3) / DTR,
                              ba=math.sqrt((p[12] + p[13] + p[14]) / 3) / DTR)
    fi = json.load(open(fi_json))["cases"]
    refd = fi["A" if (case == "C" and ref == "analytic_tv") else case][ref]
    pyport = fi[case]["ukf_port"]
    out = {"case": case, "ref": ref, "cpp_port": rows, "ratio_to_ref": {}, "ratio_to_python_port": {}}
    print(f"case {case}: C++ port vs {ref} (variance ratio) and vs the Python core at 12.5 ms")
    for c, r in rows.items():
        out["ratio_to_ref"][c] = {q: (r[q] / refd[c][q]) ** 2 for q in ("tilt", "yaw", "vh", "vz", "ph", "pz", "bg", "ba")}
        out["ratio_to_python_port"][c] = {q: (r[q] / pyport[c][q]) ** 2 for q in ("tilt", "yaw", "vh", "vz", "ph", "pz", "bg", "ba")}
        print(f"  t={c:>3s} ref:  " + "  ".join(f"{q}=x{v:.3f}" for q, v in out["ratio_to_ref"][c].items()))
        print(f"        py :  " + "  ".join(f"{q}=x{v:.6f}" for q, v in out["ratio_to_python_port"][c].items()))
    json.dump(out, open(prefix + ".score.json", "w"), indent=1)


if __name__ == "__main__":
    if sys.argv[1] == "export":
        export(sys.argv[2], float(sys.argv[3]), sys.argv[4], sys.argv[5])
    else:
        score(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
