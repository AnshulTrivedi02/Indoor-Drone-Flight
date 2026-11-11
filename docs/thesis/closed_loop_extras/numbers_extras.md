# Closed-loop extras: n = 3 no-heading EKF3/UKF flights

Registration: `docs/thesis/closed_loop_extras/preregistration.md`, committed at **7bf0bff** (D133, D136 in
`docs/thesis/tier1/decisions_log.md`). `numbers.md` stays frozen (`tools/check_numbers_frozen.py`: PASS,
confirmed after this work, not touched by it). This file adds the new values only.

**Builds, verified before flying** (md5 of the glob, binary name never typed on a command line): EKF3
`~/ardupilot/build/sitl/bin/arduc*` = `43a2165a1bb6fdde385f6367c6c105b8` (matches the registered
`43a2165a1bb6…`); UKF `~/ardupilot_ukf/build/sitl/bin/arduc*` = `5f94ea1aa7e223f90343c1948d443d32`
(matches the registered `5f94ea1aa7e2…`, port `abb0357d`). `ARDUPILOT_TREE` was unset throughout the EKF3
flights, as required.

**D136 derotation disclosure.** Both the offline UKF and this flown port remove the UKF's own gyro bias from
the flow derotation when the UKF is flying; they differ only in gyro source and timing (offline: frame-averaged
IMU gyro minus the UKF's own bias estimate; flown: the AHRS gyro `AP::ahrs().get_gyro()` averaged over the flow
interval, which already carries the UKF's bias removed while the UKF flies). Six later UKF commits
(`c25fa8980d` … `f30f6ffa2f`) are not built into `abb0357d` and are not flown here.

**Scorer disclosure.** The pre-registration (section 4) states that `--set a --est ukf` "adds S2". At the
registration commit, `--est` only changes behaviour inside the `--set b` branch of
`eval/closed_loop_score.py`; for `--set a` (used throughout, as registered) the output is `a_primary` only,
identically whether `--est ukf` is passed or not (confirmed: byte-identical JSON either way, and
`eval/closed_loop_score.py` is unchanged since 7bf0bff). This matches the existing precedent for this exact
cell: the final-port flight-1 result (`cl_ukf_a_tex_half_v2`) was itself scored and written up the same way
-- contact and window only, no U1/S2 breakdown. The nine new flights follow that precedent:
- **U2** ("no contact before +100 s") is read directly from `a_primary.no_contact_before_100s`.
- **U3** ("west-wall contact inside [+146, +218] s") is computed here from the scorer's unrounded
  `contact.t_rel_cruise_s` and `contact.wall` against the UKF's OWN window -- `a_primary.pass` must not be
  used for UKF verdicts, since it applies EKF3's window ([+155, +215]), not the UKF's ([+146, +218]); one new
  flight (`cl_ukf_a_tex_half_v2_r3`, 152.853 s) is inside the UKF window but outside EKF3's, so the two
  disagree for that flight.
- **U1 and S2 are not separately scored for any flight in this set** (old or new), consistent with how
  `cl_ukf_a_tex_half_v2` itself was reported. (Contrast: the superseded old-port flight `cl_ukf_a_tex`, listed
  below, DOES carry a hand-scored U1/S1/S2 in its own json -- it was scored by a different, bespoke method
  before the registered scorer existed in its current form, and is not re-used here.)

**IMU-gap rule**, run on every new flight before scoring (`eval/imu_gap_check.py <trial> --write`, writing
`imu_gaps.json` into each new trial directory): **9/9 "ok"** (usable). No re-flies were needed; no `...b`
flights exist.

## EKF3, full real time (RTF 1.0) -- `corridor_textured_fwdc`

Window [+155, +215] s, west wall; "PRIMARY: no contact before +100 s; contact, if any, on the west wall inside
the window."

| flight | contact (s, unrounded) | contact (s, display) | wall | verdict |
|---|---|---|---|---|
| `cl_a_tex` (flight 1, existing) | 186.237 | 186.2 | west | PASS |
| `cl_a_tex_r2` | 174.9 | 174.9 | west | PASS |
| `cl_a_tex_r3` | 181.39999999999998 | 181.4 | west | PASS |

**k/3 = 3/3.** Spread (descriptive): 174.9 - 186.2 s (min-max 11.3 s). Existing n = 1 verdict: PASS
(unchanged).

## EKF3, half real time (RTF 0.5) -- `corridor_textured_half_fwdc`

Same window and rule as above.

| flight | contact (s, unrounded) | contact (s, display) | wall | verdict |
|---|---|---|---|---|
| `cl_a_tex_half` (flight 1, existing) | 242.06100000000004 | 242.1 | west | MISS (after window) |
| `cl_a_tex_half_r2` | 178.943 | 178.9 | west | PASS |
| `cl_a_tex_half_r3` | 268.28499999999997 | 268.3 | west | MISS (after window) |

**k/3 = 1/3.** Spread (descriptive): 178.9 - 268.3 s (min-max 89.3 s). Existing n = 1 verdict: MISS
(unchanged). No comparison across real-time factors is claimed (D21).

## UKF, full real time -- `corridor_textured_fwdc` (port `abb0357d`, labelled `_v2`)

Window [+146, +218] s, west wall. U1/S2 not scored (see disclosure above); U2/U3 as defined.

| flight | contact (s, unrounded) | contact (s, display) | wall | U2 (no contact < 100 s) | U3 ([+146,+218] west) | verdict |
|---|---|---|---|---|---|---|
| `cl_ukf_a_tex_v2_r1` | 177.14499999999998 | 177.1 | west | PASS | PASS | PASS |
| `cl_ukf_a_tex_v2_r2` | 138.262 | 138.3 | west | PASS | MISS (before window) | MISS |
| `cl_ukf_a_tex_v2_r3` | 162.756 | 162.8 | west | PASS | PASS | PASS |

**k/3 = 2/3.** Spread (descriptive): 138.3 - 177.1 s (min-max 38.9 s). No flight 1 exists for this cell (the
earlier build's flight, `cl_ukf_a_tex`, is superseded -- see below); this cell is 3 new flights in total, as
pre-registered.

**Superseded, listed only (not counted in the k/3 above):** `cl_ukf_a_tex` flew the earlier,
pre-jitter-correction UKF port. Its own (bespoke-scored) result: contact +163.0 s, west wall, U1/U2/U3 all
PASS, S1/S2 both hold (`horiz_pos_rel`/healthy 100 %, `EvO` 0). Not re-scored here.

## UKF, half real time -- `corridor_textured_half_fwdc` (port `abb0357d`, `_v2`)

Same window and rule as above.

| flight | contact (s, unrounded) | contact (s, display) | wall | U2 (no contact < 100 s) | U3 ([+146,+218] west) | verdict |
|---|---|---|---|---|---|---|
| `cl_ukf_a_tex_half_v2` (flight 1, existing) | 165.93 | 165.9 | west | PASS | PASS | PASS |
| `cl_ukf_a_tex_half_v2_r2` | 163.687 | 163.7 | west | PASS | PASS | PASS |
| `cl_ukf_a_tex_half_v2_r3` | 152.853 | 152.9 | west | PASS | PASS | PASS |

**k/3 = 3/3.** Spread (descriptive): 152.9 - 165.9 s (min-max 13.0 s). Existing n = 1 verdict: PASS
(unchanged). Note: `cl_ukf_a_tex_half_v2_r3`'s contact (152.853 s) falls inside the UKF's own window
[+146, +218] but OUTSIDE EKF3's window [+155, +215] -- the scorer's stored `a_primary.pass` for this flight is
`false` because it applies EKF3's window; the UKF verdict above correctly uses the UKF's own window instead.

## Summary

| cell | k/3 | spread (min-max, s) | existing n = 1 verdict |
|---|---|---|---|
| EKF3, full real time | 3/3 | 174.9 - 186.2 | PASS |
| EKF3, half real time | 1/3 | 178.9 - 268.3 | MISS |
| UKF, full real time (`_v2`) | 2/3 | 138.3 - 177.1 | n/a (no flight 1 on this port) |
| UKF, half real time (`_v2`) | 3/3 | 152.9 - 165.9 | PASS |

No comparison across speeds, and no comparison across estimators beyond what is stated above, is claimed
(D21). No verdict in `numbers.md` is changed by this file; `numbers.md` remains frozen.
