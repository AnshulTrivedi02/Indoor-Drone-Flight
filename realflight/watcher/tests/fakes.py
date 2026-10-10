"""Test fakes: a fake flight controller (pymavlink on loopback UDP), a fake mocap stream, and a copy of the flight
script's heartbeat-file parser.

ALL sockets bind 127.0.0.1 port 0 (ephemeral); nothing here touches 14550-14560 or 5760, so nothing can reach a live
SITL instance.

The FakeFC's GCS-failsafe behaviour is OUR MODEL of ArduCopter (events.cpp failsafe_gcs_check / failsafe_gcs_on_event
and AP_Arming_Copter::gcs_failsafe_check at 7bac20cbcc), not ArduPilot itself. Tests against it prove the WATCHER's
side (what it sends, and when it stops); the FC side is proven on the bench (B1c, B2b, B3a).
"""
import math
import os
import threading
import time

os.environ.setdefault("MAVLINK20", "1")
from pymavlink import mavutil  # noqa: E402

mavlink = mavutil.mavlink

from realflight.watcher import mocap  # noqa: E402

GOOD_PARAMS = {"FS_GCS_ENABLE": 5, "FS_GCS_TIMEOUT": 3, "MAV_GCS_SYSID": 211, "MAV_GCS_SYSID_HI": 0,
               "FS_OPTIONS": 16, "MAV_OPTIONS": 0, "ARMING_RUDDER": 0, "ARMING_SKIPCHK": 0}


def watch_ok_copy(path, stale_s=3.0):
    """VERBATIM LOGIC COPY of fly_trial.py watch_ok() (fly_trial.py:314-327 at 91e87c9), with the path passed in
    instead of read from WATCH_HEARTBEAT. fly_trial.py is not imported (import side effects)."""
    try:
        f = open(path).read().split()
        age = time.time() - float(f[0]); flags = dict(kv.split("=") for kv in f[1:])
    except (OSError, ValueError, IndexError):
        return False, "no watcher heartbeat"
    if age > stale_s:
        return False, f"watcher heartbeat stale ({age:.1f} s)"
    if flags.get("box") != "1" or flags.get("bridge") != "1":
        return False, f"watcher not confirming (box={flags.get('box')} bridge={flags.get('bridge')})"
    return True, f"watcher ok (age {age:.1f} s)"


