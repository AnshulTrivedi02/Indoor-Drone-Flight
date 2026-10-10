"""MAVLink link from the watcher to the flight controller (G4, G5, G6 config check, G11).

Facts verified in ~/ardupilot at 7bac20cbcc (do not trust memory; re-verify on the real FC firmware):
  - The GCS-failsafe timer is refreshed ONLY by HEARTBEAT (GCS_Common.cpp:4345-4351 handle_heartbeat),
    RC_CHANNELS_OVERRIDE (:4184 + sysid_mygcs_seen) and MANUAL_CONTROL (:7652-7679) from a system ID for which
    GCS::sysid_is_gcs() is true (GCS.cpp:699-705: == MAV_GCS_SYSID, or within [MAV_GCS_SYSID, MAV_GCS_SYSID_HI] when
    HI > MAV_GCS_SYSID). This module therefore NEVER sends RC_CHANNELS_OVERRIDE or MANUAL_CONTROL, and sends
    HEARTBEAT only while the watcher is CONFIRMED.
  - MAV_GCS_SYSID default 255 (GCS.cpp:51) = the MAVProxy/pymavlink default source system: the watcher must use its
    own ID (G11); 255 and the FC's own ID are refused.
  - Copter LAND = custom mode 9 (ArduCopter/mode.h:86); set via MAV_CMD_DO_SET_MODE (176) with
    param1 = MAV_MODE_FLAG_CUSTOM_MODE_ENABLED (1), param2 = 9.
  - Commands from a non-GCS sysid are accepted unless MAV_OPTIONS bit 0 is set (GCS_Common.cpp:7393 accept_packet), so
    the watcher's LAND is accepted with MAV_GCS_SYSID = the watcher's ID, and the flight script (255) is still heard.

LAND policy (G4): one LAND per episode. The command is re-sent only until the FC ACKs it (any result), at most
`land_max_tries` times, `land_retry_s` apart; after the ACK it is never re-sent in the episode. Every send and the ACK
are logged for B7b.
"""
import os
import time

os.environ.setdefault("MAVLINK20", "1")
from pymavlink import mavutil  # noqa: E402

mavlink = mavutil.mavlink
COPTER_LAND = 9
FORBIDDEN_TYPES = ("RC_CHANNELS_OVERRIDE", "MANUAL_CONTROL")

# Expected FC parameters (see realflight/params/watcher_fc.parm). value -> predicate(v, sysid) -> (ok, why)
def expected_params(sysid, fs_gcs_timeout=3.0, require_lua_auth=False):
    def eq(target):
        return lambda v: (abs(v - target) < 0.5, f"!= {target}")
    exp = {
        "FS_GCS_ENABLE": eq(5),                                                     # 5 = Land
        "FS_GCS_TIMEOUT": eq(fs_gcs_timeout),
        "MAV_GCS_SYSID": eq(sysid),
        "MAV_GCS_SYSID_HI": (lambda v: (v <= sysid, f"> {sysid}: a GCS ID range would let other IDs refresh "
                                                    "the failsafe (G11)")),
        "FS_OPTIONS": (lambda v: (int(v) & 16 == 16, "bit 4 (16) clear: RC override would not win (B10)")),
        "MAV_OPTIONS": (lambda v: (int(v) & 1 == 0, "bit 0 set: the FC would drop the flight script's sysid-255 "
                                                    "traffic")),
        "ARMING_RUDDER": eq(0),                                                     # stick arming off (G6 i)
        "ARMING_SKIPCHK": (lambda v: (v >= 0 and int(v) & (1 << 17) == 0,
                                      "AUX_AUTH (bit 17) skipped or all checks skipped (-1)")),
    }
    if require_lua_auth:
        exp["SCR_ENABLE"] = eq(1)
    return exp


