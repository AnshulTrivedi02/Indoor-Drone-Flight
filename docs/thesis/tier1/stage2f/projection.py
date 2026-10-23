#!/usr/bin/env python3
"""Stage 2f: lock projection after each completed job (read-only on timing.tsv; cheap, no bag reads).
Remaining jobs x the mean measured driver wall time of completed jobs of the same class (window, cap). Classes with no
measurement yet: main W from the 1-flight ratio to the nearest measured smaller window x W ratio (linear), else the §8
planning figure (190/320/610/1180/2910 s at 0.25/0.5/1/2/5); lm10 = the measured cap-10 / cap-2 ratio at the same window
when one exists, else 5 x the cap-2 class mean (§8 upper bound). Prints one line: now, done, remaining, projected end,
margin to the 2026-11-04 23:59 AEDT lock."""
import datetime as dt, re, statistics as stt
S = "/home/makerspace/thesis_data/tier1/stage2f"
LOCK = dt.datetime.fromisoformat("2026-11-04T23:59:00+11:00")
PLAN = {0.25: 190, 0.5: 320, 1.0: 610, 2.0: 1180, 5.0: 2910}
order = open(f"{S}/order.txt").read().split()
done = {}
for ln in open(f"{S}/timing.tsv"):
    f = ln.rstrip("\n").split("\t")
    if len(f) >= 9 and f[8] in ("completed", "crashed", "NOT RUN", "timeout"):
        done[f[0]] = float(f[3]) if f[3] != "-" else 0.0
cls = lambda j: (float(re.search(r"_w([\d.]+)", j)[1]), j.endswith("_lm10"))
meas = {}
for j, w in done.items():
    meas.setdefault(cls(j), []).append(w)
m = {k: stt.mean(v) for k, v in meas.items()}
def est(k):
    W, lm = k
    if k in m: return m[k]
    base = m.get((W, False)) or PLAN[W]
    if lm:
        r = [m[(w, True)] / m[(w, False)] for (w, l) in m if l and (w, False) in m]
        return base * (max(r) if r else 5.0)
    return base
rem = [j for j in order if j not in done]
sec = sum(est(cls(j)) for j in rem)
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=11)))
end = now + dt.timedelta(seconds=sec)
print(f"{now.isoformat(timespec='seconds')} done {len(done)}/{len(order)} remaining {len(rem)} est {sec/3600:.1f} h "
      f"-> projected end {end.isoformat(timespec='minutes')}; margin to lock {(LOCK-end).total_seconds()/3600:.1f} h; "
      f"class means (s): " + ", ".join(f"w{k[0]:g}{'_lm10' if k[1] else ''}={v:.0f}(n={len(meas[k])})" for k, v in sorted(m.items())))
