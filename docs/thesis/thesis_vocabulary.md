# Thesis vocabulary: the reduced set of names for the thesis text

*DRAFT for the user, 2026-10-16. Branch `fwd-camera` at `6a0fa0f`. A new file. **Nothing in the repository, the results or
any frozen document has been renamed.** These names are for the thesis text only. The repository keeps its own codes,
and the appendix mapping (§9) leads back to them.*

*Added 2026-10-17 (after the sweep; no row renumbered): the analysis name **heading-error decomposition of sideways drift**
(§5, under H1.3) and the descriptive term **thesis-nav position-lost path** (§8.3). Neither is counted as a vocabulary term in §0:
the first is an analysis name inside a hypothesis's section, and the second is descriptive, like §8.1 rows 40 and 41.*

*Added 2026-10-17 (ordering footnotes; no row renumbered, §0 counts unchanged): **§11, "n" as used in the tables and the
ordering verdicts** (RULE MET; case (i) TEST RUN, RULE NOT MET; case (ii) FAILED AS WORDED; case (iii) NO COMPARATIVE TEST
REGISTERED). These are methodological labels written in words, defined in `methodology_definitions_draft.md`; they are not
counted as vocabulary terms in §0, which keeps its seven methodological labels.*

**Inputs read:** `docs/thesis/glossary.md`, `docs/thesis/glossary_flags.md` (including its §c proposed scheme),
`docs/thesis/numbers.md`, `docs/thesis/headline_claims_before_after.md`, `docs/thesis/figures_thesis/index.md`,
`docs/thesis/tables/T1–T8*.md`, `docs/thesis/final_results_pack_index.md`, both thesis PDFs (`pdftotext -layout`, cited as
`pdf p.N`), the appendix and figure PNGs (read as images, cited by file), and `METHODOLOGY.md`.

**Citation forms:** `file:line` is in the repository at `6a0fa0f`. "M" is shorthand for `METHODOLOGY.md`. A `glossary:NNNN`
citation is the verified quote in `docs/thesis/glossary.md`, which in turn gives the primary source.

## 0. Counting rule and the counts

There are four categories, each counted separately. Nothing has been moved between categories to meet the target.

| category | what it holds | count |
|---|---|---|
| **Vocabulary terms** (the ≤ 50 target) | experiment and sub-study names, dataset and condition names, criterion names, and label and build names (§2–§4) | **47 rows; 53 distinct names** (rows 10, 35, 44 and 46 each bundle two or three names: +2, +1, +2, +1). The ≤ 50 target is met by rows, not by distinct names |
| Methodological labels | as worded, post hoc, descriptive, confirmatory, exploratory, withdrawn, PENDING. These are defined in `docs/thesis/methodology_definitions_draft.md` and are not repeated here | 7 |
| Numbered hypothesis labels | H1.1 … H5.7, plus the comparison labels C1.a and X1.b and the validation check V3 (§5) | 32 + 3 |
| Abbreviations | §7 (front matter) | 34 |

The figure and table numbering (§6) is a scheme, not a term.

## 1. Experiment numbering: the decisions

| no. | thesis name | repo code | what it contains | defining source |
|---|---|---|---|---|
| **1** | **Corridor comparison** | (none; the `dsn`/`fwdc`/`fwdplainc` datasets, Phases 3–5, the F tests, plan step 2, the closed-loop "Part 2" sets) | **1A** the standard-sensor three-way comparison on the textured, blank and transition floors. **1B** the forward-camera heading sub-studies (measurement validation, offline fusion, the F tests, robust weighting). **1C** the closed-loop corridor flights | M:861 ("Comparison dataset — nomag"); M:2636 (Phase 3); M:2954 (Phase 4, glossary:627); M:7877 (F tests); M:4927 (closed loop, revised) |
| **2** | **Known tags** | Experiment T | AprilTag fixes at known positions; 4 tag densities (conditions A–D) × 3 | M:10100, M:10102 (glossary:517) |
| **3** | **Loop closure** | Experiment L | tags at unknown positions; keyframe FGO with or without loop closure | M:10452, M:10454 (glossary:505) |
| **4** | **Outdoor–indoor** | Experiment O | GNSS outside only; 123 s indoors on IMU, flow and LiDAR | M:10290, M:10292 (glossary:511) |
| **5** | **Tag hold** | Experiment H | marker-relative holding on a wall tag; S0–S3 stages; **5S** the safety tests | `docs/tag_hold_design.md:1`; M:10623 (glossary:500) |

**Decisions, stated:**

1. **The closed-loop corridor flights are Experiment 1C, not a separate experiment.**
   - They fly the same corridor (`corridor_textured_fwdc`, and its half real-time-factor copy) with the same camera heading
     as 1B.
   - Their question is the 1B question with the estimator in the loop. Without a heading source every estimator reaches the
     west wall; with one, every final build passes (numbers.md:462-472).
   - Their criteria are pre-registered as "Part 2" of the forward-camera work (M:4927).
2. **The safety tests are Experiment 5S.**
   - They were flown in the H configuration at the 2 m-clearance hold (numbers.md:482).
   - Appendix A2 tabulates them beside the H sets (`figures_thesis/index.md:26`, `A2_H_and_safety_p2.png`).
   - They test the closed-loop backends rather than a hold hypothesis. They therefore carry criteria (S-A1–S-A4) and no
     hypothesis numbers.
3. **Real-flight readiness is not an experiment and gets no number.**
   - It has no simulation result. Simulation results are frozen (M:13396-13399).
   - Rung 1 is the priority, rung 3 a planned goal and rung 2 parked (M:13397-13398).
   - It belongs in a closing chapter, "Towards real flights" (§6). Its one open item, the rung-1 first-leg length, is there and only there: it is not a thesis result (ruling 2026-10-16, item 4; `docs/thesis/pending_items.md`).
4. **Experiments 2–5 keep the order 2 T, 3 L, 4 O, 5 H, as instructed.** This differs from the order of the
   pre-registrations in the repository's record (M:10100 T, M:10290 O, M:10452 L).

## 2. Experiment, sub-study and dataset names (vocabulary terms 1–16)

| # | thesis name | repo code(s) | source |
|---|---|---|---|
| 1 | Experiment 1, corridor comparison | (see §1) | §1 |
| 2 | Experiment 2, known tags | Experiment T | M:10100 |
| 3 | Experiment 3, loop closure | Experiment L | M:10452 |
| 4 | Experiment 4, outdoor–indoor | Experiment O | M:10290 |
| 5 | Experiment 5, tag hold | Experiment H | M:10623 |
| 6 | 1A standard-sensor comparison | `dsn_*` batch | glossary.md:101 ("nomag comparison batch, `gnss_denied_nomag.parm`, `EK3_SRC1_YAW=0`") |
| 7 | 1B camera-heading studies | Phase 3, Phase 4, Phase 5, F1–F3c, plan step 2(a)/(b) | M:2636; M:2954; M:3392; M:7877; M:9729 |
| 8 | 1C closed-loop corridor flights | `cl_*`; "Part 2" | M:4927; glossary.md:122-137 |
| 9 | 5S safety tests | `H_safety_*`; safety (a)/(b) | M:11289-11293 |
| 10 | textured floor / blank floor / transition floor | `tex` / `blank` / `trans` | glossary.md:109 |
| 11 | standard-sensor dataset | `dsn` | glossary.md:101 |
| 12 | compass reference dataset | `ds` | glossary.md:102 ("compass-active … SUPERSEDED for the three-way comparison") |
| 13 | textured-wall camera dataset (upper bound) | `fwdc` | glossary.md:105; CLAUDE.md:40 |
| 14 | plain-wall camera dataset (featureless case) | `fwdplainc` | glossary.md:106; CLAUDE.md:40 |
| 15 | camera calibration flights | `p1c_*` | glossary.md:118; M:2750 |
| 16 | robust-weighting replication flights | `f4_*` | glossary.md:107 ("plan step 2(a) fresh open-loop flights") |

