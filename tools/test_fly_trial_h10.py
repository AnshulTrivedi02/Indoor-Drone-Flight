#!/usr/bin/env python3
"""H10 (ruling 8, 2026-10-12): offline mock test of fly_trial.py's pilot-takeover guard. No SITL.

Runs fly_trial.main() of the OLD file (`git show <ref>:fly_trial.py`, default HEAD) and of the NEW working-tree file
against the same fake vehicle (fake wall clock, sim time = wall time, scripted FC), and records EVERY command the script
sends (set_mode_apm, and every mav.*_send with its arguments, stamped with the fake time). Then:

  * default scenarios (no pilot takeover, FC never in a pilot mode or LAND before the script's own LAND):
    the NEW command list must be IDENTICAL to the OLD one (same commands, same arguments, same times);
  * declared-difference scenarios: the FC is already in LAND (no pilot) when the failure path runs -> NEW drops the
    redundant LAND (the bench rule's "already in LAND");
  * takeover scenarios: the pilot takes ALT_HOLD/STABILIZE (after a LAND, or before a watcher loss as in B10b(1)) ->
    NEW sends NO LAND and no mode change/command after that point; OLD sends LAND (the hazard). Setpoints the cruise
    loop still sends before it notices a watcher loss are reported (an ArduCopter pilot mode ignores them).

Usage: python3 tools/test_fly_trial_h10.py [--old-ref HEAD] [--json out.json]     (exit 0 = all checks pass)
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types

os.environ.setdefault("MAVLINK20", "1")
from pymavlink import mavutil  # noqa: E402

M = mavutil.mavlink
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDED, LAND, ALT_HOLD, STABILIZE = 4, 9, 2, 0


class Clock:
    def __init__(self):
        self.t = 1000.0

    def time(self):
        return self.t

    def sleep(self, dt):
        self.t += max(0.0, dt)


class Msg:
    def __init__(self, mtype, src=1, **kw):
        self._type, self._src = mtype, src
        self.__dict__.update(kw)

    def get_type(self):
        return self._type

    def get_srcSystem(self):
        return self._src


class Vehicle:
    """A scripted FC. Times are fake-clock seconds; sim time (time_boot_ms) = clock - t_boot."""

    def __init__(self, clock, sc, log):
        self.c, self.sc, self.log = clock, sc, log
        self.t_boot = clock.t
        self.mode, self.armed, self.alt, self.target_alt = GUIDED, False, 0.0, 0.0
        self.t_land = None        # when the FC entered LAND (any cause)
        self.t_pilot = None       # when the pilot took a pilot mode
        self.pending = []         # queued COMMAND_ACKs

    def step(self):
        t = self.c.t - self.t_boot
        sc = self.sc
        # pilot input: takes a pilot mode a fixed delay after the FC first shows LAND, or at a fixed sim time
        pm = sc.get("pilot_after_land")
        if pm and self.t_land is not None and self.t_pilot is None and self.c.t - self.t_land >= pm[0]:
            self.mode, self.t_pilot = pm[1], self.c.t
            self.log.append((round(self.c.t, 3), "PILOT_MODE", pm[1]))
        pa = sc.get("pilot_at")
        if pa and self.armed and self.t_pilot is None and t >= pa[0]:
            self.mode, self.t_pilot = pa[1], self.c.t
            self.log.append((round(self.c.t, 3), "PILOT_MODE", pa[1]))
        if self.t_pilot is not None and self.mode in (ALT_HOLD, STABILIZE) and sc.get("pilot_lands_after") is not None \
                and self.c.t - self.t_pilot >= sc["pilot_lands_after"]:
            self.mode = LAND; self.t_land = self.c.t                       # the pilot's LAND switch position
            self.log.append((round(self.c.t, 3), "PILOT_MODE", LAND))
        if sc.get("watcher_land_at") is not None and self.armed and self.mode == GUIDED and t >= sc["watcher_land_at"]:
            self.mode, self.t_land = LAND, self.c.t                       # the watcher's own LAND
            self.log.append((round(self.c.t, 3), "WATCHER_LAND", LAND))
        # dynamics
        if self.armed and self.mode == GUIDED and self.alt < self.target_alt:
            self.alt = min(self.target_alt, self.alt + 0.05)
        if self.armed and self.mode == LAND and self.t_land is not None:
            dd = sc.get("land_disarm_s", 6.0)
            if dd is not None and self.c.t - self.t_land >= dd:
                self.armed, self.alt = False, 0.0

    def hb(self):
        return Msg("HEARTBEAT", type=M.MAV_TYPE_QUADROTOR, autopilot=M.MAV_AUTOPILOT_ARDUPILOTMEGA, custom_mode=self.mode,
                   base_mode=(M.MAV_MODE_FLAG_SAFETY_ARMED if self.armed else 0) | M.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED)


class FakeMav:
    def __init__(self, master):
        self.m = master

    def __getattr__(self, name):
        def send(*a):
            self.m.rec(name, a)
            v = self.m.v
            if name == "command_long_send":
                cmd = a[2]
                if cmd == M.MAV_CMD_COMPONENT_ARM_DISARM:
                    v.armed = bool(a[4])
                    v.pending.append(Msg("COMMAND_ACK", command=cmd, result=M.MAV_RESULT_ACCEPTED))
                elif cmd == M.MAV_CMD_NAV_TAKEOFF:
                    v.target_alt = a[10]
                    v.pending.append(Msg("COMMAND_ACK", command=cmd, result=M.MAV_RESULT_ACCEPTED))
        return send


class FakeMaster:
    def __init__(self, clock, sc):
        self.c, self.sc, self.log = clock, sc, []
        self.v = Vehicle(clock, sc, self.log)
        self.target_system, self.target_component = 1, 1
        self.sysid_state = {}
        self.mav = FakeMav(self)

    def rec(self, name, args):
        self.log.append((round(self.c.t, 3), name, repr(tuple(round(x, 6) if isinstance(x, float) else x for x in args))))

    def mode_mapping(self):
        return {"STABILIZE": 0, "ALT_HOLD": 2, "GUIDED": 4, "LAND": 9}

    def set_mode_apm(self, name):
        self.rec("set_mode_apm", (name,))
        new = self.mode_mapping()[name]
        if new == LAND and self.v.mode != LAND:
            self.v.t_land = self.c.t
        self.v.mode = new

    def _post(self, msg):
        st = self.sysid_state.setdefault(msg.get_srcSystem(), types.SimpleNamespace(messages={}))
        st.messages[msg.get_type()] = msg
        return msg

    def recv_match(self, type=None, blocking=True, timeout=None):
        want = [type] if isinstance(type, str) else list(type or [])
        self.c.t += 0.02
        self.v.step()
        t_sim = self.c.t - self.v.t_boot
        if self.v.pending and "COMMAND_ACK" in want:
            return self._post(self.v.pending.pop(0))
        if "HEARTBEAT" in want:
            if self.sc.get("gcs_hb_every") and int(self.c.t * 50) % self.sc["gcs_hb_every"] == 0:
                return self._post(Msg("HEARTBEAT", src=255, type=M.MAV_TYPE_GCS, autopilot=M.MAV_AUTOPILOT_INVALID,
                                      custom_mode=0, base_mode=0))
            return self._post(self.v.hb())
        if "LOCAL_POSITION_NED" in want:
            out = self.sc.get("pos_outage_at")
            if out is not None and t_sim >= out:
                self.c.t += (timeout or 0.5)
                self._post(self.v.hb())        # heartbeats keep flowing (consumed passively)
                return None
            return self._post(Msg("LOCAL_POSITION_NED", time_boot_ms=int(t_sim * 1000), x=0.0, y=0.0, z=-self.v.alt))
        if "SYSTEM_TIME" in want:
            return self._post(Msg("SYSTEM_TIME", time_boot_ms=int(t_sim * 1000)))
        if "ATTITUDE" in want:
            return self._post(Msg("ATTITUDE", yaw=0.0))
        self.c.t += (timeout or 0.0)
        return None


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(path, name, sc):
    for k in ("WATCH_HEARTBEAT", "GROUND_TEST", "LAPS", "HPROFILE", "OUTBACK", "SIDESTEP", "FGO_NODE_CHECK_DIR",
              "H_PREARM", "EXPECT_OVERRIDE"):
        os.environ.pop(k, None)
    for k, v in sc.get("env", {}).items():
        os.environ[k] = v
    mod = load(path, name)
    clock = Clock()
    master = FakeMaster(clock, sc)
    mod.time = types.SimpleNamespace(time=clock.time, sleep=clock.sleep)
    mod.connect = lambda port, *a, **k: master
    mod.ensure_params = lambda m, port: None
    if sc.get("watch_lost_at") is not None:
        mod.watch_ok = lambda: ((clock.t - master.v.t_boot) < sc["watch_lost_at"], "fake watcher")
    sys_argv = sys.argv
    sys.argv = ["fly_trial.py", "--altitude", "1.5", "--velocity", "0.4", "--duration", str(sc.get("duration", 5.0))]
    out = []
    mod.log = lambda s: out.append(s)
    try:
        rc = mod.main()
    finally:
        sys.argv = sys_argv
        for k in sc.get("env", {}):
            os.environ.pop(k, None)
    return rc, master.log, out


SCENARIOS = {
    # --- default behaviour: no pilot takeover; NEW must equal OLD exactly ---
    "normal_trial": dict(kind="identical"),
    "normal_trial_gcs_heartbeats": dict(kind="identical", gcs_hb_every=7),
    "watcher_lost_in_guided": dict(kind="identical", env={"WATCH_HEARTBEAT": "/nonexistent"}, watch_lost_at=20.0,
                                   duration=30.0),
    "trialfailure_in_guided_pos_outage": dict(kind="identical", pos_outage_at=18.0, duration=30.0),
    "ground_test": dict(kind="identical", env={"GROUND_TEST": "5"}),
    "land_slow_disarm_within_cap": dict(kind="identical", land_disarm_s=150.0),
    # --- declared difference: FC already in LAND (no pilot) when the failure path would re-send LAND ---
    "land_never_disarms_no_pilot": dict(kind="declared_no_relands", land_disarm_s=None),
    "watcher_lands_then_watcher_lost": dict(kind="declared_no_relands", env={"WATCH_HEARTBEAT": "/nonexistent"},
                                            watcher_land_at=19.0, watch_lost_at=20.0, duration=30.0, land_disarm_s=None),
    # --- pilot takeover: NEW sends nothing after the takeover; OLD re-sends LAND ---
    "pilot_althold_after_script_land_held_past_cap": dict(kind="takeover", pilot_after_land=(0.33, ALT_HOLD),
                                                          pilot_lands_after=200.0, land_disarm_s=6.0),
    "pilot_stabilize_after_script_land_held_past_cap": dict(kind="takeover", pilot_after_land=(0.33, STABILIZE),
                                                            pilot_lands_after=200.0, land_disarm_s=6.0),
    "pilot_althold_then_watcher_lost_B10b1": dict(kind="takeover", env={"WATCH_HEARTBEAT": "/nonexistent"},
                                                  pilot_at=(18.0, ALT_HOLD), watch_lost_at=20.0, duration=30.0,
                                                  pilot_lands_after=30.0, land_disarm_s=6.0),
    "pilot_althold_after_watcher_land": dict(kind="takeover", env={"WATCH_HEARTBEAT": "/nonexistent"},
                                             watcher_land_at=19.0, pilot_after_land=(0.33, ALT_HOLD),
                                             watch_lost_at=20.0, duration=30.0, pilot_lands_after=200.0,
                                             land_disarm_s=6.0),
}

SCRIPT_CMDS = ("set_mode_apm", "command_long_send", "set_position_target_local_ned_send", "set_attitude_target_send",
               "param_set_send", "rc_channels_override_send")


def cmds(log):
    return [e for e in log if e[1] in SCRIPT_CMDS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-ref", default="HEAD")
    ap.add_argument("--json")
    a = ap.parse_args()
    old_src = subprocess.run(["git", "-C", REPO, "show", f"{a.old_ref}:fly_trial.py"], capture_output=True, text=True,
                             check=True).stdout
    tmp = tempfile.NamedTemporaryFile("w", suffix="_fly_trial_old.py", delete=False)
    tmp.write(old_src); tmp.close()
    new_path = os.path.join(REPO, "fly_trial.py")
    results, ok_all = {}, True
    for name, sc in SCENARIOS.items():
        rc_o, log_o, out_o = run(tmp.name, "ft_old_" + name, sc)
        rc_n, log_n, out_n = run(new_path, "ft_new_" + name, sc)
        co, cn = cmds(log_o), cmds(log_n)
        r = {"kind": sc["kind"], "rc_old": rc_o, "rc_new": rc_n, "n_cmds_old": len(co), "n_cmds_new": len(cn)}
        lands_o = [e for e in co if e[1] == "set_mode_apm" and "LAND" in e[2]]
        lands_n = [e for e in cn if e[1] == "set_mode_apm" and "LAND" in e[2]]
        r["lands_old"], r["lands_new"] = [e[0] for e in lands_o], [e[0] for e in lands_n]
        if sc["kind"] == "identical":
            ok = (co == cn) and rc_o == rc_n
            r["identical"] = co == cn
        elif sc["kind"] == "declared_no_relands":
            # NEW = OLD minus LAND commands sent while the FC was already in LAND; everything else identical
            stripped_o = [e for e in co if not (e[1] == "set_mode_apm" and "LAND" in e[2])]
            stripped_n = [e for e in cn if not (e[1] == "set_mode_apm" and "LAND" in e[2])]
            ok = stripped_o == stripped_n and len(lands_n) <= 1 and len(lands_o) > len(lands_n)
            r["identical_except_lands"] = stripped_o == stripped_n
        else:
            tp = [e[0] for e in log_n if e[1] == "PILOT_MODE" and e[2] in (ALT_HOLD, STABILIZE)]
            t_take = tp[0] if tp else None
            after_n = [e for e in cn if t_take is not None and e[0] >= t_take]
            after_o = [e for e in co if t_take is not None and e[0] >= t_take]
            r["t_takeover"] = t_take
            r["cmds_after_takeover_new"] = after_n
            r["cmds_after_takeover_old"] = after_o
            before_same = [e for e in co if t_take is not None and e[0] < t_take] == \
                          [e for e in cn if t_take is not None and e[0] < t_take]
            r["identical_before_takeover"] = before_same
            r["h10_logged"] = any("H10" in s for s in out_n)
            # the criterion: NO LAND and NO mode change / command after the takeover. Position/velocity setpoints the
            # cruise loop was still sending before it noticed the watcher loss are counted and reported, not failed
            # (an ArduCopter pilot mode ignores them; they are not a mode change).
            modecmd = ("set_mode_apm", "command_long_send")
            r["mode_cmds_after_takeover_new"] = [e for e in after_n if e[1] in modecmd]
            r["mode_cmds_after_takeover_old"] = [e for e in after_o if e[1] in modecmd]
            r["setpoints_after_takeover_new"] = len([e for e in after_n if e[1] not in modecmd])
            ok = (t_take is not None and not r["mode_cmds_after_takeover_new"] and before_same and r["h10_logged"]
                  and len(r["mode_cmds_after_takeover_old"]) > 0)
        r["PASS"] = bool(ok)
        ok_all &= bool(ok)
        results[name] = r
        print(f"{'PASS' if ok else 'FAIL'}  {name:52s} kind={sc['kind']:20s} cmds old/new {len(co)}/{len(cn)}  "
              f"LAND old {r['lands_old']} new {r['lands_new']}"
              + (f"  LAND/mode cmds after takeover old {len(r['mode_cmds_after_takeover_old'])} "
                 f"new {len(r['mode_cmds_after_takeover_new'])} (setpoints new {r['setpoints_after_takeover_new']})"
                 if sc['kind'] == 'takeover' else ""))
    os.unlink(tmp.name)
    if a.json:
        json.dump({"old_ref": a.old_ref, "all_pass": ok_all, "scenarios": results}, open(a.json, "w"), indent=1,
                  default=str)
    print("ALL PASS" if ok_all else "SOME FAILED")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
