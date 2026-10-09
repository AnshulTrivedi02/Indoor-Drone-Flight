"""Step-2 D27 diagnostic: write the offline UKF's per-step Q diagonal (make_params(dt=DT_STEP)) for UKF_EQ_QDIAG."""
import sys, numpy as np
sys.path.insert(0, "/home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4/src/estimators")
import ukf_core as U
pre = sys.argv[1]
e = np.load(pre + ".npz")
d = e["inputs"][e["type"] == 0, 6]
u, c = np.unique(d, return_counts=True)
print("predict dt values (top 3):", sorted(zip(c, u))[-3:], "n unique", len(u))
dt = u[np.argmax(c)]
q = np.diag(U.make_params(dt=dt)["Q"]).copy()      # diagonal unchanged by the NED/FRD axis permutation within blocks
q.astype("<f8").tofile(pre + ".qdiag")
print("DT_STEP", dt, "qdiag", q)
