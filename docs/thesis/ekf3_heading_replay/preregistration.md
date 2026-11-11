# EKF3 + camera heading via ArduPilot Replay: pre-registration

**Status: REGISTERED** by the coordinator's commit of this file to `fwd-camera`, before any Replay or estimator run
for it. Drafted under the Stage-1 brief (2026-11-11); the coordinator's rulings on the draft's open items are in
§0 below and take precedence over any "PROPOSAL" or "not decided" wording later in the document. User approval
2026-11-11 (D131, D132); time-box: if the round-trip check has not passed by **2026-11-13 18:00**, the work stops, is
logged as future work, and the current thesis wording stays. Nothing in "Your tasks (stage 1)" of the
brief was run to produce a thesis result; the one exception is the injector's own unit
tests and a read-only, scratch-only validation of the round-trip mechanics against a
real log (see "Round-trip check" below) — both diagnostic, neither a flight nor an
estimator replay.

## 0. Coordinator rulings on the draft's open items (decision D139, 2026-11-11; binding)

1. **Injection timing (§8.4: `TS`, `D`, `placement_latency_ms`).** Arm (ii) receives each heading at its **capture
   time**, as the offline UKF and FGO arms do (they fuse each forward measurement at its capture stamp; no live bridge
   latency is modelled for any arm):
   - `TS` = the Phase 3 capture stamp mapped to the SITL `TimeUS` clock with `eval/input_timing.py`'s `clock_map()`
     (offset and rate), the tool already used for this mapping;
   - `D` (`delay_ms`) = 0, and `placement_latency_ms` = 0 (the record is placed at the first frame boundary at or after
     `TS`);
   - DIAGNOSTIC, reported per bag: the share of injected records whose `TS − D − localFilterTimeStep_ms/2` falls behind
     EKF3's `imuDataDelayed.time_ms` horizon (and is therefore clamped to it).
2. **Heading σ for arms (iii)/(iv).** The replays have no heading-σ argument. An **additive** option is approved (an
   environment variable or CLI flag in `ukf_replay.py` / `fgo_replay.py`, or their heading arm, that sets the forward
   heading σ; default unset = the current value). Before any arm (iii)/(iv) run, the default path must be shown
   byte-identical to the stored output on one bag per estimator; if not, STOP. This is a measurement-noise setting of
   the new arm, not a change to any estimator model.
3. **H2** is accepted as a **descriptive comparison**, like H1 and H3: no numeric bound and no verdict, reported in a
   Phase-5-style table. No hypothesis in this document carries a PASS/FAIL verdict.
4. **EKF3-side acceptance and innovation fields (metric 3).** A small read-only extraction script for EKF3's own
   ExternalNav yaw fusion test ratio and innovations is approved; its output is descriptive.
5. **Checksum guard.** `tools/tier1_checksum_guard.py` snapshot/verify over the 18 bags' directories (its `--paths`
   option) before and after the runs; any difference stops the work.
6. **Yaw frame and sign check (§8.4), now a gate step:** before any arm (ii) Replay, `eval/heading_bridge_offline.py`'s
   convention check must select the "node convention" (smaller error against dataflash `SIM.Yaw`) on the bag that
   supplies the measurements; otherwise STOP.
7. **Order:** round-trip check (§8.3) → sign check (item 6) → arm (i) reproduction (≤ 1 mm, all 18 bags) → arm (ii) →
   default-path byte-identity (item 2) → arms (iii)/(iv). Any gate failing stops the steps after it.

## 1. Purpose

Reopen two prior rulings and give EKF3 a fair camera-heading arm via ArduPilot Replay,
with matched 5° UKF/FGO heading arms on the same 18 bags, so the "EKF3 has no offline
heading arm" asymmetry in the three-way comparison can be closed or confirmed as not
closeable within this scope.

**User approval (2026-11-11, verbatim), the governing instruction for this whole
document:**
> "Step 4: reopen the 2026-09-29 ruling and D70 (log both). EKF3 + camera heading via
> Replay, with the round-trip check first; add matched 5 deg UKF and FGO arms on the
> same bags. No floor-removed EKF3 build. Pre-register before running."

The coordinator logs the reopening decisions in `docs/thesis/tier1/decisions_log.md`;
this document does not edit that file.

## 2. The reopened rulings

### 2.1 METHODOLOGY "RULING — EKF3 in the offline forward-camera comparison (user,
2026-09-29)" (`METHODOLOGY.md:2884-2952`)

Adopted option 3 then: EKF3 stays the fixed no-yaw-source baseline; only the UKF/FGO
get forward-camera arms. Option 1 (re-record with `LOG_REPLAY=1` + `REPH` injection)
was explicitly left as **"a deferred extension… reconsidered after Phase 5, and only if
the heading arm shows a clear effect on the UKF and FGO"** (`METHODOLOGY.md:2895-2898`),
with three open items: a tool that writes `REPH` records; a replay-fidelity check
against live EKF3; and whether injected `REPH` records bypass the yaw noise clamp.

**Why the premise is stale.** The ruling's blocking fact was: *"Our logs lack replay
records… `fwdc_tex_r1`'s log has `LOG_REPLAY=0` and `LOG_DISARMED=0`, and no DAL records"*
(`METHODOLOGY.md:2936-2942`). That is no longer true for the datasets this document
targets. `numbers.md` erratum E1 (2026-10-17) corrects the frozen "LOG_REPLAY=0" claim:
every dataset recorded with `consolidated_rerun.parm` (added 2026-09-29, commit
`45c5483`) — which includes all 18 `fwdc_*`/`fwdplainc_*` Phase-4 bags — has
`LOG_REPLAY=1` and `LOG_DISARMED=1`. Verified directly (2026-11-11, this session, not
just cited): both `fwdc_tex_r1` (0 REPH rows) and the closed-loop heading template
`cl_bcpp_tex_r1_half` (2404 REPH rows) declare `REPH` in their own FMT tables with the
expected format, and `fwdc_tex_r1`'s dataflash carries `RFRH`/`RFRF` DAL frame records
throughout (137,879 / 138,318 in a 30.8 MB log) — i.e. it is a genuine DAL-enabled
Replay input, just one that happens to carry zero `REPH` rows because no ext-nav source
was ever wired into that flight.

