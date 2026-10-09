# Handover, 2026-10-09: reproduction check of the rebuilt T/O/H/L job lists; old-vs-new extended to T/O/L/H/F/2(a)

**Stage:** ruling item 5 of "RULINGS (user, 2026-10-09): the final consolidated re-run pipeline", plus the "before launch"
extension of the old-vs-new script. The pipeline was **not** launched. Nothing was written into any trial directory or
under `~/thesis_data/batches/`: every old-code replay ran under a scratch `HOME`.

## 0. Method

- **Old code = the code that produced the stored output.** Each stored output was dated by mtime, and its provenance
  commit was chosen against every dependency (`room_ukf_replay`, `room_fgo_replay`, `lc_fgo_replay`, `ukf_core`,
  `measurement_models`, `imu_timing`, `fgo_core`, `factors`) via `git log --all`, not by the commit that recorded the
  result. No `metadata`/`stats.json` carries a git SHA, so the evidence is mtime-vs-commit time plus the reproduction itself.
- **Where it ran:** one temporary `git worktree add --detach <sha>` per commit, placed at `<scratch>/h_<sha>/thesis_ws`,
  with `HOME=<scratch>/h_<sha>`. `<scratch>/h_<sha>/thesis_data/trials/<trial>/` holds **copies** (no symlinks) of the
  inputs: `bag/`, `imu_gaps.json`, and for O also `gnss.npz`. These commits predate `UKF_OUT_ROOT`/`FGO_OUT_ROOT`, so
  the HOME redirection is what keeps outputs out of the stored trial directories.
- **Command:** the job line verbatim from `batches/final_rerun/*.jobs`, with only `cd /home/makerspace/thesis_ws` replaced
  by `cd <worktree>` and `HOME` set. Same venv, same `OPENBLAS/OMP/MKL_NUM_THREADS=1`, same `nice -n 10`, same flags and
  `ROOM_TAG_SIGMA_POS`. All replays ran inside `heavy.py` calls (no flight running, checked before each).
- **Comparison:** `.tum` files byte for byte; `rts_cov.npz` with `np.array_equal` per array (zip metadata is not stable);
  `stats.json` leaf by leaf, **excluding the timing keys** `step_median_ms`, `batch_s`, `wall_s`, `step_p99_ms`,
  `hindsight_polish_s` (wall-clock, machine-load dependent). Scorer JSONs byte for byte.

## 1. Verdict per list

**All four lists REPRODUCE.** Every replay below matches its stored output byte for byte (`.tum`), array for array
(`rts_cov.npz`), and key for key (`stats.json`, timing keys excluded). Every re-scored JSON is byte-identical to the
committed one.

