# FGO gate count: a read-only diagnostic (stage 1: design, instrumentation, plan)

Status: DRAFT, stage 1 only. No estimator code changed, no thesis result changed, no committed
estimator file edited. Scope per the 2026-11-11 brief and the user's verbatim approval:

> "Gating: read-only count of stored FGO runs (flow NIS 9 per axis and 2-axis, range NIS 25,
> flow > 2.5 rad/s), reported both ways for FLOW_MAX sidedness. No implementation."

This is a diagnostic only. It counts how many of the flow/range factors the FGO actually used
(the ones already added to the graph by `fgo_core.py`'s unmodified `keyframe()`) would have
failed an EKF3-style gate, had that gate been implemented. It changes no estimator and no
stored result. "No FGO core gates flow/range today" is confirmed: `fgo_core.py` (keyframe(),
around line 180 to 185) and `fgo_cpp/src/fgo_core.cpp` (around line 140 to 147) only clamp
`abs(flow) < 4.2` per axis before adding a flow factor, and check the range is in
`[r_lo, r_hi]` before adding a range factor. There is no NIS test and no FLOW_MAX test anywhere
in either core.

## 1. What is being counted, and why read-only

For each flow and range factor the FGO actually added to a stored run's graph, this diagnostic
asks four independent, purely retrospective questions of that one factor:

1. Would EKF3's per-axis NIS gate (flow) have rejected it?
2. Would EKF3's NIS gate (range/height) have rejected it?
3. Would EKF3's FLOW_MAX one-sided rule have rejected it (and therefore the whole flow factor,
   both axes, see Section 5.2 of FGO_DESIGN.md and Section 3 below)?
4. Would the UKF's FLOW_MAX two-sided rule have rejected it?

None of these answers feed back into the factor graph. The FGO's actual state trajectory is
produced by the unmodified `keyframe()` exactly as today. This is why the method below (Section
2) is built as a read-before-call wrapper: it must observe the same inputs the real factor used
and must not perturb them.

**What this count is NOT.** A rejection changes later states (a dropped flow factor means the
next keyframe's IMU-only prediction is less corrected, so its own predicted covariance, and
therefore its own NIS, would differ). This diagnostic counts "would this specific, as-built
factor have failed the test", not "what would the gated FGO's trajectory have been". The two
are different questions; only the first is answered here, and only the first was asked.

## 2. Method

### 2.1 Predicted-state choice

FGO_DESIGN.md Section 9.2 already settled this for Phase 4 (headings and yaw rate) and ruled
that the gate's covariance must come from the IMU-preintegration predictive covariance of the
connected variables (`X(k), V(k), B(k)`), not from `marginalCovariance` on a key not yet in the
smoother. `fgo_core.py` already implements exactly this as a parallel, non-perturbing
recursion (`_info()`, `_posterior_cov()`, `cov_gate`), used today to gate the yaw cap
(`_att_trace_pred`, Section 9.4) and the Phase 4 forward factors (`_forward_factors`). This
diagnostic reuses the SAME machinery, unmodified, by calling the inherited `_info()`/`_values()`
helpers from a subclass, rather than re-deriving a second covariance path.

Concretely, before calling the real (unmodified) `keyframe()`, the wrapper:

1. Reads `self.pim`, `self.prev_pose`, `self.prev_vel`, `self.prev_bias`, `self.cov_gate`, all
   read-only, none mutated before the real call.
2. Rebuilds the same IMU-only prediction the real `keyframe()` is about to make:
   `pred = self.pim.predict(NavState(self.prev_pose, self.prev_vel), self.prev_bias)`.
3. Builds a graph containing ONLY the `CombinedImuFactor` (no yaw cap, no range, no flow, no
   forward factor; this is deliberately NOT what `_forward_factors` does, see Section 2.1.1).
4. Computes `P_pred = inv(self._info(g_imu, self._values(km1, k, Xk, Vk, self.prev_bias),
   km1, k, prior=self.cov_gate))[15:30, 15:30]`, the predictive covariance of
   `(X(k), V(k), B(k))`, in that stacked order: columns 0 to 5 are `X(k)`'s tangent, columns 6
   to 8 are `V(k)`, columns 9 to 14 are `B(k)`'s tangent. This is exactly `_att_trace_pred`'s own
   expression, generalised from the attitude trace to the full block.

#### 2.1.1 A real divergence from the Phase 4 forward-factor gate, flagged explicitly

`_forward_factors` computes its NIS covariance from `_info(g, ...)` where `g` by that point
already contains the IMU factor and whatever yaw-cap, range and flow factors were added earlier
in the SAME `keyframe()` call. That is correct for Phase 4, because the forward heading and
yaw-rate measurements are fused (hypothetically) after flow and range within one update cycle.

Flow and range are not in that position in the FGO's own design: each is meant to be gated
against the state before any correction from the OTHER of the pair, matching how EKF3's
innovation test is specified (an a-priori P). This diagnostic uses the pure IMU-only `P_pred`
for both the flow gate and the range gate. Section 7(a) below states precisely where this
departs from EKF3's own fusion order and quantifies the direction of the resulting bias.

### 2.2 Gate quantities, by factor type

For both flow and range, the wrapper builds the SAME `CustomFactor` object the real
`keyframe()` is about to add (via `factors.flow_factor(...)` or `factors.range_factor(...)`,
imported unmodified), and linearises it at the predicted values
`{X(k): Xk, V(k): Vk, B(k): self.prev_bias}`. These are exactly the values the real `keyframe()`
inserts as its own initial guess, per FGO_DESIGN.md Section 9.2's literal recipe:

```
A, b = factor.linearize(values)      # whitened Jacobian and residual (gtsam JacobianFactor)
S     = A @ P_pred_sub @ A.T + I      # whitened, so R folds to the identity term
testRatio = b.T @ inv(S) @ b / gate_c
```

