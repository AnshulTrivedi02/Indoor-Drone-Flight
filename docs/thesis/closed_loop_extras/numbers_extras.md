# Closed-loop extras: n = 3 no-heading EKF3/UKF flights

Registration: `docs/thesis/closed_loop_extras/preregistration.md`, committed at **7bf0bff** (D133, D136 in
`docs/thesis/tier1/decisions_log.md`). `numbers.md` stays frozen (`tools/check_numbers_frozen.py`: PASS,
confirmed after this work, not touched by it). This file adds the new values only.

**Builds, verified before flying** (md5 of the glob, binary name never typed on a command line): EKF3
`~/ardupilot/build/sitl/bin/arduc*` = `43a2165a1bb6fdde385f6367c6c105b8` (matches the registered
`43a2165a1bb6…`); UKF `~/ardupilot_ukf/build/sitl/bin/arduc*` = `5f94ea1aa7e223f90343c1948d443d32` (matches
the registered `5f94ea1aa7e2…`, port `abb0357d`). Every EKF3 flight's `~/thesis_data/closed_loop/<name>/launch.txt`
records `ARDUPILOT_TREE=` (empty), and each `result.txt` shows `ardupilot.bin copied from
/home/makerspace/ardupilot/ArduCopter/logs/...` (the EKF3 tree, not `ardupilot_ukf`), confirming the EKF3
build flew for every EKF3-labelled flight.

