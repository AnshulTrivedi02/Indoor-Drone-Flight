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

**Corrected `h_flow` (interval-averaged ω, 2026-08-01) — re-run across all nine bags.**
The correction splits the conditions into **two regimes that must be reported separately**:
only **textured** is a tracking regime where evo −a means accuracy; **transition and blank
are failure regimes** where all three estimators diverge and evo −a is *not* a quality metric
(UKF blank 14.4 < EKF3 34.8, evo -a (cruise) — full-window, historical, 16 < 38 — is "diverges *less far*
after alignment," not a quality win). The old
"formulation differences wash out under degraded sensing" is restated as: **all three fail
under flow starvation, by different failure modes.**

**(1) Textured — the tracking-regime quality comparison.** Metric: **evo -a
(cruise)**, RMSE in m, from `eval/three_way_eval.py`. This is the only cross-estimator
ranking that holds.

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
`CustomFactor`, FGO_DESIGN §6). Step-time scales ~O(window): **96 / 48 / 27 ms** at
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
3. **Attribution is a REAL decomposition, not double-counting.** ~**74%** of the
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

## Forward-camera workstream (branch `fwd-camera`) — hypothesis, sensor, worlds, Phase 1 pre-registration (2026-09-24)

### Hypothesis (stated before any forward-camera result exists)

With no compass, absolute yaw is unobservable. On `dsn_tex_r3`, **74%** of EKF3's
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

## PRE-REGISTRATION RULE (standing, from 2026-09-24)

Two errors in one phase (the ground-truth pose-rate band and the IMU gap-share band)
came from one habit: bands taken from the bare observed range with zero margin, and
diagnostic metrics used as pass/fail gates. From now on:

1. **Each criterion is labelled PRIMARY** (it tests the confound directly) **or
   DIAGNOSTIC** (reported, never a gate).
2. **No band uses the bare observed range.** Each states its margin and the basis for
   it: a physical tolerance, or the n=3 range widened by a stated factor. It also says
   why a value outside the band would indicate the confound.
3. **Only primary criteria can stop a phase.**

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
- **The Phase 1 flow→EKF3 latency figures above used a single whole-flight offset**,
  which smeared each distribution by about ±25 ms. That produced the spurious "negative
  p5" and the "transition medians up to 32 ms". They are **superseded** by the
  linear-map values below (`eval/results/input_timing_linmap.json`). The distributions
  are now positive (p5 ≥ 8 ms) and about 15 ms wide.
- **Did not work (recorded):** the first linear-map run silently reused the name `t1`
  for both the clock-fit anchor and the cruise-window end. That cropped the latency
  statistics to the first ~300 frames and produced a spurious P2 failure for
  `p1_fwd_trans`. It was caught by the valid-frame count (≈ 300 against ≈ 9000),
  fixed, and re-run before anything was concluded.

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

## OI-2 result — IMU sensor time vs receipt time (offline, 2026-09-24; awaiting ruling)

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