class FakeFC(threading.Thread):
    def __init__(self, params=None, gcs_sysid=211, fs_timeout=3.0, armed=False, failsafe_model=True,
                 drop_first_commands=0, ack=True, att_hz=50.0):
        super().__init__(daemon=True)
        self.conn = mavutil.mavlink_connection("udpin:127.0.0.1:0", source_system=1, source_component=1)
        self.port = self.conn.port.getsockname()[1]
        self.params = dict(GOOD_PARAMS if params is None else params)
        self.gcs_sysid, self.fs_timeout = gcs_sysid, fs_timeout
        self.armed, self.mode = armed, 4             # GUIDED
        self.failsafe_model = failsafe_model
        self.drop_first_commands, self.ack = drop_first_commands, ack
        self.att = (0.0, 0.0, 0.0)                    # roll, pitch, yaw (FRD, rad), settable by tests
        self.att_hz = att_hz
        self.rx = []                                  # (t_mono, type, srcSystem, msg)
        self.events = []                              # (t_mono, text)
        self.gcs_last_seen = 0.0
        self.fs_gcs = False
        self.n_cmd = 0
        self.stop_ev = threading.Event()
        self.lock = threading.Lock()

    # ---- model of the FC's arming gate (stock: refuses only while the GCS failsafe is latched) ----
    def try_arm(self):
        if self.fs_gcs:
            return False, "PreArm: GCS failsafe on"
        self.armed = True
        return True, "armed"

    def run(self):
        t_hb = t_att = t_fs = 0.0
        while not self.stop_ev.is_set():
            now = time.monotonic()
            m = self.conn.recv_match(blocking=True, timeout=0.005)
            if m is not None and m.get_type() != "BAD_DATA":
                self._handle(now, m)
            if getattr(self.conn, "clients", None):                     # a peer has spoken (udpin server mode)
                if now - t_hb >= 0.2:
                    t_hb = now
                    base = mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED | (
                        mavlink.MAV_MODE_FLAG_SAFETY_ARMED if self.armed else 0)
                    self.conn.mav.heartbeat_send(mavlink.MAV_TYPE_QUADROTOR, mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
                                                 base, self.mode, mavlink.MAV_STATE_ACTIVE)
                if self.att_hz and now - t_att >= 1.0 / self.att_hz:
                    t_att = now
                    r, p, y = self.att
                    self.conn.mav.attitude_send(int(now * 1000) & 0xFFFFFFFF, r, p, y, 0, 0, 0)
            if self.failsafe_model and now - t_fs >= 1 / 3.0:            # three_hz_loop
                t_fs = now
                self._gcs_check(now)

    def _gcs_check(self, now):
        if self.gcs_last_seen == 0.0:                                     # events.cpp: never seen -> no check
            return
        age = now - self.gcs_last_seen
        if age < self.fs_timeout and self.fs_gcs:
            self.fs_gcs = False; self.events.append((now, "GCS failsafe cleared"))
        elif age > self.fs_timeout and not self.fs_gcs:
            self.fs_gcs = True
            if self.armed:                                                # landed bench model: disarm
                self.armed = False; self.events.append((now, "GCS failsafe: disarming"))
            else:
                self.events.append((now, "GCS failsafe (disarmed)"))

    def _handle(self, now, m):
        t, src = m.get_type(), m.get_srcSystem()
        with self.lock:
            self.rx.append((now, t, src, m))
        if t in ("HEARTBEAT", "RC_CHANNELS_OVERRIDE", "MANUAL_CONTROL") and src == self.gcs_sysid:
            self.gcs_last_seen = now
        if t == "PARAM_REQUEST_READ":
            name = m.param_id if isinstance(m.param_id, str) else m.param_id.decode()
            name = name.rstrip("\0")
            if name in self.params:
                self.conn.mav.param_value_send(name.encode(), float(self.params[name]),
                                               mavlink.MAV_PARAM_TYPE_REAL32, len(self.params), 0)
        elif t == "COMMAND_LONG" and m.command == mavlink.MAV_CMD_DO_SET_MODE:
            self.n_cmd += 1
            if self.n_cmd <= self.drop_first_commands:
                return
            self.mode = int(m.param2)
            self.events.append((now, f"mode {self.mode} from sysid {src}"))
            if self.mode == 9 and self.armed:                             # LAND on the ground: disarm
                self.armed = False; self.events.append((now, "LAND: disarmed (landed)"))
            if self.ack:
                self.conn.mav.command_ack_send(m.command, mavlink.MAV_RESULT_ACCEPTED)

    def received(self, type_=None, src=None, since=None):
        with self.lock:
            return [r for r in self.rx if (type_ is None or r[1] == type_) and (src is None or r[2] == src)
                    and (since is None or r[0] >= since)]

    def lands(self, since=None):
        return [r for r in self.received("COMMAND_LONG", since=since)
                if r[3].command == mavlink.MAV_CMD_DO_SET_MODE and int(r[3].param2) == 9]

    def close(self):
        self.stop_ev.set()
        self.join(timeout=2)
        self.conn.close()


class MocapFeeder(threading.Thread):
    """Sends MCP1 packets at `hz`. Tests mutate .pos / .quat / .tracked / .body_name / .paused."""

    def __init__(self, port, hz=100.0, body_name="quad", body_id=1, tracked=1):
        super().__init__(daemon=True)
        import socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = ("127.0.0.1", port)
        self.hz, self.body_name, self.body_id, self.tracked = hz, body_name, body_id, tracked
        self.pos, self.quat = (0.0, 0.0, 1.0), (1.0, 0.0, 0.0, 0.0)
        self.paused = False
        self.frame = 0
        self.jitter = True                 # tiny noise so poses are not bit-identical
        self.stop_ev = threading.Event()
        self.sent_log = []                 # (t_mono, pos)

    def run(self):
        while not self.stop_ev.is_set():
            if not self.paused:
                self.frame += 1
                p = self.pos
                if self.jitter:
                    e = 1e-5 * math.sin(self.frame)
                    p = (p[0] + e, p[1], p[2])
                self.sent_log.append((time.monotonic(), p))
                self.sock.sendto(mocap.encode(self.frame, time.time(), self.body_id, self.body_name, self.tracked,
                                              p, self.quat), self.addr)
            time.sleep(1.0 / self.hz)

    def close(self):
        self.stop_ev.set(); self.join(timeout=2); self.sock.close()


def quat_from_euler_zup(roll, pitch, yaw):
    """FLU/z-up ZYX euler -> quaternion (w, x, y, z)."""
    cr, sr = math.cos(roll / 2), math.sin(roll / 2)
    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
    return (cr * cp * cy + sr * sp * sy, sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy)


def wait_for(pred, timeout, step=0.02):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        v = pred()
        if v:
            return v
        time.sleep(step)
    return pred()
