# Handover 2026-10-12: `rung1-geometry` merged and its Replay installed (E5); U4 GNDCLR start fix; U10 and stage-3 drafts

One stage agent. It implements METHODOLOGY "RULINGS (user, 2026-10-12)", items 1 and 3.
- No simulator or flight was run, and no trial data were written.
- METHODOLOGY.md and numbers.md are untouched.
- Every build and Replay ran under `heavy.py`, one at a time, with no FLIGHT_LOCK and no SITL running (checked before
  each step).

## State
- **`~/ardupilot_ukf`:**
  - **`ukf-jitter-fix` → `16535f9a29`** (fast-forward from `abb0357d0f`; it = `rung1-geometry`). It is checked out,
    and the tree is clean.
  - **New branch `u4-gndclr` → `53bac01636`** (one commit on `16535f9a29`). It is NOT merged and NOT installed.
  - `board-h743` (`0156bfc34e`) is unchanged and is still a descendant of the merged head.
  - The worktree list is back to its two entries (`ardupilot_ukf`, `ardupilot_diag`). The 15 submodule URLs in the
    shared `.git/config` are the `.gitmodules` remotes (none local), unchanged.
- **Installed binaries** (`~/ardupilot_ukf/build/sitl`):

  | binary | before (abb0357d) | now (16535f9a29) |
  |---|---|---|
  | `tool/Replay` | `e8e9feac6ac03512ae1742c36958f4e3` | **`be7c4d1880e09289d282ab8f076c7240`** |
  | `examples/UKF_Equiv` | `537e0dcd808ddfe4c6d3265a44d983e3` | **`180cf2d81cc004b8212b5bc447eb1113`** |
  | `bin/` SITL copter | `5f94ea1aa7e223f90343c1948d443d32` | **unchanged** (`5f94ea1a…`, not rebuilt; md5 printed before and after the build) |

  - **Backup** of the old Replay and UKF_Equiv: `~/opt/ukf_port_backup_abb0357d_2026-10-12/` (with `MD5SUMS`).
  - The build compiled with 0 warnings (`eval/results/port_merge_u4/install_build_summary.txt`).
  - The installed Replay's md5 differs from the 2026-10-11 scratch build's `a1f67e7d` (a different build tree). Output
    identity is the proof, below.
- **thesis_ws (this worktree branch):**
  - `docs/u10_replay_gate_band_draft.md` (new, DRAFT);
  - `docs/stage3_ukf_closed_loop_preregistration_draft.md` (new, DRAFT);
  - `eval/diag/port_merge_u4/` (the build, driver and comparison scripts);
  - `eval/results/port_merge_u4/` (logs, md5s, `u4_compare.json`, the U4 test geometry reports);
  - this handover.

## 1. E5 ruling: merge and install
- **E5 is recorded as "FAILED AS WORDED; accepted post hoc on increments"**, as ruled (ruling 2026-10-12 item 3):
  - on `cl_ukf_b_tex_r1_half_v2` the cumulative range-count form failed (9778 against 9749, 0.30 %), because the
    Replay UKF initialises 1.0 s after the flying port, a pre-existing offset;
  - the increment form over the paired window (identical counts) was adopted AFTER that failure, and is labelled post
    hoc;
  - `rung1-geometry` was accepted for merge on the other checks plus that increment comparison.
  - **The U10 draft pre-registers the increment form for real logs** (§4 G6), so it is no longer post hoc there.
- **The merge:** `git merge --ff-only rung1-geometry` on `ukf-jitter-fix`.
  - Its diff touches only `Tools/Replay`, `AP_NavUKF`, and argument passing in `AP_AHRS::writeOptFlowMeas` /
    `AP_DAL` (a read-only `getGyroBias`).
  - No submodule pointers changed.
- **The install:** `./waf replay` and `./waf build --target examples/UKF_Equiv` in place. There was no `waf copter`
  and no configure.

### Byte-identity re-check on the INSTALLED Replay (`eval/results/port_merge_u4/driver_inst.log`)
Five SITL `LOG_REPLAY` logs, each with the flight's own UKF options (as the 2026-10-11 stage):

