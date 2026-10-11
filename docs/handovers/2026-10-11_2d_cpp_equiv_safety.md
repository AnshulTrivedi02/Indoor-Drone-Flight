# Item 2d: C++ FGO equivalence for the D18-corrected node, and the UKF/FGO SITL safety re-tests (2026-10-11)

Stage agent, worktree branch `worktree-agent-a16391ff0a1144fd8`, based on `fwd-camera` `cca8e90` (reset from the
unrelated root first). Ruling: METHODOLOGY "RULING (user, 2026-10-11): PLAN AND BUILD TOWARDS REAL FLIGHTS", item 2(d).
METHODOLOGY.md and numbers.md were not edited. Verification only: nothing here is result data.

## Verdict in one line
**The D18 C++ FGO is NOT installed: band C `dsn_tex_r1` FAILS as worded (1.95 mm against 1 mm), a must-pass band
under the install gate written before the run. A RULING IS NEEDED.** Every other must-pass band passes, band A tex now
passes, and the live node path (L1/L2) is bit-identical to the export-driven replay. The two FGO safety re-tests were
therefore NOT flown. The UKF re-tests were flown: (a) ALL PASS; (b) S-A1/S-A3/S-A4 PASS, **S-A2 FAILS AS WORDED again
(5.69 s against 5.5 s), the relay drain recurs.**

## 1. The install gate (written first)
`eval/results/fgo_cpp_equiv_d18/INSTALL_GATE.md`, mtime 13:26:09, before the driver's first step (build START
13:31:17; `driver.log`). Bands, bags and thresholds are the 2026-10-09 ones (same count, same decisions, |Δp| ≤ 1 mm,
|Δyaw| ≤ 0.01°, default Eigen build). Must pass: B1–B5, C on all four bags, L1, L2. B6 optional. Band A blank/trans
reported as worded (known). Band A tex: the ruled threshold-tie exception (2026-10-09 item 1) applies to band A tex
ONLY. The gate file was not committed before the run (a flight was running then; commits wait for no flight); its
mtime is the evidence.

## 2. Build (scratch; NOT installed)
- Source: this worktree = `fwd-camera` `cca8e90`. `diff -rq src/estimators` against the main checkout: empty.
  Changes in the C++ core since the installed `f642cd37` build (`61fec8c`): only `df50ad9` (D18:
  `YAW0_SIGMA` = 1°, `ROLLPITCH0_SIGMA` = 5°, at `init` and the `reanchor` fallback). The Python-side changes since then
  (geometry `geom=None` default, events mode) leave the default path identical.
- Built through `heavy.py`, clean `env -i` PATH, the established cmake line, no `make install`
  (`scripts/step.sh build`): `fgo_cpp_node` `28636bf9…`, `fgo_cpp_replay` `0981e455…`, `fgo_cpp_live_replay`
  `9e4648b0…`, `fgo_cpp_frontend` `ed058257…`, `fgo_cpp_probe` `9511c13a…` (`md5_scratch_build.txt`; md5s are
  path-dependent).
- **Installed binaries UNCHANGED** (`md5_installed_unchanged.txt`): `fgo_cpp_node` `f642cd37…`, replay `714338d0…`,
  live_replay `880beefd…`, frontend `d171077c…`. No backup was needed; `~/opt/fgo_cpp` was not touched, and no
  acceptance set was created.

## 3. Probe
- Python (`fgo_core` from this worktree; `YAW0_SIGMA` 0.017453292519943295 = 1°, `ROLLPITCH0_SIGMA` 5°) vs C++:
  bit-identical on every line except `gate3`/`gate4` (rel 9.8e-12 / 2.2e-11, the known `inv` vs Eigen round-off).
- New Python probe vs the yaw-gate Python probe: only the keyframe lines `kf0`–`kf4` and `gate3` differ (they depend on
  the X(0) prior). Every factor `[A|b]` (flow, range, yaw, heading, yaw-rate, tag, GNSS), the preintegration and its
  covariance are identical. So only the initial prior moved.

