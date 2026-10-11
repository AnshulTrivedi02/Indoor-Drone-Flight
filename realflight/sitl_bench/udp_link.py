#!/usr/bin/env python3
"""SITL ONLY (bench 2c): the watcher's "telemetry link" = a UDP relay between a SITL serial port (udpclient to
--fc-side) and the watcher (udpin on --gcs-side), with a DROP switch for B3a (link cut, both directions), set by a
datagram "drop" / "pass" to --ctl-port. Logs every switch with the wall time.
"""
import argparse
import select
import socket
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fc-side", type=int, required=True, help="port SITL's udpclient sends to")
    ap.add_argument("--gcs-side", type=int, required=True, help="the watcher's udpin port")
    ap.add_argument("--ctl-port", type=int, required=True)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()
    A = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); A.bind(("127.0.0.1", a.fc_side))
    B = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); B.bind(("127.0.0.1", 0))
    C = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); C.bind(("127.0.0.1", a.ctl_port))
    log = open(a.log, "a", buffering=1)
    fc_addr = None
    drop = False
    n = [0, 0, 0]
    log.write(f"{time.time():.3f} relay up fc-side {a.fc_side} gcs-side {a.gcs_side}\n")
    while True:
        r, _, _ = select.select([A, B, C], [], [], 1.0)
        for s in r:
            data, addr = s.recvfrom(65536)
            if s is C:
                cmd = data.decode().strip()
                drop = cmd == "drop"
                log.write(f"{time.time():.3f} {cmd} (fc->gcs {n[0]}, gcs->fc {n[1]}, dropped {n[2]})\n")
            elif s is A:
                fc_addr = addr
                if drop:
                    n[2] += 1
                else:
                    B.sendto(data, ("127.0.0.1", a.gcs_side)); n[0] += 1
            else:
                if drop or fc_addr is None:
                    n[2] += 1
                else:
                    A.sendto(data, fc_addr); n[1] += 1


if __name__ == "__main__":
    main()
