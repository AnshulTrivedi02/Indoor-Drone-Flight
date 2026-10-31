# E6: map reuse ("map once, fly again"), results (Stage 2)

**Extension experiment E6, pre-registered (2026-10-31)** in `e6_preregistration.md` (committed `6c0365b` before any E6
run).
- This page records the numbers and the mechanical verdict that each pre-registered rule gives. The reading in §4 is
  plain language. No claim in it is stronger than its verdict.
- **Code:** branch `e6-map-reuse`, run from the worktree. 2a ran at `18da989` and 2b at `aabac1e`, which adds only the Stage 2 driver, its timing file, D95 and
  guard reports to `18da989` (no estimator or scorer code; `src_dirty` is empty in every `stats.json`).
- **Run:** 2026-10-31 23:16 to 2026-11-01 01:07 AEDT, serial, one `heavy.py` job at a time, thread variables at 1.
- **Every number below** was built by `e6/e6_tables.py` from the score jsons, rounded once. Positions are in m at 4 dp;
  ratios are at 2 dp. `e6/check_e6_prose.py` re-builds every table row and every hand-typed number and requires string
  equality in this file, in `e6_numbers.md` §Results and in the Stage 2 handover (0 mismatches).
- **Verdicts** are computed on the unrounded json values by `eval/e6_verdicts.py` (written in Stage 1, D93), which writes
  `scores/e6_verdicts.json`.
- **Pairing (D85, D94):** map from `E6M_fig8_r1b` → test flight `T_A_r1`, `E6M_fig8_r2` → `T_A_r2`, `E6M_fig8_r3` →
  `T_A_r3`.

## 1. Runs and gates

- **Runs:** 2a UKF (live + RTS) and 2b FGO (live + whole-flight batch), 6 runs each. All 12 exited 0. 2b had 0 keyframe
  failures, and every FGO whole-flight batch converged in 4 iterations. No replay was re-run (D95).
- **Map provenance:** in every new run, `stats.json:e6.tag_map_sha256` equals the sha256 of the map file used, and
  every non-gauge tag has a nonzero shift. For each flight, the FGO-map and UKF-map tracks differ.
- **Scorer gate S-E6:** re-run inside every scoring call, PASS 3/3 (max |diff| ≤ 4.09e-16 m, tolerance 1e-9 m).
- **Guard:** IDENTICAL before 2a, after 2a, after 2b and after scoring (§7).

## 2. Results table (horizontal RMSE over the lap window, m; world frame, no alignment)

"live" is the estimator's real-time output: the UKF filter, or the FGO 0.25 s fixed-lag smoother. "hindsight" is the
UKF RTS smoother, or the FGO whole-flight batch LM. For arm (iv) it is the stored loop-closure hindsight (Experiment 3
iSAM2 + 5 updates; E5 RTS). Arms (i) and (iv) are re-scored from stored results and were not re-run.

{main}

Source: `json:scores/e6_T_A_r{{1,2,3}}.json:tracks."<arm> | <estimator> <live|hindsight>".{{rmse_m, per_lap_rmse_m[0]}}`.
Max, every per-lap value and lap-5 ÷ lap-1 are in the same jsons.

**Map error (P1 input; 7 non-gauge tags, m).** Source: `json:scores/e6_verdicts.json:flights.<t>.map`, from
`~/thesis_data/tier1/e6/maps/<m>/map_errors.json`.

{maps}

## 3. Verdicts (as worded; `json:scores/e6_verdicts.json:criteria`)

{verdicts}

**P2 detail.** The band is [min − R, max + R] of the stored arm (i) live repeats (D87), shown to 6 dp because it is
scored unrounded.

{p2}

**Headlines (pre-registered §5 form):**
- **P1: FAIL** (2/3). The FGO map is lower on `E6M_fig8_r2` and `E6M_fig8_r3` and higher on `E6M_fig8_r1b`
  ({p1_r1b}).
- **P2: FAIL (both).** FGO 0/3: all three values are above the band. UKF 2/3: `T_A_r1` is above the band ({p2_ukf_r1}).
- **P3: FAIL (both)**, 2/3 for each estimator. On `T_A_r1` the FGO map gives the higher live error for both estimators.
- **P4: PASS (both)**, 3/3 for each estimator.

**Descriptive ratios (no verdict; §6 of the pre-registration):**

{ratios}