*"Floor" is used for the downward condition and "wall" for the forward condition, never the other way round.* No source
expands the letters "ds", "dsn", "c" or "f4" (glossary.md:112). The thesis names above are descriptions, not expansions.

## 3. Criterion names, in words (vocabulary terms 17–35)

| # | thesis name | repo code | definition (operative pre-registration) |
|---|---|---|---|
| 17 | **cruise ATE** | `evo -a (cruise)` | SE(3)-aligned ATE over the pinned cruise window, computed only by `eval/three_way_eval.py` (M:21; glossary:4677) |
| 18 | **noise floor** | `dsn` noise floor | the run-to-run SD of cruise ATE on the re-flown textured `dsn` (numbers.md:229, 715) |
| 19 | **dataset-quality bands** | P1–P4 (forward-camera Phase 1/2 criteria) | timing, latency, flow-condition and outcome bands (M:1711-1716) |
| 20 | **contact window** | closed-loop set (a) PRIMARY; U3 | west-wall contact inside the registered window: EKF3 [+155, +215] s (M:4948), UKF [+146, +218] s (M:7513), FGO [+145, +196] s (M:8995) |
| 21 | **early-contact bound** | U2 | no wall contact before cruise +100 s (M:7352) |
| 22 | **backend take-off criterion** | U1 | the backend flies the vehicle through arming, take-off to ≥ 1.8 m and entry into cruise (M:7350) |
| 23 | **mission completion** | B1 | full mission and landing with no wall contact, \|x\| < 9.58 m (M:4951) |
| 24 | **cross-track bound** | B2 | maximum cross-track in cruise ≤ 6.0 m (M:4953) |
| 25 | **heading-error bound** | B3 | yaw error p95 ≤ 1.0°, maximum ≤ 2.0° (M:4958) |
| 26 | **lateral-speed bound** | B4 | 1 s-smoothed \|GT lateral speed\| ≤ 0.25 m/s (M:4963) |
| 27 | **oscillation bound** | B5 | cruise gyro rms roll ≤ 0.05, pitch ≤ 0.0108, yaw ≤ 0.02 rad/s (M:4966; window fixed by D28, M:9943) |
| 28 | **estimator-validity criterion** | S2 (closed-loop set, UKF/FGO) | the flying estimator is valid throughout (M:7362; FGO: `XFGO.OV` 100 %, M:9277) |
| 29 | **hold accuracy** | H-H1's bound | hold error mean ≤ 0.05 m, max ≤ 0.15 m (M:10687) |
| 30 | **drift band** | P-H5 | drift during each tag loss within its per-loss band, UKF 2× (M:10689; glossary:2597) |
| 31 | **re-lock time** | P-H6 | from the first returning tag detection (M:10695; redefined M:10948) |
| 32 | **lockout criterion** | P-H7 | no estimator locks out the returning tag (M:10700) |
| 33 | **attitude criterion** | S-A1 | \|roll/pitch − GT\| ≤ 3°, \|yaw − GT\| ≤ 5° (M:11295) |
| 34 | **position-lost declaration** | S-A2 | "position lost" and LAND within the bound: 0.75 s, UKF (b) 5.5 s (M:11297, M:11300) |
| 35 | **safe landing** / **single landing** | S-A3 / S-A4 | ≤ 1.5 m drift to touchdown with no watcher breach (M:11301); a single landing, for (b) runs only (M:11307) |

## 4. Labels and build names (vocabulary terms 36–47)

| # | thesis name | repo code(s) | source / note |
|---|---|---|---|
| 36 | **live** | live | "the current (filtered) estimate at each time" (M:7937). **Defined again for Experiment 3:** "the newest keyframe after each iSAM2 update" (M:10476). glossary_flags.md:94 records the clash |
| 37 | **hindsight** | hindsight; FGO batch; RTS-UKF | the full-trajectory estimate after the flight (M:7938). In Experiments 2 and 4 this is the FGO whole-flight batch and the smoothed UKF (M:10146). In Experiment 3 it is iSAM2's full estimate (M:10557, a deviation) |
| 38 | **smoothed UKF** | RTS-UKF | "the unscented RTS smoother over the UKF's predict nodes" (M:10146) |
| 39 | **passive estimator** (write who flies: "passive, EKF3 flying" or "passive, truth flying") | shadow | three meanings (glossary_flags.md:93; glossary:3596) |
| 40 | **final build** (UKF: "final UKF port"; FGO: "final FGO node") | UKF `_v2`; FGO `_v3` / S3v2 | UKF v2 = jitter-corrected port `abb0357d` (numbers.md:458); FGO v3 = noise fix + gated yaw cap, node `f642cd37` (numbers.md:458; `tools/run_fgo_refly.sh:2`) |
| 41 | **ablation build** | FGO `_v2`, S3 | FGO noise fix only, yaw cap ungated (numbers.md:458, 466) |
| 42 | **earlier build** | UKF v1 / "old UKF (jitter)"; "original FGO" | numbers.md:458 |
| 43 | **corrected-priors node** | FGO v4 (`4c07374b`) | flown only in the v4 safety re-tests (T7:9; M:13686) |
| 44 | **initial-uncertainty correction** (original priors / corrected priors) | D18 model correction; OLD / NEW priors | FGO initial yaw σ 1e-3 rad → 1°, roll/pitch 2° → 5° (numbers.md:30-31; glossary:3549, 3534) |
| 45 | **half real-time (RTF 0.5)** (always so written, never "half speed"). One-line explanation, used wherever it first appears: **"the simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s"** (ruling 2026-10-16, captions) | `_half`; "half speed"; `corridor_textured_half_fwdc` | "half SIM speed, not half velocity" (glossary.md:134; M:7795, M:7829-7830) |
| 46 | **forced-invalid test** / **node-kill test** | safety (a) PARAM / (b) KILL | UKF (a): `AHRS_UKF_TFAIL` set in flight; (b): SIGKILL of the aiding bridges; FGO (a)/(b): node SIGKILL without / with the watcher watching the node (M:11289-11293). Note that the FGO's (a) is also a kill |
| 47 | **runaway magnitude** (marker †) | † | "evidence of divergence, not precise values" (numbers.md:682-690) |

**Set letters.** The closed-loop "set (a) / set (b)" (M:4841-4842) is written in the thesis as **"without heading / with heading"**.
The safety "(a)/(b)" is written as term 46. **The thesis never writes a bare (a) or (b).**

## 5. Hypotheses, numbered within each experiment

Each label maps to its internal code and to the **operative pre-registration line** (not the result line).

- **"H"** marks a hypothesis or prediction with a decision rule.
- **"C"** marks a pre-registered comparison with no decision rule.
- **"X"** marks an exploratory, non-pre-registered analysis.
- **"V"** marks a validation check.

### Experiment 1 (corridor comparison)

