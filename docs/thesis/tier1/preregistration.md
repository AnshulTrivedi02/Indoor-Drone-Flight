# Extension experiments E2–E5: pre-registration

**Extension experiments, pre-registered.** Offline only: replays of recordings that already exist. No flights and no
simulator runs.

- **Status: DRAFT, awaiting the user's sign-off.** Nothing in this document has been run. No replay, estimator run
  or simulation was started while it was written.
- **Written:** 2026-10-21 (AEDT), against commit `c1dd6ee` (branch `fwd-camera`). The code changes in Stage 1 are in
  the commit that adds this file (see the handover `docs/handovers/2026-10-21_tier1_stage1.md`).
- **Result lock: 2026-11-04 23:59 AEDT (UTC+11).** Every replay that counts must have finished, and its output must be
  on disk, by then. Anything not finished is reported as **not run** and listed as future work (§8). If the user
  meant the start of 4 Nov rather than its end, only the clock time in this line changes.
- **Rulings this implements:** the user's rulings of 2026-10-21. The first covers E2, E3, the output redirect, the
  checksum guard and the results location. The scope update the same day added E3 arm (b) as planned work, E4, E5
  and the 4 Nov lock.
- **Results location:** `docs/thesis/tier1/numbers_tier1.md` and `docs/thesis/tier1/` only, never `numbers.md` or the
  frozen pack (§9).
- **Citation keys.** `N:` = `docs/thesis/numbers.md` line; `M:` = `METHODOLOGY.md` line; `json:` = a file under
  `eval/results/`. Code lines are **at `c1dd6ee`** unless marked HEAD; Stage 1 shifts some line numbers.

Thesis names (`docs/thesis/thesis_vocabulary.md:72-73`): Experiment 2 = repo "Experiment T" (known tags). Experiment 3
= repo "Experiment L" (loop closure).

---

## 0. Shared definitions (every experiment)

### 0.1 Recordings

The 12 current Experiment 2 flights are `~/thesis_data/trials/T_{A,B,C,D}_r{1,2,3}`, the re-flown ones included.
- The `*_IMUGAP` and `*_ABORTED` directories are never used (M:10215-10234).
- Each flight has an `imu_gaps.json` with an `ok` verdict (M:10233-10234).
- `eval/imu_gap_check.py --write` is **not** re-run. These are not new trials, and re-running it would rewrite a
  frozen input file (the guard covers it).

| condition | tags sent in Experiment 2 (`metadata.yaml` `tag_bridge.tag_ids`) | median gap between fixes |
|---|---|---|
| A | all 8 (`all`) | 4.3 s |
| B | 0, 1, 2, 3 (corners) | 10.1 s |
| C | 0, 2 (diagonal) | 22.0 s |
| D | 0 only | 46.3 s |

Sources: the conditions are in M:10116-10121 and in each trial's `metadata.yaml`. The median gaps are at N:526-529.

The tag map is `sim/worlds/room_tags_map.json`. The 8 tags sit on a 6 m square: tag 0 at (−3, −3) with yaw 0. The
non-gauge tags are 3.00–8.49 m apart, and their yaws differ by 15–165°.

**Every T bag's `/tags/raw` contains all 8 tags, whatever the condition.** Central-third detections per flight
(whole bag; read-only input statistics computed on 2026-10-21):
- 2288–2423 in total;
- tag 0: 577–653, over 6 passes;
- each other tag: 179–302, over 5 passes.

### 0.2 Experiment 3 configuration (frozen; E2, E3 and E5 inherit it)

**Code.** `src/estimators/fgo/lc_fgo_replay.py`, which produced every frozen Experiment 3 result at commit `2cc08a2`.
- The job runner logged that commit: `~/thesis_data/batches/final2_L/jobs.log`, line 1.
- The job list is `~/thesis_data/batches/final_rerun2/final2_L.fgo.jobs`.
- N:585-587 cites the same provenance.

**Exact frozen command** (one per flight and mode):
```
cd /home/makerspace/thesis_ws && OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 nice -n 10 \
  /home/makerspace/venv-fgo/bin/python src/estimators/fgo/lc_fgo_replay.py T_A_r1 --mode lc --t-max 245
```
It was run through `eval/run_jobs_resumable.sh` with `parallel=6`.

**Every parameter.** None of these is a flag; all are fixed in code.

| setting | value | where |
|---|---|---|
| `--mode` | `lc` (one landmark per tag id) or `nolc` (a new landmark per pass) | lc_fgo_replay.py:39, 170-176 |
| `--t-max` | 245 s after the anchor (DEVIATION, recorded) | :40, :216; M:10559 |
| `--gauge-tag` | 0 (default) | :40 |
| `PASS_GAP_S` | 1.0 s (a pass ends after > 1 s without a sighting) | :44 |
| central-third rule | radius (1/3)·hypot(320, 240) px about (320, 240), with fx = 554.38 px | :45, :74-76 |
| tag input | every central detection in `/tags/raw` | :57, :69-79 |
| pre-anchor estimator | thesis FGO: window 0.25 s, 30 Hz keyframes, LM ≤ 2 | :118 |
| anchor | first sighting of the gauge tag; re-anchor, then a retained-history iSAM2 (QR) | :133-151, :230-233 |
| landmark factor | vehicle (x, y, yaw) in the landmark frame, σ = 0.05 m, 0.05 m, 5° (diagonal, NO robust kernel, NO gate) | :83-105, :123; `measurement_models.py:356-357` |
| landmark initialisation | from the predicted pose and the inverse measurement | :108-110, :203 |
| gauge | L(0) = 0, prior σ 1e-4 (isotropic) | :199-201 |
| live | newest keyframe after each iSAM2 update | :211; M:10476 |
| hindsight | iSAM2's full estimate after 5 extra `update()` calls (DEVIATION) | :278-285; M:10557 |
| no yaw cap after the anchor | | M:10468 |

**Code delta `2cc08a2` → HEAD on the files the replay imports.** It is limited to the `geom=None` plumbing in
`factors.py`, `fgo_core.py` and `measurement_models.py` (commits `0ac0983` and `4608637`). With `geom=None` (the
default) the code path is designed to be identical. Gate **G0-L** (§7) tests this rather than assuming it.

**Every `OpticalFlow.msg` copy that the recursive glob at :49 can find is identical** (81 copies, one md5,
2026-10-21). The glob therefore resolves the same message whichever copy it lands on.

### 0.3 Metrics "as Experiment 3" (E2, E3, E5)

**Scorer:** `eval/l_score.py`. The same file is used for E2–E5; Stage 1 only adds `--in-root` and `--prefix`, and with
neither flag its behaviour is unchanged.
- **Frame:** tag 0's frame. Ground truth is mapped into it by subtracting tag 0's map position (−3, −3); tag 0 has
  yaw 0, which an assert checks (l_score.py:18-19, :28). The estimator never sees the map.
