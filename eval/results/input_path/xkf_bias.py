import json, math
import numpy as np
from pymavlink import DFReader
f = DFReader.DFReader_binary("/home/makerspace/thesis_data/trials/H_s1_r1/ardupilot.bin")
rows = []
for m in iter(lambda: f.recv_match(type="XKF1"), None):
    if m.C == 0:
        rows.append((m.TimeUS * 1e-6, m.GX, m.GY, m.GZ))
r = np.array(rows)
w = (r[:, 0] > 60) & (r[:, 0] < r[-1, 0] - 30)
st = json.load(open("/home/makerspace/thesis_data/trials/H_s1_r1/apin/extract_stats.json"))
print("XKF1 core0 gyro bias (deg/s) airborne mean", r[w, 1:].mean(0), "-> mrad/s", np.radians(r[w, 1:].mean(0)) * 1e3)
print("XKF1 bias range x,y mrad/s", np.radians(r[w, 1].min()) * 1e3, np.radians(r[w, 1].max()) * 1e3, np.radians(r[w, 2].min()) * 1e3, np.radians(r[w, 2].max()) * 1e3)
print("ROFH-bag offset (FLU x,y) mrad/s", np.array(st["flow"]["derot_gyro_rofh_minus_bag_frame_avg"]["mean_rad_s"]) * 1e3)
