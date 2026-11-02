# Methodology fact sheets: index

*Created 2026-10-17 at commit `337c931` (branch `fwd-camera`); claims C1–C5/Q2/Q3/D17 applied to 3.3/3.5 at `4c783b5`;
**extended 2026-11-02 with sheet 3.9 (extension experiments E2–E6 and the attribution ablation) and updates to
3.3/3.4/3.6/3.7, at base commit `4861f3d`** (the E6 merge). These are FINAL-STATE facts as short bullets, each with a
`file:line` source. They are not chapter prose.*

**Rules applied in every sheet**
- **Numbers come only from `docs/thesis/numbers.md` or `docs/thesis/tier1/numbers_tier1.md`**, cited `numbers.md:<line>`
  or `numbers_tier1.md:<line>` as the line stands in this worktree. `numbers_tier1.md` was added for this pass: it holds
  the extension experiments' own numbers (E2–E6, pre-registered) and is never merged into `numbers.md`.
  - `numbers.md` is content-frozen. `python3 tools/check_numbers_frozen.py` returns PASS at `4861f3d`, unchanged from `337c931`.
  - `numbers.md`'s own `M:L…` source cells point into the `563a989` snapshot, so they were never copied.
  - `numbers_tier1.md` is its own separate, non-frozen file (`docs/thesis/tier1/numbers_tier1.md:1-25`); its own
    citations are exact-cross-checked against score jsons before being typed (same convention as `numbers.md`).
- **A needed number that is not in either file** is tagged `[NOT IN numbers.md: <where it appears>]` or, for bullets
  added or touched in the 2026-11-02 pass, `[NOT IN numbers files: <where it appears>]` (same meaning; the wording
  differs only by when the bullet was written). The full list is below.
- **The thesis vocabulary is used throughout** (`docs/thesis/thesis_vocabulary.md`, cited at whichever line this
  worktree carries; it has been extended since 2026-10-17, e.g. row 150 now holds the H1.3 wording that was at row
  145 when this pack was created — see Flags (a) below).
- **Values on numbers.md's not-recomputed list** (numbers.md:345-358) carry the label "measured before corrections; not
  recomputed".
- **Each sheet has the same four sections:** Facts, Appendix candidates, Flags (a) and Flags (b). Sheet 3.9 additionally
  groups its Facts under `### E2` … `### Ablation` subheadings; the bullet counter below still counts only the
  top-level `- ` bullets under each of the four `##` sections, so the subheadings do not change how it counts.
  - **Flags (a), superseded/corrected:** an item from METHODOLOGY, CLAUDE.md or another source that was later replaced. Both
    the item and what replaced it are cited.
  - **Flags (b), conflicts:** two sources that disagree. Both sides are cited.

## Base commit and what changed in the 2026-11-02 pass

