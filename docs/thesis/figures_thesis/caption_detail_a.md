Restyle stage A: caption detail file. Per figure/table, this holds the selection rule, alignment method, build/provenance
detail, cited sources, and other material removed from the plain reader-facing caption, verbatim or near-verbatim from
the pre-restyle text, so nothing is lost (only relocated). The coordinator merges this content as needed.

## F2 (Figure 4.1): caption detail

- Full condition statement dropped from the compressed caption: "Textured corridor at half real-time (RTF 0.5; the
  simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s), each estimator flying the
  vehicle (closed loop)."
- Wall/threshold citations removed from the caption text (the underlying `cite()` checks still run, as bare calls, for
  their side effects only): walls at x = ±10 m is cited to `CLAUDE.md:101` ("5 m tall and 0.2 m thick at x = ±10 m");
  the 9.58 m contact threshold is cited to `docs/thesis/numbers.md:428` ("|x| ≥ 9.58 m").
- Selection rule for the dashed (no-heading) paths: "one flight of each estimator's own n = 3 no-heading cell, Table
  4.3"; drawn up to the wall contact (X).
- Build/provenance: "Builds: the final UKF port (jitter-corrected) and the final FGO node (corrected priors,
  4c07374b/HEAD); earlier builds, including the original-priors final FGO node, are in Table A.1."
- Methodological caveat: "Closed-loop run-to-run variability is descriptive (the spread, Table 4.3); no comparison
  across real-time factors."
- Sources (already in the figure index, not duplicated here): paths from dataflash SIM of
  `cl_a_tex_half`, `cl_bcpp_tex_r1-r3_half`, `cl_ukf_a_tex_half_v2`, `cl_ukf_b_tex_r1-r3_half_v2`,
  `cl_fgo_a_tex_r1_half_rp`, `cl_fgo_b_tex_r1-r3_half_rp`; contact and B2 from `eval/results/closed_loop_<trial>.json`.

## F9 (Figure 4.1b): caption detail

- Full condition/estimator-definition clause dropped: "its own current yaw minus the simulator's true yaw; EKF3 from
  its logged state, the UKF and the FGO from their current-time outputs, the values the controller received"; "RTF
  0.5" value (the half-real-time condition is kept in the compressed caption as plain "half real time").
- "Dashed (here: without heading, not hindsight)" clarifying aside.
- "(corrected priors)" build qualifier on the no-heading contact times.
- Mechanism paragraph: "Mechanism: the controller flies the commanded path in the estimator's frame, so a heading
  error turns the forward motion by that angle and adds a sideways velocity of the flight speed times its sine; a
  positive error (estimate clockwise of truth) turns the vehicle west, and integrated over the cruise this is the
  westward drift into the wall in Figure 4.1."
- Build/provenance: "Builds: the final UKF port and the final FGO node (corrected priors, 4c07374b/HEAD), as in
  Figure 4.1; earlier builds, including the original-priors final FGO node, are in Table A.1."
- Methodological caveat: "Closed-loop run-to-run variability is descriptive (the spread, Table 4.3); no comparison
  across real-time factors."
- Legend/layout fix (task 1): the legend used to sit inside panel (a) at `loc="lower left"`, which covered the
  with-heading lines (they stay near zero for the whole flight) for roughly the first 120 s of the time axis. Moved
  to an axes-anchored legend above panel (a) via `bbox_to_anchor=(0.0, 1.02, 1.0, 0.2)` with `mode="expand"`, 4
  columns; the panel labels "(a)"/"(b)" (previously drawn with `ax.set_title(loc="left")`, which sits above the
  axes and would have collided with the raised legend) were moved to `ax.text()` inside the bottom-left corner of
  each panel instead.

## F5 (Figure 5.1): caption detail

- Setup detail dropped: "the tag room, 5 laps of a 6 m square, open loop on simulator truth"; condition definitions
  kept (A all 8 tags, B the 4 corners, C 2 diagonal, D 1 tag).
