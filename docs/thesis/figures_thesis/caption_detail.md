# Caption detail: material moved out of the thesis figure captions

One block per figure, headed "caption detail". Everything here was removed from the plain 2-4 sentence captions (selection rules, alignment methods, builds, sources, provenance) so it can go into the text or an appendix. Numbers are exactly as in the earlier captions.

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

**So the ~4 s gap between the GNSS ON line (123 s) and the EKF3 error peak (127 s) is the harness's own GNSS
source-switching script, not an EKF3-internal gate.** `sim/scripts/o_source_switch.lua` runs inside SITL,
polling the GPS fix status every 100 ms (`return update, 100`, line 25) and accumulating a one-sided vote
(`VMAX = 20`, line 6; incremented on a bad fix at line 12, decremented on a good fix at line 14) that must reach
40 consecutive same-direction polls before the script calls `ahrs:set_posvelyaw_source_set()` and switches EKF3's
active source set (lines 16-23). A full swing from -20 to +20 (or the reverse) is 40 x 100 ms = 4.0 s, and this is
the dominant component of the measured gap, not any threshold inside EKF3 itself.

Breaking the measured marker-to-source-set-change delay (`eval/results/expO_switch_delay/switch_delay.json`, from
`eval/o_switch_delay.py`, commit a833b53; ON side 4.28/4.32/4.32 s, OFF side 4.34/4.37/4.37 s per flight,
numbers.md wording) into its parts: the GNSS ON/OFF marker to the simulated GPS reporting a changed fix status is
about 0.24-0.33 s (the simulated GPS's own latency); that status change to the script's own vote completing is
about 3.95-4.02 s, matching the script's 40 x 100 ms vote timer almost exactly; and the vote completing to the
first changed `XKFS.SS` dataflash record is a further 0.02-0.09 s (0.04-0.06 s at the GNSS ON event this figure
plots). The dominant ~4.0 s component times out with the harness script's own 40-vote timer, not with any
EKF3-internal threshold.

**Reconciling with the quoted `numbers.md` line "EKF3 switched sets at OFF + 4.3 s and ON + 4.4 s":** that exact
phrasing is the SUPERSEDED, pre-correction wording (recorded, as superseded, in `numbers.md`'s own correction
table, next to a note that it was corrected by ruling because the OFF/ON deltas had been transposed). The CURRENT
`numbers.md` line states the corrected values directly: "OFF + 4.3–4.4 s (4.37 / 4.37 / 4.34) and ON + 4.3 s
(4.32 / 4.32 / 4.28)" — i.e. ON + 4.3 s, not ON + 4.4 s. This investigation's own independent measurement (4.32 /
4.32 / 4.28 s) reproduces the CURRENT corrected numbers.md value exactly, not the old transposed one; no new
discrepancy was found.

**Why the FGO's live track drops at the line instead:** recomputed directly from each flight's `room_fgo/
fgo_live.tum` against `room_ukf/ground_truth.tum` (world frame, no alignment, same as the plotted curve): FGO error
is still 2.42–2.66 m at x = 123.08 s (the GNSS ON line) and has fallen to 0.003–0.013 m by x = 124.08 s, in all
three flights — essentially one sample after the line, not 4+ seconds after it. The FGO ingests each GNSS fix
directly as a factor-graph measurement with no analogous discrete "source set" state machine to switch, so it
starts correcting on the same sample the fix becomes available, instead of waiting out the switch delay the
harness's switching script imposes on EKF3. The UKF replay takes the same approach: every GNSS sample after GNSS
ON is used as it is recorded, with no gate and no reset on return (`src/estimators/room_ukf_replay.py:108-109,
179-191`; the FGO replay likewise, `src/estimators/fgo/room_fgo_replay.py:103-104, 137-147, 168`), so neither the
UKF nor the FGO carries anything equivalent to this delay.

