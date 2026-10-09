# Handover, 2026-10-09: FINAL consolidated offline re-run, pipeline BUILT and DRY-RUN (not launched)

**Stage:** build and dry run only. No replay, no evaluator and no imu_gap_check write was run. No lock was taken.
Nothing under `~/thesis_data` was created or changed: there is no `batches/final_rerun/`, no `pre_final_trials/`, and no
`eval/results_pre_final/`.

**Rulings implemented** (METHODOLOGY):
- "RULING (user, 2026-10-09): FGO noise-model correction ... consolidated re-run plan", items 4–6.
- "MODEL AUDIT RESULT ... RULINGS", order 6–9.
- "RULINGS ... the yaw-cap ablation; the cut order".
- The derotation ruling of 2026-10-08, item 3.

**Files** (worktree branch `worktree-agent-a55370a40530b58f2`, based on `fwd-camera` `7f23197`):

| file | what it is |
|---|---|
| `eval/final_rerun_pipeline.sh` | The resumable pipeline: one `.done` per stage, and per-job resume inside the replay stages. Modes: `--dry-run`, `--only STAGE`. |
| `tools/launch_final_rerun.sh` | The launcher, **written, not launched**. It submits each stage as ONE `heavy.py` call: `python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "final_rerun <stage>" -- ~/thesis_ws/eval/final_rerun_pipeline.sh --only <stage>`. |
| `eval/final_rerun_checks.py` | Light checks: `provenance` (git SHA + md5s), `corrections` (the four grep/AST assertions), `ekf3-gate OLD NEW ...`. |
| `eval/final_rerun_merge_bb.py` | Blank-behaviour merge: replaces every `ukf*`/`fgo*` field and dies if any other field (EKF3) differs. |
| `batches/final_rerun/{F,room_H,room_O,room_T,L,cl_pred}.jobs` | The vendored job lists, which can be reviewed before launch. |
| `docs/handovers/2026-10-09_final_rerun_dryrun.txt` | **The dry-run output**: every command and every job line. |

## 1. Pipeline design (what is enforced)

**Fresh names.** All of these are new, and none exists today:
- results snapshot: `eval/results_pre_final`;
- trial-output archive: `~/thesis_data/pre_final_trials`;
- state: `~/thesis_data/batches/final_rerun/`;
- job batches: `final_phase4`, `final_phase5b`, `final_F`, `final_f4`, `final_room_{H,O,T}`, `final_L` and `final_cl_pred`;
- Phase 5b sandbox: `~/thesis_data/phase5b_final`.

**Snapshot and archive.** Both **die if the target exists**; they never skip and never overwrite.
- The archive copies every `ukf*`, `fgo*`, `room_*` and `lc_fgo_*` directory of every trial: 667 directories, about
  2.3 GB. It also copies `phase5b_d15` and the `batches/eval_<set>` logs, and writes an md5 manifest.
- The archive therefore holds both the old numbers and the "FGO noise fix only (yaw cap ungated)" ablation outputs.

**Preflight.**
- Logs the git SHA and the md5 of `ukf_core.py`, `measurement_models.py`, `imu_timing.py`, the UKF/FGO replay harnesses,
  `fgo/fgo_core.py`, `fgo/factors.py`, `fgo_cpp/src/fgo_core.cpp` + `.h`, and the installed `fgo_cpp_replay` and
  `fgo_cpp_node`. The C++ core is not used by any offline result; it is logged for provenance only.
- Dies if any tracked file is modified.
- Dies if a diagnostic or arm environment switch is set: `UKF_APIN`, `FGO_*` export, `UKF_DUMP`, `F_TAG`,
  `ROOM_TAG_SIGMA_POS`.
- Dies unless every replayed T, O, H and 2(a) trial has an `imu_gaps.json` that is not `unusable`.

**Corrections assertion** (`final_rerun_checks.py corrections`). The run dies unless all four checks pass:

| # | correction | what is asserted |
|---|---|---|
| 1 | FGO noise model | `setBiasAccOmegaInit` is exactly `np.zeros((6, 6))` in `fgo_core.py` and exactly `gtsam::Matrix6::Zero()` in `fgo_core.cpp`, and there is no other call. |
| 2 | FGO yaw cap | `ATT_VAR_GATE = 0.04` is defined, and `fire = tr > ATT_VAR_GATE` is present in both cores. |
| 3 | UKF jitter | `CHOL_JITTER_LADDER` starts at `0.0`; the first attempt is `... if jit else c * Psym`; there is no unconditional `+ 1e-12*np.eye`. |
| 4 | UKF bias-corrected derotation as the DEFAULT | AST check, applied to BOTH `ukf_replay.py` and `room_ukf_replay.py`. See below. |