- **Base commit:** `4861f3d` (branch `fwd-camera`, the E6 merge: "P1 FAIL 2/3, P2 FAIL (FGO 0/3, UKF 2/3), P3 FAIL 2/3
  each, P4 PASS 3/3 each; E6 decisions renumbered D80-D96"). Every citation added or edited in this pass is at this
  commit.
- **Line-number re-verification, done by script, not left as "unchanged bullets keep their 337c931 numbers".**
  `check_factsheets.py` (new, `docs/thesis/methodology_factsheets/check_factsheets.py`) re-resolved every
  `file:line` citation in all nine sheets against this worktree and re-matched every numeric token in a bullet that
  carries a `numbers.md`/`numbers_tier1.md` citation (or a `[NOT IN …]` tag) against the text on its cited line(s).
  It found and fixed **7 genuine line-drift citations** that no longer pointed at their claimed content at `4861f3d`
  (all pre-existing, from before this pass, not introduced by it):
  - `eval/cruise_window.py:10-37` → `:10-33` (3.6; the file shrank to 33 lines);
  - `M:4569-4575` → `M:4569-4576` (3.2; the roll-gain `D` value sits one line further down);
  - `ukf_core.py:313-314` → `:314-315` (3.3; the UKF initial bias σ lines);
  - `fgo_core.py:38-39` → `:39-40` (3.3; the FGO initial bias σ lines, same cause);
  - `thesis_vocabulary.md:145` → `:150` (3.5; the H1.3 wording moved when the vocabulary was extended; :145 is now blank);
  - `M:1711-1716, M:1857-1862` → add `M:1869` (3.5; the dejittered-baseline "0.40 m floor" sentence is at a line
    outside the originally-cited range);
  - `M:11299`/`M:12681` S-A2 citations were correct, but the matching `thesis_values_provenance.md` "row 20" needed
    its real line (`:78`) added, since "row N" alone cannot be checked as a citation (3.5).
  - After each fix, `python3 docs/thesis/methodology_factsheets/check_factsheets.py` returns **0 failures on all nine
    sheets** (see the counts below), and `python3 docs/thesis/tier1/check_claims_applied.py` still returns **58/58**.
- **A pre-existing, unrelated defect was also fixed while editing these two files**: `3.4_run_modes.md` and
  `3.6_metrics_statistics.md` each ended with two stray lines, `</content>` and `</invoke>` (a tool-output leak from
  the original 2026-10-17 authoring pass, baked into the committed file). Removed; no bullet content was lost (the
  last real bullet in each file was already complete).
- **3.5's three claim-pass NOT-IN tags for E2/E3/E5 (added at `4c783b5`) are now direct `numbers_tier1.md` citations**,
  because `numbers_tier1.md` did not exist when those tags were written. Converted: the E5 UKF-landmark-states
  bullet, the E3 wrong-re-identification bullet, the E2 tag-count bullet, and the separate H1.3 NOT-IN tag (also now a
  direct `M:3447` citation, since the exact wording is there). See Flags (a).
- **New sheet `3.9_extension_experiments.md`**: E2–E6 and the attribution ablation, with the purpose, recordings,
  arms, metrics, pre-registration dates and amendments, gates and labelled verdicts for each.
- **Updated existing sheets** (facts the extensions changed or added; no existing fact was deleted):
  - **3.3 Estimators:** three new facts — the E3 robust tag-factor FGO (Cauchy k = 2.385 on tag landmark factors
    only, an estimator variant never merged into the thesis FGO), the E5 landmark UKF design, and E6's `--tag-map`
    flag — plus the citation fixes above.
  - **3.4 How the estimators were run:** three new facts — E2–E6/the ablation are offline replay of existing
    recordings (E6 excepted, which adds 4 new flights), E6's map-supplied replay as a new sub-mode, and the "one job
    at a time via `heavy.py`" run discipline used for every tier-1 run (contrast with the stored Experiment 2/3
    results' 6-parallel batches).
  - **3.6 Metrics and statistics:** six new facts — the tier-1 extension verdict vocabulary (a narrower scheme than
    the main thesis's, with its own NOT RUN/NOT MET senses), map error (E6), gap retention R (the ablation,
    EXPLORATORY), effective mislabel rate (E3), E6's two-sided range-band method, and a pointer to 3.9.
  - **3.7 Verification process:** five new facts — the tier-1 checksum guard (new verification mechanism: scope,
    STOP-AND-REPORT rule, every verify IDENTICAL), the supplementary code snapshots for E5/E6's new code, the
    reproduction-gate pattern (G0-L/G0-UKF/G-E4/G-E4′), the exact cross-check scripts (one per experiment, string
    equality, 0 mismatches), and the ablation's own identity gate.
  - **3.1, 3.2, 3.5, 3.8** were checked for extension-related facts needing a change: 3.5's loop-closure scope
    (claims C1–C3) was already applied at `4c783b5` and only needed its citations fixed (above); 3.1, 3.2 and 3.8 had
    no fact the extensions changed or scoped, so neither gained a new bullet in this pass.

## Index and counts

The counts are top-level bullets, counted by script (`check_factsheets.py`; a "- " line at zero indentation under
each of the four `##` sections — indented `  - ` / `  · ` sub-items are not counted separately, matching the
2026-10-17 convention).

| section | file | facts | appendix candidates | (a) flags | (b) flags |
|---|---|---|---|---|---|
| 3.1 Approach and fairness principles | `3.1_approach_fairness.md` | 34 | 10 | 8 | 3 |
| 3.2 Simulation environment | `3.2_simulation.md` | 40 | 13 | 8 | 9 |
| 3.3 Estimators | `3.3_estimators.md` | 52 | 17 | 16 | 10 |
| 3.4 How the estimators were run | `3.4_run_modes.md` | 26 | 8 | 6 | 4 |
| 3.5 Experiments 1–5 and 5S | `3.5_experiments.md` | 40 | 14 | 18 | 8 |
| 3.6 Metrics and statistics | `3.6_metrics_statistics.md` | 36 | 11 | 9 | 8 |
| 3.7 Verification process | `3.7_verification.md` | 39 | 10 | 6 | 5 |
| 3.8 Closed-loop safety framework | `3.8_closed_loop_safety.md` | 32 | 8 | 7 | 4 |
| 3.9 Extension experiments E2–E6 and the attribution ablation | `3.9_extension_experiments.md` | 48 | 8 | 5 | 4 |
| **Total** | | **347** | **99** | **83** | **55** |

Grand total: 584 bullets (up from 502 at `337c931`/`4c783b5`: +3 in 3.3, +3 in 3.4, +6 in 3.6, +5 in 3.7, +48 new in
3.9, +0 net elsewhere).

## Numbers needed but not in numbers.md or numbers_tier1.md

58 tagged values across the nine sheets (grep-counted, `check_factsheets.py` resolves every one of them as a
citation; none is a checker failure — a NOT-IN tag only means the value is not in `numbers.md`/`numbers_tier1.md`
itself, not that it is uncited). Grouped by kind, with the source each tag points to:

- **Criterion bounds (pre-registered, so they live in METHODOLOGY or a tier-1/ablation pre-registration file):**
  - closed-loop criteria: U1 ≥ 1.8 m (M:7350-7351); B2 ≤ 6.0 m (M:4953); B3 p95 ≤ 1.0° and maximum ≤ 2.0° (M:4958);
    the B5 gyro-rms bounds (M:4966); the validity criterion's +50 s (M:7361); the Experiment 2 "similar" band 1.5×
    (M:10179); the heading accuracy bar (M:2727-2730);
  - tag-hold criteria: the H5.1 bounds 0.05 / 0.15 m (M:10687-10688); the UKF drift bands (M:10691, M:10960-10965);
    the H5.6 re-lock bound ≤ 0.1 s (M:10955);
  - safety-test criteria: S-A1 3° / 5° (M:11295); the S-A3 sub-bounds 40 s, 15° and 1.0 m/s (M:11302-11306);
  - **the attribution ablation's gap-retention-R formula and pass rule** (`ablation/preregistration.md:217-220`; new in
    this pass, 3.6).
