#!/usr/bin/env python3
"""SITL ONLY (bench 2c): the pre-registered intervals per test, from one or more session directories.

  python3 -m realflight.sitl_bench.results SESSION_DIR [SESSION_DIR ...]  > results.txt

For each test row in tests.jsonl it prints the intervals the criterion needs, on W (wall) and F (FC) clocks
(handover §1.1). It prints numbers only; the PASS/FAIL wording is applied in the handover against §1.2.
"""
import glob
import json
import os
import re
import sys

import numpy as np

from realflight.sitl_bench.analyse import boots, df_events, text_events
import glob


def load(sess):
    cms = boots(sess)
    bins = sorted(glob.glob(os.path.join(sess, "dataflash", "*.BIN")))
    pairs = list(zip(bins, cms)) if len(cms) == len(bins) else [(b, cms[-1]) for b in bins]
    fc = []
    for b, cm in pairs:
        fc += df_events(b, cm)
    ev = sorted(fc + text_events(sess), key=lambda x: x[0])
    tests = [json.loads(l) for l in open(os.path.join(sess, "tests.jsonl"))]
    return cms[-1], ev, tests


def first(ev, t0, src=None, pat=None, t1=None):
    for e in ev:
        if e[0] < t0 or (t1 is not None and e[0] > t1):
            continue
        if src and not e[2].startswith(src):
            continue
        if pat and not re.search(pat, e[3]):
            continue
        return e
    return None


def allm(ev, t0, t1, src=None, pat=None):
    return [e for e in ev if t0 <= e[0] <= t1 and (not src or e[2].startswith(src)) and (not pat or re.search(pat, e[3]))]


def iv(cm, t0w, e):
    """(dW, dF) from an injection at wall t0w to event e."""
    if e is None:
        return None
    dw = e[0] - t0w
    df = (e[1] - cm.w2f(t0w)) if e[1] is not None else None
    return round(dw, 3), (round(df, 3) if df is not None else None), e[2], e[3][:110]


def track(sess):
    rows = []
    p = os.path.join(sess, "watcher", "mocap_watch_track.csv")
    for l in open(p).readlines()[1:]:
        f = l.split(",")
        try:
            rows.append((float(f[0]), float(f[1]), float(f[5]), float(f[6]), float(f[7]), int(f[9]), float(f[10])))
        except (ValueError, IndexError):
            pass
    return rows


def fwd_dest0(sess):
    out = []
    for l in open(os.path.join(sess, "forwarder.csv")):
        p = l.split(",")
        if len(p) > 6 and p[1] == "0":
            try:
                out.append((float(p[0]), p[4], int(p[5])))
            except ValueError:
                pass
    return out


def df_rows(sess, types):
    """All rows of the given dataflash types from every BIN of the session: list of (bin_index, F, msg)."""
    from pymavlink import DFReader
    out = []
    for k, b in enumerate(sorted(glob.glob(os.path.join(sess, "dataflash", "*.BIN")))):
        r = DFReader.DFReader_binary(b)
        while True:
            m = r.recv_match(type=types)
            if m is None:
                break
            out.append((k, m.TimeUS / 1e6, m))
    return out


def gt_track(sess):
    """(wall, x, y, z) of every dest-0 forwarder packet."""
    out = []
    for l in open(os.path.join(sess, "forwarder.csv")):
        p = l.split(",")
        if len(p) == 10 and p[1] == "0":
            try:
                out.append((float(p[0]), float(p[7]), float(p[8]), float(p[9])))
            except ValueError:
                pass
    return out


def watcher_lines(sess, t0, t1, pat):
    out = []
    p = os.path.join(sess, "watcher", "STOP_LOG.txt")
    for l in open(p):
        parts = l.split(" ", 2)
        try:
            w = float(parts[1])
        except (ValueError, IndexError):
            continue
        if t0 <= w <= t1 and re.search(pat, parts[2]):
            out.append((w, parts[2].strip()))
    return out


def relay_lines(sess, t0, t1, pat):
    out = []
    p = os.path.join(sess, "relay_events.txt")
    for l in open(p):
        parts = l.split(" ", 1)
        try:
            w = float(parts[0])
        except ValueError:
            continue
        if t0 <= w <= t1 and re.search(pat, parts[1]):
            out.append((w, parts[1].strip()))
    return out


_YAW = {}


