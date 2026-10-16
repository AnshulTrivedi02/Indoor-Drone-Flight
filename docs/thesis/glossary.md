# Project glossary: codes, tags, labels and abbreviations

*Built 2026-10-16 on branch `fwd-camera` at `27c8f6e`. This file is a reference only. Nothing in the repository, the results or `~/thesis_data` was renamed or edited to make it.*

**Companion file:** `docs/thesis/glossary_flags.md`. It lists (a) the terms that are used but never defined, (b) the codes with more than one meaning, and (c) proposed disambiguating names for the thesis text. None of the proposals has been applied.

## How to read an entry

Each entry has this form:

- `[family] "verbatim quote" — source`, where the source is either `file:line` or `pdf p.N`.

The **family** names the code series or meaning space the quote belongs to, for example "U10 replay-gate criteria" or "mocap watcher gaps". When one code carries several families, it means different things in different places. Such a term is marked **CONFLICT** and is listed in full in the flags file, §b.

Entries also carry these markers:

- ***(superseded)***: the source itself marks this meaning as replaced, renamed or void.
- ***(used, not defined here)***: a usage location. There is no definition at that location.

## Rules followed

1. **Every definition is a verbatim quote from a written source.** The sources are the repository docs at `fwd-camera` HEAD, the three PDFs (`pdftotext -layout`, with the page number given), and the following:
   - ArduPilot and the `~/ardupilot_ukf` fork source comments, for log messages;
   - `.parm` and `.sdf` header comments;
   - script docstrings;
   - batch `.conf` and `.json` files;
   - `README.txt` files under `~/thesis_data`.
2. **Every quote was checked mechanically.** The whitespace-normalised quote, or each " ... " fragment of it, was confirmed to appear at the cited line or a few lines after it. Records that failed were re-located or dropped. Long quotes are cut with " ...".
3. **No meaning is inferred from a name.** A term with no written definition is listed as UNDEFINED.
4. **For a meaning restated in many files,** the primary definition is given, plus at most one or two other sources.
5. **Paths:**
   - repository paths are relative to the repository root;
   - `~/` paths are on the workstation;
   - `ardupilot_ukf` source citations refer to the checked-out branch `ukf-jitter-fix`.

## Scope swept

**Documents:**

- `METHODOLOGY.md`, `PROGRESS.md`, `CLAUDE.md`, `FGO_DESIGN.md`
- all of `docs/*.md` and `docs/*.json`, including:
  - the pre-registrations (rung 1, U10 band, stage-3 draft, H10 guard)
  - the specifications, plans, readiness and costing documents
  - `decisions_queue.md`
- all of `docs/handovers/*`
- `docs/thesis/*.md`, `tables/*.md`, `figures_thesis/index.md` and `world_images/index.md`
- the three PDFs: `final_results_pack.pdf`, `thesis_figures_combined.pdf` and `worlds_combined.pdf`

**Names on disk:**

- `~/thesis_data`: `trials`, every archive (`trials_pre_rerun`, `pre_d15_trials`, `pre_final_trials`, `pre_final2_trials`), `closed_loop`, `wbench`, `batches`, `acceptance`, `validation`, `d8`, `d26` and the other top-level folders
- `batches/*.conf` and `batches/*/*.json`, including `batches/expO` and `batches/expT`, which exist only in the main checkout
- `eval/results/`, plus `eval/results_pre_*` in the main checkout
- `sim/worlds/*.sdf` and `sim/models/*`
- every `*.parm` file
- the scripts in `tools/` and `eval/`
- the git branches of `thesis_ws` and `~/ardupilot_ukf`
- the dataflash log messages the project uses

**Not covered:**

- The helper scripts archived under `eval/results/**/scripts` (about 70) are not listed one by one.
- The `worktree-agent-*` branches are summarised as one class.

**The trial-name grammar** (patterns with examples) is in the section "Trial-name grammar (summary)" below. The quoted entries behind it are in §2.


## Summary counts

Counts are of distinct terms (codes or labels). A term can appear in more than one category. "Conflicting" means the same code has more than one written meaning anywhere in the project (see `glossary_flags.md` §b).

| Category | Defined | Undefined | Conflicting |
|---|---:|---:|---:|
| 1. Experiments, studies, stages and phases | 111 | 0 | 13 |
| 2. Trial, dataset, batch and results naming | 205 | 23 | 15 |
| 3. Hypothesis, prediction, criterion, check, item and question codes | 214 | 11 | 71 |
| 4. Estimator, build, binary and branch labels | 87 | 18 | 7 |
| 5. Worlds and models | 78 | 1 | 0 |
| 6. Parameters, parameter files and log messages | 135 | 0 | 0 |
| 7. Metrics and units | 37 | 1 | 2 |
| 8. Rulings, standing rules and status labels | 84 | 13 | 21 |
| 9. Scripts (tools/ and eval/) | 258 | 10 | 0 |
| **Total (category rows summed)** | 1209 | 77 | 129 |

Distinct terms overall: 1209 defined, 77 undefined, 129 with conflicting meanings. Verified source records: 2168.


## Trial-name grammar (summary)

Abbreviation used in this summary only: "M NNNN" = `METHODOLOGY.md` line NNNN. Each meaning below has its full quoted entry, with its source, in §2 of this file.


Every meaning below is quoted, with its source file and line, in §2 of this glossary. The counts are
directory counts taken mechanically from the listings on 2026-10-16. "Undefined" means no text that
defines the token was found.

### 1. Open-loop corridor datasets: `<set>_<floor>_r<k>[_variant]`

| set | meaning (quoted source) | count in `trials/` (other archives) |
|---|---|---|
| `dsn_` | nomag comparison batch, `gnss_denied_nomag.parm`, `EK3_SRC1_YAW=0` (METHODOLOGY 864, 888) | 16: tex r1–r10, trans r1–r3, blank r1–r3 (pre_rerun 9, pre_d15 16, pre_final 16, pre_final2 15, d8 16, d15_port 10) |
| `ds_` | compass-active, `gnss_denied.parm`. SUPERSEDED for the three-way comparison (M 867, 878) | 9 (pre_rerun 9, pre_final 9) |
| `fwd_` | Phase 2 forward-camera, no ceiling. SUPERSEDED, sky visible (M 1845, 2362) | 9 |
| `fwdplain_` | Phase 2b plan only. Never flown; superseded by the ceiling datasets (M 2235, 2372) | 0 |
| `fwdc_` | ceiling worlds with textured walls, the upper bound (M 2382) | 9 |
| `fwdplainc_` | ceiling worlds with plain walls, the featureless case (M 2382) | 9 |
| `f4_<fwdc\|fwdplainc>_tex_r<k>` | plan step 2(a) fresh open-loop flights (`f4_robust.conf:1`) | 12 (r1–r6 × 2) |

- `<floor>`: `tex` / `trans` / `blank` = `corridor_textured` / `corridor_transition` / `corridor_blank` (`p1c_img_calibration_spec.md:14-16`; conf rows; `world_images/index.md:22-28`).
- `_r<k>`: repeat index (M 798, 10123). `r3b` is an unchanged re-fly of r3 (O_r3b, M 10401; H_s1far_r3b, M 12199).
- Variants: `_oi2` (IMU-stamp clones) and `_oi2dj` (the dejitter control), 3 + 3 dirs (M 1250, 1287).
- No source spells out the letters "ds", "dsn", "c" (ceiling) or "f4". Only the dataset descriptions exist.

### 2. Check flights: `p<N>…` (phase number)

- `p0_smoke_tex` (Phase 0)
- `p1_control_tex`, `p1_fwd_<floor>`, `p1diag_<…>`, `p1rtf_dsn_tex`, `p1plain_<floor>` (Phase 1; 13 dirs in total, the `p1_fwd_*` and `p1plain_*` ones SUPERSEDED)
- `p1c_<fwdc|fwdplainc>_<floor>` (Phase 1c; 6 dirs; the dataset token comes before the floor, and there is no `_r<k>`)
- `p1c_img_<floor>` (calibration flights; specification only, no trial directory)
- **Collision:** `_p2` and `_p3` in `ukf_shadow_sitl_tex_p2` and `ukf_groundtest_p3` are D9 preconditions P2 and P3 (M 6847). They are not phases, and not the Phase 1/2 criteria P2 and P3.

### 3. Closed loop: `cl_[<est>_]<set>_tex[_r<k>][_half][_v<N>]` (40 dirs in `trials/` and in `closed_loop/`)

- `<est>`:
  - absent = EKF3 flying
  - `ukf_`
  - `fgo_`
  - `cl_ekf3_tex` = the smoke test; `cl_ekf3_tex_2` = Check 2c, not a repeat
- `<set>`:
  - `a` = no heading (M 4841)
  - `b` = live camera heading (M 4842)
  - `bcpp` = set (b) re-flown with the C++ heading node (M 6527; "bcpp" itself is never expanded)
  - `b_robust` = Cauchy-robust FGO (M 9760)
- `_half` = the world `corridor_textured_half_fwdc`, with `real_time_factor` 0.5. This is half SIM speed, not half velocity (M 7829, 8024).
- `_v<N>` = re-flight version:
  - FGO: v2 = noise fix only, v3 = noise fix + gated yaw cap (`tools/run_fgo_refly.sh:2`)
  - UKF: v2 = jitter-corrected port (`tools/run_ukf_refly.sh:2`)

### 4. Ground tests and shadows

- **Ground tests:**
  - `gt_heading_{1,2,3,cpp,cpp2,half,half2,half_b}` (8 dirs)
  - `fgo_groundtest_half[_b]`
  - `ukf_groundtest_{p3,hdg_v3}`
  - `H_gt_{ukf,fgo}[_far]`
- **Collision:** `gt_` means ground TEST in these names (M 5737), but "GT" means ground truth everywhere else.
- **Shadows:**
  - `ukf_shadow_sitl_tex[_p2|_d5|_d15]`, where the suffixes are precondition P2, ruling D5 and ruling D15
  - `ukf_shadow_hdg_v2`
  - `fgo_shadow_sitl_tex{,2,3,4}`, where 2–4 are flight indices
  - `fgo_shadow_half_{a,a2,a3,b,b_robust}`, where a2/a3 are the first and second attempts of the D25 confirming shadow
  - `fgo_cpp_shadow_{i,ii,iii,ii_fix}`, the stage-5 configurations (i)–(iii)
  - `fgo_dev_smoke{1,2,3}`
  - 18 dirs in total
- **Collision:** `_v2`/`_v3` in `ukf_shadow_hdg_v2` and `ukf_groundtest_hdg_v3` are D17 validation STEPS V2/V3 (M 7664, 7691). They are not re-flight versions.

### 5. Room experiments

- **T:** `T_<A|B|C|D>_r<k>`, where the letter is the tag condition: A all 8 tags, B corners, C diagonal, D single (M 10118-10121).
  - 12 reported flights, plus 6 `_IMUGAP` and 2 `_ABORTED*` (20 dirs).
  - L replays `T_A_r*`, with output suffix `_t245` = cut at anchor + 245 s (`batches/final_rerun/L.jobs:1-2`).
- **O:** `O_r<k>`. 3 reported flights plus `O_r3_IMUGAP` (4 dirs, `tools/run_expO.sh`).
- **H** (Experiment H, 53 dirs in `trials/`):
  - `H_s0a`, `H_s0b`
  - `H_s1_r<k>`, `H_s1far_r<k>`, `H_s2[v2]_r<k>`, `H_s3[v2]_r<k>`
  - `H_gt_*[_far]`, `H_ifa_ekf3`
  - `H_safety_<ukf|fgo>_<a|b>[_vN|_abortN|_run1_failed]`, `H_safety_fgo_b2`, `H_safety_ekf3_ref`
  - `H_wtest_{kill,noarm}[_v1]`
- **Collisions:**
  - In `H_safety_*`, `_a`/`_b` are failure-injection variants (M 11288-11292), not heading on/off as in `cl_`.
  - Also not to be confused with: shadow run (a)/(b), which is heading off/on (M 8071-8072); and `_b` = re-run in `fgo_groundtest_half_b` and `gt_heading_half_b`.
  - `_v3` means the same port re-tested for the UKF safety runs, but noise fix + yaw cap for the FGO.
  - `abort2` is attempt 3.
  - `_v1` on `H_wtest_*` is undefined.
- **Tag checks:**
  - `tag_check1c/2/3` are the defined check flights (M 10051).
  - `tag_check1` and `1b` exist only as batch logs and are undefined.
  - `tagchar_h<NN>`: the conf pairs h15/20/25/30 with altitudes 1.5/2.0/2.5/3.0 (`tagchar.conf:3-6`). The "h" is never expanded.
  - `room_check`: the text says only "the room check flight" (M 10021); the directory name itself is undefined.
- **Static yaw sweep:** `phase3_yaw_sweep/<floorword>_<dataset>`, e.g. `textured_fwdc` or `blank_fwdplainc`. This breaks the usual grammar: the floor comes first as a full word, then the dataset (M 2787-2788; `yaw_sweep.sh:3`).
- **Experiment H profiles** (`batches/expH/*.json`): `s0a_sweep`, `s1_profile`, `s1_far_profile`, `wtest[_far]_profile`, `ifanchor_profile`, `safety_*` and `safety2_*`.
  - `safety2_*` are the 2 m-clearance-hold profiles (`run_h_safety.sh:18`); the "2" itself is never expanded.
  - `s0b_check.json` is never named in text.

### 6. Status suffixes and markers

- `_ABORTED[_N]`: the runner renames incomplete trials (`run_resumable_batch.sh:22-24`). 6 such dirs in `trials/`.
- `H_s0a_ABORTED` and `H_s0b_ABORTED` were named by hand.
- `_IMUGAP`: the original kept after an IMU-gap re-fly (M 10223; `tools/run_expT_refly.sh:4`). 7 dirs.
- `_abort1/_abort2`, `_run1_failed`: hand-named aborted H safety attempts (M 11439, 11650, 11654).
- Markers: `SUPERSEDED.txt` in the `fwd_*`, `p1_fwd_*`, `p1plain_*` and `p1diag_fwd_*` dirs; `ABORTED.txt`.

### 7. Watcher bench (`~/thesis_data/wbench`, VERIFICATION only)

- `wbench[<N>]_<session>_<YYYYMMDD_HHMMSS>`, 30 dirs: `wbench` 11, `wbench2` 6, `wbench3` 1, `wbench4` 11, `wbench5` 1.
  - `<N>` = bench run: 2 = re-run after F6, 3 = F7, 4 = full bench, 5 = M2-R (`tools/run_wbench.sh:2-7`).
  - Sessions: smoke, ground, hoverA/B/C, f7, m2, m2r. hoverA/B/C are defined by the bench tests they contain (handover 2026-10-12, lines 29-32).
  - 2026-10-11 extras: hoverA2, hoverA3, hoverB2, lua, b4a (handover 2026-10-11 table, lines 172-182).
- Driver logs: `run2_*.out` and `run4_*.out` are defined. `run_*.out` and the sub-suffixes `_b6b`, `_b10b`, `_r2`, `B2s`, `m2b` and `m2c` are undefined. 28 `.out` files in total.

### 8. Batch state names (`~/thesis_data/batches/<batch>`)

- `rerun2_main` and `rerun2_ds`: the second start of the consolidated re-run; `rerun_main` flew nothing and is SUPERSEDED.
- `final_<stage>` and `final2_<stage>`: the first final re-run and the FGO-only pass (`eval/final_rerun_pipeline.sh:23-24, 50-53`).
- `expT_<trial>`, `expT_refly_<trial>`, `expO_<trial>`.
- `hb_<trial>`: `half_b.sh` line 2 says "D19: half-speed with-heading sets"; "hb" is never expanded.
- `v4_<trial>` (D17 V4) and `half_a_*` ("D19: half-speed set (a) re-fly").
- Job batches named `<pipeline>_<stage>`: `rerun_phase3`, `d15_phase4`, `final_room_T`, and so on (by code).
- Set evaluation logs go to `eval_<tag>`.
- `eval_<tag>` (`run_set_eval.sh:6-7`), `d15_pipeline`, `rerun_pipeline`.
- Undefined: `clfa`, `clfb<k>`, `clfr<k>`, `clukf`, `fgt`, `gth*`, `fsha*`, `fshb*`, `fgodev*`, `p2_d15`, `p3`, `v2`, `v3`, `attrib_2026-10-10`.

### 9. Archives and eval naming

### Trial archives

| archive | content |
|---|---|
| `trials_pre_rerun` | 42 dirs: the pre-re-run copies of re-flown trials (README.txt:1) |
| `pre_d15_trials` | 41 dirs: pre-D15 UKF/FGO outputs (M 7130) |
| `pre_final_trials` | 167 dirs |
| `pre_final2_trials` | 152 dirs: FGO dirs only (`initial_sigma_audit.md:175`) |

### Sandboxes, folders and acceptance sets

- **Phase 5b sandboxes:** `phase5b`, `_rerun`, `_d15`, `_final`, `_final2`.
- **Folders named after rulings:** `d8`, `d26`, `d15_port`, `d17_v2` (usage only), `d17_v1` (undefined).
- **Other folders:**
  - `f1` (F1 calibration job list)
  - `sensitivity_yaw0_0p1` (0.1 rad initial-yaw sigma; `sens_yaw0.jobs:1-4`)
  - `h10_guard_check_side`
  - `acceptance/<set>`
- **Undefined:** `ukf_dtfix_check` (only "UKF-dt-check sandboxes" at M 4255-4256) and `validation/test1_yaw*`.

### `eval/results` naming

- Snapshots: `eval/results_pre_{rerun,d10,d15,final,final2}` (main checkout only), plus `expT_preD15fix`.
- Per-trial files: `closed_loop_<trial>.json` and `ground_test_<trial>.json`.
- Set-tagged files: `*_<tag>.json`, i.e. `flow_quality_`, `input_timing_`, `_evo` and `_score` (`run_set_eval.sh:6`).
- Re-run outputs: `rerun_<set>_*`.
- Per-experiment folders: `expH/`, `expL/`, `expO/`, `expT/`.

### 10. Legacy one-off trials (`iris_textured` era, 2026-07 to 2026-08)

- Defined: `stage_b_verify` and `stage_c_*` (metadata notes), `imu_rate_verify`, `ekf3_diag_60s`, `smoke_test` (CLAUDE.md), `nomag_corridor_baseline`, `vendor_verify_full`.
- Not auditable: `check1`, `check3`, `corridor_migration_test`, `verify_textured` (M 10004).
- `sweep_v<speed>` (6 dirs; metadata notes "velocity sweep"): the `p`-for-decimal encoding is undefined, and so is `v1p100`.
- Undefined: `geom_fix_verify`, `harness_test[2]`, `verify_nomag`, `vendor_verify`, `imu_verify2`, `nomag_test_long`.


## Contents

- [1. Experiments, studies, stages and phases](#1-experiments-studies-stages-and-phases)
- [2. Trial, dataset, batch and results naming](#2-trial-dataset-batch-and-results-naming)
- [3. Hypothesis, prediction, criterion, check, item and question codes](#3-hypothesis-prediction-criterion-check-item-and-question-codes)
- [4. Estimator, build, binary and branch labels](#4-estimator-build-binary-and-branch-labels)
- [5. Worlds and models](#5-worlds-and-models)
- [6. Parameters, parameter files and log messages](#6-parameters-parameter-files-and-log-messages)
- [7. Metrics and units](#7-metrics-and-units)
- [8. Rulings, standing rules and status labels](#8-rulings-standing-rules-and-status-labels)
- [9. Scripts (tools/ and eval/)](#9-scripts-tools-and-eval)

## 1. Experiments, studies, stages and phases


### `A`

- [Experiment T conditions (tag count)] "| A, all | `all` | 8 | ≈ 4–5 s |" — `METHODOLOGY.md:10118` — note: T condition; flights named T_<cond>_r<n>; table header at line 10116
- [Experiment T conditions (tag count)] "**Conditions (tag count, the controlled variable; a LIVE per-flight condition).** All 8 tags stay in the world; the" — `METHODOLOGY.md:10113` — note: conditions are the tag count, a live per-flight condition

### `attribution study`

- [named experiments] "### RULING (user, 2026-10-09): correction ATTRIBUTION study, added to the final re-run (after the main stages; it must not delay the freeze)" — `METHODOLOGY.md:12739`
- [named experiments] "- **Bags:** `dsn_tex_r1`–`r3` and one fwdc textured bag." — `METHODOLOGY.md:12740`
- [named experiments] "### RULING (user, 2026-10-10): the attribution study is STOPPED (not resumed); attribution wording in the thesis" — `METHODOLOGY.md:13169` — note: status only, definition unchanged: STOPPED by ruling 2026-10-10; partial results (27/64) at line 13269; resumable only on spare machine time (line 13336)

### `B`

- [Experiment T conditions (tag count)] "| B, corners | `0,1,2,3` | 4 | ≈ 10–11 s (**straddles EKF3's 10 s timeout**: its timeout state is logged per gap as a covariate) |" — `METHODOLOGY.md:10119` — note: T condition; flights named T_<cond>_r<n>; table header at line 10116

### `B0`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B0. Control: everything up, so arming succeeds.**" — `docs/real_flights_plan.md:479`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "- B0: control;" — `docs/handovers/2026-10-10_flow_rule_watcher_bench.md:87` — note: pre-registration summary B0–B10
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B0** | Ground. Watcher running (D1), deps alive. Flight script requests arming in GUIDED. | Script logs "Safety watcher confirmed before arming" AND the FC arms within 60 s; no other pre-arm failure. Recorded: the watcher's MAVLink heartbeat count from system ID 211. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:69`

### `B1-native`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B1-native** | Ground. Watcher started, confirmed, then SIGKILLed while disarmed; wait ≥ 4 s F; non-force MAVLink arm. Then restart the watcher. | The arm is refused with a GCS-failsafe pre-arm message; after the restart and re-confirmation, "GCS Failsafe Cleared" and the flight script can arm. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:73`

### `B1a`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B1a** | Ground. Watcher NOT started. Flight script requests arming. | Script logs "REFUSING TO ARM: no watcher heartbeat" AND no ARM event in the dataflash. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:70`

### `B1b`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B1b** | Ground. Watcher running, `flow_tracker` stub stopped. Flight script requests arming. | "REFUSING TO ARM: watcher not confirming (… bridge=0)" AND no ARM event. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:71`

### `B1c`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B1c** (G6) | Ground, watcher never started in this boot. (i) `ARMING_RUDDER` 2 (stock default): stick arm in STABILIZE via the RC model (throttle low, yaw right, 3 s). (ii) `ARMING_RUDDER` 0: same stick arm. (iii) a NON-force MAVLink arm from system ID 255. (iv) force-arm (param2 2989). | As §7.2: the FC REFUSES. ..." — `docs/handovers/2026-10-11_watcher_sitl_bench.md:72` — note: = §7.2 B1(c), real_flights_plan.md:491

### `B1c-Lua`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B1c-Lua** (G6 ii) | Ground. `watcher_arming_auth.lua` in SITL's `scripts/`, `SCR_ENABLE` 1, reboot; watcher with `--lua-auth`. (a) watcher never started: non-force MAVLink arm, and a stick arm with `ARMING_RUDDER` 2; (b) watcher confirmed: flight-script arm; (c) watcher SIGKILLed, wait ≥ 4 s F: non-force arm; (d) ..." — `docs/handovers/2026-10-11_watcher_sitl_bench.md:74`

### `B2a`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B2a** | Hover. SIGKILL the watcher (flight script alive). | LAND (or disarm) within **4.0 s W** of the kill. The layer that acted first is reported. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:75`

### `B2b`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B2b** (G5, G11) | Hover. SIGKILL the flight script (vehicle stays armed and holds), then SIGKILL the watcher; MAVProxy (255) keeps running. | FC GCS failsafe (ERR FAILSAFE_GCS, mode LAND) within **3.5 s F** of the watcher kill. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:76`

### `B3a`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B3a** | Hover. Drop all traffic on the watcher's link (both directions) at the relay; watcher running. | FC GCS failsafe within **3.5 s F** of the cut. (Expected also: the watcher withdraws on "FC link lost" without a LAND.) |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:77`

### `B3b`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B3b** | Hover. SIGSTOP the watcher; SIGCONT 1 s after LAND is seen. | LAND/disarm within **4.0 s W** of the SIGSTOP, AND after SIGCONT: no LAND or mode command from the watcher, no mode change other than the landing, no re-arm (10 s observed after disarm). |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:78`

### `B4a`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "- **B4a:** disarmed, watcher confirmed; the vehicle is carried out through each side face ((0, 3.5), (3.5, 0)," — `docs/handovers/2026-10-11_watcher_sitl_bench.md:149` — note: pre-registered under amendment A8

### `B4b`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B4b** (side face) | Hover. Flight script moves the hold point north at 0.5 m/s across y = 3 m. | Watcher logs BREACH within **0.1 s W** of the first mocap pose outside (its own track) AND LAND within **1.0 s W** of that pose; exactly ONE LAND decision. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:79`

### `B4b-top`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B4b-top** (G10) | Hover. Flight script climbs at 0.5 m/s through z = 3.0 m. | As B4b. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:80`

### `B4c`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "- **B4c:** disarmed, the vehicle is carried to roll 65° (dropped from 0.6 m). **Pass:** BREACH "tilt"." — `docs/handovers/2026-10-11_watcher_sitl_bench.md:154` — note: pre-registered under amendment A8

### `B4d`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "- **B4d** box geometry against real hold points and the capture volume." — `docs/handovers/2026-10-11_watcher_sitl_bench.md:103` — note: hardware-only; = §7.2 B4(d), real_flights_plan.md:528

### `B5a`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B5a** (re-worded, §7.2 B5 ruling 4) | as 2026-10-11 | Stale declared within **0.525 s W** of the last frame (0.5 s limit + one 0.025 s loop period), AND LAND within **1.0 s W** of the last frame; MAVLink heartbeat stopped; confirmation withdrawn. |" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:52` — note: re-worded row (0.525 s)
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] *(superseded)* "| **B5a** | Hover. Forwarder stops sending. | Stale declared within **0.5 s W** of the last frame (watcher log) AND LAND within **1.0 s W** of the last frame; heartbeat stopped; confirmation withdrawn. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:81` — note: SITL 0.5 s bound; re-worded to 0.525 s in the 2026-10-12 re-run (watcher_bench_rerun.md:52), following §7.2 B5 ruling 4

### `B5b`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B5b** | Hover. (1) freeze with tracked = 1 for 3 s; (2) tracked = 0 (untracked) from then on. | (1) no action (frozen with a tracking flag stays fresh, by design: an OBSERVATION, not a pass item); (2) treated as stale: LAND within **1.0 s W** of the first untracked frame. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:82`

### `B5b-noflag`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B5b-noflag** (re-worded) | as 2026-10-11 (A6) | Frozen declared within **0.525 s W** of the first frozen frame AND LAND within **1.0 s W** of it. States the case: the frozen fallback. |" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:53` — note: re-worded row (0.525 s)
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] *(superseded)* "| **B5b-noflag** | Hover with the forwarder in "no tracking flag" mode (tracked = −1) throughout; freeze (bit-identical poses) in the hover. | Stale (frozen) declared within 0.5 s of the freeze start AND LAND within **1.0 s W** of the freeze start. States which case applies: the frozen fallback. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:83` — note: SITL 0.5 s bound; re-worded to 0.525 s (watcher_bench_rerun.md:53)

### `B5c`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B5c** | Ground, disarmed. Confirmed watcher; stop the stream 3 s; restore. | Confirmation returns only after ≥ **2.0 s** of continuous fresh poses; no automatic action follows the restore. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:84`

### `B6` — **CONFLICT: 3 meanings** (see flags §b)

- [FGO C++ port equivalence rows] "| B6 (only if time allows) | `room_fgo_replay.py O_r1 --gnss`, live (+ batch as a separate row) | as B2 / B4 |" — `docs/fgo_cpp_port.md:191`
- [rung-1 flight-card bench checks] "| B6 | **Fence and EKF origin** (origin procedure re-written 2026-10-12, ruling 1) | ground station fence status; then the §1a origin procedure, steps 1–5 (every EKF3 core initialised FIRST, then the origin, then verified) | ~30 s | altitude fence enabled, FENCE_ALT_MAX as filed, no pre-arm fence error; the reported ..." — `docs/rung1_flight_cards.md:189`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B6. Wrong body / rigid-body ID (G3).**" — `docs/real_flights_plan.md:571`

### `B6a`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B6a** (stream level) | Ground. Forwarder sends body `other_body` (ID 2) only; flight script requests arming. | No confirmation (wrong_bodies counted), so arming refused. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:85`

### `B6b` — **CONFLICT: 2 meanings** (see flags §b)

- [rung-1 flight-card bench checks] "| B6b | **F7 yaw check** (ruling 2) | §1a steps 5–6 on the bench: record the tie; then turn the vehicle by hand to +90°, HOLD IT STILL ≥ 5 s, and turn it back (the FC sees the turn, so the check must keep passing) | ~1 min | \|FC yaw − (mocap heading + tie)\| ≤ 5° at rest before the turn, **while held at +90°** (this ..." — `docs/rung1_flight_cards.md:190` — note: conflicts with SITL watcher bench B6b (motion identity)
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B6b** (motion identity, D1) | Hover under the primary watcher. Observer watcher (system ID 212, `--identity require`). Manoeuvre: a commanded roll of 12° held 0.8 s, then a 90° yaw. Run 1: the observer gets the right body. Run 2: the observer gets a STATIC other body under the right name. | Run 1: observer ..." — `docs/handovers/2026-10-11_watcher_sitl_bench.md:86` — note: conflicts with rung-1 flight-card B6b (F7 yaw check)

### `B7` — **CONFLICT: 2 meanings** (see flags §b)

- [rung-1 flight-card bench checks] "| B7 | **Failsafes** | RC transmitter off for 2 s (props off, disarmed): RC failsafe message; battery failsafe values read back | ~1 min | messages as expected; values as filed |" — `docs/rung1_flight_cards.md:191`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B7. Clock and latency.**" — `docs/real_flights_plan.md:580`

### `B7a`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B7a** | All hover sessions: the watcher track's `t_rx_wall − t_mocap`. | median ≤ 50 ms, p99 ≤ 100 ms — on the FORWARDER → WATCHER path only (the true exposure latency is hardware-only). Plus an OBSERVATION: 150 ms added latency is logged and NOT acted on (staleness uses receipt time). |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:87`

### `B7b`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B7b** | Ground, disarmed: ≥ 10 LAND commands with the watcher's own `FcLink` (system ID 213), each followed by a GUIDED reset; plus every in-flight LAND of B4/B5/B9. | Command send → FC MODE event: **p99 ≤ 0.3 s W** over ≥ 10 commands. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:88`

### `B7c`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "- **B7c** mocap ↔ FC alignment: needs a real mocap clock and hand-rotation sync wiggles before arming and after" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:106` — note: hardware-only; = §7.2 B7(c), real_flights_plan.md:587

### `B8` — **CONFLICT: 2 meanings** (see flags §b)

- [rung-1 flight-card bench checks] "| B8 | **Log completeness** | download the bench log; run §7 items D2–D5 on it | ~5 min of checking; the log is the B1–B7 period | LOG_REPLAY records present; `DSF.Dp` = 0 |" — `docs/rung1_flight_cards.md:192`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B8. Estimator invalid → FS_EKF_ACTION path (the open item in §7).** Per flying estimator, armed (props off," — `docs/real_flights_plan.md:592`

### `B8a`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B8a** | Hover, EKF3. Aiding loss (amendment A5): SIGKILL `flow_bridge.py` (the flow stops reaching the FC). Watcher heartbeat and deps untouched; 20 s observed, then flow restored and landed. | Report-only (§7.2). Expected from `H_safety_ekf3_ref`: EKF3 raises NO failsafe and keeps a dead-reckoned position. If the ..." — `docs/handovers/2026-10-11_watcher_sitl_bench.md:89`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B8a** (REPEATED, harness fault; expected outcome RE-REGISTERED) | As the first run: `hoverB`, `iris_textured`, the same ±3 m box, hover profile take-off 1.5 m / hold 10 s / hold 35 s / land, GUIDED; `flow_bridge.py` (not a watched dependency) SIGKILLed 1 s after the hold start; watcher heartbeat and dependencies ..." — `docs/handovers/2026-10-12_watcher_bench_rerun.md:55` — note: repeated, expected outcome re-registered

### `B8b`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "- **B8b/B8c** (UKF / FGO ports): rung 1 flies EKF3; the port paths are item 2d (`H_safety_*` re-tests)." — `docs/handovers/2026-10-11_watcher_sitl_bench.md:108` — note: B8b/B8c share this line; = §7.2 B8(b) UKF port, real_flights_plan.md:613

### `B8c`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "- **B8b/B8c** (UKF / FGO ports): rung 1 flies EKF3; the port paths are item 2d (`H_safety_*` re-tests)." — `docs/handovers/2026-10-11_watcher_sitl_bench.md:108` — note: B8b/B8c share this line; = §7.2 B8(c) FGO port, real_flights_plan.md:620

### `B9` — **CONFLICT: 2 meanings** (see flags §b)

- [rung-1 flight-card bench checks] "| B9 | **Sync wiggle in the first acceptance log** (2026-10-12) | before B8's download, with the vehicle disarmed on the bench: a sync wiggle (~5 s, sharp rotations about all three axes, \|ω\| > 2 rad/s); then run `eval/bin2fgo_accept.py` on the B8 log | ~1 min: the wiggle is what A5 tests against | the converter's A5 ..." — `docs/rung1_flight_cards.md:193`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B9. Dependency loss (`--dep-loss land|stop`; G7, G8).** Armed. For each watched dependency in turn (flow tracker," — `docs/real_flights_plan.md:630`

### `B9-hang`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B9-hang** (observation) | Hover. The `flow_tracker` stub keeps beaconing but freezes its progress counter. | No pre-registered bound (§7.2 gives none); expected: withdrawal ~2 s (progress timeout) + tick, then LAND. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:93`

### `B9a`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B9a** | Hover, `--dep-loss land`. SIGKILL (1) the `flow_tracker` stub (in-process beacon), (2) the `flow_bridge` stub (proc sidecar). One hover each. | Watcher withdraws within **1.5 s W** of the kill and stops its heartbeat AND LAND within **2.5 s W** of the kill. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:90`

### `B9b`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B9b** | Hover, `--dep-loss stop`. SIGKILL the `flow_tracker` stub. | As B9a (stop must mean LAND, G8). |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:91`

### `B9c`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B9c** | Hover. SIGSTOP (1) the `flow_tracker` stub, (2) the `flow_bridge` stub. | Detected and handled as B9a (same bounds). |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:92`

### `B9d`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B9d** | = B1b. | As B1b. |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:94` — note: defined only as "= B1b"

### `B10` — **CONFLICT: 2 meanings** (see flags §b)

- [rung-1 flight-card bench checks] "| B10 | **M2 EKF velocity check** (2026-10-12) | §1a step 7 on the bench, vehicle still: read `LOCAL_POSITION_NED` vx, vy, vz on the GCS for 5 s; then carry the vehicle by hand ~1 m and set it down; read again for 5 s | ~1 min | \|v\| < 0.2 m/s at rest before and after the carry; the at-rest maximum on the sheet ..." — `docs/rung1_flight_cards.md:194`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B10. RC override takes precedence.** Armed, GUIDED:" — `docs/real_flights_plan.md:644`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] *(superseded)* "- *Previous wording (kept verbatim):* "*Pass:* the FC mode changes within **0.3 s**, and the flight script's GUIDED" — `docs/real_flights_plan.md:650` — note: B10(a) previous pass wording, re-worded 2026-10-12 (ruling 3 on wbench4)

### `B10a`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B10a** | Hover in GUIDED. RC mode switch to ALT_HOLD; later STABILIZE briefly, then ALT_HOLD. | FC mode changes within **0.3 s W** of the RC change, AND the flight script's GUIDED setpoints have no effect afterwards (no mode change back; vehicle holds). |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:95` — note: "vehicle holds" wording; §7.2 B10(a) re-worded 2026-10-12 (real_flights_plan.md:646)

### `B10b`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B10b** | Hover in ALT_HOLD (pilot). In turn: (1) watcher SIGKILL; (2) a NEW watcher confirms, then dependency loss (SIGKILL `flow_tracker`); (3) aiding loss (A5: SIGKILL `flow_bridge.py`). | GCS failsafe and EKF failsafe make NO mode change; the watcher and the flight script send at most ONE LAND (latched); if ..." — `docs/handovers/2026-10-11_watcher_sitl_bench.md:96`

### `B10c`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "| **B10c** | Ground, armed (GUIDED, `DISARM_DELAY` 0). `SIM_RC_FAIL 1` (no pulses). | The configured `FS_THR_ENABLE` 3 action: disarm on the ground (a MODEL of a receiver failsafe only). |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:97`

### `B11`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B11. F7: estimator yaw disagrees with the mocap → arming refused (the watcher yaw check).** *(Added 2026-10-12 under" — `docs/real_flights_plan.md:667`

### `B12`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B12. M2: EKF velocity not settled, or the vehicle not still → arming refused (the watcher velocity check).** *(Added" — `docs/real_flights_plan.md:714`

### `B13`

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B13. X1 timing on the real links: the watcher's own view of the FC against the GCS link's.** *(Added 2026-10-12" — `docs/real_flights_plan.md:746`

### `C`

- [Experiment T conditions (tag count)] "| C, diagonal | `0,2` | 2 | ≈ 22–25 s |" — `METHODOLOGY.md:10120` — note: T condition; flights named T_<cond>_r<n>; table header at line 10116

### `C0`

- [offline tests] "**C0 — FGO vs UKF with heading, post-D15 (REPORT, no decision rule).**" — `METHODOLOGY.md:7892`
- [offline tests] "| **C0 (FGO vs UKF with heading, textured)** | **FGO lower on all 6** (accepted, restatement ruling 3): 3/3 `fwdc` (0.06 vs 0.13 m) and 3/3 `fwdplainc` (0.09–0.22 vs 0.15–0.25 m; **margin 0.03–0.06 m**). The first final re-run's reversal ("UKF lower on 3/3 `fwdplainc`", FGO 43 m) was the plain-wall divergence, now ..." — `docs/thesis/numbers.md:298` — note: result row

### `Check 2b`

- [other named checks and studies] "### Check 2b — open-loop check flight with a sideways step: pre-registration (before flying)" — `METHODOLOGY.md:4190`
- [other named checks and studies] "**Flight** `lfs_check_tex`. It is not part of any dataset." — `METHODOLOGY.md:4192`

### `consolidated re-run`

- [offline re-runs] "## CONSOLIDATED RE-RUN (user ruling, 2026-09-29): both baseline corrections accepted" — `METHODOLOGY.md:3774`
- [offline re-runs] "- Batched corrections (i) EKF3 `FLOW_POS_Z = 0.25` and (ii) UKF accumulated dt are" — `METHODOLOGY.md:3777`

### `D`

- [Experiment T conditions (tag count)] "| D, single | `0` | 1 | ≈ 48–52 s |" — `METHODOLOGY.md:10121` — note: T condition; flights named T_<cond>_r<n>; table header at line 10116

### `dsn baseline`

- [named experiments] "`gnss_denied_nomag.parm` (`EK3_SRC1_YAW=0`, compass unused) — the **`dsn_*`" — `METHODOLOGY.md:864` — note: dsn_* batch = 3 corridor worlds × 3 repeats under gnss_denied_nomag.parm; extra repeats dsn_tex_r4..r10 at line 6225
- [named experiments] "| **No-yaw comparison params (used by `run_trial.sh` for all `dsn_*` and forward-camera datasets)** | `~/thesis_ws/gnss_denied_nomag.parm` (+ `sim_noise.parm`) — the three-way comparison config (METHODOLOGY "Comparison dataset — nomag") |" — `CLAUDE.md:67` — note: CLAUDE.md Key Paths: dsn_* and forward-camera datasets use gnss_denied_nomag.parm

### `dsn_tex additional repeats`

- [other named checks and studies] "### PRE-REGISTRATION — additional `dsn_tex` repeats: the EKF3-vs-FGO ordering and the `dsn` noise floor (flown AFTER closed-loop sets (a) and (b))" — `METHODOLOGY.md:5638`
- [other named checks and studies] "- **Flights.** `dsn_tex_r4 … dsn_tex_r10`: 7 new repeats. Same settings as the re-flown batch:" — `METHODOLOGY.md:5640`

### `Experiment H`

- [named experiments] "# Experiment H — marker-relative position holding (supervisor item 3): DESIGN and DRAFT pre-registration" — `docs/tag_hold_design.md:1` — note: no written expansion of the letter found; the entry gives the written description of the experiment; H = marker-relative position holding (supervisor item 3)
- [named experiments] "### Experiment H (marker-relative position holding): pre-registration of S0 and S1 (written before any H flight)" — `METHODOLOGY.md:10623`

### `Experiment L`

- [named experiments] "### Experiment L: pre-registration (written before any L result; the V-L replays were started minutes earlier, no output read)" — `METHODOLOGY.md:10452` — note: no written expansion of the letter found; the entry gives the written description of the experiment
- [named experiments] "**Question.** With AprilTags at UNKNOWN positions, does a keyframe FGO that re-identifies tags (loop closure) bound" — `METHODOLOGY.md:10454`
- [named experiments] "- **L (tags at unknown positions; keyframe FGO with loop closure, iSAM2 whole history):**" — `PROGRESS.md:23` — note: short description: tags at unknown positions, loop closure

### `Experiment O`

- [named experiments] "### Experiment O: pre-registration (written before any O flight)" — `METHODOLOGY.md:10290` — note: no written expansion of the letter found; the entry gives the written description of the experiment
- [named experiments] "**Question.** In an outdoor → indoor → outdoor flight with GNSS outside only, are the live indoor errors of the three" — `METHODOLOGY.md:10292`
- [named experiments] "- **O (outdoor → indoor → outdoor, GNSS switched at the entrance; 3 flights):**" — `PROGRESS.md:18` — note: short description: outdoor → indoor → outdoor

### `Experiment T`

- [named experiments] "### Experiment T: pre-registration (written before any T flight; hypotheses, conditions, metrics and criteria fixed here)" — `METHODOLOGY.md:10100` — note: no written expansion of the letter found; the entry gives the written description of the experiment
- [named experiments] "**Question.** With absolute fixes from AprilTags at known positions, does the FGO's hindsight reconstruction gain over" — `METHODOLOGY.md:10102`
- [named experiments] "- **T (AprilTags at known positions; `room_tags`, 5 laps, 4 tag densities × 3 repeats):**" — `PROGRESS.md:10` — note: short description: AprilTags at known positions

### `F3b`

- [offline tests (F-tests)] "**F3b:** the nonlinearity test, properly designed; pre-registered below before running." — `METHODOLOGY.md:8445`
- [offline tests (F-tests)] "### PRE-REGISTRATION — F3b: the nonlinearity test, properly designed (offline, bounded; written before running)" — `METHODOLOGY.md:8485`

### `F3c`

- [offline tests (F-tests)] "spread), **not** as evidence about convergence speed. F3c tests convergence speed inside the UKF's valid range." — `METHODOLOGY.md:8925`
- [offline tests (F-tests)] "### PRE-REGISTRATION — F3c: convergence speed inside the UKF's valid range (offline, one batch; written before running)" — `METHODOLOGY.md:8943`

### `F4` — **CONFLICT: 6 meanings** (see flags §b)

- [D12/D19 take-off backlog fix options] "- (F4) EKF3 flies the take-off and the FGO takes over once its lag is inside budget. The flight is then" — `docs/d12_fgo_backend_report.md:43` — note: CONFLICT: backlog-fix option, not the offline test
- [D12/D19 take-off backlog fix options] "- (F4) EKF3 flies the take-off (not "the FGO flying", not recommended)." — `docs/decisions_queue.md:166`
- [naming collisions] `F4 (watcher finding)` "- F4: `fly_trial.connect()` latches onto the first heartbeat it sees (mode-mapping risk); fixed in the bench driver" — `METHODOLOGY.md:13611` — note: same token "F4"/"f4" as the f4_ trial prefix but a different meaning (watcher bench finding)
- [offline tests (F-tests)] "| 2(a) (F4) | `f4` | `batches/f4_replays_usable.jobs` (30 jobs, unchanged) + `f4_eval.py test cauchy:2.385 --trials <10 usable>` | none | the `--trials` order was unrecorded; it was rebuilt from `~/thesis_data/batches/f4_eval.txt`. Bags packed (handled). |" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:134` — note: F4 = plan step 2(a), the robust-weighting confirmation (pre-registered in METHODOLOGY "plan step 2"); f4_* flights
- [offline tests (F-tests)] "### PRE-REGISTRATION — plan step 2: robust-weighting confirmation (written in full before any flight; starts from exact noise parity, D27)" — `METHODOLOGY.md:9692` — note: the METHODOLOGY pre-registration does not itself use the label F4
- [offline tests (F-tests)] "| 91 | 2(a) (F4) orderings: FGO_robust − FGO_hard | f4_fwdc_tex_r2 yaw_max_deg | -0.165 → 0.002 (DIRECTION) | REAL (not interpretable as ordering) | On fwdc both arms now ~0.3° / 1–13 cm and equal to within 0.05° / 5 cm; the sign of a sub-noise difference. |" — `docs/thesis/final_restatement_draft.md:577`
- [real-flight readiness items] "| F4 | Watcher bench tests: watcher not started → no arm; watcher killed in a tethered hover → land | not built | a, b | **Being pre-registered now by another agent** (ruling 2026-10-10 item 4). The SITL analogue passed (T1/T2 in `tools/test_watch_failclosed.sh`). | 0.5 d bench, plus 0.5 d in a tethered hover (H8) | ..." — `docs/real_flight_readiness.md:118` — note: CONFLICT: readiness item (mocap watcher chain), not offline test or finding
- [thesis figures] "| F4 blank floor (pack F06) | `blank_behaviour.json`, +10/+30/+60 s, 11 flights per estimator; the EKF3 box gives the reason (invalid for the whole cruise, 0 valid airborne flow frames, origin output not scored) | 6/6 | **km-scale runaway next to metres: the axis is CUT at +60 s; the end-of-cruise values (UKF 29–40 ..." — `docs/handovers/2026-10-15_thesis_figures.md:25` — note: 2026-10-15 set
- [thesis figures] *(superseded)* "**Revision 2026-10-16.** F1 (`F1_scorecard`) became table T1; F3 (`F3_accuracy_without_and_with_heading`) became table T2; F4 (`F4_blank_floor_flow_loss`) became table T3; F8 (`F8_H_tag_loss_drift`) became table T5. The old figure files are removed from this folder; they remain in the git history (commit `7778cd6`, ..." — `docs/thesis/figures_thesis/index.md:5` — note: F4 became table T3 (e202552)
- [watcher bench findings] "- **F4: `fly_trial.connect()` takes the FIRST heartbeat it sees.** With other MAVLink senders on the link (MAVProxy, and" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:378` — note: CONFLICT with offline test / readiness item of the same number
- [watcher bench findings] "- F4: `fly_trial.connect()` latches onto the first heartbeat it sees (mode-mapping risk); fixed in the bench driver" — `METHODOLOGY.md:13611`

### `F6a`

- [watcher bench tests] "| **F6a** (NEW, in flight, LAND ACKed) | Standard hover in GUIDED. The flight script is SIGKILLed 2.0 s before the injection (as B2b), so the watcher is the ONLY process that can command LAND (`fly_trial.py`'s as-is WatcherLost LAND in GUIDED is the open H10 item, not F6). Throttle stick centred (1500). Injection: ..." — `docs/handovers/2026-10-12_watcher_bench_rerun.md:57`
- [watcher bench tests] "- **F6 in flight:** F6a (ACK delivered) and F6b (ACK stripped, heartbeats held 0.6 s) each sent exactly ONE LAND, and" — `METHODOLOGY.md:13876`

### `F6b`

- [watcher bench tests] "| **F6b** (NEW, in flight, LAND UNACKNOWLEDGED) | As F6a, plus: the relay strips every COMMAND_ACK FC → watcher (`ack_strip on`) and holds FC HEARTBEATs to the watcher for **0.6 s** after the watcher's LAND frame (`hb_hold 0.6`), so the pilot's ALT_HOLD (at +0.33 s) reaches the FC before any heartbeat showing LAND ..." — `docs/handovers/2026-10-12_watcher_bench_rerun.md:58`

### `F6c`

- [watcher bench tests] "| **F6c** (NEW, ground, lost command → re-send) | Ground, disarmed, GUIDED, watcher confirmed. The relay drops the watcher's FIRST DO_SET_MODE(LAND) frame (`drop_land_once`); FC heartbeats keep flowing. Injection: SIGKILL of the `flow_tracker` stub. | Exactly **2** sends; send 2 at **0.30–0.60 s W** after send 1 (rule ..." — `docs/handovers/2026-10-12_watcher_bench_rerun.md:59`

### `FGO-only re-run`

- [offline re-runs] "- **LAUNCHED:** the FGO-only pipeline pass at `4fb721f` (13:02), with `FINAL_FGO_ONLY=1 FINAL_SENS_YAW0=1" — `METHODOLOGY.md:13330`

### `final2`

- [offline re-runs] "`eval/results/final_old_vs_new.md` (first final re-run), `eval/results/final2_old_vs_new.md` (FGO-only re-run)." — `docs/thesis/headline_claims_before_after.md:8` — note: final2 = the FGO-only (second final) re-run
- [offline re-runs] "- New state `final_rerun2`, snapshot `results_pre_final2`, archive `pre_final2_trials` (331 dirs)." — `METHODOLOGY.md:13332` — note: state final_rerun2, snapshot results_pre_final2, archive pre_final2_trials

### `final consolidated re-run`

- [offline re-runs] "### RULINGS (user, 2026-10-09): the final consolidated re-run pipeline (`eval/final_rerun_pipeline.sh`)" — `METHODOLOGY.md:12691` — note: the first final re-run (pipeline eval/final_rerun_pipeline.sh); completed at line 12768

### `H10 guard check`

- [H10 guard verification] "# H10 guard verification flight `h10_guard_check`: PRE-REGISTRATION (2026-10-12)" — `docs/h10_guard_check_prereg.md:1`

### `M2-R`

- [other named checks and studies] "### 1.3 New test M2-R (session `m2`; the SITL counterpart of B12; NOT a hardware test)" — `docs/handovers/2026-10-12_m2_full_bench.md:111`

### `Part 1`

- [closed-loop Part 1/Part 2 and sets (a)/(b)/(c)] "### Part 1 — live heading bridge: built and tested offline (no simulation)" — `METHODOLOGY.md:4717` — note: closed-loop Part 1: live heading bridge

### `Part 2`

- [closed-loop Part 1/Part 2 and sets (a)/(b)/(c)] "### Part 2 — revised pre-registration at the ruled 5.00° EKF3 yaw σ (before any closed-loop flight)" — `METHODOLOGY.md:4927`
- [closed-loop Part 1/Part 2 and sets (a)/(b)/(c)] *(superseded)* "### Part 2 — "flying well": pre-registration — DRAFT, SUPERSEDED BEFORE FLYING (see "Part 2 — revised")" — `METHODOLOGY.md:4831` — note: draft superseded before flying; revised at line 4927

### `Part C`

- [Part C onboard feasibility] "# Part C: Feasibility of running the UKF and FGO onboard as ArduPilot estimators" — `docs/partC_onboard_feasibility.md:1`
- [Part C onboard feasibility] "## Part C — onboard feasibility investigation (2026-09-29): result" — `METHODOLOGY.md:3071`

### `Phase 0`

- [forward-camera workstream phases] "Branch `fwd-camera`, from `master` at `5b14ce3`. **Phase 0 (a), the reproducibility" — `PROGRESS.md:445` — note: Phase 0 = (a) reproducibility gate + (b) smoke test
- [forward-camera workstream phases] "**Phase 0 smoke test (b) — acceptance, pre-registered before flying.** One new" — `METHODOLOGY.md:136` — note: Phase 0 smoke test (b) acceptance

### `Phase 1` — **CONFLICT: 2 meanings** (see flags §b)

- [forward-camera workstream phases] "### Phase 1 plan and confound-check acceptance (pre-registered before flying)" — `METHODOLOGY.md:1428` — note: confound-check flights p1_control_tex / p1_fwd_{tex,blank,trans}
- [forward-camera workstream phases] "Four flights, back to back, in one session, all at the `dsn_*` settings (0.5 m/s," — `METHODOLOGY.md:1430` — note: body of the Phase 1 plan
- [project phases (CLAUDE.md / PROGRESS.md)] "### Phase 1 checklist" — `PROGRESS.md:580` — note: project-level Phase 1, defined only by enumeration: the task checklist that follows (camera, flow, RANSAC, worlds, bridges, EKF3 injection ...)
- [project phases (CLAUDE.md / PROGRESS.md)] "## Current Focus (Phase 1)" — `CLAUDE.md:1850` — note: project-level Phase 1: Completed/Remaining item lists follow; no prose definition; conflicts with forward-camera Phase 1

### `Phase 1c`

- [forward-camera workstream phases] "**Check flights (Phase 1c).** One per ceiling world, six in all:" — `METHODOLOGY.md:2374` — note: ceiling-world check flights p1c_*

### `Phase 2`

- [forward-camera workstream phases] "## Phase 2 — `fwd_*` dataset: pre-registration (2026-09-24, before any `fwd_*` data exists)" — `METHODOLOGY.md:1843` — note: fwd_* dataset; later SUPERSEDED as a dataset (no ceiling, sky visible) per CLAUDE.md Key Paths
- [forward-camera workstream phases] "**Dataset.** `fwd_{tex,trans,blank}_r{1,2,3}`: the three `corridor_*_fwd` worlds × 3" — `METHODOLOGY.md:1845`
- [project phases (CLAUDE.md / PROGRESS.md)] *(used, not defined here)* "## Next Priorities (Phase 1 remainder → Phase 2)" — `PROGRESS.md:1212` — note: project-level Phase 2: no written definition or checklist found; the block is marked SUPERSEDED (stale) 2026-09-29 at line 1214

### `Phase 2b`

- [forward-camera workstream phases] "## Phase 2b — `fwdplain_*` dataset: pre-registration (2026-09-24, before any plain-wall data exists)" — `METHODOLOGY.md:2233` — note: fwdplain_* dataset pre-registration
- [forward-camera workstream phases] *(superseded)* "### Ceiling datasets — pre-registration (2026-09-24, before any ceiling data exists; supersedes the Phase 2b plan for `fwdplain_*`)" — `METHODOLOGY.md:2372` — note: ceiling datasets pre-registration "supersedes the Phase 2b plan for `fwdplain_*`"

### `Phase 3`

- [forward-camera workstream phases] "## Phase 3 — forward-camera measurements: pre-registration (2026-09-24, before calibration or validation runs)" — `METHODOLOGY.md:2636`
- [forward-camera workstream phases] "**Scope.** Two measurements from `/forward_camera/image`, validated before any fusion:" — `METHODOLOGY.md:2638`

### `Phase 4`

- [forward-camera workstream phases] "## Phase 4 — offline forward-camera fusion, UKF and FGO only: pre-registration (2026-09-29, before any fusion code or run)" — `METHODOLOGY.md:2954`
- [forward-camera workstream phases] "- Fuse the Phase 3 forward-camera measurements into the Python UKF and FGO." — `METHODOLOGY.md:2957`

### `Phase 5`

- [forward-camera workstream phases] "The test is Phase 5: each estimator with and without the forward-camera measurements," — `METHODOLOGY.md:1336` — note: hypothesis test defined with the hypothesis
- [forward-camera workstream phases] "## Phase 5 — evaluation against the pre-registered prediction (2026-09-29; analysis of Phase 4 outputs only)" — `METHODOLOGY.md:3392`

### `Phase 5b`

- [forward-camera workstream phases] "## Phase 5b — consistency (NEES) and the heading innovation covariance (2026-09-29)" — `METHODOLOGY.md:3697`
- [forward-camera workstream phases] "**Replays.** 72 sandbox replays: UKF and FGO, baseline and heading, all 18 ceiling bags." — `METHODOLOGY.md:3699`

### `rgs_check_tex`

- [check flights (one-off names)] "### Check flight `rgs_check_tex`: pre-registration (step b, before flying) ... **Flight.** World `corridor_textured_fwdc`, the standard dataset mission (arm, climb to 2 m," — `METHODOLOGY.md:4587`
- [other named checks and studies] "### Check flight `rgs_check_tex`: pre-registration (step b, before flying)" — `METHODOLOGY.md:4587`
- [other named checks and studies] "**Flight.** World `corridor_textured_fwdc`, the standard dataset mission (arm, climb to 2 m," — `METHODOLOGY.md:4589`

### `Rung 1`

- [real-flight rungs] "- **Rung 1:** a minimal logging flight. Stock firmware; the vehicle's own flow sensor and rangefinder; EKF3 or the" — `METHODOLOGY.md:12978`
- [real-flight rungs] "A vehicle that the supervisor provides, running **stock ArduPilot**, with **its own flow sensor and rangefinder on the" — `docs/minimal_real_flight_plan.md:25` — note: "Rung 1 in one paragraph"

### `Rung 2`

- [real-flight rungs] "- **Rung 2:** open loop with OUR pipeline. Pi, camera-based flow, forward camera; EKF3 flying, with the UKF and FGO" — `METHODOLOGY.md:12980`
- [real-flight rungs] "### RULING (user, 2026-10-10): REPRIORITISATION, thesis results first; rungs 2 and 3 PARKED until after the 16 Oct freeze" — `METHODOLOGY.md:13149` — note: status only, definition unchanged: rungs 2 and 3 PARKED until after the 16 Oct freeze (ruling 2026-10-10)

### `Rung 3`

- [real-flight rungs] "- **Rung 3:** closed loop. Custom board firmware, UKF/FGO steering, the full watcher and the safety tests." — `METHODOLOGY.md:12982`
- [real-flight rungs] "### RULING (user, 2026-10-10): REPRIORITISATION, thesis results first; rungs 2 and 3 PARKED until after the 16 Oct freeze" — `METHODOLOGY.md:13149` — note: status only, definition unchanged: rungs 2 and 3 PARKED until after the 16 Oct freeze (ruling 2026-10-10)

### `S0`

- [Experiment H stages] "**S0 (no estimator uses the wall tag yet).**" — `METHODOLOGY.md:10635` — note: H stage; H stages S0a/S0b/S1..S3v2 covered by another agent
- [Experiment H stages] "- **S0 (offline + check flights; no estimator uses the tag yet):**" — `docs/tag_hold_design.md:159`

### `S0a`

- [H stages] "- **S0a, characterisation:** open loop on simulator truth (`AHRS_EKF_TYPE 10`), the 47-segment sweep" — `METHODOLOGY.md:10636`

### `S0b`

- [H stages] "- **S0b, check flight:** open loop on simulator truth. `TAG_FWD_SEND=1`; EKF3 runs ExtNav with `EK3_SRC1_POSXY 6`," — `METHODOLOGY.md:10652`

### `S1far`

- [H stages] "`H_ifa_ukf`, `H_ifa_fgo`; S1 re-fly `H_s1far_r1..3`). It stops at the first breach or failed run." — `METHODOLOGY.md:11953` — note: "S1far" as a bare label is only used in docs/thesis/figures_thesis/index.md:261 ("lockouts S1 / S1far / S2v2 / S3v2"); S1 re-fly defined at line 11341, results heading at line 12104 (s1far_r*.json)

### `S2v2`

- [H re-fly suffixes] "### S2 RE-FLY with the jitter-corrected UKF (`H_s2v2_r{1,2,3}`, `eval/results/expH/s2v2_r*.json`); the original S2 is kept, labelled "old UKF (jitter)"" — `METHODOLOGY.md:12504`
- [H stages] "### S2 RE-FLY with the jitter-corrected UKF (`H_s2v2_r{1,2,3}`, `eval/results/expH/s2v2_r*.json`); the original S2 is kept, labelled "old UKF (jitter)"" — `METHODOLOGY.md:12504`
- [H stages] "S2v2 (jitter-corrected); the C++ FGO in S3v2 (noise fix + gated yaw cap; OLD priors). Open = shadow: the UKF and FGO replayed offline on the S1 flights (final re-runs), and" — `docs/thesis/final_results_pack.pdf p.15` — note: reader-facing gloss of S2v2/S3v2

### `S3v2`

- [H re-fly suffixes] "### S3 RE-FLY with the final corrected FGO (noise fix + gated yaw cap; node `f642cd37…`; `H_s3v2_r{1,2,3}`, `eval/results/expH/s3v2_r*.json`)" — `METHODOLOGY.md:12565` — note: CONFLICT in numbering: S3v2 flies the same final FGO node as the corridor _v3 flights
- [H stages] "### S3 RE-FLY with the final corrected FGO (noise fix + gated yaw cap; node `f642cd37…`; `H_s3v2_r{1,2,3}`, `eval/results/expH/s3v2_r*.json`)" — `METHODOLOGY.md:12565`

### `safety tests (a)/(b)`

- [other named checks and studies] `safety tests (a)/(b)` "**1. Option (i) safety tests** (`room_wall_tag_far`, H config; profile: wait_fix at the spawn → 2.4 m move to" — `METHODOLOGY.md:11286` — note: UKF (a)/(b), FGO (a)/(b) runs listed at lines 11288-11293; criteria S-A1..S-A4

### `set (a)`

- [closed-loop Part 1/Part 2 and sets (a)/(b)/(c)] `set (a)` "- (a) EKF3 without heading, `corridor_textured_fwdc`, ×1 (reference)." — `METHODOLOGY.md:4841`

### `set (b)`

- [closed-loop Part 1/Part 2 and sets (a)/(b)/(c)] `set (b)` "- (b) EKF3 + live camera heading, `corridor_textured_fwdc`, ×3." — `METHODOLOGY.md:4842`

### `set (c)`

- [closed-loop Part 1/Part 2 and sets (a)/(b)/(c)] `set (c)` "- (c) only if (b) passes: EKF3 + live camera heading, `corridor_blank_fwdplainc` (plain walls" — `METHODOLOGY.md:4843`

### `Stage 3`

- [UKF-only closed-loop stage] "# Stage 3 (UKF-only closed loop): DRAFT pre-registration for the user's sign-off" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:1` — note: stage 3 = UKF-only closed loop on real hardware (draft pre-registration)

### `Stage A`

- [CLAUDE.md EKF3 integration stages] "**Stage A proves flow velocity fusion only — it is NOT a GNSS-denied" — `CLAUDE.md:216`
- [CLAUDE.md EKF3 integration stages] "### Downward Optical Flow — EKF3 Fusion (Stage A)" — `CLAUDE.md:214`

### `Stage B`

- [CLAUDE.md EKF3 integration stages] "### EKF State Estimate — Stage B (evo evaluation)" — `CLAUDE.md:350`
- [CLAUDE.md EKF3 integration stages] "> **Do not quote Stage B's 6.4 mm ATE, or Stage C's 7.7 mm / 10.0 mm ATEs, as a" — `CLAUDE.md:354` — note: status warning, definition unchanged: Stage B/C ATE numbers VOID as EKF3 accuracy (/ekf/pose was simulator truth, AHRS_EKF_TYPE=10)

### `Stage C`

- [CLAUDE.md EKF3 integration stages] "> **Do not quote Stage B's 6.4 mm ATE, or Stage C's 7.7 mm / 10.0 mm ATEs, as a" — `CLAUDE.md:354` — note: status warning, definition unchanged: Stage B/C ATE numbers VOID as EKF3 accuracy (/ekf/pose was simulator truth, AHRS_EKF_TYPE=10)
- [CLAUDE.md EKF3 integration stages] "### GNSS-Denied Configuration — Stage C" — `CLAUDE.md:432`
- [CLAUDE.md EKF3 integration stages] "**This is the config the thesis actually studies**, and the standing" — `CLAUDE.md:434`

### `T_A`

- [experiment T conditions] "| A, all | `all` | 8 | ≈ 4–5 s |" — `METHODOLOGY.md:10118` — note: condition row; trials named T_<cond>_r1..r3
- [experiment T conditions] "- **Caption:** Experiment T (room_tags, 5 laps of a 6 m square, open loop on simulator truth): horizontal RMSE in the world frame, no alignment, against the tags sent (A all 8, B the 4 corners, C 2 diagonal, D 1 tag; median gap between fixes 4.3 / 10.1 / 22.0 / 46.3 s). Solid, filled = live; dashed, open = hindsight ..." — `docs/thesis/figures_thesis/index.md:50` — note: caption gives A–D tag subsets
- [experiment T conditions] "| room_tags | CURRENT (experiments T and L) | `T_{A,B,C,D}_r1–3` (12 reported; L replays `T_A_r1–3` and is not a separate flight set), `tagchar_h15/20/25/30`, `tag_check*`, `room_check` | thesis **F5** (T), **F7** (L), A3; pack F09, F10, F12, F13; numbers §16.1, §16.3 |" — `docs/thesis/world_images/index.md:33` — note: trial naming; L replays T_A_r1–3
- [experiment trial names (T/O/H)] "| A, all | `all` | 8 | ≈ 4–5 s |" — `METHODOLOGY.md:10118`

### `T_B`

- [experiment T conditions] "| B, corners | `0,1,2,3` | 4 | ≈ 10–11 s (**straddles EKF3's 10 s timeout**: its timeout state is logged per gap as a covariate) |" — `METHODOLOGY.md:10119` — note: condition row; trials named T_<cond>_r1..r3
- [experiment trial names (T/O/H)] "| B, corners | `0,1,2,3` | 4 | ≈ 10–11 s (**straddles EKF3's 10 s timeout**: its timeout state is logged per gap as a covariate) |" — `METHODOLOGY.md:10119`

### `T_C`

- [experiment T conditions] "| C, diagonal | `0,2` | 2 | ≈ 22–25 s |" — `METHODOLOGY.md:10120` — note: condition row; trials named T_<cond>_r1..r3
- [experiment trial names (T/O/H)] "| C, diagonal | `0,2` | 2 | ≈ 22–25 s |" — `METHODOLOGY.md:10120`

### `T_D`

- [experiment T conditions] "| D, single | `0` | 1 | ≈ 48–52 s |" — `METHODOLOGY.md:10121` — note: condition row; trials named T_<cond>_r1..r3
- [experiment trial names (T/O/H)] "| D, single | `0` | 1 | ≈ 48–52 s |" — `METHODOLOGY.md:10121`

### `three-way comparison`

- [named experiments] "The three-way EKF3 / UKF / FGO comparison uses trials flown under" — `METHODOLOGY.md:863` — note: main corridor comparison; heading "Comparison dataset — nomag (no yaw source)" at line 861
- [named experiments] "## Three-way comparison — first same-metric results (nomag `dsn_*`, n=1 per bag)" — `METHODOLOGY.md:469` — note: first same-metric results section

### `V1` — **CONFLICT: 4 meanings** (see flags §b)

- [D17 heading-UKF verification sequence V1–V4] "**V1 — Replay check on set (b)'s logs** (`cl_bcpp_tex_r1..r3`, `LOG_REPLAY 1`, EKF3 flew with the C++" — `METHODOLOGY.md:7594`
- [M2-R runaway-probe validity checks] "- **Runaway detected (V1)** when the operator-link `LOCAL_POSITION_NED` 3-D |v| ≥ 0.2 m/s continuously for ≥ 1.0 s," — `docs/handovers/2026-10-12_m2_full_bench.md:126`
- [UKF port input-path variants (step 3)] "| **V1: IMU path** (DAL INS deltas, 1 kHz-integrated, accumulated to EKF3's 12 ms target: 27,079 predicts, against 22,539 × 15 ms) | 0.21 / 0.91 / **3.15 m** | **2.28°** | 10,050 / 10,246 / 111 |" — `METHODOLOGY.md:6197` — note: rows of "variant (the one input changed)" table, eval/ukf_step3.py
- [UKF-only SITL verification flights V1–V7 (costing §6)] "| V1 | UKF shadow, EKF3 flying, hover + small box | UKF initialises on the ground (also with the rangefinder min raised above the ground clearance, after U4); `XUKF` tracks truth |" — `docs/ukf_only_closed_loop_costing.md:261`

### `V2` — **CONFLICT: 3 meanings** (see flags §b)

- [D17 heading-UKF verification sequence V1–V4] "**V2 — shadow run of the exact binary with heading** (EKF3 flies as in set (b); the UKF in shadow with" — `METHODOLOGY.md:7609`
- [UKF port input-path variants (step 3)] "| **V2: flow gyro** (ArduPilot's arrival-window AHRS gyro, against the frame-averaged IMU gyro) | 0.09 / 0.41 / **1.47 m** | **1.08°** | unchanged |" — `METHODOLOGY.md:6198` — note: rows of "variant (the one input changed)" table, eval/ukf_step3.py
- [UKF-only SITL verification flights V1–V7 (costing §6)] "| V2 | UKF flying (type 12), hover 60 s + box (`fly_trial.py` GUIDED local NED) | `HORIZ_POS_REL` throughout; no `thesis_nav_check` event |" — `docs/ukf_only_closed_loop_costing.md:262`

### `V3` — **CONFLICT: 5 meanings** (see flags §b)

- [D17 heading-UKF verification sequence V1–V4] "**V3 — ground test with the UKF active and heading on** (`UKF=1 HEADING=1 GROUND_TEST=60`):" — `METHODOLOGY.md:7617`
- [M2-R runaway-probe validity checks] "- **V3 (probe validity):** every operator-link |v| sample in the 0.3 s before the probe ≥ 0.2 m/s (the runaway still" — `docs/handovers/2026-10-12_m2_full_bench.md:134`
- [UKF port input-path variants (step 3)] "| **V3: flow fused at arrival** (no delay buffer) | 0.28 / 1.34 / **4.80 m** | **3.56°** | unchanged |" — `METHODOLOGY.md:6199` — note: rows of "variant (the one input changed)" table, eval/ukf_step3.py
- [UKF-only SITL verification flights V1–V7 (costing §6)] "| V3 | Safety (a): `AHRS_UKF_TFAIL` forced invalidity in hover | `thesis_nav_check` → LAND; touchdown drift within the pre-registered bound (earlier SITL: attitude-only drift 0.37–1.4 m) |" — `docs/ukf_only_closed_loop_costing.md:263`
- [stage-3 sorties] "| **V3: first free hover, UKF flying** | verification | take-off, hover 30 s, one 1 m leg and back at ≤ 0.2 m/s, land (~1.5 min airborne) | shows the UKF holds and moves the vehicle with the right sign; nothing more | go/no-go for the result sorties; the [TBD-V] values of §6 |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:61` — note: conflicts with costing V3 (SITL safety (a)) and D17 V3; here V3 is the first real free hover

### `V4` — **CONFLICT: 3 meanings** (see flags §b)

- [D17 heading-UKF verification sequence V1–V4] "**V4 — the with-heading UKF set ×3** (`cl_ukf_b_tex_r1..r3`: `UKF=1 HEADING=1`," — `METHODOLOGY.md:7623`
- [UKF port input-path variants (step 3)] "| V4: the port's range sampling (cm-quantised, ≥ 33 ms) | 0.02 / 0.09 / 0.32 m | 0.23° | 10,050 / 9,677 / 96 |" — `METHODOLOGY.md:6200` — note: rows of "variant (the one input changed)" table, eval/ukf_step3.py
- [UKF-only SITL verification flights V1–V7 (costing §6)] "| V4 | Flow loss: `SIM_FLOW_ENABLE 0` mid-hover | LAND after the 5 s aiding timeout; drift recorded |" — `docs/ukf_only_closed_loop_costing.md:264`

### `V5` — **CONFLICT: 2 meanings** (see flags §b)

- [UKF port input-path variants (step 3)] "| V5: V1 + V2 + V3 + V4 | 0.32 / 1.46 / **5.13 m** | **3.75°** | 10,050 / 9,677 / 111 |" — `METHODOLOGY.md:6201` — note: rows of "variant (the one input changed)" table, eval/ukf_step3.py
- [UKF-only SITL verification flights V1–V7 (costing §6)] "| V5 | Rangefinder loss | Vertical hold for 15 s then … **pre-register the expected outcome** (LAND on hold height; behaviour after `VERT_HOLD_MS` [U]) |" — `docs/ukf_only_closed_loop_costing.md:265`

### `V6`

- [UKF-only SITL verification flights V1–V7 (costing §6)] "| V6 | Watcher heartbeat loss | `FS_GCS_ENABLE 5` → LAND within `FS_GCS_TIMEOUT` (**not yet tested via MAVLink**: the SITL T1/T2 tests of `tools/test_watch_failclosed.sh` used the local heartbeat file read by `fly_trial.py`; the first MAVLink test is 2(c) B0–B10, then once on the UKF build) |" — `docs/ukf_only_closed_loop_costing.md:266`

### `V7`

- [UKF-only SITL verification flights V1–V7 (costing §6)] "| V7 | Arming: `TFAIL ≠ 0` refused; rangefinder below its minimum on the ground | refusal / initialisation as designed (U4) |" — `docs/ukf_only_closed_loop_costing.md:267`

### `V-L`

- [Experiment L hypotheses] "**V-L validation (no revisits):** `dsn_tex_r1` (corridor, 300 s cruise, no tags)." — `METHODOLOGY.md:10486` — note: PASS iff live ATE within ±20% of the thesis FGO (line 10491)
- [other named checks and studies] "**V-L validation (no revisits):** `dsn_tex_r1` (corridor, 300 s cruise, no tags)." — `METHODOLOGY.md:10486` — note: validation replay of the Experiment L estimator

## 2. Trial, dataset, batch and results naming


### `*_<tag>.json`

- [eval/results naming] `*_<tag>.json (set evaluation)` "# Steps (each output goes to eval/results/*_<tag>.json, logs to" — `eval/run_set_eval.sh:6` — note: flow_quality_<tag>, input_timing_<tag>, <tag>_evo, <tag>_score (tags dsn, p1c, fwdc, fwdplainc, rerun_<set>, dsn_extra ...)

### `<batch>`

- [batch state names] `<batch> (state dir)` "| **Resumable batch runner (use for datasets)** | `~/thesis_ws/run_resumable_batch.sh <conf> <batch>` — run in tmux; state in `~/thesis_data/batches/<batch>/` (`trials.log`, `STATUS`, `DONE`/`FAILED`); re-run the same command after a crash to resume (partial t ..." — `CLAUDE.md:75`

### `<floorword>_<dataset>`

- [floor/world suffixes] `<floorword>_<dataset> (yaw-sweep keys)` "| Static sweep, pooled slope `textured_fwdc` (all y, JSON) ⚑ | 0.6240513705473866 | — | DIAGNOSTIC | json:fwd_yaw_sweep.json:textured_fwdc.slope |" — `docs/thesis/numbers.md:985` — note: grammar deviation: textured/transition/blank + _fwdc/_fwdplainc, instead of <dataset>_<tex|trans|blank>

### `<pipeline>_<stage> batch names`

- [batch state names] `<pipeline>_<stage> batch names (rerun_phase3, d15_phase4, eval_rerun_<set>)` "eval/run_jobs_resumable.sh "$STATE/phase3.jobs" rerun_phase3 "$PAR" > "$STATE/phase3_jobs.txt" 2>&1 || die "phase3 runs"" — `eval/rerun_pipeline.sh:75` — note: by code: rerun_/d15_/final_ pipelines name job-batch states <pipeline>_<stage>; set evals get tag rerun_<set> (line 66) -> eval_rerun_<set>
- [batch state names] `<pipeline>_<stage> batch names (rerun_phase3, d15_phase4, eval_rerun_<set>)` "eval/run_jobs_resumable.sh "$STATE/phase4.jobs" d15_phase4 "$PAR" > "$STATE/phase4_jobs.txt" 2>&1 || die "phase4 replays"" — `eval/d15_pipeline.sh:76`
- [batch state names] `<pipeline>_<stage> batch names (rerun_phase3, d15_phase4, eval_rerun_<set>)` "eval/run_set_eval.sh "rerun_$s" "${T[@]}" > "$STATE/set_$s.txt" 2>&1 || die "set eval $s"" — `eval/rerun_pipeline.sh:66`

### `_a / _b` — **CONFLICT: 3 meanings** (see flags §b)

- [set-letter suffixes (a)/(b)] `_a / _b (closed-loop sets)` "- (a) EKF3 without heading, `corridor_textured_fwdc`, ×1 (reference)." — `METHODOLOGY.md:4841` — note: cl_a_/cl_b_, cl_ukf_a/b, cl_fgo_a/b: a = no heading, b = with live camera heading
- [set-letter suffixes (a)/(b)] `_a / _b (H safety tests)` "- **UKF (a):** UKF flying; failure = `AHRS_UKF_TFAIL` set in flight (output forced invalid); standard watcher." — `METHODOLOGY.md:11289` — note: H_safety_<est>_a/_b: a/b = failure-injection variant, NOT heading on/off
- [set-letter suffixes (a)/(b)] `_a / _b (H safety tests)` "- **UKF (b):** UKF flying; failure = SIGKILL of the tag bridge and the flow bridge (all its aiding inputs); the" — `METHODOLOGY.md:11290`
- [set-letter suffixes (a)/(b)] `_a / _b (H safety tests)` "- **FGO (a):** C++ node flying; failure = SIGKILL of the node; standard watcher (not watching the node). ... - **FGO (b):** as FGO (a), with the watcher also watching the node (`--dep-loss land`)." — `METHODOLOGY.md:11292`
- [set-letter suffixes (a)/(b)] `_a / _b (FGO shadow runs)` "- `fgo_shadow_half_a` (no heading); ... - `fgo_shadow_half_b` (heading; after D20)." — `METHODOLOGY.md:8071`

### `_abort1 / _abort2`

- [trial status suffixes] "### H safety test UKF (a), attempt 1 (`H_safety_ukf_a_abort1`): ABORTED before arming. The tag bridge crashed on a floor tag. Fixed by a wall-tag-only ROI pose (verified equivalent)" — `METHODOLOGY.md:11439`
- [trial status suffixes] "### H safety UKF (a), attempt 3 (`H_safety_ukf_a_abort2`): ABORTED on the ground. The test hook persisted in eeprom; fixed" — `METHODOLOGY.md:11654` — note: abort2 is attempt 3 (per this heading): the suffix number is not the attempt number
- [trial status suffixes] "ABORTED 2026-10-09: pre-arm gate crashed in DFReader on a partially written dataflash record before arming (no flight). fly_trial.py guard added; re-flown as H_safety_ukf_a_v2." — `~/thesis_data/trials/H_safety_ukf_a_v2_abort1/ABORTED.txt:1` — note: hand-written ABORTED.txt (not run_resumable_batch.sh format)
- [trial status suffixes] "### H safety FGO (a), attempt 1 (`H_safety_fgo_a_abort1`): ABORTED before arming. The pre-arm gate refused (FGO "not anchored"); a gate criterion fault, fixed" — `METHODOLOGY.md:11778`

### `_ABORTED`

- [trial status suffixes] `_ABORTED (manual)` "as `H_s0a_ABORTED`." — `METHODOLOGY.md:10712` — note: H_s0a_ABORTED / H_s0b_ABORTED named by hand, not by the runner (METHODOLOGY 10711-10712, 10794)
- [trial status suffixes] `_ABORTED (manual)` "ABORTED 2026-09-24: Phase 1 stopped after p1_fwd_tex failed confound check (a) (RTF 0.768 vs control 0.954). Partial, not a valid trial." — `~/thesis_data/trials/p1_fwd_blank_ABORTED/ABORTED.txt:1`

### `_ABORTED / _ABORTED_N`

- [trial status suffixes] "# Resume rule: a trial directory that exists without a COMPLETE line (a crash, a ... # kill, or a failed run) gets ABORTED.txt and is renamed <name>_ABORTED[_N]. Its data" — `run_resumable_batch.sh:22`
- [trial status suffixes] "ABORTED — do not use this trial's data." — `~/thesis_data/trials/T_D_r1_ABORTED_2/ABORTED.txt:1` — note: marker text; _ABORTED_2 = second aborted attempt of T_D_r1 (line 5 "attempt 2 failed")

### `_aux`

- [archive folders (~/thesis_data)] `_aux (pre_final*_trials/_aux)` "cp -a ~/thesis_data/phase5b_d15 ~/thesis_data/batches/eval_{rerun_dsn dsn_extra rerun_p1c rerun_fwdc rerun_fwdplainc} /home/makerspace/thesis_data/pre_final_trials/_aux/" — `docs/handovers/2026-10-09_final_rerun_dryrun.txt:75`

### `_b`

- [set-letter suffixes (a)/(b)] `_b (re-run)` "### PRE-REGISTRATION: FGO ground test re-run `fgo_groundtest_half_b` (D24), recorded before the run" — `METHODOLOGY.md:8801` — note: here "_b" = second attempt/re-run, unlike shadow run (b) = heading
- [set-letter suffixes (a)/(b)] `_b (re-run)` "- Run 1 is repeated as `gt_heading_half_b`." — `METHODOLOGY.md:7862`

### `_d5`

- [shadow and development runs] `_d5 (ukf_shadow_sitl_tex_d5)` "### D5 report (before any UKF flight): live SITL shadow run with the delay-buffered port, `ukf_shadow_sitl_tex_d5`" — `METHODOLOGY.md:6547` — note: _d5 = ruling D5 (flow delay buffer, METHODOLOGY 6433)

### `_d15`

- [shadow and development runs] `_d15 (ukf_shadow_sitl_tex_d15)` "**P2** (`ukf_shadow_sitl_tex_d15`, port `9d2c545d29`, `AHRS_EKF_TYPE 10`, shadow, `corridor_textured`):" — `METHODOLOGY.md:7313` — note: _d15 = after ruling D15 (ground-proximity flow rule); D9 precondition P2 re-run

### `_far`

- [experiment trial names (T/O/H)] "- worlds `room_wall_tag_far` (spawn 3.9 m from the tag) and `room_wall_tag_far_occ` (the same, occluder starting in" — `METHODOLOGY.md:11272`
- [ground tests (gt_ / _groundtest)] `_far (H_gt_*_far)` "**3. Ground tests re-run** (`H_gt_ukf_far`, `H_gt_fgo_far` with the C++ node; profile `wtest_far_profile.json`)." — `METHODOLOGY.md:11321`

### `_fix`

- [closed-loop sets and build suffixes] "**PRE-REGISTERED live check `fgo_cpp_shadow_ii_fix`** (flight (ii) again: 0.10 s, time_ref, open loop on truth)," — `METHODOLOGY.md:11724` — note: _fix = re-flight of (ii) after the time_ref fix
- [re-flight version suffixes _v<N>] `_fix (fgo_cpp_shadow_ii_fix)` "**PRE-REGISTERED live check `fgo_cpp_shadow_ii_fix`** (flight (ii) again: 0.10 s, time_ref, open loop on truth)," — `METHODOLOGY.md:11724`

### `_half`

- [closed-loop sets and build suffixes] "- **All FGO closed-loop flights fly at half real-time speed** (Gazebo `real_time_factor` 0.5)." — `METHODOLOGY.md:7795`
- [closed-loop sets and build suffixes] "- **Fix (harness, before any re-run):** half-speed worlds (`*_half_*`) run with gz-transport and ROS 2" — `METHODOLOGY.md:7855`
- [closed-loop sets and build suffixes] "Textured corridor, 0.5 m/s, 300 s cruise. Full speed = `corridor_textured_fwdc`; half speed = `corridor_textured_half_fwdc` (loopback-pinned, `VISO_DELAY_MS` 25). No cross-speed comparison is claimed (D21). n = 1 per no-heading cell; closed-loop run-to-run variability is unmeasured. **All flown FGO results here (incl. ..." — `docs/thesis/numbers.md:456`
- [closed-loop trial names] "- **World:** `sim/worlds/corridor_textured_half_fwdc.sdf`, a copy of `corridor_textured_fwdc` with ... only the world name and `real_time_factor` 0.5 changed. The name must end in `_fwdc` for" — `METHODOLOGY.md:7829` — note: "half" = HALF SIM SPEED (RTF 0.5), NOT half commanded velocity (velocity stays 0.5 m/s)
- [closed-loop trial names] "- **Prediction:** unchanged (EKF3 ≈ +186 s; UKF ≈ +161…+193 s, west). Half speed changes only the ... wall-clock latencies' share of sim time, and D8 shows EKF3 insensitive to flow timing at this scale." — `METHODOLOGY.md:8024`
- [closed-loop trial names] "if [[ "$WORLD" == *_half_* ]]; then export LOOPBACK_ONLY=1 GZ_IP=127.0.0.1 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST; fi" — `sim/tools/closed_loop_run.sh:15` — note: code: _half worlds are loopback-pinned

### `_IMUGAP`

- [trial status suffixes] "- **Correction:** the six are re-flown unchanged (`tools/run_expT_refly.sh`) with nothing else on the machine. The ... old directories are kept as `<name>_IMUGAP`. Their EKF3-only numbers are not used." — `METHODOLOGY.md:10222`
- [trial status suffixes] "# bridge irregularities). Run with NOTHING else on the machine. Old dirs are kept as <name>_IMUGAP." — `tools/run_expT_refly.sh:4`
- [trial status suffixes] "It is kept as `O_r3_IMUGAP` and was re-flown unchanged as O_r3b. All gates G1–G4" — `METHODOLOGY.md:10401`

### `_oi2`

- [offline variant clones] "- **Run.** Clones `dsn_tex_r{1,2,3}_oi2` are identical except for the IMU header ... stamps. The **unchanged** UKF/FGO replays run on them. Results:" — `METHODOLOGY.md:1250`

### `_oi2dj`

- [offline variant clones] "A control, `dsn_tex_r*_oi2dj` (`oi2_imu_time.py --dejitter`), fits a line to the ... **receipt** stamps themselves. That removes the jitter and keeps the mean latency, so" — `METHODOLOGY.md:1287`

### `_p2`

- [shadow and development runs] `_p2 (ukf_shadow_sitl_tex_p2)` "**P2** (`ukf_shadow_sitl_tex_p2`, port `6f561c6a8d`, `AHRS_EKF_TYPE 10`, shadow):" — `METHODOLOGY.md:6973` — note: _p2 = D9 precondition P2 (line 6847)

### `_r3b`

- [repeat suffix _r<k>] "It is kept as `O_r3_IMUGAP` and was re-flown unchanged as O_r3b. All gates G1–G4" — `METHODOLOGY.md:10401` — note: O_r3b = unchanged re-fly of IMU-gap-unusable O_r3
- [repeat suffix _r<k>] "### `H_s1far_r3b` (S1 flight-3 re-fly) and the FGO sizing replay" — `METHODOLOGY.md:12199` — note: H_s1far_r3b = re-fly of H_s1far_r3 (IMU-gap unusable, line 12105)

### `_r<k>`

- [repeat suffix _r<k>] "The GNSS-denied dataset is three corridor conditions — textured, blank, ... transition — each flown as **three identical-config repeats** (0.5 m/s, 2.0 m," — `METHODOLOGY.md:798` — note: r1..r3 = repeat index; the letter "r" is never expanded in writing
- [repeat suffix _r<k>] "**Dataset.** `fwd_{tex,trans,blank}_r{1,2,3}`: the three `corridor_*_fwd` worlds × 3 ... repeats, 300 s, 0.5 m/s, 2.0 m, no compass (`gnss_denied_nomag.parm`)," — `METHODOLOGY.md:1845`
- [repeat suffix _r<k>] "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: T_<cond>_r<k>: repeat k of condition
- [repeat suffix _r<k>] "# Experiment O flights (METHODOLOGY "Experiment O: pre-registration"): 3 repeats, nothing else on the machine." — `tools/run_expO.sh:2`

### `_ref` — **CONFLICT: 2 meanings** (see flags §b)

- [batch state names] `_ref (batch job lists *_ref.jobs)` "# FG1 reference for fgo_shadow_half_a3 (as fgo_shadow_half_a)" — `batches/fgo_shadow_a3_ref.jobs:1` — note: COLLISION: "_ref" here = FG1 offline reference replay, not a reference flight
- [experiment trial names (T/O/H)] `_ref (H_safety_ekf3_ref)` "- **`H_safety_ekf3_ref`** (EKF3 flying, main tree; tag bridge and flow bridge SIGKILLed in the hold; the watcher ... watches the tag bridge with `--dep-loss land`, as UKF (b)). A REFERENCE measurement:" — `METHODOLOGY.md:11877`

### `_refly`

- [experiment trial names (T/O/H)] `_refly (batches/expT/*_refly.conf)` "# Experiment T: re-fly of the flights the standing IMU-gap rule (eval/imu_gap_check.py) marked unusable, unchanged" — `tools/run_expT_refly.sh:2`

### `_robust`

- [closed-loop trial names] `_robust (cl_fgo_b_robust_*)` "- `cl_fgo_b_robust_tex_r1..r3_half`, exactly as `cl_fgo_b_tex_*_half` except the parameter." — `METHODOLOGY.md:9760` — note: the parameter = robust Cauchy weighting (cauchy:2.385, plan step 2(b))
- [closed-loop trial names] `_robust (fgo_shadow_half_b_robust)` "- Shadow `fgo_shadow_half_b_robust`: heading, truth flies, the same command form as `fgo_shadow_half_b`, plus the" — `METHODOLOGY.md:9754`

### `_run1_failed`

- [trial status suffixes] "- The failed run's directories are renamed `H_safety_ukf_a_run1_failed` (trials/ and closed_loop/). Its scored result ... stays in `eval/results/expH/safety_ukf_a.json`, where the trial field reads `H_safety_ukf_a`. The re-run reuse ..." — `METHODOLOGY.md:11650`

### `_t245`

- [offline variant clones] "# FINAL re-run, Experiment L (LAST; METHODOLOGY 10452-10563): keyframe FGO with/without loop closure on T_A_r1..r3, cut at ... # anchor + 245 s (the recorded deviation) -> lc_fgo_{lc,nolc}_t245/. FGO only (L has no UKF arm). nolc runs ar ..." — `batches/final_rerun/L.jobs:1`
- [offline variant clones] "### Experiment L RESULT (`eval/results/expL/*_t245.json`): H-L1, H-L2, H-L3 and P-L4 ALL PASS 3/3" — `METHODOLOGY.md:10551`

### `_tex / _trans / _blank`

- [floor/world suffixes] "| `p1c_img_tex` | `corridor_textured.sdf` | textured | ... | `p1c_img_trans` | `corridor_transition.sdf` | textured y < 80 m, blank y > 80 m |" — `docs/p1c_img_calibration_spec.md:14` — note: the only explicit name -> floor table; _blank row at line 16
- [floor/world suffixes] "| `p1c_img_blank` | `corridor_blank.sdf` | blank |" — `docs/p1c_img_calibration_spec.md:16`
- [floor/world suffixes] "corridor_textured 0.5 2.0 300 dsn_tex_r1 ... corridor_transition 0.5 2.0 300 dsn_trans_r1" — `batches/rerun_main.conf:10` — note: conf rows pair world -> trial name (world corridor_blank -> dsn_blank_r1 on line 12)
- [floor/world suffixes] "| corridor_blank | CURRENT | `dsn_blank_r1–3`, `ds_blank_r1–3`, `corridor_blank_verify` | thesis F4, F1 blank cell; pack F06; numbers §6.2, §7 |" — `docs/thesis/world_images/index.md:23` — note: world-to-trial index; _tex/_trans rows at lines 22, 24

### `_v1`

- [UKF build versions] "- **Caption:** Pass/fail of every closed-loop corridor set (replaces pack F15a), computed from the closed-loop score files, with the build ablations labelled: UKF v1 (pre-jitter fix) against v2 (final); FGO original, robust, v2 (noise fix only, ABLATION) and v3 (final, OLD priors)." — `docs/thesis/figures_thesis/index.md:237` — note: written "UKF v1 (pre-jitter fix)"
- [re-flight version suffixes _v<N>] `_v1 (H_wtest_*_v1)` *(used, not defined here)* "catch TrialFailure around sim_time_now_s, which swallowed the first version of this check (H_wtest_kill)."""" — `fly_trial.py:311` — note: H_wtest_kill_v1 / H_wtest_noarm_v1 exist on disk; no text defines _v1 (and fly_trial.py calls plain H_wtest_kill "the first version")
- [re-flight version suffixes _v<N>] `_v1 (H_wtest_*_v1)` *(used, not defined here)* "H_wtest_kill_v1" — `~/thesis_data/trials/H_wtest_kill_v1`
- [re-flight version suffixes _v<N>] `_v1 (H_wtest_*_v1)` *(used, not defined here)* "H_wtest_noarm_v1" — `~/thesis_data/trials/H_wtest_noarm_v1`

### `_v2 / _v3` — **CONFLICT: 2 meanings** (see flags §b)

- [re-flight version suffixes _v<N>] `_v2 / _v3 (FGO re-flights)` "# FGO closed-loop RE-FLIGHTS with the corrected FGO (ruling 2026-10-09). v3 = noise fix + gated yaw cap (node f642cd37); v2 = noise fix only (kept, ablation), one per argument, under the flight lock; stop at the" — `tools/run_fgo_refly.sh:2`
- [re-flight version suffixes _v<N>] `_v2 / _v3 (FGO re-flights)` "- `cl_fgo_a_tex_half_v2`: `FGO=1`, `corridor_textured_half_fwdc`, Python node (corrected core)." — `METHODOLOGY.md:12253`
- [re-flight version suffixes _v<N>] `_v2 / _v3 (FGO re-flights)` "### FGO re-flight `cl_fgo_a_tex_half_v3` (no heading, final corrected FGO, Python node): PRIMARY PASS" — `METHODOLOGY.md:12582`
- [re-flight version suffixes _v<N>] `_v2 / _v3 (D17 validation steps)` "### D17 V2 (shadow run of the exact binary with heading, `ukf_shadow_hdg_v2`): PASS" — `METHODOLOGY.md:7664` — note: COLLISION: here _v2/_v3 are D17 validation STEPS V2/V3, not re-flight versions
- [re-flight version suffixes _v<N>] `_v2 / _v3 (D17 validation steps)` "### D17 V3 (ground test, UKF active with heading, `ukf_groundtest_hdg_v3`): PASS" — `METHODOLOGY.md:7691`
- [re-flight version suffixes _v<N>] `_v2 / _v3 (D17 validation steps)` "**V2 — shadow run of the exact binary with heading** (EKF3 flies as in set (b); the UKF in shadow with" — `METHODOLOGY.md:7609`

### `acceptance`

- [archive folders (~/thesis_data)] "- **Acceptance input preserved permanently:** `~/thesis_data/acceptance/ukf_jitter_cfi60_A.bin`, sha256" — `METHODOLOGY.md:12448`
- [archive folders (~/thesis_data)] "The new acceptance set is `~/thesis_data/acceptance/fgo_d18_bandc`; the" — `METHODOLOGY.md:13687`

### `attrib_2026-10-10` — **UNDEFINED** (see flags §a)

- [batch state names] *(used, not defined here)* "attrib_2026-10-10" — `~/thesis_data/batches/attrib_2026-10-10`

### `b2`

- [set-letter suffixes (a)/(b)] `b2 (H_safety_fgo_b2)` "- **`H_safety_fgo_b2`** (the FGO (b) configuration at the new hold): S-A1–S-A4 exactly as pre-registered for (b)." — `METHODOLOGY.md:11883`

### `board_*`

- [eval/results naming] `board_* (eval/results)` "### 2a: board firmware BUILT for two representative H743 boards (`~/ardupilot_ukf` `board-h743` `0156bfc34e`, NOT merged; nothing flashed; `docs/board_firmware_plan.md`; handover `docs/handovers/2026- ..." — `METHODOLOGY.md:13558`

### `check1 / check3 / corridor_migration_test / verify_textured`

- [legacy one-off trials] "- **4 trials were not auditable:** `check1`, `check3`, `corridor_migration_test`, `verify_textured`. They are early ... tests whose GT stamps are all identical (from before the sim-time stamping) and are used in no result." — `METHODOLOGY.md:10004`

### `cl_`

- [closed-loop trial names] "**Flights** (each a closed-loop dataset, never compared with the open-loop datasets as if the" — `METHODOLOGY.md:4838` — note: "cl" never expanded letter by letter; sets (a)/(b)/(c) defined at 4841-4844

### `cl_a_* (set (a))`

- [closed-loop trial names] "- (a) EKF3 without heading, `corridor_textured_fwdc`, ×1 (reference)." — `METHODOLOGY.md:4841`
- [closed-loop trial names] "### Closed-loop set (a), `cl_a_tex` (EKF3 without heading, `corridor_textured_fwdc`, ×1): PRIMARY PASS" — `METHODOLOGY.md:5974`

### `cl_b_* (set (b))`

- [closed-loop trial names] "- (b) EKF3 + live camera heading, `corridor_textured_fwdc`, ×3." — `METHODOLOGY.md:4842`
- [closed-loop trial names] "### Closed-loop set (b) r1, `cl_b_tex_r1` (EKF3 + live camera heading, `every_n` 4): all B1–B5 PASS, after a scorer bug fix (QUEUED for the user's confirmation)" — `METHODOLOGY.md:5988`

### `cl_bcpp_`

- [closed-loop trial names] "### Set (b) RE-FLOWN with the C++ heading node (ruling D2): PASSES, 3/3 flights pass B1–B5 ... Settings: `VISO_DELAY_MS 38`, `every_n` 4, `impl: cpp`, otherwise as the Python-node set (b)." — `METHODOLOGY.md:6527` — note: results file names closed_loop_cl_bcpp_tex_r{1,2,3}.json (6530); "bcpp" never expanded

### `cl_bcpp_*_half`

- [closed-loop trial names] "- **EKF3:** `cl_bcpp_tex_r1..r3_half`, stock tree. **UKF:** `cl_ukf_b_tex_r1..r3_half`, port" — `METHODOLOGY.md:8209`
- [closed-loop trial names] "# D19: half-speed with-heading sets, EKF3 x3 then UKF x3; each flight scored; any B1 failure stops the runner." — `~/thesis_data/batches/half_b.sh:2`

### `cl_ekf3_tex`

- [check flights (one-off names)] "- One flight, `cl_ekf3_tex`: world `corridor_textured_fwdc`, the dataset mission (arm in" — `METHODOLOGY.md:3941` — note: closed-loop smoke test (EKF3 flying)

### `cl_ekf3_tex_2`

- [check flights (one-off names)] "### Check 2c — result (`cl_ekf3_tex_2`, flown 2026-09-29): PASS on both restated criteria" — `METHODOLOGY.md:4366` — note: "_2" = Check 2c, not a repeat index

### `cl_fgo_a_`

- [closed-loop trial names] "### FGO closed-loop flight WITHOUT heading, `cl_fgo_a_tex_half` (the FGO flies; half speed, ×1): PRIMARY PASS" — `METHODOLOGY.md:9302`

### `cl_fgo_b_`

- [closed-loop trial names] "- `cl_fgo_b_tex_r1..r3_half` ×3, B1–B5 as set (b), with B3 from `XFGO` (the scorer gets `--est fgo`)." — `METHODOLOGY.md:8093`

### `cl_pred`

- [final re-run job lists (batches/final_rerun)] `cl_pred (.jobs, final_cl_pred)` "# FINAL re-run, closed-loop OFFLINE prediction inputs (DESCRIPTIVE ONLY; open question: whether to restate pre-registered bands)." — `batches/final_rerun/cl_pred.jobs:1`

### `cl_ukf_a_`

- [closed-loop trial names] "### PRE-REGISTRATION — UKF closed-loop flight WITHOUT heading (`cl_ukf_a_tex`), written before any UKF flight (ruling D9)" — `METHODOLOGY.md:6835`

### `cl_ukf_b_`

- [closed-loop trial names] "### D17 V4 — the with-heading UKF set (`cl_ukf_b_tex_r1..r3`, the UKF flies with the camera heading): PASS, 3 of 3" — `METHODOLOGY.md:7709`

### `clfa / clfb<k> / clfr<k> / clukf` — **UNDEFINED** (see flags §a)

- [batch state names] *(used, not defined here)* "clfa.log" — `~/thesis_data/batches/clfa.log` — note: no text defines these short batch names
- [batch state names] *(used, not defined here)* "clfb1.log" — `~/thesis_data/batches/clfb1.log` — note: no text defines these short batch names
- [batch state names] *(used, not defined here)* "clfr1.log" — `~/thesis_data/batches/clfr1.log` — note: no text defines these short batch names

### `closed_loop`

- [archive folders (~/thesis_data)] `closed_loop (folder)` "- Output: `~/thesis_data/trials/cl_ekf3_tex/` and `~/thesis_data/closed_loop/cl_ekf3_tex/`" — `METHODOLOGY.md:4034` — note: closed_loop/<trial> = launcher/watcher side outputs (result.txt, BREACH.txt) parallel to trials/<trial>

### `closed_loop_<trial>.json`

- [eval/results naming] "eval/results/closed_loop_<trial>.json for cl_a_tex, cl_b_tex_r*, cl_bcpp_tex_r*(_half), cl_a_tex_half, cl_ukf_a_tex(_half)(_v2), cl_ukf_b_tex_r*(_half)(_v2), cl_fgo_a_tex_half(_v2)(_v3), cl_fgo_b_tex_ ..." — `docs/thesis/final_results_pack_index.md:25`
- [eval/results naming] "~/venv-evo/bin/python eval/closed_loop_score.py $n --set b --est ukf --json eval/results/closed_loop_$n.json > ~/thesis_data/batches/v4_$n.score 2>&1" — `~/thesis_data/batches/v4_set.sh:9`

### `corridor_<floor>_verify` — **UNDEFINED** (see flags §a)

- [legacy one-off trials] *(used, not defined here)* "| corridor_blank | CURRENT | `dsn_blank_r1–3`, `ds_blank_r1–3`, `corridor_blank_verify` | thesis F4, F1 blank cell; pack F06; numbers §6.2, §7 |" — `docs/thesis/world_images/index.md:23` — note: listing only; purpose not stated

### `d8`

- [archive folders (~/thesis_data)] `d8 (folder)` "d8_dsn_tex_r1 cd /home/makerspace/thesis_ws && PYTHONPATH=/home/makerspace/.cache/thesis_pyshim OPENBLAS_NUM_THREADS=1 /home/makerspace/venv-evo/bin/python eval/d8_ekf3_retime.py dsn_tex_r1 /home/makerspace/thesis_data/d8" — `~/thesis_data/d8/d8.jobs:1` — note: job list writes eval/d8_ekf3_retime.py outputs to ~/thesis_data/d8; D8 = the EKF3 re-timing diagnostic (METHODOLOGY 7096)
- [archive folders (~/thesis_data)] `d8 (folder)` "### D8 result (DIAGNOSTIC; never replaces the dataset results)" — `METHODOLOGY.md:7096`

### `d15_blank / d27_regen` — **UNDEFINED** (see flags §a)

- [batch state names] `d15_blank / d27_regen (batch dirs)` *(used, not defined here)* "d15_blank" — `~/thesis_data/batches/d15_blank` — note: no text defines these batch dir names (eval/d27_regen.sh exists but the dir name is not stated)
- [batch state names] `d15_blank / d27_regen (batch dirs)` *(used, not defined here)* "d27_regen" — `~/thesis_data/batches/d27_regen` — note: no text defines these batch dir names (eval/d27_regen.sh exists but the dir name is not stated)

### `d15_pipeline / rerun_pipeline`

- [batch state names] "# Usage: eval/d15_pipeline.sh (state in ~/thesis_data/batches/d15_pipeline/)" — `eval/d15_pipeline.sh:8`
- [batch state names] "# Usage: eval/rerun_pipeline.sh (state in ~/thesis_data/batches/rerun_pipeline/)" — `eval/rerun_pipeline.sh:10`

### `d15_port`

- [archive folders (~/thesis_data)] "(`eval/d15_port_score.py`; `~/thesis_data/d15_port/`):" — `METHODOLOGY.md:7225` — note: UKF-port Replay outputs after ruling D15
- [closed-loop sets and build suffixes] "**The UKF port with the rule (`~/ardupilot_ukf` `9d2c545d29`), Replay on dsn_tex r1–r10**" — `METHODOLOGY.md:7224`

### `d17_v1` — **UNDEFINED** (see flags §a)

- [archive folders (~/thesis_data)] *(used, not defined here)* "cl_bcpp_tex_r1" — `~/thesis_data/d17_v1/cl_bcpp_tex_r1` — note: no text names d17_v1 (presumably D17 V1 Replay check outputs, but not stated)
- [archive folders (~/thesis_data)] *(used, not defined here)* "d17_v1" — `~/thesis_data/d17_v1` — note: no text names d17_v1 (presumably D17 V1 Replay check outputs, but not stated)
- [closed-loop sets and build suffixes] *(used, not defined here)* "- the D17 V1 Replay of `cl_bcpp_tex_r1` (`UKF_EXTYAW=1`) with the new Replay binary gives a `ukf_shadow.csv` and" — `docs/h_backends_tag_input.md:135` — note: only "D17 V1" found; no d17_v1 token in the in-scope docs

### `d17_v2` — **UNDEFINED** (see flags §a)

- [archive folders (~/thesis_data)] *(used, not defined here)* "- **Fork-flown input** (`d17_v2/ukf_shadow_hdg_v2`): XUKO is declared, but 17 283 = 8 654 copied onboard + 8 629" — `docs/handovers/2026-10-12_r1_scoring_items.md:107` — note: usage, not a definition of the folder
- [closed-loop sets and build suffixes] *(used, not defined here)* "- **Fork-flown input** (`d17_v2/ukf_shadow_hdg_v2`): XUKO is declared, but 17 283 = 8 654 copied onboard + 8 629" — `docs/handovers/2026-10-12_r1_scoring_items.md:107` — note: data directory for D17 V2; no separate definition

### `d26`

- [archive folders (~/thesis_data)] `d26 (folder)` "- Results: `eval/results/d26_jitter_control.json`; Replay outputs in `~/thesis_data/d26/`." — `METHODOLOGY.md:9409`

### `d26_core / d27_ukf_rerun`

- [batch state names] `d26_core / d27_ukf_rerun (job lists and batch dirs)` "# D26 (b): FGO node-core replay of r3 with the gate log" — `batches/d26_core.jobs:1`
- [batch state names] `d26_core / d27_ukf_rerun (job lists and batch dirs)` "# D27 (b): re-run every offline UKF replay produced since 2026-09-29 with the aligned process noise (commit 5598e30)" — `batches/d27_ukf_rerun.jobs:1`

### `ds_`

- [trial dataset prefixes] "**Why not the compass-active `ds_*` trials.** The nine `ds_{tex,blank,trans}_r*` ... trials were flown under `gnss_denied.parm`, which leaves EKF3 fusing the compass" — `METHODOLOGY.md:867`
- [trial dataset prefixes] "**The `ds_*` trials are retained, not deleted**, as (a) the run-to-run" — `METHODOLOGY.md:876` — note: retained as noise-floor + EKF3-with-yaw-source reference; SUPERSEDED for the three-way comparison (line 878)
- [trial dataset prefixes] "# Consolidated re-run part 2: ds_* (compass-active yaw). Run with" — `batches/rerun_ds.conf:1` — note: letters "ds" never expanded in writing
- [trial dataset prefixes] *(superseded)* "They are **superseded for the three-way comparison** by the nomag `dsn_*` batch," — `METHODOLOGY.md:878`

### `dsn_`

- [trial dataset prefixes] "`gnss_denied_nomag.parm` (`EK3_SRC1_YAW=0`, compass unused) — the **`dsn_*` ... batch** (3 corridor worlds × 3 repeats)." — `METHODOLOGY.md:864` — note: three-way comparison dataset (nomag). The letters "dsn" are never expanded in writing.
- [trial dataset prefixes] "absence — `dsn_*` carry `EK3_SRC1_YAW=0`/`COMPASS_USE=0`, `ds_*` carry `1`/`1`." — `METHODOLOGY.md:888` — note: positive yaw_source label in metadata.yaml
- [trial dataset prefixes] "| corridor_textured | CURRENT | `dsn_tex_r1–r10` (standard-sensor baseline); `ds_tex_r1–3` (compass on, reference); about 26 checks and shadow runs | thesis F1 (standard sensors), F3 left; pack F03; numbers §1, §2, §6.1, §6.5, §7, §8, §14, §18 |" — `docs/thesis/world_images/index.md:22` — note: same meaning restated (also worlds_combined.pdf p.1)
- [trial dataset prefixes] "**No-yaw comparison params (used by `run_trial.sh` for all `dsn_*` and forward-camera datasets)** | `~/thesis_ws/gnss_denied_nomag.parm` (+ `sim_noise.parm`) — the three-way comparison config (METHODOLOGY "Comparison dataset — nomag") |" — `CLAUDE.md:67` — note: CLAUDE.md key-paths row

### `dsn_tex_r4..r10`

- [trial dataset prefixes] "# Pre-registered confirmatory dsn_tex repeats (METHODOLOGY 'PRE-REGISTRATION — additional dsn_tex repeats'); same settings as rerun_main" — `batches/dsn_tex_extra.conf:1` — note: r4-r10 are the additional confirmatory repeats (n=10 textured)

### `dsn_tex_r10`

- [repeat suffix _r<k>] "### `dsn_tex_r4..r10` flown (7/7); `dsn_tex_r10` UNUSABLE for UKF/FGO by the IMU-gap rule — handling in the paired test, recorded BEFORE any r4–r10 result is seen" — `METHODOLOGY.md:6225`

### `eeprom_backups / fw_builds` — **UNDEFINED** (see flags §a)

- [archive folders (~/thesis_data)] *(used, not defined here)* "KakuteH7_with_0156bfc3_20261012_014453_FAILED_nested_submodules" — `~/thesis_data/fw_builds/KakuteH7_with_0156bfc3_20261012_014453_FAILED_nested_submodules` — note: eeprom_backups is named at METHODOLOGY 11276 (eeprom backup); fw_builds naming undefined

### `ekf3_diag_60s`

- [legacy one-off trials] "**Measured properly (`ekf3_diag_60s`, `iris_textured`, 0.4 m/s, compass active)," — `CLAUDE.md:889`

### `eval_<tag>`

- [batch state names] "# Steps (each output goes to eval/results/*_<tag>.json, logs to ... # ~/thesis_data/batches/eval_<tag>/):" — `eval/run_set_eval.sh:6`

### `exp<X>/ result folders`

- [eval/results naming] "### Experiment T RESULT (`eval/t_aggregate.py`, `eval/results/expT/`): H-T1 PASSES; P-T2, P-T3, P-T4 FAIL as worded" — `METHODOLOGY.md:10236` — note: expH/expL/expO/expT = per-experiment result folders

### `expO`

- [final re-run pipeline stage names] "| O | `expO` | `room_O.jobs`: `room_ukf --gnss`, `room_ukf --gnss --rts-no-yawcap`, `room_fgo --gnss` on O_r1, O_r2, O_r3b; `o_score.py` | none | rebuilt (no committed list); `gnss.npz` inputs are reused, not re-extracted |" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:136` — note: stage name / results dir eval/results/expO; also batch dir batches/expO (O_r1..O_r3b.conf, main checkout)

### `expT`

- [final re-run pipeline stage names] "| T | `expT` | `room_T.jobs`: `room_ukf` (RTS) + `room_fgo` (batch) on the 12 flights; `tag_score.py` ×12; `t_aggregate.py` | none | rebuilt (no committed list). The *_IMUGAP originals are not replayed. |" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:137` — note: stage name / results dir eval/results/expT; also batch dir batches/expT (T_<cond>_r<n>.conf, main checkout)

### `expT_<trial> / expT_refly_<trial> / expO_<trial>`

- [batch state names] "./run_resumable_batch.sh "$conf" "expO_${name}" || { echo "expO: ${name} FAILED - stopping"; exit 1; }" — `tools/run_expO.sh:12`
- [batch state names] "./run_resumable_batch.sh "$conf" "expT_refly_${name}" || { echo "expT refly: ${name} FAILED - stopping"; exit 1; }" — `tools/run_expT_refly.sh:15`

### `expT_preD15fix`

- [eval/results naming] "- Re-scored; the pre-correction JSONs are kept in `eval/results/expT_preD15fix/`." — `METHODOLOGY.md:10879`

### `F`

- [final re-run job lists (batches/final_rerun)] `F (.jobs, final_F / final2_F)` "# FINAL consolidated re-run (2026-10-09): every F-test replay arm, UKF and FGO, VERBATIM from the lists that produced" — `batches/final_rerun/F.jobs:1`

### `F1` — **CONFLICT: 6 meanings** (see flags §b)

- [D12/D19 take-off backlog fix options] "- **(F1) Run the SITL simulation slower (Gazebo `real_time_factor` 0.5, lockstep SITL follows).** This is" — `docs/d12_fgo_backend_report.md:31` — note: CONFLICT: backlog-fix option, not the offline test
- [D12/D19 take-off backlog fix options] "- **(F1) SITL at `real_time_factor` 0.5**: the estimator is unchanged and no backlog is expected," — `docs/decisions_queue.md:161` — note: CONFLICT within decisions_queue: line 24 uses F1/F2/F3c as offline tests
- [experiment H far-spawn criterion] "- **Criterion F1:** horizontal p95 ≤ **0.10 m** (5 × σ_pos) and yaw p95 ≤ **2°**. If it fails: stop and report" — `METHODOLOGY.md:11316` — note: CONFLICT: experiment H far-spawn on-ground fix-error criterion
- [offline tests (F-tests)] "### PRE-REGISTRATION — offline tests F1, F2, F3 and the post-D15 FGO-vs-UKF with-heading comparison (written before any is run)" — `METHODOLOGY.md:7877`
- [offline tests (F-tests)] "**F1 — robust weighting on bad headings.**" — `METHODOLOGY.md:7899`
- [offline tests (F-tests)] "(F1, F2, F3c, C0); record the weight difference as structural (mechanism untested: fixed-lag window / marginal" — `docs/decisions_queue.md:24` — note: same doc uses (F1)-(F4) as backlog options at lines 161-166
- [real-flight readiness items] "| F1 | Mocap client: Vicon/OptiTrack stream (VRPN/NatNet) → ROS 2 pose with host stamps and Pi/ground-station receipt stamps | not built | a, b | No mocap client exists in the repo; only `eval/mocap_align.py` (offline) and `wall_watch.py` mention mocap. | 1–2 d (assumes an existing ROS 2 driver for the system) | U7 |" — `docs/real_flight_readiness.md:115` — note: CONFLICT: readiness item (mocap watcher chain), not offline test or finding
- [real-flight readiness items] "- **the mocap watcher chain:** F1 (live client), F2, F3, F4, and the G1–G11 gaps of plan §7.2;" — `docs/minimal_real_flight_plan.md:462`
- [thesis figures] "| F1 scorecard | 3 estimators × 8 experiments; numbers.md §6.1, §6.2, §6.6, §15, §16, §17.2 and the claims table; JSONs as in the pack | 16/16 | none needed | see "Scorecard categories" below |" — `docs/handovers/2026-10-15_thesis_figures.md:22` — note: 2026-10-15 set (commit 7778cd6)
- [thesis figures] *(superseded)* "**Revision 2026-10-16.** F1 (`F1_scorecard`) became table T1; F3 (`F3_accuracy_without_and_with_heading`) became table T2; F4 (`F4_blank_floor_flow_loss`) became table T3; F8 (`F8_H_tag_loss_drift`) became table T5. The old figure files are removed from this folder; they remain in the git history (commit `7778cd6`, ..." — `docs/thesis/figures_thesis/index.md:5` — note: renamed to T1 in e202552
- [thesis figures] *(superseded)* "F6, F7), eight tables (T1–T8; each also as LaTeX booktabs and markdown in docs/thesis/tables/) and the appendix tables A1–A3. F1, F3, F4 and" — `docs/thesis/figures_thesis/thesis_figures_combined.pdf p.1` — note: PDF statement of the F1/F3/F4/F8 -> T1/T2/T3/T5 rename (continues on next text line)
- [thesis figures] *(used, not defined here)* "| corridor_textured | CURRENT | `dsn_tex_r1–r10` (standard-sensor baseline); `ds_tex_r1–3` (compass on, reference); about 26 checks and shadow runs | thesis F1 (standard sensors), F3 left; pack F03; numbers §1, §2, §6.1, §6.5, §7, §8, §14, §18 |" — `docs/thesis/world_images/index.md:22` — note: STALE: world_images index (6d3254b, after e202552) still cites thesis F1/F3/F4/F8, which are now tables T1/T2/T3/T5
- [thesis figures] *(used, not defined here)* "reported in: thesis F1 (standard sensors), F3 left; pack F03; numbers §1, §2, §6.1, §6.5, §7, §8, §14, §18" — `docs/thesis/world_images/worlds_combined.pdf p.1` — note: STALE: worlds PDF cites pre-e202552 thesis F1/F3/F4/F8 (now tables)
- [watcher bench findings] "- **F1 (B8a, one run, n = 1, GUIDED): flow loss on EKF3 was followed by a fast lateral excursion, with no EKF failsafe" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:363` — note: CONFLICT with offline test / readiness item of the same number

### `F01`

- [final results pack figures] "| F01 | `plots/final_results_pack/F01_closed_loop_paths_full.png`: Closed-loop true paths at full speed: EKF3 and UKF, with and without the camera heading | CURRENT | `eval/figs_final_pack.py`; paths: dataflash SIM of cl_a_tex, cl_bcpp_tex_r1–r3, cl_ukf_a_tex, cl_ukf_b_tex_r1–r3; contact times and B2: ..." — `docs/thesis/final_results_pack_index.md:11` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8
- [final results pack figures] "F01 Closed-loop true paths at full speed: EKF3 and UKF, with and without the camera heading [CURRENT]" — `docs/thesis/final_results_pack.pdf p.1`

### `f1`

- [archive folders (~/thesis_data)] `f1 (folder)` "# The F1 hard-gated arms are the Phase 4 heading arms (phase4 stage). F1 CALIBRATION (~/thesis_data/f1/f1cal.jobs) is NOT" — `batches/final_rerun/F.jobs:4`

### `F2` — **CONFLICT: 5 meanings** (see flags §b)

- [D12/D19 take-off backlog fix options] "- (F2) The D11 speed-up: C++ factors, or GTSAM's native factors in place of Python `CustomFactor`." — `docs/d12_fgo_backend_report.md:39` — note: CONFLICT: backlog-fix option, not the offline test
- [D12/D19 take-off backlog fix options] "- (F2) the D11 speed-up (days; needed for a real drone);" — `docs/decisions_queue.md:164`
- [offline tests (F-tests)] "**F2 — intermittent heading, evaluated in hindsight.**" — `METHODOLOGY.md:7926`
- [real-flight readiness items] "| F2 | Watcher logic: capture-volume box, process liveness, tilt | needs adapting for real sensors | a, b | `sim/tools/wall_watch.py` (`--box`, `--watch-process`, `--dep-loss land`; fail-closed heartbeat contract at `:134-146`). Its input is the Gazebo `/ground_truth/pose`, and its stop actions kill SITL processes ..." — `docs/real_flight_readiness.md:116` — note: CONFLICT: readiness item (mocap watcher chain), not offline test or finding
- [thesis figures] "| F2 | figure | `F2_heading_stops_sideways_drift.png`, `F2_heading_stops_sideways_drift.pdf` | The camera heading stops the sideways drift: without it every estimator flies into the west wall | CURRENT | 4/4 | none needed |" — `docs/thesis/figures_thesis/index.md:13` — note: current thesis figure (rev. 2026-10-16)
- [thesis figures] "| F2 heading stops drift (pack F01 + F08 + F02) | half-speed paths (dataflash SIM) for EKF3 (`cl_a_tex_half`, `cl_bcpp_*_half`), UKF v2 (`*_half_v2`) and FGO v3 (`*_half_v3`); heading error from XKF1 / XUKO / XFGO on ONE shared y-scale; B2/B3 from `closed_loop_*.json` | 8/8 | none needed | no-heading curves are cut 3 ..." — `docs/handovers/2026-10-15_thesis_figures.md:23` — note: 2026-10-15 definition; rebuilt one-panel 2026-10-16
- [watcher bench findings] "- **F2: after a LAND that began with lateral motion, ArduCopter's land detector sometimes did not trip on flow-only" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:371` — note: CONFLICT with offline test / readiness item of the same number
- [watcher bench findings] "- **F2 (SAFETY):** ArduCopter's land detector sometimes did not trip on flow-only EKF3. Once the vehicle tipped over" — `METHODOLOGY.md:13609`

### `F02`

- [final results pack figures] "| F02 | `plots/final_results_pack/F02_closed_loop_heading_error_full.png`: Closed-loop heading error at full speed, with and without the camera heading | CURRENT | `eval/figs_final_pack.py`; curves: dataflash XKF1 / XUKO / SIM of the F01 trials; p95 and max: eval/results/closed_loop_<trial>.json (B3) | §15: B3 ..." — `docs/thesis/final_results_pack_index.md:12` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8

### `F2mask` — **UNDEFINED** (see flags §a)

- [offline tests (F-tests)] *(used, not defined here)* "job: f2u_fwdc_tex_r1 cd /home/makerspace/thesis_ws && OPENBLAS_NUM_THREADS=1 F_TAG=F2mask F_MASK=30/30 nice -n 10 /home/makerspace/venv-evo/bin/python src/estimators/ukf_replay.py fwdc_tex_r1 heading" — `docs/handovers/2026-10-09_final_rerun_dryrun.txt:229` — note: run tag of the F2 masked replays; no prose definition
- [offline tests (F-tests)] *(used, not defined here)* "- every F-variant (F2mask, F3d, F3bd, F3cd; the C0/F2 pattern run PATnocap, reconstructed as" — `METHODOLOGY.md:9622` — note: listed as "F-variant" only

### `F3` — **CONFLICT: 5 meanings** (see flags §b)

- [D12/D19 take-off backlog fix options] "- (F3) Temporary keyframe decimation while behind (a longer `kf_dt` when lag > threshold). This changes" — `docs/d12_fgo_backend_report.md:41` — note: CONFLICT: backlog-fix option, not the offline test
- [D12/D19 take-off backlog fix options] "- (F3) keyframe decimation while behind (tuning, not recommended);" — `docs/decisions_queue.md:165`
- [offline tests (F-tests)] "**F3 — large initial heading error (nonlinearity).**" — `METHODOLOGY.md:7945`
- [real-flight readiness items] "| F3 | Heartbeat path to the FC and an FC-side "no heartbeat → LAND" second layer (Lua or companion), plus a watcher → `LAND` MAVLink command | not built | a, b | In SITL the heartbeat is a local file (`<out>/watch_heartbeat`) that `fly_trial.py` reads (`WATCH_HEARTBEAT`, `fly_trial.py:303-315`). Plan §7 requires a ..." — `docs/real_flight_readiness.md:117` — note: CONFLICT: readiness item (mocap watcher chain), not offline test or finding
- [real-flight readiness items] "| F3 | Watcher heartbeat → FC; FC-side LAND layer | 2, U | SW+HW | code 1.5–2 d; bench 0.5–1 d | closes G5, G6, G9, G11 | code DONE; bench WAITS; **F6 ruling OPEN** |" — `docs/real_flight_readiness_by_rung.md:145` — note: same doc says "F6 ruling OPEN" = watcher finding F6, a different series
- [thesis figures] "| F3 accuracy without (m) / with (cm) heading (pack F03 + F04 + F05) | dsn_tex r1–r9 and the 6 camera bags without heading; UKF/FGO heading arms in cm; EKF3 slot says "no offline heading arm"; the checkerboard plain-wall columns are shaded with "no heading benefit claimed" | 9/9 | none needed | F05 (Phase 5 ..." — `docs/handovers/2026-10-15_thesis_figures.md:24` — note: 2026-10-15 set
- [thesis figures] *(superseded)* "**Revision 2026-10-16.** F1 (`F1_scorecard`) became table T1; F3 (`F3_accuracy_without_and_with_heading`) became table T2; F4 (`F4_blank_floor_flow_loss`) became table T3; F8 (`F8_H_tag_loss_drift`) became table T5. The old figure files are removed from this folder; they remain in the git history (commit `7778cd6`, ..." — `docs/thesis/figures_thesis/index.md:5` — note: F3 became table T2 (e202552)
- [watcher bench findings] "- **F3 (B5b-noflag set-up): a source with no tracking flag and a perfectly still vehicle never confirms** (bit-identical" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:375` — note: CONFLICT with offline test / readiness item of the same number

### `F03`

- [final results pack figures] "| F03 | `plots/final_results_pack/F03_offline_textured_no_heading.png`: Offline accuracy, textured floor, no heading; the confirmatory EKF3 − FGO test | CURRENT | `eval/figs_final_pack.py`; eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (ate_a_cruise '+0.00'); dsn_paired_test.json | §6.1 (r1–r3 values, means, ..." — `docs/thesis/final_results_pack_index.md:13` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8

### `F3bd` — **UNDEFINED** (see flags §a)

- [offline tests (F-tests)] *(used, not defined here)* "- every F-variant (F2mask, F3d, F3bd, F3cd; the C0/F2 pattern run PATnocap, reconstructed as" — `METHODOLOGY.md:9622` — note: only occurrence; presumably the F3b run tag, but not defined

### `F3cd`

- [offline tests (F-tests)] "- **Command:** `F_TAG=F3cd$d F_YAW0_DEG=$d F_YAW0_SIGMA_DEG=30 F_NO_YAWCAP=1 F_HDG_FROM_CRUISE=1`, with" — `METHODOLOGY.md:8952` — note: F3cd = the F_TAG run tag of the F3c runs (with delta appended)
- [offline tests (F-tests)] "| F1 (test), F2, F3, F3b, F3c, PATnocap | `ftests` | `batches/final_rerun/F.jobs` (73 jobs) + `f1_eval test cauchy:2.385`, `f23_eval f2/f3`, `f3b_eval`, `f3c_eval --tag F3cd --deltas 10,30` | d27_regen (evaluators only) | `fruns.jobs` and `f3b.jobs` lived only in `~/thesis_data`; they are now **vendored** verbatim. ..." — `docs/handovers/2026-10-09_final_rerun_pipeline.md:133`

### `F04`

- [final results pack figures] "| F04 | `plots/final_results_pack/F04_offline_with_heading_C0.png`: Offline with the camera heading: FGO against UKF (C0) | CURRENT | `eval/figs_final_pack.py`; eval/results/phase4_fwdc_evo.json, phase4_fwdplainc_evo.json (UKF_heading, FGO_heading, EKF3); cross-checked against phase4_*_arms.json | §6.4 (EKF3 ..." — `docs/thesis/final_results_pack_index.md:14` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8

### `f4_`

- [trial dataset prefixes] "# Plan step 2(a) (METHODOLOGY "PRE-REGISTRATION — plan step 2"): fresh open-loop flights, interleaved by world; truth flies" — `batches/f4_robust.conf:1` — note: "f4" itself is never expanded; results file eval/results/f4_test.json. NOT the watcher finding F4 (METHODOLOGY 13611) nor an F-test (F1-F3c)
- [trial dataset prefixes] "- **plain walls over the checkerboard floor:** `corridor_textured_fwdplainc` → `f4_fwdplainc_tex_r1..r6`; ... **textured walls, end-wall region:** `corridor_textured_fwdc` → `f4_fwdc_tex_r1..r6`." — `METHODOLOGY.md:9704`

### `F5` — **CONFLICT: 2 meanings** (see flags §b)

- [thesis figures] "| F5 | figure | `F5_T_tags_known_positions.png`, `F5_T_tags_known_positions.pdf` | Fewer tags, larger live errors (no live ordering claimed); the FGO's hindsight batch stays at 1–3 cm | CURRENT | 8/8 | none needed |" — `docs/thesis/figures_thesis/index.md:14` — note: current thesis figure (rev. 2026-10-16)
- [watcher bench findings] "- **F5: B5a / B5b-noflag bound.** "Stale within 0.5 s" with a 0.5 s stale limit cannot be met (detection is 8–10 ms" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:388`
- [watcher bench findings] "(`docs/handovers/2026-10-11_watcher_sitl_bench.md` finding F5) declared stale at +0.508 s (B5a) and frozen at" — `docs/real_flights_plan.md:562`

### `F05`

- [final results pack figures] "| F05 | `plots/final_results_pack/F05_drift_decomposition.png`: Heading-driven against residual cross-track, with and without the camera heading | CURRENT (JSON only, unchecked) | `eval/figs_final_pack.py`; eval/results/phase5_analysis.json (decomposition: xtrack_head_m, xtrack_resid_m) | none (METHODOLOGY Phase 5 ..." — `docs/thesis/final_results_pack_index.md:15` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8

### `F6` — **CONFLICT: 2 meanings** (see flags §b)

- [thesis figures] "| F6 | figure | `F6_O_outdoor_indoor.png`, `F6_O_outdoor_indoor.pdf` | Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight keeps the error near 1 m | CURRENT | 4/4 | none needed |" — `docs/thesis/figures_thesis/index.md:15` — note: current thesis figure (rev. 2026-10-16)
- [thesis figures] "| F6 O (pack F11) | O_r1 time series (TUMs, XKF1 via the `/imu/time_ref` clock map) and 3-flight indoor RMSE on a shared y-axis; lines mark the far end (60 s) and the reverse (63 s) | 9/9 | none needed | the indoor sensor set is in the caption; H-O2 ratio 1.71 against numbers.md 1.72 is a last-digit rounding match |" — `docs/handovers/2026-10-15_thesis_figures.md:27` — note: 2026-10-15; time-trace only after 2026-10-16
- [watcher bench findings] "- **F6: the LAND retry policy can violate B10b (the build handover's open question 5, now with evidence).** B7b lost" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:383`
- [watcher bench findings] "- **F6 (SAFETY):** the LAND retry (every 0.3 s until acknowledged) could override a pilot who has taken ALT_HOLD." — `METHODOLOGY.md:13607`

### `F06`

- [final results pack figures] "| F06 | `plots/final_results_pack/F06_blank_flow_loss.png`: Loss of flow aiding on the blank floor | CURRENT | `eval/figs_final_pack.py`; eval/results/blank_behaviour.json (along_m, cross_m at +10/+30/+60/+120 s; EKF3 validity) | §6.2 (+10/+30/+60 s rows, end-of-cruise †, EKF3 invalid); claim 10 | 3/3 |" — `docs/thesis/final_results_pack_index.md:16` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8

### `F7` — **CONFLICT: 2 meanings** (see flags §b)

- [thesis figures] "| F7 | figure | `F7_L_loop_closure.png`, `F7_L_loop_closure.pdf` | Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps | CURRENT | 5/5 | none needed |" — `docs/thesis/figures_thesis/index.md:16` — note: current thesis figure (rev. 2026-10-16)
- [watcher bench findings] "- **F7 (n = 1; caused by the harness, amendment A9).** A Gazebo carry that rotated the vehicle by a yaw the gyros" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:405`
- [watcher bench findings] "- F7: arming is allowed with a 22° yaw error;" — `METHODOLOGY.md:13886`
- [watcher bench findings] "| D11 | **F7 and U4 as flown:** the sheet's yaw-check line filled in (\|diff\| ≤ 5°); the `ARM` event to take-off (the first `CTUN`/`RFND` climb) ≤ 5 s | yes. A deviation is recorded; it does not change the classification |" — `docs/rung1_flight_cards.md:316` — note: F7 here = the F7 yaw check (finding F7 remedy)

### `F07`

- [final results pack figures] "| F07 | `plots/final_results_pack/F07_f1_robust_tradeoff.png`: F1: robust heading weighting trade-off | CURRENT | `eval/figs_final_pack.py`; eval/results/f1_test.json | §15.2 F1 row; claim 27 | 4/4 |" — `docs/thesis/final_results_pack_index.md:17` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8
- [final results pack figures] *(superseded)* "- **Caption:** Pass/fail table for the F1 robust-weighting test (replaces pack F07), the L compute cost (diagnostic, replaces F13; linear values, no plot) and the build ablations: UKF v1 against v2; FGO v2 (noise fix only) against v3 (final) and the v4 node; the flown-FGO OLD-priors note." — `docs/thesis/figures_thesis/index.md:274` — note: thesis A3 replaces pack F07 and F13

### `F8` — **CONFLICT: 2 meanings** (see flags §b)

- [thesis figures] "| F8 H (pack F14) | FLYING estimators only, grouped by loss duration: EKF3 S1 + S1 far, UKF S2v2, FGO S3v2; effective drift, mm | 6/6 | **bands up to 400 mm next to drifts ≤ 31 mm: linear axis clipped at 60 mm; the in-range 50 mm bands are drawn as lines, and the off-scale bands as arrows labelled with their value** | ..." — `docs/handovers/2026-10-15_thesis_figures.md:29` — note: 2026-10-15 set
- [thesis figures] *(superseded)* "**Revision 2026-10-16.** F1 (`F1_scorecard`) became table T1; F3 (`F3_accuracy_without_and_with_heading`) became table T2; F4 (`F4_blank_floor_flow_loss`) became table T3; F8 (`F8_H_tag_loss_drift`) became table T5. The old figure files are removed from this folder; they remain in the git history (commit `7778cd6`, ..." — `docs/thesis/figures_thesis/index.md:5` — note: F8 became table T5 (e202552)
- [thesis figures] *(superseded)* "- **Removed** (`git rm`, still in history at `7778cd6`): F1→T1, F3→T2, F4→T3, F8→T5." — `docs/handovers/2026-10-16_thesis_figures_rev.md:16` — note: F1→T1, F3→T2, F4→T3, F8→T5
- [watcher bench findings] "- **F8 (n = 1; cause not established).** Before the first B6b run 1 attempt, EKF3's velocity on the ground diverged" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:414`
- [watcher bench findings] "- F8: EKF3's velocity runs away on the ground before arming (cause unknown);" — `METHODOLOGY.md:13887`
- [watcher bench findings] "| **F8** (EKF3 velocity runs away on the ground before arming) | Flow drops out on the final descent, so the velocity error at touchdown is the error EKF3 already had. On the ground the flow innovation gate locks that axis out, and the other axis keeps every fallback switched off. A ~0.9° roll error then ramps the ..." — `docs/handovers/2026-10-12_f8_investigation.md:20`

### `F08`

- [final results pack figures] "| F08 | `plots/final_results_pack/F08_closed_loop_paths_half.png`: Closed-loop true paths at half speed: EKF3, UKF (original and v2), FGO (original, v3, robust) | CURRENT | `eval/figs_final_pack.py`; paths: dataflash SIM of the trials named in each panel title (cl_*_half, *_v2, *_v3); contact and B2: ..." — `docs/thesis/final_results_pack_index.md:18` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8

### `F09`

- [final results pack figures] "| F09 | `plots/final_results_pack/F09_T_hindsight_gain_vs_gap.png`: T: the hindsight gain grows with the gap for the FGO, not for the single-pass RTS-UKF | CURRENT | `eval/figs_final_pack.py`; eval/results/expT/T_*.json (gaps), t_aggregate.json | §16.1 (H-T1, P-T2); claim 17 | 3/3 |" — `docs/thesis/final_results_pack_index.md:19` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8

### `F10`

- [final results pack figures] "| F10 | `plots/final_results_pack/F10_T_rmse_by_condition.png`: T: horizontal error by tag density, live and hindsight | CURRENT | `eval/figs_final_pack.py`; eval/results/expT/T_*.json (tracks.*.horiz_err_m.rmse); t_aggregate.json (means) | §16.1 table, P-T3, P-T4, condition D bullet; claims 17, 18 | 4/4 |" — `docs/thesis/final_results_pack_index.md:20` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8

### `F11`

- [final results pack figures] "| F11 | `plots/final_results_pack/F11_O_indoor_hindsight.png`: O: indoor error with GNSS outside only; hindsight reconstruction and EKF3's return jump | CURRENT | `eval/figs_final_pack.py`; eval/results/expO/O_*.json; curves: O_r1 room_ukf/, room_fgo/ TUMs (FGO-only re-run outputs), dataflash XKF1 about EKF3's origin ..." — `docs/thesis/final_results_pack_index.md:21` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8

### `F12`

- [final results pack figures] "| F12 | `plots/final_results_pack/F12_L_lap_by_lap.png`: L: tag re-identification bounds the drift lap by lap | CURRENT | `eval/figs_final_pack.py`; eval/results/expL/T_A_r*_t245.json (per_lap_rmse_m, rmse_m) | §16.3 table and bullets; claims 23, 24 | 5/5 |" — `docs/thesis/final_results_pack_index.md:22` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8

### `F13`

- [final results pack figures] "| F13 | `plots/final_results_pack/F13_L_compute_cost.png`: L: per-update solve time and wall time (diagnostic) | CURRENT | `eval/figs_final_pack.py`; ~/thesis_data/trials/T_A_r{1,2,3}/lc_fgo_{lc,nolc}_t245/stats.json (mtime 2026-10-10 19:00–21:35) | §16.3 'Computational cost' bullets (DIAGNOSTIC) | 3/3 |" — `docs/thesis/final_results_pack_index.md:23` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8

### `F14`

- [final results pack figures] "| F14 | `plots/final_results_pack/F14_H_tag_loss_drift.png`: H: hold error and tag-loss drift per loss duration, EKF3 / UKF / FGO, shadow and flying | CURRENT | `eval/figs_final_pack.py`; eval/results/expH/s1_r{1,2,3}.json, s1far_r{1,2,3b}.json, s2v2_r*.json, s2_r*.json, s3v2_r*.json, s3_r*.json ..." — `docs/thesis/final_results_pack_index.md:24` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8
- [final results pack figures] "- New: F14 (the tag experiment: hold and drift per loss duration, all three estimators, shadow and flying) and" — `METHODOLOGY.md:13531`

### `F15a`

- [final results pack figures] "| F15a | `plots/final_results_pack/F15a_closed_loop_summary_corridor.png`: Closed-loop summary (1/2): corridor sets, every flown build | CURRENT | `eval/figs_final_pack.py`; eval/results/closed_loop_<trial>.json for cl_a_tex, cl_b_tex_r*, cl_bcpp_tex_r*(_half), cl_a_tex_half, cl_ukf_a_tex(_half)(_v2), ..." — `docs/thesis/final_results_pack_index.md:25` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8
- [final results pack figures] *(superseded)* "- **Caption:** Pass/fail of every closed-loop corridor set (replaces pack F15a), computed from the closed-loop score files, with the build ablations labelled: UKF v1 (pre-jitter fix) against v2 (final); FGO original, robust, v2 (noise fix only, ABLATION) and v3 (final, OLD priors)." — `docs/thesis/figures_thesis/index.md:237` — note: thesis A1 replaces pack F15a

### `F15b`

- [final results pack figures] "| F15b | `plots/final_results_pack/F15b_closed_loop_summary_H_safety.png`: Closed-loop summary (2/2): H hold sets and the safety tests | CURRENT | `eval/figs_final_pack.py`; eval/results/expH/s1*_r*.json, s2*_r*.json, s3*_r*.json; expH/safety_*.json | §17 (S1), §17.1 (S2/S3 sets), §17.2 (comparative criteria, ..." — `docs/thesis/final_results_pack_index.md:26` — note: pack figure (2026-10-11); distinct from thesis figure series F1–F8
- [final results pack figures] *(superseded)* "- **Caption:** Experiment H sets (S1, S1 far, S2/S2v2, S3/S3v2) with hold error, drift, lockouts and the P-H5 bands, and every safety-test run with its as-worded verdict, including the v3 (UKF) and v4 (FGO, NEW priors) re-tests (replaces pack F15b)." — `docs/thesis/figures_thesis/index.md:254` — note: thesis A2 replaces pack F15b

### `fgo_cpp_*`

- [eval/results naming] `fgo_cpp_* (eval/results)` "### 2f: C++ FGO on ARM64, EMULATED (handover `docs/handovers/2026-10-11_fgo_arm64.md`; `eval/results/fgo_cpp_arm64/RESULTS.md`)" — `METHODOLOGY.md:13639`
- [eval/results naming] `fgo_cpp_* (eval/results)` "- **The install gate** was pre-written (`eval/results/fgo_cpp_equiv_d18/INSTALL_GATE.md`), with the 2026-10-09 bands" — `METHODOLOGY.md:13621`

### `fgo_cpp_shadow_i / _ii / _iii`

- [shadow and development runs] "# (i) cpp, 0.20 s, time_ref" — `docs/handovers/2026-10-08_fgo_cpp_stage5_sitl_flights.md:70` — note: roman numerals = the three stage-5 configurations (i) 0.20 s time_ref, (ii) 0.10 s time_ref, (iii) 0.10 s causal
- [shadow and development runs] "# (ii) cpp, 0.10 s, time_ref : as (i) with FGO_CPP_DELAY=0.10 and --trial-name fgo_cpp_shadow_ii ... # (iii) cpp, 0.10 s, causal : as (i) with FGO_CPP_DELAY=0.10 FGO_CPP_IMU_STAMP=causal and --trial-name fgo_cp ..." — `docs/handovers/2026-10-08_fgo_cpp_stage5_sitl_flights.md:75`
- [shadow and development runs] "### FGO C++ stage 5 RESULT (`fgo_cpp_shadow_{i,ii,iii}`, scored by `eval/fgo_cpp_sitl_check.py`; `eval/results/fgo_cpp_sitl_*.json`)" — `METHODOLOGY.md:11406`

### `fgo_dev_smoke1..3`

- [shadow and development runs] "### D19 FGO backend: development smoke tests (DEVELOPMENT, not gates; FGO in shadow, half speed)" — `METHODOLOGY.md:7988`
- [shadow and development runs] "- **`fgo_dev_smoke2`** (simulator truth, 60 s cruise): states at 30 Hz, but **yaw 90° off and N/E" — `METHODOLOGY.md:7997`

### `fgo_groundtest_half`

- [ground tests (gt_ / _groundtest)] "**Ground test `fgo_groundtest_half` (`FGO=1 GROUND_TEST=60`):**" — `METHODOLOGY.md:8075`

### `fgo_shadow_half_a2 / _a3`

- [shadow and development runs] "### PRE-REGISTRATION: D25 confirming shadow run `fgo_shadow_half_a2` (recorded before the run) ... - As `fgo_shadow_half_a`: simulator truth flies, no heading." — `METHODOLOGY.md:9155`
- [shadow and development runs] "### D25 confirming shadow, first attempt `fgo_shadow_half_a2`: EXECUTION ERROR (EKF3 flew, not truth); the D25 node behaviour is shown nonetheless; re-run as `fgo_shadow_half_a3`" — `METHODOLOGY.md:9177`
- [shadow and development runs] "**Re-run `fgo_shadow_half_a3`, with the pre-registration unchanged (C1–C3, FG1–FG3, prediction).** The command is" — `METHODOLOGY.md:9205`

### `fgo_shadow_half_a / _b`

- [shadow and development runs] "### FGO shadow run (a) `fgo_shadow_half_a` (no heading, simulator truth, half speed): FG1, FG2, FG3b PASS; **FG3 FAILS on position and velocity maxima**. STOPPE ..." — `METHODOLOGY.md:8558`
- [shadow and development runs] "### FGO shadow run (b) `fgo_shadow_half_b` (heading, truth flies, half speed): D25 C1–C3, FG1, FG2, FG3b PASS; FG3 fails as worded at the climb top only (as (a) ..." — `METHODOLOGY.md:9252`

### `fgo_shadow_sitl_tex{,2,3,4}`

- [shadow and development runs] "Four open-loop textured flights (`fgo_shadow_sitl_tex{,2,3,4}`). The vehicle flew on simulator truth," — `METHODOLOGY.md:6676` — note: numeric suffix 2-4 = flight index of four

### `fgo_shadow{,2,3,4}`

- [batch state names] `fgo_shadow{,2,3,4} (batch stats dirs)` "in `~/thesis_data/batches/fgo_shadow{,2,3,4}/`." — `METHODOLOGY.md:6678`

### `fgodev / fgodev2 / fgodev3` — **UNDEFINED** (see flags §a)

- [batch state names] *(used, not defined here)* "fgodev.log" — `~/thesis_data/batches/fgodev.log`
- [batch state names] *(used, not defined here)* "fgodev2.log" — `~/thesis_data/batches/fgodev2.log`
- [batch state names] *(used, not defined here)* "fgodev3.log" — `~/thesis_data/batches/fgodev3.log`

### `fgt / gth / gth2 / gthb` — **UNDEFINED** (see flags §a)

- [batch state names] *(used, not defined here)* "fgt.log" — `~/thesis_data/batches/fgt.log`
- [batch state names] *(used, not defined here)* "gth2.log" — `~/thesis_data/batches/gth2.log`
- [batch state names] *(used, not defined here)* "gthb.log" — `~/thesis_data/batches/gthb.log`

### `final_ / final2_`

- [batch state names] `final_ / final2_ (batches)` "# * NEW state / snapshot / archive / batch names: ~/thesis_data/batches/final_rerun2, eval/results_pre_final2, ... # ~/thesis_data/pre_final2_trials, batches final2_*, Phase 5b sandbox phase5b_final2 (all DIE if they exis ..." — `eval/final_rerun_pipeline.sh:23`
- [batch state names] `final_ / final2_ (batches)` "BP=final2; SB5=phase5b_final2" — `eval/final_rerun_pipeline.sh:50` — note: final_<stage> (first final re-run, BP=final at line 53) vs final2_<stage> (FGO-only pass)
- [batch state names] `final_ / final2_ (batches)` "# FGO-ONLY PASS (FINAL_FGO_ONLY=1; user ruling 2026-10-10, METHODOLOGY "RULINGS (user, 2026-10-10): FGO initial yaw sigma"" — `eval/final_rerun_pipeline.sh:21`

### `final_<stage> batch names`

- [final re-run job lists (batches/final_rerun)] "jobs_stage "$JOBS_DIR/room_H.jobs" ${BP}_room_H" — `eval/final_rerun_pipeline.sh:442` — note: batch state = ${BP}_<stage>, BP = final | final2

### `fsha / fsha3 / fshb / fshbr` — **UNDEFINED** (see flags §a)

- [batch state names] *(used, not defined here)* "fsha.log" — `~/thesis_data/batches/fsha.log`
- [batch state names] *(used, not defined here)* "fsha3.log" — `~/thesis_data/batches/fsha3.log`
- [batch state names] *(used, not defined here)* "fshbr.log" — `~/thesis_data/batches/fshbr.log`

### `fwd_`

- [trial dataset prefixes] "**Dataset.** `fwd_{tex,trans,blank}_r{1,2,3}`: the three `corridor_*_fwd` worlds × 3 ... repeats, 300 s, 0.5 m/s, 2.0 m, no compass (`gnss_denied_nomag.parm`)," — `METHODOLOGY.md:1845`
- [trial dataset prefixes] *(superseded)* "Superseded because the forward view includes the sky: ... the `fwd_*` dataset;" — `METHODOLOGY.md:2362`
- [trial dataset prefixes] *(superseded)* "SUPERSEDED (user ruling, 2026-09-24): kept, labelled, not analysed further." — `~/thesis_data/trials/fwd_tex_r1/SUPERSEDED.txt:1` — note: identical SUPERSEDED.txt in all 9 fwd_* dirs

### `fwdc_`

- [trial dataset prefixes] "**Datasets.** `fwdc_*` (textured walls = upper bound) and `fwdplainc_*` (plain walls = ... featureless case)." — `METHODOLOGY.md:2381` — note: the trailing "c" (ceiling) is never spelled out as a letter expansion; the worlds are the ceiling worlds _fwdc
- [trial dataset prefixes] "# Ceiling datasets fwdc_* (textured walls, upper bound) + fwdplainc_* (plain walls, featureless)." — `batches/ceiling_datasets.conf:1`
- [trial dataset prefixes] "| **Forward-camera corridor worlds** | **USE** `sim/worlds/corridor_{textured,blank,transition}_fwdc.sdf` (line-textured walls = UPPER BOUND) and `..._fwdplainc.sdf` (plain walls = featureless case), both with a plain ceiling (`corridor_ceiling`). The no-ceiling `_fwd`/`_fwdplain` worlds and the `fwd_*` dataset are ..." — `CLAUDE.md:40` — note: same meaning restated

### `fwdplain_`

- [trial dataset prefixes] "**Dataset.** `fwdplain_{tex,trans,blank}_r{1,2,3}`: the three `_fwdplain` worlds × 3" — `METHODOLOGY.md:2235` — note: planned only (Phase 2b); never flown as fwdplain_* (no such dirs on disk)
- [trial dataset prefixes] *(superseded)* "### Ceiling datasets — pre-registration (2026-09-24, before any ceiling data exists; supersedes the Phase 2b plan for `fwdplain_*`)" — `METHODOLOGY.md:2372`

### `fwdplainc_`

- [trial dataset prefixes] "**Datasets.** `fwdc_*` (textured walls = upper bound) and `fwdplainc_*` (plain walls = ... featureless case)." — `METHODOLOGY.md:2381`
- [trial dataset prefixes] "# Ceiling datasets fwdc_* (textured walls, upper bound) + fwdplainc_* (plain walls, featureless)." — `batches/ceiling_datasets.conf:1`

### `ground_test_<trial>.json`

- [eval/results naming] "`eval/results/ground_test_gt_heading_cpp.json`; metadata records `impl: cpp`." — `METHODOLOGY.md:6074` — note: pattern by usage: ground_test_<trial>.json from eval/ground_test_check.py

### `gt_`

- [ground tests (gt_ / _groundtest)] `gt_ (gt_heading_*)` "### Closed-loop Part 1: SITL ground test run 1, `gt_heading_1` (2026-09-29): G4 STOP (latency above the horizon)" — `METHODOLOGY.md:5737` — note: COLLISION: "gt_" = ground test here; "GT" means ground truth everywhere else (e.g. /ground_truth/pose)

### `gt_heading_2 / gt_heading_3`

- [ground tests (gt_ / _groundtest)] "### Ground test run 2, `gt_heading_2` (D = 60, `every_n` 3, 330 s armed hold): G5.3 FAILS on drops → switch to `every_n` 4 (as pre-registered)" — `METHODOLOGY.md:5928`
- [ground tests (gt_ / _groundtest)] "### Ground test run 3, `gt_heading_3` (D = 60, `every_n` 4, 330 s armed hold): ALL PASS → sets (a) and (b) proceed (ruling 5)" — `METHODOLOGY.md:5958`

### `gt_heading_cpp`

- [ground tests (gt_ / _groundtest)] "### C++ heading path — SITL ground test `gt_heading_cpp` (DIAGNOSTIC; `HEADING_IMPL=cpp`, `every_n` 4, 330 s armed hold, otherwise as run 3)" — `METHODOLOGY.md:6072`

### `gt_heading_cpp2`

- [ground tests (gt_ / _groundtest)] "### D2 ground test with the C++ node, `gt_heading_cpp2` (`VISO_DELAY_MS 38`, `every_n` 4, 330 s armed hold): ALL PASS → set (b) re-fly proceeds" — `METHODOLOGY.md:6411`

### `gt_heading_half / _half2 / _half_b`

- [ground tests (gt_ / _groundtest)] "- **Run 1, `gt_heading_half`:** stock tree, EKF3, `HEADING=1`, C++ node, `every_n` 4, a 330 s armed" — `METHODOLOGY.md:7832`
- [ground tests (gt_ / _groundtest)] "- **Run 2, `gt_heading_half2`:** the ground test with the new value, G1–G5 as D2. It must pass before" — `METHODOLOGY.md:7842`

### `h10_guard_check`

- [check flights (one-off names)] "# H10 guard verification flight `h10_guard_check`: PRE-REGISTRATION (2026-10-12)" — `docs/h10_guard_check_prereg.md:1`

### `h10_guard_check_side`

- [archive folders (~/thesis_data)] "- the dataflash log `~/thesis_data/h10_guard_check_side/ardupilot.bin` (`00000229.BIN`). `run_trial.sh` copies the" — `docs/handovers/2026-10-12_xuko_u10_h10.md:221`

### `H_`

- [experiment trial names (T/O/H)] `H_ (Experiment H)` "### Experiment H (marker-relative position holding): pre-registration of S0 and S1 (written before any H flight)" — `METHODOLOGY.md:10623` — note: "H" = Experiment H; S0a/S0b/S1/S2/S3 = its stages

### `H_gt_*`

- [ground tests (gt_ / _groundtest)] "### H SITL GROUND TESTS (2026-10-08, `H_gt_fgo`, `H_gt_ukf`): BOTH FAILED. The FGO vehicle crashed; the watcher stopped it correctly. Mechanisms established from the logs (FGO: direct; UKF: from logs ..." — `METHODOLOGY.md:11111`

### `H_ifa_*`

- [experiment trial names (T/O/H)] "**4. In-flight-anchor transient check** (`room_wall_tag_far_occ`, no pre-arm gate; take off with the tag hidden," — `METHODOLOGY.md:11330` — note: "ifa" = in-flight anchor, by the trial list at 11952-11953
- [experiment trial names (T/O/H)] "ifa_ekf3) name=H_ifa_ekf3; cmd=(env H=1 HPROFILE="$B/ifanchor_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far_occ);;" — `tools/run_h_far.sh:10`

### `H_s0a`

- [experiment trial names (T/O/H)] "- **S0a, characterisation:** open loop on simulator truth (`AHRS_EKF_TYPE 10`), the 47-segment sweep" — `METHODOLOGY.md:10636`

### `H_s0b`

- [experiment trial names (T/O/H)] "- **S0b, check flight:** open loop on simulator truth. `TAG_FWD_SEND=1`; EKF3 runs ExtNav with `EK3_SRC1_POSXY 6`," — `METHODOLOGY.md:10652`

### `H_s1_r<k>`

- [experiment trial names (T/O/H)] "**S1 (EKF3 flies; `AHRS_EKF_TYPE 3`, closed loop on the tag-relative estimate):** the H profile of the design, 3" — `METHODOLOGY.md:10661`
- [experiment trial names (T/O/H)] "name="H_s1_r$r"" — `tools/run_expH_s1.sh:9`

### `H_s1far_r<k>`

- [experiment trial names (T/O/H)] "**5. S1 re-fly** (EKF3 flying, ×3, `room_wall_tag_far`, `s1_far_profile.json` = S1's profile with the start at the far" — `METHODOLOGY.md:11341`

### `H_s2_r<k> / H_s3_r<k>`

- [experiment trial names (T/O/H)] "- S0 + S1 run before the Fri 16 Oct freeze. S2 (UKF flies) and S3 (FGO flies) run Mon 19–Fri 23 Oct, each with its own" — `METHODOLOGY.md:10628`
- [experiment trial names (T/O/H)] "s2r[123]) name="H_s2_r${t:3}"; cmd=(env H=1 UKF=1 HPROFILE="$B/s1_far_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_far);;" — `tools/run_h_far.sh:17`

### `H_s2v2 / H_s3v2`

- [re-flight version suffixes _v<N>] "### S2 RE-FLY with the jitter-corrected UKF (`H_s2v2_r{1,2,3}`, `eval/results/expH/s2v2_r*.json`); the original S2 is kept, labelled "old UKF (jitter)"" — `METHODOLOGY.md:12504`
- [re-flight version suffixes _v<N>] "### S3 RE-FLY with the final corrected FGO (noise fix + gated yaw cap; node `f642cd37…`; `H_s3v2_r{1,2,3}`, `eval/results/expH/s3v2_r*.json`)" — `METHODOLOGY.md:12565` — note: "v2" is fused to the stage token (s2v2) rather than a trailing _v2

### `H_safety_*`

- [experiment trial names (T/O/H)] "**1. Option (i) safety tests** (`room_wall_tag_far`, H config; profile: wait_fix at the spawn → 2.4 m move to" — `METHODOLOGY.md:11286`
- [experiment trial names (T/O/H)] "# H option (i) safety tests (pre-registered 2026-10-08), one flight per argument, under the flight lock; stops at the" — `tools/run_h_safety.sh:2`

### `H_wtest_*`

- [experiment trial names (T/O/H)] "# T1 H_wtest_noarm: the watcher is deliberately NOT started -> fly_trial must refuse to arm (no take-off). ... # T2 H_wtest_kill : the watcher is SIGKILLed once the vehicle is airborne -> fly_trial must land." — `tools/test_watch_failclosed.sh:3`

### `half_a_*`

- [batch state names] "# D19: half-speed set (a) re-fly, EKF3 then UKF, sequential." — `~/thesis_data/batches/half_a.sh:2`

### `hb_<trial>`

- [batch state names] "[ -f ~/thesis_data/batches/hb_$n.done ] && continue" — `~/thesis_data/batches/half_b.sh:8` — note: half_b.sh line 2: "D19: half-speed with-heading sets"; "hb" never expanded

### `hoverA / hoverB / hoverC`

- [watcher bench sessions] "- **R3 — sessions.** `ground` (B1a, B1c(i–iv), B0, B1b/B9d, B5c, B6a, B1-native, B7b, **F6c**, B10c, B4a/B4c (A8)," — `docs/handovers/2026-10-12_watcher_bench_rerun.md:29` — note: sessions defined by the bench tests they contain (hoverA: B2a..B5b; hoverB: B5b-noflag..B9-hang; hoverC: B10a, B10b, F6a, F6b; lines 29-32)
- [watcher bench sessions] "B1c-Lua with the 45 s post-reboot settle that the 2026-10-11 Lua re-run needed), `hoverA` (B2a, B2b, B3a, B3b," — `docs/handovers/2026-10-12_watcher_bench_rerun.md:30`

### `ifanchor_profile`

- [Experiment H flight profiles (batches/expH/*.json)] "ifa_ekf3) name=H_ifa_ekf3; cmd=(env H=1 HPROFILE="$B/ifanchor_profile.json" sim/tools/closed_loop_run.sh room_wall_tag_f ..." — `tools/run_h_far.sh:10` — note: used by the in-flight-anchor check H_ifa_* (METHODOLOGY 11330)

### `imu_rate_verify`

- [legacy one-off trials] "### Verification at the new rate (trial `imu_rate_verify`)" — `CLAUDE.md:621`

### `imu_verify2 / nomag_test_long` — **UNDEFINED** (see flags §a)

- [legacy one-off trials] *(used, not defined here)* "| iris_textured | RECORD ONLY | 13: Stage B/C, `smoke_test`, `ekf3_diag_60s`, `imu_rate_verify`, `imu_verify2`, `nomag_test_long`, `sweep_v*`; also the watcher SITL bench (`~/thesis_data/wbench`) | nu ..." — `docs/thesis/world_images/index.md:38`

### `input_path / fgo_gate_conditioning`

- [eval/results naming] `input_path / fgo_gate_conditioning (eval/results)` "### FGO gate-conditioning diagnostic (open item, report only; `docs/handovers/2026-10-09_fgo_gate_conditioning.md`)" — `METHODOLOGY.md:12525`

### `L`

- [final re-run job lists (batches/final_rerun)] `L (.jobs, final_L / final2_L)` "# FINAL re-run, Experiment L (LAST; METHODOLOGY 10452-10563): keyframe FGO with/without loop closure on T_A_r1..r3, cut at" — `batches/final_rerun/L.jobs:1`

### `legacy undefined trials` — **UNDEFINED** (see flags §a)

- [legacy one-off trials] *(used, not defined here)* "geom_fix_verify" — `~/thesis_data/trials/geom_fix_verify` — note: also harness_test, vendor_verify, imu_verify2, nomag_test_long (the last two only listed in world_images/index.md:38)
- [legacy one-off trials] *(used, not defined here)* "harness_test2" — `~/thesis_data/trials/harness_test2` — note: also harness_test, vendor_verify, imu_verify2, nomag_test_long (the last two only listed in world_images/index.md:38)
- [legacy one-off trials] *(used, not defined here)* "verify_nomag" — `~/thesis_data/trials/verify_nomag` — note: also harness_test, vendor_verify, imu_verify2, nomag_test_long (the last two only listed in world_images/index.md:38)

### `lfs_check_tex`

- [check flights (one-off names)] "**Flight** `lfs_check_tex`. It is not part of any dataset. ... World `corridor_textured_fwdc`, flown on simulator truth (`AHRS_EKF_TYPE 10`)." — `METHODOLOGY.md:4192` — note: Check 2b (sideways step); "lfs" never expanded

### `nomag_corridor_baseline`

- [legacy one-off trials] "single-trial residual +5.32 deg/min from `nomag_corridor_baseline` (`257204d`). The current" — `METHODOLOGY.md:881`

### `o_check1`

- [check flights (one-off names)] "**DISCLOSURE: written AFTER one check flight (`o_check1`, same configuration) whose scores were seen.**" — `METHODOLOGY.md:10368`

### `O_r<k>`

- [experiment trial names (T/O/H)] "way back. Indoors lasts about 120 s. Three repeats. `LOG_REPLAY 1`, `LOG_DISARMED 1`." — `METHODOLOGY.md:10310` — note: Experiment O (outdoor_indoor world, GNSS off indoors)
- [experiment trial names (T/O/H)] "name="O_r${rep}${SUFFIX:-}"; conf="batches/expO/${name}.conf"" — `tools/run_expO.sh:8`
- [experiment trial names (T/O/H)] "outdoor_indoor 0.5 2.0 60 O_r1" — `~/thesis_ws/batches/expO/O_r1.conf:1` — note: main-checkout-only conf

### `p0_smoke_tex`

- [check-flight prefixes (phases)] "**Phase 0 smoke test (b) — acceptance, pre-registered before flying.** One new ... textured trial, flown with `run_trial.sh` on the unchanged `dsn_*` configuration" — `METHODOLOGY.md:136`
- [check-flight prefixes (phases)] "**Result — PASS (trial `p0_smoke_tex`, flown 2026-09-24 at `42193a5`).**" — `METHODOLOGY.md:149`

### `p1_`

- [check-flight prefixes (phases)] `p1_ (p1_control_tex, p1_fwd_*)` "| `p1_control_tex` | `corridor_textured`, no forward camera (same-session control) |" — `METHODOLOGY.md:1435` — note: Phase 1 confound-check flights; table rows 1435-1438
- [check-flight prefixes (phases)] `p1_ (p1_control_tex, p1_fwd_*)` "| `p1_fwd_tex` | `corridor_textured_fwd` |" — `METHODOLOGY.md:1436`
- [check-flight prefixes (phases)] `p1_ (p1_control_tex, p1_fwd_*)` *(superseded)* "the check flights `p1_fwd_*` and `p1plain_*`." — `METHODOLOGY.md:2365`

### `p1c_`

- [check-flight prefixes (phases)] "**Check flights (Phase 1c).** One per ceiling world, six in all: ... `p1c_{fwdc,fwdplainc}_{tex,trans,blank}`." — `METHODOLOGY.md:2374`
- [check-flight prefixes (phases)] "# Phase 1c ceiling-world check flights (METHODOLOGY "Ceiling datasets — pre-registration")." — `batches/p1c.conf:1` — note: grammar is p1c_<dataset>_<floor> (dataset before floor, no _r<k>)

### `p1c_img/profile.json`

- [Experiment H flight profiles (batches/expH/*.json)] "- **Profile** (identical in all three; a `HPROFILE` JSON, `batches/p1c_img/profile.json`):" — `docs/p1c_img_calibration_spec.md:21`

### `p1c_img_`

- [check-flight prefixes (phases)] "# Calibration flights `p1c_img_*`: specification and pre-registered acceptance bands (SIGNED OFF by the user 2026-10-10, with the climb-cycle change below made BEFORE any flight)" — `docs/p1c_img_calibration_spec.md:1` — note: CALIBRATION flights for the real-flight camera path; no p1c_img_* trial dir exists on disk (only batches/p1c_img/profile.json)
- [check-flight prefixes (phases)] "**These are CALIBRATION flights only, NEVER datasets.** No thesis comparison result is computed from them, and the" — `docs/p1c_img_calibration_spec.md:7`
- [check-flight prefixes (phases)] "# tex | trans | blank -> p1c_img_{tex,trans,blank} on corridor_{textured,transition,blank}" — `tools/run_p1c_img.sh:5`

### `p1diag_`

- [check-flight prefixes (phases)] "**Diagnosis** (four 60 s cruise runs, one load removed at a time, same session; ... diagnostic only, no configuration change). The runs use the `FWD_DIAG` switch in" — `METHODOLOGY.md:1556`
- [check-flight prefixes (phases)] "| `p1diag_control_tex` (no forward camera) | **0.957** | ~130% | 28% |" — `METHODOLOGY.md:1562` — note: rows 1562-1565 define _control_tex, _fwd_full, _fwd_norecord, _fwd_nobridge
- [check-flight prefixes (phases)] "| `p1diag_fwd_norecord` (bridged, not recorded) | **0.761** | ~170% | 26% |" — `METHODOLOGY.md:1564`
- [check-flight prefixes (phases)] "| `p1diag_fwd_nobridge` (in the model, not bridged) | **0.958** | ~130% | 29% |" — `METHODOLOGY.md:1565`

### `p1plain_`

- [check-flight prefixes (phases)] "**Flights.** One flight per plain world: `p1plain_{tex,trans,blank}`, at the" — `METHODOLOGY.md:2205`
- [check-flight prefixes (phases)] "# One flight per plain-wall world; not part of the fwdplain_* dataset." — `batches/p1plain.conf:2`
- [check-flight prefixes (phases)] *(superseded)* "the check flights `p1_fwd_*` and `p1plain_*`." — `METHODOLOGY.md:2365`

### `p1rtf_dsn_tex`

- [check-flight prefixes (phases)] "**unchanged** `corridor_textured` world (the original iris, `dsn_*` settings), with RTF ... lowered to ~0.77 by Gazebo's runtime `set_physics` service (`real_time_factor 0.77`," — `METHODOLOGY.md:1588` — note: trial named on line 1593

### `p2_d15 / p3 / v2 / v3` — **UNDEFINED** (see flags §a)

- [batch state names] `p2_d15 / p3 / v2 / v3 (batch logs)` *(used, not defined here)* "p2_d15.log" — `~/thesis_data/batches/p2_d15.log`
- [batch state names] `p2_d15 / p3 / v2 / v3 (batch logs)` *(used, not defined here)* "p3.log" — `~/thesis_data/batches/p3.log`
- [batch state names] `p2_d15 / p3 / v2 / v3 (batch logs)` *(used, not defined here)* "v2.log" — `~/thesis_data/batches/v2.log`

### `p<N>`

- [naming collisions] `p<N> (phase vs precondition)` "- **(P2)** a shadow run of **the exact binary to be flown** (`AHRS_EKF_TYPE 10`, `AHRS_UKF_ENABLE 1`):" — `METHODOLOGY.md:6847` — note: "_p2" in ukf_shadow_sitl_tex_p2 and "_p3" in ukf_groundtest_p3 are D9 preconditions P2/P3, not Phase 1/2 criteria P2/P3 (METHODOLOGY 1713) nor phase numbers as in p1_/p1c_
- [naming collisions] `p<N> (phase vs precondition)` "| P2 | flow → EKF3 latency (median and p95) | ≤ same-world `dsn` mean + **12.5 ms** (one EKF3 prediction step, its own t ..." — `METHODOLOGY.md:1713` — note: Phase-1/2 criterion P2 (different meaning from the D9 precondition P2)

### `phase3_yaw_sweep`

- [archive folders (~/thesis_data)] "`eval/fwd_sweep_eval.py` → `eval/results/fwd_yaw_sweep.json`, with renders in ... `~/thesis_data/phase3_yaw_sweep/`. Bias and noise are computed on the non-outlier valid" — `METHODOLOGY.md:2787` — note: children use a DIFFERENT grammar: <floorword>_<dataset> e.g. textured_fwdc, blank_fwdplainc (full floor word first)
- [archive folders (~/thesis_data)] "# Static heading-response check for Phase 3 (METHODOLOGY, pre-registered supplementary" — `sim/tools/yaw_sweep.sh:3`

### `phase5b`

- [archive folders (~/thesis_data)] `phase5b (sandbox)` "# Phase 5b consistency replays (sandbox HOME=/home/makerspace/thesis_data/phase5b/home; outputs only there; logging-only instrumentation)" — `batches/phase5b_replays.jobs:1`
- [final re-run pipeline stage names] "| Phase 5b | `phase5b` | `build_5b_sandbox.sh` (fresh sandbox `phase5b_final`) + 72 jobs + `phase5b_consistency.py` | d15 | — |" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:131` — note: stage name; sandboxes phase5b_d15, phase5b_final, phase5b_final2

### `phase5b_d15`

- [archive folders (~/thesis_data)] "- Phase 5b on the **current D15 sandbox** (`phase5b_d15`);" — `METHODOLOGY.md:9621`

### `phase5b_final / phase5b_final2`

- [archive folders (~/thesis_data)] "- Phase 5b sandbox: `~/thesis_data/phase5b_final`." — `docs/handovers/2026-10-09_final_rerun_pipeline.md:31`
- [archive folders (~/thesis_data)] "# ~/thesis_data/pre_final2_trials, batches final2_*, Phase 5b sandbox phase5b_final2 (all DIE if they exist unstarted);" — `eval/final_rerun_pipeline.sh:24`

### `phase5b_rerun`

- [archive folders (~/thesis_data)] "SBH="$HOME/thesis_data/phase5b_rerun/home"" — `eval/rerun_pipeline.sh:102` — note: Phase 5b sandbox of the consolidated re-run (code only)

### `port_merge_u4`

- [eval/results naming] `port_merge_u4 (eval/results)` "### The port geometry branch MERGED, Replay INSTALLED; U4; U10 and stage-3 DRAFTS (handover `docs/handovers/2026-10-12_port_merge_u4_drafts.md`)" — `METHODOLOGY.md:13790`

### `pre_d15_trials`

- [archive folders (~/thesis_data)] "- Pre-D15 results go to `eval/results_pre_d15/`, and every trial's UKF/FGO outputs to ... `~/thesis_data/pre_d15_trials/`." — `METHODOLOGY.md:7130`

### `pre_final2_trials`

- [archive folders (~/thesis_data)] "- New state `final_rerun2`, snapshot `results_pre_final2`, archive `pre_final2_trials` (331 dirs)." — `METHODOLOGY.md:13332`
- [archive folders (~/thesis_data)] "- archive `~/thesis_data/pre_final2_trials` (FGO output dirs only: `fgo*`, `room_fgo*`, `lc_fgo_*`; 331 dirs);" — `docs/handovers/2026-10-10_initial_sigma_audit.md:175`

### `pre_final_trials`

- [archive folders (~/thesis_data)] "- trial-output archive: `~/thesis_data/pre_final_trials`;" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:28`

### `R1` — **CONFLICT: 7 meanings** (see flags §b)

- [D17 V1/V2 heading-Replay checks] "- **R1 (same input):** every `REPH` message replayed reaches the UKF, and every sample the UKF accepts" — `METHODOLOGY.md:7596` — note: PASS criteria of D17 V1 (Replay check on set (b) logs); reused live for V2 (line 7611)
- [Experiment H supervisor ruling items (2026-10-08)] "**R1. During tag loss, position hold falls back to optical flow (with IMU and rangefinder) until the tag returns.**" — `docs/tag_hold_design.md:9` — note: §R "Supervisor ruling 2026-10-08 (incorporated)"
- [plan-to-freeze risks] "- **R1 (new work, threatens 9 Oct by ~1 day).** The live FGO node has **no camera-heading input**; only" — `docs/plan_to_freeze.md:32` — note: section "Risks, flagged now"
- [result flights/sorties (R1…Rn)] "| **R1…Rn: result flights** | **result-producing (pre-registered here)** | the §3 profile (~2.5–3.5 min) | set by what the result needs (§3) | scoring (§4–§8) |" — `docs/rung1_preregistration.md:83` — note: R1…Rn = rung-1 result flights; same in docs/rung1_preregistration_draft.md:62
- [result flights/sorties (R1…Rn)] "| **R1…Rn: result sorties** | **result-producing (this document)** | the §3 profile (~2 min airborne) | set by what the result needs (§3) | scoring (§4, §7) |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:62` — note: R1…Rn = stage-3 result sorties
- [rgs_check_tex roll-gain check criteria] "| R1 | roll oscillation removed | cruise gyro-x rms **≤ 0.05 rad/s** AND 15–20 Hz band rms **≤ 0.040 rad/s** | Pitch runs at the same effective loop gain at 0.0054 rms; allowing roll 10× pitch for lateral-control activity gives 0.05. The band condition is ≥ 20 dB (×10 amplitude) below the old 0.396. | PRIMARY |" — `METHODOLOGY.md:4608` — note: pre-registered PRIMARY criteria of check flight rgs_check_tex (METHODOLOGY "Check flight `rgs_check_tex`: pre-registration")
- [rung-1 work items (minimal real-flight plan)] "| R1 | **Converter** BIN → FGO inputs (§4.3), with geometry overrides and the SITL acceptance test on `cl_a_tex_half` | 3–4 d | — | **yes** | **Medium.** Timing rules for 400 Hz deltas; `RISI` dt quirks; the SITL band may need a justified width. |" — `docs/minimal_real_flight_plan.md:358` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67
- [rung-1 work items (minimal real-flight plan)] "`docs/real_flights_plan.md` §7.2 and the new rung-1 items R1–R15 of `docs/minimal_real_flight_plan.md`." — `docs/real_flight_readiness_by_rung.md:19` — note: confirms the R1–R15 range is the rung-1 item list
- [watcher bench re-run set-up changes] "- **R1 — A1 FIXED (the B8a harness fault, handover 2026-10-12 §4).** The EKF origin (`SET_GPS_GLOBAL_ORIGIN`, the same" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:18` — note: §1.1 "Set-up changes (harness only; the watcher is not changed)"

### `r1_*`

- [eval/results naming] `r1_* (eval/results)` "### Rung-1 converter BUILT (branch `worktree-agent-a323ce1f90a749262` `eb629a6`; handover `docs/handovers/2026-10-10_r1_converter.md`): NOT MERGED YET" — `METHODOLOGY.md:13220` — note: "r1" pairs with "Rung-1" via the handover file name; r1_converter, r1_mocap_sync, r1_scorer, r1_ukf_port result folders

### `rerun_<set>_evo/_score.json`

- [eval/results naming] "`rerun_ds_evo.json`. The old `ds` figures used a different, apparatus metric, so there is no" — `METHODOLOGY.md:5615` — note: rerun_ = consolidated re-run outputs

### `rerun_main / rerun2_main / rerun2_ds`

- [batch state names] "`run_resumable_batch.sh batches/rerun_main.conf rerun2_main`. That is 33 trials in order:" — `METHODOLOGY.md:4679`
- [batch state names] "- Then, only if `rerun2_main` is DONE, `batches/rerun_ds.conf` → `rerun2_ds`: the 9 `ds_*`" — `METHODOLOGY.md:4681`
- [batch state names] *(superseded)* "Superseded 2026-09-29: this start (ff2b6a8, pre-sign-fix, old roll gains) flew nothing (refused: stale processes). The re-fly runs as rerun2_main / rerun2_ds." — `~/thesis_data/batches/rerun_main/SUPERSEDED.txt:1` — note: "rerun2_" = second start of the consolidated re-run; the first, rerun_main, flew nothing

### `results_pre_d10`

- [eval/results naming] "JSONs are kept in `eval/results_pre_d10/` as SUPERSEDED):" — `METHODOLOGY.md:6822`

### `results_pre_d15`

- [eval/results naming] "- Pre-D15 results go to `eval/results_pre_d15/`, and every trial's UKF/FGO outputs to" — `METHODOLOGY.md:7130`
- [offline re-runs] "- All pre-D15 result files are kept in `eval/results_pre_d15/`, and every trial's pre-D15 UKF/FGO outputs in" — `docs/thesis/numbers.md:1017`

### `results_pre_final`

- [eval/results naming] "- **Old:** `eval/results_pre_final/` (the snapshot taken when the run started; it equals the committed results at" — `docs/thesis/final_restatement_draft.md:7`
- [offline re-runs] "- results snapshot: `eval/results_pre_final`;" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:27` — note: snapshot of eval/results before the first final re-run

### `results_pre_final2`

- [eval/results naming] "- New state `final_rerun2`, snapshot `results_pre_final2`, archive `pre_final2_trials` (331 dirs)." — `METHODOLOGY.md:13332`
- [offline re-runs] "`~/thesis_ws/eval/results_pre_final2` (first final re-run, FGO with 1e-3 rad initial yaw; read by absolute path, untracked," — `docs/handovers/2026-10-10_final2_restatement.md:5`

### `results_pre_rerun`

- [eval/results naming] "The old results are kept in `eval/results_pre_rerun/`, and the" — `METHODOLOGY.md:5493`
- [eval/results naming] "OLD = `eval/results_pre_rerun` (pre-re-run snapshot), NEW = `eval/results`. `DIRECTION` marks a changed comparison (ordering sign, arm-effect sign, verdict, side of 1 / 50% / NEES 3); see the script docstring." — `docs/thesis/rerun_old_vs_new.md:3`
- [offline re-runs] "OLD = `eval/results_pre_rerun` (pre-re-run snapshot), NEW = `eval/results`. `DIRECTION` marks a changed comparison (ordering sign, arm-effect sign, verdict, side of 1 / 50% / NEES 3); see the script docstring." — `docs/thesis/rerun_old_vs_new.md:3` — note: pre-consolidated-re-run snapshot

### `rgs_select_tex`

- [check flights (one-off names)] "- **Gain-selection flight** (`rgs_select_tex`: 60 s cruise, part of step a, not the check" — `METHODOLOGY.md:4579` — note: "rgs" never expanded

### `room_check` — **UNDEFINED** (see flags §a)

- [check flights (one-off names)] *(used, not defined here)* "- **Texture convention frozen** on the room check flight: `u-y_v-x`, median position error 0.013 m, |yaw| 0.02°. Every" — `METHODOLOGY.md:10021` — note: text says only "the room check flight"; the dir name room_check is paired with it by name only (listed at world_images/index.md:33)

### `room_H / room_O / room_T`

- [final re-run job lists (batches/final_rerun)] `room_H / room_O / room_T (.jobs, final_room_* batches)` "# FINAL re-run, Experiment H offline shadows (RECONSTRUCTED: no committed job list existed; see the handover)." — `batches/final_rerun/room_H.jobs:1`
- [final re-run job lists (batches/final_rerun)] `room_H / room_O / room_T (.jobs, final_room_* batches)` "# FINAL re-run, Experiment O (RECONSTRUCTED from the outputs and METHODOLOGY 10398-10447): GNSS fixes from <trial>/gnss.npz" — `batches/final_rerun/room_O.jobs:1`
- [final re-run job lists (batches/final_rerun)] `room_H / room_O / room_T (.jobs, final_room_* batches)` "# FINAL re-run, Experiment T (RECONSTRUCTED from the outputs; METHODOLOGY 10126-10168, 10862-10888): tag sigma 0.05 (default)," — `batches/final_rerun/room_T.jobs:1`

### `run2_*.out / run4_*.out`

- [watcher bench sessions] "All under `~/thesis_data/wbench/`; driver logs `run4_*.out`; per-session `analysis/results.txt`" — `docs/handovers/2026-10-12_m2_full_bench.md:232`
- [watcher bench sessions] "- **Data:** `~/thesis_data/wbench/wbench2_*` and `run2_*.out`. Nothing was deleted." — `docs/handovers/2026-10-12_watcher_bench_rerun.md:449`

### `run_*.out` — **UNDEFINED** (see flags §a)

- [watcher bench sessions] `run_*.out (no number)` *(used, not defined here)* "run_hoverB2s.out" — `~/thesis_data/wbench/run_hoverB2s.out` — note: 2026-10-11 driver logs; never named in text (hoverB2s, hoverC_b10b, hoverB_b6b, m2b/m2c also undefined)
- [watcher bench sessions] `run_*.out (no number)` *(used, not defined here)* "run_smoke.out" — `~/thesis_data/wbench/run_smoke.out` — note: 2026-10-11 driver logs; never named in text (hoverB2s, hoverC_b10b, hoverB_b6b, m2b/m2c also undefined)
- [watcher bench sessions] `run_*.out (no number)` *(used, not defined here)* "run_lua.out" — `~/thesis_data/wbench/run_lua.out` — note: 2026-10-11 driver logs; never named in text (hoverB2s, hoverC_b10b, hoverB_b6b, m2b/m2c also undefined)

### `s0a_sweep`

- [Experiment H flight profiles (batches/expH/*.json)] "- **S0a, characterisation:** open loop on simulator truth (`AHRS_EKF_TYPE 10`), the 47-segment sweep ... `batches/expH/s0a_sweep.json`." — `METHODOLOGY.md:10636`

### `s0b_check` — **UNDEFINED** (see flags §a)

- [Experiment H flight profiles (batches/expH/*.json)] *(used, not defined here)* "s0b_check.json" — `batches/expH/s0b_check.json` — note: S0b check flight is defined (METHODOLOGY 10652) but the file is never named in text

### `s1_profile / s1_far_profile`

- [Experiment H flight profiles (batches/expH/*.json)] """"Experiment H S1 profile (METHODOLOGY pre-registration), in the tag frame W (LOCAL_NED with EKF3 flying on the wall tag)." — `batches/expH/make_s1_profile.py:2`
- [Experiment H flight profiles (batches/expH/*.json)] "**5. S1 re-fly** (EKF3 flying, ×3, `room_wall_tag_far`, `s1_far_profile.json` = S1's profile with the start at the far" — `METHODOLOGY.md:11341`

### `safety_* / safety2_* profiles`

- [Experiment H flight profiles (batches/expH/*.json)] "# 2 m-clearance hold W(-2.6, 0) (ruling 2026-10-09 item 3)" — `tools/run_h_safety.sh:18` — note: safety2_*_profile.json are the 2 m-clearance-hold profiles (lines 19-21); the "2" itself is never expanded; safety_* = the first option (i) profiles

### `sens_yaw0`

- [final re-run job lists (batches/final_rerun)] `sens_yaw0 (.jobs, final2_sens_yaw0)` "# LABELLED SENSITIVITY CHECK (user ruling 2026-10-10, METHODOLOGY "RULINGS (user, 2026-10-10): FGO initial yaw sigma"," — `batches/final_rerun/sens_yaw0.jobs:1`

### `sensitivity_yaw0_0p1`

- [archive folders (~/thesis_data)] "# LABELLED SENSITIVITY CHECK (user ruling 2026-10-10, METHODOLOGY "RULINGS (user, 2026-10-10): FGO initial yaw sigma", ... # item 1): the UKF and the FGO with a 0.1 rad initial yaw sigma (EKF3's CovarianceInit value; env INIT_YAW_SIG ..." — `batches/final_rerun/sens_yaw0.jobs:1` — note: "0p1" = 0.1 rad, stated by line 4 output path
- [archive folders (~/thesis_data)] "# Outputs ONLY to ~/thesis_data/sensitivity_yaw0_0p1/<trial>/<est>[_<arm>]_iy0.1/ (the knob refuses to run without" — `batches/final_rerun/sens_yaw0.jobs:4`

### `sitl_cwd`

- [watcher bench sessions] "- **SITL ran in its own working directory** (`~/thesis_data/wbench/sitl_cwd`, eeprom wiped per session), so the shared" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:447`

### `smoke_test`

- [legacy one-off trials] "**Measured evidence** (`smoke_test`, 2026-07-22, `iris_textured`, 0.4 m/s" — `CLAUDE.md:775`

### `stage_b_verify`

- [legacy one-off trials] "notes: "Stage B EKF pose evaluation - state-gated forward flight"" — `~/thesis_data/trials/stage_b_verify/metadata.yaml:9`

### `stage_c_textured / stage_c_blank`

- [legacy one-off trials] "notes: "Stage C GNSS-denied verification - textured floor, state-gated forward flight"" — `~/thesis_data/trials/stage_c_textured/metadata.yaml:9`
- [legacy one-off trials] "**Verification** (`stage_c_textured` and `stage_c_blank` trials, same" — `CLAUDE.md:471`

### `SUPERSEDED.txt`

- [trial status suffixes] `SUPERSEDED.txt (trial marker)` "the check flights `p1_fwd_*` and `p1plain_*`. ... They are kept on disk (`SUPERSEDED.txt` in each trial directory) and **not analysed" — `METHODOLOGY.md:2365`
- [trial status suffixes] `SUPERSEDED.txt (trial marker)` "SUPERSEDED (user ruling, 2026-09-24): kept, labelled, not analysed further." — `~/thesis_data/trials/p1diag_fwd_full/SUPERSEDED.txt:1` — note: p1diag_fwd_* also carry it though METHODOLOGY 2362-2364 lists only worlds, fwd_*, p1_fwd_*, p1plain_*

### `sweep_v<speed>`

- [legacy one-off trials] "notes: "velocity sweep"" — `~/thesis_data/trials/sweep_v0p25/metadata.yaml:9` — note: metadata target_velocity_m_s holds the speed; the "p"-for-decimal encoding is not written anywhere; sweep_v1p100/1p25/1p50 have empty notes
- [legacy one-off trials] "- **`sweep_v*`:** not cited for anything on the lateral axis. `analyse_flow_sweep.py` uses ... median |`flow_y`| (forward), and METHODOLOGY cites `sweep_v*` only as skipped. It **stays" — `METHODOLOGY.md:4280`
- [legacy one-off trials] *(used, not defined here)* "notes: """ — `~/thesis_data/trials/sweep_v1p100/metadata.yaml:9` — note: sweep_v1p100 (vs sweep_v1p0): suffix undefined

### `T1` — **CONFLICT: 4 meanings** (see flags §b)

- [M2-R bench criteria] "**T1 (timing; independent of the runaway's duration; every valid attempt with a runaway):**" — `docs/handovers/2026-10-12_m2r_rerun.md:114` — note: CONFLICT with thesis/pack T1
- [M2-R bench criteria] "- T1 (independent of duration): the watcher is unconfirmed by t_on + 0.5 s with a vel reason; no watcher HEARTBEAT" — `METHODOLOGY.md:14149`
- [fail-closed watcher tests] "- T1 (watcher not started): **refused to arm** ("REFUSING TO ARM: no watcher heartbeat"), no take-off. PASS." — `METHODOLOGY.md:10977`
- [fail-closed watcher tests] "| V6 | Watcher heartbeat loss | `FS_GCS_ENABLE 5` → LAND within `FS_GCS_TIMEOUT` (**not yet tested via MAVLink**: the SITL T1/T2 tests of `tools/test_watch_failclosed.sh` used the local heartbeat file read by `fly_trial.py`; the first MAVLink test is 2(c) B0–B10, then once on the UKF build) |" — `docs/ukf_only_closed_loop_costing.md:266`
- [final results pack tables] "| T1 | Headline claims before/after (36 rows) | CURRENT | rendered by `eval/figs_final_pack.py` from `docs/thesis/headline_claims_before_after.md` | all rows cited in its evidence column | 2/2 |" — `docs/thesis/final_results_pack_index.md:27` — note: CONFLICT: pack table T1 (claims) differs from thesis table T1 (scorecard)
- [final results pack tables] "T1 Headline claims: before against after the final re-runs (36 rows)" — `docs/thesis/final_results_pack.pdf p.1`
- [thesis tables] "# Table T1. Which estimator wins where (scorecard of the restated verdicts)" — `docs/thesis/tables/T1_scorecard.md:1` — note: thesis table (e202552)
- [thesis tables] "| T1 | table | `T1_scorecard.md`, `T1_scorecard.tex` | Which estimator wins where (scorecard of the restated verdicts) | CURRENT | 16/16 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:17`

### `T2` — **CONFLICT: 4 meanings** (see flags §b)

- [M2-R bench criteria] "**T2 (no arm while |v| ≥ 0.2; every valid attempt with a runaway):**" — `docs/handovers/2026-10-12_m2r_rerun.md:121`
- [fail-closed watcher tests] "- **T2 (watcher SIGKILLed during the hold): FAIL.** The heartbeat stopped at the kill, but the flight finished its" — `METHODOLOGY.md:10978`
- [final results pack tables] "| T2 | Corrections summary (18 rows) | CURRENT | `docs/thesis/final_results_pack_corrections.md` (quotes METHODOLOGY, numbers.md, eval/results) | §6.1, §6.5, §6.6, §15, §16.2, §17, §18 | 1/1 |" — `docs/thesis/final_results_pack_index.md:28` — note: CONFLICT: pack table T2 (corrections) differs from thesis table T2 (accuracy)
- [final results pack tables] "Every correction applied to the simulation results, in the order applied. This file is the source of Table T2 in" — `docs/thesis/final_results_pack_corrections.md:3`
- [thesis tables] "# Table T2. Position error without and with the camera heading (textured floor)" — `docs/thesis/tables/T2_accuracy_heading.md:1` — note: thesis table (e202552)
- [thesis tables] "| T2 | table | `T2_accuracy_heading.md`, `T2_accuracy_heading.tex` | Position error without and with the camera heading (textured floor) | CURRENT | 10/10 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:18`

### `T3` — **CONFLICT: 2 meanings** (see flags §b)

- [M2-R bench criteria] "**T3 (no LAND from M2):** 0 watcher "LAND command sent" and no BREACH from the disarm to the next M1." — `docs/handovers/2026-10-12_m2r_rerun.md:131`
- [thesis tables] "# Table T3. Blank floor: position error after the loss of flow aiding" — `docs/thesis/tables/T3_blank_floor.md:1` — note: thesis table (e202552)
- [thesis tables] "| T3 | table | `T3_blank_floor.md`, `T3_blank_floor.tex` | Blank floor: position error after the loss of flow aiding | CURRENT | 6/6 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:19`

### `T4` — **CONFLICT: 2 meanings** (see flags §b)

- [M2-R bench criteria] "**T4 (after M1, arming allowed; once, at the end):** (e) a `GPS_GLOBAL_ORIGIN` with the sent lat/lon received after" — `docs/handovers/2026-10-12_m2r_rerun.md:133`
- [thesis tables] "# Table T4. Closed loop at half speed: the final build of each estimator flying the vehicle" — `docs/thesis/tables/T4_closed_loop.md:1` — note: thesis table (e202552)
- [thesis tables] "| T4 | table | `T4_closed_loop.md`, `T4_closed_loop.tex` | Closed loop at half speed: the final build of each estimator flying the vehicle | CURRENT | 9/9 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:20`

### `T5`

- [thesis tables] "# Table T5. Experiment H: drift while the wall tag is hidden, flying estimators" — `docs/thesis/tables/T5_H_tag_loss_drift.md:1` — note: thesis table (e202552)
- [thesis tables] "| T5 | table | `T5_H_tag_loss_drift.md`, `T5_H_tag_loss_drift.tex` | Experiment H: drift while the wall tag is hidden, flying estimators | CURRENT | 6/6 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:21`

### `T6`

- [thesis tables] "# Table T6. Experiment O: indoor horizontal RMSE per flight (123 s, GNSS off)" — `docs/thesis/tables/T6_O_indoor_rmse.md:1` — note: thesis table (e202552)
- [thesis tables] "| T6 | table | `T6_O_indoor_rmse.md`, `T6_O_indoor_rmse.tex` | Experiment O: indoor horizontal RMSE per flight (123 s, GNSS off) | CURRENT | 7/7 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:22`

### `T7`

- [thesis tables] "# Table T7. Failure behaviour: blank-floor validity, the O return jump and the safety tests" — `docs/thesis/tables/T7_failure_behaviour.md:1` — note: thesis table (e202552)
- [thesis tables] "| T7 | table | `T7_failure_behaviour.md`, `T7_failure_behaviour.tex` | Failure behaviour: blank-floor validity, the O return jump and the safety tests | CURRENT | 9/9 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:23`

### `T8`

- [thesis tables] "# Table T8. Hindsight: the FGO whole-flight batch against the RTS-smoothed UKF" — `docs/thesis/tables/T8_hindsight_ratio.md:1` — note: thesis table (e202552)
- [thesis tables] "| T8 | table | `T8_hindsight_ratio.md`, `T8_hindsight_ratio.tex` | Hindsight: the FGO whole-flight batch against the RTS-smoothed UKF | CURRENT | 6/6 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:24`

### `T_<cond>_r<k>`

- [experiment trial names (T/O/H)] "**Conditions (tag count, the controlled variable; a LIVE per-flight condition).** All 8 tags stay in the world; the" — `METHODOLOGY.md:10113`
- [experiment trial names (T/O/H)] "# Experiment T flights (pre-registered: METHODOLOGY "Experiment T: pre-registration"). 12 single-trial resumable batches," — `tools/run_expT.sh:2`
- [experiment trial names (T/O/H)] "room_tags 0.5 2.0 60 T_A_r1" — `~/thesis_ws/batches/expT/T_A_r1.conf:1` — note: main-checkout-only conf

### `tag_check1 / tag_check1b` — **UNDEFINED** (see flags §a)

- [check flights (one-off names)] *(used, not defined here)* "tag_check1" — `~/thesis_data/trials/tag_check1` — note: trial dirs exist (and batch logs tag_check1(b).log), but no text defines them; only tag_check1c is named (METHODOLOGY 10051)
- [check flights (one-off names)] *(used, not defined here)* "tag_check1b" — `~/thesis_data/trials/tag_check1b` — note: trial dirs exist (and batch logs tag_check1(b).log), but no text defines them; only tag_check1c is named (METHODOLOGY 10051)

### `tag_check1c / tag_check2 / tag_check3`

- [check flights (one-off names)] "### Tag bridge, EKF3 configuration and the check flights (`tag_check1c`, `tag_check2`, `tag_check3`)" — `METHODOLOGY.md:10051`

### `tag_check2img` — **UNDEFINED** (see flags §a)

- [check flights (one-off names)] *(used, not defined here)* "worlds) put the green y-axis line across tag 5, which then never decoded (found on `tag_check2img`, 2026-10-08;" — `METHODOLOGY.md:10027` — note: usage only; the "img" suffix (downward images recorded) is stated in world_images/index.md:152 list of image-carrying bags, not as a definition

### `tagchar_h<NN>`

- [check flights (one-off names)] "# Tag module characterisation (detection range and pose accuracy vs height), room_tags, north overflight of tags 0, 4, 1" — `batches/tagchar.conf:1` — note: conf rows pair tagchar_h15/h20/h25/h30 with altitude 1.5/2.0/2.5/3.0 (lines 3-6); "h" never expanded
- [check flights (one-off names)] "room_tags 0.5 1.5 12 tagchar_h15" — `batches/tagchar.conf:3`

### `trials_pre_rerun`

- [archive folders (~/thesis_data)] "Moved 2026-09-29 before the consolidated re-run: the pre-re-run versions of the 42 re-flown trials (same names). Kept, never deleted; old results in eval/results/ and docs/thesis/numbers.md refer to these." — `~/thesis_data/trials_pre_rerun/README.txt:1`
- [archive folders (~/thesis_data)] "- **Old data moved, not deleted.** The 42 pre-re-run trial folders with the re-flown names" — `METHODOLOGY.md:4053`

### `tsx_off_tex / tsx_on_tex`

- [check flights (one-off names)] "- `tsx_off_tex`: time sync **off**, as in every dataset. World `corridor_textured_fwdc`," — `METHODOLOGY.md:3823` — note: "tsx" never expanded; batches/tsx.conf line 1 "Time-sync A/B"
- [check flights (one-off names)] "- `tsx_on_tex`: time sync **on**. World `corridor_tson_fwdc`, which differs only in using" — `METHODOLOGY.md:3825`
- [check flights (one-off names)] "# Time-sync A/B (METHODOLOGY "Steps 2-3"). Both FLOW_POS_Z=0.25 via consolidated_rerun.parm." — `batches/tsx.conf:1`

### `u10_*`

- [eval/results naming] `u10_* (eval/results)` "### U10 rule 2: the PREFERRED fix done and installed: replayed UKF records renamed (handover `docs/handovers/2026-10-12_u10_final.md`)" — `METHODOLOGY.md:14018`

### `ukf_dtfix_check` — **UNDEFINED** (see flags §a)

- [archive folders (~/thesis_data)] *(used, not defined here)* "- **72 absolute symlinks** (the `dsn_tex_r*_oi2*` variant folders, the Phase 5b and ... UKF-dt-check sandboxes) pointed into `trials/<moved name>/`. They were broken by the move" — `METHODOLOGY.md:4258` — note: only "UKF-dt-check sandboxes" is mentioned; the folder name ukf_dtfix_check never appears

### `ukf_groundtest_hdg_v3`

- [ground tests (gt_ / _groundtest)] "**V3 — ground test with the UKF active and heading on** (`UKF=1 HEADING=1 GROUND_TEST=60`):" — `METHODOLOGY.md:7617`

### `ukf_groundtest_p3`

- [ground tests (gt_ / _groundtest)] "### D9 precondition P3 (UKF backend ground test): PRE-REGISTERED before it is run ... **Run:** `UKF=1 GROUND_TEST=60 sim/tools/closed_loop_run.sh corridor_textured ukf_groundtest_p3` on port" — `METHODOLOGY.md:7370`

### `ukf_shadow_hdg_v2`

- [shadow and development runs] "### D17 V2 (shadow run of the exact binary with heading, `ukf_shadow_hdg_v2`): PASS" — `METHODOLOGY.md:7664`

### `ukf_shadow_replay`

- [eval/results naming] `ukf_shadow_replay (eval/results)` "check is `eval/ukf_shadow_replay_check.py`, with outputs in `eval/results/ukf_shadow_replay/`." — `METHODOLOGY.md:5384`

### `ukf_shadow_sitl_tex`

- [shadow and development runs] "### Part 4: shadow UKF in live SITL, `ukf_shadow_sitl_tex` (2026-09-29): runs, logs, flags valid; heading drifts" — `METHODOLOGY.md:5673`

### `v4_<trial>`

- [batch state names] "# D17 V4: the with-heading UKF set x3, sequential; stops after a flight whose B1 fails (scored between flights)." — `~/thesis_data/batches/v4_set.sh:2`

### `validation` — **UNDEFINED** (see flags §a)

- [archive folders (~/thesis_data)] `validation (test1_yaw, test1_yaw_slow)` *(used, not defined here)* "test1_yaw" — `~/thesis_data/validation/test1_yaw`
- [archive folders (~/thesis_data)] `validation (test1_yaw, test1_yaw_slow)` *(used, not defined here)* "test1_yaw_slow" — `~/thesis_data/validation/test1_yaw_slow`

### `vendor_verify_full`

- [legacy one-off trials] "(`vendor_verify_full`, corridor_textured flown from `sim/worlds/`) corroborates" — `METHODOLOGY.md:854`

### `wbench2_`

- [watcher bench sessions] "# Handover, 2026-10-12: watcher bench B0–B10 RE-RUN in SITL after F6 (`wbench2_*`)" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:1`
- [watcher bench sessions] "# (2026-10-12 re-run: output wbench2_<session>_<stamp>; --prefix wbench reproduces the 2026-10-11 naming)" — `tools/run_wbench.sh:7`

### `wbench3_f7`

- [watcher bench sessions] "# Handover, 2026-10-12: the F7 watcher yaw check, its SITL bench (`wbench3_f7`), and the flight-card procedure" — `docs/handovers/2026-10-12_f7_cards.md:1`

### `wbench4_`

- [watcher bench sessions] "# (2026-10-12 wbench4: --prefix wbench4 --checks all = the F7 yaw + M2 velocity checks, H10, M1, M3 in every session)" — `tools/run_wbench.sh:5`
- [watcher bench sessions] "| `wbench4_m2_20261012_181437`, `…_182305`, `…_182609` | M2-R: the void first run (B4), the repeat (V3 failed, B5), the final repeat |" — `docs/handovers/2026-10-12_m2_full_bench.md:246`

### `wbench5_m2r`

- [watcher bench sessions] "# (2026-10-12 wbench5: tools/run_wbench.sh m2r --prefix wbench5 --checks all = the re-registered M2-R, handover 2026-10-12_m2r_rerun.md)" — `tools/run_wbench.sh:6`

### `wbench session names`

- [watcher bench sessions] `wbench session names (smoke ground hoverA hoverB hoverC f7 m2 m2r)` "# tools/run_wbench.sh <session> [--from TEST] [--prefix P] [--checks none|all] sessions: smoke ground hoverA hoverB hoverC f7 m2 m2r" — `tools/run_wbench.sh:4`

### `wbench sub-suffixes` — **UNDEFINED** (see flags §a)

- [watcher bench sessions] `wbench sub-suffixes (_b6b, _b10b, _r2, B2s, m2b, m2c)` *(used, not defined here)* "run2_hoverB_b6b.out" — `~/thesis_data/wbench/run2_hoverB_b6b.out`
- [watcher bench sessions] `wbench sub-suffixes (_b6b, _b10b, _r2, B2s, m2b, m2c)` *(used, not defined here)* "run4_hoverC_b10b.out" — `~/thesis_data/wbench/run4_hoverC_b10b.out`
- [watcher bench sessions] `wbench sub-suffixes (_b6b, _b10b, _r2, B2s, m2b, m2c)` *(used, not defined here)* "run4_m2c.out" — `~/thesis_data/wbench/run4_m2c.out`

### `wbench_*`

- [watcher bench sessions] "# Watcher SITL bench (item 2c; docs/handovers/2026-10-11_watcher_sitl_bench.md). VERIFICATION flights only (wbench_*)," — `tools/run_wbench.sh:2`

### `wbench_<session>_<stamp>`

- [watcher bench sessions] `wbench_<session>_<stamp> (2026-10-11)` "| `wbench_smoke_20261011_122220` | plumbing (amendments A1–A5) |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:172` — note: session table lines 172-182 also defines hoverA2, hoverA3, hoverB2, lua, b4a sessions
- [watcher bench sessions] `wbench_<session>_<stamp> (2026-10-11)` "| `wbench_hoverA2_20261011_125023` | B4b_side (then stopped: landed outside the box) |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:176`
- [watcher bench sessions] `wbench_<session>_<stamp> (2026-10-11)` "| `wbench_hoverB2_20261011_130644` | B9c ×2, B9-hang |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:180` — note: COLLISION: hoverB2 here is a continuation session, unlike the "2" in wbench2 (re-run prefix)
- [watcher bench sessions] `wbench_<session>_<stamp> (2026-10-11)` "| `wbench_b4a_20261011_131756` | B4a (four side faces + top), B4c (amendment A8) |" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:182`

### `wtest_profile / wtest_far_profile`

- [Experiment H flight profiles (batches/expH/*.json)] "Profile `batches/expH/wtest_profile.json`: `wait_fix` → move → hold 60 s, flown on the backend under test" — `METHODOLOGY.md:11112`
- [Experiment H flight profiles (batches/expH/*.json)] "**3. Ground tests re-run** (`H_gt_ukf_far`, `H_gt_fgo_far` with the C++ node; profile `wtest_far_profile.json`)." — `METHODOLOGY.md:11321`

### `xuko_fmt`

- [eval/results naming] `xuko_fmt (eval/results)` "### XUKO FMT + stamp fix INSTALLED; U10 and stage-3 drafts updated; H10 guard in fly_trial.py (handover `docs/handovers/2026-10-12_xuko_u10_h10.md`)" — `METHODOLOGY.md:13968`

## 3. Hypothesis, prediction, criterion, check, item and question codes


### `A1` — **CONFLICT: 7 meanings** (see flags §b)

- [D12 FGO backend work items] "| A1 | `EKFType::FGO` (13), `AP_AHRS_FGO` backend, generated switch arms, `AHRS_EKF_TYPE 13` | 0.5 day |" — `docs/d12_fgo_backend_report.md:60`
- [Experiment T flight labels] "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: condition A (table rows METHODOLOGY.md:10118-10121: A all, B corners, C diagonal, D single) + repeat 1; expanded from "A1 B1 C1 D1 A2 … D3"
- [p1c image-flow calibration acceptance bands] "| A1 | HOVER | RMS(A) ≤ 1.10 × RMS(M) + 0.005 rad/s |" — `docs/p1c_img_calibration_spec.md:71`
- [real-flight readiness checklist rows] "| A1 | Airframe, FC, Pi and sensors assembled and wired: FC↔Pi UART, cameras, LiDAR | not built | a, b | Plan question 3 is still open. No hardware is described anywhere in the repo. | 2–4 d (parts in hand). Procurement time is unknown. | U1–U8 |" — `docs/real_flight_readiness.md:56` — note: section A "Vehicle, sensor drivers and bridges"
- [real-flight readiness checklist rows] "| A1 | Airframe, FC, sensors assembled | 1→2, U | HW | r1: 0 d (supervisor's flying vehicle) or 2–4 d; r2: +1–2 d Pi, cameras, FC↔Pi UART | | WAITS |" — `docs/real_flight_readiness_by_rung.md:88` — note: same meaning restated by rung
- [rung-1 converter acceptance checks] "| A1 | `LOG_REPLAY` | = 1 |" — `docs/rung1_preregistration.md:347`
- [rung-1 converter acceptance checks] "- A1 `LOG_REPLAY` = 1;" — `docs/handovers/2026-10-12_r1_scoring_items.md:138` — note: same meaning restated
- [thesis appendix tables] "| A1 | appendix | `A1_closed_loop_builds.png` | Closed loop: every flown build against B1–B5 and the contact window | CURRENT | 8/8 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:25`
- [thesis appendix tables] "A1 Closed loop: every flown build against B1–B5 and the contact window [checks 8/8]" — `docs/thesis/figures_thesis/thesis_figures_combined.pdf p.1` — note: PDF lists A1–A3 as "appendix tables" (index.md row type is "appendix" with a .png)
- [watcher bench amendment letters (A-series)] "- **A1 — EKF origin.** EKF3 on flow had no position estimate pre-arm ("Arm: Need Position Estimate"). The operator sends" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:118`

### `A2` — **CONFLICT: 7 meanings** (see flags §b)

- [D12 FGO backend work items] "| A2 | **Input path.** The node sends its delayed state: time of validity on the SITL clock (via the `/imu/time_ref` map the node already has), position, velocity, attitude, gyro/accel bias and valid flag. `ODOMETRY` is taken by the camera heading (it goes to `AP_VisualOdom`), so the FGO state needs its own route: ..." — `docs/d12_fgo_backend_report.md:61`
- [D12 FGO backend work items] "| Fri 2 Oct | A2: the FGO state input route (its own, not `ODOMETRY`), logged for Replay. A3: the in-ArduPilot output predictor. **Evening/overnight: re-fly EKF3 and UKF at half speed** (a ×1 and b ×3 each = 8 flights, ~13 min each wall), unattended, with the stop rules. | half-speed EKF3/UKF sets |" — `docs/plan_to_freeze.md:11` — note: same meaning restated in the schedule
- [Experiment T flight labels] "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: condition A (table rows METHODOLOGY.md:10118-10121: A all, B corners, C diagonal, D single) + repeat 2; expanded from "A1 B1 C1 D1 A2 … D3"
- [p1c image-flow calibration acceptance bands] "| A2 | CRUISE | RMS(A) ≤ 1.10 × RMS(M) + 0.005 rad/s, and \|bias(A)\| ≤ \|bias(M)\| + 0.01 rad/s |" — `docs/p1c_img_calibration_spec.md:72`
- [real-flight readiness checklist rows] "| A2 | Baseline vehicle tune on the stock image: manual hover, `MOT_THST_HOVER` learned, harmonic notch, rate gains (Autotune in ALT_HOLD) | not built | a, b | The SITL values do not transfer: `h_extnav.parm` `MOT_THST_HOVER 0.310` (SITL iris), `roll_rate_gains.parm` (SITL). METHODOLOGY "`MOT_THST_HOVER` pinned". | ..." — `docs/real_flight_readiness.md:57`
- [rung-1 converter acceptance checks] "| A2 | `DSF` dropped blocks, whole log | = 0 |" — `docs/rung1_preregistration.md:348`
- [thesis appendix tables] "| A2 | appendix | `A2_H_and_safety_p1.png`, `A2_H_and_safety_p2.png` | H hold sets and the safety tests (all runs) | CURRENT | 11/11 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:26`
- [thesis appendix tables] "A2 H hold sets and the safety tests (all runs) [checks 11/11]" — `docs/thesis/figures_thesis/thesis_figures_combined.pdf p.1`
- [watcher bench amendment letters (A-series)] "- **A2/A4 — rangefinder: the Gazebo LiDAR, not SITL's analog sonar.** The SITL analog rangefinder read 0.0 m on the" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:120` — note: A2 and A4 share one entry

### `A3` — **CONFLICT: 7 meanings** (see flags §b)

- [D12 FGO backend work items] "| A3 | **Output predictor in ArduPilot.** Buffer the DAL IMU deltas. On each FGO state, re-propagate from its time of validity to now (the UKF port's process model, mean only), then propagate forward each loop. This is EKF3's output-predictor role, and the same as the UKF's `compute_output`. | 1 day |" — `docs/d12_fgo_backend_report.md:62`
- [Experiment T flight labels] "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: condition A (table rows METHODOLOGY.md:10118-10121: A all, B corners, C diagonal, D single) + repeat 3; expanded from "A1 B1 C1 D1 A2 … D3"
- [p1c image-flow calibration acceptance bands] "| A3 | CLIMB | \|bias(A)\| ≤ 0.05 rad/s, and \|bias(A)\| ≤ 0.25 × \|bias(M)\|. **Applies only if \|bias(M)\| ≥ 0.10 rad/s** on that axis. Otherwise A3 for that axis is reported as **"not tested: no climb bias present"**, which is not a pass |" — `docs/p1c_img_calibration_spec.md:73`
- [real-flight readiness checklist rows] "| A3 | Downward-camera capture on the Pi, publishing `/downward_camera/image` and `camera_info` with **sensor capture stamps** at 30 Hz | not built | a, b | `flow_tracker.py` subscribes to `/downward_camera/image`, which is today the Gazebo bridge. `real_flights_pi_readiness.md` §2.3 lists capture as [U]. | 1–2 d ..." — `docs/real_flight_readiness.md:58`
- [rung-1 converter acceptance checks] "| A3 | `RISI` samples dropped for flags; \|DVDT − DADT\| > 0.5 ms; DVDT within 0.5 ms of the frame spacing | 0; ≤ 0.1 % of samples; ≥ 99 % of samples |" — `docs/rung1_preregistration.md:349`
- [thesis appendix tables] "| A3 | appendix | `A3_F1_cost_ablations_p1.png`, `A3_F1_cost_ablations_p2.png` | F1, the L compute cost and the build ablations | CURRENT | 8/8 | none needed (table) |" — `docs/thesis/figures_thesis/index.md:27`
- [thesis appendix tables] "A3 F1, the L compute cost and the build ablations [checks 8/8]" — `docs/thesis/figures_thesis/thesis_figures_combined.pdf p.1`
- [watcher bench amendment letters (A-series)] "- **A3 — climb rate 0.5 m/s** (`WPNAV_SPEED_UP`, `PILOT_SPEED_UP` 50) and `PLND_ENABLED 0` (gazebo-iris.parm's" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:125`

### `A4` — **CONFLICT: 5 meanings** (see flags §b)

- [D12 FGO backend work items] "| A4 | **Validity.** Invalid when there has been no FGO state for > 250 ms, or its age exceeds budget, or the node flags invalid (its existing validity rule). Health and pre-arm follow from it. | 0.5 day |" — `docs/d12_fgo_backend_report.md:63`
- [p1c image-flow calibration acceptance bands] "| A4 | all | n(A) = n(M) (option a drops no frames by construction; checked) |" — `docs/p1c_img_calibration_spec.md:74`
- [real-flight readiness checklist rows] "| A4 | `flow_tracker.py` (Shi-Tomasi + LK + RANSAC) on the Pi CPU: rate, latency, `use_sim_time` off | needs adapting for real sensors | a, b | `FOCAL_LENGTH_PX = 554.0` is hard-coded (`flow_tracker.py:16`). Validity uses the feature count only (`:313`). Pi timing is unmeasured (plan §6, "must be timed"). | 1–2 d. ..." — `docs/real_flight_readiness.md:59`
- [rung-1 converter acceptance checks] "| A4 | IMU frame rate (mean frame period) against `SCHED_LOOP_RATE` | within ± 2 % |" — `docs/rung1_preregistration.md:350`
- [watcher bench amendment letters (A-series)] "- **A2/A4 — rangefinder: the Gazebo LiDAR, not SITL's analog sonar.** The SITL analog rangefinder read 0.0 m on the" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:120` — note: A2 and A4 share one entry

### `A5` — **CONFLICT: 4 meanings** (see flags §b)

- [D12 FGO backend work items] "| A5 | **Validation, mirroring the UKF.** Pre-registered checks: input equivalence (sent state = received state; time mapping); the predictor check on a shadow run; latency through take-off within budget; a ground test (G1–G5); then set (a) and set (b) flights. | 1.5–2 days, including flights |" — `docs/d12_fgo_backend_report.md:64`
- [real-flight readiness checklist rows] "| A5 | `flow_bridge.py` → `OPTICAL_FLOW` to EKF3 over the real link | needs adapting for real sensors | a, b | UDP port 14553 via MAVProxy (`flow_bridge.py:80`). The sign is now `flow_rate_x = +flow_x_rad` (`:27-31`, 2026-09-29 finding); it must be re-verified on the real mount (D5). | 0.5 d | B1, D5 |" — `docs/real_flight_readiness.md:60`
- [rung-1 converter acceptance checks] "| A5 | the converter's raw IMU through the INS 2-pole filters (`INS_GYRO_FILTER`/`INS_ACCEL_FILTER`) against the FC's logged `IMU` record (same instance), sample by sample over the DISARMED spans only (log start → first arming; last disarming → log end: the sync wiggles). In flight, prop vibration point-sampled at 25 ..." — `docs/rung1_preregistration.md:351`
- [watcher bench amendment letters (A-series)] "- **A5 — flow: the thesis camera-flow path, world `iris_textured`.** SITL's own flow sensor (`FLOW_TYPE 10`) drifted" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:127`

### `A6` — **CONFLICT: 3 meanings** (see flags §b)

- [real-flight readiness checklist rows] "| A6 | Forward camera: capture plus the C++ heading program on the Pi | exists but untested on hardware | b (heading arms); a only if the forward camera is flown | ARM64 build checked under qemu only: 205/205 integer outputs identical, \|Δψ\| ≤ 1.25e-5° (`real_flights_pi_readiness.md` §1). Native run and capture are ..." — `docs/real_flight_readiness.md:61`
- [rung-1 converter acceptance checks] "| A6 | rest, [arming − 3 s, arming − 0.5 s], if still (gyro std < 0.05 rad/s) | \|specific force\| = 9.80665 ± 0.15 m/s²; \|gyro mean\| < 0.05 rad/s (else NOT TESTED, not a failure) |" — `docs/rung1_preregistration.md:352`
- [watcher bench amendment letters (A-series)] "- **A6 — B5b-noflag set-up.** With `tracked = −1` from the start, the vehicle at rest gives bit-identical Gazebo poses," — `docs/handovers/2026-10-11_watcher_sitl_bench.md:138`

### `A7` — **CONFLICT: 3 meanings** (see flags §b)

- [real-flight readiness checklist rows] "| A7 | Wall-tag detector (`tag_bridge.py`, pupil_apriltags) on real images; `ODOMETRY` to EKF3 ExtNav; the same fixes to the UKF/FGO | needs adapting for real sensors | a, b if P-HOLD is the profile | Uses UDP 14557, i.e. SITL SERIAL1 (`tag_bridge.py:35,68`). `tag_hold_design.md` "Transfer to the real mocap room" ..." — `docs/real_flight_readiness.md:62`
- [rung-1 converter acceptance checks] "| A7 | flow = EKF3's flow input: `OF` vs `ROFH` (counts; flowX/Y, bodyX/Y float32-identical; Qual) | exact |" — `docs/rung1_preregistration.md:353`
- [watcher bench amendment letters (A-series)] "- **A7 — harness only.** (a) Before each hover the landed, DISARMED vehicle is put back at the spawn point with Gazebo" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:141` — note: has parts (a) set_pose carry and (b) operator disarm (line 143)

### `A7b` — **UNDEFINED** (see flags §a)

- [watcher bench amendment letters (A-series)] *(used, not defined here)* "- **S5 — M3 in the harness.** The simulated pilot (A7b) disarms after **2 s** on the ground in LAND (was 4 s)." — `docs/handovers/2026-10-12_m2_full_bench.md:79` — note: no "A7b" definition found; plausibly A7 part (b) (operator disarm after 4 s on the ground in LAND), watcher_sitl_bench.md:143-145; not inferred
- [watcher bench amendment letters (A-series)] *(used, not defined here)* "in the counted sessions, each after 4 s on the ground in LAND, under amendment A7b." — `docs/handovers/2026-10-12_watcher_bench_rerun.md:422` — note: second usage

### `A10` — **CONFLICT: 3 meanings** (see flags §b)

- [real-flight readiness checklist rows] "| A10 | IMU stream: `HIGHRES_IMU` 333 Hz from a real FC serial port → `imu_bridge.py` → `/imu/data_raw` + `/imu/time_ref` | needs adapting for real sensors | a (offline replay inputs), b | 333 Hz is the 0.8 × `SCHED_LOOP_RATE` cap, verified in SITL (CLAUDE.md "IMU Bridge"). SITL feeds it on `--serial2` UDP 14556. ..." — `docs/real_flight_readiness.md:65`
- [rung-1 converter acceptance checks] "| A10 | flow sign and response: `eval/sensor_timing_from_log.py --window <a sync wiggle>` | gain > 0 on both axes and peak correlation ≥ 0.5 on both; without it: NOT accepted |" — `docs/rung1_preregistration.md:356`
- [rung-1 converter acceptance checks] "- **Converter acceptance band** `eval/bin2fgo_accept.py` (A1–A10): on SITL all pass except the IMU check, which is" — `METHODOLOGY.md:13859` — note: METHODOLOGY summary of the band (A1–A10)
- [watcher bench amendment letters (A-series)] "- **A10 (2026-10-12, ~11:58, after the hoverB re-run `wbench2_hoverB_20261012_114206` and hoverC; before the run it" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:106`

### `B1` — **CONFLICT: 8 meanings** (see flags §b)

- [Experiment T flight labels] "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: condition B (table rows METHODOLOGY.md:10118-10121: A all, B corners, C diagonal, D single) + repeat 1; expanded from "A1 B1 C1 D1 A2 … D3"
- [FGO C++ port equivalence rows] "| B1 | `fgo_replay.py fwdc_tex_r1 0.25 2 heading` | every keyframe |" — `docs/fgo_cpp_port.md:186`
- [FGO C++ port equivalence rows] "| B1 | fwdc_tex_r1 heading | 10118 / 10118 | 0 (heading accepted 9184 of 9539) | 1.2e-4 / 1.1e-4 mm | 1.2e-10 / 1.7e-11 ° | **PASS** |" — `docs/handovers/2026-10-09_fgo_binit0_equivalence.md:106` — note: same rows re-run
- [QuadPlane blockers] "| B1 | **No position-free landing in QuadPlane** | QLAND runs the QLOITER position controller (`ArduPlane/mode_qland.cpp:26-31`). No Q mode checks position validity. `AP_InertialNav` freezes the last horizontal velocity when the estimator stops reporting it. So the "position lost → LAND" response that ..." — `docs/quadplane_costing.md:31`
- [closed-loop corridor criteria B1–B5] "- **B1.** Completes the full mission (arm, climb, 300 s cruise, land) with no wall contact:" — `METHODOLOGY.md:4864` — note: first wording; kept "*(Unchanged.)*" in the revision at 4951-4952
- [closed-loop corridor criteria B1–B5] "- **B1.** Completes the full mission and lands with no wall contact (|x| < 9.58 m throughout)," — `METHODOLOGY.md:4951`
- [m2 full-bench amendment letters (B-series)] "- **B1 (2026-10-12 ~17:16, after `wbench4_ground_20261012_170507` ABORTED; before any further run). No criterion" — `docs/handovers/2026-10-12_m2_full_bench.md:172` — note: dated amendment (§1.6), not a bench test
- [real-flight readiness checklist rows] "| B1 | FC↔Pi physical link and port layout replacing the SITL UDP ports. **SITL layout today:** 14550 `fly_trial`; 14551 attitude; 14552 LiDAR; 14553 flow; 14554 EKF pose (all MAVProxy `--out`); 14556 IMU (SERIAL2); 14557 heading/tag (SERIAL1); 14558 FGO node (SERIAL3; `run_trial.sh:144-300`). **Proposal:** one or two ..." — `docs/real_flight_readiness.md:71`
- [rung-1 flight-card bench checks] "| B1 | **Parameter readback** | download all parameters from the FC; diff against `rung1_template.parm` + the variant + `rung1_failsafe_fc.parm` (2026-10-12); **AHRS_EKF_TYPE = 3**, LOG_REPLAY = 1, LOG_DISARMED = 1, ARMING_SKIPCHK = 0, GPS1_TYPE = 0, EK3_SRC1_* as filed. If any differs: PARAM_SET, reboot, read back ..." — `docs/rung1_flight_cards.md:184` — note: conflicts with §7.2 watcher bench B-numbers
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B1. No watcher → arming refused.**" — `docs/real_flights_plan.md:486`

### `B2` — **CONFLICT: 8 meanings** (see flags §b)

- [Experiment T flight labels] "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: condition B (table rows METHODOLOGY.md:10118-10121: A all, B corners, C diagonal, D single) + repeat 2; expanded from "A1 B1 C1 D1 A2 … D3"
- [FGO C++ port equivalence rows] "| B2 | `room_fgo_replay.py T_A_r1`, live track | every keyframe that is anchored in both runs |" — `docs/fgo_cpp_port.md:187`
- [QuadPlane blockers] "| B2 | **The thesis backends have no origin, so Plane has no Location** | `AP_AHRS_UKF::get_origin` returns false and `location_valid=false` (fork `AP_AHRS_UKF.h:30`, `AP_AHRS_UKF.cpp:42`). Plane builds `current_loc`, home, the guided targets, take-off targets, QRTL and the altitude fence from the Location. |" — `docs/quadplane_costing.md:32`
- [closed-loop corridor criteria B1–B5] "- **B2.** Maximum physical cross-track during cruise **≤ 6.0 m**." — `METHODOLOGY.md:4953`
- [closed-loop corridor criteria B1–B5] "- **B2:** max physical cross-track **≈ 0.3–0.6 m** (band 6.0 m). Basis: the UKF's open-loop East" — `METHODOLOGY.md:7682` — note: closed-loop prediction for the UKF set against the B2 band
- [closed-loop corridor criteria B1–B5] "- **B2** (max physical cross-track in cruise): **≈ 0.15–0.4 m** (band 6.0 m)." — `METHODOLOGY.md:9286` — note: closed-loop prediction for the FGO set
- [closed-loop corridor criteria B1–B5] *(superseded)* "- **B2.** Maximum physical cross-track |x_GT| during cruise **≤ 6.5 m**." — `METHODOLOGY.md:4866` — note: marker in the revision, METHODOLOGY.md:4957: "*(Was ≤ 6.5 m.)*"
- [m2 full-bench amendment letters (B-series)] "- **B2 (2026-10-12 ~17:50, after `wbench4_hoverB_20261012_173841` ABORTED; before any further run). Harness fix (S3" — `docs/handovers/2026-10-12_m2_full_bench.md:184`
- [real-flight readiness checklist rows] "| B2 | FC↔Pi clock map: D25 robust low-percentile envelope on `/imu/time_ref`; boot-identity pre-arm check; in-flight clock-integrity latch | exists and tested in SITL | a (offline alignment), b (live) | D25; `docs/handovers/2026-10-08_fgo_cpp_timeref_fix.md` (live check `fgo_cpp_shadow_ii_fix` ALL PASS); ruling ..." — `docs/real_flight_readiness.md:72`
- [rung-1 flight-card bench checks] "| B2 | **Sensors healthy** | ground station status: flow sensor, rangefinder, compass (healthy even in nomag: arming gate), IMU, logging | ~1 min: a status screen | all healthy; no pre-arm message other than the expected "props off" items |" — `docs/rung1_flight_cards.md:185`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B2. Watcher killed while armed → LAND/disarm.**" — `docs/real_flights_plan.md:498`

### `B3` — **CONFLICT: 8 meanings** (see flags §b)

- [Experiment T flight labels] "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: condition B (table rows METHODOLOGY.md:10118-10121: A all, B corners, C diagonal, D single) + repeat 3; expanded from "A1 B1 C1 D1 A2 … D3"
- [FGO C++ port equivalence rows] "| B3 | `room_fgo_replay.py T_D_r1`, live track | as B2 |" — `docs/fgo_cpp_port.md:188`
- [QuadPlane blockers] "| B3 | **Plane GUIDED cannot fly the experiment profile** | `SET_POSITION_TARGET_LOCAL_NED` changes **altitude only** (`ArduPlane/GCS_MAVLink_Plane.cpp:1081-1101`). There are no velocity targets. Horizontal targets need a Location (`DO_REPOSITION`), which needs B2. |" — `docs/quadplane_costing.md:33`
- [closed-loop corridor criteria B1–B5] "- **B3.** EKF3 yaw error during cruise: **95th percentile ≤ 1.0°, maximum ≤ 2.0°**." — `METHODOLOGY.md:4958`
- [closed-loop corridor criteria B1–B5] "- **B3:** UKF current-time yaw error (`XUKO`) in cruise **p95 ≈ 0.17°, max ≈ 0.33°** (band 1.0 / 2.0°)." — `METHODOLOGY.md:7681` — note: closed-loop prediction for the UKF set against the B3 band
- [closed-loop corridor criteria B1–B5] "- **B3** (`XFGO` yaw error in cruise): **p95 ≈ 0.3°, max ≈ 1.0°** (band 1.0 / 2.0°). Basis: shadow (b) 0.28° / 0.95°." — `METHODOLOGY.md:9283` — note: closed-loop prediction for the FGO set (XFGO yaw)
- [closed-loop corridor criteria B1–B5] *(superseded)* "- **B3.** EKF3 yaw error (`XKF1` vs SIM) during cruise: **95th percentile ≤ 2°, maximum ≤ 4.5°**." — `METHODOLOGY.md:4870` — note: marker in the revision, METHODOLOGY.md:4962: "*(Was p95 ≤ 2°, maximum ≤ 4.5°.)*"
- [m2 full-bench amendment letters (B-series)] "- **B3 (2026-10-12 ~18:08, after `wbench4_hoverC_20261012_175909`; before any further run). Harness fault; A10 repeat.**" — `docs/handovers/2026-10-12_m2_full_bench.md:195`
- [real-flight readiness checklist rows] "| B3 | Measured link latency distribution (one-way, jitter) for every Pi→FC stream | not built | b (feeds H2); a (report) | Plan §9.2 starts at 5–15 ± 3 ms [E], "to be replaced by the bench-measured distribution". | 0.5 d | B1 |" — `docs/real_flight_readiness.md:73`
- [rung-1 flight-card bench checks] "| B3 | **Rangefinder** | on the ground: reading ≈ `RNGFND1_GNDCLR`; then lift the vehicle by hand to ~1 m and back | ~30 s: one lift spans the range used | ground reading within ±2 cm of GNDCLR (or "out of range low" if RNGFND1_MIN > resting height: RECORD, it is a known limit, §9 item 11 of the pre-registration); ~1 ..." — `docs/rung1_flight_cards.md:186`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B3. Heartbeat loss with the watcher process alive.**" — `docs/real_flights_plan.md:509`

### `B4` — **CONFLICT: 6 meanings** (see flags §b)

- [FGO C++ port equivalence rows] "| B4 | `T_A_r1` whole-flight batch (hindsight) | every batch key (X(k) of `key_t`): |Δp| ≤ 1 mm, |Δyaw| ≤ 0.01°, same key set |" — `docs/fgo_cpp_port.md:189`
- [closed-loop corridor criteria B1–B5] "- **B4.** No fast runaway: 1 s-smoothed |GT lateral speed| during cruise **≤ 0.25 m/s**." — `METHODOLOGY.md:4874`
- [closed-loop corridor criteria B1–B5] "- **B4.** 1 s-smoothed |GT lateral speed| during cruise **≤ 0.25 m/s**." — `METHODOLOGY.md:4963` — note: "(Unchanged value; new yaw basis.)"
- [closed-loop corridor criteria B1–B5] "- **B4, B5:** as the sets. Lateral speed is typically ≤ 0.05 m/s, but a D22-type episode can reach ~0.3 m/s (the" — `METHODOLOGY.md:9291` — note: closed-loop prediction (B4, B5) for the FGO set
- [m2 full-bench amendment letters (B-series)] "- **B4 (2026-10-12 ~18:25, after `wbench4_m2_20261012_181437`; before any further run). Two harness faults; the one" — `docs/handovers/2026-10-12_m2_full_bench.md:205`
- [real-flight readiness checklist rows] "| B4 | Pi time base: `use_sim_time:=false` and wall-clock ROS time on every node; no `/clock` | needs adapting for real sensors | a, b | Every launch line uses `use_sim_time:=true` (CLAUDE.md "Launch Sequence"; `run_trial.sh`). | 0.5 d | A3, A10 |" — `docs/real_flight_readiness.md:74`
- [rung-1 flight-card bench checks] "| B4 | **Flow sign (ArduPilot's standard flow check)** | over the textured floor, at ~0.5–1 m, roll the vehicle by hand left/right, then pitch forward/back, ~3 cycles each | ~1 min: three cycles per axis show the sign unambiguously | in the log, `OF.flowX` follows `OF.bodyX` and `OF.flowY` follows `OF.bodyY` (same ..." — `docs/rung1_flight_cards.md:187`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B4. Geofence breach, hand-carried → the configured action.**" — `docs/real_flights_plan.md:518`

### `B5` — **CONFLICT: 5 meanings** (see flags §b)

- [FGO C++ port equivalence rows] "| B5 | `T_D_r1` whole-flight batch | as B4 |" — `docs/fgo_cpp_port.md:190`
- [closed-loop corridor criteria B1–B5] "- **B5.** No oscillation: cruise gyro rms roll ≤ 0.05, pitch ≤ 0.0108, yaw ≤ 0.02 rad/s (the" — `METHODOLOGY.md:4877`
- [closed-loop corridor criteria B1–B5] "- **B5.** No oscillation: cruise gyro rms roll ≤ 0.05, pitch ≤ 0.0108, yaw ≤ 0.02 rad/s." — `METHODOLOGY.md:4966`
- [closed-loop corridor criteria B1–B5] "- B5's window is now the longest contiguous run of vy > 0.3 (gaps ≤ 1 s), then (start + 5, end − 5)." — `METHODOLOGY.md:9943` — note: D28 RULED 2026-10-02: new B5 window
- [closed-loop corridor criteria B1–B5] *(superseded)* "| B5 (gyro rms) | the definition of its source band (`eval/rgs_profile.py`): cruise span with GT forward speed > 0.3 m/s (51-sample smoothing), **trimmed by 5 s at each end** |" — `METHODOLOGY.md:5075` — note: B5 scoring window; replaced by the D28 scorer fix, METHODOLOGY.md:9943
- [m2 full-bench amendment letters (B-series)] "- **B5 (2026-10-12 ~18:28, after `wbench4_m2_20261012_182305`, the B4 repeat; before any further run). V3 failed; one" — `docs/handovers/2026-10-12_m2_full_bench.md:217`
- [rung-1 flight-card bench checks] "| B5 | **Arming checks run** | attempt to arm with props off (motor safety per lab rules) | ~30 s | arming either succeeds with every check run, or fails only on the props-off/safety item; never a skipped check |" — `docs/rung1_flight_cards.md:188`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] "**B5. Mocap dropout / stale pose (G2).** *(RE-WORDED 2026-10-12 under ruling 4 of "RULINGS (user, 2026-10-12)"," — `docs/real_flights_plan.md:533`
- [watcher bench tests (§7.2 B0–B13 and SITL variants)] *(superseded)* "- **Old wording (2026-10-10, pre-registered), kept verbatim:**" — `docs/real_flights_plan.md:551` — note: B5 old wording (2026-10-10), re-worded under ruling 4 of 2026-10-12 (line 533)

### `B8e` — **UNDEFINED** (see flags §a)

- [watcher bench tests (§7.2 B0–B13 and SITL variants)] *(used, not defined here)* "- (b) In ALT_HOLD, trigger each automatic path in turn: watcher kill (B2b), estimator invalid (B8e), dependency loss" — `docs/real_flights_plan.md:656` — note: no "B8e" definition; plausibly §7.2 B8 part (e) at real_flights_plan.md:625; not inferred

### `C1` — **CONFLICT: 6 meanings** (see flags §b)

- [C++ heading-port equivalence bands] "- **C1, VP existence and validity identical on every frame.** A mismatch is allowed **only** if it" — `METHODOLOGY.md:5907`
- [C++ heading-port equivalence bands] "| C1 | VP existence and validity identical on **all** frames (0 mismatches, none needing the boundary rule) |" — `METHODOLOGY.md:6054` — note: result row
- [D25 FGO shadow criteria] "- **C1:** from the first received state (`XFGI`) to disarm, `XFGO.OV` = 1 at **every** sample. Equivalently, the" — `METHODOLOGY.md:9165`
- [Experiment T flight labels] "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: condition C (table rows METHODOLOGY.md:10118-10121: A all, B corners, C diagonal, D single) + repeat 1; expanded from "A1 B1 C1 D1 A2 … D3"
- [initial-sigma audit verification items] "- C1: with the yaw fix alone, the output is byte-identical to the trace's F_YAW0 = 1° demonstration (0.150 m, yaw max" — `METHODOLOGY.md:13325` — note: verification item in the sigma-audit METHODOLOGY entry; distinct from heading band C1
- [real-flight readiness checklist rows] "| C1 | Core real-FC parameter file: EKF3 sources from `gnss_denied.parm` and `gnss_denied_nomag.parm` (`EK3_SRC1_POSXY 0`, `POSZ 2`, `VELZ 0`, `YAW 0`, `GPS1_TYPE 0`, compass present but unused); `FS_EKF_ACTION` LAND; battery failsafe; RC mode switch; `LOG_*` (I1) | not built | a, b | **Hazards in the current files:** ..." — `docs/real_flight_readiness.md:84` — note: section C "Parameter files with real sensor values"
- [stage-3 UKF closed-loop criteria (draft)] "- **C1 completion:** the profile completes under UKF control with all of:" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:159`
- [stage-3 UKF closed-loop criteria (draft)] "- C1: completion under UKF control with no behaviour-caused takeover or failsafe;" — `docs/handovers/2026-10-12_port_merge_u4_drafts.md:188` — note: same meaning restated

### `C1a`

- [initial-sigma audit verification items] "**C1a: the yaw-only correction reproduces the trace's F_YAW0 = 1° demonstration. PASS.**" — `docs/handovers/2026-10-10_initial_sigma_audit.md:119`

### `C1b`

- [initial-sigma audit verification items] "**C1b: adding roll/pitch 5° (the full change, which is what the pass will run).**" — `docs/handovers/2026-10-10_initial_sigma_audit.md:131`

### `C2` — **CONFLICT: 6 meanings** (see flags §b)

- [C++ heading-port equivalence bands] "- **C2, |Δψ| ≤ 1e-6 deg on every frame where both have a VP.** Basis:" — `METHODOLOGY.md:5911`
- [D25 FGO shadow criteria] "- **C2:** **0** negative-age samples (10⁶ < `Age` < `UINT32_MAX`) in the whole log." — `METHODOLOGY.md:9167`
- [Experiment T flight labels] "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: condition C (table rows METHODOLOGY.md:10118-10121: A all, B corners, C diagonal, D single) + repeat 2; expanded from "A1 B1 C1 D1 A2 … D3"
- [initial-sigma audit verification items] "**C2: C++ core. PARKED (coordinator, 2026-10-10: thesis results first).**" — `docs/handovers/2026-10-10_initial_sigma_audit.md:151`
- [real-flight readiness checklist rows] "| C2 | Rangefinder parameters: `RNGFND1_TYPE`, `ORIENT 25`, `MIN`, `MAX`, `POS_X/Y/Z`, `GNDCLR` | needs adapting for real sensors | a, b | `lidar_rangefinder.parm` (`TYPE 10`, `0.05`/`40`, `POS_Z 0.12`, all sim values). | 0.5 d | A8 |" — `docs/real_flight_readiness.md:85`
- [stage-3 UKF closed-loop criteria (draft)] "- **C2 physical excursion:** the maximum horizontal distance of the mocap position from the commanded path (the" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:164`

### `C3` — **CONFLICT: 6 meanings** (see flags §b)

- [C++ heading-port equivalence bands] "- **C3, |Δsupport| ≤ 1e-6 px** on every frame where both have a VP (same basis)." — `METHODOLOGY.md:5917`
- [D25 FGO shadow criteria] "- **C3:** the first state arrives ≥ 10 s (sim) after the node's first `/imu/time_ref` (from the clock-map" — `METHODOLOGY.md:9168`
- [Experiment T flight labels] "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: condition C (table rows METHODOLOGY.md:10118-10121: A all, B corners, C diagonal, D single) + repeat 3; expanded from "A1 B1 C1 D1 A2 … D3"
- [initial-sigma audit verification items] "**C3: `final_rerun_checks.py corrections` has the fifth check.**" — `docs/handovers/2026-10-10_initial_sigma_audit.md:158`
- [real-flight readiness checklist rows] "| C3 | Flow parameters: `FLOW_TYPE 5`, `FLOW_POS_X/Y/Z`, `FLOW_ORIENT_YAW`, `EK3_FLOW_DELAY` | needs adapting for real sensors | a, b | **`FLOW_POS_Z` conflicts in SITL: 0.13 in `flow_ekf.parm`, overridden to 0.25 in `consolidated_rerun.parm`.** One measured real value replaces both. `EK3_FLOW_DELAY` is the default 10 ..." — `docs/real_flight_readiness.md:86`
- [stage-3 UKF closed-loop criteria (draft)] "- **C3 validity:** the UKF's `horiz_pos_rel` (`XUKF`/`XUKO` `SS` bit 3) set and `Healthy` on 100 % of W; no" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:166`

### `C4` — **CONFLICT: 3 meanings** (see flags §b)

- [C++ heading-port equivalence bands] "- **C4, quality identical** on every frame (it is a floor of support / S_MIN × 50, so C3 implies it" — `METHODOLOGY.md:5918`
- [real-flight readiness checklist rows] "| C4 | ExtNav parameters for the tag and heading paths: `VISO_TYPE 1`, `EK3_SRC1_POSXY/YAW 6`, `VISO_POS_M_NSE`, `VISO_YAW_M_NSE`, `VISO_DELAY_MS`, `ARMING_SKIPCHK 262144` | needs adapting for real sensors | a, b if P-HOLD (or forward heading) is flown | `h_extnav.parm` (`VISO_DELAY_MS 31`, `POS_M_NSE 0.02` from S0), ..." — `docs/real_flight_readiness.md:87`
- [stage-3 UKF closed-loop criteria (draft)] "- **C4 smoothness** (as the SITL B4/B5):" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:168`

### `C5`

- [real-flight readiness checklist rows] "| C5 | `MOT_THST_HOVER` and `MOT_HOVER_LEARN`; attitude gains | needs adapting for real sensors | a, b | `h_extnav.parm` pins 0.310 with `MOT_HOVER_LEARN 1` (SITL iris). | in A2 | A2 |" — `docs/real_flight_readiness.md:88`

### `C6`

- [real-flight readiness checklist rows] "| C6 | Sensor noise and filters: INS filters (`INS_GYRO_FILTER`/`INS_ACCEL_FILTER` 20 Hz in SITL), harmonic notch, vibration (`VIBE`); EKF3 `*_NSE` | needs adapting for real sensors | a, b | The UKF/FGO noise matching assumes EKF3's default `*_NSE` and dt 0.0125 s (CLAUDE.md "GTSAM IMU Preintegration"). That still ..." — `docs/real_flight_readiness.md:89`

### `C7`

- [real-flight readiness checklist rows] "| C7 | Estimator geometry constants, **hard-coded in three implementations**: `RANGE_LEVER 0.12` and `CAM_OFFSET 0.25` in `measurement_models.py:32-33`, `factors.h:28-29` and `AP_NavUKF.cpp:33`; a bare literal `first_range + 0.12` at `fgo_core.cpp:69`; port `RNG_MIN 0.05`, `RNG_MAX 40` (`AP_NavUKF.cpp:29`); ..." — `docs/real_flight_readiness.md:90`

### `C8`

- [real-flight readiness checklist rows] "| C8 | Fork parameters: `AHRS_EKF_TYPE 12/13`, `AHRS_UKF_ENABLE/EXTYAW/EXTPOS/TFAIL`, `AHRS_FGO_ENABLE`, `SERIALn_PROTOCOL` for the node | exists and tested in SITL | b | `closedloop_ukf.parm`, `closedloop_fgo.parm`, `h_ukf_tag.parm`. **`AHRS_UKF_TFAIL` (a test hook) has persisted in eeprom before** (METHODOLOGY "H ..." — `docs/real_flight_readiness.md:91`

### `D3` — **CONFLICT: 4 meanings** (see flags §b)

- [D-rulings] *(superseded)* "- **D3 is withdrawn.** My earlier reading, "round-off amplified by the runaway plus E5-permitted" — `METHODOLOGY.md:6325` — note: withdrawn; the original queued D3 text is not in the current docs
- [D-rulings] *(superseded)* "- **D3:** withdrawn (the UKF step 2 bug)." — `docs/decisions_queue.md:261`
- [experiment T run labels] *(used, not defined here)* "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: "… D3" = condition D repeat 3
- [real-flight readiness items] "| D3 | Camera–IMU (and LiDAR–IMU) extrinsics: lever arms; downward-camera rotation about z (sets the flow axes); forward-camera yaw offset (a heading bias) | not built | a, b | There is no tool. The simulated mounts are ideal (CLAUDE.md "Drone Model"). | 1–2 d (tape measure plus a mocap rotation and hover check) | A1, ..." — `docs/real_flight_readiness.md:99` — note: CONFLICT: readiness calibration item, not the D-ruling of the same number
- [rung-1 calendar gates] "| Mon 19 | R7 recorder test; **R13 hand-carried check + same-day pipeline** | **D3: Replay check passes on the hand-carried log (or its failure is characterised), the converter runs on real data, the scorer gives numbers.** The flow-aiding Replay check is repeated on the first hover log (Tue 20). |" — `docs/minimal_real_flight_plan.md:396` — note: CONFLICT: calendar gate in §6, not the D-ruling
- [rung-1 data-integrity checklist] "| D3 | `RFRH` continuity: no gap > 50 ms between take-off and landing | none |" — `docs/rung1_flight_cards.md:308` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number

### `D4` — **CONFLICT: 3 meanings** (see flags §b)

- [D-rulings] "- **D4:** information only (the port's binaries rebuilt); no ruling needed." — `docs/decisions_queue.md:262` — note: only written mention of D4 as a ruling
- [real-flight readiness items] "| D4 | Camera–FC time offsets: `EK3_FLOW_DELAY`, `VISO_DELAY_MS` (D2/D20 receipt rule), the flow capture stamp | needs adapting for real sensors | a, b | The D2/D20 procedure exists and was used in SITL (D20; `tags_extnav.parm`). On hardware the capture-to-receipt latency is new (plan §9.4 stage 0). | 1 d bench | A3, ..." — `docs/real_flight_readiness.md:100` — note: CONFLICT: readiness calibration item, not the D-ruling of the same number
- [rung-1 data-integrity checklist] "| D4 | **`DSF.Dp` = 0** (no dropped writes) for the whole flight | 0 |" — `docs/rung1_flight_cards.md:309` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number

### `E1` — **CONFLICT: 2 meanings** (see flags §b)

- [UKF port equivalence bands] "| E1 | 3-D position difference, `dsn_tex_r2` | **max ≤ 0.05 m, rms ≤ 0.01 m** | Same algorithm, both in double precision. The only difference expected is floating-point operation order (~1e-15 relative per operation), amplified by the filter. 0.05 m is < 0.04% of the 150 m travel and at least 10× below the smallest ..." — `METHODOLOGY.md:5467` — note: conflicts with readiness E1 (flow validity)
- [UKF port equivalence bands] "- E1: max ≤ 0.05 m, rms ≤ 0.01 m;" — `docs/handovers/2026-10-11_r1_ukf_port.md:123` — note: same band restated
- [real-flight readiness checklist rows] "| E1 | Flow validity = inlier ratio **and** feature count, ONE flag from one source, identical for EKF3, the UKF and the FGO. The threshold is calibrated on `p1c_*` only. | not built | a, b (it also feeds EKF3) | **Current committed state** (plan §7, `4556714`, lines 228–235; ruling 2026-10-09 "D22 is a SHARED ..." — `docs/real_flight_readiness.md:109` — note: conflicts with E1 of the UKF port equivalence bands

### `E2`

- [UKF port equivalence bands] "| E2 | 3-D position difference, `dsn_blank_r1` (unbounded inertial divergence amplifies any difference) | **max ≤ 0.05 m + 1e-4 × the offline UKF's displacement from cruise start** | The same round-off basis; the relative term allows the exponential amplification of an unaided inertial solution while still catching ..." — `METHODOLOGY.md:5468`

### `E3`

- [UKF port equivalence bands] "| E3 | yaw difference | **max ≤ 0.05°** (both logs) | Same basis. 0.05° is < 1% of the smallest yaw effect interpreted (the ~5° end-wall transients). |" — `METHODOLOGY.md:5469`

### `E4`

- [UKF port equivalence bands] "| E4 | gyro-z bias (rate form) and accelerometer bias | **\|Δ\| ≤ 0.1 deg/min and ≤ 0.001 m/s²** | ≤ 1% of the smallest bias magnitudes discussed (gyro drift 6.6–11.1 deg/min; the corrected accel-z bias 0.008 m/s²). |" — `METHODOLOGY.md:5470`

### `E5`

- [UKF port equivalence bands] "| E5 | gate decisions (flow X/Y, range, yaw-pseudo firings) | **≥ 99.9% identical**; accepted counts equal to within 0.1% | Decisions compare a test ratio with 1, so a round-off-level difference can flip only near-threshold ties. |" — `METHODOLOGY.md:5471`
- [UKF port equivalence bands] "- E5, for each of `FXa`, `FYa`, `Ra`: the increment over the paired span [first pair, last pair], taken from the" — `docs/u10_replay_gate_band.md:235` — note: replay-gate increment form of E5; the cumulative form FAILED AS WORDED and the increment form was accepted post hoc (METHODOLOGY.md:13779, 13800)

### `F3d` — **UNDEFINED** (see flags §a)

- [offline tests (F-tests)] *(used, not defined here)* "job: f3u_fwdc_tex_r1_10 cd /home/makerspace/thesis_ws && OPENBLAS_NUM_THREADS=1 F_TAG=F3d10 F_YAW0_DEG=10 F_HDG_FROM_CRUISE=1 nice -n 10 /home/makerspace/venv-evo/bin/python src/estimators/ukf_replay.py fwdc_tex_r1 heading" — `docs/handovers/2026-10-09_final_rerun_dryrun.txt:231` — note: run tag of the F3 injected-yaw replays (F3d10/30/60/90); no prose definition

### `F15` — **UNDEFINED** (see flags §a)

- [final results pack figures] *(used, not defined here)* "- F05 is CURRENT against its JSON only (no numbers.md row). F08, F14 and F15 use METHODOLOGY-only values where numbers.md has no row." — `docs/handovers/2026-10-11_final_results_pack.md:30` — note: no figure "F15" exists; apparently F15a+F15b together

### `FE1`

- [FGO node equivalence bands (FE)] "- **FE1:** max 3-D position difference **≤ 1e-6 m** on both logs;" — `METHODOLOGY.md:6502`
- [FGO node equivalence bands (FE)] "- **FR1:** `FgoNodeCore` with `tags=False` reproduces FGO step 2 on `dsn_tex_r1` (FE1–FE4 as registered)." — `docs/h_backends_tag_input.md:140` — note: FE1–FE4 reused as registered for FR1

### `FE2`

- [FGO node equivalence bands (FE)] "- **FE2:** max yaw difference **≤ 1e-6°**;" — `METHODOLOGY.md:6503`

### `FE3`

- [FGO node equivalence bands (FE)] "- **FE3:** keyframe count, and flow/range factor counts, **identical**;" — `METHODOLOGY.md:6504`

### `FE4`

- [FGO node equivalence bands (FE)] "- **FE4:** the gyro-z bias difference ≤ 1e-9 deg/min." — `METHODOLOGY.md:6505`

### `FG1`

- [FGO closed-loop gates (FG)] "**FG1 — backend equivalence to the offline FGO** (on each shadow run: the states ArduPilot received," — `METHODOLOGY.md:8045`

### `FG2`

- [FGO closed-loop gates (FG)] "**FG2 — validity signal:**" — `METHODOLOGY.md:8054`

### `FG3`

- [FGO closed-loop gates (FG)] "**FG3 — output-predictor check** (as the UKF's D9 check, with the bands unchanged; `XFGO` current" — `METHODOLOGY.md:8059`

### `FG3b`

- [FGO closed-loop gates (FG)] "- Plus **FG3b: output age ≤ 250 ms for 100% of samples from arming to disarm.**" — `METHODOLOGY.md:8065`

### `FN1`

- [FGO node tag-input bands (FN/FR)] "| FN1 | 3-D position difference per keyframe | **max ≤ 1e-6 m** (the `%.6f` print rounding) |" — `docs/h_backends_tag_input.md:114`

### `FN2`

- [FGO node tag-input bands (FN/FR)] "| FN2 | yaw difference per keyframe (same writer) | **max ≤ 1e-6°** |" — `docs/h_backends_tag_input.md:115`

### `FN3`

- [FGO node tag-input bands (FN/FR)] "| FN3 | structure | the same keyframe count and times; t_anchor = 49.138 s on both; tag factors equal (8,584); flow and range factor counts equal; 0 keyframe failures |" — `docs/h_backends_tag_input.md:116`

### `FN4`

- [FGO node tag-input bands (FN/FR)] "- **FN4 (band; FG1's (b) bands, the position band tightened to the tag scale):**" — `docs/h_backends_tag_input.md:124`

### `FR1`

- [FGO node tag-input bands (FN/FR)] "- **FR1:** `FgoNodeCore` with `tags=False` reproduces FGO step 2 on `dsn_tex_r1` (FE1–FE4 as registered)." — `docs/h_backends_tag_input.md:140`
- [FGO node tag-input bands (FN/FR)] "| FGO regression FR1 | PASS |" — `METHODOLOGY.md:11041`

### `G1` — **CONFLICT: 9 meanings** (see flags §b)

- [Experiment H S1 per-flight gates] "- **G1:** the profile completes, every `HSEG` and `OCCLUDER ON/OFF` marker present, landed;" — `METHODOLOGY.md:10672`
- [Experiment O per-flight gates] "- **G1:** all OUTBACK markers present; GNSS OFF and ON each logged once." — `METHODOLOGY.md:10352`
- [Experiment T per-flight gates] "- **G1:** 5 laps complete (20 `LEG START` markers and `LAPS END`), landed; `AHRS_EKF_TYPE 10`, `LOG_REPLAY 1`," — `METHODOLOGY.md:10161`
- [H backend ground-test gates (S2/S3 tag input)] "- **G1 (configuration, from the PARM dump):**" — `docs/h_backends_tag_input.md:420` — note: UKF (S2) ground test §5.1; FGO (S3) G1 at line 448; re-run far-spawn with changes at METHODOLOGY 11322
- [U10 replay-gate criteria] "| **G1** | **Initialises before arming, with the log's geometry** (definition §4.1) | must hold | the arming gate in type 12 needs an initialised UKF (`AP_AHRS_UKF::pre_arm_check`). If the rangefinder reads below its minimum on the ground, this needs U4 (`u4_init_from_gndclr` line) |" — `docs/u10_replay_gate_band.md:191`
- [U10 replay-gate criteria] *(superseded)* "| **G1** | **Initialises before arming.** `ukf_geometry.csv` resolved with every geometry source `log_parm`. 0 late-PARM warnings, or each one listed and shown not to change a value | must hold | the arming gate in type 12 needs an initialised UKF (`AP_AHRS_UKF::pre_arm_check`). If the rangefinder reads below its ..." — `docs/u10_replay_gate_band_draft.md:121` — note: draft, NOT in force (line 3); late-PARM wording replaced by N3 in the signed band
- [backend ground-test gates (D9 P3 / D17 V3 / D19 FGO)] "- **(G1) Configuration:** the log's PARM dump has `AHRS_EKF_TYPE = 12` and `AHRS_UKF_ENABLE = 1`." — `METHODOLOGY.md:7379` — note: UKF P3 ground test; D17 V3 (line 7618) and the FGO ground test (line 8076) re-define G1 with their own parameter lists
- [backend ground-test gates (D9 P3 / D17 V3 / D19 FGO)] "- G1: `AHRS_EKF_TYPE 13`, `AHRS_FGO_ENABLE 1`, `SERIAL3_PROTOCOL 2`;" — `METHODOLOGY.md:8076` — note: FGO ground test variant of the same series
- [board firmware go/no-go] "| G1 | The exact board is named, and the firmware was built for its hwdef (not the stand-in of §1) | the `.apj` `board_id` = the board's |" — `docs/board_firmware_plan.md:271` — note: §7 go/no-go before the first powered test on the fork
- [heading ground-test gates (VISO_DELAY_MS, closed-loop Part 1)] "- **G1, yaw-only ExtNav fusion.**" — `METHODOLOGY.md:5033`
- [mocap watcher gaps] "| G1 | **No mocap input.** The watcher reads Gazebo `/ground_truth/pose`. It needs the mocap rigid-body stream (e.g. VRPN or NatNet to ROS 2) in the mocap frame, aligned to the box definition. | all |" — `docs/real_flights_plan.md:442` — note: plan §7.2 gap list; conflicts with U10 G1–G6, readiness G-rows and test gates of the same labels
- [real-flight readiness checklist] *(used, not defined here)* "Lua layer needs scripting in the board build (flash, G1). Only `sim/scripts/o_source_switch.lua` exists. | 2–3 d | F2, B1, G1a |" — `docs/real_flight_readiness.md:117` — note: readiness has rows G1a/G1b but no plain G1 row; also cited at line 144 ("F3, G1")

### `G1a`

- [real-flight readiness checklist] "| G1a | Baseline firmware image for (a): the pinned `7bac20cbcc` (tag `thesis-baseline`) built for the real board, or a stock release; `.apj` and parameter dump archived (plan §9.2 step 1) | not built | a | `~/ardupilot/build/` contains only `sitl/` (checked). The pinned commit is preferred over a stock release so ..." — `docs/real_flight_readiness.md:124`
- [real-flight readiness checklist] "| G1a | Baseline firmware image (pinned or stock) | 1 | SW+HW | 0.5–1 d (R5) | | READY (script); WAITS (board, S6) |" — `docs/real_flight_readiness_by_rung.md:171` — note: re-costed by rung

### `G1b`

- [real-flight readiness checklist] "| G1b | Thesis firmware (fork `~/ardupilot_ukf`, branch `ukf-jitter-fix`) for the real board: `AP_NavUKF`, `AP_NavFGO`, `AP_AHRS_UKF/FGO`, `thesis_nav_check` | not built | b (and a, only if the UKF shadows onboard) | **BLOCKER: the port is compiled for SITL only.** `AP_NavUKF.h:29` reads `#define AP_NAVUKF_ENABLED ..." — `docs/real_flight_readiness.md:125`

### `G2` — **CONFLICT: 10 meanings** (see flags §b)

- [Experiment H S1 per-flight gates] "- **G2:** `VISP` = `/tags/sent`;" — `METHODOLOGY.md:10673`
- [Experiment O per-flight gates] "- **G2:** EKF3 changes source set twice (to set 2 after OFF, to set 1 after ON), from the `XKFS.SS` transitions." — `METHODOLOGY.md:10353`
- [Experiment T per-flight gates] "- **G2 (identical measurements):**" — `METHODOLOGY.md:10163`
- [H backend ground-test gates (S2/S3 tag input)] "- **G2 (fix accepted):**" — `docs/h_backends_tag_input.md:424` — note: FGO variant line 452
- [U10 replay-gate criteria] "| **G2** | **Stays valid through the hover and the legs:** `SS` bit 3 (`horiz_pos_rel`) set and `Healthy` = 1 on **every** `ukf_shadow.csv` row in W; `FlowAgeMs` < 5000 on every row in W; the rows cover W (§4.1) | 100 % of W | in closed loop a 5 s aiding gap (`AID_TIMEOUT_MS`) makes `thesis_nav_check` command LAND. A ..." — `docs/u10_replay_gate_band.md:192`
- [U10 replay-gate criteria] *(superseded)* "| **G2** | **Stays valid through the hover and the legs:** `SS` bit 3 (`horiz_pos_rel`) set and `Healthy` = 1 on **every** row in W; `FlowAgeMs` < 5000 throughout W | 100 % of W | in closed loop a 5 s aiding gap (`AID_TIMEOUT_MS`) makes `thesis_nav_check` command LAND. A gap in Replay means a LAND in stage 3 |" — `docs/u10_replay_gate_band_draft.md:122` — note: draft, NOT in force (line 3); coverage-of-W rule added by N2 in the signed band
- [backend ground-test gates (D9 P3 / D17 V3 / D19 FGO)] "- **(G2) Arming:** the pre-arm checks pass (including the UKF's own, "UKF not initialised" /" — `METHODOLOGY.md:7380`
- [board firmware go/no-go] "| G2 | Flash free ≥ 32 kB after the fork, for the exact board and feature set | §2 table, re-measured |" — `docs/board_firmware_plan.md:272` — note: §7 go/no-go before the first powered test on the fork
- [heading ground-test gates (VISO_DELAY_MS, closed-loop Part 1)] "- **G2, arming with the heading node.** It arms with no VisualOdom or EKF pre-arm failure, and" — `METHODOLOGY.md:5039`
- [mocap watcher gaps] "| G2 | **No stale-pose check.** The box and tilt rules are evaluated only when a pose ARRIVES, and the `box=1` flag is static, so a stopped mocap stream triggers nothing. §7 requires it to. | B5 |" — `docs/real_flights_plan.md:443` — note: plan §7.2 gap list; conflicts with U10 G1–G6, readiness G-rows and test gates of the same labels
- [mocap watcher gaps] "| **G2** no stale-pose check | `core.pose_fresh()`, evaluated on every loop, not only when a pose arrives. A pose is not fresh when: older than 0.5 s; the tracked flag is 0 (immediate); or, ONLY when the source has no tracked flag, bit-identical for at least 0.5 s. Duplicate frame numbers are ignored. Recovery needs 2 ..." — `docs/handovers/2026-10-10_mocap_watcher_build.md:58` — note: restated with the implementation (G1–G11 table, lines 57–67)
- [real-flight readiness checklist] "| G2 | UKF CPU load on the FC MCU at 80 Hz predict plus updates; loop-time margin | not built | b (onboard UKF) | Estimate only: 5–8% CPU, 0.3–0.4 ms per predict in double on H7 (Part C §5.3). Never measured. | 0.5 d bench (scheduler `PM` / perf logging) | G1b |" — `docs/real_flight_readiness.md:126` — note: section G (estimators and firmware) of the readiness checklist; distinct from watcher gap G2

### `G3` — **CONFLICT: 10 meanings** (see flags §b)

- [Experiment H S1 per-flight gates] "- **G3:** max sent-fix error vs GT ≤ 3 × σ_pos (no wrong ids);" — `METHODOLOGY.md:10674`
- [Experiment O per-flight gates] "- **G3:** EKF3 aligned yaw and used GPS before OFF. Pass if `XKF4.SS` `using_gps` is true for ≥ 5 s before OFF." — `METHODOLOGY.md:10354`
- [Experiment T per-flight gates] "- **G3:** every sent fix within 0.3 m (horizontal) and 3° of GT (no wrong ids)." — `METHODOLOGY.md:10167`
- [H backend ground-test gates (S2/S3 tag input)] "- **G3 (re-anchor visible):**" — `docs/h_backends_tag_input.md:428` — note: FGO variant line 454
- [U10 replay-gate criteria] "| **G3** | **No numerical failure:** `n_chol_fail` = 0 over the whole log, read from the Replay's `ukf_stats.csv`. **A missing `ukf_stats.csv`, or one without an `n_chol_fail` row, FAILS G3** (U10 rule 1). `n_chol_retry` is reported | = 0 | the jitter fix (2026-10-09): 0 fallbacks on all SITL data [V]; the counters in ..." — `docs/u10_replay_gate_band.md:193`
- [backend ground-test gates (D9 P3 / D17 V3 / D19 FGO)] "- **(G3) The UKF is the ACTIVE attitude source:** during the armed hold, the logged AHRS attitude" — `METHODOLOGY.md:7382` — note: FGO variant line 8078: "G3: ATT matches `XFGO` at ≤ 0.1° p95"
- [board firmware go/no-go] "| G3 | SITL byte-identity of the `board-h743` commit vs the reference, re-run if the source changed | identical (§2.5) |" — `docs/board_firmware_plan.md:273` — note: §7 go/no-go before the first powered test on the fork
- [heading ground-test gates (VISO_DELAY_MS, closed-loop Part 1)] "- **G3, EKF origin.** G1 and G2 pass without an origin ever being set (none is set in this" — `METHODOLOGY.md:5041`
- [mocap watcher gaps] "| G3 | **No rigid-body identity check** (wrong body, or a swapped or renamed asset). | B6 |" — `docs/real_flights_plan.md:444` — note: plan §7.2 gap list; conflicts with U10 G1–G6, readiness G-rows and test gates of the same labels
- [real-flight readiness checklist] "| G3 | UKF port algorithm: shadow and flying, tag ExtNav input, option (i) attitude hold on invalid output, first tag anchor refused once armed, jitter fix | exists and tested in SITL | b | Installed `ukf-jitter-fix` `abb0357d` (METHODOLOGY "UKF jitter correction MERGED"). S2v2 ×3; `cl_ukf_*_v2` PASS; tier B UB1–UB5 ..." — `docs/real_flight_readiness.md:127` — note: section G (estimators and firmware) of the readiness checklist; distinct from watcher gap G3

### `G4` — **CONFLICT: 10 meanings** (see flags §b)

- [Experiment H S1 per-flight gates] "- **G4:** IMU-gap rule ok;" — `METHODOLOGY.md:10675`
- [Experiment O per-flight gates] "- **G4:** both replays aligned before OFF and fused GNSS on both sides of the indoor segment." — `METHODOLOGY.md:10355`
- [Experiment T per-flight gates] "- **G4:** both replays complete with 0 keyframe failures; FGO tag factors ≥ 95% of the sent fixes after the anchor." — `METHODOLOGY.md:10168`
- [H backend ground-test gates (S2/S3 tag input)] "- **G4 (reset consumed):** a Copter `EKF_YAW_RESET` event at the anchor, and the GUIDED target follows the reset." — `docs/h_backends_tag_input.md:434`
- [U10 replay-gate criteria] "| **G4** | **Accuracy against mocap:** UKF (`XUKO`, message `RUKO`) evo -a (SE(3), `t_max_diff` 0.05) over W ≤ **max(2.0 × EKF3_R, EKF3_R + 0.10 m)**, with EKF3_R = the replayed EKF3 (`XKF1@100`) on the same flight, window and Replay output | per flight | see below |" — `docs/u10_replay_gate_band.md:194`
- [backend ground-test gates (D9 P3 / D17 V3 / D19 FGO)] "- **(G4) Stable on the ground:** over the armed hold, `XUKO` horizontal position stays within 0.10 m of" — `METHODOLOGY.md:7388` — note: yaw bound re-worded for D17 V3 (line 7620) and the FGO (line 8079-8081: gyro-drift-relative yaw)
- [board firmware go/no-go] "| G4 | P1–P10 all pass on the bench | as in §5 |" — `docs/board_firmware_plan.md:274` — note: §7 go/no-go before the first powered test on the fork
- [heading ground-test gates (VISO_DELAY_MS, closed-loop Part 1)] "- **G4, latency (run 1).** Minimum capture-to-receipt latency, from two independent measures:" — `METHODOLOGY.md:5043`
- [mocap watcher gaps] "| G4 | **The breach action stops the simulation** (SIGTERM to `fly_trial`/`run_trial`). On hardware it must command LAND over MAVLink (`SET_MODE`/`MAV_CMD_DO_SET_MODE` LAND), one-shot and latched, and alert the safety pilot (audible). | B4, B5, B9 |" — `docs/real_flights_plan.md:445` — note: plan §7.2 gap list; conflicts with U10 G1–G6, readiness G-rows and test gates of the same labels
- [real-flight readiness checklist] "| G4 | `thesis_nav_check`: origin-independent "position lost → LAND" for types 12/13 | exists and tested in SITL | b | `ArduCopter/ekf_check.cpp:330-340` in the fork. SITL safety tests (a) PASS for both estimators. **Copter only; a QuadPlane would need its own (U2).** It is compiled out of board builds today (G1b). | ..." — `docs/real_flight_readiness.md:128` — note: section G (estimators and firmware) of the readiness checklist; distinct from watcher gap G4

### `G5` — **CONFLICT: 8 meanings** (see flags §b)

- [Experiment H S1 per-flight gates] "- **G5 (safety):** GT stays ≥ 0.5 m from every wall." — `METHODOLOGY.md:10676`
- [H backend ground-test gates (S2/S3 tag input)] "- **G5 (no gate):** after the anchor, every `XUKT` row fuses (`NF` increments by one per row); `XUKO.EvO` = 0." — `docs/h_backends_tag_input.md:438` — note: FGO G5 differs (line 460: D25 C1–C3 and FG2/FG3b)
- [U10 replay-gate criteria] "| **G5** | **Bounded unaligned drift:** the start-aligned horizontal drift (rung-1 §4.3 rule; `drift_start_aligned.final_h_m`, the error at the last estimator sample in W, i.e. at t_ld − 5 s) ≤ **D_max = 1.0 m** (SIGNED 2026-10-12; basis: half the 2 m clearance required at every hold point; the draft had proposed it ..." — `docs/u10_replay_gate_band.md:195` — note: signed D_max = 1.0 m; N1 makes "not computable" a FAIL
- [U10 replay-gate criteria] *(superseded)* "| **G5** | **Bounded unaligned drift:** the start-aligned horizontal drift (rung-1 §4.3 rule) at t_ld − 5 s ≤ **D_max = [TBD-S] m** (proposed 1.0 m: half the smallest watcher-box half-width expected in a mocap volume) | per flight | a closed loop steers on the unaligned estimate; this is the physical excursion it ..." — `docs/u10_replay_gate_band_draft.md:125` — note: draft (line 3: "**Status: DRAFT, written 2026-10-12 ... NOT in force.**"); D_max [TBD-S] replaced by signed 1.0 m in docs/u10_replay_gate_band.md
- [backend ground-test gates (D9 P3 / D17 V3 / D19 FGO)] "- **(G5) Disarm:** the vehicle disarms on request, with no EKF/UKF failsafe or crash message in the" — `METHODOLOGY.md:7393` — note: FGO re-run D24 re-worded G5 at line 8809
- [board firmware go/no-go] "| G5 | Rollback rehearsed once on the bench (§6 steps 1–7), and the stock `.apj` and parameter backup are on the laptop | done |" — `docs/board_firmware_plan.md:275` — note: §7 go/no-go before the first powered test on the fork
- [heading ground-test gates (VISO_DELAY_MS, closed-loop Part 1)] "**G5 (re-worded; pre-registered before run 2, `gt_heading_2`, D = 60).** All must hold:" — `METHODOLOGY.md:5832` — note: re-worded G5, split into G5.1-G5.3 (lines 5833, 5837, 5846); used in gt_heading_2/3, gt_heading_cpp2, gt_heading_half2
- [heading ground-test gates (VISO_DELAY_MS, closed-loop Part 1)] *(superseded)* "- **G5, the delay takes effect and the heading is time-aligned (run 2).**" — `METHODOLOGY.md:5050` — note: original G5; re-worded before run 2 at line 5832: "**G5 (re-worded; pre-registered before run 2, `gt_heading_2`, D = 60).**"
- [mocap watcher gaps] "| G5 | **No FC-side layer: the watcher sends no MAVLink HEARTBEAT, and no GCS-failsafe parameters are set.** The native mechanism needs no Lua: `FS_GCS_ENABLE` 5 (Land), `FS_GCS_TIMEOUT` 3 s (range 2–120; the default is 5), and `MAV_GCS_SYSID` set to the watcher's own system ID (`GCS.cpp:22`, ..." — `docs/real_flights_plan.md:446` — note: plan §7.2 gap list; conflicts with U10 G1–G6, readiness G-rows and test gates of the same labels
- [real-flight readiness checklist] "| G5 | `AP_NavFGO` thin backend: `ODOMETRY` validation (flag, arrival ≤ 250 ms, age ≤ 250 ms), FC-IMU output predictor, `XFGI`/`XFGO` logging | exists and tested in SITL | b | FG1–FG3b, D25, `cl_fgo_*`, `fgo_cpp_shadow_*` (`docs/fgo_cpp_port.md` Part 4; METHODOLOGY "FGO C++ stage 5 RESULT"). | 0 d new code; hardware ..." — `docs/real_flight_readiness.md:129` — note: section G (estimators and firmware) of the readiness checklist; distinct from watcher gap G5

### `G6` — **CONFLICT: 5 meanings** (see flags §b)

- [H backend ground-test gates (S2/S3 tag input)] "- **G6 (estimate):**" — `docs/h_backends_tag_input.md:439`
- [U10 replay-gate criteria] "| **G6** | **Replay fidelity:** ONLY if rung 1 flew the fork in shadow (the Replay output holds onboard `XUKF`). Replayed `RUKF`/`RUKS` against onboard `XUKF`/`XUKS` in the same Replay output: **E1 3-D position max ≤ 0.05 m, rms ≤ 0.01 m; E3 yaw max ≤ 0.05°; E5 accepted-count increments within 0.1 %** (definition ..." — `docs/u10_replay_gate_band.md:196` — note: E1 is 3-D per N6
- [U10 replay-gate criteria] *(superseded)* "| **G6** | **Replay fidelity:** ONLY if rung 1 flew the fork in shadow (an onboard `XUKF` exists; costing §13 option). Replay `XUKF`/CSV against onboard `XUKF`: E1 horizontal max ≤ 0.05 m, rms ≤ 0.01 m; E3 yaw ≤ 0.05°; E5 accepted-count increments within 0.1 % | per flight, **[TBD-V]** | see below |" — `docs/u10_replay_gate_band_draft.md:126` — note: draft, NOT in force; "E1 horizontal" corrected to 3-D by N6 in the signed band
- [board firmware go/no-go] "| G6 | `AHRS_EKF_TYPE 3` confirmed after every flash, and `AHRS_UKF_TFAIL 0` | readback |" — `docs/board_firmware_plan.md:276` — note: §7 go/no-go before the first powered test on the fork
- [mocap watcher gaps] "| G6 | **The FC will arm without a watcher.** `failsafe_gcs_check()` returns early if the GCS has never been seen (`events.cpp:133-136`). Without the flight script, nothing on the FC enforces "no watcher, no arming". Options: (i) procedure only (arm ONLY via the flight script; stick arming disabled with ..." — `docs/real_flights_plan.md:447` — note: plan §7.2 gap list; conflicts with U10 G1–G6, readiness G-rows and test gates of the same labels
- [real-flight readiness checklist] "| G6 | C++ FGO node on x86 (GTSAM 4.2.1, ROS 2 / MAVLink adapter, time_ref stamping, reorder delay 0.20 s) | exists and tested in SITL | b | `src/estimators/fgo_cpp/`. Equivalence bands A/B/C/L passed; flew S3/S3v2 and the FGO safety re-tests (node `f642cd37`). Accepted for the **aided regime only** (plan §9.3 ..." — `docs/real_flight_readiness.md:130` — note: section G (estimators and firmware) of the readiness checklist; distinct from watcher gap G6

### `G7` — **CONFLICT: 3 meanings** (see flags §b)

- [board firmware go/no-go] "| G7 | The rung's pre-registration and the SITL gates of the costing doc (V1–V7), for anything beyond shadow | signed off |" — `docs/board_firmware_plan.md:277` — note: §7 go/no-go before the first powered test on the fork
- [mocap watcher gaps] "| G7 | **Dependency liveness uses `pgrep`, which is local only.** The flow tracker, the bridges and the estimator node run on the Pi. A networked liveness signal is needed, such as topic rates seen over ROS 2 or a per-process MAVLink/ROS heartbeat. `pgrep` also misses a process that is alive but hung (SIGSTOP). | B9 |" — `docs/real_flights_plan.md:448` — note: plan §7.2 gap list; conflicts with U10 G1–G6, readiness G-rows and test gates of the same labels
- [real-flight readiness checklist] "| G7 | Corrected FGO (initial yaw σ 1° in both cores, ruling 2026-10-10): C++ equivalence on the corrected build, plus SITL safety (a)/(b) | not built | b (FGO) | Ruling 2026-10-10 items 1–3 and the reorder ruling (in progress). Plan §7: "before any real FGO flight". All flown FGO results used 1e-3 rad. | already ..." — `docs/real_flight_readiness.md:131` — note: section G (estimators and firmware) of the readiness checklist; distinct from watcher gap G7

### `G8` — **CONFLICT: 3 meanings** (see flags §b)

- [board firmware go/no-go] "| G8 | Main-thread stack margin (P7) and no new long loops (P8) | measured |" — `docs/board_firmware_plan.md:278` — note: §7 go/no-go before the first powered test on the fork
- [mocap watcher gaps] "| G8 | **`--dep-loss stop` has no hardware meaning.** In SITL it stops the simulation. On hardware both settings must end in LAND. Pre-registered: `stop` maps to LAND plus an alert (or the option is removed). | B9 |" — `docs/real_flights_plan.md:449` — note: plan §7.2 gap list; conflicts with U10 G1–G6, readiness G-rows and test gates of the same labels
- [real-flight readiness checklist] "| G8 | C++ FGO on the real Pi: GTSAM 4.2.1 + Boost on arm64 (native or cross build), ROS 2 Jazzy arm64, keyframe CPU budget (33 ms), memory, core pinning and RT priority, **live solve-time self-stop** (stage 3 requirement: p99 > keyframe period for 2 s → node stops → backend invalid → LAND) | exists but untested on ..." — `docs/real_flight_readiness.md:132` — note: section G (estimators and firmware) of the readiness checklist; distinct from watcher gap G8

### `G9` — **CONFLICT: 2 meanings** (see flags §b)

- [mocap watcher gaps] "| G9 | **The `watch_heartbeat` file is local.** That is valid only if the watcher and the flight script run on the same ground-station machine, which is pre-registered as a requirement. | B1, B2 |" — `docs/real_flights_plan.md:450` — note: plan §7.2 gap list; conflicts with U10 G1–G6, readiness G-rows and test gates of the same labels
- [real-flight readiness checklist] "| G9 | C++ FGO node transport to a serial FC (today UDP only, learning the peer from SITL SERIAL3) | needs adapting for real sensors | b (FGO) | `fgo_cpp_node.cpp:9-10,80` (`UdpEndpoint`). With a router (B1) the change may be configuration only. | 0.5–1 d | B1 |" — `docs/real_flight_readiness.md:133` — note: section G (estimators and firmware) of the readiness checklist; distinct from watcher gap G9

### `G10` — **CONFLICT: 2 meanings** (see flags §b)

- [mocap watcher gaps] "| G10 | **The `--box` rule is x/y only.** It has no height limit (capture-volume top or ceiling). Add z_max, and z_min only for "below the floor" sanity. | B4 |" — `docs/real_flights_plan.md:451` — note: plan §7.2 gap list; conflicts with U10 G1–G6, readiness G-rows and test gates of the same labels
- [real-flight readiness checklist] "| G10 | UKF live on the Pi (only if U9 = Pi placement): a live UKF node plus a UKF mode in the thin backend | not built | b (only if U9 = Pi) | Only `ukf_core.py` and the replay scripts exist; there is no live Python UKF node. | 3–5 d plus its own SITL gates (FG1–FG3-type) | U9 |" — `docs/real_flight_readiness.md:134` — note: section G (estimators and firmware) of the readiness checklist; distinct from watcher gap G10

### `G11` — **CONFLICT: 2 meanings** (see flags §b)

- [mocap watcher gaps] "| G11 | **Heartbeat masking.** `handle_heartbeat` refreshes the GCS-failsafe timer for ANY HEARTBEAT, RC_OVERRIDE or MANUAL_CONTROL from a system ID in the GCS range (`GCS_Common.cpp:4231,4350,7671`; `sysid_is_gcs`). MAVProxy and pymavlink default to system ID 255 = the default `MAV_GCS_SYSID`. The watcher must ..." — `docs/real_flights_plan.md:452` — note: plan §7.2 gap list; conflicts with U10 G1–G6, readiness G-rows and test gates of the same labels
- [mocap watcher gaps] "| **G11** heartbeat masking | The watcher refuses system ID 255 and the FC's own ID. It never sends RC_CHANNELS_OVERRIDE or MANUAL_CONTROL. It sends HEARTBEAT only while confirmed. Any received message carrying the watcher's own system ID latches a "system-ID collision" withdrawal. The readback requires ..." — `docs/handovers/2026-10-10_mocap_watcher_build.md:67` — note: restatement with implementation
- [real-flight readiness checklist] "| G11 | Offline replay of the UKF/FGO on real-flight logs (Python `ukf_replay.py` / `fgo_replay.py`, C++ replay, port Replay on `LOG_REPLAY` dataflash) | needs adapting for real sensors | a | It assumes bag topics, sim stamps, 333 Hz/3 ms IMU dejitter and `imu_gap_check` (memory rule: run `imu_gap_check --write` ..." — `docs/real_flight_readiness.md:135` — note: section G (estimators and firmware) of the readiness checklist; distinct from watcher gap G11

### `GT` — **UNDEFINED** (see flags §a)

- [abbreviations] *(used, not defined here)* "- **The flow sensor itself** (measured forward flow ÷ flow predicted from GT through the shared" — `METHODOLOGY.md:3552` — note: never expanded; ground truth is defined in CLAUDE.md "Ground Truth Bridging"

### `H1` — **CONFLICT: 3 meanings** (see flags §b)

- [OI-1 blank-floor hypotheses] "> - **H1 — the gate decides what reaches velocity.** Under starved blank-floor flow, the" — `METHODOLOGY.md:619`
- [real-flight readiness checklist] "| H1 | SITL safety tests (a) estimator failure in a hover and (b) node or bridge kill, on the corrected UKF and FGO builds | exists and tested in SITL | b | Procedure and scorer exist (`tools/run_h_safety.sh`, `eval/h_safety_score.py`). Earlier builds passed (METHODOLOGY "RESULT: FGO safety re-test (a)/(b) v3", "UKF ..." — `docs/real_flight_readiness.md:141` — note: section H (safety tests and staging)
- [rung-1 scorer SITL regression checks] "- **H1:** heading on `dsn_tex_r1..r3`, UKF and FGO TUMs, against `d15_drift.json` (sign-flipped ENU → NED). Equal" — `docs/handovers/2026-10-12_r1_scoring_items.md:53`

### `H2` — **CONFLICT: 3 meanings** (see flags §b)

- [OI-1 blank-floor hypotheses] "> - **H2 — near-zero measured flow is being read as motion.** Blank-floor flow has" — `METHODOLOGY.md:626`
- [real-flight readiness checklist] "| H2 | SITL rehearsal at Pi-like link latency (`tc netem` or a bridge delay): FG1, FG2, FG3/FG3b, D25, plus one closed-loop P-HOLD per estimator | not built | b | Plan §9.2. A gate failure blocks hardware closed loop for that estimator. | 1 d harness, plus 1 d flights per estimator | B3, H1 |" — `docs/real_flight_readiness.md:142` — note: section H (safety tests and staging)
- [rung-1 scorer SITL regression checks] "- **H2:** heading on the NED-yaw path, `d15_port/dsn_tex_r8` `ukf_shadow.csv` against SIM: 9.293967, equal to the" — `docs/handovers/2026-10-12_r1_scoring_items.md:55`

### `H3` — **CONFLICT: 3 meanings** (see flags §b)

- [real-flight readiness checklist] "| H3 | Rehearsal of P-HOLD and P-LAPS in the simulated mocap room (`fly_trial` profiles, moving setpoints, D24 clock, land on failure) | exists and tested in SITL | a, b | Experiment H S1/S2/S3 (`room_wall_tag`); experiment T (laps). | 0 d; re-run only after a script change | — |" — `docs/real_flight_readiness.md:143` — note: section H (safety tests and staging)
- [rung-1 scorer SITL regression checks] "- **H3 (information):** EKF3 `XKF1@0` against SIM on the pinned window: +7.96 / +7.59 / +8.10 deg/min, inside" — `docs/handovers/2026-10-12_r1_scoring_items.md:59`
- [stage-3 sorties] "| **H3: hand-carried in the volume** (disarmed; type 12 active, nothing steers) | verification | ~2 min: wiggle, one carried out-and-back leg at flight height, wiggle | the output is computed exactly as in flight; one leg checks the flow sign, the UKF against mocap, the watcher live on mocap, and the IR check | the ..." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:59` — note: a sortie label; cf. readiness H7 (hand-carried stage)

### `H4`

- [real-flight readiness checklist] "| H4 | Bench stage 0 (props off): all streams at rate, clock map settled, logging complete, rollback rehearsed; for (b) also forced backend invalidity → `thesis_nav_check` LAND on the real FC | not built | a; b adds the forced-invalidity item | Plan §9.4 stage 0; plan §7 ("must pass on the bench AND in SITL"). | 1–2 d ..." — `docs/real_flight_readiness.md:144` — note: section H (safety tests and staging)

### `H5`

- [real-flight readiness checklist] "| H5 | RC override: a dedicated switch to ALT_HOLD/STABILIZE (no estimator position), rehearsed before every session | not built | a, b | Plan §7, §9.4. ALT_HOLD needs the height source (here the rangefinder) to remain healthy. | 0.5 d | A1, U8 |" — `docs/real_flight_readiness.md:145` — note: section H (safety tests and staging)

### `H6`

- [real-flight readiness checklist] "| H6 | Geofence: the mocap box (primary, F2) plus the ArduPilot fence as a secondary layer only | needs adapting for real sensors | a, b | Plan §7: the FC fence uses the AHRS position, i.e. the estimator under test. Box sizes from the SITL rule "≥ 2 m clearance from every hold point" (ruling 2026-10-09, attitude-only ..." — `docs/real_flight_readiness.md:146` — note: section H (safety tests and staging)

### `H7`

- [real-flight readiness checklist] "| H7 | Hand-carried stage (motors off): estimators against mocap; flow sign; heading and tag checks | not built | a, b | Plan §9.4 stage 0. | 0.5–1 d | H4, F1 |" — `docs/real_flight_readiness.md:147` — note: section H (safety tests and staging)

### `H8`

- [real-flight readiness checklist] "| H8 | Tethered hover with EKF3 flying | not built | a, b | Plan §7 staged bring-up step 3. | 0.5–1 d | H7, H5, F4 |" — `docs/real_flight_readiness.md:148` — note: section H (safety tests and staging)

### `H9`

- [real-flight readiness checklist] "| H9 | Per-stage pre-registration with real-flight criteria fitted to the capture volume (plan question 8); real-flight scoring scripts | not built | a, b | The SITL criteria (U1–U3, B1–B5) assume a 160 m corridor (plan question 8). | 1–2 d per stage | U7 |" — `docs/real_flight_readiness.md:149` — note: section H (safety tests and staging)

### `H10`

- [real-flight readiness checklist] "| H10 | Real-vehicle flight script: `fly_trial.py` without SITL assumptions, keeping `ensure_params`, D24 `SYSTEM_TIME` clock, `WATCH_HEARTBEAT` (to be replaced by F3), `require_fgo_node_current`, `wait_fix` before arming, land on failure | needs adapting for real sensors | a, b | `fly_trial.py` (`:303-315`, ..." — `docs/real_flight_readiness.md:150` — note: section H (safety tests and staging)
- [real-flight readiness checklist] "8. **H10:** the bench driver's pilot-takeover guard is added to `fly_trial.py` before any scripted real flight, and" — `METHODOLOGY.md:13905` — note: ruling item 8: the "H10 guard" (pilot-takeover guard in fly_trial.py)

### `H-H1`

- [Experiment H hypotheses] "- **H-H1 (primary, EKF3 flying):** mean hold error ≤ 0.05 m and max ≤ 0.15 m in every pre-loss hold window, 3/3" — `METHODOLOGY.md:10687` — note: pre-registered S1 wording (EKF3 flying); differs from the design draft (tag_hold_design.md:176, every estimator)
- [Experiment H hypotheses] "- **H-H1 (primary): every estimator holds within tag-fix accuracy.** Mean hold error ≤ 0.05 m and max ≤ 0.15 m in" — `docs/tag_hold_design.md:176` — note: design draft wording; differs from the S1 pre-registration (METHODOLOGY 10687)

### `H-H2`

- [Experiment H hypotheses] "- **H-H2: the FGO's hold error is lowest.** FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights." — `docs/tag_hold_design.md:180`
- [Experiment H hypotheses] "- **H-H2 FAILS** ("FGO lowest hold error, 3/3"). The UKF is lowest in 3/3; the FGO and EKF3 tie (7.8–7.9 mm)." — `METHODOLOGY.md:12236` — note: verdict restating the criterion ("FGO lowest hold error, 3/3")

### `H-H4`

- [Experiment H hypotheses] "- **H-H4 (tag loss):**" — `docs/tag_hold_design.md:184` — note: sub-bullets at lines 185-187 (15 s and 5 s parts)

### `H-L1`

- [Experiment L hypotheses] "- **H-L1 (PRIMARY): loop closure bounds live drift.** For LC live, the lap-5 RMSE is ≤ 1.5 × the lap-1 RMSE in 3/3" — `METHODOLOGY.md:10501`

### `H-L2`

- [Experiment L hypotheses] "- **H-L2:** LC live overall RMSE < no-LC live overall RMSE in 3/3 flights." — `METHODOLOGY.md:10503`

### `H-L3`

- [Experiment L hypotheses] "- **H-L3:** LC hindsight overall RMSE < no-LC hindsight overall RMSE in 3/3 flights." — `METHODOLOGY.md:10504`

### `H-O1`

- [Experiment O hypotheses] "- **H-O1 (PRIMARY, the ruling's hypothesis):** FGO hindsight beats the filters' live tracks indoors. PASS iff in 3/3" — `METHODOLOGY.md:10358`

### `H-O2`

- [Experiment O hypotheses] "- **H-O2 (the ruling's hypothesis, second half):** live indoor errors are similar. In every flight, the largest live" — `METHODOLOGY.md:10360`

### `H-T1`

- [Experiment T hypotheses] "- **H-T1 (PRIMARY, the ruling's hypothesis): the FGO's hindsight gain grows with the gap.** PASS iff both:" — `METHODOLOGY.md:10171`

### `I1`

- [real-flight readiness checklist rows] "| I1 | FC logging: `LOG_REPLAY=1`, `LOG_DISARMED=1` (CLAUDE.md "All future flights"), IMU at full rate (`INS_LOG_BAT_*` or a fast IMU bitmask, needed by `mocap_align`), `XUK*`/`XFG*`/`XKF*` | needs adapting for real sensors | a, b | Today these are set only in `consolidated_rerun.parm`, alongside `AHRS_EKF_TYPE 10`, ..." — `docs/real_flight_readiness.md:156`
- [real-flight readiness checklist rows] "| I1 | FC logging (`LOG_REPLAY`, `LOG_DISARMED`, buffer, `DSF`) | 1, U | SW+HW | in R6 | | template DONE; WAITS |" — `docs/real_flight_readiness_by_rung.md:203` — note: same meaning restated by rung

### `I2`

- [real-flight readiness checklist rows] "| I2 | Pi recorder: a ROS 2 bag of every input, estimator outputs, `/imu/time_ref`, heading-bridge CSV, node clock-map stats; metadata (repo commits, firmware hash, parameters, hardware IDs) | needs adapting for real sensors | a, b | `record_trial.sh` / `run_trial.sh` assume `/clock`, `/ground_truth/pose` and Gazebo ..." — `docs/real_flight_readiness.md:157`

### `I3`

- [real-flight readiness checklist rows] "| I3 | Mocap ground truth into the trial: poses with mocap-host stamps plus receipt stamps; `eval/mocap_align.py` (4-DoF frame fit) | exists but untested on hardware | a, b | `mocap_align.py` self-test: offset −3.7 ms, rate 4.9 ppm, yaw 0.30° on synthetic mocap (plan §8 item 4). | 0.5 d | F1, I1 |" — `docs/real_flight_readiness.md:158`

### `I4`

- [real-flight readiness checklist rows] "| I4 | Time sync mocap ↔ FC (|ω| correlation against the FC gyro, with the 11.3 ms INS group delay at 20 Hz) and Pi ↔ mocap host (chrony or PTP on the lab LAN) | exists but untested on hardware | a, b | The `mocap_align.py` method is self-tested only. chrony/PTP is not configured anywhere [U7]. If the notch or filter ..." — `docs/real_flight_readiness.md:159`

### `L1` — **CONFLICT: 2 meanings** (see flags §b)

- [FGO C++ port band L rows] "| L1 | dsn_tex_r1 | tape with the offline dejittered IMU stamps substituted (`--imu-stamp header`); arming time = the export's (`--arm-source param`); delay 0.20 s; everything else live: receipt order, reorder buffer, interval-averaged gyro, init, keyframing, gap rule, validity, clock map, ODOMETRY encoding |" — `docs/fgo_cpp_port.md:422`
- [G5.3 latency-stability sub-criteria] "- **(L1)** The linear-fit slope of per-frame latency (sent − capture) against capture time," — `METHODOLOGY.md:5849`

### `L2` — **CONFLICT: 2 meanings** (see flags §b)

- [FGO C++ port band L rows] "| L2 | fwdc_tex_r1 | as L1, plus the heading input: the export's frozen forward headings written as the heading bridge's sent message (NED yaw = −psi, quality 100, angErr 0) at their capture stamp, with heading sigma = the offline heading arm's (0.148°) and gate 9 |" — `docs/fgo_cpp_port.md:423`
- [G5.3 latency-stability sub-criteria] "- **(L2)** Every 30 s block median latency is ≤ 200 ms. Basis: the largest run-1 block median" — `METHODOLOGY.md:5852`

### `L3`

- [G5.3 latency-stability sub-criteria] "- **(L3)** Dropped selected frames are ≤ 5% (run 1: 0.75%)." — `METHODOLOGY.md:5854`

### `L4` — **UNDEFINED** (see flags §a)

- [Experiment L hypotheses] *(used, not defined here)* "- **P-L4 (prediction):** no-LC live per-lap RMSE grows: lap 5 > 1.5 × lap 1 in 3/3 flights." — `METHODOLOGY.md:10505` — note: "L4" occurs only inside P-L4; no standalone L4 code

### `M0`

- [F6 LAND re-send rule] "**The new rule** (in the module docstring). M0 is the FC custom mode in the last HEARTBEAT before the first send." — `docs/handovers/2026-10-12_watcher_f6_failsafe_b5_b8a.md:14`

### `M1`

- [F8 mitigations] "- **M1 (strongest, cheap): reboot the FC (or power-cycle) after every landing before re-arming.** Every runaway seen followed a landing in the same boot; 0 of 10 first arms showed it." — `docs/handovers/2026-10-12_f8_investigation.md:206`
- [F8 mitigations] "- **M1:** power-cycle the FC before any re-arm after a landing, then the origin set and re-verified" — `docs/real_flights_plan.md:403` — note: approved form (ruling 2026-10-12)

### `M2`

- [F8 mitigations] "- **M2: a pre-arm EKF velocity check, on the card AND as a watcher arming check alongside F7.**" — `docs/handovers/2026-10-12_f8_investigation.md:208`
- [F8 mitigations] "- **M2 (watcher arming check):** while the FC is disarmed, the watcher withholds its confirmation unless the FC's" — `docs/real_flights_plan.md:405` — note: approved form

### `M3`

- [F8 mitigations] "- **M3: land in ALT_HOLD (pilot throttle-down, then disarm) rather than LAND where safe.** LAND is still the abort default. After any LAND touchdown, the SP disarms within 2 s of touchdown (this tightens the F2 rule from 4 s)." — `docs/handovers/2026-10-12_f8_investigation.md:213`
- [F8 mitigations] "- **M3:** land in ALT_HOLD where safe; after any LAND-mode touchdown the safety pilot disarms within 2 s." — `docs/real_flights_plan.md:411` — note: approved form

### `M4`

- [F8 mitigations] "- **M4: state explicitly that U4 (take off within 5 s of arming) does NOT address F8.** The bad velocity exists BEFORE arming, so a quick take-off can make things worse by lifting off before the gate re-opens." — `docs/handovers/2026-10-12_f8_investigation.md:214`

### `O1` — **UNDEFINED** (see flags §a)

- [Experiment O hypotheses] *(used, not defined here)* "- **H-O1 (PRIMARY, the ruling's hypothesis):** FGO hindsight beats the filters' live tracks indoors. PASS iff in 3/3" — `METHODOLOGY.md:10358` — note: no standalone O1 found in the in-scope docs or PDFs; occurs only inside H-O1/H-O2/P-O3

### `O2` — **UNDEFINED** (see flags §a)

- [Experiment O hypotheses] *(used, not defined here)* "- **H-O2 (the ruling's hypothesis, second half):** live indoor errors are similar. In every flight, the largest live" — `METHODOLOGY.md:10360` — note: no standalone O2 found in the in-scope docs or PDFs; occurs only inside H-O1/H-O2/P-O3

### `O3` — **UNDEFINED** (see flags §a)

- [Experiment O hypotheses] *(used, not defined here)* "- **P-O3 (prediction; the fair comparison):** FGO batch and RTS-UKF indoor RMSE are within 1.5× of each other in every" — `METHODOLOGY.md:10362` — note: no standalone O3 found in the in-scope docs or PDFs; occurs only inside H-O1/H-O2/P-O3

### `OI-1`

- [open items (OI)] "> ### OPEN ITEM OI-1 — FGO blank-floor failure mode changed with the `h_flow` correction" — `METHODOLOGY.md:606`
- [open items (OI)] *(superseded)* "### OI-1 (FGO blank-floor freeze) — reviewed against the new behaviour: CLOSED as superseded" — `METHODOLOGY.md:5595`

### `OI-2`

- [open items (OI)] "## OPEN ITEM OI-2 — IMU timestamp asymmetry between estimators (fairness)" — `METHODOLOGY.md:1193`
- [open items (OI)] "### 3.2 IMU timestamp asymmetry (OI-2) and the dejitter ruling" — `docs/thesis/methodology_index.md:379` — note: "OI-2 dejitter" = the adopted remedy
- [open items (OI)] "- **OI-2 residual:** the sensor-time IMU shift is not adopted. `/imu/time_ref`" — `METHODOLOGY.md:1177`

### `P1` — **CONFLICT: 6 meanings** (see flags §b)

- [D9 UKF flight preconditions] "- **(P1)** the queue check on Replay logs (no loss; EKF3's flow timing; time-ordered);" — `METHODOLOGY.md:6846`
- [F7 bench session preconditions] "- **P1:** the watcher logs "tie … captured at the EKF-origin broadcast" (not "TIE CAPTURE FAILED") after the verified" — `docs/handovers/2026-10-12_f7_cards.md:98`
- [F8 proposed parameter items] "- **P1: RNGFND1_GNDCLR and FLOW_POS_Z must be the measured real values.**" — `docs/handovers/2026-10-12_f8_investigation.md:217`
- [board bench checks] "| P1 | Banner and version: git hash = `board-h743` commit; the board name | exact match |" — `docs/board_firmware_plan.md:227` — note: §5 after-flashing bench checks (props off)
- [forward-camera Phase 1/2 criteria] "| P1 | flow and lidar header timing (cruise) | rate 30.30 Hz ± 0.1%; ≤ 0.5% of gaps above 1.5 periods. `dsn` is exact (0.00%); 0.5% is one dropped frame per ~6.6 s, a negligible loss of information. | Dropped or late downward frames would mean the added load starves the downward pipeline. |" — `METHODOLOGY.md:1711` — note: P1 has two rows (flow/lidar, and IMU on the next line); carried unchanged to Phase 2, 2b, 1c and ceiling datasets
- [plan step 2(a) decision rules] "- **P1 (PRIMARY):** the robust FGO's **yaw maximum** < the hard-gated FGO's on **≥ 10 of 12** flights." — `METHODOLOGY.md:9730`

### `P2` — **CONFLICT: 5 meanings** (see flags §b)

- [D9 UKF flight preconditions] "- **(P2)** a shadow run of **the exact binary to be flown** (`AHRS_EKF_TYPE 10`, `AHRS_UKF_ENABLE 1`):" — `METHODOLOGY.md:6847`
- [F7 bench session preconditions] "- **P2:** `EK3_SRC1_YAW` 0, `SCR_ENABLE` 1, `AHRS_EKF_TYPE` 3 read back." — `docs/handovers/2026-10-12_f7_cards.md:100`
- [F8 proposed parameter items] "- **P2: EK3_FLOW_I_GATE.** A larger gate re-opens sooner, but it is a global change to the estimator under test. Not recommended for the comparison." — `docs/handovers/2026-10-12_f8_investigation.md:220`
- [board bench checks] "| P2 | Parameters read back: every value of the rung's parameter file (`check_parm.py` then a full readback; the eeprom gotcha, Known Issue #10, applies on hardware) | 0 mismatches |" — `docs/board_firmware_plan.md:228` — note: §5 after-flashing bench checks (props off)
- [forward-camera Phase 1/2 criteria] "| P2 | flow → EKF3 latency (median and p95) | ≤ same-world `dsn` mean + **12.5 ms** (one EKF3 prediction step, its own time resolution; `AP_NavEKF3_Measurements.cpp:232-234`). Matched frames ≥ same-world `dsn` minimum − 5 pp (`dsn` blank spreads 7 pp). | EKF3 would fuse flow at a different effective time than in ..." — `METHODOLOGY.md:1713`
- [forward-camera Phase 1/2 criteria] "### RULING (user, 2026-09-24): P2 is DIAGNOSTIC for Phase 2 (recorded before any `fwd_*` data exists)" — `METHODOLOGY.md:1812` — note: P2 demoted from PRIMARY to DIAGNOSTIC from Phase 2 on

### `P3` — **CONFLICT: 3 meanings** (see flags §b)

- [D9 UKF flight preconditions] "- **(P3)** a ground test of the backend with `AHRS_EKF_TYPE 12` (arms, holds, disarms; the UKF" — `METHODOLOGY.md:6850`
- [board bench checks] "| P3 | **Backends compiled in:** the parameters `AHRS_UKF_ENABLE`, `AHRS_UKF_TFAIL`, `AHRS_FGO_ENABLE` exist (stock firmware has no such parameters) | present |" — `docs/board_firmware_plan.md:229` — note: §5 after-flashing bench checks (props off)
- [forward-camera Phase 1/2 criteria] "| P3 | downward flow conditions (unchanged from the original (b)) | inlier mean ±0.01 of the `dsn` mean (8× the textured n=3 range, ~1.5% of the textured–blank gap); % below 0.5 within ±3 pp; features ±5%; `flow_y_raw` ±2% (textured, transition; ≈ 1 cm of height or 1 cm/s of speed) or ±5 px/s (blank); transition ..." — `METHODOLOGY.md:1714`

### `P4` — **CONFLICT: 2 meanings** (see flags §b)

- [board bench checks] "| P4 | `AHRS_EKF_TYPE 3`, `AHRS_UKF_ENABLE 0`, `AHRS_FGO_ENABLE 0`: the vehicle is stock EKF3 ("backends disabled reproduces EKF3", costing doc §2) | EKF3 active; the same pre-arm and arming behaviour as stock |" — `docs/board_firmware_plan.md:230` — note: §5 after-flashing bench checks (props off)
- [forward-camera Phase 1/2 criteria] "| P4 | outcome, **textured** | evo -a (cruise) within the n=3 range widened by one range-width each side: **FGO [4.18, 5.35]**, **EKF3 [1.26, 8.13]**. | The forward-camera setup changed estimator behaviour through the shared inputs. |" — `METHODOLOGY.md:1715` — note: second P4 row (transition/blank) on the next line; bands rebased for Phase 2 at line 1869
- [phase abbreviations] *(used, not defined here)* "| "FGO −1060 → 1337" (P4 fwdplainc blank heading-arm effect) | **REAL but not interpretable** | the difference of two diverged blank-floor evo values (baseline 7.0–7.9 km, heading 8.2–9.7 km). Under the † rule this is evidence of divergence, not a value, so its sign means nothing |" — `docs/thesis/final_restatement_draft.md:74` — note: here "P4" labels Phase 4 heading-arm results, never expanded; conflicts with criterion P4 used in the same file (line 139)

### `P5`

- [board bench checks] "| P5 | `AHRS_UKF_TFAIL 1`, then try to arm: normally, and with a GCS force-arm | **both refused**: "AHRS_UKF_TFAIL is set (test hook)". Then set it back to 0 |" — `docs/board_firmware_plan.md:231` — note: §5 after-flashing bench checks (props off)

### `P5b` — **UNDEFINED** (see flags §a)

- [phase abbreviations] *(used, not defined here)* "| "FGO_baseline 57.11 → 1.67" (P5b fwdc tex NEES) | **REAL** | same file on both sides (`phase5b_consistency.json`). Per bag 56.1/58.9/56.4 → 2.3/0.2/2.5. The FGO's predicted yaw σ falls 0.476° → 0.057° (`checker_S`), so its covariance is no longer ~57× over-confident. This is the expected effect of removing the extra ..." — `docs/thesis/final_restatement_draft.md:72` — note: abbreviation never expanded; the cited file is phase5b_consistency.json and a "Phase 5b — consistency (NEES)" heading exists at METHODOLOGY 3697
- [phase abbreviations] *(used, not defined here)* "### P5b fwdc tex: cross-track mean 1-D NEES (consistent ≈ 1; flagged across 3)" — `docs/thesis/rerun_old_vs_new.md:1013`

### `P6`

- [board bench checks] "| P6 | Shadow on: `AHRS_UKF_ENABLE 1`, `AHRS_EKF_TYPE` still 3; hand-carry | `XUKF`/`XUKO`/`XUKS` logged; the UKF initialises (the rangefinder must read above its minimum: see §8) |" — `docs/board_firmware_plan.md:232` — note: §5 after-flashing bench checks (props off)

### `P7`

- [board bench checks] "| P7 | **Main-thread stack margin:** MAVFTP `@SYS/threads.txt` after 10 min with the shadow on | the main thread's free stack is reported; ≥ 1 kB free [E threshold] |" — `docs/board_firmware_plan.md:233` — note: §5 after-flashing bench checks (props off)

### `P8`

- [board bench checks] "| P8 | CPU: `PM` log messages (load, long loops) with the shadow on, against P4 | no new long loops; load increase within the [E] budget of §2.4 |" — `docs/board_firmware_plan.md:234` — note: §5 after-flashing bench checks (props off)

### `P9`

- [board bench checks] "| P9 | `@SYS/timers.txt` and `@SYS/uarts.txt`: no new errors | as before the flash |" — `docs/board_firmware_plan.md:235` — note: §5 after-flashing bench checks (props off)

### `P10`

- [board bench checks] "| P10 | Free memory: MAVLink `MEMINFO.freemem` with every flying feature enabled (scripting heap included) | no allocation failure at boot; record the figure |" — `docs/board_firmware_plan.md:236` — note: §5 after-flashing bench checks (props off)

### `P-H3`

- [Experiment H hypotheses] "- **P-H3 (smoothness, prediction):** gyro activity in the hold windows within 1.5× across estimators." — `docs/tag_hold_design.md:183`

### `P-H5`

- [Experiment H hypotheses] "- **P-H5 (drift during loss, per estimator):**" — `METHODOLOGY.md:10689` — note: S1 pre-registration: per-loss bands 0.05/0.10/0.20 m (UKF 2x); differs from the design draft
- [Experiment H hypotheses] "- **P-H5 (drift during loss, prediction):** GT drift during the 15 s occlusion ≤ 0.3 m for every estimator." — `docs/tag_hold_design.md:188` — note: design draft: 15 s loss ≤ 0.3 m for every estimator; this wording is the one applied in the comparative verdict at METHODOLOGY 12243

### `P-H6`

- [Experiment H hypotheses] "- **P-H6 (re-lock):**" — `METHODOLOGY.md:10695` — note: re-lock time re-defined (first returning detection, primary) for S2/S3 at METHODOLOGY 10948

### `P-H7`

- [Experiment H hypotheses] "- **P-H7 (lockout):** no estimator locks out the returning tag in any loss. For EKF3 this follows when the drift" — `METHODOLOGY.md:10700`

### `P-L4`

- [Experiment L hypotheses] "- **P-L4 (prediction):** no-LC live per-lap RMSE grows: lap 5 > 1.5 × lap 1 in 3/3 flights." — `METHODOLOGY.md:10505`

### `P-O3`

- [Experiment O hypotheses] "- **P-O3 (prediction; the fair comparison):** FGO batch and RTS-UKF indoor RMSE are within 1.5× of each other in every" — `METHODOLOGY.md:10362`

### `P-T2`

- [Experiment T hypotheses] "- **P-T2 (prediction): the same holds for the RTS-UKF** (Δ_UKF, same two criteria). The prediction is that hindsight" — `METHODOLOGY.md:10176`

### `P-T3`

- [Experiment T hypotheses] "- **P-T3 (prediction): live errors are similar.** In every condition, the largest live horizontal RMSE among EKF3, UKF" — `METHODOLOGY.md:10178`

### `P-T4`

- [Experiment T hypotheses] "- **P-T4 (prediction): FGO hindsight ≈ RTS-UKF.** In every condition, the larger of their horizontal RMSEs (mean over" — `METHODOLOGY.md:10180`

### `Q1`

- [minimal-path readiness questions] "- Q1–Q3 (FC board, Pi/cameras/rangefinder, mocap system) come from the supervisor." — `METHODOLOGY.md:12972` — note: gloss only; the Q-numbered question list was not found (readiness §5 numbering differs)

### `Q2` — **CONFLICT: 2 meanings** (see flags §b)

- [final re-run open questions] "2. **Closed-loop prediction (`cl_pred`).** Should the offline FGO contact-prediction input be recomputed with the" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:304` — note: §6 item 2; cited as "(Q2)" at line 140 (restating prediction bands); mapping by number and topic, the list itself is not Q-labelled
- [minimal-path readiness questions] "- Q1–Q3 (FC board, Pi/cameras/rangefinder, mocap system) come from the supervisor." — `METHODOLOGY.md:12972` — note: range Q1–Q3 expanded

### `Q3` — **CONFLICT: 2 meanings** (see flags §b)

- [final re-run open questions] "3. **F1 calibration.** Is k = 2.385 kept as registered (the default here), or is the 14-job calibration re-run, which" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:307` — note: §6 item 3; cited as "(Q3)" at line 133
- [minimal-path readiness questions] "- Q1–Q3 (FC board, Pi/cameras/rangefinder, mocap system) come from the supervisor." — `METHODOLOGY.md:12972` — note: range Q1–Q3 expanded

### `Q4` — **CONFLICT: 2 meanings** (see flags §b)

- [final re-run open questions] "4. **D27 item 3 / F3 re-measurement.** The FGO side is scripted (opt-in). Are the D26 flights used (default, isolating" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:309` — note: §6 item 4; cited as "(Q4)" at line 139
- [minimal-path readiness questions] "- Q4 (where the UKF runs in closed loop) is moot;" — `METHODOLOGY.md:12968`

### `Q5`

- [final re-run open questions] "5. **Reconstructed T/O/H/L commands.** No committed job lists existed. Please confirm:" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:312` — note: §6 item 5; cited as "(Q5)" at line 135 (far profile)
- [minimal-path readiness questions] *(used, not defined here)* "- Q5 as above;" — `METHODOLOGY.md:12969` — note: "as above" with no stated question

### `Q6` — **CONFLICT: 2 meanings** (see flags §b)

- [final re-run open questions] "6. **V-L scoring.** The original `three_way_eval --est` labels were not recorded. Should the V-L check be re-scored" — `docs/handovers/2026-10-09_final_rerun_pipeline.md:316` — note: §6 item 6; cited as "(Q6)" at line 138
- [minimal-path readiness questions] "- Q6: yes, an offline-only FGO is acceptable;" — `METHODOLOGY.md:12970` — note: answer only; also cited as "ruling Q6" at real_flight_readiness_by_rung.md:29

### `Q7`

- [minimal-path readiness questions] "- Q7: one person plus agents;" — `METHODOLOGY.md:12971` — note: answer only; question text not found

### `QP0`

- [QuadPlane SITL re-tests] "| QP0 | Build the fork `arduplane` (SITL); parameter readback | `AHRS_UKF_*` present; `AHRS_EKF_TYPE 12` accepted | — |" — `docs/quadplane_costing.md:352`

### `QP1`

- [QuadPlane SITL re-tests] "| QP1 | UKF shadow, EKF3 flying, QLOITER hover and pilot-style box (RC override script) | UKF healthy; `XUKF` tracks SITL truth; no DCM handover | — |" — `docs/quadplane_costing.md:353`

### `QP2`

- [QuadPlane SITL re-tests] "| QP2 | UKF flying (type 12), QLOITER hover 60 s plus box | `HORIZ_POS_REL` throughout; active = configured throughout | — |" — `docs/quadplane_costing.md:354`

### `QP3`

- [QuadPlane SITL re-tests] "| QP3 | Safety (a): `AHRS_UKF_TFAIL` forced invalidity in hover | Plane `thesis_nav_check` fires; **position-free landing** lands within the pre-registered drift | B1 |" — `docs/quadplane_costing.md:355`

### `QP4`

- [QuadPlane SITL re-tests] "| QP4 | Flow loss (`SIM_FLOW_ENABLE 0` mid-hover) | Same as QP3, via the aiding timeout | B1 |" — `docs/quadplane_costing.md:356`

### `QP5`

- [QuadPlane SITL re-tests] "| QP5 | Rangefinder loss | Vertical-hold expiry → DCM handover detected and landed | B1, §1.3 |" — `docs/quadplane_costing.md:357`

### `QP6`

- [QuadPlane SITL re-tests] "| QP6 | GCS heartbeat loss (watcher killed) | `FS_GCS_ENABL 1` → QLAND (or the B1 path) within `FS_LONG_TIMEOUT` | §7 |" — `docs/quadplane_costing.md:358`

### `QP7`

- [QuadPlane SITL re-tests] "| QP7 | Every failsafe ends in a Q mode | No fixed-wing mode ever selected (RC short/long, GCS, battery, fence) | §3 |" — `docs/quadplane_costing.md:359`

### `QP8`

- [QuadPlane SITL re-tests] "| QP8 | Arming | Arms only in Q modes; the Q_ASSIST, compass and home behaviour as predicted (§8) | — |" — `docs/quadplane_costing.md:360`

### `QP9`

- [QuadPlane SITL re-tests] "| QP9 | FGO path (only if the FGO is to fly a QuadPlane) | The thin backend's FG1–FG3b on Plane | B2 if guided |" — `docs/quadplane_costing.md:361`

### `R2` — **CONFLICT: 6 meanings** (see flags §b)

- [D17 V1/V2 heading-Replay checks] "- **R2 (queue):** each accepted heading is processed exactly once, in time order, ≥ 60 ms after its" — `METHODOLOGY.md:7599` — note: PASS criteria of D17 V1 (Replay check on set (b) logs); reused live for V2 (line 7611)
- [Experiment H supervisor ruling items (2026-10-08)] "**R2. EKF3, source check:** **one source set suffices; no switching is needed.**" — `docs/tag_hold_design.md:12` — note: §R "Supervisor ruling 2026-10-08 (incorporated)"
- [plan-to-freeze risks] "- **R2.** The D15 node core's take-off step time has not been measured live. If half speed does not" — `docs/plan_to_freeze.md:38` — note: section "Risks, flagged now"
- [rgs_check_tex roll-gain check criteria] "| R2 | \|FIX\| toward the true-rotation floor | airborne mean \|FIX\| **≤ 150** | The floor is 67 (true-rotation reconstruction). The excess over it (240–254) is the uncancelled roll tone, which scales with its amplitude, so R1's ≥ 10× reduction leaves ≤ ~25: **predicted ≤ ~95**. The ×1.6 margin to 150 covers non-tone ..." — `METHODOLOGY.md:4609` — note: pre-registered PRIMARY criteria of check flight rgs_check_tex (METHODOLOGY "Check flight `rgs_check_tex`: pre-registration")
- [rung-1 work items (minimal real-flight plan)] "| R2 | **UKF port for real geometry** in Replay: DAL offsets, `EK3_FLOW_DELAY`, range limits; byte-identical on SITL; rebuild the fork's Replay (sitl board, light) | 0.5–1 d | — | **yes** | Low |" — `docs/minimal_real_flight_plan.md:359` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67
- [watcher bench re-run set-up changes] "- **R2 — consequence: the stock EKF failsafe is now LIVE in every session** (`ekf_check.cpp:35-39` no longer returns at" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:25` — note: §1.1 "Set-up changes (harness only; the watcher is not changed)"

### `R3` — **CONFLICT: 6 meanings** (see flags §b)

- [D17 V1/V2 heading-Replay checks] "- **R3 (alignment):** alignment happens at the first processed heading, and there are no pseudo-yaw" — `METHODOLOGY.md:7601` — note: PASS criteria of D17 V1 (Replay check on set (b) logs); reused live for V2 (line 7611)
- [Experiment H supervisor ruling items (2026-10-08)] "**R3. UKF and FGO: identical inputs** — the same tag fixes when visible (the `/tags/sent` stream EKF3 received), flow," — `docs/tag_hold_design.md:29` — note: §R "Supervisor ruling 2026-10-08 (incorporated)"
- [plan-to-freeze risks] "- **R3.** 20+ half-speed flights at ~13 min wall each is ~5 h of flight time before the 16 Oct freeze." — `docs/plan_to_freeze.md:41` — note: section "Risks, flagged now"
- [rgs_check_tex roll-gain check criteria] "| R3 | pitch unchanged | cruise gyro-y rms within **[0.0027, 0.0108]** (0.5×–2× the old 0.0054) | Pitch gains are unchanged, so the expectation is equality. ±6 dB covers any change in roll→pitch coupling once the limit cycle is gone. | PRIMARY |" — `METHODOLOGY.md:4610` — note: pre-registered PRIMARY criteria of check flight rgs_check_tex (METHODOLOGY "Check flight `rgs_check_tex`: pre-registration")
- [rung-1 work items (minimal real-flight plan)] "| R3 | UKF CSV → TUM on the FC clock | 0.25 d | R2 | yes | Low |" — `docs/minimal_real_flight_plan.md:360` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67
- [watcher bench re-run set-up changes] "- **R3 — sessions.** `ground` (B1a, B1c(i–iv), B0, B1b/B9d, B5c, B6a, B1-native, B7b, **F6c**, B10c, B4a/B4c (A8)," — `docs/handovers/2026-10-12_watcher_bench_rerun.md:29` — note: §1.1 "Set-up changes (harness only; the watcher is not changed)"

### `R4` — **CONFLICT: 6 meanings** (see flags §b)

- [D17 V1/V2 heading-Replay checks] "- **R4 (acceptance):** ≥ 95% of processed headings in the cruise window pass the gate. Basis: R is" — `METHODOLOGY.md:7603` — note: PASS criteria of D17 V1 (Replay check on set (b) logs); reused live for V2 (line 7611)
- [Experiment H supervisor ruling items (2026-10-08)] "**R4. Loss metrics:**" — `docs/tag_hold_design.md:32` — note: §R "Supervisor ruling 2026-10-08 (incorporated)"
- [plan-to-freeze risks] "- **R4.** If an FGO gate fails, 9 Oct has only ~1.5 days of buffer. Any failure is flagged the same day." — `docs/plan_to_freeze.md:43` — note: section "Risks, flagged now"
- [rgs_check_tex roll-gain check criteria] "| R4 | take-off, hover and cruise profile | take-off 1.484–1.502 s ± max(range, 0.1 s) → **[1.384, 1.602] s**; climb peak ± max(range, 0.046 m) → **[2.187, 2.288] m**; cruise height ± 0.046 m → **[2.244, 2.345] m**; cruise speed **[0.4899, 0.5099] m/s**; GT \|x\| ≤ 0.05 m; the P1 timing bands and P3 downward-flow ..." — `METHODOLOGY.md:4611` — note: pre-registered PRIMARY criteria of check flight rgs_check_tex (METHODOLOGY "Check flight `rgs_check_tex`: pre-registration")
- [rung-1 work items (minimal real-flight plan)] "| R4 | **EKF3 Replay**: 0 d if pinned flies, 0.5 d stock Replay if 4.7.0 flies; `check_replay.py` acceptance with a pre-registered tolerance | 0.5–1 d | S6, first real log | partly | **Medium.** Not bit-exact on ARM; a non-H7 board makes it single against double. |" — `docs/minimal_real_flight_plan.md:361` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67
- [watcher bench re-run set-up changes] "- **R4 — relay (the watcher's simulated telemetry link, `udp_link.py`).** It now parses every MAVLink frame (v1/v2; SITL" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:34` — note: §1.1 "Set-up changes (harness only; the watcher is not changed)"

### `R5` — **CONFLICT: 5 meanings** (see flags §b)

- [D17 V1/V2 heading-Replay checks] "- **R5 (yaw):** UKF yaw error (`XUKF` against SIM) in the pinned cruise window: p95 ≤ 1.0°, max ≤ 2.0°" — `METHODOLOGY.md:7606` — note: PASS criteria of D17 V1 (Replay check on set (b) logs); reused live for V2 (line 7611)
- [Experiment H supervisor ruling items (2026-10-08)] "**R5. A pre-registered prediction for drift and re-lock per estimator** (METHODOLOGY pre-registration)." — `docs/tag_hold_design.md:39` — note: §R "Supervisor ruling 2026-10-08 (incorporated)"
- [rgs_check_tex roll-gain check criteria] "| R5 | no new oscillation on any axis | cruise gyro-y rms ≤ 0.0108 and gyro-z rms ≤ 0.0200 (2× old); on every axis the largest spectral peak's ±0.5 Hz band rms **≤ 0.02 rad/s** | A single tone above 0.02 would be ≥ 2× all of the old non-roll rotational activity (y and z total rms ≤ 0.010). | PRIMARY |" — `METHODOLOGY.md:4612` — note: pre-registered PRIMARY criteria of check flight rgs_check_tex (METHODOLOGY "Check flight `rgs_check_tex`: pre-registration")
- [rung-1 work items (minimal real-flight plan)] "| R5 | **Firmware** for the board: pinned commit, clean worktree, build, archive, flash, rollback rehearsal (or flash stock 4.7.0) | 0.5–1 d | S1, S6 | build: once S1 is known | Low–medium. Bootloader and flashing quirks; the vehicle's existing parameters. |" — `docs/minimal_real_flight_plan.md:362` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67
- [watcher bench re-run set-up changes] "- **R5 — provenance.** Every session's `bench.log` records the repository HEAD and any uncommitted change under" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:39` — note: §1.1 "Set-up changes (harness only; the watcher is not changed)"

### `R7`

- [rung-1 work items (minimal real-flight plan)] "| R7 | **Mocap recorder/adapter** plus the frame convention | 0.5–1.5 d | S5 | partly | Medium [U] |" — `docs/minimal_real_flight_plan.md:364` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67

### `R8`

- [rung-1 work items (minimal real-flight plan)] "| R8 | **`mocap_align` on `RISI`**, group-delay rule, SITL re-self-test | 0.5 d | — | **yes** | Low |" — `docs/minimal_real_flight_plan.md:365` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67

### `R9`

- [rung-1 work items (minimal real-flight plan)] "| R9 | **Scorer** `real_score.py` with the pre-registered window | 1–1.5 d | R3, R8 | **yes** | Low |" — `docs/minimal_real_flight_plan.md:366` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67

### `R10`

- [rung-1 work items (minimal real-flight plan)] "| R10 | **Pre-registration** of rung 1: profile, n, window, metrics, Replay tolerance, converter band, claims | 0.5 d | — | **yes** | Low |" — `docs/minimal_real_flight_plan.md:367` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67

### `R11`

- [rung-1 work items (minimal real-flight plan)] "| R11 | **Flight cards**: pre-flight (parameter readback, `DSF`, origin if a circle fence is used, mode switches, fence test), sync wiggles, profile, abort calls, post-flight (log download, `DSF`, pipeline run) | 1 d | R6 | **yes** | Low |" — `docs/minimal_real_flight_plan.md:368` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67

### `R12`

- [rung-1 work items (minimal real-flight plan)] "| R12 | **Bench (props off)**: sensors healthy; flow orientation (rotate the vehicle and check that `OF.bodyX/Y` and `flowX/Y` agree in sign: ArduPilot's standard flow check); rangefinder on the ground and lifted; `LOG_REPLAY` log complete | 0.5–1 d | R5, R6 | no | Medium |" — `docs/minimal_real_flight_plan.md:369` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67

### `R13`

- [rung-1 work items (minimal real-flight plan)] "| R13 | **Hand-carried check in the volume** (motors off): carry the vehicle along the profile at flight height, with sync wiggles at both ends. **The SAME DAY**, run the whole offline pipeline (R4, R2, R1, R8, R9) on that log. This is the end-to-end rehearsal and the first real Replay check. **Limit:** disarmed, EKF3 ..." — `docs/minimal_real_flight_plan.md:370` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67

### `R14`

- [rung-1 work items (minimal real-flight plan)] "| R14 | Flight day(s): first hover, then n = 3–5 repeats (+3 over a plain sheet if S7) | 1–1.5 d | R13, mocap booking, safety pilot | no | **High.** Hardware, weather-free but lab-bound. |" — `docs/minimal_real_flight_plan.md:371` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67

### `R15`

- [rung-1 work items (minimal real-flight plan)] "| R15 | Offline runs + scoring of all flights, plus a METHODOLOGY result entry | 1 d | R14 | no | Low |" — `docs/minimal_real_flight_plan.md:372` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67

### `R-a` — **CONFLICT: 2 meanings** (see flags §b)

- [M2r attempt validity criteria] "- R-a: no BREACH and no crash disarm (FC text "Crash") from the arm to the next M1;" — `docs/handovers/2026-10-12_m2r_rerun.md:106` — note: §1.5 "Validity of an attempt"; conflicts with the copter-plan R-a..R-e TODO items
- [rung-1 no-hardware TODO items (copter plan §3.2)] "| R-a | **Pre-registration sign-off** (the user), then apply it: primary metric (evo -a SE(3) proposed), UKF record, drift segment, n, the Replay-fidelity tolerance (1 cm / 0.1°), the converter band, the timestamp rule. Mark the JSON final | 0.25 d after the ruling | DRAFT | **YES**, for result sorties (verification ..." — `docs/realflight_plan_copter.md:139`
- [rung-1 no-hardware TODO items (copter plan §3.2)] "2. **The no-hardware TODO** (plan §3.2 R-a…R-i, §4.3 U-a…U-l), in that order of priority: blocking items first." — `docs/handovers/2026-10-12_copter_plan.md:88` — note: confirms the R-a…R-i range

### `R-b` — **CONFLICT: 2 meanings** (see flags §b)

- [M2r attempt validity criteria] "- R-b: the true horizontal excursion from the ALT_HOLD entry point ≤ 2.0 m before touchdown;" — `docs/handovers/2026-10-12_m2r_rerun.md:107` — note: §1.5 "Validity of an attempt"; conflicts with the copter-plan R-a..R-e TODO items
- [rung-1 no-hardware TODO items (copter plan §3.2)] "| R-b | **Merge `rung1-geometry`** (after the E5 ruling) and **install a fork Replay built from it** (one light `heavy.py` build; re-check SITL byte-identity). The installed Replay still hard-codes the 0.12/0.25 m levers and the old derotation | 0.5 d | built in scratch, not merged | **YES** for the UKF row (EKF3 and ..." — `docs/realflight_plan_copter.md:140`

### `R-c` — **CONFLICT: 2 meanings** (see flags §b)

- [M2r attempt validity criteria] "- R-c: no "EKF Failsafe" FC text before touchdown (R2);" — `docs/handovers/2026-10-12_m2r_rerun.md:108` — note: §1.5 "Validity of an attempt"; conflicts with the copter-plan R-a..R-e TODO items
- [rung-1 no-hardware TODO items (copter plan §3.2)] "| R-c | **Capture-delay option in the port** (prereg §6: UKF at arrival − d_cap, like the FGO converter), default unchanged; Replay regression byte-identical | 0.5–1 d | not started; needs a ruling | **YES** for the UKF row as drafted (or re-word the prereg to EKF3's flow time for the UKF) |" — `docs/realflight_plan_copter.md:141`

### `R-d` — **CONFLICT: 2 meanings** (see flags §b)

- [M2r attempt validity criteria] "- R-d: `flow_bias.csv` shows "pass" mode for every message sent after the touchdown command (the runaway is EKF3's own," — `docs/handovers/2026-10-12_m2r_rerun.md:109` — note: §1.5 "Validity of an attempt"; conflicts with the copter-plan R-a..R-e TODO items
- [rung-1 no-hardware TODO items (copter plan §3.2)] "| R-d | **`XUKO` from a Replay run.** The prereg's proposed UKF record is `XUKO`, but Replay's logger does not emit FMT records for the UKF's messages (METHODOLOGY "Replay logging note"), and `ukf_shadow.csv` holds the horizon-time state. Check whether `XUKO` exists in a Replay output log; if not, add a current-time ..." — `docs/realflight_plan_copter.md:142`
- [rung-1 no-hardware TODO items (copter plan §3.2)] "- **Source (R-d CLOSED, 2026-10-12, ruling 4): the FMT-declared `XUKO` record in the Replay output log**, read by" — `docs/u10_replay_gate_band_draft.md:73` — note: status only: R-d marked CLOSED 2026-10-12 (ruling 4)

### `R-e` — **CONFLICT: 2 meanings** (see flags §b)

- [M2r attempt validity criteria] "- R-e: the truth speed (forwarder, 0.5 s baseline) < 0.05 m/s at every `mocap_watch_vel.csv` sample in [t_on, t_end]" — `docs/handovers/2026-10-12_m2r_rerun.md:111` — note: §1.5 "Validity of an attempt"; conflicts with the copter-plan R-a..R-e TODO items
- [rung-1 no-hardware TODO items (copter plan §3.2)] "| R-e | **U4: initialise from `RNGFND1_GNDCLR`** when disarmed and `OutOfRangeLow` [correction 2026-10-12: a PORT rule, NOT "as EKF3 does": at 7bac20cbcc EKF3 pushes no range sample for `OutOfRangeLow` and falls back to baro; implemented on branch `u4-gndclr` `53bac01636`, not merged], default unchanged; Replay ..." — `docs/realflight_plan_copter.md:143`
- [rung-1 no-hardware TODO items (copter plan §3.2)] *(superseded)* "- The "as EKF3 does" wording is WRONG in three places: the costing U4 row, plan R-e, and rung-1 prereg §9 item 11." — `METHODOLOGY.md:13808` — note: the R-e wording "as EKF3 does" declared wrong; the row in realflight_plan_copter.md:143 carries an inline [correction 2026-10-12]

### `R-f`

- [rung-1 no-hardware TODO items (copter plan §3.2)] "| R-f | **Converter acceptance band** (FGO-from-BIN against FGO-from-bag, full `cl_a_tex_half`): pre-register the band, then one light replay | 0.5 d | open (R1 follow-up) | no (an acceptance check of a tool already proven at default) |" — `docs/realflight_plan_copter.md:144`

### `R-g`

- [rung-1 no-hardware TODO items (copter plan §3.2)] "| R-g | **Flight cards:** add F2 (PROPOSED wording, the 5 s is this plan's proposal: "after any automatic LAND, the SP disarms if the FC has not disarmed within 5 s of touchdown"), a GNDCLR line, and the compass-health line for the chosen variant | 0.1 d | not done | **YES** (a safety card line; trivial) |" — `docs/realflight_plan_copter.md:145`

### `R-h`

- [rung-1 no-hardware TODO items (copter plan §3.2)] "| R-h | R8: remove or re-validate the 25 Hz `IMU` fallback; decide whether `--init-seg` uses the motion-onset rule | 0.25 d | open | no |" — `docs/realflight_plan_copter.md:146`

### `R-i`

- [rung-1 no-hardware TODO items (copter plan §3.2)] "| R-i | **Stale parameter names** (every parameter-like token checked against `pinned_param_names.txt`, 2026-10-12): **CLAUDE.md**: `ARMING_CHECK` → `ARMING_SKIPCHK` (Hidden Configuration Audit §2); `FLOW_MAX` → `EK3_FLOW_MAX` and `FLOW_M_NSE` → `EK3_FLOW_M_NSE` (UKF Design robustness table and text); `RNGFND1_MIN_CM` ..." — `docs/realflight_plan_copter.md:147`

### `R-j`

- [rung-1 no-hardware TODO items (copter plan §3.2)] "| R-j | Rung-1 firmware build ready: `build_board_fw.sh <B> --ref 7bac20cbcc --without` | 0 d | **DONE** (dry run, §6) | — |" — `docs/realflight_plan_copter.md:148` — note: R-j is outside the assigned R-a..R-i range but is in the same table

### `S1` — **CONFLICT: 7 meanings** (see flags §b)

- [H stages] "**S1 (EKF3 flies; `AHRS_EKF_TYPE 3`, closed loop on the tag-relative estimate):** the H profile of the design, 3" — `METHODOLOGY.md:10661`
- [H stages] "- **S1:** EKF3 flies; UKF and FGO in shadow (live) and offline. 3 flights." — `docs/tag_hold_design.md:167`
- [closed-loop safety criteria S1/S2 (no-heading miss-reading clause)] "- **(S1)** no fast runaway before cruise +50 s (U2 as worded: no wall contact before +50 s);" — `METHODOLOGY.md:6966`
- [closed-loop safety criteria S1/S2 (no-heading miss-reading clause)] "- **Safety criteria S1 and S2 (the miss-reading clause) are unchanged as ruled:** S1 is no fast" — `METHODOLOGY.md:7361` — note: restated as ruled
- [robust-FGO heading test (plan step 2(a)) secondary decision rules] "- **S1 (secondary):** on the plain-wall flights, the robust FGO accepts **fewer wrong headings** than the hard-gated" — `METHODOLOGY.md:9733`
- [rung-1 supervisor inputs (minimal real-flight plan §1)] "| S1 | **FC board.** An H7 is assumed (Pixhawk 6X/6C, CubeOrange(+), Durandal, MatekH743, KakuteH7: all have hwdefs at the pinned commit [V]). | Firmware build target. EKF precision: on H7, `HAL_HAVE_HARDWARE_DOUBLE` is 1 (`hwdef/scripts/STM32H743xx.py:76` [V]), so EKF3 runs in double as SITL/Replay do ..." — `docs/minimal_real_flight_plan.md:44` — note: §1 "Inputs from the supervisor (on the critical path)"
- [stage-3 safety gates (UKF-only closed loop)] "| S1 | **SITL V1–V7** on the MAVLink camera-flow path with the exact source commit to be flown (SITL build) | each as pre-registered in the costing §6 table, plus the land detector trips after LAND (F2) in V3/V4. **V1 must show the D18 swap active** | plan §4.2 |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:197` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"
- [stage-3 safety gates (UKF-only closed loop)] "- **Safety gates S1–S11 before any free flight:**" — `docs/handovers/2026-10-12_port_merge_u4_drafts.md:199` — note: earlier list stopped at S1–S11 (S12/S13 added later)
- [watcher F6 LAND re-send stop conditions] "- **S1:** a DO_SET_MODE ACK arrives;" — `docs/handovers/2026-10-12_watcher_f6_failsafe_b5_b8a.md:16` — note: "Stop for good" conditions of the new watcher LAND rule
- [watcher bench M2 set-up items] "- **S1 — the watcher's checks.** Every primary watcher runs `--yaw-check require` AND `--vel-check require`." — `docs/handovers/2026-10-12_m2_full_bench.md:58` — note: §1.1 Set-up: "everything in"

### `S2` — **CONFLICT: 7 meanings** (see flags §b)

- [H stages] "- **S2:** the UKF flies through the port. Gates first: port position-input equivalence test and a ground test. 3" — `docs/tag_hold_design.md:168`
- [closed-loop safety criteria S1/S2 (no-heading miss-reading clause)] "- **(S2)** the estimator valid throughout: `XUKS.SS` `horiz_pos_rel` true from take-off to landing," — `METHODOLOGY.md:6967`
- [closed-loop safety criteria S1/S2 (no-heading miss-reading clause)] "S2 = `XFGO.OV` 100% from arming to disarm. EKF3 is reported as a diagnostic." — `METHODOLOGY.md:9277` — note: S2 redefined for the FGO scorer (--est fgo): output-valid flag
- [robust-FGO heading test (plan step 2(a)) secondary decision rules] "- **S2 (secondary):** the robust FGO's **maximum cross-track** ≤ the hard-gated FGO's on **≥ 8 of 12**." — `METHODOLOGY.md:9737`
- [rung-1 supervisor inputs (minimal real-flight plan §1)] "| S2 | **Is the vehicle already flying?** Which firmware version is on it? Is it tuned? | 0 d of airframe work if it is already flying. Otherwise assembly and tune cost 3–6 d (`A1`+`A2`), which **breaks the calendar** (§6). |" — `docs/minimal_real_flight_plan.md:45` — note: §1 "Inputs from the supervisor (on the critical path)"
- [stage-3 safety gates (UKF-only closed loop)] "| S2 | **U10 Replay gate PASS** on the rung-1 logs | `docs/u10_replay_gate_band_draft.md` §4 | U-d0 |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:198` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"
- [watcher F6 LAND re-send stop conditions] "- **S2:** an FC heartbeat after the first send shows LAND;" — `docs/handovers/2026-10-12_watcher_f6_failsafe_b5_b8a.md:17` — note: "Stop for good" conditions of the new watcher LAND rule
- [watcher bench M2 set-up items] "- **S2 — H10 on every flight script.** Every bench flight script runs `--h10-guard`; the guard decision now calls the" — `docs/handovers/2026-10-12_m2_full_bench.md:65` — note: §1.1 Set-up: "everything in"

### `S2a`

- [rung-1 port spec options] "- **S2a. Emit the FMT records in Replay.** Before its first `WriteStreaming("XU…")` in Replay, the UKF makes sure the" — `docs/rung1_port_spec_capture_delay_xuko.md:69`

### `S2b`

- [rung-1 port spec options] "- **S2b. A current-time CSV.** In Replay, write `ukf_output.csv` with EXACTLY `XUKO`'s columns and values, at the same" — `docs/rung1_port_spec_capture_delay_xuko.md:80`

### `S3` — **CONFLICT: 5 meanings** (see flags §b)

- [H stages] "- **S3:** the FGO flies through the node. Gates first: node-equivalence test and a ground test (D25 style). 3 flights." — `docs/tag_hold_design.md:170`
- [rung-1 supervisor inputs (minimal real-flight plan §1)] "| S3 | **Flow sensor** (PMW3901-class on SPI = `FLOW_TYPE 2` Pixart; HereFlow = 6 DroneCAN; MTF-01/UPFLOW/MSP = 5/8/7 [V `AP_OpticalFlow.cpp:30`]) | `FLOW_TYPE`, `FLOW_ORIENT_YAW`, `EK3_FLOW_DELAY`, and the source of the derotation rate (§4.3: Pixart and MAV/MSP use the FC's gyro; HereFlow uses the sensor's own gyro ..." — `docs/minimal_real_flight_plan.md:46` — note: §1 "Inputs from the supervisor (on the critical path)"
- [stage-3 safety gates (UKF-only closed loop)] "| S3 | **Bench P1–P10** on the flashed image | incl. **P5: arming refused with `AHRS_UKF_TFAIL` ≠ 0, normal AND forced**; P4 backends off = EKF3 | `docs/board_firmware_plan.md` §5 |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:199` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"
- [watcher F6 LAND re-send stop conditions] "- **S3:** a heartbeat shows a **pilot mode** (ArduCopter `is_autopilot() == false`: STABILIZE, ACRO, ALT_HOLD, LOITER," — `docs/handovers/2026-10-12_watcher_f6_failsafe_b5_b8a.md:18` — note: "Stop for good" conditions of the new watcher LAND rule
- [watcher bench M2 set-up items] "- **S3 — M1 in the harness.** Before every hover that follows a landing in the same FC boot: the carry home (A7/A9)," — `docs/handovers/2026-10-12_m2_full_bench.md:72` — note: §1.1 Set-up: "everything in"

### `S4` — **CONFLICT: 4 meanings** (see flags §b)

- [rung-1 supervisor inputs (minimal real-flight plan §1)] "| S4 | **Rangefinder** (TF-Luna/TFmini = Benewake serial; VL53L1X = I²C) | `RNGFND1_TYPE`, `MIN`/`MAX`, `GNDCLR`. The minimum range matters: a TF-Luna's 0.2 m minimum means it reads out of range on the ground. |" — `docs/minimal_real_flight_plan.md:47` — note: §1 "Inputs from the supervisor (on the critical path)"
- [stage-3 safety gates (UKF-only closed loop)] "| S4 | **Forced invalidity → LAND** on the bench, then on the tether | `thesis_nav_check` text + mode LAND (reason EKF failsafe) within **0.1 s** of TFAIL (S-A2 (a) band); on the tether S-A1 (attitude ≤ 3° / yaw ≤ 5°) and S-A3 (disarm ≤ 40 s, tilt ≤ 15°, horizontal displacement ≤ 1.5 m, touchdown ≤ 1.0 m/s) | ..." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:200` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"
- [watcher F6 LAND re-send stop conditions] "- **S4:** a heartbeat shows a mode other than LAND and other than M0 (a change the watcher did not command);" — `docs/handovers/2026-10-12_watcher_f6_failsafe_b5_b8a.md:21` — note: "Stop for good" conditions of the new watcher LAND rule
- [watcher bench M2 set-up items] "- **S4 — safety net.** If `ensure_watcher` does not see a confirmation within its 90 s cap and the watcher's ONLY" — `docs/handovers/2026-10-12_m2_full_bench.md:76` — note: §1.1 Set-up: "everything in"

### `S5` — **CONFLICT: 4 meanings** (see flags §b)

- [rung-1 supervisor inputs (minimal real-flight plan §1)] "| S5 | **Mocap system** (OptiTrack/Vicon), rate, how recordings are exported, volume size, booking dates | The recorder (§4.5), the frame convention (OptiTrack streams Y-up by default), the flight profile size, and the calendar. |" — `docs/minimal_real_flight_plan.md:48` — note: §1 "Inputs from the supervisor (on the critical path)"
- [stage-3 safety gates (UKF-only closed loop)] "| S5 | **Aiding-loss timing S-A2b on the FC:** flow occluded → LAND | within **5.5 s of the last flow received by the FC** (pre-registered 2026-10-11) | ruling 2026-10-11 |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:201` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"
- [watcher F6 LAND re-send stop conditions] "- **S5:** 5 sends have been made." — `docs/handovers/2026-10-12_watcher_f6_failsafe_b5_b8a.md:22` — note: "Stop for good" conditions of the new watcher LAND rule
- [watcher bench M2 set-up items] "- **S5 — M3 in the harness.** The simulated pilot (A7b) disarms after **2 s** on the ground in LAND (was 4 s)." — `docs/handovers/2026-10-12_m2_full_bench.md:79` — note: §1.1 Set-up: "everything in"

### `S6` — **CONFLICT: 3 meanings** (see flags §b)

- [rung-1 supervisor inputs (minimal real-flight plan §1)] "| S6 | **Firmware choice:** the pinned `7bac20cbcc` built from unmodified source, or the nearest stock release (`Copter-4.7.0`) | §2. |" — `docs/minimal_real_flight_plan.md:49` — note: §1 "Inputs from the supervisor (on the critical path)"
- [stage-3 safety gates (UKF-only closed loop)] "| S6 | **Watcher heartbeat withdrawn → LAND** within `FS_GCS_TIMEOUT` (MAVLink path; first real test) | as carded | W cards |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:202` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"
- [watcher bench M2 set-up items] "- **S6 — sessions and order:** `ground`, `hoverA`, `hoverB`, `hoverC`, `f7`, `m2`; one simulation at a time, each" — `docs/handovers/2026-10-12_m2_full_bench.md:80` — note: §1.1 Set-up: "everything in"

### `S7` — **CONFLICT: 2 meanings** (see flags §b)

- [rung-1 supervisor inputs (minimal real-flight plan §1)] "| S7 | **Floor:** can a plain (low-texture) sheet be laid in the volume? | Whether the degraded-sensing variable can be touched at all (§7). |" — `docs/minimal_real_flight_plan.md:50` — note: §1 "Inputs from the supervisor (on the critical path)"
- [stage-3 safety gates (UKF-only closed loop)] "| S7 | **RC override wins** over GUIDED/LOITER/LAND; F6 fixed (the watcher stops re-sending LAND once the FC shows LAND or a pilot mode) | B10 on the vehicle; F6 offline tests + 83 `realflight` tests | U-a |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:203` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"

### `S8`

- [stage-3 safety gates (UKF-only closed loop)] "| S8 | **U4 on the vehicle** (only if `RNGFND1_MIN` > the resting clearance): the UKF initialises on the ground from `RNGFND1_GNDCLR` (`UKF: rangefinder below minimum on ground` text) and arms in type 12 | as stated | U-b |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:204` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"

### `S9`

- [stage-3 safety gates (UKF-only closed loop)] "| S9 | **Hand-carried H3:** the onboard `XUKO` against mocap is sane (the flow sign is correct: the UKF moves the right way on every carried leg); the onboard `XUKF` replayed with the U10 G6 bands **[TBD-V]** | as stated | §2 |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:205` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"

### `S10`

- [stage-3 safety gates (UKF-only closed loop)] "| S10 | **The land detector trips** after a commanded LAND under type 12 (F2), on the tether; the card line "after any automatic LAND, the SP disarms if the FC has not disarmed within 5 s of touchdown" | as stated | R-g, U-g |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:206` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"

### `S11`

- [stage-3 safety gates (UKF-only closed loop)] "| S11 | **Battery and RC failsafes** read back; G6 arming procedure; the watcher system ID set | readback | U-e, U-k |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:207` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"

### `S12`

- [stage-3 safety gates (UKF-only closed loop)] "| S12 | **EKF origin set and VERIFIED at every boot** (ruling 1, 2026-10-12) | the origin sent (or set by AHRS from `AHRS_ORIGIN_*`) only after every EKF3 core has reported initialised; a `GPS_GLOBAL_ORIGIN` received with the lat/lon set; an `ORGN` record in the log before the ARM event. NO ARMING without it | ..." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:208` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"
- [stage-3 safety gates (UKF-only closed loop)] "- B11 is added to §7.2; S12/S13 to the stage-3 draft." — `METHODOLOGY.md:13959` — note: records that S12/S13 were added to the stage-3 draft

### `S13`

- [stage-3 safety gates (UKF-only closed loop)] "| S13 | **F7 yaw check** (ruling 2, 2026-10-12): the watcher refuses arming unless the FC yaw agrees with mocap within 5° for ≥ 1 s; informational once armed | real bench B11 (a)–(d) PASS; SITL `wbench3_f7` | `docs/real_flights_plan.md` §7.2 B11 |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:209` — note: §5 "Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)"

### `S-A1`

- [SITL safety-test criteria (forced failure → LAND)] "- **S-A1 (attitude correct, not frozen):** |AHRS roll/pitch (ATT) − GT| ≤ **3°** max, and |yaw − GT| ≤ **5°**." — `METHODOLOGY.md:11295` — note: criteria from failure instant to disarm, UKF (a)/(b), FGO (a)/(b) safety runs
- [SITL safety-test criteria (forced failure → LAND)] "*Safety criteria (pre-registered): S-A1 attitude error; S-A2 'position lost' declared within the bound (0.75 s; UKF (b) 5.5 s); S-A3 safe landing (≤ 1.5 m drift to touchdown, no watcher breach); S-A4 a single landing, pre-registered for (b) runs only. UKF (b) v2 / v3 S-A2: the trigger fired 5.0 s after the last flow ..." — `docs/thesis/tables/T7_failure_behaviour.md:11` — note: same meaning restated in table caption

### `S-A2`

- [SITL safety-test criteria (forced failure → LAND)] "- **S-A2 (trigger):** the "Thesis nav: … position lost" text and a mode change to LAND (reason EKF failsafe):" — `METHODOLOGY.md:11297` — note: criteria from failure instant to disarm, UKF (a)/(b), FGO (a)/(b) safety runs

### `S-A2b`

- [SITL safety-test criteria (forced failure → LAND)] "- **Supplementary criterion for FUTURE tests only, PRE-REGISTERED NOW:** S-A2b is the trigger time measured from" — `METHODOLOGY.md:13669` — note: supplementary criterion for future tests only; S-A2 stays as worded
- [SITL safety-test criteria (forced failure → LAND)] "| S5 | **Aiding-loss timing S-A2b on the FC:** flow occluded → LAND | within **5.5 s of the last flow received by the FC** (pre-registered 2026-10-11) | ruling 2026-10-11 |" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:201` — note: carried into stage-3 gate S5

### `S-A3`

- [SITL safety-test criteria (forced failure → LAND)] "- **S-A3 (safe landing):**" — `METHODOLOGY.md:11301` — note: criteria from failure instant to disarm, UKF (a)/(b), FGO (a)/(b) safety runs

### `S-A4`

- [SITL safety-test criteria (forced failure → LAND)] "- **S-A4 (b runs only):** S-A1–S-A3 with both landing paths active, and a single landing (no re-arm, no mode" — `METHODOLOGY.md:11307` — note: criteria from failure instant to disarm, UKF (a)/(b), FGO (a)/(b) safety runs

### `U1` — **CONFLICT: 3 meanings** (see flags §b)

- [UKF-only closed-loop costing items] "| U1 | **Board firmware** with `AP_NavUKF` | `#define AP_NAVUKF_ENABLED (CONFIG_HAL_BOARD == HAL_BOARD_SITL)` (fork `libraries/AP_NavUKF/AP_NavUKF.h:28-29`); no board build exists | §2 | SW 1–2 d (shared with 2(a)); HW 1 d | SW+HW |" — `docs/ukf_only_closed_loop_costing.md:65` — note: §1 "What it needs, with effort"
- [closed-loop no-heading flight PRIMARY criteria U1–U3] "- **U1 (the backend flies the vehicle).** Arming, take-off to ≥ 1.8 m and entry into cruise under UKF" — `METHODOLOGY.md:6868` — note: UKF set (a) no-heading flight, first registration
- [closed-loop no-heading flight PRIMARY criteria U1–U3] "- **U1:** as before. The backend flies the vehicle through arming, take-off to ≥ 1.8 m and entry into" — `METHODOLOGY.md:7350` — note: restated unchanged
- [real-flight unknowns from the user (readiness §0)] "| U1 | **Flight-controller board.** Part C §5 assumed an STM32H743 (Pixhawk 6X or CubeOrange). The UKF port uses `double` state and covariance, so the board needs a hardware double FPU (H7 class). | G1a, G1b, G2, C1 |" — `docs/real_flight_readiness.md:36` — note: §0 "Required inputs from the user (unknown; not assumed)"

### `U2` — **CONFLICT: 3 meanings** (see flags §b)

- [UKF-only closed-loop costing items] "| U2 | **Real sensor geometry** in the port | fork-r1 `c25fa898`, on hold; **its Replay regression and `UKF_Equiv` not re-verified** (commit message) | merge after the regression | 0.5 d (needs one build slot) | SW (light build) |" — `docs/ukf_only_closed_loop_costing.md:66` — note: §1 "What it needs, with effort"
- [closed-loop no-heading flight PRIMARY criteria U1–U3] "- **U2:** no wall contact before cruise **+100 s**. Basis: the fastest implied contact in all fixed-UKF" — `METHODOLOGY.md:7352` — note: replacement band (+100 s)
- [closed-loop no-heading flight PRIMARY criteria U1–U3] *(superseded)* "- **U2.** No wall contact before cruise **+50 s**. Basis: the fastest implied contact in the offline" — `METHODOLOGY.md:6870` — note: original +50 s band; replaced by +100 s at line 7352 ("PRIMARY criteria (replacing U2/U3; U1 unchanged)")
- [real-flight unknowns from the user (readiness §0)] "| U2 | **Vehicle type.** Copter, or ArduPlane QuadPlane in Q modes (Part C scope)? `thesis_nav_check` exists only in `ArduCopter/`. | G1b, G4, H10 |" — `docs/real_flight_readiness.md:37` — note: §0 "Required inputs from the user (unknown; not assumed)"

### `U3` — **CONFLICT: 3 meanings** (see flags §b)

- [UKF-only closed-loop costing items] "| U3 | **Flow derotation input** (D18) | the port takes the driver's `rawGyroRates` (fork `AP_NavUKF.cpp:470`) | §3; decide, then (optionally) one port change | 0–1 d | SW |" — `docs/ukf_only_closed_loop_costing.md:67` — note: §1 "What it needs, with effort"
- [closed-loop no-heading flight PRIMARY criteria U1–U3] "- **U3:** contact on the **WEST wall inside [+146, +218] s**. Basis: the validated method's cluster," — `METHODOLOGY.md:7513` — note: UKF current window [+146, +218] s
- [closed-loop no-heading flight PRIMARY criteria U1–U3] "- **U3: west-wall contact inside [+145, +196] s.**" — `METHODOLOGY.md:8995` — note: FGO variant: window [+145, +196] s by the same rule
- [closed-loop no-heading flight PRIMARY criteria U1–U3] *(superseded)* "- **U3.** If contact occurs, it is on the **west wall inside [+83, +135] s**. Basis: the +98…+110 s" — `METHODOLOGY.md:6872` — note: original [+83, +135] s window; replaced at line 7354
- [closed-loop no-heading flight PRIMARY criteria U1–U3] *(superseded)* "- **U3:** contact on the **WEST wall inside [+160, +217] s**. Basis: the port distribution's main" — `METHODOLOGY.md:7354` — note: [+160, +217] s window; replaced again at line 7513 ("UPDATED PRIMARY criteria (U1 and U2 unchanged; U3 replaced)")
- [real-flight unknowns from the user (readiness §0)] "| U3 | **Companion computer.** Pi 4 or Pi 5? RAM? Cooling? | A4, G8 |" — `docs/real_flight_readiness.md:38` — note: §0 "Required inputs from the user (unknown; not assumed)"

### `U5` — **CONFLICT: 2 meanings** (see flags §b)

- [UKF-only closed-loop costing items] "| U5 | **Yaw source** | the UKF has no compass input (`use_compass()` false, fork `AP_AHRS_UKF.h:27`); it uses the variance-gated zero-innovation pseudo-yaw | §4; a decision, not code | 0 d (nomag) | — |" — `docs/ukf_only_closed_loop_costing.md:69` — note: §1 "What it needs, with effort"
- [real-flight unknowns from the user (readiness §0)] "| U5 | **Forward camera and lens**, if flown. | A6, D2, D6 |" — `docs/real_flight_readiness.md:40` — note: §0 "Required inputs from the user (unknown; not assumed)"

### `U6` — **CONFLICT: 2 meanings** (see flags §b)

- [UKF-only closed-loop costing items] "| U6 | **Landing trigger** | `Copter::thesis_nav_check`, a `FAST_TASK` (fork `ArduCopter/Copter.cpp:136`, `ekf_check.cpp:337-358`), SITL safety (a) PASS; **the re-run on the corrected builds is still open (H1)** | §5 | 0 d code; H1 re-run ~0.5 d (UKF only) | SIM |" — `docs/ukf_only_closed_loop_costing.md:70` — note: §1 "What it needs, with effort"
- [real-flight unknowns from the user (readiness §0)] "| U6 | **Rangefinder model and interface.** Serial/I²C to the FC, or read on the Pi. Minimum range. | A8, A9, C2 |" — `docs/real_flight_readiness.md:41` — note: §0 "Required inputs from the user (unknown; not assumed)"

### `U7` — **CONFLICT: 2 meanings** (see flags §b)

- [UKF-only closed-loop costing items] "| U7 | **Failsafe parameter file** (real FC) | the SITL files exist (`closedloop_ukf.parm`); the real-FC template is rung-1 R6 | `AHRS_EKF_TYPE 12`, `AHRS_UKF_ENABLE 1`, `AHRS_UKF_TFAIL 0`, `FS_EKF_ACTION 1`, the GCS failsafe, battery, RC | 0.5 d on top of R6 | SW |" — `docs/ukf_only_closed_loop_costing.md:71` — note: §1 "What it needs, with effort"
- [real-flight unknowns from the user (readiness §0)] "| U7 | **Mocap system.** Vicon or OptiTrack. Rate. Streaming protocol (VRPN/NatNet). Time source (PTP/NTP). Capture-volume size. | F1, I3, I4, H9 |" — `docs/real_flight_readiness.md:42` — note: §0 "Required inputs from the user (unknown; not assumed)"

### `U8` — **CONFLICT: 2 meanings** (see flags §b)

- [UKF-only closed-loop costing items] "| U8 | **Watcher** | G1–G11 built and merged (`realflight/watcher/`, 73 offline tests); SITL bench B0–B10 is 2(c); live mocap client F1 not built | §5 | F1 1–2 d (protocol per U7 mocap); B0–B10 in 2(c); hardware bench 1 d | SW + SIM + HW |" — `docs/ukf_only_closed_loop_costing.md:72` — note: §1 "What it needs, with effort"
- [real-flight unknowns from the user (readiness §0)] "| U8 | **Airframe.** Frame size, prop guards, battery, RC transmitter and receiver, telemetry radio. | A1, A2, H5 |" — `docs/real_flight_readiness.md:43` — note: §0 "Required inputs from the user (unknown; not assumed)"

### `U9` — **CONFLICT: 2 meanings** (see flags §b)

- [UKF-only closed-loop costing items] "| U9 | **SITL verification flights** with a SITL flow sensor | none with `SIM_FLOW` | §6 | harness 0.5 d; flights 1.5–2 d | SIM (after 16 Oct) |" — `docs/ukf_only_closed_loop_costing.md:73` — note: §1 "What it needs, with effort"
- [real-flight unknowns from the user (readiness §0)] "| U9 | **UKF placement** (plan question 2): onboard the FC (the port) or on the Pi. | G1b, G10 |" — `docs/real_flight_readiness.md:44` — note: §0 "Required inputs from the user (unknown; not assumed)"

### `U10`

- [UKF-only closed-loop costing items] "| U10 | **Replay gate on rung-1 logs** | the Replay UKF exists (fork Replay hooks) | §7 | 0.5–1 d after the first rung-1 log | SW |" — `docs/ukf_only_closed_loop_costing.md:74` — note: §1 "What it needs, with effort"
- [UKF-only closed-loop costing items] "# U10: the Replay gate on rung-1 logs. FOR FINAL SIGN-OFF" — `docs/u10_replay_gate_band.md:1` — note: U10 Replay gate; its G criteria are covered by another agent

### `U11`

- [UKF-only closed-loop costing items] "| U11 | **Bench, hand-carried, tethered** | not built (readiness H4, H7, H8) | §8 | 2.5–3.5 d | HW |" — `docs/ukf_only_closed_loop_costing.md:75` — note: §1 "What it needs, with effort"

### `U12`

- [UKF-only closed-loop costing items] "| U12 | **Safety tests on the vehicle** | the SITL analogues exist | §9 | in U11 + 0.5 d | HW |" — `docs/ukf_only_closed_loop_costing.md:76` — note: §1 "What it needs, with effort"

### `U13`

- [UKF-only closed-loop costing items] "| U13 | **CPU and flash on the H743** | estimates only | §10 | in U1/U11 | HW |" — `docs/ukf_only_closed_loop_costing.md:77` — note: §1 "What it needs, with effort"

### `U14`

- [UKF-only closed-loop costing items] "| U14 | **Stage-3 pre-registration** (profile, n, window, abort rules) | not written | | 1–1.5 d | SW |" — `docs/ukf_only_closed_loop_costing.md:78` — note: §1 "What it needs, with effort"

### `U15`

- [UKF-only closed-loop costing items] "| U15 | **Flights and scoring** | | | 1 d flights + 0.5–1 d scoring | HW + SW |" — `docs/ukf_only_closed_loop_costing.md:79` — note: §1 "What it needs, with effort"

### `U-a`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-a | **F6: the watcher's LAND retry.** Stop re-sending once the FC heartbeat shows LAND or any pilot mode (STABILIZE/ALT_HOLD); offline tests; re-run the 83 `realflight` tests | 0.5 d after the ruling | **DONE 2026-10-12** (rule S1–S5/R in `fc_link.py`; 8 new tests; 91/91 pass; handover ..." — `docs/realflight_plan_copter.md:206`

### `U-b`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-b | **U4** (= R-e) | (in R-e) | ruling needed | **YES** if the rangefinder minimum exceeds the ground clearance (the UKF never initialises, so the vehicle cannot arm in type 12) |" — `docs/realflight_plan_copter.md:207`

### `U-c`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-c | **SITL verification flights V1–V7** on the MAVLink flow path (§4.2): harness 0.5 d, one light SITL build, flights 1.5–2 d | 2–2.5 d | not started | **YES** (the costing's SITL gate) |" — `docs/realflight_plan_copter.md:208`

### `U-d`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-d | **Stage-3 pre-registration** (U14): profile (scripted GUIDED or pilot LOITER), n, window, abort rules, the 5 s aiding-loss latency accepted (or not), the watcher box sized for it, S-A2b, the V1–V7 and bench pass criteria (it incorporates U-d0) | 1–1.5 d | not written | **YES** |" — `docs/realflight_plan_copter.md:210`

### `U-d0`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-d0 | **The U10 Replay-gate band, pre-registered** (the onboard UKF replayed on the rung-1 logs: initialises, stays `HORIZ_POS_REL` through hover and moves, `_n_chol_fail` = 0, trajectory against mocap within a band). **Due before any UKF Replay of a real log, i.e. before rung-1 day 3**; otherwise the gate is post ..." — `docs/realflight_plan_copter.md:209`
- [UKF-only no-hardware TODO items (copter plan §4.3)] "- **U-d0: the U10 Replay-gate band must be PRE-REGISTERED before rung-1 day 3, or the gate becomes post hoc**;" — `METHODOLOGY.md:13743` — note: same item restated as a requirement

### `U-e`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-e | **Real-FC failsafe parameter file** (U7): `AHRS_EKF_TYPE 12`, `AHRS_UKF_ENABLE 1`, `AHRS_UKF_TFAIL 0`, `FS_EKF_ACTION 1`, `FS_GCS_ENABLE 5`, `FS_GCS_TIMEOUT`, `MAV_GCS_SYSID` (the watcher), `FS_OPTIONS`, RC and battery failsafes. A `check_parm.py` stage-3 mode that accepts type 12 only there | 0.5 d | ..." — `docs/realflight_plan_copter.md:211`

### `U-f`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-f | **H10 takeover guard + F4** in the real flight script: no LAND when the FC is in a pilot mode or already in LAND; pin the FC's system ID; take the mode mapping from the FC's own heartbeat. (`fly_trial.py` as it is would command LAND in B10b) | 1–2 d | prototype in the bench driver only | **YES if a scripted ..." — `docs/realflight_plan_copter.md:212`

### `U-g`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-g | **F2 investigation** (why the land detector does not trip on flow-only EKF3) and the card line (R-g) | 0.25–0.5 d | open | the card line YES; the investigation no |" — `docs/realflight_plan_copter.md:213`

### `U-h`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-h | **Own-gyro FLOW_TYPEs** (1/3/6/10) ruling: in closed loop (type 12) the rule is the identity, so a HereFlow's own gyro is fused with NO UKF bias; decide accept-and-state or derotate from the port's own DAL gyro (costing §3 option b) | 0–1 d | ruling needed | **YES only if** the sensor is HereFlow/PX4Flow/Bebop ..." — `docs/realflight_plan_copter.md:214`

### `U-i`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-i | **Multi-IMU swap**: on a 2-IMU board, the swap uses EKF3's primary-core bias while the UKF uses `get_first_usable_gyro()`, so it can mix IMUs. Inert in closed loop (type 12 = identity); matters for the U10 Replay gate on the EKF3-flown rung-1 logs. Check the code path; propose a rule (e.g. compare per IMU, or ..." — `docs/realflight_plan_copter.md:215`

### `U-j`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-j | **B5 wording** (the 0.5 s bound equals the stale limit) and **B8a** (void, repeat or accept) rulings. A B8a repeat is one short SITL verification flight on a larger floor | 0–0.25 d | **B5 re-worded 2026-10-12** (ruling 4); **B8a: determined a harness fault** (no EKF origin; handover ..." — `docs/realflight_plan_copter.md:216`

### `U-k`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-k | **G6** (procedure + `ARMING_RUDDER 0`, or the Lua arming-auth) and the watcher system ID (211/213 placeholders) | 0.1 d | rulings needed | YES (the arming procedure) |" — `docs/realflight_plan_copter.md:217`

### `U-l`

- [UKF-only no-hardware TODO items (copter plan §4.3)] "| U-l | Optional: a separate `AP_NAVFGO_ENABLED` flag (a UKF-only build drops ~5 kB flash, ~15 kB RAM) | 0.25 d | optional | no |" — `docs/realflight_plan_copter.md:218`

### `UA1`

- [H backends UKF tier A equivalence bands] "| UA1 | 3-D position difference, every event | **max ≤ 1 mm** |" — `docs/h_backends_tag_input.md:46` — note: tier A (port harness on the offline UKF event stream) bands

### `UA2`

- [H backends UKF tier A equivalence bands] "| UA2 | yaw difference, every event | **max ≤ 0.01°** |" — `docs/h_backends_tag_input.md:47` — note: tier A (port harness on the offline UKF event stream) bands

### `UA3`

- [H backends UKF tier A equivalence bands] "| UA3 | gyro-z bias (rate form); accelerometer bias | **\|Δ\| ≤ 0.1 deg/min; ≤ 0.001 m/s²** (E4) |" — `docs/h_backends_tag_input.md:48` — note: tier A (port harness on the offline UKF event stream) bands

### `UA4`

- [H backends UKF tier A equivalence bands] "| UA4 | gate decisions (flow X/Y, range, pseudo-yaw firings) | **≥ 99.9% identical**; accepted counts within 0.1% (E5) |" — `docs/h_backends_tag_input.md:49` — note: tier A (port harness on the offline UKF event stream) bands

### `UA5`

- [H backends UKF tier A equivalence bands] "| UA5 | tag handling | the re-anchor is at the same event (the first tag event), and the state right after it agrees to **≤ 1e-9** (m, rad); **every** tag event is fused on both sides (8,670, no gate); **0** pseudo-yaw fusions after the anchor on both sides |" — `docs/h_backends_tag_input.md:50` — note: tier A (port harness on the offline UKF event stream) bands

### `UB1`

- [H backends UKF tier B Replay checks] "- **UB1 (same input):**" — `docs/h_backends_tag_input.md:60` — note: tier B (Replay) checks
- [H backends UKF tier B Replay checks] "(UB1–UB6), and scored BEFORE any UKF flight." — `METHODOLOGY.md:12441` — note: tier B re-registered on H_s1far_r1 with the same bands

### `UB2`

- [H backends UKF tier B Replay checks] "- **UB2 (queue):** every accepted fix is processed exactly once, in time order, at a horizon ≥ its event time;" — `docs/h_backends_tag_input.md:67` — note: tier B (Replay) checks

### `UB3`

- [H backends UKF tier B Replay checks] "- **UB3 (anchor):**" — `docs/h_backends_tag_input.md:69` — note: tier B (Replay) checks

### `UB4`

- [H backends UKF tier B Replay checks] "- **UB4 (no gate):** every processed fix after the anchor is fused (processed = accepted)." — `docs/h_backends_tag_input.md:73` — note: tier B (Replay) checks

### `UB5`

- [H backends UKF tier B Replay checks] "- **UB5 (band, tag visible):** in "tag-visible" time, the horizontal difference must have p95 ≤ 0.02 m (σ_pos) and" — `docs/h_backends_tag_input.md:78` — note: tier B (Replay) checks

### `UB6`

- [H backends UKF tier B Replay checks] "- **UB6 (PREDICTION for S2, not an equivalence criterion; reported either way):** the Replay port's own drift" — `docs/h_backends_tag_input.md:86` — note: UB6 is a prediction, not an equivalence criterion

### `UR1`

- [H backends UKF regression check] "- **UR1:** with `AHRS_UKF_EXTPOS 0`, the port behaves as before on the D17 path. Two checks:" — `docs/h_backends_tag_input.md:134`
- [H backends UKF regression check] "| UKF regression UR1 (`AHRS_UKF_EXTPOS 0`) | PASS, byte-identical |" — `METHODOLOGY.md:11038` — note: result row restating the check

### `V0` — **CONFLICT: 2 meanings** (see flags §b)

- [FGO initial prior keys] "| `V(0)` | 0.1 m/s about zero | stationary pre-arm; confirm from the bag |" — `FGO_DESIGN.md:732` — note: written `V(0)` (initial velocity prior) in FGO_DESIGN.md; docs/fgo_cpp_port.md:59 writes "the X0/V0/B0 priors"
- [FGO initial prior keys] "`BatchFixedLagSmoother(0.25 s, LM max 2 iterations)`, `make_pim_params`, the X0/V0/B0 priors, the" — `docs/fgo_cpp_port.md:59` — note: usage spelled V0, referring to the FGO_DESIGN.md V(0) prior
- [UKF port input-path variants (step 3)] "| V0: none (step-2 stream) | 1.4e-6 / 9.8e-6 / 5.0e-5 m | 2.3e-5° | 10,050 / 10,246 / 96 |" — `METHODOLOGY.md:6196` — note: rows of "variant (the one input changed)" table, eval/ukf_step3.py

### `V1b`

- [M2-R runaway-probe validity checks] "- **Post-hoc validity V1b:** dataflash `XKF1` core 0 √(VN² + VE² + VD²) ≥ 0.2 m/s at the probe (± 0.5 s), and the" — `docs/handovers/2026-10-12_m2_full_bench.md:149`
- [M2-R runaway-probe validity checks] "- (d) validity of (c), post hoc (V1b): dataflash `XKF1` core 0 √(VN² + VE² + VD²) ≥ 0.2 m/s within ± 0.5 s of each" — `docs/handovers/2026-10-12_m2r_rerun.md:128` — note: restated for the M2-R re-run

### `V3e`

- [UKF port input-path variants (step 3)] "| **V3e: flow at EKF3's time (D5; arrival − 60 ms, about 45 ms BEFORE capture)** | **5.36 m** | **3.98°** |" — `METHODOLOGY.md:6451` — note: step 3 re-run variant (D5)

### `V5c`

- [UKF port input-path variants (step 3)] "| V5c DIAGNOSTIC: all ArduPilot inputs, flow at the offline UKF's capture time | **0.41 m** | **0.25°** |" — `METHODOLOGY.md:6454` — note: DIAGNOSTIC variant, step 3 re-run
- [UKF port input-path variants (step 3)] "- V5c's "correct time" was the capture time (the offline UKF's), not the mid-frame time." — `METHODOLOGY.md:6740` — note: later clarification (not a replacement): its "correct time" was the capture time, not the mid-frame time

### `V5e`

- [UKF port input-path variants (step 3)] "| **V5e: all ArduPilot inputs, flow at EKF3's time (port WITH D5)** | **5.06 m** | **3.81°** |" — `METHODOLOGY.md:6453` — note: step 3 re-run variant (D5)

### `VP` — **UNDEFINED** (see flags §a)

- [abbreviations] *(used, not defined here)* "heading** from the corridor vanishing point (LSD + RANSAC, per-frame confidence, "no measurement" near the end wall) and **yaw rate** from horizontal forward flow near the VP. Validated heading: textured walls 9/9, plain walls on blank/transition floors; fails plain walls over a checker floor. Yaw rate: textured walls ..." — `CLAUDE.md:157` — note: "VP" follows "vanishing point" but is never formally expanded

### `X1` — **CONFLICT: 2 meanings** (see flags §b)

- [m2 full-bench cross-checks] "- **In-flight tests:** no change expected. **New cross-check X1:** in every session, no watcher withdrawal whose" — `docs/handovers/2026-10-12_m2_full_bench.md:106` — note: conflicts with r1 scorer regression X1
- [m2 full-bench cross-checks] "`wbench4`, X1 "no yaw/vel withdrawal while the FC is armed" FAILED AS WORDED against the operator link's timing: 24 of" — `docs/real_flights_plan.md:748` — note: restated in §7.2 B13
- [r1 scorer regression checks] "- **X1:** cross-track with `XKF1` VE/VN given reproduces the stored `heading_share_restated.json` `xtrack_err_m` to" — `docs/handovers/2026-10-12_r1_scoring_items.md:57`

### `X2` — **CONFLICT: 2 meanings** (see flags §b)

- [m2 full-bench cross-checks] "- **X2:** every M1 reboot's origin verified on the first try (else the session aborts)." — `docs/handovers/2026-10-12_m2_full_bench.md:109` — note: conflicts with r1 scorer regression X2
- [r1 scorer regression checks] "- **X2:** the REGISTERED position rule equals the corridor's position-growth form (`ukf_shadow_replay_check.py`" — `docs/handovers/2026-10-12_r1_scoring_items.md:61`

## 4. Estimator, build, binary and branch labels


### `2d631fa7`

- [installed-binary md5 tags] "**The exact binary (recorded before P3):** `~/ardupilot_ukf/build/sitl/bin/arducopter`, md5 ... `2d631fa702ffdf77f50d996ff287abe4`." — `METHODOLOGY.md:7400`

### `4c07374b`

- [installed-binary md5 tags] "- **`fgo_cpp_node` `f642cd37…` → `4c07374b5c18ce1eda556d5bb9ad0768`**;" — `docs/handovers/2026-10-11_bandc_forced_install_safety.md:61`

### `43a2165a`

- [installed-binary md5 tags] "- **Flights:** `cl_a_tex_half` (EKF3, stock tree md5 `43a2165a…`) and `cl_ukf_a_tex_half` (UKF=1, port ... `1acfca00` md5 `fa440748…`)." — `METHODOLOGY.md:8016` — note: stock tree (EKF3) and UKF port 1acfca00 md5 fa440748

### `8677e30a`

- [installed-binary md5 tags] "- **attempt 2 built** (1 m 37 s for `waf copter`): `.apj` md5 `8677e30a…`, `git_identity 0156bfc3`, `board_id` 1048," — `docs/realflight_plan_copter.md:334`

### `28636bf9`

- [installed-binary md5 tags] "- **NOT installed:** `fgo_cpp_node` stays `f642cd37`; the scratch build is `28636bf9`." — `METHODOLOGY.md:13631`

### `1123742d`

- [installed-binary md5 tags] "- It installed nothing to `~/opt/fgo_cpp`. The installed node is still `1123742d…` (binit0, cap ungated)." — `docs/handovers/2026-10-09_fgo_yawcap_gate.md:12`

### `85179298`

- [installed-binary md5 tags] "- **The binary for V2–V4:** `arducopter` md5 `85179298b90fd07a59906613ccb6475b` (Replay md5" — `METHODOLOGY.md:7642`

### `(a)` — **CONFLICT: 2 meanings** (see flags §b)

- [closed-loop set letters] "- (a) EKF3 without heading, `corridor_textured_fwdc`, ×1 (reference)." — `METHODOLOGY.md:4841`
- [safety-test letters] "| | `H_safety_fgo_a_v2` (node killed; standard watcher) | `H_safety_fgo_b_v2` (node killed; watcher watches the node) |" — `METHODOLOGY.md:12309` — note: CONFLICT with closed-loop set (a): here (a) = node killed, standard watcher

### `(b)` — **CONFLICT: 2 meanings** (see flags §b)

- [closed-loop set letters] "- (b) EKF3 + live camera heading, `corridor_textured_fwdc`, ×3." — `METHODOLOGY.md:4842`
- [safety-test letters] "| | `H_safety_fgo_a_v2` (node killed; standard watcher) | `H_safety_fgo_b_v2` (node killed; watcher watches the node) |" — `METHODOLOGY.md:12309` — note: CONFLICT with closed-loop set (b): here (b) = watcher watches the node

### `_v2` — **CONFLICT: 5 meanings** (see flags §b)

- [D17 validation steps] "### D17 V2 (shadow run of the exact binary with heading, `ukf_shadow_hdg_v2`): PASS" — `METHODOLOGY.md:7664` — note: CONFLICT: _v2 in ukf_shadow_hdg_v2 = D17 validation step V2, not a build version
- [FGO build versions] "- `cl_fgo_a_tex_half_v2`: `FGO=1`, `corridor_textured_half_fwdc`, Python node (corrected core)." — `METHODOLOGY.md:12253` — note: CONFLICT: FGO _v2 = noise fix only (yaw cap ungated), a labelled ABLATION; UKF _v2 = the final jitter-corrected UKF
- [FGO build versions] "1. **The "FGO noise fix only (yaw cap ungated)" runs are KEPT as a labelled ABLATION.** What the yaw-cap gating alone" — `METHODOLOGY.md:12385` — note: CONFLICT: FGO _v2 = noise fix only (yaw cap ungated), a labelled ABLATION; UKF _v2 = the final jitter-corrected UKF
- [UKF build versions] "- **Caption:** Pass/fail of every closed-loop corridor set (replaces pack F15a), computed from the closed-loop score files, with the build ablations labelled: UKF v1 (pre-jitter fix) against v2 (final); FGO original, robust, v2 (noise fix only, ABLATION) and v3 (final, OLD priors)." — `docs/thesis/figures_thesis/index.md:237` — note: written "v2 (final)"; CONFLICT: FGO _v2 = noise fix only
- [UKF build versions] "4. **The UKF flights fly NOW,** with the jitter-corrected port: ... - S2 ×3 (`H_s2v2_r*`); ... - the half-speed corridor set (`cl_ukf_a_tex_half_v2`, `cl_ukf_b_tex_r{1,2,3}_half_v2`; the originals' settings);" — `METHODOLOGY.md:12497` — note: UKF _v2 = jitter-corrected port
- [UKF build versions] "*EKF3 = S1 near spawn (r1–r3) and S1 far spawn (r1, r2, r3b); the S1-far drifts are in METHODOLOGY only (no numbers.md row) and are not cross-checked. UKF = the jitter-corrected port (S2v2); FGO = the final C++ node (S3v2, flown with the OLD FGO priors).*" — `docs/thesis/tables/T5_H_tag_loss_drift.md:16` — note: written "UKF v2 port" in the T5 header; here "the jitter-corrected port (S2v2)"
- [re-flight version suffixes _v<N>] `_v2 (UKF re-flights)` "# UKF closed-loop RE-FLIGHTS with the jitter-corrected UKF port (ruling 2026-10-09), one per argument, under the flight lock." — `tools/run_ukf_refly.sh:2` — note: cl_ukf_*_half_v2, H_s2v2_r*, H_safety_ukf_{a,b}_v2: jitter-corrected UKF
- [re-flight version suffixes _v<N>] `_v2 (UKF re-flights)` "### UKF no-heading re-flight `cl_ukf_a_tex_half_v2` (jitter-corrected): PRIMARY PASS" — `METHODOLOGY.md:12539`
- [re-flight version suffixes _v<N>] `_v2 (H safety FGO)` "# sa sb H_safety_fgo_{a,b}_v2 (2 m-clearance hold W(-2.6,0); C++ FGO node 0.10 s time_ref)" — `tools/run_fgo_refly.sh:6`

### `_v3` — **CONFLICT: 5 meanings** (see flags §b)

- [D17 validation steps] "### D17 V3 (ground test, UKF active with heading, `ukf_groundtest_hdg_v3`): PASS" — `METHODOLOGY.md:7691` — note: CONFLICT: _v3 in ukf_groundtest_hdg_v3 = D17 validation step V3, not a build version
- [FGO build versions] "- **S3 and the FGO re-flights now fly this node:** `H_s3v2_r*`, `cl_fgo_*_v3`, `H_safety_fgo_*_v3`. The `*_v2` and" — `METHODOLOGY.md:12522` — note: FGO _v3 = final corrected FGO, node f642cd37; the H re-fly with the same node is named S3v2
- [FGO build versions] "*EKF3 = S1 near spawn (r1–r3) and S1 far spawn (r1, r2, r3b); the S1-far drifts are in METHODOLOGY only (no numbers.md row) and are not cross-checked. UKF = the jitter-corrected port (S2v2); FGO = the final C++ node (S3v2, flown with the OLD FGO priors).*" — `docs/thesis/tables/T5_H_tag_loss_drift.md:16` — note: written "FGO v3 node" in the T5 header; here "the final C++ node (S3v2)"
- [UKF build versions] "- **UKF safety re-tests** (installed port abb0357d; the short profiles unchanged; VERIFICATION):" — `METHODOLOGY.md:13633` — note: H_safety_ukf_*_v3 = installed port abb0357d; CONFLICT: FGO _v3 is a different build
- [re-flight version suffixes _v<N>] `_v3 (UKF safety re-tests)` "# sa3 sb3 H_safety_ukf_{a,b}_v3 (2d, 2026-10-11: as sa/sb, same port)" — `tools/run_ukf_refly.sh:8` — note: for the UKF, _v3 = same port re-test (2d); for the FGO, _v3 = noise fix + gated yaw cap: same suffix, different meanings
- [re-flight version suffixes _v<N>] `_v3 (FGO safety re-tests)` "### RESULT: FGO safety re-test (a), `H_safety_fgo_a_v3` (final FGO f642cd37; 2 m-clearance hold): ALL PASS" — `METHODOLOGY.md:12656`

### `_v4`

- [FGO build versions] "- **FGO safety re-tests on the corrected node** (VERIFICATION, short profiles):" — `METHODOLOGY.md:13689` — note: v4 = node 4c07374b, NEW (D18) initial priors
- [FGO build versions] "## 5. FGO SITL safety re-tests v4 (short verification flights, `tools/run_fgo_refly.sh sa4 sb4`): ALL PASS" — `docs/handovers/2026-10-11_bandc_forced_install_safety.md:73` — note: v4 = node 4c07374b, NEW (D18) initial priors
- [FGO build versions] "- **Caption:** Experiment H sets (S1, S1 far, S2/S2v2, S3/S3v2) with hold error, drift, lockouts and the P-H5 bands, and every safety-test run with its as-worded verdict, including the v3 (UKF) and v4 (FGO, NEW priors) re-tests (replaces pack F15b)." — `docs/thesis/figures_thesis/index.md:254` — note: written "v4 (FGO, NEW priors)"
- [re-flight version suffixes _v<N>] "# sa4 sb4 H_safety_fgo_{a,b}_v4 (2d, 2026-10-11: as sa/sb, D18-corrected node)" — `tools/run_fgo_refly.sh:7`

### `abb0357d`

- [installed-binary md5 tags] "*jitter-corrected UKF* = the re-flown half-speed set `cl_ukf_*_tex*_half_v2` (port `abb0357d`; ruling 2026-10-09: the full-speed set stays as recorded with the old model, labelled). FGO: *original FGO* = `cl_fgo_*_half` (pre-correction); ***FGO noise fix only (yaw cap ungated)*** = `cl_fgo_*_half_v2`, kept as the ..." — `docs/thesis/numbers.md:458` — note: port commit, not an md5

### `AHRS_EKF_TYPE 3`

- [AHRS_EKF_TYPE values] "`EKFType::SIM` — the simulator's own perfect state. EKF3 is `3`." — `CLAUDE.md:759`
- [AHRS_EKF_TYPE values] "- **Plus `AHRS_EKF_TYPE 3`** (`closedloop.parm`, appended via `EXTRA_PARM_FILES`, and enforced" — `METHODOLOGY.md:3935` — note: closed loop: EKF3 flies

### `AHRS_EKF_TYPE 10`

- [AHRS_EKF_TYPE values] "selects which estimator ArduPilot *reports* as the vehicle's position. `10` is" — `CLAUDE.md:758`
- [AHRS_EKF_TYPE values] "**CORRECTION 1: where `AHRS_EKF_TYPE=10` comes from.** ... - The Hidden Configuration Audit put it down to eeprom. It is (also) **injected as a ... default by SITL**: `SIM_JSON.cpp:410-413` calls" — `METHODOLOGY.md:3114` — note: source: injected by SITL when no_time_sync
- [AHRS_EKF_TYPE values] "- `SIM_JSON.cpp:406-414`: when the JSON peer reports `no_time_sync`, SITL prints `Forcing use_time_sync=0` and calls `AP_Param::set_default_by_name("AHRS_EKF_TYPE", 10)`. The source comment reads: *"if not using time sync then default EKF type to 10, as otherwise EKF is likely to diverge"*." — `docs/partC_onboard_feasibility.md:381`

### `AHRS_EKF_TYPE 11`

- [AHRS_EKF_TYPE values] "- **Docs.** `AHRS_EKF_TYPE=11`, `EAHRS_TYPE` selects the device (https://ardupilot.org/copter/docs/common-external-ahrs.html)." — `docs/partC_onboard_feasibility.md:262` — note: stock External AHRS; not used in this project

### `AHRS_EKF_TYPE 12`

- [AHRS_EKF_TYPE values] "- The thesis UKF as the **active** estimator, `AHRS_EKF_TYPE = 12`: the new `AP_AHRS_UKF` backend" — `METHODOLOGY.md:6838`

### `AHRS_EKF_TYPE 13`

- [AHRS_EKF_TYPE values] "- Port tree with the FGO backend (`EKFType::FGO` 13, `AP_NavFGO`), plus the FGO node in the trial" — `METHODOLOGY.md:8031`
- [AHRS_EKF_TYPE values] "| A1 | `EKFType::FGO` (13), `AP_AHRS_FGO` backend, generated switch arms, `AHRS_EKF_TYPE 13` | 0.5 day |" — `docs/d12_fgo_backend_report.md:60`

### `AHRS_EKF_TYPE values`

- [AHRS_EKF_TYPE values] "- **The parameter.** `AHRS_EKF_TYPE` (`AP_AHRS.cpp:171-176`, `@Values: 0,2,3,10,11`, default `HAL_AHRS_EKF_TYPE_DEFAULT 3`, line 56-57)." — `docs/partC_onboard_feasibility.md:222` — note: stock values 0,2,3,10,11; 12/13 are the project fork values

### `arm64 build`

- [board firmware and arm64] "# Item 2f: the C++ FGO on ARM64, cross-built and emulated (2026-10-11)" — `docs/handovers/2026-10-11_fgo_arm64.md:1`
- [board firmware and arm64] "- **Under qemu-user the arm64 replay matches the x86 scratch build of 2d** (replay `0981e455`, node `28636bf9`):" — `docs/handovers/2026-10-11_fgo_arm64.md:13`
- [board firmware and arm64] "| G8 | C++ FGO on the real Pi: GTSAM 4.2.1 + Boost on arm64 (native or cross build), ROS 2 Jazzy arm64, keyframe CPU budget (33 ms), memory, core pinning and RT priority, **live solve-time self-stop** (stage 3 requirement: p99 > keyframe period for 2 s → node stops → backend invalid → LAND) | exists but untested on ..." — `docs/real_flight_readiness.md:132`

### `ATE` — **UNDEFINED** (see flags §a)

- [ATE metrics] *(used, not defined here)* "An ATE number is meaningless without its alignment and windowing. **Always label" — `METHODOLOGY.md:9` — note: acronym not expanded; the metric variants are what the STANDING RULE defines
- [abbreviations] *(used, not defined here)* "| Evaluation | `evo` for ATE / RPE, venv at `~/venv-evo`, wrapped by `evaluate_trial.sh` |" — `CLAUDE.md:25` — note: acronym never expanded

### `batch`

- [FGO solver (BatchFixedLagSmoother)] "**Solver + timing (reported honestly).** The primary solver is `BatchFixedLagSmoother`" — `METHODOLOGY.md:715` — note: CONFLICT: here "batch" = BatchFixedLagSmoother, the live FGO solver, not the whole-flight hindsight batch
- [FGO solver (BatchFixedLagSmoother)] "implementation artefact is not yet root-caused; batch is the robust path meanwhile." — `METHODOLOGY.md:1139` — note: "batch" vs iSAM2 incremental

### `binit0` — **UNDEFINED** (see flags §a)

- [closed-loop sets and build suffixes] *(used, not defined here)* "- It installed nothing to `~/opt/fgo_cpp`. The installed node is still `1123742d…` (binit0, cap ungated)." — `docs/handovers/2026-10-09_fgo_yawcap_gate.md:12` — note: used for the noise-fix-only node; the handover 2026-10-09_fgo_binit0_equivalence.md is titled setBiasAccOmegaInit -> 0

### `board-h743`

- [board firmware and arm64] "**The fork change** is `~/ardupilot_ukf` branch `board-h743`: commits `6280a35745` (the option, the guards and the stack" — `docs/board_firmware_plan.md:20`
- [branches] "**The fork change** is `~/ardupilot_ukf` branch `board-h743`: commits `6280a35745` (the option, the guards and the stack ... fix) and `0156bfc34e` (the forced-arm refusal). It is based on `rung1-geometry` `16535f9a29`. It is NOT merged, and the checked-out branch and the installed SITL binaries are untouched." — `docs/board_firmware_plan.md:20` — note: ~/ardupilot_ukf branch
- [branches] "### 2a: board firmware BUILT for two representative H743 boards (`~/ardupilot_ukf` `board-h743` `0156bfc34e`, NOT merged; nothing flashed; `docs/board_firmware_plan.md`; handover `docs/handovers/2026-10-11_board_firmware_h743.md`)" — `METHODOLOGY.md:13558`

### `Build A`

- [real-flight FGO build options] "| **A. C++ port, numerical Jacobians** (the same central differences as `factors.py`) | language only | 4–6 | 3–4× faster than Python: ~10–20 ms | Run the C++ node and the Python node on the **same recorded bags**: identical inputs, same keyframes, same factors. Require per-keyframe state differences below solver ..." — `docs/real_flights_plan.md:865`
- [real-flight FGO build options] *(superseded)* "**Recommendation (superseded by the update above): B, with A as the stepping stone.**" — `docs/real_flights_plan.md:876`

### `Build B`

- [real-flight FGO build options] "| **B. C++ port with exact Jacobians** (hand-derived, or generated with **SymForce** from the same `h_flow`/`h_range`/`h_heading`/`h_tag` models) | language + Jacobians | 6–9 (SymForce codegen + verification) | 5–15× faster than Python (Part C §5.4): ~3–8 ms | (1) **Unit level:** generated Jacobians against numerical ..." — `docs/real_flights_plan.md:866`
- [real-flight FGO build options] *(superseded)* "**UPDATE (ruling 2026-10-08): option A built and accepted; SymForce (B) DROPPED.**" — `docs/real_flights_plan.md:869`

### `C++ heading port`

- [ports and nodes] "### C++ port of the heading node's per-frame computation — equivalence bands PRE-REGISTERED (2026-09-29, before any C++ is run)" — `METHODOLOGY.md:5883`

### `C++ node`

- [ports and nodes] "- **D2:** switch to the **C++ heading node for all subsequent closed-loop flights**." — `METHODOLOGY.md:6371`

### `cap-free RTS-UKF`

- [hindsight tracks (F2, T, O)] "- **The asymmetry:** the RTS-UKF smoothed a forward pass that kept the live-anchored pseudo-yaw. That is the same ... circularity removed from the FGO batch before the O flights (`batch_drop_yawcap`). The RTS was therefore re-run on ... a forward pass with the pseudo-yaw OFF after alignment (`room_ukf_replay.py ..." — `METHODOLOGY.md:10439` — note: cap-free RTS re-run without the live-anchored pseudo-yaw

### `cl_a`

- [closed-loop sets and build suffixes] "### Closed-loop set (a), `cl_a_tex` (EKF3 without heading, `corridor_textured_fwdc`, ×1): PRIMARY PASS" — `METHODOLOGY.md:5974`

### `cl_b`

- [closed-loop sets and build suffixes] "### Closed-loop set (a), `cl_a_tex` (EKF3 without heading, `corridor_textured_fwdc`, ×1): PRIMARY PASS" — `METHODOLOGY.md:5974`

### `cl_bcpp`

- [closed-loop sets and build suffixes] "### Set (b) RE-FLOWN with the C++ heading node (ruling D2): PASSES, 3/3 flights pass B1–B5" — `METHODOLOGY.md:6527`
- [closed-loop sets and build suffixes] "Settings: `VISO_DELAY_MS 38`, `every_n` 4, `impl: cpp`, otherwise as the Python-node set (b)." — `METHODOLOGY.md:6529` — note: cl_bcpp_tex_r1..r3 = set (b) with impl: cpp

### `D17 V1`

- [D17 validation steps] "**V1 — Replay check on set (b)'s logs** (`cl_bcpp_tex_r1..r3`, `LOG_REPLAY 1`, EKF3 flew with the C++" — `METHODOLOGY.md:7594`

### `D25 node`

- [ports and nodes] "- Node = `fgo_node.py` with the D25 fix." — `METHODOLOGY.md:9160`

### `e82c050b`

- [installed-binary md5 tags] "- Today: `ukf-jitter-fix` = `replay-rukx` `f30f6ffa2f` (= `xuko-fmt` `0a214d29d3` + the U10 rule-2 rename). It was ... installed on 2026-10-12 as Replay `3c3b62bbe51d515b6ff0789a19fe1136`, replacing `e82c050b…` [V]. UKF_Equiv is" — `docs/u10_replay_gate_band.md:124`

### `ea486dea`

- [installed-binary md5 tags] "`eval/results/expH/ukf_tag_tierB_H_s1_r1.json`; Replay binary md5 `ea486dea…` (`ukf-port-tag`)." — `docs/h_backends_tag_input.md:299`

### `EKF` — **UNDEFINED** (see flags §a)

- [estimators] *(used, not defined here)* "Master's thesis comparing **EKF**, **UKF**, and **online Factor Graph Optimisation (FGO)**" — `CLAUDE.md:5` — note: acronym never expanded in the docs

### `EKF3`

- [estimators] "**ArduPilot EKF3 is the fixed baseline.** It is set up exactly as" — `CLAUDE.md:969`
- [estimators] "`EKFType::SIM` — the simulator's own perfect state. EKF3 is `3`." — `CLAUDE.md:759` — note: EKF3 = AHRS_EKF_TYPE 3

### `EKFType::FGO`

- [AHRS_EKF_TYPE values] "- ArduPilot: `EKFType::FGO` 13, `AP_NavFGO` output predictor, `AP_AHRS_FGO`, 52 switch arms, its own" — `PROGRESS.md:49`

### `EKFType::UKF`

- [AHRS_EKF_TYPE values] "- **(i)** an `AP_AHRS` backend (`EKFType::UKF`, modelled on `AP_AHRS_External`: 220 lines) and **52" — `METHODOLOGY.md:6796`

### `emulate-gemv`

- [ports and nodes] "The CMake option `-DFGO_CPP_EMULATE_NUMPY_GEMV=ON` (default OFF) is a **diagnostic** (see below)." — `docs/fgo_cpp_port.md:73`
- [ports and nodes] "With `FGO_CPP_EMULATE_NUMPY_GEMV=ON`, the C++ does that one product with the same FMA order, and" — `docs/fgo_cpp_port.md:103`

### `ENU`

- [abbreviations] "- **Position** (NED → ENU) — purely definitional axis relabelling, no ... ambiguity: `enu.x = ned.y` (East), `enu.y = ned.x` (North), ... `enu.z = -ned.z` (Up = −Down)." — `CLAUDE.md:376`

### `ExtNav` — **UNDEFINED** (see flags §a)

- [abbreviations] *(used, not defined here)* "- **(a) ExtNav works today**, but what flies is EKF3 re-filtering the FGO output:" — `METHODOLOGY.md:3094` — note: EKF3 external-navigation source; never expanded

### `f642cd37`

- [installed-binary md5 tags] "- **Installed:** `~/opt/fgo_cpp/bin/fgo_cpp_node` md5 **`f642cd37…`** (was `1123742d…`, noise fix only)." — `METHODOLOGY.md:12518`

### `fa440748`

- [installed-binary md5 tags] "`eval/results/fgo_gate_fgo_shadow_half_a.json`. The binary had md5 `fa440748…`. The node ran 10,262" — `METHODOLOGY.md:8560`

### `FGO`

- [estimators] "Master's thesis comparing **EKF**, **UKF**, and **online Factor Graph Optimisation (FGO)**" — `CLAUDE.md:5` — note: only expansion found: online Factor Graph Optimisation
- [estimators] "12. FGO (GTSAM) implementation — **built and producing numbers** (`src/estimators/fgo/`, `BatchFixedLagSmoother`, window 0.25 s (a declared config choice), LM capped at 2 iterations, shared `h_flow`, custom flow/range/yaw-prior factors, IMU dejitter and gap rule, Phase 4 forward heading/yaw-rate factors; runs in ..." — `CLAUDE.md:1874`

### `FGO batch`

- [hindsight tracks (F2, T, O)] "- **a batch FGO, separately labelled:** one Levenberg–Marquardt optimisation over ALL of the live ... FGO's factors for the flight (identical factors, including the masked heading set), initialised" — `METHODOLOGY.md:7933` — note: F2: one LM over all live FGO factors
- [hindsight tracks (F2, T, O)] "- "FGO hindsight (whole-flight batch)": one LM (≤ 50 iterations) over every factor the live FGO received from the" — `METHODOLOGY.md:10144` — note: T/O: same thing labelled FGO hindsight; LM <= 50 iterations from the re-anchor on

### `FGO C++ port`

- [ports and nodes] "Supervisor ruling 2026-10-08: start the FGO C++ port as coding work and prove equivalence to the ... thesis FGO on recorded bags before any further step. Option A of `docs/real_flights_plan.md` §9.3:" — `docs/fgo_cpp_port.md:3` — note: option A: numerical Jacobians
- [ports and nodes] "| **A. C++ port, numerical Jacobians** (the same central differences as `factors.py`) | language only | 4–6 | 3–4× faster than Python: ~10–20 ms | Run the C++ node and the Python node on the **same recorded bags**: identical inputs, same keyframes, same factors. Require per-keyframe state differences below solver ..." — `docs/real_flights_plan.md:865` — note: options A/B/C of real_flights_plan section 9.3

### `FGO hindsight`

- [hindsight tracks (F2, T, O)] "- "FGO hindsight (whole-flight batch)": one LM (≤ 50 iterations) over every factor the live FGO received from the" — `METHODOLOGY.md:10144`

### `FGO live`

- [hindsight tracks (F2, T, O)] "- the live FGO (0.25 s window, masked);" — `METHODOLOGY.md:7932` — note: F2 definition: 0.25 s window

### `FGO noise fix only (yaw cap ungated)`

- [closed-loop build labels] `FGO noise fix only (yaw cap ungated)` "**Builds flown (labels used below).** UKF: *old UKF (jitter)* = the original port (`cl_ukf_*`, full and half speed); *jitter-corrected UKF* = the re-flown half-speed set `cl_ukf_*_tex*_half_v2` (port `abb0357d`; ruling 2026-10-09: the full-speed set stays as recorded with the old model, labelled). FGO: *original FGO* ..." — `docs/thesis/numbers.md:458` — note: PRIMARY definition of the closed-loop build labels (numbers.md section 15)

### `fgo_cpp` — **UNDEFINED** (see flags §a)

- [ports and nodes] *(used, not defined here)* "| G6 | C++ FGO node on x86 (GTSAM 4.2.1, ROS 2 / MAVLink adapter, time_ref stamping, reorder delay 0.20 s) | exists and tested in SITL | b | `src/estimators/fgo_cpp/`. Equivalence bands A/B/C/L passed; flew S3/S3v2 and the FGO safety re-tests (node `f642cd37`). Accepted for the **aided regime only** (plan §9.3 ..." — `docs/real_flight_readiness.md:130` — note: used as the directory name of the C++ FGO; the token itself is not defined

### `fgo_cpp_node`

- [ports and nodes] "- the ROS 2 node `fgo_cpp_node` (subscriptions as `fgo_node.py`, with a worker thread so callbacks never" — `docs/fgo_cpp_port.md:384`
- [ports and nodes] "`run_trial.sh` gains `FGO_NODE_IMPL=cpp` (with `FGO_NODE=1`). It runs `fgo_cpp_node` in place of `fgo_node.py`:" — `docs/fgo_cpp_port.md:518`

### `fgo_node.py`

- [ports and nodes] "| `src/estimators/fgo/fgo_node.py` | the ROS2 node |" — `FGO_DESIGN.md:982`

### `fgo_shadow`

- [shadow runs] "### FGO shadow run (a) `fgo_shadow_half_a` (no heading, simulator truth, half speed): FG1, FG2, FG3b PASS; **FG3 FAILS on position and velocity maxima**. STOPPED; queued as D23" — `METHODOLOGY.md:8558` — note: fgo_shadow_half_a: no heading, simulator truth, half speed
- [shadow runs] *(used, not defined here)* "EXTRA_PARM_FILES=$HOME/thesis_ws/fgo_shadow.parm EXPECT_OVERRIDE=AHRS_FGO_ENABLE=1,SERIAL3_PROTOCOL=2 \" — `docs/handovers/2026-10-08_fgo_cpp_stage5_sitl_flights.md:73` — note: fgo_shadow.parm parameter file

### `final FGO`

- [closed-loop build labels] "**Builds flown (labels used below).** UKF: *old UKF (jitter)* = the original port (`cl_ukf_*`, full and half speed); *jitter-corrected UKF* = the re-flown half-speed set `cl_ukf_*_tex*_half_v2` (port `abb0357d`; ruling 2026-10-09: the full-speed set stays as recorded with the old model, labelled). FGO: *original FGO* ..." — `docs/thesis/numbers.md:458` — note: PRIMARY definition of the closed-loop build labels (numbers.md section 15)

### `FLU` — **UNDEFINED** (see flags §a)

- [abbreviations] *(used, not defined here)* "**Frame transform** (ArduPilot NED/FRD → Gazebo/ROS ENU/FLU), reported and" — `CLAUDE.md:373` — note: not expanded; q_frd2flu described as 180 deg about body X (forward), CLAUDE.md:384

### `FRD` — **UNDEFINED** (see flags §a)

- [abbreviations] *(used, not defined here)* "**Frame transform** (ArduPilot NED/FRD → Gazebo/ROS ENU/FLU), reported and" — `CLAUDE.md:373` — note: not expanded; q_frd2flu described as 180 deg about body X (forward), CLAUDE.md:384

### `fwd-camera`

- [branches] "has no common ancestor with `master`, and it is left alone. Workstreams branch from ... `master` (e.g. `fwd-camera`)." — `CLAUDE.md:1838` — note: thesis_ws; origin/fwd-camera is its remote
- [branches] "## Forward-camera workstream (branch `fwd-camera`) — hypothesis, sensor, worlds, Phase 1 pre-registration (2026-09-24)" — `METHODOLOGY.md:1316`
- [branches] "Branch `fwd-camera`, from `master` at `5b14ce3`. **Phase 0 (a), the reproducibility" — `PROGRESS.md:445`

### `H743 board firmware`

- [board firmware and arm64] "# Board firmware (rung 3): build, budget, flashing and rollback for a 2 MB STM32H743" — `docs/board_firmware_plan.md:1`
- [board firmware and arm64] "**Rung 1 does NOT fly this firmware.** Rung 1 flies `7bac20cbcc` built UNMODIFIED (ruling item 1), with" — `docs/board_firmware_plan.md:12`

### `HAGL` — **UNDEFINED** (see flags §a)

- [abbreviations] *(used, not defined here)* "- **Fusion is active, not rejected**: 251/251 airborne (`HAGL`>1.0 m) `XKF5`" — `CLAUDE.md:324` — note: dataflash field; METHODOLOGY:3562 says the logged XKF5.HAGL equals body-origin height
- [abbreviations] *(used, not defined here)* "- **The logged `XKF5.HAGL` equals the body-origin height, not the lidar range:**" — `METHODOLOGY.md:3562`

### `hard gate`

- [estimator variants] "(ii) wrong headings effectively accepted: hard gate = passed the gate; robust = weight ≥ 0.5" — `METHODOLOGY.md:7916` — note: hard gate vs robust weighting

### `heading node`

- [ports and nodes] "- `heading_bridge.py` (ROS 2 node);" — `METHODOLOGY.md:4721` — note: heading node = heading_bridge.py; a C++ version from ruling D2

### `hindsight` — **CONFLICT: 3 meanings** (see flags §b)

- [L keyframe-FGO tracks] "**Hindsight** = every keyframe after a final LM polish" — `METHODOLOGY.md:10476` — note: L: final LM polish <= 20 iterations (pre-registered)
- [L keyframe-FGO tracks] *(superseded)* "- **Hindsight solve:** iSAM2's full-graph estimate after 5 extra relinearising updates, instead of the" — `METHODOLOGY.md:10557` — note: L deviation: iSAM2 full-graph estimate replaced the pre-registered LM polish
- [figure line-style convention] "Conventions: one fixed colour and marker per estimator; solid lines and filled marks = live, dashed lines and open marks = hindsight; linear" — `docs/thesis/figures_thesis/thesis_figures_combined.pdf p.1`
- [hindsight tracks (F2, T, O)] "- **hindsight:** the full-trajectory estimate after the flight (the batch FGO; for the UKF and live" — `METHODOLOGY.md:7938` — note: F2: for UKF and live FGO hindsight = live
- [hindsight tracks (F2, T, O)] "Hindsight here = the FGO whole-flight batch and the single-pass RTS smoother; L's keyframe-FGO hindsight (iSAM2 full estimate) is a different estimator and is not in this table.*" — `docs/thesis/tables/T8_hindsight_ratio.md:17` — note: T8 says L's keyframe-FGO hindsight is a different estimator

### `impl: cpp`

- [ports and nodes] "Settings: `VISO_DELAY_MS 38`, `every_n` 4, `impl: cpp`, otherwise as the Python-node set (b)." — `METHODOLOGY.md:6529`

### `iSAM2`

- [abbreviations] "incremental (iSAM2) solver is 0.2 ms/step (well under budget) but **cascades after" — `METHODOLOGY.md:1134`

### `jitter-corrected UKF`

- [closed-loop build labels] "**Builds flown (labels used below).** UKF: *old UKF (jitter)* = the original port (`cl_ukf_*`, full and half speed); *jitter-corrected UKF* = the re-flown half-speed set `cl_ukf_*_tex*_half_v2` (port `abb0357d`; ruling 2026-10-09: the full-speed set stays as recorded with the old model, labelled). FGO: *original FGO* ..." — `docs/thesis/numbers.md:458` — note: PRIMARY definition of the closed-loop build labels (numbers.md section 15)

### `keyframe FGO`

- [estimator variants] "**Estimator, labelled "keyframe FGO (loop closure)"** (`src/estimators/fgo/lc_fgo_replay.py`), separate from the thesis" — `METHODOLOGY.md:10461`
- [estimator variants] "prior), and start a **retained-history graph solved by plain iSAM2** (QR, no marginalisation, defaults otherwise)." — `METHODOLOGY.md:10465`

### `live` — **CONFLICT: 3 meanings** (see flags §b)

- [L keyframe-FGO tracks] "- **Live** = the newest keyframe after each iSAM2 update. **Hindsight** = every keyframe after a final LM polish" — `METHODOLOGY.md:10476` — note: L definition (keyframe FGO): newest keyframe after each iSAM2 update; differs from F2/T
- [figure line-style convention] "Conventions: one fixed colour and marker per estimator; solid lines and filled marks = live, dashed lines and open marks = hindsight; linear" — `docs/thesis/figures_thesis/thesis_figures_combined.pdf p.1`
- [hindsight tracks (F2, T, O)] "- **live:** the current (filtered) estimate at each time, for the UKF and the live FGO;" — `METHODOLOGY.md:7937` — note: F2 definition

### `LM`

- [abbreviations] "one Levenberg–Marquardt optimisation over ALL of the live" — `METHODOLOGY.md:7933`

### `LSD` — **UNDEFINED** (see flags §a)

- [abbreviations] *(used, not defined here)* "heading** from the corridor vanishing point (LSD + RANSAC, per-frame confidence, "no measurement" near the end wall) and **yaw rate** from horizontal forward flow near the VP. Validated heading: textured walls 9/9, plain walls on blank/transition floors; fails plain walls over a checker floor. Yaw rate: textured walls ..." — `CLAUDE.md:157` — note: never expanded

### `main`

- [branches] "`main` is an unrelated root commit that GitHub auto-created (a one-line README). It ... has no common ancestor with `master`, and it is left alone. Workstreams branch from" — `CLAUDE.md:1837` — note: thesis_ws; origin/main (and origin/HEAD) is its remote

### `master`

- [branches] "- **Branches:** `master` is the working branch, and all project history is on it." — `CLAUDE.md:1836` — note: thesis_ws branch; origin/master is its remote
- [branches] `master (~/ardupilot_ukf)` *(used, not defined here)* "ad28bb78d2ef9cb5dae20b6366fdbed7b9ca0083" — `~/ardupilot_ukf/.git/refs/heads/master:1` — note: a local branch of the fork ~/ardupilot_ukf (distinct from thesis_ws master, CLAUDE.md:1836); no project doc names it; quote is the ref SHA. The fork also carries ~100 upstream origin/* release ...

### `NED`

- [abbreviations] "- **Position** (NED → ENU) — purely definitional axis relabelling, no ... ambiguity: `enu.x = ned.y` (East), `enu.y = ned.x` (North), ... `enu.z = -ned.z` (Up = −Down)." — `CLAUDE.md:376`

### `NEW priors`

- [FGO initial priors] "- **INSTALLED:** `fgo_cpp_node` `f642cd37` → **`4c07374b`** (initial yaw 1°, roll/pitch 5°). Backup in" — `METHODOLOGY.md:13686` — note: NEW = initial yaw 1 deg, roll/pitch 5 deg (D18)

### `OF`

- [abbreviations] *(used, not defined here)* "| A7 | flow = EKF3's flow input: `OF` vs `ROFH` (counts; flowX/Y, bodyX/Y float32-identical; Qual) | exact |" — `docs/rung1_preregistration.md:353` — note: dataflash OF message (flow), not expanded
- [abbreviations] *(used, not defined here)* "| 2 | Bench cards B1–B8 (props off): flow orientation (`OF.body*` against `flow*` signs), rangefinder on the ground and lifted, `RNGFND1_GNDCLR`, compass health (nomag), log completeness (`DSF`), fence. A disarmed bench log with sync wiggles, run through the whole offline pipeline (Replay, converter, `mocap_align`, ..." — `docs/realflight_plan_copter.md:122`
- [log messages] "// @LoggerMessage: OF ... // @Description: Optical flow sensor data" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:856`
- [log messages] "- **Method.** The OF log records exactly the (raw flow, body rate) pair that EKF3 fuses. So" — `METHODOLOGY.md:4208`

### `offline UKF` — **UNDEFINED** (see flags §a)

- [estimator variants] *(used, not defined here)* "- The UKF port (`AP_NavUKF.cpp:437`, `RNG_MIN` 0.05, `RNG_MAX` 40), the offline UKF (`ukf_core.update_range`)," — `METHODOLOGY.md:8860` — note: usage distinguishing port and offline UKF

### `OLD priors`

- [FGO initial priors] "set, the FGO safety tests) and the installed C++ binary used the OLD priors (1e-3 rad yaw, 2° roll/pitch)." — `docs/thesis/numbers.md:37`

### `old UKF (jitter)`

- [closed-loop build labels] `old UKF (jitter)` "**Builds flown (labels used below).** UKF: *old UKF (jitter)* = the original port (`cl_ukf_*`, full and half speed); *jitter-corrected UKF* = the re-flown half-speed set `cl_ukf_*_tex*_half_v2` (port `abb0357d`; ruling 2026-10-09: the full-speed set stays as recorded with the old model, labelled). FGO: *original FGO* ..." — `docs/thesis/numbers.md:458` — note: PRIMARY definition of the closed-loop build labels (numbers.md section 15)

### `original FGO`

- [closed-loop build labels] "**Builds flown (labels used below).** UKF: *old UKF (jitter)* = the original port (`cl_ukf_*`, full and half speed); *jitter-corrected UKF* = the re-flown half-speed set `cl_ukf_*_tex*_half_v2` (port `abb0357d`; ruling 2026-10-09: the full-speed set stays as recorded with the old model, labelled). FGO: *original FGO* ..." — `docs/thesis/numbers.md:458` — note: PRIMARY definition of the closed-loop build labels (numbers.md section 15)

### `Python node` — **UNDEFINED** (see flags §a)

- [ports and nodes] *(used, not defined here)* "- The Python-node set (b) stays recorded as the **first result**. Set (a) (no camera) stands." — `METHODOLOGY.md:6376` — note: no defining text

### `replay-rukx`

- [branches] "- new branch `replay-rukx` = `0a214d29d3` + `f30f6ffa2f`;" — `docs/handovers/2026-10-12_u10_final.md:13` — note: ~/ardupilot_ukf branch
- [branches] "- **Port:** `replay-rukx` (`f30f6ffa2f`); `ukf-jitter-fix` fast-forwarded." — `METHODOLOGY.md:14023`

### `robust FGO`

- [estimator variants] "- **the FGO robust arm:** the same heading measurements and σ, with the χ² gate REMOVED and the ... heading factor's noise model made robust (`gtsam.noiseModel.Robust`)." — `METHODOLOGY.md:7903`
- [estimator variants] "- `cl_fgo_b_robust_tex_r1..r3_half`, exactly as `cl_fgo_b_tex_*_half` except the parameter." — `METHODOLOGY.md:9760` — note: closed-loop robust-FGO set (plan step 2(b))

### `RPE` — **UNDEFINED** (see flags §a)

- [abbreviations] *(used, not defined here)* "| Evaluation | `evo` for ATE / RPE, venv at `~/venv-evo`, wrapped by `evaluate_trial.sh` |" — `CLAUDE.md:25` — note: acronym never expanded

### `RTS` — **UNDEFINED** (see flags §a)

- [estimator variants] *(used, not defined here)* "- **S1-far UKF without RTS:** reproduced byte-identically with `--no-rts`, and the stored directory has no" — `docs/handovers/2026-10-09_final_rerun_repro.md:67` — note: acronym never expanded in the docs

### `RTS-UKF`

- [hindsight tracks (F2, T, O)] "- "RTS-UKF (hindsight)": the unscented RTS smoother over the UKF's predict nodes from the re-anchor on. A filter" — `METHODOLOGY.md:10146`
- [hindsight tracks (F2, T, O)] "- It is the single-pass unscented RTS, which linearises about the filter's estimates once and never relinearises. With" — `METHODOLOGY.md:10267`

### `rung1-geometry`

- [branches] "### Rung-1 UKF port: geometry from the log, and the D18 derotation rule (`~/ardupilot_ukf` `rung1-geometry` `16535f9a29`, NOT merged or installed; handover `docs/handovers/2026-10-11_r1_ukf_port.md`)" — `METHODOLOGY.md:13476` — note: ~/ardupilot_ukf branch

### `scratch build`

- [ports and nodes] "- These md5s differ from the scratch build's because of the build and install paths (RPATH, `__FILE__`)." — `docs/handovers/2026-10-11_bandc_forced_install_safety.md:63` — note: installed md5 differs from the scratch build by build/install paths only

### `shadow` — **CONFLICT: 3 meanings** (see flags §b)

- [shadow = EKF3 flies, estimator passive] "- Launcher: `UKF=shadow` (EKF3 flies, the UKF in shadow); `UKF=1|shadow` with `HEADING=1` adds" — `METHODOLOGY.md:7644` — note: shadow = EKF3 flies, the UKF runs passively
- [shadow = EKF3 flies, estimator passive] "**Shadow (stage S1):** with EKF3 flying, the UKF and FGO run as live shadows (the existing shadow paths), and offline" — `docs/tag_hold_design.md:121` — note: H experiment: EKF3 flies; UKF and FGO live shadows
- [shadow = a non-active estimator runs and logs] "| 2 | One build (per vehicle) with `AHRS_EKF_TYPE` selection and shadow running; FGO off-board routes | UKF: yes. EKF3 already runs and logs while not active: `dsn_tex_r1` has `AHRS_EKF_TYPE=10` and 6654 `XKF1` rows from 2 lanes. FGO: (a) the **ExtNav route exists today** (EKF3 flies, fusing FGO `ODOMETRY`); (b) **no ..." — `docs/partC_onboard_feasibility.md:28` — note: EKF3 runs and logs while not active (dsn_tex_r1 flew on SIM)
- [shadow = simulator truth flies, estimator passive] "**Shadow runs (simulator truth flies, `AHRS_EKF_TYPE 10`, 300 s cruise):**" — `METHODOLOGY.md:8070` — note: CONFLICT with the EKF3-flies meaning; METHODOLOGY 11105 records it as a deviation

### `SITL` — **UNDEFINED** (see flags §a)

- [abbreviations] *(used, not defined here)* "| Autopilot | ArduPilot SITL (ArduCopter), venv at `~/venv-ardupilot` |" — `CLAUDE.md:20`

### `stock tree` — **UNDEFINED** (see flags §a)

- [ports and nodes] *(used, not defined here)* "- **Flights:** `cl_a_tex_half` (EKF3, stock tree md5 `43a2165a…`) and `cl_ukf_a_tex_half` (UKF=1, port" — `METHODOLOGY.md:8016` — note: no defining text

### `the fork`

- [ports and nodes] "- **The fork** (`~/ardupilot_ukf`, branch `ukf-jitter-fix`, `abb0357d`, based on `7bac20cbcc`) **has no change to" — `docs/minimal_real_flight_plan.md:79`
- [ports and nodes] "8. **Firmware:** the fork (based on `7bac20cbcc`), not stock. The board's numerics differ from SITL's (no" — `docs/stage3_ukf_closed_loop_preregistration_draft.md:284`

### `the node` — **UNDEFINED** (see flags §a)

- [ports and nodes] *(used, not defined here)* "### FGO step 3 REPORT (the node on its causal inputs) and the real-time report" — `METHODOLOGY.md:6609` — note: used here for the FGO node; the phrase is also used for the heading node and the C++ FGO node; no defining text

### `the port` — **UNDEFINED** (see flags §a)

- [ports and nodes] *(used, not defined here)* "### D15 RESULTS (2026-09-30) — dsn, the port, FGO step 2" — `METHODOLOGY.md:7150` — note: used here for the UKF port; the phrase is also used for the C++ heading port and the FGO C++ port; no defining text
- [ports and nodes] *(used, not defined here)* "3. **The port is not yet equivalent to the offline UKF.** On `dsn_tex_r2` the offline UKF ends" — `METHODOLOGY.md:5407` — note: used here for the UKF port; the phrase is also used for the C++ heading port and the FGO C++ port; no defining text

### `thesis FGO` — **UNDEFINED** (see flags §a)

- [estimator variants] *(used, not defined here)* "**Estimator, labelled "keyframe FGO (loop closure)"** (`src/estimators/fgo/lc_fgo_replay.py`), separate from the thesis" — `METHODOLOGY.md:10461` — note: used to distinguish the 0.25 s fixed-lag FGO from the keyframe FGO; no defining text

### `thesis-baseline`

- [branches] "- `7bac20cbcc` (tag `thesis-baseline`, 2026-04-22) is a **master** commit. It is not an ancestor of any Copter release." — `docs/minimal_real_flight_plan.md:57` — note: a TAG in ~/ardupilot (7bac20cbcc), not a branch
- [branches] "| ArduPilot | `7bac20cbcc` | `7bac20cbcc` (pinned, tag `thesis-baseline`) |" — `CLAUDE.md:933`

### `u4-gndclr`

- [branches] "- **Implemented as a PORT rule** (branch `u4-gndclr` `53bac01636`; NOT merged or installed): while disarmed and" — `METHODOLOGY.md:13809` — note: ~/ardupilot_ukf branch

### `UKF`

- [estimators] "*(Status 2026-09-29: the UKF is implemented as the 15-state IMU-driven filter: `src/estimators/ukf_core.py`" — `CLAUDE.md:1071`
- [estimators] "11. UKF implementation — **built and producing numbers** (`src/estimators/ukf_core.py` + `ukf_replay.py`, Euler 15-state, shared `measurement_models.py`, gated pseudo-yaw matching EKF3's variance-gated `fuseEulerYaw`). Runs on the nomag `dsn_*` batch. See METHODOLOGY.md for the yaw-cap verification and the flow→yaw ..." — `CLAUDE.md:1873`

### `UKF port`

- [ports and nodes] "`~/ardupilot_ukf` (branch `ukf-port`, from `7bac20cbcc`) builds `bin/arducopter` with" — `METHODOLOGY.md:5229`
- [ports and nodes] "**Implementation (`~/ardupilot_ukf`, branch `ukf-port`, `AP_NavUKF`):**" — `METHODOLOGY.md:5359`

### `ukf-jitter-fix`

- [branches] "### UKF jitter correction MERGED (`a77e5f8`) and the port INSTALLED (`~/ardupilot_ukf` `ukf-jitter-fix` `abb0357d`)" — `METHODOLOGY.md:12408` — note: ~/ardupilot_ukf branch; checked out at 2026-10-16
- [branches] "- Today: `ukf-jitter-fix` = `replay-rukx` `f30f6ffa2f` (= `xuko-fmt` `0a214d29d3` + the U10 rule-2 rename). It was" — `docs/u10_replay_gate_band.md:124` — note: later fast-forwarded to replay-rukx f30f6ffa2f
- [closed-loop sets and build suffixes] "- **The fork** (`~/ardupilot_ukf`, branch `ukf-jitter-fix`, `abb0357d`, based on `7bac20cbcc`) **has no change to" — `docs/minimal_real_flight_plan.md:79`

### `ukf-port`

- [branches] "`~/ardupilot_ukf` (branch `ukf-port`, from `7bac20cbcc`) builds `bin/arducopter` with" — `METHODOLOGY.md:5229` — note: ~/ardupilot_ukf branch
- [branches] "**Implementation (`~/ardupilot_ukf`, branch `ukf-port`, `AP_NavUKF`):**" — `METHODOLOGY.md:5359`

### `ukf-port-tag`

- [branches] "### 2.1 UKF port (`~/ardupilot_ukf`, branch `ukf-port-tag` from `ukf-port`, commit `eb86bada`)" — `docs/h_backends_tag_input.md:148` — note: ~/ardupilot_ukf branch
- [branches] "- **UKF port** (`~/ardupilot_ukf`, branch `ukf-port-tag`, commit `eb86bada`; `AHRS_UKF_EXTPOS`, default 0 =" — `METHODOLOGY.md:11021`

### `ukf_shadow`

- [shadow runs] "the flags are logged: `XUKS.SS` and `H` in SITL, and `ukf_shadow.csv` in Replay." — `METHODOLOGY.md:5363` — note: ukf_shadow.csv = the UKF shadow dump in Replay
- [shadow runs] "- **So for G6, the Replay side is `ukf_shadow.csv` (= the replayed `XUKF`), and the onboard side is `XUKF` read" — `docs/u10_replay_gate_band_draft.md:94` — note: ukf_shadow.csv = the replayed XUKF
- [shadow runs] "**P2** (`ukf_shadow_sitl_tex_p2`, port `6f561c6a8d`, `AHRS_EKF_TYPE 10`, shadow):" — `METHODOLOGY.md:6973` — note: trial-name prefix ukf_shadow_sitl_* = P2 shadow run of the exact binary

### `worktree-agent-*`

- [branches] "Stage agent, worktree branch `worktree-agent-ab3173e5349728427` (from `fwd-camera` 104fd5e). Ruling: METHODOLOGY" — `docs/handovers/2026-10-09_fgo_binit0_equivalence.md:3` — note: 56 local thesis_ws branches named worktree-agent-<id> (git branch --list, 2026-10-16; includes this agent's own); no doc defines the class, this handover pattern ("Stage agent, worktree branch ... ...
- [branches] "- **Process:** the agent's worktree branch started from the unrelated `main` root and was hard-reset to `fwd-camera`" — `METHODOLOGY.md:11056`
- [branches] "- Commits on your worktree branch only; no commit while anything flies (`pgrep -f '[a]rducopter'`)." — `docs/handovers/2026-10-08_fgo_cpp_stage4_sitl_wiring.md:51`

### `xuko-fmt`

- [branches] "- **`~/ardupilot_ukf`:** new branch `xuko-fmt` = `16535f9a29` + `e88aa34a3d` + `0a214d29d3`. `ukf-jitter-fix` was" — `docs/handovers/2026-10-12_xuko_u10_h10.md:8` — note: ~/ardupilot_ukf branch
- [branches] "- **Port `xuko-fmt`** (`e88aa34a3d` FMT records + Cholesky counters; `0a214d29d3` XUKO stamp fix):" — `METHODOLOGY.md:13969`

## 5. Worlds and models


### `apriltag36h11_0`

- [sim models] "<description>AprilTag tag36h11 id 0, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_0/model.config:3`

### `apriltag36h11_1`

- [sim models] "<description>AprilTag tag36h11 id 1, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_1/model.config:3`

### `apriltag36h11_2`

- [sim models] "<description>AprilTag tag36h11 id 2, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_2/model.config:3`

### `apriltag36h11_3`

- [sim models] "<description>AprilTag tag36h11 id 3, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_3/model.config:3`

### `apriltag36h11_4`

- [sim models] "<description>AprilTag tag36h11 id 4, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_4/model.config:3`

### `apriltag36h11_5`

- [sim models] "<description>AprilTag tag36h11 id 5, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_5/model.config:3`

### `apriltag36h11_6`

- [sim models] "<description>AprilTag tag36h11 id 6, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_6/model.config:3`

### `apriltag36h11_7`

- [sim models] "<description>AprilTag tag36h11 id 7, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_7/model.config:3`

### `apriltag36h11_8`

- [sim models] "<description>AprilTag tag36h11 id 8, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_8/model.config:3`

### `apriltag36h11_9`

- [sim models] "<description>AprilTag tag36h11 id 9, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_9/model.config:3`

### `apriltag36h11_10`

- [sim models] "<description>AprilTag tag36h11 id 10, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_10/model.config:3`

### `apriltag36h11_11`

- [sim models] "<description>AprilTag tag36h11 id 11, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_11/model.config:3`

### `apriltag36h11_12`

- [sim models] "<description>AprilTag tag36h11 id 12, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_12/model.config:3`

### `apriltag36h11_13`

- [sim models] "<description>AprilTag tag36h11 id 13, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_13/model.config:3`

### `apriltag36h11_14`

- [sim models] "<description>AprilTag tag36h11 id 14, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_14/model.config:3`

### `apriltag36h11_15`

- [sim models] "<description>AprilTag tag36h11 id 15, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_15/model.config:3`

### `apriltag36h11_16`

- [sim models] "<description>AprilTag tag36h11 id 16, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_16/model.config:3`

### `apriltag36h11_17`

- [sim models] "<description>AprilTag tag36h11 id 17, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_17/model.config:3`

### `apriltag36h11_18`

- [sim models] "<description>AprilTag tag36h11 id 18, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_18/model.config:3`

### `apriltag36h11_19`

- [sim models] "<description>AprilTag tag36h11 id 19, 0.5 m overall (0.400 m black square), visual only.</description></model>" — `sim/models/apriltag36h11_19/model.config:3`

### `blank_ground_visual`

- [sim models] "<description>Visual-only featureless tile (no collision, no albedo_map). Degraded-condition floor for the corridor worlds.</description>" — `sim/models/blank_ground_visual/model.config:6`
- [sim models] "- **Blank floors:** they use visual `blank_ground_visual` tiles with the same material ... minus the albedo map (the Known Issue #12 fix: `gpu_lidar` raycasts the *rendered*" — `CLAUDE.md:108`

### `corridor_*_fwd.sdf`

- [sim worlds] `corridor_*_fwd.sdf (no ceiling)` *(superseded)* "| **Forward-camera corridor worlds** | **USE** `sim/worlds/corridor_{textured,blank,transition}_fwdc.sdf` (line-textured walls = UPPER BOUND) and `..._fwdplainc.sdf` (plain walls = featureless case), both with a plain ceiling (`corridor_ceiling`). The no-ceiling `_fwd`/`_fwdplain` worlds and the `fwd_*` dataset are ..." — `CLAUDE.md:40` — note: Key Paths: _fwd/_fwdplain SUPERSEDED

### `corridor_*_fwd.sdf, corridor_*_fwdplain.sdf`

- [sim worlds] *(superseded)* "| `corridor_*_fwd.sdf`, `corridor_*_fwdplain.sdf` | same three | no ceiling, so the forward camera **sees the cloud skybox** | **SUPERSEDED** (kept, not analysed) |" — `CLAUDE.md:118`

### `corridor_*_fwdc.sdf`

- [sim worlds] "| `corridor_*_fwdc.sdf` | same three | **line-textured walls + plain ceiling**, `iris_fwd` forward camera | **CURRENT**: `fwdc_*` (upper bound) |" — `CLAUDE.md:116`

### `corridor_*_fwdplainc.sdf`

- [sim worlds] "| `corridor_*_fwdplainc.sdf` | same three | **plain walls + plain ceiling**, `iris_fwd` | **CURRENT**: `fwdplainc_*` (featureless case) |" — `CLAUDE.md:117`

### `corridor_blank.sdf`

- [sim worlds] "Corridor world — degraded (featureless) condition." — `sim/worlds/corridor_blank.sdf:3`
- [sim worlds] "| **Corridor world (degraded)** | `~/thesis_ws/sim/worlds/corridor_blank.sdf` |" — `CLAUDE.md:38`

### `corridor_blank_fwd.sdf`

- [sim worlds] "Corridor world — degraded (featureless) condition." — `sim/worlds/corridor_blank_fwd.sdf:3` — note: SDF header is the copied downward-corridor template; the _fwd changes are in METHODOLOGY:1374

### `corridor_blank_fwdc.sdf`

- [sim worlds] "CEILING VARIANT (user ruling 2026-09-24) of corridor_blank_fwd.sdf. The only differences ... from it are the world name and an included model://corridor_ceiling (plain, visual-only, ... non-shadow-casting, bottom face at z = 5.0 m), so the forward camera sees no sky." — `sim/worlds/corridor_blank_fwdc.sdf:3`

### `corridor_blank_fwdplain.sdf`

- [sim worlds] "Corridor world — degraded (featureless) condition." — `sim/worlds/corridor_blank_fwdplain.sdf:3` — note: SDF header is the copied downward-corridor template; the _fwdplain changes are in METHODOLOGY:2170

### `corridor_blank_fwdplainc.sdf`

- [sim worlds] "CEILING VARIANT (user ruling 2026-09-24) of corridor_blank_fwdplain.sdf. The only differences ... from it are the world name and an included model://corridor_ceiling (plain, visual-only, ... non-shadow-casting, bottom face at z = 5.0 m), so the forward camera sees no sky." — `sim/worlds/corridor_blank_fwdplainc.sdf:3`

### `corridor_ceiling`

- [sim models] "<description>Plain, visual-only, non-shadow-casting ceiling at wall-top height for the ceiling forward-camera corridor worlds.</description>" — `sim/models/corridor_ceiling/model.config:6`
- [sim models] "- **`corridor_ceiling`:** ... - a static slab, 20.2 × 170 × 0.1 m; ... - bottom face at z = 5.0 m, the wall-top height, spanning x = −10.1…10.1 (the walls' ... outer faces) and y = −5…165 (the walls' extent). So it closes the corridor" — `METHODOLOGY.md:2346`
- [sim models] "- The ceiling is `corridor_ceiling` (visual-only, non-shadow-casting, underside at 5 m)." — `CLAUDE.md:126`

### `corridor_end_wall`

- [sim models] "<description>Textured static far end wall for the forward-camera corridor worlds.</description>" — `sim/models/corridor_end_wall/model.config:6`

### `corridor_end_wall_plain`

- [sim models] "<description>Plain (untextured) static far end wall for the plain-wall corridor worlds; same geometry as corridor_end_wall.</description>" — `sim/models/corridor_end_wall_plain/model.config:6`
- [sim models] "- the end wall uses `model://corridor_end_wall_plain`: the same 19.8 × 0.2 × 5 m box and ... pose as `corridor_end_wall`, with `corridor_wall`'s untextured material." — `METHODOLOGY.md:2178`

### `corridor_textured.sdf`

- [sim worlds] "Corridor world — nominal (fully textured) condition." — `sim/worlds/corridor_textured.sdf:3`
- [sim worlds] "| **Corridor world (nominal)** | `~/thesis_ws/sim/worlds/corridor_textured.sdf` |" — `CLAUDE.md:37`

### `corridor_textured_fwd.sdf`

- [sim worlds] "Corridor world — nominal (fully textured) condition." — `sim/worlds/corridor_textured_fwd.sdf:3` — note: SDF header is the copied downward-corridor template; the _fwd changes are in METHODOLOGY:1374

### `corridor_textured_fwdc`

- [sim worlds] "| corridor_textured_fwdc | CURRENT (line-textured walls = upper bound) | `fwdc_tex_r1–3`, `p1c_fwdc_tex`, `f4_fwdc_tex_r1–6`, `tsx_off_tex`, full-speed closed loop `cl_*_tex`, `gt_heading_*`, `rgs_*`, `lfs_check_tex` | thesis F1 (C0), F3, A3; pack F01, F02, F04, F05, F07, F15a; numbers §6.3–§6.6, §8, §9, §15, §15.1, ..." — `docs/thesis/world_images/index.md:25`

### `corridor_textured_fwdc.sdf`

- [sim worlds] "CEILING VARIANT (user ruling 2026-09-24) of corridor_textured_fwd.sdf. The only differences ... from it are the world name and an included model://corridor_ceiling (plain, visual-only, ... non-shadow-casting, bottom face at z = 5.0 m), so the forward camera sees no sky." — `sim/worlds/corridor_textured_fwdc.sdf:3`

### `corridor_textured_fwdplain.sdf`

- [sim worlds] "Corridor world — nominal (fully textured) condition." — `sim/worlds/corridor_textured_fwdplain.sdf:3` — note: SDF header is the copied downward-corridor template; the _fwdplain changes are in METHODOLOGY:2170

### `corridor_textured_fwdplainc`

- [sim worlds] "| corridor_textured_fwdplainc | CURRENT (plain walls = featureless case) | `fwdplainc_tex_r1–3`, `p1c_fwdplainc_tex`, `f4_fwdplainc_tex_r1–6` | thesis F1, F3, A3; pack F04, F07; numbers §6.4, §6.6, §8, §9, §15.1, §15.2 |" — `docs/thesis/world_images/index.md:26`

### `corridor_textured_fwdplainc.sdf`

- [sim worlds] "CEILING VARIANT (user ruling 2026-09-24) of corridor_textured_fwdplain.sdf. The only differences ... from it are the world name and an included model://corridor_ceiling (plain, visual-only, ... non-shadow-casting, bottom face at z = 5.0 m), so the forward camera sees no sky." — `sim/worlds/corridor_textured_fwdplainc.sdf:3`

### `corridor_textured_half_fwdc`

- [sim worlds] "- `corridor_textured_half_fwdc` differs from `corridor_textured_fwdc` only in its world name and `<real_time_factor>` (0.5 against 1.0)." — `docs/thesis/world_images/index.md:49`
- [sim worlds] "| corridor_textured_half_fwdc | CURRENT (every half-speed closed-loop result) | 27 `cl_*_half` flights, plus FGO dev, shadow and ground-test runs and `gt_heading_half*` (44 in total) | thesis F1 (closed loop), **F2**, **A1**; pack F08, F15a; numbers §15, claim 14 |" — `docs/thesis/world_images/index.md:29`

### `corridor_textured_half_fwdc.sdf`

- [sim worlds] "CEILING VARIANT (user ruling 2026-09-24) of corridor_textured_fwd.sdf. The only differences ... from it are the world name and an included model://corridor_ceiling (plain, visual-only," — `sim/worlds/corridor_textured_half_fwdc.sdf:3` — note: CONFLICT: header copied from corridor_textured_fwdc and claims the only differences from corridor_textured_fwd are the name and the ceiling; world_images/index.md:49 says it also differs in ...

### `corridor_transition.sdf`

- [sim worlds] "Corridor world — transition condition (the primary research gap)." — `sim/worlds/corridor_transition.sdf:3`
- [sim worlds] "Floor here: textured (checker) for y:0..80, blank (featureless) for ... y:80..160. BOUNDARY IS EXACTLY y = 80 m (corridor midpoint) — record" — `sim/worlds/corridor_transition.sdf:11` — note: boundary at y = 80 m
- [sim worlds] "| **Corridor world (transition)** | `~/thesis_ws/sim/worlds/corridor_transition.sdf` |" — `CLAUDE.md:39`

### `corridor_transition_fwd.sdf`

- [sim worlds] "Corridor world — transition condition (the primary research gap)." — `sim/worlds/corridor_transition_fwd.sdf:3` — note: SDF header is the copied downward-corridor template; the _fwd changes are in METHODOLOGY:1374

### `corridor_transition_fwdc.sdf`

- [sim worlds] "CEILING VARIANT (user ruling 2026-09-24) of corridor_transition_fwd.sdf. The only differences ... from it are the world name and an included model://corridor_ceiling (plain, visual-only, ... non-shadow-casting, bottom face at z = 5.0 m), so the forward camera sees no sky." — `sim/worlds/corridor_transition_fwdc.sdf:3`

### `corridor_transition_fwdplain.sdf`

- [sim worlds] "Corridor world — transition condition (the primary research gap)." — `sim/worlds/corridor_transition_fwdplain.sdf:3` — note: SDF header is the copied downward-corridor template; the _fwdplain changes are in METHODOLOGY:2170

### `corridor_transition_fwdplainc.sdf`

- [sim worlds] "CEILING VARIANT (user ruling 2026-09-24) of corridor_transition_fwdplain.sdf. The only differences ... from it are the world name and an included model://corridor_ceiling (plain, visual-only, ... non-shadow-casting, bottom face at z = 5.0 m), so the forward camera sees no sky." — `sim/worlds/corridor_transition_fwdplainc.sdf:3`

### `corridor_tson_fwdc`

- [sim worlds] "- `corridor_tson_fwdc` differs from it only in the drone model, `iris_fwd_ts`." — `docs/thesis/world_images/index.md:50`
- [sim worlds] "unchanged. ... - `tsx_on_tex`: time sync **on**. World `corridor_tson_fwdc`, which differs only in using" — `METHODOLOGY.md:3824`
- [sim worlds] "| corridor_tson_fwdc | RECORD ONLY (time-sync A/B) | `tsx_on_tex` | numbers §6.5 note row |" — `docs/thesis/world_images/index.md:30` — note: status RECORD ONLY

### `corridor_tson_fwdc.sdf`

- [sim worlds] "CEILING VARIANT (user ruling 2026-09-24) of corridor_textured_fwd.sdf. The only differences ... from it are the world name and an included model://corridor_ceiling (plain, visual-only," — `sim/worlds/corridor_tson_fwdc.sdf:3` — note: CONFLICT: header copied; does not mention the iris_fwd_ts drone (world_images/index.md:50, METHODOLOGY:3824)

### `corridor_wall`

- [sim models] "Plain grey boundary wall for the corridor worlds (corridor_textured / ... corridor_blank / corridor_transition). 170 m long (x0.2 x5), included ... twice per world (mirrored in X) to bound a 20 m wide, 160 m long flight ... corridor. Identical across all three corridor worlds so it never" — `sim/models/corridor_wall/model.config:7`

### `corridor_wall_lined`

- [sim models] "<description>corridor_wall with a line texture for the forward camera (fwd-camera workstream).</description>" — `sim/models/corridor_wall_lined/model.config:6`
- [sim models] "- **`corridor_wall_lined`:** its collision box is byte-identical to `corridor_wall` ... (0.2 × 170 × 5 m, link at z = 2.5 m). The one grey visual is replaced by 17 visual ... segments of 0.2 × 10 × 5 m that tile the same volume, so the geometry and the shadows" — `METHODOLOGY.md:1386`

### `corridor_{textured,blank,transition}.sdf`

- [sim worlds] "| `corridor_{textured,blank,transition}.sdf` | textured / blank / transition (textured y < 80 m, blank y > 80 m) | plain grey walls, no ceiling, downward sensors only | **CURRENT**: `dsn_*` baseline datasets |" — `CLAUDE.md:115` — note: world-set table row

### `corridor_{textured,blank,transition}_fwd.sdf`

- [sim worlds] "### Worlds — `corridor_{textured,blank,transition}_fwd.sdf` (vendored in `sim/worlds/`)" — `METHODOLOGY.md:1373`
- [sim worlds] "`diff` against each original shows exactly these changes: ... - the `<world name>` (it must equal the filename stem, because `run_trial.sh` builds ... the `dynamic_pose/info` topic from it); ... - the two side walls use `model://corridor_wall_lined` in place of `corridor_wall`;" — `METHODOLOGY.md:1375`

### `corridor_{textured,blank,transition}_fwdplain.sdf`

- [sim worlds] "### Design decision — `corridor_{textured,blank,transition}_fwdplain.sdf` (recorded before building or flying)" — `METHODOLOGY.md:2172`
- [sim worlds] "**Construction.** Each is the corresponding `_fwd` world with these changes only: ... - the `<world name>`; ... - the side walls use `model://corridor_wall` (plain grey, the `dsn` walls) in place of ... `corridor_wall_lined`;" — `METHODOLOGY.md:2174`

### `corridor_{textured,transition,blank}_fwd`

- [sim worlds] *(superseded)* "| corridor_{textured,transition,blank}_fwd | SUPERSEDED (the forward camera sees the sky) | `fwd_*_r1–3`, `p1_fwd_*`, `p1diag_fwd_*` | numbers §1/§2 Phase-2 rows, §11 no-ceiling group, superseded block; not analysed |" — `docs/thesis/world_images/index.md:31`

### `corridor_{textured,transition,blank}_fwdplain`

- [sim worlds] *(superseded)* "| corridor_{textured,transition,blank}_fwdplain | SUPERSEDED; no dataset was flown | `p1plain_{tex,trans,blank}` | numbers §11 (`p1plain_trans`); METHODOLOGY only |" — `docs/thesis/world_images/index.md:32`

### `corridor_{textured,transition,blank}_{fwdc,fwdplainc}.sdf`

- [sim worlds] "### Design — ceiling worlds `corridor_{textured,transition,blank}_{fwdc,fwdplainc}.sdf` (recorded before building or flying) ... **Construction.** ... - Six new worlds. `_fwdc` is built from `_fwd` (line-textured walls); `_fwdplainc` is" — `METHODOLOGY.md:2340`

### `ground_collision`

- [sim models] "<description>Collision-only infinite ground half-space, no visual. Included exactly once by each corridor world so physics is identical across conditions.</description>" — `sim/models/ground_collision/model.config:6`
- [sim models] "- **Floor:** 9 visual-only tiles (y = −20…160 m) plus **exactly one ... `model://ground_collision`**. This is the Known Issue #11 fix: coincident infinite" — `CLAUDE.md:105`

### `iris_fwd`

- [sim models] "Copy of ardupilot_gazebo iris_with_ardupilot (lift-drag + ArduPilotPlugin) that ... includes iris_fwd_standoffs (forward camera) instead of iris_with_standoffs. ... fwd-camera workstream." — `sim/models/iris_fwd/model.config:7`
- [sim models] "- **Ceiling worlds.** Our vendored `sim/models/iris_fwd/model.sdf` gets the same one-line ... change (git diff: 1 insertion, 1 deletion)." — `METHODOLOGY.md:3902` — note: time-sync one-line change applied to iris_fwd

### `iris_fwd_standoffs`

- [sim models] "Copy of ardupilot_gazebo iris_with_standoffs (thesis downward camera + gpu_lidar, ... ardupilot_gazebo d1eaad3) plus a level forward camera. Meshes resolve from ... model://iris_with_standoffs (~/ardupilot_gazebo). fwd-camera workstream." — `sim/models/iris_fwd_standoffs/model.config:7`

### `iris_fwd_ts`

- [sim models] "Copy of ardupilot_gazebo iris_with_ardupilot (lift-drag + ArduPilotPlugin) that ... includes iris_fwd_standoffs (forward camera) instead of iris_with_standoffs. ... fwd-camera workstream." — `sim/models/iris_fwd_ts/model.config:7` — note: CONFLICT: description is a verbatim copy of iris_fwd's and does not mention time sync
- [sim models] "model `iris_fwd_ts` (identical to `iris_fwd` except `<no_time_sync>0</no_time_sync>`)." — `METHODOLOGY.md:3826` — note: at the A/B: differs from iris_fwd only by <no_time_sync>0
- [sim models] "- `iris_fwd_ts` / `corridor_tson_fwdc` are kept only as the record of the A/B. `iris_fwd_ts` now ... differs from `iris_fwd` only in its model name." — `METHODOLOGY.md:3904` — note: CONFLICT with METHODOLOGY:3826: after iris_fwd also got time sync, iris_fwd_ts now differs only in its model name

### `iris_runway`

- [sim worlds] "| iris_runway | RECORD ONLY | `stage_c_blank` | the Stage C blank ATE is VOID; no current row |" — `docs/thesis/world_images/index.md:39`

### `iris_runway.sdf`

- [sim worlds] "| **Degraded world (blank)** | `~/thesis_ws/sim/worlds/iris_runway.sdf` |" — `CLAUDE.md:35` — note: no SDF header comment

### `iris_textured`

- [sim worlds] "| iris_textured | RECORD ONLY | 13: Stage B/C, `smoke_test`, `ekf3_diag_60s`, `imu_rate_verify`, `imu_verify2`, `nomag_test_long`, `sweep_v*`; also the watcher SITL bench (`~/thesis_data/wbench`) | numbers §2 IMU-rate rows and remaining flag 2; the Stage B/C ATE is VOID |" — `docs/thesis/world_images/index.md:38`

### `iris_textured.sdf`

- [sim worlds] "| **Nominal world (textured)**| `~/thesis_ws/sim/worlds/iris_textured.sdf` |" — `CLAUDE.md:36` — note: no SDF header comment
- [sim worlds] "6. **Textured world too small — and the consequence is far worse than "feature-poor segments".** 20 m × 20 m checkerboard (spans y = −10…+10 m); drone exits the mat during forward-flight trials. **Measured 2026-07-22: the `textured_ground` plane is the ONLY ground geometry in `iris_textured.sdf`, so past the mat edge ..." — `CLAUDE.md:1686` — note: Known Issue 6: 20 x 20 m mat only

### `iris_with_ardupilot`

- [sim models] "Starting with iris_with_standoffs ... add LiftDragPlugin ... add ArduCopterPlugin" — `sim/models/iris_with_ardupilot/model.config:28`
- [sim models] `iris_with_ardupilot (sim/models, time sync)` "| **Drone model with time sync (2026-09-29)** | `sim/models/iris_with_ardupilot/` — vendored copy of the upstream model, identical except `<no_time_sync>0</no_time_sync>` (line 789); it SHADOWS `~/ardupilot_gazebo/models/iris_with_ardupilot` for every world. `sim/models/iris_fwd/` (forward-camera drone) has the same ..." — `CLAUDE.md:43`
- [sim models] "> and our iris model does (`iris_with_ardupilot/model.sdf:789`: `<no_time_sync>1</no_time_sync>`)." — `CLAUDE.md:751` — note: states <no_time_sync>1</no_time_sync> at model.sdf:789 (upstream, 2026-09-29 correction); the vendored copy sets 0 (CLAUDE.md:43)

### `outdoor_indoor.sdf`

- [sim worlds] "<!-- Experiment O (user ruling 2026-10-08): outdoor -> indoor -> outdoor. Physics, plugins, lighting and the drone as ... room_tags.sdf (itself copied from corridor_textured.sdf; the upstream axis-line visuals removed). Floor: five" — `sim/worlds/outdoor_indoor.sdf:2`
- [sim worlds] "**World** (`sim/worlds/outdoor_indoor.sdf`): the corridor checker floor over y = −20…80 m, with exactly one collision" — `METHODOLOGY.md:10296`

### `room_tags`

- [sim worlds] "- `room_tags`: 10 × 10 m room, 3 m walls, textured floor, 8 floor tags (0.5 m, 0.4 m black square) on the 6 m lap" — `METHODOLOGY.md:10107`

### `room_tags.sdf`

- [sim worlds] "<!-- Experiments T/L (user ruling 2026-10-08): room-sized world for AprilTag fixes (assumed 10 x 10 m until the mocap ... room is confirmed). Physics, plugins, lighting and the drone are copied from corridor_textured.sdf unchanged." — `sim/worlds/room_tags.sdf:2`

### `room_tags_map.json` — **UNDEFINED** (see flags §a)

- [sim worlds] *(used, not defined here)* ""tags": [" — `sim/worlds/room_tags_map.json:2` — note: not an SDF; a JSON tag map (ids and poses) beside room_tags.sdf; no doc names the file

### `room_wall_tag.sdf`

- [sim worlds] "<!-- Experiment H (marker-relative position holding; supervisor ruling 2026-10-08): room_tags.sdf (10 x 10 m room, ... textured floor, the 8 floor tags, one collision plane; the upstream axis lines removed) plus a vertical wall tag" — `sim/worlds/room_wall_tag.sdf:2`

### `room_wall_tag_far`

- [sim worlds] "- `room_wall_tag_far` differs from `room_wall_tag` only in the spawn, (0, 1.1) against (0, 3.5)." — `docs/thesis/world_images/index.md:51`

### `room_wall_tag_far.sdf`

- [sim worlds] "<!-- Experiment H (marker-relative position holding; supervisor ruling 2026-10-08): room_tags.sdf (10 x 10 m room, ... textured floor, the 8 floor tags, one collision plane; the upstream axis lines removed) plus a vertical wall tag" — `sim/worlds/room_wall_tag_far.sdf:2`

### `room_wall_tag_far_occ`

- [sim worlds] "- `room_wall_tag_far_occ` differs from `room_wall_tag_far` only in the occluder's start height: z = 1.5 m, in front of the tag, against z = −5 m, parked." — `docs/thesis/world_images/index.md:52`

### `room_wall_tag_far_occ.sdf`

- [sim worlds] "<!-- Experiment H (marker-relative position holding; supervisor ruling 2026-10-08): room_tags.sdf (10 x 10 m room, ... textured floor, the 8 floor tags, one collision plane; the upstream axis lines removed) plus a vertical wall tag" — `sim/worlds/room_wall_tag_far_occ.sdf:2`

### `sim/worlds/`

- [sim worlds] `sim/worlds/ (world list)` "- `worlds/` — the five worlds the harness flies: `corridor_{textured,blank,transition}.sdf` ... (the degraded-sensing dataset), `iris_runway.sdf`, `iris_textured.sdf`." — `sim/README.md:9` — note: CONFLICT/stale: says "the five worlds the harness flies"; sim/worlds now holds 24 SDFs (world_images/index.md:41) plus room_tags_map.json

### `textured_ground`

- [sim models] "<description>Checkerboard ground plane for optical flow testing.</description>" — `sim/models/textured_ground/model.config:6`
- [sim models] "6. **Textured world too small — and the consequence is far worse than "feature-poor segments".** 20 m × 20 m checkerboard (spans y = −10…+10 m); drone exits the mat during forward-flight trials. **Measured 2026-07-22: the `textured_ground` plane is the ONLY ground geometry in `iris_textured.sdf`, so past the mat edge ..." — `CLAUDE.md:1686` — note: its plane is the only ground in iris_textured.sdf (Known Issue 6)

### `textured_ground_visual`

- [sim models] "<description>Visual-only checkerboard tile (no collision). Nominal-condition floor for the corridor worlds.</description>" — `sim/models/textured_ground_visual/model.config:6`

### `worlds`

- [sim worlds] `worlds (inventory)` "**24 SDFs in total:** ... - 16 have current results or their underlying data: the 3 dsn corridors, 6 fwdc/fwdplainc, the half-speed world, room_tags, room_wall_tag, room_wall_tag_far, outdoor_indoor, and iris_textured for two numbers.md rows. ... - 3 are record-only: tson, far_occ and iris_runway." — `docs/thesis/world_images/index.md:41`

## 6. Parameters, parameter files and log messages


### `ARM`

- [log messages] "// @LoggerMessage: ARM ... // @Description: Arming status changes" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:698`

### `ATT`

- [log messages] "// @LoggerMessage: ATT ... // @Description: Canonical vehicle attitude" — `~/ardupilot/libraries/AP_AHRS/LogStructure.h:51`

### `closedloop.parm`

- [parameter files] "# Closed-loop smoke test ONLY (METHODOLOGY "Closed loop - EKF3 flying"). Never used for a ... # dataset flight. Appended after consolidated_rerun.parm via EXTRA_PARM_FILES, so EKF3 becomes ... # the estimator the vehicle flies on. Everything else is the re-fly configuration." — `closedloop.parm:1`

### `closedloop_fgo.parm`

- [parameter files] "# D19 (ruling 2026-09-30): the thesis FGO as the ACTIVE estimator (AHRS_EKF_TYPE 13, port tree). The FGO node ... # (run_trial.sh FGO_NODE=1) sends its state over SITL SERIAL3 (udpclient 127.0.0.1:14558); SERIAL3 defaults to ... # the GPS protocol, so it is set to MAVLink2. EKF3 keeps running as a passive shadow. All ..." — `closedloop_fgo.parm:1`

### `closedloop_heading.parm`

- [parameter files] "# Closed-loop Part 1: live forward-camera heading into EKF3 via ExternalNav YAW ONLY. ... # Appended after closedloop.parm (AHRS_EKF_TYPE 3) by sim/tools/closed_loop_run.sh HEADING=1. ... # Not for dataset flights. Sources (pinned 7bac20cbcc) in heading_bridge_core.py and METHODOLOGY." — `closedloop_heading.parm:1`

### `closedloop_heading_half.parm`

- [parameter files] "# D20 (ruling 2026-09-30): the half-speed copy of closedloop_heading.parm, only VISO_DELAY_MS changed (25 ms, the receipt measure at RTF 0.5, as D2)." — `closedloop_heading_half.parm:1`

### `closedloop_ukf.parm`

- [parameter files] "# D9 (ruling 2026-09-30): the thesis UKF (AP_NavUKF, ~/ardupilot_ukf) as the ACTIVE estimator. ... # Use only via sim/tools/closed_loop_run.sh with UKF=1 (ARDUPILOT_TREE=~/ardupilot_ukf). EKF3 keeps ... # running as a passive shadow. Both values are enforced by EXPECT_OVERRIDE (eeprom self-heal)." — `closedloop_ukf.parm:1`
- [parameter files] "`9d2c545d29`. `UKF=1` is new in the launcher; it uses `closedloop_ukf.parm`: `AHRS_EKF_TYPE 12`," — `METHODOLOGY.md:7373`

### `closedloop_ukf_heading.parm`

- [parameter files] "# D17 (ruling 2026-09-30): the UKF fuses the ExtNav (forward-camera) yaw exactly as EKF3 does with ... # EK3_SRC1_YAW 6. Used with UKF=1 or UKF=shadow together with HEADING=1 (closed_loop_run.sh)." — `closedloop_ukf_heading.parm:1`

### `compass_active.parm`

- [parameter files] "# Consolidated re-run: ds_* only (compass-active yaw comparison dataset). Appended LAST via ... # EXTRA_PARM_FILES; undoes gnss_denied_nomag.parm's yaw lines. Live diff ds_tex_r1 vs dsn_tex_r1 ... # (PARM dump) is exactly these four params." — `compass_active.parm:1`
- [parameter files] "- `ds_*` record `EK3_SRC1_YAW 1` / `COMPASS_USE 1` with `compass_active.parm`; `dsn_*`," — `METHODOLOGY.md:5176`

### `consolidated_rerun.parm`

- [parameter files] "# Consolidated re-run configuration (user ruling 2026-09-29; METHODOLOGY "CONSOLIDATED RE-RUN"). ... # Appended LAST to run_trial.sh's --defaults chain, and also enforced by fly_trial.py ... # EXPECTED_PARAMS (live PARAM_SET + one soft reboot if eeprom-stored values differ)." — `consolidated_rerun.parm:1`
- [parameter files] "**Configuration for every re-run flight** (`consolidated_rerun.parm`, appended last to" — `METHODOLOGY.md:3814`

### `CTUN`

- [log messages] "// @LoggerMessage: CTUN ... // @Description: Control Tuning information" — `~/ardupilot/ArduCopter/Log.cpp:440`

### `DSF`

- [log messages] "// @LoggerMessage: DSF ... // @Description: Onboard logging statistics" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:740`

### `ERR`

- [log messages] "// @LoggerMessage: ERR ... // @Description: Specifically coded error messages" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:750`

### `EV`

- [log messages] "// @LoggerMessage: EV ... // @Description: Specifically coded event messages" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:757`

### `fgo_shadow.parm`

- [parameter files] "# D19: the FGO node's state received and its output predictor run in SHADOW (EKF3 flies). Port tree only." — `fgo_shadow.parm:1`

### `flow_ekf.parm`

- [parameter files] "# EKF3 optical flow fusion — Stage A of the EKF baseline (see CLAUDE.md, ... # "Downward Optical Flow — EKF3 Fusion (Stage A)"). Injected via MAVLink ... # OPTICAL_FLOW by flow_bridge.py." — `flow_ekf.parm:1`
- [parameter files] "| **Flow EKF3 params** | `~/thesis_ws/flow_ekf.parm` |" — `CLAUDE.md:65`

### `FMT`

- [log messages] "// @LoggerMessage: FMT ... // @Description: Message defining the format of messages in this file" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:763`

### `FMTU`

- [log messages] "// @LoggerMessage: FMTU ... // @Description: Message defining units and multipliers used for fields of other messages" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:772`

### `gnss_denied.parm`

- [parameter files] "# GNSS-denied baseline config — Stage C (see CLAUDE.md, "GNSS-Denied ... # Configuration — Stage C"). This is what the thesis actually studies: ... # position from flow-derived velocity dead-reckoning + IMU, height from the ... # downward LiDAR, no GPS contribution at all. This is the baseline config" — `gnss_denied.parm:1`
- [parameter files] "| **GNSS-denied params** | `~/thesis_ws/gnss_denied.parm` |" — `CLAUDE.md:66`

### `gnss_denied_nomag.parm`

- [parameter files] "# THROWAWAY test config - NOT part of the standing baseline. Loaded on top ... # of gnss_denied.parm (last in the --add-param-file chain) for a one-off ... # test of whether EKF3 can fly with no yaw source at all, matching the ... # UKF/FGO's actual sensor set. See CLAUDE.md / UKF design report for the" — `gnss_denied_nomag.parm:1` — note: CONFLICT: the file header still says THROWAWAY / NOT part of the standing baseline; CLAUDE.md:67 and :1234 say it is now the three-way comparison configuration
- [parameter files] "| **No-yaw comparison params (used by `run_trial.sh` for all `dsn_*` and forward-camera datasets)** | `~/thesis_ws/gnss_denied_nomag.parm` (+ `sim_noise.parm`) — the three-way comparison config (METHODOLOGY "Comparison dataset — nomag") |" — `CLAUDE.md:67`
- [parameter files] "**Fix found and verified working.** It lives in `gnss_denied_nomag.parm`, which **is now the ... three-way comparison configuration**: `run_trial.sh` loads it for every `dsn_*` and ... forward-camera trial (METHODOLOGY "Comparison dataset — nomag"). `gnss_denied.parm` itself is" — `CLAUDE.md:1234`

### `GPA`

- [log messages] "// @LoggerMessage: GPA ... // @Description: GPS accuracy information" — `~/ardupilot/libraries/AP_GPS/LogStructure.h:54`

### `GPS`

- [log messages] "// @LoggerMessage: GPS ... // @Description: Information received from GNSS systems attached to the autopilot" — `~/ardupilot/libraries/AP_GPS/LogStructure.h:17`

### `groundtest.parm`

- [parameter files] "# Closed-loop Part 1 SITL ground test ONLY (appended by sim/tools/closed_loop_run.sh when GROUND_TEST ... # is set; never loaded for a flight). ArduCopter auto-disarms a landed vehicle after DISARM_DELAY s" — `groundtest.parm:1`
- [parameter files] "- **For run 2, `groundtest.parm` sets `DISARM_DELAY 0`.** `closed_loop_run.sh` appends and enforces" — `METHODOLOGY.md:5879`

### `h10_guard_check.parm`

- [parameter files] "# H10 verification flight `h10_guard_check` ONLY (2026-10-12; docs/h10_guard_check_prereg.md). VERIFICATION, not data." — `h10_guard_check.parm:1`

### `h_extnav.parm`

- [parameter files] "# Experiment H (wall tag, forward camera; METHODOLOGY "Experiment H: pre-registration"). Appended after the standard chain. ... # ONE source set: tag position + yaw (ExternalNav) with optical-flow velocity and rangefinder height (no switching, ruling R2)." — `h_extnav.parm:1`
- [parameter files] "- **`h_extnav.parm`** (loaded by every H flight in both trees, and enforced by `closed_loop_run`'s EXPECT_OVERRIDE):" — `METHODOLOGY.md:11599`

### `h_ukf_tag.parm`

- [parameter files] "# Experiment H, S2 (the UKF flies on the wall tag; docs/h_backends_tag_input.md). Appended AFTER h_extnav.parm (which ... # sets the ExtNav source set, VISO_POS_M_NSE 0.02, VISO_DELAY_MS 31) and the closed-loop UKF file. NOT wired into any" — `h_ukf_tag.parm:1`

### `IMU`

- [log messages] "// @LoggerMessage: IMU ... // @Description: Inertial Measurement Unit data" — `~/ardupilot/libraries/AP_InertialSensor/LogStructure.h:45`

### `lidar_rangefinder.parm`

- [parameter files] "# RNGFND1 override for the downward-facing Gazebo LiDAR, injected via MAVLink ... # DISTANCE_SENSOR by lidar_bridge.py (see CLAUDE.md, Sensor Fusion Architecture)." — `lidar_rangefinder.parm:1`
- [parameter files] "| **LiDAR RNGFND1 params** | `~/thesis_ws/lidar_rangefinder.parm` |" — `CLAUDE.md:63`

### `MODE`

- [log messages] "// @LoggerMessage: MODE ... // @Description: vehicle control mode information" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:835`

### `MSG`

- [log messages] "// @LoggerMessage: MSG ... // @Description: Textual messages" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:843`

### `o_gnss.parm`

- [parameter files] "# Experiment O (outdoor -> indoor -> outdoor; ruling 2026-10-08). Appended LAST (EXTRA_PARM_FILES) after the standard ... # chain (which ends GNSS-denied, no compass). Flights stay on simulator truth (AHRS_EKF_TYPE 10, consolidated_rerun.parm)." — `o_gnss.parm:1`
- [parameter files] "**EKF3** (`o_gnss.parm`, appended after the standard chain):" — `METHODOLOGY.md:10317`

### `ORGN`

- [log messages] "// @LoggerMessage: ORGN ... // @Description: Vehicle navigation origin or other notable position" — `~/ardupilot/libraries/AP_AHRS/LogStructure.h:73`

### `PARM`

- [log messages] "// @LoggerMessage: PARM ... // @Description: parameter value" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:865`
- [log messages] "dumped from each flight's dataflash `PARM` stream (the *live* values, not what" — `CLAUDE.md:865`

### `PM`

- [log messages] "// @LoggerMessage: PM ... // @Description: autopilot system performance and general data dumping ground" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:902`

### `PSCD`

- [log messages] "// @LoggerMessage: PSCD ... // @Description: Position Control Down" — `~/ardupilot/libraries/AC_AttitudeControl/LogStructure.h:41`

### `PSCE`

- [log messages] "// @LoggerMessage: PSCE ... // @Description: Position Control East" — `~/ardupilot/libraries/AC_AttitudeControl/LogStructure.h:28`

### `PSCN`

- [log messages] "// @LoggerMessage: PSCN ... // @Description: Position Control North" — `~/ardupilot/libraries/AC_AttitudeControl/LogStructure.h:15`

### `R*`

- [log messages] `R* (Replay messages)` "- The `R*` messages (`RFRH`, `RFRF`, `RFRN`, `RISH`/`RISI` IMU, `RBRH`/`RBRI` baro, `RRNH`/`RRNI` rangefinder, `RGP*` GPS, `RMG*` compass, `RBC*` beacon, `RVOH` visual odometry, `ROFH` flow, `REPH` ext-nav, `REV2`/`REV3` events, and so on) are dispatched by `LogReader.cpp:65ff` to `LR_MsgHandler_*` ..." — `docs/partC_onboard_feasibility.md:343`

### `RATE`

- [log messages] "// @LoggerMessage: RATE ... // @Description: Desired and achieved vehicle attitude rates. Not logged in Fixed Wing Plane modes." — `~/ardupilot/libraries/AC_AttitudeControl/LogStructure.h:122`

### `RBCH`

- [log messages] "// @LoggerMessage: RBCH ... // @Description: Replay Data Beacon Header" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:405` — note: ArduPilot Replay (DAL) record

### `RBCI`

- [log messages] "// @LoggerMessage: RBCI ... // @Description: Replay Data Beacon Instance" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:429` — note: ArduPilot Replay (DAL) record

### `RBOH`

- [log messages] "// @LoggerMessage: RBOH ... // @Description: Replay body odometry data" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:558` — note: ArduPilot Replay (DAL) record

### `RBRH`

- [log messages] "// @LoggerMessage: RBRH ... // @Description: Replay Data Barometer Header" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:208` — note: ArduPilot Replay (DAL) record

### `RBRI`

- [log messages] "// @LoggerMessage: RBRI ... // @Description: Replay Data Barometer Instance" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:218` — note: ArduPilot Replay (DAL) record

### `RCIN`

- [log messages] "// @LoggerMessage: RCIN ... // @Description: RC input channels to vehicle" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:970`

### `RCOU`

- [log messages] "// @LoggerMessage: RCOU ... // @Description: Servo channel output values 1 to 14" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:988`

### `REPH`

- [log messages] "// @LoggerMessage: REPH ... // @Description: Replay external position data" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:485` — note: ArduPilot Replay (DAL) record
- [log messages] "- `REPH` = `RBOH` = 0, which is expected: no ExtNav or body-odometry source is configured. The ... same is true in `tsx_on_tex`, `tsx_off_tex` and `dsn_tex_r1`." — `METHODOLOGY.md:4030`

### `REPH.D`

- [log messages] "// @Field: D: delay on external data" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:498`

### `REV2`

- [log messages] "// @LoggerMessage: REV2 ... // @Description: Replay Event (EKF2)" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:143` — note: ArduPilot Replay (DAL) record

### `REV3`

- [log messages] "// @LoggerMessage: REV3 ... // @Description: Replay Event (EKF3)" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:175` — note: ArduPilot Replay (DAL) record

### `RFND`

- [log messages] "// @LoggerMessage: RFND ... // @Description: Rangefinder sensor information" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:1032`

### `RFRF`

- [log messages] "// @LoggerMessage: RFRF ... // @Description: Replay FRame data - Finished frame" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:54` — note: ArduPilot Replay (DAL) record

### `RFRH`

- [log messages] "// @LoggerMessage: RFRH ... // @Description: Replay FRame Header" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:44` — note: ArduPilot Replay (DAL) record

### `RFRH/RFRF/RFRN/RISH/RISI`

- [log messages] `RFRH/RFRF/RFRN/RISH/RISI (Replay records)` "`LOG_REPLAY 1`, `LOG_DISARMED 1`, `EK3_SRC1_YAW 0`. Replay records (`RFRH`, `RFRF`, `RFRN`, ... `RISH`, `RISI`) are present, so **these logs are replayable**. `fly_trial.py` found every" — `METHODOLOGY.md:3848`

### `RFRN`

- [log messages] "// @LoggerMessage: RFRN ... // @Description: Replay FRame - aNother frame header" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:65` — note: ArduPilot Replay (DAL) record

### `RGPH`

- [log messages] "// @LoggerMessage: RGPH ... // @Description: Replay Data GPS Header" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:263` — note: ArduPilot Replay (DAL) record

### `RGPI`

- [log messages] "// @LoggerMessage: RGPI ... // @Description: Replay Data GPS Instance, infrequently changing data" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:273` — note: ArduPilot Replay (DAL) record

### `RGPJ`

- [log messages] "// @LoggerMessage: RGPJ ... // @Description: Replay Data GPS Instance - rapidly changing data" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:299` — note: ArduPilot Replay (DAL) record

### `RISH`

- [log messages] "// @LoggerMessage: RISH ... // @Description: Replay Inertial Sensor header" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:100` — note: ArduPilot Replay (DAL) record

### `RISI`

- [log messages] "// @LoggerMessage: RISI ... // @Description: Replay Inertial Sensor instance data" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:118` — note: ArduPilot Replay (DAL) record
- [log messages] "| logging | `LOG_REPLAY 1`, `LOG_DISARMED 1`, `LOG_BITMASK` with IMU and OF; raise `LOG_FILE_BUFSIZE`; check `DSF` for dropped blocks after every flight | The full-rate IMU comes from `RISI` (400 Hz deltas, §4.3), so `INS_LOG_BAT_*` is optional. |" — `docs/minimal_real_flight_plan.md:145`

### `RMG*`

- [log messages] "| compass | `COMPASS_ENABLE 1`, `COMPASS_USE/USE2/USE3 0`, `EK3_SRC1_YAW 0` | **FLAG: is the nomag config still wanted for real?** Recommended: YES, so that all three estimators have no absolute yaw, as in the comparison. Replay can re-run EKF3 with compass fusion from the same log, as a sensitivity row (`RMG*` ..." — `docs/minimal_real_flight_plan.md:140`

### `RMGH`

- [log messages] "// @LoggerMessage: RMGH ... // @Description: Replay Data Magnetometer Header" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:359` — note: ArduPilot Replay (DAL) record

### `RMGI`

- [log messages] "// @LoggerMessage: RMGI ... // @Description: Replay Data Magnetometer Instance" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:381` — note: ArduPilot Replay (DAL) record

### `ROFH`

- [log messages] "// @LoggerMessage: ROFH ... // @Description: Replay optical flow data" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:463` — note: ArduPilot Replay (DAL) record

### `roll_rate_gains.parm`

- [parameter files] "# Simulation-model correction (user ruling 2026-09-29, METHODOLOGY "Roll rate gains"). ... # The iris SITL airframe has 2.25x the roll authority per inertia of pitch (full-body" — `roll_rate_gains.parm:1`
- [parameter files] "- **Values (`roll_rate_gains.parm`, in `run_trial.sh`'s defaults for every flight, and" — `METHODOLOGY.md:4569`

### `RRNH`

- [log messages] "// @LoggerMessage: RRNH ... // @Description: Replay Data Rangefinder Header" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:232` — note: ArduPilot Replay (DAL) record

### `RRNI`

- [log messages] "// @LoggerMessage: RRNI ... // @Description: Replay Data Rangefinder Instance" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:245` — note: ArduPilot Replay (DAL) record

### `RSO3`

- [log messages] "// @LoggerMessage: RSO3 ... // @Description: Replay Set Origin event (EKF3)" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:181` — note: ArduPilot Replay (DAL) record

### `RUK*`

- [log messages] "- the Replay output carries the onboard `XUKF`/`XUKO`/`XUKS`/`XUKH`/`XUKT` (copied through) AND the replayed ... `RUK*`, under different names and type ids;" — `docs/u10_replay_gate_band.md:172` — note: Replay-written copies of the XUK* records
- [log messages] "- (a) stock-flown: RUK* = the old XUK* value for value; replay_gate PASS; the scorer unchanged (1.0148 m);" — `METHODOLOGY.md:14027`

### `RUKF`

- [log messages] "- **Replay writes RUKF/RUKO/RUKS/RUKH/RUKT; the flying port keeps XUK*.**" — `METHODOLOGY.md:14019` — note: Replay name of XUKF

### `RUKF/RUKO/RUKS/RUKH/RUKT`

- [log messages] "// Dataflash record names (thesis fork, 2026-10-12, U10 rule 2). The flying port logs XUKF/XUKO/XUKS/XUKH/XUKT. Replay ... // logs the SAME records as RUKF/RUKO/RUKS/RUKH/RUKT: a Replay of a fork-flown log copies the onboard XUK* records" — `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp:28` — note: fork ~/ardupilot_ukf checked out at ukf-jitter-fix; line numbers branch-specific; Replay-only names of the XUK* records
- [log messages] "### U10 rule 2: the PREFERRED fix done and installed: replayed UKF records renamed (handover `docs/handovers/2026-10-12_u10_final.md`) ... - **Replay writes RUKF/RUKO/RUKS/RUKH/RUKT; the flying port keeps XUK*.**" — `METHODOLOGY.md:14018`

### `RUKH`

- [log messages] "- **Replay writes RUKF/RUKO/RUKS/RUKH/RUKT; the flying port keeps XUK*.**" — `METHODOLOGY.md:14019` — note: Replay name of XUKH

### `RUKO`

- [log messages] "- **Replay writes RUKF/RUKO/RUKS/RUKH/RUKT; the flying port keeps XUK*.**" — `METHODOLOGY.md:14019` — note: Replay name of XUKO

### `RUKS`

- [log messages] "- **Replay writes RUKF/RUKO/RUKS/RUKH/RUKT; the flying port keeps XUK*.**" — `METHODOLOGY.md:14019` — note: Replay name of XUKS

### `RUKT`

- [log messages] "- **Replay writes RUKF/RUKO/RUKS/RUKH/RUKT; the flying port keeps XUK*.**" — `METHODOLOGY.md:14019` — note: Replay name of XUKT

### `rung1_failsafe_fc.parm`

- [parameter files] "# RUNG 1 FAILSAFE PARAMETERS FOR THE REAL FLIGHT CONTROLLER (written 2026-10-12; handover" — `realflight/params/rung1_failsafe_fc.parm:2`
- [parameter files] "# Status: DRAFT. Not loaded on any vehicle. Stock ArduCopter at the pinned commit 7bac20cbcc, EKF3 flying" — `realflight/params/rung1_failsafe_fc.parm:5` — note: status line: DRAFT

### `rung1_template.parm`

- [parameter files] "# RUNG 1 REAL-SENSOR PARAMETER TEMPLATE (R6, docs/minimal_real_flight_plan.md section 3.3; written 2026-10-10)" — `realflight/params/rung1_template.parm:2`
- [parameter files] "# Status: DRAFT. Not yet loaded on any vehicle. Load order on the flight controller (FC):" — `realflight/params/rung1_template.parm:4` — note: status line: DRAFT

### `rung1_variant_compass.parm`

- [parameter files] "# RUNG 1 COMPASS VARIANT B: COMPASS YAW FUSED BY EKF3 (ArduPilot's usual configuration). ... # Load AFTER rung1_template.parm, and INSTEAD OF rung1_variant_nomag.parm. THE CHOICE IS THE SUPERVISOR'S (FLAG)." — `realflight/params/rung1_variant_compass.parm:1`

### `rung1_variant_nomag.parm`

- [parameter files] "# RUNG 1 COMPASS VARIANT A: NO-COMPASS YAW ("nomag"), the simulation's comparison configuration (gnss_denied_nomag.parm). ... # Load AFTER rung1_template.parm, and INSTEAD OF rung1_variant_compass.parm. THE CHOICE IS THE SUPERVISOR'S (FLAG)." — `realflight/params/rung1_variant_nomag.parm:1`

### `RVOH`

- [log messages] "// @LoggerMessage: RVOH ... // @Description: Replay Data Visual Odometry data" — `~/ardupilot/libraries/AP_DAL/LogStructure.h:447` — note: ArduPilot Replay (DAL) record

### `SIM`

- [log messages] "// @LoggerMessage: SIM ... // @Description: SITL simulator state" — `~/ardupilot/libraries/AP_Logger/LogStructure.h:1049`

### `SIM2`

- [log messages] "// @LoggerMessage: SIM2 ... // @Description: Additional simulator state" — `~/ardupilot/libraries/SITL/SIM_Aircraft.cpp:518`

### `sim_noise.parm`

- [parameter files] "# SITL sensor noise / gyro-drift model — PINNED for dataset reproducibility." — `sim_noise.parm:1`
- [parameter files] "- **Pinned & recorded.** `sim_noise.parm` versions the drift/noise params under" — `METHODOLOGY.md:770`

### `tags_extnav.parm`

- [parameter files] "# Experiments T/L (2026-10-08): EKF3 fuses AprilTag fixes as ExternalNav (tag_bridge.py, ODOMETRY on SERIAL1), with ... # optical flow (VELXY 5) and rangefinder height (POSZ 2) in the SAME source set (verified in source: AID_ABSOLUTE once a ... # tag arrives; flow keeps fusing; METHODOLOGY "T design"). Loaded AFTER ..." — `tags_extnav.parm:1`
- [parameter files] "- **`tags_extnav.parm`:** `VISO_TYPE 1`, `EK3_SRC1_POSXY 6` (ExtNav) with `VELXY 5` (flow) and `POSZ 2` (range) kept," — `METHODOLOGY.md:10056`

### `ukf_shadow.parm`

- [parameter files] "# Part 4: run the thesis UKF (AP_NavUKF, ~/ardupilot_ukf branch ukf-port) in SHADOW alongside EKF3. ... # Logging only (XUKF/XUKS); it never drives the vehicle. Use with ARDUPILOT_TREE=~/ardupilot_ukf." — `ukf_shadow.parm:1`

### `ukfonly_failsafe_fc.parm`

- [parameter files] "# UKF-ONLY CLOSED LOOP (stage 3): ESTIMATOR + FAILSAFE OVERRIDES FOR THE REAL FC (written 2026-10-12; plan" — `realflight/params/ukfonly_failsafe_fc.parm:2`
- [parameter files] "# Status: DRAFT. FORK FIRMWARE ONLY: ~/ardupilot_ukf branch board-h743 (0156bfc34e at writing), built with" — `realflight/params/ukfonly_failsafe_fc.parm:5`

### `VIBE`

- [log messages] "// @LoggerMessage: VIBE ... // @Description: Processed (acceleration) vibration information" — `~/ardupilot/libraries/AP_InertialSensor/LogStructure.h:116`
- [log messages] "`HIGHRES_IMU` return. **`VIBE` measures the raw 1000 Hz signal; the bridge ... receives a 20 Hz-low-passed one** (`INS_ACCEL_FILTER = INS_GYRO_FILTER = 20`)." — `CLAUDE.md:611`

### `VISO`

- [log messages] "// @LoggerMessage: VISO ... // @Description: Visual Odometry" — `~/ardupilot/libraries/AP_VisualOdom/LogStructure.h:11` — note: in project docs VISO appears only as the parameter prefix VISO_* (e.g. METHODOLOGY:2892), not as the log record

### `VISP`

- [log messages] "// @LoggerMessage: VISP ... // @Description: Vision Position" — `~/ardupilot/libraries/AP_VisualOdom/LogStructure.h:35`

### `VISP.CTimeMS`

- [log messages] "// @Field: CTimeMS: Corrected system time" — `~/ardupilot/libraries/AP_VisualOdom/LogStructure.h:39`

### `VISP.RTimeUS`

- [log messages] "// @Field: RTimeUS: Remote system time" — `~/ardupilot/libraries/AP_VisualOdom/LogStructure.h:38`

### `watcher_fc.parm`

- [parameter files] "# watcher_fc.parm -- FC-side parameters for the mocap safety watcher (gaps G5, G6, G11; docs/real_flights_plan.md 7.2) ... # TEMPLATE for the REAL flight controller. NOT used by any SITL flight (do not add it to run_trial.sh/closed_loop_run.sh)." — `realflight/params/watcher_fc.parm:1`

### `wbench_ekf3_flow.parm`

- [parameter files] "# SITL ONLY (watcher bench 2c, docs/handovers/2026-10-11_watcher_sitl_bench.md). Loaded after copter.parm and ... # gazebo-iris.parm by realflight/sitl_bench/bench.py, in its OWN SITL working directory. Never used by a thesis flight." — `realflight/sitl_bench/params/wbench_ekf3_flow.parm:1`

### `wbench_f7.parm`

- [parameter files] "# SITL ONLY: wbench3_f7 (the F7 watcher yaw-check bench, docs/handovers/2026-10-12_f7_cards.md §1). Loaded LAST, after ... # wbench_ekf3_flow.parm, watcher_fc.parm and wbench_ground.parm, in the bench's own SITL working directory (eeprom wiped). ... # Never used by a thesis flight." — `realflight/sitl_bench/params/wbench_f7.parm:1`

### `wbench_ground.parm`

- [parameter files] "# SITL ONLY (watcher bench 2c): GROUND session only, as real_flights_plan.md 7.2 ("for the bench session only, ... # DISARM_DELAY 0"): an armed, landed vehicle does not auto-disarm during a ground test." — `realflight/sitl_bench/params/wbench_ground.parm:1`

### `XFG*`

- [log messages] "- the FGO's XFG* records were not renamed;" — `METHODOLOGY.md:14046` — note: NOT renamed in Replay, unlike XUK* -> RUK*

### `XFGI`

- [log messages] "AP::logger().WriteStreaming("XFGI", "TimeUS,Tv,PN,PE,PD,Yaw,V,Late", "QIffffBI"," — `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavFGO.cpp:69` — note: fork ~/ardupilot_ukf checked out at ukf-jitter-fix; line numbers branch-specific; field list only
- [log messages] "**FG1 — backend equivalence to the offline FGO** (on each shadow run: the states ArduPilot received, ... `XFGI`, against `fgo_replay.py` on the same flight's bag, converted to the corridor frame; keyframe" — `METHODOLOGY.md:8045`

### `XFGO`

- [log messages] "AP::logger().WriteStreaming("XFGO", "TimeUS,PN,PE,PD,VN,VE,VD,Roll,Pitch,Yaw,OV,Age", "QfffffffffBI"," — `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavFGO.cpp:142` — note: fork ~/ardupilot_ukf checked out at ukf-jitter-fix; line numbers branch-specific; field list only
- [log messages] "- The thin backend logs `XFGI`/`XFGO`; the UKF port logs `XUK*`; EKF3 logs `XKF*`." — `docs/real_flights_plan.md:166`

### `XFGO.OV`

- [log messages] "**FG2 — validity signal:** ... - in each shadow run, `XFGO.OV` = 1 for 100% of samples from arming to disarm;" — `METHODOLOGY.md:8054`

### `XFGR`

- [log messages] "AP::logger().WriteStreaming("XFGR", "TimeUS,RC,DN,DE,DY,N", "QBfffI", AP_HAL::micros64(), reset_counter," — `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavFGO.cpp:107` — note: fork ~/ardupilot_ukf checked out at ukf-jitter-fix; line numbers branch-specific; field list only
- [log messages] "- Logged as `XFGR` and a GCS text "FGO re-anchor: …"." — `docs/h_backends_tag_input.md:200`

### `XFGR.DY`

- [log messages] "1. **28.95 s, the first tag fix: re-anchor.** `XFGR` reports **both** resets: position dN −1.42 m, dE +0.00 m, and ... **yaw −0.38°** (the `XFGR.DY` field is in degrees; an earlier verbal report of −22° misread the unit). AP_AHRS" — `METHODOLOGY.md:11118`

### `XKF1`

- [log messages] "// @LoggerMessage: XKF1 ... // @Description: EKF3 estimator outputs" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:61`
- [log messages] "| `XKF1` (EKF3's own logged state) | −0.274 … **1.025 m** | −0.118 … 0.023 m |" — `CLAUDE.md:783`
- [log messages] "**Decision (2026-07-22): keep `AHRS_EKF_TYPE=10`; evaluate EKF3 offline from ... `XKF1`.** Not merely because EKF3's current solution is too poor to fly on, but" — `CLAUDE.md:793`

### `XKF1.GZ`

- [log messages] "// @Field: GZ: Estimated gyro bias, Z axis" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:77`

### `XKF1.PE`

- [log messages] "// @Field: PE: Estimated distance from origin (East component)" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:73`

### `XKF1.PN`

- [log messages] "// @Field: PN: Estimated distance from origin (North component)" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:72`

### `XKF1.Yaw`

- [log messages] "// @Field: Yaw: Estimated yaw" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:67`

### `XKF2`

- [log messages] "// @LoggerMessage: XKF2 ... // @Description: EKF3 estimator secondary outputs" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:100`

### `XKF3`

- [log messages] "// @LoggerMessage: XKF3 ... // @Description: EKF3 innovations" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:139`

### `XKF3.IYAW`

- [log messages] "// @Field: IYAW: Innovation in vehicle yaw" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:152`
- [log messages] "`(0,0,0)` (vs actively-evolving nonzero values normally). `XKF3.IYAW` is ... *not* all-zero — traced this to EKF3's own internal "synthetic yaw" ... mechanism (`AP_NavEKF3_MagFusion.cpp`), which fuses a zero-innovation or ... last-known-static pseudo-observation every 140 ms purely to stop yaw" — `CLAUDE.md:1267`

### `XKF4`

- [log messages] "// @Description: EKF3 variances. SV, SP, SH and SM are probably best described as 'Squared Innovation Test Ratios' where values <1 tells us the measurement was accepted and >1 tells us it was rejected. They represent the square of the (innovation / maximum allowed innovation) where the innovation is the difference ..." — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:177` — note: full @Description: SV/SP/SH/SM are squared innovation test ratios

### `XKF4.errRP`

- [log messages] "// @Field: errRP: Filtered error in roll/pitch estimate" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:185`

### `XKF4.OFN`

- [log messages] "// @Field: OFN: Most recent position reset (North component)" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:186`

### `XKF4.SH`

- [log messages] "// @Field: SH: Square root of the height variance" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:182` — note: CONFLICT: field comment says square root of height variance, but the XKF4 @Description (line 177) calls SV/SP/SH/SM squared innovation test ratios; eval/lidar_short_returns.py uses the latter reading
- [log messages] "burst (+-0.3 s): EKF3's XKF4.SH (squared height innovation test ratio; > 1 = rejected, LogStructure.h:177)," — `eval/lidar_short_returns.py:4`

### `XKF4.SS`

- [log messages] "// @Field: SS: Filter solution status" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:190` — note: same field name SS means "Source Set" in XKFS (LogStructure.h:348) and is used again in the fork XUKS.SS
- [log messages] "param readback**: decoded the `nav_filter_status` bitfield (`XKF4.SS` in ... the dataflash log; bit layout from `AP_Nav_Common.h`) for every sample" — `CLAUDE.md:477`

### `XKF4.SV`

- [log messages] "// @Field: SV: Square root of the velocity variance" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:180`

### `XKF5`

- [log messages] "// @LoggerMessage: XKF5 ... // @Description: EKF3 Sensor innovations (primary core) and general dumping ground" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:214`
- [log messages] "0.4 m/s for ~3 m, stop, land; `ardupilot.bin` parsed via pymavlink's ... `DFReader` for the `XKF5` dataflash message — `FIX`/`FIY` are the flow ... innovations ×1000, `NI` is the normalised innovation test ratio, ≥100 means" — `CLAUDE.md:320`

### `XKF5.FIX`

- [log messages] "// @Field: FIX: Optical flow LOS rate vector innovations from the main nav filter (X-axis)" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:219`

### `XKF5.HAGL`

- [log messages] "// @Field: HAGL: Height above ground level" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:222`

### `XKF5.NI`

- [log messages] "// @Field: NI: Normalised flow variance" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:218` — note: CONFLICT: CLAUDE.md:322 calls NI "the normalised innovation test ratio, >=100 means rejected"
- [log messages] "innovations ×1000, `NI` is the normalised innovation test ratio, ≥100 means ... rejected by the gate, confirmed by reading `AP_NavEKF3_Logging.cpp`):" — `CLAUDE.md:322` — note: CONFLICT with source field comment "Normalised flow variance" (AP_NavEKF3/LogStructure.h:218)

### `XKF*`

- [log messages] "- The thin backend logs `XFGI`/`XFGO`; the UKF port logs `XUK*`; EKF3 logs `XKF*`." — `docs/real_flights_plan.md:166` — note: class term for the EKF3 XKF records; not in the assigned list

### `XKFM`

- [log messages] "// @LoggerMessage: XKFM ... // @Description: EKF3 diagnostic data for on-ground-and-not-moving check" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:300`

### `XKFS`

- [log messages] "// @LoggerMessage: XKFS ... // @Description: EKF3 sensor selection" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:340`

### `XKFS.GPS_GTA`

- [log messages] "// @Field: GPS_GTA: GPS good to align" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:349`

### `XKFS.MAG_FUSION`

- [log messages] "// @Field: MAG_FUSION: Magnetometer fusion (0=not fusing/1=fuse yaw/2=fuse mag)" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:351`
- [log messages] "this config, `XKFS.MAG_FUSION=0` for the entire flight (vs `1` in the ... compass-active baseline) and `XKF2`'s mag field states stay frozen at ... `(0,0,0)` (vs actively-evolving nonzero values normally). `XKF3.IYAW` is" — `CLAUDE.md:1265`

### `XKFS.SS`

- [log messages] "// @Field: SS: Source Set (primary=0/secondary=1/tertiary=2)" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:348` — note: CONFLICT of field name: XKF4.SS is "Filter solution status" (LogStructure.h:190)

### `XKV1`

- [log messages] "// @LoggerMessage: XKV1 ... // @Description: EKF3 State variances (primary core)" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:380`
- [log messages] "own logged quaternion covariance (`XKV1.V00..V03 = P[0][0..3]`) sits at **median" — `METHODOLOGY.md:922`

### `XKV2`

- [log messages] "// @LoggerMessage: XKV2 ... // @Description: more EKF3 State Variances (primary core)" — `~/ardupilot/libraries/AP_NavEKF3/LogStructure.h:397`

### `XUK*`

- [log messages] "// Dataflash record names (thesis fork, 2026-10-12, U10 rule 2). The flying port logs XUKF/XUKO/XUKS/XUKH/XUKT. Replay ... // logs the SAME records as RUKF/RUKO/RUKS/RUKH/RUKT: a Replay of a fork-flown log copies the onboard XUK* records" — `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp:28` — note: fork ~/ardupilot_ukf checked out at ukf-jitter-fix; line numbers branch-specific

### `XUKF`

- [log messages] "// XUKF: estimate (NED, deg); XUKS: 1-sigma of the main states and update counters" — `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp:997` — note: fork ~/ardupilot_ukf checked out at ukf-jitter-fix; line numbers branch-specific

### `XUKF / XUKS`

- [log messages] "| `XUKF` / `XUKS` FMT emitted and decoded in the SITL log | yes. 8,581 rows each, all paired. (The Replay log could not decode them, hence its CSV.) |" — `METHODOLOGY.md:5692`

### `XUKH`

- [log messages] "AP::logger().WriteStreaming(UKF_LOG_NAME("UKH"), "TimeUS,Psi,Inn,TR,Acc,Algn,NAcc,NRej", "QfffBBII"," — `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp:568` — note: fork ~/ardupilot_ukf checked out at ukf-jitter-fix; line numbers branch-specific; no comment, the WriteStreaming field list
- [log messages] "- **Logging:** each processed heading goes into a new `XUKH` message (measurement, innovation, test ... ratio, accepted, aligned, counts), and into the Replay dump." — `METHODOLOGY.md:7591`

### `XUKO`

- [log messages] "// XUKO: the CURRENT-TIME output (what AP_AHRS hands the controllers when AHRS_EKF_TYPE = 12), plus ... // the delayed-horizon queue's overflow count and peak depth (D9 precondition). Logger limits: format" — `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp:1002` — note: fork ~/ardupilot_ukf checked out at ukf-jitter-fix; line numbers branch-specific
- [log messages] "secondary (they agree to 1 mm on SITL); UKF record XUKO (current-time output, like XKF1)." — `METHODOLOGY.md:13527`

### `XUKS`

- [log messages] "// XUKF: estimate (NED, deg); XUKS: 1-sigma of the main states and update counters" — `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp:997` — note: fork ~/ardupilot_ukf checked out at ukf-jitter-fix; line numbers branch-specific

### `XUKS.SS`

- [log messages] "- `healthy()` and `getFilterStatus(nav_filter_status&)`, with the **same signatures and the same ... `nav_filter_status` union** that `NavEKF3` exposes to `AP_AHRS` (`AP_NavEKF/AP_Nav_Common.h`). ... - `AP_AHRS` selection wiring (Part C's per-type switch arms) is the next Part 4 step. Until then" — `METHODOLOGY.md:5360` — note: XUKS.SS carries the nav_filter_status flags; compare XKF4.SS / XKFS.SS

### `XUKT`

- [log messages] "// XUKT: each processed fix (stamped at its event time): measurement, the state after it, anchor flag, ... // fused count; DN/DE/DY = the re-anchor reset (non-zero only on the anchor row)" — `~/ardupilot_ukf/libraries/AP_NavUKF/AP_NavUKF.cpp:651` — note: fork ~/ardupilot_ukf checked out at ukf-jitter-fix; line numbers branch-specific
- [log messages] "- `XUKT`, per processed fix: measurement, state after it, anchor flag, fused count, and the reset (on the anchor" — `docs/h_backends_tag_input.md:188`

## 7. Metrics and units


### `along-track ratio` — **UNDEFINED** (see flags §a)

- [scale and failure metrics] *(used, not defined here)* "| EKF3 speed ratio / along-track ratio | 0.996–0.997 / 0.972–0.979 | — | CURRENT (correction (i)) | same |" — `docs/thesis/numbers.md:281` — note: no definition sentence found

### `apparatus`

- [ATE metrics] "offset for any no-compass estimator), or **apparatus** (cruise-window, origin ... gauge-fixed, **no** yaw alignment — used for the EKF3/UKF noise floor because ... `XKF1` is already in the true NED frame). **Never compare across metrics.** This" — `METHODOLOGY.md:13`

### `ATE RMSE`

- [ATE metrics] *(superseded)* "| Stage B ATE / RPE (`/ekf/pose`) | RMSE **6.4 mm** / RMSE **4.6 mm** | mm | SUPERSEDED (VOID) | C:L403, C:L405 | `/ekf/pose` was simulator truth (`AHRS_EKF_TYPE=10`), C:L345-L356 |" — `docs/thesis/numbers.md:760` — note: VOID: /ekf/pose was simulator truth

### `cruise window`

- [ATE metrics] "**Definition** (`eval/three_way_eval.py`, `cruise_window()`). The window is defined ... once per trial, from ground truth. The same interval is then applied to all three ... estimators." — `METHODOLOGY.md:32`
- [ATE metrics] "- **Criterion:** smoothed speed **> 0.30 m/s**. The window is the **largest contiguous ... run**, `[t0, t1]` inclusive. On the nine `dsn_*` bags it is ~30.0 → ~332.8 s" — `METHODOLOGY.md:41`
- [ATE metrics] "- **Alignment:** `evo_ape -a` (Umeyama SE3, no scale) is **fitted over the cropped ... cruise span only**. Pre-arm, climb and landing are excluded from both the fit and" — `METHODOLOGY.md:47`

### `cruise yaw-drift rate`

- [drift and tag-loss metrics] "- cruise yaw-drift rate (deg/min, linear fit of yaw error over the pinned cruise window) for EKF3" — `METHODOLOGY.md:8176`

### `d_i`

- [ATE metrics] "- **Test.** Paired per-flight difference `d_i = evo(EKF3) − evo(FGO)` (evo -a (cruise), the same" — `METHODOLOGY.md:5647`

### `displacement ratio`

- [scale and failure metrics] "metric; they are reported by displacement ratio (final displacement / true travel) and ... divergence onset (true y where the estimate departs ground truth by > 15 m), measured over" — `docs/thesis/methodology_index.md:470`

### `distance scale`

- [scale and failure metrics] "- **Current (n = 9, derived in Part C, item 9 row A):** ... - EKF3 **+5.7…+9.6%**; ... - FGO **+0.9…+1.1%**; ... - basis: path-length ratio of estimate to GT over cruise, with 20 s resampling, on" — `METHODOLOGY.md:3188`
- [scale and failure metrics] *(superseded)* "- **Superseded: +12.6% (EKF3) / +4.7% (FGO).** That was n = 1 (`dsn_tex_r1`), ... speed-magnitude based and pre-`h_flow`-correction." — `METHODOLOGY.md:3194`

### `divergence onset`

- [scale and failure metrics] "divergence onset (true y where the estimate departs ground truth by > 15 m), measured over" — `docs/thesis/methodology_index.md:471`

### `effective drift`

- [drift and tag-loss metrics] "- **Effective metrics (POST HOC, labelled; both kept):** using the actual gap in fixes, EKF3 fuses the first returning ... fix **28–44 ms** after its capture (its 31 ms `VISO_DELAY_MS` plus one prediction step). The UKF and FGO fuse it" — `METHODOLOGY.md:10849`
- [drift and tag-loss metrics] "*Drift = the EFFECTIVE metric (last fix → first returning fix); the end-of-loss metric of numbers.md §17.1 differs by ≤ 5 mm (unrounded 5.1 mm). Pre-registered bands (P-H5): EKF3 and FGO ≤ 50 / 100 / 200 / 150 mm, UKF ≤ 100 / 200 / 400 / 300 mm. P-H5 and P-H7 PASS. The comparative criteria (H-H2, P-H3, H-H4) FAIL as ..." — `docs/thesis/tables/T5_H_tag_loss_drift.md:14`

### `end-of-loss drift`

- [drift and tag-loss metrics] "- for each estimator and each loss: drift at the end of the loss (|estimate − GT|) against duration; re-lock time" — `METHODOLOGY.md:10681`
- [drift and tag-loss metrics] "Drift is the END-OF-LOSS metric as METHODOLOGY quotes it (`drift_end_m`); the §17 table above uses the EFFECTIVE metric" — `docs/thesis/numbers.md:619` — note: differs from effective by <= 5 mm

### `evo`

- [ATE metrics] "Conventions: evo = evo -a (cruise), metres" — `docs/thesis/final_results_pack.pdf p.1`
- [ATE metrics] "axes only (no log axes); evo = evo -a (cruise). † = a runaway magnitude from a diverging estimate (order of magnitude only). Flown FGO" — `docs/thesis/figures_thesis/thesis_figures_combined.pdf p.1`

### `evo -a`

- [ATE metrics] "which of these it is:** `evo -a` (SE3-aligned — removes a constant pose offset *and* ... the arbitrary yaw gauge, the fair cross-estimator metric under no compass), `evo`" — `METHODOLOGY.md:10`

### `evo -a (cruise)`

- [ATE metrics] `evo -a (cruise)` "**Amended 2026-09-24: the label also names the window.** The primary cross-estimator ... metric is **evo -a (cruise)**. It is computed only by `eval/three_way_eval.py`, over" — `METHODOLOGY.md:21`
- [ATE metrics] `evo -a (cruise)` "- **Summary:** Every ATE states its alignment and window: `evo -a`, unaligned, or apparatus." — `docs/thesis/methodology_index.md:460`

### `evo unaligned`

- [ATE metrics] "unaligned (origin only — penalises the yaw gauge, so it is dominated by heading" — `METHODOLOGY.md:12`

### `feature_count`

- [flow quality] "int32 feature_count # features tracked this frame" — `src/optical_flow_interfaces/msg/OpticalFlow.msg:9`
- [flow quality] "7. **Feature count is a deceptive quality metric** — ~100 features reported even on featureless off-mat texture. Use `inlier_ratio` (RANSAC survivors / pre-RANSAC tracked) as the real flow-quality indicator." — `CLAUDE.md:1687`

### `flow sensor scale`

- [scale and failure metrics] "- **The flow sensor itself** (measured forward flow ÷ flow predicted from GT through the shared ... `h_flow` model) reads **1.009** on every textured bag." — `METHODOLOGY.md:3552`

### `full-window, historical`

- [ATE metrics] "Figures quoted without "(cruise)" are **full-window, historical**, and are labelled as" — `METHODOLOGY.md:27`

### `hindsight gain`

- [drift and tag-loss metrics] "- **Hindsight gain** Δ = mean live error − mean hindsight error: for the FGO (live → whole-flight batch) and the UKF ... (live → RTS)." — `METHODOLOGY.md:10157`

### `horizontal error RMSE`

- [ATE metrics] "**Metrics** (`eval/tag_score.py`; absolute world frame, **no alignment**; ground truth from the bag):" — `METHODOLOGY.md:10150`
- [ATE metrics] "- **Per track** (EKF3 live, UKF live, RTS-UKF, FGO live, FGO hindsight): horizontal error RMSE, median, p95 and max;" — `METHODOLOGY.md:10153`

### `inlier_ratio`

- [flow quality] "float64 inlier_ratio # fraction of features surviving RANSAC (0–1)" — `src/optical_flow_interfaces/msg/OpticalFlow.msg:10`
- [flow quality] "Use `inlier_ratio` (RANSAC survivors / pre-RANSAC tracked) as the real flow-quality indicator." — `CLAUDE.md:1687`

### `lockout` — **CONFLICT: 2 meanings** (see flags §b)

- [F1 heading-gate metrics] "(iii) correct headings rejected (weight < 0.5 or gated out), and **lockout episodes** (≥ 3 s of ... consecutive correct headings rejected);" — `METHODOLOGY.md:7918` — note: F1: lockout episode = >= 3 s of consecutive correct headings rejected
- [H tag-loss metrics] "- **lockout:** EKF3 (no `VISP`-driven correction for > 2 s while fixes arrive, i.e. |estimate − fix| > 3σ_pos ... sustained); the UKF/FGO (none possible: no gate)." — `METHODOLOGY.md:10684` — note: CONFLICT: H experiment lockout = EKF3 not correcting for > 2 s while fixes arrive

### `max / band`

- [drift and tag-loss metrics] "each cell gives the maximum drift / its band in mm, with the range over the losses." — `docs/thesis/tables/T5_H_tag_loss_drift.md:3`

### `max cross-track`

- [drift and tag-loss metrics] "- (i) yaw-error RMS and max over the region (fwdplainc: the whole cruise; fwdc: y > 140 m);" — `METHODOLOGY.md:7915`

### `max ÷ min`

- [drift and tag-loss metrics] "*Ratio = max ÷ min of the two hindsight RMSEs (the pre-registered definition of P-T4 and P-O3), so it is ≥ 1 and the 'lower' column gives the direction: in O the RTS-UKF is lower on O_r1 and O_r2 and the FGO batch on O_r3b. Aggregation differs: T is per condition from the means of 3 repeats (the RMSE over the 5 laps); ..." — `docs/thesis/tables/T8_hindsight_ratio.md:15`

### `NEES`

- [consistency and innovation metrics] "**Cross-track consistency** (pinned cruise window; each estimator's own frame). Means over 3 ... repeats: % of samples outside ±3σ / mean 1-D NEES (consistent ≈ 1)." — `METHODOLOGY.md:3712`
- [consistency and innovation metrics] *(used, not defined here)* "covariance needed for a NEES consistency check against `/ground_truth/pose`." — `CLAUDE.md:1204` — note: acronym never expanded in the docs

### `NI`

- [consistency and innovation metrics] "`NI` is the normalised innovation test ratio, ≥100 means" — `CLAUDE.md:322`

### `NIS`

- [consistency and innovation metrics] "| Flow NIS gate | `EK3_FLOW_I_GATE` 300 → `testRatio < 1` at 3σ | **per-axis**, see §9.3 | `OptFlowFusion.cpp:665–668` |" — `FGO_DESIGN.md:421`
- [consistency and innovation metrics] "measurement's error against GT, coloured accepted/rejected; NIS against the gate of 9;" — `METHODOLOGY.md:3662` — note: NIS against the gate of 9

### `noise floor` — **CONFLICT: 2 meanings** (see flags §b)

- [ds_* noise floor (apparatus ATE range)] "| Noise floor `ds_*` (compass-active, apparatus): within-condition ATE range | 2.81–10.90 m | m | CURRENT (`ds_*` only) | M:L800 |" — `docs/thesis/numbers.md:865` — note: CONFLICT: ds_* noise floor = within-condition ATE range on the apparatus metric
- [dsn noise floor (SD over repeats)] "| Noise floor SD (re-flown `dsn_tex`): EKF3 (n = 10) / FGO (n = 9) / d (n = 9) | 0.31 [0.22, 0.57] / **1.30 [0.88, 2.49]** / 1.02 [0.69, 1.96] (the FGO is no longer the "tight" estimator) | m | CURRENT (FGO-only re-run 2026-10-10) | json:dsn_paired_test.json |" — `docs/thesis/numbers.md:229` — note: dsn noise floor = SD over the re-flown dsn_tex repeats
- [dsn noise floor (SD over repeats)] "**The n=3 ranges are not a noise floor.** With three repeats, a fourth run lands" — `METHODOLOGY.md:131`

### `re-lock time`

- [drift and tag-loss metrics] "re-lock time ... (occluder OFF → first fused fix); position and yaw jump at re-lock (the largest estimate step in the 2 s after the" — `METHODOLOGY.md:10681`

### `RTF`

- [run-time metrics] "**The sim's real-time factor (RTF) is the actual rate bottleneck, not `update_rate`**: this machine runs the model at RTF ≈ 0.05–0.17 (measured via `gz topic -e -t /stats`), even standalone/headless with no GUI or ArduPilot attached, so the *wall-clock* topic rate (what `ros2 topic hz` reports) is roughly `update_rate ..." — `CLAUDE.md:156`

### `RTF (cruise)`

- [run-time metrics] `RTF (cruise)` "- RTF (cruise; the scores' `diag RTF (cruise)`);" — `METHODOLOGY.md:8174`

### `SE3`

- [trajectory alignment] "- **Alignment:** `evo_ape -a` (Umeyama SE3, no scale) is **fitted over the cropped" — `METHODOLOGY.md:47` — note: SE3 spelling; Umeyama alignment with no scale used by evo_ape -a
- [trajectory alignment] "- **ATE** (`evo_ape`, SE(3)-aligned): RMSE **6.4 mm**, mean 5.4 mm, max" — `CLAUDE.md:410` — note: same alignment written SE(3)
- [trajectory alignment] "| R-a | **Pre-registration sign-off** (the user), then apply it: primary metric (evo -a SE(3) proposed), UKF record, drift segment, n, the Replay-fidelity tolerance (1 cm / 0.1°), the converter band, the timestamp rule. Mark the JSON final | 0.25 d after the ruling | DRAFT | **YES**, for result sorties (verification ..." — `docs/realflight_plan_copter.md:139` — note: "evo -a SE(3)" spelling in the rung-1 metric
- [trajectory alignment] "which of these it is:** `evo -a` (SE3-aligned — removes a constant pose offset *and*" — `METHODOLOGY.md:10`

### `speed ratio`

- [scale and failure metrics] "| horizontal speed ratio (median \|v_est\| / \|v_gt\|) | **1.068–1.070** | **0.835–0.838 / 0.850–0.851** | 1.011–1.013 / 1.012–1.015 |" — `METHODOLOGY.md:3549`

### `step time`

- [run-time metrics] "**Step time (DIAGNOSTIC, workstation Python): ~29 ms median on textured bags, ~15 ms transition, ~4 ms blank** (world-dependent). The old "~101 ms/step" was the 1.0 s-window configuration and is superseded. Distance scale over n=9 textured bags: EKF3 +5.7…+9.6 %, FGO +0.9…+1.1 % (the n=1 +12.6 %/+4.7 % is superseded); ..." — `CLAUDE.md:1874`

### `testRatio`

- [consistency and innovation metrics] "Gate formula confirmed exact: `testRatio = ν² / ((0.01·GATE)² · S)`," — `CLAUDE.md:1140`

### `yaw-error RMS`

- [drift and tag-loss metrics] "- (i) yaw-error RMS and max over the region (fwdplainc: the whole cruise; fwdc: y > 140 m);" — `METHODOLOGY.md:7915`

### `†`

- [diverging-result marker] "Rows marked **†** carry magnitudes from the Python FGO's **runaway** on blank or transition floors (end-of-cruise km ... errors, +60 s errors, displacement ratios, onsets, runaway-size bands)." — `docs/thesis/numbers.md:684`
- [diverging-result marker] "† = a runaway" — `docs/thesis/final_results_pack.pdf p.1`
- [diverging-result marker] "## † Diverging (unaided) FGO results: evidence of divergence, not precise values (ruling 2026-10-08)" — `docs/thesis/numbers.md:682`

## 8. Rulings, standing rules and status labels


### `[E]`

- [evidence labels] "- **[V]** verified: built, measured from the ELF or `.apj`, or read in source; ... - **[E]** an estimate, with its basis; ... - **[U]** unverified (needs the board or a bench)." — `docs/board_firmware_plan.md:8`
- [evidence labels] "Status: built and checked without a Pi, 2026-10-02. [V] = done and verified here; [E] = estimate; [U] = needs a real Pi." — `docs/real_flights_pi_readiness.md:3`
- [evidence labels] "- **[V]** verified (source, a build, a log or a stored result); ... - **[E]** an estimate; ... - **[U]** unknown until the hardware or a ruling arrives." — `docs/realflight_plan_copter.md:19`

### `[RULING]`

- [TBD labels (stage-3 draft)] "- **[TBD-S]** supervisor or hardware input, fixed before the first result sortie; ... - **[TBD-V]** fixed once from VERIFICATION or rung-1 data, before the first result sortie; ... - **[RULING]** a choice for the user." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:20`

### `[TBD-S]` — **CONFLICT: 2 meanings** (see flags §b)

- [TBD labels (stage-3 draft)] "- **[TBD-S]** supervisor or hardware input, fixed before the first result sortie; ... - **[TBD-V]** fixed once from VERIFICATION or rung-1 data, before the first result sortie; ... - **[RULING]** a choice for the user." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:20` — note: TBD-S deadline differs from u10 ("before day 3" vs "before the first result sortie")
- [TBD labels (u10 band)] "Labels: **[V]** verified (source, a build or a stored result); **[E]** an estimate; **[TBD-S]** supervisor or ... hardware input, fixed before day 3; **[TBD-V]** fixed ONCE on the verification logs (H, V) before any result log is" — `docs/u10_replay_gate_band.md:11`

### `[TBD-V]` — **CONFLICT: 2 meanings** (see flags §b)

- [TBD labels (stage-3 draft)] "- **[TBD-S]** supervisor or hardware input, fixed before the first result sortie; ... - **[TBD-V]** fixed once from VERIFICATION or rung-1 data, before the first result sortie; ... - **[RULING]** a choice for the user." — `docs/stage3_ukf_closed_loop_preregistration_draft.md:20` — note: TBD-S deadline differs from u10 ("before day 3" vs "before the first result sortie")
- [TBD labels (u10 band)] "Labels: **[V]** verified (source, a build or a stored result); **[E]** an estimate; **[TBD-S]** supervisor or ... hardware input, fixed before day 3; **[TBD-V]** fixed ONCE on the verification logs (H, V) before any result log is" — `docs/u10_replay_gate_band.md:11`

### `[U]` — **CONFLICT: 3 meanings** (see flags §b)

- [U label = needs a real Pi] "Status: built and checked without a Pi, 2026-10-02. [V] = done and verified here; [E] = estimate; [U] = needs a real Pi." — `docs/real_flights_pi_readiness.md:3` — note: CONFLICT: the U label has three wordings across the plans
- [U label = unknown until the hardware or a ruling arrives] "- **[V]** verified (source, a build, a log or a stored result); ... - **[E]** an estimate; ... - **[U]** unknown until the hardware or a ruling arrives." — `docs/realflight_plan_copter.md:19` — note: CONFLICT: the U label has three wordings across the plans
- [U label = unverified (needs the board or a bench)] "- **[V]** verified: built, measured from the ELF or `.apj`, or read in source; ... - **[E]** an estimate, with its basis; ... - **[U]** unverified (needs the board or a bench)." — `docs/board_firmware_plan.md:8` — note: CONFLICT: the U label has three wordings across the plans

### `[V]`

- [evidence labels] "- **[V]** verified: built, measured from the ELF or `.apj`, or read in source; ... - **[E]** an estimate, with its basis; ... - **[U]** unverified (needs the board or a bench)." — `docs/board_firmware_plan.md:8`
- [evidence labels] "Status: built and checked without a Pi, 2026-10-02. [V] = done and verified here; [E] = estimate; [U] = needs a real Pi." — `docs/real_flights_pi_readiness.md:3`
- [evidence labels] "- **[V]** verified (source, a build, a log or a stored result); ... - **[E]** an estimate; ... - **[U]** unknown until the hardware or a ruling arrives." — `docs/realflight_plan_copter.md:19`

### `A8` — **CONFLICT: 3 meanings** (see flags §b)

- [real-flight readiness checklist rows] "| A8 | Rangefinder on the vehicle: a native FC driver (`RNGFND1_TYPE` per model), or read on the Pi and injected as `DISTANCE_SENSOR` (the SITL pattern) | not built | a, b | `lidar_rangefinder.parm` is `TYPE 10` (MAVLink), `MIN 0.05`, `MAX 40` (gpu_lidar values). The sim LiDAR rests at 0.075 m, below many real LiDAR ..." — `docs/real_flight_readiness.md:63`
- [rung-1 converter acceptance checks] "| A8 | geometry: `FLOW_POS_*` vs `ROFH.posOffset`; `RNGFNDn_POS_*` vs `RRNI.pos_offset` | to 1e-6 |" — `docs/rung1_preregistration.md:354`
- [watcher bench amendment letters (A-series)] "- **A8 — B4a and B4c ARE run in SITL (pre-registered here, committed before the run).** §1.3 listed them as" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:146`
- [watcher bench amendment letters (A-series)] "### 2c: watcher bench B0–B10 in SITL with a simulated mocap feed (VERIFICATION only; `wbench_*`; handover `docs/handovers/2026-10-11_watcher_sitl_bench.md`, pre-registration plus amendments A1–A8)" — `METHODOLOGY.md:13585` — note: METHODOLOGY: "amendments A1–A8"

### `A9` — **CONFLICT: 3 meanings** (see flags §b)

- [real-flight readiness checklist rows] "| A9 | Range to the Pi for the UKF/FGO: FC `DISTANCE_SENSOR` telemetry → `/downward_lidar/range` republisher (if the LiDAR is on the FC) | not built | b live; a can instead use dataflash `RFND` offline | Today `lidar_bridge.py` goes the other way (ROS → FC). | 0.5 d | A8, B1 |" — `docs/real_flight_readiness.md:64`
- [rung-1 converter acceptance checks] "| A9 | range vs the FC's `RFND` (same instance, Good), the RFND sample within 60 ms of each converter range emission | ≥ 50 pairs; median \|diff\| ≤ 0.02 m; p95 ≤ 0.05 m |" — `docs/rung1_preregistration.md:355`
- [watcher bench amendment letters (A-series)] "- **A9 (2026-10-12, ~11:45, after `wbench2_hoverB_20261012_112751` was stopped; before any further run). Harness" — `docs/handovers/2026-10-12_watcher_bench_rerun.md:83`
- [watcher bench amendment letters (A-series)] "- **A9:** the first hoverB session was aborted and kept unused. Carrying the vehicle home also rotated it unseen by" — `METHODOLOGY.md:13882` — note: same meaning restated

### `ABLATION`

- [verdict and evidence labels] "1. **The "FGO noise fix only (yaw cap ungated)" runs are KEPT as a labelled ABLATION.** What the yaw-cap gating alone ... changes is reported against the final corrected runs. The pairs:" — `METHODOLOGY.md:12385`

### `ARTEFACT`

- [re-run comparison flags] "| **ARTEFACT** | **7** | #3–#6 (6.4 transition displacement ratios) and #7–#9 (section 8 per-trial verdicts) |" — `docs/thesis/final_restatement_draft.md:27`

### `as worded` — **UNDEFINED** (see flags §a)

- [verdict and evidence labels] *(used, not defined here)* "**2. `fwdc_tex_r2`: recorded as a PRIMARY MISS as worded, not re-scored.**" — `METHODOLOGY.md:5332` — note: 118 uses in METHODOLOGY; no defining text
- [verdict and evidence labels] *(used, not defined here)* "**Rule A, as worded: "adopt 0.10 s".** The literal maximum age of (i) exceeds 250 ms. The literal maxima are" — `METHODOLOGY.md:11417` — note: 118 uses in METHODOLOGY; no defining text
- [verdict and evidence labels] *(used, not defined here)* "- Criterion 4's wording did not exempt the post-disarm period, so the criterion fails as worded, and it is reported" — `docs/handovers/2026-10-12_xuko_u10_h10.md:241` — note: 118 uses in METHODOLOGY; no defining text

### `BASELINE CORRECTIONS ARE BATCHED (user, 2026-09-24)`

- [standing rules] `BASELINE CORRECTIONS ARE BATCHED (user, 2026-09-24)` "The OI-2 dejitter re-run (below) is the **current `dsn` baseline**. From now on, ... further corrections to the `dsn` baseline are **batched into one consolidated re-run ... before the results chapter**, not restated one at a time. **Dejitter applies to all new" — `METHODOLOGY.md:1168` — note: not titled "standing rule" but a standing instruction

### `bounded, not proven`

- [lifecycle labels] "**Clock sensitivity — bounded, not proven.** EKF3's TUMs come from dataflash `TimeUS`. ... The UKF/FGO TUMs and the window come from bag sim-time. Applying one interval to both ... assumes the two clocks share an epoch. Rather than prove this formally, the check ... shifts the whole window by ±0.25 s and ±0.5 s (a ..." — `METHODOLOGY.md:84`
- [lifecycle labels] "**CLOSED 2026-09-24 as "bounded, not proven".** No formal alignment proof was ... done. Instead, a sensitivity check shifts the pinned cruise window by ±0.25 s and" — `CLAUDE.md:815`

### `CLOSED` — **UNDEFINED** (see flags §a)

- [lifecycle labels] *(used, not defined here)* "### OI-1 (FGO blank-floor freeze) — reviewed against the new behaviour: CLOSED as superseded" — `METHODOLOGY.md:5595`
- [lifecycle labels] *(used, not defined here)* "rates. **The heading-timing fairness concern is CLOSED as negligible.**" — `METHODOLOGY.md:9399`
- [lifecycle labels] *(used, not defined here)* "- **The `dsn` noise floor is CLOSED** in `numbers.md` (EKF3 0.31 m, FGO 0.13 m). The ruled UKF claim" — `METHODOLOGY.md:6749`

### `CURRENT`

- [status labels (numbers.md / methodology_index)] "- CURRENT: the standing value." — `docs/thesis/numbers.md:16`
- [status labels (numbers.md / methodology_index)] "- **Status:** CURRENT = the standing record. SUPERSEDED = replaced; the replacing entry is" — `docs/thesis/methodology_index.md:25` — note: methodology_index says "the standing record", numbers.md "the standing value"

### `CURRENT (pre-registered)`

- [status labels (numbers.md / methodology_index)] `CURRENT (pre-registered)` "- CURRENT (pre-registered): a pre-registered band or setting." — `docs/thesis/numbers.md:19`

### `D1` — **CONFLICT: 5 meanings** (see flags §b)

- [D-rulings] "- **D1 (B4 scorer), extra evidence.** Under the ORIGINAL sample-count scorer, `cl_b_tex_r2` and" — `METHODOLOGY.md:6344`
- [D-rulings] "- **D1:** the time-window B4 scorer is a **bug fix, not a criterion change**. Set (b) with the Python" — `METHODOLOGY.md:6367` — note: ruling 2026-09-30
- [D-rulings] "- **D1** (B4 time-window scorer): bug fix. Set (b) with the Python node is "3/3 corrected, 2/3" — `docs/decisions_queue.md:258` — note: same meaning, summary
- [experiment T run labels] *(used, not defined here)* "Three repeats each, run interleaved (A1 B1 C1 D1 A2 … D3): 12 flights. Every condition anchors on tag 0, at the" — `METHODOLOGY.md:10123` — note: run list of experiment T; D1/D3 here are run labels (not defined as such), unrelated to the D-rulings
- [real-flight readiness items] "| D1 | Downward-camera intrinsics and distortion: focal length for the px/s → rad/s conversion | exists but untested on hardware | a, b | `tools/real_camera/calibrate.py`. Self-test `selftest_calibration.py` passed (fx within 0.15%, k1 within 0.0012; README). Never run on a real lens. | 0.5 d | A3 |" — `docs/real_flight_readiness.md:97` — note: CONFLICT: readiness calibration item, not the D-ruling of the same number
- [rung-1 calendar gates] "| **Mon 12** | **Supervisor inputs S1–S7**; firmware decision S6; mocap booking | **D1: inputs received.** If there is no answer by Tue 13, rung 1 is at risk. |" — `docs/minimal_real_flight_plan.md:393` — note: CONFLICT: calendar gate in §6, not the D-ruling
- [rung-1 data-integrity checklist] "| D1 | `.BIN` downloaded, file size plausible, copied to two places; named `<sortie>_<date>.BIN` | yes |" — `docs/rung1_flight_cards.md:306` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number
- [watcher bench deviations] "- **Deviation D1 (identity):** the G3 identity proof is a HAND motion before arming. SITL has no hand, and arming" — `docs/handovers/2026-10-11_watcher_sitl_bench.md:48` — note: CONFLICT: bench deviation D1, not the D-ruling

### `D2` — **CONFLICT: 4 meanings** (see flags §b)

- [D-rulings] "- **D2:** switch to the **C++ heading node for all subsequent closed-loop flights**." — `METHODOLOGY.md:6371`
- [D-rulings] "- **D2** (C++ heading node): switched. `VISO_DELAY_MS 38`; ground test passed; set (b) re-flown 3/3." — `docs/decisions_queue.md:260` — note: same meaning; "D2 rule"/"D2 procedure" later = VISO_DELAY_MS from min receipt latency
- [D-rulings] "### D2: `VISO_DELAY_MS` for the C++ node, by the ORIGINAL G4 rule" — `METHODOLOGY.md:6398` — note: D2 rule for VISO_DELAY_MS
- [real-flight readiness items] "| D2 | Forward-camera intrinsics, undistortion and resampling onto the frozen simulated camera (640×480, fx 554.38) | exists but untested on hardware | b (heading arms); a if flown | `tools/real_camera/run_heading_video.py`. A PNG round trip reproduced Phase 3's headings to 2.4e-14° (README). | 0.5–1 d | A6 |" — `docs/real_flight_readiness.md:98` — note: CONFLICT: readiness calibration item, not the D-ruling of the same number
- [rung-1 calendar gates] "| Thu 15 – Fri 16 | R5 firmware build and flash; R6 bench readback; R12 bench (flow orientation, rangefinder, log completeness); R1/R2 SITL acceptance tests (light single replays) | **D2 (Fri 16): a flying vehicle with working flow and rangefinder on the bench, logs complete.** If not, rung 1 is NOT reached by 23 Oct. ..." — `docs/minimal_real_flight_plan.md:395` — note: CONFLICT: calendar gate in §6, not the D-ruling
- [rung-1 data-integrity checklist] "| D2 | **LOG_REPLAY records present**: `RFRH`, `RFRF`, `RISH`, `RISI`, `ROFH`, `RRNH`, `RRNI` counts > 0; `RFRH` at ≈ 400 Hz | all present |" — `docs/rung1_flight_cards.md:307` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number

### `D5` — **CONFLICT: 3 meanings** (see flags §b)

- [D-rulings] "the user's, and is queued (D5).** Adding a buffer changes the port only, never the offline UKF." — `METHODOLOGY.md:6223` — note: queued text: the choice of adding a flow delay buffer to the UKF port (preceding lines)
- [D-rulings] "- **D5:** **add a flow delay buffer to the UKF port** (EKF3's approach). The IMU path and flow-gyro" — `METHODOLOGY.md:6378`
- [real-flight readiness items] "| D5 | Flow sign and axis re-verification on the real mount: the lateral-sign finding of 2026-09-29 | needs adapting for real sensors | a, b | `flow_bridge.py:27-31`. Only the SITL mount is verified, and CLAUDE.md warns against transferring it to a different mount. | 0.5 d hand-carried, against mocap | A5, D3, F1 |" — `docs/real_flight_readiness.md:101` — note: CONFLICT: readiness calibration item, not the D-ruling of the same number
- [rung-1 data-integrity checklist] "| D5 | `PARM` dump in the log: AHRS_EKF_TYPE = 3, LOG_REPLAY = 1, the EK3_SRC1_* and sensor values as filed | as filed |" — `docs/rung1_flight_cards.md:310` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number

### `D6` — **CONFLICT: 3 meanings** (see flags §b)

- [D-rulings] "- **Queued (D6):** whether to fly a replacement `dsn_tex_r11`, with the rule applied to it as well," — `METHODOLOGY.md:6244`
- [D-rulings] "- **D6:** not needed." — `METHODOLOGY.md:6382`
- [real-flight readiness items] "| D6 | Vanishing-point heading method re-validated on real images under a **new pre-registration** (plan question 6) | not built | b (heading arms); a if the forward camera is flown | The frozen parameters (0.5° tolerance, `S_MIN` 200 px, 80 px box) were calibrated on ideal simulated images. It fails plain walls over ..." — `docs/real_flight_readiness.md:102` — note: CONFLICT: readiness calibration item, not the D-ruling of the same number
- [rung-1 data-integrity checklist] "| D6 | `ARM`/`EV` records: one arm and one disarm; both sync wiggles visible in `RISI` gyro (rates > 2 rad/s) **while disarmed** | yes |" — `docs/rung1_flight_cards.md:311` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number

### `D7` — **CONFLICT: 3 meanings** (see flags §b)

- [D-rulings] "- **D7:** the FGO track starts with the **ROS-node route and its validation**:" — `METHODOLOGY.md:6383`
- [D-rulings] "- **D7** (the FGO node route): started. Steps 2–3, real-time, validity and shadow runs are done (see" — `docs/decisions_queue.md:265`
- [real-flight readiness items] "| D7 | Wall-tag method re-validated: S0 (validity rule and σ_pos) repeated on real images against mocap | not built | a, b if P-HOLD | `tag_hold_design.md` "Transfer"; the D18 shared tag-validity rule (METHODOLOGY "RULING 2026-10-08, shared tag-fix VALIDITY RULE"). | 1–2 d | A7, I3 |" — `docs/real_flight_readiness.md:103` — note: CONFLICT: readiness calibration item, not the D-ruling of the same number
- [rung-1 data-integrity checklist] "| D7 | **Mocap file present** (`<take>.csv`, exported as `t_s, x, y, z, qx, qy, qz, qw`, metres, z up), covering both sync wiggles; tracking loss in the flight < 0.5 s cumulative | yes |" — `docs/rung1_flight_cards.md:312` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number

### `D8` — **CONFLICT: 2 meanings** (see flags §b)

- [D-rulings] "### D8. Flow timing (from D5's step-3 re-run)" — `docs/decisions_queue.md:295` — note: queue text (kept as history under "Former OPEN text of D8–D14")
- [D-rulings] "- **D8:** **keep EKF3's flow timing in the UKF port** (fair to EKF3 in closed loop)." — `METHODOLOGY.md:6754` — note: ruling 2026-09-30
- [rung-1 data-integrity checklist] "| D8 | **Mocap synced:** `mocap_align` run on this sortie; its default windows (since 2026-10-11) are the two DISARMED sync-wiggle bursts (`RISI` \|ω\| > 2 rad/s: the last burst before arming and the first after disarming, ± 2 s; the old default, arm to arm + 25 s, missed the pre-arm wiggle). Check `window_sources` in ..." — `docs/rung1_flight_cards.md:313` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number

### `D9` — **CONFLICT: 2 meanings** (see flags §b)

- [D-rulings] "### D9. First UKF flight: with or without the forward-camera heading" — `docs/decisions_queue.md:308` — note: queue text (kept as history under "Former OPEN text of D8–D14")
- [D-rulings] "- **D9:** the first UKF flight **without** the heading source, then **with** it." — `METHODOLOGY.md:6760` — note: ruling 2026-09-30
- [rung-1 data-integrity checklist] "| D9 | Sortie sheet complete: class (VERIFICATION/RESULT), battery, times, take name, any deviation | yes |" — `docs/rung1_flight_cards.md:314` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number

### `D10` — **CONFLICT: 2 meanings** (see flags §b)

- [D-rulings] "### D10. `fgo_replay.py` TUM quaternion typo" — `docs/decisions_queue.md:321` — note: queue text (kept as history under "Former OPEN text of D8–D14")
- [D-rulings] "- **D10:** **fix the FGO trajectory-writer quaternion typo.** Check every reported FGO heading or" — `METHODOLOGY.md:6767` — note: ruling 2026-09-30
- [rung-1 data-integrity checklist] "| D10 | **EKF origin in the log** (ruling 1): an `ORGN` record in this boot's dataflash BEFORE the ARM event; the boot's "EKF3 IMUn initialised" messages (every core) precede the origin | yes. If not: no further sortie until the cause is found (a safety stop; NOT a scoring exclusion, since the pre-registration §3.3 is ..." — `docs/rung1_flight_cards.md:315` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number

### `D11` — **CONFLICT: 2 meanings** (see flags §b)

- [D-rulings] "### D11. FGO speed-up route" — `docs/decisions_queue.md:327` — note: queue text (kept as history under "Former OPEN text of D8–D14")
- [D-rulings] "- **D11:** **defer the FGO speed-up**; not needed for SITL. Revisit only for the real drone." — `METHODOLOGY.md:6770` — note: ruling 2026-09-30
- [rung-1 data-integrity checklist] "| D11 | **F7 and U4 as flown:** the sheet's yaw-check line filled in (\|diff\| ≤ 5°); the `ARM` event to take-off (the first `CTUN`/`RFND` climb) ≤ 5 s | yes. A deviation is recorded; it does not change the classification |" — `docs/rung1_flight_cards.md:316` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number

### `D12` — **CONFLICT: 2 meanings** (see flags §b)

- [D-rulings] "### D12. External-estimator backend for the FGO" — `docs/decisions_queue.md:334` — note: queue text (kept as history under "Former OPEN text of D8–D14")
- [D-rulings] "- **D12:** **prefer the external-estimator AHRS backend.** The FGO's estimate and validity go directly" — `METHODOLOGY.md:6771` — note: ruling 2026-09-30
- [rung-1 data-integrity checklist] "| D12 | **M1/M2/M3 as flown (2026-10-12):** no landing (`EV` LAND_COMPLETE / LAND_COMPLETE_MAYBE after a take-off) before this sortie's `ARM` in this boot's log (M1); the sheet's M2 line filled in, and `XKF1` (core 0) √(VN²+VE²+VD²) < 0.2 m/s over the 5 s before `ARM`; if the landing was in LAND mode, the disarm ≤ 2 s ..." — `docs/rung1_flight_cards.md:317` — note: CONFLICT: post-sortie data-integrity check, not the D-ruling of the same number

### `D13`

- [D-rulings] "### D13. Ruling on FGO step 3 (owed: the UKF gate was "step 2 passes AND step 3 is ruled on")" — `docs/decisions_queue.md:344` — note: queue text (kept as history under "Former OPEN text of D8–D14")
- [D-rulings] "- **D13:** **accept FGO step 3 as reported** (input-path cost < 0.1 m, at the 0.13 m noise floor," — `METHODOLOGY.md:6780` — note: ruling 2026-09-30

### `D14`

- [D-rulings] "### D14. Confirm the equivalence-test comparison fixes (the same category as D1)" — `docs/decisions_queue.md:352` — note: queue text (kept as history under "Former OPEN text of D8–D14")
- [D-rulings] "- **D14:** **accept the FGO FE1/FE2 and UKF step-3 matcher fixes as bug fixes**, reporting the first" — `METHODOLOGY.md:6782` — note: ruling 2026-09-30

### `D15`

- [D-rulings] "### D15. UKF take-off yaw kick: adopt EKF3's low-height flow rule? (BLOCKS the UKF flights)" — `docs/decisions_queue.md:268` — note: decision-queue entry
- [D-rulings] "### Ruling D15 (user, 2026-09-30): option (b). The GROUND-PROXIMITY FLOW RULE, defined from EKF3's source BEFORE any re-run" — `METHODOLOGY.md:7038`

### `D16`

- [D-rulings] "### D16. RULED (a), 2026-09-30: P3 yaw miss recorded as worded; flying not blocked (the no-heading flight has since PASSED)" — `docs/decisions_queue.md:214` — note: decision-queue entry
- [D-rulings] "### Ruling D16 (user, 2026-09-30): option (a)" — `METHODOLOGY.md:7454`

### `D17`

- [D-rulings] "### D17. RULED (a) 2026-09-30: UKF heading at EKF3's 5°. V1–V4 all PASS (the with-heading UKF set 3/3)" — `docs/decisions_queue.md:185` — note: decision-queue entry
- [D-rulings] "### Ruling D17 (user, 2026-09-30): option (a), the UKF port's heading input" — `METHODOLOGY.md:7553`

### `D18`

- [D-rulings] "### D18. EKF3's STATIC yaw fusion on the ground (pre-arm gyro-z bias learning): give it to the UKF?" — `docs/decisions_queue.md:171` — note: decision-queue entry
- [D-rulings] "**D18: no. PRINCIPLE, recorded:**" — `METHODOLOGY.md:7785`
- [D-rulings] "- **D18 principle recorded:** sensor-validity rules are shared; design features are not." — `PROGRESS.md:47` — note: later uses ("D18 model correction", "D18 own-bias derotation", "D18 rule") apply this principle; same family

### `D19`

- [D-rulings] "### D19. D12 route and the take-off backlog fix (report: `docs/d12_fgo_backend_report.md`)" — `docs/decisions_queue.md:152` — note: decision-queue entry
- [D-rulings] "**D19: route (a).** The FGO becomes an ArduPilot estimator backend with its own input route." — `METHODOLOGY.md:7794`

### `D20`

- [D-rulings] "### D20. `VISO_DELAY_MS` at half speed: (a) and (b) disagree by 5.4 ms (BLOCKS every half-speed flight)" — `docs/decisions_queue.md:138` — note: decision-queue entry
- [D-rulings] "**D20:** `VISO_DELAY_MS` = **25 ms** at half speed (the receipt measure, as D2)." — `METHODOLOGY.md:8141`

### `D21`

- [D-rulings] "### D21. Half-speed EKF3 set (a) PRIMARY MISS: contact +242.1 s (full speed +186.2; window [+155, +215]). The UKF passed (+198.0 against +163.0)" — `docs/decisions_queue.md:119` — note: decision-queue entry
- [D-rulings] "### Recorded against D21 (user, 2026-10-01)" — `METHODOLOGY.md:8246`

### `D22`

- [D-rulings] "### D22. Half-speed UKF with-heading r3 FAILS B4 (0.296 m/s > 0.25) at cruise +0.5 s; EKF3 half set 3/3 PASS, UKF 2/3 (BLOCKS the FGO gates and flights)" — `docs/decisions_queue.md:102` — note: decision-queue entry
- [D-rulings] "### RULING (user, 2026-10-09): D22 is a SHARED SENSOR-PIPELINE LIMITATION; the fix is planned for real flights only" — `METHODOLOGY.md:12642`
- [D-rulings] "### D22 note RULED (user, 2026-10-01): flow validity uses the feature count only" — `METHODOLOGY.md:8936` — note: D22 also names the start-of-cruise lateral-burst mechanism (D22 plateau/fix/recurrence)

### `D23`

- [D-rulings] "### D23. FGO shadow (a): FG3 fails as worded at the climb top (position max 0.51 m, velocity max 3.8 m/s); FG1 (after a checker fix), FG2 and FG3b pass (BLOCKS the FGO ground test and flights)" — `docs/decisions_queue.md:85` — note: decision-queue entry
- [D-rulings] "### D23 bounded diagnosis (2 h): the FGO climb-top transient is a burst of SHORT LIDAR RETURNS at the climb-to-cruise transition; the 3.8 m/s spike was a checker-proxy artefact" — `METHODOLOGY.md:8646`

### `D24`

- [D-rulings] "### D24. FGO ground test: G5 fails as worded (no disarm), from the harness's sim clock, not the backend — RULED 2026-10-01" — `docs/decisions_queue.md:63` — note: decision-queue entry
- [D-rulings] "### D24 RULED (user, 2026-10-01): G5 of `fgo_groundtest_half` FAILED AS WORDED; harness clock fixed; ground test re-run without the node stop" — `METHODOLOGY.md:8765`

### `D25`

- [D-rulings] "### D25. FGO ground test re-run: G5 fails as worded on PRE-ARM "FGO invalid or stale" text (node start-up clock map stamps states ~4 ms in the future; the backend's uint32 age wraps -> invalid). Arm-hold-disarm itself passes — RULED 2026-10-01: node fix (settled, outlier-robust clock map); confirming shadow ..." — `docs/decisions_queue.md:45` — note: decision-queue entry
- [D-rulings] "**D25: the node fix.**" — `METHODOLOGY.md:9067`

### `D26`

- [D-rulings] "### D26. FGO with-heading set FAILS (2/3) — RULED 2026-10-01: (a)+(b) done (METHODOLOGY "D26 RULED", "D26 (b)"): r3 B5 pitch gyro rms 0.0230 (band 0.0108) at the end-wall heading degradation (y ~ 138-145 m), with the FGO yaw swinging -1.9..+0.6 deg; r1, r2 pass; no-heading flight passed (contact +165.8 s in window)" — `docs/decisions_queue.md:31` — note: decision-queue entry
- [D-rulings] "### D26 RULED (user, 2026-10-01): (a) + (b)" — `METHODOLOGY.md:9387`
- [D-rulings] *(superseded)* "**D26 CORRECTED.** The r3 "B5 failure at the end-wall heading degradation" was a **scoring artefact**: the window" — `METHODOLOGY.md:9957` — note: D26 failure reversed by D28

### `D27`

- [D-rulings] "### D27. Noise parity (plan step 1): closed-loop builds MATCH; OFFLINE the UKF's IMU process noise per second is 1.2x the FGO's (UKF steps 15 ms with EKF3's per-step (dt*NSE)^2 form; FGO conversion pinned to 12.5 ms)" — `docs/decisions_queue.md:19` — note: decision-queue entry
- [D-rulings] "### D27 RULED (user, 2026-10-01): option (b) — the offline UKF's IMU process noise aligned to the same per-second densities as the FGO and the UKF port" — `METHODOLOGY.md:9567`

### `D28`

- [D-rulings] "### D28. — RULED 2026-10-02: (a) scorer fixed, both FGO sets 3/3, D26 corrected. B5 CHECKER BUG reverses both FGO r3 B5 failures (hard-gated cl_fgo_b_tex_r3_half 0.0230 -> 0.0032; robust 0.0212 -> 0.0028 rad/s pitch): a landing-time vy spike set B5's window end to 339 s, taking in the end-of-cruise deceleration" — `docs/decisions_queue.md:8` — note: decision-queue entry
- [D-rulings] "### D28 RULED (user, 2026-10-02): option (a) — B5 window fixed; both FGO with-heading sets restated as 3/3; D26 corrected (both scores kept)" — `METHODOLOGY.md:9940`

### `D29`

- [D-rulings] "### D29. UKF port tag input: tier A failed as worded (D27 Q form), queued 2026-10-08 — RULED (a) 2026-10-08: tier A recorded as failed as worded, with the diagnostic; port accepted on tier B + UR1; not re-registered" — `docs/decisions_queue.md:363` — note: decision-queue entry
- [D-rulings] "**D29 RULED (a).**" — `METHODOLOGY.md:11063`

### `DESCRIPTIVE ONLY`

- [status labels (numbers.md / methodology_index)] "**Stated only alongside the confirmatory EKF3-vs-FGO test, "no ordering claimed"** (r4–r10: mean d −0.021 m, 95% CI [−0.989, +0.947]; row above); the means are descriptive only (restatement ruling 5) | m | DESCRIPTIVE ONLY (FGO-only re-run 2026-10-10; UKF unchanged; restatement ruling 5) | json:rerun_dsn_evo.json, ..." — `docs/thesis/numbers.md:236`
- [status labels (numbers.md / methodology_index)] "textured means at n = 3 are ... descriptive only." — `docs/thesis/final_results_pack.pdf p.1`

### `DIAGNOSTIC` — **CONFLICT: 2 meanings** (see flags §b)

- [DIAGNOSTIC (numbers.md status: adds descriptive record)] "- DIAGNOSTIC: reported but never a gate, or a descriptive record." — `docs/thesis/numbers.md:17` — note: adds "or a descriptive record" to the METHODOLOGY meaning
- [status labels (numbers.md / methodology_index)] "DIAGNOSTIC** (reported, never a gate)." — `METHODOLOGY.md:1149`

### `DIRECTION`

- [re-run comparison flags] "`DIRECTION` marks a changed comparison (ordering sign, arm-effect sign, verdict, side of 1 / 50% / NEES 3); see the script docstring." — `docs/thesis/rerun_old_vs_new.md:3`

### `DRAFT`

- [re-run comparison flags] "**Status: DRAFT.** Nothing here has been copied into `numbers.md` or METHODOLOGY. Every number below was read from the" — `docs/thesis/final_restatement_draft.md:3`

### `empirical re-run gate (standing control)`

- [standing rules] `empirical re-run gate (standing control)` "**METHODOLOGICAL CONTROL — the empirical re-run gate.** The sign fix was supported by" — `METHODOLOGY.md:438`
- [standing rules] `empirical re-run gate (standing control)` "### 2.13 Empirical re-run gate (standing control) ... - **Summary:** Every measurement-model, gate or noise change is gated on a from-scratch ... estimator re-run and reverted if the outcome degrades; offline residuals and innovation" — `docs/thesis/methodology_index.md:347`

### `ESTIMATE`

- [status labels (numbers.md / methodology_index)] "- ESTIMATE: not measured." — `docs/thesis/numbers.md:18`

### `EXPLORATORY`

- [verdict and evidence labels] "- An **EXPLORATORY (not pre-registered)** comparison of the robust FGO against the hard-gated FGO" — `METHODOLOGY.md:8436`

### `FINDING —` — **UNDEFINED** (see flags §a)

- [lifecycle labels] *(used, not defined here)* "### FINDING — the UKF yaw drift is a yaw-capping-frequency effect, NOT a parameterisation difference (diagnosed + FGO-tested)" — `METHODOLOGY.md:941` — note: heading prefix for diagnosed findings (7 headings); the label itself is not defined
- [lifecycle labels] *(used, not defined here)* "## FINDING — the SITL dataflash clock runs ~0.02% slow against Gazebo sim time (2026-09-24)" — `METHODOLOGY.md:1207`
- [lifecycle labels] *(used, not defined here)* "## FINDING — lateral optical-flow sign is wrong in EKF3's input and in the UKF/FGO model (2026-09-29)" — `METHODOLOGY.md:4069`

### `first result` — **UNDEFINED** (see flags §a)

- [verdict and evidence labels] *(used, not defined here)* "- The Python-node set (b) stays recorded as the **first result**. Set (a) (no camera) stands." — `METHODOLOGY.md:6376` — note: no defining text

### `freeze`

- [freeze deadlines] "- simulation freeze **Fri 16 Oct** (no new simulation experiments after it); ... - experiment freeze **Fri 23 Oct**." — `METHODOLOGY.md:7824`
- [freeze deadlines] "Deadlines (user ruling): **FGO closed-loop flights done by Fri 9 Oct**; simulation freeze **Fri 16 Oct**; ... experiment freeze **Fri 23 Oct**." — `docs/plan_to_freeze.md:3`

### `FREEZES`

- [estimator freeze behaviour] "- **EKF3 FREEZES** (`const_pos` on aiding loss): blank displacement **0.20× true** — it stops" — `METHODOLOGY.md:578` — note: different sense: estimator output stops (const_pos), not a status label

### `FROZEN` — **CONFLICT: 2 meanings** (see flags §b)

- [FROZEN = parameters fixed before validation] "### Phase 3 calibration — result (p1c_* only; parameters FROZEN before validation)" — `METHODOLOGY.md:2750` — note: different sense: calibration parameters fixed before validation
- [FROZEN = simulation results frozen] "- **Simulation results are FROZEN:** no new result experiments or re-runs. Verification flights for real-flight ... readiness are allowed, short, under the standing rule." — `METHODOLOGY.md:13399`
- [FROZEN = simulation results frozen] "(simulation results, FROZEN 2026-10-11)" — `docs/thesis/final_results_pack.pdf p.1`

### `METHODOLOGY LESSON: every future prediction carries a numeric threshold`

- [standing rules] "**METHODOLOGY LESSON (standing rule from now on): every future prediction carries a numeric ... threshold.** A verbal criterion such as "roughly unchanged" cannot be scored without" — `METHODOLOGY.md:3535`

### `MISS` — **UNDEFINED** (see flags §a)

- [verdict and evidence labels] *(used, not defined here)* "**2. `fwdc_tex_r2`: recorded as a PRIMARY MISS as worded, not re-scored.**" — `METHODOLOGY.md:5332` — note: no defining text

### `N1`

- [U10 sign-off decisions] "- **(N1) G5 "not computable = FAIL".** When the rung-1 drift rule refuses its initial segment (it moves < 1.0 m" — `docs/u10_replay_gate_band.md:70`

### `N2`

- [U10 sign-off decisions] "- **(N2) G2 coverage of W.** "Throughout W" is read as: the `ukf_shadow.csv` rows cover W, with no gap (including" — `docs/u10_replay_gate_band.md:74`

### `N3`

- [U10 sign-off decisions] "- **(N3) G1 late-PARM rule.** A late geometry PARM passes only if:" — `docs/u10_replay_gate_band.md:76`

### `N4`

- [U10 sign-off decisions] "- **(N4) Single binary.** Every flight in the set must carry the same Replay md5 (`binary.md5`). Mixed → INVALID; a" — `docs/u10_replay_gate_band.md:82`
- [U10 sign-off decisions] "- N4: one Replay binary for the whole set;" — `METHODOLOGY.md:14041` — note: METHODOLOGY summary list N1–N6 (lines 14038–14043)

### `N5`

- [U10 sign-off decisions] "- **(N5) Score↔log precondition.** The score JSON must have been computed on the same Replay output .BIN (sha256)," — `docs/u10_replay_gate_band.md:84`

### `N6`

- [U10 sign-off decisions] "- **(N6) G6 E1 is 3-D, not "horizontal".**" — `docs/u10_replay_gate_band.md:87`

### `PARKED`

- [lifecycle labels] "- **Rung 1** (the logging flight) is the PRIORITY. **Rung 3** (closed loop, UKF/FGO steering) is a PLANNED GOAL. ... **Rung 2** (our own camera pipeline on real hardware) stays PARKED." — `METHODOLOGY.md:13397`

### `PENDING` — **UNDEFINED** (see flags §a)

- [lifecycle labels] *(used, not defined here)* "- **The scale-cause check ("bounded check 5a") is still PENDING.** It is not yet defined" — `METHODOLOGY.md:3196`
- [lifecycle labels] *(used, not defined here)* "### 17.2 H comparative criteria (H-H2, P-H3, H-H4) — computed 2026-10-11 on the re-flown sets, PENDING user ruling" — `docs/thesis/numbers.md:631`
- [lifecycle labels] *(used, not defined here)* "- **PENDING:** finalised when the supervisor confirms the room size. The flight card (`docs/rung1_flight_cards.md`," — `METHODOLOGY.md:14173`

### `PLANNED GOAL`

- [lifecycle labels] "- **Rung 1** (the logging flight) is the PRIORITY. **Rung 3** (closed loop, UKF/FGO steering) is a PLANNED GOAL. ... **Rung 2** (our own camera pipeline on real hardware) stays PARKED." — `METHODOLOGY.md:13397`

### `post hoc` — **UNDEFINED** (see flags §a)

- [verdict and evidence labels] *(used, not defined here)* "- **Post-hoc condition check (clearly labelled POST HOC):** valid airborne flow frames in cruise are" — `METHODOLOGY.md:5343`
- [verdict and evidence labels] *(used, not defined here)* "results were seen: **a post-hoc diagnosis, not a pre-registered pass.**" — `METHODOLOGY.md:10756` — note: contrasted with a pre-registered pass
- [verdict and evidence labels] *(used, not defined here)* "- **E5 uses the increment form** over the paired window, pre-registered here. On 2026-10-11 it was adopted post hoc." — `docs/u10_replay_gate_band.md:271`

### `pre-registered`

- [verdict and evidence labels] "## Pre-registered equivalence band (written 2026-10-08, before the first comparison run)" — `docs/fgo_cpp_port.md:8` — note: glossed in a heading (written before the first comparison run); no general definition sentence
- [verdict and evidence labels] *(used, not defined here)* "**Step 1. Agreement criterion, PRE-REGISTERED before any equivalence test.**" — `METHODOLOGY.md:5458`

### `PRE-REGISTRATION RULE (standing, from 2026-09-24)`

- [standing rules] `PRE-REGISTRATION RULE (standing, from 2026-09-24)` "## PRE-REGISTRATION RULE (standing, from 2026-09-24)" — `METHODOLOGY.md:1142`
- [standing rules] `PRE-REGISTRATION RULE (standing, from 2026-09-24)` "1. **Each criterion is labelled PRIMARY** (it tests the confound directly) **or ... DIAGNOSTIC** (reported, never a gate)." — `METHODOLOGY.md:1148`

### `PRIMARY`

- [status labels (numbers.md / methodology_index)] "1. **Each criterion is labelled PRIMARY** (it tests the confound directly) **or" — `METHODOLOGY.md:1148`

### `PRIORITY`

- [lifecycle labels] "- **Rung 1** (the logging flight) is the PRIORITY. **Rung 3** (closed loop, UKF/FGO steering) is a PLANNED GOAL. ... **Rung 2** (our own camera pipeline on real hardware) stays PARKED." — `METHODOLOGY.md:13397`

### `QUEUED` — **UNDEFINED** (see flags §a)

- [verdict and evidence labels] *(used, not defined here)* "(QUEUED for the user's confirmation)" — `METHODOLOGY.md:5988`

### `R6` — **CONFLICT: 2 meanings** (see flags §b)

- [Experiment H supervisor ruling items (2026-10-08)] "**R6. Recording** (no full-rate forward-camera stream). The exact bag topics:" — `docs/tag_hold_design.md:41` — note: §R "Supervisor ruling 2026-10-08 (incorporated)"
- [rung-1 work items (minimal real-flight plan)] "| R6 | **Real-sensor parameter template** (§3.3) plus bench readback, `DSF` check and the compass arming check | 1.5 d | S1, S3, S4 | draft: yes | **Medium.** Sensor driver setup; compass calibration; the fence-origin question. |" — `docs/minimal_real_flight_plan.md:363` — note: rung-1 item table; restated by number in docs/real_flight_readiness_by_rung.md:53-67

### `REAL`

- [re-run comparison flags] "- **Attribution caveat.** "REAL" below means *produced by today's corrected code on the same inputs*. Which of the" — `docs/thesis/final_restatement_draft.md:13`

### `recorded deviation` — **UNDEFINED** (see flags §a)

- [verdict and evidence labels] *(used, not defined here)* "accepted as a **recorded deviation**" — `METHODOLOGY.md:11105`

### `REPORT ONLY` — **UNDEFINED** (see flags §a)

- [verdict and evidence labels] *(used, not defined here)* "(REPORT ONLY; no change)" — `METHODOLOGY.md:12601`

### `restatement ruling n`

- [status labels (numbers.md / methodology_index)] "cited here as "restatement ruling n", to keep them apart from the earlier 2026-10-10 rulings): §8 counts as computed, with the extended band caveat (1); F3c (b) TRUE, fragile (2); C0 "FGO lower on all 6" with its margin and the 0.1 rad result (3); the plain-wall heading benefit conditional and linked to Phase 3, with ..." — `docs/thesis/numbers.md:38`

### `RESULT`

- [verdict and evidence labels] "**Classification (METHODOLOGY standing rule, 2026-10-10):** every card says whether it is **VERIFICATION** (shortest ... profile that exercises the check; never scored, never reused as result data) or **RESULT** (pre-registered; scored)." — `docs/rung1_flight_cards.md:35`
- [verdict and evidence labels] "Per the standing rule, every sortie is classified IN ADVANCE. **Verification sorties are never scored and never reused ... as result data**, whatever they show. Their logs may be used ONLY for the purposes listed (and for §6's timing" — `docs/rung1_preregistration.md:74`

### `RULED` — **UNDEFINED** (see flags §a)

- [verdict and evidence labels] *(used, not defined here)* "**EKF3: RULED (user, 2026-09-29). See "RULING — EKF3 in the offline forward-camera" — `METHODOLOGY.md:1836`

### `RULING` — **UNDEFINED** (see flags §a)

- [verdict and evidence labels] *(used, not defined here)* "### RULING (user, 2026-09-24): the IMU gap-share miss is benign" — `METHODOLOGY.md:1675` — note: heading form "RULING (user, date): title"; no definition sentence

### `STANDING RULE (user, 2026-10-10): verification flights are SHORT and never result data`

- [standing rules] "### STANDING RULE (user, 2026-10-10): verification flights are SHORT and never result data" — `METHODOLOGY.md:13096`
- [standing rules] "- **Verification flights** (smoke tests, ground tests, safety tests, timing or pipeline checks, fix verification) use ... the SHORTEST profile that exercises the thing being checked, typically 1–2 minutes. Each spec states why that length ... suffices." — `METHODOLOGY.md:13097`

### `STANDING RULE — every ATE states its metric wherever it is quoted`

- [standing rules] "## STANDING RULE — every ATE states its metric wherever it is quoted" — `METHODOLOGY.md:7` — note: amended 2026-09-24 to name the window (line 21)
- [standing rules] "### 4.4 STANDING RULE on metrics (label every ATE, never compare across metrics)" — `docs/thesis/methodology_index.md:459`

### `STANDING RULE — scope control (user, 2026-09-24)`

- [standing rules] `STANDING RULE — scope control (user, 2026-09-24)` "## STANDING RULE — scope control (user, 2026-09-24)" — `METHODOLOGY.md:1155`
- [standing rules] `STANDING RULE — scope control (user, 2026-09-24)` "**Before starting any work that is not in the phase brief, ask:** ... - **(a)** does it change a thesis claim? ... - **(b)** would a reviewer's objection stand without it?" — `METHODOLOGY.md:1157`

### `Standing rule: any live PARAM_SET goes into a .parm file the same session`

- [standing rules] "any live `PARAM_SET` must be written into a `.parm` file in the same session." — `CLAUDE.md:744` — note: CLAUDE.md Hidden Configuration Audit; restated methodology_index:177

### `STANDING RULE: ceiling datasets vs dsn_* on the transition world need the ceiling effect size`

- [standing rules] "**STANDING RULE: no comparison between the ceiling datasets (`fwdc_*`, `fwdplainc_*`) ... and `dsn_*` on the transition world without stating this effect size.** It does not" — `METHODOLOGY.md:2622`
- [standing rules] "The ceiling vs no-ceiling transition-flow effect size (+0.43 px/s, p = 0.31) must be" — `CLAUDE.md:127`

### `STANDING RULE: EKF3 on fwd_* never compared with EKF3 on dsn_* without the flow-latency difference`

- [standing rules] "**STANDING RULE: EKF3 on `fwd_*` is never compared with EKF3 on `dsn_*` without stating ... the flow-latency difference** (median and p95, per world, from `eval/input_timing.py`)." — `METHODOLOGY.md:1828`
- [standing rules] "### 3.5 Latency standing rules" — `docs/thesis/methodology_index.md:413`

### `Standing rule: excitation check for any new sensor model`

- [standing rules] "**Standing rule from 2026-09-29: any new sensor model gets an excitation check before use.** ... Each axis it measures must be excited deliberately, and its sign and scale regressed against ... truth." — `METHODOLOGY.md:4244`

### `Standing rule: no file a running batch uses is edited while it runs`

- [standing rules] "- **Standing rule (confirmed by the user):** no file a running batch uses is edited while it ... runs; changes are held as patches until the batch ends." — `METHODOLOGY.md:5116`

### `Standing rule: the UKF/FGO are not replayed on unusable bags`

- [standing rules] "- The UKF/FGO are not replayed on unusable bags (standing rule)." — `METHODOLOGY.md:9807`

### `SUPERSEDED`

- [SUPERSEDED (world sets: kept, not analysed)] "**SUPERSEDED** (kept, not analysed) |" — `CLAUDE.md:118` — note: world-set status: kept, not analysed
- [status labels (numbers.md / methodology_index)] "SUPERSEDED = replaced; the replacing entry is" — `docs/thesis/methodology_index.md:25`
- [status labels (numbers.md / methodology_index)] "- **Superseded values** appear only in the last section, each with what superseded it." — `docs/thesis/numbers.md:20`

### `U4` — **CONFLICT: 2 meanings** (see flags §b)

- [UKF-only closed-loop costing items] "| U4 | **Ground initialisation** when the rangefinder reads below its minimum | the port initialises only on a Good downward range above `RNG_MIN` (fork `AP_NavUKF.cpp:493,524`; fork-r1 607,641) | initialise from `RNGFNDn_GNDCLR` (plus the lever arm) while disarmed and `OutOfRangeLow` [correction 2026-10-12: NOT "as ..." — `docs/ukf_only_closed_loop_costing.md:68` — note: §1 "What it needs, with effort"
- [UKF-only closed-loop costing items] "7. **U4:** a flight-card rule NOW: take off within 5 s of arming. A proper fix is deferred to the closed-loop work." — `METHODOLOGY.md:13904` — note: ruling item 7: card rule derived from U4 (take off within 5 s of arming); restated in docs/rung1_flight_cards.md:10
- [UKF-only closed-loop costing items] *(superseded)* "- The "as EKF3 does" wording is WRONG in three places: the costing U4 row, plan R-e, and rung-1 prereg §9 item 11." — `METHODOLOGY.md:13808` — note: "as EKF3 does" wording in the costing U4 row declared wrong; implemented as a PORT rule
- [real-flight unknowns from the user (readiness §0)] "| U4 | **Downward camera and lens.** Interface: CSI/libcamera or USB/V4L2. Global or rolling shutter. | A3, D1, D3, D4 |" — `docs/real_flight_readiness.md:39` — note: §0 "Required inputs from the user (unknown; not assumed)"

### `UNCLEAR` — **UNDEFINED** (see flags §a)

- [re-run comparison flags] *(used, not defined here)* "| **UNCLEAR** | **0** | — |" — `docs/thesis/final_restatement_draft.md:28` — note: appears only as a class with count 0; no definition sentence

### `VERDICT`

- [re-run comparison flags] "`final_old_vs_new.md` has 95 flagged rows: 86 DIRECTION and 9 VERDICT. The header calls all 95 "direction flags"." — `docs/thesis/final_restatement_draft.md:22` — note: counted alongside DIRECTION; no separate definition sentence

### `VERIFICATION`

- [verdict and evidence labels] "**Classification (METHODOLOGY standing rule, 2026-10-10):** every card says whether it is **VERIFICATION** (shortest ... profile that exercises the check; never scored, never reused as result data) or **RESULT** (pre-registered; scored)." — `docs/rung1_flight_cards.md:35`
- [verdict and evidence labels] "Per the standing rule, every sortie is classified IN ADVANCE. **Verification sorties are never scored and never reused ... as result data**, whatever they show. Their logs may be used ONLY for the purposes listed (and for §6's timing" — `docs/rung1_preregistration.md:74`

### `VOID` — **CONFLICT: 2 meanings** (see flags §b)

- [VOID = metric invalid as a measurement] "**⚠️ VOID as an EKF3 measurement** — computed from `/ekf/pose`, which is ... simulator ground truth under `AHRS_EKF_TYPE=10`, not the EKF3 estimate." — `CLAUDE.md:493` — note: VOID for a metric that compared truth with truth
- [VOID = metric invalid as a measurement] "| Stage B ATE / RPE (`/ekf/pose`) | RMSE **6.4 mm** / RMSE **4.6 mm** | mm | SUPERSEDED (VOID) | C:L403, C:L405 | `/ekf/pose` was simulator truth (`AHRS_EKF_TYPE=10`), C:L345-L356 |" — `docs/thesis/numbers.md:760` — note: status written SUPERSEDED (VOID)
- [VOID = run not a result] "**Run 1 (`gt_heading_half`) VOID: an environmental failure, not a result.**" — `METHODOLOGY.md:7846`

### `WITHDRAWN`

- [status labels (numbers.md / methodology_index)] "Withdrawn claims stay in place, marked **WITHDRAWN** with the reason. Old → new:" — `docs/thesis/numbers.md:33`

### `⚑` — **CONFLICT: 2 meanings** (see flags §b)

- [numbers.md discrepancy flag] "- **Discrepancies** between sources are flagged with ⚑ in the quantity cell and collected in the second-last" — `docs/thesis/numbers.md:25`
- [restatement-draft change flag] "Legend: ⚑ = a verdict, ordering or wording change. Plain = a magnitude only." — `docs/thesis/final_restatement_draft.md:145` — note: CONFLICT: here the flag = a verdict/ordering/wording change, not a source discrepancy

## 9. Scripts (tools/ and eval/)


### `eval/apin_extract.py`

- [scripts] """"Input-path diagnostic (user ruling 2026-10-08; docs/handovers/2026-10-08_input_path_diagnostic.md): extract the" — `eval/apin_extract.py:2`

### `eval/b5_window_check.py`

- [scripts] """"B5 window check (2026-10-02, a CHECKER BUG found in the robust-FGO set): closed_loop_score.py's B5 window is" — `eval/b5_window_check.py:2`

### `eval/bin2fgo.py`

- [scripts] """"Rung 1, item R1: ArduPilot dataflash (LOG_REPLAY=1) -> the FGO's input event stream." — `eval/bin2fgo.py:2`

### `eval/bin2fgo_accept.py`

- [scripts] """"Rung 1: the CONVERTER ACCEPTANCE BAND on a real log (pre-registered 2026-10-12, docs/rung1_preregistration.md" — `eval/bin2fgo_accept.py:2`

### `eval/bin2fgo_default_check.py`

- [scripts] """"R1 default-unchanged check, level (a): the geometry parametrisation leaves the SIM path BYTE-IDENTICAL." — `eval/bin2fgo_default_check.py:2`

### `eval/bin2fgo_sitl_check.py`

- [scripts] """"R1 hardware-free acceptance checks: eval/bin2fgo.py's output from a SITL LOG_REPLAY log against the SAME flight's" — `eval/bin2fgo_sitl_check.py:2`

### `eval/bin2fgo_test.py`

- [scripts] """"Tests of eval/bin2fgo.py's capture-delay configuration (2026-10-12) and of the converter acceptance band checker" — `eval/bin2fgo_test.py:1`

### `eval/blank_behaviour.py`

- [scripts] """"Behaviour under total loss of flow aiding (user ruling 2026-09-29, consolidated re-run)." — `eval/blank_behaviour.py:2`

### `eval/build_5b_sandbox.sh`

- [scripts] "# Build a Phase 5b sandbox HOME for the current trials and write its jobs file (the old" — `eval/build_5b_sandbox.sh:2`

### `eval/ceiling_flow_effect.py`

- [scripts] """"Transition-world forward flow: ceiling vs no-ceiling effect size (user ruling" — `eval/ceiling_flow_effect.py:2`

### `eval/cl_yaw_prediction.py`

- [scripts] """"Basis for the closed-loop Part 2 bands at the ruled EKF3 yaw sigma (5.00 deg, the" — `eval/cl_yaw_prediction.py:2`

### `eval/climb_top_response.py`

- [scripts] """"Climb-top response (D23; for the FGO flight predictions). Per flight: the flying estimator's output height" — `eval/climb_top_response.py:2`

### `eval/closed_loop_score.py`

- [scripts] """"Score a closed-loop flight against its PRE-REGISTERED criteria (METHODOLOGY "Part 2 — revised" — `eval/closed_loop_score.py:2`

### `eval/cruise_window.py`

- [scripts] """"The pinned cruise window: defined once here, imported by every evaluation script." — `eval/cruise_window.py:1`

### `eval/cruise_window_audit.py`

- [scripts] """"Cruise-window audit (user ruling 2026-10-02, after D28): can a spurious ground-truth sample change the PINNED" — `eval/cruise_window_audit.py:2`

### `eval/d8_ekf3_retime.py`

- [scripts] """"D8 DIAGNOSTIC (ruling 2026-09-30; never replaces the dataset results): EKF3's own cost from fusing" — `eval/d8_ekf3_retime.py:2`

### `eval/d15_compare.py`

- [scripts] """"D15: old (eval/results_pre_d15) vs new (eval/results) for every numbers.md row the rule can move." — `eval/d15_compare.py:2`

### `eval/d15_drift.py`

- [scripts] """"D15 item 5 basis: each estimator's heading drift over the PINNED cruise window (three_way_eval.cruise_window):" — `eval/d15_drift.py:2`

### `eval/d15_kick.py`

- [scripts] """"D15 item 3: the take-off yaw change, DEFINED as in METHODOLOGY (P2 finding, table "UKF yaw change at" — `eval/d15_kick.py:2`

### `eval/d15_pipeline.sh`

- [scripts] "# D15 re-run (user ruling 2026-09-30, option (b)): the ground-proximity flow rule (METHODOLOGY" — `eval/d15_pipeline.sh:2`

### `eval/d15_port_score.py`

- [scripts] """"D15: score the UKF PORT run in Replay (ukf_shadow.csv, SITL clock) as three_way_eval scores EKF3: against the" — `eval/d15_port_score.py:2`

### `eval/d15_rule_audit.py`

- [scripts] """"D15 per-bag audit: did the ground-proximity rule fire in every UKF/FGO replay of the re-run?" — `eval/d15_rule_audit.py:2`

### `eval/d24_clock_equiv.py`

- [scripts] """"D24: old vs new fly_trial.sim_time_now_s on a recorded MAVProxy tlog (file playback, non-blocking reads)." — `eval/d24_clock_equiv.py:1`

### `eval/d25_clockmap_check.py`

- [scripts] """"D25: old vs new fgo_node._sitl_us on a recorded /imu/time_ref stream (arrival order = bag order), queried at" — `eval/d25_clockmap_check.py:2`

### `eval/d25_shadow_check.py`

- [scripts] """"D25 confirming shadow (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION: D25 confirming shadow run"):" — `eval/d25_shadow_check.py:2`

### `eval/d26_fgo_gate.py`

- [scripts] """"D26 (b), EXPLORATORY: the FGO's own treatment of the heading stream near the end wall, from the node-core replay" — `eval/d26_fgo_gate.py:2`

### `eval/d26_heading_stream.py`

- [scripts] """"D26 (b), EXPLORATORY: the heading stream the estimators received in a flight (logs/heading_bridge.csv, sent rows)," — `eval/d26_heading_stream.py:2`

### `eval/d26_jitter_control.py`

- [scripts] """"D26 (b), EXPLORATORY: does the flying estimator's fast heading jitter become control activity in closed loop?" — `eval/d26_jitter_control.py:2`

### `eval/d26_ukf_ekf3_gate.py`

- [scripts] """"D26 (b), EXPLORATORY: the same heading stream through the UKF port's gate (Replay of the flight's own log with" — `eval/d26_ukf_ekf3_gate.py:2`

### `eval/d27_compare.py`

- [scripts] """"D27 (b): old (eval/results_preD27/) vs new (eval/results/) for every regenerated result. Every numeric or string" — `eval/d27_compare.py:2`

### `eval/d27_regen.sh`

- [scripts] "# D27 (b): regenerate every offline-UKF-dependent result from the re-run UKF replays (batches/d27_ukf_rerun_v2.jobs)," — `eval/d27_regen.sh:2`

### `eval/df_reader.py`

- [scripts] """"A strict, self-contained ArduPilot dataflash (.BIN) reader for the rung-1 scorer (2026-10-12)." — `eval/df_reader.py:2`

### `eval/diag/board_h743/analyse_elf.py`

- [scripts] """"board-h743 (2a): flash/RAM breakdown of the thesis backends from a build's nm dump (nm -C --size-sort -S)." — `eval/diag/board_h743/analyse_elf.py:2`

### `eval/diag/board_h743/build_board.sh`

- [scripts] "# board-h743 (2a, 2026-10-11): build Copter for one ChibiOS board, with or without the thesis UKF/FGO backends" — `eval/diag/board_h743/build_board.sh:2`

### `eval/diag/board_h743/build_sitl.sh`

- [scripts] "# board-h743 (2a, 2026-10-11): SITL rebuild of the board-h743 working tree (Replay, UKF_Equiv, the copter SITL binary)," — `eval/diag/board_h743/build_sitl.sh:2`

### `eval/diag/board_h743/collect.py`

- [scripts] """"board-h743 (2a): collect the text results (no binaries) into thesis_ws eval/results/board_h743/." — `eval/diag/board_h743/collect.py:2`

### `eval/diag/board_h743/dbg_chibios.sh`

- [scripts] "# board-h743: show why the ChibiOS_lib make step fails (verbose, one job)" — `eval/diag/board_h743/dbg_chibios.sh:2`

### `eval/diag/board_h743/edit_io.py`

- [scripts] """"board-h743 (2a): route AP_NavUKF.cpp's Replay-only stdio through ukf_fopen/ukf_fprintf/ukf_fflush (no-ops on a board)." — `eval/diag/board_h743/edit_io.py:2`

### `eval/diag/board_h743/equiv_identity.sh`

- [scripts] "# board-h743 (2a): (iii) UKF_Equiv byte-identity, new build vs the installed binary and the stored 2026-10-09 port outputs. One heavy.py step." — `eval/diag/board_h743/equiv_identity.sh:2`

### `eval/diag/board_h743/map_by_lib.py`

- [scripts] """"board-h743 (2a): flash (text+rodata+data init) and RAM (bss/data) per ArduPilot library, from a build's Linker.map" — `eval/diag/board_h743/map_by_lib.py:2`

### `eval/diag/board_h743/sitl_identity.sh`

- [scripts] "# board-h743 (2a): SITL byte-identity of the board-h743 build (6280a35745 source) against" — `eval/diag/board_h743/sitl_identity.sh:2`

### `eval/diag/board_h743/stack_usage.py`

- [scripts] """"board-h743: recompile the thesis estimator sources for a board with -fstack-usage (output to scratch, the build tree" — `eval/diag/board_h743/stack_usage.py:2`

### `eval/diag/board_h743/subinit_h7.sh`

- [scripts] "# board-h743 stage: init the submodules a SITL + ChibiOS build needs, referencing the main checkout (no network fetch)." — `eval/diag/board_h743/subinit_h7.sh:2`

### `eval/diag/fgo_tilt_trace/bagdump.py`

- [scripts] """"Dump bag topics needed for the tilt trace into an npz (diagnostic)." — `eval/diag/fgo_tilt_trace/bagdump.py:1`

### `eval/diag/fgo_tilt_trace/climb.py`

- [scripts] """"Tag fixes around take-off: count, error vs GT (W frame from h_score: N_W = y - 4.998, E_W = x), per 1 s bin." — `eval/diag/fgo_tilt_trace/climb.py:1`

### `eval/diag/fgo_tilt_trace/diag_replay.py`

- [scripts] """"DIAGNOSTIC wrapper around the UNCHANGED room_fgo_replay.py (FGO tilt trace, 2026-10-09). Not a result." — `eval/diag/fgo_tilt_trace/diag_replay.py:1`

### `eval/diag/fgo_tilt_trace/flowres.py`

- [scripts] """"Flow residual against the shared model evaluated on GROUND TRUTH (velocity, attitude, height) + raw gyro, per 0.5 s bin." — `eval/diag/fgo_tilt_trace/flowres.py:1`

### `eval/diag/fgo_tilt_trace/h_score_diag.py`

- [scripts] """"Experiment H scorer, S1 (METHODOLOGY "Experiment H: pre-registration"). One flight:" — `eval/diag/fgo_tilt_trace/h_score_diag.py:2`

### `eval/diag/fgo_tilt_trace/pimcov.py`

- [scripts] """"Does setBiasAccOmegaInit enter the preintegrated covariance in this gtsam build? (diagnostic)" — `eval/diag/fgo_tilt_trace/pimcov.py:1`

### `eval/diag/fgo_tilt_trace/reg.py`

- [scripts] """"Relation of the estimate's roll/pitch to GT roll/pitch: gain and lag (diagnostic)." — `eval/diag/fgo_tilt_trace/reg.py:1`

### `eval/diag/fgo_tilt_trace/run_2.sh`

- [scripts] "# FGO tilt trace, batch 2: the safety flights (to the failure) base vs binit0, and the full-length H_s1_r1 binit0." — `eval/diag/fgo_tilt_trace/run_2.sh:2`

### `eval/diag/fgo_tilt_trace/run_3.sh`

- [scripts] "# FGO tilt trace, batch 3: the residual take-off pitch offset on H_safety_fgo_b (binit0 + one more knob each), to 60 s." — `eval/diag/fgo_tilt_trace/run_3.sh:2`

### `eval/diag/fgo_tilt_trace/run_4.sh`

- [scripts] "# FGO tilt trace, batch 4: the residual take-off tilt offset, binit0 + window / climb-flow knobs, through the hover window." — `eval/diag/fgo_tilt_trace/run_4.sh:2`

### `eval/diag/fgo_tilt_trace/run_s1.sh`

- [scripts] "# FGO tilt trace: diagnostic replays of H_s1_r1 (to t = 130 s), one knob at a time. Scratch output only." — `eval/diag/fgo_tilt_trace/run_s1.sh:2`

### `eval/diag/fgo_tilt_trace/run_score.sh`

- [scripts] "# FGO tilt trace: score H_s1_r1 tag losses with a scratch copy of eval/h_score.py (only the FGO track path is switchable)." — `eval/diag/fgo_tilt_trace/run_score.sh:2`

### `eval/diag/fgo_tilt_trace/spec.py` — **UNDEFINED** (see flags §a)

- [scripts] *(used, not defined here)* "import sys, numpy as np" — `eval/diag/fgo_tilt_trace/spec.py:1` — note: no module docstring or header comment

### `eval/diag/fgo_tilt_trace/tagatt.py`

- [scripts] """"Is the tag-fix error coupled to the TRUE attitude (roll/pitch) of the vehicle? Regress tag err on GT roll/pitch." — `eval/diag/fgo_tilt_trace/tagatt.py:1`

### `eval/diag/fgo_tilt_trace/tagerr.py`

- [scripts] """"Tag-fix error vs GT (rigid 2D fit W<-world), its spectrum, and its relation to the FGO roll/pitch error." — `eval/diag/fgo_tilt_trace/tagerr.py:1`

### `eval/diag/fgo_tilt_trace/tilt.py` — **UNDEFINED** (see flags §a)

- [scripts] *(used, not defined here)* "import sys, numpy as np" — `eval/diag/fgo_tilt_trace/tilt.py:1` — note: no module docstring or header comment

### `eval/diag/h10/analyse_h10.py`

- [scripts] """"H10 verification flight h10_guard_check: score the pre-registered criteria (docs/h10_guard_check_prereg.md) from the" — `eval/diag/h10/analyse_h10.py:2`

### `eval/diag/initial_sigma_audit/c1_metrics.py`

- [scripts] """"C1 verification metrics (venv-ardupilot): fwdplainc_tex_r1 FGO heading arm, for the stored output (1e-3 rad yaw / 2 deg" — `eval/diag/initial_sigma_audit/c1_metrics.py:2`

### `eval/diag/initial_sigma_audit/runtime_estimate.py`

- [scripts] """"Runtime estimate for the FGO-only pass (FINAL_FGO_ONLY=1) from the full re-run's own records (2026-10-09/10):" — `eval/diag/initial_sigma_audit/runtime_estimate.py:2`

### `eval/diag/model_audit/build.sh`

- [scripts] "# Model audit (DIAGNOSTIC): copy EKF3's generated covariance-prediction block verbatim and build the harness." — `eval/diag/model_audit/build.sh:2`

### `eval/diag/model_audit/free_inertial.py`

- [scripts] """"Model audit (2026-10-09), DIAGNOSTIC: free-inertial covariance growth of EKF3, the UKF and the FGO on the SAME 10 s" — `eval/diag/model_audit/free_inertial.py:1`

### `eval/diag/model_audit/fusion_rates.py`

- [scripts] """"Model audit (2026-10-09), DIAGNOSTIC: effective fusion RATE of flow and range per estimator (item 2)." — `eval/diag/model_audit/fusion_rates.py:1`

### `eval/diag/model_audit/heading_S.py`

- [scripts] """"Model audit (2026-10-09), DIAGNOSTIC: heading innovation covariance S, UKF against the FGO before and after the" — `eval/diag/model_audit/heading_S.py:1`

### `eval/diag/model_audit/imu_window.py`

- [scripts] """"Model audit (2026-10-09), DIAGNOSTIC: extract the shared 10 s IMU window and the sensor arrival stamps." — `eval/diag/model_audit/imu_window.py:1`

### `eval/diag/model_audit/meas_probe.py`

- [scripts] """"Model audit (2026-10-09), DIAGNOSTIC: the measurement noise each estimator's CODE actually applies (item 2)." — `eval/diag/model_audit/meas_probe.py:1`

### `eval/diag/model_audit/tables.py`

- [scripts] """"Model audit (2026-10-09), DIAGNOSTIC: markdown tables from free_inertial.py outputs (variance ratios, flag > 2x)." — `eval/diag/model_audit/tables.py:1`

### `eval/diag/model_audit/ukf_dump_bias.py`

- [scripts] """"Model audit (2026-10-09), DIAGNOSTIC: the UKF's in-flight gyro/accel-bias variance from a UKF_DUMP replay (scratch)," — `eval/diag/model_audit/ukf_dump_bias.py:1`

### `eval/diag/plainwall_trace/a1.py` — **UNDEFINED** (see flags §a)

- [scripts] *(used, not defined here)* "import numpy as np, sys, math" — `eval/diag/plainwall_trace/a1.py:1` — note: no module docstring or header comment

### `eval/diag/plainwall_trace/a2.py`

- [scripts] """"Per bag: the first heading measurements, their NIS/accept in FGO and UKF, the meas error vs GT," — `eval/diag/plainwall_trace/a2.py:1`

### `eval/diag/plainwall_trace/a3.py`

- [scripts] """"Stored Phase-4 outputs: (1) the late FGO acceptances are wrap-through passes (yaw error mod 360 ~ 0);" — `eval/diag/plainwall_trace/a3.py:1`

### `eval/diag/plainwall_trace/a4.py`

- [scripts] """"Evaluate the diagnostic replays (scratch) against the stored Phase-4 arms, with the same evo -a (cruise)" — `eval/diag/plainwall_trace/a4.py:1`

### `eval/diag/plainwall_trace/a5.py`

- [scripts] """"Per-keyframe gyro-z bias and yaw around the first heading acceptances, from the equivalence dumps" — `eval/diag/plainwall_trace/a5.py:1`

### `eval/diag/plainwall_trace/fig.py`

- [scripts] """"Figure for the plain-wall divergence trace (fwdplainc_tex_r1): (a) yaw error, first 3 s after the first heading;" — `eval/diag/plainwall_trace/fig.py:1`

### `eval/diag/plainwall_trace/run1.sh`

- [scripts] "# Plain-wall divergence trace (2026-10-10): diagnostic replays, outputs to scratch only." — `eval/diag/plainwall_trace/run1.sh:2`

### `eval/diag/plainwall_trace/run2.sh`

- [scripts] "# Re-run of the y0s1 FGO on fwdplainc_tex_r1 without the equivalence dump (the dump refuses F-variants)." — `eval/diag/plainwall_trace/run2.sh:2`

### `eval/diag/plainwall_trace/unpack.sh`

- [scripts] "# Decompress scratch COPIES of the packed bags (read-only on the trial directories)." — `eval/diag/plainwall_trace/unpack.sh:2`

### `eval/diag/plainwall_trace/watch.sh`

- [scripts] "# Wait loop: reports each job exit; stops on BOTHDONE, on both.sh dying, or after ~29 min." — `eval/diag/plainwall_trace/watch.sh:2`

### `eval/diag/port_merge_u4/ahrs_type_of_trials.py` — **UNDEFINED** (see flags §a)

- [scripts] *(used, not defined here)* "import os, sys, time" — `eval/diag/port_merge_u4/ahrs_type_of_trials.py:1` — note: no module docstring or header comment

### `eval/diag/port_merge_u4/driver_inst.sh`

- [scripts] "# 2026-10-12: byte-identity re-check of the INSTALLED Replay (~/ardupilot_ukf build, ukf-jitter-fix = rung1-geometry" — `eval/diag/port_merge_u4/driver_inst.sh:2`

### `eval/diag/port_merge_u4/driver_u4.sh`

- [scripts] "# U4 (2026-10-12): regression + positive test of the u4-gndclr scratch Replay. One heavy.py step per Replay." — `eval/diag/port_merge_u4/driver_u4.sh:2`

### `eval/diag/port_merge_u4/equiv_inst.sh`

- [scripts] "# 2026-10-12: the INSTALLED UKF_Equiv (built from ukf-jitter-fix = rung1-geometry 16535f9a29) on the stored 2026-10-09" — `eval/diag/port_merge_u4/equiv_inst.sh:2`

### `eval/diag/port_merge_u4/install_build.sh`

- [scripts] "# 2026-10-12: install build of the merged ukf-jitter-fix (= rung1-geometry 16535f9a29): Replay and UKF_Equiv ONLY," — `eval/diag/port_merge_u4/install_build.sh:2`

### `eval/diag/port_merge_u4/u4_build.sh`

- [scripts] "# U4 (2026-10-12): scratch SITL build of the u4-gndclr working tree (Replay, UKF_Equiv, and the copter target as a" — `eval/diag/port_merge_u4/u4_build.sh:2`

### `eval/diag/port_merge_u4/u4_compare.py`

- [scripts] """"U4 positive test (2026-10-12): the u4-gndclr Replay with UKF_TEST_RNG_LOW=0.15 ('low') against its default run" — `eval/diag/port_merge_u4/u4_compare.py:1`

### `eval/diag/port_merge_u4/u4_subinit.sh`

- [scripts] "# U4 (2026-10-12): init the submodules a SITL build needs in the scratch worktree, by --reference to the main checkout" — `eval/diag/port_merge_u4/u4_subinit.sh:2`

### `eval/diag/r1_scoring/rawscan.py`

- [scripts] """"Raw scan of a dataflash log: FMT table, then a strict walk (header A3 95 + type, length from FMT); counts per type," — `eval/diag/r1_scoring/rawscan.py:1`

### `eval/diag/r1_scoring/xuko_replay.sh`

- [scripts] "# One Replay of a log with no UKF FMT records (cl_a_tex_half, EKF3-flown) by the INSTALLED fork Replay (be7c4d18," — `eval/diag/r1_scoring/xuko_replay.sh:2`

### `eval/diag/r1_ukf_port/build.sh`

- [scripts] "# rung-1 UKF port (2026-10-11): build Replay, UKF_Equiv and the copter SITL target from the scratch worktree of" — `eval/diag/r1_ukf_port/build.sh:2`

### `eval/diag/r1_ukf_port/cmp_a.py`

- [scripts] """"(a) byte-identity table, old vs each new variant, plus the size of any difference in ukf_shadow.csv." — `eval/diag/r1_ukf_port/cmp_a.py:2`

### `eval/diag/r1_ukf_port/driver_a2.sh`

- [scripts] "# (a2) after the FLOW_TYPE gate: re-run the new build's default and UKF_GEOM_SITL=1 variants on the five logs (all" — `eval/diag/r1_ukf_port/driver_a2.sh:2`

### `eval/diag/r1_ukf_port/driver_a.sh`

- [scripts] "# (a) old vs new Replay regression: 5 logs x {old, new, new+GEOM_SITL, new+DEROT_ROFH, new+both}. Each Replay is one" — `eval/diag/r1_ukf_port/driver_a.sh:2`

### `eval/diag/r1_ukf_port/equiv_c.sh`

- [scripts] "# (c) UKF_Equiv, old (installed, abb0357d0f, md5 537e0dcd; read-only use) vs new (scratch build), on the existing" — `eval/diag/r1_ukf_port/equiv_c.sh:2`

### `eval/diag/r1_ukf_port/peek.py`

- [scripts] """"Peek at a .BIN: selected PARM values and counts of the replay/UKF records." — `eval/diag/r1_ukf_port/peek.py:2`

### `eval/diag/r1_ukf_port/run_one.sh`

- [scripts] "# One Replay run (one heavy step): run_one.sh <outdir> <replay-binary> <log.bin> [ENV=VAL ...]" — `eval/diag/r1_ukf_port/run_one.sh:2`

### `eval/diag/u10_audit/gate_demo.sh`

- [scripts] "# U10 gate demo RE-RUN (2026-10-12, stage u10_g5_audit_rebase) with the audited eval/u10_gate.py. PLUMBING ONLY:" — `eval/diag/u10_audit/gate_demo.sh:2`

### `eval/diag/u10_audit/port/rebase.sh`

- [scripts] "# Rebase board-h743 and u4-gndclr onto f30f6ffa2f (ukf-jitter-fix) in temporary worktrees; board-h743 also gets the" — `eval/diag/u10_audit/port/rebase.sh:2`

### `eval/diag/u10_audit/port/u4_build.sh`

- [scripts] "# ONE heavy step (run under heavy.py): SITL Replay build of the rebased u4-gndclr worktree. Never installs." — `eval/diag/u10_audit/port/u4_build.sh:2`

### `eval/diag/u10_audit/port/u4_driver.sh`

- [scripts] "# Byte-identity of the rebased u4-gndclr Replay against the INSTALLED Replay 3c3b62bb on the 5 SITL LOG_REPLAY logs:" — `eval/diag/u10_audit/port/u4_driver.sh:2`

### `eval/diag/u10_audit/port/u4_prep.sh`

- [scripts] "# A temporary detached worktree of the REBASED u4-gndclr, with the submodules a SITL Replay build needs, initialised by" — `eval/diag/u10_audit/port/u4_prep.sh:2`

### `eval/diag/u10_audit/port/wait_clear.sh`

- [scripts] "# Wait until no flight runs: FLIGHT_LOCK absent AND no arducopter / gz sim process (exact comm names), polling every" — `eval/diag/u10_audit/port/wait_clear.sh:2`

### `eval/diag/u10_audit/port/when_clear.sh`

- [scripts] "# when_clear.sh <limit_s> <script> [args]: poll every 5 s (FLIGHT_LOCK absent, no arducopter, no gz sim, no BUILD_LOCK)," — `eval/diag/u10_audit/port/when_clear.sh:2`

### `eval/diag/u10_final/build.sh`

- [scripts] "# U10 rule 2 (2026-10-12): scratch SITL build of the replay-rukx worktree: Replay, UKF_Equiv, and the copter target as" — `eval/diag/u10_final/build.sh:2`

### `eval/diag/u10_final/check_all.sh`

- [scripts] "# U10 rule 2: check_rukx.py on the five Replay outputs of a build (tag), against the installed e82c050b outputs." — `eval/diag/u10_final/check_all.sh:2`

### `eval/diag/u10_final/check_rukx.py`

- [scripts] """"U10 rule 2 verification (2026-10-12) on a Replay output log of the replay-rukx build (UKF records renamed RUK* in" — `eval/diag/u10_final/check_rukx.py:2`

### `eval/diag/u10_final/commit_port.sh`

- [scripts] "# Commit the U10 rule-2 port change on replay-rukx (scratch worktree)." — `eval/diag/u10_final/commit_port.sh:2`

### `eval/diag/u10_final/driver.sh`

- [scripts] "# U10 rule 2 (2026-10-12): Replay a build on the five SITL LOG_REPLAY logs (one heavy.py step per Replay), keep the" — `eval/diag/u10_final/driver.sh:2`

### `eval/diag/u10_final/gate_branch_tests.py`

- [scripts] """"U10 gate tool, every pass/fail branch executed once (2026-10-12). PLUMBING on SITL Replay outputs of the installed" — `eval/diag/u10_final/gate_branch_tests.py:2`

### `eval/diag/u10_final/gate_demo.sh`

- [scripts] "# U10 gate end-to-end on SITL (PLUMBING ONLY: SIM truth stands in for mocap, D_max = 1.0 m is the PROPOSED value used" — `eval/diag/u10_final/gate_demo.sh:2`

### `eval/diag/u10_final/gitdiff.sh` — **UNDEFINED** (see flags §a)

- [scripts] *(used, not defined here)* "#!/bin/bash" — `eval/diag/u10_final/gitdiff.sh:1` — note: no module docstring or header comment

### `eval/diag/u10_final/install_build.sh`

- [scripts] "# U10 rule 2 install (2026-10-12): ~/ardupilot_ukf on ukf-jitter-fix, fast-forwarded to replay-rukx. Back up the" — `eval/diag/u10_final/install_build.sh:2`

### `eval/diag/u10_final/mkwt.sh`

- [scripts] "# U10 rule 2 (2026-10-12): scratch worktree of ~/ardupilot_ukf on a NEW branch replay-rukx from ukf-jitter-fix." — `eval/diag/u10_final/mkwt.sh:2`

### `eval/diag/u10_final/patch_port.py`

- [scripts] """"U10 rule 2 (2026-10-12): in Replay, the UKF's five dataflash records get distinct names (RUKF/RUKO/RUKS/RUKH/RUKT)," — `eval/diag/u10_final/patch_port.py:2`

### `eval/diag/u10_final/recheck_installed.sh`

- [scripts] "# U10 rule 2: re-check on the INSTALLED binaries (~/ardupilot_ukf build, ukf-jitter-fix = replay-rukx f30f6ffa2f):" — `eval/diag/u10_final/recheck_installed.sh:2`

### `eval/diag/u10_final/rmwt.sh`

- [scripts] "# Remove the scratch port worktree (the branch replay-rukx is kept); show the port checkout's final state." — `eval/diag/u10_final/rmwt.sh:2`

### `eval/diag/u10_final/score_all.sh`

- [scripts] "# U10 rule 2: replay_gate.py and the rung-1 scorer (SIM truth standing in for mocap; plumbing only) on the Replay" — `eval/diag/u10_final/score_all.sh:2`

### `eval/diag/u10_final/score_rukx.py`

- [scripts] """"U10 rule 2 verification (2026-10-12; adapted from eval/diag/xuko_fmt/score_xuko.py): the rung-1 scorer (eval/real_score.py) on a Replay output log of a SITL flight," — `eval/diag/u10_final/score_rukx.py:2`

### `eval/diag/u10_final/stage_scratch.sh`

- [scripts] "# U10 rule 2: scratch build (one heavy step), then the 5-log Replay driver on the scratch Replay." — `eval/diag/u10_final/stage_scratch.sh:2`

### `eval/diag/u10_final/subinit.sh`

- [scripts] "# U10 rule 2 (2026-10-12): init the submodules a SITL build needs in the scratch worktree, by --reference to the main" — `eval/diag/u10_final/subinit.sh:2`

### `eval/diag/ukf_jitter_fix/build_port.sh`

- [scripts] "# Build the ukf-jitter-fix port in its OWN scratch worktree (never ~/ardupilot_ukf/build)." — `eval/diag/ukf_jitter_fix/build_port.sh:2`

### `eval/diag/ukf_jitter_fix/collect2.sh` — **UNDEFINED** (see flags §a)

- [scripts] *(used, not defined here)* "#!/bin/sh" — `eval/diag/ukf_jitter_fix/collect2.sh:1` — note: no module docstring or header comment

### `eval/diag/ukf_jitter_fix/collect.sh` — **UNDEFINED** (see flags §a)

- [scripts] *(used, not defined here)* "#!/bin/sh" — `eval/diag/ukf_jitter_fix/collect.sh:1` — note: no module docstring or header comment

### `eval/diag/ukf_jitter_fix/copymods.sh`

- [scripts] "# Copy the submodule WORKING TREES (no git metadata) from ~/ardupilot_ukf into the scratch worktree; build with" — `eval/diag/ukf_jitter_fix/copymods.sh:2`

### `eval/diag/ukf_jitter_fix/cpp_free_inertial.py`

- [scripts] """"UKF jitter correction (2026-10-09), DIAGNOSTIC: free-inertial covariance growth through the C++ PORT itself." — `eval/diag/ukf_jitter_fix/cpp_free_inertial.py:1`

### `eval/diag/ukf_jitter_fix/equiv.sh`

- [scripts] "# UKF jitter fix: (1) C++ free-inertial; (2) step-2 dsn_tex_r2 E1-E5; (3) tier A H_s1_r1 UA1-UA5 (+ D27 diagnostic)." — `eval/diag/ukf_jitter_fix/equiv.sh:2`

### `eval/diag/ukf_jitter_fix/fi_wrap.py` — **UNDEFINED** (see flags §a)

- [scripts] *(used, not defined here)* "import runpy, sys" — `eval/diag/ukf_jitter_fix/fi_wrap.py:1` — note: no module docstring or header comment

### `eval/diag/ukf_jitter_fix/rts.sh`

- [scripts] "# RTS-UKF smoke check with the fixed core: room_ukf_replay.py H_s1_r1 (RTS ON) under a FAKE HOME of real copies." — `eval/diag/ukf_jitter_fix/rts.sh:2`

### `eval/diag/ukf_jitter_fix/s2_d27.sh` — **UNDEFINED** (see flags §a)

- [scripts] *(used, not defined here)* "#!/bin/sh" — `eval/diag/ukf_jitter_fix/s2_d27.sh:1` — note: no module docstring or header comment

### `eval/diag/ukf_jitter_fix/s2_old.sh`

- [scripts] "# Step 2 as worded with the OLD (pre-fix, post-D27) core and the OLD port (UR1 export of 2026-10-08): real copies." — `eval/diag/ukf_jitter_fix/s2_old.sh:2`

### `eval/diag/ukf_jitter_fix/s2_qdiag.py`

- [scripts] """"Step-2 D27 diagnostic: write the offline UKF's per-step Q diagonal (make_params(dt=DT_STEP)) for UKF_EQ_QDIAG." — `eval/diag/ukf_jitter_fix/s2_qdiag.py:1`

### `eval/diag/ukf_jitter_fix/score_cfi.sh` — **UNDEFINED** (see flags §a)

- [scripts] *(used, not defined here)* "#!/bin/sh" — `eval/diag/ukf_jitter_fix/score_cfi.sh:1` — note: no module docstring or header comment

### `eval/diag/ukf_jitter_fix/stat_live.sh`

- [scripts] "# Fingerprint the main session's ~/ardupilot_ukf build state (must be unchanged by this stage)." — `eval/diag/ukf_jitter_fix/stat_live.sh:2`

### `eval/diag/ukf_jitter_fix/tierB_base.sh`

- [scripts] "# Attribution: the branch BASE's Replay (~/ardupilot_ukf build, ukf-port-tag 00b597dd, run read-only) on H_s1_r1." — `eval/diag/ukf_jitter_fix/tierB_base.sh:2`

### `eval/diag/ukf_jitter_fix/tierB_build.sh`

- [scripts] "# Rebuild Replay from the COMMITTED ukf-jitter-fix (abb0357d0f) in a fresh scratch worktree." — `eval/diag/ukf_jitter_fix/tierB_build.sh:2`

### `eval/diag/ukf_jitter_fix/tierB_run.sh`

- [scripts] "# Tier B with the fixed port: Replay of H_s1_r1 (UKF_EXTPOS=1 UKF_EXTYAW=1), then eval/ukf_tag_tierB.py against the" — `eval/diag/ukf_jitter_fix/tierB_run.sh:2`

### `eval/diag/xuko_fmt/build.sh`

- [scripts] "# XUKO FMT (2026-10-12): scratch SITL build of the xuko-fmt worktree: Replay, UKF_Equiv, and the copter target as a" — `eval/diag/xuko_fmt/build.sh:2`

### `eval/diag/xuko_fmt/check_logs.py`

- [scripts] """"XUKO FMT verification (a) on Replay output logs (2026-10-12). Read only." — `eval/diag/xuko_fmt/check_logs.py:2`

### `eval/diag/xuko_fmt/driver.sh`

- [scripts] "# XUKO FMT (2026-10-12): byte-identity of the four CSVs of a Replay build against the INSTALLED Replay be7c4d18's" — `eval/diag/xuko_fmt/driver.sh:2`

### `eval/diag/xuko_fmt/install_build.sh`

- [scripts] "# XUKO FMT install (2026-10-12): ~/ardupilot_ukf on ukf-jitter-fix, fast-forwarded to xuko-fmt. Back up the installed" — `eval/diag/xuko_fmt/install_build.sh:2`

### `eval/diag/xuko_fmt/recheck_installed.sh`

- [scripts] "# XUKO FMT (2026-10-12): re-check on the INSTALLED binaries (~/ardupilot_ukf build, ukf-jitter-fix = xuko-fmt 0a214d29d3):" — `eval/diag/xuko_fmt/recheck_installed.sh:2`

### `eval/diag/xuko_fmt/run_one_keep.sh`

- [scripts] "# One Replay run (one heavy step): run_one_keep.sh <outdir> <replay-binary> <log.bin> [ENV=VAL ...]" — `eval/diag/xuko_fmt/run_one_keep.sh:2`

### `eval/diag/xuko_fmt/score_xuko.py`

- [scripts] """"XUKO verification (b), 2026-10-12: the rung-1 scorer (eval/real_score.py) on a Replay output log of a SITL flight," — `eval/diag/xuko_fmt/score_xuko.py:2`

### `eval/diag/xuko_fmt/stage2.sh`

- [scripts] "# XUKO FMT + Replay stamp fix (2026-10-12): rebuild the scratch tree (one heavy step), the 5-log CSV byte-identity" — `eval/diag/xuko_fmt/stage2.sh:2`

### `eval/diag/xuko_fmt/subinit.sh`

- [scripts] "# XUKO FMT (2026-10-12): init the submodules a SITL build needs in the scratch worktree, by --reference to the main" — `eval/diag/xuko_fmt/subinit.sh:2`

### `eval/diag/xuko_fmt/summ.py`

- [scripts] """"Print the key lines of a check_logs.py JSON." — `eval/diag/xuko_fmt/summ.py:2`

### `eval/dsn_paired_test.py`

- [scripts] """"PRE-REGISTERED confirmatory test and noise floor (METHODOLOGY "PRE-REGISTRATION — additional" — `eval/dsn_paired_test.py:2`

### `eval/extract_frames.py`

- [scripts] """"Extract sample frames from a trial bag's image topic at chosen ground-truth y positions." — `eval/extract_frames.py:2`

### `eval/extract_gnss.py`

- [scripts] """"Experiment O: the GNSS samples EKF3 received, for the UKF/FGO replays (identical measurements) and the scorer." — `eval/extract_gnss.py:2`

### `eval/extract_gt_tum.py`

- [scripts] """"Write `<trial>/ukf/ground_truth.tum` from the bag alone, with no estimator replay." — `eval/extract_gt_tum.py:2`

### `eval/f1_eval.py`

- [scripts] """"F1 (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION — offline tests F1, F2, F3"): robust weighting on bad headings." — `eval/f1_eval.py:2`

### `eval/f3b_eval.py`

- [scripts] """"F3b (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION — F3b"): the nonlinearity test. fwdc_tex_r1..r3; delta in" — `eval/f3b_eval.py:2`

### `eval/f3c_eval.py`

- [scripts] """"F3c (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION — F3c"): as eval/f3b_eval.py (F3b, the nonlinearity test)," — `eval/f3c_eval.py:2`

### `eval/f4_eval.py`

- [scripts] """"F4 = plan step 2(a) (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION — plan step 2"): F1's evaluator unchanged except that" — `eval/f4_eval.py:2`

### `eval/f23_eval.py`

- [scripts] """"F2 and F3 (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION — offline tests F1, F2, F3")." — `eval/f23_eval.py:2`

### `eval/fgo_contact_prediction.py`

- [scripts] """"D19: the FGO no-heading contact prediction by the method VALIDATED in set (a) (the estimator's open-loop" — `eval/fgo_contact_prediction.py:2`

### `eval/fgo_contact_prediction_live.py`

- [scripts] """"FGO live-shadow variant of eval/ukf_contact_prediction.py (D21: the FGO no-heading prediction from half-speed" — `eval/fgo_contact_prediction_live.py:2`

### `eval/fgo_core_replay.py`

- [scripts] """"Offline twin of the LIVE FGO node, for FG1 on shadow runs WITH heading (declared before fgo_shadow_half_b)." — `eval/fgo_core_replay.py:2`

### `eval/fgo_cpp_sitl_check.py`

- [scripts] """"SITL checks of the live FGO node (C++ fgo_cpp_node, or fgo_node.py), PRE-REGISTERED in docs/fgo_cpp_port.md" — `eval/fgo_cpp_sitl_check.py:2`

### `eval/fgo_gate_check.py`

- [scripts] """"FGO closed-loop gates FG1-FG3 (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION — the FGO closed-loop gates")." — `eval/fgo_gate_check.py:2`

### `eval/fgo_groundtest_check.py`

- [scripts] """"FGO ground test (PRE-REGISTERED in "PRE-REGISTRATION — the FGO closed-loop gates"; execution deviation in "FGO ground" — `eval/fgo_groundtest_check.py:2`

### `eval/fgo_node_equiv.py`

- [scripts] """"FGO node validation (ruling D7; METHODOLOGY "FGO track ... PRE-REGISTERED")." — `eval/fgo_node_equiv.py:2`

### `eval/fgo_node_tag_equiv.py`

- [scripts] """"Experiment H, S3 gate (docs/h_backends_tag_input.md sections 1.3-1.4, PRE-REGISTERED): the FGO node core with tag" — `eval/fgo_node_tag_equiv.py:2`

### `eval/fgo_odom_mapping_check.py`

- [scripts] """"Experiment H, S3: offline check of the FGO node's state -> ODOMETRY mapping (fgo_node_core.odom_ned), the only new" — `eval/fgo_odom_mapping_check.py:2`

### `eval/figs_final_pack.py`

- [scripts] """"FINAL RESULTS PACK (2026-10-11; METHODOLOGY ruling 2026-10-11, item 0). Analysis only: no replays, no new runs." — `eval/figs_final_pack.py:2`

### `eval/figs_supervisor_2026_10_01.py`

- [scripts] """"Supervisor-meeting figures (2026-10-01). No new experiments: every number comes from committed result files" — `eval/figs_supervisor_2026_10_01.py:2`

### `eval/figs_thesis.py`

- [scripts] """"READER-FACING THESIS FIGURE SET (2026-10-15; REVISED 2026-10-16). Plotting and tabulating only: no number is recomputed," — `eval/figs_thesis.py:2`

### `eval/figs_TLO.py`

- [scripts] """"Supervisor figures for experiments T, O and L (2026-10-08). Same style and palette as" — `eval/figs_TLO.py:2`

### `eval/final_rerun_checks.py`

- [scripts] """"Checks for the FINAL consolidated offline re-run (eval/final_rerun_pipeline.sh; user rulings 2026-10-09, METHODOLOGY" — `eval/final_rerun_checks.py:2`

### `eval/final_rerun_merge_bb.py`

- [scripts] """"Final consolidated re-run: merge the regenerated blank-behaviour outputs into eval/results/blank_behaviour.json." — `eval/final_rerun_merge_bb.py:2`

### `eval/final_rerun_pipeline.sh`

- [scripts] "# FINAL consolidated offline re-run (user rulings 2026-10-09: METHODOLOGY "RULING (user, 2026-10-09): FGO noise-model" — `eval/final_rerun_pipeline.sh:2`

### `eval/fix_fgo_tum_quat.py`

- [scripts] """"Ruling D10 (2026-09-30): repair the FGO TUM orientations written with fgo_replay.py's euler_to_quat" — `eval/fix_fgo_tum_quat.py:2`

### `eval/flow_quality.py`

- [scripts] """"Downward-flow quality per trial — the Phase 1 confound check (b)." — `eval/flow_quality.py:2`

### `eval/fwd_eval.py`

- [scripts] """"Phase 3 evaluation of the forward-camera measurements against ground truth." — `eval/fwd_eval.py:2`

### `eval/fwd_run.py`

- [scripts] """"Run the Phase 3 forward-camera measurements over every forward frame of one bag." — `eval/fwd_run.py:2`

### `eval/fwd_sweep_eval.py`

- [scripts] """"Phase 3 supplementary check: static heading response (METHODOLOGY, pre-registered)." — `eval/fwd_sweep_eval.py:2`

### `eval/fwd_transition_segments.py`

- [scripts] """"Phase 3 heading/yaw-rate accuracy on the transition world, split by floor segment:" — `eval/fwd_transition_segments.py:2`

### `eval/ground_test_check.py`

- [scripts] """"Closed-loop Part 1 SITL ground test: criteria G1-G5 (METHODOLOGY "SITL ground test", fixed" — `eval/ground_test_check.py:2`

### `eval/h_comparative.py`

- [scripts] """"Experiment H comparative criteria (H-H2, P-H3, H-H4; pre-registered in docs/tag_hold_design.md §e) from the STORED" — `eval/h_comparative.py:2`

### `eval/h_gt_far_score.py`

- [scripts] """"Experiment H, far-spawn SITL ground tests (pre-registered 2026-10-08 item 3; docs/h_backends_tag_input.md section 5" — `eval/h_gt_far_score.py:2`

### `eval/h_ifa_score.py`

- [scripts] """"Experiment H, in-flight-anchor transient check (pre-registered 2026-10-08, amended 2026-10-09; METHODOLOGY)." — `eval/h_ifa_score.py:2`

### `eval/h_s0a_char.py`

- [scripts] """"Experiment H, S0a: wall-tag characterisation from the FORWARD camera (pre-registered rules, METHODOLOGY" — `eval/h_s0a_char.py:2`

### `eval/h_s0b_check.py`

- [scripts] """"Experiment H, S0b check flight (pre-registered checks, METHODOLOGY "Experiment H: pre-registration"):" — `eval/h_s0b_check.py:2`

### `eval/h_safety_score.py`

- [scripts] """"Experiment H, option (i) safety tests (H ruling 2026-10-08; METHODOLOGY "PRE-REGISTRATION (2026-10-08, before any" — `eval/h_safety_score.py:2`

### `eval/h_score.py`

- [scripts] """"Experiment H scorer, S1 (METHODOLOGY "Experiment H: pre-registration"). One flight:" — `eval/h_score.py:2`

### `eval/heading_bridge_offline.py`

- [scripts] """"Offline test of the live heading bridge (closed-loop Part 1) on a recorded fwdc bag." — `eval/heading_bridge_offline.py:2`

### `eval/heading_cpp_equivalence.py`

- [scripts] """"Equivalence test of the C++ heading port (src/forward_camera/cpp/libheading.so) against the" — `eval/heading_cpp_equivalence.py:2`

### `eval/heading_share.py`

- [scripts] """"Heading share of EKF3's lateral drift on the pinned cruise window (the batched correction" — `eval/heading_share.py:2`

### `eval/imu_gap_check.py`

- [scripts] """"IMU gap rule for the replay estimators (UKF/FGO) — METHODOLOGY "RULE — IMU gaps and" — `eval/imu_gap_check.py:2`

### `eval/input_timing.py`

- [scripts] """"Sim-time timing of the estimator inputs, and flow delivery latency into live EKF3." — `eval/input_timing.py:2`

### `eval/l_score.py`

- [scripts] """"Experiment L scorer (METHODOLOGY "Experiment L: pre-registration"). For one T flight: the keyframe FGO's live and" — `eval/l_score.py:2`

### `eval/lidar_short_returns.py`

- [scripts] """"LiDAR short returns (D23 cause): does ArduPilot's range path reject them for EKF3 and the UKF port?" — `eval/lidar_short_returns.py:2`

### `eval/mocap_align.py`

- [scripts] """"Mocap alignment (real-flight plan, tooling item 4; rung-1 item R8): TIME and FRAME alignment of motion-capture ground" — `eval/mocap_align.py:2`

### `eval/mocap_align_test.py`

- [scripts] """"Tests of eval/mocap_align.py's window rule (2026-10-11 fixes; synthetic flights from mocap_align_validate)." — `eval/mocap_align_test.py:1`

### `eval/mocap_align_validate.py`

- [scripts] """"Validation of the mocap <-> FC time sync on the 400 Hz RISI records (rung-1 item R8)." — `eval/mocap_align_validate.py:2`

### `eval/o_score.py`

- [scripts] """"Experiment O scorer (pre-registered in METHODOLOGY "Experiment O: pre-registration"). Absolute world frame, NO" — `eval/o_score.py:2`

### `eval/oi2_imu_time.py`

- [scripts] """"OI-2: rebuild a trial's bag with /imu/data_raw on SENSOR time instead of receipt time." — `eval/oi2_imu_time.py:2`

### `eval/phase2_score.py`

- [scripts] """"Phase 2 (`fwd_*`) scoring against the pre-registered criteria." — `eval/phase2_score.py:2`

### `eval/phase4_eval.py`

- [scripts] """"Phase 4 evaluation: every arm of the offline forward-camera fusion (UKF and FGO)," — `eval/phase4_eval.py:2`

### `eval/phase5_analysis.py`

- [scripts] """"Phase 5 — evaluation of the Phase 4 outputs against the pre-registered prediction." — `eval/phase5_analysis.py:2`

### `eval/phase5b_consistency.py`

- [scripts] """"Phase 5b: consistency (NEES) of the estimators' own covariance, and the heading" — `eval/phase5b_consistency.py:2`

### `eval/r1_followup_replays.sh`

- [scripts] "# R1 follow-up (docs/handovers/2026-10-10_r1_converter.md): the two LIGHT single replays the R1 stage could not run" — `eval/r1_followup_replays.sh:2`

### `eval/real_score.py`

- [scripts] """"Rung-1 scorer (real-flight plan item R9): the three estimators, all on the FC clock, against mocap, on ONE window" — `eval/real_score.py:2`

### `eval/real_score_test.py`

- [scripts] """"Synthetic tests of eval/real_score.py (window rule, mocap-gap masking, drift-segment guard)." — `eval/real_score_test.py:1`

### `eval/rebuild_supervisor_pdf.py`

- [scripts] """"Rebuild a supervisor figure set's combined figures.pdf from its existing PNGs and INDEX.md captions (same page" — `eval/rebuild_supervisor_pdf.py:2`

### `eval/replay_gate.py`

- [scripts] """"Rung-1 Replay-fidelity gate (pre-registration sec. 5): the onboard EKF3 (XKF1 core 0) against the replayed EKF3" — `eval/replay_gate.py:2`

### `eval/rerun_bands.py`

- [scripts] """"P4 outcome bands recomputed from the RE-FLOWN dsn baseline with the pre-registered" — `eval/rerun_bands.py:2`

### `eval/rerun_compare.py`

- [scripts] """"Old vs new for every headline number of the consolidated re-run (user ruling 2026-09-29):" — `eval/rerun_compare.py:2`

### `eval/rerun_latency_check.py`

- [scripts] """"EKF3 flow latency (DIAGNOSTIC) for every re-flown trial, against the pre-registered P2 band" — `eval/rerun_latency_check.py:2`

### `eval/rerun_pipeline.sh`

- [scripts] "# Consolidated re-run: the whole analysis pipeline, from scratch, on the re-flown bags" — `eval/rerun_pipeline.sh:2`

### `eval/rgs_profile.py`

- [scripts] "| B5 (gyro rms) | the definition of its source band (`eval/rgs_profile.py`): cruise span with GT forward speed > 0.3 m/s (51-sample smoothing), **trimmed by 5 s at each end** |" — `METHODOLOGY.md:5075` — note: nearest defining text: the B5 gyro-rms source band it computes
- [scripts] *(used, not defined here)* "import sys, os, json, numpy as np" — `eval/rgs_profile.py:1` — note: no module docstring or header comment
- [scripts] *(used, not defined here)* "`eval/rgs_profile.py`):" — `METHODOLOGY.md:4596` — note: script has no docstring; usage in docs

### `eval/rtf_drift_check.py`

- [scripts] """"PRE-REGISTERED RTF check (METHODOLOGY "PRE-REGISTRATION — RTF check"): open-loop cruise yaw drift and" — `eval/rtf_drift_check.py:2`

### `eval/run_jobs_resumable.sh`

- [scripts] "# Crash-safe, resumable parallel job runner for offline replays (Phase 4 onwards)." — `eval/run_jobs_resumable.sh:2`

### `eval/run_set_eval.sh`

- [scripts] "# Evaluate one recorded trial set end to end, exactly as Phase 2 was evaluated." — `eval/run_set_eval.sh:2`

### `eval/scale_check.py`

- [scripts] """"Distance-scale check (user ruling 2026-09-29; replaces "bounded check 5a")." — `eval/scale_check.py:2`

### `eval/sens_yaw0_eval.py`

- [scripts] """"Labelled SENSITIVITY CHECK (user ruling 2026-10-10, METHODOLOGY "RULINGS (user, 2026-10-10): FGO initial yaw sigma"," — `eval/sens_yaw0_eval.py:2`

### `eval/sensor_timing_from_log.py`

- [scripts] """"Rung 1: measure each sensor's RATE and DELAY from a dataflash log, for pre-registering the UKF/FGO capture-time" — `eval/sensor_timing_from_log.py:2`

### `eval/t_aggregate.py`

- [scripts] """"Experiment T: pooled verdicts over the 12 flights (METHODOLOGY "Experiment T: pre-registration"). Reads" — `eval/t_aggregate.py:2`

### `eval/t_flow_catchup.py`

- [scripts] """"T lap flights: optical-flow tracker validity in the post-corner catch-up segments vs the straight segments (user" — `eval/t_flow_catchup.py:2`

### `eval/tag_char_report.py`

- [scripts] """"Tag module characterisation (experiments T/L; reported BEFORE any estimator uses tags). Per trial (recorded with" — `eval/tag_char_report.py:2`

### `eval/tag_flight_check.py`

- [scripts] """"Experiment T: check flight analysis for a lap flight with the tag bridge (EKF3 in ExtNav mode). Reads the trial's" — `eval/tag_flight_check.py:2`

### `eval/tag_score.py`

- [scripts] """"Experiment T scorer (pre-registered in METHODOLOGY "Experiment T: pre-registration"). Absolute world frame, NO" — `eval/tag_score.py:2`

### `eval/three_way_eval.py`

- [scripts] """"Three-way evaluation — EKF3 / UKF / FGO on ONE pinned cruise window." — `eval/three_way_eval.py:2`

### `eval/topic_rates.py`

- [scripts] """"Per-topic message counts and mean sim-time rates for trial bags." — `eval/topic_rates.py:2`

### `eval/u10_gate.py`

- [scripts] """"U10: the Replay gate on rung-1 logs (docs/u10_replay_gate_band.md, SIGNED OFF by the user 2026-10-12, including" — `eval/u10_gate.py:2`

### `eval/u10_gate_test.py`

- [scripts] """"Synthetic tests of eval/u10_gate.py against the SIGNED docs/u10_replay_gate_band.md (2026-10-12): a PASS case and a" — `eval/u10_gate_test.py:1`

### `eval/ukf_contact_prediction.py`

- [scripts] """"D16 ruling check (2026-09-30): the no-heading contact prediction by the method VALIDATED in set (a)" — `eval/ukf_contact_prediction.py:2`

### `eval/ukf_csv_to_tum.py`

- [scripts] """"R3 (rung 1): convert the UKF port's Replay output (`ukf_shadow.csv`, written by AP_NavUKF::log_state in" — `eval/ukf_csv_to_tum.py:2`

### `eval/ukf_equivalence.py`

- [scripts] """"UKF port validation STEP 2, part 3: compare the C++ port's states (UKF_Equiv harness output)" — `eval/ukf_equivalence.py:2`

### `eval/ukf_event_export.py`

- [scripts] """"UKF port validation STEP 2, part 1: export the offline UKF's exact event stream and states." — `eval/ukf_event_export.py:2`

### `eval/ukf_heading_v1.py`

- [scripts] """"D17 V1/V2 (PRE-REGISTERED, METHODOLOGY "PRE-REGISTRATION (D17)"): the UKF port's ExtNav heading input." — `eval/ukf_heading_v1.py:2`

### `eval/ukf_p3_check.py`

- [scripts] """"D9 precondition P3 (PRE-REGISTERED, METHODOLOGY "D9 precondition P3"): the UKF backend ground test" — `eval/ukf_p3_check.py:2`

### `eval/ukf_predictor_check.py`

- [scripts] """"D9 output-predictor check (PRE-REGISTERED in METHODOLOGY before P2 was looked at): each current-time" — `eval/ukf_predictor_check.py:2`

### `eval/ukf_queue_check.py`

- [scripts] """"UKF port, D9 precondition (ruling 2026-09-30): the D5 delayed-horizon event queue never overflows and" — `eval/ukf_queue_check.py:2`

### `eval/ukf_replay_vs_flying.py`

- [scripts] """"Rung 1 (2026-10-11): the UKF port in Replay against the FLYING port's own logged state." — `eval/ukf_replay_vs_flying.py:2`

### `eval/ukf_shadow_bin2csv.py`

- [scripts] """"Part 4: convert the shadow UKF's own dataflash records (XUKF + XUKS, written live in SITL by" — `eval/ukf_shadow_bin2csv.py:2`

### `eval/ukf_shadow_replay_check.py`

- [scripts] """"Part 4: check the shadow UKF (AP_NavUKF, ~/ardupilot_ukf) run in ArduPilot Replay on a flown log." — `eval/ukf_shadow_replay_check.py:2`

### `eval/ukf_step3.py`

- [scripts] """"UKF port validation STEP 3 (a REPORT, not pass/fail; METHODOLOGY "Step 1 ... Step 3"): the cost of" — `eval/ukf_step3.py:2`

### `eval/ukf_tag_equivalence.py`

- [scripts] """"Experiment H, S2 gate, UKF tier A (docs/h_backends_tag_input.md section 1.1, PRE-REGISTERED): compare the C++ port's" — `eval/ukf_tag_equivalence.py:2`

### `eval/ukf_tag_event_export.py`

- [scripts] """"Experiment H, S2 gate (docs/h_backends_tag_input.md, tier A): export the offline ROOM UKF's exact event stream" — `eval/ukf_tag_event_export.py:2`

### `eval/ukf_tag_tierB.py`

- [scripts] """"Experiment H, S2 gate, UKF tier B (docs/h_backends_tag_input.md section 1.2, PRE-REGISTERED): the port on" — `eval/ukf_tag_tierB.py:2`

### `tools/bag_pack.sh`

- [scripts] "# Lossless file-level compression of a trial's rosbag2 file (ruling 2026-10-08; docs/disk_report_2026-10-08.md)." — `tools/bag_pack.sh:2`

### `tools/build_board_fw.sh`

- [scripts] "# build_board_fw.sh: one-command board build of the thesis fork (ArduCopter + the UKF/FGO backends) for a named hwdef." — `tools/build_board_fw.sh:2`

### `tools/edit_guard.py`

- [scripts] """"HARD edit guard (user ruling 2026-10-01, after two edits to files a running batch used): a Claude Code" — `tools/edit_guard.py:2`

### `tools/flight_lock.sh`

- [scripts] "# Flight-lock helpers (source this file). Ruling 2026-10-08: locks are created ATOMICALLY with an owner ID and only" — `tools/flight_lock.sh:1`

### `tools/h10_pilot.py`

- [scripts] """"SITL ONLY (H10 verification flight `h10_guard_check`, pre-registered in docs/h10_guard_check_prereg.md): a scripted" — `tools/h10_pilot.py:2`

### `tools/launch_final_rerun.sh`

- [scripts] "# Launcher for the FINAL consolidated offline re-run (eval/final_rerun_pipeline.sh). WRITTEN, NOT LAUNCHED (2026-10-09)." — `tools/launch_final_rerun.sh:2`

### `tools/node_stop_watch.sh`

- [scripts] "# FGO ground test (METHODOLOGY "FGO ground test ... DEVIATION"): once fly_trial reports the armed hold, wait" — `tools/node_stop_watch.sh:2`

### `tools/pack_all.sh`

- [scripts] "# Pack every trial bag except experiments T/O/L (T_*, O_*, o_check1), one at a time (ruling 2026-10-08)." — `tools/pack_all.sh:2`

### `tools/pi/heading_arm_check.py`

- [scripts] """"ARM64 check of the C++ heading library (real-flight plan, tooling item 2). Extracts every Nth forward-camera frame" — `tools/pi/heading_arm_check.py:2`

### `tools/real_camera/calibrate.py`

- [scripts] """"Real-camera lens calibration (real-flight plan, tooling item 3). Chessboard views from a video or an image folder ->" — `tools/real_camera/calibrate.py:2`

### `tools/real_camera/run_heading_video.py`

- [scripts] """"Run the FROZEN heading program on a recorded real video (real-flight plan, tooling item 3). Nothing here changes" — `tools/real_camera/run_heading_video.py:2`

### `tools/real_camera/selftest_calibration.py`

- [scripts] """"Self-test of the real-camera calibration step (no real camera needed). Renders N synthetic chessboard views through a" — `tools/real_camera/selftest_calibration.py:2`

### `tools/run_expH_s1.sh`

- [scripts] "# Experiment H S1 (pre-registered): 3 closed-loop flights, EKF3 flying on the wall tag (closed_loop_run.sh H=1)." — `tools/run_expH_s1.sh:2`

### `tools/run_expO.sh`

- [scripts] "# Experiment O flights (METHODOLOGY "Experiment O: pre-registration"): 3 repeats, nothing else on the machine." — `tools/run_expO.sh:2`

### `tools/run_expT.sh`

- [scripts] "# Experiment T flights (pre-registered: METHODOLOGY "Experiment T: pre-registration"). 12 single-trial resumable batches," — `tools/run_expT.sh:2`

### `tools/run_expT_refly.sh`

- [scripts] "# Experiment T: re-fly of the flights the standing IMU-gap rule (eval/imu_gap_check.py) marked unusable, unchanged" — `tools/run_expT_refly.sh:2`

### `tools/run_fgo_cpp_stage5.sh`

- [scripts] "# FGO C++ stage 5 (docs/handovers/2026-10-08_fgo_cpp_stage5_sitl_flights.md): the three SITL shadow flights, flown on" — `tools/run_fgo_cpp_stage5.sh:2`

### `tools/run_fgo_refly.sh`

- [scripts] "# FGO closed-loop RE-FLIGHTS with the corrected FGO (ruling 2026-10-09). v3 = noise fix + gated yaw cap (node f642cd37); v2 = noise fix only (kept, ablation), one per argument, under the flight lock; stop at the" — `tools/run_fgo_refly.sh:2`

### `tools/run_h10_guard_check.sh`

- [scripts] "# H10 verification flight h10_guard_check (pre-registered: docs/h10_guard_check_prereg.md). VERIFICATION only. ONE" — `tools/run_h10_guard_check.sh:2`

### `tools/run_h_far.sh`

- [scripts] "# H far-spawn sequence (pre-registered 2026-10-08/09), one flight per argument, under the flight lock; stops at the first" — `tools/run_h_far.sh:2`

### `tools/run_h_safety.sh`

- [scripts] "# H option (i) safety tests (pre-registered 2026-10-08), one flight per argument, under the flight lock; stops at the" — `tools/run_h_safety.sh:2`

### `tools/run_p1c_img.sh`

- [scripts] "# p1c_img CALIBRATION flights (ruling 2026-10-10; docs/p1c_img_calibration_spec.md, signed off). NEVER datasets." — `tools/run_p1c_img.sh:2`

### `tools/run_ukf_refly.sh`

- [scripts] "# UKF closed-loop RE-FLIGHTS with the jitter-corrected UKF port (ruling 2026-10-09), one per argument, under the flight lock." — `tools/run_ukf_refly.sh:2`

### `tools/run_wbench.sh`

- [scripts] "# Watcher SITL bench (item 2c; docs/handovers/2026-10-11_watcher_sitl_bench.md). VERIFICATION flights only (wbench_*)," — `tools/run_wbench.sh:2`

### `tools/test_fly_trial_h10.py`

- [scripts] """"H10 (ruling 8, 2026-10-12): offline mock test of fly_trial.py's pilot-takeover guard. No SITL." — `tools/test_fly_trial_h10.py:2`

### `tools/test_watch_failclosed.sh`

- [scripts] "# Fail-closed safety-watcher tests (ruling 2026-10-08). Lock protocol: waits for BUILD_LOCK to clear, holds FLIGHT_LOCK." — `tools/test_watch_failclosed.sh:2`
