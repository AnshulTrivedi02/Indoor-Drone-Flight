# Methodology fact sheets: index

*Created 2026-10-17. Line numbers are at commit `337c931` (branch `fwd-camera`). These are new files only; no existing file
was edited. They hold FINAL-STATE facts as short bullets, each with a `file:line` source. They are not chapter prose.*

**Rules applied in every sheet**
- **Numbers come only from `docs/thesis/numbers.md`**, cited `numbers.md:<line>` as the line stands in this worktree.
  - numbers.md is content-frozen. `python3 tools/check_numbers_frozen.py` was run at `337c931` and returned PASS.
  - numbers.md's own `M:L…` source cells point into the `563a989` snapshot, so they were never copied.
- **A needed number that is not in numbers.md** is tagged `[NOT IN numbers.md: <where it appears>]`. The full list is below.
- **The thesis vocabulary is used throughout** (`docs/thesis/thesis_vocabulary.md` at `337c931`).
  - The vocabulary and `methodology_definitions_draft.md` are being extended by another agent, with ordering footnotes and a
    definition of n. The sheets cite their current text and say so.
- **Values on numbers.md's not-recomputed list** (numbers.md:345-358) carry the label "measured before corrections; not
  recomputed".
- **Each sheet has the same four sections:** Facts, Appendix candidates, Flags (a) and Flags (b).
  - **Flags (a), superseded/corrected:** an item from METHODOLOGY, CLAUDE.md or another source that was later replaced. Both
    the item and what replaced it are cited.
  - **Flags (b), conflicts:** two sources that disagree. Both sides are cited.

## Index and counts

The counts are top-level bullets, counted by script.

| section | file | facts | appendix candidates | (a) flags | (b) flags |
|---|---|---|---|---|---|
| 3.1 Approach and fairness principles | `3.1_approach_fairness.md` | 34 | 10 | 8 | 3 |
| 3.2 Simulation environment | `3.2_simulation.md` | 40 | 13 | 8 | 9 |
| 3.3 Estimators | `3.3_estimators.md` | 49 | 17 | 16 | 10 |
| 3.4 How the estimators were run | `3.4_run_modes.md` | 23 | 8 | 6 | 4 |
| 3.5 Experiments 1–5 and 5S | `3.5_experiments.md` | 40 | 14 | 18 | 8 |
| 3.6 Metrics and statistics | `3.6_metrics_statistics.md` | 30 | 11 | 9 | 8 |
| 3.7 Verification process | `3.7_verification.md` | 34 | 10 | 6 | 5 |
| 3.8 Closed-loop safety framework | `3.8_closed_loop_safety.md` | 32 | 8 | 7 | 4 |
| **Total** | | **282** | **91** | **78** | **51** |

Grand total: 502 bullets.

## Numbers needed but not in numbers.md

There are 49 tags. Some quantities are tagged in more than one sheet. Grouped by kind, with the source each tag points to:

- **Criterion bounds.** These are pre-registered, so they live in METHODOLOGY:
  - closed-loop criteria: U1 ≥ 1.8 m (M:7350); B2 ≤ 6.0 m (M:4953); B3 p95 ≤ 1.0° and maximum ≤ 2.0° (M:4958); the B5
    gyro-rms bounds (M:4966); the validity criterion's +50 s (M:7361);
  - tag-hold criteria: the H5.1 bounds 0.05 / 0.15 m (M:10687-10688); the UKF drift bands (M:10691, M:10960-10965); the
    H5.6 re-lock bound ≤ 0.1 s (M:10955);
  - safety-test criteria: S-A1 3° / 5° (M:11295); the S-A3 sub-bounds 40 s, 15° and 1.0 m/s (M:11302-11306);
  - other bands: the Experiment 2 "similar" band 1.5× (M:10179); the heading accuracy bar (M:2727-2730).
- **Statistics:** the sign-test p 0.0625 at 6/7 (M:5650); the H1.3 verdict count 10/12 (M:3447).
- **Estimator configuration:**
  - the UKF's pseudo-yaw R 0.5 rad (ukf_core.py:46-47), its sigma-point α/β/κ (ukf_core.py:48), its initial bias σ
    (ukf_core.py:313-314) and its 0.5 m/s validity bound (M:5372);
  - the FGO's initial bias σ (fgo_core.py:38-39), its whole-flight batch LM cap of ≤ 50 iterations (M:10143) and the
    GTSAM version 4.2.1 (CLAUDE.md:71);
  - the tag model σ 0.05 m / 5° (M:10130); the EKF3 tag noise (tags_extnav.parm:7-8); the tag-fix validity range 0.9–2.8 m
    (M:11614);
  - the calibration-set σ_ψ (M:2855-2856); `VISO_DELAY_MS 38` (closedloop_heading.parm:19);
  - the ground-proximity flow-rule thresholds (M:7045-7050); EKF3's pre-arm gyro-z bias (M:7790-7791).
