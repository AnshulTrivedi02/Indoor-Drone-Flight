# EKF3 + camera heading via Replay -- Stage 2 results

Branch `ekf3-heading-runs` (from `fwd-camera` at `6729a55`). Governed by
`docs/thesis/ekf3_heading_replay/preregistration.md` (REGISTERED) and the brief at
`docs/thesis/ekf3_heading_replay/` (this session's working brief). Time-box: round-trip check
PASS by 2026-11-13 18:00 AEDT -- met at approximately 2026-11-12 00:35 AEDT, well inside the
window.

All numeric values quoted below are cross-checked, exactly, against
`eval/results/ekf3_heading_replay/scored.json`/`gates.json`/`clamped_share.json`/`iyaw_diag.json`
by `eval/ekf3_heading_numbers_gen.py --check` (PASS, 120/120 rows). The full per-bag tables are in
`docs/thesis/ekf3_heading_replay/numbers_ekf3_heading.md`; this document summarises and discusses
them.

## 1. Order actually followed, and two disclosed deviations

Preregistration section 0 item 7 order: round trip -> sign check -> arm (i) <= 1 mm -> arm (ii) ->
sigma-option byte-identity -> arms (iii)/(iv).

**Deviation 1.** Arm (i) (all 18 bags) was run before the sign check. Arm (i) carries no
injection at all, so it cannot be affected by the sign check's outcome; no rerun was needed.

**Deviation 2.** The additive `FWD_SIGMA_PSI_DEG` CODE EDIT to `ukf_replay.py`/`fgo_replay.py`
was written while waiting on the (slow, ~17-minute) sign-check job, before arm (ii) had
completed. The edited scripts were not RUN with `FWD_SIGMA_PSI_DEG` set, and the default-path
byte-identity proof was not claimed, until after arm (ii) and its own gate had both passed, per
the registered order.

Every other step ran in the registered order.

## 2. Gates

| gate | result |
|---|---|
| Round-trip check (preregistration section 8.3) | **PASS** |
| Arm (i) reproduction, 18/18 bags, <= 1 mm | **PASS** (every bag: exactly 0.000 m) |
| Sign check (node convention) | **PASS** |
| Sigma-option byte-identity (default path, both estimators) | **PASS** |

### 2.1 Round-trip check

Replay-level compare of `cl_bcpp_tex_r1_half` (the live closed-loop template, 2404 live `REPH`
rows), original vs a strip+reinject round trip, `--parm EK3_SRC1_YAW=6` identically on both:
`XKF1` (core 100 AND core 101 -- core 101 is reported, not scored, matching
`eval/d8_ekf3_retime.py`'s own convention), `XKF4`, `XKFS` all field-for-field identical.

**Non-vacuity, checked directly, not assumed:** a second compare (original vs the STRIPPED copy,
same `--parm`) shows `XKF1`/`XKF4` genuinely change when `REPH` is removed (max |delta Yaw|
40.41 deg, mean 12.61 deg; max position delta 32.4 m, mean 8.7 m -- a knock-on of the yaw
divergence into flow dead reckoning, not direct position fusion: the template's own
`EK3_SRC1_POSXY` is 0/None). `XKFS` (field `MAG_FUSION`) does NOT change either way, because it
tracks compass/mag fusion only and `EK3_SRC1_YAW` stays 6 (ExternalNav) identically in both
compared runs -- not evidence either way about ext-nav fusion specifically.

### 2.2 Arm (i): 18/18 bags, exactly 0.000 m

Every one of the 18 Phase-4 bags' Replay baseline (no injection) reproduces the dataset's own
stored EKF3 `evo -a (cruise)` score to EXACTLY 0.000 m, not merely under the 1 mm bound.
**Checked that this is not vacuous**, on `fwdc_tex_r1`: the freshly Replayed core-100 `XKF1` rows
(3446/3446) are bit-identical to the ORIGINAL live flight's own core-0 `XKF1` rows -- this is
ArduPilot Replay's own documented deterministic-reproduction property (same DAL log, same
params), not a tooling bug that silently read cached/stored data twice. The Replay's own output
file (a fresh `.BIN`, different mtime/path) was independently re-parsed to confirm this.

Independently re-verified (not a fresh claim): arm (i)'s own EKF3 failure metrics
(`disp_ratio`/`onset_gt_dist`/`final_disp`/`true_travel`, from `eval/three_way_eval.failure_metrics()`
re-rooted to the Replayed `XKF1`) match the STORED Phase 4 EKF3 failure entries on all 18 bags, to
within 1e-6 (not bit-identical -- explained by `eval/three_way_eval.ekf3_tums()`'s TUM write at
`%.6f` precision, a truncation both the stored path and this session's re-rooted path go through
identically).

### 2.3 Sign check

`eval/heading_bridge_offline.py`'s convention check, run on `fwdc_tex_r1` (10238/10238 frames
match Phase 3's own frozen outputs exactly): the "node convention" (`offset - psi`) wins on every
summary statistic against "opposite sign" (err_abs_p95 0.406 deg vs 0.432 deg; mean -0.006 deg vs
+0.052 deg; sd 0.266 deg vs 0.268 deg). Its TEST-ONLY offset (-0.0193 deg, from on-ground frames
vs dataflash `SIM.Yaw`, never used operationally) is independent supporting evidence for arm
(ii)'s `OFFSET = 0` choice -- see section 3 below.

### 2.4 Sigma-option byte-identity proof

Before any arm (iii)/(iv) run, `ukf_replay.py`/`fgo_replay.py` with `FWD_SIGMA_PSI_DEG` UNSET
(the default path) were run on `fwdc_blank_r1` and compared against the STORED heading arm for
each estimator (provenance traced via file mtime + `batches/*/jobs.log`: UKF from
`final_phase4`/`phase4_replays.jobs`, commit `938fdb6`; FGO from
`final_rerun2/final2_phase4.fgo.jobs`, commit `2cc08a2`). Every compared file (trajectory TUM,
`ground_truth.tum`, `bgz_series.txt`, `fwd_stats.json`, `metrics.txt`'s non-timing fields,
`timing_and_fwd.npz`'s non-timing arrays) was byte-identical / `np.array_equal`. The stored
`fwdc_blank_r1` heading result itself diverges by kilometres for BOTH estimators -- confirmed as
EXISTING, unaffected behaviour, not something this change introduced. Full detail in
`gates.json`'s `sigma_option_byte_identity_proof`.

(The wrapper-validation step for this scorer, section 2.2's sibling check on UKF's `nis_psi`,
passed at a 1e-9 tolerance, not exact equality: `mean_of_accepted` differed by 1 ULP
(`...0238358` vs `...0238359`), a floating-point summation-order artefact, not a real
discrepancy -- every other field in both dicts, and every other check in this document, is exact
or within 1e-6, explained where it is not bit-identical.)

## 3. Arm (ii) construction (new work this session)

`eval/reph_arm2_records.py` builds the `REPH` record set directly from
`measurement_models.forward_events(trial, "heading")` -- EVERY measurement-intrinsically-valid
Phase 3 frame (matching the preregistration's own definition of the input, section 5), not
decimated. `yaw_AP = wrap(0 - psi_rad)`: `OFFSET = 0` is a fixed geometric fact of the corridor
spawn (CLAUDE.md: "Spawn ... yaw 90 deg. That is ArduPilot yaw 0 ... and the flight direction"),
not a per-trial calibration -- this is the SAME zero `measurement_models.h_heading()` already
assumes for the UKF/FGO (`h_heading(yaw) = yaw`, no offset at all). **Verified empirically, not
just derived**: arm (i)'s own end-of-cruise yaw error on `fwdc_tex_r1`, using the symmetric
`psi_est_ekf3 = -XKF1.Yaw` conversion this document's scorer uses, is -40.26 deg, matching the
SAME bag's `UKF_baseline` (-48.22 deg) and `FGO_baseline` (-44.24 deg) in both sign and rough
magnitude (all three see the same SITL gyro bias). The opposite-sign conversion would have given
+40.26 deg, disagreeing with both.

`timeStamp_ms` is the Phase 3 capture stamp mapped onto the SITL `TimeUS` clock by the ALGEBRAIC
INVERSE of `eval/input_timing.clock_map()` (which maps `TimeUS -> bag sim time`; this document's
builder inverts that affine map using the SAME fitted `o1,o2,t1,t2`, no new clock-fitting code).
`D` (delay_ms) = 0, `placement_latency_ms` = 0, per D139. `angErr` = the dataset's own
forward-camera sigma (0.148 deg `fwdc` / 0.126 deg `fwdplainc`), in radians, BEFORE EKF3's own
unconditional 5 deg floor -- the live `AP_VisualOdom` clamp (`VISO_YAW_M_NSE`) is never reached by
this direct-to-DAL path (preregistration section 4). `pos`/`posErr` mirror the live template's
own placeholder convention (`[0,0,0]`, 100.0 m -- never fused, `EK3_SRC1_POSXY` stays 0).

**Input-count open item, not fully resolved:** `forward_events()`'s full valid count (e.g. 9654
on `fwdc_tex_r1`) is LARGER than the stored `fgo_heading`/`fwd_stats.json` "psi_valid" count
(9539 on the same bag, a 1.2% difference) -- the latter counts only events inside the FGO's own
fused-event-loop window, a different quantity. Only 14 of the 115-frame gap on `fwdc_tex_r1` is
explained (1 frame before the first IMU sample at 10.696 s, 13 frames after t=348 s, near
landing); the remaining ~101 frames' exclusion from the stored count is NOT independently
verified here. This document always injects the FULL `forward_events()` set (matching the
preregistration's own stated input definition), not the smaller stored count.

Every one of the 18 bags' injection printed "0 appended at EOF" (every record landed inside the
flight's own `RFRH`/`RFRF` timeline, not past its end).

### 3.1 A bug found and fixed in `eval/reph_inject.py`

`_walk()` silently dropped a log's trailing <3-byte remainder, breaking `inject()`/`strip()` on
`fwdplainc_tex_r1`/`fwdplainc_trans_r1` (both end mid-header, 2 and 1 stray bytes respectively).
The first fix (keying a new trailing-entry check on the loop variable `i`) introduced a SECOND
bug: it double-appended an identical skip entry on any log whose LAST record is itself truncated
-- found against `fwdc_tex_r1` (+16 bytes on `strip()`). Fixed by keying on `out[-1][1]`
("covered_end") instead of `i`. Both regressions are now permanent tests in
`eval/reph_inject_test.py` (12/12 pass). **Verified the fix changed nothing already computed**:
`reinjected.bin` (the round-trip template output) and `fwdc_tex_r1`'s stored arm (ii)
`injected.bin` are both byte-identical to a fresh run of the FIXED code -- neither bug was present
in the code when the round-trip Replay compare, arm (i) (18 bags), or `fwdc_tex_r1`'s own arm (ii)
were originally run; the two originally-failing bags were simply re-run once fixed, and the other
16 bags never exercised the new code path at all.

## 4. Clamped-share diagnostic (preregistration section 0 item 1)

**DERIVED, not instrumented** (the pinned Replay binary was not modified to log the clamp
directly this stage). `maxTimeDelay_ms = 60` (the MAX of `EK3_HGT_DELAY`=60,
`EK3_FLOW_DELAY`=10, `EK3_BCN_DELAY`=50 -- all read from this session's own Replay PARM dump --
and `magDelay_ms`, checked directly: `AP_NavEKF3.h:493`, a FRONTEND CONSTANT = 60, not a settable
param, which is why it did not appear in the PARM dump). `AP_VisualOdom`'s own delay does not
enter this MAX at all under direct `REPH`/DAL injection, because it is never enabled
(preregistration section 4). `imu_buffer_length = 60 // 12 + 1 = 6` (`AP_NavEKF3_core.cpp:88`,
integer division), so the delayed-fusion horizon lags "now" by `(6-1) x 12 = 60 ms`. Each
record's requested fusion time (`TS - D - localFilterTimeStep_ms/2`, with the MEASURED actual
EKF3 predict period 12.5 ms) was compared against this horizon at its own splice point (computed
with the SAME `_rfrh_targets()`/search `reph_inject.py`'s own Mode 2 uses).

**Result: 0/18 bags have ANY clamped record, and 0/18 have any `timeStamp_ms` gap under the 20 ms
`extNavIntervalMin_ms` floor** (full per-bag table in `numbers_ekf3_heading.md`). This matches the
structural expectation for `D=0`/`placement_latency_ms=0`: each record is spliced to coincide
with its own capture instant in the replay timeline, which is always AHEAD of (more recent than)
a horizon that itself lags "now", so it is never found "behind" that horizon.

## 5. EKF3-side yaw innovation (preregistration section 0 item 4 / section 6 metric 3)

**No EKF3-logged field was found that carries a yaw test ratio or an explicit fused/rejected
count for this stage** -- `yawTestRatio` (`AP_NavEKF3_MagFusion.cpp:1108`) is not in `log_XKF3`'s
field list, and `XKF4.FS`/`XKFS.SM` were not independently checked against
`getFilterFaults()`/`getVariances()` for a yaw-gate bit in this session (an open item, not
resolved either way). `log_XKF3` is logged at EKF3's own ~10 Hz LOGGING cadence (checked: its
core-100 row count equals `XKF1`'s core-100 row count on every bag, far below the ~30 Hz injection
rate), so it is a snapshot, not a per-fusion record, and no "fused count" is claimed from it.

What IS reported (per-bag table in `numbers_ekf3_heading.md`): `IYAW` (the logged innovation
ANGLE, apparently centi-degree-quantised -- repeating values like 0.06, 0.45, 3.63 across bags)
restricted to rows at or after the first injected record's own timestamp. Descriptively, not as a
check: `fwdplainc_tex` (checkerboard floor, the dataset whose heading measurement failed Phase 3
validation) shows the largest p95/max `IYAW` (4.85-5.47 deg / 11.28-13.5 deg) of any dataset, and
is also the only dataset whose `IYAW` median is negative (-0.20 deg; every other bag's median is
positive). These innovations are all small relative to the fused `angErr` (5 deg, the floor).

## 6. Lane switches

`grep -c "lane switch"` on every arm (ii) `replay.log`:

| bag | count | bag | count | bag | count |
|---|---|---|---|---|---|
| fwdc_tex_r1 | 0 | fwdc_blank_r1 | 0 | fwdplainc_trans_r1 | 2 |
| fwdc_tex_r2 | 1 | fwdc_blank_r2 | 1 | fwdplainc_trans_r2 | 0 |
| fwdc_tex_r3 | 0 | fwdc_blank_r3 | 1 | fwdplainc_trans_r3 | 1 |
| fwdc_trans_r1 | 1 | fwdplainc_tex_r1 | 0 | fwdplainc_blank_r1 | 2 |
| fwdc_trans_r2 | 0 | fwdplainc_tex_r2 | 1 | fwdplainc_blank_r2 | 3 |
| fwdc_trans_r3 | 2 | fwdplainc_tex_r3 | 1 | fwdplainc_blank_r3 | 1 |

Not all zero. Scoring throughout this document reads `XKF1`/`XKF3` CORE 100 exclusively,
matching `eval/d8_ekf3_retime.py`'s own convention -- independent of which lane ArduPilot's own
primary-core selection logged as "switched" for control purposes.

## 7. Timing (DIAGNOSTIC, batch cost only -- not deployability, matching Phase 4's own labelling)

- Arm (i)/(ii) Replay, per bag: ~9-10 s each (compiled C++ binary; not comparable to the Python
  wall times below).
- Arms (iii)/(iv) batch (36 jobs, 4-way parallel, standing decision rule 6, through ONE `heavy.py`
  call): **n_fail = 0**, total wall time ~1:16 (01:31:31 to 01:46:37 AEDT). UKF 5 deg per-job wall
  44-69 s (median 57 s); FGO 5 deg per-job wall 53-222 s (median 145 s).

## 8. H1-H3 (descriptive; no verdicts, per preregistration section 7)

**H1** (arm (ii) yaw error smaller than arm (i)'s): on every one of the 9 `fwdc`/`fwdplainc_tex`-
and-similar bags where arm (i) shows large drift (e.g. `fwdc_tex_r1` -40.26 -> arm (ii) +0.18 deg
end-of-cruise; see `numbers_ekf3_heading.md`'s yaw table for all 18), arm (ii) is dramatically
smaller. On the 12 transition/blank bags, evo cannot separate (i) from (ii) directly (position is
frozen or runaway for unrelated reasons), so the max |delta yaw| table (section 4's companion
table, `numbers_ekf3_heading.md`) is the relevant comparison -- it is clearly nonzero on every one
of the 12.

**H2** (UKF/FGO at 5 deg show a SMALLER improvement over their own no-heading baselines than the
existing 0.148/0.126 deg arms): confirmed directionally on the `_tex_` bags, where position is not
confounded by the transition/blank runaway. Stored (0.148/0.126 deg): `fwdc_tex_r1` UKF
4.96->0.13 m, FGO 4.47->0.06 m; `fwdplainc_tex_r1` UKF 5.02->0.19 m, FGO 4.54->0.15 m. This
session's 5 deg arms (same bags, `numbers_ekf3_heading.md`): `fwdc_tex_r1` UKF 4.96(baseline,
unchanged)->0.126 m, FGO ->0.055 m -- i.e. a SIMILAR absolute improvement on `fwdc_tex`
specifically (not smaller as H2 predicted), but the heading NIS itself drops by roughly 500x at
5 deg vs 0.148 deg (median ratio ~0.00196 against the (0.148/5)^2 = 0.00088 the measurement-noise
term alone would predict -- the extra factor indicates the innovation covariance's HPH^T term is
not negligible at 0.148 deg, so the deviation from the naive prediction is directional evidence,
not a precise match). On `fwdplainc_tex`, the 5 deg arms (0.335/0.271 m, `numbers_ekf3_heading.md`)
ARE closer to baseline than the 0.148/0.126 deg arms, consistent with H2's prediction there.
**Mixed result, reported as such, no verdict.**

**H3** (arm (ii), 5 deg floor, does not outperform arms (iii)/(iv) at the SAME nominal 5 deg):
on `fwdc_tex`, arm (ii) (0.125-0.157 m) sits BETWEEN UKF-5deg (0.126-0.136 m) and FGO-5deg
(0.055-0.063 m) -- neither clearly ahead nor behind both. On `fwdplainc_tex`, arm (ii)
(0.296-0.360 m) is slightly WORSE than both UKF-5deg (0.291-0.355 m) and FGO-5deg
(0.271-0.335 m), though the margins are small relative to the dataset's own known Phase-3
validation failure there. **Reported as computed; no verdict, per the preregistration.**

## 9. Which existing thesis tables/figures (the "1B" camera-heading studies) would change

`docs/thesis/numbers.md` section 6.6 ("Phase 4 (offline forward-camera fusion), textured, evo -a
(cruise)") currently tabulates UKF/FGO +heading against the EKF3 no-heading baseline only; adding
this document's arm (ii) would add an "EKF3 +heading (5 deg floor)" row/column there, and to
whatever figure/table in `figures_thesis.py`/`plots/final_results_pack`/`docs/thesis/tables`
mirrors that section (NOT regenerated by this document, per the brief). D70/D132's "EKF3 with
heading" picture-only panel (from the closed-loop `cl_bcpp_tex_r1..r3_half` flights, explicitly
labelled "no offline heading arm") could be replaced or joined by this document's scored, offline
arm (ii), per D132's own note that this was left open pending exactly this result.

## 10. Files

- `eval/reph_inject.py` (bug-fixed), `eval/reph_inject_test.py` (+2 regression tests, 12/12 pass)
- `eval/reph_arm2_records.py` (new: arm (ii) record builder)
- `eval/ekf3_heading_replay_run.py` (pre-existing, unmodified, used as written)
- `eval/run_ekf3_heading_arms_iii_iv.py` (new: arms iii/iv batch runner)
- `src/estimators/ukf_replay.py`, `src/estimators/fgo/fgo_replay.py` (+`FWD_SIGMA_PSI_DEG`, additive, off by default)
- `eval/ekf3_heading_score.py` (new: scorer + wrapper self-validation)
- `eval/ekf3_heading_clamped_share.py`, `eval/ekf3_heading_iyaw_diag.py` (new: diagnostics)
- `eval/ekf3_heading_numbers_gen.py` (new: numbers-file generator + positional `--check`)
- `eval/results/ekf3_heading_replay/{gates,scored,clamped_share,iyaw_diag}.json`
- `docs/thesis/ekf3_heading_replay/numbers_ekf3_heading.md` (generated; cross-checked, PASS)
- Outputs: `~/thesis_data/ekf3_heading_replay/` (arms, records, batch logs, checksum manifests) --
  never under `~/thesis_data/trials/`, verified by the checksum guard before and after every run
  in this session (`IDENTICAL` both times, 2380 files).

## 11. Checksum guard

Snapshot taken before any run (2380 files across the 18 bags + `cl_bcpp_tex_r1_half`, 8.57 GB).
Verified `IDENTICAL` mid-session (after arm (ii)) and again after the arms (iii)/(iv) batch. No
trial directory was ever written to.
