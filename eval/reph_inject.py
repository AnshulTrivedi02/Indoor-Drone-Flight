#!/usr/bin/env python3
"""reph_inject.py -- insert or strip ArduPilot DAL REPH (ExternalNav) dataflash records
in a .bin log, for the EKF3+camera-heading Replay round-trip check and the (not yet run)
arm (ii) injection. See docs/thesis/ekf3_heading_replay/preregistration.md ("Injector").

STAGE 1 TOOL ONLY (2026-11-11). Never edits a log in place, never writes under
~/thesis_data/trials/. Does not invoke Replay itself -- that is a separate, later step,
gated by the round-trip check this tool's output feeds.

SPLICING, NOT RE-ENCODING. Every byte of the input that is not a REPH record this tool
adds or removes is copied verbatim (raw slices). FMT declarations, every other record
type, and any unparsed/resynced byte run are passed through untouched. This is
deliberate: df_reader.py (the format reference this tool reuses) reports a handful of
unparsed bytes even in clean logs (16 in fwdc_tex_r1, 50 in cl_bcpp_tex_r1_half, both
2026-11-11), so a decode-then-re-encode round trip would not be byte-identical even
before any REPH change. Splicing sidesteps that: it never has to understand those bytes.

FORMAT, VERIFIED EMPIRICALLY (2026-11-11, not assumed from the ArduPilot source alone --
checked against two real logs: fwdc_tex_r1, LOG_REPLAY=1 with zero REPH rows, and
cl_bcpp_tex_r1_half, the closed-loop heading template with 2404 live REPH rows):
  - Every ArduPilot dataflash record is b'\\xa3\\x95' + 1 type-id byte + packed fields.
    The type id's meaning (name, struct format, record length) comes from that SAME
    LOG's own FMT (type 0x80) declarations -- never a fixed id shared across logs.
  - REPH is declared in BOTH logs above: type id 156, format 'fffffffffIIH', columns
    PX,PY,PZ,Q1,Q2,Q3,Q4,PEr,AEr,TS,RT,D, record length 49 bytes (3 header + 46 payload,
    struct.calcsize('<fffffffffIIH') == 46). So AP_DAL declares the FULL FMT table at
    every log's start regardless of whether a type is ever used: injecting REPH into a
    log with zero REPH rows needs NO new FMT record and NO type-id allocation, only new
    REPH payload records using the id the log's own FMT table already assigns. This tool
    ASSERTS that REPH is declared with exactly this format before doing anything else,
    and refuses (loudly) if a log ever declares it differently or not at all.
  - log_REPH's Quaternion field order (AP_Math/quaternion.h: q1,q2,q3,q4) is (w,x,y,z):
    confirmed against cl_bcpp_tex_r1_half's own rows (Q1~=1, Q4 small, a near-identity
    yaw-only rotation) and against src/forward_camera/heading_bridge_core.py's
    HeadingCore.q_yaw(), which already returns [w,x,y,z] for the live ODOMETRY path.

PLACEMENT -- TWO MODES, because a naive single "derive position from timeStamp_ms" rule
was tried, measured at full scale against cl_bcpp_tex_r1_half (ALL 2404 live rows, not
just a synthetic sample), and was WRONG: a first attempt derived position straight from
timeStamp_ms (31.3% of the file's bytes differed); a second attempt anchored on "how
many RFRH precede this REPH" instead, which fixed the common case but still differed on
one real stretch where 40 records logged (a REPH among them) between two RFRF with NO
RFRH between them at all. Reading AP_DAL.cpp explains why: `end_frame()`
(AP_DAL.cpp:178-183) writes RFRF only when `_RFRF.frame_types != 0`, and does not itself
write a new RFRH -- only `start_frame()` does that, only on a genuinely new IMU
timestamp. `AP_DAL::writeExtNavData()` (AP_DAL.cpp:359-371) calls `end_frame()` ITSELF,
synchronously, immediately before writing REPH. So a REPH's own write is what triggers
(or finds already-flushed) the RFRF immediately before it -- RFRH count is NOT coupled
to this at all, but RFRF position is, exactly and unconditionally. Both wrong attempts
and the fix are recorded in docs/thesis/ekf3_heading_replay/preregistration.md
("Injector") and METHODOLOGY, not just fixed silently here.

  MODE 1 -- POSITIONAL (exact; used for the round-trip check and the unit tests).
  When every record carries "rfrf_count_before" (the number of RFRF records that
  precede it in file order -- a property roundtrip_extract() computes from the SAME
  log being reconstructed, needing no timestamp arithmetic at all), that count is used
  directly: insert immediately after the (count)-th RFRF of the file being written to
  (stripping never changes the RFRF sequence or count, so the index is stable across
  strip). Records sharing one "rfrf_count_before" are emitted in the ORDER GIVEN (file
  order from roundtrip_extract, not re-sorted by timeStamp_ms) -- the unit tests cover
  this with a SYNTHETIC "double-delivery" case (two REPH, no RFRF between them, because
  a source reading of end_frame() -- AP_DAL.cpp:178-183, "writes RFRF only if
  frame_types != 0" -- shows this is a real possible ArduPilot behaviour, not merely
  hypothesised): it reproduces their relative order exactly, though NOT byte-identically
  if other content (e.g. VISP) was originally interleaved between them; see
  test_double_delivery_gap_not_byte_identical. **That synthetic case does not actually
  occur in the real template** (checked: 0/2404 REPH rows share an rfrf_count_before in
  cl_bcpp_tex_r1_half). Measured against the real template in full (2404 records):
  **99.997% byte-identical (928/31,150,080 bytes differing, NOT byte-identical)** --
  the residual's real cause (an REPH sharing its end_frame() flush with a PRECEDING
  OF/ROFH flow-injection record, a different mechanism from the synthetic
  double-delivery case above) is in the pre-registration's "Injector" section, not
  repeated here.

  MODE 2 -- FROM A CAPTURE TIMESTAMP (approximate; for arm (ii), injecting a brand-new
  measurement that was never written by any live run, so there is no "rfrf_count_before"
  to recover). RFRF carries no timestamp field, so this mode still has to go via RFRH
  (the only timestamped frame record): find the first RFRH whose TimeUS exceeds
  (timeStamp_ms + placement_latency_ms) * 1000, then use the RFRF immediately before
  THAT RFRH as the insertion point (falling back to the RFRH's own start if none
  precedes it yet). placement_latency_ms is REQUIRED -- there is deliberately no
  default -- modelling the assumed capture-to-write latency. This IS AN OPEN ITEM: the
  live closed-loop template's own latency (44.4-71.2 ms, mean 50.6, median 49.7, as
  measured against its RFRH times) is that PARTICULAR pipeline's VISO_DELAY_MS plus
  processing/transport time, not necessarily representative of whatever synthetic delay
  arm (ii) is given -- see the pre-registration's "which measurements" / "TS and D"
  discussion. This mode is NOT claimed exact, and no arm (ii) run should treat its
  placement as validated by the round-trip check, which only exercises Mode 1.

  Records may not mix the two: either ALL carry "rfrf_count_before" (Mode 1) or NONE
  do (Mode 2, placement_latency_ms required). If no qualifying RFRF/RFRH exists at all
  (a target past the end of the log), the record is appended at EOF.

USAGE
  reph_inject.py strip IN.bin OUT.bin [--count-json N.json]
      Write OUT.bin = IN.bin with every REPH record removed. Refuses if OUT.bin exists,
      if OUT.bin's realpath equals IN.bin's, or if OUT.bin's realpath is under
      ~/thesis_data/trials/. With zero REPH records present, OUT.bin is byte-identical
      to IN.bin (this is itself one of the required unit tests, run on a real zero-REPH
      log, not just a synthetic one).

  reph_inject.py inject IN.bin OUT.bin --records RECORDS.json [--placement-latency-ms MS]
      Write OUT.bin = IN.bin with the records in RECORDS.json inserted. Mode 1
      (positional) if every record has "rfrf_count_before"; Mode 2 otherwise, which
      then REQUIRES --placement-latency-ms. RECORDS.json: a JSON list of objects, each:
        {"timeStamp_ms": int, "pos": [x,y,z], "quat": [w,x,y,z], "posErr": float,
         "angErr": float, "resetTime_ms": int, "delay_ms": int,
         "rfrf_count_before": int (Mode 1 only)}
      Same refusals as strip. Mode 2 refuses on any two records sharing the same
      (timeStamp_ms + placement_latency_ms) target (ambiguous order).

  reph_inject.py roundtrip-extract IN.bin RECORDS_OUT.json
      Decode every REPH record of IN.bin, in file order, WITH its "rfrf_count_before"
      -- i.e. output directly usable as Mode-1 input to `inject`. Used by the
      round-trip check and the unit tests to verify "strip, then inject the SAME
      records back, reproduces the original byte-for-byte" without needing Replay.
"""
import argparse, json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import df_reader as D  # noqa: E402  (shared FMT/record-format reference; never modified by this tool)

