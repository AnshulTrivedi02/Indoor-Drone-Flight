#!/usr/bin/env python3
"""A strict, self-contained ArduPilot dataflash (.BIN) reader for the rung-1 scorer (2026-10-12).

WHY NOT pymavlink: the thesis fork's Replay writes the UKF's streaming records (XUKF, XUKO, XUKS, XUKH) WITHOUT their
FMT records when the input log does not already declare them (a stock-flown log, i.e. every rung-1 log). Checked on
stored Replay outputs (handover docs/handovers/2026-10-12_r1_scoring_items.md, section C):
  * pymavlink's fast (Cython) indexer stops the whole process ("Invalid length in FMT message at <offset>");
  * its pure-Python reader resynchronises badly and returns about 15 XKF1 per core instead of ~3 457.
So on a real rung-1 Replay output, `mavlink_connection(...)` would either exit or silently score a handful of samples.

THIS READER walks the file record by record using the FMT table (header A3 95, type byte, length from that type's FMT).
A record whose type has NO FMT has an unknown length; the reader then resynchronises at the next position where a valid
header of a DECLARED type starts AND is followed, at exactly that record's length, by another valid header (or the end
of the file). Every undeclared type id and every skipped byte is counted and returned, so a caller can refuse a log
whose integrity it cannot confirm (real_score.bin_trajs asserts that the replayed XKF1 cores match the onboard ones).

UPDATE 2026-10-12: Replay e82c050b and later emit those FMT records, so pymavlink reads such outputs again; this reader
remains the scorer's reader (strict, with the diagnostics below). From the U10 rule-2 Replay (port `replay-rukx`), Replay
writes the UKF records under DISTINCT names RUKF/RUKO/RUKS/RUKH/RUKT; a Replay output's XUK* records are then only ever
the onboard ones (copied through from a fork-flown input log). Selecting replayed vs onboard is done by the caller
(real_score.parse_record / bin_trajs), by name.

  recs, info = read_records(path, ["XKF1", "XUKO"])     # {name: [dict(field -> value), ...]}, {...diagnostics...}
"""
import struct

HEAD = b"\xa3\x95"
FMT_TYPE = 0x80
FMT_LEN = 89                       # 3 header + B type + B length + 4s name + 16s format + 64s labels
FORMAT_TO_STRUCT = {               # ArduPilot LogStructure.h format characters (as pymavlink's DFReader table)
    "a": ("64s", None), "b": ("b", None), "B": ("B", None), "g": ("e", None), "h": ("h", None), "H": ("H", None),
    "i": ("i", None), "I": ("I", None), "f": ("f", None), "n": ("4s", None), "N": ("16s", None), "Z": ("64s", None),
    "c": ("h", 0.01), "C": ("H", 0.01), "e": ("i", 0.01), "E": ("I", 0.01), "L": ("i", 1.0e-7), "d": ("d", None),
    "M": ("b", None), "q": ("q", None), "Q": ("Q", None),
}


def _cstr(b):
    return b.split(b"\0", 1)[0].decode("ascii", "replace")


class _Fmt:
    def __init__(self, ty, length, name, fmt, cols):
        self.type, self.length, self.name, self.fmt = ty, length, name, fmt
        self.cols = cols.split(",") if cols else []
        try:
            self.struct = struct.Struct("<" + "".join(FORMAT_TO_STRUCT[c][0] for c in fmt))
            self.mul = [FORMAT_TO_STRUCT[c][1] for c in fmt]
            self.ok = self.struct.size == length - 3 and len(self.cols) == len(fmt)
        except KeyError:
            self.struct, self.mul, self.ok = None, None, False

    def decode(self, buf, off):
        vals = self.struct.unpack_from(buf, off + 3)
        out = {}
        for c, v, m in zip(self.cols, vals, self.mul):
            if isinstance(v, bytes):
                v = _cstr(v)
            elif m is not None:
                v = v * m
            out[c] = v
        return out


