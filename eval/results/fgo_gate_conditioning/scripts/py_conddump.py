"""DIAGNOSTIC ONLY: run the Python FGO replay with the yaw-cap gate decisions forced to a C++ run's (so both builds
follow one trajectory), log the REAL gate trace at every check, and dump at every cov_gate update the 30x30
information matrix L and the new 15x15 cov_gate (same row layout as the patched C++).
Usage: py_conddump.py <cpp .yawgate.f64> <dump prefix> <replay script> <replay args...>
Patches the core in this process only."""
import sys, os, runpy
import numpy as np
SRC = "/home/makerspace/thesis_ws/.claude/worktrees/agent-a9aad2e9b298caf92/src/estimators"
sys.path.insert(0, os.path.join(SRC, "fgo")); sys.path.insert(0, SRC)
import fgo_core
from gtsam.symbol_shorthand import X, V, B

log = np.fromfile(sys.argv[1]).reshape(-1, 4)
fire_k = set(log[log[:, 3] == 1, 1].astype(int).tolist())
pref = sys.argv[2]
fdump = open(pref + ".cond.f64", "wb")
ftr = open(pref + ".realtrace.f64", "wb")
print(f"[conddump] {len(fire_k)} forced fired keyframes from {sys.argv[1]}")

FGO = fgo_core.FGO
orig_kf, orig_pc, orig_tr = FGO.keyframe, FGO._posterior_cov, FGO._att_trace_pred


def kf(self, t, *a, **kw):
    self._cd_t = t
    return orig_kf(self, t, *a, **kw)


def pc(self, g, est, km1, k, prior=None):
    out = orig_pc(self, g, est, km1, k, prior)
    if prior is not None:
        v = self._values(km1, k, est.atPose3(X(k)), est.atVector(V(k)), est.atConstantBias(B(k)), src=est)
        L = self._info(g, v, km1, k, prior)
        np.concatenate([[self._cd_t, float(k)], L.ravel(), out.ravel()]).astype(np.float64).tofile(fdump)
    return out


def tr(self, g, km1, k, Xk, Vk):
    x = orig_tr(self, g, km1, k, Xk, Vk)
    np.array([self._cd_t, float(k), x, 1.0 if k in fire_k else 0.0]).tofile(ftr)
    return 1.0 if k in fire_k else 0.0


FGO.keyframe, FGO._posterior_cov, FGO._att_trace_pred = kf, pc, tr
script = sys.argv[3]
sys.argv = [script] + sys.argv[4:]
runpy.run_path(script, run_name="__main__")
fdump.close(); ftr.close()
