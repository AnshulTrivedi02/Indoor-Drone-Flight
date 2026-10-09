# UKF flow derotation: bias-corrected rate made the default (2026-10-09)

Stage agent, worktree branch `worktree-agent-a84982284acff5fce`, from `fwd-camera` 7f23197. Ruling: METHODOLOGY
"RULINGS (user, 2026-10-08) … UKF flow derotation corrected", item 3. This is a MODEL CORRECTION. **Only the
implementation and its verification are in this stage.** The re-run of every offline UKF result (item 3(a)/(b)) is
NOT done here.

No simulator was run, and no trial directory was written. Every replay ran through `heavy.py`, one step at a time.
No flight was running (`pgrep -fa '[a]rducopter'` empty, no `FLIGHT_LOCK`) before the runs or before the commits.

## 1. What changed

**Commit 1 (a966d7d), harness only, no estimator change.** It adds an off-by-default `UKF_OUT_ROOT` to
`src/estimators/ukf_replay.py` (the `OUTDIR` line) and `src/estimators/room_ukf_replay.py` (the `D`/`OUT` lines).
- It mirrors the FGO's `FGO_OUT_ROOT`.
- Outputs go to `<root>/<trial>/ukf…/` or `<root>/<trial>/room_ukf…/`. Inputs are still read from the trial directory.