- **Window:** the lap window, from the first `LAP k LEG 0 START` to `LAPS END`. These come from `fly_trial.log` on the
  SITL clock and are mapped to the bag clock through the `/imu/time_ref` lower envelope (:30-43). It is the same window
  as Experiment 2's: for example, both are 29.52–269.57 s on T_A_r1 (`json:expL/T_A_r1_t245.json:lap_bounds_s`,
  `json:expT/T_A_r1.json:window_s`).
- **Metrics** (:45-53):
  - per track (live, hindsight) and mode: **horizontal RMSE overall** over the window;
  - **max error**;
  - **per-lap RMSE**, laps 1–5;
  - the derived **lap-5 ÷ lap-1 ratio**.
- **No alignment.**
- **Precision:** results are quoted to 4 dp in m in `numbers_tier1.md` and compared on the unrounded json values.
  N:§16.3 prints 3 dp, and its no-LC live lower bound sits on a rounding boundary: 0.2625 is printed 0.262 / 0.263
  (`final_results_pack_index.md`, FLAGGED item).

### 0.4 Stored reference values (CURRENT; the derivations use these only)

The superseded METHODOLOGY Experiment 3 result table (M:10566-10580: LC live 0.041–0.047, lap ratios 0.40/0.57/0.27)
is **not** used. The current values come from the final re-run (N:567-590) and are listed here.

| flight | LC live | LC hindsight | no-LC live | no-LC hindsight | LC live lap1 → lap5 | LC lap5/lap1 | no-LC lap5/lap1 |
|---|---|---|---|---|---|---|---|
| T_A_r1 | 0.0574 | 0.0198 | 0.3494 | 0.2210 | 0.106 → 0.034 | 0.32 | 3.86 |
| T_A_r2 | 0.0494 | 0.0270 | 0.2625 | 0.2451 | 0.082 → 0.035 | 0.43 | 4.50 |
| T_A_r3 | 0.0760 | 0.0172 | 0.3608 | 0.2657 | 0.161 → 0.026 | 0.16 | 2.94 |

All values are in m. Source: `json:expL/T_A_r{1,2,3}_t245.json`, keys `tracks.{lc,nolc} {live,hindsight}.rmse_m` and
`.per_lap_rmse_m`. They are summarised at N:571-574.

In all three flights, lap-1 LC live equals lap-1 no-LC live exactly. Every tag is new on lap 1, so lap 1 is dead
reckoning from the anchor in both modes.

**Experiment 2 per flight** (`json:expT/T_*_r*.json`, `tracks.<track>.horiz_err_m.rmse`; condition means at N:526-529):

| | FGO live | FGO batch | UKF live | RTS-UKF |
|---|---|---|---|---|
| A r1–r3 | 0.0214 / 0.0196 / 0.0190 | 0.0106 / 0.0107 / 0.0101 | 0.0356 / 0.0362 / 0.0382 | 0.0128 / 0.0141 / 0.0142 |
| B r1–r3 | 0.0233 / 0.0292 / 0.0252 | 0.0144 / 0.0142 / 0.0153 | 0.0607 / 0.0603 / 0.0625 | 0.0317 / 0.0317 / 0.0306 |
| C r1–r3 | 0.0538 / 0.0502 / 0.0565 | 0.0194 / 0.0191 / 0.0188 | 0.0717 / 0.0751 / 0.0808 | 0.0374 / 0.0407 / 0.0402 |
| D r1–r3 | 0.0931 / 0.0813 / 0.0745 | 0.0272 / 0.0261 / 0.0309 | 0.1332 / 0.1275 / 0.1311 | 0.1059 / 0.1111 / 0.1105 |

### 0.5 Verdict vocabulary and general decision rules

- **PASS / FAIL:** the criterion as worded, judged on the stated count (for example 3/3) of runs that completed and
  passed their gates. **NOT MET (insufficient data):** a run needed by the criterion is missing (not run by the lock, or
  crashed). It is never counted as PASS or FAIL.
- **No re-tuning, no re-runs to change a verdict.** A run that finishes is scored once. A crash is re-run once from
  scratch with the identical command (the runner does this on resume). The crash is reported either way.
- **Keyframe failures** (`stats.json:keyframe_failures`) do not exclude a run. They are reported, as in Experiment 3.
- A **gate** failure (§7) stops the experiment it guards before any hypothesis is scored, and is reported.
- **Prediction (P-)** criteria are scored and reported like hypotheses (H-), but do not carry the experiment's
  headline. **PRIMARY** marks the headline hypothesis.
- **Null result (general):** a pre-registered effect that is absent (FAIL) is a result. It is reported in
  `numbers_tier1.md` with the same prominence as a PASS.
- **Judgement bands.** Where a band contains a multiplier that is not computed from stored data, it is labelled
  **JUDGEMENT** below and flagged for sign-off.

---

## 1. E2: loop closure with fewer tags

**Question.** With tags at UNKNOWN positions, does the Experiment 3 keyframe FGO still bound its live drift when only
the condition's tags exist? Conditions B (4 corner tags), C (2 diagonal tags) and D (tag 0 only). And does it beat the
same FGO without re-identification?

**Recordings.** `T_B_r1–r3`, `T_C_r1–r3`, `T_D_r1–r3` (9 flights). Each flight is used with its OWN condition's
tags, the subset its `metadata.yaml` records. Condition A is not re-run: the stored Experiment 3 result IS
condition A.

**Arms.** For every flight: `--mode lc` (with re-identification) and `--mode nolc` (without). That makes 18 replays.

**Configuration: IDENTICAL to Experiment 3 (§0.2).** The only change is the tag-id filter.
```
cd /home/makerspace/thesis_ws && OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 src/estimators/fgo_cpp/tools/heavy.py "tier1 E2 lc T_B_r1" -- \
  /home/makerspace/venv-fgo/bin/python src/estimators/fgo/lc_fgo_replay.py T_B_r1 --mode lc --t-max 245 \
  --tag-ids 0,1,2,3 --out-root /home/makerspace/thesis_data/tier1
```
- **Filter:** `--tag-ids` takes B = `0,1,2,3`, C = `0,2` and D = `0`, copied from each trial's `metadata.yaml`.
- **Where it applies:** to the decoded id, after the central-third rule (HEAD lc_fgo_replay.py, read loop).
  - The central rule is geometry-only, so the order does not change which detections survive.
  - Excluded detections are counted in `stats.json:tier1.n_filtered_out_by_tag_ids`.
- **Output:** `~/thesis_data/tier1/T_B_r1/lc_fgo_lc_t245_tags0-1-2-3/`.

**Condition D is degenerate (stated).**
- **D with LC:** the only tag is the gauge tag, which is the origin by definition. LC on D is therefore the
  *known-map, one-tag* case, with one loop closure to the origin per lap.
