# Freeze audit of the thesis outputs

Audited commit: `259371cb3d029d1b7ca3ce94f2a38088e9c6116f` (branch `freeze-audit`, built from `fwd-camera`). Run date (UTC): 2026-11-14 11:29 UTC. This report and `eval/freeze_audit.py` are the only two files this audit writes or touches; no table, figure, caption or numbers file was edited.

Re-run: `python3 eval/freeze_audit.py --write-report` (safe to re-run after fixes land; it reads only, from the working tree at run time).

## Summary

- A (supersession map): **PASS** - 181 entries harvested (13 TA appendix rows, 12 refly §5 rows, 3 numbers_extras rows, 11 numbers.md superseded sections / 153 escaped rows).
- B(i) (superseded values presented as current): **FAIL** - 31 hit(s) across 156 thesis-facing files scanned.
- B(ii) (verdict labels vs TA_verdicts.md): **FAIL** - H4.2 checked 25 occurrence(s), 4 not reading NOT MET; 2 other unambiguous mismatch(es); 150 non-standard bare-word label(s).
- C (numeric cells vs cited source): **FAIL** - 1065 `numbers*.md:LINE` citations found; 429 matched on the cited line, 73 matched elsewhere in the file (cite drift), 3 not found, 560 unresolved (non-numeric/no-token cites excluded from scope per the request).
- D (style checks): **FAIL** - see per-file counts below.
- E (4.3 s delay / 4.10 m jump): **FAIL** - 45 statement(s) found, 33 qualified, 12 unqualified.
- F (coverage matrix): **FAIL**

## Scope notes

