#!/usr/bin/env python3
"""
State-gated flight controller for the automated trial harness (run_trial.sh).

Generalises the flight profile validated across Stages A/B/C into a
reusable, parameterised script: arm, climb to a target altitude, cruise
forward at a target velocity for a target *sim-time* duration, stop, land.

Two hard-won constraints from earlier stage work shape every wait in this
script (see CLAUDE.md, Known Issues — RTF is low on this machine, roughly
0.05-0.17):

  1. Never gate on a fixed wall-clock time.sleep() for anything tied to
     simulated flight progress. A first attempt at this (Stage A) used
     wall-clock sleeps for climb/cruise timing and silently produced a
     near-empty 7-12 s flight log, because at RTF~0.1 a sleep(N) only buys
     ~N*RTF seconds of sim time. Every phase below gates on *measured*
     state instead: altitude via LOCAL_POSITION_NED, cruise duration via
     the vehicle's own onboard clock (time_boot_ms, which runs in sim
     time), landing via the disarm flag.
  2. Wall-clock timeouts are used only as generous safety-net caps (to stop
     a genuinely stuck flight from hanging forever), scaled to the
     requested sim-time duration rather than fixed small numbers, since
     the harness must support long trials.

Also self-heals the eeprom persistence gotcha found in Stages A/C: ArduPilot
SITL's eeprom.bin can silently keep a param at an old value despite a
--add-param-file saying otherwise, once that param has ever been
explicitly stored. This script reads back the expected GNSS-denied +
flow + LiDAR baseline params after connecting and, if any mismatch, live
PARAM_SETs them and does one soft reboot (MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN)
before proceeding — rather than silently flying with a wrong config.

Exit code 0 on a successful trial; nonzero (with a clear message on
stderr) on any failure, so run_trial.sh's error trap can detect it and
clean up.

Usage:
    python3 fly_trial.py --port 14550 --altitude 2.0 --velocity 0.4 --duration 30
"""

import argparse
import json
import math
import subprocess
import os
import sys
import time

from pymavlink import mavutil

# Expected GNSS-denied + flow + LiDAR baseline (see lidar_rangefinder.parm,
# flow_ekf.parm, gnss_denied.parm). Verified after connecting; self-healed
# if the eeprom persistence gotcha has left any of these stale.
EXPECTED_PARAMS = {
    # Consolidated re-run (2026-09-29, consolidated_rerun.parm): correction (i) and the
    # replayable-log standing rule; AHRS_EKF_TYPE=10 keeps flights on simulator truth.
    'FLOW_POS_Z': 0.25,
    'AHRS_EKF_TYPE': 10,
    'LOG_REPLAY': 1,
    'LOG_DISARMED': 1,
    # Roll rate gains scaled to this airframe (roll_rate_gains.parm, 2026-09-29): removes the
    # 17.5 Hz roll limit cycle. Pitch/yaw stay at firmware defaults.
    'ATC_RAT_RLL_P': 0.06003,
    'ATC_RAT_RLL_I': 0.06003,
    'ATC_RAT_RLL_D': 0.0016,
    'RNGFND1_TYPE': 10,
    'FLOW_TYPE': 5,
    'EK3_SRC1_VELXY': 5,
    'EK3_FLOW_USE': 1,
    'EK3_SRC1_POSXY': 0,
    'EK3_SRC1_POSZ': 2,
    'EK3_SRC1_VELZ': 0,
    'SIM_GPS1_ENABLE': 0,
    # experiment O guards (2026-10-08): scripting and the source options must stay off in every other flight
    'SCR_ENABLE': 0,
    'EK3_SRC_OPTIONS': 0,
    # GPS1_TYPE=0 (None) is required for arming, not just for GNSS-denial:
    # gps_checks() rejects a configured-but-unfixed GPS with "GPS 1: Bad
    # fix" regardless of the EK3_SRC selections. It carries
    # AP_PARAM_FLAG_ENABLE, so it is squarely subject to the eeprom
    # persistence gotcha this dict exists to self-heal. See gnss_denied.parm.
    'GPS1_TYPE': 0,
    # SITL noise/drift model, pinned for reproducibility (see sim_noise.parm,
    # METHODOLOGY.md). Deterministic gyro drift retained; all random sensor
    # noise zeroed. Non-integer expected values (SIM_DRIFT_SPEED=0.05) are why
    # the check below is float-tolerant, not round()-based.
    'SIM_DRIFT_SPEED': 0.05,
    'SIM_DRIFT_TIME': 5,
    'SIM_ACC1_RND': 0,
    'SIM_ACC2_RND': 0,
    'SIM_GYR1_RND': 0,
    'SIM_GYR2_RND': 0,
    'SIM_BARO_RND': 0,
    'SIM_SONAR_RND': 0,
    'SIM_FLOW_RND': 0,
    # No-yaw config (gnss_denied_nomag.parm) — the UKF/FGO sensor suite has no
    # yaw source, so EKF3 must not fuse the compass either. EK3_SRC1_YAW=0 and
    # COMPASS_USE*=0 carry AP_PARAM_FLAG_ENABLE / are eeprom-persistent, so they
    # go through this self-heal. COMPASS_ENABLE=1 stays (arming gate only).
    'EK3_SRC1_YAW': 0,
    'COMPASS_ENABLE': 1,
    'COMPASS_USE': 0,
    'COMPASS_USE2': 0,
    'COMPASS_USE3': 0,
    'EK3_GSF_RUN_MASK': 3,
    'EK3_GSF_USE_MASK': 3,
}

# Minimum RTF to assume when sizing wall-clock safety-net timeouts. This
# machine has measured as low as ~0.05; padding further below that keeps
# the caps from being the thing that fails a trial on a slow run.
MIN_ASSUMED_RTF = 0.03

TYPE_MASK_VELOCITY_ONLY = 0b0000_1111_1100_0111


class TrialFailure(Exception):
    pass