TRIALS_DIR = os.path.realpath(os.path.expanduser("~/thesis_data/trials"))
REPH_EXPECT_FMT = "fffffffffIIH"
REPH_EXPECT_COLS = "PX,PY,PZ,Q1,Q2,Q3,Q4,PEr,AEr,TS,RT,D"
REPH_FIELDS = ["pos_x", "pos_y", "pos_z", "quat_w", "quat_x", "quat_y", "quat_z",
               "posErr", "angErr", "timeStamp_ms", "resetTime_ms", "delay_ms"]


class RephInjectError(Exception):
    pass


def _refuse_output_path(out_path, in_path):
    out_real = os.path.realpath(out_path)
    in_real = os.path.realpath(in_path)
    if out_real == in_real:
        raise RephInjectError(f"refusing: OUT.bin equals IN.bin ({out_path})")
    if os.path.exists(out_path):
        raise RephInjectError(f"refusing to overwrite existing file: {out_path}")
    if out_real == TRIALS_DIR or out_real.startswith(TRIALS_DIR + os.sep):
        raise RephInjectError(f"refusing: OUT.bin is under {TRIALS_DIR} (never write into trials/)")


def _walk(data):
    """Single forward pass over the WHOLE file. Returns a list of records covering every
    byte with no gaps: (start, end, name_or_None, type_id_or_None). A byte run this
    pass cannot resynchronise on (same semantics as df_reader.read_records's resync
    logic) becomes one (start, end, None, None) entry, so concatenating data[start:end]
    for every entry in order reconstructs `data` exactly -- the property the splicing
    design above depends on, and what the "skip is preserved" unit test checks."""
    n = len(data)
    fmts = {D.FMT_TYPE: D._Fmt(D.FMT_TYPE, D.FMT_LEN, "FMT", "BBnNZ", "Type,Length,Name,Format,Columns")}

    def valid_at(j):
        return j + 3 <= n and data[j] == 0xA3 and data[j + 1] == 0x95 and data[j + 2] in fmts

    def resync(i):
        j = data.find(D.HEAD, i + 1)
        while j >= 0:
            if valid_at(j):
                k = j + fmts[data[j + 2]].length
                if k == n or (k + 2 <= n and data[k] == 0xA3 and data[k + 1] == 0x95):
                    return j
            j = data.find(D.HEAD, j + 1)
        return n

    out = []
    i = 0
    while i + 3 <= n:
        if data[i] != 0xA3 or data[i + 1] != 0x95 or data[i + 2] not in fmts:
            j = resync(i)
            out.append((i, j, None, None))
            i = j
            continue
        f = fmts[data[i + 2]]
        if i + f.length > n:
            out.append((i, n, None, None))
            break
        name = f.name
        if f.type == D.FMT_TYPE:
            ty, ln, nm, fmt, cols = f.struct.unpack_from(data, i + 3)
            nf = D._Fmt(ty, ln, D._cstr(nm), D._cstr(fmt), D._cstr(cols))
            old = fmts.get(ty)
            if ty != D.FMT_TYPE and old is not None and (old.name, old.fmt, old.length) != (nf.name, nf.fmt, nf.length):
                raise RephInjectError(f"type id {ty} redeclared ({old.name}/{old.fmt} -> {nf.name}/{nf.fmt}) "
                                       f"at offset {i}; refusing (ambiguous for a splice tool)")
            fmts[ty] = nf
            name = f"FMT({D._cstr(nm)})"
        out.append((i, i + f.length, name, data[i + 2]))
        i += f.length
    covered_end = out[-1][1] if out else 0
    if covered_end < n:
        # BUGFIX (found 2026-11-12 against real fwdplainc_tex_r1/fwdplainc_trans_r1 logs, both of
        # which end mid-header -- 2 and 1 trailing bytes respectively, "\xa3\x95" / "\xa3", i.e. the
        # log was truncated exactly while writing a new record's 3-byte header, presumably at
        # disarm/shutdown). The main loop's `while i + 3 <= n` condition stops BEFORE even looking at
        # a final run of fewer than 3 bytes, so they were silently dropped by every caller of
        # _walk() -- never copied through by strip()/inject() either, which both reconstruct the
        # file purely from this record list. Treat a trailing <3-byte remainder the same as any
        # other unparseable run: one final (covered_end, n, None, None) entry, copied through
        # verbatim by strip()/inject() like any other skip. Deliberately keyed on out[-1][1]
        # ("covered_end"), NOT the loop variable `i` -- the i+f.length > n branch above already
        # appends its own (i, n, ...) entry and `break`s WITHOUT advancing i, so using `i < n` here
        # double-appended an identical entry on every log whose last record is truncated that way
        # (e.g. a trailing XKF1 row with no room for the next record's header): found and fixed in
        # the same session, against fwdc_tex_r1, which has exactly this shape. Exercised by
        # reph_inject_test.py's test_trailing_stray_bytes_at_eof and
        # test_truncated_final_record_no_duplicate_tail_entry.
        out.append((covered_end, n, None, None))
    assert out[-1][1] == n if out else n == 0
    return out, fmts


