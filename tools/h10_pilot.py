#!/usr/bin/env python3
"""SITL ONLY (H10 verification flight `h10_guard_check`, pre-registered in docs/h10_guard_check_prereg.md): a scripted
"pilot" on its own MAVLink link (SITL SERIAL1, tcp:127.0.0.1:5762, system 255 = SYSID_MYGCS, so RC override is
accepted). It never sends a mode command; it only moves the mode switch (channel 5) and centres the throttle by
RC_CHANNELS_OVERRIDE, as a pilot's transmitter would.

1. Wait until the FC has been ARMED in GUIDED and then shows LAND (fly_trial.py's scripted LAND).
2. 0.33 s (wall) later: the mode switch to position 5 (1685 us, FLTMODE5 = ALT_HOLD in h10_guard_check.parm) and the
   throttle centred (1500 us), re-sent at 10 Hz (RC_OVERRIDE_TIME default 3 s).
3. Hold for HOLD_S (wall) from the switch move: longer than fly_trial.land()'s 180 s wall cap, so the old code's
   failure path (re-send LAND) would have run inside the hold.
4. The mode switch to position 2 (1295 us, FLTMODE2 = LAND): the pilot lands. Keep the override until DISARMED, then
   release it (all zeros) and exit.
Every event is logged with wall time and the FC's time_boot_ms. Liveness: exits (rc 2) if no FC heartbeat for 60 s;
overall cap CAP_S. Usage: h10_pilot.py [--hold-s 200] [--cap-s 1500]
"""
import argparse
import os
import sys
import time

os.environ.setdefault("MAVLINK20", "1")
from pymavlink import mavutil  # noqa: E402

M = mavutil.mavlink
IGN = 65535                     # UINT16_MAX: "ignore this channel" (keep the RC input)
SW_ALTHOLD, SW_LAND, THR_MID = 1685, 1295, 1500


def log(s):
    print(f"[h10_pilot {time.time():.3f}] {s}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--link", default="tcp:127.0.0.1:5762")
    ap.add_argument("--hold-s", type=float, default=200.0)
    ap.add_argument("--cap-s", type=float, default=1500.0)
    a = ap.parse_args()
    t_start = time.time()
    m = None
    while m is None and time.time() - t_start < 600:
        try:
            # autoreconnect: fly_trial's ensure_params may soft-reboot SITL, which drops the TCP link
            m = mavutil.mavlink_connection(a.link, source_system=255, source_component=190, autoreconnect=True)
        except OSError as e:
            log(f"link not up yet ({e}); retrying"); time.sleep(5)
    if m is None:
        log("FAILED: no link"); return 2
    m.target_system, m.target_component = 1, 1
    log(f"connected {a.link}")
    state = "wait_armed_guided"
    t_land = t_sw = t_pilot_land = None
    last_hb = time.time(); last_rc = 0.0; ch5 = None
    boot_ms = 0
    while time.time() - t_start < a.cap_s:
        msg = m.recv_match(type=["HEARTBEAT", "SYSTEM_TIME"], blocking=True, timeout=0.05)
        now = time.time()
        if msg is not None and msg.get_type() == "SYSTEM_TIME":
            boot_ms = msg.time_boot_ms
        if msg is not None and msg.get_type() == "HEARTBEAT" and msg.get_srcSystem() == 1 and msg.type != M.MAV_TYPE_GCS:
            last_hb = now
            armed = bool(msg.base_mode & M.MAV_MODE_FLAG_SAFETY_ARMED)
            mode = msg.custom_mode
            if state == "wait_armed_guided" and armed and mode == 4:
                state = "wait_land"; log(f"FC armed in GUIDED (boot_ms {boot_ms})")
            elif state == "wait_land" and mode == 9:
                state, t_land = "pre_switch", now; log(f"FC shows LAND (the script's) (boot_ms {boot_ms})")
            elif state in ("hold", "pilot_land") and mode not in (2, 9):
                log(f"FC mode {mode} during the {state} (boot_ms {boot_ms})")
            if state == "hold" and mode == 2 and not getattr(m, "_seen_ah", False):
                m._seen_ah = True; log(f"FC shows ALT_HOLD, {now - t_sw:.3f} s after the switch move (boot_ms {boot_ms})")
            if state == "pilot_land" and not armed:
                log(f"FC DISARMED (boot_ms {boot_ms}); releasing the override")
                for _ in range(5):
                    m.mav.rc_channels_override_send(1, 1, 0, 0, 0, 0, 0, 0, 0, 0); time.sleep(0.1)
                return 0
        if now - last_hb > 60:
            log("FAILED: no FC heartbeat for 60 s"); return 2
        if state == "pre_switch" and now - t_land >= 0.33:
            state, t_sw, ch5 = "hold", now, SW_ALTHOLD
            log(f"PILOT: mode switch -> position 5 (ALT_HOLD), throttle centred, {now - t_land:.3f} s after LAND "
                f"(boot_ms {boot_ms})")
        if state == "hold" and now - t_sw >= a.hold_s:
            state, t_pilot_land, ch5 = "pilot_land", now, SW_LAND
            log(f"PILOT: mode switch -> position 2 (LAND) after a {now - t_sw:.1f} s hold (boot_ms {boot_ms})")
        if ch5 is not None and now - last_rc >= 0.1:
            m.mav.rc_channels_override_send(1, 1, IGN, IGN, THR_MID, IGN, ch5, IGN, IGN, IGN); last_rc = now
    log("FAILED: overall cap reached"); return 2


if __name__ == "__main__":
    sys.exit(main())
