# Handover, 2026-10-11: rung 1, the converter merged and proven; R7/R8 unheld and fixed; the scorer on a pre-registered JSON

**Stage:** one stage agent. Coding, light tests and two light replays under `heavy.py`. No flights, no simulator.
METHODOLOGY.md and numbers.md NOT edited. Stored trial data only read (one packed bag decompressed to the scratchpad,
checked against `PACKED.txt`, deleted).
Branch: `worktree-agent-a9fbc9cfb2e80625f`, reset to `fwd-camera` `bccbc78` first. NOT merged into `fwd-camera`.
Implements METHODOLOGY "RULING (user, 2026-10-11): PLAN AND BUILD TOWARDS REAL FLIGHTS", item 1 (rung-1 software).

## A. The converter (R1): merged, proof (b) PASS, smoke PASS after a fix

- **Merged** `worktree-agent-a323ce1f90a749262` (`eb629a6`). One conflict, in `fgo_replay.py`: both the events-mode
  block and the `INIT_YAW_SIGMA_RAD` block (the initial-yaw correction) are kept. The events-mode output directory also
  carries the `_iy<value>` suffix. `fgo_core.py` auto-merged: the converter's `geom` keyword sits next to the new
  `YAW0_SIGMA`/`ROLLPITCH0_SIGMA`.
- **(b) default-unchanged replay: PASS.** One bag-mode replay of `cl_a_tex_half` (`0.25 2`) through the merged
  `fgo_replay.py` on the CURRENT `fgo_core`. `fgo_traj.tum`, `ground_truth.tum` and `bgz_series.txt` are
  **byte-identical** to the STORED output of the FGO-only re-run (2026-10-10 18:51). It ran at the merge commit and again
  at `fcd67df`. sha256 values are in `eval/results/r1_converter/proofs_2026-10-11.txt`. No `fgo/` code changed on
  `fwd-camera` after that output was written (the last change is `5e0eba5`, 13:00).
- **Events-mode smoke (`eval/r1_followup_replays.sh smoke`):**
  - **The first run was OOM-killed** at 13.8 GB.
  - **Cause:** `np.load` on an `.npz` is lazy. Each `_Z["imu_acc"][i]` re-read the whole array, and every stored row was
    a view that pinned its own full copy, so memory grew as O(N²).
  - **Fix (`b9da351`):** every array is loaded once and the rows are copied. The edit is inside `if EVENTS:`, so the bag
    path is unchanged, and (b) re-passed after it.
  - **The re-run passes end to end:** 2 565 keyframes, 2 345 flow and 1 710 range factors, take-off detected at
    28.05 s (arm 24.15 s).
  - Scale and flow residual equal the bag run's: |V| 0.4881 vs 0.4879 m/s; residual −0.0057/−0.0055 vs −0.0058/−0.0058.
  - **Plumbing only, not a result.** The replay's `[result]`/`[yaw]` corridor diagnostics do not apply to this flight.
- **Still open from the R1 handover:**
  - the derotation ruling (now given: the 2026-10-11 ruling, D18, own bias-corrected gyro; the converter already does
    this for the FGO);
  - the FGO-from-BIN vs FGO-from-bag acceptance band on the full flight;
  - the C++ FGO's events input;
  - pre-registering d_flow and d_range from verification logs.

## B. Mocap recorder (R7) and alignment (R8): unheld, three defects fixed, adapter unified