Check 4 in detail:
- **Passes if** the variable passed as the 4th argument of `update_flow(...)` (the derotation rate) is assigned a value
  containing `BG_SLICE`, and that assignment is NOT inside an `if` whose test mentions `APIN` or `biascorr`.
- **Also passes if** `ukf_core.update_flow` or `measurement_models.h_flow` itself references `BG_SLICE`, i.e. the
  subtraction was moved into the core.
- **Today it FAILS, as intended.** Both harnesses have the subtraction only under `if APIN == "biascorr":` (lines 161 and
  152).
- **Tested against simulated landings:** an unconditional subtraction, `if True:`, and an opt-out
  `if not os.environ.get(...)` all PASS.
- **One form would make it fail falsely:** a condition that still mentions `APIN`/`biascorr` (e.g.
  `if APIN == "biascorr" or True`). If the parallel agent's form trips the check, adjust `_harness_biascorr_default`.
  Do not weaken the other three checks.

**EKF3 gates** (`ekf3-gate`). Every JSON leaf whose key path contains "EKF3" must be byte-identical to the snapshot,
otherwise the run dies.
- **The HARD GATE after `dsn`** covers `rerun_dsn_evo`, `input_timing_rerun_dsn` and `flow_quality_rerun_dsn`. The
  last has no EKF3 leaves and is warned only.
- The same gate is also applied after `dsn_extra`, after each forward set, after Phase 4, and on the H, O and T scores.
- **Checked on the committed files:** 382 EKF3 leaves in them are compared, and all are pure-EKF3 paths.
- **Caveat (H/O/T only):** if `h_score.py`, `o_score.py` or `tag_score.py` changed after their JSONs were committed, a
  scorer change (not an estimator change) can trip these gates. The replays are then already `.done`, so a re-run redoes
  only the scoring.

**Flight check.**
- Runs at the start of every stage: `FLIGHT_LOCK`, `[a]rducopter` or `[g]z sim`.
- The default `FLIGHT_WAIT_S=0` dies at once. Set `FLIGHT_WAIT_S` to pause instead (checked every 60 s, then dies).
- `heavy.py` adds its own wait (up to 6 h) and holds `BUILD_LOCK` only for the stage it runs. Because each stage is a
  separate `heavy.py` call, a flight can take the machine **between** stages.

**Packed bags: a gap found and fixed in the build.** 62 of the replayed bags are zstd-packed (`tools/bag_pack.sh`;
`bag_0.db3.zst`) and cannot be read until unpacked.
- This covers all of `dsn`, `fwdc`, `fwdplainc`, `p1c`, `f4` and `cl_*`. T, O and H are not packed.
- **Unpacking** uses `bag_pack.sh unpack`, which is sha256-verified:
  - stage `unpack`: the corridor sets, 40 bags, 78 GB;
  - stage `f4`: 38 GB, unpacked and repacked inside the stage;
  - the V-L bag, unpacked inside `L`.
- **Free-space guard:** the needed size + 40 GB. Today 263 GB are free; the peak use is about 78 GB.
- **Repacking does NOT use `bag_pack.sh pack`.** That command's sha-mismatch branch deletes the `.zst` (the original).
  The pipeline instead removes a restored `.db3` only if its sha256 equals `PACKED.txt` and the `.zst` exists;
  otherwise it keeps both and warns.

**Stage order** (L last among the replays; the protected items come first):

```
preflight -> snapshot -> unpack -> dsn [HARD EKF3 GATE] -> dsn_extra -> bands -> paired -> set_p1c -> set_fwdc ->
set_fwdplainc -> phase4 -> phase5 -> phase5b -> d15_bb -> ftests -> repack_corridor -> f4 -> h_shadows -> expO ->
expT -> [d27item3, opt-in] -> [cl_pred, opt-in] -> L -> compare
```

## 2. Inventory: each ruled item, its stage, script and inputs, template coverage, and what was missing