- **D without LC:** every later pass over tag 0 becomes a new, free landmark (6 passes; lc_fgo_replay.py:172, 199).
  So no-LC D is dead reckoning, plus within-pass constraints only.
- **Reporting:** D's comparison with Experiment 2 is therefore descriptive. D's hypotheses are reported, but D carries
  no claim about *unknown* landmarks.

**Metrics:** as Experiment 3 (§0.3), per flight and mode, with the scorer below. Output:
`docs/thesis/tier1/scores/E2_T_B_r1.json`.
```
~/venv-tags/bin/python eval/l_score.py T_B_r1 --in-root ~/thesis_data/tier1 --suffix _t245_tags0-1-2-3 \
  --json docs/thesis/tier1/scores/E2_T_B_r1.json
```

**Hypotheses.** Each is judged per condition (B, C, D) on its 3 flights, with no pooling across conditions.

| id | criterion (per condition) | band | derivation (stored only) |
|---|---|---|---|
| **H-E2.1 (PRIMARY)** | LC live lap-5 RMSE ≤ 1.5 × lap-1 RMSE | ≤ 1.5, 3/3 flights | The pre-registered H-L1 band, unchanged (M:10501-10502). Stored A ratios are 0.32 / 0.43 / 0.16 (§0.4). Lap 1 is dead reckoning from the anchor in every condition (lap-1 LC = lap-1 no-LC in all of A), so lap 1 does not depend on the condition. Lap 5 follows a re-identification of every condition tag ≥ 4 times. In D, lap 5 is one lap of dead reckoning from tag 0, like lap 1, but with converged biases; a ratio ≈ ≤ 1 is expected, so D is the boundary case. |
| H-E2.2 | LC live overall < no-LC live overall | 3/3 | H-L2's band (M:10503). In A the margin is 4.7–6.1× (§0.4). |
| H-E2.3 | LC hindsight overall < no-LC hindsight overall | 3/3 | H-L3's band (M:10504). In A the margin is 9.1–15.4× (§0.4). |
| P-E2.4 | no-LC live lap-5 > 1.5 × lap-1 | 3/3 | P-L4's band (M:10505). Stored A: 3.86 / 4.50 / 2.94. no-LC landmarks are free after their pass in every condition, so drift growth should not depend on the condition. |
| P-E2.5 (graded) | the mean over 3 flights of LC live **lap-5** RMSE does not decrease along A → B → C → D (A = stored 0.0317 m) | ordering only | Experiment 2's known-map FGO live increases strictly A < B < C < D (0.020 / 0.026 / 0.054 / 0.083 m, N:526-529), driven by drift between re-observations. Lap 5 is the lap closest to the known-map regime, since by then every landmark has been re-observed. Lap 1 is dead reckoning in every condition, so it is excluded. One ordering check over 4 means (n = 3 each): PASS iff all three steps are non-decreasing. |

**Decision rules.** H-E2.1 is reported per condition: "PASS in B, C and D (9/9)" is the full E2 headline, and any
other outcome is reported per condition. H-E2.2, H-E2.3 and P-E2.4 are judged the same way. P-E2.5 is one check. A
condition with a missing flight is NOT MET for that condition.

**Null result.**
- If H-E2.1 FAILs in a condition, loop closure on that tag set does not bound the live drift lap on lap.
- If H-E2.2 or H-E2.3 FAILs, re-identification gives no accuracy gain on that tag set.
- Both are reported as findings on tag density, not as estimator faults.

**Comparison with the existing known-map results: DESCRIPTIVE ONLY.** No hypothesis, no verdict.
- **Quantities:** per flight, E2 LC live ÷ Experiment 2 FGO live, and E2 LC hindsight ÷ Experiment 2 FGO batch.
  - Experiment 2 values come from §0.4: N:526-529 and `json:expT/T_<c>_r<i>.json`.
  - For reference, A gives 2.69 / 2.52 / 3.99 (live) and 1.86 / 2.53 / 1.70 (hindsight), from the stored jsons.
- **The inputs differ, which is why this stays descriptive:**
  - Experiment 3/E2 uses **every central detection in `/tags/raw`**: on T_B_r1, 1313 detections of tags 0–3 over the
    whole bag.
  - Experiment 2 uses **`/tags/sent`, at most one fix per camera frame** (the best decision margin among central
    subset tags; `tag_bridge.py:88-99`): 908 fixes inside the window on T_B_r1 (`json:expT/T_B_r1.json:n_sent_in_window`).
- **The solvers differ:** fixed-lag 0.25 s with a whole-flight batch LM, against retained-history iSAM2 with a
  5-update hindsight.
- **The frames differ only by a translation:** world, against tag 0's frame (l_score.py:18-19, :28). The windows are
  identical.

---

## 2. E3: wrong re-identification

**Question.** How sensitive is the Experiment 3 loop-closure FGO, which has no robust weighting on tag factors, to
wrong tag ids? Wrong ids are injected at 1% and 5% of detections.

**Recordings.** `T_A_r1`, `T_A_r2`, `T_A_r3` (all 8 tags, as Experiment 3).

**Arms.**
- **(a) PRIMARY:** the FGO as-is, `--mode lc`. Rates 1% and 5%, seeds 0, 1 and 2: 18 replays.
- **(b) estimator variant (planned):** §2.6.
- **Clean reference:** rate 0 is the stored Experiment 3 LC result (§0.4). G0-L (§7) confirms it is reproducible at
  HEAD.

**Configuration: IDENTICAL to Experiment 3 (§0.2) plus the injection.**
```
... lc_fgo_replay.py T_A_r1 --mode lc --t-max 245 --tag-ids 0,1,2,3,4,5,6,7 \
    --mislabel-rate 0.01 --mislabel-seed 0 --out-root /home/makerspace/thesis_data/tier1
```
- The prefix is the same heavy.py wrapper as in E2.
- `--tag-ids 0,…,7` is a no-op filter on T_A (all 8 tags exist). It is required because it names the valid ids the
  replacement is drawn from; the estimator never reads the map.
- Output: `~/thesis_data/tier1/T_A_r1/lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0.01_s0/`.

### 2.1 Error model, exactly as ruled, plus the choices the ruling left open (FLAGGED for sign-off)

Implemented in `src/estimators/fgo/tier1_paths.py:Mislabeller`; the self-test is `python3 tier1_paths.py --selftest`.

1. **Per detection:** each central detection of a NON-gauge tag is mislabelled independently, with probability p ∈
   {0.01, 0.05}.
   - **Choice (flag 1):** p is the rate among *eligible* (non-gauge) detections. On T_A tag 0 is about 27% of central
     detections (653/2423 on T_A_r1), so the realised rate among *all* detections is about 0.73·p.
   - The alternative is to scale p by 1/0.73. It was not chosen because it would mislabel at a rate the ruling did not
     state.
   - Both realised rates are reported: `stats.json:tier1.mislabel.n_mislabelled / n_eligible_non_gauge / n_calls`.
