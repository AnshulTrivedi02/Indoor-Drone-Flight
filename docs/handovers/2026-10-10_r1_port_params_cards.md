# Handover 2026-10-10: rung-1 software R2/R3 (UKF port geometry + CSV→TUM), R6 (parameters), R10 (pre-registration draft), R11 (flight cards)

One stage agent, coding and docs only (no simulator, no flights, no install). METHODOLOGY.md and numbers.md untouched.

> **USER TRIAGE (2026-10-10, received mid-stage):**
> - **A (the UKF-port geometry, `~/ardupilot_ukf`) is ON HOLD** until the supervisor confirms the hardware. Its state
>   was committed on its own branch only (`rung1-geometry` `c25fa8980d`); no build, no install; the scratch worktree is
>   removed. What exists and what is left: see A below and "Left to do on A when it resumes".
> - **C (the pre-registration draft) is ON HOLD**: committed as it stood, marked DRAFT/ON HOLD, with its two known
>   defects listed at its top.
> - **B (parameters + `check_parm.py`) and D (flight cards, with the short-verification rule) CONTINUE**; both are done
>   in this stage (D now carries the verification/result table and the explicit exclusion of verification sorties
>   from scoring).

## What was done

### A. R2/R3: the UKF port reads the sensor geometry from the log
- **Repo/branch:** `~/ardupilot_ukf`, NEW branch **`rung1-geometry`** (from `ukf-jitter-fix` `abb0357d0f`), commit
  **`c25fa8980d`**. The checked-out branch (`ukf-jitter-fix`), `~/ardupilot_ukf/build` and the installed SITL binary were
  NOT touched. Not merged.
- **Before:** `AP_NavUKF.cpp` hard-coded `RANGE_LEVER 0.12`, `CAM_OFFSET 0.25`, `RNG_MIN 0.05`/`RNG_MAX 40`,
  `FLOW_DELAY_MS 10` and `HORIZON_MS 60`; the Replay flow hook dropped `ROFH.posOffset`.
- **Now** (the constants are only defaults = today's SITL values):

  | quantity | source on a vehicle | source in Replay |
  |---|---|---|
  | flow sensor offset (3-D, FRD) | `posOffset` from `AP_AHRS::writeOptFlowMeas` (= `FLOW_POS_*`) | `ROFH.posOffset` (hook now passes it) |
  | range lever (z) | DAL rangefinder backend `get_pos_offset()` (`RNGFNDn_POS_*`) | `RRNI.pos_offset` |
  | both, minus | `INS_POSn_*` of the first usable accel (EKF3's `posOffset − accelPosOffset`) | same (INS group is in Replay's table) |
  | `RNGFNDn_MIN/_MAX` (per backend) | `AP_Param::get` | the log's `PARM` records via a NEW `AP_DAL::ukf_param_hook`, called from `LR_MsgHandler_PARM::set_parameter` (Replay's table has no RNGFND group, so `AP_Param` cannot see them there) |
  | flow delay | `AP_Param::get("EK3_FLOW_DELAY")` | same (EK3 group is in Replay's table; it is what Replay's EKF3 uses) |
  | fusion horizon | EKF3's `MAX(EK3_HGT_DELAY, EK3_FLOW_DELAY, EK3_BCN_DELAY, magDelay_ms 60, 12)` (`AP_NavEKF3_core.cpp:42-47`) | same |

  - The flow model uses the full 3-D offset in the `ω × r` term; the camera height keeps the port's model (`−pD − r.z`,
    no tilt). Changing that would be a D18 model change, so it was not made.
  - The range model keeps `−pD − lever.z` (flat, no tilt; lateral rangefinder offsets × tilt are neglected, as before).
  - **Bit-identity device:** every float value is quantised to 1 µm in double (`q_um`); IEEE division is correctly
    rounded, so `0.12f` → exactly `D(12, 100)`, the old constant. `EK3_FLOW_DELAY` is an integer.
  - `writeOptFlowMeas` now REQUIRES `posOffset` (no default argument, so no caller can silently get a zero lever arm).
    Call sites updated: `AP_AHRS.cpp`, the DAL hook typedef, `AP_DAL.cpp`, the Replay lambda. `examples/UKF_Equiv`
    does not call it and uses the constructor defaults (unchanged).
  - Replay writes **`ukf_geometry.csv`** (the geometry actually used and where each value came from; the lever arms
    when first seen and whenever they change). `ukf_shadow.csv` and `ukf_inputs.csv` formats are unchanged (so the old
    byte-identity comparisons still apply). `UKF_GEOM_SITL=1` forces the old constants (for any older log).
