#!/usr/bin/env python3
"""Unit tests for eval/reph_inject.py (STAGE 1: no Replay; see the pre-registration's
"Injector" section). Builds small synthetic ArduPilot dataflash logs in the scratch
directory (never under ~/thesis_data/trials/) and checks:

  1. PARSE: pymavlink's DFReader (an independent reader from df_reader.py/reph_inject.py's
     own FMT-table walker) parses the synthetic log and recovers the same REPH field
     values this tool wrote -- a cross-check against a second implementation, not just
     our own round-trip.
  2. ROUND TRIP: strip(WITH_REPH) -> inject(records extracted from WITH_REPH) reproduces
     WITH_REPH byte-for-byte. This is the "mechanics" half of the pre-registered
     round-trip check; the Replay half (does the REPLAYED EKF3 reproduce field-for-field)
     needs Replay and is run later by the coordinator, not here.
  3. ZERO RECORDS: strip() on a log with no REPH rows at all produces a byte-identical
     copy of the input (checked on a tiny synthetic "no REPH" log AND, if present, on a
     real recorded trial's .bin known to have zero REPH rows -- the latter is skipped,
     not failed, if that trial directory is not present on this machine).
  4. REFUSALS: output path under trials/, output == input, an existing output file, a
     wrong REPH format/columns, and duplicate timeStamp_ms are all rejected (non-zero
     exit / exception), never silently handled.
  5. MULTI-INSERT ORDERING: several injected records landing in the same inter-frame
     gap, and one whose target time is past the log's last RFRH (appended at EOF), both
     reproduce the intended layout.

Usage (venv-ardupilot, for pymavlink):
  ~/venv-ardupilot/bin/python3 eval/reph_inject_test.py
Exits 0 iff every check passes; prints PASS/FAIL per check.
"""
import json, os, struct, sys, tempfile, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import df_reader as D
import reph_inject as R

RFRH_TY, RFRF_TY, REPH_TY, VISP_TY = 129, 130, 156, 157

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True, None))
        print(f"PASS  {name}")
    except Exception as e:
        RESULTS.append((name, False, f"{type(e).__name__}: {e}"))
        print(f"FAIL  {name}: {type(e).__name__}: {e}")
        traceback.print_exc()


def fmt_header():
    return (D.write_fmt(0x80, "FMT", "BBnNZ", "Type,Length,Name,Format,Columns")
            + D.write_fmt(RFRH_TY, "RFRH", "QI", "TimeUS,TF")
            + D.write_fmt(RFRF_TY, "RFRF", "BB", "FTypes,Slow")
            + D.write_fmt(VISP_TY, "VISP", "Q", "TimeUS")
            + D.write_fmt(REPH_TY, "REPH", R.REPH_EXPECT_FMT, R.REPH_EXPECT_COLS))


def rfrh(t_us, tf=1):
    return D.write_rec(RFRH_TY, "QI", t_us, tf)


def rfrf(ftypes=1, slow=0):
    return D.write_rec(RFRF_TY, "BB", ftypes, slow)


def visp(t_us):
    return D.write_rec(VISP_TY, "Q", t_us)


def reph_bytes(ts_ms, pos=(0.0, 0.0, 0.0), quat=(1.0, 0.0, 0.0, 0.0), poserr=100.0, angerr=0.05, rt=0, delay=25):
    """TS/RT are uint32 ms, D is uint16 ms (REPH_EXPECT_FMT 'IIH') -- real logs store
    timeStamp_ms as a whole millisecond, so round rather than truncate."""
    return D.write_rec(REPH_TY, R.REPH_EXPECT_FMT, *pos, *quat, poserr, angerr, int(round(ts_ms)), rt, delay)


def frame_sequence(n, start_us=1_000_000, step_us=12_500):
    """n frames of (RFRH, RFRF), no REPH -- the clean skeleton every test builds on."""
    out, t = b"", start_us
    for _ in range(n):
        out += rfrh(t) + rfrf()
        t += step_us
    return out