## 4. Bands (logs: `eval/results/fgo_cpp_equiv_d18/logs/`)
| band | run | result |
|---|---|---|
| A | dsn_tex_r1 | **PASS**: 10197/10197, 0 decision and 0 gate mismatches (63/63 fired), max / p99 \|Δp\| 0.139 / 0.0098 mm, yaw 1.3e-4° (it FAILED at 1.14 mm under the yaw-gate build) |
| A | dsn_blank_r1 | FAIL as worded (known): 2.5e6 mm; 81 gate mismatches; the Python FGO itself diverges (along-track 2.7 km) |
| A | dsn_trans_r1 | FAIL as worded (known): 5.2e5 mm; 39 gate mismatches; Python diverges (along-track 22.4 km) |
| B1 | fwdc_tex_r1 heading | PASS: 9.6e-5 mm, 4.7e-11°; heading accepted 9184/9539, 0 mismatches; min \|NIS − 9\| 0.028; gate 0/2023 fired |
| B2 / B4 | T_A_r1 live (7774 anchored) / batch | PASS 1.6e-7 mm / PASS 2.6e-9 mm; batch LM 135.725570 (4 it.) both languages |
| B3 / B5 | T_D_r1 live (7755 anchored) / batch | PASS 3.1e-4 mm / PASS 4.8e-8 mm; batch LM 58.588776 (5 it.) both; gate 9/52, 0 mismatches |
| B6 (opt.) | O_r1 GNSS live / batch | PASS 4.2e-4 mm / PASS 3.7e-7 mm; batch LM 29.374977 (10 it.) both; gate 15/1457, 0 mismatches |
| C | dsn_tex_r1 baseline | **FAIL as worded: max / p99 \|Δp\| 1.95 / 0.353 mm**, yaw 2.4e-3°; 16 gate decision mismatches |
| C | fwdc_tex_r1 heading | PASS 8.9e-5 mm |
| C | T_A_r1 live (+ batch) | PASS 2.6e-7 mm (batch 2.2e-9) |
| C | T_D_r1 live (+ batch) | PASS 5.1e-4 mm (batch 4.0e-8) |
| L1 | dsn_tex_r1 | **PASS**: adapter states bit-identical to the export-driven C++ replay; 9919 ODOMETRY, 0 CRC errors, byte-identical to pymavlink; time_usec 9919/9919 |
| L2 | fwdc_tex_r1 heading | **PASS**: bit-identical; 9840 ODOMETRY, 0 CRC errors |

Live step time (L1 / L2): median 0.53 / 0.96 ms, p99 0.91 / 1.69 ms (budget 33 ms), as before.

### 4.1 The band C failure (post-hoc diagnostic, `onset_c_dsn_tex.txt`; evidence, NOT a pass)
- Band C compares the NATIVE front end (`fgo_cpp_frontend`, offline; it rebuilds the stream from the bag) with the
  export-driven C++ replay. The front end's dejittered IMU stamps differ from Python's `np.polyfit` by ≤ 1.1e-13 s
  (as in every earlier stage), so `t_init` differs in the last bits.
- **States agree to 8.6 µm (yaw 1.1e-5°) until the first yaw-cap gate decision flip at t = 241.12 s** (keyframe 6970):
  trace 0.0400064 (export-driven: fired) against 0.0399997 (front end: not fired), straddling the 0.04 threshold;
  max relative trace difference before it 2.2e-4.
- Then 16 mismatches in 8 pairs (241.1/241.3, 254.0/254.1, …, 335.5/335.6 s): one run fires one check earlier than the
  other. |Δp| grows to 1.95 mm.
- **This is the same threshold-tie mechanism as the yaw-gate stage's band A tex failure** (ruling 2026-10-09 item 1),
  and consistent with the recorded growth of the gate-trace drift with flight length (conditioning diagnostic,
  2026-10-09). Consistent, not proven: the flip moved from the A comparison (now passing, 0 mismatches) to the C
  comparison with the new prior.
- **Which path flies:** `fgo_cpp_node` uses `live_adapter.cpp` (in `fgo_cpp_core`), not `fgo_frontend.cpp`. L1/L2 show
  the live adapter bit-identical to the export-driven replay, which passes band A. The native front end is not the
  flown path.
- Extra post-hoc row: the emulate-gemv build against Python on dsn_tex also flips (14 gate mismatches, 1.67 mm),
  while the default build matches Python's decisions. Diagnostic only, not a band.

### 4.2 The ruling needed (options; none chosen here)
1. Accept band C dsn_tex as the ruled threshold-tie mode (extend the 2026-10-09 item 1 exception from band A to band C)
   and install the D18 node via the established recipe, then fly `H_safety_fgo_{a,b}_v4`.
2. Require the forced-gate check for band C first (front end forced to the export-driven run's decisions, then re-band
   it), and install only if that comes back within 1 mm.
3. Hold the install (the flown node stays `f642cd37`, old priors) until the gate recursion is made reproducible (the
   2026-10-09 rejected options would need re-opening).

