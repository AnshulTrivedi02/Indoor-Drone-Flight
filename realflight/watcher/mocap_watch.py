#!/usr/bin/env python3
"""Real-hardware mocap safety watcher (docs/real_flights_plan.md 7, 7.2; closes G1-G11, see
docs/handovers/2026-10-10_mocap_watcher_build.md). Runs on the GROUND STATION, next to the flight script.

Fail-closed contract, two layers:
  1. Flight-script layer (unchanged from SITL, G9): <out>/watch_heartbeat, rewritten every tick and immediately on
     any change, '<wall time> box=<0|1> bridge=<0|1> pose= id= fc= latch= host=<name>'. fly_trial.py's watch_ok()
     reads it (extra tokens are each one key=value). The file is LOCAL: the watcher and the flight script must run
     on the same machine (pre-registered requirement); the networked path to the vehicle is layer 2.
  2. FC layer (G5, G11): a MAVLink HEARTBEAT from the watcher's OWN system ID (--sysid, never 255) every tick, sent
     ONLY while confirmed. With FS_GCS_ENABLE 5 / FS_GCS_TIMEOUT 3 / MAV_GCS_SYSID = --sysid (watcher_fc.parm) the FC
     lands (disarms if landed) 3 s after the heartbeat stops, and refuses to arm while that failsafe is latched.
On a breach (box incl. height, tilt, stale/untracked/frozen pose, dependency lost) it: latches, alerts (terminal
bell, --alert-cmd, STATUSTEXT to the FC), sends ONE LAND (MAV_CMD_DO_SET_MODE; re-sent only under fc_link's F6 rule:
never once the FC reports LAND, a pilot mode or any mode change it did not command), stops the MAVLink heartbeat and
withdraws the file flags. It never kills processes (G4).

Usage (ground station):
  python3 -m realflight.watcher.mocap_watch OUT_DIR --fc udpin:0.0.0.0:14560 --sysid 211 \
      --mocap-port 9870 --body-name thesis_quad --box=-2,2,-2,2,0,2.5 \
      --dep flow_tracker --dep flow_bridge --liveness-port 9871 --yaw-tie origin

F7 pre-arm yaw check (yawcheck.py; ON by default, fail-closed): while the FC is disarmed, no confirmation unless the
FC's ATTITUDE yaw agrees with the mocap heading (+ the tie) within 5 deg for >= 1 s with mocap valid; informational
only once armed. --yaw-tie origin (default) captures the tie at the FC's EKF-origin broadcast, so the watcher MUST be
running before the origin is set (flight cards); --yaw-tie <deg> is a surveyed constant (compass variant only).
"""
import argparse
import math
import os
import select
import signal
import socket
import subprocess
import sys
import time