# Optional EXPECT_OVERRIDE="NAME=value,NAME=value" replaces entries of EXPECTED_PARAMS for a
# one-off test (e.g. the closed-loop smoke test's AHRS_EKF_TYPE=3). Unset for dataset flights.
for _kv in filter(None, os.environ.get("EXPECT_OVERRIDE", "").split(",")):
    _k, _v = _kv.split("=")
    EXPECTED_PARAMS[_k.strip()] = float(_v)


def log(msg: str) -> None:
    print(f"[fly_trial] {msg}", flush=True)


def connect(port: int, wait_heartbeat_timeout_s: float = 240.0):
    # Timeout matches run_trial.sh's "MAVProxy relaying" wait_for cap, not a
    # guess: the Gazebo<->SITL JSON lockstep channel can stall for ~90-110s
    # real time after a MAVLink client first attaches to SERIAL0 (confirmed
    # via gdb - SITL blocks in SITL::JSON::recv_fdm() waiting on Gazebo's next
    # physics packet - and via ArduCopter's own "No JSON sensor message
    # received, resending servos" retry log), independent of world choice or
    # load time. run_trial.sh's own wait_for already waits out one such stall
    # before this script even runs, but the relay can still be settling when
    # this fresh connection is made, so this wait needs the same generous
    # margin. See CLAUDE.md, Known Issues, and run_trial.sh's own comment.
    log(f"Connecting to SITL on udp:127.0.0.1:{port} ...")
    master = mavutil.mavlink_connection(f'udp:127.0.0.1:{port}', source_system=255)
    hb = master.wait_heartbeat(timeout=wait_heartbeat_timeout_s)
    if hb is None:
        raise TrialFailure(f"No heartbeat within {wait_heartbeat_timeout_s:.0f}s")
    log(f"Heartbeat received from system {master.target_system} component {master.target_component}")
    return master


def read_param(master, name: str, timeout_s: float = 5.0, retries: int = 5):
    # Retries, not a single shot: the link can still be settling for a few
    # seconds right after the heartbeat first arrives (same Gazebo<->SITL
    # JSON-lockstep stall connect() waits out - see its comment), so a lone
    # PARAM_REQUEST_READ/PARAM_VALUE round trip can legitimately get lost
    # even once heartbeats are flowing.
    for attempt in range(retries):
        master.mav.param_request_read_send(
            master.target_system, master.target_component, name.encode(), -1)
        msg = master.recv_match(type='PARAM_VALUE', blocking=True, timeout=timeout_s)
        while msg is not None and msg.param_id.rstrip('\x00') != name:
            msg = master.recv_match(type='PARAM_VALUE', blocking=True, timeout=timeout_s)
        if msg is not None:
            return msg.param_value
        log(f"No response reading {name} (attempt {attempt + 1}/{retries}), retrying...")
    return None


def set_param(master, name: str, value: float) -> None:
    master.mav.param_set_send(
        master.target_system, master.target_component,
        name.encode(), float(value), mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
    master.recv_match(type='PARAM_VALUE', blocking=True, timeout=5.0)


def ensure_params(master, port: int):
    """Self-heal the eeprom persistence gotcha - see module docstring.
    Returns a new connection if a reboot was needed, else None."""
    log("Verifying baseline params...")
    mismatched = {}
    for name, expected in EXPECTED_PARAMS.items():
        actual = read_param(master, name)
        if actual is None:
            raise TrialFailure(f"No response reading {name}")
        if abs(actual - expected) > 1e-4:
            mismatched[name] = expected

    if not mismatched:
        log("All baseline params correct.")
        return

    log(f"Mismatched params (eeprom persistence gotcha): {mismatched} - fixing and rebooting...")
    for name, value in mismatched.items():
        set_param(master, name, value)

    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN, 0,
        1, 0, 0, 0, 0, 0, 0)
    time.sleep(3)  # one-off: SITL process needs a moment before it will accept a new link

    master = connect(port)
    still_wrong = {}
    for name, expected in mismatched.items():
        actual = read_param(master, name)
        if actual is None or abs(actual - expected) > 1e-4:
            still_wrong[name] = (actual, expected)
    if still_wrong:
        raise TrialFailure(f"Params still wrong after fix-and-reboot: {still_wrong}")
    log("Params corrected and verified after reboot.")
    return master


def wait_ready_to_arm(master, wall_clock_cap_s: float = None) -> None:
    """Retry arming until accepted. Bounded by a wall-clock cap since
    transient prearm failures (e.g. "Gyros inconsistent", gyro bias not yet
    learned) resolve over sim time, not wall-clock time, and we have no
    direct 'ready' flag to poll instead - only the arm attempt's own
    result. A first attempt at this capped at 90s wall-clock and a fresh
    SITL boot didn't clear "Gyros inconsistent" within that window even
    once; sized generously (assumes up to ~15s of *sim* time may genuinely
    be needed) rather than guessed from wall-clock alone."""
    if wall_clock_cap_s is None:
        wall_clock_cap_s = 15.0 / MIN_ASSUMED_RTF + 60.0
    log("Waiting for vehicle to become armable...")
    master.set_mode_apm('GUIDED')

    t0 = time.time()
    last_reason = None
    while time.time() - t0 < wall_clock_cap_s:
        # 2026-10-08 fix: after ensure_params' fix-and-reboot, the GUIDED request above can land while SITL is still
        # rebooting ("System not initialised"); the reboot then completes in STABILIZE and the take-off is ignored
        # (tag_check1b). Re-assert GUIDED before every arm attempt if the heartbeat shows another mode (a no-op when
        # already GUIDED, so a flight that never rebooted sends exactly the same arm commands as before).
        hb = master.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
        if hb is not None and (hb.get_srcSystem() != master.target_system or hb.type == mavutil.mavlink.MAV_TYPE_GCS):
            hb = None                                    # only the vehicle's own heartbeat counts
        if hb is not None and hb.custom_mode != (master.mode_mapping() or {}).get('GUIDED', 4):
            log(f"Mode is {hb.custom_mode}, not GUIDED: re-asserting GUIDED before arming")
            master.set_mode_apm('GUIDED')
            continue
        master.mav.command_long_send(
            master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0,
            1, 0, 0, 0, 0, 0, 0)
        deadline = time.time() + 3.0
        while time.time() < deadline:
            msg = master.recv_match(type=['COMMAND_ACK', 'STATUSTEXT'], blocking=True, timeout=1.0)
            if msg is None:
                continue
            if msg.get_type() == 'STATUSTEXT':
                last_reason = msg.text
            elif msg.get_type() == 'COMMAND_ACK' and msg.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
                if msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                    log("Armed.")
                    return
                last_reason = last_reason or f"MAV_RESULT={msg.result}"
                break
        time.sleep(1.0)

    raise TrialFailure(f"Failed to arm within {wall_clock_cap_s:.0f}s (last reason: {last_reason})")