def read_records(path, names, data=None):
    """Decode every record of the given type NAMES. Returns (records, info).
    info: n_records (per declared name, all types), undeclared_types {type id at a resync point: count; later
    undeclared records inside the same skipped run are not counted separately}, skipped_bytes, n_resyncs,
    declared (names with an FMT), bad_fmt (FMTs whose format/length/labels disagree),
    redeclared_ids (2026-10-12: a type id declared again with a DIFFERENT name, format or length; the later records of
    that id decode under the new FMT, so a caller must refuse such a log: e.g. an input-log FMT in Replay's dynamic id
    window [220, 230] colliding with a record Replay itself allocates), type_ids {name: [type ids declared for it]}."""
    d = open(path, "rb").read() if data is None else data
    n = len(d); want = set(names)
    fmts = {FMT_TYPE: _Fmt(FMT_TYPE, FMT_LEN, "FMT", "BBnNZ", "Type,Length,Name,Format,Columns")}
    recs = {k: [] for k in names}
    counts, undeclared = {}, {}
    skipped = resyncs = 0
    bad_fmt = []
    redeclared, ids = [], {}

    def valid_at(j):
        return j + 3 <= n and d[j] == 0xA3 and d[j + 1] == 0x95 and d[j + 2] in fmts

    def resync(i):
        """Next j > i where a declared record starts and, at exactly its length, the next record header (A3 95, of any
        type, declared or not: undeclared records may be dense) or the end of the file follows."""
        j = d.find(HEAD, i + 1)
        while j >= 0:
            if valid_at(j):
                k = j + fmts[d[j + 2]].length
                if k == n or (k + 2 <= n and d[k] == 0xA3 and d[k + 1] == 0x95):
                    return j
            j = d.find(HEAD, j + 1)
        return n

    i = 0
    while i + 3 <= n:
        if d[i] != 0xA3 or d[i + 1] != 0x95 or d[i + 2] not in fmts:
            if d[i] == 0xA3 and d[i + 1] == 0x95:
                undeclared[d[i + 2]] = undeclared.get(d[i + 2], 0) + 1
            j = resync(i); skipped += j - i; resyncs += 1; i = j
            continue
        f = fmts[d[i + 2]]
        if i + f.length > n:
            skipped += n - i
            break
        if f.type == FMT_TYPE:
            ty, ln, name, fmt, cols = f.struct.unpack_from(d, i + 3)
            nf = _Fmt(ty, ln, _cstr(name), _cstr(fmt), _cstr(cols))
            if not nf.ok:
                bad_fmt.append(nf.name)
            if ty != FMT_TYPE:
                old = fmts.get(ty)
                if old is not None and (old.name, old.fmt, old.length) != (nf.name, nf.fmt, nf.length):
                    redeclared.append({"type": int(ty), "was": old.name, "now": nf.name, "offset": int(i)})
                fmts[ty] = nf
                ids.setdefault(nf.name, set()).add(int(ty))
            counts["FMT"] = counts.get("FMT", 0) + 1
        else:
            counts[f.name] = counts.get(f.name, 0) + 1
            if f.name in want and f.ok:
                recs[f.name].append(f.decode(d, i))
        i += f.length
    info = {"n_records": counts, "undeclared_types": undeclared, "skipped_bytes": skipped, "n_resyncs": resyncs,
            "declared": sorted({f.name for f in fmts.values()}), "bad_fmt": bad_fmt,
            "redeclared_ids": redeclared, "type_ids": {k: sorted(v) for k, v in sorted(ids.items())}}
    return recs, info


def write_fmt(ty, name, fmt, cols):
    """Encode an FMT record (tests)."""
    length = 3 + struct.calcsize("<" + "".join(FORMAT_TO_STRUCT[c][0] for c in fmt))
    return HEAD + bytes([FMT_TYPE]) + struct.pack("<BB4s16s64s", ty, length, name.encode(), fmt.encode(), cols.encode())


def write_rec(ty, fmt, *vals):
    """Encode one record of type id `ty` with format string `fmt` (tests)."""
    return HEAD + bytes([ty]) + struct.pack("<" + "".join(FORMAT_TO_STRUCT[c][0] for c in fmt), *vals)
