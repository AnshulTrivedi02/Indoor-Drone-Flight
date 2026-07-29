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
import sys
import time

from pymavlink import mavutil

# Expected GNSS-denied + flow + LiDAR baseline (see lidar_rangefinder.parm,
# flow_ekf.parm, gnss_denied.parm). Verified after connecting; self-healed
# if the eeprom persistence gotcha has left any of these stale.
EXPECTED_PARAMS = {
    'RNGFND1_TYPE': 10,
    'FLOW_TYPE': 5,
    'EK3_SRC1_VELXY': 5,
    'EK3_FLOW_USE': 1,
    'EK3_SRC1_POSXY': 0,
    'EK3_SRC1_POSZ': 2,
    'EK3_SRC1_VELZ': 0,
    'SIM_GPS1_ENABLE': 0,
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


def sim_time_now_s(master, timeout_s: float = 3.0) -> float:
    """Vehicle's own onboard clock (sim time), from any fresh MAVLink message."""
    msg = master.recv_match(type=['LOCAL_POSITION_NED', 'HEARTBEAT', 'SYS_STATUS'],
                             blocking=True, timeout=timeout_s)
    if msg is None or not hasattr(msg, 'time_boot_ms'):
        # HEARTBEAT has no time_boot_ms; retry with a type that does.
        msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=timeout_s)
    if msg is None:
        raise TrialFailure("No message received while reading sim-time clock")
    return msg.time_boot_ms / 1000.0


def cruise(master, velocity: float, duration_s: float, wall_clock_cap_s: float = None) -> None:
    """Fly forward at `velocity` m/s for `duration_s` SIM seconds, gated on
    the vehicle's own onboard clock, not wall-clock time."""
    if wall_clock_cap_s is None:
        wall_clock_cap_s = duration_s / MIN_ASSUMED_RTF + 120.0
    log(f"Cruising forward at {velocity:.2f} m/s for {duration_s:.1f} s of SIM time "
        f"(wall-clock cap {wall_clock_cap_s:.0f}s)...")

    start_sim_t = sim_time_now_s(master)
    t0 = time.time()
    last_sim_elapsed = 0.0
    while time.time() - t0 < wall_clock_cap_s:
        send_velocity(master, velocity, 0.0, 0.0)
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

    try:
        master = connect(args.port)
        healed = ensure_params(master, args.port)
        if healed is not None:
            master = healed
        wait_ready_to_arm(master)
        wait_altitude(master, args.altitude)
        cruise(master, args.velocity, args.duration)
        stop(master)
        land(master)
    except TrialFailure as e:
        print(f"[fly_trial] FAILED: {e}", file=sys.stderr, flush=True)
        return 1

    log("Trial flight complete.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