def wait_altitude(master, target_m: float, tolerance_frac: float = 0.9,
                   wall_clock_cap_s: float = None) -> None:
    if wall_clock_cap_s is None:
        wall_clock_cap_s = max(120.0, target_m / MIN_ASSUMED_RTF)
    threshold = target_m * tolerance_frac
    log(f"Commanding takeoff to {target_m:.2f} m, waiting for >= {threshold:.2f} m "
        f"(measured, wall-clock cap {wall_clock_cap_s:.0f}s)...")

    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0,
        0, 0, 0, 0, 0, 0, target_m)
    master.recv_match(type='COMMAND_ACK', blocking=True, timeout=5.0)

    t0 = time.time()
    last_alt = 0.0
    while time.time() - t0 < wall_clock_cap_s:
        msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=2.0)
        if msg is None:
            continue
        last_alt = -msg.z
        if last_alt >= threshold:
            log(f"Reached {last_alt:.2f} m after {time.time()-t0:.1f}s wall-clock.")
            return

    raise TrialFailure(f"Did not reach {threshold:.2f} m within {wall_clock_cap_s:.0f}s "
                        f"(last measured altitude: {last_alt:.2f} m)")


def send_velocity(master, vx: float, vy: float, vz: float) -> None:
    master.mav.set_position_target_local_ned_send(
        0, master.target_system, master.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, TYPE_MASK_VELOCITY_ONLY,
        0, 0, 0, vx, vy, vz, 0, 0, 0, 0, 0)


# ---- fail-closed safety watcher (ruling 2026-10-08) ----
# With WATCH_HEARTBEAT=<path> (set by closed_loop_run.sh for closed-loop flights), no arming without a fresh watcher
# heartbeat with box=1 and bridge=1; in flight, a stale (> WATCH_STALE_S) or withdrawn heartbeat makes the flight land.
WATCH_STALE_S = 3.0
_watch = {"active": False, "last_check": 0.0}


class WatcherLost(Exception):
    """Raised when the safety watcher's heartbeat is lost in flight. Deliberately NOT a TrialFailure: the flight loops
    catch TrialFailure around sim_time_now_s, which swallowed the first version of this check (H_wtest_kill)."""


def watch_ok() -> tuple:
    p = os.environ.get("WATCH_HEARTBEAT")
    if not p:
        return True, "no watcher required"
    try:
        f = open(p).read().split()
        age = time.time() - float(f[0]); flags = dict(kv.split("=") for kv in f[1:])
    except (OSError, ValueError, IndexError):
        return False, "no watcher heartbeat"
    if age > WATCH_STALE_S:
        return False, f"watcher heartbeat stale ({age:.1f} s)"
    if flags.get("box") != "1" or flags.get("bridge") != "1":
        return False, f"watcher not confirming (box={flags.get('box')} bridge={flags.get('bridge')})"
    return True, f"watcher ok (age {age:.1f} s)"


def require_watcher_before_arming(cap_s: float = 60.0) -> None:
    if not os.environ.get("WATCH_HEARTBEAT"):
        return
    t0 = time.time(); ok, why = watch_ok()
    while not ok and time.time() - t0 < cap_s:
        time.sleep(1.0); ok, why = watch_ok()
    if not ok:
        raise TrialFailure(f"REFUSING TO ARM: {why} (fail-closed safety watcher, WATCH_HEARTBEAT)")
    log(f"Safety watcher confirmed before arming: {why}"); _watch["active"] = True


def _sitl_serial1_ports() -> set:
    """Local UDP ports of the running arducopter's socket(s) to 127.0.0.1:14557 (SERIAL1, the tag link); if `ss` shows no
    peer for them, every arducopter UDP port (membership is then the check)."""
    r = subprocess.run(["ss", "-Hunap"], capture_output=True, text=True)
    peer, anyp = set(), set()
    for ln in r.stdout.splitlines():
        if '"arducopter"' not in ln:
            continue
        f = ln.split()
        loc, rem = f[3], f[4]
        port = int(loc.rsplit(":", 1)[1])
        anyp.add(port)
        if rem.endswith(":14557"):
            peer.add(port)
    return peer or anyp


def _live_bin_since_boot():
    """Snapshot of the running SITL's dataflash log (the newest .BIN; a new file starts at every boot, so this is since
    the latest boot): MSG texts, the VISP count and the last VISP / last record TimeUS."""
    d = os.path.join(os.environ.get("ARDUPILOT_TREE", os.path.expanduser("~/ardupilot")), "ArduCopter", "logs")
    bins = sorted((os.path.join(d, f) for f in os.listdir(d) if f.endswith(".BIN")), key=os.path.getmtime)
    if not bins:
        return None
    from pymavlink import DFReader
    try:
        lg = DFReader.DFReader_binary(bins[-1], zero_time_base=True)
    except Exception:
        return None                                       # a partially written last record: retry at the next poll
    msgs, n_visp, t_visp, t_last, xfgi_v = [], 0, None, 0, None
    while True:
        try:
            m = lg.recv_match(type=["MSG", "VISP", "XFGI"])
        except Exception:
            break                                         # a partially written last record
        if m is None:
            break
        t = getattr(m, "TimeUS", 0); t_last = max(t_last, t)
        if m.get_type() == "MSG":
            msgs.append(m.Message)
        elif m.get_type() == "XFGI":
            xfgi_v = int(m.V)
        else:
            n_visp += 1; t_visp = t
    return {"file": bins[-1], "msgs": msgs, "n_visp": n_visp, "t_visp": t_visp, "t_last": t_last, "xfgi_v": xfgi_v}


