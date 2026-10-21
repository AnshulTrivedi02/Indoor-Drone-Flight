# Extension experiments: Stage 2a reproduction gates

**Extension experiment, pre-registered (2026-10-21; signed off with amendments 2026-10-22).** This page covers Stage 2a
only: the checksum snapshot and the reproduction gates G0-L, G0-UKF and G-E4 of `preregistration.md` §7. No main E2,
E3, E4 or E5 run was started. V-E5 was not run, because the E5 code does not exist yet.

**Result: every gate PASSES.**
- Every compared file is byte-identical to its stored frozen counterpart: 4/4 for G0-L, 24/24 for G0-UKF and 12/12
  for G-E4.
- The guard `verify` after the last gate is IDENTICAL: 13,253 files, exit 0.

- **Code:** `fwd-camera` at `a09230a`, run from the main checkout `/home/makerspace/thesis_ws`. Every replay's
  `stats.json` records `commit a09230a` and `src_dirty ''`.
- **Date:** 2026-10-22, 00:28–01:13 AEDT.
- **Idle:** checked before the snapshot and before the first job. There was no `arducopter`, no `gz sim`, no
  `FLIGHT_LOCK` and no `BUILD_LOCK`. `heavy.py` re-checked this before every job.

## 1. Checksum snapshot (§6)

| item | value |
|---|---|
| command | `python3 tools/tier1_checksum_guard.py snapshot` (default scope: result data, documents excluded) |
| manifest | `docs/thesis/tier1/frozen_manifest_20261022T002851.json` (2.6 MB) |
| repo commit in manifest | `a09230ae76120ed6ebe804ec2acb15e1ff248c62` |
| files / bytes | **13,253 files, 10,115.4 MB** |
| per group (files, bytes) | `trials_T` 556, 1,709,962,854 · `trials_outputs` 8,010, 8,390,410,725 · `batches` 4,078, 9,460,772 · `results` 609, 5,609,888 |
| hashing time | 28.7 s (wall 0:28.77) |
| unmatched specs | none (`unmatched_specs: []`) |

§6's figure of "about 10 s for about 1.7 GB" belongs to the narrower Stage 1 scope, so it is stale. The widened default
measured 28.7 s for 10.1 GB.

## 2. How the gates were run

- **Serial, one job at a time.** Each job ran as
  `python3 src/estimators/fgo_cpp/tools/heavy.py --wait-s 1800 "tier1 stage2a <job>" -- bash <job script>`.
- **Driver:** `~/thesis_data/tier1/stage2a/driver.sh`, which runs the jobs strictly in sequence.
- **Job scripts:** `~/thesis_data/tier1/stage2a/jobs/`, one per job.
  - Each sets `cd /home/makerspace/thesis_ws` and `OMP/OPENBLAS/MKL/TBB_NUM_THREADS=1`.
  - Each uses the frozen interpreter: `~/venv-fgo` for the FGO replays and `~/venv-evo` for `room_ukf_replay.py`, as
    in frozen job `tu__*`.
  - `heavy.py` runs the command at nice 19.
- **Logs:** `~/thesis_data/tier1/stage2a/logs/<job>.log`.
- **Start, end, wall time and exit code:** `~/thesis_data/tier1/stage2a/timing.tsv`. All 26 jobs exited 0, and no log
  contains a warning, an error or a traceback.
- **Comparison:** `~/thesis_data/tier1/stage2a/compare.py`, which reads files only, with its output in `compare.json`.
  It takes the sha256 of each new and stored file, makes a full byte comparison, and counts rows. For a mismatch it
  would also give the first differing line and the maximum absolute difference; none occurred.
- **Deviation from §8's mechanism, not its intent:** the jobs were not queued through
  `eval/run_jobs_resumable.sh <jobs> tier1_<exp> 1`.
  - That runner creates `~/thesis_data/batches/tier1_<exp>/`, which the guard's `batches` group covers. `verify` would
    therefore report the folder as ADDED, which means STOP.
  - All job state is kept under `~/thesis_data/tier1/stage2a/` instead.
  - Execution was still serial under `heavy.py` with the pre-registered thread settings. The main runs need the same
    treatment, or an explicit ruling on where batch state may live.
