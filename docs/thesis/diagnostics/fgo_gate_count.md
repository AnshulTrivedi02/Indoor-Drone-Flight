# FGO gate count: a read-only diagnostic (stage 1 -- design, instrumentation, plan)

Status: DRAFT, stage 1 only. No estimator code changed, no thesis result changed, no committed
estimator file edited. Scope per the 2026-11-11 brief and the user's verbatim approval:

> "Gating: read-only count of stored FGO runs (flow NIS 9 per axis and 2-axis, range NIS 25,
> flow > 2.5 rad/s), reported both ways for FLOW_MAX sidedness. No implementation."

This is a diagnostic only. It counts how many of the flow/range factors the FGO actually used
(the ones already added to the graph by `fgo_core.py`'s unmodified `keyframe()`) would have
failed an EKF3-style gate, had that gate been implemented. It changes no estimator and no
stored result. "No FGO core gates flow/range today" is confirmed: `fgo_core.py` (keyframe(),
~line 180-185) and `fgo_cpp/src/fgo_core.cpp` (~line 140-147) only clamp `abs(flow) < 4.2`
per axis before adding a flow factor, and check the range is in `[r_lo, r_hi]` before adding
a range factor -- no NIS test, no FLOW_MAX test, anywhere in either core.

## 1. What is being counted, and why read-only

For each flow and range factor the FGO actually added to a stored run's graph, this diagnostic
asks four independent, purely retrospective questions of that one factor:

1. Would EKF3's per-axis NIS gate (flow) have rejected it?
2. Would EKF3's NIS gate (range/height) have rejected it?
3. Would EKF3's FLOW_MAX one-sided rule have rejected it (and therefore the whole flow factor,
   both axes, see 5.2)?
4. Would the UKF's FLOW_MAX two-sided rule have rejected it?

None of these answers feed back into the factor graph. The FGO's actual state trajectory is
produced by the unmodified `keyframe()` exactly as today. This is why the method below (sec. 2)
is built as a read-before-call wrapper: it must observe the same inputs the real factor used
and must not perturb them.

**What this count is NOT.** A rejection changes later states (a dropped flow factor means the
next keyframe's IMU-only prediction is less corrected, so its own predicted covariance -- and
therefore its own NIS -- would differ). This diagnostic counts "would this specific, as-built
factor have failed the test", not "what would the gated FGO's trajectory have been". The two
are different questions; only the first is answered here, and only the first was asked.

## 2. Method

### 2.1 Predicted-state choice

FGO_DESIGN.md Section 9.2 already settled this for Phase 4 (headings/yaw-rate) and ruled that
the gate's covariance must come from the IMU-preintegration predictive covariance of the
connected variables (`X(k), V(k), B(k)`), not from `marginalCovariance` on a key not yet in the
smoother. `fgo_core.py` already implements exactly this as a parallel, non-perturbing
recursion (`_info()`, `_posterior_cov()`, `cov_gate`), used today to gate the yaw cap
(`_att_trace_pred`, Section 9.4) and the Phase 4 forward factors (`_forward_factors`). This
diagnostic reuses the SAME machinery, unmodified, by calling the inherited `_info()`/`_values()`
helpers from a subclass, rather than re-deriving a second covariance path.

Concretely, before calling the real (unmodified) `keyframe()`, the wrapper:

1. Reads `self.pim`, `self.prev_pose`, `self.prev_vel`, `self.prev_bias`, `self.cov_gate` --
   all read-only, none are mutated before the real call.
2. Rebuilds the same IMU-only prediction the real `keyframe()` is about to make:
   `pred = self.pim.predict(NavState(self.prev_pose, self.prev_vel), self.prev_bias)`.
3. Builds a graph containing ONLY the `CombinedImuFactor` (no yaw cap, no range, no flow,
   no forward factor -- this is deliberately NOT what `_forward_factors` does, see 2.1.1).
4. Computes `P_pred = inv(self._info(g_imu, self._values(km1, k, Xk, Vk, self.prev_bias),
   km1, k, prior=self.cov_gate))[15:30, 15:30]` -- the predictive covariance of
   `(X(k), V(k), B(k))`, in that stacked (6, 3, 6) order. This is exactly
   `_att_trace_pred`'s own expression, generalised from the attitude trace to the full block.

#### 2.1.1 A real divergence from the Phase 4 forward-factor gate, flagged explicitly

