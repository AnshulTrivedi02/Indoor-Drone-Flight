# FGO re-fly with corrected initial priors: results

Registration: `docs/thesis/refly_priors/preregistration.md`, commit `29f6719` (AMENDMENT 1 included in that same
commit), **AMENDMENT 2** (commit `1446ba1`, the `run_trial.sh` pipefail/SIGPIPE harness fix, D143-D145, hold flights
continue as `r1c`/`r2`/`r3`). Decisions D127-D130, D138 (gate NOT ATTAINABLE with the recorded data, re-fly proceeds
as registered), D140 (precedent for scoring S2 via `--set b --est <est>` where the registered `--set a` path omits
it), D141 (hold set initially stopped after two failed runs), D142 (whether S2 gates the H1.8 FGO count, and if so
which window; see section 1), D143 (harness fix), D144 (H1.8 set result confirmed), D145 (checksum guard
added-only disclosure). `numbers.md` is unchanged (frozen; `tools/check_numbers_frozen.py` PASSES, section 6).

**Hold set completed in this continuation.** Section 4 was empty ("NOT FLOWN, set stopped") when this agent took
over; `H_s3rp_r1c`, `H_s3rp_r2` and `H_s3rp_r3` all flew cleanly after the AMENDMENT 2 harness fix, and are scored in
section 4 below. No criterion's verdict changed from the original S3v2 set (H5.1, H5.5, H5.6, H5.7, H-H2, P-H3,
H-H4a, H-H4b all read the same PASS/FAIL as before); see section 5 for the full old-vs-new table.