def _reph_fmt(fmts):
    for ty, f in fmts.items():
        if f.name == "REPH":
            if f.fmt != REPH_EXPECT_FMT or ",".join(f.cols) != REPH_EXPECT_COLS:
                raise RephInjectError(f"REPH declared with unexpected format/columns: {f.fmt} / {f.cols} "
                                       f"(expected {REPH_EXPECT_FMT} / {REPH_EXPECT_COLS}); refusing")
            return ty, f
    raise RephInjectError("REPH is not declared (no FMT record) in this log; this tool does not add a new "
                           "FMT record (see module docstring) -- refusing")


def load(path):
    with open(path, "rb") as fh:
        data = fh.read()
    recs, fmts = _walk(data)
    reph_ty, reph_f = _reph_fmt(fmts)
    rfrh_f = next((f for f in fmts.values() if f.name == "RFRH"), None)
    if rfrh_f is None:
        raise RephInjectError("RFRH is not declared in this log; cannot place REPH records (no frame clock)")
    return data, recs, reph_ty, reph_f, rfrh_f


def decode_reph(data, recs, reph_ty, reph_f):
    """REPH records in file order, each with "rfrf_count_before" = how many RFRF
    records precede it in `recs` -- the Mode-1 positional anchor (see module
    docstring). Stripping never removes or reorders RFRH/RFRF, so this count is stable
    across strip() and directly usable against the stripped file's own RFRF sequence."""
    out = []
    n_rfrf = 0
    for start, end, name, ty in recs:
        if name == "RFRF":
            n_rfrf += 1
        elif ty == reph_ty and name == "REPH":
            vals = reph_f.struct.unpack_from(data, start + 3)
            d = dict(zip(REPH_FIELDS, vals))
            out.append({"pos": [d["pos_x"], d["pos_y"], d["pos_z"]],
                        "quat": [d["quat_w"], d["quat_x"], d["quat_y"], d["quat_z"]],
                        "posErr": d["posErr"], "angErr": d["angErr"],
                        "timeStamp_ms": d["timeStamp_ms"], "resetTime_ms": d["resetTime_ms"],
                        "delay_ms": d["delay_ms"], "rfrf_count_before": n_rfrf, "_offset": start})
    return out