## 5. UKF SITL safety re-tests (short verification flights; the installed port `~/ardupilot_ukf` `abb0357d`, vehicle `5f94ea1a…`, checked unchanged)
**Length justification (standing rule 2026-10-10):** the existing `safety2_ukf_{a,b}_profile.json`, unchanged:
wait_fix → 1.3 m move at 0.2 m/s → 20 s hold (pre-failure attitude reference for S-A1, settled estimator) → failure →
landing (~9–11 s to disarm). The trailing 40 s hold only bounds the wait for the trigger. S-A2–S-A4 need only the
failure-to-disarm interval.

Driver: `tools/run_ukf_refly.sh sa3 sb3` (new cases `sa3`/`sb3`; existing cases unchanged). Harness files identical to
the main checkout (`cmp`). Scored with `eval/h_safety_score.py --from-effect`; S-A2 bound **0.75 s for (a), 5.5 s for
(b)**: the bounds the previous re-tests used (`safety_ukf_a_v2.json` 0.75, `safety_ukf_b_v2.json` 5.5, the pre-registered
`AID_TIMEOUT` bound). The brief said 0.75 for all; at 0.75 s (b) fails as well (5.69 s).

### `H_safety_ukf_a_v3` (TFAIL at t_f 79.35 s, effect 79.99 s): ALL PASS (`eval/results/expH/safety_ukf_a_v3.json`)
- S-A1: roll 0.37°, pitch 0.10°, yaw 0.31° (n 98). PASS.
- S-A2: "Thesis nav: UKF position lost" and LAND (reason 6) in the same log tick as the forced-invalid text (0.00 s). PASS.
- S-A3: disarm +9.14 s; max tilt 0.57°; touchdown vz −0.47 m/s; horizontal displacement 0.58 m; no breach. PASS.
- S-A4: one LAND entry, no re-arm. PASS.

### `H_safety_ukf_b_v3` (bridges KILLed at t_f 76.78 s): S-A1, S-A3, S-A4 PASS; **S-A2 FAILS AS WORDED** (`safety_ukf_b_v3.json`)
- S-A1: roll 0.32°, pitch 0.26°, yaw 0.53° (n 105). PASS.
- **S-A2: "position lost" at +5.69 s against 5.5 s. FAIL as worded.** The watcher-path LAND (reason 2) came at +1.71 s.
- S-A3: disarm +10.52 s; max tilt 2.19°; touchdown vz −0.52 m/s; displacement 1.07 m; no breach. PASS.
- S-A4: one LAND entry, no re-arm. PASS.
- **The relay drain recurs** (`eval/results/expH/safety_ukf_b_v3_drain.txt`, `scripts/ukf_b_drain.py`): the FC received
  OF rows (quality > 0) until 77.47 s, **0.69 s after the kill**; the trigger came **exactly 5.00 s after that last
  flow row** (the UKF's 5 s aiding timeout). Recomputed for v2 with the same script: drain +0.75 s, trigger +5.00 s after
  the last OF. (METHODOLOGY's 0.71 s for v2 is measured from 58.67 s; the scorer's t_f is 58.638 s. Reference instant
  only, not a contradiction.)
- As in v2: the fly_trial log reports "FAILED: safety watcher lost in flight … bridge=0; landing" (the designed
  dep-loss LAND path), `run_trial exit 1`, and no `metadata.yaml`; the BIN came from
  `~/ardupilot_ukf/ArduCopter/logs/00000093.BIN` (the UKF tree).

## 6. FGO SITL safety re-tests: NOT FLOWN
`tools/run_fgo_refly.sh` has new cases `sa4`/`sb4` (`H_safety_fgo_{a,b}_v4`; same settings as `sa`/`sb`), added but
NOT flown, pending the band-C ruling. The names do not exist. If the install is cleared: install per the yaw-gate
recipe (back up `~/opt/fgo_cpp` first; old md5s above), build a new acceptance set from this stage's
`d18/dump` (dsn_tex export, `cpp_dsn_tex_r1_baseline.{kf,yawgate}.f64`, `L1.kf.f64`) into a NEW permanent directory,
run the replay/live `cmp` acceptance via heavy.py, then `bash tools/run_fgo_refly.sh sa4 sb4` and score with
`--from-effect --a2-bound 0.75`.

## Files
- Committed: `eval/results/fgo_cpp_equiv_d18/` (INSTALL_GATE.md, scripts, logs, driver logs, probe outputs, md5 lists,
  onset diagnostic), `eval/results/expH/safety_ukf_{a,b}_v3.json`, `safety_ukf_b_v3_drain.txt`, the driver cases, this
  handover.
- Scratch only: `/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/d18/`
  (build, build_emu, dump with every export and kf/gate file, out).
- Trial data: `~/thesis_data/{trials,closed_loop}/H_safety_ukf_{a,b}_v3` (verification flights, never result data).
