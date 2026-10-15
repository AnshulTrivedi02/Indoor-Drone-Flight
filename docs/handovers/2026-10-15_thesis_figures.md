# Handover: reader-facing thesis figure set (2026-10-15)

**Stage:** build a reader-facing figure set from the FROZEN results. Plotting only: no number was recomputed, re-run or
changed. `eval/figs_final_pack.py`, `docs/thesis/final_results_pack.pdf`, METHODOLOGY.md, numbers.md and every result
file are untouched (the `git diff` of these is empty).

**Outputs**
- `eval/figs_thesis.py`. Run it with `/home/makerspace/venv-evo/bin/python eval/figs_thesis.py` (about 2 min). Its
  loaders (`sim_path`, `log_yaw`, `cl_meta`, `check`, the path panels) are COPIED from `figs_final_pack.py`, which runs
  everything at module level, so importing it would regenerate the frozen pack. `log_yaw` gained an FGO branch
  (`XFGO.Yaw`, the source `closed_loop_score.py` uses for `--est fgo`).
- `docs/thesis/figures_thesis/`: F1–F8 and the appendix tables A1–A3 (each as `.pdf` and `.png`; A2 and A3 run to 2
  pages), `thesis_figures_combined.pdf` (14 pages, for the supervisor), and `index.md` (palette, captions, sources and
  the full check tables).
- **Palette (Okabe–Ito):** EKF3 `#0072B2` circle, UKF `#009E73` triangle, FGO `#D55E00` square, truth/reference grey
  `#999999`. Solid lines and filled marks = live; dashed lines and open marks = hindsight. No log axis anywhere.

## Per figure

| fig | content and sources | checks | log-scale handling | caveats |
|---|---|---|---|---|
| F1 scorecard | 3 estimators × 8 experiments; numbers.md §6.1, §6.2, §6.6, §15, §16, §17.2 and the claims table; JSONs as in the pack | 16/16 | none needed | see "Scorecard categories" below |
| F2 heading stops drift (pack F01 + F08 + F02) | half-speed paths (dataflash SIM) for EKF3 (`cl_a_tex_half`, `cl_bcpp_*_half`), UKF v2 (`*_half_v2`) and FGO v3 (`*_half_v3`); heading error from XKF1 / XUKO / XFGO on ONE shared y-scale; B2/B3 from `closed_loop_*.json` | 8/8 | none needed | no-heading curves are cut 3 s before wall contact (impact transient). Older builds are in A1 |
| F3 accuracy without (m) / with (cm) heading (pack F03 + F04 + F05) | dsn_tex r1–r9 and the 6 camera bags without heading; UKF/FGO heading arms in cm; EKF3 slot says "no offline heading arm"; the checkerboard plain-wall columns are shaded with "no heading benefit claimed" | 9/9 | none needed | F05 (Phase 5 decomposition) appears as caption numbers only, and is JSON-only (numbers.md §6.3 "NOT RESTATED") |
| F4 blank floor (pack F06) | `blank_behaviour.json`, +10/+30/+60 s, 11 flights per estimator; the EKF3 box gives the reason (invalid for the whole cruise, 0 valid airborne flow frames, origin output not scored) | 6/6 | **km-scale runaway next to metres: the axis is CUT at +60 s; the end-of-cruise values (UKF 29–40 km, FGO 22–41 km, †) are annotated arrows** | — |
| F5 T (pack F09 + F10) | x = "8 / 4 / 2 tags / 1 tag" with the median gap; RMSE in cm, linear; live solid for all three, hindsight dashed for the RTS-UKF and the FGO batch; the H-T1/P-T2 gains are given as text under the axis | 8/8 | none needed (the pack's log axis is removed) | condition B = the 4 corner tags (checked in `T_B_r1.json` laps_ids). Two last-digit rounding matches (A FGO batch 0.010 against 0.011; C FGO live 0.054 against 0.053), accepted as in the pack |
| F6 O (pack F11) | O_r1 time series (TUMs, XKF1 via the `/imu/time_ref` clock map) and 3-flight indoor RMSE on a shared y-axis; lines mark the far end (60 s) and the reverse (63 s) | 9/9 | none needed | the indoor sensor set is in the caption; H-O2 ratio 1.71 against numbers.md 1.72 is a last-digit rounding match |
| F7 L (pack F12) | two panels (with / without loop closure) on ONE shared linear cm axis; FGO colour only (one estimator) | 5/5 | none needed (pack log axis removed) | nolc live 0.263 against numbers.md 0.262: last-digit rounding |
| F8 H (pack F14) | FLYING estimators only, grouped by loss duration: EKF3 S1 + S1 far, UKF S2v2, FGO S3v2; effective drift, mm | 6/6 | **bands up to 400 mm next to drifts ≤ 31 mm: linear axis clipped at 60 mm; the in-range 50 mm bands are drawn as lines, and the off-scale bands as arrows labelled with their value** | effective vs end-of-loss drift max \|Δ\| = 5.1 mm (S2v2 r1, move loss), against numbers.md "≤ 5 mm": a match at printed precision |
| A1 closed loop, all builds (pack F15a) | `closed_loop_*.json`: EKF3 full (Python/C++), half; UKF v1 full/half, v2; FGO original, robust, v2 (ablation), v3 | 8/8 | table | — |
| A2 H sets + safety, all runs (pack F15b) | H sets S1, S1 far, S2/S2v2, S3/S3v2; every safety run incl. UKF v3 and FGO v4, as-worded verdicts | 11/11 | table | see "Values not in numbers.md" |
| A3 F1, L cost, build ablations (pack F07, F13) | `f1_test.json`; `stats.json`; the ablation rows: UKF v1→v2, FGO v2→v3(→v4), and the flown-FGO OLD-priors note | 8/8 | table (F13 values given linearly as text) | — |

**Total: 94/94 checks match** (6 of them at last-digit rounding, listed in `index.md`).

## Scorecard categories (F1)

The brief's best / tied / failed did not fit every cell, so three neutral states were added (all defined on the
figure):
- **BEHIND:** UKF with heading (C0: the FGO is lower on 6/6, claim 7), and EKF3 in O (H-O2 FAIL: the live errors are
  not similar, and EKF3 is the largest in every flight, 1.71–1.84× the smallest).