| ruled item | stage | script(s) / inputs → outputs | template? | what was missing / done here |
|---|---|---|---|---|
| dsn r1–r3 | `dsn` | `run_set_eval.sh rerun_dsn` (gap check, UKF + FGO 0.25 replays, timing, flow quality, `three_way_eval`, `phase2_score`) → `rerun_dsn_{evo,score}.json`, `dsn_dejitter_baseline.json` | d15 | the hard EKF3 gate (added); **bags packed** (unpack added) |
| dsn_extra r4–r10 | `dsn_extra` | `run_set_eval.sh dsn_extra` → `dsn_extra_{evo,score}.json`; r10 is unusable, so EKF3 only | d15 | gate added |
| P4 bands | `bands` | `rerun_bands.py rerun_dsn_evo.json` → `rerun_p4_bands.json`, exported before the forward sets are scored (the D27 lesson) | d15 | — |
| Confirmatory EKF3-vs-FGO test | `paired` | `dsn_paired_test.py rerun_dsn_evo dsn_extra_evo`, UNCHANGED, original rule → `dsn_paired_test.json` | d15 | — |
| p1c / fwdc / fwdplainc | `set_*` | `run_set_eval.sh rerun_{p1c,fwdc,fwdplainc}` | d15 | gate added |
| Phase 4 (and C0) | `phase4` | `batches/phase4_replays.jobs` (90 jobs, unchanged) + `phase4_eval.py fwdc fwdplainc` → `phase4_*_{evo,arms}.json`. C0 is read from these (no separate script). | d15 | — |
| Phase 5, scale check, heading share | `phase5` | `phase5_analysis.py`, `scale_check.py`, `heading_share.py` | d15 | — |
| Phase 5b | `phase5b` | `build_5b_sandbox.sh` (fresh sandbox `phase5b_final`) + 72 jobs + `phase5b_consistency.py` | d15 | — |
| D15 kick/drift, RTF, blank behaviour | `d15_bb` | `d15_kick.py`, `d15_drift.py`, `rtf_drift_check.py`, `blank_behaviour.py` (both arm groups) | d27_regen | d27 replaced only the `ukf*` fields; both estimators now change, so a **new merge** replaces `ukf*` + `fgo*` and dies on any other difference |
| F1 (test), F2, F3, F3b, F3c, PATnocap | `ftests` | `batches/final_rerun/F.jobs` (73 jobs) + `f1_eval test cauchy:2.385`, `f23_eval f2/f3`, `f3b_eval`, `f3c_eval --tag F3cd --deltas 10,30` | d27_regen (evaluators only) | `fruns.jobs` and `f3b.jobs` lived only in `~/thesis_data`; they are now **vendored** verbatim. **F1 calibration is not re-run** (Q3). |
| 2(a) (F4) | `f4` | `batches/f4_replays_usable.jobs` (30 jobs, unchanged) + `f4_eval.py test cauchy:2.385 --trials <10 usable>` | none | the `--trials` order was unrecorded; it was rebuilt from `~/thesis_data/batches/f4_eval.txt`. Bags packed (handled). |
| H shadows | `h_shadows` | `room_H.jobs`: `ROOM_TAG_SIGMA_POS=0.02`. S1 r1–r3: UKF with RTS, FGO `--no-batch`. S1-far r1, r2, **r3b (new)**: UKF `--no-rts`, FGO `--no-batch`. Then `h_score.py --profile s1[_far]_profile.json --sigma 0.02` (venv-tags). | none | **no committed job list**: rebuilt from the stored outputs (`stats.json` σ 0.02; no `ukf_rts.tum` for far r1/r2) and `docs/h_backends_tag_input.md:17-20`. The far profile is inferred (Q5). |
| O | `expO` | `room_O.jobs`: `room_ukf --gnss`, `room_ukf --gnss --rts-no-yawcap`, `room_fgo --gnss` on O_r1, O_r2, O_r3b; `o_score.py` | none | rebuilt (no committed list); `gnss.npz` inputs are reused, not re-extracted |
| T | `expT` | `room_T.jobs`: `room_ukf` (RTS) + `room_fgo` (batch) on the 12 flights; `tag_score.py` ×12; `t_aggregate.py` | none | rebuilt (no committed list). The *_IMUGAP originals are not replayed. |
| L (last) | `L` | `L.jobs`: `lc_fgo_replay.py T_A_r{1,2,3} --mode lc/nolc --t-max 245`, plus V-L `dsn_tex_r1 --mode lc --no-tags`; `l_score.py --suffix _t245` | none | rebuilt. **V-L scoring is MISSING**: the `three_way_eval --est` labels were not recorded (Q6). L has no UKF arm. |
| D27 item 3 / F3 lockout re-measurement | `d27item3` (opt-in), `ftests` | FGO side: `fgo_core_replay.py cl_fgo_b_tex_r{1,3}_half --save-npz` + `d26_fgo_gate.py`. The F3 lockout comes from `f23_eval f3`. | none | **MISSING:** the UKF side used the UKF port's SITL Replay (not an offline Python replay), and the 15.9 % / 2.9 % per-heading weights have no script (computed by hand in D26). Opt-in: `FINAL_D27I3=1` (Q4). |
| Closed-loop scoring | (none) / `cl_pred` (opt-in) | `closed_loop_score.py` reads only the bag, dataflash and heading CSV, with **no offline replay**, so the closed-loop scores are unaffected. The only offline input is the FGO contact prediction (`fgo_half_pred.jobs` + `fgo_contact_prediction.py`), written to a NEW `fgo_contact_prediction_half_final.json` | none | whether to restate a pre-registered prediction band is a ruling (Q2). The `cl_*` bags have **no `imu_gaps.json`** (the stage writes them first) and are packed. |
| Old vs new | `compare` | `rerun_compare.py results_pre_final results` → `final_old_vs_new.{md,json}` | rerun_pipeline | **covers the corridor headlines only.** T/O/L/H/F/2(a) rows need extending (§5). |

