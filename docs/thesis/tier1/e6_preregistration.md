# E6: map reuse ("map once, fly again"): pre-registration

**Extension experiment, pre-registered.** This document fixes the question, the Step 0 answers, the design, the
predictions with their bands and pass rules, the gates and the run list BEFORE any E6 run. It mirrors
`preregistration.md` (E2–E5) in format and in its §0 rules, which apply here unless this document says otherwise.

- **Status:** written 2026-10-31 (AEDT) on branch `e6-map-reuse`, cut from `fwd-camera` at `1519f4e`. It is committed
  together with the E6 code and BEFORE any E6 run: no gate, flight, replay or scorer run of E6 had started when it was
  committed. (Read-only work done before the commit, all on stored data: the `e6_map.py --selftest` round-off check,
  the stored-map errors of §1.4, and the baseline guard verify. None of these is a result run.)
- **Rulings this implements:** the user's E6 instruction of 2026-10-31 (quoted in the handover), under the standing
  decision rules of 2026-10-23 (`decisions_log.md`). Decisions taken while writing this are D69–D82 in
  `decisions_log.md` on this branch.
- **Lock:** results lock **2026-11-04 23:59 AEDT**. If the runs cannot finish by **2026-11-04 12:00 AEDT**, E6 stops at
  the last complete stage and reports (user ruling). A run not finished at a stop or at the lock is **NOT RUN**
  (`preregistration.md` §0.5).
- **Results location:** numbers go to `docs/thesis/tier1/e6_numbers.md` during the run and into `numbers_tier1.md` only
  at merge time (user ruling, concurrency). Nothing in `numbers.md`, the frozen pack, any existing result file or any
  figure or table is touched.
- **Labels:** every E6 result is labelled "extension experiment E6, pre-registered (2026-10-31)".
- **Citation keys:** as `preregistration.md`. `N:` = `docs/thesis/numbers.md` line; `T1:` = `docs/thesis/tier1/
  numbers_tier1.md` line; `json:` = a file under `eval/results/` or `docs/thesis/tier1/scores/`.
- **Thesis names:** Experiment 2 = repo "T" (known tags); Experiment 3 = repo "L" (loop closure); E5 = the landmark
  UKF.

---

## 1. Question and Step 0

**Question (user, verbatim).** "Can a tag map from one flight's full-trajectory (hindsight) solve replace surveying the
tags for later flights, and does the FGO's map do better than a filter's?"

### 1.1 Step 0 item 1: cost, UKF and FGO (EKF3 excluded: it needs Replay tooling)

All figures are wall times from stored logs; DIAGNOSTIC, workstation Python, one job at a time unless marked.

| job | per run | source |
|---|---|---|
| Experiment 2 UKF replay, live + RTS (`room_ukf_replay.py`) | 50.6–54.4 s (serial) | `stage2_gates.md` §3 G0-UKF |
| Experiment 2 FGO replay, live only (`room_fgo_replay.py --no-batch`, 0.25 s) | 130.7–154.8 s (serial) | `stage2_gates.md` §3 G-E4 |
| Experiment 2 FGO whole-flight batch LM (hindsight) | **no serial measurement**; stored 2,961 s on T_A_r1 at 6-parallel (`batch_s`); final2 wall 3,147–3,152 s for T_A (live + batch, 6-parallel) | `~/thesis_data/trials/T_A_r1/room_fgo/stats.json:batch_s`; `~/thesis_data/batches/final2_room_T/jobs.log` |
| Experiment 3 LC replay (`lc_fgo_replay.py --mode lc --t-max 245`) | 127.2–129.7 s serial (T_A_r1); stored 6-parallel 301–521 s | `stage2_gates.md` §3, §4 |
| E5 landmark UKF, LC (`lc_ukf_replay.py --mode lc`) | 115.6–117.6 s (serial) | `e5_results.md` §4 |
| A T flight (`run_trial.sh`, 5 laps, 240 s route) | 314–315 s wall per flight | `~/thesis_data/batches/expT_refly_T_A_r3/trials.log`; `expT_console.log` |

**E6 cost (planning; upper bounds use the stored 6-parallel batch figure, since no serial batch figure exists):**
- per test flight and map: UKF ≈ 55 s; FGO live + batch ≤ 155 + 2,961 s ≈ 52 min (upper bound; a serial run is
  expected to be faster, as every other serial-vs-parallel comparison here was, about 0.42–0.43× on the LC replay);
