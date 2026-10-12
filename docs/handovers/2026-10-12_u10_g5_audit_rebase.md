# Handover, 2026-10-12: U10 N1/G5 on H_s2v2_r1, the u10_gate.py audit against the SIGNED band, and the port rebases

**Stage:** one stage agent.
- **thesis_ws branch:** `worktree-agent-a5792858aabb1c0d5`. It started on the unrelated `main` root and was reset to
  `fwd-camera` `0c32f14` ("U10 band SIGNED OFF 2026-10-12"). NOT merged.
- **Not edited:** METHODOLOGY.md, `docs/u10_replay_gate_band.md` (signed), `docs/rung1_preregistration.*`,
  `eval/real_score.py`. Stored trial data are not modified.
- Every build and Replay ran under `heavy.py`, one at a time, with no flight running. Commits and the rebases were made
  only with FLIGHT_LOCK absent and no `arducopter` process (re-checked as a separate step before each). A watcher SITL
  bench (`wbench_ground`, another agent) held FLIGHT_LOCK on and off during this stage.

## 1. N1 / G5 on the SITL `H_s2v2_r1` demo: the RULE, not tooling

**Cause.** The rung-1 §4.3 rule (`motion_onset_path`, signed JSON: onset 0.15 m/s held 1 s with a 1 s boxcar;
segment = the first `init_path_m` 2.0 m of mocap path after the onset; refused if the segment's largest horizontal
distance from its first point is below `min_extent_m` 1.0 m) refuses the segment, and N1 then fails G5. Evidence
(`eval/results/u10_final/score_H_s2v2_r1_sim_truth_inst.json` and the SIM truth):
- W = [55.42, 385.68] s (take-off 30.42 s + 25 s; landing 390.68 s − 5 s).
- The flight's only horizontal move longer than 1 m is the 3.5 m northward move during the climb, at about
  34–48 s: **before W opens**.
- Inside W the vehicle hovers at (0, 3.5) and makes ±0.5 m lateral tags (x = +0.57 at 110 s, −0.5 at 126 s, +0.5 at
  142 s, −0.5 at 158 s, …). The onset is the first tag (107.23 s); the 2.0 m of path is used up going back and forth by
  125.67 s; the largest distance from the onset point is **0.605 m < 1.0 m**.
- EKF3 (0.615 m) and the onboard UKF are refused identically: the cause is the mocap profile, not an estimator, the
  reader, the clock map (SIM truth is on the FC clock) or a missing field.
- **N1 stays fail-closed** (signed). Nothing in `real_score.py` was changed: any change to the onset or the extent
  would redefine the signed §4.3 rule.
- **Context:** H_s2v2_r1 is a SITL hover/tag closed-loop flight (Replay environment `UKF_EXTPOS=1 UKF_EXTYAW=1`, test
  hooks), not a rung-1 result profile. In the real protocol the hand-carried log H is gated in plumbing mode only (no
  score, G1 and G3), so N1 cannot fire on H. The demo fed it through gated mode; G5 FAIL is the correct result there.

**Demo re-run** (`eval/diag/u10_audit/gate_demo.sh`, results `eval/results/u10_audit/`, gate only on the stored
Replay `3c3b62bb` outputs and the committed SIM-truth scores; D_max the signed default):

| input | verdict |
|---|---|
| `cl_a_tex_half` | FAIL: G5 (5.154 m > 1.0 m over a 150 m corridor) |
| `cl_ukf_b_tex_r1_half_v2` | PASS (G6 applies) |
| `H_s2v2_r1`, gated | FAIL: G5 (N1: segment extent 0.605 m < 1.0 m) |
| `H_s2v2_r1`, plumbing (as an H log) | PLUMBING PASS |
| `H_s2v2_r1`, verification (as a V log) | VERIFICATION PASS (G5 reported, not judged) |
| `cl_a_tex_half` without `ukf_stats.csv` | FAIL: G3 (rule 1), G5 |
| `--d-max 2.0` | refused |
| set of the 3 gated records | NOT EVALUABLE (3 < 4) |

Same verdicts as the 2026-10-12_u10_final demo.