| list | job (rebuilt line) | stored output (mtime) | provenance commit | result |
|---|---|---|---|---|
| T | `tu__T_A_r1` (`room_ukf_replay.py T_A_r1`, RTS) | `T_A_r1/room_ukf` (10-08 06:39) | **5e9e12e** (06:41; it carries the "RTS gain on the scaled covariance" change the output needs) | `ukf_live.tum`, `ukf_rts.tum`, `ground_truth.tum` bytes identical; `rts_cov.npz` equal; stats equal |
| T | `tf__T_A_r2` (`room_fgo_replay.py T_A_r2`, live + batch) | `T_A_r2/room_fgo` (live 06:03, batch 06:40) | **5e9e12e** | `fgo_live.tum`, `fgo_batch.tum` bytes identical; stats equal (batch_s 2173 vs 1609 s, timing) |
| T | `tf__T_A_r1` | `T_A_r1/room_fgo` (19:10, one of the six D15 re-runs) | **e88d403** (19:11; code as 305694f…2544585^) | bytes identical; stats equal |
| T | scorers: `tag_score.py` ×12 (venv-tags) + `t_aggregate.py` on the re-scored JSONs | `eval/results/expT/*.json` | e88d403 (tag_score/t_aggregate unchanged since 02f8df7/5e9e12e = HEAD) | **12/12 + aggregate byte-identical** |
| O | `ou__O_r1` (`room_ukf_replay.py O_r1 --gnss`) | `O_r1/room_ukf` (07:38) | **1558de1** (= 29f915f code) | bytes identical; npz equal; stats equal |
| O | `on__O_r1` (`--gnss --rts-no-yawcap`) | `O_r1/room_ukf_rtsnocap` (08:04:30) | **fb36114** (08:04:44; the flag does not exist at 1558de1) | bytes identical; npz equal; stats equal |
| O | `of__O_r1` (`room_fgo_replay.py O_r1 --gnss`, live + batch) | `O_r1/room_fgo` (live 07:41, batch 08:01) | **1558de1** | bytes identical; stats equal |
| O | `extract_gnss.py O_r1` (venv-tags) into a scratch HOME | `O_r1/gnss.npz` (07:32) | 1558de1 (unchanged since 8a4e9cf) | **file md5-identical** (943a35e2…) |
| O | scorer: `o_score.py` O_r1, O_r2, O_r3b (venv-tags) | `eval/results/expO/*.json` | fb36114 (= HEAD) | **3/3 byte-identical** |
| H | `hu__H_s1_r1` (`ROOM_TAG_SIGMA_POS=0.02`, RTS) | `H_s1_r1/room_ukf` (17:34) | **305694f** | bytes identical; npz equal; stats equal |
| H | `hf__H_s1_r1` (`--no-batch`) | `H_s1_r1/room_fgo` (17:38) | **305694f** (17:33, "room replay import fix") | bytes identical; stats equal |
| H | `hu__H_s1far_r1` (`--no-rts`) | `H_s1far_r1/room_ukf` (10-09 02:09) | **6082c56** | bytes identical; stats equal; no `ukf_rts.tum`/`rts_cov.npz`/`rts_nodes` on either side |
| H | `hf__H_s1far_r1` (`--no-batch`) | `H_s1far_r1/room_fgo` (02:13) | **6082c56**, i.e. BEFORE the noise-model fix 2544585 (02:47) | bytes identical; stats equal |
| H | scorer: `h_score.py` s1_r1..r3 (`s1_profile`) | `eval/results/expH/s1_r*.json` (67d6f02) | 67d6f02 | **3/3 byte-identical** |
| H | scorer: `h_score.py` s1far_r1, r2 (`s1_far_profile`) | `eval/results/expH/s1far_r*.json` (committed in 140d1bf) | **3c271e6** (the committed files carry the PRE-rename key, so they were written before the rename landed in 140d1bf) | **2/2 byte-identical**. With the 140d1bf scorer: all 186 values identical, only the hold key renamed |
| L | `llc__T_A_r1` (`lc_fgo_replay.py T_A_r1 --mode lc --t-max 245`) | `T_A_r1/lc_fgo_lc_t245` (12:54) | **009ba2f** (13:38) | `live.tum`, `hindsight.tum` bytes identical; stats equal (timing excluded) |
| L | `lnolc__T_A_r1` (`--mode nolc --t-max 245`, 54 min) | `T_A_r1/lc_fgo_nolc_t245` (13:37) | **009ba2f** | bytes identical; stats equal (incl. `landmarks_final`) |
| L | scorer: `l_score.py --suffix _t245` T_A_r1..r3 (venv-tags) | `eval/results/expL/*_t245.json` | 009ba2f (= HEAD) | **3/3 byte-identical** |

**Extra check: the stored T FGO set is consistent across its two code eras.** Six T `room_fgo` outputs (e.g. T_A_r2)
predate 29f915f (`batch_drop_yawcap`) and 8a4e9cf (GNSS model); the six D15 re-runs (e.g. T_A_r1) postdate them. Re-running
T_A_r2 with the e88d403 tree gives `fgo_live.tum` and `fgo_batch.tum` **byte-identical** to the stored 5e9e12e-era
output; `stats.json` differs only by the two keys 8a4e9cf added (`mode: tags`, `n_gnss_factors: 0`). So
`batch_drop_yawcap` is inert in T (as its code comment says) and old-vs-new deltas for T are not confounded by era.

**Today's scorers on the stored outputs** (what the pipeline's pre-score runs): O and T byte-identical to the committed
JSONs; H all 186 values identical, only `hold_windows_EKF3_flying` → `hold_windows_vehicle`. So the pre-score is the
committed numbers under the new key, and the fatal EKF3 gate against it is sound.

**Not reproduced (not attempted), stated plainly:** the other flights of each list (O_r2, O_r3b, T_B..D, H_s1_r2/r3,
H_s1far_r2, T_A_r2/r3 for L); `lvl__dsn_tex_r1` (V-L; packed bag; reported as not re-scorable under ruling 6);
`H_s1far_r3b` has no stored shadows (new jobs, nothing to reproduce; its `imu_gaps.json` is `ok`).

### Rebuilt choices (ruling item 5)

- **S1-far UKF without RTS:** reproduced byte-identically with `--no-rts`, and the stored directory has no
  `ukf_rts.tum`, no `rts_cov.npz` and no `rts_nodes` in `stats.json`, exactly as a `--no-rts` run produces. (The live
  track alone could not discriminate: RTS runs after the live pass.) CONFIRMED.
