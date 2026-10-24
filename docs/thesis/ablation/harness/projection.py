"""Finish-time projection: Step 0 per-rung projections (step0_report.md §3.2) scaled by the measured actual/projected
ratio (per rung where it has started, else the overall measured ratio)."""
import time, datetime
P = {"r0": 2957, "r3": 5914, "r2": 2957, "r1": 2957, "r7": 3364, "r6": 1682, "r4": 2957 * 486.3 / 141.3, "r5": 2957 * 964.8 / 141.3}
N = {r: (6 if r in ("r6", "r7") else 12) for r in P}
done = {r: [] for r in P}
for ln in open("/home/makerspace/thesis_data/ablation/timing.tsv"):
    p = ln.rstrip("\n").split("\t")
    if len(p) == 9 and p[8] == "completed":
        done[p[0].split("__")[0]].append(float(p[3]))
tot_a = sum(sum(v) for v in done.values()); tot_p = sum(P[r] * len(v) / N[r] for r, v in done.items())
g = tot_a / tot_p
rem = 0
for r in P:
    k = len(done[r]); ratio = (sum(done[r]) / (P[r] * k / N[r])) if k else g
    rem += P[r] * (N[r] - k) / N[r] * ratio
    print(f"{r}: {k}/{N[r]} done, {sum(done[r]):.0f} s, ratio {ratio:.2f}")
eta = datetime.datetime.now() + datetime.timedelta(seconds=rem)
print(f"overall ratio {g:.3f}; remaining ~{rem/3600:.1f} h; ETA {eta:%Y-%m-%d %H:%M} (lock 2026-11-04 23:59)")