(Mechanism, confirmed from the stored data and the harness script, not re-derived: the script's own "O-switch:
source set 1 (GPS)" log line fires at essentially the same instant as the `XKFS.SS` change in every flight - at
most 0.06 s apart at the GNSS ON event this figure plots (`ev_sitl_s` vs `ss_change_sitl_s`,
`switch_delay.json`) - not ~4 s before it, so the ~4 s gap sits BETWEEN the GPS fix becoming good and the script's
own vote completing, not between the script firing and EKF3 accepting the switch. EKF3's own GPS-validation
machinery (`readyToUseGPS()`/`gpsGoodToAlign`, `AP_NavEKF3_Control.cpp`/`AP_NavEKF3_VehicleStatus.cpp`) is a
separate, faster gate and is not the source of this delay in this harness: here it is the script's own
`ahrs:set_posvelyaw_source_set()` call that moves EKF3 between source sets, not a GPS-quality timer EKF3
evaluates on its own schedule.)


Material removed from the Figure 4.2 (R3), Figure 4.1c (R5) and Figure 4.1d (R6) captions when they were shortened to
plain 2-4 sentence captions, kept here verbatim per the restyle brief ("Everything removed ... goes VERBATIM into a
block in your own file"). Each of the three sections below holds ONLY the removed text, exactly as it last rendered
in `docs/thesis/figures_thesis/captions/<id>.md` before this stage's edit (verified against the `d8d39d4` commit).
Stage B's own commentary (what changed and why, the task 5 recommendation) is kept separately, after the three
blocks, so it is not mixed into material the coordinator merges.

## Figure 4.2: caption detail

> Flights chosen by a rule fixed before plotting: (a) of the 9 textured-floor flights of the standard-sensor dataset
> that all three estimators complete (flights 1–9; flight 10 is unusable for the UKF and FGO), the flight whose mean
> cruise ATE over EKF3, UKF and FGO is the median (5th of 9); (b) the flight of the textured-wall camera dataset
> (textured floor) with the same repeat index as (a) if it exists among its flights 1–3, otherwise the median of
> those three by the mean cruise ATE of the arms drawn solid. Chosen: (a) standard sensors, no heading,
> standard-sensor dataset, textured floor, flight 3 (cross-estimator mean cruise ATEs, ascending, by flight: 6: 1.85,
> 2: 2.42, 1: 4.02, 9: 4.46, 3: 4.58, 4: 4.59, 5: 4.62, 7: 4.64, 8: 4.84 m); (b) with the camera heading (offline
> heading arms), textured-wall camera dataset, textured floor, flight 3 (same repeat index as (a), flight 3).
> Top-down, cruise window only, truth grey. Each estimated path is drawn after a best-fit rotation about the vertical
> and a shift (no scale), fitted over the stored cruise window against its own ground-truth file. This gives the same
> average error as the standard 3D alignment used for the cruise ATE (the RMSE of every plotted path is within
> 0.005 m of its stored cruise ATE; cross-checks), but cannot roll the path about the corridor axis: the 3D fit is
> free to do so on a straight path and can turn sideways drift into up-and-down error that is invisible from above.
> The alignment removes a constant heading offset, so the metres-scale sideways drift of the unaligned estimates
> (Table 4.1, heading-error decomposition) is not shown; an error along the corridor (for example EKF3's
> distance-scale error) lies along the path and barely shows top-down. Dashed: no heading source; solid: with the
> camera heading (offline heading arms, UKF and FGO only); EKF3 is drawn as the no-heading baseline. EKF3's own
> offline heading arm (offline Replay, 5° floor; a separate, later run, D131) is reported in Table 4.1b and is not
> drawn here. The lateral (East) axis is stretched 3.0× relative to the along-corridor axis, the same in both panels;
> no log axes. Passive estimators, truth flying (Experiment 1A/1B offline). Cruise ATE (m): (a) EKF3 4.10, UKF 5.17,
> FGO 4.48 (all no heading); (b) EKF3 4.08 (no heading), UKF 4.96 (no heading) / 0.14 (with heading), FGO 4.54 (no
> heading) / 0.06 (with heading).

## Figure 4.1c: caption detail

> Offline standard-sensor dataset (IMU, downward flow, downward LiDAR; no heading source), textured floor, flight 3,
> chosen by the same rule as Figure 4.2(a), fixed before plotting: of the 9 textured-floor flights that all three
> estimators complete, the flight whose mean cruise ATE over EKF3, UKF and FGO is the median (5th of 9). n = 1 flight
> shown (of 9). Passive estimators, truth flying. (a) Top-down paths from take-off to the end of the cruise window,
> truth grey. Unlike Figure 4.2, the paths are NOT aligned: each estimate is drawn as estimated, in its own
> navigation frame with its origin at take-off, so the sideways drift caused by heading error, which the SE(3)
> alignment of the cruise ATE (and of Figure 4.2) removes, is shown; it reaches tens of metres by the end of the
> cruise. No fitted alignment is applied to any estimate. EKF3 reports North/East directly. The UKF and FGO
> trajectories are expressed in the world frame by a fixed axis relabel from the known take-off heading (the vehicle
> spawns facing North, and both start with yaw 0 along it, so their x is North and their y is West: (North, East) =
> (x, −y)), the same convention as eval/phase5_analysis.py. The East axis is stretched 1.0× relative to North (equal
> scale: the drift is large enough not to need stretching). For reference, each estimator's stored cruise ATE after
> alignment (Figure 4.2): EKF3 4.10 m, UKF 5.17 m, FGO 4.48 m. (b) Along-track error (estimated North − true North)
> and (c) sideways error (estimated East − true East) against the true distance travelled along the corridor, from
> take-off to the end of the cruise window (the stop and landing are not drawn). Truth is interpolated to each
> estimator's own timestamps. (b) and (c) share one y-scale. The along-track error is not a pure scale error: a
> heading error also shortens the North component of the estimated travel. Dashed: no heading source (all three). No
> log axes.
>
> The 9-flight view of the same dataset is in Figure 4.1d (provisional).
>
> Companion table: Table 4.4 (provisional), fitted cruise ATE (registered) and raw world-frame error (descriptive)
> over Experiment 1A flights 1-9 of the standard-sensor dataset, textured floor (this figure shows flight 3 of those
> 9).

## Figure 4.1d: caption detail

> Offline standard-sensor dataset (IMU, downward flow, downward LiDAR; no heading source), textured floor,
> Experiment 1A, all 9 flights (dsn_tex_r1-r9). Passive estimators, truth flying. Each panel is one estimator; every
> one of its 9 flights is drawn, from take-off to the end of its own cruise window. Paths are raw: each estimate is
> drawn exactly as estimated, in its own navigation frame with its origin at take-off, with no fitted alignment (no
> rotation, translation or scale fit). EKF3 reports North/East directly. The UKF and FGO trajectories are expressed
> in the world frame by a fixed axis relabel from the known take-off heading (the vehicle spawns facing North, and
> both start with yaw 0 along it, so their x is North and their y is West: (North, East) = (x, −y)), the same
> convention as Figure 4.1c and eval/phase5_analysis.py. The grey line is the true path (simulator); the black dot is
> take-off, at the origin of every panel. The shaded bands beyond East = ±10 m (CLAUDE.md:101), labelled "wall", are
> the corridor walls. East and North are drawn at equal scale (1.0×); all three panels share the same x- and
> y-limits. Fitted and raw values: Table 4.4 (provisional).

## Stage B notes (not part of the removed-text blocks above — coordinator reading only)

**R3 (Figure 4.2).** Beyond wording, the "D131" decision-number citation is dropped per the binding rule (no
D-numbers on a caption), not merely shortened. The full selection rule, the per-flight ATE ranking table, the
alignment-method explanation (why a yaw-only best-fit is used instead of the registered 3D fit) and the
"Table 4.1/4.1b" cross-references remain fully available in `docs/thesis/figures_thesis/index_results.md`'s own
Caption/Cross-checks sections, which were not shortened. Panel-title change (task 4): the short caption no longer
states that panels (a) and (b) use different flights with different ATEs (4.10/5.17/4.48 m vs 4.08/4.96/4.54 m) — do
not read the two panels' dashed curves as literally identical data; they are two different flights (standard-sensor
dataset flight 3 vs textured-wall camera dataset flight 3) that happen to produce a visually similar heading-error
signature. This is why the new panel titles say "no heading (dashed), aligned by best fit" rather than calling the
two panels' curves the same.

