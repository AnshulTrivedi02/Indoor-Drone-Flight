#!/usr/bin/env python3
"""Experiment O: the GNSS samples EKF3 received, for the UKF/FGO replays (identical measurements) and the scorer.
Reads the trial's dataflash GPS + GPA (and XKFS for EKF3's origin), and the bag's /imu/time_ref for the SITL -> bag
clock map (lower envelope, as eval/ground_test_check.py).
  * kept: samples with Status >= 3 (3D fix). SITL keeps sending the TRUE position with NO_FIX while disabled
    (SIM_GPS.cpp:516), so the status filter is what removes them; EKF3 does the same (Measurements.cpp:570);
  * time: EKF3's measurement time = GPA.SMS - 120 ms (driver lag, M8) - 6 ms (half a filter step)
    (AP_NavEKF3_Measurements.cpp:590-597), mapped to the bag clock. The UKF and FGO use exactly this time;
  * position: lat/lon -> world ENU about SITL home (SIM_OPOS: the Gazebo origin; North = Gazebo +y, East = +x);
  * velocity: Spd, GCrs -> (vE, vN) (the GPS log carries no VN/VE);
  * EKF3 origin: the GPS sample at the rising edge of XKFS.GPS_GTA (core 0), as world (E, N), for XKF1 -> world.
Writes ~/thesis_data/trials/<trial>/gnss.npz. Usage (venv-tags): python3 eval/extract_gnss.py TRIAL"""
import math, os, sys
import numpy as np
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

LAG_S, HALF_STEP_S = 0.120, 0.006
LATLON_TO_M = 0.011131884502145034                        # m per 1e-7 degree (ArduPilot)
TR_ = sys.argv[1]; D = os.path.expanduser(f"~/thesis_data/trials/{TR_}")


def ll_to_en(lat, lon, lat0, lon0):
    # AP Location::get_distance_NE: dN = dlat * LATLON_TO_M, dE = dlon * LATLON_TO_M * cos(lat0-scale)
    k = LATLON_TO_M * 1e7                                     # AP_Common/Location.h constant (m per degree)
    return (lon - lon0) * k * math.cos(math.radians((lat + lat0) / 2)), (lat - lat0) * k


m = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); gps = {}; gpa = {}; par = {}; gta = []
while True:
    r = m.recv_match(type=["GPS", "GPA", "XKFS", "PARM"])
    if r is None: break
    ty = r.get_type()
    if ty == "PARM": par[r.Name] = r.Value
    elif ty == "GPS" and getattr(r, "I", 0) == 0: gps[r.TimeUS] = (r.Status, r.Lat, r.Lng, r.Spd, r.GCrs, r.VZ)
    elif ty == "GPA" and getattr(r, "I", 0) == 0: gpa[r.TimeUS] = (r.SMS, r.HAcc, r.SAcc)
    elif ty == "XKFS" and r.C == 0: gta.append((r.TimeUS, r.GPS_GTA))
lat0 = par.get("SIM_OPOS_LAT", -35.363261); lon0 = par.get("SIM_OPOS_LNG", 149.165230)
rows = []
for tu, (st, lat, lng, spd, crs, vz) in sorted(gps.items()):
    if tu not in gpa: continue
    sms, hacc, sacc = gpa[tu]
    E, N = ll_to_en(lat, lng, lat0, lon0)
    c = math.radians(crs)
    rows.append((sms / 1e3 - LAG_S - HALF_STEP_S, st, E, N, spd * math.sin(c), spd * math.cos(c), hacc, sacc, tu / 1e6))
A = np.array(rows)
# clock map SITL -> bag
ts = get_typestore(Stores.ROS2_JAZZY); TR = []
with Reader(f"{D}/bag") as rd:
    cs = [c for c in rd.connections if c.topic == "/imu/time_ref"]
    for con, _, raw in rd.messages(connections=cs):
        mm = ts.deserialize_cdr(raw, con.msgtype)
        TR.append((mm.time_ref.sec + mm.time_ref.nanosec * 1e-9, mm.header.stamp.sec + mm.header.stamp.nanosec * 1e-9))
TR = np.array(TR); sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
to_bag = lambda x: x + (kk * x + c0)
ok = A[:, 1] >= 3
# EKF3 origin: GPS sample nearest the first XKFS.GPS_GTA rising edge
gta = np.array(gta); i_r = np.argmax(gta[:, 1] > 0) if (gta[:, 1] > 0).any() else None
origin = None
if i_r is not None:
    j = np.argmin(np.abs(A[:, 8] - gta[i_r, 0] / 1e6)); origin = (A[j, 2], A[j, 3])
np.savez(f"{D}/gnss.npz", t=to_bag(A[ok, 0]), E=A[ok, 2], N=A[ok, 3], vE=A[ok, 4], vN=A[ok, 5], hacc=A[ok, 6], sacc=A[ok, 7],
         t_all=to_bag(A[:, 0]), status_all=A[:, 1], ekf3_origin_EN=np.array(origin if origin else (np.nan, np.nan)),
         clock_rate_ppm=1e6 * kk)
print(f"{TR_}: {ok.sum()}/{len(A)} samples with 3D fix; outage(s) at bag t "
      f"{[round(float(x), 1) for x in to_bag(A[1:, 0][np.diff(ok.astype(int)) != 0])]}; EKF3 origin (E, N) {origin}; "
      f"HAcc {np.unique(A[ok, 6])[:3]} SAcc {np.unique(A[ok, 7])[:3]}")
