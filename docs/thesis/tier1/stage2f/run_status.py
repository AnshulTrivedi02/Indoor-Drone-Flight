#!/usr/bin/env python3
"""Stage 2f (E4): per-run estimator-failure status, post hoc, read-only on outputs (the stage2e rule, ported to
room_fgo_replay.py outputs).
For each finished E4 run: keyframe_failures (stats.json), keyframe attempts = stats.json tier1.n_steps (one entry per
attempt, failures included), failure fraction = failures / attempts, first failure time and exception types from the
job log ('[warn] keyframe at T failed: Type: ...'), and whether fgo_live.tum has any non-finite value (the only track;
--no-batch). The log warn count must equal keyframe_failures (reported).
STATUS = FAILED-ESTIMATOR if keyframe_failures > 0 or any non-finite value; else OK. The live excursion onset (first
live row with |x| or |y| > 10 m, or non-finite) is DESCRIPTIVE only. Never edits a run.
Usage: run_status.py <job> [<job> ...]  (job names as in order.txt; e4_<trial>_w<W>[_lm10], or e4_<trial>_w0.25 for the
stage2a reference runs, whose logs are in stage2a/logs/ge4_<trial>.log)
Writes stage2f/status/<job>.json (overwritten) and prints one TSV line per job."""
import json, math, os, re, sys, collections
S = "/home/makerspace/thesis_data/tier1/stage2f"; T1 = "/home/makerspace/thesis_data/tier1"


def run_dir(job):
    m = re.fullmatch(r"e4_(T_[A-D]_r\d)_w([\d.]+)(_lm10)?", job)
    t, w, lm = m.groups()
    return f"{T1}/{t}/room_fgo_w{float(w):g}{lm or ''}", t


def log_of(job):
    m = re.fullmatch(r"e4_(T_[A-D]_r\d)_w0\.25", job)
    return f"{T1}/stage2a/logs/ge4_{m[1]}.log" if m else f"{S}/logs/{job}.log"


def status(job):
    rdir, _ = run_dir(job); log = log_of(job)
    st = json.load(open(f"{rdir}/stats.json"))
    nf, na = st["keyframe_failures"], st["tier1"]["n_steps"]
    first, kinds = None, collections.Counter()
    for ln in open(log, errors="replace"):
        m = re.match(r"\[warn\] keyframe at ([\d.]+) failed: (\w+)", ln)
        if m:
            kinds[m[2]] += 1
            if first is None:
                first = float(m[1])
    rows = bad = 0; div = None
    for ln in open(f"{rdir}/fgo_live.tum"):
        rows += 1; v = [float(x) for x in ln.split()]
        fin = all(math.isfinite(x) for x in v)
        bad += (not fin)
        if div is None and (not fin or max(abs(v[1]), abs(v[2])) > 10.0):
            div = v[0]
    d = {"job": job, "run_dir": rdir, "log": log, "keyframe_attempts": na, "keyframe_failures": nf,
         "failure_fraction": nf / na if na else None, "first_failure_t_s": first,
         "live_excursion_onset_t_s (|x| or |y| > 10 m, or non-finite; DESCRIPTIVE)": div,
         "exception_counts_in_log": dict(kinds), "log_warn_count == keyframe_failures": sum(kinds.values()) == nf,
         "fgo_live_rows": rows, "fgo_live_rows_nonfinite": bad,
         "status": "FAILED-ESTIMATOR" if (nf > 0 or bad > 0) else "OK"}
    os.makedirs(f"{S}/status", exist_ok=True)
    json.dump(d, open(f"{S}/status/{job}.json", "w"), indent=1)
    print("\t".join(str(x) for x in (job, d["status"], nf, na, f"{d['failure_fraction']:.4f}", first, div, dict(kinds),
                                     bad, d["log_warn_count == keyframe_failures"])))
    return d


if __name__ == "__main__":
    for j in sys.argv[1:]:
        status(j)
