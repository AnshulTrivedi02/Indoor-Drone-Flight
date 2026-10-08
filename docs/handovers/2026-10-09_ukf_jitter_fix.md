# UKF covariance-jitter correction, both builds (2026-10-09)

Stage agent, worktree branch from `fwd-camera` a03bfb7. Ruling: METHODOLOGY "MODEL AUDIT RESULT … and RULINGS (user,
2026-10-09)" item 1 (a D18 model correction). The evidence is `docs/handovers/2026-10-09_model_audit.md` §3a.

No simulator was run. No trial directory was written. Every build, replay and harness run went through `heavy.py`.
`~/ardupilot_ukf`'s checked-out branch (`ukf-port-tag`) and its `build/` are unchanged: the md5s and mtimes of the
binary, UKF_Equiv, Replay, `c4che` and the waf lock file match before and after
(`eval/diag/ukf_jitter_fix/results/{before,after}_stat.txt`).

## 1. The change (identical rule in both builds)

**Rule chosen: jitter only on factorisation failure.**
- The first Cholesky attempt has **no** jitter.
- On failure it retries with the ladder 1e-12, 1e-9, 1e-6 (·I, inside c·(P + jit·I)). Each retry is counted, and the
  first one is reported.
- Why this option rather than a covariance-scaled jitter:
  - It is the only option that adds **exactly nothing** in normal propagation, which is what the ruling asks for.
  - A relative jitter (e.g. 1e-12·diag P) still adds a little every step.
  - A relative jitter also cannot repair a genuinely indefinite P, because it does not touch the correlations.
  - The port already had the retry ladder and counters, so the change there is one rung.

**Offline: `src/estimators/ukf_core.py` `_sigma_points`.**
- `CHOL_JITTER_LADDER = (0.0, 1e-12, 1e-9, 1e-6)`.
- Counter `CHOL_STATS = {calls, retry, eig_fallback}`. The first retry prints a warning to stderr.
- If every rung fails, the pre-existing eigen-clip fallback is kept. It is now applied to c·P without the 1e-12.

**Port: `~/ardupilot_ukf` branch `ukf-jitter-fix`, `libraries/AP_NavUKF/AP_NavUKF.cpp` `NavUKF::sigma_points`.**
- 4 attempts: 0, 1e-12, 1e-9, 1e-6. Previously 3: 1e-12, 1e-9, 1e-6.
- `_n_chol_retry` is counted as before. The first retry also sends `GCS_SEND_TEXT` WARNING "UKF: Cholesky needed
  jitter (first fallback)", which lands in the dataflash MSG log.
- If every rung fails, the pre-existing behaviour is kept: `_n_chol_fail++`, and the step is skipped.

**Pre-existing difference, unchanged:** the terminal fallback differs between the builds (Python eigen-clip; the port
skips the step). Neither fired anywhere below.

**Harness only:** `examples/UKF_Equiv/UKF_Equiv.cpp` gets the DIAGNOSTIC option `UKF_EQ_PDIAG=<file>`, which dumps
diag(P) after every event.
- It is off unless set, and the state file is unchanged.
- It is used for the C++ free-inertial check (§2.2).

Nothing else was changed in either build.

## 2. Verification: free-inertial growth (the audit's harness, case A; variance ratio to `analytic_tv`, band 0.94–1.09)

### 2.1 Python core (`eval/diag/model_audit/free_inertial.py` with the fixed `ukf_core`)
Outputs are in `results/fi60.json`, `results/fi10.json` and `results/tables.md`.
- The `ukf_offline` and `ukf_port` columns now equal the audit's `*_nojitter` diagnostic columns (same values to 4
  significant figures).

