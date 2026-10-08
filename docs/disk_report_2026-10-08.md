# Disk report, 2026-10-08 (supervisor item 1) — REPORT ONLY, nothing changed

**Free space:** 16 GB of 476 GB (97% used). Below "remaining need + 50 GB" (see below), so **new flights are paused
until ruled**. No external drive is attached; only the internal NVMe is present.

## Breakdown (GB = 1e9; from an exact per-topic SQL sum over every bag)

| location | total | forward-camera images | downward-camera images | other bag topics | dataflash | other files |
|---|---|---|---|---|---|---|
| `~/thesis_data/trials` (217 trials) | 330.6 | **304.0** | 8.8 | 10.4 | 4.7 | 2.6 |
| `~/thesis_data/trials_pre_rerun` (43) | 79.9 | **75.9** | 0 | 2.5 | 0.7 | 0.9 |
| rest of `thesis_data` (batches, d*, phase*) | ~5 | | | | | |
| code, venvs, ArduPilot trees (`ardupilot`, `ardupilot_ukf`, `ardupilot_diag`) | ~13 | | | | | |

**The forward-camera image topic is 380 of 410 GB of trial data.**

Largest groups:
- each 9-flight forward set (`fwdc_*`, `fwdplainc_*`, the superseded no-ceiling `fwd_*`, and the pre-rerun `fwdc`
  and `fwdplainc` originals): 29–30 GB;
- closed-loop UKF / FGO / C++-EKF3 sets: 23 / 21 / 20 GB;
- `p1c` and its pre-rerun copy: 20 GB each;
- `f4_*`: 19 GB each;
- each closed-loop ground test or shadow flight: ~3.3 GB.

## What the remaining simulation work needs

- **Tag-holding experiment (item 3):** about 30 flights. If the forward images are **not** recorded (tag
  detection is live; `/tags/raw` is enough), that is ~0.15 GB per flight ≈ **5 GB**. With forward images it is
  ~3.3 GB per 5 min ≈ **100 GB**.
- **Need + 50 GB margin:** **≈ 55 GB without images, ≈ 150 GB with images.** Free now: 16 GB.

## Options (none applied)

**1. Lossless file-level compression of the bag files (RECOMMENDED; saves ≈ 290 GB, conservatively).**
- `bag_0.db3` → `bag_0.db3.zst` (zstd -9), decompressed on demand. Decompression takes about 6 s per bag.
- **Verified on `fwdc_tex_r1`:**
  - 3.23 GB → 0.63 GB (5.1×), in 39 s;
  - the decompressed file has the same sha256 as the original;
  - the UKF heading-arm replay from it is byte-identical to the replay from the original, which is also identical to
    the run behind the committed results.
- **Image compressibility by group** (zstd-9 on 200 frames): textured walls / closed loop 4.5×, plain walls on a
  textured floor 7×, ceiling blank/trans 11×, plain walls on blank/trans up to 170×, no-ceiling (sky) 2.8–5×.
- **Procedure:** one bag at a time, with nothing else running. Compress, decompress to a pipe and compare the sha256
  with the original, and **only then** remove the original `.db3`. About 2–2.5 h of CPU in total.
  `tools/bag_pack.sh pack|unpack <trial>` (to be written) restores a trial in place.
- **No result changes:** the restored file is the same bytes.
- **REJECTED alternative:** rosbag2's own compression (`ros2 bag convert`, zstd). All 649,663 messages are
  identical, but messages with equal receive timestamps are reordered (~196k positions: `/imu`, `/clock`). The UKF
  replay's IMU-timing safeguard then refuses the bag ("receipt stamps not monotonic"). That would change the
  replay input, so it is not acceptable.

**2. Move to external storage (needs a drive from you; ≈ 84 GB).**
- **`trials_pre_rerun/` (79.9 GB):** the originals of the re-flown sets. They are referenced only as the archive
  location (METHODOLOGY 4054–4261). No current `numbers.md` entry, figure or result JSON reads them.
- **Aborted and IMU-gap trial dirs (4.2 GB, 11 dirs):** excluded by rule from every result.
- **NOT proposed:** the superseded no-ceiling `fwd_*` (29.4 GB). They feed a current number, the ceiling effect
  size (`numbers.md` §11, `ceiling_flow_effect.json`, a standing METHODOLOGY rule). Keep them on disk; compress them
  under option 1.

**3. Regenerable intermediates (≈ 2.6 GB of replay outputs).** Not worth the regeneration risk. Not proposed.

## Recommendation

Option 1 on every trial **except** the T / O / L / room flights (they have no forward images and are needed now).
That leaves ≈ 300 GB free. Option 2 only if you want the pre-rerun originals off the machine. Flights stay paused
until you rule.
