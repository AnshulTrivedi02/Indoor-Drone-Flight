#!/usr/bin/env python3
"""SITL ONLY (bench 2c): the FLIGHT-SCRIPT layer for the watcher bench. A separate process (so B2b can SIGKILL it).

Uses fly_trial.py's OWN watcher gate, unchanged and imported read-only: require_watcher_before_arming, watch_ok,
check_watcher_in_flight (called inside fly_trial.sim_time_now_s), WatcherLost, plus its connect / wait_ready_to_arm /
wait_altitude / land. WATCH_HEARTBEAT must point at the real-hardware watcher's file (same format, G9).

Profile (JSON list), steps:
  {"takeoff": 1.5}                         after arming (fly_trial.wait_altitude)
  {"hold": S}                              position-hold setpoint at the take-off point, re-sent at 2 Hz, S sim s
  {"vel": [vn, ve, vd], "s": S}            velocity setpoints at 5 Hz for S sim s
  {"roll": DEG, "s": S}                    SET_ATTITUDE_TARGET roll DEG (hover thrust) for S sim s, then level
  {"yaw": DEG}                             MAV_CMD_CONDITION_YAW relative DEG, then 4 s sim hold
  {"ground": S}                            stay on the ground, armed, S sim s (ground tests; DISARM_DELAY 0)
  {"land": true}                           fly_trial.land
Markers "STEP <i> <kind> start/end" are logged (wall time) for the operator. After the profile the script lands.
It exits when the FC reports DISARMED (whichever layer landed it).

H10 (--h10-guard; since 2026-10-12 the decision calls the merged fly_trial.fc_mode / fly_trial.H10_PILOT_OR_LAND; real_flights_plan.md §7.2 B10b, the build handover §5 item 6): on WatcherLost the script
does NOT command LAND if the FC is in a pilot mode (STABILIZE 0, ALT_HOLD 2) or already in LAND (9); it logs that
fly_trial.py as-is WOULD have commanded LAND there. Without the flag it behaves as fly_trial.py (LAND on WatcherLost).
"""
import argparse
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # the repo root (fly_trial.py)
os.environ.setdefault("MAVLINK20", "1")
import fly_trial as ft  # noqa: E402
from pymavlink import mavutil  # noqa: E402

M = mavutil.mavlink
PILOT_OR_LAND = {0: "STABILIZE", 2: "ALT_HOLD", 9: "LAND"}


def log(s):
    print(f"[flight_script {time.time():.3f}] {s}", flush=True)


class Done(Exception):
    pass


