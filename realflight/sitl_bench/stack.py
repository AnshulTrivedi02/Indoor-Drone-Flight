"""SITL ONLY (bench 2c): launch / tear down the watcher-bench stack, and the bench operator's MAVLink link.

Stack (all ports outside 14550-14560; SITL instance 0 because the Gazebo ArduPilotPlugin is fixed to it):
  gz sim (iris_runway, headless) -> arducopter (OWN cwd ~/thesis_data/wbench/sitl_cwd, eeprom wiped per session)
    SERIAL0 tcp 5760  <- MAVProxy (system ID 255 GCS; --out 14581 for the flight script)
    SERIAL1 -> 14571  <- udp_link relay -> watcher udpin 14572 (relay control 9878)
    SERIAL2 -> 14575  <- this operator (udpin)
    SERIAL3 -> 14577  <- the B6b observer watcher (udpin)
    RC in: UDP 5501 (the "transmitter")
  ros_gz_bridge (dynamic_pose + clock) -> ground_truth_pub.py -> mocap_forwarder (dest0 9870 watcher, dest1 9880
  observer; control 9879)
  deps: flow_tracker stub (in-process beacon) and flow_bridge stub (+ proc sidecar) -> liveness 9871
gz-transport and ROS 2 are isolated (GZ_PARTITION, ROS_DOMAIN_ID, loopback).
"""
import math
import os
import re
import signal
import socket
import struct
import subprocess
import threading
import time

os.environ.setdefault("MAVLINK20", "1")
from pymavlink import mavutil  # noqa: E402

M = mavutil.mavlink
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOME = os.path.expanduser("~")
AP = f"{HOME}/ardupilot"
VENV_PY = f"{HOME}/venv-ardupilot/bin/python3"
WORLD = "iris_textured"   # amendment A5 (was iris_runway): the camera-flow path needs the textured mat
P = dict(serial1=14571, watcher_fc=14572, op=14575, observer_fc=14577, fs=14581, mocap=9870, observer_mocap=9880,
         fwd_ctl=9879, relay_ctl=9878, live=9871, rc=5501)
BOX = "-3,3,-3,3,-0.5,3.0"
ISO = {"GZ_PARTITION": "wbench", "GZ_IP": "127.0.0.1", "ROS_DOMAIN_ID": "57",
       "ROS_AUTOMATIC_DISCOVERY_RANGE": "LOCALHOST"}


def ros_env():
    out = subprocess.run(["bash", "-c", "source /opt/ros/jazzy/setup.bash >/dev/null 2>&1; source $HOME/thesis_ws/install/setup.bash >/dev/null 2>&1; env -0"],
                         capture_output=True, check=True).stdout
    env = dict(kv.split("=", 1) for kv in out.decode().split("\0") if "=" in kv)
    env.update(ISO)
    env["PYTHONPATH"] = REPO + ":" + env.get("PYTHONPATH", "")
    return env