**R5 (Figure 4.1c).** Beyond wording, the frame-derivation paragraph (axis relabel, take-off heading, the
`eval/phase5_analysis.py` cross-reference) and the "for reference" comparison against Figure 4.2's aligned ATEs are
dropped from the caption; the full frame derivation and its PASS/FAIL table remain in
`docs/thesis/figures_thesis/index_drift.md`'s own "Frame check" section, unchanged by this stage.

**R6 (Figure 4.1d).** Beyond wording, the per-trial file-name list ("dsn_tex_r1-r9"), the "CLAUDE.md:101" line
citation and the frame-relabel derivation paragraph are dropped from the caption per the binding rule (no file names
or line citations on a caption) — the full derivation and the file list remain in
`docs/thesis/figures_thesis/index_drift9.md`'s own "Inputs" and "Frame check" sections, unchanged by this stage. The
"same convention as Figure 4.1c" cross-reference is also dropped so this caption stands alone if Figure 4.1c is
dropped (see the task 5 note below); the frame convention itself is unchanged and is still fully documented in
`index_drift9.md`.

Axis-convention change (task 3, R6/Figure 4.1d): the figure's layout changed from three panels side by side (East
horizontal, North vertical — the pre-restyle orientation) to a 2x2 grid, North horizontal (increasing right) and
East vertical (positive up), matching Figures 4.1c and 4.2. The fourth grid cell holds only the truth/take-off
legend. This was necessary, not cosmetic: a true 1:1 aspect over the full ±LIM1 East range (needed to keep both
corridor walls in frame) makes a single row of 3 panels too short to be legible and three stacked rows too tall for
one page; the 2x2 grid is the layout that fits both the equal-scale requirement and the page.

