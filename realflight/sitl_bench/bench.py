#!/usr/bin/env python3
"""SITL ONLY (item 2c): the watcher bench B0-B10 in SITL with a simulated mocap feed, using the REAL-HARDWARE watcher
(realflight/watcher). Pre-registered criteria: docs/handovers/2026-10-11_watcher_sitl_bench.md §1 (committed first).
VERIFICATION flights only, named wbench_* (2026-10-11) and wbench2_* (the 2026-10-12 re-run after F6, pre-registered in
docs/handovers/2026-10-12_watcher_bench_rerun.md §1); never result data. Run through tools/run_wbench.sh (FLIGHT_LOCK):
  bench.py <session> [--from TEST] [--prefix wbench2]
--from skips every test before TEST in that session (recovery after an aborted session, without editing code).

Every injection and observation is logged with the wall clock (tests.jsonl, op_events.csv, the watcher's STOP_LOG,
the flight-script logs, forwarder.csv, relay_events.txt); FC events come from the session's own dataflash logs and
are mapped to the wall clock with op_systime.csv by analyse.py.
"""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time

from realflight.sitl_bench.stack import BOX, P, REPO, RC, VENV_PY, Operator, Stack, tail_has

M_REQUEST_MESSAGE = 512      # MAV_CMD_REQUEST_MESSAGE

OUTROOT = os.path.expanduser("~/thesis_data/wbench")
HOLD = [{"takeoff": 1.5}, {"hold": 10}, {"hold": 60}]          # inject at "STEP 2 hold start"
GUIDED, ALT_HOLD, STABILIZE, LAND = 4, 2, 0, 9
SW = {"guided": 1555, "alt_hold": 1300, "alt_hold2": 1685, "stabilize": 1425, "land": 1850}


class Abort(Exception):
    pass


