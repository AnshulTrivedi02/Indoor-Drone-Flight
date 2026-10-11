# Board firmware (rung 3): build, budget, flashing and rollback for a 2 MB STM32H743

Status: written 2026-10-11 for item 2(a) of the ruling "PLAN AND BUILD TOWARDS REAL FLIGHTS" (METHODOLOGY, 2026-10-11).
Firmware was BUILT for two representative boards. **Nothing was flashed or flown.** The final build waits for the
exact board (§7). Handover: `docs/handovers/2026-10-11_board_firmware_h743.md`.

Labels:
- **[V]** verified: built, measured from the ELF or `.apj`, or read in source;
- **[E]** an estimate, with its basis;
- **[U]** unverified (needs the board or a bench).

**Rung 1 does NOT fly this firmware.** Rung 1 flies `7bac20cbcc` built UNMODIFIED (ruling item 1), with
`AHRS_EKF_TYPE 3`. This document is for rung 3, plus the optional rung-1 "fork in shadow" variant (the costing doc
§13). That variant is the user's call: if it is chosen, `AHRS_EKF_TYPE` stays 3 and only `AHRS_UKF_ENABLE` changes.

---

## 1. What was built

**The fork change** is `~/ardupilot_ukf` branch `board-h743`, commit `6280a35745`. It is based on `rung1-geometry`
`16535f9a29`. It is NOT merged, and the checked-out branch and the installed SITL binaries are untouched.
- **A build option instead of SITL-only.** `AP_NAVUKF_ENABLED` keeps its default: on for SITL, off for every other
  board. On a board it is switched on in one of two ways:
  - **waf:** `./waf configure --board <board> --enable-THESIS_NAVUKF` (a new `build_options.py` Feature);
  - **hwdef:** `define AP_NAVUKF_ENABLED 1` (the board's hwdef, or an `--extra-hwdef` file).
  It compiles in:
  - the UKF (`AHRS_EKF_TYPE 12`);
  - the FGO input and output predictor (`AHRS_EKF_TYPE 13`);
  - the `AHRS_UKF_*`/`AHRS_FGO_*` parameters;
  - the `ODOMETRY` hook;
  - Copter's `thesis_nav_check`.
  The FGO is not separately switchable; its share is measured from the symbols (§2.2).
- **Replay-only file I/O guarded.** `AP_NAVUKF_REPLAY_IO_ENABLED` defaults to SITL only. The CSV, input-dump and report
  writes now go through `ukf_fopen`/`ukf_fprintf`/`ukf_fflush`, which are no-ops on a board.
  - [V] None of the Replay strings (CSV headers, report keys) are in the board ELF.
  - The other Replay test hooks (`force_*`, `mark_replay`, the AP_DAL hook pointers) are only ever called by
    `Tools/Replay`. They stay compiled in: a few hundred bytes, and `nullptr` on a vehicle.
- **Arming refused with `AHRS_UKF_TFAIL` ≠ 0 on a real board.** `AP_NAVUKF_TFAIL_ARM_GUARD` defaults to every board
  except SITL, because the SITL safety tests arm with the hook set. The refusal is in two places:
  - `AP_AHRS::pre_arm_check` (a pre-arm message);
  - `AP_Arming_Copter::arm_checks`, unconditionally: like the compass gate, `ARMING_SKIPCHK` does not skip it.
  The bench forced-invalidity test sets TFAIL **after** arming, which still works (`NavUKF::update` reads it live).
  **Untested:** it is compiled out of SITL. Bench check P5 (§5) and costing-doc V7 test it.
- **Main-thread stack fix (found by this build).** The first board build FAILED with
  `-Werror=frame-larger-than=1300`:
  - `NavUKF::predict` had a 2,256 B frame, and `sigma_points()` 1,848 B (two `double[15][15]` locals);
  - the ChibiOS main thread has `PROCESS_STACK` = 0x1C00 = **7,168 B** on both boards (`hwdef.h`, [V]);
  - the predict chain alone (update → predict → sigma_points → process) was about 4.9 kB of it [V, `-fstack-usage`].
  The two matrices are now static scratch, zeroed on every call (exactly the former `= {}`), as the existing static
  `fs` already was. The frames are now predict 456 B and sigma_points 56 B. The deepest UKF chain is about 1.6 kB
  (update 384 → fuse_heading 512 → update_scalar 456 → h 224 → sigma_points 56) [V frames, E chain]. SITL output is
  unchanged (§2.5).
- **Builds** (Copter, `heavy.py`, nice 19, `arm-none-eabi-gcc` 10-2020-q4-major): MatekH743 and Pixhawk6X, each with
  and without the option. All four built with **0 warnings**, as did the SITL rebuild (Replay, UKF_Equiv, copter).
  Nothing was flashed.

## 2. The budget

### 2.1 Flash against the board's limit [V, the `.apj` header and the waf size table]

"2 MB" is not the usable space. The limit is the board's `flash_total`:
- Pixhawk6X: 2048 KB less the 128 KB bootloader = **1,966,080 B**;
- MatekH743: also less 256 KB of flash parameter storage = **1,703,936 B**.

| board (class) | build | image (B) | free (B) | free % of limit | `.apj` md5 |
|---|---|---|---|---|---|
| **MatekH743** (tight) | without the option | 1,545,012 | **158,924** | 9.3 % | `79e2c872…` |
| | **with UKF + FGO** | 1,569,196 | **134,740** | 7.9 % | `7d8652f3…` |
| **Pixhawk6X** (roomy) | without the option | 1,674,900 | **291,180** | 14.8 % | `ec7b189f…` |
| | **with UKF + FGO** | 1,698,684 | **267,396** | 13.6 % | `f68a3f5b…` |

- **The backends cost +24,184 B (Matek) and +23,784 B (Pixhawk6X)** of flash, inside Part C's 25–50 kB estimate.
- **Both boards fit with a wide margin.** The Matek keeps 135 kB free, the Pixhawk6X 267 kB.
- **"Without" is not exactly stock.** It is the fork with the option off. It still carries the ungated AP_DAL hook
  pointers and the empty `thesis_nav_check` task, so it is stock `7bac20cbcc` plus a few hundred bytes [E].
  For comparison, the published stable `dbe79216` Copter builds have 154,020 B (Matek) and 286,652 B (Pixhawk6X) free
  (`docs/quadplane_costing.md` §9).

### 2.2 What each backend adds [V, `nm -S` on the ELF; identical on both boards]

| part | code (B) | static RAM (B) |
|---|---|---|
| UKF core (`NavUKF::`) | 13,226 | 7,320 (static scratch: `fs` 3,720, `L` 1,800, `Pm` 1,800) |
| UKF AHRS backend (`AP_AHRS_UKF::`) | 1,268 | — |
| FGO input + output predictor (`NavFGO::`) | 3,322 | — |
| FGO AHRS backend (`AP_AHRS_FGO::`) | 1,272 | — |
| `thesis_nav_check` | 160 | 2 |
| **named thesis symbols** | **19,248** | 7,322 |
| the rest of the +24.2 kB: `AP_AHRS` switch arms, the GCS `ODOMETRY` hook, the arming lines, parameter tables, strings | ≈ 4.9 k [E, by difference] | — |

- **UKF ≈ 19 kB of flash and FGO ≈ 5 kB** [E: the named symbols, with the plumbing split evenly]. The FGO is small,
  because GTSAM runs off-board; this is only the state input and output predictor.
- [V] **The FGO input path is linked on both boards.** `GCS_MAVLINK::handle_odometry` calls `NavFGO::writeState`
  (objdump). The `ODOMETRY` dispatch sits behind `HAL_VISUALODOM_ENABLED`, which is on for every board above 1 MB.

### 2.3 Compile-out candidates (if a board or a later feature needs the space)

Flash per library is the kept input sections in the linker map (`map_by_lib.py`). These are **[E] upper bounds**:
disabling a feature may leave shared code in.

| feature (waf `--disable-<label>`) | Matek (B) | Pixhawk6X (B) | indoor flow/mocap use |
|---|---|---|---|
| `SCRIPTING` (Lua) | 143,790 | 145,903 | **needed only for the watcher's Lua arming-auth draft** (`realflight/params/watcher_arming_auth.lua`, G6(ii)). A C++ check in the fork would cost under 1 kB |
| `MOUNT` (gimbals) | 40,921 | 40,941 | none |
| Ethernet: `lwip` + `AP_Networking` | — | 46,142 + 7,780 | none unless the Pi link is Ethernet |
| `OSD` (+ `MSP`) | 29,899 (+ 10,087) | 27,562 (+ 10,079) | none (an analogue FPV feed on a cinewhoop may want OSD) |
| `PROXIMITY` | 18,947 | 18,947 | none |
| `AIRSPEED` | 16,371 | 16,371 | none on Copter (keep on a QuadPlane) |
| `Camera` | 15,656 | 15,656 | none |
| FrSky / CRSF / Spektrum telemetry (`AP_Frsky_Telem`, `AP_RCTelemetry`) | 11,063 + 17,176 | same | keep the one the RC link uses |
| `ADSB` | 10,600 | 10,600 | none |
| `GyroFFT` | 10,662 | 10,662 | optional (notch tuning) |
| `EFI`, `GENERATOR` | 7,426 | 7,426 | none |
| `PRECLAND`, `TERRAIN`, `VIDEO_TX`, `MODE_FOLLOW` | 6,315 / 6,285 / 6,042 / 4,824 | same | none |
| **Keep** | EKF3 (121,703), `OPTICALFLOW`, the rangefinder, `EKF3_EXTNAV` + `VISUALODOM` (the FGO/ODOMETRY and tag routes), `AC_AutoTune` (13,784; tuning), logging and `LOG_REPLAY` | | |

- Without scripting and mount, the Matek would gain about 185 kB [E] for anything else.
- **Nothing needs compiling out for the UKF+FGO build itself** on either board.

### 2.4 RAM [V static, E split] and CPU [E]

**RAM.** The backends add **+40,296 B of static RAM** (`.bss`) on both boards. There is no heap use (no `new` or
`malloc` in the thesis sources).
- The `copter` object grows 39,712 → 72,680 B (Matek), because `NavUKF` and `NavFGO` are `AP_AHRS` members.
- The UKF's static scratch is 7,320 B.
- Split [E, from the member sizes]:
  - **NavFGO ≈ 14.8 kB**, of which the 400 × 36 B IMU ring buffer (1 s at 400 Hz) is 14.4 kB;
  - **NavUKF ≈ 25 kB** in all: the event queue (`EV_MAX 64` × the `Ev` record) about 9 kB, P/sigma/state about
    6 kB, plus the static scratch.
  - The costing doc's ~20 kB estimate left out the FGO.
- **Against the H743's ~1 MB this is small.** But it comes out of the linker's first RAM region (`ram0`):
  - Matek: ram0's free heap goes from 119,756 to **79,460 B**. The other regions (AXI and SRAM4) also feed the heap,
    and their sizes are in `hwdef.h`;
  - Pixhawk6X: 375,596 → 335,300 B.
  - Lua's heap (`SCR_HEAP_SIZE`) and the logger buffers come from the same pool. So on the bench check `MEMINFO`
    free memory with every feature that will fly enabled (P10).
- **The main-thread stack** is 7,168 B on both boards; the UKF's deepest chain after the fix is about 1.6 kB (§1).
  The real margin is measured on the bench from `@SYS/threads.txt` (P7).

**CPU [E].** Two estimates agree:
- **Part C §5.3** (flop count): about 5–8 % at 80 Hz in double, about 0.3–0.4 ms per predict.
- **A quick scaling from this build.**
  - `UKF_Equiv` replays the 45,277-event `dsn_tex_r2` tape (one ~5.5-minute flight) in 0.28 s on the workstation
    (i7-8700). That is **6.2 µs per event** (predicts and scalar updates; harness I/O included).
  - A 480 MHz Cortex-M7 in double is assumed to be 20–50× slower than the workstation core: 9× in clock, 2–5× in IPC
    and software transcendentals [E].
  - That gives about 0.12–0.3 ms per event. At about 80 predicts plus about 100 updates per second, that is
    **about 2–6 % CPU**.
- **Onboard extras the tape leaves out:**
  - the current-time output propagates the about 5 queued predict steps every 400 Hz loop, about +0.5 % [E];
  - the FGO output predictor replays up to about 100 buffered IMU steps per state, at about 10 Hz [E].
  - EKF3 (2 lanes) keeps running in shadow. If the loop overruns, the documented relief is `EK3_IMU_MASK 1`.
- **The real figure comes from the bench:** `PM` (loop time, long loops) with the shadow on, against off (P8).

### 2.5 SITL byte-identity [V]

The SITL behaviour is byte-identical. The SITL rebuild of `board-h743` was Replay `acda76be`, UKF_Equiv `b4f45b98` and
copter `a5070045`, all with 0 warnings.
- **Against `rung1-geometry` `16535f9a29`** (the previous stage's stored outputs, Replay `a1f67e7d`). These logs carry
  the D18 rule, so this is the reference that includes the geometry and derotation work. Results:
  - `cl_a_tex_half` (type 3): `ukf_shadow.csv`, `ukf_inputs.csv`, `ukf_derot.csv` and `ukf_geometry.csv` are all
    byte-identical;
  - `cl_ukf_b_tex_r1_half_v2` (type 12, `UKF_EXTYAW=1`): all four are byte-identical.
- **Against the INSTALLED Replay** (`e8e9feac`, `abb0357d0f`), used only where installed equals rung1 (a type-12 log):
  `cl_ukf_b_tex_r1_half_v2` `ukf_shadow.csv` and `ukf_inputs.csv` are byte-identical.
- **UKF_Equiv on the 2026-10-09 tapes** (cfi60_A, cfi60_C, cfi10_B with diag(P), dsn_tex_r2 and h_s1_r1, plain and
  `QDIAG`): the new build matches the installed `537e0dcd` byte for byte. It also matches the stored port outputs.
- Evidence: `eval/results/board_h743/sitl_identity_*.txt`.

---

## 3. Before flashing: the backup (every time)

1. **Write down the board's identity.** Record the board name, the bootloader, and the current firmware version and git
   hash. The GCS shows these; so does `uploader.py --identify` (`Tools/scripts/uploader.py:1154`, [V] the option exists).
2. **Back up the parameters.** Do this two ways:
   - MAVProxy `param save backup_<date>_<board>.parm`, or the QGC / Mission Planner "save parameters to file";
   - MAVFTP: copy `@PARAM/param.pck` (the complete set, including defaults).
   Store both in `~/thesis_data/fc_backups/<board>/<date>/` and record their md5.
3. **Back up the current firmware image.** Use `uploader.py --download <file>` (`uploader.py:1153`, [U] not tested on
   our board). If it does not work, record the exact stock release and board (`firmware.ardupilot.org` keeps every
   release), so that the identical `.apj` can be fetched again.
4. **Copy the logs off.** Download the SD-card logs and `@SYS/` (`crash_dump.bin` if present, `threads.txt`,
   `timers.txt`) before any reflash.
5. **Have the stock image ready** before flashing anything: the rung-1 build of `7bac20cbcc` (unmodified) for the same
   board, plus the published stable `.apj` for that board.

## 4. Flashing (the fork `.apj` through the existing ArduPilot bootloader)

- **The bootloader is NOT replaced.** A board that already runs ArduPilot keeps its bootloader. Flash only the
  application `.apj`. Never flash `*_with_bl.hex` unless the board has no ArduPilot bootloader (see below).
- **The file:** `arducopter.apj` from the board build (§1). Its JSON header carries `board_id`, `image_size`,
  `flash_total` and `git_identity`. Check `board_id` against the board, and `git_identity` against the `board-h743`
  commit, BEFORE flashing.
- **Three equivalent ways to flash (pick one, over USB):**
  - **uploader.py:** `python3 Tools/scripts/uploader.py --port /dev/ttyACM0 <file>.apj`. It reboots the board into
    the bootloader over MAVLink, then erases, programs and verifies with a CRC. The board-type check refuses a wrong
    `board_id`. **Never pass `--force`.**
  - **MAVProxy:** `fw flashfile <file>.apj` calls the same `uploader.py` (MAVProxy `mavproxy_firmware.py:199-201`,
    [V] in `~/venv-ardupilot`).
  - **QGroundControl:** Vehicle Setup → Firmware → "Advanced settings" → "Custom firmware file". Mission Planner:
    "Install Firmware" → "Load custom firmware".
- **A board with no ArduPilot bootloader** (for example a Matek board shipped with Betaflight or INAV): DFU once, with
  `arducopter_with_bl.hex` (STM32CubeProgrammer or `dfu-util`, BOOT button held). From then on use the `.apj` path.
  This is a one-time step, done with the supervisor.
- **After the flash:**
  - reboot;
  - confirm the identical image with `uploader.py --verify-firmware-is <file>.apj` (`uploader.py:1155`, [U] not tested
    on our board);
  - confirm the GCS banner shows the `board-h743` git hash.

## 5. After flashing: what to verify (bench, props OFF)

| # | check | pass |
|---|---|---|
| P1 | Banner and version: git hash = `board-h743` commit; the board name | exact match |
| P2 | Parameters read back: every value of the rung's parameter file (`check_parm.py` then a full readback; the eeprom gotcha, Known Issue #10, applies on hardware) | 0 mismatches |
| P3 | **Backends compiled in:** the parameters `AHRS_UKF_ENABLE`, `AHRS_UKF_TFAIL`, `AHRS_FGO_ENABLE` exist (stock firmware has no such parameters) | present |
| P4 | `AHRS_EKF_TYPE 3`, `AHRS_UKF_ENABLE 0`, `AHRS_FGO_ENABLE 0`: the vehicle is stock EKF3 ("backends disabled reproduces EKF3", costing doc §2) | EKF3 active; the same pre-arm and arming behaviour as stock |
| P5 | `AHRS_UKF_TFAIL 1`, then try to arm | **refused**: "AHRS_UKF_TFAIL is set (test hook)" (pre-arm and at arming). Then set it back to 0 |
| P6 | Shadow on: `AHRS_UKF_ENABLE 1`, `AHRS_EKF_TYPE` still 3; hand-carry | `XUKF`/`XUKO`/`XUKS` logged; the UKF initialises (the rangefinder must read above its minimum: see §8) |
| P7 | **Main-thread stack margin:** MAVFTP `@SYS/threads.txt` after 10 min with the shadow on | the main thread's free stack is reported; ≥ 1 kB free [E threshold] |
| P8 | CPU: `PM` log messages (load, long loops) with the shadow on, against P4 | no new long loops; load increase within the [E] budget of §2.4 |
| P9 | `@SYS/timers.txt` and `@SYS/uarts.txt`: no new errors | as before the flash |
| P10 | Free memory: MAVLink `MEMINFO.freemem` with every flying feature enabled (scripting heap included) | no allocation failure at boot; record the figure |

**`AHRS_EKF_TYPE` stays 3 for rung 1** (and for every flight until rung 3's own pre-registration says otherwise).
`check_parm.py` already refuses 10. Rung 3 changes it to 12 (UKF) or 13 (FGO) only on the bench and SITL gates' pass.

## 6. Rollback to stock (exact steps)

Do this in this order. Stock firmware has no AHRS types 12/13, so the vehicle must be left on EKF3 BEFORE the stock
image boots.
1. On the fork, set `AHRS_EKF_TYPE 3`, `AHRS_UKF_ENABLE 0`, `AHRS_FGO_ENABLE 0`, `AHRS_UKF_TFAIL 0`. Read them back.
2. Flash the stock `.apj` (the unmodified `7bac20cbcc` build for the board, or the published release) by the same
   method as §4.
3. Reboot. Check the banner shows the stock hash.
4. **Restore the pre-flash parameter backup** (§3 step 2): MAVProxy `param load <backup>.parm`, or the GCS. Reboot.
5. **Read every value back** against the backup (`param diff` in MAVProxy, or `check_parm.py`-style comparison). The
   eeprom gotcha applies.
6. Note the leftovers. The fork's `AHRS_UKF_*`/`AHRS_FGO_*` values (AP_AHRS sub-groups 22 and 23) stay in parameter
   storage. Stock firmware ignores them (no such group), so they are harmless.
   - On a board that keeps parameters in flash (MatekH743, KakuteH7) they also survive a reflash.
   - If they must go: `FORMAT_VERSION 0` + reboot resets ALL parameters, so restore the backup afterwards.
7. Bench-check as P1, P2 and P4.

**If the board does not boot** (a hard fault in the fork):
- the ArduPilot bootloader is untouched, so it still accepts a new `.apj`. Power up with USB and run `uploader.py`
  within the bootloader's wait window, or hold the bootloader button where the board has one;
- the last resort is DFU (BOOT pin) with the stock `*_with_bl.hex`, which restores the bootloader too.
- Before the reflash, copy `@SYS/crash_dump.bin` (or the SD card's `crash_dump.bin`) for the fault analysis.

## 7. Go / no-go before the first powered test on the fork

Every item must be **go**. One **no-go** means stock firmware stays on the vehicle.

| # | item | go when |
|---|---|---|
| G1 | The exact board is named, and the firmware was built for its hwdef (not the stand-in of §1) | the `.apj` `board_id` = the board's |
| G2 | Flash free ≥ 32 kB after the fork, for the exact board and feature set | §2 table, re-measured |
| G3 | SITL byte-identity of the `board-h743` commit vs the reference, re-run if the source changed | identical (§2.5) |
| G4 | P1–P10 all pass on the bench | as in §5 |
| G5 | Rollback rehearsed once on the bench (§6 steps 1–7), and the stock `.apj` and parameter backup are on the laptop | done |
| G6 | `AHRS_EKF_TYPE 3` confirmed after every flash, and `AHRS_UKF_TFAIL 0` | readback |
| G7 | The rung's pre-registration and the SITL gates of the costing doc (V1–V7), for anything beyond shadow | signed off |
| G8 | Main-thread stack margin (P7) and no new long loops (P8) | measured |

## 8. What changes with the exact board

- **The hwdef.** Build with `--board <exact board>`. The flash limit is the board's `flash_total`, not "2 MB":
  - Pixhawk class: 1,966,080 B;
  - boards that keep parameters in flash (Matek, Kakute): 1,703,936 B.
  The stack (`PROCESS_STACK`), the IMU count (multi-IMU: the D18 open item) and `HAL_WITH_EKF_DOUBLE` come from the
  hwdef too.
- **The enable.** Either `--enable-THESIS_NAVUKF` at configure time, or a one-line `define AP_NAVUKF_ENABLED 1` in an
  `--extra-hwdef` file (keep the board's own hwdef stock).
- **The feature set.** If the margin is under G2's threshold, compile out features (§2.3) with `--disable-<label>` or
  `--extra-hwdef`, and re-measure.
- **No compass fitted:** add `define ALLOW_ARM_NO_COMPASS` (costing doc §4), or Copter's compass arming gate refuses
  to arm.
- **The rangefinder below its minimum on the ground:** the UKF does not initialise until the range exceeds
  `RNGFNDn_MIN`, so with the UKF active it cannot arm. This is a known open port change (costing doc U4), not part of
  this build.
- **QuadPlane:** the arming refusal of `AHRS_UKF_TFAIL` is wired into Copter's `arm_checks` only. Plane needs its own
  line, plus B1–B3 of `docs/quadplane_costing.md`.
- **Numerics:** board and SITL are not bit-identical (newlib against glibc, FMA). Equivalence transfers statistically:
  replay a board log in SITL Replay (costing doc U10).
