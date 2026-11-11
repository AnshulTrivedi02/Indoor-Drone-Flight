# FGO re-fly with corrected initial priors: results

Registration: `docs/thesis/refly_priors/preregistration.md`, commit `29f6719` (AMENDMENT 1 included in that same
commit). Decisions D127-D130, D138 (gate NOT ATTAINABLE with the recorded data, re-fly proceeds as registered),
D140 (precedent for scoring S2 via `--set b --est <est>` where the registered `--set a` path omits it), D141 (hold
set stopped after two failed runs), D142 (S2 window correction, see section 1). `numbers.md` is unchanged (frozen;
`tools/check_numbers_frozen.py` PASSES, section 6).

**Lead item for the coordinator: a claim comparison, not just a new result.** `numbers.md` reports H1.8 FGO as
PASS (n=1, `cl_fgo_a_tex_half_v3`). This re-fly reports H1.8 FGO PRIMARY at k/3 = 2/3 for the corrected priors
(section 1), using the arm-to-contact S2 window METHODOLOGY already used for that exact cell (D142). An alternative
S2 window (the scorer's own `--set b --est fgo` path, with no `--set a` equivalent) gives k/3 = 0/3 instead; both
are reported, and OQ-R5 asks the coordinator to confirm which is primary. Either way this is a verdict comparison
the coordinator should see, not a silent match.

## 0. Pre-flight verification (all confirmed before any flight; nothing was running at each check)

| Check | Required | Found |
|---|---|---|
| `~/opt/fgo_cpp/bin/fgo_cpp_node` md5 | starts `4c07374b` | `4c07374b5c18ce1eda556d5bb9ad0768` |
| `~/ardupilot_ukf/build/sitl/bin/arduc*` md5 | starts `5f94ea1aa7e2` | `5f94ea1aa7e223f90343c1948d443d32` |
| `git diff 0b25c91 HEAD -- src/estimators/fgo/fgo_node.py src/estimators/fgo/fgo_node_core.py src/estimators/imu_timing.py` | empty | empty (0 lines) |
| `grep -n "YAW0_SIGMA = np.radians(1)\|ROLLPITCH0_SIGMA = np.radians(5)" src/estimators/fgo/fgo_core.py` | both present | both present (lines 44, 48) |
| `eval/closed_loop_score.py cl_fgo_a_tex_half_v3 --set a --est fgo` | reproduces `eval/results/closed_loop_cl_fgo_a_tex_half_v3.json` | EXACT MATCH (`PYTHONPATH=~/.cache/thesis_pyshim ~/venv-evo/bin/python`, the pymavlink shim) |
| `eval/h_score.py H_s3v2_r1 --sigma 0.02` | reproduces `eval/results/expH/s3v2_r1.json` | EXACT MATCH (`~/venv-tags/bin/python3`) |
| `eval/h_comparative_rp.py --check-only` | reproduces `eval/results/expH/h_comparative_2026-10-11.json` | EXACT MATCH |

Launcher `tools/run_fgo_refly_priors.sh` committed before any flight (commits `5679ed6`, `09ab921` for the
run-trial-failed check added before flying); `eval/h_comparative_rp.py` committed before any flight (`1a5fedb`).

## 1. Corridor flights: set 1C without heading (H1.8 FGO)

Flown serially, `cl_fgo_a_tex_r{1,2,3}_half_rp`. All three completed to a west-wall BREACH (`run_trial exit 143`,
"wall contact" first line), the EXPECTED end for this set, so the launcher continued past it (mirroring
`tools/run_cl_extras.sh`'s `exp_contact=1` pattern, as instructed). IMU-gap check (`eval/imu_gap_check.py <trial>
--write`): **3/3 "ok"** (usable; no re-fly needed).

| flight | contact t_rel_cruise_s (3 dp; verdict on the unrounded scorer value) | wall | U1 | U2 | U3 (window [+145,+196] incl.) | S2 (arm to contact, PRIMARY) |
|---|---|---|---|---|---|---|
| `cl_fgo_a_tex_r1_half_rp` | 166.728 | west | PASS | PASS | PASS | 100 % (0/4312 invalid) |
| `cl_fgo_a_tex_r2_half_rp` | 193.884 | west | PASS | PASS | PASS (margin 2.12 s to the edge) | 100 % (0/4991 invalid) |
| `cl_fgo_a_tex_r3_half_rp` | 203.464 | west | PASS | PASS | **MISS** (7.46 s outside) | 100 % (0/5230 invalid) |

- **U2** (`no_contact_before_100s`): true on all three (scorer's `a_primary`).
- **U1** ("no crash, failsafe or loss of control before contact"): `fly_trial.log` shows `Armed.` then `Reached`
  >=1.8 m then `Cruising forward...` on all three (no failsafe/crash line before cruise). The dataflash `ERR`/`MSG`
  stream (`eval/results/closed_loop_extras_s2/failsafe_check.py`, re-used unmodified, D140's method; output saved to
  `eval/results/refly_priors_s2/failsafe_check_output.txt`) shows, on every flight, one early `COMPASS` ECode 0
  (resolved, about 3.3 s after boot, well before arming, benign, the same pattern D140 noted for the UKF set) and
  one `EKFCHECK`/`FAILSAFE_EKFINAV` to "EKF Failsafe: changed to Land Mode" event. Checked against the contact time
  via a clock map recomputed directly from each bag's `/imu/time_ref` with the scorer's own method (not inferred
  from the stored json's `offset_ms_start` alone, which is not the map's intercept; script and output saved,
  `eval/results/refly_priors_s2/s2_to_contact.py`/`.json`): the failsafe occurs **after** contact on all three
  (r1 +0.157 s, r2 +0.151 s, r3 +0.130 s). METHODOLOGY attributes the matching post-contact LAND event on the
  original `cl_fgo_a_tex_half_v2` to the watcher's stop and the node/sim teardown, not to a flight event before
  contact; not independently re-traced here, since no verdict depends on the mechanism (rule 4). **U1 PASS on all
  three** (the failsafe is after contact in every case, not a precursor by timing alone).
- **S2 ("the estimator valid throughout"), PRIMARY window: arming to CONTACT.** The registered wording
  (`3.5_experiments.md:64`, `M:7362-7364`) only says "the estimator is valid throughout" and does not state an
  endpoint for a flight with no clean disarm; `closed_loop_score.py` has no `--set a` S2 code path at all (checked
  in its source). METHODOLOGY reports `cl_fgo_a_tex_half_v2` and `_v3` (the original old-priors no-heading flights)
  as "`XFGO.OV` 100 % from arming to contact", which is the window this cell's original PASS used. Re-derived here
  (not merely cited), with the dataflash `XFGO`/`ARM` stream and the clock map above
  (`eval/results/refly_priors_s2/s2_to_contact.py`/`.json`): it reproduces exactly "100 %, 0 invalid" for both `_v2`
  and `_v3`, then applied the same way to the three new flights, also giving **100 %, 0 invalid samples, on all
  three**. Kept as primary for like-for-like continuity with the original verdict (D142), not as a new reading
  chosen after seeing this re-fly's result; logged as **OQ-R5** for the coordinator, since the registered wording
  itself leaves the endpoint open.
- **Diagnostic only, not primary (kept for transparency): the `--set b --est fgo` arm-to-disarm-or-last-sample
  window (D140's method for an estimator with no `--set a` S2 path) reads 99.81-99.84 % on these three flights**,
  because that window (used for a flight with no clean disarm) extends past contact into the final 0.28-0.36 s of
  recorded output, after `run_trial.sh`'s cleanup starts stopping the FGO node. The same check on the ORIGINAL
  old-priors flight `cl_fgo_a_tex_half_v3` (which never had S2 scored by this method at all, confirmed: no `S2` key
  in its stored json) gives the same pattern, 99.818 % (`eval/results/refly_priors_s2/cl_fgo_a_tex_half_v3_setb_est_fgo.json`).
  On each flight the first invalid sample follows the EKF failsafe/Land-Mode switch above by about 0.02-0.03 s; the
  exact mechanism inside the node's shutdown sequence was not traced further, since the PRIMARY S2 reading above does
  not depend on it (rule 4). The three with-heading flights, which land and disarm normally before the node is
  stopped, score a clean 100 % on this same diagnostic window (section 2). The artefact is not simply "any
  watcher-stopped flight": D140's UKF no-heading set is also watcher-stopped and reads 100 % on its own
  `--set b --est ukf` window (`numbers_extras.md`). It appears specifically on these FGO watcher-stopped flights,
  identically with old and new priors, and is not attributable to the corrected priors.

**H1.8 FGO verdict (U1 AND U2 AND U3 AND S2, each flight; S2 by the arm-to-contact window, D142/OQ-R5):**

- **PRIMARY k/3 = 2/3.** r1 and r2 meet U1, U2, U3 and S2; r3 meets U1, U2 and S2 but misses U3 (203.464 s is
  7.46 s outside the [+145, +196] s window).
- **If the coordinator rules for the scorer's `--set b` window instead (OQ-R5): k/3 = 0/3**, since that window
  reads below 100 % on every flight (section above).
- Spread of the three contact times (descriptive, no criterion): 166.7-203.5 s (range 36.7 s).

S2: PRIMARY (arm to contact) in `eval/results/refly_priors_s2/s2_to_contact.json`; diagnostic (`--set b`) window
in `eval/results/refly_priors_s2/cl_fgo_a_tex_r{1,2,3}_half_rp_setb_est_fgo.json`. U1 checks: saved to
`eval/results/refly_priors_s2/failsafe_check_output.txt` (D140 itself saved its own `failsafe_check_output.txt`;
an earlier draft of this document wrongly said D140 only printed and did not save it, corrected here).

## 2. Corridor flights: set 1C with heading (H1.9 FGO)

Flown serially, `cl_fgo_b_tex_r{1,2,3}_half_rp`. All three completed the full mission and landed (`run_trial exit 0`,
no BREACH). IMU-gap check: **3/3 "ok"**.

| flight | B1 \|x\| flight (m) | B2 \|x\| cruise (m) | B3 yaw err p95/max/mean (deg) | B4 max lat speed (m/s) | B5 gyro rms r/p/y (rad/s) | S2 |
|---|---|---|---|---|---|---|
| `cl_fgo_b_tex_r1_half_rp` | 0.218 | 0.218 | 0.398 / 0.459 / 0.197 | 0.119 | 0.00201 / 0.00168 / 0.00290 | 100.0 % |
| `cl_fgo_b_tex_r2_half_rp` | 0.041 | 0.038 | 0.264 / 0.332 / 0.203 | 0.0076 | 0.00199 / 0.00171 / 0.00287 | 100.0 % |
| `cl_fgo_b_tex_r3_half_rp` | 0.318 | 0.318 | 0.300 / 0.726 / 0.182 | 0.196 | 0.00205 / 0.00164 / 0.00294 | 100.0 % |

All of B1-B5 and S2 PASS on all three flights (scored with the registered call, `--set b --est fgo`, which already
produces S2, the arm-to-disarm-or-last-sample window, no workaround needed here since these flights land and
disarm normally before the node is stopped).

**H1.9 FGO verdict: k/3 = 3/3** (all B1-B5 and S2 met on every flight).

Scores: `eval/results/closed_loop_cl_fgo_b_tex_r{1,2,3}_half_rp.json`.

## 3. IMU-gap results (all six corridor flights)

| flight | verdict |
|---|---|
| `cl_fgo_a_tex_r1_half_rp` | ok |
| `cl_fgo_a_tex_r2_half_rp` | ok |
| `cl_fgo_a_tex_r3_half_rp` | ok |
| `cl_fgo_b_tex_r1_half_rp` | ok |
| `cl_fgo_b_tex_r2_half_rp` | ok |
| `cl_fgo_b_tex_r3_half_rp` | ok |

6/6 "ok" (usable). No `...b` re-fly was needed for any of the six corridor flights.

## 4. Hold flights (H5.1, H5.5, H-H2, P-H3, H-H4): NOT FLOWN, set stopped (D141)

`H_s3rp_r1` failed before any flight began (`run_trial` exit 141, SIGPIPE, immediately after the `FGO_NODE_IMPL=cpp`
branch starts the FGO node, the node itself started and anchored cleanly, confirmed in `fgo_node.log`, and before
`fgo_node_restart.sh` is written). One retry was flown under a new name, `H_s3rp_r1b` (case added and committed to
`tools/run_fgo_refly_priors.sh` while nothing was running, commit `f29e2ee`), on the operating assumption at the time
that this was the project's documented transient JSON-lockstep/connection-reset flake. **It failed identically**
(same exit code, same missing-file signature). Root cause was then identified, not assumed (D141, full detail in
`docs/thesis/tier1/decisions_log.md`): a genuine, reproducible harness bug in `run_trial.sh`'s `FGO_NODE_IMPL=cpp`
branch:

```
ls -t "$AP_TREE/ArduCopter/logs/"*.BIN 2>/dev/null | head -1 | xargs -r basename > "$LOG_DIR/fgo_node_boot.txt"
```

under `set -euo pipefail`. `ls -t` now lists 108 `.BIN` files (6480 bytes, more than one stdio write); if `head -1`
exits after the first write, `ls` can take SIGPIPE on its second, and `pipefail` turns that into the script's `ERR`
trap firing with exit 141. Confirmed empirically: `fgo_node_restart.sh` (the very next statement) is missing on both
`H_s3rp_r1` and `H_s3rp_r1b`, present on the original `H_s3v2_r1` (which had far fewer `.BIN` files at the time,
`fgo_node_boot.txt` reads `00000077.BIN`). Only the C++-node branch has this line, which is why all six Python-node
corridor re-fly flights (sections 1-2) were unaffected. An earlier hypothesis (a generic transient / system memory
pressure) was checked and withdrawn: "ArduPilot controller has reset" also appears 6-8 times in successful flights'
`gazebo.log`, and the 1-minute load average at diagnosis time was 0.30. Checked: no other `| head` pipeline exists
under `set -e` in `run_trial.sh` or `sim/tools/closed_loop_run.sh`.

**Per the pre-registration's own rule ("a breach or failed run stops that set; report it"), the hold set stops here.**
One retry had already been flown past the literal first-failure rule; a second identical failure is reported rather
than retried again blindly. `H_s3rp_r2` and `H_s3rp_r3` were **not flown**. `H_s3rp_r1` and `H_s3rp_r1b` are kept, not
deleted. Two candidate fixes exist (a one-line `run_trial.sh` patch, or moving already-copied `.BIN` files out of the
glob path) but both are outside this agent's remit: the first would contradict D138's "the re-fly flies ... with the
current harness unchanged", the second changes SITL's working environment outside the registered configuration.
Both are left for the coordinator in `docs/thesis/tier1/open_questions.md` (OQ-R4, now listed under STOP items).

**Consequence:** H5.1 (FGO-flying bounds), H5.5 (FGO drift bands), H5.6/H5.7-as-reported, and the comparative
criteria H5.2/H5.3/H5.4a/H5.4b all have **no corrected-priors value**. `eval/h_comparative_rp.py`'s step 1 (gate:
reproduce `h_comparative_2026-10-11.json` exactly from the original files) was run and passed, EXACT MATCH, but
step 2 (recompute with `s3rp_r*`) could not run, since no `s3rp_r*` score files exist.

## 5. Old vs new per criterion

| criterion | original (OLD priors) value and verdict | corrected (NEW) priors value and verdict | verdict changed? |
|---|---|---|---|
| **H1.8 FGO** (no heading) | `cl_fgo_a_tex_half_v3` (n=1): contact +169.9 s west, U1/U2/U3 PASS, S2 100 % arm-to-contact (re-derived here; METHODOLOGY's own stated value for this flight). Published verdict: PASS | n=3: k/3 = 2/3, same S2 window (arm to contact, 100 % on all three). r1, r2 PASS; r3 MISS on U3 alone (window edge, 203.5 s vs the 196 s bound) | **Yes, k/3 = 2/3 against the original's single-flight PASS.** This is a genuine 3-flight spread around the registered window's edge (166.7 to 203.5 s), not an artefact of the S2 method: the SAME arm-to-contact S2 reading is 100 % on every flight checked, old priors and new. Not tested: whether a 3-flight re-fly of the original (old-priors) build would show a similar spread; this report does not claim that it would or would not |
| **H1.9 FGO** (with heading) | `cl_fgo_b_tex_r{1,2,3}_half_v3`: 3/3, ALL B criteria and S2 PASS (numbers.md row; confirmed from stored jsons, section 2 table) | `cl_fgo_b_tex_r{1,2,3}_half_rp`: 3/3, ALL B criteria and S2 PASS | **No** |
| **H5.1** (FGO-flying bounds) | `H_s3v2_r*`: mean 8.1-9.0 mm, max 18-28 mm (H-H1 PASS, numbers.md section 17.1) | **not available** (hold set not flown, section 4) | N/A, blocked |
| **H5.5** (FGO drift bands) | `H_s3v2_r*`: 13/20/17; 7/25/27; 22/15/9; 17/11/18 mm (every band PASSES, numbers.md section 17.1) | **not available** | N/A, blocked |
| **H5.6/H5.7 as reported** | `H_s3v2_r*`: re-lock 0.002-0.032 s PASS; no lockout; jump AS WORDED fails in 4 of 12 losses; yaw wander over the 30 s loss -0.23/+0.52/+0.52 deg (<=3 deg, PASS) | **not available** | N/A, blocked |
| **H-H2** | FAIL (0/3): FGO highest in all three runs, 8.3-8.6 mm against EKF3 7.8-7.9 mm (`h_comparative_2026-10-11.json`) | **not available** | N/A, blocked |
| **P-H3** | FAIL (0/3): UKF 2.40-2.58x, FGO 2.10-2.37x EKF3's hold gyro activity | **not available** | N/A, blocked |
| **H-H4 (15 s)** | FAIL (0/3): EKF3 strictly smallest (5/5/7 mm) against UKF 20-30, FGO 7-30 mm | **not available** | N/A, blocked |
| **H-H4 (5 s)** | FAIL (0/3): EKF3 4-5 mm against UKF 7-16, FGO 11-34 mm (max/min 3.2-7.7) | **not available** | N/A, blocked |

The originals above are labelled **"superseded: original priors"** per the pre-registration's convention (D129); none
of their directories, score files or `numbers.md` rows were renamed, edited or deleted.

## 6. Checksum guard

`python3 tools/check_numbers_frozen.py`: **PASS** (run after all scoring above, re-run after the S2-window
correction in section 1, before this document's final commit).

## 7. Summary

- Corridor re-fly: **6/6 flights flown, all IMU-ok, both sets scored.** H1.9 (with heading) is unchanged at 3/3.
  H1.8 (no heading) reads **k/3 = 2/3**, using the same arm-to-contact S2 window METHODOLOGY already applied to the
  original cell, against the original's published single-flight PASS: see the lead item at the top of this document
  and the old-vs-new row above.
- Hold re-fly: **blocked after two failed runs**, root cause identified as a harness bug (D141), not flown past
  `H_s3rp_r1b`. `H5.1`, `H5.5`, `H5.6/H5.7`, `H-H2`, `P-H3`, `H-H4a/b` for the corrected-prior FGO hold set are
  **not available**.
- No frozen material was touched. `check_numbers_frozen.py` PASSES.
- **Corrections to this document's own history, disclosed rather than silently fixed (git safety protocol: no
  amending commits):** commit `f29e2ee`'s message attributed `H_s3rp_r1b`'s retry to a generic transient flake;
  D141 identifies the actual cause (the harness bug above). Commit `aecd390`'s message said "D140's own flights
  disarmed normally"; D140's UKF no-heading set did NOT disarm normally either (it is also watcher-stopped) and
  reads 100 % on its own window regardless, corrected in section 1 above. Section 1's S2 window itself was also
  corrected once between commits `31314e9` and `aecd390` (strict `--set b` reading as primary, 0/3) and then again
  in this version (arm-to-contact as primary, per D142, 2/3); the full history is in the three commits' messages
  and D141/D142.