**Commit 2, the correction.**
- **`ukf_replay.py`, flow branch** (formerly the `APIN == "biascorr"` lines 160-161): it now always computes
  `omega_flow = gyro_avg.average(t, omega) - x[U.BG_SLICE] / DT_STEP`. That is the same formula the `biascorr`
  diagnostic used: the flow-frame gyro average minus the UKF's own gyro-bias estimate, converted from delta form to a
  rate, at the state mean. The `len(d) == 4` substitution (EKF3's bodyRate, x/y) is applied after it. That is
  deliberate: EKF3's bodyRate is already bias-corrected and must not be corrected twice.
- **`room_ukf_replay.py`, flow branch** (formerly lines 151-152): the same change on `om`.
- **Not touched:**
  - `gp.on_gyro`, the take-off detector, which already used `|gyro - bias|`;
  - `fwd_avg` and `update_yawrate`, the forward camera;
  - `ukf_core`, the FGO, and the EKF3 tooling.
- **`apin.py`:**
  - The docstring now says `biascorr` is a no-op alias of the default, and how the other modes now behave.
  - `substitute()` returns early for `biascorr`. Before this, `biascorr` loaded `apin/ap_inputs.npz` even though it
    swaps nothing, so it crashed on any trial without an extraction (found on `H_s1far_r1`).
  - `MODES` is unchanged, so the `_apin_biascorr` directory suffix still resolves.
- **`measurement_models.py`, `h_flow_pose` docstring** (formerly lines 64-67): "the UKF passes the RAW measured rate" is
  replaced. It now says both estimators pass a bias-corrected rate, and that the UKF passed the raw rate before
  2026-10-09.

**APIN modes after the change.**
- In `flow`, `both` and `flowgyro`, the x/y derotation rate is EKF3's own bodyRate. z is the UKF's corrected average,
  and h_flow does not use z: the lever arm is along z and `h_flow_rot` uses x/y only. These modes therefore reproduce
  their earlier outputs. This was verified bit-identical for `flow` on dsn_tex_r2 (§2); `both` and `flowgyro` follow
  by the same argument and were not run.
- `imu` and `flowtime` derotate with the UKF's own corrected average, so they now differ from their stored outputs.

## 2. Verification

All in scratch (`$S = …/scratchpad/derot`: `run_one.sh`, `driver.sh`, `driver2.sh`, `compare.py`, `compare.json`).
- **"old"** = a copy of `src/estimators/*.py` at a966d7d.
- **"oldbc"** = old plus only the `biascorr` early return, needed because old `biascorr` crashes on `H_s1far_r1`.
- **"new"** = this branch.
- **dsn_tex_r2** ran under a scratch `HOME` holding real copies only: the bag decompressed from `.zst` (sha256 matches
  `PACKED.txt`), `imu_gaps.json`, `apin/ap_inputs.npz` and `OpticalFlow.msg`. No symlinks.
- **The H bags** ran with the real `HOME`, `UKF_OUT_ROOT` = scratch and `ROOM_TAG_SIGMA_POS=0.02`.
- `OPENBLAS_NUM_THREADS=1` in every run.

### (a) New default = old `UKF_APIN=biascorr`: PASS, bit-identical at full precision
| bag | compared | result |
|---|---|---|
| dsn_tex_r2 | `ukf_traj.tum`, `metrics.txt` (bytes); `UKF_DUMP` npz (full state + diag P per predict; flow pred/meas/omega) | identical; `np.array_equal` True for `x` and `flow` |
| H_s1far_r1 | `ukf_live.tum`, `ukf_rts.tum` (bytes), `rts_cov.npz` (all arrays), `stats.json` | identical (reference = oldbc) |
| H_s1_r1 | same | identical (reference = old) |
| H_s1far_r1 | new `UKF_APIN=biascorr` (alias) vs new default | identical (and it now runs without `ap_inputs.npz`) |
| dsn_tex_r2 | new `UKF_APIN=flow` vs old `UKF_APIN=flow` | trajectory and state dump identical; only flow-dump column 7 (omega_z, unused by h_flow) differs |

**Stored diagnostic outputs do NOT match fresh old-code runs.** The cause is most likely the later jitter correction
(47de1ca), which postdates the stored files; this is attributed, not proven.
- `~/thesis_data/trials/H_s1_r1/room_ukf_apin_biascorr` (Oct 8 21:50) vs fresh old biascorr: max position diff
  0.010 m live / 0.010 m RTS, final horizontal 0.5 mm.
- `dsn_tex_r2/ukf_apin_biascorr` (Oct 8 21:50) vs fresh old biascorr: max 2.01 m, final 1.85 m.
- Likewise, the stored `dsn_tex_r2/ukf` vs the fresh old default: max 2.53 m. The stored `H_s1far_r1/room_ukf` vs the
  fresh old default: max 0.010 m.
- **So the stored dsn UKF outputs are not reproduced by pre-change HEAD either. The re-run in item 3(a) supersedes
  them anyway.**

### (b) Old default vs new default: non-zero (sanity PASS)
- **dsn_tex_r2:** max position diff 2.32 m, final horizontal 2.88 m. Metrics:
  - along_pN 3.883 → 6.100;
  - yaw drift −2.373 → −2.292 deg/min;
  - gyro-z bias −6.62 → −6.70 deg/min (74.3 → 75.2 % of true);
  - the yaw pseudo-measurement fired 63/2253 in both.
- **H_s1far_r1:** live max 0.199 m, RTS max 0.0056 m, final horizontal 7.8 mm.

**evo -a (cruise), dsn_tex_r2: FIRST INDICATION ONLY (n = 1 bag, not a result).**
- Cruise window [30.556, 333.044] s, computed with `three_way_eval`'s `cruise_window`, `crop` and `evo_ape_a`.

| run | evo -a (cruise) | final displacement ratio |
|---|---|---|
| old default (fresh, a966d7d) | **2.025 m** | 0.966 |
| **new default** | **1.614 m** | 0.977 |
| stored `ukf/` (older code) | 2.135 m | 0.965 |

### (c) Unit/regression tests
- **No UKF unit or regression tests exist.** There is no `tests/` directory. The only `test_*.py` files are the
  ament lint tests of `optical_flow_node`, and `eval/dsn_paired_test.py` is a statistics script.
- The port-equivalence harness (`eval/ukf_event_export.py` → `UKF_Equiv`) was not run, because it needs the port build.
  Its compatibility was checked read-only (§3).

## 3. Open / for the next stage
- **Item 3(a)/(b) is not done:**
  - re-run every offline UKF result: `dsn_*`, `fwdc_*`, `fwdplainc_*`, Phase 4/5/5b, the scale and heading-share
    checks, C0, F1–F3c, 2(a), T, O and the H shadows;
  - report old vs new;
  - restate numbers.md and the figures.

  The stored UKF outputs are now stale twice over: once for the jitter fix (§2a) and once for this change.
- **Event-tape exporters** (`eval/ukf_event_export.py`, `eval/ukf_tag_event_export.py`): they wrap the replays, so the
  flow `om` on the tape is now the bias-corrected rate.
  - `UKF_Equiv` (`~/ardupilot_ukf/.../UKF_Equiv.cpp:82-85`) uses the tape's om verbatim as `_flow_gyro`. The port's
    flow model (`AP_NavUKF.cpp:208-211`) does not subtract its drift from `_flow_gyro`; in flight that input is
    already AHRS-corrected.
  - So the equivalence stays like-for-like, with no double correction (read-only check, not run).
- **Not changed, and deliberately left as historical diagnostics:** `plots/ukf_state_diagnostic.py` and
  `plots/diag_derotation_ekf3_vs_ukf.py` (August, cfad39f). They contain their own replay loops calling
  `U.update_flow` with the raw rate, they import from the main checkout, and they already predate several model
  changes.
- **Process note (my scratch driver, not `heavy.py`).** The old `biascorr` crash on `H_s1far_r1` was logged as
  "exit 0" because the `$(date)` in my echo reset `$?`. `heavy.py` does propagate the step's return code. The crash
  was caught from the step log and re-run as "oldbc".
- **Not done:** the low-priority items in the ruling (the 2.6 mrad/s → 0.29 m question, the SITL gyro bias source).
