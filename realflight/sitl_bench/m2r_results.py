#!/usr/bin/env python3
"""SITL ONLY: evaluate the re-registered M2-R (`wbench5_m2r_*`) AS WORDED in docs/handovers/2026-10-12_m2r_rerun.md
§1.4–§1.5. Read-only on the session directory. Usage (in ~/venv-ardupilot):
    python -m realflight.sitl_bench.m2r_results <session_dir>
"""
import csv
import glob
import json
import os
import sys

import numpy as np


def load(sd):
    tests = [json.loads(l) for l in open(os.path.join(sd, "tests.jsonl"))]
    vel = list(csv.DictReader(open(os.path.join(sd, "watcher", "mocap_watch_vel.csv"))))
    hb = list(csv.DictReader(open(os.path.join(sd, "watcher", "mocap_watch_heartbeat.csv"))))
    stop = [l.rstrip("\n") for l in open(os.path.join(sd, "watcher", "STOP_LOG.txt"))]
    ghb = [tuple(map(float, l.split(","))) for l in open(os.path.join(sd, "relay_gcs_hb.csv")) if l.count(",") == 1]
    ev = [l.rstrip("\n").split(",", 2) for l in open(os.path.join(sd, "op_events.csv"))]
    fb = [l.rstrip("\n").split(",") for l in open(os.path.join(sd, "flow_bias.csv"))
          if not l.startswith("#") and not l.startswith("t_wall")]
    st = np.array([tuple(map(float, l.split(","))) for l in open(os.path.join(sd, "op_systime.csv"))])
    return tests, vel, hb, stop, ghb, ev, fb, st


def stop_t(l):
    try:
        return float(l.split()[1])
    except (IndexError, ValueError):
        return None


def xkf1_core0(sd):
    """[(time_boot_s, |v| 3-D)] of XKF1 core 0 from every BIN of the session (time since boot, not zero-based)."""
    from pymavlink import DFReader
    out = []
    for f in sorted(glob.glob(os.path.join(sd, "dataflash", "*.BIN"))):
        r = DFReader.DFReader_binary(f, zero_time_base=False)
        rows = []
        while True:
            m = r.recv_match(type="XKF1")
            if m is None:
                break
            if m.C == 0:
                rows.append((m.TimeUS * 1e-6, (m.VN ** 2 + m.VE ** 2 + m.VD ** 2) ** 0.5))
        out.append((f, rows))
    return out


