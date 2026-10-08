"""DIAGNOSTIC wrapper around the UNCHANGED room_fgo_replay.py (FGO tilt trace, 2026-10-09). Not a result.
Env knobs (all optional):
  DIAG_BINIT_ACC, DIAG_BINIT_GYR : 1-sigma used in setBiasAccOmegaInit (thesis: 0.2, 0.043633)
  DIAG_TMAX                      : drop every event after this bag time (shorter run)
  DIAG_SKIP_TAG "a,b"            : drop tag fixes in [a, b] AFTER the first one (anchor kept)
Output goes to FGO_OUT_ROOT (must be set; a scratch dir), never to the trial's room_fgo/.
Usage: FGO_OUT_ROOT=... ROOM_TAG_SIGMA_POS=0.02 python diag_replay.py <trial> --no-batch"""
import os, sys, runpy, numpy as np
assert os.environ.get("FGO_OUT_ROOT"), "set FGO_OUT_ROOT to a scratch dir"
REPO = os.environ.get("DIAG_REPO", "/home/makerspace/thesis_ws/.claude/worktrees/agent-a2b8ef99455db24c0")
sys.path.insert(0, f"{REPO}/src/estimators/fgo"); sys.path.insert(0, f"{REPO}/src/estimators")
import fgo_core, imu_timing
_orig = fgo_core.make_pim_params
ba, bg = float(os.environ.get("DIAG_BINIT_ACC", 0.2)), float(os.environ.get("DIAG_BINIT_GYR", 0.043633))


def make_pim_params():
    p = _orig()
    p.setBiasAccOmegaInit(np.diag([ba ** 2] * 3 + [bg ** 2] * 3))
    return p


fgo_core.make_pim_params = make_pim_params
_gap = imu_timing.apply_gap_rule
TMAX = float(os.environ.get("DIAG_TMAX", "inf"))
SKIP = [float(x) for x in os.environ["DIAG_SKIP_TAG"].split(",")] if os.environ.get("DIAG_SKIP_TAG") else None


def apply_gap_rule(ev, trial):
    ev = [e for e in _gap(ev, trial) if e[0] <= TMAX]
    if SKIP:
        tags = sorted(e[0] for e in ev if e[1] == "tag")
        t_first = tags[0] if tags else None
        ev = [e for e in ev if not (e[1] == "tag" and e[0] != t_first and SKIP[0] <= e[0] <= SKIP[1])]
    return ev


imu_timing.apply_gap_rule = apply_gap_rule
# DIAG_WINDOW / DIAG_LM: override the smoother lag and the LM cap; DIAG_SKIP_FLOW "a,b": no flow events in [a, b]
_init = fgo_core.FGO.__init__


def _patched_init(self, window=1.0, kf_dt=1.0 / 30.0, solver="batch", lm_maxiter=2, **kw):
    window = float(os.environ.get("DIAG_WINDOW", window)); lm_maxiter = int(os.environ.get("DIAG_LM", lm_maxiter))
    _init(self, window=window, kf_dt=kf_dt, solver=solver, lm_maxiter=lm_maxiter, **kw)


fgo_core.FGO.__init__ = _patched_init
SKIPF = [float(x) for x in os.environ["DIAG_SKIP_FLOW"].split(",")] if os.environ.get("DIAG_SKIP_FLOW") else None
if SKIPF:
    _g2 = imu_timing.apply_gap_rule

    def apply_gap_rule(ev, trial):
        return [e for e in _g2(ev, trial) if not (e[1] == "flow" and SKIPF[0] <= e[0] <= SKIPF[1])]
    imu_timing.apply_gap_rule = apply_gap_rule
print(f"[diag] binit acc {ba} gyr {bg} tmax {TMAX} skip {SKIP}", flush=True)
sys.argv = [f"{REPO}/src/estimators/fgo/room_fgo_replay.py"] + sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
