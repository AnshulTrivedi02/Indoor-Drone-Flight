#!/usr/bin/env python3
"""U10 rule 2 verification (2026-10-12) on a Replay output log of the replay-rukx build (UKF records renamed RUK* in
Replay). Read only.

  check_rukx.py --new NEW.BIN --ref E82.BIN [--input FLIGHT.bin --shadow ukf_shadow.csv --stored-b B.json] [--json OUT]

(1) df_reader on NEW: 0 undeclared ids, 0 skipped bytes, 0 bad FMT, 0 re-declared type ids; the UKF type ids.
(2) Every RUK* series and every XUK* series has strictly increasing TimeUS (they no longer interleave).
(3) STOCK-flown input (no --input): NEW holds NO XUK* record, and its RUK* records equal the installed e82c050b
    output's (REF) XUK* records, value for value; byte level, record by record NEW vs REF: identical except the FMT
    records of the UKF types (the name bytes only) and FMTU records (ArduPilot stamps those with the process clock).
(4) FORK-flown input (--input): NEW's XUK* records equal the INPUT log's (the copied-through onboard records), value
    for value; RUKF equals ukf_shadow.csv (TimeUS exact, values to the CSV's printing); RUKF vs the onboard XUKF with
    the stored ukf_replay_vs_flying.py bands (E1/E3 on exact-TimeUS pairs, E5 increments from RUKS vs XUKS), against
    the stored result computed from the CSV (--stored-b).
(5) pymavlink, both readers (mavlink_connection and DFReader_binary): RUKO, XUKO, RUKF and XKF1-per-core counts equal
    df_reader's.
"""
import argparse, collections, json, os, sys
import numpy as np

sys.path.insert(0, "/home/makerspace/thesis_ws/.claude/worktrees/agent-a5e6fd9bcc14a040c/eval")
os.environ.setdefault("MAVLINK20", "1")
from df_reader import read_records  # noqa: E402

SUF = ["UKF", "UKO", "UKS", "UKH", "UKT"]
X = ["X" + s for s in SUF]; R = ["R" + s for s in SUF]


def walk(d):
    fmt = {0x80: ("FMT", 89)}; out = []; i = 0; n = len(d)
    while i + 3 <= n:
        assert d[i] == 0xA3 and d[i + 1] == 0x95, f"lost sync at {i}"
        t = d[i + 2]; assert t in fmt, f"undeclared type {t} at {i}"
        if t == 0x80:
            fmt[d[i + 3]] = (d[i + 5:i + 9].rstrip(b"\0").decode(), d[i + 4])
        ln = fmt[t][1]; out.append((i, t, ln)); i += ln
    return out, fmt


def bytecmp(dn, do):
    rn, fn = walk(dn); ro, fo = walk(do)
    res = {"records_new": len(rn), "records_ref": len(ro), "differing": collections.Counter()}
    if len(rn) != len(ro):
        res["PASS"] = False; return res
    for (a, ta, la), (b, tb, lb) in zip(rn, ro):
        x, y = dn[a:a + la], do[b:b + lb]
        if x == y:
            continue
        nm = fn[ta][0]
        if nm == "FMT" and x[:5] == y[:5] and x[9:] == y[9:] and x[5:9].rstrip(b"\0").decode() in R \
                and y[5:9].rstrip(b"\0").decode() == "X" + x[6:9].rstrip(b"\0").decode():
            res["differing"]["FMT name XUK->RUK only"] += 1
        elif nm == "FMTU":
            res["differing"]["FMTU (process-clock stamp)"] += 1
        else:
            res["differing"][nm] += 1
    res["differing"] = dict(res["differing"])
    res["PASS"] = all(k.startswith("FMT") for k in res["differing"])
    return res


def strictly_inc(rs):
    t = np.array([r["TimeUS"] for r in rs], float)
    return bool(len(t) < 2 or np.all(np.diff(t) > 0))


def same_records(a, b):
    return len(a) == len(b) and all(x == y for x, y in zip(a, b))


def pym_counts(path):
    from pymavlink import mavutil, DFReader
    out = {}
    for lab, mk in (("mavlink_connection", lambda: mavutil.mavlink_connection(path)),
                    ("DFReader_binary", lambda: DFReader.DFReader_binary(path))):
        m = mk(); c = collections.Counter()
        while True:
            r = m.recv_match(type=["RUKO", "XUKO", "RUKF", "XUKF", "XKF1"])
            if r is None:
                break
            ty = r.get_type(); c[ty if ty != "XKF1" else f"XKF1@{r.C}"] += 1
        out[lab] = dict(c)
    return out