- **Evidence that SITL behaviour should be unchanged:** the PARM dumps of the existing SITL `LOG_REPLAY` logs
  `cl_a_tex_half`, `dsn_tex_r1`, `dsn_tex_r4`, `H_s1_r1` all carry `FLOW_POS_Z 0.25`, `RNGFND1_POS_Z 0.12`,
  `RNGFND1_MIN/MAX 0.05/40`, `EK3_FLOW_DELAY 10`, `EK3_HGT_DELAY 60`, `EK3_BCN_DELAY 50`, `INS_POS* 0`.
  `LOG_REPLAY 1` arrived in the same commit as `FLOW_POS_Z 0.25` (`45c5483`, `consolidated_rerun.parm`), so no
  replayable SITL log should carry the older `0.13`. `UKF_GEOM_SITL=1` covers any exception.
- **Compile status:** see "Compile check" below.
- **R3: `eval/ukf_csv_to_tum.py`** (thesis_ws). `ukf_shadow.csv` → TUM on the FC clock (s). `--frame enu` (default,
  the frame `mocap_align.py` writes mocap truth in: `(E, N, U)` and `q_enu_flu = q_ned2enu ⊗ q_ned_frd ⊗ q_frd2flu`) or
  `--frame ned` (as `three_way_eval` for EKF3); `--identity-quat`, `--healthy-only`, `--t0-us/--t1-us`. TimeUS in the CSV
  is the fusion-horizon time of the logged state (1 ms resolution). `--selftest` PASS (9 checks incl. ENU yaw 90° when
  facing North, roll sign); ran on `d15_port/dsn_tex_r8/ukf_shadow.csv` (8606 poses).

### Must be re-verified once a build is allowed (the port equivalence harness)
1. Build the fork's Replay from `rung1-geometry` (sitl board, `./waf replay`), in a scratch worktree or after the SITL
   re-tests no longer need the installed binary.
