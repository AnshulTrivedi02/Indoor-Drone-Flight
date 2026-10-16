# Glossary flags: undefined terms, conflicts and naming proposals

*Built 2026-10-16 on branch `fwd-camera` at `27c8f6e`. This file goes with `docs/thesis/glossary.md`, and every quote below was checked the same way as the quotes there.*

*This file is READ-ONLY with respect to the project. Nothing has been renamed or edited. The proposals in §c are for the thesis text only and have **not** been applied.*

## Headline conflicts (curated)

The codes most likely to mislead a reader of the thesis. Every meaning, with its source, is listed in §b.

1. **G-codes: at least nine series.**
   - The U10 replay-gate criteria **G1–G6** (`docs/u10_replay_gate_band.md:191-196`) clash with the mocap **watcher gaps G1–G11** (`docs/real_flights_plan.md:442-452`).
   - G1–G6 are also used for:
     - the heading ground-test gates (METHODOLOGY 5033-5050)
     - the backend ground-test gates (D9 P3 / D17 V3 / D19)
     - the per-flight gates of Experiments T, O and H
     - the H backend tag-input ground tests (`docs/h_backends_tag_input.md`)
     - the board go/no-go G1–G8 (`docs/board_firmware_plan.md`)
     - the readiness checklist G1a–G11
2. **B-codes: eight series.**
   - The closed-loop corridor criteria **B1–B5** (METHODOLOGY 4864ff; the closed-loop predictions) clash with the watcher **bench tests B0–B13** (`docs/real_flights_plan.md` §7.2) and the m2 full-bench **amendment letters B1–B5**.
   - Other B series:
     - the rung-1 flight-card bench checks B1–B10
     - the FGO C++ port equivalence rows B1–B6
     - the QuadPlane blockers B1–B3
     - the readiness rows
     - the Experiment T flight labels B1–B3
   - **B6b** means different things in the flight cards and in the SITL bench.
3. **A-codes: seven series.**
   - The watcher-bench **amendment letters A1–A10**
   - The rung-1 **converter acceptance checks A1–A10**
   - The thesis **appendix tables A1–A3**
   - The readiness rows A1–A10
   - The D12 work items A1–A5
   - The p1c calibration bands A1–A4
   - The Experiment T flight labels A1–A3
4. **F-codes.** All of these share F1–F8:
   - the offline tests **F1–F4** (F3b/F3c)
   - the watcher bench **findings F1–F8**
   - the original thesis **figures F1–F8**
   - the D12/D19 backlog-fix options (F1)–(F4)
   - the readiness items F1–F4
   - Experiment H "Criterion F1"

   Since `e202552`, figures F1/F3/F4/F8 have become tables T1/T2/T3/T5. However, `docs/thesis/world_images/index.md` and `worlds_combined.pdf` (commit `6d3254b`, made after the rename) still cite the old F1/F3/F4/F8 (see §a).
5. **T-codes.**
   - Thesis **tables T1–T8**
   - The final-results-pack tables T1 (claims) and T2 (corrections)
   - The M2-R bench criteria **T1–T4**
   - The fail-closed watcher tests **T1/T2**
   - **Experiment T**, its conditions **A–D** and trial names `T_A`…`T_D`

   Thesis T1 (scorecard) and pack T1 (claims) are different tables.
6. **D-codes.** The D-rulings **D1–D29** (`docs/decisions_queue.md`) clash with:
   - the rung-1 data-integrity checklist D1–D12 (`docs/rung1_flight_cards.md:306-317`)
   - the readiness calibration items D1–D7
   - the calendar gates D1–D3
   - the watcher-bench "Deviation D1"
7. **S-codes.**
   - The **stage-3 safety gates S1–S13**
   - The **Experiment H stages S0a…S3v2**
   - The rung-1 supervisor inputs S1–S7
   - The closed-loop safety criteria S1/S2
   - The robust-FGO secondary rules S1/S2
   - The M2 bench set-up items S1–S6
   - The F6 stop conditions S1–S5
8. **P-codes.**
   - The forward-camera Phase 1/2 **criteria P1–P4**
   - The **board bench checks P1–P10**
   - The D9 UKF flight preconditions P1–P3, which also appear as the trial suffixes `_p2`/`_p3`
   - The plan-step-2(a) rule P1
   - The F7 preconditions and the F8 parameter items
   - "P4" for Phase 4 results
9. **R-, U- and V-codes.**
   - **R1–R15** (rung-1 work items) are also:
     - the rgs criteria
     - the D17 Replay checks
     - the plan-to-freeze risks
     - the H ruling items
     - the watcher re-run set-up
     - "R1…Rn" result sorties
   - **R-a…R-e** are both copter-plan TODO items and M2r attempt-validity criteria.
   - **U1–U3** (closed-loop criteria), the real-flight unknowns **U1–U9** and the UKF-only costing items **U1–U15** (which include U4 and U10) overlap.
   - **V0–V7** is used for four series, and V3 is also a stage-3 sortie.
10. **Trial-name tokens.**
    - **`_a`/`_b`:** heading off/on in `cl_` and the shadows, but failure-injection variants in `H_safety_`.
    - **`_v2`/`_v3`:** different builds for the UKF and the FGO, and D17 validation steps in `ukf_shadow_hdg_v2`/`ukf_groundtest_hdg_v3`.
    - **`gt_`:** ground *test*, while **GT** means ground truth.
    - **`_p2`/`_p3`:** D9 preconditions, not phases.
    - **`_half`:** half *real-time factor*, not half speed of flight.
    - **`abort2`:** attempt 3.
11. **Status and estimator labels.**
    - **"shadow"** has three meanings: EKF3 flies; simulator truth flies; a non-active estimator logs.
    - **"live"/"hindsight"** are defined differently for F2/T/O and for L.
    - **"batch"** is both the whole-flight hindsight batch and the live `BatchFixedLagSmoother`.
    - **VOID** is both "run not a result" and "metric invalid".
    - **FROZEN** is both "simulation results" and "parameters".
    - **⚑** is a discrepancy flag in numbers.md but a change flag in `final_restatement_draft.md`.
    - **[U]** has three wordings.
12. **Source-level contradictions,** found as a side effect. These are flagged here and not fixed:
    - `gnss_denied_nomag.parm:1` still calls itself a "THROWAWAY test config - NOT part of the standing baseline", while CLAUDE.md says it is the comparison configuration.
    - The headers of `corridor_textured_half_fwdc.sdf` and `corridor_tson_fwdc.sdf` are copies and understate their differences.
    - METHODOLOGY 3826 and 3904 describe `iris_fwd_ts` differently.
    - `sim/README.md:9` says "five worlds".
    - The ArduPilot field comment for `XKF5.NI` ("Normalised flow variance") differs from CLAUDE.md's "innovation test ratio".


## (a) UNDEFINED terms

Terms used in the project with no written definition found anywhere in scope. No meaning is inferred.

| Term | Category | Where used (up to 3) |
|---|---|---|
| `A7b` | Hypothesis, prediction, criterion, check, item and question codes | `docs/handovers/2026-10-12_m2_full_bench.md:79`; `docs/handovers/2026-10-12_watcher_bench_rerun.md:422` |
| `along-track ratio` | Metrics and units | `docs/thesis/numbers.md:281` |
| `as worded` | Rulings, standing rules and status labels | `METHODOLOGY.md:5332`; `METHODOLOGY.md:11417`; `docs/handovers/2026-10-12_xuko_u10_h10.md:241` |
| `ATE` | Estimator, build, binary and branch labels | `CLAUDE.md:25`; `METHODOLOGY.md:9` |
| `attrib_2026-10-10` | Trial, dataset, batch and results naming | `~/thesis_data/batches/attrib_2026-10-10` |
| `B8e` | Hypothesis, prediction, criterion, check, item and question codes | `docs/real_flights_plan.md:656` |
| `binit0` | Estimator, build, binary and branch labels | `docs/handovers/2026-10-09_fgo_yawcap_gate.md:12` |
| `clfa / clfb<k> / clfr<k> / clukf` | Trial, dataset, batch and results naming | `~/thesis_data/batches/clfa.log`; `~/thesis_data/batches/clfb1.log`; `~/thesis_data/batches/clfr1.log` |
| `CLOSED` | Rulings, standing rules and status labels | `METHODOLOGY.md:5595`; `METHODOLOGY.md:9399`; `METHODOLOGY.md:6749` |
| `corridor_<floor>_verify` | Trial, dataset, batch and results naming | `docs/thesis/world_images/index.md:23` |
| `d15_blank / d27_regen` | Trial, dataset, batch and results naming | `~/thesis_data/batches/d15_blank`; `~/thesis_data/batches/d27_regen` |
| `d17_v1` | Trial, dataset, batch and results naming | `~/thesis_data/d17_v1/cl_bcpp_tex_r1`; `~/thesis_data/d17_v1`; `docs/h_backends_tag_input.md:135` |
| `d17_v2` | Trial, dataset, batch and results naming | `docs/handovers/2026-10-12_r1_scoring_items.md:107`; `docs/handovers/2026-10-12_r1_scoring_items.md:107` |
| `eeprom_backups / fw_builds` | Trial, dataset, batch and results naming | `~/thesis_data/fw_builds/KakuteH7_with_0156bfc3_20261012_014453_FAILED_nested_submodules` |
| `EKF` | Estimator, build, binary and branch labels | `CLAUDE.md:5` |
| `eval/diag/fgo_tilt_trace/spec.py` | Scripts (tools/ and eval/) | `eval/diag/fgo_tilt_trace/spec.py:1` |
| `eval/diag/fgo_tilt_trace/tilt.py` | Scripts (tools/ and eval/) | `eval/diag/fgo_tilt_trace/tilt.py:1` |
| `eval/diag/plainwall_trace/a1.py` | Scripts (tools/ and eval/) | `eval/diag/plainwall_trace/a1.py:1` |
| `eval/diag/port_merge_u4/ahrs_type_of_trials.py` | Scripts (tools/ and eval/) | `eval/diag/port_merge_u4/ahrs_type_of_trials.py:1` |
| `eval/diag/u10_final/gitdiff.sh` | Scripts (tools/ and eval/) | `eval/diag/u10_final/gitdiff.sh:1` |
| `eval/diag/ukf_jitter_fix/collect2.sh` | Scripts (tools/ and eval/) | `eval/diag/ukf_jitter_fix/collect2.sh:1` |
| `eval/diag/ukf_jitter_fix/collect.sh` | Scripts (tools/ and eval/) | `eval/diag/ukf_jitter_fix/collect.sh:1` |
| `eval/diag/ukf_jitter_fix/fi_wrap.py` | Scripts (tools/ and eval/) | `eval/diag/ukf_jitter_fix/fi_wrap.py:1` |
| `eval/diag/ukf_jitter_fix/s2_d27.sh` | Scripts (tools/ and eval/) | `eval/diag/ukf_jitter_fix/s2_d27.sh:1` |
| `eval/diag/ukf_jitter_fix/score_cfi.sh` | Scripts (tools/ and eval/) | `eval/diag/ukf_jitter_fix/score_cfi.sh:1` |
| `ExtNav` | Estimator, build, binary and branch labels | `METHODOLOGY.md:3094` |
| `F2mask` | Trial, dataset, batch and results naming | `docs/handovers/2026-10-09_final_rerun_dryrun.txt:229`; `METHODOLOGY.md:9622` |
| `F3bd` | Trial, dataset, batch and results naming | `METHODOLOGY.md:9622` |
| `F3d` | Hypothesis, prediction, criterion, check, item and question codes | `docs/handovers/2026-10-09_final_rerun_dryrun.txt:231` |
| `F15` | Hypothesis, prediction, criterion, check, item and question codes | `docs/handovers/2026-10-11_final_results_pack.md:30` |
| `fgo_cpp` | Estimator, build, binary and branch labels | `docs/real_flight_readiness.md:130` |
| `fgodev / fgodev2 / fgodev3` | Trial, dataset, batch and results naming | `~/thesis_data/batches/fgodev.log`; `~/thesis_data/batches/fgodev2.log`; `~/thesis_data/batches/fgodev3.log` |
| `fgt / gth / gth2 / gthb` | Trial, dataset, batch and results naming | `~/thesis_data/batches/fgt.log`; `~/thesis_data/batches/gth2.log`; `~/thesis_data/batches/gthb.log` |
| `FINDING —` | Rulings, standing rules and status labels | `METHODOLOGY.md:941`; `METHODOLOGY.md:1207`; `METHODOLOGY.md:4069` |
| `first result` | Rulings, standing rules and status labels | `METHODOLOGY.md:6376` |
| `FLU` | Estimator, build, binary and branch labels | `CLAUDE.md:373` |
| `FRD` | Estimator, build, binary and branch labels | `CLAUDE.md:373` |
| `fsha / fsha3 / fshb / fshbr` | Trial, dataset, batch and results naming | `~/thesis_data/batches/fsha.log`; `~/thesis_data/batches/fsha3.log`; `~/thesis_data/batches/fshbr.log` |
| `GT` | Hypothesis, prediction, criterion, check, item and question codes | `METHODOLOGY.md:3552` |
| `HAGL` | Estimator, build, binary and branch labels | `CLAUDE.md:324`; `METHODOLOGY.md:3562` |
| `imu_verify2 / nomag_test_long` | Trial, dataset, batch and results naming | `docs/thesis/world_images/index.md:38` |
| `L4` | Hypothesis, prediction, criterion, check, item and question codes | `METHODOLOGY.md:10505` |
| `legacy undefined trials` | Trial, dataset, batch and results naming | `~/thesis_data/trials/geom_fix_verify`; `~/thesis_data/trials/harness_test2`; `~/thesis_data/trials/verify_nomag` |
| `LSD` | Estimator, build, binary and branch labels | `CLAUDE.md:157` |
| `MISS` | Rulings, standing rules and status labels | `METHODOLOGY.md:5332` |
| `O1` | Hypothesis, prediction, criterion, check, item and question codes | `METHODOLOGY.md:10358` |
| `O2` | Hypothesis, prediction, criterion, check, item and question codes | `METHODOLOGY.md:10360` |
| `O3` | Hypothesis, prediction, criterion, check, item and question codes | `METHODOLOGY.md:10362` |
| `offline UKF` | Estimator, build, binary and branch labels | `METHODOLOGY.md:8860` |
| `p2_d15 / p3 / v2 / v3` | Trial, dataset, batch and results naming | `~/thesis_data/batches/p2_d15.log`; `~/thesis_data/batches/p3.log`; `~/thesis_data/batches/v2.log` |
| `P5b` | Hypothesis, prediction, criterion, check, item and question codes | `docs/thesis/final_restatement_draft.md:72`; `docs/thesis/rerun_old_vs_new.md:1013` |
| `PENDING` | Rulings, standing rules and status labels | `METHODOLOGY.md:3196`; `docs/thesis/numbers.md:631`; `METHODOLOGY.md:14173` |
| `post hoc` | Rulings, standing rules and status labels | `METHODOLOGY.md:5343`; `METHODOLOGY.md:10756`; `docs/u10_replay_gate_band.md:271` |
| `Python node` | Estimator, build, binary and branch labels | `METHODOLOGY.md:6376` |
| `QUEUED` | Rulings, standing rules and status labels | `METHODOLOGY.md:5988` |
| `recorded deviation` | Rulings, standing rules and status labels | `METHODOLOGY.md:11105` |
| `REPORT ONLY` | Rulings, standing rules and status labels | `METHODOLOGY.md:12601` |
| `room_check` | Trial, dataset, batch and results naming | `METHODOLOGY.md:10021` |
| `room_tags_map.json` | Worlds and models | `sim/worlds/room_tags_map.json:2` |
| `RPE` | Estimator, build, binary and branch labels | `CLAUDE.md:25` |
| `RTS` | Estimator, build, binary and branch labels | `docs/handovers/2026-10-09_final_rerun_repro.md:67` |
| `RULED` | Rulings, standing rules and status labels | `METHODOLOGY.md:1836` |
| `RULING` | Rulings, standing rules and status labels | `METHODOLOGY.md:1675` |
| `run_*.out` | Trial, dataset, batch and results naming | `~/thesis_data/wbench/run_hoverB2s.out`; `~/thesis_data/wbench/run_smoke.out`; `~/thesis_data/wbench/run_lua.out` |
| `s0b_check` | Trial, dataset, batch and results naming | `batches/expH/s0b_check.json` |
| `SITL` | Estimator, build, binary and branch labels | `CLAUDE.md:20` |
| `stock tree` | Estimator, build, binary and branch labels | `METHODOLOGY.md:8016` |
| `tag_check1 / tag_check1b` | Trial, dataset, batch and results naming | `~/thesis_data/trials/tag_check1`; `~/thesis_data/trials/tag_check1b` |
| `tag_check2img` | Trial, dataset, batch and results naming | `METHODOLOGY.md:10027` |
| `the node` | Estimator, build, binary and branch labels | `METHODOLOGY.md:6609` |
| `the port` | Estimator, build, binary and branch labels | `METHODOLOGY.md:7150`; `METHODOLOGY.md:5407` |
| `thesis FGO` | Estimator, build, binary and branch labels | `METHODOLOGY.md:10461` |
| `ukf_dtfix_check` | Trial, dataset, batch and results naming | `METHODOLOGY.md:4258` |
| `UNCLEAR` | Rulings, standing rules and status labels | `docs/thesis/final_restatement_draft.md:28` |
| `validation` | Trial, dataset, batch and results naming | `~/thesis_data/validation/test1_yaw`; `~/thesis_data/validation/test1_yaw_slow` |
| `VP` | Hypothesis, prediction, criterion, check, item and question codes | `CLAUDE.md:157` |
| `wbench sub-suffixes` | Trial, dataset, batch and results naming | `~/thesis_data/wbench/run2_hoverB_b6b.out`; `~/thesis_data/wbench/run4_hoverC_b10b.out`; `~/thesis_data/wbench/run4_m2c.out` |

### Not project codes (pattern matches dropped deliberately)