**What a rung-1 result profile must contain for G5 to be computable** (from the signed rule; tested on synthetic
profiles in `eval/u10_gate_test.py`, the last three tests, with the signed JSON's `drift` section):
1. a motion onset INSIDE W: mocap horizontal speed (1 s boxcar) above 0.15 m/s for at least 1 s, after take-off +
   25 s. The profile's 30 s hover puts the first leg about 5 s into W;
2. the first 2.0 m of mocap path after that onset must reach at least 1.0 m from the onset point. A straight first
   leg of at least 2 m guarantees it (a 2 m out-and-back leg: extent 2.0 m, computable; 0.6 m legs: refused);
3. at least 5 replayed-`XUKO` samples in that segment and at least 10 mocap samples in W (trivial at the rates used).

**Check against the rung-1 documents:** the profile (prereg §3.1) is a rectangle or out-and-back, two laps, at
0.3–0.5 m/s, with legs **[TBD-S]**; the result sortie card (`docs/rung1_flight_cards.md` §5 item 3) has "legs __ m"
blank. **So G5 is computable on the nominal profile only if legs of at least 2 m are chosen.** Prereg §4.3 already
requires, as a [TBD-S] confirmation before any result flight, that "2.0 m must not exceed the first leg length".
**Residual risk:** ALT_HOLD has no position hold, so a hover correction in the ~5 s of hover inside W can trigger the
onset early; if it drifts back and forth it eats into the 2 m and can leave the extent below 1 m, failing G5 (N1).
A first leg of at least 3 m, flown straight from the hover, leaves margin. Recommendation for the user's [TBD-S]
entry, not made here: leg length ≥ 2 m (≥ 3 m preferred), first leg straight.

## 2. Audit of `eval/u10_gate.py` against the SIGNED document

Tests: `eval/u10_gate_test.py`, **57 / 57 pass** (synthetic: a dataflash .BIN from `df_reader.write_fmt/write_rec`,
tiny CSVs, a score JSON with the .BIN's sha256). `eval/real_score_test.py` 16 / 16 still pass.

### 2.1 Traceability (document clause → code → tests: PASS case / FAIL case)

| clause (signed doc) | code | pass test | fail test(s) |
|---|---|---|---|
| §4.1 preconditions, N5: score computed on THIS Replay output (`estimators.*.sha256`) | `preconditions()` | `test_base_gated_flight_passes`; `..._TUM_row_is_exempt` (a) | `test_N5_score_of_another_log_fails`; `test_N5_any_log_row_of_another_log_fails...` (b); `test_N5_missing_sha_key_fails_without_crash` |
| N5 + rule 2: UKF = `XUKO` / message `RUKO`; EKF3 = `XKF1@100` / `XKF1` | `preconditions()` (`REQUIRED_ROWS`) | base | `test_rule2_UKF_read_from_onboard_XUKO_fails` |
| N5: 0 undeclared types, 0 bad FMT, 0 re-declared ids | `preconditions()` | base | `test_integrity_redeclared_id_fails`; `test_integrity_undeclared_type_fails` |
| G1: `mode,log`, `resolved_at_ms`, the four source labels `log_parm` | `g1()` | base | `test_G1_source_not_log_parm_fails`; `_mode_not_log_`; `_never_resolved_`; `_missing_geometry_` |
| G1: first UKF row and geometry resolution before the first ARM (ArmState 1) | `g1_before_arming()` | base | `test_G1_init_after_arming_fails`; `test_G1_header_only_shadow_fails_never_initialised` |
| N3: late PARM passes only as the value in use or a lever arm | `g1_late_parm()` | `test_N3_late_parm_same_value_passes`; `test_N3_late_lever_arm_passes` | `test_N3_late_parm_changing_value_fails`; `test_N3_late_other_parameter_fails` |
| N3: missing ARM fails a gated flight; not applicable on H | `g1_before_arming(need_arm)` | `test_N3_missing_ARM_not_applicable_on_H` | `test_N3_missing_ARM_fails_gated_flight` |
| G2: SS bit 3, Healthy = 1, FlowAgeMs < 5000 on every row in W | `g2()` | base; `test_G2_bad_row_outside_W_passes`; `test_G2_flow_age_4999_passes` | `test_G2_one_bad_row_in_W_fails[SS / Healthy / FlowAgeMs]` |
| N2: rows cover W (gaps incl. W's ends ≤ `max_gap_s` 0.5 s) | `g2_coverage()` | `test_N2_gap_inside_W_le_max_gap_passes` | `test_N2_gap_inside_W_gt_max_gap_fails`; `test_N2_gap_at_W_end_fails` |
| G3: `n_chol_fail` = 0 | `g3()` | base; `test_G3_retries_without_fail_pass` | `test_G3_chol_fail_fails` |
| Rule 1: missing `ukf_stats.csv` / missing row FAILS | `g3()` | base | `test_rule1_missing_stats_fails`; `test_rule1_stats_without_n_chol_fail_row_fails` |
| G4: UKF ≤ max(2.0 × EKF3_R, EKF3_R + 0.10 m) | `g4()` | `test_G4_at_band_passes_and_above_fails` (a); `test_G4_floor_branch` (a) | the same tests (b); `test_G4_not_computable_fails` |
| G5: start-aligned drift ≤ D_max | `g5()` | `test_G5_at_D_max_passes_above_fails` (a) | (b) |
| N1: not computable = FAIL | `g5()` | (any computable case) | `test_N1_not_computable_fails`; the `H_s2v2_r1` demo |
| D_max = 1.0 m (signed) | `D_MAX_M`, `flight()` | `test_D_max_default_is_signed_and_other_values_refused` (default, `--d-max 1.0`) | the same test (`--d-max 1.5` refused) |
| G6: applies only with onboard `XUKF`; fails without replayed `RUKF` | `g6()` | `test_G6_does_not_apply_on_stock_flown`; `test_G6_E1_within_band_passes` | `test_G6_onboard_without_replayed_fails`; `test_G6_E5_increment_fails` |
| G6 pairing: exact TimeUS from the later initialisation + 10 s | `g6()` | `test_G6_pairing_starts_after_later_init_plus_10s` | (E5/E1 fail tests use the same pairing) |
| N6: E1 is 3-D | `g6()` | `test_G6_E1_within_band_passes` | `test_N6_E1_is_3D_vertical_difference_fails` (0 horizontal, 0.06 m vertical) |
| §2 item 1 / §7: H = plumbing, G1 and G3 | `flight()` (no score) | `test_H_plumbing_pass_and_fail` (a) | (b) |
| §7 step 2: G1–G3 on V | `flight(--verification)` | `test_V_judges_G1_to_G3_only` (a) | (b) |
| Set rule: every flight passes | `gate_set()` | `test_set_four_passing_is_PASS` | `test_set_one_failing_is_FAIL` |
| ≥ 4 usable flights | `set_min_flights()` | `test_set_four_passing_is_PASS` | `test_set_three_is_NOT_EVALUABLE` |
| N4: ONE Replay binary (md5); missing md5 refused | `set_single_binary()` | `test_set_four_passing_is_PASS` | `test_N4_mixed_binaries_INVALID`; `test_N4_missing_md5_refused` |
| Each score on its own Replay log | `preconditions()` (per flight) + `set_distinct_logs()` | the N5 pass tests; 4 distinct logs → PASS | the N5 fail tests; `test_set_same_log_twice_refused`; `test_set_duplicate_name_refused` |
| Set takes gated result flights only | `gate_set()` | 4 gated → PASS | `test_set_refuses_H_and_V_records` |
| No changed band (§1, §10; G6 [TBD-V] confirmed ONCE) | `set_same_bands()` | 4 equal → PASS | `test_set_refuses_mixed_G6_bands_and_unsigned_D_max` |

**Procedure clauses, not tool-checked (by design; checking them would be stricter than the signed N5):** the default
Replay environment (§2; §7's commands write no `env.txt`); that the score used the signed prereg (`real_score.py`
loads it strictly; its sha256 is in the score); "usable" (rung-1 §3.3 exclusions, decided by the user); the Replay
built from the flying commit (§2); the `XKF1@100` vs `XKF1@0` TimeUS check (refused by `real_score.py` /
`replay_gate.py` before a score exists). The Replay md5 is NOT pinned to `3c3b62bb`: §2 expects a new binary once U4
and board-h743 are merged; N4 is one md5 across the set.

### 2.2 Fixes made IN THE CODE (the document is unchanged)

1. **D_max:** `D_MAX_M = 1.0` (signed); `--d-max` defaults to it and any other value is refused ("a changed band is a
   dated amendment"). Before: required, no default, any value accepted. The flight record carries `d_max_m`.
2. **V mode** (`--verification`): §7 step 2 says "G1–G3 on V", which the tool could not do (only H plumbing or the full
   gate). G1–G3 judged, G4–G6 computed and reported (`judged: false`), verdict "VERIFICATION PASS/FAIL", refused by
   `set`.
3. **N5 scope:** the sha256 check covered UKF and EKF3 only; the document says `estimators.*.sha256`. Now every row
   read from the log (every row with a `physical_record`) must match; a TUM row (FGO) carries its own file's sha256
   and is exempt. Missing keys FAIL instead of raising KeyError.
4. **Fail-closed instead of crashing:** G4 with a missing or non-finite value → not passed (was KeyError); G5 with a
   non-finite value → N1 FAIL; a header-only or column-less `ukf_shadow.csv` → G1 "never initialised" / G2 fail (was a
   `genfromtxt` crash); a non-integer `n_chol_fail` → G3 fail; malformed `ukf_geometry.csv` rows → G1 fail; NaN in
   `SS` / `FlowAgeMs` counts as a bad row.
5. **Set:** refuses two records of the same Replay log or the same score (sha256): "each score on its own Replay
   log"; refuses V records; refuses records gated with a D_max other than the signed one or with different G6 bands.
   Each flight record now carries `g6_bands`.
6. **One function per criterion:** `g1_late_parm()`, `g1_before_arming()`, `g2_coverage()`, `preconditions()`,
   `set_single_binary()`, `set_distinct_logs()`, `set_same_bands()`, `set_min_flights()` split out; docstring
   updated from "FOR FINAL SIGN-OFF" to SIGNED.

No band, threshold or definition changed; the 2026-10-12_u10_final demo verdicts are reproduced.

## 3. Port rebases (`~/ardupilot_ukf`)

Scripts: `eval/diag/u10_audit/port/`; logs: `eval/results/u10_audit/`. Done with FLIGHT_LOCK absent (17:32).
`ukf-jitter-fix` NOT moved (`f30f6ffa2f`); the checkout is back on it, clean; no worktree left (only the
pre-existing `~/ardupilot_diag`, not ours). Nothing installed.

| branch | old tip (tag kept) | new tip | commits on `f30f6ffa2f` |
|---|---|---|---|
| `board-h743` | `0156bfc34e` (`board-h743-pre-rukx`) | **`6e7c373691`** | `5b4ca48738` (2a build option), `53ec88be5f` (forced-arm guard), `6e7c373691` (NEW fix-up) |
| `u4-gndclr` | `53bac01636` (`u4-gndclr-pre-rukx`) | **`746e132a9e`** | `746e132a9e` (U4) |

- **Both rebases applied without conflicts** (git's 3-way merge; `AP_Logger.cpp`'s hunk is under
  `APM_BUILD_TYPE(APM_BUILD_Replay)`, so the board's flying log format is unchanged).
- **board-h743 fix-up `6e7c373691`:** `write_end_stats()` (added by `e88aa34a3d`, stdio) now inside
  `AP_NAVUKF_REPLAY_IO_ENABLED` (`(void)path` otherwise): the item handover `2026-10-12_xuko_u10_h10.md` §1.6 flagged.
  SITL behaviour unchanged (the guard is on for SITL). The `UKF_LOG_NAME()` rename merged into all 5 records.
- **board build** (`tools/build_board_fw.sh MatekH743`, ref `board-h743` = `6e7c3736`, under heavy.py; output
  `~/thesis_data/fw_builds/MatekH743_with_6e7c3736_20261012_173243/`, apj md5 `91486aa4c633570cc74d6513d4100edd`):
  **every check PASS**: flash free 134 692 B, 0 warnings, NavUKF + NavFGO present, identity `6e7c3736`.
  - **Stack check, first real exercise since the `-o` script fix:** 0 `COMPILE FAILED`; all 5 thesis sources produced
    `.su` files (AP_NavUKF, AP_NavFGO, AP_AHRS_UKF, AP_AHRS_FGO, AP_AHRS). Limit 1300 B; largest thesis frame **648 B**
    (`AP_NavFGO.cpp`, an `Imu&` function); next `AP_NavUKF` 512 B (an `Ev&` function); chain-6 bound
    **2960 B ≤ 3584 B** (half of the 7168 B main stack). The real margin remains bench check P7.
  - The script exited 4 ("CLEANUP ERROR: 3 worktrees listed, 2 before") **only because this stage's u4 worktree was
    added while the board build ran**; its own temporary worktree was removed (`/tmp/bfw_*` gone) and `board-h743` did
    not move. Not a build defect. (Script caveat for the record: the worktree-count check is not robust to concurrent
    worktree changes by other jobs.)
- **u4-gndclr Replay build** (temporary worktree, SITL `waf replay`, 0 warnings): Replay md5
  `0f3644a29deb4712722a930c61288910`. **Byte-identity against the installed Replay `3c3b62bb`** on the 5 SITL logs
  (each in its stored environment: `X=0` ×3, `UKF_EXTYAW=1`, `UKF_EXTPOS=1 UKF_EXTYAW=1`): **25 / 25 CSVs IDENTICAL**
  (`ukf_shadow`, `ukf_inputs`, `ukf_derot`, `ukf_geometry`, `ukf_stats`); end of run 0 / 0 on all five. (The U4 path
  is inert when the range is Good, as on all five logs.) The replayed .BINs were not compared (FMTU process-clock
  stamps differ run to run).
- **For the later merge of the two branches:** u4's two new `fprintf((FILE *)_georep, ...)` lines (`u4_gndclr_first`,
  `u4_init_from_gndclr`) must become `ukf_fprintf`/`ukf_fflush` when merged with board-h743, or the board build loses
  its no-stdio property / fails. Not done here (the branches are kept separate).

## 4. Open / next

1. The user's [TBD-S] entries for the rung-1 profile: leg length ≥ 2 m (≥ 3 m preferred) so that G5 is computable
   (§1). Without it a short-leg profile fails every flight on N1.
2. Merge this branch into `fwd-camera`: the coordinator's call. `eval/diag/u10_final/gate_branch_tests.py` (old
   worktree paths, scratch data) is superseded by `eval/u10_gate_test.py` and left unchanged for the record.
3. METHODOLOGY entry for this stage (the coordinator / user).