def encode_reph(rec, reph_ty, reph_f):
    pos = rec["pos"]; quat = rec["quat"]
    vals = [pos[0], pos[1], pos[2], quat[0], quat[1], quat[2], quat[3],
            float(rec["posErr"]), float(rec["angErr"]),
            int(rec["timeStamp_ms"]), int(rec["resetTime_ms"]), int(rec["delay_ms"])]
    payload = reph_f.struct.pack(*vals)
    assert len(payload) == reph_f.length - 3, (len(payload), reph_f.length)
    return D.HEAD + bytes([reph_ty]) + payload


def strip(in_path, out_path, count_json=None):
    _refuse_output_path(out_path, in_path)
    data, recs, reph_ty, reph_f, _rfrh_f = load(in_path)
    pieces, n_removed = [], 0
    for start, end, name, ty in recs:
        if ty == reph_ty and name == "REPH":
            n_removed += 1
            continue
        pieces.append(data[start:end])
    out = b"".join(pieces)
    with open(out_path, "wb") as fh:
        fh.write(out)
    if count_json:
        json.dump({"in": in_path, "out": out_path, "n_removed": n_removed,
                   "in_bytes": len(data), "out_bytes": len(out)}, open(count_json, "w"), indent=1)
    byte_identical = (n_removed == 0 and out == data)
    print(f"strip: {in_path} -> {out_path}: removed {n_removed} REPH record(s) "
          f"({len(data)} -> {len(out)} bytes); byte_identical={byte_identical}")
    return n_removed, byte_identical