`P_pred_sub` is the sub-block of the 15x15 `P_pred` (Section 2.1) matching `factor.keys()`
(range touches only `X(k)`, 6-wide; flow touches `X(k), V(k), B(k)`, 15-wide), taken via a
fixed offset map (`X(k)` at columns 0 to 5, `V(k)` at columns 6 to 8, `B(k)` at columns 9 to 14
within `P_pred`), the same block layout `_posterior_cov`/`_info` already use.

This is a direct, mechanical application of the already-decided design in FGO_DESIGN.md
Section 9.2/9.3. It is not a new gate design; it is that design run once, read-only, per stored
factor.

### 2.3 Per-axis flow gating (Section 9.3)

FGO_DESIGN.md Section 9.3 already settled that EKF3 gates flow X and Y independently
(`AP_NavEKF3_OptFlowFusion.cpp:328,665,668`: a `for (obsIndex=0;obsIndex<=1;...)` loop with a
scalar `flowTestRatio[obsIndex]`, gated per axis), and that the FGO must match the per-axis
accept/reject decision, not a joint 2-DOF test, while documenting as a bounded, accepted
difference that EKF3 re-solves the whole state between axis 0 and axis 1 (`:713`) and a
non-sequential gate cannot reproduce that intermediate update. This diagnostic follows the same
documented approximation: both axes are gated against the SAME `P_pred` (not sequentially
updated between them), matching Section 9.3's own acceptance of this limit.

Per-axis NIS is the row-wise form of the formula in Section 2.2: for row `i` of the flow
factor's `(A, b)`, `S_i = A_i @ P_pred_sub @ A_i.T + 1`, `nis_i = b_i^2 / S_i`.

### 2.4 Joint 2-axis NIS (reported for completeness, not as the primary count)

The brief asks for the 2-axis joint NIS to be reported too, since EKF3 itself has no joint flow
test to compare against, and the brief anticipated ambiguity about which threshold is the fair
"same 3-sigma-equivalent" comparison. Both are reported:

- **9**: the naive reuse of the per-axis gate constant unchanged (what results if the degrees
  of freedom are not adjusted for).
- **11.83**: the chi-square(2) quantile at the SAME confidence level the per-axis gate of 9
  (chi-square(1) at 9, that is 3-sigma, cumulative probability `p = 2*Phi(3) - 1 = 0.9973002`)
  implies. Chi-square(2)'s CDF has the closed form `1 - exp(-x/2)`, so the quantile at `p` is
  `x = -2*ln(1-p) = -2*ln(0.0026998) = 11.829...`. Computed analytically (no `scipy` dependency,
  consistent with this project's "derive, don't assume" standard), to full float precision in
  the script, not rounded here.

`nis_joint = b.T @ inv(S_joint) @ b` using the full 2-row `(A, b)` and `S_joint = A @
P_pred_sub @ A.T + I(2)`.

## 3. FLOW_MAX: one-sided (EKF3) vs two-sided (UKF), and the sign chain

**EKF3's FLOW_MAX check is at factor level, not axis level, and it rejects the WHOLE sample if
EITHER raw axis exceeds the bound** (`AP_NavEKF3_OptFlowFusion.cpp:668`):

```
if (really_fuse && (flowTestRatio[obsIndex]) < 1.0f
        && (ofDataDelayed.flowRadXY.x < frontend->_maxFlowRate)
        && (ofDataDelayed.flowRadXY.y < frontend->_maxFlowRate)) { ... fuse axis obsIndex ... }
```

`flowRadXY.x`/`.y` do not depend on `obsIndex`: the same condition on the full flow sample is
evaluated on both the X-axis pass and the Y-axis pass of the `for (obsIndex=0;obsIndex<=1;...)`
loop. So if `flowRadXY.x >= 2.5` (say), both axes are rejected that cycle, not just X. This
diagnostic counts FLOW_MAX at the factor level for this reason: one count per flow factor, not
two.

It is also a ONE-SIDED, SIGNED test, written as `<`, never `abs(...) <`. This is confirmed by
reading the line directly (`AP_NavEKF3_OptFlowFusion.cpp:668`), not assumed. `_maxFlowRate`
defaults to 2.5 (`AP_NavEKF3.cpp:312`, `FLOW_MAX`), confirmed live in a stored dataset's own
dataflash PARM dump (`dsn_tex_r1/ardupilot.bin`, `EK3_FLOW_MAX 2.5`), not only from source.

### 3.1 `flowRadXY` is `-rawFlowRates`, not the raw sensor value, and that sign must be chased

`AP_NavEKF3_Measurements.cpp:221`: `ofDataNew.flowRadXY = -rawFlowRates.toftype();`. This
project's own FGO_DESIGN.md already flags this ("a signed `<` on `flowRadXY = -rawFlowRates`").
`rawFlowRates` is whatever arrives over MAVLink `OPTICAL_FLOW`'s `flow_rate_x`/`flow_rate_y`
extension fields, passed through unmodified by `AP_OpticalFlow_MAV::update()`
(`state.flowRate = (flow_sum/count) * scale * dt_used`; confirmed `FLOW_FXSCALER`,
`FLOW_FYSCALER` and `FLOW_ORIENT_YAW` are all 0 in the same live PARM dump used above, so
scale is 1 and `_applyYaw` is a no-op, giving `rawFlowRates.x = flow_rate_x`,
`.y = flow_rate_y` exactly).

The FGO (and the UKF) do NOT go through this MAVLink round trip at all. `fgo_replay.py` and
`ukf_replay.py` both read `flow_x_rad`/`flow_y_rad` directly off the recorded
`/optical_flow/measurement` bag topic (`fgo_replay.py:82`), bypassing `flow_bridge.py`
entirely. To ask "would EKF3's own onboard gate have rejected this exact sample", the sign
chain `flow_x_rad/flow_y_rad -> flow_rate_x/flow_rate_y -> rawFlowRates -> flowRadXY` has to be
reconstructed by hand, using whichever `flow_bridge.py` mapping was actually live for that
flight. This is a per-dataset provenance question, handled concretely in Section 3.2 below, not
left as a caveat.

**Using the CURRENT (HEAD) `flow_bridge.py` mapping** (`flow_rate_x = msg.flow_x_rad`,
`flow_rate_y = msg.flow_y_rad`, confirmed by reading `flow_bridge.py:134-135` directly, both
unflipped):

```
flowRadXY.x = -rawFlowRates.x = -flow_rate_x = -flow_x_rad
flowRadXY.y = -rawFlowRates.y = -flow_rate_y = -flow_y_rad
```

EKF3 rejects the whole sample if `flowRadXY.x >= 2.5 OR flowRadXY.y >= 2.5`, that is, in terms
of the FGO's own `flow_xy = (flow_x_rad, flow_y_rad)`:

> **EKF3 one-sided reject rule (current mapping): `flow_x_rad <= -2.5 OR flow_y_rad <= -2.5`.**

That is: large NEGATIVE raw flow on either axis is rejected by this specific check; large
POSITIVE raw flow is not caught by it at all (it may still be caught by the separate 4.2 rad/s
vector-length clamp at `Measurements.cpp:203`, which is a different, pre-existing, already-known
asymmetry; the FGO's own clamp is per-axis `abs < 4.2` on flow only, EKF3's is
`rawFlowRates.length() < 4.2` on flow AND gyro jointly; not re-derived here, flagged as a
related but separate limitation, see Section 7(c)).

**UKF two-sided reject rule** (`ukf_core.py:293`, unchanged, both read directly as written):
`abs(flow_x_rad) >= 2.5 OR abs(flow_y_rad) >= 2.5`.

**Reading adopted for this diagnostic.** The question this diagnostic answers is the
counterfactual "EKF3's rule, applied to the flow this project actually (and, as of the fix
below, correctly) injects". Under that reading the CURRENT mapping is the right one to use for
every run, independent of each flight's own date, because the diagnostic is not trying to
replay history faithfully; it is trying to ask what a correctly-wired EKF3 gate would have done
with the SAME physical measurement the FGO used. Section 3.2's per-flight check is kept anyway,
as supporting context and as the input needed if a future ruling instead wants the
historically-faithful reading for a specific flight.

