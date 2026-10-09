# Plain-wall FGO yaw divergence: offline trace (ruling 2026-10-10, item 1)

Stage agent, worktree branch `worktree-agent-a375613081292d466`, based on `fwd-camera` `ef7a0a5`.
Time box 3 h (user). Offline only: no simulator, no flight.

**What this stage did not do:**
- It changed no estimator core, harness, METHODOLOGY.md, numbers.md or comparison script.
- It wrote nothing into any trial directory. Outputs went to scratch (`FGO_OUT_ROOT` / `UKF_OUT_ROOT`).
  - The bags are packed (`bag_0.db3.zst`), so scratch COPIES were unpacked and read via `FGO_BAG_ROOT`.
  - `ukf_replay.py` has no bag-root knob. A scratch copy with a two-line patch was used
    (`eval/diag/plainwall_trace/ukf_replay_scratch.diff`: one `sys.path` line, one `UKF_BAG_ROOT` line). The UKF
    core is untouched.
- Every replay ran through `heavy.py` (3 steps).

## Verdict in one line

**GENUINE INCONSISTENCY (D18-type): the FGO's X(0) yaw prior σ is 1e-3 rad (0.057°), against the UKF's 1° and
EKF3's 0.1 rad (5.7°).**
- It is documented as a "gauge fix" (FGO_DESIGN §8 table). That justification holds only while nothing observes
  absolute heading.
- In the heading arms the camera heading observes it. The prior then becomes a substantive claim, 17× tighter than
  the UKF's.
- **With the UKF's 1°, the FGO matches the UKF in yaw and gyro-z bias on every plain-wall bag** (yaw max within
  0.02°, bgz within 0.1 deg/min). In position it matches on the textured floor. On the transition floor it falls
  back to the FGO's own no-heading blank-half failure (§3).
- **With the FGO's 1e-3 rad, the UKF diverges exactly as the FGO does.**
- Hard gating is what *sustains* the failure (lockout), but the *trigger* is the prior.

**Proposed correction (for the user to rule on; NOT applied):**
- Set the X(0) yaw prior σ to `np.radians(1)` in both cores:
  - `src/estimators/fgo/fgo_core.py:114` (`pose_sig[2]`);
  - `src/estimators/fgo_cpp/src/fgo_core.cpp:75` and `:200`.
- The alternative target is EKF3's 0.1 rad. **The UKF's 1° is not EKF3-sourced** (`ukf_core.init_state`). EKF3's
  `CovarianceInit` uses `rot_vec_var = sq(0.1)` per axis (`AP_NavEKF3_core.cpp:579-584`).
- Secondary, NOT demonstrated: roll/pitch are 2° (FGO), 5° (UKF) and 5.7° (EKF3).

## 1. Mechanism (stored Phase 4 outputs + `FGO_DUMP_EVENTS` re-run of `fwdplainc_tex_r1`)

**1. The headings start ON THE GROUND.**
- On the plain-wall textured and transition bags, valid headings begin at 9.8–13.3 s, 0–3 s after init.
- GT take-off is at 27.9–28.5 s. So there are about 15–18 s of ground headings.
- **On the ground, the camera reads about +3° off truth.** At the first heading, NIS is 358 with predicted σ
  0.162°, so |ν| = 3.07°. The UKF, after its first acceptance, sits at +2.7…+2.9°.
- This is Phase 3's known failure: plain walls over the checker floor.
- `fwdplainc_blank` has no valid heading until 28 s (airborne). `fwdc` ground headings agree with truth: first NIS
  0.06, error ≤ 0.06°.

**2. The predicted yaw σ differs 6× at the first heading.**

| | first heading σ_pred | growth |
|---|---|---|
| UKF | 1.01° | its 1° initial P |
| FGO | 0.162° | +0.075° per frame (≈ 2.3 °/s) |

- The FGO's 0.162° is the 0.057° prior plus the bias spread.
- Its growth of about 2.3 °/s is the 2.5 °/s B(0) gyro-bias prior times elapsed time. **All of the FGO's yaw
  spread is carried by the gyro-z bias.**
