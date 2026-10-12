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

LAND policy (G4): one LAND per episode. Every send, the ACK and the end of re-sending are logged (B7b).

LAND RE-SEND RULE (F6 fix, 2026-10-12; docs/handovers/2026-10-11_watcher_sitl_bench.md finding F6). The watcher's only
commanded state is LAND. Let M0 = the custom mode in the last FC HEARTBEAT received BEFORE the first send (None if no
FC heartbeat has been seen yet). After the first send:
  (S) STOP for good (latched for the episode; never re-sent) as soon as ANY of these holds:
      S1  the FC ACKs MAV_CMD_DO_SET_MODE (any result: the command reached the FC);
      S2  an FC HEARTBEAT received after the first send shows LAND (9): the command took effect, ACK lost or not;
      S3  an FC HEARTBEAT received after the first send shows a PILOT mode (PILOT_MODES below: ArduCopter's
          is_autopilot() == false, e.g. STABILIZE, ALT_HOLD, LOITER, POSHOLD), INCLUDING when M0 was already that mode:
          the safety pilot has (or keeps) authority, as FS_OPTIONS bit 4 gives it for the GCS failsafe (B10b);
      S4  an FC HEARTBEAT received after the first send shows a mode other than LAND and other than M0: a mode change
          the watcher did not command (e.g. the pilot switched, or the FC's own failsafe acted);
      S5  `land_max_tries` sends have been made.
  (R) RE-SEND only with positive evidence that the previous send had no effect: not stopped, at least `land_retry_s`
      since the last send, AND an FC HEARTBEAT received at least `land_evidence_s` after the last send shows the FC
      still in M0, an autopilot mode (not LAND, not a pilot mode). If M0 is None, the evidence heartbeat must show an
      autopilot mode other than LAND (no mode change is then detectable, but S2/S3 still apply).
  Why the evidence rule and not "re-send every 0.3 s until ACKed" (the old rule): the FC sends HEARTBEAT at 1 Hz by
  default (GCS_Common.cpp get_default_interval_for_ap_message), so a pilot can switch to ALT_HOLD 0.33 s after an
  accepted LAND (B10b) before any heartbeat shows LAND; a blind 0.3 s re-send would then override the pilot. Under (R)
  a re-send needs a heartbeat that post-dates the send by `land_evidence_s` and still shows the pre-LAND autopilot mode,
  and any heartbeat showing LAND, a pilot mode or another mode stops it. `request_streams` asks for HEARTBEAT at
  `fc_hb_hz` (5 Hz) on this link so the evidence normally arrives within ~0.2 s.
  Residual (stated, not closed): a heartbeat the FC emitted BEFORE it processed the LAND but that arrives more than
  `land_evidence_s` after the send (link latency > 0.2 s) looks like "no effect" and allows ONE re-send of the same LAND;
  it re-commands LAND only if the pilot switched to an AUTOPILOT mode in that window (a pilot mode stops it via S3 on
  the next heartbeat, and the re-sent LAND would be the same LAND the pilot just left). With no FC heartbeat at all
  nothing is re-sent; the watcher then withdraws on "FC link lost" and the FC's GCS failsafe acts (B3a).
"""
import os
import time

os.environ.setdefault("MAVLINK20", "1")
from pymavlink import mavutil  # noqa: E402

mavlink = mavutil.mavlink
COPTER_LAND = 9
# ArduCopter modes with is_autopilot() == false (ArduCopter/mode.h at 7bac20cbcc; Mode::Number values): the modes in
# which the GCS failsafe "continues pilot control" under FS_OPTIONS bit 4 (events.cpp:223). The watcher never re-sends
# LAND once the FC reports one of these (rule S3).
PILOT_MODES = {0: "STABILIZE", 1: "ACRO", 2: "ALT_HOLD", 5: "LOITER", 11: "DRIFT", 13: "SPORT", 14: "FLIP",
               15: "AUTOTUNE", 16: "POSHOLD", 18: "THROW", 22: "FLOWHOLD", 25: "SYSTEMID", 28: "TURTLE"}
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
                 land_retry_s=0.3, land_max_tries=5, clock=time.monotonic, land_evidence_s=0.2, fc_hb_hz=5.0):
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
        self.land_evidence_s, self.fc_hb_hz = land_evidence_s, fc_hb_hz
        self.fc_mode = None       # custom_mode of the last FC HEARTBEAT (None until one is received)
        self.fc_mode_t = None     # self.clock() at its receipt
        # {"reason", "tries", "t_first", "t_last", "acked", "result", "m0", "evidence_t", "stopped"}
        self.land = None
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

    def request_streams(self, attitude_hz=25.0, lpn_hz=10.0):
        """ATTITUDE for the identity check (>= 20 Hz); HEARTBEAT at fc_hb_hz (default 1 Hz on the FC) so the LAND
        re-send rule (F6) sees mode changes quickly. HEARTBEAT is in the FC's message-interval table
        (GCS_Common.cpp:1045), so SET_MESSAGE_INTERVAL applies to it; the request affects this link only.
        LOCAL_POSITION_NED at lpn_hz for the M2 velocity check (velcheck.py); it is in the same table
        (GCS_Common.cpp:1099, MSG_LOCAL_POSITION) and is sent only once the AHRS has a position relative to the EKF
        origin (GCS_Common.cpp:3042-3051)."""
        self.mav.command_long_send(self.fc_sysid, self.fc_compid, mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
                                   mavlink.MAVLINK_MSG_ID_ATTITUDE, 1e6 / attitude_hz, 0, 0, 0, 0, 0)
        self._count("COMMAND_LONG")
        if lpn_hz:
            self.mav.command_long_send(self.fc_sysid, self.fc_compid, mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
                                       mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 1e6 / lpn_hz, 0, 0, 0, 0, 0)
            self._count("COMMAND_LONG")
        if self.fc_hb_hz:
            self.mav.command_long_send(self.fc_sysid, self.fc_compid, mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
                                       mavlink.MAVLINK_MSG_ID_HEARTBEAT, 1e6 / self.fc_hb_hz, 0, 0, 0, 0, 0)
            self._count("COMMAND_LONG")

    def statustext(self, text):
        self.mav.statustext_send(mavlink.MAV_SEVERITY_CRITICAL, text[:50].encode())
        self._count("STATUSTEXT")

    def command_land(self, reason):
        """Start the one-shot LAND for this episode (idempotent within the episode)."""
        if self.land is not None:
            return
        self.land = {"reason": reason, "tries": 0, "t_first": None, "t_last": None, "acked": False, "result": None,
                     "m0": self.fc_mode, "evidence_t": None, "stopped": None}
        self._send_land()

    def reset_episode(self):
        self.land = None

    def _send_land(self):
        L = self.land
        L["tries"] += 1
        L["t_last"] = self.clock()
        if L["t_first"] is None:
            L["t_first"] = L["t_last"]
        L["evidence_t"] = None                      # evidence must post-date THIS send (rule R)
        self.mav.command_long_send(self.fc_sysid, self.fc_compid, mavlink.MAV_CMD_DO_SET_MODE,
                                   L["tries"] - 1,
                                   mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, COPTER_LAND, 0, 0, 0, 0, 0)
        self._count("COMMAND_LONG")
        self._count("LAND")
        self.log(f"LAND command sent (try {L['tries']}, wall {time.time():.3f}, FC mode before the first send "
                 f"{L['m0']}): {L['reason']}")

    def _stop_land(self, why):
        L = self.land
        if L is not None and L["stopped"] is None:
            L["stopped"] = why
            self.log(f"LAND re-send stopped after {L['tries']} send(s): {why} (wall {time.time():.3f})")

    def _land_on_fc_mode(self, mode, t_rx):
        """Rules S2-S4 and the evidence for R, applied to every FC HEARTBEAT received after the first send."""
        L = self.land
        if L is None or L["stopped"] is not None or L["t_first"] is None:
            return
        if mode == COPTER_LAND:
            self._stop_land("FC heartbeat shows LAND (S2)")
        elif mode in PILOT_MODES:
            self._stop_land(f"FC heartbeat shows the pilot mode {PILOT_MODES[mode]} (S3): the pilot has authority")
        elif L["m0"] is not None and mode != L["m0"]:
            self._stop_land(f"FC mode changed {L['m0']} -> {mode}, not commanded by the watcher (S4)")
        elif t_rx - L["t_last"] >= self.land_evidence_s:
            L["evidence_t"] = t_rx                  # still in M0 (an autopilot mode) after the send: no effect seen

    def service(self):
        """Re-send an un-ACKed LAND under rule R only. Call every loop iteration, after poll()."""
        L = self.land
        if not L or L["acked"] or L["stopped"] is not None:
            return
        if L["tries"] >= self.land_max_tries:
            self._stop_land(f"{L['tries']} sends without an ACK or a mode change (S5)")
            return
        if self.clock() - L["t_last"] >= self.land_retry_s and L["evidence_t"] is not None:
            self._send_land()

    # ---- incoming ----
    def poll(self):
        """Drain received messages. Returns a list of (kind, data) events:
        ('fc_hb', armed, custom_mode), ('att', roll, pitch, yaw, time_boot_ms), ('param', name, value),
        ('ack', cmd, result), ('collision', text), ('fc_text', text), ('lpn', vx, vy, vz, time_boot_ms)
        (LOCAL_POSITION_NED velocity, NED m/s, for the M2 check), ('origin', lat_e7, lon_e7) (GPS_GLOBAL_ORIGIN:
        the AHRS broadcasts it on every channel when the EKF origin first becomes valid, AP_AHRS.cpp:428-440; the F7
        yaw-check tie is captured at the first one in an FC boot)."""
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
                t_rx = self.clock()
                self.fc_mode, self.fc_mode_t = m.custom_mode, t_rx
                self._land_on_fc_mode(m.custom_mode, t_rx)
                ev.append(("fc_hb", bool(m.base_mode & mavlink.MAV_MODE_FLAG_SAFETY_ARMED), m.custom_mode))
            elif t == "ATTITUDE":
                ev.append(("att", m.roll, m.pitch, m.yaw, m.time_boot_ms))
            elif t == "LOCAL_POSITION_NED":
                ev.append(("lpn", m.vx, m.vy, m.vz, m.time_boot_ms))
            elif t == "GPS_GLOBAL_ORIGIN":
                ev.append(("origin", m.latitude, m.longitude))
            elif t == "PARAM_VALUE":
                name = m.param_id if isinstance(m.param_id, str) else m.param_id.decode()
                name = name.rstrip("\0")
                self.params[name] = m.param_value
                ev.append(("param", name, m.param_value))
            elif t == "COMMAND_ACK":
                if m.command == mavlink.MAV_CMD_DO_SET_MODE and self.land and not self.land["acked"]:
                    self.land["acked"], self.land["result"] = True, m.result
                    self.log(f"LAND ACK result {m.result} after {self.land['tries']} send(s) (wall {time.time():.3f})")
                    self._stop_land(f"ACK received, result {m.result} (S1)")
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
