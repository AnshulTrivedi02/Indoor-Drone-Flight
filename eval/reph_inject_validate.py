#!/usr/bin/env python3
"""Full-scale, read-only validation of eval/reph_inject.py's placement mechanism against
a real log with live REPH rows (the closed-loop heading template). Reproduces the
findings cited in docs/thesis/ekf3_heading_replay/preregistration.md ("Injector" /
"round-trip check") as a committed, re-runnable script -- not just this session's
scratch output, which disappears with the session.

Checks, all against the SAME log (default: cl_bcpp_tex_r1_half):
  1. VISP.TimeUS, for every REPH row, equals the time_us of the RFRH immediately
     preceding it (file order) -- exactly, not approximately. This is what makes
     Mode 2's search-and-cut mechanism checkable against real per-record arrival
     times, not just Mode 1's stored-position restore.
  2. Mode 1 (positional) round trip: strip + reinject using each row's own
     rfrf_count_before. Byte-identical count/percentage reported.
  3. Mode 2 round trip, driven by each row's OWN exact VISP.TimeUS as its target (NOT
     timeStamp_ms + a shared --placement-latency-ms -- that is the separate, still-open
     "how does arm (ii) compute arrival" question). Uses reph_inject's own internal
     _rfrh_targets / _gap_cut_before_rfrh / encode_reph, the same code Mode 2's public
     `inject()` calls, just given a per-record exact target instead of one shared
     latency.
  4. Residual cluster analysis: for every byte-level difference between original and
     reinjected, finds the nearest preceding REPH and reports what record type
     immediately precedes THAT REPH in the original (the mechanism, not just the count).

Checks 1-4 all replay history that already exists in cl_bcpp_tex_r1_half, which is NOT
what arm (ii) will do (it injects into a log with ZERO prior REPH/ext-nav history).
--generalization-trial (default: fwdc_tex_r1, a real Phase-4 bag with 0 REPH rows) adds:
  5. Mode 2 placement on a log with NO REPH history at all: inject N (default 20)
     evenly-spaced synthetic records (placement_latency_ms=0) and report each one's
     neighbours. PASS iff every injected record is immediately preceded by RFRF and
     immediately followed by either RFRH or a record that itself calls end_frame()
     (ROFH, REV2, REV3, ...) -- i.e. the same "RFRH, RFRF, REPH, <next>" pattern found
     throughout cl_bcpp_tex_r1_half, not something different on a zero-history log.
     Also reports how often an RFRF in this log is NOT immediately followed by RFRH
     (other content landing in the gap, same phenomenon as cl_bcpp_tex_r1_half's slow
     stretches, checked here to confirm it is not specific to ext-nav-carrying logs).

Writes JSON to --out (default: ~/thesis_data/ekf3_heading_replay/reph_inject_validate.json)
-- never under ~/thesis_data/trials/, enforced the same way reph_inject.py enforces it.

Usage: ~/venv-ardupilot/bin/python3 eval/reph_inject_validate.py [--trial NAME] [--out PATH]
       [--generalization-trial NAME] [--n-synthetic N]
"""
import argparse, bisect, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import df_reader as D
import reph_inject as R

TRIALS_DIR = os.path.realpath(os.path.expanduser("~/thesis_data/trials"))


def _visp_fmt(data, recs):
    cur = {D.FMT_TYPE: D._Fmt(D.FMT_TYPE, D.FMT_LEN, "FMT", "BBnNZ", "Type,Length,Name,Format,Columns")}
    visp_f = None
    for start, end, name, ty in recs:
        if name and name.startswith("FMT("):
            tyval, ln, nm, fmt, cols = cur[D.FMT_TYPE].struct.unpack_from(data, start + 3)
            nf = D._Fmt(tyval, ln, D._cstr(nm), D._cstr(fmt), D._cstr(cols))
            cur[tyval] = nf
            if nf.name == "VISP":
                visp_f = nf
    return visp_f