**Not in the pipeline** (not listed by the ruling; flagged):
- the UKF shadow-SITL D15 checks (`ukf_shadow_sitl_tex_d5`, `_d15`; in `d27_ukf_rerun_v2.jobs`);
- numbers.md §3/§5 window-sensitivity rows that carry UKF/FGO values (max Δ evo under a clock shift; the 0.20 m/s row);
- `fgo_contact_prediction_live.py`;
- the old full-length `lc_fgo_lc/` and `lc_fgo_nolc` runs (superseded by t245).

**IMU-gap rule:**

| trial | status |
|---|---|
| `H_s1far_r3` | **UNUSABLE** (98 ms receipt bunch); excluded, `r3b` is used instead |
| `O_r3_IMUGAP`, `T_*_IMUGAP` (×6), `dsn_tex_r10`, `f4_fwdc_tex_r1`, `f4_fwdplainc_tex_r3` | unusable, handled as before (not replayed; EKF3 only, or counted against) |
| `H_s1far_r3b` | `ok` |
| every replayed T / O / H / f4 trial | has `imu_gaps.json` (dry-run listing: all `ok`, `f4_fwdc_tex_r4` `trim`) |
| `cl_*` bags | **lack `imu_gaps.json`** (needed only for the opt-in `cl_pred` stage, which writes it after unpacking) |

Also lacking `imu_gaps.json`, with no replay planned: all `H_s2*`, `H_s3*`, `H_safety_*`, `H_gt_*`, `H_ifa_ekf3` and
the `fgo_shadow_*` trials. **No imu_gap_check was written in this stage:** the corridor and `cl` bags are packed, and the
replayed trials already have the file.

## 3. Dry run

- **Output:** `docs/handovers/2026-10-09_final_rerun_dryrun.txt`, 452 lines, with every command and all 253 job lines.
  Reproduce it with `./eval/final_rerun_pipeline.sh --dry-run`. It writes nothing outside stdout.
- **Corrections check:** (1)–(3) ok; **(4) FAILS**, as expected until the derotation change lands.
- **Provenance at the time of the dry run:** HEAD `7f23197`.

  | file | md5 |
  |---|---|
  | `ukf_core.py` | `483383f0…` |
  | `measurement_models.py` | `1054a390…` |
  | `fgo_core.py` | `d7e5ff7d…` |
  | `fgo_core.cpp` | `de92e852…` |
  | installed `fgo_cpp_node` | `f642cd37…` (the final FGO) |

## 4. Runtime estimate (from the earlier logs; workstation, PAR 6, single-threaded BLAS, nice 19)