- `A2b` — "- **Supplementary criterion for FUTURE tests only, PRE-REGISTERED NOW:** S-A2b is the trigger time measured from" — `METHODOLOGY.md:13669` — occurs only inside S-A2b (H safety-test family), never standalone
- `A72` — "- **Pi 4 (Cortex-A72, 1.8 GHz): about 5–7× slower → roughly 75–135 ms per frame.**" — `METHODOLOGY.md:6099` — Cortex-A72 CPU core name
- `A76` — "- **Pi 5 (Cortex-A76, 2.4 GHz): about 2–3× slower → roughly 30–60 ms per frame.**" — `METHODOLOGY.md:6098` — Cortex-A76 CPU core name
- `C5` — "- Channel 5 then falls back to MAVProxy's RC input. Dataflash RCIN shows C5 going 1295 → 1800 and C3 going" — `docs/handovers/2026-10-12_xuko_u10_h10.md:236` — RC input channel 5 (and C3 = channel 3) in dataflash RCIN; not a project code
- `E1max` — "--d-max <D_max> [--g6-bands <E1max> <E1rms> <E3> <E5>] --name F --json eval/results/u10_gate/F.json" — `docs/u10_replay_gate_band.md:353` — command-line placeholder for the G6 E1 max band
- `E1rms` — "--d-max <D_max> [--g6-bands <E1max> <E1rms> <E3> <E5>] --name F --json eval/results/u10_gate/F.json" — `docs/u10_replay_gate_band.md:353` — command-line placeholder for the G6 E1 rms band
- `F4` — "- Dry runs (argument errors, an unknown board, an F4 board, an include-chain board, an H757 warning, the stock" — `docs/handovers/2026-10-12_copter_plan.md:54` — STM32F4 board class; not a code
- `F7` — "On an F7/F4 the board runs EKF3 in single precision while Replay runs it in double, so the two cannot be bit-exact. |" — `docs/minimal_real_flight_plan.md:44` — STM32F7/F4 board class; not a code
- `L7..L99` — "| Cruise window on the nine `dsn_*` bags | ~30.0 → ~332.8 s | s | CURRENT | M:L42-L43 |" — `docs/thesis/numbers.md:59` — noise: L7–L99 are line references (M:L42 = METHODOLOGY line 42, C:L99 = CLAUDE.md line 99); L8 is the Gazebo pixel format (METHODOLOGY 1369). Not codes
- `M7` — "- A 480 MHz Cortex-M7 in double is assumed to be 20–50× slower than the workstation core: 9× in clock, 2–5× in IPC" — `docs/board_firmware_plan.md:155` — noise: Arm Cortex-M7 MCU core, not a project code
- `T0` — "--window T0 T1`. It cross-correlates the high-passed flow with the RISI gyro averaged over each flow interval." — `docs/rung1_preregistration.md:411` — command-line window bounds; no definition
- `T0` — "~/venv-fgo/bin/python eval/sensor_timing_from_log.py <log.BIN> [--truth-tum mocap_FC.tum] [--window T0 T1] --json t.json" — `docs/handovers/2026-10-10_r1_converter.md:26` — also T1 here = window end

## (b) CONFLICTS

The same code or label carries more than one written meaning. Every meaning is listed with its source. A restatement of the same meaning is not counted; a meaning explicitly superseded is marked.


### `(a)` — 2 meanings

- **closed-loop set letters**: "- (a) EKF3 without heading, `corridor_textured_fwdc`, ×1 (reference)." — `METHODOLOGY.md:4841`
- **safety-test letters**: "| | `H_safety_fgo_a_v2` (node killed; standard watcher) | `H_safety_fgo_b_v2` (node killed; watcher watches the node) |" — `METHODOLOGY.md:12309`

### `(b)` — 2 meanings

- **closed-loop set letters**: "- (b) EKF3 + live camera heading, `corridor_textured_fwdc`, ×3." — `METHODOLOGY.md:4842`
- **safety-test letters**: "| | `H_safety_fgo_a_v2` (node killed; standard watcher) | `H_safety_fgo_b_v2` (node killed; watcher watches the node) |" — `METHODOLOGY.md:12309`

### `[TBD-S]` — 2 meanings

- **TBD labels (stage-3 draft)**: "- **[TBD-S]** supervisor or hardware input, fixed before the first result sortie; ... - **[TBD-V]** fixed once from VERIFICATION or rung-1 data, before the first result sortie; ... - **[RULING]** a choice for the user." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:20`
- **TBD labels (u10 band)**: "Labels: **[V]** verified (source, a build or a stored result); **[E]** an estimate; **[TBD-S]** supervisor or ... hardware input, fixed before day 3; **[TBD-V]** fixed ONCE on the verification logs (H, V) before any result log is" — `docs/u10_replay_gate_band.md:11`

### `[TBD-V]` — 2 meanings

- **TBD labels (stage-3 draft)**: "- **[TBD-S]** supervisor or hardware input, fixed before the first result sortie; ... - **[TBD-V]** fixed once from VERIFICATION or rung-1 data, before the first result sortie; ... - **[RULING]** a choice for the user." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:20`
- **TBD labels (u10 band)**: "Labels: **[V]** verified (source, a build or a stored result); **[E]** an estimate; **[TBD-S]** supervisor or ... hardware input, fixed before day 3; **[TBD-V]** fixed ONCE on the verification logs (H, V) before any result log is" — `docs/u10_replay_gate_band.md:11`

### `[U]` — 3 meanings

- **U label = needs a real Pi**: "Status: built and checked without a Pi, 2026-10-02. [V] = done and verified here; [E] = estimate; [U] = needs a real Pi." — `docs/real_flights_pi_readiness.md:3`
- **U label = unknown until the hardware or a ruling arrives**: "- **[V]** verified (source, a build, a log or a stored result); ... - **[E]** an estimate; ... - **[U]** unknown until the hardware or a ruling arrives." — `docs/realflight_plan_copter.md:19`
- **U label = unverified (needs the board or a bench)**: "- **[V]** verified: built, measured from the ELF or `.apj`, or read in source; ... - **[E]** an estimate, with its basis; ... - **[U]** unverified (needs the board or a bench)." — `docs/board_firmware_plan.md:8`

### `_a / _b` — 3 meanings

- **set-letter suffixes (a)/(b)::FGO shadow runs**: "- `fgo_shadow_half_a` (no heading); ... - `fgo_shadow_half_b` (heading; after D20)." — `METHODOLOGY.md:8071`
- **set-letter suffixes (a)/(b)::H safety tests**: "- **UKF (a):** UKF flying; failure = `AHRS_UKF_TFAIL` set in flight (output forced invalid); standard watcher." — `METHODOLOGY.md:11289` (+2 more source(s))
- **set-letter suffixes (a)/(b)::closed-loop sets**: "- (a) EKF3 without heading, `corridor_textured_fwdc`, ×1 (reference)." — `METHODOLOGY.md:4841`

### `_ref` — 2 meanings

- **batch state names::batch job lists *_ref.jobs**: "# FG1 reference for fgo_shadow_half_a3 (as fgo_shadow_half_a)" — `batches/fgo_shadow_a3_ref.jobs:1`
- **experiment trial names (T/O/H)::H_safety_ekf3_ref**: "- **`H_safety_ekf3_ref`** (EKF3 flying, main tree; tag bridge and flow bridge SIGKILLed in the hold; the watcher ... watches the tag bridge with `--dep-loss land`, as UKF (b)). A REFERENCE measurement:" — `METHODOLOGY.md:11877`

### `_v2` — 5 meanings

- **D17 validation steps**: "### D17 V2 (shadow run of the exact binary with heading, `ukf_shadow_hdg_v2`): PASS" — `METHODOLOGY.md:7664`
- **FGO build versions**: "- `cl_fgo_a_tex_half_v2`: `FGO=1`, `corridor_textured_half_fwdc`, Python node (corrected core)." — `METHODOLOGY.md:12253` (+1 more source(s))
- **UKF build versions**: "- **Caption:** Pass/fail of every closed-loop corridor set (replaces pack F15a), computed from the closed-loop score files, with the build ablations labelled: UKF v1 (pre-jitter fix) against v2 (final); FGO original, robust, v2 (noise fix ..." — `docs/thesis/figures_thesis/index.md:237` (+2 more source(s))
- **re-flight version suffixes _v<N>::H safety FGO**: "# sa sb H_safety_fgo_{a,b}_v2 (2 m-clearance hold W(-2.6,0); C++ FGO node 0.10 s time_ref)" — `tools/run_fgo_refly.sh:6`
- **re-flight version suffixes _v<N>::UKF re-flights**: "# UKF closed-loop RE-FLIGHTS with the jitter-corrected UKF port (ruling 2026-10-09), one per argument, under the flight lock." — `tools/run_ukf_refly.sh:2` (+1 more source(s))

### `_v2 / _v3` — 2 meanings

- **re-flight version suffixes _v<N>::D17 validation steps**: "### D17 V2 (shadow run of the exact binary with heading, `ukf_shadow_hdg_v2`): PASS" — `METHODOLOGY.md:7664` (+2 more source(s))
- **re-flight version suffixes _v<N>::FGO re-flights**: "# FGO closed-loop RE-FLIGHTS with the corrected FGO (ruling 2026-10-09). v3 = noise fix + gated yaw cap (node f642cd37); v2 = noise fix only (kept, ablation), one per argument, under the flight lock; stop at the" — `tools/run_fgo_refly.sh:2` (+2 more source(s))

### `_v3` — 5 meanings

- **D17 validation steps**: "### D17 V3 (ground test, UKF active with heading, `ukf_groundtest_hdg_v3`): PASS" — `METHODOLOGY.md:7691`
- **FGO build versions**: "- **S3 and the FGO re-flights now fly this node:** `H_s3v2_r*`, `cl_fgo_*_v3`, `H_safety_fgo_*_v3`. The `*_v2` and" — `METHODOLOGY.md:12522` (+1 more source(s))
- **UKF build versions**: "- **UKF safety re-tests** (installed port abb0357d; the short profiles unchanged; VERIFICATION):" — `METHODOLOGY.md:13633`
- **re-flight version suffixes _v<N>::FGO safety re-tests**: "### RESULT: FGO safety re-test (a), `H_safety_fgo_a_v3` (final FGO f642cd37; 2 m-clearance hold): ALL PASS" — `METHODOLOGY.md:12656`
- **re-flight version suffixes _v<N>::UKF safety re-tests**: "# sa3 sb3 H_safety_ukf_{a,b}_v3 (2d, 2026-10-11: as sa/sb, same port)" — `tools/run_ukf_refly.sh:8`

### `A1` — 7 meanings

- **D12 FGO backend work items**: "| A1 | `EKFType::FGO` (13), `AP_AHRS_FGO` backend, generated switch arms, `AHRS_EKF_TYPE 13` | 0.5 day |" — `docs/d12_fgo_backend_report.md:60`
- **Experiment T flight labels**: "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123`
- **p1c image-flow calibration acceptance bands**: "| A1 | HOVER | RMS(A) ≤ 1.10 × RMS(M) + 0.005 rad/s |" — `docs/p1c_img_calibration_spec.md:71`
- **real-flight readiness checklist rows**: "| A1 | Airframe, FC, Pi and sensors assembled and wired: FC↔Pi UART, cameras, LiDAR | not built | a, b | Plan question 3 is still open. No hardware is described anywhere in the repo. | 2–4 d (parts in hand). Procurement time is unknown. | ..." — `docs/real_flight_readiness.md:56` (+1 more source(s))
- **rung-1 converter acceptance checks**: "| A1 | `LOG_REPLAY` | = 1 |" — `docs/rung1_preregistration.md:347` (+1 more source(s))
- **thesis appendix tables**: "| A1 | appendix | `A1_closed_loop_builds.png` | Closed loop: every flown build against B1–B5 and the contact window | CURRENT | 8/8 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:25` (+1 more source(s))
- **watcher bench amendment letters (A-series)**: "- **A1 — EKF origin.** EKF3 on flow had no position estimate pre-arm ("Arm: Need Position Estimate"). The operator sends" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:118`

### `A2` — 7 meanings

- **D12 FGO backend work items**: "| A2 | **Input path.** The node sends its delayed state: time of validity on the SITL clock (via the `/imu/time_ref` map the node already has), position, velocity, attitude, gyro/accel bias and valid flag. `ODOMETRY` is taken by the camera ..." — `docs/d12_fgo_backend_report.md:61` (+1 more source(s))
- **Experiment T flight labels**: "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123`
- **p1c image-flow calibration acceptance bands**: "| A2 | CRUISE | RMS(A) ≤ 1.10 × RMS(M) + 0.005 rad/s, and \|bias(A)\| ≤ \|bias(M)\| + 0.01 rad/s |" — `docs/p1c_img_calibration_spec.md:72`
- **real-flight readiness checklist rows**: "| A2 | Baseline vehicle tune on the stock image: manual hover, `MOT_THST_HOVER` learned, harmonic notch, rate gains (Autotune in ALT_HOLD) | not built | a, b | The SITL values do not transfer: `h_extnav.parm` `MOT_THST_HOVER 0.310` (SITL ..." — `docs/real_flight_readiness.md:57`
- **rung-1 converter acceptance checks**: "| A2 | `DSF` dropped blocks, whole log | = 0 |" — `docs/rung1_preregistration.md:348`
- **thesis appendix tables**: "| A2 | appendix | `A2_H_and_safety_p1.png`, `A2_H_and_safety_p2.png` | H hold sets and the safety tests (all runs) | CURRENT | 11/11 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:26` (+1 more source(s))
- **watcher bench amendment letters (A-series)**: "- **A2/A4 — rangefinder: the Gazebo LiDAR, not SITL's analog sonar.** The SITL analog rangefinder read 0.0 m on the" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:120`

### `A3` — 7 meanings

- **D12 FGO backend work items**: "| A3 | **Output predictor in ArduPilot.** Buffer the DAL IMU deltas. On each FGO state, re-propagate from its time of validity to now (the UKF port's process model, mean only), then propagate forward each loop. This is EKF3's ..." — `docs/d12_fgo_backend_report.md:62`
- **Experiment T flight labels**: "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123`
- **p1c image-flow calibration acceptance bands**: "| A3 | CLIMB | \|bias(A)\| ≤ 0.05 rad/s, and \|bias(A)\| ≤ 0.25 × \|bias(M)\|. **Applies only if \|bias(M)\| ≥ 0.10 rad/s** on that axis. Otherwise A3 for that axis is reported as **"not tested: no climb bias present"**, which is not a ..." — `docs/p1c_img_calibration_spec.md:73`
- **real-flight readiness checklist rows**: "| A3 | Downward-camera capture on the Pi, publishing `/downward_camera/image` and `camera_info` with **sensor capture stamps** at 30 Hz | not built | a, b | `flow_tracker.py` subscribes to `/downward_camera/image`, which is today the ..." — `docs/real_flight_readiness.md:58`
- **rung-1 converter acceptance checks**: "| A3 | `RISI` samples dropped for flags; \|DVDT − DADT\| > 0.5 ms; DVDT within 0.5 ms of the frame spacing | 0; ≤ 0.1 % of samples; ≥ 99 % of samples |" — `docs/rung1_preregistration.md:349`
- **thesis appendix tables**: "| A3 | appendix | `A3_F1_cost_ablations_p1.png`, `A3_F1_cost_ablations_p2.png` | F1, the L compute cost and the build ablations | CURRENT | 8/8 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:27` (+1 more source(s))
- **watcher bench amendment letters (A-series)**: "- **A3 — climb rate 0.5 m/s** (`WPNAV_SPEED_UP`, `PILOT_SPEED_UP` 50) and `PLND_ENABLED 0` (gazebo-iris.parm's" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:125`

### `A4` — 5 meanings

- **D12 FGO backend work items**: "| A4 | **Validity.** Invalid when there has been no FGO state for > 250 ms, or its age exceeds budget, or the node flags invalid (its existing validity rule). Health and pre-arm follow from it. | 0.5 day |" — `docs/d12_fgo_backend_report.md:63`
- **p1c image-flow calibration acceptance bands**: "| A4 | all | n(A) = n(M) (option a drops no frames by construction; checked) |" — `docs/p1c_img_calibration_spec.md:74`
- **real-flight readiness checklist rows**: "| A4 | `flow_tracker.py` (Shi-Tomasi + LK + RANSAC) on the Pi CPU: rate, latency, `use_sim_time` off | needs adapting for real sensors | a, b | `FOCAL_LENGTH_PX = 554.0` is hard-coded (`flow_tracker.py:16`). Validity uses the feature count ..." — `docs/real_flight_readiness.md:59`
- **rung-1 converter acceptance checks**: "| A4 | IMU frame rate (mean frame period) against `SCHED_LOOP_RATE` | within ± 2 % |" — `docs/rung1_preregistration.md:350`
- **watcher bench amendment letters (A-series)**: "- **A2/A4 — rangefinder: the Gazebo LiDAR, not SITL's analog sonar.** The SITL analog rangefinder read 0.0 m on the" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:120`

### `A5` — 4 meanings

- **D12 FGO backend work items**: "| A5 | **Validation, mirroring the UKF.** Pre-registered checks: input equivalence (sent state = received state; time mapping); the predictor check on a shadow run; latency through take-off within budget; a ground test (G1–G5); then set ..." — `docs/d12_fgo_backend_report.md:64`
- **real-flight readiness checklist rows**: "| A5 | `flow_bridge.py` → `OPTICAL_FLOW` to EKF3 over the real link | needs adapting for real sensors | a, b | UDP port 14553 via MAVProxy (`flow_bridge.py:80`). The sign is now `flow_rate_x = +flow_x_rad` (`:27-31`, 2026-09-29 finding); ..." — `docs/real_flight_readiness.md:60`
- **rung-1 converter acceptance checks**: "| A5 | the converter's raw IMU through the INS 2-pole filters (`INS_GYRO_FILTER`/`INS_ACCEL_FILTER`) against the FC's logged `IMU` record (same instance), sample by sample over the DISARMED spans only (log start → first arming; last ..." — `docs/rung1_preregistration.md:351`
- **watcher bench amendment letters (A-series)**: "- **A5 — flow: the thesis camera-flow path, world `iris_textured`.** SITL's own flow sensor (`FLOW_TYPE 10`) drifted" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:127`

### `A6` — 3 meanings

- **real-flight readiness checklist rows**: "| A6 | Forward camera: capture plus the C++ heading program on the Pi | exists but untested on hardware | b (heading arms); a only if the forward camera is flown | ARM64 build checked under qemu only: 205/205 integer outputs identical, ..." — `docs/real_flight_readiness.md:61`
- **rung-1 converter acceptance checks**: "| A6 | rest, [arming − 3 s, arming − 0.5 s], if still (gyro std < 0.05 rad/s) | \|specific force\| = 9.80665 ± 0.15 m/s²; \|gyro mean\| < 0.05 rad/s (else NOT TESTED, not a failure) |" — `docs/rung1_preregistration.md:352`
- **watcher bench amendment letters (A-series)**: "- **A6 — B5b-noflag set-up.** With `tracked = −1` from the start, the vehicle at rest gives bit-identical Gazebo poses," — `docs/handovers/2026-10-11_watcher_sitl_bench.md:138`

### `A7` — 3 meanings

- **real-flight readiness checklist rows**: "| A7 | Wall-tag detector (`tag_bridge.py`, pupil_apriltags) on real images; `ODOMETRY` to EKF3 ExtNav; the same fixes to the UKF/FGO | needs adapting for real sensors | a, b if P-HOLD is the profile | Uses UDP 14557, i.e. SITL SERIAL1 ..." — `docs/real_flight_readiness.md:62`
- **rung-1 converter acceptance checks**: "| A7 | flow = EKF3's flow input: `OF` vs `ROFH` (counts; flowX/Y, bodyX/Y float32-identical; Qual) | exact |" — `docs/rung1_preregistration.md:353`
- **watcher bench amendment letters (A-series)**: "- **A7 — harness only.** (a) Before each hover the landed, DISARMED vehicle is put back at the spawn point with Gazebo" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:141`

### `A8` — 3 meanings

