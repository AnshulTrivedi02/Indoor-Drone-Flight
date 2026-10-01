"""D24: old vs new fly_trial.sim_time_now_s on a recorded MAVProxy tlog (file playback, non-blocking reads).
Usage (venv-ardupilot): python3 eval/d24_clock_equiv.py DIR [TLOG]; DIR holds fly_trial_old.py
(git show 0ab58eb:fly_trial.py). The fgo_groundtest_half tlog is kept at ~/thesis_data/trials/fgo_groundtest_half/mav.tlog."""
import importlib.util, sys
from pymavlink import mavutil
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
S = sys.argv[1]
old = load(f"{S}/fly_trial_old.py", "old"); new = load("/home/makerspace/thesis_ws/fly_trial.py", "new")
def run(mod, tl):
    m = mavutil.mavlink_connection(tl); out = []
    rm = m.recv_match; m.recv_match = lambda **k: rm(**{**k, "blocking": False})
    while True:
        try: out.append(mod.sim_time_now_s(m, timeout_s=0.5))
        except mod.TrialFailure: return out
        if len(out) > 100000: return out
tl = sys.argv[2] if len(sys.argv) > 2 else f"{S}/fgo_groundtest_half_mav.tlog"
a, b = run(old, tl), run(new, tl)
n = len(a); same = [x for x in b if a[0] <= x <= a[-1]] == a   # the window where LOCAL_POSITION_NED streamed
print(f"old calls before failure {n}, last {a[-1]:.3f}s; new calls {len(b)}, identical within the LOCAL_POSITION_NED window: {same}")
print("new values after the old one failed (estimator-independent fallback):", len(b) - n, "calls, last", f"{b[-1]:.3f}s")
print("monotone new:", all(y >= x for x, y in zip(b, b[1:])))
import difflib
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
for op in sm.get_opcodes():
    if op[0] != "equal": print(op, "old", a[op[1]:op[2]][:5], "new", b[op[3]:op[4]][:5])