| stage | basis | estimate |
|---|---|---|
| preflight, snapshot (3.1 GB copy + md5), unpack (78 GB zstd) | disk speed | 10–15 min |
| dsn / dsn_extra | d15 9.1 / 8.3 min; rerun 9.3 min | 18 min |
| bands, paired | < 1 min | 1 min |
| set_p1c / fwdc / fwdplainc | d15 6.3 / 8.7 / 8.6 min | 24 min |
| phase4 (90 jobs) | d15 35 min; rerun 33 min | 35 min |
| phase5 | 2.7 min | 3 min |
| phase5b (72 jobs) | d15 28.7 min | 30 min |
| d15_bb | d27_regen ~10 min | 10 min |
| ftests (73 jobs) | CPU: fruns 15.8 ks, f3b 5.3 ks, f3c 36.2 ks (F3c FGO jobs 38–125 min each, run without the BLAS thread limit); 57 ks / 6 ≈ 2.7 h; long pole ~2 h | **2.5–4 h** |
| repack_corridor | sha256 of 78 GB | 10 min |
| f4 (30 jobs + unpack/repack 38 GB) | f4_replays 25 min | 35 min |
| h_shadows (12 jobs) | room ~4 min per replay | 15 min |
| expO (9 jobs) | FGO batch ~20 min + live | 25–30 min |
| expT (24 jobs) | FGO batch 2050–2180 s + live ≈ 40 min each, 12 in 2 waves | **1.5 h** |
| L (7 jobs) | nolc_t245 17–50 min, lc ~6 min, V-L ~10 min, in parallel | **~1 h** |
| compare | — | 2 min |
| **total (default stages)** | | **≈ 8–10.5 h of machine time** |

- **Opt-in stages:** `d27item3` +15 min; `cl_pred` +30 min (8 FGO replays + 24 GB unpack).
- **Unknowns:**
  - FGO speed with the noise fix: the sizing replay did not log a time. LM is capped at 2 iterations, so it is expected
    to be similar.
  - Whether F3c's 2 h jobs shrink under the thread limit.
  - Memory: 6 parallel T batch FGOs ran before without trouble on 15 GB.
- **Against the freeze** (today 9 Oct, freeze 16 Oct):
  - **The whole default pipeline fits in one overnight run.**
  - Even with flights interleaved between stages, and a second full run after a failure, it fits by 11–12 Oct.
  - That leaves 3–4 days for old-vs-new, numbers.md and the figures.
- **Preconditions to start:**
  1. The derotation change lands (check 4 passes).
  2. This branch and that one are merged into the main checkout, with the tracked tree clean.
  3. No flight is scheduled. Per the cut-order ruling, the safety re-tests run after this if needed.

## 5. Draft: headline UKF/FGO numbers that get old-vs-new rows (from `docs/thesis/numbers.md`, plus METHODOLOGY verdicts)

`rerun_compare.py` covers the rows marked (c). The rest need the comparison extended (or done by hand) from the
`results_pre_final` against `results` JSONs named.

**§6.1 textured dsn (c):**
- FGO r1/r2/r3 (4.59/4.72/4.60), mean/range;
- UKF r1/r2/r3 (4.23/2.14/5.38);
- **the confirmatory test** (EKF3 lower; d < 0 6/7; mean d −0.69 m [−1.16, −0.21]): **the verdict is flagged whichever
  way it falls**;
- noise-floor SD for FGO and for d;
- UKF r1–r9 median/range/SD (5.34 / 1.71–5.96 / 1.55) and the "UKF stable on all 9 usable" wording;
- UKF cruise yaw drift r1–r9 / transition (`d15_drift.json`);
- UKF take-off yaw change |Δ| ≤ 0.79° (`d15_kick.json`).

**§6.2 blank/transition (`blank_behaviour.json`):**
- UKF / FGO baseline error at +10/+30/+60 s after loss (blank);
- end-of-cruise km (†);
- transition +60 s (†);
- heading arms, blank +60 s.

**§6.4 forward sets (c):**
- fwdc FGO and UKF textured r1–r3;
- fwdplainc FGO and UKF textured r1–r3 (UKF r2/r3 take-off kick);
- p1c FGO.

**§6.5 scale (c):**
- FGO baseline / +heading speed ratio (0.997/0.998);
- UKF +heading speed / along-track ratio.

**§6.6 Phase 4 (c):**
- UKF and FGO +heading fwdc/fwdplainc r1–r3;
- +yaw rate;
- heading-arm yaw RMS (UKF / FGO);
- **UKF NEES 6.11** (`phase5b_consistency.json`).

**§7 / §8 bands and counts:**
- P4 FGO textured band [4.189, 5.117] (recomputed);
- fwdc 6/9 and fwdplainc 8/9 primary pass counts, where the misses are UKF/FGO bands.

**C0** (METHODOLOGY "C0 RESULT"): FGO vs UKF with heading, from `phase4_*_arms.json`.

**F-tests** (METHODOLOGY verdicts):