- **real-flight readiness checklist rows**: "| A8 | Rangefinder on the vehicle: a native FC driver (`RNGFND1_TYPE` per model), or read on the Pi and injected as `DISTANCE_SENSOR` (the SITL pattern) | not built | a, b | `lidar_rangefinder.parm` is `TYPE 10` (MAVLink), `MIN 0.05`, `MAX ..." — `docs/real_flight_readiness.md:63`
- **rung-1 converter acceptance checks**: "| A8 | geometry: `FLOW_POS_*` vs `ROFH.posOffset`; `RNGFNDn_POS_*` vs `RRNI.pos_offset` | to 1e-6 |" — `docs/rung1_preregistration.md:354`
- **watcher bench amendment letters (A-series)**: "- **A8 — B4a and B4c ARE run in SITL (pre-registered here, committed before the run).** §1.3 listed them as" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:146` (+1 more source(s))

### `A9` — 3 meanings

- **real-flight readiness checklist rows**: "| A9 | Range to the Pi for the UKF/FGO: FC `DISTANCE_SENSOR` telemetry → `/downward_lidar/range` republisher (if the LiDAR is on the FC) | not built | b live; a can instead use dataflash `RFND` offline | Today `lidar_bridge.py` goes the ..." — `docs/real_flight_readiness.md:64`
- **rung-1 converter acceptance checks**: "| A9 | range vs the FC's `RFND` (same instance, Good), the RFND sample within 60 ms of each converter range emission | ≥ 50 pairs; median \|diff\| ≤ 0.02 m; p95 ≤ 0.05 m |" — `docs/rung1_preregistration.md:355`
- **watcher bench amendment letters (A-series)**: "- **A9 (2026-10-12, ~11:45, after `wbench2_hoverB_20261012_112751` was stopped; before any further run). Harness" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:83` (+1 more source(s))

### `A10` — 3 meanings

- **real-flight readiness checklist rows**: "| A10 | IMU stream: `HIGHRES_IMU` 333 Hz from a real FC serial port → `imu_bridge.py` → `/imu/data_raw` + `/imu/time_ref` | needs adapting for real sensors | a (offline replay inputs), b | 333 Hz is the 0.8 × `SCHED_LOOP_RATE` cap, ..." — `docs/real_flight_readiness.md:65`
- **rung-1 converter acceptance checks**: "| A10 | flow sign and response: `eval/sensor_timing_from_log.py --window <a sync wiggle>` | gain > 0 on both axes and peak correlation ≥ 0.5 on both; without it: NOT accepted |" — `docs/rung1_preregistration.md:356` (+1 more source(s))
- **watcher bench amendment letters (A-series)**: "- **A10 (2026-10-12, ~11:58, after the hoverB re-run `wbench2_hoverB_20261012_114206` and hoverC; before the run it" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:106`

### `B1` — 8 meanings

- **Experiment T flight labels**: "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123`
- **FGO C++ port equivalence rows**: "| B1 | `fgo_replay.py fwdc_tex_r1 0.25 2 heading` | every keyframe |" — `docs/fgo_cpp_port.md:186` (+1 more source(s))
- **QuadPlane blockers**: "| B1 | **No position-free landing in QuadPlane** | QLAND runs the QLOITER position controller (`ArduPlane/mode_qland.cpp:26-31`). No Q mode checks position validity. `AP_InertialNav` freezes the last horizontal velocity when the estimator ..." — `docs/quadplane_costing.md:31`
- **closed-loop corridor criteria B1–B5**: "- **B1.** Completes the full mission (arm, climb, 300 s cruise, land) with no wall contact:" — `METHODOLOGY.md:4864` (+1 more source(s))
- **m2 full-bench amendment letters (B-series)**: "- **B1 (2026-10-12 ~17:16, after `wbench4_ground_20261012_170507` ABORTED; before any further run). No criterion" — `docs/handovers/2026-10-12_m2_full_bench.md:172`
- **real-flight readiness checklist rows**: "| B1 | FC↔Pi physical link and port layout replacing the SITL UDP ports. **SITL layout today:** 14550 `fly_trial`; 14551 attitude; 14552 LiDAR; 14553 flow; 14554 EKF pose (all MAVProxy `--out`); 14556 IMU (SERIAL2); 14557 heading/tag ..." — `docs/real_flight_readiness.md:71`
- **rung-1 flight-card bench checks**: "| B1 | **Parameter readback** | download all parameters from the FC; diff against `rung1_template.parm` + the variant + `rung1_failsafe_fc.parm` (2026-10-12); **AHRS_EKF_TYPE = 3**, LOG_REPLAY = 1, LOG_DISARMED = 1, ARMING_SKIPCHK = 0, ..." — `docs/rung1_flight_cards.md:184`
- **watcher bench tests (§7.2 B0–B13 and SITL variants)**: "**B1. No watcher → arming refused.**" — `docs/real_flights_plan.md:486`

### `B2` — 8 meanings

- **Experiment T flight labels**: "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123`
- **FGO C++ port equivalence rows**: "| B2 | `room_fgo_replay.py T_A_r1`, live track | every keyframe that is anchored in both runs |" — `docs/fgo_cpp_port.md:187`
- **QuadPlane blockers**: "| B2 | **The thesis backends have no origin, so Plane has no Location** | `AP_AHRS_UKF::get_origin` returns false and `location_valid=false` (fork `AP_AHRS_UKF.h:30`, `AP_AHRS_UKF.cpp:42`). Plane builds `current_loc`, home, the guided ..." — `docs/quadplane_costing.md:32`
- **closed-loop corridor criteria B1–B5**: "- **B2.** Maximum physical cross-track |x_GT| during cruise **≤ 6.5 m**." — `METHODOLOGY.md:4866` (+3 more source(s))
- **m2 full-bench amendment letters (B-series)**: "- **B2 (2026-10-12 ~17:50, after `wbench4_hoverB_20261012_173841` ABORTED; before any further run). Harness fix (S3" — `docs/handovers/2026-10-12_m2_full_bench.md:184`
- **real-flight readiness checklist rows**: "| B2 | FC↔Pi clock map: D25 robust low-percentile envelope on `/imu/time_ref`; boot-identity pre-arm check; in-flight clock-integrity latch | exists and tested in SITL | a (offline alignment), b (live) | D25; ..." — `docs/real_flight_readiness.md:72`
- **rung-1 flight-card bench checks**: "| B2 | **Sensors healthy** | ground station status: flow sensor, rangefinder, compass (healthy even in nomag: arming gate), IMU, logging | ~1 min: a status screen | all healthy; no pre-arm message other than the expected "props off" items |" — `docs/rung1_flight_cards.md:185`
- **watcher bench tests (§7.2 B0–B13 and SITL variants)**: "**B2. Watcher killed while armed → LAND/disarm.**" — `docs/real_flights_plan.md:498`

### `B3` — 8 meanings

- **Experiment T flight labels**: "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123`
- **FGO C++ port equivalence rows**: "| B3 | `room_fgo_replay.py T_D_r1`, live track | as B2 |" — `docs/fgo_cpp_port.md:188`
- **QuadPlane blockers**: "| B3 | **Plane GUIDED cannot fly the experiment profile** | `SET_POSITION_TARGET_LOCAL_NED` changes **altitude only** (`ArduPlane/GCS_MAVLink_Plane.cpp:1081-1101`). There are no velocity targets. Horizontal targets need a Location ..." — `docs/quadplane_costing.md:33`
- **closed-loop corridor criteria B1–B5**: "- **B3.** EKF3 yaw error (`XKF1` vs SIM) during cruise: **95th percentile ≤ 2°, maximum ≤ 4.5°**." — `METHODOLOGY.md:4870` (+3 more source(s))
- **m2 full-bench amendment letters (B-series)**: "- **B3 (2026-10-12 ~18:08, after `wbench4_hoverC_20261012_175909`; before any further run). Harness fault; A10 repeat.**" — `docs/handovers/2026-10-12_m2_full_bench.md:195`
- **real-flight readiness checklist rows**: "| B3 | Measured link latency distribution (one-way, jitter) for every Pi→FC stream | not built | b (feeds H2); a (report) | Plan §9.2 starts at 5–15 ± 3 ms [E], "to be replaced by the bench-measured distribution". | 0.5 d | B1 |" — `docs/real_flight_readiness.md:73`
- **rung-1 flight-card bench checks**: "| B3 | **Rangefinder** | on the ground: reading ≈ `RNGFND1_GNDCLR`; then lift the vehicle by hand to ~1 m and back | ~30 s: one lift spans the range used | ground reading within ±2 cm of GNDCLR (or "out of range low" if RNGFND1_MIN > ..." — `docs/rung1_flight_cards.md:186`
- **watcher bench tests (§7.2 B0–B13 and SITL variants)**: "**B3. Heartbeat loss with the watcher process alive.**" — `docs/real_flights_plan.md:509`

### `B4` — 6 meanings

- **FGO C++ port equivalence rows**: "| B4 | `T_A_r1` whole-flight batch (hindsight) | every batch key (X(k) of `key_t`): |Δp| ≤ 1 mm, |Δyaw| ≤ 0.01°, same key set |" — `docs/fgo_cpp_port.md:189`
- **closed-loop corridor criteria B1–B5**: "- **B4.** No fast runaway: 1 s-smoothed |GT lateral speed| during cruise **≤ 0.25 m/s**." — `METHODOLOGY.md:4874` (+2 more source(s))
- **m2 full-bench amendment letters (B-series)**: "- **B4 (2026-10-12 ~18:25, after `wbench4_m2_20261012_181437`; before any further run). Two harness faults; the one" — `docs/handovers/2026-10-12_m2_full_bench.md:205`
- **real-flight readiness checklist rows**: "| B4 | Pi time base: `use_sim_time:=false` and wall-clock ROS time on every node; no `/clock` | needs adapting for real sensors | a, b | Every launch line uses `use_sim_time:=true` (CLAUDE.md "Launch Sequence"; `run_trial.sh`). | 0.5 d | ..." — `docs/real_flight_readiness.md:74`
- **rung-1 flight-card bench checks**: "| B4 | **Flow sign (ArduPilot's standard flow check)** | over the textured floor, at ~0.5–1 m, roll the vehicle by hand left/right, then pitch forward/back, ~3 cycles each | ~1 min: three cycles per axis show the sign unambiguously | in ..." — `docs/rung1_flight_cards.md:187`
- **watcher bench tests (§7.2 B0–B13 and SITL variants)**: "**B4. Geofence breach, hand-carried → the configured action.**" — `docs/real_flights_plan.md:518`

### `B5` — 5 meanings

- **FGO C++ port equivalence rows**: "| B5 | `T_D_r1` whole-flight batch | as B4 |" — `docs/fgo_cpp_port.md:190`
- **closed-loop corridor criteria B1–B5**: "- **B5.** No oscillation: cruise gyro rms roll ≤ 0.05, pitch ≤ 0.0108, yaw ≤ 0.02 rad/s (the" — `METHODOLOGY.md:4877` (+3 more source(s))
- **m2 full-bench amendment letters (B-series)**: "- **B5 (2026-10-12 ~18:28, after `wbench4_m2_20261012_182305`, the B4 repeat; before any further run). V3 failed; one" — `docs/handovers/2026-10-12_m2_full_bench.md:217`
- **rung-1 flight-card bench checks**: "| B5 | **Arming checks run** | attempt to arm with props off (motor safety per lab rules) | ~30 s | arming either succeeds with every check run, or fails only on the props-off/safety item; never a skipped check |" — `docs/rung1_flight_cards.md:188`
- **watcher bench tests (§7.2 B0–B13 and SITL variants)**: "**B5. Mocap dropout / stale pose (G2).** *(RE-WORDED 2026-10-12 under ruling 4 of "RULINGS (user, 2026-10-12)"," — `docs/real_flights_plan.md:533` (+1 more source(s))

### `B6` — 3 meanings

- **FGO C++ port equivalence rows**: "| B6 (only if time allows) | `room_fgo_replay.py O_r1 --gnss`, live (+ batch as a separate row) | as B2 / B4 |" — `docs/fgo_cpp_port.md:191`
- **rung-1 flight-card bench checks**: "| B6 | **Fence and EKF origin** (origin procedure re-written 2026-10-12, ruling 1) | ground station fence status; then the §1a origin procedure, steps 1–5 (every EKF3 core initialised FIRST, then the origin, then verified) | ~30 s | ..." — `docs/rung1_flight_cards.md:189`
- **watcher bench tests (§7.2 B0–B13 and SITL variants)**: "**B6. Wrong body / rigid-body ID (G3).**" — `docs/real_flights_plan.md:571`

### `B6b` — 2 meanings

- **rung-1 flight-card bench checks**: "| B6b | **F7 yaw check** (ruling 2) | §1a steps 5–6 on the bench: record the tie; then turn the vehicle by hand to +90°, HOLD IT STILL ≥ 5 s, and turn it back (the FC sees the turn, so the check must keep passing) | ~1 min | \|FC yaw − ..." — `docs/rung1_flight_cards.md:190`
- **watcher bench tests (§7.2 B0–B13 and SITL variants)**: "| **B6b** (motion identity, D1) | Hover under the primary watcher. Observer watcher (system ID 212, `--identity require`). Manoeuvre: a commanded roll of 12° held 0.8 s, then a 90° yaw. Run 1: the observer gets the right body. Run 2: the ..." — `docs/handovers/2026-10-11_watcher_sitl_bench.md:86`

### `B7` — 2 meanings

- **rung-1 flight-card bench checks**: "| B7 | **Failsafes** | RC transmitter off for 2 s (props off, disarmed): RC failsafe message; battery failsafe values read back | ~1 min | messages as expected; values as filed |" — `docs/rung1_flight_cards.md:191`
- **watcher bench tests (§7.2 B0–B13 and SITL variants)**: "**B7. Clock and latency.**" — `docs/real_flights_plan.md:580`

### `B8` — 2 meanings

- **rung-1 flight-card bench checks**: "| B8 | **Log completeness** | download the bench log; run §7 items D2–D5 on it | ~5 min of checking; the log is the B1–B7 period | LOG_REPLAY records present; `DSF.Dp` = 0 |" — `docs/rung1_flight_cards.md:192`
- **watcher bench tests (§7.2 B0–B13 and SITL variants)**: "**B8. Estimator invalid → FS_EKF_ACTION path (the open item in §7).** Per flying estimator, armed (props off," — `docs/real_flights_plan.md:592`

### `B9` — 2 meanings

- **rung-1 flight-card bench checks**: "| B9 | **Sync wiggle in the first acceptance log** (2026-10-12) | before B8's download, with the vehicle disarmed on the bench: a sync wiggle (~5 s, sharp rotations about all three axes, \|ω\| > 2 rad/s); then run `eval/bin2fgo_accept.py` ..." — `docs/rung1_flight_cards.md:193`
- **watcher bench tests (§7.2 B0–B13 and SITL variants)**: "**B9. Dependency loss (`--dep-loss land|stop`; G7, G8).** Armed. For each watched dependency in turn (flow tracker," — `docs/real_flights_plan.md:630`

### `B10` — 2 meanings

- **rung-1 flight-card bench checks**: "| B10 | **M2 EKF velocity check** (2026-10-12) | §1a step 7 on the bench, vehicle still: read `LOCAL_POSITION_NED` vx, vy, vz on the GCS for 5 s; then carry the vehicle by hand ~1 m and set it down; read again for 5 s | ~1 min | \|v\| < ..." — `docs/rung1_flight_cards.md:194`
- **watcher bench tests (§7.2 B0–B13 and SITL variants)**: "**B10. RC override takes precedence.** Armed, GUIDED:" — `docs/real_flights_plan.md:644` (+1 more source(s))

### `C1` — 6 meanings

- **C++ heading-port equivalence bands**: "- **C1, VP existence and validity identical on every frame.** A mismatch is allowed **only** if it" — `METHODOLOGY.md:5907` (+1 more source(s))
- **D25 FGO shadow criteria**: "- **C1:** from the first received state (`XFGI`) to disarm, `XFGO.OV` = 1 at **every** sample. Equivalently, the" — `METHODOLOGY.md:9165`
- **Experiment T flight labels**: "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123`
- **initial-sigma audit verification items**: "- C1: with the yaw fix alone, the output is byte-identical to the trace's F_YAW0 = 1° demonstration (0.150 m, yaw max" — `METHODOLOGY.md:13325`
- **real-flight readiness checklist rows**: "| C1 | Core real-FC parameter file: EKF3 sources from `gnss_denied.parm` and `gnss_denied_nomag.parm` (`EK3_SRC1_POSXY 0`, `POSZ 2`, `VELZ 0`, `YAW 0`, `GPS1_TYPE 0`, compass present but unused); `FS_EKF_ACTION` LAND; battery failsafe; RC ..." — `docs/real_flight_readiness.md:84`
- **stage-3 UKF closed-loop criteria (draft)**: "- **C1 completion:** the profile completes under UKF control with all of:" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:159` (+1 more source(s))

### `C2` — 6 meanings

- **C++ heading-port equivalence bands**: "- **C2, |Δψ| ≤ 1e-6 deg on every frame where both have a VP.** Basis:" — `METHODOLOGY.md:5911`
- **D25 FGO shadow criteria**: "- **C2:** **0** negative-age samples (10⁶ < `Age` < `UINT32_MAX`) in the whole log." — `METHODOLOGY.md:9167`
- **Experiment T flight labels**: "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123`
- **initial-sigma audit verification items**: "**C2: C++ core. PARKED (coordinator, 2026-10-10: thesis results first).**" — `docs/handovers/2026-10-10_initial_sigma_audit.md:151`
- **real-flight readiness checklist rows**: "| C2 | Rangefinder parameters: `RNGFND1_TYPE`, `ORIENT 25`, `MIN`, `MAX`, `POS_X/Y/Z`, `GNDCLR` | needs adapting for real sensors | a, b | `lidar_rangefinder.parm` (`TYPE 10`, `0.05`/`40`, `POS_Z 0.12`, all sim values). | 0.5 d | A8 |" — `docs/real_flight_readiness.md:85`
- **stage-3 UKF closed-loop criteria (draft)**: "- **C2 physical excursion:** the maximum horizontal distance of the mocap position from the commanded path (the" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:164`

### `C3` — 6 meanings

- **C++ heading-port equivalence bands**: "- **C3, |Δsupport| ≤ 1e-6 px** on every frame where both have a VP (same basis)." — `METHODOLOGY.md:5917`
- **D25 FGO shadow criteria**: "- **C3:** the first state arrives ≥ 10 s (sim) after the node's first `/imu/time_ref` (from the clock-map" — `METHODOLOGY.md:9168`
- **Experiment T flight labels**: "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123`
- **initial-sigma audit verification items**: "**C3: `final_rerun_checks.py corrections` has the fifth check.**" — `docs/handovers/2026-10-10_initial_sigma_audit.md:158`
- **real-flight readiness checklist rows**: "| C3 | Flow parameters: `FLOW_TYPE 5`, `FLOW_POS_X/Y/Z`, `FLOW_ORIENT_YAW`, `EK3_FLOW_DELAY` | needs adapting for real sensors | a, b | **`FLOW_POS_Z` conflicts in SITL: 0.13 in `flow_ekf.parm`, overridden to 0.25 in ..." — `docs/real_flight_readiness.md:86`
- **stage-3 UKF closed-loop criteria (draft)**: "- **C3 validity:** the UKF's `horiz_pos_rel` (`XUKF`/`XUKO` `SS` bit 3) set and `Healthy` on 100 % of W; no" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:166`

### `C4` — 3 meanings

- **C++ heading-port equivalence bands**: "- **C4, quality identical** on every frame (it is a floor of support / S_MIN × 50, so C3 implies it" — `METHODOLOGY.md:5918`
- **real-flight readiness checklist rows**: "| C4 | ExtNav parameters for the tag and heading paths: `VISO_TYPE 1`, `EK3_SRC1_POSXY/YAW 6`, `VISO_POS_M_NSE`, `VISO_YAW_M_NSE`, `VISO_DELAY_MS`, `ARMING_SKIPCHK 262144` | needs adapting for real sensors | a, b if P-HOLD (or forward ..." — `docs/real_flight_readiness.md:87`
- **stage-3 UKF closed-loop criteria (draft)**: "- **C4 smoothness** (as the SITL B4/B5):" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:168`