| defect | fix | tests |
|---|---|---|
| **R8 crashes on a disarmed hand-carry log** (`default_windows` indexed the first ARM record; `land` indexed an empty rangefinder array) | `resolve_windows()` computes defaults ONLY for missing `--early/--late/--init-seg`. With no ARM record and anything missing, it stops with a message naming all three arguments. The old rule is kept as `legacy_windows()` and exits cleanly. `main(argv)` is testable. | `eval/mocap_align_test.py`: no ARM → clear SystemExit; partly given → exit; all given → aligns (< 1 ms) |
| **R8's default early window missed the pre-arm sync wiggle** | Defaults are now the two DISARMED wiggle bursts (`sync_bursts`): the last burst of \|ω\| > 2 rad/s before the first arming, and the first after the last disarming, each ± 2 s (0.1 s boxcar; bursts merged across gaps < 1 s; bursts < 1 s ignored). 2 rad/s is the flight cards' D6 figure. A missing burst stops the run, naming the argument. Grid points outside either record are now MASKED (`np.interp` used to hold the end value as fake flat data). The JSON records `window_sources` and `sync_window_rule`. | synthetic flight (`synth_flight(..., wiggle_gain=2.0)`): the default covers the wiggle at boot+7…13, arm at boot+15, mapped-time error < 1 ms; only missing windows are defaulted; no disarm → `--late` requested; a mocap take starting mid-wiggle is masked, < 1 ms |
| **R7 dropped the rest of a flight after a frame-counter reset** | The recorder now starts a new **segment**: (a) at once on a backward jump > 100 frames; (b) after 10 consecutive, mutually increasing would-be rejections, which are HELD and then written, so none are lost; (c) on a mocap-clock step backwards (also a clock fault). Each restart is logged in `restarts` (kind, frames and t_mocap/t_rx before and after), and that body's state is reset, so there are no spurious gaps or faults. New CSV column `segment`. **`export.py`** refuses a multi-segment log whose t_mocap is not increasing in recording order unless `--segment N` is given; it allows one with a continuous mocap clock, or `--time rx`. | `realflight/mocap/tests/` (+5): large jump with a duplicate inside segment 2; small jump (held run written, no frame lost); 5 re-sent frames stay duplicates; Motive restart (export refused, then `--segment 0/1`); clock reset with increasing frames |

- **Adapter unified:** `realflight/mcp1.py` is the ONE module: the packet, `MocapSample`, `PoseSource`,
  `UdpPoseSource` and `pose_stamped_to_sample`.
  - `realflight/watcher/mocap.py` re-exports it. Its requirements docstring is kept, and its behaviour is unchanged
    (OS-default receive buffer).
  - `realflight/mocap/source.py` re-exports it with a subclass whose default `SO_RCVBUF` is 1 MiB, as before.
  - **The watcher's 73 tests pass**; all of `realflight/` gives 83 passed.
- **The synthetic R8 validation is unchanged:** `mocap_align_validate.py synthetic` (8 seeds) reproduces the stored
  summary exactly, which shows the masking does not move it.
- **The stored SITL R8 numbers** (`eval/results/r1_mocap_sync/`) used the old arm-anchored windows, because SITL logs have
  no wiggles. `selftest` and `run_sitl` now call `legacy_windows` and were not re-run.
- `docs/rung1_flight_cards.md` D8 is updated to the new default.
- **Not done:**
  - the 25 Hz `IMU` fallback in R8 still fails with the fine-fit settings (do not use `--gyro-src IMU`);
  - the vendor forwarder (system unknown);
  - absolute sync accuracy on real data (needs the R13 log);
  - `mocap_align`'s default `--init-seg` (arm to arm + 30 s) still lies in the hover. This does not affect scoring,
    since the scorer re-aligns every estimator, but the 4-DoF frame in `mocap_align.json` is poorly defined for this
    profile.

## C. The scorer with a pre-registered window (R9/R10)

