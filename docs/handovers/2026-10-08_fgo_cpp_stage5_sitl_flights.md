# Handover: FGO C++ port, stage 5 (the three SITL shadow flights and their scoring), 2026-10-08

**From:** the stage-4 agent, which wrote the code and ran no simulator. This file is on branch
`worktree-agent-ad3a9c56cd2a4135a`, based on `fwd-camera` `8dfe675`; it is not merged.
**For:** the main session, which flies.

## RULING NEEDED BEFORE THE FLIGHTS LAND: Rule B (IMU time base) will almost certainly return "indistinguishable"

Check (b)'s pre-registered primary metric is δ_att, the roll/pitch time shift against ground truth on separate
flights. On a3 a single flight cannot locate it:
- the two halves of a3 give −23.0 and +37.5 ms;
- the RMS rises only about 0.0009° at ±20 ms from the minimum.

So R = max(5 ms, |δ(iii) − δ(a3)|) will very likely be tens of ms. Rule B would then say "indistinguishable; keep
time_ref" whatever the truth is, and the user's question would not be answered.

**This agent has NOT amended the rule.** It has already seen a3's same-bag paired replay (time_ref −3.5 ms, causal
+6.0 ms; the live and replay causal results agreed to 1.5 ms), so an amendment written by this agent would look
result-driven. The pre-registration was also partly on the advice that the cross-flight shift be primary; a3 shows
that only same-bag pairing removes the within- and between-flight variation.

Options for the main session or the user to rule on, **before** the flight data are scored:
- **(a)** Make the same-bag paired replay primary. Each of the four bags is replayed through
  `fgo_cpp_live_replay` in both modes (the `--replay-pair` rows, already computed below). A consistency rule is
  needed, for example "time_ref has the smaller |δ_att| on at least 3 of 4 bags, else indistinguishable".
- **(b)** Keep δ_att, but high-pass or detrend the roll/pitch error and fit only the climb, start-of-cruise and stop
  segments. This needs a code change and a re-check on a3 first.
- **(c)** Keep Rule B as registered and accept "indistinguishable".

The flights do not depend on this ruling. The scoring commands below already compute the paired replay on all four
bags as report rows, so any of (a)–(c) can be applied to them.

## State (stage 4, done)