### `D1` — 5 meanings

- **D-rulings**: "- **D1 (B4 scorer), extra evidence.** Under the ORIGINAL sample-count scorer, `cl_b_tex_r2` and" — `METHODOLOGY.md:6344` (+2 more source(s))
- **real-flight readiness items**: "| D1 | Downward-camera intrinsics and distortion: focal length for the px/s → rad/s conversion | exists but untested on hardware | a, b | `tools/real_camera/calibrate.py`. Self-test `selftest_calibration.py` passed (fx within 0.15%, k1 ..." — `docs/real_flight_readiness.md:97`
- **rung-1 calendar gates**: "| **Mon 12** | **Supervisor inputs S1–S7**; firmware decision S6; mocap booking | **D1: inputs received.** If there is no answer by Tue 13, rung 1 is at risk. |" — `docs/minimal_real_flight_plan.md:393`
- **rung-1 data-integrity checklist**: "| D1 | `.BIN` downloaded, file size plausible, copied to two places; named `<sortie>_<date>.BIN` | yes |" — `docs/rung1_flight_cards.md:306`
- **watcher bench deviations**: "- **Deviation D1 (identity):** the G3 identity proof is a HAND motion before arming. SITL has no hand, and arming" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:48`

### `D2` — 4 meanings

- **D-rulings**: "- **D2:** switch to the **C++ heading node for all subsequent closed-loop flights**." — `METHODOLOGY.md:6371` (+2 more source(s))
- **real-flight readiness items**: "| D2 | Forward-camera intrinsics, undistortion and resampling onto the frozen simulated camera (640×480, fx 554.38) | exists but untested on hardware | b (heading arms); a if flown | `tools/real_camera/run_heading_video.py`. A PNG round ..." — `docs/real_flight_readiness.md:98`
- **rung-1 calendar gates**: "| Thu 15 – Fri 16 | R5 firmware build and flash; R6 bench readback; R12 bench (flow orientation, rangefinder, log completeness); R1/R2 SITL acceptance tests (light single replays) | **D2 (Fri 16): a flying vehicle with working flow and ..." — `docs/minimal_real_flight_plan.md:395`
- **rung-1 data-integrity checklist**: "| D2 | **LOG_REPLAY records present**: `RFRH`, `RFRF`, `RISH`, `RISI`, `ROFH`, `RRNH`, `RRNI` counts > 0; `RFRH` at ≈ 400 Hz | all present |" — `docs/rung1_flight_cards.md:307`

### `D3` — 4 meanings

- **D-rulings** *(superseded)*: "- **D3 is withdrawn.** My earlier reading, "round-off amplified by the runaway plus E5-permitted" — `METHODOLOGY.md:6325` (+1 more source(s))
- **real-flight readiness items**: "| D3 | Camera–IMU (and LiDAR–IMU) extrinsics: lever arms; downward-camera rotation about z (sets the flow axes); forward-camera yaw offset (a heading bias) | not built | a, b | There is no tool. The simulated mounts are ideal (CLAUDE.md ..." — `docs/real_flight_readiness.md:99`
- **rung-1 calendar gates**: "| Mon 19 | R7 recorder test; **R13 hand-carried check + same-day pipeline** | **D3: Replay check passes on the hand-carried log (or its failure is characterised), the converter runs on real data, the scorer gives numbers.** The flow-aiding ..." — `docs/minimal_real_flight_plan.md:396`
- **rung-1 data-integrity checklist**: "| D3 | `RFRH` continuity: no gap > 50 ms between take-off and landing | none |" — `docs/rung1_flight_cards.md:308`

### `D4` — 3 meanings

- **D-rulings**: "- **D4:** information only (the port's binaries rebuilt); no ruling needed." — `docs/decisions_queue.md:262`
- **real-flight readiness items**: "| D4 | Camera–FC time offsets: `EK3_FLOW_DELAY`, `VISO_DELAY_MS` (D2/D20 receipt rule), the flow capture stamp | needs adapting for real sensors | a, b | The D2/D20 procedure exists and was used in SITL (D20; `tags_extnav.parm`). On ..." — `docs/real_flight_readiness.md:100`
- **rung-1 data-integrity checklist**: "| D4 | **`DSF.Dp` = 0** (no dropped writes) for the whole flight | 0 |" — `docs/rung1_flight_cards.md:309`

### `D5` — 3 meanings

- **D-rulings**: "the user's, and is queued (D5).** Adding a buffer changes the port only, never the offline UKF." — `METHODOLOGY.md:6223` (+1 more source(s))
- **real-flight readiness items**: "| D5 | Flow sign and axis re-verification on the real mount: the lateral-sign finding of 2026-09-29 | needs adapting for real sensors | a, b | `flow_bridge.py:27-31`. Only the SITL mount is verified, and CLAUDE.md warns against ..." — `docs/real_flight_readiness.md:101`
- **rung-1 data-integrity checklist**: "| D5 | `PARM` dump in the log: AHRS_EKF_TYPE = 3, LOG_REPLAY = 1, the EK3_SRC1_* and sensor values as filed | as filed |" — `docs/rung1_flight_cards.md:310`

### `D6` — 3 meanings

- **D-rulings**: "- **Queued (D6):** whether to fly a replacement `dsn_tex_r11`, with the rule applied to it as well," — `METHODOLOGY.md:6244` (+1 more source(s))
- **real-flight readiness items**: "| D6 | Vanishing-point heading method re-validated on real images under a **new pre-registration** (plan question 6) | not built | b (heading arms); a if the forward camera is flown | The frozen parameters (0.5° tolerance, `S_MIN` 200 px, ..." — `docs/real_flight_readiness.md:102`
- **rung-1 data-integrity checklist**: "| D6 | `ARM`/`EV` records: one arm and one disarm; both sync wiggles visible in `RISI` gyro (rates > 2 rad/s) **while disarmed** | yes |" — `docs/rung1_flight_cards.md:311`

### `D7` — 3 meanings

- **D-rulings**: "- **D7:** the FGO track starts with the **ROS-node route and its validation**:" — `METHODOLOGY.md:6383` (+1 more source(s))
- **real-flight readiness items**: "| D7 | Wall-tag method re-validated: S0 (validity rule and σ_pos) repeated on real images against mocap | not built | a, b if P-HOLD | `tag_hold_design.md` "Transfer"; the D18 shared tag-validity rule (METHODOLOGY "RULING 2026-10-08, ..." — `docs/real_flight_readiness.md:103`
- **rung-1 data-integrity checklist**: "| D7 | **Mocap file present** (`<take>.csv`, exported as `t_s, x, y, z, qx, qy, qz, qw`, metres, z up), covering both sync wiggles; tracking loss in the flight < 0.5 s cumulative | yes |" — `docs/rung1_flight_cards.md:312`

### `D8` — 2 meanings

- **D-rulings**: "### D8. Flow timing (from D5's step-3 re-run)" — `docs/decisions_queue.md:295` (+1 more source(s))
- **rung-1 data-integrity checklist**: "| D8 | **Mocap synced:** `mocap_align` run on this sortie; its default windows (since 2026-10-11) are the two DISARMED sync-wiggle bursts (`RISI` \|ω\| > 2 rad/s: the last burst before arming and the first after disarming, ± 2 s; the old ..." — `docs/rung1_flight_cards.md:313`

### `D9` — 2 meanings

- **D-rulings**: "### D9. First UKF flight: with or without the forward-camera heading" — `docs/decisions_queue.md:308` (+1 more source(s))
- **rung-1 data-integrity checklist**: "| D9 | Sortie sheet complete: class (VERIFICATION/RESULT), battery, times, take name, any deviation | yes |" — `docs/rung1_flight_cards.md:314`

### `D10` — 2 meanings

- **D-rulings**: "### D10. `fgo_replay.py` TUM quaternion typo" — `docs/decisions_queue.md:321` (+1 more source(s))
- **rung-1 data-integrity checklist**: "| D10 | **EKF origin in the log** (ruling 1): an `ORGN` record in this boot's dataflash BEFORE the ARM event; the boot's "EKF3 IMUn initialised" messages (every core) precede the origin | yes. If not: no further sortie until the cause is ..." — `docs/rung1_flight_cards.md:315`

### `D11` — 2 meanings

- **D-rulings**: "### D11. FGO speed-up route" — `docs/decisions_queue.md:327` (+1 more source(s))
- **rung-1 data-integrity checklist**: "| D11 | **F7 and U4 as flown:** the sheet's yaw-check line filled in (\|diff\| ≤ 5°); the `ARM` event to take-off (the first `CTUN`/`RFND` climb) ≤ 5 s | yes. A deviation is recorded; it does not change the classification |" — `docs/rung1_flight_cards.md:316`

### `D12` — 2 meanings

- **D-rulings**: "### D12. External-estimator backend for the FGO" — `docs/decisions_queue.md:334` (+1 more source(s))
- **rung-1 data-integrity checklist**: "| D12 | **M1/M2/M3 as flown (2026-10-12):** no landing (`EV` LAND_COMPLETE / LAND_COMPLETE_MAYBE after a take-off) before this sortie's `ARM` in this boot's log (M1); the sheet's M2 line filled in, and `XKF1` (core 0) √(VN²+VE²+VD²) < 0.2 ..." — `docs/rung1_flight_cards.md:317`

### `DIAGNOSTIC` — 2 meanings

- **DIAGNOSTIC (numbers.md status: adds descriptive record)**: "- DIAGNOSTIC: reported but never a gate, or a descriptive record." — `docs/thesis/numbers.md:17`
- **status labels (numbers.md / methodology_index)**: "DIAGNOSTIC** (reported, never a gate)." — `METHODOLOGY.md:1149`

### `E1` — 2 meanings

- **UKF port equivalence bands**: "| E1 | 3-D position difference, `dsn_tex_r2` | **max ≤ 0.05 m, rms ≤ 0.01 m** | Same algorithm, both in double precision. The only difference expected is floating-point operation order (~1e-15 relative per operation), amplified by the ..." — `METHODOLOGY.md:5467` (+1 more source(s))
- **real-flight readiness checklist rows**: "| E1 | Flow validity = inlier ratio **and** feature count, ONE flag from one source, identical for EKF3, the UKF and the FGO. The threshold is calibrated on `p1c_*` only. | not built | a, b (it also feeds EKF3) | **Current committed ..." — `docs/real_flight_readiness.md:109`

### `F1` — 6 meanings

- **D12/D19 take-off backlog fix options**: "- **(F1) Run the SITL simulation slower (Gazebo `real_time_factor` 0.5, lockstep SITL follows).** This is" — `docs/d12_fgo_backend_report.md:31` (+1 more source(s))
- **experiment H far-spawn criterion**: "- **Criterion F1:** horizontal p95 ≤ **0.10 m** (5 × σ_pos) and yaw p95 ≤ **2°**. If it fails: stop and report" — `METHODOLOGY.md:11316`
- **offline tests (F-tests)**: "### PRE-REGISTRATION — offline tests F1, F2, F3 and the post-D15 FGO-vs-UKF with-heading comparison (written before any is run)" — `METHODOLOGY.md:7877` (+2 more source(s))
- **real-flight readiness items**: "| F1 | Mocap client: Vicon/OptiTrack stream (VRPN/NatNet) → ROS 2 pose with host stamps and Pi/ground-station receipt stamps | not built | a, b | No mocap client exists in the repo; only `eval/mocap_align.py` (offline) and `wall_watch.py` ..." — `docs/real_flight_readiness.md:115` (+1 more source(s))
- **thesis figures**: "| F1 scorecard | 3 estimators × 8 experiments; numbers.md §6.1, §6.2, §6.6, §15, §16, §17.2 and the claims table; JSONs as in the pack | 16/16 | none needed | see "Scorecard categories" below |" — `docs/handovers/2026-10-15_thesis_figures.md:22` (+2 more source(s))
- **watcher bench findings**: "- **F1 (B8a, one run, n = 1, GUIDED): flow loss on EKF3 was followed by a fast lateral excursion, with no EKF failsafe" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:363`

### `F2` — 5 meanings

- **D12/D19 take-off backlog fix options**: "- (F2) The D11 speed-up: C++ factors, or GTSAM's native factors in place of Python `CustomFactor`." — `docs/d12_fgo_backend_report.md:39` (+1 more source(s))
- **offline tests (F-tests)**: "**F2 — intermittent heading, evaluated in hindsight.**" — `METHODOLOGY.md:7926`
- **real-flight readiness items**: "| F2 | Watcher logic: capture-volume box, process liveness, tilt | needs adapting for real sensors | a, b | `sim/tools/wall_watch.py` (`--box`, `--watch-process`, `--dep-loss land`; fail-closed heartbeat contract at `:134-146`). Its input ..." — `docs/real_flight_readiness.md:116`
- **thesis figures**: "| F2 | figure | `F2_heading_stops_sideways_drift.png`, `F2_heading_stops_sideways_drift.pdf` | The camera heading stops the sideways drift: without it every estimator flies into the west wall | CURRENT | 4/4 | none needed |" — `docs/thesis/figures_thesis/index.md:13` (+1 more source(s))
- **watcher bench findings**: "- **F2: after a LAND that began with lateral motion, ArduCopter's land detector sometimes did not trip on flow-only" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:371` (+1 more source(s))

### `F3` — 5 meanings

- **D12/D19 take-off backlog fix options**: "- (F3) Temporary keyframe decimation while behind (a longer `kf_dt` when lag > threshold). This changes" — `docs/d12_fgo_backend_report.md:41` (+1 more source(s))
- **offline tests (F-tests)**: "**F3 — large initial heading error (nonlinearity).**" — `METHODOLOGY.md:7945`
- **real-flight readiness items**: "| F3 | Heartbeat path to the FC and an FC-side "no heartbeat → LAND" second layer (Lua or companion), plus a watcher → `LAND` MAVLink command | not built | a, b | In SITL the heartbeat is a local file (`<out>/watch_heartbeat`) that ..." — `docs/real_flight_readiness.md:117` (+1 more source(s))
- **thesis figures**: "| F3 accuracy without (m) / with (cm) heading (pack F03 + F04 + F05) | dsn_tex r1–r9 and the 6 camera bags without heading; UKF/FGO heading arms in cm; EKF3 slot says "no offline heading arm"; the checkerboard plain-wall columns are shaded ..." — `docs/handovers/2026-10-15_thesis_figures.md:24` (+1 more source(s))
- **watcher bench findings**: "- **F3 (B5b-noflag set-up): a source with no tracking flag and a perfectly still vehicle never confirms** (bit-identical" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:375`

### `F4` — 6 meanings

- **D12/D19 take-off backlog fix options**: "- (F4) EKF3 flies the take-off and the FGO takes over once its lag is inside budget. The flight is then" — `docs/d12_fgo_backend_report.md:43` (+1 more source(s))
- **naming collisions**: "- F4: `fly_trial.connect()` latches onto the first heartbeat it sees (mode-mapping risk); fixed in the bench driver" — `METHODOLOGY.md:13611`
- **offline tests (F-tests)**: "| 2(a) (F4) | `f4` | `batches/f4_replays_usable.jobs` (30 jobs, unchanged) + `f4_eval.py test cauchy:2.385 --trials <10 usable>` | none | the `--trials` order was unrecorded; it was rebuilt from `~/thesis_data/batches/f4_eval.txt`. Bags ..." — `docs/handovers/2026-10-09_final_rerun_pipeline.md:134` (+2 more source(s))
- **real-flight readiness items**: "| F4 | Watcher bench tests: watcher not started → no arm; watcher killed in a tethered hover → land | not built | a, b | **Being pre-registered now by another agent** (ruling 2026-10-10 item 4). The SITL analogue passed (T1/T2 in ..." — `docs/real_flight_readiness.md:118`
- **thesis figures**: "| F4 blank floor (pack F06) | `blank_behaviour.json`, +10/+30/+60 s, 11 flights per estimator; the EKF3 box gives the reason (invalid for the whole cruise, 0 valid airborne flow frames, origin output not scored) | 6/6 | **km-scale runaway ..." — `docs/handovers/2026-10-15_thesis_figures.md:25` (+1 more source(s))
- **watcher bench findings**: "- **F4: `fly_trial.connect()` takes the FIRST heartbeat it sees.** With other MAVLink senders on the link (MAVProxy, and" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:378` (+1 more source(s))

### `F5` — 2 meanings

- **thesis figures**: "| F5 | figure | `F5_T_tags_known_positions.png`, `F5_T_tags_known_positions.pdf` | Fewer tags, larger live errors (no live ordering claimed); the FGO's hindsight batch stays at 1–3 cm | CURRENT | 8/8 | none needed |" — `docs/thesis/figures_thesis/index.md:14`
- **watcher bench findings**: "- **F5: B5a / B5b-noflag bound.** "Stale within 0.5 s" with a 0.5 s stale limit cannot be met (detection is 8–10 ms" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:388` (+1 more source(s))

### `F6` — 2 meanings

- **thesis figures**: "| F6 | figure | `F6_O_outdoor_indoor.png`, `F6_O_outdoor_indoor.pdf` | Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight keeps the error near 1 m | CURRENT | 4/4 | none needed |" — `docs/thesis/figures_thesis/index.md:15` (+1 more source(s))
- **watcher bench findings**: "- **F6: the LAND retry policy can violate B10b (the build handover's open question 5, now with evidence).** B7b lost" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:383` (+1 more source(s))

### `F7` — 2 meanings

- **thesis figures**: "| F7 | figure | `F7_L_loop_closure.png`, `F7_L_loop_closure.pdf` | Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps | CURRENT | 5/5 | none needed |" — `docs/thesis/figures_thesis/index.md:16`
- **watcher bench findings**: "- **F7 (n = 1; caused by the harness, amendment A9).** A Gazebo carry that rotated the vehicle by a yaw the gyros" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:405` (+2 more source(s))

### `F8` — 2 meanings