- **Nice level:** the frozen jobs ran at `nice -n 10`; these ran at nice 19 under `heavy.py`, as §3 states for E4.
  Nice affects scheduling only, never the arithmetic.

## 3. Gate results

### G0-L: PASS

There were two runs on `T_A_r1`, with output root `~/thesis_data/tier1/g0`:
- (i) `--mode lc --t-max 245 --out-root …/g0`;
- (ii) the same, plus `--tag-ids 0,1,2,3,4,5,6,7 --mislabel-rate 0 --mislabel-seed 0`.

Reference: `~/thesis_data/trials/T_A_r1/lc_fgo_lc_t245/{live,hindsight}.tum`, the frozen Experiment 3 output from
`2cc08a2`.

**Run (ii) exercised the neutral new paths.** Its `stats.json` `tier1` block shows:
- `n_filtered_out_by_tag_ids 0`;
- mislabel `n_calls 2423`, `n_eligible_non_gauge 1770`, `n_mislabelled 0`;
- `landmarks_first_sighting_mislabelled 0`.

**`stats.json` (descriptive, not gated).** Against the stored file, only timing keys and the added `tier1` block
differ:
- `wall_s`: stored 299.4 s, new 127.2 s (i) and 129.7 s (ii);
- `step_median_ms`: 35.33 stored, 13.91 / 14.09 new;
- `step_p99_ms`;
- `hindsight_polish_s`.

Every other key is equal, including `t_anchor`, the landmark counts and the keyframe failures.

| run | file | rows | sha256 (new = stored) | result |
|---|---|---|---|---|
| `lc_fgo_lc_t245` | `live.tum` | 7350 | `37efcba34c9dd8e831b31aad291b2ed36fd5533df27e507fffea0fbeed1b88b2` | IDENTICAL |
| `lc_fgo_lc_t245` | `hindsight.tum` | 7351 | `b8cfacc0fce3e80d469315ae03aa999f020102476318dc3349d00abc41f4c677` | IDENTICAL |
| `lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0_s0` | `live.tum` | 7350 | `37efcba34c9dd8e831b31aad291b2ed36fd5533df27e507fffea0fbeed1b88b2` | IDENTICAL |
| `lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7_mis0_s0` | `hindsight.tum` | 7351 | `b8cfacc0fce3e80d469315ae03aa999f020102476318dc3349d00abc41f4c677` | IDENTICAL |

### G0-UKF: PASS (12/12)

- **Command:** frozen `room_ukf_replay.py <trial>` under `~/venv-evo`, with `UKF_OUT_ROOT=~/thesis_data/tier1/g0_ukf`.
- **Output:** `g0_ukf/<trial>/room_ukf/`.
- **Reference:** `~/thesis_data/trials/<trial>/room_ukf/{ukf_live,ukf_rts}.tum`, from `1b978de`.
- **Not gated, extra evidence:** `ground_truth.tum`, `rts_cov.npz` and `stats.json` are also byte-identical on 12/12
  (`compare.json`, group `G0-UKF_extra`).

