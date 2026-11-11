# Tier-1 extension experiments: open questions for the user

These are non-blocking questions collected under the standing decision rules (2026-10-23). They go into the morning
digest. Each one says what is being done meanwhile. STOP items, if any, are listed first and marked **STOP**.

## STOP items

- **OQ-R4 (FGO prior re-fly hold set, STOP, blocking H5.1/H5.5/H-H2/P-H3/H-H4 for the new FGO priors):** `H_s3rp_r1`
  and its retry `H_s3rp_r1b` both failed before any flight began, root cause identified (D141): `run_trial.sh`'s
  `ls -t "$AP_TREE/ArduCopter/logs/"*.BIN | head -1 | xargs -r basename > fgo_node_boot.txt` line, only reached by the
  `FGO_NODE_IMPL=cpp` branch, can SIGPIPE `ls` once the glob's output (now 6480 bytes for 108 files) needs more than
  one stdio write and `head -1` exits after the first; `set -euo pipefail` turns that into a 141 exit via the `ERR`
  trap. The 6 Python-node corridor re-fly flights are unaffected (no such line on that branch). Candidate fixes,
  either outside this agent's remit per D141:
  (a) one-line `run_trial.sh` patch, `head -1` to `sed -n 1p` (reads all input, so `ls` never gets SIGPIPE; no
      behaviour change otherwise), contradicts D138's "the re-fly flies ... with the current harness unchanged";
  (b) move the already-copied `.BIN` files older than the re-fly out of `~/ardupilot_ukf/ArduCopter/logs/` into a
      subdirectory (not delete) so the glob's output shrinks back under one write, changes SITL's own working
      directory outside the registered configuration, though it touches nothing under `~/thesis_data`.
  Checked (D141): no other `| head` pipeline exists under `set -e` in `run_trial.sh` or `sim/tools/closed_loop_run.sh`,
  so this is the only instance of the latent bug on this path.
  Meanwhile: `H_s3rp_r1`/`H_s3rp_r1b` are kept; `H_s3rp_r2`/`H_s3rp_r3` and the hold-set scoring are not flown/run.

| # | raised (AEDT) | question | default being followed meanwhile | blocks anything? |
|---|---|---|---|---|