- **thesis figures**: "| F8 H (pack F14) | FLYING estimators only, grouped by loss duration: EKF3 S1 + S1 far, UKF S2v2, FGO S3v2; effective drift, mm | 6/6 | **bands up to 400 mm next to drifts ≤ 31 mm: linear axis clipped at 60 mm; the in-range 50 mm bands are ..." — `docs/handovers/2026-10-15_thesis_figures.md:29` (+2 more source(s))
- **watcher bench findings**: "- **F8 (n = 1; cause not established).** Before the first B6b run 1 attempt, EKF3's velocity on the ground diverged" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:414` (+2 more source(s))

### `FROZEN` — 2 meanings

- **FROZEN = parameters fixed before validation**: "### Phase 3 calibration — result (p1c_* only; parameters FROZEN before validation)" — `METHODOLOGY.md:2750`
- **FROZEN = simulation results frozen**: "- **Simulation results are FROZEN:** no new result experiments or re-runs. Verification flights for real-flight ... readiness are allowed, short, under the standing rule." — `METHODOLOGY.md:13399` (+1 more source(s))

### `G1` — 9 meanings

- **Experiment H S1 per-flight gates**: "- **G1:** the profile completes, every `HSEG` and `OCCLUDER ON/OFF` marker present, landed;" — `METHODOLOGY.md:10672`
- **Experiment O per-flight gates**: "- **G1:** all OUTBACK markers present; GNSS OFF and ON each logged once." — `METHODOLOGY.md:10352`
- **Experiment T per-flight gates**: "- **G1:** 5 laps complete (20 `LEG START` markers and `LAPS END`), landed; `AHRS_EKF_TYPE 10`, `LOG_REPLAY 1`," — `METHODOLOGY.md:10161`
- **H backend ground-test gates (S2/S3 tag input)**: "- **G1 (configuration, from the PARM dump):**" — `docs/h_backends_tag_input.md:420`
- **U10 replay-gate criteria**: "| **G1** | **Initialises before arming, with the log's geometry** (definition §4.1) | must hold | the arming gate in type 12 needs an initialised UKF (`AP_AHRS_UKF::pre_arm_check`). If the rangefinder reads below its minimum on the ground, ..." — `docs/u10_replay_gate_band.md:191` (+1 more source(s))
- **backend ground-test gates (D9 P3 / D17 V3 / D19 FGO)**: "- **(G1) Configuration:** the log's PARM dump has `AHRS_EKF_TYPE = 12` and `AHRS_UKF_ENABLE = 1`." — `METHODOLOGY.md:7379` (+1 more source(s))
- **board firmware go/no-go**: "| G1 | The exact board is named, and the firmware was built for its hwdef (not the stand-in of §1) | the `.apj` `board_id` = the board's |" — `docs/board_firmware_plan.md:271`
- **heading ground-test gates (VISO_DELAY_MS, closed-loop Part 1)**: "- **G1, yaw-only ExtNav fusion.**" — `METHODOLOGY.md:5033`
- **mocap watcher gaps**: "| G1 | **No mocap input.** The watcher reads Gazebo `/ground_truth/pose`. It needs the mocap rigid-body stream (e.g. VRPN or NatNet to ROS 2) in the mocap frame, aligned to the box definition. | all |" — `docs/real_flights_plan.md:442`

### `G2` — 10 meanings

- **Experiment H S1 per-flight gates**: "- **G2:** `VISP` = `/tags/sent`;" — `METHODOLOGY.md:10673`
- **Experiment O per-flight gates**: "- **G2:** EKF3 changes source set twice (to set 2 after OFF, to set 1 after ON), from the `XKFS.SS` transitions." — `METHODOLOGY.md:10353`
- **Experiment T per-flight gates**: "- **G2 (identical measurements):**" — `METHODOLOGY.md:10163`
- **H backend ground-test gates (S2/S3 tag input)**: "- **G2 (fix accepted):**" — `docs/h_backends_tag_input.md:424`
- **U10 replay-gate criteria**: "| **G2** | **Stays valid through the hover and the legs:** `SS` bit 3 (`horiz_pos_rel`) set and `Healthy` = 1 on **every** `ukf_shadow.csv` row in W; `FlowAgeMs` < 5000 on every row in W; the rows cover W (§4.1) | 100 % of W | in closed ..." — `docs/u10_replay_gate_band.md:192` (+1 more source(s))
- **backend ground-test gates (D9 P3 / D17 V3 / D19 FGO)**: "- **(G2) Arming:** the pre-arm checks pass (including the UKF's own, "UKF not initialised" /" — `METHODOLOGY.md:7380`
- **board firmware go/no-go**: "| G2 | Flash free ≥ 32 kB after the fork, for the exact board and feature set | §2 table, re-measured |" — `docs/board_firmware_plan.md:272`
- **heading ground-test gates (VISO_DELAY_MS, closed-loop Part 1)**: "- **G2, arming with the heading node.** It arms with no VisualOdom or EKF pre-arm failure, and" — `METHODOLOGY.md:5039`
- **mocap watcher gaps**: "| G2 | **No stale-pose check.** The box and tilt rules are evaluated only when a pose ARRIVES, and the `box=1` flag is static, so a stopped mocap stream triggers nothing. §7 requires it to. | B5 |" — `docs/real_flights_plan.md:443` (+1 more source(s))
- **real-flight readiness checklist**: "| G2 | UKF CPU load on the FC MCU at 80 Hz predict plus updates; loop-time margin | not built | b (onboard UKF) | Estimate only: 5–8% CPU, 0.3–0.4 ms per predict in double on H7 (Part C §5.3). Never measured. | 0.5 d bench (scheduler `PM` ..." — `docs/real_flight_readiness.md:126`

### `G3` — 10 meanings

- **Experiment H S1 per-flight gates**: "- **G3:** max sent-fix error vs GT ≤ 3 × σ_pos (no wrong ids);" — `METHODOLOGY.md:10674`
- **Experiment O per-flight gates**: "- **G3:** EKF3 aligned yaw and used GPS before OFF. Pass if `XKF4.SS` `using_gps` is true for ≥ 5 s before OFF." — `METHODOLOGY.md:10354`
- **Experiment T per-flight gates**: "- **G3:** every sent fix within 0.3 m (horizontal) and 3° of GT (no wrong ids)." — `METHODOLOGY.md:10167`
- **H backend ground-test gates (S2/S3 tag input)**: "- **G3 (re-anchor visible):**" — `docs/h_backends_tag_input.md:428`
- **U10 replay-gate criteria**: "| **G3** | **No numerical failure:** `n_chol_fail` = 0 over the whole log, read from the Replay's `ukf_stats.csv`. **A missing `ukf_stats.csv`, or one without an `n_chol_fail` row, FAILS G3** (U10 rule 1). `n_chol_retry` is reported | = 0 ..." — `docs/u10_replay_gate_band.md:193`
- **backend ground-test gates (D9 P3 / D17 V3 / D19 FGO)**: "- **(G3) The UKF is the ACTIVE attitude source:** during the armed hold, the logged AHRS attitude" — `METHODOLOGY.md:7382`
- **board firmware go/no-go**: "| G3 | SITL byte-identity of the `board-h743` commit vs the reference, re-run if the source changed | identical (§2.5) |" — `docs/board_firmware_plan.md:273`
- **heading ground-test gates (VISO_DELAY_MS, closed-loop Part 1)**: "- **G3, EKF origin.** G1 and G2 pass without an origin ever being set (none is set in this" — `METHODOLOGY.md:5041`
- **mocap watcher gaps**: "| G3 | **No rigid-body identity check** (wrong body, or a swapped or renamed asset). | B6 |" — `docs/real_flights_plan.md:444`
- **real-flight readiness checklist**: "| G3 | UKF port algorithm: shadow and flying, tag ExtNav input, option (i) attitude hold on invalid output, first tag anchor refused once armed, jitter fix | exists and tested in SITL | b | Installed `ukf-jitter-fix` `abb0357d` ..." — `docs/real_flight_readiness.md:127`

### `G4` — 10 meanings

- **Experiment H S1 per-flight gates**: "- **G4:** IMU-gap rule ok;" — `METHODOLOGY.md:10675`
- **Experiment O per-flight gates**: "- **G4:** both replays aligned before OFF and fused GNSS on both sides of the indoor segment." — `METHODOLOGY.md:10355`
- **Experiment T per-flight gates**: "- **G4:** both replays complete with 0 keyframe failures; FGO tag factors ≥ 95% of the sent fixes after the anchor." — `METHODOLOGY.md:10168`
- **H backend ground-test gates (S2/S3 tag input)**: "- **G4 (reset consumed):** a Copter `EKF_YAW_RESET` event at the anchor, and the GUIDED target follows the reset." — `docs/h_backends_tag_input.md:434`
- **U10 replay-gate criteria**: "| **G4** | **Accuracy against mocap:** UKF (`XUKO`, message `RUKO`) evo -a (SE(3), `t_max_diff` 0.05) over W ≤ **max(2.0 × EKF3_R, EKF3_R + 0.10 m)**, with EKF3_R = the replayed EKF3 (`XKF1@100`) on the same flight, window and Replay ..." — `docs/u10_replay_gate_band.md:194`
- **backend ground-test gates (D9 P3 / D17 V3 / D19 FGO)**: "- **(G4) Stable on the ground:** over the armed hold, `XUKO` horizontal position stays within 0.10 m of" — `METHODOLOGY.md:7388`
- **board firmware go/no-go**: "| G4 | P1–P10 all pass on the bench | as in §5 |" — `docs/board_firmware_plan.md:274`
- **heading ground-test gates (VISO_DELAY_MS, closed-loop Part 1)**: "- **G4, latency (run 1).** Minimum capture-to-receipt latency, from two independent measures:" — `METHODOLOGY.md:5043`
- **mocap watcher gaps**: "| G4 | **The breach action stops the simulation** (SIGTERM to `fly_trial`/`run_trial`). On hardware it must command LAND over MAVLink (`SET_MODE`/`MAV_CMD_DO_SET_MODE` LAND), one-shot and latched, and alert the safety pilot (audible). | ..." — `docs/real_flights_plan.md:445`
- **real-flight readiness checklist**: "| G4 | `thesis_nav_check`: origin-independent "position lost → LAND" for types 12/13 | exists and tested in SITL | b | `ArduCopter/ekf_check.cpp:330-340` in the fork. SITL safety tests (a) PASS for both estimators. **Copter only; a ..." — `docs/real_flight_readiness.md:128`

### `G5` — 8 meanings

- **Experiment H S1 per-flight gates**: "- **G5 (safety):** GT stays ≥ 0.5 m from every wall." — `METHODOLOGY.md:10676`
- **H backend ground-test gates (S2/S3 tag input)**: "- **G5 (no gate):** after the anchor, every `XUKT` row fuses (`NF` increments by one per row); `XUKO.EvO` = 0." — `docs/h_backends_tag_input.md:438`
- **U10 replay-gate criteria**: "| **G5** | **Bounded unaligned drift:** the start-aligned horizontal drift (rung-1 §4.3 rule; `drift_start_aligned.final_h_m`, the error at the last estimator sample in W, i.e. at t_ld − 5 s) ≤ **D_max = 1.0 m** (SIGNED 2026-10-12; basis: ..." — `docs/u10_replay_gate_band.md:195` (+1 more source(s))
- **backend ground-test gates (D9 P3 / D17 V3 / D19 FGO)**: "- **(G5) Disarm:** the vehicle disarms on request, with no EKF/UKF failsafe or crash message in the" — `METHODOLOGY.md:7393`
- **board firmware go/no-go**: "| G5 | Rollback rehearsed once on the bench (§6 steps 1–7), and the stock `.apj` and parameter backup are on the laptop | done |" — `docs/board_firmware_plan.md:275`
- **heading ground-test gates (VISO_DELAY_MS, closed-loop Part 1)**: "- **G5, the delay takes effect and the heading is time-aligned (run 2).**" — `METHODOLOGY.md:5050` (+1 more source(s))
- **mocap watcher gaps**: "| G5 | **No FC-side layer: the watcher sends no MAVLink HEARTBEAT, and no GCS-failsafe parameters are set.** The native mechanism needs no Lua: `FS_GCS_ENABLE` 5 (Land), `FS_GCS_TIMEOUT` 3 s (range 2–120; the default is 5), and ..." — `docs/real_flights_plan.md:446`
- **real-flight readiness checklist**: "| G5 | `AP_NavFGO` thin backend: `ODOMETRY` validation (flag, arrival ≤ 250 ms, age ≤ 250 ms), FC-IMU output predictor, `XFGI`/`XFGO` logging | exists and tested in SITL | b | FG1–FG3b, D25, `cl_fgo_*`, `fgo_cpp_shadow_*` ..." — `docs/real_flight_readiness.md:129`

### `G6` — 5 meanings

- **H backend ground-test gates (S2/S3 tag input)**: "- **G6 (estimate):**" — `docs/h_backends_tag_input.md:439`
- **U10 replay-gate criteria**: "| **G6** | **Replay fidelity:** ONLY if rung 1 flew the fork in shadow (the Replay output holds onboard `XUKF`). Replayed `RUKF`/`RUKS` against onboard `XUKF`/`XUKS` in the same Replay output: **E1 3-D position max ≤ 0.05 m, rms ≤ 0.01 m; ..." — `docs/u10_replay_gate_band.md:196` (+1 more source(s))
- **board firmware go/no-go**: "| G6 | `AHRS_EKF_TYPE 3` confirmed after every flash, and `AHRS_UKF_TFAIL 0` | readback |" — `docs/board_firmware_plan.md:276`
- **mocap watcher gaps**: "| G6 | **The FC will arm without a watcher.** `failsafe_gcs_check()` returns early if the GCS has never been seen (`events.cpp:133-136`). Without the flight script, nothing on the FC enforces "no watcher, no arming". Options: (i) procedure ..." — `docs/real_flights_plan.md:447`
- **real-flight readiness checklist**: "| G6 | C++ FGO node on x86 (GTSAM 4.2.1, ROS 2 / MAVLink adapter, time_ref stamping, reorder delay 0.20 s) | exists and tested in SITL | b | `src/estimators/fgo_cpp/`. Equivalence bands A/B/C/L passed; flew S3/S3v2 and the FGO safety ..." — `docs/real_flight_readiness.md:130`

### `G7` — 3 meanings

- **board firmware go/no-go**: "| G7 | The rung's pre-registration and the SITL gates of the costing doc (V1–V7), for anything beyond shadow | signed off |" — `docs/board_firmware_plan.md:277`
- **mocap watcher gaps**: "| G7 | **Dependency liveness uses `pgrep`, which is local only.** The flow tracker, the bridges and the estimator node run on the Pi. A networked liveness signal is needed, such as topic rates seen over ROS 2 or a per-process MAVLink/ROS ..." — `docs/real_flights_plan.md:448`
- **real-flight readiness checklist**: "| G7 | Corrected FGO (initial yaw σ 1° in both cores, ruling 2026-10-10): C++ equivalence on the corrected build, plus SITL safety (a)/(b) | not built | b (FGO) | Ruling 2026-10-10 items 1–3 and the reorder ruling (in progress). Plan §7: ..." — `docs/real_flight_readiness.md:131`

### `G8` — 3 meanings

- **board firmware go/no-go**: "| G8 | Main-thread stack margin (P7) and no new long loops (P8) | measured |" — `docs/board_firmware_plan.md:278`
- **mocap watcher gaps**: "| G8 | **`--dep-loss stop` has no hardware meaning.** In SITL it stops the simulation. On hardware both settings must end in LAND. Pre-registered: `stop` maps to LAND plus an alert (or the option is removed). | B9 |" — `docs/real_flights_plan.md:449`
- **real-flight readiness checklist**: "| G8 | C++ FGO on the real Pi: GTSAM 4.2.1 + Boost on arm64 (native or cross build), ROS 2 Jazzy arm64, keyframe CPU budget (33 ms), memory, core pinning and RT priority, **live solve-time self-stop** (stage 3 requirement: p99 > keyframe ..." — `docs/real_flight_readiness.md:132`

### `G9` — 2 meanings

- **mocap watcher gaps**: "| G9 | **The `watch_heartbeat` file is local.** That is valid only if the watcher and the flight script run on the same ground-station machine, which is pre-registered as a requirement. | B1, B2 |" — `docs/real_flights_plan.md:450`
- **real-flight readiness checklist**: "| G9 | C++ FGO node transport to a serial FC (today UDP only, learning the peer from SITL SERIAL3) | needs adapting for real sensors | b (FGO) | `fgo_cpp_node.cpp:9-10,80` (`UdpEndpoint`). With a router (B1) the change may be configuration ..." — `docs/real_flight_readiness.md:133`

### `G10` — 2 meanings

- **mocap watcher gaps**: "| G10 | **The `--box` rule is x/y only.** It has no height limit (capture-volume top or ceiling). Add z_max, and z_min only for "below the floor" sanity. | B4 |" — `docs/real_flights_plan.md:451`
- **real-flight readiness checklist**: "| G10 | UKF live on the Pi (only if U9 = Pi placement): a live UKF node plus a UKF mode in the thin backend | not built | b (only if U9 = Pi) | Only `ukf_core.py` and the replay scripts exist; there is no live Python UKF node. | 3–5 d plus ..." — `docs/real_flight_readiness.md:134`

### `G11` — 2 meanings

- **mocap watcher gaps**: "| G11 | **Heartbeat masking.** `handle_heartbeat` refreshes the GCS-failsafe timer for ANY HEARTBEAT, RC_OVERRIDE or MANUAL_CONTROL from a system ID in the GCS range (`GCS_Common.cpp:4231,4350,7671`; `sysid_is_gcs`). MAVProxy and pymavlink ..." — `docs/real_flights_plan.md:452` (+1 more source(s))
- **real-flight readiness checklist**: "| G11 | Offline replay of the UKF/FGO on real-flight logs (Python `ukf_replay.py` / `fgo_replay.py`, C++ replay, port Replay on `LOG_REPLAY` dataflash) | needs adapting for real sensors | a | It assumes bag topics, sim stamps, 333 Hz/3 ms ..." — `docs/real_flight_readiness.md:135`

### `H1` — 3 meanings

- **OI-1 blank-floor hypotheses**: "> - **H1 — the gate decides what reaches velocity.** Under starved blank-floor flow, the" — `METHODOLOGY.md:619`
- **real-flight readiness checklist**: "| H1 | SITL safety tests (a) estimator failure in a hover and (b) node or bridge kill, on the corrected UKF and FGO builds | exists and tested in SITL | b | Procedure and scorer exist (`tools/run_h_safety.sh`, `eval/h_safety_score.py`). ..." — `docs/real_flight_readiness.md:141`
- **rung-1 scorer SITL regression checks**: "- **H1:** heading on `dsn_tex_r1..r3`, UKF and FGO TUMs, against `d15_drift.json` (sign-flipped ENU → NED). Equal" — `docs/handovers/2026-10-12_r1_scoring_items.md:53`

### `H2` — 3 meanings

- **OI-1 blank-floor hypotheses**: "> - **H2 — near-zero measured flow is being read as motion.** Blank-floor flow has" — `METHODOLOGY.md:626`
- **real-flight readiness checklist**: "| H2 | SITL rehearsal at Pi-like link latency (`tc netem` or a bridge delay): FG1, FG2, FG3/FG3b, D25, plus one closed-loop P-HOLD per estimator | not built | b | Plan §9.2. A gate failure blocks hardware closed loop for that estimator. | ..." — `docs/real_flight_readiness.md:142`
- **rung-1 scorer SITL regression checks**: "- **H2:** heading on the NED-yaw path, `d15_port/dsn_tex_r8` `ukf_shadow.csv` against SIM: 9.293967, equal to the" — `docs/handovers/2026-10-12_r1_scoring_items.md:55`

### `H3` — 3 meanings

- **real-flight readiness checklist**: "| H3 | Rehearsal of P-HOLD and P-LAPS in the simulated mocap room (`fly_trial` profiles, moving setpoints, D24 clock, land on failure) | exists and tested in SITL | a, b | Experiment H S1/S2/S3 (`room_wall_tag`); experiment T (laps). | 0 ..." — `docs/real_flight_readiness.md:143`
- **rung-1 scorer SITL regression checks**: "- **H3 (information):** EKF3 `XKF1@0` against SIM on the pinned window: +7.96 / +7.59 / +8.10 deg/min, inside" — `docs/handovers/2026-10-12_r1_scoring_items.md:59`
- **stage-3 sorties**: "| **H3: hand-carried in the volume** (disarmed; type 12 active, nothing steers) | verification | ~2 min: wiggle, one carried out-and-back leg at flight height, wiggle | the output is computed exactly as in flight; one leg checks the flow ..." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:59`