def _rfrf_ends(recs):
    """End offsets of every RFRF record, in file order. REASON this (not RFRH) is the
    Mode-1 positional anchor, found from the ArduPilot source after a second full-scale
    round-trip attempt (RFRH-count based, after the first, timeStamp_ms-only attempt's
    31.3% had already been fixed) still measured 0.3% of a real log's bytes differing --
    AP_DAL::writeExtNavData() (AP_DAL.cpp:359-371) calls end_frame() ITSELF,
    synchronously, immediately before writing REPH; end_frame() (AP_DAL.cpp:178-183)
    writes RFRF only if frame_types != 0, but writes NOTHING towards a new RFRH --
    that only happens inside start_frame(), on a genuinely new IMU timestamp, which is
    NOT coupled to how many ext-nav writes happen in between. So a REPH's "RFRH count
    before it" is NOT a stable count (confirmed: a real stretch of 40 records, including
    a REPH, sat between two consecutive RFRF with ZERO RFRH between them -- a batch of
    slow-rate telemetry logged while start_frame()'s own early-return branch (same
    imu_us) kept firing). RFRF, by contrast, is written by the SAME function call that
    is about to write REPH (when frame_types != 0, 99.5% of the live template's rows),
    landing byte-adjacent to it with nothing in between -- an exact, unambiguous anchor."""
    return [end for start, end, name, ty in recs if name == "RFRF"]


def _rfrh_targets(data, recs, rfrh_f):
    """(time_us, rfrh_start_offset) for every RFRH, in file order -- Mode 2's time axis
    (RFRF carries no timestamp field; REPH's own TS must be related to SOMETHING that
    does, and RFRH.TimeUS is the only option an ArduPilot dataflash log offers)."""
    out = []
    for start, end, name, ty in recs:
        if name == "RFRH":
            out.append((rfrh_f.struct.unpack_from(data, start + 3)[0], start))
    return out


def _gap_cut_before_rfrh(rfrf_ends, rfrh_start_offset):
    """End offset of the most recent RFRF before the RFRH starting at rfrh_start_offset
    (or that RFRH's own start, if none precedes it yet). Used only by Mode 2, to turn an
    RFRH-time target into the same RFRF-anchored gap Mode 1 uses. rfrf_ends: from
    _rfrf_ends(), ascending (file order == offset order)."""
    import bisect
    i = bisect.bisect_left(rfrf_ends, rfrh_start_offset)
    return rfrf_ends[i - 1] if i > 0 else rfrh_start_offset


