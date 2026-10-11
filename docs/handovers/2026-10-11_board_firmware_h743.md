# Handover 2026-10-11: board firmware for a representative STM32H743 (ruling item 2a)

One stage agent. The ruling is METHODOLOGY "RULING (user, 2026-10-11)", item 2(a). Firmware was built for two boards.
**Nothing was flashed, flown or installed.** METHODOLOGY.md and numbers.md are untouched. The full write-up, with the
flashing and rollback plan, is `docs/board_firmware_plan.md`.

## State
- **`~/ardupilot_ukf` branch `board-h743` → `6280a35745`**, on `rung1-geometry` `16535f9a29`. It is NOT merged.
  - The checked-out branch (`ukf-jitter-fix` `abb0357d0f`) and `~/ardupilot_ukf/build` are untouched. The installed
    Replay `e8e9feac` and UKF_Equiv `537e0dcd` were re-checked after the stage.
- **The build** ran in a temporary `git worktree` in the scratchpad. Its submodules were `--reference`d to the main
  checkout (waf, mavlink + pymavlink, ChibiOS, DroneCAN ×4, littlefs, lwip, CrashDebug + CrashCatcher). All builds ran
  under `heavy.py`, one at a time. The worktree has been removed (`git worktree remove --force`).
- **The toolchain was present:** `/opt/gcc-arm-none-eabi-10-2020-q4-major` (10.2.1). Nothing was installed.
- **thesis_ws (this worktree branch):**
  - `docs/board_firmware_plan.md` (new);
  - `eval/diag/board_h743/` (the build, identity, stack, ELF and map scripts);
  - `eval/results/board_h743/` (`sizes.json`, the size tables, per-library flash, the thesis symbols, the with − without
    deltas, the stack usage, the SITL identity outputs, `hwdef.h` per build);
  - this handover.

## 1. The fork change (`6280a35745`)
- **`AP_NAVUKF_ENABLED` is a build option.**
  - Default unchanged: on for SITL, off for every board.
  - On a board: `--enable-THESIS_NAVUKF` (a new `build_options.py` Feature), or `define AP_NAVUKF_ENABLED 1` in a
    hwdef.
  - One switch covers the UKF, the FGO, the `ODOMETRY` hook and `thesis_nav_check`. **The FGO has no separate flag**;
    its size was measured from the symbols instead.
- **`AP_NAVUKF_REPLAY_IO_ENABLED`** (SITL only): the Replay-only stdio goes through no-op wrappers on a board. No
  Replay strings are in the board ELF [V].
- **`AP_NAVUKF_TFAIL_ARM_GUARD`** (every board, not SITL): arming is refused with `AHRS_UKF_TFAIL` ≠ 0, in
  `AP_AHRS::pre_arm_check` and unconditionally in `AP_Arming_Copter::arm_checks`.
  - **UNTESTED:** it is compiled out of SITL. Bench check P5 and costing-doc V7 cover it.
  - Copter only; Plane needs its own line.
- **Stack fix, found by the board build.** `-Werror=frame-larger-than=1300` failed the first build:
  - `NavUKF::predict` had 2,256 B of frame, and `sigma_points` 1,848 B;
  - the main-thread stack is 7,168 B.
  `L` and `Pm` are now static scratch, zeroed every call (as the existing static `fs`). The frames are now 456 B and
  56 B, and the deepest UKF chain is about 1.6 kB.

## 2. Results (details and tables in `docs/board_firmware_plan.md` §2)

| board | limit (B) | without: used / free | with UKF+FGO: used / free | Δ flash | Δ static RAM |
|---|---|---|---|---|---|
| MatekH743 (tight) | 1,703,936 | 1,545,012 / 158,924 | 1,569,196 / **134,740** | +24,184 | +40,296 |
| Pixhawk6X (roomy) | 1,966,080 | 1,674,900 / 291,180 | 1,698,684 / **267,396** | +23,784 | +40,296 |

- **All four builds have 0 warnings.**
- **Split** [V symbols, E plumbing]:
  - **flash:** UKF ≈ 19 kB and FGO ≈ 5 kB;
  - **RAM:** UKF ≈ 25 kB (incl. 7.3 kB of static scratch) and FGO ≈ 14.8 kB (the 400-entry IMU ring buffer).
