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

## Lateral-flow derotation coupling — characterised; two fixes refuted by the empirical gate; leak mechanism quantified (acceptance-driven, unobservable-yaw); nomag ordering null

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

**Status — correction APPLIED 2026-08-01, by decision.** The interval-averaged gyro is
now fed to `h_flow` in **both** the UKF and FGO (shared `FlowFrameGyroAverager` in
`measurement_models.py`; the `h_flow` math is unchanged — only the ω it derotates against
is now the flow-frame average). The sign flip stays **reverted**. The mechanism is
quantified (FINDING 4): the correct, EKF3-faithful derotation whose estimator payoff,
under unobservable yaw, is dominated by an **acceptance-driven flow→yaw leak** that scales
with flow volume (~71–75% of its nomag textured degradation is the extra flow its correct,
smaller innovations let past the gate, not the ω values). No admissible measurement-side
lever removes that leak (the gate and `R` are EKF3-matched; tuning them is the fairness
violation) — the only admissible avenue is a filter-formulation change to the unobservable
direction (OC-UKF/FEJ), a research direction.

**DECISION — apply the correction (reasoning, for the record).** Applied despite it
degrading nominal (flow-rich) nomag evo −a, because keeping a known-incorrect derotation
because it produces better numbers is not defensible; the correct implementation is.
Three grounds: (1) it is the **geometrically correct** derotation (FINDING 1: it takes the
lateral residual roll-coupling from −2.09 toward EKF3's −0.15); (2) it **restores
EKF3-consistent gating** — the baseline rejects ~29% of lateral flow where EKF3 rejects
7.5% (`XKF5 NI≥100`) and the corrected UKF ~2%, so the baseline was the divergence, not the
fix; (3) it **touches no tuned parameter** — `FLOW_GATE` stays at EKF3's 300; acceptance
rises only because correct innovations are smaller. **Honest cost, re-measured across nine
bags (n=1 each):** textured (the tracking regime) UKF **16.44 → 19.96** evo −a, FGO
4.87 → 5.46 — the fix degrades both flow-rich cases, as FINDING 4 predicts. Also bundled
in: **PHYS_DRIFT corrected** — SITL's gyro-z drift is a triangle wave (slope 3.0 deg/min
per min, `sitl_gyro_drift`), not the constant 9.8 (a window mean); bias % now against the
instantaneous true bias.

**Derotation architecture (code-path verified — `[VERIFIED file:line]`).** All three
estimators receive **identical raw, un-compensated flow**: `flow_bridge.py:126-137`
sends the flow rates only (`flow_rate_x = −flow_x_rad`, `flow_rate_y = +flow_y_rad`),
with **no gyro fields** (`flow_x/y` and `flow_comp_m_x/y` are zero; OPTICAL_FLOW carries
no vehicle-gyro field). Each estimator then derotates internally, but on a **different
side of the residual**: EKF3 derotates on the **measurement side** using its own AHRS
gyro — `bodyRadXYZ = gyro − flowGyroBias`, `flowRadXYcomp = flowRadXY + bodyRadXYZ`,
and the fusion uses the compensated `flowRadXYcomp` (`AP_NavEKF3_Measurements.cpp:206-228`,
`AP_NavEKF3_OptFlowFusion.cpp:458,619`); it is **active** in this config (`FLOW_OPTIONS = 0`,
so the `Stabilised` bit that would zero `bodyRate` at `AP_OpticalFlow_MAV.cpp:71` is
unset). The UKF and FGO derotate on the **prediction side**, inside `h_flow` (the
`flow_x_rot = −rollspeed` term). Same job, two code paths. **EKF3 is not pre-derotated
externally, and its compensation is not disabled to level it down.**

**FINDING 1 — the residual asymmetry is real and established (like-for-like, EKF3 vs
`h_flow`).** The earlier innovation-based comparison (EKF3 `FIX` +0.03 vs UKF ν +0.71)
was **not** like-for-like — a post-derotation innovation against a full-model one — and
is not relied on. The settling test reconstructs both estimators' lateral derotation
residual against a **common GT reference** (`residual = derotated-flow − translational-
flow(GT)`) on `dsn_tex_r1`:

