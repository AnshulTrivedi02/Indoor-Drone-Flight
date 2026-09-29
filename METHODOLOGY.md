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
4.79 m vs FGO 5.10 m — on par (full-window, historical; on **evo -a (cruise)**, EKF3 4.58
vs FGO 4.47 — still on par). Same-metric-only, always.

**Amended 2026-09-24: the label also names the window.** The primary cross-estimator
metric is **evo -a (cruise)**. It is computed only by `eval/three_way_eval.py`, over
one pinned window (next section). A second near-miss of the same kind prompted this.
The published three-way table had mixed windows: EKF3's textured per-repeat values
came from the cruise window, while every other figure came from the full recording.
The Phase 0 reproducibility gate caught it (see the three-way comparison section).
Figures quoted without "(cruise)" are **full-window, historical**, and are labelled as
such where they appear.

## Cruise window — pinned definition and clock sensitivity (2026-09-24)

**Definition** (`eval/three_way_eval.py`, `cruise_window()`). The window is defined
once per trial, from ground truth. The same interval is then applied to all three
estimators.
- **Source:** `/ground_truth/pose` from the bag (Gazebo truth, sim-time clock), read
  from `<trial>/ukf/ground_truth.tum`.
- **Speed:** horizontal ground speed `|d(x,y)/dt|` (`np.gradient`), smoothed by a
  **centred 0.42 s moving average**. This is the historical 25-sample boxcar at the
  ~59 Hz GT rate (dt 15–19 ms), now defined in time so it does not depend on the
  sample rate.
- **Criterion:** smoothed speed **> 0.30 m/s**. The window is the **largest contiguous
  run**, `[t0, t1]` inclusive. On the nine `dsn_*` bags it is ~30.0 → ~332.8 s
  (about 302 s of the 300 s commanded cruise, including the acceleration and
  deceleration tails above 0.30 m/s).
- **Application:** the same `[t0, t1]` in seconds is cropped out of every estimator's
  estimate **and** reference TUM.
- **Alignment:** `evo_ape -a` (Umeyama SE3, no scale) is **fitted over the cropped
  cruise span only**. Pre-arm, climb and landing are excluded from both the fit and
  the RMSE.

The only change from the historical per-estimator windows is that the boxcar is now
defined in time rather than in samples. The resulting numbers match the earlier
per-clock cruise values to ≤ 0.051 m (EKF3 only; UKF/FGO are unchanged).

**Threshold justification and sensitivity (2026-09-24).** Measured on the GT speed
profile of `dsn_{tex,trans,blank}_r1`:
- **Pre-cruise horizontal speed** (hover, climb) is ≤ 0.001 m/s.
- **In-cruise smoothed speed** has median 0.500 m/s and 1st percentile 0.497 m/s. The
  raw speed std is 0.005 m/s.
- **Acceleration** from 0.1 to 0.45 m/s takes ~0.56 s, and the stop is similar.

So any threshold strictly between hover and cruise selects the same flight segment,
differing only by where it cuts the ~0.6 s ramps. **0.30 m/s** is 60% of the commanded
0.5 m/s: well clear of hover (300× the hover speed) and of the cruise floor (0.497).
The **0.42 s boxcar** does not denoise a noisy signal (the raw speed is already clean).
It guards the "largest contiguous run" rule against a single-sample spike from
differentiation splitting the run. It is shorter than the ~0.56 s ramp, so it does
not blur the window edges materially. It keeps the historical value (25 samples at
~59 Hz) for continuity with the apparatus metrics.

**Sensitivity:** thresholds of 0.20 and 0.40 m/s on all nine bags
(`eval/results/threshold_{0.20,0.40}.json`), compared with 0.30:

| | window edges | max \|Δ evo -a (cruise)\| EKF3 / UKF / FGO, m | max \|Δ disp ratio\| | max \|Δ onset\| |
|---|---|---|---|---|
| 0.20 m/s | ±0.13–0.15 s wider | textured 0.005 / 0.038 / 0.009; trans ≤ 0.027; blank ≤ 0.046 | ≤ 0.002 | ≤ 0.4 m |
| 0.40 m/s | ±0.13–0.17 s narrower | textured 0.008 / 0.043 / 0.011; trans ≤ 0.034; blank ≤ 0.037 | ≤ 0.003 | ≤ 0.8 m |

**No conclusion moves.** The textured means stay EKF3 4.65–4.66 / FGO 4.80–4.82 / UKF
17.04–17.10, and the EKF3–FGO gap stays 0.15–0.16 m. Every failure-mode category and
onset ordering is unchanged. The window is set by the flight profile, not by the
threshold.

**Clock sensitivity — bounded, not proven.** EKF3's TUMs come from dataflash `TimeUS`.
The UKF/FGO TUMs and the window come from bag sim-time. Applying one interval to both
assumes the two clocks share an epoch. Rather than prove this formally, the check
shifts the whole window by ±0.25 s and ±0.5 s (a clock offset of that size) on all
nine bags and records the largest change in evo -a (cruise). The results
(`eval/results/phase0_cruise_pinned.json`):

| max \|Δ evo -a (cruise)\|, m | EKF3 | UKF | FGO |
|---|---|---|---|
| textured (3 bags) | 0.002–0.009 | 0.007–0.009 | 0.014–0.015 |
| transition | 0.085–0.103 | 0.004–0.016 | 0.006–0.007 |
| blank | 0.001–0.013 | 0.002–0.009 | 0.005–0.006 |

On textured, the largest change (0.015 m) is **~10× smaller than the smallest
between-estimator gap** (EKF3–FGO mean gap 0.16 m). Every UKF gap is metres. The transition maximum (0.10 m) sits in a failure
regime where the gaps are metres. The two clocks' independently computed cruise
windows already agreed to within 0.14–0.34 s. **Result: a clock offset of up to
0.5 s cannot move any cross-estimator conclusion.** This closes the Hidden
Configuration Audit §1 clock item (CLAUDE.md) as **bounded, not proven**.

**ATE window audit (2026-09-24).** Every ATE quoted in this file and in PROGRESS was
checked for which window it used.
- **Restated on cruise** (the historical full-window value is kept alongside; each
  re-run first reproduced its published full-window number exactly, and only then was
  cropped):
  - the three-way table
  - the corrected-`h_flow` before/after, all nine bags (re-run from `08bc2eb`)
  - FINDING 2 and the FINDING 4 A/B/C tables (stored `dc_*` / `dd_*` trajectories)
  - the refuted sign flip (re-run from `51aaeba^` with `+rollspeed`)
  - the FGO window sweep (re-run from `08bc2eb` at 1.0 / 0.5 s)
  - the first fair-anchor FGO vs EKF3 comparison
  - the `ds_tex_r1` unconditional → gated yaw-cap pair (re-run from `6f953b2`)
- **Every qualitative conclusion survives on cruise.** The fixes that degraded the UKF
  still degrade it. The correction still degrades both flow-rich cases. FINDING 4's
  71% split is unchanged, and so is its `ds` sign inversion. The FGO is still
  window-independent and still on par with EKF3.
- **Not restated:**
  - The full-LM half of the "capped vs full-LM, identical ATE 4.23" pair. That
    trajectory was never stored; the capped run alone is 3.72 cruise.
  - The void 0.49 m artefact.
  - Apparatus-metric figures (the `ds_*` noise floor, the `ukf_replay`/`fgo_replay`
    `ate_apparatus`). The apparatus metric is cruise-windowed by definition and is a
    different metric.
  - The Stage B/C mm-level figures, already void.
- **Also found:** before the correction, the FGO froze on blank rather than
  dead-reckoning (flagged in the three-way section).

**The n=3 ranges are not a noise floor.** With three repeats, a fourth run lands
outside the observed range with probability 2/(n+1) = 50% (under exchangeability). The
per-estimator ranges in the three-way table describe the data; they do not bound it. A
`dsn_*` evo -a (cruise) noise floor is **still an open item**.

**Phase 0 smoke test (b) — acceptance, pre-registered before flying.** One new
textured trial, flown with `run_trial.sh` on the unchanged `dsn_*` configuration
(`corridor_textured`, 0.5 m/s, 2.0 m, 300 s, nomag). It passes if all of the following
hold:
1. The pipeline completes: bag, `ardupilot.bin` and `metadata.yaml` are written, and
   `fly_trial.py` verifies `EXPECTED_PARAMS`.
2. Every recorded topic's sim-time rate (`eval/topic_rates.py`) is within ±2% of the
   `dsn_tex` mean.
3. evo -a (cruise) falls within the n=3 range widened by one range-width on each side:
   - **FGO** [4.18, 5.35] — the sensitive indicator.
   - **EKF3** [1.26, 8.13].
   - **UKF** [0, 34.95] — a sanity check only.

**Result — PASS (trial `p0_smoke_tex`, flown 2026-09-24 at `42193a5`).**
1. The pipeline completed and `fly_trial.py` reported "All baseline params correct".
   Metadata confirms `EK3_SRC1_YAW=0`, `COMPASS_USE=0` and the `sim_noise` block,
   identical to `dsn_*`.
2. Topic rates, as the deviation from the `dsn_tex` mean:

   | topic | deviation |
   |---|---|
   | `/optical_flow/measurement` | +0.01% |
   | `/downward_lidar/range` | 0.00% |
   | `/imu/data_raw` | −0.25% |
   | `/attitude/angular_rates` | +0.33% |
   | `/ekf/pose` | −0.37% |
   | `/clock` | 0.00% |
   | `/ground_truth/pose` | +1.89% |

   `/ground_truth/pose` is the only one outside the `dsn` spread (60.92 Hz against
   59.65–59.89). It is Gazebo's published pose rate. It feeds no estimator, and the
   cruise-window boxcar is defined in seconds, so the rate does not affect the window.
   Noted, not a failure.
3. evo -a (cruise):
   - **FGO 4.81**, inside [4.18, 5.35] and equal to the n=3 mean.
   - **EKF3 5.74**, inside [1.26, 8.13] and inside the raw n=3 range.
   - **UKF 19.36**, which passes the sanity check.

   The largest change under a ±0.5 s clock shift is 0.014 m. The failure metrics match
   `dsn_tex`: EKF3 ratio 1.06, FGO 0.98, and the UKF's leak-driven onset at 65 m.

The `dsn_*` pipeline reproduces end to end on the current code.

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

> **⚠️ SUPERSEDED IN PART (2026-09-29), kept unedited below as history.** The shared `h_flow`
> lateral row was wrong in BOTH terms: the translation was negated as well as the rotation
> (see "FINDING — lateral optical-flow sign"). The 2026-08-01 flip below changed only the
> rotation term. That left the row inconsistent, which is why it made the UKF worse; it was
> not evidence that `−rollspeed` was right. The `−2.07·rollspeed` residual below is what a
> whole-row sign error predicts: model `(−v, −ω)` against measured `(+v, +~1.5ω)`. The
> "acceptance-driven flow→yaw leak" quantification was made with the wrong lateral row and
> is on the batched corrections list (iv).

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
1. Flipping the sign **made the UKF worse**, not better: ATE evo `-a` 11.7 → 16.3 m
   (full-window, historical; **evo -a (cruise) 10.49 → 14.22**, re-run 2026-09-24),
   yaw drift +12.4 → +19.3 deg/min, gyro-z overshoot 245% → 336% (`dsn_tex_r1`) *(mixed
denominators; under one definition the pair is 245% → ~371% or 222% → 336%; see "Source-pack
flag resolutions (2026-09-29)" §3)*. The
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
bags (n=1 each):** textured (the tracking regime), **evo -a (cruise)**: UKF **14.09 → 17.07**, FGO
**4.32 → 4.81** — the fix degrades both flow-rich cases, as FINDING 4 predicts. (Full-window,
historical: UKF 16.44 → 19.96, FGO 4.87 → 5.46. The pre-correction side was re-run from
commit `08bc2eb` on 2026-09-24 and reproduced 16.44 / 4.87 exactly before the cruise
values were taken; per repeat, cruise, UKF 10.49/13.76/18.03 → 18.57/10.11/22.53, FGO
3.72/4.84/4.39 → 4.96/4.91/4.57.) Also bundled
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
| ATE, evo -a (cruise) | **10.49** | 18.57 |
| *ATE, evo `-a` full-window (historical)* | *11.69* | *21.58* |
| yaw drift (deg/min) | **+12.4** | +32.9 |
| gyro-z overshoot (% of 9.8; definition A, see 2026-09-29 flag resolutions §3) | **222%** | 494% |
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

*`dsn_tex_r1` (config A reproduces the committed baseline exactly — harness validated):*

| # | ω | acc_X | evo -a (cruise) | *evo −a full (hist.)* | yaw drift |
|---|---|---|---|---|---|
| A baseline | instantaneous | 72.5% | 10.49 | *11.69* | +12.4 |
| B *more-flow only* | **instantaneous** | 99.6% | 16.23 | *18.70* | +27.7 |
| C fix | interval-avg | 99.6% | 18.57 | *21.58* | +32.9 |

**~71% of the evo −a loss (cruise: A→B 5.74 of 8.08 m = 71%; full: 71%) and ~75% of the yaw-drift loss is the additional accepted flow
at unchanged derotation (A→B); the ω values add only the remaining ~25–29% (B→C).** Leak
path confirmed, not inferred: acc_Y (forward) stays pinned at 100% in every config — only
acc_X (lateral) moves — and the cumulative **absolute per-update yaw correction on the X
channel** rises 196° → 362° (A→B) while the Y channel's stays flat (88° → 76°). So the
extra accepted flow is entirely lateral and it is the lateral channel that pumps yaw.
(196→362° is a cumulative |Δyaw| *magnitude* — how hard the X updates push yaw — not net drift.)

*The correction is geometrically sound but flight-dependent — the compass-active `ds_tex_r1`
inverts the SIGN of its effect:*

| # | ω | acc_X | evo -a (cruise) | *evo −a full (hist.)* | yaw drift |
|---|---|---|---|---|---|
| A baseline | instantaneous | 76.2% | 17.43 | *19.90* | −23.4 |
| B *more-flow only* | **instantaneous** | 99.9% | 27.13 | *31.94* | +50.1 |
| C fix | interval-avg | 99.9% | **7.88** | ***8.72*** | −5.8 |

Isolating the ω correction at matched acceptance (B→C): on `dsn` slightly harmful (+2.3
evo -a (cruise); full +2.9), on `ds` a large benefit (−19.3 cruise; full −23.2). **More
acceptance hurts both flights (cruise +5.7 dsn, +9.7 ds; full +7 / +12 — the leak is on both); the correction itself helps `ds`, is ~neutral on `dsn`.**
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
(81.8 → 46.4 → 40.8, A→B→C) while *worsening* evo −a (cruise 10.5 → 18.6; full 11.7 → 21.6) and yaw drift
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
was still **wrong**: applied, it degraded the UKF (ATE evo -a (cruise) 10.49→14.22; full 11.7→16.3, drift 12.4→19.3,
overshoot 245%→336%, mixed denominators, see §3 of the 2026-09-29 flag resolutions) and its innovation flipped (+0.71→−0.69) rather than zeroing. The
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

**Corrected `h_flow` (interval-averaged ω, 2026-08-01) — re-run across all nine bags.**
The correction splits the conditions into **two regimes that must be reported separately**:
only **textured** is a tracking regime where evo −a means accuracy; **transition and blank
are failure regimes** where all three estimators diverge and evo −a is *not* a quality metric
(UKF blank 14.4 < EKF3 34.8, evo -a (cruise) — full-window, historical, 16 < 38 — is "diverges *less far*
after alignment," not a quality win). The old
"formulation differences wash out under degraded sensing" is restated as: **all three fail
under flow starvation, by different failure modes.**

**(1) Textured — the tracking-regime quality comparison. CURRENT BASELINE (OI-2
dejitter, 2026-09-24).** Metric: **evo -a (cruise)**, RMSE in m. UKF and FGO are re-run
with the OI-2 dejittered IMU stamps (`src/estimators/imu_timing.py`, master `cb4c845`,
all nine bags; `eval/results/dsn_dejitter_baseline.json`). EKF3 is unchanged.

| estimator | r1 / r2 / r3 | mean | range |
|---|---|---|---|
| EKF3 | 4.58 / 3.55 / 5.84 | **4.66** | 2.29 |
| FGO (0.25 s) | 4.63 / 4.74 / 4.57 | **4.65** | 0.17 |
| UKF (gated) | 16.98 / 9.96 / 20.71 | **15.88** | 10.75 |

**EKF3 and the FGO are indistinguishable at n=3.** The thesis claims no ordering
between them. That ordering **flips under the IMU-timestamp variants**: FGO 4.81
(receipt stamps) / 4.65 (dejittered) / 4.52 (reconstructed sensor time) against EKF3
4.66. The UKF remains ~3.4× worse and unstable across repeats (range 10.75 against
2.29 and 0.17).

**Why the correction was made — fairness, not ATE.** EKF3 integrates the IMU on SITL's
regular internal sensor time. The UKF and FGO had been integrating on bridge receipt
stamps with ±12 ms jitter. Dejittering gives them **equally regular IMU timing** (OI-2).
The ATE change is a *consequence*, reported here, not the reason: UKF 17.07 → 15.88 and
FGO 4.81 → 4.65, both better. **The reconstructed 5–9 ms sensor-time shift was NOT
adopted**: it would be an IMU–flow time offset fitted to a ±5 ms reconstruction, and
it moves the two estimators in opposite directions (OI-2 decomposition).

**Re-run gate.** The shared implementation reproduces the offline `oi2dj` control
exactly on all three textured bags (UKF 16.98 / 9.96 / 20.71, FGO 4.63 / 4.74 / 4.57),
so the implementation is the correction that was tested.

> **Superseded (kept for the record): the receipt-stamp cruise table below, and every
> UKF/FGO number elsewhere in this file computed on receipt stamps.** Only the textured
> table is restated. Per the batching ruling, all other UKF/FGO tables (transition and
> blank failure metrics, FINDING 2 and 4, ramp tracking, consistency) are restated
> **once**, in the consolidated re-run before the results chapter. The dejittered
> transition and blank values are already in `dsn_dejitter_baseline.json`; they are not
> yet interpreted here.

*Receipt-stamp cruise table (superseded 2026-09-24):*

| estimator | r1 / r2 / r3 | mean | range |
|---|---|---|---|
| EKF3 | 4.58 / 3.55 / 5.84 | **4.66** | 2.29 |
| FGO (0.25 s) | 4.96 / 4.91 / 4.57 | **4.81** | **0.39** |
| UKF (gated) | 18.57 / 10.11 / 22.53 | **17.07** | **12.42** |
| *supplementary, full-window (historical): EKF3 / FGO / UKF* | *4.79/3.89/6.21 · 5.58/5.60/5.21 · 21.58/11.65/26.65* | *4.97 · 5.46 · 19.96* | *2.32 · 0.39 · 15.00* |

**EKF3 ≈ FGO (~4.7–4.8 m, gap 0.16 m); the UKF is ~3.6× worse.** It is also worse
than before the correction (14.09 → 17.07, cruise), because the correct derotation
degrades the flow-rich case (FINDING 4). **The UKF is unstable across repeats.** Its
range is 12.4 m against EKF3's 2.3 m and the FGO's 0.4 m, and its worst repeat is
2.2× its best. The flow→yaw leak makes its evo -a sensitive to the particular flight.
The smoother's anchor does not.

> **Superseded — the mixed-window table (how it was found).** Until 2026-09-24 this
> table read EKF3 4.6 / 3.5 / 5.8 (mean 4.97), FGO 5.6 / 5.6 / 5.2 (5.46), UKF
> 11.7 / 21.6 / 26.7 (19.96), with prose saying "two of three > 21". That table mixed
> windows.
> - EKF3's per-repeat values came from `plots/failure_analysis.py`, a 2-D SE(2)
>   Umeyama fit over the cruise window.
> - Every mean, and all UKF/FGO per-repeat values, came from evo -a on the full
>   recording (`plots/rerun_batch.py`).
> - The UKF's r1 and r2 were transposed (r1 = 21.58, r2 = 11.65).
> - "Full" was also not a common window: EKF3's `XKF1` trajectory starts 2.6–4.0 s
>   after the UKF/FGO trajectories.
>
> It was caught by the **forward-camera Phase 0 reproducibility gate**: regenerate
> every published figure from stored data with one committed script before building on
> it (`eval/results/phase0_window_check.json`). Neither window alone reproduced the
> EKF3 column. The ruling was cruise, applied as one GT-defined window to all
> estimators (pinned-window section above). **No textured conclusion changed**: the
> ordering EKF3 ≈ FGO ≪ UKF holds on both windows. The EKF3–FGO gap narrows from
> 0.49 m (full) to 0.16 m (cruise). "Two of three > 21" held on full only and is
> dropped.

**(2) Transition & blank — degraded-sensing FAILURE analysis** (evo −a meaningless; failure
metrics instead — final displacement magnitude vs true travel 151 m, and the true-y at which
the estimate departs GT by > 15 m).

*Window:* these metrics are measured over the cruise window, with the origin at the
cruise start. Until 2026-09-24 each estimator's cruise window was computed on its own
clock; they now use the pinned common window. **They do not depend on the window.** On
all nine bags, recomputing them over the full recording moves the displacement ratio by
≤ 0.05 and the onset by ≤ 1 m. The values below reproduce exactly under the pinned
window (`eval/results/phase0_cruise_pinned.json`).

| condition | metric | EKF3 | UKF | FGO |
|---|---|---|---|---|
| **transition** | \|disp\| / true | 0.57 | 0.83 | 0.74 |
| | divergence onset (true-y) | 102 m | 78 m | 95 m |
| **blank** | \|disp\| / true | **0.20** | **1.30** | **1.60** |
| | divergence onset (true-y) | 18 m | 50 m | 24 m |

**The failure MODES differ — the §9.5 formulation difference, now empirically visible:**
- **EKF3 FREEZES** (`const_pos` on aiding loss): blank displacement **0.20× true** — it stops
  (~30 m) where flow starves while GT travels on.
- **UKF and FGO DEAD-RECKON** (no `const_pos`, by the §9.5 decision): blank **1.30× / 1.60×**
  — they integrate garbage starved-flow and over-travel (197 m / 242 m vs 151).

> **FLAGGED, not investigated (2026-09-24), tracked as OPEN ITEM OI-1 below: before the
> `h_flow` correction, the FGO froze on blank.** Re-running the pre-correction code (`08bc2eb`, all nine bags, reproducing
> the historical full-window means exactly) gives these results:
> - **Blank:** pre-correction FGO displacement ratio **0.06 / 0.18 / 0.04**, onset 17–26 m.
>   That is EKF3-like stopping, although the FGO has no `const_pos`. The corrected FGO
>   over-travels at 1.58–1.64×.
> - **Transition:** the pre-correction FGO ratio is 0.51–0.55, against 0.73–0.75 corrected.
>
> So the "UKF and FGO DEAD-RECKON" failure mode below is **not solely** the §9.5 decision
> (no `const_pos`). For the FGO it appears with the corrected derotation. The mechanism
> is not established; a plausible candidate is that the wider lateral-flow acceptance
> (FINDING 4) lets starved flow drive velocity. **The comparison's claim that the
> failure modes differ still stands**, since it is measured on the corrected
> (committed) estimators. Only the attribution to §9.5 alone is qualified.
>
> Cruise-window before/after on the degraded conditions, evo -a (cruise), which is *not*
> a quality metric here:
> - Transition: UKF 24.68 → 16.04, FGO 22.33 → 26.08.
> - Blank: UKF 36.02 → 14.42, FGO 39.64 → 27.68.
>
> The historical full-window figures were transition 27.11 → 17.48 / 24.55 → 28.93 and
> blank 39.84 → 16.05 / 43.28 → 30.48 (`eval/results/precorr_vs_corr.json`).

> ### OPEN ITEM OI-1 — FGO blank-floor failure mode changed with the `h_flow` correction
>
> **Must be resolved (half-day time-box) before the failure-mode analysis is written up.
> Not investigated yet, by decision (2026-09-24).**
>
> **Observation.** On `dsn_blank_r{1,2,3}`, the pre-correction FGO (`08bc2eb`,
> instantaneous ω in `h_flow`) **freezes**: displacement ratio 0.06 / 0.18 / 0.04, onset
> 17–26 m, like EKF3's `const_pos` behaviour even though the FGO has no `const_pos`. The
> corrected FGO (interval-averaged ω, current) **dead-reckons** at 1.58–1.64×. The
> transition ratio moves from 0.51–0.55 to 0.73–0.75. Nothing else changed between the
> two runs: same bags, same window, same factors apart from the ω fed to `h_flow`.
>
> **Candidate hypotheses:**
> - **H1 — the gate decides what reaches velocity.** Under starved blank-floor flow, the
>   roll-coupled instantaneous-ω residual inflates lateral innovations, so the χ² gate
>   rejects most flow. With no accepted flow, the smoother's velocity is held near its
>   prior or zero, and position stops. The correction makes innovations consistent
>   (FINDING 4: acceptance 71% → 98% on textured), so starved, near-zero-mean garbage
>   flow is accepted and integrated. Test: flow acceptance per axis on blank, pre vs
>   post correction.
> - **H2 — near-zero measured flow is being read as motion.** Blank-floor flow has
>   ~zero translational content (`flow_y_raw` −0.71 px/s). The corrected `h_flow` now
>   subtracts the frame-averaged rotational term, so if that term is biased relative to
>   the measured (rotation-only) flow, the remainder reads as a velocity. That would
>   explain the over-travel beyond 1×. Test: the sign and magnitude of the implied
>   velocity from accepted blank-floor flow, against GT.
>
> **Why it matters.** The current text attributes "UKF/FGO dead-reckon" to §9.5 alone.
> If H1 holds, the failure mode is partly a *gating* consequence of the derotation
> model, not only a formulation choice, and the failure-mode analysis has to say so.

**(3) The degradation gradient survives as a WITHIN-estimator result.** The *between*-estimator
comparison does not hold on transition/blank (different failure modes), but each estimator
degrades monotonically as flow degrades, read on **divergence onset**: **EKF3** tracks textured
(no divergence) → transition 102 m (past the y=80 boundary) → blank 18 m (early); **FGO** tracks
→ 95 m → 24 m — both monotonic (later onset = better sensing). The **UKF**'s gradient is muddied
— it already "diverges" at 69 m *on textured* (the leak-driven yaw drift, not aiding loss), so
its onset (69 → 78 → 50 m) is not clean. **So the texture→transition→blank gradient survives
within EKF3 and the FGO** (failure onset moves earlier as flow degrades); the UKF's own tracking
is corrupted by the leak before the sensing even degrades.

- **evo `-a` remains the only fair cross-estimator metric, and only in the textured regime.**
  Unaligned is not comparable (EKF3 true frame vs UKF/FGO ~90° init-yaw gauge). Yaw drift:
  EKF3 ~8, **FGO −9 in every condition** (anchor-locked), UKF flow-dependent (+14…+41 textured);
  the FGO's *position* did move (evo -a (cruise) textured 4.32→4.81, blank 39.6→27.7;
  full-window, historical, 4.87→5.46, 43→30), so its flat yaw is the anchor, not a no-op.

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
window-independent** — **evo -a (cruise) 4.47 / 4.44 / 3.72 m** at 1.0 / 0.5 / 0.25 s
(full-window, historical: 5.10 / 5.07 / 4.23; `dsn_tex_r1`, pre-correction code `08bc2eb`, all
three re-run 2026-09-24 and reproduced exactly before cropping), so the FGO
is ~equally accurate at any window and 0.25 s merely also happens to be (mildly) best.

**Solver + timing (reported honestly).** The primary solver is `BatchFixedLagSmoother`
(iSAM2-incremental is unusable — GTSAM `marginalizeLeaves` cascades on the Python flow
`CustomFactor`, FGO_DESIGN §6). *(Step times below: DIAGNOSTIC, workstation Python, window sweep
on `dsn_tex_r1`, 2026-08-01, `04426d2`. The current 0.25 s figure is ~29 ms on textured bags;
see "Source-pack flag resolutions (2026-09-29)" §1.)* Step-time scales ~O(window): **96 / 48 / 27 ms** at
1.0 / 0.5 / 0.25 s. **The FGO meets the 33 ms deployability budget ONLY in its
short-window (0.25 s) configuration — a real result, not a footnote:** a Python-bound
`CustomFactor` FGO is budget-compliant only at a short window; larger windows spend
compute for no accuracy gain. LM iterations are capped at 2 (warm-started); verified
against full-LM at 0.25 s — max position difference 0.11 m, **RMS 0.029 m, identical
ATE (4.23, full-window, historical; the full-LM trajectory was not stored, so this pair is
not restated on cruise — the capped run alone is 3.72 cruise)** over 10047 keyframes — so the cap is not a truncated approximation.

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
drifts too (~5 deg/min under the deterministic SIM_DRIFT). *(SUPERSEDED: ~5 deg/min is the
single-trial residual +5.32 deg/min from `nomag_corridor_baseline` (`257204d`). The current
figure is +6.6…+11.1, mean ~8.1 deg/min, n = 9 `dsn_*` bags (`ca4c474`); see "Source-pack flag
resolutions (2026-09-29)" §2.)*

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
the yaw drifts 12–32 deg/min, and the trajectory diverges (ds_tex_r1, unconditional → gated cap,
evo -a (cruise) 7.73 → 17.43 m; full-window, historical 8.6 → 19.9 — re-run from `6f953b2`
2026-09-24, reproduced 8.64). Diagnosed (half-day box, no fixes applied):

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

### Lateral drift — EKF3's east-velocity bias is yaw rotation, not the measurement or the gate (CLOSED)

EKF3 carries a sustained **+0.194 m/s east-velocity bias** on `dsn_tex_r3` (→ +55.9 m
cross-track), yet the flow measurement is **unbiased in the body frame** — the accepted
lateral flow innovations mean **0.0089 rad/s** (`XKF5.FIX`, ×1000). Resolved by three
checks (`plots/lateral_checks.py`, diagnosis only):

1. **Not gating.** The raw lateral innovations *do* carry a +0.238 rad/s mean (positive
   roll-coupled spikes), but the gate **removes** it (rejects positive 91.6% vs negative
   95.7%), leaving accepted mean 0.0089 rad/s ≈ 0.016 m/s of velocity. Gating *reduces* the
   innovation bias; it does not create the velocity bias. (EKF3's `NI` is a combined 2-axis
   ratio, so per-axis accept is approximate.)
2. **Yaw rotation is the mechanism.** Yaw has drifted (+9.5 deg/min → +48°), so the
   correctly-estimated **body-forward** velocity rotates into an apparent world-East
   component: `slope(errVE vs spd·sin(yawErr)) = +1.10` — the exact geometric relationship.
   The filter is **self-consistent in its drifted frame** (the lateral flow correctly drives
   *body*-lateral velocity to ~0), which is why zero-mean innovations coexist with a biased
   *world*-frame velocity: **the bias lives in the unobservable yaw direction, not in the
   measurement or the gate.**
3. **Attribution is a REAL decomposition, not double-counting.** *(SUPERSEDED share: 74% used the old window, aiding onset to end of log. On the pinned cruise window it is **69%**; see "Heading share restated (2026-09-29)".)* ~**74%** of the
   east-velocity bias is heading-driven (`vE_head` +0.143 of +0.194 m/s; cross-track 45.6 m
   of 62 m); the ~**26%** remainder (~0.05 m/s, ~16 m) is **uncorrelated with yaw error
   (−0.23)** — a genuinely separate lateral-velocity bias, source not established (not the
   gate — ≤0.016 m/s — and not the heading term reappearing). **Open residual, magnitude
   stated; not worth further investigation** — uncorrelated with everything tested, small
   vs the heading term, and common-mode across estimators (shared `h_flow` geometry).

**The t≈200 s regime change is motion-profile, not a filter event.** The drone decelerates
near the corridor end (GT speed 0.50 → 0.44 m/s); translational flow shrinks so the
roll-coupled residual becomes a larger share of the lateral channel (mean |FIX| 449 → 1055).
Altitude (2.1 m), roll amplitude (0.26°), and flow acceptance (~6.5%) are unchanged. So the
"oscillate-then-settle" transition is the speed profile, not gating/altitude/roll.

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
| ATE, evo `-a` (full, hist.) | 0.49 m ⚠️void | **5.10 m** |
| ATE, evo -a (cruise) | — | **4.47 m** |
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
essentially equal, FGO marginally worse (full-window, historical). On **evo -a (cruise)** it
is EKF3 4.58 vs FGO 4.47 — still essentially equal, the 0.1 m ordering now reversed; "on par"
is the finding on both windows, neither "better" is. The apparent 5× improvement was a
metric mismatch (aligned vs unaligned), not a result. The FGO's *unaligned* ATE is
139 m, dominated by the ~90° init-yaw gauge offset (no compass → arbitrary heading),
which `evo -a` removes. **Not a bug and not smoothing-magic:** instrumented, the FGO
tracks the flow (cruise flow-factor residual ≈ 0: x −0.0007, y −0.0012 rad/s) and
its cruise velocity is `|V(k)| = 0.517 m/s`, **+4.7 %** over true — so it *does*
inherit a flow scale error, merely smaller than EKF3's `0.556 m/s` (+12.6 %) *(SUPERSEDED,
n = 1: the current nine-flight values are EKF3 +5.7…+9.6 %, FGO +0.9…+1.1 %; see "Source-pack flag
resolutions (2026-09-29)" §4)* on this
bag (n=1; the smaller inheritance is unexplained and not leaned on). The along-track
147.5 m looking "too good" vs true 151.1 was coincidence: the +4.7 % speed offset is
cancelled in *displacement* by the −9.24 deg/min yaw-drift curvature. Flow is the
only horizontal-velocity observation, so the FGO could not have avoided the scale —
and it didn't.

**Flow_x partition (re-checked).** The controlled single-update partition is
anchor-independent — Euler-UKF and SO(3)-FGO still both 69 % velocity / 31 % yaw.
The fair-anchor full run confirms the accumulated consequence: yaw drifts once the
cap no longer over-constrains it.

**Computational cost — goes in the results regardless of accuracy.** *(SUPERSEDED as the
FGO's cost: this is the 1.0 s-window, pre-LM-cap configuration of 2026-08-01. The current
0.25 s configuration is ~29 ms/step on textured bags. See "Source-pack flag resolutions
(2026-09-29)" §1.)* Batch smoother
**101 ms/step median, p99 167 ms — 3–5× over the 33 ms deployability budget**. The
incremental (iSAM2) solver is 0.2 ms/step (well under budget) but **cascades after
~590 keyframes**. The cascade is isolated to the incremental marginalisation layer,
not our estimator logic: the *same* factors and core run to completion under batch
(10047 keyframes, 0 failures), so it is a GTSAM iSAM2 + Python-`CustomFactor` +
fixed-lag interaction. Whether it is inherent to that combination or an
implementation artefact is not yet root-caused; batch is the robust path meanwhile.
This is the measured version of FGO's main known weakness (compute).

## PRE-REGISTRATION RULE (standing, from 2026-09-24)

Two errors in one phase (forward-camera Phase 1, branch `fwd-camera`: the ground-truth pose-rate band and the IMU gap-share band)
came from one habit: bands taken from the bare observed range with zero margin, and
diagnostic metrics used as pass/fail gates. From now on:

1. **Each criterion is labelled PRIMARY** (it tests the confound directly) **or
   DIAGNOSTIC** (reported, never a gate).
2. **No band uses the bare observed range.** Each states its margin and the basis for
   it: a physical tolerance, or the n=3 range widened by a stated factor. It also says
   why a value outside the band would indicate the confound.
3. **Only primary criteria can stop a phase.**

## STANDING RULE — scope control (user, 2026-09-24)

**Before starting any work that is not in the phase brief, ask:**
- **(a)** does it change a thesis claim?
- **(b)** would a reviewer's objection stand without it?

**If both are no,** add one line to the open-items list below and move on.

**Only primary criteria that could change a conclusion stop a phase.** Diagnostics
are reported, never investigated on the spot.

## BASELINE CORRECTIONS ARE BATCHED (user, 2026-09-24)

The OI-2 dejitter re-run (below) is the **current `dsn` baseline**. From now on,
further corrections to the `dsn` baseline are **batched into one consolidated re-run
before the results chapter**, not restated one at a time. **Dejitter applies to all new
data from Phase 2 onwards.**

### Open-items list (logged, not being worked)

- **OI-1:** the FGO's blank-floor failure mode changed with the `h_flow` correction
  (Three-way comparison section). Resolve before the failure-mode write-up.
- **OI-2 residual:** the sensor-time IMU shift is not adopted. `/imu/time_ref`
  (recorded from Phase 2 on) allows true sensor time to be used in the consolidated
  re-run if ruled.
- **Baseline corrections queued, 2026-09-29 (distance-scale check):**
  - **(i) EKF3 `FLOW_POS_Z` 0.13 → 0.25.** Configuration. The logged HAGL is body-origin
    referenced. Requires re-flying all datasets.
  - **(ii) UKF process dt = the accumulated IMU interval** (15.00 ms, not the nominal 12.5
    ms), with Q scaled to it. Implementation. Requires re-replaying all bags.
  - **Both block:** the with-heading FGO-vs-UKF comparison and any EKF3/UKF cross-estimator
    ATE claim.
  - **(iii) The heading share was restated on the pinned cruise window:** 74% → 69%
    (`dsn_tex_r3`). It is to be restated again after (i).
- **Tables not yet restated on the dejittered baseline** (deferred to the consolidated
  re-run): transition and blank evo -a and failure metrics; the FINDING 2 and 4
  tables; the gyro-z ramp-tracking table; the consistency percentages.

## OPEN ITEM OI-2 — IMU timestamp asymmetry between estimators (fairness)

EKF3 integrates the IMU on **true sensor time** (inside SITL). The UKF and FGO replay
`/imu/data_raw` on its **header stamp**, which `imu_bridge.py:169` sets to the ROS sim
clock at *receipt*. Those stamps scatter 0–9 ms around the true 3 ms sampling, with an
exact mean of 3.0005 ms. This is common to every bag, so it cannot bias a comparison
**between conditions**. It is an **asymmetry between estimators** in a framework whose
premise is matched inputs, so it has to be quantified, not asserted small.

**Plan** (offline only, half-day time-box, no estimator or `dsn` result changes): on
`dsn_tex_r1..r3`, re-run the UKF and FGO with IMU samples timed on sensor time mapped
to the sim clock. Report the change in evo -a (cruise) and yaw drift. The user then
rules on whether a correction goes through the re-run gate.

## FINDING — the SITL dataflash clock runs ~0.02% slow against Gazebo sim time (2026-09-24)

Found while building OI-2. `TimeUS` (SITL, dataflash) and the bag's sim clock differ
in **rate**, not just offset. Fitting the `SIM`-vs-`/ground_truth/pose` alignment
separately early (takeoff, cruise start) and late (cruise stop, landing) gives:
- offset ≈ −6 to −9 ms early and −52 to −68 ms late on every bag;
- SITL slow by **0.016–0.022%**;
- the same drift appears independently in the IMU, where receipt stamps drift 52 ms
  against dataflash IMU time over the flight.

`eval/input_timing.py` now maps TimeUS → sim time with `clock_map()` (offset **and**
rate).

**Consequences:**
- **Clock-sensitivity item (Hidden Configuration Audit §1).** It stays "bounded, not
  proven". The drift, ≤ ~60 ms over a flight, is well inside the ±0.5 s shift that was
  shown to move no conclusion. EKF3's evo -a is unaffected: `XKF1` and `SIM` share
  `TimeUS`.
- **The forward-camera Phase 1 flow→EKF3 latency figures (branch `fwd-camera`) used a single whole-flight offset**,
  which smeared each distribution by about ±25 ms. That produced the spurious "negative
  p5" and the "transition medians up to 32 ms". They are **superseded** by the
  linear-map values below (`eval/results/input_timing_linmap.json`). The distributions
  are now positive (p5 ≥ 8 ms) and about 15 ms wide.
- **Did not work (recorded):** the first linear-map run silently reused the name `t1`
  for both the clock-fit anchor and the cruise-window end. That cropped the latency
  statistics to the first ~300 frames and produced a spurious P2 failure for
  `p1_fwd_trans`. It was caught by the valid-frame count (≈ 300 against ≈ 9000),
  fixed, and re-run before anything was concluded.

## OI-2 result — IMU sensor time vs receipt time (offline, 2026-09-24)

**Method** (`eval/oi2_imu_time.py`; estimators and `dsn` results untouched):
- **Anchors.** Sensor time is reconstructed from the dataflash `IMU` records (25 Hz,
  instance 0) matched by value to bag samples. 6722–6823 anchors, ≈ 81% of dataflash
  samples. That is the expected 333/400 overlap, since `HIGHRES_IMU` is sent on 5 of
  every 6 loop ticks.
- **Clock.** Anchors are mapped to sim time with `clock_map()`.
- **Model.** t = a + b·i, fitted to the anchors. The period is 3.0005 ms (equal to the
  receipt mean), with residual std **0.82 ms** and max 1.89 ms, consistent with the
  2.5 ms loop grid (±1.25 ms).
- **Check.** Receipt minus sensor time is stationary, with a median of 5–9 ms from start
  to end. The p5 of −1 to −2 ms is within the ±2–3 ms accuracy of the grid plus clock
  map.
- **Run.** Clones `dsn_tex_r{1,2,3}_oi2` are identical except for the IMU header
  stamps. The **unchanged** UKF/FGO replays run on them. Results:
  `eval/results/oi2_evo.json`.

| evo -a (cruise), m | r1 | r2 | r3 | mean | Δ mean |
|---|---|---|---|---|---|
| UKF, receipt → sensor | 18.57 → 18.83 | 10.11 → 11.71 | 22.53 → 22.64 | 17.07 → 17.73 | +0.66 (mixed sign across repeats) |
| FGO, receipt → sensor | 4.96 → 4.69 | 4.91 → 4.52 | 4.57 → 4.34 | **4.81 → 4.52** | **−0.30 (−6%, same sign on all three)** |

| yaw drift, deg/min | r1 | r2 | r3 |
|---|---|---|---|
| UKF | 32.9 → 33.2 | 13.9 → 10.5 | 40.9 → 42.0 |
| FGO | −9.31 → −9.16 | −9.71 → −9.18 | −9.26 → −8.62 |

**Reading.**
- **FGO:** a small, consistent improvement (0.23–0.39 m on every repeat), comparable to
  its own n=3 range (0.39). It **reverses the sign of the EKF3–FGO gap** (EKF3 4.66;
  FGO 4.81 → 4.52). That gap was already inside "on par", so no textured
  conclusion changes, but the fine ordering depends on OI-2.
- **UKF:** no consistent direction; the changes are small against its 12.4 m range.
- **Yaw drift:** barely moves for either estimator (FGO −9.3 → −9.0 on average), so
  receipt jitter is not a driver of the yaw leak.
- **The asymmetry is real but second-order.** It does not touch UKF ≪ {EKF3, FGO}. It
  does decide the sign of the EKF3–FGO difference.

**Awaiting the user's ruling** on whether a sensor-time IMU correction goes through the
re-run gate. Implementing it properly means recording `time_usec` in `imu_bridge.py`
for new bags and reconstructing it (as here) for the existing `dsn_*` bags.

### OI-2 decomposition — dejitter vs shift (control, 2026-09-24)

The sensor-time clone changes **two** things: it removes the 0–9 ms receipt jitter, and
it moves every IMU sample 5–9 ms **earlier** relative to the flow and lidar capture
stamps. The shift depends on the clock map. The within-flight drift of the
receipt-minus-sensor median (r2 +0.6 → +6.0 ms, r3 +2.2 → −2.3 ms) shows that the
**reconstruction is accurate to about ±5 ms, not ±2–3 ms** as stated above.

A control, `dsn_tex_r*_oi2dj` (`oi2_imu_time.py --dejitter`), fits a line to the
**receipt** stamps themselves. That removes the jitter and keeps the mean latency, so
there is no shift. Results: `eval/results/oi2dj_evo.json`.

| evo -a (cruise), m | r1 | r2 | r3 | mean |
|---|---|---|---|---|
| UKF, receipt (current) | 18.57 | 10.11 | 22.53 | 17.07 |
| UKF, **dejitter only** | 16.98 | 9.96 | 20.71 | **15.88 (better on all three)** |
| UKF, sensor (dejitter + shift) | 18.83 | 11.71 | 22.64 | 17.73 |
| FGO, receipt (current) | 4.96 | 4.91 | 4.57 | 4.81 |
| FGO, **dejitter only** | 4.63 | 4.74 | 4.57 | **4.65 (2 of 3 better, 1 unchanged)** |
| FGO, sensor (dejitter + shift) | 4.69 | 4.52 | 4.34 | 4.52 |

Yaw drift, deg/min (receipt → dejitter): UKF 32.9 → 29.5, 13.9 → 13.2, 40.9 → 37.2;
FGO −9.31 → −9.19, −9.71 → −9.41, −9.26 → −8.92.

**Reading.**
- **Removing the jitter is a robust improvement for both estimators.** It needs no
  clock map and is well determined.
- **The IMU-vs-flow shift acts as an estimator-dependent tuning lever.** It helps the
  FGO further and undoes the UKF's gain. It is known only to about ±5 ms. Adopting it
  from the reconstruction would amount to choosing a time offset, which is exactly
  what the fairness rules forbid.
- A defensible correction is therefore either **dejitter only**, or **true
  sensor time recorded at source** (`time_usec` in `imu_bridge.py` for new bags). The
  second fixes the shift by measurement rather than by fit.
- Either way it goes through the re-run gate on the full `dsn` set. That ruling is the
  user's.

## Forward-camera workstream (branch `fwd-camera`) — hypothesis, sensor, worlds, Phase 1 pre-registration (2026-09-24)

### Hypothesis (stated before any forward-camera result exists)

With no compass, absolute yaw is unobservable. *(74% / 26% below: old window, SUPERSEDED by 69% / 31% on the pinned cruise window; see "Heading share restated (2026-09-29)". The prediction text is left verbatim as pre-registered.)* On `dsn_tex_r3`, **74%** of EKF3's
east-velocity error is heading-driven: `errVE` against speed × sin(yaw error) has a
slope of 1.10. The remaining **26%** (~0.05 m/s) is uncorrelated with yaw error
(§"Lateral drift", CLOSED).

**Hypothesis:** a forward camera supplies two things:
- an **absolute heading cue relative to the corridor** (the vanishing point, or the
  dominant wall-line direction);
- through horizontal forward flow, **observability of the gyro-z bias**.

Together these reduce the heading-driven share of lateral drift.

**Prediction:** the heading-driven share falls, and the 26% residual stays roughly
unchanged. If the residual also moves, that is a finding, not a failure. The residual's
source was never established, so any movement would say something about it.

The test is Phase 5: each estimator with and without the forward-camera measurements,
on the same `fwd_*` bags, reading the heading-driven/residual decomposition, yaw
drift, gyro-z bias tracking and ±3σ consistency.

### Sensor design — `iris_fwd` (vendored in `sim/models/`)

`iris_fwd_standoffs` is a copy of `~/ardupilot_gazebo/models/iris_with_standoffs`.
`diff` against the original shows **only** the inserted `forward_camera` sensor block,
so the downward camera, the gpu_lidar and the IMU are byte-identical to the `dsn_*`
model.

`iris_fwd` is a copy of `iris_with_ardupilot`. Its `diff` shows only the model name and
the include: `model://iris_fwd_standoffs`, with `<name>iris_with_standoffs</name>`
kept. Every scoped reference (joint parents, lift-drag links, `ArduPilotPlugin
imuName`) therefore resolves unchanged. The meshes still resolve from
`model://iris_with_standoffs`. The worlds instantiate it as `iris_with_ardupilot`, so
tooling that names the model is unchanged.

**The flights run on simulator truth (`AHRS_EKF_TYPE=10`), so the physical heading is
fixed.** Cruise GT yaw is 90.01°, std 0.017°. The vanishing point therefore sits at the
image centre whatever an estimator's yaw does. The FOV does not need to cover
estimator heading error; that only matters in closed-loop flight (Term 3), where the
physical heading can wander. The design is set by corridor geometry and measured
attitude. Cruise attitude from `dsn_tex_r1` / `dsn_blank_r1` GT:
- roll: mean 0.00°, std 0.26°, max 0.53°
- pitch: mean +0.02°, std 0.17°, max 5.2° (the acceleration transients)
- base_link height: 2.29 m

| parameter | value | justification |
|---|---|---|
| HFOV | **60°** (1.047 rad), VFOV ±23.4° | Same intrinsics as the downward camera; `camera_info` confirms f = 554.38 px. Side walls at ±10 m enter the frame 17.3 m ahead, where the wall base is at −7.5° and the wall top at +8.9°, well inside ±23.4°. Angular resolution is 0.094°/px. A wider lens would lose resolution with no gain, since the heading is fixed (above). |
| resolution | **640 × 480** | Same sensor as the downward camera. |
| rate | **30 Hz** (sim-time) | Matches the downward camera, flow and LiDAR cadence. At 30 Hz the rotation between frames stays small for the forward-flow yaw-rate measurement. |
| format | **mono (L8 → `mono8`)** | Every Phase 3 algorithm (line/VP extraction, LK flow) is greyscale. The bag data rate is one third of RGB: ~9 MB/s sim against ~28 MB/s. The L8 → `mono8` bridge conversion was **tested** in the render check. |
| mount | **0.15 m forward of base_link, level (0 pitch, 0 roll)**, looking along body +x, rigid | Cruise pitch mean +0.02° (std 0.17°) puts the vanishing point at the image centre to within ~3 px. The render check shows no body or propeller occlusion. |
| clip | near 0.05 m, **far 200 m** | The corridor is 165 m long. The downward camera's 20 m far clip would cut the corridor off before the vanishing point. |

### Worlds — `corridor_{textured,blank,transition}_fwd.sdf` (vendored in `sim/worlds/`)

`diff` against each original shows exactly these changes:
- the `<world name>` (it must equal the filename stem, because `run_trial.sh` builds
  the `dynamic_pose/info` topic from it);
- the two side walls use `model://corridor_wall_lined` in place of `corridor_wall`;
- a static `corridor_end_wall` at y = 165;
- the drone include is `model://iris_fwd`, with the instance named
  `iris_with_ardupilot`.

The floor tiles, `ground_collision`, lighting, spawn and physics are identical. The
originals and every `dsn_*` dependency are untouched.

- **`corridor_wall_lined`:** its collision box is byte-identical to `corridor_wall`
  (0.2 × 170 × 5 m, link at z = 2.5 m). The one grey visual is replaced by 17 visual
  segments of 0.2 × 10 × 5 m that tile the same volume, so the geometry and the shadows
  it casts are identical and only the surface material differs. Segments are used
  because Ogre2 stretches one texture over a whole face, the same UV trap documented
  for the floor tiles.
- **Texture** (`sim/tools/make_wall_textures.py`, seeded, three variants cycling every
  30 m):
  - horizontal black lines every 0.5 m, 8 cm thick, on a white base; they run parallel
    to the corridor axis, so they converge on the vanishing point;
  - non-periodic vertical bars (random width, height, grey level and spacing), which
    give horizontal flow 2-D texture (stripes alone have the aperture problem) and
    avoid a regular spacing that could alias the LK tracker or RANSAC.
- **Did not work: texture v1.** Grey 160 base with 25 lines, 4 cm thick. It rendered
  the wall at ~20–40 grey, with the lines only ~15 levels darker, which is too faint:
  the inner faces receive little direct sun. v2 (above) renders the walls at mean
  75–106, std 35–45. Found by the render check before any flight.
- **End wall:** static, so it never enters `dynamic_pose/info` and cannot displace
  `poses[0]`. The sun's +y component throws its shadow beyond the corridor. It is
  19.8 × 0.2 × 5 m and textured with non-periodic rectangles plus the same lines.

**Design decision: the walls are textured in all three worlds.** The question is
whether a forward heading cue **compensates for floor degradation**. So the forward cue
must be present, and identical, in every floor condition, with floor texture remaining
the only variable between worlds. A **blank-wall variant** (forward camera present,
walls untextured) is deferred as a later ablation. It would separate "the forward
camera sees structure" from "the forward camera is present".

### Recording and harness

- **Raw forward images are recorded** (`/forward_camera/image` and `camera_info`), the
  opposite of downward flow, which is fixed at record time (§"Flow processing is baked
  in"). Phase 3 builds its measurements offline, so its processing choices stay open.
  Cost is ~3 GB per 300 s trial.
- **`run_trial.sh` is opt-in and name-driven.** A world named `*_fwd` fills two arrays
  (bridge arguments, record topics) and adds `forward_camera: true` to
  `metadata.yaml`. For every other world the arrays are empty; under `set -u` in bash
  5.2 an empty `"${arr[@]}"` expands to **no** argument, so the default bridge and
  recorder command lines are unchanged. This is verified from `/proc/<pid>/cmdline` on
  the control flight (below).
- **Trial names:** Phase 1 uses `p1_*`; `fwd_*` is reserved for the Phase 2 dataset.

### Phase 1 plan and confound-check acceptance (pre-registered before flying)

Four flights, back to back, in one session, all at the `dsn_*` settings (0.5 m/s,
2.0 m, 300 s, nomag, `sim_noise.parm`, RANSAC seed 42):

| trial | world |
|---|---|
| `p1_control_tex` | `corridor_textured`, no forward camera (same-session control) |
| `p1_fwd_tex` | `corridor_textured_fwd` |
| `p1_fwd_blank` | `corridor_blank_fwd` |
| `p1_fwd_trans` | `corridor_transition_fwd` |

The control flight exists because the desktop was under measurable background load
(Firefox ~110% CPU plus gnome-shell; ~12–23% GPU at idle). That load is the likely
reason the smoke test's RTF (0.954) was below the `dsn_*` flights' (0.975–0.981). The
control measures that same-session baseline, so any drop can be attributed to the
second camera. It is used for diagnosis, not tuning.

**(a) RTF and topic rates.**
- **RTF method:** 300 s of cruise sim time over the cruise wall time in
  `fly_trial.log`. On the same method, `dsn_*` measured 0.975–0.981 and the smoke test
  0.954. The 0.92 floor is the 2026-07-23 lockstep figure. **Pass** if each `p1_fwd_*`
  flight has RTF ≥ 0.92 **and** ≥ (control RTF − 0.03). **If it fails: stop and report;
  no tuning.**
- **Rates** (`eval/topic_rates.py`, sim-time):
  - every `dsn_*` topic, including `/optical_flow/measurement`, which would expose
    dropped downward frames, must be within ±2% of the `dsn_tex` mean (the smoke-test
    band);
  - `/forward_camera/image` and `/forward_camera/camera_info` must be within ±2% of
    30.30 Hz (the 33 ms sim period; a slow bag writer would show up here as missing
    frames).

**(b) Downward-flow conditions unchanged** (`eval/flow_quality.py`, cruise window).
The baseline is the `dsn_*` n=3 cruise-window values, which share the pipeline,
config and window definition:
- textured inlier_ratio 0.9729–0.9741
- blank 0.3130–0.3153
- transition switch in the absolute 80–82 m bin, with levels 0.972–0.974 (y < 75) and
  0.312–0.315 (y > 85)

These differ slightly from the 0.9752 / 0.3101 quoted from the 2026-07-23
verification trials, which were different flights and used whole-flight statistics
from an earlier script. The n=3 cruise-window values are the like-for-like baseline.

Pass if all of the following hold, per world against its `dsn` counterpart:

| check | band |
|---|---|
| inlier_ratio mean | within ±0.01 of the `dsn` mean |
| % of frames below 0.5 | within ±3 percentage points |
| feature_count mean | within ±5% |
| `flow_y_raw` mean | textured and transition within ±2%; blank within ±5 px/s absolute (its mean is ~0) |
| transition | switch in the 80–82 m bin; y < 75 and y > 85 levels within ±0.01 |
| GT lateral x | within ±0.05 m |

**(c) The wall texture cannot enter the downward camera's view** (geometry, confirmed
from the flight):
- The downward camera sits ≈ 2.04 m above the floor (base_link 2.29 m, camera offset
  −0.25 m).
- Its worst-case half-footprint is 2.04 · tan(30° + 5.2° max tilt) ≈ **1.44 m**. The
  30° is the half-HFOV; the half-VFOV is 23.4°, which is smaller.
- GT |x| ≤ 0.01 m during cruise, so the footprint stays within |x| ≤ 1.45 m, against
  the walls' inner faces at |x| = 9.9 m.
- Along the corridor the drone stops at GT y ≤ 151.6 m, so the footprint reaches at
  most ~153 m, against the end wall's inner face at 164.9 m.
- The walls' shadows fall where they fell in `dsn_*` (identical geometry), and the
  end wall's shadow falls at y > 165.

The flights must reproduce GT |x| ≤ 0.05 m and y_max ≤ 153 m for (c) to hold.

### Phase 1 result — confound check (a) FAILED; flights stopped (2026-09-24)

Flown at `c89d05a`: `p1_control_tex`, then `p1_fwd_tex`. `p1_fwd_blank` was aborted
mid-cruise when (a) failed, and its directory is marked `ABORTED.txt` (not a valid
trial). `p1_fwd_trans` was not flown.

**(a) RTF: FAIL.**
- `p1_control_tex` ran at **0.954**, the same as the smoke test.
- `p1_fwd_tex` ran at **0.768**, below both the 0.92 floor and control − 0.03 = 0.924.
  Adding the forward camera costs about 19% RTF on this machine.
- Per the pre-registration: stop and report; no tuning.

**Rates**, as deviation from the `dsn_tex` mean:

| topic | `p1_fwd_tex` | `p1_control_tex` | in ±2% band? |
|---|---|---|---|
| `/downward_lidar/range` | 0.00% | — | yes |
| `/clock` | −0.10% | — | yes |
| `/optical_flow/measurement` | −0.43% | — | yes |
| `/imu/data_raw` | −0.50% | — | yes |
| `/forward_camera/image`, `camera_info` | 30.30 Hz (no frame loss) | — | yes |
| `/attitude/angular_rates` | **−2.64%** | +0.36% | no (fwd) |
| `/ekf/pose` | **−3.10%** | +0.06% | no (fwd) |
| `/ground_truth/pose` | **+13.2%** | **+2.55%** | no (both) |

The control's own ground-truth rate is also outside ±2%. Across flights, that rate
scales with 1/RTF (smoke 0.954 → +1.9%, control 0.954 → +2.55%, fwd 0.768 → +13.2%):
it is a **wall-clock-driven topic** (Gazebo's scene broadcaster), so a ±2% band was
the wrong criterion for it. Recorded as a criterion defect, not re-scored. The
MAVLink-sourced `/attitude/angular_rates` and `/ekf/pose` also lose ~3% of messages
at the lower RTF. Neither is an estimator input: the UKF/FGO consume `/imu/data_raw`,
flow and range, and EKF3 is read from the dataflash log.

**(b) Downward flow: PASS on `p1_fwd_tex`** (`eval/results/flow_quality_p1.json`):
- inlier_ratio 0.9741 (the `dsn` mean is 0.9733), 0.0% of frames below 0.5;
- features 53.0 against 52.8;
- `flow_y_raw` 136.05 against 136.45 px/s (−0.3%);
- GT x within ±0.01 m.

The second camera and the lower RTF leave the downward-flow conditions unchanged, as
expected: Gazebo↔SITL lockstep keeps sensor timing in sim time.

**(c) Geometry: holds.** GT |x| ≤ 0.01 m. Forward frames:
`plots/fwd_camera/p1_fwd_tex_forward_frames.png`.

**Harness: verified.** On `p1_control_tex`, `/proc/<pid>/cmdline` for the bridge and
the recorder are exactly the pre-fwd argument lists. On `p1_fwd_tex` they add only the
two forward topics.

**Open (awaiting a ruling).** The cause of the RTF loss was not isolated. The
candidates are:
- rendering the second camera on the 2 GB Quadro P620;
- the `ros_gz_bridge` image conversion;
- the bag writer (~9 MB/s sim of images);
- interaction with the background desktop load.

### Phase 1 follow-up — RTF diagnosis, and a direct test of whether RTF matters (2026-09-24)

**Diagnosis** (four 60 s cruise runs, one load removed at a time, same session;
diagnostic only, no configuration change). The runs use the `FWD_DIAG` switch in
`run_trial.sh`, which is unset by default.

| run | RTF | `gz sim` CPU | GPU |
|---|---|---|---|
| `p1diag_control_tex` (no forward camera) | **0.957** | ~130% | 28% |
| `p1diag_fwd_full` | **0.759** | ~170% | 27% |
| `p1diag_fwd_norecord` (bridged, not recorded) | **0.761** | ~170% | 26% |
| `p1diag_fwd_nobridge` (in the model, not bridged) | **0.958** | ~130% | 29% |

- **Rendering backend: hardware.** Ogre2 runs OpenGL 4.5 on the Quadro P620 (NVIDIA
  driver, EGL headless, `~/.gz/rendering/ogre2.log`), not the Mesa software device.
- **Recording costs nothing.** The **whole ~20% RTF loss appears once the forward image
  is consumed (bridged)**, as ~40% more CPU in the `gz sim` process, with GPU
  utilisation unchanged.
- **Caveat:** gz-sensors is understood to skip rendering a camera that has no
  subscribers, so "not bridged" probably also means "not rendered". The diagnosis
  therefore isolates "forward image produced" from "absent", but not rendering from
  bridge conversion. Either way the cost is CPU work inside the single `gz sim`
  process that paces the lockstep.
- **Not done:** the "desktop apps closed" run. It needs the user's desktop
  applications closed (Firefox ~70–110% CPU).

**Why RTF was only a proxy.** The confound that matters is whether the **estimator
inputs keep their `dsn_*` sim-time timing**. The UKF and FGO replay the bags offline
on header stamps, so they are affected only through those stamps. EKF3 is the one
estimator fed live, by wall-clock ROS nodes over MAVLink. So the questions are:
(a) the inputs' sim-time timing, (b) the flow delivery latency into EKF3 in sim time,
and (c) the outcome itself. RTF was a stand-in for all three.

**Direct test (pre-registered before flying).** One 300 s flight of the
**unchanged** `corridor_textured` world (the original iris, `dsn_*` settings), with RTF
lowered to ~0.77 by Gazebo's runtime `set_physics` service (`real_time_factor 0.77`,
`max_step_size 0.001` as in the world file). No file changes. This isolates RTF
itself. The forward camera's actual mechanism, CPU contention inside `gz sim`, is
covered by re-scoring `p1_fwd_tex` on the same three checks. The trial is
`p1rtf_dsn_tex`.

The baseline is `eval/results/input_timing_baseline.json`: all nine `dsn_*` bags, the
smoke test and the controls, from `eval/input_timing.py`.
- **(a) Estimator-input sim-time timing.** Measured on header stamps over the cruise
  window. Every baseline bag, **including `p1_fwd_tex` at RTF 0.768**, shows:
  - `/optical_flow/measurement` and `/downward_lidar/range` at 30.30 Hz, median and
    p99 gap 33.0 ms, 0.00% of gaps above 1.5 periods;
  - `/imu/data_raw` at 333.27–333.28 Hz, median gap 3.0 ms, p99 6–7 ms, and
    18.4–18.7% of gaps above 1.5× (a fixed alternation from receipt stamping).

  **Pass** if flow and lidar match exactly (30.30 Hz, 33.0 / 33.0 ms, 0.00%), and the
  IMU is within 333.27–333.28 Hz, p99 ≤ 7 ms, and 18.4–18.7%.
- **(b) Flow → EKF3 latency** (sim time; per-trial clock offset from `SIM` vs GT,
  METHODOLOGY `input_timing.py`).
  - **Tolerance: one EKF3 prediction step, 12.5 ms.** EKF3 time-stamps flow as
    receipt − `EK3_FLOW_DELAY` (10 ms) − half the frame interval − half its step
    (`AP_NavEKF3_Measurements.cpp:232-234`), so a latency shift below one step is
    below EKF3's own time resolution.
  - Baseline: the `dsn_tex` mean has median 10.9 ms and p95 42.7 ms, with 100% of
    valid frames matched.
  - **Pass** if the median is ≤ 23.4 ms, the p95 is ≤ 55.2 ms, and matching stays
    ≥ 99.5%.
  - **Stated openly:** `p1_fwd_tex`'s latency (median 19.8, p95 51.5) and the `dsn`
    world-to-world spread (transition medians up to 32.0 ms at RTF ~0.98) were seen
    before this tolerance was set. The tolerance comes from EKF3's time resolution,
    not from those numbers.
- **(c) evo -a (cruise)** within the smoke-test bands: **FGO [4.18, 5.35]** (the
  sensitive indicator), EKF3 [1.26, 8.13], UKF [0, 34.95] (sanity only).

**Decision rule.** If (a)–(c) pass on `p1rtf_dsn_tex`, **and** on `p1_fwd_tex`
re-scored the same way, a revised Phase 1 criterion replaces the RTF threshold. It is
written up as revised after the observed failure. If any check fails: stop and report.

**Direct-test result — one pre-registered sub-criterion FAILED; stopped per the
decision rule (2026-09-24).** `p1rtf_dsn_tex` was flown at `e37fd46` with the Gazebo
RTF target at 0.77, applied at runtime. Measured cruise RTF: **0.762**. `p1_fwd_tex`
was re-scored on the same checks. Results:
`eval/results/{input_timing_p1rtf,p1_rtf_test_evo}.json`.

| check | `p1rtf_dsn_tex` (RTF 0.762) | `p1_fwd_tex` (RTF 0.768) | band |
|---|---|---|---|
| (a) flow and lidar sim-time timing | 30.30 Hz, 33.0 / 33.0 ms, 0.00% | same | exact match: **pass** / **pass** |
| (a) IMU rate, p99 gap | 333.28 Hz, 6 ms | 333.28 Hz, 7 ms | **pass** / **pass** |
| (a) IMU % gaps above 1.5× | **18.24%** | 18.42% | 18.4–18.7%: **FAIL** / pass |
| (b) flow → EKF3 latency, median / p95 | 16.1 / 48.4 ms, 100% matched | 19.8 / 51.5 ms, 100% | ≤ 23.4 / ≤ 55.2 ms, ≥ 99.5%: **pass** / **pass** |
| (c) evo -a (cruise), FGO / EKF3 / UKF | **4.80** / 3.90 / 7.75 | **4.55** / 4.07 / 12.58 | [4.18, 5.35] / [1.26, 8.13] / [0, 34.95]: **pass** / **pass** |

**What the failed sub-criterion measures.** `/imu/data_raw` is stamped at *receipt*
by `imu_bridge.py` (ROS sim clock, `imu_bridge.py:169`). So its header gaps scatter
from 0 to ~9 ms around a mean that is **exactly 3.0005 ms in every trial**.

| trial | gaps of 2–3 ms | gaps of 0 ms | gaps ≥ 6 ms |
|---|---|---|---|
| `dsn_tex_r1` | 64.0% | 2.6% | 3.7% |
| `p1_control_tex` | 60.6% | 3.9% | 4.5% |
| `p1_fwd_tex` | 58.4% | 4.4% | 5.1% |
| `p1rtf_dsn_tex` | **70.0%** | **0.8%** | **2.2%** |

The throttled flight is **more regular** than `dsn_*`: the wall-clock bridge gets more
wall time per sim millisecond. Its lower ">1.5×" share is on the benign side. The
failure is nonetheless real against the band as pre-registered, and that band was
itself a **criterion-design error**: the exact observed n=12 range, with no margin.
This is the second such error after the ground-truth rate band. Not re-scored.

Per the decision rule, **the revised Phase 1 criterion is NOT written, and
`p1_fwd_blank` / `p1_fwd_trans` are NOT flown, pending a ruling.** `p1_fwd_tex` itself
passes every pre-registered (a)–(c) check.

**Side finding, independent of the forward camera.** The UKF and FGO integrate the IMU
on these receipt stamps, which carry 0–9 ms jitter around the true 3 ms sampling (the
`HIGHRES_IMU` `time_usec` is not used). It is common to every bag, so it does not bias
the comparison between conditions, but it is a property of the replay inputs. Logged
for the methodology.

**Note for Phase 3 (no action yet).** The end wall fills the forward view by y ≈ 150 m
(`plots/fwd_camera/p1_fwd_tex_forward_frames.png`), so the vanishing point, and the
wall lines that define it, disappear at the corridor end. The heading-from-structure
measurement therefore needs a per-frame confidence that goes to "no measurement" as
the VP leaves the frame or the converging-line support collapses. It must not report
a confident heading from the end-wall texture.

### RULING (user, 2026-09-24): the IMU gap-share miss is benign

Recorded as the user's ruling, **not a re-score**: *"the IMU gap-share miss is benign.
It measures bridge receipt jitter, not sensor timing; the deviation is towards more
regular gaps; the mean-gap check (3.0005 ms) and every direct confound check pass on
both trials. Replace the gap-share check with the mean-gap check plus p99 gap."*

The desktop-apps diagnostic run is skipped, because the cause is identified.

**Infrastructure note for later phases that add sensors.** Bridging a 640×480 30 Hz
image costs ~40% of a core inside the `gz sim` process. That process paces the
Gazebo↔SITL lockstep, so on this machine the cost shows up as a ~20% RTF drop. Any
further camera will cost roughly the same. Budget for it, and test estimator-input
timing directly rather than RTF.

### Phase 1 criterion — REVISED after the observed failures (pre-registered before `p1_fwd_blank` / `p1_fwd_trans`)

**Why it was revised.** The original gate (a) was RTF ≥ 0.92 plus ±2% topic rates.
RTF was a **proxy** for "the estimator inputs keep their `dsn_*` sim-time timing".
- It failed on `p1_fwd_tex` (0.768).
- The diagnosis traced the loss to bridging the forward image.
- The direct test, `p1rtf_dsn_tex` (the unchanged `dsn` world throttled to RTF 0.762),
  showed that lowering RTF leaves input timing, EKF3 flow latency and estimator outcome
  inside tolerance.
- The ±2% receive-rate band failed on the wall-clock-driven ground-truth topic, which
  is not an input.

The revised criterion therefore tests the confound directly. **It is a revision made
after seeing failures, and is stated as such.** RTF, receive rates and the IMU gap-share
become diagnostics. Baselines are the same-world `dsn_*` n=3 values
(`eval/results/{input_timing_baseline,phase0_cruise_pinned,flow_quality_dsn}.json`).

**PRIMARY**

| # | criterion | band and basis | why a miss would mean the confound |
|---|---|---|---|
| P1 | flow and lidar header timing (cruise) | rate 30.30 Hz ± 0.1%; ≤ 0.5% of gaps above 1.5 periods. `dsn` is exact (0.00%); 0.5% is one dropped frame per ~6.6 s, a negligible loss of information. | Dropped or late downward frames would mean the added load starves the downward pipeline. |
| P1 | IMU header timing (cruise) | mean gap 3.0005 ± 0.003 ms (0.1% = one lost sample in 1000; `dsn` is exact to 0.0001 ms); p99 gap ≤ 10 ms (the `dsn` maximum of 7 ms plus one 3 ms period, at most one extra late sample at the 99th percentile). | Lost or late IMU samples. |
| P2 | flow → EKF3 latency (median and p95) | ≤ same-world `dsn` mean + **12.5 ms** (one EKF3 prediction step, its own time resolution; `AP_NavEKF3_Measurements.cpp:232-234`). Matched frames ≥ same-world `dsn` minimum − 5 pp (`dsn` blank spreads 7 pp). | EKF3 would fuse flow at a different effective time than in `dsn_*`. |
| P3 | downward flow conditions (unchanged from the original (b)) | inlier mean ±0.01 of the `dsn` mean (8× the textured n=3 range, ~1.5% of the textured–blank gap); % below 0.5 within ±3 pp; features ±5%; `flow_y_raw` ±2% (textured, transition; ≈ 1 cm of height or 1 cm/s of speed) or ±5 px/s (blank); transition switch in the same 2 m bin (the metric's resolution), levels ±0.01; GT \|x\| ≤ 0.05 m. | The downward image content or geometry changed. |
| P4 | outcome, **textured** | evo -a (cruise) within the n=3 range widened by one range-width each side: **FGO [4.18, 5.35]**, **EKF3 [1.26, 8.13]**. | The forward-camera setup changed estimator behaviour through the shared inputs. |
| P4 | outcome, **transition / blank** (failure metrics, cruise) | For **EKF3 and the FGO**: displacement ratio within the n=3 range ± max(range, 0.05), where 0.05 is the window-sensitivity bound. Onset within the n=3 range ± max(range, 5 m), a third of the 15 m divergence threshold. Transition: EKF3 ratio [0.51, 0.63], onset [96, 108] m; FGO ratio [0.68, 0.80], onset [90, 101] m. Blank: EKF3 ratio [0.12, 0.27], onset [13, 24] m; FGO ratio [1.52, 1.70], onset [17, 30] m. | Same as above. |

**DIAGNOSTIC** (reported, never a gate):
- RTF, and topic receive rates (`topic_rates.py`), including `/ground_truth/pose`,
  `/attitude/angular_rates` and `/ekf/pose`
- the IMU ">1.5× gap" share
- every UKF metric (its n=3 range is too wide to gate on)
- evo -a (cruise) on transition and blank (a failure regime, not a quality metric)
- the forward-image rate (30.30 Hz expected)

**`p1_fwd_tex` re-scored under the revised criterion: PASS.**
- **P1:** flow and lidar exact; IMU mean gap 3.0005 ms, p99 7 ms.
- **P2:** latency median 19.8 / p95 51.5 ms, against ≤ 23.4 / ≤ 55.2; 100% matched.
- **P3:** pass (above).
- **P4:** FGO 4.55, EKF3 4.07.
- Diagnostics: RTF 0.768, UKF 12.58.

### Phase 1 result under the revised criterion — ALL THREE fwd worlds PASS (2026-09-24)

`p1_fwd_blank` and `p1_fwd_trans` were flown at `cc588df`. Results:
`eval/results/{input_timing_p1fwd,flow_quality_p1fwd,p1_fwd_evo}.json`.
Frames: `plots/fwd_camera/p1_forward_frames_all.png`.

| | `p1_fwd_tex` | `p1_fwd_trans` | `p1_fwd_blank` |
|---|---|---|---|
| **P1** flow and lidar (30.30 Hz, 33 / 33 ms, 0%) | pass | pass | pass |
| **P1** IMU mean gap / p99 | 3.0005 / 7 ms | 3.0005 / 6 ms | 3.0005 / 6 ms |
| **P2** latency median (limit) | 19.8 (≤ 23.4) | **38.4 (≤ 40.0)** | 21.1 (≤ 28.0) |
| **P2** latency p95 (limit) | 51.5 (≤ 55.2) | 57.7 (≤ 59.0) | 53.2 (≤ 59.3) |
| **P2** matched (floor) | 100% (≥ 95.0) | 99.0% (≥ 93.5) | 82.0% (≥ 72.4) |
| **P3** inlier mean (`dsn` mean) | 0.9741 (0.9733) | 0.6654 (0.6645) | 0.3132 (0.3139) |
| **P3** % below 0.5 / features / `flow_y_raw` | 0.0 / 53.0 / 136.05 | 39.5 / 31.6 / 72.29 (+1.2%) | 84.5 / 8.0 / −2.30 |
| **P3** transition switch, levels | — | 80–82 m bin; 0.974 / 0.313 | — |
| **P4** EKF3 | evo -a (cruise) 4.07 | ratio 0.56, onset 101 m | ratio 0.21, onset 20 m |
| **P4** FGO | evo -a (cruise) 4.55 | ratio 0.71, onset 94 m | ratio 1.58, onset 24 m |
| *diag.* RTF | 0.768 | 0.752 | 0.743 |
| *diag.* UKF | 12.58 | ratio 0.76, onset 53 m | ratio 1.30, onset 54 m |
| *diag.* forward image rate | 30.30 Hz | 30.30 Hz | 30.30 Hz |

**Every primary criterion passes in all three worlds.**
- **Closest to its limit:** the transition latency median, 38.4 against 40.0. The
  `dsn` transition medians already span 20.6–32.0 at RTF ~0.98, so latency on that
  world is the least stable quantity. It is flagged for Phase 2, where it gets n=3.
- **Downward flow is indistinguishable from `dsn_*`** in every world, on every P3
  metric. The texture boundary still falls in the same 2 m bin.
- **Diagnostic observation:** the UKF's transition onset was 53 m (`dsn` 69–82). It is
  not a gate, since the UKF is unstable across repeats.

**Phase 1 complete.** Phase 2 (`fwd_*`: 3 worlds × 3 repeats) is gated on the user's
go, and will apply this same revised criterion to all nine bags.

### Phase 1 P2 re-checked on the corrected (offset + rate) clock map (2026-09-24)

**P2 re-checked on the corrected measurement.** The limit is the same-world `dsn` mean
plus 12.5 ms. `dsn` medians / p95: textured 14.5–17.6 / 23.7–24.9, transition
15.2–20.5 / 24.8–27.7, blank 16.4–18.9 / 24.9–27.0.

| trial | median (limit) | p95 (limit) | verdict |
|---|---|---|---|
| `p1_fwd_tex` | 20.7 (≤ 28.1) | 31.5 (≤ 36.7) | pass |
| `p1_fwd_trans` | 27.7 (≤ 30.4) | **37.2 (≤ 38.3)** | pass |
| `p1_fwd_blank` | 27.4 (≤ 29.9) | **37.9 (≤ 38.2)** | pass, 0.3 ms margin |
| `p1rtf_dsn_tex` | 19.9 (≤ 28.1) | 28.6 (≤ 36.7) | pass |

**All still pass, but the tighter measurement exposes a real, systematic effect.** The
forward camera adds **~5–10 ms median and ~8–13 ms p95** of flow→EKF3 latency. RTF
alone (`p1rtf`) adds ~4 ms median.

EKF3 assumes ~10 ms plus half a frame (`EK3_FLOW_DELAY`). Its flow time-alignment error
therefore grows from ~5 ms (`dsn`) to ~11–18 ms (`fwd`), up to ~1.4 EKF3 prediction
steps. It is an input to **EKF3 only**; the UKF/FGO replay on capture stamps. The
margins on transition and blank p95 are thin, so **Phase 2's n=3 may cross P2**. That
possibility is flagged now, before any Phase 2 data exists.

### Framing corrections to the Phase 1 P2 results (2026-09-24)

- **`p1_fwd_tex` re-score limits.** The "≤ 23.4 / ≤ 55.2 ms" limits in the revised-
  criterion re-score came from the single-offset clock and are **superseded** by the
  linear-map table in the clock-rate FINDING (limits ≤ 28.1 / ≤ 36.7; 20.7 / 31.5,
  pass).
- **Blank p95 margin.** 37.9 against a 38.2 limit is **at the limit, within measurement
  uncertainty**. The clock map is good to a few ms, not 0.3 ms. It is reported as a
  pass under the criterion as written, but not as a clean pass. Transition (1.1 ms
  margin) is similar.
- **Scope of the latency effect.** The extra 5–10 ms of flow→EKF3 latency affects EKF3
  only.
  - It does **not** confound the Phase 5 hypothesis test, which compares with and
    without the forward-camera measurements on the same `fwd_*` bags.
  - It **does** confound any comparison of EKF3 on `fwd_*` against EKF3 on `dsn_*`.
    That comparison must carry this caveat or be avoided.
- **Open before Phase 2, to be ruled before any `fwd_*` data exists** (pre-registration
  rule):
  1. Is P2 judged per trial or on the n=3 mean?
  2. Does the 12.5 ms band have to absorb the latency measurement's own uncertainty,
     about ±5 ms from the clock map? If so, it becomes an explicit stated margin.

### RULING (user, 2026-09-24): P2 is DIAGNOSTIC for Phase 2 (recorded before any `fwd_*` data exists)

**Reasoning, as ruled.**
- The forward camera's added EKF3 flow latency (~5–10 ms median) is now
  **characterised**.
- Phase 5 compares each estimator **with and without** the forward-camera
  measurements **on the same bags**, so both arms share that latency. It cannot
  confound the hypothesis test.

**Therefore, for Phase 2:**
- **P2 (flow → EKF3 latency) is DIAGNOSTIC.** Its band is unchanged: same-world `dsn`
  mean + 12.5 ms, on the corrected (offset + rate) clock map. It is reported **per
  trial and as the n=3 mean**.
- **Stays PRIMARY:** EKF3 evo -a (cruise) on textured, EKF3 failure metrics on
  transition and blank, and P1, P3 and the FGO's P4.

**STANDING RULE: EKF3 on `fwd_*` is never compared with EKF3 on `dsn_*` without stating
the flow-latency difference** (median and p95, per world, from `eval/input_timing.py`).

### Phase 4 design note (updated 2026-09-29 by the EKF3 ruling below)

Any estimator's with- and without-forward-camera arms **must come from the same sensor
logs**. The datasets are `fwdc_*` and `fwdplainc_*`; the earlier `fwd_*` is superseded.

**EKF3: RULED (user, 2026-09-29). See "RULING — EKF3 in the offline forward-camera
comparison".**
- For the offline comparison, EKF3 is the fixed no-yaw-source baseline.
- Only the UKF and the FGO get forward-camera arms.
- ArduPilot Replay was the intended route, but it is **not available on the recorded
  logs**: they were flown with `LOG_REPLAY=0` and hold no replay records.

## Phase 2 — `fwd_*` dataset: pre-registration (2026-09-24, before any `fwd_*` data exists)

**Dataset.** `fwd_{tex,trans,blank}_r{1,2,3}`: the three `corridor_*_fwd` worlds × 3
repeats, 300 s, 0.5 m/s, 2.0 m, no compass (`gnss_denied_nomag.parm`),
`sim_noise.parm`, RANSAC seed 42, `run_trial.sh`. Everything matches `dsn_*` except:
- **By design:** the forward camera (`iris_fwd`), the line-textured walls and the
  end wall.
- **Recording deviations, all additive:**
  - `/forward_camera/image` and `camera_info` (needed by Phase 3);
  - `/imu/time_ref` (HIGHRES_IMU `time_usec`; OI-2 infrastructure; first flight
    verifies it);
  - `forward_camera: true` in `metadata.yaml`.

**Flight order is interleaved** (tex r1, trans r1, blank r1, tex r2, …), so any drift
in machine state over the session is spread across worlds rather than aliased onto
one. Replays use the current baseline estimators (OI-2 dejitter). Evaluation uses
`eval/three_way_eval.py`, `eval/input_timing.py` (clock map) and
`eval/flow_quality.py`.

**PRIMARY** (judged per trial; a miss that could change a conclusion stops the phase):

| # | criterion | band and basis |
|---|---|---|
| P1 | estimator-input header timing | As in Phase 1: flow and lidar at 30.30 Hz ± 0.1% with ≤ 0.5% of gaps above 1.5×; IMU mean gap 3.0005 ± 0.003 ms, p99 ≤ 10 ms. |
| P3 | downward-flow conditions vs same-world `dsn` n=3 | As in Phase 1: inlier ±0.01, % below 0.5 within ±3 pp, features ±5%, `flow_y_raw` ±2% (±5 px/s on blank), transition switch in the 80–82 m bin with levels ±0.01, GT \|x\| ≤ 0.05 m. |
| P4 | EKF3 outcome, unchanged by OI-2 | Textured evo -a (cruise) [1.26, 8.13]. Transition ratio [0.51, 0.63], onset [96, 108] m. Blank ratio [0.12, 0.27], onset [13, 24] m. Basis as in Phase 1. |
| P4 | FGO outcome, **rebased on the dejittered `dsn` baseline** | **Textured evo -a (cruise) [4.17, 5.14]:** the n=3 range 4.57–4.74 ± max(range 0.17, **0.40 m**). The 0.40 m floor is the *measured* sensitivity of FGO evo -a to IMU-timestamp treatment (per-repeat moves up to 0.39 m across the OI-2 variants); a one-range margin of 0.17 m would sit below the pipeline's own known sensitivity. **Transition:** ratio 0.72–0.73 ± 0.05 → [0.67, 0.78]; onset 95–96 ± 5 → [90, 101] m. **Blank:** ratio 1.50–1.55 ± 0.05 → [1.45, 1.60]; onset 33–37 ± 5 → [28, 42] m. Basis as in Phase 1. |

**DIAGNOSTIC** (reported, never a gate):
- **P2**, flow → EKF3 latency against the same-world `dsn` mean + 12.5 ms, reported per
  trial and as the n=3 mean (ruling above);
- RTF; topic receive rates; the forward-image rate;
- `/imu/time_ref` presence and rate;
- every UKF metric;
- evo -a (cruise) on transition and blank.

**Why a primary miss would indicate the confound.**
- P1 and P3: the forward-camera setup would be altering the shared inputs.
- P4: estimator behaviour would differ from `dsn_*` through those inputs. Without
  forward-camera measurements fused, the bags should be `dsn_*`-equivalent for every
  estimator.

### Phase 2 result — STOPPED pending ruling (2026-09-24)

**Flown.** All nine `fwd_*` trials completed first time, with no aborts. Commit
`7967a39`, run by `run_resumable_batch.sh` in tmux. Interleaved order, 09:10:46–10:19:45:
69.0 min against the 70 min estimated from the Phase 1 fwd wall-clock times.
- Per-trial event log: `~/thesis_data/batches/phase2_fwd/trials.log`.
- Crash-safety: the runner exists because a kernel panic (rt2800usb Wi-Fi dongle
  disconnect → xhci NULL dereference, recovered from pstore) froze the machine
  before the batch. The Wi-Fi stayed on.
- `/imu/time_ref` is present in every bag at 332.4–333.3 Hz, matching the IMU. This is
  the first-flight verification the pre-registration asked for.

**Replays.** UKF and FGO (window 0.25 s) with the OI-2 dejitter, exactly as the `dsn`
baseline: re-running `dsn_tex_r1` reproduced both stored trajectories byte for byte.
Results: `eval/results/{input_timing_p2fwd,flow_quality_p2fwd,phase2_fwd_evo,phase2_score}.json`.
Scorer: `eval/phase2_score.py`, which applies the pre-registered bands verbatim.

| trial | P1 | P3 | P4 EKF3 | P4 FGO | primary |
|---|---|---|---|---|---|
| `fwd_tex_r1` | pass | pass | 4.37 | **5.158 (> 5.14)** | **FAIL** |
| `fwd_tex_r2` | pass | pass | 4.15 | 4.71 | pass |
| `fwd_tex_r3` | pass | pass | 4.41 | 4.53 | pass |
| `fwd_trans_r1` | pass | pass | 0.55 / 101 m | 0.72 / 95 m | pass |
| `fwd_trans_r2` | pass | pass | 0.56 / 101 m | 0.72 / 95 m | pass |
| `fwd_trans_r3` | pass | pass | 0.55 / 100 m | **not evaluated** | **incomplete** |
| `fwd_blank_r1` | pass | pass | 0.19 / 19 m | 1.51 / 36 m | pass |
| `fwd_blank_r2` | pass | pass | 0.20 / 19 m | 1.51 / 36 m | pass |
| `fwd_blank_r3` | pass | pass | 0.22 / 20 m | 1.52 / 32 m | pass |

P4 textured cells are evo -a (cruise) in m. Transition and blank cells are
displacement ratio / onset.
- **P1:** flow and lidar are exactly 30.30 Hz with 0% late gaps in all nine. IMU mean
  gap is 3.0005 ms and p99 is 6 ms in all nine.
- **P3:** every metric is inside its band in all nine. The transition switch falls in
  the 80–82 m bin in all three.

**Primary miss 1: `fwd_tex_r1` FGO evo -a (cruise) = 5.158, band [4.17, 5.14].**
- It is over by 0.018 m. The band's 0.40 m floor is already the measured IMU-timing
  sensitivity, so the miss is not argued away as noise.
- Under the standing rule, whether it could change a conclusion is **the user's
  ruling**. It was not investigated.
- Facts already on disk, stated without analysis:
  - The FGO n=3 mean is 4.80, inside the band; r2 and r3 are 4.71 and 4.53.
  - EKF3 on the same bag is normal (4.37). EKF3 does not use the bridged IMU stream.
  - The **UKF on the same bag is 42.73** (diagnostic), against a `dsn` range of
    9.96–20.71, with displacement ratio 0.15 and onset 43 m. Its r2 and r3 are 7.67
    and 9.31.
  - So the two replays driven by the bridged IMU both sit high on this bag.
  - Its dejitter stats are unremarkable: residual std 3.35 ms, max 11.84 ms.

**Incomplete: `fwd_trans_r3` UKF/FGO replay refused by the dejitter guard**
(`imu_timing.py`, residual 30.2 ms > 25 ms).
- **Cause, from `/imu/time_ref`:** one real IMU dropout. A single 29.99 ms step in
  SITL sensor time means about 9 samples never arrived. It happened at t ≈ 6.16 s, in
  the first 0.65 s of the IMU stream: on the ground, pre-arm, about 24 s before the
  cruise window.
- No other bag has one. With the first 2 s excluded, this bag's residual max is
  11.2 ms and the fit moves 0.23 ms.
- The guard behaved as designed and has **not** been changed.
- EKF3 is unaffected, since it runs live in SITL. It is scored from a
  `ukf/ground_truth.tum` written by `eval/extract_gt_tum.py`. That method was verified
  byte-identical on `fwd_trans_r2`. **That `ukf/` folder holds ground truth only, with
  no UKF trajectory.**
- **Options for the ruling:**
  - **(a), recommended:** start this bag's replay at the first IMU sample after the
    single dropout. That trims only the pre-arm, on-ground segment (t < 6.17 s) and
    leaves the cruise window untouched.
  - **(b)** Accept n=2 for UKF/FGO on transition.
  - **(c)** Fly an extra trial. It breaks the interleaved order, gives a new
    trajectory realisation, and the dropout could recur.
  - **Not an option:** using `/imu/time_ref` sensor time for this one bag. That is the
    OI-2 residual option, batched for the consolidated re-run, and it would make this
    bag inconsistent with the other eight.

**Diagnostics (reported, never a gate).**
- **P2 flow → EKF3 latency** (median / p95 ms):
  - textured 24.9/34.4, 22.7/33.5, 19.7/29.6 (n=3 mean 22.4/32.5; limits ≤ 28.1/36.7)
  - transition 21.4/31.5, 25.7/35.9, 22.6/35.7 (mean 23.2/34.4; limits ≤ 30.4/38.2)
  - blank 29.2/39.4, 24.1/33.9, 25.1/36.1 (mean 26.1/36.5; limits ≤ 29.9/38.2)
  - **`fwd_blank_r1` p95 exceeds its limit: 39.4 against 38.2.** Phase 1 flagged this
    possibility in advance.
  - Matched frames: textured 100%, transition 98.7–98.8%, blank 80–82%, all above
    their floors.
  - This is the flow-latency difference the STANDING RULE requires to be stated
    alongside any EKF3 `fwd` vs `dsn` comparison, including P4 above.
- **RTF:** 0.73–0.81. Forward image 30.29–30.30 Hz.
- **IMU dejitter residual max** (ms): 11.8, 10.9, 12.8 (textured); 21.8, 13.5, refused
  (transition); 11.0, 12.1, 11.8 (blank). The `dsn` validity was ±13 ms.
  `fwd_trans_r1`'s 21.8 is under the guard but outside that range.
- **UKF evo -a (cruise):** 42.73 / 7.67 / 9.31 (textured).
- **evo -a (cruise) on transition and blank:**
  - EKF3: 21.9 / 21.7 / 22.0 (transition); 34.8 / 34.9 / 34.0 (blank)
  - FGO: 25.8 / 26.3 / — (transition); 25.6 / 25.7 / 26.0 (blank)

**Status.** Phase 2 is **not** declared passed.
- `fwd_tex_r1`'s primary miss needs a ruling.
- `fwd_trans_r3`'s UKF/FGO needs a handling ruling before it is computed. No
  provisional number was produced, so the rule comes before the result.
- Everything else passes every primary criterion.

### RULE — IMU gaps and the replay estimators (user ruling, 2026-09-24; recorded before any result under it)

**Rule.**
- **A gap before arming:** the UKF/FGO replay starts at the first IMU sample after
  the (last) gap.
- **Any gap after arming:** the bag is **unusable for the replay estimators**
  (UKF/FGO). It is reported as such, and EKF3 is still scored.

**Definitions** (`eval/imu_gap_check.py`; verdict written to `<trial>/imu_gaps.json`,
read by the replays):
- **Gap.** A step in `/imu/time_ref` sensor time (HIGHRES_IMU `time_usec`) larger than
  **10 ms**.
  - In all nine `fwd_*` bags the normal steps are only 2, 3, 5 and 6 ms. The 333 Hz
    stream is sampled off SITL's 400 Hz loop, so steps alternate while averaging
    3.0005 ms.
  - The two real dropouts found are 20 and 30 ms. So 10 ms sits above every normal
    step and below both.
- **Arming.** The first dataflash `ARM` record with ArmState = 1.
  - `time_usec` and `TimeUS` are the same clock (`AP_HAL::micros64()`,
    GCS_Common.cpp:2298), so no clock mapping is involved.
- **Replay start.** The replay drops every event (all sensors) before the start
  stamp, so the estimator initialises on the stationary data after it. Its
  initialisation (range height, levelling from gravity) only needs stationary data.
- **Scope.** Bags without `/imu/time_ref` (all `dsn_*`) cannot be checked, and their
  replays are unchanged. They passed the dejitter validity check (residuals within
  ±13 ms, no dropped-sample step).

**Applying the rule to all nine `fwd_*` bags catches two, not one:**
- `fwd_trans_r3`: a 30 ms gap at t = 6.16 s (arming 24.09 s). This is the bag the
  dejitter guard refused.
- **`fwd_trans_r1`: a 20 ms gap at t = 14.04 s (arming 24.13 s).** The guard did not
  catch it, because its residual (21.8 ms) is under the 25 ms limit. Its UKF/FGO
  result reported above was computed with the pre-gap samples mis-timed by ~17 ms. It
  is re-replayed under the rule, and any change is reported.
- The other seven have no gap.

### RULING 1 — `fwd_tex_r1` FGO primary miss (user, 2026-09-24; recorded before the check)

**The miss stands as recorded.** Before the user rules on the bag's use, there is
**one bounded check, time-boxed to one hour**, reading only what is on disk or cheap
to compute:
1. UKF and FGO yaw error over the cruise window, r1 against r2/r3.
2. Simulated gyro drift over the cruise window, per bag: arming time within the
   triangle-wave cycle, and the true bias ramp during cruise.
3. Any IMU-stream difference between r1 and r2/r3 beyond the gap check: dejitter
   residual statistics, and `time_ref` against receipt timing.

**Decision rule** (recorded now):
- **If the cause is a property of the flight** (for example the drift phase): the bag
  is kept, with the miss recorded.
- **If it is an input defect:** the bag is excluded, and one replacement trial is flown
  at the end of the batch, with the order break documented.
- **If nothing explains it within the hour:** that is reported and not investigated
  further.

**`fwd_blank_r1` P2 p95 (39.4 against 38.2 ms):** diagnostic under the
reclassification. Recorded; no action.

### IMU-gap rule applied (2026-09-24)

`imu_timing.apply_gap_rule`, called by both replays before the dejitter, reads
`<trial>/imu_gaps.json`.
- **Unchanged where no rule applies.** Re-running with the rule in place reproduced
  the stored UKF and FGO trajectories **byte for byte** on `dsn_tex_r1` (no file) and
  `fwd_tex_r2` (verdict "ok").
- **Remaining pre-arm stationary period**, from replay start to takeoff (first GT
  height 5 cm above rest). Over both periods the GT horizontal speed is 0.0 m/s and the
  height span is 0.0 m.

| trial | gap | replay start | arming | takeoff | stationary (of which before arming) |
|---|---|---|---|---|---|
| `fwd_trans_r1` | 20 ms at 14.04 s | 14.062 s | 24.13 s | 27.61 s | 13.5 s (10.1 s) |
| `fwd_trans_r3` | 30 ms at 6.16 s | 6.190 s | 24.09 s | 27.56 s | 21.4 s (17.9 s) |

**Results** (`eval/results/phase2_fwd_evo.json`; `fwd_trans_r1`'s pre-rule result is
kept under `superseded`, and its old replay folders are renamed `*_pregaprule`):
- **`fwd_trans_r3`:** now evaluated, and **passes every primary criterion.**
  - FGO: ratio 0.716 [0.67, 0.78], onset 95.1 m [90, 101].
  - EKF3 unchanged: 0.55 / 100.5 m.
  - UKF (diagnostic): 8.95, ratio 0.957, onset 71.1 m.
- **`fwd_trans_r1`:** the rule changes almost nothing.
  - FGO evo -a (cruise) 25.849 → 25.840, with ratio 0.724 and onset 95.5 m unchanged.
  - UKF (diagnostic) 8.66 → 7.98, ratio 0.959 → 0.963, onset 70.4 → 68.7 m.
  - Still passes.
- **Phase 2 primary status:** eight of nine pass. The only miss is `fwd_tex_r1` FGO
  (Ruling 1).

### Ruling 1 bounded check — result (2026-09-24, well inside the one-hour box)

Textured cruise windows; reference = the other five textured bags (`fwd` r2/r3, `dsn`
r1–r3).

**(1) Yaw error against GT heading.** Change from cruise start to the 25/50/75/100%
points, in degrees:

| bag | FGO Δ at 100% | FGO RMS Δ | UKF Δ at 100% |
|---|---|---|---|
| `fwd_tex_r1` | **−49.4** | 23.7 | **+451.5** |
| `fwd_tex_r2` / `r3` | −45.6 / −44.8 | 21.7 / 21.1 | +25.7 / +50.7 |
| `dsn_tex_r1` / `r2` / `r3` | −45.6 / −46.6 / −44.0 | 21.5 / 22.1 / 20.6 | +152.0 / +64.8 / +184.5 |

- The FGO's heading error on r1 ends ~4° beyond the other five, which span −44.0 to
  −46.6.
- The UKF's heading runs away (yaw drift 89.6 deg/min; gyro-bias estimate −116 deg/min
  against a true 8.9).
- **Both replay estimators drift further in yaw on this bag.** That localises the
  higher UKF/FGO scores to heading error. It does not say why the heading drifts more.

**(2) Simulated gyro drift: identical across all six bags.**
- Cruise starts 29.8–30.4 s after boot. The triangle-wave true bias runs from
  1.49–1.52 to 13.35–13.41 deg/min over cruise, with a mean of 8.87–8.90.
- The phase and ramp are the same to within ~0.5 s, so the drift phase **does not**
  distinguish r1.

**(3) IMU stream: no difference.**
- Beyond the gap check, which found no gap on r1, measured from `/imu/data_raw`
  against GT yaw rate over cruise:

  | quantity | r1 | other five |
  |---|---|---|
  | gyro-z bias mean (deg/min) | −8.890 | −8.877 to −8.913 |
  | gyro-z bias ramp (deg/min/min) | −2.841 | −2.812 to −2.829 |
  | 10 s-bin std (deg/min) | 4.12 | 4.09–4.11 |
  | gyro x/y means | same | same |
  | GT yaw span (°) | 0.12 | 0.12–0.14 |

- Dejitter residual std / max, in ms: r1 3.35 / 11.8; r2 3.40 / 10.9; r3 3.41 / 12.8.
- `time_ref` against receipt timing (header minus a linear fit on sensor time), std /
  max in ms: r1 3.25 / 11.0; r2 3.30 / 11.1; r3 3.31 / 12.1.

**Conclusion under the pre-recorded decision rule: none of the three explains it.**
- Neither the drift phase (a flight property) nor an IMU-stream defect (an input
  defect) differs on r1.
- The check localises the miss to larger estimator heading drift on identical IMU
  input. Its cause was not found within the box, and is **not investigated further**.
- The bag's use is the user's ruling.

### RULING (user, 2026-09-24): `fwd_tex_r1` is KEPT; the P4 miss stays recorded

**The bag is kept. Its P4 primary miss (FGO evo -a (cruise) 5.158 against a band of
[4.17, 5.14]) stays recorded as a miss.** It is not re-scored and not waived.

**Reasoning, as ruled.**
- **No defect, so no exclusion.** The decision rule allowed exclusion only for an input
  defect, and the bounded check found none: identical drift phase, identical IMU
  statistics, no gap. Excluding or re-flying a bag because an estimator performed
  badly on it, without a defect, would be **selection bias**.
- **The excess error is heading drift in the unobservable direction.** The UKF runaway
  (+451°) is the documented consistency failure ("Filter consistency — measured
  overconfidence in the weakly-observable directions") at a larger magnitude.
  - This is **run-to-run variability in an unobservable state**, which n=3 bands
    cannot fully capture.
  - It links to the open `dsn` noise-floor item ("The n=3 ranges are not a noise
    floor"). No new work on that now.
- **The world did not introduce the confound.**
  - EKF3 is normal (4.37).
  - P3 passes.
  - The FGO n=3 mean (4.80) is in band.
  - Together these indicate the new world did not introduce the confound P4 guards
    against.
- **Flagged for Phase 5 as the high-heading-drift case.** `fwd_tex_r1` is reported
  **individually as well as in the means**.

## Phase 2 — COMPLETE (2026-09-24), one recorded primary miss

All nine `fwd_*` bags are in the dataset.
- **Primary:** P1 and P3 pass in all nine. P4 passes in eight.
- **The one miss:** `fwd_tex_r1` FGO evo -a (cruise), kept per the ruling above and
  flagged for Phase 5.
- **IMU-gap rule:** `fwd_trans_r1` and `fwd_trans_r3` were replayed under it.
- **Diagnostic, no action:** `fwd_blank_r1` P2 p95 (39.4 against 38.2 ms).
- **Results:** `eval/results/{input_timing_p2fwd,flow_quality_p2fwd,phase2_fwd_evo,phase2_score}.json`.

## Scope reframing — textured walls are the UPPER BOUND (user, 2026-09-24)

**The thesis is about featureless environments.** Line-textured walls give the forward
camera close to best-case conditions.
- **The `fwd_*` dataset (textured walls) is the upper bound for a forward heading
  cue.** It shows what a forward cue can do when the walls give it rich structure.
- **No claim that a forward cue works in featureless environments is made from
  `fwd_*`.**
- The featureless case is the **plain-wall** dataset `fwdplain_*` below. It is promoted
  from "a later ablation" (Forward camera — worlds, design decision) into the **main
  experiment**.
- **Phases 3–5 run on both datasets:** `fwd_*` as the upper bound, `fwdplain_*` as the
  featureless case.

### Design decision — `corridor_{textured,blank,transition}_fwdplain.sdf` (recorded before building or flying)

**Construction.** Each is the corresponding `_fwd` world with these changes only:
- the `<world name>`;
- the side walls use `model://corridor_wall` (plain grey, the `dsn` walls) in place of
  `corridor_wall_lined`;
- the end wall uses `model://corridor_end_wall_plain`: the same 19.8 × 0.2 × 5 m box and
  pose as `corridor_end_wall`, with `corridor_wall`'s untextured material.

The floor tiles, `ground_collision`, lighting, spawn, physics and the `iris_fwd` drone
are identical to `_fwd`. Equivalently, each plain world is its `dsn` world plus the
forward camera and the plain end wall.

**Reasoning.**
- **The only forward-visible structure is geometric:** the wall–floor junctions, the
  end wall's outline, and the shading differences between faces under the fixed sun.
  Those structural edges are all a forward camera would have in a featureless
  corridor.
- **The geometry and lighting stay normal**, so the scene is not made artificially
  empty.
- **No ceiling exists** in any corridor world (`dsn`, `_fwd`). None is added: it would
  change the geometry and the lighting relative to both reference datasets.
- **The end wall is kept, but made plain.** Removing it would change the geometry
  against `_fwd`. Keeping it textured would leave a texture cue.
- **The floor is unchanged,** so downward-flow conditions should match `dsn` and
  `fwd`, and floor texture stays the only variable between the three worlds.

**Harness.** `run_trial.sh` enables the forward-camera bridge and recording for world
names matching `*_fwd` **or** `*_fwdplain`. Every other world's bridge and recorder
argument lists are unchanged (the same empty-array mechanism as `_fwd`).

### Plain-wall Phase 1 — confound check, pre-registered before flying

**Flights.** One flight per plain world: `p1plain_{tex,trans,blank}`, at the
`dsn`/`fwd` settings (0.5 m/s, 2.0 m, 300 s, no compass, `sim_noise.parm`, RANSAC seed
42). Flown with `run_resumable_batch.sh` in tmux, in the order tex, trans, blank.

**Criteria.** These are the Phase 1 primary checks under the revised criterion, with
the Phase 2 bands. Baseline: the same-world `dsn` n=3 values.

| # | criterion | band | status |
|---|---|---|---|
| P1 | estimator-input header timing | flow and lidar 30.30 Hz ± 0.1%, ≤ 0.5% of gaps above 1.5×; IMU mean gap 3.0005 ± 0.003 ms, p99 ≤ 10 ms | PRIMARY |
| P3 | downward-flow conditions | inlier ±0.01, % below 0.5 within ±3 pp, features ±5%, `flow_y_raw` ±2% (±5 px/s on blank), transition switch in the 80–82 m bin with levels ±0.01, GT \|x\| ≤ 0.05 m | PRIMARY |
| P4 | EKF3 outcome | textured evo -a (cruise) [1.26, 8.13]; transition ratio [0.51, 0.63], onset [96, 108] m; blank ratio [0.12, 0.27], onset [13, 24] m | PRIMARY |
| P4 | FGO outcome (dejittered baseline) | textured [4.17, 5.14]; transition ratio [0.67, 0.78], onset [90, 101] m; blank ratio [1.45, 1.60], onset [28, 42] m | PRIMARY |
| P2 | flow → EKF3 latency against same-world `dsn` mean + 12.5 ms | as Phase 2 | DIAGNOSTIC (the 2026-09-24 ruling's reasoning applies unchanged: Phase 5 compares with and without the forward cue on the same bags) |
| — | RTF, topic rates, forward-image rate, `/imu/time_ref`, every UKF metric, evo -a (cruise) on transition and blank | report | DIAGNOSTIC |

**Why a miss would mean the confound.** It is the same reasoning as Phases 1 and 2.
P1 and P3 test whether the forward camera's load, or the new walls, alter the shared
inputs. P4 tests whether estimator behaviour changes through them.

**Handling.**
- The IMU-gap rule applies: pre-arm gap → trim; post-arm gap → UKF/FGO unusable and
  reported, so FGO P4 is then NOT EVALUATED for that flight.
- **Gate:** the `fwdplain_*` batch starts only if every evaluated primary criterion
  passes on all three flights. A primary miss stops the work and is reported to the
  user.
- The Phase 1 check flights are not part of the `fwdplain_*` dataset.

## Phase 2b — `fwdplain_*` dataset: pre-registration (2026-09-24, before any plain-wall data exists)

**Dataset.** `fwdplain_{tex,trans,blank}_r{1,2,3}`: the three `_fwdplain` worlds × 3
repeats.
- **Settings:** the same as `fwd_*` (300 s, 0.5 m/s, 2.0 m, no compass,
  `sim_noise.parm`, RANSAC seed 42, `run_trial.sh`).
- **Recording:** the same as `fwd_*`, including the forward images and
  `/imu/time_ref`.
- **Order:** interleaved (tex r1, trans r1, blank r1, tex r2, …).
- **Runner:** `run_resumable_batch.sh` in tmux, crash-safe and resumable.
- **Replays:** the current baseline estimators (OI-2 dejitter, FGO window 0.25 s,
  IMU-gap rule).
- **Evaluation:** `eval/three_way_eval.py`, `eval/input_timing.py`,
  `eval/flow_quality.py` and `eval/imu_gap_check.py`, scored by `eval/phase2_score.py`.

**Criteria.** Identical to the Phase 2 table: **PRIMARY** P1, P3, and P4 for EKF3 and
the FGO, with the same bands and the same `dsn` n=3 baseline, judged per trial.
**DIAGNOSTIC:** P2, RTF, topic and forward-image rates, `/imu/time_ref`, every UKF
metric, and evo -a (cruise) on transition and blank.

**Handling, fixed now.**
- **A primary miss:** reported to the user, as in Phase 2. It is not re-scored or
  waived on the spot.
- **Bags are excluded only for an input defect** (Ruling 1's standard). A poor
  estimator result alone never excludes a bag.
- **IMU-gap rule:**
  - pre-arm gap → trim;
  - post-arm gap → the bag is reported as unusable for UKF/FGO, EKF3 is still scored,
    and UKF/FGO in that world are reported at n=2. No re-flight, which avoids
    outcome-dependent selection.
- **A trial that fails to complete** (run_trial error or failed validation) is
  re-flown by the runner once. That is a recording failure, not an outcome.

### Plain-wall Phase 1 — result: ALL PRIMARY PASS (2026-09-24)

`p1plain_{tex,trans,blank}`, flown 10:56–11:18 with `run_resumable_batch.sh`, 3/3
complete.
- **Provenance:** the batch started at `23d9423`. The trial metadata records `3aa80aa`,
  because `run_trial.sh` reads HEAD at the end of a trial and an eval-only commit
  landed mid-batch. Commits are held while flying from now on.
- **Evaluation:** `eval/run_set_eval.sh p1plain …`; results
  `eval/results/{input_timing,flow_quality}_p1plain.json`, `p1plain_{evo,score}.json`.
- **IMU-gap rule:** `p1plain_blank` had two pre-arm gaps (22 and 25 ms at 12.4 and
  13.2 s; arming at 24.7 s). The replay starts at 13.19 s, leaving 15.0 s stationary
  (GT speed 0).

| | `p1plain_tex` | `p1plain_trans` | `p1plain_blank` |
|---|---|---|---|
| P1 flow, lidar, IMU | pass | pass | pass |
| P3 downward flow | pass (inlier 0.9735) | pass (switch 80–82 m bin; levels 0.973 / 0.314) | pass (inlier 0.3137) |
| P4 EKF3 | 4.46 | 0.545 / 100 m | 0.205 / 18 m |
| P4 FGO | 4.69 | 0.710 / 95 m | 1.533 / 37 m |
| *diag.* P2 median / p95 (ms) | 21.1 / 31.5 | 22.1 / 32.5 | 28.5 / 38.2 (limit 38.2) |
| *diag.* RTF; UKF | 0.82; 36.4 | 0.76; 9.18 | 0.78; 13.3 |

**Gate met on the pre-registered criteria.** However, the batch is **HELD** for the
finding below.

### FINDING (render check, 2026-09-24) — the forward camera sees a textured SKY; `fwdplain_*` held pending a ruling

Frames: `plots/fwd_camera/p1plain/`.
- **The plain walls render as intended:** uniform grey faces; only the wall–floor
  junctions, the end wall's outline and the shading between faces are visible.
- **The problem is above them.** **No corridor world has a ceiling**, and every world
  declares `<sky></sky>` (Gazebo's cloud skybox).
  - The forward camera sees textured clouds across **~46% of the frame height** on the
    centre line for most of the flight (rows 0–~225 of 480). That falls to ~29% near
    the end wall.
  - The same holds in `fwd_*` (`plots/fwd_camera/p1_fwd_blank_forward_frames.png`).
- **Why it matters.** Clouds at effectively infinite range are a near-ideal
  **rotation/heading reference**: pure rotation, no parallax. A forward heading cue
  could lock onto the sky rather than the corridor. In `fwdplain_*` that would make
  the "featureless case" not featureless, which would change the thesis claim it
  exists to support.
- **For `fwd_*` as the upper bound,** the sky only adds cue, so the upper-bound framing
  holds. It must be stated that the upper bound includes a far-field sky cue that a
  real indoor corridor does not have.
- **Options, for the user's ruling:**
  - **(a) Recommended:** a plain, non-shadow-casting ceiling at z = 5 m (the wall top)
    in the `_fwdplain` worlds.
    - It matches the design intent ("normal wall/floor/ceiling geometry") and a real
      indoor corridor, and adds only wall–ceiling edges.
    - With `cast_shadows` off, the sun still lights the floor, so downward-flow
      conditions should be unchanged.
    - The plain-wall Phase 1 check is re-flown on the modified worlds, since P3 is the
      test that the floor lighting is unchanged.
  - **(b)** Remove `<sky>` in the `_fwdplain` worlds, giving the uniform 0.8 grey
    background. There is no geometry change, but it is not physically an indoor scene.
    The check is again re-flown.
  - **(c)** Keep the sky in both datasets and document it as a shared far-field cue.
    `fwdplain_*` is then "plain walls under an open, textured sky", not featureless.
  - Under (a) or (b), `fwd_*` and `fwdplain_*` differ in wall texture **and** in the
    sky. Isolating wall texture alone would need the same change and a re-flight of
    `fwd_*`; that is also the user's call.

## RULING (user, 2026-09-24): CEILING in both forward-camera datasets — option (a), applied to both

**Reasoning, as ruled.**
- **The sky is a near-ideal heading and yaw-rate cue.** Clouds at infinity show pure
  rotation with no parallax.
- **It would contaminate both measurements** the forward camera exists for: heading
  from structure, and yaw rate from forward flow. It would do so in both datasets,
  with a cue no real indoor corridor has.
- **The textured-wall upper bound must not include it either.**
- **The ceiling is therefore added to both datasets,** so wall texture is the only
  difference between them.

### Design — ceiling worlds `corridor_{textured,transition,blank}_{fwdc,fwdplainc}.sdf` (recorded before building or flying)

**Construction.**
- Six new worlds. `_fwdc` is built from `_fwd` (line-textured walls); `_fwdplainc` is
  built from `_fwdplain` (plain walls). The source worlds are **not modified**.
- **The one change:** each includes `model://corridor_ceiling`, plus its own world name.
- **`corridor_ceiling`:**
  - a static slab, 20.2 × 170 × 0.1 m;
  - bottom face at z = 5.0 m, the wall-top height, spanning x = −10.1…10.1 (the walls'
    outer faces) and y = −5…165 (the walls' extent). So it closes the corridor
    exactly, including over the end wall (y = 164.9–165.1);
  - plain, untextured, with `corridor_wall`'s material;
  - **non-shadow-casting** (`<cast_shadows>false</cast_shadows>`), so the directional
    sun still lights the floor as before;
  - **visual-only, no collision.** The drone flies at 2 m. Known Issue #11 showed that
    redundant collision geometry is the lockstep hazard. `gpu_lidar` raycasts the
    rendering scene, but points straight down, never up.
- Everything else is identical to the source world: floor, walls, end wall, lighting,
  spawn, physics, and `iris_fwd`.

### Superseded (kept, labelled, not analysed further)

Superseded because the forward view includes the sky:
- the worlds `corridor_*_fwd.sdf` and `corridor_*_fwdplain.sdf`;
- the `fwd_*` dataset;
- the check flights `p1_fwd_*` and `p1plain_*`.

They are kept on disk (`SUPERSEDED.txt` in each trial directory) and **not analysed
further**. Their Phase 1/2 results above remain as the record of what was run.
`fwd_tex_r1`'s Phase 5 high-heading-drift flag is **not carried across.** It applies
to whichever ceiling-dataset bag shows high heading drift.

### Ceiling datasets — pre-registration (2026-09-24, before any ceiling data exists; supersedes the Phase 2b plan for `fwdplain_*`)

**Check flights (Phase 1c).** One per ceiling world, six in all:
`p1c_{fwdc,fwdplainc}_{tex,trans,blank}`.
- Flown in one resumable tmux batch (`run_resumable_batch.sh`), interleaved by dataset
  within each world.
- Same settings as `dsn`/`fwd`: 0.5 m/s, 2.0 m, 300 s, no compass, `sim_noise.parm`,
  RANSAC seed 42.

**Datasets.** `fwdc_*` (textured walls = upper bound) and `fwdplainc_*` (plain walls =
featureless case).
- Each is three worlds × three repeats, same settings.
- Flown in one resumable tmux batch, interleaved as tex r1 fwdc, tex r1 fwdplainc,
  trans r1 fwdc, trans r1 fwdplainc, blank r1 fwdc, blank r1 fwdplainc, then r2, r3.
- **No commits while flights are running.**

**Criteria** (checks and datasets alike; judged per trial; same bands and same `dsn`
n=3 baseline as Phase 2):

| # | criterion | status |
|---|---|---|
| P1 | estimator-input header timing (Phase 2 bands) | PRIMARY |
| P3 | downward-flow conditions (Phase 2 bands) — **the key check that the ceiling did not alter floor lighting** | PRIMARY |
| P4 | EKF3 and FGO outcome (Phase 2 bands; FGO on the dejittered baseline) | PRIMARY |
| R | **render check: no sky visible anywhere in the forward view**, from sample frames (below) | PRIMARY |
| P2 | flow → EKF3 latency (same-world `dsn` mean + 12.5 ms) | DIAGNOSTIC |
| — | RTF, topic and forward-image rates, `/imu/time_ref`, every UKF metric, evo -a (cruise) on transition and blank | DIAGNOSTIC |

**Render check R.** It is applied at two points.
- **Before any flight:** `sim/tools/render_check.sh` on each of the six worlds, at y
  = 0, 80 and 160 (z = 2.3 m).
- **After each check flight:** forward frames extracted at y = 0.5, 10, 40, 80, 120 and
  150 m, and 153 m (the cruise end).
- **Pass:** in every sampled frame, everything above the walls is the plain ceiling,
  with no sky pixels anywhere.

**Gate and handling.**
- **P3 fails anywhere in the check flights:** stop and report. **Lighting is not
  adjusted to make it pass.**
- **Any other primary miss in the check flights:** also stop and report.
- **The datasets are flown only if all six check flights pass every evaluated primary
  criterion.**
- **Dataset handling is the same as fixed for Phase 2b:**
  - a primary miss is reported, not re-scored or waived;
  - bags are excluded only for an input defect;
  - IMU-gap rule: pre-arm gap → trim; post-arm gap → UKF/FGO unusable for that bag,
    reported at n=2, no re-flight;
  - a trial that fails to record is re-flown once by the runner.

### Phase 1c ceiling check flights — result: STOPPED on a P3 miss (2026-09-24)

`p1c_{fwdc,fwdplainc}_{tex,trans,blank}` were flown 11:33–12:20 at `4a7ab90`, 6/6
complete. Results: `eval/results/{input_timing,flow_quality}_p1c.json`,
`p1c_{evo,score}.json`; frames in `plots/fwd_camera/p1c_frames/`.

| | fwdc tex | fwdplainc tex | fwdc trans | fwdplainc trans | fwdc blank | fwdplainc blank |
|---|---|---|---|---|---|---|
| P1 | pass | pass | pass | pass | pass | pass |
| P3 | pass | pass | pass (`flow_y_raw` 71.38) | **FAIL: `flow_y_raw` 73.01 against 71.43 ± 2% (≤ 72.86)** | pass | pass |
| P4 EKF3 | 3.92 | 4.49 | 0.55 / 101 m | 0.555 / 101 m | 0.208 / 20 m | 0.195 / 18 m |
| P4 FGO | 4.60 | 4.53 | **not evaluated** (below) | 0.712 / 95 m | 1.529 / 37 m | 1.496 / 38 m |
| R (no sky) | pass | pass | pass | pass | pass | pass |

**Render check R: PASS.**
- Before flight: 18 frames (six worlds × y = 0, 80, 160).
- In flight: 42 frames (six flights × seven positions).
- Everything above the walls is the uniform ceiling in every frame, with no sky
  anywhere.

**P3 miss, as the pre-registration requires: stop and report; lighting is not
adjusted.** Recorded facts only, not investigated:
- `p1c_fwdplainc_trans` `flow_y_raw` = 73.01 px/s, which is +2.2% against the `dsn`
  n=3 mean of 71.43.
- Every other P3 metric on that flight passes: inlier mean 0.6647, % below 0.5 39.49,
  features 31.64, switch in the 80–82 m bin, levels 0.972 / 0.312, GT |x| 0.0099 m.
- Its P1 and P4 pass. Its ceiling-world sibling `p1c_fwdc_trans` gives 71.38.
- Reference values for the same metric on transition:
  - `dsn` 70.89 / 71.73 / 71.67;
  - superseded `fwd_trans` 71.14 / 70.52 / 71.90, `p1_fwd_trans` 72.29,
    `p1plain_trans` 71.37.
- `flow_y_raw` passes on textured (136.08 twice, against 136.45 ± 2%) and on blank, in
  both ceiling datasets.

**Also pending:** `p1c_fwdc_trans` UKF/FGO replay was refused by the dejitter guard
(residual 289 ms).
- **Cause:** 92 IMU samples arrived with **one receipt stamp** at t = 12.48 s, after a
  292 ms delivery pause. `/clock` also paused for 170 ms at t = 12.28 s.
- This was at IMU stream start, pre-arm (arming 24.93 s), with **no sensor-time gap**
  (sensor steps are all normal, so no samples were lost).
- Flow and lidar never gap above 33 ms. P1 (cruise) passes.
- The IMU-gap rule defines a gap on sensor time, so it does not cover a receipt
  bunching. The rule is **not extended without a ruling**. FGO P4 for this flight is
  NOT EVALUATED, and EKF3 is scored.

**The ceiling datasets (`fwdc_*`, `fwdplainc_*`) are NOT flown** pending the user's
ruling.

### RULINGS (user, 2026-09-24) on the Phase 1c result — recorded before applying or flying

**Ruling 1 — `p1c_fwdplainc_trans` P3 forward-flow miss (73.01 against ≤ 72.86).**
- **The miss stays recorded.** The ceiling-dataset batch proceeds.
- **Decision rule, fixed before flying:**
  - **If 2 or more of the 3 `fwdplainc_trans_r*` dataset trials fail** the P3
    `flow_y_raw` criterion: stop and report, for investigation of the world.
  - **Otherwise** the check-flight miss is recorded as **run-to-run variability**,
    noting that:
    - every other P3 metric on that flight passed;
    - its textured-wall twin `p1c_fwdc_trans` gave 71.38;
    - the walls are outside the downward camera's view (Phase 1).
- **The ±2% band is not changed.** Note: the transition world's historical spread of
  this metric (70.52–72.29 across `dsn`, `fwd_trans`, `p1_fwd_trans` and
  `p1plain_trans`) sits close to the band (70.00–72.86 around the `dsn` mean of 71.43).
  The transition mean mixes a textured level (~136 px/s) and a blank level (~−3 px/s),
  so it has less headroom than the textured or blank values.

**Ruling 2 — IMU timing rule EXTENDED** (supersedes "RULE — IMU gaps and the replay
estimators").
- **Irregularity:** any IMU timing irregularity the timing correction cannot process.
  Either:
  - a **gap**: a step of more than 10 ms in `/imu/time_ref` sensor time, or
  - a **receipt bunch**: samples whose receipt stamp is displaced by more than 25 ms
    from the linear map of receipt against sensor time. 25 ms is the dejitter guard's
    own limit, i.e. exactly what the correction cannot process.
- **Before arming:** the replay starts at the first clean sample after the last
  irregularity, **provided at least 10 s of stationary data remains before arming**.
- **Less than 10 s remains, or the irregularity is after arming:** the bag is
  **unusable for UKF/FGO**, and reported as such. EKF3 is still scored.
- **Applied to** `p1c_fwdc_trans` and to **every dataset bag**, via
  `eval/imu_gap_check.py` → `<trial>/imu_gaps.json`.

**Extended timing rule applied to `p1c_fwdc_trans`.**
- An 89-sample receipt bunch at t = 12.48 s (max displacement 288 ms), pre-arm.
- The replay starts at 12.775 s, leaving 12.2 s before arming (≥ 10 s). The dejitter
  residual max is then 11.75 ms.
- **It now passes every primary criterion:** FGO ratio 0.700 [0.67, 0.78], onset
  94.9 m [90, 101]; EKF3 0.55 / 100.6 m. UKF (diagnostic): 17.76, ratio 0.794, onset
  82.7 m.
- **Phase 1c status:**
  - five of six pass every primary criterion;
  - the one miss (`p1c_fwdplainc_trans` P3 `flow_y_raw`) is recorded, with Ruling 1's
    decision rule to be applied on the dataset;
  - render check R passes on all six.
- **The extended rule leaves every earlier verdict unchanged** (re-checked on
  `fwd_trans_r1`, `fwd_trans_r3`, `fwd_tex_r2` and `p1plain_blank`).
- **Note:** even clean bags carry only 11.5–13.8 s of IMU data before arming, because
  the IMU stream starts after `SET_MESSAGE_INTERVAL` lands. So the 10 s floor leaves
  room only for irregularities in the first ~1.5–3.8 s of the stream.

## Ceiling datasets `fwdc_*` / `fwdplainc_*` — result (2026-09-24): one primary miss, reported

**Flown.** 18/18 trials completed first time, with no aborts, at `2f3dbf1`.
- Tmux batch `ceiling_datasets`, 12:38:40–14:59:33 (140.9 min), interleaved as
  pre-registered.
- No commits during flights.
- Evaluation: `eval/run_set_eval.sh`; results
  `eval/results/{input_timing,flow_quality}_{fwdc,fwdplainc}.json`,
  `{fwdc,fwdplainc}_{evo,score}.json`.
- Frames: `plots/fwd_camera/ceiling_dataset_frames/`.

**Extended IMU timing rule, applied to all 18.** 15 bags are `ok` and 3 are `trim`. None
is unusable, so UKF/FGO are evaluated on all 18.

| trial | pre-arm irregularity | left before arming |
|---|---|---|
| `fwdc_tex_r1` | receipt bunches of 60 and 1 samples | 12.2 s |
| `fwdc_tex_r2` | a 2-sample bunch | 10.7 s |
| `fwdplainc_trans_r2` | a 30 ms gap | 12.4 s |

**Render check R: PASS on all 18.** In 7 sampled positions per bag, only the uniform
ceiling is above the walls; there is no sky.

**Primary results.**
- **`fwdplainc_*`: 9/9 pass every primary criterion.**
- **`fwdc_*`: 8/9 pass.** **`fwdc_trans_r1` FAILS P3 `flow_y_raw`: 73.57 against
  71.43 ± 2% (≤ 72.86).** Everything else on it passes: inlier mean 0.6654, switch in
  the 80–82 m bin, levels 0.975 / 0.312, EKF3 0.564 / 101 m, FGO 0.713 / 95 m.

| | tex r1 / r2 / r3 (EKF3; FGO evo -a (cruise)) | trans r1 / r2 / r3 `flow_y_raw` | blank |
|---|---|---|---|
| `fwdc` | 3.44 / 3.98 / 3.99; 4.68 / 4.42 / 4.97 | **73.57** / 71.58 / 72.00 | all pass |
| `fwdplainc` | 3.88 / 4.26 / 4.15; 4.67 / 4.82 / 4.64 | 71.66 / 71.38 / 70.40 | all pass |

- **Transition P4:** EKF3 ratio 0.547–0.564, onset 100–101 m; FGO ratio 0.691–0.725,
  onset 94.5–95.2 m. All pass, in both datasets.
- **Blank P4:** EKF3 ratio 0.181–0.223, onset 17–20 m; FGO ratio 1.506–1.529, onset
  34–38 m. All pass.
- **Diagnostics:**
  - P2 is within its limits on all 18 (p95 at most 36.4 ms).
  - RTF 0.72–0.77.
  - UKF (textured): `fwdc` 14.6 / 20.9 / 7.3, `fwdplainc` 15.8 / 10.0 / 8.7.
    `fwdplainc_trans_r2` UKF 31.55.

**Ruling 1's decision rule, applied as recorded.** 0 of 3 `fwdplainc_trans_r*` fail the
forward-flow criterion. So **the `p1c_fwdplainc_trans` check-flight miss is recorded as
run-to-run variability**:
- every other P3 metric on it passed;
- its textured-wall twin gave 71.38;
- the walls are outside the downward camera's view.

**New primary miss, reported for a ruling** (the decision rule covered only
`fwdplainc_trans`). Facts only, not investigated. Transition `flow_y_raw`, all flights
so far:

| group | values | above 72.86 |
|---|---|---|
| no ceiling: `dsn` | 70.89 / 71.73 / 71.67 | 0 |
| no ceiling: `fwd_trans` | 71.14 / 70.52 / 71.90 | 0 |
| no ceiling: `p1_fwd_trans` | 72.29 | 0 |
| no ceiling: `p1plain_trans` | 71.37 | 0 |
| ceiling: `p1c_fwdc_trans` / `p1c_fwdplainc_trans` | 71.38 / **73.01** | 1 |
| ceiling: `fwdc_trans` | **73.57** / 71.58 / 72.00 | 1 |
| ceiling: `fwdplainc_trans` | 71.66 / 71.38 / 70.40 | 0 |

- **2 of 8 ceiling-world transition flights exceed the band; 0 of 8 without a
  ceiling.**
- Every transition flight has the switch in the same 81 m bin and the same levels
  (0.970–0.975 / 0.312–0.316).
- Textured and blank `flow_y_raw` pass in all 18.

### RULING (user, 2026-09-24): `fwdc_trans_r1` P3 miss recorded as run-to-run variability — characterised effect size

**The miss (73.57 against ≤ 72.86) stays recorded.** It is treated as run-to-run
variability, as for `p1c_fwdplainc_trans`. One bounded quantification was run (data on
disk only; no mechanism investigation, no flights, no lighting changes):
`eval/ceiling_flow_effect.py` → `eval/results/ceiling_flow_effect.json`.

**Method.** Transition-world `flow_y_raw` over cruise, with the same frame selection as
`flow_quality.py`. It is split into the textured half (GT y < 75 m) and the blank half
(GT y > 85 m), flow_quality's own level windows. Groups:
- 8 ceiling flights: `p1c_*_trans`, `fwdc_trans_r*`, `fwdplainc_trans_r*`;
- 8 no-ceiling flights: `dsn_trans_r*`, `fwd_trans_r*`, `p1_fwd_trans`,
  `p1plain_trans`.

Test: Welch's two-sample t, two-sided.

| window | ceiling mean (sd) | no-ceiling mean (sd) | difference | Welch t (df) | p |
|---|---|---|---|---|---|
| whole cruise | 71.87 (1.00) | 71.44 (0.58) | **+0.43 px/s (+0.6%)** | 1.06 (11.2) | 0.31 |
| textured half | 136.08 (0.55) | 135.98 (0.41) | +0.10 px/s (+0.07%) | 0.39 (13.0) | 0.70 |
| blank half | −2.08 (2.43) | −2.39 (0.85) | +0.31 px/s | 0.34 (8.7) | 0.74 |

**Characterised effect: a +0.43 px/s (+0.6%) difference in transition forward flow,
not distinguishable from zero at n = 8 + 8 (p = 0.31).**
- The textured half is unchanged to within 0.1 px/s.
- The blank half has the larger spread under the ceiling: sd 2.43 against 0.85, a
  variance ratio of 8.1 (Levene p = 0.17, not significant).
- **Both over-band flights have the highest blank-half means:** `p1c_fwdplainc_trans`
  +0.87 and `fwdc_trans_r1` +1.30, against −6.40 to −1.34 for the other 14.
- Recorded as a fact, not interpreted.

**STANDING RULE: no comparison between the ceiling datasets (`fwdc_*`, `fwdplainc_*`)
and `dsn_*` on the transition world without stating this effect size.** It does not
affect Phase 5, which compares with and without the forward measurements on the same
bags.

## Ceiling datasets — COMPLETE (2026-09-24)

- **`fwdc_*` (textured walls = upper bound): 8/9 pass every primary criterion.** The one
  recorded miss is `fwdc_trans_r1` P3 `flow_y_raw` (run-to-run variability, above).
- **`fwdplainc_*` (plain walls = featureless case): 9/9 pass.**
- The render check passes on all 18. The extended IMU timing rule trimmed 3 bags; none
  is unusable.
- **These two datasets are the forward-camera datasets for Phases 3–5.**

## Phase 3 — forward-camera measurements: pre-registration (2026-09-24, before calibration or validation runs)

**Scope.** Two measurements from `/forward_camera/image`, validated before any fusion:
- **Heading** ψ: yaw relative to the corridor axis, with a per-frame confidence.
- **Yaw rate** ω: from horizontal forward-image flow.

Guardrails as ruled:
- the simplest standard methods first;
- no features added to the worlds;
- **no ground truth inside the measurement pipeline** (`src/forward_camera/fwd_measure.py`
  and `eval/fwd_run.py` read only the forward image);
- a time-box of one working session.

### Method (frozen now)

**Heading.**
- LSD line segments (OpenCV defaults). Segments are discarded if shorter than 15 px, or
  within 5° of horizontal or vertical.
- RANSAC vanishing point: 300 iterations, length-weighted pair sampling, seeded per
  frame. It is refined by length-weighted least squares on the inliers.
- ψ = atan((u_vp − cx)/fx). Positive means the nose is to the left, matching ENU yaw.
  Roll and pitch are not compensated (cruise pitch ~0.02°), stated as a limitation.
- **Three priors, all added after they failed on CALIBRATION frames (`p1c_*`, stated
  openly):**
  - **(i) the VP must lie inside the image**, i.e. |ψ| < 30°, the half-FOV. This
    rejects the checkerboard floor's diagonal families near ±45°.
  - **(ii) the VP must lie within ±5° of the horizon row** (level mount, cruise pitch
    ~0.02°). This rejects aliasing families about 11° below it.
  - **(iii) RANSAC scores by balanced two-sided support,** 2 × min(left, right inlier
    length). A corridor VP is supported by both walls; the checker families are
    one-sided.
- **Known failure before calibration:** plain walls over a checkerboard floor. The
  three or four junction segments are detected and point at the true VP to within
  0.2–0.25°, but on 3–5 of 10 sampled calibration frames the floor's aliasing segments
  still win, by +2.4 to +4.4°. **No further method changes are made. This is reported,
  not engineered away.**

**Validity (confidence).**
- A heading is valid iff support ≥ S_MIN; otherwise the output is **"no measurement"**.
- Support = the balanced inlier length in px, and doubles as the per-frame confidence.
- This is also the **end-wall dropout**: near y ≈ 150 m the junctions shorten and
  vanish, support collapses, and the output is "no measurement".

**Yaw rate.**
- Shi-Tomasi corners (up to 100) inside a box of half-size B px around the **previous
  frame's VP**. They are tracked by pyramidal LK into the current frame.
- ω = median(Δu)/fx/Δt, in deg/s, positive anticlockwise. It is valid iff the previous
  frame had a VP, and at least N_MIN corners were tracked.
- **Parallax limitation:** forward flight adds radial flow from the focus of expansion
  (≈ the VP), with horizontal component (u − u_foe)·V/Z. The box keeps |u − u_foe|
  small and Z large, and the median over a roughly symmetric box cancels it to first
  order. It is **not removed**: residual parallax is a bias that depends on the feature
  layout.

### Calibration / validation split

- **Calibration: the six `p1c_*` check flights only.** The calibrated values are:
  - the inlier tolerance, from {0.5, 1.0, 1.5}°;
  - S_MIN, from {0, 200, 400, 600, 800, 1000} px;
  - the box half-size B, from {40, 80, 160} px;
  - N_MIN, from {5, 10, 20};
  - the measurement noise σ_ψ and σ_ω (1.4826 × MAD of valid-output errors, pooled per
    dataset type) for Phase 4.
- **Selection rule, fixed now.** Among the grid:
  - pick the combination for which the most calibration bags meet the accuracy bar
    below;
  - break ties by mean availability.
  - Heading (tolerance, S_MIN) is chosen first; then yaw rate (B, N_MIN), using that
    tolerance's VPs.
  - One parameter set is used for both datasets.
- **Validation: the 18 dataset bags (`fwdc_*`, `fwdplainc_*`),** with the frozen
  parameters. **No re-tuning after validation starts.**

### Ground truth (evaluation only)

- ψ_true = GT ENU yaw − 90° (the corridor runs along +Y).
- ω_true = the finite difference of GT yaw between the same two frame stamps.
- Both are interpolated from `/ground_truth/pose` at the frame stamps.
- Cruise window: `eval/cruise_window.py` from GT.
- **Limitation:** in these flights the true heading is nearly constant (GT yaw span
  ≈ 0.1° over cruise) and the true yaw rate is ≈ 0. **The validation therefore tests
  bias, noise, outliers and availability at near-zero heading and yaw rate, not the
  response to heading changes.**
- A supplementary **static yaw sweep** tests the heading response. It uses rendered
  frames, not flights: each of the six worlds at y = 20, 100 and 140 m, z = 2.3 m, yaw
  offsets of {−10, −5, −2, 0, +2, +5, +10}°. **Its bar:** fitted slope 1 ± 0.05, and
  every |residual| ≤ 0.5°, where a valid output exists. It is run after the main
  validation, if the time-box allows.

### Accuracy bar (per bag, over cruise; pre-registered)

| measurement | availability (% of cruise frames valid) | \|bias\| (mean error) | noise (sd of non-outlier errors) | outlier rate |
|---|---|---|---|---|
| heading ψ | ≥ 70% | ≤ 0.5° | ≤ 1.0° | ≤ 5% (\|error\| > 3°) |
| yaw rate ω | ≥ 70% | ≤ 0.05 deg/s | ≤ 1.0 deg/s | ≤ 5% (\|error\| > 3 deg/s) |

**Basis for the bar.**
- **Heading:** the replay estimators' unobservable yaw drifts by ~45° over a 300 s
  cruise (FGO; the UKF more). A measurement with sub-degree bias and noise, available
  for most frames, bounds that drift by more than an order of magnitude.
- **Yaw rate:** the true SITL gyro bias averages 8.9 deg/min = 0.148 deg/s over cruise.
  A yaw-rate measurement must be unbiased to about a third of that (0.05 deg/s) to help
  observe it. 1 deg/s per-frame noise averages to ~0.18 deg/s over 1 s at 30 Hz.
- 70% availability allows for the end-wall dropout (~3% of cruise) and occasional
  frame losses.

**Reported per bag, and aggregated per world and per dataset:** bias, noise, robust σ,
outlier rate, availability (overall, and for y > 145 m separately), and the degradation
from textured walls (`fwdc`) to plain walls (`fwdplainc`).

**Time-box.** If the simple method has not produced a validated measurement within one
working session, the work stops and what is known is reported; the method is not
escalated.

### Phase 3 calibration — result (p1c_* only; parameters FROZEN before validation)

`eval/fwd_eval.py --calibrate` → `eval/results/fwd_calibration.json`, applying the
pre-registered selection rule.

**Frozen:** inlier tolerance **0.5°**, S_MIN **200 px**, yaw-rate box half-size **80 px**,
N_MIN **5**. Measurement noise for Phase 4 (robust σ over valid calibration errors):

| | σ_ψ | σ_ω |
|---|---|---|
| `fwdc` | 0.097° | 0.106 deg/s |
| `fwdplainc` | 0.026° | 2.07 deg/s |

**Calibration bags against the bar:**

| bag | heading (avail / bias / sd / outliers) | yaw rate (avail / bias / sd / outliers) |
|---|---|---|
| `p1c_fwdc_tex` | 96.8% / −0.005° / 0.21° / 0.1% **pass** | 99.9% / +0.006 / 0.20 / 0.0% **pass** |
| `p1c_fwdc_trans` | 96.7% / −0.012 / 0.13 / 0.0% **pass** | 97.4% / +0.008 / 0.21 / 0.0% **pass** |
| `p1c_fwdc_blank` | 96.7% / −0.016 / 0.10 / 0.0% **pass** | 97.4% / +0.003 / 0.14 / 0.0% **pass** |
| `p1c_fwdplainc_tex` | 60.2% / +0.22 / 0.71 / 11.3% fail | 89.8% / +0.038 / 1.48 / 15.1% fail |
| `p1c_fwdplainc_trans` | 87.3% / +0.03 / 0.39 / 2.9% **pass** | 85.9% / +0.092 / 1.43 / 15.6% fail |
| `p1c_fwdplainc_blank` | 95.4% / −0.03 / 0.12 / 0.1% **pass** | 87.3% / −0.061 / 1.35 / 23.7% fail |

- **Heading: 5/6.** The fail is plain walls over a checkerboard floor, as flagged
  before calibration.
- **Yaw rate: 3/6.** It passes with textured walls and fails with plain walls, where
  there are too few trackable corners near the VP (noise ~1.4 deg/s, 15–24%
  outliers).
- **End-wall dropout works as designed:** heading availability for GT y > 145 m is
  0–19%.
- **The validation runner** uses `fwd_run.py --frozen`, verified identical to the grid
  run on 600 frames (t, ψ, support, ω, n_trk all equal).

### Phase 3 validation — result (18 dataset bags, frozen parameters, no re-tuning)

`eval/fwd_eval.py --validate` → `eval/results/fwd_validation.json`. Static sweep:
`eval/fwd_sweep_eval.py` → `eval/results/fwd_yaw_sweep.json`, with renders in
`~/thesis_data/phase3_yaw_sweep/`. Bias and noise are computed on the non-outlier valid
errors; the all-valid mean is also in the JSON. Values are means over the three
repeats; every bag's own values are in the JSON.

**Heading ψ (vanishing point).**

| dataset / world | availability | bias | noise sd | robust σ | outliers | bar |
|---|---|---|---|---|---|---|
| `fwdc` tex | 96.8% | −0.006° | 0.20° | 0.13° | 0.09% | **3/3** |
| `fwdc` trans | 96.8% | −0.014° | 0.13° | 0.09° | 0.00% | **3/3** |
| `fwdc` blank | 96.8% | −0.018° | 0.11° | 0.08° | 0.00% | **3/3** |
| `fwdplainc` tex | 60.0% | +0.206° | 0.68° | 0.33° | 11.9% | **0/3** |
| `fwdplainc` trans | 87.6% | +0.035° | 0.39° | 0.02° | 3.0% | **3/3** |
| `fwdplainc` blank | 95.5% | −0.027° | 0.12° | 0.01° | 0.14% | **3/3** |

**Yaw rate ω (horizontal flow near the VP).**

| dataset / world | availability | bias | noise sd | outliers | bar |
|---|---|---|---|---|---|
| `fwdc` tex / trans / blank | 99.9 / 97.4 / 97.4% | +0.006 / +0.009 / +0.002 deg/s | 0.19 / 0.21 / 0.13 deg/s | 0.0% | **9/9** |
| `fwdplainc` tex / trans / blank | 89.7 / 86.1 / 87.5% | +0.053 / +0.080 / −0.066 deg/s | 1.48 / 1.43 / 1.36 deg/s | 15.4 / 15.7 / 23.7% | **0/9** |

**The validation reproduces the calibration** to within a few hundredths in every
metric: the split held, and nothing was re-tuned.

**End-wall dropout.** Heading availability for GT y > 145 m:
- `fwdc`: 14–20%;
- `fwdplainc`: 0–10%.

The output goes to "no measurement", as designed.

**Degradation from textured to plain walls.**
- **Heading:**
  - It holds on blank and transition floors: noise 0.12° and 0.39°, against 0.11°
    and 0.13° with textured walls.
  - On the blank floor, plain walls give the lowest robust σ of all (0.01°). The four
    junction lines are clean.
  - It **fails on the checkerboard floor**: availability 97% → 60%, outliers 0.1% →
    12%. With plain walls, the only corridor-parallel structure is 3–4 junction
    segments, and floor aliasing outvotes them. **This is floor texture defeating the
    method, not wall texture helping it.**
- **Yaw rate:** it **fails everywhere with plain walls**. Noise 0.13–0.21 → 1.36–1.48
  deg/s, outliers 0% → 15–24%. Plain walls give no trackable corners near the VP, and
  line junctions have the aperture problem.

**Static heading response (supplementary, pre-registered bar: slope 1 ± 0.05, every
|residual| ≤ 0.5°): 1/6 worlds pass** (`blank_fwdc`). **The bar stands as failed.**
- **Near the end wall** (y = 140 m, 25 m from it) with ±5–10° offsets, several wrong
  VPs clear S_MIN: for example, a true +10° is reported as −17.2° (`textured_fwdc`).
- **Plain walls over a checkerboard floor** show errors of up to 2.3–3.2°.
- **Descriptive only, not the bar:** at y = 20 and 100 m, every textured-wall world and
  `blank_fwdplainc` respond with slope 1.00–1.01 and max |residual| ≤ 0.32°. The
  plain-wall checkerboard worlds show slope 1.03–1.05 and residuals up to 2.5°.

**Phase 3 conclusion (validated measurements, and where they fail).**
- **Heading is validated** (flight bar) on 15/18 bags:
  - every textured-wall bag;
  - plain walls on blank and transition floors.
- **Heading fails** on plain walls over a checkerboard floor.
- **Its response to heading changes is confirmed only away from the end wall.** Within
  ~25 m of it, large offsets produce confident wrong outputs. The flight data (true
  heading ≈ 0) does not exercise this. **Phase 4 must treat heading near the end wall
  with suspicion, or gate it out.**
- **Yaw rate is validated only with textured walls.** With plain walls, horizontal flow
  near the VP is not a usable measurement.
- **Measurement noise for Phase 4** comes from the calibration set:
  - `fwdc`: σ_ψ 0.097°, σ_ω 0.106 deg/s;
  - `fwdplainc`: σ_ψ 0.026°. There is no σ_ω, because it failed validation.
- **The method was not escalated** (time-box and guardrail). Three priors were added on
  calibration frames and are stated above.

## SCOPE CHANGE — supervisor direction (2026-09-29; details pending the supervisor's reply)

Direction received from the supervisor:
- **Real indoor flights with motion-capture ground truth are in scope.**
- **The UKF and FGO should ideally run ONLINE, onboard the ArduPilot flight
  controller.** Each would be a **drop-in replacement for EKF3**, the estimator the
  vehicle flies on.
- **The forward camera is included in the real flights only if it is first implemented
  and verified in simulation.**

**Consequences, as recorded by the user:**
- **The Python UKF and FGO become the reference implementations.** Onboard versions
  will be validated against them on the same data.
- **Offline Phases 4 and 5 are the simulation verification** the supervisor requires
  before the forward camera goes on the real vehicle.
- **All current flights are flown on simulator truth** (`AHRS_EKF_TYPE=10`, Hidden
  Configuration Audit §1).
  - No estimator, EKF3 included, influences the trajectory. All three are **offline
    observers**.
  - **Closed-loop flight**, with each estimator flying the vehicle, is now planned
    under the onboard direction.
- **For all future flights, simulated closed-loop and real:** ArduPilot logs with
  **`LOG_REPLAY=1` and `LOG_DISARMED=1` from the first flight**, so any flight can be
  replayed.

## RULING — EKF3 in the offline forward-camera comparison (user, 2026-09-29)

**Adopted: option 3.**
- **EKF3 is the fixed no-yaw-source baseline** (`EK3_SRC1_YAW=0`).
- **Only the UKF and FGO get forward-camera arms.**

**Option 2 (live injection) is rejected for the offline comparison:**
- it reintroduces the separate-run latency confound;
- the `VISO_YAW_M_NSE` floor (≥ 0.05 rad) would force EKF3 to under-trust the heading
  relative to the UKF and FGO.

**Option 1 (re-record with `LOG_REPLAY=1` plus `REPH` injection) is a deferred
extension.**
- It is reconsidered after Phase 5, and only if the heading arm shows a clear effect
  on the UKF and FGO.
- **Open items:**
  - a tool that writes `REPH` records;
  - a replay-fidelity check against live EKF3;
  - whether injected `REPH` records bypass the yaw noise clamp. The clamp is applied
    in `AP_VisualOdom_MAV`, upstream of `AP_DAL::writeExtNavData`, and that is
    unverified.
- **This ruling will be revisited under the onboard plan.** There, EKF3 heading via
  ExternalNav may become the natural route.

**Evidence** (ArduPilot source at the pinned commit `7bac20cbcc`; our logs):
- **One downward optical-flow sensor only.**
  - `AP_OpticalFlow` holds a single backend (`OpticalFlow_backend *backend;`,
    `AP_OpticalFlow.h:134`).
  - Its parameters have no instance index (`FLOW_TYPE`), and the only orientation
    parameter is `FLOW_ORIENT_YAW` (`AP_OpticalFlow.cpp:51-53`).
  - EKF3's flow model predicts range as height above ground over the vertical-axis
    cosine, i.e. a flat floor below (`AP_NavEKF3_OptFlowFusion.cpp:116,174`). It gates
    on tilt (`prevTnb.c.z > DCM33FlowMin`, line 44).
  - **A forward camera is not a second flow sensor for EKF3.**
- **ExternalNav yaw exists live, with two constraints.**
  - `EK3_SRC1_YAW` accepts `6:ExternalNav` (`AP_NavEKF_Source.cpp:58`).
  - The path: `VISION_POSITION_ESTIMATE` / `ODOMETRY` / `ATT_POS_MOCAP`
    (`GCS_Common.cpp:4562-4581`) → `AP_VisualOdom`, which needs `VISO_TYPE=1`
    (`AP_VisualOdom.cpp:34,154`) → `writeExtNavData`, with yaw extracted at
    `AP_NavEKF3_Measurements.cpp:1112-1117` → `fuseEulerYaw(EXTNAV)`
    (`AP_NavEKF3_MagFusion.cpp:366-374`).
  - Position is fused only if `EK3_SRC1_POSXY=ExternalNav`
    (`AP_NavEKF3_Control.cpp:617`).
  - **Constraint: each message needs a position.** A NaN position or position error
    drops the whole sample, yaw included (`AP_NavEKF3_Measurements.cpp:1076`).
  - **Constraint: a noise floor.** `angErr` is clamped to at least `VISO_YAW_M_NSE`
    (`AP_VisualOdom_MAV.cpp:43`): default 0.2 rad, documented range 0.05–1.0 rad
    (`AP_VisualOdom.cpp:101-107`). The static-sweep heading residuals are well below
    that.
  - **There is no EKF3 input for an external yaw-rate measurement.**
    `bodyOdmDataNew.angRate` is written (`AP_NavEKF3_Measurements.cpp:133`) and read
    nowhere else in EKF3.
- **Our logs lack replay records.**
  - Replay supports ExternalNav via the DAL `REPH` record (`AP_DAL.cpp:359-371`;
    `Tools/Replay/LogReader.cpp:119`, `LR_MsgHandler.cpp:286`).
  - But it needs `LOG_REPLAY=1` and `LOG_DISARMED=1` or `2` at recording
    (`AP_Logger.cpp:114-124`).
  - `fwdc_tex_r1`'s log has `LOG_REPLAY=0` and `LOG_DISARMED=0`, and no DAL records
    (no `RFRH`/`RFRN`/`RISH`/`REPH`).

**Consequence for Phase 5.**
- **The prediction is tested within the UKF and within the FGO:** each with and
  without heading, on the same bags.
- **EKF3 appears only as the no-heading reference.** No claim is made about EKF3 with
  heading.
- Which measurement is which:
  - the **vanishing-point heading** is an external heading measurement, not optical
    flow;
  - the **forward yaw rate** is used only by our own estimators.

## Phase 4 — offline forward-camera fusion, UKF and FGO only: pre-registration (2026-09-29, before any fusion code or run)

**Scope.**
- Fuse the Phase 3 forward-camera measurements into the Python UKF and FGO.
- **EKF3 is the fixed no-yaw-source baseline** (ruling above).
- Offline, on all 18 ceiling-dataset bags.
- **Phase 4 builds and runs the arms. The hypothesis test and its interpretation are
  Phase 5.**

**Arms (per estimator, per bag):**

| dataset | arms |
|---|---|
| `fwdc_*` (textured walls) | baseline / +heading / +heading+yaw rate |
| `fwdplainc_*` (plain walls) | baseline / +heading (yaw rate failed Phase 3 validation) |

That is 18 bags × 2 estimators, giving 90 replay runs, all from scratch. The
**baseline arm must reproduce the existing ceiling-dataset UKF/FGO trajectories byte
for byte** (a regression check on the refactor). If it does not, stop and report.

**Measurements.**
- The frozen Phase 3 outputs (`<trial>/fwd_meas/meas_frozen.npz`), stamped at the
  forward-image header (sim time).
- **Validity is measurement-intrinsic only**, from Phase 3: heading valid iff
  support ≥ S_MIN = 200 px; yaw rate valid iff ≥ N_MIN = 5 tracked corners.
- **No ground truth, estimated position or world knowledge enters any gating.** This
  includes the end wall: there is no position-based gate. The end-wall weakness found
  in Phase 3 is left to the intrinsic confidence and the χ² gate, and reported.

**Measurement models (shared code, `src/estimators/measurement_models.py`).**
- **Heading:** h_ψ(x) = yaw, with the innovation wrapped.
  - The navigation frame's yaw reference is the corridor axis. Both estimators already
    initialise yaw = 0 at spawn, facing along the corridor, so this is the same frame.
  - This is the ExternalNav convention: the external heading source defines the yaw
    reference.
- **Yaw rate:** h_ω(x) = ω̄_z − b_g,z.
  - ω̄_z is the co-sampled gyro-z averaged over the forward-frame interval
    (t_{k−1}, t_k], using a second instance of the shared `FlowFrameGyroAverager`.
  - b_g,z is the gyro-z bias state in rate units (UKF: delta-form bias / dt).
  - Roll and pitch coupling is neglected (cruise tilt ≈ 0.02°).

**Noise (from the static-sweep residuals, not the smaller flight values).**
- **σ_ψ** = robust σ (1.4826 × MAD) of (ψ − commanded offset) over every valid sweep
  frame, pooled per dataset (`eval/results/fwd_yaw_sweep.json`):
  - **`fwdc` 0.148°**, **`fwdplainc` 0.126°**;
  - against flight calibration values of 0.097° and 0.026°.
- **σ_ω: the sweep contains no yaw-rate measurement**, so σ_ω cannot come from it
  directly.
  - **Rule:** the flight-calibration σ_ω scaled by the same sweep/flight inflation as
    σ_ψ for that dataset.
  - **`fwdc`: 0.106 × (0.148/0.097) = 0.162 deg/s.** Yaw rate is not used on `fwdplainc`.
  - A derived choice, flagged for the user.

**Gate (identical in both estimators).**
- χ² test on the scalar innovation: **ν²/S ≤ 9** (3σ; EKF3's flow gate 300 → (0.01 ×
  300)² = 9). Rejected measurements are not fused.
- S = H P⁻ Hᵀ + σ², with P⁻ each estimator's own predicted covariance:
  - **UKF:** its sigma-point prediction (the existing `_update_scalar` path).
  - **FGO:** the Python `BatchFixedLagSmoother` exposes no marginal covariance. So a
    **filtering covariance recursion** runs alongside it: per keyframe, the previous
    posterior marginal of (X, V, B) acts as a prior; the keyframe's factors are
    linearised at the current estimates; and the 30-dimensional information matrix is
    inverted.
    - This gives P⁻ (IMU factor only) for the gate, and the posterior for the next
      step.
    - It is used **for gating only**; the smoother's solution is untouched.

**Timing (DIAGNOSTIC only).**
- Per-update wall-clock is logged in every arm:
  - UKF: each predict step (80 Hz, period 12.5 ms) and each forward update;
  - FGO: each keyframe step (30 Hz, period 33.3 ms), including the gate recursion in
    forward arms.
- Reported as median, p95, max and ratio to the sensor period.
- **Python timing on the workstation says nothing directly about flight-controller
  feasibility. It must not change any Phase 4 setting or stop the phase.**

**Runner.** A crash-safe, resumable job runner in tmux
(`eval/run_jobs_resumable.sh`). Each job writes a DONE marker; a re-run skips done jobs
and redoes incomplete ones.

**Outputs, per arm and bag** (reported, not judged; judging is Phase 5):
- evo -a (cruise);
- transition and blank failure metrics;
- yaw error against GT over cruise;
- gyro-z bias against the SITL truth ramp;
- forward-measurement acceptance (valid, gated, fused);
- NIS statistics;
- timing.

### Supervisor answers (2026-09-29, received after the scope-change brief)

- **One firmware build with parameter selection is preferred**, if feasible.
- **Real hardware flights are expected for full marks.**
  - SITL-only is an acceptable fallback **only if** the drone flights are delayed by
    circumstances outside our control.
  - **Real flights are planned as the main result.**
- **The offline comparison stays and is written up.** It carries less weight once
  real-world results exist.
- **Target hardware: likely an STM32H743 flight controller** (2 MB flash, ~1 MB RAM) on
  a **VTOL: ArduPlane quadplane, flown in multirotor mode indoors.**
- **The UKF runs onboard as a drop-in replacement for EKF3.**
- **The FGO may run online with GTSAM on a companion computer** (e.g. a Raspberry Pi),
  provided it is shown working and beating EKF3.
  - **If EKF3 is what flies, the FGO must show a clear benefit over standard EKF3 in a
    clear case.**

**Part C (onboard feasibility) was adjusted accordingly:**
- the FGO's off-board routes to driving flight: EKF3 via ExternalNav, or
  `AP_ExternalAHRS`;
- the H743 flash budget for Plane quadplane and Copter;
- companion-computer compute for FGO plus forward camera together;
- a new item 9: candidate scenarios where the FGO could show a clear, fair benefit over
  EKF3, from existing results only.
- **The item 9 instruction arrived truncated** ("…consistency of the"). It was
  interpreted as estimate consistency (NEES and uncertainty reporting), to be
  confirmed by the user.

## Part C — onboard feasibility investigation (2026-09-29): result

Full report, read-only (nothing built or modified), with citations at `7bac20cbcc`:
**`docs/partC_onboard_feasibility.md`**. Spot-checked here:
- `SIM_JSON.cpp:410-413`
- `iris_with_ardupilot/model.sdf:789`
- `AP_NavEKF3_Measurements.cpp:1118`

**Key conclusions.**
- **The UKF onboard is feasible on the H743, for Copter and QuadPlane.**
  - Estimated ~25–50 kB flash, < 16 kB RAM, ~2–8% CPU. About 270–325 kB of flash is
    free on current CubeOrange/Pixhawk6X builds (from published `.apj` files; our own
    commit's size was not measured).
  - EKF3 runs in double precision on the H7, so the UKF should too.
  - The interface spec: 86 `EKF3.*` call sites in `AP_AHRS`. The semantics matter
    (for example, `get_variances()` returns normalised test ratios), and so do the
    reset reports.
  - A new `EKFType` needs about 52 switch arms in `AP_AHRS.cpp`.
  - **Shadow running already works:** `dsn_tex_r1` flew on SIM and still logged EKF3
    (6654 `XKF1` rows, 2 lanes).
  - **QuadPlane loops at 300 Hz**, so EKF3's prediction dt differs from Copter's.
    The UKF must match it per vehicle.
- **The FGO off-board:**
  - **(a) ExtNav works today**, but what flies is EKF3 re-filtering the FGO output:
    the IMU is double-counted, and a 5° yaw floor applies.
  - **(b) There is no MAVLink or companion External-AHRS backend** at this commit, and
    External AHRS is compiled out on 2 MB boards.
  - **Fairness:** route (a) is "EKF3 fusing the FGO", not the FGO flying.
- **Companion compute:** the FGO (Python, 29 ms/step) and the camera pipeline
  (Python, ≤ 61 ms/frame on the i7, measured under load) need C++ ports to run
  together on a Pi 4/5. A resolution or rate change would break the frozen Phase 3
  calibration.
- **Replay:** no existing trial is replayable (`LOG_REPLAY=0`). A new DAL backend also
  needs log-format changes.
- **Closed loop:** under SIM the EKF failsafes never fire, and `crash_check` won't
  catch a wall scrape. Wall contact from GT is |x| ≥ 9.58 m. Current blank-floor
  behaviour would not survive in a 20 m corridor.
- **Where the FGO could fairly beat EKF3 (item 9):** nothing on disk shows it on ATE.
  - The candidates are **distance scale** (EKF3 +6–10% against the FGO's ~+1%, n = 9)
    and **consistency/NEES**, since the FGO's covariance has never been logged.
  - A forward-heading gain is only fair if EKF3 also gets that heading.
- **Effort:** ~18–30 person-weeks (estimate), plus 4–6 if route (b) is built.

**CORRECTION 1: where `AHRS_EKF_TYPE=10` comes from.**
- The Hidden Configuration Audit put it down to eeprom. It is (also) **injected as a
  default by SITL**: `SIM_JSON.cpp:410-413` calls
  `set_default_by_name("AHRS_EKF_TYPE", 10)` when the model sends `no_time_sync`. Our
  iris model sends `<no_time_sync>1</no_time_sync>` (`model.sdf:789`).
- ArduPilot's comment: without time sync the "EKF is likely to diverge".
- **Before any closed-loop run:** set `AHRS_EKF_TYPE` explicitly in a `.parm` file,
  confirm it from the log's PARM dump, and settle the time-sync question.

**CORRECTION 2: the ExternalNav yaw floor is 5°, set inside EKF3.**
- `NavEKF3_core::writeExtNavData` sets `yawAngErr = MAX(angErr, radians(5))`
  (`AP_NavEKF3_Measurements.cpp:1118`). This comes on top of the `VISO_YAW_M_NSE`
  clamp cited in the EKF3 ruling.
- **Replay's `REPH` records re-enter through the same function**, so injected heading
  cannot bypass it. This answers one of Option 1's open items: **EKF3 cannot be told
  that heading is better than 5°**, against the UKF/FGO's 0.13–0.15°.


## Source-pack flag resolutions (2026-09-29, documentation only)

Resolves the discrepancies flagged in `docs/thesis/numbers.md`. **Rule:** the later
measurement over more flights is current; the other moves to the superseded section with
a one-line reason. Where the rule does not settle it, that is said, and nothing is chosen.

**§1 FGO step time (window 0.25 s).**
- **Current: ~29 ms median on textured bags** (Part C, 2026-09-29).
- The stored 0.25 s runs give medians of:

  | world | n | median step (ms) |
  |---|---|---|
  | textured (`dsn`/`fwdc`/`fwdplainc`) | 9 | 26.9–29.2 |
  | transition | 9 | 15.1–15.7 |
  | blank | 9 | 4.0–4.3 |

  Source: `<trial>/fgo/metrics.txt` `step_median_ms`, runs of 2026-09-24.
- **The step time is world-dependent:** it scales with the number of flow factors in the
  window. Any single FGO step-time figure must state its world.
- **27 ms** is the textured-world figure from the 2026-08-01 window sweep on
  `dsn_tex_r1` (`04426d2`). It is kept as the sweep's own result, not as the current
  figure.
- **101 ms/step** is the superseded 1.0 s-window, pre-LM-cap configuration.
- **All of these are DIAGNOSTICS measured in Python on the workstation**, with parallel
  jobs and load not recorded. They say nothing directly about onboard feasibility.
  Phase 4's forward arms add a gating recursion, and their timing is reported separately.

**§2 EKF3 yaw drift with no compass.**
- **Current: +6.6…+11.1 deg/min, mean ~8.1, from `XKF1.Yaw`, n = 9 `dsn_*` bags**
  (`ca4c474`, 2026-07-29).
- **The window is not stated in the record** (commit `ca4c474` or the text). It is to be
  stated if the figure is re-derived.
- **Superseded: "~5 deg/min"** (`6f953b2`). Its origin is the single-trial residual
  **+5.32 deg/min** on `nomag_corridor_baseline` (`257204d`). That is one trial, and not
  representative of `dsn_*`, where EKF3 corrects only ~14–33%.

**§3 UKF gyro-z bias overshoot, `dsn_tex_r1` baseline.** There are two definitions in
the source:
- **Definition A, "% of 9.8":** |mean estimated gyro-z bias over the cruise window| ÷ the
  constant physical drift of 9.8 deg/min (raw gyro-z integrated).
  - This is the code up to `51aaeba`: `bgz_frac = 100*|bgz_mean|/PHYS_DRIFT`,
    `PHYS_DRIFT = 9.8`.
  - Stored runs (re-run 2026-09-24): baseline (`ukf_precorr`) `bgz_mean` −21.793 →
    **222.4%**; sign-flip (`ukf_signflip`) −32.929 → **336.0%**.
- **Definition B, "% of the instantaneous true mean":** the same numerator ÷ the window
  mean of the true SITL triangle-wave bias, `sitl_gyro_drift(t)`, ≈ 8.88 deg/min.
  - This is the code since `51e1bb9`: `bgz_frac = 100*|bgz_mean|/true_mean`.
  - Same runs: baseline **245.3%**; sign-flip **≈ 370.7%**, using 8.884. That run did not
    store its own window mean.
- **The "245% → 336%" pair in the sign-flip paragraphs mixes the two:** 245 is B, 336 is
  A. Consistent pairs are **A: 222% → 336%** and **B: 245% → ~371%**.
- **The thesis uses definition B**, the current harness definition. It is measured
  against the true, time-varying bias, as recorded in the ramp-tracking finding.
- A is kept only where the source table labels it ("% of 9.8").

**§4 Distance / velocity scale.**
- **Current (n = 9, derived in Part C, item 9 row A):**
  - EKF3 **+5.7…+9.6%**;
  - FGO **+0.9…+1.1%**;
  - basis: path-length ratio of estimate to GT over cruise, with 20 s resampling, on
    `dsn_tex`, `fwdc_tex` and `fwdplainc_tex`.
- Corroborated by `disp_ratio`: EKF3 1.04–1.06, FGO 0.98–0.99 on 12 textured bags.
- **Superseded: +12.6% (EKF3) / +4.7% (FGO).** That was n = 1 (`dsn_tex_r1`),
  speed-magnitude based and pre-`h_flow`-correction.
- **The scale-cause check ("bounded check 5a") is still PENDING.** It is not yet defined
  anywhere in this record, so its scope needs to be written down before it is run.

**§5 OI-2 commit.**
- `cc588df` (fwd-camera, 03:39) and `9b0f5d9` (master, 08:18) record **the same OI-2
  opening**. Their text is identical except that `9b0f5d9` adds one line ("…rules on
  whether a correction goes through the re-run gate.").
- `9b0f5d9` is the consolidated dsn-record commit on `master`, merged into `fwd-camera`
  via `54b9bce`.
- **Cite `9b0f5d9`**: it is on both branches, including `fwd-camera`, where the thesis
  results are. `cc588df` is noted as the first recording.

**§6 Stale working-file sections** were brought in line with this record in CLAUDE.md:
- the corridor worlds;
- the IMU bridge rate and port, plus the manual Terminal 2 and Terminal 11;
- the UKF "not yet implemented" header;
- the nomag "throwaway" label;
- the FGO step time;
- the not-yet-implemented list.

In PROGRESS.md, the old Known Issues and Next Priorities blocks got banners.

### Phase 4 run note — thread oversubscription found and fixed (2026-09-29)

**The problem.** The first launch of the 90 replays (01:02, six in parallel) ran with
default numerical-library threading.
- Each FGO process ran 12 threads, and the load average reached ~43 on 12 logical CPUs.
- The FGO forward-arm replays took over 80 minutes each and had not finished.

**The fix.**
- **Stopped at 02:28**, with the user's approval. The 11 completed jobs were kept; the 6
  in progress were redone.
- **Restarted at 02:34** with `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=1`.

**Identity check first (on `fwdc_tex_r2`, which the batch had not reached).** With the
thread limit, each of these is **byte-identical** to its default-threading counterpart:
- the FGO baseline, against the stored `fgo/`;
- the FGO heading + yaw-rate arm;
- the UKF heading + yaw-rate arm.

**Threading therefore changes no result.** The 11 jobs completed before the restart are
kept as valid.

**It changes timing only (DIAGNOSTIC).** The FGO forward-arm step fell from ~101 ms (the
earlier two-in-parallel test, already oversubscribed) to **35 ms median** single-threaded.
The baseline step is 27.6 ms. Phase 4 timing is reported from the restarted, thread-limited
runs, with the thread setting stated.

## Phase 4 — result (2026-09-29): all 90 replays done; reported, not judged (judging is Phase 5)

**Completeness.**
- **90/90 replays completed**, with 0 failures. Runner log:
  `~/thesis_data/batches/phase4_replays/jobs.log`.
- **Pre-registered regression check passes: 36/36 baseline trajectories (UKF and FGO,
  all 18 bags) are byte-identical** to the stored ceiling-dataset runs.
- Results: `eval/results/phase4_{fwdc,fwdplainc}_{evo,arms}.json`, produced by
  `eval/phase4_eval.py`.
- Values below are the **mean of 3 repeats, with the [min–max] range**. EKF3 is the fixed
  no-heading reference.

**Textured-floor world, evo -a (cruise) in m:**

| | EKF3 | UKF baseline | UKF +heading | UKF +heading+yaw rate | FGO baseline | FGO +heading | FGO +heading+yaw rate |
|---|---|---|---|---|---|---|---|
| `fwdc` (textured walls) | 3.80 [3.44–3.99] | 14.28 [7.30–20.94] | 6.62 [6.61–6.63] | 6.62 | 4.69 [4.42–4.97] | **0.47 [0.46–0.49]** | 0.47 |
| `fwdplainc` (plain walls) | 4.10 [3.88–4.26] | 11.49 [8.71–15.81] | 6.64 [6.61–6.67] | — | 4.71 [4.64–4.82] | **0.54 [0.52–0.57]** | — |

**Yaw error against GT over cruise (RMS, degrees):**

| world | baseline UKF / FGO | +heading UKF / FGO |
|---|---|---|
| textured walls, textured floor | 68.2 / 21.8 | 0.08 / 0.18 |
| **plain walls, textured floor** | — | **1.59 / 1.97** (heading acceptance 69% / 79%) |
| every other world and dataset | 8–77 / 19–23 | 0.08–0.56 / 0.11–0.38 |

**Transition world.**

| | EKF3 evo | FGO baseline → +heading | UKF baseline → +heading |
|---|---|---|---|
| `fwdc` | 21.75 | evo 26.04 → **20.70**; ratio 0.71 → 0.91; onset 95 → 110 m | evo 15.50 [7.97–25.67] → 19.61 [19.47–19.74]; ratio 0.81 → 0.76 |
| `fwdplainc` | 21.76 | evo 26.06 → 20.77; onset 95 → 109 m | 17.12 [7.40–31.55] → 19.79 |

**Blank world.** Heading removes the yaw error (RMS 0.08–0.19° with heading) but leaves
position essentially unchanged:

| | EKF3 | FGO baseline → +heading | UKF baseline → +heading |
|---|---|---|---|
| `fwdc` evo | 34.62 | 26.24 → 26.37 | 13.00 → 13.82 |
| `fwdc` ratio | — | 1.52 → 1.56 | 1.23 → 1.28 |
| `fwdplainc` evo | 34.94 | 25.73 → 25.84 | 12.54 → 13.51 |

**Yaw rate on top of heading (`fwdc` only).**
- **evo -a is unchanged to 0.01 m** in every world.
- **It changes the gyro-z bias estimate** (|cruise-mean estimate| ÷ true instantaneous
  mean; definition B):

  | | heading only | + yaw rate |
  |---|---|---|
  | FGO | 55–56% | 86–95% |
  | UKF | 118–120% | 97–109% |

- Yaw-rate gate acceptance is 72–75%, as flagged: the pre-registered σ_ω is tighter than
  the observed innovations. Heading acceptance is 96–100% on `fwdc`.

**Observations for Phase 5 (recorded, not interpreted).**
1. **With heading, the UKF's textured error collapses to one value, 6.61–6.67 m in both
   datasets,** with displacement ratio 0.85: a ~15% along-track under-travel. The FGO with
   heading has ratio 1.01.
2. **The FGO-with-heading textured result (~0.5 m) beats EKF3's 3.8–4.1 m. This is not a
   like-for-like comparison:** EKF3 has no heading, by ruling (information asymmetry). The
   Phase 5 claim is within-estimator only.
3. **On plain walls over a textured floor, heading is weaker, but the position gain holds**
   (FGO 0.54 m). This matches the Phase 3 finding that floor aliasing, not wall texture,
   is what degrades heading there.
4. **On blank floors, fixing yaw does not fix position:** flow starvation dominates.

**Plain-wall transition, Phase 3 heading by segment**
(`eval/results/fwd_transition_segments.json`; previously in the JSON only):

| segment | availability | noise sd | outliers |
|---|---|---|---|
| checkerboard half (y < 80 m) | 84.9–85.0% | 0.50–0.52° | 5.2–5.9% |
| blank half (y > 80 m) | 90.1–91.1% | 0.18–0.21° | 0.1–0.2% |

- **The plain-wall heading weakness is confined to the checkerboard half.**
- Yaw rate fails on both halves (outliers 5.3–5.5% checker, **30.7–31.6% blank**).
- With textured walls, both halves pass: heading sd 0.12–0.14°, 0% outliers.

**Timing (DIAGNOSTIC; workstation Python, single-threaded numerical libraries, 6 jobs in
parallel).**
- Only the 79 restarted jobs are used. The 11 pre-restart jobs ran oversubscribed: their
  results are valid (identity-checked) but their timing is not comparable. So n = 2–3 per
  cell.
- **UKF:** predict step 1.5–1.6 ms median (p95 ≤ 2.1 ms), 0.12–0.13 of the 12.5 ms period.
  Forward update 0.25 ms (heading) / 0.49 ms (heading + yaw rate), against a 33 ms period.
- **FGO keyframe step, median / p95 ms (period 33.3 ms):**

  | | textured | transition | blank |
  |---|---|---|---|
  | baseline | 32.7–32.9 / 37–38 | 17–18 / 33–37 | 4.5 / 16–18 |
  | +heading | 37–40 / 44–46 | 23–35 / 44 | 11–12 / 19–23 |
  | +heading+yaw rate | 42 / 49 | 27 / 46 | 12.5 / 25 |

- The added cost is the Python gate-covariance recursion (numerical Jacobians). **Textured
  forward arms run ~1.1–1.3× over the 33 ms period.**
- **This says nothing directly about flight-controller or companion feasibility, and
  changes no Phase 4 setting.**

## RULINGS (user, 2026-09-29) after Phase 4

**1. The post-hoc yaw-rate sensitivity arm is cancelled.**
- **Two-question rule:** once heading is fused, yaw rate changes evo -a (cruise) by
  < 0.01 m in every world. So the pre-registered σ_ω cannot change a position claim.
- **Reported as observed, with no further arm:**
  - the gate rejects **25–28%** of valid yaw-rate measurements (acceptance 72–75%), because
    the pre-registered σ_ω (0.162 deg/s) is tighter than the observed innovations;
  - yaw rate **improves gyro-z bias tracking**: FGO **55–56% → 86–95%** of the true bias
    (definition B), and UKF 118–120% → 97–109%.

**2. The superseding rule is applied to the "~+6.5%" scale figure** (the lateral-drift
mechanism paragraph).
- It first appears in `4a023df` (2026-07-29) as "the documented ~+6.5% scale", but **its
  source measurement is not documented anywhere in the record**. It predates the `h_flow`
  correction and is at most a single-flight figure.
- **Current:** EKF3 +5.7…+9.6% (n = 9, derived; flag resolutions §4).

**3. Timing measured before the thread-limit fix is marked as such. Only post-fix timing
is current.**
- **Marked "before the fix":**
  - the 27 ms FGO step (window sweep, 2026-08-01);
  - the 29 ms textured and the 26.9–29.2 / 15.1–15.7 / 4.0–4.3 ms stored medians
    (2026-09-24 runs);
  - Part C's 29 ms/step and ≤ 61 ms/frame camera figures;
  - the 101 ms/step superseded 1.0 s figure.
- **Current (post-fix, single-threaded numerical libraries, Phase 4):**

  | | median | p95 | conditions |
  |---|---|---|---|
  | FGO baseline, textured | 32.7–32.9 ms | 37–38 ms | 6 jobs in parallel |
  | FGO baseline, `fwdc_tex_r2` | 27.6 ms | — | identity check, 3 jobs in parallel |
  | FGO +heading, textured | 37–40 ms | — | |
  | FGO +heading+yaw rate, textured | 42 ms | — | |
  | FGO baseline / +heading, transition | 17–18 / 23–35 ms | — | |
  | FGO baseline / +heading, blank | 4.5 / 11–12.5 ms | — | |
  | UKF predict | 1.5–1.6 ms | — | |
  | UKF forward update | 0.25–0.49 ms | — | |

- **Observation, recorded as data:**
  - the post-fix FGO **baseline** figures are not lower than the pre-fix ones (27.6 ms at 3
    in parallel; 32.7–32.9 ms at 6 in parallel, against 26.9–29.2 ms pre-fix), so these
    data show no inflation of the pre-fix baseline figures;
  - the inflation was large for the forward arms' gate recursion: 101 ms before the fix,
    35–42 ms after.
- The camera pipeline has no post-fix measurement. Its ≤ 61 ms stays marked pre-fix, with
  no current value.

## Phase 5 — evaluation against the pre-registered prediction (2026-09-29; analysis of Phase 4 outputs only)

`eval/phase5_analysis.py` → `eval/results/phase5_analysis.json`. No new replays.

**The prediction, verbatim** ("Forward-camera workstream — hypothesis"): *"the heading-driven
share falls, and the 26% residual stays roughly unchanged. If the residual also moves, that
is a finding, not a failure."*

**Method.** The same decomposition as `plots/lateral_checks.py`:
- errV_lat = estimated minus true lateral velocity;
- heading part = spd·(sin ψ_est − sin ψ_true);
- residual = errV_lat − heading part;
- share = mean(heading part) / mean(errV_lat).

**Checked:** it reproduces the recorded EKF3 `dsn_tex_r3` result exactly with the original
window (from aiding onset): 0.194 = 0.143 + 0.051 m/s, share 73.6%, cross-track 62.0 / 45.6 /
16.4 m, corr −0.226.

**Two differences from the original analysis, stated:**
- **Window:** here, the pinned evo cruise window (on `dsn_tex_r3` that gives share 69%
  rather than 74%).
- **UKF/FGO velocity:** from their own frame (yaw 0 along the corridor; GT mapped by a fixed
  −90° rotation), with lateral velocity differentiated from the stored positions.
  EKF3 keeps `XKF1` VE, as in the original.

Values are means over 3 repeats, in m/s (cross-track in m).

| dataset / world | estimator | heading part: baseline → +heading | residual: baseline → +heading | residual change vs itself | residual change / removed heading part |
|---|---|---|---|---|---|
| `fwdc` tex | UKF | +0.232 → 0.000 | −0.038 → −0.007 | −82% | 0.06–0.14 |
| `fwdc` tex | FGO | −0.141 → 0.000 | −0.006 → −0.003 | −50% | 0.02 |
| `fwdc` trans | UKF | +0.179 → 0.000 | −0.196 → −0.300 | +53% | 0.15–1.12 |
| `fwdc` trans | FGO | −0.148 → 0.000 | −0.195 → −0.365 | +87% | 1.13–1.15 |
| `fwdc` blank | UKF | −0.061 → 0.000 | −0.551 → −0.637 | +16% | 1.37–1.53 |
| `fwdc` blank | FGO | −0.145 → 0.000 | −0.582 → −0.780 | +34% | 1.37 |
| `fwdplainc` tex | UKF | +0.307 → −0.004 | −0.049 → −0.006 | −88% | 0.13–0.15 |
| `fwdplainc` tex | FGO | −0.143 → −0.003 | −0.005 → −0.002 | −60% | 0.02 |
| `fwdplainc` trans | UKF | +0.090 → +0.001 | −0.008 → −0.299 | large (baseline ≈ 0) | 0.14–1.76 |
| `fwdplainc` trans | FGO | −0.143 → 0.000 | −0.201 → −0.365 | +82% | 1.14–1.15 |
| `fwdplainc` blank | UKF | +0.016 → 0.000 | −0.631 → −0.633 | +0.3% | unstable (heading part ≈ 0.03) |
| `fwdplainc` blank | FGO | −0.121 → −0.001 | −0.611 → −0.773 | +27% | 1.27–1.36 |

**EKF3 reference** (no heading), in the same window: share 0.76 (`fwdc`) / 0.81 (`fwdplainc`)
textured, with residual +0.021 m/s; transition and blank shares 0.96–1.00, with residual
≈ 0.002 m/s.

### Verdicts

**(a) "The heading-driven share falls": PASS in all 12 estimator × world × dataset cells.**
- The heading part falls from 0.02–0.31 m/s to ≤ 0.004 m/s everywhere.
- Heading-driven cross-track goes from 18–93 m to ≤ 1.1 m.
- Judged on the heading part's magnitude. The share ratio itself is unstable where the total
  error is near zero: for example, `fwdplainc` tex with heading has shares of 0.20 / 0.56,
  which are ratios of mm/s quantities.

**(b) "The residual stays roughly unchanged": FAIL as worded in 10 of 12 cells.** The
pre-registration gave no numerical band for "roughly".
- **Textured:** the residual **shrank** by 50–88% (UKF −0.038 → −0.007, FGO −0.006 → −0.003
  m/s). That is small in absolute terms (≤ 0.043 m/s; ≤ 13 m of cross-track) against the
  heading part removed (0.14–0.31 m/s). **FGO textured:** the residual halved (−1.8 → −1.0 m
  cross-track). The total lateral error is now almost all residual, at ~0.003 m/s.
- **Transition and blank:** the residual **grew**: +53–87% in transition and +16–34% in
  blank. The exception is UKF `fwdplainc` blank, +0.3%.
  - **In every FGO transition and blank cell the residual grew by 1.1–1.4× the heading part
    that was removed**, so the total lateral velocity error did not fall: FGO transition
    −0.343 → −0.365 m/s.
- *(Descriptive only, not a definition of "roughly".)* The smallest residual changes are UKF
  blank (`fwdc` +16%, `fwdplainc` +0.3%).
- **By the pre-registration's own terms, the residual moving is "a finding, not a
  failure".** It is reported here as a failure of part (b) as worded.

### Where the heading arm made things worse: UKF transition (evo 15.50 [7.97–25.67] → 19.61 [19.47–19.74] m)

What the data show:
- **In the baseline, the heading part (+0.179 m/s) and the residual (−0.196 m/s) have
  opposite signs** and largely cancel: mean errV −0.017 m/s, spread −0.277 to +0.250 across
  repeats.
- **With heading,** the heading part is 0 and the residual is −0.300 m/s, consistent across
  repeats (errV −0.298 to −0.302).
- So the lower baseline mean evo came with large repeat-to-repeat spread, and is associated
  with the two components cancelling.
- The same pattern holds in `fwdplainc` transition: baseline errV +0.082 [−0.176, +0.441] →
  −0.298.
- **No further explanation is claimed.**

**FGO transition** improves in evo (26.04 → 20.70 m) while its lateral velocity error does
not fall. The improvement coincides with the along-track displacement ratio 0.71 → 0.91
(Phase 4).

### End wall (GT y > 140 m): confident wrong heading outputs

These are valid outputs (support ≥ S_MIN) with |error| > 3° against GT. Totals over 3 bags:

| dataset | valid outputs | wrong > 3° (max \|error\|) | UKF gate: fused / rejected | FGO gate: fused / rejected / not tested |
|---|---|---|---|---|
| `fwdc` | 3928 | 47 (6.7°) | **0 / 47** | **29 / 18** / 0 |
| `fwdplainc` | 2233 | 59 (8.5°) | **0 / 59** | **2 / 55** / 2 |

- "Not tested" means a later valid frame superseded it before the keyframe.
- The same frame-to-keyframe mapping is used for both FGO arms; the counts are identical with
  yaw rate.
- The flight data contain no gross end-wall errors like the static sweep's (−17° for +10°),
  because the true heading stays ≈ 0.
- **The FGO fused 29 of the 47 wrong `fwdc` outputs; the UKF fused none.** Recorded as data.
  The end-of-cruise FGO yaw error stays ≤ 0.53° (Phase 4).

### Plain walls over the checkerboard floor (`fwdplainc_tex`, heading arm)

| | gate acceptance r1 / r2 / r3 | yaw error RMS r1 / r2 / r3 | end-of-cruise yaw error |
|---|---|---|---|
| UKF | 68.5 / 66.4 / 71.2% | 0.35 / **4.05** / 0.37° | r2 **−17.4°** |
| FGO | 77.1 / 80.6 / 80.5% | 2.11 / 2.06 / 1.73° | ≤ 0.28° |

- The UKF r2 heading ends 17.4° off despite the heading arm. Recorded; not investigated here.

### Scope of claims

- **Within-estimator claims only.** EKF3 is the no-heading reference; no EKF3-vs-UKF or
  EKF3-vs-FGO claim is made with heading.
- **FGO vs UKF with heading** (textured evo 0.47 vs 6.62 m) is reported as a result but is
  **conditional on the distance-scale check**: the UKF's with-heading displacement ratio is
  0.85, the FGO's 1.01.


### Phase 5 — accepted (user, 2026-09-29)

**Result as accepted.**
- **(a) PASS 12/12.**
- **(b) FAIL as worded, 10/12.** Both the absolute and the relative residual changes are
  reported in the table above.
- **"Roughly" is not defined retrospectively.** The "residual change / removed heading part"
  column and the smallest-change remark are descriptive only. They are not a band.

**What the data show about the two components (a finding, not an explained mechanism).**
- Where the heading error is removed, the residual grows in transition and blank.
- In the UKF transition baseline, the heading part and the residual have **opposite signs**
  and largely cancel.
- **So the heading-driven and residual components were not independent in these bags.**
  Removing one changed the other.
- The decomposition's premise was that the residual is a separate term that removing heading
  error would leave alone. The data do not support that premise here.
- No mechanism is claimed.

**METHODOLOGY LESSON (standing rule from now on): every future prediction carries a numeric
threshold.** A verbal criterion such as "roughly unchanged" cannot be scored without
defining it after the fact. That is exactly what the pre-registration rules exist to prevent.

## Distance-scale check — result (2026-09-29; replaces "bounded check 5a"; 11:18–12:05, inside the half-day bound)

`eval/scale_check.py` → `eval/results/scale_check.json` (existing outputs, 18 ceiling bags).
There was one minimal diagnostic replay: UKF `fwdc_tex_r1` heading arm, with an opt-in state dump (`UKF_DUMP`, logging only). Its trajectory is byte-identical to the stored run.

**Measurements (cruise window), textured bags, all 6 bags consistent.**

| quantity | EKF3 | UKF (baseline / +heading) | FGO (baseline / +heading) |
|---|---|---|---|
| displacement ratio (Phase 4) | 1.04–1.06 | 0.68 / 0.85 | 0.98 / 1.01 |
| horizontal speed ratio (median \|v_est\| / \|v_gt\|) | **1.068–1.070** | **0.835–0.838 / 0.850–0.851** | 1.011–1.013 / 1.012–1.015 |
| height bias (m) | n/a (origin-dependent) | +0.014–0.016 | +0.011–0.013 |

- **The flow sensor itself** (measured forward flow ÷ flow predicted from GT through the shared
  `h_flow` model) reads **1.009** on every textured bag.
- **Transition** speed ratios: EKF3 1.035–1.038, UKF 0.85–0.87, FGO 1.03–1.04.
- **Blank:** EKF3 0.21–0.23 (it freezes), UKF 1.25–1.29, FGO 1.54–1.57.
- `FLOW_FXSCALER` and `FLOW_FYSCALER` are 0 in the logs. Our estimators apply no flow
  scaling either.

**EKF3 reads ~7% fast: a CONFIGURATION difference.**
- EKF3 forms the flow range from `heightAboveGndEst = terrainState − pd`, minus `FLOW_POS_Z`
  (`AP_NavEKF3_OptFlowFusion.cpp:297-316`).
- **The logged `XKF5.HAGL` equals the body-origin height, not the lidar range:**

  | bag | HAGL (m) | GT base_link height (m) | lidar range (m) |
  |---|---|---|---|
  | `fwdc_tex_r1` | 2.293 | 2.295 | 2.177 |
  | `fwdplainc_tex_r2` | 2.295 | 2.298 | 2.178 |
  | `dsn_tex_r1` | 2.284 | 2.293 | 2.168 |

- **So `FLOW_POS_Z = 0.13` gives a flow range of HAGL − 0.13 ≈ 2.16 m, against a true camera
  height of ≈ 2.05 m: a factor of 1.054–1.058.** Multiplied by the flow scale of 1.009, that
  predicts 1.064–1.067; measured, 1.068–1.070.
- **The 2026-08 derivation** in `flow_ekf.parm` and FGO_DESIGN ("`pd` cancels, the range is
  lidar-referenced, so 0.13 = camera − lidar") **is contradicted by the logged HAGL at
  runtime.**
- **The value matching the data is the camera's body position, `FLOW_POS_Z = 0.25`.** Not yet
  flown.
- This also accounts, arithmetically, for the historical pre-`FLOW_POS` +12.6% (n = 1):
  2.30 / 2.05 = 1.122.
- **It affects every EKF3 result recorded so far** (`dsn`, `fwd`, ceiling datasets). EKF3 runs
  live and no log is replayable, so **correcting it needs re-flying**.

**The UKF reads ~15% short: an IMPLEMENTATION difference.**
- Its velocity state is right: 0.507 m/s against 0.500, tracking flow with predicted/measured
  0.992. **Its position is integrated with the fixed nominal dt.**
- `ukf_replay.py` predicts once `acc_dt ≥ 0.0125`. With the dejittered 3.0006 ms IMU stamps,
  that is **every 5 samples = 15.00 ms** (dump: spacing mean, median, min and max all
  0.01500 s).
- But `ukf_core._process` integrates position and gravity with `p['dt'] = 0.0125`
  (`p += v·dt`, `dv_world = R·dv + g·dt`).
- **Predicted position scale:** 0.0125 / 0.015 × 1.014 = **0.845**; measured, **0.850–0.851**.
- **The gravity mismatch this creates**, 9.81 × 2.5/12.5 = **1.964 m/s²**, matches the UKF's
  accelerometer z-bias estimate of **1.971 m/s²**.
- So the UKF actually predicts at 66.7 Hz, not the recorded 80 Hz / 0.0125 s "exactly as
  EKF3". **EKF3 uses the accumulated interval as its dt** (`AP_NavEKF3_core.cpp:1036`).
- **It affects every UKF result recorded so far.** The UKF is offline, so correcting it needs
  only a re-replay.

**The FGO (~1.01) follows the flow sensor.** Its speed ratio matches the measured flow scale
of 1.009 within 0.5%, and its preintegration uses the actual IMU intervals. **No
configuration difference was found for the FGO.**

**Conclusion: configuration and implementation differences, not genuine model
differences.**
- **Both go on the batched corrections list:**
  - **EKF3:** `FLOW_POS_Z = 0.25`, requiring the datasets to be re-flown. Note also Part C's
    `AHRS_EKF_TYPE` / time-sync item for any re-flight.
  - **UKF:** use the accumulated IMU interval as the process dt, and scale Q with it. Re-replay
    all bags.
- **The with-heading FGO-vs-UKF comparison waits for the corrected re-run.**
- **Any cross-estimator ATE comparison involving EKF3 or the UKF is provisional until then.**
  This includes the dejittered `dsn` baseline tables.
- **Phase 5 caveat:** the UKF's lateral velocity in the decomposition is differentiated from
  its under-integrated positions, so the UKF's errV and residual magnitudes carry the same
  ~0.83–0.85 position scale. The heading part uses GT speed and is unaffected. **The Phase 5
  UKF verdicts are provisional on the corrected re-run.**
- **Records now known to be wrong:**
  - the `flow_ekf.parm` / FGO_DESIGN claim that 0.13 yields the true camera height;
  - the CLAUDE.md / METHODOLOGY statement that the UKF predicts at 0.0125 s "exactly as EKF3".
  - Both are corrected by this entry. The parameter file is **not** changed until the batched
    re-run is ruled.


### Heading share restated on the pinned cruise window (2026-09-29; batched correction)

**The ~74% heading share is SUPERSEDED.**
- It came from the old window, aiding onset to end of log, which includes the stop and
  landing.
- It drew on **one bag, `dsn_tex_r3`** (`plots/lateral_checks.py`).
- Recomputed with the same method on the **pinned evo cruise window**
  (`eval/results/heading_share_restated.json`, via `eval/phase5_analysis.ekf3`):

| bag | errV (m/s) | heading part (m/s) | **share** | residual (m/s) | cross-track err / heading / residual (m) |
|---|---|---|---|---|---|
| **`dsn_tex_r3`** (the original bag) | 0.218 | 0.150 | **68.9%** | 0.068 (31.1%) | 65.9 / 45.4 / 20.5 |
| *`dsn_tex_r1` (context, not in the original)* | 0.201 | 0.110 | *54.9%* | 0.090 | 60.7 / 33.3 / 27.4 |
| *`dsn_tex_r2` (context)* | 0.131 | 0.080 | *60.7%* | 0.052 | 39.8 / 24.2 / 15.6 |

- **The current figure is 69% (n = 1, `dsn_tex_r3`).** The three textured `dsn` repeats span
  55–69%.
- These are EKF3 values, so they also carry the `FLOW_POS_Z` scale (correction (i)). **They
  are to be restated again after the corrected re-flight.**

**Every place that quotes 74% (or its complement, 26%):**
- **METHODOLOGY:**
  - "Lateral drift … (CLOSED)", item 3 (annotated in place);
  - "Forward-camera workstream — hypothesis" (annotated in place; the prediction wording
    that follows is left verbatim as pre-registered);
  - the Phase 5 section (it already notes 69% on the pinned window, and quotes the
    prediction verbatim).
- **`docs/thesis/numbers.md`:** the heading-share and residual-share rows (moved to
  superseded).
- **`docs/thesis/methodology_index.md`:** entries for the lateral drift, the forward-camera
  hypothesis and open item 9.6.
- **Not quoted in PROGRESS.md or CLAUDE.md.** The "0.74" values there are RTF, not the share.

**Added to the batched corrections list as (iii).**

### UKF `fwdplainc_tex_r2` heading arm, 17.4° at cruise end: bounded check (2026-09-29, ~15 min of a 1 h box; existing outputs only)

Plot: `plots/phase5/ukf_checker_r2_gate.png` (UKF yaw error; each tested heading
measurement's error against GT, coloured accepted/rejected; NIS against the gate of 9;
acceptance per 5 s; GT y).

**What the data show, by corridor position (GT y):**

| y (m) | UKF yaw error | measurement error (median \|err\|) | acceptance | NIS |
|---|---|---|---|---|
| 0–100 | within ±0.3° | 0.1–0.3° | 70–86% | median ~1 |
| 100–125 | −0.2 → −0.5° | 0.3–1.1° | falls 70 → 30% | median 2 → 23 |
| **125–140** | **−1.1 → −11.4°** | 2–6° | **8, 2 and 1** accepted in the 10 s bins at 285–315 s | — |
| **> 140** | −14 → −21° | **0.09–0.17°** (correct) | **0%** | 20–970 |

- **In the 125–140 m band the UKF yaw error changes at −0.27 to −0.39 deg/s.** The few
  accepted measurements there have errors close to the estimate's own (−1.9, −5.1, −8.6°).
- **The baseline arm's unaided drift on this bag is +0.22 deg/s**, the opposite sign.
- **After y > 140 m, 244 measurements within 1° of truth are rejected in the last 40 s.**
- Throughout the flight, a band of wrong checkerboard headings at +3 to +5° is (correctly)
  rejected.

**Classification.**
- **The terminal state is gate lockout.** Once the estimate is 14–21° off, correct heading
  measurements fail the χ² gate (NIS 20–87 at the end), so no correction is possible.
- **The onset is not fully established within the box.** The yaw error grew during a
  stretch of degraded measurements with almost none accepted (y ≈ 125–140 m). The data do
  not separate the two possibilities:
  - the few accepted wrong measurements drove it; or
  - the estimate drifted and the gate admitted only measurements near it.

  The accepted errors track the estimate, which is consistent with either.
- **No fix and no new arm, as ruled.** The UKF's other two checkerboard repeats did not lock
  out (end-of-cruise error 0.01° and 0.26°). The FGO did not lock out on any repeat (≤ 0.28°).
- **Relevant to the UKF correction (ii):** the under-scaled position integration and the
  gravity-absorbing accelerometer-bias state are present in this run. Whether the lockout
  recurs after the correction is a question for the corrected re-run.

## Phase 5b — consistency (NEES) and the heading innovation covariance (2026-09-29)

**Replays.** 72 sandbox replays: UKF and FGO, baseline and heading, all 18 ceiling bags.
- Logging-only instrumentation, identity-checked.
- **All 72 trajectories are byte-identical to the Phase 4 outputs.**
- Analysis: `eval/phase5b_consistency.py` → `eval/results/phase5b_consistency.json`.

**Can the gating covariance be reused? Yes, as an approximation.**
- The FGO covariance used here is the gate-only **two-keyframe filtering recursion** (logged
  via `FGO_COV_LOG`, in any arm). It is **not the smoother's true marginal**, which the
  Python `BatchFixedLagSmoother` does not expose.
- UKF: its own P. EKF3: `XKV1` V08, as in `plots/ekf3_state_diagnostic.py`.
- **Caveat:** the UKF's lateral error carries the position under-integration found by the
  scale check (correction (ii)). UKF numbers are provisional until the corrected re-run.

**Cross-track consistency** (pinned cruise window; each estimator's own frame). Means over 3
repeats: % of samples outside ±3σ / mean 1-D NEES (consistent ≈ 1).

| dataset / world | EKF3 | UKF baseline | UKF +heading | FGO baseline | FGO +heading |
|---|---|---|---|---|---|
| `fwdc` tex | **0.0% / 0.44** | 57.6% / 153 | **0.0% / 1.19** | 62.4% / 167 | **0.0% / 0.28** |
| `fwdc` trans | 2.1% / 1.36 | 56.7% / 39 | 44.7% / 173 | 63.4% / 338 | 44.9% / 462 |
| `fwdc` blank | 63.3% / 12.5 | 98.7% / 752 | 98.8% / 857 | 98.8% / 2989 | 98.9% / 4682 |
| `fwdplainc` tex | **0.0% / 0.71** | 71.5% / 110 | **0.8% / 0.68** | 63.4% / 168 | **0.0% / 0.16** |
| `fwdplainc` trans | 0.0% / 1.35 | 66.9% / 137 | 44.2% / 169 | 63.0% / 351 | 44.7% / 476 |
| `fwdplainc` blank | 67.5% / 12.3 | 98.9% / 754 | 99.0% / 862 | 99.0% / 3173 | 99.3% / 4470 |

Median σ, cross-track: EKF3 4–8 m; UKF baseline 3.3–4.1 m and with heading ~1.0 m; FGO
1.1–1.2 m in textured and transition, 2.0–2.1 m in blank.

**What the data show.**
- **EKF3 is consistent in cross-track on textured and transition floors, and overconfident on
  blank.** This differs from the earlier `dsn_tex_r1` result (39% outside ±3σ; n = 1,
  whole flight from t = 44 s, pre-ceiling dataset). The two are not reconciled here; the
  window and dataset differ.
- **Both baseline replay estimators are overconfident in cross-track everywhere.**
- **With heading, both become consistent on textured floors** (FGO conservative, NEES
  0.16–0.28). **They stay overconfident on transition and blank.**
- **Consequence for Part C item 9 (candidate "B, consistency"):** these data do not show the
  FGO (baseline) more consistent than EKF3. The FGO baseline is overconfident where EKF3 is
  consistent. As usual, subject to the FGO covariance approximation.

**Heading innovation covariance S.** S = the estimator's predicted yaw variance + σ_ψ²
(0.148° `fwdc`, 0.126° `fwdplainc`). Medians:

| points | est. | √S | predicted yaw σ | \|est. yaw error\| | yaw NEES of the prediction (mean) |
|---|---|---|---|---|---|
| all headings, `fwdc` tex | UKF | 0.157° | 0.053° | 0.044° | 1.7 |
| | FGO | **0.499°** | **0.476°** | 0.085° | **0.25** (conservative) |
| all headings, `fwdplainc` tex (checkerboard, plain walls) | UKF | 0.139° | 0.058° | 0.186° | **184** (overconfident) |
| | FGO | **0.489°** | **0.472°** | 0.218° | 3.4 |
| end wall, wrong > 3°, `fwdc` | UKF (47, all rejected) | 0.198° | 0.131° | 0.171° | 3.0 |
| | FGO **accepted** (30) | 0.499° | 0.476° | **2.98°** | **33** |
| | FGO rejected (18) | 0.499° | 0.476° | 0.46° | 1.2 |
| end wall, wrong > 3°, `fwdplainc` | UKF (59, all rejected) | 0.136° | 0.052° | 0.107° | 4.6 |
| | FGO (2 accepted / 55 rejected) | 0.488° | 0.471° | 1.57° / 0.15° | 21 / 0.6 |

**What the data show.**
- **The FGO's wider heading acceptance comes from a larger innovation covariance.** Its
  predicted yaw σ is ~0.47–0.48°, **about 8–9× the UKF's** 0.05–0.06°. The measurement term
  is the same in both.
- **Against the actual yaw error, this makes the FGO:**
  - **conservative on textured floors** (NEES 0.25), where the UKF is roughly consistent
    (1.7);
  - **closer to consistent on the checkerboard floor with plain walls** (3.4), where the UKF
    is strongly overconfident (184). That matches the UKF r2 lockout above.
- **At the end wall,** the FGO accepted wrong headings (> 3°) at moments when its own estimate
  was already ~3° off (median 2.98°) while still reporting a 0.48° predicted σ: NEES 33.
  - These wrong outputs arrive in runs (Phase 5). The data are consistent with earlier
    accepted measurements, within the ~1.5° 3σ window, having moved the estimate toward
    them.
  - The mechanism is not established beyond that.
- **The end-wall counts differ by one from Phase 5** (FGO 30/48 here, against 29/47). That
  comes from the frame-to-keyframe mapping: here, the latest valid frame at or before each
  keyframe. It is recorded, not reconciled.
- **The FGO's predicted yaw σ comes from the gate-only covariance approximation.**

## CONSOLIDATED RE-RUN (user ruling, 2026-09-29): both baseline corrections accepted

**Ruling.**
- Batched corrections (i) EKF3 `FLOW_POS_Z = 0.25` and (ii) UKF accumulated dt are
  **accepted**. The consolidated re-run runs now.
- It unlocks every cross-estimator claim. **After it, results are frozen for writing.**
- **It is a correction, not a tuning pass:** no parameter changes beyond the listed
  corrections, and any result that changes direction is flagged.

### Step 1: UKF time-step fix, correction (ii), applied and verified offline

**The change** (`ukf_replay.py`, `ukf_core.predict(dt=)`):
- The predict step still fires once the accumulated IMU time reaches EKF3's target of
  0.0125 s.
- The process now integrates with the **actual** accumulated interval: 5 dejittered IMU
  samples = **15.0028 ms**, derived from the dejitter period.
- Q, the delta-form bias states, their initial σ and every rate conversion use that same
  step.
- Nothing else changed.

**Verified on `fwdc_tex_r1` (sandbox; the stored Phase 4 outputs are untouched):**

| | UKF baseline, old → new | UKF +heading, old → new |
|---|---|---|
| speed ratio | 0.838 → **1.006** | 0.851 → **1.021** |
| displacement ratio | 0.683 → 0.82 | 0.849 → **1.02** |
| evo -a (cruise), m | 14.60 → 12.17 | 6.62 → **0.83** |
| divergence onset | 72 → 122 m | — |
| accel-bias z, m/s² | 1.97 → **0.008** | → 0.007 |
| gyro-z bias vs truth | 429% → 354% | 118% → 98% |

**Everything that moved is explained by the fix.**
- Position is now integrated over the true interval, so the scale is ≈ 1.
- The accelerometer-bias state no longer absorbs the 1.96 m/s² gravity mismatch.
- The bias states and Q now match the real step, which moves the gyro-bias estimates.
- The baseline displacement ratio stays below 1 because its yaw still drifts (a curved
  path). That is heading error, not scale.

### Steps 2–3: time-sync A/B and FLOW_POS_Z = 0.25 verification (recorded before flying; half-day bound)

**Configuration for every re-run flight** (`consolidated_rerun.parm`, appended last to
`run_trial.sh`'s `--defaults`, and enforced by `fly_trial.py` `EXPECTED_PARAMS` via live set +
one soft reboot):
- `FLOW_POS_Z 0.25`, correction (i);
- `AHRS_EKF_TYPE 10`: still flown on simulator truth, as ruled;
- `LOG_REPLAY 1` and `LOG_DISARMED 1`.

**Two flights,** both `corridor_textured_fwdc` geometry, the standard mission (300 s,
0.5 m/s, 2 m, no compass):
- `tsx_off_tex`: time sync **off**, as in every dataset. World `corridor_textured_fwdc`,
  unchanged.
- `tsx_on_tex`: time sync **on**. World `corridor_tson_fwdc`, which differs only in using
  model `iris_fwd_ts` (identical to `iris_fwd` except `<no_time_sync>0</no_time_sync>`).

**Compared:** EKF3 evo -a (cruise), EKF3 displacement ratio and speed ratio, flow → EKF3
latency (median, p95), and RTF.

**Proposed thresholds for "material".** These are for the user's decision; n = 1 per
condition.
- EKF3 evo -a (cruise) differs by **more than 0.55 m** (the `fwdc` textured EKF3 n = 3
  range, 3.44–3.99);
- **or** the displacement ratio differs by **more than 0.02**;
- **or** the latency median differs by **more than 5 ms**.
- RTF is reported only.

**FLOW_POS_Z verification (step 3), on both flights.**
- **Pass:** EKF3 displacement ratio within **1.00 ± 0.02**, and speed ratio within
  **0.99–1.03** (the flow sensor itself reads 1.009).
- Also check that `XKF5.HAGL` − 0.25 equals the true camera height.
- All four re-run parameters are confirmed from each log's PARM dump.

### Steps 2–3: result (flown 12:26–12:40; `tsx_off_tex`, `tsx_on_tex`; `eval/results/tsx_{evo,timing}.json`)

**Configuration confirmed from each log's PARM dump:** `FLOW_POS_Z 0.25`, `AHRS_EKF_TYPE 10`,
`LOG_REPLAY 1`, `LOG_DISARMED 1`, `EK3_SRC1_YAW 0`. Replay records (`RFRH`, `RFRF`, `RFRN`,
`RISH`, `RISI`) are present, so **these logs are replayable**. `fly_trial.py` found every
parameter already correct, so no reboot was needed.

**Step 3, `FLOW_POS_Z = 0.25`: PASS on both flights.**

| | time sync off | time sync on | band |
|---|---|---|---|
| HAGL − `FLOW_POS_Z` / true camera height | 0.998 | 0.995 | — |
| EKF3 speed ratio | 1.019 | 1.022 | 0.99–1.03 |
| EKF3 displacement ratio | 0.99 | 0.99 | 1.00 ± 0.02 |

This compares with 1.068–1.070 speed ratio on the dataset flights (`FLOW_POS_Z = 0.13`).
**Correction (i) does what it was predicted to.**

**Step 2, time-sync A/B (n = 1 per condition).**

| | time sync off | time sync on | difference | proposed "material" threshold |
|---|---|---|---|---|
| EKF3 evo -a (cruise) | 3.22 m | 2.50 m | **0.72 m** | > 0.55 m: **exceeded** |
| EKF3 displacement ratio | 0.99 | 0.99 | 0.00 | > 0.02: not exceeded |
| EKF3 speed ratio | 1.019 | 1.022 | 0.003 | — |
| flow → EKF3 latency median / p95 | 22.6 / 33.6 ms | 21.6 / 32.5 ms | 1.0 / 1.1 ms | > 5 ms: not exceeded |
| RTF (cruise) | 0.839 | 0.836 | — | report only |

- P1 input timing is identical on both flights (flow and lidar 30.30 Hz with 0% late gaps;
  IMU mean gap 3.0005 ms).
- **Only EKF3 evo -a crosses its proposed threshold,** and that comparison is n = 1 against
  n = 1.
- For scale, EKF3's textured run-to-run spread (n = 3) was 0.55 m on `fwdc` and **2.29 m on
  `dsn`** (both under the old `FLOW_POS_Z`). **The 0.72 m difference is inside the `dsn`
  spread.** These data cannot separate a time-sync effect from run-to-run variation.
- **Decision: the user's.**

### RULING (user, 2026-09-29): time sync ON for every re-flown dataset

**Decided on correctness, not on the one-vs-one error difference** (which cannot separate an
effect from run-to-run spread). The reasons, as ruled:
- ArduPilot warns that EKF3 "is likely to diverge" without time sync
  (`SIM_JSON.cpp:410-413`).
- Closed-loop flight needs it.
- Real hardware is time-synchronised.
- It costs nothing measurable: RTF 0.839 → 0.836, flow latency 22.6 → 21.6 ms.

The two check flights (`tsx_off_tex`, `tsx_on_tex`) are **supporting data only**.

**Where time sync is set** (`<no_time_sync>0</no_time_sync>` in the drone model's
`ArduPilotPlugin`):
- **`dsn` worlds.** A vendored copy of the upstream `iris_with_ardupilot` lives at
  **`sim/models/iris_with_ardupilot/`**. It shadows `~/ardupilot_gazebo/models/iris_with_ardupilot`
  because `sim/models` comes first in `GZ_SIM_RESOURCE_PATH`. No world file changes.
  - Proof: `diff -r ~/ardupilot_gazebo/models/iris_with_ardupilot sim/models/iris_with_ardupilot`
    (upstream at `ardupilot_gazebo` `81e6b10`) shows **one line, 789:
    `<no_time_sync>1` → `<no_time_sync>0`**. The model name is unchanged.
- **Ceiling worlds.** Our vendored `sim/models/iris_fwd/model.sdf` gets the same one-line
  change (git diff: 1 insertion, 1 deletion).
- `iris_fwd_ts` / `corridor_tson_fwdc` are kept only as the record of the A/B. `iris_fwd_ts` now
  differs from `iris_fwd` only in its model name.
- **`AHRS_EKF_TYPE` stays 10** for all dataset flights, set explicitly in
  `consolidated_rerun.parm`, because SITL no longer injects it once time sync is on. **The
  dataset flights stay on simulator truth**, with every estimator an offline observer.

### RULING (user, 2026-09-29): re-fly scope and order

- **Order:** `p1c_*` (pass checks) → `dsn_*` → `fwdc_*` → `fwdplainc_*` → `ds_*`, about 4.9 h.
  `sweep_v*` is skipped.
- **The Phase 3 camera parameters stay frozen.** The re-flown `p1c_*` are check flights and a
  second validation, not a recalibration.
- **Every flight:** tmux, crash-safe runner, `LOG_REPLAY=1`, `LOG_DISARMED=1`,
  `FLOW_POS_Z=0.25`, time sync on, the same missions and worlds, and the IMU-gap rule.
- **Pass bands** are recomputed from the re-flown `dsn` baseline with the pre-registered
  formula.

## Closed loop — EKF3 flying the vehicle: smoke test (2026-09-29; recorded before flying)

**Why.** Every flight so far has been flown on simulator truth, so no estimator has ever
steered the drone. The supervisor's direction is that the estimators must eventually fly the
vehicle: first EKF3 in SITL, then our UKF as a drop-in EKF3 replacement, then real hardware.

In closed loop the controller steers by the estimate, so estimation error becomes physical
deviation, and the drone can hit a wall. **This is the first step: EKF3 flying, with no
estimator code changes.** This flight is **not part of any dataset and not compared across
estimators.**

**Settings.**
- The final re-fly settings: time sync on (`iris_fwd`), `FLOW_POS_Z 0.25`, `LOG_REPLAY 1`,
  `LOG_DISARMED 1`.
- **Plus `AHRS_EKF_TYPE 3`** (`closedloop.parm`, appended via `EXTRA_PARM_FILES`, and enforced
  by `fly_trial.py` via `EXPECT_OVERRIDE`).
- EKF3 sources are as in the datasets: flow + rangefinder, no GPS, no compass (`EK3_SRC1_YAW 0`).
- `AHRS_EKF_TYPE = 3` is to be confirmed from the log.

**Flight.**
- One flight, `cl_ekf3_tex`: world `corridor_textured_fwdc`, the dataset mission (arm in
  GUIDED, climb to 2 m, 300 s of 0.5 m/s cruise commanded in `MAV_FRAME_LOCAL_NED` along
  North, land).
- Launched by `sim/tools/closed_loop_run.sh`, with **no retry**.

**Arming.** If arming checks fail without GPS or compass:
- the exact failing checks are reported;
- only the minimum change needed to arm is made;
- every change is recorded;
- no other check is disabled.

**Wall contact and crash.** Judged from Gazebo ground truth (`sim/tools/wall_watch.py`):
- **wall contact:** |x| ≥ 9.58 m;
- **crash:** tilt > 60°, or height < 0.5 m after climbing and before the landing point.
- A breach stops the flight (SIGTERM to the trial's process group, which flushes the bag), and
  it is reported. **No retry with changed settings.**

**To report:**
- arms / completes the corridor;
- arming issues and the changes made;
- EKF3 estimated against true trajectory;
- physical deviation from the intended path (cross-track and along-track over the cruise);
- minimum wall clearance;
- EKF3 cruise position error, compared with the open-loop check flight `tsx_on_tex` (same
  settings, open loop);
- whether the replay records (`RFRH`, `RFRN`, `RISH`) are present.

### Closed-loop smoke test — result (`cl_ekf3_tex`, 2026-09-29)

**Outcome: the drone armed but did NOT complete the corridor.** It hit the west-wall threshold
(|x| ≥ 9.58 m) about 9 s into the cruise. The watcher stopped the flight, and **there was no
retry.** The flight is not part of any dataset.

**Settings, confirmed from the log's PARM dump:**
- `AHRS_EKF_TYPE 3`, `FLOW_POS_Z 0.25`, `LOG_REPLAY 1`, `LOG_DISARMED 1`;
- `EK3_SRC1_YAW 0`, `COMPASS_USE 0`, `EK3_SRC1_POSXY 0`, `EK3_SRC1_VELXY 5`, `EK3_SRC1_POSZ 2`;
- `GPS1_TYPE 0`, `SIM_GPS1_ENABLE 0`.

**Arming.**
- **No changes were needed.** `fly_trial.py` reported "All baseline params correct".
- `Arm: Gyros inconsistent` was logged 9 times over about 7 s, then it armed with nothing
  changed. This is normal warm-up: the same message appears 12× in `tsx_on_tex` and
  `tsx_off_tex`, and 9× in `dsn_tex_r1`.
- EKF3 started relative aiding at t = 10.8 s, before arming.

**What happened** (Gazebo truth vs EKF3 `XKF1`, NED, cruise start = first GT forward speed
> 0.2 m/s):

| cruise + | GT North | GT East | EKF3 North | EKF3 East | EKF3 East error |
|---|---|---|---|---|---|
| 3 s | 1.39 | −2.01 | 1.48 | +0.13 | +2.14 m |
| 6 s | 3.07 | −7.65 | 2.78 | +0.85 | +8.50 m |
| 9 s | 3.52 | −9.47 | 3.04 | +0.25 | +9.72 m |

- **Along-track** was roughly as commanded: 3.5 m in about 9 s at 0.5 m/s, with the EKF3
  North error ≤ 0.5 m.
- **Cross-track:** the drone accelerated west, to about 3.6 m/s true lateral speed. EKF3
  believed it was holding the track: its East estimate stayed within +1 m, and its VE never
  exceeded −1.2 m/s.
- **Wall contact:** at t = 37.52 s, x = −9.581, y = 3.60, z = 2.31 m. **Minimum wall
  clearance is 0**, because the contact threshold was reached. (The watcher summary's
  "1.48 m" is its last 2 Hz log row, not the minimum.)
- **Crash criteria** (tilt, height) did not trigger.

**Mechanism (measured, not tuned).**
- The EKF3 roll estimate fell progressively behind the truth: −4.0° vs −6.1° at 36.0 s, and
  −8.6° vs −11.1° at 36.5 s. Pitch matched exactly.
- The controller levels the *estimated* attitude, so the true tilt drove the drone west.
- The lateral flow that showed the motion was increasingly rejected: 31/84 airborne `XKF5`
  samples had NI ≥ 100, with |FIX| a mean of 830. In the open-loop `tsx_on_tex` the rejection
  rate was 3.6%.
- EKF3's X gyro-bias estimate moved from 0 to −0.09 over the same seconds.

**The same estimator error exists open loop.** In `tsx_on_tex` (same settings, flown on
simulator truth), EKF3's East error at cruise +3 / +6 / +9 s was **+0.07 / +0.31 / +1.09 m**,
with the same sign and growing. In closed loop the controller converted that error into
physical motion and amplified it.

**A 300 s evo -a (cruise) figure cannot be computed** for a 9 s cruise. The +3/+6/+9 s
comparison above is the like-for-like figure.

**Lateral flow channel — CORRECTED the same day: the lateral (X) flow sign is wrong in all
three estimators.** The first version of this paragraph "retracted" a sign flip on the basis of
a flawed regression. That retraction is itself withdrawn. See "FINDING — lateral optical-flow
sign" below.

**Replay records** are present:
- `RFRH` 13407, `RFRN` 82, `RFRF` 13445, `RISH` 1, `RISI` 26815, `ROFH` 819, `RRNH` 1,
  `RRNI` 154, `RMGH` 1, `RGPH` 1.
- `REPH` = `RBOH` = 0, which is expected: no ExtNav or body-odometry source is configured. The
  same is true in `tsx_on_tex`, `tsx_off_tex` and `dsn_tex_r1`.

**Artefacts and manual handling.**
- Output: `~/thesis_data/trials/cl_ekf3_tex/` and `~/thesis_data/closed_loop/cl_ekf3_tex/`
  (BREACH.txt, the watcher track and summary).
- The flight was killed mid-cruise, so `run_trial.sh` did not finish: there is no
  `metadata.yaml`, and `ardupilot.bin` was copied by hand from `logs/00000082.BIN` (it matches
  `LASTLOG.TXT` and the flight time).
- The watcher exited with an rclpy `ExternalShutdownException`, a side effect of the process
  group kill.

**Do the re-fly settings play a part?** Superseded. The lateral flow sign (FINDING below) is
part of every flight's EKF3 input, so it IS a problem with the re-fly configuration. **The
batch is held for a ruling.** (It never flew: it refused to start because the closed-loop run
had left processes running.) The original text follows.
- The dataset flights keep `AHRS_EKF_TYPE 10`, so EKF3 cannot steer them.
- The lateral-channel statistics are unchanged by time sync and match the pre-change bags.
- `FLOW_POS_Z` affects scale only, and the forward channel is clean.
- Per the ruling, the re-fly batch was started without waiting.

### Consolidated re-run — batch launch (2026-09-29)

- **Old data moved, not deleted.** The 42 pre-re-run trial folders with the re-flown names
  were moved to `~/thesis_data/trials_pre_rerun/`, so the re-flown trials keep their names
  and the crash-safe runner does not mark the old data ABORTED. The old numbers in
  `eval/results/` and `numbers.md` refer to those folders.
- **Batch 1: `batches/rerun_main.conf`** (33 trials, run by `rerun_main`):
  - order `p1c_*` (6) → `dsn_*` (9) → `fwdc_*` (9) → `fwdplainc_*` (9);
  - settings from `run_trial.sh` defaults (nomag + `consolidated_rerun.parm`);
  - `EXTRA_PARM_FILES` and `EXPECT_OVERRIDE` are unset.
- **Batch 2: `batches/rerun_ds.conf`** (9 trials, `rerun_ds`), started only after
  `rerun_main` is DONE:
  - the compass-active `ds_*` set, run with
    `EXTRA_PARM_FILES=compass_active.parm` and
    `EXPECT_OVERRIDE=EK3_SRC1_YAW=1,COMPASS_USE=1,COMPASS_USE2=1,COMPASS_USE3=1`;
  - these are the only four live-parameter differences between the old `ds_tex_r1` and
    `dsn_tex_r1` (from the PARM dumps; calibration state and counters excluded).

## FINDING — lateral optical-flow sign is wrong in EKF3's input and in the UKF/FGO model (2026-09-29)

**Found by the closed-loop smoke test.** The flight's roughly 3.6 m/s lateral excursion is the
first data in the project with substantial lateral velocity: the rms lateral speed was
1.56 m/s, against ≤ 0.014 m/s in every open-loop dataset. The lateral translation sign had never
been tested before. Stage A validated forward flow only, and Known Issue #1 records that roll
derotation was never tested.

**What the data says** (`/optical_flow/measurement` in the bag, against GT body velocity and
the co-sampled `/imu/data_raw` gyro, FLU, h = camera height):
- **Translation** (`cl_ekf3_tex`, 248 airborne frames, lateral v rms 1.56 m/s):
  - `flow_x_rad = +1.004 · v_left/h`;
  - `flow_y_rad = +0.994 · v_fwd/h`.
- **Rotation** (integrated gyro over each frame interval, high-passed; lag fixed at −16 ms,
  which is where the forward axis fits best and is independent of this question):
  - `flow_x_rad ≈ +1.5 · ω_x` (R² 0.99 in `tsx_on_tex`, `dsn_tex_r1` and `fwdc_tex_r1`; +1.50
    in `cl_ekf3_tex`);
  - `flow_y_rad ≈ −1.2 · ω_y`.
  - With no lag fixed, the roll term is ambiguous. The roll content is a narrowband tone near
    17–18 Hz (the vibration that the IMU-rate work found at 17.4 Hz), so a half-period lag
    (28 ms) flips its apparent sign. That is why the first regression, and the closed-loop
    section's first draft, went wrong.
  - Magnitudes above 1 are consistent with the gyro being attenuated by the 20 Hz 2-pole INS
    filter at about 17 Hz, plus a lever-arm term of about 0.14. That is a separate, open
    magnitude question, not a sign question.
- The measured signal is self-consistent in **ArduPilot's own convention**
  (`AP_NavEKF3_Measurements.cpp:221,227-228`: `flowRadXY = −raw`,
  `comp = flowRadXY + bodyRate`; `OptFlowFusion.cpp:334-335`: `losPred = (+v_right/h, −v_fwd/h)`).
  That convention requires:
  - `raw_x = v_left/h + p` and `raw_y = v_fwd/h + q` (FRD rates);
  - the Y channel satisfies this with `raw_y = +flow_y_rad`, which is why Stage A worked;
  - the X channel satisfies it with **`raw_x = +flow_x_rad`**.

**What each estimator assumes.**
- **EKF3** (`flow_bridge.py:123`, since `f3a5559`, 2026-07-14): `flow_rate_x = −flow_x_rad`.
  - This is **wrong**: EKF3 sees the lateral translation with the wrong sign, and the roll term
    added rather than cancelled.
  - Evidence: airborne |FIX| is 326–446 against |FIY| 8–9 in every open-loop dataset.
  - In closed loop the wrong translation sign is positive feedback, which is the runaway.
- **UKF/FGO** (shared `measurement_models.h_flow_pose`, `SIGN_X = −1` since `a19196a`,
  2026-07-29): they predict `flow_x = −v_left/h − ω_x`.
  - The **whole X row is negated**: on the closed-loop bag the measured-vs-model slope is −0.96
    and the correlation −0.99.
  - The Y rotation term is also negated: the model has `+ω_y` against about −1.06 measured once
    the lever arm is removed. It has little effect because the pitch rate is small (0.008 rad/s
    high-pass rms).
  - The 2026-08-01 test flipped only the X rotation term. That left the X row internally
    inconsistent (translation still negated), which explains why it made the UKF worse.
- **Root cause (ours, not a parameter or plugin):**
  - `FLOW_ORIENT_YAW = 0`, and the camera mounting is consistent. Both estimators' X mappings
    come from the untested derotation formula in `flow_tracker.py` (`flow_x_rot = −FOCAL·rollspeed`;
    the data gives +).
  - The UKF's Y rotation sign is an FRD→FLU slip: `flow_tracker.py` uses `+pitchspeed` (FRD),
    which is `−ω_y` in FLU.
  - `flow_x`/`flow_y` (the characterisation-only derotated fields) inherit the same roll
    sign error.

**Scope.** Every flight since Stage A has this flow input: `ds_*`, `dsn_*`, `p1c_*`, `fwd*_*`,
`fwdc_*`, `fwdplainc_*`, `tsx_*`, `sweep_*`. Every UKF and FGO result uses the negated model.

**Estimated effect in the open-loop datasets.**
- True lateral velocity was ≤ 0.014 m/s rms, so the translation flip itself contributes little
  directly.
- The main effect is the uncancelled roll tone. EKF3's X measurement carried about
  (1.4 + 1) × 0.2 ≈ 0.5 rad/s rms of roll content instead of about (1.4 − 1) × 0.2 ≈ 0.08. At a
  1.8 m camera height that is about 0.9 m/s of equivalent lateral-velocity noise instead of
  about 0.15.
- Observed EKF3 lateral-velocity error over cruise:

| bag | mean | rms |
|---|---|---|
| `ds_tex_r1` | +0.16 m/s | 0.33 m/s |
| `dsn_tex_r1` | +0.20 m/s | 0.31 m/s |
| `dsn_blank_r1` | +0.14 m/s | 0.16 m/s |
| `fwdc_tex_r1` | +0.07 m/s | 0.10 m/s |
| `p1c_fwdc_tex` | +0.10 m/s | 0.13 m/s |

- The compass-active `ds_tex_r1` shows the same bias, so it is not a heading effect.
- These are **upper bounds on the flip's contribution, not attributions**. The counterfactual
  needs the corrected re-fly (EKF3) or corrected replays (UKF/FGO).
- The lateral-drift decomposition, the heading share, the flow→yaw coupling finding and every
  cross-track number may be affected. They are to be restated after the fix.

**Status:** fix proposed, and the re-fly batch is held pending the user's ruling. The
proposed fix and verification are in the session report.

## Lateral flow sign — rulings, fix and verification (2026-09-29)

**Ruling (user, 2026-09-29).** The diagnosis and fix are accepted. The full history stays
visible, with entries marked rather than erased:
- the original model (`SIGN_X = −1`, `−ω_x`; `flow_bridge` `−flow_x_rad`, since Stage A);
- the 2026-08-01 partial flip and why it made the UKF worse (the section marked above);
- the wrong "retraction" in the closed-loop section and its withdrawal (both kept there).

**Fix applied** (one commit; data untouched):
- `flow_bridge.py`: `flow_rate_x = +flow_x_rad` (was `−`).
- `measurement_models.h_flow_pose`: `flow_x = +v_left/h + ω_x` (`SIGN_X = +1`, rotation
  `+ω_x`) and `flow_y = +v_fwd/h − ω_y` (rotation was `+ω_y`). The lever arm and forward
  translation are unchanged.
- `flow_tracker.py` (characterisation-only `flow_x`/`flow_y`): roll term back to
  `+FOCAL·rollspeed`, the original derivation; the flip had come from the confounded hover
  test. The pitch term is unchanged, since it is `+pitchspeed` in FRD and already matched.
- The UKF and FGO both call `h_flow_pose`, so one change covers both.

**Open item (ruling 3, not acted on):** the rotation-term magnitude is ~1.4–1.6 × the
filtered gyro on X and ~1.2 on Y. It is consistent with the 20 Hz 2-pole INS filter
attenuating the ~17 Hz roll tone. It is not changed unless check 2b fails its |FIX|
criterion, and then only after reporting.

### Check 2a — fixed model against the closed-loop bag: PASS

On `cl_ekf3_tex` (248 airborne frames, 1.56 m/s rms lateral), measured `flow_x_rad` against
the fixed `h_flow_pose` (GT pose and velocity, interval-averaged co-sampled gyro):
- **slope +0.959, correlation +0.992** (0.3 s smoothing);
- +0.906 to +0.960 across smoothing windows of 1–15 frames;
- +0.957 to +0.960 over |v_left| > 0.3 m/s only.

The band was +0.8 to +1.2. The old model gave −0.96 / −0.99.
- **Side effect on the forward axis:** correlation 0.298 → 0.978, slope 0.84 → 1.00, from
  the corrected `flow_y` rotation sign.

### Check 2b — open-loop check flight with a sideways step: pre-registration (before flying)

**Flight** `lfs_check_tex`. It is not part of any dataset.
- World `corridor_textured_fwdc`, flown on simulator truth (`AHRS_EKF_TYPE 10`).
- The fixed bridge, time sync on, `FLOW_POS_Z 0.25`, `LOG_REPLAY 1`, `LOG_DISARMED 1`.
- The standard mission plus `SIDESTEP=60,0.5,6`: from 60 s of cruise, command +0.5 m/s East
  for 6 s and then −0.5 m/s for 6 s, back to the centreline. The peak offset is 3 m, and
  forward speed is unchanged. `fly_trial.py`'s `SIDESTEP` is unset for every dataset.

**Pass criteria (fixed by the ruling):**
1. airborne mean |FIX| ≤ 150;
2. `XKF5` rejections (NI ≥ 100, airborne) ≤ 1%;
3. over the step window (step start − 1 s to step end + 2 s), the least-squares slope of
   EKF3's `XKF1` lateral velocity on GT lateral velocity is 0.8 to 1.2;
4. over the same window, the fixed `h_flow_pose` prediction against measured `flow_x_rad`
   has slope 0.8 to 1.2 (the 2a method).

**Basis and margin for |FIX| ≤ 150, and the prediction.**
- **Method.** The OF log records exactly the (raw flow, body rate) pair that EKF3 fuses. So
  the post-fix compensated flow can be reconstructed from existing logs as
  `comp_new = OF.flowX + OF.bodyX`, against the old `−OF.flowX + OF.bodyX`. The innovation
  is |losPred − comp|, with losPred = v_right/h from truth or from EKF3's own state (the two
  agree within 5%).
- **Validation.** The method reproduces the old logged |FIX| on textured bags:

| bag | logged | reconstructed |
|---|---|---|
| `tsx_on_tex` | 402 | 387 |
| `tsx_off_tex` | 414 | 389 |
| `dsn_tex_r1` | 446 | 428 |
| `fwdc_tex_r1` | 326 | 310 |
| `fwdplainc_tex_r1` | 344 | 332 |

  It overestimates on transition bags (277 → 402), where fewer blank-half samples are fused.
- **Prediction after the fix: |FIX| ≈ 250–380** (`dsn_tex_r1` 249–264, `tsx` 302–308,
  `fwdc_tex_r1` 383, `fwdplainc_tex_r1` 369). **Criterion 1 is therefore PREDICTED TO FAIL.**
- **Why.** Correcting the sign removes the reversed translation, but it does not make EKF3's
  roll cancellation work. `AP_OpticalFlow_MAV` averages the gyro over the flow-message
  *arrival* interval (`gyro_sum` between messages), not the camera's capture interval. The
  roll content is a ~17 Hz tone, so that pairing is phase-incoherent in either sign. The
  OF-log body-rate coefficient on X was −0.78 / −0.36 / +0.32 across bags.
- **Consequence.** This is the rotation-term (timing/magnitude) open item, not the sign. No
  sign-only fix can meet ≤ 150. The ruled band stands as fixed; this pre-flight prediction
  is recorded so that a failure is not read as a failed sign fix.
- **Other criteria predicted to pass:** 3 (EKF3 now sees lateral motion with the right sign)
  and 4 (the 2a result, slope about 0.96).
- **Rule:** if any criterion fails, stop and report. Check 2c and the batch do not proceed.

### Excitation checks — methodology note (ruling 7)

Open-loop straight flights cannot detect sign errors on axes they do not excite. Every open
dataset has lateral speed ≤ 0.014 m/s rms, so a negated lateral flow row was invisible from
Stage A until the first closed-loop flight. Closed-loop flight and deliberate excitation
manoeuvres (the `SIDESTEP` hook) do excite those axes.
**Standing rule from 2026-09-29: any new sensor model gets an excitation check before use.**
Each axis it measures must be excited deliberately, and its sign and scale regressed against
truth.

### Records (rulings 5 and 6)

- **Trial folders moved (2026-09-29).**
  - The 42 pre-re-run folders that share names with re-flown trials are in
    `~/thesis_data/trials_pre_rerun/`, moved and not deleted: 6 `p1c_*`, 9 `dsn_*`,
    9 `fwdc_*`, 9 `fwdplainc_*`, 9 `ds_*`.
  - Every trial name referenced in `eval/results/` and `docs/thesis/` is present there with
    its `bag/`.
  - The results files hold trial names, not absolute paths, so their numbers stay traceable
    to `trials_pre_rerun/<name>`.
  - **72 absolute symlinks** (the `dsn_tex_r*_oi2*` variant folders, the Phase 5b and
    UKF-dt-check sandboxes) pointed into `trials/<moved name>/`. They were broken by the move
    and would have silently resolved to the NEW data after the re-fly. They were retargeted to
    `trials_pre_rerun/`, and no broken links remain under `~/thesis_data`.
  - `plots/lateral_checks.py` hardcodes `trials/dsn_tex_r3`. It is a script, and after the
    re-fly it reads the new data (the restatement).
- **`cl_ekf3_tex` is a diagnostic record, not a dataset.** It is incomplete: the flight was
  killed at the wall, there is no `metadata.yaml`, `ardupilot.bin` was hand-copied from
  `logs/00000082.BIN`, and the bag ran about 12 min past the breach until the recorder was
  stopped by hand. It is used only for the sign diagnosis and check 2a.
- **Batched correction (iv): the lateral flow sign** (EKF3 bridge and `h_flow_pose`). Every
  exposed result is restated after the re-run:
  - the heading share (69% restated; originally 74%);
  - the Phase 5 drift decomposition (errV, heading part, residual, correlations);
  - all cross-track numbers (EKF3/UKF/FGO lateral error, onset, displacement ratio);
  - the flow→yaw coupling / acceptance-driven leak finding (FINDING 4) and the 2026-08-01
    derotation-coupling characterisation;
  - the Phase 4 arm magnitudes (evo -a (cruise), yaw error, gyro-bias, NIS, acceptance);
  - the Phase 5 verdicts and the Phase 5b NEES and heading-S results;
  - the scale check (forward, but it uses the shared model);
  - EKF3 lateral noise (|FIX|, XKF5 rejections, lateral-velocity error);
  - the dejittered `dsn` baseline tables and every cross-estimator ATE.
- **`sweep_v*`:** not cited for anything on the lateral axis. `analyse_flow_sweep.py` uses
  median |`flow_y`| (forward), and METHODOLOGY cites `sweep_v*` only as skipped. It **stays
  skipped.**

### Check 2b — result (`lfs_check_tex`, flown 2026-09-29): FAIL on criterion 1 (as predicted); criteria 2–4 PASS

**Settings confirmed from the PARM dump:** `AHRS_EKF_TYPE 10`, `FLOW_POS_Z 0.25`,
`LOG_REPLAY 1`, `LOG_DISARMED 1`, `EK3_SRC1_YAW 0`. Replay records are present (`RFRH`
137497, `RISH` 1). The flight completed normally. The step reached a peak GT lateral speed of
+0.50 / −0.49 m/s and a peak offset of +2.96 m East, with GT |vE| > 0.1 from 91.7 to 104.7 s.

| criterion | result | band | verdict |
|---|---|---|---|
| 1. airborne mean \|FIX\| | **321** (\|FIY\| 10, n = 3147) | ≤ 150 | **FAIL**; predicted 250–380 before flying |
| 2. XKF5 rejections | 0.22% (NI mean 22.3) | ≤ 1% | PASS |
| 3. EKF3 VE on GT VE over the step window | **OLS slope +0.910** (intercept +0.045; through origin +0.917; corr +0.935; n = 161) | 0.8–1.2 | PASS |
| 4. measured `flow_x_rad` against the fixed `h_flow_pose` (2a method, 9-frame smoothing) | **slope +0.884**, corr +0.835, n = 444 | 0.8–1.2 | PASS |

- **The sign is confirmed.** EKF3 now follows the commanded sideways step with the correct
  sign, and the fixed shared model tracks the measured lateral flow. Before the fix, both had
  the opposite sign.
- **Criterion 1 fails for the pre-registered reason:** EKF3's roll derotation is
  phase-incoherent against the ~17 Hz roll tone (gyro averaged over the message *arrival*
  interval), and a sign fix cannot change that. The |FIX| of 321 falls inside the predicted
  250–380. **Per ruling 3, nothing about the rotation term was changed; this is reported
  first.**
- **Criterion 4 without smoothing:** slope +0.18, corr +0.14. Frame by frame, the raw
  `flow_x` is dominated by the same unmodelled roll tone (about 0.3 rad/s against about
  0.28 rad/s of step translation). The pre-registered 2a method (0.3 s smoothing) passes.
  The unsmoothed figure is stated so that it is not hidden.
- **Observation, not concluded from:** EKF3's yaw error jumped from +2.3° to +7.5° across the
  step (cruise +60 s to +90 s), against a background drift of about 9 deg/min. Lateral
  excitation couples into EKF3's no-heading yaw.
- **Per the ruling, "if anything fails, stop and report":** check 2c was not flown and the
  re-fly batch was not started.

### Check 2c — prediction written down (NOT flown; held with 2b's failure)

**Basis.** The open-loop EKF3 East error from `lfs_check_tex`, referenced to the start of
cruise. In closed loop the controller holds EKF3's estimate on the centreline, so the
physical cross-track ≈ −(open-loop EKF3 East error). This holds to first order; the
trajectories differ once the error grows.

| cruise + | 60 s | 90 s | 120 s | 150 s | 180 s | 240 s | 300 s |
|---|---|---|---|---|---|---|---|
| EKF3 East error (m) | −0.29 | +1.64 | +4.26 | +7.82 | +12.56 | +25.99 | +44.13 |
| yaw error (°) | +2.3 | +7.5 | +10.6 | +14.6 | +19.3 | +30.6 | +44.5 |

The overall yaw drift is 9.2 deg/min, within the `dsn` range of 6.6–11.1.

**Prediction:**
- **EKF3 with no heading source reaches the WEST wall (x ≤ −9.58 m)** at about cruise
  +160 s (open-loop |error| first ≥ 9.58 m at +161 s), with GT y ≈ 80 m.
- Allowing for the step's yaw jump, which a closed-loop smoke-test mission would not have,
  and first-order error: **contact between cruise +140 s and +200 s, y ≈ 70–100 m.**
- The 2c pass criterion (|x| < 9.58 m over the whole corridor) is therefore **predicted to
  FAIL**, because of heading drift, now that the sign-driven runaway is removed.
- The expected sequence is a slow, yaw-driven arc into the wall, not the fast (~3.6 m/s)
  lateral runaway seen in `cl_ekf3_tex`.

### Rulings on 2b and 2c (user, 2026-09-29)

- **2b criterion 1 (|FIX| ≤ 150) is recorded as FAILED as worded, and not re-scored.** Its
  basis, once worked out, predicted the failure before flying (reconstructed 250–380; flown
  321). **Criteria 3 and 4 are the direct tests of the sign, and both passed.** The sign fix
  is **accepted**.
- **The ~5° EKF3 yaw jump during the 2b sideways step is an observation only.**
- **Before any re-fly:** a bounded investigation of EKF3's flow-derotation timing
  (half-day time-box). Nothing that reaches EKF3 is changed without a ruling. **The batch
  stays on hold.**

**Check 2c: criterion restated BEFORE flying.**
- The original criterion, "|x| < 9.58 m for the whole corridor", is **SUPERSEDED**. The
  sign-driven runaway is fixed, and heading drift with no absolute heading source is
  predicted to cause wall contact (the prediction above).
- **New pass criteria, fixed before flying.** Cruise time is referenced as in the
  prediction: cruise start = GT forward speed (smoothed) first > 0.3 m/s.
  1. no wall contact before cruise +100 s (no fast runaway);
  2. if wall contact occurs, it is on the **west** wall (x ≤ −9.58) between cruise +140 and
     +200 s, with GT y ≈ 70–100 m, consistent with the written prediction.
- **Reported:** the outcome against the prediction, and EKF3's in-flight yaw drift rate
  against the 9.2 deg/min used for the prediction.
- **Flight:** `cl_ekf3_tex_2`, the same settings as `cl_ekf3_tex` plus the sign fix. It is
  launched by `sim/tools/closed_loop_run.sh` with the rewritten watcher, with no retry, and
  it is not part of any dataset.

### Check 2c — result (`cl_ekf3_tex_2`, flown 2026-09-29): PASS on both restated criteria

**Settings from the PARM dump:** `AHRS_EKF_TYPE 3`, `FLOW_POS_Z 0.25`, `LOG_REPLAY 1`,
`EK3_SRC1_YAW 0`, with the sign fix. Cruise start (GT forward speed first > 0.3 m/s) was at
`TimeUS` 30.66 s.

| cruise + | 30 s | 60 s | 90 s | 100 s | 120 s | 140 s | 160 s |
|---|---|---|---|---|---|---|---|
| GT East (m) | −0.49 | −0.44 | −2.17 | −2.52 | −4.48 | −6.60 | −9.14 |
| EKF3 `PE` (m) | −0.03 | +0.04 | −0.14 | −0.02 | −0.16 | −0.00 | −0.05 |
| EKF3 yaw error (°) | +2.0 | +3.5 | +6.2 | +7.4 | +9.2 | +12.1 | +15.1 |

1. **No wall contact before cruise +100 s: PASS.** At +100 s, x = −2.52 m. The maximum GT
   lateral speed before contact was 0.57 m/s, against about 3.6 m/s in `cl_ekf3_tex`. **The
   fast runaway is gone.**
2. **Contact on the west wall between +140 and +200 s, y ≈ 70–100 m: PASS.** Contact came at
   **cruise +164.2 s, x = −9.58, GT y (N) = 80.9 m**. The written prediction was about +161 s
   and y ≈ 80 m.

- **Mechanism, as predicted:** EKF3's East estimate stayed at 0 ± 0.16 m (the controller
  holds it on the centreline) while the true track arced west with the yaw error. It was a
  slow, heading-driven arc.
- **Yaw drift in flight: +5.8 deg/min**, against the 9.2 deg/min used for the prediction. The
  prediction's curve came from `lfs_check_tex`, which included the sideways step's ~5° yaw
  jump. The contact time still landed within 3 s of the point prediction. With drift that
  much slower, that agreement is partly coincidence and is **not claimed as quantitative
  validation of the first-order model.**
- **EKF3 flow innovations:** airborne |FIX| 320 (the same as open loop) and rejections 0.48%.
- **Stop path (rewritten watcher) worked in a real flight.** On the breach it sent SIGTERM to
  `fly_trial.py` and `run_trial.sh` by PID. run_trial's own cleanup stopped the recorder, so
  the bag is flushed and its `metadata.yaml` written. No process remained after 1 s, and the
  watcher exited 0 (`STOP_LOG.txt`).
- **Diagnostic record, not a dataset.** There is no trial `metadata.yaml`, because run_trial
  writes it only at a normal exit. `ardupilot.bin` was hand-copied from `logs/00000084.BIN`,
  which matches `LASTLOG.TXT` and the flight time.

## EKF3 flow-derotation timing — bounded investigation (ruling 2, 2026-09-29; about 1.5 h of a half-day box)

**Nothing that reaches EKF3 was changed.** All numbers below are reconstructions from
existing logs.

### (a) Our message path against a real sensor (source at `7bac20cbcc`)

**What we send.** MAVLink `OPTICAL_FLOW` (msg 100) with only the rate extension fields
`flow_rate_x/y` (rad/s, instantaneous), with `quality` and `ground_distance`, via MAVProxy
`--out` on 14553. `OPTICAL_FLOW_RAD` (msg 106), which carries `integrated_x/y`,
`integrated_xgyro/ygyro` and `integration_time_us`, is not handled by this build (Stage A).

**Receiver: `AP_OpticalFlow_MAV`.**
- `handle_msg` stamps the message at **arrival**: `latest_frame_us = AP_HAL::micros64()`,
  with the source comment "ToDo: add jitter correction" (`AP_OpticalFlow_MAV.cpp:105-107`).
  Our `time_usec` is ignored.
- `update()` runs at 200 Hz (`ArduCopter/Copter.cpp:158`). It sums the **AHRS gyro**
  (`AP::ahrs().get_gyro()`, the INS-filtered gyro) on every call (`:36-43`).
- When a message has arrived it outputs `bodyRate = gyro_sum/gyro_sum_count` (`:76`) and
  resets the sum (`:94-96`). **So the body rate is averaged over the interval between the
  `update()` calls that saw messages arrive, not over the camera's exposure interval.**
- The frontend passes (flow, bodyRate) to EKF3 (`AP_OpticalFlow.cpp:275-280`). EKF3 forms
  `comp = −flow + bodyRate − flowGyroBias`
  (`AP_NavEKF3_Measurements.cpp:193-194,206-207,221,227-228`) and dates it arrival −
  `EK3_FLOW_DELAY` (10 ms) − half the average interval − half a filter step (`:232-234`).
- **Our measured flow → EKF3 latency:** median 10.9 ms, p95 42.7 ms (`dsn_tex`; METHODOLOGY
  "Input timing").

**Real sensors.**
- **PX4Flow** (I²C) sends its own **gyro integral over the same integration timespan** as the
  flow integral, and `bodyRate = gyro_rate_integral / timespan`
  (`AP_OpticalFlow_PX4Flow.cpp:120-128`).
- **HereFlow** (DroneCAN) does the same: `flow_integral`, `rate_gyro_integral`,
  `integration_interval` (`AP_OpticalFlow_HereFlow.cpp:52-54,76-82`).
- **Pixart** (SPI on the flight controller) integrates AHRS gyro × dt over each burst,
  synchronously with the flow sample (`AP_OpticalFlow_Pixart.cpp:288-303,356`).
- **UPFLOW and MSP** use the same arrival-window AHRS-gyro averaging as the MAV backend
  (`AP_OpticalFlow_UPFLOW.cpp:101-109,177`; `AP_OpticalFlow_MSP.cpp:39-44,71`).

### (b) Genuine property or bridge artefact? Mostly neither: the vehicle's roll limit cycle meets the gyro filter

- **Arrival-window pairing is a genuine ArduPilot property of the MAVLink path.** Any real
  MAVLink flow source, such as companion-computer flow, gets it too. Its cost scales with
  latency and jitter times the frequency of the body motion.
- **Stated separately: which gyro is used matters more than when.** The same logs give three
  reconstructions (`lfs_check_tex`, 9396/10130 fused frames matched to their bag frames by
  value; the method reproduces the logged |FIX| 321 as 307):

| pairing | reconstructed \|FIX\| |
|---|---|
| A: current (arrival window, AHRS filtered gyro) | **307** |
| B: bridge derotates with the co-sampled `HIGHRES_IMU` gyro averaged over the camera frame, plus `FLOW_OPTIONS` Stabilised | **355** (no better) |
| C: derotation with the TRUE frame-integrated body rotation (GT quaternions), plus Stabilised | **67** |

- **The flow is correct.** It tracks the true roll rotation with slope 1.19.
- **The problem is that every available gyro is the 20 Hz 2-pole INS-filtered gyro**
  (`INS_GYRO_FILTER 20`; the AHRS gyro and `HIGHRES_IMU` both return `_gyro_filtered`). At the
  17.5 Hz roll tone that filter attenuates the gyro to about 0.7× (hence the flow/gyro
  "magnitude" of 1.4–1.5) and delays it by about 80° (hence the −16 ms best lag).
- **No filtered-gyro pairing, arrival-aligned or frame-aligned, cancels it.** Correct timing
  (B) does not help.
- A real integrating sensor avoids this only because it uses its own higher-bandwidth gyro.
- **Fairness consequence:** the UKF and FGO derotate with the same filtered gyro (via
  `HIGHRES_IMU` and `FlowFrameGyroAverager`), so the uncancellable roll content is
  **common-mode across all three estimators**. EKF3 additionally carries the arrival-pairing
  jitter.

### (c) Minimal bridge change: none admissible

- **B** is the "behave like a real sensor" change available with the data we have: derotate
  in the bridge over the frame interval, send it as stabilised, and let EKF3 subtract only its
  learned `flowGyroBias`. It makes |FIX| worse (355), so **it is not proposed**.
- **C** works (67) only because it uses simulator truth for rotation. That would feed truth
  into EKF3's input alone, which is **inadmissible** on fairness grounds.
- `OPTICAL_FLOW_RAD` would carry a sensor gyro, but it is unhandled in this build.
- A timing-only fix (regular messages, lower latency) cannot beat the filter's ~13–16 ms
  phase lag at 17.5 Hz.
- **Conclusion: no bridge change is recommended.**

### (d) The ~17.5 Hz roll tone is a simulation artefact: a roll-axis rate-loop limit cycle

- **It is absent with motors off.** Gyro-x rms is 0.0003 rad/s on the ground before takeoff,
  0.40 rad/s from the first 20 s airborne onwards (peak 17.5 Hz), and 0.40 in cruise.
  Pitch is 0.005–0.04.
- **It is in the whole roll control loop** (dataflash, aliased by the 10 Hz / 25 Hz logging to
  2.5 / 7.5 Hz):
  - `RATE.R` 22.8 deg/s rms, against a desired `RATE.RDes` of 2.2 deg/s rms;
  - roll PID D-term 0.11 rms and `RATE.ROut` 0.16 rms;
  - **motor PWM oscillating about ±67 µs rms**;
  - on pitch, `RATE.P` is 1.05 deg/s rms.
- **The cause is consistent with the plant.** The iris model has **Ixx = 0.008, Iyy = 0.015**
  and rotor arms of ±0.22 m (roll) and ±0.13 m (pitch). Roll authority per inertia is
  0.22/0.008 ≈ 27.5 against 0.13/0.015 ≈ 8.7, which is **about 3.2× the roll loop gain**.
- The roll and pitch rate gains are identical **firmware defaults** (P 0.135, I 0.135,
  D 0.0036). Neither `copter.parm` nor `gazebo-iris.parm` sets them, so they were never tuned
  for this airframe.
- A sustained 0.4 rad/s rms body oscillation at 17.5 Hz, next to the gyro filter corner,
  would be visible and removed by tuning (for example AutoTune) on a real vehicle. Real
  vibration sits at motor and propeller frequencies, far above the filter, where it causes
  negligible flow.
- **It is not claimed to be proven** that retuning removes it. That needs a check flight.

### Options for the ruling (none applied)

1. **Leave everything as is and document it.** The tone is a common-mode simulation
   artefact that affects all three estimators' lateral channel. EKF3's extra arrival-pairing
   jitter is a genuine property of ArduPilot's MAVLink flow path. The re-fly proceeds now.
2. **Remove the limit cycle at the source** with roll rate gains for this airframe (for
   example, pinned from a SITL AutoTune run, or scaled by the roll/pitch authority ratio),
   pinned in a `.parm` file and applied to every re-flown dataset.
   - This changes the vehicle, not any estimator input path. It is realistic (tuned
     vehicles).
   - It needs a pre-registered check flight: tone gone, |FIX| falling toward C's 67, pitch
     unchanged.
   - It adds one parameter change to the re-run and must be stated as a simulation-model
     correction.
3. The bridge changes B and C are not recommended (B does not help; C is inadmissible).

## Rulings (user, 2026-09-29): check 2c accepted; the roll oscillation is removed at its source

**Check 2c accepted.** Both restated criteria passed.
- **Caveat on the prediction match:** EKF3's in-flight yaw drift was 5.8 deg/min, against the
  9.2 deg/min in the prediction, so the close timing (+164.2 s against about +161 s) is
  **partly luck**.
- **`cl_ekf3_tex_2` is flagged as a candidate thesis figure.** EKF3's East estimate stays near
  zero while the true track arcs into the west wall.

**Derotation: option 2. The 17.5 Hz roll oscillation is removed at its source before the
re-fly.** Reasoning:
- it is a simulation artefact from untuned roll gains;
- it degrades every flow-based estimate;
- it likely penalises EKF3 more, because it interacts with ArduPilot's arrival-time jitter;
- fixing it changes the vehicle, not any estimator's input.

**Recorded as findings:**
- **EKF3's arrival-time pairing on the MAVLink path is a genuine ArduPilot property**
  (`AP_OpticalFlow_MAV.cpp:105-107,36-43,76`).
- **No bridge change is admissible.** Evidence, as reconstructed |FIX|: current pairing
  **307**, frame-aligned filtered-gyro derotation **355**, true-rotation derotation **67**.

**History (kept, not rewritten).**
- **The roll oscillation was first observed in July** (PROGRESS, 2026-07-02, `5787b04`),
  during the flow-derotation work. The record reads: "a persistent ~0.4 rad/s (23°/s)
  roll-rate oscillation present even at idle hover … real (visible camera shake …), but with
  ArduPilot's own VIBRATION and EKF_STATUS_REPORT reporting healthy/low levels, consistent
  with fast self-cancelling motor/frame buzz rather than a control-loop problem."
  - The user recalls it as a ~50 Hz buzz; **the written record gives no frequency**.
  - It was then accepted as a characterised noise floor ("background sim vibration source —
    deferred indefinitely"), **on the assumption that it affected all estimators equally.
    That assumption is now refuted:** it interacts with EKF3's arrival-time pairing.
  - It was also a control-loop limit cycle (at 17.5 Hz), not a buzz.
- **The roll derotation sign was flagged in July as validated only indirectly.** The same
  entry says "Pitch-only and roll-only isolated hover tests — not attempted", and the roll
  term's sign had been flipped after a hover test confounded by this oscillation. **That is
  the lateral sign error now fixed.**

### Roll rate gains: choice, basis and values (step a)

- **Basis: scale the roll rate gains so the roll loop gain matches pitch.** This is the
  simplest defensible basis, and SITL AutoTune was not needed (see the selection flight).
  - Full-body inertia from the flown model's SDF (`iris_with_standoffs`, identical in
    `iris_fwd_standoffs`), including the rotor masses by the parallel-axis theorem:
    **Ixx = 0.01252, Iyy = 0.01743 kg m²** (total mass 1.75 kg). The earlier 0.008 / 0.015
    was the base link only and is corrected here.
  - Rotor arms: 0.210 m (roll, mean |y|) and 0.130 m (pitch, mean |x|).
  - Torque authority per inertia: roll 0.210/0.01252 = 16.77, pitch 0.130/0.01743 = 7.46.
    **The ratio is 2.249**, which the identical gains turned into 2.25× the roll loop gain.
- **Values (`roll_rate_gains.parm`, in `run_trial.sh`'s defaults for every flight, and
  enforced in `fly_trial.py` `EXPECTED_PARAMS`):** P, I and D scaled by 1/2.249 = 0.4447.

  | parameter | old | new |
  |---|---|---|
  | `ATC_RAT_RLL_P` | 0.135 | 0.06003 |
  | `ATC_RAT_RLL_I` | 0.135 | 0.06003 |
  | `ATC_RAT_RLL_D` | 0.0036 | 0.0016 |

  Pitch, yaw, the filters, FF and the angle loops are unchanged.
- **Gain-selection flight** (`rgs_select_tex`: 60 s cruise, part of step a, not the check
  flight; **seen before this pre-registration and stated openly**):
  - cruise gyro-x rms **0.0017 rad/s**, against 0.398 with the old gains, and the 17.5 Hz
    peak is gone;
  - gyro-y rms 0.0034 and gyro-z rms 0.0027.
  - Scaling was sufficient, so SITL AutoTune was not used. **The bands below do not derive
    from these values.**

### Check flight `rgs_check_tex`: pre-registration (step b, before flying)

**Flight.** World `corridor_textured_fwdc`, the standard dataset mission (arm, climb to 2 m,
300 s of 0.5 m/s cruise, land) with **no** sideways step. Flown open loop on simulator truth
(`AHRS_EKF_TYPE 10`), with the final settings: sign fix, `FLOW_POS_Z 0.25`, time sync on,
`LOG_REPLAY 1`, `LOG_DISARMED 1`, and the new roll gains.

**References.**
- Old gains, standard mission: `fwdc_tex_r1..r3` (`eval/results/rgs_reference_fwdc_tex_oldgains.json`,
  `eval/rgs_profile.py`):
  - take-off (GT liftoff > 0.3 m to ≥ 1.8 m) 1.484–1.502 s;
  - climb peak z 2.233–2.242 m;
  - cruise GT height 2.290–2.299 m and speed 0.4999 m/s;
  - cruise gyro rms x 0.398, y 0.0054, z 0.0100 rad/s;
  - 15–20 Hz band rms on x 0.396.
- The P3 references are the existing same-world `dsn` n=3 means from `flow_quality_dsn.json`
  (textured: inlier_mean 0.9733 / inlier_pct_below_0.5 0.0073 / features_mean 52.8268 / flow_y_raw_mean 136.4536).
- Cruise is the span where GT forward speed exceeds 0.3 m/s, trimmed by 5 s at each end.

| # | criterion | band | basis and margin | class |
|---|---|---|---|---|
| R1 | roll oscillation removed | cruise gyro-x rms **≤ 0.05 rad/s** AND 15–20 Hz band rms **≤ 0.040 rad/s** | Pitch runs at the same effective loop gain at 0.0054 rms; allowing roll 10× pitch for lateral-control activity gives 0.05. The band condition is ≥ 20 dB (×10 amplitude) below the old 0.396. | PRIMARY |
| R2 | \|FIX\| toward the true-rotation floor | airborne mean \|FIX\| **≤ 150** | The floor is 67 (true-rotation reconstruction). The excess over it (240–254) is the uncancelled roll tone, which scales with its amplitude, so R1's ≥ 10× reduction leaves ≤ ~25: **predicted ≤ ~95**. The ×1.6 margin to 150 covers non-tone roll content and arrival jitter. | PRIMARY |
| R3 | pitch unchanged | cruise gyro-y rms within **[0.0027, 0.0108]** (0.5×–2× the old 0.0054) | Pitch gains are unchanged, so the expectation is equality. ±6 dB covers any change in roll→pitch coupling once the limit cycle is gone. | PRIMARY |
| R4 | take-off, hover and cruise profile | take-off 1.484–1.502 s ± max(range, 0.1 s) → **[1.384, 1.602] s**; climb peak ± max(range, 0.046 m) → **[2.187, 2.288] m**; cruise height ± 0.046 m → **[2.244, 2.345] m**; cruise speed **[0.4899, 0.5099] m/s**; GT \|x\| ≤ 0.05 m; the P1 timing bands and P3 downward-flow bands as in Phase 2 | 0.1 s is one `fly_trial` command period. 0.046 m is P3's "±2% ≈ 1 cm/s or 1 cm" basis applied to height (2% of 2.3 m). ±0.01 m/s is P3's speed-equivalent resolution. P1 and P3 are the existing dataset bands. | PRIMARY |
| R5 | no new oscillation on any axis | cruise gyro-y rms ≤ 0.0108 and gyro-z rms ≤ 0.0200 (2× old); on every axis the largest spectral peak's ±0.5 Hz band rms **≤ 0.02 rad/s** | A single tone above 0.02 would be ≥ 2× all of the old non-roll rotational activity (y and z total rms ≤ 0.010). | PRIMARY |
| D | diagnostics, not gating | XKF5 rejections, \|FIY\|, dataflash RATE/RCOU rms (aliased at 10 Hz), EKF3/UKF/FGO evo -a (cruise), P2 latency | The Phase 2 P4 outcome bands are **not applicable**: they are pre-sign-fix and pre-`FLOW_POS_Z`, and are recomputed from the re-flown `dsn`. | DIAGNOSTIC |

**Decision.** All PRIMARY criteria pass → the gain change is added to the batched corrections
as a simulation-model correction, and the re-fly batch starts. Any PRIMARY failure → stop and
report.

### Check flight `rgs_check_tex` — result (2026-09-29): ALL PRIMARY PASS

**Settings from the PARM dump:** `ATC_RAT_RLL_P/I 0.06003`, `ATC_RAT_RLL_D 0.0016`; pitch
unchanged (P 0.135, D 0.0036); `AHRS_EKF_TYPE 10`; `FLOW_POS_Z 0.25`; `LOG_REPLAY 1`;
`LOG_DISARMED 1`. It was the standard mission, and it completed normally.

| # | result | band | verdict |
|---|---|---|---|
| R1 | cruise gyro-x rms **0.0028** (old 0.398); 15–20 Hz band rms **0.0013** (old 0.396); x peak now 2.4 Hz | ≤ 0.05; ≤ 0.040 | PASS |
| R2 | airborne mean \|FIX\| **7** (p95 10, max 66), against 321 before | ≤ 150 (predicted ≤ ~95) | PASS |
| R3 | cruise gyro-y rms **0.0037** (old 0.0054) | [0.0027, 0.0108] | PASS |
| R4 | take-off **1.452 s**; climb peak **2.263 m**; cruise height **2.320 m**; speed **0.4999 m/s**; GT \|x\| ≤ **0.0093 m** | [1.384, 1.602]; [2.187, 2.288]; [2.244, 2.345]; [0.4899, 0.5099]; ≤ 0.05 | PASS |
| R4 P1 | flow and lidar 30.30 Hz, 0.00% late; IMU mean gap 3.0005 ms, p99 6 ms | Phase 2 P1 | PASS |
| R4 P3 | against the `dsn_tex` mean: inlier **+0.00999** (0.98332 vs 0.97333); % below 0.5 +0.36 pp; features −1.63%; `flow_y_raw` **−1.86%** | ±0.01; ±3 pp; ±5%; ±2% | PASS, **marginal on inlier and `flow_y_raw`** |
| R5 | largest peak, ±0.5 Hz band rms: x 0.0010 (2.4 Hz), y 0.0028 (7.4 Hz), z 0.0008 (15.2 Hz); gyro-z rms 0.0029 (old 0.0100) | ≤ 0.02; y ≤ 0.0108, z ≤ 0.0200 | PASS |

**Diagnostics (not gating).**
- **EKF3 fuses flow throughout:** `horiz_pos_rel` 100% of airborne time, `const_pos_mode` 0,
  and 97% of `FIX` samples non-zero. XKF5 rejections 0.00%; NI ≈ 0 because the innovations
  are tiny. |FIY| 8.
- **Dataflash `RATE` rms** (10 Hz log): R 0.15 deg/s (old 22.8), RDes 0.14, P 0.21, Y 0.16.
- **Flow → EKF3 latency:** median 18.6 ms, p95 29.8 ms, 100% matched. `eval/input_timing.py`
  now detects the bridge's X sign per trial; before this it matched with `−flow_x_rad`
  only, and gave 0% on post-fix bags.
- **EKF3 cruise speed ratio** (XKF1 VN median / GT; PN displacement ratio): `rgs_check_tex`
  0.935 / 0.945, against `tsx_on_tex` 0.955 / 0.973 and `lfs_check_tex` (with the step)
  0.909 / 0.916. That is a shift of about 2–3% with the new gains and the sign fix. It is
  **reported, not acted on**; the distance-scale check in the re-run restates it.
- **Cruise height** is about 2 cm higher (2.320 m against 2.290–2.299 m), within R4. It
  accounts for about −1% of the −1.86% `flow_y_raw` change.

**Interpretation.**
- **EKF3's old lateral innovation (|FIX| 300–450 in every dataset) was almost entirely the
  roll limit cycle.** With the limit cycle removed it is 7, the same level as the forward
  axis (|FIY| 8).
- The "67" true-rotation reconstruction was not a floor. It was limited by the 16 ms spacing
  of the GT samples against the 17.5 Hz tone.
- The two marginal P3 items (inlier +0.00999 and `flow_y_raw` −1.86%) are consistent with a
  steadier camera (fewer tracking losses) and the slightly higher cruise height. P3's
  references will be replaced by the re-flown `dsn`.

**Decision: all PRIMARY criteria pass.** Per the ruling, the gain change is added to the
batched corrections, and the re-fly batch is started without waiting.

### Batched corrections list — consolidated (2026-09-29)

| # | correction | kind | applied in |
|---|---|---|---|
| (i) | EKF3 `FLOW_POS_Z = 0.25` | configuration | re-flown bags (`consolidated_rerun.parm`) |
| (ii) | UKF process dt = the accumulated IMU interval | estimator implementation | re-replays |
| (iii) | heading share restated on the pinned cruise window (74% → 69%, then restated again) | analysis | re-run analysis |
| (iv) | lateral optical-flow sign: EKF3 bridge `+flow_x_rad`; `h_flow_pose` lateral row and forward rotation sign; `flow_tracker` roll derotation sign. Exposed results are listed under "Records (rulings 5 and 6)". | sensor model / bridge | re-flown bags (EKF3), re-replays (UKF/FGO) |
| (v) | **roll rate gains ×0.4447 (`roll_rate_gains.parm`)**, removing the 17.5 Hz roll limit cycle | **simulation-model correction** (the vehicle, not any estimator input) | re-flown bags |

Plus the earlier items: the OI-2 dejitter, the IMU-gap rule, time sync on (the vendored iris
model), `LOG_REPLAY` / `LOG_DISARMED`, and `AHRS_EKF_TYPE 10` set explicitly.

### Re-fly batch launch (2026-09-29)

- `tmux` session `rerun`: `~/thesis_data/batches/rerun.sh` runs
  `run_resumable_batch.sh batches/rerun_main.conf rerun2_main`. That is 33 trials in order:
  `p1c_*` (6), `dsn_*` (9), `fwdc_*` (9), `fwdplainc_*` (9).
- Then, only if `rerun2_main` is DONE, `batches/rerun_ds.conf` → `rerun2_ds`: the 9 `ds_*`
  trials with `compass_active.parm`.
- `SIDESTEP`, `EXTRA_PARM_FILES` and `EXPECT_OVERRIDE` are unset for the datasets.
- The earlier `rerun_main` state directory (`ff2b6a8`) flew nothing and is marked
  `SUPERSEDED.txt`.
- The missions and worlds are unchanged; flights are on simulator truth; the Phase 3 camera
  parameters are frozen.

## CLOSED-LOOP GOAL (user, 2026-09-29): EKF3 flying with the live forward-camera heading

**Goal (supervisor):** by the end of this week, closed-loop SITL + Gazebo flights that fly the
corridor well. Check 2c showed that EKF3 with no absolute heading reaches a wall through yaw
drift, which no tuning can fix. So the route is EKF3 flying (`AHRS_EKF_TYPE 3`), fed the
camera heading live through ArduPilot's ExternalNav yaw path. **There are no estimator code
changes.** Nothing flies while the re-fly batch or the pipeline re-run is running.

### EKF3 speed ratio: tsx 1.02 against rgs 0.935 — reconciled (they are different quantities)

- **tsx 1.019 / 1.022** is `eval/scale_check.est_scale`: the median of the 1 s-smoothed
  horizontal speed MAGNITUDE |v| from the stored EKF3 trajectory, against GT.
- **"0.935"** (`rgs_check_tex` report) was `XKF1.VN` alone against GT north speed: the
  projection on North. It is reduced by EKF3's growing yaw error (cos ψ_err, with ψ_err 20–40°
  late in cruise), so it is heading-dependent and **not a scale measure. That number is
  withdrawn.**
- **Like for like** (both metrics now in `scale_check.py`, plus EKF3's lateral velocity):

| flight | \|v\| ratio | along-track ratio | EKF3 lateral velocity, mean / rms |
|---|---|---|---|
| `tsx_on_tex` (old gains, pre-sign-fix) | 1.022 | 0.983 | +0.094 / 0.197 m/s |
| `rgs_check_tex` (new gains, sign fix) | 0.997 | 0.973 | +0.120 / 0.155 m/s |

- **What changed:** the magnitude ratio fell 2.5 points. Most of that is less lateral
  velocity noise inflating |v| now that the roll limit cycle is gone (rms 0.197 → 0.155).
  The along-track component moved only 1% (n = 1 each).
- The re-run scale check reports both columns.

### Part 1 — live heading bridge: built and tested offline (no simulation)

**Files:**
- `src/forward_camera/heading_bridge_core.py` (pure core, shared with the offline test);
- `heading_bridge.py` (ROS 2 node);
- `closedloop_heading.parm`;
- the `run_trial.sh` `HEADING_BRIDGE` hook, held as a patch
  (`~/thesis_data/batches/heading_bridge_run_trial.patch`), since the batch executes
  `run_trial.sh`;
- `sim/tools/closed_loop_run.sh` (`HEADING=1`);
- `sim/tools/wall_watch.py` (`--watch-process`);
- `eval/heading_bridge_offline.py`.

**Measurement.** The frozen Phase 3 heading, with the same code and parameters
(`fwd_calibration.json`): inlier tolerance 0.5°, S_MIN 200 px.
- The RANSAC seed is the frame's index in the image stream, exactly as in Phase 3. Live, the
  index counts from node start: same method, different seeds.
- **Runtime stack:** the node runs on the Phase 3 stack, system python with **OpenCV 4.6.0
  and numpy 1.26**. `venv-ardupilot` has OpenCV **5.0.0** and numpy 2.5, which would silently
  change a "frozen" measurement. pymavlink comes from a path shim.

**Message, and the answers to the user's seven additions** (source at the pinned
`7bac20cbcc`):
1. **`ODOMETRY`** (the dev docs' preferred message).
   - `frame_id = MAV_FRAME_LOCAL_FRD` and `child_frame_id = MAV_FRAME_BODY_FRD`, the only frames
     accepted (`GCS_Common.cpp:4066-4070`).
   - The heading goes in `q` (roll = pitch = 0).
   - The rate is 10 Hz (every 3rd frame), above the documented 4 Hz minimum.
   - `handle_odometry` always forwards a velocity too (`:4083-4086`). It is sent as NaN, so
     `writeExtNavVelData` returns early (`AP_NavEKF3_Measurements.cpp:1130`), and VELXY is flow
     in any case.
   - *Changed from the first build, which used `VISION_POSITION_ESTIMATE`.*
2. **Angle error.** ArduPilot combines the three covariance entries as
   `angErr = sqrt(cov[15] + cov[18] + cov[20])` (`GCS_Common.cpp:4077`).
   - Roll and pitch are set to 0, so `angErr` = σ_ψ exactly (0.148° `fwdc`, 0.126°
     `fwdplainc`), verified by an encode/decode round trip.
   - It is then clamped to `[VISO_YAW_M_NSE, 1.5]` rad (`AP_VisualOdom_MAV.cpp:43`), floored at
     5° by EKF3 (`AP_NavEKF3_Measurements.cpp:1118`), and fused with
     `R_YAW = max(err, 0.05)²` (`AP_NavEKF3_MagFusion.cpp:879`).
   - **Effective EKF3 yaw σ: 11.46° at the default `VISO_YAW_M_NSE` 0.2 rad; 5.00° if
     `VISO_YAW_M_NSE` ≤ 0.0873 rad** (range 0.05–1.0). **The value is for the user to rule on;
     it stays at the default until then.**
3. **Quality.** `quality = floor(50 · support / S_MIN)` (capped at 100), and −1 when there is no
   vanishing point, with **`VISO_QUAL_MIN = 50`** as the gate (`AP_VisualOdom_MAV.cpp:47-51`).
   - That accepts exactly the frozen Phase 3 validity: support 199 → 49 is rejected, 200 → 50
     is accepted.
   - Every processed frame is sent once the offset is set, and the dataflash `VISP` log records
     each as consumed or ignored.
   - *Changed: the first build dropped invalid frames in the node.*
4. **`VISO_TYPE 1`, not 3.**
   - 3 (VOXL) selects the IntelT265 driver (`AP_VisualOdom.cpp:145-147`). That driver adds a
     yaw trim, reset-jump handling and a 1 s ignore after resets, all for VIO.
   - Its automatic yaw alignment is explicitly refused when ExtNav is the yaw source
     (`AP_VisualOdom_IntelT265.cpp:143-146`).
   - 1 (MAVLink) passes the attitude straight to `writeExtNavData`, which is what a yaw-only,
     fixed-offset source needs.
5. **Yaw is fused with no ExtNav position fusion.**
   - The EXTNAV yaw branch of `SelectMagFusion` (`AP_NavEKF3_MagFusion.cpp:365-393`) does not
     depend on the position source. The first sample aligns yaw (`alignYawAngle`), and later
     samples go through `fuseEulerYaw(EXTNAV)`.
   - Position fusion needs `readyToUseExtNav()`, which is false unless POSXY is EXTNAV
     (`AP_NavEKF3_Control.cpp:613-621`).
   - The placeholder position (0, 0, 0; stated error 100 m) cannot enter the state either.
     `ResetPosition()` uses ExtNav only when `PV_AidingMode == AID_ABSOLUTE`
     (`AP_NavEKF3_PosVelFusion.cpp:124-162`), which flow aiding never reaches. This corrects
     Part C's open caveat.
   - **EKF origin:** nothing in the ExtNav yaw path checks `validOrigin`. The origin checks in
     MagFusion concern GPS and declination (`:687,718,1000`), so none is expected to be needed.
   - Both points are **to be tested in SITL on the ground** (disarmed and armed) once the batch
     and re-run are done.
6. **Alignment.** "Viso Align" (`request_align_yaw_to_ahrs`) exists only in the IntelT265/VOXL
   driver (the MAVLink backend's version is a no-op, `AP_VisualOdom_Backend.h:50`), and it
   refuses when ExtNav is the yaw source.
   - So the node's one-off offset is used instead. It is set on the ground before arming:
     the circular mean of `ATTITUDE.yaw + ψ` over the first 30 valid headings.
   - **Frame definition:** `yaw_AP = OFFSET − ψ` (wrapped). ψ is Phase 3's heading relative to
     the corridor, ENU-signed (nose left positive), and ArduPilot's yaw is NED.
   - **The sign is established from the static yaw sweep's definition** (`yaw_sweep.sh` sets
     ENU yaw = 90° + offset, and ψ tracks the offset with slope +1.007), not from the straight
     flight, where ψ is too small to discriminate (±0.3°).
   - The first message therefore equals EKF3's own yaw, so EKF3's first-sample alignment is a
     no-op.
   - It must be set before arming, because the VisualOdom arming check needs a message within
     300 ms (`AP_VisualOdom_Backend.cpp:33-37`).
   - **Ground truth is never used.**
7. **`GPS_INPUT` is not used.**

**Offline test** (`eval/heading_bridge_offline.py` on `fwdc_tex_r1`, the same core code the
node runs, niced and single-threaded;
`eval/results/heading_bridge_offline_fwdc_tex_r1.json`):
- **Match: PASS.** All **10,203 frames** are identical to Phase 3's `meas_frozen.npz` in
  heading (maximum difference 0.0°), support and validity (9,668 valid).
- **Timing** (under the batch's concurrent load, so an upper bound): median 90.5 ms, p95
  102.3 ms, minimum 53.4 ms per frame. At the lowest dataset RTF (0.72) a frame arrives every
  45.8 ms of wall time, so **N = 3** (10 Hz), and a processed frame always finishes before the
  next selected one.
- **On-ground validity:** 603/603 frames before take-off are valid, so the pre-arm offset is
  feasible.
- **Convention check against the dataflash SIM yaw (test only):** node convention −0.007° ±
  0.27°. This does not discriminate by itself; the sign is settled by the yaw sweep above.

**Latency and `VISO_DELAY_MS`.**
- ArduPilot's jitter correction (`GCS_Common.cpp:7373-7387`) maps the capture timestamp to its
  clock by assuming the fastest message had zero lag. So `VISO_DELAY_MS` must equal the
  MINIMUM capture-to-receipt latency.
- Offline gives only the processing part: minimum 53 ms wall, about 40–45 ms sim at RTF ~0.8.
- **Stated openly: the parameter file holds the ArduPilot default (10 ms) as a placeholder.**
  The value is set from the node's own log (`t_capture` against sim time sent) in the SITL
  ground test, before any flight.

**Watcher safeguard.** `wall_watch.py --watch-process heading_bridge.py`. If the node dies while
run_trial is running and the vehicle is airborne (z > 0.5 m), it is a breach and the flight is
stopped. The wall and crash checks never depend on the node.

### Part 2 — "flying well": pre-registration — DRAFT, SUPERSEDED BEFORE FLYING (see "Part 2 — revised")

> **SUPERSEDED (2026-09-29, before any closed-loop flight).** This draft assumed the default
> `VISO_YAW_M_NSE` (0.2 rad, an effective EKF3 yaw σ of 11.46°). The ruling set 0.05 rad, which
> gives 5.00°. Its B2/B3 bases (a ~1° tracking allowance) and its diagnostic prediction (a ~34°
> gate) no longer hold. Kept unedited as history.

**Flights** (each a closed-loop dataset, never compared with the open-loop datasets as if the
same experiment). All use the final settings: sign fix, `FLOW_POS_Z 0.25`, time sync on, the
new roll gains, `LOG_REPLAY`, and the watcher.
- (a) EKF3 without heading, `corridor_textured_fwdc`, ×1 (reference).
- (b) EKF3 + live camera heading, `corridor_textured_fwdc`, ×3.
- (c) only if (b) passes: EKF3 + live camera heading, `corridor_blank_fwdplainc` (plain walls
  over the blank floor), ×3.

**Bases (open-loop data, n = 1, stated):**
- `rgs_check_tex` (new gains, sign fix, no heading): EKF3 yaw drift **8.28 deg/min**.
  - 91% of its lateral velocity error is heading-driven.
  - The **non-heading residual cross-track is 3.76 m over the 300 s cruise**.
  - Open-loop East error reaches 9.58 m at cruise **+187 s**.
- `dsn` yaw-drift range (n = 9): 6.6–11.1 deg/min.
- Camera heading dropouts (Phase 3):
  - textured walls: longest gap 1.2–3.0 s, near the end wall;
  - plain walls over blank floor: none until y ≈ 144.5 m, then ~12 s to the end of cruise.

**(a) Prediction, written before flying.**
- West-wall contact at cruise **+187 s** (GT y ≈ 94 m).
- Lateral error grows as drift × t², so contact time scales as 1/√drift. The `dsn` drift range
  gives a **window of +161 to +209 s**.
- **PRIMARY:** no wall contact before cruise +100 s; contact, if any, on the west wall inside
  [+155, +215] s (the window rounded outward by 6 s for first-order error).

**(b) and (c): PRIMARY criteria (each flight):**
- **B1.** Completes the full mission (arm, climb, 300 s cruise, land) with no wall contact:
  |x| < 9.58 m throughout, and no crash criterion.
- **B2.** Maximum physical cross-track |x_GT| during cruise **≤ 6.5 m**.
  - Basis: the non-heading residual (3.8 m), plus the lateral displacement from a mean EKF3 yaw
    error of up to 1° over 150 m (150 · sin 1° = 2.6 m), which gives 6.4 m.
  - The margin to the wall threshold is 3.1 m.
- **B3.** EKF3 yaw error (`XKF1` vs SIM) during cruise: **95th percentile ≤ 2°, maximum ≤ 4.5°**.
  - Basis: tracking of order 1° with the ≥ 5° R floor, plus the drift during the longest
    dropout. That is 12 s at the maximum `dsn` drift of 11.1 deg/min, i.e. 2.2° for (c) and
    0.6° for (b), giving 3.2°. The margin is 1.3°.
- **B4.** No fast runaway: 1 s-smoothed |GT lateral speed| during cruise **≤ 0.25 m/s**.
  - Basis: 0.5 · sin(4.5°) = 0.04 m/s from yaw, plus about 2.5× the heading-free EKF3 lateral
    velocity noise (~0.10 m/s rms, `rgs_check_tex`).
- **B5.** No oscillation: cruise gyro rms roll ≤ 0.05, pitch ≤ 0.0108, yaw ≤ 0.02 rad/s (the
  `rgs_check_tex` R1/R3/R5 bands).

**DIAGNOSTIC (reported, not gating):**
- the fraction of heading messages consumed (`VISP`) and fused by EKF3 (yaw test ratio);
- the number of confident-wrong end-wall headings (valid, |error vs GT| > 3°, y > 140 m) that
  EKF3 fused, with the predicted outcome: **most are fused**, since the 3σ gate on an ≥ 11.46°
  σ admits errors up to ~34°;
- the flow → EKF3 and camera → EKF3 latency;
- the heading-bridge frame drops;
- RTF.

**Decision:**
- (b) passes if all three flights pass B1–B5.
- (c) runs only if (b) passes.
- Any B1 failure stops the set and is reported.

### Rulings (user, 2026-09-29) on Parts 1 and 2

1. **`VISO_YAW_M_NSE = 0.05` rad** (the documented minimum; added to `closedloop_heading.parm`
   and enforced by `closed_loop_run.sh`).
   - The effective EKF3 yaw σ is then **5.00°**. It is set by **ArduPilot's hard clamp in
     `writeExtNavData`** (`MAX(angErr, radians(5.0f))`, `AP_NavEKF3_Measurements.cpp:1118`),
     not by the parameter. **The 5° floor is an ArduPilot limit.**
   - Reasoning: the camera heading is accurate to ~0.15–0.3°, so both options over-state its
     error. The fairest choice is the least distorted value ArduPilot permits. It is a
     documented parameter within its documented range (0.05–1.0), **so EKF3 remains stock.**
2. The Part 2 bands and predictions were recomputed for 5.00°. The default-based draft is
   marked SUPERSEDED above, before flying.
3. **Accepted as reported:**
   - `VISO_TYPE 1`;
   - `quality = floor(50 · support / 200)`, −1 with no vanishing point, `VISO_QUAL_MIN 50`;
   - the one-off pre-arm offset (Viso Align is unavailable with ExtNav as the yaw source);
   - `yaw = offset − ψ`, from the static sweep;
   - processing every 3rd frame (10 Hz), with the same per-frame method and parameters.
   - **The version pin is part of "frozen":** the heading node runs on the Phase 3 stack,
     **OpenCV 4.6.0 and numpy 1.26** (system python), never `venv-ardupilot`'s OpenCV 5.0.0.
4. **`VISO_DELAY_MS`** is set from the minimum capture-to-receipt latency measured in the SITL
   ground test, before any flight. The measurement is recorded.
5. The speed-ratio reconciliation is accepted; **0.935 is withdrawn.** The re-run scale check
   reports both the magnitude and the along-track ratio.
6. **Working rule:** never edit any file a running batch uses; changes are held as patches
   until the batch ends.
7. **The 91% heading-driven share is preliminary** (one check flight). The re-run heading-share
   restatement is the value that counts.

**Order after the batch:** finish the Part 4 build → the pipeline re-run → the SITL ground test
(yaw-only fusion, arming with the heading node, `VISO_DELAY_MS`) → the closed-loop flights as
pre-registered. **Commit when the flights end.**

### Part 2 — revised pre-registration at the ruled 5.00° EKF3 yaw σ (before any closed-loop flight)

**New basis: an offline approximation of EKF3's yaw subsystem** (`eval/cl_yaw_prediction.py`
→ `eval/results/cl_yaw_prediction_5deg.json`; archived `fwdc_tex_r1..3` and
`fwdplainc_blank_r1..3`).
- **States:** yaw and gyro-z bias (delta form).
- **Predict:** every 12.5 ms with EKF3's own formulas, `q_att = (dt · GYRO_P_NSE)²` and
  `q_bias = (dt² · GBIAS_P_NSE)²`, driven by the recorded gyro-z.
- **Update:** with the frozen camera heading on every 3rd frame when valid, R = (5°)², and a gate
  of |ν| ≤ 3√S (`EK3_YAW_I_GATE 300`).
- **It is not EKF3.** It omits EKF3's coupling of flow into yaw (the Phase 5 flow→yaw finding),
  its other states, and the first-sample alignment. So the bands carry an explicit margin for
  that.

| world (archived, n = 3) | yaw error p95 | yaw error max | mean (lag on the drift ramp) | cross-track from yaw alone | confident-wrong end-wall headings (every 3rd frame) / passing the gate |
|---|---|---|---|---|---|
| `fwdc_tex` | 0.25–0.28° | 0.28–0.37° | −0.17…−0.18° | 0.46–0.49 m | 0–2 / **all** |
| `fwdplainc_blank` | 0.26° | 0.34–0.46° | −0.18…−0.19° | 0.54 m | 3–6 / **all** |

**(a) No heading, textured, ×1.** Unchanged (no camera):
- predicted west-wall contact at cruise +187 s;
- **PRIMARY:** no contact before +100 s; contact, if any, on the west wall inside [+155, +215] s.

**(b) and (c): PRIMARY criteria (each flight), revised:**
- **B1.** Completes the full mission and lands with no wall contact (|x| < 9.58 m throughout),
  and no crash criterion. *(Unchanged.)*
- **B2.** Maximum physical cross-track during cruise **≤ 6.0 m**.
  - Prediction ≈ 4.3 m: the non-heading residual of 3.76 m (preliminary, n = 1, from
    `rgs_check_tex`) plus ≤ 0.54 m from the yaw error.
  - The 1.7 m margin (~40%) is for the n = 1 residual. The margin to the wall threshold is 3.6 m.
  - *(Was ≤ 6.5 m.)*
- **B3.** EKF3 yaw error during cruise: **95th percentile ≤ 1.0°, maximum ≤ 2.0°**.
  - Prediction: p95 ≤ 0.28° and maximum ≤ 0.46°.
  - The ~3.5–4× margin is for what the two-state approximation omits: EKF3's flow→yaw coupling,
    and the wrong end-wall headings, which all pass the gate.
  - *(Was p95 ≤ 2°, maximum ≤ 4.5°.)*
- **B4.** 1 s-smoothed |GT lateral speed| during cruise **≤ 0.25 m/s**.
  - The yaw part is now ≤ 0.004 m/s. The band is set by about 2.5× EKF3's heading-free lateral
    velocity noise (~0.10 m/s rms, `rgs_check_tex`). *(Unchanged value; new yaw basis.)*
- **B5.** No oscillation: cruise gyro rms roll ≤ 0.05, pitch ≤ 0.0108, yaw ≤ 0.02 rad/s.
  *(Unchanged.)*

**DIAGNOSTIC predictions (written before flying):**
- **Heading acceptance:** `VISP` consumed = sent with quality ≥ 50 (about 97% of processed
  cruise frames on `fwdc_tex`, and about 96% on `fwdplainc_blank` up to y ≈ 144.5 m). EKF3's
  gate should pass almost all of them.
- **Confident-wrong end-wall headings fused:** **all that occur** (0–2 per `fwdc_tex` flight, 3–6
  per `fwdplainc_blank` flight). Their errors (3–17° in Phase 5) sit inside the ~15° 3σ gate,
  and those above ~15° are rejected.
  - The expected effect is a transient yaw error of well under 2° (B3), because each is one
    sample at R = (5°)² among many correct ones.

**Decision:**
- (b) passes if all three flights pass B1–B5.
- (c) runs only if (b) passes.
- Any B1 failure stops the set and is reported.

### `VISO_DELAY_MS` alongside optical flow: source analysis, and the ground-test verification (user request, 2026-09-29)

**Concern:** a user report (ArduPilot issue #20163; *not fetched here, no network use*) says
`VISO_DELAY_MS` had no effect with optical flow enabled.

**What the pinned source (`7bac20cbcc`) does:**
1. **Horizon.** At filter start (`setup_core`), EKF3 sizes its fusion horizon (the delayed-state
   buffer) from the MAXIMUM delay of all enabled sensors (`AP_NavEKF3_core.cpp:41-88`):
   - `EK3_HGT_DELAY` (default **60 ms**) and `EK3_FLOW_DELAY` (10 ms);
   - GPS/airspeed when used;
   - **`VISO_DELAY_MS` when VisualOdom is enabled** (`:79-85`, capped at 250 ms).

   Then `imu_buffer_length = maxDelay/12 + 1` (`:88`), and the ExtNav buffer is sized from the
   same horizon (`:104`).
2. **Dating.** Each ExtNav sample is dated
   `receipt_corrected − VISO_DELAY_MS − localFilterTimeStep/2` and clamped to be no older than the
   horizon (`AP_NavEKF3_Measurements.cpp:1101-1107`). **This is independent of the flow delay**,
   which dates flow samples separately (`:232-236`).
3. **Recall.** The yaw sample is recalled and fused when the delayed IMU time reaches it
   (`AP_NavEKF3_MagFusion.cpp:367`).
4. **Receipt time.** `receipt_corrected` is ArduPilot's jitter-corrected version of our capture
   timestamp: `offboard + min(local − offboard)`, re-estimated every few samples to follow clock
   drift (`AP_RTC/JitterCorrection.cpp`, `GCS_Common.cpp:7373-7387`). That is capture +
   minimum lag.

   So the fusion time is capture + min_lag − `VISO_DELAY_MS` − ½ step, which is **time-aligned
   when `VISO_DELAY_MS` = the minimum capture-to-receipt lag.**

**Ways the delay could have "no effect", at this commit:**
- **(i)** `VISO_DELAY_MS` exceeds the horizon from the other sensors while VisualOdom was
  disabled at filter start. Then it is not folded into the horizon, and the excess is clamped
  away by `MAX(timeStamp_ms, imuDataDelayed.time_ms)`.
- **(ii)** It is changed live after filter start, so the buffers are not resized.

**Neither applies here:**
- `VISO_TYPE 1` and `VISO_DELAY_MS` load from the parameter file at boot.
- The expected delay (~40–50 ms) is inside the 60 ms horizon that `EK3_HGT_DELAY` already sets.

This is to be **proven from the ground-test logs, not assumed.**

**SITL ground test** (after the batch and pipeline re-run; the vehicle does not take off):
- **Run.** `HEADING=1 GROUND_TEST=60 sim/tools/closed_loop_run.sh corridor_textured_fwdc gt_heading_<n>`.
  The `fly_trial.py` `GROUND_TEST` mode (held patch
  `~/thesis_data/batches/ground_test_fly_trial.patch`) arms, stays armed on the ground for 60 s of
  sim time, then disarms. It uses the final closed-loop settings (`closedloop.parm`,
  `closedloop_heading.parm`).
- **Run 1** measures the latency with the placeholder `VISO_DELAY_MS 10`. **Run 2** repeats with
  the measured value.
- **Pass criteria, fixed before the test:**
  - **G1, yaw-only ExtNav fusion.**
    - The EKF3 status shows ExtNav yaw in use (a "using external nav data" / yaw-alignment
      message; `XKF4.SS`).
    - `REPH` samples are present, with `angErr` = 0.05 rad (the clamp).
    - EKF3's `PN`/`PE` do not jump to the (0,0) placeholder or to its ±100 m error.
    - `EK3_SRC1_POSXY` = 0 in the PARM dump.
  - **G2, arming with the heading node.** It arms with no VisualOdom or EKF pre-arm failure, and
    the node's offset is locked before arming (node log). The node CSV records the offset.
  - **G3, EKF origin.** G1 and G2 pass without an origin ever being set (none is set in this
    configuration). If either fails for want of an origin, stop and report.
  - **G4, latency (run 1).** Minimum capture-to-receipt latency, from two independent measures:
    - (a) node CSV: `t_sim_sent − t_capture` (Gazebo sim clock), plus the loopback transport;
    - (b) dataflash `VISP`: `TimeUS − RemTimeUS`, with the SITL↔Gazebo clock offset from
      `eval/input_timing.clock_map`.

    **`VISO_DELAY_MS` = round(min latency)**, provided (a) and (b) agree within 5 ms. It must be
    ≤ the horizon (60 ms); if larger, stop and report.
  - **G5, the delay takes effect and the heading is time-aligned (run 2).**
    - Every `REPH.delay_ms` equals the set `VISO_DELAY_MS`, with flow fusion active in the same
      run (XKF5 flow innovations present).
    - EKF3's assigned measurement time, `REPH.timeStamp_ms − delay_ms − 6 ms` (half the 12 ms
      step), against the capture time mapped to the SITL clock: the median |difference|
      ≤ 6 ms and the p95 ≤ 12.5 ms (one EKF3 step, its own time resolution).
    - The horizon from the PARM dump (`max(HGT_DELAY, FLOW_DELAY, VISO_DELAY_MS)`) ≥
      `VISO_DELAY_MS`, so no clamping.
- **Report before flying.** Any failure stops before the closed-loop flights.

### Part 2 — evaluation windows for every band (recorded before flying; user request, 2026-09-29)

**The window is the PINNED dataset cruise window** (`eval/cruise_window.cruise_bounds`, METHODOLOGY
"Cruise window — pinned definition"): the largest contiguous run where the 0.42 s-smoothed GT
horizontal speed exceeds 0.30 m/s. On the forward-camera bags it spans **GT y ≈ 0.1 → 151 m**,
so **it INCLUDES the end-wall approach (y > 140 m)**. In a flight that the watcher stops, the
window ends where the speed criterion ends, or at the stop.

| band | window |
|---|---|
| (a) contact timing | "cruise +t" is measured from the pinned window's t0. The +187 s prediction came from the `rgs_check_tex` open-loop curve, whose start used the GT forward speed first > 0.3 m/s (25-sample smoothing); the two starts differ by < 1 s, which is stated. |
| B1 (completion, no wall contact) | **the whole flight**, arming to disarm (the watcher's \|x\| check runs throughout) |
| B2 (maximum cross-track) | pinned cruise window, **end-wall approach included** |
| B3 (yaw error p95 / max) | pinned cruise window, **end-wall approach included**; y ≤ 140 m and y > 140 m are also reported separately as a DIAGNOSTIC |
| B4 (lateral speed) | pinned cruise window, end-wall approach included |
| B5 (gyro rms) | the definition of its source band (`eval/rgs_profile.py`): cruise span with GT forward speed > 0.3 m/s (51-sample smoothing), **trimmed by 5 s at each end** |
| diagnostics (heading acceptance, confident-wrong fused) | pinned cruise window; "end wall" = GT y > 140 m inside it |

**Keeping the end-wall region in the yaw bands: the check.** The offline yaw prediction was
re-run on the pinned window and split at y = 140 m (`eval/cl_yaw_prediction.py`,
`eval/results/cl_yaw_prediction_5deg.json`; archived bags, n = 3 per world):

| world | whole window p95 / max | y ≤ 140 m max | **y > 140 m p95 / max** | end-wall rise over the value at 140 m | wrong end-wall headings fused |
|---|---|---|---|---|---|
| `fwdc_tex` | 0.25–0.29° / 0.29–0.39° | 0.29–0.38° | 0.20–0.25° / **0.23–0.28°** | +0.00…+0.08° | 0–2 (all that occur) |
| `fwdplainc_blank` | 0.26° / 0.34–0.43° | 0.26–0.27° | 0.30–0.41° / **0.34–0.43°** | +0.26…+0.34° | 3–6 (all that occur) |

- The predicted end-wall transients (fused wrong headings, plus the ~12 s dropout on
  plain-blank) peak at **0.43°**, against the **2.0° maximum band: a 1.57° margin (×4.6).**
- **Decision: the band holds, and the end-wall approach stays INSIDE B3's window.** The
  y > 140 m numbers are reported alongside as a diagnostic, so that an end-wall-driven failure
  can be told apart from a cruise-wide one.
- The same margin logic as before covers what the two-state model omits (EKF3's flow→yaw
  coupling).
- The B2/B3 predictions above supersede the earlier "prediction" figures (p95 ≤ 0.28°, max
  ≤ 0.46°), which used a slightly different window (GT speed > 0.3 with a 31-sample boxcar).
  The bands themselves are unchanged: B3 p95 ≤ 1.0° and max ≤ 2.0°, B2 ≤ 6.0 m, B4 ≤ 0.25 m/s.

### Consolidated re-fly — aborted attempt `p1c_fwdplainc_blank` (attempt 1), 2026-09-29

- **What happened.** Attempt 1 (started 14:40:06) completed its flight normally: armed, 300 s
  cruise, landed, "Trial flight complete". `run_trial.sh` then died in its post-flight step with
  `run_trial.sh: line 343: HEADING_SIGMA_DEG: unbound variable` (exit 1, 14:47:34).
- **Cause: a harness failure, unrelated to any estimator, the flight or the data.**
  - During that trial I edited `run_trial.sh` (the closed-loop `HEADING_BRIDGE` hook) while the
    batch was executing it.
  - The file was restored byte for byte about a minute later, but the running bash instance still
    read the edited text when it resumed after the flight.
  - The failing line is the hook's metadata `printf`, which exists only in the edited version.
- **Handling, under the runner's pre-declared rules** (`run_resumable_batch.sh`: a failed attempt
  is marked ABORTED, its folder is kept and renamed, and the trial is re-flown once):
  - the attempt was marked ABORTED and moved to `trials/p1c_fwdplainc_blank_ABORTED/`, **kept,
    never used**;
  - the trial was re-flown immediately as attempt 2 (14:47:34 → 14:55:37, COMPLETE).
- **Checked:** every completed re-fly trial, including the re-flown `p1c_fwdplainc_blank`,
  records `git_commit 7a90e81` (the committed harness) and contains no trace of the heading hook.
- **Standing rule (confirmed by the user):** no file a running batch uses is edited while it
  runs; changes are held as patches until the batch ends.

**Which trials the edit could have affected: evidence (user request, 2026-09-29).**

**1. The edit window: 14:45:40.96 → 14:45:57.56 AEST (16.6 s).**
- Start: the in-place edit was issued at `2026-09-29T04:45:40.961Z` (session transcript,
  tool call "Add HEADING_BRIDGE hook to run_trial").
- End: the restore, `git checkout -- run_trial.sh` (transcript `04:45:56.506Z`). The file mtime
  is **14:45:57.5645**, and the patch saved immediately before it is 14:45:57.5605.
- The file now matches the committed and batch-commit (`7a90e81`) content byte for byte
  (md5 `98d448f60e83` for all three).
- No other file a dataset trial uses changed after the batch began (14:02:40). The only files
  modified since are `run_trial.sh` (restored), and `closedloop_heading.parm`,
  `heading_bridge.py`, `heading_bridge_core.py`, `sim/tools/wall_watch.py` and
  `sim/tools/closed_loop_run.sh`, none of which a dataset trial invokes.
  `fly_trial.py` and every `.parm` in `run_trial.sh`'s defaults are untouched.

**2. Mechanism (why the restore did not save the running trial).**
- The edit rewrote the file IN PLACE (Python `open(p, "w")`), on the same inode the running
  `bash run_trial.sh` of `p1c_fwdplainc_blank` attempt 1 had open.
- `git checkout` then wrote a NEW file (a new inode), so that bash kept reading the edited old
  inode and hit `HEADING_SIGMA_DEG: unbound` after the flight.
- **Consequence:** only a `run_trial.sh` process already running during the window could see the
  edit. Each trial starts a fresh `run_trial.sh`, which opens the path, and so gets the
  committed file if it started after 14:45:57.56.

**3. Trial times (runner `trials.log`) against the window:**
- **Finished before the edit** (all ended ≤ 14:40:06, before 14:45:40.96):
  - `p1c_fwdc_tex` 14:02:40–14:10:05;
  - `p1c_fwdplainc_tex` 14:10:05–14:17:18;
  - `p1c_fwdc_trans` 14:17:18–14:24:29;
  - `p1c_fwdplainc_trans` 14:24:29–14:32:19;
  - `p1c_fwdc_blank` 14:32:20–14:40:06.
- **Overlapping the window: only `p1c_fwdplainc_blank` attempt 1** (14:40:06–14:47:34). It is
  ABORTED, and its log shows the hook's unbound variable and no exit-0 cleanup. **Not used, and
  already re-flown.**
- **Started after the restore:** the re-flown `p1c_fwdplainc_blank` (14:47:34–14:55:37) and every
  later trial, `dsn_tex_r1` (14:55:37) through `fwdc_trans_r3` (16:48:11–16:55:49), and all
  trials still to fly.

**4. Log evidence for every completed trial** (22 of 22):
- zero occurrences of `HEADING`, `heading_bridge`, `SERIAL1` or `unbound` in `run_trial.log`;
- a normal `Cleaning up (exit code 0)`;
- no `heading_bridge` block in `metadata.yaml`;
- `git_commit 7a90e81`.

The ABORTED attempt is the only log with a hook reference (1) and no exit-0 cleanup.

**Conclusion:** no completed dataset trial executed the edited script. **Nothing is marked for
re-flight.** The same log check is repeated on the remaining trials when the batch ends, before
the pipeline re-run uses any of them.

## Consolidated re-fly — post-batch checks (2026-09-29, before the pipeline re-run)

**Batch complete.** `rerun2_main` is 33/33 (18:14) and `rerun2_ds` is 9/9 (19:09). The only
abort is the recorded `p1c_fwdplainc_blank` attempt 1.
- **Harness log check on all 42 re-flown trials:** each has `git_commit 7a90e81`, a clean
  exit-0 cleanup, no heading-hook trace in `run_trial.log` or `metadata.yaml`, and no
  `SIDESTEP`. **0 anomalies.**
- `ds_*` record `EK3_SRC1_YAW 1` / `COMPASS_USE 1` with `compass_active.parm`; `dsn_*`,
  `fwdc_*` and `fwdplainc_*` record 0 / 0.

**EKF3 flow latency (DIAGNOSTIC).** Tool: `eval/input_timing.py` → `rerun_latency_check.py`;
`eval/results/{input_timing_rerun_all,rerun_latency_check}.json`. The band is the pre-registered
P2 (same-world OLD `dsn` mean + 12.5 ms; matched ≥ min − 5 pp): textured median ≤ 28.1 / p95
≤ 36.7 ms, transition ≤ 30.4 / 38.2, blank ≤ 29.9 / 38.2.
- **Flagged trials, both IN BAND:**
  - `dsn_trans_r1` (RTF 0.956): median 20.6 ms, p95 30.8 ms, 100% matched;
  - `dsn_trans_r2` (RTF 0.931): 27.6 / 36.9 ms, 100%.
- **Outside band (just):**
  - `ds_tex_r1`: p95 37.7 against 36.7;
  - `fwdc_tex_r3`: median 28.9 against 28.1, p95 37.7 against 36.7.

  Both are diagnostic only.
- **All other textured and transition trials are in band.**
- **Blank floor (14 trials): P2 is UNDEFINED.** No cruise frame is flow_tracker-`valid`, so there
  is nothing to match; the tool previously crashed on this and now reports it explicitly.
- A second, labelled column (the latency over quality > 0 frames) is added. It is identical to
  the `valid` column wherever frames exist.

### FINDING — the roll-gain correction changes the blank-floor flow condition (all blank data)

Cruise-window flow statistics, re-flown against the pre-re-run bags of the same names (all 42
pairs; `eval/flow_quality.py` definitions plus the cruise `valid` share):

| floor | `valid` share (flow_tracker, ≥ 20 tracked features) | inlier mean | % inlier < 0.5 | features | `flow_y_raw` |
|---|---|---|---|---|---|
| **blank** (15 bags) | **8.4–9.1% → 0.0%** | 0.31 → 0.24 | 84% → 99.7% | 8.0 → 5.8 | −0.6…−4.5 → **−9.9…−13.5 px/s** |
| transition (12) | 56–57% → 52–53% | 0.665 → 0.634 | 39.5% → 46.5% | 31.7 → 30.5 | ~71.5 → ~66.3 px/s |
| textured (15) | 98.7% → 98.7% | 0.973 → 0.983 | 0 → 0 | 52.8 → 52.5 | ~136 → ~134 px/s (−1.5%) |

- **Mechanism.** `flow_tracker` marks a frame valid only if ≥ 20 features are tracked
  (`min_valid_features`, `flow_tracker.py:27,313`). The old 17.5 Hz roll oscillation shook the
  camera over the featureless floor, and about 9% of frames reached 20 tracked features. With a
  steady camera, no cruise frame does.
- **Consequence 1, EKF3.** `flow_bridge.py:123` forwards only `valid` frames, so **on the re-flown
  blank floor EKF3 receives NO optical flow during cruise.** `dsn_blank_r1`: 701 `OF` records,
  all outside cruise, against 1,196 before.
- **Consequence 2, UKF/FGO.** Their flow update also requires `valid` (`ukf_core.update_flow`),
  so **all three estimators get no flow on the blank floor.** The blank condition changes from
  "sparse flow, ~9% of frames" to **"no flow"**, identically for all three. The same holds for
  the blank half of the transition world.
- **Assessment.** The old blank-floor flow was partly produced by the simulation artefact the
  correction removes, so the new condition is the physically consistent one.
- **But this changes the meaning of the blank condition**, and every blank result (failure
  metrics, onset, blank-world bands and references) will change. Some are likely to change
  direction.
- **No parameter was changed** (`min_valid_features` stays 20, the frozen flow-tracker setting).
- **Reported to the user before the pipeline re-run uses these bags.**

### Part 4 — shadow UKF builds in SITL

`~/ardupilot_ukf` (branch `ukf-port`, from `7bac20cbcc`) builds `bin/arducopter` with
`AP_NavUKF` (`waf copter`, exit 0) after two compile fixes: a non-const `AP::dal()` reference and
`is_equal` for the float comparison. **Running it in shadow is a SITL run, so it waits until
after the pipeline.**

### Rulings (user, 2026-09-29) after the post-batch checks

1. **The pipeline re-run proceeds, with the blank floor as a "no flow" condition for all three
   estimators.** `min_valid_features` stays frozen at 20, and there are no parameter changes
   beyond the listed corrections.
   - The old sparse blank-floor flow (~9% valid frames) was partly produced by the removed
     17.5 Hz roll oscillation. With a steady camera the tracker finds no valid frames, which is
     **the physically consistent behaviour of a flow sensor over a featureless floor.**
   - **The old blank results are SUPERSEDED as dependent on a simulation artefact.**
2. **Blank-floor results (and the blank half of the transition world) are reported as behaviour
   under total loss of flow aiding, not as accuracy rankings.** For each estimator, the report
   covers what it does when flow disappears:
   - EKF3's aiding-mode changes and position-validity flags (`XKF4.SS`);
   - the UKF/FGO dead-reckoning growth.

   The old-vs-new direction flags are reported as planned. **OI-1 (the FGO blank-floor freeze)
   is reviewed against the new behaviour.**
3. **Latency:** `ds_tex_r1` and `fwdc_tex_r3` are recorded as marginally out of band (diagnostic
   only; no action). **Latency is undefined on the blank-floor trials because no flow is fused.**
   `eval/phase2_score.py` now reports P2 as "undefined (no flow fused)" there, instead of failing.
4. **Closed-loop plan change: set (c) is DROPPED as a "flying well" test** (EKF3 with the camera
   heading, plain walls over the blank floor).
   - With no flow, EKF3 has no velocity aiding.
   - **No plain-wall world provides both valid flow and valid heading:** the blank floor gives no
     flow, and on the checkerboard floor the plain-wall heading fails Phase 3 validation.
   - **The week's "flying well" goal is sets (a) and (b), on textured walls.**
   - A plain-wall closed-loop flight may be flown later only as a **pre-registered failure
     demonstration** (the failsafe or failure mode predicted first), and not without the
     user's ruling.
5. **Order:** the pipeline re-run → the shadow UKF SITL run → the ground test → closed-loop sets
   (a) and (b).

### Loss-of-flow analysis — flow-loss point defined BEFORE the analysis runs (user request, 2026-09-29)

**Definition** (`eval/blank_behaviour.py`; one rule for all three estimators):
- **Airborne:** GT base_link height (`/ground_truth/pose` z) > 0.5 m. Rest is 0.195 m.
- **Take-off time:** the first time GT z > 0.5 m.
- **Flow-loss point `t_loss`:** the time of the **last flow_tracker-`valid` frame received while
  airborne, at any time up to the end of cruise**. If **no** valid frame occurs while airborne,
  `t_loss` = take-off, and the trial is marked **"flow never valid airborne"**.
- **Case labels per trial:**
  - **A:** flow valid airborne, lost before cruise start (during the climb or hover);
  - **B:** lost inside the cruise window (e.g. the transition boundary);
  - **C:** never valid airborne (`t_loss` = take-off).
- **"Flow fused airborne", reported per trial:**
  - (i) the number of valid frames while airborne. These are what the UKF and FGO can fuse
    (their update requires `valid`), subject to their gates.
  - (ii) the number of EKF3 dataflash `OF` records while airborne. These are what reached EKF3,
    since `flow_bridge.py` forwards only valid frames.
- **Same rule for all estimators.** EKF3's own clock (`TimeUS`) is mapped by the per-trial
  cruise-start offset (tens of ms, negligible at these timescales).
- **Error growth** is measured with each estimate re-referenced to GT at `t_loss`, at
  `t_loss` + 10/30/60/120 s and at the end of cruise.

**Flow-loss cases, per trial** (computed from the bags and dataflash BEFORE the loss-of-flow
analysis runs; the same numbers come from `eval/blank_behaviour.py`):

| world | trials | case | `t_loss` − cruise start | GT y at loss | valid frames airborne | EKF3 `OF` records airborne | flow fused airborne? |
|---|---|---|---|---|---|---|---|
| transition | all 14 (`dsn`, `ds`, `fwdc`, `fwdplainc`, `p1c`) | **B** | **+161.05 … +161.09 s** | **80.5–80.6 m** (the boundary) | 4,858–4,874 (textured half) | 4,859–4,879 | yes, until the boundary |
| blank | 13 of 14 (listed below) | **A** | **−0.30 … −1.43 s** (during the climb) | 0.0 m | **1–4** (take-off only) | 1–7 | **only a few take-off frames; none in cruise** |
| blank | `ds_blank_r2` | **C** | take-off (−1.84 s) | 0.0 m | **0** (never valid airborne) | 3 | only arrivals of frames captured just before take-off |

- **Blank, case A:** `ds_blank_r1`, `ds_blank_r3`, `dsn_blank_r1..r3`, `fwdc_blank_r1..r3`,
  `fwdplainc_blank_r1..r3`, `p1c_fwdc_blank`, `p1c_fwdplainc_blank`. **Case C:** `ds_blank_r2`.
- **Airborne `OF` records slightly exceed the airborne valid frames** (for example 3 against 0 on
  `ds_blank_r2`). This is expected: `OF` is stamped on arrival at ArduPilot, ~20 ms after capture,
  so frames captured just below 0.5 m arrive after the vehicle passes 0.5 m.
- **In every blank trial, flow is effectively absent for the whole flight:** at most 7 samples at
  take-off, and zero in cruise. The analysis therefore measures from `t_loss`, a second or two
  before cruise starts, which is equivalent to "from take-off" to within 2 s.

### Rulings on the early pipeline results (user, 2026-09-29)

**1. EKF3's displacement ratio of 0.00 on blank and transition is a SCORING ARTEFACT (established
from the logs before any interpretation).**
- **`dsn_trans_r1`.** EKF3 aids normally up to the boundary (PN 74.5 m at t = 180 s,
  `horiz_pos_rel` = 1).
  - At **t = 196.1 s** it logs "EKF3 IMU0/IMU1 stopped aiding".
  - From then on `XKF1` PN/PE are **exactly 0.00 / 0.00 (the origin)**, with `XKF4.SS`
    `const_pos_mode` = 1, `horiz_pos_rel` = 0, `pred_horiz_pos_rel` = 0 and `horiz_pos_abs` = 0.
    **EKF3 itself flags its position invalid.**
  - "Started relative aiding" returns only at t = 344.6 s, after landing.
- **`dsn_blank_r1`.** The same from **t = 34.2 s** (just after take-off) to landing.
- **Velocity.** Throughout, `horiz_vel` stays 1 while `XKF1` VN drifts to about −0.2 m/s: the
  velocity is flagged valid but is wrong. This is reported, not scored.
- **The 0.00 ratio is therefore EKF3's invalid output, the origin, scored as a position.**
- **EVALUATION RULE (recorded before any blank/transition interpretation):** an estimate that the
  estimator itself flags as invalid is not scored as a position estimate.
  - For EKF3, invalid means `horiz_pos_rel` = `pred_horiz_pos_rel` = `horiz_pos_abs` = 0.
  - **The invalid period (start relative to the flow-loss point, and duration) is reported
    instead.**
  - EKF3 position metrics on blank and transition use only its valid period.
- **The UKF and FGO have no validity flag.** Their unbounded dead-reckoning growth is reported as
  it is (ratios 47–197× on the re-flown blank and transition). **The asymmetry is stated plainly in
  the blank-floor behaviour section:** EKF3 "fails safe" by declaring its position invalid, while
  the UKF and FGO keep outputting a diverging position with no flag.

**2. `fwdc_tex_r2`: recorded as a PRIMARY MISS as worded, not re-scored.**
- EKF3 evo -a (cruise) was 3.603 m against the band floor of 3.613 m.
- The two-sided band ([3.613, 4.34] m, from the new `dsn` EKF3 n = 3 range of 0.24 m) is narrower
  than the n = 3 variability justifies. A 0.01 m deviation in the *better* direction changes no
  conclusion. It does not stop the pipeline.

**3. Blank-floor P4 misses (`fwdc_blank_r1..r3`: FGO ratio, and onset for r1/r2;
`fwdplainc_blank_r2`: FGO ratio): recorded as misses as worded, not re-scored.**
- **Context:** under the no-flow condition, the FGO displacement-ratio and onset bands measure the
  size of an unbounded inertial runaway (`dsn` blank ratios 182–197), not the downward sensing
  condition they were built to check.
- **Post-hoc condition check (clearly labelled POST HOC):** valid airborne flow frames in cruise are
  **zero in all 3 `dsn` blank and all 8 forward-camera blank trials** (and in the 3 `ds` blank
  trials) (flow-loss table above). The sensing condition matches exactly; only the runaway size
  differs.

**4. UKF `dsn_tex_r1` (evo -a (cruise) 17.45 m) is recorded as a remaining instability case.**
The same bag was 16.98 m before the corrections, while r2/r3 improved to 2.28 / 4.30 m. **Not
investigated now.**

## Part 4 — the UKF drop-in's health and validity (user ruling, 2026-09-29)

**Requirement:** before the UKF ever flies, it must report health and position/velocity validity
through the same `AP_AHRS` interface EKF3 uses (Part C §1.3), with an explicit rule for declaring
position invalid, tested in shadow on a blank-floor replay. **There are no changes to the offline
UKF used in the comparison.**

**Implementation (`~/ardupilot_ukf`, branch `ukf-port`, `AP_NavUKF`):**
- `healthy()` and `getFilterStatus(nav_filter_status&)`, with the **same signatures and the same
  `nav_filter_status` union** that `NavEKF3` exposes to `AP_AHRS` (`AP_NavEKF/AP_Nav_Common.h`).
- `AP_AHRS` selection wiring (Part C's per-type switch arms) is the next Part 4 step. Until then
  the flags are logged: `XUKS.SS` and `H` in SITL, and `ukf_shadow.csv` in Replay.
- It switched to DAL time (`dal.millis()`), so SITL and Replay behave identically.

**VALIDITY RULE** (horizontal velocity, relative horizontal position, and the predicted relative
position):
- **Invalid when either:**
  - **(a)** no flow update has been accepted (either axis) for more than **5000 ms**. That is
    **EKF3's own relative-aiding timeout** (`flowFusionTimeout`, `AP_NavEKF3_Control.cpp:306`),
    which moves EKF3 to AID_NONE and constant-position mode;
  - **or (b)** the horizontal-velocity 1σ `√(P_vN + P_vE)` exceeds **0.5 m/s**, the cruise
    speed: an estimate less certain than the speed it navigates at.
- **Valid again** at the next accepted flow update, with (b) satisfied.
- `vert_pos` / `vert_vel`: a rangefinder update accepted within 5000 ms.
- `healthy()` requires initialisation and finite state and covariance.
- **Unlike EKF3, the UKF has no constant-position fallback.** When invalid it keeps outputting its
  inertial estimate, flagged invalid, and `const_pos_mode` is always false. `dead_reckoning` is
  set while still valid but with no flow accepted for more than 1 s.

**Shadow test in ArduPilot Replay on the re-flown logs** (`LOG_REPLAY=1`):
- **Method.** The Replay tool is built from `ukf-port`. Two replay-only `AP_DAL` hooks (null in
  every vehicle build) run the UKF on exactly the DAL frames and flow records EKF3 receives. The
  check is `eval/ukf_shadow_replay_check.py`, with outputs in `eval/results/ukf_shadow_replay/`.
- **A port bug found by the textured control and fixed.** Range was sampled only on a changed
  value, but MAVLink `DISTANCE_SENSOR` is integer cm, so steady-hover readings repeat. Only 152
  range updates in 300 s were fused, height stuck at its on-ground value, and flow was mis-scaled
  about 20×. Range is now sampled at 30 Hz while its status is Good: 9,813–9,815 range updates
  per flight.
- **Replay logging note.** Replay's logger did not emit FMT records for the UKF's dynamically named
  messages. In Replay mode the UKF therefore also writes a CSV. Dataflash logging is kept for SITL
  and is checked in the SITL shadow run.

| log | healthy | `horiz_pos_rel` valid (cruise) | validity change | position error vs GT at cruise end (along / cross) |
|---|---|---|---|---|
| **`dsn_blank_r1`** (no flow) | 100% | **0.6%** | **invalid at cruise +1.95 s** (flow age 3.2 s, σ_vh 0.506 m/s: rule (b) fired before the 5 s timeout); **never valid again** | −17.1 km / +15.2 km, **flagged invalid throughout** |
| `dsn_tex_r2` (control) | 100% | 100% | none | −29.7 m / **+66.2 m** (σ_vh 0.16–0.17 m/s) |
| `dsn_tex_r1` (control; the known UKF instability bag) | 100% | 100% | none | −142.5 m / +99.4 m |

**Findings (stated plainly):**
1. **The rule does what it is for on loss of aiding.** On the blank floor the UKF declares its
   position invalid within 2 s of cruise start, and keeps it invalid while its estimate runs away.
   That is the equivalent of EKF3's "stopped aiding", reached through the same status interface.
2. **Validity is not accuracy.** On the textured controls, the port stays valid and confident
   (σ_vh 0.16 m/s) while its position wanders 66–99 m cross-track: a heading drift that no
   velocity-covariance rule catches. EKF3 has the same property in its own nomag configuration.
3. **The port is not yet equivalent to the offline UKF.** On `dsn_tex_r2` the offline UKF ends
   about 146 m along and 1.5 m cross (GT 151 m), against the port's ~120 m along and 66 m cross.
   Likely contributors, not yet tested:
   - EKF3's arrival-window AHRS gyro pairing for flow, against the offline UKF's co-sampled
     frame-interval average;
   - fusion at arrival with no delayed-state buffer;
   - the INS delta inputs.

   On `dsn_tex_r1` both wander ~98 m sideways (the recorded instability case).
- **Consequence:** the UKF port **does not fly** until it has been validated against the offline
  UKF on replayed logs, with a pre-registered agreement criterion. That validation is the next
  Part 4 step, together with the `AP_AHRS` selection wiring.