### `hindsight` — 3 meanings

- **L keyframe-FGO tracks**: "**Hindsight** = every keyframe after a final LM polish" — `METHODOLOGY.md:10476` (+1 more source(s))
- **figure line-style convention**: "Conventions: one fixed colour and marker per estimator; solid lines and filled marks = live, dashed lines and open marks = hindsight; linear" — `docs/thesis/figures_thesis/thesis_figures_combined.pdf p.1`
- **hindsight tracks (F2, T, O)**: "- **hindsight:** the full-trajectory estimate after the flight (the batch FGO; for the UKF and live" — `METHODOLOGY.md:7938` (+1 more source(s))

### `L1` — 2 meanings

- **FGO C++ port band L rows**: "| L1 | dsn_tex_r1 | tape with the offline dejittered IMU stamps substituted (`--imu-stamp header`); arming time = the export's (`--arm-source param`); delay 0.20 s; everything else live: receipt order, reorder buffer, interval-averaged ..." — `docs/fgo_cpp_port.md:422`
- **G5.3 latency-stability sub-criteria**: "- **(L1)** The linear-fit slope of per-frame latency (sent − capture) against capture time," — `METHODOLOGY.md:5849`

### `L2` — 2 meanings

- **FGO C++ port band L rows**: "| L2 | fwdc_tex_r1 | as L1, plus the heading input: the export's frozen forward headings written as the heading bridge's sent message (NED yaw = −psi, quality 100, angErr 0) at their capture stamp, with heading sigma = the offline heading ..." — `docs/fgo_cpp_port.md:423`
- **G5.3 latency-stability sub-criteria**: "- **(L2)** Every 30 s block median latency is ≤ 200 ms. Basis: the largest run-1 block median" — `METHODOLOGY.md:5852`

### `live` — 3 meanings

- **L keyframe-FGO tracks**: "- **Live** = the newest keyframe after each iSAM2 update. **Hindsight** = every keyframe after a final LM polish" — `METHODOLOGY.md:10476`
- **figure line-style convention**: "Conventions: one fixed colour and marker per estimator; solid lines and filled marks = live, dashed lines and open marks = hindsight; linear" — `docs/thesis/figures_thesis/thesis_figures_combined.pdf p.1`
- **hindsight tracks (F2, T, O)**: "- **live:** the current (filtered) estimate at each time, for the UKF and the live FGO;" — `METHODOLOGY.md:7937`

### `lockout` — 2 meanings

- **F1 heading-gate metrics**: "(iii) correct headings rejected (weight < 0.5 or gated out), and **lockout episodes** (≥ 3 s of ... consecutive correct headings rejected);" — `METHODOLOGY.md:7918`
- **H tag-loss metrics**: "- **lockout:** EKF3 (no `VISP`-driven correction for > 2 s while fixes arrive, i.e. |estimate − fix| > 3σ_pos ... sustained); the UKF/FGO (none possible: no gate)." — `METHODOLOGY.md:10684`

### `noise floor` — 2 meanings

- **ds_* noise floor (apparatus ATE range)**: "| Noise floor `ds_*` (compass-active, apparatus): within-condition ATE range | 2.81–10.90 m | m | CURRENT (`ds_*` only) | M:L800 |" — `docs/thesis/numbers.md:865`
- **dsn noise floor (SD over repeats)**: "| Noise floor SD (re-flown `dsn_tex`): EKF3 (n = 10) / FGO (n = 9) / d (n = 9) | 0.31 [0.22, 0.57] / **1.30 [0.88, 2.49]** / 1.02 [0.69, 1.96] (the FGO is no longer the "tight" estimator) | m | CURRENT (FGO-only re-run 2026-10-10) | ..." — `docs/thesis/numbers.md:229` (+1 more source(s))

### `P1` — 6 meanings

- **D9 UKF flight preconditions**: "- **(P1)** the queue check on Replay logs (no loss; EKF3's flow timing; time-ordered);" — `METHODOLOGY.md:6846`
- **F7 bench session preconditions**: "- **P1:** the watcher logs "tie … captured at the EKF-origin broadcast" (not "TIE CAPTURE FAILED") after the verified" — `docs/handovers/2026-10-12_f7_cards.md:98`
- **F8 proposed parameter items**: "- **P1: RNGFND1_GNDCLR and FLOW_POS_Z must be the measured real values.**" — `docs/handovers/2026-10-12_f8_investigation.md:217`
- **board bench checks**: "| P1 | Banner and version: git hash = `board-h743` commit; the board name | exact match |" — `docs/board_firmware_plan.md:227`
- **forward-camera Phase 1/2 criteria**: "| P1 | flow and lidar header timing (cruise) | rate 30.30 Hz ± 0.1%; ≤ 0.5% of gaps above 1.5 periods. `dsn` is exact (0.00%); 0.5% is one dropped frame per ~6.6 s, a negligible loss of information. | Dropped or late downward frames would ..." — `METHODOLOGY.md:1711`
- **plan step 2(a) decision rules**: "- **P1 (PRIMARY):** the robust FGO's **yaw maximum** < the hard-gated FGO's on **≥ 10 of 12** flights." — `METHODOLOGY.md:9730`

### `P2` — 5 meanings

- **D9 UKF flight preconditions**: "- **(P2)** a shadow run of **the exact binary to be flown** (`AHRS_EKF_TYPE 10`, `AHRS_UKF_ENABLE 1`):" — `METHODOLOGY.md:6847`
- **F7 bench session preconditions**: "- **P2:** `EK3_SRC1_YAW` 0, `SCR_ENABLE` 1, `AHRS_EKF_TYPE` 3 read back." — `docs/handovers/2026-10-12_f7_cards.md:100`
- **F8 proposed parameter items**: "- **P2: EK3_FLOW_I_GATE.** A larger gate re-opens sooner, but it is a global change to the estimator under test. Not recommended for the comparison." — `docs/handovers/2026-10-12_f8_investigation.md:220`
- **board bench checks**: "| P2 | Parameters read back: every value of the rung's parameter file (`check_parm.py` then a full readback; the eeprom gotcha, Known Issue #10, applies on hardware) | 0 mismatches |" — `docs/board_firmware_plan.md:228`
- **forward-camera Phase 1/2 criteria**: "| P2 | flow → EKF3 latency (median and p95) | ≤ same-world `dsn` mean + **12.5 ms** (one EKF3 prediction step, its own time resolution; `AP_NavEKF3_Measurements.cpp:232-234`). Matched frames ≥ same-world `dsn` minimum − 5 pp (`dsn` blank ..." — `METHODOLOGY.md:1713` (+1 more source(s))

### `P3` — 3 meanings

- **D9 UKF flight preconditions**: "- **(P3)** a ground test of the backend with `AHRS_EKF_TYPE 12` (arms, holds, disarms; the UKF" — `METHODOLOGY.md:6850`
- **board bench checks**: "| P3 | **Backends compiled in:** the parameters `AHRS_UKF_ENABLE`, `AHRS_UKF_TFAIL`, `AHRS_FGO_ENABLE` exist (stock firmware has no such parameters) | present |" — `docs/board_firmware_plan.md:229`
- **forward-camera Phase 1/2 criteria**: "| P3 | downward flow conditions (unchanged from the original (b)) | inlier mean ±0.01 of the `dsn` mean (8× the textured n=3 range, ~1.5% of the textured–blank gap); % below 0.5 within ±3 pp; features ±5%; `flow_y_raw` ±2% (textured, ..." — `METHODOLOGY.md:1714`

### `P4` — 2 meanings

- **board bench checks**: "| P4 | `AHRS_EKF_TYPE 3`, `AHRS_UKF_ENABLE 0`, `AHRS_FGO_ENABLE 0`: the vehicle is stock EKF3 ("backends disabled reproduces EKF3", costing doc §2) | EKF3 active; the same pre-arm and arming behaviour as stock |" — `docs/board_firmware_plan.md:230`
- **forward-camera Phase 1/2 criteria**: "| P4 | outcome, **textured** | evo -a (cruise) within the n=3 range widened by one range-width each side: **FGO [4.18, 5.35]**, **EKF3 [1.26, 8.13]**. | The forward-camera setup changed estimator behaviour through the shared inputs. |" — `METHODOLOGY.md:1715`

### `Phase 1` — 2 meanings

- **forward-camera workstream phases**: "### Phase 1 plan and confound-check acceptance (pre-registered before flying)" — `METHODOLOGY.md:1428` (+1 more source(s))
- **project phases (CLAUDE.md / PROGRESS.md)**: "### Phase 1 checklist" — `PROGRESS.md:580` (+1 more source(s))

### `Q2` — 2 meanings

- **final re-run open questions**: "2. **Closed-loop prediction (`cl_pred`).** Should the offline FGO contact-prediction input be recomputed with the" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:304`
- **minimal-path readiness questions**: "- Q1–Q3 (FC board, Pi/cameras/rangefinder, mocap system) come from the supervisor." — `METHODOLOGY.md:12972`

### `Q3` — 2 meanings

- **final re-run open questions**: "3. **F1 calibration.** Is k = 2.385 kept as registered (the default here), or is the 14-job calibration re-run, which" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:307`
- **minimal-path readiness questions**: "- Q1–Q3 (FC board, Pi/cameras/rangefinder, mocap system) come from the supervisor." — `METHODOLOGY.md:12972`

### `Q4` — 2 meanings

- **final re-run open questions**: "4. **D27 item 3 / F3 re-measurement.** The FGO side is scripted (opt-in). Are the D26 flights used (default, isolating" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:309`
- **minimal-path readiness questions**: "- Q4 (where the UKF runs in closed loop) is moot;" — `METHODOLOGY.md:12968`

### `Q6` — 2 meanings

- **final re-run open questions**: "6. **V-L scoring.** The original `three_way_eval --est` labels were not recorded. Should the V-L check be re-scored" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:316`
- **minimal-path readiness questions**: "- Q6: yes, an offline-only FGO is acceptable;" — `METHODOLOGY.md:12970`

### `R1` — 7 meanings

- **D17 V1/V2 heading-Replay checks**: "- **R1 (same input):** every `REPH` message replayed reaches the UKF, and every sample the UKF accepts" — `METHODOLOGY.md:7596`
- **Experiment H supervisor ruling items (2026-10-08)**: "**R1. During tag loss, position hold falls back to optical flow (with IMU and rangefinder) until the tag returns.**" — `docs/tag_hold_design.md:9`
- **plan-to-freeze risks**: "- **R1 (new work, threatens 9 Oct by ~1 day).** The live FGO node has **no camera-heading input**; only" — `docs/plan_to_freeze.md:32`
- **result flights/sorties (R1…Rn)**: "| **R1…Rn: result flights** | **result-producing (pre-registered here)** | the §3 profile (~2.5–3.5 min) | set by what the result needs (§3) | scoring (§4–§8) |" — `docs/rung1_preregistration.md:83` (+1 more source(s))
- **rgs_check_tex roll-gain check criteria**: "| R1 | roll oscillation removed | cruise gyro-x rms **≤ 0.05 rad/s** AND 15–20 Hz band rms **≤ 0.040 rad/s** | Pitch runs at the same effective loop gain at 0.0054 rms; allowing roll 10× pitch for lateral-control activity gives 0.05. The ..." — `METHODOLOGY.md:4608`
- **rung-1 work items (minimal real-flight plan)**: "| R1 | **Converter** BIN → FGO inputs (§4.3), with geometry overrides and the SITL acceptance test on `cl_a_tex_half` | 3–4 d | — | **yes** | **Medium.** Timing rules for 400 Hz deltas; `RISI` dt quirks; the SITL band may need a justified ..." — `docs/minimal_real_flight_plan.md:358` (+1 more source(s))
- **watcher bench re-run set-up changes**: "- **R1 — A1 FIXED (the B8a harness fault, handover 2026-10-12 §4).** The EKF origin (`SET_GPS_GLOBAL_ORIGIN`, the same" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:18`

### `R2` — 6 meanings

- **D17 V1/V2 heading-Replay checks**: "- **R2 (queue):** each accepted heading is processed exactly once, in time order, ≥ 60 ms after its" — `METHODOLOGY.md:7599`
- **Experiment H supervisor ruling items (2026-10-08)**: "**R2. EKF3, source check:** **one source set suffices; no switching is needed.**" — `docs/tag_hold_design.md:12`
- **plan-to-freeze risks**: "- **R2.** The D15 node core's take-off step time has not been measured live. If half speed does not" — `docs/plan_to_freeze.md:38`
- **rgs_check_tex roll-gain check criteria**: "| R2 | \|FIX\| toward the true-rotation floor | airborne mean \|FIX\| **≤ 150** | The floor is 67 (true-rotation reconstruction). The excess over it (240–254) is the uncancelled roll tone, which scales with its amplitude, so R1's ≥ 10× ..." — `METHODOLOGY.md:4609`
- **rung-1 work items (minimal real-flight plan)**: "| R2 | **UKF port for real geometry** in Replay: DAL offsets, `EK3_FLOW_DELAY`, range limits; byte-identical on SITL; rebuild the fork's Replay (sitl board, light) | 0.5–1 d | — | **yes** | Low |" — `docs/minimal_real_flight_plan.md:359`
- **watcher bench re-run set-up changes**: "- **R2 — consequence: the stock EKF failsafe is now LIVE in every session** (`ekf_check.cpp:35-39` no longer returns at" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:25`

### `R3` — 6 meanings

- **D17 V1/V2 heading-Replay checks**: "- **R3 (alignment):** alignment happens at the first processed heading, and there are no pseudo-yaw" — `METHODOLOGY.md:7601`
- **Experiment H supervisor ruling items (2026-10-08)**: "**R3. UKF and FGO: identical inputs** — the same tag fixes when visible (the `/tags/sent` stream EKF3 received), flow," — `docs/tag_hold_design.md:29`
- **plan-to-freeze risks**: "- **R3.** 20+ half-speed flights at ~13 min wall each is ~5 h of flight time before the 16 Oct freeze." — `docs/plan_to_freeze.md:41`
- **rgs_check_tex roll-gain check criteria**: "| R3 | pitch unchanged | cruise gyro-y rms within **[0.0027, 0.0108]** (0.5×–2× the old 0.0054) | Pitch gains are unchanged, so the expectation is equality. ±6 dB covers any change in roll→pitch coupling once the limit cycle is gone. | ..." — `METHODOLOGY.md:4610`
- **rung-1 work items (minimal real-flight plan)**: "| R3 | UKF CSV → TUM on the FC clock | 0.25 d | R2 | yes | Low |" — `docs/minimal_real_flight_plan.md:360`
- **watcher bench re-run set-up changes**: "- **R3 — sessions.** `ground` (B1a, B1c(i–iv), B0, B1b/B9d, B5c, B6a, B1-native, B7b, **F6c**, B10c, B4a/B4c (A8)," — `docs/handovers/2026-10-12_watcher_bench_rerun.md:29`

### `R4` — 6 meanings

- **D17 V1/V2 heading-Replay checks**: "- **R4 (acceptance):** ≥ 95% of processed headings in the cruise window pass the gate. Basis: R is" — `METHODOLOGY.md:7603`
- **Experiment H supervisor ruling items (2026-10-08)**: "**R4. Loss metrics:**" — `docs/tag_hold_design.md:32`
- **plan-to-freeze risks**: "- **R4.** If an FGO gate fails, 9 Oct has only ~1.5 days of buffer. Any failure is flagged the same day." — `docs/plan_to_freeze.md:43`
- **rgs_check_tex roll-gain check criteria**: "| R4 | take-off, hover and cruise profile | take-off 1.484–1.502 s ± max(range, 0.1 s) → **[1.384, 1.602] s**; climb peak ± max(range, 0.046 m) → **[2.187, 2.288] m**; cruise height ± 0.046 m → **[2.244, 2.345] m**; cruise speed **[0.4899, ..." — `METHODOLOGY.md:4611`
- **rung-1 work items (minimal real-flight plan)**: "| R4 | **EKF3 Replay**: 0 d if pinned flies, 0.5 d stock Replay if 4.7.0 flies; `check_replay.py` acceptance with a pre-registered tolerance | 0.5–1 d | S6, first real log | partly | **Medium.** Not bit-exact on ARM; a non-H7 board makes ..." — `docs/minimal_real_flight_plan.md:361`
- **watcher bench re-run set-up changes**: "- **R4 — relay (the watcher's simulated telemetry link, `udp_link.py`).** It now parses every MAVLink frame (v1/v2; SITL" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:34`

### `R5` — 5 meanings

- **D17 V1/V2 heading-Replay checks**: "- **R5 (yaw):** UKF yaw error (`XUKF` against SIM) in the pinned cruise window: p95 ≤ 1.0°, max ≤ 2.0°" — `METHODOLOGY.md:7606`
- **Experiment H supervisor ruling items (2026-10-08)**: "**R5. A pre-registered prediction for drift and re-lock per estimator** (METHODOLOGY pre-registration)." — `docs/tag_hold_design.md:39`
- **rgs_check_tex roll-gain check criteria**: "| R5 | no new oscillation on any axis | cruise gyro-y rms ≤ 0.0108 and gyro-z rms ≤ 0.0200 (2× old); on every axis the largest spectral peak's ±0.5 Hz band rms **≤ 0.02 rad/s** | A single tone above 0.02 would be ≥ 2× all of the old ..." — `METHODOLOGY.md:4612`
- **rung-1 work items (minimal real-flight plan)**: "| R5 | **Firmware** for the board: pinned commit, clean worktree, build, archive, flash, rollback rehearsal (or flash stock 4.7.0) | 0.5–1 d | S1, S6 | build: once S1 is known | Low–medium. Bootloader and flashing quirks; the vehicle's ..." — `docs/minimal_real_flight_plan.md:362`
- **watcher bench re-run set-up changes**: "- **R5 — provenance.** Every session's `bench.log` records the repository HEAD and any uncommitted change under" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:39`

### `R6` — 2 meanings

- **Experiment H supervisor ruling items (2026-10-08)**: "**R6. Recording** (no full-rate forward-camera stream). The exact bag topics:" — `docs/tag_hold_design.md:41`
- **rung-1 work items (minimal real-flight plan)**: "| R6 | **Real-sensor parameter template** (§3.3) plus bench readback, `DSF` check and the compass arming check | 1.5 d | S1, S3, S4 | draft: yes | **Medium.** Sensor driver setup; compass calibration; the fence-origin question. |" — `docs/minimal_real_flight_plan.md:363`

### `R-a` — 2 meanings

- **M2r attempt validity criteria**: "- R-a: no BREACH and no crash disarm (FC text "Crash") from the arm to the next M1;" — `docs/handovers/2026-10-12_m2r_rerun.md:106`
- **rung-1 no-hardware TODO items (copter plan §3.2)**: "| R-a | **Pre-registration sign-off** (the user), then apply it: primary metric (evo -a SE(3) proposed), UKF record, drift segment, n, the Replay-fidelity tolerance (1 cm / 0.1°), the converter band, the timestamp rule. Mark the JSON final ..." — `docs/realflight_plan_copter.md:139` (+1 more source(s))