def main(sd):
    tests, vel, hb, stop, ghb, ev, fb, st = load(sd)
    att = [t for t in tests if t["test"].startswith("M2R_attempt")]
    m1 = [t for t in tests if t["test"] == "M1_reboot"]
    df = None
    summary = []
    for i, a in enumerate(att):
        name = a["test"]
        t_arm = a["t_arm_w"]
        # the next M1 reboot after this attempt bounds its window
        reboots = [m["t_reboot_w"] for m in m1] + [t["t_reboot_w"] for t in tests if t["test"] == "M2R_M1"]
        t_m1 = min(r for r in reboots if r > t_arm)
        print(f"===== {name}  (v {a['v_mps']} m/s)  result field: {a['result']}")
        V = [r for r in vel if t_arm <= float(r["t_wall"]) < t_m1]
        t_armw = next(float(r["t_wall"]) for r in V if r["fc_armed"] == "True")     # the watcher's own arm view
        t_dis = next((float(r["t_wall"]) for r in V if float(r["t_wall"]) > t_armw and r["fc_armed"] == "False"), None)
        t_on = next((float(r["t_wall"]) for r in V if t_dis and float(r["t_wall"]) >= t_dis and r["vnorm"]
                     and float(r["vnorm"]) >= 0.2 and float(r["mocap_speed"]) < 0.05
                     and float(r["t_wall"]) <= t_dis + 5.0), None)
        # §1.4: t_end is searched only within the probe phase (its end = the last 20 Hz poll); none -> "capped"
        t_phase_end = max(p[0] for p in json.load(open(os.path.join(sd, f"{name}_polls.json"))))
        t_end = next((float(r["t_wall"]) for r in V if t_on and t_on < float(r["t_wall"]) <= t_phase_end
                      and r["vnorm"] and float(r["vnorm"]) < 0.2), None)
        capped = t_on is not None and t_end is None
        t_end_eval = t_end if t_end else t_phase_end
        vmax = max((float(r["vnorm"]) for r in V if t_on and t_on <= float(r["t_wall"]) <= t_end_eval), default=None)
        dur = None if t_on is None else t_end_eval - t_on
        print(f"t_dis(watcher) {t_dis:.3f}  op disarm seen {a['t_disarm_seen_w']:.3f} (op-watcher lag "
              f"{a['t_disarm_seen_w'] - t_dis:+.3f} s)")
        print(f"t_on {t_on}  t_end {t_end}  capped {capped}  duration {dur and round(dur, 2)} s  max |v| "
              f"{vmax and round(vmax, 2)} m/s  touchdown->t_on {t_on and round(t_on - a['t_touchdown_w'], 2)} s")
        # validity
        texts = [(float(e[0]), e[2]) for e in ev if len(e) == 3 and e[1] == "TEXT"]
        Ra = not any(t_arm <= stop_t(l) < t_m1 and "BREACH" in l for l in stop if stop_t(l)) and \
            not any(t_arm <= t < t_m1 and "Crash" in x for t, x in texts)
        Rb = a["truth_excursion_before_td_m"] <= 2.0
        Rc = not any(t_arm <= t < a["t_touchdown_w"] and "EKF Failsafe" in x for t, x in texts)
        after = [r for r in fb if float(r[0]) >= a["t_pass_cmd_w"] and float(r[0]) < t_m1]
        Rd = all(r[1] == "pass" for r in after)
        cut = [r for r in fb if t_arm <= float(r[0]) <= a["t_pass_cmd_w"]]
        last_bias = max((float(r[0]) for r in cut if r[1] == "bias"), default=None)
        Re = t_on is not None and all(float(r["mocap_speed"]) < 0.05 for r in V
                                      if t_on <= float(r["t_wall"]) <= t_end_eval and r["mocap_speed"])
        valid = Ra and Rb and Rc and Rd and (Re or t_on is None)
        print(f"VALIDITY R-a {Ra} R-b {Rb} (excursion {a['truth_excursion_before_td_m']} m) R-c {Rc} R-d {Rd} "
              f"({len(after)} msgs after the pass command; last bias msg {last_bias and round(last_bias - a['t_touchdown_w'], 2)} s "
              f"rel. touchdown) R-e {Re}  => {'VALID' if valid else 'VOID'}")
        if t_on is None:
            summary.append((name, a["v_mps"], valid, None, None))
            continue
        # T1
        H = [r for r in hb if float(r["t_wall"]) <= t_on + 0.5]
        last_row = H[-1]
        lines = [l for l in stop if stop_t(l) and stop_t(l) <= t_on + 0.5 and "confirmation " in l]
        T1i = last_row["confirmed"] == "0" and "vel " in lines[-1]
        hb_after = [t for t, s in ghb if s == 211 and t_on + 0.5 < t <= t_end_eval]
        T1ii = not hb_after
        rows3 = [r for r in hb if t_on + 0.5 <= float(r["t_wall"]) <= t_end_eval]
        T1iii = all(r["confirmed"] == "0" for r in rows3)
        first0 = next((float(r["t_wall"]) for r in hb if float(r["t_wall"]) >= t_dis - 1 and r["confirmed"] == "0"),
                      None)
        last_hb = max((t for t, s in ghb if s == 211 and t <= t_on + 0.5), default=None)
        print(f"T1 (i) {T1i}: last hb row {float(last_row['t_wall']) - t_on:+.3f} s conf {last_row['confirmed']}; "
              f"line in force: {lines[-1][26:110]!r}")
        print(f"   withdrawal (first confirmed=0 row) at {first0 - t_on:+.3f} s rel. t_on; last watcher HEARTBEAT to "
              f"the FC at {last_hb - t_on:+.3f} s rel. t_on")
        print(f"T1 (ii) {T1ii}: {len(hb_after)} watcher HEARTBEATs to the FC in (t_on+0.5, t_end]")
        print(f"T1 (iii) {T1iii}: {len(rows3)} heartbeat-CSV rows in [t_on+0.5, t_end], all confirmed=0")
        # T2
        polls = json.load(open(os.path.join(sd, f"{name}_polls.json")))
        P = [p for p in polls if t_on + 0.5 <= p[0] <= t_end_eval]
        T2a = all(p[1] == "0" for p in P)
        T2b = a.get("fs2_armed_before_kill") is False
        probes = a["fc_probes"]
        print(f"T2 (a) {T2a}: {len(P)} polls, box=1 in {sum(p[1] != '0' for p in P)}")
        print(f"T2 (b) {T2b}: flight script during the runaway: armed {a.get('fs2_armed_before_kill')}; "
              f"lines {a.get('fs2_lines')}")
        if df is None:
            df = xkf1_core0(sd)
        counted, T2c = 0, True
        for p in probes:
            j = np.argmin(abs(st[:, 0] - p["t_w"]))
            tb = st[j, 1] * 1e-3 + (p["t_w"] - st[j, 0])
            v1b = None
            for f, rows in df:
                vv = [v for t, v in rows if abs(t - tb) <= 0.5]
                if vv and rows[0][0] <= tb <= rows[-1][0]:
                    v1b = min(vv)
            ok = p["ack"] != 0 and not p["armed"] and any("GCS failsafe" in x for x in p["fc_texts"])
            inrun = p["t_w"] <= t_end_eval
            if v1b is not None and v1b >= 0.2 and inrun:
                counted += 1
                T2c = T2c and ok
            print(f"   probe +{p['t_w'] - t_on:6.2f} s (hb gap {p['t_w'] - p['t_last_gcs_hb_w']:.2f} s): ack "
                  f"{p['ack']} armed {p['armed']} texts {p['fc_texts']} op|v| {p['op_v_0p3s'][-1:]} "
                  f"XKF1c0 min|v| ±0.5 s {v1b and round(v1b, 3)} -> {'counted' if v1b and v1b >= 0.2 and inrun else 'not counted'}"
                  f" {'refused' if ok else 'NOT REFUSED'}")
        print(f"T2 (c) {'NOT EVALUATED' if counted == 0 else T2c} ({counted} counted probes)")
        land = sum(1 for l in stop if stop_t(l) and t_dis <= stop_t(l) < t_m1 and "LAND command sent" in l)
        br = sum(1 for l in stop if stop_t(l) and t_dis <= stop_t(l) < t_m1 and "BREACH" in l)
        T3 = land == 0 and br == 0
        print(f"T3 {T3}: LAND sends {land}, BREACH {br} from the disarm to the next M1")
        rc = a.get("t_reconfirm_same_boot_w")
        print(f"obs: same-boot re-confirmation {rc and round(rc - t_end, 2)} s after t_end (watcher)")
        summary.append((name, a["v_mps"], valid, dur, dict(T1=T1i and T1ii and T1iii, T2ab=T2a and T2b,
                                                           T2c=None if counted == 0 else T2c, T3=T3, n=counted)))
    m = [t for t in tests if t["test"] == "M2R_M1"][0]
    T4 = bool(m["origin_verified"]) and m["t_confirmed_w"] is not None and \
        m["t_confirmed_w"] - m["t_watcher_start_w"] <= 90 and m["op_vmax_5s_before_confirm"] < 0.2 and \
        any("Safety watcher confirmed before arming" in x for x in m["lines"]) and any("Armed." in x for x in m["lines"])
    print(f"===== T4 {T4}: origin {m['origin_verified']}, confirmed {m['t_confirmed_w'] - m['t_watcher_start_w']:.1f} s "
          f"after restart, op |v|max 5 s before {m['op_vmax_5s_before_confirm']}, lines {m['lines']}")
    print("===== SUMMARY")
    for s in summary:
        print(s)


if __name__ == "__main__":
    main(sys.argv[1])