### 3.2 Provenance check on the sign chain, done per trial

`flow_bridge.py`'s X-axis mapping was corrected in commit `2236590` (2026-09-29, "Lateral flow
sign fix"), from `flow_rate_x = -msg.flow_x_rad` to `flow_rate_x = msg.flow_x_rad`. The same
commit also corrected `measurement_models.h_flow_pose`'s lateral row (`SIGN_X`), which the
FGO's own flow factor (and this diagnostic's NIS gate) uses directly. The two corrections are
coupled: as of `2236590`, both the EKF3-replica sign chain above and the FGO's own measurement
model use the corrected X convention consistently.

**Checked for every trial in the proposed run set (Section 5), not just the replay commit.**
Each trial's own `metadata.yaml` records the `thesis_ws` commit at RECORDING time (when the bag
was flown, which is what actually determines the sensor data's provenance, as distinct from
`4fb721f`, which is the commit that later REPLAYED the bags to produce the stored `fgo/`
outputs). `git merge-base --is-ancestor 2236590 <that commit>` was run for all 15 proposed set
1A trials and all 18 proposed set 1B trials (Section 5.1):

**Result: all 33 trials checked post-date `2236590`.** The flown commits recorded in each
trial's `metadata.yaml` are `7a90e81`, `651c6a4` or `bc0a818` depending on which batch the
trial was flown in, and `2236590` is an ancestor of all three. So the current flow_bridge.py
mapping applies, unambiguously and by flight-date provenance as well as by the Section 3.1
reading, to every run in this diagnostic's proposed set.

**What would still need checking before extending this diagnostic to a different run set**: any
trial flown before `2236590`. None exist in the sets this stage proposes.

## 4. Range gate: citation correction, and clip versus reject

CLAUDE.md's UKF Design table cites `EK3_RNG_I_GATE` (500) as the range NIS gate. **This is the
wrong parameter name for the fusion path this thesis actually uses.** Checked directly in
`AP_NavEKF3_OptFlowFusion.cpp:140`: `_rngInnovGate` (`RNG_I_GATE`) gates `auxRngTestRatio`,
which belongs to `EstimateTerrainOffset`, the auxiliary terrain-offset estimator used for
optical-flow terrain tracking. FGO_DESIGN.md itself already notes a related line in the same
file is "inactive under EK3_SRC1_POSZ = RangeFinder" (our config); the same inactivity applies
to this one too.

The gate actually protecting the main height/position fusion (`EK3_SRC1_POSZ = RangeFinder`,
our config) is `HGT_I_GATE` (`_hgtInnovGate`, default 500, `AP_NavEKF3.cpp:226`), used at
`AP_NavEKF3_PosVelFusion.cpp:1022` (`hgtTestRatio = sq(innovVelPos[5]) / (sq(0.01*HGT_I_GATE) *
varInnovVelPos[5])`), where `R_OBS[5] = posDownObsNoise = sq(RNG_M_NSE)` for a rangefinder
height source (`PosVelFusion.cpp:1428`). `RNG_M_NSE` (0.5 m, `AP_NavEKF3.cpp:292`, `_rngNoise`)
IS the correct R value and matches the FGO's own `range_noise = Isotropic.Sigma(1, 0.5)`
exactly.