| thesis label | name in words | internal code | operative source | verdict now (source) |
|---|---|---|---|---|
| H1.1 | standard-sensor ordering, EKF3 vs FGO (confirmatory) | the r4–r10 paired test ("EKF3 lower") | M:5638, rule M:5649-5656 | "no ordering claimed" (numbers.md:227; claim 2 WITHDRAWN) |
| H1.2 | heading-measurement validation | Phase 3 validation | M:2636 | heading: `fwdc` 9/9, `fwdplainc` 6/9 (numbers.md:329) |
| H1.3 | heading-fusion prediction | Phase 5 prediction (heading share falls; residual "roughly unchanged") | M:1332, M:1336 | part (b) FAIL as worded, 10/12 (M:3447) |
| (analysis, H1.3) | **heading-error decomposition of sideways drift** | Phase 5 decomposition (`plots/lateral_checks.py` method) | method M:3400-3404; the Phase 5 test reads it, M:1336-1338 | the analysis H1.3 is judged on, not a hypothesis. The lateral-velocity error (estimated − true) is split into a heading-driven part, speed × (sin ψ_est − sin ψ_true), and a residual; integrated, the heading-driven part is the sideways (cross-track) drift caused by the estimator's own heading error. Values: numbers.md §6.3 (Phase 5 decomposition row) |
| C1.a | FGO vs UKF with heading | C0 ("REPORT, no decision rule") | M:7892 | FGO lower 6/6 (numbers.md:298) |
| H1.4 | robust-weighting test | F1 (pre-registered) | M:7899 (block M:7877) | NOT met, lockout tie (numbers.md:501) |
| X1.b | robust vs hard-gated FGO, same bags | F1 EXPLORATORY | M:8460 | exploratory (M:8436) |
| H1.5 | hindsight heading correction | F2 | M:7926 | MET (numbers.md:502) |
| H1.6 | large initial heading error | F3 | M:7945 | NOT met (numbers.md:503) |
| H1.6b | nonlinearity test, redesigned | F3b | M:8485 | (a) TRUE, (b) FALSE (numbers.md:504) |
| H1.6c | convergence speed in the UKF's valid range | F3c | M:8943 | (a) FALSE, (b) TRUE, FRAGILE (numbers.md:505) |
| H1.7a | robust-weighting replication: yaw maximum (primary) | plan step 2(a) P1 | M:9730 | FAIL 7/12 (numbers.md:489) |
| H1.7b | replication: fewer wrong headings (secondary) | 2(a) S1 | M:9733 | PASS 5/6 (numbers.md:490) |
| H1.7c | replication: cross-track (secondary) | 2(a) S2 | M:9737 | FAIL 5/12 (numbers.md:491) |
| H1.8 | closed loop without heading: contact prediction | set (a) PRIMARY (EKF3); U1–U3 (UKF, FGO) | M:4948; M:7350, 7352, 7513; M:8995 | EKF3 MISS at RTF 0.5 (D21); UKF, FGO PASS (numbers.md:462-465) |
| H1.9 | closed loop with heading: criteria pass | set (b) B1–B5 (+S2) | M:4951-4966; M:7362 | 3/3 each final build (numbers.md:469-472) |
| (criteria) | dataset-quality bands | P1–P4 | M:1711-1716 | `fwdc` 7/9, `fwdplainc` 7/9, `p1c` 6/6 (numbers.md:326-328) |

### Experiment 2 (known tags)

| label | name | code | source |
|---|---|---|---|
| H2.1 | FGO hindsight gain grows with the gap (primary) | H-T1 | M:10171 |
| H2.2 | the same for the smoothed UKF | P-T2 | M:10176 |
| H2.3 | live errors similar | P-T3 | M:10178 |
| H2.4 | FGO hindsight ≈ smoothed UKF | P-T4 | M:10180 |

### Experiment 3 (loop closure)

| label | name | code | source |
|---|---|---|---|
| V3 | estimator validation check (not re-scorable, ruling 6) | V-L | M:10486, M:10490; M:12706 |
| H3.1 | loop closure bounds live drift (primary) | H-L1 | M:10501 |
| H3.2 | live error lower with loop closure | H-L2 | M:10503 |
| H3.3 | hindsight error lower with loop closure | H-L3 | M:10504 |
| H3.4 | without loop closure, drift grows lap on lap | P-L4 | M:10505 |

### Experiment 4 (outdoor–indoor)

| label | name | code | source |
|---|---|---|---|
| H4.1 | FGO hindsight beats the filters' live tracks indoors (primary) | H-O1 | M:10358 |
| H4.2 | live indoor errors similar | H-O2 | M:10360 |
| H4.3 | FGO batch ≈ smoothed UKF | P-O3 | M:10362 |

### Experiment 5 (tag hold)

| label | name | code | source |
|---|---|---|---|
| H5.1 | hold accuracy (primary) | H-H1 | M:10687 (S1 pre-registration, EKF3 flying). Design draft "every estimator": `tag_hold_design.md:176` (glossary:2411 notes the difference) |
| H5.2 | FGO holds tightest | H-H2 | `tag_hold_design.md:180` (no METHODOLOGY pre-registration line; the verdict is at M:12236) |
| H5.3 | smoothness similar | P-H3 | `tag_hold_design.md:183` |
| H5.4a | after a 15 s loss, EKF3 jumps most | H-H4 (15 s) | `tag_hold_design.md:184-186` |
| H5.4b | after a 5 s loss, jumps similar | H-H4 (5 s) | `tag_hold_design.md:187` |
| H5.5 | drift band | P-H5 | M:10689 (per-loss bands). Draft "15 s ≤ 0.3 m": `tag_hold_design.md:188`, which is the wording the comparative verdict applies (M:12243) |
| H5.6 | re-lock time | P-H6 | M:10695; redefined M:10948 |
| H5.7 | no lockout | P-H7 | M:10700 |
| (criteria, 5S) | attitude / position-lost declaration / safe landing / single landing | S-A1–S-A4 | M:11295-11307 |

**Count:** 32 hypothesis labels: H1.1–H1.9 with sub-labels (13), H2.1–H2.4 (4), H3.1–H3.4 (4), H4.1–H4.3 (3) and
H5.1–H5.7 with 5.4a/b (8). There are also 3 labels of other kinds: C1.a, X1.b and V3.

## 6. Figure and table numbering: proposal

**Proposed: by chapter** ("Figure n.m", "Table n.m", appendix "Table A.m").

Why not flat:
- Five experiments over several chapters, plus an appendix, make flat numbers long and fragile when chapters move.
- The repository's flat F/T/A codes already collide with six or more other code families (glossary_flags.md:11-53).

The chapter plan is **provisional** and is the user's to set. The mapping below assumes it.

| proposed chapter | content |
|---|---|
| 3 | Method: simulator, worlds, sensors, estimators, metrics |
| 4 | Experiment 1 |
| 5 | Experiments 2–4 |
| 6 | Experiment 5 |
| 7 | Synthesis across experiments |
| 8 | Towards real flights (unnumbered work, no results) |
| A | Appendix |

