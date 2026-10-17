# Handover 2026-10-17: the methodology figure and tables, plus the compute and safety tables

*One stage. Built only from existing code, parameter files and documents: no simulation, no estimator result recomputed.
**Not edited:** numbers.md (CONTENT-FROZEN; `tools/check_numbers_frozen.py` PASS), METHODOLOGY, results, the frozen pack, and
the files in use by the other agent (`eval/figs_thesis.py`, `thesis_figures_combined.pdf`, `docs/thesis/figures_thesis/index.md`).*

## Outputs

The generator is `eval/figs_thesis_methods.py`. Run it with `/home/makerspace/venv-evo/bin/python eval/figs_thesis_methods.py`; it exits non-zero on any failure.

| proposed no. | files | content |
|---|---|---|
| Figure 3.1 | `docs/thesis/figures_thesis/methods_architecture.{pdf,png}` | system architecture (sensors, bridges, EKF3/UKF/FGO, offline / flight controller / companion, ExtNav path, both safety watchers, FLYING vs SHADOW) |
| Table 3.1 | `docs/thesis/tables/methods_estimator_design.{md,tex,png}` | estimator design: rows × EKF3/UKF/FGO, source per cell |
| Table 3.2 | `methods_noise_parity.*` | noise per sensor per estimator, offline and in flight |
| Table 3.3 | `methods_noise_exceptions.*` (2 pages) | 22 documented exceptions, each with its ruling, or "no ruling found" |
| Table 3.4 | `methods_experiment_matrix.*` (2 pages) | 1A, 1B (4 sub-rows), 1C, 2, 3, 4, 5, 5S |
| Table 8.1 | `realflight_compute.*` | compute and deployability, each value labelled MEASURED / ESTIMATED / DIAGNOSTIC |
| Table 8.2 | `realflight_safety_findings.*` (2 pages) | F2, F6, F7, F8, B8a, the FC refusal gap, H10, M1–M3, stock-firmware arming (G6), and G1–G11 summarised |
| index | `docs/thesis/figures_thesis/index_methods.md` | captions, the diagram's edge sources, cross-checks, every citation with its needle, and the gaps |

**File names are descriptive** (`methods_*`, `realflight_*`). M1/M2/M3 were not used as ids because they are the F8
mitigation codes printed in Table 8.2.

**Proposed numbering:**
- Chapter 3 (method): Figure 3.1 and Tables 3.1–3.4.
- Chapter 8 (towards real flights): Tables 8.1–8.2.

The offline-timing row of Table 8.1 could also go in Chapter 3. These are proposals: the chapter plan is still the user's to set (vocabulary §6).

**Not yet integrated:** the combined PDF and `index.md` are still to be merged in.

## Checks

- **Source checks: 316/316.** Every file:line in every cell, and every diagram edge, is stored as (file, line, verbatim needle). The generator asserts that the needle is on that exact line. ArduPilot citations point outside the repository and are read with `git show <rev>:<path>`, so they do not depend on the checked-out branch:
  - the thesis fork `~/ardupilot_ukf` @ `f30f6ffa2f` (branch `ukf-jitter-fix`);
  - the pinned `~/ardupilot` @ `7bac20cbcc`.
- **Every printed derived value is the checked string.** It is computed once into a variable used in both the cell and the check (counts, covariances, flash differences, keyframe times, the 12.5 ms period).
- **Vocabulary:** no D-number, log-record code (XKF1/XUKF/XFGO), "Phase 3" or "plan step 2(b)" in any cell outside the source column (grep of the rendered `.md`). Half real-time carries its explanation in the Table 3.4 and 8.1 notes.
- **Cross-checks: 30/30 EXACT.** The expected value is read from the cited line itself. The computed value goes through `rd()` from `eval/figs_thesis.py`. `rd()` is loaded by AST, function definitions only, because that module has no `__main__` guard and importing it would regenerate the other agent's outputs. The checks cover:
  - the GTSAM σ_c = NSE·√dt and covariance = NSE²·dt, against numbers.md §3 and the `fgo_core.py` literals;
  - EKF3's NSE defaults, read from source;
  - √dt, and the EKF3 12.5 ms period;
  - the UKF port's TARGET_DT, which equals EKF3's;
  - the NIS gates 9 / 25 and the heading χ² 9;
  - EKF3's effective ExtNav yaw σ (11.46°) and the 0.0873 rad threshold;
  - the flight counts: 9, 18, 90 replays, 12, 12;
  - the H743 flash differences (+24.2 kB and +23.8 kB);
  - the 33.3 ms and 66.7 ms keyframe times;
  - the count of 11 watcher gaps.