- **`s1_far` profile:** the committed s1far JSONs are reproduced byte-identically with `s1_far_profile.json`. **This
  check does not discriminate:** scoring s1far_r1 with the near profile `s1_profile.json` gives the same 186 values. The two
  profiles differ only in `wait_fix.near` (−1.5 vs −3.9 m), which `h_score.py` uses only for the setpoint before the first
  move; no scored window starts there (`h_score.py` lines ~51-58). The far profile is the correct one by
  METHODOLOGY ("S1 re-fly … `s1_far_profile.json`"), and it cannot change a number either way.
- **venv-tags for the scorers:** reproduces byte-identically. venv-evo cannot run them at all (no `pymavlink`;
  `ModuleNotFoundError`), so venv-tags is the only working choice. CONFIRMED.
- **Reuse of `gnss.npz`:** a fresh `extract_gnss.py O_r1` gives an md5-identical file, and the O replays that read the
  stored `gnss.npz` reproduce. CONFIRMED.
- **Thread setting:** all reproductions used the job lists' single-thread BLAS and match bit for bit, so the originals ran
  with the same setting (or the setting has no effect on these paths).

## 2. The old-vs-new script (`eval/rerun_compare.py`, extended)

- **Usage (unchanged CLI for the corridor part):** `python3 eval/rerun_compare.py OLD_DIR NEW_DIR --md OUT.md [--json OUT.json] [--prescore DIR]`.
  The pipeline's `compare` stage now passes `--prescore "$STATE/prescore"` (one-line change in
  `eval/final_rerun_pipeline.sh`; the dry run prints it).
- **New sections** (headline list of the pipeline handover §5):
  - **T** (`expT/t_aggregate.json`): mean RMSE per condition for the five tracks; orderings (FGO batch − RTS-UKF,
    FGO live − UKF live, UKF/FGO live − EKF3) flagged on sign; H-T1/P-T2 gain medians (sign), ρ (sign), p (≤ 0.01),
    strictly-increasing and PASS (verdict); P-T3/P-T4 ratios (band ≤ 1.5) and PASS.
  - **O** (`expO/O_r1, O_r2, O_r3b`): per-flight indoor RMSE, error at return, max step after return, for all six tracks
    including the cap-free RTS; orderings; H-O2 and P-O3 (capped and cap-free) ratios against 1.5; H-O1/H-O2/P-O3 as
    flight counts ("k/3", PASS iff all).
  - **L** (`expL/T_A_r*_t245.json`): lc/nolc live and hindsight RMSE; lap-5/lap-1 (H-L1, P-L4 against 1.5); lc − nolc
    orderings; H-L1..P-L4 counts. **V-L is printed as "NOT re-scorable (ruling 6)"** with its old value.
  - **H** (`expH/s1_r1..3`, `s1far_r1, r2`, and `s1far_r3b` new-only): H-H1 hold means (≤ 0.05); P-H5 drift at the end
    of each loss for EKF3/UKF/FGO, as worded and effective, against the pre-registered bands (EKF3/FGO 0.05/0.10/0.20/
    0.15 m, UKF 2×); re-lock from the first returning fix and the jump (UKF/FGO); drift orderings (FGO − UKF, UKF − EKF3,
    FGO − EKF3); P-H5 and P-H7 counts per estimator. Both hold keys (`hold_windows_EKF3_flying`, renamed
    `hold_windows_vehicle` in 140d1bf) are accepted.
  - **F1** (6-flight means per arm, FGO_robust − FGO_hard yaw-max orderings, decision incl. `robust_FGO_better`),
    **F2** (per flight, orderings, `hindsight_correction`), **F3/F3b/F3c** (per flight per Δ, FGO − UKF integral
    orderings, ratios, decision booleans), **2(a)/F4** (means, robust − hard orderings, P1/S1/S2 counts and PASS,
    reference counts, lockout totals).
- **Flags:** `DIRECTION` (sign/bool/side, as before) and the new `VERDICT` (a value crossing its band). Count rows are
  flagged when PASS changes.
- **Old side for H and O (conflict, recorded):** the brief says "old = `eval/results_pre_final`"; the pipeline handover
  says the same-scorer pre-score. The script supports both: per-trial H/O files come from `--prescore` when present,
  else from `OLD/expH`, `OLD/expO`. T's aggregate always comes from `OLD/expT` (the pre-score does not run
  `t_aggregate`). Section 1 shows the two sources are numerically identical for every value the script reads (only the
  H hold key differs), so the choice does not change a number.