| quantity | before (offline / port cadence) | **after, 10 s** (offline / port) | **after, 60 s** (offline / port) |
|---|---|---|---|
| tilt | ×4.07 / ×6.30 | ×1.00 / ×1.00 | ×1.01 / ×1.01 |
| yaw | ×4.07 / ×6.30 | ×1.00 / ×1.00 | ×1.01 / ×1.01 |
| horiz. vel | ×2.23 / ×3.11 | ×1.00 / ×1.00 | ×1.00 / ×1.00 |
| vert. vel | ×1.01 / ×1.01 | ×1.00 / ×1.00 | ×1.00 / ×1.00 |
| horiz. pos | ×1.56 / ×1.96 | ×1.00 / ×0.99 | ×1.00 / ×1.00 |
| vert. pos | ×1.00 / ×1.00 | ×1.00 / ×1.00 | ×1.00 / ×1.00 |
| **gyro-bias RW** | **×24.71 / ×41.96** | **×1.00 / ×1.00** | **×1.00 / ×1.00** |
| accel-bias RW | ×1.04 / ×1.06 | ×1.00 / ×1.00 | ×1.00 / ×1.00 |

- **Case B** (configured initial bias σ): ×0.96–×1.08 on every quantity. The largest is vertical velocity at 10 s
  (×1.08; EKF3 ×1.03), as before.
- **Case C** (yaw-bounding on): the UKF now matches case A, and its pseudo-yaw fired **0** times in 60 s (offline and
  port cadence). It was 59 / 115, driven by the jitter-inflated tilt variance.
- The remaining flags in `tables.md` are the audit's other, out-of-scope items:
  - EKF3's 1e4 m² position hold;
  - the FGO's ungated yaw cap (ruling 2), at 60 s.
- **Cholesky fallback:** 17,596 `_sigma_points` calls, **0 retries**, 0 eigen fallbacks.

### 2.2 The C++ port itself (new: the audit's "port" column was the Python core at 12.5 ms)
- **Method:** `eval/diag/ukf_jitter_fix/cpp_free_inertial.py` exports the same 12.5 ms bins, initial state and P0
  (converted to NED/FRD as `ukf_event_export.py` does). The fixed `UKF_Equiv` runs on them with `UKF_EQ_PDIAG`.
  Results are in `results/cfi*.score.{json,txt}`.
- **Case A against `analytic_tv`:**
  - 10 s: ×0.995–×1.000 on every quantity;
  - 60 s: tilt ×1.006, yaw ×1.013, velocity and position ×0.997–×0.999, gyro-bias ×1.000, accel-bias ×1.000.
- **Case B (10 s):** ×0.960–×1.075.
- **Case C:** identical to A.
- **C++ against the Python core at 12.5 ms:** every ratio is ×1.000000 (6 d.p.) at every checkpoint, in all three
  cases.
- **Cholesky:** 0 retries and 0 failures (4,799, 5,198 and 800 events).

**Verdict: both builds are within the 0.94–1.09 band at 10 s and 60 s on every process-noise quantity.**

## 3. Port-vs-offline equivalence (fixed port `UKF_Equiv` md5 `8f915bf0…` against the fixed Python core)

### 3.1 Step 2, `dsn_tex_r2`, E1–E5
- **Run:** re-exported with the fixed core under a fake HOME of real copies (no symlinks; the packed bag was unpacked
  into scratch and deleted afterwards).
- **As worded: FAIL.**
  - E1: max 4.18 m, rms 1.93 m.
  - E3: 3.1°.
  - E4: gyro-z 0.58 deg/min, accel 0.0014 m/s².
  - E5: fails.
- **First divergence > 1e-6 m:** event 53, a plain predict at t = 10.80 s.
- **Cause: the D27 noise form, not this change.** This is the same mechanism as tier A's known failure:
  - since D27 the offline Q is EKF3's form scaled by DT_REF/dt and fixed at the 15 ms replay step;
  - the port uses (dt·NSE)² at the step's actual dt, i.e. 1.2× at the harness's 15 ms steps;
  - step 2 predates D27 and had not been re-run against Python since. The 2026-10-08 UR1 check compared only old
    against new binary.
