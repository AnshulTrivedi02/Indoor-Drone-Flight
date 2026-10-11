#!/usr/bin/env python3
"""SITL ONLY (bench 2c): stand-in for a Pi dependency process (the real flow tracker / bridges are not run: SITL's own
flow sensor feeds EKF3).
  --beacon HOST:PORT  in-process LivenessBeacon at 5 Hz with a progress counter (the PREFERRED wiring, liveness.py);
                      SIGUSR1 freezes the counter while the beacon keeps going (a hang in the work path).
  no --beacon         a plain process (watched by the real `proc` sidecar instead).
"""
import argparse
import signal
import time

from realflight.watcher.liveness import LivenessBeacon


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--beacon")
    a = ap.parse_args()
    b = None
    if a.beacon:
        h, p = a.beacon.rsplit(":", 1)
        b = LivenessBeacon(a.name, (h, int(p)))
    st = {"hung": False, "prog": 0}

    def hang(*_):
        st["hung"] = True
        print(f"{time.time():.3f} {a.name}: work path HUNG (beacon continues, progress frozen)", flush=True)
    signal.signal(signal.SIGUSR1, hang)
    while True:
        if not st["hung"]:
            st["prog"] += 1
        if b:
            b.beat(st["prog"])
        time.sleep(0.2)


if __name__ == "__main__":
    main()