- The yaw-cap gate never fires on the ground: 109 checks, trace max 0.0052 against 0.04 (`a5.txt`).

**3. The first acceptance goes into the bias, not into yaw.**
- The FGO rejects the first 3–7 headings. It accepts the first heading whose NIS falls below 9 (7.13 on tex_r1).
- Per-keyframe dump, `fwdplainc_tex_r1` (`a5.txt`):

| t (s) | bgz (°/s) | yaw err (°) | heading NIS | accepted |
|---|---|---|---|---|
| 9.880 | 0.000 | −0.001 | 93.6 | no |
| **9.913** | **−6.149** | +0.862 | 7.13 | **yes** |
| 9.947 | −5.214 | +0.909 | 1.92 | yes |
| 10.147 | −4.240 | +1.607 | 2.76 | yes |
| 10.380 | −4.778 | +2.896 | 1.11 | yes |
| 12 / 60 / 200 | −4.78 / −4.75 / −5.37 | +10.7 / +237 / +994 | — | — |

- **One accepted heading moves the gyro-z bias from 0 to −6.1 °/s.** That is 2.5σ of the 2.5 °/s B(0) prior.
- In the next 0.5 s the bias settles at −4.8 °/s (−287 deg/min), against a true +8.9 deg/min (0.15 °/s).
- **The bias does NOT drift before lockout.** Yaw error is 0.000 until the first acceptance, and the jump is
  immediate.
- The UKF puts the same residual into yaw. Its yaw P is about 8× the bias-induced spread. It stays at +2.8° with
  a flat slope (+0.009 °/s).

**4. Lockout follows within 0.5 s and is permanent.**
- After about 10.4 s, yaw runs at 4.1–8.0 °/s (`a2.txt`, all 6 bags) and every heading is gated out. The 5 s median
  NIS is 330–500 by t = 12–40 s, and up to 1e4 later.
- Nothing else observes gyro-z bias:
  - the bias random walk is 1e-4 rad/s/√s;
  - downward flow carries no yaw rate;
  - the yaw cap is zero-innovation.
- **The 19–28 "fused" headings are wrap-throughs, not re-acquisitions** (`a3.txt`):
  - after the initial burst they come in clusters every 45–80 s, which equals 360°/slope (e.g. tex_r1: 66.9 s
    against 360/5.38);
  - the yaw error mod 360 at those acceptances is within ±9° (most within ±0.5°).
  - This is also why F1/F4 FGO_hard shows yaw max ≈ 180°: the wrapped error spans the full circle.

**5. Why it appeared only after the corrected re-run (supported by stored data).**
- Before the `setBiasAccOmegaInit = 0` correction, the extra IMU white noise (gyro about 26× looser) let yaw spread
  grow through the IMU factor itself. The ground-heading conflict was absorbed by yaw, not by bias.
- Stored pre-correction Phase 4 (`eval/results_pre_final`): tex FGO fused 4634–4981 of about 6.2–6.3 k headings,
  median NIS 0.1–0.2, bgz −4.7…−5.0 deg/min.
- With the IMU now EKF3-tight, the bias is the only cheap route. The 1e-3 rad prior that was harmless before is
  now decisive.

## 2. The FGO's and the UKF's yaw uncertainty on the same bags

- **At the first heading:** FGO 0.162° against UKF 1.01° on all 6 plain-wall tex/trans bags.
- **During lockout,** the FGO's σ_pred is small, so the innovation is enormous:
  - t = 100 s: 0.89° against an error of 468°;
  - t = 200 s: 2.3° against 994°.
- **The UKF** is at 0.05–0.5° and fuses intermittently (752 of 6,377 on tex_r1), with the measurement itself off
  by up to about 2–3°.
- **On fwdplainc_blank,** both are 0.049° while fusing more than 99 % (`a1.py` output).

## 3. Diagnostic demonstration (scratch; off-by-default knobs only)