def check_visp_matches_preceding_rfrh(data, recs, reph_f, rfrh_f):
    visp_f = _visp_fmt(data, recs)
    if visp_f is None:
        return {"error": "VISP not declared in this log"}
    rfrh_rec_idx = [k for k, (s, e, nm, ty) in enumerate(recs) if nm == "RFRH"]
    rfrh_time = {k: rfrh_f.struct.unpack_from(data, recs[k][0] + 3)[0] for k in rfrh_rec_idx}
    reph_rec_idx = [k for k, (s, e, nm, ty) in enumerate(recs) if nm == "REPH"]
    mismatches = []
    for k in reph_rec_idx:
        assert recs[k + 1][2] == "VISP", (k, recs[k + 1])
        visp_time_us = visp_f.struct.unpack_from(data, recs[k + 1][0] + 3)[0]
        pos = bisect.bisect_right(rfrh_rec_idx, k)
        rfrh_before = rfrh_time[rfrh_rec_idx[pos - 1]] if pos > 0 else None
        if rfrh_before is None or visp_time_us != rfrh_before:
            mismatches.append({"rec_idx": k, "visp_time_us": visp_time_us, "rfrh_before": rfrh_before})
    return {"n_reph": len(reph_rec_idx), "n_mismatches": len(mismatches), "mismatches": mismatches[:20],
            "exact_match": len(mismatches) == 0}


def mode1_roundtrip(orig_path, scratch_dir):
    stripped = os.path.join(scratch_dir, "m1_stripped.bin")
    extracted = os.path.join(scratch_dir, "m1_records.json")
    R.roundtrip_extract(orig_path, extracted)
    R.strip(orig_path, stripped)
    records = json.load(open(extracted))
    reinjected = os.path.join(scratch_dir, "m1_reinjected.bin")
    if records:
        R.inject(stripped, reinjected, records)
    else:
        reinjected = stripped
    orig = open(orig_path, "rb").read()
    reinj = open(reinjected, "rb").read()
    return _byte_report(orig, reinj), reinj if len(orig) == len(reinj) else None


def mode2_roundtrip_exact_arrival(orig_path, scratch_dir):
    """Mode 2's ACTUAL code (_rfrh_targets / _gap_cut_before_rfrh / encode_reph), fed
    each record's own exact VISP.TimeUS as its target -- bypassing the public inject()
    API's single shared placement_latency_ms, which cannot express a per-record exact
    arrival. See module docstring item 3."""
    odata, orecs, oreph_ty, oreph_f, orfrh_f = R.load(orig_path)
    visp_f = _visp_fmt(odata, orecs)
    records = R.decode_reph(odata, orecs, oreph_ty, oreph_f)
    reph_rec_indices = [k for k, (s, e, nm, ty) in enumerate(orecs) if nm == "REPH"]
    assert len(reph_rec_indices) == len(records)
    targets_us = []
    for rec, k in zip(records, reph_rec_indices):
        assert orecs[k + 1][2] == "VISP"
        targets_us.append(visp_f.struct.unpack_from(odata, orecs[k + 1][0] + 3)[0])
        del rec["_offset"], rec["rfrf_count_before"]

    stripped_path = os.path.join(scratch_dir, "m2_stripped.bin")
    if not os.path.exists(stripped_path):
        R.strip(orig_path, stripped_path)
    sdata, srecs, sreph_ty, sreph_f, srfrh_f = R.load(stripped_path)
    rfrh_entries = R._rfrh_targets(sdata, srecs, srfrh_f)
    rfrf_ends = R._rfrf_ends(srecs)

    dup = len(set(targets_us)) != len(targets_us)
    order = sorted(range(len(records)), key=lambda i: targets_us[i])
    plan, ptr = [], 0
    for i in order:
        while ptr < len(rfrh_entries) and rfrh_entries[ptr][0] <= targets_us[i]:
            ptr += 1
        cut = R._gap_cut_before_rfrh(rfrf_ends, rfrh_entries[ptr][1]) if ptr < len(rfrh_entries) else None
        plan.append((cut, records[i]))

    pieces, prev_end, appended = [], 0, []
    for cut, rec in plan:
        if cut is None:
            appended.append(rec)
            continue
        assert cut >= prev_end, (cut, prev_end)
        pieces.append(sdata[prev_end:cut])
        pieces.append(R.encode_reph(rec, sreph_ty, sreph_f))
        prev_end = cut
    pieces.append(sdata[prev_end:])
    for rec in appended:
        pieces.append(R.encode_reph(rec, sreph_ty, sreph_f))
    out = b"".join(pieces)
    odata_full = open(orig_path, "rb").read()
    report = _byte_report(odata_full, out)
    report["duplicate_exact_targets"] = dup
    report["appended_at_eof"] = len(appended)
    return report, out if len(odata_full) == len(out) else None


