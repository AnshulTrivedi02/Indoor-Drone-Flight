# FGO gate-count diagnostic: stage 2 results (DIAGNOSTIC)

Status: DIAGNOSTIC. No verdict. No estimator code changed, no thesis result changed, no committed
estimator file edited. This is stage 2 of `docs/thesis/diagnostics/fgo_gate_count.md` (read that
first for the method, the predicted-state choice, the per-axis/joint NIS formulas, the FLOW_MAX
one-sided-vs-two-sided question, and the Section 6 byte-identity proof design). Scope per D134 and
D137 (`docs/thesis/tier1/decisions_log.md`): run sets 1A (15 `dsn_*` runs) and 1B (54 Phase 4
trial-arm runs) only. No F-test ablation arms, no room experiments.

User approval (2026-11-11), quoted verbatim: "Gating: read-only count of stored FGO runs (flow NIS
9 per axis and 2-axis, range NIS 25, flow > 2.5 rad/s), reported both ways for FLOW_MAX sidedness.
No implementation."

**Up front: set 1B's registered size of 54 is not achievable: 9 of the 54 registered combinations
(`fwdplainc_*` x `heading_yawrate`, all 3 floors x 3 repeats) do not exist in this project's own
code** (`measurement_models.py:232` raises `ValueError` for this exact combination, matching
CLAUDE.md's existing "Yaw rate: textured walls only" statement). This was found while running set
1B, not assumed beforehand; see Section 3 for the full detail and the confirming evidence (no
`fwdplainc_*` trial has a stored `fgo_heading_yawrate/` directory at all). 60 of the 69 registered
1A+1B jobs ran; the other 9 are this N/A combination, not failures. All counts below are over the
60 runs that exist: 15/15 set 1A, 45/45 of set 1B's achievable combinations.

## 0. What changed in the diagnostic script between stage 1 and stage 2

Two bugs in stage 1's `cmd_run` (the `--run` driver) were found and fixed before set 1B could be
run correctly, both in `eval/fgo_gate_count.py` only (never `fgo_core.py`, `factors.py`,
`measurement_models.py` or `fgo_replay.py`, all still imported unmodified):

1. **Arm collision.** The stage-1 summary filename was `{trial}_gate_summary.json`, with no arm
   suffix. Running `baseline`, `heading` and `heading_yawrate` for the same trial would have
   silently overwritten the same file three times, leaving only the last arm's counts. Fixed: the
   filename and a new `"arm"` field now disambiguate (`{trial}_{arm}_gate_summary.json`).
2. **No per-run byte-identity check.** D134's acceptance condition ("accepted only if its output
   is byte-identical to the stored run's") was checked once, for one trial (`dsn_trans_r1`), in
   stage 1. That is not the same claim as "every run in this count is accepted on this basis" -
   stage 1 never checked, for example, whether `dsn_tex_r4`-`r9` (the "confirmatory 4-10" trials)
   or any of the 54 set-1B runs were produced by code and a window matching current HEAD. Fixed:
   `cmd_run` now also runs the instrumented replay into a scratch directory, `cmp`s its TUM output
   against the trial's own stored TUM, and records `instrumented_vs_stored_byte_identical` in every
   run's summary JSON. `eval/fgo_gate_count_aggregate.py`'s `load_runs()` now ASSERTS every loaded
   run is byte-identical before building any sum, so a run whose output is NOT byte-identical to its
   stored counterpart would refuse to aggregate, not silently enter a count. In this run set the
   assert never fires: all 60 runs that actually produced a summary are byte-identical (Section 3).

A third bug, in the new aggregation script written for this stage (`eval/fgo_gate_count_aggregate.py`,
not in anything from stage 1), was found and fixed before any count was quoted: its `_pct()` helper
pre-rounded a percentage to 4 decimal places before the thesis's own `rd()` function rounded it a
second time to 2 decimal places for display. This double rounding can move a value across the final
rounding boundary: `10/1770*100 = 0.564971...%` must round to `0.56%`, but `round(0.564971..., 4) =
0.5650`, which THEN rounds to `0.57%`. Found by the `--check` step itself failing on exactly this case
(`1B_fwdc_blank_baseline`'s axis-0 and axis-1 columns). Fixed by storing the full-precision percentage
(no intermediate rounding) and letting `rd()` be the only rounding step, per the project's own stated
rounding rule (`eval/figs_thesis.py:86-96`, "round the full-precision file value ONCE").

All three fixes were exercised: the stage-1 proof (`dsn_trans_r1`, Section 6 of the design note)
stands unchanged; a fresh 1B byte-identity proof was run before set 1B started (Section 2 below);
every one of the 60 registered runs that actually produced a summary now carries its own per-run
byte-identity result (the other 9 are N/A, Section 3, and carry no such field); and every percentage
in `numbers_fgo_gate_count.md` passes the double-check described in Section 4.

## 1. FLOW_MAX one-sided sign chain: independently re-derived

Re-traced step by step, at `~/ardupilot` pinned commit `7bac20cbcc`, reading each file directly
rather than trusting the stage-1 design note's citations:

1. **`flow_bridge.py` (this repo, current HEAD):** `flow_rate_x = msg.flow_x_rad`,
   `flow_rate_y = msg.flow_y_rad`, both UNFLIPPED (confirmed by reading the file; the module's own
   comment records the 2026-09-29 lateral-sign fix, commit `2236590`, that made X unflipped).
2. **`AP_OpticalFlow_MAV::handle_msg` (`AP_OpticalFlow_MAV.cpp:118-121`):** `flow_sum.x +=
   packet.flow_rate_x; flow_sum.y += packet.flow_rate_y;`, unflipped, summed verbatim.
3. **`AP_OpticalFlow_MAV::update` (`AP_OpticalFlow_MAV.cpp:61-68,79-80`):** `flow_scale_factor_{x,y}
   = 1 + 0.001*FLOW_{FX,FY}SCALER`; `dt_used = 1.0` (since `flow_sum_is_rads` is true once any
   `flow_rate_x/y` extension field is non-zero, which is always true here); then `_applyYaw(...)`.
   `OpticalFlow_backend::_applyYaw` (`AP_OpticalFlow_Backend.cpp:38-45`) is a no-op when
   `FLOW_ORIENT_YAW == 0`. **Confirmed live, not assumed**, from a PARM dump of three trials spanning
   both run sets (`fwdc_tex_r1`, `fwdplainc_blank_r1`, `dsn_tex_r1`): `FLOW_FXSCALER = FLOW_FYSCALER
   = FLOW_ORIENT_YAW = 0.0` in all three, so `state.flowRate = (flow_x_rad, flow_y_rad)` exactly,
   unscaled, unrotated, this is `rawFlowRates` as read by EKF3's measurement-ingestion path.
4. **`AP_NavEKF3_Measurements.cpp:221`:** `ofDataNew.flowRadXY = - rawFlowRates.toftype();`, a
   negation of BOTH axes, confirmed by reading the line directly.
5. **`AP_NavEKF3_OptFlowFusion.cpp:668`:** `if (really_fuse && (flowTestRatio[obsIndex]) < 1.0f &&
   (ofDataDelayed.flowRadXY.x < frontend->_maxFlowRate) && (ofDataDelayed.flowRadXY.y <
   frontend->_maxFlowRate))`, fusion (of EITHER axis) requires BOTH `flowRadXY.x < FLOW_MAX` AND
   `flowRadXY.y < FLOW_MAX`; `_maxFlowRate` is `FLOW_MAX`, confirmed at `AP_NavEKF3.cpp:305-312`
   (`AP_GROUPINFO("FLOW_MAX", 20, NavEKF3, _maxFlowRate, 2.5f)`), the parameter name the stage-1
   note cited is correct (not `EK3_MAX_FLOW`).
6. **`fgo_replay.py:111`:** `ev.append((tt, "flow", (np.array([m.flow_x_rad, m.flow_y_rad]), ...)))`:
   the flow array handed into the event stream is `[flow_x_rad, flow_y_rad]` directly off the bag,
   with NO negation and NO axis swap. Confirmed by reading the line (both the live-bag path at
   line 111 and the `FGO_EVENTS` dataflash-replay path at line 90-91, which reads the same
   `flow_xy` field out of a pre-converted `.npz`, already in this convention by construction of
   `eval/bin2fgo.py`, out of scope for this run set regardless since `EVENTS` mode is unused by
   `fgo_replay.py <trial> 0.25 [2 [<arm>]]`, the only invocation form used here).

**One real wrinkle, read and accounted for, not glossed over:** between step 6 and the factor
actually being added, `fgo_replay.py:203-205` can REPLACE `flow_pend[0]` via
`measurement_models.GroundProximityFlow.replace()`, but only pre-takeoff, below 0.5 m height
(`GP_HEIGHT_M`), where it substitutes a synthetic rotation-only value
(`h_flow_rot(omega_flu)`, "EKF3's `flowRadXYcomp = 0` (zero `relVelSensor`, lever arm included)" per
the function's own comment) instead of the raw measured flow, mirroring EKF3's own
pre-takeoff/zero-relative-velocity assumption. The diagnostic's `flow_xy` is read off exactly what
`fgo_core.keyframe()` receives, i.e. AFTER this replacement, for the same reason the diagnostic
uses the real factor's own `(A, b)`: it is asking "would THIS, the factor the FGO actually added,
have failed the gate", not "would the raw un-replaced bag sample have failed the gate". This means
a small number of near-ground, pre-takeoff flow factors are gated on a synthetic value, not the raw
sensor reading; `n_flow_gp_replaced` is reported per run/group below so this is visible, not hidden.

**Re-derivation confirms stage 1's rule exactly, no sign disagreement found:**

```
flowRadXY.x = -rawFlowRates.x = -flow_rate_x = -flow_x_rad
flowRadXY.y = -rawFlowRates.y = -flow_rate_y = -flow_y_rad
reject (fuse neither axis) iff flowRadXY.x >= FLOW_MAX OR flowRadXY.y >= FLOW_MAX
                            iff flow_x_rad <= -FLOW_MAX OR flow_y_rad <= -FLOW_MAX
```

**EKF3 one-sided reject rule (re-derived, matches stage 1): `flow_x_rad <= -2.5 OR flow_y_rad <=
-2.5`.** This is implemented unchanged in `eval/fgo_gate_count.py`'s `flow_max_onesided_reject()`.
Large POSITIVE raw flow on either axis is NOT caught by this check (it is one-sided and signed, not
`abs(...)`); it may still be caught by the separate 4.2 rad/s vector-length clamp
(`AP_NavEKF3_Measurements.cpp:203`, `rawFlowRates.length() < 4.2f`), a different, already-known,
not-newly-instrumented asymmetry (design note Section 3, limitation (c)).

**UKF two-sided reject rule (read directly, unchanged): `abs(flow_x_rad) >= 2.5 OR
abs(flow_y_rad) >= 2.5`** (`src/estimators/ukf_core.py` ~line 293).

**Noise models confirmed Gaussian for every run in this set.** `fgo_core.py:97-98`:
`self.flow_noise = gtsam.noiseModel.Isotropic.Sigma(2, 0.25)`, `self.range_noise =
gtsam.noiseModel.Isotropic.Sigma(1, 0.5)`, plain Gaussian, unconditionally. The only robust-kernel
path in the file (`fwd_robust`, `fgo_core.py:102-106`) wraps `heading_noise` only, is an F1
ablation-only switch, off by default, and is never set by any command in this run set (no `F_TAG`,
no `F_ROBUST` environment variable in any of the 69 jobs). The NIS formula `S = A P Aᵀ + I` (R
already folded into the whitened `A, b`) is therefore valid for every flow and range factor counted
here, a robust re-weighting would have invalidated it.

## 2. Byte-identity: stage-1 proof stands; a fresh 1B proof run before set 1B

**Stage-1 proof (`dsn_trans_r1`, no arm):** unchanged, stands as recorded in the design note Section
6.3 (control == instrumented == stored, 5340 flow factors, 10030 range factors, hook ran cleanly).

**New 1B proof, run before set 1B started, per the brief's requirement:** `fwdc_blank_r1`, arm
`heading` (line-textured walls, the wall type heading is validated on per CLAUDE.md's Sensor
Status table, blank floor, chosen as the cheapest 1B cell to prove the method on before paying for
all 54). Run via `eval/fgo_gate_count.py --byte-identity fwdc_blank_r1 --arm heading`, through
`heavy.py`, `OMP_NUM_THREADS=1`/`OPENBLAS_NUM_THREADS=1`:

```
control run: 79.6 s wall clock
instrumented run: 80.9 s wall clock
hook ran cleanly: True (gate_errors=0, flow checked 708/708, range checked 10220/10220)
control_vs_instrumented_byte_identical: true
control_vs_stored_byte_identical: true
n_flow_factors: 708   n_range_factors: 10220
PASS: hook ran on every factor added, and control == instrumented == stored.
```

**PASS.** Both comparisons hold, and the hook-ran assertion confirms it was exercised on every one
of the 708 flow factors and 10220 range factors this run's unmodified `keyframe()` actually added
(not a subset, zero internal errors), the same non-vacuity standard as the stage-1 proof. Set 1B
was run only after this result.

(Note, not a correctness problem: this particular run's own trajectory diverges severely, logged
`[result] along-track = 24461.2 m (true 150.9) ... ATE = 9648.28 m`, a known FGO dead-reckoning
failure mode once flow aiding is effectively lost, the same category already documented for
`dsn_trans_r1` in the stage-1 design note. This diagnostic does not evaluate trajectory accuracy and
is unaffected by it; raised here only so the large along-track number in this run's log is not
mistaken for a bug in the byte-identity check itself.)

## 3. Per-run byte-identity: all 69 registered runs; 60 actually ran; 9 are N/A

Every one of the 60 runs that actually produced a summary carries its own
`instrumented_vs_stored_byte_identical` field (Section 0, fix 2), checked against
`~/thesis_data/trials/<trial>/fgo[_<arm>]/fgo_traj.tum`; the 9 N/A combinations carry no such field,
since no replay and no summary were ever produced for them (see immediately below).

**60/69 jobs ran and wrote a summary. The other 9 are NOT failures of this diagnostic; they are a
registered-run-set error, found and confirmed during this stage: the `heading_yawrate` arm does not
exist for any `fwdplainc_*` trial.** All 9 are the same `fwdplainc_*` x `heading_yawrate` combination
(`fwdplainc_tex_r1..r3`, `fwdplainc_trans_r1..r3`, `fwdplainc_blank_r1..r3`), and all 9 fail identically:

```
File "measurement_models.py", line 232, in forward_events
    raise ValueError(f"{trial}: yaw-rate arm not defined for {ds} (failed Phase 3 validation)")
ValueError: fwdplainc_blank_r3: yaw-rate arm not defined for fwdplainc (failed Phase 3 validation)
```

This is the unmodified production code's own, pre-existing gate (`measurement_models.py:230-232`,
`if use_w and FWD_SIGMA[ds]["omega"] is None: raise ValueError(...)`), and it matches CLAUDE.md's
own Sensor Status table verbatim: "Yaw rate: textured walls only." (i.e. `fwdc_*`, line-textured
walls, only, never `fwdplainc_*`, plain walls). **Confirmed directly against the stored trial
directories, not just inferred from the error**: no `fwdplainc_*` trial has a stored
`fgo_heading_yawrate/` output at all (`fwdplainc_tex_r1/` has `fgo`, `fgo_baseline`, `fgo_heading`,
one F1-ablation directory, no `fgo_heading_yawrate`), while every `fwdc_*` trial does. **The design
note's Section 5.1 run-set table ("All 18 trials ... have stored `fgo_baseline/`, `fgo_heading/` and
`fgo_heading_yawrate/` directories") was wrong for the 9 `fwdplainc_*` trials specifically**; that
claim should have excluded `fwdplainc_*` x `heading_yawrate` from the start. Set 1B's REGISTERED size
(D137, "54 Phase 4 trial-arm runs") therefore includes 9 combinations that cannot exist in this
project's own code; the count of combinations that CAN exist is 45 (`fwdc_*`: 9 trials x 3 arms = 27;
`fwdplainc_*`: 9 trials x 2 arms [`baseline`, `heading`] = 18).

**All 60 runs that did produce a summary are byte-identical to their stored counterpart. Zero gate
hook errors across all 60.** (`python3 -c` check over `eval/results/fgo_gate_count/per_run.json`:
`instrumented_vs_stored_byte_identical` is `True` for all 60; `n_gate_errors` is 0 for all 60.) This
is the per-run strengthening of D134's acceptance condition (Section 0, fix 2), not just the single
`dsn_trans_r1` and `fwdc_blank_r1`/`heading` proofs (Section 2), but every run actually counted below.

Set 1A: 15/15 ran, 15/15 byte-identical. Set 1B: 45/54 ran (9 N/A, not failures), 45/45 of those
byte-identical.

## 4. Per-set and per-run counts

See `docs/thesis/diagnostics/numbers_fgo_gate_count.md` for the full per-set table (flow per-axis/
joint/FLOW_MAX rejection counts and percentages, range rejection counts, near-threshold counts,
ground-proximity-replacement counts, byte-identity status) AND a per-run appendix (all 69
registered combinations, 60 with counts and 9 marked N/A), generated by
`eval/fgo_gate_count_numbers.py` from `eval/results/fgo_gate_count/per_set.json` and `per_run.json`
(`eval/fgo_gate_count_aggregate.py`, reading the stored per-run
`~/thesis_data/diagnostics/fgo_gate_count/*_gate_summary.json` files). 799/799 checks pass
(`eval/fgo_gate_count_numbers.py --check`): every count and percentage in the written table is
re-parsed from the markdown (not read from code) and checked TWO ways, against `rd()` of the
stored JSON percentage field directly (the brief's literal ask) and against an independent,
from-scratch decimal recomputation that calls neither `rd()` nor the stored field (catching a bug
in either one, which the first check alone cannot).

**The joint threshold used, stated explicitly (D137 requires this).** Two joint thresholds are
reported in every table, per the design note Section 2.4: **11.83**, the chi-square(2) quantile at
the same p = 0.9973 confidence the per-axis gate of 9 implies (chi-square(1) at 9 is the 3-sigma
point), is the threshold intended as the fair "same confidence" joint comparison; **9**, the naive
reuse of the per-axis constant with no degrees-of-freedom adjustment, is reported alongside it as
the secondary column, per the brief's "reported both ways" instruction. Neither is privileged as
"the" EKF3 joint gate; EKF3 itself has no joint flow test to compare against (Section 8).

**Read Section 6a before this one.** Only the set-1A/1B TEXTURED groups are a flight that stayed on
its commanded trajectory throughout, per the checked ATE bands (Section 6a): textured 118.6-133.9 m
(n=24 runs), transition 654-860 m (n=18, ALL in `numbers.md`'s documented runaway/† category), blank
8533-16293 m (n=18, ALL in the same † category). The bullets below report what the stored counts
say; the "blank is worse than textured" READING specifically should be taken with Section 6a's
caveat that blank's (and transition's) own `P_pred` is itself orders of magnitude larger, which
mechanically suppresses rejections regardless of how degraded the sensor stream is.

**Headline pattern, read from the table, not re-derived here:**

- **Flow rejection (gate 9 or 11.83, either axis or joint) is under 1% in every set-1A group**:
  textured joint-9 ~= 0.006% (5/89490), transition ~= 0.33% (53/16058), blank ~= 0.73% (10/1366).
  Textured is the only one of these three not flagged † in Section 6a, so only its figure is read
  as a relatively direct measurement of flow-factor extremity; transition's and blank's own figures
  are each confounded, to different degrees, by the runaway-`P_pred` effect Section 6a describes
  (no attempt was made here to separate "worse sensor" from "worse covariance" on either floor).
  The joint gate (9 vs 11.83) agrees exactly on textured and blank; on transition they differ
  (0.33% vs 0.23%), i.e. some transition-trial flow factors fall in the narrow discriminating band
  `[9, 11.83)` (design note Section 2.4), the only floor condition in set 1A where the two
  thresholds give a different answer.
- **Direct answer to the FLOW_MAX sidedness question (the user's literal ask): in this entire run
  set, the one-sided and two-sided counts are IDENTICAL in every single group, with no exception.**
  0/0 in all four set-1A groups; in set 1B, every group is 0/0 except `fwdc` transition, where the
  per-arm count is 1/1 (checked against `per_run.json`: this is ONE flow sample, in trial
  `fwdc_trans_r1`, counted once in each of its three replayed arms, since the raw flow input is
  identical across arms; it is not three independent extreme samples). On this data, sidedness
  never changes the count: the one flow factor extreme enough to trip the two-sided
  `abs(...) >= 2.5` rule in this project's recorded flights also trips the one-sided `<= -2.5` rule,
  i.e. it is not a large POSITIVE excursion. This is a property of what was actually flown, not a
  proof that the two rules are equivalent in general (design note Section 3.1 already establishes
  they are not, by construction). FLOW_MAX overall is rare: expected at this project's commanded
  cruise speed, derived (not assumed) from `METHODOLOGY.md`'s own measured `∂flow/∂v = 0.571` rad/s
  per m/s (the translational flow sensitivity, "Lateral-vs-forward asymmetry" finding) times the
  standard 0.5 m/s commanded forward speed, giving an expected cruise flow magnitude of about
  0.29 rad/s, well inside both the 2.5 rad/s FLOW_MAX bound and the 4.2 rad/s vector-length clamp
  already in the FGO's own `keyframe()`. A near-zero FLOW_MAX count is therefore consistent with
  the flown envelope, not evidence the check never applies; this one sample is presumably a
  transient excursion above the cruise baseline (not characterised further here), and it falls in
  `fwdc_trans_r1`, itself one of the † runaway trials (Section 6a).
- **The NUMBER of flow (and range) factors counted is identical across `baseline`/`heading`/
  `heading_yawrate` for the same wall/floor** (e.g. `fwdc` transition: 16168 flow factors in all
  three arms; `fwdc` blank: 1770 in all three), confirming the forward-camera factors are additive
  (CLAUDE.md "Sensor Fusion Architecture"; FGO_DESIGN.md Section 9) and do not add or remove flow/
  range measurements from the stream this diagnostic counts. **But the REJECTION COUNTS on that
  same, unchanged set of factors vary substantially by arm; this was checked against the stored
  per-run data, not assumed. The swings reported below are n=1 per group (one aggregated set of 3
  repeats, no independent replication of the swing itself), so they are reported as numbers to be
  read with that caveat, not as a statistically-established effect**: `fwdc` transition joint-9 goes
  69 (baseline) -> 51 (heading) -> 103 (heading+yawrate); `fwdplainc` blank axis-0 goes 8 (baseline)
  -> 61 (heading), a 7.6x jump; `fwdc` blank axis-0 goes 9 (baseline) -> 24 (heading) -> 47
  (heading+yawrate), a >5x jump base to heading+yawrate. The mechanism is that the arm changes the
  FGO's own trajectory and therefore `P_pred` and the linearisation point the SAME flow factor is
  gated against, not a different measurement stream being gated; BOTH `fwdc` transition and
  `fwdplainc`/`fwdc` blank are themselves in Section 6a's † runaway category, so these swings are
  swings in an already-diverged `P_pred`, which this diagnostic has not decomposed into "arm changed
  the degree of divergence" versus any other contributor.
- **`n_flow_gp_replaced` (the ground-proximity pre-takeoff substitution, Section 1) dominates the
  set-1A blank group: 83.1% of its counted flow factors (1135/1366) are the synthetic
  rotation-only pre-takeoff value, not a raw degraded-floor measurement**, against 5.0% on
  textured (4488/89490) and 8.3% on transition (1326/16058). This is because blank floor has so
  few flow factors overall (1366, against textured's 89490) that the fixed-size pre-takeoff window
  is a much larger share of what little got counted. **Any reading of "blank floor's flow factors
  are gated the same way as textured" must account for this: the large majority of what is being
  gated on blank is not even a measurement of the degraded floor** (and, per Section 6a, most of
  what remains is gated against an already-diverged covariance besides).

## 5. "Would have been rejected", what this does and does not mean

Repeated from the design note because it is the single most important caveat: **a rejection changes
later states.** EKF3 (or the FGO, if this were ever implemented, which it has not been) re-solves
its state after a rejection differently than after an acceptance, the next prediction's covariance,
and therefore its own next NIS, would differ. Every count in Section 4 answers "would this specific,
as-actually-used factor, evaluated against the UNGATED FGO's own trajectory and IMU-only predictive
covariance, have failed this test", not "what would a gated FGO's own, different, trajectory have
looked like". The two are different questions; only the first is answered anywhere in this
diagnostic, in either stage.

## 6. Conditioning caveat

`docs/handovers/2026-10-09_fgo_gate_conditioning.md` measured `cond(L)` (the 30x30 information
matrix `_info()` inverts, the same recursion this diagnostic reuses unmodified, Section 2.1 of the
design note) growing from 3.6e8 at the start of a flight to 1.5e12 by its end (`dsn_tex_r1`, 340 s),
with the Python-vs-C++ relative difference in the gate-trace quantity growing from 6e-8 to 5e-4 over
the same flight, both driven by backward-stable round-off amplified by that conditioning (`cond(L)`
times machine epsilon, measured there at factor 0.3-1.7), because horizontal position is
unobservable in this formulation and nothing contracts the relevant direction. This diagnostic's own
NIS values therefore carry growing numerical uncertainty late in a long flight, independent of any
bug in the gate-count hook itself. Mitigation, not a fix: every per-set group in Section 4 reports
how many NIS values fell within +/-0.1% of the relevant threshold (9, 11.83 or 25), the count of
decisions this conditioning could plausibly flip, not a hand-wave that "numbers get noisy late in
the flight". See the per-set `near_threshold` block in `per_set.json` / the near-threshold table in
`numbers_fgo_gate_count.md`.

## 6a. Diverged runs: blank-AND-transition low rejection rates are partly a covariance artefact, not evidence of good fit

> **Coordinator correction (2026-11-12): the "own-logged `ATE`" in the table below is NOT a trajectory error.** It is
> the `ATE =` print of `src/estimators/fgo/fgo_replay.py:309`, the `ate_apparatus` quantity also written to each run's
> `metrics.txt`. That quantity is axis-swapped (TUM column 1 is read as East when it is North), a known, traced
> artefact that no thesis value derives from (METHODOLOGY "FINDING (2026-10-17): axis mislabel", lines 14341-14353).
> So "textured 118.6-133.9 m" is the swap artefact: about the 151 m along-track distance appearing as cross-track,
> not a 120 m error (the textured FGO's registered evo -a (cruise) is a few metres). The transition and blank runs'
> classification as diverging does NOT rest on this print: it is numbers.md's own, independent "Diverging (unaided)
> FGO results" category for blank and transition floors. The floor split, and the caveat that a diverged `P_pred`
> suppresses rejections, stand; the metre values in the table should not be quoted.


Checked, not assumed, and grouped strictly by floor tag: `grep -h "ATE =" ~/thesis_data/diagnostics/fgo_gate_count/job_*.log`
over all 60 completed runs, split by `tex`/`trans`/`blank` in the trial name. The three floors are
cleanly separated, with no overlap:

| floor | n runs | own-logged `ATE` range | `numbers.md` † category? |
|---|---|---|---|
| textured | 24 | 118.6 m - 133.9 m | no |
| transition | 18 | 654.1 m - 859.8 m | **yes, all 18** |
| blank | 18 | 8533.1 m - 16293.3 m | **yes, all 18** |

against a true along-track of about 151 m in every case. **Both transition and blank are, in full, in
`numbers.md`'s own, independently documented "Diverging (unaided) FGO results" category** (section
header "Diverging (unaided) FGO results: evidence of divergence, not precise values", ruling
2026-10-08, which explicitly covers "runaway on BLANK OR TRANSITION floors"), consistent with the
stage-1 design note's own characterisation of `dsn_trans_r1` at 695 m in Section 6.3. **An earlier
draft of this section wrongly described only blank as diverged and transition as "smaller, bounded";
that was not checked by floor at the time and is corrected here.** Only textured stays in the
100-150 m band, well short of the † criterion. This diagnostic has not established what this
own-logged `ATE` print represents relative to the thesis's own windowed `evo -a (cruise)` metric, and
does not claim either figure, textured's included, is numerically comparable to that metric; the
only claim made here is the floor-conditioned SPLIT within this diagnostic's own replays, and that
split exactly matches `numbers.md`'s pre-existing †/non-† boundary.

**Why this matters for Section 4's transition- and blank-floor numbers.** Section 6's conditioning
finding is that the unobservable horizontal-position variance inside `P_pred` grows without bound
over a flight; on a genuinely diverged run that growth is far more extreme, so `P_pred` (and
therefore `S = A P Aᵀ + I`) is far larger than on a non-diverged run for most of the flight. In the
NIS ratio `nis = bᵀ S⁻¹ b`, BOTH the residual `b` (which should itself grow as the linearisation
point drifts from the true state) and `S` grow on a diverged run; this diagnostic has not measured
which effect dominates, so no claim is made about the NET direction of the resulting NIS. **The
claim that IS supported: a near-zero rejection rate on a diverged run cannot, by itself, be read as
"the gated-against factors are well-matched to the model"**, because the gate's own reference
covariance is itself a product of the same divergence, not an independent check on it. This
compounds, rather than contradicts, the separate `n_flow_gp_replaced` finding in Section 4 (83.1% of
1A-blank's counted flow factors are pre-takeoff synthetic values, from BEFORE the divergence even
begins): between the two effects, only a minority of 1A-blank's already-tiny flow-factor count
(1366, against textured's 89490) is both a real, airborne measurement AND gated against a covariance
that has not been affected by the divergence this section describes. No attempt was made here to
isolate that minority, or to determine whether `b` or `S` dominates the net NIS effect on these
floors (either would need a per-keyframe timeline, not built in this stage); flagged as a limitation,
not resolved, and not something Section 4's stated percentages should be read past without this
caveat.

**Limitation: a NaN NIS would be silently counted as accepted.** `S = A P Aᵀ + I` cannot itself be
singular from a finite, positive-semi-definite `P` (`A P Aᵀ` is PSD, so `S >= I`, strictly positive
definite, and `S⁻¹` exists), so a NaN or infinite NIS, if one ever occurred, would have to come from
a non-finite `A`, `b` or `P` upstream (for instance an overflowed linearisation on a sufficiently
diverged trajectory), not from an ill-conditioned-to-singular `S`. Whether that upstream
non-finiteness occurs anywhere in this run set was NOT checked (`np.isnan`/`np.isinf` over the
stored per-keyframe NIS values was not run, since the per-keyframe values were not retained by this
stage's instrumentation, only the aggregate counts). Every comparison in this diagnostic's own code
(`eval/fgo_gate_count.py`'s `nis > GATE_C`) would evaluate `False` for a NaN input in Python,
counting it as accepted rather than flagging or excluding it. So a silent NaN-as-accepted count
cannot currently be ruled out on the most severely diverged runs; listed as a limitation, not a
finding either way.

## 7. Fusion-order caveat (restated from the design note, not re-measured here)

Both the flow gate and the range gate are evaluated against the SAME pure-IMU-only predictive
covariance `P_pred` (design note Section 2.1.1). EKF3's own `UpdateFilter()`
(`AP_NavEKF3_core.cpp:663,677`) runs yaw/mag fusion, then `SelectVelPosFusion()` (which includes the
rangefinder height fusion), then `SelectFlowFusion()`, so EKF3's actual flow NIS test uses a
covariance already corrected (shrunk) by that cycle's own height fusion, which this diagnostic's
flow gate does not reproduce.

**The direction of the resulting bias is known, even though its magnitude is not quantified here.**
A Kalman-style fusion step never increases covariance, so the TRUE, height-corrected covariance
EKF3 would use is less than or equal to the pure-IMU `P_pred` this diagnostic substitutes for it.
In the NIS formula (design note Section 2.2), `S = A P Aᵀ + I`: a LARGER `P` gives a LARGER `S`,
and `nis = bᵀ S⁻¹ b` therefore comes out SMALLER than it truly would with the height-corrected `P`.
**So this diagnostic's flow-gate NIS values, and therefore its flow rejection counts, are biased
LOW (under-counted) relative to what EKF3's own fusion-order would actually produce**; every
rejection percentage in Section 4 should be read as a floor, not a best estimate, of what a
correctly-ordered gate would reject. This is consistent with, and plausibly contributes to (though
does not fully explain, Section 8's window mismatch is a separate factor), the large gap between
this diagnostic's 0.02% and EKF3's own measured 7.5% on `dsn_tex_r1` (Section 8). A "range-updated
P" variant was scoped in the design note (Section 8 item 3) but was not built, per the registered
run set (D137: "no verdict depends on the count"); quantifying the bias's magnitude is therefore
left open, not resolved here.

## 8. Comparison against the recorded EKF3 / UKF rejection rates on the same data, where they exist

**Only one such figure exists in this project, and it is for exactly one of the 15 set-1A trials.**
`METHODOLOGY.md:407` (section "flow/yaw" finding, nomag): measured directly from `dsn_tex_r1`'s own
dataflash log, **EKF3's own nomag flow rejection is 7.5% (`XKF5 NI>=100`, 236/3153 airborne; mean 43,
p99 150)**. The same passage reports the UKF's own gate on the same trial: the corrected
(interval-averaged omega) UKF rejects ~2% of flow (lateral axis); an earlier, uncorrected UKF
baseline rejects ~29% (lateral axis), flagged there as itself a divergence from EKF3's behaviour,
not the comparison point.

**`METHODOLOGY.md:413`'s own caveat applies here too, stated again rather than dropped:** EKF3's `NI`
is a COMBINED 2-axis ratio; the UKF's own gate (and this diagnostic's per-axis gate) is per-axis, so
the percentages are not directly comparable number-for-number, though the ordering (uncorrected UKF
29% >> EKF3 7.5% > corrected UKF 2%) is reported there as robust. This diagnostic's own joint-NIS
column (Section 2.4 of the design note, gate 9 or 11.83) is the more directly comparable quantity to
EKF3's combined `NI`, not the per-axis columns.

**For `dsn_tex_r1` specifically, this diagnostic's own joint-NIS rejection rate is: 0.02% (2/10018
flow factors) at BOTH the naive gate 9 and the chi2(2) gate 11.83** (the two agree exactly on this
trial), against EKF3's measured 7.5% (236/3153 airborne, combined, same trial, same floor
condition), nearly three orders of magnitude lower.

**Two caveats specific to this comparison, checked rather than assumed, and one earlier draft of
this section got the first one wrong (corrected here):**

- **Checked directly from `dsn_tex_r1`'s own PARM dump: `AHRS_EKF_TYPE = 10`.** Per the project's
  standing decision (CLAUDE.md "Hidden Configuration Audit" §1), this means the FLOWN trajectory on
  `dsn_tex_r1` was driven by simulator ground truth, not by EKF3's own estimate; EKF3 is passive
  here, exactly like the FGO. **An earlier draft of this section incorrectly stated that EKF3 "was
  itself gating against its own trajectory, which the controller then flew to" on this flight; that
  is wrong for `dsn_tex_r1` specifically and has been corrected.** Both EKF3's 7.5% and this
  diagnostic's 0.02% are therefore measured on the SAME flown trajectory, not two different ones.
  What genuinely differs, and is not corrected for, is the COVARIANCE each gate uses: EKF3 gates
  against its own real, sequentially-updated filter covariance, carried forward and corrected every
  cycle over the whole flight (yaw/mag, then height, then flow, within one cycle, Section 7 above);
  this diagnostic gates against a pure IMU-only predictive covariance with no memory of any prior
  correction (design note Section 2.1). Section 7's one-sided bias (now stated with direction, see
  above) is exactly this effect, not a trajectory difference.
- **The two counts are also not over the same window, and the mismatch pushes in a known direction.**
  EKF3's 7.5% is 236/3153 AIRBORNE `XKF5` rows only, logged at roughly 10 Hz (3153 rows over a
  flight of about 300 s; `XKF5` is not logged at EKF3's own ~80 Hz internal predict rate). This
  diagnostic's 10018 flow factors cover the WHOLE replay at the FGO's ~30 Hz keyframe cadence,
  including the pre-arm/ground period, of which 584 (5.8%) are the pre-takeoff
  `GroundProximityFlow`-substituted synthetic value (Section 1), not a raw measurement at all, and
  are not "airborne" in EKF3's sense. Those 584 synthetic factors sit in THIS diagnostic's own
  denominator, not EKF3's, so including them can only ever push this diagnostic's percentage DOWN
  relative to an airborne-only comparison, the same direction as the 7.5%-vs-0.02% gap.

A numeric gap between 7.5% and 0.02% is therefore not attributable to "the FGO's factors are more/
less often extreme" alone, and specifically not to a different flown trajectory (that explanation is
ruled out directly above); the covariance-propagation difference (Section 7, which biases this
diagnostic's count DOWN) and the window mismatch (which also biases it DOWN) are candidate
contributors, not a quantified decomposition of the gap, which this diagnostic has not attempted.
Reported for completeness, not as a comparison this diagnostic is positioned to adjudicate.

**No other published EKF3 or UKF flow-rejection rate was found, on a search wider than the two
METHODOLOGY/numbers.md documents checked in an earlier draft of this section.** Also checked: the
stored per-trial `ekf3/of.npy` arrays (continuous flow values, not a rejection flag or count, across
all 33 trial directories, confirmed by inspecting `dsn_tex_r1`'s own array directly rather than
assumed), every stored `ukf*/metrics.txt` and `ukf*/fwd_stats.json` (the latter's `gate: 9.0` /
`psi_fused` / `omega_fused` fields are the forward-camera HEADING/yaw-rate fusion gate, not the
downward-flow gate), and `docs/thesis/ekf3_heading_replay/` (the D139 EKF3-heading-Replay
innovation-extraction documents, which cover the forward-camera heading innovation, not downward
flow). None of these hold a flow rejection count or rate. This section is therefore not extended to
the other 59 runs for that reason, not because they were not checked for one.

## 9. Checksum guard and cleanup

**The first snapshot attempt had a real coverage bug, found during review, not assumed fixed.**
`tools/tier1_checksum_guard.py`'s `--paths` option is `nargs="+"` (one flag, many values), but it was
invoked as `--paths dir1 --paths dir2 ... --paths dir33` (33 separate `--paths` flags). Argparse's
default `store` action means each repeated `--paths` OVERWRITES the previous one, so only the LAST
directory (`fwdplainc_blank_r3`) was actually captured: the written manifest holds 83 files, 111.8 MB,
which is one trial's worth, not 33. This was not caught at the time (the file count looked plausible
in isolation) and is corrected here rather than left standing.

**What actually establishes nothing in the 33 trial directories changed, given the broken snapshot:**

1. **A retroactive mtime/ctime check against the (still correctly-timestamped) broken snapshot
   file**, taken at 2026-11-12T02:13:10, before any heavy compute in this stage (the 1B byte-identity
   proof and the full run set both started after this): `find <33 dirs> -newer checksum_before.json`
   and `-cnewer` both return ZERO files. Any write to any of the 33 trial directories during this
   stage's whole run would have updated at least one file's mtime or ctime; neither check found one.
   **Checked that this zero is not vacuous (a wrong path would also return zero)**: the same 33
   directories, with `stderr` NOT suppressed this time, give `find <33 dirs> -type f | wc -l` = 3045
   (exactly matching item 2's full snapshot's own file count below) and
   `find <33 dirs> -type f ! -newer checksum_before.json | wc -l` = 3045 too, i.e. every one of the
   3045 files that exist is accounted for and none is newer than the marker. This is real, if
   indirect, evidence, not the intended per-file hash comparison.
2. **A full, correctly-covered snapshot taken now** (single `--paths` call, all 33 directories as
   space-separated arguments to it): 3045 files, 8874.6 MB, written to
   `~/thesis_data/diagnostics/fgo_gate_count/checksum_after_full33.json`. `verify` against itself
   confirms the tool and the correct invocation work:

```
snapshot: 3045 files in 1 groups ({'custom': 3045}), 8874.6 MB, 22.6 s
verify: 3045 files against .../checksum_after_full33.json: IDENTICAL
```

This full snapshot is an AFTER-the-fact baseline (taken once all runs had already completed), not a
before/after hash comparison across the whole run set; it does not by itself prove nothing changed
during the runs. Combined with item 1's independent mtime/ctime evidence, and with the diagnostic's
own write-path design (`eval/fgo_gate_count.py`'s `_assert_safe_out_root` refuses any write outside
`~/thesis_data/diagnostics/fgo_gate_count/`, and `_ensure_bag_readable` only ever READS a trial's
`.db3.zst`, decompressing to a scratch copy elsewhere, never writing back), this is the evidence
actually available for this stage, stated plainly rather than overclaimed as a full hash-verified
"IDENTICAL" the way the (broken) one-trial snapshot's `verify` result would have misleadingly implied.
**Correction, not withdrawn**: an earlier draft of this document reported "IDENTICAL, no trial
directory changed" on the strength of the broken one-trial snapshot alone; that specific claim was not
supported by what the guard actually covered, and has been replaced by the evidence above.

`python3 tools/check_numbers_frozen.py` also PASSes (unaffected regardless, since
this diagnostic never touches `numbers.md`, but run and recorded per the brief):

```
PASS: numbers.md above '## Errata' sha256 6a77b9abf19b668c6b9e11e021b460c11b4cc7ca844b75193a7a96e18fe17b5a (frozen 6a77b9abf19b668c6b9e11e021b460c11b4cc7ca844b75193a7a96e18fe17b5a)
ok: frozen commit 669f099 has the frozen content
```

**Cleanup.** Every run touched a trial's bag via a decompressed scratch copy under
`~/thesis_data/diagnostics/fgo_gate_count/bagcache/<trial>/` (`eval/fgo_gate_count.py`'s
`_ensure_bag_readable`, never the trial's own `bag/`). This grew to 56 GB across all 33 distinct
trials touched by the full run set, far more than the design note's Section 5.3 estimate of 1.5-2
GB, because the `fwdc_*`/`fwdplainc_*` bags also carry recorded forward-camera frames (CLAUDE.md:
"`run_trial.sh` enables forward-camera recording for all four suffixes"), unlike the `dsn_*` bags
the original estimate was anchored to. **Removed in full after both run sets completed** (`rm -rf
~/thesis_data/diagnostics/fgo_gate_count/bagcache`, confirmed by `ls` returning "No such file or
directory" immediately after; this removal happened before the checksum-coverage bug above was
found, so the later corrected 33-directory snapshot was taken on a machine with the cache already
gone, which does not affect it either way since `bagcache/` sits under this diagnostic's own
directory, never under any of the 33 trial directories the snapshot covers).
`~/thesis_data/diagnostics/fgo_gate_count/runs/` (161 MB, the
diagnostic's own instrumented-replay TUM/export outputs, not a bag cache) and `byte_identity/`
(11 MB, the two byte-identity proofs' control/instrumented outputs) were kept, since they are this
diagnostic's own small, legitimate evidence artefacts, not a decompressed copy of anything.