- **Statistics:** the sign-test p 0.0625 at 6/7 (M:5650).
- **Estimator configuration:**
  - the UKF's pseudo-yaw R 0.5 rad (ukf_core.py:46-47), its sigma-point α/β/κ (ukf_core.py:48), its initial bias σ
    (ukf_core.py:314-315) and its 0.5 m/s validity bound (M:5372);
  - the FGO's initial bias σ (fgo_core.py:39-40), its whole-flight batch LM cap of ≤ 50 iterations (M:10143) and the
    GTSAM version 4.2.1 (CLAUDE.md:71);
  - the tag model σ 0.05 m / 5° (M:10130); the EKF3 tag noise (tags_extnav.parm:7-8); the tag-fix validity range 0.9–2.8 m
    (M:11614);
  - the calibration-set σ_ψ (M:2855-2856); `VISO_DELAY_MS 38` (closedloop_heading.parm:19);
  - the ground-proximity flow-rule thresholds (M:7045-7050); EKF3's pre-arm gyro-z bias (M:7790-7791);
  - E4's W = 0.5 s median step time, DIAGNOSTIC (`tier1/e4_results.md:169`, 3.3).
- **Simulation:**
  - Gazebo 8.14.0 and ros_gz_bridge 1.0.22 (CLAUDE.md:932, 934);
  - the downward camera's 30 Hz, HFOV and 640 × 480 (sim/reference/iris_with_standoffs.model.sdf:239-246); the flow focal
    length 554.0 px (flow_tracker.py:16);
  - the time-sync cost (M:3891); the old roll gains (M:4569-4576, corrected — see above); the room_tags world geometry
    (sim/worlds/room_tags.sdf:2-5).