def _byte_report(a, b):
    if len(a) != len(b):
        return {"len_a": len(a), "len_b": len(b), "byte_identical": False, "lengths_differ": True}
    n_diff = sum(1 for x, y in zip(a, b) if x != y)
    return {"len": len(a), "bytes_differing": n_diff, "pct_differing": 100 * n_diff / len(a),
            "byte_identical": n_diff == 0}


def residual_clusters(orig_path, reinjected_bytes):
    data, recs, reph_ty, reph_f, rfrh_f = R.load(orig_path)
    if reinjected_bytes is None or len(reinjected_bytes) != len(data):
        return {"error": "length mismatch; cannot do a byte-level residual analysis"}
    diffs = [i for i in range(len(data)) if data[i] != reinjected_bytes[i]]
    if not diffs:
        return {"n_clusters": 0, "clusters": []}
    clusters, cur = [], [diffs[0]]
    for x in diffs[1:]:
        if x - cur[-1] > 1000:
            clusters.append((cur[0], cur[-1]))
            cur = [x]
        else:
            cur.append(x)
    clusters.append((cur[0], cur[-1]))
    reph_rec_idx = [k for k, (s, e, nm, ty) in enumerate(recs) if nm == "REPH"]
    reph_offsets = [recs[k][0] for k in reph_rec_idx]
    out = []
    for c0, c1 in clusters:
        pos = bisect.bisect_right(reph_offsets, c1)
        near_k = reph_rec_idx[pos - 1] if pos > 0 else None
        context = [recs[near_k + i][2] for i in range(-2, 4)] if near_k is not None else None
        out.append({"cluster": [c0, c1], "len": c1 - c0 + 1, "nearest_reph_rec_idx": near_k,
                    "nearest_reph_offset": recs[near_k][0] if near_k is not None else None, "context": context})
    return {"n_clusters": len(clusters), "clusters": out}


END_FRAME_CALLERS = {"RFRH", "ROFH", "REPH", "RSLL", "REVH", "RWOH", "RBOH", "RTER", "REV2", "REV3"}
# Every DAL record type whose write function calls end_frame() first, per AP_DAL.cpp's
# own end_frame() docstring ("Must be called on all events and injections of data") --
# read for each one in AP_DAL.cpp (WRITE_REPLAY_BLOCK[_IFCHANGED] calls preceded by
# end_frame()), not assumed from the docstring's examples alone.


