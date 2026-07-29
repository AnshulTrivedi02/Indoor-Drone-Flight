#!/usr/bin/env python3
"""Noise-floor report across identical-config repeats.
For each trial: flow-msg count, final PN/PE (XKF1), cross-track error, ATE
(RMSE position error XKF1-vs-SIM over the aided window). Plus mean + range.
ATE/cross-track are referenced to the aiding-engage point (origin gauge fix,
NO yaw/SE(3) alignment) — the honest dead-reckoning error.
Usage: noise_floor.py <trial_name> [<trial_name> ...]
"""
import sys, os, math, re
import numpy as np
from pymavlink import mavutil

def flow_count(trial):
    md = os.path.expanduser(f"~/thesis_data/trials/{trial}/bag/metadata.yaml")
    if not os.path.exists(md): return None
    txt = open(md).read()
    for n, c in re.findall(r'name:\s*(\S+).*?message_count:\s*(\d+)', txt, re.S):
        if n == "/optical_flow/measurement": return int(c)
    return None

def analyse(trial):
    p = os.path.expanduser(f"~/thesis_data/trials/{trial}/ardupilot.bin")
    m = mavutil.mavlink_connection(p)
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
    t=xk['t']; lat=sim['Lat'].copy(); lng=sim['Lng'].copy()
    if abs(lat).max()>1000: lat/=1e7; lng/=1e7
    R=6378137.0; la0=math.radians(lat.mean())
    sN=np.radians(lat-lat[0])*R; sE=np.radians(lng-lng[0])*R*math.cos(la0)
    tN=np.interp(t,sim['t'],sN); tE=np.interp(t,sim['t'],sE)
    dt=np.gradient(t)/1e6; spd=np.convolve(np.hypot(np.gradient(tN)/dt,np.gradient(tE)/dt),np.ones(25)/25,mode='same')
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
    err=np.hypot(dpn-dtn, dpe-dte)
    ate=float(np.sqrt(np.mean(err**2)))
    xtrack=float((dpe-dte)[-1])                 # final east deviation from truth
    along=float((dpn-dtn)[-1])                  # final north deviation
    return dict(flow=flow_count(trial),
                PN=float(xk['PN'][i1-1]), PE=float(xk['PE'][i1-1]),
                true_travel=float(math.hypot(dtn[-1],dte[-1])),
                xtrack=xtrack, along=along, ate=ate,
                win=(float(t[i0]/1e6), float(t[i1-1]/1e6)))

trials=sys.argv[1:]
rows={tr: analyse(tr) for tr in trials}
print(f"{'trial':14} {'flow':>6} {'travel':>7} {'finalPN':>8} {'finalPE':>8} {'xtrack':>8} {'ATE':>7}")
for tr in trials:
    r=rows[tr]
    print(f"{tr:14} {r['flow']!s:>6} {r['true_travel']:7.1f} {r['PN']:8.2f} {r['PE']:8.2f} {r['xtrack']:8.2f} {r['ate']:7.3f}   win[{r['win'][0]:.0f},{r['win'][1]:.0f}]s")
def stat(k):
    v=[rows[tr][k] for tr in trials if rows[tr][k] is not None]
    return (np.mean(v), min(v), max(v), max(v)-min(v)) if v else (None,)*4
print("\n--- across repeats (mean / min / max / range) ---")
for k,lab in [('flow','flow msgs'),('xtrack','cross-track err (m)'),('ate','ATE (m)'),('PE','final PE (m)'),('PN','final PN (m)')]:
    mean,mn,mx,rng=stat(k)
    if mean is not None:
        print(f"  {lab:22} mean={mean:8.3f}  min={mn:8.3f}  max={mx:8.3f}  range={rng:8.3f}")
