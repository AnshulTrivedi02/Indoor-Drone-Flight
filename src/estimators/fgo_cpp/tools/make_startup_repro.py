"""(~/venv-fgo) Build a live-timing reproduction tape from a bag tape: a synthetic imu_bridge start-up backlog.
usage: make_startup_repro.py <in.tape> <out.tape> <mode: ramp|burst> [E0=0.55] [T=1.5]
ramp : IMU + time_ref rows (paired by header stamp) with th < th0 + T get th' = th + E0 * (1 - (th - th0) / T)
       (receipt stamps late by a backlog that drains linearly); they are moved to their new arrival position.
burst: IMU + time_ref rows with th < th0 + E0 all get th' = th0 + E0 (one receipt instant, duplicate header stamps),
       and arrive as all the IMU rows first, then all the time_ref rows (the worst live executor order).
Other rows keep their order (arrival key = running max of their own stamps)."""
import sys, numpy as np
src, dst, mode = sys.argv[1:4]
E0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.55
T = float(sys.argv[5]) if len(sys.argv) > 5 else 1.5
R = np.fromfile(src).reshape(-1, 9).copy()
k = R[:, 0].astype(int)
th0 = R[k == 0, 1].min()
key = np.empty(len(R)); sub = np.zeros(len(R))
run = -np.inf
aff = np.isin(k, (0, 7)) & (R[:, 1] < th0 + (T if mode == "ramp" else E0))
for i in range(len(R)):
    if not aff[i]:
        run = max(run, R[i, 1]); key[i] = run
if mode == "ramp":
    R[aff, 1] = R[aff, 1] + E0 * (1 - (R[aff, 1] - th0) / T)
    key[aff] = R[aff, 1]
else:
    R[aff, 1] = th0 + E0
    key[aff] = th0 + E0
    sub[aff & (k == 7)] = 1          # all burst IMU rows before all burst time_ref rows
# affected rows sort after unaffected rows of equal key (they arrive late)
order = np.lexsort((np.arange(len(R)), sub, aff.astype(int), key))
R[order].tofile(dst)
print(f"[repro] {mode}: {aff.sum()} rows re-stamped (E0 {E0} s, th0 {th0:.3f}); {len(R)} rows")