- Median gap between fixes, by condition: 4.3 / 10.1 / 22.0 / 46.3 s.
- Condition D descriptive comparison: "in condition D the FGO live {FGO live rmse} m against EKF3 {EKF3 live rmse} m
  is descriptive, 3 flights."
- Live max/min ratio, condition A to D: 1.97 / 2.36 / 1.42 / 1.57.
- FGO whole-flight hindsight batch's hindsight gain over FGO live, median per gap, condition A to D (SI-rounded, 3
  dp, m); the smoothed UKF's gain over UKF live, same conditions (signed, SI-rounded, 3 dp, m); the ratio of the
  batch's gain to the smoothed UKF's gain is 1.31-3.89.
- "Same tag fixes for every estimator" (every estimator scored against the identical tag-fix sequence, per
  condition).

## F6 (Figure 5.3): caption detail

- Indoor sensor set, dropped from the compressed caption but unchanged as a design fact: IMU (accelerometer and
  gyro), downward optical flow and the downward LiDAR rangefinder only; no GNSS (switched off at the entrance), no
  compass, no forward-camera heading (descoped) and no tags (none in the world) - the same sensor set for all three
  estimators.
- Route-event detail dropped: the far end is 30 m inside the corridor and is held for 3 s before the return; the
  return is flown in reverse at the same heading (no yaw turn).
- See also the task 6 investigation note below (EKF3 reset timing against the GNSS ON marker).

## F7 (Figure 5.2): caption detail

- Overall RMSE values dropped from the compressed caption (SI-rounded, 3 dp, m): with loop closure, live and
  hindsight overall RMSE over flights 1-3; without loop closure, live overall RMSE over flights 1-3 (all already
  cross-checked by this figure's own `check()` calls against `numbers.md §16.3`, just not restated in the caption
  text).
- "(pre-registered)" qualifier on the extension-experiment mentions, and "(extension experiment)" qualifiers after
  the 4-and-2-tag sentence and the wrong-tag-ID sentence - dropped as repeated context; the sentences' own content
  (the counts, the UKF/FGO ratio) is kept verbatim because three of the retained clauses are asserted, character for
  character, by `docs/thesis/tier1/check_claims_applied.py` (claims C1-C3): "The thesis's EKF3 and UKF, as
  configured, have no landmark states"; "its live error with loop closure was below the no-loop-closure error on the
  same flight in 0/9 runs (6 of 9 runs diverged)"; "loop closure also bounded live drift in 3/3 flights in each".
  These three clauses could not be shortened or reworded without breaking that checker's assertions, so F7's
  caption stays longer than the other four captions in this stage; everything NOT required by that checker was
  still moved out per the normal rule.
- Removed entirely (not required by any checker, confirmed by search): "One estimator, so one colour, with live
  solid/filled and hindsight dashed/open." (restated earlier in the new caption instead) and "The estimator
  validation check (V3) is not re-scorable on the corrected FGO (its labels were never recorded)."

## A1 (Table A.1): caption detail

- Build detail dropped: the UKF earlier build is specifically "pre-jitter fix"; the FGO earlier build is
  specifically "original, hard-gated and robust"; the ablation build is specifically "noise fix only".
- Provenance/date: the final FGO node's corrected-priors re-fly is commit `4c07374b/HEAD`, from the 2026-11-12
  regeneration, and is the table's last row.

## A2 (Table A.2): caption detail

- "(corrected priors)" qualifier after "FGO corrected-priors node" in the first sentence.
- The provenance sentence spliced from the shared `PRIORS` constant (dropped because it names a date): "The FGO
  safety re-tests (corrected-priors node) and the FGO hold and closed-loop corridor results reported as current
  here (the 2026-11-12 regeneration) all used the corrected initial priors; every earlier FGO build, recorded as
  superseded, used the original priors."
- "(superseded: original priors for the FGO column)" qualifier on the comparative-criteria-page final-build sets.
- Cross-reference dropped: "(current numbers: Table 7.1 footnote [i])" after the FGO hold-value-narrows clause.

