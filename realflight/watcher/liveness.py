"""Networked process liveness (G7): replaces wall_watch.py's local `pgrep`.

Each process the flight depends on (on the Pi: flow tracker, flow bridge, tag/heading bridge, estimator node) is
represented by a BEACON: a small UDP datagram sent to the watcher at >= 5 Hz:
    {"n": <name>, "seq": <int>, "pid": <int>, "host": <str>, "t": <wall s>, "prog": <int or null>}
A dependency is ALIVE iff
    (a) a beacon from it arrived within dep_timeout_s (default 1.0 s), AND
    (b) if it reports "prog" (a work counter, e.g. messages processed or published), that counter advanced within
        progress_timeout_s (default 2.0 s).
(a) catches death, a SIGSTOP and a lost link; (b) catches a process that is alive and beaconing but no longer doing
its work (a hang in its processing path while a beacon thread keeps running).

Where the beacon comes from:
  - PREFERRED (deferred to the real-flight branch): `LivenessBeacon.beat(progress)` called from each process's own
    main work loop, so a hang stops the beacon itself. The SITL processes (flow_tracker.py, the bridges, fgo_node)
    must NOT be edited while the SITL safety re-tests fly, so this wiring is not done here.
  - NOW: sidecars, one per dependency, run on the Pi (see sidecars.py): a topic-rate sidecar (progress = messages
    seen on the process's OUTPUT topic, so a hung process stops the counter) and a /proc state sidecar (dead,
    zombie or stopped = no beacon). A dead sidecar also stops the beacon, so the failure is fail-closed.
"""
import json
import os
import socket
import time


class LivenessBeacon:
    def __init__(self, name, addr, host=None):
        self.name, self.addr = name, addr
        self.host = host or socket.gethostname()
        self.seq = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def beat(self, progress=None):
        self.seq += 1
        msg = {"n": self.name, "seq": self.seq, "pid": os.getpid(), "host": self.host, "t": time.time(),
               "prog": progress}
        try:
            self.sock.sendto(json.dumps(msg).encode(), self.addr)
        except OSError:
            pass                                  # a send failure is seen by the watcher as silence (fail-closed)

    def close(self):
        self.sock.close()


class LivenessMonitor:
    """Watcher side. feed(datagram, now) on receipt; status(now) -> {name: (alive, why)}."""

    def __init__(self, names, dep_timeout_s=1.0, progress_timeout_s=2.0):
        self.names = list(names)
        self.dep_timeout_s, self.progress_timeout_s = dep_timeout_s, progress_timeout_s
        self.last_rx = {}          # name -> monotonic receipt time
        self.last_prog = {}        # name -> (value, monotonic time it last changed)
        self.info = {}             # name -> last decoded beacon
        self.bad = 0
        self.unknown = {}

    def feed(self, data: bytes, now: float):
        try:
            m = json.loads(data.decode())
            name = m["n"]
        except (ValueError, KeyError, UnicodeDecodeError, TypeError):
            self.bad += 1
            return
        if name not in self.names:
            self.unknown[name] = self.unknown.get(name, 0) + 1
            return
        self.last_rx[name] = now
        self.info[name] = m
        p = m.get("prog")
        if p is not None:
            old = self.last_prog.get(name)
            if old is None or p != old[0]:
                self.last_prog[name] = (p, now)

    def status(self, now: float):
        out = {}
        for n in self.names:
            t = self.last_rx.get(n)
            if t is None:
                out[n] = (False, "no beacon yet")
            elif now - t > self.dep_timeout_s:
                out[n] = (False, f"beacon silent {now - t:.2f} s")
            elif n in self.last_prog and now - self.last_prog[n][1] > self.progress_timeout_s:
                out[n] = (False, f"no progress for {now - self.last_prog[n][1]:.2f} s (hung)")
            else:
                out[n] = (True, "ok")
        return out


class UdpLivenessSocket:
    def __init__(self, host="0.0.0.0", port=0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.sock.setblocking(False)

    @property
    def port(self):
        return self.sock.getsockname()[1]

    def fileno(self):
        return self.sock.fileno()

    def drain(self):
        out = []
        while True:
            try:
                out.append(self.sock.recv(4096))
            except (BlockingIOError, InterruptedError):
                return out

    def close(self):
        self.sock.close()
