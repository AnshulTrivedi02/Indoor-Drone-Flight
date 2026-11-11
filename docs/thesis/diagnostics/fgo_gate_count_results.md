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

**Up front: set 1B's registered size of 54 is not achievable — 9 of the 54 registered combinations
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
   stage 1. That is not the same claim as "every run in this count is accepted on this basis" —
   stage 1 never checked, for example, whether `dsn_tex_r4`-`r9` (the "confirmatory 4-10" trials)
   or any of the 54 set-1B runs were produced by code and a window matching current HEAD. Fixed:
   `cmd_run` now also runs the instrumented replay into a scratch directory, `cmp`s its TUM output
   against the trial's own stored TUM, and records `instrumented_vs_stored_byte_identical` in every
   run's summary JSON. A run whose output is NOT byte-identical to its stored counterpart is
   excluded from every aggregated count below and reported separately (Section 4).

Both fixes were exercised: the stage-1 proof (`dsn_trans_r1`, Section 6 of the design note) stands
unchanged; a fresh 1B byte-identity proof was run before set 1B started (Section 2 below); and every
one of the 69 set 1A/1B runs now carries its own per-run byte-identity result (Section 3).

## 1. FLOW_MAX one-sided sign chain: independently re-derived

Re-traced step by step, at `~/ardupilot` pinned commit `7bac20cbcc`, reading each file directly
rather than trusting the stage-1 design note's citations:

1. **`flow_bridge.py` (this repo, current HEAD):** `flow_rate_x = msg.flow_x_rad`,
   `flow_rate_y = msg.flow_y_rad` — both UNFLIPPED (confirmed by reading the file; the module's own
   comment records the 2026-09-29 lateral-sign fix, commit `2236590`, that made X unflipped).
2. **`AP_OpticalFlow_MAV::handle_msg` (`AP_OpticalFlow_MAV.cpp:118-121`):** `flow_sum.x +=
   packet.flow_rate_x; flow_sum.y += packet.flow_rate_y;` — unflipped, summed verbatim.
3. **`AP_OpticalFlow_MAV::update` (`AP_OpticalFlow_MAV.cpp:61-68,79-80`):** `flow_scale_factor_{x,y}
   = 1 + 0.001*FLOW_{FX,FY}SCALER`; `dt_used = 1.0` (since `flow_sum_is_rads` is true once any
   `flow_rate_x/y` extension field is non-zero, which is always true here); then `_applyYaw(...)`.
   `OpticalFlow_backend::_applyYaw` (`AP_OpticalFlow_Backend.cpp:38-45`) is a no-op when
   `FLOW_ORIENT_YAW == 0`. **Confirmed live, not assumed**, from a PARM dump of three trials spanning
   both run sets (`fwdc_tex_r1`, `fwdplainc_blank_r1`, `dsn_tex_r1`): `FLOW_FXSCALER = FLOW_FYSCALER
   = FLOW_ORIENT_YAW = 0.0` in all three, so `state.flowRate = (flow_x_rad, flow_y_rad)` exactly,
   unscaled, unrotated — this is `rawFlowRates` as read by EKF3's measurement-ingestion path.
4. **`AP_NavEKF3_Measurements.cpp:221`:** `ofDataNew.flowRadXY = - rawFlowRates.toftype();` — a
   negation of BOTH axes, confirmed by reading the line directly.
5. **`AP_NavEKF3_OptFlowFusion.cpp:668`:** `if (really_fuse && (flowTestRatio[obsIndex]) < 1.0f &&
   (ofDataDelayed.flowRadXY.x < frontend->_maxFlowRate) && (ofDataDelayed.flowRadXY.y <
   frontend->_maxFlowRate))` — fusion (of EITHER axis) requires BOTH `flowRadXY.x < FLOW_MAX` AND
   `flowRadXY.y < FLOW_MAX`; `_maxFlowRate` is `FLOW_MAX`, confirmed at `AP_NavEKF3.cpp:305-312`
   (`AP_GROUPINFO("FLOW_MAX", 20, NavEKF3, _maxFlowRate, 2.5f)`) — the parameter name the stage-1
   note cited is correct (not `EK3_MAX_FLOW`).
