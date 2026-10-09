"""Analyse the gate-recursion dumps: condition numbers over time (both builds), relative cov_gate differences per
block, the real gate-trace difference at every check, trend fits. Writes summary JSON + a figure."""
import json, sys
import numpy as np
G = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/gatecond/out/"
D = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/yawgate2/dump/"
P = "dsn_tex_r1_baseline"
W = 2 + 900 + 225
STEP = int(sys.argv[1]) if len(sys.argv) > 1 else 10      # keyframe subsampling for the eig work


def load(f):
    a = np.fromfile(f)
    return a.reshape(-1, W)


def conds(rows):
    out = []
    for r in rows:
        L = r[2:902].reshape(30, 30); C = r[902:].reshape(15, 15)
        Ls = 0.5 * (L + L.T)
        ev = np.linalg.eigvalsh(Ls)
        d = 1 / np.sqrt(np.diag(Ls)); evs = np.linalg.eigvalsh(Ls * d[:, None] * d[None, :])
        evc = np.linalg.eigvalsh(C)
        dc = 1 / np.sqrt(np.abs(np.diag(C))); evcs = np.linalg.eigvalsh(C * dc[:, None] * dc[None, :])
        prior = L[:15, :15]   # = inv(cov_gate_old) + factor contributions on km1 (cannot separate here)
        out.append((r[0], ev[-1] / ev[0], evs[-1] / evs[0], evc[-1] / evc[0], evcs[-1] / evcs[0], ev[0], ev[-1],
                    evc[0], evc[-1], np.trace(C[0:3, 0:3]), C[3, 3] + C[4, 4], C[5, 5]))
    return np.array(out)


BLK = {"att": slice(0, 3), "pos": slice(3, 6), "vel": slice(6, 9), "bias": slice(9, 15)}


def blockdiff(a, b):
    res = {}
    for n, s in BLK.items():
        A = a[:, 902:].reshape(-1, 15, 15)[:, s, s]; Bm = b[:, 902:].reshape(-1, 15, 15)[:, s, s]
        res[n] = np.linalg.norm((A - Bm).reshape(len(a), -1), axis=1) / np.linalg.norm(A.reshape(len(a), -1), axis=1)
    A = a[:, 902:]; Bm = b[:, 902:]
    res["all"] = np.linalg.norm(A - Bm, axis=1) / np.linalg.norm(A, axis=1)
    LA = a[:, 2:902]; LB = b[:, 2:902]
    res["L"] = np.linalg.norm(LA - LB, axis=1) / np.linalg.norm(LA, axis=1)
    return res


def fit(t, y, tmin=5.0):
    m = (y > 0) & (t > tmin) & np.isfinite(y)
    ll = np.polyfit(np.log10(t[m]), np.log10(y[m]), 1)
    sl = np.polyfit(t[m], np.log10(y[m]), 1)
    # second half only: is growth still on?
    h = m & (t > t[m].max() / 2)
    llh = np.polyfit(np.log10(t[h]), np.log10(y[h]), 1)
    return {"loglog_exp": ll[0], "semilog_dec_per_100s": 100 * sl[0], "loglog_exp_second_half": llh[0]}


def bins(t, y, w=30):
    o = []
    for lo in np.arange(0, t.max(), w):
        s = (t >= lo) & (t < lo + w) & np.isfinite(y)
        if s.any():
            o.append((float(lo), float(np.median(y[s])), float(np.max(y[s]))))
    return o


summary = {}
emu = load(G + "emu.cond.f64"); pye = load(G + "pyemu.cond.f64")
n = min(len(emu), len(pye))
assert np.array_equal(emu[:n, :2], pye[:n, :2]), "keyframe rows differ"
print(f"rows emu {len(emu)} py {len(pye)}; t {emu[0,0]:.2f}..{emu[n-1,0]:.2f}")
ce = conds(emu[:n:STEP]); cp = conds(pye[:n:STEP])
t = ce[:, 0]
names = ["cond_L", "cond_L_scaled", "cond_covgate", "cond_covgate_scaled"]
for i, nm in enumerate(names, 1):
    summary[nm] = {"py_bins": bins(t, cp[:, i]), "cpp_bins": bins(t, ce[:, i]), "fit_py": fit(t, cp[:, i]),
                   "fit_cpp": fit(t, ce[:, i]), "max_rel_py_vs_cpp": float(np.max(np.abs(cp[:, i] / ce[:, i] - 1)))}
    print(nm, "py", summary[nm]["fit_py"], "cpp", summary[nm]["fit_cpp"])
summary["eig"] = {"L_min_bins": bins(t, ce[:, 5]), "L_max_bins": bins(t, ce[:, 6]),
                  "C_min_bins": bins(t, ce[:, 7]), "C_max_bins": bins(t, ce[:, 8]),
                  "att_trace_bins": bins(t, ce[:, 9]), "posxy_var_bins": bins(t, ce[:, 10])}
