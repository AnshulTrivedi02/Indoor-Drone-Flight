import os
import signal
import subprocess
import sys
import time

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from realflight.watcher.tests.fakes import FakeFC, MocapFeeder, wait_for  # noqa: E402


class Rig:
    """One end-to-end rig: the watcher as a real subprocess, a FakeFC thread, a MocapFeeder thread, and optional
    beacon subprocesses. Everything is torn down in `close()` (SIGCONT before kill, sockets closed)."""

    def __init__(self, tmp_path):
        self.tmp = tmp_path
        self.procs = []
        self.fc = self.feeder = self.w = None

    def start(self, fc_kwargs=None, extra=(), deps=(), body_name="quad", identity="off", recover_s=0.5,
              feeder_body="quad", yaw_check="off", vel_check="off"):
        self.fc = FakeFC(**(fc_kwargs or {})); self.fc.start()
        self.out = str(self.tmp / "out")
        cmd = [sys.executable, "-m", "realflight.watcher.mocap_watch", self.out,
               "--fc", f"udpout:127.0.0.1:{self.fc.port}", "--sysid", "211",
               "--mocap-host", "127.0.0.1", "--mocap-port", "0", "--liveness-host", "127.0.0.1",
               "--box=-2,2,-2,2,0,2.5", "--body-name", body_name, "--identity", identity,
               "--yaw-check", yaw_check, "--vel-check", vel_check,
               "--recover-s", str(recover_s), "--land-retry-s", "0.3"]
        for d in deps:
            cmd += ["--dep", d]
        cmd += list(extra)
        self.log = open(self.tmp / "watcher.stderr", "w")
        self.w = subprocess.Popen(cmd, cwd=ROOT, stdout=self.log, stderr=subprocess.STDOUT)
        self.procs.append(self.w)
        ports = wait_for(lambda: self._ports(), 10)
        assert ports, "watcher did not start: " + open(self.tmp / "watcher.stderr").read()
        self.mocap_port, self.live_port = ports
        self.feeder = MocapFeeder(self.mocap_port, body_name=feeder_body); self.feeder.start()
        return self

    def _ports(self):
        p = os.path.join(self.out, "mocap_watch_ports.txt")
        try:
            d = dict(l.strip().split("=") for l in open(p) if "=" in l)
            return int(d["mocap"]), int(d["liveness"])
        except (OSError, KeyError, ValueError):
            return None

    def beacon(self, name, period=0.1, progress=True):
        code = ("import sys,time; sys.path.insert(0,%r)\n"
                "from realflight.watcher.liveness import LivenessBeacon\n"
                "b=LivenessBeacon(%r,('127.0.0.1',%d)); i=0\n"
                "while True:\n i+=1; b.beat(i if %r else None); time.sleep(%r)\n") % (
            ROOT, name, self.live_port, progress, period)
        p = subprocess.Popen([sys.executable, "-c", code])
        self.procs.append(p)
        return p

    def hb_file(self):
        return os.path.join(self.out, "watch_heartbeat")

    def stoplog(self):
        try:
            return open(os.path.join(self.out, "STOP_LOG.txt")).read()
        except OSError:
            return ""

    def close(self):
        for p in self.procs:
            try:
                p.send_signal(signal.SIGCONT)
            except ProcessLookupError:
                pass
        for p in self.procs:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(3)
                except subprocess.TimeoutExpired:
                    p.kill(); p.wait(3)
        if self.feeder:
            self.feeder.close()
        if self.fc:
            self.fc.close()
        if getattr(self, "log", None):
            self.log.close()


@pytest.fixture
def rig(tmp_path):
    r = Rig(tmp_path)
    try:
        yield r
    finally:
        r.close()
