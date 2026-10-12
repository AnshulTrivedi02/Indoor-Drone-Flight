#!/usr/bin/env python3
"""H10 verification flight h10_guard_check: score the pre-registered criteria (docs/h10_guard_check_prereg.md) from the
flight's dataflash log (MODE records: Rsn 1 = RC_COMMAND, 2 = GCS_COMMAND; ModeReason.h), fly_trial.log and the pilot
log. Read only.

  analyse_h10.py <ardupilot.bin> <fly_trial.log> <h10_pilot.log> <out.json>
"""
import json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from df_reader import read_records  # noqa: E402

binp, ftlog, plog, out = sys.argv[1:5]
recs, info = read_records(binp, ["MODE", "ARM", "PARM", "CTUN"])
NAMES = {0: "STABILIZE", 2: "ALT_HOLD", 4: "GUIDED", 9: "LAND", 3: "AUTO", 5: "LOITER", 6: "RTL", 7: "CIRCLE"}
modes = [{"t_s": r["TimeUS"] / 1e6, "mode": NAMES.get(int(r["ModeNum"]), int(r["ModeNum"])), "num": int(r["ModeNum"]),
          "rsn": int(r["Rsn"])} for r in recs["MODE"]]
arms = [{"t_s": r["TimeUS"] / 1e6, "armed": int(r["ArmState"])} for r in recs["ARM"]]
parm = {r["Name"]: r["Value"] for r in recs["PARM"] if r["Name"] in ("FLTMODE_CH", "FLTMODE2", "FLTMODE5", "MAV_GCS_SYSID",
                                                                     "RC_OVERRIDE_TIME", "AHRS_EKF_TYPE")}
t_arm = next((a["t_s"] for a in arms if a["armed"] == 1), None)
t_dis = next((a["t_s"] for a in arms if a["armed"] == 0 and t_arm is not None and a["t_s"] > t_arm), None)
fl = [m for m in modes if t_arm is not None and m["t_s"] >= t_arm and (t_dis is None or m["t_s"] <= t_dis + 1.0)]
gcs_land = [m for m in fl if m["num"] == 9 and m["rsn"] == 2]
take = next((m for m in fl if m["num"] == 2 and m["rsn"] == 1), None)
after = [m for m in fl if take is not None and m["t_s"] > take["t_s"]]
ft = open(ftlog, errors="replace").read().splitlines()
pl = open(plog, errors="replace").read()
i_latch = next((i for i, s in enumerate(ft) if "H10: the pilot took ALT_HOLD" in s), None)
i_guard = next((i for i, s in enumerate(ft) if "H10 guard: the pilot took ALT_HOLD -> NOT commanding LAND" in s), None)
landing_lines = [i for i, s in enumerate(ft) if "Landing (wall-clock cap" in s]
lat = re.search(r"FC shows ALT_HOLD, ([0-9.]+) s after the switch move", pl)
sw = re.search(r"mode switch -> position 5 \(ALT_HOLD\), throttle centred, ([0-9.]+) s after LAND", pl)
hold = re.search(r"position 2 \(LAND\) after a ([0-9.]+) s hold", pl)
res = {"modes_in_flight": fl, "arm_s": t_arm, "disarm_s": t_dis, "parm": parm,
       "reader": {k: info[k] for k in ("undeclared_types", "skipped_bytes")},
       "pilot": {"switch_after_land_s": float(sw.group(1)) if sw else None,
                 "althold_seen_after_switch_s": float(lat.group(1)) if lat else None,
                 "hold_wall_s": float(hold.group(1)) if hold else None},
       "fly_trial": {"landing_lines": landing_lines, "latch_line": i_latch, "guard_line": i_guard,
                     "lines_after_latch": ft[i_latch:] if i_latch is not None else None}}
c = {}
c["void_fltmode5"] = parm.get("FLTMODE5") != 2.0
c["1_one_gcs_land"] = len(gcs_land) == 1
c["2_takeover_rc_althold_within_1s"] = take is not None and lat is not None and float(lat.group(1)) <= 1.0
nxt = after[0] if after else None
c["3a_no_mode_record_until_pilot_land"] = nxt is not None and nxt["num"] == 9 and nxt["rsn"] == 1
c["3b_hold_sim_s"] = (nxt["t_s"] - take["t_s"]) if (nxt and take) else None
c["3c_fly_trial_no_landing_after_latch"] = i_latch is not None and all(i < i_latch for i in landing_lines)
c["3d_latch_and_guard_logged"] = i_latch is not None and i_guard is not None and i_guard > i_latch
c["4_pilot_land_then_disarm_only"] = (nxt is not None and nxt["num"] == 9 and nxt["rsn"] == 1 and len(after) == 1
                                      and t_dis is not None and t_dis > nxt["t_s"])
c["PASS"] = (not c["void_fltmode5"] and c["1_one_gcs_land"] and c["2_takeover_rc_althold_within_1s"]
             and c["3a_no_mode_record_until_pilot_land"] and c["3c_fly_trial_no_landing_after_latch"]
             and c["3d_latch_and_guard_logged"] and c["4_pilot_land_then_disarm_only"])
res["criteria"] = c
json.dump(res, open(out, "w"), indent=1, default=str)
print(json.dumps({"criteria": c, "modes_in_flight": fl, "parm": parm, "pilot": res["pilot"]}, indent=1, default=str))