**Lead item for the coordinator: a claim comparison, not just a new result.** `numbers.md` reports H1.8 FGO as
PASS (n=1, `cl_fgo_a_tex_half_v3`). This re-fly reports H1.8 FGO PRIMARY at **k/3 = 2/3** for the corrected priors
(section 1): r1 and r2 meet U1, U2 and U3; r3 misses U3 alone (203.464 s, outside [+145, +196]). Whether S2 gates
this count is genuinely ambiguous in the pre-registration (D142; OQ-R5), but it does not change the number: S2 is
100% on the window already established for this cell (METHODOLOGY's own `cl_fgo_a_tex_half_v2`/`_v3` entries), so
gating with that window still gives 2/3. Only gating AND substituting a different, untested window (never applied
to this cell before) would give 0/3; both readings are reported (section 1), and OQ-R5 asks the coordinator to
rule on the gating and the window. **H1.8 also has no registered set-level PASS/NOT MET threshold** (unlike
H1.9's explicit "3/3"), so whether 2/3 (or 0/3) maps to a set-level PASS or NOT MET is also the coordinator's
call, not made here. Either way this is a verdict comparison the coordinator should see, not a silent match.

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
- **S2 ("the estimator valid throughout"): whether it gates the k/3 count is genuinely ambiguous in the
  pre-registration (D142/OQ-R5); either way, reported per flight.** Section 3.1's first bullet defines the FGO
  rule including "S2, the estimator valid throughout"; its second, count-defining bullet says only "the count of
  flights that meet U1, U2 and U3 (k/3)" (S2 omitted). `3.5_experiments.md:64` (the FGO bullet) likewise omits S2
  (line 63, which does mention S2, is the UKF bullet above it, not the FGO one). Per rule 2 (read ambiguity against
  the hypothesis), D142 treats S2 as GATING, on the window already established for this cell, not a substitute:
  - **Arm-to-contact** (the window METHODOLOGY's own entries for this exact cell, `cl_fgo_a_tex_half_v2`/`_v3`,
    report: "`XFGO.OV` 100 % from arming to contact", the ONLY window ever actually applied to this cell).
    Re-derived here, not merely cited, with the dataflash `XFGO`/`ARM` stream and a clock map recomputed from each
    bag's `/imu/time_ref` (`eval/results/refly_priors_s2/s2_to_contact.py`/`.json`): reproduces exactly "100 %, 0
    invalid" for both `_v2` and `_v3`, and gives **100 %, 0 invalid samples** on all three new flights too. Gating
    on this window changes nothing (still 2/3, since S2 is 100 % on every flight).
  - **Disclosed secondary reading, not primary: the scorer's `--set b --est fgo` arm-to-disarm-or-last-sample
    window** (D140's method, built for a different estimator shape, never applied to this cell before) reads
    **99.81-99.84 %** on these three flights, because that window extends past contact into the final 0.28-0.36 s
    of recorded output, after `run_trial.sh`'s cleanup starts stopping the FGO node. The same check on the
    original `cl_fgo_a_tex_half_v3` (which never had S2 scored by this method at all, confirmed: no `S2` key in
    its stored json) gives the same pattern, 99.818 % (`eval/results/refly_priors_s2/cl_fgo_a_tex_half_v3_setb_est_fgo.json`).
    On each flight the first invalid sample follows the EKF failsafe/Land-Mode switch above by about 0.02-0.03 s;
    the exact mechanism inside the node's shutdown sequence was not traced further (rule 4). The three
    with-heading flights, which land and disarm normally before the node is stopped, score a clean 100 % on this
    same window (section 2). The artefact is not simply "any watcher-stopped flight": D140's UKF no-heading set is
    also watcher-stopped and reads 100 % on its own `--set b --est ukf` window (`numbers_extras.md`). It appears
    specifically on these FGO watcher-stopped flights, identically with old and new priors, and is not
    attributable to the corrected priors. **Using this window instead, AND gating on it, would give k/3 = 0/3.**

**H1.8 FGO verdict:**

- **PRIMARY k/3 = 2/3** (S2 gating, per rule 2, on the cell's own established arm-to-contact window; equally,
  the registered formula's literal U1/U2/U3-only count, if S2 is read as not gating at all, gives the same 2/3).
  r1 and r2 meet U1, U2, U3 (and S2); r3 meets U1, U2 (and S2) but misses U3 alone (203.464 s is 7.46 s outside the
  [+145, +196] s window).
- **k/3 = 0/3 only if the coordinator separately rules for BOTH S2 gating AND the `--set b` substitute window**
  (OQ-R5); this combination was never applied to this cell before the re-fly.
- **H1.8 has no registered set-level PASS/NOT MET threshold** (unlike H1.9's explicit "a set passes iff all 3
  flights pass"); mapping 2/3 (or 0/3) to a set-level verdict is the coordinator's call, not made here.
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

6/6 "ok" (usable). No `...b` re-fly was needed for any of the six corridor flights. `eval/imu_gap_check.py` was NOT
run on `H_s3rp_r1` or `H_s3rp_r1b` (section 4): both failed before `run_trial.sh` reached "Full stack up", so bag
recording never started and there is no bag for the check to read.

## 4. Hold flights (H5.1, H5.5, H-H2, P-H3, H-H4): FLOWN as `H_s3rp_r1c`, `r2`, `r3` (AMENDMENT 2, D143-D145)

**Launch history.** `H_s3rp_r1` failed before any flight began (`run_trial` exit 141, SIGPIPE, immediately after the
`FGO_NODE_IMPL=cpp` branch starts the FGO node, the node itself started and anchored cleanly, confirmed in
`fgo_node.log`, and before `fgo_node_restart.sh` is written). One retry was flown under a new name, `H_s3rp_r1b`
(case added and committed to `tools/run_fgo_refly_priors.sh` while nothing was running, commit `f29e2ee`), on the
operating assumption at the time that this was the project's documented transient JSON-lockstep/connection-reset
flake. **It failed identically** (same exit code, same missing-file signature). Root cause was then identified, not
assumed (D141, full detail in `docs/thesis/tier1/decisions_log.md`): a genuine, reproducible harness bug in
`run_trial.sh`'s `FGO_NODE_IMPL=cpp` branch:

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

**AMENDMENT 2 (D143) fixed the harness bug** (`head -1` -> `sed -n 1p`, same output, committed `1446ba1`) without
changing the registered error model (rule 3: a harness bug is fixed, not an estimator result). `H_s3rp_r1` and
`H_s3rp_r1b` are kept, not deleted or re-flown further; a third case, `H_s3rp_r1c`, was added to
`tools/run_fgo_refly_priors.sh` (identical command to `H_s3rp_r1`/`r2`/`r3`, commit `25ae937`, nothing running at the
time) and stands in for `H_s3rp_r1` in the registered 3-flight hold set. **All three hold flights then flew cleanly:
`H_s3rp_r1c`, `H_s3rp_r2`, `H_s3rp_r3`, all `run_trial exit 0; watcher exit 0`, no BREACH, landed and disarmed
normally.** Pre-flight verification was re-checked immediately before flying (fresh, not reused from section 0):
`fgo_cpp_node` md5 `4c07374b5c18ce1eda556d5bb9ad0768`, `arducopter` md5 `5f94ea1aa7e223f90343c1948d443d32` (both
match); `run_trial.sh:433` confirmed to read `sed -n 1p` (the fix is in the tree the flights ran); `BUILD_LOCK`
absent. The S3v2 reproduction check was **re-run with the exact scoring command this task uses (including
`--profile`, which section 0's original check omitted)**: `eval/h_score.py H_s3v2_r{1,2,3} --profile
batches/expH/s1_far_profile.json --sigma 0.02` reproduces `eval/results/expH/s3v2_r{1,2,3}.json` EXACTLY on all
three (not just r1); confirmed `h_score.py` writes nothing into the trial directories (no new/changed files under
`~/thesis_data/trials/H_s3v2_r*/`).

**IMU-gap results (`eval/imu_gap_check.py <trial> --write`):**

| flight | verdict | reason / detail |
|---|---|---|
| `H_s3rp_r1c` | **trim** | one 1976.5 ms gap before arming (`before_arm: true`); `replay_start_s` 24.898, well clear of arming at 47.155 s -> usable, not unusable; no re-fly needed |
| `H_s3rp_r2` | **ok** | no gaps |
| `H_s3rp_r3` | **ok** | no gaps |

3/3 usable (none "unusable"); no `<name>b` re-fly was needed. This is a different, closed-loop-flight check than the
original `H_s3v2_r*` flights ran: no `imu_gaps.json` exists for any `H_s3v2_r*` trial (confirmed; the check was never
run on them), so there is no prior verdict to compare against.

**Scoring.** `eval/h_score.py <trial> --profile batches/expH/s1_far_profile.json --sigma 0.02 --json
eval/results/expH/s3rp_r<k>.json`, with the mapping **`H_s3rp_r1c` -> `s3rp_r1.json`, `H_s3rp_r2` -> `s3rp_r2.json`,
`H_s3rp_r3` -> `s3rp_r3.json`** (as instructed, `r1c` stands in for the registered `r1` slot; `eval/h_comparative_rp.py`'s
`NEW_SETS` already expects exactly these three file names).

### 4.1 H5.1 (hold accuracy, FGO-flying)

"mean hold error <= 0.05 m and max <= 0.15 m in every pre-loss hold window, 3/3 flights" (`TA_verdicts.md:44`,
applied to the FGO-flying set exactly as the original S3v2 rows did).

| flight | window 1 mean / max (mm) | window 2 mean / max (mm) |
|---|---|---|
| `s3rp_r1` (`H_s3rp_r1c`) | 7.396 / 21.133 | 7.220 / 15.004 |
| `s3rp_r2` (`H_s3rp_r2`) | 8.719 / 25.511 | 7.961 / 19.031 |
| `s3rp_r3` (`H_s3rp_r3`) | 7.119 / 20.720 | 7.857 / 22.800 |

Range across all 6 windows: mean 7.1-8.7 mm, max 15.0-25.5 mm. Every window inside the 50/150 mm bounds.
**H5.1 (FGO-flying): PASS, 3/3** (unrounded values checked against the bounds; display rounded above).

### 4.2 H5.5 (FGO drift bands) and H5.6/H5.7 as reported for S3v2

Bands: 5 s <= 50 mm, 15 s <= 100 mm, 30 s <= 200 mm, move (~7 s) <= 150 mm (`TA_verdicts.md:49`).

**Drift at end of loss (mm), r1/r2/r3 per loss type:**

| loss | r1 | r2 | r3 | band | verdict |
|---|---|---|---|---|---|
| 5 s | 20.175 | 20.158 | 19.132 | 50 | PASS |
| 15 s | 21.873 | 6.535 | 5.537 | 100 | PASS |
| 30 s | 8.583 | 11.635 | 28.157 | 200 | PASS |
| move (~7 s) | 2.967 | 24.198 | 1.142 | 150 | PASS |

**Effective drift (last fix -> first returning fix), mm, r1/r2/r3, also reported:**

| loss | r1 | r2 | r3 |
|---|---|---|---|
| 5 s | 19.275 | 19.342 | 18.278 |
| 15 s | 22.811 | 6.683 | 5.421 |
| 30 s | 8.465 | 11.685 | 28.290 |
| move | 2.803 | 23.243 | 0.992 |

**Every band PASSES on both metrics, all 12 losses (H5.5 FGO bands: PASS).** The individual numbers moved around
relative to the original S3v2 set (end-of-loss 13/20/17; 7/25/27; 22/15/9; 17/11/18 mm) without a consistent
direction per loss type; the band verdict is unaffected either way.

**H5.6 redefined primary (re-lock, effective, from the first returning tag detection to the first FGO keyframe that
fuses it): band <= 0.1 s.**

| flight | 5 s | 15 s | 30 s | move |
|---|---|---|---|---|
| r1 | 14.5 ms | 2.8 ms | 11.5 ms | 20.2 ms |
| r2 | 24.7 ms | 21.3 ms | 29.0 ms | 3.0 ms |
| r3 | 25.3 ms | 8.0 ms | 30.3 ms | 6.7 ms |

Range 2.8-30.3 ms, all << 100 ms. **H5.6 redefined primary: PASS, 12/12** (original S3v2: 0.002-0.032 s, i.e. the
same ~2-32 ms range; unchanged).

**Lockout (H5.7): none in any of the 12 losses (PASS).** Matches the original (no lockout).

**H5.6 jump criterion kept as worded** (largest single step in the 2 s after re-lock <= the accumulated effective
drift at re-lock; both figures below in mm, jump/drift):

| loss | r1 | r2 | r3 |
|---|---|---|---|
| 5 s | 21/19 FAIL | 10/19 PASS | 17/18 PASS |
| 15 s | 24/23 FAIL | 7/7 FAIL | 8/5 FAIL |
| 30 s | 12/8 FAIL | 11/12 PASS | 19/28 PASS |
| move | 6/3 FAIL | 25/23 FAIL | 8/1 FAIL |

**Fails in 8 of 12 losses** (r1: all 4; r2: 15 s and move; r3: 15 s and move) — descriptive, as worded, no set-level
threshold registered for this part (same convention as the original, which reported "fails in 4 of 12 losses"). The
fail count roughly doubled (8 vs 4); flagged descriptively, not claimed as a verdict change (this part carries no
PASS/FAIL set threshold in either flight).

**30 s-loss yaw wander.** No script computing this was found committed anywhere in the repository history for the
original S3v2 figures (`-0.23/+0.52/+0.52 deg`): `eval/h_score.py` has no "wander" field (confirmed by reading it and
by `git show 55edd75 -- eval/h_score.py`, the commit that added the XFGO track, which added no such field), so the
original number was evidently computed ad hoc and never persisted. Re-derived here with a new script
(`eval/results/refly_priors_s2/yaw_wander_30s.py`, same clock map and XFGO `OV==1` track `h_score.py` itself builds,
signed wrapped yaw at the loss's `t_off` minus yaw at `t_on` for the duration-closest-to-30-s loss) which gives:

| flight | yaw wander (deg) |
|---|---|
| r1 | +0.009 |
| r2 | -0.004 |
| r3 | +0.001 |

**Could not exactly reproduce the original -0.23/+0.52/+0.52 deg figures**; both the original and this re-derivation
are far inside the <= 3 deg band, so **PASS either way**, and per standing rule 4 ("spend no machine time on checks
that no verdict depends on") no further time was spent chasing the exact original method once it was established
that no definitional choice here changes the PASS verdict. Flagged as not exactly reproducible, not resolved as a
match.

### 4.3 Comparative criteria H5.2/H5.3/H5.4a/H5.4b

`eval/h_comparative_rp.py`, step 1 gate (reproduce `h_comparative_2026-10-11.json` exactly from the original files):
**EXACT MATCH** (re-confirmed; see section 0 for the earlier `--check-only` run). Step 2, recomputed with
`s3rp_r{1,2,3}` in place of `s3v2_r{1,2,3}` (EKF3 = `s1far_r1/r2/r3b`, UKF = `s2v2_r{1,2,3}`, unchanged, paired by run
index): output saved `eval/results/expH/h_comparative_refly_priors.json`.

| criterion | result |
|---|---|
| H-H2 (FGO holds tightest) | FAIL (0/3 FGO lowest); `lowest_hold` = UKF on all 3 runs |
| P-H3 (gyro activity within 1.5x) | FAIL (0/3); ratios 2.402 / 2.577 / 2.499 |
| H-H4, 15 s (EKF3 jumps most) | FAIL (0/3 EKF3 largest) |
| H-H4, 5 s (jumps within 1.5x) | FAIL (0/3); ratios 5.135 / 2.144 / 3.411 |

**Underlying numbers (hold mean mm, per run):** EKF3 7.756/7.926/7.840 (unchanged); UKF 6.399/7.113/6.729
(unchanged); **FGO (new, s3rp) 7.308/8.340/7.488** against **FGO (old, s3v2) 8.296/8.288/8.559**. UKF is lowest in
all three runs both before and after (unchanged). **FGO is no longer highest in all three runs**: it was highest in
all 3 originally (8.3-8.6 against EKF3 7.8-7.9 mm); with the corrected priors it is highest in only 1 of 3 runs (r2,
8.340 > EKF3's 7.926) and *below* EKF3 in the other two (r1 7.308 < 7.756; r3 7.488 < 7.840). **The H-H2 verdict
category is unchanged (FAIL 0/3 in both cases), but the underlying pattern changed**: FGO's hold error moved from
"clearly the worst of the three" to "mixed with EKF3, still above UKF".

P-H3's ratios are driven by max(UKF)/min(EKF3) in every run (both before and after; FGO's own gyro activity, ~2.0-2.3x
EKF3's, is never the extremal value), so the ratios and the verdict are unaffected by the prior correction.

H-H4 (15 s): EKF3 (4.9/4.5/7.3 mm) is strictly smallest in all 3 runs both before and after; UKF (29.6/20.4/25.6 mm,
unchanged) is the largest in all 3 runs both before and after. FGO's own 15 s jump narrowed from 7.2-30.1 mm
(original) to 7.1-24.0 mm (new), but this does not change which estimator is largest or the FAIL verdict.

H-H4 (5 s): ratio range narrowed from 3.2-7.7 (original) to 2.1-5.1 (new); still FAIL (all > 1.5) in both cases.

## 5. Old vs new per criterion

| criterion | original (OLD priors) value and verdict | corrected (NEW) priors value and verdict | verdict changed? |
|---|---|---|---|
| **H1.8 FGO** (no heading) | `cl_fgo_a_tex_half_v3` (n=1): contact +169.9 s west, U1/U2/U3 PASS, S2 100 % arm-to-contact (re-derived here; METHODOLOGY's own stated value). Published format: PASS (n=1; no registered set-level threshold exists even for n=1) | n=3: PRIMARY k/3 = 2/3. r1, r2 PASS U1/U2/U3 (and S2); r3 MISS on U3 alone (window edge, 203.5 s vs the 196 s bound). k/3 = 0/3 only if S2 is BOTH made to gate AND read on the scorer's substitute window (never applied to this cell before); on the cell's own established arm-to-contact window, S2 is 100 % on all three, so gating or not makes no difference (D142/OQ-R5) | **The format changed (n=1 PASS to a k/3 count; H1.8 has no registered set-level threshold to map either to), and the count itself (2/3) differs from a single PASS.** This is a genuine 3-flight spread around the registered window's edge (166.7 to 203.5 s). It does not depend on which S2 window is used, or on whether S2 gates at all, as long as the window used is the one established for this cell. Not tested: whether a 3-flight re-fly of the original (old-priors) build would show a similar spread; this report does not claim that it would or would not. Whether this counts as "the verdict changed" is itself the coordinator's call (OQ-R5) |
| **H1.9 FGO** (with heading) | `cl_fgo_b_tex_r{1,2,3}_half_v3`: 3/3, ALL B criteria and S2 PASS (numbers.md row; confirmed from stored jsons, section 2 table) | `cl_fgo_b_tex_r{1,2,3}_half_rp`: 3/3, ALL B criteria and S2 PASS | **No** |
| **H5.1** (FGO-flying bounds) | `H_s3v2_r*`: mean 8.1-9.0 mm, max 18-28 mm (H-H1 PASS, numbers.md section 17.1) | `s3rp_r*`: mean 7.1-8.7 mm, max 15.0-25.5 mm (PASS, section 4.1) | **No** (PASS both; numbers slightly lower) |
| **H5.5** (FGO drift bands) | `H_s3v2_r*`: end of loss 13/20/17; 7/25/27; 22/15/9; 17/11/18 mm (every band PASSES, numbers.md section 17.1) | `s3rp_r*`: end of loss 20/20/19; 22/7/6; 9/12/28; 3/24/1 mm (every band PASSES, section 4.2) | **No** (PASS both; individual numbers moved without a consistent direction) |
| **H5.6 redefined primary (re-lock)** | `H_s3v2_r*`: 0.002-0.032 s, PASS | `s3rp_r*`: 0.003-0.030 s, PASS (section 4.2) | **No** |
| **H5.6 jump as worded** | `H_s3v2_r*`: fails in 4 of 12 losses | `s3rp_r*`: fails in 8 of 12 losses (section 4.2) | descriptive only (no set threshold either way); fail count roughly doubled |
| **H5.7 lockout** | `H_s3v2_r*`: no lockout, PASS | `s3rp_r*`: no lockout, PASS | **No** |
| **30 s-loss yaw wander** | `H_s3v2_r*`: -0.23 / +0.52 / +0.52 deg (<=3 deg, PASS); method not persisted anywhere in the repo | `s3rp_r*`: +0.009 / -0.004 / +0.001 deg via a best-effort re-derivation (section 4.2); PASS; exact original method not reproducible | **No** (PASS both; the exact original figures could not be reproduced, flagged not resolved) |
| **H-H2** | FAIL (0/3): FGO highest in all three runs, 8.3-8.6 mm against EKF3 7.8-7.9 mm (`h_comparative_2026-10-11.json`) | FAIL (0/3 FGO lowest; `lowest_hold`=UKF all 3); FGO 7.3-8.3 mm, highest in only 1 of 3 runs, below EKF3 (7.8-7.9 mm) in the other 2 (section 4.3) | **No** (FAIL both); underlying pattern changed: FGO moved from "clearly worst" to "mixed with EKF3" |
| **P-H3** | FAIL (0/3): UKF 2.40-2.58x, FGO 2.10-2.37x EKF3's hold gyro activity | FAIL (0/3): ratios 2.402/2.577/2.499, numerically unchanged (driven by UKF/EKF3, not FGO; section 4.3) | **No** |
| **H-H4 (15 s)** | FAIL (0/3): EKF3 strictly smallest (5/5/7 mm) against UKF 20-30, FGO 7-30 mm | FAIL (0/3): EKF3 strictly smallest (5/5/7 mm) against UKF 20-30 (unchanged), FGO 7-24 mm (narrower; section 4.3) | **No** |
| **H-H4 (5 s)** | FAIL (0/3): EKF3 4-5 mm against UKF 7-16, FGO 11-34 mm (max/min 3.2-7.7) | FAIL (0/3): ratios 2.1-5.1 (narrower than 3.2-7.7; section 4.3) | **No** |

The originals above are labelled **"superseded: original priors"** per the pre-registration's convention (D129); none
of their directories, score files or `numbers.md` rows were renamed, edited or deleted.

## 6. Checksum guard

`python3 tools/check_numbers_frozen.py`: **PASS** (run after all scoring above, re-run after every subsequent
correction, before this document's final commit).

**`tools/tier1_checksum_guard.py` (standing rule 7): disclosed as `"DIFFERENT: STOP AND REPORT"`, not resolved as
clean.** Its default coverage includes the whole `eval/results` tree (not only `expL`/`expT`, which is all the
tool's own summary text names but not what its code actually globs), so this task's new output files are in
scope. `verify` against the latest pre-existing manifest (`docs/thesis/tier1/frozen_manifest_20261022T002851.json`,
taken 2026-10-22 by a different, unrelated tier-1 workstream) gives, verbatim:

```
"verdict": "DIFFERENT: STOP AND REPORT"
```

with **0 changed, 0 missing, 0 errors, 30 added** across 13253 covered files (report saved:
`docs/thesis/tier1/frozen_manifest_20261022T002851_verify_fgo_refly_priors_20261111.json`). No prior `verify` run
in this repository shows an added-only outcome being accepted as a non-issue; every one on record is `IDENTICAL`
(0/0/0/0). This re-fly never took its own before-snapshot (neither the brief nor the pre-registration mentions this
guard), so this `verify` call is not a genuine before/after pair for this task: a three-week-old manifest from an
unrelated workstream will show many legitimate additions from the intervening weeks regardless of what this task
did. The part that bears on integrity, 0 changed / 0 missing / 0 errors, reads clean; the formal "STOP AND REPORT"
verdict is reported as-is rather than waved away, and flagged for the coordinator as **OQ-R6** (non-STOP here, but
disclosed since the standing rules list "a guard... fails with no safe default" as a STOP condition).

**D145 (after this hold-flight continuation): take the before-snapshot.** Per D145's own instruction ("future runs
take their own before-snapshot"), this agent took `tools/tier1_checksum_guard.py snapshot` immediately before the
first hold flight (`H_s3rp_r1c`), to a scratch path (not committed, per the tool's own recommendation that the
snapshot be taken immediately before the first run; a scratch path was used since this continuation flies, not
registers, the set). `verify` against that snapshot, run after all three hold flights and all scoring, gives a
genuine before/after pair:

```
verify: 13683 files against <scratch>/before_snapshot.json: DIFFERENT: STOP AND REPORT
  ADDED  eval/results/refly_priors_s2/yaw_wander_30s.py
  ADDED  eval/results/expH/s3rp_r1.json
  ADDED  eval/results/expH/s3rp_r2.json
  ADDED  eval/results/expH/s3rp_r3.json
  ADDED  eval/results/expH/h_comparative_refly_priors.json
```

**0 changed, 0 missing, 0 errors, 5 added** — exactly this task's own five new output files, nothing else.
Per D145 ("the STOP condition is an existing output changing... 0 changed/0 missing/0 errors... Accepted"), this is
a clean result: no existing output was touched by the hold flights or scoring. Unlike the earlier `verify` against
the stale 2026-10-22 manifest (30 added, not a genuine pair), this IS a genuine before/after pair for the work in
this continuation and reads clean on the part the guard exists to check.

## 7. Summary

- Corridor re-fly: **6/6 flights flown, all IMU-ok, both sets scored.** H1.9 (with heading) is unchanged at 3/3.
  H1.8 (no heading) reads **PRIMARY k/3 = 2/3**, via the pre-registration's own explicit formula (the count of
  flights meeting U1, U2 and U3; S2 does not gate it, D142), against the original's published single-flight PASS:
  see the lead item at the top of this document and the old-vs-new row above. This result does not depend on
  which S2 window is used, nor (per D142) on whether S2 gates the count at all; OQ-R5 asks the coordinator to
  confirm both points.
- Hold re-fly: **initially blocked after two failed runs** (`H_s3rp_r1`, `H_s3rp_r1b`), root cause identified as a
  harness bug (D141). **Fixed and continued (AMENDMENT 2, D143-D145):** `run_trial.sh`'s `head -1` -> `sed -n 1p`
  (commit `1446ba1`), a new case `H_s3rp_r1c` added to the launcher (commit `25ae937`), then **all three hold
  flights flown cleanly**: `H_s3rp_r1c`, `H_s3rp_r2`, `H_s3rp_r3` (`run_trial exit 0`, no BREACH, IMU-gap 3/3 usable:
  trim/ok/ok). **H5.1 PASS (3/3). H5.5 FGO bands PASS (12/12, both end-of-loss and effective). H5.6 redefined
  primary PASS (12/12, 2.8-30.3 ms). H5.7 no lockout. H5.6 jump as worded: fails 8/12 (vs 4/12 originally,
  descriptive only).** Comparatives H-H2, P-H3, H-H4 (15 s), H-H4 (5 s): **all FAIL, unchanged from the original
  (0/3 each)**, though H-H2's underlying pattern changed (FGO moved from clearly-worst to mixed with EKF3; section
  4.3). The 30 s-loss yaw wander could not be exactly reproduced from the original method (none was found persisted
  anywhere in the repository) but PASSes comfortably either way. **No verdict changed** across H5.1, H5.5, H5.6,
  H5.7, H-H2, P-H3, H-H4a, H-H4b.
- No frozen material was touched. `check_numbers_frozen.py` PASSES. `tools/tier1_checksum_guard.py` formally
  returns `"DIFFERENT: STOP AND REPORT"` against the latest pre-existing (stale, unrelated-workstream) manifest
  (0 changed, 0 missing, 0 errors, 30 added); disclosed, not resolved, as OQ-R6. **This continuation separately took
  its own before-snapshot per D145 and verified after the hold flights: 0 changed, 0 missing, 0 errors, 5 added**
  (exactly this task's own five new output files) — a genuine before/after pair, reading clean (section 6).
- **Corrections to this document's own history, disclosed rather than silently fixed (git safety protocol: no
  amending commits):** commit `f29e2ee`'s message attributed `H_s3rp_r1b`'s retry to a generic transient flake;
  D141 identifies the actual cause (the harness bug above). Commit `aecd390`'s message said "D140's own flights
  disarmed normally"; D140's UKF no-heading set did NOT disarm normally either (it is also watcher-stopped) and
  reads 100 % on its own window regardless, corrected in section 1 above. The PRIMARY k/3 number has been 2/3 since
  `aecd390`, but its justification changed twice since: `31314e9` first scored it as 0/3 (S2 treated as gating,
  read on the scorer's strict `--set b` window); `aecd390` corrected this to 2/3 (S2 treated as gating, but on the
  arm-to-contact window instead); this final version keeps 2/3 but on a different and more defensible basis (S2
  does not gate the count at all, per the pre-registration's own explicit k/3 formula, D142), making the 2/3 result
  robust to the window question that the two earlier versions treated as decisive. The full history is in the four
  commits' messages and D141/D142.