| flight | file | rows | sha256 (new = stored) | result | wall (s) |
|---|---|---|---|---|---|
| T_A_r1 | `ukf_live.tum` | 17272 | `4ee02af0abda974c3a751f7dbca069ad4297c5b4d944722500eb54b123e54022` | IDENTICAL | 51.7 |
| T_A_r1 | `ukf_rts.tum` | 17272 | `62ee1665306508746a5f2b0803beac05db21e198343f14b610fe9d4764f1b7a9` | IDENTICAL | 51.7 |
| T_A_r2 | `ukf_live.tum` | 17240 | `67044802c5677b43afdd1bfff495fb467d71b37aab54cf87765f1a954408d143` | IDENTICAL | 51.6 |
| T_A_r2 | `ukf_rts.tum` | 17240 | `c5b2bf6d870ea97a2f3a97f1b8a589a03bff7379495a347992707940972f16e5` | IDENTICAL | 51.6 |
| T_A_r3 | `ukf_live.tum` | 17256 | `03966c17f6c7e9a012fe18d438a82a87200b535ff83209f7ee921b6a91b807dd` | IDENTICAL | 54.4 |
| T_A_r3 | `ukf_rts.tum` | 17256 | `394788fdad2040cf9bf64e4ee4279170aa2cd1f4636a8a3cb2ede58f767b228e` | IDENTICAL | 54.4 |
| T_B_r1 | `ukf_live.tum` | 17272 | `101d7c1b764f2050aacff79055fdef5d516f7fabb80cc6f8a44afccddd2830d3` | IDENTICAL | 51.7 |
| T_B_r1 | `ukf_rts.tum` | 17272 | `5a3cf9aef15c21a2b01aa2444ee2d3abd520c44a32dccd99c891f93b9386c87e` | IDENTICAL | 51.7 |
| T_B_r2 | `ukf_live.tum` | 17273 | `56891027cb486b1f70a478e325cd0dc383ebcc628a450c8d69be3a09d37f4412` | IDENTICAL | 50.8 |
| T_B_r2 | `ukf_rts.tum` | 17273 | `3a15d50431ca2cab236f9b267b9e0420faf0c91e3819387d839b78c27af278dc` | IDENTICAL | 50.8 |
| T_B_r3 | `ukf_live.tum` | 17259 | `309903320d2d77d2aa67d6edab6cbcf25b74cd4d7482fdac38c44cd6de7cac06` | IDENTICAL | 51.3 |
| T_B_r3 | `ukf_rts.tum` | 17259 | `b0fd0e4b5eb96caf711424f27bbeee6dc064aa51e85e213444ed3ef599e2e93a` | IDENTICAL | 51.3 |
| T_C_r1 | `ukf_live.tum` | 17258 | `7dd42bd2cccbc9d9fb8babbcb4165794268ca4ad8ae5dd80cd95b2bbfe5b82f1` | IDENTICAL | 50.6 |
| T_C_r1 | `ukf_rts.tum` | 17258 | `2e234aa3520a55fe55983532a2daa2007fa3801466f788cc5e5bc38e3fbffcf9` | IDENTICAL | 50.6 |
| T_C_r2 | `ukf_live.tum` | 17261 | `ae173a3341c75a8f88f77a129471e804d8cb3f25798f654412558c78529885ac` | IDENTICAL | 51.8 |
| T_C_r2 | `ukf_rts.tum` | 17261 | `4a8fbb0c17a6b6a05b58a3f45fb7ba00124e6ab0558dfca2bd78aae7fb1a2914` | IDENTICAL | 51.8 |
| T_C_r3 | `ukf_live.tum` | 17268 | `9b7663ba689d17796f4497a95ccfa3380f142452fdf62565b8f128e394997b5e` | IDENTICAL | 50.6 |
| T_C_r3 | `ukf_rts.tum` | 17268 | `9f2f38803fcc6c3216040a0f8324a230dd34909c5322217d580d358ad875a745` | IDENTICAL | 50.6 |
| T_D_r1 | `ukf_live.tum` | 17230 | `abd1c0e662810971cf3d7d26f0d4b6993a7635a56fed8fa703f3cf118fc5d97a` | IDENTICAL | 51.2 |
| T_D_r1 | `ukf_rts.tum` | 17230 | `308cb93464338ffde33a07604fb9f261f61544e8b2ff99467769d73bad2d9cb8` | IDENTICAL | 51.2 |
| T_D_r2 | `ukf_live.tum` | 17270 | `d50ff8cf86b93fc32eaa646d594f535ae113b027deceb6d860b9e6a7f9747af4` | IDENTICAL | 51.9 |
| T_D_r2 | `ukf_rts.tum` | 17270 | `03525c9a237c5ca851957ca6310b8059d3bc57fcdc72dccb367e6e41d0ccf774` | IDENTICAL | 51.9 |
| T_D_r3 | `ukf_live.tum` | 17235 | `17c48292a2cd13c396549f54a538aa69ae44fb05c95a9ab1cca13eb2e461e8a2` | IDENTICAL | 52.8 |
| T_D_r3 | `ukf_rts.tum` | 17235 | `73498c2a35d8f7982a79c580e7d283c6ac147c9d6c41a49fb597ecbe6eed9c59` | IDENTICAL | 52.8 |