class Bench:
    def __init__(self, session, prefix="wbench2", start=None, only=None):
        self.session = session
        self.only = only
        self.start_from = start
        self.go = start is None
        self.out = os.path.join(OUTROOT, f"{prefix}_{session}_{time.strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(self.out)
        self._log = open(os.path.join(self.out, "bench.log"), "a", buffering=1)
        self.tests = open(os.path.join(self.out, "tests.jsonl"), "a", buffering=1)
        f7 = session == "f7"
        self.stack = Stack(self.out, ground=(session in ("ground", "lua", "b4a", "f7")), log=self.log,
                           extra_defaults=[f"{REPO}/realflight/sitl_bench/params/wbench_f7.parm"] if f7 else [],
                           lua_at_boot=f7)
        self.nfs = 0
        self.t_start = time.time()
        # provenance: the code under test (watcher + driver) is pinned by the commit
        vcs = "g" + "it"
        head = subprocess.run([vcs, "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run([vcs, "-C", REPO, "status", "--porcelain", "realflight/", "tools/run_wbench.sh"],
                               capture_output=True, text=True).stdout.strip()
        self.log(f"PROVENANCE repo {REPO} HEAD {head}; realflight/ uncommitted changes: {dirty or 'none'}")

    def should_run(self, name):
        """--from: skip tests before `start_from` (by test-name prefix) in this session. --only: run only the tests
        whose name starts with `only` (a single repeat, e.g. after an incomplete manoeuvre; each use is an amendment)."""
        if self.only is not None:
            ok = name.startswith(self.only)
            if not ok:
                self.log(f"skipping {name} (--only {self.only})")
            return ok
        if not self.go and name.startswith(self.start_from):
            self.go = True
        if not self.go:
            self.log(f"skipping {name} (--from {self.start_from})")
        return self.go

    def log(self, s):
        line = f"{time.strftime('%H:%M:%S')} {time.time():.3f} {s}"
        print(line, flush=True)
        self._log.write(line + "\n")

    def rec(self, name, **kw):
        kw["test"] = name
        self.tests.write(json.dumps(kw) + "\n")
        self.log(f"RECORD {json.dumps(kw)}")

    # ------------------------------------------------------------------ setup
    def alive(self):
        return self.stack.alive("gz") and self.stack.alive("sitl")

    def setup(self):
        self.stack.start()
        self.op = Operator(self.out, self.log)
        self.rc = RC(self.log)
        if self.op.wait("FC heartbeat on the operator link", lambda: self.op.armed is not None, 60, self.alive) is None:
            raise Abort("no FC heartbeat on SERIAL2")
        # Amendment A1, FIXED 2026-10-12 (the B8a harness fault): the origin is sent only AFTER EKF3 has initialised
        # and is then VERIFIED (GPS_GLOBAL_ORIGIN received). The 2026-10-11 driver sent it 3x in the first ~1.5 s,
        # before "EKF3 IMU0 initialised", and EKF3 refused it (setOriginLLH, AP_NavEKF3_Control.cpp:692): no origin
        # in any session, so Copter::ekf_check() returned at once (ekf_check.cpp:35-39).
        self.establish_origin(self.t_start, 0)
        snap = {}
        for n in ("AHRS_EKF_TYPE", "FLOW_TYPE", "EK3_SRC1_VELXY", "EK3_SRC1_POSZ", "GPS1_TYPE", "FS_GCS_ENABLE",
                  "FS_GCS_TIMEOUT", "MAV_GCS_SYSID", "MAV_GCS_SYSID_HI", "FS_OPTIONS", "MAV_OPTIONS", "ARMING_RUDDER",
                  "ARMING_SKIPCHK", "FS_EKF_ACTION", "FS_THR_ENABLE", "DISARM_DELAY", "LOG_REPLAY", "LOG_DISARMED",
                  "SIM_FLOW_ENABLE", "SIM_RC_FAIL", "SCR_ENABLE", "FLTMODE_CH", "EK3_IMU_MASK", "FS_EKF_THRESH"):
            snap[n] = self.op.param_get(n)
        self.rec("param_snapshot_start", params=snap)
        if snap["AHRS_EKF_TYPE"] != 3 or snap["MAV_GCS_SYSID"] != 211 or snap["FS_GCS_ENABLE"] != 5:
            raise Abort(f"parameters not as loaded: {snap}")

    ORIGIN = (-353632610, 1491652300, 584000)    # lat/lon 1e7 deg, alt mm: SITL's default home (CMAC), as 2026-10-11

    def establish_origin(self, t_since, mp_off, cap=120):
        """Send SET_GPS_GLOBAL_ORIGIN only after EVERY EKF3 core has reported "EKF3 IMUn initialised" in this boot
        (STATUSTEXT on the operator link since t_since, or in MAVProxy's console log after byte mp_off), then verify
        it: a GPS_GLOBAL_ORIGIN from the FC received after the send (the AHRS sends one when the origin becomes valid,
        AP_AHRS.cpp:439, and on MAV_CMD_REQUEST_MESSAGE 49). Retried at 1 Hz; the session aborts without a verified
        origin. The dataflash ORGN record is checked after the session (results.py)."""
        mask = int(self.op.param_get("EK3_IMU_MASK"))
        cores = [f"IMU{i}" for i in range(8) if mask & (1 << i)]
        mp = os.path.join(self.out, "mavproxy.log")
        t0 = time.time()

        def inited(c):
            pat = f"EKF3 {c} initialised"
            if any(pat in x[2] for x in self.op.texts_since(t_since) if x[1] == 1):
                return True
            try:
                with open(mp) as f:
                    f.seek(mp_off)
                    return pat in f.read()
            except OSError:
                return False
        if self.op.wait("EKF3 initialised (all cores)", lambda: all(inited(c) for c in cores), cap, self.alive) is None:
            raise Abort(f"EKF3 did not report initialised for {cores} within {cap} s")
        t_gate = time.time()
        self.log(f"EKF3 initialised on {cores} ({t_gate - t0:.1f} s); sending the origin")
        lat, lon, alt = self.ORIGIN
        for k in range(1, 31):
            t_send = time.time()
            self.op.m.mav.set_gps_global_origin_send(1, lat, lon, alt, int(time.time() * 1e6))
            self.op.note("OP", f"SET_GPS_GLOBAL_ORIGIN sent (A1 fixed), try {k}")
            time.sleep(0.2)
            self.op.m.mav.command_long_send(1, 1, M_REQUEST_MESSAGE, 0, 49, 0, 0, 0, 0, 0, 0)
            ok = self.op.wait("GPS_GLOBAL_ORIGIN", lambda: any(o[0] >= t_send for o in self.op.origins), 1.0)
            if ok is not None:
                o = [o for o in self.op.origins if o[0] >= t_send][0]
                match = (o[1], o[2]) == (lat, lon)
                self.rec("origin", t_gate_w=t_gate, t_sent_w=t_send, t_verified_w=o[0], tries=k, cores=cores,
                         lat=o[1], lon=o[2], alt_mm=o[3], matches_sent=match)
                if not match:
                    raise Abort(f"origin verified but not the one sent: {o}")
                return o[0]
        raise Abort("EKF origin not verified after 30 tries")

    def teardown(self):
        try:
            self.rc.run = False
            self.op.run = False
        except AttributeError:
            pass
        self.stack.teardown()
        import glob
        import shutil
        d = os.path.join(self.out, "dataflash")
        os.makedirs(d, exist_ok=True)
        for f in sorted(glob.glob(os.path.join(self.stack.cwd, "logs", "*.BIN"))):
            if os.path.getmtime(f) >= self.t_start - 1:
                shutil.copy2(f, d)
                self.log(f"dataflash copied: {f}")

    # ------------------------------------------------------------------ helpers
    def ensure_watcher(self, *extra, cap=90, restart=False):
        if restart or not self.stack.alive("watcher"):
            self.stack.start_watcher(*extra)
        if self.op.wait("watcher confirmed", lambda: self.stack.confirmed(), cap, self.alive) is None:
            raise Abort(f"watcher did not confirm within {cap} s: {self.stack.watch_file()}")
        self.log(f"watcher confirmed: {self.stack.watch_file()[1]}")

    def flight(self, profile, h10=False):
        self.nfs += 1
        name = f"fs{self.nfs:02d}"
        pf = os.path.join(self.out, f"{name}_profile.json")
        json.dump(profile, open(pf, "w"))
        env = dict(self.stack.penv, WATCH_HEARTBEAT=os.path.join(self.out, "watcher", "watch_heartbeat"))
        cmd = [VENV_PY, "-m", "realflight.sitl_bench.flight_script", "--port", str(P["fs"]), "--profile", pf]
        if h10:
            cmd.append("--h10-guard")
        self.stack.spawn(name, cmd, env=env)
        return name, os.path.join(self.out, f"{name}.log")

    def wait_text(self, path, pattern, cap, proc=None):
        t0 = time.time()
        while time.time() - t0 < cap:
            if tail_has(path, pattern):
                return time.time()
            if not self.alive():
                raise Abort("stack died")
            if proc and not self.stack.alive(proc):
                return None
            time.sleep(0.1)
        return None

    def gt_z(self):
        """Latest ground-truth height from the forwarder log (dest 0)."""
        try:
            with open(os.path.join(self.out, "forwarder.csv"), "rb") as f:
                f.seek(-2000, 2)
                for l in reversed(f.read().decode(errors="replace").splitlines()):
                    p = l.split(",")
                    if len(p) == 10 and p[1] in ("0", "1"):
                        return float(p[9])
        except (OSError, ValueError):
            pass
        return None

    def wait_disarmed(self, cap=150):
        """Wait for the disarm. If the vehicle is on the ground in LAND (true height < 0.25 m) for 15 s and still armed,
        the operator disarms it, as the safety pilot would; logged (finding: ArduCopter's land detector did not trip
        after a LAND that began with lateral motion, B4b_side first attempt)."""
        t0 = time.time()
        low_since = None
        while time.time() - t0 < cap:
            if not self.alive():
                raise Abort("stack died")
            if self.op.armed is False:
                return time.time()
            z = self.gt_z()
            if self.op.mode == LAND and z is not None and z < 0.25:
                low_since = low_since or time.time()
                if time.time() - low_since > 4:
                    self.log("OPERATOR DISARM: landed in LAND for 4 s, land detector did not trip")
                    self.op.note("OP", "operator disarm: on the ground in LAND 4 s, not disarmed by the FC")
                    self.op.disarm()
                    low_since = time.time() + 1e9
            else:
                low_since = None
            time.sleep(0.1)
        return None

    def wait_armed(self, cap=90):
        return self.op.wait("armed", lambda: self.op.armed is True, cap, self.alive)

    def safe_down(self):
        """Make sure the vehicle is on the ground and disarmed (failure paths)."""
        if self.op.armed:
            self.log("safe_down: vehicle armed; commanding LAND")
            self.op.set_mode(LAND)
            if self.wait_disarmed(150) is None:
                raise Abort("vehicle did not land/disarm")

    def end_flight(self, fs):
        if self.stack.alive(fs):
            self.op.wait("flight script exit", lambda: not self.stack.alive(fs), 20)
            self.stack.stop(fs, signal.SIGTERM, 5)

    def hover(self, name, inject, profile=None, h10=False, marker="STEP 2 hold start", post=None, cap=180):
        """Arm via the flight-script gate, take off, hold; at `marker` (+1 s) call inject() -> dict of wall times.
        Then wait for the disarm (or `observe` seconds if given), and record."""
        if not self.should_run(name):
            return None
        self.log(f"===== {name}")
        self.home_if_needed()
        self.ensure_watcher()
        fs, fsl = self.flight(profile or HOLD, h10=h10)
        t_arm = self.wait_text(fsl, r"Armed\.", 120, fs)
        if t_arm is None:
            self.rec(name, result="NOT_RUN", why="flight script did not arm", fs_log=fsl)
            self.safe_down(); self.end_flight(fs)
            return None
        t_m = self.wait_text(fsl, marker, cap, fs)
        if t_m is None:
            self.rec(name, result="NOT_RUN", why=f"marker '{marker}' not reached", fs_log=fsl)
            self.safe_down(); self.end_flight(fs)
            return None
        time.sleep(1.0)
        info = {"t_arm_w": t_arm, "t_marker_w": t_m, "fs": fs, "fs_log": fsl}
        info.update(inject(fs) or {})
        t_dis = self.wait_disarmed(cap)
        info["t_disarm_seen_w"] = t_dis
        if t_dis is None:
            self.safe_down()
        if post:
            info.update(post(fs) or {})
        self.rec(name, **info)
        self.end_flight(fs)
        self.back_to_guided()
        return info

    def home_if_needed(self):
        """A vehicle that landed outside (or near the edge of) the box keeps the watcher latched, correctly; carry it
        back (disarmed only), as on the bench."""
        try:
            with open(os.path.join(self.out, "forwarder.csv"), "rb") as f:
                f.seek(-2000, 2)
                p = [l.split(",") for l in f.read().decode(errors="replace").splitlines() if l.count(",") == 9]
            x, y = float(p[-1][7]), float(p[-1][8])
        except (OSError, ValueError, IndexError):
            return
        # always (amendment A7): B9b's landing tipped the vehicle over (crash disarm); start every hover upright at home
        if self.op.armed is False:
            self.stack.carry_home()
            time.sleep(3)

    def back_to_guided(self):
        if not self.op.armed and self.op.mode != GUIDED:
            self.op.set_mode(GUIDED)
            self.op.wait("GUIDED", lambda: self.op.mode == GUIDED, 10)

    # ------------------------------------------------------------------ ground helpers
    def script_arm(self, name, profile=(), cap=150):
        """The flight-script gate on the ground: returns (refused_line or None, armed_seen)."""
        fs, fsl = self.flight(list(profile))
        t0 = time.time()
        res = None
        while time.time() - t0 < cap:
            if tail_has(fsl, r"REFUSING TO ARM"):
                res = "refused"; break
            if tail_has(fsl, r"Armed\."):
                res = "armed"; break
            if not self.stack.alive(fs):
                res = "exited"; break
            time.sleep(0.2)
        lines = [l.strip() for l in open(fsl) if "REFUSING" in l or "confirmed before arming" in l or "Armed." in l
                 or "FAILED" in l]
        if res == "armed":
            self.wait_disarmed(60)
        self.end_flight(fs)
        self.safe_down()
        self.back_to_guided()
        return res, lines, fsl

    def stick_arm(self, s=4.0):
        """Transmitter stick arm: STABILIZE, throttle low, yaw right for s seconds."""
        self.rc.set(ch5=SW["stabilize"], ch3=1000)
        self.op.wait("STABILIZE", lambda: self.op.mode == STABILIZE, 10)
        t = self.rc.set(ch4=2000)
        armed = self.op.wait("armed by stick", lambda: self.op.armed is True, s + 1.5)
        self.rc.set(ch4=1500)
        return t, armed is not None

    def mav_arm(self, force=False, mode=STABILIZE):
        sw = SW["stabilize"] if mode == STABILIZE else SW["guided"]
        self.rc.set(ch5=sw, ch3=1000)
        self.op.wait("mode", lambda: self.op.mode == mode, 10)
        t, res = self.op.arm(force=force)
        armed = self.op.wait("armed by MAVLink", lambda: self.op.armed is True, 3)
        texts = [x[2] for x in self.op.texts_since(t - 0.1) if x[1] == 1]
        return t, res, armed is not None, texts

    def disarm_now(self):
        if self.op.armed:
            self.op.disarm()
            self.op.wait("disarmed", lambda: self.op.armed is False, 10)
        self.rc.set(ch5=SW["guided"], ch3=1000)
        self.op.wait("GUIDED", lambda: self.op.mode == GUIDED, 10)

    def reboot(self, settle=12):
        self.op.armed = None
        try:
            mp_off = os.path.getsize(os.path.join(self.out, "mavproxy.log"))
        except OSError:
            mp_off = 0
        t = self.op.reboot()
        self.op.wait("FC back after reboot", lambda: self.op.armed is not None, 90, self.alive)
        self.establish_origin(t, mp_off)      # gated on this boot's EKF3 initialisation, then verified (A1 fixed)
        self.op.wait("EKF settled", lambda: False, settle)
        return t

    # ------------------------------------------------------------------ sessions
    def s_ground(self):
        st = self.stack
        # ---- B1a: watcher never started
        if self.should_run("B1a"):
            res, lines, fsl = self.script_arm("B1a")
            self.rec("B1a", outcome=res, lines=lines, fs_log=fsl, armed_ever=False if res != "armed" else True)
        self.ground_main()

    def ground_main(self):
        """Every ground test after B1a, each guarded by --from (B1c needs a boot in which no watcher ran: run it
        only from the start of a session)."""
        st = self.stack
        # ---- B1c (stock firmware, watcher never started in this boot)
        if self.should_run("B1c"):
            self.op.param_set("ARMING_RUDDER", 2)
            t, armed = self.stick_arm()
            self.rec("B1c_i_stick_rudder2", t_w=t, armed=armed)
            self.disarm_now()
            self.op.param_set("ARMING_RUDDER", 0)
            t, armed = self.stick_arm()
            self.rec("B1c_ii_stick_rudder0", t_w=t, armed=armed)
            self.disarm_now()
            t, r, armed, texts = self.mav_arm(force=False)
            self.rec("B1c_iii_mavlink_nonforce", t_w=t, ack=r, armed=armed, fc_texts=texts)
            self.disarm_now()
            t, r, armed, texts = self.mav_arm(force=True)
            self.rec("B1c_iv_mavlink_force", t_w=t, ack=r, armed=armed, fc_texts=texts)
            self.disarm_now()
        # ---- B0
        if self.should_run("B0"):
            self.ensure_watcher()
            res, lines, fsl = self.script_arm("B0")
            self.rec("B0", outcome=res, lines=lines, fs_log=fsl)
        # ---- B1b / B9d: a dependency down
        if self.should_run("B1b"):
            self.ensure_watcher()
            t = st.send_sig("flow_tracker", 9)
            time.sleep(2.5)
            res, lines, fsl = self.script_arm("B1b")
            self.rec("B1b", t_dep_kill_w=t, outcome=res, lines=lines, fs_log=fsl)
            st.start_deps(("flow_tracker",))
        # ---- B5c: stream stop 3 s, restore, confirmation only after >= 2 s fresh
        if self.should_run("B5c"):
            self.ensure_watcher()
            t_stop = st.fwd(0, mode="stop")
            time.sleep(3.0)
            t_res = st.fwd(0, mode="normal")
            t_conf = self.op.wait("re-confirm", lambda: st.confirmed(), 60)
            time.sleep(3)
            self.rec("B5c", t_stop_w=t_stop, t_restore_w=t_res, t_reconfirm_file_w=t_conf)
            self.back_to_guided()
        # ---- B6a: wrong rigid body (name and ID)
        if self.should_run("B6a"):
            self.ensure_watcher()
            t = st.fwd(0, body_name="other_body", body_id=2)
            time.sleep(2)
            res, lines, fsl = self.script_arm("B6a", cap=90)
            self.rec("B6a", t_wrong_w=t, outcome=res, lines=lines, fs_log=fsl)
            st.fwd(0, body_name="thesis_quad", body_id=1)
        # ---- B1-native: started, confirmed, killed while disarmed -> the FC refuses ("GCS failsafe on")
        if self.should_run("B1_native"):
            self.ensure_watcher()
            time.sleep(3)
            t_kill = st.send_sig("watcher", 9)
            time.sleep(6.0)
            t, r, armed, texts = self.mav_arm(force=False, mode=GUIDED)
            self.rec("B1_native_refusal", t_kill_w=t_kill, t_arm_w=t, ack=r, armed=armed, fc_texts=texts)
            self.disarm_now()
            t_restart = time.time()
            self.ensure_watcher()
            cleared = self.op.wait("GCS Failsafe Cleared", lambda: any("Cleared" in x[2] for x in
                                                                      self.op.texts_since(t_restart)), 20)
            res, lines, fsl = self.script_arm("B1_native_rearm")
            self.rec("B1_native_after_restart", t_restart_w=t_restart, t_cleared_w=cleared, outcome=res, lines=lines)
        if self.should_run("B7b"):
            self.b7b()
        if self.should_run("F6c"):
            self.f6c()
        # ---- B10c: RC failsafe model, armed on the ground
        if self.should_run("B10c"):
            self.ensure_watcher()
            fs, fsl = self.flight([{"ground": 60}])
            if self.wait_text(fsl, r"STEP 0 ground start", 120, fs):
                time.sleep(2)
                t = self.op.param_set("SIM_RC_FAIL", 1)
                td = self.wait_disarmed(30)
                texts = [x[2] for x in self.op.texts_since(t - 0.1) if x[1] == 1]
                self.rec("B10c", t_rcfail_w=t, t_disarm_seen_w=td, fc_texts=texts)
            else:
                self.rec("B10c", result="NOT_RUN", why="did not arm", fs_log=fsl)
            self.op.param_set("SIM_RC_FAIL", 0)
            self.end_flight(fs); self.safe_down(); time.sleep(2); self.back_to_guided()
        # ---- B4a / B4c (amendment A8), now inside the ground session (same ground parameters)
        if self.should_run("B4a"):
            self.s_b4a()
        # ---- B1c-Lua (G6 ii): the draft aux-auth script; 45 s settle after each reboot (the 2026-10-11 re-run's
        # value: with 12 s, (a) was confounded by "Gyros inconsistent")
        if self.should_run("B1c_lua"):
            self.lua_block(settle=45)

    def b7b(self):
        """B7b: 12 LAND commands through the watcher's own FcLink (system ID 213) on the watcher's link (watcher
        stopped), disarmed, each followed by a GUIDED reset. WARM-UP (pre-registered 2026-10-12, before any run):
        before command 0 the link must have received >= 1 FC HEARTBEAT (a udpin link cannot send before it knows its
        peer), request_streams() is called, and >= 3 FC heartbeats must arrive within 1 s (the 5 Hz request took
        effect); the warm-up time is recorded. During the 12 commands the link is polled continuously and
        request_streams() is re-called every 2 s, as the watcher's own loop does (mocap_watch.py). Timing starts at
        each command's send; command i is sent only once a heartbeat received after its GUIDED reset shows GUIDED."""
        st = self.stack
        st.stop("watcher", 15)
        from realflight.watcher.fc_link import FcLink
        fl = FcLink(f"udpin:127.0.0.1:{P['watcher_fc']}", 213, log=self.log)
        hbs = []
        last_req = [0.0]

        def pump(dur, until=None):
            t_end = time.time() + dur
            while time.time() < t_end:
                for e in fl.poll():
                    if e[0] == "fc_hb":
                        hbs.append((time.time(), e[2]))
                fl.service()
                if time.time() - last_req[0] > 2.0:
                    fl.request_streams(); last_req[0] = time.time()
                if until and until():
                    return True
                time.sleep(0.005)
            return False
        t_w0 = time.time()
        if not pump(30, lambda: len(hbs) >= 1):
            self.rec("B7b", result="NOT_RUN", why="no FC heartbeat on the watcher link in 30 s"); fl.close(); return
        t_first_hb = time.time()
        fl.request_streams(); last_req[0] = time.time()
        warm_ok = False
        t_cap = time.time() + 15
        while time.time() < t_cap:
            pump(0.2)
            n1 = [h for h in hbs if h[0] >= time.time() - 1.0 and h[0] > last_req[0]]
            if len(n1) >= 3:
                warm_ok = True; break
        warm = {"t_start_w": t_w0, "t_first_hb_w": t_first_hb, "t_streams_req_w": last_req[0],
                "t_warm_ok_w": time.time() if warm_ok else None, "warm_ok": warm_ok,
                "warmup_s": round(time.time() - t_w0, 3)}
        self.log(f"B7b warm-up: {warm}")
        if not warm_ok:
            self.rec("B7b", result="NOT_RUN", why="warm-up: < 3 FC heartbeats within 1 s after request_streams",
                     warmup=warm); fl.close(); return
        cmds = []
        for i in range(12):
            t_reset = self.op.set_mode(GUIDED)[0]
            pump(1.5)
            ok = pump(3.0, lambda: any(h[0] > t_reset + 0.05 and h[1] == GUIDED for h in hbs[-5:]))
            fl.reset_episode()
            t_send = time.time()
            fl.command_land(f"B7b latency command {i}")
            t_ack = [None]

            def acked():
                if fl.land and fl.land["acked"] and t_ack[0] is None:
                    t_ack[0] = time.time()
                return False
            pump(3.0, acked)
            cmds.append({"i": i, "t_send_w": t_send, "t_ack_w": t_ack[0], "tries": fl.land["tries"],
                         "result": fl.land["result"], "m0": fl.land["m0"], "stopped": fl.land["stopped"],
                         "guided_seen_before_send": bool(ok)})
            pump(1.5)
        fl.close()
        self.rec("B7b", commands=cmds, warmup=warm,
                 hb_rate_hz=round(len([h for h in hbs if h[0] > warm["t_streams_req_w"]]) /
                                  max(1e-3, hbs[-1][0] - warm["t_streams_req_w"]), 2))
        self.back_to_guided()

    def f6c(self):
        """F6c (NEW, pre-registered 2026-10-12): the positive re-send case, on the ground (disarmed, GUIDED). The
        relay drops the watcher's FIRST DO_SET_MODE(LAND) frame (a lost command, not a lost ACK); FC heartbeats keep
        flowing, so rule R must re-send exactly once, after an evidence heartbeat showing GUIDED. Trigger: the
        watcher's dependency loss (SIGKILL of the flow_tracker stub)."""
        st = self.stack
        self.back_to_guided()
        self.ensure_watcher(restart=True)
        time.sleep(3)
        t_arm = st.relay("drop_land_once")
        time.sleep(0.5)
        t_kill = st.send_sig("flow_tracker", 9)
        time.sleep(6)
        self.rec("F6c", t_relay_drop_land_once_w=t_arm, t_flow_tracker_sig9_w=t_kill)
        st.relay("pass")
        st.start_deps(("flow_tracker",))
        self.back_to_guided()

    def lua_block(self, settle, name="B1c_lua"):
        st = self.stack
        st.stop("watcher", 15)
        import shutil
        shutil.copy(os.path.join(REPO, "realflight/params/watcher_arming_auth.lua"),
                    os.path.join(st.cwd, "scripts", "watcher_arming_auth.lua"))
        self.op.param_set("SCR_ENABLE", 1)
        self.reboot(settle)
        lua = {}
        t, r, armed, texts = self.mav_arm(force=False)
        lua["a_mavlink"] = dict(t_w=t, ack=r, armed=armed, fc_texts=texts)
        self.disarm_now()
        self.op.param_set("ARMING_RUDDER", 2)
        t, armed = self.stick_arm()
        lua["a_stick_rudder2"] = dict(t_w=t, armed=armed,
                                      fc_texts=[x[2] for x in self.op.texts_since(t - 0.1) if x[1] == 1])
        self.disarm_now()
        self.op.param_set("ARMING_RUDDER", 0)
        self.ensure_watcher("--lua-auth", restart=True)
        res, lines, fsl = self.script_arm("B1c_lua_b")
        lua["b_script_arm"] = dict(outcome=res, lines=lines)
        self.ensure_watcher("--lua-auth")
        time.sleep(2)
        t_kill = st.send_sig("watcher", 9)
        time.sleep(6.0)
        t, r, armed, texts = self.mav_arm(force=False, mode=GUIDED)
        lua["c_after_kill"] = dict(t_kill_w=t_kill, t_w=t, ack=r, armed=armed, fc_texts=texts)
        self.disarm_now()
        self.reboot(settle)
        t, r, armed, texts = self.mav_arm(force=True)
        lua["d_force"] = dict(t_w=t, ack=r, armed=armed, fc_texts=texts)
        self.disarm_now()
        self.rec(name, **lua)
        self.op.param_set("SCR_ENABLE", 0)


    def s_lua(self):
        """Re-run of B1c-Lua: in the ground session the first arm attempts after the reboot also failed "Gyros
        inconsistent" (12 s settle), which confounds (a). Here the settle after each reboot is 45 s."""
        self.lua_block(settle=45, name="B1c_lua_rerun")

    def _kill(self, n, sig=9):
        return {f"t_{n}_sig{sig}_w": self.stack.send_sig(n, sig)}

    def s_hoverA2(self):
        """hoverA from B4b on (hoverA aborted at B4b_side: the land detector did not trip; see wait_disarmed)."""
        self.s_hoverA(start="B4b_side")

    def s_hoverA3(self):
        """hoverA from B4b_top on (hoverA2 stopped there: the vehicle had landed outside the box after B4b_side, so the
        watcher correctly stayed latched; home_if_needed added)."""
        self.s_hoverA(start="B4b_top")

    def s_hoverA(self, start=None):
        st = self.stack
        go = start is None
        def run(name, *a, **k):
            nonlocal go
            go = go or name == start
            if go:
                self_hover(name, *a, **k)
        self_hover = self.hover
        self.hover = run
        # B2a: watcher SIGKILL, both layers
        self.hover("B2a", lambda fs: self._kill("watcher"))
        # B2b: flight script killed first, then the watcher: the FC layer alone
        def b2b(fs):
            t1 = st.send_sig(fs, 9)
            time.sleep(2.0)
            return {"t_fs_kill_w": t1, "t_watcher_kill_w": st.send_sig("watcher", 9)}
        self.hover("B2b", b2b)
        # B3a: link cut at the relay (both directions)
        self.hover("B3a", lambda fs: {"t_cut_w": st.relay("drop")},
                   post=lambda fs: {"t_restore_w": st.relay("pass")})
        # B3b: watcher SIGSTOP; SIGCONT 1 s after LAND is seen; observe 10 s after the disarm
        def b3b(fs):
            t = st.send_sig("watcher", signal.SIGSTOP)
            tl = self.op.wait("LAND", lambda: self.op.mode == LAND, 20)
            time.sleep(1.0)
            return {"t_sigstop_w": t, "t_land_seen_w": tl, "t_sigcont_w": st.send_sig("watcher", signal.SIGCONT)}
        def obs10(fs):
            t = time.time(); time.sleep(10)
            return {"t_obs_start_w": t, "t_obs_end_w": time.time()}
        self.hover("B3b", b3b, post=obs10)
        # B4b side face (north, y = 3 m) and top face (z = 3.0 m)
        self.hover("B4b_side", lambda fs: {}, marker="STEP 2 vel start",
                   profile=[{"takeoff": 1.5}, {"hold": 10}, {"vel": [0.5, 0, 0], "s": 15}, {"hold": 30}])
        self.hover("B4b_top", lambda fs: {}, marker="STEP 2 vel start",
                   profile=[{"takeoff": 1.5}, {"hold": 10}, {"vel": [0, 0, -0.5], "s": 6}, {"hold": 30}])
        # B5a: stream stopped
        self.hover("B5a", lambda fs: {"t_stop_w": st.fwd(0, mode="stop")},
                   post=lambda fs: {"t_restore_w": st.fwd(0, mode="normal")})
        # B5b: frozen with a tracking flag (observation), then untracked
        def b5b(fs):
            t1 = st.fwd(0, mode="freeze", tracked=1)
            time.sleep(3.0)
            return {"t_freeze_tracked1_w": t1, "t_untracked_w": st.fwd(0, mode="untracked")}
        self.hover("B5b", b5b, post=lambda fs: {"t_restore_w": st.fwd(0, mode="normal", tracked=1)})
        # observations: added latency, frame-counter reset, then a wrong body ID mid-hover
        def obs(fs):
            t1 = st.fwd(0, latency_s=0.15)
            time.sleep(5)
            t2 = st.fwd(0, latency_s=0.0)
            time.sleep(2)
            t3 = st.fwd(0, frame_reset=True)
            time.sleep(4)
            return {"t_latency_on_w": t1, "t_latency_off_w": t2, "t_frame_reset_w": t3,
                    "t_wrong_id_w": st.fwd(0, body_id=2)}
        self.hover("obs_latency_reset_wrongid", obs, post=lambda fs: {"t_restore_w": st.fwd(0, body_id=1)})
        self.hover = self_hover

    def observer(self, mode):
        st = self.stack
        st.stop("observer", 15)
        st.fwd(1, mode=mode, tracked=1)
        st.spawn("observer", st.watcher_cmd(name="observer", sysid=212, fc_port=P["observer_fc"],
                                            mocap_port=P["observer_mocap"], box="-100,100,-100,100,-10,100",
                                            deps=False, identity="require", fc_params="off"))

    def s_hoverB(self):
        st = self.stack
        # B5b-noflag (amendment A6): with tracked = -1 from the start the vehicle at rest gives bit-identical
        # Gazebo poses, so the frozen fallback never let the watcher confirm (hoverB run 1, fail-closed). The source
        # switches to "no tracking flag" once airborne, holds 3 s (moving poses: no action expected), then freezes.
        def noflag(fs):
            t1 = st.fwd(0, tracked=-1)
            time.sleep(3.0)
            return {"t_noflag_w": t1, "t_freeze_w": st.fwd(0, mode="freeze", tracked=-1)}
        self.hover("B5b_noflag", noflag, post=lambda fs: {"t_restore_w": st.fwd(0, mode="normal", tracked=1)})
        st.fwd(0, mode="normal", tracked=1)
        # B6b: the motion-identity check by an observer watcher (system ID 212)
        man = [{"takeoff": 1.5}, {"hold": 8}, {"roll": 12, "s": 0.8}, {"hold": 3}, {"yaw": 90}, {"hold": 4},
               {"land": True}]
        for run, mode in (("right_body", "normal"), ("static_other_body", "static")):
            if not self.should_run(f"B6b_{run}"):
                continue
            self.observer(mode)
            t0 = time.time()
            info = self.hover(f"B6b_{run}", lambda fs: {}, profile=man, marker="STEP 2 roll start")
            st.stop("observer", 15)
            summ = open(os.path.join(self.out, "observer", "mocap_watch_summary.txt")).read()
            os.replace(os.path.join(self.out, "observer", "mocap_watch_summary.txt"),
                       os.path.join(self.out, "observer", f"summary_{run}.txt"))
            idlines = [l.strip() for l in open(os.path.join(self.out, "observer", "STOP_LOG.txt"))
                       if "identity" in l.lower() and float(l.split()[1]) >= t0]
            self.rec(f"B6b_{run}_observer", summary=summ, identity_log=idlines)
        st.fwd(1, mode="normal")
        # B8a: aiding loss (the flow bridge stops); watcher, deps and script untouched; 20 s, then restored
        def b8a(fs):
            t = st.send_sig("flow_bridge_real", 9)
            time.sleep(20)
            st.spawn("flow_bridge_real", [VENV_PY, f"{REPO}/flow_bridge.py", "--ros-args", "-p",
                                          "use_sim_time:=true"], env=st.renv)
            return {"t_flow_bridge_kill_w": t, "t_flow_bridge_restart_w": time.time()}
        self.hover("B8a", b8a, profile=[{"takeoff": 1.5}, {"hold": 10}, {"hold": 35}, {"land": True}])
        # B9a/c: dependency loss, both beacon paths
        self.hover("B9a_flow_tracker_kill", lambda fs: self._kill("flow_tracker"),
                   post=lambda fs: st.start_deps(("flow_tracker",)))
        self.hover("B9a_flow_bridge_kill", lambda fs: self._kill("flow_bridge"),
                   post=lambda fs: st.start_deps(("flow_bridge",)))
        self.ensure_watcher("--dep-loss", "stop", restart=True)
        self.hover("B9b_stop_flow_tracker_kill", lambda fs: self._kill("flow_tracker"),
                   post=lambda fs: st.start_deps(("flow_tracker",)))
        self.ensure_watcher(restart=True)
        self.hover("B9c_flow_tracker_sigstop", lambda fs: self._kill("flow_tracker", signal.SIGSTOP),
                   post=lambda fs: self._kill("flow_tracker", signal.SIGCONT))
        self.hover("B9c_flow_bridge_sigstop", lambda fs: self._kill("flow_bridge", signal.SIGSTOP),
                   post=lambda fs: self._kill("flow_bridge", signal.SIGCONT))
        def unhang(fs):
            st.stop("flow_tracker", signal.SIGKILL, 3); st.start_deps(("flow_tracker",)); return {}
        self.hover("B9_hang_flow_tracker", lambda fs: self._kill("flow_tracker", signal.SIGUSR1), post=unhang)

    def s_b4a(self):
        """B4a / B4c (amendment A8): disarmed, the vehicle is 'carried' (Gazebo set_pose of the real simulated vehicle)
        out through each side face and the top face, and tilted past 60 deg. After each: wait 3 s, record; after the
        first face the flight script tries to arm (must be refused). Carried home and re-confirmed between faces."""
        st = self.stack
        faces = [("north_y+", (0, 3.5, 0.2)), ("east_x+", (3.5, 0, 0.2)), ("south_y-", (0, -3.5, 0.2)),
                 ("west_x-", (-3.5, 0, 0.2)), ("top_z+", (0, 0, 3.3))]
        for i, (face, pos) in enumerate(faces):
            self.ensure_watcher()
            t = st.teleport(*pos)
            time.sleep(3)
            info = {"face": face, "pos": pos, "t_carry_w": t}
            if i == 0:
                res, lines, fsl = self.script_arm("B4a_arm_after_breach", cap=70)
                info.update(arm_attempt=res, arm_lines=lines)
            self.rec(f"B4a_{face}", **info)
            st.carry_home(); time.sleep(2); self.back_to_guided()
        # B4c: tilt 65 deg (roll), dropped from 0.6 m
        self.ensure_watcher()
        t = st.teleport(0, 0, 0.6, q=(0.59637, 0.37993, 0.37993, 0.59637))
        time.sleep(3)
        self.rec("B4c_tilt65", t_carry_w=t)
        st.carry_home(); time.sleep(2); self.back_to_guided()
        self.ensure_watcher()

    def s_hoverB2(self):
        """hoverB from B9c on (hoverB run 2 stopped after B9b: the vehicle tipped over after touching down in LAND,
        so the watcher correctly refused to confirm (tilt 64.7 deg))."""
        st = self.stack
        self.ensure_watcher(restart=True)
        self.hover("B9c_flow_tracker_sigstop", lambda fs: self._kill("flow_tracker", signal.SIGSTOP),
                   post=lambda fs: self._kill("flow_tracker", signal.SIGCONT))
        self.hover("B9c_flow_bridge_sigstop", lambda fs: self._kill("flow_bridge", signal.SIGSTOP),
                   post=lambda fs: self._kill("flow_bridge", signal.SIGCONT))
        def unhang(fs):
            st.stop("flow_tracker", signal.SIGKILL, 3); st.start_deps(("flow_tracker",)); return {}
        self.hover("B9_hang_flow_tracker", lambda fs: self._kill("flow_tracker", signal.SIGUSR1), post=unhang)

    def s_hoverC(self):
        st = self.stack
        rc = self.rc
        # B10a: the pilot takes ALT_HOLD, then STABILIZE briefly, then ALT_HOLD; lands with the LAND switch position
        def b10a(fs):
            rc.set(ch3=1500)
            time.sleep(0.5)
            t1 = rc.set(ch5=SW["alt_hold"]); time.sleep(8)
            t2 = rc.set(ch5=SW["stabilize"]); time.sleep(1.5)
            t3 = rc.set(ch5=SW["alt_hold2"]); time.sleep(8)
            t4 = rc.set(ch5=SW["land"])
            return {"t_althold_w": t1, "t_stabilize_w": t2, "t_althold2_w": t3, "t_land_switch_w": t4}
        def rc_reset(fs):
            rc.set(ch5=SW["guided"], ch3=1000); time.sleep(2); return {}
        self.hover("B10a", b10a, profile=[{"takeoff": 1.5}, {"hold": 10}, {"hold": 60}, {"land": True}],
                   post=rc_reset)
        # B10b: in ALT_HOLD, each automatic path in turn; H10-guarded flight script
        def b10b(fs):
            r = {}
            rc.set(ch3=1500); time.sleep(0.5)
            r["t_althold_w"] = rc.set(ch5=SW["alt_hold"]); time.sleep(3)
            # (1) watcher SIGKILL
            r["t_watcher_kill_w"] = st.send_sig("watcher", 9); time.sleep(10)
            # (2) a NEW watcher confirms; then dependency loss -> its ONE LAND; the pilot toggles the switch
            r["t_watcher_restart_w"] = time.time()
            st.start_watcher()
            r["t_reconfirmed_w"] = self.op.wait("re-confirm", lambda: st.confirmed(), 40)
            time.sleep(3)
            nb = os.path.getsize(os.path.join(self.out, "watcher", "STOP_LOG.txt"))
            r["t_dep_kill_w"] = st.send_sig("flow_tracker", 9)
            tl = self.wait_text(os.path.join(self.out, "watcher", "STOP_LOG.txt"), r"LAND command sent", 6)
            r["t_land_cmd_seen_w"] = tl
            if tl and tail_has(os.path.join(self.out, "watcher", "STOP_LOG.txt"), "LAND command sent", nb):
                self.op.wait("FC in LAND", lambda: self.op.mode == LAND, 3)
                time.sleep(0.3)
                r["t_toggle_w"] = rc.set(ch5=SW["alt_hold2"])
            time.sleep(10)
            st.start_deps(("flow_tracker",))
            # (3) aiding loss in ALT_HOLD
            r["t_flow_bridge_kill_w"] = st.send_sig("flow_bridge_real", 9); time.sleep(15)
            st.spawn("flow_bridge_real", [VENV_PY, f"{REPO}/flow_bridge.py", "--ros-args", "-p",
                                          "use_sim_time:=true"], env=st.renv)
            r["t_flow_bridge_restart_w"] = time.time(); time.sleep(5)
            r["t_land_switch_w"] = rc.set(ch5=SW["land"])
            return r
        self.hover("B10b", b10b, profile=[{"takeoff": 1.5}, {"hold": 10}, {"hold": 200}], h10=True,
                   post=rc_reset, cap=240)
        # F6a / F6b (NEW, pre-registered 2026-10-12): the watcher's LAND from GUIDED, then the pilot's ALT_HOLD
        self.f6_inflight("F6a_acked", ack_strip=False, hb_hold=0.0)
        self.f6_inflight("F6b_unacked", ack_strip=True, hb_hold=0.6)

    def f6_inflight(self, name, ack_strip, hb_hold):
        """Hover in GUIDED. The flight script is SIGKILLed 2.0 s before the injection (as B2b), so the watcher is the
        only process that can command LAND (fly_trial.py's as-is WatcherLost LAND in GUIDED is the open H10 item, not
        F6). Throttle stick centred. Optionally the relay strips every COMMAND_ACK FC -> watcher (the unacknowledged
        LAND) and holds FC HEARTBEATs to the watcher for `hb_hold` s after the LAND frame (so the pilot's switch
        reaches the FC before any heartbeat showing LAND reaches the watcher). Injection: SIGKILL of the flow_tracker
        stub (dependency loss, --dep-loss land) -> the watcher's ONE LAND. The pilot moves the mode switch to ALT_HOLD
        0.33 s after the watcher's send (B10b's measured toggle), observes 10 s, then lands with the LAND switch."""
        st, rc = self.stack, self.rc
        stop_log = os.path.join(self.out, "watcher", "STOP_LOG.txt")

        def inject(fs):
            r = {}
            rc.set(ch3=1500)
            r["t_fs_kill_w"] = st.send_sig(fs, 9)
            time.sleep(2.0)
            if ack_strip:
                r["t_ack_strip_on_w"] = st.relay("ack_strip on")
            if hb_hold:
                r["t_hb_hold_armed_w"] = st.relay(f"hb_hold {hb_hold}")
            time.sleep(0.2)
            nb = os.path.getsize(stop_log)
            r["t_flow_tracker_sig9_w"] = st.send_sig("flow_tracker", 9)
            t_send = None
            t_cap = time.time() + 6
            while time.time() < t_cap and t_send is None:
                with open(stop_log) as f:
                    f.seek(nb)
                    m = re.search(r"LAND command sent \(try 1, wall ([0-9.]+)", f.read())
                if m:
                    t_send = float(m.group(1))
                time.sleep(0.005)
            r["t_land_send_w"] = t_send
            if t_send is None:
                r["error"] = "no watcher LAND within 6 s"
                return r
            time.sleep(max(0.0, t_send + 0.33 - time.time()))
            r["t_toggle_althold_w"] = rc.set(ch5=SW["alt_hold"])
            time.sleep(10.0)
            r["t_land_switch_w"] = rc.set(ch5=SW["land"])
            return r

        def post(fs):
            st.relay("ack_strip off"); st.relay("hb_hold 0")
            st.start_deps(("flow_tracker",))
            rc.set(ch5=SW["guided"], ch3=1000); time.sleep(2)
            return {}
        self.hover(name, inject, profile=[{"takeoff": 1.5}, {"hold": 10}, {"hold": 60}], post=post)

    # ------------------------------------------------------------------ wbench3_f7 (F7 yaw check)
    def _wlog(self):
        try:
            return open(os.path.join(self.out, "watcher", "STOP_LOG.txt")).read()
        except OSError:
            return ""

    def _yaw_last(self):
        try:
            rows = open(os.path.join(self.out, "watcher", "mocap_watch_yaw.csv")).read().splitlines()[1:]
            return rows[-1] if rows else None
        except OSError:
            return None

    def setup_f7(self):
        """wbench3_f7 set-up (pre-registered in docs/handovers/2026-10-12_f7_cards.md §1 before any run). Differs from
        setup() in ONE respect: the watcher (yaw check on, tie captured at the origin broadcast, --lua-auth) is started
        BEFORE the origin is sent, as the flight cards require, and the flow_tracker stub is held down until F7-0's
        rotation so the watcher cannot confirm before it (the yaw check must be the only remaining reason)."""
        st = self.stack
        st.start()
        self.op = Operator(self.out, self.log)
        self.rc = RC(self.log)
        if self.op.wait("FC heartbeat on the operator link", lambda: self.op.armed is not None, 60, self.alive) is None:
            raise Abort("no FC heartbeat on SERIAL2")
        self.t_fc_up = time.time()
        st.stop("flow_tracker", signal.SIGKILL, 3)
        st.start_watcher("--lua-auth", yaw_check="require", yaw_tie="origin")
        yc = os.path.join(self.out, "watcher", "mocap_watch_yaw.csv")
        if self.op.wait("watcher receiving FC ATTITUDE", lambda: os.path.exists(yc) and
                        sum(1 for _ in open(yc)) > 26, 60, self.alive) is None:
            raise Abort("the watcher saw no FC ATTITUDE before the origin step")
        self.establish_origin(self.t_start, 0)
        if self.op.wait("yaw tie", lambda: "tie " in self._wlog() and ("captured" in self._wlog() or
                                                                       "FAILED" in self._wlog()), 15) is None:
            raise Abort("the watcher logged no yaw-tie outcome within 15 s of the origin")
        tie = [l for l in self._wlog().splitlines() if "yaw check: " in l and ("captured" in l or "FAILED" in l)]
        snap = {}
        for n in ("AHRS_EKF_TYPE", "EK3_SRC1_YAW", "COMPASS_USE", "SCR_ENABLE", "FS_GCS_ENABLE", "FS_GCS_TIMEOUT",
                  "MAV_GCS_SYSID", "ARMING_RUDDER", "ARMING_SKIPCHK", "DISARM_DELAY", "EK3_IMU_MASK"):
            snap[n] = self.op.param_get(n)
        self.rec("f7_setup", tie_lines=tie, params=snap, gz_yaw_enu_deg=self._gz_yaw())
        if snap["EK3_SRC1_YAW"] != 0 or snap["SCR_ENABLE"] != 1 or snap["AHRS_EKF_TYPE"] != 3:
            raise Abort(f"parameters not as loaded: {snap}")
        if not tie or "FAILED" in tie[0]:
            raise Abort(f"precondition P1 (tie captured) not met: {tie}")

    def _gz_yaw(self):
        import math
        w, x, y, z = self.stack.current_q()
        return math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))

    def s_f7(self):
        """F7-0, F7-a, F7-b, F7-c, F7-d as pre-registered (docs/handovers/2026-10-12_f7_cards.md §1.2)."""
        st, op = self.stack, self.op
        yaw0 = self._gz_yaw()
        rot = 15.0
        texts_of = lambda t: [x[2] for x in op.texts_since(t - 0.1) if x[1] == 1]  # noqa: E731
        # ---- F7-0: a disagreement before the watcher has ever confirmed in this boot (only the Lua path can refuse)
        t_rot = st.rotate_in_place(yaw0 + rot)
        time.sleep(1.5)
        st.start_deps(("flow_tracker",))
        time.sleep(8.0)
        # B1c-Lua settle: no arm attempt before 45 s after the FC came up ("Gyros inconsistent" confound, 2026-10-11)
        time.sleep(max(0.0, self.t_fc_up + 45.0 - time.time()))
        _, fl = st.watch_file()
        last = [l for l in self._wlog().splitlines() if "confirmation " in l]
        t, r, armed, texts = self.mav_arm(force=False, mode=GUIDED)
        self.rec("F7_0_mav_arm", t_rotate_w=t_rot, ever_confirmed="CONFIRMED: all checks pass" in self._wlog(),
                 file_flags=fl, last_confirmation_line=last[-1] if last else None, yaw_row=self._yaw_last(),
                 t_arm_w=t, ack=r, armed=armed, fc_texts=texts)
        self.disarm_now()
        res, lines, fsl = self.script_arm("F7_0_script")
        self.rec("F7_0_script_arm", outcome=res, lines=lines, fs_log=fsl,
                 ever_confirmed="CONFIRMED: all checks pass" in self._wlog())
        # ---- F7-a: rotated back -> agreement -> allowed
        t_back = st.rotate_in_place(yaw0)
        t_conf = op.wait("watcher confirmed", lambda: st.confirmed(), 30, self.alive)
        res, lines, fsl = self.script_arm("F7_a")
        self.rec("F7_a", t_rotate_back_w=t_back, t_confirmed_file_w=t_conf, outcome=res, lines=lines, fs_log=fsl)
        # ---- F7-b: confirmed, then rotated unseen by the gyros -> withdrawn, no LAND, FC cannot arm
        op.wait("watcher confirmed", lambda: st.confirmed(), 30, self.alive)
        time.sleep(3.0)
        n_land0 = self._wlog().count("LAND command sent")
        t_rot = st.rotate_in_place(yaw0 + rot)
        t_wd = op.wait("watcher withdrawn", lambda: not st.confirmed(), 10, self.alive)
        time.sleep(6.0)
        t, r, armed, texts = self.mav_arm(force=False, mode=GUIDED)
        self.rec("F7_b", t_rotate_w=t_rot, t_withdrawn_file_w=t_wd, yaw_row=self._yaw_last(), t_arm_w=t, ack=r,
                 armed=armed, fc_texts=texts, watcher_land_sends=self._wlog().count("LAND command sent") - n_land0,
                 breach_in_log="BREACH" in self._wlog(), latched_flag=st.watch_file()[1].get("latch"))
        self.disarm_now()
        # ---- F7-c: rotated back -> re-confirmed -> allowed
        t_back = st.rotate_in_place(yaw0)
        t_conf = op.wait("watcher re-confirmed", lambda: st.confirmed(), 30, self.alive)
        t_clr = op.wait("GCS Failsafe Cleared", lambda: any("Cleared" in x for x in texts_of(t_back)), 20)
        res, lines, fsl = self.script_arm("F7_c")
        self.rec("F7_c", t_rotate_back_w=t_back, t_confirmed_file_w=t_conf, t_gcs_fs_cleared_seen_w=t_clr,
                 outcome=res, lines=lines, fs_log=fsl)
        # ---- F7-d: armed (on the ground, GUIDED) -> a disagreement is INFORMATIONAL only
        op.wait("watcher confirmed", lambda: st.confirmed(), 30, self.alive)
        time.sleep(2.0)
        fs, fsl = self.flight([{"ground": 25}])
        t_g = self.wait_text(fsl, r"STEP 0 ground start", 120, fs)
        if t_g is None:
            self.rec("F7_d", result="NOT_RUN", why="did not arm", fs_log=fsl)
        else:
            time.sleep(2.0)
            n_land0 = self._wlog().count("LAND command sent")
            mode0 = op.mode
            t_rot = st.rotate_in_place(yaw0 + rot)
            unconf = []
            t_end = time.time() + 8.0
            while time.time() < t_end:
                if not st.confirmed():
                    unconf.append(round(time.time() - t_rot, 3))
                time.sleep(0.05)
            self.rec("F7_d", t_rotate_w=t_rot, armed_at_end=op.armed, mode_before=mode0, mode_at_end=op.mode,
                     file_unconfirmed_at=unconf[:20], n_unconfirmed_polls=len(unconf),
                     watcher_land_sends=self._wlog().count("LAND command sent") - n_land0,
                     breach_in_log="BREACH" in self._wlog(), informational_logged="INFORMATIONAL" in self._wlog(),
                     yaw_row=self._yaw_last(), fc_texts=texts_of(t_rot))
            td = self.wait_disarmed(90)
            time.sleep(3.0)
            self.rec("F7_d_after_disarm", t_disarm_seen_w=td, confirmed_3s_after_disarm=st.confirmed(),
                     yaw_row=self._yaw_last())
        self.end_flight(fs)
        self.safe_down()
        t_back = st.rotate_in_place(yaw0)
        t_conf = op.wait("watcher re-confirmed", lambda: st.confirmed(), 30, self.alive)
        self.rec("F7_end", t_rotate_back_w=t_back, t_confirmed_file_w=t_conf,
                 land_sends_total=self._wlog().count("LAND command sent"), breach_in_log="BREACH" in self._wlog())

    def s_smoke(self):
        self.ensure_watcher()
        self.hover("wbench_smoke", lambda fs: {}, profile=[{"takeoff": 1.5}, {"hold": 15}, {"land": True}],
                   marker="STEP 1 hold start")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("--from", dest="start", default=None)
    ap.add_argument("--prefix", default="wbench2")
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    s = a.session
    b = Bench(s, prefix=a.prefix, start=a.start, only=a.only)
    code = 0
    try:
        getattr(b, f"setup_{s}", b.setup)()
        getattr(b, f"s_{s}")()
    except Exception as e:  # noqa: BLE001
        b.log(f"SESSION ABORTED: {e!r}")
        code = 1
    finally:
        try:
            if getattr(b, "op", None) and b.op.armed:
                b.safe_down()
        except Exception as e:  # noqa: BLE001
            b.log(f"safe_down failed: {e!r}")
        b.teardown()
        b.log(f"session {s} done, output {b.out}")
    sys.exit(code)


if __name__ == "__main__":
    main()
