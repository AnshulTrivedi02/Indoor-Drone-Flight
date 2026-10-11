#!/usr/bin/env python3
"""SITL ONLY (bench 2c): the pre-registered intervals per test, from one or more session directories.

  python3 -m realflight.sitl_bench.results SESSION_DIR [SESSION_DIR ...]  > results.txt

For each test row in tests.jsonl it prints the intervals the criterion needs, on W (wall) and F (FC) clocks
(handover §1.1). It prints numbers only; the PASS/FAIL wording is applied in the handover against §1.2.
"""
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


def report(sess):
    cm, ev, tests = load(sess)
    print(f"\n######## {os.path.basename(sess)}")
    fd = None
    for t in tests:
        n = t["test"]
        if n.startswith("param_snapshot"):
            continue
        print(f"\n=== {n}")
        g = lambda k: t.get(k)  # noqa: E731
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
        elif n == "B8a":
            k = g("t_flow_bridge_kill_w"); r = g("t_flow_bridge_restart_w")
            print(" during aiding loss (kill .. restart+5 s): FC events:",
                  [e[3][:90] for e in allm(ev, k, r + 5, "FC")])
            print(" watcher events:", [e[3][:90] for e in allm(ev, k, r + 5, "WATCHER")])
            print(" flight script events:", [e[3][:90] for e in allm(ev, k, r + 5, "fs")])
            rows = track(sess)
            seg = [r_ for r_ in rows if k <= r_[0] <= r]
            if seg:
                print(f" GT drift during the loss: dx {seg[-1][2]-seg[0][2]:+.2f} dy {seg[-1][3]-seg[0][3]:+.2f} m")
        elif n == "B7b":
            out = []
            for c in t["commands"]:
                e = first(ev, c["t_send_w"] - 0.05, "FC", "MODE LAND", c["t_send_w"] + 3)
                out.append(e[0] - c["t_send_w"] if e else None)
                print(f"  cmd {c['i']}: tries {c['tries']} ack {c['t_ack_w'] - c['t_send_w']:.3f} s  MODE LAND "
                      f"{(e[0] - c['t_send_w']) if e else None}")
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
