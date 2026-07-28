#!/usr/bin/env python3
"""Plot 3: inlier_ratio vs along-corridor position, corridor_transition
(textured 0-80 m, blank 80-160 m), boundary at y=80 m. Plotting only."""
import os, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg

TRIAL="corridor_trans_verify"
BAG=os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/bag")
OUT=os.path.expanduser("~/thesis_ws/plots"); os.makedirs(OUT,exist_ok=True)
BOUND=80.0

ts=get_typestore(Stores.ROS2_JAZZY)
msgpath=[p for p in [
    os.path.expanduser("~/thesis_ws/src/optical_flow_interfaces/msg/OpticalFlow.msg")] if os.path.exists(p)]
if not msgpath:
    import glob
    msgpath=glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"),recursive=True)
ts.register(get_types_from_msg(open(msgpath[0]).read(),"optical_flow_interfaces/msg/OpticalFlow"))

def stamp(h): return h.stamp.sec + h.stamp.nanosec*1e-9
flow_t=[]; inlier=[]; valid=[]; gt_t=[]; gt_y=[]
with Reader(BAG) as r:
    conns_flow=[c for c in r.connections if c.topic=="/optical_flow/measurement"]
    conns_gt  =[c for c in r.connections if c.topic=="/ground_truth/pose"]
    for con,t,raw in r.messages(connections=conns_flow+conns_gt):
        m=ts.deserialize_cdr(raw,con.msgtype)
        if con.topic=="/optical_flow/measurement":
            flow_t.append(stamp(m.header)); inlier.append(m.inlier_ratio); valid.append(bool(m.valid))
        else:
            gt_t.append(stamp(m.header)); gt_y.append(m.pose.position.y)
flow_t=np.array(flow_t); inlier=np.array(inlier); valid=np.array(valid)
gt_t=np.array(gt_t); gt_y=np.array(gt_y)
o=np.argsort(gt_t); gt_t=gt_t[o]; gt_y=gt_y[o]
fy=np.interp(flow_t, gt_t, gt_y)   # along-corridor Y at each flow sample
print(f"{TRIAL}: {len(inlier)} flow msgs, GT y range [{gt_y.min():.1f},{gt_y.max():.1f}] m")

fig,ax=plt.subplots(figsize=(9.5,5.2))
tex=fy<=BOUND; bl=fy>BOUND
ax.axvspan(fy.min(),BOUND,color="#2c7fb8",alpha=0.07)
ax.axvspan(BOUND,fy.max(),color="#636363",alpha=0.10)
ax.scatter(fy[tex],inlier[tex],s=6,color="#2c7fb8",alpha=0.5,label="textured (y<80 m)")
ax.scatter(fy[bl], inlier[bl], s=6,color="#d95f0e",alpha=0.5,label="blank (y>80 m)")
ax.axvline(BOUND,color="k",lw=1.6,ls="--")
ax.text(BOUND+1,0.03,"texture boundary\ny = 80 m",fontsize=9,va="bottom")
# region mean overlays
for msk,c in [(tex,"#08519c"),(bl,"#a63603")]:
    if msk.sum():
        ax.hlines(np.mean(inlier[msk]),
                  fy[msk].min(),fy[msk].max(),color=c,lw=2.5,
                  label=f"mean {np.mean(inlier[msk]):.2f}")
ax.set_xlabel("along-corridor position, GT y (m)"); ax.set_ylabel("inlier_ratio (RANSAC survivors)")
ax.set_ylim(0,1.02); ax.grid(alpha=0.3); ax.legend(loc="lower left",fontsize=9)
ax.set_title(f"Optical-flow inlier_ratio vs along-corridor position\n{TRIAL}  (corridor_transition, n=1)")
fig.tight_layout(); fig.savefig(f"{OUT}/inlier_ratio_transition.png",dpi=200); plt.close(fig)
print(f"wrote {OUT}/inlier_ratio_transition.png  "
      f"(textured mean {np.mean(inlier[tex]):.2f}, blank mean {np.mean(inlier[bl]):.2f})")
