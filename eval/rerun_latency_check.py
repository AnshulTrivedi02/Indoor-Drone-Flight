#!/usr/bin/env python3
"""EKF3 flow latency (DIAGNOSTIC) for every re-flown trial, against the pre-registered P2 band
(user request 2026-09-29): same-world OLD dsn mean + 12.5 ms for the median and the p95, and
matched frames >= same-world old dsn minimum - 5 pp (METHODOLOGY Phase 1/2 "P2"). The old dsn
references are the pre-re-run input_timing_linmap.json (read before the pipeline overwrites
it; the pipeline snapshots it to eval/results_pre_rerun/). RTF moves only wall-clock time in
the lockstep sim, but the flow/camera bridges and ArduPilot's arrival stamping run on the wall
clock, so RTF can move this latency; dsn_trans_r1 / dsn_trans_r2 (RTF 0.956 / 0.931) are
flagged specifically.
Usage: python3 eval/rerun_latency_check.py TIMING_JSON [--ref OLD_LINMAP_JSON] [--json OUT]
  TIMING_JSON = eval/input_timing.py --json output on the re-flown trials."""
import argparse, json, os, statistics as st
ap = argparse.ArgumentParser(); ap.add_argument("timing")
ap.add_argument("--ref", default=None); ap.add_argument("--json"); a = ap.parse_args()
here = os.path.dirname(os.path.abspath(__file__))
ref_path = a.ref or (os.path.join(here, "results_pre_rerun", "input_timing_linmap.json")
                     if os.path.exists(os.path.join(here, "results_pre_rerun", "input_timing_linmap.json"))
                     else os.path.join(here, "results", "input_timing_linmap.json"))
ref, it = json.load(open(ref_path)), json.load(open(a.timing))
world = lambda t: next(x for x in t.split("_") if x in ("tex", "trans", "blank"))
band = {}
for w in ("tex", "trans", "blank"):
    d = [ref[f"dsn_{w}_r{r}"]["flow_to_ekf3"] for r in (1, 2, 3)]
    band[w] = {"median_max": st.mean(x["lat_median_ms"] for x in d) + 12.5, "p95_max": st.mean(x["lat_p95_ms"] for x in d) + 12.5,
               "matched_min": min(x["matched_pct"] for x in d) - 5}
out = {"ref": ref_path, "band": band, "trials": {}}
print(f"reference: {ref_path}")
for w, b in band.items():
    print(f"  band {w}: median <= {b['median_max']:.1f} ms, p95 <= {b['p95_max']:.1f} ms, matched >= {b['matched_min']:.1f}%")
nout = 0
nund = 0
fmt = lambda x, w=5: "n/a".rjust(w) if x is None else f"{x:{w}.1f}"
for t, v in sorted(it.items()):
    f = v["flow_to_ekf3"]; q = v.get("flow_to_ekf3_quality_gt0", {}); b = band[world(t)]
    flag = "  <-- flagged (RTF dip)" if t in ("dsn_trans_r1", "dsn_trans_r2") else ""
    if f["lat_median_ms"] is None:
        ok = None; nund += 1; verdict = f"UNDEFINED (0 of {f['valid_frames']} valid frames in cruise)"
    else:
        ok = f["lat_median_ms"] <= b["median_max"] and f["lat_p95_ms"] <= b["p95_max"] and f["matched_pct"] >= b["matched_min"]
        nout += not ok; verdict = "in band" if ok else "OUTSIDE BAND"
    print(f"{t:22} [valid] median {fmt(f['lat_median_ms'])}  p95 {fmt(f['lat_p95_ms'])}  matched {fmt(f['matched_pct'])}%  {verdict}{flag}"
          f"   | [quality>0, n {q.get('valid_frames', 0)}] median {fmt(q.get('lat_median_ms'))} p95 {fmt(q.get('lat_p95_ms'))}")
    out["trials"][t] = {"valid": {k: f[k] for k in ("lat_median_ms", "lat_p95_ms", "matched_pct", "valid_frames")}, "in_band": ok,
                        "quality_gt0": {k: q.get(k) for k in ("lat_median_ms", "lat_p95_ms", "matched_pct", "valid_frames")}}
print(f"{nund} trial(s) with P2 undefined (no valid frames)")
print(f"{nout} trial(s) outside band (DIAGNOSTIC)")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
