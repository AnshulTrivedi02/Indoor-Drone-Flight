# Methodology notes

Reproducibility and scope decisions that feed the thesis methodology chapter.
Facts here are pinned in the harness/config (referenced inline) so they cannot
drift silently.

## STANDING RULE — every ATE states its metric wherever it is quoted

An ATE number is meaningless without its alignment and windowing. **Always label
which of these it is:** `evo -a` (SE3-aligned — removes a constant pose offset *and*
the arbitrary yaw gauge, the fair cross-estimator metric under no compass), `evo`
unaligned (origin only — penalises the yaw gauge, so it is dominated by heading
offset for any no-compass estimator), or **apparatus** (cruise-window, origin
gauge-fixed, **no** yaw alignment — used for the EKF3/UKF noise floor because
`XKF1` is already in the true NED frame). **Never compare across metrics.** This
rule exists because a real near-miss happened: the FGO's `evo -a` 5.10 m read as a
5× win over EKF3's *apparatus* 24.3 m; on the same metric (`evo -a`) it is EKF3
4.79 m vs FGO 5.10 m — on par. Same-metric-only, always.

## Filter consistency — measured overconfidence in the weakly-observable directions (a result)

Direct consistency check: each estimator's error (vs ground truth) against **its own
±3σ** from the logged covariance, `dsn_tex_r1`, n=1. Where the error leaves the band
the filter is overconfident — reporting a tighter covariance than its actual error.

- **EKF3** (from `XKV1/XKV2/XKF4`): **cross-track position (Pos E) is outside ±3σ 39%**
  of the flight (from t=44 s; error grows to ~55 m while the band grows far slower);
  lateral velocity (Vel E) 16%; yaw 10% (last 30 s only). Along-track, height, roll,
  pitch, gyro-Z all consistent.
- **UKF** (logs its own covariance directly, ENU/Euler): **far worse — Pos E 91%,
  Pos N 65%, Vel N 51%, Vel E 33%, yaw 58%.** Both horizontal position axes, both
  horizontal velocity axes, and yaw all overconfident; height, tilt, vertical
  consistent. (Accel-Z bias diverges to ~2 m/s², outside its band throughout —
  flagged, truth-0 assumed.)

Both filters report covariances **far tighter than their actual horizontal/heading
error**, and precisely in the directions that are unobservable or weakly observable
from IMU + downward-flow + range with **no yaw source** (global horizontal position
and heading). This is the textbook symptom addressed by the **observability-consistency
literature** — First-Estimates-Jacobian (FEJ; Huang, Mourikis & Roumeliotis 2008/2010),
Observability-Constrained EKF / OC-VINS, and OC-UKF: a filter that re-linearises at
successive state estimates injects **spurious information into the unobservable
subspace**, artificially shrinking the covariance there and producing exactly this
overconfidence. It is **a result in its own right** and a discriminating axis for the
comparison: the UKF's sigma-point linearisation is markedly more overconfident than
EKF3's here, and a re-linearising smoother (FGO) is expected to differ again. NEES
against ground truth would quantify it directly. Figures:
`plots/{ekf3,ukf}_diag_2_consistency.png`.

## Lateral-flow derotation coupling — real anomaly, proposed fix FAILED and reverted

**What is real.** The shared `h_flow`'s lateral-flow prediction carries a large
roll-rate-coupled residual against the measured flow: `lateral_residual =
−2.07·rollspeed` (stable ±0.02 across `dsn_tex_r1/r2/r3`, corr −0.94), tracking roll
*rate* not roll *acceleration* (so not a timestamp offset). The lateral flow channel
is `h_flow`'s noisiest by far (residual std 0.60 vs 0.007 forward). Found by the
state-vs-time diagnostic (`plots/ekf3_diag_4`, `diag_flow_residual.py`), not by
hypothesis-testing.