`_forward_factors` computes its NIS covariance from `_info(g, ...)` where `g` by that point
already contains the IMU factor AND whatever yaw-cap/range/flow factors were added earlier in
the SAME `keyframe()` call. That is correct for Phase 4, because the forward heading/yaw-rate
measurements are fused (hypothetically) after flow/range within one update cycle.

Flow and range are not in that position: each is the FIRST correction applied to the IMU-only
prediction in its own right, so the predicted covariance it should be gated against is the pure
IMU-only one (step 4 above), not a value already corrected by the OTHER of the pair. This
diagnostic uses the pure IMU-only P for the flow gate and the range gate alike. See Section 7
item (a) for why that is itself an approximation.

### 2.2 Gate quantities, by factor type

For both flow and range, the wrapper builds the SAME `CustomFactor` object the real
`keyframe()` is about to add (via `factors.flow_factor(...)` / `factors.range_factor(...)`,
imported unmodified), and linearises it at the predicted values
`{X(k): Xk, V(k): Vk, B(k): self.prev_bias}` -- i.e. exactly the values the real `keyframe()`
inserts as its own initial guess, per FGO_DESIGN.md Section 9.2's literal recipe:

```
A, b = factor.linearize(values)      # whitened Jacobian and residual (gtsam JacobianFactor)
S     = A @ P_pred_sub @ A.T + I      # whitened, so R folds to the identity term
testRatio = b.T @ inv(S) @ b / gate_c
```

`P_pred_sub` is the sub-block of the 15x15 `P_pred` (Section 2.1) matching `factor.keys()`
(range touches only `X(k)`, 6-wide; flow touches `X(k), V(k), B(k)`, 15-wide) -- taken via a
fixed offset map `{X(k): (0,6), V(k): (6,9), B(k): (9,15)}` into `P_pred`, the same block
layout `_posterior_cov`/`_info` already use.

This is a direct, mechanical application of the already-decided design in FGO_DESIGN.md
Section 9.2/9.3 -- it is not a new gate design, it is that design run once, read-only, per
stored factor.

### 2.3 Per-axis flow gating (Section 9.3)

FGO_DESIGN.md Section 9.3 already settled that EKF3 gates flow X and Y **independently**
(`AP_NavEKF3_OptFlowFusion.cpp:328,665,668` -- a `for (obsIndex=0;obsIndex<=1;...)` loop, a
scalar `flowTestRatio[obsIndex]`, gated per axis) and that the FGO must match the per-axis
accept/reject decision, not a joint 2-DOF test, while documenting as a bounded, accepted
difference that EKF3 re-solves the whole state between axis 0 and axis 1 (`:713`) and a
non-sequential gate cannot reproduce that intermediate update. This diagnostic follows the
same documented approximation: BOTH axes are gated against the SAME `P_pred` (not sequentially
updated between them), matching Section 9.3's own acceptance of this limit.

Per-axis NIS is the row-wise form of the formula in 2.2: for row `i` of the flow factor's
`(A, b)`, `S_i = A_i @ P_pred_sub @ A_i.T + 1`, `nis_i = b_i^2 / S_i`.

### 2.4 Joint 2-axis NIS (reported for completeness, not as the primary count)

The brief asks for the 2-axis joint NIS to be reported too, since EKF3 itself has no joint
flow test to compare against, and the brief anticipated ambiguity about which threshold is the
fair "same 3-sigma-equivalent" comparison. Both are reported:

- **9** -- the naive reuse of the per-axis gate constant unchanged (what you get if you forget
  that the degrees of freedom changed).
