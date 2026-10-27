# Closed-loop Experiment 2 (known tags): scoping and costing

**READ-ONLY SCOPING, 2026-10-27. Nothing was run:** no flights, SITL, Gazebo, replays, estimator runs or timing
benchmarks. No frozen result was changed and no pre-registration was written. Three read-only search agents collected
sources. Numbers were traced by this session or taken from those agents' read-only sweeps with their citations. A sample
of each sweep was re-checked by this session: the batch `wall=` lines, three mtime walls, all six `lc_fgo_*_t245`
`stats.json` values, `ukf_lm` stats, and three corrections rows.

**Labels.**
- **[M]** = measured and stored (the source is given).
- **[D]** = derived by arithmetic from stored values (the formula is given).
- **[E]** = estimate or inference.
- M:n = `METHODOLOGY.md` line n. Other files are given by repo-relative path:line.

**Naming collision, stated once.** "Experiment 2" (known tags, repo code Experiment T; `thesis_vocabulary.md:42,72`)
is not the tier-1 extension "E2" (`docs/thesis/tier1/e2_results.md:1`, loop closure with fewer tags). Likewise
"Experiment 5" (tag hold, Experiment H; `thesis_vocabulary.md:44`) is not the extension "E5" (the landmark UKF,
`docs/thesis/tier1/e5_results.md:1`). Section 7 is about E5; everything else is about Experiments 2 and 5.

## Headline

- **The gating item: the frame change is not solved by reuse.** Open-loop Experiment 2 first anchors after arming.
  - The downward camera cannot see a tag on the ground (`tags_extnav.parm:11-12`).
  - The first sent fix in `T_A_r1` was at z_enu 0.742 m, i.e. airborne (`~/thesis_data/trials/T_A_r1/logs/tag_bridge.csv`
    row 2: `t_capture` 28.546 s, `z_enu` 0.74194).
  - "No frame change after arming" is an ENFORCED ruling for every closed-loop estimator (M:11989-12003). It follows
    `H_ifa_ekf3`: 2.25 m displacement, 19.2° tilt and a watcher stop (M:11965-11972).
  - A closed-loop Experiment 2 therefore needs a pre-arm anchor that the open-loop experiment never had. That is a
    design change.
- **Flights:** 36 result flights (3 estimators × 4 conditions × 3 repeats), plus 4 verification flights, 0–4
  conditional 5S safety flights and about 5–6 contingency re-flies.
  - Per result flight, about 7–8 min wall [E], built from measured parts (§3).
  - **Total about 7–9.5 machine hours**, serial, one simulation at a time [E].
- **Effort: about 6–9 working days elapsed** [E], split as machine ≈ 7–9.5 h, agent 4.5–6.75 days and user review
  2–2.75 days, partly overlapping.
  - Started today (Tue 27 Oct), it would finish Tue 3 Nov at best, Fri 6 Nov at the upper end. The lock is Wed 4 Nov 23:59
    AEDT.
  - It fits only in the best case, with no margin. The user's earlier decision was "no further stages planned"
    (`docs/thesis/tier1/open_questions.md:23`).
- **Closed-loop results would sit BESIDE the open-loop ones, never replace them** (§4).
- **Live landmark UKF (Experiment 3):**
  - **Python, workstation:** plausibly live. The stored derived upper bound is **≤ 7.2 ms per filter step at n = 36**
    [D], against the UKF's 15.0 ms step period.
  - **Onboard in the ArduPilot port:** not feasible before the lock. The port is fixed at N = 15 with no state
    augmentation (§7).

---

## 1. Reused code and configuration, and the new code needed

### 1.1 Reused as is (paths)

