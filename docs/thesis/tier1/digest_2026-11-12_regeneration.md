# Digest: post-lock results and thesis regeneration (2026-11-11 to 2026-11-12)

All new results were final on 2026-11-12, before the 2026-11-14 12:00 cut-off. numbers.md is unchanged (content-frozen; `tools/check_numbers_frozen.py` PASS). Every new number lives in a new, exact-checked numbers file, and the thesis tables, figures and captions were regenerated from those files. Head at the time of writing: `548a796` (branch `fwd-camera`, pushed).

## 1. New results (old against new)

| Item | Result now | Before | Source |
|---|---|---|---|
| 1C no heading, EKF3, full real time (n = 3) | **3/3** inside [+155, +215] s; 174.9 / 181.4 / 186.2 s | n = 1: +186.2 s PASS | `closed_loop_extras/numbers_extras.md` |
| 1C no heading, EKF3, half real time (n = 3) | **1/3**; 242.1 / 178.9 / 268.3 s, spread 178.9–268.3 s (one inside, two after the window) | n = 1: +242.1 s, after the window | same |
| 1C no heading, UKF, full real time, final port `abb0357d` (n = 3) | **2/3** inside [+146, +218] s; 177.1 / 138.3 / 162.8 s (138.3 s before the window) | n = 1 on the earlier port only (+163.0 s): now superseded, earlier build | same |
| 1C no heading, UKF, half real time (n = 3) | **3/3**; 165.9 / 163.7 / 152.9 s | n = 1: +165.9 s PASS | same |
| 1C no heading, FGO, half real time, corrected priors (n = 3) | **2/3** inside [+145, +196] s; 166.7 / 193.9 / 203.5 s | n = 1, original priors: +169.9 s PASS (superseded: original priors) | `refly_priors/numbers_refly.md` |
| 1C with heading, FGO, corrected priors | **3/3** all B1–B5 and S2 | 3/3 (original priors, superseded) | same |
| Experiment 5 hold, FGO flying, corrected priors | H5.1 bounds 3/3 (mean 7.1–8.7 mm, max 15.0–25.5 mm); H5.5 bands 12/12; re-lock 12/12; no lockout; yaw wander −0.16 / +0.49 / +0.68° | all met (original priors, superseded) | same |
| H5.2, H5.3, H5.4a, H5.4b (comparatives, with the FGO on corrected priors) | all FAIL (0/3), unchanged | all FAIL | same |
| 1B EKF3 + camera heading via Replay (5° floor), with matched 5° UKF/FGO arms | DESCRIPTIVE: on textured walls/floor EKF3 0.13–0.16 m with heading against 3.6–4.1 m without (UKF 0.13–0.14 m, FGO 0.05–0.06 m at 5°); no position bound without flow (transition, blank †) | no offline EKF3 heading arm | `ekf3_heading_replay/numbers_ekf3_heading.md` |
| FGO flow/range gating, read-only count (DIAGNOSTIC) | textured flow factors that EKF3-style gates would reject: 0.01 % (5 of 89,490); FLOW_MAX one-sided and two-sided counts identical | not counted | `diagnostics/numbers_fgo_gate_count.md` |
| Per-flight with-heading values (EKF3 full Python/C++, EKF3 half, original FGO hard-gated/robust) | per-flight B2/B3/B4 values (ranges only before) | ranges only | `numbers_cl_heading_perflight.md` |

Every EKF3 + heading value carries the 5° floor caveat. No comparison across real-time factors is claimed (D21).

## 2. Verdict changes