- **`eval/real_score.py` reads a STRICT pre-registration JSON** (`load_prereg`):
  - every key is required, unknown keys are refused, and nothing is defaulted;
  - `t_max_diff_s` must be 0.05 (three_way_eval's call).
- **Sections:**

  | section | content |
  |---|---|
  | `window` | `airborne` / `speed` / `fixed` |
  | `metrics` | primary `evo_ape_a_se3` \| `ate_4dof` |
  | `drift` | NEW `motion_onset_path` (or `window_start_time` for regressions) |
  | `estimator_records` | `--est-bin LABEL=REC` must equal the registered record; a TUM needs `"TUM"` |
  | `clock_map` (optional) | with `--mocap-align-json`, refuses a flight aligned with non-default windows or a different burst rule |

- **The output** carries `primary` per estimator, each estimator's record, and the prereg's sha256.
- **Tests** (`eval/real_score_test.py`, 8, pass):
  - the old 3 tests;
  - the motion-onset segment skips the hover (the old segment is refused);
  - strictness (7 bad variants);
  - the JSON drives the window (+5 s) and the primary metric through `main()`;
  - the record mismatch is refused;
  - the clock-map check;
  - the draft JSON loads and equals the tested definitions.
- **Regression** (`eval/results/r1_scorer/regression_dsn_tex_r1_strict_prereg_2026-10-11.json`), against
  `three_way_eval`'s call on the CURRENT stored outputs:
  - **UKF 3.983563, identical**;
  - **FGO 4.04733, identical**. It was 4.067897 before the FGO-only re-run; the new value matches numbers.md's 4.05;
  - the `speed` rule reproduces [30.348, 333.041].
- **The draft is unheld:** `docs/rung1_preregistration_draft.md` is still marked **DRAFT for user sign-off**, and
  `docs/rung1_preregistration_draft.json` holds the machine-readable values. `eval/real_score_prereg_example.json` is
  removed.
- **Both known defects are fixed:**
  1. **The drift segment** runs from the mocap motion onset (> 0.15 m/s for 1 s) for 2.0 m of travel, which is the start
     of the first leg. 2.0 m must be ≤ the first leg [TBD-S].
  2. **The clock-map windows** are the disarmed wiggle bursts, found by `mocap_align`'s default and checked by the
     scorer. A missing wiggle is §3.3 exclusion item 3, and windows are never set by hand for a result flight.
- **Also corrected:**
  - §4.2: the ground level is now the code's 5th percentile, not "the median before arming";
  - §9 limit 8: the UKF/FGO derotate with their OWN bias-corrected `RISI` gyro (ruling 2026-10-11, D18), not `ROFH.G`.
- **Proposed for sign-off:**
  - **Primary metric: evo -a SE(3).** §7's sim-to-real statement compares decision categories, and all simulation
    categories were decided on evo -a. The 4-DoF fit is secondary; it agrees to 1 mm on SITL.
  - **UKF record: `XUKO`.** `XKF1` logs EKF3's current-time output predictor (`AP_NavEKF3_Logging.cpp:26-27` →
    `AP_NavEKF3_Outputs.cpp:257-263`, `outputDataNew`, checked in source). `XUKO` is the port's current-time output.
    `XUKF` (the delayed horizon) is the secondary row `UKF_horizon`, and onboard EKF3 is `EKF3_onboard`.
- `eval/results/r1_scorer/e2e_cl_ukf_clockmap.py` (a stored script of a past run) now points at the draft. A comment
  says a re-run needs a prereg without `clock_map` and with `UKF_fused`.

## State at stop

- **Commits on the branch:** `4608637` (merge), `b9da351` (npz fix and adapter unification), `0d04efe` (R7/R8),
  `fcd67df` (R9/R10), and the handover commit after them.
- No locks held. No uncommitted work, apart from the untracked files the checkout already had.

## Follow-ups

1. User sign-off on the draft: the primary metric, `XUKO`, the drift segment (init_path_m vs the leg length), and the
   other §10 items.
2. Merge this branch into `fwd-camera`. It carries the converter merge.
3. The R1 acceptance band on the full `cl_a_tex_half` (FGO-from-BIN vs FGO-from-bag).
4. R8: remove or re-validate the 25 Hz IMU path. Decide whether `mocap_align`'s default init segment should also use
   the motion-onset rule.