Knobs:
- **FGO:** the existing `F_TAG=y0s1 F_YAW0_DEG=0 F_YAW0_SIGMA_DEG=1`. The string "0" is truthy, so σ is applied with
  zero offset.
- **UKF (the discriminator):** `F_TAG=y0t F_YAW0_DEG=0 F_YAW0_SIGMA_DEG=0.0572958`.

Metrics:
- evo -a (cruise) uses `three_way_eval`'s own `evo_ape_a`/`crop`/`write_tum` and the stored pinned window.
- The yaw error is `phase4_eval`'s.
- **Reproduction check:** the unmodified scratch re-runs equal the stored outputs exactly (FGO 43.54 m; UKF 0.19 m).

Full table: `eval/diag/plainwall_trace/results/a4.txt`.

| bag | FGO as run: evo / yaw max / bgz / fused | **FGO yaw0 σ 1°** | UKF as run | **UKF yaw0 σ 1e-3 rad** |
|---|---|---|---|---|
| plainc tex_r1 | 43.54 m / 1718° / −319 / 28 | **0.15 m / 5.03° / −8.0 / 747** | 0.19 / 5.04° / −8.0 / 752 | **42.99 m / 1809° / −335 / 21** |
| plainc tex_r2 | 42.65 / 1508° / −284 / 21 | **0.09 / 4.92° / −8.4 / 653** | 0.15 / 4.94° / −8.4 / 653 | – |
| plainc tex_r3 | 43.13 / 1421° / −267 / 21 | **0.22 / 4.59° / −7.6 / 778** | 0.25 / 4.59° / −7.6 / 781 | – |
| plainc trans_r1 | 36.93 / 2469° / +447 / 19 | **656 / 3.91° / −7.7 / 5911** | 119 / 3.92° / −7.7 / 5968 | **30.04 / 2745° / +499 / 22** |
| plainc trans_r2 | 55.29 / 1972° / −372 / 26 | **732 / 6.24° / −7.8 / 3582** | 123 / 6.25° / −7.8 / 3612 | – |
| plainc trans_r3 | 37.42 / 2541° / −480 / 20 | **560 / 4.16° / −7.7 / 5471** | 119 / 4.16° / −7.6 / 5517 | – |
| plainc blank_r1 (control) | 8809 / 0.65° / −8.3 / 8631 | 8596 / 0.45° / −8.3 / 8631 | 10561 / 0.45° / −8.3 / 8716 | – |
| fwdc tex_r1 (control) | 0.06 / 0.40° / −8.2 / 9184 | **0.06 / 0.40° / −8.2 / 9184 (unchanged)** | 0.13 / 0.40° / −8.2 / 9274 | – |

bgz is in deg/min; the true value is +8.9 (the sign convention as in the Phase 4 table, where −8 is correct).

**Reading:**
- **The behaviour follows the prior value, not the estimator.** It is symmetric: with the FGO's prior the UKF
  diverges (bias −335 / +499 deg/min). With the UKF's prior the FGO matches the UKF to ≤ 0.02° in yaw max on every
  plain-wall bag.