**Answered:**
- **Q1 (user, 2026-10-23):** yes. Thesis tables use SI units, converted at generation time only; numbers.md stays exactly as is. Use one unit per quantity, the same in a table as in its matching figure. SI prefixes are fine where they read better (e.g. drift in mm, position error in m): pick the readable unit and use it consistently. Keep the exact cross-check against the stored values. → done: units pass merged 2026-10-23 (2dcee76); decisions D7, D8.
- **Q2 (user, 2026-10-24):** "scope the claim: "In the corridor configuration, 0.25 s was the largest window within the 33 ms budget; on the tag-room flights 0.5 s also fitted (27-28 ms)." No general claim." → done: `methodology_factsheets/3.3_estimators.md` (en dash, D20); see `claims_applied.md`.
- **Q3 (user, 2026-10-24):** add to limitations.md: "The FGO as configured (plain least squares, tag readings ungated) is not robust to wrong tag IDs: at 1% wrong IDs, 6 of 9 runs diverged and the remaining 3 ended 51-85x the clean error (H-E3.1 FAIL, 0/9). A robust-weighted variant avoided divergence in all 21 runs, though one collapsed. The landmark UKF (E5) was not tested with wrong IDs." → done verbatim as limitation 3, with a scope note: 51–85× is the range over all 12 non-diverged plain runs (1% and 5%); the 3 at 1% are 51.26–75.23× (D19).
- **C1–C5 (user, 2026-10-24):** "accepted as proposed. Apply to the thesis files at the listed lines; the existing claims table and frozen documents are not edited (apply to thesis-facing outputs only, with a mapping note)." → done: `claims_applied.md`.
- **D17 / claims_update open point 4 (user, 2026-10-24):** the T1 Experiment 3 UKF cell names the variant: "UKF with landmark states (extension E5): bounded; ~2x FGO error", footnoted [k] as an extension variant, not the UKF used elsewhere (measured 1.76–2.08×, LC live, descriptive) → done.
- **D16 (claims_update open point 1):** accepted with C2 as proposed (no claim that the robust arm keeps the loop-closure advantage).
- No further experiment stages are planned (user, 2026-10-24).
- **Q4 (user, 2026-10-24):** yes: limitations.md item 3 now reads "51-75x" (the 3 non-diverged 1% runs: 51.26, 65.59, 75.23); the scope note keeps 51.26–85.49× for all 12 non-diverged runs at 1% and 5%. Searched all thesis-facing material for "51-85"/"51–85": limitations.md item 3 was the only instance describing only the 1% runs (see claims_applied.md §Q4). check_claims_update.py pinned to 181f156.
- **D43 (user, 2026-10-25):** the ablation gate override is accepted.
- **A-Q8 (user, 2026-10-25):** accept P1's qualification as pre-registered; no investigation.
- **A-Q9 (user, 2026-10-25):** stop. Separating the remaining FGO–UKF differences is future work.
- **A-Q10 (user, 2026-10-25):** yes. One exploratory paragraph added to `docs/thesis/discussion_material.md` §1 (new file), verbatim, with every number traced to ablation_numbers.md (`ablation/check_discussion.py` 13/13). See A-Q12 for a wording point.
- **A-Q11 (user, 2026-10-25):** yes, delete after re-verifying the originals against the guard manifest. The manifest does not cover the bags, so this is re-asked as A-Q11b.
- **Morning digest job (user, 2026-10-25):** stopped; no further stages planned.
- **A-Q11b (user, 2026-10-25):** delete. `~/thesis_data/ablation/bags/` (19 GB, plain copies: 0 symlinks, 0 hard links) was deleted. Verification basis: the originals were checked against `PACKED.txt` (2026-10-08): decompressed sha256 and .zst size match on 6/6. The guard manifest excludes `bag/`. The record is `~/thesis_data/ablation/bags_DELETED.txt`. The originals are untouched.
- **A-Q12 (user, 2026-10-25):** the last sentence of discussion_material.md §1 is replaced with the user's corrected wording ("…beyond the noise band on one flight (by about 0.4 m), and by up to 1.3 m on another, within that flight's wide noise band."), recorded as a correction of the user's own wording. The scope note is removed and both numbers are traced. check_discussion.py 18/18.

## Open from the overnight run (2026-11-03; coordinator, for the user)
- **ON-1 (stale line citations in dated records):** stage 2 found line-number citations in `tier1/claims_applied.md` and `tier1/claims_update.md` that point into `tables/T1_scorecard.md` and the generators, and that have moved (some were already stale before tonight). Both files are dated records. Options: leave as dated snapshots (recommended; their own header dates them), or add a dated erratum mapping old to new lines (the mapping is in `docs/handovers/2026-11-02_raw_tables_stage2.md`).
- **ON-2 (R3 spacing):** Figure 4.2 (R3) has about 0.75 in of empty space under its shared legend. Cosmetic; tighten in the final layout pass?
- **ON-3 (caption check scope):** `eval/caption_verdict_check.py` catches the literal verdict words only, not a verdict restated in other words. The eight captions were also reviewed by eye (three review rounds). Accept as is?
- **ON-4 (information only):** during stage 2, three `eval/figs_thesis.py` processes the stage-2 agent had not launched appeared in its worktree; it stopped them. The committed tables come from a later single clean run and pass check_raw_tables 79/79, and the coordinator recomputed Table 4.4 independently. No action needed unless it recurs.
- **ON-5 (numbering):** Table 4.4 and Figure 4.1c are provisional labels, joining Figure 4.1b and Figure 4.2; final numbers are assigned once the chapter plan is locked (standing ruling).
- **ON-1 to ON-5 (user, 2026-11-03):** "agree with your recommendations. ON-2 in the final layout pass." ON-1: claims_applied.md / claims_update.md stay as dated snapshots. ON-2: R3 legend spacing is tightened in the final layout pass. ON-3: caption check accepted as is. ON-4: information only. ON-5: provisional numbering as standing.
- **Fitted-vs-raw tables (user, 2026-11-03, item 1):** both survive; they cover different flight sets (decision D121). Table 4.4 (T9): Experiment 1A flights 1-9; walkthrough page 05 table: Experiment 1B flights 1-3. Each header and caption now names its flight set.