- 3 test flights × 2 maps: UKF ≈ 6 min; FGO ≤ 5.2 h. The surveyed arm (i) and no-map arm (iv) cost nothing (§1.4).

### 1.2 Step 0 item 2: one frame for every arm, with no fitted alignment

**The world frame (Gazebo ENU), reached from tag 0's frame by a fixed, registered translation.**
- Experiment 2 (arm (i)) estimates in the world frame: the fixes on `/tags/sent` are world poses
  (`tag_bridge.py:87-99`), and `eval/tag_score.py` scores against world ground truth with no alignment.
- The hindsight maps (arms (ii), (iii)) and the no-map arm (iv) are in **tag 0's frame**: the loop-closure replays
  anchor on the first central sighting of the gauge tag 0 and hold its landmark at the origin (`lc_fgo_replay.py`,
  gauge prior σ 1e-4 and stored L(0) within 4e-10 of the origin; E5 holds it exactly, `e5_design.md` §5).
- **Transform:** world = tag-0 frame + p₀, with p₀ = (−3, −3) m, tag 0's surveyed position in `sim/worlds/
  room_tags_map.json`, and tag 0's surveyed yaw 0° (asserted in code). It is a pure translation, identical for every
  run, taken from the survey of ONE tag. It is not fitted to any estimate. It is the same mapping `eval/l_score.py:28`
  applies to ground truth (Experiment 3 subtracts p₀ from ground truth; E6 adds p₀ to the estimate, which gives the same
  error to round-off; scorer gate S-E6, §7).
- **Stated consequence:** arms (ii) and (iii) use one surveyed tag to register the frame. Tag 0's entry in every
  supplied map is its surveyed pose by construction, so every tag-0 fix, including the anchoring one, is identical in
  arms (i), (ii) and (iii). "Replacing the survey" in E6 means replacing the survey of the other 7 tags.

### 1.3 Step 0 item 3: a new mapping flight on a different route, within half a day? YES

**Decision (D71): new mapping flights, out of sample.**
- **Route:** a figure of eight through the tag room (two half-squares flown in opposite senses, sharing the mid-line,
  §3.1). It is flown with the existing `HPROFILE` "move" segments of `fly_trial.py` (moving position setpoint with
  velocity feed-forward, yaw held, on simulator truth as every T flight). **No harness code changes** (D72).
- **Time, from stored per-flight wall times:** a T flight took 314–315 s wall for a 240 s route; a 216 s figure-of-eight
  flight is therefore about 5.5 min. One verification flight (one circuit, about 3 min wall) + three mapping flights
  (about 17 min) + the IMU gap check + six map replays (3 × ~130 s LC FGO + 3 × ~117 s landmark UKF, about 13 min)
  ≈ **1 h including checks**, well inside the 4–5 h half-day budget.
- So the map source is a NEW flight on a DIFFERENT route, and every test flight (T_A_r1–r3) is out of sample. The
  same-route caveat does not apply; the rotation fallback (a T_A recording as the source) is not used.
- **Fallback, decided now (D73):** if the verification flight shows any tag with no central detection in the circuit
  (§7, V-F), the route falls back to **reversed laps** (5 laps E→N→W→S of the same 6 m square, `HPROFILE`, same
  speed and height), still a new flight and out of sample, and the reason is logged.

### 1.4 Step 0 item 4: existing results that already cover an arm

| arm | estimator, track | covered by | values (T_A_r1 / r2 / r3, m) | citation |
|---|---|---|---|---|
| (i) surveyed map | FGO live | Experiment 2, condition A | 0.0214 / 0.0196 / 0.0190 | `json:expT/T_A_r*.json:tracks."FGO live".horiz_err_m.rmse`; N:526 (mean 0.020) |
| (i) | FGO hindsight (whole-flight batch) | Experiment 2 | 0.0106 / 0.0107 / 0.0101 | `…"FGO hindsight (whole-flight batch)"…`; N:526 (0.010) |
| (i) | UKF live | Experiment 2 | 0.0356 / 0.0362 / 0.0382 | `…"UKF live"…`; N:526 (0.037) |
| (i) | UKF hindsight (RTS) | Experiment 2 | 0.0128 / 0.0141 / 0.0142 | `…"RTS-UKF (hindsight)"…`; N:526 (0.014) |
| (iv) no map, loop closure online | FGO live (Experiment 3 keyframe FGO, LC) | Experiment 3 | overall 0.0574 / 0.0494 / 0.0760; lap 1 0.1063 / 0.0818 / 0.1608 | `json:expL/T_A_r*_t245.json:tracks."lc live"`; N:573 |
| (iv) | FGO hindsight (iSAM2 + 5 updates) | Experiment 3 | 0.0198 / 0.0270 / 0.0172 | `…"lc hindsight"…`; N:573 |
| (iv) | UKF live (E5 landmark UKF, LC) | E5 | overall 0.1193 / 0.0911 / 0.1335; lap 1 0.2240 / 0.1560 / 0.2565 | `json:scores/e5_T_A_r*.json:tracks."lc live"`; T1:534-554 |
| (iv) | UKF hindsight (RTS) | E5 | 0.0445 / 0.0461 / 0.0552 | `…"lc hindsight"…`; T1:536-552 |
| map error (in sample, same route) | FGO map / UKF map from each T_A flight itself | Experiment 3 `landmarks_final`, E5 `landmarks_in_state_final_filtered` | position RMS over the 7 non-gauge tags: FGO 0.0204 / 0.0269 / 0.0152; UKF 0.0420 / 0.0432 / 0.0526 | computed read-only 2026-10-31 by `eval/e6_maps.py T_A_r* --errors-only` (stored stats.json files; the index→tag invariants held on all three) |

- **Arms (ii) and (iii) are not covered by any existing result:** no stored run uses an estimated map as known tags.
- **Arm (i) and arm (iv) are NOT re-run.** They are re-scored, read only, by the one E6 scorer (§4) for per-lap values
  in the common frame; the scorer must reproduce every cited value (S-E6, §7).
- The in-sample map errors above are used only to set the direction of P1 (§5). They are not E6 maps.

---

## 2. What "a supplied map" means in the replays (fixed known landmarks)

- **Experiment 2 replays, unchanged except the map.** `room_ukf_replay.py` (thesis UKF) and `room_fgo_replay.py` (thesis
  FGO: window 0.25 s, 2 LM iterations, 30 Hz keyframes, plus the whole-flight batch LM as hindsight) consume
  `/tags/sent`: at most one fix per camera frame (the central-third detection with the largest decision margin), the
  vehicle (x, y, yaw) in the world frame computed by the bridge with the tag's SURVEYED pose.
- **New flag `--tag-map FILE --tag-map-name NAME`** (both replays; `src/estimators/e6_map.py`). It re-expresses every
  fix with the supplied pose of the tag named in its `frame_id`:
  p′ = t′ⱼ + Rz(θ′ⱼ − θⱼ)(p − tⱼ), ψ′ = ψ + (θ′ⱼ − θⱼ), with (tⱼ, θⱼ) surveyed and (t′ⱼ, θ′ⱼ) supplied.
  - Which detection is sent never depends on the map values, so this is exactly what a bridge holding the supplied
    map would have sent. For a tag flat on the floor it is exact: the self-test on T_A_r1 (2,423 fixes, a random
    ±0.2 m / ±5° perturbed map) matched `tag_measure.vehicle_pose` recomputed from `/tags/raw` to 1.3e-15
    (`e6_map.py --selftest`).
  - **The supplied map is treated exactly as the surveyed map: fixed, known landmarks.** The tag noise is unchanged
    (σ_pos 0.05 m, σ_yaw 5°, `measurement_models.TAG_SIGMA_POS/YAW`); no map uncertainty is added and nothing is
    re-estimated. `ROOM_TAG_SIGMA_POS`, `--gnss`, `--window`, `--lm-iters` and the diagnostic options are refused with
    the flag.
  - Output only under `~/thesis_data/tier1/<trial>/room_{ukf,fgo}_e6_<NAME>/`; never under `~/thesis_data/trials`,
    never over a non-empty directory. Provenance (map sha256, per-tag shift) in `stats.json:e6`.
  - **Without the flag the code path is unchanged:** gates G0-UKF and G-E4′ (§7) must be byte-identical.

---

## 3. Map production

### 3.1 Mapping flights (new; out of sample)

- **World and configuration:** `room_tags`, exactly the T_A configuration: `TAG_BRIDGE=1`, `TAG_IDS=all`,
  `TAG_SIGMA_POS=0.05`, `EXTRA_PARM_FILES=tags_extnav.parm`, the same `EXPECT_OVERRIDE`, loopback only, 2.0 m, 0.5 m/s,
  yaw held north, flown open loop on simulator truth (`tools/run_expT_refly.sh` minus `LAPS`, plus `HPROFILE`).
- **Route (`docs/thesis/tier1/e6/fig8_3c_profile.json`):** from the spawn over tag 0 at world (−3, −3), one circuit is
  E 6 m (y = −3: tags 7, 3) → N 3 m (x = 3: tag 6) → W 6 m along the mid-line (y = 0: tag 4) → N 3 m (x = −3: tag 1) →
  E 6 m (y = 3: tags 5, 2) → S 3 m (x = 3: tag 6) → W 6 m along the mid-line (tag 4) → S 3 m (x = −3: tag 0). 36 m,
  72 s per circuit; **3 circuits, 216 s**. Every tag lies on the route; tags 4 and 6 are passed twice per circuit, the
  others once. The T laps never flew the mid-line or the bottom edge eastbound.
- **Names (no `T_` prefix: the guard globs `T_*`, §8):** `E6V_fig8_check` (verification, one circuit,
  `fig8_check_profile.json`; NOT result data), `E6M_fig8_r1`, `E6M_fig8_r2`, `E6M_fig8_r3` (mapping).
- **IMU gap rule:** `eval/imu_gap_check.py <trial> --write` on every new trial before any replay. An "unusable" verdict
  means the flight is re-flown under a new name (`…_r<k>b`), as in Experiment 2; the old directory is kept.
- **Pairing, fixed now (D74):** the map from `E6M_fig8_rk` is used on test flight `T_A_rk` (k = 1, 2, 3). Every test
  flight gets an independent map; n = 3 for every prediction.

### 3.2 Map sources (both from the same mapping flight)

| map | estimator and track | command (output under `~/thesis_data/tier1/<mapping trial>/`) |
|---|---|---|
| **(a) FGO map** | Experiment 3 keyframe FGO, hindsight landmark estimate `stats.json:landmarks_final` (iSAM2's full-graph estimate after 5 extra updates: the Experiment 3 hindsight, DEVIATION M:10557, not an LM batch; the same mapping as S-E5.6) | `lc_fgo_replay.py <m> --mode lc --t-max 245 --out-root ~/thesis_data/tier1` (frozen Experiment 3 configuration, `preregistration.md` §0.2; venv-fgo) |
| **(b) UKF map** | E5 landmark UKF, LC, landmarks `stats.json:landmarks_in_state_final_filtered`. A static landmark (identity transition, zero process noise, never removed in LC) has its RTS-smoothed estimate equal to its filtered estimate at the final node, so this is the RTS-smoothed map | `lc_ukf_replay.py <m> --mode lc` (default out-root `~/thesis_data/tier1`, t-max 245; venv-evo) |

- **Expected exit 3 from `lc_ukf_replay.py` (D75):** its §5.3 invariant reads the stored FGO run at
  `~/thesis_data/trials/<m>/lc_fgo_lc_t245/`, which does not exist for a new flight; it writes every output and then
  exits 3 with reason "no stored FGO stats". The same invariant is checked by `eval/e6_maps.py` against the tier-1 FGO
  map run instead: `t_anchor` equal in both replays and equal to the first central tag-0 detection, landmark count 8 in
  both, and the FGO landmark index → tag id mapping (recomputed from `/tags/raw` with the replay's own rules) equal to
  the landmark UKF's recorded mapping. A failure means no map is written for that flight (gate MAP-INV, §7).
- **Map files:** `eval/e6_maps.py <m> --fgo-dir … --ukf-dir … --out-dir ~/thesis_data/tier1/e6/maps/<m>/` writes
  `map_fgo.json`, `map_ukf.json` (the `room_tags_map.json` layout, world frame, tag z/roll/pitch surveyed, tag 0
  surveyed by definition) and `map_errors.json`.
- **Map error against truth (reported for each map):** for each of the 7 non-gauge tags, horizontal position error
  |p′ⱼ − pⱼ| (m) and yaw error (°). Summary: **position RMS over the 7 tags (the P1 metric)**, max, mean; yaw RMS and
  max (descriptive).

---

## 4. Test runs, arms and scoring

**Test flights:** `T_A_r1`, `T_A_r2`, `T_A_r3` (condition A, all 8 tags sent; Experiment 2 style; tag noise unchanged).

| arm | map | UKF (live + RTS) | FGO (live + whole-flight batch) | status |
|---|---|---|---|---|
| (i) surveyed | `room_tags_map.json` | stored `trials/T_A_rk/room_ukf/` | stored `trials/T_A_rk/room_fgo/` | covered (§1.4); re-scored only |
| (ii) FGO map | `e6/maps/E6M_fig8_rk/map_fgo.json` | `room_ukf_replay.py T_A_rk --tag-map … --tag-map-name fgomap_E6M_fig8_rk` (UKF_OUT_ROOT=~/thesis_data/tier1) | `room_fgo_replay.py T_A_rk --out-root ~/thesis_data/tier1 --tag-map … --tag-map-name fgomap_E6M_fig8_rk` | NEW, 6 runs |
| (iii) UKF map | `e6/maps/E6M_fig8_rk/map_ukf.json` | same, `--tag-map-name ukfmap_E6M_fig8_rk` | same | NEW, 6 runs |
| (iv) no map, LC online | none (landmarks estimated online) | stored E5 `tier1/T_A_rk/lc_ukf_lc_t245/` | stored Experiment 3 `trials/T_A_rk/lc_fgo_lc_t245/` | covered (§1.4); re-scored only |

**Scorer:** `eval/e6_score.py T_A_rk --fgo-map-name fgomap_E6M_fig8_rk --ukf-map-name ukfmap_E6M_fig8_rk --json
docs/thesis/tier1/scores/e6_T_A_rk.json` (venv-evo). One scorer, one frame (world), no alignment:
- lap window and laps: `eval/l_score.py`'s code (first `LAP 0 LEG 0 START` to `LAPS END`, SITL clock mapped to the bag
  clock by the `/imu/time_ref` lower envelope), the same window as `eval/tag_score.py` (29.52–269.57 s on T_A_r1);
- per track: horizontal RMSE over the window, max, per-lap RMSE laps 1–5, lap-5 / lap-1;
- verdicts on the unrounded json values; values quoted to 4 dp in m (`preregistration.md` §0.3);
- verdict script: `eval/e6_verdicts.py` (written in Stage 1 from §5 as worded and committed with this document, D82; it writes `docs/thesis/tier1/scores/e6_verdicts.json`).

**Stated differences between arms (not removed):**
- Arms (i)–(iii) use the thesis estimators on `/tags/sent` (one fix per frame). Arm (iv) uses the separate
  loop-closure estimators (iSAM2 keyframe FGO; landmark UKF) on every central `/tags/raw` detection. The
  `preregistration.md` §1 E2 comparison ruled this pairing descriptive-only; E6 keeps P4 as the user worded it, with
  this confound stated (§10).
- Arm (iv) runs are cut at anchor + 245 s; the lap window ends earlier on every T_A flight (269.57 s < 28.55 + 245 s on
  T_A_r1), so the window is the same.

---

## 5. Predictions, bands and pass rules

**General.** Each criterion is judged on 3/3 runs that completed and passed their gates (`preregistration.md` §0.5:
PASS / FAIL / NOT MET / NOT RUN; no early decisions; no re-runs to change a verdict; ambiguity read against the
prediction). **P2–P4 are judged separately for each test estimator (UKF and FGO), 3/3 each.** The headline for a
prediction reads "PASS (both)", "FAIL (both)" or the split, e.g. "PASS for the FGO, FAIL for the UKF"; there is no
pooling across estimators. Hindsight tracks carry no verdict (descriptive, §6). A FAIL is a result, reported with the
same prominence as a PASS.

| id | criterion (per estimator for P2–P4) | band and pass rule | derivation (stored only) |
|---|---|---|---|
| **P1** | The FGO map has lower landmark error than the UKF map | PASS iff FGO-map position RMS < UKF-map position RMS on **3/3 mapping flights** (strict, unrounded) | **Direction only.** From E5: FGO hindsight 1.7–3.2× better (user). On the stored in-sample T_A maps (§1.4) the direction held 3/3: UKF ÷ FGO = 2.06 / 1.61 / 3.46; the smallest margin, 0.0163 m (T_A_r2), exceeds the repeat range of either map (FGO 0.0117 m, UKF 0.0106 m). A magnitude band is not meaningful at n = 3 for a new route with fewer re-observations per tag; the ratio is reported descriptively. |
| **P2** | Live error on the FGO map is within the band of the surveyed map | PASS iff, on **3/3 test flights**, the live RMSE on the FGO map lies inside the surveyed-map band [min − R, max + R] of the same estimator | **Band from the stored repeat spread of arm (i) live, n = 3.** R = max − min of the three T_A values (`json:expT`, unrounded). **FGO:** 0.019026 / 0.019636 / 0.021360 → R = 0.002335, band **[0.016691, 0.023695] m** (0.0167–0.0237). **UKF:** 0.035602 / 0.036233 / 0.038193 → R = 0.002591, band **[0.033011, 0.040785] m** (0.0330–0.0408). Method: with n = 3 the range is the only spread estimate; the band extends the observed repeat interval by one range on each side (for normal repeats E[R] ≈ 1.69σ). **The width "one R on each side" is judgement, not derived from data** (the simplest symmetric extension; no multiplier was tuned). The band is two-sided, scored literally: a value below the lower edge is outside the band (read against the prediction) and is reported. |
| **P3** | Live error on the FGO map is lower than on the UKF map | PASS iff live RMSE (FGO map) < live RMSE (UKF map) on **3/3 test flights** (paired: same flight, same estimator; strict, unrounded) | **Direction only; no spread band is needed:** the two arms are deterministic replays of the same recording with the same estimator, so their difference is caused by the maps alone (there is no run-to-run noise to band). The expected size is set by the map errors (stored in-sample difference 0.016–0.037 m RMS, §1.4), which is comparable to the live error itself. |
| **P4** | Live error on the FGO map is lower than with no map (iv), at least on the first lap | PASS iff **lap-1** live RMSE (FGO map) < lap-1 live RMSE (arm (iv)) on **3/3 test flights** (paired by flight; the FGO estimator is compared with the stored Experiment 3 FGO, the UKF with the stored E5 landmark UKF) | **Direction only.** Stored arm (iv) lap 1 is dead reckoning from the anchor (every tag is new on lap 1): FGO 0.1063 / 0.0818 / 0.1608 m; UKF 0.2240 / 0.1560 / 0.2565 m (§1.4). Arm (i)'s overall live (0.019–0.038 m) is 2–8× below these, so a map arm fails only if the map degrades lap 1 by about that much. The **overall-window** comparison (map vs arm (iv), live) is reported for every flight as **P4-overall, descriptive** (the user's "at least on the first lap"): no verdict, direction stated. |

**What would read against the hypothesis (written before the runs).**
- P2 FAIL with P3 PASS: the FGO map is the better map but not survey-grade at this noise level.
- P1 PASS with P3 FAIL: lower landmark RMS does not translate into lower live error (for example, errors concentrated on
  frequently seen tags).
- P4 FAIL: a supplied hindsight map is worse on lap 1 than dead reckoning to the first re-observation.

---

## 6. Descriptive outputs (no verdict)

- Each map's per-tag errors, position RMS, max, mean, yaw RMS and max (3 mapping flights × 2 maps).
- For every test flight and estimator: live and hindsight overall RMSE, max, per-lap RMSE and lap-5 / lap-1, for arms
  (i)–(iv).
- Ratios per flight: map arm ÷ surveyed (live, hindsight); FGO map ÷ UKF map; map arm ÷ arm (iv) overall (P4-overall).
- The stored in-sample T_A map errors beside the out-of-sample mapping-flight map errors (route effect, descriptive).
- Keyframe failures (`stats.json:keyframe_failures`), reported, never an exclusion.

---

## 7. Gates (in order; a gate failure stops what it guards, before any prediction is scored)

| gate | what | pass rule | cost |
|---|---|---|---|
| **Idle** | no `arducopter`, no `gz sim`, no `FLIGHT_LOCK`/`BUILD_LOCK` of another job, no plot job (`pgrep` for `figs_`, `figs_walkthrough`, `heavy.py`); recorded before every job | all clear | — |
| **Guard (before)** | `tools/tier1_checksum_guard.py verify` against `frozen_manifest_20261022T002851.json` | IDENTICAL | 30 s |
| **G0-UKF** (flag unset) | `room_ukf_replay.py <trial>` from this branch, `UKF_OUT_ROOT=~/thesis_data/tier1/e6_g0_ukf`, 12 flights | `ukf_live.tum`, `ukf_rts.tum` byte-identical to the stored `room_ukf/` 12/12 (as `stage2_gates.md` G0-UKF) | ≈ 11 min |
| **G-E4′** (flag unset) | `room_fgo_replay.py <trial> --no-batch --window 0.25 --out-root ~/thesis_data/tier1/e6_g0_fgo`, 12 flights | `fgo_live.tum` byte-identical to the stored `room_fgo/fgo_live.tum` 12/12 (as `stage2_gates.md` G-E4); `t_anchor`, `n_tag_factors` equal | ≈ 28 min |
| **V-E6** (flag set to the TRUE map) | T_A_r1–r3: UKF (`--tag-map sim/worlds/room_tags_map.json --tag-map-name truemap`, `UKF_OUT_ROOT=~/thesis_data/tier1/e6_val`) and FGO live (`--no-batch`, same root) | `eval/e6_val_compare.py`: rows 1:1, `t_anchor` and tag count equal, RMS ≤ 1.0 mm and max ≤ 2.0 mm in the window against the stored tracks, every track (V-E5b's tolerance and reason, `e5_design.md` §8.4); byte identity reported | ≈ 10 min |
| **S-E6** (scorer) | `eval/e6_score.py T_A_rk --stored-only` | the re-scored arms (i) and (iv) reproduce every stored value (expT RMSE; expL / E5 RMSE, max, per-lap) and the stored windows to ≤ 1e-9 m | seconds |
| **V-F** (verification flight `E6V_fig8_check`, one circuit; NOT result data) | flight completes; `/tags/raw`, `/tags/sent`, `/imu/time_ref`, `/ground_truth/pose` recorded; imu_gap_check not "unusable"; every one of the 8 tags has ≥ 1 central detection; route followed (GT within 0.5 m of each leg line at mid-leg) | all hold; otherwise D73 fallback (reversed laps) and a new verification flight | ≈ 10 min |
| **IMU** | `imu_gap_check --write` on every mapping flight | "ok" or "trim"; "unusable" → re-fly (§3.1) | seconds |
| **MAP-INV** | `eval/e6_maps.py` invariants per mapping flight (§3.2) | all hold; otherwise no map from that flight, the flight's pair is NOT MET unless a re-flight (new name) passes before the lock | seconds |
| **Guard (after each stage)** | as before | IDENTICAL | 30 s |

**The guard and new data.** The guard re-expands `~/thesis_data/trials/T_*` and all of `~/thesis_data/batches/` (and
the main checkout's `batches/`), so a new `T_*` trial or a new batch folder would read as ADDED (a STOP). E6 therefore
names its trials without `T_`, keeps batch-runner state under `~/thesis_data/tier1/e6/batches/`
(`run_resumable_batch.sh` with `BATCHES_DIR`), and keeps job state under `~/thesis_data/tier1/e6/`. A new non-`T_`
trial folder is not in the manifest's explicit `trials_outputs` list.

---

## 8. Run list, order and time projection

**Mechanics.** One job at a time. Replays and gates through `src/estimators/fgo_cpp/tools/heavy.py` with the thread
variables at 1, from this branch's worktree (byte-identical code to `fwd-camera` except the E6 files). Flights through
`run_resumable_batch.sh` (state under `~/thesis_data/tier1/e6/batches/`) holding `~/thesis_data/FLIGHT_LOCK` via
`tools/flight_lock.sh` (D70: `heavy.py` holds `BUILD_LOCK` and `flight_lock_acquire` waits for `BUILD_LOCK`, so a
flight is never wrapped in `heavy.py`; the two locks exclude each other as designed). Wait loops check liveness
(`pgrep` with a bracketed pattern) and have timeouts. No command line contains the simulator or autopilot process
names.

| stage | jobs | estimate | projected (AEDT) |
|---|---|---|---|
| **1a** | code + this pre-registration committed on `e6-map-reuse` | — | 31 Oct ≈ 23:00 |
| **1b** | gates G0-UKF (12), G-E4′ (12), V-E6 (3 + 3), S-E6 (3) | ≈ 50 min | 1 Nov ≈ 00:00 |
| **1c** | verification flight V-F | ≈ 10 min | 1 Nov ≈ 00:15 |
| **1d** | mapping flights E6M_fig8_r1–r3 + IMU gap check | ≈ 20 min | 1 Nov ≈ 00:40 |
| **1e** | map replays (3 LC FGO, 3 landmark UKF) + `e6_maps.py` (MAP-INV, map files, P1 inputs) | ≈ 15 min | 1 Nov ≈ 01:00 |
| — | handover to Stage 2 (a fresh agent) | — | — |
| **2a** | test runs, UKF: 6 × ≈ 55 s (all UKF first) | ≈ 6 min | from Stage 2 start |
| **2b** | test runs, FGO live + batch: 6 runs in the order r1 fgomap, r1 ukfmap, r2 fgomap, r2 ukfmap, r3 fgomap, r3 ukfmap (complete pairs first) | ≤ 5.2 h (upper bound) | ≤ Stage 2 start + 5.5 h |
| **2c** | scoring (3), verdicts, `e6_numbers.md`, report | ≈ 1 h | ≤ Stage 2 start + 6.5 h |

- **Projected end of all E6 runs:** even if Stage 2 starts as late as 3 Nov 12:00, the upper bound ends by 3 Nov
  ≈ 18:30, before 4 Nov 12:00. **If at any point the projection passes 4 Nov 12:00, E6 stops at the last complete
  stage** (for example, after 2a: UKF arms scored, FGO arms NOT RUN) and reports; runs not finished are NOT RUN.
- Possible delay: `heavy.py` waits while another agent's job holds `BUILD_LOCK` or a flight runs; the plot agent's
  figure jobs are not heavy-locked, so every E6 job also checks for them first (Idle gate) and waits.

---

## 9. Outputs and results rules

| what | where |
|---|---|
| new trials | `~/thesis_data/trials/E6V_fig8_check/`, `~/thesis_data/trials/E6M_fig8_r{1,2,3}/` (not guard-covered; never `T_*`) |
| map replays | `~/thesis_data/tier1/E6M_fig8_rk/{lc_fgo_lc_t245, lc_ukf_lc_t245}/` |
| maps | `~/thesis_data/tier1/e6/maps/E6M_fig8_rk/{map_fgo.json, map_ukf.json, map_errors.json}` |
| test runs | `~/thesis_data/tier1/T_A_rk/room_{ukf,fgo}_e6_{fgomap,ukfmap}_E6M_fig8_rk/` |
| gate runs | `~/thesis_data/tier1/{e6_g0_ukf, e6_g0_fgo, e6_val}/` |
| job and batch state, logs | `~/thesis_data/tier1/e6/{batches, jobs, logs}/` |
| scores, gate jsons | `docs/thesis/tier1/scores/e6_*.json` |
| numbers | `docs/thesis/tier1/e6_numbers.md` (into `numbers_tier1.md` only at merge) |
| guard reports | `docs/thesis/tier1/frozen_manifest_20261022T002851_verify_e6_*.json` |

Deviations from this document are recorded in `e6_numbers.md` §Deviations and in `decisions_log.md` BEFORE the
affected result is read.

---

## 10. Limitations (stated before the runs)

- **Simulation only:** rendered tags, simulator-truth flight paths, no lighting change or tag wear between the mapping
  and test flights; the map's only error source is the estimator.
- **n = 3:** three mapping flights, three test flights, fixed pairs. Bands from three repeats are coarse; P1, P3 and P4
  are direction-only.
- **Perfect tag IDs:** no misidentification in the mapping or test flights (E3 studied wrong IDs separately).
- **Same world, same day, same tags:** map reuse over time (moved or replaced tags) is not tested.
- **One surveyed tag registers the frame** (tag 0, §1.2).
- **P4 confound:** arm (iv) uses different estimators (iSAM2 keyframe FGO, landmark UKF) and every central detection;
  arms (i)–(iii) use the thesis estimators on one fix per frame (§4).
- **The FGO map is the Experiment 3 iSAM2 hindsight (5 extra updates), not an LM batch** (DEVIATION inherited, M:10557).
- **No map uncertainty is propagated:** the supplied map is used as if exact (the user's design: "treated as fixed known
  landmarks"), so a map error acts as a fixed bias per tag.
- **Route:** the mapping route differs from the test route (out of sample); the figure of eight re-observes tags 4 and 6
  twice per circuit and the others once, over 3 circuits (fewer re-observations per tag than the 5 T laps).