def yaw_at_arm(sess, cm, t_arm_w):
    """Amendment A9 check: EKF yaw (ATT) minus the simulator's true yaw (SIM) at the ARM event nearest before the
    flight script's "Armed." line (a hover with |diff| > 5 deg at arming is VOID)."""
    if sess not in _YAW:
        rows = df_rows(sess, ["ATT", "SIM", "EV"])
        _YAW[sess] = rows
    rows = _YAW[sess]
    fa = cm.w2f(t_arm_w)
    arm = [f for b, f, m in rows if m.get_type() == "EV" and int(m.Id) == 10 and fa - 10 < f <= fa + 0.5]
    if not arm:
        return "EKF-vs-true yaw at arming: no ARM event found"
    f0 = arm[-1]
    att = min((x for x in rows if x[2].get_type() == "ATT"), key=lambda x: abs(x[1] - f0))
    sim = min((x for x in rows if x[2].get_type() == "SIM"), key=lambda x: abs(x[1] - f0))
    d = (att[2].Yaw - sim[2].Yaw + 180) % 360 - 180
    return f"EKF-vs-true yaw at arming (F {f0:.2f}): {d:+.1f} deg (A9: |diff| <= 5 deg required)"


def report(sess):
    cm, ev, tests = load(sess)
    print(f"\n######## {os.path.basename(sess)}")
    orgn = df_rows(sess, ["ORGN"])
    print(" dataflash ORGN records (bin, F, type, lat, lng):",
          [(k, round(f, 2), m.Type, m.Lat, m.Lng) for k, f, m in orgn])
    fd = None
    for t in tests:
        n = t["test"]
        if n.startswith("param_snapshot"):
            continue
        print(f"\n=== {n}")
        g = lambda k: t.get(k)  # noqa: E731
        if t.get("t_arm_w"):
            print("  " + yaw_at_arm(sess, cm, t["t_arm_w"]))
        LAND = r"MODE LAND|EV DISARMED"
        if n in ("B2a",):
            k = g("t_watcher_sig9_w")
            print(" kill -> first LAND/disarm:", iv(cm, k, first(ev, k, "FC", LAND)))
            print(" kill -> flight script LAND cmd:", iv(cm, k, first(ev, k, "fs", "LAND commanded")))
            print(" kill -> FC GCS failsafe ERR:", iv(cm, k, first(ev, k, "FC", "FAILSAFE_GCS")))
        elif n == "B2b":
            k = g("t_watcher_kill_w")
            print(" (flight script killed at watcher_kill", round(g("t_fs_kill_w") - k, 3), "s)")
            print(" watcher kill -> FC GCS failsafe ERR:", iv(cm, k, first(ev, k, "FC", "FAILSAFE_GCS")))
            print(" watcher kill -> MODE LAND:", iv(cm, k, first(ev, k, "FC", "MODE LAND")))
        elif n == "B3a":
            k = g("t_cut_w")
            print(" cut -> FC GCS failsafe ERR:", iv(cm, k, first(ev, k, "FC", "FAILSAFE_GCS")))
            print(" cut -> MODE LAND:", iv(cm, k, first(ev, k, "FC", "MODE LAND")))
            print(" cut -> watcher withdrawal:", iv(cm, k, first(ev, k, "WATCHER", "BREACH|confirmation 0")))
            print(" watcher LAND commands after cut:", len(allm(ev, k, k + 30, "WATCHER", "LAND command sent")))
            print(" flight script:", iv(cm, k, first(ev, k, "fs", "WatcherLost|LAND commanded")))
        elif n == "B3b":
            k = g("t_sigstop_w"); c = g("t_sigcont_w")
            print(" SIGSTOP -> first LAND/disarm:", iv(cm, k, first(ev, k, "FC", LAND)))
            print(" first FC GCS failsafe ERR:", iv(cm, k, first(ev, k, "FC", "FAILSAFE_GCS")))
            print(" flight script:", iv(cm, k, first(ev, k, "fs", "WatcherLost|LAND commanded")))
            end = g("t_obs_end_w")
            print(" after SIGCONT (", round(c - k, 2), "s ): watcher LAND cmds:",
                  len(allm(ev, c, end, "WATCHER", "LAND command")), "; FC MODE events:",
                  [e[3] for e in allm(ev, c, end, "FC", "MODE|EV ARMED")])
            print(" watcher after SIGCONT:", [e[3][:100] for e in allm(ev, c, c + 5, "WATCHER")][:4])
        elif n.startswith("B4a_") or n == "B4c_tilt65":
            rows = track(sess)
            tw0 = g("t_carry_w")
            out = next((r for r in rows if r[0] > tw0 and (r[5] == 0 or n == "B4c_tilt65")), None)
            br = first(ev, tw0, "WATCHER", "BREACH")
            if n == "B4c_tilt65":
                print(" breach:", iv(cm, tw0, br))
            else:
                print(f" first pose outside: {out[0] - tw0:+.3f} s after the carry ({out[2]:.2f},{out[3]:.2f},{out[4]:.2f})")
                print(" first outside pose -> BREACH:", iv(cm, out[0], br))
            print(" -> confirmation withdrawn:", iv(cm, tw0, first(ev, tw0, "WATCHER", "confirmation 0")))
            print(" LAND sends:", [e[3][:60] for e in allm(ev, tw0, tw0 + 3, "WATCHER", "LAND (command|ACK)")])
            print(" FC MODE:", [e[3] for e in allm(ev, tw0, tw0 + 3, "FC", "MODE")])
            if "arm_attempt" in t:
                print(" arm attempt:", t["arm_attempt"], t["arm_lines"])
        elif n.startswith("B4b"):
            rows = track(sess)
            m = g("t_marker_w")
            out = next((r for r in rows if r[0] > m and r[5] == 0), None)
            if out is None:
                print(" no outside pose"); continue
            tw = out[0]
            print(f" first pose outside: wall {tw:.3f} pos ({out[2]:.3f},{out[3]:.3f},{out[4]:.3f})")
            print(" -> watcher BREACH:", iv(cm, tw, first(ev, tw - 0.05, "WATCHER", "BREACH")))
            print(" -> watcher LAND cmd:", iv(cm, tw, first(ev, tw - 0.05, "WATCHER", "LAND command sent")))
            print(" -> FC MODE LAND:", iv(cm, tw, first(ev, tw - 0.05, "FC", "MODE LAND")))
            print(" LAND decisions in episode:", len(allm(ev, tw - 1, tw + 30, "WATCHER", "LAND command sent \\(try 1")),
                  " sends:", len(allm(ev, tw - 1, tw + 30, "WATCHER", "LAND command sent")))
        elif n in ("B5a", "B5b", "B5b_noflag", "obs_latency_reset_wrongid"):
            fd = fd or fwd_dest0(sess)
            if n == "B5a":
                k = g("t_stop_w")
                last = max((r[0] for r in fd if r[0] <= k + 0.05), default=None)
                print(f" last frame sent {last - k:+.3f} s from the stop command")
                ref = last
            elif n == "B5b":
                k = g("t_untracked_w"); f1 = g("t_freeze_tracked1_w")
                print(" freeze(tracked=1) window: watcher events:",
                      [e[3][:80] for e in allm(ev, f1, k, "WATCHER")], "; FC MODE:",
                      [e[3] for e in allm(ev, f1, k, "FC", "MODE")])
                ref = next((r[0] for r in fd if r[0] >= k and r[2] == 0), None)
                print(f" first untracked frame {ref - k:+.3f} s from the command")
            elif n == "B5b_noflag":
                k = g("t_freeze_w")
                ref = next((r[0] for r in fd if r[0] >= k and r[1] == "freeze"), None)
                print(f" first frozen frame {ref - k:+.3f} s from the command")
            else:
                for kk in ("t_latency_on_w", "t_latency_off_w", "t_frame_reset_w"):
                    a = g(kk)
                    print(f" {kk}: watcher events within 4 s:", [e[3][:80] for e in allm(ev, a, a + 4, "WATCHER")],
                          "FC MODE:", [e[3] for e in allm(ev, a, a + 4, "FC", "MODE")])
                rows = track(sess)
                a, b = g("t_latency_on_w"), g("t_latency_off_w")
                lat = [r[6] for r in rows if a + 0.5 < r[0] < b]
                lat0 = [r[6] for r in rows if b + 0.5 < r[0] < b + 5]
                print(f" latency column during +150 ms: median {np.median(lat):.3f} s; after: {np.median(lat0):.3f} s")
                k = g("t_wrong_id_w")
                ref = next((r[0] for r in fd if r[0] >= k), None)
                print(f" first wrong-ID frame {ref - k:+.3f} s from the command")
            print(" ref -> watcher stale/BREACH:", iv(cm, ref, first(ev, ref - 0.05, "WATCHER", "BREACH")))
            print(" ref -> watcher LAND cmd:", iv(cm, ref, first(ev, ref - 0.05, "WATCHER", "LAND command sent")))
            print(" ref -> FC MODE LAND:", iv(cm, ref, first(ev, ref - 0.05, "FC", LAND)))
            print(" watcher MAVLink heartbeat:", hb_after(sess, ref))
            print(" watcher confirmation withdrawn:", iv(cm, ref, first(ev, ref - 0.05, "WATCHER", "confirmation 0")))
        elif n.startswith("B9"):
            k = next(v for kk, v in t.items() if re.match(r"t_flow_(tracker|bridge)_sig", kk))
            print(" inject -> watcher BREACH (withdrawal):", iv(cm, k, first(ev, k, "WATCHER", "BREACH")))
            print(" inject -> watcher LAND cmd:", iv(cm, k, first(ev, k, "WATCHER", "LAND command sent")))
            print(" inject -> FC MODE LAND:", iv(cm, k, first(ev, k, "FC", LAND)))
            print(" heartbeat log after inject:", hb_after(sess, k))
        elif n == "origin":
            print(f"  EKF3 init gate -> sent {g('t_sent_w') - g('t_gate_w'):.3f} s; sent -> GPS_GLOBAL_ORIGIN received "
                  f"{g('t_verified_w') - g('t_sent_w'):.3f} s; tries {g('tries')}; cores {g('cores')}; "
                  f"lat/lon {g('lat')}/{g('lon')} matches {g('matches_sent')}")
        elif n == "B8a":
            k = g("t_flow_bridge_kill_w"); r = g("t_flow_bridge_restart_w")
            kF = cm.w2f(k)
            rows = df_rows(sess, ["OF", "XKF4", "XKF1", "MODE", "ERR", "ORGN", "EV"])
            # the BIN whose span holds the kill (wbench4: M1 reboots give one BIN per hover; SITL keeps its clock)
            span = {}
            for b_, f_, _m in rows:
                lo, hi = span.get(b_, (f_, f_))
                span[b_] = (min(lo, f_), max(hi, f_))
            cover = [b_ for b_, (lo, hi) in span.items() if lo <= kF <= hi]
            boot = max(cover) if cover else max(span)
            rows = [x for x in rows if x[0] == boot]
            org = [f for b, f, m in rows if m.get_type() == "ORGN" and f < kF]
            print(f" PRECONDITION origin: ORGN record(s) before the kill at F {[round(x, 2) for x in org]}")
            rel_before = [(f, (m.SS >> 3) & 1) for b, f, m in rows if m.get_type() == "XKF4" and m.C == 0
                          and kF - 3 < f < kF]
            print(f" PRECONDITION HORIZ_POS_REL (core 0) in the 3 s before the kill: "
                  f"{'all true' if rel_before and all(v for _, v in rel_before) else rel_before[-5:]}")
            of = [f for b, f, m in rows if m.get_type() == "OF" and kF - 2 < f < kF + 25]
            last_of = None
            for a_, b_ in zip(of, of[1:]):
                if b_ - a_ > 1.0 and a_ > kF - 0.5:
                    last_of = a_; break
            if last_of is None and of:
                last_of = of[-1]
            print(f" kill at F {kF:.3f}; last OF row F {last_of:.3f} (kill -> last OF {last_of - kF:+.3f} s)")
            lost = next((f for b, f, m in rows if m.get_type() == "XKF4" and m.C == 0 and f > kF
                         and not (m.SS >> 3) & 1), None)
            print(f" HORIZ_POS_REL lost (core 0): F {lost} ({(lost - last_of) if lost else None} s after the last OF)")
            for b, f, m in rows:
                if kF - 0.5 < f < kF + 25 and m.get_type() in ("MODE", "ERR", "EV"):
                    ty = m.get_type()
                    d = (f"MODE {m.ModeNum} rsn {m.Rsn}" if ty == "MODE" else f"ERR {m.Subsys} {m.ECode}" if ty == "ERR"
                         else f"EV {m.Id}")
                    print(f"   F {f:9.3f} (+{f - last_of:6.3f} s after the last OF)  {d}")
            ekf_land = next((f for b, f, m in rows if m.get_type() == "MODE" and f > kF and int(m.Rsn) == 6), None)
            ekf_land_w = cm.f2w(ekf_land) if ekf_land else None
            print(f" -> MODE LAND reason EKF_FAILSAFE: {(ekf_land - last_of) if ekf_land else None} s F after the last OF")
            for lab, src, pat in (("watcher BREACH/LAND", "WATCHER", "BREACH|LAND command sent"),
                                  ("flight script LAND", "fs", "LAND commanded|WatcherLost"),
                                  ("FC GCS failsafe", "FC", "FAILSAFE_GCS")):
                e = first(ev, k, src, pat, k + 30)
                print(f" first {lab} after the kill: {iv(cm, k, e)}"
                      + (f"  (vs EKF LAND: {'AFTER' if ekf_land_w and e[0] > ekf_land_w else 'BEFORE/none'})" if e else ""))
            x1 = [(f, m.PN, m.PE) for b, f, m in rows if m.get_type() == "XKF1" and m.C == 0 and kF < f < kF + 25]
            jumps = [(round(b_[0], 2), round(((b_[1] - a_[1]) ** 2 + (b_[2] - a_[2]) ** 2) ** 0.5, 3))
                     for a_, b_ in zip(x1, x1[1:]) if ((b_[1] - a_[1]) ** 2 + (b_[2] - a_[2]) ** 2) ** 0.5 > 0.3]
            print(f" XKF1 (core 0) reported-position jumps > 0.3 m between rows after the kill: {jumps or 'none'}")
            gt = gt_track(sess)
            td = g("t_disarm_seen_w") or (r + 5)
            seg = [x for x in gt if k <= x[0] <= td]
            if seg:
                x0, y0 = seg[0][1], seg[0][2]
                dmax = max(((x[1] - x0) ** 2 + (x[2] - y0) ** 2) ** 0.5 for x in seg)
                print(f" GT excursion kill -> disarm: max horizontal distance from the kill position {dmax:.3f} m; "
                      f"max |x| {max(abs(x[1]) for x in seg):.3f}, max |y| {max(abs(x[2]) for x in seg):.3f} m "
                      f"(box +-3 m); at kill ({x0:.2f}, {y0:.2f})")
            print(" during aiding loss (kill .. restart+5 s): FC events:",
                  [e[3][:90] for e in allm(ev, k, r + 5, "FC")])
            print(" watcher events:", [e[3][:90] for e in allm(ev, k, r + 5, "WATCHER")])
            print(" flight script events:", [e[3][:90] for e in allm(ev, k, r + 5, "fs")])
            rows = track(sess)
            seg = [r_ for r_ in rows if k <= r_[0] <= r]
            if seg:
                print(f" GT drift during the loss: dx {seg[-1][2]-seg[0][2]:+.2f} dy {seg[-1][3]-seg[0][3]:+.2f} m")
        elif n.startswith("F6a") or n.startswith("F6b"):
            k = g("t_flow_tracker_sig9_w"); ts = g("t_land_send_w"); tt = g("t_toggle_althold_w")
            tl = g("t_land_switch_w"); td = g("t_disarm_seen_w") or tl + 30
            print(f"  flight script killed {g('t_fs_kill_w') - k:+.3f} s before the dependency kill")
            sends = watcher_lines(sess, k - 0.5, td, r"LAND command sent")
            print(f"  watcher LAND sends (kill .. disarm): {len(sends)}: {[(round(w - k, 3), x[:70]) for w, x in sends]}")
            print("  watcher ACK / stop lines:", [(round(w - k, 3), x[:110]) for w, x in
                                                 watcher_lines(sess, k - 0.5, td, r"LAND ACK|re-send stopped")])
            print("  relay stripped/held/LAND frames:", [(round(w - k, 3), x[:80]) for w, x in
                                                        relay_lines(sess, k - 0.5, tl, r"stripped|held|DO_SET_MODE")])
            print(f"  send -> FC MODE LAND: {iv(cm, ts, first(ev, ts - 0.05, 'FC', 'MODE LAND', ts + 2))}")
            print(f"  switch move -> FC MODE: {iv(cm, tt, first(ev, tt - 0.05, 'FC', 'MODE', tt + 2))}")
            e_alt = first(ev, tt - 0.05, "FC", "MODE ALT_HOLD", tt + 2)
            if e_alt:
                win = allm(ev, e_alt[0] + 0.001, min(e_alt[0] + 10, tl), "FC", "MODE")
                print(f"  FC MODE events in the {min(10, tl - e_alt[0]):.2f} s after ALT_HOLD (until the LAND switch): "
                      f"{[e[3] for e in win] or 'none'}")
            print("  FC GCS failsafe texts after the kill:", [e[3][:70] for e in allm(ev, k, tl, "op.TEXT", "ailsafe")])
        elif n == "F6c":
            k = g("t_flow_tracker_sig9_w")
            sends = watcher_lines(sess, k - 0.5, k + 6, r"LAND command sent")
            print(f"  watcher LAND sends: {[(round(w - k, 3), x[:60]) for w, x in sends]}")
            if len(sends) >= 2:
                print(f"  send 1 -> send 2: {sends[1][0] - sends[0][0]:.3f} s")
            print("  watcher ACK / stop lines:", [(round(w - k, 3), x[:110]) for w, x in
                                                 watcher_lines(sess, k - 0.5, k + 6, r"LAND ACK|re-send stopped")])
            print("  relay:", [(round(w - k, 3), x[:80]) for w, x in relay_lines(sess, k - 2, k + 6, r"DO_SET_MODE|drop")])
            for i, (w, _) in enumerate(sends):
                print(f"  send {i + 1} -> next FC MODE LAND: {iv(cm, w, first(ev, w - 0.05, 'FC', 'MODE LAND', k + 6))}")
        elif n == "B7b":
            print("  warm-up:", t.get("warmup"), " FC heartbeat rate on the link:", t.get("hb_rate_hz"), "Hz")
            out = []
            for c in t["commands"]:
                e = first(ev, c["t_send_w"] - 0.05, "FC", "MODE LAND", c["t_send_w"] + 3)
                out.append(e[0] - c["t_send_w"] if e else None)
                ack = f"{c['t_ack_w'] - c['t_send_w']:.3f}" if c.get("t_ack_w") else "none"
                print(f"  cmd {c['i']}: tries {c['tries']} ack {ack} s  MODE LAND "
                      f"{(e[0] - c['t_send_w']) if e else None}  stopped: {c.get('stopped')}  m0 {c.get('m0')}")
            v = np.array([x for x in out if x is not None])
            print(f" send -> MODE LAND (W): n={len(v)} median {np.median(v):.3f} p99 {np.percentile(v, 99):.3f} "
                  f"max {v.max():.3f}")
        elif n.startswith("B10a"):
            for kk in ("t_althold_w", "t_stabilize_w", "t_althold2_w", "t_land_switch_w"):
                a = g(kk)
                print(f" {kk} -> MODE:", iv(cm, a, first(ev, a - 0.05, "FC", "MODE")))
            a, b = g("t_althold_w"), g("t_land_switch_w")
            print(" MODE events between ALT_HOLD and LAND switch:", [e[3] for e in allm(ev, a - 0.1, b, "FC", "MODE")])
        elif n == "B10b":
            for kk in sorted((k_ for k_ in t if k_.startswith("t_") and t[k_]), key=lambda x: t[x]):
                print(f"  {kk}: {t[kk] - t['t_althold_w']:+.3f}")
            a = g("t_althold_w"); b = g("t_land_switch_w")
            for e in allm(ev, a - 0.2, b + 0.5):
                if e[2].startswith(("FC", "WATCHER", "fs")) and re.search("MODE|ERR|LAND|WatcherLost|H10|BREACH|"
                                                                           "CONFIRMED|Failsafe|failsafe", e[3]):
                    print(f"   {e[0] - a:+8.3f}  {e[2]:8s} {e[3][:120]}")
        else:
            for k, v in t.items():
                if k not in ("test",):
                    print(f"  {k}: {str(v)[:300]}")


def hb_after(sess, k):
    p = os.path.join(sess, "watcher", "mocap_watch_heartbeat.csv")
    rows = [l.split(",") for l in open(p).readlines()[1:]]
    before = [r for r in rows if float(r[0]) < k and r[8] == "1"]
    after = [r for r in rows if float(r[0]) >= k and r[8] == "1"]
    lastb = float(before[-1][0]) - k if before else None
    return {"last_mav_hb_before": lastb, "mav_hb_sent_after_inject_within_15s_at":
            [round(float(r[0]) - k, 2) for r in after if float(r[0]) < k + 15]}


if __name__ == "__main__":
    for s in sys.argv[1:]:
        report(s)
