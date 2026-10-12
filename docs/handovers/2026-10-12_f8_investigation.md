# Handover 2026-10-12: F8 investigation (EKF3 pre-arm velocity runaway; B10b second EKF failsafe)

**Stage:** the bounded F8 investigation, METHODOLOGY RULINGS 2026-10-12 item 3. Time box 2 h. LOGS ONLY: no SITL run,
no parameter change, no data modified. METHODOLOGY.md was not edited.

**Branch:** `worktree-agent-a4e051dd89b04d979`, based on `fwd-camera` `0c2bd8a`. Not merged.

**Source:** ArduPilot pinned `~/ardupilot` `7bac20cbcc`. The binary that ran is the same build: every session's boot
`MSG` reads "ArduCopter V4.8.0-dev (7bac20cb)". All file:line citations below are at that commit.

**Data:** `~/thesis_data/wbench/wbench*_*/dataflash/*.BIN`, read with pymavlink. Truth is the Gazebo pose in each
session's `forwarder.csv`, using only rows with dest 1, mode normal and the vehicle's own body.
- Truth x is East and y is North (ENU).
- FC time F is mapped to wall time W from the FC events in each session's `analysis/` timelines, good to tens of ms.

## 1. Summary

| finding | cause | verdict | SITL artefact or real? | rung-1 risk |
|---|---|---|---|---|
| **F8** (EKF3 velocity runs away on the ground before arming) | Flow drops out on the final descent, so the velocity error at touchdown is the error EKF3 already had. On the ground the flow innovation gate locks that axis out, and the other axis keeps every fallback switched off. A ~0.9° roll error then ramps the velocity. | **CONFIRMED** (chain §2.1–2.6). The roll-error ramp is **likely** (it matches g·sin(roll) to 5 %). The take-off lurch is **likely, not established** (§2.8). | **Real mechanism.** The gate lock-out and the disabled fallbacks are stock EKF3 logic, and none of it depends on SITL. The SITL parts are the trigger and its size: the flow dropout near the floor, and the camera sitting 5.5 cm below the floor at rest. | **Moderate on a re-arm after a landing in the same boot** (the card's battery change per sortie probably power-cycles the FC, §5); low on the first arm of a boot. In ALT_HOLD/STABILIZE nothing controls horizontal velocity, so there is no lurch. But a LAND-mode touchdown can feed F2, and the logged estimate is corrupted. |
| **F2** (no land detection / tip-over in LAND) | It follows from F8. LAND's horizontal controller leans hard against the phantom ground velocity, so the land detector's "large angle request" stays true. | **CONFIRMED** in the 2 cases checked (§3) | Real mechanism, same as F8 | **Real for any LAND-mode touchdown** (rung 1's abort default) |
| **B10b second EKF failsafe** | In ALT_HOLD with nobody correcting, the vehicle drifted off the 20 × 20 m textured mat (x < −10 m). The LiDAR lost the floor (Known Issue #6), so HORIZ_POS_REL was lost. | **CONFIRMED** (§4) | **SITL world artefact.** Flow re-acquisition worked correctly. | None from this mechanism. On hardware the analogue is leaving the rangefinder's surface. |

## 2. F8: the mechanism, step by step (B6b run 1, `wbench2_hoverB_20261012_114206`, F 44–62 s)

Figure: `docs/figures/f8/f8_b6b_prearm.png`, with four panels:
- EKF VE on both cores against the true East velocity;
- XKF5.NI against the gate;
- the OF rows;
- the rangefinder and HAGL.

### 2.1 The flow drops out on the final descent, so the velocity error is in place before touchdown

- B5b-noflag's LAND descended from 1.5 m.
- Below a rangefinder reading of about 0.5 m, the FC received almost no `OPTICAL_FLOW`. The OF rows stop from F 47.0 to 49.85 s, with one row at 47.5.
  - `flow_tracker.py` publishes "invalid" when fewer than 20 features are tracked.
  - `flow_bridge.py` drops invalid messages (`flow_bridge.py:123-124`).
  - **Confirmed from the session's `flow_tracker_real.log`:** tracked features fell 38 → 22 → 13 → 6 → 2–3 over
    W 779.7–782.8 (F ≈ 46.4–49.5), then "Tracked features = 0", while the camera height (HAGL − 0.25) fell from
    about 0.55 m to about 0.1 m. The few frames that passed carried wild raw flow (800–3000 px/s).
  - At touchdown the tracker reported 164 features with zero flow. The camera is then below the floor plane, a SITL
    view.
- So `flowDataValid` lapsed after 1 s (`AP_NavEKF3_OptFlowFusion.cpp:40`), and HORIZ_POS_REL was lost from 48.5 s.
- Then came "EKF variance: position lost" / "EKF Failsafe" at 49.611 (`ekf_check.cpp:79-87`). That was the first EKF failsafe, logged in the rerun handover.
- In the meantime the truth drifted West at about −0.55 m/s, while EKF3 had VE ≈ −0.03 to −0.11.

**Prevalence:** 24 of the 47 touchdowns in the hover sessions had a flow gap of ≥ 1 s in the 5 s before. This is confounded: several tests kill the flow on purpose.

**Real sensors:** they also have a minimum working range, for example around 8 cm for a PMW3901-class sensor; that figure is from memory, not checked. Whether a real one drops out this high is unknown.

### 2.2 EKF3 integrates the touchdown impulse correctly; the phantom velocity is the pre-existing error

- At F 49.93 the IMU logs AccY +21.5 m/s² (IMU0) and +26.5 m/s² (IMU1): the ground stopping the West drift.
- Core 0 VE went from −0.027 to +0.56 m/s. That matches the pre-touchdown estimate plus the true Δv (−0.03 + 0.55 ≈ +0.52).
- **The error after touchdown (+0.56 m/s against a true 0) is the error EKF3 carried into the touchdown.**
- Core 1 went to +0.91 m/s. That is about 0.36 m/s more than the true Δv, which fits its larger logged spike. The difference between the IMUs is not explained (observation only).

### 2.3 On the ground, flow is a near-perfect velocity measurement, so the innovation gate locks the axis out

**The prediction.**
- The flow prediction is v / r (`AP_NavEKF3_OptFlowFusion.cpp:298-317,334-335`).
- r = max(HAGL, `rngOnGnd`) / cos(tilt) − FLOW_POS_Z, where `rngOnGnd` = max(RNGFND1_GNDCLR, 0.05) (`AP_NavEKF3_Measurements.cpp:29`).
- Note that the `rngOnGnd` clamp is applied BEFORE the lever-arm subtraction.

**The bench values.**
- HAGL = 0.21, GNDCLR = 0.10 and FLOW_POS_Z = 0.25 give r ≈ −0.04 m.
- Measured from the log, r = VE / (FIX/1000) = −0.034 to −0.039 m at F 50.2–53.5 (`figures.py` prints this).
- **The negative sign is a SITL geometry artefact.** The camera is 0.25 m below a body origin that sits 0.195 m above the floor, so it is 5.5 cm below the floor at rest.
- The sign does NOT drive the lock-out.

**The gate.**
- The test ratio is ν² / ((0.01·EK3_FLOW_I_GATE)² · S) (`:665`).
- With zero measured flow it is about v² / (9·(P_v + R_LOS·r²)), which does not depend on the sign of r.
- At |r| = 0.04 m, R_LOS·r² ≈ 1e-4 (m/s)². At 1.2 m it is ≈ 0.09 (m/s)².
- **So on the ground any velocity error beyond about 3σ of the EKF's own velocity variance is rejected (`:668`).** A real vehicle with a small positive r of a few cm gets the same effect.

**What the log shows.**
- XKF5.NI was 255 from F 50.0.
- FIX (East axis) was −13 to −30 rad/s.
- `FIX` is `int16(1000·innovation)` (`AP_NavEKF3_Logging.cpp:198`), so it wraps beyond ±32.767 rad/s. **The sign flip after F ≈ 54 s is that wrap, not physics.**

### 2.4 The other flow axis keeps every fallback switched off

- **The North (Y) axis kept being fused.**
  - FIY was about −1.7 rad/s for the first ~0.3 s after touchdown, then small from about F 50.5.
  - The direct evidence: core 0 VN was pulled from −0.059 (F 50.0) to 0.003 m/s by F 51.0 and held at 0.00–0.02 m/s over F 51–58, while VE ramped.
  - Each accepted axis refreshes `prevFlowFuseTime_ms` (`OptFlowFusion.cpp:668-670`).
- **The aiding fallback never fired.** EKF3 drops to AID_NONE only after 5 s with no accepted flow (`AP_NavEKF3_Control.cpp:304-316`). That never happened in the 9 s lock-out: there was no "stopped aiding" message and HORIZ_POS_REL stayed set. This is consistent with Y being accepted (XKF5.NI logs only the larger of the two ratios).
- **The zero-velocity pseudo-measurement was suppressed.** EKF3 fuses a stationary zero velocity on the ground only when no flow has been accepted in the last 1 s (`AP_NavEKF3_PosVelFusion.cpp:710-731`).
  - The ground condition was met: XKFM.OGNM = 1 from F 51.9, apart from the carry at 52.5–52.8.
  - But no NE velocity was fused at all: XKF3.IVN/IVE = 0 and XKF4.SV = 0.00 throughout F 50–59.
  - **This is exactly the case that code exists to prevent, defeated here by the per-axis acceptance.**
- **No arming check looks at this.**
  - EKF3's `pre_arm_check` tests the horizontal velocity innovation only in AID_ABSOLUTE with GPS velocity (`AP_NavEKF3_Outputs.cpp:40-57`).
  - The Copter EKF check uses variances (SV ≤ 0.06 against FS_EKF_THRESH 0.8) and position availability (`ekf_check.cpp:52-54`).
  - Both passed, so the FC armed at VE 1.46 (core 0) and 1.70 m/s (core 1).

### 2.5 A roll error ramps the unaided axis (likely)

- From F 50.5 to 58.4, VE rose at 0.145 m/s².
- The EKF roll was +0.90° (mean). The IMU AccY was −0.001 m/s², so the vehicle was level.
- g·sin(0.90°) = 0.153 m/s², which matches to 5 %.
- Nothing corrects the roll, because the only East-observing measurement is gated.
- **Classed as likely, not confirmed**: the roll error itself is not compared with a truth attitude.

### 2.6 The gate re-opens by variance growth, which is the "reset at take-off"

- Unaided, P_v grows, so the test ratio falls: NI went 255 → 152 at arming → < 100 at about F 58.9.
- Flow fusion then snapped the state back: VE 1.89 → 0.41 m/s and PE 10.6 → 5.7 m.
- **The "estimate reset at take-off" in the rerun handover is this gate re-opening, not a reset.**

### 2.7 Candidate causes ruled out

| candidate | verdict | evidence |
|---|---|---|
| Flow fused on the ground with the camera too close (defocus, zero flow against non-zero IMU) | **Partly, re-cast.** Near the floor the flow DROPS OUT (§2.1); on the ground it reads exactly zero (truth is zero). The fault is the gate (§2.3), not wrong flow. | OF rows; FIX/VE |
| Takeoff/ground flags, `EK3_FLOW_USE` | **Not the cause.** On the ground the flow is zeroed only when `!takeOffDetected` (`OptFlowFusion.cpp:48-52`), which is correct here, because truth is zero. `takeOffDetected` resets only when disarmed (`AP_NavEKF3_VehicleStatus.cpp:466-480`); `onGround` = disarmed for Copter (`:376-384`). `EK3_FLOW_USE` = 1, as filed. | XKF4.SS takeoff_detected bit |
| Origin set mid-initialisation | **Ruled out.** The ORGN records are from F ≈ 4.8 s. The onset is at the touchdown (49.93 s), with no origin event. | ORGN rows |
| Ground-effect compensation | **Ruled out.** `takeoff_expected`/`touchdown_expected` only change baro handling (`PosVelFusion.cpp:1103-1110`), and the height source is the rangefinder. | parameters |
| IMU bias learning | **Ruled out.** XKF2 accel bias stays 0 (XY inhibited on the ground, `AP_NavEKF3_core.cpp:1170-1185`). The XKF1 gyro bias is constant. | XKF1/XKF2 |
| SITL physics on the ground | **Contributes only through the trigger.** The touchdown impulse is physical and integrated correctly (§2.2). The carry (`set_pose` teleport) at F 52.4 left the ramp unchanged. | figure |
| The carry/teleport as the onset | **Ruled out for all 5 cases.** Each onset is at the preceding touchdown (§2.9). | timelines |

### 2.8 The 2.08 m take-off excursion (likely, not established)

- GUIDED take-off controls horizontal VELOCITY toward zero (`ArduCopter/takeoff.cpp:183-190`), not a stored position.
- **Counter-example:** a large position snap BEFORE lift-off produces no lurch. In `114206`, the arm at F 257.69 was followed by an 8 m PE snap at 259.0–259.5, lift-off (EV NOT_LANDED) at 260.8, and an excursion of 0.04 m.
- **In the B6b case the re-capture (58.9) straddled lift-off (EV 28 at 59.57).** The climb then crossed the low-height zone where flow drops out again or is gated (OF gap 60.3–61.0; NI 255). The EKF and true East velocities both rose to about 1.1–1.3 m/s.
- An untested, SITL-only candidate: for the first ~4 cm of climb r < 0 (the camera is still below the floor), so any accepted non-zero flow pushes the velocity the wrong way.
- The exact controller interaction is not resolved within the time box. **Conclusion: the lurch needs a velocity or attitude state error at lift-off, so it needs a position or velocity-controlled take-off. STABILIZE/ALT_HOLD take-offs have no horizontal velocity control.**

### 2.9 Prevalence (`docs/figures/f8/scan.csv`, all hover sessions except the aborted F7 session `112751`)

- **46 arms:** 5 had EKF |Vh| > 0.3 m/s on either core at arming. All 5 were re-arms after a landing in the same boot. Their onsets are at the preceding touchdown, never the carry:
  - `114206` F 56.43: 1.46/1.70 m/s;
  - `114206` F 193.85: 0.65/1.15 m/s;
  - `114206` F 257.69: 1.71/2.07 m/s;
  - `125941` F 88.22: 0.26/0.36 m/s;
  - `125941` F 209.16: 1.03/1.19 m/s.
- **0 of 10 first arms after boot** had any (max 0.001 m/s).
- **Only 1 of the 5 produced a take-off excursion > 0.15 m.** The others re-captured at or before lift-off.
- **47 touchdowns** (anchored on EV LAND_COMPLETE_MAYBE):
  - 17 had ≥ 3 s of flow-gate lock-out (NI ≥ 100) in the next 10 s;
  - 20 reached an EKF |Vh| ≥ 0.5 m/s on the ground within 10 s.
- **F8 is therefore NOT n = 1.** It is the common outcome of a landing, and it reaches the arming only when the vehicle is re-armed before the gate re-opens (the bench re-arms 4–6 s after the disarm).
- **These are SITL rates.** On the bench, r passes through zero in the last few cm of descent and stays negative on the ground, so every bench landing sits in the near-zero-r regime. The real frequency is unknown. It will depend on the real sensor's dropout height and on the velocity error at touchdown.

## 3. F2 follows from F8 (CONFIRMED in the 2 cases checked; `f2_check.py`)

**The land detector requires all of the following (`ArduCopter/land_detector.cpp:113-116,145`):**
- no roll/pitch TARGET above 15° (`LAND_CHECK_LARGE_ANGLE_RAD`);
- no angle error above 30°;
- throttle at its lower limit.

**B6b run 2's LAND (`114206`, F 76.5–80.6)** was an operator disarm, "land detector did not trip":
- after touchdown, EKF VN ran −0.73 → −1.54 m/s on the ground;
- LAND's horizontal controller demanded DesPitch −9.5 → −28.3° and DesRoll −6.5 → −17.9°, with ThO 0;
- the actual attitude stayed about 1° (on the ground);
- `large_angle_request` was therefore true throughout, so there was no land detection.

**The tip-over (`wbench_hoverB_20261011_125941`, B9b, F 260.5–269.5):**
- after touchdown, EKF VN ran −0.60 → −2.08 m/s;
- DesPitch went to the −30° limit with ThO 0;
- the pitch rocked (−5 to −11°), then the vehicle tipped (−64°);
- "Crash: Disarming: AngErr=34>30".

**On a real vehicle the mechanism is the same.** The existing F2 rule (the pilot disarms after any automatic LAND if the FC does not) stays the primary mitigation, and the F8 mitigations reduce how often it is needed.

## 4. B10b second EKF failsafe (`wbench2_hoverC_20261012_114843`, F 115–146 s)

Figure: `docs/figures/f8/f8_b10b_second_fs.png`.

- **World:** the session ran `iris_textured.sdf` (`gz.log`). Its `textured_ground` (20 × 20 m at the origin, `sim/models/textured_ground/model.sdf:10`) is the only ground geometry, which is Known Issue #6.
- **The drift.** In ALT_HOLD with the sticks centred and no pilot correction, the vehicle drifted from (0.4, 2.1) to (−16.6, 13.1) m over about 27 s, reaching about 2 m/s.
  - The drift was under way before the flow kill (0.15 m/s at F 116–120).
  - This is reported as an observation, with no mechanism claimed.
- **The flow restore worked.**
  - Flow was restored at F 135.6; "EKF3 IMU0/1 started relative aiding" and "fusing optical flow" came at 136.158.
  - The failsafe cleared at 137.126.
  - EKF3 then tracked the true velocity (F 138: EKF VN 0.68 / VE −1.35 against a true ≈ +0.64 / −1.45 m/s).
  - **The re-acquisition candidate (reset handling, gate re-open) is ruled out.**
- **The rangefinder lost the floor.**
  - True x crossed −10 m at F 138.35.
  - RFND fell to 0 / no data from 138.68 ("PreArm: Rangefinder 1: No Data" at 146.825).
  - HORIZ_POS_REL and TERRAIN_ALT (`gndOffsetValid`) cleared about 138.9.
  - Ten failed 10 Hz checks later came "EKF Failsafe" at 140.025 (`ekf_check.cpp:79-87`). The "position lost" text was rate-limited (`:85`).
- **No mode change followed** (ALT_HOLD does not require a position, `ekf_check.cpp:190`). The pilot's LAND switch came at 140.65.
- **Verdict:** a SITL world artefact. The rung-1 analogue is flying beyond the rangefinder's valid surface, which the volume and fence bound.

## 5. Rung-1 risk (EKF3 flying, pilot-flown in ALT_HOLD/STABILIZE, origin set)

1. **First arm of a boot: low.** No case was seen in 10 first arms. The EKF has not yet been through a touchdown.
2. **A re-arm after a landing in the same boot: moderate, but conditional on the procedure.**
   - The card flies one take-off per sortie and changes the battery between sorties (§5, §7 "before the next battery").
   - If the FC is powered from the flight battery, every sortie starts from a fresh boot, so M1 below already holds in practice. That is to be confirmed for the real power wiring.
   - The residual exposure is a second take-off within one sortie: after an abort-landing, a bounced landing or a "land and go again", without a power-cycle.
   - In that case, a take-off can start with a phantom velocity and position of 1–2 m/s and several metres. In ALT_HOLD/STABILIZE that does not command motion.
   - It does corrupt the logged EKF3 estimate for scoring, until the gate re-opens: about 6–10 s after the touchdown, or later.
   - It can also trip the EKF failsafe check, though here it did not.
3. **Any touchdown in LAND mode, the abort default: real F2 risk.** On the ground the phantom velocity makes LAND demand up to 30° of lean, so there is no land detection and the vehicle can tip over.
4. **Hypothesis, untested:** the rung-1 card's disarmed "sync wiggle" (hand-held, > 2 rad/s), followed by setting the vehicle down, could leave a velocity error that the ground gate then locks in, as at a touchdown. Check it in the props-off hand-carried pass (Card §3) by reading XKF1 VN/VE after the set-down.

## 6. Proposed mitigations (PROPOSALS ONLY; nothing applied)

Flight card / procedure:
- **M1 (strongest, cheap): reboot the FC (or power-cycle) after every landing before re-arming.** Every runaway seen followed a landing in the same boot; 0 of 10 first arms showed it.
  - This interacts with the origin ruling: the origin must be re-set and verified after each boot, as Card B6 already requires.
- **M2: a pre-arm EKF velocity check, on the card AND as a watcher arming check alongside F7.**
  - Refuse arming unless `LOCAL_POSITION_NED` |(vx, vy)| < 0.2 m/s (proposed) for N = 5 s, while mocap shows the vehicle stationary.
  - `LOCAL_POSITION_NED` reports the primary core only, so "both cores" cannot be checked live. Core 0 alone exceeded 0.2 m/s in all 5 cases (the lowest was 0.26), so a primary-only check would still have caught every one.
  - `EKF_STATUS_REPORT` carries no flow-innovation ratio. Its velocity variance is the SV that stayed 0.00 throughout the runaway, which is exactly why FS_EKF passed, so it cannot be used for this check.
  - The card version: GS reads the ground-station velocity (from `LOCAL_POSITION_NED`) after set-down and before arming.
- **M3: land in ALT_HOLD (pilot throttle-down, then disarm) rather than LAND where safe.** LAND is still the abort default. After any LAND touchdown, the SP disarms within 2 s of touchdown (this tightens the F2 rule from 4 s).
- **M4: state explicitly that U4 (take off within 5 s of arming) does NOT address F8.** The bad velocity exists BEFORE arming, so a quick take-off can make things worse by lifting off before the gate re-opens.

Parameters (for discussion; each changes the rung-1 configuration and needs its own ruling and bench test):
- **P1: RNGFND1_GNDCLR and FLOW_POS_Z must be the measured real values.**
  - The real camera is above the floor, so r > 0. The near-zero-r gate sharpness remains.
  - Note for the simulation only: FLOW_POS_Z 0.25 with the camera below the floor makes r < 0 on the ground.
- **P2: EK3_FLOW_I_GATE.** A larger gate re-opens sooner, but it is a global change to the estimator under test. Not recommended for the comparison.
- **No EKF3 parameter switches off the stationary-zero-velocity suppression** (`PosVelFusion.cpp:723`, the `!haveRecentFlowVel` condition); that would need a code change. It is noted here as a possible upstream issue: the per-axis flow acceptance suppresses zero-velocity fusion while one axis is locked out.

## 7. What was not done / open

- The take-off lurch mechanism (§2.8) is not resolved: why the B6b climb's EKF and true velocities both went East.
- Core 1's larger touchdown step (§2.2) is not explained.
- The roll error is not checked against a truth attitude (forwarder.csv has positions only).
- The sync-wiggle hypothesis (§5.4) is untested.
- No SITL runs were made, by the stage constraint. A confirming bench test would land, wait 15 s (past the re-open), then re-arm, against re-arming at 4 s, as the evidence for M1/M2.

## 8. Files

All new; no existing file was modified.
- `realflight/sitl_bench/f8/dump_df.py`: dumps one dataflash log to a pickle.
- `realflight/sitl_bench/f8/dump_all.py`: dumps every session's log.
- `realflight/sitl_bench/f8/timeline.py`: binned EKF/flow/range timeline.
- `realflight/sitl_bench/f8/fine.py`: raw merged rows.
- `realflight/sitl_bench/f8/scan.py`: the per-arm and per-touchdown prevalence table.
- `realflight/sitl_bench/f8/figures.py`: the two figures and the numeric checks.
- `realflight/sitl_bench/f8/f2_check.py`: attitude demand on the ground.
- `docs/figures/f8/f8_b6b_prearm.png`, `docs/figures/f8/f8_b10b_second_fs.png`, `docs/figures/f8/scan.csv`.

Reproduce (in `~/venv-ardupilot`): `python realflight/sitl_bench/f8/dump_all.py <dir>`, then run `scan.py`, `figures.py`
and `f2_check.py` on `<dir>`. The pickles are not committed.
