# FGO yaw cap variance-gated like EKF3's and the UKF's (ruling 2026-10-09 item 2): verification and C++-vs-Python equivalence

Stage agent (continuation), worktree branch `worktree-agent-aa29cfc08768a86c5`. It started from `fwd-camera` `c41358a`
and merged the stopped agent's branch `worktree-agent-add36c43f1fbc72e3` (code commit `8dfb035`).

**Ruling:** METHODOLOGY "MODEL AUDIT RESULT … and RULINGS (user, 2026-10-09)", item 2.

**What this stage did not do:**
- It ran no simulator.
- It touched no harness file.
- It wrote nothing into a trial directory.
- It installed nothing to `~/opt/fgo_cpp`. The installed node is still `1123742d…` (binit0, cap ungated).

## Verdict in one line
**The gate is correct against EKF3/UKF, and free-inertial yaw variance is now ×0.98–1.00 of EKF3's and the UKF's at
10 s and 60 s** (it was ×0.37 at 60 s).

The gate fires on real corridor data, about 3–4 % of checks, and its trace sits at the 0.04 threshold. Because of that:
- **Band A dsn_tex now FAILS as worded** (1.14 mm, against 1 mm). This is a NEW failure.
- Band A blank and trans FAIL as before.

**Cause of all three FAILs:** a threshold tie. Python and C++ make the same decisions until one check, close to 0.04,
falls on opposite sides. The states are bit-identical up to that check in the emulate-gemv build.

**Every other band PASSES:**
- B1–B5, and the optional B6 (PASS / PASS);
- C (all four bags);
- L1 and L2 (the adapter is bit-identical to the C++ replay).

**Live step time with the gate:**
- **L1:** median 0.52 ms, p95 0.78 ms.
- **L2:** median 0.93 ms, p95 1.08 ms.

That is far inside 33 ms, and unchanged from binit0.

**RULING NEEDED before this build is installed or S3 is re-flown.**
- Band A dsn_tex FAILS as worded (1.14 mm against 1 mm). Under binit0 it was a pre-registered PASS, so METHODOLOGY's
  "S3 gate met" no longer holds as worded for this build.
- **Evidence (post hoc; not a decision):** with the gate decisions forced equal, Python and the emulate-gemv build are
  bit-identical on tex, blank and trans, and the default build is 0.15 mm on tex.
- The install recipe in §6 is ready, but it is NOT cleared by this stage.

## 1. The change (`8dfb035`, both cores) and the gate definition
Files: `src/estimators/fgo/fgo_core.py` and `src/estimators/fgo_cpp/src/fgo_core.cpp` (+ `fgo_core.h`). The rest of the
commit is plumbing:
- the gate log exported as `.yawgate.f64`, with columns (t, k, trace, fired);
- probe variants;
- the audit harness driving the core.

**The gate:**
- **Check opportunity:** the first keyframe with `t − t_yawchk ≥ YAW_DT = 0.14 s`. `t_yawchk` starts at `init` and is
  reset at every check, fired or not, as in `ukf_replay.py:142-146`.
  - With 1/30 s keyframes this is every 5th keyframe (167 ms).
  - The UKF checks every 10 × 15 ms (150 ms) and EKF3 every 12 × 12.5 ms (150 ms).
  - This difference is structural: the check can only fall on a keyframe.