- **Self-test** (`python3 eval/rerun_compare.py --selftest eval/results`): OLD = NEW = the committed results. **PASS**:
  1221 rows, 800 of them in T/O/L/H/F/2(a); in those, 0 non-zero deltas (raw values compared, not the rounded
  strings), 0 old≠new (V-L's "not re-scorable" excepted), 0 flags. Then three mutations of a scratch copy, each flagged:
  - H-T1 PASS flipped → `T verdicts | H-T1 PASS` flagged;
  - O_r1 FGO batch set to 3× the RTS-UKF → the three O_r1 "FGO batch − …" orderings and the H-O1 count (3/3 → 2/3) flagged;
  - s1_r1 UKF 30 s drift set to 0.55 m (band 0.40) → that P-H5 row and the UKF P-H5 count (20/20 → 19/20) flagged.
  No other row in the extended sections was flagged.
  - a new-only `s1far_r3b.json` (copy of s1far_r1 with a failing 0.9 m UKF 30 s drift) → its own "new-only" count row
    (3/4 FAIL), **not** flagged, and the both-sides P-H5/P-H7 counts unchanged. (Added after review: the counts
    originally mixed in flights present on one side only, so r3b alone could have flipped 20/20 to 23/24 as a
    "VERDICT"; counts now use flights scored on both sides.)
  - `f4_test.json` deleted on the new side → one `MISSING` row, a WARNING on stderr and exit code 3, so the pipeline's
    `compare` stage dies instead of rendering "—" as "no change". A presence guard covers every file the extended
    sections read (T aggregate, O ×3, L ×3, H ×6 with r3b allowed new-only, F1–F3c, F4).
- **Loss order is checked, not assumed:** P-H5 bands are assigned by loss index (5/15/30 s, move); the script emits a
  `LOSS ORDER` flag if a loss's `duration_s` falls outside 3–8 / 12–18 / 26–34 / 5–10 s. All five committed H files are in
  order today (5.1–5.3, 15.1–15.6, 30.1–30.6, 7.2–7.6 s).
- **New-side file names were checked against the dry run:** the pipeline writes `eval/results/expT/t_aggregate.json`,
  `expO/O_*.json`, `expL/T_A_r*_t245.json`, `expH/s1*_r*.json` (including `s1far_r3b.json`) and `f1/f2/f3/f3b/f3c/f4_test.json`,
  which are exactly the names read; the snapshot is a `cp -a eval/results eval/results_pre_final` (subdirectories included).
  - A second check with `--prescore` pointing at today's scorer's outputs on the stored data (renamed H key) gives 0
    mismatches and 0 flags in the 800 extended rows.
  - The corridor sections are NOT an identity under OLD = NEW (they map old file names to new ones,
    e.g. `dsn_dejitter_baseline` → `rerun_dsn_evo`), so their 10 flags in the self-compare are expected and excluded.

## 3. Open

- **Nothing blocks launch from this stage.** Still required before launch, from the ruling: the derotation fix merged and
  the four-correction preflight check passing in the main checkout.
- Reproduction covers one or two flights per list (table above), not every flight.
- `rerun_compare.py`'s H/O "old" source: `--prescore` (pipeline default) vs `results_pre_final` — numerically the same
  (§1), but the ruling text names only `results_pre_final`; confirm which is cited in the write-up.
- The extended sections compare JSON outputs only. The handover-§5 items that are not in any JSON (D27 item 3 per-heading
  weights 15.9/2.9 %, the closed-loop contact prediction, the C0 wording, the "S1→S2/S3 gap closes" wording, numbers.md
  prose) still need a by-hand row.
- `H_s1far_r3b` appears only on the new side (old "—").
- Leftover from an earlier, unrelated session in the shared scratch dir (`repro/thesis_ws` symlink, `repro/thesis_data`,
  dated 24 Sep) was left untouched.

## 4. State at the end

- Scripts and logs (scratch): `…/scratchpad/repro/{run_repro.sh, run_repro2.sh, run_scores.sh, score_3c271e6.sh,
  cmp_out.py, cmp_json.py, cmp_scores.sh, logs/, score/}`. Two `heavy.py` calls (12 replays + gnss extraction in
  parallel, ~54 min; then T_A_r2 at e88d403, ~25 min). No flight ran; `FLIGHT_LOCK` absent throughout.
- Temporary worktrees (10: 5e9e12e, e88d403, 1558de1, fb36114, 305694f, 6082c56, 009ba2f, 67d6f02, 140d1bf, 3c271e6)
  removed and pruned; no `BUILD_LOCK` held.
- No trial directory written: `find` over T_A_r1, T_A_r2, O_r1, H_s1_r1, H_s1far_r1 for files newer than the start
  returns nothing.
- Commit on `worktree-agent-ad7567d9245939b21`: `eval/rerun_compare.py` (extended + `--selftest`),
  `eval/final_rerun_pipeline.sh` (compare stage passes `--prescore`; comment), this handover. Not merged.