ANCHOR_TEXT = {"EKF3": "is using external nav data", "UKF": "UKF tag re-anchor", "FGO": "FGO re-anchor"}


def require_fgo_node_current(cap_s: float = 120.0) -> None:
    """FC-reboot check (user ruling 2026-10-09). The C++ FGO node's clock map is built against ONE FC boot; a SITL
    reboot after the node started (e.g. ensure_params' soft reboot) would step the FC clock back under it. run_trial
    records the FC boot the node started against (the newest dataflash log then: one per boot). If the FC has rebooted
    since, stop the node (SIGINT, it writes its stats), start it again (fgo_node_restart.sh, same parameters) and wait
    for its 'FIRST STATE SENT' (clock map settled) before arming. Mid-flight the node itself latches its output INVALID
    on a clock step back (live_adapter clock_broken), so the FC's landing trigger applies."""
    d = os.environ.get("FGO_NODE_CHECK_DIR", "")
    if not d:
        return
    logs = os.environ["FGO_NODE_AP_LOGS"]
    bins = sorted((f for f in os.listdir(logs) if f.endswith(".BIN")), key=lambda f: os.path.getmtime(os.path.join(logs, f)))
    started = open(os.path.join(d, "fgo_node_boot.txt")).read().strip()
    now = bins[-1] if bins else ""
    if now == started:
        log(f"FGO node check ok: no FC reboot since the node started (boot log {now})")
        return
    log(f"FGO node check: FC REBOOTED since the node started (boot log {started} -> {now}); restarting the node")
    pid = int(open(os.path.join(d, "fgo_node.pid")).read().strip())
    try:
        os.killpg(pid, 2)
    except ProcessLookupError:
        pass
    t0 = time.time()
    while time.time() - t0 < 30:
        try:
            os.kill(pid, 0); time.sleep(0.5)
        except ProcessLookupError:
            break
    else:
        raise TrialFailure(f"REFUSING TO ARM: the old FGO node (pid {pid}) did not stop")
    subprocess.run(["bash", os.path.join(d, "fgo_node_restart.sh")], check=True)
    open(os.path.join(d, "fgo_node_boot.txt"), "w").write(now + "\n")
    rl = os.path.join(d, "fgo_node_restart.log"); t0 = time.time()
    while time.time() - t0 < cap_s:
        if os.path.exists(rl) and "FIRST STATE SENT" in open(rl, errors="replace").read():
            log(f"FGO node restarted (pid {open(os.path.join(d, 'fgo_node.pid')).read().strip()}); clock map settled after "
                f"{time.time() - t0:.1f} s wall")
            return
        time.sleep(1.0)
    raise TrialFailure("REFUSING TO ARM: the restarted FGO node did not settle its clock map in time")


def require_anchor_before_arming(cap_s: float = 180.0) -> None:
    """Experiment H ruling 2026-10-08 (item 2): no arming until every listed backend has anchored to the tag frame (its own
    anchor text in the running SITL's log since the latest boot) AND the FC is receiving fixes (VISP rows growing, the
    last one recent), AND (item 4) the tag bridge's target port is SITL's current SERIAL1 port. H_PREARM = the backends
    on the FC that must anchor, e.g. "EKF3" or "EKF3,UKF" or "EKF3,FGO"; unset = no gate. Offline estimators (replays)
    anchor at their first fix, which this gate places before arming."""
    req = [x for x in os.environ.get("H_PREARM", "").split(",") if x]
    if not req:
        return
    status = os.environ.get("TAG_BRIDGE_STATUS", "")
    t0 = time.time(); prev_n = None; why = "not checked"
    while time.time() - t0 < cap_s:
        problems = []
        try:
            ts_, port, n_sent = open(status).read().split()
            age = time.time() - float(ts_); port = int(port)
            live = _sitl_serial1_ports()
            if age > 2.0:
                problems.append(f"bridge status stale ({age:.1f} s)")
            if port not in live:
                problems.append(f"bridge target port {port} is not SITL's SERIAL1 port {sorted(live)}")
        except (OSError, ValueError) as e:
            problems.append(f"no bridge status ({e})")
        snap = _live_bin_since_boot()
        if snap is None:
            problems.append("no live dataflash log")
        else:
            missing = [b for b in req if b != "FGO" and not any(ANCHOR_TEXT[b] in m for m in snap["msgs"])]
            if "FGO" in req:
                # the C++ node anchors before its FIRST state when the tag is in view pre-arm, so the FC sees no frame
                # change (no "FGO re-anchor" text; H_safety_fgo_a attempt 1). Anchored = the current node logged
                # "ANCHORED" AND the FC's latest FGO state (XFGI) is valid.
                d = os.environ.get("FGO_NODE_CHECK_DIR", "")
                rl = os.path.join(d, "fgo_node_restart.log"); nl = rl if os.path.exists(rl) else os.path.join(d, "fgo_node.log")
                node_anch = bool(d) and os.path.exists(nl) and "ANCHORED" in open(nl, errors="replace").read()
                if not (node_anch and snap["xfgi_v"] == 1):
                    missing.append(f"FGO(node anchored {node_anch}, FC state valid {snap['xfgi_v']})")
            if missing:
                problems.append(f"not anchored: {','.join(missing)}")
            if prev_n is None or snap["n_visp"] <= prev_n:
                problems.append(f"VISP not growing ({snap['n_visp']})")
            elif snap["t_visp"] is None or snap["t_last"] - snap["t_visp"] > 1_000_000:
                problems.append("last VISP older than 1 s")
            prev_n = snap["n_visp"]
        if not problems:
            log(f"PREARM ANCHOR ok: {','.join(req)} anchored; VISP {snap['n_visp']} and growing; bridge port {port} = SITL "
                f"SERIAL1; log {os.path.basename(snap['file'])}")
            return
        why = "; ".join(problems)
        time.sleep(2.0)
    raise TrialFailure(f"REFUSING TO ARM: {why} (H pre-arm anchoring gate, H_PREARM)")


