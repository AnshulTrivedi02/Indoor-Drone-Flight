#!/usr/bin/env python3
"""Two result figures (existing data, n=3 per condition):
A) ATE and cross-track error by condition, showing the 3 repeats + mean/range.
B) EKF along-track estimate (XKF1 PN) vs true y, all 9 trials.
Condition palette matches the committed plots (blue/orange/gray)."""
import os, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pymavlink import mavutil

COND=[("textured",["ds_tex_r1","ds_tex_r2","ds_tex_r3"],"#2c7fb8"),
      ("transition",["ds_trans_r1","ds_trans_r2","ds_trans_r3"],"#d95f0e"),
      ("blank",["ds_blank_r1","ds_blank_r2","ds_blank_r3"],"#636363")]
OUT="/tmp/claude-1000/-home-makerspace/49a84f21-951f-48f9-9d24-12f0efc66b9a/scratchpad"
plt.rcParams.update({'axes.grid':True,'grid.alpha':0.25,'axes.axisbelow':True,
                     'axes.spines.top':False,'axes.spines.right':False,'font.size':11})

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
    tN=np.interp(t,sim['t']/1e6,sN); tE=np.interp(t,sim['t']/1e6,sE)
    dt=np.gradient(t); spd=np.convolve(np.hypot(np.gradient(tN)/dt,np.gradient(tE)/dt),np.ones(25)/25,mode='same')
    cr=spd>0.30; bi=bj=0; i=0
    while i<len(cr):
        if cr[i]:
            j=i
            while j<len(cr) and cr[j]: j+=1
            if j-i>bj-bi: bi,bj=i,j
            i=j
        else: i+=1
    i0=max(bi,int(np.argmax((np.abs(xk['PN'])+np.abs(xk['PE']))>0.05))); i1=bj; w=slice(i0,i1)
    dpn=xk['PN'][w]-xk['PN'][i0]; dpe=xk['PE'][w]-xk['PE'][i0]
    dtn=tN[w]-tN[i0]; dte=tE[w]-tE[i0]
    ate=float(np.sqrt(np.mean((dpn-dtn)**2+(dpe-dte)**2)))
    xtrack=abs(float((dpe-dte)[-1]))
    return dict(ate=ate,xtrack=xtrack, y=tN[w]-tN[i0], pn=dpn)   # pn,y referenced to engage

D={tr:load(tr) for _,ts,_ in COND for tr in ts}

# ---------- Figure A: ATE & cross-track by condition ----------
fig,axes=plt.subplots(1,2,figsize=(11,5.2))
for ax,metric,title in [(axes[0],'ate','ATE (m)'),(axes[1],'xtrack','cross-track error (m)')]:
    for xi,(name,ts,col) in enumerate(COND):
        vals=[D[tr][metric] for tr in ts]
        xs=xi+np.linspace(-0.09,0.09,3)
        ax.scatter(xs,vals,s=70,color=col,edgecolor='k',lw=0.6,zorder=5)
        ax.hlines(np.mean(vals),xi-0.22,xi+0.22,color=col,lw=2.5,zorder=4)
        ax.vlines(xi,min(vals),max(vals),color=col,lw=1.2,alpha=0.6)
        ax.annotate(f"mean {np.mean(vals):.1f}\nrange {max(vals)-min(vals):.1f}",
                    (xi,min(vals)),textcoords="offset points",xytext=(0,-10),
                    ha='center',va='top',fontsize=8.5,color='#333')
    ax.set_xticks(range(len(COND))); ax.set_xticklabels([c[0] for c in COND])
    ax.set_ylabel(title); ax.set_ylim(bottom=0, top=max(max(D[tr][metric] for tr in ts) for _,ts,_ in COND)*1.12)
    ax.margins(x=0.12)
axes[0].set_title("ATE separates the conditions (~68 m)")
axes[1].set_title("cross-track overlaps (noisy channel)")
fig.suptitle("Noise floor: 3 identical repeats per condition (n=3), points = repeats, bar = mean",fontsize=12)
fig.tight_layout(); fig.savefig(f"{OUT}/ate_by_condition.png",dpi=200); plt.close(fig)

# ---------- Figure B: along-track PN vs true y ----------
fig,ax=plt.subplots(figsize=(9,6))
ax.plot([0,150],[0,150],'k--',lw=1,alpha=0.5,label="PN = true y (ideal)")
ax.axvline(80,color='gray',ls=':',lw=1); ax.text(81,5,"y = 80 m\nboundary",fontsize=8,color='gray')
seen=set()
for name,ts,col in COND:
    for tr in ts:
        lbl=name if name not in seen else None; seen.add(name)
        ax.plot(D[tr]['y'],D[tr]['pn'],color=col,lw=1.6,alpha=0.9,label=lbl)
ax.set_xlabel("true along-track position, y (m)"); ax.set_ylabel("EKF along-track estimate, XKF1 PN (m)")
ax.set_xlim(0,150); ax.set_ylim(-5,165); ax.legend(loc="upper left")
ax.set_title("EKF along-track estimate vs true position — all 9 trials (n=3 per condition)")
fig.tight_layout(); fig.savefig(f"{OUT}/pn_vs_truey.png",dpi=200); plt.close(fig)
print("wrote ate_by_condition.png and pn_vs_truey.png")
for name,ts,_ in COND:
    print(f"  {name:11}: ATE={[round(D[tr]['ate'],1) for tr in ts]}  xtrack={[round(D[tr]['xtrack'],1) for tr in ts]}")
