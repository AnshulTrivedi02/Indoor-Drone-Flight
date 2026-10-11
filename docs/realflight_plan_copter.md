# Real flights on ArduCopter: ONE consolidated plan (rung 1 and the UKF-only closed loop)

Status: PLAN, written 2026-10-12 on `fwd-camera` at `4220cc4`. It implements the ruling "RULING (user, 2026-10-12):
ArduCopter confirmed for the real vehicle (for now)" (METHODOLOGY, last entry). Nothing was flown, flashed or installed
to write it. The only build was one test of the new firmware script (§6). Handover:
`docs/handovers/2026-10-12_copter_plan.md`.

**This plan supersedes the scheduling parts** of these documents. Their technical content stands.
- `docs/minimal_real_flight_plan.md` (rung 1, 10-10). Its §6 calendar to 23 Oct is superseded by §3 here.
- `docs/ukf_only_closed_loop_costing.md` (2e, 10-11). Its §6 SITL plan is corrected in §4.2 here, and its §12 calendar
  by §4.1.
- `docs/real_flight_readiness_by_rung.md`. It is updated to match (Copter only).
- `docs/board_firmware_plan.md` (2a). Its flashing, rollback and bench checks P1–P10 stand.

**QuadPlane is DROPPED** from the active plan (supervisor, 2026-10-12). `docs/quadplane_costing.md` is kept as
**reference only**. Nothing here depends on it, and its blockers B1–B3 are not planned.

Labels:
- **[V]** verified (source, a build, a log or a stored result);
- **[E]** an estimate;
- **[U]** unknown until the hardware or a ruling arrives.

Every effort is for one person, in working days ("d"), and is [E].

---

## 0. Summary

| | **Rung 1** (logging flight) | **UKF-only closed loop** (the onboard UKF steers) |
|---|---|---|
| What flies | Stock `7bac20cbcc` (unmodified), EKF3 (`AHRS_EKF_TYPE 3`), a safety pilot in ALT_HOLD. Nothing of ours steers | The fork (`board-h743`), `AHRS_EKF_TYPE 12`, the vehicle's own flow sensor and rangefinder; EKF3 in shadow; the watcher on the ground laptop |
| From hardware arrival (Day 0) | **6 working days** (+2 contingency) | **14 working days** (+2–3 contingency), i.e. rung 1 first, then **8 more** |
| Mocap days | 3 | 3 (rung 1) + 4 = 7 |
| No-hardware work left | **~3–4.25 d** (§3.2) | **~6–9.5 d more** (§4.3) |
| Blocking open items | §5: the pre-registration sign-off, E5/merge of `rung1-geometry`, the capture-delay option, `XUKO` in Replay, compass (if none is fitted), U4 (if the rangefinder minimum exceeds the ground clearance) | everything rung 1 blocks on, plus F6, U4, the stage-3 pre-registration (with the U10 band filed before rung-1 day 3), the SITL verification flights, the own-gyro driver rule (if HereFlow/PX4Flow), the H10 takeover guard (if scripted) |

**Day 0** is the day all of these are in hand:
- the supervisor's vehicle: an STM32H743 ArduCopter, **already flying and tuned**, with its flow sensor and rangefinder on
  the FC;
- the board name;
- a mocap booking.

**If the vehicle is not already flying, add 3–6 d** (assembly, tune, hover learn: readiness A1/A2).

**Against the 23 Oct freeze** (no new information since 2026-10-10): rung 1 can finish by Fri 23 Oct only if Day 0 is
no later than Thu 15 Oct, with no contingency left. The UKF-only closed loop cannot finish by 23 Oct for any Day 0
from now. Whether flights after 23 Oct count is still the open freeze-scope question.

---

## 1. Already DONE (accounted for; nothing here needs redoing)