### `R-b` — 2 meanings

- **M2r attempt validity criteria**: "- R-b: the true horizontal excursion from the ALT_HOLD entry point ≤ 2.0 m before touchdown;" — `docs/handovers/2026-10-12_m2r_rerun.md:107`
- **rung-1 no-hardware TODO items (copter plan §3.2)**: "| R-b | **Merge `rung1-geometry`** (after the E5 ruling) and **install a fork Replay built from it** (one light `heavy.py` build; re-check SITL byte-identity). The installed Replay still hard-codes the 0.12/0.25 m levers and the old ..." — `docs/realflight_plan_copter.md:140`

### `R-c` — 2 meanings

- **M2r attempt validity criteria**: "- R-c: no "EKF Failsafe" FC text before touchdown (R2);" — `docs/handovers/2026-10-12_m2r_rerun.md:108`
- **rung-1 no-hardware TODO items (copter plan §3.2)**: "| R-c | **Capture-delay option in the port** (prereg §6: UKF at arrival − d_cap, like the FGO converter), default unchanged; Replay regression byte-identical | 0.5–1 d | not started; needs a ruling | **YES** for the UKF row as drafted (or ..." — `docs/realflight_plan_copter.md:141`

### `R-d` — 2 meanings

- **M2r attempt validity criteria**: "- R-d: `flow_bias.csv` shows "pass" mode for every message sent after the touchdown command (the runaway is EKF3's own," — `docs/handovers/2026-10-12_m2r_rerun.md:109`
- **rung-1 no-hardware TODO items (copter plan §3.2)**: "| R-d | **`XUKO` from a Replay run.** The prereg's proposed UKF record is `XUKO`, but Replay's logger does not emit FMT records for the UKF's messages (METHODOLOGY "Replay logging note"), and `ukf_shadow.csv` holds the horizon-time state. ..." — `docs/realflight_plan_copter.md:142` (+1 more source(s))

### `R-e` — 2 meanings

- **M2r attempt validity criteria**: "- R-e: the truth speed (forwarder, 0.5 s baseline) < 0.05 m/s at every `mocap_watch_vel.csv` sample in [t_on, t_end]" — `docs/handovers/2026-10-12_m2r_rerun.md:111`
- **rung-1 no-hardware TODO items (copter plan §3.2)**: "| R-e | **U4: initialise from `RNGFND1_GNDCLR`** when disarmed and `OutOfRangeLow` [correction 2026-10-12: a PORT rule, NOT "as EKF3 does": at 7bac20cbcc EKF3 pushes no range sample for `OutOfRangeLow` and falls back to baro; implemented ..." — `docs/realflight_plan_copter.md:143` (+1 more source(s))

### `S1` — 7 meanings

- **H stages**: "**S1 (EKF3 flies; `AHRS_EKF_TYPE 3`, closed loop on the tag-relative estimate):** the H profile of the design, 3" — `METHODOLOGY.md:10661` (+1 more source(s))
- **closed-loop safety criteria S1/S2 (no-heading miss-reading clause)**: "- **(S1)** no fast runaway before cruise +50 s (U2 as worded: no wall contact before +50 s);" — `METHODOLOGY.md:6966` (+1 more source(s))
- **robust-FGO heading test (plan step 2(a)) secondary decision rules**: "- **S1 (secondary):** on the plain-wall flights, the robust FGO accepts **fewer wrong headings** than the hard-gated" — `METHODOLOGY.md:9733`
- **rung-1 supervisor inputs (minimal real-flight plan §1)**: "| S1 | **FC board.** An H7 is assumed (Pixhawk 6X/6C, CubeOrange(+), Durandal, MatekH743, KakuteH7: all have hwdefs at the pinned commit [V]). | Firmware build target. EKF precision: on H7, `HAL_HAVE_HARDWARE_DOUBLE` is 1 ..." — `docs/minimal_real_flight_plan.md:44`
- **stage-3 safety gates (UKF-only closed loop)**: "| S1 | **SITL V1–V7** on the MAVLink camera-flow path with the exact source commit to be flown (SITL build) | each as pre-registered in the costing §6 table, plus the land detector trips after LAND (F2) in V3/V4. **V1 must show the D18 ..." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:197` (+1 more source(s))
- **watcher F6 LAND re-send stop conditions**: "- **S1:** a DO_SET_MODE ACK arrives;" — `docs/handovers/2026-10-12_watcher_f6_failsafe_b5_b8a.md:16`
- **watcher bench M2 set-up items**: "- **S1 — the watcher's checks.** Every primary watcher runs `--yaw-check require` AND `--vel-check require`." — `docs/handovers/2026-10-12_m2_full_bench.md:58`

### `S2` — 7 meanings

- **H stages**: "- **S2:** the UKF flies through the port. Gates first: port position-input equivalence test and a ground test. 3" — `docs/tag_hold_design.md:168`
- **closed-loop safety criteria S1/S2 (no-heading miss-reading clause)**: "- **(S2)** the estimator valid throughout: `XUKS.SS` `horiz_pos_rel` true from take-off to landing," — `METHODOLOGY.md:6967` (+1 more source(s))
- **robust-FGO heading test (plan step 2(a)) secondary decision rules**: "- **S2 (secondary):** the robust FGO's **maximum cross-track** ≤ the hard-gated FGO's on **≥ 8 of 12**." — `METHODOLOGY.md:9737`
- **rung-1 supervisor inputs (minimal real-flight plan §1)**: "| S2 | **Is the vehicle already flying?** Which firmware version is on it? Is it tuned? | 0 d of airframe work if it is already flying. Otherwise assembly and tune cost 3–6 d (`A1`+`A2`), which **breaks the calendar** (§6). |" — `docs/minimal_real_flight_plan.md:45`
- **stage-3 safety gates (UKF-only closed loop)**: "| S2 | **U10 Replay gate PASS** on the rung-1 logs | `docs/u10_replay_gate_band_draft.md` §4 | U-d0 |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:198`
- **watcher F6 LAND re-send stop conditions**: "- **S2:** an FC heartbeat after the first send shows LAND;" — `docs/handovers/2026-10-12_watcher_f6_failsafe_b5_b8a.md:17`
- **watcher bench M2 set-up items**: "- **S2 — H10 on every flight script.** Every bench flight script runs `--h10-guard`; the guard decision now calls the" — `docs/handovers/2026-10-12_m2_full_bench.md:65`

### `S3` — 5 meanings

- **H stages**: "- **S3:** the FGO flies through the node. Gates first: node-equivalence test and a ground test (D25 style). 3 flights." — `docs/tag_hold_design.md:170`
- **rung-1 supervisor inputs (minimal real-flight plan §1)**: "| S3 | **Flow sensor** (PMW3901-class on SPI = `FLOW_TYPE 2` Pixart; HereFlow = 6 DroneCAN; MTF-01/UPFLOW/MSP = 5/8/7 [V `AP_OpticalFlow.cpp:30`]) | `FLOW_TYPE`, `FLOW_ORIENT_YAW`, `EK3_FLOW_DELAY`, and the source of the derotation rate ..." — `docs/minimal_real_flight_plan.md:46`
- **stage-3 safety gates (UKF-only closed loop)**: "| S3 | **Bench P1–P10** on the flashed image | incl. **P5: arming refused with `AHRS_UKF_TFAIL` ≠ 0, normal AND forced**; P4 backends off = EKF3 | `docs/board_firmware_plan.md` §5 |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:199`
- **watcher F6 LAND re-send stop conditions**: "- **S3:** a heartbeat shows a **pilot mode** (ArduCopter `is_autopilot() == false`: STABILIZE, ACRO, ALT_HOLD, LOITER," — `docs/handovers/2026-10-12_watcher_f6_failsafe_b5_b8a.md:18`
- **watcher bench M2 set-up items**: "- **S3 — M1 in the harness.** Before every hover that follows a landing in the same FC boot: the carry home (A7/A9)," — `docs/handovers/2026-10-12_m2_full_bench.md:72`

### `S4` — 4 meanings

- **rung-1 supervisor inputs (minimal real-flight plan §1)**: "| S4 | **Rangefinder** (TF-Luna/TFmini = Benewake serial; VL53L1X = I²C) | `RNGFND1_TYPE`, `MIN`/`MAX`, `GNDCLR`. The minimum range matters: a TF-Luna's 0.2 m minimum means it reads out of range on the ground. |" — `docs/minimal_real_flight_plan.md:47`
- **stage-3 safety gates (UKF-only closed loop)**: "| S4 | **Forced invalidity → LAND** on the bench, then on the tether | `thesis_nav_check` text + mode LAND (reason EKF failsafe) within **0.1 s** of TFAIL (S-A2 (a) band); on the tether S-A1 (attitude ≤ 3° / yaw ≤ 5°) and S-A3 (disarm ≤ 40 ..." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:200`
- **watcher F6 LAND re-send stop conditions**: "- **S4:** a heartbeat shows a mode other than LAND and other than M0 (a change the watcher did not command);" — `docs/handovers/2026-10-12_watcher_f6_failsafe_b5_b8a.md:21`
- **watcher bench M2 set-up items**: "- **S4 — safety net.** If `ensure_watcher` does not see a confirmation within its 90 s cap and the watcher's ONLY" — `docs/handovers/2026-10-12_m2_full_bench.md:76`

### `S5` — 4 meanings

- **rung-1 supervisor inputs (minimal real-flight plan §1)**: "| S5 | **Mocap system** (OptiTrack/Vicon), rate, how recordings are exported, volume size, booking dates | The recorder (§4.5), the frame convention (OptiTrack streams Y-up by default), the flight profile size, and the calendar. |" — `docs/minimal_real_flight_plan.md:48`
- **stage-3 safety gates (UKF-only closed loop)**: "| S5 | **Aiding-loss timing S-A2b on the FC:** flow occluded → LAND | within **5.5 s of the last flow received by the FC** (pre-registered 2026-10-11) | ruling 2026-10-11 |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:201`
- **watcher F6 LAND re-send stop conditions**: "- **S5:** 5 sends have been made." — `docs/handovers/2026-10-12_watcher_f6_failsafe_b5_b8a.md:22`
- **watcher bench M2 set-up items**: "- **S5 — M3 in the harness.** The simulated pilot (A7b) disarms after **2 s** on the ground in LAND (was 4 s)." — `docs/handovers/2026-10-12_m2_full_bench.md:79`

### `S6` — 3 meanings

- **rung-1 supervisor inputs (minimal real-flight plan §1)**: "| S6 | **Firmware choice:** the pinned `7bac20cbcc` built from unmodified source, or the nearest stock release (`Copter-4.7.0`) | §2. |" — `docs/minimal_real_flight_plan.md:49`
- **stage-3 safety gates (UKF-only closed loop)**: "| S6 | **Watcher heartbeat withdrawn → LAND** within `FS_GCS_TIMEOUT` (MAVLink path; first real test) | as carded | W cards |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:202`
- **watcher bench M2 set-up items**: "- **S6 — sessions and order:** `ground`, `hoverA`, `hoverB`, `hoverC`, `f7`, `m2`; one simulation at a time, each" — `docs/handovers/2026-10-12_m2_full_bench.md:80`

### `S7` — 2 meanings

- **rung-1 supervisor inputs (minimal real-flight plan §1)**: "| S7 | **Floor:** can a plain (low-texture) sheet be laid in the volume? | Whether the degraded-sensing variable can be touched at all (§7). |" — `docs/minimal_real_flight_plan.md:50`
- **stage-3 safety gates (UKF-only closed loop)**: "| S7 | **RC override wins** over GUIDED/LOITER/LAND; F6 fixed (the watcher stops re-sending LAND once the FC shows LAND or a pilot mode) | B10 on the vehicle; F6 offline tests + 83 `realflight` tests | U-a |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:203`

### `shadow` — 3 meanings

- **shadow = EKF3 flies, estimator passive**: "- Launcher: `UKF=shadow` (EKF3 flies, the UKF in shadow); `UKF=1|shadow` with `HEADING=1` adds" — `METHODOLOGY.md:7644` (+1 more source(s))
- **shadow = a non-active estimator runs and logs**: "| 2 | One build (per vehicle) with `AHRS_EKF_TYPE` selection and shadow running; FGO off-board routes | UKF: yes. EKF3 already runs and logs while not active: `dsn_tex_r1` has `AHRS_EKF_TYPE=10` and 6654 `XKF1` rows from 2 lanes. FGO: (a) ..." — `docs/partC_onboard_feasibility.md:28`
- **shadow = simulator truth flies, estimator passive**: "**Shadow runs (simulator truth flies, `AHRS_EKF_TYPE 10`, 300 s cruise):**" — `METHODOLOGY.md:8070`

### `T1` — 4 meanings

- **M2-R bench criteria**: "**T1 (timing; independent of the runaway's duration; every valid attempt with a runaway):**" — `docs/handovers/2026-10-12_m2r_rerun.md:114` (+1 more source(s))
- **fail-closed watcher tests**: "- T1 (watcher not started): **refused to arm** ("REFUSING TO ARM: no watcher heartbeat"), no take-off. PASS." — `METHODOLOGY.md:10977` (+1 more source(s))
- **final results pack tables**: "| T1 | Headline claims before/after (36 rows) | CURRENT | rendered by `eval/figs_final_pack.py` from `docs/thesis/headline_claims_before_after.md` | all rows cited in its evidence column | 2/2 |" — `docs/thesis/final_results_pack_index.md:27` (+1 more source(s))
- **thesis tables**: "# Table T1. Which estimator wins where (scorecard of the restated verdicts)" — `docs/thesis/tables/T1_scorecard.md:1` (+1 more source(s))

### `T2` — 4 meanings

- **M2-R bench criteria**: "**T2 (no arm while |v| ≥ 0.2; every valid attempt with a runaway):**" — `docs/handovers/2026-10-12_m2r_rerun.md:121`
- **fail-closed watcher tests**: "- **T2 (watcher SIGKILLed during the hold): FAIL.** The heartbeat stopped at the kill, but the flight finished its" — `METHODOLOGY.md:10978`
- **final results pack tables**: "| T2 | Corrections summary (18 rows) | CURRENT | `docs/thesis/final_results_pack_corrections.md` (quotes METHODOLOGY, numbers.md, eval/results) | §6.1, §6.5, §6.6, §15, §16.2, §17, §18 | 1/1 |" — `docs/thesis/final_results_pack_index.md:28` (+1 more source(s))
- **thesis tables**: "# Table T2. Position error without and with the camera heading (textured floor)" — `docs/thesis/tables/T2_accuracy_heading.md:1` (+1 more source(s))

### `T3` — 2 meanings

- **M2-R bench criteria**: "**T3 (no LAND from M2):** 0 watcher "LAND command sent" and no BREACH from the disarm to the next M1." — `docs/handovers/2026-10-12_m2r_rerun.md:131`
- **thesis tables**: "# Table T3. Blank floor: position error after the loss of flow aiding" — `docs/thesis/tables/T3_blank_floor.md:1` (+1 more source(s))

### `T4` — 2 meanings

- **M2-R bench criteria**: "**T4 (after M1, arming allowed; once, at the end):** (e) a `GPS_GLOBAL_ORIGIN` with the sent lat/lon received after" — `docs/handovers/2026-10-12_m2r_rerun.md:133`
- **thesis tables**: "# Table T4. Closed loop at half speed: the final build of each estimator flying the vehicle" — `docs/thesis/tables/T4_closed_loop.md:1` (+1 more source(s))

### `U1` — 3 meanings

- **UKF-only closed-loop costing items**: "| U1 | **Board firmware** with `AP_NavUKF` | `#define AP_NAVUKF_ENABLED (CONFIG_HAL_BOARD == HAL_BOARD_SITL)` (fork `libraries/AP_NavUKF/AP_NavUKF.h:28-29`); no board build exists | §2 | SW 1–2 d (shared with 2(a)); HW 1 d | SW+HW |" — `docs/ukf_only_closed_loop_costing.md:65`
- **closed-loop no-heading flight PRIMARY criteria U1–U3**: "- **U1 (the backend flies the vehicle).** Arming, take-off to ≥ 1.8 m and entry into cruise under UKF" — `METHODOLOGY.md:6868` (+1 more source(s))
- **real-flight unknowns from the user (readiness §0)**: "| U1 | **Flight-controller board.** Part C §5 assumed an STM32H743 (Pixhawk 6X or CubeOrange). The UKF port uses `double` state and covariance, so the board needs a hardware double FPU (H7 class). | G1a, G1b, G2, C1 |" — `docs/real_flight_readiness.md:36`

### `U2` — 3 meanings

- **UKF-only closed-loop costing items**: "| U2 | **Real sensor geometry** in the port | fork-r1 `c25fa898`, on hold; **its Replay regression and `UKF_Equiv` not re-verified** (commit message) | merge after the regression | 0.5 d (needs one build slot) | SW (light build) |" — `docs/ukf_only_closed_loop_costing.md:66`
- **closed-loop no-heading flight PRIMARY criteria U1–U3**: "- **U2.** No wall contact before cruise **+50 s**. Basis: the fastest implied contact in the offline" — `METHODOLOGY.md:6870` (+1 more source(s))
- **real-flight unknowns from the user (readiness §0)**: "| U2 | **Vehicle type.** Copter, or ArduPlane QuadPlane in Q modes (Part C scope)? `thesis_nav_check` exists only in `ArduCopter/`. | G1b, G4, H10 |" — `docs/real_flight_readiness.md:37`

### `U3` — 3 meanings

- **UKF-only closed-loop costing items**: "| U3 | **Flow derotation input** (D18) | the port takes the driver's `rawGyroRates` (fork `AP_NavUKF.cpp:470`) | §3; decide, then (optionally) one port change | 0–1 d | SW |" — `docs/ukf_only_closed_loop_costing.md:67`
- **closed-loop no-heading flight PRIMARY criteria U1–U3**: "- **U3.** If contact occurs, it is on the **west wall inside [+83, +135] s**. Basis: the +98…+110 s" — `METHODOLOGY.md:6872` (+3 more source(s))
- **real-flight unknowns from the user (readiness §0)**: "| U3 | **Companion computer.** Pi 4 or Pi 5? RAM? Cooling? | A4, G8 |" — `docs/real_flight_readiness.md:38`

### `U4` — 2 meanings

- **UKF-only closed-loop costing items**: "| U4 | **Ground initialisation** when the rangefinder reads below its minimum | the port initialises only on a Good downward range above `RNG_MIN` (fork `AP_NavUKF.cpp:493,524`; fork-r1 607,641) | initialise from `RNGFNDn_GNDCLR` (plus the ..." — `docs/ukf_only_closed_loop_costing.md:68` (+2 more source(s))
- **real-flight unknowns from the user (readiness §0)**: "| U4 | **Downward camera and lens.** Interface: CSI/libcamera or USB/V4L2. Global or rolling shutter. | A3, D1, D3, D4 |" — `docs/real_flight_readiness.md:39`

### `U5` — 2 meanings

