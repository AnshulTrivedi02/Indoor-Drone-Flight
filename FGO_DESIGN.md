# FGO Design — online factor-graph smoother (third estimator)

**Status:** design record, no estimator code written yet. This is the durable
counterpart to `CLAUDE.md`'s "UKF Design" section, kept as its own file so
`CLAUDE.md` stays owned by the world/config session. On approval the code
deliverables listed in [Files this creates](#files-this-creates) are built
against this document; nothing here is committed as running code yet.

## Provenance and how to read the attributions

This file is derived from the week-9 FGO structural-design plan produced in an
earlier session (`~/.claude/plans/here-s-prompt-2-complete-spicy-bird.md`,
"FGO Design — structure only"). That plan crash-survived only in the plan
cache; committing it here is the point of this file. Attribution convention:

- **Unmarked prose** is from that design plan, which itself cites ArduPilot
  EKF3 source and `CLAUDE.md` at the line level (citations preserved).
- **`[VERIFIED]`** — a claim I re-checked against live source or the committed
  repo in this session; the checking evidence is given inline.
- **`[RESOLVED]`** — something the plan left as an open action that has since
  been closed in the repo (chiefly the lever-arm `.parm` work, commit
  `2f34efd`); folded in here with the resolving evidence.
- **`[DECIDED]`** — a design question that was open in the prior pass and is now
  settled with user sign-off. The three items in
  [§9 Resolved design decisions](#9-resolved-design-decisions) are all `[DECIDED]`
  as of this pass; where a decision conflicts with earlier §1/§8 prose, the §9
  decision governs (cross-referenced inline). (`[OPEN]`/`[INFERRED]` was the
  earlier status of these items — retained in git history, no longer present.)

Governing principle throughout, unchanged from the plan: **sensor inputs must
match across estimators; formulation may differ.** The FGO sits alongside
ArduPilot EKF3 (fixed baseline) and the UKF (designed, not yet coded). Scope is
fixed: fixed-lag smoother, IMU preintegration, custom optical-flow and range
factors, **no loop closure**, a live ROS2 node publishing `/fgo/pose` as
`geometry_msgs/PoseWithCovarianceStamped`, developed against bag replay with
`use_sim_time:=true` and deployable unchanged to hardware.

### Sources read (from the plan, citations preserved)

| Source | What it gave |
|---|---|
| `CLAUDE.md` "UKF Design" | 15-state vector, ENU/FLU, `h_flow`/`h_range`, matched `R`/gates, init strategy |
| `CLAUDE.md` "Sensor Fusion Architecture" | each estimator derotates internally; raw flow + raw gyro are the common inputs |
| `src/optical_flow_node/optical_flow_node/flow_tracker.py:224–275` | validated derotation coefficients and the FRD→FLU→camera-optical frame chain |
| `optical_flow_interfaces/msg/OpticalFlow.msg` | `flow_x_rad`/`flow_y_rad`, `inlier_ratio`, `valid` |
| commit `ca120e6` | 333 Hz IMU, EKF3 predict dt = 0.0125 s, the four GTSAM noise constants, the ~2.35 s late start |
| `AP_NavEKF3_OptFlowFusion.cpp` | EKF3's own flow model, `losPred`, tilt-corrected range, the `FLOW_MAX` gates, sequential X/Y fusion |
| `AP_NavEKF3_Measurements.cpp` | the 4.2 rad/s corrupt-data clamp, `flowRadXYcomp = flowRadXY + bodyRadXYZ`, raw range storage |
| `AP_NavEKF3_PosVelFusion.cpp`, `core.cpp` | `hgtMea = rng·cos(tilt) − terrainState`, `terrainState = 0` |
| `AP_NavEKF3_GyroBias.cpp`, `core.h`, `AP_NavEKF3.cpp` | EKF3's *initial bias uncertainties* — reused below as matched priors |

---

## 0. Resolved geometry — sensor lever arms `[RESOLVED]` `[VERIFIED]`

The plan flagged `FLOW_POS_*` / `RNGFND1_POS_*` being unset as a **pre-flight
gate**: with them at zero EKF3 ran `posOffsetBody = 0`, so its flow model
multiplied the `bodyRadXYZ × posOffsetBody` term by zero and treated the range
as the height of the IMU rather than of `base_link`. That gate is now **closed**
in commit `2f34efd` ("Set flow/rangefinder body-frame position offsets to
correct the EKF3 lever-arm scale error"), which is HEAD as of this writing.

### The one thing the FGO factor must not re-derive wrong

**`FLOW_POS_Z = 0.13` is the camera-to-rangefinder offset, NOT the camera's
body position.** The camera sits at z = −0.25 m and the LiDAR at z = −0.12 m
relative to `base_link` (= IMU/body origin) in `iris_with_standoffs/model.sdf`;
both on centreline, so X = Y = 0. The literal camera-from-origin figure is 0.25,
yet `FLOW_POS_Z` is set to **0.13 = 0.25 − 0.12**. This is not a fudge — it is
forced by how EKF3 forms the flow height, traced at pinned ArduPilot commit
`7bac20cbcc` and **re-verified against the live source tree this session**:

- `readRangeFinder` (`AP_NavEKF3_Measurements.cpp:85`) stores the **raw** LiDAR
  distance (`rangeDataNew.rng = MAX(storedRngMeas…, rngOnGnd)`); it never
  applies `RNGFND1_POS_Z` to the range. So the range EKF3's flow path sees is
  **LiDAR-referenced**, not origin-referenced. `[VERIFIED]`
- The flow terrain height is `heightAboveGndEst = MAX(terrainState − pd,
  rngOnGnd)` (`AP_NavEKF3_OptFlowFusion.cpp:298`) with
  `terrainState = MAX(rng·prevTnb.c.z, rngOnGnd) + stateStruct.position.z`
  (`:112`). The origin height `pd` (= `position.z`) therefore **cancels**:
  `terrainState − pd = rng·c.z`. `[VERIFIED]`
- `:317` then applies the flow offset: `range −= posOffsetEarth.z /
  prevTnb.c.z`, i.e. it subtracts `FLOW_POS_Z` (rotated to earth, tilt-scaled)
  from that LiDAR-referenced range. So EKF3 computes
  **`camera_height ≈ lidar_range − FLOW_POS_Z`**. `[VERIFIED]`

The value that yields the *true* camera height is thus the camera-to-LiDAR
separation **0.13**, not the camera-from-origin 0.25 (which would over-correct
to 1.90 m, −5.9%). `RNGFND1_POS_Z = 0.12` is set to the true physical value for
the **height-estimate** path (`EK3_SRC1_POSZ = RangeFinder`), where it correctly
refers origin height to the ground datum; it does **not** enter the flow path
(it cancels, as above).

### Consequence for the shared measurement models — state it so it is not re-derived

The camera height used in the flow denominator must equal EKF3's
`lidar_range − 0.13`. Two equivalent forms, both correct, and the FGO/UKF must
use one of them — **never** `p_U − 0.13` or `lidar_range − 0.25`:

```
camera_height  =  lidar_range − 0.13                       (LiDAR-referenced form)
              =  p_U − 0.25                                (base_link-referenced form)
```

They are identical because the range factor pins `p_U = lidar_range + 0.12`
(§3): `(lidar_range + 0.12) − 0.25 = lidar_range − 0.13`. The design below uses
the **`p_U − 0.25`** form inside `h_flow` because the factor already holds
`X(k).translation().z()`; the identity above is the audit trail proving it
matches EKF3's flow path. `[VERIFIED]` this identity holds under commit
`2f34efd`'s values.

Empirical arbiter, pre-registered: the +6.4% flow-derived velocity/position
over-estimate (n = 1 on `corridor_tex_verify`, `ekf3_diag_60s`) was the symptom;
acceptance is `|residual| ≤ 2%` on the validation trial. That trial has **not**
run yet — it is the next step after this design is on disk.

### Implementation decisions carried from the plan (unchanged)

- **Implementation target — Python `gtsam.CustomFactor`, decided not hedged.**
  The shared `h_flow` is the fairness argument, not a convenience: the UKF and
  FGO must share one measurement model so the only difference is
  filtering-vs-smoothing. Two implementations in two languages is a place they
  silently diverge (that exact class of bug has bitten repeatedly). Importing
  one function makes divergence structurally impossible. Python overhead lands
  only on the `CustomFactor` error/Jacobian callback; linearisation, Cholesky
  and marginalisation stay in GTSAM C++. Two consequences carried into §6:
  1. A **real-time failure threshold defined up front**, per-step wall-clock
     logged from the first commit.
  2. **§8.3 must state the FGO is Python-bound while EKF3 is compiled C++**;
     the UKF is also Python (`filterpy`), so UKF-vs-FGO timing is like-for-like
     and only the EKF3 timing comparison carries the caveat.

---

## 1. Factor graph structure

### Variables, per keyframe *k*

| Key | Type | Meaning |
|---|---|---|
| `X(k)` | `gtsam.Pose3` | `R_world_body` (ENU ← FLU) and position of `base_link` in ENU |
| `V(k)` | `gtsam.Point3` (Vector3) | velocity of `base_link` in the **world** (ENU) frame |
| `B(k)` | `gtsam.imuBias.ConstantBias` | accel bias (m/s²) and gyro bias (rad/s), both **rates** |

World frame is ENU with Z up; body frame is FLU. `/imu/data_raw` is already
bridged FRD→FLU (`imu_bridge.py`), so no extra rotation enters preintegration.

### Factors

| Factor | Keys | Dim | Source |
|---|---|---|---|
| `CombinedImuFactor` | `X(k−1), V(k−1), X(k), V(k), B(k−1), B(k)` | 15 | GTSAM |
| `FlowFactor` (custom) | `X(k), V(k), B(k)` | 2 (see §9.3 re per-axis) | bespoke, §2 |
| `RangeFactor` (custom) | `X(k)` | 1 | bespoke, §3 |
| `PriorFactorPose3` / `PriorFactorPoint3` / `PriorFactorConstantBias` | `X(0), V(0), B(0)` | 6/3/6 | §8 |

`CombinedImuFactor` carries the bias random walk internally, so **no separate
`BetweenFactor<ConstantBias>`** — adding one would double-count
`biasAccCovariance`.

The graph is a chain. No landmarks, no loop closures, no between-pose factors
other than the IMU chain. Flow is a *velocity* measurement, so absolute
horizontal position is unobservable and drifts — exactly as for EKF3 and the
UKF. That is expected, not a defect.

### Keyframe strategy — measurement-triggered at the flow cadence (~30 Hz) `[SUPERSEDED — see §9.1]`

> **Superseded by the §9.1 decision:** keyframes are **IMU-clock-driven at a
> fixed cadence, not flow-triggered.** The flow-cadence prose below is retained
> for its measurement-attachment and midpoint-timing detail (still valid), but
> keyframe *timing* is now the IMU clock, and flow attaches to the nearest
> keyframe (§9.1). Read §9.1 first.

**One keyframe per `/optical_flow/measurement` message**, placed at the flow
interval **midpoint** `t_k − dt_k/2`, where `dt_k = t_k − t_{k−1}` from
consecutive message stamps. Those stamps are the image capture stamps
`flow_tracker.py` differences (`flow_tracker.py:214–219`), so `dt_k` is exactly
the interval the measurement averages over — no message change needed.

Midpoint placement mirrors EKF3, which back-dates the flow sample by
`flowTimeDeltaAvg_ms/2` (`AP_NavEKF3_Measurements.cpp:230–233`). Skipping it
biases the trajectory by `dt/2 ≈ 16.5 ms`, ~6.6 mm at 0.4 m/s cruise — small,
free to get right, and it shows up in RPE.

Why measurement-triggered and **not** motion-triggered:

- Motion-triggered keyframing is a visual-SLAM device for landmark parallax and
  suppressing redundant hover nodes. There are no landmarks here.
- A flow measurement can only be used if a state exists at its time. Decimating
  keyframes discards flow measurements EKF3 and the UKF both fuse — a
  sensor-input asymmetry, which the fairness principle forbids.
- Preintegration interval length is bounded by the keyframe rate; short
  intervals keep bias linearisation valid without needing `biasCorrectedDelta`
  re-integration.
- During hover the drone still needs range and flow fused to hold height and
  zero velocity; a motion gate would starve the quiet segments where drift
  accumulates.

> **Fallback if real-time fails.** *Shortening the fixed-lag window* is a
> legitimate knob; *lengthening the keyframe interval* is **not**, because it
> throws away measurements. The sanctioned decimation fallback keeps every flow
> measurement and attaches each to the **nearest** keyframe under a
> zero-order-hold on velocity (worst-case 50 ms hold at 10 Hz keyframes, ≲0.02
> m/s velocity change) — a documented *formulation* approximation, not a
> discarded sample.

> **Note:** the plan gated *keyframe creation* on flow validity. That is wrong
> and is decided in §9.1 — keyframes are created on the IMU clock regardless of
> whether flow arrives or is valid; only the flow *factor* is gated. §9.1 governs.

### Mapping onto the UKF's 15-state vector

| UKF state | FGO equivalent | Clean? |
|---|---|---|
| `p_E, p_N, p_U` | `X(k).translation()` | ✅ identical, both `base_link` in ENU |
| `v_E, v_N, v_U` | `V(k)` | ✅ identical, both world-frame ENU |
| `roll, pitch, yaw` | `X(k).rotation()` | ⚠️ same quantity, different chart — §7 |
| `gyro_bias` (rad, Δangle per 0.0125 s) | `B(k).gyroscope()` (rad/s) | ⚠️ unit conversion `rate = Δ/dt`, exact — §7 |
| `accel_bias` (m/s per step) | `B(k).accelerometer()` (m/s²) | ⚠️ same, `rate = Δ/dt` |

**Does not map cleanly — flag so they are not "fixed" later:**

1. **The FGO's estimate is a trajectory, not an instant.** The comparable
   quantity is the *newest* keyframe's marginal. Older keyframes keep being
   revised inside the window; those revisions must never reach `/fgo/pose` (§6).
2. **Covariance is not comparable term-by-term.** The UKF's 15×15 is in Euler
   coordinates; GTSAM's is in the `Pose3` right-tangent space (body-frame
   perturbation, ordering `[rotation; translation]`). NEES requires converting
   both into one common chart (§6).
3. **EKF3's `terrainState` has no FGO counterpart.** Under
   `EK3_SRC1_POSZ = RangeFinder` it is pinned at 0 (`core.cpp:253`,
   `PosVelFusion.cpp:1389`). The FGO takes the flat-floor assumption as a hard
   constant, not a state (§3).
4. **EKF3's separate `flowGyroBias`** (`Measurements.cpp:208–210`) is a
   flow-sensor-specific gyro bias distinct from its navigation gyro bias. The
   FGO has one gyro bias, `B(k).gyroscope()`, used by both the IMU and flow
   factors. Legitimate formulation difference; recorded.

---

## 2. The custom optical flow factor — the risk item

GTSAM ships IMU preintegration and range factors but nothing for optical flow.
This is the bespoke piece and the reason the design was done ahead of coding.

### Single source of truth

Both estimators import **one function** from a new shared module:

```
src/estimators/common/measurement_models.py
    h_flow(R_wb, v_world, p_U, omega_body_flu, bias_gyro) -> np.ndarray[2]
    h_range(R_wb, p_U)                                    -> float
    FLOW_LEVER_ARM_BODY = np.array([0.0, 0.0, -0.25])   # FLU, camera below CG
    RANGE_LEVER_ARM_M   = 0.12
    SIGN_X, SIGN_Y                                        # pinned empirically
```

The UKF calls it from its sigma-point measurement function; the FGO calls it
inside `CustomFactor.error`. Neither owns a private copy. This is the fairness
argument made structural.

> **Geometry reminder (§0):** the `−0.25` camera lever and the resulting
> `camera_height = p_U − 0.25` are the *base_link-referenced* form of EKF3's
> `lidar_range − 0.13`. `FLOW_POS_Z = 0.13` in the `.parm` is the
> camera-to-rangefinder offset, not the camera position. Do not "simplify"
> `p_U − 0.25` to use `0.13`.

### The model, derived from what is already validated

Given `X(k)`, `V(k)`, `B(k)` and the flow-interval-mean gyro `ω_meas` (FLU):

```
R      = X(k).rotation()                     # world←body
ω      = ω_meas − B(k).gyroscope()           # bias-corrected body rate, FLU
v_b    = Rᵀ · V(k)                           # world velocity into the body frame
v_s    = v_b + ω × r_cam                     # sensor-point velocity, r_cam = (0,0,−0.25) FLU
h_cam  = max(X(k).translation().z() − 0.25, H_MIN)      # = lidar_range − 0.13 (§0)
```

- `v_b = Rᵀ·V` is exactly EKF3's `relVelSensor = prevTnb * stateStruct.velocity`
  (`AP_NavEKF3_OptFlowFusion.cpp:331`), in FLU rather than FRD.
- `ω × r_cam` is exactly EKF3's `+ (ofDataDelayed.bodyRadXYZ % posOffsetBody)`
  on the same line — zero before commit `2f34efd`, non-zero now (§0).
- `h_cam` is the UKF's `h_cam(x) = p_U − 0.25`. `H_MIN` (0.10 m) mirrors EKF3's
  `MAX(..., rngOnGnd)` guards and keeps the division finite on the ground.

Body-FLU → camera-optical is the mapping `flow_tracker.py:226–232` already
validated: `(ω_x, ω_y, ω_z)_FLU → (ω_y, −ω_x, ω_z)_opt`. Being a rotation it
applies identically to `v_s`. Predicted angular flow in the camera optical
frame — the frame `flow_x_rad`/`flow_y_rad` are in:

```
translational:   ŷ_trans = ( S_x · (−v_s.y / h_cam),
                             S_y · (+v_s.x / h_cam) )

rotational:      ŷ_rot   = ( −ω.x,
                             −ω.y )        # flow_tracker.py's validated coefficients

prediction:      ŷ = ŷ_trans + ŷ_rot
error:           e = ŷ − (flow_x_rad, flow_y_rad)
```

This is the **raw**, non-derotated prediction compared against the raw sensor
values — the FGO derotates inside its own factor, per the Sensor Fusion
Architecture decision. The derotated `flow_x`/`flow_y` characterisation fields
are never read.

Structurally this is EKF3's own formulation: EKF3 forms
`flowRadXYcomp = flowRadXY + bodyRadXYZ` on the measurement side and predicts
`losPred = (v_s.y/range, −v_s.x/range)` on the state side. Adding the rotational
term to the *prediction* instead of subtracting it from the *measurement* is
algebraically the same residual, and it is the form that lets gyro bias enter as
a variable.

### The two sign constants — pin them, do not re-derive them

`CLAUDE.md` deliberately leaves the exact `f_x`/`f_y` axis sign to be pinned
empirically against the validated Stage A result ("vx → flow_y only");
`flow_bridge.py:26–39` records its mapping as best-derived, not confirmed.
`S_x, S_y ∈ {+1, −1}` are constants in the shared module, not free parameters.

Consistency check the model already passes: forward flight `v_b = (0.4, 0, 0)`
FLU gives `ŷ_trans = (0, +0.4/h)` — flow in **y only**, matching Stage A.

**Pinning costs no new flight.** `dump_flow.py` plus an existing forward-flight
bag gives `S_y` from the sign of `flow_y_rad` during steady cruise against
`/ground_truth/pose` velocity; a lateral segment (or the rotation-mapping
consistency argument) gives `S_x`. Do this **before** writing the factor, and
record both values and the bag in this file (§ Verification, step 1).

### Jacobians — numerical, via manifold retract

**Decision: numerical differentiation on the manifold.** Not Expressions, not
analytic.

- **Expressions are unavailable** through the Python bindings; choosing them
  means choosing C++, already rejected.
- **Analytic Jacobians are the wrong risk** — ~40 lines of error-prone algebra
  for a `Pose3` right-perturbation with `1/h_cam` scaling and an `ω × r` term,
  whose failure mode is silent slow convergence, and a second place the model
  lives.
- **Numerical differentiation keeps `h_flow` as the only definition.** The
  Jacobian is by construction the derivative of the function the UKF uses.

```python
def numeric_jacobian(f, values, key_types, eps=1e-6):
    # central differences; Pose3 via x.retract(δ), Vector3/ConstantBias via +δ
```

Central differences, not forward — forward-differencing a `1/h` term near the
ground is where truncation error bites.

**Compute cost, up front.** The flow factor touches 6 + 3 + 6 = 15 tangent
dims. Central differences = `2 × 15 = 30` evaluations of `h_flow` per
linearisation plus one for the error. `h_flow` is a handful of NumPy 3-vector
ops (~5–10 µs), so ~0.3 ms per flow-factor linearisation. With a 1 s window at
30 Hz (~30 flow factors) and iSAM2 relinearising only the affected subset:
order 1–10 ms of Python per update step. That is the number §6's threshold is
set against, and the number to log.

Cheaper variants recorded but **not** recommended: dropping `B(k)` (→18 evals,
rejected — estimating gyro bias is the point); forward differences (→15 evals,
rejected — halves accuracy for a saving not needed unless the threshold breaks).

### Noise model

`noiseModel.Isotropic.Sigma(2, 0.25)` — `EK3_FLOW_M_NSE` unchanged, per §4.
(But see §9.3: matching EKF3's per-axis gating favours **two 1-DOF factors**
with `Sigma(1, 0.25)` each, which is numerically identical for the isotropic
case.)

---

## 3. Range factor

Custom 1-D `CustomFactor` on `X(k)` alone.

```
h_range(X(k)) = X(k).translation().z() − 0.12
e             = h_range(X(k)) − range_meas
noise         = noiseModel.Isotropic.Sigma(1, 0.5)      # EK3_RNG_M_NSE
```

**Flat floor, ground at zero.** EKF3 under `EK3_SRC1_POSZ = RangeFinder`
computes `hgtMea = MAX(rng·prevTnb.c.z, rngOnGnd) − terrainState`
(`AP_NavEKF3_PosVelFusion.cpp:1416–1418`) with `terrainState` initialised to 0
(`core.cpp:253`) and not updated when the rangefinder is the height reference
(`OptFlowFusion.cpp:89–91` sets `inhibitGndState`). The FGO takes the identical
assumption as a hard constant. All trial worlds are flat.

**Tilt term deliberately omitted, magnitude stated.** EKF3 applies `·prevTnb.c.z`
(cos of tilt). The exact model would be `h_range = (p_U − 0.12)/cos(tilt)`,
trivially available from `X(k).rotation()`. Omitted so `h_range` stays literally
identical to the UKF's, and because at 5° cruise tilt and 2 m height it is 8 mm
against `RNG_M_NSE = 0.5 m` (1.6% of one sigma). One-line change in the shared
module if ever wanted; both estimators get it at once.

The `0.12` lever is matched to EKF3's height path now that `RNGFND1_POS_Z = 0.12`
is set (§0). It refers `p_U` to `base_link` for both estimators.

**Validity gate** mirrors `lidar_bridge.py:70`: finite, and
`min_range ≤ range ≤ max_range`. This rejects the 41.0 no-return sentinel. A
rejected range adds no factor — matching EKF3, starved identically.

Jacobian: the same numerical helper, 12 evaluations of a trivial function.

---

## 4. Gating and measurement quality

Match EKF3's live operating point exactly.

| Gate | Value | FGO implementation | EKF3 source |
|---|---|---|---|
| Flow quality | `inlier_ratio > 0` **and** `valid` | binary accept; no factor if rejected | `Measurements.cpp:203` |
| Flow `R` | `FLOW_M_NSE` 0.25 rad/s, fixed | `Isotropic.Sigma(2, 0.25)`, never scaled by quality | `AP_NavEKF3.cpp:41,321` |
| Range `R` | `RNG_M_NSE` 0.5 m, fixed | `Isotropic.Sigma(1, 0.5)` | `AP_NavEKF3.cpp:293` |
| Corrupt-data clamp | `‖raw_flow‖ < 4.2` **and** `‖raw_gyro‖ < 4.2` rad/s | reject the whole flow sample | `Measurements.cpp:203` |
| `FLOW_MAX` | 2.5 rad/s | one-sided, see below | `AP_NavEKF3.cpp:312`, `OptFlowFusion.cpp:668` |
| Flow NIS gate | `EK3_FLOW_I_GATE` 300 → `testRatio < 1` at 3σ | **per-axis**, see §9.3 | `OptFlowFusion.cpp:665–668` |
| Range NIS gate | `EK3_RNG_I_GATE` 500 → 5σ | same mechanism | `AP_NavEKF3.cpp:301` |

**No continuous R-scaling on `inlier_ratio`.** Above zero the exact quality
value is unused (`AP_OpticalFlow_MAV::update()`/`writeOptFlowMeas()`). Scaling
`R` would hand the FGO a defence the baseline lacks.

**The `FLOW_MAX` comparison is one-sided in EKF3, and that is not a typo.**
`OptFlowFusion.cpp:668` tests `flowRadXY.x < _maxFlowRate && …y < _maxFlowRate`
— a **signed** `<` on `flowRadXY = −rawFlowRates` (`Measurements.cpp:221`). So
the live gate is `−raw_x < 2.5 && −raw_y < 2.5`: large *negative* raw flow
passes, large *positive* raw flow is rejected. Replicate the asymmetry, quirk
and all — implement it literally with a comment pointing at line 668. An
`abs() < 2.5` "correction" would be a different operating point. (The separate
`MAX(flowRadXY[0], flowRadXY[1]) > _maxFlowRate` at line 87 governs
terrain-offset updating only and is inactive under
`EK3_SRC1_POSZ = RangeFinder`; do not replicate it.)

### The innovation gate — implement it, or the FGO is *less* defended

Neither factor has a natural innovation gate; the optimiser simply absorbs a bad
measurement. EKF3 and the UKF both reject on
`testRatio = ν² / ((0.01·GATE)²·S) > 1`. Omitting it would be an asymmetry in
the FGO's *disfavour*.

**Recommendation: matched NIS gate at factor-insertion time.**

```
A, b = factor.linearize(current_estimate)     # whitened Jacobian and residual
P    = <predictive covariance of the connected key>   # see §9.2 — NOT marginalCovariance on a new key
S    = A P Aᵀ + I                             # whitened, so R folds to identity
testRatio = bᵀ S⁻¹ b / (0.01·GATE)²
```

Identical formula, identical `GATE` values (300 flow, 500 range). Two
corrections vs the plan's first draft, both in §9:
- **§9.2** — for a brand-new keyframe the connected variables are not yet in the
  smoother, so `marginalCovariance(key)` is invalid at insertion time; use the
  IMU-preintegration predictive covariance instead.
- **§9.3** — EKF3 gates flow **per axis sequentially**, not as a joint 2-DOF
  test; the FGO gate must too.

Rejections are counted and logged per axis, exactly as Stage C reports EKF3's.

### Robust loss — **not in the headline comparison**

Huber/Cauchy are a genuine capability of the formulation (a smoother can
down-weight a measurement after seeing what came next; a filter cannot). This is
a *formulation* difference, not a sensor asymmetry — the same data reaches all
three estimators. But enabling it in the primary config confounds the thesis
question (a better ATE would have two explanations: the window or the kernel),
and layers a second outlier defence on top of a gate EKF3 also has.

- **Primary `fgo`: Gaussian noise models only**, matched gates, matched `R`.
  The ATE/RPE headline numbers come from here.
- **Secondary `fgo_huber`: identical but `noiseModel.Robust(Huber(k=1.345),
  base)` on the flow factor only.** `k = 1.345` is the standard
  95%-efficiency-under-Gaussian constant (stated so it is not read as tuning).
  Reported as an explicitly-labelled *FGO-only capability*, most interesting on
  `corridor_blank.sdf`-class data where `inlier_ratio` collapses to ~0.47 and
  the binary gate still passes samples through.

---

## 5. Preintegration parameters

`PreintegratedCombinedMeasurements` / `CombinedImuFactor`, on
`PreintegrationCombinedParams.MakeSharedU(9.81)`.

`MakeSharedU` sets `n_gravity = (0, 0, −9.81)` in a Z-up world and expects
specific-force accelerometer input, so a level stationary IMU reads `+9.81` on
body Z — exactly what `imu_bridge.py` publishes (verified `+9.811 m/s²` at rest,
`CLAUDE.md`). No sign fix anywhere.

```python
p = gtsam.PreintegrationCombinedParams.MakeSharedU(9.81)
p.setAccelerometerCovariance(np.eye(3) * 1.53125e-3)   # σ 0.03913119 m/s²/√Hz
p.setGyroscopeCovariance    (np.eye(3) * 2.8125e-6)    # σ 0.001677051 rad/s/√Hz
p.setBiasAccCovariance      (np.eye(3) * 5.0e-6)       # σ 0.002236068 m/s²/√s
p.setBiasOmegaCovariance    (np.eye(3) * 1.25e-8)      # σ 0.0001118034 rad/s/√s
p.setIntegrationCovariance  (np.eye(3) * 1e-8)         # see below
p.setBiasAccOmegaInit(np.diag([0.2**2]*3 + [0.043633**2]*3))   # see below
```

All four sensor covariances from `ca120e6` unchanged: `σ_c = NSE·√dt` at
`dt = 0.0125 s`, derived against `PreintegrationParams.h:27–29` and
`CombinedImuFactor.cpp:136–155`. The `k=2` form does not carry over because
EKF3's bias states are delta quantities while GTSAM's are rates, and that unit
conversion cancels the extra `dt²`.

**Every bridged sample at 333 Hz goes to `integrateMeasurement(accel, gyro,
dt)`. Never decimate to keyframe rate.** `dt` comes from consecutive
`/imu/data_raw` header stamps, not a nominal 3 ms. A decimating consumer
reintroduces the aliasing `ca120e6` fixed and breaks the `σ_c = NSE·√dt`
derivation. The instantaneous-sample rectangular-integration approximation the
bridge documents is identical for the UKF, so it is not an asymmetry.

### `integrationCovariance` — 1e-8

No EKF3 counterpart (EKF3 propagates position and velocity in one step). A
**numerical conditioning floor, not a matched sensor parameter** — its referent
is rectangular-vs-trapezoidal integration error at 333 Hz. Order of magnitude:
dominant residual accel ~0.018 m/s² RMS near 35 Hz → per-step position error
~6e-8 m → variance ~4e-15, four orders below the conventional `1e-8·dt = 3e-11`,
i.e. conservative — the right side to err on for a positive-definiteness floor.
Document as unmatched-by-construction and **verify insensitivity with a ±100×
sweep** on one bag; if ATE moves, the term is doing modelling work it should not.

### `biasAccOmegaInit` — matched, not invented

`CombinedImuFactor` needs the initial-bias covariance used during
preintegration. Take EKF3's own initial bias uncertainties, converted from delta
to rate form by dividing by `dtEkfAvg` (cancels exactly):

| | EKF3 | Source | GTSAM rate form |
|---|---|---|---|
| gyro bias 1σ | 2.5 deg/s × `dtEkfAvg` | `GyroBias.cpp:20–23`, `core.cpp:595` | **0.043633 rad/s** |
| accel bias 1σ | `ACCEL_BIAS_LIM_SCALER`(0.2) × `EK3_ACC_BIAS_LIM`(1.0) × `dtEkfAvg` | `core.h:55`, `AP_NavEKF3.cpp:541`, `core.cpp:599` | **0.2 m/s²** |

The same two values become the `PriorFactorConstantBias` sigmas on `B(0)` (§8).
Derived from EKF3 source, not chosen.

---

## 6. Fixed-lag window, marginalisation, solver

### Solver: `BatchFixedLagSmoother` (incremental is UNUSABLE — GTSAM limitation)

> **⚠️ CORRECTION 2026-08-01 — `IncrementalFixedLagSmoother` cannot be used here.**
> The plan intended iSAM2-backed incremental as the primary (fast) solver. **It
> cascades unrecoverably** whenever a Python flow `CustomFactor` is in the graph:
> `IndexError: variable 'x…' not in this VectorValues` at the first lag-boundary
> marginalisation (~keyframe 589 at a 1.0 s lag), after which every step fails.
> Diagnosed four ways: (a) removing the flow factor (IMU+range+yaw only) runs all
> 10047 keyframes cleanly → the flow `CustomFactor` is the trigger; (b) `update()`
> succeeds, only `calculateEstimate()`/typed single-key accessors throw → the
> marginalisation corrupts the iSAM2 delta; (c) ISAM2Params (QR factorisation,
> `cacheLinearizedFactors=False`, `findUnusedFactorSlots`), typed accessors, and
> disabling relinearisation **all fail identically**; (d) `BatchFixedLagSmoother`
> re-solves rather than marginalising and handles the same factors fine. It is a
> GTSAM `marginalizeLeaves`-vs-Python-`CustomFactor` limitation, not our logic.
>
> **Primary solver is therefore `BatchFixedLagSmoother`**, made affordable by (i)
> capping LM to 2 warm-started iterations (each step is near-converged; ATE
> unchanged, but timing barely moved — the cost is GTSAM's re-solve/marginalise
> machinery, not the LM iterations) and (ii) the **window length**, which sets the
> factor count per re-solve and dominates the step time (see below). Incremental is
> kept behind `solver="incremental"` only for the flow-free correctness cross-check.

### Window length — the primary cost knob; the sweep is a real result

~30 keyframes at 1.0 s / 30 Hz. With no loop closure the window buys smoothing of
IMU bias and attitude against flow/range history and nothing else; its value
saturates once it spans several bias-correlation times. Accel bias is observable
only through attitude coupling and the flow/range constraints, both sub-second at
this envelope.

**Measured (`dsn_tex_r1`, batch):** the ATE is nearly window-independent — evo `-a`
**5.10 m at 1.0 s, 5.07 m at 0.5 s** — confirming the saturation above, so the window
is chosen for *cost*, not accuracy. Batch step-time scales ~O(window): **median 96 /
48 / ~29 ms at 1.0 / 0.5 / 0.25 s**. The 33 ms deployability budget is met only at
≈0.25 s; a 1.0 s window is neither deployable nor affordable (2.4 h per 9-bag run) for
a Python-bound `CustomFactor` FGO. **The 9-bag comparison therefore runs at a shorter
window (0.5 s ≈ 1.2 h, or 0.25 s ≈ 44 min, both under-budget-or-close), with the full
`{0.25,0.5,1.0,2.0,4.0}` s sweep on one bag as the §8.3 cost/accuracy result.**

Sweep `{0.25, 0.5, 1.0, 2.0, 4.0}` s on one bag and report the curve in §8.3
(FGO-specific — the filters have no equivalent knob). Expected shape: ATE
improving then flattening, cost growing roughly linearly.

### Real-time threshold — defined now, logged from the first commit

Keyframe interval = 33 ms of **sim** time.

| Criterion | Budget | Meaning |
|---|---|---|
| **Deployability (binding)** | **33 ms** | what a real drone at RTF 1.0 requires ("deployable unchanged") |
| Bag-replay viability | ≈ 38 ms at RTF 0.86 | what the sim needs to keep up |

**Pass = median < 33 ms AND p99 < 33 ms. Fail = p99 > 33 ms sustained.** On
failure, ordered responses: (1) shorten the fixed-lag window; (2) drop the flow
factor's `B(k)` dependency (30 → 18 evaluations); (3) nearest-keyframe ZOH
decimation of §1 — never plain measurement dropping.

Log per update step to CSV alongside the bag: `wall_ns_total`,
`wall_ns_python_callbacks`, `n_factors_relinearised`, `n_keyframes_in_window`.
Splitting out the Python callback time makes §8.3's caveat quantitative.

### Output — causal only

`smoother.calculateEstimate()` returns the whole window; **publish only the
newest keyframe's `X(k)`.** Republishing revised older keyframes puts future
measurements into a past estimate — a non-causal advantage no filter has, and
the one way this design could quietly cheat.

- `/fgo/pose` — `PoseWithCovarianceStamped`, `frame_id = "world"` (matching
  `ground_truth_pub.py:74`; note `ekf_bridge.py:127` uses `"map"`, an existing
  inconsistency worth aligning), stamped with the keyframe's sim time
  (`t_k − dt_k/2`). Published after every smoother update, ~30 Hz.
- `/fgo/pose_smoothed` — optional, the full revised window, for a
  clearly-labelled "what smoothing recovers offline" figure. **Never** used for
  the headline ATE.

Covariance from `smoother.marginalCovariance(X(k))`, with two conversions easy
to get silently wrong:

1. **Ordering.** GTSAM `Pose3` tangent is `[rx, ry, rz, x, y, z]`; ROS
   `PoseWithCovariance` is `[x, y, z, rx, ry, rz]`. Permute.
2. **Frame.** GTSAM is a right (body-frame) perturbation; ROS expects the fixed
   frame. Transform with the adjoint: `Σ_world = Ad(X) Σ_body Ad(X)ᵀ`.

The same conversion makes the NEES check against `/ground_truth/pose` comparable
to the UKF's (Euler coordinates). Put it in the shared module so both NEES
computations use one function.

---

## 7. Where UKF and FGO legitimately differ

Documented so they are not "fixed" into an inconsistency later.

### Legitimate formulation differences — keep these

| # | Difference | Why it is fine |
|---|---|---|
| 1 | `Pose3` / proper SO(3) vs UKF Euler attitude | Different chart, same manifold. Affects covariance comparison (§6), not information content. |
| 2 | GTSAM bias states are **rates**; EKF3/UKF biases are **deltas** | Exact conversion `rate = Δ/dt`; `ca120e6` shows the extra `dt²` cancels. |
| 3 | IMU **preintegration** vs per-sample propagation | Both consume every 333 Hz sample; algebraic reorganisation, not data reduction. |
| 4 | Fixed-lag **smoothing** vs single-instant filtering | This *is* the thesis variable. |
| 5 | Rotational flow added to **prediction** vs subtracted from **measurement** | Algebraically identical residual; the FGO form lets gyro bias be a variable. |
| 6 | Innovation gate via predictive covariance + factor Jacobian rather than explicit `S = HPHᵀ + R` | Same formula, same gate values, different route to `S` (§9.2). |
| 7 | Keyframe at flow **interval midpoint** | Matches EKF3 back-dating; the UKF's ZOH catch-up predict is the filter-side equivalent. |
| 8 | One gyro bias vs EKF3's separate `flowGyroBias` | EKF3's sensor-specific extra state folds into `B(k)`. |
| 9 | Tilt term omitted from `h_range`, flat floor constant | Same simplification in both; bounded at 8 mm (§3). |
| 10 | Numerical Jacobians in Python; `integrationCovariance = 1e-8` | Implementation/conditioning choices with no baseline counterpart; both bounded and swept. |
| 11 | Robust loss (`fgo_huber` only) | Real capability; reported as a separate labelled configuration (§4). |

### Would-be asymmetries — none of these may happen

| # | Asymmetry | Why forbidden |
|---|---|---|
| A | Decimating keyframes so flow/range go unused | Sensor-input difference; use the ZOH fallback (§1). |
| B | Different `R`, or scaling `R` by `inlier_ratio` | EKF3 uses fixed `R` above a binary gate. |
| C | Different accept gates, or "correcting" the one-sided `FLOW_MAX` | Changes the operating point (§4). |
| D | Consuming derotated `flow_x`/`flow_y` instead of raw | Pre-processing asymmetry; violates Sensor Fusion Architecture. |
| E | Lever arms modelled in one estimator only | The §0 `.parm` fix (commit `2f34efd`) closes this. |
| F | Any use of ground truth for init, alignment or gating | None of the three may see `/ground_truth/pose`. |
| G | Publishing the retro-smoothed window as `/fgo/pose` | Non-causal (§6). |
| H | A different IMU rate or any decimation of `/imu/data_raw` | Breaks `σ_c = NSE·√dt` and input parity. |
| I | Robust loss in the primary configuration | Extra outlier defence the baseline lacks (§4). |

---

## 8. Multi-rate handling and initialisation

### Rates

| Stream | Sim-time rate | Role |
|---|---|---|
| `/imu/data_raw` | 333 Hz | every sample into `integrateMeasurement`; never triggers a keyframe |
| `/optical_flow/measurement` | ~30 Hz | **defines** keyframes at `t_k − dt_k/2` |
| `/downward_lidar/range` | ~30 Hz (33.00 ms spacing) | attached to the nearest existing keyframe |

Event-driven throughout, no fixed-rate loop — same architecture as the UKF, and
the reason the node runs unchanged on hardware.

**Range-to-keyframe association.** Attach each valid range sample to the nearest
keyframe within ±16.5 ms. Vertical velocity ≲0.1 m/s → ≤1.7 mm against
`RNG_M_NSE = 0.5 m`, negligible, and avoids doubling the keyframe count. If two
range samples map to one keyframe (jitter), keep the temporally nearest and
count the drop.

**Update sequence per keyframe** — driven by the IMU-clock cadence (§9.1), not
per flow message:

1. **Create the keyframe** on the fixed IMU-clock tick (§9.1), independent of
   whether flow or range arrived this interval.
2. `pim.integrateMeasurement(...)` for every buffered IMU sample up to the new
   keyframe time. If the IMU gap > 0.2 s, skip the keyframe and warn (below).
3. Predict `X(k), V(k), B(k)` via `pim.predict(NavState(X(k−1), V(k−1)),
   B(k−1))` as the initial value.
4. Always build `CombinedImuFactor`. Attach a `RangeFactor` if a range
   associates to this keyframe, and a `FlowFactor` if a valid flow sample
   associates (§4 gates) — each measurement to its nearest keyframe (§9.1). A
   missing or invalid measurement simply contributes no factor this step.
5. NIS-gate each measurement factor before insertion using the **predictive**
   covariance (§9.2), **per axis** for flow (§9.3); drop and count on failure.
6. `smoother.update(newFactors, newValues, newTimestamps)`; timestamp = keyframe
   sim time (drives marginalisation).
7. Publish `/fgo/pose` from `X(k)` and its marginal.
8. `pim.resetIntegrationAndSetBias(B(k))` using the newly optimised bias.

### Initialisation

1. **Wait for the first `/imu/data_raw` sample.** Nothing exists before it.
2. **Gravity levelling** over the first 0.5 s (~167 samples): `roll0`/`pitch0`
   from `atan2` against mean sensed `g`, exactly the UKF's method. `yaw0 = 0`
   (unobservable without a compass; `evo -a` absorbs a fixed offset).
3. **Height** from the first valid range in that window: `p_U0 = range + 0.12`.
   Not `(0,0,0)`. If no valid range within 2 s of the first IMU sample, log an
   error and keep waiting; do **not** fall back to an assumed height (that is
   the `corridor_blank.sdf` failure mode, Known Issue #12).
4. **Insert `X(0), V(0), B(0)`** at the first flow-interval midpoint at or after
   levelling completes, with priors:

| Prior | 1σ | Justification |
|---|---|---|
| `x, y` | 1e-3 m | **gauge fix** — horizontal position unobservable from flow+range; graph rank-deficient without it |
| `z` | 0.5 m | `RNG_M_NSE`, since `z` is from one range sample |
| `roll, pitch` | **5°** (was a fixed 2° in code, never the measured scatter planned here) | **the UKF's value** (`ukf_core.init_state`); D18 correction 2026-10-10, initial-uncertainty audit (`docs/handovers/2026-10-10_initial_sigma_audit.md`) |
| `yaw` | **1°** (was 1e-3 rad) | **the UKF's value**; user ruling 2026-10-10 (METHODOLOGY "RULINGS (user, 2026-10-10): FGO initial yaw sigma"). 1e-3 rad was a "gauge fix" that became a substantive heading claim once the forward camera observes heading. EKF3's `CovarianceInit` is 0.1 rad per axis |
| `V(0)` | 0.1 m/s about zero | stationary pre-arm; confirm from the bag |
| `B(0)` | accel 0.2 m/s², gyro 0.043633 rad/s about **zero** | EKF3's own initial bias uncertainties (§5); zero mean matches EKF3 |

### The ~2.35 s late start of `/imu/data_raw`

No readiness gate; `ca120e6` warns "do not assume a shared start instant."

- Flow/range messages arriving **before the first IMU sample** are buffered then
  **discarded** at init, with the count logged (expect ~70 of each over 2.35 s).
  No state to attach them to; drone on the ground pre-arm, nothing lost.
- **The UKF has the identical constraint** (its predict is IMU-driven), so this
  is symmetric — provided both estimators discard the same samples. Record the
  discarded count for each estimator every trial and check they match; a
  mismatch is a real bug.
- **EKF3 is unaffected** — its own onboard IMU, never saw `/imu/data_raw`. State
  it in the methodology.

**Robustness rules the node must implement regardless** (these make it
deployable unchanged):

- Never create a keyframe with zero IMU samples since the previous one.
- Reject any measurement stamped at or before the last keyframe time
  (out-of-order delivery under bag replay).
- If the IMU gap exceeds 0.2 s, log a warning and skip the keyframe rather than
  preintegrating across a hole.
- Guard `h_cam` and `h_range` against non-positive heights (`H_MIN = 0.10 m`).

---

## 9. Resolved design decisions

§9.1–9.5 are all **decided** (user sign-off; §9.5 ruled 2026-07-30). Each
is a concrete correction to the plan's first draft; the EKF3 behaviour each
matches/documents is source-verified. Where a decision conflicts with the earlier
§1/§8 prose, **it governs** (cross-referenced inline). §9.4–9.5 were added during
UKF bring-up, where the corresponding EKF3 behaviour was exercised on real data.

### 9.1 Keyframe cadence — IMU-clock-driven, independent of flow `[DECIDED]`

**Decision.** Keyframes are created on a **fixed cadence driven by the IMU
clock**, independent of flow entirely. Every measurement — flow, range, anything
else — attaches as a factor to whichever keyframe is current at its timestamp; a
measurement's absence at a given step simply means no factor is added that step.
Keyframe *creation* is never triggered by, or gated on, any measurement. This
supersedes §1's "measurement-triggered at the flow cadence" and subsumes the
earlier partial fix (decouple keyframe creation from flow *validity*): keyframes
are now decoupled from flow *arrival* as well.

**Why.**

- **Matches EKF3.** EKF3 advances its state on the IMU every step regardless of
  whether flow arrives (`FuseOptFlow` is one optional fusion path gated by
  `rawFlowQuality > 0`, `Measurements.cpp:203`); flow and range only correct an
  already-advancing state. IMU-clock keyframes make the FGO's graph advance the
  same way — on the IMU chain, always.
- **Prevents a fabricated "FGO diverges under degradation."** Under
  `corridor_blank` (inlier_ratio collapse) or any flow outage, flow-triggered
  keyframing stops creating nodes: the smoother stalls and `/fgo/pose` freezes.
  The trajectory error that follows would be misread as the *smoother* failing
  under degraded sensing when the truth is the *graph stopped advancing* — a
  result attributable to the harness, not the estimator. IMU-clock keyframes keep
  the graph advancing on IMU + range through the entire outage, so what is
  measured is the estimator's real behaviour.
- **Bounds the preintegration interval by construction.** A fixed cadence caps
  every preintegration interval at the keyframe period, so the short-interval
  bias-linearisation argument holds unconditionally — no longer contingent on
  flow arriving.
- **Closes the old §9.1 open question.** "What triggers a keyframe if flow stops
  entirely?" is moot: nothing about a keyframe depends on flow.

**Cadence and attachment.** Fixed period matched to the ~30 Hz measurement rate
(≈ every 11 IMU samples at 333 Hz), so flow/range attach to the nearest keyframe
with ≤ half-period time offset. Flow-to-keyframe association is the
nearest-keyframe zero-order-hold that §1 previously listed only as a real-time
*fallback* — it is now the **standard** mechanism, since keyframe times no longer
coincide with flow stamps. EKF3's flow-midpoint back-dating (old §1) is preserved
as a per-sample timestamp correction applied when associating a flow measurement
to its keyframe, not as a keyframe-placement rule.

**Still true from the earlier fix.** Only the flow *factor* is gated on flow
validity (§4); on an invalid or missing flow sample the keyframe is still created
and still carries its `CombinedImuFactor` and any associated `RangeFactor`.

### 9.2 NIS-gate ordering hole — `marginalCovariance` before the variable is in the graph

**The hole.** The plan computes the innovation covariance from
`P = smoother.marginalCovariance(key)` and gates *before* the factor joins the
graph. For a **newly created** keyframe, `X(k)`, `V(k)`, `B(k)` are not yet in
the smoother — they are only added by `smoother.update(...)`. Calling
`marginalCovariance(X(k))` on a key the Bayes tree does not contain is invalid
(no marginal exists yet). So the gate as written cannot run at insertion time
for the new keyframe's own variables — the common case, since flow and range
both attach to the newest keyframe.

**What the correct quantity is** `[VERIFIED against EKF3 semantics]`. EKF3's
innovation test uses the **a-priori** (predicted) covariance `S = HPHᵀ + R`,
where `P` is the state covariance *before* fusing this measurement. The GTSAM
equivalent is the **predictive** covariance of `X(k), V(k), B(k)` from the IMU
preintegration — `pim.predict(...)` propagates the NavState and
`PreintegratedCombinedMeasurements` carries `preintMeasCov`, giving exactly the
a-priori covariance of the new keyframe before any flow/range factor is added.

**Decision `[DECIDED]`.** Build `S` from the IMU-preintegration predictive
covariance of the connected variables, not from `marginalCovariance` on a
not-yet-inserted key. This both fixes the ordering hole *and* matches EKF3's
a-priori-`P` innovation test more faithfully than a marginal-after-insertion
would. For factors that touch **only already-marginalised keyframes** (the ZOH
fallback in §1), `marginalCovariance` is valid and can be used. Alternative
considered and rejected: a two-phase update (insert IMU + variables, query
marginal, then add gated measurement factors in a second `update`) — doubles the
solver calls per step for no accuracy gain.

### 9.3 Per-axis flow gating — match EKF3's sequential 1-DOF tests

**The mismatch.** The plan's NIS gate is a joint 2-DOF Mahalanobis test,
`testRatio = bᵀ S⁻¹ b / (0.01·GATE)²` on the 2-vector flow residual. EKF3 does
**not** do a joint test.

**What EKF3 does** `[VERIFIED]` — `AP_NavEKF3_OptFlowFusion.cpp`:

- `:65` "Fuse the optical flow X and Y axis data into the main filter
  **sequentially**";
- `:328` `for (obsIndex = 0; obsIndex <= 1; obsIndex++)` — "Fuse X and Y axis
  measurements **sequentially** assuming observation errors are uncorrelated";
- `:665` `flowTestRatio[obsIndex] = sq(flowInnov[obsIndex]) / (sq(0.01·gate) ·
  flowVarInnov[obsIndex])` — an independent **scalar** ratio per axis;
- `:668` the gate `flowTestRatio[obsIndex] < 1.0` is applied **per axis**;
- `:713` the state is updated after axis 0, so axis 1 is gated against the
  post-X-update state; `:722` "record bad axis" tracks each axis independently.

So EKF3 can **accept one axis while rejecting the other**. A joint 2-DOF gate
would reject *both* axes whenever one is bad, discarding good data — an
asymmetry in the FGO's disfavour (would-be asymmetry C, §7).

**Decision `[DECIDED]`.** Gate each flow axis independently with a scalar
test, `testRatio_i = ν_i² / ((0.01·GATE)²·S_ii) > 1 → reject axis i`, and let
each axis's contribution be dropped independently. Cleanest implementation:
**two 1-DOF `FlowFactor`s** (one per optical-frame axis), each with
`noiseModel.Isotropic.Sigma(1, 0.25)` — numerically identical to the single
2-DOF `Sigma(2, 0.25)` for the isotropic case, but individually gate-able. This
supersedes the §2 "one 2-DOF factor" sketch; keep `h_flow` returning the
2-vector and have each 1-DOF factor select its row.

**Not fully replicable, and say so.** EKF3 re-solves the whole state between
axis 0 and axis 1 (`:713`); a smoother fuses both jointly in one optimisation
step. The FGO cannot reproduce the *intermediate* single-axis state update. What
it can and must match is the **per-axis accept/reject decision** and the scalar
gate value. Record this as a bounded, documented formulation difference (it is
difference #6 in §7, refined), not a silent divergence.

---

### 9.4 Yaw variance cap — zero-innovation pseudo-yaw `[DECIDED]`

**Decision (fairness, not a fix).** Yaw is unobservable from IMU + flow + range,
so its variance grows unbounded and the flow update can rotate it freely. The UKF
caps this with a **zero-innovation yaw pseudo-measurement** (R = `EK3_YAW_M_NSE`²
= 0.5 rad², ~7 Hz), matching EKF3's `fuseEulerYaw(PREDICTED)`
(`AP_NavEKF3_MagFusion.cpp:275-277`: *"prevent uncontrolled yaw variance growth …
by fusing a zero innovation"*; noise `AP_NavEKF3.cpp:446`). Without it the UKF yaw
drifted **~50 deg/min** (measured, ds_tex_r1) vs EKF3's ~5 deg/min — a difference
by *omission*, not formulation.

**The FGO must match this.** Attach a **weak yaw-prior factor** to each keyframe's
`Pose3` rotation — a soft anchor on the yaw DOF with the same 0.5 rad sigma — so
the smoother's yaw marginal is bounded and does not free-drift. Equivalent to the
UKF pseudo-yaw and EKF3's PREDICTED yaw; without it the FGO's yaw would be better-
or worse-controlled than the baselines by implementation accident.

> **⚠️ IMPLEMENTATION CORRECTION (2026-07-30) — "anchor" must be to the PREDICTED
> yaw, not a fixed value.** The first build read "soft anchor on the yaw DOF"
> literally and anchored each keyframe's yaw to a *fixed* reference (yaw→0). Repeated
> per keyframe that accumulates into a ~5° effective **absolute heading anchor** —
> stronger than, and mechanically different from, a zero-innovation cap: it injects
> absolute heading the baselines do not have. It pinned yaw (drift −0.04 deg/min) and
> produced a **VOID** 0.49 m ATE. **Fix (in `fgo_core.py`):** anchor to each
> keyframe's IMU-**predicted** yaw (`Xk.rotation().yaw()`), so the error is ~0 at the
> linearisation point — a genuine zero-innovation cap matching EKF3's
> `fuseEulerYaw(PREDICTED)`: `innovYaw = 0.0f` (`AP_NavEKF3_MagFusion.cpp:1062-1064`)
> against `yawAngPredicted` = current state yaw (`:970`). With the fix the FGO yaw
> drifts −9.24 deg/min (near physical 9.8, like EKF3 8.4 / UKF 12.7).
>
> **And a result this exposed:** a controlled single-`flow_x`-residual test shows the
> Euler-UKF and SO(3)-FGO partition **identically** (69% velocity / 31% yaw), so the
> yaw leak under an unobservable heading is **independent of the attitude
> parameterisation and of filtering-vs-smoothing — controlled only by the yaw-capping
> frequency**. This refuted an earlier ~70–75%-confidence "Euler-vs-SO(3) formulation
> difference" attribution. Full write-up in METHODOLOGY.md "FINDING".

> **⚠️ IMPLEMENTATION CORRECTION (2026-10-09, user ruling: METHODOLOGY "MODEL AUDIT RESULT … RULINGS"
> item 2) — the cap is now VARIANCE-GATED, as EKF3's and the UKF's.** The model audit found that the cap
> was added at EVERY keyframe (30 Hz, ungated). In free inertial over 60 s that held the FGO's yaw variance at ×0.37
> of EKF3's and the UKF's. The "each keyframe" wording above is superseded. Both cores (`fgo_core.py`,
> `fgo_core.cpp`) now:
> - check every 140 ms (`YAW_DT`: the first keyframe with t − t_check ≥ 0.14 s; t_check starts at init and is
>   reset at every check, as `ukf_replay.py`). With 1/30 s keyframes that is every 5th keyframe (167 ms; EKF3 and
>   the UKF check every ~150 ms);
> - add the 0.5 rad zero-innovation cap only if the trace of THIS keyframe's PREDICTED attitude covariance exceeds
>   0.04 rad² (`ATT_VAR_GATE`: EKF3's quaternion-trace gate 0.01, `MagFusion.cpp:274`, mapped as in `ukf_core`).
> - "Predicted" = the gate-only filtering recursion (the previous keyframe's covariance + this keyframe's IMU
>   factor, before range, flow and forward factors). It runs whenever the cap is active, independently of
>   `log_cov`. Its newest-keyframe covariance equals the smoother's filtering marginal (checked against
>   `gtsam.Marginals` in free inertial). onGround / AID_NONE are ignored, as in the UKF.
> Handover: `docs/handovers/2026-10-09_fgo_yawcap_gate.md`.

### 9.5 Behaviour when flow aiding is lost — `[DECIDED — do NOT replicate const_pos]`

**The question.** When flow is gated out (e.g. `corridor_blank`, where the NIS
gate rejected ~87% of flow — measured on the UKF), what happens to horizontal
position?

**What EKF3 does** `[VERIFIED, file:line]`. After flow fusion times out (flow
rejected > 5000 ms) it transitions `AID_RELATIVE → AID_NONE`
(`AP_NavEKF3_Control.cpp:304-315`, the `flowFusionTimeout` branch at `:313-314`;
also entered on critical attitude-data loss, `:392-393`). In `AID_NONE` it
**fuses a synthetic constant-position + zero-velocity measurement** to constrain
tilt (`:414-417`) and **freezes** the reported horizontal position at the value
captured when aiding was lost — `lastKnownPositionNE = stateStruct.position`
(`:424-425`), reported as `lastKnownPositionNE + posOffsetNED`
(`AP_NavEKF3_Outputs.cpp:369-370`; the EKF position states themselves sit at the
origin in this mode, `Outputs.cpp:259-267`). `status.flags.const_pos_mode`
(`Control.cpp:808`) flags it. Measured: EKF3 held ~1.5 m over a 145 m blank flight;
on the nomag `dsn_blank` batch its `XKF1` PN froze near the origin (final PN ≈ −5 m
against 151 m travelled).

**What the UKF and FGO do.** The UKF dead-reckons on IMU + range through the outage
(measured on `dsn_blank`: PN diverged to ≈ −270 m). The FGO under §9.1 advances
keyframes on the IMU clock and adds no flow factor when flow is gated, so it
**dead-reckons on IMU + range** likewise. A factor graph has **no natural const_pos
analogue** — freezing a smoother's position mid-window is not a graph operation.

**Ruling (user, 2026-07-30): do NOT replicate `const_pos` in the UKF or the FGO.**
What an estimator does when aiding is lost is a **legitimate formulation
difference**, not a sensor-input asymmetry — the same (gated) data reaches all
three. Replicating EKF3's `AID_NONE` state machine in the other two would make them
**EKF3 imitations rather than genuine alternatives**, defeating the comparison.
EKF3 freezes (const_pos); the UKF and FGO dead-reckon on IMU + range. This is a
**characterised distinction**, documented here with EKF3's exact mechanism
(file:line above) so it does not read as an oversight, and it is a headline axis of
the degraded-sensing (`corridor_blank`, transition) results — how each formulation
behaves once its only horizontal aiding is gone. `[DECIDED]`, §9.5 closed.

## Files this creates

| Path | Contents |
|---|---|
| `FGO_DESIGN.md` | this design record (**created**) |
| `src/estimators/common/measurement_models.py` | shared `h_flow`, `h_range`, lever arms, pinned signs, covariance conversion — imported by **both** UKF and FGO |
| `src/estimators/fgo/flow_factor.py` | `CustomFactor` wrapper(s) + shared numerical-Jacobian helper (two 1-DOF factors, §9.3) |
| `src/estimators/fgo/range_factor.py` | `CustomFactor` wrapper |
| `src/estimators/fgo/fgo_node.py` | the ROS2 node |

Lever-arm `.parm` work (`FLOW_POS_*`, `RNGFND1_POS_*`) is **done** — commit
`2f34efd`, §0. Nothing further is handed to the world session.

---

## Verification

Ordered so each step can fail for one reason only. Mirrors the UKF's Stages
A/B/C.

1. **Pin `S_x`, `S_y`** — `dump_flow.py` on an existing forward-flight bag
   against `/ground_truth/pose` velocity. No new flight. Record values + bag
   here. *Before writing the factor.*
2. **Factor unit tests, no ROS.** `h_flow` against hand cases (pure forward →
   y-flow only; pure roll → x only; hover → zero). Numerical Jacobians
   cross-checked against `gtsam.numericalDerivative` where a matching
   instantiation is wrapped, and against a finite-difference of the whole factor
   error otherwise.
3. **IMU-only dead reckoning.** One bag's `/imu/data_raw` through preintegration,
   no flow/range; confirm smooth drift, not seconds-to-diverge. Isolates gravity
   sign, frame convention, noise constants.
4. **Plumbing scaffold** on an existing bag — no divergence, no crashes,
   `/fgo/pose` at ~30 Hz with sim-time stamps at the flow midpoints. Not a
   result.
5. **Solver cross-check.** `--solver batch` vs `--solver incremental` agree to
   numerical tolerance. The real correctness test on the custom factors.
6. **Flow-only sanity.** Commanded 0.4 m/s cruise converges `v_body_x ≈ 0.4`.
7. **Timing.** Per-step wall-clock CSV from step 4 on; median and p99 vs 33 ms.
   Report the Python-callback fraction separately.
8. **Window sweep** `{0.25, 0.5, 1.0, 2.0, 4.0}` s — ATE and wall-clock, §8.3.
9. **`integrationCovariance` insensitivity** — ±100× on one bag; ATE must not
   move.
10. **Nominal ATE/RPE** via `evo_ape`/`evo_rpe` against `/ground_truth/pose`,
    beside EKF3 and the UKF on the same bags.
11. **NEES consistency** from the logged covariance, using the shared
    ordering/adjoint conversion.
12. **`fgo_huber`** as a separate labelled run, reported apart from the headline.

### Gating checks specific to §9 (add to the above)

- **§9.1** — on a `corridor_blank`-class bag confirm keyframes and `/fgo/pose`
  continue through the `inlier_ratio` collapse (range + IMU still fused); assert
  the flow-factor count drops while the keyframe count does not.
- **§9.2** — assert the node never calls `marginalCovariance` on a key absent
  from the smoother; unit-test the predictive-covariance `S` against a
  hand-computed `HPHᵀ + R` on a toy graph.
- **§9.3** — feed a single-axis flow glitch and confirm exactly one axis is
  rejected while the other fuses, matching EKF3's per-axis `flowTestRatio`.