class Stack:
    def __init__(self, out, ground=False, log=print):
        self.out, self.ground, self.log = out, ground, log
        os.makedirs(out, exist_ok=True)
        self.procs = {}
        self.cwd = f"{HOME}/thesis_data/wbench/sitl_cwd"
        self.renv = ros_env()
        self.penv = dict(os.environ, PYTHONPATH=REPO, MAVLINK20="1", **ISO)

    # ---------- processes ----------
    def spawn(self, name, cmd, env=None, cwd=None):
        f = open(os.path.join(self.out, f"{name}.log"), "a")
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env or self.penv,
                             cwd=cwd or REPO, start_new_session=True)
        self.procs[name] = p
        self.log(f"spawned {name} pid {p.pid}")
        return p

    def alive(self, name):
        p = self.procs.get(name)
        return p is not None and p.poll() is None

    def send_sig(self, name, sig):
        p = self.procs[name]
        t = time.time()
        os.kill(p.pid, sig)
        return t

    def stop(self, name, sig=signal.SIGTERM, wait=10):
        p = self.procs.get(name)
        if p is None or p.poll() is not None:
            return
        try:
            os.killpg(p.pid, sig)
        except ProcessLookupError:
            return
        try:
            p.wait(wait)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL); p.wait(5)

    def wait_for(self, what, cond, cap, need=("gz", "sitl")):
        t0 = time.time()
        while time.time() - t0 < cap:
            for n in need:
                if n in self.procs and not self.alive(n):
                    raise RuntimeError(f"{n} died while waiting for {what}")
            try:
                if cond():
                    self.log(f"ready: {what} after {time.time() - t0:.1f} s")
                    return
            except Exception:
                pass
            time.sleep(0.5)
        raise RuntimeError(f"timeout ({cap} s) waiting for {what}")

    def start(self):
        os.makedirs(self.cwd, exist_ok=True)
        for f in ("eeprom.bin",):
            if os.path.exists(os.path.join(self.cwd, f)):
                os.remove(os.path.join(self.cwd, f))
        gz_env = dict(self.renv)
        gz_env["GZ_SIM_RESOURCE_PATH"] = f"{REPO}/sim/models:{HOME}/ardupilot_gazebo/models:{HOME}/ardupilot_gazebo/worlds"
        gz_env["GZ_SIM_SYSTEM_PLUGIN_PATH"] = f"{HOME}/ardupilot_gazebo/build"
        self.gz_env = gz_env
        self.spawn("gz", ["gz", "sim", "-v3", "-s", "-r", f"{REPO}/sim/worlds/{WORLD}.sdf"], env=gz_env,
                   cwd=f"{HOME}/ardupilot_gazebo")
        self.wait_for("gz world up", lambda: f"/world/{WORLD}/dynamic_pose/info" in subprocess.run(
            ["gz", "topic", "-l"], capture_output=True, text=True, timeout=5, env=gz_env).stdout, 90, need=("gz",))
        defaults = [f"{AP}/Tools/autotest/default_params/copter.parm",
                    f"{AP}/Tools/autotest/default_params/gazebo-iris.parm",
                    f"{REPO}/lidar_rangefinder.parm",
                    f"{REPO}/flow_ekf.parm",
                    f"{REPO}/realflight/sitl_bench/params/wbench_ekf3_flow.parm",
                    f"{REPO}/realflight/params/watcher_fc.parm"]
        if self.ground:
            defaults.append(f"{REPO}/realflight/sitl_bench/params/wbench_ground.parm")
        os.makedirs(os.path.join(self.cwd, "scripts"), exist_ok=True)
        self.spawn("sitl", [f"{AP}/build/sitl/bin/arducopter", "--model", "JSON", "--speedup", "1", "--slave", "0",
                            "--defaults", ",".join(defaults),
                            f"--serial1=udpclient:127.0.0.1:{P['serial1']}",
                            f"--serial2=udpclient:127.0.0.1:{P['op']}",
                            f"--serial3=udpclient:127.0.0.1:{P['observer_fc']}",
                            "--sim-address=127.0.0.1", "-I0"], cwd=self.cwd)
        self.wait_for("SITL tcp 5760", lambda: ":5760 " in subprocess.run(["ss", "-tln"], capture_output=True,
                                                                         text=True).stdout, 60)
        self.spawn("relay", [VENV_PY, "-m", "realflight.sitl_bench.udp_link", "--fc-side", str(P["serial1"]),
                             "--gcs-side", str(P["watcher_fc"]), "--ctl-port", str(P["relay_ctl"]),
                             "--log", os.path.join(self.out, "relay_events.txt"),
                             "--hb-log", os.path.join(self.out, "relay_fc_hb.csv")])
        self.spawn("mavproxy", [f"{HOME}/venv-ardupilot/bin/mavproxy.py", "--daemon", "--retries", "5",
                                "--master", "tcp:127.0.0.1:5760", "--out", f"127.0.0.1:{P['fs']}",
                                "--out", "127.0.0.1:14551", "--out", "127.0.0.1:14552", "--out", "127.0.0.1:14553"], cwd=self.out)
        self.wait_for("MAVProxy online", lambda: "online system" in open(os.path.join(self.out, "mavproxy.log")).read(),
                      240)
        self.spawn("bridge", ["ros2", "run", "ros_gz_bridge", "parameter_bridge",
                              f"/world/{WORLD}/dynamic_pose/info@geometry_msgs/msg/PoseArray[gz.msgs.Pose_V",
                              "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
                              "/downward_lidar/range@sensor_msgs/msg/Range[gz.msgs.LaserScan",
                              "/downward_camera/image@sensor_msgs/msg/Image@gz.msgs.Image",
                              "/downward_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo"],
                   env=self.renv)
        # the thesis stack's rangefinder path (amendment A4): Gazebo gpu_lidar -> lidar_bridge.py -> DISTANCE_SENSOR
        self.spawn("lidar_bridge", [VENV_PY, f"{REPO}/lidar_bridge.py", "--ros-args", "-p", "use_sim_time:=true"],
                   env=self.renv)
        # the thesis camera-flow path (amendment A5): flow_tracker (attitude via /attitude/angular_rates is only for its
        # characterisation output) -> flow_bridge -> OPTICAL_FLOW on 14553
        self.spawn("attitude_bridge", [VENV_PY, f"{REPO}/attitude_bridge.py", "--ros-args", "-p", "use_sim_time:=true"],
                   env=self.renv)
        self.spawn("flow_tracker_real", ["ros2", "run", "optical_flow_node", "flow_tracker", "--ros-args", "-p",
                                         "use_sim_time:=true", "-p", "ransac_seed:=42"], env=self.renv)
        self.spawn("flow_bridge_real", [VENV_PY, f"{REPO}/flow_bridge.py", "--ros-args", "-p", "use_sim_time:=true"],
                   env=self.renv)
        self.spawn("gtpub", ["python3", f"{REPO}/ground_truth_pub.py", WORLD], env=self.renv)
        self.spawn("forwarder", ["python3", "-m", "realflight.sitl_bench.mocap_forwarder",
                                 "--dest", f"127.0.0.1:{P['mocap']}", "--dest", f"127.0.0.1:{P['observer_mocap']}",
                                 "--ctl-port", str(P["fwd_ctl"]), "--log", os.path.join(self.out, "forwarder.csv")],
                   env=self.renv)
        self.wait_for("mocap packets flowing", lambda: os.path.getsize(os.path.join(self.out, "forwarder.csv")) > 5000,
                      90)
        self.start_deps()

    def start_deps(self, which=("flow_tracker", "flow_bridge", "sidecar")):
        live = f"127.0.0.1:{P['live']}"
        if "flow_tracker" in which:
            self.spawn("flow_tracker", [VENV_PY, "-m", "realflight.sitl_bench.dep_stub", "--name", "flow_tracker",
                                        "--beacon", live])
        if "flow_bridge" in which:
            self.spawn("flow_bridge", [VENV_PY, "-m", "realflight.sitl_bench.dep_stub", "--name", "flow_bridge"])
        if "sidecar" in which:
            self.spawn("sidecar", [VENV_PY, "-m", "realflight.watcher.sidecars", "proc", "--name", "flow_bridge",
                                   "--pattern", "realflight.sitl_bench.dep_stub --name flow_bridge", "--to", live])

    def teardown(self):
        for n in reversed(list(self.procs)):
            p = self.procs[n]
            if p.poll() is None:
                try:
                    os.killpg(p.pid, signal.SIGCONT)
                except ProcessLookupError:
                    pass
                self.stop(n, signal.SIGTERM, wait=8)
        # belt and braces, scoped to THIS stack's unique command lines
        for pat in (f"sim/worlds/{WORLD}.sdf", "sitl_bench.mocap_forwarder", "sitl_bench.udp_link",
                    "sitl_bench.dep_stub", "sitl_bench.flight_script", "realflight.watcher.mocap_watch",
                    "realflight.watcher.sidecars", f"serial2=udpclient:127.0.0.1:{P['op']}",
                    f"--out 127.0.0.1:{P['fs']}", f"/world/{WORLD}/dynamic_pose/info@geometry_msgs",
                    f"ground_truth_pub.py {WORLD}", f"{REPO}/lidar_bridge.py", f"{REPO}/flow_bridge.py", f"{REPO}/attitude_bridge.py",
                    "optical_flow_node/flow_tracker", "/downward_camera/image@sensor_msgs"):
            subprocess.run(["pkill", "-9", "-f", "--", pat])
        self.log("teardown complete")

    def current_q(self):
        """The vehicle's current Gazebo orientation (w, x, y, z), from one dynamic_pose/info message."""
        for _ in range(3):
            out = subprocess.run(["gz", "topic", "-e", "-n", "1", "-t", f"/world/{WORLD}/dynamic_pose/info"],
                                 capture_output=True, text=True, env=self.gz_env, timeout=15).stdout
            i = out.find('name: "iris_with_ardupilot"')
            if i < 0:
                continue
            j = out.find("orientation {", i)
            k = out.find("}", j)
            if j < 0 or k < 0:
                continue
            v = dict(re.findall(r"([wxyz]): (-?[0-9.eE+-]+)", out[j:k]))
            return tuple(float(v.get(c, 0.0)) for c in "wxyz")
        raise RuntimeError("could not read the vehicle orientation from Gazebo")

    def carry_home(self):
        """The bench analogue of carrying the landed, DISARMED vehicle back to the spawn point (Gazebo set_pose).
        Amendment A9 (2026-10-12): the vehicle KEEPS ITS CURRENT HEADING (levelled, yaw unchanged). A teleport that
        also rotates it back to the spawn heading is a rotation the FC's gyros never see: after B6b's 90 deg yaw it
        left EKF3's yaw 77 deg off the truth, the compass corrected it at ~1.4 deg/s, the FC armed at 22 deg error and
        the vehicle flew away on take-off (wbench2_hoverB_20261012_112751, B6b_static_other_body)."""
        w, x, y, z = self.current_q()
        yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        self.log(f"carry home keeping the heading: Gazebo yaw {math.degrees(yaw):.1f} deg (ENU)")
        return self.teleport(0, 0, 0.2, q=(math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)))

    def teleport(self, x, y, z, q=(0.70710678, 0, 0, 0.70710678)):
        """Gazebo set_pose of the vehicle (DISARMED only): the SITL analogue of carrying it by hand. Returns wall time."""
        req = (f'name: "iris_with_ardupilot", position: {{x: {x}, y: {y}, z: {z}}}, '
               f'orientation: {{w: {q[0]}, x: {q[1]}, y: {q[2]}, z: {q[3]}}}')
        t = time.time()
        r = subprocess.run(["gz", "service", "-s", f"/world/{WORLD}/set_pose", "--reqtype", "gz.msgs.Pose",
                            "--reptype", "gz.msgs.Boolean", "--timeout", "3000", "--req", req],
                           capture_output=True, text=True, env=self.gz_env, timeout=10)
        self.log(f"teleport ({x}, {y}, {z}) q={q}: {r.stdout.strip()} {r.stderr.strip()[:200]}")
        return t

    # ---------- watchers ----------
    def watcher_cmd(self, *extra, name="watcher", sysid=211, fc_port=None, mocap_port=None, box=BOX, deps=True,
                    identity="off", fc_params="require"):
        out = os.path.join(self.out, name)
        cmd = [VENV_PY, "-m", "realflight.watcher.mocap_watch", out,
               "--fc", f"udpin:127.0.0.1:{fc_port or P['watcher_fc']}", "--sysid", str(sysid),
               "--mocap-port", str(mocap_port or P["mocap"]), "--body-name", "thesis_quad", "--body-id", "1",
               f"--box={box}", "--identity", identity, "--fc-params", fc_params]
        if deps:
            cmd += ["--dep", "flow_tracker", "--dep", "flow_bridge", "--liveness-port", str(P["live"])]
        return cmd + list(extra)

    def start_watcher(self, *extra, **kw):
        name = kw.get("name", "watcher")
        self.stop(name, signal.SIGKILL, 3)
        return self.spawn(name, self.watcher_cmd(*extra, **kw))

    def watch_file(self, name="watcher"):
        try:
            f = open(os.path.join(self.out, name, "watch_heartbeat")).read().split()
            return time.time() - float(f[0]), dict(kv.split("=", 1) for kv in f[1:])
        except (OSError, ValueError, IndexError):
            return None, {}

    def confirmed(self, name="watcher"):
        age, fl = self.watch_file(name)
        return age is not None and age < 3 and fl.get("box") == "1" and fl.get("bridge") == "1"

    # ---------- controls ----------
    def fwd(self, dest=0, **kw):
        import json
        kw["dest"] = dest
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        t = time.time()
        s.sendto(json.dumps(kw).encode(), ("127.0.0.1", P["fwd_ctl"]))
        s.close()
        return t

    def relay(self, cmd):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        t = time.time()
        s.sendto(cmd.encode(), ("127.0.0.1", P["relay_ctl"]))
        s.close()
        return t


