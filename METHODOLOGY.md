# Methodology notes

Reproducibility and scope decisions that feed the thesis methodology chapter.
Facts here are pinned in the harness/config (referenced inline) so they cannot
drift silently.

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

### FINDING — the UKF drift is predominantly a flow-sensor-residual coupling (modelling), diagnosed before the FGO

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

**Verdict: predominantly a modelling / robustness issue (confidence ~70%), not a
fundamental UKF limitation** — EKF3 handles the identical observability and the
same flow error without yaw drift, the isolated flow model is correct-signed, and
clean flow removes the amplification. A **secondary** gyro-z-bias conditioning
weakness persists even with true flow (yaw still drifts, bias still overshoots) —
that part may be a genuine Euler-UKF-vs-quaternion-EKF3 distinction and is not yet
settled. **Because the FGO imports the same `h_flow`, this is diagnosed before the
FGO consumes it** (per the standing instruction). What would settle the remainder:
(a) why a `flow_x` residual partitions to yaw in the UKF but to velocity in EKF3
(compare the velocity/yaw information split); (b) the persistent-bias-with-true-
flow behaviour; (c) whether a fix lives inside the locked constraints. **No fix
proposed here — reported for a decision.**
