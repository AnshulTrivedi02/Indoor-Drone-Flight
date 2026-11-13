# Caption detail — stage B (restyle)

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
