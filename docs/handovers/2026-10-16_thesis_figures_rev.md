# Handover: thesis figure set revised into figures + tables (2026-10-16)

**Stage:** revise the 2026-10-15 reader-facing set. FROZEN NUMBERS ONLY: plotting and tabulating from the stored result
JSONs and recorded files; nothing re-run or recomputed. METHODOLOGY.md, numbers.md, every result file,
`eval/figs_final_pack.py` and `docs/thesis/final_results_pack.pdf` are untouched.

**Run:** `/home/makerspace/venv-evo/bin/python eval/figs_thesis.py` (about 2 min). The outputs stamp the HEAD at run time
(`7778cd6`, the parent of this commit; the script itself is the one in this commit).

## Outputs
- `docs/thesis/tables/T1…T8_*.{tex,md,png}`: each table from ONE row list → LaTeX (booktabs), markdown and a rendered page.
  **The .tex was NOT compiled** (no TeX on this machine); `tex_selfcheck()` asserts pure ASCII, balanced braces and
  ncols−1 `&` per row. Needs `\usepackage{booktabs}` (and textcomp on an old TeX).
- `docs/thesis/figures_thesis/`: F2 (rebuilt, one panel), F5, F7 (unchanged), F6 (time trace only), A1–A3,
  `thesis_figures_combined.pdf` (18 pages: title, 4 figures, 8 tables, A1–A3), `index.md` (captions, sources, every check).
- **Removed** (`git rm`, still in history at `7778cd6`): F1→T1, F3→T2, F4→T3, F8→T5.