class Script:
    def __init__(self, a):
        self.a = a
        self.m = ft.connect(a.port)
        # the first HEARTBEAT through MAVProxy can come from another GCS (MAVProxy relays them): pin the FC (system 1)
        self.m.target_system, self.m.target_component = 1, 1
        # pymavlink's set_mode_apm() maps mode names with the vehicle type of the system `self.m.sysid` (the first
        # HEARTBEAT seen, here often a GCS): GUIDED was mapped to 15 ("Mode change to Autotune failed") in hoverA.
        # Use the FC's own heartbeat for the mapping.
        t0 = time.time()
        while time.time() - t0 < 30:
            hb = self.m.recv_match(type="HEARTBEAT", blocking=True, timeout=2)
            if hb is not None and hb.get_srcSystem() == 1 and hb.type != M.MAV_TYPE_GCS:
                break
        self.m.sysid = 1
        log(f"mode mapping from the FC heartbeat: GUIDED={self.m.mode_mapping().get('GUIDED')} "
            f"LAND={self.m.mode_mapping().get('LAND')}")
        self.was_armed = False
        self.landing_cmded = False

    def fc_hb(self):
        st = self.m.sysid_state.get(self.m.target_system)
        return None if st is None else st.messages.get("HEARTBEAT")

    def armed(self):
        hb = self.fc_hb()
        return hb is not None and bool(hb.base_mode & M.MAV_MODE_FLAG_SAFETY_ARMED)

    def mode(self):
        hb = self.fc_hb()
        return None if hb is None else hb.custom_mode

    def now(self):
        """FC sim time; runs fly_trial's in-flight watcher check (may raise WatcherLost); exits on disarm."""
        t = ft.sim_time_now_s(self.m)
        if self.armed():
            self.was_armed = True
        elif self.was_armed:
            raise Done("FC reports DISARMED")
        return t

    def pos_target(self, n, e, alt):
        self.m.mav.set_position_target_local_ned_send(0, self.m.target_system, self.m.target_component,
                                                      M.MAV_FRAME_LOCAL_NED, 0b110111111000, n, e, -alt,
                                                      0, 0, 0, 0, 0, 0, 0, 0)

    def run_step(self, i, st):
        k = [x for x in st if x != "s"][0]
        log(f"STEP {i} {k} start {json.dumps(st)}")
        if k == "takeoff":
            ft.wait_altitude(self.m, st["takeoff"])
            self.alt = st["takeoff"]
            lp = self.m.recv_match(type="LOCAL_POSITION_NED", blocking=True, timeout=3)
            self.n0, self.e0 = (lp.x, lp.y) if lp else (0.0, 0.0)
        elif k == "hold":
            t0 = self.now(); last = 0
            while self.now() - t0 < st["hold"]:
                if time.time() - last > 0.5:
                    self.pos_target(self.n0, self.e0, self.alt); last = time.time()
        elif k == "vel":
            vn, ve, vd = st["vel"]
            t0 = self.now(); last = 0
            while self.now() - t0 < st["s"]:
                if time.time() - last > 0.2:
                    ft.send_velocity(self.m, vn, ve, vd); last = time.time()
            lp = self.m.recv_match(type="LOCAL_POSITION_NED", blocking=True, timeout=3)
            if lp:
                self.n0, self.e0, self.alt = lp.x, lp.y, -lp.z
        elif k == "roll":
            r = math.radians(st["roll"])
            q = [math.cos(r / 2), math.sin(r / 2), 0.0, 0.0]
            t0 = self.now(); last = 0
            while self.now() - t0 < st["s"]:
                if time.time() - last > 0.05:
                    # attitude target, body rates ignored (type_mask bits 0-2); thrust 0.5 = hover-ish
                    self.m.mav.set_attitude_target_send(0, self.m.target_system, self.m.target_component,
                                                        0b00000111, q, 0, 0, 0, 0.5); last = time.time()
            lp = self.m.recv_match(type="LOCAL_POSITION_NED", blocking=True, timeout=3)
            if lp:
                self.n0, self.e0 = lp.x, lp.y
            self.pos_target(self.n0, self.e0, self.alt)
        elif k == "yaw":
            self.m.mav.command_long_send(self.m.target_system, self.m.target_component, M.MAV_CMD_CONDITION_YAW, 0,
                                         abs(st["yaw"]), 30, 1 if st["yaw"] > 0 else -1, 1, 0, 0, 0)
            t0 = self.now()
            while self.now() - t0 < 4.0:
                pass
        elif k == "ground":
            t0 = self.now()
            while self.now() - t0 < st["ground"]:
                pass
        elif k == "land":
            self.land("profile end")
        log(f"STEP {i} {k} end")

    def land(self, why):
        log(f"LAND commanded by the flight script: {why}")
        self.landing_cmded = True
        ft._watch["active"] = False
        self.m.set_mode_apm("LAND")

    def wait_disarm(self, cap=240):
        t0 = time.time()
        while time.time() - t0 < cap:
            hb = self.m.recv_match(type="HEARTBEAT", blocking=True, timeout=2.0)
            if not self.armed() and self.was_armed:
                log("Disarmed - landed.")
                return
        log("WARNING: disarm not seen within cap")

    def main(self):
        prof = json.load(open(self.a.profile))
        ft.require_watcher_before_arming()
        ft.wait_ready_to_arm(self.m)
        self.was_armed = True
        try:
            for i, st in enumerate(prof):
                try:
                    self.run_step(i, st)
                except ft.WatcherLost as e:
                    mode = self.mode()
                    # wbench4 (2026-10-12): the guard decision uses the MERGED fly_trial.py code (ft.fc_mode, the
                    # FC's own latest HEARTBEAT read passively, and ft.H10_PILOT_OR_LAND); the bench's own copy above
                    # is kept for the log line. fly_trial.land()'s takeover latch is not exercised here (mock test).
                    fmode = ft.fc_mode(self.m)
                    if self.a.h10_guard and fmode in ft.H10_PILOT_OR_LAND:
                        log(f"WatcherLost: {e}. H10 guard (fly_trial.fc_mode={fmode}, bench copy {mode}): FC in "
                            f"{ft.H10_PILOT_OR_LAND[fmode]} -> NOT commanding LAND "
                            "(the pre-H10 fly_trial.py WOULD command LAND here)")
                    else:
                        log(f"WatcherLost: {e} (FC mode {mode})")
                        self.land("watcher lost (fly_trial behaviour)")
                    self.wait_disarm(); return 0
                if not self.armed() and self.was_armed:
                    raise Done("FC reports DISARMED")
            self.land("profile complete")
            self.wait_disarm()
        except Done as d:
            log(f"{d}; flight script exits")
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--h10-guard", action="store_true")
    a = ap.parse_args()
    try:
        return Script(a).main()
    except ft.TrialFailure as e:
        log(f"FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