bd = blockdiff(pye[:n], emu[:n]); tt = emu[:n, 0]
summary["reldiff_py_vs_emu"] = {k: {"bins": bins(tt, v), "fit": fit(tt, v)} for k, v in bd.items()}
for k, v in bd.items():
    print("reldiff", k, summary["reldiff_py_vs_emu"][k]["fit"], "last-bin", summary["reldiff_py_vs_emu"][k]["bins"][-1])
# real gate traces at the checks (py forced to emu decisions vs emu own)
rt = np.fromfile(G + "pyemu.realtrace.f64").reshape(-1, 4)
eg = np.fromfile(D + f"emu_{P}.yawgate.f64").reshape(-1, 4)
m = min(len(rt), len(eg)); assert np.array_equal(rt[:m, 1], eg[:m, 1])
rel = np.abs(rt[:m, 2] - eg[:m, 2]) / np.abs(eg[:m, 2])
summary["gate_trace_rel"] = {"bins": bins(rt[:m, 0], rel), "fit": fit(rt[:m, 0], rel), "n": int(m)}
print("gate trace rel (forced, whole flight)", summary["gate_trace_rel"]["fit"], summary["gate_trace_rel"]["bins"][-3:])
# would the python core's real decisions have differed from emu's?
flip = np.where((rt[:m, 2] > 0.04) != (eg[:m, 3] == 1))[0]
summary["py_real_vs_emu_decision_flips"] = [(float(rt[i, 0]), float(rt[i, 2]), float(eg[i, 2])) for i in flip]
# relation of reldiff to conditioning: regress log reldiff(all cov_gate) on log cond_L at the subsampled rows
rd = bd["all"][::STEP][:len(ce)]
mm = rd > 0
summary["reldiff_vs_condL"] = dict(zip(["slope", "intercept"], np.polyfit(np.log10(ce[mm, 1]), np.log10(rd[mm]), 1)))
summary["reldiff_vs_condL_scaled"] = dict(zip(["slope", "intercept"], np.polyfit(np.log10(ce[mm, 2]), np.log10(rd[mm]), 1)))
summary["reldiff_over_eps_condL_bins"] = bins(t[mm], rd[mm] / (2.2e-16 * ce[mm, 1]))
print("reldiff vs cond", summary["reldiff_vs_condL"], summary["reldiff_vs_condL_scaled"])

# default build (secondary)
try:
    de = load(G + "def.cond.f64"); pd = load(G + "pydef.cond.f64")
    n2 = min(len(de), len(pd)); assert np.array_equal(de[:n2, :2], pd[:n2, :2])
    bd2 = blockdiff(pd[:n2], de[:n2])
    summary["reldiff_py_vs_default"] = {k: {"bins": bins(de[:n2, 0], v), "fit": fit(de[:n2, 0], v)} for k, v in bd2.items()}
    rt2 = np.fromfile(G + "pydef.realtrace.f64").reshape(-1, 4)
    dg = np.fromfile(D + f"cpp_{P}.yawgate.f64").reshape(-1, 4)
    m2 = min(len(rt2), len(dg))
    rel2 = np.abs(rt2[:m2, 2] - dg[:m2, 2]) / np.abs(dg[:m2, 2])
    summary["gate_trace_rel_default"] = {"bins": bins(rt2[:m2, 0], rel2), "fit": fit(rt2[:m2, 0], rel2)}
    print("default gate trace rel", summary["gate_trace_rel_default"]["fit"])
except FileNotFoundError as e:
    print("default build dumps missing:", e)

json.dump(summary, open(G + "summary.json", "w"), indent=1, default=float)

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
ax[0].semilogy(t, cp[:, 1], label="cond(L) Python"); ax[0].semilogy(t, ce[:, 1], "--", label="cond(L) C++ emu")
ax[0].semilogy(t, ce[:, 2], label="cond(L) Jacobi-scaled"); ax[0].semilogy(t, ce[:, 3], label="cond(cov_gate)")
ax[0].semilogy(t, ce[:, 4], label="cond(cov_gate) scaled"); ax[0].legend(fontsize=7); ax[0].set_ylabel("condition number")
for k, v in bd.items():
    ax[1].semilogy(tt, np.maximum(v, 1e-18), lw=0.6, label=k)
ax[1].legend(fontsize=7); ax[1].set_ylabel("rel. Frobenius diff Py vs C++ emu")
ax[2].semilogy(rt[:m, 0], np.maximum(rel, 1e-18), ".", ms=2, label="gate trace rel diff (forced, emu)")
if "gate_trace_rel_default" in summary:
    ax[2].semilogy(rt2[:m2, 0], np.maximum(rel2, 1e-18), ".", ms=2, label="gate trace rel diff (forced, default)")
ax[2].legend(fontsize=7); ax[2].set_xlabel("t (s)")
fig.tight_layout(); fig.savefig(G + "gate_conditioning.png", dpi=110)
print("wrote summary.json and gate_conditioning.png")
