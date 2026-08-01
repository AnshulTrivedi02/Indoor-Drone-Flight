#!/usr/bin/env python3
"""Three diagnostic checks on EKF3's sustained east-velocity bias, dsn_tex_r3.
Diagnosis only. venv-ardupilot.
  1. asymmetric gating of lateral flow innovations
  2. yaw-velocity coupling (is errVE heading-driven, double-counting the remainder?)
  3. the t~200s regime change."""
import os, math
import numpy as np
from pymavlink import mavutil

BIN = os.path.expanduser("~/thesis_data/trials/dsn_tex_r3/ardupilot.bin")
def wrap180(a): return (a+180)%360-180

m = mavutil.mavlink_connection(BIN)
K = {t: [] for t in ['XKF1','XKF4','XKF5','SIM','IMU']}
while True:
    x = m.recv_match(type=list(K))
    if x is None: break
    T = x.get_type()
    if T.startswith('XK') and getattr(x,'C',0)!=0: continue
    if T=='IMU' and getattr(x,'I',0)!=0: continue
    K[T].append(x)
def col(msgs,*f): return np.array([[getattr(x,k) for k in f] for x in msgs],float)

t1=col(K['XKF1'],'TimeUS')[:,0]/1e6
xk1=col(K['XKF1'],'Yaw','VN','VE','PN','PE','PD')
t5=col(K['XKF5'],'TimeUS')[:,0]/1e6
xk5=col(K['XKF5'],'FIX','FIY','NI')
t4=col(K['XKF4'],'TimeUS')[:,0]/1e6; SS=col(K['XKF4'],'SS')[:,0]
ts=col(K['SIM'],'TimeUS')[:,0]/1e6
sim=col(K['SIM'],'Roll','Pitch','Yaw','Lat','Lng','Alt')
ti=col(K['IMU'],'TimeUS')[:,0]/1e6; imu=col(K['IMU'],'GyrX','GyrY','GyrZ')

lat,lng=sim[:,3].copy(),sim[:,4].copy()
if np.abs(lat).max()>1000: lat/=1e7; lng/=1e7
R=6378137.0
gN=np.radians(lat-lat[0])*R; gE=np.radians(lng-lng[0])*R*math.cos(math.radians(lat.mean()))
gVN,gVE=np.gradient(gN,ts),np.gradient(gE,ts)
gYaw=np.degrees(np.unwrap(np.radians(sim[:,2])))
gVN1=np.interp(t1,ts,gVN); gVE1=np.interp(t1,ts,gVE); gYaw1=np.interp(t1,ts,gYaw)
errVE=xk1[:,2]-gVE1; yawErr=wrap180(xk1[:,0]-gYaw1)
spd=np.hypot(gVN1,gVE1)
i0=int(np.argmax((np.abs(xk1[:,3])+np.abs(xk1[:,4]))>0.05)); t_aid=t1[i0]
cru=t1>t_aid
Tc=t1-t1[0]

print(f"=== baseline: cruise errVE mean {errVE[cru].mean():+.3f} m/s, yawErr final {yawErr[-1]:+.1f} deg ===\n")

# ---- CHECK 1: asymmetric gating ----
acc5=xk5[:,2]<100.0                       # accepted = NI<100 (combined ratio — see note)
airb=np.interp(t5,t1,np.abs(xk1[:,3])+np.abs(xk1[:,4]))>0.05
print("CHECK 1 — asymmetric gating of flow innovations (FIX=X, FIY=Y; airborne only)")
print(f"  overall reject rate: {100*(~acc5[airb]).mean():.1f}%  ({(~acc5[airb]).sum()}/{airb.sum()})")
for j,lab in ((0,'FIX'),(1,'FIY')):
    inn=xk5[airb,j]; ac=acc5[airb]
    pos=inn>0; neg=inn<0
    print(f"  {lab}: mean(ALL)={inn.mean():+.4f}  mean(ACCEPTED)={inn[ac].mean():+.4f}   "
          f"accept+={100*ac[pos].mean():.1f}%  accept-={100*ac[neg].mean():.1f}%   "
          f"(n+={pos.sum()}, n-={neg.sum()})")
print("  [NI is EKF3's combined 2-axis test ratio, not per-axis — accept flag is shared across FIX/FIY]\n")

# ---- CHECK 2: yaw-velocity coupling ----
psi_t=np.radians(gYaw1); psi_e=np.radians(gYaw1+yawErr)
vE_head=spd*(np.sin(psi_e)-np.sin(psi_t)); vE_other=errVE-vE_head
c=cru
r_ve_yaw=np.corrcoef(errVE[c],yawErr[c])[0,1]
r_other_yaw=np.corrcoef(vE_other[c],yawErr[c])[0,1]
r_head_yaw=np.corrcoef(vE_head[c],yawErr[c])[0,1]
print("CHECK 2 — yaw-velocity coupling")
print(f"  corr(errVE, yawErr)              = {r_ve_yaw:+.3f}")
print(f"  corr(vE_head, yawErr)            = {r_head_yaw:+.3f}   (heading term, by construction)")
print(f"  corr(vE_other 'remainder', yawErr)= {r_other_yaw:+.3f}   <-- if high, remainder is ALSO heading-driven")
print(f"  cruise means: errVE {errVE[c].mean():+.3f} = vE_head {vE_head[c].mean():+.3f} + vE_other {vE_other[c].mean():+.3f} m/s")
# direct magnitude: does errVE ~ spd*sin(yawErr)?
pred=spd*np.sin(np.radians(yawErr))
print(f"  slope errVE vs spd*sin(yawErr)   = {np.polyfit(pred[c],errVE[c],1)[0]:+.3f}  corr={np.corrcoef(pred[c],errVE[c])[0,1]:+.3f} (1.0 => fully heading-driven)\n")

# ---- CHECK 3: t~200s regime change ----
print("CHECK 3 — regime change around flight-time t=200s (cruise only)")
def stats(mask):
    a5=(t5>t_aid)&mask(t5-t1[0]); ai=(ti>t_aid)&mask(ti-t1[0]); a1=(t1>t_aid)&mask(Tc); asi=(ts>t1[0]+t_aid)&mask(ts-t1[0])
    return dict(rej=100*(~acc5[a5&airb[:len(a5)] if False else a5]).mean(),
                fix=np.abs(xk5[a5,0]).mean(), fiy=np.abs(xk5[a5,1]).mean(),
                alt=(-xk1[a1,5]).mean(), spd=spd[a1].mean(),
                rollamp=sim[asi,0].std(), rollrate=imu[ai,0].std(), errve=errVE[a1].mean())
before=stats(lambda T: (T>=t_aid)&(T<200)); after=stats(lambda T: T>=200)
print(f"  {'metric':22}{'before 200s':>13}{'after 200s':>12}")
for k,lab in [('errve','errVE mean (m/s)'),('rej','flow reject %'),('fix','mean|FIX|'),('fiy','mean|FIY|'),
              ('alt','altitude (m)'),('spd','GT speed (m/s)'),('rollamp','roll std (deg)'),('rollrate','roll-rate std (rad/s)')]:
    print(f"  {lab:22}{before[k]:>13.3f}{after[k]:>12.3f}")