2. **Replay regression, old vs new, byte-identical `ukf_shadow.csv` and `ukf_inputs.csv`** on at least: one
   `dsn_tex` log (e.g. `dsn_tex_r1`), one closed-loop UKF log (`cl_ukf_b_tex_r1_half_v2` or `H_gt_ukf_far` with
   `UKF_EXTPOS=1 UKF_EXTYAW=1`, the earlier regression's case), one `fwdplainc` log. Check `ukf_geometry.csv` reads
   `mode,log`, flow_delay 10 (param), horizon 60, rng1 0.05/40 (log_parm), flow_lever 0,0,0.25, range_lever 0,0,0.12.
3. **`UKF_GEOM_SITL=1`** on the same logs → also byte-identical (proves the switch).
4. **`examples/UKF_Equiv`** harness (validation step 2) rebuilt and re-run on its existing event tapes → identical
   output (it uses the constructor defaults; expected unchanged).
5. A synthetic non-SITL geometry check: Replay one log with `--parm` style overrides is NOT possible for FLOW_POS
   (ROFH carries the logged offset); instead check on the first real (hand-carried) log that `ukf_geometry.csv` shows the
   vehicle's measured offsets.
6. In-vehicle SITL (`AHRS_UKF_ENABLE 1`) is affected only through `AP_AHRS` passing `posOffset`; any future SITL UKF
   flight with this branch should log the "UKF geometry: …" text line once.

### B. R6: `realflight/params/`
- **`rung1_template.parm`** (commented line by line): AHRS_EKF_TYPE 3 with the loud NEVER-10 warning; EK3 sources (flow
  velocity, rangefinder height, no GPS); EK3_FLOW_*; FLOW_*; RNGFND1_*; INS_POS1_*; GPS1_TYPE 0; ARMING_SKIPCHK 0;
  altitude-only fence; failsafes; mode switch; LOG_REPLAY 1, LOG_DISARMED 1, LOG_BITMASK 180222 (decoded),
  LOG_FILE_BUFSIZE, LOG_FILE_DSRMROT 0.
- **Compass variants (the supervisor's choice, FLAG):** `rung1_variant_nomag.parm` (EK3_SRC1_YAW 0, COMPASS_ENABLE 1,
  COMPASS_USE* 0; recommended for like-for-like) and `rung1_variant_compass.parm` (EK3_SRC1_YAW 1; the yaw confound
  stated). Exactly one is appended.
- **`check_parm.py`**: refuses AHRS_EKF_TYPE 10, any SIM_*, ARMING_SKIPCHK ≠ 0, the stale name ARMING_CHECK, unknown
  names (against `pinned_param_names.txt`), non-numeric values, two variants; `--final` also refuses TODO_SUPERVISOR and
  missing required values. `--selftest` PASS (10 checks: `consolidated_rerun.parm` and `gnss_denied.parm` refused; both
  variants pass in draft; `--final` refuses placeholders; …).
- **`pinned_param_names.txt`**: all 1379 names from the PARM dump of a SITL build at `7bac20cbcc` (`cl_a_tex_half`).
- **Name verification: every one of the 66 names used exists** (in the dump AND as an `@Param` leaf in `~/ardupilot`).
  **Names that do NOT exist (and are therefore not used), corrections to earlier docs:**
  - `ARMING_CHECK` → **`ARMING_SKIPCHK`** at this commit (a skip mask; 0 = skip nothing). CLAUDE.md's Hidden
    Configuration Audit §2 still says ARMING_CHECK (stale; already noted by the watcher build).
  - `RNGFND1_GNDCLEAR` (plan §1 S4, §3.3) → **`RNGFND1_GNDCLR`**.
- **TODO_SUPERVISOR placeholders (board/sensor/volume dependent):** EK3_FLOW_DELAY, FLOW_TYPE, FLOW_ORIENT_YAW,
  FLOW_POS_X/Y/Z, FLOW_ADDR, RNGFND1_TYPE, RNGFND1_MIN, RNGFND1_MAX, RNGFND1_GNDCLR, RNGFND1_POS_X/Y/Z, RNGFND1_ADDR,
  INS_POS1_X/Y/Z, FENCE_ALT_MAX, FENCE_MARGIN, BATT_LOW_VOLT, BATT_CRT_VOLT, FLTMODE_CH, FLTMODE1/4/6,
  LOG_FILE_BUFSIZE, COMPASS_USE2/3 (compass variant); plus SERIALn_PROTOCOL/BAUD for a serial rangefinder (n unknown).
- **Fence decision recorded in the file:** maximum-altitude fence only (`FENCE_TYPE 1`, `FENCE_ALT_MAX_TP 1` above
  home, `FENCE_ACTION 2` always land). Circle/polygon need a position (`AC_Fence.cpp:509-516`); "above terrain" needs a
  location and would breach permanently. The above-home height without a GPS home is a bench check (cards B6).

### C. R10: `docs/rung1_preregistration_draft.md` (DRAFT, for the user's sign-off)
- Sorties classified: B (bench), H (hand-carried, ~2 min), V (first hover, ~1.5–2 min) = VERIFICATION, never scored;
  R1…Rn = RESULT. Each verification length is justified in one line (standing rule).
- Profile: wiggle, take-off to h [TBD-S], hover 30 s, two laps of a rectangle at 0.3–0.5 m/s (~90 s), hover 10 s, land,
  wiggle. n = 5 (+1 spare, only for a §3.3 exclusion decided before any estimator runs).
- Metric: evo -a over **W = [t_to + 25 s, t_ld − 5 s]**, t_to/t_ld from MOCAP height > rest + 0.30 m (never from an
  estimator).
- **Replay-fidelity gate:** ≤ 1 cm position (horizontal and height), ≤ 0.1° yaw, Replay vs onboard XKF1 core 0; fail →
  "Replay EKF3", flight not excluded; bound confirmed/widened ONCE on verification logs, then fixed.
- **Timestamp rule:** EKF3 its own; UKF/FGO arrival − d_cap, d_cap [TBD-V] measured on verification logs only (ROFH
  interval + flow-vs-RISI-gyro cross-correlation during wiggles). Flagged: the port needs a capture-delay option.
- **Decision rule (mirrors the simulation's confirmatory test):** primary pair EKF3 vs FGO; claim "A lower" only if
  d_i < 0 on EVERY usable flight (5/5 p = 0.031, 4/4 p = 0.0625) AND the 95% t-CI excludes 0; < 4 usable → descriptive
  only. "Consistent with the simulation" only if the decision categories match.
- Limits listed (11 items, incl. the rangefinder-minimum problem below).

### D. R11: `docs/rung1_flight_cards.md` (DRAFT)
Roles (safety pilot, mocap operator, GS, observer), pre-session, bench B1–B8 (each with duration and why), hand-carried
card, first-hover card, the per-sortie result card, abort criteria, the post-sortie data-integrity checklist D1–D9
(LOG_REPLAY records present, RFRH continuity, DSF.Dp = 0, PARM readback, wiggles disarmed, mocap file present and synced),
end of day.

## Compile check: NOT RUN
- Prepared as instructed: a scratch `git worktree` of `rung1-geometry` with only the submodules a SITL Replay build
  needs (waf, mavlink, DroneCAN; `--reference` to the main checkout), and a build script for `./waf configure --board
  sitl; ./waf replay` under `heavy.py --wait-s 1800`.
- It never started: `BUILD_LOCK` was held throughout by the attribution study (pid 1322821), with two more heavy jobs
  queued. Per the brief ("skip it if the lock is held for long") the waiting `heavy.py` was stopped with SIGTERM
  before it acquired the lock (it held none), and then the triage put A on hold. The scratch worktree was removed
  (`git worktree remove --force --force` + `prune`); `~/ardupilot_ukf` lists only its original two worktrees.
- **So the R2 code is uncompiled.** It was written against the source read here (signatures of `AP_Param::get(const
  char*, float&)`, `hal.util->snprintf`, `AP_DAL_RangeFinder_Backend::get_pos_offset()`,
  `AP_DAL_InertialSensor::get_imu_pos_offset()`), but a compile error is possible.

## PARM ordering in the log (checked read-only, relevant to A)
- The port resolves its geometry ONCE, at its first `update()`. In Replay that is safe only if the log's `PARM`
  records come before the first replay frame.
- **On the two SITL logs checked it holds:** in `cl_a_tex_half` and `H_s1_r1` every geometry parameter (`EK3_FLOW_DELAY`,
  `EK3_HGT_DELAY`, `RNGFND1_MIN/_MAX/_POS_Z`, `FLOW_POS_Z`, `INS_POS1_Z`) is at message index 169–915, and the first
  `RFRH` at 1380/1390. Each logs 1396/1416 `PARM` records against 1379 names, i.e. a few later re-writes, none of them
  these parameters.
- **Not known for a real board's log** (logging may start before the parameter dump completes). Hence item 2 below.

## Left to do on A when it resumes
1. **Compile and regress** (the list above under "Must be re-verified").
2. **Robustness of the geometry timing (from the review):** resolve the geometry at `initialise()` rather than at the
   first `update()`; let the PARM hook also capture `EK3_FLOW_DELAY`, `EK3_HGT_DELAY`, `EK3_BCN_DELAY`; write a warning
   line to `ukf_geometry.csv` if a geometry `PARM` arrives after initialisation; label each source honestly
   ("param" / "log_parm" / "default"; today an `AP_Param::get` that returns the REGISTERED DEFAULT in Replay, before any
   PARM, would still be labelled "param"). EKF3 re-reads `_flowDelay_ms` on every sample; the port does not.
3. The capture-delay option (open question 2) and the GNDCLR initialisation (open question 1), each after a ruling.

## Open questions / follow-ups
1. **Rangefinder minimum vs resting height (rung-1 blocker if it applies):** the UKF port initialises only on a `Good`
   range sample above RNGFND1_MIN. With a sensor whose minimum exceeds the resting height (e.g. TF-Luna 0.2 m), it stays
   uninitialised on the ground and initialises mid-climb from the first in-range sample: the height is then right, but
   the roll/pitch come from the levelling average taken on the ground long before, and the velocity starts at 0
   during the climb. EKF3 uses `RNGFND1_GNDCLR` (`rngOnGnd`) instead. A port option (initialise from GNDCLR when
   disarmed and out-of-range-low) would mirror EKF3; it is a model/initialisation change → needs a ruling.
2. **Capture-time option in the port** (pre-registration §6): today the port uses EKF3's flow time with the logged
   EK3_FLOW_DELAY. The ruling wants the UKF/FGO at arrival − d_cap. Needs a small port change + regression.
3. Compass variant (supervisor); all TODO_SUPERVISOR values; fence above-home height without GPS home (bench B6).
4. The R2 Replay regression (above) when the build is allowed.
5. `minimal_real_flight_plan.md` §1/§3.3 and CLAUDE.md say `RNGFND1_GNDCLEAR`/`ARMING_CHECK`: stale names, to be
   corrected by whoever next edits them (not edited here).

## State at stop
- thesis_ws: committed on the worktree branch `worktree-agent-a28741f2c8a8ea439` (based on `fwd-camera` `c4e05a1`);
  not merged.
- `~/ardupilot_ukf`: branch `rung1-geometry` at `c25fa8980d` (ON HOLD); the scratch worktree removed and pruned;
  `ukf-jitter-fix` (checked out) untouched; `~/ardupilot_ukf/build` untouched.
- No locks held (the queued `heavy.py` was stopped before acquiring one); no simulator or flight touched.