- **11.83** -- the chi-square(2) quantile at the SAME confidence level the per-axis gate of 9
  (chi-square(1) at 9, i.e. 3-sigma, cumulative probability `p = 2*Phi(3) - 1 = 0.9973002`)
  implies. Chi-square(2)'s CDF has the closed form `1 - exp(-x/2)`, so the quantile at `p` is
  `x = -2*ln(1-p) = -2*ln(0.0026998) = 11.829...`. Computed analytically (no `scipy` dependency,
  consistent with this project's "derive, don't assume" standard), to full float precision in
  the script, not rounded here.

`nis_joint = b.T @ inv(S_joint) @ b` using the full 2-row `(A, b)` and `S_joint = A @
P_pred_sub @ A.T + I(2)`.

## 3. FLOW_MAX: one-sided (EKF3) vs two-sided (UKF), and the sign chain

**EKF3's FLOW_MAX check is at factor level, not axis level, and it is a hard reject of the
WHOLE sample if EITHER raw axis exceeds the bound** (`AP_NavEKF3_OptFlowFusion.cpp:668`):

```
if (really_fuse && (flowTestRatio[obsIndex]) < 1.0f
        && (ofDataDelayed.flowRadXY.x < frontend->_maxFlowRate)
        && (ofDataDelayed.flowRadXY.y < frontend->_maxFlowRate)) { ... fuse axis obsIndex ... }
```

`flowRadXY.x`/`.y` do not depend on `obsIndex` -- the SAME two-sided-free, signed condition is
evaluated on both the X-axis pass and the Y-axis pass of the `for (obsIndex=0;obsIndex<=1;...)`
loop. So if `flowRadXY.x >= 2.5` (say), BOTH axes are rejected that cycle, not just X. This
diagnostic counts FLOW_MAX at the factor level for this reason: one count per flow factor, not
two.

It is also a ONE-SIDED, SIGNED test -- `<`, never `abs(...) <` -- confirmed by reading the line
directly (`AP_NavEKF3_OptFlowFusion.cpp:668`), not assumed. `_maxFlowRate` defaults to 2.5
(`AP_NavEKF3.cpp:312`, `FLOW_MAX`), confirmed live in a stored dataset's own dataflash PARM dump
(`dsn_tex_r1/ardupilot.bin`, `EK3_FLOW_MAX 2.5`), not only from source.

### 3.1 `flowRadXY` is `-rawFlowRates`, not the raw sensor value, and that sign must be chased

`AP_NavEKF3_Measurements.cpp:221`: `ofDataNew.flowRadXY = -rawFlowRates.toftype();` -- this
project's own FGO_DESIGN.md already flags this ("a signed `<` on `flowRadXY = -rawFlowRates`").
`rawFlowRates` is whatever arrives over MAVLink `OPTICAL_FLOW`'s `flow_rate_x`/`flow_rate_y`
extension fields, passed through unmodified by `AP_OpticalFlow_MAV::update()`
(`state.flowRate = (flow_sum/count) * scale * dt_used`, confirmed `FLOW_FXSCALER`/
`FLOW_FYSCALER` are 0 and `FLOW_ORIENT_YAW` is 0 in the same live PARM dump used above, so
scale = 1 and `_applyYaw` is a no-op -- `rawFlowRates.x = flow_rate_x`, `.y = flow_rate_y`
exactly).

The FGO (and the UKF) do NOT go through this MAVLink round trip at all -- `fgo_replay.py` and
`ukf_replay.py` both read `flow_x_rad`/`flow_y_rad` directly off the recorded
`/optical_flow/measurement` bag topic (`fgo_replay.py:82`), bypassing `flow_bridge.py`
entirely. To ask "would EKF3's own onboard gate have rejected this exact sample", the sign
chain `flow_x_rad/flow_y_rad -> flow_rate_x/flow_rate_y -> rawFlowRates -> flowRadXY` has to be
reconstructed by hand, using whichever `flow_bridge.py` mapping was actually live for that
flight (this is a per-dataset provenance question, not a constant -- see Section 3.2).

**Using the CURRENT (HEAD) `flow_bridge.py` mapping** (`flow_rate_x = msg.flow_x_rad`,
`flow_rate_y = msg.flow_y_rad`, confirmed by reading `flow_bridge.py:134-135` directly, both
unflipped):

```
flowRadXY.x = -rawFlowRates.x = -flow_rate_x = -flow_x_rad
flowRadXY.y = -rawFlowRates.y = -flow_rate_y = -flow_y_rad
```

EKF3 rejects the WHOLE sample if `flowRadXY.x >= 2.5 OR flowRadXY.y >= 2.5`, i.e. in terms of
the FGO's own `flow_xy = (flow_x_rad, flow_y_rad)`:

> **EKF3 one-sided reject rule (current mapping): `flow_x_rad <= -2.5 OR flow_y_rad <= -2.5`.**

That is: large NEGATIVE raw flow on either axis is rejected by this specific check; large
POSITIVE raw flow is not caught by it at all (it may still be caught by the separate 4.2 rad/s
vector-length clamp at `Measurements.cpp:203`, which is a different, pre-existing, already-known
asymmetry -- the FGO's own clamp is per-axis `abs < 4.2`, EKF3's is `rawFlowRates.length() <
4.2`; not re-derived here, flagged as a related but separate limitation, see Section 7(c)).

**UKF two-sided reject rule** (`ukf_core.py:293`, unchanged, both read directly as written):
`abs(flow_x_rad) >= 2.5 OR abs(flow_y_rad) >= 2.5`.

### 3.2 Provenance caveat on the sign chain -- NEEDS A RULING

`flow_bridge.py`'s X-axis mapping was corrected in commit `2236590` (2026-09-29, "Lateral flow
sign fix"), from `flow_rate_x = -msg.flow_x_rad` to `flow_rate_x = msg.flow_x_rad`. The SAME
commit also corrected `measurement_models.h_flow_pose`'s lateral row (`SIGN_X`), which the
FGO's own flow factor (and this diagnostic's NIS gate) uses directly. The two corrections are
coupled: as of `2236590`, both the EKF3-replica sign chain above and the FGO's own measurement
model use the corrected X convention consistently.

