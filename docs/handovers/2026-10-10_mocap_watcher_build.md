# Handover, 2026-10-10: real-hardware mocap watcher built (gaps G1–G11), offline tests only

**Stage:** coding and offline tests only. No simulator runs, no flights, no heavy jobs. METHODOLOGY.md, numbers.md,
`sim/tools/wall_watch.py`, `tools/closed_loop_run.sh`, `fly_trial.py`, `run_trial.sh` and every SITL-used file are
**unchanged**. The SITL safety re-tests keep the tested watcher. `docs/real_flight_readiness.md` was NOT edited (another
agent is re-costing by rung); the status update for its rows F1–F4 is in §6 below.

## 1. What was built

The watcher is a new package, `realflight/watcher/`. It does not import `wall_watch.py` or modify it. Two things are
copied from it, and each copy is marked in the code:
- the tilt rule (60°);
- the heartbeat-file format, `<wall time> box= bridge=`, which `fly_trial.watch_ok()` reads unchanged.

| file | role |
|---|---|
| `realflight/watcher/mocap.py` | Mocap input interface (`MocapSample`, `PoseSource`) and the concrete UDP adapter `UdpPoseSource`. The packet is 93 bytes (`MCP1`) and carries: frame number, mocap time, body ID and name, a tracked flag, position and quaternion. `pose_stamped_to_sample` is the hook for a swappable ROS 2 adapter. |
| `realflight/watcher/frames.py` | Converts a z-up or y-up mocap frame to the z-up "watch frame", with a body yaw offset. Gives tilt, and Euler angles in the FC's FRD convention. |
| `realflight/watcher/core.py` | The decision logic: I/O-free, with a clock injected (`WatcherCore`, `Identity`, `Config`). |
| `realflight/watcher/fc_link.py` | MAVLink to the FC: a heartbeat from the watcher's own system ID; LAND as `MAV_CMD_DO_SET_MODE` custom mode 9, retried until ACKed; a parameter readback and check; STATUSTEXT; detection of another sender using the watcher's system ID. |
| `realflight/watcher/liveness.py` | Networked liveness: `LivenessBeacon` (sender) and `LivenessMonitor` (watcher side). |
| `realflight/watcher/sidecars.py` | Pi-side beacon sidecars. `proc` sends while the process exists and is not in state T/Z/X. `topic` (needs rclpy) reports progress as the count of messages on the process's output topic. Only `TopicRateCore` is tested; the rclpy glue in `main()` is UNTESTED (no ROS sourcing in this stage). |
| `realflight/watcher/mocap_watch.py` | The executable: `python3 -m realflight.watcher.mocap_watch OUT --fc ... --sysid 211 --mocap-port ... --box=xmin,xmax,ymin,ymax,zmin,zmax ...` |
| `realflight/params/watcher_fc.parm` | FC parameter template, with the names verified in source. |
| `realflight/params/watcher_arming_auth.lua` | Lua arming-authorisation script for G6(ii). **DRAFT, UNTESTED** (no Lua interpreter here, and no SITL use allowed). |
| `realflight/watcher/tests/` | 73 tests, using a fake FC (pymavlink on loopback), a fake mocap stream, beacon subprocesses and the watcher as a real subprocess. |

**Behaviour:**
- **Main loop:** about 50 Hz. The 1 s tick, as pre-registered, governs the file and the MAVLink heartbeat.
- **Confirmed** means box=1 and bridge=1:
  - box=1 needs: a fresh tracked pose for at least `recover_s` (2 s); the vehicle inside the 3-D box with tilt ≤ 60°; rigid-body identity proven; FC parameters verified; the FC link up; and no latched episode.
  - bridge=1 needs every beacon dependency alive and no latched episode.