**What FAILED.** I concluded this was a *sign error* in `flow_x_rot` (h_flow uses
`−rollspeed`; the value was flipped from the original `+rollspeed` derivation after a
hover test that CLAUDE.md Known Issue #1 flags as confounded), and that EKF3 had the
correct sign while the UKF/FGO were disadvantaged — motivated by EKF3's own flow-X
innovation correlating +0.03 with roll rate vs the UKF's +0.71. **That conclusion was
wrong on two counts, caught by gating the fix on a re-run (do this — it is the
discipline that saved the result):**
1. Flipping the sign **made the UKF worse**, not better: ATE evo `-a` 11.7 → 16.3 m,
   yaw drift +12.4 → +19.3 deg/min, gyro-z overshoot 245% → 336% (`dsn_tex_r1`). The
   UKF's flow-X innovation flipped +0.71 → −0.69 rather than dropping to ~0 — because
   the UKF's velocity *adapts* to absorb flow, so its innovation reflects the
   prediction term, not the sensor residual.
2. The EKF3-vs-UKF innovation comparison (+0.03 vs +0.71) that motivated it was
   **not apples-to-apples**: EKF3's `FIX` is a *post-derotation* innovation; the UKF's
   is a *full-model* innovation, so EKF3's is naturally less roll-coupled by
   construction. It does **not** establish that EKF3 derotates "more correctly."

**Status.** The sign flip is **reverted** (`measurement_models.py` unchanged from
baseline). The rollspeed coupling in the GT residual is real but its correct treatment
is not a sign flip and is **not yet understood** — the sensor-model residual improves
under the flip while the estimator degrades, and the EKF3/UKF derotation relationship
is more subtle (different fusion structure + the `flow_bridge.py:123` path flip).
**No prior result is retracted or marked provisional** on this basis: the premise
(a fixable handicap that disadvantaged the UKF/FGO) did not hold. The four-estimator
yaw finding **stands**. **Parked** as a characterised open question for the thesis:
common-mode across UKF and FGO (shared `h_flow`), non-blocking.

**METHODOLOGICAL CONTROL — the empirical re-run gate.** The sign fix was supported by
**three independent offline lines** — the −2.07 GT-residual slope, roll-*rate*-not-
acceleration coupling, and EKF3's +0.03 vs the UKF's +0.71 innovation correlation — and
was still **wrong**: applied, it degraded the UKF (ATE `-a` 11.7→16.3, drift 12.4→19.3,
overshoot 245%→336%) and its innovation flipped (+0.71→−0.69) rather than zeroing. The
control that caught it: **gate every measurement-model change on a from-scratch
estimator re-run, and revert if the outcome metric degrades** — offline residual
diagnostics and innovation correlations are necessary evidence but not sufficient,
because a filter's state adapts to whatever model it is given. Adopt this as a standing
rule for `h_flow`/gate/noise changes, not a one-off.

**Lateral-vs-forward asymmetry — motion profile, not structural (settled).** `h_flow`'s
two axes are structurally near-symmetric: translational sensitivity is identical
(`∂flow/∂v = 0.571` both), rotational sensitivity differs only 1.3× (`∂flow_x/∂rollspeed
= −1.14` vs `∂flow_y/∂pitchspeed = +0.86`, from the `ω×lever` term × the `SIGN_X/Y`
convention). The 27× lateral-noise excess is **the corridor motion profile**: cruise
**rollspeed std 0.399 rad/s vs pitchspeed std 0.013 — 31×** (forward flight commands
large oscillatory roll for lateral position control, near-zero oscillatory pitch), so
the lateral rotational-flow term is ~40× the forward one. Expected and documented; not
a structural defect in the measurement model.

## Sensor noise & gyro drift — controlled, deterministic, single realisation

- **All three estimators see one identical noise/drift realisation.** EKF3, the
  UKF and the FGO are all evaluated **offline on the same recorded bag** (EKF3
  from `ardupilot.bin` `XKF1`; UKF/FGO from the bag's `/imu/data_raw`,
  `/optical_flow/measurement`, `/downward_lidar/range`). They therefore consume
  the *same* recorded sensor stream — the gyro the FGO integrates is byte-for-byte
  the gyro EKF3 saw. Fairness on this axis is guaranteed by the replay
  architecture, not by any random-seed matching.

- **The gyro drift is deterministic and reproducible, NOT a random draw.** SITL
  injects no random gyro bias in this configuration: `INS_GYROFFS=0`,
  `SIM_GYR*_BIAS=0`, `SIM_GYR*_RND=0`, and all other random sensor noise is
  zeroed (`sim_noise.parm`). The gyro drift comes solely from SITL's
  **deterministic periodic** drift model, `SIM_DRIFT_SPEED=0.05` deg/s/minute and
  `SIM_DRIFT_TIME=5` minutes (`SITL.h:213-214`, `SITL.cpp:73,77`) — a fixed
  function of sim time. SITL has no PRNG seed to set (no `srand`/`srandom`
  anywhere), so with the random noise zeroed its sensor output is deterministic.
  The **physical yaw drift is +9.8 deg/min** — measured by integrating the raw
  gyro-z (`IMU.GyrZ`) over the cruise (true yaw, `SIM.Yaw`, drifts +0.01 deg/min,
  confirming straight flight so the whole 9.8 is gyro bias). It is near-identical
  across every `dsn_*` bag (9.81–9.84, deterministic) and reproduces on any
  re-fly — **controlled**, not **sampled**. (Do not confuse this with an
  estimator's *residual* drift: `nomag_corridor_baseline` earlier reported EKF3's
  own residual yaw drift of +5.32 deg/min, i.e. what was left after EKF3 corrected
  ~40% of the bias on that particular trial. That 40% is trial-specific — on the
  `dsn_*` batch EKF3 corrects only ~14–33%, XKF1 yaw drifting +6.6…+11.1 deg/min,
  mean ~8.1 — so EKF3 too drifts near the physical rate under no yaw source.)

- **Robustness across drift realisations is explicitly out of scope.** The study
  uses one controlled drift profile, identical in every trial, so drift is *not*
  a confound between worlds or estimators — it is held fixed while floor texture
  (and the estimator) varies. Because it is a single realisation (n=1 in
  drift-space), no claim is made about robustness to *different* drift
  realisations; that is a **Term 3 extension** (real flights, in-loop, with
  varied/real IMU drift), not a gap in this comparison.

- **Pinned & recorded.** `sim_noise.parm` versions the drift/noise params under
  `git_commit`; `fly_trial.py`'s `EXPECTED_PARAMS` verifies them live each trial
  (eeprom-persistence gotcha); and `run_trial.sh` dumps the live `SIM_*` values
  from each flight's `.BIN` into `metadata.yaml` (`sim_noise:` block). The
  flow-pipeline RANSAC seed is fixed (`ransac_seed=42`, `flow_tracker.py`) and
  recorded (`flow_ransac_seed` in `metadata.yaml`).

## Flow processing is baked in at record time — irreversible from the bags

The dataset bags record the **processed** optical-flow output
(`/optical_flow/measurement`: `flow_x_raw/y_raw`, `flow_x_rad/y_rad`,
`inlier_ratio`, `valid`, `feature_count`), **not** the raw camera frames. Raw
`/downward_camera/image` and `/downward_camera/camera_info` are bridged live for
`flow_tracker` but deliberately kept off the record list (bag-size cost).

**Consequence — state this in the methodology:** all optical-flow processing
choices are **fixed at the dataset flight and cannot be varied afterward from
these bags**. This includes the RANSAC parameters (reprojection threshold,
model, `ransac_seed`), the camera **focal length** used for the pixel→angular
conversion (`flow_x_raw/FOCAL_LENGTH_PX → flow_x_rad`), and the derotation
handling. Every estimator consumes the *same* frozen flow stream — which is the
intended fairness property — but any experiment that would require *re-deriving*
flow with different processing needs a **new dataset flight**, not a reprocessing
of the existing bags. This is an accepted, deliberate limitation of the recording
design, not an oversight.

## Run-to-run noise floor (n=3 per condition)

The GNSS-denied dataset is three corridor conditions — textured, blank,
transition — each flown as **three identical-config repeats** (0.5 m/s, 2.0 m,
300 s, ~145 m, RANSAC seed 42). **All figures below are n=3.**

Repeats are not identical. Even with the gyro drift deterministic (above) and
the RANSAC seed fixed, the live pipeline (Gazebo→ROS2 camera-frame capture/drops
and scheduling) produces run-to-run variation; that variation *is* the
measurement noise floor, and it is characterised here before any condition is
interpreted. All metrics are XKF1-vs-SIM over the aided window, origin
gauge-fixed, **no** yaw/SE(3) alignment.

- **Within-condition ATE range is 2.81–10.90 m** (blank 2.81, transition 8.15,
  textured 10.90) against a **~68 m between-condition separation** (textured
  mean ATE 17.8 m vs blank mean ATE 85.8 m).
- **Cross-track (east) is a noisy channel.** Within-condition ranges are
  7.0–22.9 m and the ranges **overlap across conditions**, so cross-track error
  alone does not separate them.
- **The cross-track variation is not heading divergence.** Yaw error (XKF1−SIM)
  is reproducible to **0.263° at 300 s** (spread across the three textured
  repeats) — far too small to account for the ~15 m cross-track spread. Yaw is
  compass-aided and consistent run-to-run; the spread originates in the flow
  channel, not in heading.
- **Along-track distance is reproducible and boundary-sharp.** Final XKF1 PN
  varies ≤1.15 m within a condition (textured 0.48, transition 0.53, blank
  1.15); in the transition world all three repeats stop accumulating PN at true
  y = 81.7 m (range 0.2 m), tracking the y=80 m texture boundary to ~1.7 m with
  a ~1.4 m transition width.

**Primary metrics: ATE and along-track distance.** Cross-track error is reported
with its n=3 spread but is **not** used as a primary discriminator between
conditions (noisy, overlapping ranges). Figures: `plots/alongtrack_vs_travel.png`,
`plots/textured_crosstrack.png`, `plots/textured_yaw.png`.

## Simulation environment provenance

The thesis sim environment — corridor worlds + custom floor/wall models + iris
sensor config — is vendored under `sim/` and committed at `7be3672`. From that
commit the harness runs from the tracked files (`sim/worlds`, `sim/models`), so a
trial's `git_commit` pins the environment. See `sim/README.md`.

**Mesh provenance (not vendored).** The iris drone (~22 MB) and runway (~28 MB)
meshes are supplied by `~/ardupilot_gazebo`, a clone of
`ArduPilot/ardupilot_gazebo` at **upstream base `082a0fe`** ("Iris: improve
collisions") plus three thesis commits: `d1eaad3` (iris downward camera +
gpu_lidar — mirrored in `sim/reference/iris_with_standoffs.model.sdf`),
`e0359c2` (corridor worlds), `81e6b10` (visual-only floor tiles + ground
collision). Every trial records the live `ardupilot_gazebo_commit` and
`ardupilot_gazebo_upstream_base` in its `metadata.yaml`, so the mesh source is
explicit per trial even though the meshes are not in git.

**The nine dataset trials predate vendoring.** `ds_{tex,blank,trans}_r{1,2,3}`
were flown from `~/ardupilot_gazebo` **before** the `sim/` vendoring commit
(`7be3672`) — *not* from the tracked `sim/` path. Equivalence rests primarily on
a **byte-identical `diff`**: the vendored worlds and models match the
`~/ardupilot_gazebo` originals that flew the dataset exactly (0 differences), so
any flight difference is run-to-run noise by definition. A verify flight
(`vendor_verify_full`, corridor_textured flown from `sim/worlds/`) corroborates
this — it matched tightly on **along-track PN** (154.04 m, inside the `ds_tex`
0.48 m reproducible band), while cross-track (9.37 m) fell within run-to-run
variability, below the n=3 observed band ([19.82, 39.22] m) that three samples do
not bound on that noise-dominated channel. Stated as honest provenance, not a
retroactive claim the dataset was flown from the tracked path.

## Comparison dataset — nomag (no yaw source)

The three-way EKF3 / UKF / FGO comparison uses trials flown under
`gnss_denied_nomag.parm` (`EK3_SRC1_YAW=0`, compass unused) — the **`dsn_*`
batch** (3 corridor worlds × 3 repeats).

**Why not the compass-active `ds_*` trials.** The nine `ds_{tex,blank,trans}_r*`
trials were flown under `gnss_denied.parm`, which leaves EKF3 fusing the compass
for yaw. That is a **yaw source the UKF and FGO structurally cannot have** — the
thesis sensor suite is IMU + flow + LiDAR, and no compass topic is even recorded.
So on `ds_*`, EKF3 holds a correct heading while the no-compass UKF/FGO yaw drifts
at the physical gyro rate — an **information asymmetry that invalidates the
comparison**, not a formulation difference. (Confirmed during UKF bring-up: the
UKF's yaw tracks the raw gyro drift ~9 deg/min; EKF3-with-compass does not.)

**The `ds_*` trials are retained, not deleted**, as (a) the run-to-run
noise-floor characterisation (above) and (b) the EKF3-with-yaw-source reference.
They are **superseded for the three-way comparison** by the nomag `dsn_*` batch,
in which all three estimators face the same no-yaw condition and EKF3's own yaw
drifts too (~5 deg/min under the deterministic SIM_DRIFT).

Both datasets are labelled by a `yaw_source:` block in `metadata.yaml`
(`EK3_SRC1_YAW`, `COMPASS_USE`, read from each flight `.BIN` by `run_trial.sh`),
so a downstream script distinguishes them **positively**, not by inference from
absence — `dsn_*` carry `EK3_SRC1_YAW=0`/`COMPASS_USE=0`, `ds_*` carry `1`/`1`.
The nine of each were backfilled after the field was added.

**Framing for the results: both estimators struggle under unobservable yaw.**
Against the physical drift of +9.8 deg/min, EKF3's own yaw (`XKF1.Yaw`) drifts
+6.6…+11.1 (mean ~8.1) across the nine `dsn_*` bags — it corrects only **14–33%**
of the bias. This is *not* "UKF diverges, EKF3 fine": with no yaw source, EKF3 too
runs near the physical rate, because yaw is weakly observable from downward flow
at 0.5 m/s (∂flow/∂yaw = v/h ≈ 0.29 rad/s per rad, against 0.25 rad/s measurement
noise). The interesting axis of the comparison is therefore *how each estimator
fails* under an unobservable heading — a fairer and more informative framing than
an accuracy race. (The UKF's *additional* failure — a diverging gyro-z-bias state
that amplifies the drift rather than tracking near the physical rate — is the open
finding below.)

## UKF pseudo-yaw cap — variance-gated to match EKF3 (fairness)

The UKF fuses a zero-innovation yaw pseudo-measurement to bound yaw variance in
the no-mag case, matching EKF3's `fuseEulerYaw(PREDICTED)`. EKF3 does **not** do
this every cycle: it checks the opportunity every 140 ms
(`AP_NavEKF3_MagFusion.cpp:263`) but only fuses when attitude covariance has
grown past a threshold (`MagFusion.cpp:274`,
`P[0][0]+P[1][1]+P[2][2]+P[3][3] > 0.01`). The UKF now gates the same way — fire
only when `P[6,6]+P[7,7]+P[8,8] > 0.04` — rather than firing unconditionally at
7 Hz. **Firing unconditionally is rejected on the same principle as `FLOW_FXSCALER`:
it produces a better ATE by doing something EKF3 does not do.**

**The 0.04 threshold is verified, not assumed** — three independent ways.
(i) The quaternion→Euler factor is *exact* to first order at any nominal attitude:
the quaternion error Jacobian `G` (`δq = ½·G·δθ`) has `GᵀG = I`, so
`trace(P[0..3]) = ¼·trace(Cov(δθ))` — EKF3's `0.01` maps to attitude-trace `0.04`,
independent of heading (not a small-angle approximation). (ii) EKF3's own cruise
tilt variance is `XKF4.errRP² ≈ 1×10⁻⁴ rad²` (`dsn_*`), negligible against the
0.01 gate, so EKF3's cap is effectively a **pure yaw-variance gate**. (iii) EKF3's
own logged quaternion covariance (`XKV1.V00..V03 = P[0][0..3]`) sits at **median
0.0093, max 0.01001 — pinned just under its 0.01 gate on all nine bags**,
confirming the gate value directly from EKF3's operating state. No reflight or
printf was needed.

### The firing rates differ — but the threshold is right; the cause is upstream

EKF3's `P[0..3]` is *pinned at* its gate → EKF3 fires the zero-innovation yaw cap
at essentially **every 140 ms opportunity** to hold it there. The UKF, with the
*same* threshold, fires only **~1%** — because its own attitude-cov trace sits at
Euler **0.029** (quaternion-equivalent 0.0072), **below** the 0.04 gate, so it
rarely trips. This is not a mis-specified threshold (verified three ways above):
the UKF's yaw covariance is **suppressed below EKF3's operating point by the flow
updates themselves**, whereas EKF3's yaw covariance rises to the gate. So the UKF
is simultaneously **over-confident in yaw** (covariance lower than EKF3's) *and*
**drifting faster** (yaw drift 12–32 vs EKF3's ~8 deg/min) — a filter-consistency
failure localised to how the flow measurement couples into the yaw / gyro-z-bias
states, *not* to the yaw cap.

### FINDING — the UKF yaw drift is a yaw-capping-frequency effect, NOT a parameterisation difference (diagnosed + FGO-tested)

Denominator corrected: physical drift is **9.8 deg/min** (not the earlier 8.9;
raw `IMU.GyrZ`, see the sensor-noise section). Against it the unclamped UKF
gyro-z bias overshoots to **~220–450%** across the `dsn_tex` batch (three bags),
the yaw drifts 12–32 deg/min, and the trajectory diverges (ds_tex_r1 ATE evo `-a`:
8.6 → 19.9 m). Diagnosed (half-day box, no fixes applied):

1. **Yaw is weakly observable from downward flow at 0.5 m/s** — `∂flow/∂yaw = v/h ≈
   0.286` rad/s per rad (numerical Jacobian), against `FLOW_M_NSE = 0.25`; a 5.7°
   yaw error moves flow only 0.029 rad/s (SNR ≈ 0.11). Per-update the UKF moves yaw
   only ~0.024°, so the movement is not *excessive in magnitude* — the problem is a
   systematic *wrong-direction* bias.
2. **Not attributing to states EKF3 doesn't; not a sign error.** EKF3's flow `H`
   is nonzero only on quaternion (0–3) + velocity (4–6)
   (`AP_NavEKF3_OptFlowFusion.cpp:342-348,504-510`), fuses X then Y sequentially
   (`:327-328`), and updates gyro bias (10–12) via cross-covariance once
   `!inhibitDelAngBiasStates` (`:470-473`, un-inhibited after tilt align,
   `AP_NavEKF3_Control.cpp:172`) — structurally identical to the UKF (attitude+
   velocity observation, per-axis sequential, gyro-bias via cross-cov). A
   controlled single-update test confirms `h_flow`'s yaw coupling has the **correct
   sign** (flow moves a drifted yaw *toward* truth in isolation).
3. **The driver is the real flow sensor's residual, not the filter machinery.**
   Decomposing yaw by source over cruise, the *measured*-flow update **adds** +3.69
   deg/min to the drift (predict +9.00, NET +12.70). Re-running with **true flow
   injected from ground truth** (velocity from `d(GT pos)/dt`, GT attitude — no
   sensor scale/derotation/noise), flow's contribution flips to **−0.66** (it now
   correctly *reduces* drift). So the real flow error (the documented ~+6.5% scale,
   plus derotation/noise) is what leaks into yaw via the measurement model —
   **where EKF3 confines the same residual to velocity** (giving its +6.5% velocity
   scale) and does not let yaw drift.

**The partition is the SAME across Euler and SO(3) — parameterisation is NOT the
cause** `[direct test, supersedes the earlier "formulation difference" hypothesis]`.
A `flow_x` residual splits between velocity and yaw in proportion to `(P·Hᵀ)`, and
all three estimators share the velocity/yaw diagonal ratio (~0.57). A controlled
single-update test — one `flow_x` residual, UKF-matched diagonal priors — settles
the parameterisation question directly:

| estimator | Δyaw | Δv_E | residual lands in |
|---|---|---|---|
| UKF (Euler) | +0.328° | +0.0064 m/s | velocity 69% / yaw 31% |
| FGO (SO(3), `Pose3`) | +0.317° | +0.0062 m/s | velocity 69% / yaw 31% |

They partition **identically**. So the attitude representation (Euler vs SO(3))
does **not** change where a `flow_x` residual lands — this **refutes** the earlier
hypothesis (in prior git revisions of this section) that the leak was an
Euler-vs-quaternion formulation difference. The SO(3) re-parameterisation that was
recorded as the "falsifying test" is effectively run: the FGO *is* an SO(3)
estimator, and it leaks to yaw the same 31% as the Euler UKF.

**The real discriminator is the yaw-capping frequency, not the parameterisation.**
The ~31%-per-update yaw leak is common to all three. What differs is how often the
accumulated yaw is re-constrained: EKF3 fires `fuseEulerYaw(PREDICTED)` at ~every
140 ms opportunity (its `P[0..3]` pinned at the 0.01 gate), while the UKF's
variance-gated pseudo-yaw fires ~1% (its trace sits just below the gate) — so the
UKF lets the leak accumulate into drift while EKF3 caps it continuously. `h_flow`
is verified correct (true-flow test); this is a capping-mechanism distinction, not
a measurement-model bug and not a parameterisation effect.

### Does the FGO inherit this? — Yes in principle; its yaw behaviour is set by the anchor, not by SO(3)

Earlier this section concluded "No — SO(3) makes the FGO immune, fix-before-FGO
does not apply." **That is now retracted.**

> ## ⚠️ THE FIRST FGO ATE (0.49 m aligned) IS AN ARTEFACT — DO NOT QUOTE IT AS AN FGO RESULT
>
> The first FGO run (`dsn_tex_r1`, n=1, `BatchFixedLagSmoother`) gave ATE evo `-a`
> **0.49 m** (unaligned 128 m; a ~90° init-yaw gauge offset), along-track 151.8 m
> (true 151.1), 10047 keyframes. **This number is void as an estimator result.** It
> came from a yaw prior that anchors each keyframe's yaw to a *fixed* reference
> (yaw→0, 0.5 rad), which repeated per keyframe accumulates into a ~5° effective
> **absolute heading anchor** — stronger than, and mechanically different from,
> EKF3's/UKF's *zero-innovation* cap. That pinned the yaw (drift −0.04 deg/min) and
> flattered the aligned ATE. **A 50× improvement over EKF3's 24.3 m on the same
> condition is not credible** and is entirely explained by the over-constrained yaw,
> not by smoothing. FGO_DESIGN §9.4 conflated "weak yaw prior" with "zero-innovation
> cap"; they are not equivalent. Kept only as the before/after evidence for why the
> anchor was wrong. The fair-anchor re-run (below) is the real first FGO result.

**Corrected conclusion.** The FGO does not get yaw-drift immunity for free from
SO(3); the per-update partition is identical to the UKF's, so its yaw behaviour is
decided entirely by the anchor mechanism. **Proposed (not applied):** anchor the
yaw prior to each keyframe's IMU-*predicted* yaw (zero-innovation, matching EKF3)
instead of a fixed reference, then re-run — the expected outcome, given the
identical partition, is that the FGO drifts comparably to the UKF, making the yaw
leak a **genuine, parameterisation-independent** phenomenon under weak yaw
observability (controlled only by the capping mechanism), not an Euler artifact.
`h_flow` correctness stands. §9.5 stays open.

### The real first FGO result — fair (zero-innovation) yaw anchor

The yaw cap now anchors each keyframe to its IMU-**predicted** yaw
(`Xk.rotation().yaw()`), so the error is ~0 at the linearisation point — a genuine
zero-innovation cap matching EKF3's `fuseEulerYaw(PREDICTED)` (`innovYaw = 0.0f`,
`AP_NavEKF3_MagFusion.cpp:1062-1064`, against `yawAngPredicted` = current state yaw,
`:970`). Re-run `dsn_tex_r1`, n=1, batch:

| metric | fixed anchor (artefact) | **fair anchor (result)** |
|---|---|---|
| ATE, evo `-a` | 0.49 m ⚠️void | **5.10 m** |
| ATE, unaligned | 128 m | 139 m |
| along-track | 151.8 m | 147.5 m (true 151.1) |
| cross-track | +151.7 m | +139.8 m |
| **yaw drift** | −0.04 deg/min | **−9.24 deg/min** |
| gyro-z bias | −4.88 | +0.13 deg/min |

**The prediction held: with a fair cap the FGO's yaw drifts (−9.24 deg/min), and the
0.49 m artefact is gone.** Stated plainly and as a *result*, not a failure:

> **The yaw leak under an unobservable heading is independent of the attitude
> parameterisation AND of filtering-vs-smoothing — it is controlled only by the
> yaw-capping mechanism.** All four configurations drift near the physical
> +9.8 deg/min and none recovers yaw from flow: EKF3 (quaternion filter) **8.4**,
> FGO (SO(3) smoother) **9.24**, UKF-Euler unconditional-cap **9.52**, UKF-Euler
> gated-cap **12.7**. The spread is explained entirely by **capping frequency**:
> EKF3, the FGO and the unconditional UKF cap yaw often (EKF3 ~7 Hz with `P` pinned
> at its gate; FGO every keyframe ~30 Hz; UKF-uncond 7 Hz) and drift near physical
> with a stable bias; only the UKF's *variance-gated* cap fires ~1 %, letting flow
> corrupt the gyro-z bias (overshoot ~220–450 %) and drift *above* physical. Neither
> the Euler↔SO(3) chart nor filter↔smoother changes this — the estimator's only
> lever on yaw under no yaw source is how often it caps the variance.

(One documented formulation detail: the FGO caps every keyframe, ~30 Hz, vs
EKF3's/UKF's ~7 Hz — more frequent, but zero-innovation so it injects no heading;
it only holds the yaw marginal slightly tighter. Matching the rate exactly is a
refinement, not a fairness violation.)

**Scale sanity-check — the 5.10 m is NOT a 5× win over EKF3; it is on par.** The
5.10 m is `evo -a` (SE3-aligned); EKF3's 24.3 m (apparatus floor) is *unaligned*.
On the **same metric** (`evo -a`, `dsn_tex_r1`): **EKF3 4.79 m vs FGO 5.10 m** —
essentially equal, FGO marginally worse. The apparent 5× improvement was a
metric mismatch (aligned vs unaligned), not a result. The FGO's *unaligned* ATE is
139 m, dominated by the ~90° init-yaw gauge offset (no compass → arbitrary heading),
which `evo -a` removes. **Not a bug and not smoothing-magic:** instrumented, the FGO
tracks the flow (cruise flow-factor residual ≈ 0: x −0.0007, y −0.0012 rad/s) and
its cruise velocity is `|V(k)| = 0.517 m/s`, **+4.7 %** over true — so it *does*
inherit a flow scale error, merely smaller than EKF3's `0.556 m/s` (+12.6 %) on this
bag (n=1; the smaller inheritance is unexplained and not leaned on). The along-track
147.5 m looking "too good" vs true 151.1 was coincidence: the +4.7 % speed offset is
cancelled in *displacement* by the −9.24 deg/min yaw-drift curvature. Flow is the
only horizontal-velocity observation, so the FGO could not have avoided the scale —
and it didn't.

**Flow_x partition (re-checked).** The controlled single-update partition is
anchor-independent — Euler-UKF and SO(3)-FGO still both 69 % velocity / 31 % yaw.
The fair-anchor full run confirms the accumulated consequence: yaw drifts once the
cap no longer over-constrains it.

**Computational cost — goes in the results regardless of accuracy.** Batch smoother
**101 ms/step median, p99 167 ms — 3–5× over the 33 ms deployability budget**. The
incremental (iSAM2) solver is 0.2 ms/step (well under budget) but **cascades after
~590 keyframes**. The cascade is isolated to the incremental marginalisation layer,
not our estimator logic: the *same* factors and core run to completion under batch
(10047 keyframes, 0 failures), so it is a GTSAM iSAM2 + Python-`CustomFactor` +
fixed-lag interaction. Whether it is inherent to that combination or an
implementation artefact is not yet root-caused; batch is the robust path meanwhile.
This is the measured version of FGO's main known weakness (compute).