Checked: `2236590` is an ancestor of `4fb721f` (the commit recorded at the start of the
`final_rerun2` pipeline, 2026-10-10, whose `dsn` stage is the most recent regeneration of
`~/thesis_data/trials/dsn_*/fgo/`) and of current `HEAD`. So **the proposed run set (Section 5)
post-dates the fix, and using the current mapping for the Section 3.1 derivation is consistent
for that run set.** This was checked from `git log`/`git merge-base`, not assumed.

**What still needs a ruling, not assumed here:** whether any run in a LATER run set (e.g. a
Phase 4 ceiling-world re-run, or a future dataset) predates `2236590`. If so, the X-axis
one-sided rule in Section 3.1 flips sign for that specific run
(`flow_x_rad >= 2.5 OR flow_y_rad <= -2.5`, the PRE-fix mapping), and the script must check each
run's provenance commit (closest available signal: `metadata.yaml`'s `git_commit`, which is the
`thesis_ws` commit at RECORDING time -- the sensor data itself is unaffected by the later fix,
only the interpretation is) against `2236590` before choosing which rule to apply. The design
below computes and reports BOTH the one-sided and two-sided counts per the brief's explicit
request ("reported both ways for FLOW_MAX sidedness"); it does not pick a winner.

## 4. Range gate: citation correction

CLAUDE.md's UKF Design table cites `EK3_RNG_I_GATE` (500) as the range NIS gate. **This is the
wrong parameter name for the fusion path this thesis actually uses.** Checked directly in
`AP_NavEKF3_OptFlowFusion.cpp:140`: `_rngInnovGate` (`RNG_I_GATE`) gates `auxRngTestRatio`,
which belongs to `EstimateTerrainOffset` -- the AUXILIARY terrain-offset estimator used for
optical-flow terrain tracking, which FGO_DESIGN.md itself already notes is "inactive under
EK3_SRC1_POSZ = RangeFinder" (our config, for a different line in the same file -- the same
inactivity applies here).

The gate actually protecting the main height/position fusion (`EK3_SRC1_POSZ = RangeFinder`,
our config) is `HGT_I_GATE` (`_hgtInnovGate`, default 500, `AP_NavEKF3.cpp:226`), used at
`AP_NavEKF3_PosVelFusion.cpp:1022` (`hgtTestRatio = sq(innovVelPos[5]) / (sq(0.01*HGT_I_GATE) *
varInnovVelPos[5])`), where `R_OBS[5] = posDownObsNoise = sq(RNG_M_NSE)` for a rangefinder
height source (`PosVelFusion.cpp:1428`). `RNG_M_NSE` (0.5 m, `AP_NavEKF3.cpp:292`, `_rngNoise`)
IS the correct R value and matches the FGO's own `range_noise = Isotropic.Sigma(1, 0.5)`
exactly.

Both `HGT_I_GATE` and `RNG_I_GATE` default to 500, confirmed live in the same PARM dump used
above (`EK3_HGT_I_GATE 500.0`, `EK3_RNG_I_GATE 500.0`), so this correction changes NO number in
this diagnostic (`gate_c = (0.01*500)^2 = 25` either way) -- it only corrects which parameter is
cited as the source. Worth fixing in CLAUDE.md separately; not done here (read-only brief).

## 5. Run set and cost

### 5.1 Candidate runs