| item | path | role in a closed-loop Experiment 2 |
|---|---|---|
| Closed-loop launcher | `sim/tools/closed_loop_run.sh` (130 lines) | `UKF=1` → `closedloop_ukf.parm`, `AHRS_EKF_TYPE=12` (:22-37); `FGO=1` → `closedloop_fgo.parm`, `AHRS_EKF_TYPE=13`, C++ node (:40-52); EKF3 → `closedloop.parm`, `AHRS_EKF_TYPE=3` (:17). Watcher with fail-closed heartbeat (:74-75, :117). `AHRS_UKF_TFAIL=0` forced at every start (:28-30) |
| Watcher | `sim/tools/wall_watch.py` (211 lines) | room box `--box=-4.4,4.4,-4.4,4.4` (`closed_loop_run.sh:74`), process liveness, `--dep-loss land` (:104) |
| Flight lock | `tools/flight_lock.sh:1-22` | `~/thesis_data/FLIGHT_LOCK`, atomic, owner token; excludes `BUILD_LOCK` |
| Flight script | `fly_trial.py` (970 lines) | lap mode `LAPS=5,6,0.5` (:574-611, :933-934); pre-arm anchor gate `require_anchor_before_arming` / `H_PREARM` (:434-484, :918) |
| Run harness | `run_trial.sh` (627 lines) | `TAG_BRIDGE=1` + `TAG_IDS` (:137-143, :385-391); FGO node with `FGO_NODE_TAGS` and `TAG_SIGMA_POS` (:418-423 C++, :445-449 Python) |
| Downward tag bridge | `tag_bridge.py` (131 lines) | floor-tag fixes, condition subset `tag_ids`, central-third validity (:38-39, :89-90), `/tags/sent`, `ODOMETRY` to SERIAL1 |
| Forward tag bridge | `tag_bridge_fwd.py` (187 lines) | D18 range band and the armed/disarmed anchor rule (:70-81, :124-126), status file (:67-69) |
| World with T's floor tags, a wall tag and `iris_fwd` | `sim/worlds/room_wall_tag_far.sdf` | **its 8 floor-tag poses are identical to `room_tags.sdf`** (diff of the `apriltag36h11_0..7` poses, this session); wall tag id 10 at (0, 4.999, 1.5) (:175-177); `iris_fwd` spawn (0, 1.1), yaw 90° (:194-196), 3.9 m from the tag |
| Parameters | `tags_extnav.parm` (σ_pos 0.05, `VISO_DELAY_MS 15`, :4-13); `h_extnav.parm` (`MOT_THST_HOVER 0.310` pinned, :17-18); `h_ukf_tag.parm` (`AHRS_UKF_EXTPOS 1`, :7-8); `closedloop{,_ukf,_fgo}.parm`; `consolidated_rerun.parm` (`LOG_REPLAY 1`, `LOG_DISARMED 1`, :13-14) | as listed |
| Time sync | `sim/models/iris_fwd/model.sdf:793` and `sim/models/iris_with_ardupilot/model.sdf:789`: `<no_time_sync>0</no_time_sync>` | time sync on. `AHRS_EKF_TYPE` set explicitly in every closed-loop parm file and enforced by `EXPECT_OVERRIDE` |
| Backends | UKF port `~/ardupilot_ukf` (`AP_NavUKF`, ExtNav position + yaw path, `docs/h_backends_tag_input.md:148-194`); SITL copter at `5f94ea1a` (M:13794). C++ FGO node `4c07374b`, corrected priors (M:13686) | the flying UKF and FGO |
| Offline estimators (hindsight tracks, shadows) | `src/estimators/room_ukf_replay.py` (205 lines), `src/estimators/fgo/room_fgo_replay.py` (227 lines) | the FGO whole-flight batch and the RTS-UKF on each flight, as in open-loop Experiment 2 |
| Scorers | `eval/tag_score.py` (168 lines), `eval/t_aggregate.py` (52), `eval/h_safety_score.py` (103), `eval/h_gt_far_score.py`, `eval/ukf_tag_tierB.py`, `eval/fgo_node_tag_equiv.py`, `eval/imu_gap_check.py` | per-track errors, per-gap gains, safety, ground tests, equivalence, IMU-gap rule |
| Run-script templates | `tools/run_h_far.sh` (28 lines), `tools/run_ukf_refly.sh`, `tools/run_fgo_refly.sh`, `tools/run_expT.sh` (18 lines) | per-flight wrappers under the flight lock |

### 1.2 New code needed (sizes are [E])

`closed_loop_run.sh` cannot be used unchanged. Its `H=1` branch (:67-95) hard-codes:
- the forward bridge;
- `h_extnav.parm` (σ 0.02, `VISO_DELAY_MS 31`);
- `ALT=1.5` and `HPROFILE`;
- `H_PREARM` only for `room_wall_tag_far*`.

`run_trial.sh` refuses to run the two tag bridges together, since both write to SERIAL1 (:142, :150).