- **UKF-only closed-loop costing items**: "| U5 | **Yaw source** | the UKF has no compass input (`use_compass()` false, fork `AP_AHRS_UKF.h:27`); it uses the variance-gated zero-innovation pseudo-yaw | §4; a decision, not code | 0 d (nomag) | — |" — `docs/ukf_only_closed_loop_costing.md:69`
- **real-flight unknowns from the user (readiness §0)**: "| U5 | **Forward camera and lens**, if flown. | A6, D2, D6 |" — `docs/real_flight_readiness.md:40`

### `U6` — 2 meanings

- **UKF-only closed-loop costing items**: "| U6 | **Landing trigger** | `Copter::thesis_nav_check`, a `FAST_TASK` (fork `ArduCopter/Copter.cpp:136`, `ekf_check.cpp:337-358`), SITL safety (a) PASS; **the re-run on the corrected builds is still open (H1)** | §5 | 0 d code; H1 re-run ..." — `docs/ukf_only_closed_loop_costing.md:70`
- **real-flight unknowns from the user (readiness §0)**: "| U6 | **Rangefinder model and interface.** Serial/I²C to the FC, or read on the Pi. Minimum range. | A8, A9, C2 |" — `docs/real_flight_readiness.md:41`

### `U7` — 2 meanings

- **UKF-only closed-loop costing items**: "| U7 | **Failsafe parameter file** (real FC) | the SITL files exist (`closedloop_ukf.parm`); the real-FC template is rung-1 R6 | `AHRS_EKF_TYPE 12`, `AHRS_UKF_ENABLE 1`, `AHRS_UKF_TFAIL 0`, `FS_EKF_ACTION 1`, the GCS failsafe, battery, RC ..." — `docs/ukf_only_closed_loop_costing.md:71`
- **real-flight unknowns from the user (readiness §0)**: "| U7 | **Mocap system.** Vicon or OptiTrack. Rate. Streaming protocol (VRPN/NatNet). Time source (PTP/NTP). Capture-volume size. | F1, I3, I4, H9 |" — `docs/real_flight_readiness.md:42`

### `U8` — 2 meanings

- **UKF-only closed-loop costing items**: "| U8 | **Watcher** | G1–G11 built and merged (`realflight/watcher/`, 73 offline tests); SITL bench B0–B10 is 2(c); live mocap client F1 not built | §5 | F1 1–2 d (protocol per U7 mocap); B0–B10 in 2(c); hardware bench 1 d | SW + SIM + HW |" — `docs/ukf_only_closed_loop_costing.md:72`
- **real-flight unknowns from the user (readiness §0)**: "| U8 | **Airframe.** Frame size, prop guards, battery, RC transmitter and receiver, telemetry radio. | A1, A2, H5 |" — `docs/real_flight_readiness.md:43`

### `U9` — 2 meanings

- **UKF-only closed-loop costing items**: "| U9 | **SITL verification flights** with a SITL flow sensor | none with `SIM_FLOW` | §6 | harness 0.5 d; flights 1.5–2 d | SIM (after 16 Oct) |" — `docs/ukf_only_closed_loop_costing.md:73`
- **real-flight unknowns from the user (readiness §0)**: "| U9 | **UKF placement** (plan question 2): onboard the FC (the port) or on the Pi. | G1b, G10 |" — `docs/real_flight_readiness.md:44`

### `V0` — 2 meanings

- **FGO initial prior keys**: "| `V(0)` | 0.1 m/s about zero | stationary pre-arm; confirm from the bag |" — `FGO_DESIGN.md:732` (+1 more source(s))
- **UKF port input-path variants (step 3)**: "| V0: none (step-2 stream) | 1.4e-6 / 9.8e-6 / 5.0e-5 m | 2.3e-5° | 10,050 / 10,246 / 96 |" — `METHODOLOGY.md:6196`

### `V1` — 4 meanings

- **D17 heading-UKF verification sequence V1–V4**: "**V1 — Replay check on set (b)'s logs** (`cl_bcpp_tex_r1..r3`, `LOG_REPLAY 1`, EKF3 flew with the C++" — `METHODOLOGY.md:7594`
- **M2-R runaway-probe validity checks**: "- **Runaway detected (V1)** when the operator-link `LOCAL_POSITION_NED` 3-D |v| ≥ 0.2 m/s continuously for ≥ 1.0 s," — `docs/handovers/2026-10-12_m2_full_bench.md:126`
- **UKF port input-path variants (step 3)**: "| **V1: IMU path** (DAL INS deltas, 1 kHz-integrated, accumulated to EKF3's 12 ms target: 27,079 predicts, against 22,539 × 15 ms) | 0.21 / 0.91 / **3.15 m** | **2.28°** | 10,050 / 10,246 / 111 |" — `METHODOLOGY.md:6197`
- **UKF-only SITL verification flights V1–V7 (costing §6)**: "| V1 | UKF shadow, EKF3 flying, hover + small box | UKF initialises on the ground (also with the rangefinder min raised above the ground clearance, after U4); `XUKF` tracks truth |" — `docs/ukf_only_closed_loop_costing.md:261`

### `V2` — 3 meanings

- **D17 heading-UKF verification sequence V1–V4**: "**V2 — shadow run of the exact binary with heading** (EKF3 flies as in set (b); the UKF in shadow with" — `METHODOLOGY.md:7609`
- **UKF port input-path variants (step 3)**: "| **V2: flow gyro** (ArduPilot's arrival-window AHRS gyro, against the frame-averaged IMU gyro) | 0.09 / 0.41 / **1.47 m** | **1.08°** | unchanged |" — `METHODOLOGY.md:6198`
- **UKF-only SITL verification flights V1–V7 (costing §6)**: "| V2 | UKF flying (type 12), hover 60 s + box (`fly_trial.py` GUIDED local NED) | `HORIZ_POS_REL` throughout; no `thesis_nav_check` event |" — `docs/ukf_only_closed_loop_costing.md:262`

### `V3` — 5 meanings

- **D17 heading-UKF verification sequence V1–V4**: "**V3 — ground test with the UKF active and heading on** (`UKF=1 HEADING=1 GROUND_TEST=60`):" — `METHODOLOGY.md:7617`
- **M2-R runaway-probe validity checks**: "- **V3 (probe validity):** every operator-link |v| sample in the 0.3 s before the probe ≥ 0.2 m/s (the runaway still" — `docs/handovers/2026-10-12_m2_full_bench.md:134`
- **UKF port input-path variants (step 3)**: "| **V3: flow fused at arrival** (no delay buffer) | 0.28 / 1.34 / **4.80 m** | **3.56°** | unchanged |" — `METHODOLOGY.md:6199`
- **UKF-only SITL verification flights V1–V7 (costing §6)**: "| V3 | Safety (a): `AHRS_UKF_TFAIL` forced invalidity in hover | `thesis_nav_check` → LAND; touchdown drift within the pre-registered bound (earlier SITL: attitude-only drift 0.37–1.4 m) |" — `docs/ukf_only_closed_loop_costing.md:263`
- **stage-3 sorties**: "| **V3: first free hover, UKF flying** | verification | take-off, hover 30 s, one 1 m leg and back at ≤ 0.2 m/s, land (~1.5 min airborne) | shows the UKF holds and moves the vehicle with the right sign; nothing more | go/no-go for the ..." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:61`

### `V4` — 3 meanings

- **D17 heading-UKF verification sequence V1–V4**: "**V4 — the with-heading UKF set ×3** (`cl_ukf_b_tex_r1..r3`: `UKF=1 HEADING=1`," — `METHODOLOGY.md:7623`
- **UKF port input-path variants (step 3)**: "| V4: the port's range sampling (cm-quantised, ≥ 33 ms) | 0.02 / 0.09 / 0.32 m | 0.23° | 10,050 / 9,677 / 96 |" — `METHODOLOGY.md:6200`
- **UKF-only SITL verification flights V1–V7 (costing §6)**: "| V4 | Flow loss: `SIM_FLOW_ENABLE 0` mid-hover | LAND after the 5 s aiding timeout; drift recorded |" — `docs/ukf_only_closed_loop_costing.md:264`

### `V5` — 2 meanings

- **UKF port input-path variants (step 3)**: "| V5: V1 + V2 + V3 + V4 | 0.32 / 1.46 / **5.13 m** | **3.75°** | 10,050 / 9,677 / 111 |" — `METHODOLOGY.md:6201`
- **UKF-only SITL verification flights V1–V7 (costing §6)**: "| V5 | Rangefinder loss | Vertical hold for 15 s then … **pre-register the expected outcome** (LAND on hold height; behaviour after `VERT_HOLD_MS` [U]) |" — `docs/ukf_only_closed_loop_costing.md:265`

### `VOID` — 2 meanings

- **VOID = metric invalid as a measurement**: "**⚠️ VOID as an EKF3 measurement** — computed from `/ekf/pose`, which is ... simulator ground truth under `AHRS_EKF_TYPE=10`, not the EKF3 estimate." — `CLAUDE.md:493` (+1 more source(s))
- **VOID = run not a result**: "**Run 1 (`gt_heading_half`) VOID: an environmental failure, not a result.**" — `METHODOLOGY.md:7846`

### `X1` — 2 meanings

- **m2 full-bench cross-checks**: "- **In-flight tests:** no change expected. **New cross-check X1:** in every session, no watcher withdrawal whose" — `docs/handovers/2026-10-12_m2_full_bench.md:106` (+1 more source(s))
- **r1 scorer regression checks**: "- **X1:** cross-track with `XKF1` VE/VN given reproduces the stored `heading_share_restated.json` `xtrack_err_m` to" — `docs/handovers/2026-10-12_r1_scoring_items.md:57`

### `X2` — 2 meanings

- **m2 full-bench cross-checks**: "- **X2:** every M1 reboot's origin verified on the first try (else the session aborts)." — `docs/handovers/2026-10-12_m2_full_bench.md:109`
- **r1 scorer regression checks**: "- **X2:** the REGISTERED position rule equals the corridor's position-growth form (`ukf_shadow_replay_check.py`" — `docs/handovers/2026-10-12_r1_scoring_items.md:61`

### `⚑` — 2 meanings

- **numbers.md discrepancy flag**: "- **Discrepancies** between sources are flagged with ⚑ in the quantity cell and collected in the second-last" — `docs/thesis/numbers.md:25`
- **restatement-draft change flag**: "Legend: ⚑ = a verdict, ordering or wording change. Plain = a magnitude only." — `docs/thesis/final_restatement_draft.md:145`

## (c) PROPOSALS — NOT APPLIED

**These are PROPOSALS only. Nothing below has been applied, and no file, trial, result or branch has been renamed.**

They are intended for the thesis *text* (chapters, captions and the appendix code table). The repository's own documents and on-disk names stay as they are. Where a family is used in only one chapter, a first-use gloss may be enough in place of a rename.

### General rules (proposed)

1. **Qualify every bare code.** In the thesis, never write a bare one-letter-plus-number code. Each family gets a short, unique prefix, and the appendix maps each prefix back to the repo code (e.g. thesis "WG3" = repo "G3" in `docs/real_flights_plan.md:442-452`).
2. **Pick one owner per letter.** Keep the bare form only for the family the thesis cites most often:
   - **D** → the D-rulings
   - **T** → the thesis tables, written as "Table 1"…"Table 8"
   - **Fig.** → figures
   - **H-/P-/V-** → the hypothesis and prediction codes, which are already unique
   - **S0a…S3v2** → the H stages, written as "H-S1" etc.

   Every other family gets a prefix.
3. **Expand the dataset abbreviations at first use.** `dsn`, `ds`, `fwdc`, `fwdplainc`, `bcpp`, `rgs`, `lfs`, `tsx`, `hb` and `f4` have no written expansion (see §a). The thesis should define each once, in a dataset table, by its description. Do not invent an expansion of the letters.

### Proposed prefixes, by clashing family

| Repo code | Family | Proposed thesis label |
|---|---|---|
| G1–G6 | U10 replay-gate criteria | **RG1–RG6** (replay gate) |
| G1–G11 | mocap watcher gaps | **WG1–WG11** |
| G1a–G11 | real-flight readiness checklist | **RC-G1a…RC-G11** (and RC-A…, RC-B…, RC-C…, RC-D…, RC-E…, RC-F…, RC-H… for the other readiness rows) |
| G1–G8 | board firmware go/no-go | **BG1–BG8** |
| G1–G5 | heading ground-test gates | **HG1–HG5** |
| G1–G6 | backend ground-test gates (D9 P3 / D17 V3 / D19) | **GT-G1…** — or better **GTG1…**, since "GT" means ground truth |
| G1–G6 | H backend tag-input ground tests | **TG1–TG6** |
| G1–G4 | Experiment T / O / H per-flight gates | **T-G1…, O-G1…, H-G1…** |
| B1–B5 | closed-loop corridor criteria (predictions) | **CB1–CB5** |
| B0–B13 (+ lettered) | watcher bench tests | **WB0–WB13** (WB5a, WB10b, …) |
| B1–B10, B6b | rung-1 flight-card bench checks | **FCB1–FCB10** |
| B1–B5 | m2 full-bench amendment letters | **Am-B1…Am-B5** |
| A1–A10 | watcher-bench amendment letters | **Am-A1…Am-A10** |
| A1–A10 | rung-1 converter acceptance checks | **CV1–CV10** |
| A1–A3 | thesis appendix tables | **Table A1–A3** (always with the word "Table") |
| A1–A5 / A1–A4 | D12 work items / p1c calibration bands | **D12-A1…** / **CAL1–CAL4** |
| A1…D3 | Experiment T flight labels | write as **T_A r1** etc., matching the trial names |
| B1–B6 / L1–L2 / E1–E5 / C1–C4 / FE, FG, FN, FR | port equivalence rows and bands | **PE-B1…, PE-L1…, PE-E1…, PE-C1…** (keep FE/FG/FN/FR, which are unique) |
| B1–B3 | QuadPlane blockers | **QB1–QB3** |
| C0 | offline report | keep **C0** |
| C1–C4 | stage-3 criteria (draft) | **S3C1–S3C4** |
| C1–C3 | D25 FGO shadow criteria | **D25-C1…C3** |
| F1–F4 (F3b, F3c) | offline tests | **OT1–OT4** (OT3b, OT3c) or "F-test 1" |
| F1–F8 | watcher bench findings | **WF1–WF8** |
| F1–F8 / F01–F15 | thesis figures / pack figures | **Fig. 1–8** / **Pack Fig. 01–15** |
| (F1)–(F4) | D12/D19 backlog-fix options | **BF1–BF4** |
| T1–T8 | thesis tables | **Table 1–8** |
| T1, T2 | final-results-pack tables | **Pack Table 1/2** |
| T1–T4 | M2-R bench criteria | **M2R-1…M2R-4** |
| T1, T2 | fail-closed watcher tests | **FC1, FC2** |
| A–D | Experiment T conditions | **condition A–D** (never "T1…") |
| D1–D12 | rung-1 data-integrity checklist | **DI1–DI12** |
| D1–D3 | rung-1 calendar gates | **CG1–CG3** |
| D1 | watcher-bench deviation | **Dev1** |
| S1–S13 | stage-3 safety gates | **SG1–SG13** |
| S0a…S3v2 | Experiment H stages | **H-S0a…H-S3v2** |
| S1–S7 | rung-1 supervisor inputs | **SI1–SI7** |
| S1/S2 | closed-loop safety criteria; robust-FGO rules | **CS1/CS2**; **RS1/RS2** |
| S1–S6 / S1–S5 | M2 set-up items / F6 stop conditions | **M2S1…** / **F6S1…** |
| P1–P4 | forward-camera Phase 1/2 criteria | **PC1–PC4** |
| P1–P10 | board bench checks | **BB1–BB10** |
| P1–P3 | D9 UKF flight preconditions | **D9-P1…D9-P3** |
| P4 (as "Phase 4") | phase abbreviation | write **Phase 4** in full |
| R1–R15 | rung-1 work items | **RW1–RW15** |
| R1…Rn | result sorties | **sortie 1…n** |
| R1–R4 | plan-to-freeze risks | **Risk 1–4** |
| R1–R6 / R1–R5 | H ruling items / watcher re-run set-up | **HR1–HR6** / **WR1–WR5** |
| R1–R5 | rgs roll-gain criteria / D17 Replay checks | **RG-R1…** / **D17-R1…** |
| R-a…R-j / R-a…R-e | copter-plan TODO / M2r validity | **TODO-a…** / **M2R-a…** |
| U1–U3 | closed-loop no-heading criteria | **CU1–CU3** |
| U1–U9 | real-flight unknowns | **UQ1–UQ9** |
| U1–U15 (incl. U4, U10) | UKF-only costing items | keep **U4/U10** (widely cited); the others **U-item n** |
| V0–V5 / V1–V4 / V1–V7 / V1, V3, V1b | port input variants / D17 steps / costing flights / M2-R checks | **IV0–IV5** / **D17-V1…V4** / **CF1–CF7** / **M2R-V1…** |
| H1/H2 | OI-1 hypotheses | **OI1-H1/H2** |
| H1–H10 | readiness rows | **RC-H1…RC-H10** (keep "H10 guard" as a name) |
| H1–H3 | rung-1 scorer regression checks | **SR1–SR3** |
| X1/X2 | m2 cross-checks / r1 scorer checks | **M2X1/2** / **SRX1/2** |
| Q1–Q7 / Q2–Q6 | minimal-path questions / re-run open questions | **MQ1…** / **RQ2…** |
| L1–L3 / L1–L2 | G5.3 latency sub-criteria / port band L | **LS1–LS3** / **PE-L1…** |
| E1 | readiness flow-validity row | **RC-E1** |
| Phase 1 / Phase 2 | forward-camera phases vs project phases | **FC Phase 1/2** vs **project Phase 1/2** |

### Proposed wording for labels (thesis text only)

- **shadow**: always qualify who flies, e.g. "shadow (EKF3 flying)", "shadow (truth flying)" or "passive logging".
- **live / hindsight**: define once per experiment. For L, say "keyframe FGO (live)" / "keyframe FGO (LM hindsight)".
- **batch**: write "hindsight batch" for the whole-flight solve. Write "fixed-lag smoother" for `BatchFixedLagSmoother`.
- **VOID**: keep it for invalid metrics. Write "not a result" for runs.
- **FROZEN**: keep it for frozen results. Write "fixed (pre-registered)" for parameters.
- **⚑**: use it in one sense only, or replace it with "discrepancy" / "changed".
- **gt_ trial names**: write "ground-test runs (`gt_`)". Reserve "GT" for ground truth.
- **_half**: write "half real-time factor (RTF 0.5)".
- **_a/_b**: write "set (a) no heading / set (b) heading" for `cl_`. Write "safety variant (a)/(b)" for `H_safety_`.
- **_v2/_v3**: name the build in the text (e.g. "UKF port v2 (jitter-corrected)", "FGO node v3 (noise fix + gated yaw cap)"), not the suffix alone.
- **Undefined abbreviations** (EKF, ATE, RPE, SITL, GT, VP, LSD, HAGL, ExtNav, OF, FRD, FLU, NED/ENU, NEES, RTS): add a list of abbreviations to the thesis front matter. These abbreviations are standard, so expanding them is a writing task, not an inference about project meaning.
- **"as worded", "post hoc", "pre-registered", PENDING and CLOSED**: define each once in the methodology chapter's conventions section. "as worded" alone occurs 209 times across the in-scope docs (case-sensitive count) with no written definition.

