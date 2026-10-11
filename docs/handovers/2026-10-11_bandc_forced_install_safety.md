# Band C with forced gate decisions; install of the D18 C++ FGO node; FGO safety re-tests v4 (2026-10-11)

Stage agent, worktree branch `worktree-agent-a77df11041902ee58`, reset to `fwd-camera` `b908abf` first (it had been
made from the unrelated root). Ruling: METHODOLOGY "RULINGS (user, 2026-10-11): Band C; UKF safety (b) S-A2; records",
item 1 (option (ii)). METHODOLOGY.md and numbers.md were NOT edited. Verification only; nothing here is result data.
Results directory: `eval/results/fgo_cpp_bandc_forced/`.

## 1. The switch (commit `2610bdb`; diff minimal, defaults unchanged)
- CMake option **`FGO_CPP_FORCED_GATE`, OFF by default** (the `FGO_CPP_EMULATE_NUMPY_GEMV` pattern). The gate line in
  `FGO::keyframe` is `const bool fire = FGO_GATE_FIRE(kk, tr);`. With the option OFF, the macro expands to
  `((tr) > ATT_VAR_GATE)`, the old expression. With it ON, `forced_gate_fire(kk, tr)` (appended at the end of
  `fgo_core.cpp`, inside `#ifdef`) reads the Python gate log named by env `FGO_CPP_FORCED_GATE_LOG` (rows t, k,
  trace, fired), keyed by keyframe index k. The trace is still computed and logged. It aborts if the variable is unset
  or a check falls on a k that Python never checked.
- The macro and the helper sit at the END of the header / source, so no line above them moved.
- **Unreachable in the flown node:** it is a compile-time option. The install cmake line does not set it
  (`FGO_CPP_FORCED_GATE:BOOL=OFF` in the install CMakeCache). `strings`/`nm` show 0 matches for `FORCED_GATE` /
  `forced_gate_fire` in all four installed binaries and in the scratch OFF binaries.

## 2. Switch-OFF byte-identity (`md5_builds.txt`, `ident_switch_off.txt`)
- **Control first:** unmodified HEAD `b908abf` (its `src/estimators` is identical to the 2d source `cca8e90`), built
  in scratch `bcf/build`.
  - replay `0981e455`, front end `ed058257`, live replay `9e4648b0`, probe `9511c13a`: **identical to the 2d build**.
  - node `8c116954`, against 2d's `28636bf9`. The two are identical after replacing the embedded worktree path
    string (7 occurrences, rcutils `__FILE__`), except the 20-byte `.note.gnu.build-id`.
- **Switch OFF (`2610bdb`):** same source and build paths, all 8 objects recompiled. **All five md5s are identical to the
  control** (node `8c116954`, replay `0981e455`).
- **Outputs:** the OFF build was run on the four Band C bags (export-driven replay and native front end) and on L1
  (live adapter, `--imu-stamp header --arm-source param --delay 0.20`). Every output is **byte-identical** to the 2d
  build's outputs in `d18/dump`: kf, yawgate, avg, tum, batch, events, frontend.json, `L1.mav.bin` and `L1.live.f64`.
  Wall-clock timing is excluded (step_ns files, `batch_s`, and the step_ns column of `L1.live.f64`).

## 3. Forced Band C: PRE-REGISTERED (`PREREG.md`, commit `b3ec6f4`, before any forced run), then run: **PASS**
- **Design:** both the export-driven C++ replay and the native front end are forced to the Python replay's own gate
  log. `compare_kf` compares forced replay with forced front end on the 2d Band C bags.
- **Pass rule:**
  - max |Δp| ≤ 1 mm on every bag;
  - the construction check (same checks, same k sequence, same fired flags as Python) PASSES for every forced run;
  - same count, |Δyaw| ≤ 0.01°, and 0 factor-flag mismatches.
- **Switch validity control:** the forced replay must be byte-identical to the unforced 2d replay.
- **Results (`RESULT.md`, `logs/forced_*.log`):**

  | bag | max \|Δp\| (mm) |
  |---|---|
  | dsn_tex_r1 | **0.111** (was 1.95 unforced) |
  | fwdc_tex_r1 | 8.9e-5 |
  | T_A_r1 | 2.6e-7 |
  | T_D_r1 | 5.1e-4 |

  - On every bag: count equal, |Δyaw| ≤ 3.6e-5°, 0 factor-flag mismatches.
  - The construction checks PASS 8/8.
  - The switch validity control is byte-identical on all four bags (including the room batches).
- **The forcing overrode exactly ONE decision in total:** the front end's 241.1 s threshold tie on dsn_tex.

## 4. Install (the switch-OFF build; recipe of 2026-10-09)
- **Backup:** `~/opt/fgo_cpp_backup_f642cd37_2026-10-11/bin/` (node `f642cd37`, replay `714338d0`, live replay
  `880beefd`, front end `d171077c`).