from realflight.watcher.core import Config, WatcherCore
from realflight.watcher.fc_link import FcLink, expected_params
from realflight.watcher.liveness import UdpLivenessSocket
from realflight.watcher.mocap import UdpPoseSource


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--fc", required=True, help="pymavlink connection string to the FC (its own link or a MAVProxy "
                    "--out); e.g. udpin:0.0.0.0:14560")
    ap.add_argument("--sysid", type=int, required=True, help="the watcher's own MAVLink system ID (1..254, != FC, "
                    "unique on the network; = the FC's MAV_GCS_SYSID)")
    ap.add_argument("--compid", type=int, default=190)
    ap.add_argument("--fc-sysid", type=int, default=1)
    ap.add_argument("--mocap-host", default="0.0.0.0"); ap.add_argument("--mocap-port", type=int, required=True)
    ap.add_argument("--body-name"); ap.add_argument("--body-id", type=int)
    ap.add_argument("--up-axis", choices=("z", "y"), default="z")
    ap.add_argument("--body-yaw-offset-deg", type=float, default=0.0)
    ap.add_argument("--box", required=True, help="--box=xmin,xmax,ymin,ymax,zmin,zmax (use =, values may be negative) in the z-up watch frame (m); "
                    "zmax = capture-volume top / ceiling margin (G10)")
    ap.add_argument("--tilt-max-deg", type=float, default=60.0)
    ap.add_argument("--stale-s", type=float, default=0.5)
    ap.add_argument("--recover-s", type=float, default=2.0)
    ap.add_argument("--dep", action="append", default=[], help="dependency name (beacon 'n'); repeatable")
    ap.add_argument("--liveness-host", default="0.0.0.0"); ap.add_argument("--liveness-port", type=int, default=0)
    ap.add_argument("--dep-timeout-s", type=float, default=1.0)
    ap.add_argument("--progress-timeout-s", type=float, default=2.0)
    ap.add_argument("--dep-loss", choices=("land", "stop"), default="land",
                    help="hardware: BOTH mean withdraw + ONE LAND + alert (G8); 'stop' kept for SITL compatibility")
    ap.add_argument("--tick-s", type=float, default=1.0)
    ap.add_argument("--stall-s", type=float, default=1.0)
    ap.add_argument("--fs-gcs-timeout", type=float, default=3.0)
    ap.add_argument("--identity", choices=("require", "off"), default="require",
                    help="'off' only for offline tests; a real session requires the B6 identity proof")
    ap.add_argument("--fc-params", choices=("require", "off"), default="require")
    ap.add_argument("--yaw-check", choices=("require", "off"), default="require",
                    help="F7 pre-arm yaw check (yawcheck.py); 'off' only for offline tests and bench tests that are "
                         "not about it")
    ap.add_argument("--yaw-tie", default="origin",
                    help="'origin' (default): capture the mocap/FC yaw tie at the FC's EKF-origin broadcast (the "
                         "watcher must be running before the origin is set); or a number: the surveyed NED bearing of "
                         "the mocap +x axis in deg (compass variant only)")
    ap.add_argument("--yaw-tol-deg", type=float, default=5.0)
    ap.add_argument("--lua-auth", action="store_true", help="also require SCR_ENABLE 1 (the G6(ii) arming-auth script)")
    ap.add_argument("--alert-cmd", help="shell command run (non-blocking) on every alert, e.g. an audible alarm")
    ap.add_argument("--land-retry-s", type=float, default=0.3)
    ap.add_argument("--land-evidence-s", type=float, default=0.2,
                    help="F6: a LAND is re-sent only after an FC heartbeat this long after the send still shows the "
                         "pre-LAND autopilot mode")
    ap.add_argument("--exit-after-s", type=float, help="tests only")
    a = ap.parse_args(argv)
    if a.yaw_tie == "origin":
        a.yaw_tie_deg = None
    else:
        try:
            a.yaw_tie_deg = float(a.yaw_tie)
        except ValueError:
            ap.error("--yaw-tie must be 'origin' or a number of degrees")
    a.box = tuple(float(v) for v in a.box.split(","))
    if len(a.box) != 6:
        ap.error("--box needs 6 values (x/y/z min,max): the height limit is mandatory (G10)")
    return a