| current id (repo) | file | proposed thesis number |
|---|---|---|
| F2 | `figures_thesis/F2_heading_stops_sideways_drift.*` | **Figure 4.1** |
| T2 | `tables/T2_accuracy_heading.*` | **Table 4.1** |
| T3 | `tables/T3_blank_floor.*` | **Table 4.2** |
| T4 | `tables/T4_closed_loop.*` | **Table 4.3** |
| F5 | `figures_thesis/F5_T_tags_known_positions.*` | **Figure 5.1** (Experiment 2) |
| F7 | `figures_thesis/F7_L_loop_closure.*` | **Figure 5.2** (Experiment 3) |
| F6 | `figures_thesis/F6_O_outdoor_indoor.*` | **Figure 5.3** (Experiment 4) |
| T6 | `tables/T6_O_indoor_rmse.*` | **Table 5.1** |
| T8 | `tables/T8_hindsight_ratio.*` | **Table 5.2** (spans Experiments 2 and 4) |
| T5 | `tables/T5_H_tag_loss_drift.*` | **Table 6.1** |
| T1 | `tables/T1_scorecard.*` | **Table 7.1** |
| T7 | `tables/T7_failure_behaviour.*` | **Table 7.2** (spans Experiments 1, 4 and 5S) |
| A1 | `figures_thesis/A1_closed_loop_builds.png` | **Table A.1** |
| A2 | `figures_thesis/A2_H_and_safety_p1.png`, `_p2.png` | **Table A.2** (two parts) |
| A3 | `figures_thesis/A3_F1_cost_ablations_p1.png`, `_p2.png` | **Table A.3** (two parts) |
| world pages | `world_images/worlds_combined.pdf` pp. 1–25 | Chapter 3 figures (3.m), chosen when Chapter 3 is drafted; not numbered here |

The repository files keep their names. Only the printed captions take the new numbers. The old pack numbers (F01–F15b) and
the pre-2026-10-16 thesis numbers (F1, F3, F4, F8) are not used in the thesis (§8.1 rows 4–5).

## 7. Abbreviations (front matter; 34)

"Repo" means that the expansion is written in the repository, at the location cited. **"Standard expansion, not in the repo"**
means that a search of CLAUDE.md, METHODOLOGY.md, FGO_DESIGN.md, `docs/`, `src/` and `eval/` found no written expansion
(searches run 2026-10-16). "Co-occurrence" means that the long form appears beside the abbreviation but is not written as
a definition.