| check | dsn_tex_r1 (10) | fwdplainc_tex_r1 (10) | cl_a_tex_half (3) | cl_ukf_b_tex_r1_half_v2 (12) | H_s2v2_r1 (12) |
|---|---|---|---|---|---|
| `UKF_DEROT_ROFH=1`: shadow + inputs vs the OLD installed Replay (`e8e9feac`) | identical | identical | identical | identical | identical |
| default: all 4 CSVs vs the tested scratch build of 2026-10-11 (`a2/<log>/new`) | identical | identical | identical | identical | identical |
| default: shadow + inputs vs the OLD installed Replay | inputs identical; shadow differs (the D18 swap, as designed) | same | same | **identical** | **identical** |

- **UKF_Equiv** (installed `180cf2d8`) on the 7 stored 2026-10-09 tape runs: state and diag(P) are byte-identical to
  the old installed build's outputs, 10 of 10 files (`equiv_inst.log`).
- So the installed Replay is the tested one, the old rule is reproduced exactly under `UKF_DEROT_ROFH=1`, and type 12
  is unchanged.

### Does the SITL copter need reinstalling? **Not for any type-12 flight; YES (a new SITL build) before V1.**
- **Type 12 (the UKF active), the only configuration flown on the installed copter:**
  - the derotation rule is the identity (`activeIsOwn` true → the paired gyro used as delivered = the old rule);
  - the R2 geometry reads the SITL parameters, which equal the old constants bit-for-bit (`q_um`; Replay shows
    `UKF_GEOM_SITL` and the default give identical outputs);
  - the only other change is argument passing;
  - the Replay rows above prove the type-12 identity on two flown type-12 logs.
  - So the installed copter `5f94ea1a` (`abb0357d`) flies type 12 identically. **No reinstall.**
- **When the UKF is NOT the active backend (EKF3 or SIM flying, UKF in shadow)** the swap changes the UKF's shadow
  state, though never the vehicle's flight, since the shadow does not steer.
  - **Every UKF-enabled flight since the installed copter was built (2026-10-09 12:26) was type 12.** This is the
    PARM readback of all 36 trials whose log carries `XUKF`, and covers 10 flights since the build:
    - `H_s2v2_r1..r3`;
    - `cl_ukf_a_tex_half_v2`;
    - `cl_ukf_b_tex_r1..r3_half_v2`;
    - `H_safety_ukf_a/b_v2`;
    - `H_safety_ukf_a/b_v3`.
  - **Historically, shadow flights DID exist on earlier binaries:** `ukf_shadow_sitl_tex*` (type 10) and
    `ukf_shadow_hdg_v2` (type 3), 2026-09-29/30. "Never happens" is true only of the installed copter's flights.
- **Consequence:** SITL V1 (UKF shadow, EKF3 flying; plan §4.2) needs a SITL build of the branch to be flown.
  - With the installed copter, V1 would test the OLD derotation rule.
  - That is one light build, and also needed for U4 if merged.
- **Caution:** the installed copter is still `abb0357d` while the branch HEAD has moved to `16535f9a29`. Any
  `sim_vehicle.py` run WITHOUT `--no-rebuild` would silently rebuild it from the new HEAD (`run_trial.sh` passes
  `--no-rebuild`).

## 2. U4: the rangefinder start fix (`u4-gndclr` `53bac01636`; not merged, not installed)

### What EKF3 actually does (verified in the pinned source, `~/ardupilot` `7bac20cbcc`)
- `rngOnGnd = MAX(RNGFND GNDCLR, 0.05)` (`AP_NavEKF3_Measurements.cpp:29`). It is used:
  - as a floor on Good samples (`:85`);
  - as a pseudo-sample on the ground when the sensor is Good but fewer than three samples are fresh, at > 200 ms
    staleness (`:94-104`);
  - in terrain/height clamps.
- **For a non-Good sensor (OutOfRangeLow) `readRangeFinder` hits `else { continue; }` before the on-ground branch, so
  EKF3 pushes NOTHING.** Its range data go stale, `lostRngHgt` is set, and it **falls back to baro height**
  (`AP_NavEKF3_PosVelFusion.cpp:1290, 1356-1374`). Its initialisation does not need a range.
