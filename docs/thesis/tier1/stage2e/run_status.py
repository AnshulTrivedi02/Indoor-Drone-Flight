#!/usr/bin/env python3
"""Stage 2e STEP 2 (coordinator ruling 2026-10-22): per-run estimator-failure status, post hoc, read-only on outputs.
For each finished E3 run: keyframe_failures (stats.json), failure fraction = keyframe_failures / (keyframes +
keyframe_failures) (stats.json `keyframes` counts successful keyframes, `keyframe_failures` the caught exceptions;
together they are all keyframe attempts), time of the first failure (first '[warn] keyframe T:' line of the job log),
the exception types and counts, and whether live.tum / hindsight.tum contain any non-finite value.
STATUS = FAILED-ESTIMATOR if keyframe_failures > 0 or any non-finite value; else OK (as ruled). The live excursion onset
(first live row with |x| or |y| > 10 m, or non-finite) is DESCRIPTIVE only and does not set the status. Never edits a run.
Usage: run_status.py <job name> [<job name> ...]   (job names as in order.txt; logs in stage2e/logs/ or the given --log)
Writes stage2e/status/<job>.json (overwritten) and prints one TSV line per job."""
import json, math, os, re, sys, collections
S = "/home/makerspace/thesis_data/tier1/stage2e"; T1 = "/home/makerspace/thesis_data/tier1"
BASE = "_t245_tags0-1-2-3-4-5-6-7"; ROB = "_robcauchy2.385"


def run_dir(job):
    m = re.fullmatch(r"e3([ab])_(T_A_r\d)_(0|0\.01|0\.05)(?:_s(\d))?(?:_(cf.*))?", job)
    arm, t, p, s, cf = m.groups()
    suf = BASE + ("" if p == "0" else f"_mis{p}_s{s}") + (ROB if arm == "b" else "")
    return f"{T1}/{t}/lc_fgo_lc{suf}", t


def status(job, log=None, rdir=None):
    if rdir is None:
        rdir, _ = run_dir(job)
    log = log or f"{S}/logs/{job}.log"
    st = json.load(open(f"{rdir}/stats.json"))
    nf, nk = st["keyframe_failures"], st["keyframes"]
    first, kinds = None, collections.Counter()
    for ln in open(log, errors="replace"):
        m = re.match(r"\[warn\] keyframe ([\d.]+): (\w+)", ln)
        if m:
            kinds[m[2]] += 1
            if first is None:
                first = float(m[1])
    nonfinite = {}
    for f in ("live.tum", "hindsight.tum"):
        bad = 0; rows = 0
        for ln in open(f"{rdir}/{f}"):
            rows += 1
            if any(not math.isfinite(float(x)) for x in ln.split()):
                bad += 1
        nonfinite[f] = {"rows": rows, "rows_nonfinite": bad}
    anynf = any(v["rows_nonfinite"] for v in nonfinite.values())
    div = None                       # divergence onset: first live row with |x| or |y| > 10 m (room ~ 0..6.5 m) or non-finite
    for ln in open(f"{rdir}/live.tum"):
        v = [float(x) for x in ln.split()]
        if not all(math.isfinite(x) for x in v) or max(abs(v[1]), abs(v[2])) > 10.0:
            div = v[0]; break
    d = {"job": job, "run_dir": rdir, "log": log, "keyframes_ok": nk, "keyframe_failures": nf,
         "failure_fraction": nf / (nk + nf) if nk + nf else None, "first_failure_t_s": first,
         "live_excursion_onset_t_s (|x| or |y| > 10 m, or non-finite; DESCRIPTIVE)": div,
         "exception_counts_in_log": dict(kinds), "log_warn_count == keyframe_failures": sum(kinds.values()) == nf,
         "nonfinite": nonfinite, "status": "FAILED-ESTIMATOR" if (nf > 0 or anynf) else "OK"}
    os.makedirs(f"{S}/status", exist_ok=True)
    json.dump(d, open(f"{S}/status/{job}.json", "w"), indent=1)
    print("\t".join(str(x) for x in (job, d["status"], nf, nk, f"{d['failure_fraction']:.4f}", first, div,
                                     dict(kinds), {k: v["rows_nonfinite"] for k, v in nonfinite.items()})))
    return d


if __name__ == "__main__":
    for j in sys.argv[1:]:
        status(j)
