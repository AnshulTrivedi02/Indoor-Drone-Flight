"""Ablation rung table (pre-registration §3, docs/thesis/ablation/preregistration.md). Analysis harness, not estimator code."""
import os
A = "/home/makerspace/thesis_data/ablation"
TR = "/home/makerspace/thesis_data/trials"
BAGS = [f"{ds}_tex_r{r}" for ds in ("fwdc", "fwdplainc") for r in (1, 2, 3)]
HUB = {"F_TAG": "H1345", "F_ROBUST": "huber:1.345"}
# rung: (folder, W, cap, arms, extra env)
RUNGS = {
    "r0": ("r0_w0.25_lm2", "0.25", 2, ("heading", "baseline"), {}),
    "r1": ("r1_kf1_lm1", "0.01", 1, ("heading", "baseline"), {}),
    "r2": ("r2_kf1_lm2", "0.01", 2, ("heading", "baseline"), {}),
    "r3": ("r3_kf1_lm100", "0.01", 100, ("heading", "baseline"), {}),
    "r4": ("r4_w1_lm2", "1", 2, ("heading", "baseline"), {}),
    "r5": ("r5_w2_lm2", "2", 2, ("heading", "baseline"), {}),
    "r6": ("r6_w0.25_lm2_huber", "0.25", 2, ("heading",), HUB),
    "r7": ("r7_kf1_lm100_huber", "0.01", 100, ("heading",), HUB),
}
ORDER = ["r0", "GATE", "r3", "r2", "r1", "r7", "r6", "r4", "r5"]


def sub(rung, arm):
    return f"fgo_{arm}" + (f"_{RUNGS[rung][4]['F_TAG']}" if RUNGS[rung][4] else "")


def jobs():
    out = []
    for r in ORDER:
        if r == "GATE":
            out.append("GATE"); continue
        for arm in RUNGS[r][3]:
            for t in BAGS:
                out.append(f"{r}__{t}__{arm}")
    return out


def parse(job):
    r, t, arm = job.split("__")
    folder = RUNGS[r][0]
    return r, t, arm, os.path.join(A, folder, t, sub(r, arm))