| set | trials | notes |
|---|---|---|
| 1A: `dsn_*` baseline (primary) | `dsn_tex_r1..r3`, `dsn_trans_r1..r3`, `dsn_blank_r1..r3` (9), plus the confirmatory `dsn_tex_r4..r10` where present | the three-way comparison baseline; cap on (always `cap_on=True`, no `reanchor()`), so `cov_gate` is live and valid throughout -- the diagnostic's covariance recursion is meaningful end to end |
| 1B: Phase 4 forward-camera arms | `fwdc_*`/`fwdplainc_*` baseline + heading + heading_yawrate arms (textured, plain walls) | same `cap_on` property; the forward factors themselves are out of scope (already gated, Section 9.4/Phase 4), only each run's OWN flow/range factors are counted |
| 2-4 (optional): room experiments (T, O, L, H, S2/S3) | `room_tags`, `T_A_*`, `H_*`, `S2v2_*`, `S3v2_*` | **OUT OF SCOPE for stage 1.** `reanchor()` sets `no_yawcap=True`, after which `cov_gate` is only updated under `log_cov` (not by default) -- it goes stale, and the NIS computed from it would be meaningless without first proving a covariance path that stays live through a reanchor. Flagging this, not fixing it. |
| Flown (closed-loop) FGO | `cl_bcpp_*`, `cl_b_*`, `clf*` | **OUT OF SCOPE unless the C++ node's own logs carry the per-keyframe state needed to rebuild `P_pred`.** Not checked in this stage; say so rather than assume. |