def check_watcher_in_flight() -> None:
    if not _watch["active"] or time.time() - _watch["last_check"] < 1.0:
        return
    _watch["last_check"] = time.time(); ok, why = watch_ok()
    if not ok:
        _watch["active"] = False         # the landing that follows must not re-trigger this
        raise WatcherLost(f"safety watcher lost in flight: {why}; landing")


def sim_time_now_s(master, timeout_s: float = 3.0) -> float:
    """Vehicle's own onboard clock (sim time, AP_HAL::millis()).

    Prefers LOCAL_POSITION_NED exactly as before (so nominal flights read the same values), but that message
    is an ESTIMATOR output: send_local_position() (GCS_Common.cpp:3048-3050) sends nothing while the active
    AHRS backend has no position, so an estimator invalidation used to hang this clock and fail the trial
    before landing/disarm (D24, fgo_groundtest_half G5). SYSTEM_TIME (STREAM_EXTRA3, GCS_Common.cpp:2148) carries
    the same AP_HAL::millis() independently of any estimator; it is returned only when no LOCAL_POSITION_NED
    arrives before two SYSTEM_TIMEs (LOCAL_POSITION_NED streams ~6x faster) or before the timeout."""
    check_watcher_in_flight()
    t0 = time.time()
    sys_ms, n_sys = None, 0
    while time.time() - t0 < timeout_s:
        msg = master.recv_match(type=['LOCAL_POSITION_NED', 'SYSTEM_TIME'], blocking=True,
                                timeout=max(0.01, timeout_s - (time.time() - t0)))
        if msg is None:
            break
        if msg.get_type() == 'LOCAL_POSITION_NED':
            return msg.time_boot_ms / 1000.0
        sys_ms, n_sys = msg.time_boot_ms, n_sys + 1
        if n_sys >= 2:
            return sys_ms / 1000.0
    if sys_ms is not None:
        return sys_ms / 1000.0
    raise TrialFailure("No message received while reading sim-time clock")


def cruise(master, velocity: float, duration_s: float, wall_clock_cap_s: float = None) -> None:
    """Fly forward at `velocity` m/s for `duration_s` SIM seconds, gated on
    the vehicle's own onboard clock, not wall-clock time."""
    if wall_clock_cap_s is None:
        wall_clock_cap_s = duration_s / MIN_ASSUMED_RTF + 120.0
    log(f"Cruising forward at {velocity:.2f} m/s for {duration_s:.1f} s of SIM time "
        f"(wall-clock cap {wall_clock_cap_s:.0f}s)...")

    # Optional SIDESTEP="t_start,v_east,T" (check flights only; unset for datasets = no
    # change): from t_start s of cruise, command v_east m/s East for T s, then -v_east for
    # T s back to the centreline, forward speed unchanged. A deliberate lateral excitation
    # (METHODOLOGY "Excitation checks"), added 2026-09-29 for the lateral-flow-sign check.
    step = [float(v) for v in os.environ.get("SIDESTEP", "").split(",")] if os.environ.get("SIDESTEP") else None
    if step:
        log(f"SIDESTEP: {step[1]:+.2f} m/s East for {step[2]:.1f} s from cruise t={step[0]:.1f} s, then back")
    start_sim_t = sim_time_now_s(master)
    t0 = time.time()
    last_sim_elapsed = 0.0
    while time.time() - t0 < wall_clock_cap_s:
        v_east = 0.0
        if step:
            dt_s = last_sim_elapsed - step[0]
            v_east = step[1] if 0.0 <= dt_s < step[2] else (-step[1] if step[2] <= dt_s < 2 * step[2] else 0.0)
        send_velocity(master, velocity, v_east, 0.0)
        try:
            now_sim_t = sim_time_now_s(master, timeout_s=0.5)
        except TrialFailure:
            now_sim_t = None
        if now_sim_t is not None:
            last_sim_elapsed = now_sim_t - start_sim_t
            if last_sim_elapsed >= duration_s:
                log(f"Cruise complete - {last_sim_elapsed:.1f}s sim time elapsed "
                    f"({time.time()-t0:.1f}s wall-clock).")
                return
        time.sleep(0.1)

    raise TrialFailure(f"Cruise did not complete within {wall_clock_cap_s:.0f}s wall-clock "
                        f"(last measured sim-time elapsed: {last_sim_elapsed:.1f}s "
                        f"of {duration_s:.1f}s target)")


TYPE_MASK_POS_VEL_YAW = 0b0000_1001_1100_0000   # use position + velocity (feed-forward) + yaw; ignore accel, yaw rate