| item | where | state |
|---|---|---|
| **Converter** BIN → FGO inputs (R1) | `eval/bin2fgo.py`, merged into `fwd-camera` (`dde0061`) | Proof (b) PASS (byte-identical default replay); events-mode smoke PASS after the OOM fix `b9da351`. The FGO derotates with its own bias-corrected `RISI` gyro (D18) [V] |
| **Scorer** with a strict pre-registration JSON (R9) | `eval/real_score.py`, 9 tests | Matches `three_way_eval` exactly on `dsn_tex_r1`; `XKF1` must name its core (`@100` replayed, `@0` onboard) [V] |
| **Pre-registration draft** (R10) | `docs/rung1_preregistration_draft.md` + `.json` | **DRAFT, awaiting the user's sign-off** (§5 item 1) |
| **Parameter template + `check_parm.py`** (R6) | `realflight/params/` | 66 names verified at `7bac20cbcc`; refuses `AHRS_EKF_TYPE 10`, `SIM_*`, `ARMING_SKIPCHK` ≠ 0 and stale names. `TODO_SUPERVISOR` values wait on the sensors (§3.3) [V] |
| **Flight cards** (R11) | `docs/rung1_flight_cards.md` | DRAFT: bench B1–B8, hand-carried, first hover, result sortie, aborts, data-integrity D1–D9 |
| **Mocap recorder (R7) and alignment on `RISI` (R8)** | `realflight/mocap/`, `realflight/mcp1.py`, `eval/mocap_align.py` | Segment restarts; windows default to the disarmed sync wiggles; 83 `realflight` tests pass. The vendor forwarder waits on the mocap system |
| **Watcher G1–G11** | `realflight/watcher/` (`0502282`), 73 offline tests | Built for Copter: LAND = mode 9 |
| **Watcher SITL bench B0–B10** (2c) | handover `2026-10-11_watcher_sitl_bench.md` | PASS except: **B5a/B5b-noflag fail as worded** (stale 8–10 ms after a bound equal to the stale limit); **B8a VOID, not repeated**. Findings **F2, F6** (safety), F4. Stock-firmware arming without the watcher confirmed in SITL |
| **Board firmware** for H743 (2a) | `~/ardupilot_ukf` `board-h743` `0156bfc34e` (NOT merged) | MatekH743 and Pixhawk6X built with the backends: 134,692 / 267,348 B free; 0 warnings; SITL byte-identical; TFAIL arming refusal (incl. force-arm) compiled in but **untested** (bench P5) [V] |
| **Firmware build script** (this stage) | `tools/build_board_fw.sh` | One command per board; result in §6 |
| **UKF port, rung-1 geometry + D18 own-bias derotation** | `~/ardupilot_ukf` `rung1-geometry` `16535f9a29` (NOT merged, NOT installed) | (a) byte-identity PASS; (b) E1/E3 PASS, **E5 fails as worded, passes post hoc on increments**; (c) `UKF_Equiv` byte-identical [V] |
| **Corrected FGO node** (Band C, forced-gate switch) | `fgo_cpp_node` `4c07374b` INSTALLED; reproduced from `fwd-camera` | Forced Band C PASS; FGO safety `a_v4`/`b_v4` PASS (S-A3 1.45 m against 1.5 m) [V]. Not needed by either plan here; it matters for a later FGO closed loop |
| **UKF safety re-tests** on the installed port | `H_safety_ukf_a_v3`, `_b_v3` | (a) PASS; **(b) S-A2 FAILED AS WORDED** (5.69 s against 5.5 s; relay drain), recorded as such. S-A2b (from the last flow received by the FC, bound 5.5 s) is pre-registered for future tests |
| **C++ FGO on ARM64** (emulated) | 2f | Not needed by either plan here (no Pi). Pi 5 recommended for a later FGO path |

---

## 2. What waits on hardware (by input)

### 2.1 The BOARD
- **The exact hwdef build**: `tools/build_board_fw.sh <BOARD>` (fork) and `--ref 7bac20cbcc --without` (rung-1 stock).
  Each is one `heavy.py` step of a few minutes. Then re-check G2 (≥ 32 kB free) and the stack.
- **Which board decides:**
  - the flash margin (§6.2);
  - the IMU count (the multi-IMU swap question, §5 item 9);
  - whether it carries a compass (§5 item 12);
  - for KakuteH7 / -bdshot / v2, **the physical revision**: all three share `board_id` 1048, so the uploader's ID
    check cannot catch the wrong hwdef [V, the `.apj` headers].
- **Bench P1–P10** (`docs/board_firmware_plan.md` §5):
  - P5, the TFAIL arming refusal (untested; compiled out of SITL);
  - P7, the stack margin;
  - P8, CPU from `PM`;
  - P10, `MEMINFO`.
- **The FC trigger-timing bench test** (ruling 2026-10-11): the S-A2b timing on the real FC.
- **Lua on the board**, if the G6 arming-auth route (ii) is chosen.
- **Backup, rollback rehearsal** (`docs/board_firmware_plan.md` §3, §6).

### 2.2 The SENSORS (the flow sensor and rangefinder models)
- **`FLOW_TYPE`** decides the D18 path:
  - Pixart 2, CXOF 4, MAVLink 5, MSP 7, UPFLOW 8 pair the AHRS gyro: the own-bias swap applies;
  - PX4Flow 1, Bebop 3, HereFlow 6 send their own gyro: used as delivered, **ruling needed** (§5 item 8).
- **Flow parameters:** `EK3_FLOW_DELAY`, `FLOW_ORIENT_YAW`, `FLOW_POS_*`, the sensor rate.
- **Rangefinder:** type, `RNGFND1_MIN/MAX`, and `RNGFND1_GNDCLR`. **If the minimum exceeds the resting clearance**
  (e.g. a TF-Luna at 0.2 m), U4 becomes blocking (§5 item 7).
- **All `TODO_SUPERVISOR` values** in `rung1_template.parm`. Then `check_parm.py --final`.
- **Mocap IR against a ToF rangefinder or flow sensor:** a bench check inside the volume.

