# Handover: final results pack (2026-10-11; METHODOLOGY ruling 2026-10-11, item 0)

**Stage:** analysis only. No replays, no new runs, no edits to METHODOLOGY.md, numbers.md or src/.

## What was built
- **Script:** `eval/figs_final_pack.py`. Run it with `~/venv-evo/bin/python eval/figs_final_pack.py`; it takes about 3 min and reads dataflash logs.
  It writes:
  - `plots/final_results_pack/F01…F15b_*.png` (17 figure images);
  - `docs/thesis/final_results_pack.pdf` (23 pages: cover with contents, one captioned page per figure, then the tables T1 and T2);
  - `docs/thesis/final_results_pack_index.md` (status, source, the numbers.md rows each figure supports, the per-figure check
    tables, the FLAG list, the historical figures and the full captions).
- **Corrections table source:** `docs/thesis/final_results_pack_corrections.md`, 18 rows (T2).
  - Each correction has its scope, what was wrong, how it was found, its effect, and its attribution status.
  - The attribution status follows the 2026-10-10 rulings: joint, except for the plain-wall trace, the O partial
    attribution, `dsn_tex_r2` by elimination, the explicit ablation pairs, and the FGO-only re-run, which is a single-correction pair.
- **T1** is rendered verbatim from `docs/thesis/headline_claims_before_after.md`. The counts are checked: 36 rows, 17 HOLDS / 16 CHANGED / 3 WITHDRAWN.
- **Checks:**
  - Every plotted headline value is compared with the value typed from numbers.md, or from METHODOLOGY where numbers.md has no row.
  - A match within one unit of the last printed digit is accepted and listed as a rounding-boundary transcription.
- **Closed-loop paths** come from the dataflash `SIM` record (simulator truth), not the zstd-packed bags. Cross-check:
  max |Δ| ≤ 4 mm against the scored B2 (bag GT) on the 6 full-speed flights.
- **The historical supervisor sets** (`plots/supervisor_2026-10-0{1,8}/`) are untouched. The index lists each old figure and
  what replaced it.

## Status counts
- **Figures:** 16 CURRENT, 1 FLAGGED (F13). Two historical figures are NOT REGENERATED and replaced:
  - the fig15 per-block curve, whose logs pre-date the final re-runs;
  - fig7, the old corrections table, now T2.
- **Tables:** T1 and T2 are CURRENT.
- F05 is CURRENT against its JSON only (no numbers.md row). F08, F14 and F15 use METHODOLOGY-only values where numbers.md has no row.

## FLAGS for the user (decisions or numbers.md tidy; nothing was edited)
1. **F13 / numbers.md §16.3 cost bullets** quote the FIRST final re-run: LC 36–41 ms, no-LC 47–54 ms, wall 9,868–11,175 s.
   The current FGO-only re-run outputs give LC 35–41 ms, no-LC 50–61 ms, wall 7,276–9,583 s. This is diagnostic only.
2. **numbers.md §15 lags METHODOLOGY.**
   - It still lists the original UKF half heading set as 2/3.
   - It has no rows for the UKF v2 contact (+165.9 s) or for the UKF v2 / FGO v2 / FGO v3 heading sets (all 3/3).
3. **H comparative criteria (H-H2, P-H3, H-H4) were never restated on S2v2/S3v2**, although METHODOLOGY says they would
   be "updated in the final restatement". F14 shows the values without a verdict. S2, S2v2, S3, S3v2, the S1-far
   shadows and the safety tests have no numbers.md rows.
4. **Rounding-boundary transcriptions in numbers.md**, each within one last-digit unit:
   - confirmatory d r5 is −0.4885, printed −0.489;
   - T table: A FGO batch is 0.0105, printed 0.011; C FGO live is 0.0535, printed 0.053;
   - L no-LC live lower bound is 0.263 from the file, printed 0.262.

## Not done / open
- The PDF footer commit is the base commit (`bccbc78`) the script ran on. The pack commit follows it.
- The old `plots/*.png` diagnostics (pre-2026-09-29) are listed as NOT REGENERATED. Their values must not be quoted.