**D136 derotation disclosure.** Both the offline UKF and this flown port remove the UKF's own gyro bias from
the flow derotation when the UKF is flying; they differ only in gyro source and timing (offline: frame-averaged
IMU gyro minus the UKF's own bias estimate; flown: the AHRS gyro, `AP::ahrs().get_gyro()`, averaged over the
flow interval, which already carries the UKF's own bias removed while the UKF flies).

Separately disclosed: six later UKF commits (`c25fa8980d` through `f30f6ffa2f`, 2026-10-10 to 2026-10-12) are
not built into `abb0357d` and are not flown here.

**Scorer disclosure.** The pre-registration (section 4) states that `--set a --est ukf` "adds S2". At the
registration commit, `--est` only changes behaviour inside the `--set b` branch of
`eval/closed_loop_score.py`; for `--set a`, the output is `a_primary` only, identically whether `--est ukf`
is passed or not. **Verified, not assumed**: all nine `--set a` jsons stored under `eval/results/` were
produced by the exact registered call (five of the nine UKF-labelled flights, the two half-speed `_r2`/`_r3`
and both already included `--est ukf`; for the three full-speed flights, the stored json omitted `--est`, so
each was re-run to a scratch file with `--est ukf` added and `diff`'d against the stored json: all three are
byte-identical).

Because of this, **U1 and S2 are additionally scored here for the five new UKF flights**, using
`eval/closed_loop_score.py <trial> --set b --est ukf` (to a scratch path, not `eval/results/closed_loop_<trial>.json`,
which stays the registered `--set a` output) for S2, plus `logs/fly_trial.log` and the dataflash `ERR`/`MSG`
stream for U1:
- **S2** ("the estimator is valid throughout"): the scorer's `S2` block, `XUKS` `horiz_pos_rel`/healthy from
  arming to disarm (or to the flight's last sample, since every flight here ends in a watcher stop, not a
  normal disarm). **100 % / 100 % on all five** (PASS on all five).
- **U1** ("flies through arming, take-off to >= 1.8 m and entry into cruise, with no crash, failsafe or loss
  of control before any wall contact"): `fly_trial.log` shows `Armed.` and `Reached` 1.81-1.84 m (all five,
  all >= 1.8 m) followed by `Cruising forward...` on every flight; the dataflash `ERR` stream has exactly one
  entry on each flight, `Subsys 3` (COMPASS) `ECode 0` (resolved) at 2.6-3.3 s after boot, i.e. roughly 20 s
  before arming on every flight and not a failsafe during flight; and `result.txt`/`BREACH.txt` on all five
  record a `wall contact` breach, never a `crash:`/`dependency died` breach (`sim/tools/wall_watch.py`'s only
  other breach strings). **PASS on all five.**

Flight 1 of the half-speed UKF cell (`cl_ukf_a_tex_half_v2`, existing, not re-scored) carries neither U1 nor
S2 in its own stored result or write-up, which only report the contact time and window check; it is reported
below as "not in stored result" for those two columns, and is still counted in the cell's k/3 as registered.

**U2/U3**, for every UKF flight (old, existing, and new):
- **U2** ("no contact before +100 s") is read directly from the stored `a_primary.no_contact_before_100s`.
- **U3** ("west-wall contact inside [+146, +218] s") is computed here from the scorer's unrounded
  `contact.t_rel_cruise_s` and `contact.wall`, against the UKF's OWN window. `a_primary.pass` must not be
  used for a UKF verdict, since it applies EKF3's window ([+155, +215]), not the UKF's ([+146, +218]): one
  flight, `cl_ukf_a_tex_half_v2_r3` (152.853 s), is inside the UKF window but outside EKF3's, so the two
  disagree for that flight; the table below uses the UKF window throughout.

**On the superseded old-port flight, `cl_ukf_a_tex` (listed only, not counted, see below):** its own json
carries a hand-built U1/S1/S2 (commit `4c060ae`, 2026-09-30 20:20). That predates, by the same evening's log,
the commit that added `--est ukf` (B3 from `XUKO`, S2) to `eval/closed_loop_score.py` (`9c13d0c`, 2026-09-30
20:47) though the scorer itself already existed (`622334a`, 2026-09-29). So `cl_ukf_a_tex` was genuinely
scored before the registered scorer could produce S2 at all, and that hand-built result is quoted as-is, not
re-derived.

**IMU-gap rule**, run on every new flight before scoring (`eval/imu_gap_check.py <trial> --write`, writing
`imu_gaps.json` into each new trial directory): **9/9 "ok"** (usable). No re-flies were needed; no `...b`
flights exist.

**Not part of this flying session**: `docs/thesis/tier1/decisions_log.md` and
`docs/thesis/refly_priors/preregistration.md` carry uncommitted changes from a different, concurrent piece of
work (the FGO prior re-fly pre-registration). They were not touched here and are left as found.

## EKF3, full real time (RTF 1.0): `corridor_textured_fwdc`

Window [+155, +215] s, west wall; "PRIMARY: no contact before +100 s; contact, if any, on the west wall
inside the window."

| flight | contact (s, unrounded) | contact (s, display) | wall | verdict |
|---|---|---|---|---|
| `cl_a_tex` (flight 1, existing) | 186.237 | 186.2 | west | PASS |
| `cl_a_tex_r2` | 174.9 | 174.9 | west | PASS |
| `cl_a_tex_r3` | 181.39999999999998 | 181.4 | west | PASS |

**k/3 = 3/3.** Spread (descriptive): 174.9-186.2 s (min-max 11.3 s). Existing n = 1 verdict: PASS (unchanged).

## EKF3, half real time (RTF 0.5): `corridor_textured_half_fwdc`

Same window and rule as above.

| flight | contact (s, unrounded) | contact (s, display) | wall | verdict |
|---|---|---|---|---|
| `cl_a_tex_half` (flight 1, existing) | 242.06100000000004 | 242.1 | west | MISS (after window) |
| `cl_a_tex_half_r2` | 178.943 | 178.9 | west | PASS |
| `cl_a_tex_half_r3` | 268.28499999999997 | 268.3 | west | MISS (after window) |

**k/3 = 1/3.** Spread (descriptive): 178.9-268.3 s (min-max 89.3 s). Existing n = 1 verdict: MISS (unchanged).
No comparison across real-time factors is claimed (D21).

## UKF, full real time: `corridor_textured_fwdc` (port `abb0357d`, labelled `_v2`)

Window [+146, +218] s, west wall.

| flight | contact (s, unrounded) | contact (s, display) | wall | U1 | U2 | U3 | S2 | verdict |
|---|---|---|---|---|---|---|---|---|
| `cl_ukf_a_tex_v2_r1` | 177.14499999999998 | 177.1 | west | PASS | PASS | PASS | PASS | PASS |
| `cl_ukf_a_tex_v2_r2` | 138.262 | 138.3 | west | PASS | PASS | MISS (before window) | PASS | MISS |
| `cl_ukf_a_tex_v2_r3` | 162.756 | 162.8 | west | PASS | PASS | PASS | PASS | PASS |

**k/3 = 2/3.** Spread (descriptive): 138.3-177.1 s (min-max 38.9 s). No flight 1 exists on this port (see the
superseded flight below); this cell is 3 new flights in total, as pre-registered.

**Superseded, listed only (not counted in the k/3 above):** `cl_ukf_a_tex` flew the earlier,
pre-jitter-correction UKF port. Its own (hand-scored, pre-dating the registered scorer's S2 support; see
above) result: contact +163.0 s, west wall, U1/U2/U3 all PASS, S1/S2 both hold (`horiz_pos_rel`/healthy
100 %, `EvO` 0). Not re-scored here. The existing n = 1 verdict for this cell, on that earlier build, is
**PASS**.

## UKF, half real time: `corridor_textured_half_fwdc` (port `abb0357d`, `_v2`)

Same window and rule as above.

| flight | contact (s, unrounded) | contact (s, display) | wall | U1 | U2 | U3 | S2 | verdict |
|---|---|---|---|---|---|---|---|---|
| `cl_ukf_a_tex_half_v2` (flight 1, existing) | 165.93 | 165.9 | west | not in stored result | PASS | PASS | not in stored result | PASS |
| `cl_ukf_a_tex_half_v2_r2` | 163.687 | 163.7 | west | PASS | PASS | PASS | PASS | PASS |
| `cl_ukf_a_tex_half_v2_r3` | 152.853 | 152.9 | west | PASS | PASS | PASS | PASS | PASS |

**k/3 = 3/3.** Spread (descriptive): 152.9-165.9 s (min-max 13.1 s). Existing n = 1 verdict: PASS (unchanged).
Note: `cl_ukf_a_tex_half_v2_r3`'s contact (152.853 s) falls inside the UKF's own window [+146, +218] but
OUTSIDE EKF3's window [+155, +215]; the scorer's stored `a_primary.pass` for this flight is `false` because
it applies EKF3's window, but the UKF verdict above correctly uses the UKF's own window.

## Summary

| cell | k/3 | spread (min-max, s) | existing n = 1 verdict |
|---|---|---|---|
| EKF3, full real time | 3/3 | 174.9-186.2 | PASS |
| EKF3, half real time | 1/3 | 178.9-268.3 | MISS |
| UKF, full real time (`_v2`) | 2/3 | 138.3-177.1 | PASS (earlier, superseded port, `cl_ukf_a_tex`, +163.0 s; not counted) |
| UKF, half real time (`_v2`) | 3/3 | 152.9-165.9 | PASS |

No comparison across speeds, and no comparison across estimators beyond what is stated above, is claimed
(D21). No verdict in `numbers.md` is changed by this file; `numbers.md` remains frozen.