- **H1.8 (1C, no heading):** now reported per estimator and speed as **REPORTED k/3 (no set rule)** (D144, D149): EKF3 full 3/3, EKF3 half 1/3, UKF full 2/3, UKF half 3/3, FGO half 2/3. The original single flights stay as recorded ("as recorded (n = 1; flight 1 of the n = 3 cell)"); the UKF old-port flight and the original-prior FGO flight are superseded (appendix, not counted).
- **H1.9 FGO:** 3/3 PASS, unchanged (now on corrected priors).
- **Experiment 5 FGO rows (H5.1-as-applied, H5.5, H5.6, H5.7) and comparatives H5.2–H5.4b:** no verdict word changed; values replaced with the corrected-prior re-fly.
- **New DESCRIPTIVE rows:** 1B-H1, 1B-H2, 1B-H3 (EKF3 + heading via Replay; no verdicts).
- **Category totals (R1 parts, reconciled with TA_verdicts):** PASS 24 → 24; FAIL AS WORDED 4 → 4; NOT MET 17 → 17; WITHDRAWN 1 → 1; DESCRIPTIVE 2 → 5; REPORTED k/3 0 → 5. Total 48 → 56 parts, 35 → 38 labels; TA_verdicts 88 → 96 rows, plus a 13-row superseded appendix. (The PASS total is unchanged because H1.8 FGO's original PASS left the counted table while the new "H5.1 bounds applied to the FGO-flying set" row entered it.)

## 3. Changed text outside the tables

- **Table 3.3:** row 5 (FGO gating) gains the read-only count; row 2 records the reopened EKF3 offline heading arm (D131, D132); row 6 now "counted, identical"; row 11 marks the original-prior FGO results superseded. Row 23 (`VISO_DELAY_MS` 15) present and unchanged.
- **limitations.md:** new item 6 (the gating count).
- **Fact sheets 3.1, 3.3, 3.4, 3.5, 3.8 (+README):** n = 3 cells; corrected-prior FGO current; EKF3 heading reopening; D150 H5.1 wording; erratum E3 folded in (S-A2 bound for UKF (a) is 0.1 s).
- **thesis_vocabulary.md:** build labels ("final FGO" = corrected priors; "superseded: original priors" / "superseded: earlier build"); new terms "REPORTED k/3 (no set rule)" and "EKF3 + heading (5° floor)".
- **Captions:** F2, F9 (contact time and priors; verdict pointers to the new rows), A1–A3 (priors), R3 (EKF3's offline heading arm is now in Table 4.1b; pointer kept).
- **New tables:** Table 4.1b (`T2B`, 1B EKF3 + heading with the matched 5° arms; OQ-R3: the D70 closed-loop picture is candidate A20, labelled "closed loop, picture only, not scored"; this table is the scored arm, "offline Replay, 5° floor") and Table 4.3b (`T4F`, 1C full real time n = 3 cells).

## 4. Files to replace in the writing project

The writing pack (`docs/thesis/writing_pack/`, 78 files, every copy byte-identical to HEAD, plus `new_2026-11-11/` with 10 files) was rebuilt. Relative to the pack as it was before the regeneration:

**New:**
- `figures_thesis/A1_closed_loop_builds_p1.pdf`
- `figures_thesis/A1_closed_loop_builds_p2.pdf`
- `tables/T2B_ekf3_heading_replay.md`
- `tables/T4F_closed_loop_full_speed.md`

**Changed (replace):**
- `figures_thesis/A2_H_and_safety_p1.pdf`
- `figures_thesis/A2_H_and_safety_p2.pdf`
- `figures_thesis/A2_H_and_safety_p3.pdf`
- `figures_thesis/A3_F1_cost_ablations_p1.pdf`
- `figures_thesis/A3_F1_cost_ablations_p2.pdf`
- `figures_thesis/captions/A1.md`
- `figures_thesis/captions/A2.md`
- `figures_thesis/captions/A3.md`
- `figures_thesis/captions/F2.md`
- `figures_thesis/captions/F9.md`
- `figures_thesis/captions/R3.md`
- `figures_thesis/F2_heading_stops_sideways_drift.pdf`
- `figures_thesis/F5_T_tags_known_positions.pdf`
- `figures_thesis/F6_O_outdoor_indoor.pdf`
- `figures_thesis/F7_L_loop_closure.pdf`
- `figures_thesis/F9_heading_error_closed_loop.pdf`
- `figures_thesis/thesis_figures_combined.pdf`
- `limitations.md`
- `methodology_factsheets/3.1_approach_fairness.md`
- `methodology_factsheets/3.3_estimators.md`
- `methodology_factsheets/3.4_run_modes.md`
- `methodology_factsheets/3.5_experiments.md`
- `methodology_factsheets/3.8_closed_loop_safety.md`
- `methodology_factsheets/README.md`
- `tables/methods_noise_exceptions.md`
- `tables/R1_hypothesis_scorecard.md`
- `tables/R4_information_vs_estimator.md`
- `tables/T1_scorecard.md`
- `tables/T2_accuracy_heading.md`
- `tables/T3_blank_floor.md`
- `tables/T4_closed_loop.md`
- `tables/T5_H_tag_loss_drift.md`
- `tables/T7_failure_behaviour.md`
- `tables/TA_verdicts.md`
- `thesis_vocabulary.md`

**New in `new_2026-11-11/` since 2026-11-11 (all byte-checked):** `extras_preregistration.md`, `refly_preregistration.md` (with AMENDMENTS 1 and 2), `ekf3_heading_preregistration.md`, `numbers_extras.md`, `numbers_refly.md`, `numbers_cl_heading_perflight.md`, `numbers_ekf3_heading.md`, `ekf3_heading_results.md`, `numbers_fgo_gate_count.md`, `fgo_gate_count_results.md`; this digest is added as `digest_2026-11-12.md`.

## 5. Not regenerated (stale, listed rather than rebuilt)

- Candidate captions A13, A14, A16, A18 ("1 flight per estimator", the old `H1.8 FGO` pointer): stale; update if any is promoted.
- `docs/thesis/summary/` (results walkthrough, summary plots): an overview, not a number source; left as is.
- Drafts and records not in the pack (`final_restatement_draft.md`, `glossary.md`, `headline_claims_before_after.md`, `pending_items.md`): historical; left as is.
- R2 (corrections by discovery): no row added for the post-lock re-fly or the harness fix; optional.

## 6. Decisions and open items

Decisions D127–D150 (`docs/thesis/tier1/decisions_log.md`), pre-registration amendments 1 and 2 (FGO re-fly). Open: the checksum guard's repeated `--paths` (tool fix logged, not applied); the EKF3 Replay's 115-frame input-count gap (14 explained) and EKF3's per-fusion yaw test ratio (not recoverable from the logs); a cosmetic attribution of three T2/T3 checks in `figs_thesis.py`'s console output.

## Appendix: cell-level table changes (mechanical diff, `e8381ef` → `548a796`)

### T1_scorecard.md
- `Experiment 5: tag hold [i] · hold 7.8–7.9 mm (bands PASS; comparatives` col 4: `hold 8.3–8.6 mm (bands PASS; comparatives FAIL)` → `hold 7.3–8.3 mm (bands PASS; comparatives FAIL)`
- `Experiment 1C: closed loop (the estimator flies) [j] · 3/3 pass; max c` col 4: `3/3 pass; max cross-track ≤ 0.39 m (final FGO node, original priors)` → `3/3 pass; max cross-track ≤ 0.32 m (final FGO node, corrected priors)`
- notes: 2 footnote paragraph(s) changed or added

### T2_accuracy_heading.md
- notes: 1 footnote paragraph(s) changed or added

### T2B_ekf3_heading_replay.md (NEW TABLE)
- new table, 18 rows

### T3_blank_floor.md
- no cell change

### T4_closed_loop.md
- ADDED row `EKF3 (unmodified) · k/3 = 1/3 (window [+155, +215] s); flights +242.1 s (after window) / +`
- ADDED row `final UKF port · k/3 = 3/3 (window [+146, +218] s); flights +165.9 s (PASS) / +163.7 s (PA`
- ADDED row `final FGO node (corrected priors, 4c07374b/HEAD) · k/3 = 2/3 (window [+145, +196] s); flig`
- REMOVED/MOVED row `EKF3 (unmodified) · +242.1 s; window [+155, +215] s: MISS`
- REMOVED/MOVED row `final UKF port · +165.9 s; window [+146, +218] s: PASS`
- REMOVED/MOVED row `final FGO node (original priors) · +169.9 s; window [+145, +196] s: PASS`
- notes: 2 footnote paragraph(s) changed or added

### T4F_closed_loop_full_speed.md (NEW TABLE)
- new table, 2 rows

### T5_H_tag_loss_drift.md
- `tag lost: 5 s hover · 27 / 50 (range 11–27; 6 losses, one per flight)` col 4: `22 / 50 (range 12–22; 3 losses, one per flight)` → `19 / 50 (range 18–19; 3 losses, one per flight)`
- `tag lost: 15 s hover · 25 / 100 (range 6–25; 6 losses, one per flight)` col 4: `27 / 100 (range 7–27; 3 losses, one per flight)` → `23 / 100 (range 5–23; 3 losses, one per flight)`
- `tag lost: 30 s hover · 26 / 200 (range 3–26; 6 losses, one per flight)` col 4: `23 / 200 (range 9–23; 3 losses, one per flight)` → `28 / 200 (range 8–28; 3 losses, one per flight)`
- `tag lost: ~7 s during a move · 31 / 150 (range 4–31; 6 losses, one per` col 4: `18 / 150 (range 10–18; 3 losses, one per flight)` → `23 / 150 (range 1–23; 3 losses, one per flight)`
- notes: 2 footnote paragraph(s) changed or added

### T7_failure_behaviour.md
- no cell change

### TA_verdicts.md
- `Experiment 1 · H1.8 EKF3, real time (RTF 1.0)` col 4: `west-wall contact at cruise +186.2 s [numbers.md:470]` → `west-wall contact at cruise +186.2 s; as recorded (n = 1; flight 1 of the n = 3 cell) [numbers.md:470]`
- `Experiment 1 · H1.8 EKF3, real time (RTF 1.0)` col 6: `no (flight; claims row 14)` → `no (flight; claims row 14); n = 1 label is D149(b)`
- `Experiment 1 · H1.8 EKF3, half real-time (RTF 0.5)` col 4: `contact at cruise +242.1 s: after the registered window (MISS) [numbers.md:470]` → `contact at cruise +242.1 s: after the registered window (MISS); as recorded (n = 1; flight 1 of the n = 3 cell) [numbers.md:470]`
- `Experiment 1 · H1.8 EKF3, half real-time (RTF 0.5)` col 6: `no (flight); no comparison across real-time factors is claimed` → `no (flight); no comparison across real-time factors is claimed; n = 1 label is D149(b)`
- ADDED row `Experiment 1 · H1.8 UKF, half real-time (final UKF port, abb0357d)`
- ADDED row `Experiment 1 · H1.8 n = 3 EKF3, full real time (RTF 1.0)`
- ADDED row `Experiment 1 · H1.8 n = 3 EKF3, half real-time (RTF 0.5)`
- ADDED row `Experiment 1 · H1.8 n = 3 UKF, full real time (final port, abb0357d)`
- ADDED row `Experiment 1 · H1.8 n = 3 UKF, half real-time (final port, abb0357d)`
- ADDED row `Experiment 1 · H1.8 n = 3 FGO, half real-time (corrected priors, 4c07374b/HEAD)`
- ADDED row `Experiment 1 · H1.9 FGO (corrected priors, 4c07374b/HEAD, half real-time)`
- ADDED row `Experiment 1B · 1B-H1`
- ADDED row `Experiment 1B · 1B-H2`
- ADDED row `Experiment 1B · 1B-H3`
- `Experiment 5 · H5.1` col 4: `PASS: hold error mean 8 mm, max 16–25 mm (EKF3 flying); also PASS on the FGO-flying hold set (final FGO node) [numbers.md:606; numbers.md:646]` → `PASS: hold error mean 8 mm, max 16–25 mm (EKF3 flying) [numbers.md:606]`
- `Experiment 5 · H5.1` col 6: `no (flights; claims row 25)` → `no (flights; claims row 25); the FGO-flying reading moved to a separate row below (D150, OQ-R1); this is the primary H5.1 verdict, EKF3 flying only`
- ADDED row `Experiment 5 · H5.1 (FGO-flying) corrected priors, 2026-11-12 regeneration`
- `Experiment 5 · H5.2` col 3: `“H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.” (design draft §e; no METHODOLOGY pre-registration line) [tag_ho` → `“H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.” [tag_hold_design.md:180]; (design draft §e; no METHODOLOGY pre-`
- `Experiment 5 · H5.2` col 4: `FAIL (0/3): UKF lowest 3/3 (6.4–7.1 mm); FGO highest in all three (8.3–8.6 against EKF3 7.8–7.9 mm) [numbers.md:675]` → `FAIL (0/3 FGO lowest): UKF lowest 3/3 (6.4–7.1 mm); FGO (corrected priors) 7.3–8.3 mm, highest in only 1 of 3 runs (r2), below EKF3 (7.8–7.9 mm) in the other tw`
- `Experiment 5 · H5.2` col 6: `wording only (tie → FGO highest) on the final-build sets; verdict identical to the original-build verdict` → `2026-11-12 regeneration (D149(c)): corrected priors; the H-H2 verdict category is unchanged (FAIL 0/3 both), but the underlying pattern changed from 'clearly th`
- `Experiment 5 · H5.3` col 4: `FAIL (0/3): UKF 2.40–2.58×, FGO 2.10–2.37× EKF3's [numbers.md:676]` → `FAIL (0/3): ratios 2.402/2.577/2.499 (driven by max(UKF)/min(EKF3) in every run; numerically unchanged, since FGO's own gyro activity, ~2.0–2.3x EKF3's, is neve`
- `Experiment 5 · H5.3` col 6: `no: identical to the original-build verdict` → `2026-11-12 regeneration (D149(c)): re-derived on the corrected priors, numerically unchanged (not driven by the FGO); superseded original-prior reading: UKF 2.4`
- `Experiment 5 · H5.4a` col 4: `FAIL (0/3): EKF3 strictly the smallest (5 / 5 / 7 against UKF 20–30, FGO 7–30 mm) [numbers.md:677]` → `FAIL (0/3 EKF3 largest): EKF3 (4.9/4.5/7.3 mm) strictly smallest in all 3 runs both before and after; UKF (29.6/20.4/25.6 mm, unchanged) largest in all 3; FGO (`
- `Experiment 5 · H5.4a` col 6: `wording only (smallest or tied → strictly smallest); verdict identical` → `2026-11-12 regeneration (D149(c)): corrected priors narrow the FGO's own 15 s jump from 7.2–30.1 mm (original) to 7.1–24.0 mm (new); verdict and extremal estima`
- `Experiment 5 · H5.4b` col 4: `FAIL (0/3): EKF3 4–5 against UKF 7–16, FGO 11–34 mm (max/min 3.2–7.7) [numbers.md:678]` → `FAIL (0/3): ratio range narrowed from 3.2–7.7 (original) to 2.1–5.1 (corrected priors); still FAIL (all > 1.5) in both cases [refly_priors/numbers_refly.md:340-`
- `Experiment 5 · H5.4b` col 6: `no: identical to the original-build verdict` → `2026-11-12 regeneration (D149(c)): corrected priors; original-prior reading (EKF3 4-5 against UKF 7-16, FGO 11-34 mm, max/min 3.2–7.7) superseded (D149(b))`
- `Experiment 5 · H5.5` col 4: `PASS: every loss inside its band (20/20 each estimator in S1; every band passes on the UKF- and FGO-flying hold sets) [numbers.md:629; numbers.md:644; numbers.m` → `PASS: every loss inside its band (20/20 each estimator in S1; every band passes on the UKF-flying hold set and on the FGO-flying hold set, corrected priors) [nu`
- `Experiment 5 · H5.5` col 6: `no (claims row 25); the S1 shadow drifts were restated (claims row 26)` → `no (claims row 25); the S1 shadow drifts were restated (claims row 26); 2026-11-12 regeneration (D149(c)): the FGO citation is now the corrected-prior re-fly (n`
- ADDED row `Experiment 5 · H5.5 S2/S3 directional prediction (UKF-flying hold set, final port; FGO-fly`
- ADDED row `Experiment 5 · H5.6 redefined primary (UKF-flying hold set, final port; FGO-flying hold se`
- ADDED row `Experiment 5 · H5.6 jump criterion, kept as worded (UKF-flying hold set, final port; FGO-f`
- `Experiment 5 · H5.7` col 4: `PASS: no lockout in any loss [numbers.md:629]` → `PASS: no lockout in any loss (S1; confirmed again on the FGO-flying hold set, corrected priors) [numbers.md:629; refly_priors/numbers_refly.md:275]`
- `Experiment 5 · H5.7` col 6: `no (claims row 25)` → `no (claims row 25); re-confirmed on the corrected-priors FGO-flying hold set (numbers_refly.md §4.2)`
- `Experiment 5S · S-A (FGO forced-invalid test, corrected-priors node, r` col 6: `flew the corrected initial priors; the flown FGO hold/closed-loop corridor results used the ORIGINAL priors (T7)` → `flew the corrected initial priors, as do the current FGO corridor and hold rows after the 2026-11-12 regeneration (D149(c)); the original-prior sets are listed `
- ADDED row `id · reason`
- ADDED row `H1.8 UKF, full real time · superseded: earlier build`
- ADDED row `H1.8 FGO, half real-time · superseded: original priors`
- ADDED row `H1.9 FGO, half real-time · superseded: original priors`
- ADDED row `H5.1 (FGO-flying) · superseded: original priors`
- ADDED row `H5.2 (original priors) · superseded: original priors`
- ADDED row `H5.3 (original priors) · superseded: original priors`
- ADDED row `H5.4a (original priors) · superseded: original priors`
- ADDED row `H5.4b (original priors) · superseded: original priors`
- ADDED row `H5.5, drift band (FGO) · superseded: original priors`
- ADDED row `H5.5, S2/S3 directional prediction (FGO) · superseded: original priors`
- ADDED row `H5.6, redefined primary (FGO) · superseded: original priors`
- ADDED row `H5.6, jump as worded (FGO) · superseded: original priors`
- ADDED row `H5.7 (FGO) · superseded: original priors`
- REMOVED/MOVED row `Experiment 1 · H1.8 UKF (real time; half real-time, final UKF port)`
- REMOVED/MOVED row `Experiment 1 · H1.8 FGO (half real-time, final FGO node)`
- REMOVED/MOVED row `Experiment 1 · H1.9 FGO (final FGO node, half real-time)`
- REMOVED/MOVED row `Experiment 5 · H5.5 S2/S3 directional prediction (UKF- and FGO-flying hold sets, final bui`
- REMOVED/MOVED row `Experiment 5 · H5.6 redefined primary (UKF- and FGO-flying hold sets)`
- REMOVED/MOVED row `Experiment 5 · H5.6 jump criterion, kept as worded (UKF- and FGO-flying hold sets)`
- notes: 1 footnote paragraph(s) changed or added

### R1_hypothesis_scorecard.md
- `H1.8 EKF3, real time (RTF 1.0) · closed loop without heading: contact ` col 4: `west-wall contact at cruise +186.2 s` → `west-wall contact at cruise +186.2 s; as recorded (n = 1; flight 1 of the n = 3 cell)`
- `H1.8 EKF3, real time (RTF 1.0) · closed loop without heading: contact ` col 6: `no (flight; claims row 14)` → `no (flight; claims row 14); n = 1 label is D149(b)`
- `H1.8 EKF3, half real-time (RTF 0.5) · closed loop without heading: con` col 4: `contact at cruise +242.1 s: after the registered window (MISS)` → `contact at cruise +242.1 s: after the registered window (MISS); as recorded (n = 1; flight 1 of the n = 3 cell)`
- `H1.8 EKF3, half real-time (RTF 0.5) · closed loop without heading: con` col 6: `no (flight); no comparison across real-time factors is claimed` → `no (flight); no comparison across real-time factors is claimed; n = 1 label is D149(b)`
- ADDED row `H1.8 UKF, half real-time (final UKF port, abb0357d) · closed loop without heading: contact`
- ADDED row `H1.8 n = 3 EKF3, full real time (RTF 1.0) · closed loop without heading: contact predictio`
- ADDED row `H1.8 n = 3 EKF3, half real-time (RTF 0.5) · closed loop without heading: contact predictio`
- ADDED row `H1.8 n = 3 UKF, full real time (final port, abb0357d) · closed loop without heading: conta`
- ADDED row `H1.8 n = 3 UKF, half real-time (final port, abb0357d) · closed loop without heading: conta`
- ADDED row `H1.8 n = 3 FGO, half real-time (corrected priors, 4c07374b/HEAD) · closed loop without hea`
- ADDED row `H1.9 FGO (corrected priors, 4c07374b/HEAD, half real-time) · closed loop with heading: cri`
- ADDED row `1B-H1 · EKF3 + camera heading via Replay: yaw error vs no heading (descriptive)`
- ADDED row `1B-H2 · Arms (iii)/(iv) at 5° vs the stored 0.148/0.126° arms (descriptive, PROPOSAL accep`
- ADDED row `1B-H3 · EKF3's 5°-floored ExternalNav path vs the UKF/FGO's own 5° arms (descriptive)`
- `H5.1 · hold accuracy (primary)` col 4: `PASS: hold error mean 8 mm, max 16–25 mm (EKF3 flying); also PASS on the FGO-flying hold set (final FGO node)` → `PASS: hold error mean 8 mm, max 16–25 mm (EKF3 flying)`
- `H5.1 · hold accuracy (primary)` col 6: `no (flights; claims row 25)` → `no (flights; claims row 25); the FGO-flying reading moved to a separate row below (D150, OQ-R1); this is the primary H5.1 verdict, EKF3 flying only`
- `H5.1 · hold accuracy (primary)` col 7: `numbers.md:606; numbers.md:646` → `numbers.md:606`
- ADDED row `H5.1 (FGO-flying) corrected priors, 2026-11-12 regeneration · H5.1 bounds applied to the F`
- `H5.2 · FGO holds tightest` col 3: `“H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.” (design draft §e; no METHODOLOGY pre-registration line) [tag_ho` → `“H-H2: the FGO's hold error is lowest. FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.” [tag_hold_design.md:180]; (design draft §e; no METHODOLOGY pre-`
- `H5.2 · FGO holds tightest` col 4: `FAIL (0/3): UKF lowest 3/3 (6.4–7.1 mm); FGO highest in all three (8.3–8.6 against EKF3 7.8–7.9 mm)` → `FAIL (0/3 FGO lowest): UKF lowest 3/3 (6.4–7.1 mm); FGO (corrected priors) 7.3–8.3 mm, highest in only 1 of 3 runs (r2), below EKF3 (7.8–7.9 mm) in the other tw`
- `H5.2 · FGO holds tightest` col 6: `wording only (tie → FGO highest) on the final-build sets; verdict identical to the original-build verdict` → `2026-11-12 regeneration (D149(c)): corrected priors; the H-H2 verdict category is unchanged (FAIL 0/3 both), but the underlying pattern changed from 'clearly th`
- `H5.2 · FGO holds tightest` col 7: `numbers.md:675` → `refly_priors/numbers_refly.md:337-337; refly_priors/numbers_refly.md:342-348`
- `H5.3 · smoothness similar` col 4: `FAIL (0/3): UKF 2.40–2.58×, FGO 2.10–2.37× EKF3's` → `FAIL (0/3): ratios 2.402/2.577/2.499 (driven by max(UKF)/min(EKF3) in every run; numerically unchanged, since FGO's own gyro activity, ~2.0–2.3x EKF3's, is neve`
- `H5.3 · smoothness similar` col 6: `no: identical to the original-build verdict` → `2026-11-12 regeneration (D149(c)): re-derived on the corrected priors, numerically unchanged (not driven by the FGO); superseded original-prior reading: UKF 2.4`
- `H5.3 · smoothness similar` col 7: `numbers.md:676` → `refly_priors/numbers_refly.md:338-338; refly_priors/numbers_refly.md:350-351`
- `H5.4a · after a 15 s loss, EKF3 jumps most` col 4: `FAIL (0/3): EKF3 strictly the smallest (5 / 5 / 7 against UKF 20–30, FGO 7–30 mm)` → `FAIL (0/3 EKF3 largest): EKF3 (4.9/4.5/7.3 mm) strictly smallest in all 3 runs both before and after; UKF (29.6/20.4/25.6 mm, unchanged) largest in all 3; FGO (`
- `H5.4a · after a 15 s loss, EKF3 jumps most` col 6: `wording only (smallest or tied → strictly smallest); verdict identical` → `2026-11-12 regeneration (D149(c)): corrected priors narrow the FGO's own 15 s jump from 7.2–30.1 mm (original) to 7.1–24.0 mm (new); verdict and extremal estima`
- `H5.4a · after a 15 s loss, EKF3 jumps most` col 7: `numbers.md:677` → `refly_priors/numbers_refly.md:339-339; refly_priors/numbers_refly.md:353-355`
- `H5.4b · after a 5 s loss, jumps similar` col 4: `FAIL (0/3): EKF3 4–5 against UKF 7–16, FGO 11–34 mm (max/min 3.2–7.7)` → `FAIL (0/3): ratio range narrowed from 3.2–7.7 (original) to 2.1–5.1 (corrected priors); still FAIL (all > 1.5) in both cases`
- `H5.4b · after a 5 s loss, jumps similar` col 6: `no: identical to the original-build verdict` → `2026-11-12 regeneration (D149(c)): corrected priors; original-prior reading (EKF3 4-5 against UKF 7-16, FGO 11-34 mm, max/min 3.2–7.7) superseded (D149(b))`
- `H5.4b · after a 5 s loss, jumps similar` col 7: `numbers.md:678` → `refly_priors/numbers_refly.md:340-340; refly_priors/numbers_refly.md:357-357`
- `H5.5 · drift band` col 4: `PASS: every loss inside its band (20/20 each estimator in S1; every band passes on the UKF- and FGO-flying hold sets)` → `PASS: every loss inside its band (20/20 each estimator in S1; every band passes on the UKF-flying hold set and on the FGO-flying hold set, corrected priors)`
- `H5.5 · drift band` col 6: `no (claims row 25); the S1 shadow drifts were restated (claims row 26)` → `no (claims row 25); the S1 shadow drifts were restated (claims row 26); 2026-11-12 regeneration (D149(c)): the FGO citation is now the corrected-prior re-fly (n`
- `H5.5 · drift band` col 7: `numbers.md:629; numbers.md:644; numbers.md:646` → `numbers.md:629; numbers.md:644; refly_priors/numbers_refly.md:245-259`
- ADDED row `H5.5 S2/S3 directional prediction (UKF-flying hold set, final port; FGO-flying hold set, c`
- ADDED row `H5.6 redefined primary (UKF-flying hold set, final port; FGO-flying hold set, corrected pr`
- ADDED row `H5.6 jump criterion, kept as worded (UKF-flying hold set, final port; FGO-flying hold set,`
- `H5.7 · no lockout` col 4: `PASS: no lockout in any loss` → `PASS: no lockout in any loss (S1; confirmed again on the FGO-flying hold set, corrected priors)`
- `H5.7 · no lockout` col 6: `no (claims row 25)` → `no (claims row 25); re-confirmed on the corrected-priors FGO-flying hold set (numbers_refly.md §4.2)`
- `H5.7 · no lockout` col 7: `numbers.md:629` → `numbers.md:629; refly_priors/numbers_refly.md:275`
- ADDED row `id · reason`
- ADDED row `H1.8 UKF, full real time · superseded: earlier build`
- ADDED row `H1.8 FGO, half real-time · superseded: original priors`
- ADDED row `H1.9 FGO, half real-time · superseded: original priors`
- ADDED row `H5.1 (FGO-flying) · superseded: original priors`
- ADDED row `H5.2 (original priors) · superseded: original priors`
- ADDED row `H5.3 (original priors) · superseded: original priors`
- ADDED row `H5.4a (original priors) · superseded: original priors`
- ADDED row `H5.4b (original priors) · superseded: original priors`
- ADDED row `H5.5, drift band (FGO) · superseded: original priors`
- ADDED row `H5.5, S2/S3 directional prediction (FGO) · superseded: original priors`
- ADDED row `H5.6, redefined primary (FGO) · superseded: original priors`
- ADDED row `H5.6, jump as worded (FGO) · superseded: original priors`
- ADDED row `H5.7 (FGO) · superseded: original priors`
- REMOVED/MOVED row `H1.8 UKF (real time; half real-time, final UKF port) · closed loop without heading: contac`
- REMOVED/MOVED row `H1.8 FGO (half real-time, final FGO node) · closed loop without heading: contact predictio`
- REMOVED/MOVED row `H1.9 FGO (final FGO node, half real-time) · closed loop with heading: criteria pass`
- REMOVED/MOVED row `H5.5 S2/S3 directional prediction (UKF- and FGO-flying hold sets, final builds) · drift ba`
- REMOVED/MOVED row `H5.6 redefined primary (UKF- and FGO-flying hold sets) · re-lock time`
- REMOVED/MOVED row `H5.6 jump criterion, kept as worded (UKF- and FGO-flying hold sets) · re-lock time`
- notes: 4 footnote paragraph(s) changed or added

### R4_information_vs_estimator.md
- notes: 1 footnote paragraph(s) changed or added

### methods_noise_exceptions.md
- `2 · forward heading offline (1B)` col 4: `EKF3 is the fixed no-yaw-source baseline (VISO_YAW_M_NSE floor; LOG_REPLAY=0)` → `EKF3 is the fixed no-yaw-source baseline for the registered Phase 4 comparison (VISO_YAW_M_NSE floor; LOG_REPLAY=0). REOPENED (D131/D132): EKF3 + camera heading`
- `2 · forward heading offline (1B)` col 5: `ruling M:2884-2888` → `ruling M:2884-2888; reopened decisions_log.md:157, decisions_log.md:158`
- `5 · FGO flow/range gating (design deviation)` col 4: `DESIGN DEVIATION, documented, not corrected or re-run (results frozen); it leaves the FGO less defended, not more. The design called for matched gates` → `DESIGN DEVIATION, documented, not corrected or re-run (results frozen); it leaves the FGO less defended, not more. The design called for matched gates. A read-o`
- `5 · FGO flow/range gating (design deviation)` col 5: `EKF3 AP_NavEKF3_OptFlowFusion.cpp:665, AP_NavEKF3_PosVelFusion.cpp:1022; UKF UC:295, UC:231; FGO FC:184, CC:144; design FGO_DESIGN.md:446; ruling M:14302` → `EKF3 AP_NavEKF3_OptFlowFusion.cpp:665, AP_NavEKF3_PosVelFusion.cpp:1022; UKF UC:295, UC:231; FGO FC:184, CC:144; design FGO_DESIGN.md:446; ruling M:14302; gatin`
- `6 · FLOW_MAX sidedness` col 6: `NO RULING FOUND; at 0.5 m/s and 2 m the flow is ~0.25 rad/s, far from the limit (not counted)` → `NO RULING FOUND; at 0.5 m/s and 2 m the flow is ~0.25 rad/s, far from the limit. Now counted, read-only (row 5): the one-sided and two-sided counts are identica`
- `6 · FLOW_MAX sidedness` col 7: `UC:293; AP_NavUKF.cpp:874; EKF3 AP_NavEKF3_OptFlowFusion.cpp:668` → `UC:293; AP_NavUKF.cpp:874; EKF3 AP_NavEKF3_OptFlowFusion.cpp:668; gating count fgo_gate_count_results.md:254`
- `11 · FGO initial uncertainty` col 3: `corrected to yaw 1°, roll/pitch 5° (the UKF's); flown FGO results used 1e-3 rad / 2°; EKF3 keeps 0.1 rad` → `corrected to yaw 1°, roll/pitch 5° (the UKF's); the ORIGINAL flown FGO corridor and hold results used 1e-3 rad / 2° (now superseded: original priors); a re-fly `
- `11 · FGO initial uncertainty` col 5: `ruling M:12857-12862; N:36` → `ruling M:12857-12862; N:36; re-fly decisions_log.md:153`
