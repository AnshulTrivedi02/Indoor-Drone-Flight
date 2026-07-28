#!/usr/bin/env python3
"""Plots 1 & 2 from nomag_corridor_baseline .BIN (plotting only, no re-analysis)."""
import math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymavlink import mavutil

BIN=os.path.expanduser("~/thesis_data/trials/nomag_corridor_baseline/ardupilot.bin")
OUT=os.path.expanduser("~/thesis_ws/plots")
os.makedirs(OUT, exist_ok=True)
TRIAL="nomag_corridor_baseline"

m=mavutil.mavlink_connection(BIN)
xk={k:[] for k in("t","PN","PE","Yaw")}; sim={k:[] for k in("t","Lat","Lng","Yaw")}
while True:
    msg=m.recv_match(type=["XKF1","SIM"])
    if msg is None: break
    T=msg.get_type()
    if T=="XKF1" and getattr(msg,"C",0)==0:
        xk["t"].append(msg.TimeUS);xk["PN"].append(msg.PN);xk["PE"].append(msg.PE);xk["Yaw"].append(msg.Yaw)
    elif T=="SIM":
        sim["t"].append(msg.TimeUS);sim["Lat"].append(msg.Lat);sim["Lng"].append(msg.Lng);sim["Yaw"].append(msg.Yaw)
for d in (xk,sim):
    for k in d: d[k]=np.asarray(d[k],float)
t=xk["t"]
lat=sim["Lat"].copy(); lng=sim["Lng"].copy()
if abs(lat).max()>1000: lat/=1e7; lng/=1e7
R=6378137.0; la0=math.radians(lat.mean())
sN=np.radians(lat-lat[0])*R; sE=np.radians(lng-lng[0])*R*math.cos(la0)
tN=np.interp(t,sim["t"],sN); tE=np.interp(t,sim["t"],sE)
# aided window (EKF pos leaves 0 within true cruise)
dt=np.gradient(t)/1e6; spd=np.convolve(np.hypot(np.gradient(tN)/dt,np.gradient(tE)/dt),np.ones(25)/25,mode="same")
cr=spd>0.30; bi=bj=0; i=0
while i<len(cr):
    if cr[i]:
        j=i
        while j<len(cr) and cr[j]: j+=1
        if j-i>bj-bi: bi,bj=i,j
        i=j
    else: i+=1
i0=max(bi,int(np.argmax((np.abs(xk["PN"])+np.abs(xk["PE"]))>0.05))); i1=bj
w=slice(i0,i1)

# ---- Plot 1: top-down trajectory ----
gE=tE[w]-tE[i0]; gN=tN[w]-tN[i0]; eE=xk["PE"][w]-xk["PE"][i0]; eN=xk["PN"][w]-xk["PN"][i0]
sep=math.hypot(eE[-1]-gE[-1], eN[-1]-gN[-1])
fig,ax=plt.subplots(figsize=(6.5,8))
ax.plot(gE,gN,color="#2c7fb8",lw=2.5,label="Ground truth (SIM)")
ax.plot(eE,eN,color="#d95f0e",lw=2.5,label="EKF3 estimate (XKF1)")
ax.scatter([0],[0],c="k",s=70,zorder=5,label="Start")
ax.scatter([gE[-1]],[gN[-1]],c="#2c7fb8",marker="s",s=60,zorder=5)
ax.scatter([eE[-1]],[eN[-1]],c="#d95f0e",marker="s",s=60,zorder=5)
ax.plot([gE[-1],eE[-1]],[gN[-1],eN[-1]],"k--",lw=1.2,alpha=0.7)
ax.annotate(f"end-point separation\n{sep:.1f} m",
            xy=((gE[-1]+eE[-1])/2,(gN[-1]+eN[-1])/2), xytext=(eE[-1]+3,eN[-1]-18),
            fontsize=10, ha="left",
            arrowprops=dict(arrowstyle="->",color="k",lw=1))
ax.set_xlabel("East (m)"); ax.set_ylabel("North / along-corridor (m)")
ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.legend(loc="upper left")
ax.set_title(f"Top-down trajectory: GT vs EKF3\n{TRIAL}  (n=1)")
fig.tight_layout(); fig.savefig(f"{OUT}/nomag_trajectory.png",dpi=200); plt.close(fig)

# ---- Plot 2: yaw error vs time ----
simYaw=np.degrees(np.interp(t,sim["t"],np.unwrap(np.radians(sim["Yaw"]))))
off=((xk["Yaw"]-simYaw+180)%360)-180
tw=(t[w]-t[i0])/1e6; ow=off[w]
A=np.polyfit(tw,ow,1)  # deg/s
fig,ax=plt.subplots(figsize=(9,5))
ax.plot(tw,ow,color="#d95f0e",lw=1.8,label="XKF1 yaw − GT yaw")
ax.plot(tw,np.polyval(A,tw),"k--",lw=1.5,
        label=f"fitted drift {A[0]*60:+.2f} deg/min")
ax.axhline(0,color="gray",lw=0.8)
ax.set_xlabel("time since aiding engaged (s)"); ax.set_ylabel("yaw error (deg)")
ax.grid(alpha=0.3); ax.legend(loc="upper left")
ax.set_title(f"Yaw error vs time (no yaw source)\n{TRIAL}  (n=1)")
ax.annotate(f"drift {A[0]*60:+.2f} deg/min\ntotal {ow[-1]-ow[0]:+.1f} deg over {tw[-1]:.0f}s",
            xy=(tw[-1],ow[-1]), xytext=(tw[-1]*0.55,ow.max()*0.5),
            fontsize=10, arrowprops=dict(arrowstyle="->",color="k"))
fig.tight_layout(); fig.savefig(f"{OUT}/nomag_yaw_error.png",dpi=200); plt.close(fig)

print("wrote:")
print(f"  {OUT}/nomag_trajectory.png   (end-sep {sep:.1f} m)")
print(f"  {OUT}/nomag_yaw_error.png    (drift {A[0]*60:+.2f} deg/min)")