**Clip versus reject, checked directly (`PosVelFusion.cpp:1015-1045`).** EKF3's height gate has
a clip-instead-of-reject branch: `if (hgtTestRatio < maxTestRatio) hgtCheckPassed = true; else
if ((_gpsGlitchRadiusMax <= 0) && !onGroundNotNavigating && (activeHgtSource == GPS)) {
varInnovVelPos[5] *= hgtTestRatio; hgtCheckPassed = true; }`. The clip branch requires
`activeHgtSource == GPS`. Under `EK3_SRC1_POSZ = RangeFinder` (this project's config, confirmed
from a live PARM dump), `activeHgtSource` is RangeFinder, not GPS, so this condition is false
and the clip branch is never taken, independent of `EK3_GLITCH_RAD`'s value (which defaults to
25 anyway, not 0, per `AP_NavEKF3.cpp`'s `GLITCH_RADIUS_DEFAULT`, so even a GPS height source
would not take it by default). **So for this project's configuration, `hgtTestRatio >=
maxTestRatio` (1.0 in flight, 3.0 on ground and not navigating) is a genuine reject, not a
clip.** `RANGE_GATE_C = 25` in this diagnostic's output column means "EKF3 would have rejected
this range factor", not "would have clipped its variance".

One further nuance, noted rather than modelled: `if (hgtCheckPassed || hgtTimeout ||
badIMUdata)` still fuses the measurement even after repeated rejections, once `hgtTimeout`
trips (followed by `ResetHeight()`), so chronic per-sample rejection does not mean EKF3 "never
uses height again". This diagnostic answers the per-sample NIS question only; it does not model
EKF3's timeout/reset fallback.

**Also note, for completeness:** `posDownObsNoise` for a rangefinder source
(`PosVelFusion.cpp:1430`) adds a small `(rng * terrGradMax)^2 * (1 - cos(tilt)^2)` term on top
of `RNG_M_NSE^2`, so "R matches exactly" is true at level flight and only approximately true
under tilt. Negligible at cruise tilt angles in this project's flights, but not exactly zero;
flagged rather than assumed away.

Both `HGT_I_GATE` and `RNG_I_GATE` default to 500, confirmed live in the same PARM dump used
above (`EK3_HGT_I_GATE 500.0`, `EK3_RNG_I_GATE 500.0`), so the citation correction above changes
NO number in this diagnostic (`gate_c = (0.01*500)^2 = 25` either way); it only corrects which
parameter is cited as the source and what the resulting column means. Worth fixing in
CLAUDE.md separately; not done here (read-only brief).

## 5. Run set and cost

### 5.1 Run set, built from what is actually stored

Checked directly against `~/thesis_data/trials/` (not assumed from naming conventions), and
cross-checked against the production arguments each set was actually replayed with
(`eval/run_set_eval.sh`'s `rerun_dsn` job line, and `final_rerun2/final2_f4.fgo.jobs`'s Phase 4
job lines).

**Set 1A, `dsn_*` baseline, 15 runs, `fgo_replay.py <trial> 0.25`, no arm:**

| trial | has stored `fgo/` |
|---|---|
| `dsn_blank_r1`, `dsn_blank_r2`, `dsn_blank_r3` | yes |
| `dsn_tex_r1`, `dsn_tex_r2`, `dsn_tex_r3` | yes |
| `dsn_tex_r4`, `dsn_tex_r5`, `dsn_tex_r6`, `dsn_tex_r7`, `dsn_tex_r8`, `dsn_tex_r9` | yes (the brief's "confirmatory 4-10") |
| `dsn_tex_r10` | **no stored `fgo/`, excluded** |
| `dsn_trans_r1`, `dsn_trans_r2`, `dsn_trans_r3` | yes |

**Set 1B, Phase 4 forward-camera arms, 3 arms x 2 wall types x 3 floor conditions x 3 repeats
= 54 runs, `fgo_replay.py <trial> 0.25 2 <arm>`:**

| world prefix | floor conditions (3 repeats each) | arms |
|---|---|---|
| `fwdc_*` (line-textured walls, upper bound) | `tex`, `trans`, `blank` | `baseline`, `heading`, `heading_yawrate` |
| `fwdplainc_*` (plain walls, featureless case) | `tex`, `trans`, `blank` | `baseline`, `heading`, `heading_yawrate` |

All 18 trials (9 `fwdc_*` + 9 `fwdplainc_*`) have stored `fgo_baseline/`, `fgo_heading/` and
`fgo_heading_yawrate/` directories. They ALSO have a large number of F-test ablation arm
directories (`fgo_heading_F1cauchy_2_385`, `fgo_heading_F2mask`, `fgo_heading_F3bd10`, and
more; up to 19 extra arms on `fwdc_tex_r1`). **These are a separate, much larger ablation study
and are NOT included in the proposed set 1B.** Whether to extend the diagnostic to them is
Section 8 item 4, for the coordinator to rule on.

**Sets 2 to 4 (room experiments T, O, L, H, S2v2, S3v2): OUT OF SCOPE for stage 1**, for the
structural reason in Section 5.1 of the original scope note, repeated here: `reanchor()` sets
`no_yawcap=True`, after which `cov_gate` is only updated under `log_cov` (not by default), so it
goes stale, and a NIS computed from it would be meaningless without first proving a covariance
path that stays live through a reanchor. Not fixed here; flagged as its own item (Section 8
item 5).

**Flown (closed-loop) FGO runs (`cl_bcpp_*`, `cl_b_*`, `clf*`): OUT OF SCOPE**, unless the C++
node's own logs carry the per-keyframe state needed to rebuild `P_pred`. Not checked in this
stage; stated as unknown rather than assumed either way.

### 5.2 Job list

One `heavy.py` line per trial (set 1A) or per trial-and-arm (set 1B):

```
# set 1A (15 jobs)
for t in dsn_blank_r1 dsn_blank_r2 dsn_blank_r3 dsn_tex_r1 dsn_tex_r2 dsn_tex_r3 \
         dsn_tex_r4 dsn_tex_r5 dsn_tex_r6 dsn_tex_r7 dsn_tex_r8 dsn_tex_r9 \
         dsn_trans_r1 dsn_trans_r2 dsn_trans_r3; do
  python3 src/estimators/fgo_cpp/tools/heavy.py "fgo_gate_count --run $t" -- \
    ~/venv-fgo/bin/python3 eval/fgo_gate_count.py --run "$t"