| # | item | why | size [E] |
|---|---|---|---|
| N1 | **Pre-arm anchor design** (the gating decision, §8 Q1). Recommended option: reuse `room_wall_tag_far`'s geometry. The wall tag is used **only while disarmed** (anchor), the floor tags in flight. All fixes are expressed in T's world map frame. W and T's map NED differ only by a 5 m N offset (the wall tag at world y = 5; `docs/tag_hold_design.md:69-76`) [E, from the frame definitions] | rule M:11994-11997. Without an anchor, arming is refused (`closed_loop_run.sh:84-94`) | world variant (copy + ids + spawn): ~20 lines |
| N2 | `tag_bridge_fwd.py`: an anchor-only mode (send only while disarmed) and output in the map frame | in T's lap the east-bound leg along y = 3 m passes about 2.06 m from the wall tag (closest at (0, 3, 2)) (inside the 0.9–2.8 m D18 band), so it would add in-flight fixes that open-loop T never had [E] | ~30–50 lines |
| N3 | `tag_bridge.py`: the "no first fix after arming" rule, the drain and the status file, ported from `tag_bridge_fwd.py:67-160` | the downward bridge has no armed-state logic (grep: no `armed` in `tag_bridge.py`) | ~50–80 lines |
| N4 | Two tag senders: a second SITL serial port for one bridge (`SERIALn_PROTOCOL 2`, a run_trial branch), or a merged bridge. `/tags/sent` from both, one topic or a remap for the FGO node | `run_trial.sh:142,150` | ~30–60 lines + 1 parm file |
| N5 | `closed_loop_run.sh`: a T branch with `TAG_BRIDGE=1`, `TAG_IDS`, `tags_extnav.parm` (enforced), `LAPS`, `ALT=2.0`, `TAG_SIGMA_POS=0.05` passed to the node (the node default is 0.02: `run_trial.sh:423,449`), the room-box watcher, `H_PREARM` for the new world, and the UKF `EXTPOS` file | the H branch is H-specific | ~40–60 lines |
| N6 | `fly_trial.py`: a transit segment from the spawn (0, 1.1) to the lap start at tag 0 (−3, −3), 5.1 m [D], excluded from scoring (as H's 2.4 m approach, M:11345) | the far spawn | ~30–50 lines |
| N7 | Scorer: the flying estimator's live track from the dataflash (UKF/FGO log rows) or the node output, lap tracking error against the setpoint, the per-gap profile on each estimator's own trajectory, and re-worded gates (§2 G-T) | `tag_score.py` assumes one shared trajectory and reads the UKF/FGO live tracks from offline replays | ~150–250 lines |
| N8 | Aggregation: closed-loop Experiment 2 tables and figures, beside F5 | §4 | ~100–150 lines |
| N9 | Run wrapper `tools/run_expT_cl.sh` (36 flights, interleaved, flight lock, stop on breach) | template `tools/run_h_far.sh` | ~40 lines |
| — | Backend code (UKF port, C++ node) | **none needed under N1** [E]. The port takes a per-fix σ from the `ODOMETRY` covariance (R_pos = constrain(posErr, 0.01, 10)², `docs/h_backends_tag_input.md:150-180`). The node's single `tag_sigma_pos` 0.05 also covers the on-ground anchor (a declared choice) | 0 |

**Total new code: about 500–800 lines** [E], all harness, bridge and scoring. No estimator code changes.

---

## 2. Safety tests and gates to re-run

| gate | re-run? | reason |
|---|---|---|
| **Configuration and time sync (per flight, from the PARM dump):** `AHRS_EKF_TYPE` 3 / 12 / 13 (not T's 10, M:10161-10162), `LOG_REPLAY 1`, `VISO_DELAY_MS 15`, `MOT_THST_HOVER 0.310`; `no_time_sync 0` in the model used | **yes, every flight** | Correction #7 (time sync, `AHRS_EKF_TYPE`) and the eeprom-persistence gotcha (CLAUDE.md Known Issue #10; the test hook persisted, M:11654). **`preflight_check.sh` does not exist.** CLAUDE.md:743 names it, but PROGRESS.md:573,738 list it as still to build. The working equivalents are `fly_trial` `ensure_params`/`EXPECT_OVERRIDE` and the PARM-dump G1 |
| **Port-tree eeprom/PARM audit** (first flight's PARM dump against the last H flight) | yes, once | as M:11393; a new world and parm chain on the port tree |
| **F1, on-ground fix error** (horizontal p95 ≤ 0.10 m, yaw p95 ≤ 2°; M:11316) | every flight | the anchor is the frame |
| **Ground tests G1–G6** (UKF and FGO flying; `docs/h_backends_tag_input.md:409-465` as amended at M:11321-11328) | **yes, 2 flights** | new input stream in flight: many floor-tag ids, σ 0.05, a 15 ms delay against H's 31 ms, ungated fixes; anchor before arming |
| **Equivalence:** UKF tier B Replay (`eval/ukf_tag_tierB.py`, as M:12454) and FGO node FN1–FN4 (`eval/fgo_node_tag_equiv.py`) on an EKF3-flown closed-loop T tape | **yes, offline** | different tag stream. The FGO node core was already compared offline on T bags in Band C (T_A max \|Δp\| 2.6e-7 mm, T_D 5.1e-4 mm; M:13683), which lowers this risk |
| **"No first fix after arming" regression** (N3) | yes, offline (a bridge unit check on recorded `tag_bridge.csv`) | the new bridge logic. M:12008-12013 is the model: byte-identical outputs on a pre-arm-anchored log, refusal on a post-arm one |
| **5S S-A1–S-A4** (attitude, trigger, safe landing, single landing; M:11294-11309) | **conditional: 0 flights if no backend binary changes; 4 (UKF a/b, FGO a/b) if any does** [E] | 5S tests the backends' behaviour when output becomes invalid, which N1–N9 do not touch. **Standing: UKF (b) S-A2 FAILS AS WORDED** (5.69 s against 5.5 s; numbers.md:490), so closed-loop UKF flights would fly with that recorded failure |
| **In-flight-anchor test (`H_ifa_*`)** | no | answered and enforced (M:11989-12003); N1/N3 prevent the case |
| **EKF3 same-frame resets under lap mode (new, verification)** | **yes, 1 short flight (condition D)** | in B–D, EKF3 times out in most gaps (`horiz_pos_abs` 0.05; numbers.md §16.1), so it resets position at almost every fix. The ruling says same-frame resets are "NOT covered" (M:12003-12004). Whether lap mode's moving setpoint drives the vehicle to the old target, as GUIDED did in `H_ifa_ekf3`, is untested [E] |
| **IMU-gap rule** (`eval/imu_gap_check.py --write`) and "nothing else running" | every flight | M:10215-10224 (the T process slip: 6 of 12 flights re-flown) |
| **Watcher fail-closed** (`tools/test_watch_failclosed.sh`) | once | new launcher branch |
| **G-T gates re-worded** | before flying | T's G2 "every subset tag sent in each lap" (M:10163-10166) is a gate open loop. Closed loop it becomes an outcome: a drifting estimator can miss the central third (radius 133 px, `tag_bridge.py:38-39`), so missed tags are a result, not a pipeline failure |

---

## 3. Flights, measured wall time and machine hours

**One simulation at a time.** Each flight runs SITL + Gazebo under `FLIGHT_LOCK` (`tools/flight_lock.sh:6-18`).
`run_resumable_batch.sh:141` refuses to start beside a running sim. No replay or heavy job may run while a flight runs
(M:10222-10224). So flights cannot run in parallel, and offline replays come after, or between, flights.
`closed_loop_run.sh` does not take the lock itself; the `tools/` wrappers do (e.g. `tools/run_h_far.sh:21-23`).

### 3.1 Measured wall time per flight (stored sources)

| flight group | wall per flight | source | kind |
|---|---|---|---|
| **Exp. 2 open loop, 12 final flights** | **312–317 s** | `~/thesis_data/batches/expT_console.log` / `expT_refly_console.log` `COMPLETE … wall=` (e.g. T_A_r1 `wall=312s`, :90; T_A_r3 `wall=315s`, refly :454); bash `$SECONDS` around `run_trial.sh` (`run_resumable_batch.sh:155-163`) | [M] |
| Exp. 2, its bag sim time | 266.9–271.5 s | bag `duration` | [M] |
| Exp. 2, RTF | 0.948–0.967 | bag sim / recording wall span | [D] |
| Exp. 2 IMUGAP originals (under concurrent replay load) | 321–383 s | same logs (:452-995) | [M] |
| **Exp. 5 S1far (EKF3 flying), r1–r3b** | 502–546 s | `closed_loop/<name>/result.txt` mtime − `launch.txt` mtime (`closed_loop_run.sh:105`, :122) | [D, mtime] |
| **Exp. 5 S2v2 (UKF flying)** | 518 / 532 / 550 s | same (verified for `H_s2v2_r1`: 518 s) | [D, mtime] |
| **Exp. 5 S3v2 (FGO flying)** | 580 / 564 / 534 s | same (verified for `H_s3v2_r1`: 580 s) | [D, mtime] |
| Exp. 5 closed-loop RTF (S1far, S2v2, S3v2) | 0.721–0.803 | bag sim / recording wall | [D] |
| Exp. 5 overhead outside recording (S2v2) | 38–40 s | mtime wall − recording wall span (518 − 478.5, 532 − 493.7, 550 − 511.1) | [D] |
| Exp. 5 far ground tests `H_gt_ukf_far` / `H_gt_fgo_far` | 170 / 179 s | mtime | [D] |
| 5S safety, final builds (UKF v3, FGO v4) | 124–178 s (UKF), 103–156 s (FGO) | mtime (verified `H_safety_fgo_a_v4`: 156 s) | [D] |
| Exp. 1C corridor, half-speed set (b) v2/v3 | 707–709 s; cruise 602.3–602.8 s wall for 300 s sim | mtime; `trials/cl_ukf_b_tex_r1_half_v2/run_trial.log:49` "300.1s sim time elapsed (602.7s wall-clock)" | [D] / [M] |

No stored source gives a per-flight wall time for an H or `cl_*` flight from a logged timer. The mtime-derived values
and the ROS log-epoch spans agree within about 10–30 s (agent cross-check). The per-flight wall-time figure in
`docs/tag_hold_design.md:124,191-192` is a sim-time estimate, not a measurement.

### 3.2 Per-flight estimate for closed-loop Experiment 2 [E]

- Sim ≈ 270 s (T's laps and landing, measured) + ≈ 30 s (anchor wait and the 5.1 m transit) ≈ **300 s** [E].
- At the measured closed-loop room RTF of 0.721–0.803, plus about 39 s of overhead: **≈ 413–455 s ≈ 7–8 min per flight** [E].
- The lower bound, if RTF stayed at T's 0.95, would be about 355 s [E].

### 3.3 Flight count and machine hours

| block | flights | wall each | hours |
|---|---|---|---|
| EKF3 closed-loop check flight (short: anchor, transit, 1 lap, condition A; also the equivalence tape) | 1 | ~3 min [E] (analogue `H_gt_*_far` 170–179 s [D]) | 0.05 |
| UKF and FGO ground tests G1–G6 | 2 | 170–179 s [D, analogue] | 0.1 |
| EKF3 lap-mode reset check (short, condition D) | 1 | ~4 min [E] | 0.07 |
| 5S S-A1–S-A4 (conditional) | 0 or 4 | 103–178 s [D] | 0–0.2 |
| **Result flights: 3 estimators × 4 conditions × 3 repeats** | **36** | 7–8 min [E] | **4.2–4.8** |
| Contingency re-flies (~15%; Exp. 2 history: 6 IMU-gap re-flies + 2 aborted starts, M:10212-10224; Exp. 5: 5 aborted or failed attempts, `closed_loop/*abort*`) | 5–6 | 7.5 min [E] | 0.6–0.75 |
| **Flights subtotal** | **45–50** | | **≈ 5.0–6.0** |
| Offline hindsight and shadow replays, after the flights (UKF + RTS: ~53–55 s per flight, by the E5 `val_world` / no-LC `wall_s` proxies 52.9–54.4 s [M]; FGO live + batch: ~3–5 min [E] from `room_fgo/stats.json` `step_median_ms` 18.3 [M] × ~7,350 keyframes) | 36 × 2 | | ≈ 2–3.5 [E] |
| **Total machine time** | | | **≈ 7–9.5 h** [E] |

No stored wall time exists for the room replays themselves (`room_fgo/stats.json` and `room_ukf/stats.json` hold only
`step_median_ms` / `dt_step_ms`).

---

## 4. Frozen items touched, and replace versus beside

**BESIDE, not replace.** Open-loop Experiment 2 was built so that "the flown path does not depend on the estimator or
the tag condition" (M:10061-10062). P-T3 and the per-gap profiles assume one trajectory per flight.

A closed-loop version differs in several ways:
- each estimator flies its own trajectory;
- the airframe is `iris_fwd` in the far-spawn world, against T's `iris_with_ardupilot` in `room_tags` (`room_tags.sdf:175-176`);
- there is a transit and a wall-tag anchor fix, which T never had;
- `AHRS_EKF_TYPE` is 3/12/13 instead of 10.

So it is a new sub-study with its own pre-registration. Its numbers cannot replace any frozen open-loop row.

| frozen item | what would change |
|---|---|
| `docs/thesis/numbers.md` §16.1 (:520-545; content-frozen above `## Errata`, `tools/check_numbers_frozen.py` PASS, sha256 `6a77b9ab…`) | **untouched.** New numbers cannot be added above `## Errata` without breaking the freeze, so they need a separate results page (as `docs/thesis/tier1/e*_results.md`) or an Errata entry. §8 Q4 |
| `final_results_pack.pdf` / `final_results_pack_corrections.md` (frozen) | untouched. They would not list the new sub-study unless regenerated, which is a user decision |
| F5 / **Figure 5.1** (`eval/figs_thesis.py:1248-1292`), **Table 5.2** T8 (`:1967-1980`) | unchanged (beside). A new figure would be added |
| **Table 7.3** R1 scorecard (`eval/figs_thesis_results.py:569, 598-605`), **Table 7.5** R4 (`:949-1005`), **Table 7.1** footnotes | regenerated if the new hypotheses are added. Existing rows unchanged |
| Summary and walkthrough PDFs (`eval/figs_thesis_summary.py:210, 1451`; last built at `c0c8c02`) | new pages; existing pages should stay pixel-identical (the `c0c8c02` precedent) |
| `docs/thesis/thesis_vocabulary.md` (Experiment 2 rows :42, :72; hypotheses H2.1–H2.4 :166-173; F5 → Figure 5.1 :236) | one new sub-study name (e.g. "2C, closed loop"), new H2.x labels. The vocabulary sits at 47 rows against the ≤ 50 target (:30) |
| `docs/thesis/limitations.md`, `discussion_material.md`, claims (`tier1/claims_applied.md`) | `limitations.md` has no open-loop row for Experiment 2 today (grep). A new claim or limitation row would be added; no existing row would be edited |
| `METHODOLOGY.md` | append-only entries (pre-registration, results); nothing existing changes |

---

## 5. Risks

### 5.1 Specific risks [E unless cited]

1. **Pre-arm anchor (blocking).** See the Headline and N1. Any option changes the experiment. The far-spawn wall-tag
   option is the least new code because it reuses a world whose floor tags already match T's.
2. **EKF3 same-frame resets in conditions B–D** under GUIDED lap mode: an untested interaction (§2). The size of each
   step is about the accumulated drift (open-loop EKF3 live RMSE 0.055–0.096 m in B–D; numbers.md §16.1).
3. **Drift feedback.** The FGO cannot be gated. A drifting closed-loop estimator can carry the vehicle away from the tag
   centres, so fewer tags fall inside the central third and the drift grows further.
   - Open-loop condition D live RMSE is UKF 0.131 m and FGO 0.083 m (numbers.md §16.1). The central-third radius at
     2 m is roughly 0.4–0.5 m on the ground [E, from 133 px and the camera geometry].
   - So a miss is plausible but not expected in D [E].
   - The room box leaves 1.4 m from the lap corners (±3 m against ±4.4 m).
4. **Standing 5S failure:** UKF (b) S-A2 fails as worded (numbers.md:490).
5. **Which FGO build flies.**
   - The installed node `4c07374b` has the corrected priors (#18). The flown Experiment 5 S3v2 and corridor v3
     results used the OLD priors `f642cd37` (numbers.md:37, :490).
   - So a closed-loop Experiment 2 would be the first result set flown on the corrected node. Its numbers would not
     be comparable build-for-build with S3v2.
6. **UKF tilt bias** (M:11539): masked by the D18 range band in the forward bridge, not fixed in the model.
   - The downward bridge has no range band; T's fixes are all at ~2 m height, so this is probably not triggered [E].
   - The anchor at 3.9 m on the ground is the same geometry as H's far spawn, which passed F1.
7. **Time.** The lock leaves 7 working days including today. Exp. 5's own design estimate was 6.5–7.5 days
   (`docs/tag_hold_design.md:194-203`). The dated record shows failed ground tests, a failed in-flight-anchor test and
   repeated safety re-runs between 2026-10-08 and 2026-10-12 (M:11111-13690).
8. **Concurrency slip.** Experiment 2's own history: 6 of 12 flights were spoilt by concurrent replays (M:10215-10224).

### 5.2 The 18 recorded corrections

The 18 are the numbered table in `docs/thesis/final_results_pack_corrections.md:26-45` (Table T2 of the pack;
"T2 corrections (18) are CURRENT", M:13533). Two later ones, #19 and #20, are in
`docs/thesis/tables/R2_corrections_by_discovery.md:30-32`.

| # | correction (corrections.md line) | exposed by closed-loop or onboard work? | fixed in the current backends? | could recur in closed-loop Exp. 2? [E] |
|---|---|---|---|---|
| 1 | UKF/FGO IMU dejitter (:28) | no | offline rule; the port integrates on sensor time | no |
| 2 | IMU-gap exclusion (:29) | no | data rule | **yes as an event**: needs the per-flight check |
| 3 | EKF3 `FLOW_POS_Z` 0.25 (:30) | no | config in every re-fly (`consolidated_rerun.parm:8`) | only if the parm chain drops it: G1 checks |
| 4 | UKF process dt (:31) | no | offline UKF | no |
| 5 | **Lateral flow sign** (:32) | **yes, the closed-loop smoke test** (M:4069, 4155) | yes: `flow_bridge.py` and shared `h_flow_pose` (M:4155-4172); right-signed in T (M:10190-10193) | low. Lap legs E/W are pure lateral, the same as the T check that passed |
| 6 | Roll rate gains (:33) | no | vehicle params | no |
| 7 | **Time sync / `AHRS_EKF_TYPE` / `LOG_REPLAY`** (:34) | found by source reading; it matters most closed loop | yes: `no_time_sync 0` (both models), explicit `AHRS_EKF_TYPE` | **yes, via eeprom/parm chain**: G1 per flight |
| 8 | Heading share window (:35) | no | analysis | no |
| 9 | D15 ground-proximity flow rule (:36) | partly (port comparison) | yes, port and offline | **yes**, it recurred once as #12 |
| 10 | D27 UKF per-second process noise (:37) | partly (port equivalence) | offline aligned to the port | no |
| 11 | **CL scorer B5 window** (:38) | **yes, closed-loop scoring** | scorer | **yes in kind**: the new closed-loop scorer (N7) needs its windows pre-registered |
| 12 | **Six T FGO runs lacked D15** (:39) | **yes, the C++ port equivalence work** (M:10862) | re-run, no verdict change | **yes**: the same pipeline gap (no `imu_gaps.json` → no arming time) would hit new replays if the IMU-gap step is skipped |
| 13 | **UKF port float constants; C++ FGO live `time_ref` seed** (:40) | **yes, port + live node** | fixed (`d1e5dc4`; live check M:11737) | low; covered by G1–G6 and the Rule A timing check |
| 14 | **FGO `biasAccOmegaInt` → 0** (:41) | **yes, the Exp. 5 hover-tilt and safety work** | yes, node `1123742d` onwards | no (source check `eval/final_rerun_checks.py`) |
| 15 | FGO yaw cap variance-gated (:42) | no (audit) | yes, `f642cd37` onwards | no |
| 16 | **Offline UKF bias-corrected derotation** (:43) | **yes, the Exp. 5 S1 shadow-vs-flying gap** | offline default since `29db0d8` (M:12721); the port already used it | low; offline hindsight replays use the default |
| 17 | UKF Cholesky jitter (:44) | no (audit), but re-flown | yes, port `abb0357d` and offline | no |
| 18 | **FGO initial σ (priors)** (:45) | no (offline re-run) | **only in node `4c07374b`** (M:13686); S3v2 and v3 flew the old priors | **build-mismatch risk** (risk 5) |
| — | not in the 18: the UKF tilt bias (M:11539), the eeprom-saved test hook (M:11654), the D22 lateral burst (M:8516, a ruled limitation) | Exp. 5 / closed loop | masked by D18 / forced `TFAIL=0` / not fixed | tilt bias: see risk 6; test hook: handled by `closed_loop_run.sh:28-30` |

Recurrence is not recorded anywhere for any correction except #12, which is a recurrence of #9. The last column is
this scoping's inference.

---

## 6. Total effort in working days [E]

| work | agent | user review | machine |
|---|---|---|---|
| Anchor-design ruling (Q1), replace/beside, gate re-wording | 0.25 | 0.5 | — |
| Pre-registration (not written here) and sign-off | 0.5 | 0.5 | — |
| N1–N9 code and offline checks (bridge regression, fail-closed) | 2–3 | 0.25 | — |
| Verification flights (check, ground tests, reset check) + equivalence + PARM audit | 0.5–1 | 0.25 | ~0.2 h |
| 5S (if triggered) | 0–0.25 | 0–0.25 | 0–0.2 h |
| 36 result flights + re-flies + IMU-gap checks | 0.25 (monitoring) | — | 4.8–5.6 h |
| Offline hindsight replays, scoring, aggregation, results page, figures | 1–1.5 | 0.5–1 | 2–3.5 h |
| **Total** | **4.5–6.75 d** | **2–2.75 d** | **≈ 7–9.5 h (~1–1.5 d)** |

**Elapsed: about 6–9 working days**, because flights wait on each gate and the user reviews overlap with agent work.

Assumptions:
- Q1 is answered on day 1 with the recommended option.
- No backend code changes.
- No failed gate needs a new ruling. Experiment 5 had several, so this is optimistic.
- Flights run unattended overnight in a resumable wrapper.

**Calendar** (counting today, Tue 27 Oct, as day 1): 7 working days remain to the lock (27, 28, 29, 30 Oct; 2, 3,
4 Nov).
- A 6-day finish lands **Tue 3 Nov**.
- A 9-day finish lands **Fri 6 Nov**, after the 2026-11-04 23:59 AEDT lock and on the last reporting day.

**Verdict:** this fits only in the best case, with about one day of margin, and only if Q1 is ruled at once. It
conflicts with the user's decision "no further stages planned" (`docs/thesis/tier1/open_questions.md:23`).

A reduced option: **EKF3 closed loop only** (12 flights, UKF/FGO as offline shadows on EKF3's trajectory, as in Exp. 5
S1).
- It drops the UKF and FGO ground tests, the equivalence checks and any 5S.
- Still needs N1–N9 minus the backend-specific parts.
- About 3.5–5 working days [E], about 2.5–3.5 machine hours [E].

---

## 7. A live landmark UKF for Experiment 3

**State size.** `src/estimators/ukf_lm.py`:
- 15 vehicle states, then one [x, y, ψ] block per landmark (:5, :23, :31-33);
- 2n + 1 sigma points;
- a fresh Cholesky in every `sigma_points` call (:46), with a jitter ladder and eigh fallback (:44-58).

The design bounds are n ≤ 15 + 3 × 7 = 36 with loop closure (all landmarks kept), and smaller without, since finished
landmarks are marginalised (`docs/thesis/tier1/e5_design.md:190-193`).

Stored `max_state_dim`:
- 36 (LC, T_A_r1–r3);
- 18 (no-LC);
- 39 (`val_augmented`, T_A_r1) [M, `~/thesis_data/tier1/T_A_r*/lc_ukf_*/stats.json`].

**Stored timing.** No per-step compute time is stored.
- `dt_step_ms` = 15.0032 is the filter step *period*, not compute time.
- `wall_s` covers bag reading, the pre-pass, the forward filter, the RTS backward pass and the writes.

The derived upper bounds per filter step [D, `wall_s` / `rts_nodes`, which ignores ~1,900 pre-anchor steps and the RTS
pass, so it overstates the forward step]:

| run | max_state_dim | wall_s [M] | rts_nodes [M] | ≤ ms/step [D] |
|---|---|---|---|---|
| T_A_r1 / r2 / r3 LC | 36 | 116.5 / 115.3 / 117.3 | 16,330 | 7.1 / 7.1 / 7.2 |
| T_A_r1 / r2 / r3 no-LC | 18 | 54.4 / 54.0 / 53.8 | 16,330 | 3.3 / 3.3 / 3.3 |
| T_A_r1 val_augmented | 39 | 138.4 | 17,272 | 8.0 |
| T_A_r1 val_world (no landmarks) | 15 | 52.9 | 17,272 | 3.1 |

Run conditions: workstation Python, `~/venv-evo`, numpy 2.5.1, BLAS threads 1, one job at a time
(`e5_results.md:9`; `preregistration.md:214`).

**Budgets.**
- The binding live budget for a UKF is its own step period, **15.0 ms**.
- The FGO's deployability budget is **33 ms** per keyframe (M:704-721: the 0.25 s window was chosen as the largest
  meeting it).
- The derived bound of ≤ 7.2 ms at n = 36 is under both. **This is workstation Python only.**

**For comparison, the FGO in Experiment 3:**
- LC keyframe step median 35.3 / 41.3 / 39.2 ms [M, `~/thesis_data/trials/T_A_r*/lc_fgo_lc_t245/stats.json`
  `step_median_ms`], i.e. **over** the 33 ms budget. M:10599 records 33–43 ms.
- No-LC: 50.2–60.6 ms median [M].
  - These no-LC json values do not match M:10600 (36–55 ms; wall 1,044–2,996 s against stored 7,276–9,583 s).
  - The files are dated 2026-10-10 21:22, which suggests a later re-run. This is flagged, not resolved (§8 Q7).

**Onboard.** The ArduPilot port is a fixed-size C++ filter:
- `static constexpr uint8_t N = 15; NS = 2 * N + 1;` (`~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.h:149-150`);
- fixed arrays;
- SITL-only build;
- tags enter as world-frame ExtNav position fixes, not landmark states (`docs/h_backends_tag_input.md:150-180`).

A landmark version is a re-architecture, not an extension: variable n up to 36–39, data association and landmark
initialisation.
- Cholesky cost alone scales by (36/15)³ ≈ 13.8× to (39/15)³ ≈ 17.6× [E].
- The port's per-predict cost on an H7 is itself only an estimate (0.3–0.4 ms in double; `docs/partC_onboard_feasibility.md:452`).
  Scaled, that would be several ms per predict against a 2.5 ms main loop [E].
- No port timing has ever been measured (`docs/real_flight_readiness.md:126`).
- On a Pi companion, the i7→Pi 4 factor of 3–5× [E, `docs/real_flights_pi_readiness.md:60-61`] would put the n = 36
  Python step bound at about 21–36 ms, over 15 ms [E].

**Verdict.**
- **Live, in Python on the workstation:** feasible on the stored evidence (an upper bound of ≤ 7.2 ms against 15 ms).
  The forward-only step time is **not measurable without a run**. A run would time each forward step (predict, flow,
  range and tag updates, augmentation) with the RTS pass off, and report the median and p99 per step against n.
- **Onboard (port), or on a Pi 4:** not feasible within the lock. It would be a re-architecture with no measured basis.
- Not costed further, since no flights would use it before the lock.

---

## 8. Open questions (for the user; none blocks this report)

1. **Q1, the pre-arm anchor.** Options:
   - (a) the far-spawn wall tag, used only while disarmed. **Recommended:** it reuses `room_wall_tag_far`, whose floor
     tags match T's.
   - (b) a synthetic "surveyed launch pose" fix while disarmed. This is a new measurement type.
   - (c) a ruling to allow a first anchor after arming when no position target is stored. This reverses an ENFORCED
     ruling (M:11989-12003). It also needs backend code: the port's `fuse_tag` and the C++ node's `LiveAdapter::tag`
     refuse a first anchor while armed (M:11996-12000). That brings back the port and node regressions and makes the
     5S re-runs required, not conditional.

   Each changes the experiment against open-loop Experiment 2.
2. **Q2:** all three estimators flying (36 flights, 6–9 days), the reduced EKF3-only option (12 flights, 3.5–5 days),
   or neither? This weighs against "no further stages planned" (`open_questions.md:23`).
3. **Q3:** which FGO node flies: `4c07374b` (corrected priors, never used for a result flight) or `f642cd37` (S3v2's
   build)?
4. **Q4:** where the new numbers live, given that `numbers.md` is content-frozen above `## Errata`: a separate results
   page (as the tier-1 `e*_results.md`) or an Errata entry?
5. **Q5:** are the 5S tests re-flown when no backend binary changes (0 or 4 flights)? Does the standing UKF (b) S-A2
   failure need a ruling before the UKF flies closed loop again?
6. **Q6:** is Tue 3 Nov a working day for the user (it is a public holiday in Victoria)? The calendar in §6 assumes
   it is.
7. **Q7 (not costing-relevant):** the stored no-LC FGO `stats.json` (`step_median_ms` 50.2–60.6, `wall_s`
   7,276–9,583) does not match M:10600 (36–55 ms; 1,044–2,996 s). Which is current?

**Decision logged:** D56 in `docs/thesis/tier1/decisions_log.md`. It records that the costing assumes anchor option (a),
under rule 1, reversible.