- **Simulation:**
  - Gazebo 8.14.0 and ros_gz_bridge 1.0.22 (CLAUDE.md:932, 934);
  - the downward camera's 30 Hz, HFOV and 640 × 480 (sim/reference/iris_with_standoffs.model.sdf:239-246); the flow focal
    length 554.0 px (flow_tracker.py:16);
  - the time-sync cost (M:3891); the old roll gains (M:4569-4575); the room_tags world geometry (sim/worlds/room_tags.sdf:2-5).
- **Safety framework:**
  - the crash rule, tilt > 60° and height < 0.5 m (sim/tools/wall_watch.py:7-9); the inner wall faces at ±9.9 m
    (wall_watch.py:5-6);
  - the room box ±4.4 m (closed_loop_run.sh:74; M:11874); the 2 m-clearance hold geometry W(−2.6, 0) (M:11873-11874);
  - the heartbeat timeout 3 s (fly_trial.py:305); the watcher latency ≤ 4 s (M:10986); `VERT_HOLD_MS` 15 s (M:11262);
    `MOT_THST_HOVER` 0.310 (M:11600).
- **Verification:** the old-vs-new row and flag counts (M:12778, M:13350); the 62 bags of the final re-run (M:12715).

## The most important flags

**(a) superseded or corrected**
- **H1.1 verdict.** "EKF3 lower" is WITHDRAWN and replaced by "no ordering claimed" (3.5, 3.6).
- **FGO noise and priors.** `biasAccOmegaInt` is now zero, and the FGO's initial σ is now 1° / 5°.
  - FGO_DESIGN.md:529-541 still describes the old value as "matched" (3.1, 3.3).
- **UKF prediction step.** It is not "0.0125 s, EKF3's values unchanged": the offline step is 15.00 ms, with per-second
  noise matched (3.1, 3.3).
- **Lateral flow sign and `FLOW_POS_Z`.** The lateral flow sign was corrected, and `FLOW_POS_Z` 0.13 → 0.25 (3.2, 3.3).
- **Contact windows and the B5 window.** The UKF contact window became [+146, +218] s, and the B5 window was fixed (3.5,
  3.6).
- **Re-lock time.** The re-lock time (H5.6) was redefined (3.5, 3.6).

**(b) conflicts**
- **`LOG_REPLAY`.** numbers.md:409 and CLAUDE.md:1900 say `LOG_REPLAY=0`, or not set, in every dataset. But
  consolidated_rerun.parm:12-14 sets 1 for the re-flown datasets (3.3, 3.6).
- **S-A2 bound for the UKF forced-invalid test.** It was pre-registered at 0.1 s (M:11299), and the re-tests were scored at
  0.75 s (M:12681; numbers.md:490). No amendment line was found (3.5, 3.8).
- **Tag-hold hypotheses.** H5.1 and H5.5 each have two wordings, and H5.2–H5.4 exist only in `tag_hold_design.md` (3.5).
- **UKF contact window against the scorer key** (numbers.md:471).
- **Cruise length:** 300 s (numbers.md:56) against "320 s cruise" (CLAUDE.md:1724) and ~302 s (M:7356).
- **Phase 5 provenance:** "126 inputs" (numbers.md:263) against 203 files (numbers.md:1336).
- **Withdrawn paired-test CI.** It is printed as [−1.16, −0.21] (numbers.md:228) and as [−1.20, −0.19] (M:6264). The
  pre-registration says df 6, and the run used df 5.
- **Manual launch.** The manual launch in CLAUDE.md omits `consolidated_rerun.parm` and `roll_rate_gains.parm`, which
  `run_trial.sh:299` loads (3.2).
- **Code line numbers have drifted.** numbers.md:377-378 cite `measurement_models.py` lines from the `563a989` snapshot;
  the same constants now sit at :186 and :191-192 (3.3).