### G-E4: PASS (12/12)

- **Command:** `room_fgo_replay.py <trial> --no-batch --window 0.25 --out-root ~/thesis_data/tier1` under `~/venv-fgo`.
- **Output:** `~/thesis_data/tier1/<trial>/room_fgo_w0.25/{fgo_live.tum, stats.json, step_times.npz}`.
- **Reference:** `~/thesis_data/trials/<trial>/room_fgo/fgo_live.tum`, from `2cc08a2`.
- **Also equal on 12/12:** `t_anchor` and `n_tag_factors`. There were 0 keyframe failures, and `step_times.npz` is
  present.
- **These runs are E4's own serial 0.25 s reference runs** (§3). They sit at the E4 output path, so E4 does not repeat
  them.

| flight | rows | sha256 of `fgo_live.tum` (new = stored) | result | wall (s) | step median / p95 (ms) | after anchor median / p95 (ms) | stored 6-parallel median (ms) | keyframe failures |
|---|---|---|---|---|---|---|---|---|
| T_A_r1 | 7774 | `df6a11a8880c3a7d8878cac1748cb7368efbb08f5c0cda0c361677068bb24b16` | IDENTICAL | 154.6 | 15.08 / 30.53 | 15.04 / 30.55 | 18.30 | 0 |
| T_A_r2 | 7760 | `794c53e3a92f09a54568237b9479768b7210416f7d251b3dc3971c479eb02e1b` | IDENTICAL | 150.9 | 15.01 / 30.23 | 14.96 / 30.27 | 18.41 | 0 |
| T_A_r3 | 7767 | `942a0528bdf5548b125560803868054b75bb482feed63d8e5febfc5f744fa20c` | IDENTICAL | 154.8 | 15.01 / 30.23 | 14.96 / 30.26 | 18.35 | 0 |
| T_B_r1 | 7774 | `3e6f9cd856b92fecd72c5631ae030ffb331a9b9eafc1618d549b6dfb5a2ff123` | IDENTICAL | 139.1 | 14.83 / 29.83 | 14.81 / 29.85 | 17.98 | 0 |
| T_B_r2 | 7775 | `b0f4babec37bb72b654bcbbb2cd7a9c4cef32e97a923273740169811fafc70c7` | IDENTICAL | 136.0 | 14.52 / 29.33 | 14.51 / 29.35 | 18.76 | 0 |
| T_B_r3 | 7769 | `247c2eb2d4ac24abc2b9a2429638e22ee4b673e5ed71719e54a5cecfbd62b17c` | IDENTICAL | 143.1 | 14.79 / 30.08 | 14.76 / 30.11 | 18.52 | 0 |
| T_C_r1 | 7768 | `57417851446124dd61d71ad910884dbb3d19e823fddb7be1f026d709759f3f29` | IDENTICAL | 139.0 | 14.67 / 29.52 | 14.65 / 29.56 | 17.29 | 0 |
| T_C_r2 | 7769 | `ab8d29a672444df57f69e8dcc57f0033e0ddeb5c6394b27c566bfff488cfb983` | IDENTICAL | 138.3 | 14.66 / 29.46 | 14.64 / 29.53 | 18.04 | 0 |
| T_C_r3 | 7772 | `f6d70c5161760f68017cab59df9d22bff25fdc76b8ca54fa50e244bcc824c399` | IDENTICAL | 137.9 | 14.63 / 29.65 | 14.61 / 29.66 | 18.21 | 0 |
| T_D_r1 | 7755 | `186fe3094f0cd3622ce498339ee5ef3ae556e18e326bde344eaf4b0e2d161c08` | IDENTICAL | 131.9 | 14.36 / 27.61 | 14.35 / 27.69 | 18.55 | 0 |
| T_D_r2 | 7773 | `028f7a36069761c7f29b288e9a675a7e9be557750fe5400312693b129b326df1` | IDENTICAL | 130.7 | 14.43 / 29.11 | 14.41 / 29.12 | 18.62 | 0 |
| T_D_r3 | 7757 | `6e92ca21e243d118f8bb5cb1fa5ddb1aae78ae6ed25575cdb5037d447c2656e1` | IDENTICAL | 139.0 | 15.14 / 29.92 | 15.13 / 30.05 | 18.43 | 0 |