def generalization_check(trial, n_synthetic):
    """Mode 2 on a log with ZERO REPH history -- see module docstring item 5."""
    path = os.path.expanduser(f"~/thesis_data/trials/{trial}/ardupilot.bin")
    if not os.path.exists(path):
        return {"error": f"{path} does not exist"}
    data, recs, reph_ty, reph_f, rfrh_f = R.load(path)
    n_existing_reph = sum(1 for r in recs if r[2] == "REPH")
    n_rfrh = sum(1 for r in recs if r[2] == "RFRH")
    n_rfrf = sum(1 for r in recs if r[2] == "RFRF")
    n_rfrf_not_followed_by_rfrh = sum(
        1 for k, (s, e, nm, ty) in enumerate(recs)
        if nm == "RFRF" and (k + 1 >= len(recs) or recs[k + 1][2] != "RFRH"))

    rfrh_times = [rfrh_f.struct.unpack_from(data, s + 3)[0] for s, e, nm, ty in recs if nm == "RFRH"]
    step = max(1, len(rfrh_times) // (n_synthetic + 2))
    records = []
    for i in range(1, n_synthetic + 1):
        t_us = rfrh_times[i * step]
        ts_ms = round((t_us - 100) / 1000.0)  # 0.1 ms before this frame
        records.append({"timeStamp_ms": ts_ms, "pos": [0.0, 0.0, 0.0], "quat": [1.0, 0.0, 0.0, 0.0],
                         "posErr": 100.0, "angErr": 0.05, "resetTime_ms": 0, "delay_ms": 25})

    with tempfile.TemporaryDirectory() as d:
        out_path = os.path.join(d, "out.bin")
        R.inject(path, out_path, records, placement_latency_ms=0.0)
        odata2, orecs2, oreph_ty2, oreph_f2, orfrh_f2 = R.load(out_path)
        reph_idx2 = [k for k, r in enumerate(orecs2) if r[2] == "REPH"]
        placements = []
        all_sane = True
        for k in reph_idx2:
            before = orecs2[k - 1][2] if k > 0 else None
            after = orecs2[k + 1][2] if k + 1 < len(orecs2) else None
            sane = before == "RFRF" and after in END_FRAME_CALLERS
            all_sane = all_sane and sane
            placements.append({"offset": orecs2[k][0], "before": before, "after": after, "sane": sane})

    return {"trial": trial, "n_existing_reph": n_existing_reph, "n_rfrh": n_rfrh, "n_rfrf": n_rfrf,
            "rfrf_not_followed_by_rfrh": n_rfrf_not_followed_by_rfrh,
            "rfrf_not_followed_by_rfrh_pct": 100 * n_rfrf_not_followed_by_rfrh / n_rfrf if n_rfrf else None,
            "n_synthetic_injected": len(records), "n_found": len(reph_idx2),
            "all_placements_sane": all_sane, "placements": placements}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial", default="cl_bcpp_tex_r1_half")
    ap.add_argument("--out", default=os.path.expanduser("~/thesis_data/ekf3_heading_replay/reph_inject_validate.json"))
    ap.add_argument("--generalization-trial", default="fwdc_tex_r1")
    ap.add_argument("--n-synthetic", type=int, default=20)
    a = ap.parse_args()

    out_real = os.path.realpath(a.out)
    if out_real == TRIALS_DIR or out_real.startswith(TRIALS_DIR + os.sep):
        raise SystemExit(f"refusing: --out is under {TRIALS_DIR} (never write there)")
    os.makedirs(os.path.dirname(out_real), exist_ok=True)

    orig_path = os.path.expanduser(f"~/thesis_data/trials/{a.trial}/ardupilot.bin")
    if not os.path.exists(orig_path):
        raise SystemExit(f"{orig_path} does not exist")

    report = {"trial": a.trial, "input": orig_path}
    with tempfile.TemporaryDirectory() as scratch:
        data, recs, reph_ty, reph_f, rfrh_f = R.load(orig_path)
        report["visp_check"] = check_visp_matches_preceding_rfrh(data, recs, reph_f, rfrh_f)
        m1_report, m1_bytes = mode1_roundtrip(orig_path, scratch)
        report["mode1_roundtrip"] = m1_report
        report["mode1_residual"] = residual_clusters(orig_path, m1_bytes)
        m2_report, m2_bytes = mode2_roundtrip_exact_arrival(orig_path, scratch)
        report["mode2_exact_arrival_roundtrip"] = m2_report
        report["mode2_residual"] = residual_clusters(orig_path, m2_bytes)

    if a.generalization_trial:
        report["generalization_check"] = generalization_check(a.generalization_trial, a.n_synthetic)

    json.dump(report, open(out_real, "w"), indent=1)
    summary = {k: v for k, v in report.items() if k != "trial"}
    if "generalization_check" in summary:
        summary["generalization_check"] = {k: v for k, v in summary["generalization_check"].items() if k != "placements"}
    print(json.dumps(summary, indent=1)[:5000])
    print(f"-> {out_real}")


if __name__ == "__main__":
    main()