done

# set 1B (54 jobs: 18 trials x 3 arms)
for t in fwdc_tex_r1 fwdc_tex_r2 fwdc_tex_r3 fwdc_trans_r1 fwdc_trans_r2 fwdc_trans_r3 \
         fwdc_blank_r1 fwdc_blank_r2 fwdc_blank_r3 fwdplainc_tex_r1 fwdplainc_tex_r2 \
         fwdplainc_tex_r3 fwdplainc_trans_r1 fwdplainc_trans_r2 fwdplainc_trans_r3 \
         fwdplainc_blank_r1 fwdplainc_blank_r2 fwdplainc_blank_r3; do
  for a in baseline heading heading_yawrate; do
    python3 src/estimators/fgo_cpp/tools/heavy.py "fgo_gate_count --run $t --arm $a" -- \
      ~/venv-fgo/bin/python3 eval/fgo_gate_count.py --run "$t" --arm "$a"
  done
done
```

Each job writes one `~/thesis_data/diagnostics/fgo_gate_count/<trial>[_<arm>]_gate_summary.json`
and touches no trial directory.

### 5.3 Cost estimate, anchored to a measured number

**Measured, this stage** (Section 6.3): one instrumented replay of `dsn_trans_r1` (a
transition-world bag, 10031 keyframes) took about 115 seconds wall clock, single-threaded, bag
already cached. The hook's OWN overhead, read from the script's existing per-keyframe timing
print, is small: median update time went from 15.5 ms to 16.7 ms and p99 from 29.9 ms to 31.6 ms
when the hook was added, about 6 to 8 percent. The 115 second figure is the WHOLE instrumented
run's wall clock (bag load, 111442 IMU integrations, 10031 keyframe updates, TUM write), not the
hook's overhead alone; the earlier draft of this document misread it as the latter.

**Per numbers.md Section 14, FGO step time is strongly world-dependent (DIAGNOSTIC, workstation,
post thread-limit fix): textured median 32.7-32.9 ms, transition 17-18 ms, blank 4.5 ms,
baseline arm.** Scaling the measured 115 second transition figure by these ratios (textured
roughly 1.9x transition's per-step cost; blank roughly 0.27x) gives rough per-trial estimates:

| world | per-trial estimate (baseline arm, set 1A) |
|---|---|
| blank | about 30-40 s |
| transition | about 115 s (measured) |
| textured | about 210-220 s |

**Set 1A total (15 trials: 3 blank, 9 textured [3 core + 6 confirmatory], 3 transition):**
roughly 3x35 + 9x215 + 3x115 = 105 + 1935 + 345 = about 2400 s, call it 40 minutes serial,
single-job. The project's own harness runs several jobs in parallel (`numbers.md`'s "6 jobs
parallel, 1 thread" note for the FGO batch), so a parallel run across available cores would be
considerably faster; 40 minutes is the serial upper bound, not an expected wall-clock time.

**Set 1B total (54 trial-arm runs):** the `+heading`/`+heading_yawrate` arms cost MORE per step
than baseline (`numbers.md` Section 14: textured baseline 32.7-32.9 ms vs +heading 37-40 ms vs
+heading_yawrate 42 ms; transition baseline 17-18 ms vs +heading 23-35 ms; blank baseline 4.5 ms
vs +heading 11-12.5 ms). Using the same per-trial durations as set 1A scaled by these per-step
ratios (roughly 1.2x for heading, 1.3x for heading_yawrate on textured; more pronounced on
blank), set 1B's 54 runs are estimated at roughly 54 x 150 s average (a rough blend across the
three arms and three floor conditions, biased toward the cheaper blank/transition worlds since
half the trials are `fwdplainc`/`fwdc` blank or transition), call it 2 to 2.5 hours serial,
single-job. As with set 1A this is a serial upper bound.

**Disk:** `bagcache/` (Section 6.2) holds one decompressed `.db3` per trial touched, about
14 to 76 MB each depending on trial length (measured: `dsn_trans_r1`'s was about 76 MB). Running
the full job list touches up to 15 + 18 = 33 distinct trials (set 1B's 3 arms share one bag per
trial, so the cache is NOT tripled), so budget roughly 33 x 50 MB, call it 1.5 to 2 GB, and clean
`~/thesis_data/diagnostics/fgo_gate_count/bagcache/` after stage 2 completes.

## 6. Byte-identity proof

### 6.1 Why `dsn_tex_r1`/`dsn_trans_r1`'s stored output is a valid comparison target

Checked (not assumed) via `git log`/`git merge-base`/`git diff`:

- `final_rerun2/pipeline.log` records `thesis_ws HEAD 4fb721fde5d1f01cded4c11f2a8559357c2d0e71`
  at its preflight step (2026-10-10T13:02:52), immediately before its `dsn` stage
  (13:08:06 to 13:15:14) wrote `~/thesis_data/trials/dsn_*/fgo/`, the most recent regeneration
  of the stored baseline FGO outputs.
- `git diff 4fb721f..HEAD -- src/estimators/fgo/fgo_core.py src/estimators/fgo/factors.py
  src/estimators/measurement_models.py src/estimators/fgo/fgo_replay.py` shows real changes
  (14/12/42/110 lines), but every one of them is gated behind a new, off-by-default parameter
  (`geom=None` in the estimator files, `FGO_EVENTS` unset in the harness) added for a "rung 1"
  real-vehicle feature. Read line by line: with `geom=None` (the only value any SIM call site
  ever passes) and `FGO_EVENTS` unset (true for a plain `fgo_replay.py <trial>` invocation),
  every changed branch resolves to the unchanged prior behaviour. This is stated in the diff's
  own comments ("`geom=None` everywhere (the default) keeps the module constants above, so
  every simulation result is unchanged").
- The lateral-flow sign fix (`2236590`, Section 3.2) predates `4fb721f`, so it is already baked
  into the stored output, with no mismatch there either.
- This claim was checked PER TRIAL for provenance in Section 3.2 (all 33 trials in the proposed
  run set postdate `2236590`), and empirically for `dsn_trans_r1` in Section 6.3 below.

So a plain `python3 src/estimators/fgo/fgo_replay.py dsn_trans_r1 0.25` on current HEAD is
expected to reproduce `~/thesis_data/trials/dsn_trans_r1/fgo/fgo_traj.tum` byte for byte,
independent of this diagnostic's own instrumentation. **The window must be `0.25`, not
`fgo_replay.py`'s own `1.0` fallback.** Checked directly in `eval/run_set_eval.sh`
(`rerun_dsn`'s job line: `fgo_replay.py $t 0.25`), the stage `eval/final_rerun_pipeline.sh`'s
`dsn` step actually calls (`SKIP_UKF="$FGO_ONLY" runlog ... eval/run_set_eval.sh rerun_dsn
"${DSN[@]}"`) to produce the stored output. `eval/fgo_gate_count.py --byte-identity` defaults
to `--window 0.25` for this reason, not `fgo_replay.py`'s own unused scaffold default.

### 6.2 Proof design

Two runs, both to a scratch `FGO_OUT_ROOT` (never the trial directory), same environment
(`OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, matching `heavy.py`'s default and the
"thread-limit fix" environment referenced in `numbers.md` Section 14):