- **Heartbeat to the FC:** the watcher sends a MAVLink HEARTBEAT ONLY while confirmed. It never sends RC_CHANNELS_OVERRIDE or MANUAL_CONTROL.
- **Response to a breach:**
  - it latches an *episode*;
  - it alerts by terminal bell, `--alert-cmd` and STATUSTEXT;
  - it sends ONE LAND, re-sent only until the FC ACKs it (at most 5 tries, 0.3 s apart), and never again in that episode;
  - it stops the heartbeat and withdraws the file flags.
- **End of an episode:** only when the FC reports DISARMED AND every check has held for `recover_s`.
- **Self-stall:** a gap of more than 1 s in the watcher's own loop (a hang or a SIGSTOP) latches WITHOUT a LAND. This is checked at the top of every iteration, and again just before any heartbeat is sent.
- **Exit:** SIGINT/SIGTERM exit fail-closed. The file is withdrawn, and the MAVLink heartbeat stops.

**How to run the tests:**
- Command: `python3 -m pytest realflight/watcher -q -p no:cacheprovider`.
- The interpreter must have pymavlink; here `python3` resolves to `~/venv-ardupilot` (pymavlink 2.4.x, pytest 7.4.4).
- **Result: 73 passed in about 85 s** (the first 71 run twice with no flakes before the identity-latency change; the final suite run is in §7).
- Every socket binds 127.0.0.1 on port 0. None touches 14550–14560 or 5760.

## 2. Gap → implementation → test → bench test

The FakeFC's GCS-failsafe and arming behaviour is **our model** of `events.cpp` / `AP_Arming_Copter.cpp`, not
ArduPilot itself. The tests prove the **watcher's side**: what it sends, what it withholds, and when. The FC-side
halves of G5, G6 and G11 are **closed in code and parameters, and proven only on the bench** (B1c, B2b, B3a).