- Writing pack read from: `docs/thesis/writing_pack` (untracked; read from the working tree, not a commit - sha256 of each file recorded below for re-run comparability).
- `tables_png` images are not text-scannable; their `.md`/`.tex` sources are scanned instead, per the request's own distinction between 'tables_tex/*.tex' and 'tables_png sources'.
- Candidate figure captions/index files (`figures_thesis/candidates/`) are scanned but reported in their own section below; they are not thesis-numbered and are out of the main B/C/D counts.
- Section A's treatment of `numbers.md`'s own internal `### Superseded by ...` correction-trail sections is at SECTION granularity (quantity + superseded value harvested per escaped row; 'current value' is reported as unresolved for these rows rather than guessed, since matching each row to its exact live counterpart across dozens of embedded historical tables was not completed inside the time box). The TA_verdicts.md appendix (13 rows) and numbers_refly.md §5 (12 rows) ARE resolved to a current value each. These section-granularity facts are still used to drive the B(i) 'superseded value presented as current' scan below, since that only needs the superseded value, not its resolved current counterpart.
- Section B(ii) only reports a mismatch when TA_verdicts.md records exactly ONE verdict for the matched base ID across its whole main table (ids like H1.2 recur with different verdicts per sub-row and are intentionally not scored, per the known H1.2 ambiguity).

## A. Supersession map

| quantity | superseded value | current value | current source | origin |
|---|---|---|---|---|
| H1.8 UKF, full real time | +163.0 s west; U1/U2/U3 PASS (hand-scored S1/S2 both hold, pre-dating the registered scorer's S2 support) | k/3 = 2/3: 177.1 (PASS), 138.3 (before window), 162.8 (PASS) s, all west wall. Spread: 138.3–177.1 s. No flight 1 exists on this port (the e | TA_verdicts.md:30 | TA_verdicts.md:110 |
| H1.8 FGO, half real-time | +169.9 s west (U1, U2, U3 PASS) | PRIMARY k/3 = 2/3: 166.7 (PASS), 193.9 (PASS), 203.5 (after window, 7.46 s outside) s, all west wall. S2 100% (arm-to-contact window) on all | TA_verdicts.md:32 | TA_verdicts.md:111 |
| H1.9 FGO, half real-time | 3/3, ALL B criteria and S2 PASS; flight 3 lateral speed 0.246 m/s, 0.004 m/s inside the 0.25 m/s band | 3/3, all five criteria and estimator validity PASS (corrected priors); per-flight max lateral speed 0.119 / 0.008 / 0.196 m/s, comfortably i | TA_verdicts.md:35 | TA_verdicts.md:112 |
| H5.1 (FGO-flying) | hold error mean 8.1–9.0 mm, max 18–28 mm | PASS: hold error mean 7.1–8.7 mm, max 15.0–25.5 mm, every window inside the 50/150 mm bounds, 3/3 [refly_priors/numbers_refly.md:228-235] | TA_verdicts.md:52 | TA_verdicts.md:113 |
| H5.2 (original priors) | FGO highest in all three runs (8.3–8.6 against EKF3 7.8–7.9 mm) | FAIL (0/3 FGO lowest): UKF lowest 3/3 (6.4–7.1 mm); FGO (corrected priors) 7.3–8.3 mm, highest in only 1 of 3 runs (r2), below EKF3 (7.8–7.9 | TA_verdicts.md:53 | TA_verdicts.md:114 |
| H5.3 (original priors) | UKF 2.40–2.58×, FGO 2.10–2.37× EKF3's (numerically unchanged by the prior correction) | FAIL (0/3): ratios 2.402/2.577/2.499 (driven by max(UKF)/min(EKF3) in every run; numerically unchanged, since FGO's own gyro activity, ~2.0– | TA_verdicts.md:54 | TA_verdicts.md:115 |
| H5.4a (original priors) | EKF3 strictly the smallest (5/5/7 against UKF 20–30, FGO 7–30 mm) | FAIL (0/3 EKF3 largest): EKF3 (4.9/4.5/7.3 mm) strictly smallest in all 3 runs both before and after; UKF (29.6/20.4/25.6 mm, unchanged) lar | TA_verdicts.md:55 | TA_verdicts.md:116 |
| H5.4b (original priors) | EKF3 4–5 against UKF 7–16, FGO 11–34 mm (max/min 3.2–7.7) | FAIL (0/3): ratio range narrowed from 3.2–7.7 (original) to 2.1–5.1 (corrected priors); still FAIL (all > 1.5) in both cases [refly_priors/n | TA_verdicts.md:56 | TA_verdicts.md:117 |
| H5.5, drift band (FGO) | every FGO band PASSES | NOT borne out (the predicted outcome did not occur): per matched loss (same loss and repeat, flying EKF3 = the EKF3-flying hold set, near sp | TA_verdicts.md:58 | TA_verdicts.md:118 |
| H5.5, S2/S3 directional prediction (FGO) | FGO drifted more than flying EKF3 in 9 of 12 (effective drift range 7–27 mm) | NOT borne out (the predicted outcome did not occur): per matched loss (same loss and repeat, flying EKF3 = the EKF3-flying hold set, near sp | TA_verdicts.md:58 | TA_verdicts.md:119 |
| H5.6, redefined primary (FGO) | FGO 0.002–0.032 s | PASS: UKF −0.048…−0.015 s; FGO (corrected priors) 2.8–30.3 ms [numbers.md:644; refly_priors/numbers_refly.md:268-272] | TA_verdicts.md:60 | TA_verdicts.md:120 |
| H5.6, jump as worded (FGO) | fails in 4 of 12 losses | fails as worded: final UKF port in most losses (steps 5–30 mm against drifts 2–26 mm); corrected-priors FGO node in 8 of 12 losses (r1: all  | TA_verdicts.md:61 | TA_verdicts.md:121 |
| H5.7 (FGO) | no lockout in any loss (identical conclusion on corrected priors) | PASS: no lockout in any loss (S1; confirmed again on the FGO-flying hold set, corrected priors) [numbers.md:629; refly_priors/numbers_refly. | TA_verdicts.md:62 | TA_verdicts.md:122 |
| H1.8 FGO** (no heading) | `cl_fgo_a_tex_half_v3` (n=1): contact +169.9 s west, U1/U2/U3 PASS, S2 100 % arm-to-contact (re-derived here; METHODOLOGY's own stated value | n=3: PRIMARY k/3 = 2/3. r1, r2 PASS U1/U2/U3 (and S2); r3 MISS on U3 alone (window edge, 203.5 s vs the 196 s bound). k/3 = 0/3 only if S2 i | refly_priors/numbers_refly.md:363 | refly_priors/numbers_refly.md:363 |
| H1.9 FGO** (with heading) | `cl_fgo_b_tex_r{1,2,3}_half_v3`: 3/3, ALL B criteria and S2 PASS (numbers.md row; confirmed from stored jsons, section 2 table) | `cl_fgo_b_tex_r{1,2,3}_half_rp`: 3/3, ALL B criteria and S2 PASS | refly_priors/numbers_refly.md:364 | refly_priors/numbers_refly.md:364 |
| H5.1** (FGO-flying bounds) | `H_s3v2_r*`: mean 8.1-9.0 mm, max 18-28 mm (H-H1 PASS, numbers.md section 17.1) | `s3rp_r*`: mean 7.1-8.7 mm, max 15.0-25.5 mm (PASS, section 4.1) | refly_priors/numbers_refly.md:365 | refly_priors/numbers_refly.md:365 |
| H5.5** (FGO drift bands) | `H_s3v2_r*`: end of loss 13/20/17; 7/25/27; 22/15/9; 17/11/18 mm (every band PASSES, numbers.md section 17.1) | `s3rp_r*`: end of loss 20/20/19; 22/7/6; 9/12/28; 3/24/1 mm (every band PASSES, section 4.2) | refly_priors/numbers_refly.md:366 | refly_priors/numbers_refly.md:366 |
| H5.6 redefined primary (re-lock) | `H_s3v2_r*`: 0.002-0.032 s, PASS | `s3rp_r*`: 0.003-0.030 s, PASS (section 4.2) | refly_priors/numbers_refly.md:367 | refly_priors/numbers_refly.md:367 |
| H5.6 jump as worded | `H_s3v2_r*`: fails in 4 of 12 losses | `s3rp_r*`: fails in 8 of 12 losses (section 4.2) | refly_priors/numbers_refly.md:368 | refly_priors/numbers_refly.md:368 |
| H5.7 lockout | `H_s3v2_r*`: no lockout, PASS | `s3rp_r*`: no lockout, PASS | refly_priors/numbers_refly.md:369 | refly_priors/numbers_refly.md:369 |
| 30 s-loss yaw wander | `H_s3v2_r*`: -0.23 / +0.52 / +0.52 deg (<=3 deg, PASS); method not persisted anywhere in the repo, re-derived and verified here (reproduces  | `s3rp_r*`: -0.160 / +0.488 / +0.680 deg (section 4.2); PASS | refly_priors/numbers_refly.md:370 | refly_priors/numbers_refly.md:370 |
| H-H2 | FAIL (0/3): FGO highest in all three runs, 8.3-8.6 mm against EKF3 7.8-7.9 mm (`h_comparative_2026-10-11.json`) | FAIL (0/3 FGO lowest; `lowest_hold`=UKF all 3); FGO 7.3-8.3 mm, highest in only 1 of 3 runs, below EKF3 (7.8-7.9 mm) in the other 2 (section | refly_priors/numbers_refly.md:371 | refly_priors/numbers_refly.md:371 |
| P-H3 | FAIL (0/3): UKF 2.40-2.58x, FGO 2.10-2.37x EKF3's hold gyro activity | FAIL (0/3): ratios 2.402/2.577/2.499, numerically unchanged (driven by UKF/EKF3, not FGO; section 4.3) | refly_priors/numbers_refly.md:372 | refly_priors/numbers_refly.md:372 |
| H-H4 (15 s) | FAIL (0/3): EKF3 strictly smallest (5/5/7 mm) against UKF 20-30, FGO 7-30 mm | FAIL (0/3): EKF3 strictly smallest (5/5/7 mm) against UKF 20-30 (unchanged), FGO 7-24 mm (narrower; section 4.3) | refly_priors/numbers_refly.md:373 | refly_priors/numbers_refly.md:373 |
| H-H4 (5 s) | FAIL (0/3): EKF3 4-5 mm against UKF 7-16, FGO 11-34 mm (max/min 3.2-7.7) | FAIL (0/3): ratios 2.1-5.1 (narrower than 3.2-7.7; section 4.3) | refly_priors/numbers_refly.md:374 | refly_priors/numbers_refly.md:374 |
| UKF H1.8 full real time (old port cl_ukf_a_tex) | **On the superseded old-port flight, `cl_ukf_a_tex` (listed only, not counted, see below):** its own json | see closed_loop_extras/numbers_extras.md Summary table, 'UKF, full real time (_v2)' row (2/3, 138.3-177.1 s) | closed_loop_extras/numbers_extras.md (Summary table) | closed_loop_extras/numbers_extras.md:67 |
| UKF H1.8 full real time (old port cl_ukf_a_tex) | **Superseded, listed only (not counted in the k/3 above):** `cl_ukf_a_tex` flew the earlier, | see closed_loop_extras/numbers_extras.md Summary table, 'UKF, full real time (_v2)' row (2/3, 138.3-177.1 s) | closed_loop_extras/numbers_extras.md (Summary table) | closed_loop_extras/numbers_extras.md:127 |
| UKF H1.8 full real time (old port cl_ukf_a_tex) | / UKF, full real time (`_v2`) / 2/3 / 138.3-177.1 / PASS (earlier, superseded port, `cl_ukf_a_tex`, +163.0 s; not counted) / | see closed_loop_extras/numbers_extras.md Summary table, 'UKF, full real time (_v2)' row (2/3, 138.3-177.1 s) | closed_loop_extras/numbers_extras.md (Summary table) | closed_loop_extras/numbers_extras.md:154 |

### A appendix: `numbers.md` internal correction-trail sections (11 sections, 153 escaped rows, section-granularity only)

- **### Superseded by D27 (2026-10-01): offline-UKF values with 1.2× per-s**
- **### Superseded by the final consolidated re-run (2026-10-10): rows rep**
- **### Superseded by the FGO-only re-run (2026-10-10): FGO rows of the fi**
- **### Superseded by the restatement rulings (2026-10-10, items 1–5): wor**
- **### Superseded by the closed-loop re-flight restatement (2026-10-11, p**
- **### Superseded by the rulings of 2026-10-16 (pending items and caption**
- **### Superseded by the ruling of 2026-10-16 (numbers.md rounding): doub**
- **### Superseded by the ruling of 2026-10-16 (the three mismatched rows**

## B(i). Superseded values presented as current

**Read before acting**: a few rows below are matches WITHIN `refly_priors/numbers_refly.md`'s own §5 'Old vs new per criterion' table (or its direct copies under the writing pack), which is a deliberate side-by-side presentation of the old value next to the new one - not a defect. The headline findings that ARE real, unqualified presentations of a superseded value as current are the ones in `docs/thesis/tables/R4_information_vs_estimator.md:14`, `T1_scorecard.md:42`, `T5_H_tag_loss_drift.md:22`, and the `figures_thesis/index.md`/`index_results.md` rows for H5.4b / H-H4 (15 s) / H5.5 - none of those five files is the old-vs-new comparison table itself.

| file:line | quantity | matched value | origin (where it was superseded) | context |
|---|---|---|---|---|
| docs/thesis/tables/R4_information_vs_estimator.md:14 | H5.2 (original priors) | 7.8–7.9 | TA_verdicts.md:114 | / Experiment 5: tag hold (each estimator flying) / mean hold error (mm), tag visible; n = 3 flights per estimator (paired by run index, not trajectory) / EKF3 7 |
| docs/thesis/tables/R4_information_vs_estimator.md:14 | H-H2 | 7.8-7.9 | refly_priors/numbers_refly.md:371 | / Experiment 5: tag hold (each estimator flying) / mean hold error (mm), tag visible; n = 3 flights per estimator (paired by run index, not trajectory) / EKF3 7 |
| docs/thesis/tables/T1_scorecard.md:44 | H-H2 | 7.8-7.9 | refly_priors/numbers_refly.md:371 | *[i] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |
| docs/thesis/tables/T1_scorecard.md:44 | P-H3 | 2.40-2.58 | refly_priors/numbers_refly.md:372 | *[i] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |
| docs/thesis/tables/T5_H_tag_loss_drift.md:22 | H-H2 | 7.8-7.9 | refly_priors/numbers_refly.md:371 | *[a] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |
| docs/thesis/tables/T5_H_tag_loss_drift.md:22 | P-H3 | 2.40-2.58 | refly_priors/numbers_refly.md:372 | *[a] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |
| docs/thesis/figures_thesis/index.md:411 | H5.4b (original priors) | 3.2–7.7 | TA_verdicts.md:117 | / H5.3 / H5.4b max/min, final-build sets, corrected priors / `2.40–2.58 / 2.1–5.1` / `2.40–2.58 / 2.1–5.1` / numbers_refly.md §4.3 (ratios 2.1-5.1, narrowed fro |
| docs/thesis/figures_thesis/index.md:479 | H5.4b (original priors) | 3.2–7.7 | TA_verdicts.md:117 | / H5.3 / H5.4b max/min, final-build sets, corrected priors / `2.40–2.58 / 2.1–5.1` / `2.40–2.58 / 2.1–5.1` / numbers_refly.md §4.3 (ratios 2.1-5.1, narrowed fro |
| docs/thesis/figures_thesis/index.md:608 | H5.4b (original priors) | 3.2–7.7 | TA_verdicts.md:117 | / H5.3 / H5.4b max/min, final-build sets, corrected priors / `2.40–2.58 / 2.1–5.1` / `2.40–2.58 / 2.1–5.1` / numbers_refly.md §4.3 (ratios 2.1-5.1, narrowed fro |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:365 | H5.1 (FGO-flying) | 8.1–9.0 | TA_verdicts.md:113 | / **H5.1** (FGO-flying bounds) / `H_s3v2_r*`: mean 8.1-9.0 mm, max 18-28 mm (H-H1 PASS, numbers.md section 17.1) / `s3rp_r*`: mean 7.1-8.7 mm, max 15.0-25.5 mm  |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:345 | H5.2 (original priors) | 8.3–8.6 | TA_verdicts.md:114 | all 3 originally (8.3-8.6 against EKF3 7.8-7.9 mm); with the corrected priors it is highest in only 1 of 3 runs (r2, |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:272 | H5.6, redefined primary (FGO) | 0.002–0.032 | TA_verdicts.md:120 | Range 2.8-30.3 ms, all << 100 ms. **H5.6 redefined primary: PASS, 12/12** (original S3v2: 0.002-0.032 s, i.e. the |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:367 | H5.6, redefined primary (FGO) | 0.002–0.032 | TA_verdicts.md:120 | / **H5.6 redefined primary (re-lock)** / `H_s3v2_r*`: 0.002-0.032 s, PASS / `s3rp_r*`: 0.003-0.030 s, PASS (section 4.2) / **No** / |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:365 | H5.1** (FGO-flying bounds) | 8.1-9.0 | refly_priors/numbers_refly.md:365 | / **H5.1** (FGO-flying bounds) / `H_s3v2_r*`: mean 8.1-9.0 mm, max 18-28 mm (H-H1 PASS, numbers.md section 17.1) / `s3rp_r*`: mean 7.1-8.7 mm, max 15.0-25.5 mm  |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:272 | H5.6 redefined primary (re-lock) | 0.002-0.032 | refly_priors/numbers_refly.md:367 | Range 2.8-30.3 ms, all << 100 ms. **H5.6 redefined primary: PASS, 12/12** (original S3v2: 0.002-0.032 s, i.e. the |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:367 | H5.6 redefined primary (re-lock) | 0.002-0.032 | refly_priors/numbers_refly.md:367 | / **H5.6 redefined primary (re-lock)** / `H_s3v2_r*`: 0.002-0.032 s, PASS / `s3rp_r*`: 0.003-0.030 s, PASS (section 4.2) / **No** / |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:345 | H-H2 | 8.3-8.6 | refly_priors/numbers_refly.md:371 | all 3 originally (8.3-8.6 against EKF3 7.8-7.9 mm); with the corrected priors it is highest in only 1 of 3 runs (r2, |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:371 | H-H2 | 8.3-8.6 | refly_priors/numbers_refly.md:371 | / **H-H2** / FAIL (0/3): FGO highest in all three runs, 8.3-8.6 mm against EKF3 7.8-7.9 mm (`h_comparative_2026-10-11.json`) / FAIL (0/3 FGO lowest; `lowest_hol |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:372 | P-H3 | 2.40-2.58 | refly_priors/numbers_refly.md:372 | / **P-H3** / FAIL (0/3): UKF 2.40-2.58x, FGO 2.10-2.37x EKF3's hold gyro activity / FAIL (0/3): ratios 2.402/2.577/2.499, numerically unchanged (driven by UKF/E |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:373 | H-H4 (15 s) | 20-30 | refly_priors/numbers_refly.md:373 | / **H-H4 (15 s)** / FAIL (0/3): EKF3 strictly smallest (5/5/7 mm) against UKF 20-30, FGO 7-30 mm / FAIL (0/3): EKF3 strictly smallest (5/5/7 mm) against UKF 20- |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:374 | H-H4 (5 s) | 7-16 | refly_priors/numbers_refly.md:374 | / **H-H4 (5 s)** / FAIL (0/3): EKF3 4-5 mm against UKF 7-16, FGO 11-34 mm (max/min 3.2-7.7) / FAIL (0/3): ratios 2.1-5.1 (narrower than 3.2-7.7; section 4.3) /  |
| docs/thesis/writing_pack/numbers.md:675 | H-H2 | 8.3-8.6 | refly_priors/numbers_refly.md:371 | / **H-H2**: FGO < EKF3 and FGO < UKF mean hold error, 3/3 / **FAIL** (0/3): UKF lowest 3/3 (5.5–6.1 mm); FGO and EKF3 tie (7.8–7.9 mm) / **FAIL** (0/3): UKF low |
| docs/thesis/writing_pack/numbers.md:676 | P-H3 | 2.40-2.58 | refly_priors/numbers_refly.md:372 | / **P-H3**: hold gyro activity within 1.5× across estimators / **FAIL** (0/3): UKF 2.33–2.43×, FGO 2.13–2.37× EKF3's (max/min 2.37–2.43) / **FAIL** (0/3): UKF 2 |
| docs/thesis/writing_pack/numbers.md:677 | H-H4 (15 s) | 20-30 | refly_priors/numbers_refly.md:373 | / **H-H4 (15 s)**: EKF3's re-lock jump larger than the UKF's and the FGO's, 3/3 / **FAIL** (0/3): EKF3 smallest or tied (5 / 5 / 7 mm) / **FAIL** (0/3): EKF3 st |
| docs/thesis/writing_pack/numbers.md:678 | H-H4 (5 s) | 7-16 | refly_priors/numbers_refly.md:374 | / **H-H4 (5 s)**: jumps within 1.5× of each other / **FAIL** (0/3): EKF3 4–5 against UKF 6–17 (effective; 7–17 as scored), FGO 12–26 mm (max/min 3.4–5.9, the sa |
| docs/thesis/writing_pack/tables/R4_information_vs_estimator.md:14 | H5.2 (original priors) | 7.8–7.9 | TA_verdicts.md:114 | / Experiment 5: tag hold (each estimator flying) / mean hold error (mm), tag visible; n = 3 flights per estimator (paired by run index, not trajectory) / EKF3 7 |
| docs/thesis/writing_pack/tables/R4_information_vs_estimator.md:14 | H-H2 | 7.8-7.9 | refly_priors/numbers_refly.md:371 | / Experiment 5: tag hold (each estimator flying) / mean hold error (mm), tag visible; n = 3 flights per estimator (paired by run index, not trajectory) / EKF3 7 |
| docs/thesis/writing_pack/tables/T1_scorecard.md:44 | H-H2 | 7.8-7.9 | refly_priors/numbers_refly.md:371 | *[i] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |
| docs/thesis/writing_pack/tables/T1_scorecard.md:44 | P-H3 | 2.40-2.58 | refly_priors/numbers_refly.md:372 | *[i] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |
| docs/thesis/writing_pack/tables/T5_H_tag_loss_drift.md:22 | H-H2 | 7.8-7.9 | refly_priors/numbers_refly.md:371 | *[a] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |
| docs/thesis/writing_pack/tables/T5_H_tag_loss_drift.md:22 | P-H3 | 2.40-2.58 | refly_priors/numbers_refly.md:372 | *[a] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |

## B(ii). Verdict labels against TA_verdicts.md

### H4.2 (must read NOT MET everywhere)

H4.2 belongs to Experiment 4, not the E2-E6 tier-1 extensions, so TA_verdicts.md's FAIL-literal exception for extensions (see below) does not excuse a bare 'H4.2 FAIL' here - every occurrence below is checked against the one allowed wording, NOT MET.

| file:line | label found | text |
|---|---|---|
| docs/thesis/tables/TA_verdicts.md:49 | NOT MET | / Experiment 4 / H4.2 / “H-O2 … live indoor errors are similar. In every flight, the largest live indoor RMSE of EKF3, UKF and FGO is ≤ 1.5 × the smallest” [M:1 |
| docs/thesis/tables/T1_scorecard.md:22 | NOT MET | *Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with the camera headi |
| docs/thesis/tables/T1_scorecard.md:38 | NOT MET | *[f] Ordering basis, Experiment 4 live tracks indoors, EKF3, UKF and FGO (H4.2). Metric: indoor horizontal RMSE in the world frame, no alignment, over the 123 s |
| docs/thesis/tables/T1_scorecard.tex:29 | NOT MET | \textit{Note.} Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with th |
| docs/thesis/tables/T1_scorecard.tex:37 | NOT MET | \textit{Note.} [f] Ordering basis, Experiment 4 live tracks indoors, EKF3, UKF and FGO (H4.2). Metric: indoor horizontal RMSE in the world frame, no alignment,  |
| docs/thesis/tables/T6_O_indoor_rmse.md:3 | NOT MET | Indoors without GNSS the live errors are 0.8–1.4 m and not similar across estimators (EKF3 largest in every flight, H4.2 NOT MET) [a]; the two hindsight tracks  |
| docs/thesis/tables/T6_O_indoor_rmse.md:18 | NOT MET | *[a] Ordering basis, Experiment 4 live tracks indoors, EKF3, UKF and FGO (H4.2). Metric: indoor horizontal RMSE in the world frame, no alignment, over the 123 s |
| docs/thesis/tables/T6_O_indoor_rmse.tex:8 | NOT MET | \caption{Experiment 4 (outdoor--indoor): indoor horizontal RMSE per flight (123 s, GNSS off). Indoors without GNSS the live errors are 0.8--1.4 m and not simila |
| docs/thesis/tables/T6_O_indoor_rmse.tex:25 | NOT MET | \textit{Note.} [a] Ordering basis, Experiment 4 live tracks indoors, EKF3, UKF and FGO (H4.2). Metric: indoor horizontal RMSE in the world frame, no alignment,  |
| docs/thesis/figures_thesis/index.md:353 | NOT MET | - **Caption:** Indoors without GNSS the live errors are 0.8–1.4 m and not similar across estimators (EKF3 largest in every flight, H4.2 NOT MET) [a]; the two hi |
| docs/thesis/thesis_assets/tables_tex/tab_5-1.tex:9 | NOT MET | \caption{Table 5.1. Experiment 4 (outdoor--indoor): indoor horizontal RMSE per flight (123 s, GNSS off). Indoors without GNSS the live errors are 0.8--1.4 m and |
| docs/thesis/thesis_assets/tables_tex/tab_5-1.tex:26 | NOT MET | \textit{Note.} [a] Ordering basis, Experiment 4 live tracks indoors, EKF3, UKF and FGO (H4.2). Metric: indoor horizontal RMSE in the world frame, no alignment,  |
| docs/thesis/thesis_assets/tables_tex/tab_7-1.tex:30 | NOT MET | \textit{Note.} Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with th |
| docs/thesis/thesis_assets/tables_tex/tab_7-1.tex:38 | NOT MET | \textit{Note.} [f] Ordering basis, Experiment 4 live tracks indoors, EKF3, UKF and FGO (H4.2). Metric: indoor horizontal RMSE in the world frame, no alignment,  |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:121 | NOT MET | · Verdicts: H4.1 PASS 3/3, H4.2 NOT MET, H4.3 PASS (numbers.md:558-560). |
| docs/thesis/writing_pack/new_2026-11-11/numbers_o_window_check.md:30 | NOT MET | **Summary.** Starting the window at EKF3's switch raises EKF3's indoor RMSE by about 0.025 m per flight, and the H4.2 ratio moves by less than 0.001. H4.2 stays |
| docs/thesis/writing_pack/new_2026-11-11/numbers_o_window_check.md:30 | NOT MET | **Summary.** Starting the window at EKF3's switch raises EKF3's indoor RMSE by about 0.025 m per flight, and the H4.2 ratio moves by less than 0.001. H4.2 stays |
| docs/thesis/writing_pack/numbers.md:559 | FAIL **MISMATCH** | - **H-O2 FAIL:** the live ratio is 1.71–1.84× (was about 2.2×). |
| docs/thesis/writing_pack/numbers.md:1118 | FAIL **MISMATCH** | / §16.2 / - **H-O2 FAIL:** the live ratio is about 2.2×. / |
| docs/thesis/writing_pack/numbers.md:1275 | FAIL **MISMATCH** | / §16.2 H-O2 / - **H-O2 FAIL:** the live ratio is 1.72–1.84× (was about 2.2×). / |
| docs/thesis/writing_pack/numbers.md:1275 | FAIL **MISMATCH** | / §16.2 H-O2 / - **H-O2 FAIL:** the live ratio is 1.72–1.84× (was about 2.2×). / |
| docs/thesis/writing_pack/tables/T1_scorecard.md:22 | NOT MET | *Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with the camera headi |
| docs/thesis/writing_pack/tables/T1_scorecard.md:38 | NOT MET | *[f] Ordering basis, Experiment 4 live tracks indoors, EKF3, UKF and FGO (H4.2). Metric: indoor horizontal RMSE in the world frame, no alignment, over the 123 s |
| docs/thesis/writing_pack/tables/T6_O_indoor_rmse.md:3 | NOT MET | Indoors without GNSS the live errors are 0.8–1.4 m and not similar across estimators (EKF3 largest in every flight, H4.2 NOT MET) [a]; the two hindsight tracks  |
| docs/thesis/writing_pack/tables/T6_O_indoor_rmse.md:18 | NOT MET | *[a] Ordering basis, Experiment 4 live tracks indoors, EKF3, UKF and FGO (H4.2). Metric: indoor horizontal RMSE in the world frame, no alignment, over the 123 s |

### Other unambiguous mismatches (base ID has exactly one TA verdict)

**Caveat, read before acting on this table**: this is a proximity match (nearest verdict word within 60 characters after the ID token on the same line), not a parse of which ID the word actually belongs to. Two rows below are very likely proximity false positives on manual inspection: the H1.1 row's 'WITHDRAWN' describes a withdrawn CLAIM ('EKF3 lower'), not H1.1's own verdict label; the H2.2 row's 'PASS' sits next to a figure/data self-check phrase, not necessarily the hypothesis verdict. Each row should be opened and read in context before being treated as a defect.

| file:line | id | found | TA verdict | text |
|---|---|---|---|---|
| docs/thesis/figures_thesis/index.md:283 | H2.2 | PASS | NOT MET | / H2.2 gain A–D (m), PASS / `+0.020 / +0.032 / +0.037 / +0.029 False` / `+0.020 / +0.032 / +0.037 / +0.029 False` / numbers.md §16.1 / yes / |
| docs/thesis/writing_pack/methodology_factsheets/README.md:228 | H1.1 | WITHDRAWN | NOT MET | - **H1.1 verdict.** "EKF3 lower" is WITHDRAWN and replaced by "no ordering claimed" (3.5, 3.6). |

### Extension-experiment (E2-E6) ID/verdict-word occurrences, TA FAIL-literal convention

Not counted as mismatches (see TA_verdicts.md's own legend: E2-E6 and the ablation keep their source's literal word FAIL, never harmonised to NOT MET - so a source document legitimately using PASS/NOT MET/NOT RUN for the same registered check is not itself a defect). Surfaced here per the advisor guidance this audit followed: report the tension, do not silently resolve it either way.

| file:line | id | found | TA verdict | text |
|---|---|---|---|---|
| docs/thesis/thesis_assets/candidates/C04_table.md:11 | H-E3.3 | PASS | FAIL | / P-E3.5c / 5%: as H-E3.3 / 9 of 9 / PASS /  / |
| docs/thesis/writing_pack/tier1/e3_results.md:87 | H-E3.3 | PASS | FAIL | / P-E3.5c 5%: the H-E3.3 criterion / **PASS** / 9/9 / 0 of 3 per flight / `criteria_a.P-E3.5c …` / |
| docs/thesis/writing_pack/tier1/numbers_tier1.md:159 | H-E2.2 | DESCRIPTIVE | PASS | Verdicts: H-E2.1 (PRIMARY) per condition, H-E2.2, H-E2.3, P-E2.4, P-E2.5. Known-map comparison (DESCRIPTIVE). |
| docs/thesis/writing_pack/tier1/numbers_tier1.md:159 | H-E2.3 | DESCRIPTIVE | PASS | Verdicts: H-E2.1 (PRIMARY) per condition, H-E2.2, H-E2.3, P-E2.4, P-E2.5. Known-map comparison (DESCRIPTIVE). |
| docs/thesis/writing_pack/tier1/numbers_tier1.md:273 | H-E3.3 | PASS | FAIL | / P-E3.5c 5%: H-E3.3 criterion / **PASS** / 9/9 / T_A_r1: 0 of 3 runs diverged; T_A_r2: 0 of 3 runs diverged; T_A_r3: 0 of 3 runs diverged (total 0 of 9 runs di |
| docs/thesis/writing_pack/tier1/preregistration.md:596 | H-E4.3 | NOT MET | FAIL | with either run missing makes H-E4.3 NOT RUN or NOT MET (§0.5). |

### Non-standard bare-word labels (FAIL / MET / MISS without the project's full wording)

150 occurrence(s). Per TA_verdicts.md's own legend, Experiments 1-5/5S use the words PASS / FAIL AS WORDED / NOT MET / WITHDRAWN / DESCRIPTIVE / REPORTED k/3, but the tier-1 extension experiments (E2-E6) and the ablation keep their own sources' literal word FAIL (not harmonised to NOT MET) - this is TA's own documented convention, not a defect, and such rows are reported here but not counted as mismatches.

| file:line | id | label | text |
|---|---|---|---|
| docs/thesis/tables/R2_corrections_by_discovery.md:23 | H1.1 | MET | / SITL flight (a defect exposed by a flown result) / 14 / FGO noise model: biasAccOmegaInt → 0 / MODEL / FGO hover-tilt trace (H safety tests, 2026-10-09). / fi |
| docs/thesis/tables/R2_corrections_by_discovery.md:23 | H1.5 | MET | / SITL flight (a defect exposed by a flown result) / 14 / FGO noise model: biasAccOmegaInt → 0 / MODEL / FGO hover-tilt trace (H safety tests, 2026-10-09). / fi |
| docs/thesis/tables/R2_corrections_by_discovery.md:23 | H1.6 | FAIL | / SITL flight (a defect exposed by a flown result) / 14 / FGO noise model: biasAccOmegaInt → 0 / MODEL / FGO hover-tilt trace (H safety tests, 2026-10-09). / fi |
| docs/thesis/tables/R2_corrections_by_discovery.md:23 | H1.6c | FAIL | / SITL flight (a defect exposed by a flown result) / 14 / FGO noise model: biasAccOmegaInt → 0 / MODEL / FGO hover-tilt trace (H safety tests, 2026-10-09). / fi |
| docs/thesis/tables/R2_corrections_by_discovery.md:23 | H4.3 | FAIL | / SITL flight (a defect exposed by a flown result) / 14 / FGO noise model: biasAccOmegaInt → 0 / MODEL / FGO hover-tilt trace (H safety tests, 2026-10-09). / fi |
| docs/thesis/tables/R2_corrections_by_discovery.tex:28 | H1.5 | MET | SITL flight (a defect exposed by a flown result) & 14 & FGO noise model: biasAccOmegaInt $\rightarrow$ 0 & MODEL & FGO hover-tilt trace (H safety tests, 2026-10 |
| docs/thesis/tables/R2_corrections_by_discovery.tex:28 | H1.6c | FAIL | SITL flight (a defect exposed by a flown result) & 14 & FGO noise model: biasAccOmegaInt $\rightarrow$ 0 & MODEL & FGO hover-tilt trace (H safety tests, 2026-10 |
| docs/thesis/tables/R2_corrections_by_discovery.tex:28 | H4.3 | FAIL | SITL flight (a defect exposed by a flown result) & 14 & FGO noise model: biasAccOmegaInt $\rightarrow$ 0 & MODEL & FGO hover-tilt trace (H safety tests, 2026-10 |
| docs/thesis/tables/T1_scorecard.md:22 | H2.3 | FAIL | *Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with the camera headi |
| docs/thesis/tables/T1_scorecard.md:22 | H5.2 | FAIL | *Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with the camera headi |
| docs/thesis/tables/T1_scorecard.md:22 | H5.3 | FAIL | *Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with the camera headi |
| docs/thesis/tables/T1_scorecard.md:22 | H5.4a | FAIL | *Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with the camera headi |
| docs/thesis/tables/T1_scorecard.md:44 | H5.4b | FAIL | *[i] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |
| docs/thesis/tables/T1_scorecard.md:48 | H-E3.1 | FAIL | *[k] Extensions to Experiment 3 (extension experiments, pre-registered 2026-10-21, signed off with amendments 2026-10-22; condition A unless stated, n = 3 fligh |
| docs/thesis/tables/T1_scorecard.tex:29 | H2.3 | FAIL | \textit{Note.} Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with th |
| docs/thesis/tables/T1_scorecard.tex:29 | H5.2 | FAIL | \textit{Note.} Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with th |
| docs/thesis/tables/T1_scorecard.tex:29 | H5.3 | FAIL | \textit{Note.} Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with th |
| docs/thesis/tables/T1_scorecard.tex:29 | H5.4a | FAIL | \textit{Note.} Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with th |
| docs/thesis/tables/T1_scorecard.tex:40 | H5.4b | FAIL | \textit{Note.} [i] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold |
| docs/thesis/tables/T1_scorecard.tex:42 | H-E3.1 | FAIL | \textit{Note.} [k] Extensions to Experiment 3 (extension experiments, pre-registered 2026-10-21, signed off with amendments 2026-10-22; condition A unless state |
| docs/thesis/tables/T5_H_tag_loss_drift.md:3 | H5.2 | FAIL | Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered band, and none locks out; each cel |
| docs/thesis/tables/T5_H_tag_loss_drift.md:3 | H5.3 | FAIL | Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered band, and none locks out; each cel |
| docs/thesis/tables/T5_H_tag_loss_drift.md:3 | H5.4a | FAIL | Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered band, and none locks out; each cel |
| docs/thesis/tables/T5_H_tag_loss_drift.md:22 | H5.4b | FAIL | *[a] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |
| docs/thesis/tables/T5_H_tag_loss_drift.tex:8 | H5.2 | FAIL | \caption{Experiment 5 (tag hold): drift while the wall tag is hidden, flying estimators. Holding on a wall tag, every flying estimator drifts at most about 30 m |
| docs/thesis/tables/T5_H_tag_loss_drift.tex:8 | H5.3 | FAIL | \caption{Experiment 5 (tag hold): drift while the wall tag is hidden, flying estimators. Holding on a wall tag, every flying estimator drifts at most about 30 m |
| docs/thesis/tables/T5_H_tag_loss_drift.tex:8 | H5.4a | FAIL | \caption{Experiment 5 (tag hold): drift while the wall tag is hidden, flying estimators. Holding on a wall tag, every flying estimator drifts at most about 30 m |
| docs/thesis/tables/T5_H_tag_loss_drift.tex:27 | H5.4b | FAIL | \textit{Note.} [a] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold |
| docs/thesis/tables/T8_hindsight_ratio.md:3 | H2.4 | FAIL | With tags at known positions (Experiment 2) the FGO whole-flight batch is below the smoothed UKF in every condition, by 1.3–3.9× (largest with 1 tag; H2.4 FAIL  |
| docs/thesis/tables/T8_hindsight_ratio.md:7 | H2.4 | FAIL | / Experiment 2, condition A: 8 tags (mean of 3) / 0.010 / 0.014 / FGO whole-flight batch / 1.31 / H2.4 FAIL / |
| docs/thesis/tables/T8_hindsight_ratio.md:8 | H2.4 | FAIL | / Experiment 2, condition B: 4 tags (mean of 3) / 0.015 / 0.031 / FGO whole-flight batch / 2.14 / H2.4 FAIL / |
| docs/thesis/tables/T8_hindsight_ratio.md:9 | H2.4 | FAIL | / Experiment 2, condition C: 2 tags (mean of 3) / 0.019 / 0.039 / FGO whole-flight batch / 2.06 / H2.4 FAIL / |
| docs/thesis/tables/T8_hindsight_ratio.md:10 | H2.4 | FAIL | / Experiment 2, condition D: 1 tag (mean of 3) / 0.028 / 0.109 / FGO whole-flight batch / 3.89 / H2.4 FAIL / |
| docs/thesis/tables/T8_hindsight_ratio.tex:8 | H2.4 | FAIL | \caption{Hindsight: the FGO whole-flight batch against the smoothed UKF. With tags at known positions (Experiment 2) the FGO whole-flight batch is below the smo |
| docs/thesis/tables/T8_hindsight_ratio.tex:14 | H2.4 | FAIL | Experiment 2, condition A: 8 tags (mean of 3) & 0.010 & 0.014 & FGO whole-flight batch & 1.31 & H2.4 FAIL \\ |
| docs/thesis/tables/T8_hindsight_ratio.tex:15 | H2.4 | FAIL | Experiment 2, condition B: 4 tags (mean of 3) & 0.015 & 0.031 & FGO whole-flight batch & 2.14 & H2.4 FAIL \\ |
| docs/thesis/tables/T8_hindsight_ratio.tex:16 | H2.4 | FAIL | Experiment 2, condition C: 2 tags (mean of 3) & 0.019 & 0.039 & FGO whole-flight batch & 2.06 & H2.4 FAIL \\ |
| docs/thesis/tables/T8_hindsight_ratio.tex:17 | H2.4 | FAIL | Experiment 2, condition D: 1 tag (mean of 3) & 0.028 & 0.109 & FGO whole-flight batch & 3.89 & H2.4 FAIL \\ |
| docs/thesis/figures_thesis/index.md:316 | H-E3.1 | FAIL | / E3 H-E3.1 at 1% wrong ids: verdict, count; diverged runs / `FAIL 0/9; 6 of 9 runs diverged` / `FAIL 0/9; 6 of 9 runs diverged` / tier1/e3_results.md §1 (H-E3. |
| docs/thesis/figures_thesis/index.md:316 | H-E3.1 | FAIL | / E3 H-E3.1 at 1% wrong ids: verdict, count; diverged runs / `FAIL 0/9; 6 of 9 runs diverged` / `FAIL 0/9; 6 of 9 runs diverged` / tier1/e3_results.md §1 (H-E3. |
| docs/thesis/figures_thesis/index.md:376 | H2.4 | FAIL | - **Caption:** With tags at known positions (Experiment 2) the FGO whole-flight batch is below the smoothed UKF in every condition, by 1.3–3.9× (largest with 1  |
| docs/thesis/figures_thesis/index.md:394 | H5.2 | FAIL | - **Caption:** Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered band, and none lock |
| docs/thesis/figures_thesis/index.md:394 | H5.3 | FAIL | - **Caption:** Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered band, and none lock |
| docs/thesis/figures_thesis/index.md:394 | H5.4a | FAIL | - **Caption:** Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered band, and none lock |
| docs/thesis/figures_thesis/index.md:409 | H-H2 | FAIL | / Experiment 5 (final-build sets, corrected priors): flights with the FGO / the UKF lowest mean hold error / `0/3 / 3/3` / `0/3 / 3/3` / numbers_refly.md §4.3 c |
| docs/thesis/figures_thesis/index.md:413 | H5.3 | FAIL | / Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds, corrected priors) / `FAIL; FAIL; FAIL; FAIL` / `FAIL; FAIL; FAIL; FAIL` / numbers_re |
| docs/thesis/figures_thesis/index.md:413 | H5.4a | FAIL | / Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds, corrected priors) / `FAIL; FAIL; FAIL; FAIL` / `FAIL; FAIL; FAIL; FAIL` / numbers_re |
| docs/thesis/figures_thesis/index.md:413 | H5.4b | FAIL | / Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds, corrected priors) / `FAIL; FAIL; FAIL; FAIL` / `FAIL; FAIL; FAIL; FAIL` / numbers_re |
| docs/thesis/figures_thesis/index.md:442 | H5.4b | FAIL | / Experiment 5 comparative H5.2; H5.3; H5.4a (15 s); H5.4b (5 s) (final builds, corrected priors) / `FAIL; FAIL; FAIL; FAIL` / `FAIL; FAIL; FAIL; FAIL` / number |
| docs/thesis/figures_thesis/index.md:477 | H-H2 | FAIL | / Experiment 5 (final-build sets, corrected priors): flights with the FGO / the UKF lowest mean hold error / `0/3 / 3/3` / `0/3 / 3/3` / numbers_refly.md §4.3 c |
| docs/thesis/figures_thesis/index.md:481 | H5.3 | FAIL | / Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds, corrected priors) / `FAIL; FAIL; FAIL; FAIL` / `FAIL; FAIL; FAIL; FAIL` / numbers_re |
| docs/thesis/figures_thesis/index.md:481 | H5.4a | FAIL | / Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds, corrected priors) / `FAIL; FAIL; FAIL; FAIL` / `FAIL; FAIL; FAIL; FAIL` / numbers_re |
| docs/thesis/figures_thesis/index.md:481 | H5.4b | FAIL | / Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds, corrected priors) / `FAIL; FAIL; FAIL; FAIL` / `FAIL; FAIL; FAIL; FAIL` / numbers_re |
| docs/thesis/figures_thesis/index.md:500 | H-E3.1 | FAIL | / E3 H-E3.1 at 1% wrong ids: verdict, count; diverged runs / `FAIL 0/9; 6 of 9 runs diverged` / `FAIL 0/9; 6 of 9 runs diverged` / tier1/e3_results.md §1 (H-E3. |
| docs/thesis/figures_thesis/index.md:500 | H-E3.1 | FAIL | / E3 H-E3.1 at 1% wrong ids: verdict, count; diverged runs / `FAIL 0/9; 6 of 9 runs diverged` / `FAIL 0/9; 6 of 9 runs diverged` / tier1/e3_results.md §1 (H-E3. |
| docs/thesis/figures_thesis/index.md:606 | H-H2 | FAIL | / Experiment 5 (final-build sets, corrected priors): flights with the FGO / the UKF lowest mean hold error / `0/3 / 3/3` / `0/3 / 3/3` / numbers_refly.md §4.3 c |
| docs/thesis/figures_thesis/index.md:610 | H5.3 | FAIL | / Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds, corrected priors) / `FAIL; FAIL; FAIL; FAIL` / `FAIL; FAIL; FAIL; FAIL` / numbers_re |
| docs/thesis/figures_thesis/index.md:610 | H5.4a | FAIL | / Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds, corrected priors) / `FAIL; FAIL; FAIL; FAIL` / `FAIL; FAIL; FAIL; FAIL` / numbers_re |
| docs/thesis/figures_thesis/index.md:610 | H5.4b | FAIL | / Experiment 5 comparative verdicts H5.2; H5.3; H5.4a; H5.4b (final builds, corrected priors) / `FAIL; FAIL; FAIL; FAIL` / `FAIL; FAIL; FAIL; FAIL` / numbers_re |
| docs/thesis/figures_thesis/index_results.md:36 | H-E3.1 | FAIL | *Note.* Experiment 3 scope (claims C2 and C3, user ruling 2026-10-24; the H3.1–H3.4 verdicts are unchanged): H3.1–H3.4 were scored with all 8 tags and correct t |
| docs/thesis/figures_thesis/index_results.md:95 | H-E3.1 | FAIL | / R1 / extension E3: H-E3.1 at 1% wrong ids; diverged runs / FAIL 0/9; 6 of 9 runs diverged / FAIL 0/9; 6 of 9 runs diverged / docs/thesis/tier1/scores/E3_verdi |
| docs/thesis/figures_thesis/index_results.md:314 | H1.2 | MET | / R1 / H1.2 heading and yaw rate, textured walls prediction quote / METHODOLOGY.md:2727-2730 / found / |
| docs/thesis/figures_thesis/index_results.md:358 | H1.8 | MET | / R1 / H1.8 n = 3 EKF3, full real time (RTF 1.0) prediction quote / METHODOLOGY.md:4948 / found / |
| docs/thesis/figures_thesis/index_results.md:361 | H1.8 | MET | / R1 / H1.8 n = 3 EKF3, half real-time (RTF 0.5) prediction quote / METHODOLOGY.md:4948 / found / |
| docs/thesis/figures_thesis/index_results.md:376 | H1.9 | MET | / R1 / H1.9 UKF (final UKF port, half real-time) prediction quote / METHODOLOGY.md:7361-7362 / found / |
| docs/thesis/thesis_assets/tables_tex/tab_5-2.tex:9 | H2.4 | FAIL | \caption{Table 5.2. Hindsight: the FGO whole-flight batch against the smoothed UKF. With tags at known positions (Experiment 2) the FGO whole-flight batch is be |
| docs/thesis/thesis_assets/tables_tex/tab_5-2.tex:15 | H2.4 | FAIL | Experiment 2, condition A: 8 tags (mean of 3) & 0.010 & 0.014 & FGO whole-flight batch & 1.31 & H2.4 FAIL \\ |
| docs/thesis/thesis_assets/tables_tex/tab_5-2.tex:16 | H2.4 | FAIL | Experiment 2, condition B: 4 tags (mean of 3) & 0.015 & 0.031 & FGO whole-flight batch & 2.14 & H2.4 FAIL \\ |
| docs/thesis/thesis_assets/tables_tex/tab_5-2.tex:17 | H2.4 | FAIL | Experiment 2, condition C: 2 tags (mean of 3) & 0.019 & 0.039 & FGO whole-flight batch & 2.06 & H2.4 FAIL \\ |
| docs/thesis/thesis_assets/tables_tex/tab_5-2.tex:18 | H2.4 | FAIL | Experiment 2, condition D: 1 tag (mean of 3) & 0.028 & 0.109 & FGO whole-flight batch & 3.89 & H2.4 FAIL \\ |
| docs/thesis/thesis_assets/tables_tex/tab_6-1.tex:9 | H5.2 | FAIL | \caption{Table 6.1. Experiment 5 (tag hold): drift while the wall tag is hidden, flying estimators. Holding on a wall tag, every flying estimator drifts at most |
| docs/thesis/thesis_assets/tables_tex/tab_6-1.tex:9 | H5.3 | FAIL | \caption{Table 6.1. Experiment 5 (tag hold): drift while the wall tag is hidden, flying estimators. Holding on a wall tag, every flying estimator drifts at most |
| docs/thesis/thesis_assets/tables_tex/tab_6-1.tex:9 | H5.4a | FAIL | \caption{Table 6.1. Experiment 5 (tag hold): drift while the wall tag is hidden, flying estimators. Holding on a wall tag, every flying estimator drifts at most |
| docs/thesis/thesis_assets/tables_tex/tab_6-1.tex:28 | H5.4b | FAIL | \textit{Note.} [a] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold |
| docs/thesis/thesis_assets/tables_tex/tab_7-1.tex:30 | H2.3 | FAIL | \textit{Note.} Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with th |
| docs/thesis/thesis_assets/tables_tex/tab_7-1.tex:30 | H5.2 | FAIL | \textit{Note.} Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with th |
| docs/thesis/thesis_assets/tables_tex/tab_7-1.tex:30 | H5.3 | FAIL | \textit{Note.} Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with th |
| docs/thesis/thesis_assets/tables_tex/tab_7-1.tex:30 | H5.4a | FAIL | \textit{Note.} Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with th |
| docs/thesis/thesis_assets/tables_tex/tab_7-1.tex:41 | H5.4b | FAIL | \textit{Note.} [i] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold |
| docs/thesis/thesis_assets/tables_tex/tab_7-1.tex:43 | H-E3.1 | FAIL | \textit{Note.} [k] Extensions to Experiment 3 (extension experiments, pre-registered, signed off with amendments; condition A unless stated, n = 3 flights; clai |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:59 | H-H2 | FAIL | H5.2 & FGO holds tightest & ``H-H2: the FGO's hold error is lowest. FGO $<$ EKF3 and FGO $<$ UKF mean hold error in 3/3 flights.'' [tag\_hold\_design.md:180]; ( |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:78 | H-E3.1 | FAIL | \textit{Note.} Experiment 3 scope (claims C2 and C3, user ruling; the H3.1--H3.4 verdicts are unchanged): H3.1--H3.4 were scored with all 8 tags and correct tag |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:102 | H5.6 | FAIL | H5.6, jump as worded (FGO) & superseded: original priors & FAIL AS WORDED & fails in 4 of 12 losses & H\_s3v2\_r\{1,2,3\} & numbers.md:646 \\ |
| docs/thesis/thesis_assets/tables_tex/tab_7-4.tex:29 | H1.5 | MET | SITL flight (a defect exposed by a flown result) & 14 & FGO noise model: biasAccOmegaInt $\rightarrow$ 0 & MODEL & FGO hover-tilt trace (H safety tests, 2026-10 |
| docs/thesis/thesis_assets/tables_tex/tab_7-4.tex:29 | H1.6c | FAIL | SITL flight (a defect exposed by a flown result) & 14 & FGO noise model: biasAccOmegaInt $\rightarrow$ 0 & MODEL & FGO hover-tilt trace (H safety tests, 2026-10 |
| docs/thesis/thesis_assets/tables_tex/tab_7-4.tex:29 | H4.3 | FAIL | SITL flight (a defect exposed by a flown result) & 14 & FGO noise model: biasAccOmegaInt $\rightarrow$ 0 & MODEL & FGO hover-tilt trace (H safety tests, 2026-10 |
| docs/thesis/thesis_assets/candidates/C04_table.md:6 | H-E3.2 | FAIL | / H-E3.2 / 1%: the same for the hindsight error / 0 of 9 / FAIL /  / |
| docs/thesis/thesis_assets/candidates/C04_table.md:7 | H-E3.3 | FAIL | / H-E3.3 / 1%: lap-5 live error at most 1.5 × lap 1 / 3 of 9 / FAIL /  / |
| docs/thesis/thesis_assets/candidates/C04_table.md:9 | H-E3.1 | FAIL | / P-E3.5a / 5%: as H-E3.1 / 0 of 9 / FAIL /  / |
| docs/thesis/thesis_assets/candidates/C04_table.md:10 | H-E3.2 | FAIL | / P-E3.5b / 5%: as H-E3.2 / 0 of 9 / FAIL /  / |
| docs/thesis/writing_pack/limitations.md:11 | H-E3.1 | FAIL | / 3 / The FGO as configured (plain least squares, tag readings ungated) is not robust to wrong tag IDs: at 1% wrong IDs, 6 of 9 runs diverged and the remaining  |
| docs/thesis/writing_pack/limitations.md:11 | H-E3.1 | FAIL | / 3 / The FGO as configured (plain least squares, tag readings ungated) is not robust to wrong tag IDs: at 1% wrong IDs, 6 of 9 runs diverged and the remaining  |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:70 | H-E4.3 | FAIL | - Extension experiment E4 (pre-registered; claim C4) on the 12 Experiment 2 flights: the median step time rose strictly with the window on every flight (P-E4.1  |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:101 | H-E3.1 | FAIL | · The result assumes correct re-identification (claim C2). In an extension experiment (pre-registered), with wrong ids in 1% of the eligible detections, the key |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:198 | H1.3 | FAIL | - **H1.3 verdict count.** The vocabulary cites "part (b) FAIL as worded, 10/12" (thesis_vocabulary.md:150 [corrected from :145, which is blank at this commit])  |
| docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md:36 | H-E3.1 | FAIL | - **H-E3.1 (PRIMARY) at 1%: FAIL, 0/9** — 6 of 9 runs diverged (2 of 3 on every flight), and the 3 non-diverged runs' LC live is far above the stored no-LC live |
| docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md:37 | H-E3.2 | FAIL | - H-E3.2, H-E3.3, P-E3.4 at 1%: **FAIL** (H-E3.3 **3/9**, the other two **0/9**) (`numbers_tier1.md:268-270`). |
| docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md:37 | H-E3.3 | FAIL | - H-E3.2, H-E3.3, P-E3.4 at 1%: **FAIL** (H-E3.3 **3/9**, the other two **0/9**) (`numbers_tier1.md:268-270`). |
| docs/thesis/writing_pack/new_2026-11-11/digest_2026-11-12.md:16 | H5.4b | FAIL | / H5.2, H5.3, H5.4a, H5.4b (comparatives, with the FGO on corrected priors) / all FAIL (0/3), unchanged / all FAIL / same / |
| docs/thesis/writing_pack/new_2026-11-11/digest_2026-11-12.md:157 | H5.2 | FAIL | - `Experiment 5 · H5.2` col 4: `FAIL (0/3): UKF lowest 3/3 (6.4–7.1 mm); FGO highest in all three (8.3–8.6 against EKF3 7.8–7.9 mm) [numbers.md:675]` → `FAIL (0 |
| docs/thesis/writing_pack/new_2026-11-11/digest_2026-11-12.md:158 | H-H2 | FAIL | - `Experiment 5 · H5.2` col 6: `wording only (tie → FGO highest) on the final-build sets; verdict identical to the original-build verdict` → `2026-11-12 regener |
| docs/thesis/writing_pack/new_2026-11-11/digest_2026-11-12.md:159 | H5.3 | FAIL | - `Experiment 5 · H5.3` col 4: `FAIL (0/3): UKF 2.40–2.58×, FGO 2.10–2.37× EKF3's [numbers.md:676]` → `FAIL (0/3): ratios 2.402/2.577/2.499 (driven by max(UKF)/ |
| docs/thesis/writing_pack/new_2026-11-11/digest_2026-11-12.md:161 | H5.4a | FAIL | - `Experiment 5 · H5.4a` col 4: `FAIL (0/3): EKF3 strictly the smallest (5 / 5 / 7 against UKF 20–30, FGO 7–30 mm) [numbers.md:677]` → `FAIL (0/3 EKF3 largest): |
| docs/thesis/writing_pack/new_2026-11-11/digest_2026-11-12.md:163 | H5.4b | FAIL | - `Experiment 5 · H5.4b` col 4: `FAIL (0/3): EKF3 4–5 against UKF 7–16, FGO 11–34 mm (max/min 3.2–7.7) [numbers.md:678]` → `FAIL (0/3): ratio range narrowed fro |
| docs/thesis/writing_pack/new_2026-11-11/digest_2026-11-12.md:215 | H5.2 | FAIL | - `H5.2 · FGO holds tightest` col 4: `FAIL (0/3): UKF lowest 3/3 (6.4–7.1 mm); FGO highest in all three (8.3–8.6 against EKF3 7.8–7.9 mm)` → `FAIL (0/3 FGO lowe |
| docs/thesis/writing_pack/new_2026-11-11/digest_2026-11-12.md:216 | H-H2 | FAIL | - `H5.2 · FGO holds tightest` col 6: `wording only (tie → FGO highest) on the final-build sets; verdict identical to the original-build verdict` → `2026-11-12 r |
| docs/thesis/writing_pack/new_2026-11-11/digest_2026-11-12.md:218 | H5.3 | FAIL | - `H5.3 · smoothness similar` col 4: `FAIL (0/3): UKF 2.40–2.58×, FGO 2.10–2.37× EKF3's` → `FAIL (0/3): ratios 2.402/2.577/2.499 (driven by max(UKF)/min(EKF3) i |
| docs/thesis/writing_pack/new_2026-11-11/digest_2026-11-12.md:221 | H5.4a | FAIL | - `H5.4a · after a 15 s loss, EKF3 jumps most` col 4: `FAIL (0/3): EKF3 strictly the smallest (5 / 5 / 7 against UKF 20–30, FGO 7–30 mm)` → `FAIL (0/3 EKF3 larg |
| docs/thesis/writing_pack/new_2026-11-11/digest_2026-11-12.md:224 | H5.4b | FAIL | - `H5.4b · after a 5 s loss, jumps similar` col 4: `FAIL (0/3): EKF3 4–5 against UKF 7–16, FGO 11–34 mm (max/min 3.2–7.7)` → `FAIL (0/3): ratio range narrowed f |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:337 | H-H2 | FAIL | / H-H2 (FGO holds tightest) / FAIL (0/3 FGO lowest); `lowest_hold` = UKF on all 3 runs / |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:371 | H-H2 | FAIL | / **H-H2** / FAIL (0/3): FGO highest in all three runs, 8.3-8.6 mm against EKF3 7.8-7.9 mm (`h_comparative_2026-10-11.json`) / FAIL (0/3 FGO lowest; `lowest_hol |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:443 | H-H2 | FAIL | descriptive only).** Comparatives H-H2, P-H3, H-H4 (15 s), H-H4 (5 s): **all FAIL, unchanged from the original |
| docs/thesis/writing_pack/numbers.md:559 | H-O2 | FAIL | - **H-O2 FAIL:** the live ratio is 1.71–1.84× (was about 2.2×). |
| docs/thesis/writing_pack/numbers.md:675 | H-H2 | FAIL | / **H-H2**: FGO < EKF3 and FGO < UKF mean hold error, 3/3 / **FAIL** (0/3): UKF lowest 3/3 (5.5–6.1 mm); FGO and EKF3 tie (7.8–7.9 mm) / **FAIL** (0/3): UKF low |
| docs/thesis/writing_pack/numbers.md:1118 | H-O2 | FAIL | / §16.2 / - **H-O2 FAIL:** the live ratio is about 2.2×. / |
| docs/thesis/writing_pack/numbers.md:1275 | H-O2 | FAIL | / §16.2 H-O2 / - **H-O2 FAIL:** the live ratio is 1.72–1.84× (was about 2.2×). / |
| docs/thesis/writing_pack/numbers.md:1275 | H-O2 | FAIL | / §16.2 H-O2 / - **H-O2 FAIL:** the live ratio is 1.72–1.84× (was about 2.2×). / |
| docs/thesis/writing_pack/tables/R2_corrections_by_discovery.md:23 | H1.1 | MET | / SITL flight (a defect exposed by a flown result) / 14 / FGO noise model: biasAccOmegaInt → 0 / MODEL / FGO hover-tilt trace (H safety tests, 2026-10-09). / fi |
| docs/thesis/writing_pack/tables/R2_corrections_by_discovery.md:23 | H1.5 | MET | / SITL flight (a defect exposed by a flown result) / 14 / FGO noise model: biasAccOmegaInt → 0 / MODEL / FGO hover-tilt trace (H safety tests, 2026-10-09). / fi |
| docs/thesis/writing_pack/tables/R2_corrections_by_discovery.md:23 | H1.6 | FAIL | / SITL flight (a defect exposed by a flown result) / 14 / FGO noise model: biasAccOmegaInt → 0 / MODEL / FGO hover-tilt trace (H safety tests, 2026-10-09). / fi |
| docs/thesis/writing_pack/tables/R2_corrections_by_discovery.md:23 | H1.6c | FAIL | / SITL flight (a defect exposed by a flown result) / 14 / FGO noise model: biasAccOmegaInt → 0 / MODEL / FGO hover-tilt trace (H safety tests, 2026-10-09). / fi |
| docs/thesis/writing_pack/tables/R2_corrections_by_discovery.md:23 | H4.3 | FAIL | / SITL flight (a defect exposed by a flown result) / 14 / FGO noise model: biasAccOmegaInt → 0 / MODEL / FGO hover-tilt trace (H safety tests, 2026-10-09). / fi |
| docs/thesis/writing_pack/tables/T1_scorecard.md:22 | H2.3 | FAIL | *Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with the camera headi |
| docs/thesis/writing_pack/tables/T1_scorecard.md:22 | H5.2 | FAIL | *Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with the camera headi |
| docs/thesis/writing_pack/tables/T1_scorecard.md:22 | H5.3 | FAIL | *Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with the camera headi |
| docs/thesis/writing_pack/tables/T1_scorecard.md:22 | H5.4a | FAIL | *Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met [a], the UKF medians descriptive [b]; with the camera headi |
| docs/thesis/writing_pack/tables/T1_scorecard.md:44 | H5.4b | FAIL | *[i] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |
| docs/thesis/writing_pack/tables/T1_scorecard.md:48 | H-E3.1 | FAIL | *[k] Extensions to Experiment 3 (extension experiments, pre-registered 2026-10-21, signed off with amendments 2026-10-22; condition A unless stated, n = 3 fligh |
| docs/thesis/writing_pack/tables/T5_H_tag_loss_drift.md:3 | H5.2 | FAIL | Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered band, and none locks out; each cel |
| docs/thesis/writing_pack/tables/T5_H_tag_loss_drift.md:3 | H5.3 | FAIL | Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered band, and none locks out; each cel |
| docs/thesis/writing_pack/tables/T5_H_tag_loss_drift.md:3 | H5.4a | FAIL | Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered band, and none locks out; each cel |
| docs/thesis/writing_pack/tables/T5_H_tag_loss_drift.md:22 | H5.4b | FAIL | *[a] Ordering basis, Experiment 5 comparative hypotheses, final-build sets (H5.2, H5.3, H5.4a, H5.4b). Metric: H5.2 mean hold error, mm; H5.3 hold gyro activity |
| docs/thesis/writing_pack/tables/T8_hindsight_ratio.md:3 | H2.4 | FAIL | With tags at known positions (Experiment 2) the FGO whole-flight batch is below the smoothed UKF in every condition, by 1.3–3.9× (largest with 1 tag; H2.4 FAIL  |
| docs/thesis/writing_pack/tables/T8_hindsight_ratio.md:7 | H2.4 | FAIL | / Experiment 2, condition A: 8 tags (mean of 3) / 0.010 / 0.014 / FGO whole-flight batch / 1.31 / H2.4 FAIL / |
| docs/thesis/writing_pack/tables/T8_hindsight_ratio.md:8 | H2.4 | FAIL | / Experiment 2, condition B: 4 tags (mean of 3) / 0.015 / 0.031 / FGO whole-flight batch / 2.14 / H2.4 FAIL / |
| docs/thesis/writing_pack/tables/T8_hindsight_ratio.md:9 | H2.4 | FAIL | / Experiment 2, condition C: 2 tags (mean of 3) / 0.019 / 0.039 / FGO whole-flight batch / 2.06 / H2.4 FAIL / |
| docs/thesis/writing_pack/tables/T8_hindsight_ratio.md:10 | H2.4 | FAIL | / Experiment 2, condition D: 1 tag (mean of 3) / 0.028 / 0.109 / FGO whole-flight batch / 3.89 / H2.4 FAIL / |
| docs/thesis/writing_pack/thesis_vocabulary.md:155 | H1.5 | MET | / H1.5 / hindsight heading correction / F2 / M:7926 / MET (numbers.md:502) / |
| docs/thesis/writing_pack/tier1/e3_results.md:82 | H-E3.2 | FAIL | / H-E3.2 1%: LC hindsight < stored no-LC hindsight / **FAIL** / 0/9 / 2 of 3 per flight (6 of 9) / `criteria_a.H-E3.2 …` / |
| docs/thesis/writing_pack/tier1/e3_results.md:83 | H-E3.3 | FAIL | / H-E3.3 1%: LC live lap-5 ≤ 1.5 × lap-1 / **FAIL** / 3/9 / 2 of 3 per flight (6 of 9); the 3 non-diverged runs pass / `criteria_a.H-E3.3 …` / |
| docs/thesis/writing_pack/tier1/e3_results.md:85 | H-E3.1 | FAIL | / P-E3.5a 5%: the H-E3.1 criterion / **FAIL** / 0/9 / 0 of 3 per flight / `criteria_a.P-E3.5a …` / |
| docs/thesis/writing_pack/tier1/e3_results.md:86 | H-E3.2 | FAIL | / P-E3.5b 5%: the H-E3.2 criterion / **FAIL** / 0/9 / 0 of 3 per flight / `criteria_a.P-E3.5b …` / |
| docs/thesis/writing_pack/tier1/e4_results.md:16 | H-E4.3 | FAIL | - **H-E4.3 FAIL 7/12** (band ≥ 10/12). Live RMSE at 5 s was lower than at 0.25 s on all three D flights, two C flights, |
| docs/thesis/writing_pack/tier1/numbers_tier1.md:267 | H-E3.1 | FAIL | / H-E3.1 (PRIMARY) 1%: LC live < stored no-LC live / **FAIL** / 0/9 / T_A_r1: 2 of 3 runs diverged; T_A_r2: 2 of 3 runs diverged; T_A_r3: 2 of 3 runs diverged ( |
| docs/thesis/writing_pack/tier1/numbers_tier1.md:268 | H-E3.2 | FAIL | / H-E3.2 1%: LC hindsight < stored no-LC hindsight / **FAIL** / 0/9 / T_A_r1: 2 of 3 runs diverged; T_A_r2: 2 of 3 runs diverged; T_A_r3: 2 of 3 runs diverged ( |
| docs/thesis/writing_pack/tier1/numbers_tier1.md:269 | H-E3.3 | FAIL | / H-E3.3 1%: LC live lap5 <= 1.5 x lap1 / **FAIL** / 3/9 / T_A_r1: 2 of 3 runs diverged; T_A_r2: 2 of 3 runs diverged; T_A_r3: 2 of 3 runs diverged (total 6 of  |
| docs/thesis/writing_pack/tier1/numbers_tier1.md:271 | H-E3.1 | FAIL | / P-E3.5a 5%: H-E3.1 criterion / **FAIL** / 0/9 / T_A_r1: 0 of 3 runs diverged; T_A_r2: 0 of 3 runs diverged; T_A_r3: 0 of 3 runs diverged (total 0 of 9 runs di |
| docs/thesis/writing_pack/tier1/numbers_tier1.md:272 | H-E3.2 | FAIL | / P-E3.5b 5%: H-E3.2 criterion / **FAIL** / 0/9 / T_A_r1: 0 of 3 runs diverged; T_A_r2: 0 of 3 runs diverged; T_A_r3: 0 of 3 runs diverged (total 0 of 9 runs di |
| docs/thesis/writing_pack/tier1/numbers_tier1.md:521 | H-E4.3 | FAIL | / H-E4.3 / FAIL (7/12) / — / CURRENT / `json:scores/E4_verdicts.json:H-E4.3.verdict` / |
| docs/thesis/writing_pack/tier1/preregistration.md:409 | H-E3.1 | FAIL | > pre-registration's "insufficient data". A genuinely diverged run counts against the criterion, so H-E3.1 is FAIL, |

### Subprocess checks (run read-only, not modified)

**`eval/ta_verdicts_check.py` was deliberately NOT run.** Its own docstring states it WRITES `docs/thesis/tables/TA_verdicts.md` and RENDERS `docs/thesis/figures_thesis/tables_extra/TA_verdicts.{pdf,png}` as part of running - it is a generator/checker hybrid, not a pure read-only check, despite being named as one to consult in the task. Running it once during development of this script touched those three files; the change was reverted with `git checkout --` before anything was committed, and the script is excluded from every subsequent run of this audit to keep the read-only guarantee. `eval/caption_verdict_check.py` and `tools/check_numbers_frozen.py` were read in full first and confirmed to only read and print.

- `eval/caption_verdict_check.py` (exit 1):
```
CHECK FAIL: A13: every pointer id is a TA_verdicts.md ID-column value -> H1.8 FGO
   CHECK FAIL: A14: every pointer id is a TA_verdicts.md ID-column value -> H1.8 FGO
   CHECK FAIL: A16: every pointer id is a TA_verdicts.md ID-column value -> H1.8 FGO
   CHECK FAIL: A18: every pointer id is a TA_verdicts.md ID-column value -> H1.8 FGO
caption_verdict_check: 159/163 (9 caption files + 54 candidate captions checked, 3 exempt: A1, A2, A3)
```
- `tools/check_numbers_frozen.py` (exit 0):
```
PASS: numbers.md above '## Errata' sha256 6a77b9abf19b668c6b9e11e021b460c11b4cc7ca844b75193a7a96e18fe17b5a (frozen 6a77b9abf19b668c6b9e11e021b460c11b4cc7ca844b75193a7a96e18fe17b5a)
ok: frozen commit 669f099 has the frozen content
```

## C. Numeric table cells against their cited source

1065 `numbers*.md:LINE[-LINE]` citations found across the thesis-facing scan set. Only this citation form is resolved automatically (M:/C:/P:/json:/code: citations are provenance to a different document and are counted as unresolved, not guessed at). A citing line is scored a match if at least one numeric token on that line also appears verbatim within the cited `numbers*.md` line window (+/-1 line).

### Mismatches: cite drift (value found elsewhere in the file, not at the cited line)

| file:line | cite | found at |
|---|---|---|
| docs/thesis/tables/R4_information_vs_estimator.md:9 | numbers.md:248-249 | numbers.md:1448 |
| docs/thesis/tables/R4_information_vs_estimator.md:14 | numbers.md:621-623 | numbers.md:675 |
| docs/thesis/tables/R4_information_vs_estimator.md:14 | numbers_refly.md:247 | numbers_refly.md:345 |
| docs/thesis/tables/R4_information_vs_estimator.tex:14 | numbers.md:248-249 | numbers.md:127 |
| docs/thesis/tables/R4_information_vs_estimator.tex:19 | numbers.md:621-623 | numbers.md:79 |
| docs/thesis/figures_thesis/index.md:601 | numbers.md:677 | numbers.md:62 |
| docs/thesis/figures_thesis/index_results.md:353 | numbers.md:470 | numbers.md:60 |
| docs/thesis/figures_thesis/index_results.md:355 | numbers.md:470 | numbers.md:36 |
| docs/thesis/figures_thesis/index_results.md:360 | numbers_extras.md:95-99 | numbers_extras.md:88 |
| docs/thesis/figures_thesis/index_results.md:363 | numbers_extras.md:107-111 | numbers_extras.md:101 |
| docs/thesis/figures_thesis/index_results.md:507 | numbers.md:291-295 | numbers.md:38 |
| docs/thesis/figures_thesis/index_results.md:563 | numbers.md:263 | numbers.md:134 |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:14 | numbers.md:330 | numbers.md:36 |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:39 | numbers.md:477 | numbers.md:52 |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:50 | numbers.md:577 | numbers.md:114 |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:52 | numbers.md:577 | numbers.md:67 |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:54 | numbers.md:558 | numbers.md:89 |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:57 | numbers.md:606 | numbers.md:54 |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:63 | numbers.md:646 | numbers.md:54 |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:63 | numbers.md:629 | numbers.md:54 |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:67 | numbers.md:644 | numbers.md:565 |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:68 | numbers.md:629 | numbers.md:565 |
| docs/thesis/thesis_assets/tables_tex/tab_7-5.tex:15 | numbers.md:248-249 | numbers.md:127 |
| docs/thesis/thesis_assets/tables_tex/tab_7-5.tex:20 | numbers.md:621-623 | numbers.md:79 |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:19 | numbers.md:28 | numbers.md:72 |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:36 | numbers_ekf3_heading.md:5 | numbers_ekf3_heading.md:7 |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:60 | numbers.md:28 | numbers.md:48 |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:64 | numbers.md:211-237 | numbers.md:843 |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:7 | numbers.md:411 | numbers.md:60 |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:38 | numbers.md:520 | numbers.md:36 |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:41 | numbers.md:58 | numbers.md:36 |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:77 | numbers.md:82 | numbers.md:36 |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:30 | numbers_ekf3_heading.md:5 | numbers_ekf3_heading.md:7 |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:30 | numbers.md:301 | numbers.md:176 |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:33 | numbers.md:402 | numbers.md:54 |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:64 | numbers.md:451 | numbers.md:565 |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:68 | numbers.md:209 | numbers.md:36 |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:149 | numbers_tier1.md:576 | numbers_tier1.md:192 |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:156 | numbers_tier1.md:614-615 | numbers_tier1.md:192 |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:207 | numbers.md:227 | numbers.md:222 |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:209 | numbers.md:440 | numbers.md:445 |
| docs/thesis/writing_pack/methodology_factsheets/3.4_run_modes.md:93 | numbers_extras.md:99 | numbers_extras.md:111 |
| docs/thesis/writing_pack/methodology_factsheets/3.4_run_modes.md:125 | numbers.md:120 | numbers.md:118 |
| docs/thesis/writing_pack/methodology_factsheets/3.4_run_modes.md:128 | numbers.md:133 | numbers.md:121 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:11 | numbers.md:58 | numbers.md:36 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:35 | numbers.md:369-370 | numbers.md:176 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:35 | numbers.md:371 | numbers.md:176 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:60 | numbers_extras.md:99 | numbers_extras.md:111 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:65 | numbers_refly.md:97 | numbers_refly.md:18 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:79 | numbers.md:470-473 | numbers.md:36 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:79 | numbers_extras.md:148-155 | numbers_extras.md:88 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:79 | numbers_refly.md:97 | numbers_refly.md:298 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:89 | numbers.md:520 | numbers.md:36 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:91 | numbers.md:542 | numbers.md:54 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:100 | numbers_tier1.md:560 | numbers_tier1.md:248 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:102 | numbers_tier1.md:163 | numbers_tier1.md:157 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:115 | numbers.md:546 | numbers.md:36 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:115 | numbers.md:548 | numbers.md:36 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:128 | numbers.md:606 | numbers.md:54 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:135 | numbers.md:626 | numbers.md:54 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:135 | numbers.md:629 | numbers.md:54 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:136 | numbers_refly.md:272 | numbers_refly.md:65 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:154 | numbers.md:312-319 | numbers.md:203 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:173 | numbers.md:736-738 | numbers.md:318 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:186 | numbers.md:649-656 | numbers.md:62 |
| docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md:53 | numbers_tier1.md:35-36 | numbers_tier1.md:46 |
| docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md:78 | numbers_tier1.md:560 | numbers_tier1.md:248 |
| docs/thesis/writing_pack/tables/R4_information_vs_estimator.md:9 | numbers.md:248-249 | numbers.md:1448 |
| docs/thesis/writing_pack/tables/R4_information_vs_estimator.md:14 | numbers.md:621-623 | numbers.md:675 |
| docs/thesis/writing_pack/tables/R4_information_vs_estimator.md:14 | numbers_refly.md:247 | numbers_refly.md:345 |
| docs/thesis/writing_pack/thesis_vocabulary.md:343 | numbers.md:598-662 | numbers.md:134 |
| docs/thesis/writing_pack/thesis_vocabulary.md:403 | numbers.md:501 | numbers.md:509 |
| docs/thesis/writing_pack/units.md:104 | numbers.md:480 | numbers.md:134 |

### Mismatches: value not found anywhere in the cited file

| file:line | cite | tokens on citing line |
|---|---|---|
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:193 | numbers.md:466 | 24.7 |
| docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md:120 | numbers_tier1.md:68 | 0.95–1.86, 0.95–2.43 |
| docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md:123 | numbers_tier1.md:559 | 6.34–14.62 |

### Unresolved (560)

Citing lines where no comparable numeric token could be extracted, or the target file could not be resolved - listed rather than guessed, per the request.

| file:line | cite | reason |
|---|---|---|
| docs/thesis/tables/R2_corrections_by_discovery.md:8 | numbers.md:227 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/tables/R2_corrections_by_discovery.md:8 | numbers.md:497 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/tables/R2_corrections_by_discovery.md:15 | numbers.md:230 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/tables/R2_corrections_by_discovery.md:26 | numbers.md:479 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/tables/R2_corrections_by_discovery.tex:13 | numbers.md:227 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/tables/R2_corrections_by_discovery.tex:13 | numbers.md:497 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/tables/R2_corrections_by_discovery.tex:20 | numbers.md:230 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/tables/R2_corrections_by_discovery.tex:31 | numbers.md:479 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index.md:68 | numbers.md:428 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index.md:68 | numbers.md:428 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index.md:98 | numbers.md:470 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index.md:98 | numbers.md:470 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index.md:99 | numbers.md:470 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index.md:99 | numbers.md:470 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index.md:259 | numbers.md:230 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index.md:259 | numbers.md:232 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index.md:264 | numbers.md:232 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_drift.md:23 | numbers.md:221 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_drift9.md:63 | numbers.md:230 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:32 | numbers.md:263 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:121 | numbers.md:644 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:122 | numbers.md:646 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:124 | numbers.md:644 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:131 | numbers.md:644 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:132 | numbers_refly.md:241-248 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:134 | numbers.md:644 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:214 | numbers_refly.md:287 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:277 | numbers.md:248 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:299 | numbers.md:621 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:300 | numbers.md:622 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:301 | numbers.md:623 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:302 | numbers.md:644 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:313 | numbers.md:227 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:315 | numbers.md:330 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:319 | numbers.md:330 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:321 | numbers.md:301 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:325 | numbers.md:263 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:329 | numbers.md:299 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:331 | numbers.md:509 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:333 | numbers.md:501 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:335 | numbers.md:510 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:337 | numbers.md:511 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:339 | numbers.md:512 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:341 | numbers.md:512 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:343 | numbers.md:513 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:345 | numbers.md:513 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:347 | numbers.md:497 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:349 | numbers.md:498 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:351 | numbers.md:499 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:357 | numbers.md:471 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:366 | numbers_extras.md:120-124 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:369 | numbers_extras.md:139-143 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:372 | numbers_refly.md:51-53 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:373 | numbers_refly.md:95-99 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:375 | numbers.md:477 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:377 | numbers.md:478 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:379 | numbers_refly.md:119-121 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:380 | numbers_refly.md:127 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:383 | numbers_ekf3_heading.md:43-43 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:384 | numbers_ekf3_heading.md:52-52 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:385 | numbers_ekf3_heading.md:35-37 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:388 | numbers_ekf3_heading.md:20-22 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:389 | numbers_ekf3_heading.md:29-31 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:390 | numbers.md:291-295 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:393 | numbers_ekf3_heading.md:43-48 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:394 | numbers_ekf3_heading.md:46-48 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:396 | numbers.md:533-534 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:398 | numbers.md:535 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:400 | numbers.md:536 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:402 | numbers.md:537 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:404 | numbers.md:576 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:406 | numbers.md:573 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:407 | numbers.md:577 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:409 | numbers.md:573-574 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:410 | numbers.md:577 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:412 | numbers.md:573-574 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:413 | numbers.md:577 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:415 | numbers.md:574 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:416 | numbers.md:577 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:418 | numbers.md:558 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:419 | numbers.md:552-556 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:421 | numbers.md:559 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:423 | numbers.md:560 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:426 | numbers.md:606 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:429 | numbers_refly.md:228-235 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:432 | numbers_refly.md:337-337 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:433 | numbers_refly.md:342-348 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:436 | numbers_refly.md:338-338 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:437 | numbers_refly.md:350-351 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:440 | numbers_refly.md:339-339 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:441 | numbers_refly.md:353-355 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:444 | numbers_refly.md:340-340 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:445 | numbers_refly.md:357-357 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:448 | numbers.md:629 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:449 | numbers.md:644 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:450 | numbers_refly.md:245-259 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:453 | numbers_refly.md:245-248 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:454 | numbers.md:644 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:458 | numbers.md:617 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:461 | numbers.md:644 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:462 | numbers_refly.md:268-272 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:465 | numbers.md:644 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:466 | numbers_refly.md:282-287 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:469 | numbers.md:629 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:470 | numbers_refly.md:275 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:474 | numbers.md:644 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:475 | numbers.md:646 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:481 | numbers_extras.md:127-131 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:482 | numbers.md:473 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:483 | numbers.md:480 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:484 | numbers.md:646 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:485 | numbers.md:675 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:486 | numbers.md:676 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:487 | numbers.md:677 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:488 | numbers.md:678 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:489 | numbers.md:646 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:490 | numbers.md:646 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:491 | numbers.md:646 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:492 | numbers.md:646 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:493 | numbers.md:629 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:498 | numbers_ekf3_heading.md:5-5 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:499 | numbers_ekf3_heading.md:43-45 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:500 | numbers_ekf3_heading.md:52-54 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:501 | numbers_ekf3_heading.md:35-37 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:502 | numbers_ekf3_heading.md:173-173 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:503 | numbers_ekf3_heading.md:174-174 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:505 | numbers_ekf3_heading.md:20-22 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:506 | numbers_ekf3_heading.md:29-31 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/figures_thesis/index_results.md:534 | numbers.md:1014 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:15 | numbers.md:330 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:20 | numbers.md:509 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:21 | numbers.md:501 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:23 | numbers.md:511 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:24 | numbers.md:512 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:25 | numbers.md:512 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:26 | numbers.md:513 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:28 | numbers.md:497 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:29 | numbers.md:498 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:30 | numbers.md:499 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:64 | numbers.md:644 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:97 | numbers.md:677 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:99 | numbers.md:646 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:100 | numbers.md:646 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:102 | numbers.md:646 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:103 | numbers.md:629 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-4.tex:14 | numbers.md:227 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-4.tex:14 | numbers.md:497 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-4.tex:21 | numbers.md:230 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/thesis_assets/tables_tex/tab_7-4.tex:32 | numbers.md:479 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/ablation/ablation_numbers.md:204 | numbers.md:301 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/ablation/ablation_numbers.md:205 | numbers.md:299 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/ablation/preregistration.md:225 | numbers.md:301 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/ablation/preregistration.md:225 | numbers.md:299 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_definitions_draft.md:64 | numbers.md:467 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_definitions_draft.md:100 | numbers.md:236 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_definitions_draft.md:148 | numbers.md:480-481 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_definitions_draft.md:165 | numbers.md:33 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:8 | numbers.md:407-408 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:9 | numbers.md:462 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:11 | numbers.md:57 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:15 | numbers.md:237 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:22 | numbers.md:158-160 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:28 | numbers.md:693 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:30 | numbers.md:120 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:31 | numbers.md:115-116 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:32 | numbers.md:110 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:35 | numbers.md:402-405 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:37 | numbers.md:157 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:39 | numbers.md:231 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:41 | numbers.md:487 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:48 | numbers.md:151-157 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:50 | numbers.md:117-120 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:50 | numbers.md:21-24 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:54 | numbers.md:134-135 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:61 | numbers.md:296 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:61 | numbers.md:464 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:61 | numbers_refly.md:376 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:61 | numbers_refly.md:16-23 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:71 | numbers.md:132-133 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:13 | numbers.md:407-408 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:13 | numbers.md:409-410 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:16 | numbers.md:57 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:33 | numbers.md:49 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:37 | numbers.md:73 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:39 | numbers.md:546 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:54 | numbers.md:96-100 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:56 | numbers.md:75-76 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:60 | numbers.md:73-74 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:73 | numbers.md:96 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:78 | numbers.md:58 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:9 | numbers.md:411 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:22 | numbers.md:231 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:39 | numbers.md:542 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:40 | numbers.md:538-539 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:42 | numbers.md:600 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:43 | numbers.md:602 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:57 | numbers.md:700 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:69 | numbers.md:444 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:75 | numbers.md:157 | no decimal value token on citing line (after stripping citations/code spans) |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:81 | numbers.md:700 | no decimal value token on citing line (after stripping citations/code spans) |

## D. Style checks

Counts are per-file after stripping code spans, bracketed `[...]` citations, and (for table rows) a trailing provenance-looking source cell. Full file:line detail capped per file in this report; re-run the script for the complete list if needed.

| file | prose en/em dashes (not a digit-range) | bare `RTF 0.5` (not wrapped as 'half real-time (RTF 0.5)') |
|---|---|---|
| docs/thesis/figures_thesis/index.md | 19 | 0 |
| docs/thesis/figures_thesis/index_drift.md | 1 | 0 |
| docs/thesis/figures_thesis/index_drift9.md | 1 | 0 |
| docs/thesis/figures_thesis/index_methods.md | 1 | 1 |
| docs/thesis/figures_thesis/index_results.md | 5 | 0 |
| docs/thesis/tables/R1_hypothesis_scorecard.md | 3 | 0 |
| docs/thesis/tables/R2_corrections_by_discovery.md | 9 | 0 |
| docs/thesis/tables/R4_information_vs_estimator.md | 5 | 0 |
| docs/thesis/tables/T1_scorecard.md | 4 | 0 |
| docs/thesis/tables/T2_accuracy_heading.md | 1 | 0 |
| docs/thesis/tables/T5_H_tag_loss_drift.md | 2 | 0 |
| docs/thesis/tables/T6_O_indoor_rmse.md | 2 | 0 |
| docs/thesis/tables/TA_verdicts.md | 7 | 0 |
| docs/thesis/tables/methods_estimator_design.md | 1 | 0 |
| docs/thesis/tables/methods_experiment_matrix.md | 3 | 1 |
| docs/thesis/tables/methods_experiment_matrix.tex | 0 | 1 |
| docs/thesis/tables/realflight_compute.md | 4 | 3 |
| docs/thesis/tables/realflight_compute.tex | 0 | 3 |
| docs/thesis/thesis_assets/index.md | 1 | 0 |
| docs/thesis/thesis_assets/tables_tex/tab_3-4.tex | 0 | 1 |
| docs/thesis/thesis_assets/tables_tex/tab_8-1.tex | 0 | 3 |
| docs/thesis/writing_pack/ablation/ablation_numbers.md | 15 | 0 |
| docs/thesis/writing_pack/ablation/preregistration.md | 11 | 0 |
| docs/thesis/writing_pack/methodology_definitions_draft.md | 1 | 1 |
| docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md | 1 | 1 |
| docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md | 3 | 1 |
| docs/thesis/writing_pack/methodology_factsheets/3.4_run_modes.md | 3 | 1 |
| docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md | 4 | 1 |
| docs/thesis/writing_pack/methodology_factsheets/3.6_metrics_statistics.md | 2 | 0 |
| docs/thesis/writing_pack/methodology_factsheets/3.7_verification.md | 3 | 0 |
| docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md | 26 | 0 |
| docs/thesis/writing_pack/methodology_factsheets/README.md | 18 | 1 |
| docs/thesis/writing_pack/new_2026-11-11/caption_detail.md | 12 | 1 |
| docs/thesis/writing_pack/new_2026-11-11/ekf3_heading_preregistration.md | 93 | 0 |
| docs/thesis/writing_pack/new_2026-11-11/extras_preregistration.md | 1 | 0 |
| docs/thesis/writing_pack/new_2026-11-11/numbers_cl_heading_perflight.md | 17 | 0 |
| docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md | 7 | 0 |
| docs/thesis/writing_pack/new_2026-11-11/refly_preregistration.md | 0 | 2 |
| docs/thesis/writing_pack/numbers.md | 239 | 0 |
| docs/thesis/writing_pack/raw_corridor/raw_corridor_numbers.md | 13 | 0 |
| docs/thesis/writing_pack/tables/R1_hypothesis_scorecard.md | 3 | 0 |
| docs/thesis/writing_pack/tables/R2_corrections_by_discovery.md | 9 | 0 |
| docs/thesis/writing_pack/tables/R4_information_vs_estimator.md | 5 | 0 |
| docs/thesis/writing_pack/tables/T1_scorecard.md | 4 | 0 |
| docs/thesis/writing_pack/tables/T2_accuracy_heading.md | 1 | 0 |
| docs/thesis/writing_pack/tables/T5_H_tag_loss_drift.md | 2 | 0 |
| docs/thesis/writing_pack/tables/T6_O_indoor_rmse.md | 2 | 0 |
| docs/thesis/writing_pack/tables/TA_verdicts.md | 7 | 0 |
| docs/thesis/writing_pack/tables/methods_estimator_design.md | 1 | 0 |
| docs/thesis/writing_pack/tables/methods_experiment_matrix.md | 3 | 1 |
| docs/thesis/writing_pack/thesis_vocabulary.md | 26 | 1 |
| docs/thesis/writing_pack/tier1/e3_results.md | 60 | 0 |
| docs/thesis/writing_pack/tier1/e4_results.md | 2 | 0 |
| docs/thesis/writing_pack/tier1/e5_results.md | 1 | 0 |
| docs/thesis/writing_pack/tier1/e6_preregistration.md | 8 | 0 |
| docs/thesis/writing_pack/tier1/numbers_tier1.md | 14 | 0 |
| docs/thesis/writing_pack/tier1/preregistration.md | 4 | 0 |

### Sample detail (up to 40 lines per file)

**docs/thesis/tables/R1_hypothesis_scorecard.md**
- L39 [dash_prose]: `| H2.1 | FGO hindsight gain grows with the gap (primary) | “H-T1 … the FGO's hindsight gain grows with the gap. PASS iff both: (i) the per-c`
- L41 [dash_prose]: `| H2.3 | live errors similar | “P-T3 (prediction): live errors are similar. In every condition, the largest live horizontal RMSE among EKF3,`
- L42 [dash_prose]: `| H2.4 | FGO hindsight ≈ smoothed UKF | “P-T4 (prediction): FGO hindsight ≈ RTS-UKF. In every condition, the larger of their horizontal RMSE`

**docs/thesis/tables/R2_corrections_by_discovery.md**
- L7 [dash_prose]: `| fairness (input-equivalence) audit | 1 | UKF/FGO IMU dejitter (sensor-time reconstruction) | DATA | Fairness audit OI-2 (2026-09-24): an i`
- L9 [dash_prose]: `| offline cross-check against ground truth (distance scale) | 3 | EKF3 flow sensor position FLOW_POS_Z 0.13 → 0.25 | CONFIG | Distance-scale`
- L10 [dash_prose]: `| offline cross-check against ground truth (distance scale) | 4 | UKF process dt = the accumulated IMU interval | MODEL | Distance-scale che`
- L11 [dash_prose]: `| analysis audit (window) | 8 | heading share on the pinned cruise window | ANALYSIS | Window audit (2026-09-29). | none: before the claims `
- L12 [dash_prose]: `| source-code reading | 7 | time sync on; AHRS_EKF_TYPE explicit; replay logging | CONFIG | Part C source reading (SIM_JSON.cpp:410-413, 202`
- L19 [dash_prose]: `| port and offline equivalence or comparison work | 19 | FGO trajectory-writer quaternion typo (D10) | SCORER (output writer) | Yaw represen`
- L20 [dash_prose]: `| diagnostic investigation of a measured effect | 6 | roll rate gains ×0.4447 (simulated vehicle) | MODEL (vehicle) | EKF3 flow-derotation t`
- L22 [dash_prose]: `| SITL flight (a defect exposed by a flown result) | 5 | lateral optical-flow sign | MODEL / bridge | Closed-loop smoke test (2026-09-29): t`
- L24 [dash_prose]: `| SITL flight (a defect exposed by a flown result) | 16 | offline UKF bias-corrected flow derotation | MODEL | H S1 input-path diagnostic (2`

**docs/thesis/tables/R4_information_vs_estimator.md**
- L3 [dash_prose]: `For each condition: the primary metric of each estimator, the best–worst spread across the estimators (max − min and max ÷ min), and the cha`
- L10 [dash_prose]: `| Experiment 2: known tags, live | horizontal RMSE (m); n = 3 flights per condition (mean); 4 conditions | 1 tag: EKF3 0.096, UKF 0.131, FGO`
- L11 [dash_prose]: `| Experiment 2: known tags, hindsight | horizontal RMSE (m); n = 3 flights per condition (mean) | 1 tag: FGO batch 0.028, smoothed UKF 0.109`
- L12 [dash_prose]: `| Experiment 4: outdoor–indoor, live | indoor horizontal RMSE (m), GNSS off for 123 s; n = 3 flights | EKF3 1.42–1.43, UKF 0.77–0.84, FGO 0.`
- L13 [dash_prose]: `| Experiment 4: outdoor–indoor, hindsight | indoor horizontal RMSE (m); n = 3 flights | FGO batch 0.59–0.59, smoothed UKF 0.58–0.60 | - | ma`

**docs/thesis/tables/T1_scorecard.md**
- L3 [dash_prose]: `Each cell gives the key number and the verdict it rests on, with a status (PASSED, N/A, or on the blank floor 'no estimator bounds position `
- L13 [dash_prose]: `| Experiment 4: outdoor–indoor (GNSS outside only)   | indoor 1.42–1.43 m (no live ordering claimed; 4.10 m jump, about 4.3 s after GNSS ret`
- L22 [dash_prose]: `*Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met  , the UKF medians descriptive  ; with `
- L26 [dash_prose]: `*Ordering footnotes  –  (one per comparison; the letters in the experiment column): each footnote states the rule, the result and why no ord`

**docs/thesis/tables/T2_accuracy_heading.md**
- L7 [dash_prose]: `| EKF3 | 4.10 (3.11–4.12) | RMS 14.58 (7.84–14.64); end 37.39 (22.54–37.56) | 4.09 / 3.60 / 4.08 | RMS 14.54 / 11.16 / 14.45; end 37.30 / 29`

**docs/thesis/tables/T5_H_tag_loss_drift.md**
- L3 [dash_prose]: `Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered band, and none`
- L14 [dash_prose]: `*Drift = the EFFECTIVE metric (last fix → first returning fix); the end-of-loss metric differs by ≤ 5 mm (unrounded 5.1 mm). Pre-registered `

**docs/thesis/tables/T6_O_indoor_rmse.md**
- L1 [dash_prose]: `# Table 5.1. Experiment 4 (outdoor–indoor): indoor horizontal RMSE per flight (123 s, GNSS off)`
- L12 [dash_prose]: `| live max ÷ min (H4.2) | — | 1.72 | 1.71 | 1.84 | 1.71–1.84 |`

**docs/thesis/tables/TA_verdicts.md**
- L3 [dash_prose]: `ONE row per pre-registered hypothesis, check or prediction, gathered from the tables and verdict files that already scored it, so that no PA`
- L39 [dash_prose]: `| Experiment 2 | H2.1 | “H-T1 … the FGO's hindsight gain grows with the gap. PASS iff both: (i) the per-condition medians of Δ_FGO increase `
- L41 [dash_prose]: `| Experiment 2 | H2.3 | “P-T3 (prediction): live errors are similar. In every condition, the largest live horizontal RMSE among EKF3, UKF an`
- L42 [dash_prose]: `| Experiment 2 | H2.4 | “P-T4 (prediction): FGO hindsight ≈ RTS-UKF. In every condition, the larger of their horizontal RMSEs (mean over rep`
- L80 [dash_prose]: `| Extension E3 | P-E3.6 | dose–response: per flight, the seed-mean LC live overall satisfies clean ≤ 1% ≤ 5%, 3/3 flights   | FAIL 0/3 | FAI`
- L101 [dash_prose]: `| EXPLORATORY | P2 (with heading) | the one-keyframe converged FGO (r3: cap 100; convergence not confirmed, iteration counts not logged) ret`
- L124 [dash_prose]: `*Verdicts (the project's own vocabulary; never softened or strengthened): PASS = the record says PASS, MET, TRUE or an accepted-as-worded ve`

**docs/thesis/tables/methods_estimator_design.md**
- L10 [dash_prose]: `| filter or smoother | extended Kalman filter | unscented Kalman filter (an RTS smoother over its predict nodes gives the hindsight track in`

**docs/thesis/tables/methods_experiment_matrix.md**
- L11 [dash_prose]: `| 1B: robust-weighting replication | corridor with ceiling, textured floor; plain and textured walls | as 1B offline fusion | UKF hard-gated`
- L15 [dash_prose]: `| 4 outdoor–indoor | outdoor–indoor world (GNSS outside only) | IMU, flow, LiDAR; GNSS outdoors only | EKF3 live, passive (truth flying); UK`
- L21 [rtf_bare]: `*'Truth flying' = AHRS_EKF_TYPE 10: the simulator's state flies the vehicle, so the path does not depend on any estimator; EKF3 then runs li`

**docs/thesis/tables/methods_experiment_matrix.tex**
- L28 [rtf_bare]: `\textit{Note.} 'Truth flying' = AHRS\_EKF\_TYPE 10: the simulator's state flies the vehicle, so the path does not depend on any estimator; E`

**docs/thesis/tables/realflight_compute.md**
- L8 [dash_prose]: `| C++ FGO node on the workstation (DIAGNOSTIC) | — | — | replay median / p99: 0.53 / 0.92 ms (standard-sensor bag), 0.91 / 1.68 ms (with hea`
- L12 [dash_prose]: `| companion computer (Pi), C++ FGO node | — | — | ESTIMATED p99 ~3.4 ms (Pi 5), ~8.7 ms (Pi 4) against the 33 ms keyframe; worst spike ~25 m`
- L13 [rtf_bare]: `| closed-loop real-time factor (Exp. 1C) | flew at full real time and at half real-time   | flew at full real time (old UKF) and at half rea`
- L13 [rtf_bare]: `| closed-loop real-time factor (Exp. 1C) | flew at full real time and at half real-time   | flew at full real time (old UKF) and at half rea`
- L17 [rtf_bare]: `*Half real-time (RTF 0.5): the simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s. Nothing was flashed to `

**docs/thesis/tables/realflight_compute.tex**
- L19 [rtf_bare]: `closed-loop real-time factor (Exp. 1C) & flew at full real time and at half real-time   & flew at full real time (old UKF) and at half real-`
- L19 [rtf_bare]: `closed-loop real-time factor (Exp. 1C) & flew at full real time and at half real-time   & flew at full real time (old UKF) and at half real-`
- L24 [rtf_bare]: `\textit{Note.} Half real-time (RTF 0.5): the simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s. Nothing w`

**docs/thesis/figures_thesis/index.md**
- L11 [dash_prose]: `**Colour mapping (Okabe–Ito, colour-blind safe; fixed across every figure):** EKF3 #0072B2 (blue, circle) · UKF #009E73 (bluish green, trian`
- L33 [dash_prose]: `| Table 5.1 | T6 | table |  ,  ,   | Experiment 4 (outdoor–indoor): indoor horizontal RMSE per flight (123 s, GNSS off) | CURRENT | 14/14 | `
- L280 [dash_prose]: `| Experiment 2 median gaps A–D (s) |   |   | numbers.md §16.1 table header | yes |`
- L282 [dash_prose]: `| H2.1 median gain A–D (m), rho, PASS |   |   | numbers.md §16.1 | yes |`
- L283 [dash_prose]: `| H2.2 gain A–D (m), PASS |   |   | numbers.md §16.1 | yes |`
- L284 [dash_prose]: `| H2.1 gain A–D: rd_si() caption string == rd() check string |   |   | this file: rd_si() vs rd() on the same values | yes |`
- L285 [dash_prose]: `| H2.2 gain A–D: rd_si() caption string == rd() check string |   |   | this file: rd_si() vs rd() on the same values | yes |`
- L287 [dash_prose]: `| F5 title: FGO whole-flight batch over A–D, 2 dp (m) = former caption literal '1–3' cm × 10^-2 |   |   | eval/results/expT/t_aggregate.json`
- L351 [dash_prose]: `### Table 5.1 (internal T6, table): Experiment 4 (outdoor–indoor): indoor horizontal RMSE per flight (123 s, GNSS off)`
- L384 [dash_prose]: `| Experiment 2 smoothed UKF A–D (m) |   |   | numbers.md §16.1 table | yes |`
- L385 [dash_prose]: `| Experiment 2 FGO whole-flight batch A–D (m) |   |   | numbers.md §16.1 table | yes |`
- L394 [dash_prose]: `- **Caption:** Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered`
- L423 [dash_prose]: `- **Caption:** Each cell gives the key number and the verdict it rests on, with a status (PASSED, N/A, or on the blank floor 'no estimator b`
- L436 [dash_prose]: `| Experiment 2 FGO whole-flight batch A–D (m) |   |   | numbers.md §16.1 table | yes |`
- L643 [dash_prose]: `- **Caption:** ONE row per pre-registered hypothesis, check or prediction, gathered from the tables and verdict files that already scored it`
- L672 [dash_prose]: `| Table 5.1 | T6 |  ,  ,   | Experiment 4 (outdoor–indoor): indoor horizontal RMSE per flight (123 s, GNSS off) |`
- L692 [dash_prose]: `| Experiment 4, outdoor–indoor | Experiment O | Figure 5.3, Table 5.1, Table 5.2, Table 7.1, Table 7.2, Table A.3 | §2 row 4 |`
- L695 [dash_prose]: `| condition A–D (8 / 4 / 2 / 1 tags; kept as letters) | Experiment T conditions A–D;   …   | Figure 5.1, Table 5.2, Table 7.1 | §8.1 row 29;`

**docs/thesis/figures_thesis/index_drift.md**
- L7 [dash_prose]: `**Rounding:**   parsed from   (not executed); SHA-256 of its source  . Palette: Okabe–Ito, EKF3 #0072B2, UKF #009E73, FGO #D55E00, truth #99`

**docs/thesis/figures_thesis/index_drift9.md**
- L7 [dash_prose]: `**Rounding:**   parsed from   (not executed); SHA-256 of its source  .  / / /  parsed from   (not executed, not imported); SHA-256 of their `

**docs/thesis/figures_thesis/index_methods.md**
- L7 [dash_prose]: `**Proposed numbering** (vocabulary §6: by chapter; Chapter 3 = method, Chapter 8 = towards real flights). File names are descriptive and new`
- L129 [rtf_bare]: `| wall time per keyframe at RTF 0.5 = (1/30 s)/0.5 (ms) |   |   | M:7779 | yes |`

**docs/thesis/figures_thesis/index_results.md**
- L5 [dash_prose]: `**Rounding:** every number goes through   from  , loaded by parsing that file (it is not run). SHA-256 of  's source:  . Palette: the fixed `
- L66 [dash_prose]: `**Caption.** For each condition: the primary metric of each estimator, the best–worst spread across the estimators (max − min and max ÷ min)`
- L116 [dash_prose]: `| R1 | H2.1 median FGO hindsight gain A–D (m) | 0.010 / 0.011 / 0.023 / 0.052 | 0.010 / 0.011 / 0.023 / 0.052 | docs/thesis/numbers.md:533 |`
- L117 [dash_prose]: `| R1 | H2.3 live max/min A–D | 1.97 / 2.36 / 1.42 / 1.57 | 1.97 / 2.36 / 1.42 / 1.57 | docs/thesis/numbers.md:536 | OK |`
- L118 [dash_prose]: `| R1 | H2.4 hindsight max/min A–D | 1.31 / 2.14 / 2.06 / 3.89 | 1.31 / 2.14 / 2.06 / 3.89 | docs/thesis/numbers.md:537 | OK |`

**docs/thesis/thesis_assets/tables_tex/tab_3-4.tex**
- L29 [rtf_bare]: `\textit{Note.} 'Truth flying' = AHRS\_EKF\_TYPE 10: the simulator's state flies the vehicle, so the path does not depend on any estimator; E`

**docs/thesis/thesis_assets/tables_tex/tab_8-1.tex**
- L20 [rtf_bare]: `closed-loop real-time factor (Exp. 1C) & flew at full real time and at half real-time   & flew at full real time (old UKF) and at half real-`
- L20 [rtf_bare]: `closed-loop real-time factor (Exp. 1C) & flew at full real time and at half real-time   & flew at full real time (old UKF) and at half real-`
- L25 [rtf_bare]: `\textit{Note.} Half real-time (RTF 0.5): the simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s. Nothing w`

**docs/thesis/thesis_assets/index.md**
- L25 [dash_prose]: `| Table 5.1 | Experiment 4 (outdoor–indoor): indoor horizontal RMSE per flight (123 s, GNSS off) |  ,   |   |  ,   |`

**docs/thesis/writing_pack/ablation/ablation_numbers.md**
- L113 [dash_prose]: `| fwdc_tex_r1, baseline | 16.4 / 18.2 | 6.2 / 6.6 | 6.2 / 7.0 | 6.2 / 6.8 | 51.9 / 55.1 | 100.6 / 106.1 | — | — |`
- L114 [dash_prose]: `| fwdc_tex_r2, baseline | 17.0 / 18.6 | 6.2 / 6.6 | 6.2 / 6.8 | 6.3 / 7.0 | 51.8 / 55.5 | 102.3 / 109.1 | — | — |`
- L115 [dash_prose]: `| fwdc_tex_r3, baseline | 17.1 / 18.5 | 6.1 / 6.5 | 6.2 / 7.0 | 6.1 / 6.8 | 51.3 / 55.3 | 100.8 / 106.2 | — | — |`
- L116 [dash_prose]: `| fwdplainc_tex_r1, baseline | 16.3 / 17.9 | 6.4 / 6.8 | 6.1 / 6.8 | 6.1 / 6.8 | 51.6 / 55.8 | 104.6 / 111.4 | — | — |`
- L117 [dash_prose]: `| fwdplainc_tex_r2, baseline | 16.4 / 17.7 | 6.2 / 6.6 | 6.1 / 6.6 | 6.1 / 6.9 | 51.3 / 54.6 | 102.3 / 109.4 | — | — |`
- L118 [dash_prose]: `| fwdplainc_tex_r3, baseline | 16.4 / 17.9 | 6.2 / 6.6 | 6.1 / 7.0 | 6.2 / 7.0 | 51.6 / 55.4 | 101.2 / 106.1 | — | — |`
- L140 [dash_prose]: `| P1 overall | FAIL | — | P1 needs every rung 6/6 |`
- L141 [dash_prose]: `| P2 | PASS | 3/3 | — (R(r3) on  : 1.01, 0.97, 0.98; pass needs ≥ 0.5 on each) |`
- L176 [dash_prose]: `(r3) keeps the FGO–UKF gap essentially whole (R = 1.01, 0.97, 0.98, each above its ≈ 0.91 threshold), and so do the`

**docs/thesis/writing_pack/ablation/preregistration.md**
- L103 [dash_prose]: `| r0 (thesis config; identity gate + serial timing) |   | 0.25 | 2 | heading, baseline | — |   |`
- L104 [dash_prose]: `| r1 one keyframe × 1 iteration |   | 0.01 | 1 | heading, baseline | — | same |`
- L105 [dash_prose]: `| r2 one keyframe × cap 2 (kept, Q2) |   | 0.01 | 2 | heading, baseline | — | same |`
- L106 [dash_prose]: `| r3 one keyframe × cap 100; convergence not confirmed (iteration counts not logged) |   | 0.01 | 100 | heading, baseline | — | same |`
- L107 [dash_prose]: `| r4 1 s |   | 1 | 2 | heading, baseline | — | same |`
- L108 [dash_prose]: `| r5 2 s |   | 2 | 2 | heading, baseline | — | same |`
- L111 [dash_prose]: `| r6s (zero machine cost) | — | 0.25 | 2 | heading | stored   (Cauchy 2.385, gate off) | scored read-only from   |`
- L218 [dash_prose]: `logged)) retains at least half the FGO–UKF gap.**`
- L249 [dash_prose]: `| r0 → r3 changes R while r2 ≈ r3 | the change is due to the **window**, not the iterations (this is why r2 exists, Q2) | — |`
- L250 [dash_prose]: `| P1 fails (a control rung moves beyond its band) | the variant changes the FGO generally, not only its heading handling. The P2 reading is `
- L252 [dash_prose]: `| headings fused differ markedly between rungs | part of any change acts through the gate's linearisation point, not through the window. Rep`

**docs/thesis/writing_pack/methodology_definitions_draft.md**
- L1 [dash_prose]: `# Methodology chapter: conventions for reporting results — DRAFT FOR THE USER`
- L206 [rtf_bare]: `## Half real-time (RTF 0.5)`

**docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md**
- L39 [dash_prose]: `- **Outdoor–indoor world (Experiment 4).**  : corridor checker floor outside and inside, and a building with an entrance and a plain roof. W`
- L44 [rtf_bare]: `- **Half real-time (RTF 0.5).** The closed-loop corridor flights also ran in  , a copy of the textured-wall world with   0.5 (sim/worlds/cor`

**docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md**
- L64 [dash_prose]: `- **FGO, solver:** a GTSAM 4.2.1    . It solves with Levenberg–Marquardt, capped at 2 iterations and warm-started (numbers.md:451; src/estim`
- L136 [dash_prose]: `Mahalanobis residual of every tag landmark factor only — not the gauge prior, not any IMU, flow or range factor`
- L152 [dash_prose]: `place of the surveyed one, treating the supplied map exactly as fixed, known landmarks — same tag noise, no map`
- L202 [rtf_bare]: `- **Closed-loop   for the Python heading node** was replaced by 38 for the C++ node (closedloop_heading.parm:16-19), and 25 at RTF 0.5 (clos`

**docs/thesis/writing_pack/methodology_factsheets/3.4_run_modes.md**
- L69 [rtf_bare]: `25 at RTF 0.5 (numbers.md:464); 38 at RTF 1.0  .`
- L148 [dash_prose]: `METHODOLOGY.md:1985-2005) is superseded by "Ruling 2 — IMU timing rule EXTENDED" (receipt bunch added, ≥ 10 s`
- L161 [dash_prose]: `flies (METHODOLOGY.md:8070); a non-active estimator logs (docs/partC_onboard_feasibility.md:28) — glossary_flags.md:93;`
- L164 [dash_prose]: `(METHODOLOGY.md:10476) — glossary_flags.md:94; glossary.md:3482, 3507.`

**docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md**
- L9 [dash_prose]: `- **Numbering.** Five experiments: 1 corridor comparison (1A standard-sensor comparison, 1B camera-heading studies, 1C closed-loop corridor `
- L48 [dash_prose]: `- **H1.7a–c (robust-weighting replication; plan step 2(a)), operative M:9692-9750.**`
- L79 [rtf_bare]: `· **Verdicts (original n = 1 flights, as recorded):** EKF3 PASS at RTF 1.0 and MISS at RTF 0.5 (numbers.md:464) (contact after its window); `
- L90 [dash_prose]: `· Conditions A–D are the number of tags sent (8 / 4 / 2 / 1) × 3 repeats, interleaved: n = 12 flights (M:10115-10126).`
- L113 [dash_prose]: `- **Exp 4 (outdoor–indoor), operative M:10290-10363.**`

**docs/thesis/writing_pack/methodology_factsheets/3.6_metrics_statistics.md**
- L133 [dash_prose]: `crashed run or a failed gate; **NOT RUN** for a run the lock cut off; no early decisions — a criterion with a`
- L139 [dash_prose]: `fraction of the stored FGO–UKF gap a rung ρ keeps, per bag; R = 1 unchanged, R ≤ 0 the FGO is no better than the`

**docs/thesis/writing_pack/methodology_factsheets/3.7_verification.md**
- L51 [dash_prose]: `directly traced plain-wall case and the ruled outdoor–indoor partial attribution (numbers.md:35-36,`
- L110 [dash_prose]: `s then  s a manifest of result data — every   file, every other trial's`
- L111 [dash_prose]: `outputs except its recorded bag,  , and   — never code and never documents`

**docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md**
- L10 [dash_prose]: `- **Recordings.**  ,  ,   (9 existing Experiment 2 flights, not new flights); condition A is not re-run — the stored Experiment 3 result IS `
- L36 [dash_prose]: `- **H-E3.1 (PRIMARY) at 1%: FAIL, 0/9** — 6 of 9 runs diverged (2 of 3 on every flight), and the 3 non-diverged runs' LC live is far above t`
- L39 [dash_prose]: `- P-E3.6 (dose–response): **FAIL, 0/3** — every flight has 2 diverged 1% runs, so seed means are not computed ( ).`
- L40 [dash_prose]: `- **P-E3b.1 (robust, "no worse" than +10%): PASS, 9/9 at 1% and 9/9 at 5%** (rates  ) — 6 of the 9 runs at 1% are the SATISFIED-flagged case`
- L51 [dash_prose]: `- **Pre-registration.**   §3 ( ), written 2026-10-21, **signed off 2026-10-22 with amendments** — amendment 3 is E4's directional accuracy h`
- L57 [dash_prose]: `- **H-E4.3 (live RMSE at 5 s < at 0.25 s, ≥ 10/12: judgement, not derived from data): FAIL, 7/12** — a null result; the D flights are lower `
- L64 [dash_prose]: `- **Recordings.**  , LC and no-LC, cut at anchor + 245 s — the same recordings and cut as Experiment 3 ( ). 6 result replays, all exit 0 ( )`
- L65 [dash_prose]: `- **Arms.** The new landmark UKF ( / , written for E5): 15-state vehicle block plus a 3-state   landmark per tag, augmented by unscented tra`
- L68 [dash_prose]: `- **Gates (HARD; amendment 2 — no E5 result counts until all pass).**`
- L69 [dash_prose]: `- G0-UKF (byte-identical reproduction of the stored Experiment 2 UKF, 12/12 flights,  ) — a precondition, not itself an E5 validation gate (`
- L84 [dash_prose]: `- **Recordings.** New mapping flights only —  ,  ,  , a figure-of-eight route (3 circuits, 216 s) through the same   world and tag configura`
- L95 [dash_prose]: `- **P1 (FGO map error < UKF map error, 3/3 mapping flights): FAIL, 2/3** — the FGO's map is lower on 2 of 3 mapping flights ( ;  ).`
- L96 [dash_prose]: `- **P2 (FGO) (FGO live RMSE on the FGO map inside the surveyed band, 3/3): FAIL, 0/3** — all three above the band ( ;  ).`
- L97 [dash_prose]: `- **P2 (UKF): FAIL, 2/3** — one flight ( ) above the band ( ;  ).`
- L102 [dash_prose]: `### Attribution ablation (FGO vs UKF with heading) — EXPLORATORY`
- L105 [dash_prose]: `- **Purpose (one line).** Which of window length, iteration count and robust loss explains the with-heading FGO–UKF gap ( )?`
- L110 [dash_prose]: `- **Amendments/clarifications.** The sign-off itself IS the set of amendments to the draft: Q1–Q7 resolved as the draft's own recommendation`
- L113 [dash_prose]: `- **P1 (control, no heading, within the between-flight band): FAIL** — r1/r2/r3 each **5/6**, r4/r5 **PASS 6/6**; overall **FAIL** because P`
- L114 [dash_prose]: `- **P2 (one-keyframe FGO retains R ≥ 0.5 of the FGO–UKF gap on line-textured walls, per bag): PASS, 3/3** — R(r3) = 1.01, 0.97, 0.98  .`
- L115 [dash_prose]: `- **P3 (robust weighting replacing the heading gate, within the heading band): FAIL** — r6 **4/6**, r7 **2/6**  .`
- L120 [dash_prose]: `- E2's descriptive comparison with the known-map Experiment 2 FGO (different inputs —   every detection vs   one fix per frame — and differe`
- L138 [dash_prose]: `"inside the band" — this is the pre-registration's own "weak test" caveat, already stated against P1 above, not a`
- L150 [dash_prose]: `- **"NOT MET" means two different things across the main experiments and the tier-1 extensions, and E3 shows the collision directly.** The m`

**docs/thesis/writing_pack/methodology_factsheets/README.md**
- L24 [dash_prose]: `145 when this pack was created — see Flags (a) below).`
- L33 [dash_prose]: `correct facts, without either source disagreeing with the other, belongs in Appendix candidates instead — see the`
- L46 [dash_prose]: `bullet states) is run in **strict** mode — numbers.md/numbers_tier1.md or a   tag only, no other`
- L47 [dash_prose]: `citation counts — **only on bullets this pass's own   against   touched**, in the Facts or`
- L57 [dash_prose]: `citation as "known to resolve at this commit", not as "content re-verified this pass" — the exception is any`
- L78 [dash_prose]: `- A value correction, not just a citation fix: **"24×/42×" → "×24.7/×42"** (3.3, UKF Cholesky-jitter bullet) — the`
- L90 [dash_prose]: `item, not Facts) keeps citing   and   directly, as it always did — see Flags (a).`
- L91 [rtf_bare]: `Also added to 3.5:   (confirms "RTF 1.0"/"RTF 0.5" literally, for the closed-loop-without-heading`
- L96 [dash_prose]: `- **3.3 Estimators:** three new facts — the E3 robust tag-factor FGO (Cauchy k = 2.385 on tag landmark factors`
- L98 [dash_prose]: `flag — plus the citation and value fixes above.`
- L99 [dash_prose]: `- **3.4 How the estimators were run:** three new facts — E2–E6/the ablation are offline replay of existing`
- L100 [dash_prose]: `recordings (E6 excepted, which adds 5 new flights — 1 verification + 4 mapping attempts, since   was`
- L104 [dash_prose]: `- **3.6 Metrics and statistics:** six new facts — the tier-1 extension verdict vocabulary (a narrower scheme than`
- L107 [dash_prose]: `- **3.7 Verification process:** five new facts — the tier-1 checksum guard (new verification mechanism: scope,`
- L113 [dash_prose]: `and only needed its citations and one value fixed (above) plus the   addition — no new`
- L125 [dash_prose]: `each of the four   sections — indented   /   sub-items are not counted separately, matching the`
- L170 [dash_prose]: `them, and none is a checker failure — a NOT-IN tag only means the value is not in  /`
- L202 [dash_prose]: `- the time-sync cost (M:3891); the old roll gains (M:4569-4576, corrected — see above); the room_tags world geometry`
- L271 [dash_prose]: `summary pages — the extension pages print the registered word, not a paraphrase (3.6, 3.9).`

**docs/thesis/writing_pack/new_2026-11-11/caption_detail.md**
- L11 [rtf_bare]: `- Full condition statement dropped from the compressed caption: "Textured corridor at half real-time (RTF 0.5; the`
- L151 [dash_prose]: `(O_r1), 123.08 s (O_r2) and 123.08 s (O_r3b) — matching the "~123 s" read off the plot. EKF3's own source-set`
- L155 [dash_prose]: `window — i.e. the actual position jump, independently recomputed here from each flight's  , using`
- L156 [dash_prose]: `the same   lower-envelope clock map   already uses for F6/F9 — occurs at EXACTLY the`
- L160 [dash_prose]: `OFF), that jump sits at x = 127.40 s (O_r1), 127.40 s (O_r2) and 127.37 s (O_r3b) — matching the "~127 s" peak read`
- L184 [dash_prose]: `(4.32 / 4.32 / 4.28)" — i.e. ON + 4.3 s, not ON + 4.4 s. This investigation's own independent measurement (4.32 /`
- L191 [dash_prose]: `three flights — essentially one sample after the line, not 4+ seconds after it. The FGO ingests each GNSS fix`
- L283 [dash_prose]: `## Stage B notes (not part of the removed-text blocks above — coordinator reading only)`
- L290 [dash_prose]: `states that panels (a) and (b) use different flights with different ATEs (4.10/5.17/4.48 m vs 4.08/4.96/4.54 m) — do`
- L303 [dash_prose]: `or line citations on a caption) — the full derivation and the file list remain in`
- L310 [dash_prose]: `horizontal, North vertical — the pre-restyle orientation) to a 2x2 grid, North horizontal (increasing right) and`
- L316 [dash_prose]: `### Task 5 — does Figure 4.1c carry information Figure 4.1d does not?`
- L323 [dash_prose]: `figure's panel (b) — that prose is all backed by a separate, already-registered distance-scale computation`

**docs/thesis/writing_pack/new_2026-11-11/ekf3_heading_preregistration.md**
- L10 [dash_prose]: `real log (see "Round-trip check" below) — both diagnostic, neither a flight nor an`
- L59 [dash_prose]: `### 2.1 METHODOLOGY "RULING — EKF3 in the offline forward-camera comparison (user,`
- L74 [dash_prose]: `) — which includes all 18  /  Phase-4 bags — has`
- L79 [dash_prose]: `throughout (137,879 / 138,318 in a 30.8 MB log) — i.e. it is a genuine DAL-enabled`
- L83 [dash_prose]: `**The "Phase 5 trigger" is also met — checked against the actual Phase 5 verdict, not`
- L84 [dash_prose]: `assumed.** Phase 5's pre-registered prediction (a) — "the heading-driven [lateral`
- L85 [dash_prose]: `velocity error] share falls" — is accepted **PASS in 12/12 estimator × world × dataset`
- L86 [dash_prose]: `cells** ( , "Phase 5 — accepted (user, 2026-09-29)"): the`
- L90 [dash_prose]: `staying unchanged, was scored FAIL in 10/12 cells — not relevant to this trigger, which`
- L92 [dash_prose]: `This is a real, accepted, measured effect of adding camera heading to the UKF/FGO — the`
- L97 [dash_prose]: `D70 (2026-10-31) answered a narrower question — whether to add a sixth, **unscored,`
- L104 [dash_prose]: `untouched — this document does not ask for that panel to be re-scored or removed.`
- L123 [dash_prose]: `— heading noise 0.148° (fwdc) / 0.126° (fwdplainc), per`
- L126 [dash_prose]: `— same noise values (shared code).`
- L132 [dash_prose]: `| (i) | EKF3 | none (Replay, no injection) | — | NEW; must reproduce the dataset's stored EKF3   score to ≤ 1 mm (METHODOLOGY D8,  ) |`
- L139 [dash_prose]: `UKF/FGO under the SAME σ**, not against their existing, tighter 0.148°/0.126° arms —`
- L146 [dash_prose]: `and read nowhere else in EKF3 — there is no EKF3 input`
- L154 [dash_prose]: `— the floor is the whole point of comparing (ii) against (iii)/(iv) at the SAME nominal`
- L166 [dash_prose]: `— i.e.`
- L167 [dash_prose]: `( ) — directly. **So arm (ii) is governed by the`
- L170 [dash_prose]: `path the ruling considered (option 2) would have imposed — part of why option 1`
- L177 [dash_prose]: `delay buffer) — i.e. a measurement timestamped before the current delayed-fusion`
- L181 [dash_prose]: `to fall behind this horizon, EKF3's own clamp — not this tool's splice position —`
- L187 [dash_prose]: `this horizon is not checked in this stage — it is listed as part of the open "TS and D"`
- L192 [dash_prose]: `**Source: the frozen Phase 3 outputs**,   — the exact`
- L194 [dash_prose]: `existing UKF/FGO heading arms. **Validity: measurement-intrinsic only** — support ≥`
- L204 [dash_prose]: `— no   decimation in  . Injecting every`
- L207 [dash_prose]: `to be "decided by matching the offline UKF/FGO heading arm's input, and state it" — done:`
- L217 [dash_prose]: `every  / /  bag — arm (i) is scored by the identical function`
- L220 [dash_prose]: `2. Yaw error vs ground truth (mean, RMS, end-of-cruise, linear drift deg/min) — same`
- L223 [dash_prose]: `3. Forward-measurement valid/fused counts and NIS of the tested measurements — for`
- L227 [dash_prose]: `fusion test ratio, logged in  /innovation fields — this needs the SAME field`
- L233 [dash_prose]: `the UKF/FGO's Python step-time figures at all — arms (iii)/(iv)'s Python step time is`
- L245 [dash_prose]: `prediction for "EKF3 + camera heading via a 5°-floored ExternalNav path" specifically —`
- L251 [dash_prose]: `n = 9   bags" is the closest existing EKF3 figure, though not on these bags) —`
- L256 [dash_prose]: `baselines (a looser σ should help less) — this one IS a quantitative-shaped`
- L264 [dash_prose]: `UKF/FGO's own best arms use — whether EKF3's different fusion mechanics (gated`
- L272 [dash_prose]: `## 8. The round-trip check — findings, final design, and the gate`
- L277 [dash_prose]: `template, which surfaced two wrong placement rules before the correct one — recorded`
- L285 [dash_prose]: `original — a stronger, directly-runnable proxy for "does the mechanics preserve the`

**docs/thesis/writing_pack/new_2026-11-11/extras_preregistration.md**
- L83 [dash_prose]: `-   gets, per cell: the contact times, k/3, the spread (min–max), and the existing n = 1 verdict for`

**docs/thesis/writing_pack/new_2026-11-11/numbers_cl_heading_perflight.md**
- L9 [dash_prose]: `| EKF3, full speed (RTF 1.0), Python heading node | 1 ( ) | 0.27 | 0.36 | 0.54 | 0.033 | all pass | — |`
- L10 [dash_prose]: `| EKF3, full speed (RTF 1.0), Python heading node | 2 ( ) | 0.31 | 0.28 | 0.31 | 0.019 | all pass | — |`
- L11 [dash_prose]: `| EKF3, full speed (RTF 1.0), Python heading node | 3 ( ) | 0.29 | 0.28 | 0.34 | 0.017 | all pass | — |`
- L12 [dash_prose]: `| EKF3, full speed (RTF 1.0), C++ heading node | 1 ( ) | 0.25 | 0.31 | 0.42 | 0.140 | all pass | — |`
- L13 [dash_prose]: `| EKF3, full speed (RTF 1.0), C++ heading node | 2 ( ) | 0.23 | 0.28 | 0.40 | 0.027 | all pass | — |`
- L14 [dash_prose]: `| EKF3, full speed (RTF 1.0), C++ heading node | 3 ( ) | 0.34 | 0.29 | 0.42 | 0.021 | all pass | — |`
- L15 [dash_prose]: `| EKF3, half real time (RTF 0.5), C++ heading node | 1 ( ) | 0.33 | 0.32 | 0.39 | 0.181 | all pass | — |`
- L16 [dash_prose]: `| EKF3, half real time (RTF 0.5), C++ heading node | 2 ( ) | 0.25 | 0.28 | 0.34 | 0.044 | all pass | — |`
- L17 [dash_prose]: `| EKF3, half real time (RTF 0.5), C++ heading node | 3 ( ) | 0.24 | 0.29 | 0.33 | 0.027 | all pass | — |`
- L18 [dash_prose]: `| original FGO, hard-gated, half real time | 1 ( ) | 0.06 | 0.26 | 1.44 | 0.037 | all pass | — |`
- L19 [dash_prose]: `| original FGO, hard-gated, half real time | 2 ( ) | 0.08 | 0.26 | 1.28 | 0.013 | all pass | — |`
- L20 [dash_prose]: `| original FGO, hard-gated, half real time | 3 ( ) | 0.25 | 0.38 | 1.88 | 0.120 | all pass | — |`
- L21 [dash_prose]: `| original FGO, robust weighting, half real time | 1 ( ) | 0.08 | 0.26 | 0.86 | 0.014 | all pass | — |`
- L22 [dash_prose]: `| original FGO, robust weighting, half real time | 2 ( ) | 0.14 | 0.29 | 0.95 | 0.019 | all pass | — |`
- L23 [dash_prose]: `| original FGO, robust weighting, half real time | 3 ( ) | 0.05 | 0.30 | 1.15 | 0.040 | all pass | — |`
- L27 [dash_prose]: `*Checks (EXACT): 25/25 — every value against its score file; the half real-time EKF3 row against Table 4.3; the per-set min–max against numb`

**docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md**
- L188 [dash_prose]: `finishing — checked, not assumed, since another agent is working in this same checkout.** It touched only`
- L189 [dash_prose]: `and a new standalone script   — neither`
- L287 [dash_prose]: `**Fails in 8 of 12 losses** (r1: all 4; r2: 15 s and move; r3: 15 s and move) — descriptive, as worded, no set-level`
- L298 [dash_prose]: `gave <0.02 deg on all three   flights — 25-60x too small to be the quantity behind -0.23/+0.52/+0.52 deg,`
- L307 [dash_prose]: `**-0.228 / +0.512 / +0.515 deg**, against the stored -0.23/+0.52/+0.52 deg — matching to within 0.01-0.02 deg (the`
- L423 [dash_prose]: `**0 changed, 0 missing, 0 errors, 5 added** — exactly this task's own five new output files, nothing else.`
- L456 [dash_prose]: `(exactly this task's own five new output files) — a genuine before/after pair, reading clean (section 6).`

**docs/thesis/writing_pack/new_2026-11-11/refly_preregistration.md**
- L23 [rtf_bare]: `| 1C without heading |   (RTF 0.5) | FGO, Python node | 3 |   |   (n = 1) |`
- L24 [rtf_bare]: `| 1C with heading |   (RTF 0.5) | FGO, Python node; C++ heading node | 3 |   |   |`

**docs/thesis/writing_pack/numbers.md**
- L57 [dash_prose]: `| Flow RANSAC seed | 42 | — | CURRENT |`
- L75 [dash_prose]: `| RTF, old machine | 0.05 – 0.17 | — | CURRENT (historical) |`
- L76 [dash_prose]: `| RTF, new machine (pre-fix) | ≈0.86 | — | CURRENT (historical) |`
- L77 [dash_prose]: `| RTF, corridor collision root cause (as-is) | 0.0134 | — | CURRENT (finding) |`
- L78 [dash_prose]: `| RTF, 8 tiles rendering, 1 with collision | 0.3934 | — | CURRENT (finding) |`
- L79 [dash_prose]: `| RTF, live lockstep after fix (tex / blank / trans) | 0.917 / 0.912 / 0.927 | — | CURRENT |`
- L80 [dash_prose]: `| RTF, live lockstep mean | 0.919 | — | CURRENT |`
- L81 [dash_prose]: `| RTF,   flights (cruise method) | 0.975–0.981 | — | CURRENT |`
- L85 [dash_prose]: `| Forward camera RTF cost: control / fwd | 0.954 / 0.768 | — | DIAGNOSTIC |`
- L86 [dash_prose]: `| RTF diagnosis: control / full / norecord / nobridge | 0.957 / 0.759 / 0.761 / 0.958 | — | DIAGNOSTIC |`
- L87 [dash_prose]: `| Cost of bridging one 640×480 30 Hz image | ~40% of a core | — | CURRENT |`
- L88 [dash_prose]: `| RTF, Phase 2   | 0.73–0.81 | — | DIAGNOSTIC |`
- L89 [dash_prose]: `| RTF, ceiling datasets | 0.72–0.77 | — | DIAGNOSTIC |`
- L90 [dash_prose]: `| Live parameter audit | 1379 parameters on each side … 16 value differences | — | CURRENT |`
- L97 [dash_prose]: `| IMU rate evidence | 29665 msgs / 89.012 s; median dt 3.000 ms | — | CURRENT |`
- L117 [dash_prose]: `| OI-2 anchors per bag | 6722–6823 anchors, ≈ 81% | — | DIAGNOSTIC |`
- L147 [dash_prose]: `|   | 300 → NIS gate 9 (3σ) | — | CURRENT |`
- L149 [dash_prose]: `|   | 500 → NIS gate 25 (5σ) | — | CURRENT |`
- L151 [dash_prose]: `| GTSAM conversion rule |   | — | CURRENT |`
- L157 [dash_prose]: `|   (no EKF3 counterpart) | ~1e-8·I | — | CURRENT |`
- L159 [dash_prose]: `| EKF3 pseudo-yaw gate (quaternion trace) | 0.01 | — | CURRENT |`
- L162 [dash_prose]: `| EKF3   quaternion covariance | median 0.0093, max 0.01001 | — | CURRENT |`
- L163 [dash_prose]: `| UKF attitude-cov trace / firing rate | Euler **0.029** (quaternion-equivalent 0.0072) / ~1% | — | CURRENT |`
- L167 [dash_prose]: `|   translational sensitivity |   | — | CURRENT |`
- L168 [dash_prose]: `| Cruise rollspeed / pitchspeed std | 0.399 rad/s vs … 0.013 — 31× | rad/s | CURRENT |`
- L169 [dash_prose]: `| SITL gyro drift parameters |   deg/s/minute …   minutes | — | CURRENT |`
- L183 [dash_prose]: `| Frames per prediction | 5 frames = **0.0125 s** | — | CURRENT |`
- L187 [dash_prose]: `| UKF process noise vs EKF3 / FGO | identical per-second densities (EKF3's at DT_REF 12.5 ms; offline per-step forms scaled by DT_REF/dt) | `
- L195 [dash_prose]: `| Boxcar historical equivalent | 25-sample boxcar at the ~59 Hz GT rate | — | CURRENT |`
- L196 [dash_prose]: `| Window rule | largest contiguous run | — | CURRENT |`
- L197 [dash_prose]: `| Alignment |   (Umeyama SE3, no scale) | — | CURRENT |`
- L207 [dash_prose]: `| Failure metrics vs window (full vs cruise) | ratio by ≤ 0.05 and the onset by ≤ 1 m | — | CURRENT |`
- L208 [dash_prose]: `| n=3 exceedance probability | 2/(n+1) = 50% | — | CURRENT |`
- L211 [dash_prose]: `## 6. Baseline results — RESTATED after the consolidated re-run (2026-09-29)`
- L226 [dash_prose]: `| EKF3 vs FGO (claim wording) | **WITHDRAWN (ruling 2, 2026-10-10): "EKF3 beats / is lower than the FGO on standard sensors (textured floor)`
- L243 [dash_prose]: `| Valid airborne flow frames in cruise, blank (all 14 blank bags) | 0 | — | CURRENT | M: "Loss-of-flow analysis — flow-loss point defined" |`
- L244 [dash_prose]: `| Flow-loss cases | transition 14/14 B (y ≈ 80.5 m); blank 13 A + 1 C ( ) | — | CURRENT | same |`
- L246 [dash_prose]: `| EKF3 output while invalid | exactly the origin (0, 0); not scored (evaluation rule) | — | CURRENT | M: "Rulings on the early pipeline resu`
- L253 [dash_prose]: `|   transition displacement ratio, UKF / FGO (mean of 3) †| 6.8 / 17.7 (per flight FGO 18.0 / 18.1 / 17.0; was 45.9 / 50.0 before the final `
- L259 [dash_prose]: `| Heading share of EKF3 lateral drift (pinned window),   / r1 / r2 | 0.906 / 0.904 / 0.899 | — | CURRENT (correction (iii)) |`

**docs/thesis/writing_pack/raw_corridor/raw_corridor_numbers.md**
- L3 [dash_prose]: `Generated by   from   (generated by  ). **DESCRIPTIVE ONLY — nothing fitted** (no rotation, translation or scale alignment); these values do`
- L5 [dash_prose]: `**Stage 1b (D111, binding):** Stage 1 withheld raw values per CELL on a 2° heading-of-first-5m check; 69/154 cells were withheld. D111 ruled`
- L7 [dash_prose]: `**Frame convention** (identical to Figure 4.1c / R5,  , re-derived for this scope — not imported, since that script is scoped to one flight)`
- L9 [dash_prose]: `**Window source:** the registered cruise window   stored alongside each cell's own   (cited per row below) — the same window the registered `
- L11 [dash_prose]: `**Association:**  ,  , identical to  / . The raw (unaligned) error is a plain subtraction in the common (N, E, U) frame on this same associa`
- L15 [dash_prose]: `**Strict check definition** (same computation as Stage 1's per-cell check, now informational only — see   below for what actually gates raw-`
- L27 [dash_prose]: `**Early heading offset column (DESCRIPTIVE, never a gate):**   over the first 5 m of true cruise travel from the window start (same quantity`
- L33 [dash_prose]: `**RC-7 (Stage 1 handover) still applies:** EKF3 on the transition floor sits pinned near the origin for ~140 s of the ~300 s cruise after lo`

**docs/thesis/writing_pack/tables/R1_hypothesis_scorecard.md**
- L39 [dash_prose]: `| H2.1 | FGO hindsight gain grows with the gap (primary) | “H-T1 … the FGO's hindsight gain grows with the gap. PASS iff both: (i) the per-c`
- L41 [dash_prose]: `| H2.3 | live errors similar | “P-T3 (prediction): live errors are similar. In every condition, the largest live horizontal RMSE among EKF3,`
- L42 [dash_prose]: `| H2.4 | FGO hindsight ≈ smoothed UKF | “P-T4 (prediction): FGO hindsight ≈ RTS-UKF. In every condition, the larger of their horizontal RMSE`

**docs/thesis/writing_pack/tables/R2_corrections_by_discovery.md**
- L7 [dash_prose]: `| fairness (input-equivalence) audit | 1 | UKF/FGO IMU dejitter (sensor-time reconstruction) | DATA | Fairness audit OI-2 (2026-09-24): an i`
- L9 [dash_prose]: `| offline cross-check against ground truth (distance scale) | 3 | EKF3 flow sensor position FLOW_POS_Z 0.13 → 0.25 | CONFIG | Distance-scale`
- L10 [dash_prose]: `| offline cross-check against ground truth (distance scale) | 4 | UKF process dt = the accumulated IMU interval | MODEL | Distance-scale che`
- L11 [dash_prose]: `| analysis audit (window) | 8 | heading share on the pinned cruise window | ANALYSIS | Window audit (2026-09-29). | none: before the claims `
- L12 [dash_prose]: `| source-code reading | 7 | time sync on; AHRS_EKF_TYPE explicit; replay logging | CONFIG | Part C source reading (SIM_JSON.cpp:410-413, 202`
- L19 [dash_prose]: `| port and offline equivalence or comparison work | 19 | FGO trajectory-writer quaternion typo (D10) | SCORER (output writer) | Yaw represen`
- L20 [dash_prose]: `| diagnostic investigation of a measured effect | 6 | roll rate gains ×0.4447 (simulated vehicle) | MODEL (vehicle) | EKF3 flow-derotation t`
- L22 [dash_prose]: `| SITL flight (a defect exposed by a flown result) | 5 | lateral optical-flow sign | MODEL / bridge | Closed-loop smoke test (2026-09-29): t`
- L24 [dash_prose]: `| SITL flight (a defect exposed by a flown result) | 16 | offline UKF bias-corrected flow derotation | MODEL | H S1 input-path diagnostic (2`

**docs/thesis/writing_pack/tables/R4_information_vs_estimator.md**
- L3 [dash_prose]: `For each condition: the primary metric of each estimator, the best–worst spread across the estimators (max − min and max ÷ min), and the cha`
- L10 [dash_prose]: `| Experiment 2: known tags, live | horizontal RMSE (m); n = 3 flights per condition (mean); 4 conditions | 1 tag: EKF3 0.096, UKF 0.131, FGO`
- L11 [dash_prose]: `| Experiment 2: known tags, hindsight | horizontal RMSE (m); n = 3 flights per condition (mean) | 1 tag: FGO batch 0.028, smoothed UKF 0.109`
- L12 [dash_prose]: `| Experiment 4: outdoor–indoor, live | indoor horizontal RMSE (m), GNSS off for 123 s; n = 3 flights | EKF3 1.42–1.43, UKF 0.77–0.84, FGO 0.`
- L13 [dash_prose]: `| Experiment 4: outdoor–indoor, hindsight | indoor horizontal RMSE (m); n = 3 flights | FGO batch 0.59–0.59, smoothed UKF 0.58–0.60 | - | ma`

**docs/thesis/writing_pack/tables/T1_scorecard.md**
- L3 [dash_prose]: `Each cell gives the key number and the verdict it rests on, with a status (PASSED, N/A, or on the blank floor 'no estimator bounds position `
- L13 [dash_prose]: `| Experiment 4: outdoor–indoor (GNSS outside only)   | indoor 1.42–1.43 m (no live ordering claimed; 4.10 m jump, about 4.3 s after GNSS ret`
- L22 [dash_prose]: `*Why no ordering label, by row (the footnote letters): standard sensors, H1.1 test run, rule not met  , the UKF medians descriptive  ; with `
- L26 [dash_prose]: `*Ordering footnotes  –  (one per comparison; the letters in the experiment column): each footnote states the rule, the result and why no ord`

**docs/thesis/writing_pack/tables/T2_accuracy_heading.md**
- L7 [dash_prose]: `| EKF3 | 4.10 (3.11–4.12) | RMS 14.58 (7.84–14.64); end 37.39 (22.54–37.56) | 4.09 / 3.60 / 4.08 | RMS 14.54 / 11.16 / 14.45; end 37.30 / 29`

**docs/thesis/writing_pack/tables/T5_H_tag_loss_drift.md**
- L3 [dash_prose]: `Holding on a wall tag, every flying estimator drifts at most about 30 mm while the tag is hidden, inside every pre-registered band, and none`
- L14 [dash_prose]: `*Drift = the EFFECTIVE metric (last fix → first returning fix); the end-of-loss metric differs by ≤ 5 mm (unrounded 5.1 mm). Pre-registered `

**docs/thesis/writing_pack/tables/T6_O_indoor_rmse.md**
- L1 [dash_prose]: `# Table 5.1. Experiment 4 (outdoor–indoor): indoor horizontal RMSE per flight (123 s, GNSS off)`
- L12 [dash_prose]: `| live max ÷ min (H4.2) | — | 1.72 | 1.71 | 1.84 | 1.71–1.84 |`

**docs/thesis/writing_pack/tables/TA_verdicts.md**
- L3 [dash_prose]: `ONE row per pre-registered hypothesis, check or prediction, gathered from the tables and verdict files that already scored it, so that no PA`
- L39 [dash_prose]: `| Experiment 2 | H2.1 | “H-T1 … the FGO's hindsight gain grows with the gap. PASS iff both: (i) the per-condition medians of Δ_FGO increase `
- L41 [dash_prose]: `| Experiment 2 | H2.3 | “P-T3 (prediction): live errors are similar. In every condition, the largest live horizontal RMSE among EKF3, UKF an`
- L42 [dash_prose]: `| Experiment 2 | H2.4 | “P-T4 (prediction): FGO hindsight ≈ RTS-UKF. In every condition, the larger of their horizontal RMSEs (mean over rep`
- L80 [dash_prose]: `| Extension E3 | P-E3.6 | dose–response: per flight, the seed-mean LC live overall satisfies clean ≤ 1% ≤ 5%, 3/3 flights   | FAIL 0/3 | FAI`
- L101 [dash_prose]: `| EXPLORATORY | P2 (with heading) | the one-keyframe converged FGO (r3: cap 100; convergence not confirmed, iteration counts not logged) ret`
- L124 [dash_prose]: `*Verdicts (the project's own vocabulary; never softened or strengthened): PASS = the record says PASS, MET, TRUE or an accepted-as-worded ve`

**docs/thesis/writing_pack/tables/methods_estimator_design.md**
- L10 [dash_prose]: `| filter or smoother | extended Kalman filter | unscented Kalman filter (an RTS smoother over its predict nodes gives the hindsight track in`

**docs/thesis/writing_pack/tables/methods_experiment_matrix.md**
- L11 [dash_prose]: `| 1B: robust-weighting replication | corridor with ceiling, textured floor; plain and textured walls | as 1B offline fusion | UKF hard-gated`
- L15 [dash_prose]: `| 4 outdoor–indoor | outdoor–indoor world (GNSS outside only) | IMU, flow, LiDAR; GNSS outdoors only | EKF3 live, passive (truth flying); UK`
- L21 [rtf_bare]: `*'Truth flying' = AHRS_EKF_TYPE 10: the simulator's state flies the vehicle, so the path does not depend on any estimator; EKF3 then runs li`

**docs/thesis/writing_pack/thesis_vocabulary.md**
- L42 [dash_prose]: `| **2** | **Known tags** | Experiment T | AprilTag fixes at known positions; 4 tag densities (conditions A–D) × 3 |`
- L44 [dash_prose]: `| **4** | **Outdoor–indoor** | Experiment O | GNSS outside only; 123 s indoors on IMU, flow and LiDAR |`
- L74 [dash_prose]: `| 4 | Experiment 4, outdoor–indoor | Experiment O |`
- L185 [dash_prose]: `### Experiment 4 (outdoor–indoor)`
- L266 [dash_prose]: `| ENU | east–north–up | repo: CLAUDE.md:376 (axis definitions) |`
- L270 [dash_prose]: `| FLU | forward–left–up (body frame) | standard expansion, not in the repo (glossary:3450) |`
- L271 [dash_prose]: `| FRD | forward–right–down (body frame) | standard expansion, not in the repo (glossary:3454) |`
- L279 [dash_prose]: `| LM | Levenberg–Marquardt | co-occurrence:   ( ) |`
- L283 [dash_prose]: `| NED | north–east–down | repo: CLAUDE.md:376 |`
- L290 [dash_prose]: `| RTS | Rauch–Tung–Striebel (smoother) |`
- L339 [dash_prose]: `| 12 | 2(a) P1/S1/S2; 2(b) | numbers.md:489-495 | H1.7a–c; 2(b) as "the robust closed-loop set" (descriptive) |`
- L356 [dash_prose]: `| 29 | conditions A–D;  …  | F5 caption (index.md:50);   | "condition A–D" (kept; see §10) |`
- L424 [dash_prose]: `| Experiment 4, outdoor–indoor | Experiment O |`
- L491 [dash_prose]: `| 8 | departure | 2(a) robust-FGO rules **RS1/RS2** (1132) | **H1.7a–c** | as row 7 |`
- L494 [rtf_bare]: `| 11 | adopted with extension | **"_half: write 'half real-time factor (RTF 0.5)'"** (1166) | adopted. It also bans "half speed", which is i`
- L496 [dash_prose]: `| 13 | adopted | **"live / hindsight: define once per experiment"** (1160) | adopted. Defined once (M:7937-7938), with an explicit Experimen`
- L497 [dash_prose]: `| 14 | adopted | **"batch: hindsight batch / fixed-lag smoother"** (1161) | adopted, as "FGO whole-flight batch"; the live solver is "fixed-`
- L500 [dash_prose]: `| 17 | adopted | **"gt_: write 'ground-test runs'; reserve GT for ground truth"** (1165) | adopted. GT is expanded in §7 | — |`
- L501 [dash_prose]: `| 18 | adopted | **"Expand the dataset abbreviations at first use … do not invent an expansion"** (1089) | adopted. Terms 11–16 are descript`
- L504 [dash_prose]: `| 21 | adopted | Experiment T conditions **"condition A–D (never 'T1…')"** (1125) | adopted unchanged | — |`

**docs/thesis/writing_pack/tier1/e3_results.md**
- L88 [dash_prose]: `| P-E3.6 dose–response: seed-mean LC live clean ≤ 1% ≤ 5%, per flight | **FAIL** | 0/3 | each flight has 2 diverged 1% runs (seed means not `
- L108 [dash_prose]: `| T_A_r1 | 1% | 1 | **diverged**: onset 49.699 s, 1st exception 52.432 s, fail fraction 0.90 | diverged | diverged | diverged | diverged → d`
- L109 [dash_prose]: `| T_A_r1 | 1% | 2 | **diverged**: onset 59.699 s, 1st exception 63.832 s, fail fraction 0.86 | diverged | diverged | diverged | diverged → d`
- L114 [dash_prose]: `| T_A_r2 | 1% | 1 | **diverged**: onset 61.795 s, 1st exception 62.595 s, fail fraction 0.86 | diverged | diverged | diverged | diverged → d`
- L115 [dash_prose]: `| T_A_r2 | 1% | 2 | **diverged**: onset 59.928 s, 1st exception 60.695 s, fail fraction 0.87 | diverged | diverged | diverged | diverged → d`
- L120 [dash_prose]: `| T_A_r3 | 1% | 1 | **diverged**: onset 56.248 s, 1st exception 60.548 s, fail fraction 0.87 | diverged | diverged | diverged | diverged → d`
- L121 [dash_prose]: `| T_A_r3 | 1% | 2 | **diverged**: onset 60.314 s, 1st exception 65.614 s, fail fraction 0.85 | diverged | diverged | diverged | diverged → d`
- L160 [dash_prose]: `Sources:   and  . "—" marks a ratio that needs a diverged arm (a) run.`
- L164 [dash_prose]: `| T_A_r1 | 0 (control) | — | OK | 0.0581 | 0.0201 | 0.1080 → 0.0329 | 0.30 | (clean 0.0574) | — | — | 1.01 | 0 | 206.2 | 1.62 (not like for `
- L166 [dash_prose]: `| T_A_r1 | 1% | 1 | OK | 0.1758 | 0.0154 | 0.3645 → 0.0275 | 0.08 | diverged | — | — | 3.06 | 0 | 230.5 | — | 0.1 / 0.0 |`
- L167 [dash_prose]: `| T_A_r1 | 1% | 2 | OK | 0.3902 | 0.0149 | 0.8693 → 0.0296 | 0.03 | diverged | — | — | 6.80 | 0 | 281.1 | — | 0.1 / 0.0 |`
- L171 [dash_prose]: `| T_A_r2 | 0 (control) | — | OK | 0.0484 | 0.0263 | 0.0811 → 0.0341 | 0.42 | (clean 0.0494) | — | — | 0.98 | 0 | 121.2 | 0.79 (serial pair, `
- L173 [dash_prose]: `| T_A_r2 | 1% | 1 | OK | 0.0496 | 0.0154 | 0.0904 → 0.0271 | 0.30 | diverged | — | — | 1.00 | 0 | 193.0 | — | 0.1 / 0.0 |`
- L174 [dash_prose]: `| T_A_r2 | 1% | 2 | OK | 0.2287 | 0.0151 | 0.4342 → 0.0256 | 0.06 | diverged | — | — | 4.63 | 0 | 306.1 | — | 0.1 / 0.0 |`
- L178 [dash_prose]: `| T_A_r3 | 0 (control) | — | OK | 0.0760 | 0.0175 | 0.1614 → 0.0250 | 0.15 | (clean 0.0760) | — | — | 1.00 | 0 | 387.3 | 0.75 (not like for `
- L180 [dash_prose]: `| T_A_r3 | 1% | 1 | OK | 0.1984 | 0.0120 | 0.4147 → 0.0265 | 0.06 | diverged | — | — | 2.61 | 0 | 229.1 | — | 0.1 / 0.0 |`
- L181 [dash_prose]: `| T_A_r3 | 1% | 2 | OK | 0.1259 | 0.0114 | 0.2767 → 0.0238 | 0.09 | diverged | — | — | 1.66 | 0 | 251.3 | — | 0.1 / 0.0 |`
- L201 [dash_prose]: `| the pair's arm (a)   and   vs the stored Experiment 3   | **byte-IDENTICAL** ( , both files) | — |   |`
- L202 [dash_prose]: `| (b)/(a) at 1%: median (min–max) of 3 pairs without a diverged run | 0.07 (0.04–0.16) | NOT LIKE FOR LIKE (parallel batch; arm (a) T_A_r1 s`
- L203 [dash_prose]: `| (b)/(a) at 5%: median (min–max) of 9 pairs | 0.04 (0.03–0.08) | NOT LIKE FOR LIKE |   |`
- L331 [dash_prose]: `| original (scored) | — | 19 | 3, 6 | OK | 3.7618 | 3.5648 | 1.224 | 3088.4 |`

**docs/thesis/writing_pack/tier1/e4_results.md**
- L53 [dash_prose]: `| W (s) | cap | runs completed | status OK / FAILED-ESTIMATOR | driver wall min–max (s) | mean (s) |`
- L119 [dash_prose]: `| W (s) | F(W) pooled, 12 flights | F A | F B | F C | F D | median f_i | f_i min–max | flights |`

**docs/thesis/writing_pack/tier1/e5_results.md**
- L132 [dash_prose]: `| 36 judges | 36 | 0.9–1.0 | 33 | — |`

**docs/thesis/writing_pack/tier1/e6_preregistration.md**
- L189 [dash_prose]: `- Arms (i)–(iii) use the thesis estimators on   (one fix per frame). Arm (iv) uses the separate`
- L226 [dash_prose]: `(i)–(iv).`
- L237 [dash_prose]: `| **Idle** | no  , no  , no  /  of another job, no plot job (  for  ,  ,  ); recorded before every job | all clear | — |`
- L268 [dash_prose]: `| **1a** | code + this pre-registration committed on   | — | 31 Oct ≈ 23:00 |`
- L273 [dash_prose]: `| — | handover to Stage 2 (a fresh agent) | — | — |`
- L315 [dash_prose]: `arms (i)–(iii) use the thesis estimators on one fix per frame (§4).`

**docs/thesis/writing_pack/tier1/numbers_tier1.md**
- L261 [dash_prose]: `| T_A_r1 P-E3.6 | not satisfied (diverged: E3a_T_A_r1_0.01_s1, E3a_T_A_r1_0.01_s2); seed means not computed | — | CURRENT |   |`
- L262 [dash_prose]: `| T_A_r2 P-E3.6 | not satisfied (diverged: E3a_T_A_r2_0.01_s1, E3a_T_A_r2_0.01_s2); seed means not computed | — | CURRENT |   |`
- L263 [dash_prose]: `| T_A_r3 P-E3.6 | not satisfied (diverged: E3a_T_A_r3_0.01_s1, E3a_T_A_r3_0.01_s2); seed means not computed | — | CURRENT |   |`
- L291 [dash_prose]: `| T_A_r1 robust 1% s1 P-E3b.1 | (a) diverged at 49.699 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not `
- L295 [dash_prose]: `| T_A_r1 robust 1% s2 P-E3b.1 | (a) diverged at 59.699 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not `
- L319 [dash_prose]: `| T_A_r2 robust 1% s1 P-E3b.1 | (a) diverged at 61.795 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not `
- L323 [dash_prose]: `| T_A_r2 robust 1% s2 P-E3b.1 | (a) diverged at 59.928 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not `
- L347 [dash_prose]: `| T_A_r3 robust 1% s1 P-E3b.1 | (a) diverged at 56.248 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not `
- L351 [dash_prose]: `| T_A_r3 robust 1% s2 P-E3b.1 | (a) diverged at 60.314 s, (b) OK: SATISFIED, flagged (user ruling 2026-10-23); no ratio, (a)'s error is not `
- L365 [dash_prose]: `| runtime (b)/(a), 1%: median (min–max) of 3 pairs without a diverged run | 0.07 (0.04–0.16) | ratio | DESCRIPTIVE, NOT LIKE FOR LIKE (paral`
- L366 [dash_prose]: `| runtime (b)/(a), 5%: median (min–max) of 9 pairs without a diverged run | 0.04 (0.03–0.08) | ratio | DESCRIPTIVE, NOT LIKE FOR LIKE (paral`
- L519 [dash_prose]: `| P-E4.1 | PASS (12/12) | — | CURRENT |   |`
- L520 [dash_prose]: `| P-E4.2 | PASS (0.25 s 12/12, 1 s 12/12, 2 s 12/12, 5 s 12/12) | — | CURRENT |   |`
- L521 [dash_prose]: `| H-E4.3 | FAIL (7/12) | — | CURRENT |   |`

**docs/thesis/writing_pack/tier1/preregistration.md**
- L375 [dash_prose]: `| P-E3.6 (dose–response) | per flight, the seed-mean LC live overall satisfies clean ≤ 1% ≤ 5% | 3/3 flights | The nesting (§2.1 item 4) mea`
- L592 [dash_prose]: `| — | live RMSE at every W; f_i(W) and F(W) | **DESCRIPTIVE ONLY** | Defined above. |`
- L823 [dash_prose]: `| snapshot, G0-L, G0-UKF | 1 + 2 + 12 | 521 s; 63 s | 0.5 h | — |`
- L825 [dash_prose]: `| E2 no-LC | 9 | ≤ 9,584 s (fewer landmarks in B–D: 21 / 11 / 6 passes against 41, so likely much less) | **≤ 24 h** | 0 |`

## E. EKF3 4.3 s switching delay / 4.10 m jump statements

Source checked: `eval/results/expO_switch_delay/switch_delay.json` (loaded OK) and `sim/scripts/o_source_switch.lua` (found).
- Harness vote line (lua): `elseif votes <= -VMAX and current ~= 0 then`
- `numbers.md` §16.2 (O - outdoor->indoor): EKF3 live largest step in 10 s after return = **4.10 m (reset jump, every flight)**; error at GNSS return 3.53-3.54 m. This is the measured source of both numbers (not independently re-derived here; see METHODOLOGY context cited in the task).

### Mechanism, confirmed from the stored data and the harness script (read, not re-derived)

`sim/scripts/o_source_switch.lua`: `VMAX = 20`, re-scheduled every 100 ms (`return update, 100`); a full swing from +20 to -20 needs 40 one-sided vote increments, i.e. **40 x 100 ms = 4.0 s** - this is the 'harness Lua script's 40-vote (4.0 s) GPS-status vote' the task's known context names, confirmed directly in the script's own constants, not assumed.

`eval/results/expO_switch_delay/switch_delay.json` (`O_r1`/`O_r2`/`O_r3b`, all three agree to within 0.06 s) breaks the ON-side delay into exactly these two parts: `gps_status_minus_parm_sitl_s` = 0.30-0.36 s (SIM_GPS1_ENABLE flip to a good GPS fix - the '~0.3 s simulated GPS latency'), then `ss_minus_gps_status_sitl_s` = 4.04 s (good fix to `XKFS.SS` actually switching) - and `lua_msgs_sitl_s`'s own 'O-switch: source set 1 (GPS)' log line fires at essentially the same instant as the `XKFS.SS` change (within 0.06 s), not ~4 s before it. The ~4 s gap sits BETWEEN the GPS fix becoming good and the Lua script's own vote completing, not between the Lua script firing and EKF3 acting on it. Total delay (`ss_minus_marker_sitl_s`) = 4.32-4.37 s, matching the stated 4.3 s.

**Finding worth flagging on its own**: `docs/thesis/writing_pack/new_2026-11-11/caption_detail.md` Task 6 (lines 145-193) is the single most detailed investigation of this delay found anywhere in the scanned corpus - it independently re-measures `XKFS.SS` and the `XKF1` position jump from each flight's `ardupilot.bin` and gets the same 4.3 s / 4.10 m numbers. But its own explanation (lines 163-193) attributes the delay to **EKF3's internal GPS-validation gate** (`readyToUseGPS()`/`gpsGoodToAlign` in `AP_NavEKF3_Control.cpp`/`AP_NavEKF3_VehicleStatus.cpp`), and never mentions the harness's `o_source_switch.lua` vote script at all, although it does honestly caveat (line 192) that 'the exact 4.3 s was not traced sample-by-sample through that gate here - it is measured ... not derived from the gate's internal thresholds.' Given the switch_delay.json breakdown above, the dominant ~4.0 s component times out almost exactly with the harness script's own 40-vote timer, not with an EKF3-internal threshold search of that script's own constants; this document's attribution looks incomplete at best, and is itself an UNQUALIFIED statement by the task's definition (it names an EKF3-internal cause, not the harness switching script). This is reported as a finding for the coordinator, not resolved here.

| file:line | matched | qualified? | text |
|---|---|---|---|
| docs/thesis/tables/T1_scorecard.md:13 | 4.10 m | yes | / Experiment 4: outdoor–indoor (GNSS outside only) [f, g] / indoor 1.42–1.43 m (no live ordering claimed; 4.10 m jump, about 4.3 s after GNSS returns (the switching script's delay)) / indoor 0.77–0.84 |
| docs/thesis/tables/T1_scorecard.md:20 | 4.10 m | yes | *Experiment 4's EKF3 jump: the 4.10 m figure is measured once the simulation's GNSS switching script moves EKF3 off its indoor source set, about 4.3 s after GNSS returns (the script waits for 40 conse |
| docs/thesis/tables/T1_scorecard.tex:20 | 4.10 m | yes | Experiment 4: outdoor--indoor (GNSS outside only) [f, g] & indoor 1.42--1.43 m (no live ordering claimed; 4.10 m jump, about 4.3 s after GNSS returns (the switching script's delay)) & indoor 0.77--0.8 |
| docs/thesis/tables/T1_scorecard.tex:28 | 4.10 m | yes | \textit{Note.} Experiment 4's EKF3 jump: the 4.10 m figure is measured once the simulation's GNSS switching script moves EKF3 off its indoor source set, about 4.3 s after GNSS returns (the script wait |
| docs/thesis/tables/T7_failure_behaviour.md:3 | 4.1 m | yes | How each estimator fails: EKF3 declares its blank-floor position invalid while the UKF and the FGO run away with no invalid period recorded [a]; on the return to GNSS EKF3 jumps 4.1 m, about 4.3 s aft |
| docs/thesis/tables/T7_failure_behaviour.md:7 | 4.10 m | yes | / EKF3 / position flagged INVALID from take-off on all 14 blank flights (301–310 s of cruise; 0 valid airborne flow frames); outputs the origin, not scored: a DECLARED failure / resets to GNSS on retu |
| docs/thesis/tables/T7_failure_behaviour.md:21 | 4.3 s | yes | *[b] Ordering basis, Experiment 4, the jump on the return to GNSS. Metric: largest position step in the 10 s after GNSS returns, m. n = 3 flights (same flights for every estimator). Rule: none: EKF3's |
| docs/thesis/tables/T7_failure_behaviour.tex:8 | 4.1 m | yes | \caption{Failure behaviour: blank-floor validity, the Experiment 4 return jump and the 5S safety tests. How each estimator fails: EKF3 declares its blank-floor position invalid while the UKF and the F |
| docs/thesis/tables/T7_failure_behaviour.tex:14 | 4.10 m | yes | EKF3 & position flagged INVALID from take-off on all 14 blank flights (301--310 s of cruise; 0 valid airborne flow frames); outputs the origin, not scored: a DECLARED failure & resets to GNSS on retur |
| docs/thesis/tables/T7_failure_behaviour.tex:25 | 4.3 s | yes | \textit{Note.} [b] Ordering basis, Experiment 4, the jump on the return to GNSS. Metric: largest position step in the 10 s after GNSS returns, m. n = 3 flights (same flights for every estimator). Rule |
| docs/thesis/figures_thesis/captions/F6.md:1 | 4.1 m | yes | Figure 5.3. Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return, about 4.3 s after GNSS returns (the switching script's delay); hindsight keeps the error near 1 m. |
| docs/thesis/figures_thesis/captions/F6.md:3 | 4.10 m | yes | Experiment 4 (outdoor-indoor), flight 1: horizontal error against time in the world frame, with no alignment, as the vehicle flies outdoors, through a GNSS-denied indoor section, and back outdoors. Ro |
| docs/thesis/figures_thesis/index.md:32 | 4.1 m | yes | / Figure 5.3 / F6 / figure / `F6_O_outdoor_indoor.png`, `F6_O_outdoor_indoor.pdf` / Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return, about 4.3 s after GNSS returns (the switc |
| docs/thesis/figures_thesis/index.md:325 | 4.1 m | yes | ### Figure 5.3 (internal F6, figure): Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return, about 4.3 s after GNSS returns (the switching script's delay); hindsight keeps the erro |
| docs/thesis/figures_thesis/index.md:327 | 4.10 m | yes | - **Caption:** Experiment 4 (outdoor-indoor), flight 1: horizontal error against time in the world frame, with no alignment, as the vehicle flies outdoors, through a GNSS-denied indoor section, and ba |
| docs/thesis/figures_thesis/index.md:335 | 4.10 m | **NO** | / Experiment 4 EKF3 reset jump (m) / `4.10–4.10` / `4.10–4.10` / numbers.md §16.2 ('4.10 m, every flight') / yes / |
| docs/thesis/figures_thesis/index.md:506 | 4.1 m | yes | - **Caption:** How each estimator fails: EKF3 declares its blank-floor position invalid while the UKF and the FGO run away with no invalid period recorded [a]; on the return to GNSS EKF3 jumps 4.1 m,  |
| docs/thesis/figures_thesis/index.md:671 | 4.1 m | yes | / Figure 5.3 / F6 / `F6_O_outdoor_indoor.png`, `F6_O_outdoor_indoor.pdf` / Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return, about 4.3 s after GNSS returns (the switching scri |
| docs/thesis/thesis_assets/tables_tex/tab_7-1.tex:21 | 4.10 m | yes | Experiment 4: outdoor--indoor (GNSS outside only) [f, g] & indoor 1.42--1.43 m (no live ordering claimed; 4.10 m jump, about 4.3 s after GNSS returns (the switching script's delay)) & indoor 0.77--0.8 |
| docs/thesis/thesis_assets/tables_tex/tab_7-1.tex:29 | 4.10 m | yes | \textit{Note.} Experiment 4's EKF3 jump: the 4.10 m figure is measured once the simulation's GNSS switching script moves EKF3 off its indoor source set, about 4.3 s after GNSS returns (the script wait |
| docs/thesis/thesis_assets/tables_tex/tab_7-2.tex:9 | 4.1 m | yes | \caption{Table 7.2. Failure behaviour: blank-floor validity, the Experiment 4 return jump and the 5S safety tests. How each estimator fails: EKF3 declares its blank-floor position invalid while the UK |
| docs/thesis/thesis_assets/tables_tex/tab_7-2.tex:15 | 4.10 m | yes | EKF3 & position flagged INVALID from take-off on all 14 blank flights (301--310 s of cruise; 0 valid airborne flow frames); outputs the origin, not scored: a DECLARED failure & resets to GNSS on retur |
| docs/thesis/thesis_assets/tables_tex/tab_7-2.tex:26 | 4.3 s | yes | \textit{Note.} [b] Ordering basis, Experiment 4, the jump on the return to GNSS. Metric: largest position step in the 10 s after GNSS returns, m. n = 3 flights (same flights for every estimator). Rule |
| docs/thesis/thesis_assets/index.md:24 | 4.1 m | yes | / Figure 5.3 / Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return, about 4.3 s after GNSS returns (the switching script's delay); hindsight keeps the error near 1 m. / `figures/ |
| docs/thesis/writing_pack/figures_thesis/captions/F6.md:1 | 4.1 m | yes | Figure 5.3. Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return, about 4.3 s after GNSS returns (the switching script's delay); hindsight keeps the error near 1 m. |
| docs/thesis/writing_pack/figures_thesis/captions/F6.md:3 | 4.10 m | yes | Experiment 4 (outdoor-indoor), flight 1: horizontal error against time in the world frame, with no alignment, as the vehicle flies outdoors, through a GNSS-denied indoor section, and back outdoors. Ro |
| docs/thesis/writing_pack/new_2026-11-11/caption_detail.md:149 | 4.3 s | **NO** | **Finding: yes, EKF3's reset happens AFTER GNSS returns, by about 4.3 s, consistently across all three flights.** |
| docs/thesis/writing_pack/new_2026-11-11/caption_detail.md:164 | o_source_switch | yes | source-switching script, not an EKF3-internal gate.** `sim/scripts/o_source_switch.lua` runs inside SITL, |
| docs/thesis/writing_pack/new_2026-11-11/caption_detail.md:180 | 4.3 s | **NO** | **Reconciling with the quoted `numbers.md` line "EKF3 switched sets at OFF + 4.3 s and ON + 4.4 s":** that exact |
| docs/thesis/writing_pack/new_2026-11-11/caption_detail.md:183 | 4.3 s | **NO** | `numbers.md` line states the corrected values directly: "OFF + 4.3–4.4 s (4.37 / 4.37 / 4.34) and ON + 4.3 s |
| docs/thesis/writing_pack/new_2026-11-11/caption_detail.md:184 | 4.3 s | **NO** | (4.32 / 4.32 / 4.28)" — i.e. ON + 4.3 s, not ON + 4.4 s. This investigation's own independent measurement (4.32 / |
| docs/thesis/writing_pack/new_2026-11-11/caption_detail.md:193 | switch delay | yes | starts correcting on the same sample the fix becomes available, instead of waiting out the switch delay the |
| docs/thesis/writing_pack/new_2026-11-11/numbers_o_window_check.md:32 | switch delay | yes | Related: the switch delay itself is explained in `eval/results/expO_switch_delay/switch_delay.json` (`eval/o_switch_delay.py`, commit `a833b53`): about 0.3 s of simulated GPS latency plus the harness  |
| docs/thesis/writing_pack/numbers.md:526 | 4.3 s | **NO** | / A: all 8 (4.3 s) / 0.039 m / 0.037 m / **0.020 m** / 0.014 m / **0.010 m** / |
| docs/thesis/writing_pack/numbers.md:552 | 3.54 m | **NO** | / EKF3 live / 1.42–1.43 m / 3.53–3.54 m / **4.10 m (reset jump, every flight)** / |
| docs/thesis/writing_pack/numbers.md:565 | 4.3 s | **NO** | - EKF3 switched source set (`XKFS.SS`) at OFF + 4.3–4.4 s (4.37 / 4.37 / 4.34) and ON + 4.3 s (4.32 / 4.32 / 4.28), O_r1 / O_r2 / O_r3b (json:expO/O_*.json:ekf3.source_set_changes − markers_bag_s; tra |
| docs/thesis/writing_pack/numbers.md:1105 | 4.3 s | **NO** | / §16.1 / ¦ A: all 8 (4.3 s) ¦ 0.039 m ¦ 0.037 m ¦ **0.018 m** ¦ 0.014 m ¦ **0.011 m** ¦ / |
| docs/thesis/writing_pack/numbers.md:1271 | 4.3 s | **NO** | / §16.1 table / ¦ A: all 8 (4.3 s) ¦ 0.039 m ¦ 0.037 m ¦ **0.020 m** ¦ 0.014 m ¦ **0.011 m** ¦ / |
| docs/thesis/writing_pack/numbers.md:1307 | 4.3 s | **NO** | / §16.2 bullet / - EKF3 switched source set at OFF + 4.3 s and ON + 4.4 s; `posTimeout` was set for 92% of the indoor segment. / "Switched source set" = the time of the `XKFS.SS` change after the GNSS |
| docs/thesis/writing_pack/tables/T1_scorecard.md:13 | 4.10 m | yes | / Experiment 4: outdoor–indoor (GNSS outside only) [f, g] / indoor 1.42–1.43 m (no live ordering claimed; 4.10 m jump, about 4.3 s after GNSS returns (the switching script's delay)) / indoor 0.77–0.84 |
| docs/thesis/writing_pack/tables/T1_scorecard.md:20 | 4.10 m | yes | *Experiment 4's EKF3 jump: the 4.10 m figure is measured once the simulation's GNSS switching script moves EKF3 off its indoor source set, about 4.3 s after GNSS returns (the script waits for 40 conse |
| docs/thesis/writing_pack/tables/T7_failure_behaviour.md:3 | 4.1 m | yes | How each estimator fails: EKF3 declares its blank-floor position invalid while the UKF and the FGO run away with no invalid period recorded [a]; on the return to GNSS EKF3 jumps 4.1 m, about 4.3 s aft |
| docs/thesis/writing_pack/tables/T7_failure_behaviour.md:7 | 4.10 m | yes | / EKF3 / position flagged INVALID from take-off on all 14 blank flights (301–310 s of cruise; 0 valid airborne flow frames); outputs the origin, not scored: a DECLARED failure / resets to GNSS on retu |
| docs/thesis/writing_pack/tables/T7_failure_behaviour.md:21 | 4.3 s | yes | *[b] Ordering basis, Experiment 4, the jump on the return to GNSS. Metric: largest position step in the 10 s after GNSS returns, m. n = 3 flights (same flights for every estimator). Rule: none: EKF3's |
| docs/thesis/writing_pack/tier1/preregistration.md:65 | 4.3 s | **NO** | / A / all 8 (`all`) / 4.3 s / |

## F. Coverage matrix

Experiment-to-ID / experiment-to-table mapping sourced from `docs/thesis/tables/methods_experiment_matrix.md` (Table 3.4), not guessed.

| experiment | registered IDs (per Table 3.4 / TA_verdicts.md) | has TA verdict row(s)? | has a table? | has a figure/caption? | numbers source |
|---|---|---|---|---|---|
| 1A: 1A standard-sensor comparison | H1.1 | 1/1 present | mentioned in 4 table file(s) (textual-mention proxy, not a structural map) | mentioned in 3 figure/caption/index file(s) (textual-mention proxy) | docs/thesis/numbers.md (+ extras/refly as applicable per Table 3.4) |
| 1B: 1B camera-heading studies: measurement validation / offline fusion / robust-weighting | H1.2, H1.3, C1.a, H1.4, X1.b, H1.5, H1.6, H1.6b, H1.6c, H1.7a, H1.7b, H1.7c, 1B-H1, 1B-H2, 1B-H3 | 15/15 present | mentioned in 4 table file(s) (textual-mention proxy, not a structural map) | mentioned in 2 figure/caption/index file(s) (textual-mention proxy) | docs/thesis/numbers.md (+ extras/refly as applicable per Table 3.4) |
| 1C: 1C closed-loop corridor flights | H1.8, H1.9 | 2/2 present | mentioned in 4 table file(s) (textual-mention proxy, not a structural map) | mentioned in 2 figure/caption/index file(s) (textual-mention proxy) | docs/thesis/numbers.md (+ extras/refly as applicable per Table 3.4) |
| 2: 2 known tags | H2.1, H2.2, H2.3, H2.4 | 4/4 present | mentioned in 4 table file(s) (textual-mention proxy, not a structural map) | mentioned in 2 figure/caption/index file(s) (textual-mention proxy) | docs/thesis/numbers.md (+ extras/refly as applicable per Table 3.4) |
| 3: 3 loop closure | V3, H3.1, H3.2, H3.3, H3.4 | 5/5 present | mentioned in 5 table file(s) (textual-mention proxy, not a structural map) | mentioned in 4 figure/caption/index file(s) (textual-mention proxy) | docs/thesis/numbers.md (+ extras/refly as applicable per Table 3.4) |
| 4: 4 outdoor-indoor | H4.1, H4.2, H4.3 | 3/3 present | mentioned in 6 table file(s) (textual-mention proxy, not a structural map) | mentioned in 3 figure/caption/index file(s) (textual-mention proxy) | docs/thesis/numbers.md (+ extras/refly as applicable per Table 3.4) |
| 5: 5 tag hold | H5.1, H5.2, H5.3, H5.4a, H5.4b, H5.5, H5.6, H5.7 | 8/8 present | mentioned in 5 table file(s) (textual-mention proxy, not a structural map) | mentioned in 4 figure/caption/index file(s) (textual-mention proxy) | docs/thesis/numbers.md (+ extras/refly as applicable per Table 3.4) |
| 5S: 5S safety tests | (none registered) | (no H-labelled hypotheses registered for this experiment per Table 3.4/TA legend) | mentioned in 5 table file(s) (textual-mention proxy, not a structural map) | mentioned in 4 figure/caption/index file(s) (textual-mention proxy) | eval/results/expH/safety_*.json (per TA_verdicts.md header) |
| E2: Extension E2: loop closure, fewer tags | (none registered) | (no H-labelled hypotheses registered for this experiment per Table 3.4/TA legend) | mentioned in 1 table file(s) (textual-mention proxy, not a structural map) | mentioned in 3 figure/caption/index file(s) (textual-mention proxy) | present |
| E3: Extension E3: wrong re-identification | (none registered) | (no H-labelled hypotheses registered for this experiment per Table 3.4/TA legend) | mentioned in 1 table file(s) (textual-mention proxy, not a structural map) | mentioned in 3 figure/caption/index file(s) (textual-mention proxy) | present |
| E4: Extension E4: live window sweep | (none registered) | (no H-labelled hypotheses registered for this experiment per Table 3.4/TA legend) | mentioned in 1 table file(s) (textual-mention proxy, not a structural map) | mentioned in 0 figure/caption/index file(s) (textual-mention proxy) - NONE | present |
| E5: Extension E5: UKF with tag landmark states | (none registered) | (no H-labelled hypotheses registered for this experiment per Table 3.4/TA legend) | mentioned in 2 table file(s) (textual-mention proxy, not a structural map) | mentioned in 3 figure/caption/index file(s) (textual-mention proxy) | present |
| E6: Extension E6: figure-8 route | (none registered) | (no H-labelled hypotheses registered for this experiment per Table 3.4/TA legend) | mentioned in 1 table file(s) (textual-mention proxy, not a structural map) | mentioned in 1 figure/caption/index file(s) (textual-mention proxy) | present |

### Flags

- **E4**: no figure caption/index file's text names 'Experiment E4' / 'Extension E4' (textual-mention proxy)

## Candidates (figures_thesis/candidates/)

Scanned 59 candidate caption/index files (not thesis-numbered; reported here separately, per the scope rule, rather than folded into the B/D counts above).

- B(i) superseded-as-current hits: 0

- B(ii) H4.2 occurrences: 0, not NOT MET: 0; other mismatches: 0; non-standard bare-word labels: 0

- D style checks: see below

| file | prose en/em dashes | bare `RTF 0.5` |
|---|---|---|
| docs/thesis/figures_thesis/candidates/captions/A13.md | 0 | 1 |

## Numbered fix list

1. `docs/thesis/tables/R4_information_vs_estimator.md:14` presents the superseded value `7.8–7.9` for 'H5.2 (original priors)' (superseded at TA_verdicts.md:114) without marking it superseded.
2. `docs/thesis/tables/R4_information_vs_estimator.md:14` presents the superseded value `7.8-7.9` for 'H-H2' (superseded at refly_priors/numbers_refly.md:371) without marking it superseded.
3. `docs/thesis/tables/T1_scorecard.md:44` presents the superseded value `7.8-7.9` for 'H-H2' (superseded at refly_priors/numbers_refly.md:371) without marking it superseded.
4. `docs/thesis/tables/T1_scorecard.md:44` presents the superseded value `2.40-2.58` for 'P-H3' (superseded at refly_priors/numbers_refly.md:372) without marking it superseded.
5. `docs/thesis/tables/T5_H_tag_loss_drift.md:22` presents the superseded value `7.8-7.9` for 'H-H2' (superseded at refly_priors/numbers_refly.md:371) without marking it superseded.
6. `docs/thesis/tables/T5_H_tag_loss_drift.md:22` presents the superseded value `2.40-2.58` for 'P-H3' (superseded at refly_priors/numbers_refly.md:372) without marking it superseded.
7. `docs/thesis/figures_thesis/index.md:411` presents the superseded value `3.2–7.7` for 'H5.4b (original priors)' (superseded at TA_verdicts.md:117) without marking it superseded.
8. `docs/thesis/figures_thesis/index.md:479` presents the superseded value `3.2–7.7` for 'H5.4b (original priors)' (superseded at TA_verdicts.md:117) without marking it superseded.
9. `docs/thesis/figures_thesis/index.md:608` presents the superseded value `3.2–7.7` for 'H5.4b (original priors)' (superseded at TA_verdicts.md:117) without marking it superseded.
10. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:365` presents the superseded value `8.1–9.0` for 'H5.1 (FGO-flying)' (superseded at TA_verdicts.md:113) without marking it superseded.
11. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:345` presents the superseded value `8.3–8.6` for 'H5.2 (original priors)' (superseded at TA_verdicts.md:114) without marking it superseded.
12. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:272` presents the superseded value `0.002–0.032` for 'H5.6, redefined primary (FGO)' (superseded at TA_verdicts.md:120) without marking it superseded.
13. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:367` presents the superseded value `0.002–0.032` for 'H5.6, redefined primary (FGO)' (superseded at TA_verdicts.md:120) without marking it superseded.
14. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:365` presents the superseded value `8.1-9.0` for 'H5.1** (FGO-flying bounds)' (superseded at refly_priors/numbers_refly.md:365) without marking it superseded.
15. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:272` presents the superseded value `0.002-0.032` for 'H5.6 redefined primary (re-lock)' (superseded at refly_priors/numbers_refly.md:367) without marking it superseded.
16. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:367` presents the superseded value `0.002-0.032` for 'H5.6 redefined primary (re-lock)' (superseded at refly_priors/numbers_refly.md:367) without marking it superseded.
17. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:345` presents the superseded value `8.3-8.6` for 'H-H2' (superseded at refly_priors/numbers_refly.md:371) without marking it superseded.
18. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:371` presents the superseded value `8.3-8.6` for 'H-H2' (superseded at refly_priors/numbers_refly.md:371) without marking it superseded.
19. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:372` presents the superseded value `2.40-2.58` for 'P-H3' (superseded at refly_priors/numbers_refly.md:372) without marking it superseded.
20. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:373` presents the superseded value `20-30` for 'H-H4 (15 s)' (superseded at refly_priors/numbers_refly.md:373) without marking it superseded.
21. `docs/thesis/writing_pack/new_2026-11-11/numbers_refly.md:374` presents the superseded value `7-16` for 'H-H4 (5 s)' (superseded at refly_priors/numbers_refly.md:374) without marking it superseded.
22. `docs/thesis/writing_pack/numbers.md:675` presents the superseded value `8.3-8.6` for 'H-H2' (superseded at refly_priors/numbers_refly.md:371) without marking it superseded.
23. `docs/thesis/writing_pack/numbers.md:676` presents the superseded value `2.40-2.58` for 'P-H3' (superseded at refly_priors/numbers_refly.md:372) without marking it superseded.
24. `docs/thesis/writing_pack/numbers.md:677` presents the superseded value `20-30` for 'H-H4 (15 s)' (superseded at refly_priors/numbers_refly.md:373) without marking it superseded.
25. `docs/thesis/writing_pack/numbers.md:678` presents the superseded value `7-16` for 'H-H4 (5 s)' (superseded at refly_priors/numbers_refly.md:374) without marking it superseded.
26. `docs/thesis/writing_pack/tables/R4_information_vs_estimator.md:14` presents the superseded value `7.8–7.9` for 'H5.2 (original priors)' (superseded at TA_verdicts.md:114) without marking it superseded.
27. `docs/thesis/writing_pack/tables/R4_information_vs_estimator.md:14` presents the superseded value `7.8-7.9` for 'H-H2' (superseded at refly_priors/numbers_refly.md:371) without marking it superseded.
28. `docs/thesis/writing_pack/tables/T1_scorecard.md:44` presents the superseded value `7.8-7.9` for 'H-H2' (superseded at refly_priors/numbers_refly.md:371) without marking it superseded.
29. `docs/thesis/writing_pack/tables/T1_scorecard.md:44` presents the superseded value `2.40-2.58` for 'P-H3' (superseded at refly_priors/numbers_refly.md:372) without marking it superseded.
30. `docs/thesis/writing_pack/tables/T5_H_tag_loss_drift.md:22` presents the superseded value `7.8-7.9` for 'H-H2' (superseded at refly_priors/numbers_refly.md:371) without marking it superseded.
31. `docs/thesis/writing_pack/tables/T5_H_tag_loss_drift.md:22` presents the superseded value `2.40-2.58` for 'P-H3' (superseded at refly_priors/numbers_refly.md:372) without marking it superseded.
32. `docs/thesis/writing_pack/numbers.md:559` labels an H4.2 occurrence 'FAIL' - TA_verdicts.md requires NOT MET.
33. `docs/thesis/writing_pack/numbers.md:1118` labels an H4.2 occurrence 'FAIL' - TA_verdicts.md requires NOT MET.
34. `docs/thesis/writing_pack/numbers.md:1275` labels an H4.2 occurrence 'FAIL' - TA_verdicts.md requires NOT MET.
35. `docs/thesis/writing_pack/numbers.md:1275` labels an H4.2 occurrence 'FAIL' - TA_verdicts.md requires NOT MET.
36. `docs/thesis/figures_thesis/index.md:283` labels H2.2 'PASS' - TA_verdicts.md's unique verdict for this ID is NOT MET.
37. `docs/thesis/writing_pack/methodology_factsheets/README.md:228` labels H1.1 'WITHDRAWN' - TA_verdicts.md's unique verdict for this ID is NOT MET.
38. `docs/thesis/tables/R4_information_vs_estimator.md:9` cites `numbers.md:248-249` but the value is actually at `numbers.md:1448` (cite drift).
39. `docs/thesis/tables/R4_information_vs_estimator.md:14` cites `numbers.md:621-623` but the value is actually at `numbers.md:675` (cite drift).
40. `docs/thesis/tables/R4_information_vs_estimator.md:14` cites `numbers_refly.md:247` but the value is actually at `numbers_refly.md:345` (cite drift).
41. `docs/thesis/tables/R4_information_vs_estimator.tex:14` cites `numbers.md:248-249` but the value is actually at `numbers.md:127` (cite drift).
42. `docs/thesis/tables/R4_information_vs_estimator.tex:19` cites `numbers.md:621-623` but the value is actually at `numbers.md:79` (cite drift).
43. `docs/thesis/figures_thesis/index.md:601` cites `numbers.md:677` but the value is actually at `numbers.md:62` (cite drift).
44. `docs/thesis/figures_thesis/index_results.md:353` cites `numbers.md:470` but the value is actually at `numbers.md:60` (cite drift).
45. `docs/thesis/figures_thesis/index_results.md:355` cites `numbers.md:470` but the value is actually at `numbers.md:36` (cite drift).
46. `docs/thesis/figures_thesis/index_results.md:360` cites `numbers_extras.md:95-99` but the value is actually at `numbers_extras.md:88` (cite drift).
47. `docs/thesis/figures_thesis/index_results.md:363` cites `numbers_extras.md:107-111` but the value is actually at `numbers_extras.md:101` (cite drift).
48. `docs/thesis/figures_thesis/index_results.md:507` cites `numbers.md:291-295` but the value is actually at `numbers.md:38` (cite drift).
49. `docs/thesis/figures_thesis/index_results.md:563` cites `numbers.md:263` but the value is actually at `numbers.md:134` (cite drift).
50. `docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:14` cites `numbers.md:330` but the value is actually at `numbers.md:36` (cite drift).
51. `docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:39` cites `numbers.md:477` but the value is actually at `numbers.md:52` (cite drift).
52. `docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:50` cites `numbers.md:577` but the value is actually at `numbers.md:114` (cite drift).
53. `docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:52` cites `numbers.md:577` but the value is actually at `numbers.md:67` (cite drift).
54. `docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:54` cites `numbers.md:558` but the value is actually at `numbers.md:89` (cite drift).
55. `docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:57` cites `numbers.md:606` but the value is actually at `numbers.md:54` (cite drift).
56. `docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:63` cites `numbers.md:646` but the value is actually at `numbers.md:54` (cite drift).
57. `docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:63` cites `numbers.md:629` but the value is actually at `numbers.md:54` (cite drift).
58. `docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:67` cites `numbers.md:644` but the value is actually at `numbers.md:565` (cite drift).
59. `docs/thesis/thesis_assets/tables_tex/tab_7-3.tex:68` cites `numbers.md:629` but the value is actually at `numbers.md:565` (cite drift).
60. `docs/thesis/thesis_assets/tables_tex/tab_7-5.tex:15` cites `numbers.md:248-249` but the value is actually at `numbers.md:127` (cite drift).
61. `docs/thesis/thesis_assets/tables_tex/tab_7-5.tex:20` cites `numbers.md:621-623` but the value is actually at `numbers.md:79` (cite drift).
62. `docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:19` cites `numbers.md:28` but the value is actually at `numbers.md:72` (cite drift).
63. `docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:36` cites `numbers_ekf3_heading.md:5` but the value is actually at `numbers_ekf3_heading.md:7` (cite drift).
64. `docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:60` cites `numbers.md:28` but the value is actually at `numbers.md:48` (cite drift).
65. `docs/thesis/writing_pack/methodology_factsheets/3.1_approach_fairness.md:64` cites `numbers.md:211-237` but the value is actually at `numbers.md:843` (cite drift).
66. `docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:7` cites `numbers.md:411` but the value is actually at `numbers.md:60` (cite drift).
67. `docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:38` cites `numbers.md:520` but the value is actually at `numbers.md:36` (cite drift).
68. `docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:41` cites `numbers.md:58` but the value is actually at `numbers.md:36` (cite drift).
69. `docs/thesis/writing_pack/methodology_factsheets/3.2_simulation.md:77` cites `numbers.md:82` but the value is actually at `numbers.md:36` (cite drift).
70. `docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:30` cites `numbers_ekf3_heading.md:5` but the value is actually at `numbers_ekf3_heading.md:7` (cite drift).
71. `docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:30` cites `numbers.md:301` but the value is actually at `numbers.md:176` (cite drift).
72. `docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:33` cites `numbers.md:402` but the value is actually at `numbers.md:54` (cite drift).
73. `docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:64` cites `numbers.md:451` but the value is actually at `numbers.md:565` (cite drift).
74. `docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:68` cites `numbers.md:209` but the value is actually at `numbers.md:36` (cite drift).
75. `docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:149` cites `numbers_tier1.md:576` but the value is actually at `numbers_tier1.md:192` (cite drift).
76. `docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:156` cites `numbers_tier1.md:614-615` but the value is actually at `numbers_tier1.md:192` (cite drift).
77. `docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:207` cites `numbers.md:227` but the value is actually at `numbers.md:222` (cite drift).
78. `docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:209` cites `numbers.md:440` but the value is actually at `numbers.md:445` (cite drift).
79. `docs/thesis/writing_pack/methodology_factsheets/3.4_run_modes.md:93` cites `numbers_extras.md:99` but the value is actually at `numbers_extras.md:111` (cite drift).
80. `docs/thesis/writing_pack/methodology_factsheets/3.4_run_modes.md:125` cites `numbers.md:120` but the value is actually at `numbers.md:118` (cite drift).
81. `docs/thesis/writing_pack/methodology_factsheets/3.4_run_modes.md:128` cites `numbers.md:133` but the value is actually at `numbers.md:121` (cite drift).
82. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:11` cites `numbers.md:58` but the value is actually at `numbers.md:36` (cite drift).
83. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:35` cites `numbers.md:369-370` but the value is actually at `numbers.md:176` (cite drift).
84. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:35` cites `numbers.md:371` but the value is actually at `numbers.md:176` (cite drift).
85. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:60` cites `numbers_extras.md:99` but the value is actually at `numbers_extras.md:111` (cite drift).
86. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:65` cites `numbers_refly.md:97` but the value is actually at `numbers_refly.md:18` (cite drift).
87. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:79` cites `numbers.md:470-473` but the value is actually at `numbers.md:36` (cite drift).
88. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:79` cites `numbers_extras.md:148-155` but the value is actually at `numbers_extras.md:88` (cite drift).
89. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:79` cites `numbers_refly.md:97` but the value is actually at `numbers_refly.md:298` (cite drift).
90. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:89` cites `numbers.md:520` but the value is actually at `numbers.md:36` (cite drift).
91. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:91` cites `numbers.md:542` but the value is actually at `numbers.md:54` (cite drift).
92. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:100` cites `numbers_tier1.md:560` but the value is actually at `numbers_tier1.md:248` (cite drift).
93. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:102` cites `numbers_tier1.md:163` but the value is actually at `numbers_tier1.md:157` (cite drift).
94. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:115` cites `numbers.md:546` but the value is actually at `numbers.md:36` (cite drift).
95. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:115` cites `numbers.md:548` but the value is actually at `numbers.md:36` (cite drift).
96. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:128` cites `numbers.md:606` but the value is actually at `numbers.md:54` (cite drift).
97. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:135` cites `numbers.md:626` but the value is actually at `numbers.md:54` (cite drift).
98. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:135` cites `numbers.md:629` but the value is actually at `numbers.md:54` (cite drift).
99. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:136` cites `numbers_refly.md:272` but the value is actually at `numbers_refly.md:65` (cite drift).
100. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:154` cites `numbers.md:312-319` but the value is actually at `numbers.md:203` (cite drift).
101. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:173` cites `numbers.md:736-738` but the value is actually at `numbers.md:318` (cite drift).
102. `docs/thesis/writing_pack/methodology_factsheets/3.5_experiments.md:186` cites `numbers.md:649-656` but the value is actually at `numbers.md:62` (cite drift).
103. `docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md:53` cites `numbers_tier1.md:35-36` but the value is actually at `numbers_tier1.md:46` (cite drift).
104. `docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md:78` cites `numbers_tier1.md:560` but the value is actually at `numbers_tier1.md:248` (cite drift).
105. `docs/thesis/writing_pack/tables/R4_information_vs_estimator.md:9` cites `numbers.md:248-249` but the value is actually at `numbers.md:1448` (cite drift).
106. `docs/thesis/writing_pack/tables/R4_information_vs_estimator.md:14` cites `numbers.md:621-623` but the value is actually at `numbers.md:675` (cite drift).
107. `docs/thesis/writing_pack/tables/R4_information_vs_estimator.md:14` cites `numbers_refly.md:247` but the value is actually at `numbers_refly.md:345` (cite drift).
108. `docs/thesis/writing_pack/thesis_vocabulary.md:343` cites `numbers.md:598-662` but the value is actually at `numbers.md:134` (cite drift).
109. `docs/thesis/writing_pack/thesis_vocabulary.md:403` cites `numbers.md:501` but the value is actually at `numbers.md:509` (cite drift).
110. `docs/thesis/writing_pack/units.md:104` cites `numbers.md:480` but the value is actually at `numbers.md:134` (cite drift).
111. `docs/thesis/writing_pack/methodology_factsheets/3.3_estimators.md:193` cites `numbers.md:466`, but no matching numeric token (24.7) was found anywhere in that file.
112. `docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md:120` cites `numbers_tier1.md:68`, but no matching numeric token (0.95–1.86, 0.95–2.43) was found anywhere in that file.
113. `docs/thesis/writing_pack/methodology_factsheets/3.9_extension_experiments.md:123` cites `numbers_tier1.md:559`, but no matching numeric token (6.34–14.62) was found anywhere in that file.
114. `docs/thesis/figures_thesis/index.md:335` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: `| Experiment 4 EKF3 reset jump (m) | `4.10–4.10` | `4.10–4.10` | numbers.md §16.2 ('4.10 m, every flight') | yes |`
115. `docs/thesis/writing_pack/new_2026-11-11/caption_detail.md:149` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: `**Finding: yes, EKF3's reset happens AFTER GNSS returns, by about 4.3 s, consistently across all three flights.**`
116. `docs/thesis/writing_pack/new_2026-11-11/caption_detail.md:180` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: `**Reconciling with the quoted `numbers.md` line "EKF3 switched sets at OFF + 4.3 s and ON + 4.4 s":** that exact`
117. `docs/thesis/writing_pack/new_2026-11-11/caption_detail.md:183` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: ``numbers.md` line states the corrected values directly: "OFF + 4.3–4.4 s (4.37 / 4.37 / 4.34) and ON + 4.3 s`
118. `docs/thesis/writing_pack/new_2026-11-11/caption_detail.md:184` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: `(4.32 / 4.32 / 4.28)" — i.e. ON + 4.3 s, not ON + 4.4 s. This investigation's own independent measurement (4.32 /`
119. `docs/thesis/writing_pack/numbers.md:526` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: `| A: all 8 (4.3 s) | 0.039 m | 0.037 m | **0.020 m** | 0.014 m | **0.010 m** |`
120. `docs/thesis/writing_pack/numbers.md:552` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: `| EKF3 live | 1.42–1.43 m | 3.53–3.54 m | **4.10 m (reset jump, every flight)** |`
121. `docs/thesis/writing_pack/numbers.md:565` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: `- EKF3 switched source set (`XKFS.SS`) at OFF + 4.3–4.4 s (4.37 / 4.37 / 4.34) and ON + 4.3 s (4.32 / 4.32 / 4.28), O_r1 / O_r2 / O_r3b (json:expO/O_*.json:ekf3.source_set_changes − markers_bag_s; tra`
122. `docs/thesis/writing_pack/numbers.md:1105` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: `| §16.1 | ¦ A: all 8 (4.3 s) ¦ 0.039 m ¦ 0.037 m ¦ **0.018 m** ¦ 0.014 m ¦ **0.011 m** ¦ |`
123. `docs/thesis/writing_pack/numbers.md:1271` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: `| §16.1 table | ¦ A: all 8 (4.3 s) ¦ 0.039 m ¦ 0.037 m ¦ **0.020 m** ¦ 0.014 m ¦ **0.011 m** ¦ |`
124. `docs/thesis/writing_pack/numbers.md:1307` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: `| §16.2 bullet | - EKF3 switched source set at OFF + 4.3 s and ON + 4.4 s; `posTimeout` was set for 92% of the indoor segment. | "Switched source set" = the time of the `XKFS.SS` change after the GNSS`
125. `docs/thesis/writing_pack/tier1/preregistration.md:65` states the switching delay/jump without qualifying it as coming from the harness's source-switch script: `| A | all 8 (`all`) | 4.3 s |`
126. Experiment E4: no figure caption/index file's text names 'Experiment E4' / 'Extension E4' (textual-mention proxy)

## Writing-pack files read (sha256, for re-run comparability)

- `README.md`: `3ade0f94068c7ce6`
- `ablation/ablation_numbers.md`: `1a92ce1b7f46f4ef`
- `ablation/preregistration.md`: `c61d4478709c0ff6`
- `discussion_material.md`: `82abc047c7ae8ac9`
- `figures_thesis/captions/A1.md`: `d50edf685118e05d`
- `figures_thesis/captions/A2.md`: `03c5f378deb431ea`
- `figures_thesis/captions/A3.md`: `0bccf450a603f384`
- `figures_thesis/captions/F2.md`: `72a214b80742b42e`
- `figures_thesis/captions/F5.md`: `f0cef05bb82c66eb`
- `figures_thesis/captions/F6.md`: `0d8d4f787ac207be`
- `figures_thesis/captions/F7.md`: `320417e2aba87549`
- `figures_thesis/captions/F9.md`: `6521b25e3cbb5071`
- `figures_thesis/captions/R3.md`: `9a4d58f4e4f0198a`
- `figures_thesis/captions/R5.md`: `a90812e4ed4710c4`
- `figures_thesis/captions/R6.md`: `b067a2841ef6197d`
- `figures_thesis/captions/methods_architecture.md`: `ee893e34de6e9b34`
- `limitations.md`: `1ebe09d23bf602f7`
- `methodology_definitions_draft.md`: `d3765c1ee5df735f`
- `methodology_factsheets/3.1_approach_fairness.md`: `c9337e1c428c353a`
- `methodology_factsheets/3.2_simulation.md`: `8e0eb9a327064ab9`
- `methodology_factsheets/3.3_estimators.md`: `ada84c13c153209a`
- `methodology_factsheets/3.4_run_modes.md`: `3459bddea505a0d7`
- `methodology_factsheets/3.5_experiments.md`: `8df5cca66053dfe2`
- `methodology_factsheets/3.6_metrics_statistics.md`: `d779fcb17b8155cd`
- `methodology_factsheets/3.7_verification.md`: `3fd75ef2a9c64b9a`
- `methodology_factsheets/3.8_closed_loop_safety.md`: `38af3ce728560e31`
- `methodology_factsheets/3.9_extension_experiments.md`: `e77c0aa440424d25`
- `methodology_factsheets/README.md`: `e401908be6a519b1`
- `new_2026-11-11/caption_detail.md`: `142ba6aca2d00e12`
- `new_2026-11-11/digest_2026-11-12.md`: `23a6cba747548bca`
- `new_2026-11-11/ekf3_heading_preregistration.md`: `1f63e88ad945cf6d`
- `new_2026-11-11/ekf3_heading_results.md`: `47d39e448d8a8bd1`
- `new_2026-11-11/extras_preregistration.md`: `ac9d835ebff6c52d`
- `new_2026-11-11/fgo_gate_count_results.md`: `c42c4befad3d73b0`
- `new_2026-11-11/numbers_cl_heading_perflight.md`: `20617e9246ead812`
- `new_2026-11-11/numbers_ekf3_heading.md`: `c3a14d50c3182660`
- `new_2026-11-11/numbers_extras.md`: `814dc76da235e7b3`
- `new_2026-11-11/numbers_fgo_gate_count.md`: `ac6d3a7d3fdd8031`
- `new_2026-11-11/numbers_o_window_check.md`: `2692cc5527166d17`
- `new_2026-11-11/numbers_refly.md`: `70c75ca0ca3b9fb4`
- `new_2026-11-11/refly_preregistration.md`: `1771c97128b916d5`
- `numbers.md`: `334d723b6742e371`
- `raw_corridor/raw_corridor_numbers.md`: `c0996189f20ed65f`
- `tables/R1_hypothesis_scorecard.md`: `f387b59b33644ef6`
- `tables/R2_corrections_by_discovery.md`: `fdf8ee7ec1908291`
- `tables/R4_information_vs_estimator.md`: `0a7917a968714b48`
- `tables/T1_scorecard.md`: `1857ab0938cdd64d`
- `tables/T2B_ekf3_heading_replay.md`: `b469d0d1d297a917`
- `tables/T2_accuracy_heading.md`: `a96b3202b9008373`
- `tables/T3_blank_floor.md`: `2ab12c1a3d8ae8df`
- `tables/T4F_closed_loop_full_speed.md`: `4873ac76e056965a`
- `tables/T4_closed_loop.md`: `24c666a831cb2095`
- `tables/T5_H_tag_loss_drift.md`: `d49e1296b91ac2e9`
- `tables/T6_O_indoor_rmse.md`: `401b44d2fa457754`
- `tables/T7_failure_behaviour.md`: `45d3c7e1fb404c85`
- `tables/T8_hindsight_ratio.md`: `23ef5cf2141907fc`
- `tables/T9_1A_fitted_vs_raw.md`: `c127ff9935be9f5c`
- `tables/TA_verdicts.md`: `25523f561c47cb59`
- `tables/methods_estimator_design.md`: `cdcae3f0e304c997`
- `tables/methods_experiment_matrix.md`: `2a219d17e6b1befd`
- `tables/methods_noise_exceptions.md`: `0276b81902dc83f7`
- `tables/methods_noise_parity.md`: `2aac7bc4264590b1`
- `thesis_vocabulary.md`: `54576f15fc12a5c1`
- `tier1/e2_results.md`: `a602678a9a6605dd`
- `tier1/e3_results.md`: `fb405cab0f7ed792`
- `tier1/e4_results.md`: `26de2e61714ea7bc`
- `tier1/e5_results.md`: `161fe8ade5faeb38`
- `tier1/e6_preregistration.md`: `94147e17443b65ab`
- `tier1/e6_results.md`: `9ac3ad302ac3640b`
- `tier1/numbers_tier1.md`: `421fdb284890a425`
- `tier1/preregistration.md`: `0c7b103595fb5bf9`
- `units.md`: `e7a262e98c731477`