| abbreviation | expansion | status / source |
|---|---|---|
| AHRS | attitude and heading reference system | standard expansion, not in the repo |
| ATE | absolute trajectory error | standard expansion, not in the repo (glossary:3288: UNDEFINED) |
| CI | confidence interval | standard expansion, not in the repo. Used as the "95% t-interval" (M:5652) |
| EKF | extended Kalman filter | standard expansion, not in the repo (glossary:3363: UNDEFINED; used CLAUDE.md:5) |
| EKF3 | ArduPilot's EKF3 (third-generation extended Kalman filter), the fixed baseline | the repo defines its role, not the name: "ArduPilot EKF3 is the fixed baseline" (CLAUDE.md:969); "EKF3 is `3`" (CLAUDE.md:759). The "third-generation" gloss is standard, not in the repo |
| ENU | east–north–up | repo: CLAUDE.md:376 (axis definitions) |
| ExtNav | external navigation (EKF3's external-navigation source) | co-occurrence only: "using external nav data" (M:5034). Otherwise standard, not in the repo (glossary:3389: UNDEFINED) |
| FC | flight controller | repo: "the flight controller (FC)" (`docs/rung1_preregistration.md:58`) |
| FGO | factor graph optimisation | repo: "online Factor Graph Optimisation (FGO)" (CLAUDE.md:5) |
| FLU | forward–left–up (body frame) | standard expansion, not in the repo (glossary:3450) |
| FRD | forward–right–down (body frame) | standard expansion, not in the repo (glossary:3454) |
| GNSS | global navigation satellite system | standard expansion, not in the repo (used CLAUDE.md:6) |
| GT | ground truth (simulator truth; motion capture later) | standard expansion, not in the repo (glossary:2360: UNDEFINED). **Never used for "ground test"** (glossary_flags.md:88) |
| GTSAM | Georgia Tech Smoothing and Mapping (library) | standard expansion, not in the repo |
| HAGL | height above ground level | standard expansion, not in the repo (glossary:3469). The repo's "height above ground" (CLAUDE.md:1095) describes `p_U`, not HAGL |
| IMU | inertial measurement unit | ArduPilot source: "Inertial Measurement Unit data" (`~/ardupilot/libraries/AP_InertialSensor/LogStructure.h:45`, glossary:4139) |
| iSAM2 | incremental smoothing and mapping, version 2 | standard expansion, not in the repo |
| LiDAR | light detection and ranging | standard expansion, not in the repo |
| LM | Levenberg–Marquardt | co-occurrence: `gtsam.LevenbergMarquardtParams()` (`src/estimators/fgo/fgo_core.py:88`) |
| LSD | line segment detector | standard expansion, not in the repo (glossary:3517: UNDEFINED) |
| MAVLink | Micro Air Vehicle Link (protocol) | standard expansion, not in the repo |
| mocap | motion capture | co-occurrence: "motion capture" (CLAUDE.md:10), "motion-capture ground truth" (M:2862) |
| NED | north–east–down | repo: CLAUDE.md:376 |
| NEES | normalised estimation error squared | standard expansion, not in the repo (glossary:4730; the "consistent ≈ 1" use is at M:3712) |
| NIS | normalised innovation squared | standard expansion, not in the repo (glossary:4739) |
| RANSAC | random sample consensus | standard expansion, not in the repo |
| RMSE | root-mean-square error | standard expansion, not in the repo |
| RPE | relative pose error | standard expansion, not in the repo (glossary:3575: UNDEFINED) |
| RTF | real-time factor | repo: "real-time factor (RTF)" (CLAUDE.md:156) |
| RTS | Rauch–Tung–Striebel (smoother) | standard expansion, not in the repo (glossary:3579: UNDEFINED; usage M:10146) |
| SITL | software in the loop | standard expansion, not in the repo (glossary:3603: UNDEFINED) |
| UAV | uncrewed aerial vehicle | standard expansion, not in the repo (used CLAUDE.md:6) |
| UKF | unscented Kalman filter | standard expansion, not in the repo. Only "unscented RTS smoother" (M:10146) appears |
| VP | vanishing point | co-occurrence: "corridor vanishing point … near the VP" (CLAUDE.md:157). Otherwise standard, not in the repo (glossary:3138: UNDEFINED) |

**Not abbreviations, glossed separately:**
- **evo** is the evaluation tool (`evo_ape`/`evo_rpe`, CLAUDE.md:25). The thesis writes "cruise ATE" (term 17) and names evo
  only as the tool.
- **D18** is a ruling, not an abbreviation: decision-queue entry 18 (`docs/decisions_queue.md:171`). Its principle is
  "sensor-validity rules are shared; design features are not" (PROGRESS.md:47; M:7785). The thesis writes "the
  initial-uncertainty correction" (term 44) for the "D18 model correction". **No D-number appears in the thesis text**
  (§8.2).
- **ArduPilot**, **Gazebo**, **ROS 2** and **GTSAM** are product names. They are cited, not expanded (GTSAM is listed above
  only because readers ask).

## 8. Internal codes in thesis-facing material that had NO thesis name

**Scope swept:**
- the captions and notes of `docs/thesis/tables/T1–T8*.md`;
- the caption and check lines of `docs/thesis/figures_thesis/index.md`;
- `thesis_figures_combined.pdf` (19 pages) and `worlds_combined.pdf` (25 pages), by page;
- the A1–A3 and F2/F5/F6/F7 images, by reading them;
- the numbers.md rows these cite: §6.1 (217-238), §6.2 (239-253), §6.4 (264-274), §6.6 (286-305), §15–§15.2 (454-505),
  §16.1–§17.2 (507-663) and §18 (665-680).

The sweep was a mechanical token match, plus a second pass for lowercase dataset tokens, markers, and "claim n" / "ruling n".

**Result:** **65 code families** appear in that material, and **none** had a thesis name in the repository.
- **This vocabulary names 41.** The thesis names are given beside each.
- **24 are left unnamed on purpose.** These are file names, JSON keys, commit hashes, trial names, log-message names and
  ruling/claim numbers. The recommendation for these is to **remove them from captions**, and to keep them only in the
  appendix data statement or in §9.

### 8.1 Named by this vocabulary (41)

| # | code(s) | where (first locations) | thesis name |
|---|---|---|---|
| 1 | F2, F5, F6, F7 | `figures_thesis/index.md:13-16`; `thesis_figures_combined.pdf` p.1 | Figure 4.1, 5.1, 5.3, 5.2 |
| 2 | T1–T8 | `tables/T1…T8*.md:1`; pdf p.1 | Table 7.1, 4.1, 4.2, 4.3, 6.1, 5.1, 7.2, 5.2 |
| 3 | A1–A3 | `figures_thesis/index.md:25-27`; `T4_closed_loop.md:11` | Table A.1–A.3 |
| 4 | F1, F3, F4, F8 (old thesis figure numbers) | `thesis_figures_combined.pdf` p.1; `worlds_combined.pdf` pp.1, 2, 4, 5, 8, 9, 10, 19, 20, 22 | the new numbers (row 2): F1 → Table 7.1, F3 → Table 4.1, F4 → Table 4.2, F8 → Table 6.1. **The worlds PDF needs regenerating** (glossary_flags.md:45) |
| 5 | F01–F15b (pack figures) | `figures_thesis/index.md:237, 254, 274`; `worlds_combined.pdf` pp.1, 2, 4, 10, 18–20, 22 | not cited in the thesis. "replaces pack F15a" is dropped from captions |
| 6 | B1–B5 | `T4_closed_loop.md:3, 5`; `F2` caption (index.md:37); `A1` image | terms 23–27 |
| 7 | S2 (closed-loop "+S2") | `T4_closed_loop.md:3`; index.md:115 | term 28 |
| 8 | U1–U3 | numbers.md:465-466 | terms 20–22 |
| 9 | C0 | `T1_scorecard.md:8`; `T2_accuracy_heading.md:3, 13` | comparison C1.a, "FGO vs UKF with heading" |
| 10 | F1 (offline test) | `A3_*` images; `figures_thesis/index.md:274`; numbers.md:501 | H1.4, robust-weighting test |
| 11 | F2, F3, F3b, F3c (offline tests) | numbers.md:502-505 | H1.5, H1.6, H1.6b, H1.6c |
| 12 | 2(a) P1/S1/S2; 2(b) | numbers.md:489-495 | H1.7a–c; 2(b) as "the robust closed-loop set" (descriptive) |
| 13 | H-T1, P-T2, P-T3, P-T4 | `T1_scorecard.md:10`; `T8_hindsight_ratio.md:3`; F5 image; pdf p.3 | H2.1–H2.4 |
| 14 | H-L1, H-L2, H-L3, P-L4, V-L | `T1_scorecard.md:12`; index.md:80; pdf p.5 | H3.1–H3.4; V3 |
| 15 | H-O1, H-O2, P-O3 | `T6_O_indoor_rmse.md:3, 14`; `T1_scorecard.md:11`; pdf p.4 | H4.1–H4.3 |
| 16 | H-H1, H-H2, P-H3, H-H4, P-H5, P-H6, P-H7 | `T5_H_tag_loss_drift.md:12, 14`; `T1_scorecard.md:18`; numbers.md:598-662 | H5.1–H5.7 (5.4a/b) |
| 17 | S-A1–S-A4 | `T7_failure_behaviour.md:3, 8, 11`; `A2_*_p2.png` | terms 33–35 |
| 18 | S0a, S0b, S1, S1 far, S2, S2v2, S3, S3v2 (H stages) | `T5_H_tag_loss_drift.md:5, 16`; `A2_*_p1.png`; `worlds_combined.pdf` p.19; numbers.md:583-629 | Experiment 5 stages, written in words: "characterisation (S0a)", "check flight (S0b)", "EKF3-flying hold set" (S1; "far spawn" for S1 far), "UKF-flying hold set" (S2v2, final; S2, earlier build), "FGO-flying hold set" (S3v2, final; S3, ablation build) |
| 19 | v1, v2, v3, v4; `_v2`, `_v3` | `T1_scorecard.md:14`; `T4_closed_loop.md:8-9`; `T7_failure_behaviour.md:8-9`; A1–A3 images | terms 40–43 |
| 20 | (a)/(b) closed-loop sets | `cl_a`/`cl_b` (glossary.md:130-131); F2 caption | "without heading / with heading" |
| 21 | (a)/(b) safety; PARAM; KILL | `T7_failure_behaviour.md:5`; `A2_*_p2.png` | term 46 |
| 22 | OLD priors / NEW priors | `T1_scorecard.md:14`; `T4_closed_loop.md:9`; `T7_failure_behaviour.md:9` | term 44 |
| 23 | ABLATION | index.md:237; pdf p.14 | term 41 |
| 24 | "half speed", `_half`, `corridor_textured_half_fwdc` | F2 caption (index.md:37); `T4_closed_loop.md:1`; A1 image; `worlds_combined.pdf` p.10 | term 45. **The caption wording "half speed" is misleading and needs changing** (glossary_flags.md:90). **DONE 2026-10-16:** every thesis-facing caption, table and both PDFs now read "half real-time (RTF 0.5)" |
| 25 | `dsn`, `dsn_tex`, `ds_*` | `T1_scorecard.md:20`; `T2_accuracy_heading.md:5`; `worlds_combined.pdf` pp.1–3 | terms 11, 12 |
| 26 | `fwdc`, `fwdplainc`, `fwdc_tex` | `T2_accuracy_heading.md:5`; `T1_scorecard.md:22` | terms 13, 14 |
| 27 | `p1c`, `f4_` | `T3_blank_floor.md:11`; `worlds_combined.pdf` pp.4–9 | terms 15, 16 |
| 28 | `tex` / `trans` / `blank` | throughout | term 10 |
| 29 | conditions A–D; `T_A`…`T_D` | F5 caption (index.md:50); `T8_hindsight_ratio.md:7-10` | "condition A–D" (kept; see §10) |
| 30 | Phase 3, Phase 5 | `T2_accuracy_heading.md:3, 13, 15` | H1.2 "heading-measurement validation"; H1.3 "heading-fusion prediction" |
| 31 | LC / no-LC / `nolc` | index.md:31, 88-89, 284-287; A3 image | "with / without loop closure" |
| 32 | RTS-UKF | `T6_O_indoor_rmse.md:10`; `T8_hindsight_ratio.md:5`; F5, F6 images | term 38 |
| 33 | FGO batch | `T6_O_indoor_rmse.md:11`; `T8_hindsight_ratio.md:1` | "FGO whole-flight batch" (term 37) |
| 34 | `FGO_hard`, `UKF_hard`, `FGO_robust` | index.md:281-283; A3 image | "hard-gated FGO / hard-gated UKF / robust FGO" |
| 35 | live, hindsight, shadow | tables T1, T6, T8; `worlds_combined.pdf` pp.1, 10 | terms 36, 37, 39 |
| 36 | † | `T1_scorecard.md:9`; `T3_blank_floor.md:8`; pdf p.1 | term 47 |
| 37 | evo; `evo -a (cruise)` | `T2_accuracy_heading.md:11`; pdf p.1 | term 17 |
| 38 | noise floor | numbers.md:229 | term 18 |
| 39 | P4 band | numbers.md:274; `worlds_combined.pdf` | term 19 |
| 40 | "Python bridge" / "C++ bridge"; `bcpp` | A1 image; `T4_closed_loop.md:13` | "EKF3 with the Python / C++ heading node" (descriptive; not a vocabulary term) |
| 41 | watcher (watcher breach; "the watcher watches the node") | `T7_failure_behaviour.md:8, 11` | "safety watcher" (descriptive; not a vocabulary term) |

### 8.2 Left unnamed on purpose: remove from captions (24)

**Applied 2026-10-16** (rulings of 2026-10-16, captions item): these families were removed from the figure and table captions,
the table notes and cells, and the caption pages of both thesis PDFs, in one pass. The sources now live only in
`docs/thesis/figures_thesis/index.md` (inputs, numbers.md rows and the cross-checks). Rows 22–24 are glossed at first use, as
their handling column says, so they remain. Trial names and build hashes remain only in the appendix tables (A2's trial and
build columns) and the worlds PDF (the appendix world table), as rows 15, 16 and 18 allow. The residual hits are listed in
`docs/handovers/2026-10-16_pending_rulings_applied.md`.

| # | code(s) | where | handling |
|---|---|---|---|
| 1 | D21, D22 | `T4_closed_loop.md:7, 11`; F2 caption (index.md:37) and image; A1 image | **no D-numbers in the thesis.** Say what was ruled: "the half-RTF contact time lies after EKF3's registered window" (D21, glossary:4990); "a shared flow-validity limitation of the sensor pipeline" (D22, M:12642) |
| 2 | D8, D15, D18, D23, D27, D28, D2 | numbers.md:231, 230, 295, 477, 186, 454/471, 534 | the same: describe the ruling. D18 → term 44 |
| 3 | "claim n" (claims 1a–35) | `T1_scorecard.md:7-12, 22`; `T2_accuracy_heading.md:17`; index.md:39 onwards | replace with a section or table reference. Claim numbers are the claims table's (`headline_claims_before_after.md:14-50`) |
| 4 | "ruling n", "restatement ruling n", "EKF3 ruling 2026-09-29" | `T1_scorecard.md:8, 10, 18`; `T2_accuracy_heading.md:11`; F5/F7 captions (index.md:50, 80); numbers.md:226-305 | cite the ruling once in the methodology chapter; captions say "by ruling" at most |
| 5 | "pack flag 1/2/3" | numbers.md:454, 570, 617 | drop |
| 6 | correction (i), (iii) | numbers.md:259, 281 | describe the correction |
| 7 | OI-2 | numbers.md:117-118 (cited via §2) | "IMU sensor-time reconstruction" |
| 8 | P5b | numbers.md:305 | drop (an internal analysis label) |
| 9 | ⚑ | `T7_failure_behaviour.md:8, 9, 13` | replace with a footnote mark. ⚑ has two meanings (glossary_flags.md:98) |
| 10 | `XKF1`, `SIM`, `XFGO.OV`, `XUKS.SS` | F2 caption (index.md:37); F6 inputs (index.md:68); numbers.md:466 | "EKF3's logged state", "simulator truth", "the FGO output-valid flag" |
| 11 | `horiz_pos_abs`, `posTimeout`, `jump_pos_m`, `contact_if_any_west_in_155_215` | numbers.md:530, 557, 639, 463 | describe in words |
| 12 | JSON keys: `ate_a_cruise`, `xtrack_head_m`, `along_m`, `cross_m`, `valid_frames_in_cruise`, `EKF3_invalid_period`, `drift_end_m`, `rearmed_after_disarm`, `max_step_after_return_m`, `markers_bag_s`, `per_lap_rmse_m`, `rmse_m` | `T2:15, 17`; `T3:17`; `T5:14, 18`; `T7:13, 17`; index.md:68, 81 | data statement only |
| 13 | result files: `rerun_dsn_evo.json`, `phase4_*`, `phase5_analysis.json`, `blank_behaviour.json`, `closed_loop_*.json`, `expT/…`, `expO/…`, `expL/…`, `expH/…`, `f1_test.json` | the "Sources" line of every table; index.md "Inputs" lines | data statement only |
| 14 | scripts: `eval/figs_thesis.py`, `fly_trial.py outback()`, `o_gnss.parm`, `closed_loop_run.sh` | every table's last line; index.md:68; `worlds_combined.pdf` p.19 | data statement only |
| 15 | commit hashes: `7778cd6`, `819caab`, `f642cd37`, `4c07374b`, `abb0357d`, `b7a3aca` | tables' last lines; `T2:15`; A2/A3 images; numbers.md:458, 556 | appendix build table only |
| 16 | trial names: `cl_*`, `H_safety_*`, `H_s*`, `T_A_r1–r3`, `O_r1`/`O_r2`/`O_r3b`, `dsn_tex_r1`… | F2/F5/F6/F7 captions; `T6:5`; A2 image; F7 image panel titles | "flight 1–3" in text; trial names in the appendix. `O_r3b` = an unchanged re-fly of r3 (glossary.md:110) |
| 17 | repeat indices r1–r10, r3b | `T2:5`; `T4:3`; `T1:20` | "flight n" / "repeat n" |
| 18 | world names: `corridor_*`, `room_tags`, `room_wall_tag*`, `outdoor_indoor`, `iris_textured`, `iris_runway`, `corridor_tson_fwdc` | `worlds_combined.pdf` pp.1–25; F2/F5 captions | name each world in words in Chapter 3; keep file names in a world table |
| 19 | model names `iris_fwd`, `iris_fwd_ts` | `worlds_combined.pdf` pp.11, 13 | "forward-camera vehicle"; "time-sync variant" |
| 20 | check-flight names: `gt_heading_*`, `rgs_*`, `lfs_check_tex`, `tsx_*`, `tagchar_*`, `tag_check*`, `room_check`, `o_check1`, `*_verify`, `stage_b_verify`, `stage_c_*`, `smoke_test`, `ekf3_diag_60s`, `imu_rate_verify`, `imu_verify2`, `nomag_test_long`, `sweep_v*`, `H_s0a`, `H_gt_*`, `H_wtest_*`, `H_ifa_ekf3`, `p1_fwd_*`, `p1diag_*`, `p1plain_*`, `fwd_*` | `worlds_combined.pdf` pp.1–25 ("flown:" lines) | appendix world table only. Several are undefined (glossary_flags.md:115-193) |
| 21 | `S-A2b` | `A2_H_and_safety_p2.png` note | "a supplementary criterion for future tests" (M:13669) |
| 22 | MAVProxy, SIGKILL | `T7_failure_behaviour.md:11`; A2 image | technical terms; gloss at first use |
| 23 | k = 2.385 | A3 image; numbers.md:501 | a parameter; keep, with its meaning (the M-estimator threshold, M:7905) |
| 24 | `VISO_DELAY_MS`, `AHRS_UKF_TFAIL` | numbers.md:456, 534; M:11289 | parameter names; gloss at first use |

*Not counted (not a code): the source note "S1-far EKF3 drifts … METHODOLOGY only" (`T5_H_tag_loss_drift.md:16`; index.md:175). See `pending_items.md` item 7.*

### 8.3 Added after the sweep (2026-10-17)

| code | where | thesis wording and definition | source |
|---|---|---|---|
| thesis-nav ("EKF3 has no thesis-nav position-lost path"; "no thesis-nav text") | `T7_failure_behaviour.md` (Table 7.2, EKF3 forced-invalid cell); Table A.2 note (`A2_H_and_safety_p2.png`) | **thesis-nav position-lost path** (descriptive; not a vocabulary term): the Copter landing trigger `thesis_nav_check` in the thesis firmware fork. It runs every loop; when the vehicle is armed with the UKF or the FGO as the AHRS type and loses `HORIZ_POS_REL` after having had it since arming, it commands the EKF failsafe action (LAND), with no origin needed, and sends its status text. EKF3 flights use ArduPilot's own EKF failsafe instead, so the trigger and its text do not apply to EKF3 | M:11264-11265; fork `ArduCopter/ekf_check.cpp:337-358` (glossary.md:2964); its status text with mode LAND: glossary_flags.md:915 |

## 9. APPENDIX: mapping table (thesis name → internal code(s) → source)

| thesis name | internal code(s) | source file:line |
|---|---|---|
| Experiment 1, corridor comparison | `dsn`/`fwdc`/`fwdplainc` datasets; Phase 3–5; F1–F3c; plan step 2; closed-loop Part 2 | M:861; M:2636; M:2954; M:3392; M:7877; M:9728; M:4927 |
| 1A standard-sensor comparison | `dsn_*` | M:861; glossary.md:101 |
| 1B camera-heading studies | Phase 3/4/5; F1–F3c; 2(a)/(b) | M:2636; M:2954; M:3392; M:7877; M:9729 |
| 1C closed-loop corridor flights | `cl_*`; sets (a)/(b) | M:4927; M:4841-4842; glossary.md:122 |
| Experiment 2, known tags | Experiment T | M:10100 |
| Experiment 3, loop closure | Experiment L | M:10452 |
| Experiment 4, outdoor–indoor | Experiment O | M:10290 |
| Experiment 5, tag hold | Experiment H | M:10623; `docs/tag_hold_design.md:1` |
| 5S safety tests | `H_safety_*`; S-A1–S-A4 | M:11289-11307 |
| textured / blank / transition floor | `tex` / `blank` / `trans` | glossary.md:109; CLAUDE.md:113-118 |
| standard-sensor dataset | `dsn` | glossary.md:101 |
| compass reference dataset | `ds` | glossary.md:102 |
| textured-wall camera dataset | `fwdc` | glossary.md:105 |
| plain-wall camera dataset | `fwdplainc` | glossary.md:106 |
| camera calibration flights | `p1c_*` | glossary.md:118 |
| robust-weighting replication flights | `f4_*` | glossary.md:107 |
| cruise ATE | `evo -a (cruise)` | M:21 |
| noise floor | `dsn` noise floor | numbers.md:715 |
| dataset-quality bands | P1–P4 | M:1711-1716 |
| contact window | set (a) PRIMARY; U3 | M:4948; M:7513; M:8995 |
| early-contact bound | U2 | M:7352 |
| backend take-off criterion | U1 | M:7350 |
| mission completion | B1 | M:4951 |
| cross-track bound | B2 | M:4953 |
| heading-error bound | B3 | M:4958 |
| lateral-speed bound | B4 | M:4963 |
| oscillation bound | B5 | M:4966; M:9943 |
| estimator-validity criterion | closed-loop S2 | M:7362; M:9277 |
| hold accuracy | H-H1 bound | M:10687 |
| drift band | P-H5 | M:10689 |
| re-lock time | P-H6 | M:10695; M:10948 |
| lockout criterion | P-H7 | M:10700 |
| attitude criterion | S-A1 | M:11295 |
| position-lost declaration | S-A2 | M:11297 |
| safe landing / single landing | S-A3 / S-A4 | M:11301 / M:11307 |
| live | live | M:7937; M:10476 (Experiment 3) |
| hindsight | hindsight; FGO batch | M:7938; M:10476; M:10557 |
| smoothed UKF | RTS-UKF | M:10146 |
| passive estimator | shadow | glossary:3596 |
| final build | UKF v2; FGO v3; S2v2; S3v2 | numbers.md:458; M:12504; M:12565 |
| ablation build | FGO v2; S3 | numbers.md:458, 466, 629 |
| earlier build | UKF v1 (old UKF); original FGO | numbers.md:458 |
| corrected-priors node | FGO v4 `4c07374b` | M:13686 |
| initial-uncertainty correction | D18 model correction; OLD/NEW priors | numbers.md:30-31, 37; M:13686 |
| half real-time (RTF 0.5) | `_half`; "half speed" (banned wording) | M:7795; M:7829-7830; glossary.md:134 |
| forced-invalid test / node-kill test | safety (a) PARAM / (b) KILL | M:11289-11293 |
| runaway magnitude | † | numbers.md:682-690 |
| with / without heading | closed-loop set (b) / (a) | M:4841-4842 |
| with / without loop closure | LC / no-LC | M:10454; numbers.md:563-566 |
| hard-gated / robust FGO | `FGO_hard` / `FGO_robust` | M:7899; numbers.md:501 |
| heading-error decomposition of sideways drift | Phase 5 decomposition | M:3400-3404; M:1336-1338 |
| thesis-nav position-lost path | Copter `thesis_nav_check` | M:11264-11265 |
| H1.1 … H5.7, C1.a, X1.b, V3 | see §5 | §5 tables |

## 10. Departures from the proposed scheme in glossary_flags.md §c

Every row of `docs/thesis/glossary_flags.md:1072-1170` that this vocabulary touches, with its class and the reason.

**Count:**
- **11 departures**: rows 1–9 and 19, plus row 20, which is partial;
- 3 adopted with an extension (rows 10–12);
- 6 adopted (rows 13, 14, 16, 17, 18, 21);
- 2 not taken up, as out of scope (rows 15, 22).

| # | class | flags proposal (line) | this vocabulary | why |
|---|---|---|---|---|
| 1 | departure | Keep the bare **H-/P-/V-** codes, "already unique" (1085) | renumbered **H2.1 …**, with H-T1 etc. kept only in the §9 mapping | The task requires hypotheses numbered within each experiment. The H-/P- split (hypothesis vs prediction) is not explained to a reader, and P-codes collide visually with the P1–P4 and P1–P10 families |
| 2 | departure | **D** is the bare-letter owner: "D → the D-rulings" (1082) | **no D-numbers in the thesis text** | Thesis-facing captions cite D21/D22 with no gloss. The rulings are better described by content. glossary_flags.md:54-58 shows D-codes clash in four families |
| 3 | departure | Figures **"Fig. 1–8"** and tables **"Table 1–8"**, flat (1084, 1119, 1121) | **by chapter**, "Figure 4.1", "Table 7.1" | Five experiments over four results chapters. The thesis now has 4 figures and 8 tables, so flat "Fig. 1–8" would not even match the current set (F2, F5–F7) |
| 4 | departure | Appendix tables **"Table A1–A3"** (1109) | **"Table A.1–A.3"** | consistent with "n.m" chapter numbering. A minor change |
| 5 | departure | Closed-loop criteria **CB1–CB5**, U → **CU1–CU3**, safety S1/S2 → **CS1/CS2** (1103, 1144, 1132) | **criteria named in words** (terms 20–28) | The task asks for criteria in words, not codes |
| 6 | departure | Forward-camera criteria **PC1–PC4** (1134) | **"dataset-quality bands"** (one term) | in words. The four bands are reported together as pass counts (numbers.md:326-328) |
| 7 | departure | Offline tests **OT1–OT4** (OT3b, OT3c), or "F-test 1" (1117) | **H1.4–H1.6c** plus names in words | They are pre-registered decision rules, so they enter the hypothesis numbering. F1's exploratory variant is kept apart as X1.b (M:8460) |
| 8 | departure | 2(a) robust-FGO rules **RS1/RS2** (1132) | **H1.7a–c** | as row 7 |
| 9 | departure | H stages **"H-S0a…H-S3v2"** (1086, 1130) | **written in words** ("EKF3-flying hold set", "UKF-flying hold set (final build)") | a reader needs to know who flies and which build. "S3v2" flies the FGO's **v3** node (glossary:686), so "H-S3v2" keeps that numbering trap |
| 10 | adopted with extension | **"_v2/_v3: name the build in the text"** (1168) | adopted, with fixed names: **final / ablation / earlier build, corrected-priors node** | v3 means different things for the UKF and the FGO (glossary_flags.md:269-273). Four fixed names avoid per-sentence improvisation |
| 11 | adopted with extension | **"_half: write 'half real-time factor (RTF 0.5)'"** (1166) | adopted. It also bans "half speed", which is in the current F2/T4/A1 captions | the current captions use "half speed" (index.md:37; `T4_closed_loop.md:1`) (fixed 2026-10-16) |
| 12 | adopted with extension | **"shadow: always qualify who flies"** (1159) | adopted, as **"passive estimator"** plus who flies | a single noun avoids "shadow" altogether |
| 13 | adopted | **"live / hindsight: define once per experiment"** (1160) | adopted. Defined once (M:7937-7938), with an explicit Experiment 3 redefinition | — |
| 14 | adopted | **"batch: hindsight batch / fixed-lag smoother"** (1161) | adopted, as "FGO whole-flight batch"; the live solver is "fixed-lag smoother" | — |
| 15 | not taken up (out of scope) | **"VOID / FROZEN"** wording (1162-1163) | not in this vocabulary | neither appears in the thesis-facing captions, apart from "results FROZEN" on pdf p.1, which is used as plain English |
| 16 | adopted | **"⚑: one sense only, or replace"** (1164) | **replace with a footnote mark** | ⚑ appears in T7 in a third, informal sense ("scorer artefact") |
| 17 | adopted | **"gt_: write 'ground-test runs'; reserve GT for ground truth"** (1165) | adopted. GT is expanded in §7 | — |
| 18 | adopted | **"Expand the dataset abbreviations at first use … do not invent an expansion"** (1089) | adopted. Terms 11–16 are descriptions, not letter expansions | — |
| 19 | departure | Abbreviation list including **OF** (1169) | OF is omitted | OF (the dataflash flow message) appears in no thesis-facing caption |
| 20 | partial departure | **"as worded", "post hoc", "pre-registered", PENDING, CLOSED: define in the methodology chapter** (1170) | adopted for six terms plus PENDING (`methodology_definitions_draft.md`). **"pre-registered" and "CLOSED" are not drafted** | They were outside this stage's list. "pre-registered" appears 16 times in thesis-facing captions and should be added next |
| 21 | adopted | Experiment T conditions **"condition A–D (never 'T1…')"** (1125) | adopted unchanged | — |
| 22 | not taken up (out of scope) | The many families absent from thesis-facing material (RG, WG, BG, FCB, CV, SG, RW, UQ, …) | **not named here** | they appear in no thesis-facing caption, table or PDF. They belong to the real-flight chapter, if anywhere |

## 11. "n" and the ordering verdicts in the tables (added 2026-10-17)

**n.** In the thesis tables and captions, **n is the number of independent units entering a comparison, and its unit is
always named**: "n = 7 flights", "3 flights per estimator", "6 bags", "24 losses over 6 flights". A bare "n = 3" is not
used. The units in use:

| unit | meaning | where |
|---|---|---|
| **flights** | independent repeats of the same flight profile (a new simulator run each) | H1.1 (7 flights, flights 4–10; 6 usable for the FGO), 1A medians (9 flights), Experiments 2 (3 flights per condition, 4 conditions), 3 and 4 (3 flights each), the closed loop (1 flight per estimator without heading, 3 with) |
| **flights per estimator** | each estimator flew its own flights (closed loop, Experiment 5): **unpaired**, or paired by run index only | Experiment 5 comparatives (3 flights per estimator; EKF3 = far-spawn hold set), Experiment 1C |
| **bags** | recorded flights replayed offline by more than one estimator: **paired** | C1.a and H1.4 (6 bags each), the camera-dataset no-heading columns (6 bags) |
| **losses** | tag losses within the hold flights (one of each kind per flight) | Experiment 5 drift bands (EKF3 24 over 6 flights; UKF, FGO 12 over 3 flights each) |

Whether the units are paired (the same flights or bags for every estimator) or unpaired (each estimator flew its own)
is stated with n.

**Ordering verdicts.** Every place a table or caption claims, or declines to claim, an ordering carries a lettered footnote
with the metric and unit, n with its unit, the pre-registered rule with its source line, and the result against the rule
(`eval/figs_thesis.py`, `obasis()`). The verdict is one of four fixed phrases; the three "no ordering" cases are kept apart:

| verdict phrase | meaning | instances |
|---|---|---|
| **RULE MET** | a pre-registered rule was applied and met, so its ordering (or similarity) is claimed | H4.1 (3/3), H3.1–H3.4 (3/3); H4.3 (similarity) |
| **case (i), TEST RUN, RULE NOT MET** | a pre-registered decision rule whose outcomes include "no ordering" was applied and gave that outcome | H1.1 (the confirmatory test), H1.4 (the robust-weighting test) |
| **case (ii), FAILED AS WORDED** | a pre-registered prediction of an ordering or a similarity was scored literally ("as worded") and is false. A failed criterion does not by itself establish the opposite ordering; any ordering shown beside it is descriptive | H2.3, H2.4, H4.2, H5.2, H5.3, H5.4a, H5.4b |
| **case (iii), NO COMPARATIVE TEST REGISTERED** | no comparative test was pre-registered; the values are descriptive. Its variant **registered comparison without a decision rule** is C1.a ("REPORT, no decision rule", M:7892) | the 1A UKF standing (M:7187), the blank floor (ruled "Not accuracy comparisons", M:5551), the closed loop across estimators (M:9355), the Experiment 2 condition-D ordering (M:12803), the Experiment 4 return jump ("Reported regardless", M:10365), the safety tests across estimators, the build ablations, C1.a |

**Terms written in words, not added to the counted vocabulary:** RULE MET, TEST RUN / RULE NOT MET, NO COMPARATIVE TEST
REGISTERED, "registered comparison without a decision rule", and the units "bags" and "losses". "As worded" and
"descriptive" are the existing methodological labels (`methodology_definitions_draft.md`).

**Source lines** (line numbers at `337c931`, the commit this section was written on). Every rule line a footnote cites is read when the tables are built and checked to contain the quoted
phrase (the "rule text …" checks in `docs/thesis/figures_thesis/index.md`). The Experiment 5 comparatives are written only in
the design draft (`docs/tag_hold_design.md` §e, lines 180–187); METHODOLOGY has their verdicts (M:12236, M:13549) but no
pre-registration line of its own.