- **No heap use.**
- **The FGO input path is linked** (`handle_odometry` → `NavFGO::writeState`, objdump) [V].
- **CPU [E]:** about 2–6 % at 80 Hz on the H7. This scales the measured 6.2 µs/event of `UKF_Equiv` on the
  workstation by 20–50×. It agrees with Part C's 5–8 %. The bench `PM` measurement is the real figure.
- **Compile-out candidates [E upper bounds, linker map]:**
  - Scripting ~144 kB (needed only for the watcher's Lua arming-auth draft);
  - Mount ~41 kB;
  - Ethernet lwip + networking ~54 kB (Pixhawk6X);
  - OSD ~30 kB (+ MSP 10 kB);
  - Proximity 19 kB, Airspeed 16 kB, Camera 16 kB, ADSB 11 kB, GyroFFT 11 kB, EFI 7 kB, and smaller.
  - **None is needed for the UKF+FGO build itself.**

## 3. SITL byte-identity (re-proved after the stack change)
- **SITL rebuild:** Replay `acda76be`, UKF_Equiv `b4f45b98`, copter `a5070045`, all with 0 warnings.
- **Against `rung1-geometry` `16535f9a29`** (the stored outputs of the previous stage, `r1ukf/a2/<log>/new`):
  - `cl_a_tex_half` (type 3): all four CSVs byte-identical;
  - `cl_ukf_b_tex_r1_half_v2` (type 12, EXTYAW): all four CSVs byte-identical.
- **Against the INSTALLED Replay `e8e9feac`** (type-12 log only, where installed = rung1): `ukf_shadow.csv` and
  `ukf_inputs.csv` are byte-identical.
- **UKF_Equiv**, on all 7 tape runs from 2026-10-09: byte-identical to the installed `537e0dcd`, and to the stored port
  outputs.

## 4. Artefacts (scratchpad; NOT committed)
`/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/h7/out/`:
- **`MatekH743_with/`:** `arducopter.apj` md5 `7d8652f3…`, `git_identity 6280a357`. Also there:
  - `arducopter_with_bl.hex`, `arducopter.bin` and `vehicle.elf`;
  - `Linker.map` and `compile_commands.json`;
  - `size_A.txt` and `nm.txt`.
- **`MatekH743_without/`:** `.apj` `79e2c872…`.
- **`Pixhawk6X_with/`:** `.apj` `f68a3f5b…`.
- **`Pixhawk6X_without/`:** `.apj` `ec7b189f…`.
- **`MatekH743_with_precommit/`:** the first successful build. It is identical in size, but its identity is
  `16535f9a`. Do not use it.
- **`sitl/`:** the build logs, `md5.txt` and `bin/` (Replay, UKF_Equiv and the copter SITL binary).
- **Elsewhere:** the stack-usage `.su` files are in `../su_before`, `../su_after` and `../su_px6`; the identity outputs
  are in `../ident/`.

## 5. Open items for the exact board (and for the user)
1. **The exact board and its hwdef.**
   - Rebuild with `--board <it> --enable-THESIS_NAVUKF`.
   - Re-measure flash (G2: ≥ 32 kB free) and the stack.
   - Check the multi-IMU question (D18 open item) on that board.
2. **Compass.** If none is fitted, add `define ALLOW_ARM_NO_COMPASS` (an extra hwdef).
3. **Rangefinder below its minimum on the ground** (costing doc U4): the UKF does not initialise there, so with the UKF
   active it cannot arm. This is a port change, not in this build.
4. **The bench:** P1–P10 of the plan, especially:
   - P5 (the TFAIL refusal, untested);
   - P7 (main-thread stack free from `@SYS/threads.txt`);
   - P8 (`PM` CPU);
   - P10 (`MEMINFO`).
5. **Scripting.** Keep it (for the watcher Lua arming-auth draft) or replace it with a C++ check in the fork. This
   decides the Matek margin.
6. **QuadPlane:** the TFAIL refusal and B1–B3 (`docs/quadplane_costing.md`).
7. **Merging `board-h743`** (it carries `rung1-geometry`) is the user's call. Rung 1 still flies `7bac20cbcc`,
   unmodified.
8. **Optional:** a separate `AP_NAVFGO_ENABLED` flag, so that a UKF-only build drops the FGO's ~5 kB of flash and
   ~15 kB of RAM.