6. **`fgo_replay.py:111`:** `ev.append((tt, "flow", (np.array([m.flow_x_rad, m.flow_y_rad]), ...)))`
   — the flow array handed into the event stream is `[flow_x_rad, flow_y_rad]` directly off the bag,
   with NO negation and NO axis swap. Confirmed by reading the line (both the live-bag path at
   line 111 and the `FGO_EVENTS` dataflash-replay path at line 90-91, which reads the same
   `flow_xy` field out of a pre-converted `.npz`, already in this convention by construction of
   `eval/bin2fgo.py`, out of scope for this run set regardless since `EVENTS` mode is unused by
   `fgo_replay.py <trial> 0.25 [2 [<arm>]]`, the only invocation form used here).

**One real wrinkle, read and accounted for, not glossed over:** between step 6 and the factor
actually being added, `fgo_replay.py:203-205` can REPLACE `flow_pend[0]` via
`measurement_models.GroundProximityFlow.replace()` — but only pre-takeoff, below 0.5 m height
(`GP_HEIGHT_M`), where it substitutes a synthetic rotation-only value
(`h_flow_rot(omega_flu)`, "EKF3's `flowRadXYcomp = 0` (zero `relVelSensor`, lever arm included)" per
the function's own comment) instead of the raw measured flow, mirroring EKF3's own
pre-takeoff/zero-relative-velocity assumption. The diagnostic's `flow_xy` is read off exactly what
`fgo_core.keyframe()` receives — i.e. AFTER this replacement, for the same reason the diagnostic
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
gtsam.noiseModel.Isotropic.Sigma(1, 0.5)` — plain Gaussian, unconditionally. The only robust-kernel
path in the file (`fwd_robust`, `fgo_core.py:102-106`) wraps `heading_noise` only, is an F1
ablation-only switch, off by default, and is never set by any command in this run set (no `F_TAG`,
no `F_ROBUST` environment variable in any of the 69 jobs). The NIS formula `S = A P Aᵀ + I` (R
already folded into the whitened `A, b`) is therefore valid for every flow and range factor counted
here — a robust re-weighting would have invalidated it.

## 2. Byte-identity: stage-1 proof stands; a fresh 1B proof run before set 1B

**Stage-1 proof (`dsn_trans_r1`, no arm):** unchanged, stands as recorded in the design note Section
6.3 (control == instrumented == stored, 5340 flow factors, 10030 range factors, hook ran cleanly).

**New 1B proof, run before set 1B started, per the brief's requirement:** `fwdc_blank_r1`, arm
`heading` (line-textured walls — the wall type heading is validated on per CLAUDE.md's Sensor
Status table — blank floor, chosen as the cheapest 1B cell to prove the method on before paying for
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
(not a subset, zero internal errors) — the same non-vacuity standard as the stage-1 proof. Set 1B
was run only after this result.

(Note, not a correctness problem: this particular run's own trajectory diverges severely — logged
`[result] along-track = 24461.2 m (true 150.9) ... ATE = 9648.28 m` — a known FGO dead-reckoning
failure mode once flow aiding is effectively lost, the same category already documented for
`dsn_trans_r1` in the stage-1 design note. This diagnostic does not evaluate trajectory accuracy and
is unaffected by it; raised here only so the large along-track number in this run's log is not
mistaken for a bug in the byte-identity check itself.)

## 3. Per-run byte-identity: all 69 registered runs; 60 actually ran; 9 are N/A

Every one of the 15 set-1A and 54 set-1B runs carries its own `instrumented_vs_stored_byte_identical`
field (Section 0, fix 2), checked against `~/thesis_data/trials/<trial>/fgo[_<arm>]/fgo_traj.tum`.

**60/69 jobs ran and wrote a summary. The other 9 are NOT failures of this diagnostic — they are a
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
walls, only — never `fwdplainc_*`, plain walls). **Confirmed directly against the stored trial
directories, not just inferred from the error**: no `fwdplainc_*` trial has a stored
`fgo_heading_yawrate/` output at all (`fwdplainc_tex_r1/` has `fgo`, `fgo_baseline`, `fgo_heading`,
one F1-ablation directory — no `fgo_heading_yawrate`), while every `fwdc_*` trial does. **The design
note's Section 5.1 run-set table ("All 18 trials ... have stored `fgo_baseline/`, `fgo_heading/` and
`fgo_heading_yawrate/` directories") was wrong for the 9 `fwdplainc_*` trials specifically** — that
claim should have excluded `fwdplainc_*` x `heading_yawrate` from the start. Set 1B's REGISTERED size
(D137, "54 Phase 4 trial-arm runs") therefore includes 9 combinations that cannot exist in this
project's own code; the count of combinations that CAN exist is 45 (`fwdc_*`: 9 trials x 3 arms = 27;
`fwdplainc_*`: 9 trials x 2 arms [`baseline`, `heading`] = 18).

**All 60 runs that did produce a summary are byte-identical to their stored counterpart. Zero gate
hook errors across all 60.** (`python3 -c` check over `eval/results/fgo_gate_count/per_run.json`:
`instrumented_vs_stored_byte_identical` is `True` for all 60; `n_gate_errors` is 0 for all 60.) This
is the per-run strengthening of D134's acceptance condition (Section 0, fix 2) — not just the single
`dsn_trans_r1` and `fwdc_blank_r1`/`heading` proofs (Section 2), but every run actually counted below.

Set 1A: 15/15 ran, 15/15 byte-identical. Set 1B: 45/54 ran (9 N/A, not failures), 45/45 of those
byte-identical.

## 4. Per-set and per-run counts

See `docs/thesis/diagnostics/numbers_fgo_gate_count.md` for the full per-set table (flow per-axis/
joint/FLOW_MAX rejection counts and percentages, range rejection counts, near-threshold counts,
ground-proximity-replacement counts, byte-identity status), generated by
`eval/fgo_gate_count_numbers.py` from `eval/results/fgo_gate_count/per_set.json`
(`eval/fgo_gate_count_aggregate.py`, reading the stored per-run
`~/thesis_data/diagnostics/fgo_gate_count/*_gate_summary.json` files). 301/301 independent
cross-checks pass (`eval/fgo_gate_count_numbers.py --check`; every count and percentage in the
written table re-parsed from the markdown and compared against a freshly, independently computed
`rd()`-equivalent rounding of the JSON — not the same code path that rendered the table).

**Headline pattern, read from the table, not re-derived here:**

- **Flow rejection (gate 9, either axis or joint) is under 1% in every set-1A group, but blank is
  one to two orders of magnitude higher than textured in relative terms**: textured joint-9 ≈
  0.006% (5/89490), transition ≈ 0.33% (53/16058), blank ≈ 0.73% (10/1366) — rising monotonically
  with degradation as expected, though all three stay under 1% in absolute terms. The joint gate
  (9 vs 11.83) agrees exactly on textured and blank; on transition they differ (0.33% vs 0.23%),
  i.e. some transition-trial flow factors fall in the narrow discriminating band `[9, 11.83)`
  (design note Section 2.4) — the only floor condition in set 1A where the two thresholds give a
  different answer.
- **FLOW_MAX (2.5 rad/s) essentially never fires, one-sided or two-sided, in any set-1A group.**
  This is expected at this project's cruise speed: CLAUDE.md's own measurement puts cruise flow
  around 0.3-0.4 rad/s at 0.5 m/s forward and ~1.75 m camera height (well inside both the 2.5 rad/s
  FLOW_MAX bound and the 4.2 rad/s vector-length clamp already in the FGO's own `keyframe()`), so a
  near-zero FLOW_MAX count is consistent with the flown envelope, not evidence the check never
  applies.
- **The NUMBER of flow (and range) factors counted is identical across `baseline`/`heading`/
  `heading_yawrate` for the same wall/floor** (e.g. `fwdc` transition: 16168 flow factors in all
  three arms; `fwdc` blank: 1770 in all three) — confirming the forward-camera factors are additive
  (CLAUDE.md "Sensor Fusion Architecture"; FGO_DESIGN.md Section 9) and do not add or remove flow/
  range measurements from the stream this diagnostic counts. **But the REJECTION COUNTS on that
  same, unchanged set of factors vary substantially by arm — this was checked, not assumed, and
  the variation is large enough to be a real finding, not noise**: `fwdc` transition joint-9 goes
  69 (baseline) -> 51 (heading) -> 103 (heading+yawrate); `fwdplainc` blank axis-0 goes 8 (baseline)
  -> 61 (heading), a 7.6x jump; `fwdc` blank axis-0 goes 9 (baseline) -> 24 (heading) -> 47
  (heading+yawrate), a >5x jump base to heading+yawrate. This is consistent with Section 1's
  mechanism (the arm changes the FGO's own trajectory and therefore `P_pred` and the linearisation
  point the SAME flow factor is gated against), not with a different measurement stream being
  gated — but the size of the swing on blank floor specifically is large enough that "the forward
  factors are additive so gating is unaffected" would be an overstatement; the trajectory THEY
  PRODUCE clearly is not gating-neutral on the degraded floor.
- **`n_flow_gp_replaced` (the ground-proximity pre-takeoff substitution, Section 1) dominates the
  set-1A blank group: 83.1% of its counted flow factors (1135/1366) are the synthetic
  rotation-only pre-takeoff value, not a raw degraded-floor measurement** — against 5.0% on
  textured (4488/89490) and 8.3% on transition (1326/16058). This is because blank floor has so
  few flow factors overall (1366, against textured's 89490) that the fixed-size pre-takeoff window
  is a much larger share of what little got counted. **Any reading of "blank floor's flow factors
  are gated the same way as textured" must account for this: the large majority of what is being
  gated on blank is not even a measurement of the degraded floor.**

## 5. "Would have been rejected" — what this does and does not mean

Repeated from the design note because it is the single most important caveat: **a rejection changes
later states.** EKF3 (or the FGO, if this were ever implemented, which it has not been) re-solves
its state after a rejection differently than after an acceptance — the next prediction's covariance,
and therefore its own next NIS, would differ. Every count in Section 4 answers "would this specific,
as-actually-used factor, evaluated against the UNGATED FGO's own trajectory and IMU-only predictive
covariance, have failed this test" — not "what would a gated FGO's own, different, trajectory have
looked like". The two are different questions; only the first is answered anywhere in this
diagnostic, in either stage.

## 6. Conditioning caveat

`docs/handovers/2026-10-09_fgo_gate_conditioning.md` measured `cond(L)` (the 30x30 information
matrix `_info()` inverts — the same recursion this diagnostic reuses unmodified, Section 2.1 of the
design note) growing from 3.6e8 at the start of a flight to 1.5e12 by its end (`dsn_tex_r1`, 340 s),
with the Python-vs-C++ relative difference in the gate-trace quantity growing from 6e-8 to 5e-4 over
the same flight — both driven by backward-stable round-off amplified by that conditioning (`cond(L)`
times machine epsilon, measured there at factor 0.3-1.7), because horizontal position is
unobservable in this formulation and nothing contracts the relevant direction. This diagnostic's own
NIS values therefore carry growing numerical uncertainty late in a long flight, independent of any
bug in the gate-count hook itself. Mitigation, not a fix: every per-set group in Section 4 reports
how many NIS values fell within +/-0.1% of the relevant threshold (9, 11.83 or 25) — the count of
decisions this conditioning could plausibly flip, not a hand-wave that "numbers get noisy late in
the flight". See the per-set `near_threshold` block in `per_set.json` / the near-threshold table in
`numbers_fgo_gate_count.md`.

## 7. Fusion-order caveat (restated from the design note, not re-measured here)

Both the flow gate and the range gate are evaluated against the SAME pure-IMU-only predictive
covariance `P_pred` (design note Section 2.1.1). EKF3's own `UpdateFilter()`
(`AP_NavEKF3_core.cpp:663,677`) runs yaw/mag fusion, then `SelectVelPosFusion()` (which includes the
rangefinder height fusion), then `SelectFlowFusion()` — so EKF3's actual flow NIS test uses a
covariance already corrected by that cycle's own height fusion, which this diagnostic's flow gate
does not reproduce. This will tend to OVERSTATE the flow gate's covariance (not an understated
one), in a direction not quantified here; a "range-updated P" variant was scoped in the design note
(Section 8 item 3) but was not built, per the registered run set (D137: "no verdict depends on the
count").

## 8. Comparison against the recorded EKF3 / UKF rejection rates on the same data, where they exist

**Only one such figure exists in this project, and it is for exactly one of the 15 set-1A trials.**
`METHODOLOGY.md:407` (section "flow/yaw" finding, nomag): measured directly from `dsn_tex_r1`'s own
dataflash log, **EKF3's own nomag flow rejection is 7.5% (`XKF5 NI>=100`, 236/3153 airborne; mean 43,
p99 150)**. The same passage reports the UKF's own gate on the same trial: the corrected
(interval-averaged omega) UKF rejects ~2% of flow (lateral axis); an earlier, uncorrected UKF
baseline rejects ~29% (lateral axis) — flagged there as itself a divergence from EKF3's behaviour,
not the comparison point.

**`METHODOLOGY.md:413`'s own caveat applies here too, stated again rather than dropped:** EKF3's `NI`
is a COMBINED 2-axis ratio; the UKF's own gate (and this diagnostic's per-axis gate) is per-axis — so
the percentages are not directly comparable number-for-number, though the ordering (uncorrected UKF
29% >> EKF3 7.5% > corrected UKF 2%) is reported there as robust. This diagnostic's own joint-NIS
column (Section 2.4 of the design note, gate 9 or 11.83) is the more directly comparable quantity to
EKF3's combined `NI`, not the per-axis columns.

**For `dsn_tex_r1` specifically, this diagnostic's own joint-NIS rejection rate is: 0.02% (2/10018
flow factors) at BOTH the naive gate 9 and the chi2(2) gate 11.83** (the two agree exactly on this
trial), against EKF3's measured 7.5% (236/3153 airborne, combined, same trial, same floor
condition) — nearly three orders of magnitude lower. **A further caveat specific to
this comparison, not previously stated**: EKF3 was itself gating against ITS OWN trajectory (the
estimate it produced, which the controller then flew to, under `AHRS_EKF_TYPE != 10` for the 7.5%
figure's own flight) and ITS OWN sequentially-updated covariance (yaw/mag, then height, then flow,
within one cycle — Section 7 above), whereas this diagnostic gates the FGO's factors against a
DIFFERENT fixed ground-truth-driven trajectory (per the project's standing `AHRS_EKF_TYPE=10`
decision, CLAUDE.md "Hidden Configuration Audit" §1) and a pure-IMU-only predictive covariance. A
numeric gap between 7.5% and this diagnostic's figure is therefore not attributable to "the FGO's
factors are more/less often extreme" alone; the two numbers are not computed from the same
trajectory or the same covariance path. Reported for completeness, not as a comparison this
diagnostic is positioned to adjudicate.

No other trial in set 1A, and no trial in set 1B, has a published EKF3 or UKF rejection rate in this
project's own documents to compare against; this section is not extended to the other 67 runs for
that reason, not because they were not checked for one (`METHODOLOGY.md` and `numbers.md` were both
searched for "NI>=100", "XKF5 NI", "rejection rate" and "% rejected"; no other hit exists).

## 9. Checksum guard and cleanup

`tools/tier1_checksum_guard.py snapshot --paths <33 trial dirs>` was run before any run in this
stage (83 files, 111.8 MB, written to
`~/thesis_data/diagnostics/fgo_gate_count/checksum_before.json`). `verify` was run after both run
sets completed:

```
verify: 83 files against .../checksum_before.json: IDENTICAL
```

**IDENTICAL — no trial directory changed, added or lost a file across all 69 registered jobs (60
of which ran).** `python3 tools/check_numbers_frozen.py` also PASSes (unaffected regardless, since
this diagnostic never touches `numbers.md`, but run and recorded per the brief):

```
PASS: numbers.md above '## Errata' sha256 6a77b9abf19b668c6b9e11e021b460c11b4cc7ca844b75193a7a96e18fe17b5a (frozen 6a77b9abf19b668c6b9e11e021b460c11b4cc7ca844b75193a7a96e18fe17b5a)
ok: frozen commit 669f099 has the frozen content
```

**Cleanup.** Every run touched a trial's bag via a decompressed scratch copy under
`~/thesis_data/diagnostics/fgo_gate_count/bagcache/<trial>/` (`eval/fgo_gate_count.py`'s
`_ensure_bag_readable`, never the trial's own `bag/`). This grew to 56 GB across all 33 distinct
trials touched by the full run set — far more than the design note's Section 5.3 estimate of 1.5-2
GB, because the `fwdc_*`/`fwdplainc_*` bags also carry recorded forward-camera frames (CLAUDE.md:
"`run_trial.sh` enables forward-camera recording for all four suffixes"), unlike the `dsn_*` bags
the original estimate was anchored to. **Removed in full after both run sets completed and the
checksum verify above passed** (`rm -rf
~/thesis_data/diagnostics/fgo_gate_count/bagcache`, confirmed by `ls` returning "No such file or
directory" immediately after). `~/thesis_data/diagnostics/fgo_gate_count/runs/` (161 MB — the
diagnostic's own instrumented-replay TUM/export outputs, not a bag cache) and `byte_identity/`
(11 MB — the two byte-identity proofs' control/instrumented outputs) were kept, since they are this
diagnostic's own small, legitimate evidence artefacts, not a decompressed copy of anything.
