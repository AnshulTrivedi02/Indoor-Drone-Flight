#!/usr/bin/env python3
"""Runtime estimate for the FGO-only pass (FINAL_FGO_ONLY=1) from the full re-run's own records (2026-10-09/10):
per-job wall times from ~/thesis_data/batches/final_*/jobs.log, classified UKF / FGO by the job's COMMAND in the vendored
list (ukf_replay.py / room_ukf_replay.py = UKF), re-scheduled on PAR = 6 workers (longest-processing-time first). Stage
wall times without job lists come from ~/thesis_data/batches/final_rerun/pipeline.log. Light; standard library only."""
import datetime, os, re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
B = os.path.expanduser("~/thesis_data/batches")
LISTS = {"phase4": "batches/phase4_replays.jobs", "phase5b": f"{B}/final_rerun/phase5b_clean.jobs",
         "F": "batches/final_rerun/F.jobs", "f4": "batches/f4_replays_usable.jobs", "room_H": "batches/final_rerun/room_H.jobs",
         "room_O": "batches/final_rerun/room_O.jobs", "room_T": "batches/final_rerun/room_T.jobs",
         "L": "batches/final_rerun/L.jobs", "cl_pred": "batches/final_rerun/cl_pred.jobs"}
STAGE_OF = {"phase4": "phase4", "phase5b": "phase5b", "F": "ftests", "f4": "f4", "room_H": "h_shadows", "room_O": "expO",
            "room_T": "expT", "L": "L", "cl_pred": "cl_pred"}
UKF = re.compile(r"ukf_replay\.py")


def durations(f):
    st, dur = {}, {}
    for l in open(f):
        m = re.match(r"(\S+)\s+(START|DONE|FAILED)\s+(\S+)", l)
        if not m:
            continue
        t = datetime.datetime.fromisoformat(m.group(1))
        if m.group(2) == "START":
            st[m.group(3)] = t
        elif m.group(3) in st:
            dur[m.group(3)] = (t - st[m.group(3)]).total_seconds()
    return dur


def lpt(v, n=6):
    w = [0.0] * n
    for x in sorted(v, reverse=True):
        w[w.index(min(w))] += x
    return max(w) if v else 0.0


def stage_walls():
    beg, out = {}, {}
    for l in open(f"{B}/final_rerun/pipeline.log"):
        m = re.match(r"(\S+)\s+(BEGIN|DONE)\s+(\S+)", l)
        if m:
            t = datetime.datetime.fromisoformat(m.group(1))
            if m.group(2) == "BEGIN":
                beg[m.group(3)] = t
            elif m.group(3) in beg:
                out[m.group(3)] = (t - beg[m.group(3)]).total_seconds()
    return out


sw = stage_walls()
new = dict(sw)
print(f"{'batch':9} {'FGO jobs':>8} {'FGO cpu-h':>9} {'UKF jobs':>8} {'UKF cpu-h':>9} {'stage wall old':>14} {'jobs LPT old':>12} {'FGO-only LPT':>12}")
for k, lf in LISTS.items():
    cmd = {}
    for l in open(lf if os.path.isabs(lf) else os.path.join(REPO, lf)):
        l = l.strip()
        if l and not l.startswith("#"):
            j, c = l.split(None, 1)
            cmd[j] = c
    d = durations(f"{B}/final_{k}/jobs.log")
    fg = [v for j, v in d.items() if not UKF.search(cmd.get(j, ""))]
    uk = [v for j, v in d.items() if UKF.search(cmd.get(j, ""))]
    s = STAGE_OF[k]
    old_jobs, new_jobs = lpt(fg + uk), lpt(fg)
    new[s] = sw.get(s, 0) - old_jobs + new_jobs          # stage wall minus the jobs' old LPT wall plus the FGO-only LPT wall
    print(f"{k:9} {len(fg):8d} {sum(fg)/3600:9.2f} {len(uk):8d} {sum(uk)/3600:9.2f} {sw.get(s, 0)/60:13.1f}m {old_jobs/60:11.1f}m {new_jobs/60:11.1f}m")
# run_set_eval stages (dsn, dsn_extra, set_*): UKF replays ~0.37x of the FGO's in Phase 4 (cpu-h above); without per-job
# records, take the FGO share of the replay step as FGO/(FGO+UKF) cpu of Phase 4 and assume the whole stage is replay-bound
d4 = durations(f"{B}/final_phase4/jobs.log")
c4 = {l.split(None, 1)[0]: l.split(None, 1)[1] for l in open(os.path.join(REPO, LISTS["phase4"])) if l.strip() and not l.startswith("#")}
f4c = sum(v for j, v in d4.items() if not UKF.search(c4[j])); u4c = sum(v for j, v in d4.items() if UKF.search(c4[j]))
share = f4c / (f4c + u4c)
for s in ("dsn", "dsn_extra", "set_p1c", "set_fwdc", "set_fwdplainc"):
    new[s] = sw.get(s, 0) * max(share, 1.0 / 4)    # xargs -P 4: the FGO replays alone still need >= 1/4 of the slots
print(f"run_set_eval stages scaled by the Phase 4 FGO cpu share {share:.2f}")
tot_old = sum(sw.values()); opt = ("d27item3", "cl_pred")
print(f"full re-run (pipeline.log): {tot_old/3600:.2f} h incl. opt-in {sum(sw.get(s, 0) for s in opt)/3600:.2f} h")
tot_new = sum(v for s, v in new.items() if s not in opt)
print(f"FGO-only pass estimate WITHOUT opt-in d27item3/cl_pred: {tot_new/3600:.2f} h; with them: "
      f"{(tot_new + sum(new.get(s, 0) for s in opt))/3600:.2f} h")