- **DIAGNOSTIC (labelled, post hoc), `UKF_EQ_QDIAG` = the offline per-step Q diagonal: PASS on every band.**
  - E1: max 1.04e-5 m, rms 5.4e-6 m.
  - E3: 7.3e-6°.
  - E4: 1.6e-6 deg/min and 2.5e-9 m/s².
  - E5: all gate decisions identical (flow 9,045/9,166 per axis, range 9,166, pseudo-yaw 42/2,016).
  - Results: `results/equiv_dsn_tex_r2{,_d27}.json`.
- **Cholesky:** Python 52,950 calls with 0 fallbacks; the port 0 retries and 0 failures.

### 3.2 Tier A, `H_s1_r1`, UA1–UA5 (`eval/ukf_tag_event_export.py` + `eval/ukf_tag_equivalence.py`)
- **Reference:** the export's wrapped `room_ukf` run is the fresh fixed-core offline reference.
  - Its `ukf_live.tum` is, as expected, **not** byte-identical to the stored (old-model) `H_s1_r1/room_ukf/`.
  - The stored directory was untouched (mtime check).
- **As worded: FAIL** (it was FAIL as worded before the fix too, for the known D27 noise form).

| band | before the fix (doc §3.1) | after |
|---|---|---|
| UA1 max ≤ 1 mm | 3.6 mm | **FAIL** 3.8 mm |
| UA2 max ≤ 0.01° | 0.0039° | **FAIL** 0.032° |
| UA3 accel ≤ 0.001 m/s² | 0.0036 | **FAIL** 0.0039 (gyro-z 0.047 deg/min, passes) |
| UA4 gates | PASS | PASS (flow 11,481/11,548, range 11,547, pseudo-yaw 26/204) |
| UA5 anchor state ≤ 1e-9 | 2.7 mm | **FAIL** 2.5 mm (other UA5 items pass) |

- **New:** UA2 now fails as worded. A plausible reading is that without the jitter the yaw variance is smaller, so the
  1.2× Q difference shows more in yaw. This is not separately tested.
- **DIAGNOSTIC `UKF_EQ_QDIAG`:**
  - UA1 3.2e-8 m, UA2 3.2e-7°, UA3 6.3e-7 deg/min and 6.6e-9 m/s², UA4 identical: all PASS by 4–5 orders of magnitude.
  - **UA5 fails as worded by round-off:** the post-anchor state differs by **2.16e-9** against the 1e-9 band.
  - The element is vertical velocity, carried unchanged from the event before the anchor. It is accumulated
    double-precision round-off over 4,100 events, and there is no difference above 1e-6 anywhere.
  - The pre-fix diagnostic gave 2.5e-10 (max element 2.5e-10).
  - Every other UA5 item passes: the anchor is the first tag event; the port state equals the fix; 8,670/8,670 fused
    on both sides; 0 pseudo-yaw after the anchor.
- Results: `results/tierA_H_s1_r1{,_diagD27q}.json`.
- **Cholesky:** 0 retries and 0 failures.

### 3.3 Tier B (Replay of `H_s1_r1/ardupilot.bin`): NOT re-run
- It needs a Replay run with the new binary plus a fixed-core offline `room_ukf` reference, which tier A's export now
  provides in scratch.
- The new Replay binary is built (md5 `874f775a…`); the run was left for time.
- UB1–UB4 concern the input path and do not involve `sigma_points`, so they are expected unchanged. UB5 compares
  against the offline track and would need the new reference.

### 3.4 RTS-UKF
- `rts_smooth` has its own diagonal scaling and does not rely on the jitter.
- Smoke run: `room_ukf_replay.py H_s1_r1` with RTS on, fixed core, fake HOME. See §6.

## 4. How often the fallback fires on real data

**Zero, everywhere it was measured:**

| run | result |
|---|---|
| Python, dsn_tex_r2 step-2 replay | 52,950 Cholesky calls, 0 fallbacks |
| Python, H_s1_r1 tag replay | 0 fallbacks |
| Port UKF_Equiv on dsn_tex_r2 | 45,277 events, 0 retries |
| Port UKF_Equiv on H_s1_r1 | 57,371 events, 0 retries |
| free inertial (both builds) | 0 |