def build_with_reph():
    """20 frames (12.5 ms apart, the EKF prediction cadence this project pins
    elsewhere -- NOTE this is a coarser frame rate than the real logs' own RFRH cadence,
    which runs at the ~400 Hz IMU-frame rate; that only changes which absolute gap (in
    ms) separates a REPH from its target RFRH, not the placement MECHANICS this test
    checks, so the test picks a gap well inside one frame step rather than reproducing
    the real logs' 44-71 ms figure). REPH rows inserted exactly per the validated
    placement rule (in the inter-frame gap before frame k's RFRH, timestamp a little
    under one step earlier so exactly frame k, not an earlier one, is "the first RFRH
    after this timestamp"), ONE per gap, at frames 5 and 15. (The "two REPH sharing one
    gap" case -- 0.5% of the live template's rows -- is covered separately by
    build_with_double_delivery() / test_double_delivery_gap_not_byte_identical(): this
    tool's placement rule does not reproduce the live template byte-for-byte in that
    minority case, and that limitation is documented, not silently papered over here.)"""
    header = fmt_header()
    start_us, step_us, n = 1_000_000, 12_500, 20
    body = b""
    t = start_us
    inserted = []  # ts_ms values, in insertion order
    for k in range(n):
        if k in (5, 15):
            ts_ms = round((t - 1_000) / 1000.0)         # 1 ms before frame k (< 12.5 ms step)
            body += reph_bytes(ts_ms) + visp(t - 1000)
            inserted.append(ts_ms)
        body += rfrh(t) + rfrf()
        t += step_us
    return header + body, inserted, (start_us, step_us, n)


def build_with_double_delivery():
    """Same skeleton, but frame 10's gap holds TWO REPH+VISP pairs (the live template's
    0.5% double-delivery pattern: REPH, VISP, REPH, VISP, next RFRH)."""
    header = fmt_header()
    start_us, step_us, n = 1_000_000, 12_500, 20
    body = b""
    t = start_us
    inserted = []
    for k in range(n):
        if k == 10:
            ts_ms_a = round((t - 2_000) / 1000.0)        # 2 ms before frame k=10
            ts_ms_b = round((t - 1_000) / 1000.0)        # 1 ms before frame k=10 (same gap, later)
            body += reph_bytes(ts_ms_a) + visp(t - 1000) + reph_bytes(ts_ms_b) + visp(t - 900)
            inserted += [ts_ms_a, ts_ms_b]
        body += rfrh(t) + rfrf()
        t += step_us
    return header + body, inserted, (start_us, step_us, n)


def test_pymavlink_parses_reph():
    data, inserted, _ = build_with_reph()
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(data)
        path = f.name
    try:
        from pymavlink import mavutil
        m = mavutil.mavlink_connection(path)
        seen_ts = []
        while True:
            msg = m.recv_match(type=["REPH"])
            if msg is None:
                break
            seen_ts.append(msg.TS)
        assert len(seen_ts) == len(inserted), (len(seen_ts), len(inserted))
        for got, want in zip(seen_ts, sorted(inserted)):
            assert abs(got - want) < 1e-3, (got, want)
    finally:
        os.unlink(path)


def _roundtrip(data):
    with tempfile.TemporaryDirectory() as d:
        in_path = os.path.join(d, "in.bin")
        open(in_path, "wb").write(data)
        stripped = os.path.join(d, "stripped.bin")
        extracted = os.path.join(d, "records.json")
        R.roundtrip_extract(in_path, extracted)
        n_removed, _ = R.strip(in_path, stripped)
        reinjected = os.path.join(d, "reinjected.bin")
        records = json.load(open(extracted))
        if records:
            R.inject(stripped, reinjected, records)
        else:
            reinjected = stripped
        return open(in_path, "rb").read(), open(reinjected, "rb").read(), n_removed


def test_roundtrip_byte_identical():
    data, inserted, _ = build_with_reph()
    original, reinjected, n_removed = _roundtrip(data)
    assert n_removed == len(inserted), (n_removed, len(inserted))
    assert original == reinjected, (len(original), len(reinjected), "byte mismatch")


def test_zero_records_byte_identical_synthetic():
    data = fmt_header() + frame_sequence(10)
    with tempfile.TemporaryDirectory() as d:
        in_path = os.path.join(d, "in.bin")
        open(in_path, "wb").write(data)
        out_path = os.path.join(d, "out.bin")
        n_removed, byte_identical = R.strip(in_path, out_path)
        assert n_removed == 0
        assert byte_identical
        assert open(out_path, "rb").read() == data