2. **Replacement:** uniform over the OTHER valid non-gauge ids of the condition: for T_A, the 6 ids in {1..7} \ {true}.
3. **The anchor tag 0 is never mislabelled and never used as a replacement.**
   - The ruling says "anchor tag never mislabelled". Excluding 0 as a *replacement* as well is the stated
     interpretation (flag 2). Two reasons, both from the code:
     - (i) a relabel *to* 0 before the first true tag-0 sighting would trigger `start_isam` at a wrong pose
       (lc_fgo_replay.py:230-233);
     - (ii) a relabel to 0 later would tie the vehicle to the tight gauge prior (σ 1e-4, :199-201), which is a
       different and much stronger error.
   - Excluding it keeps the anchor time and the frame identical across arms. This is a checkable invariant: every E3
     run's `t_anchor` must equal the stored value (28.546 / 28.975 / 28.744 s;
     `T_A_r*/lc_fgo_lc_t245/stats.json:t_anchor`).
   - If the user prefers to allow relabel-to-0 *after* the anchor, it is a one-line change, and it must be ruled
     before any run.
4. **Seeds:** 0, 1 and 2, fixed now.
   - **Generator:** `numpy.random.default_rng(seed)` (PCG64).
   - **Draws:** TWO uniforms per central detection that passes the tag filter, in bag order, whether or not that
     detection is mislabelled. That includes tag-0 detections, whose draws are discarded. The two uniforms are u
     (mislabel iff u < p) and r (replacement = choices[floor(r · len(choices))]).
   - **Consequence:** for one seed the 1% set is NESTED in the 5% set, with identical replacement ids. The self-test
     verifies this.
5. **Applied AFTER the central-third filter** (flag 3). The central rule depends only on geometry, so the central set
   is the same either way. Drawing only for central detections makes p the rate on the detections that can actually
   become factors.
6. **Pre-anchor detections** get draws too, but have no effect: before the anchor only tag 0 is used, and tag 0 is
   never altered.
7. **Logged** (`stats.json:tier1`):
   - every injection as (time, true id, wrong id);
   - the count of landmarks whose FIRST sighting was a wrong id, `landmarks_first_sighting_mislabelled`. Such a
     landmark is initialised at a wrong position; this is a reported covariate.

**Expected magnitudes** (for the band derivations; JUDGEMENT-level arithmetic on stored inputs):
- **Number of wrong detections.** The stored post-anchor landmark factors are 2145 / 2057 / 2038
  (`stats.json:landmark_factors`). About 73% are non-gauge, giving ≈ 1,490–1,570 eligible. That means ≈ 15–16 wrong
  detections per flight at 1% and ≈ 75–78 at 5%.
- **Size of each wrong factor.** Each wrong id implies a vehicle position offset equal to the separation of the true
  and the reported tag, 3.0–8.5 m, which is 60–170 σ at σ = 0.05 m. It also implies a yaw offset of 15–165°, which is
  3–33 σ at 5°.
- **Pull on the vehicle track (non-robust least squares).** One wrong factor competes with the ~52 correct factors of
  the same pass (2145 factors / 41 passes, `T_A_r1/lc_fgo_nolc_t245/stats.json`). It therefore displaces that pass by
  roughly 3–8.5 m / 53 ≈ 0.06–0.16 m.
- **Pull on the landmark.** The wrong landmark shares the pull with about 270 factors (2145 / 8), so it moves by
  about 1–3 cm.

### 2.2 Metrics and frame