def laps(master, n_laps: int, side_m: float, speed: float, alt_m: float) -> None:
    """Experiments T/L (2026-10-08): square laps N -> E -> S -> W from the lap-start point, at constant heading (yaw
    held at the lap-start yaw). A MOVING POSITION SETPOINT with velocity feed-forward (SET_POSITION_TARGET_LOCAL_NED,
    position + velocity + yaw) travels the square at `speed`, timed on the estimator-independent clock (sim_time_now_s,
    D24), so the flown path matches the square (the timed velocity-only version, tag_check1c, overshot the first corner
    by ~1 m and shifted the square off the tag line). Position here is simulator truth (AHRS_EKF_TYPE 10), so the path
    is independent of the estimator under test. Logs 'LAP <k> LEG <j> START t_sim=<s>' when the setpoint enters each
    leg (the pre-registered lap evaluation window) and 'LAPS END t_sim'."""
    dirs = [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)]       # (north, east) unit vectors
    leg_s = side_m / speed; total_s = 4 * n_laps * leg_s
    msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=5.0)
    att = master.recv_match(type='ATTITUDE', blocking=True, timeout=5.0)
    if msg is None or att is None:
        raise TrialFailure("no LOCAL_POSITION_NED/ATTITUDE at lap start")
    n0, e0, yaw0 = msg.x, msg.y, att.yaw
    corners = [(n0, e0)]
    for dn, de in dirs[:3]:
        corners.append((corners[-1][0] + dn * side_m, corners[-1][1] + de * side_m))
    log(f"LAPS: {n_laps} laps of a {side_m:.2f} m square at {speed:.2f} m/s ({leg_s:.1f} s per leg), "
        f"start N {n0:.2f} E {e0:.2f}, yaw {math.degrees(yaw0):.1f} deg, alt {alt_m:.2f} m (position setpoint)")
    t0 = sim_time_now_s(master); tw = time.time(); cap = total_s / MIN_ASSUMED_RTF + 120.0; cur = None
    while time.time() - tw < cap:
        try:
            now = sim_time_now_s(master, timeout_s=0.5)
        except TrialFailure:
            now = None
        if now is not None:
            el = now - t0
            if el >= total_s:
                break
            idx = int(el // leg_s); k, j = divmod(idx, 4)
            if (k, j) != cur:
                cur = (k, j); log(f"LAP {k} LEG {j} START t_sim={t0 + idx * leg_s:.3f}")
            u = dirs[j]; s = el - idx * leg_s
            pn, pe = corners[j][0] + u[0] * speed * s, corners[j][1] + u[1] * speed * s
            master.mav.set_position_target_local_ned_send(
                0, master.target_system, master.target_component, mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                TYPE_MASK_POS_VEL_YAW, pn, pe, -alt_m, u[0] * speed, u[1] * speed, 0, 0, 0, 0, yaw0, 0)
        time.sleep(0.05)
    else:
        raise TrialFailure(f"laps did not complete within {cap:.0f} s wall-clock")
    master.mav.set_position_target_local_ned_send(          # hold the closing corner (the stop() velocity hold follows)
        0, master.target_system, master.target_component, mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        TYPE_MASK_POS_VEL_YAW, n0, e0, -alt_m, 0, 0, 0, 0, 0, 0, yaw0, 0)
    log(f"LAPS END t_sim={t0 + total_s:.3f}")


def set_gnss(master, on: bool) -> None:
    """Experiment O: the simulated GPS on/off, live (SIM_GPS1_ENABLE; SITL then reports NO_FIX). Every later trial's
    ensure_params restores the baseline (SIM_GPS1_ENABLE 0, GPS1_TYPE 0, SCR_ENABLE 0, EK3_SRC_OPTIONS 0)."""
    set_param(master, 'SIM_GPS1_ENABLE', 1 if on else 0)
    log(f"GNSS {'ON' if on else 'OFF'} t_sim={sim_time_now_s(master):.3f}")


def outback(master, align_m: float, align_speed: float, out_m: float, speed: float, gate_n: float, alt_m: float,
            hold_s: float = 3.0) -> None:
    """Experiment O (2026-10-08). Along +North from the start point at constant yaw, with a moving position setpoint
    (position + velocity feed-forward + yaw, as laps()) on simulator truth (AHRS_EKF_TYPE 10):
      1. ALIGN: align_m forward at align_speed (outdoors, GNSS on). EKF3 without a compass aligns yaw only from GPS
         course or its GSF, which need > ~1.16 m/s (AP_NavEKF3_MagFusion.cpp:150-190), and uses GPS only after that;
      2. OUT: out_m forward at `speed` (through the entrance into the building);
      3. hold hold_s; 4. BACK: out_m in REVERSE at `speed` (same heading) to the end of the align run.
    GNSS is switched OFF when the measured North position first exceeds gate_n (the entrance) and ON again when it
    first falls below gate_n on the way back. Markers: 'OUTBACK ALIGN START', 'OUTBACK OUT START', 'OUTBACK BACK
    START', 'OUTBACK END', 'GNSS OFF/ON t_sim'."""
    msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=5.0)
    att = master.recv_match(type='ATTITUDE', blocking=True, timeout=5.0)
    if msg is None or att is None:
        raise TrialFailure("no LOCAL_POSITION_NED/ATTITUDE at out-and-back start")
    n0, e0, yaw0 = msg.x, msg.y, att.yaw
    ta, to = align_m / align_speed, out_m / speed
    T1, T2, T3 = ta, ta + to, ta + to + hold_s; total_s = T3 + to
    n1, n2 = n0 + align_m, n0 + align_m + out_m
    log(f"OUTBACK: align {align_m:.1f} m at {align_speed:.2f} m/s, then {out_m:.1f} m out and back at {speed:.2f} m/s; "
        f"start N {n0:.2f} E {e0:.2f}, yaw {math.degrees(yaw0):.1f} deg, GNSS gate N = {gate_n:.1f} m, alt {alt_m:.2f} m")
    t0 = sim_time_now_s(master); log(f"OUTBACK ALIGN START t_sim={t0:.3f}")
    tw = time.time(); cap = total_s / MIN_ASSUMED_RTF + 120.0; phase = 0; gnss_on = True
    while time.time() - tw < cap:
        m = master.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=0.5)
        if m is None:
            continue
        el = m.time_boot_ms / 1000.0 - t0
        if el >= total_s:
            break
        if el < T1:
            pn, vn = n0 + align_speed * el, align_speed
        elif el < T2:
            if phase < 1: phase = 1; log(f"OUTBACK OUT START t_sim={t0 + T1:.3f}")
            pn, vn = n1 + speed * (el - T1), speed
        elif el < T3:
            pn, vn = n2, 0.0
        else:
            if phase < 2: phase = 2; log(f"OUTBACK BACK START t_sim={t0 + T3:.3f}")
            pn, vn = n2 - speed * (el - T3), -speed
        master.mav.set_position_target_local_ned_send(
            0, master.target_system, master.target_component, mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            TYPE_MASK_POS_VEL_YAW, pn, e0, -alt_m, vn, 0, 0, 0, 0, 0, yaw0, 0)
        if gnss_on and m.x > gate_n:
            set_gnss(master, False); gnss_on = False
        elif not gnss_on and phase == 2 and m.x < gate_n:
            set_gnss(master, True); gnss_on = True
    else:
        raise TrialFailure(f"out-and-back did not complete within {cap:.0f} s wall-clock")
    master.mav.set_position_target_local_ned_send(
        0, master.target_system, master.target_component, mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        TYPE_MASK_POS_VEL_YAW, n1, e0, -alt_m, 0, 0, 0, 0, 0, 0, yaw0, 0)
    if not gnss_on:
        raise TrialFailure("GNSS never switched back on (the vehicle did not return past the gate)")
    log(f"OUTBACK END t_sim={t0 + total_s:.3f}")