## 2026-11-11 (FGO prior re-fly, closed-loop extras, EKF3 heading Replay, gating count)
- **OQ-R1 (H5.1 scope for the FGO re-fly):** the registered H5.1 names EKF3 flying; the re-fly applies its bounds to the FGO-flying hold set, as the S3v2 rows did (numbers.md:646). Reported as such, not as the primary H5.1 verdict. Confirm or rule otherwise.
- **OQ-R2 (EKF3 half-speed registration timing):** the EKF3 half real-time re-registration commit (`a3f54c7`) and the flight start carry the same timestamp (22:42:01, 2026-09-30). Proposed wording: "registered immediately before the flight". Confirm.
- **OQ-R3 (D70 panel after the EKF3 heading Replay):** keep the closed-loop picture-only panel, replace it with the scored offline EKF3 heading arm, or show both? Decided after the Replay results.
- **OQ-R5 (H1.8 FGO re-fly: S2 gating, S2 window, and the set-level mapping, not a STOP):** three questions.
  (1) Does S2 gate the H1.8 k/3 count? The pre-registration section 3.1's first bullet defines the FGO rule
  including "S2, the estimator valid throughout"; its second, count-defining bullet says only "the count of
  flights that meet U1, U2 and U3 (k/3)" (S2 omitted). Genuinely ambiguous. D142's default, per rule 2 (read
  ambiguity against the hypothesis), treats S2 as GATING. (2) If S2 gates, which window: the window already
  established for this exact cell (`cl_fgo_a_tex_half_v2`/`_v3`, "100% from arming to contact", re-derived here
  and reproducing their reported values exactly) or the scorer's `--set b --est fgo` substitute window (D140's
  precedent for a different estimator shape, never applied to this cell before; 99.81-99.84% on these flights and
  on the original `_v3` once checked the same way). D142's default uses the cell's own established window, since
  switching to an untested substitute is a second, separate choice not compelled by rule 2. **Under that default,
  k/3 = 2/3 regardless of (1)**, since S2 is 100% on the established window on every flight; k/3 = 0/3 only if the
  coordinator wants BOTH S2 gating AND the substitute window. (3) H1.8, unlike H1.9 ("a set passes iff all 3
  flights pass"), has NO registered set-level PASS/NOT MET threshold, only "reported as the count (k/3)"; whether
  2/3 (or 0/3) maps to a TA_verdicts-style PASS or NOT MET for this set is the coordinator's call, not made here.
  All readings reported in `docs/thesis/refly_priors/numbers_refly.md` section 1. Confirm or rule otherwise.
- **OQ-R6 (tier-1 checksum guard verdict on the FGO re-fly's own outputs, not a STOP, but flagged since a
  guard-fails-with-no-safe-default is a listed STOP condition):** `tools/tier1_checksum_guard.py verify` against
  the latest pre-existing manifest (`frozen_manifest_20261022T002851.json`, taken 2026-10-22 by a different
  workstream) reports `"verdict": "DIFFERENT: STOP AND REPORT"`, with 0 changed, 0 missing, 0 errors and 30 added
  files across the 13253 files its specs cover (`eval/results` is covered in full, not just `expL`/`expT`, so this
  task's new `eval/results/closed_loop_*` and `*_s2/` outputs are in scope). No prior `verify` run in this project
  shows an added-only (non-IDENTICAL) outcome being treated as acceptable; the tool's own stated semantics are
  that ANY difference, including an addition, is "STOP AND REPORT". This re-fly never took its own pre-task
  snapshot (the brief and pre-registration do not mention this guard), so running `verify` against a three-week-old
  manifest from an unrelated tier-1 (Experiment 2/3) workstream will show many legitimate additions from the
  intervening weeks regardless of what this task did; the 0 changed / 0 missing / 0 errors is the part that
  actually bears on integrity (nothing existing was touched), and that reads clean. Report saved at
  `docs/thesis/tier1/frozen_manifest_20261022T002851_verify_fgo_refly_priors_20261111.json`. Flagged rather than
  treated as a self-resolved non-issue, since the coordinator may want a dedicated before/after pair for future
  tasks that touch `eval/results`.
- **OQ-R4, OQ-R5, OQ-R6 resolved (coordinator, 2026-11-11, standing rules):** D143 (harness fix, hold flights continue; pre-registration AMENDMENT 2), D144 (H1.8 reported as k/3 = 2/3, no set threshold), D145 (checksum guard added-only accepted).