class FcLink:
    def __init__(self, device, sysid, compid=190, fc_sysid=1, fc_compid=1, log=print,
                 land_retry_s=0.3, land_max_tries=5, clock=time.monotonic):
        if not 1 <= sysid <= 254:
            raise ValueError(f"watcher sysid {sysid} not allowed: 255 is the MAVProxy/pymavlink default and would be "
                             "masked by any other GCS process (G11); use 1..254")
        if sysid == fc_sysid:
            raise ValueError("watcher sysid equals the FC's own sysid")
        self.sysid, self.compid, self.fc_sysid, self.fc_compid = sysid, compid, fc_sysid, fc_compid
        self.conn = mavutil.mavlink_connection(device, source_system=sysid, source_component=compid)
        self.mav = self.conn.mav
        self.log, self.clock = log, clock
        self.land_retry_s, self.land_max_tries = land_retry_s, land_max_tries
        self.land = None          # {"reason", "tries", "t_last", "acked", "result"}
        self.params = {}
        self.sent = {}            # message type -> count (for the tests and the summary)
        self.hb_sent = 0

    def fileno(self):
        try:
            return self.conn.fd
        except AttributeError:
            return self.conn.port.fileno()

    def _count(self, name):
        self.sent[name] = self.sent.get(name, 0) + 1

    # ---- outgoing ----
    def send_heartbeat(self):
        self.mav.heartbeat_send(mavlink.MAV_TYPE_GCS, mavlink.MAV_AUTOPILOT_INVALID, 0, 0, mavlink.MAV_STATE_ACTIVE)
        self.hb_sent += 1
        self._count("HEARTBEAT")

    def request_params(self, names):
        for n in names:
            self.mav.param_request_read_send(self.fc_sysid, self.fc_compid, n.encode(), -1)
            self._count("PARAM_REQUEST_READ")

    def request_streams(self, attitude_hz=25.0):
        """ATTITUDE for the identity check (>= 20 Hz) and HEARTBEAT is sent by the FC anyway."""
        self.mav.command_long_send(self.fc_sysid, self.fc_compid, mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
                                   mavlink.MAVLINK_MSG_ID_ATTITUDE, 1e6 / attitude_hz, 0, 0, 0, 0, 0)
        self._count("COMMAND_LONG")

    def statustext(self, text):
        self.mav.statustext_send(mavlink.MAV_SEVERITY_CRITICAL, text[:50].encode())
        self._count("STATUSTEXT")

    def command_land(self, reason):
        """Start the one-shot LAND for this episode (idempotent within the episode)."""
        if self.land is not None:
            return
        self.land = {"reason": reason, "tries": 0, "t_last": None, "acked": False, "result": None}
        self._send_land()

    def reset_episode(self):
        self.land = None

    def _send_land(self):
        self.land["tries"] += 1
        self.land["t_last"] = self.clock()
        self.mav.command_long_send(self.fc_sysid, self.fc_compid, mavlink.MAV_CMD_DO_SET_MODE,
                                   self.land["tries"] - 1,
                                   mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, COPTER_LAND, 0, 0, 0, 0, 0)
        self._count("COMMAND_LONG")
        self._count("LAND")
        self.log(f"LAND command sent (try {self.land['tries']}, wall {time.time():.3f}): {self.land['reason']}")

    def service(self):
        """Retry an un-ACKed LAND. Call every loop iteration."""
        L = self.land
        if L and not L["acked"] and L["tries"] < self.land_max_tries and \
                self.clock() - L["t_last"] >= self.land_retry_s:
            self._send_land()

    # ---- incoming ----
    def poll(self):
        """Drain received messages. Returns a list of (kind, data) events:
        ('fc_hb', armed, custom_mode), ('att', roll, pitch, yaw), ('param', name, value), ('ack', cmd, result),
        ('collision', text), ('fc_text', text)."""
        ev = []
        while True:
            m = self.conn.recv_match(blocking=False)
            if m is None:
                break
            t = m.get_type()
            if t == "BAD_DATA":
                continue
            src = m.get_srcSystem()
            if src == self.sysid:
                ev.append(("collision", f"received {t} from system ID {src} (the watcher's own ID), compid "
                                        f"{m.get_srcComponent()}"))
                continue
            if src != self.fc_sysid:
                continue
            if t == "HEARTBEAT" and m.autopilot != mavlink.MAV_AUTOPILOT_INVALID:
                ev.append(("fc_hb", bool(m.base_mode & mavlink.MAV_MODE_FLAG_SAFETY_ARMED), m.custom_mode))
            elif t == "ATTITUDE":
                ev.append(("att", m.roll, m.pitch, m.yaw))
            elif t == "PARAM_VALUE":
                name = m.param_id if isinstance(m.param_id, str) else m.param_id.decode()
                name = name.rstrip("\0")
                self.params[name] = m.param_value
                ev.append(("param", name, m.param_value))
            elif t == "COMMAND_ACK":
                if m.command == mavlink.MAV_CMD_DO_SET_MODE and self.land and not self.land["acked"]:
                    self.land["acked"], self.land["result"] = True, m.result
                    self.log(f"LAND ACK result {m.result} after {self.land['tries']} send(s) (wall {time.time():.3f})")
                ev.append(("ack", m.command, m.result))
            elif t == "STATUSTEXT":
                ev.append(("fc_text", m.text))
        return ev

    def verify_params(self, expected):
        """-> (ok or None if incomplete, why)."""
        missing = [n for n in expected if n not in self.params]
        if missing:
            return None, f"waiting for {missing}"
        bad = []
        for n, pred in expected.items():
            ok, why = pred(self.params[n])
            if not ok:
                bad.append(f"{n}={self.params[n]:g} {why}")
        return (not bad), ("ok" if not bad else "; ".join(bad))

    def close(self):
        self.conn.close()