As Experiment 3 (§0.3): LC live and hindsight, overall and per lap, in tag 0's frame. The scorer is `l_score.py
--in-root … --suffix _t245_tags0-1-2-3-4-5-6-7_mis0.01_s0`, which writes `docs/thesis/tier1/scores/E3a_<trial>_<rate>_s<seed>.json`.

Covariates reported per run: the injection count, `landmarks_first_sighting_mislabelled`, `keyframe_failures` and
`t_anchor`.

### 2.3 Hypotheses, arm (a)

The unit is a run: (flight, seed), 9 runs per rate. References are the SAME flight's stored values (§0.4).

| id | criterion | band | derivation |
|---|---|---|---|
| **H-E3.1 (PRIMARY)** | at 1%: LC live overall < the same flight's stored no-LC live overall | 9/9 runs | Stored references: no-LC live 0.3494 / 0.2625 / 0.3608 m; clean LC 0.0574 / 0.0494 / 0.0760 m. At ≈ 15–16 wrong factors per flight, each displacing one pass by ≤ 0.16 m (§2.1), the RMSE should stay far below the no-LC level (≥ 0.26 m). The question is whether loop closure still beats no loop closure under 1% wrong ids. |
| H-E3.2 | at 1%: LC hindsight overall < the same flight's stored no-LC hindsight overall (0.2210 / 0.2451 / 0.2657) | 9/9 | Same argument, and the same stored source. |
| H-E3.3 | at 1%: LC live lap-5 ≤ 1.5 × lap-1 | 9/9 | H-L1's band (M:10501). Stored clean ratios 0.16–0.43. |
| P-E3.4 (JUDGEMENT) | at 1%: LC live overall ≤ 2 × the same flight's clean LC live | 9/9 | The **×2 is a JUDGEMENT**, flagged. The §2.1 arithmetic predicts about +20% (≈ 16 excursions of ≤ 0.16 m over ~12% of the window). ×2 allows for nonlinearity. |
| P-E3.5 | at 5%: the H-E3.1, H-E3.2 and H-E3.3 criteria | 9/9 each | Predicted to hold: ≈ 75–78 excursions, an RMSE of order 0.1 m, still below no-LC. They are labelled predictions rather than hypotheses because a non-robust iSAM2 with yaw residuals up to 33σ may fail nonlinearly. |
| P-E3.6 (dose–response) | per flight, the seed-mean LC live overall satisfies clean ≤ 1% ≤ 5% | 3/3 flights | The nesting (§2.1 item 4) means the 5% runs contain every 1% wrong factor plus more. |

**Decision rules.**
- Each criterion is judged on its count; one failing run is a FAIL, and every run is reported.
- A run whose `t_anchor` differs from the stored value is a **gate failure** for that run. It means the injection
  touched the anchor, which the design forbids. The run is excluded and reported, and the criterion becomes NOT MET if
  it lacks runs.

**Null result.**
- If H-E3.1 FAILs, 1% wrong ids are enough to destroy the loop-closure advantage of a non-robust FGO. That is a
  reportable robustness finding about the estimator as built.
- If every criterion PASSes at both rates, the FGO tolerates these error rates without robust weighting. That is
  equally reportable.

### 2.4 Arm (b): robust weighting on tag factors (ESTIMATOR VARIANT; planned)

**Label:** "keyframe FGO (loop closure), robust tag factors", an estimator VARIANT. It is not the Experiment 3
estimator and is not part of the primary hypotheses.
- **Kernel:** Cauchy, k = 2.385 (in units of σ), via `--tag-robust cauchy:2.385`.
  - It is applied to every **tag landmark factor**: `gtsam.noiseModel.Robust` wrapping the diagonal 0.05 / 0.05 m /
    5° model on the 3-vector Mahalanobis residual.
  - It is NOT applied to the gauge prior on L(0), nor to any IMU, flow or range factor.
- **Justification for the parameter:**
  - k = 2.385 is the project's own calibrated robust choice. F1 calibration chose Cauchy 2.385 over Huber and over other
    k on the calibration bags (M:8281-8298). The same record shows Huber diverging under persistent gross outliers
    (M:8297-8298).
  - k = 2.385 is also the textbook tuning constant that gives the Cauchy M-estimator 95% asymptotic efficiency under
    Gaussian noise. The project choice and the standard default therefore coincide.
  - It was calibrated for HEADING factors and is transferred, not re-calibrated, to tag factors. That is stated.
- **Runs:**
  - rate 0, as a control: one per flight, 3 runs;
  - rates 1% and 5% × seeds 0–2: 18 runs;
  - 21 replays in total.
  - The rate-0 control separates the kernel's own effect from its outlier rejection. It uses `--tag-ids 0,…,7
    --tag-robust cauchy:2.385` with no mislabel flags.
- **Criteria** (variant, reported beside arm (a), never merged into it):

| id | criterion | band | derivation |
|---|---|---|---|
| P-E3b.1 | at 5% (and at 1%): robust LC live overall ≤ arm (a) LC live overall, same flight and seed | 9/9 per rate | A wrong factor's whitened residual is ≥ 60σ (§2.1), so its Cauchy weight is 1/(1+(60/2.385)²) ≤ 0.0016. Its influence is cut by more than 600×, while correct factors keep a weight of ≥ 0.90 (next row). |
| P-E3b.2 (JUDGEMENT) | rate-0 control: robust LC live overall within ±10% of the stored clean LC live, same flight | 3/3 | Correct tag residuals are small: central-third position p95 is 40 mm, which is 0.8σ, and yaw p95 is 0.10° (N:540). The Cauchy weight at 0.8σ is 1/(1+(0.8/2.385)²) = 0.90. **±10% is a JUDGEMENT**, flagged. |

All other robust-arm numbers (hindsight, per lap, against no-LC) are **descriptive only**.

---

## 3. E4: live window sweep (Experiment 2 FGO)

**Question.**
- How do the Experiment 2 FGO's **live** accuracy and per-step compute change with the fixed-lag window: 0.25 s (the
  thesis configuration), 0.5, 1, 2 and 5 s?
- How does live accuracy at each window compare with the stored whole-flight batch (hindsight) result?

**Recordings.** All 12 T flights (§0.1). All are used because the window effect plausibly depends on the fix gap, and
the gap is the condition variable (median 4.3–46.3 s).

**Configuration: IDENTICAL to the Experiment 2 FGO, except for the window.**
- **Code:** `room_fgo_replay.py`, frozen at `2cc08a2` (`~/thesis_data/batches/final2_room_T/jobs.log`, line 1).
- **Frozen job:** `room_fgo_replay.py T_x_ry` with the thread variables at 1 and nice 10
  (`batches/final_rerun2/final2_room_T.fgo.jobs`).
- **Settings:** window 0.25 s, `BatchFixedLagSmoother`, LM ≤ 2, 30 Hz keyframes, the first-fix re-anchor, and the
  newest `/tags/sent` fix on the next keyframe with no gate (room_fgo_replay.py:36, :78, :112-118; M:10125-10145).
- **E4 command:**
```
... heavy.py "tier1 E4 T_A_r1 w1" -- /home/makerspace/venv-fgo/bin/python src/estimators/fgo/room_fgo_replay.py \
    T_A_r1 --no-batch --window 1.0 --out-root /home/makerspace/thesis_data/tier1