- **So "initialise from GNDCLR, as EKF3 does on the ground" (costing U4, plan R-e) and rung-1 prereg §9 limit 11 ("EKF3
  then uses RNGFND1_GNDCLR") are INACCURATE.** EKF3 uses baro in that case. Those documents were not edited here; this
  needs a wording fix when they are next amended.

### The port rule implemented (a PORT rule, labelled as such in the code and commit)
- **When:** while DISARMED (EKF3's onGround = not armed, `AP_NavEKF3_VehicleStatus.cpp:378-384`), with no downward Good
  sample for > 200 ms, and a downward backend reading `OutOfRangeLow`.
- **What:** the UKF uses EKF3's on-ground value `rngOnGnd = MAX(GNDCLR, 0.05)` (from the DAL, i.e. `RRNH` in Replay),
  with that backend's lever arm:
  - to initialise (h = rngOnGnd + lever);
  - as a range sample every > 200 ms (EKF3's on-ground cadence), exempt from the `RNGFNDn_MIN/_MAX` window;
  - as the D15 "range at arming".
- **It stops at arming, and is inert whenever a downward backend is Good.**
- **NOT added:** EKF3's `MAX(range, rngOnGnd)` floor on Good samples. SITL's `RNGFND1_GNDCLR` is 0.10 m against a
  0.075 m resting range, so the floor would change SITL outputs. This difference from EKF3 predates U4.
- **Reporting:** a GCS text "UKF: rangefinder below minimum on ground; using GNDCLR …"; in Replay, the
  `u4_gndclr_first` and `u4_init_from_gndclr` lines in `ukf_geometry.csv`. The other CSV formats are unchanged.
- **Replay-only test hook `UKF_TEST_RNG_LOW=<m>`:** inside the UKF only, a Good downward range below <m> counts as
  OutOfRangeLow. Replay EKF3 is unaffected.

### Proof (scratch worktree build under heavy.py; 0 warnings)
- **The scratch build:** Replay `cd4c2f76`, UKF_Equiv `075d7671`, copter compile check `8c81905b`. The worktree was
  removed afterwards.
- **Regression:** the default Replay on the 5 logs, with `ukf_shadow`, `ukf_inputs`, `ukf_derot` and `ukf_geometry`
  **byte-identical to the installed Replay**, 20 of 20 files (`driver_u4.log`).
- **UKF_Equiv:** 10 of 10 outputs byte-identical (`equiv_u4.log`).
- **Positive test**, `UKF_TEST_RNG_LOW=0.15` on `dsn_tex_r1` (type 10) and `cl_ukf_b_tex_r1_half_v2` (type 12)
  (`u4_compare.json`):
  - initialised from GNDCLR 0.10 m at the same instant as the default run (5.793 s / 5.750 s), h 0.22 against 0.20 m;
  - the same number of rows, `SS` identical on the ground, healthy;
  - about 5 Hz on-ground samples (Ra 100 / 99 at lift-off, against 652 at 30 Hz);
  - normal fusion once airborne.
  - The trajectory then differs as any UKF perturbation does: `dsn_tex_r1` max 1.57 m horizontal over the 150 m
    corridor, yaw ≤ 1.19°; `cl_ukf_b` (with heading) ≤ 0.010 m.
  - These are diagnostics of the test hook, not results. The hook also makes in-flight readings < 0.15 m (take-off and
    landing) count as low, but the GNDCLR path is not used then because the vehicle is armed.

### U4 open points (for the ruling or merge)
1. **After arming, no range is fused until the sensor reads above its minimum.** If take-off follows arming by more
   than `RNG_TIMEOUT_MS` (5 s), the UKF's `vert_pos`/`vert_vel` flags lapse until then. The UKF has no baro.
   - Options: a card line (take off within 5 s of arming), or extend the GNDCLR range to "armed and the D15 take-off
     not yet detected".
   - Not decided here; stage-3 draft §9 item 9.
2. GNDCLR comes from the FIRST downward backend (`ground_clearance_orient`), as EKF3. The lever comes from the backend
   that reads low. These differ only with two downward rangefinders.
3. The flying path compiles but is untested: it needs SITL V1/V7 (with a raised `RNGFND1_MIN`) and bench S8.

## 3. Drafts for the user's sign-off (both marked DRAFT)
### (a) `docs/u10_replay_gate_band_draft.md`: must be signed off BEFORE rung-1 day 3
- **The gate:** the fork's Replay (the commit to be flown) of every usable rung-1 result flight. **PASS only if every
  flight passes and at least 4 are usable:**

  | # | criterion | band |
  |---|---|---|
  | G1 | initialised before arming; the geometry from `log_parm` | must hold |
  | G2 | `horiz_pos_rel` + `Healthy` on 100 % of W, `FlowAgeMs` < 5 s | 100 % |
  | G3 | `_n_chol_fail` | = 0 |
  | G4 | UKF evo -a ≤ max(2.0 × EKF3-Replay, EKF3-Replay + 0.10 m) | per flight |
  | G5 | start-aligned drift ≤ D_max | [TBD-S], proposed 1.0 m |
  | G6 | only with the fork-in-shadow option: Replay vs onboard `XUKF` | E1 0.05/0.01 m, E3 0.05°, E5 increments 0.1 %, pairing from the later initialisation + 10 s; [TBD-V] confirmed or widened once on H/V |

- **The basis of G4:** the SITL textured UKF/EKF3 ratio was ≤ 1.43 on all 9 `dsn_tex` flights and ≤ 1.21 on `fwdc`.
  Only the two take-off-kick `fwdplainc` flights (2.74, 2.65) would fail it.
- **Found, a precondition:** **no Replay output carries `_n_chol_fail`** [V, source]. One summary line must be added
  before day 3.
- **The record:** `XUKO`, else `ukf_shadow.csv`, if R-d is unresolved by day 3.
- **The multi-IMU caveat:** the IMU count, `EK3_PRIMARY` and the core are recorded; a `UKF_DEROT_ROFH=1` sensitivity
  row is reported; the result is labelled "IMU-mixed" if the primary core is not on the UKF's IMU.
- **Reported, not gated:** the heading and cross-track drift rates. They feed the stage-3 excursion band.

### (b) `docs/stage3_ukf_closed_loop_preregistration_draft.md`
- **Sorties:** bench P/F/W, hand-carried H3, tethered T and the first free hover V3 are verification (short, never
  scored). **Result sorties:**
  - n = 5 (+1 spare);
  - profile: a 30 s hover, then ONE 2–3 m out-and-back leg at 0.2–0.3 m/s, then a 10 s hover; ~2 min airborne;
  - **[RULING]** option A, scripted GUIDED (needs H10/F4), or option B, pilot LOITER.
- **Decision (C1–C4, every sortie, ≥ 4 usable; any C1 failure stops the set):**
  - C1: completion under UKF control with no behaviour-caused takeover or failsafe;
  - C2: physical excursion ≤ E_max;
  - C3: 100 % validity;
  - C4: hover lateral speed ≤ 0.25 m/s, gyro rms ≤ 2 × rung-1.
- **E_max:** pre-registered formula, E_pred = L·sin(ψ̇T) + v_b·T + 0.10 m, with ψ̇ and v_b from the U10 replayed
  drift rates. E_max = max(1.5·E_pred, 0.30 m), and it must fit the watcher box minus 0.5 m, or the profile is
  shortened.
- **Metrics:** the rung-1 family (evo -a of the onboard `XUKO`, 4-DoF, start-aligned, and the UNALIGNED cross-track
  and heading drift rates), descriptive.
  - The EKF3 shadow is DIAGNOSTIC only (a UKF-flown trajectory, not like-for-like).
  - No ordering claims.
- **Safety gates S1–S11 before any free flight:**
  - V1–V7 (V1 with the swap active);
  - U10 PASS;
  - P1–P10 incl. P5 forced;
  - forced invalidity (0.1 s; S-A1/S-A3 on the tether);
  - S-A2b ≤ 5.5 s;
  - the heartbeat → LAND;
  - RC override + F6;
  - U4 (if applicable);
  - the H3 Replay;
  - the F2 land detector;
  - the failsafe readback.
- **Aborts:** the box, tilt > 25°, oscillation, lateral > 0.5 m/s, failsafe texts, mocap or watcher loss, the pilot's
  judgement.

## 4. Open (for the user)
1. **Rulings:**
   - sign off the two drafts (U10 before rung-1 day 3);
   - the U4 post-arming gap (§2 open 1);
   - whether to merge `u4-gndclr`;
   - stage-3 option A/B and the [RULING] items of its §10.
2. **Wording fixes to schedule:** the "as EKF3 does" claim for GNDCLR in the costing U4 row, plan R-e, and rung-1
   prereg §9 limit 11 (EKF3 falls back to baro, §2 above). Not edited here.
3. **Before day 3 (U10 preconditions):**
   - a `_n_chol_fail`/`_n_chol_retry` Replay output line;
   - the R-d `XUKO` decision;
   - D_max from the volume.
4. **Before SITL V1:** a SITL copter build from the branch to be flown (the installed one is `abb0357d`).
5. The rung-1 JSON does not yet contain the two signed-off drift-rate secondaries. Applying the sign-off (R-a) is a
   separate item.
