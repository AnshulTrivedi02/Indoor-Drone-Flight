import runpy, sys
sys.argv = ["free_inertial.py"] + sys.argv[1:]
sys.path.insert(0, "/home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4/src/estimators")
import ukf_core
runpy.run_path("/home/makerspace/thesis_ws/.claude/worktrees/agent-af3c884451ec5bfd4/eval/diag/model_audit/free_inertial.py", run_name="__main__")
print("CHOL_STATS (fixed _sigma_points only)", ukf_core.CHOL_STATS, "file", ukf_core.__file__)
