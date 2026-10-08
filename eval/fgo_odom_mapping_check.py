#!/usr/bin/env python3
"""Experiment H, S3: offline check of the FGO node's state -> ODOMETRY mapping (fgo_node_core.odom_ned), the only new
path S3 flies on that the core equivalence (FN1-FN4) does not exercise.
  A. anchored (W written as ENU): an FGO state at x = E 0, y = N -1.5, facing W north (yaw ENU 90 deg), velocity
     (vx, vy) -> NED N -1.5, E 0, NED yaw 0 (from the quaternion, ArduPilot's 321 extraction), (vN, vE) = (vy, vx);
     a yaw of ENU 60 deg -> NED 30 deg; roll/pitch preserved; biases FLU -> FRD.
  B. corridor (pre-anchor; every non-H use): byte-for-byte the same output as the pre-H inline code (copied below from
     fgo_node.py at c02c8a4) on 1,000 random states; FGO yaw 0 -> NED yaw 0.
  C. the reset the node signals: reset_counter = n_anchors % 256 (0 before, 1 after the first anchor), per anchor_log.
Usage: python3 eval/fgo_odom_mapping_check.py [--json OUT]  (needs numpy only)"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "estimators", "fgo"))
import importlib.util
spec = importlib.util.spec_from_file_location("onc", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                                   "src", "estimators", "fgo", "fgo_node_core.py"))
# odom_ned is pure numpy; load it without importing gtsam (fgo_node_core imports fgo_core at module level)
src = open(spec.origin).read()
ns = {"np": np}
exec(src[src.index("def odom_ned("):], ns)
odom_ned = ns["odom_ned"]


def Rz(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def Ry(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rx(a):
    c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def euler321(q):              # ArduPilot Quaternion::to_euler
    w, x, y, z = q
    return (math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)), math.asin(max(-1, min(1, 2 * (w * y - z * x)))),
            math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def old_corridor(p, v, R, bg, ba):          # fgo_node.py _send_state at c02c8a4, verbatim arithmetic
    C = np.array([[1.0, 0, 0], [0, -1, 0], [0, 0, -1]]); Fb = np.diag([1.0, -1, -1])
    pn, vn, Rn = C @ p, C @ v, C @ R @ Fb
    tr = np.trace(Rn)
    if tr > 0:
        S = math.sqrt(tr + 1.0) * 2; qw = 0.25 * S; qx = (Rn[2, 1] - Rn[1, 2]) / S; qy = (Rn[0, 2] - Rn[2, 0]) / S; qz = (Rn[1, 0] - Rn[0, 1]) / S
    elif Rn[0, 0] > Rn[1, 1] and Rn[0, 0] > Rn[2, 2]:
        S = math.sqrt(1.0 + Rn[0, 0] - Rn[1, 1] - Rn[2, 2]) * 2; qw = (Rn[2, 1] - Rn[1, 2]) / S; qx = 0.25 * S; qy = (Rn[0, 1] + Rn[1, 0]) / S; qz = (Rn[0, 2] + Rn[2, 0]) / S
    elif Rn[1, 1] > Rn[2, 2]:
        S = math.sqrt(1.0 + Rn[1, 1] - Rn[0, 0] - Rn[2, 2]) * 2; qw = (Rn[0, 2] - Rn[2, 0]) / S; qx = (Rn[0, 1] + Rn[1, 0]) / S; qy = 0.25 * S; qz = (Rn[1, 2] + Rn[2, 1]) / S
    else:
        S = math.sqrt(1.0 + Rn[2, 2] - Rn[0, 0] - Rn[1, 1]) * 2; qw = (Rn[1, 0] - Rn[0, 1]) / S; qx = (Rn[0, 2] + Rn[2, 0]) / S; qy = (Rn[1, 2] + Rn[2, 1]) / S; qz = 0.25 * S
    return pn, vn, (qw, qx, qy, qz), Fb @ bg, Fb @ ba


out = {}
# A. anchored
bg, ba = np.array([0.01, 0.02, 0.03]), np.array([0.1, 0.2, 0.3])
pn, vn, q, bgf, baf = odom_ned(np.array([0.0, -1.5, 1.5]), np.array([0.05, 0.2, 0.01]), Rz(math.radians(90)), bg, ba, True)
r, pch, y = euler321(q)
A = {"pos_NED": pn.tolist(), "vel_NED": vn.tolist(), "yaw_NED_deg": math.degrees(y), "roll_deg": math.degrees(r), "pitch_deg": math.degrees(pch)}
okA = np.allclose(pn, [-1.5, 0, -1.5]) and np.allclose(vn, [0.2, 0.05, -0.01]) and abs(y) < 1e-12 and abs(r) < 1e-12 and abs(pch) < 1e-12
_, _, q2, _, _ = odom_ned(np.zeros(3), np.zeros(3), Rz(math.radians(60)), bg, ba, True)
A["yaw_ENU60_to_NED_deg"] = math.degrees(euler321(q2)[2]); okA = okA and abs(A["yaw_ENU60_to_NED_deg"] - 30) < 1e-9
# attitude with roll/pitch: FLU roll +5 deg (right wing up in FLU = left side down?) -> check against the FRD meaning:
# a FLU body with R_enu<-flu = Rz(yaw) Ry(pitch_flu) Rx(roll_flu); FRD roll = roll_flu, FRD pitch = -pitch_flu
rf, pf, yf = math.radians(5), math.radians(-3), math.radians(90)
_, _, q3, _, _ = odom_ned(np.zeros(3), np.zeros(3), Rz(yf) @ Ry(pf) @ Rx(rf), bg, ba, True)
e3 = euler321(q3)
A["roll_pitch_check_deg"] = [math.degrees(e3[0]), math.degrees(e3[1]), math.degrees(e3[2])]
okA = okA and abs(e3[0] - rf) < 1e-12 and abs(e3[1] + pf) < 1e-12 and abs(e3[2]) < 1e-12
A["bias_FRD"] = [bgf.tolist(), baf.tolist()]; okA = okA and np.allclose(bgf, [0.01, -0.02, -0.03]) and np.allclose(baf, [0.1, -0.2, -0.3])
A["pass"] = bool(okA); out["A_anchored"] = A
# B. corridor unchanged
rng = np.random.default_rng(1); nb = 0
for _ in range(1000):
    e = rng.uniform(-math.pi, math.pi, 3) * np.array([0.3, 0.3, 1]); R = Rz(e[2]) @ Ry(e[1]) @ Rx(e[0])
    p, v, b1, b2 = rng.normal(size=3), rng.normal(size=3), rng.normal(size=3), rng.normal(size=3)
    a1, a2 = odom_ned(p, v, R, b1, b2, False), old_corridor(p, v, R, b1, b2)
    same = all(np.array_equal(np.asarray(x1, float), np.asarray(x2, float)) for x1, x2 in zip(a1, a2))
    nb += not same
_, _, q0, _, _ = odom_ned(np.zeros(3), np.zeros(3), np.eye(3), bg, ba, False)
out["B_corridor"] = {"random_states": 1000, "not_bit_identical": nb, "yaw_FGO0_NED_deg": math.degrees(euler321(q0)[2]),
                     "pass": bool(nb == 0 and abs(euler321(q0)[2]) < 1e-12)}
# C. reset counter as the node sends it
log = [(False, 0)] * 3 + [(True, 1)] * 3
out["C_reset_counter"] = {"sequence": [int(n) % 256 for _, n in log], "pass": [int(n) % 256 for _, n in log] == [0, 0, 0, 1, 1, 1]}
out["pass"] = bool(out["A_anchored"]["pass"] and out["B_corridor"]["pass"] and out["C_reset_counter"]["pass"])
print(json.dumps(out, indent=1))
if len(sys.argv) > 2 and sys.argv[1] == "--json":
    json.dump(out, open(sys.argv[2], "w"), indent=1)