**The "Phase 5 trigger" is also met — checked against the actual Phase 5 verdict, not
assumed.** Phase 5's pre-registered prediction (a) — "the heading-driven [lateral
velocity error] share falls" — is accepted **PASS in 12/12 estimator × world × dataset
cells** (`METHODOLOGY.md:3440,3516-3519`, "Phase 5 — accepted (user, 2026-09-29)"): the
heading part of lateral velocity error falls from 0.02-0.31 m/s to ≤ 0.004 m/s in every
cell, with heading-driven cross-track error falling from 18-93 m to ≤ 1.1 m
(`METHODOLOGY.md:3441-3442`). (Part (b), about the OTHER, residual error component
staying unchanged, was scored FAIL in 10/12 cells — not relevant to this trigger, which
is about the heading arm having "a clear effect", not about the residual's behaviour.)
This is a real, accepted, measured effect of adding camera heading to the UKF/FGO — the
condition the 2026-09-29 ruling itself set for reconsidering option 1.

### 2.2 `docs/thesis/tier1/decisions_log.md` D70 (line 96)

D70 (2026-10-31) answered a narrower question — whether to add a sixth, **unscored,
picture-only** "EKF3 with heading" panel to a specific figure, drawn from the
**closed-loop** Experiment 1C flights (`cl_bcpp_tex_r1..r3_half`), explicitly labelled
*"no offline heading arm"* and *"a different trajectory, so no score or raw maximum is
printed for it"*. D70 did not create an offline, scored EKF3 heading arm; it is reopened
here only in the sense that this document's Step 4 supersedes its premise ("EKF3 has no
offline heading arm") for the scope defined below. D70's own figure-panel decision is
untouched — this document does not ask for that panel to be re-scored or removed.

## 3. Scope: bags, exclusions, and existing reference data

### 3.1 The 18 Phase-4 bags

`fwdc_{tex,trans,blank}_r1-r3`, `fwdplainc_{tex,trans,blank}_r1-r3`
(`~/thesis_data/trials/<name>/`). **IMU-gap status: all 18 verdict `"ok"`** (checked
2026-11-11 from each trial's own `imu_gaps.json`; no exclusions). This matches "Phase 4"
exclusions, which excluded none of these 18 bags.

### 3.2 Existing reference data (not re-run; used as stored)

Per estimator/arm, already computed and stored under each bag's own trial directory
(`ukf_replay.py`/`fgo_replay.py`'s own `OUTDIR` convention):
- EKF3: the dataset's own `XKF1`/`XKF4`/`XKFS` in `ardupilot.bin` (no-heading; the fixed
  reference, per the 2026-09-29 ruling, unchanged by this document for any arm except
  (i)/(ii) below).
- UKF: `<trial>/ukf_baseline/`, `<trial>/ukf_heading/`, and (fwdc only)
  `<trial>/ukf_heading_yawrate/` — heading noise 0.148° (fwdc) / 0.126° (fwdplainc), per
  `measurement_models.FWD_SIGMA`.
- FGO: `<trial>/fgo_baseline/`, `<trial>/fgo_heading/`, (fwdc only)
  `<trial>/fgo_heading_yawrate/` — same noise values (shared code).

## 4. Arms

| arm | estimator | heading source | heading σ | status this document |
|---|---|---|---|---|
| (i) | EKF3 | none (Replay, no injection) | — | NEW; must reproduce the dataset's stored EKF3 `evo -a (cruise)` score to ≤ 1 mm (METHODOLOGY D8, `~line 7105`) |
| (ii) | EKF3 | camera heading via injected `REPH` (ExternalNav) | the measurement's own σ (0.148°/0.126°), **then EKF3's own 5° floor applies unconditionally** (`AP_NavEKF3_Measurements.cpp:1118`, `NavEKF3_core::writeExtNavData()`: `yawAngErr = MAX(angErr, radians(5.0f))`) | NEW; gated by the round-trip check (§8) |
| (iii) | UKF | camera heading, σ fixed at 5° | 5° (`radians(5)`, NOT the 0.148°/0.126° values) | NEW; offline replay, same gates as Phase 4 |
| (iv) | FGO | camera heading, σ fixed at 5° | 5° | NEW; offline replay, same gates as Phase 4 |
| reference | UKF/FGO | baseline / 0.148°/0.126° heading / (fwdc) heading+yaw-rate | as stored | existing, not re-run |

Arms (iii)/(iv) exist **so EKF3's forced 5° floor (arm (ii)) is compared against the
UKF/FGO under the SAME σ**, not against their existing, tighter 0.148°/0.126° arms —
that would confound "EKF3 vs UKF/FGO" with "5° vs measurement σ". The existing
0.148°/0.126° arms remain the stored reference for "how much does the UKF/FGO gain from
its own best-available σ", a different, already-answered question (Phase 5).

**No yaw-rate arm for EKF3.** Per the 2026-09-29 ruling's own evidence
(`METHODOLOGY.md:2933-2935`): `bodyOdmDataNew.angRate` is written by
`AP_NavEKF3_Measurements.cpp:133` and read nowhere else in EKF3 — there is no EKF3 input
for an external yaw-rate measurement at all. Arm (ii) is heading-only, matching the
brief's "Established facts" line 15.

**No floor-removed EKF3 build.** Per the user's instruction, EKF3's 5° `angErr` floor
(`AP_NavEKF3_Measurements.cpp:1118`) is left exactly as the pinned `7bac20cbcc` build has
it. Arm (ii) injects `angErr` = the measurement's own σ (0.148° fwdc / 0.126° fwdplainc,
radians) and lets that floor bind, which it always will (both values are well under 5°)
— the floor is the whole point of comparing (ii) against (iii)/(iv) at the SAME nominal
5°, not a confound to engineer around.

**Resolves the 2026-09-29 ruling's open item 3 (whether injected `REPH` records bypass
the yaw noise clamp).** Read directly, not assumed: `AP_VisualOdom_MAV.cpp`'s
`angErr = constrain_float(angErr, _frontend.get_yaw_noise(), 1.5f)` (the
`VISO_YAW_M_NSE`-floored clamp, default 0.2 rad ≈ 11.46°, the ≥ 0.05 rad floor the
2026-09-29 ruling worried about) runs inside `AP_VisualOdom_MAV::handle_vision_position_estimate()`,
which only live MAVLink `ODOMETRY`/`VISION_POSITION_ESTIMATE` traffic reaches
(`GCS_Common.cpp:4562-4581`). **Replay's `REPH` path never touches `AP_VisualOdom` at
all**: `Tools/Replay/LogReader.cpp:119-120` dispatches `REPH` straight to
`AP_DAL::handle_message()` (`AP_DAL.cpp:498-502`), which calls
`ekf3.writeExtNavData()` — i.e. `NavEKF3_core::writeExtNavData()`
(`AP_NavEKF3_Measurements.cpp`) — directly. **So arm (ii) is governed by the
unconditional 5° floor only; the 0.2 rad (11.46°) `VISO_YAW_M_NSE` floor the ruling
flagged does not apply to it at all.** This is a materially looser floor than the live
path the ruling considered (option 2) would have imposed — part of why option 1
(Replay) is the fairer route, independent of the latency confound the ruling also cited.