def e_bands(rukf, xukf, ruks, xuks):
    tf = np.array([r["TimeUS"] for r in xukf], np.int64); tr = np.array([r["TimeUS"] for r in rukf], np.int64)
    common, i, j = np.intersect1d(tr, tf, return_indices=True)
    g = lambda rs, k, ix: np.array([rs[q][k] for q in ix])
    d3 = np.linalg.norm(np.stack([g(rukf, k, i) - g(xukf, k, j) for k in ("PN", "PE", "PD")], 1), axis=1)
    dy = np.abs((g(rukf, "Yaw", i) - g(xukf, "Yaw", j) + 180) % 360 - 180)
    t0, t1 = common[0], common[-1]
    def inc(rs, k):
        t = np.array([r["TimeUS"] for r in rs]); a = np.searchsorted(t, t0, "right") - 1; b = np.searchsorted(t, t1, "right") - 1
        return float(rs[b][k] - rs[a][k])
    e5 = {k: {"replay": inc(ruks, k), "flying": inc(xuks, k)} for k in ("FXa", "FYa", "Ra")}
    for v in e5.values():
        v["rel_diff"] = abs(v["flying"] - v["replay"]) / max(v["flying"], 1.0)
    return {"paired": int(len(common)), "E1_max_m": float(d3.max()), "E1_rms_m": float(np.sqrt((d3 ** 2).mean())),
            "E3_yaw_max_deg": float(dy.max()), "E5": e5}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--new", required=True); ap.add_argument("--ref", required=True)
    ap.add_argument("--input"); ap.add_argument("--shadow"); ap.add_argument("--stored-b"); ap.add_argument("--json")
    a = ap.parse_args()
    names = X + R + ["XKF1"]
    rn, inf = read_records(a.new, names)
    out = {"new": a.new, "ref": a.ref, "input": a.input}
    out["df_reader"] = {k: inf[k] for k in ("undeclared_types", "skipped_bytes", "bad_fmt", "redeclared_ids")}
    out["df_reader"]["ukf_type_ids"] = {k: v for k, v in inf["type_ids"].items() if k in X + R}
    out["counts"] = {k: len(rn[k]) for k in X + R}
    out["xkf1_per_core"] = dict(collections.Counter(r["C"] for r in rn["XKF1"]))
    out["strictly_increasing"] = {k: strictly_inc(rn[k]) for k in X + R if rn[k]}
    ok = (not inf["undeclared_types"] and inf["skipped_bytes"] == 0 and not inf["bad_fmt"] and not inf["redeclared_ids"]
          and all(out["strictly_increasing"].values()) and len(rn["RUKO"]) > 0)
    rr, _ = read_records(a.ref, X)
    if not a.input:
        out["stock"] = {"no_XUK_in_new": all(len(rn[k]) == 0 for k in X),
                        "RUK_equals_ref_XUK": {s: same_records(rn["R" + s], rr["X" + s]) for s in SUF if rr["X" + s] or rn["R" + s]}}
        out["bytecmp_vs_ref"] = bytecmp(open(a.new, "rb").read(), open(a.ref, "rb").read())
        ok = ok and out["stock"]["no_XUK_in_new"] and all(out["stock"]["RUK_equals_ref_XUK"].values()) \
            and out["bytecmp_vs_ref"]["PASS"]
    else:
        ri, ii = read_records(a.input, X)
        out["fork"] = {"input_skipped_bytes": ii["skipped_bytes"],
                       "XUK_equals_input": {s: same_records(rn["X" + s], ri["X" + s]) for s in SUF if ri["X" + s] or rn["X" + s]},
                       "ref_XUKO_count_interleaved": len(rr["XUKO"])}
        c = np.genfromtxt(a.shadow, delimiter=",", names=True)
        t = np.array([r["TimeUS"] for r in rn["RUKF"]], np.int64)
        same_t = len(t) == len(c) and np.array_equal(t, c["TimeUS"].astype(np.int64))
        dmax = max(float(np.max(np.abs(np.array([r[k] for r in rn["RUKF"]]) - c[k]))) for k in ("PN", "PE", "PD", "VN", "VE", "VD")) if same_t else None
        out["fork"]["RUKF_vs_ukf_shadow_csv"] = {"TimeUS_identical": bool(same_t), "max_abs_diff_pos_vel": dmax}
        out["fork"]["bands_RUKF_vs_onboard_XUKF"] = e_bands(rn["RUKF"], rn["XUKF"], rn["RUKS"], rn["XUKS"])
        if a.stored_b:
            sb = json.load(open(a.stored_b))
            out["fork"]["stored_from_csv"] = {"paired": sb["paired"], "E1_max_m": sb["all"]["E1_pos3d_max_m"],
                                              "E1_rms_m": sb["all"]["E1_pos3d_rms_m"], "E3_yaw_max_deg": sb["all"]["E3_yaw_max_deg"]}
        ok = ok and all(out["fork"]["XUK_equals_input"].values()) and same_t and dmax is not None and dmax <= 6e-5
    out["pymavlink"] = pym_counts(a.new)
    want = {k: v for k, v in {"RUKO": len(rn["RUKO"]), "XUKO": len(rn["XUKO"]), "RUKF": len(rn["RUKF"]),
                               "XUKF": len(rn["XUKF"]), **{f"XKF1@{c}": n for c, n in out["xkf1_per_core"].items()}}.items() if v}
    out["pymavlink_matches_df_reader"] = {lab: c == want for lab, c in out["pymavlink"].items()}
    ok = ok and all(out["pymavlink_matches_df_reader"].values())
    out["PASS"] = bool(ok)
    print(json.dumps(out, indent=1, default=str))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