def test_inject_zero_records_byte_identical():
    """The brief's literal "the injector with zero records leaves the log byte-identical"
    -- inject() called with an EMPTY records list, not strip() on an already-zero-REPH
    log (that is test_zero_records_byte_identical_synthetic, a different check: it
    exercises strip's removal-count-zero path, not inject's zero-length-input path,
    which used to raise instead (an early bug, fixed) because it fell through to Mode 2
    and demanded --placement-latency-ms for nothing to place."""
    data, _, _ = build_with_reph()  # a log that DOES have REPH rows, to make the check non-trivial
    with tempfile.TemporaryDirectory() as d:
        in_path = os.path.join(d, "in.bin")
        open(in_path, "wb").write(data)
        out_path = os.path.join(d, "out.bin")
        n = R.inject(in_path, out_path, [])
        assert n == 0
        assert open(out_path, "rb").read() == data

    real = os.path.expanduser("~/thesis_data/trials/fwdc_tex_r1/ardupilot.bin")
    if os.path.exists(real):
        with tempfile.TemporaryDirectory() as d:
            out_path = os.path.join(d, "out.bin")
            n = R.inject(real, out_path, [])
            assert n == 0
            assert open(out_path, "rb").read() == open(real, "rb").read()
    else:
        print("SKIP  (real fwdc_tex_r1 sub-check): not present on this machine")


def test_zero_records_real_log_if_present():
    """Same check against a real recorded trial known to have zero REPH rows, if this
    machine has it (eval/results/... does not pin a trial dir; skip, don't fail, if
    absent -- this is a bonus check, not the required synthetic one above)."""
    real = os.path.expanduser("~/thesis_data/trials/fwdc_tex_r1/ardupilot.bin")
    if not os.path.exists(real):
        print("SKIP  test_zero_records_real_log_if_present: fwdc_tex_r1 not present on this machine")
        return
    with tempfile.TemporaryDirectory() as d:
        out_path = os.path.join(d, "out.bin")
        n_removed, byte_identical = R.strip(real, out_path)
        assert n_removed == 0, n_removed
        assert byte_identical


def test_double_delivery_gap_reinjects_both_in_time_order():
    """Two REPH rows sharing one inter-frame gap: both reinjected records must land in
    that SAME gap (immediately after the RFRF before frame 10's RFRH, before frame 10's
    RFRH itself) and in ascending timeStamp_ms order -- but see
    test_double_delivery_gap_not_byte_identical for what this test deliberately does
    NOT require."""
    data, inserted, _ = build_with_double_delivery()
    with tempfile.TemporaryDirectory() as d:
        in_path = os.path.join(d, "in.bin")
        open(in_path, "wb").write(data)
        stripped, extracted = os.path.join(d, "stripped.bin"), os.path.join(d, "records.json")
        R.roundtrip_extract(in_path, extracted)
        R.strip(in_path, stripped)
        records = json.load(open(extracted))
        reinjected = os.path.join(d, "reinjected.bin")
        R.inject(stripped, reinjected, records)
        raw, recs2, reph_ty2, reph_f2, rfrh_f2 = R.load(reinjected)
        reph_idx = [k for k, (s, e, n, t) in enumerate(recs2) if n == "REPH"]
        assert len(reph_idx) == 2, reph_idx
        ts_vals = [reph_f2.struct.unpack_from(raw, recs2[k][0] + 3)[9] for k in reph_idx]
        assert ts_vals == sorted(ts_vals) == inserted, (ts_vals, inserted)
        # both sit in the same gap: nothing of type RFRH/RFRF appears strictly between them
        between = [recs2[j][2] for j in range(reph_idx[0] + 1, reph_idx[1])]
        assert all(nm not in ("RFRH", "RFRF") for nm in between), between


