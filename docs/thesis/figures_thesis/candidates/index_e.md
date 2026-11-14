# Candidate thesis figures, group E: extension-experiment and Experiment 4/5 PATH candidates

Built by `eval/figs_cand_e.py` at commit `a4ec984` (run with `/home/makerspace/venv-evo/bin/python`). These are CANDIDATES for the user to pick from - not inserted into the thesis figure set in `docs/thesis/figures_thesis/` itself, and not folded into the combined candidates PDF, the thesis_assets bundle or the writing pack. Stored outputs only: `eval/results/*.json`, `docs/thesis/tier1/scores/*.json`, trial-directory `.tum` files, `sim/worlds/room_tags_map.json`, `gnss.npz`, and a cache of bag/dataflash reads pre-populated ONCE by `eval/figs_cand_e_extract.py` under `heavy.py`, written to `~/thesis_data/cand_e_cache/` and deleted at the end of this group's work. No estimator is run, no replay, no simulation, no flight.

**Checks:** 71/71 EXACT (string equality after one rounding by `rd()`, parsed from `eval/figs_thesis.py`, sha256 of the source segment used to detect drift).

**Style:** `eval/thesis_style.py` (160 mm / 6.30 in text width, Okabe-Ito palette, no in-figure titles, no verdict words, no bold text, equal-scale top-down axes labelled East/North for every spatial-path candidate; E05 is a time series, not a spatial path, and is labelled accordingly). No two plots overlap.

## Candidates

| id | proposed title | source chart(s) | data files | checks | verdict pointer |
|---|---|---|---|---|---|
| E01 | Extension E2 (loop closure with fewer tags): the FGO's live path, with and without loop closure, by tag count | NEW (not drawn by any existing figure or candidate; B03 draws the equivalent for condition A, 8 tags) | docs/thesis/tier1/scores/E2_T_{B,C,D}_r1.json; ~/thesis_data/tier1/T_{B,C,D}_r1/lc_fgo_*/live.tum | 18/18 | Verdicts: Table A.4, none (descriptive). |
| E02 | Extension E3 (wrong tag IDs): the FGO's live path, clean reference and two 1% runs | NEW (not drawn by any existing figure or candidate; C05/C06 draw the hindsight track + final landmark map for non-diverged runs only) | docs/thesis/tier1/scores/E3a_T_A_r1_0.01_{s0,s1}.json, E3_verdicts.json; eval/results/expL/T_A_r1_t245.json | 9/9 | Verdicts: Table A.4, none (descriptive). |
| E03 | Extension E5 (UKF with tag landmark states): UKF and FGO paths, with and without loop closure | NEW (not drawn by any existing figure or candidate; B03 draws the FGO-only equivalent) | docs/thesis/tier1/scores/e5_T_A_r1.json; eval/results/expL/T_A_r1_t245.json; ~/thesis_data/tier1/T_A_r1/lc_ukf_{lc,nolc}_t245/*.tum; ~/thesis_data/trials/T_A_r1/lc_fgo_{lc,nolc}_t245/*.tum | 16/16 | Verdicts: Table A.4, none (descriptive). |
| E04 | Experiment 4 (outdoor-indoor): each estimator's live path over the true path, dropout and return marked | NEW spatial-path view (B04 draws the same data as error against time, not a path) | eval/results/expO/O_r1.json; ~/thesis_data/trials/O_r1/room_ukf/ukf_live.tum, room_fgo/fgo_live.tum, gnss.npz | 9/9 | Verdicts: Table A.4, none (descriptive). |
| E05 | Experiment 5 (tag hold): each flying estimator's own distance from ground truth over time, occluder intervals shaded | NEW (B06/B07 draw aggregate bars over all losses/flights, not a per-flight time series) | eval/results/expH/{s1far_r1,s2v2_r1,s3rp_r2}.json | 10/10 | Verdicts: Table A.4, none (descriptive). |
| E06 | Extension E4 (live window sweep): the FGO's live path at three window lengths | NEW (not drawn by any existing figure or candidate) | docs/thesis/tier1/scores/E4_T_D_r1_w{0.25,1,5}.json | 9/9 | Verdicts: Table A.4, none (descriptive). |

## Skipped or time-boxed (not in any candidate's caption - process notes belong here, not on the figure)

- E01 (Extension E2): only flight 1 of 3 per condition B/C/D is plotted; flights 2 and 3 are not. Their per-lap numbers are already in the Extension E2 results.
- E02 (Extension E3): only flight T_A_r1 is plotted; one non-diverged (1% seed 0) and one diverged (1% seed 1) run of the 6 diverged and 12 non-diverged arm (a) runs are shown.
- E03 (Extension E5): only flight T_A_r1 of 3 is plotted.
- E04 (Experiment 4): only flight O_r1 of 3 is plotted; flights O_r2/O_r3b are not - their error-against-time curves for all three flights are already candidate B04.
- E05 (Experiment 5): only the first loss of each flight is cross-checked against the stored per-loss drift; the later shaded intervals on each flight's own timeline are read directly from its own stored result file, not independently re-checked.
- E06 (Extension E4, window sweep): lowest-value item per the common brief's time-box priority; only one tag count (condition D) and three of the five tested windows are plotted.

## Judgement calls for the coordinator

- **E02 vs C05/C06**: both groups draw Extension E3 paths for T_A_r1's 1% seed 0 run. C05 draws its hindsight track plus the final landmark map (a non-diverged, already-settled view); E02 draws its live track (the same run, different track) alongside a genuinely diverged run's live excursion, which no existing candidate shows. Kept as complementary, not flagged as a duplicate to drop.
- **E05's FGO flight uses the corrected-priors hold set (s3rp_r2), not the original-priors set (s3v2) candidates B06/B07 use.** `H_s3rp_r1` (the first repeat of that set) has no stored bag, only `ardupilot.bin` - but `H_s3rp_r2` and `H_s3rp_r3` do have full stored bags, so E05 uses `s3rp_r2` rather than falling back to the superseded set. Flagged here because B06/B07 (an earlier group) still plot the superseded set; the coordinator may want to redraw B06/B07's FGO bar onto s3rp as a separate, later fix.
- **E06 uses flight T_D_r1 (condition D, 1 tag), not T_A_r1.** On T_A, the live RMSE is identical to 4 dp across all five tested windows (e4_results.md), so three plotted paths would be visually and numerically indistinguishable there; T_D has the largest spread across windows (0.0931 / 0.0863 / 0.0887 m) of the four tested conditions.