| | roll-rate corr | slope vs rollspeed | std |
|---|---|---|---|
| **EKF3** (`flowRadXYcomp − losPred(GT)`) | **−0.09** | **−0.15** | 0.48 |
| **`h_flow`** (UKF/FGO) | **−0.95** | **−2.09** | 0.60 |

EKF3's lateral residual is **roll-decoupled**; `h_flow`'s is strongly roll-coupled — so
the residual is common-mode across the UKF and FGO (identical `h_flow`) but **NOT** shared
by EKF3. **Mechanism:** the raw flow's rotational content is the body rate *integrated
over the camera frame* then divided by `dt` (`flow_tracker.py:223-227`, `flow_x_px_s =
mean_dx/dt`), i.e. the gyro **averaged over the frame interval**. EKF3 cancels it with the
same interval-average — `bodyRadXYZ` from `rawGyroRates = gyro_sum/gyro_sum_count`
(`AP_OpticalFlow_MAV.cpp:38-42,76`), fused as `flowRadXYcomp` (`Measurements.cpp:206,227`);
`h_flow` used the **instantaneous** rate. Roll oscillates faster than the 30 Hz frame rate
(cruise rollspeed std 0.40 rad/s), so the two are not equivalent and the instantaneous
rate leaves the coupling. EKF3's `flowGyroBias` LP (`Measurements.cpp:193`, ±0.1 rad/s,
~3 s constant) touches only the mean, not the fast coupling. (EKF3's residual **std** 0.48
is not itself small — a shared lateral noise floor both carry — and is partly inflated by
GT-reference differentiation in the reconstruction; the roll-rate **coupling** is the
robust diagnostic, not the absolute std.)

**FINDING 2 — but it does not disadvantage the UKF/FGO; removing it degraded the UKF
(empirical gate, a substantive result).** Feeding `h_flow` the interval-averaged gyro
(co-sampled `/imu/data_raw`, 333 Hz, averaged over the exact frame window `(prev,current]`
— no free offset: the flow stamp *is* the capture time, `flow_tracker.py:296`) drops the
offline residual slope −2.09 → −1.24 (std 0.60 → 0.40). Gated on a from-scratch UKF
re-run (`dsn_tex_r1`, n=1), it **degraded every outcome metric**:

| | instantaneous ω (baseline) | interval-averaged ω |
|---|---|---|
| ATE (evo `-a`) | **11.69** | 21.58 |
| yaw drift (deg/min) | **+12.4** | +32.9 |
| gyro-z overshoot (% of 9.8) | **222%** | 494% |
| lateral (X) flow acceptance | 71% | **98%** |