## A3 (Table A.3): caption detail

- "(noise fix only)" qualifier on the FGO ablation build.
- "the note on the original priors flown by the FGO" clause.
- The provenance sentence spliced from the shared `PRIORS` constant (dropped because it names a date), same text as
  quoted under A2 above.

## Table 4.3 (T4) / Table 4.3b (T4F): detail

- T4 caption: "(D21, D98)" dropped after "no cross-speed comparison is drawn" (both are decision-ruling numbers, not
  thesis figure/table numbers).
- T4 notes: "(D21)" dropped after "No comparison across real-time factors is claimed"; "(4c07374b/HEAD)" dropped
  after "the corrected initial priors" (the FGO build commit hash).
- T4F caption: "(D21, D98)" dropped after "no cross-speed comparison is drawn".
- T4F notes: file/trial names in backticks removed (`cl_a_tex`, `abb0357d`, `cl_ukf_a_tex`) - the sentence now reads
  "EKF3's full real-time flight 1 is the same pre-existing single flight already reported elsewhere; the UKF full
  real-time port has no flight 1 of its own (an earlier, pre-jitter-correction build's full real-time flight,
  +163.0 s, is a different build and is superseded, Table A.1) - this cell is 3 new flights in total, as
  pre-registered." (The dropped tokens named which stored trial each sentence refers to; the +163.0 s value and the
  "different build, superseded" status are both kept.)
