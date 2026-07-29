#!/usr/bin/env python3
"""Cross-track error and yaw error vs time for the 3 corridor_textured repeats.
Overlaid plots + spread (max-min across repeats) at sim-time 60/150/300 s.
Existing data only, no interpretation."""
import os, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymavlink import mavutil

TRIALS=["ds_tex_r1","ds_tex_r2","ds_tex_r3"]
OUT="/tmp/claude-1000/-home-makerspace/49a84f21-951f-48f9-9d24-12f0efc66b9a/scratchpad"
COL={"ds_tex_r1":"#d95f0e","ds_tex_r2":"#2c7fb8","ds_tex_r3":"#31a354"}

def wrap180(a): return (a+180)%360-180

def load(trial):
    m=mavutil.mavlink_connection(os.path.expanduser(f"~/thesis_data/trials/{trial}/ardupilot.bin"))
    xk={'t':[],'PN':[],'PE':[],'Yaw':[]}; sim={'t':[],'Lat':[],'Lng':[],'Yaw':[]}
    while True:
        x=m.recv_match(type=['XKF1','SIM'])
        if x is None: break
        T=x.get_type()
        if T=='XKF1' and getattr(x,'C',0)==0:
            xk['t'].append(x.TimeUS);xk['PN'].append(x.PN);xk['PE'].append(x.PE);xk['Yaw'].append(x.Yaw)
        elif T=='SIM':
            sim['t'].append(x.TimeUS);sim['Lat'].append(x.Lat);sim['Lng'].append(x.Lng);sim['Yaw'].append(x.Yaw)
    for d in (xk,sim):
        for k in d: d[k]=np.asarray(d[k],float)
    t=xk['t']/1e6
    lat=sim['Lat'].copy(); lng=sim['Lng'].copy()
    if abs(lat).max()>1000: lat/=1e7; lng/=1e7
    R=6378137.0; la0=math.radians(lat.mean())
    sN=np.radians(lat-lat[0])*R; sE=np.radians(lng-lng[0])*R*math.cos(la0)
    E=np.interp(t,sim['t']/1e6,sE)
    simYaw=np.degrees(np.interp(t,sim['t']/1e6,np.unwrap(np.radians(sim['Yaw']))))
    # aiding engage: EKF pos leaves 0
    i0=int(np.argmax((np.abs(xk['PN'])+np.abs(xk['PE']))>0.05))
    ct=(xk['PE']-xk['PE'][i0])-(E-E[i0])         # cross-track error vs truth
    yerr=wrap180(xk['Yaw']-simYaw)
    return t, ct, yerr

data={tr:load(tr) for tr in TRIALS}
grid=np.arange(45,331,0.5)
ct_i={tr:np.interp(grid,data[tr][0],data[tr][1]) for tr in TRIALS}
ye_i={tr:np.interp(grid,data[tr][0],data[tr][2]) for tr in TRIALS}

# spread at 60/150/300 s
print("=== cross-track error (m) per repeat + spread ===")
print(f"{'t(s)':>6} " + " ".join(f"{tr:>10}" for tr in TRIALS) + f"{'spread':>10}")
for T in (60,150,300):
    vals=[float(np.interp(T,grid,ct_i[tr])) for tr in TRIALS]
    print(f"{T:6d} " + " ".join(f"{v:10.2f}" for v in vals) + f"{max(vals)-min(vals):10.2f}")
print("\n=== yaw error (deg) per repeat + spread ===")
print(f"{'t(s)':>6} " + " ".join(f"{tr:>10}" for tr in TRIALS) + f"{'spread':>10}")
for T in (60,150,300):
    vals=[float(np.interp(T,grid,ye_i[tr])) for tr in TRIALS]
    print(f"{T:6d} " + " ".join(f"{v:10.3f}" for v in vals) + f"{max(vals)-min(vals):10.3f}")

# Plot 1: cross-track
fig,ax=plt.subplots(figsize=(9,5))
for tr in TRIALS: ax.plot(grid,ct_i[tr],color=COL[tr],lw=1.8,label=tr)
for T in (60,150,300): ax.axvline(T,color='gray',ls=':',lw=0.8)
ax.set_xlabel("sim time (s)"); ax.set_ylabel("cross-track error (m)")
ax.grid(alpha=0.3); ax.legend(); ax.set_title("Cross-track error vs time — 3 corridor_textured repeats (n=1 each, identical config)")
fig.tight_layout(); fig.savefig(f"{OUT}/textured_crosstrack.png",dpi=200); plt.close(fig)

# Plot 2: yaw error
fig,ax=plt.subplots(figsize=(9,5))
for tr in TRIALS: ax.plot(grid,ye_i[tr],color=COL[tr],lw=1.8,label=tr)
ax.axhline(0,color='gray',lw=0.8)
ax.set_xlabel("sim time (s)"); ax.set_ylabel("yaw error XKF1-SIM (deg)")
ax.grid(alpha=0.3); ax.legend(); ax.set_title("Yaw error vs time — 3 corridor_textured repeats")
fig.tight_layout(); fig.savefig(f"{OUT}/textured_yaw.png",dpi=200); plt.close(fig)
print(f"\nwrote {OUT}/textured_crosstrack.png and textured_yaw.png")
