import json
import numpy as np
S = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/home_diag/thesis_data/trials/H_s1_r1"
d = json.load(open("/home/makerspace/thesis_data/trials/H_s1_r1/../H_s1_r1/apin/extract_stats.json"))
h = json.load(open("/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/results/h_room_ukf.json"))
for v in ("room_ukf", "room_ukf_apin_biascorr"):
    z = np.load(f"{S}/{v}/live_state.npz"); t, x, dt = z["t"], z["x"], float(z["dt"])
    b = x[:, 9:12] / dt * 1e3                      # mrad/s, FLU
    w = (t > 60) & (t < t[-1] - 30)
    print(v, "airborne mean bias FLU mrad/s", b[w].mean(0).round(2))
    for L in h["losses"]:
        e = L["UKF"]["effective"]; m = (t >= e["t_last_fix"]) & (t <= e["t_first_fix"])
        print(f"   loss {e['loss_s']:.1f}s: bias x,y mean {b[m,0].mean():+.2f} {b[m,1].mean():+.2f}; vel E,N at end {x[m][-1,3]*1e3:+.1f} {x[m][-1,4]*1e3:+.1f} mm/s")
print("EKF3-implied true bias FLU (x, y) mrad/s: +2.56, -2.64 (XKF1 FRD +2.56, +2.64)")