- **Gate quantity:** the trace of THIS keyframe's PREDICTED rotation-tangent covariance.
  - It comes from the gate-only filtering recursion: `cov_gate` (the previous keyframe's filtering covariance) plus
    this keyframe's CombinedImuFactor, linearised at the IMU prediction.
  - It is taken before that keyframe's range, flow, forward, tag or GNSS factors.
  - The trace is frame-invariant.
- **Fire if the trace exceeds `ATT_VAR_GATE = 0.04` rad².** EKF3's quaternion-trace gate is 0.01
  (`MagFusion.cpp:274`), mapped to the attitude tangent ×4, as `ukf_core.ATT_VAR_GATE`.
- **When it fires:** the unchanged σ 0.5 rad zero-innovation yaw prior on X(k), anchored to the IMU-predicted yaw.
- **Recursion update:** at every keyframe while the cap is active, `cov_gate` ← the posterior filtering covariance
  with ALL of this keyframe's factors. That includes the cap when it fired, as EKF3's covariance after fusion does.
  - Under `log_cov` it is the same recursion as `cov_prev`, and the forward-camera gate is unchanged.
  - **After a tag re-anchor:** the cap stays off, as before (`no_yawcap`).
  - **After a GNSS re-anchor:** it continues (`keep_yawcap`), and `cov_gate` is re-initialised.

**Review against EKF3 and the UKF (this stage):**
- The threshold direction matches the UKF (fire if the trace is greater than the gate).
- The 0.01 → 0.04 mapping matches.
- Init and reset of the check timer match.
- "Predicted" means the same thing in each:
  - In the UKF, the check runs immediately after `predict` and before the next asynchronous flow or range update.
    The UKF's P there carries all earlier updates plus this prediction.
  - In the FGO, `cov_gate` (the previous keyframe's posterior) plus this IMU factor is the same quantity.
- onGround / AID_NONE are ignored, as in the UKF.
- **No error found.**
- **Numerical caveat:** see §4.4. The information-form recursion loses relative precision over a long flight.

## 2. Verification with the audit harness (`eval/diag/model_audit/free_inertial.py`)
- **Inputs:** the audit's window `win60_tex_r1.npz` and `ekf3_cov_harness`, each sha256-identical to the audit's.
- **Run on this merged tree,** so the UKF rows are the jitter-corrected core.
- **One harness fix,** carried over from the stopped agent's uncommitted diff: the checkpoint keyframe index is capped at
  the last keyframe. Before the fix, the 60 s checkpoint of `fgo_chain` and `fgo_ungated` repeated the 30 s value.
- **Ratios are of VARIANCES** (FGO / reference), from `fi10.json` and `fi60.json` (`ratios.py`). Audit band 0.94–1.09.

| case | t | FGO / EKF3 | FGO / UKF offline | FGO / UKF port | FGO / analytic | old ungated / EKF3 |
|---|---|---|---|---|---|---|
| **C** (common small P, yaw bounding ON; the audit's flag) | 10 s | **0.999** | **0.998** | **0.999** | 0.999 | 0.987 |
| **C** | 60 s | **0.998** | **0.984** | **0.985** | 0.996 | **0.372** |
| A (bounding off) | 10 s / 60 s | 0.999 / 0.998 | 1.000 / 0.984 | 0.999 / 0.985 | 0.999 / 0.996 | – |
| B (configured bias σ) | 10 s | 1.000 | 1.002 | 1.000 | 1.000 | – |
| D (positive control: B with bounding ON) | 10 s | n/a (see below) | **1.075** | **1.073** | – | – |

**Tilt variance in case C** is 0.999 (10 s) and 0.99 (60 s) against every reference.

**In case C, all three gates stay shut over 60 s:**
- EKF3's quaternion trace peaks at 8.0e-4 against 0.01;
- the UKF fires 0 times;
- the FGO's trace peaks at 3.2e-3 against 0.04 (0 of 359 checks).

**`fgo` (core `cov_gate`) against `fgo_chain` (full-chain `gtsam.Marginals`, the smoother's marginal):** yaw
×1.000–1.0004 at every checkpoint. Tilt is ×1.029 at 60 s: the recursion's linearisation against the full chain's.

**Case D (positive control: the gates must open):**
- The FGO fires 45 of 60 checks (first at 2.67 s); the UKF port fires 49 (first at 2.70 s).
- FGO / UKF yaw variance: ×1.04 at 5 s and ×1.07 at 10 s.
- The FGO's checks are 167 ms apart against the UKF's 150 ms, so it fires slightly less often.
- **EKF3 is not a valid denominator in D.** The harness does not simulate `fuseEulerYaw`, so its D yaw is unbounded
  (FGO / EKF3 0.06 at 10 s). It only reports the gate opening at 2.65 s.

**The audit's "×0.82 at 10 s"** was the 10 s checkpoint of a 60 s full chain. That is a SMOOTHED marginal, which uses
the caps after 10 s. The filtering value at 10 s (the 10 s run, or the fixed checkpointing) is ×0.987. The 60 s figure
×0.372 reproduces the audit's ×0.37 exactly.

## 3. Build (scratch; NOT installed)
- Built from this worktree's `src/estimators/fgo_cpp` with a clean `env -i` PATH, the same cmake line as
  `build_fgo_main.sh`, and no `make install`.
- Through `heavy.py`, into `…/scratchpad/yawgate2/build`. No warnings.

| binary | md5 (path-dependent; use the functional check, §6) |
|---|---|
| fgo_cpp_node | `a36261f5b1460d648f02dc5f780e9983` |
| fgo_cpp_live_replay | `0c0e7f87108904c98eb50b6d356e50f7` |
| fgo_cpp_replay | `816a26033110c091a27de0e260c5811e` |
| fgo_cpp_frontend | `96daf49847365e454db8aadb8545f967` |
| fgo_cpp_probe | `e9e59417f594cd45bb5650c7bffb2f1f` |

**Probe, Python vs C++:** every line is bit-identical except three. In each case the gate trace is computed through
`np.linalg.inv` against Eigen's `inverse()`, plus the known gemv rounding:
- `gate3`: rel 3.3e-12;
- `gate4`: rel 2.2e-11;
- `kf4` (gate open, cap added): 2.2e-15.

**Probe, new Python vs binit0's:** `kf1` and `kf2` differ, as expected, because the cap is no longer added within 140 ms
of init. Every other common line is identical.

## 4. Bands (pre-registered: same count, |Δp| ≤ 1 mm, |Δyaw| ≤ 0.01°; default Eigen build)
The steps, scripts and thresholds are binit0's. Everything ran single-threaded at nice 19 through `heavy.py`:
- bags from scratch copies;
- outputs to scratch;
- band-L tapes as in binit0.

**All Python references and exports were produced in this stage from this tree** (§7 explains why the stopped agent's
outputs are not reused). Logs: `eval/results/fgo_cpp_equiv_yawgate/logs/`.

### Band A (Python vs C++ export-driven replay)
| bag | keyframes | factor decisions | gate checks / fired (Py / C++) | gate mismatches | max / p99 \|Δp\| | max / p99 \|Δyaw\| | band |
|---|---|---|---|---|---|---|---|
| dsn_tex_r1 | 10197 / 10197 | 0 | 2039 / 63 / 63 | **4** (first at 327.95 s) | 1.14 / 0.115 mm | 1.6e-3 / 1.2e-4 ° | **FAIL (as worded)** |
| dsn_blank_r1 | 10048 / 10048 | 0 | 2009 / 75 / 70 | 61 (first at 91.15 s) | 1.1e7 / 9.8e6 mm | 108 / 8.7 ° | **FAIL (as worded)** |
| dsn_trans_r1 | 10031 / 10031 | 0 | 2006 / 86 / 64 | 36 (first at 254.50 s) | 1.9e6 / 1.8e6 mm | 11.1 / 2.7 ° | **FAIL (as worded)** |

### Band B (C++ vs Python)
| row | run | keyframes | decisions | gate (checks / fired; mismatches) | max / p99 \|Δp\| | max \|Δyaw\| | band |
|---|---|---|---|---|---|---|---|
| B1 | fwdc_tex_r1 heading | 10118 / 10118 | 0 (heading accepted 9184 / 9539; min \|NIS − 9\| 0.028) | 2023 / 0; 0 | 1.2e-4 / 1.1e-4 mm | 2.3e-10 ° | **PASS** |
| B2 | T_A_r1 live (anchored rows) | 8015 / 8015 | 0 | 48 / 8; 0 | 1.4e-7 / 9.8e-8 mm | 4.5e-9 ° | **PASS** |
| B3 | T_D_r1 live (anchored rows) | 8017 / 8017 | 0 | 52 / 9; 0 | 5.7e-5 / 3.9e-5 mm | 9.5e-7 ° | **PASS** |
| B4 | T_A_r1 batch | 7775 / 7775, ids identical | n/a | – | 3.8e-9 mm | 8.5e-12 ° | **PASS** |
| B5 | T_D_r1 batch | 7756 / 7756, ids identical | n/a | – | 3.5e-8 mm | 4.8e-11 ° | **PASS** |
| B6 (optional) | O_r1 GNSS live (all and anchored rows) / batch | 7288 / 7288; batch 6896 / 6896, ids identical | 0 (533 GNSS factors) | 1457 / 15; 0 | 6.9e-4 / 4.1e-4 mm; batch 8.1e-8 mm | 1.3e-5 °; batch 2.9e-10 ° | **PASS / PASS** |

- **Batch LM, Python = C++:** T_A error 135.730890 (4 iterations), against 135.736713 under binit0; T_D 58.596354 (5),
  against 58.605479; O_r1 29.376517 (10), against 29.469094.
- **The cap on T_A/T_D** fires only before the tag re-anchor (t_anchor 28.5 / 29.2 s): 8 and 9 times.
- **On O_r1** it continues after the GNSS re-anchor (31.8 s), firing 15 of 1457 times. The closest call is 1.1e-5 from
  0.04, and there was no flip.

### Band C (native front end vs export-driven C++)
| bag | keyframes | decisions | gate mismatches | max / p99 \|Δp\| | max \|Δyaw\| | band |
|---|---|---|---|---|---|---|
| dsn_tex_r1 baseline | 10197 / 10197 | 0 | 0 (63 / 63) | 0.28 / 9.3e-3 mm | 7.9e-5 ° | **PASS** |
| fwdc_tex_r1 heading | 10118 / 10118 | 0 | 0 (0 / 0) | 1.4e-4 / 1.3e-4 mm | 1.5e-10 ° | **PASS** |
| T_A_r1 live (+ batch) | 8015 / 8015 | 0 | 0 (8 / 8) | 1.4e-7 mm (batch 1.9e-9) | 9.3e-10 ° | **PASS** (batch PASS) |
| T_D_r1 live (+ batch) | 8017 / 8017 | 0 | 0 (9 / 9) | 1.9e-4 mm (batch 4.2e-8) | 2.6e-6 ° | **PASS** (batch PASS) |

- The stream diagnostics are as in binit0: kinds, non-IMU stamps, payloads, flow ω and forward gyro-z are
  bit-identical, and the IMU stamps differ by ≤ 2.3e-13 s.
- "key ids identical: False" on T_A/T_D refers to the stamps only, as in binit0.
- **Band C dsn_tex passes, but its margin shrank:** 0.28 mm, against 1.7e-2 under binit0. The gate trace differs by
  up to rel 2.2e-4 between the two C++ runs, with no flip.

### Band L (live adapter vs export-driven C++; dejittered tape, `--imu-stamp header --arm-source param --delay 0.20`)
| row | keyframes | decisions | adapter states | ODOMETRY frames (CRC errors) | time_usec = `_sitl_us` | band |
|---|---|---|---|---|---|---|
| L1 dsn_tex_r1 | 10197 / 10197 | 0 | **bit-identical** (`L1.kf.f64` == `cpp_….kf.f64`) | 9919 (0); byte-identical to pymavlink | 9919 / 9919 | **PASS** |
| L2 fwdc_tex_r1 heading | 10118 / 10118 | 0 | **bit-identical** | 9840 (0); byte-identical | 9840 / 9840 | **PASS** |

### 4.4 Why band A fails: a threshold tie, amplified (post-hoc diagnostics, NOT bands)
**The trace sits on the threshold.** On real corridor data the gated cap behaves like EKF3's synthetic yaw:
- the yaw variance grows to 0.04, the cap fires, the variance drops, and so on;
- **17–20 % of all checks have a trace within ±2.5 % of 0.04**;
- the closest is 2.1e-6 from it.

**The gate recursion is not bit-reproducible across languages, and its relative error grows over the flight.**
- In the emulate-gemv build the STATES are bit-identical to Python's until the first gate mismatch (max |Δp| before it
  = 0 on all three bags).
- The gate trace nevertheless drifts apart:

| bag | rel. trace diff at 9 s | at ~75 s | at ~210 s | at the first flip |
|---|---|---|---|---|
| tex | 5e-11 | 5e-6 | 2.5e-4 | 3.6e-4 (327.95 s) |
| blank | 2e-10 | 7.5e-4 (80 s) | – | 4.5e-3 (86.98 s) |
| trans | 2e-11 | 3e-7 (81 s) | 2e-4 | 1.1e-3 (254.5 s) |

**Hypothesis (consistent with the data; NOT measured): the information-form recursion.** I did not compute the
condition number, and I did not compare `cov_gate` with the smoother's marginal over a long flight; `fgo` vs `fgo_chain`
was checked only over 60 s of free inertial. Each keyframe inverts a 30×30 information matrix whose prior block is
`inv(cov_gate)`. Horizontal position is unobservable, so its variance grows without bound while the bias variances
stay ~1e-8. The conditioning therefore worsens through the flight, and the `np.linalg.inv` vs Eigen `inverse()`
rounding would be amplified through the recursion. The decisions it feeds are near-exact ties, so one flips:
- On tex, a 1.3 mm state difference follows: the emu build gives 1.28 mm, and the default build 1.14 mm.
- **On blank and trans**, where the Python FGO itself diverges (along-track 23.8 km and 4.5 km), the flips cascade.
- **After that divergence, the recursion loses positive definiteness:** negative traces in Python, from 144.8 s on
  blank and 294.3 s on trans.

**Log names:** `logs/fe_{tex,blank,trans}.log` are forced to the EMULATE-GEMV build's decisions, and
`logs/fd_*.log` to the default build's. Do not confuse them with the band C front-end logs `fe_dsn_tex.log`,
`fe_fwdc.log` and `fe_T_*.log`.

**Forced-gate diagnostic** (`forced_gate.py`: Python with its gate decisions forced to the C++ run's; the core is
patched in-process only):

| bag | Python forced to the emulate-gemv build's decisions, vs that build | Python forced to the default build's decisions, vs that build |
|---|---|---|
| dsn_tex_r1 | **bit-identical** (whole kf export, `cmp`) | max / p99 \|Δp\| 0.151 / 0.012 mm, yaw 1.1e-4 °: **within the band** |
| dsn_blank_r1 | **bit-identical** | 6.0e6 mm: outside the band, as under binit0 (gemv round-off on a divergent run) |
| dsn_trans_r1 | **bit-identical** | 9.8e5 mm: outside the band, as under binit0 |

- **Once the decisions agree, the cores are identical:**
  - emulate-gemv: bit-identical;
  - default build: the binit0 picture (tex passes, while blank and trans differ only through the known gemv rounding
    on a diverging trajectory).
- **So the only new source of difference is the gate decision itself.**

**Assessment (mine, for the user to rule on):**
- Band A's FAIL on tex is a decision tie, not a port error: same factors, same decision rule, round-off-level
  differences in a threshold quantity.
- It does show a property of the design that the thesis should state: **which individual checks fire is not
  reproducible across implementations at the 1e-4 level**.
- The live node (C++) is bit-identical to the C++ replay (L1/L2), so the FLOWN behaviour is deterministic.
- **If a reproducible gate is wanted,** two possible fixes, each a design decision and NOT made here:
  - propagate `cov_gate` in covariance form (Joseph), instead of inverting the information form;
  - or put a hysteresis band on the gate.

### Not re-run
- The live IMU-stamp mode reports (part 3).
- The SITL checks.
- The H tag-input bands FN1–FN4.

## 5. Step time (with the gate; C++ is the flown path)
Single-threaded, nice 19, load average about 1.5, on the workstation.

| run | n | median | p95 | p99 | max | > 33 ms | binit0 median / p95 |
|---|---|---|---|---|---|---|---|
| **C++ live adapter L1** (dsn_tex) | 10197 | **0.523 ms** | **0.783 ms** | 0.898 | 3.09 | 0 % | 0.514 / 0.816 |
| **C++ live adapter L2** (fwdc heading) | 10118 | **0.928 ms** | **1.084 ms** | 1.548 | 3.65 | 0 % | 0.938 / 1.132 |
| C++ replay dsn_tex / trans / blank / fwdc | – | 0.52 / 0.53 / 0.49 / 1.01 ms | 0.67 / 0.86 / 1.04 / 1.25 | ≤ 2.0 | ≤ 3.9 | 0 % | 0.51 / 0.50 / 0.47 / 1.02 |
| Python dsn_tex / fwdc (offline, not flown) | – | 16.1 / 25.4 ms | 19.1 / 35.4 | 31.4 / 39.8 | 45.5 / 54.5 | 0.5 % / 30 % | 15.6 / 24.4 |

**The gate's cost** (a 30×30 inverse at every keyframe for `cov_gate`, plus one at each check) is within run-to-run
noise in C++.

## 6. Install recipe and functional acceptance check (main session; after review and merge; only when no flight runs)
```bash
# 0. preconditions
pgrep -fa '[a]rducopter'; ls ~/thesis_data/FLIGHT_LOCK     # both must be empty / absent
# 1. merge this branch into fwd-camera, then:
cat > /tmp/build_yawgate.sh <<'EOF'
env -i HOME=$HOME PATH=/usr/bin:/bin bash -c 'source /opt/ros/jazzy/setup.bash && B=$HOME/opt/src/build-fgo_cpp-yawgate && cmake -S $HOME/thesis_ws/src/estimators/fgo_cpp -B $B -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$HOME/opt/fgo_cpp -DPython3_EXECUTABLE=/usr/bin/python3 "-DCMAKE_PREFIX_PATH=/opt/ros/jazzy;$HOME/thesis_ws/install/optical_flow_interfaces" && make -C $B -j4 && make -C $B install && md5sum $HOME/opt/fgo_cpp/bin/*'
EOF
python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "install fgo_cpp yawgate" -- bash /tmp/build_yawgate.sh
```

**2. Functional acceptance check, instead of md5.**
- **Inputs:** copied to a PERMANENT path, `~/thesis_data/acceptance/fgo_yawcap_gate/`, with `SHA256SUMS`:
  - the export `dsn_tex_r1_baseline.{init.json,events.f64,raw.f64}`;
  - the reference outputs `cpp_dsn_tex_r1_baseline.{kf,yawgate}.f64` and `L1.kf.f64`;
  - the band-L1 tape `dsn_tex_r1.dj.tape`.
- **Run:**
  ```bash
  A=~/thesis_data/acceptance/fgo_yawcap_gate; O=$(mktemp -d)
  (cd $A && sha256sum -c SHA256SUMS)
  ~/opt/fgo_cpp/bin/fgo_cpp_replay $A/dsn_tex_r1_baseline $O/accept \
    && cmp $A/cpp_dsn_tex_r1_baseline.kf.f64 $O/accept.kf.f64 && cmp $A/cpp_dsn_tex_r1_baseline.yawgate.f64 $O/accept.yawgate.f64 && echo "ACCEPT replay"
  ~/opt/fgo_cpp/bin/fgo_cpp_live_replay $A/dsn_tex_r1.dj.tape $A/dsn_tex_r1_baseline.init.json $O/L1 --imu-stamp header --arm-source param --delay 0.20 \
    && cmp $A/L1.kf.f64 $O/L1.kf.f64 && echo "ACCEPT live (node path)"
  ```
  The replay and live replay are single heavy steps. Run them through `heavy.py`, as `bash <script>`.
- **Reference sha256:**
  - `cpp_dsn_tex_r1_baseline.kf.f64` = `L1.kf.f64` = `baa79472e4c7a7a3c56a549fe86479d0b15ca80e110996c5c5bd13ef7c05ef87`;
  - `cpp_dsn_tex_r1_baseline.yawgate.f64` = `047a0cc2a46f4c6d0ce0d735b0840fb4d4f2e8d47628e040ebd33903c2e6d562`;
  - inputs: `dsn_tex_r1_baseline.events.f64` `07d9bb27…`, `.init.json` `3f44f0a0…`, `.raw.f64` `543a379b…`, the tape
    `fee51e1a…` (full values in `SHA256SUMS`).
- **The old binit0 reference** (`fef3533a…`) no longer applies: the gate changes the keyframes.
- **Dry run of this exact check**, with this stage's scratch build in place of `~/opt`: **ACCEPT replay** and **ACCEPT live (node path)**, with `sha256sum -c` OK on all 7 files (`accept.sh`, run through
  `heavy.py`; log `logs/accept.log`).
- **If ACCEPT fails** on a source that changed after this branch, the bands must be re-run on the merged source.
- **Before S3:** record the new `fgo_cpp_node` md5 in METHODOLOGY (the installed one is `1123742d…`).

## 7. Process notes and anything unexpected
**Continuation.** The stopped agent had run the full band set from its own worktree. Its outputs were NOT reused as
results:
- `room_fgo_replay.py` was edited (12:22:53) after its T_A, T_D and O_r1 Python runs.
- Its `fi60.json` predates the checkpoint fix (12:31:52 against 12:31:23).
- Its UKF rows predate the UKF jitter fix that is now on `fwd-camera`.

Everything was re-run from this tree. As a reproducibility cross-check, its `dsn_tex_r1` Python export and C++ replay
keyframes are byte-identical (`cmp`) to this stage's. Its scripts were copied (not linked), and the old worktree and
the old scratch dir were not modified.

**Other notes:**
- **The probe's comparison with the binit0 probe** stopped on a line-count assert, because there are 4 new lines.
  The common lines were compared separately (§3).
- **Unexpected: the gate fires in flight on dsn_tex**, 63 of 2039 checks. Most of the flight sits just below
  0.04 rad². This is EKF3-like behaviour, not a fault.
  - On fwdc (heading) it never fires, 0 of 2023 checks: the heading keeps yaw variance low.
- **First indications** (single bags, unaligned harness metric; NOT thesis results; old = binit0 ungated):

  | bag | ATE | yaw drift | cruise \|V\| |
  |---|---|---|---|
  | dsn_tex | 133.65 → 131.65 m | −9.05 → −8.04 °/min | 0.487 m/s, unchanged |
  | fwdc heading | 123.22 → 123.22 m | – | – |

  On fwdc the heading acceptance is unchanged (9184 / 9539).

## Files
- **Committed:**
  - `eval/diag/model_audit/free_inertial.py` (the checkpoint fix);
  - `eval/results/fgo_cpp_equiv_yawgate/`: logs, `fi10`/`fi60` JSON and logs, ratios, timing, md5s, every driver and
    step script, and the gate logs;
  - this handover.
- **Scratch only** (`…/scratchpad/yawgate2/`): the exports, the C++ and Python outputs, and the builds.
- **Permanent:** `~/thesis_data/acceptance/fgo_yawcap_gate/`.