| test | current verdict |
|---|---|
| F1 | NOT met |
| F2 | NOT met |
| F3 | NOT met (gate lockout) |
| F3b | (a) TRUE, (b) FALSE (UKF representation limit) |
| F3c | (a) FALSE, (b) TRUE |

**§15.1, 2(a)** (`f4_test.json`): P1 9/12 FAIL, S1 5/6 PASS, S2 6/12 FAIL, plus the descriptive comparison against the
UKF.

**§15 closed loop:**
- the FGO open-loop contact prediction +169.6 s (only if `cl_pred` is ruled in);
- the per-heading weight 15.9 / 2.9 % and the F3 lockout (D27/F3 re-measurement, ruled).

**§16.1 T** (`t_aggregate.json`):
- the UKF live, FGO live, RTS-UKF and FGO batch RMSE for A–D;
- H-T1 (PASS: gains 0.005/0.015/0.025/0.050, ρ 0.47);
- P-T2 / P-T3 / P-T4 (FAIL) ratios.

**§16.2 O:**
- UKF live 0.63–0.64, FGO live 0.97–1.17, RTS-UKF 0.60–0.64 (cap-free 0.97–0.98), FGO batch 0.33 m;
- error at return / jump;
- H-O1 PASS, H-O2 / P-O3 FAIL.

**§16.3 L:**
- lc / nolc live and hindsight RMSE, lap-5 ÷ lap-1;
- V-L 4.63 vs 4.59;
- H-L1–3 and P-L4 PASS;
- cost (DIAGNOSTIC).

**§17 H:**
- the UKF and FGO shadow drift per loss (S1: 5/15/30 s / move), re-lock 0 ms, P-H5;
- the S1-far shadow table (METHODOLOGY "S1 RE-FLY RESULT"; the bands UKF ≤ 100/200/400/300 and FGO ≤ 50/100/200/150);
- the new r3b shadows;
- the S1→S2/S3 "gap closes" wording.

**Ablation pairs** (yaw-cap gating alone, ruled): S3 `H_s3_r*` vs `H_s3v2_r*`; `cl_fgo_*_v2` vs `_v3`;
`H_safety_fgo_*_v2` vs `_v3`. These are flight results, not this pipeline; listed for the old-vs-new write-up.

## 6. Open questions needing a user ruling

1. **Launch mode.** Per-stage `heavy.py` (the default; flights can interleave; the longest single hold is the ftests
   stage, ~3 h, during which a flight's `flight_lock_acquire` gives up after 1 h), or one `heavy.py` call for the whole
   run (~10 h of `BUILD_LOCK`)?
2. **Closed-loop prediction (`cl_pred`).** Should the offline FGO contact-prediction input be recomputed with the
   corrected FGO? If so, is it only reported as a new file, or are the pre-registered prediction bands restated? The
   closed-loop scores themselves use no offline replay and are unaffected.
3. **F1 calibration.** Is k = 2.385 kept as registered (the default here), or is the 14-job calibration re-run, which
   could re-select k?
4. **D27 item 3 / F3 re-measurement.** The FGO side is scripted (opt-in). Are the D26 flights used (default, isolating
   the model change) or the `_v3` re-flights? The UKF side needs the port's SITL Replay, outside this pipeline: run it
   separately, or report the FGO side only?
5. **Reconstructed T/O/H/L commands.** No committed job lists existed. Please confirm:
   - H S1-far UKF `--no-rts` and the far profile `s1_far_profile.json`;
   - the venv for the T/O/L/H scorers (`venv-tags` is used here);
   - O replays reusing the existing `gnss.npz`.
6. **V-L scoring.** The original `three_way_eval --est` labels were not recorded. Should the V-L check be re-scored
   (labels to be defined), or reported from the new `lc_fgo_notags` output by hand?
7. **H/O/T EKF3 gates.** Keep them hard (default), or make them report-only in case a scorer changed since the committed
   JSONs?
8. **numbers.md §3/§5 sensitivity rows** with UKF/FGO values (clock shift, 0.20 m/s): are they re-run or labelled as
   pre-correction?

## 7. State at the end of this stage

- **Locks:** none held by this stage. No `FLIGHT_LOCK`. A `BUILD_LOCK` was held during this stage by the parallel
  derotation agent's verification job; it was not touched.
- **Data:** nothing written under `~/thesis_data`.
- **Commit:** on `worktree-agent-a55370a40530b58f2`, not merged. Merge after, or together with, the derotation change,
  then dry-run again from the main checkout. Check 4 must pass before launching.