def test_double_delivery_gap_not_byte_identical():
    """DOCUMENTED LIMITATION (not a silent gap): when two REPH rows originally shared
    one inter-frame gap with other content (VISP) interleaved between them (REPH, VISP,
    REPH, VISP, next RFRH), this tool's placement rule reinjects both immediately after
    the preceding RFRF, so the reconstructed gap is (REPH, REPH, VISP, VISP, next RFRH)
    -- same gap, same relative order of the two REPH rows, but NOT byte-identical to
    the original interleaving. Confirmed against the live template
    (cl_bcpp_tex_r1_half): 12/2404 REPH rows (0.5%) are this double-delivery case, so
    this is the ONLY known source of round-trip byte divergence. Stated here and in
    docs/thesis/ekf3_heading_replay/preregistration.md ("Round-trip check") so the
    coordinator's later round-trip run expects it rather than treating it as a failure.
    It cannot affect arm (ii) (which only ever injects into gaps with zero pre-existing
    REPH/VISP content)."""
    data, inserted, _ = build_with_double_delivery()
    original, reinjected, n_removed = _roundtrip(data)
    assert n_removed == 2
    assert original != reinjected, "expected a byte difference in the double-delivery case (see docstring)"
    assert len(original) == len(reinjected)


def test_eof_append():
    header = fmt_header()
    start_us, step_us, n = 1_000_000, 12_500, 5
    body = frame_sequence(n, start_us, step_us)
    last_t = start_us + (n - 1) * step_us
    with tempfile.TemporaryDirectory() as d:
        in_path = os.path.join(d, "in.bin")
        open(in_path, "wb").write(header + body)
        out_path = os.path.join(d, "out.bin")
        late_ts_ms = (last_t + 1_000_000) / 1000.0  # far past the last RFRH
        R.inject(in_path, out_path, [{"timeStamp_ms": late_ts_ms, "pos": [0, 0, 0], "quat": [1, 0, 0, 0],
                                       "posErr": 100.0, "angErr": 0.05, "resetTime_ms": 0, "delay_ms": 25}],
                 placement_latency_ms=0.0)
        out = open(out_path, "rb").read()
        assert out[:len(header + body)] == header + body, "prefix must be untouched when appended at EOF"
        assert len(out) == len(header + body) + 49, (len(out), len(header + body))  # REPH record length


def test_mode2_timestamp_placement():
    """Mode 2 (no rfrf_count_before): requires placement_latency_ms; with the latency
    set to exactly match how build_with_reph() constructed its gaps (1 ms before the
    target frame), a freshly-synthesised record lands in the SAME gap a positionally
    round-tripped one would. Also checks the required-argument and duplicate-target
    refusals."""
    data, inserted, (start_us, step_us, n) = build_with_reph()
    with tempfile.TemporaryDirectory() as d:
        in_path = os.path.join(d, "in.bin")
        open(in_path, "wb").write(data)
        stripped = os.path.join(d, "stripped.bin")
        R.strip(in_path, stripped)

        # frame 5's time: start_us + 5*step_us; place a NEW record at frame-5-time - 1ms capture
        # timestamp, with placement_latency_ms=0 (so target_us == timeStamp_ms*1000 exactly matches
        # the gap this file's own frame-5 record used).
        frame5_us = start_us + 5 * step_us
        new_ts_ms = round((frame5_us - 1_000) / 1000.0)
        out1 = os.path.join(d, "out1.bin")
        try:
            R.inject(stripped, out1, [{"timeStamp_ms": new_ts_ms, "pos": [0, 0, 0], "quat": [1, 0, 0, 0],
                                        "posErr": 100.0, "angErr": 0.05, "resetTime_ms": 0, "delay_ms": 25}])
            raise AssertionError("expected refusal without --placement-latency-ms")
        except R.RephInjectError:
            pass
        assert not os.path.exists(out1)

        out2 = os.path.join(d, "out2.bin")
        R.inject(stripped, out2, [{"timeStamp_ms": new_ts_ms, "pos": [0, 0, 0], "quat": [1, 0, 0, 0],
                                    "posErr": 100.0, "angErr": 0.05, "resetTime_ms": 0, "delay_ms": 25}],
                 placement_latency_ms=0.0)
        raw, recs2, reph_ty2, reph_f2, _ = R.load(out2)
        reph_idx = [k for k, (s, e, nm, t) in enumerate(recs2) if nm == "REPH"]
        assert len(reph_idx) == 1
        assert recs2[reph_idx[0] - 1][2] == "RFRF", recs2[max(0, reph_idx[0] - 2):reph_idx[0] + 2]

        # duplicate targets refused
        out3 = os.path.join(d, "out3.bin")
        dup = [{"timeStamp_ms": new_ts_ms, "pos": [0, 0, 0], "quat": [1, 0, 0, 0], "posErr": 100.0,
                "angErr": 0.05, "resetTime_ms": 0, "delay_ms": 25}] * 2
        try:
            R.inject(stripped, out3, dup, placement_latency_ms=0.0)
            raise AssertionError("expected refusal for duplicate Mode-2 targets")
        except R.RephInjectError:
            pass
        assert not os.path.exists(out3)