- `rowsT4`/`rowsT4F` cells: the "flight 1 as recorded (n = 1; flight 1 of this n = 3 cell): PASS/MISS" aside is
  removed from every no-heading cell. No value is lost: the per-flight list immediately before it (e.g. "flights
  +242.1 s (after window) / +178.9 s (PASS) / +268.3 s (after window)") already states flight 1's own outcome inside
  the same cell.
- `ob_cl()`'s ordering-basis "n" statement (footnote [a] on T4, printed via `ob_cl("a", clean=True)`) is corrected
  from "1 flight per estimator without heading and 3 flights per estimator with heading" to "3 flights per
  estimator without heading and 3 flights per estimator with heading" - the no-heading cells became an n = 3, k/3
  count (not a single flight) when the 2026-11-12 regeneration added them, but `ob_cl()`'s own wording was never
  updated to match until this edit. The non-"clean" code path (used, discarded, for Table 7.1's footnote [j] and for
  the bare `ob_cl("a")` calls under F2/F9, whose return value is never placed in a caption) still carries the old
  "1 flight" wording and the METHODOLOGY line citations - out of scope here (task 8 names T4/T4F only; "other
  tables' tex cleaning is done by the coordinator in the export step"). **Flagged for the coordinator**: Table 7.1's
  own footnote [j] and `docs/thesis/figures_thesis/index.md`'s F7 caption inherit from the same stale wording
  pattern, and `eval/figs_thesis_results.py:467,471,476` (R3's caption) also has three literal "as recorded (n = 1;
  flight 1 of the n = 3 cell)" phrases - all untouched by this stage, all candidates for the same fix.

## Task 6: Figure 5.3 (Experiment O) EKF3 reset timing vs the GNSS ON marker

Read-only investigation; no plotted data, selection rule or number changed.

**Finding: yes, EKF3's reset happens AFTER GNSS returns, by about 4.3 s, consistently across all three flights.**
The GNSS ON vertical marker in the figure is drawn at `x = GNSS ON (bag s) − GNSS OFF (bag s)`, which is 123.08 s
(O_r1), 123.08 s (O_r2) and 123.08 s (O_r3b) — matching the "~123 s" read off the plot. EKF3's own source-set
field (`XKFS.SS`, the dataflash record of which source set EKF3 is using) does not switch back to GPS at that
instant: the nearest `XKFS.SS` change after GNSS ON is at bag time ON + 4.32 s (O_r1), ON + 4.32 s (O_r2) and
ON + 4.28 s (O_r3b). The largest consecutive-sample step in `XKF1`'s own logged (PN, PE) in a [ON − 5 s, ON + 30 s]
window — i.e. the actual position jump, independently recomputed here from each flight's `ardupilot.bin`, using
the same `/imu/time_ref` lower-envelope clock map `figs_thesis.py` already uses for F6/F9 — occurs at EXACTLY the
same sample as that `XKFS.SS` switch, in all three flights: magnitude 4.095 m / 4.104 m / 4.097 m (matching the
stored `tracks."EKF3 live".max_step_after_return_m` of 4.095 / 4.104 / 4.097 m to the metre-level digit, confirming
the independent recomputation and the stored value agree). In the figure's own x-axis convention (time since GNSS
OFF), that jump sits at x = 127.40 s (O_r1), 127.40 s (O_r2) and 127.37 s (O_r3b) — matching the "~127 s" peak read
off the plot; the plotted peak is the last sample of accumulating error immediately before this jump corrects it.

**So the ~4 s gap between the GNSS ON line (123 s) and the EKF3 error peak (127 s) is EKF3's own source-set switch
latency**, not a plotting artefact or a different event: for about 4.3 s after GNSS is physically available again,
EKF3 is still running on its indoor (GPS-denied) source set, during which its error keeps rising, before it
validates and switches sets and the logged position jumps back near truth.

**Reconciling with the quoted `numbers.md` line "EKF3 switched sets at OFF + 4.3 s and ON + 4.4 s":** that exact
phrasing is the SUPERSEDED, pre-correction wording (recorded, as superseded, in `numbers.md`'s own correction
table, next to a note that it was corrected by ruling because the OFF/ON deltas had been transposed). The CURRENT
`numbers.md` line states the corrected values directly: "OFF + 4.3–4.4 s (4.37 / 4.37 / 4.34) and ON + 4.3 s
(4.32 / 4.32 / 4.28)" — i.e. ON + 4.3 s, not ON + 4.4 s. This investigation's own independent measurement (4.32 /
4.32 / 4.28 s) reproduces the CURRENT corrected numbers.md value exactly, not the old transposed one; no new
discrepancy was found. (Source trace, not re-derived here: `AP_NavEKF3_Control.cpp`'s source-set selection is a
discrete state machine gated on GPS-fix-quality timers, separate from `AP_AHRS::active_EKF_type()`, which is why
the logged position only moves once the source-set field itself has already changed, not on the raw GNSS-available
instant.)

**Why the FGO's live track drops at the line instead:** recomputed directly from each flight's `room_fgo/
fgo_live.tum` against `room_ukf/ground_truth.tum` (world frame, no alignment, same as the plotted curve): FGO error
is still 2.42–2.66 m at x = 123.08 s (the GNSS ON line) and has fallen to 0.003–0.013 m by x = 124.08 s, in all
three flights — essentially one sample after the line, not 4+ seconds after it. The FGO ingests each GNSS fix
directly as a factor-graph measurement with no analogous discrete "source set" state machine to switch, so it
starts correcting on the same sample the fix becomes available, instead of waiting out EKF3's internal switch
delay.

(Source trace, confirmed by reading `~/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_Control.cpp` and
`AP_NavEKF3_VehicleStatus.cpp` directly, not assumed: EKF3's GPS source only becomes usable once
`readyToUseGPS()` returns true, which itself requires the quality flag `gpsGoodToAlign` to be true; that flag is
set/cleared in `AP_NavEKF3_VehicleStatus.cpp`/`AP_NavEKF3_Measurements.cpp` by GPS quality checks, not on the raw
fix-available instant, so a multi-second gate between "GPS physically returns" and "EKF3 accepts it" is consistent
with ArduPilot's own source code, though the exact 4.3 s was not traced sample-by-sample through that gate here -
it is measured, from the dataflash, not derived from the gate's internal thresholds.)