def occluder(world: str, on: bool) -> None:
    """Experiment H: move the world's visual-only `occluder` panel in front of the wall tag (on) or back below the
    floor (off), via the Gazebo set_pose service. Logged with the sim time by the caller."""
    pos = "x: 0, y: 4.7, z: 1.5" if on else "x: 0, y: 4.7, z: -5"
    r = subprocess.run(["gz", "service", "-s", f"/world/{world}/set_pose", "--reqtype", "gz.msgs.Pose",
                        "--reptype", "gz.msgs.Boolean", "--timeout", "3000",
                        "--req", f'name: "occluder", position: {{{pos}}}'], capture_output=True, text=True, timeout=10)
    if "data: true" not in r.stdout:
        raise TrialFailure(f"occluder set_pose failed: {r.stdout.strip()} {r.stderr.strip()}")


def hprofile(master, path: str, alt_m: float, world: str) -> None:
    """Experiment H (2026-10-08): a scripted profile from a JSON file, in the vehicle's LOCAL_NED frame (with
    AHRS_EKF_TYPE 10, simulator truth: N = world +y, E = world +x; with EKF3 flying on the wall tag: the tag frame W).
    Segments, each logged as 'HSEG <i> <type> START t_sim=<s>':
      {"type": "move", "to": [N, E], "speed": v}  moving position setpoint (+ velocity feed-forward), yaw held
      {"type": "hold", "s": T}                    hold the current target for T sim seconds
      {"type": "occluder", "on": true|false}      cover / uncover the wall tag (logged 'OCCLUDER ON/OFF t_sim')
      {"type": "kill", "patterns": [p, ...]}     SIGKILL every process matching each pgrep -f pattern (logged 'KILL ...
                                                  t_sim'; option (i) safety tests, H ruling 2026-10-08)
      {"type": "param", "name": N, "value": v}    PARAM_SET in flight (logged 'PARAM N=v t_sim'; e.g. AHRS_UKF_TFAIL)
      {"type": "idle", "s": T}                    send NO setpoint for T sim seconds: the FC holds its own GUIDED target,
                                                  which follows an estimator reset (in-flight-anchor check; an absolute
                                                  setpoint from here would not follow a frame change)
      {"type": "wait_fix", "near": [N, E], "tol": m, "timeout": s}
          closed loop only: wait (holding position commands off) until LOCAL_POSITION_NED is within tol of `near`
          for 2 s, i.e. EKF3's ExtNav reset has put the estimate in the tag frame. Fails the trial on timeout.
    Ends with 'HPROFILE END t_sim=<s>'."""
    segs = json.load(open(path))
    msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=5.0)
    att = master.recv_match(type='ATTITUDE', blocking=True, timeout=5.0)
    if msg is None or att is None:
        raise TrialFailure("no LOCAL_POSITION_NED/ATTITUDE at profile start")
    cur = [msg.x, msg.y]; yaw0 = att.yaw
    log(f"HPROFILE: {len(segs)} segments from {path}, start N {cur[0]:.2f} E {cur[1]:.2f}, yaw {math.degrees(yaw0):.1f} deg, alt {alt_m:.2f} m")

    def send(pn, pe, vn, ve):
        master.mav.set_position_target_local_ned_send(
            0, master.target_system, master.target_component, mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            TYPE_MASK_POS_VEL_YAW, pn, pe, -alt_m, vn, ve, 0, 0, 0, 0, yaw0, 0)

    for i, sg in enumerate(segs):
        t0 = sim_time_now_s(master); log(f"HSEG {i} {sg['type']} START t_sim={t0:.3f}")
        if sg["type"] == "occluder":
            occluder(world, bool(sg["on"])); log(f"OCCLUDER {'ON' if sg['on'] else 'OFF'} t_sim={sim_time_now_s(master):.3f}")
            continue
        if sg["type"] == "kill":
            for pat in sg["patterns"]:
                r = subprocess.run(["pkill", "-KILL", "-f", pat], capture_output=True)
                log(f"KILL '{pat}' rc={r.returncode} t_sim={sim_time_now_s(master):.3f}")
            continue
        if sg["type"] == "param":
            master.mav.param_set_send(master.target_system, master.target_component, sg["name"].encode(), float(sg["value"]),
                                      mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
            log(f"PARAM {sg['name']}={sg['value']} t_sim={sim_time_now_s(master):.3f}")
            continue
        if sg["type"] == "idle":
            tw = time.time(); cap = float(sg["s"]) / MIN_ASSUMED_RTF + 60.0
            while time.time() - tw < cap:
                try:
                    if sim_time_now_s(master, timeout_s=0.5) - t0 >= float(sg["s"]):
                        break
                except TrialFailure:
                    pass
                time.sleep(0.1)
            else:
                raise TrialFailure(f"profile segment {i} (idle) did not complete within {cap:.0f} s wall-clock")
            continue
        if sg["type"] == "wait_fix":
            tw = time.time(); ok_since = None
            while time.time() - tw < float(sg["timeout"]) / MIN_ASSUMED_RTF + 30:
                m = master.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=1.0)
                if m is None:
                    continue
                inside = math.hypot(m.x - sg["near"][0], m.y - sg["near"][1]) <= float(sg["tol"])
                now = m.time_boot_ms / 1000.0
                ok_since = (ok_since or now) if inside else None
                if ok_since is not None and now - ok_since >= 2.0:
                    cur = [m.x, m.y]; yaw0 = master.recv_match(type='ATTITUDE', blocking=True, timeout=2.0).yaw
                    log(f"WAIT_FIX ok at N {m.x:.2f} E {m.y:.2f} t_sim={now:.3f}"); break
                if now - t0 > float(sg["timeout"]):
                    raise TrialFailure(f"wait_fix: no tag-frame position within {sg['timeout']} s")
            else:
                raise TrialFailure("wait_fix: wall-clock cap")
            continue
        if sg["type"] == "move":
            to = sg["to"]; v = float(sg["speed"]); d = math.hypot(to[0] - cur[0], to[1] - cur[1]); T = d / v if v > 0 else 0.0
            un, ue = ((to[0] - cur[0]) / d, (to[1] - cur[1]) / d) if d > 1e-9 else (0.0, 0.0)
        else:
            T = float(sg["s"]); un = ue = 0.0; v = 0.0
        tw = time.time(); cap = T / MIN_ASSUMED_RTF + 60.0
        while time.time() - tw < cap:
            try:
                now = sim_time_now_s(master, timeout_s=0.5)
            except TrialFailure:
                now = None
            if now is not None:
                el = now - t0
                if el >= T:
                    break
                send(cur[0] + un * v * el, cur[1] + ue * v * el, un * v, ue * v)
            time.sleep(0.05)
        else:
            raise TrialFailure(f"profile segment {i} did not complete within {cap:.0f} s wall-clock")
        if sg["type"] == "move":
            cur = [float(to[0]), float(to[1])]
        send(cur[0], cur[1], 0, 0)
    log(f"HPROFILE END t_sim={sim_time_now_s(master):.3f}")