**A second clamp, found while reading the same function, affects WHEN the measurement
is fused, not just how much it is trusted.** `NavEKF3_core::writeExtNavData()` computes
the fusion time as `timeStamp_ms - delay_ms - localFilterTimeStep_ms/2`, then
**clamps it up to `imuDataDelayed.time_ms`** (the oldest IMU sample still in EKF3's
delay buffer) — i.e. a measurement timestamped before the current delayed-fusion
horizon is NOT dropped, it is silently fused as if it arrived exactly at the horizon.
`docs/h_backends_tag_input.md:303` reports the SAME mechanism for tags: "100% clamped to
arrival − 60". **Consequence for Mode 2 (§8.4): if `timeStamp_ms - delay_ms` is chosen
to fall behind this horizon, EKF3's own clamp — not this tool's splice position —
decides the effective fusion time, and the exact byte-stream placement this document
spent most of §8 validating matters less than feared, PROVIDED the splice still lands
the `REPH` record in a plausible position in the Replay message STREAM (so DAL message
processing order relative to IMU/flow stays sane).** Whether arm (ii)'s chosen
`timeStamp_ms`/`delay_ms`/`placement_latency_ms` combination falls behind or ahead of
this horizon is not checked in this stage — it is listed as part of the open "TS and D"
item in §8.4, now with the exact mechanism that makes it matter.

## 5. Heading measurements and injection cadence

**Source: the frozen Phase 3 outputs**, `<trial>/fwd_meas/meas_frozen.npz` — the exact
same file `measurement_models.forward_events()` reads for arms (iii)/(iv) and for the
existing UKF/FGO heading arms. **Validity: measurement-intrinsic only** — support ≥
`S_MIN` = 200 px (the frozen `fwd_calibration.json` value), the identical rule Phase 4
uses. No ground truth, estimated position, or world knowledge enters the gate, matching
`forward_events()`'s own stated invariant.

**Which measurements are injected: every valid frame (`every_n=1`), not the live
bridge's own cadence.** The live `heading_bridge.py` defaults to `every_n=1` as well
(`sigma_psi_deg` is its only tuned default parameter; `every_n` defaults to `1` in its
`declare_parameter` call), but more importantly: arms (iii)/(iv) and the existing
0.148°/0.126° UKF/FGO arms already consume every valid Phase-3 frame via
`forward_events()` — no `every_n` decimation in `measurement_models.py`. Injecting every
valid frame into arm (ii) as well keeps the INPUT identical across (ii)/(iii)/(iv); only
the estimator and σ differ. This is the choice stated by the brief's task 1 as needing
to be "decided by matching the offline UKF/FGO heading arm's input, and state it" — done:
matched to every valid frame.

## 6. Metrics

**Exactly the Phase 4 metrics for heading arms**, computed by the existing scorer
(`eval/phase4_eval.py`, cited `METHODOLOGY.md:2954-3002` "Phase 4" pre-registration and
numbers.md's 1B rows):
1. `eval/three_way_eval.py`'s `evo -a (cruise)` and the transition/blank failure metrics,
   on the SAME pinned cruise window `three_way_eval.cruise_window()` already uses for
   every `dsn_*`/`fwdc_*`/`fwdplainc_*` bag — arm (i) is scored by the identical function
   call as the stored EKF3 reference, which is also how the ≤ 1 mm reproduction claim is
   checked.
2. Yaw error vs ground truth (mean, RMS, end-of-cruise, linear drift deg/min) — same
   definition `phase4_eval.py` already applies to the UKF/FGO arms, applied to arm (ii)'s
   `XKF1` yaw the same way it is applied to arm (i)'s and the dataset's own EKF3 `XKF1`.
3. Forward-measurement valid/fused counts and NIS of the tested measurements — for
   arm (ii), "fused" means EKF3's own gate (`AP_VisualOdom_MAV`'s `VISO_QUAL_MIN`-style
   quality check is not used by the injector, since there is no live quality field in
   this path; the DAL/EKF3-side acceptance gate is `AP_NavEKF3_Measurements.cpp`'s yaw
   fusion test ratio, logged in `XKF3`/innovation fields — this needs the SAME field
   extraction `phase4_eval.py` already does for the UKF/FGO's χ² gate, adapted to read
   EKF3's own innovation log fields instead; this adaptation is a small, reviewed script
   change, not a new metric).
4. Timing (DIAGNOSTIC only, as Phase 4 already labels it): arms (i)/(ii) run through the
   compiled `Replay` C++ binary (not Python), so their wall time is not comparable to
   the UKF/FGO's Python step-time figures at all — arms (iii)/(iv)'s Python step time is
   the one Phase 4 already labels "says nothing directly about flight-controller
   feasibility"; arms (i)/(ii)'s Replay wall time is reported (§12) only as a batch-cost
   figure, not as any kind of deployability comparison to (iii)/(iv).