| commit | content |
|---|---|
| `b85fefa` | **Pre-registration 4** in `docs/fgo_cpp_port.md`, committed before any C++-node SITL data existed and before the script was run on any trial |
| `ee3d642` | WIP `b641287` adopted as a whole after review (`FGO_NODE_IMPL=cpp` in `run_trial.sh`, the node's stats and SIGINT drain, CMake install rules), plus `t_armed_header` in the node stats; `eval/fgo_cpp_sitl_check.py` rewritten to the pre-registration |
| (this commit) | the part-4 verification record in `docs/fgo_cpp_port.md`, the script's report-only diagnostics, this note |

**Verified** (details in `docs/fgo_cpp_port.md`, "Part 4: what was built and verified"):
- The `fgo_node.py` path in `run_trial.sh` is unchanged.
- The binaries are installed at `~/opt/fgo_cpp/bin`. md5 of `fgo_cpp_node`: `ecc683b2773a7dd6fde3c9f96d2573dd`.
- Bag-play smoke tests of the run_trial-style launch passed:
  - SIGINT stop with rc 0 in ≤ 0.16 s, and the stats written;
  - the arming time taken from HEARTBEAT;
  - ODOMETRY sent, and `/fgo/pose` recorded.
- The script's unit checks passed.
- A dry run of the script on `fgo_shadow_half_a3` worked.

**Not verified (needs SITL, which is your part):**
- UDP to and from the real SERIAL3;
- AP_NavFGO receiving the C++ node's ODOMETRY;
- real arrival timing.

## Before flying

1. **Merge** `worktree-agent-ad3a9c56cd2a4135a` into `fwd-camera` in the main checkout, so that `run_trial.sh`
   has `FGO_NODE_IMPL`.
2. The installed binary is already in place at `~/opt/fgo_cpp/bin/fgo_cpp_node`. If you rebuild after merging, do it
   through `heavy.py`, with `-DCMAKE_INSTALL_PREFIX=$HOME/opt/fgo_cpp` and `make install`, as in `docs/fgo_cpp_port.md`.
3. Use the flight lock (`source tools/flight_lock.sh; flight_lock_acquire "<name>"` … `flight_lock_release`).

## The three shadow flights (exact; each is `fgo_shadow_half_a3`'s command with only the C++ env added)

Truth flies (`AHRS_EKF_TYPE` 10 from `consolidated_rerun.parm`) and the FGO runs in shadow. The world is
`corridor_textured_half_fwdc`: 0.5 m/s, 2.0 m, 300 s, no heading. Run from `~/thesis_ws`:

```
# (i) cpp, 0.20 s, time_ref
env FGO_NODE=1 FGO_NODE_IMPL=cpp FGO_CPP_DELAY=0.20 FGO_CPP_IMU_STAMP=time_ref FGO_CPP_ARM_SOURCE=heartbeat \
  LOOPBACK_ONLY=1 GZ_IP=127.0.0.1 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ARDUPILOT_TREE=$HOME/ardupilot_ukf \
  EXTRA_PARM_FILES=$HOME/thesis_ws/fgo_shadow.parm EXPECT_OVERRIDE=AHRS_FGO_ENABLE=1,SERIAL3_PROTOCOL=2 \
  ./run_trial.sh --world corridor_textured_half_fwdc --velocity 0.5 --altitude 2.0 --duration 300 --trial-name fgo_cpp_shadow_i
# (ii) cpp, 0.10 s, time_ref : as (i) with FGO_CPP_DELAY=0.10 and --trial-name fgo_cpp_shadow_ii
# (iii) cpp, 0.10 s, causal  : as (i) with FGO_CPP_DELAY=0.10 FGO_CPP_IMU_STAMP=causal and --trial-name fgo_cpp_shadow_iii
```

Each flight is about 6–7 minutes of wall-clock time.

**Deviation from the stage-4 brief, stated.**
- The brief said "EKF3 flies". The existing shadow flights flew on truth.
- EKF3 in the loop (a2) hit the west wall at about 211 s, so a 300 s flight would not finish on this world.
- Truth flying also lets `fgo_shadow_half_a3` (the Python node, 0.10 s, causal) serve as the fourth, between-flight
  reference flight.
- If you want EKF3 flying instead, Rule A is unchanged and δ_att still applies. The secondary position rows would not
  be comparable across flights.

**Check after each flight, before scoring:**
- `AHRS_EKF_TYPE` 10 in the PARM dump. The script checks it and marks the flight VOID otherwise.
- `logs/fgo_node.log` begins with `fgo_cpp_node: reorder_delay_s=… imu_stamp=…`.
- `fgo_node_stats.json` exists.

## Scoring (pre-registered; run each step through `heavy.py`, after the flight has ended)

```
cd ~/thesis_ws
H="python3 src/estimators/fgo_cpp/tools/heavy.py"; P=$HOME/venv-fgo/bin/python; C=eval/fgo_cpp_sitl_check.py
R="--replay-pair $HOME/opt/fgo_cpp/bin"   # same-bag paired replay on every bag (report rows; see the ruling above)
$H "score i"   -- $P $C score fgo_cpp_shadow_i   --json eval/results/fgo_cpp_sitl_i.json   $R
$H "score ii"  -- $P $C score fgo_cpp_shadow_ii  --json eval/results/fgo_cpp_sitl_ii.json  $R
$H "score iii" -- $P $C score fgo_cpp_shadow_iii --json eval/results/fgo_cpp_sitl_iii.json $R
$H "score a3"  -- $P $C score fgo_shadow_half_a3 --json eval/results/fgo_cpp_sitl_a3.json  $R
$P $C decide --i eval/results/fgo_cpp_sitl_i.json --ii eval/results/fgo_cpp_sitl_ii.json \
  --iii eval/results/fgo_cpp_sitl_iii.json --a3 eval/results/fgo_cpp_sitl_a3.json --json eval/results/fgo_cpp_sitl_decision.json
```

How the script handles bags and timing:
- A packed bag is decompressed to a scratch COPY, sha256-checked and then removed.
- If a bag is still unpacked, it is read in place, read-only.
- Each `score` takes a few minutes. `--replay-pair` adds the tape and two replays.

**Rules** (`docs/fgo_cpp_port.md` Pre-registration 4):
- **A.** If (i)'s max `XFGO.Age` over W_a is above 250 ms, adopt 0.10 s and record the figures. If (ii) also exceeds
  250 ms, report "neither delay" to the user; the budget is not changed.
- **B.** δ_att is the roll/pitch time shift against ground truth. R = max(5 ms, |δ(iii) − δ(a3)|). The smaller
  |δ| of (ii) and (iii) wins if they differ by R or more. Otherwise the verdict is "indistinguishable; keep
  time_ref".

## What to expect (stated before the flights, for honesty)

- **(i) will very likely trigger Rule A.**
  - a3 (0.10 s horizon) had a median Age of 132 ms and a max of 176 ms.
  - Age is roughly the delay plus about 35–75 ms, so 0.20 s should give a median of about 230 ms, with a tail above
    250 ms.
- **Rule B may well end "indistinguishable".**
  - On a3 the δ_att minimum is shallow, and the two halves of the flight disagree (−23 / +37.5 ms).
  - The paired replay of a3's own bag separated the modes by 9.5 ms (time_ref −3.5, causal +6.0). That replay is a
    report row only.

## Open items

- The Rule B ruling at the top.
- **Check (a) reports wrapped ages.** A future-stamped state wraps `XFGO.Age` to about 4.29e9 (the D25 failure
  mode). Rule A still uses the literal maximum. The script also reports `n_age_wrapped` and
  `max_excluding_wrapped`, and `decide` warns if any wrap occurred. That is parsing only. If it fires, the
  'max Age' is a clock-map fault, not staleness, so report it as that.
- Whether AP_NavFGO accepts the C++ node's ODOMETRY live has not been tested. A void or empty `XFGI` in (i)
  answers it.
- The flight results, the verdicts and the METHODOLOGY entry are for the next stage. Write them after
  `decide`.
- Merge to `fwd-camera`, which this agent was not permitted to do.