def stop(master, settle_sim_s: float = 2.0) -> None:
    log(f"Stopping (holding zero velocity for {settle_sim_s:.1f}s sim time)...")
    start_sim_t = sim_time_now_s(master)
    t0 = time.time()
    wall_clock_cap_s = settle_sim_s / MIN_ASSUMED_RTF + 30.0
    while time.time() - t0 < wall_clock_cap_s:
        send_velocity(master, 0.0, 0.0, 0.0)
        try:
            now_sim_t = sim_time_now_s(master, timeout_s=0.5)
        except TrialFailure:
            now_sim_t = None
        if now_sim_t is not None and (now_sim_t - start_sim_t) >= settle_sim_s:
            return
        time.sleep(0.1)
    log("WARNING: stop settle did not confirm via sim time within cap - proceeding to land anyway.")


def land(master, wall_clock_cap_s: float = 180.0) -> None:
    log(f"Landing (wall-clock cap {wall_clock_cap_s:.0f}s)...")
    master.set_mode_apm('LAND')
    t0 = time.time()
    while time.time() - t0 < wall_clock_cap_s:
        hb = master.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
        if hb is not None and not (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
            log("Disarmed - landed.")
            return
    raise TrialFailure(f"Did not confirm disarm within {wall_clock_cap_s:.0f}s")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=14550)
    parser.add_argument('--altitude', type=float, required=True, help='target altitude, m')
    parser.add_argument('--velocity', type=float, required=True, help='cruise forward velocity, m/s')
    parser.add_argument('--duration', type=float, required=True, help='cruise duration, SIM seconds')
    args = parser.parse_args()
    master = None

    try:
        master = connect(args.port)
        healed = ensure_params(master, args.port)
        if healed is not None:
            master = healed
        require_fgo_node_current()
        require_watcher_before_arming()
        require_anchor_before_arming()
        wait_ready_to_arm(master)
        # Optional GROUND_TEST=<sim seconds> (closed-loop Part 1 SITL ground test only; unset for
        # every flight = unchanged): stay on the ground armed for that long, then disarm. No take-off.
        if os.environ.get("GROUND_TEST"):
            hold = float(os.environ["GROUND_TEST"])
            log(f"GROUND_TEST: holding armed on the ground for {hold:.0f} s sim, no take-off")
            t_start = sim_time_now_s(master)
            while sim_time_now_s(master) - t_start < hold:
                time.sleep(0.2)
            master.mav.command_long_send(master.target_system, master.target_component,
                                         mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 0, 0, 0, 0, 0, 0, 0)
            log("GROUND_TEST: disarm requested; ground test complete.")
            return 0
        wait_altitude(master, args.altitude)
        if os.environ.get("LAPS"):          # experiments T/L: "n_laps,side_m,speed"; unset = the corridor cruise, unchanged
            n_, side_, v_ = os.environ["LAPS"].split(",")
            laps(master, int(n_), float(side_), float(v_), args.altitude)
        elif os.environ.get("HPROFILE"):    # experiment H: JSON profile path; HWORLD = the Gazebo world name (occluder)
            hprofile(master, os.environ["HPROFILE"], args.altitude, os.environ.get("HWORLD", ""))
        elif os.environ.get("OUTBACK"):     # experiment O: "align_m,align_speed,out_m,speed,gate_n"
            a_, as_, o_, v_, g_ = (float(x) for x in os.environ["OUTBACK"].split(","))
            outback(master, a_, as_, o_, v_, g_, args.altitude)
        else:
            cruise(master, args.velocity, args.duration)
        stop(master)
        _watch["active"] = False     # landing: the watcher check is not applied (it must not abort the landing)
        land(master)
    except (TrialFailure, WatcherLost) as e:
        _watch["active"] = False
        print(f"[fly_trial] FAILED: {e}", file=sys.stderr, flush=True)
        # D24: a failure after arming must not leave the vehicle armed. Best effort, failure paths only
        # (a completed trial never reaches here): disarm on the ground test, LAND otherwise; confirmation
        # comes from HEARTBEAT, which does not depend on the estimator.
        try:
            if master is not None:
                hb = master.recv_match(type='HEARTBEAT', blocking=True, timeout=3.0)
                if hb is not None and (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
                    if os.environ.get("GROUND_TEST"):
                        log("After failure: disarming (ground test).")
                        master.mav.command_long_send(master.target_system, master.target_component,
                                                     mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 0, 0, 0, 0, 0, 0, 0)
                    land(master)
        except Exception as e2:
            print(f"[fly_trial] post-failure land/disarm did not confirm: {e2}", file=sys.stderr, flush=True)
        return 1

    log("Trial flight complete.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
