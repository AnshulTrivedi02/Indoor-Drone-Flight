"""POST-HOC DIAGNOSTIC (not a band): replay the Python FGO with its yaw-cap gate DECISIONS forced to the C++ run's
(fire exactly at the keyframes where the C++ log fired), to attribute a band FAIL to threshold ties.
Copy of fgo_cpp_equiv_yawgate/scripts/forced_gate.py with SRC = this worktree.
Usage: forced_gate.py <cpp .yawgate.f64> <replay script> <replay args...>   (env FGO_DUMP_EVENTS / FGO_OUT_ROOT set)
Never changes the cores: it patches FGO._att_trace_pred in this process only."""
import sys, os, runpy
import numpy as np
SRC = "/home/makerspace/thesis_ws/.claude/worktrees/agent-a16391ff0a1144fd8/src/estimators"
sys.path.insert(0, os.path.join(SRC, "fgo")); sys.path.insert(0, SRC)
import fgo_core
log = np.fromfile(sys.argv[1]).reshape(-1, 4)
fire_k = set(log[log[:, 3] == 1, 1].astype(int).tolist())
print(f"[forced] {len(fire_k)} fired keyframes from {sys.argv[1]}")
fgo_core.FGO._att_trace_pred = lambda self, g, km1, k, Xk, Vk: (1.0 if k in fire_k else 0.0)
script = sys.argv[2]
sys.argv = [script] + sys.argv[3:]
runpy.run_path(script, run_name="__main__")