- **PASSED:** the FGO in L (an FGO-only capability; H-L1 to P-L4 PASS 3/3).
- **N/A:** EKF3 with heading offline (EKF3 ruling 2026-09-29: no offline heading arm), and EKF3 and the UKF in L.

**TIED, because no ordering is claimed:**
- standard sensors (claim 2 confirmatory "no ordering claimed"; the UKF median is descriptive, claim 1b);
- T live (ruling 7);
- H (all bands PASS; the comparative criteria FAIL as adjudicated and the same on S2v2/S3v2, PENDING a ruling);
- the closed loop (every half-speed set passes 3/3).

**FAILED:** every estimator on the blank floor (claim 10).

**BEST:** only the FGO with heading (C0).

No cell restates a WITHDRAWN claim.

## O design check (answers)

- **Heading source or tags indoors: NONE.**
  - The forward-camera heading walls were descoped (METHODOLOGY "Experiment O: pre-registration").
  - `sim/worlds/outdoor_indoor.sdf` includes no tag models. The drone is `iris_with_ardupilot`: downward camera, no
    forward camera.
  - The O_r1 bag has no `/tags/*` topic (a check in F6).
  - EKF3's indoor source set 2 has `YAW 0`. Its GSF yaw (set 1) works only outdoors on GNSS.
  - The UKF/FGO yaw cap is a self-referential pseudo-yaw, not a heading sensor.
- **Indoor sensor set (all three estimators):** IMU (accelerometer and gyro), downward optical flow and the downward
  LiDAR rangefinder. There is no GNSS (switched off at the entrance), no compass, no forward camera and no tags.
- **Route** (`fly_trial.py outback()`, `OUTBACK=15,1.5,50,0.5,20`; times from `O_r1` `markers_bag_s`):
  1. A 15 m yaw-alignment run outdoors at 1.5 m/s.
  2. North at 0.5 m/s. GNSS goes OFF at the entrance (y = 20 m), 40.0 s into the OUT leg.
  3. The vehicle reaches the far end (y = 50 m, 30 m inside) **about 60 s after OFF** and holds for 3 s.
  4. It then **flies back in REVERSE at the same heading (no yaw turn)**, from 63.0 s after OFF.
  5. It re-crosses the entrance at GNSS ON, 123 s after OFF.
- **So: yes, it turns back at about 60 s, but 30 m inside, not past the entry point.** It passes the entry point again
  only at about 123 s, when GNSS returns. F6 marks 60 s and 63 s.

## Values not in numbers.md (flagged; not edited)

- **The S1-far EKF3 drifts** (3 of F8's 6 EKF3 flights) appear in METHODOLOGY only. They are not cross-checked.
- **The Phase 5 decomposition** (F3 caption) is JSON-only.
- **The safety re-tests** `H_safety_ukf_a_v3`, `H_safety_ukf_b_v3` (S-A2 5.69 s, FAILED AS WORDED) and
  `H_safety_fgo_{a,b}_v4` (corrected node 4c07374b, NEW priors; 0.60 s / 1.45 m and 0.62 s / 0.21 m, ALL PASS) are in
  METHODOLOGY only. **numbers.md §15 still lists v2/v3 as the final runs.** The v3/v4 values were checked against the
  METHODOLOGY text.
- **The first `H_safety_ukf_a` and `H_safety_fgo_b` score files also show S-A4 FAIL.** numbers.md cites only S-A2/S-A3
  for those runs. A2 shows the file flags.
- **The first `H_safety_ukf_a` run has an S-A2 bound of 0.10 s** in its score file (0.75 s in the later runs). It is
  shown as recorded.

## Not done / open

- The pack's full-speed closed-loop paths (F01) are not drawn. The brief asked for half speed so that all three
  estimators appear. Their scores are in A1.
- The other F tests (F2, F3, F3b, F3c, 2(a)) were not added to A3. Only F1 (pack F07) was requested.
