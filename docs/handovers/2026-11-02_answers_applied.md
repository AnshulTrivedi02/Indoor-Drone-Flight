# Handover 2026-11-02: the user's five answers applied

**Request:** the user's answers 1–5 of 2026-11-02 (walkthrough dividers, extra 1C flights, Figure 5.2 title, E3 tag maps, E6 page and
limitation). Branch `answers-applied`, cut from `fwd-camera` at `4861f3d`. **Not merged.** No number, pass rule or registered verdict
changed. numbers.md, the frozen pack and every result file are untouched. Decisions **D97–D105** are in `docs/thesis/tier1/decisions_log.md`.
METHODOLOGY has the entry "RULING (user, 2026-11-02): answers 1–5 applied".

## Per answer
1. **Walkthrough standalone, dividers kept.** Built without `--no-dividers`.
2. **Five additional no-heading 1C flights** (`cl_a_tex`, `cl_ukf_a_tex`, `cl_ukf_a_tex_half`, `cl_fgo_a_tex_half`, `cl_fgo_a_tex_half_v2`;
   the list is confirmed: the 8 stored `closed_loop_*_a_tex*` files minus the 3 registered ones).
   - **Verdict independence:** every registered 1C verdict is computed from `HALF` in `eval/figs_thesis.py` and `eval/figs_thesis_summary.py`
     (the flights script parses the former). `HALF` holds none of the five. `figs_walkthrough_extra.py` asserts it: HALF is identical in
     both scripts, the five are not in it, and the stored files are exactly 3 registered + 5.
   - Shown in the appendix only (walkthrough page A3, `extra/ex_1C_extra.png`), tagged "additional flights, not part of the pre-registered
     set": contact times only, each equal to `numbers.md` §15 lines 470–474 (+186.2, +163.0, +198.0, +165.8, +169.6 s), with each flight's
     speed and build. No windows or PASS marks are drawn (D98).
3. **Figure 5.2 (F7) title** now reads "… the error grows 2.9 to 4.5 times over five laps". The stored range matches: live lap 5 ÷ lap 1
   without loop closure, `rng(nl5, 1)` over `eval/results/expL/T_A_r{1,2,3}_t245.json` (3.855 / 4.498 / 2.945), the same string as F7's
   existing check row ("Experiment 3 lap5/lap1 … 2.9–4.5") and `numbers.md:574`. The title is built from that value and asserted.
   - `check_claims_applied.py`'s "F7 title kept" row now expects the new title (D99).
   - F7 png/pdf, `figures_thesis/index.md` and `thesis_figures_combined.pdf` were regenerated. Every other `figs_thesis.py` output that
     differed only in its commit line or PDF metadata was restored. The old title survives only in dated snapshots (`glossary.md`,
     `glossary_flags.md`, `tier1/claims_update.md`), left unedited.
4. **E3 tag maps:** the main page shows the clean reference (kept, D100) and one collapse example, T_A_r1 1% s0, FGO as built. The other two
   maps moved to the appendix (page A2, `flights/fl_E3_maps_app.png`, DESCRIPTIVE). No extra runs were added.
5. **E6 page** in both PDFs, in the extension section between E5 and the ablation.
   - Summary page id 20 (`summary_20_E6_map_reuse.png`; the ablation keeps id 19, D101). The walkthrough page is 20 (`extra/ex_E6_map_reuse.png`):
     - P4 first lap: FGO 0.0303–0.0510 against 0.0818–0.1608 m, UKF 0.0389–0.0471 against 0.1560–0.2565 m;
     - P2 whole flight: FGO map ÷ surveyed 1.52–2.14 (FGO), 0.98–1.26 (UKF), with the surveyed bands;
     - P1 / P3: map-error vs live-error differences per flight, DESCRIPTIVE ("same sign on 3 of 3 for both estimators; on r1b the maps
       differ by 0.0007 m"), and the limitations on the figure.
   - Every number is from `scores/e6_verdicts.json`, cross-checked with `e6_T_A_r{1,2,3}.json` and found in `e6_results.md`.
   - The registered section's new page R7 prints E6's Metric / Pass rule (pre-registration fragments, word for word) and Result (the
     verdicts as worded: P1 FAIL 2/3; P2 FAIL (FGO 0/3, UKF 2/3); P3 FAIL 2/3 each; P4 PASS 3/3 each).
   - The summary section page now says E6 was pre-registered separately and flew three new mapping flights.
   - `limitations.md` item 4 added verbatim (D104).

## Also fixed
- The walkthrough contents note overlapped the first row (present at HEAD): rows lowered (D105).

## Pages
- `summary_plots.pdf`: 22 → **23** pages.
- `results_walkthrough.pdf`: 40 → **44** pages (E6 page, registered page R7, appendix pages A2 and A3).

## Checks (before → after)
| check | before | after |
|---|---|---|
| figs_thesis | 348/348 | 348/348 |
| summary | numbers 196/196, display 50/50, rules 86/86, counts 13/13 | 214/214, 54/54, 100/100, 14/14 |
| flights | 95/95 printed, 167/167 data identity | 96/96, 167/167 |
| extra | 130/130 | 166/166 |
| walkthrough | verbatim 112/112, NEW 80, worlds 16/16, failures none | 118/118, NEW 86, worlds 17/17, failures none |
| check_claims_applied | 58/58 | 58/58 |
| check_discussion | 18/18 | 18/18 |
| check_ablation | 228 / 0 mismatches | 228 / 0 |
| e6/check_e6_prose | 0 mismatches | 0 mismatches |
| check_numbers_frozen | PASS | PASS |
| sha256 records under docs/thesis | 72 match | 78 match |

For the sha256 records, the only mismatches are the 3 known rows that hash rd()'s source text, not a file. The `stage2_gates.md` rows point
at data files outside the repo.

## Heavy step
- `figs_walkthrough_flights.py` (`--extract-only`, then the plots) ran through `heavy.py` with the cache at `~/thesis_data/walkthrough_cache`.
- The cache was deleted afterwards. Every other `fl_*.png` is byte-identical to HEAD.

## Rebuild order
`figs_thesis.py` (venv-evo) → `figs_thesis_summary.py` → `figs_walkthrough_extra.py` → flights via `heavy.py` → `figs_results_walkthrough.py`.
Restore pixel-identical PNGs only before the walkthrough runs, then re-check the sha records.

## Open
- The summary contents numbers rows by position, so E6 (id 20) is row 19 and the ablation row 20.