### 2.3 MOCAP (system, booking)
- **The system and its protocol** (OptiTrack NatNet or Vicon):
  - the vendor forwarder for R7;
  - the live client F1 for the watcher (UKF-only only);
  - the frame convention (OptiTrack streams Y-up);
  - the rotational noise (it matters for `mocap_align`).
- **The volume size:** the profile, `FENCE_ALT_MAX`, the watcher box and z_max.
- **The booking:** 3 days for rung 1, then 4 for the UKF-only closed loop (§3.1, §4.1).
- **The watcher's hardware-only tests:** B4d, the B6 hand procedure, B7a true latency, B7c alignment, the real B10c
  receiver failsafe, the audible alert.

---

## 3. Rung 1 (logging flight)

### 3.1 Timeline from Day 0 (working days; assumes §3.2 done and the vehicle already flying)

| day | work | mocap |
|---|---|---|
| 1 | Identify the board, firmware and parameters; back up parameters and firmware. Build the rung-1 image (`build_board_fw.sh <B> --ref 7bac20cbcc --without`, or flash stock 4.7.0 if S6 says so); flash; rollback rehearsal. Fill the `TODO_SUPERVISOR` values; `check_parm.py --final`; readback (eeprom gotcha). | — |
| 2 | Bench cards B1–B8 (props off): flow orientation (`OF.body*` against `flow*` signs), rangefinder on the ground and lifted, `RNGFND1_GNDCLR`, compass health (nomag), log completeness (`DSF`), fence. A disarmed bench log with sync wiggles, run through the whole offline pipeline (Replay, converter, `mocap_align`, scorer in plumbing mode) | — |
| 3 | R7 recorder test in the volume; **R13 hand-carried pass**, with the full pipeline run the SAME day (Replay-fidelity check on a non-aiding EKF3) | ✔ |
| 4 | First hovers (verification sorties V): flow aiding first exercised; the Replay-fidelity gate confirmed on a hover log; d_flow / d_range measured on verification logs, then FIXED in the pre-registration | ✔ |
| 5 | **R14 result flights**, n = 5 (+1 spare for a pre-decided exclusion); 3 over a plain sheet if S7 allows | ✔ |
| 6 | R15: Replay (EKF3 + UKF port), converter + FGO, scoring, METHODOLOGY entry. **Also the U10 Replay gate** for the UKF-only closed loop (§4) | — |
| (7–8) | Contingency: one fix-and-repeat cycle or a mocap re-booking | (✔) |