1. **Control**: current HEAD, unmodified `fgo_core.FGO`, via `fgo_replay.py dsn_trans_r1 0.25`
   straight (no monkeypatch).
2. **Instrumented**: current HEAD, `fgo_core.FGO` monkeypatched to `GateCountFGO` (Section 2)
   before `fgo_replay.py` is executed in-process via `runpy.run_path(..., run_name="__main__")`,
   the same in-process technique `docs/handovers/2026-10-09_fgo_gate_conditioning.md` already
   used for a comparable non-perturbation proof.

Before comparing TUM files, the script asserts the hook actually exercised every factor the
real FGO added: zero internal errors, and the count of logged flow/range gate entries equals
`fgo.n_flow`/`fgo.n_range` exactly. Without this check, a wrapper that silently errored on every
keyframe would still report a trivial, meaningless PASS (its exception handler means the real
`keyframe()` still runs; an unexercised hook changes nothing by construction, so comparing it
against a control proves nothing about stage 2's actual counting logic). An early version of
this script did not have this check; it was added and the proof re-run before the result in
Section 6.3 was accepted.

Then, in order:

- `cmp` control's `fgo_traj.tum` against instrumented's `fgo_traj.tum`: proves the wrapper
  itself is non-perturbing. This is the brief's actual ask.
- `cmp` control's `fgo_traj.tum` against the stored `~/thesis_data/trials/dsn_trans_r1/fgo/
  fgo_traj.tum`: proves (or disproves) the Section 6.1 provenance claim. If this one fails, it
  is a PROVENANCE finding (current code differs from the code that produced the stored file),
  not an instrumentation finding, and is reported as such, separately from the first
  comparison, per the brief's STOP condition.

`eval/fgo_gate_count.py --byte-identity dsn_trans_r1` runs both and reports both comparisons,
plus the hook-ran check and per-run wall-clock timing. `--arm` is supported (for set 1B's
`fgo_<arm>/` output directories) but was not exercised in the Section 6.3 run below; a set 1B
byte-identity check is listed as job 1 of the Section 5.2 job list's heading arm, for stage 2.

### 6.3 Result

**Run, via `heavy.py` (single-threaded: `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`), after a
concurrent agent's `BUILD_LOCK` cleared.** Three attempts in total: the first used the wrong
window (`fgo_replay.py`'s own `1.0` s fallback instead of production's `0.25` s) and was killed
before completing once the bug was caught (exit 143, `BUILD_LOCK` released cleanly by
`heavy.py`'s own `SIGTERM` handler); the second, with `--window 0.25`, passed both file
comparisons but was re-run a third time after the hook-ran assertion (Section 6.2) was added,
since a PASS without that assertion does not prove what it claims to prove.

**Third run's result:**

```
control run: 105.8 s wall clock
instrumented run: 115.0 s wall clock
hook ran cleanly: True (gate_errors=0, flow checked 5340/5340, range checked 10030/10030)
{
  "trial": "dsn_trans_r1", "arm": null,
  "control_vs_instrumented_byte_identical": true,
  "control_vs_stored_byte_identical": true,
  "hook_ran_cleanly": true,
  "n_flow_factors": 5340, "n_range_factors": 10030,
  "control_wall_s": 105.8, "instrumented_wall_s": 115.0
}
PASS: hook ran on every factor added, and control == instrumented == stored.
```

**All three checks passed.** The hook-ran assertion confirms the wrapper actually computed a
gate decision for every one of the 5340 flow factors and 10030 range factors the real
`keyframe()` added (not a subset, and with zero internal errors), so the non-perturbation proof
that follows is not vacuous. `control == instrumented` proves the wrapper does not change the
estimate. `control == stored` confirms the Section 6.1 provenance claim empirically: current
HEAD, run with the production window, reproduces the stored `dsn_trans_r1/fgo/fgo_traj.tum`
byte for byte.

**Measured cost, both runs separately timed this time** (superseding the first attempt's single
mtime-delta figure, which conflated the whole instrumented run's duration with the hook's own
overhead): control 105.8 s, instrumented 115.0 s, for a hook overhead of 9.2 s, about 8.7
percent of the control run's own time. This matches the per-keyframe timing the script itself
prints (median 15.3 ms to 16.8 ms, about 9.8 percent) to within the run-to-run noise expected on
a shared machine. Section 5.3's cost estimate uses the 115.0 s whole-run figure as the anchor,
not the 9.2 s overhead alone, since a stage 2 job runs the instrumented path only (no control
run needed per job once this proof stands).

**Not evaluated and not relevant to this diagnostic**: the run's own `[result] along-track =
2717.7 m (true 151.1) ... ATE = 695.74 m` is `dsn_trans_r1`'s own known large divergence once
flow aiding is lost over the blank half (`numbers.md`'s "Diverging (unaided) FGO results"
category, FGO_DESIGN.md Section 9.5; the FGO dead-reckons on IMU and range rather than freezing
position, by design, unlike EKF3's `const_pos`). This diagnostic does not evaluate accuracy; it
is unaffected by whether the trajectory it is checking happens to be an accurate one.

## 7. Limitations

(a) **Flow and range are gated against the pure IMU-only predictive covariance, not a
sequentially-updated one, and EKF3 fuses height before flow within one cycle.** Traced
directly: EKF3's own `UpdateFilter()` (`AP_NavEKF3_core.cpp:663,677`) runs yaw/mag fusion, then
`SelectVelPosFusion()` (which includes the rangefinder height fusion), then
`SelectFlowFusion()`. So EKF3's actual flow NIS test uses a covariance already corrected by that
cycle's height fusion, which this diagnostic's flow gate does not reproduce (both flow and range
are gated against the same pure-IMU `P_pred`, per FGO_DESIGN.md Section 9.2's already-decided,
documented approximation). This will tend to overstate flow's gating covariance somewhat, in a
way not measured here. A second, "range-updated P" variant for the flow gate is a one-extra-
inversion addition the coordinator can request if this matters enough to check (Section 8
item 3).

(b) **Conditioning.** `docs/handovers/2026-10-09_fgo_gate_conditioning.md` measured `cond(L)`
(the 30x30 information matrix this recursion inverts) growing from 3.6e8 to 1.5e12 over a 340 s
flight, with the Python-versus-C++ relative difference in the gate-trace quantity growing from
6e-8 to 5e-4 over the same flight, dominated by round-off amplified by that conditioning
(horizontal position is unobservable, so nothing contracts the relevant direction). This
diagnostic uses the SAME recursion (`_info`/`_posterior_cov`, Python, `np.linalg.inv`), so its
NIS values late in a long flight carry the same growing numerical uncertainty, independent of
any bug. The planned implementation reports, per run, how many NIS values fall within plus or
minus 0.1 percent of a threshold (9, 11.83 or 25); that is the count of decisions this
conditioning could plausibly flip, not a hand-wave claim that numbers get noisy late in the
flight.

(c) **The FLOW_MAX one-sided-versus-two-sided comparison is reported, with an adopted reading
stated in Section 3.1 and supporting per-flight provenance in Section 3.2.** A second, narrower,
already-known asymmetry (EKF3's existing vector-length-4.2 clamp on flow and gyro jointly versus
the FGO's existing per-axis-abs-4.2 clamp on flow only) is noted but not newly instrumented: it
was already known before this brief (Context item 1) and is a different question from FLOW_MAX
(2.5).

(d) **A rejection changes later states; this count does not simulate that.** Repeated from
Section 1 for visibility: every NIS and FLOW_MAX answer here is "would this exact, as-actually-
used factor have failed the test", evaluated against the trajectory the UNGATED FGO actually
produced. It is not a simulation of a gated FGO's own, different, trajectory.

(e) **Room and closed-loop runs are out of scope for stage 1** (Section 5.1) for a structural
reason (`cov_gate` staleness after `reanchor()`, and unknown coverage of the C++ node's own logs
respectively), not a cost reason.

## 8. Design choices needing a ruling before stage 2

1. **The FLOW_MAX sign chain (Section 3.1) and the reading adopted there (apply the current,
   corrected mapping to every run, rather than each flight's historically-live mapping) should
   be independently re-checked before being used to produce a number anyone cites.** Signs like
   this have been flipped and re-flipped in this project's own history (the lateral-flow sign
   fix itself, `2236590`, corrected an earlier wrong derivation of the SAME kind), and the
   Section 3.2 check, while thorough for the proposed run set, is not a substitute for an
   independent re-derivation.
2. **Whether to extend set 1B to the F-test ablation arms** (Section 5.1), currently excluded.
3. **Whether to also log the "range-updated P" variant of the flow gate** (limitation (a)): one
   extra inversion per keyframe with a flow factor, cheap, but a scope decision since it is not
   what FGO_DESIGN.md Section 9.2 specifies.
4. **Whether set 1B (Phase 4 arms) and the optional room sets (Section 5.1 sets 2 to 4) are
   wanted for stage 2 at all**, or whether set 1A alone is sufficient for the diagnostic's
   purpose, given the cost estimate in Section 5.3.
5. **Whether a covariance path that survives `reanchor()` is worth building**, to bring the room
   experiments (T, O, L, H, S2v2, S3v2) into scope for a later stage.

## 9. Stage-2 addendum (dated 2026-11-12; see `docs/thesis/diagnostics/fgo_gate_count_results.md` for the full write-up)

Item 1 above was done, item 2 and 4 were resolved (set 1A + 1B only, no F-test arms, per D137), and
items 3/5 remain open (not built in stage 2 either).

### 9.1 Independent FLOW_MAX sign-chain re-derivation, step by step with file:line

Re-traced at `~/ardupilot` pinned commit `7bac20cbcc`, reading each file directly rather than
trusting this design note's own Section 3.1/3.2 citations a second time:

1. **`flow_bridge.py` (this repo, current HEAD):** `flow_rate_x = msg.flow_x_rad`,
   `flow_rate_y = msg.flow_y_rad`, both UNFLIPPED (confirmed by reading the file directly; its own
   comment records the 2026-09-29 lateral-sign fix, commit `2236590`).
2. **`AP_OpticalFlow_MAV::handle_msg` (`AP_OpticalFlow_MAV.cpp:118-121`):** `flow_sum.x +=
   packet.flow_rate_x; flow_sum.y += packet.flow_rate_y;`, unflipped, summed verbatim.
3. **`AP_OpticalFlow_MAV::update` (`AP_OpticalFlow_MAV.cpp:61-68,79-80`):**
   `flow_scale_factor_{x,y} = 1 + 0.001*FLOW_{FX,FY}SCALER`; `dt_used = 1.0` (since
   `flow_sum_is_rads` is true once any `flow_rate_x/y` extension field is non-zero, always true
   here); then `_applyYaw(...)`. `OpticalFlow_backend::_applyYaw` (`AP_OpticalFlow_Backend.cpp:
   38-45`) is a no-op when `FLOW_ORIENT_YAW == 0`. Confirmed LIVE, from a PARM dump of three
   trials spanning both run sets (`fwdc_tex_r1`, `fwdplainc_blank_r1`, `dsn_tex_r1`):
   `FLOW_FXSCALER = FLOW_FYSCALER = FLOW_ORIENT_YAW = 0.0` in all three, so
   `state.flowRate = (flow_x_rad, flow_y_rad)` exactly, unscaled, unrotated: this is
   `rawFlowRates` as read by EKF3's measurement-ingestion path.
4. **`AP_NavEKF3_Measurements.cpp:221`:** `ofDataNew.flowRadXY = - rawFlowRates.toftype();`, a
   negation of BOTH axes.
5. **`AP_NavEKF3_OptFlowFusion.cpp:668`:** `if (really_fuse && (flowTestRatio[obsIndex]) < 1.0f &&
   (ofDataDelayed.flowRadXY.x < frontend->_maxFlowRate) && (ofDataDelayed.flowRadXY.y <
   frontend->_maxFlowRate))`, fusion of EITHER axis requires BOTH `flowRadXY.x < FLOW_MAX` AND
   `flowRadXY.y < FLOW_MAX`; `_maxFlowRate` is `FLOW_MAX`, confirmed at `AP_NavEKF3.cpp:305-312`
   (`AP_GROUPINFO("FLOW_MAX", 20, NavEKF3, _maxFlowRate, 2.5f)`) - the parameter name this design
   note already cited is correct (not `EK3_MAX_FLOW`).
6. **`fgo_replay.py:111`:** `ev.append((tt, "flow", (np.array([m.flow_x_rad, m.flow_y_rad]), ...)))`:
   the flow array handed into the event stream is `[flow_x_rad, flow_y_rad]` directly off the bag,
   with NO negation and NO axis swap (also checked the `FGO_EVENTS` dataflash-replay path at line
   90-91, out of scope for this run set regardless since it is unused by the plain
   `fgo_replay.py <trial> 0.25 [2 [<arm>]]` invocation).

One real wrinkle, read and accounted for: `fgo_replay.py:203-205` can REPLACE the flow value via
`measurement_models.GroundProximityFlow.replace()` before `keyframe()` sees it, but only
pre-takeoff below 0.5 m height, substituting a synthetic rotation-only value. The gate-count
diagnostic reads `flow_xy` off exactly what `keyframe()` receives, i.e. after this replacement,
consistent with asking "would THIS, the factor actually added, have failed the gate". Reported
per run as `n_flow_gp_replaced`.

**Result: the re-derivation confirms this design note's Section 3.1/3.2 rule exactly, with no sign
disagreement found:**

```
flowRadXY.x = -rawFlowRates.x = -flow_rate_x = -flow_x_rad
flowRadXY.y = -rawFlowRates.y = -flow_rate_y = -flow_y_rad
reject (fuse neither axis) iff flowRadXY.x >= FLOW_MAX OR flowRadXY.y >= FLOW_MAX
                            iff flow_x_rad <= -FLOW_MAX OR flow_y_rad <= -FLOW_MAX
```

So **"EKF3 one-sided reject rule: `flow_x_rad <= -2.5 OR flow_y_rad <= -2.5`"** (Section 3.1 above)
stands as independently re-derived, item 1 of Section 8's list is closed, and
`eval/fgo_gate_count.py`'s `flow_max_onesided_reject()` was not changed.

### 9.2 Corrections to Section 5.1 (run set) and Section 5.3 (cost estimate)

- **Section 5.1's claim "All 18 trials ... have stored `fgo_baseline/`, `fgo_heading/` and
  `fgo_heading_yawrate/` directories" is WRONG for the 9 `fwdplainc_*` trials.** Running set 1B hit
  `measurement_models.py:230-232`'s own `ValueError` on all 9 `fwdplainc_*` x `heading_yawrate`
  combinations ("yaw-rate arm not defined for fwdplainc, failed Phase 3 validation"); confirmed
  directly that no `fwdplainc_*` trial directory has a stored `fgo_heading_yawrate/` output at
  all, consistent with CLAUDE.md's Sensor Status table ("Yaw rate: textured walls only"). Set 1B's
  achievable size is 45, not 54: `fwdc_*` 9 trials x 3 arms = 27, `fwdplainc_*` 9 trials x 2 arms
  (`baseline`, `heading`) = 18.
- **Section 5.3's bag-cache estimate (1.5-2 GB) was far too low.** The actual decompressed cache
  (`~/thesis_data/diagnostics/fgo_gate_count/bagcache/`) reached 56 GB across the 33 trials
  actually touched, because the estimate was anchored to a `dsn_*` bag (76 MB, no camera frames),
  while the `fwdc_*`/`fwdplainc_*` bags also carry recorded forward-camera frames (CLAUDE.md:
  "`run_trial.sh` enables forward-camera recording for all four suffixes"). Removed after both
  run sets completed; see the results file Section 9 for the full account, including a checksum-
  guard coverage bug found and corrected in the same stage.

Full results, per-set/per-run tables, and all further caveats: see
`docs/thesis/diagnostics/fgo_gate_count_results.md` and
`docs/thesis/diagnostics/numbers_fgo_gate_count.md`.