- **Built** from this worktree's source (this stage could not merge) in `~/opt/src/build-fgo_cpp-d18`, with the
  default cmake line, then `make install` to `~/opt/fgo_cpp`.
- **Installed:**
  - **`fgo_cpp_node` `f642cd37…` → `4c07374b5c18ce1eda556d5bb9ad0768`**;
  - replay `138962e5…`, live replay `358d9c53…`, front end `1e5c946d…`.
  - These md5s differ from the scratch build's because of the build and install paths (RPATH, `__FILE__`).
  - **Installed node vs the scratch OFF node `8c116954`:** `.text` (858,311 B) and `.rodata` are byte-identical
    (`objcopy --only-section` + `cmp`, re-checked after both v4 flights with the md5 still `4c07374b`). So the flown
    node is the proven switch-OFF code.
- **Acceptance** (`~/thesis_data/acceptance/fgo_d18_bandc/`, SHA256SUMS; inputs from the 2d dump, which §2 shows are
  the OFF build's outputs): inputs OK, **ACCEPT replay** (kf + yawgate `cmp`), **ACCEPT live (node path)** (L1 kf `cmp`).
  Log: `logs/install.log`.
- **To be recorded in METHODOLOGY by the caller:** the installed node md5 is now `4c07374b…`, and its source is the
  `2610bdb` tree. The default code is unchanged from `fwd-camera`: the switch is compiled out.

## 5. FGO SITL safety re-tests v4 (short verification flights, `tools/run_fgo_refly.sh sa4 sb4`): ALL PASS
- **How they were flown:**
  - Driver cases `sa4`/`sb4` (added in 2d, already in `fwd-camera`), the settings of `sa`/`sb`, profile
    `safety2_fgo_profile.json` (unchanged).
  - Harness files `cmp`-identical to the main checkout.
  - Under FLIGHT_LOCK, one at a time.
  - Node: the installed `~/opt/fgo_cpp/bin/fgo_cpp_node` (`4c07374b`), as `metadata.yaml` records, with time_ref and
    0.10 s.
- **Scoring:** `eval/h_safety_score.py --from-effect --a2-bound 0.75`, giving `eval/results/expH/safety_fgo_{a,b}_v4.json`.
  - The failure in both runs is the KILL of the node, so S-A2 is timed from the kill (`t_failure_effect` None, as
    in v3).
- **`H_safety_fgo_a_v4`** (KILL at t_f 62.98 s): **S-A1–S-A4 PASS.**
  - S-A1: roll 0.24°, pitch 0.41°, yaw 0.29°.
  - S-A2: "Thesis nav: FGO position lost" plus LAND (reason 6) at +0.60 s, against 0.75 s.
  - S-A3: disarm +9.46 s; tilt 2.22°; touchdown vz −0.51 m/s; **displacement 1.45 m against 1.5 m (near the
    bound)**; no breach.
  - S-A4: one LAND, no re-arm.
- **`H_safety_fgo_b_v4`** (KILL at t_f 61.57 s; watcher dep-loss land on): **S-A1–S-A4 PASS.**
  - S-A1: 0.12° / 0.09° / 0.64°.
  - S-A2: +0.62 s.
  - S-A3: disarm +9.37 s; tilt 1.01°; vz −0.52 m/s; displacement 0.21 m; no breach.
  - S-A4: one LAND, no re-arm.
  - As in v3, fly_trial reports "FAILED: safety watcher lost in flight … bridge=0; landing" (the designed dep-loss
    path) and `run_trial exit 1`. The BIN came from `~/ardupilot_ukf/ArduCopter/logs/00000095.BIN`.
- **S-A2b** (pre-registered 2026-10-11: trigger time measured from the last flow message received by the FC, bound
  5.5 s): **NOT APPLICABLE to either run.**
  - The failure here is the FGO node, not the flow path. The FC kept receiving OF rows (quality > 0) until after
    disarm: last OF at kill +10.32 s (b) and +44.93 s (a).
  - The trigger therefore came 9.70 s / 44.33 s BEFORE the last flow message
    (`eval/results/expH/safety_fgo_b_v4_flow_after_kill.txt`, computed with the 2d drain script).
  - S-A2b is meaningful only where the failure cuts the flow feed: UKF (b).
- **Observation (not a criterion):** the S-A2 delay is 0.60–0.62 s here, against 0.249 s in `H_safety_fgo_b_v3`.
  It is still inside 0.75 s, but with less margin. Not investigated.

## Files
- Committed: `eval/results/fgo_cpp_bandc_forced/` (PREREG.md, RESULT.md, md5_builds.txt, ident_switch_off.txt,
  scripts, logs), the switch in `src/estimators/fgo_cpp/`, this handover.
- Scratch: `/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/bcf/` (builds,
  outputs, flight driver logs).
