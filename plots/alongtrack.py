#!/usr/bin/env python3
"""(a) final PN vs true travel, all 9 trials grouped by condition -> plot.
(b) where along-track PN growth flattens in each transition repeat (sim time,
    true y), vs the y=80 m boundary, and transition sharpness. Numbers only."""
import os, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymavlink import mavutil

COND={"textured":["ds_tex_r1","ds_tex_r2","ds_tex_r3"],
      "blank":["ds_blank_r1","ds_blank_r2","ds_blank_r3"],
      "transition":["ds_trans_r1","ds_trans_r2","ds_trans_r3"]}
CCOL={"textured":"#2c7fb8","blank":"#636363","transition":"#d95f0e"}
OUT="/tmp/claude-1000/-home-makerspace/49a84f21-951f-48f9-9d24-12f0efc66b9a/scratchpad"

def load(trial):
    m=mavutil.mavlink_connection(os.path.expanduser(f"~/thesis_data/trials/{trial}/ardupilot.bin"))
    xk={'t':[],'PN':[],'PE':[]}; sim={'t':[],'Lat':[],'Lng':[]}
    while True:
        x=m.recv_match(type=['XKF1','SIM'])
        if x is None: break
        T=x.get_type()
        if T=='XKF1' and getattr(x,'C',0)==0:
            xk['t'].append(x.TimeUS);xk['PN'].append(x.PN);xk['PE'].append(x.PE)
        elif T=='SIM':
            sim['t'].append(x.TimeUS);sim['Lat'].append(x.Lat);sim['Lng'].append(x.Lng)
    for d in (xk,sim):
        for k in d: d[k]=np.asarray(d[k],float)
    t=xk['t']/1e6
    lat=sim['Lat'].copy(); lng=sim['Lng'].copy()
    if abs(lat).max()>1000: lat/=1e7; lng/=1e7
    R=6378137.0; la0=math.radians(lat.mean())
    sN=np.radians(lat-lat[0])*R; sE=np.radians(lng-lng[0])*R*math.cos(la0)
    trueN=np.interp(t,sim['t']/1e6,sN); trueE=np.interp(t,sim['t']/1e6,sE)
    return t, xk['PN'], xk['PE'], trueN, trueE

# ---- (a) final PN vs true travel, all 9 ----
pts={}
for cond,trials in COND.items():
    pts[cond]=[]
    for tr in trials:
        t,PN,PE,tN,tE=load(tr)
        # aided-window bounds (true cruise)
        dt=np.gradient(t); spd=np.convolve(np.hypot(np.gradient(tN)/dt,np.gradient(tE)/dt),np.ones(25)/25,mode='same')
        cr=spd>0.30; bi=bj=0; i=0
        while i<len(cr):
            if cr[i]:
                j=i
                while j<len(cr) and cr[j]: j+=1
                if j-i>bj-bi: bi,bj=i,j
                i=j
            else: i+=1
        i0=max(bi,int(np.argmax((np.abs(PN)+np.abs(PE))>0.05))); i1=bj
        travel=math.hypot(tN[i1-1]-tN[i0], tE[i1-1]-tE[i0])
        pts[cond].append((travel, float(PN[i1-1])))
fig,ax=plt.subplots(figsize=(7.5,6.5))
lim=160; ax.plot([0,lim],[0,lim],'k--',lw=1,alpha=0.6,label="PN = true travel (ideal)")
ax.axhline(80,color='gray',ls=':',lw=1,alpha=0.7); ax.text(4,82,"y = 80 m boundary",fontsize=8,color='gray')
for cond in COND:
    xs=[p[0] for p in pts[cond]]; ys=[p[1] for p in pts[cond]]
    ax.scatter(xs,ys,s=90,color=CCOL[cond],label=f"{cond} (n=3)",edgecolor='k',zorder=5)
ax.set_xlabel("true travel (m)"); ax.set_ylabel("final EKF along-track estimate, XKF1 PN (m)")
ax.set_xlim(140,156); ax.set_ylim(-5,165); ax.grid(alpha=0.3); ax.legend(loc="center right")
ax.set_title("Final along-track estimate vs true travel — all 9 trials (n=3 per condition)")
fig.tight_layout(); fig.savefig(f"{OUT}/alongtrack_vs_travel.png",dpi=200); plt.close(fig)
print("wrote alongtrack_vs_travel.png")

# ---- (b) transition PN-flatten point ----
print("\n=== corridor_transition: where along-track PN growth flattens ===")
print(f"{'trial':12} {'t_flat(s)':>10} {'true_y@flat(m)':>15} {'PN@flat(m)':>11} {'y-80(m)':>9} {'sharpness Δy(m)':>16}")
ys_flat=[]
for tr in COND["transition"]:
    t,PN,PE,tN,tE=load(tr)
    dt=np.gradient(t); vPN=np.convolve(np.gradient(PN)/dt,np.ones(41)/41,mode='same')
    # cruise established when vPN>0.3; flatten = last index in that cruise where vPN>0.25
    cruise=np.where(vPN>0.30)[0]
    if len(cruise)==0: print(f"{tr:12}  (no cruise detected)"); continue
    c0=cruise[0]
    # first index after c0 where vPN drops below 0.15 and stays low
    idx=None
    for k in range(c0,len(vPN)-5):
        if vPN[k]<0.15 and np.median(vPN[k:k+10])<0.15:
            idx=k; break
    if idx is None: idx=cruise[-1]
    t_flat=t[idx]; y_flat=tN[idx]; pn_flat=PN[idx]
    # sharpness: LOCAL drop width around the flatten point — walk backward to the
    # last y where vPN was still >0.4 (tracking), forward to first vPN<0.1 (frozen)
    hi=idx
    while hi>c0 and vPN[hi]<0.40: hi-=1
    lo=idx
    while lo<len(vPN)-1 and vPN[lo]>0.10: lo+=1
    sharp=abs(tN[lo]-tN[hi])
    ys_flat.append(y_flat)
    print(f"{tr:12} {t_flat:10.1f} {y_flat:15.1f} {pn_flat:11.1f} {y_flat-80:9.1f} {sharp:16.1f}")
if ys_flat:
    print(f"\ntrue_y@flatten across 3: mean={np.mean(ys_flat):.1f}  min={min(ys_flat):.1f}  max={max(ys_flat):.1f}  range={max(ys_flat)-min(ys_flat):.1f} m")