**Timing for the §3/§8 tables. DIAGNOSTIC:** workstation Python, single-threaded BLAS, nice 19, serial.
- **Median step at 0.25 s:** 14.36–15.14 ms over all keyframes, and 14.35–15.13 ms after the anchor.
- **p95:** 27.61–30.53 ms.
- **Stored 6-parallel medians:** 17.29–18.76 ms.
- **The serial run is faster on every flight,** as §8 expected. These serial values, not the stored ones, are E4's
  timing reference.

## 4. Wall times (feed §8)

| run | n | wall per run (s) | total (s) | §8 planning figure |
|---|---|---|---|---|
| G0-L (LC, T_A_r1, t245) | 2 | 129.6, 132.0 | 261.6 | ≤ 521 s each (stored 6-parallel 301–521 s) |
| G0-UKF (live + RTS) | 12 | 50.6–54.4 (median 51.65) | 620.4 | 57–63 s each |
| G-E4 (0.25 s, `--no-batch`) | 12 | 130.7–154.6 (median 139.0) | 1,695.3 | about 190 s each (165–189 s stored, live part) |
| **all gates** | 26 | | **2,577.3 s (43.0 min)** | about 0.5 h for snapshot + G0-L + G0-UKF |

- Each wall time is measured by the driver around the `heavy.py` call, so it includes the lock check and the
  interpreter start.
- Every measured figure is below its §8 planning upper bound.
- On this evidence, serial LC replays take about 0.25–0.45× their stored 6-parallel wall times. That suggests the E2
  and E3 budgets in §8 are conservative. This is an inference from one LC flight, not a measurement of the others.

## 5. Guard verify (after the last gate)

| item | value |
|---|---|
| command | `python3 tools/tier1_checksum_guard.py verify docs/thesis/tier1/frozen_manifest_20261022T002851.json --report …_verify_stage2a.json` |
| result | **IDENTICAL**, exit 0. 13,253 files checked; changed 0, missing 0, added 0, errors 0, unmatched specs 0 |
| report | `docs/thesis/tier1/frozen_manifest_20261022T002851_verify_stage2a.json` (2026-10-22T01:12:44+1100) |

## 6. Consequence

- **G0-L PASS:** E2 and E3 may proceed.
- **G-E4 PASS:** E4 may proceed at windows other than 0.25 s.
- **G0-UKF PASS:** the stored Experiment 2 UKF reference is reproducible at HEAD. E5 still needs the supplementary
  code snapshot and V-E5a/b/c before any result run counts.
- **Next step, per §8 and the sign-off:** report these gates to the user, then run the main queue serially in the
  pre-registered order: E2 LC → E2 no-LC → E3 (a) → E3 (b) → E4 main (W = 0.5, 1, 2, 5) → E4 convergence (LM 10).
  The E5 validation and result runs join it at the next job boundary once the E5 code is ready.
- **Open procedural item for the user:** where batch state may live, given that the guard covers all of
  `~/thesis_data/batches/` (§2 above).