Set 1A is the minimum the brief asks for ("at minimum the 1A `dsn_*` FGO baseline replays
(flights 1-9, and 4-10 confirmatory)"). Set 1B is the second tier ("the 1B Phase 4 FGO arms").

### 5.2 Cost estimate (no run performed for this, beyond the one proof run in Section 6)

From `docs/thesis/numbers.md` Section 14 (DIAGNOSTIC, workstation Python, single-thread-capped
post-fix): FGO step time is world-dependent -- textured ~27-40 ms/median, transition ~15-35 ms,
blank ~4-12 ms, depending on arm. `dsn_tex_r1` alone is 10047 keyframes (same Section). The
instrumented wrapper adds one extra `np.linalg.inv` of a (up to) 30x30 matrix and one or two
small (<=15x15) linear solves per flow/range factor actually added -- call it roughly the SAME
ORDER as the existing `_posterior_cov`/`_att_trace_pred` calls already made every keyframe when
`cap_on`, so a reasonable estimate is a SMALL constant-factor overhead (not measured; to be
confirmed in the Section 6 proof run's own wall-clock numbers, or in stage 2 if this estimate is
wrong).

Using the pipeline's own recorded stage timing as the best available anchor:
`final_rerun2/pipeline.log` shows the whole `dsn` stage (9+ trials, uninstrumented baseline FGO
runs, among other things) completed in `BEGIN 13:08:06 -> DONE 13:15:14`, about 7 minutes. That
stage likely parallelised across trials (this project's harness runs multiple FGO jobs in
parallel per `numbers.md` Section 14's "6 jobs parallel, 1 thread" note), so 7 minutes is a
lower bound for what a SERIAL instrumented pass over the same 9 bags would cost, not an upper
bound. A serial, single-job, single-thread run of all 9 textured/transition/blank bags, using
the per-bag step-time figures above and ~10000 keyframes/bag, is roughly 9 x (a few minutes) =
15-30 minutes, a safe estimate for set 1A alone; set 1B (Phase 4 arms, textured + plain, 3
arms x 2 wall types x however many repeats recorded) is a comparable or larger multiple. This
is an ESTIMATE for the coordinator to release against, not a measured figure for the full set --
the only measured figure in this document is the Section 6 proof run.

## 6. Byte-identity proof

### 6.1 Why `dsn_tex_r1`/`dsn_trans_r1`'s stored output is a valid comparison target

Checked (not assumed) via `git log`/`git merge-base`/`git diff`:

- `final_rerun2/pipeline.log` records `thesis_ws HEAD 4fb721fde5d1f01cded4c11f2a8559357c2d0e71`
  at its preflight step (2026-10-10T13:02:52), immediately before its `dsn` stage
  (13:08:06-13:15:14) wrote `~/thesis_data/trials/dsn_*/fgo/` -- the most recent regeneration of
  the stored baseline FGO outputs.
- `git diff 4fb721f..HEAD -- src/estimators/fgo/fgo_core.py src/estimators/fgo/factors.py
  src/estimators/measurement_models.py src/estimators/fgo/fgo_replay.py` shows real changes
  (14/12/42/110 lines), but every one of them is gated behind a NEW, OFF-BY-DEFAULT parameter
  (`geom=None` in the estimator files, `FGO_EVENTS` unset in the harness) added for a "rung 1"
  real-vehicle feature. Read line by line: with `geom=None` (the only value any SIM call site
  ever passes) and `FGO_EVENTS` unset (true for a plain `fgo_replay.py <trial>` invocation),
  every changed branch resolves to the UNCHANGED prior behaviour. This is stated in the diff's
  own comments ("`geom=None` everywhere (the default) keeps the module constants above ... so
  every simulation result is unchanged").
- The lateral-flow sign fix (`2236590`, Section 3.2) predates `4fb721f`, so it is already baked
  into the stored output -- no mismatch there either.

So a plain `python3 src/estimators/fgo/fgo_replay.py dsn_trans_r1 0.25` on current HEAD is
expected to reproduce `~/thesis_data/trials/dsn_trans_r1/fgo/fgo_traj.tum` byte for byte,
independent of this diagnostic's own instrumentation. This lets the proof target the STORED
file directly, rather than only a same-session control run. **The window must be `0.25`, not
`fgo_replay.py`'s own `1.0` fallback** -- checked directly in `eval/run_set_eval.sh`
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
   before `fgo_replay.py` is executed in-process via `runpy.run_path(..., run_name="__main__")`
   -- the same in-process technique `docs/handovers/2026-10-09_fgo_gate_conditioning.md`
   already used for a comparable non-perturbation proof.

Compared, in order:

- `cmp` control's `fgo_traj.tum` against instrumented's `fgo_traj.tum` -- proves the WRAPPER
  itself is non-perturbing. This is the brief's actual ask.
- `cmp` control's `fgo_traj.tum` against the STORED `~/thesis_data/trials/dsn_trans_r1/fgo/
  fgo_traj.tum` -- proves (or disproves) the Section 6.1 provenance claim. If this one fails,
  it is a PROVENANCE finding (current code differs from the code that produced the stored
  file), not an instrumentation finding, and is reported as such, separately from the first
  comparison, per the brief's STOP condition.

`eval/fgo_gate_count.py --byte-identity dsn_trans_r1` runs both and reports both comparisons.

### 6.3 Result

**Run, via `heavy.py` (single-threaded: `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`), after a
concurrent agent's `BUILD_LOCK` cleared.** First attempt used the WRONG window (`fgo_replay.py`'s
own `1.0` s fallback instead of production's `0.25` s) and was killed before completing (exit
143, `BUILD_LOCK` released cleanly by `heavy.py`'s own `SIGTERM` handler) once the bug was
caught; re-run with `--window 0.25` (now the script's default, Section 6.2):

```
{
  "trial": "dsn_trans_r1",
  "control_vs_instrumented_byte_identical": true,
  "control_vs_stored_byte_identical": true
}
PASS: control == instrumented == stored.
```

**Both comparisons passed.** `control == instrumented` proves the wrapper (`GateCountFGO`) does
not perturb the estimate -- the brief's actual ask. `control == stored` additionally confirms
the Section 6.1 provenance claim empirically, not just from the `git diff` argument: current
HEAD, run with the production window, reproduces the stored `dsn_trans_r1/fgo/fgo_traj.tum`
byte for byte.

Output used `10031` keyframes (`5340` flow factors, `10030` range factors added -- consistent
with the geometry: range fuses almost every keyframe, flow is gated out for long stretches once
the trajectory crosses into the blank half, per `fgo_replay.py`'s own printed
`[run] ... flow factors 5340 range factors 10030`). Per-keyframe update time (the script's own
existing timing instrument, unrelated to this diagnostic): median 15.5-16.7 ms, matching
`numbers.md` Section 14's transition-world figure. **Measured wall-clock cost of the
instrumented run beyond the control run: about 115 s** (file-mtime delta between the two runs'
`fgo_traj.tum`, for this one ~10000-keyframe bag) -- a real anchor for the Section 5.2 estimate,
on top of whatever the control run itself costs (not separately isolated here, but of the same
order based on the printed per-keyframe timing).

**Not evaluated and not relevant to this diagnostic**: the run's own `[result] along-track =
2717.7 m (true 151.1) ... ATE = 695.74 m` is `dsn_trans_r1`'s own known large divergence once
flow aiding is lost over the blank half (`numbers.md`'s "Diverging (unaided) FGO results"
category, FGO_DESIGN.md Section 9.5 -- the FGO dead-reckons on IMU+range rather than freezing
position, by design, unlike EKF3's `const_pos`). This diagnostic does not evaluate accuracy; it
is unaffected by whether the trajectory it is checking happens to be an accurate one.

## 7. Limitations

(a) **Flow and range are gated against the pure IMU-only predictive covariance, not a
sequentially-updated one.** Traced directly: EKF3's own `UpdateFilter()`
(`AP_NavEKF3_core.cpp:663,677`) runs `SelectVelPosFusion()` (which includes the rangefinder
height fusion) BEFORE `SelectFlowFusion()` in the same predict-update cycle. So EKF3's actual
flow NIS test uses a covariance already corrected by that cycle's height fusion, which this
diagnostic's flow gate does not reproduce (both flow and range are gated against the same
pure-IMU `P_pred`, per FGO_DESIGN.md Section 9.2's already-decided, documented approximation).
This will tend to overstate flow's gating covariance somewhat, in a way not measured here. A
second, "range-updated P" variant for the flow gate is a one-extra-inversion addition the
coordinator can request if this matters enough to check.

(b) **Conditioning.** `docs/handovers/2026-10-09_fgo_gate_conditioning.md` measured `cond(L)`
(the 30x30 information matrix this recursion inverts) growing from 3.6e8 to 1.5e12 over a 340 s
flight, with the Python-vs-C++ relative difference in the gate-trace quantity growing from 6e-8
to 5e-4 over the same flight, dominated by round-off amplified by that conditioning (horizontal
position is unobservable, so nothing contracts the relevant direction). This diagnostic uses
the SAME recursion (`_info`/`_posterior_cov`, Python, `np.linalg.inv`), so its NIS values late
in a long flight carry the same growing numerical uncertainty, independent of any bug. Any
implementation of this diagnostic should report, per run, how many NIS values fall within
+/-0.1% of a threshold (9, 11.83 or 25) -- that is the count of decisions this conditioning
could plausibly flip, not a hand-wave "numbers get noisy late in the flight".

(c) **The FLOW_MAX one-sided-vs-two-sided comparison is reported, not resolved, pending the
Section 3.2 provenance ruling.** A second, narrower, already-known asymmetry (EKF3's existing
vector-length-4.2 clamp vs the FGO's existing per-axis-abs-4.2 clamp) is noted but not newly
instrumented -- it was already known before this brief (Context item 1) and is a different
question from FLOW_MAX (2.5).

(d) **A rejection changes later states; this count does not simulate that.** Repeated from
Section 1 for visibility: every NIS/FLOW_MAX answer here is "would this exact, as-actually-used
factor have failed the test", evaluated against the trajectory the UNGATED FGO actually
produced. It is not a simulation of a gated FGO's own (different) trajectory.

(e) **Room/closed-loop runs are out of scope for stage 1** (Section 5.1) for a structural reason
(`cov_gate` staleness after `reanchor()`, and unknown coverage of the C++ node's own logs
respectively), not a cost reason.

## 8. Design choices needing a ruling before stage 2

1. **The FLOW_MAX sign chain (Section 3.1/3.2) is new, careful, multi-step derivation, not
   previously stated in this form anywhere in the codebase.** It should be independently
   re-derived or re-checked before being used to produce a number anyone cites, given how easy
   a sign error is in this exact spot and how much this project's own history shows signs like
   this getting flipped and re-flipped (the lateral-flow sign fix itself, `2236590`, corrected
   an earlier wrong derivation of the SAME kind).
2. **Per-run provenance check for the sign chain** (Section 3.2): before running stage 2 on any
   run set beyond 1A/1B, confirm each run's `metadata.yaml` `git_commit` postdates `2236590`,
   or compute the pre-fix variant for runs that predate it.
3. **Whether to also log the "range-updated P" variant of the flow gate** (limitation (a)) --
   one extra inversion per keyframe with a flow factor, cheap, but a scope decision since it is
   not what FGO_DESIGN.md Section 9.2 specifies.
4. **Whether set 1B (Phase 4 arms) and the optional room sets (2-4) are wanted for stage 2**, or
   whether 1A alone is sufficient for the diagnostic's purpose.