- **Transition evo (560–730 m) is NOT yaw.** Yaw is fine (1.6–3.7° rms, as the UKF's).
  - It is the FGO's own no-heading blank-half position failure: the stored FGO **baseline** arm on the same bags is
    726 / 557 / 584 m, against y0s1 656 / 732 / 560 m. The UKF baseline is 138 / 130 / 135 m and EKF3 41 m.
  - These are the "cite the order of magnitude only" rows. The FGO-vs-UKF trans position gap is a baseline
    property, not something the heading or the prior introduces. Pre-correction FGO trans was about 1,060 m. Do not
  read it as a regression from the 37–55 m "diverged" values: those were evaluated on a spinning trajectory.
- **The controls are unaffected:** fwdc_tex_r1 is identical, and blank yaw max is 0.65 → 0.45°.
- **NOT run:** the no-heading baseline arm with the new prior, and the C++ core. The baseline yaw is gauge-free, but
  the cap gate trace includes the yaw variance (+3e-4 rad² at init against the 0.04 gate). It should be checked if
  the correction is ruled in.

## 3a. Consistency with the 2026-10-01 ruling ("the yaw-prior hypothesis was rejected")

That ruling concerns a **different object**: the per-keyframe 0.5 rad zero-innovation yaw CAP.
- METHODOLOGY "EXPLORATORY … C0/F2 pattern", Hypothesis 1, was tested with `F_NO_YAWCAP` on `fwdc_tex_r1`.
- That was under the pre-correction IMU noise, on textured walls, where ground headings agree with truth.

This stage concerns the **X(0) initial yaw σ**.
- It matters only when the first headings disagree with the initial yaw by several σ_pred. That happens on plain
  walls over the checker floor, about +3° on the ground.
- It became decisive only after the `biasAccOmegaInit` correction removed the white-noise route (§1.5).
- **No contradiction:** fwdc_tex_r1 is unchanged under the 1° prior to the printed precision (evo, yaw, bgz, fused count) (§3).

## 4. Answers to the ruling's questions

1. **Gate decisions against innovations.**
   - The first 3–7 ground headings are rejected (NIS 38–870). One or two are then accepted at NIS 2–7.
   - Lockout is within 0.1–0.5 s, with NIS in the hundreds to 1e4.
   - The later accepts are wrap-throughs only.
2. **Heading uncertainty, FGO against UKF.** 0.16° against 1.0° at the first heading. The FGO's spread is entirely
   bias-borne.
3. **Lockout?**
   - **Yes, but it is secondary.** The first rejection streak starts at the first heading (9.81 s, before any
     acceptance) and is caused by the tight prior against a +3° measurement error.
   - The lockout proper (correct-ish headings rejected as yaw drifts) starts within 0.5 s of the first acceptance.
   - **What drives the drift is the bias jump at the first acceptance.** There is no bias drift before it (bgz
     exactly 0.000 until 9.913 s).
   - **Not the yaw-cap gate:** it never fires on the ground.
   - **Not a bias/yaw split poorly constrained by the IMU noise as such.** The split is set by the initial yaw prior
     relative to the B(0) bias prior. The tighter IMU only removed the white-noise route that used to mask it.
4. **Decision: genuine inconsistency** (a mismatched initial-yaw prior between the FGO and the UKF/EKF3, which
   becomes load-bearing whenever absolute heading is observed).
   - Report the hard gate as the amplifier: once the bias is wrong, the hard gate locks out, and the robust (Cauchy)
     arm escapes.
   - **If the correction is ruled out,** the plain-wall rows should be reported as "FGO with a gauge-tight initial
     yaw prior + hard gate", not as a property of hard gating alone. The UKF with the same prior fails identically.

## 5. If the correction is ruled in (not done here)

- Change both cores (Python and C++), and the `lc_fgo_replay` "thesis gauge" line if it is meant to match.
- Re-run every FGO arm that touches heading or yaw (Phase 4 both datasets, F1–F4, P5b, T/O re-anchors).
- Also re-run the baseline arm, to confirm the cap-gate change is negligible.
- Re-score bands A/B/C and the equivalence work, because the C++ X(0) prior changes.
- The UKF and EKF3 are untouched.

## Files

- `eval/diag/plainwall_trace/`:
  - `a1.py`–`a5.py` (the analyses);
  - `fig.py`;
  - `run1.sh`, `run2.sh`, `unpack.sh`, `watch.sh` (heavy steps and wait loop);
  - `ukf_replay_scratch.diff`;
  - `results/` (`a2`–`a5` txt/json).
- `plots/plainwall_trace/fwdplainc_tex_r1_yaw0_prior.png`:
  - (a) yaw error in the first 3 s, for all four prior × estimator combinations;
  - (b) heading NIS and acceptance, FGO against UKF;
  - (c) yaw error over the flight (symlog).
- Scratch outputs (not committed). The unpacked bag copies (about 26 GB) were deleted at the end of the stage;
  the outputs remain in:
  `/tmp/claude-1000/…/scratchpad/pw/out/`.