- **P4-overall** (descriptive): the FGO map's overall live error is lower than arm (iv)'s on 3/3 flights for each
  estimator (ratio {p4o_fgo} for the FGO and {p4o_ukf} for the UKF).

## 4. Plain-language reading

- **A map from one earlier flight is much better than no map at the start of a flight.** On lap 1, before the
  loop-closure estimators have re-observed any tag, the FGO map gives lap-1 live errors of {l1_fgo_map} for the FGO,
  against {l1_fgo_iv} with no map. For the UKF it gives {l1_ukf_map}, against {l1_ukf_iv}. This is P4, PASS for both
  estimators.
- **It does not replace the survey at survey accuracy.** The estimated maps are off by {map_fgo} (FGO map) and
  {map_ukf} (UKF map) RMS per tag. With the map used as exact, that error becomes a fixed bias near each tag.
  - FGO estimator: on the FGO map, the live error is {r_fgo} times the surveyed-map value and outside the
    surveyed-map band on every flight (P2 FAIL, 0/3).
  - UKF estimator: its surveyed-map live error is larger to begin with ({ukf_i}), and on the FGO map it is
    {r_ukf} times that. It still left the band on one flight (P2 FAIL, 2/3). The cause of the smaller relative
    cost was not diagnosed.
  - The hindsight tracks do not recover surveyed-map accuracy either. The FGO whole-flight batch on the FGO map reaches
    {hs_fgo_map}, against {hs_fgo_i} on the surveyed map.
- **The FGO's map was better on two of the three mapping flights, not on all three** (P1 FAIL, 2/3). Descriptively,
  on every flight the live error ranked the two maps the same way as their map error did: the per-flight outcomes of
  P1, P3 (FGO) and P3 (UKF) are identical (no, yes, yes).
  Where the FGO map was the better map (r2, r3), both estimators flew better on it. On r1b the two maps were within
  {r1b_diff} of each other and the FGO map was slightly worse, and so were the live errors (P3 FAIL for both).
- **Hindsight is different (descriptive, no verdict).** The FGO that estimates its own map online (arm (iv), iSAM2
  hindsight, {hs_fgo_iv}) beat the FGO whole-flight batch on either fixed estimated map ({hs_fgo_maps}) on
  {n_hs_fgo}/3 flights. The UKF did not show this: arm (iv) RTS gives {hs_ukf_iv}, against {hs_ukf_fmap} on the FGO
  map. The P4 confound (different estimators in arm (iv)) applies here too.
- **In short, for the live tracks:** "map once, fly again" works as a replacement for surveying in the sense of
  beating no map (P4), but not as a like-for-like replacement for a surveyed map (P2). The pre-registered expectation that the FGO's map is
  consistently the better one (P1, P3) did not hold on all three flights.

## 5. Limitations

- **Simulation only.** Rendered tags and simulator-truth flight paths, with no lighting change or tag wear between the
  mapping and test flights. The map's only error source is the estimator.
- **n = 3.** There are three mapping flights and three test flights, in fixed pairs. Bands built from three repeats are
  coarse, and P1, P3 and P4 are direction-only.
- **Perfect tag IDs.** No tag was misidentified in the mapping or test flights (E3 studied wrong IDs separately).
- **The same-route caveat does NOT apply.** The mapping flights are out-of-sample figures of eight on a different route
  from the test flights' square laps (pre-registration §1.3, §3.1). They re-observe tags 4 and 6 twice per circuit and
  the others once, over 3 circuits.
- **One surveyed tag registers the frame** (tag 0, pre-registration §1.2), so "replacing the survey" here means
  replacing the survey of the other 7 tags.
- **P4 confound.** Arm (iv) uses different estimators (the iSAM2 keyframe FGO and the landmark UKF) and every central
  detection. The map arms use the thesis estimators on one fix per frame.
- **The FGO map is the Experiment 3 iSAM2 hindsight** (5 extra updates), not an LM batch.
- **No map uncertainty is propagated:** the map is used as exact, as the user designed it.
- **Same world, same day, same tags.** Map reuse over time (moved or replaced tags) is not tested.

## 6. Run timings (DIAGNOSTIC, workstation, serial; `e6/stage2_timing.tsv`)

{timing}

- FGO whole-flight batch alone: {batch} per run (`stats.json:batch_s`). That is well below the pre-registered upper
  bound of 2,961 s, which was a 6-parallel figure.

## 7. Guard (`frozen_manifest_20261022T002851.json`, 13,253 files)

| check | result | report |
|---|---|---|
{guard}
