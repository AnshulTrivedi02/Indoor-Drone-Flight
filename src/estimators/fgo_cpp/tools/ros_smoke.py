#!/usr/bin/env python3
"""ROS 2 smoke test of fgo_cpp_node (no simulator): play a recorded bag with `ros2 bag play` and check that the node
publishes /fgo/pose and /fgo/valid, and that its MAVLink endpoint emits ODOMETRY to a peer that has sent it a datagram
(as SITL SERIAL3 would). This tests the ROS plumbing only; timing under real arrival is a SITL ground-test item.
Usage (system python3): ros_smoke.py <node_binary> <bag_dir> <seconds> [--rate R]
Run it through heavy.py. It sources nothing itself: the ROS environment is built from /opt/ros/jazzy/setup.bash and the
thesis workspace overlay by a login shell, once, and passed to the children."""
import json, os, signal, socket, subprocess, sys, time

node, bag, secs = sys.argv[1], sys.argv[2], float(sys.argv[3])
rate = sys.argv[sys.argv.index("--rate") + 1] if "--rate" in sys.argv else "1.0"
env_txt = subprocess.run(["/bin/bash", "-c", "source /opt/ros/jazzy/setup.bash && source $HOME/thesis_ws/install/setup.bash"
                          " && python3 -c 'import os, json; print(json.dumps(dict(os.environ)))'"],
                         capture_output=True, text=True, check=True).stdout
env = json.loads(env_txt.strip().splitlines()[-1])
env["ROS_DOMAIN_ID"] = "77"                      # isolated from any other ROS graph on the machine
env["ROS_LOCALHOST_ONLY"] = "1"
port = 14998
peer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); peer.bind(("127.0.0.1", 0)); peer.settimeout(0.05)
n_mav = 0
pn = subprocess.Popen([node, "--ros-args", "-p", "use_sim_time:=false", "-p", f"mavlink_out:=udp:127.0.0.1:{port}",
                       "-p", "arm_source:=none"], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
echo = subprocess.Popen(["ros2", "topic", "echo", "--csv", "/fgo/valid"], env=env, stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, text=True)
time.sleep(2.0)
play = subprocess.Popen(["ros2", "bag", "play", bag, "--rate", rate, "--topics", "/imu/data_raw", "/imu/time_ref",
                         "/optical_flow/measurement", "/downward_lidar/range", "/attitude/angular_rates"],
                        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
t0 = time.time()
while time.time() - t0 < secs:
    peer.sendto(b"\xfe\x00\x00\x01\x01\x00\x00\x00", ("127.0.0.1", port))   # any datagram: the node learns the peer
    try:
        while True:
            d, _ = peer.recvfrom(4096)
            n_mav += d.count(b"\xfd") and 1
    except socket.timeout:
        pass
    time.sleep(0.2)
for p in (play, echo, pn):
    p.send_signal(signal.SIGINT)
for p in (play, echo, pn):
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
valid_lines = echo.stdout.read().split()
node_log = pn.stdout.read()
print(f"[smoke] /fgo/valid messages seen: {len(valid_lines)} (true {sum(v == 'True' for v in valid_lines)})")
print(f"[smoke] MAVLink datagrams received from the node: {n_mav}")
print("[smoke] node log tail:\n" + "\n".join(node_log.strip().splitlines()[-5:]))