def inject(in_path, out_path, records, placement_latency_ms=None):
    """records: list of dicts, each as decode_reph()/RECORDS.json produces. See the
    module docstring for Mode 1 (every record has "rfrf_count_before", the EXACT
    positional anchor -- see _rfrf_ends()) vs Mode 2 (none do; placement_latency_ms then
    required, and placement is approximate). Mode 1 records are placed in the order
    GIVEN (not re-sorted by timeStamp_ms: two sharing a gap may not be time-ordered by
    construction -- preserving file order is what makes the round trip exact). Mode 2
    records are sorted by (timeStamp_ms + placement_latency_ms); ties are refused."""
    _refuse_output_path(out_path, in_path)
    data, recs, reph_ty, reph_f, rfrh_f = load(in_path)
    if len(records) == 0:
        # Zero records: a verbatim copy, byte-identical, per the brief's explicit
        # "injector with zero records leaves the log byte-identical" requirement --
        # handled here, before any mode logic, rather than falling into Mode 2 (which
        # would otherwise raise for lack of placement_latency_ms on an empty list).
        with open(out_path, "wb") as fh:
            fh.write(data)
        print(f"inject (zero records): {in_path} -> {out_path}: byte-identical copy ({len(data)} bytes)")
        return 0
    has_count = ["rfrf_count_before" in r for r in records]
    if any(has_count) and not all(has_count):
        raise RephInjectError("refusing: some records have rfrf_count_before and some do not (modes cannot mix)")
    mode1 = all(has_count) and len(records) > 0

    if mode1:
        rfrf_ends = _rfrf_ends(recs)
        groups = {}
        for rec in records:
            groups.setdefault(int(rec["rfrf_count_before"]), []).append(rec)
        plan = []  # (cut_offset_or_None, [records in file order])
        for count in sorted(groups):
            if count < 0 or count > len(rfrf_ends):
                raise RephInjectError(f"rfrf_count_before={count} out of range (log has {len(rfrf_ends)} RFRF)")
            cut = rfrf_ends[count - 1] if count >= 1 else 0
            plan.append((cut, groups[count]))
    else:
        if placement_latency_ms is None:
            raise RephInjectError("Mode 2 (no rfrf_count_before) requires --placement-latency-ms (see module "
                                   "docstring: this is an OPEN, pre-registration-level item, not a tool default)")
        rfrh_entries = _rfrh_targets(data, recs, rfrh_f)
        rfrf_ends = _rfrf_ends(recs)
        targets = [int(r["timeStamp_ms"]) * 1000 + int(round(placement_latency_ms * 1000)) for r in records]
        if len(set(targets)) != len(targets):
            raise RephInjectError("refusing: two or more records resolve to the same placement target "
                                   "(timeStamp_ms + placement_latency_ms); ambiguous order")
        order = sorted(range(len(records)), key=lambda i: targets[i])
        plan, ptr = [], 0
        for i in order:
            while ptr < len(rfrh_entries) and rfrh_entries[ptr][0] <= targets[i]:
                ptr += 1
            cut = _gap_cut_before_rfrh(rfrf_ends, rfrh_entries[ptr][1]) if ptr < len(rfrh_entries) else None
            plan.append((cut, [records[i]]))

    pieces, prev_end = [], 0
    appended_at_end = []
    for cut, group in plan:
        if cut is None:
            appended_at_end += group
            continue
        if cut < prev_end:
            raise RephInjectError(f"internal: computed cut {cut} precedes prior cut end {prev_end}")
        pieces.append(data[prev_end:cut])
        for rec in group:
            pieces.append(encode_reph(rec, reph_ty, reph_f))
        prev_end = cut
    pieces.append(data[prev_end:])
    for rec in appended_at_end:
        pieces.append(encode_reph(rec, reph_ty, reph_f))
    out = b"".join(pieces)
    with open(out_path, "wb") as fh:
        fh.write(out)
    print(f"inject ({'positional' if mode1 else 'timestamp'}): {in_path} -> {out_path}: inserted "
          f"{len(records)} REPH record(s) ({len(appended_at_end)} appended at EOF, no later RFRH found); "
          f"{len(data)} -> {len(out)} bytes")
    return len(records)


def roundtrip_extract(in_path, out_json):
    data, recs, reph_ty, reph_f, _rfrh_f = load(in_path)
    records = decode_reph(data, recs, reph_ty, reph_f)
    for r in records:
        del r["_offset"]
    json.dump(records, open(out_json, "w"), indent=1)
    print(f"roundtrip-extract: {in_path}: {len(records)} REPH record(s) -> {out_json}")
    return len(records)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("strip"); s.add_argument("in_bin"); s.add_argument("out_bin"); s.add_argument("--count-json")
    i = sp.add_parser("inject"); i.add_argument("in_bin"); i.add_argument("out_bin"); i.add_argument("--records", required=True)
    i.add_argument("--placement-latency-ms", type=float, default=None)
    r = sp.add_parser("roundtrip-extract"); r.add_argument("in_bin"); r.add_argument("records_out")
    a = ap.parse_args()
    try:
        if a.cmd == "strip":
            strip(a.in_bin, a.out_bin, a.count_json)
        elif a.cmd == "inject":
            inject(a.in_bin, a.out_bin, json.load(open(a.records)), a.placement_latency_ms)
        elif a.cmd == "roundtrip-extract":
            roundtrip_extract(a.in_bin, a.records_out)
    except RephInjectError as e:
        print(f"reph_inject: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