### Task 5 — does Figure 4.1c carry information Figure 4.1d does not?

See the handback report for the full analysis and the recommendation (kept out of this file since it is Stage B's
own reasoning, not removed caption text, and the brief's merge is of the removed-text blocks above only). Short
version: panel (b) (along-track error vs distance) is the only content not duplicated by Figure 4.1d or Table 4.4,
but a check of every place in the thesis that discusses along-track/distance-scale error (`limitations.md`,
`headline_claims_before_after.md`, `numbers.md` §6.5, `glossary.md`) found none of it sourced from or citing this
figure's panel (b) — that prose is all backed by a separate, already-registered distance-scale computation
(`scale_check.json`), not by reading values off this plot. Panel (b) is therefore unique but uncited, which does not
meet the bar for overriding the user's stated default; the recommendation is that the default stands (drop the
whole figure, keep only Figure 4.1d) unless the user wants the sideways-drift-vs-along-track-foreshortening
distinction kept as an illustration in its own right.


Material removed from reader-facing captions during the 2026-11-13 figure restyle (common brief: "Restyle the
thesis figures only", item 7 - captions become plain 2-4 sentences, with everything removed from the previous
caption kept here verbatim). One block per figure, headed `## <figure id>: caption detail`.

## Figure 3.1: caption detail

Scope: `eval/figs_thesis_methods.py`, `fig_architecture()`. The previous (2026-11-02 restyle) caption read, verbatim:

> Sensors (left) reach ArduPilot's flight controller through MAVLink bridges (flow, range, and the
> external-navigation (ExtNav) path for the camera heading or a tag) and reach the UKF and FGO through recorded
> ROS 2 topics. Which estimator flies is set by AHRS_EKF_TYPE: simulator truth in Experiments 1A, 1B, 2, 3 and 4
> (open loop; EKF3 runs live but passively, the UKF and FGO are replayed offline), and EKF3, the UKF port or the
> FGO in Experiments 1C, 5 and 5S (closed loop; the others run in shadow). The FGO runs outside ArduPilot as a
> node whose state an in-firmware output predictor (AP_NavFGO) propagates. In simulation every process ran on
> one desktop; the companion computer (Pi) is planned and its timing is estimated. Two safety watchers: the
> simulation watcher used in Experiments 1C, 5 and 5S, and the real-hardware watcher, tested only on the SITL
> bench.

The 2026-11-13 pass replaced this with 4 plain sentences (no experiment-id enumeration, no `AHRS_EKF_TYPE` or
`AP_NavFGO` named, no file/script names). Nothing beyond the quote above was removed from the caption body.

