#!/usr/bin/env python3
"""SITL ONLY (bench 2c; re-run 2026-10-12): the watcher's "telemetry link" = a UDP relay between a SITL serial port
(udpclient to --fc-side) and the watcher (udpin on --gcs-side). Control datagrams to --ctl-port (each switch is logged
with the wall time in --log):

  "drop" / "pass"       B3a link cut: drop ALL traffic, both directions / pass everything (the default)
  "ack_strip on|off"    F6 (unacknowledged LAND): strip every COMMAND_ACK (msgid 77) frame FC -> watcher only
  "hb_hold S"           F6: ARM a one-shot hold. On the next watcher -> FC DO_SET_MODE(LAND) frame, FC HEARTBEAT
                        frames FC -> watcher are dropped for S seconds (the pilot's switch move then reaches the FC
                        before any heartbeat showing LAND reaches the watcher: the F6 scenario). "hb_hold 0" disarms it
  "drop_land_once"      F6 (lost command): drop the NEXT watcher -> FC DO_SET_MODE(LAND) frame only, once

SITL's UDP serial output can pack several MAVLink frames into one datagram, so every datagram is parsed into frames
(v1 0xFE and v2 0xFD, v2 signature honoured); only the selected frames are removed, the rest is forwarded unchanged
(an unparseable tail is forwarded as is). Every removed frame is logged. FC HEARTBEAT arrivals (system 1, component 1)
are logged to --hb-log (wall time, custom_mode, forwarded 1/0): this measures whether the watcher's 5 Hz HEARTBEAT
request took effect (F6 depends on it). Watcher -> FC HEARTBEAT frames that are FORWARDED to the FC are logged to
--gcs-hb-log (wall time, system ID; added for wbench5_m2r: the FC-side time of the watcher's withdrawal).
"""
import argparse
import select
import socket
import struct
import time

MSG_HEARTBEAT, MSG_COMMAND_LONG, MSG_COMMAND_ACK = 0, 76, 77
CMD_DO_SET_MODE, COPTER_LAND = 176, 9


def frames(data):
    """Split a datagram into [(bytes, msgid, sysid, compid, payload)]; an unparseable tail is one (bytes, None, ...)."""
    out, i, n = [], 0, len(data)
    while i < n:
        b = data[i]
        if b == 0xFD and i + 10 <= n:
            ln, inc = data[i + 1], data[i + 2]
            L = 10 + ln + 2 + (13 if inc & 1 else 0)
            if i + L > n:
                break
            msgid = data[i + 7] | (data[i + 8] << 8) | (data[i + 9] << 16)
            out.append((data[i:i + L], msgid, data[i + 5], data[i + 6], data[i + 10:i + 10 + ln]))
            i += L
        elif b == 0xFE and i + 6 <= n:
            ln = data[i + 1]
            L = 6 + ln + 2
            if i + L > n:
                break
            out.append((data[i:i + L], data[i + 5], data[i + 3], data[i + 4], data[i + 6:i + 6 + ln]))
            i += L
        else:
            break
    if i < n:
        out.append((data[i:], None, None, None, b""))
    return out


def pad(p, n):
    return p + b"\0" * max(0, n - len(p))


def is_land_cmd(msgid, payload):
    if msgid != MSG_COMMAND_LONG:
        return False
    p = pad(payload, 33)
    param2 = struct.unpack_from("<f", p, 4)[0]
    cmd = struct.unpack_from("<H", p, 28)[0]
    return cmd == CMD_DO_SET_MODE and abs(param2 - COPTER_LAND) < 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fc-side", type=int, required=True, help="port SITL's udpclient sends to")
    ap.add_argument("--gcs-side", type=int, required=True, help="the watcher's udpin port")
    ap.add_argument("--ctl-port", type=int, required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--hb-log", default=None)
    ap.add_argument("--gcs-hb-log", default=None)
    a = ap.parse_args()
    A = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); A.bind(("127.0.0.1", a.fc_side))
    B = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); B.bind(("127.0.0.1", 0))
    C = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); C.bind(("127.0.0.1", a.ctl_port))
    log = open(a.log, "a", buffering=1)
    hbl = open(a.hb_log, "a", buffering=1) if a.hb_log else None
    ghl = open(a.gcs_hb_log, "a", buffering=1) if a.gcs_hb_log else None
    fc_addr = None
    drop = False
    ack_strip = False
    hb_hold_s = 0.0           # armed one-shot hold length
    hb_hold_until = 0.0
    drop_land_once = False
    n = [0, 0, 0]
    log.write(f"{time.time():.3f} relay up fc-side {a.fc_side} gcs-side {a.gcs_side}\n")
    while True:
        r, _, _ = select.select([A, B, C], [], [], 1.0)
        for s in r:
            data, addr = s.recvfrom(65536)
            now = time.time()
            if s is C:
                cmd = data.decode().strip()
                w = cmd.split()
                if cmd in ("drop", "pass"):
                    drop = cmd == "drop"
                elif w[0] == "ack_strip":
                    ack_strip = w[1] == "on"
                elif w[0] == "hb_hold":
                    hb_hold_s = float(w[1]); hb_hold_until = 0.0
                elif w[0] == "drop_land_once":
                    drop_land_once = True
                log.write(f"{now:.3f} {cmd} (fc->gcs {n[0]}, gcs->fc {n[1]}, dropped {n[2]})\n")
            elif s is A:
                fc_addr = addr
                if drop:
                    n[2] += 1
                    continue
                keep = []
                for raw, msgid, sysid, compid, pl in frames(data):
                    if msgid == MSG_HEARTBEAT and sysid == 1 and compid == 1:
                        held = now < hb_hold_until
                        if hbl:
                            hbl.write(f"{now:.4f},{struct.unpack_from('<I', pad(pl, 4), 0)[0]},{int(not held)}\n")
                        if held:
                            log.write(f"{now:.4f} held FC HEARTBEAT (mode "
                                      f"{struct.unpack_from('<I', pad(pl, 4), 0)[0]})\n")
                            continue
                    if ack_strip and msgid == MSG_COMMAND_ACK:
                        c_, r_ = struct.unpack_from("<HB", pad(pl, 3), 0)
                        log.write(f"{now:.4f} stripped COMMAND_ACK command {c_} result {r_}\n")
                        continue
                    keep.append(raw)
                if keep:
                    B.sendto(b"".join(keep), ("127.0.0.1", a.gcs_side)); n[0] += 1
            else:
                if drop or fc_addr is None:
                    n[2] += 1
                    continue
                keep = []
                for raw, msgid, sysid, compid, pl in frames(data):
                    if msgid is not None and is_land_cmd(msgid, pl):
                        if drop_land_once:
                            drop_land_once = False
                            log.write(f"{now:.4f} dropped watcher DO_SET_MODE(LAND) (drop_land_once)\n")
                            continue
                        if hb_hold_s > 0:
                            hb_hold_until = now + hb_hold_s
                            log.write(f"{now:.4f} watcher DO_SET_MODE(LAND) passed; FC HEARTBEAT held until "
                                      f"{hb_hold_until:.4f}\n")
                            hb_hold_s = 0.0
                        else:
                            log.write(f"{now:.4f} watcher DO_SET_MODE(LAND) passed\n")
                    keep.append(raw)
                    if ghl and msgid == MSG_HEARTBEAT:
                        ghl.write(f"{now:.4f},{sysid}\n")
                if keep:
                    A.sendto(b"".join(keep), fc_addr); n[1] += 1


if __name__ == "__main__":
    main()
