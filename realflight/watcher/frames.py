"""Mocap frame handling.

The watcher works in ONE frame, the "watch frame": right-handed, z UP, metres. The box (--box) is given in it.
The rigid body's own axes are assumed FLU (x forward, y left, z up) once converted; a fixed yaw offset can be
applied if the mocap asset was created with a different forward axis (--body-yaw-offset-deg).

Supported mocap world conventions (HARDWARE-DEPENDENT, to be confirmed at bench test B6 by hand-rolling and
hand-pitching the vehicle and comparing with the FC's ATTITUDE):
  'z'  z-up, right-handed (e.g. Vicon's default). Identity.
  'y'  y-up, right-handed (e.g. OptiTrack Motive's default). A = Rx(+90 deg): (x, y, z) -> (x, -z, y).
       Both the world and the body axes are converted (R' = A R A^T), because a Motive asset's local axes are
       defined in the same y-up convention when it is created.

Euler angles are returned in the FC's convention (ArduPilot ATTITUDE: FRD body, NED-like z-down world):
  with R_flu = Rz(yaw) Ry(pitch) Rx(roll) (ZYX), flipping both frames about x (F = diag(1,-1,-1)) gives
  F Rz(y) Ry(p) Rx(r) F = Rz(-y) Ry(-p) Rx(r), so roll_frd = roll_flu, pitch_frd = -pitch_flu, yaw_frd = -yaw_flu.
  The mocap yaw has an arbitrary offset to the FC's yaw (no compass), so only yaw CHANGES are compared.
"""
import math

import numpy as np

_A = {
    "z": np.eye(3),
    "y": np.array([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]]),
}


def quat_to_rot(qw, qx, qy, qz):
    n = math.sqrt(qw * qw + qx * qx + qy * qy + qz * qz)
    if n < 1e-9:
        raise ValueError("zero quaternion")
    w, x, y, z = qw / n, qx / n, qy / n, qz / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ])


class FrameConverter:
    def __init__(self, up_axis="z", body_yaw_offset_deg=0.0):
        if up_axis not in _A:
            raise ValueError(f"up_axis must be one of {sorted(_A)}")
        self.A = _A[up_axis]
        c, s = math.cos(math.radians(body_yaw_offset_deg)), math.sin(math.radians(body_yaw_offset_deg))
        self.B = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])   # body-frame correction (right-multiplied)

    def convert(self, pos, quat):
        """pos (x,y,z), quat (w,x,y,z) in the mocap frame -> (p_watch ndarray(3), R_watch ndarray(3,3) body->watch)."""
        p = self.A @ np.asarray(pos, dtype=float)
        R = self.A @ quat_to_rot(*quat) @ self.A.T @ self.B
        return p, R


def tilt_deg(R):
    """Angle between the body z axis and the world z axis (copied in spirit from wall_watch.py's tilt rule)."""
    return math.degrees(math.acos(max(-1.0, min(1.0, R[2, 2]))))


def euler_frd(R):
    """(roll, pitch, yaw) in radians, FC (FRD) convention, from a z-up body(FLU)->world rotation."""
    roll = math.atan2(R[2, 1], R[2, 2])
    pitch = -math.asin(max(-1.0, min(1.0, -R[2, 0])))   # -pitch_flu
    yaw = -math.atan2(R[1, 0], R[0, 0])
    return roll, pitch, yaw


def wrap_pi(a):
    return (a + math.pi) % (2 * math.pi) - math.pi