| gap | implementation | offline test(s) | bench test that exercises it on hardware |
|---|---|---|---|
| **G1** no mocap input | `mocap.py`: the `PoseSource` interface and `UdpPoseSource` (the MCP1 packet); the `pose_stamped_to_sample` hook. `frames.py`: z-up/y-up and a body yaw offset. The requirements on the real system are in the `mocap.py` docstring (see §4). | `test_inputs.py::test_g1_*` (packet round trip, malformed packets, loopback receive, the PoseStamped adapter, FRD Euler signs, y-up conversion); every e2e test feeds poses over UDP | B0, B4, B5, B7a |
| **G2** no stale-pose check | `core.pose_fresh()`, evaluated on every loop, not only when a pose arrives. A pose is not fresh when: older than 0.5 s; the tracked flag is 0 (immediate); or, ONLY when the source has no tracked flag, bit-identical for at least 0.5 s. Duplicate frame numbers are ignored. Recovery needs 2 s of continuous fresh poses AND the FC disarmed. | `test_core.py::test_g2_*` (7 tests: confirm only after 2 s; LAND within 0.5 s; untracked; frozen fallback; identical poses with a flag stay fresh; recovery needs disarm + 2 s with no second LAND; never received → no LAND); e2e `test_b5a_*` (LAND 0.4–0.7 s after the stream stops), `test_b5b_*`, `test_b5c_*` | B5a/b/c |
| **G3** no rigid-body ID check | Two levels. (1) Stream level: samples whose `--body-name`/`--body-id` does not match are ignored and counted (`wrong_bodies` in the summary), so a wrong body is stale and never confirms. (2) `core.Identity` (B6), evaluated on each FC ATTITUDE arrival against the best-matching mocap sample of the preceding 0.3 s (a latency allowance for the telemetry link): UNPROVEN until a hand motion. A roll/pitch excitation ≥ 8° must agree within 5° for 0.25 s; procedure: tilt ≥ 10° and hold about 1 s. A yaw change ≥ 45° (over a sliding 3 s span, so slow FC yaw drift cancels) must agree within 10° within 1 s. A disagreement > 5° sustained for 0.5 s, or a yaw mismatch, makes it FAILED, final until restart. There is NO fixed roll/pitch offset parameter: the asset axes must match the FC's IMU axes within 5° at rest, checked at B6 setup. ATTITUDE is re-requested at 25 Hz every 2 s (MAVProxy can override a one-shot interval), and the measured rate is in the summary. It gates CONFIRMATION only: after proof, a disagreement is alerted, never acted on (not pre-registered). | `test_core.py::test_g3_*` (8 tests: wrong name ignored; proven with the right body; FAILED with a wrong body, no confirmation, no LAND; yaw-only failure; post-proof disagreement only alerted; 20°/min FC yaw drift does not fail it; **FC ATTITUDE at 10 Hz, 150 ms late, quick hand motions incl. a 40°/s tilt: the right body proves, the wrong body fails** (without the lag allowance the right body falsely FAILS, checked); ATTITUDE at 4 Hz still proves with a held tilt); e2e `test_b6_wrong_body_name_never_confirms`, `test_b6_identity_by_hand_motion[True/False]` (through real pymavlink ATTITUDE) | B6 |
| **G4** breach kills processes | `core._breach` returns a ("LAND", why) at most once per episode, only if the watcher was confirmed in that episode. `FcLink.command_land` sends `MAV_CMD_DO_SET_MODE` (param1 1, param2 9), re-sends until ACKed (5 × 0.3 s at most), and is idempotent within the episode. Alerts go to the bell, `--alert-cmd` and STATUSTEXT. No process is ever killed. | `test_core.py::test_g4_*` (x/y breach on the first outside pose; tilt; one LAND across box + height + stale in one episode, a new LAND only after disarm + re-confirm; no LAND before any confirmation); `test_fc_link.py::test_g4_*` (retry until ACK, then never again; give up after max tries); e2e `test_b4_*` (LAND ≤ 0.3 s after the first outside pose, exactly one, heartbeat stops, BREACH.txt), `test_b4c_tilt_breach` | B4a/b/c, B5, B9, B10b (at most one LAND) |
| **G5** no FC-side layer | The watcher's MAVLink HEARTBEAT (MAV_TYPE_GCS, own system ID), sent only while confirmed. `watcher_fc.parm`: `FS_GCS_ENABLE` 5, `FS_GCS_TIMEOUT` 3, `MAV_GCS_SYSID` = the watcher's ID, `MAV_GCS_SYSID_HI` 0, `FS_OPTIONS` bit 4. The watcher reads these back at startup (`fc_link.expected_params`) and withholds confirmation until they match. | `test_fc_link.py::test_g5_*` (heartbeat with its own system ID refreshes the fake FC's timer; the template values pass; 9 unsafe values rejected); e2e `test_b0_*` (about 1 Hz heartbeat), `test_b1_bad_fc_params_never_confirm`, `test_b2_watcher_sigkill_*` (FC model fails safe ≤ 3.5 s after the kill), `test_sigterm_exits_fail_closed` | B0, B2b, B3a |
| **G6** FC arms without a watcher | See §3. (i) `ARMING_RUDDER` 0, no RC arm switches, arm only via the flight script, never force-arm: the watcher checks `ARMING_RUDDER` 0 in its readback. (ii) the DRAFT Lua aux-auth script, plus `ARMING_SKIPCHK` bit 17 clear and not −1 (checked in the readback). `--lua-auth` makes the watcher require `SCR_ENABLE` 1 too. | `test_fc_link.py::test_fake_fc_model_documents_the_stock_arming_gap` (model: never seen → arms; seen then lost → "GCS failsafe on"); the `ARMING_SKIPCHK`/`ARMING_RUDDER` cases of `test_g5_g6_param_check_rejects_unsafe_values`. **The Lua script itself is untested.** | B1c (with and without the Lua script), plus a B1 variant "watcher started, then stopped, then arm" (native refusal) |
| **G7** pgrep liveness is local and blind to a hang | `liveness.py`: per-dependency UDP beacons. A dependency is alive iff a beacon arrived within 1.0 s AND its `prog` counter (if reported) advanced within 2.0 s. `sidecars.py` gives the Pi side: `proc` (death and SIGSTOP via /proc state) and `topic` (output-topic message count, which catches a hang). A dependency never seen blocks confirmation without a LAND. | `test_inputs.py::test_g7_*` (monitor silence/progress/unknown; beacon over UDP; proc sidecar with a real SIGSTOP/SIGCONT/kill; topic core); `test_core.py::test_g7_*`; e2e `test_b9_dependency_loss_lands[SIGSTOP/SIGKILL]` (LAND ≤ 1.5 s), `test_b9_hung_dependency_beacon_alive_but_no_progress`, `test_b1b_*` | B9a/c/d, B1b |
| **G8** `--dep-loss stop` has no hardware meaning | `--dep-loss stop` is accepted for compatibility and mapped to the same withdrawal + ONE LAND + alert, with the mapping logged ("mapped to LAND + alert, G8"). | `test_core.py::test_g8_dep_loss_stop_maps_to_land`; e2e `test_b9_dependency_loss_lands[SIGSTOP-stop]` | B9b |
| **G9** the heartbeat file is local | The file is kept for the flight-script layer (same format, so `fly_trial.watch_ok()` reads it unchanged). The extra tokens are each one `key=value` (`pose= id= fc= latch= host=`). It is written every tick and immediately on any change. The networked path to the vehicle is the MAVLink heartbeat (G5). The same-machine requirement stands as pre-registered; `host=` records the machine. | e2e tests parse the file with `fakes.watch_ok_copy` (a labelled VERBATIM copy of `fly_trial.py:314-327`; fly_trial is not imported); `test_b2_*` (file stale ≤ 4.2 s after SIGKILL); `test_sigterm_*` | B1a/b, B2a |
| **G10** no height limit | `--box` REQUIRES 6 values (x/y/z min, max). The parser rejects fewer, saying the height limit is mandatory. | `test_core.py::test_g10_height_limit_top_and_bottom`; e2e `test_b4_box_breach_*[pos0]` (z 2.6 > 2.5) | B4a (top face), B4d |
| **G11** heartbeat masking | The watcher refuses system ID 255 and the FC's own ID. It never sends RC_CHANNELS_OVERRIDE or MANUAL_CONTROL. It sends HEARTBEAT only while confirmed. Any received message carrying the watcher's own system ID latches a "system-ID collision" withdrawal. The readback requires `MAV_GCS_SYSID` = its ID and `MAV_GCS_SYSID_HI` ≤ its ID (a range would mask). | `test_fc_link.py::test_g11_*` (refuses 255 and the FC ID; never sends the three refreshing types other than HEARTBEAT; detects a rogue sender with its ID); `test_core.py::test_sysid_collision_latches`; the `MAV_GCS_SYSID`=255 and `_HI`=250 cases | B2b (proves no other process refreshes the timer), B3a |

**Hang and stall (B3b):**
- e2e `test_b3b_watcher_sigstop_*`: SIGSTOP the watcher for 2 s, then SIGCONT, with the FC armed. The result:
  - no heartbeat is sent after the stop;
  - no LAND or mode command is sent after SIGCONT;
  - the latch is set (`latch=1`);
  - the heartbeat resumes only after the FC reports disarmed and recover_s has passed.
- Also covered by `test_core.py::test_stall_latches_without_land_and_stays_withdrawn_while_armed`.

## 3. Finding: how "no arming without the watcher" is achieved on the FC

Verified in `~/ardupilot` at `7bac20cbcc`. Re-verify on the board's firmware.

1. **Stock ArduCopter does NOT refuse to arm when the watcher was never started.**
   - `failsafe_gcs_check()` returns early while `sysid_mygcs_last_seen_time_ms() == 0` (`events.cpp:134-136`).
   - So `failsafe.gcs` never latches.
   - `AP_Arming_Copter::gcs_failsafe_check()` (`AP_Arming_Copter.cpp:519-525`) refuses only while `failsafe.gcs` is set.
2. **Stock ArduCopter DOES refuse to arm after the watcher was seen and then lost.**
   - The failsafe latches even while disarmed (`events.cpp` `failsafe_gcs_on_event`: disarmed → `announce_failsafe`).
   - Pre-arm then fails with "GCS failsafe on".
   - The fail-closed rule therefore holds natively for "started, then died". It does NOT hold for "never started".
3. **Proposed closure, in two layers (no firmware change):**
   - **(i) Procedure plus parameters, on stock firmware:**
     - arm only via the flight script (`require_watcher_before_arming`);
     - `ARMING_RUDDER` 0;
     - no `RCx_OPTION` 153/154/165 arm switches;
     - never force-arm (param2 2989/21196 skips every pre-arm check, `GCS_Common.cpp:5271`).
     - This needs the explicit ruling that the §7.2 pass rule asks for.
   - **(ii) Lua auxiliary arming authorisation** (`realflight/params/watcher_arming_auth.lua`, DRAFT):
     - it reports FAILED unless `millis() − gcs:last_seen()` < `FS_GCS_TIMEOUT` (`gcs:last_seen()` must also be non-zero);
     - it needs a board with scripting (`HAL_PROGRAM_SIZE_LIMIT_KB > 1024`), `SCR_ENABLE` 1, and `ARMING_SKIPCHK` bit 17 clear and not −1;
     - a force-arm bypasses it too;
     - the aux-auth state does not expire: a dead script leaves its last state in place. The script wraps its update in `pcall` and sets FAILED on an error, but a stopped interpreter cannot. The flight-script layer stays primary.
   - **Bench:** B1c with (i), then with (ii), plus a B1 variant "start the watcher, stop it, try to arm" for the native refusal in item 2.
4. **Consequence of `MAV_GCS_SYSID` = the watcher's ID:**
   - RC override and MANUAL_CONTROL from MAVProxy (255) are ignored.
   - Commands from 255 are still accepted, because `MAV_OPTIONS` bit 0 is clear (`GCS_Common.cpp:7393-7415`).
   - The safety pilot uses the real transmitter, so nothing is lost.

## 4. Still hardware-dependent (cannot be closed offline)

- **The mocap system** (supervisor input U7). It needs a forwarder from the vendor SDK (NatNet, Vicon DataStream, or VRPN) to the MCP1 packet; the format is in the `mocap.py` docstring. The real system must provide:
  - **rate:** ≥ 50 Hz;
  - **frame:** right-handed, z-up or y-up, in metres;
  - **body:** a stable body name/ID;
  - **tracking:** a tracked flag if available. Without one, the frozen-pose fallback applies, and B5b must say which case applies;
  - **timing:** a frame number and a mocap timestamp;
  - **latency:** median ≤ 50 ms, p99 ≤ 100 ms to the ground station (B7a), with chrony/PTP sync.
  - If a ROS 2 driver is chosen instead, wrap `pose_stamped_to_sample`. It has no tracked flag, so the frozen fallback applies.
- **Frame conventions:** check the `--up-axis` and `--body-yaw-offset-deg` signs at B6 (hand roll and pitch against the FC ATTITUDE). The box corners must be measured in the watch frame (B4d).
- **The FC side:**
  - the parameter names on the flashed firmware;
  - the GCS failsafe timing (B2b, B3a);
  - LAND acceptance and ACK, while disarmed and armed (B4a/b, B7b);
  - that nothing else refreshes the timer (B2b);
  - the Lua script on the board (B1c).
- **The MAVLink route to the FC:** a dedicated telemetry link, or a MAVProxy `--out` (`--fc` takes any pymavlink string). FC ATTITUDE must reach the watcher at ≥ 20 Hz for the identity check (`request_streams` asks for 25 Hz).
- **Beacon wiring on the Pi:**
  - The sidecars work now.
  - The preferred in-process `LivenessBeacon.beat(progress)` calls belong in the real-flight branch's flow tracker, bridges and estimator node. They were NOT added, because those files are used by the SITL flights.
  - Not every process has a ROS output topic (e.g. `flow_bridge.py` emits MAVLink). For those, the `proc` sidecar catches death and SIGSTOP but not a hang inside a running process.
- **Audible alert:** `--alert-cmd` must be pointed at a real sound on the ground station.

## 5. Open questions (for the user or supervisor)

1. **G6 ruling:** accept (i) procedure + `ARMING_RUDDER` 0 for B1c, or require (ii) the Lua script once the board is known?
2. **Watcher system ID:** 211 is a placeholder. Confirm it is unused on the real network (companion, MAVProxy, flight script).
3. **Identity in flight:**
   - after proof, a mocap/FC disagreement is only alerted (not pre-registered as an action);
   - "identity proven by a hand motion" is required before EVERY session; that is a procedural step to add to the B0 day-start checklist.
   - Should an in-flight disagreement withdraw the confirmation?
4. **FC link loss** (no FC HEARTBEAT for 3 s) withdraws the confirmation without a LAND, because a LAND cannot reach the FC anyway. Is that acceptable, given that the FC's own GCS failsafe then acts?
5. **The LAND retry policy** (re-send until ACKed, at most 5 × 0.3 s): is it compatible with B10b's "at most ONE LAND"? It is one LAND decision per episode; the retries are the same un-ACKed command.
6. **B10b across layers (requirement on H10, the real flight script):** when the file flags drop, `fly_trial.py` raises `WatcherLost` and commands LAND itself. If the safety pilot has already taken ALT_HOLD after the watcher's ACKed LAND, that second LAND would re-command LAND, which B10b forbids. The adapted real flight script must NOT command LAND if the FC is already in a pilot mode (ALT_HOLD/STABILIZE) or once the FC is in LAND. `fly_trial.py` was not touched here (off-limits).
7. **Episode clearing:** the watcher re-confirms after any episode once the FC is disarmed and all checks hold for 2 s, with no operator action. Should a manual reset be required instead?

## 6. Status for `docs/real_flight_readiness.md` (NOT edited here; for whoever owns that file)

- **F1** (mocap client): the watcher-side INTERFACE and a UDP adapter are built and tested offline. The vendor forwarder is still to be written once the system is known (U7).
- **F2** (watcher logic for real sensors): **built** (`realflight/watcher/`; G2, G3, G7, G8, G10). Offline tests pass.
- **F3** (heartbeat to the FC + FC-side layer + LAND command):
  - **built and tested offline:** the watcher side (G4, G5, G11) and the parameter template;
  - **not done:** the FC-side proof (bench) and the Lua arming script (draft only).
- **F4** (bench tests): **not run** (no hardware). Each B-test's watcher-side behaviour has an offline analogue (§2).
- **H10** (real flight script): `fly_trial.py` is unchanged and can consume the new watcher's file as is. NEW requirement (B10b, §5 item 6): no LAND from the script when the FC is already in a pilot mode or in LAND.

## 7. Housekeeping

- Before the commit: no `arducopter` process was running, and `~/thesis_data/FLIGHT_LOCK` was checked.
- Final suite run (after the identity-latency change): **73 passed in 85 s**.
- The tests leave no processes or sockets behind (`ss -uapn | grep python` showed 0 after every run).
- Not edited: METHODOLOGY.md, numbers.md, `wall_watch.py`, `closed_loop_run.sh`, `fly_trial.py`, `run_trial.sh`, `docs/real_flight_readiness*.md`.
