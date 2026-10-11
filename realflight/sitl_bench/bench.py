#!/usr/bin/env python3
"""SITL ONLY (item 2c): the watcher bench B0-B10 in SITL with a simulated mocap feed, using the REAL-HARDWARE watcher
(realflight/watcher). Pre-registered criteria: docs/handovers/2026-10-11_watcher_sitl_bench.md §1 (committed first).
VERIFICATION flights only, named wbench_*; never result data. Run through tools/run_wbench.sh (FLIGHT_LOCK).

Every injection and observation is logged with the wall clock (tests.jsonl, op_events.csv, the watcher's STOP_LOG,
the flight-script logs, forwarder.csv, relay_events.txt); FC events come from the session's own dataflash logs and
are mapped to the wall clock with op_systime.csv by analyse.py.
"""
import json
import os
import signal
import sys
import time

from realflight.sitl_bench.stack import BOX, P, REPO, RC, VENV_PY, Operator, Stack, tail_has

OUTROOT = os.path.expanduser("~/thesis_data/wbench")
HOLD = [{"takeoff": 1.5}, {"hold": 10}, {"hold": 60}]          # inject at "STEP 2 hold start"
GUIDED, ALT_HOLD, STABILIZE, LAND = 4, 2, 0, 9
SW = {"guided": 1555, "alt_hold": 1300, "alt_hold2": 1685, "stabilize": 1425, "land": 1850}


class Abort(Exception):
    pass


class Bench:
    def __init__(self, session):
        self.session = session
        self.out = os.path.join(OUTROOT, f"wbench_{session}_{time.strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(self.out)
        self._log = open(os.path.join(self.out, "bench.log"), "a", buffering=1)
        self.tests = open(os.path.join(self.out, "tests.jsonl"), "a", buffering=1)
        self.stack = Stack(self.out, ground=(session == "ground"), log=self.log)
        self.nfs = 0

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
        # Amendment A1 (pre-registered fallback 1): an EKF origin, as for any non-GPS ArduPilot vehicle; without it
        # EKF3 on flow reports no position estimate and GUIDED arming fails ("Need Position Estimate", smoke run 1).
        for _ in range(3):
            self.op.m.mav.set_gps_global_origin_send(1, -353632610, 1491652300, 584000, int(time.time() * 1e6))
            time.sleep(0.5)
        self.op.note("OP", "SET_GPS_GLOBAL_ORIGIN sent (A1)")
        snap = {}
        for n in ("AHRS_EKF_TYPE", "FLOW_TYPE", "EK3_SRC1_VELXY", "EK3_SRC1_POSZ", "GPS1_TYPE", "FS_GCS_ENABLE",
                  "FS_GCS_TIMEOUT", "MAV_GCS_SYSID", "MAV_GCS_SYSID_HI", "FS_OPTIONS", "MAV_OPTIONS", "ARMING_RUDDER",
                  "ARMING_SKIPCHK", "FS_EKF_ACTION", "FS_THR_ENABLE", "DISARM_DELAY", "LOG_REPLAY", "LOG_DISARMED",
                  "SIM_FLOW_ENABLE", "SIM_RC_FAIL", "SCR_ENABLE", "FLTMODE_CH"):
            snap[n] = self.op.param_get(n)
        self.rec("param_snapshot_start", params=snap)
        if snap["AHRS_EKF_TYPE"] != 3 or snap["MAV_GCS_SYSID"] != 211 or snap["FS_GCS_ENABLE"] != 5:
            raise Abort(f"parameters not as loaded: {snap}")

    def teardown(self):
        try:
            self.rc.run = False
            self.op.run = False
        except AttributeError:
            pass
        self.stack.teardown()

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

    def wait_disarmed(self, cap=150):
        return self.op.wait("disarmed", lambda: self.op.armed is False, cap, self.alive)

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

    def hover(self, name, inject, profile=None, h10=False, marker="STEP 2 hold start", observe=None, cap=180):
        """Arm via the flight-script gate, take off, hold; at `marker` (+1 s) call inject() -> dict of wall times.
        Then wait for the disarm (or `observe` seconds if given), and record."""
        self.log(f"===== {name}")
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
        self.rec(name, **info)
        if t_dis is None:
            self.safe_down()
        self.end_flight(fs)
        return info

    # ------------------------------------------------------------------ sessions
    def s_smoke(self):
        self.ensure_watcher()
        self.hover("wbench_smoke", lambda fs: {}, profile=[{"takeoff": 1.5}, {"hold": 15}, {"land": True}],
                   marker="STEP 1 hold start")


def main():
    s = sys.argv[1]
    b = Bench(s)
    code = 0
    try:
        b.setup()
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