**Mechanism — gating under unobservable yaw.** The instantaneous-ω residual is roll-
coupled and noisy (std 0.60), so the innovation gate was **rejecting ~29% of lateral
flow**. Interval-averaging makes it model-consistent (std 0.40), so lateral-flow
acceptance rises **71% → 98%** (the forward axis was already ~98% and unchanged). With
**no yaw source**, a lateral-flow discrepancy has no observable home and **leaks into
yaw** (the `flow_x`→yaw partition, §"FINDING — the UKF yaw drift…"): so *more* lateral
flow → *more* yaw drift and gyro-z overshoot. The gate was **incidentally protecting the
filter from its own flow→yaw leak** by rejecting the coupled flow; removing the coupling
removed the protection. This is the **OC-UKF / FEJ failure mode** — spurious information
gain in a weakly/unobservable direction — surfacing as a *gating* effect: a cleaner, more
self-consistent measurement is *worse* when the estimator cannot observe where its
discrepancy belongs. (Connects to the measured overconfidence result, §"Filter
consistency".)

**FINDING 3 — effect on the comparison is null.** The three-way ordering **stands** and
the headline ("formulation differences wash out under degraded sensing") does **not** need
re-establishing. The EKF3-vs-UKF/FGO residual asymmetry is geometrically real but does
**not** disadvantage the UKF/FGO: on nomag the instantaneous-ω result is the UKF's *better*
case, the "fair" interval-averaged version its worse one (this **reverses** on the
compass-active `ds_tex_r1` — see FINDING 4). The UKF's dominant error is the
**unobservable-yaw leak, not the derotation residual**. (n=1, `dsn_tex_r1`, UKF, at the
time this was written; the correction has **since been applied and re-run across all nine
bags** — the qualitative ordering holds (textured EKF3≈FGO with the UKF worse; degraded
conditions all diverge), see Status/DECISION and the updated three-way table.)

**FINDING 4 — mechanism quantified: the leak is acceptance-driven, the correction is
geometrically sound but flight-dependent, and no admissible gate lever fixes it.** *Method
— the matched-acceptance decomposition* (the tool the two failed fixes lacked). The
interval-average bundles two changes: the ω values in `h_flow`, and — because smaller
innovations pass the χ² gate more often — a higher flow-acceptance rate. Config B isolates
the second: it loosens the gate with the *baseline* (instantaneous) ω until acceptance
matches the fix, changing derotation not at all.

*`dsn_tex_r1` (evo −a; config A reproduces the committed baseline exactly — harness validated):*

| # | ω | acc_X | evo −a | yaw drift |
|---|---|---|---|---|
| A baseline | instantaneous | 72.5% | 11.69 | +12.4 |
| B *more-flow only* | **instantaneous** | 99.6% | 18.70 | +27.7 |
| C fix | interval-avg | 99.6% | 21.58 | +32.9 |

**~71% of the evo −a loss and ~75% of the yaw-drift loss is the additional accepted flow
at unchanged derotation (A→B); the ω values add only the remaining ~25–29% (B→C).** Leak
path confirmed, not inferred: acc_Y (forward) stays pinned at 100% in every config — only
acc_X (lateral) moves — and the cumulative **absolute per-update yaw correction on the X
channel** rises 196° → 362° (A→B) while the Y channel's stays flat (88° → 76°). So the
extra accepted flow is entirely lateral and it is the lateral channel that pumps yaw.
(196→362° is a cumulative |Δyaw| *magnitude* — how hard the X updates push yaw — not net drift.)

*The correction is geometrically sound but flight-dependent — the compass-active `ds_tex_r1`
inverts the SIGN of its effect:*

| # | ω | acc_X | evo −a | yaw drift |
|---|---|---|---|---|
| A baseline | instantaneous | 76.2% | 19.90 | −23.4 |
| B *more-flow only* | **instantaneous** | 99.9% | 31.94 | +50.1 |
| C fix | interval-avg | 99.9% | **8.72** | −5.8 |

Isolating the ω correction at matched acceptance (B→C): on `dsn` slightly harmful (+2.9
evo −a), on `ds` a large benefit (−23.2). **More acceptance hurts both flights (+7 dsn,
+12 ds — the leak is on both); the correction itself helps `ds`, is ~neutral on `dsn`.**
So the correction is *not wrong on its own terms* — it is the right derotation whose
estimator payoff, under unobservable yaw, is set by a flight-specific accident: the
*uncorrected* roll-coupled residual biases yaw drift by a flight-dependent sign (hurting
`ds`, mildly helping `dsn`). (n=1 per flight; `ds_tex_r1` runs in a high-error regime;
B→C acceptance matches to ~0.4%.)

**The corrected config is MORE faithful to EKF3 at the gate, not less** — this inverts the
intuition that applying the correction breaks the EKF3 match. The correction never touches
the gate threshold (`FLOW_GATE`=300, EKF3's value, identical in A and C); acceptance rises
only because the correct derotation shrinks the innovations, and a χ² gate *should* accept
a more model-consistent measurement. Measured on the same `dsn_tex_r1` `.BIN`: **EKF3's own
nomag flow rejection is 7.5%** (`XKF5 NI≥100`, 236/3153 airborne; mean 43, p99 150). The
corrected UKF rejects ~2% (lateral); the **baseline ~29% (lateral) is the outlier** — its
high lateral rejection is a *divergence* from EKF3 caused by the roll-coupled residual
inflating its lateral innovations. The correction *restores* EKF3-consistent gate behaviour;
the baseline is right-for-the-wrong-reason on nomag. (Caveat: EKF3's `NI` is a combined
2-axis ratio vs the UKF's per-axis gate, so the percentages aren't directly comparable —
but the ordering baseline 29% ≫ EKF3 7.5% > corrected 2% is robust.)

**No admissible lever removes the nomag degradation.** Clawing acceptance back means
tightening the gate below EKF3's 300 or inflating `R` below `FLOW_M_NSE`=0.25 — both
EKF3-matched, so tuning either *is* the fairness violation. The only admissible way to
handle the flow→yaw leak is a *filter-formulation* change to the unobservable direction
(observability-constrained / FEJ update) — legitimate under §9.5 as a formulation
difference, but a research direction and itself an EKF3 divergence, not a measurement-model
tweak. Whatever is decided propagates to the FGO through the shared `h_flow` and the same
no-yaw gate, unassessable without a re-run.

**Metric arbiter — evo −a, not apparatus.** More flow *improves* apparatus ATE
(81.8 → 46.4 → 40.8, A→B→C) while *worsening* evo −a (11.7 → 21.6) and yaw drift
(12.4 → 32.9). The disagreement is real. evo −a arbitrates: (1) the three-way is reported
in evo −a and the STANDING RULE forbids mixing metrics, so any change must be judged in it
to be comparable; (2) under nomag the *constant* yaw offset is unobservable (arbitrary
yaw0) — apparatus penalizes it, evo −a aligns it out but retains yaw *drift*, the real
error. Decomposing the apparatus gain (RMS error, `dsn`): along-track (N, travel)
54.8 → 33.9 → 33.7 **and** cross-track (E) 60.7 → 31.7 → 23.1 — *both* shrink, so the gain
is a genuine absolute-position improvement (more flow → better velocity scale), *not* an
along-vs-cross artifact. But it rides on a worse SE(3)-aligned *shape*: **the fix trades
heading for position**, and evo −a — which cannot align out drifting yaw — is the metric
that reflects the heading failure the nomag comparison is about. Apparatus measures a real
position gain; it is simply the wrong arbiter for nomag estimator *quality*.

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

**This gate has now caught TWO offline-evidenced changes — it has earned its place
twice.** (1) the sign flip (three offline lines), and (2) the interval-averaged gyro (a
correct geometric fix matching EKF3's *own* mechanism, residual slope −2.09 → −1.24,
FINDING 2 above) — **both refuted by the from-scratch re-run** (each degraded ATE, yaw
drift, and gyro-z overshoot on `dsn_tex_r1`). A measurement-model change that is provably
right offline can still degrade the estimator, because the filter's state **and its
innovation gate** adapt to whatever model they are given — and under an unobservable
direction (no-yaw), a more self-consistent measurement can feed a leak the gate was
otherwise suppressing. Two independent refutations, same control: it is not a one-off.

**Lateral-vs-forward asymmetry — motion profile, not structural (settled).** `h_flow`'s
two axes are structurally near-symmetric: translational sensitivity is identical
(`∂flow/∂v = 0.571` both), rotational sensitivity differs only 1.3× (`∂flow_x/∂rollspeed
= −1.14` vs `∂flow_y/∂pitchspeed = +0.86`, from the `ω×lever` term × the `SIGN_X/Y`
convention). The 27× lateral-noise excess is **the corridor motion profile**: cruise
**rollspeed std 0.399 rad/s vs pitchspeed std 0.013 — 31×** (forward flight commands
large oscillatory roll for lateral position control, near-zero oscillatory pitch), so
the lateral rotational-flow term is ~40× the forward one. Expected and documented; not
a structural defect in the measurement model.

## Three-way comparison — first same-metric results (nomag `dsn_*`, n=1 per bag)

All three estimators on **evo `-a`** (SE3-aligned — the fair cross-estimator metric
under no compass; it removes the arbitrary init-yaw gauge the UKF/FGO carry but EKF3,
in its true NED frame, does not). EKF3 from `XKF1`-vs-`SIM`; UKF/FGO from their TUM
trajectories vs `/ground_truth/pose`.

**Corrected `h_flow` (interval-averaged ω, 2026-08-01) — re-run across all nine bags:**

| condition (regime) | EKF3 | UKF (gated) | FGO (0.25 s) |
|---|---|---|---|
| **textured** *(tracks)* | 4.97 | 19.96 (rng 15.0) | **5.46 (rng 0.4)** |
| **transition** *(under-travel)* | 23.41 | 17.48 (rng 18.8) | 28.93 (rng 0.4) |
| **blank** *(diverges)* | 37.79 | 16.05 (rng 0.9) | 30.48 (rng 1.3) |

(mean of 3 repeats, evo `-a` RMSE in m. EKF3 unchanged — the correction is prediction-side,
UKF/FGO only. Uncorrected values were UKF 16.44/27.11/39.84, FGO 4.87/24.55/43.28 —
**superseded**.) Yaw drift (deg/min): EKF3 ~8, **FGO −9 in every condition** (anchor-locked),
**UKF now flow-dependent** — textured +14…+41, blank −1…−7 (the FINDING-4 leak scaling with
accepted flow). The FGO's position metrics *did* move (textured 4.87→5.46, blank 43→30), so
the flat FGO yaw is its per-keyframe anchor dominating, not a no-op.

- **Read by regime — displacement magnitude vs true 151 m, frame-independent:** textured
  is the **tracking** regime (FGO 0.98, EKF3 tracks; UKF 0.58 — yaw-drift *curving* the
  path, the leak); transition **under-travels** (0.6–1.0, loses the blank half); blank
  **diverges** — all three *over-travel* (UKF 200 m, FGO 247 m vs true 151) on garbage
  starved flow. **The old "formulation differences wash out under degraded sensing" is
  restated: all three DIVERGE under flow starvation.**
- **Do NOT read the blank/transition evo −a as a quality ranking.** UKF blank 16 < EKF3 38
  is "diverges *less far* after SE(3) alignment," not a quality win — every estimator has
  failed there. Only the **textured** row is a tracking-regime comparison: **EKF3 ≈ FGO
  (~5 m); the UKF is ~4× worse (20 m)** — the flow→yaw leak, worse than before (16.4→20.0)
  under the correct derotation, exactly as FINDING 4 predicts for a flow-rich case.
- **The UKF is unstable across repeats on flow-bearing conditions** (textured range 15,
  transition range 19) while the **FGO is tight everywhere** (ranges ≤1.3) — the leak makes
  the UKF's evo −a repeat-sensitive; the smoother's anchor does not.
- **evo `-a` is the only fair cross-estimator metric**, and even it is not a clean quality
  metric in the divergence regime. Unaligned is NOT comparable (EKF3 true frame vs UKF/FGO
  ~90° init-yaw gauge).

**Caveats.** n=1 per bag. Under the corrected `h_flow` the neat four-estimator yaw
clustering (EKF3 8.4 / FGO 9.24 / UKF-uncond 9.52 / UKF-gated 12.7, all near physical
9.8) **no longer holds for the UKF** — the corrected UKF drifts +14…+41 on textured (the
amplified leak). The FGO and EKF3 still sit near physical; the UKF now separates. This is
a first pass, not the final comparison.

### Gyro-z bias ramp-tracking — the bias is effectively unobservable under no yaw (a result)

SITL's gyro-z drift is a **triangle wave** (`sitl_gyro_drift`, slope 3.0 deg/min per min,
validated vs recorded gyro-z to ~0.2 deg/min), so the right test is whether each estimator
**tracks the ramp**: `d|bias|/dt` vs the true ~2.8 deg/min per min (windowed; 3.0 ideal).
Across all nine bags:

| estimator | d\|bias\|/dt (deg/min/min) | |bias| vs true | reads as |
|---|---|---|---|
| EKF3 | 0.1–0.3 | 4–29% of true | barely tracks; holds bias ~0 |
| FGO | ≈0 (±0.06) | 0–7% | does **not** track; bias pinned ~0 |
| UKF | +1.5…+2.1 tex, **−0.5…−0.7 blank** | 34–650% | "tracks" on textured but by the leak — overshoots 3–6×, **ramps the wrong way on blank** |

**Read:** the gyro-z bias is effectively **unobservable under no yaw** for all three. EKF3
and the FGO leave it near zero (so their yaw drifts at ~the physical rate, EKF3 ~8 / FGO
−9); the UKF's bias is **not an observation but the flow→yaw/bias leak** — it moves with
accepted flow (chases the ramp on textured, ramps *backwards* on blank), which is why its
magnitude overshoots and its yaw drift scatters. None of the three genuinely observes the
drift ramp.

### Parameterisation-independence — re-established under the corrected `h_flow` (three-part verdict)

The headline finding (yaw leak is **capping-controlled, not a parameterisation effect**)
was measured with the uncorrected model; re-checked against the correction:

1. **The 69/31 partition (Euler-UKF = SO(3)-FGO) SURVIVES.** The correction changes ω (an
   input), and the flow Jacobian columns that set the velocity/yaw partition are
   **ω-invariant to machine precision** (only the `p_U`/height column moves, via the
   lever-arm ÷ h_cam coupling). So the partition is unchanged, for both parameterisations
   (same `h_flow_pose`). *Measured* on the UKF Euler side; *argued* on the FGO side (shared
   model), not separately re-measured.
2. **"All drift near physical 9.8" does NOT survive** for the corrected UKF — it drifts
   +14…+41 on textured (the amplified leak). The tidy four-estimator clustering breaks; the
   FGO (−9 everywhere) and EKF3 (~8) still cluster, the UKF no longer does.
3. **The capping attribution SURVIVES and strengthens** — distinct from (1). The *same*
   geometric correction, applied identically to both, hits the weakly-capped UKF hard
   (yaw +12→+33 textured) and the per-keyframe-anchored FGO not at all (−9.24→−9.31). If
   parameterisation drove yaw, an identical geometric change would affect both alike; it
   does not, so the discriminator is the **capping mechanism** (UKF rare variance-gated cap
   vs FGO per-keyframe weak prior), not Euler-vs-SO(3). Net: the parameterisation-
   independence finding holds; only the incidental "near-physical" numerical coincidence
   for the UKF is lost.

### FGO configuration — window is a declared config choice, not a default

**The FGO's fixed-lag window (0.25 s) is a deliberately-set config value, declared as
such** — unlike EKF3, which runs at literal ArduPilot defaults. It was **not** chosen
for accuracy. Sequence: FGO_DESIGN §6 pre-registered 1.0 s, which measured 96 ms/step
and **violates the pre-registered 33 ms deployability budget**; the window sweep
{1.0, 0.5, 0.25} s was then run and **0.25 s selected as the largest window meeting
that budget** (0.5 s = 48 ms is over). Cherry-picking is ruled out because **ATE is
window-independent** — evo `-a` 5.10 / 5.07 / 4.23 m at 1.0 / 0.5 / 0.25 s, so the FGO
is ~equally accurate at any window and 0.25 s merely also happens to be (mildly) best.

**Solver + timing (reported honestly).** The primary solver is `BatchFixedLagSmoother`
(iSAM2-incremental is unusable — GTSAM `marginalizeLeaves` cascades on the Python flow
`CustomFactor`, FGO_DESIGN §6). Step-time scales ~O(window): **96 / 48 / 27 ms** at
1.0 / 0.5 / 0.25 s. **The FGO meets the 33 ms deployability budget ONLY in its
short-window (0.25 s) configuration — a real result, not a footnote:** a Python-bound
`CustomFactor` FGO is budget-compliant only at a short window; larger windows spend
compute for no accuracy gain. LM iterations are capped at 2 (warm-started); verified
against full-LM at 0.25 s — max position difference 0.11 m, **RMS 0.029 m, identical
ATE (4.23)** over 10047 keyframes — so the cap is not a truncated approximation.

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
  The drift is a **triangle wave, NOT a constant** (corrected 2026-08-01;
  `AP_InertialSensor_SITL.cpp:390-402`): period `2·DRIFT_TIME = 10` min, ramping
  0 → ~15 → 0 at slope `radians(DRIFT_SPEED=0.05)/min` = **3.00 deg/min per minute**.
  Over a cruise window it sweeps the instantaneous bias from **~1.6 to ~14.8 deg/min**;
  the "+9.8 deg/min physical drift" quoted throughout is the **window MEAN** of that ramp
  (≈8.9–9.8 depending on the window — integrating raw `IMU.GyrZ`; true yaw `SIM.Yaw`
  drifts +0.01 deg/min, confirming straight flight so it is all gyro bias). Deterministic
  and reproducible — **controlled**, not **sampled**. Bias % and ramp-tracking are now
  computed against the **instantaneous** true bias `sitl_gyro_drift(t)` (validated vs
  recorded gyro-z to ~0.2 deg/min), not the constant — see the ramp-tracking finding. (Do not confuse this with an
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