class RC:
    """The SITL 'transmitter': 16 x uint16 PWM to SITL's RC UDP port, re-sent at 10 Hz."""

    def __init__(self, log):
        self.ch = [1500] * 16
        self.ch[2] = 1000          # throttle low (GUIDED arming needs it neutral/low; the pilot centres it (1500)
                                   # before taking ALT_HOLD/STABILIZE in B10)
        self.ch[4] = 1555          # mode switch: GUIDED
        self.ch[5] = self.ch[6] = self.ch[7] = 1000   # aux switches low (no aux function at mid)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.log = log
        self.run = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.run:
            self.sock.sendto(struct.pack("<16H", *self.ch), ("127.0.0.1", P["rc"]))
            time.sleep(0.1)

    def set(self, **chans):
        for k, v in chans.items():
            self.ch[int(k[2:]) - 1] = v
        self.sock.sendto(struct.pack("<16H", *self.ch), ("127.0.0.1", P["rc"]))
        t = time.time()
        self.log(f"RC set {chans}")
        return t


class Operator:
    """The bench operator's own MAVLink link (SITL SERIAL2, system ID 255 like MAVProxy; it sends no HEARTBEAT,
    RC override or MANUAL_CONTROL). A reader thread logs every FC HEARTBEAT transition, STATUSTEXT and the
    SYSTEM_TIME clock map."""

    def __init__(self, out, log):
        self.log = log
        self.m = mavutil.mavlink_connection(f"udpin:127.0.0.1:{P['op']}", source_system=255, source_component=191)
        self.ev = open(os.path.join(out, "op_events.csv"), "a", buffering=1)
        self.st = open(os.path.join(out, "op_systime.csv"), "a", buffering=1)
        self.armed = None
        self.mode = None
        self.params = {}
        self.acks = []
        self.texts = []
        self.lock = threading.Lock()
        self.run = True
        self.last_hb = 0
        self.origins = []         # (wall, lat_e7, lon_e7, alt_mm) of every GPS_GLOBAL_ORIGIN from the FC
        threading.Thread(target=self._loop, daemon=True).start()
        threading.Thread(target=self._streams, daemon=True).start()

    def note(self, kind, text):
        self.ev.write(f"{time.time():.4f},{kind},\"{text}\"\n")

    def _streams(self):
        while self.run:
            try:
                self.m.mav.command_long_send(1, 1, M.MAV_CMD_SET_MESSAGE_INTERVAL, 0, M.MAVLINK_MSG_ID_SYSTEM_TIME,
                                             100000, 0, 0, 0, 0, 0)
            except OSError:
                pass
            time.sleep(3)

    def _loop(self):
        while self.run:
            try:
                msg = self.m.recv_match(blocking=True, timeout=0.5)
            except Exception as e:  # noqa: BLE001
                self.note("ERR", repr(e)); continue
            if msg is None:
                continue
            t = time.time()
            ty = msg.get_type()
            src = msg.get_srcSystem()
            if ty == "SYSTEM_TIME" and src == 1:
                self.st.write(f"{t:.4f},{msg.time_boot_ms}\n")
            elif ty == "HEARTBEAT" and src == 1 and msg.type != M.MAV_TYPE_GCS:
                armed = bool(msg.base_mode & M.MAV_MODE_FLAG_SAFETY_ARMED)
                self.last_hb = t
                if armed != self.armed or msg.custom_mode != self.mode:
                    self.note("HB", f"armed={int(armed)} mode={msg.custom_mode}")
                self.armed, self.mode = armed, msg.custom_mode
            elif ty == "STATUSTEXT":
                self.note("TEXT", f"src{src}: {msg.text}")
                with self.lock:
                    self.texts.append((t, src, msg.text))
            elif ty == "PARAM_VALUE":
                n = msg.param_id if isinstance(msg.param_id, str) else msg.param_id.decode()
                self.params[n.rstrip("\0")] = (msg.param_value, t)
            elif ty == "GPS_GLOBAL_ORIGIN" and src == 1:
                self.note("ORIGIN", f"lat={msg.latitude} lon={msg.longitude} alt={msg.altitude}")
                with self.lock:
                    self.origins.append((t, msg.latitude, msg.longitude, msg.altitude))
            elif ty == "COMMAND_ACK" and src == 1:
                self.note("ACK", f"cmd={msg.command} result={msg.result}")
                with self.lock:
                    self.acks.append((t, msg.command, msg.result))

    def texts_since(self, t0):
        with self.lock:
            return [x for x in self.texts if x[0] >= t0]

    def param_set(self, name, value, cap=10):
        t0 = time.time()
        while time.time() - t0 < cap:
            self.m.mav.param_set_send(1, 1, name.encode(), float(value), M.MAV_PARAM_TYPE_REAL32)
            t1 = time.time()
            while time.time() - t1 < 1.5:
                v = self.params.get(name)
                if v and v[1] >= t1 and abs(v[0] - value) < 1e-3:
                    self.note("PARAM", f"{name}={value}")
                    self.log(f"param {name} = {value} (read back)")
                    return t1
                time.sleep(0.05)
        raise RuntimeError(f"param {name} not set to {value}")

    def param_get(self, name, cap=6):
        t1 = time.time()
        while time.time() - t1 < cap:
            self.m.mav.param_request_read_send(1, 1, name.encode(), -1)
            t2 = time.time()
            while time.time() - t2 < 1.0:
                v = self.params.get(name)
                if v and v[1] >= t1:
                    return v[0]
                time.sleep(0.05)
        raise RuntimeError(f"param {name} not read")

    def cmd(self, command, *p, wait_ack=3.0):
        p = list(p) + [0] * (7 - len(p))
        t0 = time.time()
        self.m.mav.command_long_send(1, 1, command, 0, *p)
        while time.time() - t0 < wait_ack:
            with self.lock:
                for a in self.acks:
                    if a[0] >= t0 and a[1] == command:
                        return t0, a[2]
            time.sleep(0.02)
        return t0, None

    def arm(self, force=False):
        self.note("OP", f"arm request force={force}")
        return self.cmd(M.MAV_CMD_COMPONENT_ARM_DISARM, 1, 2989 if force else 0)

    def disarm(self):
        self.note("OP", "disarm request (forced)")
        return self.cmd(M.MAV_CMD_COMPONENT_ARM_DISARM, 0, 21196)

    def set_mode(self, mode):
        self.note("OP", f"set mode {mode}")
        return self.cmd(M.MAV_CMD_DO_SET_MODE, M.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, mode)

    def reboot(self):
        self.note("OP", "reboot")
        self.m.mav.command_long_send(1, 1, M.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN, 0, 1, 0, 0, 0, 0, 0, 0)
        return time.time()

    def wait(self, what, cond, cap, alive=None):
        t0 = time.time()
        while time.time() - t0 < cap:
            if alive and not alive():
                raise RuntimeError(f"stack died while waiting for {what}")
            if cond():
                return time.time()
            time.sleep(0.05)
        return None


def tail_has(path, pattern, since_bytes=0):
    try:
        with open(path) as f:
            f.seek(since_bytes)
            return re.search(pattern, f.read()) is not None
    except OSError:
        return False