No new metric is introduced. Item 3's EKF3-side field adaptation is the one place the
scorer needs a small, reviewed extension; it is listed in "Scripts" (§9) as not yet run.

## 7. Hypotheses

Per the brief: **worded as descriptive comparisons**, not a registered-style predicted
effect size, because no existing Phase 4/5 rule gives a derivable quantitative
prediction for "EKF3 + camera heading via a 5°-floored ExternalNav path" specifically —
Phase 5's accepted predictions were about the UKF/FGO's OWN heading arms at their
measurement σ, not about EKF3's ExternalNav path at all.

- **H1 (descriptive).** Arm (ii)'s yaw error (mean/RMS/drift) is smaller than arm (i)'s
  (EKF3's existing no-yaw-source drift, METHODOLOGY "+6.6…+11.1 deg/min (mean ~8.1),
  n = 9 `dsn_*` bags" is the closest existing EKF3 figure, though not on these bags) —
  descriptive only: by how much, and whether it narrows the gap to arms (iii)/(iv), is
  reported, not predicted.
- **H2 (descriptive).** Arms (iii)/(iv) at 5° show a SMALLER yaw-error improvement over
  their own no-heading baselines than the existing 0.148°/0.126° arms show over the SAME
  baselines (a looser σ should help less) — this one IS a quantitative-shaped
  prediction, but it follows directly from the χ²-gate/Kalman-gain mechanics already
  described for the existing arms (tighter σ → more trusted measurement → more
  correction), not from a new empirical rule, so it is marked **PROPOSAL**, for the
  coordinator to accept, reword, or drop before any run.
- **H3 (descriptive).** Arm (ii) (5° floor) does not outperform arms (iii)/(iv) (5°) on
  yaw error, because EKF3's `angErr` floor imposes the SAME nominal measurement
  trust as arms (iii)/(iv) while not benefiting from the tighter 0.148°/0.126° the
  UKF/FGO's own best arms use — whether EKF3's different fusion mechanics (gated
  `fuseEulerYaw`, full joint-covariance update) makes up for this is the open question
  this whole exercise is actually testing. No numeric bound is proposed.

These are descriptive comparisons to be reported in Phase-5-style tables; any
registered-style numeric bound is explicitly left for the coordinator to add, not
invented here.

## 8. The round-trip check — findings, final design, and the gate

**This section is the substantive technical result of Stage 1.** The brief asked for the
round-trip check to be *specified* as a gate (not run, except for the injector's own
unit tests). Specifying it required building and testing the injector against the real
template, which surfaced two wrong placement rules before the correct one — recorded
here in full because it changes what the round-trip check can and cannot certify.

### 8.1 What was tried, in order, and measured (not assumed)

All three were checked against **every one of the 2404 live `REPH` rows** in
`cl_bcpp_tex_r1_half` (not a sample), using `eval/reph_inject.py roundtrip-extract` +
`strip` + `inject`, comparing the reinjected file byte-for-byte against the untouched
original — a stronger, directly-runnable proxy for "does the mechanics preserve the
log", run without Replay:

| attempt | rule | result (bytes differing / 31,150,080 total) |
|---|---|---|
| 1 | position derived purely from `timeStamp_ms` ("first RFRH after `TS*1000`") | **31.3%** |
| 2 | position anchored on "count of RFRH records before this REPH" (Mode-1-shaped, but counting the wrong record type) | **0.31%** |
| 3 (final) | position anchored on "count of RFRF records before this REPH" | **0.003%** (928 bytes, in ~12 clusters) |

**Root cause, read from `~/ardupilot/libraries/AP_DAL/AP_DAL.cpp` at the pinned
`7bac20cbcc`, not assumed:**
- `AP_DAL::writeExtNavData()` (lines 359-371) calls `end_frame()` **itself**,
  synchronously, immediately before writing `REPH`.
- `end_frame()` (lines 178-183) writes `RFRF` **only if `_RFRF.frame_types != 0`**, and
  does **not** write a new `RFRH` — that only happens inside `start_frame()`, and only
  on a genuinely new IMU timestamp (`AP::ins().get_last_update_usec()` changing).
- These two facts are independent: a `REPH` write's own `RFRF` flush is NOT coupled to
  how many `RFRH` records have occurred recently. Confirmed directly: one real stretch
  of 40 consecutive records (one `REPH` among them, surrounded by `BARO`, `CTUN`,
  `XKF1/2/3/4/5`, `PID*`, `AHR2`, `SIM`, `VIBE`, etc. — all independently-scheduled
  telemetry) sits between TWO `RFRF` records with **zero** `RFRH` between them, because
  `start_frame()`'s early-return branch (same `imu_us`) kept firing throughout that
  stretch while unrelated logging continued. Attempt 2's "RFRH count" anchor collapses
  exactly here.
- `RFRF`, by contrast, is written by the SAME function call (`writeExtNavData`) that is
  about to write `REPH` (when `frame_types != 0` — 2392/2404, 99.5%, of the live
  template's rows are immediately preceded by one), landing byte-adjacent with nothing
  in between. It is an exact, unambiguous positional anchor.

### 8.2 Final design: `eval/reph_inject.py`, two modes

- **Mode 1 (positional, exact)** — used for the round-trip check and the unit tests.
  Each extracted `REPH` carries `rfrf_count_before` (how many `RFRF` precede it in file
  order); reinjection places it immediately after the same-numbered `RFRF` in the
  stripped file. Verified **99.997% byte-identical** (928 / 31,150,080 bytes differing)
  against `cl_bcpp_tex_r1_half` in full — NOT byte-identical, that specific figure is
  the measured result, not rounded up.
- **Mode 2 (from a capture timestamp, approximate for arm (ii); exact when fed each
  record's true arrival time, see below)** — for arm (ii), which injects brand-new
  measurements that were never written by any live run, so there is no
  `rfrf_count_before` to recover. Requires an explicit `placement_latency_ms` (no
  default): target = first `RFRH` after `(timeStamp_ms + placement_latency_ms) * 1000`,
  cut = the `RFRF` immediately before that `RFRH`. **`placement_latency_ms` is an OPEN
  ITEM for arm (ii)** (§8.4) — but the search-and-cut MECHANISM itself (not the still-open
  question of how arm (ii) computes its input to it) has now been validated independently
  of Mode 1, below.

**Mode 1 alone is a weaker check than it looks: it trivially restores a stored position
index, so it cannot show that a genuinely TIME-DERIVED placement (the only kind arm (ii)
can use, since a synthetic measurement has no stored position) gets the same answer.**
Checked directly, not left as a gap: every one of the 2404 `REPH` rows is immediately
followed by a `VISP` record (confirmed earlier, §8.1), and `VISP.TimeUS` turns out to
equal — **exactly, 2404/2404, 0 exceptions** — the `time_us` of the `RFRH` record
immediately preceding that `REPH` in file order. `VISP.TimeUS` is therefore a genuine,
independently-logged arrival-time field, sourced from the SAME original payload bundle
as the brief's "the original REPH payload" (not a quantity this tool's own bookkeeping
derived). Feeding Mode 2's actual search-and-cut code each record's own `VISP.TimeUS` as
its exact target (bypassing the separate, still-open `timeStamp_ms + placement_latency_ms`
arithmetic entirely) and running it over all 2404 rows reproduces the SAME **99.997%
byte-identical** result (928 bytes differing, in the same clusters) as Mode 1 — the
mechanism arm (ii) will actually use is therefore validated, not just Mode 1's trivial
positional restore. (Script: `eval/reph_inject_validate.py`, committed — see §11 — not
the shipped CLI; Mode 2's public `inject()` takes one shared `placement_latency_ms` per
call, not a per-record arrival time; giving it one would be a reasonable follow-up,
listed in §9, not done in this stage.)

**The 928-byte residual is now fully explained, not left open.** 11/12 clusters sit
immediately after an `OF`/`ROFH` pair (ArduPilot's optical-flow DAL replay record, in
`docs/partC_onboard_feasibility.md:343`'s own list of `R*` Replay-input record types;
one of the 11 has `PL` directly before `OF` too) — e.g.
`['ROFH', 'OF', 'REPH', 'VISP', 'REVH', ...]` instead of the usual
`['...', 'RFRF', 'REPH', 'VISP', ...]`; the 12th sits after `['REV2', 'REV3', 'REPH', ...]`
(ArduPilot event records) instead. Exact context for all 12, reproducibly, from
`eval/reph_inject_validate.py`'s own output (§11), not just this prose. Mechanism, read
from the same `end_frame()` docstring already cited in §8.1 ("Must be called on all
events and injections of data (eg flow)…"): `ROFH`'s write, and `log_event2()`'s (the
`REV2`/`REV3` path, `AP_DAL.cpp:185-192`), both call `end_frame()` first, exactly as
`writeExtNavData()` does. For these 12/2404 (0.5%) rows, the EARLIER call's `end_frame()`
flushed the pending `RFRF` a moment before the `REPH` write's own `end_frame()` call
found `frame_types` already 0 — the SAME "shared flush" mechanism the unit tests'
double-delivery case covers, except here `REPH` shares its flush with a PRECEDING `OF`
or `REV2`/`REV3`, not another `REPH`. **This tool reinserts the new `REPH` immediately
after the shared `RFRF` — i.e. BEFORE the record that originally came first in that
gap.**

**A source-level argument this is likely harmless to `XKF1`, checked, not just asserted
— but not treated as proof; the Replay-level comparison in §8.3 is still the actual
gate.** Read directly (`~/ardupilot_diag/libraries/AP_DAL/AP_DAL.cpp`, the SAME tree the
pinned `Replay` binary was built from — confirmed byte-identical to stock `~/ardupilot`
for every file cited in this section except `AP_DAL.cpp` itself, whose only diff from
stock is two added shadow-UKF hook calls, `ukf_update_hook`/`ukf_flow_hook`, at
`UpdateFilter()`/`writeOptFlowMeas()` call sites — unrelated to `REPH`/`RFRF`/`end_frame()`
mechanics): `AP_DAL::handle_message(const log_ROFH&, ...)` and
`AP_DAL::handle_message(const log_REPH&, ...)` (the Replay-time dispatch targets for
these two record types) both do nothing but call the corresponding
`ekf3.writeOptFlowMeas(...)`/`ekf3.writeExtNavData(...)`, which push a time-stamped
element into EKF3's OWN internal buffered-measurement queue (`storedExtNav.push(...)`
for ext-nav). **Fusion happens later, keyed by each buffered element's own stored
timestamp, not by the order these two push-calls were made in** — so swapping which of
a `ROFH`/`REV2`-`REV3` pair and an adjacent `REPH` gets WRITTEN TO THE BUFFER first,
within the same small gap, should not change which element is fused when, provided both
land before the buffer actually needs them (true here: they are a few RFRH-frames apart
at most). This is a source-grounded argument for why the residual is UNLIKELY to move
any `XKF1` field, not a substitute for actually checking: **it is exactly what §8.3's
Replay-level field comparison settles**, and the comparison is pointed at this named
mechanism specifically, not left to find it blindly. Not fixed in this stage (fixing the
splice tool itself would mean tracking relative order against every record type sharing
a flush gap, not just other `REPH` rows — a larger change than Stage 1's scope).

**Checked separately: does any of this generalise to the logs arm (ii) actually
targets, which (unlike `cl_bcpp_tex_r1_half`) have ZERO prior `REPH` history?** All of
§8.1/8.2 so far validates placement by reconstructing EXISTING rows in a log that
already has ext-nav traffic — not the same thing as placing a BRAND-NEW row into a log
that has never had any. `eval/reph_inject_validate.py --generalization-trial
fwdc_tex_r1` (one of the actual 18 Phase-4 bags, 0 `REPH` rows) injects 20 evenly-spaced
synthetic records (Mode 2, `placement_latency_ms=0`) and checks each one's immediate
neighbours. **Result: 20/20 land immediately after `RFRF` and immediately before
either `RFRH` or another `end_frame()`-calling record** (`ROFH`, `REV2`, `REV3`, …,
enumerated from `AP_DAL.cpp`'s own `end_frame();` call sites, not assumed) — the same
"`RFRH`, `RFRF`, `REPH`, …" pattern found throughout `cl_bcpp_tex_r1_half`, not
something different on a zero-history log. The same log also shows the "other content
lands between an `RFRF` and the next `RFRH`" phenomenon is not specific to ext-nav
logs either: 13,634/138,318 (9.9%) of `fwdc_tex_r1`'s own `RFRF` records are not
immediately followed by `RFRH`. **This is evidence of correct generalisation, not
proof** — it checks placement sanity (neighbours look right), not that the resulting
`XKF1` is correct (no ground truth exists for a synthetic measurement); that is, again,
what §8.3's Replay-level comparison on the ACTUAL target logs would need to confirm,
and this document does not claim it already has.

### 8.3 The round-trip check (specified; NOT run by this document)

Per the brief, as a gate before any arm (ii) run:
1. Take `cl_bcpp_tex_r1_half` (live `REPH`, the template).
2. `reph_inject.py roundtrip-extract` it (Mode-1 records, in scratch, not `trials/`).
3. `reph_inject.py strip` it (in scratch).
4. `reph_inject.py inject` the stripped copy with the extracted records (Mode 1, in
   scratch) — mechanics check, already run in this document, 99.997% byte-identical
   (§8.1/8.2); this step alone needs no Replay and has been done.
5. **Not yet run (needs Replay): Replay BOTH the untouched original and the
   reinjected copy, with identical params**, through `heavy.py`, one at a time, using
   `eval/ekf3_heading_replay_run.py` (§9) — `~/ardupilot_diag/build/sitl/tool/Replay`,
   the D8-verified binary, SHA-256 `415e69650ac7f5c7d658b3e3c8a021b2e66cea8f7617c62ce1c91c61df08eda2`
   (recorded here, and by the driver script itself in its `manifest.json`, since the
   ≤ 1 mm reproduction claim is tied to this specific build, not just its name). **PASS
   requires `XKF1` (both logged EKF3 cores, `C==100` plus `101` if present) and the
   yaw-fusion-relevant fields of `XKF4`/`XKFS` to be field-for-field identical** between
   the two Replay outputs. **STOP RULE: if this check fails, arm (ii) is not run; the
   discrepancy is diagnosed (the 12-row `OF`/`ROFH`-shared-flush mechanism in §8.2 is
   the first thing to check, now that it is named) and this document is revised before
   any further attempt.**
6. **A second check, independently runnable now and already run by this document's unit
   tests**: `reph_inject.py strip` on a log with zero `REPH` records (checked on a real
   zero-`REPH` log, `fwdc_tex_r1`, 30,789,632 bytes) is byte-identical to the input.
   PASS (confirmed).

**Caution about reused helper functions and `trials/`.** `eval/input_timing.py`'s
`sim_truth()` and `eval/three_way_eval.py`'s `ekf3_tums()` both cache a derived file
under `<trial>/ekf3/` on first call, created if missing. All 18 Phase-4 bags already
have this cache (checked 2026-11-11 — calling these helpers on them is a no-op, not a
new write). **`cl_bcpp_tex_r1_half` does NOT** (checked). Any step 5 script that scores
via these helpers must therefore NOT call them against
`~/thesis_data/trials/cl_bcpp_tex_r1_half` directly — it must copy the needed inputs
into `~/thesis_data/ekf3_heading_replay/` first, or use a scoring path that does not
cache into `trials/`. Stated here as a required design constraint on the (not yet
written/run) step-5 script, not assumed solved.

### 8.4 Open items this round-trip check does NOT resolve (for the coordinator)

- **`placement_latency_ms` for Mode 2 (arm (ii)'s actual injection).** The live
  template's own latency (its REPH's `TS` vs the `RFRH` it precedes: 44.4-71.2 ms, mean
  50.6, median 49.7, n = 2404) is that PARTICULAR closed-loop pipeline's
  `VISO_DELAY_MS` + transport/processing time — not necessarily representative of a
  pure-Replay injection with no live transport at all. Candidate choices, NOT decided
  here: (a) 0 (assume instantaneous write, i.e. place strictly at the measurement's own
  capture-mapped time); (b) the measured closed-loop figure (~50 ms) as a stand-in; (c)
  something tied to `VISO_DELAY_MS` as configured for arm (ii)'s `--parm`. This needs a
  ruling before any arm (ii) run.
- **`TS` itself: mapping the Phase-3 capture timestamp (bag/sim time) to the SITL
  `TimeUS` clock.** `eval/input_timing.py`'s `clock_map()` (offset AND rate, fitted
  early/late in the flight) is the existing, already-used tool for this — the SAME
  function `eval/d8_ekf3_retime.py` uses. Not yet wired into a reph_inject caller; listed
  in §9 as a script to write, not run.
- **`D` (delay_ms).** The live template's `D` is a constant 25 ms throughout. One
  candidate for arm (ii), marked PROPOSAL and NOT decided: `D = 0`, folding the whole
  known delay into `TS` via the clock map, with EKF3's own extra −6 ms
  (`AP_NavEKF3_Measurements.cpp:232-236`, already documented for flow) accounted for
  separately. §5's new finding on EKF3's `imuDataDelayed.time_ms` clamp bears directly
  on this choice: whichever `TS`/`D`/`placement_latency_ms` combination is picked, check
  whether `TS - D - localFilterTimeStep_ms/2` falls behind that horizon before assuming
  the chosen values are "just a detail".
- **`extNavIntervalMin_ms` — checked, NOT a problem.** `AP_NavEKF3.h:518`:
  `extNavIntervalMin_ms = 20` (ms, fixed constant). The forward camera's 30 Hz cadence
  (33.3 ms) is already above this floor, so arm (ii), injecting every valid frame, is
  NOT silently decimated by this constant — confirmed by reading the constant directly,
  not assumed.
- **Yaw frame/sign.** Not re-derived here. Before any arm (ii) Replay, run
  `eval/heading_bridge_offline.py`'s existing frame-convention check (its "node
  convention" vs "opposite sign" comparison against dataflash `SIM.Yaw`) on whichever
  bag supplies arm (ii)'s measurements, and require the "node convention" branch to be
  the smaller-error one, exactly as that script already does for the live bridge. A
  silent sign error here would pass the round-trip check (which only exercises REPLAYING
  EXISTING rows, never NEW ones) and corrupt every arm (ii) result.
- **Quaternion field order.** Resolved, not open: `AP_Math/quaternion.h`'s
  `q1,q2,q3,q4` is `(w,x,y,z)`, confirmed against the live template's own near-identity
  rows (`Q1≈1`, small `Q4`) and matching `HeadingCore.q_yaw()`'s existing `[w,x,y,z]`
  convention exactly.

## 9. Scripts (NOT run; task 3)

- **Replay driver for arms (i)/(ii) — written, NOT run: `eval/ekf3_heading_replay_run.py`.**
  Wraps `~/ardupilot_diag/build/sitl/tool/Replay` via `heavy.py` (one job at a time, per
  the brief), `--parm EK3_SRC1_YAW=6` for arm (ii) (confirmed this is the only `--parm`
  REPH-via-Replay itself needs, since EKF3 reads it through the DAL path directly,
  bypassing live `AP_VisualOdom` entirely — §4's new finding; whether any OTHER param,
  e.g. for arming checks under Replay, is also needed is not separately re-derived
  here), writing outputs under `~/thesis_data/ekf3_heading_replay/<bag>/{baseline,heading}/`.
  Scores via the SAME `three_way_eval.cruise_window`/`crop`/`write_tum`/`evo_ape_a`/
  `ekf3_tums` functions `eval/d8_ekf3_retime.py` already uses for its own baseline
  arm — not a reimplementation. Records the Replay binary's path and SHA-256 in its own
  `manifest.json` (§8.3). Refuses to write under `~/thesis_data/trials/`, refuses arm
  (ii) without an explicit `--require-roundtrip-ok` gate file recording
  `{"round_trip_check": "PASS"}` (this document's §8.3 stop rule, enforced in code, not
  left to convention), and refuses arm (ii) records that lack `rfrf_count_before`
  without the caller choosing a `placement_latency_ms` explicitly (no silent default).
  **Not run** — per task 4, the only code exercised in this stage is the injector's own
  tests and the read-only validations in §8.1/§8.2.
- **Mode 2, per-record arrival time** — to be written: the shipped `inject()` CLI takes
  one shared `placement_latency_ms` per call; §8.2's Mode-2-mechanism validation used a
  bespoke per-record-target script instead (not the public API) because each record's
  true arrival time differs. A proper per-record `inject()` input (e.g. an optional
  `"arrival_us"` field per record, alongside `"timeStamp_ms"`) would let the SAME public
  API serve both the validation and arm (ii)'s eventual real injection. Not written in
  this stage — the validation's informal script already exists in this session's
  scratch output, not committed.
- **UKF/FGO 5° arm job list** — per the brief's instruction to "reuse the existing
  replay CLIs with a heading-sigma argument; check they accept one". **Checked: they do
  NOT.** `src/estimators/ukf_replay.py:119` and `src/estimators/fgo/fgo_replay.py:127`
  both read σ directly from `measurement_models.FWD_SIGMA`, keyed by dataset name
  (`fwdc`/`fwdplainc`), with no CLI flag or environment-variable override of any kind —
  confirmed by reading both files, not assumed. **Per the brief's own instruction, this
  is a STOP: no code change to an estimator-adjacent script is made in this document.**
  Proposed, NOT applied, diff (for the coordinator's ruling): add an env-var override
  following this project's own existing pattern in the SAME file
  (`INIT_YAW_SIGMA_RAD`/`UKF_OUT_ROOT`/`FGO_OUT_ROOT`: off by default, asserted to only
  write outside `trials/`):
  ```python
  # ukf_replay.py, proposed (NOT applied): after "sig_fwd = FWD_SIGMA.get(...)"
  FWD_SIGMA_PSI_DEG = os.environ.get("FWD_SIGMA_PSI_DEG")
  if FWD_SIGMA_PSI_DEG:
      assert os.environ.get("UKF_OUT_ROOT"), "FWD_SIGMA_PSI_DEG needs UKF_OUT_ROOT (never into a trial directory)"
      sig_fwd = {**sig_fwd, "psi": np.radians(float(FWD_SIGMA_PSI_DEG))}
  ```
  ```python
  # fgo_replay.py, proposed (NOT applied): after "sig_fwd = FWD_SIGMA[...] if ... else None"
  FWD_SIGMA_PSI_DEG = os.environ.get("FWD_SIGMA_PSI_DEG")
  if FWD_SIGMA_PSI_DEG and sig_fwd is not None:
      assert os.environ.get("FGO_OUT_ROOT"), "FWD_SIGMA_PSI_DEG needs FGO_OUT_ROOT (never into a trial directory)"
      sig_fwd = {**sig_fwd, "psi": np.radians(float(FWD_SIGMA_PSI_DEG))}
  ```
  This does not touch `ukf_core.py`, `fgo_core.py`, or `measurement_models.py` — both
  `U.update_heading(x, P, psi_m, sig_fwd["psi"], ...)` and `FGO(..., fwd_sigma=sig_fwd,
  ...)` already accept σ as a plain argument; only the SOURCE of that value would
  change, additively, off by default. Marked as a proposal needing explicit sign-off,
  per the brief, not applied.
  Once (if) approved, the job list is: for each of the 18 bags, `ARM="heading"`,
  `FWD_SIGMA_PSI_DEG=5`, `UKF_OUT_ROOT`/`FGO_OUT_ROOT=~/thesis_data/ekf3_heading_replay/{ukf,fgo}`
  — 18 UKF + 18 FGO = 36 runs.
- **Clock-map wiring for Mode 2** (§8.4) — to be written: a thin caller that fits
  `eval/input_timing.clock_map()` per target bag and feeds `reph_inject.py inject
  --placement-latency-ms` the resolved value. Not written in this stage.

## 10. Output discipline

- All new outputs under `~/thesis_data/ekf3_heading_replay/`, never under
  `~/thesis_data/trials/` — enforced IN CODE by `eval/reph_inject.py`'s
  `_refuse_output_path()` (realpath check against `~/thesis_data/trials`, tested; see
  §11).
- Replay runs, when run, go through `heavy.py` one job at a time (the brief's
  instruction; also `heavy.py`'s own flight/build-lock protocol, unconditionally
  required regardless).
- **Checksum guard.** `tools/tier1_checksum_guard.py`'s DEFAULT snapshot specs are
  scoped to a different experiment (Tier-1's `T_*` trial glob, its own batch folders,
  `eval/results/expL`/`expT`) and do NOT cover the 18 `fwdc_*`/`fwdplainc_*` bags or
  `cl_bcpp_tex_r1_half` at all — checked by reading `default_specs()`, not assumed. So
  this document does NOT claim "run it with defaults"; it proposes the tool's `--paths`
  option (documented in the tool's own help as "TEST ONLY", but not code-enforced to
  only that use) pointed explicitly at
  `~/thesis_data/trials/{fwdc,fwdplainc}_*/ardupilot.bin` and
  `~/thesis_data/trials/cl_bcpp_tex_r1_half/ardupilot.bin`, with `--out` under
  `~/thesis_data/ekf3_heading_replay/` — snapshotted BEFORE the round-trip Replay runs
  (§8.3 step 5) and verified unchanged AFTER. This is a deliberate repurposing of an
  existing escape hatch for a new, reviewed one-off use, not an unmodified default run
  — flagged for the coordinator's sign-off, not silently assumed covered.

## 11. Injector and its tests (task 2; built and run in this stage)

`eval/reph_inject.py` (`strip`, `inject` [Mode 1/Mode 2], `roundtrip-extract`) and
`eval/reph_inject_test.py` (10 checks, all passing, no Replay):

| check | result |
|---|---|
| pymavlink (independent reader) parses synthetic REPH rows matching what was written | PASS |
| round trip (strip + reinject original records) byte-identical, single-REPH-per-gap | PASS |
| zero records: synthetic log byte-identical after strip | PASS |
| `inject()` with an EMPTY records list is byte-identical (the brief's exact wording; fixed a bug this check first caught — `inject([])` used to fall into Mode 2 and raise for a missing `--placement-latency-ms` that zero records never needed) | PASS |
| zero records: real `fwdc_tex_r1` (30,789,632 bytes) byte-identical after strip | PASS |
| double-delivery gap: both reinjected in the same gap, correct relative order | PASS |
| double-delivery gap: documented non-byte-identical case (see §8.2) | PASS |
| insertion past the last RFRH appends at EOF, prefix untouched | PASS |
| Mode 2 (timestamp + required latency) placement, and its refusals | PASS |
| refusals: OUT==IN, existing OUT, OUT under `trials/`, duplicate target, bad REPH format | PASS |

Plus `eval/reph_inject_validate.py` (committed, not scratch, so these numbers are
re-runnable, not just prose claims): two full-scale validations, read-only against the
real template, writing JSON under `~/thesis_data/ekf3_heading_replay/`, never
`trials/`. Mode 1 (positional) and Mode 2 driven by each record's own `VISP.TimeUS`
both reproduce `cl_bcpp_tex_r1_half`'s all 2404 `REPH` rows to **99.997% byte-identical**
(928/31,150,080 bytes differing, the SAME 12 clusters, now explained as the
`OF`/`ROFH`/`REV2`/`REV3`-shared-flush mechanism, §8.2) — independent confirmation that
Mode 2's actual search-and-cut mechanism, not just Mode 1's trivial position restore,
is correct. The script also confirms the `VISP.TimeUS`-equals-preceding-`RFRH.time_us`
claim directly: 2404/2404, 0 exceptions.

`eval/ekf3_heading_replay_run.py` (the Replay driver, §9): written, syntax-checked, NOT
run (no Replay was invoked in this stage).

## 12. Estimated runtime for the full run set (sourced from existing logs, not timed
fresh for this run set)

| job set | n | per-job wall time (source) | serial total | notes |
|---|---|---|---|---|
| EKF3 Replay, arms (i)+(ii) | 36 (18 bags × 2) | ~4-6 s (D8: `dsn_tex_r1` baseline 5.24 s, retimed 3.67 s, from `~/thesis_data/d8/dsn_tex_r1/{baseline,retimed}/replay.log` file-mtime spans) | ~2.5-4 min | Must run one at a time (heavy.py) regardless — already cheap |
| Round-trip check Replays | 2 (original + reinjected) | ~5 s each | ~10 s | One-off, before any arm (ii) run |
| UKF 5° heading arm | 18 | 45-313 s (`~/thesis_data/batches/phase4_replays/jobs.log`, existing UKF Phase-4 `heading` jobs, n=45 across all arms/datasets — range quoted, not averaged past what the log shows) | ~14-78 min serial; ~4-20 min at 4-way parallel (standing decision rule 6's cap) | Textured bags slower than blank, consistent with existing Phase 4 figures |
| FGO 5° heading arm | 18 | 40-362 s (`~/thesis_data/batches/final2_phase4/jobs.log`, existing FGO Phase-4 jobs; that batch itself ran 6-way, a DIFFERENT experiment's own decision, not reused here) | ~12-108 min serial; ~3-27 min at 4-way parallel (this run set's own cap, below) | Same pattern |

**This is a non-timing experiment, so standing decision rule 6 caps parallelism at 4,
not the 6 the cited FGO batch happened to use for itself.** **Total, at 4-way parallel
for the UKF/FGO 5° arms and serial Replay (heavy.py, one job at a time, per the brief,
regardless of rule 6): roughly 10-55 minutes of machine time**, dominated by whichever
of the UKF/FGO 4-way batches is slower. This is a rough bound built from existing,
cited job logs for similar-sized bags on the same machine — the per-job times are
sourced, not timed fresh for this run set; the parallelism cap and the arithmetic
combining them are this document's own, not independently sourced.