class Watcher:
    def __init__(self, a):
        self.a = a
        os.makedirs(a.out, exist_ok=True)
        self.cfg = Config(box=a.box, tilt_max_deg=a.tilt_max_deg, stale_s=a.stale_s, recover_s=a.recover_s,
                          deps=tuple(a.dep), dep_timeout_s=a.dep_timeout_s, progress_timeout_s=a.progress_timeout_s,
                          dep_loss=a.dep_loss, stall_s=a.stall_s, body_name=a.body_name, body_id=a.body_id,
                          up_axis=a.up_axis, body_yaw_offset_deg=a.body_yaw_offset_deg,
                          require_identity=a.identity == "require", require_fc_params=a.fc_params == "require",
                          require_yaw=a.yaw_check == "require", yaw_tie_deg=a.yaw_tie_deg, yaw_tol_deg=a.yaw_tol_deg)
        self.core = WatcherCore(self.cfg)
        self.slog = open(os.path.join(a.out, "STOP_LOG.txt"), "a")
        self.track = open(os.path.join(a.out, "mocap_watch_track.csv"), "a")
        if self.track.tell() == 0:
            self.track.write("t_rx_wall,t_mocap,frame,body,tracked,x,y,z,tilt_deg,inside,latency_s\n")
        self.hblog = open(os.path.join(a.out, "mocap_watch_heartbeat.csv"), "a")
        if self.hblog.tell() == 0:
            self.hblog.write("t_wall,confirmed,box,bridge,pose,id,fc,latch,mav_hb_sent,reasons\n")
        self.ylog = open(os.path.join(a.out, "mocap_watch_yaw.csv"), "a")
        if self.ylog.tell() == 0:
            self.ylog.write("t_wall,fc_armed,fc_yaw_deg,mocap_hdg_deg,tie_deg,diff_deg,gate_ok,why\n")
        self.host = socket.gethostname()
        self.mocap = UdpPoseSource(a.mocap_host, a.mocap_port)
        self.live = UdpLivenessSocket(a.liveness_host, a.liveness_port)
        self.fc = FcLink(a.fc, a.sysid, a.compid, a.fc_sysid, log=self.note, land_retry_s=a.land_retry_s,
                        land_evidence_s=a.land_evidence_s)
        self.exp = expected_params(a.sysid, a.fs_gcs_timeout, a.lua_auth)
        self.running = True
        self.last_conf = None
        self.last_reasons = None
        self.last_param_req = self.last_stream_req = -1e9
        self.att_seen = False
        self.note(f"mocap watcher start: sysid {a.sysid}, mocap udp {self.mocap.port}, liveness udp {self.live.port}, "
                  f"box {a.box}, deps {a.dep}, dep-loss {a.dep_loss}"
                  + (" (== land on hardware, G8)" if a.dep_loss == "stop" else ""))
        with open(os.path.join(a.out, "mocap_watch_ports.txt"), "w") as f:
            f.write(f"mocap={self.mocap.port}\nliveness={self.live.port}\npid={os.getpid()}\n")

    def note(self, s):
        self.slog.write(f"{time.strftime('%H:%M:%S')} {time.time():.3f} {s}\n"); self.slog.flush()
        print(s, file=sys.stderr, flush=True)

    def alert(self, text):
        self.note("ALERT " + text)
        sys.stderr.write("\a"); sys.stderr.flush()
        try:
            self.fc.statustext("WATCH " + text)
        except OSError:
            pass
        if self.a.alert_cmd:
            subprocess.Popen(self.a.alert_cmd, shell=True, stdin=subprocess.DEVNULL)

    def handle(self, acts):
        for a in acts:
            if a[0] == "LOG":
                self.note(a[1])
            elif a[0] == "ALERT":
                self.alert(a[1])
                if a[1].startswith("BREACH"):
                    with open(os.path.join(self.a.out, "BREACH.txt"), "a") as f:
                        p = self.core.p
                        pos = "" if p is None else f" x={p[0]:.3f} y={p[1]:.3f} z={p[2]:.3f}"
                        f.write(f"{time.time():.3f} {a[1]}{pos}\n")
            elif a[0] == "LAND":
                self.fc.command_land(a[1])

    def write_file(self, now, hb_sent):
        f, reasons = self.core.flags(now)
        line = (f"{time.time():.3f} box={f['box']} bridge={f['bridge']} pose={f['pose']} id={f['id']} fc={f['fc']} "
                f"latch={f['latch']} yaw={f['yaw']} host={self.host}\n")
        tmp = os.path.join(self.a.out, "watch_heartbeat.tmp")
        with open(tmp, "w") as fh:
            fh.write(line)
        os.replace(tmp, os.path.join(self.a.out, "watch_heartbeat"))
        conf = int(f["box"] and f["bridge"])
        self.hblog.write(f"{time.time():.3f},{conf},{f['box']},{f['bridge']},{f['pose']},{f['id']},{f['fc']},"
                         f"{f['latch']},{int(hb_sent)},\"{'; '.join(reasons)}\"\n"); self.hblog.flush()

    def fc_events(self, now):
        for ev in self.fc.poll():
            k = ev[0]
            if k == "fc_hb":
                self.core.on_fc_heartbeat(now, ev[1])
            elif k == "att":
                self.att_seen = True
                self.handle(self.core.on_fc_attitude(now, ev[1], ev[2], ev[3], ev[4]))
                if self.cfg.require_yaw:
                    self.log_yaw(now)
            elif k == "origin":
                self.note(f"FC GPS_GLOBAL_ORIGIN lat={ev[1]} lon={ev[2]}")
                self.handle(self.core.on_fc_origin(now))
            elif k == "param":
                ok, why = self.fc.verify_params(self.exp)
                if ok is not None and (ok, why) != (self.core.params_ok, self.core.params_why):
                    self.core.on_params(ok, why)
                    (self.note if ok else self.alert)(f"FC parameter check: {why}")
            elif k == "collision":
                self.handle(self.core.on_sysid_collision(now, ev[1]))
            elif k == "fc_text":
                self.note(f"FC: {ev[1]}")

    def log_yaw(self, now):
        y = self.core.yaw
        deg = lambda v: "" if v is None else f"{math.degrees(v):.3f}"  # noqa: E731
        ok, why = y.ok(now, self.core.fc_armed, self.core.pose_fresh(now)[0])
        self.ylog.write(f"{time.time():.3f},{self.core.fc_armed},{deg(y.fc_yaw)},{deg(y.moc_hdg)},{deg(y.tie)},"
                        f"{deg(y.diff)},{int(ok)},\"{why}\"\n")
        self.ylog.flush()

    def run(self):
        a = self.a
        t_end = None if a.exit_after_s is None else time.monotonic() + a.exit_after_s
        next_tick = time.monotonic()
        while self.running and (t_end is None or time.monotonic() < t_end):
            it0 = time.monotonic()
            self.handle(self.core.loop_start(it0))                     # self-stall check FIRST (B3b)
            try:
                select.select([self.mocap, self.live, self.fc.fileno()], [], [], 0.02)
            except (InterruptedError, ValueError):
                pass
            now = time.monotonic()
            for s in self.mocap.poll():
                acts = self.core.on_pose(s.t_rx, s)
                if self.core.p is not None:
                    p = self.core.p
                    self.track.write(f"{s.t_rx_wall:.4f},{s.t_mocap:.4f},{s.frame_no},{s.body_name}#{s.body_id},"
                                     f"{s.tracked},{p[0]:.4f},{p[1]:.4f},{p[2]:.4f},{self.core.tilt:.2f},"
                                     f"{int(self.core.inside)},{s.t_rx_wall - s.t_mocap:.4f}\n")
                self.handle(acts)
            for d in self.live.drain():
                self.core.on_beacon(now, d)
            self.fc_events(now)
            # FC housekeeping: params (until verified, then every 30 s) and the ATTITUDE stream
            if self.cfg.require_fc_params and now - self.last_param_req > (30.0 if self.core.params_ok else 2.0):
                self.fc.request_params(list(self.exp)); self.last_param_req = now
            # re-asserted every 2 s, always: MAVProxy/the FC can silently override a one-shot SET_MESSAGE_INTERVAL
            # (the attitude_bridge.py / RANGEFINDER lesson), and the identity check needs ATTITUDE >= ~10 Hz
            if now - self.last_stream_req > 2.0:
                self.fc.request_streams(); self.last_stream_req = now
            self.fc.service()
            was_latched = self.core.latched is not None
            self.handle(self.core.tick(now))
            if was_latched and self.core.latched is None:
                self.fc.reset_episode()
            conf = self.core.confirmed(now)
            sent = False
            if now >= next_tick or conf != self.last_conf:
                # guard: never send after an unnoticed stall inside this iteration
                if time.monotonic() - it0 > self.cfg.stall_s:
                    self.handle(self.core.loop_start(time.monotonic()))
                    conf = self.core.confirmed(time.monotonic())
                if conf and now >= next_tick:
                    self.fc.send_heartbeat(); sent = True
                self.write_file(now, sent)
                if now >= next_tick:
                    next_tick = now + a.tick_s
                reasons = "; ".join(self.core.flags(now)[1]) or "all checks pass"
                if conf != self.last_conf or reasons != self.last_reasons:
                    self.note(f"confirmation {int(conf)}: {reasons}")
                self.last_conf, self.last_reasons = conf, reasons
        self.shutdown()

    def shutdown(self):
        # fail-closed exit: withdraw the file flags; the MAVLink heartbeat simply stops (FC failsafe after 3 s)
        tmp = os.path.join(self.a.out, "watch_heartbeat.tmp")
        with open(tmp, "w") as fh:
            fh.write(f"{time.time():.3f} box=0 bridge=0 pose=0 id=0 fc=0 latch=1 host={self.host}\n")
        os.replace(tmp, os.path.join(self.a.out, "watch_heartbeat"))
        with open(os.path.join(self.a.out, "mocap_watch_summary.txt"), "w") as f:
            f.write(f"heartbeats_sent={self.fc.hb_sent}\nsent={self.fc.sent}\nbreaches={self.core.n_breach}\n"
                    f"latched={self.core.latched}\nidentity={self.core.ident.state} ({self.core.ident.why})\n"
                    f"identity_max_rp_diff_deg={self.core.ident.max_rp_diff:.2f}\n"
                    f"fc_attitude_rate_hz={self.core.ident.att_rate():.1f}\n"
                    f"wrong_bodies={self.core.wrong_bodies}\nmax_loop_gap_s={self.core.max_gap:.3f}\n"
                    f"land={self.fc.land}\nmocap_bad_packets={self.mocap.bad}\n"
                    f"yaw_check={'require' if self.cfg.require_yaw else 'off'} ({self.core.yaw.tie_why})\n"
                    f"yaw_max_diff_disarmed_deg={self.core.yaw.max_diff_disarmed:.2f}\n"
                    f"yaw_max_diff_armed_deg={self.core.yaw.max_diff_armed:.2f}\n")
        self.note("watcher exit: heartbeat withdrawn")
        for c in (self.mocap, self.live, self.fc):
            c.close()


def main(argv=None):
    a = parse(argv)
    w = Watcher(a)

    def stop(signum, _):
        w.note(f"signal {signum}: exiting fail-closed (heartbeat withdrawn)")
        w.running = False
    signal.signal(signal.SIGINT, stop); signal.signal(signal.SIGTERM, stop)
    w.run()


if __name__ == "__main__":
    main()