No closed-loop or Replay log was examined. Search the dataflash MSG for "Cholesky needed jitter" after the re-flights.

**Indicative only, one bag, not a thesis result:** the fixed offline `dsn_tex_r2` replay printed:
- pseudo-yaw fired 63/2,253 (was 96);
- yaw drift −2.37 deg/min (was −2.70);
- along-track 146.0 m (unchanged).

## 5. Port branch and the rebuild recipe for the main session
- **Branch:** `ukf-jitter-fix` in `~/ardupilot_ukf`, from `ukf-port-tag` 00b597dd7f, commit **abb0357d0f**. Not merged,
  and not checked out in `~/ardupilot_ukf`.
- **Built and tested in a scratch worktree only.** The new binaries' md5s: the vehicle binary `e0509409…`, Replay
  `874f775a…`, UKF_Equiv `8f915bf0…`.

**Rebuild `~/ardupilot_ukf/build/` for the UKF re-flights, only when no flight is running:**
```
git -C ~/ardupilot_ukf status --short          # must be clean
git -C ~/ardupilot_ukf checkout ukf-jitter-fix
cat > /tmp/rebuild_ukf.sh <<'EOF'
#!/bin/sh
set -e
cd ~/ardupilot_ukf
./waf copter
./waf replay
./waf build --target examples/UKF_Equiv
B=ardu; B=${B}copter; md5sum build/sitl/bin/$B build/sitl/tool/Replay build/sitl/examples/UKF_Equiv
EOF
python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "rebuild ukf-jitter-fix" -- sh /tmp/rebuild_ukf.sh
```
- **Expected md5s:** they should equal those above if the toolchain and configure are the same. The scratch build was
  `./waf configure --board sitl --no-submodule-update`.
- If they differ, `ukf-port-tag` was configured differently; the source diff is still the one commit.
- **Do not reconfigure unless needed.**
- **To return to the old model:** `git checkout ukf-port-tag`, then the same rebuild.

**The offline fix is on this thesis_ws branch.** Every offline UKF replay after merging uses the corrected model.
Per the ruling, the old runs stay as recorded and labelled.

## 6. RTS smoke run
`room_ukf_replay.py H_s1_r1`, RTS on, fixed core, fake HOME (`eval/diag/ukf_jitter_fix/rts.sh`). It completes:
- 23,362 RTS nodes, with finite live and RTS tracks;
- 8,670 tags fused, and 26 pseudo-yaw fusions before the anchor (unchanged);
- 85,944 Cholesky calls, 0 retries, 0 eigen fallbacks.

The raw (unaligned) horizontal-difference figure, 5.0 m live / 5.0 m RTS for t > 60 s, equals the stored old-model
tracks to 1 mm. It is dominated by the frame offset; it is a smoke check only, not an accuracy result.

## 7. Commits, slips and loose ends
- **Commits:** see the final report (thesis_ws worktree branch; port `ukf-jitter-fix`).
- **SLIP (recorded, reverted):**
  - While initialising submodules in the scratch port worktree, `git config submodule.<x>.url <local path>` was run
    inside the worktree. That writes to the **shared** `~/ardupilot_ukf/.git/config`.
  - 11 submodule URLs pointed at `~/ardupilot_ukf/modules/*` for a few minutes.
  - **They were restored** to the `.gitmodules` URLs, which equal each submodule's own `origin` remote. Nothing was
    fetched or updated in `~/ardupilot_ukf`.
  - The scratch worktree then used rsync copies of the module working trees (no git metadata) and
    `--no-submodule-update`.
  - If the main session had custom URLs there before, they were not recorded. The `origin` remotes match
    `.gitmodules`, so this is unlikely.
- **No symlinks were left:**
  - the fake HOME holds real file copies only;
  - the tier-A export's `bag` / `imu_gaps.json` symlinks in scratch were removed;
  - the step-2 `_d27_replay_out` symlink was removed.
- **The scratch port worktree** was removed (`git worktree remove`), with its build; the branch `ukf-jitter-fix` (abb0357d0f) remains. Rebuild per §5.