## Check counts (all match; 117/117 total, a check shared by two items counted in each)
| item | checks | was |
|---|---|---|
| F2 | 4/4 (contacts; B2 ranges; plotted path max\|x\| vs scored B2 ≤ 0.05 m (0.011); path ends at the scored contact ≤ 0.5 m (≤ 0.023)) | 8/8 (heading-curve vs scorer check dropped with the panel) |
| F5 / F7 | 8/8 / 5/5 | unchanged |
| F6 | 4/4 (jump, 123 s, curve vs json, no tags) | 9/9 (the 5 per-track RMSE checks moved to T6) |
| T1 | 16/16 | F1 16/16 |
| T2 | 10/10 (F3's 9 + dsn median) | F3 9/9 |
| T3 | 6/6 | F4 6/6 |
| T4 | 9/9 (passes, B2 per flight, B3 per flight, contacts, FGO r3 B4 0.246) | new (B3 from F2) |
| T5 | 6/6 | F8 6/6 |
| T6 | 7/7 (5 RMSE ranges, H-O2 ratio, H-O1 3/3) | new |
| T7 | 9/9 | new |
| T8 | 6/6 (P-T4 1.31/2.14/2.07/3.89; table = stored ratio; RTS and batch A–D; O 1.01–1.02; cap-free 1.02–1.05) | new |
| A1 / A2 / A3 | 8/8 / 11/11 / 8/8 | unchanged |

Last-digit rounding matches (accepted as before; listed in index.md): T FGO batch A 0.010 vs 0.011; T C FGO live 0.054 vs
0.053; O H-O2 1.71 vs 1.72; L nolc 0.263 vs 0.262; **new:** T8 C ratio 2.06 (stored 2.0649) vs numbers.md 2.07; O cap-free
1.01–1.05 vs 1.02–1.05.

## Design notes
- **F2:** one panel, corridor horizontal, lateral axis stretched **3.0×** (computed from the drawn axes after layout and printed
  on the figure and in the caption). Dashed = no heading, cut at the contact time, X = contact (EKF3 +242.1, UKF +165.9,
  FGO +169.9 s); solid = with heading, 9 flights, overlapping on the centreline (stated). UKF and FGO contact at nearly the same
  point (~84 m), so their Xs overlap; labels are placed apart with leader lines.
- **F6:** time trace only, events from `markers_bag_s`: GNSS OFF 0 s, far end ~60 s (+3 s hold), return 63 s, GNSS ON 123 s;
  EKF3 jump annotation now points at the actual 4.10 m peak (~127 s).
- **T8 ratio** = max ÷ min (the pre-registered P-T4 / P-O3 definition), with a "lower" column: in O the RTS-UKF is lower on
  O_r1/O_r2, the FGO batch on O_r3b. T is per condition (mean of 3), O per flight.
- **T2 Phase 5 column** comes from `phase5_analysis.json`, last changed in the FGO-only re-run (`819caab`, 2026-10-10), so it
  is current; still JSON-only (no numbers.md row; not cross-checked).
- **T7 "no invalid period recorded"** for UKF/FGO on the blank floor means only that `blank_behaviour.json` stores an invalid
  period for EKF3 alone. It does not claim the estimators have no validity output.

## S-A4 finding (early score files)
`safety_ukf_a.json` (UKF (a) run 1) and `safety_fgo_b.json` (FGO (b) run 1) score **S-A4 FAIL**, with
`rearmed_after_disarm: null` (no disarm recorded). numbers.md cites only S-A2/S-A3 for them. METHODOLOGY says:
- UKF (a) run 1: "S-A4: not applicable (an (a) run)" (L11490). S-A4 is pre-registered for (b) runs only (L11307).
- FGO (b) run 1: "S-A4: not scored (no touchdown). One LAND entry, no conflict between the two paths" (L11827). The run was
  stopped at the room-box breach.

So both are **scorer artefacts**, not landing conflicts. The scorer also evaluates S-A4 on (a) runs. T7 and the A2 note show
the file value, the METHODOLOGY reading and the flag. A ruling on whether to state it in numbers.md is the user's.

## C: can T condition A (live) and L share a metric on T_A_r1–r3? **YES** (checked, not built)
- **Window:** T's `window_s` equals L's `lap_bounds_s[0]` and `[-1]` exactly on all three flights. Both are first
  `LAP 0 LEG 0 START` → `LAPS END` from fly_trial.log, mapped with the same `/imu/time_ref` lower-envelope polyfit.
- **Time base:** bag sim time for both. Both anchor at the same instant (28.546 / 28.975 / 28.744 s). The L replays end at
  ~273.5 s, after the window end (~269.6–270.0 s), so the cut at anchor + 245 s does not truncate the window.
- **Metric:** both are horizontal \|p − p_gt\| at the track's own samples inside the window, RMSE, no alignment. T is in the world
  frame. L is in tag 0's frame, and `l_score.py` maps ground truth by the known translation (−3, −3) (tag 0 yaw asserted 0).
  That is a fixed known translation, not an estimated alignment, so the error is identical. Check: at the anchor,
  L live + (−3, −3) equals T `room_fgo` live to ≤ 1.2 mm.
- **Sampling:** L live/hindsight have 7202 / 7201 / 7201 samples in the window, the same keyframes as T's FGO live and batch
  (30 Hz). T's EKF3 has 2400 (XKF1) and the UKF 16000 (15 ms); both are already mixed within T.
- **Information:** L's central-third detections (2423 / 2328 / 2314) equal T_A's `n_sent` exactly. The only difference is that
  the map is unknown in L.
- **Caveats:**
  - L is a different estimator: the keyframe iSAM2 FGO, not the thesis fixed-lag FGO. L's "hindsight" is the full iSAM2
    estimate plus an LM polish, not the whole-flight batch. Label these separately.
  - L's gauge is set by the first tag-0 sighting, so that sighting's error persists as an offset (an inherent L property).
- **What exists now:** overall RMSE for both, directly from the stored JSONs. T has no per-lap values.
- **Proposed combined figure (NOT built):** per-lap horizontal RMSE, laps 1–5 on L's `lap_bounds_s`, T_A_r1–r3.
  - Solid/filled: EKF3, UKF and FGO live with known tags (T_A); the L keyframe FGO live with and without loop closure.
  - Dashed/open: the T_A FGO batch / RTS-UKF and the L hindsight.
  - The T per-lap points need the STORED T tracks (`room_ukf/*.tum`, `room_fgo/*.tum`, XKF1 via the clock map) re-scored over
    L's lap bounds. That is **scoring of stored outputs, not recomputing estimator outputs**: **flagged for the user's
    decision.**
  - A fallback that needs no re-scoring: an overall-RMSE dot plot (T_A per flight from `tracks.*.horiz_err_m.rmse`, L from
    `rmse_m`).

## Not done / open
- The .tex files were not compiled (no TeX installed).
- numbers.md still lists the UKF v2 / FGO v3 safety runs as final, and the S-A4 artefact is not in it. Both are flagged for
  the user, not edited.