def test_refusals():
    data = fmt_header() + frame_sequence(5)
    with tempfile.TemporaryDirectory() as d:
        in_path = os.path.join(d, "in.bin")
        open(in_path, "wb").write(data)

        # output == input
        try:
            R.strip(in_path, in_path)
            raise AssertionError("expected refusal for OUT == IN")
        except R.RephInjectError:
            pass

        # existing output file
        out_path = os.path.join(d, "out.bin")
        open(out_path, "wb").write(b"existing")
        try:
            R.strip(in_path, out_path)
            raise AssertionError("expected refusal for existing OUT.bin")
        except R.RephInjectError:
            pass

        # under trials/
        fake_trials_out = os.path.join(R.TRIALS_DIR, "reph_inject_test_should_not_exist.bin")
        try:
            R.strip(in_path, fake_trials_out)
            raise AssertionError("expected refusal for OUT under trials/")
        except R.RephInjectError:
            pass
        assert not os.path.exists(fake_trials_out)

        # duplicate Mode-2 targets (timeStamp_ms + placement_latency_ms) -- see also
        # test_mode2_timestamp_placement for the dedicated Mode-2 coverage
        out2 = os.path.join(d, "out2.bin")
        dup = [{"timeStamp_ms": 500.0, "pos": [0, 0, 0], "quat": [1, 0, 0, 0], "posErr": 100.0,
                "angErr": 0.05, "resetTime_ms": 0, "delay_ms": 25}] * 2
        try:
            R.inject(in_path, out2, dup, placement_latency_ms=0.0)
            raise AssertionError("expected refusal for duplicate timeStamp_ms")
        except R.RephInjectError:
            pass
        assert not os.path.exists(out2)

        # wrong REPH format
        bad_header = (D.write_fmt(0x80, "FMT", "BBnNZ", "Type,Length,Name,Format,Columns")
                      + D.write_fmt(RFRH_TY, "RFRH", "QI", "TimeUS,TF")
                      + D.write_fmt(RFRF_TY, "RFRF", "BB", "FTypes,Slow")
                      + D.write_fmt(REPH_TY, "REPH", "ffff", "PX,PY,PZ,Q1"))  # deliberately wrong
        bad_path = os.path.join(d, "bad.bin")
        open(bad_path, "wb").write(bad_header + frame_sequence(3))
        out3 = os.path.join(d, "out3.bin")
        try:
            R.strip(bad_path, out3)
            raise AssertionError("expected refusal for wrong REPH format")
        except R.RephInjectError:
            pass
        assert not os.path.exists(out3)


def main():
    check("pymavlink parses synthetic REPH rows", test_pymavlink_parses_reph)
    check("round trip (strip + reinject original records) byte-identical", test_roundtrip_byte_identical)
    check("zero records: synthetic log byte-identical after strip", test_zero_records_byte_identical_synthetic)
    check("inject() with an EMPTY records list is byte-identical (the brief's own wording)", test_inject_zero_records_byte_identical)
    check("zero records: real fwdc_tex_r1 byte-identical after strip (skips if absent)", test_zero_records_real_log_if_present)
    check("double-delivery gap: both reinjected in the same gap, time-ordered", test_double_delivery_gap_reinjects_both_in_time_order)
    check("double-delivery gap: documented non-byte-identical case", test_double_delivery_gap_not_byte_identical)
    check("insertion past the last RFRH appends at EOF, prefix untouched", test_eof_append)
    check("Mode 2 (timestamp + required latency) placement, and its refusals", test_mode2_timestamp_placement)
    check("refusals (OUT==IN, existing OUT, trials/ path, duplicate TS, bad REPH fmt)", test_refusals)
    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"\n{len(RESULTS) - n_fail}/{len(RESULTS)} checks passed")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