```
- **Output:** `~/thesis_data/tier1/T_A_r1/room_fgo_w1/{fgo_live.tum, stats.json, step_times.npz}`.
- **`--no-batch`** (an existing flag) saves about 2,650–2,970 s per run (`room_fgo/stats.json:batch_s`). It does not
  touch the smoother: `batch_record` only copies factors and estimates *after* `smoother.update`
  (HEAD `fgo_core.py:193-208`, `:221-222`).

**Gate G-E4 (identity).** For all 12 flights, the 0.25 s E4 run's `fgo_live.tum` must be **byte-identical** to the
stored `room_fgo/fgo_live.tum`. It is checked before any window ≠ 0.25 s is scored, and a failure stops E4 scoring.

**"Live" (as in Experiment 2).** `fgo.latest()`, the newest keyframe's estimate after each smoother update
(room_fgo_replay.py:136, :142-143). It is appended from the anchor on.

**Per-step time.**
- **Measurement, as stored:** `time.perf_counter_ns()` around the flow ground-proximity replacement plus
  `fgo.keyframe()`, every keyframe (room_fgo_replay.py:127-135). The stored stat is `step_median_ms` over all
  keyframes, :163.
- **Added in tier-1 runs:** p95; median and p95 after the anchor; the full per-step array (`step_times.npz`).
- **DIAGNOSTIC:** workstation Python, single-threaded BLAS, nice 19, **one job at a time**.
- The stored medians (17.3–18.8 ms) were measured with **6 jobs in parallel**, so they are not the timing reference.
  The reference is E4's own serial 0.25 s run.

**Metrics** (Experiment 2's scorer `eval/tag_score.py --in-root ~/thesis_data/tier1 --fgo-subdir room_fgo_w<W>`):
- FGO live horizontal RMSE in the lap window, in the world frame, with no alignment (tag_score.py header, :92-101);
- median, p95 and max;
- yaw error;
- per-gap mean error.

**Comparison with the batch.**
- Per flight and window, the fraction of the live-to-batch gap that is closed:
  `(live(0.25) − live(W)) / (live(0.25) − batch)`.
- `batch` is the stored whole-flight batch: `json:expT/T_*.json:tracks."FGO hindsight (whole-flight batch)".horiz_err_m.rmse`,
  N:526-529.
- The batch is not re-run per window. It is solved by LM (≤ 50 iterations, rel tol 1e-6) over the same factor set,
  which does not depend on the window apart from initial values (room_fgo_replay.py:164-170).

**Convergence of the 2-iteration LM cap.** The cap was verified only at 0.25 s and on the corridor (M:723-726; N:451-452:
max 0.11 m, RMS 0.029 m against full LM).
- **Extra runs:** `--lm-iters 10` at every window on `T_A_r1` (densest fixes) and `T_D_r1` (longest gaps). That is
  10 runs, with output `room_fgo_w<W>_lm10/`.
- **Reported per window:** the max and RMS live-position difference between cap 2 and cap 10, and the RMSE difference.
- **Flag:** "cap 2 NOT CONVERGED at W" iff the RMS difference is > 0.029 m, the value accepted at 0.25 s (N:452).
- These flags qualify E4's accuracy rows. They do not change any verdict.

**Hypotheses.**

| id | criterion | band | derivation |
|---|---|---|---|
| P-E4.1 | the median step time (after the anchor) increases strictly with W: 0.25 < 0.5 < 1 < 2 < 5 s | 12/12 flights | Direction only. The corridor sweep measured 27 / 48 / 96 ms at 0.25 / 0.5 / 1.0 s (N:444). That figure is DIAGNOSTIC and pre-thread-fix, so **only its direction is used, not its magnitude**. |
| P-E4.2 | the 33 ms deployability budget (M:707-721): the median is ≤ 33 ms at W = 0.25 s and > 33 ms at W ≥ 1 s | 12/12 at each | The stored room medians are 17.3–18.8 ms at 0.25 s (`room_fgo/stats.json:step_median_ms`, 6-parallel). The corridor ratio at 4× window was 3.56 (N:444), giving ≥ 62 ms at 1 s. W = 0.5 s (predicted ≈ 31–33 ms) sits on the budget: **descriptive only**. |
| — | live RMSE as a function of W | **DESCRIPTIVE ONLY** | No current stored basis exists. The corridor "ATE does not depend on window" evidence is superseded and pre-correction (N:457-458). Theory (stated, not banded): in a linear-Gaussian system the newest-state estimate of a fixed-lag smoother equals the filter's, whatever the window. Any change is therefore expected to come from relinearisation and the LM cap. |
| — | fraction of the live-to-batch gap closed | **DESCRIPTIVE ONLY** | As above. |

**Null result.**
- If live accuracy does not improve with the window, a longer window buys nothing live. That would confirm the
  0.25 s choice on this world too.
- Any P-E4.2 FAIL is reported as a compute finding.

---

## 4. E5: UKF with tag landmark states

**Design:** `docs/thesis/tier1/e5_design.md`. The design is written; the code is NOT. It will be new modules only, and
must not edit any file covered by the guard (§6).

**Question.**
- With tags at UNKNOWN positions, does a UKF that adds each tag to its state, re-identifies it, and smooths with RTS
  bound its live drift the way the Experiment 3 FGO does?
- How does it compare with that FGO?

**Recordings and arms: the same as Experiment 3.** `T_A_r1–r3`, LC and no-LC, cut at anchor + 245 s. That is 6
result replays.

**Validation gates (HARD).** No E5 result counts until all of these pass. The precise definitions are in
e5_design.md §8.
- **G0-UKF:** the frozen `room_ukf_replay.py`, run at HEAD with `UKF_OUT_ROOT=~/thesis_data/tier1/g0_ukf`, must
  reproduce the stored `room_ukf/{ukf_live,ukf_rts}.tum` byte-identically on 12/12 flights. The stored files are from
  commit `1b978de` (`~/thesis_data/batches/final_room_T/jobs.log`); the only UKF-path delta since then is the
  `geom=None` plumbing.
- **All V-E5 runs are validation runs.** They are uncut, anchored on the first `/tags/sent` fix as
  `room_ukf_replay.py:173-178` does, and fed `/tags/sent`, because the stored files cover the whole flight. The 245 s
  cut and the `/tags/raw` tag-0 anchor apply to result runs only.
- **V-E5a:** the E5 harness with the world-frame tag update (`ukf_core.update_tag` on `/tags/sent`) must reproduce the
  stored `room_ukf` byte-identically on 12/12 flights. The filter calls are ONLY `ukf_core` functions. The variable-n
  `ukf_lm.py` first enters at V-E5b.
- **V-E5b (the ruling's "known map reproduces the Experiment 2 UKF"):** the E5 tag-relative update with each landmark
  FIXED at its true map pose, fed `/tags/sent`, compared with V-E5a on 12/12 flights. All of the following must hold:
  - identical flow and range accept counts;
  - max per-sample horizontal position difference ≤ 1 mm, live and RTS;
  - per-flight RMSE (`tag_score`) equal to 0.1 mm (|Δ| ≤ 1e-4 m).
- **V-E5c:** the same comparison with the landmarks *augmented into the state*, initialised at the true map with
  variance 1e-10, against V-E5b, with the same tolerances.

**Metrics:** as Experiment 3 (§0.3).
```
l_score.py --in-root ~/thesis_data/tier1 --prefix lc_ukf --suffix _t245
```
- Live = the state after each predict step, as the Experiment 2 UKF (room_ukf_replay.py:182-185).
- Hindsight = RTS over the augmented state.

**Hypotheses** (3 flights each).

| id | criterion | band | derivation |
|---|---|---|---|
| **H-E5.1 (PRIMARY)** | UKF-LC live lap-5 ≤ 1.5 × lap-1 | 3/3 | H-L1's band (M:10501). In Experiment 2 D, the UKF's dead reckoning between single fixes gives a live RMSE of 0.1275–0.1332 m (§0.4); lap 1 is dead reckoning in LC. With every landmark known, the Experiment 2 UKF reaches 0.0356–0.0382 m in A. A lap-5 value near that, plus landmark uncertainty, against a lap 1 near 0.13 m, gives a ratio well under 1.5. |
| H-E5.2 | UKF-LC live overall < UKF-no-LC live overall | 3/3 | H-L2's band. In the FGO it held with a 4.7–6.1× margin (§0.4). |
| H-E5.3 | UKF-LC RTS overall < UKF-no-LC RTS overall | 3/3 | H-L3's band. |
| P-E5.4 | UKF-no-LC live lap-5 > 1.5 × lap-1 | 3/3 | P-L4's band. |
| P-E5.5 | UKF-LC live overall > stored FGO-LC live overall, same flight | 3/3 | Experiment 2 ordering: UKF live > FGO live in 12/12 flights, and in A by 1.67 / 1.85 / 2.01× (`json:expT`). |
| P-E5.6 | UKF-LC RTS overall > stored FGO-LC hindsight overall, same flight | 3/3 | Experiment 2 ordering: RTS-UKF > FGO batch in 12/12, A by 1.20 / 1.32 / 1.41×. Caveat: the FGO-LC hindsight is iSAM2 after 5 updates, not a batch LM. |

**Magnitudes** (ratios to the FGO, absolute RMSE) are **descriptive only**.

**Null result.**
- If H-E5.1 FAILs, a filter with landmark states does not bound drift on re-identification within this design. That
  is reportable as a filter-versus-graph finding, given the same measurements and noise.
- If P-E5.5 FAILs, the UKF matches or beats the FGO here, contrary to the Experiment 2 ordering. That is reported as
  such.

---

## 5. Output locations (chosen)

| what | where | why |
|---|---|---|
| raw replay outputs (TUM, stats.json, step times) | `~/thesis_data/tier1/<trial>/<run>/` | Data sits beside, but OUTSIDE, `~/thesis_data/trials`, so nothing can land in a frozen trial folder. `tier1_paths.resolve_out` refuses any other root, anything under `trials/`, and any existing non-empty output directory. |
| batch runner state | `~/thesis_data/batches/tier1_<exp>/` (new names) | `run_jobs_resumable.sh` appends to an existing batch name, so the frozen `final2_L`, `final2_room_T` and `final_room_T` must never be reused. The guard covers them. |
| scores (json per run) | `docs/thesis/tier1/scores/` | small, version-controlled; the scorers refuse `--json` outside the tier-1 locations |
| summary and provenance | `docs/thesis/tier1/numbers_tier1.md` | never mixed with `numbers.md` |
| guard manifests and reports | `docs/thesis/tier1/frozen_manifest_<ts>.json`, `…_verify_<ts>.json` | |

---

## 6. Checksum guard (`tools/tier1_checksum_guard.py`)

**When.**
1. **Stage 2 step 1:** `snapshot`, immediately before the first run. Run it from the main checkout, or with
   `--repo /home/makerspace/thesis_ws`. The default repo is the directory holding the script.
2. `verify` after each experiment's last run. This is cheap, about 10 s for about 1.7 GB.
3. A final `verify` after the last run of all.

**Any difference is STOP AND REPORT:** exit 1, a report listing every changed, missing or added file, and no further
runs until the user rules.

**Coverage**, listed exactly in the tool's docstring:
- **`trials_T`:** every file of every `~/thesis_data/trials/T_*` directory. That includes:
  - the bags, `imu_gaps.json`, `metadata.yaml` and `logs/`;
  - every `lc_fgo_*`, `room_fgo*` and `room_ukf*` folder;
  - the IMUGAP and ABORTED directories.
  These are the inputs and every frozen Experiment 2 and 3 output that a mis-pathed run could touch.
- **`trials_lc_other`:** `dsn_tex_r1/lc_fgo_notags` and `dsn_tex_r1/fgo_baseline`, the V-L pair.
- **`batches`:** `final2_L`, `final_L`, `final_rerun2`, `final2_room_T` and `final_room_T`. These hold the job lists
  and logs behind N:579-587 and the timing estimates in §8.
- **`results`:** `eval/results/expL`, `eval/results/expT` (N:§16.1 and §16.3 sources, the E2–E5 references) and
  `batches/final_rerun/room_T.jobs`.
- **`frozen_docs`:**
  - `docs/thesis/numbers.md`;
  - the frozen pack: `final_results_pack.pdf`, `final_results_pack_index.md`, `final_results_pack_corrections.md`
    and `headline_claims_before_after.md`;
  - `docs/thesis/figures_thesis/` and `docs/thesis/tables/`;
  - `plots/final_results_pack/` and `plots/supervisor_2026-10-08/`.
- **`run_code`:** every file the replays, scorers and runners execute, so that the code cannot change between the
  snapshot and the last run. Edits to a covered file during the experiments are therefore a stop-and-report.

**Flag 13: other workstreams are editing covered documents.** Since 2026-10-14 there have been 13 commits to
`numbers.md`, 3 to `headline_claims_before_after.md`, and many to `docs/thesis/figures_thesis/` and
`docs/thesis/tables/` (`b90c939` and `c1dd6ee` among them, today). A `verify` over a multi-day run could therefore stop
for edits unrelated to the replays. Three options:
- (a) Freeze those paths for the duration of the runs.
- (b) `snapshot --docs pack`: cover only the frozen pack files (`final_results_pack.pdf`, `_index.md`,
  `_corrections.md`) plus `plots/final_results_pack/` and `plots/supervisor_2026-10-08/`. None of these has changed
  since 2026-10-14. The edited documents are then left to their repository history.
- (c) Keep full coverage and accept stops that need a ruling.

The tools write only under the tier-1 roots, and the scorers refuse other `--json` targets, so (b) loses little.
**Recommendation: (b).**

**NOT covered, and why:**
- **`METHODOLOGY.md`:** the user will append the 2026-10-21 ruling. Covering it would make `verify` fail for a reason
  that is not a frozen-result change.
  - **Flag 4 for sign-off:** the alternative is to take the snapshot only after the append, and include it.
- **`docs/thesis/tier1/` and `~/thesis_data/tier1/`:** the outputs themselves.
- **Future E5 modules:** they do not exist at snapshot time.
  - A **supplementary snapshot** `snapshot --paths <E5 files> --out docs/thesis/tier1/e5_code_manifest_<ts>.json` is
    taken immediately before the first E5 validation run.
  - It is verified after the last E5 result run, so the validated code is the code that produced the results.

**Tested (Stage 1).** On a temporary copy (one `lc_fgo_lc_t245`, one `room_fgo` and one expL json), `verify`
returned IDENTICAL (exit 0). After the copy was edited, it reported CHANGED, MISSING and ADDED (exit 1). Details are
in the handover.

---

## 7. Gates before results (Stage 2, in order)

1. **Idle check:** `pgrep -fa '[a]rducopter'` and `[g]z sim` both empty, and no `~/thesis_data/FLIGHT_LOCK`.
   `heavy.py` re-checks this before every job.
2. **Snapshot** (§6).
3. **G0-L** (about 20 min). Two runs on `T_A_r1`:
   - (i) `--mode lc --t-max 245 --out-root ~/thesis_data/tier1/g0` (default configuration, redirected);
   - (ii) the same, plus `--tag-ids 0,1,2,3,4,5,6,7 --mislabel-rate 0 --mislabel-seed 0`, which exercises every new
     code path at neutral values.

   In both, `live.tum` and `hindsight.tum` must be **byte-identical** to the frozen
   `T_A_r1/lc_fgo_lc_t245/{live,hindsight}.tum`. LC replays were byte-reproducible before (M:10563). A failure stops
   E2 and E3.
4. **G0-UKF** (12 × about 1 min; E5 only) and **G-E4** (inside E4: its 0.25 s runs).
5. V-E5a/b/c (E5 only), after the supplementary E5 code snapshot.

---

## 8. Runtime plan, effort and compute against the 4 Nov lock

**The replay process rules found:**
- **M:10224:** no replay or other heavy job while any flight runs, and replays run single-threaded
  (`OMP/OPENBLAS/MKL/TBB_NUM_THREADS=1`).
- **`heavy.py`** (ruling 2026-10-08, its docstring): ONE CPU-heavy step at a time. Each step holds `BUILD_LOCK` and
  waits while `FLIGHT_LOCK`, `arducopter`, `gz sim` or another job's lock is present.
- **Conflict, reported:** the frozen Experiment 2 and 3 replays ran 6 in parallel through `run_jobs_resumable.sh`,
  without `heavy.py` (2026-10-10 jobs logs).

**Proposal (flag 5 for sign-off):** serial, one job at a time.
- Every job is wrapped in `heavy.py` and queued through `eval/run_jobs_resumable.sh <jobs> tier1_<exp> 1`.
- Thread variables at 1, with `TBB_NUM_THREADS=1` added as M:10224 states.
- Why serial:
  - (i) it obeys the heavy-job rule and leaves `BUILD_LOCK` coordination with other agents intact;
  - (ii) E4's per-step time is a measured metric and must not be contaminated by concurrent jobs;
  - (iii) the total fits comfortably before the lock (table below).
- If the user prefers to finish E2 no-LC sooner, parallel runs could be allowed for E2/E3/E5 only, never for E4.

**Stored wall times.** These are 6-parallel, single-thread figures; a serial run should be no slower.

| replay | stored wall per run | source |
|---|---|---|
| Experiment 3 LC (T_A) | 301 / 386 / 521 s | `~/thesis_data/batches/final2_L/jobs.log` |
| Experiment 3 no-LC (T_A, 41 landmarks) | 7,277 / 8,798 / 9,584 s | same |
| Experiment 2 FGO, live part only (wall − `batch_s`) | 165–189 s | `final2_room_T/jobs.log`, `room_fgo/stats.json:batch_s` |
| Experiment 2 UKF (live + RTS) | 57–63 s | `~/thesis_data/batches/final_room_T/jobs.log` |

**Compute estimate (upper bounds) and development effort.**

| item | replays | per-replay basis | serial compute | development |
|---|---|---|---|---|
| snapshot, G0-L, G0-UKF | 1 + 2 + 12 | 521 s; 63 s | 0.5 h | — |
| E2 LC | 9 | ≤ 521 s | 1.3 h | 0 (flags done) |
| E2 no-LC | 9 | ≤ 9,584 s (fewer landmarks in B–D: 21 / 11 / 6 passes against 41, so likely much less) | **≤ 24 h** | 0 |
| E3 arm (a) | 18 | ≤ 521 s | 2.6 h | 0 |
| E3 arm (b) | 21 | ≤ 521 s × 1.5 (robust relinearisation, JUDGEMENT) | 4.6 h | 0 |
| E4 main | 60 (12 × 5 W) | live time ≈ 30 s + ~9,000 steps × 18 ms × r(W); r = 1 / 1.78 / 3.56 / 7.1 / 17.8 (corridor ratio, extrapolated linearly beyond 1 s; DIAGNOSTIC) → about 190 / 320 / 610 / 1,180 / 2,910 s | 17.4 h | 0 (flags done) |
| E4 convergence (LM 10) | 10 | ≤ 5 × the cap-2 time | ≤ 14.5 h | 0 |
| E5 validation | 36 (V-E5a/b/c × 12) | ≤ 2 × 63 s | 1.3 h | **3 days**: implementation 1.5 d, validation and debugging 1 d, buffer 0.5 d |
| E5 results | 6 | LC ≤ 10 × 63 s (state ≤ 36); no-LC ≤ 3 × 63 s (finished-pass landmarks dropped; e5_design §6) | 0.3 h | (included) |
| scoring (all) | about 130 | seconds each | < 1 h | 0.5 d (`numbers_tier1.md`) |
| **total** | | | **≤ about 67 h serial** (about 2.8 days of machine time) | **about 3.5 days** |

**Proposed order** (E5 starts first, as the highest priority; compute runs underneath):
1. **Day 0, after sign-off:**
   - merge this branch, run the idle check, snapshot, then G0-L and G0-UKF;
   - **start E5 implementation**, which is coding plus light unit tests on synthetic data and no heavy jobs.
2. **The compute queue, serial, in the ruling's order:** E2 LC → E2 no-LC → E3 (a) → E3 (b) → E4 main → E4
   convergence.
   - E2 no-LC is the long pole, at ≤ 24 h.
   - E5 development overlaps it completely.
3. **When the E5 code is ready (about day 3):** take the supplementary E5 code snapshot, then insert V-E5a/b/c and the
   E5 result runs at the **next job boundary**. They jump the queue (one heavy job at a time still holds), because E5
   is the highest-priority experiment.
4. **Earliest finish:**
   - all compute about day 3–4 (25–26 Oct, if signed off on 22 Oct);
   - E5 results about day 4;
   - scoring and `numbers_tier1.md` about day 5.
   - That leaves about 8 days of buffer before the 4 Nov lock.
5. **At the lock (2026-11-04 23:59 AEDT):**
   - any replay not finished is killed;
   - outputs are written only at the end of a replay (lc_fgo_replay.py:273-291), so a killed run leaves nothing to
     score;
   - it is reported as **not run** (future work), and its criteria become NOT MET.
   - Scoring of runs that completed before the lock may finish after it, as analysis only. **Flag 6:** the user may
     prefer scoring to be inside the lock as well.

---

## 9. Results rules

- Every number goes in `docs/thesis/tier1/numbers_tier1.md`, with the same exact cross-check convention as
  `numbers.md`: a value, its unit, a status and a source (`json:` path and key, or `tier1:` run directory).
- Nothing goes into `numbers.md`, `METHODOLOGY.md`, the frozen pack or `eval/figs_thesis*.py`.
- Every result is labelled **"extension experiment, pre-registered (2026-10-21)"**.
- Deviations from this document are recorded in `numbers_tier1.md` §Deviations *before* the affected result is read.

## 10. Choices flagged for sign-off (not fixed by the rulings)

1. The E3 rate counts non-gauge detections. The realised all-detection rate is about 0.73 p; both are reported.
2. Tag 0 is excluded as a replacement as well as a source.
3. Mislabels are applied after the central filter.
4. METHODOLOGY.md is excluded from the guard, or the snapshot is taken after the user's append.
5. Serial execution under `heavy.py` (about 67 h upper bound), rather than the 6-parallel precedent.
6. Scoring of completed runs may finish after the lock.
7. E4 does not re-run the batch per window; it compares against the stored batch.
8. The E4 convergence check uses LM cap 10 on T_A_r1 and T_D_r1 only.
9. The JUDGEMENT bands: P-E3.4 (×2), P-E3b.2 (±10%), and the E3 (b) cost factor 1.5.
10. The E4 hypotheses: timing only. Accuracy is descriptive.
11. E5 design choices (e5_design.md §10): a joint augmented sigma set; dropping finished-pass landmarks in no-LC;
    landmark yaw as an angle state.
12. The lock clock time (23:59 AEDT on 4 Nov).
13. Guard coverage of the actively edited thesis documents (§6): (a) freeze them, (b) `--docs pack` (recommended), or
    (c) full coverage.