- **Safety framework:**
  - the crash rule, tilt > 60° and height < 0.5 m (sim/tools/wall_watch.py:7-9); the inner wall faces at ±9.9 m
    (wall_watch.py:5-6);
  - the room box ±4.4 m (closed_loop_run.sh:74; M:11874); the 2 m-clearance hold geometry W(−2.6, 0) (M:11873-11874);
  - the heartbeat timeout 3 s (fly_trial.py:305); the watcher latency ≤ 4 s (M:10986); `VERT_HOLD_MS` 15 s (M:11262);
    `MOT_THST_HOVER` 0.310 (M:11600).
- **Verification:** the old-vs-new row and flag counts (M:12778, M:13350); the 62 bags of the final re-run (M:12715).
- **Extension experiments and the attribution ablation (new group, added 2026-11-02, sheet 3.9 unless noted):**
  - the ablation's own three verdicts, since `ablation_numbers.md` is not `numbers.md`/`numbers_tier1.md`: P1
    (`ablation_numbers.md:135-140`), P2 (`:141`), P3 (`:142`);
  - the ablation's step-time ladder, DIAGNOSTIC (`ablation_numbers.md:192-194`);
  - the ruled thesis paragraph quoting the ablation's plain-language reading (`discussion_material.md:9-15`, itself
    traced line by line to `ablation_numbers.md` by `docs/thesis/ablation/check_discussion.py`, 18/18).

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
- **Three claim-pass NOT-IN tags became direct citations once `numbers_tier1.md` existed (2026-11-02).** The E5
  (UKF-landmark-states), E3 (wrong-re-identification) and E2 (tag-count) bullets in 3.5, and the separate H1.3
  verdict-count bullet, previously pointed at `tier1/e*_results.md` section numbers or a bare vocabulary row; they
  now cite exact `numbers_tier1.md` lines (and `thesis_vocabulary.md:150`, not the now-blank `:145`) (3.5).
- **E4's "27–28 ms" and cap-10-convergence bullets in 3.3 kept their rounded wording** (asserted verbatim by
  `check_claims_applied.py`) **but gained direct `numbers_tier1.md` citations** alongside the pre-existing
  `tier1/e4_results.md` section references, rather than relying on the section reference alone (3.3).
- **The loop-closure claim's scope (claims C1–C3, applied at `4c783b5`) is unchanged by E6.** E6 studies map reuse
  with correct tag IDs on condition A only (`e6_preregistration.md:10`); it does not revisit E2's tag-count scoping
  or E3's wrong-ID scoping (3.5, 3.9).

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
- **"NOT MET" means two different things across the main experiments and the tier-1 extensions (new, 2026-11-02).**
  The main-experiment vocabulary's sense is a pre-registered rule that was applied and gave a "no ordering" outcome
  (thesis_vocabulary.md:530). `preregistration.md` §0.5's tier-1 sense is narrower: a crashed run or a failed gate
  only, with FAIL used for a criterion whose count was not reached. E3's 2026-10-22 ruling used the main-experiment
  sense for a genuinely diverged run and was clarified the same day to the tier-1 FAIL sense
  (`tier1/preregistration.md:168-180, 409-424`). Both wordings are on the record (3.6, 3.9).
- **E6's P2 bands and their band-width method are two different kinds of number (new, 2026-11-02).** The band
  numbers themselves are computed from a stored repeat spread; the one-range-width-each-side method that produced
  them is itself "judgement, not derived from data" (D87) (3.9).