- **Total: 6 working days from Day 0, 8 with contingency; 3 mocap days.**
- **+3–6 d if the vehicle is not already flying.**
- Optional (supervisor's choice, costing §13): fly the **fork in shadow** (`AHRS_EKF_TYPE 3`, `AHRS_UKF_ENABLE 1`)
  instead of stock. That gives an onboard UKF shadow on real sensors in the same flights. It departs from "rung-1
  firmware = `7bac20cbcc` unmodified" and moves the fork bench (§4.1 day 7) before day 3. **Not the default.**

### 3.2 No-hardware TODO (do NOW: coding and paper only)

| # | item | effort | status | blocks rung 1? |
|---|---|---|---|---|
| R-a | **Pre-registration sign-off** (the user), then apply it: primary metric (evo -a SE(3) proposed), UKF record, drift segment, n, the Replay-fidelity tolerance (1 cm / 0.1°), the converter band, the timestamp rule. Mark the JSON final | 0.25 d after the ruling | DRAFT | **YES**, for result sorties (verification sorties may fly before it) |
| R-b | **Merge `rung1-geometry`** (after the E5 ruling) and **install a fork Replay built from it** (one light `heavy.py` build; re-check SITL byte-identity). The installed Replay still hard-codes the 0.12/0.25 m levers and the old derotation | 0.5 d | built in scratch, not merged | **YES** for the UKF row (EKF3 and FGO rows unaffected) |
| R-c | **Capture-delay option in the port** (prereg §6: UKF at arrival − d_cap, like the FGO converter), default unchanged; Replay regression byte-identical | 0.5–1 d | not started; needs a ruling | **YES** for the UKF row as drafted (or re-word the prereg to EKF3's flow time for the UKF) |
| R-d | **`XUKO` from a Replay run.** The prereg's proposed UKF record is `XUKO`, but Replay's logger does not emit FMT records for the UKF's messages (METHODOLOGY "Replay logging note"), and `ukf_shadow.csv` holds the horizon-time state. Check whether `XUKO` exists in a Replay output log; if not, add a current-time CSV (or re-word the prereg to `XUKF`/CSV) | 0.25–0.5 d [U] | not checked | **YES** for the UKF row as drafted |
| R-e | **U4: initialise from `RNGFND1_GNDCLR`** when disarmed and `OutOfRangeLow` (as EKF3 does), default unchanged; Replay regression | 0.5–1 d | needs a ruling | only if the rangefinder minimum exceeds the ground clearance; then the UKF row starts mid-climb |
| R-f | **Converter acceptance band** (FGO-from-BIN against FGO-from-bag, full `cl_a_tex_half`): pre-register the band, then one light replay | 0.5 d | open (R1 follow-up) | no (an acceptance check of a tool already proven at default) |
| R-g | **Flight cards:** add F2 (PROPOSED wording, the 5 s is this plan's proposal: "after any automatic LAND, the SP disarms if the FC has not disarmed within 5 s of touchdown"), a GNDCLR line, and the compass-health line for the chosen variant | 0.1 d | not done | **YES** (a safety card line; trivial) |
| R-h | R8: remove or re-validate the 25 Hz `IMU` fallback; decide whether `--init-seg` uses the motion-onset rule | 0.25 d | open | no |
| R-i | **Stale parameter names** (every parameter-like token checked against `pinned_param_names.txt`, 2026-10-12): **CLAUDE.md**: `ARMING_CHECK` → `ARMING_SKIPCHK` (Hidden Configuration Audit §2); `FLOW_MAX` → `EK3_FLOW_MAX` and `FLOW_M_NSE` → `EK3_FLOW_M_NSE` (UKF Design robustness table and text); `RNGFND1_MIN_CM` is correctly cited as the pre-rename name. **`minimal_real_flight_plan.md`** §1/§3.3: `RNGFND1_GNDCLEAR` → `RNGFND1_GNDCLR`. **`ukf_only_closed_loop_costing.md`**: `ARMING_CHECK` (§5) and `RNGFND1_GNDCLEAR`/`RNGFNDn_GNDCLEAR` (§1, §8) | 0.2 d | not done (not edited here) | no (`check_parm.py` already refuses the stale names) |
| R-j | Rung-1 firmware build ready: `build_board_fw.sh <B> --ref 7bac20cbcc --without` | 0 d | **DONE** (dry run, §6) | — |

**Total ≈ 3–4.25 d** (R-a to R-i, excluding the rulings themselves).

### 3.3 What rung 1 waits on (hardware)
- **Board:** the exact hwdef; the rung-1 image built for it; S6 (pinned or stock 4.7.0) approved; backup and rollback.
- **Sensors:** every `TODO_SUPERVISOR` value; the flow orientation and sign on the real mount (bench); `EK3_FLOW_DELAY`
  from the datasheet; the rangefinder minimum against the ground clearance (decides R-e).
- **Mocap:** the system and forwarder (R7), the volume (profile, fence), 3 booked days, a safety pilot.

---

## 4. UKF-only closed loop (the onboard UKF steering with the vehicle's own flow sensor and rangefinder)

No Pi, no camera pipeline, no FGO. Same vehicle and sensors as rung 1. The watcher runs on the ground laptop with a
live mocap feed and a MAVLink link to the FC.

### 4.1 Timeline from Day 0 (rung 1 first: the U10 Replay gate needs its logs)

| day | work | mocap |
|---|---|---|
| 1–6 | Rung 1 (§3.1). The U10 Replay gate (the fork's Replay of the onboard UKF on the rung-1 logs, pre-registered bands) runs on day 6 | 3, 4, 5 |
| 7 | Build the fork for the exact board (`build_board_fw.sh <B>`); flash; **bench P1–P10**: boot, readback, backends off = EKF3 (P4), **TFAIL refusal normal and forced (P5)**, shadow on (P6), stack (P7), CPU `PM` (P8), `MEMINFO` (P10); U4 initialisation on the ground | — |
| 8 | Bench: forced invalidity → `thesis_nav_check` → LAND (TFAIL set after arming, motors safe); **FC trigger-timing test (S-A2b)**; watcher heartbeat → FC and GCS failsafe → LAND; RC override; telemetry link worst gap (sets `FS_GCS_TIMEOUT`) | — |
| 9 | Hand-carried in the volume: UKF shadow and type 12 active (disarmed) against mocap; mocap-IR check on the sensors; watcher live on mocap (B4d, B6 hand procedure, B7a, B7c) | ✔ |
| 10 | Tethered: EKF3 hover first, then **UKF flying** hovers; forced invalidity and flow occlusion on the tether; check that the land detector trips (F2) | ✔ |
| 11 | Buffer / fixes (a firmware fix means a reflash and repeating day 7's readback) | — |
| 12–13 | Free flights, UKF flying: a hover first, then the pre-registered profile, n = 3–5 | ✔ ✔ |
| 14 | Scoring (`real_score.py`), METHODOLOGY entry | — |
| (15–17) | Contingency: a fix-and-reflash cycle, or a mocap re-booking | (✔) |

- **Total: 14 working days from Day 0 (8 after rung 1), 16–17 with contingency; 7 mocap days in all (4 after rung 1).**
- **+3–6 d if the vehicle is not already flying.**
- With the fork-in-shadow option of §3.1, day 7's bench moves before rung 1's day 3 and the rung-1 flights give an
  onboard shadow; that saves about 1 d.

### 4.2 Correction to the costing's SITL plan (U9)
- The costing (`ukf_only_closed_loop_costing.md` §6, option A) assumed `FLOW_TYPE 10` / `SIM_FLOW` with Gazebo.
  **The 2c bench found the SITL flow sensor and the analogue SITL rangefinder unusable with this Gazebo model** [V,
  handover `2026-10-11_watcher_sitl_bench.md` §2.2].
- **Re-planned:** fly V1–V7 on the thesis camera-flow MAVLink path (`FLOW_TYPE 5`, `flow_bridge.py`, `lidar_bridge.py`),
  as the bench did.
  - This is the better test: `FLOW_TYPE 5` pairs the AHRS gyro, whereas `SIM_FLOW` would have used the true gyro.
  - **The D18 bias swap runs only in V1** (UKF shadow, EKF3 flying). Under type 12 (V2–V6) the rule is the identity.
    **V1 would be the first flying log with the swap active**, which closes open item 1 of the r1-port handover
    (`2026-10-11_r1_ukf_port.md` §4).
  - The built-in `-f quad` model (option B) remains a fallback.
- **The "after 16 Oct" restriction is superseded.** Short verification flights are allowed now under the standing rule
  (2026-10-11), one at a time, under the locks. So V1–V7 are in the no-hardware list.
- **They need a SITL build of the branch that will fly** (`rung1-geometry` + U4, or `board-h743` merged): the
  installed SITL copter is `ukf-jitter-fix` `abb0357d`. One light build.
- **V7's TFAIL arming refusal cannot be tested in SITL** (the guard is compiled out of SITL). It is bench P5 only.
- **Add to V3/V4's pass criteria:** the land detector trips after the LAND under type 12 (F2).

### 4.3 No-hardware TODO (beyond rung 1's §3.2; do NOW)

| # | item | effort | status | blocks UKF-only? |
|---|---|---|---|---|
| U-a | **F6: the watcher's LAND retry.** Stop re-sending once the FC heartbeat shows LAND or any pilot mode (STABILIZE/ALT_HOLD); offline tests; re-run the 83 `realflight` tests | 0.5 d after the ruling | **DONE 2026-10-12** (rule S1–S5/R in `fc_link.py`; 8 new tests; 91/91 pass; handover `2026-10-12_watcher_f6_failsafe_b5_b8a.md`) | **YES** (a safety finding). Also blocks rung 1 if the watcher is used there |
| U-b | **U4** (= R-e) | (in R-e) | ruling needed | **YES** if the rangefinder minimum exceeds the ground clearance (the UKF never initialises, so the vehicle cannot arm in type 12) |
| U-c | **SITL verification flights V1–V7** on the MAVLink flow path (§4.2): harness 0.5 d, one light SITL build, flights 1.5–2 d | 2–2.5 d | not started | **YES** (the costing's SITL gate) |
| U-d0 | **The U10 Replay-gate band, pre-registered** (the onboard UKF replayed on the rung-1 logs: initialises, stays `HORIZ_POS_REL` through hover and moves, `_n_chol_fail` = 0, trajectory against mocap within a band). **Due before any UKF Replay of a real log, i.e. before rung-1 day 3**; otherwise the gate is post hoc (the E5 failure class) | 0.25 d | not written | **YES** |
| U-d | **Stage-3 pre-registration** (U14): profile (scripted GUIDED or pilot LOITER), n, window, abort rules, the 5 s aiding-loss latency accepted (or not), the watcher box sized for it, S-A2b, the V1–V7 and bench pass criteria (it incorporates U-d0) | 1–1.5 d | not written | **YES** |
| U-e | **Real-FC failsafe parameter file** (U7): `AHRS_EKF_TYPE 12`, `AHRS_UKF_ENABLE 1`, `AHRS_UKF_TFAIL 0`, `FS_EKF_ACTION 1`, `FS_GCS_ENABLE 5`, `FS_GCS_TIMEOUT`, `MAV_GCS_SYSID` (the watcher), `FS_OPTIONS`, RC and battery failsafes. A `check_parm.py` stage-3 mode that accepts type 12 only there | 0.5 d | **DRAFTED 2026-10-12**: `rung1_failsafe_fc.parm` + `ukfonly_failsafe_fc.parm`, `check_parm.py --stage3`; TODO_SUPERVISOR values and the EKF-origin FLAG remain | **YES** |
| U-f | **H10 takeover guard + F4** in the real flight script: no LAND when the FC is in a pilot mode or already in LAND; pin the FC's system ID; take the mode mapping from the FC's own heartbeat. (`fly_trial.py` as it is would command LAND in B10b) | 1–2 d | prototype in the bench driver only | **YES if a scripted GUIDED profile is chosen**; not needed for a pilot-flown LOITER profile |
| U-g | **F2 investigation** (why the land detector does not trip on flow-only EKF3) and the card line (R-g) | 0.25–0.5 d | open | the card line YES; the investigation no |
| U-h | **Own-gyro FLOW_TYPEs** (1/3/6/10) ruling: in closed loop (type 12) the rule is the identity, so a HereFlow's own gyro is fused with NO UKF bias; decide accept-and-state or derotate from the port's own DAL gyro (costing §3 option b) | 0–1 d | ruling needed | **YES only if** the sensor is HereFlow/PX4Flow/Bebop |
| U-i | **Multi-IMU swap**: on a 2-IMU board, the swap uses EKF3's primary-core bias while the UKF uses `get_first_usable_gyro()`, so it can mix IMUs. Inert in closed loop (type 12 = identity); matters for the U10 Replay gate on the EKF3-flown rung-1 logs. Check the code path; propose a rule (e.g. compare per IMU, or pin `EK3_PRIMARY` / the UKF's IMU) | 0.5 d | open | for U10's validity on a multi-IMU board; not for the flight itself |
| U-j | **B5 wording** (the 0.5 s bound equals the stale limit) and **B8a** (void, repeat or accept) rulings. A B8a repeat is one short SITL verification flight on a larger floor | 0–0.25 d | **B5 re-worded 2026-10-12** (ruling 4); **B8a: determined a harness fault** (no EKF origin; handover `2026-10-12_watcher_f6_failsafe_b5_b8a.md`), repeat for the user to schedule | the rulings YES (they close the watcher bench); the code no |
| U-k | **G6** (procedure + `ARMING_RUDDER 0`, or the Lua arming-auth) and the watcher system ID (211/213 placeholders) | 0.1 d | rulings needed | YES (the arming procedure) |
| U-l | Optional: a separate `AP_NAVFGO_ENABLED` flag (a UKF-only build drops ~5 kB flash, ~15 kB RAM) | 0.25 d | optional | no |
| U-m | Firmware build ready (`tools/build_board_fw.sh`) | 0 d | **DONE** (§6) | — |

**Total ≈ 6–9.5 d beyond rung 1's §3.2** (U-a, U-c to U-k with U-d0; excluding the rulings themselves and the
optional U-l).

### 4.4 What the UKF-only closed loop waits on (hardware)
Everything in §3.3, plus:
- **Board:** the fork built for its hwdef; P1–P10; the FC trigger-timing test; the stack and CPU margins; Lua (if
  G6(ii)); `ALLOW_ARM_NO_COMPASS` if no compass.
- **Sensors:** `FLOW_TYPE` (decides U-h); the rangefinder minimum (decides U4); the IR check in the volume.
- **Mocap:** the protocol for the live client F1 (1–2 d of coding once known; not startable before); 4 more booked
  days; the telemetry link (radio or Wi-Fi) and its worst gap.

---

## 5. Open rulings and defects: what each one blocks

"Blocks" means the plan cannot proceed past that point without it. "Condition" says when it applies.

| # | item | rung 1 | UKF-only | condition / note |
|---|---|---|---|---|
| 1 | **Pre-registration sign-off** (rung 1) | **BLOCKS** result sorties | blocks (via U10, which uses the rung-1 logs) | verification sorties may fly before it |
| 2 | **E5 post hoc** (increment form adopted after the cumulative form failed) | **BLOCKS** the UKF row (via the `rung1-geometry` merge, R-b) | **BLOCKS** (the flying port is `rung1-geometry`-based) | EKF3 and FGO rows of rung 1 unaffected |
| 3 | **Capture-delay option** (R-c) | **BLOCKS** the UKF row as drafted | no | could be dropped by re-wording the prereg |
| 4 | **`XUKO` in Replay** (R-d) | **BLOCKS** the UKF row as drafted [U] | no (onboard, `XUKO` is logged) | check first |
| 5 | **F6** LAND resend against the pilot | blocks only if the watcher is used in rung 1 | **BLOCKS** | safety |
| 6 | **F2** land detector on flow-only EKF3 | **BLOCKS** until the card line exists (R-g) | **BLOCKS** until the V3/V4 criterion and the card line exist | safety |
| 7 | **U4** rangefinder below minimum on the ground (GNDCLR init) | UKF row degraded (initialises mid-climb), flight not blocked | **BLOCKS** arming in type 12 | only if `RNGFND1_MIN` > the resting clearance |
| 8 | **Own-gyro FLOW_TYPEs** 1/3/6/10 | UKF row uses the sensor's gyro as delivered, with a warning (state it) | **BLOCKS** until ruled | only if the sensor is one of these |
| 9 | **Multi-IMU swap** | UKF row: the swap may mix IMUs (state or fix) | U10 gate validity | only on a multi-IMU board |
| 10 | **`fly_trial.py` takeover guard** (H10) + F4 | no (pilot-flown) | **BLOCKS** a scripted profile | only if the stage-3 profile is scripted GUIDED |
| 11 | **B5 wording / B8a repeat** | no | **BLOCKS** the watcher-bench sign-off | rulings, not code |
| 12 | **Compass variant / `ALLOW_ARM_NO_COMPASS`** | **BLOCKS** arming if no compass is fitted: stock unmodified firmware cannot arm in nomag (Copter's compass gate is unconditional); needs a fitted compass, or a ruling to fly an `--extra-hwdef` build (departs from "unmodified") | **BLOCKS** in the same case (the define goes into the fork build) | the `--extra-hwdef` build path is UNTESTED |
| 13 | **GNDCLR initialisation** | = item 7 | = item 7 | |
| 14 | **Stale parameter names** in CLAUDE.md / the 10-10 plan | no | no | `check_parm.py` refuses them anyway |
| 15 | **S6** firmware: pinned `7bac20cbcc` or stock 4.7.0 | **BLOCKS** day 1 | — | supervisor |
| 16 | **Merging `board-h743`** (carries `rung1-geometry`) | no | **BLOCKS** the flown build being on a named, merged commit | user's call |
| 17 | **Stage-3 pre-registration** (U-d) | no | **BLOCKS** | |
| 17a | **U10 Replay-gate band pre-registered** (U-d0) | no | **BLOCKS**, and must be filed before rung-1 day 3 | otherwise the gate is post hoc |
| 18 | **G6** arming procedure / Lua; watcher system ID | no | **BLOCKS** | |
| 19 | **Freeze scope** (do flights after 23 Oct count?) | decides whether rung 1 is in the thesis if Day 0 is after 15 Oct | decides whether it is in the thesis at all | |

---

## 6. Firmware kept READY

### 6.1 The script
`tools/build_board_fw.sh <BOARD> [--without] [--dry-run] [--out DIR] [--ref REF] [--extra-hwdef FILE] [--no-lock-check]`
- **One command per board.** It validates the board's hwdef on the ref (default `board-h743`), the MCU (H7; warns for
  anything but STM32H743xx), the toolchain and the submodules. Then it creates a temporary detached worktree, builds
  Copter with `--enable-THESIS_NAVUKF`, and copies out the `.apj`/`.hex`/ELF/`hwdef.h`/logs. Finally it removes the
  worktree and checks that the ref did not move.
- **`summary.json` checks:**
  - flash free ≥ 32 kB (from the `.apj` header);
  - 0 warnings;
  - the backends present (or absent with `--without`);
  - the identity equals the ref;
  - the stack: the largest thesis frame within the build's `frame-larger-than` limit, and a conservative chain bound
    (the 6 largest thesis frames) within half the main stack.
- **Rung-1 stock image:** `--ref 7bac20cbcc --without` (a clean detached worktree of the pinned commit, unmodified
  source).
- **A real build refuses to run** without the `heavy.py` that holds `BUILD_LOCK`, or with `FLIGHT_LOCK` present.
  `--dry-run` needs no lock. **Nothing is ever flashed.**
- `--extra-hwdef` (e.g. `define ALLOW_ARM_NO_COMPASS`) is wired but **untested**, as in 2a.

### 6.2 Likely H743 Copter targets (all 18 hwdefs present on BOTH `board-h743` and `7bac20cbcc` [V, `git cat-file`])
Published stable Copter `.apj` headers, `git_identity dbe79216`, fetched 2026-10-12 from
`firmware.ardupilot.org/Copter/stable/<board>/` [V] (`eval/results/board_fw_ready/stable_dbe79216_apj_headers.txt`).
**"Fork, projected" = stable free − 24 kB** [E], a conservative rule: the backends add 23.8–24.2 kB, while our
`7bac20cbcc` base came out 1.4–4.9 kB smaller than stable on the three boards measured (fork free 134,692 / 267,348 /
245,276 B against the projected ~130 k / ~263 k / ~244 k).

| board | class | flash_total (B) | stable image (B) | **stable free (B)** | fork, projected free [E] | measured fork free |
|---|---|---|---|---|---|---|
| Pixhawk6C | Pixhawk | 1,966,080 | 1,590,348 | **375,732** | ~352 k | — |
| Durandal | Pixhawk | 1,966,080 | 1,596,172 | **369,908** | ~346 k | — |
| CubeOrange | Cube | 1,966,080 | 1,644,436 | **321,644** | ~298 k | — |
| Pixhawk6X | Pixhawk | 1,966,080 | 1,679,428 | **286,652** | ~263 k | **267,348** (2a) |
| CubeOrangePlus | Cube (**STM32H757**, not H743) | 1,966,080 | 1,713,060 | **253,020** | ~229 k | — |
| AEROFOX-H7 | other | 1,966,080 | 1,519,020 | **447,060** | ~423 k | — |
| FoxeerH743v1 | FPV / cinewhoop AIO | 1,703,936 | 1,238,160 | **465,776** | ~442 k | — |
| KakuteH7v2 | FPV / cinewhoop | 1,703,936 | 1,418,380 | **285,556** | ~262 k | — |
| FlywooH743Pro | FPV | 1,703,936 | 1,422,132 | **281,804** | ~258 k | — |
| JHEMCU-H743HD | FPV | 1,703,936 | 1,425,908 | **278,028** | ~254 k | — |
| KakuteH7Mini | FPV / cinewhoop | 1,703,936 | 1,429,732 | **274,204** | ~250 k | — |
| KakuteH7 | FPV / cinewhoop | 1,703,936 | 1,436,028 | **267,908** | ~244 k | **245,276** (§6.3) |
| KakuteH7-bdshot | FPV / cinewhoop | 1,703,936 | 1,437,388 | **266,548** | ~243 k | — |
| MicoAir743 | FPV | 1,703,936 | 1,528,404 | **175,532** | ~152 k | — |
| TBS_LUCID_H7 | FPV | 1,703,936 | 1,553,284 | **150,652** | ~127 k | — |
| MatekH743 | FPV / wing | 1,703,936 | 1,549,916 | **154,020** | ~130 k | **134,692** (2a) |
| MatekH743-bdshot | FPV / wing | 1,703,936 | 1,553,764 | **150,172** | ~126 k | — |
| MambaH743v4 | FPV (tightest) | 1,703,936 | 1,591,292 | **112,644** | ~89 k | — |

- **Every target clears G2's 32 kB with the backends**, the tightest (MambaH743v4) by about 57 kB [E].
- **With scripting kept** for the Lua arming-auth (G6(ii)), nothing changes: scripting is already in these images.
- **Boards that keep parameters in flash** (Kakute, Matek, Mamba, Flywoo, Foxeer, JHEMCU, MicoAir, LUCID) have
  1,703,936 B; Pixhawk/Cube-class 1,966,080 B.
- **IMU count** is NOT read from the hwdef: its `IMU` lines are probe alternatives, so the fitted count is [U] until
  the board is in hand (it matters for §5 item 9).
- **KakuteH7, -bdshot and v2 share `board_id` 1048.** The uploader's board-ID check will not catch the wrong one;
  confirm the revision physically.

### 6.3 The test build (2026-10-12)
- **Dry runs** (no lock needed), all behaving as designed:
  - no board, or an unknown option → usage, exit 2;
  - an unknown board (`NoSuchBoard`) → "no hwdef on board-h743", exit 2, nothing created;
  - an F4 board (`BrahmaF4`) → refused (not an H7), exit 2;
  - `KakuteH7v2` (MCU resolved through its include chain), `CubeOrangePlus --without` (H757 warning), `KakuteH7 --ref
    7bac20cbcc --without` (the rung-1 stock image), `MambaH743v4 --extra-hwdef …`: worktree created at the right
    commit, listed, removed; "cleanup OK", ref unchanged, the fork's worktree list back to its 2 entries;
  - a real build outside `heavy.py` → refused ("no BUILD_LOCK").
- **One real build, KakuteH7, with the backends, under `heavy.py`** (no flight running, `BUILD_LOCK` free):
  - **attempt 1 failed in seconds** (waf's mavgen: the nested `pymavlink` submodule was not initialised). Fixed: the
    script now initialises the nested submodules (pymavlink, CrashCatcher, mri) by reference. Its output directory is
    kept, renamed `…_FAILED_nested_submodules`;
  - **attempt 2 built** (1 m 37 s for `waf copter`): `.apj` md5 `8677e30a…`, `git_identity 0156bfc3`, `board_id` 1048,
    image 1,458,660 B, **flash free 245,276 B of 1,703,936 (PASS ≥ 32 kB)**, **0 warnings**, NavUKF and NavFGO
    symbols present, `.bss` 158,444 B, main stack 7,168 B; worktree removed, `board-h743` unchanged;
  - **its stack sub-check FAILED because of a script bug**, not the firmware: the `-fstack-usage` recompile kept waf's
    joined `-o<path>` and gcc refused "too many filenames", so no frames were read (the summary says `pass: false`).
    The build itself passed `-Werror=frame-larger-than=1300` (limit 1,300 B per frame), so no thesis frame exceeds it.
    **Fixed afterwards** (the 2a `stack_usage.py` filter, which worked on these boards) and the chain check now
    requires frames to have been read. **The fix is NOT re-verified by a build** (one real build only, per the stage
    brief): the next real build is its first test.
  - Artefacts (not in git): `~/thesis_data/fw_builds/KakuteH7_with_0156bfc3_20261012_014707/` (`.apj`, `_with_bl.hex`,
    `.bin`, ELF, logs). Text results in git: `eval/results/board_fw_ready/`.
  - **Nothing was flashed.**