- **Viewing:**
  - The diagram was viewed composited on white and on #1e1e1e. It is a white rounded panel on a transparent background.
  - All 11 table pages were viewed. Column overflow was fixed by narrowing the characters-per-line estimate.

## Corrections to the brief, from the sources

- **Who flies.** In 1A, 1B, 2, 3 and 4 **simulator truth** flies (`AHRS_EKF_TYPE 10`, `consolidated_rerun.parm:11`). EKF3 runs live but passively, and the UKF and FGO are offline. EKF3 flies only in 1C, in 5 (the EKF3-flying set) and in the 5S reference run. The matrix uses vocabulary term 39.
- **ExtNav camera heading.** It reaches EKF3 (`EK3_SRC1_YAW 6`) and the UKF port (D17, `AHRS_UKF_EXTYAW`) in **1C with heading**. The FGO node takes `/forward_camera/heading_sent` instead. In Experiment 5, the wall tag gives ExtNav position + yaw. In **offline 1B**, EKF3 receives nothing (ruling M:2884), and the UKF/FGO read the frozen Phase 3 heading (`measurement_models.forward_events`), not a live bridge.
- **Two safety watchers.**
  - `sim/tools/wall_watch.py` (ground truth + pgrep liveness, acting through `fly_trial.py`) was used in 1C, 5 and 5S.
  - `realflight/watcher` (mocap + FC telemetry + beacons, one LAND, a HEARTBEAT gating FS_GCS) is tested only on the SITL bench. The 5S tests did **not** use it.
- **No separate AP_NavFGO library.** `AP_NavFGO.{h,cpp}` sits inside `libraries/AP_NavUKF/` in the fork. It receives the node's ODOMETRY (LOCAL_NED / NAIVE) on SERIAL3 (14558).
- **The Pi is notional in SITL.** Every process ran on the desktop. Pi timing is ESTIMATED (M:13651).
- **The F1 kernel is Cauchy** (k = 2.385, M:8281), not Huber.

## Could not be built from existing sources (reported, not filled)

1. EKF3 offline step time: none exists.
2. EKF3 flight-controller CPU, flash and RAM: not measured.
3. The FGO interface's flight-controller CPU: not estimated. Only an [E] note exists: ~100 buffered IMU steps at ~10 Hz (`board_firmware_plan.md:161`).
4. **No ruling found** for two code differences, both listed in Table 3.3, rows 5–6:
   - **(a)** the FGO has **no flow/range NIS gate** in either core: only a 4.2 rad/s flow clamp (`fgo_core.py:184`, C++ `fgo_core.cpp:144`). FGO_DESIGN recommends matched gates (`FGO_DESIGN.md:446`). It is recorded only as "no gate" (M:8659, M:8884).
   - **(b)** the UKF's FLOW_MAX is two-sided `abs()`, whereas FGO_DESIGN describes EKF3's test as signed and one-sided (`FGO_DESIGN.md:420`).
   - **These need a user ruling.**
5. **G6** (stock firmware arms without a watcher): the ruling is still open (M:13750).
6. **Thesis names** for F2, F6, F7, F8, B8a, H10 and M1–M3: the vocabulary has none. Table 8.2 uses descriptive proposals with the code in brackets, which needs a user ruling. F2/F6/F7 also collide with figure ids (glossary_flags.md:37-40).
7. **H5.2–H5.4** have only `tag_hold_design.md` sources. **Plan step 2(b)** and the static yaw sweep have no H label. Both are stated in the Table 3.4 note.

## Notes for integration

- `index_methods.md` follows `index.md`'s structure, so its items can be appended to the combined PDF by the `figs_thesis.py` owner. Its "used in" and "numbers.md rows" fields are replaced by the per-item source tables.
- The `.tex` uses `\scriptsize` with p-columns. It is checked for ASCII, braces and column counts only (no TeX on this machine). Tables 3.3, 3.4 and 8.2 will need `longtable` or a landscape page when typeset.
- Stale statements met in passing, not edited:
  - `AP_NavUKF.h:3-4` ("never drives the vehicle yet");
  - `h_ukf_tag.parm:3` ("NOT wired into any launcher");
  - `fgo_node.py:7`;
  - `run_trial.sh:128` (says VISION_POSITION_ESTIMATE; the code sends ODOMETRY);
  - `real_flight_readiness.md` (older Pi/CPU figures; G1–G4 rows show the pre-build status).
